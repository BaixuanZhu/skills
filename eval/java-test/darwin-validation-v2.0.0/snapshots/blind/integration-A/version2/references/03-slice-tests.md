# 03 · 切片测试

> 切片测试只加载某一层（Web / JPA / JSON），不起全量 Context——秒级启动，定位精准。当不需要跨层协作时，切片优于全量 `@SpringBootTest`。切片属本技能分级中的契约切片层（`@WebMvcTest` / `@JsonTest` / `@RestClientTest`）；`@DataJpaTest` + Testcontainers 属真实依赖层——激活协议与分级准入见 SKILL.md 与 `01`。示例注解 `@MockitoBean` 需 Boot 3.4+（≤3.3 写作 `@MockBean`，4.0 已移除旧注解——版本口径见 `02`）。

## 切片 vs 全量：何时用什么

| 你要测的 | 切片？ | 全量？ | 理由 |
|---|---|---|---|
| Controller 参数校验 / 路由 / 异常处理 | `@WebMvcTest` | | 只需 Web 层，Service 可以 mock |
| Controller + Service 联调 | | `@SpringBootTest` | 需要跨层真实协作 |
| Repository SQL / 查询 / 分页 | `@DataJpaTest` | | 只需 JPA 层 + 真实 DB |
| JSON 序列化 / 反序列化 | `@JsonTest` | | 只需 Jackson |
| RestTemplate / WebClient 调用 | `@RestClientTest` | | 只需 HTTP 客户端 + Mock Server |
| Controller → Service → Repository → DB 全链路 | | `@SpringBootTest` | 需要所有层协作 |

> **原则**：能切片就切片。全量启动整个 Context（十秒级），切片只启动一层（秒级）。

## @WebMvcTest：Web 层切片

只加载 Spring MVC 相关组件（Controller / `@ControllerAdvice` / `Filter` / `Validator`），**不加载 Service / Repository / 配置类**。

**头号隐蔽坑**：`@WebMvcTest` 只扫描 `@Controller`/`@RestController`——Controller 依赖的 Service 不会注入 → 启动报 `NoSuchBeanDefinitionException`。解法：`@MockitoBean` Service（最常见，测 Controller 逻辑）；或 `@Import(MyService.class)` 载入真实 Service（其依赖仍需 mock）。

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mockMvc;
    @MockitoBean OrderService orderService;   // 不在切片范围，必须 mock
}
```

### @WebMvcTest 与 Security

项目用 Spring Security 时切片会加载 `SecurityFilterChain`，未认证请求 401。两条路：排除 `excludeAutoConfiguration = SecurityAutoConfiguration.class`（只测 Controller 逻辑），或 `@WithMockUser` 模拟认证用户（测权限控制，详见 `07` 认证节）。

> Sa-Token 项目：`@WebMvcTest` 走 MockMvc 不经过 Sa-Token 过滤器，鉴权行为与生产不同——测 Sa-Token 集成用 `@SpringBootTest(RANDOM_PORT)`（登录态模拟写法见 `07`）。

## @DataJpaTest：JPA 层切片

只加载 JPA 相关组件，不加载 Web / Service 层。**头号隐蔽坑：默认 `@AutoConfigureTestDatabase` 用 H2 替换生产数据库**——方言差异（`jsonb`/`ARRAY`/`CREATE TYPE AS ENUM`）导致"测试绿生产炸"。需要真实行为时：`@AutoConfigureTestDatabase(replace = NONE)` + Testcontainers（`replace = NONE` 不写则容器白启动；完整可运行示例见 `04` §@DataJpaTest）。

> `@DataJpaTest` 默认带 `@Transactional`——每方法结束自动回滚，无需手动清理。

## @JsonTest / @RestClientTest（各两行）

- `@JsonTest`：只加载 Jackson，用 `JacksonTester<T>` 断言序列化 / 反序列化——验证 `@JsonProperty` 命名、日期 / 金额格式、反序列化容错。
- `@RestClientTest(PaymentClient.class)`：只加载 HTTP 客户端 + `MockWebServer`——测 `RestTemplate` / `RestClient` / `WebClient` 的请求构造、响应解析、错误处理，Mock Server 返回可控响应。

## 速度对比

| 测试类型 | 典型启动时间 | Context 范围 |
|---|---|---|
| `@Mock`+`@InjectMocks`（纯单测） | <100ms | 无 |
| `@WebMvcTest` / `@JsonTest` | 2~5s | 单层 |
| `@DataJpaTest` + H2 | 2~5s | JPA 层 |
| `@DataJpaTest` + Testcontainers | 5~15s（首次拉镜像更久） | JPA 层 + 真实 DB |
| `@SpringBootTest(MOCK / RANDOM_PORT)` | 5~15s | 全量（+HTTP） |
