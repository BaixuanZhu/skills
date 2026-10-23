# 03 · 存量代码审查

审查**已有的、别人写的**代码时逐条对照。收录标准是 **PMD 查不出、出错也不报错**——能静态判定的
写法已进 `assets/gate/` 的规则集，本文件不重复。

写新代码时不必逐条对照：这些坑在生成时基本不犯（实测 3/3、7/7 全部避开）。本清单的靶子是**人写的
遗留代码**——`Integer ==`、`finally` 里 return、`Arrays.asList(int[])` 在存量里很常见，
这部分不会随模型变强而消失。

## 审查顺序

按影响面从大到小，不要跳步：

1. **返回契约**——无结果返回什么、null 参数怎么处理、重复 key 留谁。对照项目的 `.claude/rules/java-contract.md`。
2. **集合与 Map**——视图、不可变、null 元素。
3. **数值与时间**——精度比较、除法、时区、包装类型。
4. **字符串**——拆分、区域、正则。
5. **异常与资源**——吞掉、断言、中断恢复。
6. **并发**——原子性、共享状态。

## 一、返回契约

| 写法 | 何时才暴露 | 正确做法 |
|---|---|---|
| 查不到返回 `null` | 调用方`.size()` 时 NPE，或各处补判空 | 空集合 / `Optional` |
| 空集合聚合返回 `0` | 报表多出一条 0 值假数据，永不报错 | `Optional` 或抛异常 |
| 必填参数 null 编默认值 | 方法恒返回同一结果（`threshold == null` 当 0 时，「是否存在金额 > 0」几乎恒为 true） | `Objects.requireNonNull` |
| `put` 与 `putIfAbsent` 混用 | 同一份导入，保留首条还是末条取决于写法，都不报错 | 统一 `putIfAbsent`，覆盖要注释 |

## 二、集合与 Map

| 写法 | 何时才暴露 | 正确做法 |
|---|---|---|
| `subList` 当独立列表用 | 改子列表改到原列表；原列表结构变更后抛 `ConcurrentModificationException` | `new ArrayList<>(sub)` / `List.copyOf(sub)` |
| `Arrays.asList(基本类型数组)` | 得到 `List<int[]>`，`size()` 恒为 1，遍历时才见怪结果 | `Arrays.stream(arr).boxed().toList()` |
| 并发 Map 两段式（`containsKey` + `put`、`get` 判空再 `put`） | 并发下丢更新，单测不出现 | `computeIfAbsent` / `merge` / `putIfAbsent` |
| `Collectors.toMap` 两参 | 脏数据出现重复 key 才抛 `IllegalStateException` | 三参 `(a, b) -> a`，或 `groupingBy` |
| `toMap` 的 value 可能为 null | 内部走 `HashMap.merge`，抛 NPE | `groupingBy` 或先 `filter` |
| 返回内部集合引用 | 调用方 `clear()` 改了对象状态，排查时找不到调用点 | `List.copyOf(items)` |
| 可变字段做 `HashMap` / `HashSet` 的 key | 改字段后再也查不到，`contains` 恒 false | key 用不可变对象；或用 id 作 key |
| `ConcurrentHashMap` 存 null value | `get` 返回 null 无法区分「没有」与「值是 null」 | 哨兵值或 `Optional` 包装 |
| `List.of` / `Arrays.asList` 结果做 `add` | 抛 `UnsupportedOperationException`，只在特定分支触发 | 需可变就 `new ArrayList<>(...)` |

## 三、数值与时间

| 写法 | 何时才暴露 | 正确做法 |
|---|---|---|
| `BigDecimal` 用 `equals` 比较 | 受 scale 影响，`1.0` 与 `1.00` 为 false，金额比对失败 | `compareTo(bd) == 0` |
| 裸 `divide` | 非整除时抛 `ArithmeticException`，只在某些金额组合下出现 | 给 scale + `RoundingMode` |
| `new BigDecimal(double 变量)` | 二进制误差完整带入，`0.1` 变 `0.1000000000000000055…` | `BigDecimal.valueOf` / 字符串构造 |
| 金额 `toString()` 输出 | 大数走指数形式 `1E+2`，前端或对接方解析失败 | `toPlainString()` |
| `LocalDateTime.now()` 记事件时间 | 服务器时区不同则时间错位，跨时区排查极难 | `Instant.now()` / `ZonedDateTime` |
| 共享 `SimpleDateFormat` 实例 | 并发下解析出错误日期，不抛异常 | `DateTimeFormatter`（不可变、线程安全） |
| `Math.abs(Integer.MIN_VALUE)` | 结果仍为负 | `Math.abs((long) x)` 或先判边界 |
| `Integer` / `Long` 用 `==` 比较 | 超出 -128~127 后恒为 false，测试数据小的时候完全不暴露 | `Objects.equals(a, b)`（先判 null） |
| `int v = map.get(k)` 直接拆箱 | key 不存在时 NPE，堆栈指向取值行而非根因 | 用 `Integer` 接再判空，或 `getOrDefault` |

## 四、字符串

| 写法 | 何时才暴露 | 正确做法 |
|---|---|---|
| `split(",")` 不传 limit | 尾随空串被丢弃，按固定下标取值错位 | 定长字段解析一律 `split(",", -1)` |
| `toLowerCase()` / `toUpperCase()` 不传 `Locale` | 土耳其语环境 `I` 变 `ı`，协议字段、枚举值比较失败 | `toLowerCase(Locale.ROOT)` |
| `split(".")` 等特殊字符 | 参数是正则，切不出预期结果 | 转义 `\\.`，或改用 `replace` |
| `replaceAll` 传字面量 | 参数按正则解释，`.` 与 `\` 行为不符预期 | 字面量替换用 `replace` |
| `trim()` 当去空白用 | 只处理 ≤ U+0020，中文全角空格去不掉 | 11+ `strip()` |
| 循环内 `s += x` | O(n²) 复制，几千次迭代才感知 | `StringBuilder` / `String.join` |

## 五、异常与资源

| 写法 | 何时才暴露 | 正确做法 |
|---|---|---|
| catch 块里有语句但无处理 | PMD 的 `EmptyCatchBlock` 只抓全空；记了日志不抛、不补偿，故障被吞 | 抛业务异常，或明确降级 + 告警 |
| `assert` 做参数校验 | 生产默认 `-da` 关闭，校验不生效 | 显式 `if` + 抛异常 |
| `catch (InterruptedException)` 不恢复中断 | 中断信号丢失，线程无法退出 | `Thread.currentThread().interrupt()` |
| `finally` 内 `return` / `throw` | 覆盖 try 的返回值与异常，异常凭空消失 | 移出 finally；资源用 try-with-resources |
| `try` 块包住不相关的代码 | 误捕获本该向上抛的异常 | `try` 只包真正可能失败的那几行 |

## 六、并发

| 写法 | 何时才暴露 | 正确做法 |
|---|---|---|
| `new Random()` 多线程共享 | 争用同一 seed，吞吐下降且序列可预测 | `ThreadLocalRandom.current()`（8+） |
| `forEach` 里做累积 | 并行流下顺序不定，结果不稳定且不报错 | `collect` / `reduce` |
| `parallelStream()` 默认使用 | 小数据量下慢于串行，并与其它并行任务抢公共 ForkJoinPool | 只在「大数组 + 纯计算 + 无共享状态」用 |
| `findAny` 当 `findFirst` 用 | 并行流返回的元素不确定，测试偶发失败 | 需要第一个就 `findFirst` |
| 共享可变字段无线程安全措施 | 可见性与竞态，压测才暴露 | `volatile` / 原子类 / 加锁，或改为不可变 |

## 与门禁的分工

| 类型 | 归属 |
|---|---|
| 空 catch、`finally` return、`new BigDecimal(0.1)` 字面量、命名规范、未用变量、`printStackTrace`、`SimpleDateFormat` 静态字段 | 规则集（`assets/gate/`），PMD 能查 |
| 本文件全部条目 | 人工或 agent 审查，PMD 查不出 |
| 空指针解引用、资源泄漏、弱加密 / SQL 注入等字节码级问题 | 需 SpotBugs / Semgrep 一类工具，本技能不含 |
