# 06 · 测试隔离与外部依赖

> 测试隔离是集成测试的头号难题。`@Transactional` 回滚在 `RANDOM_PORT` 下静默失效；外部 API 真调导致测试不可重复。本文件固化隔离陷阱与正确方案。示例注解 `@MockitoBean` 需 Boot 3.4+（≤3.3 写作 `@MockBean`，4.0 已移除旧注解——版本口径见 `02`）。

## @Transactional 回滚

**MOCK 模式（默认）有效**：HTTP 请求在测试线程内通过 MockMvc 分发，`@Transactional` 包裹整个测试方法，结束自动回滚——写接口的 MOCK 测试默认零清理成本。

**RANDOM_PORT 模式失效（头号陷阱）**：HTTP 请求走**真实 Servlet 容器线程**，与测试线程不在同一事务——测试线程回滚管不到请求线程的提交。测试"绿"但库里有残留，下一个依赖干净状态的用例突然红（"上次跑过了这次报错"的典型根因）。

### 失效场景全集

| 场景 | 回滚是否有效 | 原因 |
|---|---|---|
| `MOCK` 模式 + `@Transactional` | ✓ | 同线程事务 |
| `RANDOM_PORT` / `DEFINED_PORT` + `@Transactional` | **✗** | HTTP 请求走容器线程 |
| `@Async` 异步方法 + `@Transactional` | **✗** | 异步线程独立事务，测试结束时可能未完成 |
| 多线程 / `CompletableFuture` | **✗** | 子线程独立事务 |
| `@TransactionalEventListener(AFTER_COMMIT)` | **✗** | 事件在提交后触发 |

### RANDOM_PORT 的替代清理

- **`@Sql(AFTER_TEST_METHOD)`**：注解挂测试方法上，执行清理脚本（`src/test/resources/sql/`）。
- **Testcontainers + `@AfterEach` TRUNCATE**：容器是测试专用的，直接清空不影响任何环境——多表场景 `TRUNCATE TABLE a, b CASCADE` 一次清。
- `@Sql(BEFORE)` 插入的预置数据：MOCK + `@Transactional` 下随事务回滚（无需 AFTER）；RANDOM_PORT 下必须显式 AFTER 清理。

## 数据库重置策略对比

| 策略 | 适用模式 | 速度 | 适合 |
|---|---|---|---|
| `@Transactional` 回滚 | MOCK | 零开销 | Service 集成测试（真实依赖层，MOCK 模式） |
| `@Sql(AFTER)` | RANDOM_PORT | 快 | HTTP API 测试 |
| `TRUNCATE` in `@AfterEach` | RANDOM_PORT + Testcontainers | 快 | E2E 多表测试 |
| Flyway `clean` + `migrate` | RANDOM_PORT | 慢 | 验证迁移可重放（不常用） |
| `@DirtiesContext` | 任意 | 极慢 | Bean 状态污染（最后手段，代价见 `02`） |

## WireMock：外部 HTTP 依赖隔离

**判据**：内部 Bean 依赖 → `@MockitoBean`（跳过 HTTP 层）；**外部 HTTP API**（要测序列化 / 超时 / 重试）→ WireMock——`PaymentClient` 真发 HTTP，WireMock 起 Mock Server 返回可控响应。

| 能力 | 用途 |
|---|---|
| `willReturn(okJson(...))` | 可控 JSON 响应 |
| `withFixedDelay(ms)` / `withStatus(500/503)` | 模拟延迟 / 服务端错误（测超时 / 重试） |
| `withFault(...)` | 模拟连接断开 |
| `verify(postRequestedFor(...))` | 验证请求是否发出、发了几次 |
| `scenario(...)` | 有状态 stub（首次 401，第二次 200） |
| `dynamicPort()` | 随机端口（并行测试不冲突） |

```java
static WireMockServer wireMock = new WireMockServer(options().dynamicPort());

@DynamicPropertySource
static void configure(DynamicPropertyRegistry registry) {
    wireMock.start();
    registry.add("payment.api.url", wireMock::baseUrl);
}

@AfterEach
void resetWireMock() {
    wireMock.resetAll();   // 清 stub，防跨测试污染
}
```

依赖：`org.wiremock:wiremock-standalone`（test scope，版本取当前稳定）。

## 异步测试与 Awaitility

**不用 `Thread.sleep`**：等待时长与实际执行时间无关——快机器白等，慢机器不够等，必然 flaky。Awaitility 轮询直到条件满足（快环境毫秒级通过，慢环境有超时兜底）：

```java
await()
    .atMost(Duration.ofSeconds(5))
    .pollInterval(Duration.ofMillis(100))
    .untilAsserted(() -> assertThat(order.getStatus()).isEqualTo(COMPLETED));
```

- 首选 `untilAsserted`（失败时报错信息清晰）；返回 boolean 用 `until(() -> ...)`。
- 依赖 `org.awaitility:awaitility`（test scope）；Boot 3.x 的 `spring-boot-starter-test` 已传递。
- 异步线程已独立提交事务 → 数据残留，`untilAsserted` 断言完仍需 `@AfterEach` 显式清理（上表）。

## Redis / MongoDB 清理

容器是测试专用，直接清空：Redis `redis.getConnectionFactory().getConnection().flushAll()`；MongoDB `mongo.getDb().drop()`（`@AfterEach`）。
