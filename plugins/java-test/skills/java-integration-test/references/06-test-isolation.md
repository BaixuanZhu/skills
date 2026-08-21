# 06 · 测试隔离与外部依赖

> 测试隔离是集成测试的头号难题。`@Transactional` 回滚在 `RANDOM_PORT` 下静默失效；外部 API 真调导致测试不可重复。本文件固化隔离陷阱与正确方案。示例注解 `@MockitoBean` 需 Boot 3.4+（≤3.3 写作 `@MockBean`，4.0 已移除旧注解——版本口径见 `02`）。

## @Transactional 回滚

### MOCK 模式：回滚有效

`@SpringBootTest` 默认 `webEnvironment=MOCK`——HTTP 请求在测试线程内通过 MockMvc 分发，`@Transactional` 包裹整个测试方法，结束后自动回滚。

```java
@SpringBootTest
@Transactional
class ServiceLayerTest {
    @Autowired OrderRepository orderRepository;
    @Autowired OrderService orderService;

    @Test
    void should_create_order() {
        orderService.create(request);  // 写入 DB

        // 测试方法结束后 @Transactional 回滚 → DB 干净
        // 下一个测试方法从空表开始
    }
}
```

### RANDOM_PORT 模式：回滚失效（头号陷阱）

`@SpringBootTest(webEnvironment=RANDOM_PORT)` 时，HTTP 请求走**真实 Servlet 容器线程**，与测试线程**不在同一事务**。测试线程的 `@Transactional` 只回滚测试线程的事务，HTTP 请求线程的提交不受影响。

```java
// ✗ @Transactional 在 RANDOM_PORT 下不回滚
@SpringBootTest(webEnvironment = RANDOM_PORT)
@Transactional
class HttpApiTest {
    @Test
    void should_create_order() {
        given().body(request).when().post("/api/orders");  // 走容器线程
        // 测试方法结束 → 测试线程事务回滚
        // 但 HTTP 请求在容器线程中已提交 → 数据残留！
    }
}
```

> **这是最隐蔽的隔离坑**：测试"绿"但数据库有残留数据，下一个测试依赖干净状态时突然失败——"上次跑过了这次报错"的典型表现。

### RANDOM_PORT 下的替代方案

```java
// ✓ 方案 1：@Sql 清理（推荐）
@SpringBootTest(webEnvironment = RANDOM_PORT)
class HttpApiTest {
    @Test
    @Sql(scripts = "/sql/cleanup-orders.sql",
         executionPhase = Sql.ExecutionPhase.AFTER_TEST_METHOD)
    void should_create_order() {
        given().body(request).when().post("/api/orders").then().statusCode(201);
        // 测试后执行 cleanup-orders.sql：DELETE FROM orders;
    }
}

// ✓ 方案 2：Testcontainers + 重置
@SpringBootTest(webEnvironment = RANDOM_PORT)
class HttpApiTest {
    @Container @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17.11-alpine");

    @Autowired JdbcTemplate jdbcTemplate;  // Boot 自动配置的 Bean

    @AfterEach
    void cleanup() {
        // 直接清理——容器是测试专用，重置不影响生产
        jdbcTemplate.execute("TRUNCATE TABLE orders, order_items CASCADE");
    }
}
```

### @Transactional 回滚失效的完整场景

| 场景 | 回滚是否有效 | 原因 |
|---|---|---|
| `MOCK` 模式 + `@Transactional` | ✓ | 同线程事务 |
| `RANDOM_PORT` + `@Transactional` | **✗** | HTTP 请求走容器线程，非测试线程事务 |
| `@Async` 异步方法 + `@Transactional` | **✗** | 异步线程独立事务，测试方法结束时异步事务可能未完成 |
| 多线程 / `CompletableFuture` | **✗** | 子线程独立事务 |
| `@TransactionalEventListener(AFTER_COMMIT)` | **✗** | 事件在提交后触发，回滚不取消 |

> 异步场景：测试方法结束时，异步方法可能尚未执行或正在执行中。需用 `Awaitility` 等待异步完成后再断言，并单独清理数据。

## @Sql：测试数据管理

```java
// 测试前插入数据
@Test
@Sql(scripts = "/sql/insert-test-orders.sql",
     executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
void should_query_existing_orders() {
    // 表中已有 insert-test-orders.sql 插入的数据
    given().when().get("/api/orders").then().statusCode(200).body("data.size()", equalTo(5));
}

// 测试后清理
@Test
@Sql(scripts = "/sql/cleanup-orders.sql",
     executionPhase = Sql.ExecutionPhase.AFTER_TEST_METHOD)
void should_not_pollute_other_tests() {
    given().body(request).when().post("/api/orders").then().statusCode(201);
    // 测试后 cleanup 清理
}
```

`@Sql` 脚本路径默认在 `src/test/resources/sql/` 下。

### @Sql 与 @Transactional 共存

```java
// MOCK 模式：@Sql(BEFORE) 插入 + @Transactional 回滚 = 测试后自动清理（无需 AFTER）
@SpringBootTest
@Transactional
@Sql(scripts = "/sql/insert-test-orders.sql")  // BEFORE_TEST_METHOD
class ServiceTest {
    // @Sql 插入的数据在 @Transactional 内 → 测试方法结束自动回滚
}
```

> `MOCK` + `@Transactional`：`@Sql(BEFORE)` 插入的数据随事务回滚清理，不需要 `AFTER`。`RANDOM_PORT`：必须显式 `@Sql(AFTER)` 清理。

## @DirtiesContext：最后手段

```java
@SpringBootTest
@DirtiesContext(classMode = ClassMode.AFTER_CLASS)
class StatefulBeanTest { }
```

| `classMode` | 时机 | 代价 |
|---|---|---|
| `BEFORE_EACH_TEST_METHOD` | 每个测试方法前 | ×N 重建 Context（极慢） |
| `AFTER_EACH_TEST_METHOD` | 每个测试方法后 | ×N 重建 Context（极慢） |
| `AFTER_CLASS` | 类结束后 | 1 次重建（可接受） |

> **优先级**：`@Sql` / `@Transactional` > `@DirtiesContext`。只有 Bean 内部状态被测试修改且无法重置时才用。典型场景：测试修改了 `@ConfigurationProperties` 绑定的单例 Bean 的内部状态。

## 数据库重置策略对比

| 策略 | 适用模式 | 速度 | 干净度 | 适合 |
|---|---|---|---|---|
| `@Transactional` 回滚 | MOCK | 零开销 | ✓ | 跨层 Service 测试 |
| `@Sql(AFTER)` | RANDOM_PORT | 快 | ✓ | HTTP API 测试 |
| `TRUNCATE` in `@AfterEach` | RANDOM_PORT + Testcontainers | 快 | ✓ | E2E 多表测试 |
| Flyway `clean` + `migrate` | RANDOM_PORT | 慢 | ✓✓ | 需验证迁移脚本（不常用） |
| `@DirtiesContext` | 任意 | 极慢 | ✓ | Bean 状态污染（最后手段） |

## WireMock：外部 HTTP 依赖隔离

### 为什么不用 @MockitoBean 替代外部调用

| | `@MockitoBean` | WireMock |
|---|---|---|
| 替换层级 | 替换 Spring Bean | 替换 HTTP 端点 |
| 测到什么 | Bean 调用逻辑 | HTTP 序列化 / 反序列化 / 超时 / 重试 |
| 适合 | 内部 Bean 依赖 | 外部 HTTP API |

> `@MockitoBean` 替换 `PaymentClient` Bean → 跳过 HTTP 序列化。WireMock 起 Mock Server → `PaymentClient` 真发 HTTP，WireMock 返回可控响应。后者能测到 JSON 序列化、连接超时、重试逻辑。

### 基本用法

```xml
<dependency>
    <groupId>org.wiremock</groupId>
    <artifactId>wiremock-standalone</artifactId>
    <version>3.13.2</version>
    <scope>test</scope>
</dependency>
```

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
class PaymentIntegrationTest {

    static WireMockServer wireMock = new WireMockServer(
        options().dynamicPort());  // 随机端口，避免并行冲突

    @DynamicPropertySource
    static void configure(DynamicPropertyRegistry registry) {
        wireMock.start();
        registry.add("payment.api.url", wireMock::baseUrl);
    }

    @AfterEach
    void resetWireMock() {
        wireMock.resetAll();  // 清理所有 stub，防止跨测试污染
    }

    @Test
    void should_handle_payment_success() {
        // stub 外部支付 API 返回成功
        wireMock.stubFor(post(urlEqualTo("/api/charge"))
            .willReturn(okJson("{\"code\":0,\"data\":{\"paymentId\":\"PAY123\"}}")));

        given()
            .body(Map.of("amount", 199, "method", "ALIPAY"))
        .when()
            .post("/api/orders/1/pay")
        .then()
            .statusCode(200)
            .body("data.paymentId", equalTo("PAY123"));
    }

    @Test
    void should_retry_when_payment_timeout() {
        // stub 超时 → 测重试逻辑
        wireMock.stubFor(post(urlEqualTo("/api/charge"))
            .willReturn(aResponse().withFixedDelay(5000)
                .withStatus(503)));

        given()
            .body(Map.of("amount", 199, "method", "ALIPAY"))
        .when()
            .post("/api/orders/1/pay")
        .then()
            .statusCode(200);  // 重试后成功（需有重试逻辑 + 第二个 stub 返回成功）
    }
}
```

### WireMock 关键能力

| 能力 | 用途 |
|---|---|
| `willReturn(okJson(...))` | 返回可控 JSON 响应 |
| `withFixedDelay(ms)` | 模拟延迟（测超时 / 重试） |
| `withStatus(500/503)` | 模拟服务端错误 |
| `withFault(...)` | 模拟连接断开 |
| `verify(postRequestedFor(...))` | 验证请求是否发出、发了几次 |
| `scenario(...)` | 有状态 stub（首次返回 401，第二次返回 200） |
| `dynamicPort()` | 随机端口（并行测试不冲突） |

### @MockitoBean vs WireMock 选择

**判据**：内部 Bean 依赖 → `@MockitoBean`；外部 HTTP API（序列化 / 超时 / 重试）→ WireMock（机制对比见上表）。

## 异步测试与 Awaitility

### 为什么不用 Thread.sleep

```java
// ✗ 固定等待——要么等太久（慢），要么等不够（flaky）
@Test
void should_process_async_order() {
    orderService.processAsync(orderId);
    Thread.sleep(2000);  // 等多久？不知道。快机器 200ms 够了，CI 上 2s 不够
    assertThat(orderRepository.findById(orderId)).isCompleted();
}

// ✓ Awaitility——轮询直到条件满足或超时
@Test
void should_process_async_order() {
    orderService.processAsync(orderId);

    await()
        .atMost(Duration.ofSeconds(5))           // 最多等 5 秒
        .pollInterval(Duration.ofMillis(100))     // 每 100ms 检查一次
        .untilAsserted(() -> {                   // 条件：断言通过
            Order order = orderRepository.findById(orderId).orElseThrow();
            assertThat(order.getStatus()).isEqualTo(OrderStatus.COMPLETED);
        });
}
```

> `Thread.sleep` 的本质问题：等待时间与实际执行时间无关——快环境白等，慢环境不够等。Awaitility 轮询直到条件满足，快环境毫秒级通过，慢环境有超时兜底。

### 依赖

```xml
<dependency>
    <groupId>org.awaitility</groupId>
    <artifactId>awaitility</artifactId>
    <scope>test</scope>
</dependency>
```

> Spring Boot 3.x 的 `spring-boot-starter-test` 已包含 Awaitility，不需要单独引入。

### 常用模式

```java
// 模式 1：untilAsserted —— 最推荐（断言失败时报错信息清晰）
await()
    .atMost(Duration.ofSeconds(3))
    .untilAsserted(() -> {
        assertThat(redisTemplate.opsForValue().get("order:" + orderId))
            .isEqualTo("COMPLETED");
    });

// 模式 2：until —— 返回 boolean
await()
    .atMost(Duration.ofSeconds(3))
    .until(() -> orderService.isProcessed(orderId));

// 模式 3：等待事件发布（ApplicationEvent）
CountDownLatch eventReceived = new CountDownLatch(1);
@EventListener
void onOrderCompleted(OrderCompletedEvent event) {
    if (event.getOrderId() == orderId) eventReceived.countDown();
}
// 注册 listener 后触发异步操作
orderService.processAsync(orderId);
await().atMost(Duration.ofSeconds(3)).until(() -> eventReceived.getCount() == 0);
```

### 与 @Transactional 回滚失效的关系

异步测试是 `@Transactional` 回滚失效的高频场景（见上方失效表）。正确做法：

```java
// ✓ 异步测试：Awaitility 等待 + @AfterEach 清理
@SpringBootTest
class AsyncOrderTest {
    @Autowired OrderRepository orderRepository;
    @Autowired JdbcTemplate jdbcTemplate;

    @Test
    void should_complete_async_processing() {
        orderService.processAsync(orderId);

        await().atMost(Duration.ofSeconds(5)).untilAsserted(() ->
            assertThat(orderRepository.findById(orderId))
                .get().extracting(Order::getStatus)
                .isEqualTo(OrderStatus.COMPLETED));

        // 异步线程已提交事务 → 数据残留 → 必须显式清理
    }

    @AfterEach
    void cleanup() {
        jdbcTemplate.execute("TRUNCATE TABLE orders CASCADE");
    }
}
```

> 异步方法在独立线程中提交事务，`@Transactional` 回滚无法触及。用 Awaitility 等异步完成并断言，再用 `@AfterEach` 显式清理。

## Redis / MongoDB 数据清理

```java
// Redis：@AfterEach 清空
@SpringBootTest
class RedisTest {
    @Autowired RedisTemplate<String, String> redis;

    @AfterEach
    void cleanup() {
        redis.getConnectionFactory().getConnection().flushAll();
    }
}

// MongoDB：@AfterEach 清空
@SpringBootTest
class MongoTest {
    @Autowired MongoTemplate mongo;

    @AfterEach
    void cleanup() {
        mongo.getDb().drop();
    }
}
```

> Spring Boot 3.1+ + Testcontainers 用 `@ServiceConnection` 启动 Redis/MongoDB 容器，`@AfterEach` 清理数据即可——容器是测试专用，不影响生产。
