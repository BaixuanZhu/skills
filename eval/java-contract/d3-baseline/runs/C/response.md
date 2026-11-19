# MemberIndex 边界处理决策说明

实现文件：`src/main/java/com/example/directory/MemberIndex.java`
契约依据：`.claude/rules/java-contract.md`（本项目列为空，全部取默认约定）

## 方法形态

四个方法均为纯函数 → **全部 `static`**，类为 `final` + 私有构造的工具类。契约「静态还是实例」行约定纯函数用 static 且同一个类不混用，本类无任何依赖注入需求，故不出现实例方法。

## 返回契约（无结果返回什么）

| 方法 | 返回类型 | 无结果时 | 理由 |
|---|---|---|---|
| `index` | `Map<String, Member>` | 空 Map | 契约：列表/映射返回空集合，不用 null |
| `find` | `Optional<Member>` | `Optional.empty()` | 契约：单条结果用 `Optional`，不用 null |
| `averageAge` | `Optional<Double>` | `Optional.empty()` | 契约：聚合看 0 是否有业务含义——平均无「0 岁」业务含义，故用 `Optional` 而非 0.0 |
| `groupByTeam` | `Map<String, List<Member>>` | 空 Map | 同 `index` |

## 各类边界情况的处理规则

### 1. 参数为 null

- **`members` 集合参数（四个方法都有）**：**按空集合处理**——返回空 Map / `Optional.empty()`，不抛异常。依据契约「null 参数」行：集合参数按空处理；本业务允许空输入（需求明确"可能整个集合为空"），故不做 `isEmpty()` 非空校验。
- **`find` 的 `id` 标量参数**：`Objects.requireNonNull(id, "id")` 抛 **NullPointerException**，fail fast。依据契约「必填标量 requireNonNull，不编默认值」——id 是查找的必填键，为 null 时编造默认值（如"匹配不到"）会掩盖上游数据错误。不改抛 `IllegalArgumentException`：契约把 null 参数（requireNonNull/NPE）与非法参数（IAE）分开归类，null 属于前者。

### 2. 集合里的 null 元素

一律**跳过**，继续处理后续元素（契约「集合里的 null」行：`null` 元素跳过）。四个方法行为一致，不因个别脏元素整体失败。

### 3. 字段无值（Member 各字段都可能没有值）

契约规则："字段无值：累加/平均跳过整条记录"。推广到键型操作：**操作所依赖的字段无值 → 该记录在本操作中整条跳过**：

| 方法 | 依赖字段 | 该字段无值时 | 理由 |
|---|---|---|---|
| `index` | `id` | 整条跳过 | id 无值无法成为索引键；Map 不收 null 键，返回契约也要求"不用 null" |
| `find` | `id` | 整条跳过 | `id` 查询参数已 requireNonNull 非 null，null id 的记录本就不会命中，显式跳过语义更清楚 |
| `averageAge` | `age` | 整条跳过 | 契约明示"累加/平均跳过整条记录"；不把缺失当 0 计入，避免拉低平均值 |
| `groupByTeam` | `team` | 整条跳过 | team 无值无组可入；不编造"未知组"哨兵键（会污染真实 team 名空间） |

其余字段无值不影响本操作：如 `averageAge` 只看 `age`，id/name/team 缺失仍计入平均。

### 4. 重复 id 的成员

- **`index` / `find`（id 是键）**：**保留首条**——`index` 用 `putIfAbsent`，`find` 返回首个命中。契约「重复 key」行：`putIfAbsent` 保留首条；覆盖需 `put` + 注释，本实现不需要覆盖语义。两方法首条语义保持一致。
- **`averageAge` / `groupByTeam`（id 不是键）**：**不去重、按记录原样处理**。契约「重复 key」行约束的是以该 key 建 Map 的场景（putIfAbsent）；分组的键是 team、聚合无键，把"保留首条"外推为按 id 去重属于编造规则。同一 id 的两条记录是导入数据里的两条记录，各计入一次平均、各留在所属组内。

### 5. 空集合输入

正常路径处理，自然得到空 Map / `Optional.empty()`（见返回契约表），不抛异常。

### 6. 返回集合的形态

- Map 一律 `Collections.unmodifiableMap(new LinkedHashMap<>(...))`：**保插入顺序**（`index` 为 id 首次出现顺序，`groupByTeam` 为 team 首次出现顺序，组内为输入顺序）、**不可变**。契约明示 `Map.copyOf` 不保序，故不用。
- `groupByTeam` 的组内 List 一律 `Collections.unmodifiableList(new ArrayList<>(...))`，同样不可变。
- 未要求字典序，故不用 `TreeMap`（契约：字典序才用 TreeMap，默认保插入序）。

### 7. 未处理的场景（显式不引入规则）

- `age` 负值/极端值：需求列出的质量问题不含取值范围，按原值计入平均，不做范围校验（避免过度设计）。
- 非法参数抛 `IllegalArgumentException` 的场景：本类没有"参数值不合法"的判定标准（null 已按契约走 requireNonNull），故未使用。

## 编译与验证情况

- **编译**：`mvn -q compile` 通过（exit 0，无 warning 输出）。JDK 17（`maven.compiler.release=17`），未使用 17 以上语法/API。
- **契约分支实测**（jshell + `target/classes`，覆盖契约要求的"空入参 / 无结果 / 重复 key 至少跑一次"，另覆盖 null 元素、字段无值、不可变性）：

| 用例 | 结果 | 符合预期 |
|---|---|---|
| `index([a(30),null,a(26),null-id(40),b(20),c(no age)])` | `{a=首条Ann, b=Bob, c=Cat}` | 重复 id 首条、null 元素/无 id 跳过 |
| `find(src,"a")` | `Optional[首条Ann]` | 重复 id 首条 |
| `find(src,"zz")` | `Optional.empty` | 无结果 |
| `averageAge(src)` | `Optional[29.0]`（(30+26+40+20)/4） | null 元素与无 age 记录跳过，其余按记录计入 |
| `groupByTeam(src)` | `{T1=[Ann,Amy,NoId], T2=[Cat]}` | 无 team 的 Bob 跳过，组内保输入序 |
| `index(null)` / `groupByTeam(null)` | `{}` | 集合参数 null 按空处理 |
| `find(null,"a")` | `Optional.empty` | 同上 |
| `find(src,null)` | `NullPointerException` | 必填标量 fail fast |
| `averageAge([])` / `averageAge(全无age)` | `Optional.empty` | 平均无业务含义不返回 0 |
| `index(...).put(...)` | `UnsupportedOperationException` | Map 不可变 |
| `groupByTeam(...).get("T1").add(...)` | `UnsupportedOperationException` | 组内 List 不可变 |
