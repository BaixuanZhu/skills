# 03 · 切片测试

> 切片测试只加载某一层（Web / JPA / JSON），不起全量 Context——秒级启动，定位精准。当不需要跨层协作时，切片优于全量 `@SpringBootTest`。

## 切片 vs 全量：何时用什么

| 你要测的 | 切片？ | 全量？ | 理由 |
|---|---|---|---|
| Controller 参数校验 / 路由 / 异常处理 | `@WebMvcTest` | | 只需 Web 层，Service 可以 mock |
| Controller + Service 联调 | | `@SpringBootTest` | 需要跨层真实协作 |
| Repository SQL / 查询 / 分页 | `@DataJpaTest` | | 只需 JPA 层 + 真实 DB |
| JSON 序列化 / 反序列化 | `@JsonTest` | | 只需 Jackson |
| RestTemplate / WebClient 调用 | `@RestClientTest` | | 只需 HTTP 客户端 + Mock Server |
| Controller → Service → Repository → DB 全链路 | | `@SpringBootTest` | 需要所有层协作 |

> **原则**：能切片就切片。全量 `@SpringBootTest` 启动整个 Context（十秒级），切片只启动一层（秒级）。

## @WebMvcTest：Web 层切片

只加载 Spring MVC 相关组件（Controller / `@ControllerAdvice` / `Filter` / `Validator`），**不加载 Service / Repository / 配置类**。

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mockMvc;

    @MockBean OrderService orderService;  // Service 不在切片范围，必须 mock

    @Test
    void should_return_400_when_qty_is_zero() throws Exception {
        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"productId\":1,\"qty\":0}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.errors[0].field").value("qty"));
    }

    @Test
    void should_return_order_when_valid() throws Exception {
        when(orderService.create(any())).thenReturn(new OrderDTO(1L, "CREATED"));

        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"productId\":1,\"qty\":2}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.data.status").value("CREATED"));
    }
}
```

### 隐蔽坑：@WebMvcTest 不加载 Service

`@WebMvcTest` **只加载 `@Controller` / `@RestController`**，不扫描 `@Service` / `@Repository` / `@Component`。Controller 依赖的 Service 不会被注入 → 启动报 `NoSuchBeanDefinitionException`。

**解法**：
- `@MockBean` Service（最常见）——测试 Controller 逻辑，Service 行为可控。
- `@Import(MyService.class)` ——需要真实 Service 逻辑时。

```java
// ① Mock Service（推荐：测 Controller 逻辑）
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @MockBean OrderService orderService;  // mock → 控制返回值
}

// ② Import 真实 Service（需要真实业务逻辑时）
@WebMvcTest(OrderController.class)
@Import(OrderService.class)  // 加载真实 Service，但其依赖仍需 mock
class OrderControllerWithRealServiceTest {
    @MockBean OrderRepository orderRepository;  // Service 的依赖 mock
}
```

### @WebMvcTest 与 Security

项目用了 Spring Security 时，`@WebMvcTest` 会加载 Security 配置（`SecurityFilterChain`），未认证请求返回 401。

```java
// 方案 1：排除 Security（测 Controller 逻辑，不管鉴权）
@WebMvcTest(controllers = OrderController.class,
            excludeAutoConfiguration = SecurityAutoConfiguration.class)

// 方案 2：加 @WithMockUser 模拟认证用户
@WebMvcTest(OrderController.class)
class SecuredControllerTest {
    @Test
    @WithMockUser(roles = "ADMIN")
    void should_allow_admin() throws Exception { ... }
}
```

> Sa-Token 项目：`@WebMvcTest` 走 MockMvc 不经过 Sa-Token 过滤器，鉴权行为与生产不同。测 Sa-Token 集成用 `@SpringBootTest(RANDOM_PORT)` + REST Assured（见 `05`）。

## @DataJpaTest：JPA 层切片

只加载 JPA 相关组件（`@Entity` / `@Repository` / `EntityManager`），不加载 Web / Service 层。**默认替换为内嵌数据库（H2）**。

```java
@DataJpaTest
class OrderRepositoryTest {
    @Autowired OrderRepository orderRepository;
    @Autowired TestEntityManager entityManager;  // 辅助工具：直接操作实体

    @Test
    void should_find_by_status() {
        entityManager.persist(new Order("CREATED"));
        entityManager.persist(new Order("PAID"));

        List<Order> result = orderRepository.findByStatus("CREATED");

        assertThat(result).hasSize(1);
        assertThat(result.get(0).getStatus()).isEqualTo("CREATED");
    }
}
```

### 隐蔽坑：默认替换为 H2

`@DataJpaTest` 默认 `@AutoConfigureTestDatabase` → 用 H2 替换生产数据库。H2 与 PostgreSQL 的方言差异（`jsonb` / `ARRAY` / `CREATE TYPE AS ENUM` 等 H2 不支持）导致"测试绿生产炸"——完整差异表见 `04` §为什么不用 H2。

**解法**：用 Testcontainers 替代 H2。

```java
// ✗ 默认用 H2——与生产 PostgreSQL 方言不一致
@DataJpaTest
class BadRepoTest { }

// ✓ 禁用 H2 替换 + Testcontainers 真实数据库
@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)  // 禁用 H2 替换
// 完整示例（@ServiceConnection + PostgreSQLContainer + jsonb 查询测试）见 references/04 §@DataJpaTest + Testcontainers
```

> 关键：`@AutoConfigureTestDatabase(replace = NONE)` 必须，否则 `@DataJpaTest` 默认用 H2 替换，容器白启动。完整可运行代码在 `04`。

### @DataJpaTest 默认回滚

`@DataJpaTest` 默认 `@Transactional`——每个测试方法结束后自动回滚，无需手动清理。但与 `RANDOM_PORT` 无关（JPA 切片不起 Web）。

## @JsonTest：JSON 序列化切片

```java
@JsonTest
class OrderJsonTest {
    @Autowired JacksonTester<OrderDTO> json;

    @Test
    void should_serialize_order() throws Exception {
        OrderDTO order = new OrderDTO(1L, "CREATED", new BigDecimal("199.00"));

        assertThat(json.write(order))
            .hasJsonPathNumberValue("$.id")
            .hasJsonPathStringValue("$.status")
            .extractingJsonPathStringValue("$.status").isEqualTo("CREATED");
    }
}
```

用途：验证字段命名（`@JsonProperty`）、序列化格式（日期 / 金额）、反序列化容错。

## @RestClientTest：HTTP 客户端切片

```java
@RestClientTest(PaymentClient.class)
class PaymentClientTest {
    @Autowired PaymentClient paymentClient;
    @Autowired MockWebServer mockWebServer;  // OkHttp MockWebServer

    @Test
    void should_call_payment_api() {
        mockWebServer.enqueue(new MockResponse()
            .setBody("{\"code\":0,\"data\":{\"paymentId\":\"PAY123\"}}")
            .setHeader("Content-Type", "application/json"));

        PaymentResult result = paymentClient.charge(new BigDecimal("100"));

        assertThat(result.getPaymentId()).isEqualTo("PAY123");
    }
}
```

用途：测 `RestTemplate` / `WebClient` / `RestClient` 调用外部 API 的逻辑——请求构造、响应解析、错误处理。MockWebServer 模拟外部服务响应。

## 速度对比

| 测试类型 | 典型启动时间 | Context 范围 |
|---|---|---|
| `@Mock`+`@InjectMocks`（纯单测） | <100ms | 无 |
| `@WebMvcTest` | 2~5s | Web 层 |
| `@DataJpaTest` + H2 | 2~5s | JPA 层 |
| `@DataJpaTest` + Testcontainers | 5~15s（首次拉镜像更久） | JPA 层 + 真实 DB |
| `@SpringBootTest(MOCK)` | 5~15s | 全量 |
| `@SpringBootTest(RANDOM_PORT)` | 5~15s | 全量 + HTTP |

> 切片测试比全量快 2~5 倍。Controller 参数校验用 `@WebMvcTest`（秒级），不必等全量 Context 启动。
