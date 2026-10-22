# 03 · 字符串

## 判空与去空白

| ✗ | ✓ |
|---|---|
| `s.length() == 0` | `s.isEmpty()` |
| `s != null && !s.trim().isEmpty()` | 11+ `s != null && !s.isBlank()` |
| `s.trim()`（去 ASCII 空白） | 11+ `s.strip()`（按 Unicode 空白，含全角空格） |
| 手写循环去首尾空白 | `stripLeading()` / `stripTrailing()`（11+） |
| 手写判「是否为数字」 | 无标准库；用 `try { new BigDecimal(s); }` 或项目既有工具 |

`trim()` 只处理码点 ≤ U+0020，`strip()` 处理 `Character.isWhitespace`，中文全角空格只有 `strip()` 能去。

## 拼接

| 场景 | 选 |
|---|---|
| 固定几段、单次 | `+`（编译器已优化，不必手写 `StringBuilder`） |
| 循环内累积 | `StringBuilder`；或改成 `String.join` / `Collectors.joining` |
| 集合连接 | `String.join(",", list)` / `stream().collect(Collectors.joining(",", "[", "]"))` |
| 带索引判断分隔符的循环 | 直接 `joining`，不手写 `if (i > 0) sb.append(",")` |

```java
// ✗ 循环内 += ，O(n²) 复制
String r = "";
for (String s : items) { r += s + ","; }

// ✓
String r = String.join(",", items);
```

`StringBuilder` 默认容量 16，已知长度时 `new StringBuilder(items.size() * 8)` 可减少扩容。

## 格式化

| ✗ | ✓ |
|---|---|
| `String.format("%s-%d", a, b)` | 15+ `"%s-%d".formatted(a, b)`；8~14 用 `String.format` |
| 手写补零 `(n < 10 ? "0" : "") + n` | `String.format("%02d", n)` |
| 手写千分位 | `String.format("%,.2f", amount)` |
| 手写多行拼接 `"a\n" + "b\n"` | 15+ 文本块 `"""` |

格式符：`%s` 任意、`%d` 整数、`%f` 浮点、`%.2f` 两位小数、`%02d` 补零、`%,d` 千分位、`%b` 布尔、`%n` 换行（跨平台）。
`%d` 传 `long` 也可；`%s` 传 null 输出 `"null"`，要控制就用 `Objects.toString(x, "")`。

## 拆分

| ✗ | ✓ |
|---|---|
| `s.split(",")` 需要全部字段（含尾部空串） | `s.split(",", -1)` |
| `s.split(".")` | `s.split("\\.")` —— 参数是**正则**，`. \| * + ? ( ) [ ] { } ^ $` 都要转义 |
| `s.split(",")` 只取前 N 段 | `s.split(",", N)`（limit 为正时最多 N 段，最后一段含剩余） |
| 只为取一段就 split 整个串 | `s.substring(0, s.indexOf(','))` 或 `StringUtils`（若项目已有） |

`split(",")` 会把**尾部连续空串全部丢弃**：`"a,b,,".split(",").length == 2`，字段数变化会让按下标取值错位。需要定长字段解析一律传 `-1`。

## 替换

| 意图 | 用法 |
|---|---|
| 字面量替换（含特殊字符） | `replace(".", "_")` —— 字面量，`replaceAll` 才按正则 |
| 正则替换 | `replaceAll("\\s+", " ")` |
| 只替换第一处 | `replaceFirst` |
| 大小写无关替换 | 8+ `replaceAll("(?i)abc", "x")` |

`replace(char, char)` 比 `replace(String, String)` 快，单字符替换优先用 char 版本。

## 比较与大小写

| ✗ | ✓ |
|---|---|
| `a == b` | `a.equals(b)` / `Objects.equals(a, b)` |
| `a.equals(b)` 且 a 可能 null | `"x".equals(a)` / `Objects.equals` |
| `s.toLowerCase().equals("abc")` | `s.equalsIgnoreCase("abc")` |
| `s.toLowerCase()`（默认 Locale） | `s.toLowerCase(Locale.ROOT)` —— 土耳其语环境下 `I` 会变成 `ı`，导致协议字段名、枚举值比较失败 |
| `s.isEmpty()` 判空白 | 11+ `s.isBlank()` |

排序用 `compareTo`（字典序），不要用 `==` 或 `equals` 判断大小。

## 其他高频

| 意图 | ✓ |
|---|---|
| 查找 | `indexOf` / `lastIndexOf` / `contains` |
| 前后缀 | `startsWith` / `endsWith`（可传 offset 版本 8+ 已有） |
| 重复 | 11+ `s.repeat(n)` |
| 逐行处理 | 11+ `s.lines()`（按 `\n` / `\r\n` 切） |
| 取字符 | `s.charAt(i)`（越界抛 `StringIndexOutOfBoundsException`）；11+ `s.codePointAt(i)` 处理代理对 |
| 按码点遍历 | `s.codePoints()`，`charAt` 遍历会把 emoji 拆成两个 char |
| 缩进重排 | 12+ `s.indent(n)` |
| 截取一段 | `s.substring(begin, end)`，`end` 不含；`begin == end` 返回空串，`begin > end` 抛异常 |

## 坑

- **`intern()` 慎用**：字符串常量池在 JDK 7 后位于堆，但仍可能拖慢且有内存滞留；比较用 `equals`。
- **循环 `+=` 是 O(n²)**：每次都新建 String 并复制，几千次迭代就能感知。
- **`String.format` 慢于 `+`**：热路径（每秒数千次）用 `+` 或 `StringBuilder`。
- **`substring` 在 JDK 7+ 会复制字符数组**：旧版本的「共享 char[] 导致内存泄漏」已不存在，不必再手动 `new String(s.substring(...))`。
- **`"a".equals(null)` 返回 false，`null.equals("a")` 抛 NPE**：常量放前面。
