# 02 · Spring Boot Test 核心

> `@SpringBootTest` 配置、`webEnvironment` 选项、MockMvc / WebTestClient / RestTestClient（Boot 4+，TestRestTemplate 迁移）选择、`@MockitoBean` 在集成测试中的用法。

## @SpringBootTest 基础

`@SpringBootTest` 启动完整 Spring Application Context（生产代码的 Bean 全部加载），是集成测试的主力注解。

```java
@SpringBootTest
class MyIntegrationTest {
    @Autowired MyService service;  // 注入真实 Bean（非 Mock）

    @Test
    void should_work_with_real_beans() {
        // service 的依赖全是真实的——DB / Redis 等需 Testcontainers 或 @MockitoBean 处理
    }
}
```

## webEnvironment 决策表

| 模式 | HTTP？ | MockMvc？ | `@Transactional` 回滚？ | 适用场景 |
|---|---|---|---|---|
| `MOCK`（默认） | 否（Mock Servlet） | ✓ 自动配置 | ✓ 有效 | Service 跨层协作；不需要真实 HTTP 的集成测试 |
| `RANDOM_PORT` | ✓ 真实（随机端口） | ✗ | **✗ 失效** | 完整 HTTP API 测试（含过滤器 / 序列化）；REST Assured / WebTestClient |
| `DEFINED_PORT` | ✓ 真实（固定端口） | ✗ | **✗ 失效** | 需要固定端口（外部工具对接）——一般不用，端口冲突风险 |
| `NONE` | 否 | ✗ | ✓ 有效 | 只启动 Context，不做 Web 测试（批处理 / 定时任务） |

> **`@Transactional` 在 `RANDOM_PORT` 下失效**：HTTP 请求走 Servlet 容器线程，与测试线程不在同一事务，回滚失效。这是最隐蔽的隔离坑——根因 + 替代方案见 `references/06`。

```java
// RANDOM_PORT 模式：@Transactional 回滚失效，需 @Sql(AFTER) 清理
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class HttpApiTest {
    @LocalServerPort int port;

    @Test
    @Sql(scripts = "/sql/cleanup.sql", executionPhase = AFTER_TEST_METHOD)
    void should_test_real_http() {
        // HTTP 请求走真实 Servlet 容器 → @Transactional 无效
    }
}
```

> MOCK 模式下 `@Transactional` 回滚有效的完整示例见 `references/06`。

## MockMvc vs WebTestClient vs RestTestClient

| 工具 | 模式 | 适合 | 真实 HTTP？ | 响应式支持 |
|---|---|---|---|---|
| **MockMvc** | MOCK | Spring MVC（Servlet）测试，最轻量 | 否（进程内 Mock Servlet） | ✗ |
| **WebTestClient** | RANDOM_PORT | Servlet + Reactive 通用，流式断言 | ✓ | ✓ |
| **RestTestClient**（Boot 4+） | MOCK / RANDOM_PORT | Servlet 统一客户端：MOCK 底层走 MockMvc、RANDOM_PORT 直打真实服务器，流式断言 | 按 webEnvironment | ✗ |
| **TestRestTemplate**（≤3.x） | RANDOM_PORT | Servlet 简单场景；Boot 4 起废弃（遗留项目才见） | ✓ | ✗ |

**选择规则**：
- `MOCK` 模式 → MockMvc（最轻量，秒级）。
- `RANDOM_PORT`：Boot 4+ Servlet 栈 → RestTestClient；响应式栈（WebFlux）→ WebTestClient；复杂多步断言（given/when/then）→ REST Assured（见 `05`）。
- TestRestTemplate 仅限 Boot ≤3.x 遗留项目的简单 GET/POST 断言；Boot 4+ 新测试一律 RestTestClient（迁移见下节），复杂场景用 REST Assured。

### MockMvc（MOCK 模式）

```java
@SpringBootTest
@AutoConfigureMockMvc
class ControllerTest {
    @Autowired MockMvc mockMvc;

    @Test
    void should_return_400_when_invalid_input() throws Exception {
        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"qty\": 0}"))  // qty=0 无效
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.errors[0].field").value("qty"));
    }
}
```

> MockMvc 走 Spring MVC 管道（DispatcherServlet → Controller → Validator → ExceptionHandler），但**不开真实 HTTP socket**——无序列化差异、无网络层过滤器。需要测试 HTTP 过滤器 / 序列化用 `RANDOM_PORT`。**Boot 4 起 `@SpringBootTest` 不再自动配置 MockMvc——必须显式 `@AutoConfigureMockMvc`**（≤3.x 省略也能注入是旧行为）。

### WebTestClient（RANDOM_PORT）

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@AutoConfigureWebTestClient
class ApiTest {
    @Test
    void should_create_order(WebTestClient client) {
        client.post().uri("/api/orders")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(Map.of("productId", 1, "qty", 2))
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .jsonPath("$.data.orderId").isNotEmpty()
            .jsonPath("$.data.totalAmount").isEqualTo("199.00");
    }
}
```

### RestTestClient（Boot 4+，替代 TestRestTemplate）

Spring Boot 4 起 `TestRestTemplate` 废弃：从 `spring-boot-test` 拆到独立模块，升级 Boot 4 后原有 `@Autowired TestRestTemplate` **直接注入失败**（补依赖才恢复，且官方方向是废弃）。新测试用 `RestTestClient`。

```xml
<!-- pom.xml（test scope，版本随 Boot 4 BOM） -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-resttestclient</artifactId>
    <scope>test</scope>
</dependency>
```

> ⚠️ 坐标是 `spring-boot-resttestclient`——**没有** `spring-boot-starter-resttestclient` 这个 starter（部分教程讹传，Maven Central 404）。不加依赖则 `RestTestClient` 与 `TestRestTemplate` 都无法解析。

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@AutoConfigureRestTestClient  // Boot 4：HTTP 测试客户端不再自动配置，须显式开启
class ApiTest {
    @Autowired RestTestClient restTestClient;  // RANDOM_PORT → 直打真实服务器

    @Test
    void should_create_order() {
        restTestClient.post().uri("/api/orders")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(Map.of("productId", 1, "qty", 2))
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .jsonPath("$.data.orderId").isNotEmpty();
    }
}
```

**TestRestTemplate → RestTestClient 迁移要点**：
- 注入：`@Autowired TestRestTemplate` → `@Autowired RestTestClient` + 类上 `@AutoConfigureRestTestClient`。
- 遗留项目暂留 TestRestTemplate 的代价：Boot 4 下类移到 `org.springframework.boot.resttestclient.TestRestTemplate`（原 import 失效），且需类上 `@AutoConfigureTestRestTemplate` + runtime 依赖 `spring-boot-restclient`——改动不比迁移到 RestTestClient 少，不推荐。
- API 风格：命令式 `getForObject` / `exchange` → 流式 `get().uri().exchange().expectStatus().expectBody()`（与 WebTestClient 一致；要拿反序列化对象用 `.expectBody(T.class).returnResult().getResponseBody()`）。
- 双模式：默认 `MOCK`（MockMvc 在 classpath）底层走 MockMvc，不开真实 socket；`RANDOM_PORT` 直打真实服务器——同一 API 覆盖两种环境。
- 响应式栈（WebFlux）不用它——仍用 WebTestClient。

## @MockitoBean vs @Mock（关键区分）

| | `@Mock` | `@MockitoBean` |
|---|---|---|
| 来源 | Mockito 原生 | Spring Framework 6.2+（`org.springframework.test.context.bean.override.mockito`） |
| 范围 | 纯单元测试 | 切片 / 集成测试 |
| 作用 | 替换被测对象的依赖字段 | 替换 Spring Context 中的 Bean 定义 |
| 容器 | 不起容器 | 启动 / 重建 Spring Context |
| 开销 | 毫秒 | 秒级（首次启动 Context） |

```java
// 纯单测 → @Mock（→ java-unit-test）
@ExtendWith(MockitoExtension.class)
class OrderServiceUnitTest {
    @Mock OrderRepository repo;      // Mockito mock，不起容器
    @InjectMocks OrderService service;
}

// 集成测试 → @MockitoBean
@SpringBootTest
class OrderIntegrationTest {
    @MockitoBean PaymentClient paymentClient;  // 替换 Context 中的 PaymentClient Bean
    @Autowired OrderService orderService;     // 真实 Bean，但 PaymentClient 被 mock
}
```

> **版本口径**：Boot 3.4+ 用 `@MockitoBean` / `@MockitoSpyBean`；旧的 `@MockBean` / `@SpyBean` 是 Boot ≤3.3 写法（3.4 废弃，**4.0 已移除——编译错误**）。字段上可直接替换。关键差异：**`@MockitoBean` 不能声明在 `@Configuration` / `@TestConfiguration` 类里**（旧 `@MockBean` 可以）——跨测试类共享 mock 改为测试类上重复标注 `@MockitoBean(types = {...})` 或自定义组合注解。

> **`@MockitoBean` 配置变化会重建 Context（十秒级）**——完整缓存机制与统一配置示例见下文「Context 缓存机制」。

### @MockitoSpyBean：部分真实 + 部分 mock

```java
// 真实 OrderService 运行，但 spy 其 sendNotification 方法
@SpringBootTest
class NotificationTest {
    @MockitoSpyBean OrderService orderService;

    @Test
    void should_call_notification() {
        orderService.createOrder(request);  // 真实执行 createOrder
        verify(orderService).sendNotification(any());  // 验证 sendNotification 被调用
    }
}
```

> `@MockitoSpyBean` 对真实 Bean 创建 spy——真实方法照常执行，但可 `verify` 调用 / `doReturn` 桩特定方法。与 `@MockitoBean` 区别：`@MockitoBean` 完全替换（所有方法返回默认值），`@MockitoSpyBean` 保留真实行为。

## @TestConfiguration

```java
@TestConfiguration
class TestConfig {
    @Bean
    @Primary  // 覆盖生产配置的同名 Bean
    Clock fixedClock() {
        return Clock.fixed(Instant.parse("2026-01-01T00:00:00Z"), ZoneOffset.UTC);
    }
}

@SpringBootTest
@Import(TestConfig.class)  // 导入测试配置
class TimeSensitiveTest {
    @Autowired Clock clock;  // 注入固定时钟
}
```

> 用途：注入测试专用 Bean（固定 Clock / Mock 外部客户端 / 测试数据初始化器），不污染生产配置。`@TestConfiguration` 不会被 `@ComponentScan` 扫描，须显式 `@Import`。

## @ActiveProfiles

```java
@SpringBootTest
@ActiveProfiles("test")  // 激活 application-test.yml
class MyTest { }
```

`application-test.yml` 放测试专用配置（低连接池 / Testcontainers 端口 / mock 端点）。

## Context 缓存机制

Spring Test 会缓存 ApplicationContext——**相同配置的测试类共享同一个 Context 实例**。缓存命中 = 零启动开销。

**什么会破坏缓存**（导致重建 Context，每次十秒）：
- 不同的 `@MockitoBean` / `@MockitoSpyBean` 组合
- 不同的 `@SpringBootTest` 属性（`properties` / `webEnvironment`）
- 不同的 `@ActiveProfiles`
- `@DirtiesContext`（显式标记 Context 被污染）

**优化策略**：统一所有测试类的 mock 配置和 profile → 共享一个 Context → 只启动一次。

```java
// ✗ 每个测试类 mock 不同 Bean → 3 个 Context → 30s 启动
class TestA { @MockitoBean Repo repo; }
class TestB { @MockitoBean Service service; }
class TestC { @MockitoBean Repo repo; @MockitoBean Service service; }

// ✓ 统一 Base 类 → 1 个 Context → 10s 启动
@SpringBootTest
abstract class BaseIntegrationTest {
    @MockitoBean Repo repo;
    @MockitoBean Service service;
}
class TestA extends BaseIntegrationTest { }
class TestB extends BaseIntegrationTest { }
```

## @DirtiesContext：核弹级重置

```java
@SpringBootTest
@DirtiesContext(classMode = ClassMode.AFTER_EACH_TEST_METHOD)
class StatefulTest { }
```

> **代价**：每个测试方法后**重建整个 ApplicationContext**（十秒级）。仅用于 Bean 内部状态被测试修改且无法通过 `@Sql` / `@Transactional` 重置的场景。默认不用，优先其他隔离方案（见 `06`）。
