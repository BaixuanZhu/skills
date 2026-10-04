# 03 · 本地接口测试（启动本地服务，真 HTTP 断言）

> 开发期验证"接口真实通"的形态：启动本地服务（连本地已运行环境），HTTP 客户端请求真实接口，断言 status + body——**Controller → Service → Repository 全链路真实，不 mock**。它把手动的"跑起来 curl 一下"自动化成可断言、可重复、进版本控制的测试。重型真实依赖测试（Testcontainers / E2E）不在此 → java-integration-test。

## 形态

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("local")   // application-local.yml 指向本地 docker compose 环境
class OrderApiTest {

    @LocalServerPort int port;

    @Test
    @Sql(scripts = "/sql/cleanup-orders.sql",
         executionPhase = Sql.ExecutionPhase.AFTER_TEST_METHOD)   // 见下文「数据清理」
    void should_create_order_when_valid() {
        given()
            .baseUri("http://localhost:" + port)
            .contentType(ContentType.JSON)
            .body(Map.of("productId", 1, "qty", 2))
        .when()
            .post("/api/orders")
        .then()
            .statusCode(200)
            .body("data.status", equalTo("CREATED"))
            .body("data.totalAmount", equalTo(199.00f));
    }
}
```

- 端点路径、请求体、响应字段**跟随项目实际定义**，不断言猜测的字段。
- 认证传递（token header / cookie）跟随项目认证方式——探测项目安全配置，不假设。

## HTTP 客户端选择（版本事实——省查文档）

| 客户端 | 版本口径 | 说明 |
|---|---|---|
| **REST Assured** | 全版本可用；Boot ≤3.x BOM 管理（删 `<version>`）；Boot 4 需手写 `6.0.1`（BOM 已不管理），且 ≤3.x 用 `spring-mock-mvc` 子模块时必须停在 5.5.x | given/when/then 流式断言，多步串联提取值方便 |
| **WebTestClient** | 全版本（需 `@AutoConfigureWebTestClient`） | Servlet + Reactive 通用 |
| **RestTestClient** | 仅 Boot 4+：依赖 `org.springframework.boot:spring-boot-resttestclient`（test scope）+ `@AutoConfigureRestTestClient`；旧 `TestRestTemplate` 已废弃（升 Boot 4 原注入直接失败） | ≤3.x 项目沿用 `TestRestTemplate` |

> Boot 4 不再自动配置测试客户端——`@AutoConfigure*` 注解必须显式写。

## 三条硬护栏

1. **环境未启动 → 明确报错，禁止兜底**：连不上本地 DB/Redis → 测试失败并给出可操作信息（"本地环境未启动：`docker compose up -d` 后重跑"）。**禁止**测试代码转而拉起 Testcontainers 或切 H2——那是重型测试的领地（java-integration-test，确认后激活），开发期测试不自管基础设施。
2. **数据清理用 `@Sql(AFTER)` / `TRUNCATE`，不用 `@Transactional`**：`RANDOM_PORT` 下 HTTP 请求走 Servlet 容器线程，与测试线程不在同一事务，`@Transactional` 回滚**静默失效**——测试绿但数据残留，下个用例突然红（"上次跑过这次报错"的典型根因）。每条写接口的用例配 `@Sql(executionPhase = AFTER_TEST_METHOD)` 清理，或多表场景 `@AfterEach` + `JdbcTemplate` TRUNCATE。
3. **Context 配置统一**：`@ActiveProfiles` / 属性 / webEnvironment 全套一致 → Spring 缓存一个 Context，**一次 ~10s 启动全套共享**；任何一个属性不同 → 再付一次启动。不要每个测试类自定义不同属性。

## 数量与边界

- **每端点 1~3 条**：正向（200 + 关键 body 字段）+ 校验失败 / 异常（400/409 + 错误信息）各一条。业务分支矩阵**不铺在这里**——铺纯单测（SKILL.md 四维度）。接口测试验证的是"链路通 + 契约对"，不是"逻辑全"。
- **外部 HTTP 依赖（支付/短信/三方认证）按 local 配置 stub**（mock server / WireMock），真调禁止——费用、不可重复。
- 断言粒度：HTTP status + 响应体关键字段值（能定位行为的最小字段集），不断言整个 JSON 快照（脆）。
- 类名用 `*Test`（surefire，`mvn test` 跑）；重型集成测试用 `*IT`（failsafe，`mvn verify`）——两套不混，保证 `mvn test` 保持轻量。

## 稳定后的升格路径

本地接口测试是开发期资产；功能稳定（需求冻结 / 验收 / 发布准备）后，**同用例换 Testcontainers 数据源**即成为 CI 可重复的重型集成测试（去 `java-integration-test`，其激活协议与容器用法在那里）。开发期不提前做这件事。

## antipatterns

- ✗ mock 掉 Service 只测 Controller 转发 → ✓ 开发期接口测试的价值就在**真实链路**；只要契约（参数校验/异常映射）才 mock Service——那是重型技能的切片测试（`@WebMvcTest`）。
- ✗ 测试连不上本地库，加 `@Container` 拉个 PostgreSQL → ✓ 开发期不自管基础设施：报错提示启动本地环境；要容器级隔离去 java-integration-test。
- ✗ `@Transactional` 期望自动回滚 → ✓ `RANDOM_PORT` 下失效，`@Sql(AFTER)` 清理。
- ✗ 每个测试类不同 `@ActiveProfiles` / 属性 → ✓ 配置统一共享一个 Context，启动只付一次。
- ✗ 每端点写 8、9 条用例把分支矩阵铺进来 → ✓ 接口 1~3 条验链路契约，分支铺纯单测。
