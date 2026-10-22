# 01 · 判空与 Optional

## 要不要判空

判空是契约问题，不是风格问题。「标准库优先」约束的是**写法**（`s != null && !s.isEmpty()` 写成 `!s.isBlank()`），不是**省略检查**——把「少写 if」理解成「不判空」是本末倒置。

| 位置 | 处理 |
|---|---|
| 对外契约边界：Controller 入参、RPC/HTTP 响应解析、消息体、配置读取、文件与命令行输入 | 必须判。外部输入不满足任何内部契约 |
| 公共库 / SDK 的公开方法 | 必须判。调用方是谁不可知，入参 `Objects.requireNonNull` 或返回 `Optional` |
| 同一个类或模块内的私有方法 | 按调用方契约；上游已判则不重复判，用 `@Nullable` / 文档写明 |
| 集合 / 数组返回值 | 恒返回空实例而非 null，调用方不必判 |

判断依据是「这个值从哪里来」，不是「方法有多少行」。

## 判空矩阵

| 类型 | ✗ 手写 | ✓ 标准库 |
|---|---|---|
| `String` | `s != null && s.length() > 0` | `s != null && !s.isEmpty()` |
| `String`（含空白） | `s != null && !s.trim().isEmpty()` | 11+ `s != null && !s.isBlank()`；8~10 用 `!s.trim().isEmpty()` |
| `String` 常量在前 | `s.equals("x")`（s 可能 null） | `"x".equals(s)` / `Objects.equals(s, "x")` |
| 集合 / Map | `c != null && c.size() > 0` | `c != null && !c.isEmpty()` |
| 数组 | `a != null && a.length > 0` | `a != null && a.length > 0`（无更短写法） |
| 任意对象相等 | `a != null && a.equals(b)` | `Objects.equals(a, b)` |
| 取默认值 | `x == null ? 默认 : x` | 9+ `Objects.requireNonNullElse(x, 默认)` |
| 必填校验 | `if (x == null) throw new IllegalArgumentException("x")` | `Objects.requireNonNull(x, "x 不能为空")` |

`Objects.requireNonNull` 的异常类型是 `NullPointerException`，需要 `IllegalArgumentException` 时手写判断。

## Optional 的边界

**只做返回值**。以下都算误用：

| ✗ | 原因 |
|---|---|
| 字段 `private Optional<String> name;` | 不可序列化；字段可空就用 null，必填就用 `requireNonNull` |
| 参数 `void f(Optional<String> x)` | 调用方得先包一层；直接重载或用 null |
| 集合元素 `List<Optional<T>>` | 用 `filter(Objects::nonNull)` 或空集合语义 |
| `Optional.of(maybeNull)` | 值为 null 时抛 NPE，应 `ofNullable` |

## 取值

| 意图 | ✓ |
|---|---|
| 无值给默认（默认是常量） | `orElse(默认)` |
| 无值给默认（默认要计算） | `orElseGet(() -> 计算())` —— `orElse` 会无条件计算实参 |
| 无值抛异常 | `orElseThrow()`（10+）/ `orElseThrow(() -> new BizException("..."))` |
| 有值才执行 | `ifPresent(v -> ...)` |
| 有值执行一个、无值执行另一个 | 9+ `ifPresentOrElse(v -> ..., () -> ...)` |
| 链式转换 | `map(f).filter(p).orElse(...)` |
| 转集合 | 9+ `stream().toList()`；8 用 `Collections.singletonList` 或空列表判断 |

**禁 `get()`**：没有前置 `isPresent()` 就是运行期风险；有前置判断则整段可换成上面的形式。

## 坑

- `optional.map(f)` 里 `f` 返回 null → 结果是 `Optional.empty()`，不是 `Optional.of(null)`。要区分「映射后为 null」和「原本为空」，得在 `f` 里显式判断。
- `orElse(null)` 能编译，但等于把 Optional 又退化成可空引用；需要可空就直接用 null，不要绕 Optional。
- `Stream<Optional<T>>` 上 `flatMap(Optional::stream)` 可一次剔空（9+）。
- `==` 与 `equals` 的默认值陷阱：`Optional.of(128) == Optional.of(128)` 恒 false（不同实例），永远用 `equals`。

## null 返回约定

| 方法类型 | ✗ | ✓ |
|---|---|---|
| 返回集合 | `return null;` | `List.of()` / `Collections.emptyList()` |
| 返回单个对象 | 返回 null 且调用方不知道 | 返回 `Optional<T>`，或文档写明可空 |
| 返回数组 | `return null;` | `new T[0]` |
