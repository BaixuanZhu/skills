# MemberIndex 边界处理决策说明

实现文件：`src/main/java/com/example/directory/MemberIndex.java`
目标 JDK：17（`maven.compiler.release=17`）
API 形态：`public final class MemberIndex`，四个能力均为**无状态静态方法**，私有构造器防实例化（纯函数式工具，无共享可变状态，天然线程安全）。

方法签名（返回类型由我选定）：

| 能力 | 方法 | 返回类型 |
| --- | --- | --- |
| 按 id 建索引 | `index(List<Member>)` | `Map<String, Member>`（不可变） |
| 查单个成员 | `find(List<Member>, String)` | `Optional<Member>` |
| 平均年龄 | `averageAge(List<Member>)` | `OptionalDouble` |
| 按 team 分组 | `groupByTeam(List<Member>)` | `Map<String, List<Member>>`（不可变，内层列表也不可变） |

返回值尽量不可变、用 `Optional`/`OptionalDouble` 显式表达“可能无结果”，避免用 `null` 或魔法值（如 `0.0` / `-1`）承载“无定义”。

---

## 一、逐类边界情况的处理规则与理由

### 1. 参数 `members` 为 `null`
**规则**：按**空集合**处理——`index`/`groupByTeam` 返回空映射，`find` 返回 `Optional.empty()`，`averageAge` 返回 `OptionalDouble.empty()`。

**理由**：任务明确“输入来自外部导入、质量不可信”，`null` 入参被列为需处理的边界之一。此处选择**宽容降级**而非 `Objects.requireNonNull` 直接抛 NPE，与其余数据质量问题（空元素、空集合）的处理风格一致：让方法在任何输入下都返回一个语义正确的结果、从不抛异常，便于在数据管道中安全串联。
**取舍**：另一派观点认为“参数为 null 是编程错误应 fail-fast 抛 NPE”。本项目语境是外部脏数据清洗，我优先“不中断流水线”，并在文档中显式声明该契约，调用方可据此判断是否要在上游自行校验。

### 2. 集合为空
**规则**：返回“空/无结果”。`index`→空映射；`find`→`Optional.empty()`；`averageAge`→`OptionalDouble.empty()`；`groupByTeam`→空映射。

**理由**：空集合是合法输入，各方法的“空结果”语义自洽。平均年龄对空集**无定义**，故用 `OptionalDouble.empty()` 而非返回 `0.0`（0 会被误读为“平均年龄 0 岁”）。

### 3. 集合内含 `null` 元素
**规则**：**静默跳过**，四个方法统一忽略 `null` 元素。

**理由**：`null` 元素不携带任何 id/team/age，无法参与建索引、查找、求均值、分组；它是导入过程产生的损坏记录。跳过能保证“跳过坏记录、保留好记录”，不让一条脏数据让整个调用失败。

### 4. 成员 `id` 为 `null`
**规则**：不进入 id 索引/查找。`index` 中跳过 id 为 `null` 的成员；`find` 在待查 `id` 为 `null` 时直接返回 `Optional.empty()`。

**理由**：id 是索引主键，`null` 不是合法的键。若把 `null` 当键存入 `Map`，会带来 `Map.copyOf` 抛 NPE、`get(null)` 歧义等实现隐患；若允许 `find(list, null)` 去匹配 id 为 `null` 的成员，又与“null 不是合法键”自相矛盾。故统一把 `null` id 视作**无主键的记录**，不参与按 id 的检索。

### 5. 重复 `id` 的成员
**规则**：**首次出现者生效**。`index` 用 `putIfAbsent` 保留列表中最先出现的成员；`find` 返回首个 id 匹配的成员——两者保持一致。

**理由**：一个 id 对应多条记录时必须择一。选择“首现优先”而非“后现覆盖（upsert）”，因为：① 给定列表顺序下结果确定；② 视后到的重复为噪声/重复行，避免一条可能残缺的重复记录覆盖掉先前的有效记录；③ `index` 与 `find` 语义统一，`find(m, id)` 必然等于 `index(m).get(id)`。
**取舍**：若业务语义是“后写覆盖”，应改为 `put` 覆盖；此处按“去重取权威首条”的保守契约实现，并在 Javadoc 注明。

### 6. 成员 `age` 无值（`null`）
**规则**：**不参与平均年龄计算**，即被排除出分子与分母。若全部成员的 age 都缺失（或集合为空/全为 null 元素），`averageAge` 返回 `OptionalDouble.empty()`。

**理由**：缺失年龄是“未知”而非“0”；若按 0 计入会系统性拉低均值。均值只应基于已知年龄的成员计算。当没有任何已知年龄时，均值无定义，用 `OptionalDouble.empty()` 显式表达，而不是返回 `0.0`/`NaN`/抛异常。
**附注**：年龄的**取值合法性**（如负数）不在本任务范围（任务只要求处理“可能没有值”），故未做取值校验，避免过度设计。求和用 `long` 累加以规避超大列表下 `int` 累加溢出。

### 7. 成员 `team` 为 `null`
**规则**：归入键 `""`（空字符串）——“未分组”桶；`team` 本身为 `""` 的成员与之同桶。`groupByTeam` 仍会包含这些成员（不丢数据）。

**理由**：① 分组应尽量覆盖全量成员，把无 team 的成员单独放到“未分组”桶而非丢弃，避免静默丢数据；② 用 `""` 而非 `null` 作键，规避 `null` 键在 `Map.copyOf`、部分 `Map` 实现、以及消费方 `get(...)` 上的隐患；③ 任何字符串都可能成为真实 team 名，无法构造“绝不冲突”的哨兵值，故采用约定俗成的空串作为“无 team”桶，并在 Javadoc 显式声明 `null` 与 `""` 会同桶这一轻微合并行为。
**取舍**：另一方案是丢弃无 team 成员，但那会造成分组不再覆盖全集；也有方案用 `null` 键保留原值，但会引入 null 键隐患。综合“不丢数据 + 不埋 null 键雷”选了空串桶。

### 8. 返回值可变性
**规则**：`index`/`groupByTeam` 返回不可变映射，`groupByTeam` 的内层列表也不可变；键的迭代顺序为首次出现顺序（用 `LinkedHashMap` 保持确定性）。

**理由**：调用方不应反向篡改工具内部产出的数据结构；不可变返回值更安全、行为更可预测，且保持插入顺序让结果可复现、可测试。

---

## 二、一致性保证

- `find(m, id)` 与 `index(m).get(id)` 在所有输入下结果一致（均“首现优先”，均排除 null/null-id）。
- 四个方法对 `null` 入参、`null` 元素的处理完全一致（全部跳过/降级为“空”）。
- 任何输入都不抛异常（纯降级语义），边界行为可预测、可测试。

---

## 三、编译 / 验证情况

- 工作目录：`I:/GitDownload/skills/eval/java-contract/d3-baseline/runs/A`
- 命令：`mvn -q compile`
- 结果：**编译通过**（退出码 0）。
- 产物核对：`target/classes/com/example/directory/` 下已生成 `Member.class` 与 `MemberIndex.class`。
- 项目依赖仅使用标准库 `java.util`（`LinkedHashMap`/`List`/`Map`/`Optional`/`OptionalDouble`/`Collections`/`ArrayList`），无需额外依赖，符合 JDK 17。
- 未修改 `pom.xml` 与 `Member.java`；仅新增 `MemberIndex.java` 与本文件。

> 备注：本次验证为**编译级验证**（按任务要求执行 `mvn -q compile`），未新增单元测试文件（受“只创建/修改这两个文件”的约束）。边界规则已逐条在 Javadoc 与本文档中声明，便于后续按契约补充针对性测试。
