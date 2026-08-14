# 07 · 冒烟测试与 API 级 E2E

> 冒烟测试验证"服务能启动 + 核心端点活着"；API 级 E2E 验证完整业务流程（多接口串联）。两者都不是 curl——而是有断言的自动化测试。

## 冒烟测试

### 什么是冒烟测试

冒烟测试是最轻量的集成测试——**验证应用能正常启动、核心依赖（DB / Redis）连通、关键端点响应正常**。它不是功能测试（不验证业务逻辑），而是"系统活着"的快速检查。

### 正确做法：Actuator health + 断言

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
class SmokeTest {

    @LocalServerPort int port;

    @Test
    void should_start_and_health_check_pass() {
        given()
            .baseUri("http://localhost:" + port)
        .when()
            .get("/actuator/health")
        .then()
            .statusCode(200)
            .body("status", equalTo("UP"))
            .body("components.db.status", equalTo("UP"))        // 数据库连通
            .body("components.redis.status", equalTo("UP"));    // Redis 连通
    }

    @Test
    void should_core_endpoints_respond() {
        given().baseUri("http://localhost:" + port)
        .when().get("/api/products")
        .then().statusCode(200);  // 核心查询端点可访问

        given().baseUri("http://localhost:" + port)
        .when().get("/api/orders")
        .then().statusCode(anyOf(is(200), is(401)));  // 可能需认证，但端点存在
    }
}
```

> **冒烟测试断言什么**：`status=UP`（服务活着）、`components.db.status=UP`（DB 连通）、核心端点返回非 5xx。**不验证业务逻辑**——那是集成测试 / E2E 的职责。

### Actuator 依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

```yaml
# application.yml
management:
  endpoints:
    web:
      exposure:
        include: health,info  # 生产可按需暴露更多
  endpoint:
    health:
      show-details: always     # 测试中显示组件详情（DB / Redis 状态）
```

> `show-details: always` 在测试中显示各组件健康状态（`components.db.status`）。生产环境按安全策略配置（`when-authorized` 或 `never`）。

### curl 冒烟测试的反模式

```bash
# ✗ curl 冒烟测试——手动执行，无断言，不进 CI
curl http://localhost:8080/actuator/health
# 看到 {"status":"UP"} → "冒烟通过"
# 但：没检查 DB 组件状态、不在 CI 中、换人跑不了
```

```java
// ✓ 自动化冒烟测试——进 CI，有断言
@Test
void should_health_check_pass() {
    when().get("/actuator/health")
    .then()
        .statusCode(200)
        .body("status", equalTo("UP"))
        .body("components.db.status", equalTo("UP"));
}
```

### 冒烟测试在 CI 中的位置

```
CI Pipeline:
  1. mvn compile          → 编译通过
  2. mvn test             → 单元测试
  3. mvn verify           → 集成测试 + 冒烟测试（Testcontainers 起依赖）
  4. docker build & push  → 镜像构建
  5. deploy to staging    → 部署
  6. smoke test on staging → 生产环境冒烟（验证部署成功）
```

> 冒烟测试在部署后执行——验证"部署到目标环境后服务能启动"。这是 curl 最常被误用的场景：部署后手动 curl → 应改为自动化冒烟测试。

## API 级 E2E

### 什么是 API 级 E2E

E2E（End-to-End）验证**完整业务流程**——从用户操作的第一个接口到最后一个接口，所有中间步骤串联。与集成测试的区别：

| | 集成测试 | API 级 E2E |
|---|---|---|
| 范围 | 跨层协作（Controller→Service→Repository） | 完整业务流程（多接口串联） |
| 数据 | 单个操作 | 多个操作有前后依赖 |
| 典型 | 创建订单 | 注册→登录→浏览→下单→支付→查询订单 |

### 完整示例：电商下单流程

> 以下示例展示 E2E 多步串联模式——端点路径、请求体结构、响应字段跟随项目实际定义，不要直接复制。

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@Testcontainers
class OrderFlowE2ETest {

    @LocalServerPort int port;
    @Container @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    RequestSpecification spec;

    @BeforeEach
    void setup() {
        RestAssured.port = port;
        spec = new RequestSpecBuilder()
            .setContentType(ContentType.JSON)
            .build();
    }

    @AfterEach
    void cleanup() {
        // E2E 后清理所有表——RANDOM_PORT 下 @Transactional 无效
        new JdbcTemplate(dataSource).execute(
            "TRUNCATE TABLE users, products, orders, order_items CASCADE");
    }

    @Test
    @Sql(scripts = "/sql/insert-products.sql")  // 预置商品数据
    void should_complete_full_order_flow() {
        // ① 注册
        String token =
            given().spec(spec)
                .body(Map.of("username", "e2e-user", "password", "Pass123!"))
            .when()
                .post("/api/auth/register")
            .then().statusCode(201)
                .extract().path("data.token");

        RequestSpecification authSpec = new RequestSpecBuilder()
            .addHeader("Authorization", "Bearer " + token)
            .setContentType(ContentType.JSON)
            .build();

        // ② 浏览商品
        given().spec(authSpec)
        .when()
            .get("/api/products")
        .then().statusCode(200)
            .body("data.size()", greaterThan(0));

        // ③ 创建订单
        Integer orderId =
            given().spec(authSpec)
                .body(Map.of("productId", 1, "qty", 2, "address", "南宁市"))
            .when()
                .post("/api/orders")
            .then().statusCode(201)
                .body("data.status", equalTo("CREATED"))
                .body("data.totalAmount", equalTo(199.00f))
                .extract().path("data.id");

        // ④ 支付
        given().spec(authSpec)
            .body(Map.of("paymentMethod", "ALIPAY"))
        .when()
            .post("/api/orders/{id}/pay", orderId)
        .then().statusCode(200)
            .body("data.status", equalTo("PAID"));

        // ⑤ 查询验证最终状态
        given().spec(authSpec)
        .when()
            .get("/api/orders/{id}", orderId)
        .then().statusCode(200)
            .body("data.status", equalTo("PAID"))
            .body("data.paidAt", notNullValue())
            .body("data.items.size()", equalTo(1))
            .body("data.items[0].qty", equalTo(2));
    }

    @Test
    @Sql(scripts = "/sql/insert-products.sql")
    void should_reject_order_when_out_of_stock() {
        // ① 注册 + 登录
        String token = registerAndGetToken("e2e-user-2");

        // ② 下单超出库存
        given()
            .header("Authorization", "Bearer " + token)
            .body(Map.of("productId", 1, "qty", 999999))
        .when()
            .post("/api/orders")
        .then()
            .statusCode(409)  // 或 400，取决于业务设计
            .body("msg", containsString("库存不足"));
    }
}
```

### E2E 测试设计原则

1. **测试业务流程，不测试单个接口**：E2E 价值在于"串联"——验证接口间的数据传递、状态流转。单个接口的断言放在集成测试中。
2. **预置数据用 `@Sql`**：E2E 需要初始数据（商品 / 配置项）→ 用 `@Sql(BEFORE)` 插入，不要在测试中通过 API 创建。
3. **清理用 `TRUNCATE`**：E2E 涉及多表，`@Sql(AFTER)` 逐表删繁琐——`TRUNCATE TABLE ... CASCADE` 一次清空。
4. **提取 token 复用**：多步骤共享认证 → `RequestSpecification` 封装 header。
5. **正向流程 + 关键异常流程**：E2E 不求全覆盖（那是单测的职责），覆盖核心路径 + 1~2 个关键异常（库存不足 / 权限拒绝）。

### E2E 测试数量控制

E2E 测试慢（十秒+），不宜过多。经验法则：

| 测试类型 | 数量 | 速度 | 覆盖 |
|---|---|---|---|
| 单元测试 | 数十~数百 | 毫秒 | 所有方法逻辑 |
| 切片测试 | 十~数十 | 秒 | 每层关键行为 |
| 集成测试 | 数~十数 | 秒~十秒 | 跨层协作 |
| E2E | 3~10 | 十秒+ | 核心业务流程 |

> E2E 测**核心业务路径**（下单 / 支付 / 退款），不测边界情况（那是单测 + 集成测试的职责）。E2E 太多 → CI 时间爆炸。

## 认证与权限测试

### Spring Security：@WithMockUser

```java
@WebMvcTest(OrderController.class)
@Import(SecurityConfig.class)  // 加载安全配置
class OrderControllerSecurityTest {

    @MockBean OrderService orderService;

    @Test
    @WithMockUser(roles = "ADMIN")
    void should_allow_admin_to_delete_order() {
        when(orderService.deleteById(1)).thenReturn(true);

        mockMvc.perform(delete("/api/orders/1"))
            .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "USER")
    void should_forbid_user_to_delete_order() {
        mockMvc.perform(delete("/api/orders/1"))
            .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(username = "user1", roles = "USER")
    void should_show_user_identity_in_audit_log() {
        // SecurityContext 中可直接获取当前用户
        // 适合测试 @PreAuthorize("principal.username == #username") 等表达式
    }
}
```

> `@WithMockUser` 不走真实认证流程（不校验密码 / 不发 Token），直接往 SecurityContext 注入一个虚拟用户。适合测权限控制（谁能调 / 谁不能调），不适合测认证流程本身（登录 / Token 签发）。

### @WithMockUser vs 真实认证流程

| 你要测的 | 用什么 |
|---|---|
| 权限控制（`@PreAuthorize` / `@Secured` / URL 拦截） | `@WithMockUser` |
| 认证流程（登录接口 / Token 签发 / 密码校验） | 真实调用 `/api/auth/login` |
| E2E 完整流程（含登录步骤） | 真实调用 `/api/auth/login` 获取 Token |
| Controller 层权限断言（快、隔离） | `@WithMockUser` + `@WebMvcTest` |

> **经验**：E2E 中走真实认证（注册→登录→拿 Token→带 Token 调后续接口）——因为 E2E 的价值就是验证完整链路。Controller 层测权限用 `@WithMockUser`——因为这里测的是权限逻辑，不是认证流程。

### Sa-Token 项目：测试中模拟登录态

Sa-Token 不用 Spring Security 的 `@WithMockUser`。测试中模拟登录态的方式：

```java
// 切片测试：MockMvc + 手动注入 Sa-Token 上下文
@WebMvcTest(OrderController.class)
class OrderControllerSaTokenTest {

    @MockBean OrderService orderService;

    @Test
    void should_allow_logged_in_user() {
        // 模拟已登录用户
        StpUtil.getStpLogic().setLoginId(1001);  // 模拟用户 ID=1001 已登录

        when(orderService.create(any())).thenReturn(1L);

        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"productId\":1,\"qty\":2}"))
            .andExpect(status().isOk());

        StpUtil.getStpLogic().logout();  // 清理登录态
    }

    @Test
    void should_reject_anonymous_user() {
        // 不设置登录态 → StpUtil.checkLogin() 抛 NotLoginException
        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"productId\":1,\"qty\":2}"))
            .andExpect(status().isUnauthorized());  // 全局异常处理器返回 401
    }
}
```

```java
// E2E：走真实 Sa-Token 登录流程
@Test
void should_complete_order_flow_with_real_login() {
    // ① 真实登录拿 Token
    String token =
        given().body(Map.of("username", "e2e-user", "password", "Pass123!"))
        .when().post("/api/auth/login")
        .then().statusCode(200)
        .extract().path("data.token");

    // ② 带 Token 调后续接口
    given().header("Authorization", token)  // Sa-Token 默认从 Header 读
        .body(Map.of("productId", 1, "qty", 2))
    .when().post("/api/orders")
    .then().statusCode(201);
}
```

> Sa-Token 详细用法（拦截器配置、注解鉴权、Token 类型选择）→ **sa-token-dev** 技能。本节只覆盖测试中如何模拟登录态。

## 部署后冒烟测试（非 Spring Boot Test）

部署到测试 / 预发环境后，服务已在外部运行——此时不能用 `@SpringBootTest`（进程内启动），需连外部地址：

```java
// 部署后冒烟：连接已部署的服务（非进程内）
@Test
class DeployedSmokeTest {

    @Test
    void should_deployed_service_be_healthy() {
        String baseUrl = System.getenv("DEPLOYED_URL");  // CI 注入部署地址

        given()
            .baseUri(baseUrl)
        .when()
            .get("/actuator/health")
        .then()
            .statusCode(200)
            .body("status", equalTo("UP"))
            .body("components.db.status", equalTo("UP"));
    }
}
```

> 部署后冒烟测试不需要 Spring Boot Test——只需 REST Assured 连外部地址。`DEPLOYED_URL` 由 CI 环境变量注入。
