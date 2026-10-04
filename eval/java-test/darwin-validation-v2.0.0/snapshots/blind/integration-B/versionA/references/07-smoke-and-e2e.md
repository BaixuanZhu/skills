# 07 · 冒烟测试与 API 级 E2E

> 冒烟测试验证"服务能启动 + 核心端点活着"；API 级 E2E 验证完整业务流程（多接口串联）。两者都不是 curl——而是有断言的自动化测试。冒烟与 E2E 属本技能真实依赖层——激活协议通过后才写（见 SKILL.md）；数量锚点见下文「E2E 测试数量控制」。示例注解 `@MockitoBean` 需 Boot 3.4+（≤3.3 写作 `@MockBean`，4.0 已移除旧注解——版本口径见 `02`）。

## 冒烟测试

最轻量的集成测试——验证应用能启动、核心依赖（DB / Redis）连通、关键端点响应正常。**不验证业务逻辑**（那是单测 / 集成测试的职责），断言三件事：`status=UP`、`components.db.status=UP`（各组件连通）、核心端点非 5xx。

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
class SmokeTest {
    @LocalServerPort int port;

    @Test
    void should_start_and_health_check_pass() {
        given().baseUri("http://localhost:" + port)
        .when().get("/actuator/health")
        .then().statusCode(200)
            .body("status", equalTo("UP"))
            .body("components.db.status", equalTo("UP"));
    }
}
```

依赖 `spring-boot-starter-actuator`；`management.endpoint.health.show-details: always`（测试中显示组件详情，生产按安全策略收敛）。

✗ curl 打 `/actuator/health` 看"UP"就算冒烟——手动执行、无组件检查、不进 CI；✓ 上述自动化测试。

**CI 中的位置**：`mvn compile` → 单元测试（`mvn test`）→ 集成 + 冒烟（`mvn verify`，Testcontainers 起依赖）→ 构建镜像 → 部署 → **部署后冒烟**（连已部署环境，见文末）。

## API 级 E2E

验证**完整业务流程**——从用户第一个接口到最后一个接口串联，接口间数据传递 / 状态流转是重点。与集成测试的区别：集成测单个操作（跨层协作），E2E 测多操作有前后依赖的流程（注册→登录→下单→支付→查询）。

### E2E 骨架（多步串联模式）

> 端点路径、请求体、响应字段跟随项目实际定义。串联语法（extract 复用 token / spec）见 `05`「多步串联」。

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@Testcontainers
class OrderFlowE2ETest {

    @LocalServerPort int port;
    @Container @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17.11-alpine");

    @AfterEach
    void cleanup() {
        // E2E 后清理所有表——RANDOM_PORT 下 @Transactional 无效
        new JdbcTemplate(dataSource).execute("TRUNCATE TABLE users, products, orders CASCADE");
    }

    @Test
    @Sql(scripts = "/sql/insert-products.sql")   // 预置数据用 @Sql(BEFORE)，不在测试中通过 API 创建
    void should_complete_full_order_flow() {
        // ① 注册/登录 → extract token → 构建 authSpec（写法见 05）
        // ② 核心链路逐步断言：下单 → 201 + status / totalAmount 字段值
        // ③ 支付 → 200 + status=PAID
        // ④ 查询终态 → 断言最终状态 + 关键字段（paidAt / items）
        // 每步都有 statusCode + body 字段断言，不是"调一下就算过"
    }

    @Test
    void should_reject_order_when_out_of_stock() {
        // 异常流程：超库存下单 → 409/400 + 错误信息断言
    }
}
```

### 设计原则与数量控制

1. **测业务流程不测单接口**：接口间数据传递 / 状态流转是 E2E 价值；单接口断言放集成测试。
2. **预置数据用 `@Sql(BEFORE)`**，清理用 `TRUNCATE ... CASCADE`（多表一次清）。
3. **正向流程 + 1~2 个关键异常**（库存不足 / 权限拒绝），不求全覆盖。

| 测试类型 | 数量 | 速度 | 覆盖 |
|---|---|---|---|
| 单元测试 | 数十~数百 | 毫秒 | 所有方法逻辑（→ java-unit-test） |
| 切片测试 | 十~数十 | 秒 | 每层关键行为 |
| 集成测试 | 数~十数 | 秒~十秒 | 跨层协作 |
| E2E | 3~10 | 十秒+ | 核心业务流程 |

> E2E 测**核心业务路径**（下单 / 支付 / 退款），不测边界情况——E2E 太多 → CI 时间爆炸。

## 认证与权限测试

| 你要测的 | 用什么 |
|---|---|
| 权限控制（`@PreAuthorize` / `@Secured` / URL 拦截） | `@WithMockUser` + 切片（快、隔离） |
| 认证流程（登录 / Token 签发 / 密码校验） | 真实调 `/api/auth/login` |
| E2E 完整流程（含登录步骤） | 真实登录拿 Token 复用 |

> `@WithMockUser` 不走真实认证（不校验密码），直接往 SecurityContext 注入虚拟用户——适合测权限逻辑，不适合测认证流程。E2E 走真实认证（E2E 的价值就是验证完整链路）。

**Sa-Token 项目**（不用 Spring Security 的 `@WithMockUser`）：

```java
// 切片内模拟登录态：直接注入 Sa-Token 上下文（MockMvc 不经过 Sa-Token 过滤器，
// 与生产鉴权行为不同——测真实鉴权集成用 RANDOM_PORT + 真实登录）
StpUtil.getStpLogic().setLoginId(1001);   // 模拟已登录
// ... 测试 ...
StpUtil.getStpLogic().logout();           // 清理登录态

// E2E：真实登录拿 token（Sa-Token 默认从 Header 读，token 名由 sa-token.token-name 决定）
String token = given().body(loginRequest)
    .when().post("/api/auth/login")
    .then().statusCode(200)
    .extract().path("data.token");
given().header(tokenName, token).body(orderRequest)
    .when().post("/api/orders").then().statusCode(201);
```

> Sa-Token 详细用法（拦截器配置、注解鉴权、Token 类型）→ **sa-token-dev** 技能。本节只覆盖测试中如何模拟登录态。

## 部署后冒烟测试（非 Spring Boot Test）

部署到测试 / 预发环境后，服务已在外部运行——不能用 `@SpringBootTest`（进程内启动），连外部地址：REST Assured 打 `System.getenv("DEPLOYED_URL")`（CI 注入）断言 `/actuator/health`。不需要 Spring Boot Test，只需 REST Assured。
