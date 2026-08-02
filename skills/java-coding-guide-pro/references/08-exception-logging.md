# 08 · 异常、日志、随机与断言

> **日志**：**SLF4J 门面**（`org.slf4j`）+ **Logback**（固定实现）。版本按 JDK 门控（见文末「引入 SLF4J」）。
> **异常**：Hutool `ExceptionUtil`（`cn.hutool.core.exceptions`）；**断言**：Hutool `Assert`（`cn.hutool.core.lang`）。
> **随机**：Hutool `RandomUtil`（`cn.hutool.core.util`）。

## 日志规范（SLF4J 占位符，最高频违规）

| 场景 | ✗ 禁止 | ✓ 推荐 |
|---|---|---|
| 普通日志 | `log.error("x=" + x)` 字符串拼接 | `log.error("x={}", x)` 占位符 |
| 含异常 | `log.error("失败: " + e.getMessage())` | `log.error("失败: {}", id, e)` 异常作末参不占位 |
| 日志变量 | `log.info("user:" + user.toString())` | `log.info("user={}", user)`（SLF4J 自动 toString） |
| 获取 Logger | `System.out.println(...)` | `private static final Logger log = LoggerFactory.getLogger(X.class);` |

### antipattern：字符串拼接（基线测试高频违规）
```java
// ✗ 每次调用都执行拼接（即使该级别被关闭也拼接），且失去结构化
log.warn("用户不存在, id=" + id);

// ✓ 占位符 {}：仅在该级别真正输出时才格式化
log.warn("用户不存在, id={}", id);
```
> **借口拦截**「warn 一直开着，拼接差别可忽略」→ 错。占位符让代码一致、可读、且对 debug/trace 级别（常被关闭）真实省开销。团队约定**无例外**全用占位符。

### antipattern：异常日志写法
```java
// ✗ 异常对象当字符串拼接（丢堆栈）；getMessage() 可能 null
log.error("失败: " + e.getMessage());

// ✓ 异常作最后一个参数，不占 {} 位，SLF4J 自动打印堆栈
log.error("订单处理失败, orderId={}", orderId, e);
// ✓ 取异常消息用 null 安全工具
log.error("失败: {}", ExceptionUtil.getMessage(e), e);
```

## 异常处理规范

| 场景 | ✗ 禁止 | ✓ 推荐 |
|---|---|---|
| 异常消息 | `e.getMessage()`（可能 null → NPE） | `ExceptionUtil.getMessage(e)`（null 安全） |
| 根因 | 手搓循环取 cause | `ExceptionUtil.getRootCause(e)` |
| 根因消息 | 手写 | `ExceptionUtil.getRootCauseMessage(e)` |
| 堆栈转串 | 手写 | `ExceptionUtil.stacktraceToString(e)` |
| 吞异常 | `catch (Exception e) {}` 空 catch | 记日志 + 透传或包装 |
| 自定义异常 | `new RuntimeException(msg)` 无 cause | `new BizException(msg, e)` 保留 cause 链 |

### antipattern：吞异常 / 不判空 getMessage
```java
// ✗ 空 catch 吞掉问题，排查无踪
try { ... } catch (Exception e) { /* 静默吞 */ }

// ✗ getMessage() 可能 null，后续操作 NPE
String msg = e.getMessage().toLowerCase();

// ✓ 记日志 + 透传；取消息用工具方法
try {
    riskyOp();
} catch (Exception e) {
    log.error("op failed", e);
    throw e; // 或包装：throw new BizException("op failed", e);（保留 cause）
}
String msg = ExceptionUtil.getMessage(e); // null 安全
Throwable root = ExceptionUtil.getRootCause(e);
```

### 异常三级分类（阿里规约）

| 类别 | 继承关系 | 示例 | 处理策略 |
|---|---|---|---|
| 业务异常 | `RuntimeException` + 错误码 | `BizException(ErrorCode.USER_NOT_FOUND)` | catch 后返回业务提示，记 warn 不记 error |
| 系统异常 | `RuntimeException`（非业务） | `NullPointerException`/`ClassCastException` | catch 后记 error + 降级/告警 |
| 第三方异常 | 原始异常包装 | `RpcException("超时", cause)` | catch 后重试/降级 + 记 warn |

> **铁律**：自定义业务异常继承 `RuntimeException`（非 checked），携带错误码；禁止业务异常继承 `Error`。三分法的价值在于**处理策略不同**——业务异常可预期、需用户提示；系统异常不可预期、需告警；第三方异常需重试/降级。

### antipattern：InterruptedException 空吞（SonarQube S2142）
```java
// ✗ 吞掉中断状态，上层无法感知中断信号
try { Thread.sleep(1000); }
catch (InterruptedException e) { /* 静默吞 */ }

// ✓ 恢复中断状态 + 按需中止
try { Thread.sleep(1000); }
catch (InterruptedException e) {
    Thread.currentThread().interrupt();  // 恢复中断标志
    log.warn("线程被中断", e);
    return; // 或 throw，按业务决定是否中止
}
```
> **铁律**：`InterruptedException` 被捕获后中断标志会被清除。**必须**调用 `Thread.currentThread().interrupt()` 恢复中断状态，否则上层无法感知中断信号，线程池优雅关闭会失效。

### antipattern：finally 抛异常 / return（SonarQube S1181）
```java
// ✗ finally 抛异常会掩盖 try 块的原始异常
try { riskyOp(); }
finally { closeResource(); } // closeResource() 抛异常 → 原始异常丢失

// ✗ finally return 会掩盖 try 块的异常
try { return compute(); }
finally { return cached; } // 返回 cached，compute() 的异常被吞

// ✓ finally 只做清理，不抛不 return；资源关闭用 try-with-resources
try (var conn = dataSource.getConnection()) {
    riskyOp();
} // 自动关闭，异常不丢失
```
> **铁律**：`finally` 块**禁抛异常、禁 return**。finally 中抛异常会掩盖 try 块的原始异常（排查噩梦）；finally return 会吞掉 try 块的异常。资源关闭用 try-with-resources 替代手动 finally close。

### antipattern：catch 丢堆栈（SonarQube S1166）
```java
// ✗ 只记 getMessage()，丢掉完整堆栈
catch (Exception e) {
    log.error("失败: {}", e.getMessage()); // 无堆栈，排查无踪
}

// ✓ 完整异常对象作末参，SLF4J 自动打印堆栈
catch (Exception e) {
    log.error("失败, ctx={}", ctx, e); // 保留完整堆栈
}
```
> **铁律**：catch 中记日志**必须传异常对象**（作 SLF4J 最后参数），禁仅 `getMessage()`。`getMessage()` 可能 null 且丢失堆栈；完整异常对象让排查有据可循。

### antipattern：catch Throwable / Error（阿里 + SonarQube）
```java
// ✗ catch Throwable 吞掉所有错误（含 OOM/StackOverflow）
try { ... } catch (Throwable t) { log.error("err", t); }

// ✗ catch Error 吞掉 JVM 级错误
try { ... } catch (Error e) { /* 不该 catch */ }

// ✓ 按异常类型分别 catch，精准处理
try {
    riskyOp();
} catch (BizException e) {
    log.warn("业务异常: {}", e.getMessage());
    return Result.fail(e.getCode());
} catch (IOException e) {
    log.error("IO异常", e);
    throw new RpcException("IO失败", e);
}
```
> **铁律**：禁 `catch (Throwable)`/`catch (Error)`。`Error` 是 JVM 级错误（OOM/StackOverflow），应用不应 catch——应让 JVM 处理或崩溃。按异常类型分别 catch，精准处理。

### antipattern：catch 只 rethrow 不处理（SonarQube S2221）
```java
// ✗ catch 后只 rethrow，无任何处理（等于没 catch）
try { riskyOp(); }
catch (Exception e) { throw e; }

// ✓ 要么加日志/降级/包装，要么干脆不 catch
try { riskyOp(); }
catch (Exception e) {
    log.error("riskyOp failed", e);
    throw new BizException("操作失败", e); // 包装 + 保留 cause
}
// 或：不 catch，让异常自然向上传播
```
> **铁律**：catch 后只 rethrow 不做任何处理（无日志、无包装）等于没 catch——白白增加嵌套。要么加日志/降级/包装，要么删除 try-catch 让异常自然传播。

## 断言规范（Hutool Assert）

```java
// ✗ 手写 if-null-throw 样板，异常类型不统一
if (userId == null) throw new IllegalArgumentException("userId required");
if (age < 0)        throw new IllegalStateException("age < 0");

// ✓ Hutool Assert（cn.hutool.core.lang.Assert，抛 IllegalArgumentException）
Assert.notNull(order, "order required");
Assert.notNull(order, "order required, type={}", type);   // 支持 {} 占位
Assert.isTrue(order.getAmount() > 0, "amount must > 0, got {}", amount);
Assert.notBlank(name, "name required");
Assert.notEmpty(list, "list required");
```
> **注意**：Hutool `Assert` 统一抛 **`IllegalArgumentException`**（非 ValidateException）；消息参数顺序 `(被断言对象, errorMsgTemplate, Object... params)`，支持 `{}` 占位符。

## 随机数规范

**选型先行**：普通随机（抽样/测试数据）→ `RandomUtil`/`ThreadLocalRandom`；安全凭证（token/验证码/盐）→ `SecureRandom`；唯一标识（单号/ID）→ 禁随机，用单调发号器。

| 场景 | ✗ 禁止 | ✓ 推荐 |
|---|---|---|
| 随机整数 | `new Random().nextInt(max-min)+min`（边界易错）、`(int)(Math.random()*n)` 强转 | `RandomUtil.randomInt(min, max)` |
| 随机字符串 | 手搓（`Math.random()`+`String.format` / 自建字符表循环） | `RandomUtil.randomString(len)` |
| 随机纯数字 | 手搓 | `RandomUtil.randomNumbers(len)` |
| 随机 Long | `new Random().nextLong()` | `RandomUtil.randomLong()` / `randomLong(min,max)` |
| 随机元素 | 手写下标 | `RandomUtil.randomEle(list)` |
| 安全凭证 | `Random`/`ThreadLocalRandom`/`Math.random()` | `SecureRandom` / `RandomUtil.getSecureRandom()` |
| 单号/序号/ID | 任何随机数充当唯一值 | DB 序列 / Redis `INCR` / 雪花 ID |

### antipattern：Random 范围计算错（边界语义混乱）
```java
// ✗ nextInt(n) 返回 [0,n)，手写偏移常写错边界
int r = new Random().nextInt(max - min) + min;

// ✓ RandomUtil.randomInt(min, max) —— **[min, max) 半开区间，不含 max**
int r = RandomUtil.randomInt(100000, 1000000); // 6 位验证码范围（注意不含上界）
```
> **关键**：`randomInt(min, max)` 是 **[min, max)** 半开，与部分其它库（如 Spring `RandomUtils.nextInt`）的闭区间相反，迁移时务必调整。

### antipattern：Math.random() 强转充当序号（S 级，AI 生成代码高发）
```java
// ✗ 随机≠唯一：10 万空间约 400 次即 50% 碰撞（生日悖论），单号重复是事故；且 Math.random() 全局共享实例有锁竞争
String date = DateUtil.format(LocalDateTime.now(), "yyyyMMdd");
String seq = String.format("%05d", (int) (Math.random() * 100000));
String orderNo = date + seq;

// ✓ 唯一性由单调发号器承担（Redis INCR 按天自增 / DB 序列 / 雪花 ID）；now() 显式传时区（java:S8688，见 03）
String date = LocalDate.now(ZoneId.of("Asia/Shanghai")).format(DateTimeFormatter.BASIC_ISO_DATE);
String orderNo = date + String.format("%07d", redis.opsForValue().increment("order:seq:" + date));
// 仅需防猜后缀（允许重复）时：RandomUtil.randomNumbers(5)
```

### antipattern：普通随机生成安全凭证（S 级）
```java
// ✗ 线性同余可由少量输出反推种子，token/验证码可预测
String token = RandomUtil.randomString(32);      // 底层 ThreadLocalRandom，非密码学安全
int code = (int) (Math.random() * 900000) + 100000;

// ✓ SecureRandom（实例可复用；禁 new SecureRandom(seed) 固定种子播种）
SecureRandom sr = new SecureRandom();
byte[] buf = new byte[24];
sr.nextBytes(buf);
String token = Base64.getUrlEncoder().withoutPadding().encodeToString(buf);
int code = sr.nextInt(900000) + 100000;          // 6 位验证码
```

## 推荐示例

```java
private static final Logger log = LoggerFactory.getLogger(OrderService.class);

public void process(Order order) {
    Assert.notNull(order, "order required");
    Assert.isTrue(order.getAmount().signum() > 0, "amount must > 0");
    try {
        doProcess(order);
        log.info("订单完成, orderId={}, amount={}", order.getId(), order.getAmount());
    } catch (Exception e) {
        log.error("订单处理失败, orderId={}", order.getId(), e);
        throw new BizException("处理失败: " + ExceptionUtil.getMessage(e), e);
    }
}

// 验证码（安全凭证 → SecureRandom，见上节 antipattern）
int code = secureRandom.nextInt(900000) + 100000;
// 普通随机（抽样/测试数据）
int sample = RandomUtil.randomInt(0, 100);
String mockName = RandomUtil.randomString(8);
```

## 引入 SLF4J + Logback

> 坐标与 JDK 门控见 SKILL.md「必选依赖」（SLF4J 门面 + Logback 实现，按 JDK 版本选号）。实现固定 Logback，不引 Log4j2。
> **门控原因**：Logback 1.5.x 需 JDK 11+/SLF4J 2.0.1+；1.2.x 已 EOL 且**不绑定 SLF4J 2.0**——两套不可混用，否则运行期报 "no SLF4J provider"。

## 强约束提醒

- 日志**必须 SLF4J 占位符 `{}`**；禁字符串拼接；异常作最后参数不占位。
- 异常**禁吞**（空 catch）；取消息用 **`ExceptionUtil.getMessage`**（null 安全）；保留 cause 链。
- 参数校验用 **`Assert.notNull`/`isTrue`**（抛 `IllegalArgumentException`，支持 `{}` 占位）。
- 随机数用 **`RandomUtil`**；`randomInt(min,max)` 是 **[min, max) 半开**，禁手算 `Random` 范围、禁 `Math.random()` 强转。
- **随机≠唯一**：单号/序号/ID 禁用随机数，用单调发号器；token/验证码/盐必须 **`SecureRandom`**。
- **InterruptedException**：捕获后必须 `Thread.currentThread().interrupt()` 恢复中断状态（S2142）。
- **finally**：禁抛异常、禁 return（S1181）；资源关闭用 try-with-resources。
- **catch**：禁 `Throwable`/`Error`（阿里）；禁仅 `getMessage()` 丢堆栈（S1166）；禁只 rethrow 不处理（S2221）。
- **异常分类**：业务异常继承 `RuntimeException` + 错误码；系统/第三方异常处理策略不同（阿里三级分类）。
