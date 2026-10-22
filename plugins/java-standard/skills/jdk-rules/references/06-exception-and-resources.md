# 06 · 异常与资源

## 资源关闭

| ✗ | ✓ |
|---|---|
| `try { ... } finally { conn.close(); }` | `try (Connection conn = ...) { ... }` |
| 手写多资源嵌套 finally | `try (A a = ...; B b = ...) { ... }`（关闭顺序为声明逆序） |
| `finally` 里 `close()` 且未判空 | try-with-resources 自动处理 null 资源 |
| 自己实现 `Closeable` 但 `close()` 可能抛异常 | 声明 `implements AutoCloseable`，`close()` 里不要抛业务异常 |

try-with-resources 会把 `close()` 抛的异常挂到主异常的 `suppressed` 上，不会覆盖主异常；手写 finally 则会覆盖（吞掉真正的错误）。

**不能进 try-with-resources 的**：`Connection` 来自连接池且需要归还时，某些池实现要求业务层不关闭；这类要按池的文档用，不能盲目套。

## 异常链

| ✗ | ✓ |
|---|---|
| `throw new BizException(e.getMessage())` | `throw new BizException("下单失败", e)` |
| `throw new BizException(e.toString())` | 同上；`toString` 只有类名和 message，没有栈 |
| 捕获后 `log.error(e.getMessage())` 而不传 e | `log.error("下单失败 orderId={}", id, e)` —— 异常对象必须是**最后一个参数**且不加占位符 |
| 包装后丢失原始异常 | 构造器第二个参数传 cause |

丢 cause 的后果：日志里只剩一句 message，栈帧断在最外层，定位不到根因。

## 捕获范围

| ✗ | ✓ |
|---|---|
| `catch (Exception e)` 包住整个方法 | 缩窄到实际会抛的类型，分别处理 |
| `catch (Throwable t)` | 不用；`Error` 不该被业务代码捕获 |
| 空 catch | 至少要记录并说明为什么可以忽略 |
| `catch (Exception e) { throw new RuntimeException(e); }` 只为绕过受检异常 | 声明 `throws`，或用业务异常包装并保留 cause |

**受检异常不吞**：`IOException` 被 `catch` 后既不处理也不抛，等于把失败当成功。

## 中断

```java
// ✗ 吞掉中断信号，线程无法退出
try {
    Thread.sleep(1000);
} catch (InterruptedException e) {
}

// ✓ 恢复中断标志，交由上层决定
try {
    Thread.sleep(1000);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new BizException("任务被中断", e);
}
```

`sleep` / `wait` / `join` / 阻塞队列 `take` 抛 `InterruptedException` 时会清除中断标志，必须重新设置，否则外层永远感知不到取消。

## finally

| ✗ | 原因 |
|---|---|
| `finally { return x; }` | 覆盖 try 块的返回值，也吞掉异常 |
| `finally { throw ... }` | 覆盖原始异常 |
| `finally` 里做业务判断 | finally 只做资源清理 |

## 自定义异常

| 规则 | 说明 |
|---|---|
| 继承 `RuntimeException`（业务异常） | 不强制调用方 catch，避免污染签名 |
| 继承 `Exception`（需要强制处理的场景） | 如 SDK 内部、必须显式处理的失败 |
| 类名以 `Exception` 结尾 | |
| 提供 `(String message)` 和 `(String message, Throwable cause)` 两个构造器 | |
| 不用异常做流程控制 | 「查不到就抛异常再 catch」比返回 `Optional` 慢几十倍且难读 |
| 异常信息带上下文 | `"订单 " + orderId + " 状态不允许取消"`，但**不要拼用户输入的原值**（可能含敏感信息 / 注入日志） |

## 日志

| ✗ | ✓ |
|---|---|
| `log.error("失败：" + e)` | `log.error("失败", e)` |
| `log.error("id=" + id + " 失败", e)` | `log.error("id={} 失败", id, e)` |
| `log.error(e.getMessage())` | 同上，异常对象作最后参数 |
| 每层都 `log.error` 再往上抛 | 只在能处理的那一层记，否则同一异常打多遍 |
| `e.printStackTrace()` | `log.error("...", e)` |
| INFO 级别打全量对象 | `log.info("下单 orderId={} amount={}", id, amount)`，敏感字段脱敏 |

占位符 `{}` 只有 SLF4J 风格支持；`String.format` 风格（`%s`）在 SLF4J 里不会替换。

## 坑

- **异常在 `catch` 里被吞且无日志**：最常见的事故来源，PMD 的 `EmptyCatchBlock` 只能抓完全空的，有语句但无处理抓不到。
- **`Optional` 别用来表示异常**：`orElseThrow` 是给「无值是异常」的场景；「无值是正常分支」用 `orElse`。
- **`try` 块过大**：把不相关的代码一起包住，导致误捕获；`try` 只包住真正可能失败的那几行。
- **`assert` 不能用于参数校验**：默认关闭，生产不生效。
- **`Error` 与 `RuntimeException` 的区别**：`OutOfMemoryError`、`StackOverflowError` 属于 `Error`，业务代码不该 catch；`Exception` 下才是可处理的失败。
