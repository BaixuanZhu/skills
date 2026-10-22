# 05 · Stream 与 Collectors

## 先判断该不该用

| 场景 | 选 |
|---|---|
| 简单过滤 + 转换 + 收集 | Stream |
| 需要 `break` / `continue` / 提前返回多层 | 普通 `for` |
| 需要下标访问、相邻元素比较 | 普通 `for`（或用 `IntStream.range`） |
| 循环体里有 IO、事务、异常处理 | 普通 `for` —— Stream 里受检异常要包 try-catch，反而更难读 |
| 性能极敏感的百万级热路径 | 普通 `for`（Stream 有对象创建与装箱开销） |
| 只需判断存在 / 全匹配 / 无匹配 | `anyMatch` / `allMatch` / `noneMatch`（短路） |

**为了「看起来函数式」而把 for 改成 Stream 是负收益。**

## 常用形态

| 意图 | ✓ |
|---|---|
| 过滤 | `stream().filter(p)` |
| 转换 | `stream().map(f)` |
| 扁平化（集合套集合） | `flatMap(x -> x.getItems().stream())`；`Optional` 用 `flatMap(Optional::stream)` |
| 去重 | `distinct()`（依赖 `equals`/`hashCode`） |
| 排序 | `sorted()` / `sorted(Comparator.comparing(...))` |
| 取前 N / 跳过 | `limit(n)` / `skip(n)` |
| 剔 null | `filter(Objects::nonNull)` |
| 转 Map | `collect(Collectors.toMap(k, v))` |
| 分组 | `collect(Collectors.groupingBy(Foo::getType))` |
| 连接 | `collect(Collectors.joining(",", "[", "]"))` |
| 求和 | `mapToInt(Foo::getCount).sum()`（避免装箱） |
| 转数组 | `toArray(String[]::new)` |

`Stream.ofNullable(x)`（9+）用于「可能为 null 的单个元素」建流；`takeWhile` / `dropWhile`（9+）用于有序流的条件截断。

## Collectors

| 用途 | 写法 |
|---|---|
| 转 List | `.toList()`（16+，**不可变**）/ `collect(Collectors.toList())`（可变，8+） |
| 转不可变 List | 10+ `Collectors.toUnmodifiableList()` |
| 转 Set | `Collectors.toSet()`（`HashSet`，无序）→ 需要有序用 `toCollection(LinkedHashSet::new)` |
| 转 Map | `Collectors.toMap(Foo::getId, Foo::getName)` |
| 转 Map（重复 key 保留先出现的） | `toMap(k, v, (a, b) -> a)` |
| 转 Map（指定实现） | `toMap(k, v, (a, b) -> a, LinkedHashMap::new)` |
| 分组 | `groupingBy(Foo::getType)` → `Map<K, List<Foo>>` |
| 分组后计数 | `groupingBy(Foo::getType, Collectors.counting())` |
| 分组后取字段 | `groupingBy(Foo::getType, mapping(Foo::getName, toList()))` |
| 分区 | `partitioningBy(p)` → 恒有 `true` / `false` 两个 key |
| 求和 / 均值 | `summingInt` / `averagingInt`（返回 `Double`） |
| 同时要两个结果 | 12+ `teeing(collector1, collector2, (a, b) -> ...)` |

## 坑

- **`toMap` 不给 merge 函数**：重复 key 抛 `IllegalStateException: Duplicate key`。只要 key 可能重复就必须给 `(a, b) -> a`。
- **`toMap` 的 value 不能为 null**：`HashMap.merge` 内部实现会抛 NPE。value 可能为 null 时改用 `groupingBy` 或先 `filter`。
- **`toList()` 不可变**：16+ 的 `Stream.toList()` 返回不可修改列表，后续想 `add` 会抛 `UnsupportedOperationException`；需要可变用 `collect(Collectors.toList())`。
- **Stream 只能消费一次**：`Stream s = list.stream(); s.count(); s.count();` 第二次抛 `IllegalStateException: stream has already been operated upon or closed`。
- **`forEach` 里做累积**：`forEach` 不保证顺序（并行流更是），累积用 `collect` / `reduce`。
- **`map` 里有副作用**（写库、改外部变量）：并行流下会乱序且线程不安全；有副作用就用 `forEachOrdered` 或退回普通 `for`。
- **`findFirst` vs `findAny`**：串行流两者等价；并行流 `findAny` 更快但结果不确定，需要「第一个」就用 `findFirst`。
- **`reduce` 无初始值时返回 `Optional`**：`reduce((a, b) -> a + b)` 对空流返回 `Optional.empty()`；有初始值 `reduce(0, Integer::sum)` 返回具体值。
- **`sorted` 遇 null 元素抛 NPE**：先 `filter(Objects::nonNull)` 或用 `Comparator.nullsFirst`。
- **并行流不是默认选项**：数据量小（< 1 万）时线程开销大于收益；`parallelStream()` 内部用公共 ForkJoinPool，会与其他并行任务抢线程。只在「大数组 + 纯计算 + 无共享状态」时考虑。
- **`IntStream.range` 优于 `for` 计数**：`IntStream.range(0, n).map(i -> ...)` 可比手写 for 更清晰，但要访问外部变量时仍用 for。
