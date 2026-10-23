# 02 · 版本门控

判据：`目标 JDK ≥ 特性最低版本` 可用。LTS 锚点 8 / 11 / 17 / 21 / 25；非 LTS 按版本号比较；
preview / incubator 一律不用（需 `--enable-preview`，CI 与生产不匹配）。

完整 API 清单不列——`List.of` 属 9、`record` 属 16 这类孤立事实不必查表。本文件只放两样容易漏的：
**同一意图在四档 LTS 上的写法**、**越界后的编译症状**。

## 一、同一意图 × LTS 写法

| 意图 | JDK 8 | JDK 11 | JDK 17 | JDK 21 |
|---|---|---|---|---|
| 判空字符串 | `s != null && !s.trim().isEmpty()` | `s != null && !s.isBlank()` | 同 11 | 同 11 |
| 不可变列表 | `unmodifiableList(new ArrayList<>(src))` | `List.copyOf(src)`（10+） | 同 | 同 |
| 固定元素列表 | `Arrays.asList(a, b)`（定长） | `List.of(a, b)` | 同 | 同 |
| Stream 转 List | `collect(Collectors.toList())` | 同 | `toList()`（不可变） | 同 |
| 数据载体 | POJO + getter/setter + equals/hashCode | 同（record 需 16） | `record Point(int x, int y) {}` | 同 |
| 类型判断后强转 | `if (o instanceof Foo) { Foo f = (Foo) o; }` | 需 16 | `if (o instanceof Foo f) { }` | 或 `case Foo f ->` |
| 多分支返回 | `if-else` 链 / `switch` + `break` | 需 14 | `return switch (k) { case A -> 1; default -> 0; };` | 可加 `when` 守卫 |
| 多行字符串 | `"a\n" + "b\n"` | 文本块（15+） | 文本块 | 文本块 |
| 取首尾 | `get(0)` / `get(size() - 1)` | 同 | 同 | `getFirst()` / `getLast()` |
| 区间夹取 | `Math.min(max, Math.max(min, v))` | 同 | 同 | `Math.clamp(v, min, max)` |

## 二、越界后的编译症状

| 症状 | 原因 |
|---|---|
| `cannot find symbol: method of(...)` | JDK 8 用了 `List.of`（9+） |
| `records are not supported in -source N` | 用了 `record`（16+） |
| `text blocks are not supported in -source N` | 用了文本块（15+） |
| `as of release 10, 'var' is a restricted type name` | 用了 `var`（10+） |
| `switch expressions are not supported in -source N` | 用了 `case X ->`（14+） |
| `illegal start of expression` 指向 `instanceof Foo f` | 模式匹配需 16 |
| `cannot find symbol: class ScopedValue` / 方法名属高版本 API | 用了更高版本的 API |

**判断顺序：先确认目标 JDK，再改写法。** 上表前六行都带版本线索，按提示降级即可。真正危险的是
`cannot find symbol` 且 `symbol` 看不出归属（如 `method toList()`）——这类报错不含版本信息，
顺着去补 import 或改名，只会把版本问题改成一堆无用代码。

不要调高 `pom.xml` 的 `release` 消除报错：产物会在目标运行时 `UnsupportedClassVersionError`。

升级前先确认依赖栈支持该版本：Spring Boot 2.x 不支持 17+ 的部分特性，3.x 需 17+。
