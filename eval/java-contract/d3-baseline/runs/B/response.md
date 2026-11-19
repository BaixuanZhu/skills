# MemberIndex 边界处理决策说明

实现文件：`src/main/java/com/example/directory/MemberIndex.java`（新建）。
遵循 `.claude/rules/java-contract.md`（java-contract@2.7.1 播种，「本项目」列为空 → 全部取默认值）与
`context/java-contract/` 技能全文。`pom.xml` 确认目标 JDK 为 17（`maven.compiler.release=17`）。

## 方法签名（返回类型与 static 按契约自定）

四个方法都是只依赖入参的纯函数 → 全部 `static`（契约第六项：纯函数 static、同类不混用），
类为 `final` + 私有构造器。

| 方法 | 签名 | 决策要点 |
|---|---|---|
| `index` | `static Map<String, Member> index(List<Member>)` | 重复 id 保留首条；空入参 → 空 Map |
| `find` | `static Optional<Member> find(List<Member>, String id)` | 单条 → `Optional`，不返回 null |
| `averageAge` | `static OptionalDouble averageAge(List<Member>)` | 平均，0 无业务含义 → Optional 族，不返回 0 |
| `groupByTeam` | `static Map<String, List<Member>> groupByTeam(List<Member>)` | 分组键缺失的记录跳过；保插入顺序、不可变 |

`averageAge` 选 `OptionalDouble`（而非 `Optional<Double>`）：它是 JDK 对「平均值可能不存在」的原生表达
（`DoubleStream.average()` 即此返回类型），语义就是契约要求的「平均 → Optional」。

## 边界处理决策（逐类情况）

### 1. 集合参数本身为 null / 空集合

**规则**：`members == null` 与空集合等价，按空处理，不抛异常、不用 `requireNonNull`。
**为什么**（契约第二节）：集合参数一律按空处理——`null` 与空在这类方法里没有语义差别，区分它们只是
给调用方制造两种失败方式。空集合是合法输入，结果由「无结果」规则兜底（见第 7 条）。

### 2. 集合里的 null 元素

**规则**：跳过，不参与任何方法，也不让整批失败。
**为什么**（契约第三节）：入参来自外部导入，容忍脏元素比要求调用方先清洗更符合业务预期；
跳过元素层的 null 是任何集合入参的统一前置（「先剔除再计算」）。

### 3. 重复 id 的成员

**规则**：保留首条（`putIfAbsent` 语义），后到的记录整体丢弃，四个方法口径一致——
`index` 存首条、`find` 返回首条、`averageAge` 只计首条、`groupByTeam` 只归组首条。
首条即使字段有缺失也不被后条覆盖。
**为什么**（契约第四节）：数据从外部导入且 key 不唯一时，默认保留首条——「判不出要先到还是最新就选
保留首条，覆盖会让后到的脏数据悄悄替换正确值」。若同一成员被导入两次，平均值把它计两次、分组里出现两份，
都是静默失真；`find` 与 `index` 若各持一种去重口径，还会出现「index 里是 A、find 找回 B」的同契约两种结果。
首条字段缺失时不改用后条补位——那等于隐式切换成「覆盖」策略，需要显式决策而不是顺手发生。

### 4. 记录的 id 字段无值（null 或空白）

**规则**：跳过整条记录（四个方法共享的「有效成员集」在入口剔除）。
**为什么**：id 是成员身份键。无 id 的记录无法参与「按 id 判重」（无从判断它是不是某条已有记录的重复，
计入聚合会与第 3 条的去重规则自相矛盾），也无法被 `index`/`find` 定位。空白与 null 同等视为缺失
（契约第三节字段层：「字段为 null 或空白」即无值，0/空串与「无值」不是一回事）。四个方法共用同一
有效成员集，避免同一份契约在不同方法下得出两种成员口径。

### 5. 记录的 age 字段无值（null）

**规则**：`averageAge` 跳过整条记录——不计入分子也不计入分母，**不用 0 代替**；分母只含有效 age。
**为什么**（契约第三节字段层「累加/平均 → 跳过整条记录」）：0 岁与「没有年龄」不是一回事。
用 0 代替会拉低均值且不报错，报表上留下一条与「平均年龄确实是 0」不可区分的假数据。
其余三个方法不用 age，不受影响。

### 6. 记录的 team 字段无值（null 或空白）

**规则**：`groupByTeam` 跳过整条记录，不归入 null 键或 `""` 组；`index`/`find`/`averageAge` 不用 team，不受影响。
**为什么**：team 是分组键，无键无法归组。归入 `""` 组或 null 键会伪造一个「空 team 组」，与某个真实存在的
空名团队不可区分——同样是把「无值」折成一个值。分组视图只呈现能归组的成员，无法归组的记录不出现在任何组里。

### 7. 无结果（三种形态）

**规则**：`find` 查不到 → `Optional.empty()`；`averageAge` 无可算记录（空入参 / 全被剔除）→ `OptionalDouble.empty()`；
`index` / `groupByTeam` 无成员 → 空 Map。一律不返回 null。
**为什么**（契约第一节）：单条查询「可能不存在」→ `Optional`；列表型结果 → 空集合；聚合看 0 是否有业务含义——
平均值 0 是假数据（与「平均年龄确实是 0」不可区分），故平均返回 Optional 族而不是 0。

### 8. find 的 id 参数为 null / 空白

**规则**：`id == null` → `Objects.requireNonNull(id, "id")` 抛 NPE（fail fast）；空白 id → 抛 `IllegalArgumentException`。
**为什么**：id 是「参与定位」的必填标量（契约第二节）——null 无法定位，必须 fail fast 且**不给它编默认值**
（若把 null 当「查不到」返回 `Optional.empty()`，调用方传错被静默掩盖成业务上的「查无此人」，比抛 NPE 难查得多）。
空白 id 属「参数本身违规（空串）」（契约第五节），且 find 是领域层查询、非展示层参数，按领域层 fail fast 抛
`IllegalArgumentException`（JDK 标准异常，不新造异常类）。与之对照：格式合法但不存在的 id（如 `"Z"`）返回
`Optional.empty()`——「查不到」是该方法的正常结果域，只对无法定位/格式违规的入参 fail fast。
不 trim：`" A "` 与 `"A"` 视为不同 id，方法不做值域清洗。

### 9. 返回集合的顺序与可变性

**规则**：`index` / `groupByTeam` 的 Map 一律保插入顺序（key 首次出现顺序，`LinkedHashMap`），
Map 与 `groupByTeam` 的内层 List 均不可变（`Collections.unmodifiableMap(new LinkedHashMap<>(x))` + `List.copyOf`）。
**为什么**（契约第七节）：方法返回值是对外契约，调用方无从判断顺序哪天会变——`HashMap` 的遍历顺序
随 hash 而定，必须定下来；team 名是任意标签而非枚举/状态码，故用插入顺序而非 `TreeMap` 字典序。
可变性默认不可变，防止调用方改动返回值后反向污染；`Map.copyOf` 不保序，故不用（保序 Map 显式用
`unmodifiableMap(new LinkedHashMap<>(x))`）。

### 10. 未做校验的项（明确排除）

- **age 数值范围**（负数、超大值）：属数据质量而非本次边界契约的分歧点，未校验，按原值参与平均。
- **id/team 的值域格式**（长度、字符集）：需求未定义合法格式，不做猜测校验。
- **重复到达（契约第八项）**：四个方法都是无副作用的只读纯函数，天然幂等，该契约项不适用。

## 编译 / 验证情况

1. **编译**：`mvn -q compile` 通过（maven 可用，未走 javac 回退）。目标版本取自 `pom.xml` 的
   `maven.compiler.release=17`，未使用 JDK 9+ 之外的语法，也未改任何编译配置。
2. **契约分支冒烟**（jshell 对 `target/classes` 直接调用，三类各覆盖）：
   - 空入参：`index(null)` → `{}`；`find(null, "A")` → `Optional.empty`；`averageAge(List.of())` → `OptionalDouble.empty`；`groupByTeam(null)` → `{}`。
   - 无结果：`find(raw, "Z")` → `Optional.empty`；全部记录 age 缺失时 `averageAge` → `OptionalDouble.empty`（不是 0）。
   - 重复 key：`raw = [A/Alice/30, null, A/AliceDup/99, B/Bob/40, C/Cara/无age, D/无team/25, 无id/Eve/20]`：
     `index` 保留 `A=Alice`（首条，非 AliceDup）；`find(raw,"A")` → Alice；`averageAge` → `31.666…`（(30+40+25)/3，
     无 age 的 Cara 与无 id 的 Eve 被剔除）；`groupByTeam` → `{T1=[Alice, Bob], T2=[Cara]}`（无 team 的 Dan 不归组）。
   - 异常与不可变：`find(raw, null)` → `NullPointerException: id`；`find(raw, " ")` → `IllegalArgumentException`；
     对 `index` 结果 `put`、对分组内层 List `add` 均抛 `UnsupportedOperationException`。
3. **无正式测试文件的原因**：任务约束只允许创建/修改 `MemberIndex.java` 与 `response.md` 两个文件，
   不得新增测试类；故以 jshell 冒烟替代，覆盖了契约要求的三类分支及异常/不可变性检查。

## 约束遵守

- 只创建/修改了 `src/main/java/com/example/directory/MemberIndex.java` 与本文件；
  `pom.xml`、`Member.java`、`.claude/rules/java-contract.md` 均未改动。
- 仅读取工作目录内文件，未联网。
