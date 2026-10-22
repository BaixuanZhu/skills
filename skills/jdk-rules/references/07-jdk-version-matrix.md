# 07 · 版本矩阵

目标 JDK 决定可用语法。本文件给两张表：**按 API 反查最低版本**、**同一意图在各版本的写法**。

LTS 锚点：8 / 11 / 17 / 21 / 25。非 LTS 按版本号比较，preview / incubator 一律不用（编译需 `--enable-preview`，CI 与生产环境不匹配）。

## 一、API → 最低版本

### 集合与 Optional

| API | 版本 |
|---|---|
| `Map.getOrDefault`、`List.sort`、`Collection.removeIf`、`Comparator.comparing` / `thenComparing` / `nullsFirst` | 8 |
| `List.of` / `Set.of` / `Map.of` / `Map.ofEntries` / `Map.entry` | 9 |
| `Optional.ifPresentOrElse`、`Optional.or(Supplier)`、`Optional.stream` | 9 |
| `Stream.ofNullable`、`Stream.takeWhile` / `dropWhile`、`Stream.iterate` 三参版 | 9 |
| `List.copyOf` / `Set.copyOf` / `Map.copyOf` | 10 |
| `Collectors.toUnmodifiableList` / `toUnmodifiableSet` / `toUnmodifiableMap` | 10 |
| `Optional.orElseThrow()` 无参版、`Optional.isEmpty` | 11 |
| `Collectors.teeing` | 12 |
| `Stream.toList`（不可变） | 16 |
| `SequencedCollection`（`getFirst` / `getLast` / `addFirst` / `reversed`） | 21 |

### 字符串

| API | 版本 |
|---|---|
| `String.join` | 8 |
| `String.isBlank` / `strip` / `stripLeading` / `stripTrailing` / `lines` / `repeat` | 11 |
| `String.indent` / `transform` | 12 |
| `String.formatted` | 15 |
| 文本块 `"""` | 15 |

### 数值

| API | 版本 |
|---|---|
| `Math.addExact` / `multiplyExact` / `toIntExact`、`Integer.compare`、`Integer.hashCode` | 8 |
| `Math.floorDiv` / `floorMod`（处理负数取模） | 8 |
| `Math.clamp` | 21 |

### 语言语法

| 语法 | 版本 |
|---|---|
| Lambda、方法引用、接口 `default` / `static` 方法 | 8 |
| 接口私有方法 | 9 |
| `var`（仅局部变量） | 10 |
| `switch` 表达式（箭头 `->`、`yield`） | 14 |
| `record` | 16 |
| `instanceof` 模式匹配 | 16 |
| `sealed` / `permits` | 17 |
| `switch` 模式匹配（类型模式 + `when` 守卫 + null 分支） | 21 |
| 未命名变量 `_` | 22 |

### 并发与 IO

| API | 版本 |
|---|---|
| `CompletableFuture`、`ThreadLocalRandom`、`Arrays.parallelSort` | 8 |
| `CompletableFuture.orTimeout` / `completeOnTimeout` / `delayedExecutor` | 9 |
| `java.net.http.HttpClient` | 11 |
| `Files.readString` / `writeString` | 11 |
| `ExecutorService` 实现 `AutoCloseable` | 19 |
| 虚拟线程 `Thread.ofVirtual()` / `Executors.newVirtualThreadPerTaskExecutor()` | 21 |
| `ScopedValue` | 25 |
| `Stream.gather`（Gatherers） | 24 |

## 二、同一意图 × 版本写法

| 意图 | JDK 8 | JDK 11 | JDK 17 | JDK 21 |
|---|---|---|---|---|
| 判空字符串 | `s != null && !s.trim().isEmpty()` | `s != null && !s.isBlank()` | 同 11 | 同 11 |
| 不可变列表 | `Collections.unmodifiableList(new ArrayList<>(src))` | `List.copyOf(src)`（10+）或 `Collections.unmodifiableList` | 同 | 同 |
| 固定元素列表 | `Arrays.asList(a, b)`（定长） | `List.of(a, b)` | 同 | 同 |
| Stream 转 List | `collect(Collectors.toList())` | 同 | `toList()`（不可变） | 同 |
| 多行字符串 | `"a\n" + "b\n"` | 文本块（15+） | 文本块 | 文本块 |
| 格式化 | `String.format("%s-%d", a, b)` | `String.format` | `"%s-%d".formatted(a, b)`（15+） | 同 |
| 重复字符串 | 手写循环 | `"x".repeat(n)` | 同 | 同 |
| 数据载体 | 手写 POJO + getter/setter + equals/hashCode | 手写 POJO（record 需 16） | `record Point(int x, int y) {}` | 同 |
| 类型判断后强转 | `if (o instanceof Foo) { Foo f = (Foo) o; ... }` | 需 16 | `if (o instanceof Foo f) { ... }` | 同，或 `switch (o) { case Foo f -> ... }` |
| 多分支返回 | `if-else` 链或 `switch` + `break` | 需 14 | `return switch (k) { case A -> 1; default -> 0; };` | 同，可加 `case Integer i when i > 0 -> ...` |
| 取集合首尾 | `list.get(0)` / `list.get(list.size() - 1)` | 同 | 同 | `list.getFirst()` / `list.getLast()` |
| 剔除 null 元素 | `filter(x -> x != null)` | `filter(Objects::nonNull)`（9+） | 同 | 同 |
| 有值才执行 | `if (o.isPresent()) { use(o.get()); }` | `o.ifPresent(this::use)`（8 已有）/ `ifPresentOrElse`（9+） | 同 | 同 |
| 区间限制 | `Math.min(max, Math.max(min, v))` | 同 | 同 | `Math.clamp(v, min, max)` |
| 后台任务 | `new Thread(r).start()` / 固定线程池 | 同 | 同 | `Thread.ofVirtual().start(r)`（IO 密集场景） |

## 三、低版本项目误用高版本 API 的编译症状

| 症状 | 原因 |
|---|---|
| `cannot find symbol: method of(java.lang.String)` | JDK 8 用了 `List.of`（9+） |
| `records are not supported in -source 8` / `Record declarations are a feature of Java 16` | 用了 `record` |
| `text blocks are not supported in -source 8` | 用了 `"""` |
| `as of release 10, 'var' is a restricted type name` | 用了 `var` |
| `switch expressions are not supported in -source 8` / `-source 11` | 用了 `case X ->` |
| `illegal start of expression` 指向 `instanceof Foo f` | 模式匹配需 16 |
| `cannot find symbol: class ScopedValue` / `Stream.gather` | 用了更高版本的 API |

看到这些错误，**先确认目标 JDK，再改写法**；不要通过调高 `pom.xml` 的 `release` 来消除——那会让产物在目标运行时上直接 `UnsupportedClassVersionError`。

## 四、升级时的优先收益

从低版本升到某版本后，可立即减少手写的地方：

| 升到 | 立刻能删掉的手写代码 |
|---|---|
| 11 | 判空辅助方法（`isBlank` / `strip`）、文件读写工具（`Files.readString`）、手写 HTTP 客户端（`HttpClient`） |
| 17 | 手写 DTO 的 getter/setter/equals/hashCode（`record`）、手写类型判断强转（`instanceof` 模式）、层层 if-else 分支（`switch` 表达式） |
| 21 | 手写「取首尾元素」判断（`getFirst` / `getLast`）、线程池包装的异步任务（虚拟线程）、手写区间夹取（`Math.clamp`） |

升级前先确认依赖栈支持该版本（Spring Boot 2.x 不支持 17+ 的部分特性，Spring Boot 3.x 需 17+）。
