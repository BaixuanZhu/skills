# 04 · 数值与日期时间

## 整数

| 陷阱 | 正确做法 |
|---|---|
| `a + b` 溢出静默回绕 | `Math.addExact(a, b)`（溢出抛 `ArithmeticException`） |
| `a * b` 溢出 | `Math.multiplyExact(a, b)` |
| `(int) longValue` 截断 | `Math.toIntExact(longValue)` |
| 手写 `if (a > b) return 1; if (a < b) return -1; return 0;` | `Integer.compare(a, b)` / `Long.compare` |
| `i1 == i2`（`Integer`） | `i1.equals(i2)` / `Objects.equals` —— 只有 -128~127 走缓存，超出范围 `==` 为 false |
| `int v = map.get(k);`（可能 null） | `map.getOrDefault(k, 0)` / `Objects.requireNonNullElse` —— 拆箱 NPE |
| 整数除法求百分比 `a / b * 100` | `a * 100 / b`（先乘后除），或转 `double`/`BigDecimal` |
| `Math.abs(Integer.MIN_VALUE)` | 仍是负数（无正数对应）→ `Math.abs((long) x)` 或先判边界 |
| `int` 存金额分 | 优先 `long`；上限 `Integer.MAX_VALUE` 约 21 亿分 = 2147 万元 |

`long` 字面量用大写 `L`（`123L`），小写 `l` 易被看成 `1`。

## 浮点

| 陷阱 | 正确做法 |
|---|---|
| `0.1 + 0.2 == 0.3` 为 false | 不要用 `==` 比较浮点；金额一律 `BigDecimal` |
| 需要比较浮点 | `Math.abs(a - b) < 1e-9`（按业务精度定阈值） |
| `float` 存金额 | 用 `BigDecimal` 或 `long` 存最小单位（分） |
| `(int) 3.99` | 得到 3（截断）；要四舍五入用 `Math.round(3.99)` |

## BigDecimal

| 规则 | 说明 |
|---|---|
| 只用 `String` 构造或 `valueOf` | `new BigDecimal(0.1)` 会把 double 的二进制误差完整带进来，得到 `0.1000000000000000055511151231257827...` |
| 比较用 `compareTo` | `equals` 同时比 scale：`new BigDecimal("1.0").equals(new BigDecimal("1.00"))` 为 false |
| `divide` 必须给 scale + `RoundingMode` | 否则非整除时抛 `ArithmeticException: Non-terminating decimal expansion` |
| `setScale` 必须给 `RoundingMode` | 不给且需舍入时抛 `ArithmeticException` |
| 输出用 `toPlainString()` | `toString()` 在指数场景输出 `1E+2` 形式，前端/接口会解析失败 |
| 判零用 `signum() == 0` | `compareTo(BigDecimal.ZERO) == 0` 等价，`equals` 受 scale 影响 |
| 除法链式运算 | `a.divide(b, 10, RoundingMode.HALF_UP).multiply(c).setScale(2, RoundingMode.HALF_UP)` —— 只在最后一步定 scale |
| 比较大小 | `a.compareTo(b) > 0`，不要 `a.subtract(b).signum()` |
| `stripTrailingZeros()` 后 `toPlainString` | 去掉无意义的尾零，但注意 `new BigDecimal("0.00").stripTrailingZeros()` 会变成 `0E-2`，再 `toPlainString()` 得 `"0.00"` |

常用舍入：`HALF_UP`（四舍五入，业务默认）、`HALF_EVEN`（银行家舍入，财务对账场景）、`DOWN`（截断）、`CEILING` / `FLOOR`（方向）。

## 日期时间类型选择

| 场景 | 类型 |
|---|---|
| 时间戳、跨时区存储、日志 | `Instant` |
| 数据库 `timestamp` 列（有时区语义） | `Instant` 或 `OffsetDateTime` |
| 本地日期时间（不带时区） | `LocalDateTime` |
| 只有日期 / 只有时间 | `LocalDate` / `LocalTime` |
| 需要带时区偏移或夏令时规则 | `ZonedDateTime` / `ZoneId` |
| 时间长度 / 日期跨度 | `Duration`（时分秒）/ `Period`（年月日） |

**`LocalDateTime` 不携带时区**，存库后跨时区读取会歧义；存「事件发生时刻」用 `Instant`。

## 取当前时间

| ✗ | ✓ |
|---|---|
| `LocalDateTime.now()` | `LocalDateTime.now(zoneId)` |
| `new Date()` | `Instant.now()` |
| 各 Service 各写一个时区字符串 | 应用级单一 `ZoneId` 常量或注入 `Clock`（便于单测固定时间） |

`Clock` 注入是唯一能让时间相关逻辑可测的做法，`LocalDate.now()` 无法在测试里固定。

## 格式化与解析

| ✗ | ✓ |
|---|---|
| `SimpleDateFormat` 作字段/静态字段 | `DateTimeFormatter`（不可变、线程安全） |
| 格式串 `"YYYY-MM-dd"` | `"yyyy-MM-dd"` —— `Y` 是**周所属年**，12 月 30 日可能格式化成下一年 |
| `"hh:mm:ss"` 表示 24 小时制 | `"HH:mm:ss"` —— `hh` 是 12 小时制 |
| `formatter.parse` 后用 `Date` | `LocalDate.parse(s, formatter)` 直接得到类型 |
| 自定义解析格式 | 优先 ISO 标准：`LocalDate.parse("2026-10-22")`、`Instant.parse("2026-10-22T08:00:00Z")` |

常用 pattern：`yyyy-MM-dd`、`yyyy-MM-dd HH:mm:ss`、`HH:mm:ss`、`yyyyMMddHHmmss`（无分隔符，适合做流水号）。

## 运算

| 意图 | ✓ |
|---|---|
| 加 N 天 / 月 / 年 | `plusDays(n)` / `plusMonths(n)` / `plusYears(n)` |
| 月末 | `date.with(TemporalAdjusters.lastDayOfMonth())` |
| 下月第一天 | `date.with(TemporalAdjusters.firstDayOfNextMonth())` |
| 下一个工作日 | `TemporalAdjusters.next(DayOfWeek.MONDAY)` |
| 两个日期差 | `ChronoUnit.DAYS.between(from, to)` / `MONTHS` / `YEARS` |
| 两个时刻差 | `Duration.between(a, b).toMinutes()` |
| 截断到天 / 小时 | `dt.truncatedTo(ChronoUnit.DAYS)` |
| 判断区间 | `!d.isBefore(start) && !d.isAfter(end)`，或 `Range` 语义自行封装 |
| 时区换算 | `instant.atZone(zone)` / `zoned.withZoneSameInstant(other)` |

**月末加减会截断**：1 月 31 日 `plusMonths(1)` 得到 2 月 28/29 日（不是 3 月 3 日），需要「保持月末」时用 `TemporalAdjusters.lastDayOfMonth()` 组合。

## 遗留 `java.util.Date`

| 意图 | ✓ |
|---|---|
| `Date` → `Instant` | `date.toInstant()` |
| `Instant` → `Date` | `Date.from(instant)` |
| `Date` → `LocalDateTime` | `LocalDateTime.ofInstant(date.toInstant(), zoneId)` |
| `LocalDateTime` → `Date` | `Date.from(ldt.atZone(zoneId).toInstant())` |
| 格式化 `Date` | `formatter.format(date.toInstant().atZone(zoneId))`，不要新建 `SimpleDateFormat` |

`Calendar` 一律不用：月份从 0 开始、可变、非线程安全，全部换成 `java.time`。
