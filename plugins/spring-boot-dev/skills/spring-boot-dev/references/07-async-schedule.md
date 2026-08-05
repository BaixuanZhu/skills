# 07 · 异步 `@Async` 与定时 `@Scheduled`

> `@Async` 默认线程池坑、自定义 `ThreadPoolTaskExecutor`、`@Scheduled` cron 表达式、自调用失效、异步异常处理。

## 一、`@Async` 基础

### 开启异步

```java
@SpringBootApplication
@EnableAsync                              // 必须开启，否则 @Async 失效
public class Application { }
```

### 基本用法

```java
@Service
public class EmailService {

    @Async                               // 异步执行（立即返回，方法在新线程跑）
    public void sendAsync(String to) {
        // 阻塞操作（发邮件 / 调第三方）
        mailSender.send(to);
    }
}
```

## 二、坑 1：默认 `SimpleAsyncTaskExecutor`（生产灾难）

**不配线程池时，`@Async` 用 `SimpleAsyncTaskExecutor`**——**每次调用新建线程，不复用**。

```java
// ✗ 默认 SimpleAsyncTaskExecutor：每次 new Thread()
@Async
public void sendAsync(String to) { ... }

// 高并发 1000 次调用 → 1000 个线程 → OOM / 线程爆炸
```

**解法：自定义 `ThreadPoolTaskExecutor`**

```java
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean("emailExecutor")                // 命名（@Async 按名引用）
    public Executor emailExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);          // 核心线程数
        executor.setMaxPoolSize(20);          // 最大线程数
        executor.setQueueCapacity(200);       // 队列容量
        executor.setKeepAliveSeconds(60);     // 空闲存活
        executor.setThreadNamePrefix("email-");// 线程名前缀（排障用）
        executor.setRejectedExecutionHandler( // 拒绝策略
            new ThreadPoolExecutor.CallerRunsPolicy()  // 由调用线程执行（反压）
        );
        executor.initialize();
        return executor;
    }
}

// 引用指定线程池
@Async("emailExecutor")                  // ✓ 用自定义线程池
public void sendAsync(String to) { ... }
```

### 拒绝策略（4 种）

| 策略 | 行为 | 适用 |
|---|---|---|
| **`AbortPolicy`**（默认） | 抛 `RejectedExecutionException` | 需感知过载并处理 |
| **`CallerRunsPolicy`** | 由调用线程执行（反压，降速） | **推荐**（不丢任务，自然限流） |
| `DiscardPolicy` | 静默丢弃 | 可接受丢任务的场景 |
| `DiscardOldestPolicy` | 丢队列最老任务 | 只关心最新任务 |

> **生产推荐**：`CallerRunsPolicy`——任务过载时由调用线程执行，自然形成反压（调用方变慢，不会无限堆积任务）。

### 线程池参数调优

- **CPU 密集型**（计算）：`maxPoolSize ≈ CPU 核数 + 1`，`queueCapacity` 小（避免堆积）。
- **IO 密集型**（网络 / DB）：`maxPoolSize ≈ CPU 核数 × 2~10`，`queueCapacity` 可大。
- **核心原则**：宁可排队（队列满再开新线程到 max），不要无限开线程。

## 三、坑 2：自调用失效（同 `@Transactional`）

同类内 `this.sendWelcome(u)` 绕过代理，`@Async` 失效（同步执行）。原因与解法同 `06-transaction.md` 坑 1（`@Async` 也是 AOP 注解）：自注入代理 / 拆到另一个 Bean。

## 四、坑 3：返回值类型

```java
@Async
public void sendVoid(String to) { ... }           // ✓ void（最常用）

@Async
public Future<String> sendFuture(String to) {     // ✓ Future / CompletableFuture
    return CompletableFuture.completedFuture("ok");
}

@Async
public String sendString(String to) { ... }       // ✗ 非 Future 返回值：调用方拿到 null
```

> `@Async` 方法直接返回普通类型时，调用方拿到的是 `null`（方法异步执行，主线程不等返回）。要拿结果，须返回 `Future` / `CompletableFuture`（**推荐 `CompletableFuture`**；`ListenableFuture` 在 Spring 6 / SpringBoot 3.x 起 `@Deprecated`）。

## 五、坑 4：异步异常不进 `@ExceptionHandler`

```java
@Async
public void sendAsync() {
    throw new RuntimeException("发送失败");        // 异步线程抛的异常
}
// 全局 @ExceptionHandler 捕获不到（不是 Controller 线程）
```

**解法 1：返回 `Future`，调用方 `.get()` 时会抛 `ExecutionException`**

```java
@Async
public CompletableFuture<Void> sendAsync() {
    return CompletableFuture.runAsync(() -> {
        mailSender.send();
    });
}
// 调用方：future.get() 抛 ExecutionException（包装原异常）
```

**解法 2：`AsyncUncaughtExceptionHandler`（void 返回值时）**

```java
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {

    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return (ex, method, params) -> {
            log.error("异步方法 {} 异常", method.getName(), ex);
        };
    }
}
```

## 六、`@Scheduled` 定时任务

### 开启定时

```java
@SpringBootApplication
@EnableScheduling                        // 必须开启
public class Application { }
```

### 基本用法

```java
@Component
public class ReportTask {

    @Scheduled(fixedRate = 5000)              // 每 5 秒（上次开始后 5 秒，不等完成）
    public void byFixedRate() { ... }

    @Scheduled(fixedDelay = 5000)             // 每 5 秒（上次完成后 5 秒）
    public void byFixedDelay() { ... }

    @Scheduled(initialDelay = 10000, fixedRate = 5000)  // 启动 10 秒后开始，每 5 秒
    public void withInitial() { ... }

    @Scheduled(cron = "0 0 2 * * ?")          // 每天凌晨 2 点
    public void byCron() { ... }
}
```

### `fixedRate` vs `fixedDelay`

| 类型 | 计时起点 | 行为 |
|---|---|---|
| `fixedRate` | 上次**开始** | 理想间隔固定；任务耗时 > 间隔 → 串行补跑（默认单线程） |
| `fixedDelay` | 上次**结束** | 相邻两次结束-开始间隔固定 |

> **坑**：`@Scheduled` 默认**单线程**——多个定时任务串行执行，一个长任务会阻塞其他任务。

## 七、坑 5：`@Scheduled` 单线程阻塞

```java
@Scheduled(fixedRate = 5000)
public void longTask() throws InterruptedException {
    Thread.sleep(10000);                  // 耗时 10 秒，每 5 秒应触发 → 实际 10 秒后才下一次
}

@Scheduled(fixedRate = 1000)
public void quickTask() { ... }           // 被上面长任务阻塞，无法并行
```

**解法：自定义 `TaskScheduler`（并行）**

```java
@Configuration
@EnableScheduling
public class ScheduleConfig implements SchedulingConfigurer {
    @Bean(destroyMethod = "shutdown")
    public ThreadPoolTaskScheduler taskScheduler() {
        ThreadPoolTaskScheduler s = new ThreadPoolTaskScheduler();
        s.setPoolSize(5);                       // 并行线程数
        s.setThreadNamePrefix("schedule-");
        s.setWaitForTasksToCompleteOnShutdown(true);
        s.setAwaitTerminationSeconds(30);
        return s;
    }
    @Override
    public void configureTasks(ScheduledTaskRegistrar r) { r.setScheduler(taskScheduler()); }
}
```

## 八、Cron 表达式

### 格式（6 字段，Spring 不含年）

```
秒 分 时 日 月 周
0  0  2  *  *  ?      → 每天凌晨 2 点
```

| 字段 | 范围 | 特殊字符 |
|---|---|---|
| 秒 | 0-59 | `,` `-` `*` `/` |
| 分 | 0-59 | 同上 |
| 时 | 0-23 | 同上 |
| 日 | 1-31 | `,` `-` `*` `?` `/` `L` `W` `C` |
| 月 | 1-12 / JAN-DEC | `,` `-` `*` `/` |
| 周 | 0-7 / SUN-SAT（0,7=周日） | `,` `-` `*` `?` `/` `L` `C` `#` |

> **Spring cron 是 6 字段，不含年份**（Linux crontab 是 5 字段，无秒）。`0 0 2 * * ?` 与 `0 0 2 * * *` 等价（日和周互斥，用 `?` 表示不限制）。

### 特殊字符

| 字符 | 含义 | 示例 |
|---|---|---|
| `*` | 任意值 | `* * * * * ?`（每秒） |
| `?` | 不限制（仅日/周） | 日和周互斥时，一个用值另一个用 `?` |
| `,` | 枚举 | `0 0 9,12,18 * * ?`（每天 9/12/18 点） |
| `-` | 范围 | `0 0 9-18 * * MON-FRI`（工作日 9-18 点每小时） |
| `/` | 步进 | `0 */5 * * * ?`（每 5 分钟） |
| `L` | 最后 | `0 0 0 L * ?`（每月最后一天 0 点）；`0 0 0 ? * 6L`（每月最后一个周五） |
| `W` | 最近工作日 | `0 0 0 15W * ?`（每月最接近 15 号的工作日） |
| `#` | 第几周 | `0 0 0 ? * 6#3`（每月第三个周五） |

### 常见 cron 速查

| 场景 | Cron |
|---|---|
| 每 5 秒 | `*/5 * * * * ?` |
| 每 5 分钟 | `0 */5 * * * ?` |
| 每小时整点 | `0 0 * * * ?` |
| 每天凌晨 2 点 | `0 0 2 * * ?` |
| 每周一 9 点 | `0 0 9 ? * MON` |
| 每月 1 号 0 点 | `0 0 0 1 * ?` |
| 工作日（周一到周五）9 点 | `0 0 9 ? * MON-FRI` |
| 每月最后一天 23 点 | `0 0 23 L * ?` |

## 九、最佳实践（仅列前文未详述项）

1. **`@Async("executor名")` 显式指定线程池**——不指定仍用默认 `SimpleAsyncTaskExecutor`。
2. **`fixedDelay` 优于 `fixedRate`**——任务耗时不确定时，`fixedDelay`（结束后等）更可控。
3. **`@Async` / `@Scheduled` 方法 `public` 非 `private` 非 `static`**——同代理原理。
4. **cron 用 `@Scheduled(cron="...")` 字符串**——Spring 原生解析，非 Quartz，不需引 Quartz 依赖。

> 自定义线程池、拒绝策略、异步异常处理、`@Scheduled` 并行、自调用失效——见上文章节。

