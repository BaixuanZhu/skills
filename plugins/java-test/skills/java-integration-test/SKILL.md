---
name: java-integration-test
slug: java-integration-test
displayName: Java 集成测试
description: >-
  Java/Spring Boot 集成测试助手——在编写、评审、补全集成测试 / E2E / 冒烟测试 /
  接口测试时使用本技能。核心：消灭 curl 仿真测试——用可断言、可重复、可版本控制
  的测试替代 curl 调接口 + 肉眼判断。覆盖：Spring Boot Test（@SpringBootTest /
  @WebMvcTest / @DataJpaTest 切片测试）、MockMvc / WebTestClient / TestRestTemplate、
  REST Assured API 断言、Testcontainers 真实依赖、WireMock 外部服务 stub、
  测试隔离（@Transactional 回滚 / @Sql / @DirtiesContext）、冒烟测试（Actuator health）。
  次级触发信号：用 curl 测接口、手动启动应用再调接口、@SpringBootTest 全量上下文
  测单层 Controller、测试间数据互相污染、H2 测试 + PostgreSQL 生产、外部 API 真调、
  "返回 200 就是通过了"、仿真测试不稳定、反复全量 mvn test、全文读测试输出、跑测试太慢。
  与 java-unit-test 的边界：纯单测（@Mock + @InjectMocks，毫秒级，不起容器）→ java-unit-test；
  跨层协作 + 真实依赖 + 进程内 HTTP 断言 → 本技能。
version: "1.0.0"
last_verified: "2026-08-13"
---

# Java 集成测试

面向 Java/Spring Boot 的**集成测试 / 冒烟测试 / API 级 E2E** 助手。本技能提供从切片测试到全量集成的完整工具链，每条规则含「✗ 错误做法 → ✓ 正确做法」——核心是消灭 curl 仿真测试（无断言 / 不可重复 / 不进版本控制，详见铁律 1 + `references/01`）。

## 三条铁律

1. **curl 不是测试**：测试必须有结构化断言（HTTP status + response body + jsonPath），而非"看起来返回正常"。curl 是调试工具，不是测试工具——它没有断言、不可重复、不进版本控制、无隔离。
2. **选对层次**：切片测试（`@WebMvcTest`/`@DataJpaTest`）秒级启动，够用就不用全量 `@SpringBootTest`。单层逻辑用 `@Mock`+`@InjectMocks`（→ java-unit-test），跨层协作用集成测试——不越界、不滥用全量上下文。
3. **隔离优先**：测试间数据不污染。`@Transactional` 回滚（注意失效场景）、Testcontainers 重置、`@Sql` 清理——一个测试的副作用不能影响另一个。

## 快速入门

| 你想做的 | 看这份 | 读多少 |
|---|---|---|
| 不知道用哪种测试 / curl 该不该用 | `references/01` 测试层次 + curl 反模式 | 各前 40 行 |
| 写 @SpringBootTest / MockMvc / WebTestClient | `references/02` | 通读 |
| 只测单层 Controller 或 Repository（切片） | `references/03` | 通读 |
| 用真实数据库 / Redis / Kafka 测 | `references/04` | 通读 |
| 写 API 断言（REST Assured given/when/then） | `references/05` | 通读 |
| 测试隔离 / @Transactional 失效 / WireMock | `references/06` | 通读 |
| 冒烟测试 / 多接口串联 E2E | `references/07` | 通读 |
| 跑测试烧 token / 反复全量 / 输出太多 | `references/08` | 通读 |

> `01` 根文件（选层次前必读）；`02`-`05` 工具链落地；`06` 隔离陷阱；`07` 冒烟与 E2E；`08` 执行效率。

## 第 0 步：探测项目与场景（激活时先执行）

读项目 `pom.xml` / `build.gradle` 和测试代码，一次性判断：

1. **工具栈**：
   - Spring Boot 版本（`pom.xml` 读 `spring-boot-starter-parent`）→ 决定 `@ServiceConnection` 可用性（3.1+）、命名空间（`javax.*` vs `jakarta.*`）。
   - 是否已有 `testcontainers` 依赖（`grep testcontainers pom.xml`）→ 决定是否需引导引入。
   - 是否已有 `rest-assured` 依赖（`grep rest-assured pom.xml`）→ 决定 API 测试用 REST Assured 还是 MockMvc。
   - 是否已有 `wiremock` 依赖（`grep wiremock pom.xml`）→ 决定外部 stub 方案。
2. **测试场景**（决定用哪种测试，见路由表）：
   - 只测 Controller 层（参数校验 / 路由 / 异常处理）→ `@WebMvcTest` 切片
   - 测 Service + Repository + 真实 DB → `@SpringBootTest` + Testcontainers
   - 测完整 HTTP API（含序列化 / 过滤器 / 拦截器）→ `@SpringBootTest(RANDOM_PORT)` + REST Assured / WebTestClient
   - "验证服务能不能正常启动"→ Actuator health 冒烟测试
   - 多接口串联的业务流程 → API 级 E2E
3. **curl 检测**：如果正在用 curl 或打算用 curl 调接口"测试"→ **立即拦截**，按路由表引导到正确工具。

## 测试层次路由

> 选层次前**先读 `references/01`**：含完整决策树与 curl 反模式分析。

| 场景 | 工具 | 启动速度 | 详见 |
|---|---|---|---|
| 单类逻辑 + Mock 依赖（纯单测） | `@Mock`+`@InjectMocks` | 毫秒 | → **java-unit-test** |
| 单层 Controller + 参数校验 / 异常 | `@WebMvcTest` + MockMvc | 秒级 | `03` |
| JPA Repository + 真实 SQL | `@DataJpaTest` + Testcontainers | 秒级 | `03`+`04` |
| Service + Repository 跨层协作 | `@SpringBootTest(MOCK)` + `@Transactional` | 秒~十秒 | `02`+`06` |
| 完整 HTTP API（含序列化 / 过滤器） | `@SpringBootTest(RANDOM_PORT)` + REST Assured | 十秒+ | `02`+`05` |
| "服务能不能启动"冒烟 | `@SpringBootTest` + Actuator health | 十秒+ | `07` |
| 多接口串联业务流程（E2E） | `@SpringBootTest(RANDOM_PORT)` + REST Assured 多步 | 十秒+ | `05`+`07` |
| 外部 HTTP 依赖隔离 | WireMock stub | — | `06` |
| 真实数据库 / Redis / Kafka | Testcontainers | 十秒+ | `04` |

## S 级反模式表（致命——测试存在但测不出问题）

> S 级：导致"测试存在但测不出 bug"——新测试禁止；审查既有测试命中 → 立即指出补全。

| ✗ 错误做法 | ✓ 正确做法 |
|---|---|
| 用 `curl` 调接口 + 肉眼判断输出 | 用 MockMvc / REST Assured / WebTestClient 写可断言测试（statusCode + body + jsonPath） |
| 手动启动应用再 curl "测试" | `@SpringBootTest(webEnvironment=RANDOM_PORT)` 进程内启动 + 自动断言 |
| 全量 `@SpringBootTest` 测单层 Controller | `@WebMvcTest` 切片测试——只加载 Web 层，秒级启动 |
| `@Transactional` 回滚用于 `RANDOM_PORT` 场景 | `RANDOM_PORT` 下 HTTP 请求走独立线程，`@Transactional` 回滚**失效**→ 用 `@Sql` 清理 or Testcontainers 重置（见 `06`） |
| H2 测试 + PostgreSQL 生产 | Testcontainers 用真实数据库——消除方言差异（`jsonb`/`ARRAY`/`SERIAL` 等 H2 不支持） |
| 外部 API 真调（第三方支付 / 短信） | WireMock stub——可控、可重复、不产生费用 |
| 无断言测试（调一下接口即算"覆盖"） | 每个测试必须有结构化断言：HTTP status + 响应体字段值 |
| `@DirtiesContext` 每个测试都加 | 只在 Context 状态确实被污染时用——它会重建整个 Spring Context（十秒级），优先 `@Sql` / `@Transactional` |
| 启动日志有 WARN/ERROR 但测试绿 | 日志报错 = 测试失败信号，必须排查——Bean 创建失败、Flyway 迁移失败常被 Mock 遮掩 |

## A 级规则表（约定——约束新生成测试）

| ✗ 错误做法 | ✓ 正确做法 |
|---|---|
| 测试间共享数据，互相污染 | 每个 `@Test` 自包含；`@AfterEach` / `@Sql` 清理 |
| 测试依赖执行顺序 | 可乱序执行（JUnit 5 默认）；不依赖 `@Order` |
| `@MockBean` 替换大量 Bean | 每组不同 `@MockBean` 组合重建 Context → 测试极慢；尽量统一 mock 配置，或用 `@Import` + `@TestConfiguration` |
| `@DataJpaTest` 默认用 H2 但生产是 PostgreSQL | `@AutoConfigureTestDatabase(replace = NONE)` + Testcontainers（见 `04`） |
| `@WebMvcTest` 不 mock Service 导致启动失败 | `@WebMvcTest` 只加载 Web 层——Service 需 `@MockBean` 或 `@Import` |
| REST Assured `RestAssuredMockMvc` 当真实 HTTP 用 | `RestAssuredMockMvc` 走 MockMvc（进程内，无真实 HTTP）；要真实 HTTP 用 `RestAssured` + `RANDOM_PORT`（见 `05`） |
| Testcontainers 容器每个测试方法启停 | `@Container` + `static` → 容器全类共享；或 `testcontainers.reuse.enable=true` 跨类复用 |
| WireMock 固定端口，并行测试端口冲突 | WireMock 随机端口（`options().dynamicPort()`）+ `@DynamicPropertySource` 注入 |

## 核心强约束（Agent 必须遵守）

1. **禁止 curl 测试**：生成测试不得用 `curl` / `httpie` / 手动 HTTP 客户端；必须用 MockMvc / WebTestClient / REST Assured / TestRestTemplate 编写含结构化断言的测试（本质见铁律 1）。
2. **`@Transactional` 回滚仅限 `MOCK` 模式**：MOCK 有效、`RANDOM_PORT` 失效（根因见 S 级表 + `references/06`），改用 `@Sql(execution=AFTER_TEST_METHOD)` 或 Testcontainers 重置。
3. **切片测试优先**：只测单层时用 `@WebMvcTest`（Controller）/ `@DataJpaTest`（Repository），不起全量 Context。全量 `@SpringBootTest` 只用于真正需要跨层协作的场景。
4. **Testcontainers 消除环境差异**：生产用 PostgreSQL/MySQL/Redis → 测试用 Testcontainers 起同款容器，不用 H2 替代（方言差异是"测试绿生产炸"头号来源，差异表见 `references/04`）。
5. **外部依赖必须 stub**：调用外部 HTTP API（支付 / 短信 / 第三方认证）必须用 WireMock stub，不得真调（理由见 S 级表）。
6. **`@DirtiesContext` 是最后手段**：重建整个 Context（十秒级，代价见 S 级表），仅在 Bean 内部状态被污染且无法用 `@Sql` / `@Transactional` / Testcontainers 重置时才用。
7. **Context 缓存友好**：`@MockBean` / `@SpyBean` / `@SpringBootTest` 属性的组合变化会导致 Context 缓存失效并重建。统一测试的 mock 配置，避免每个测试类用不同 `@MockBean` 组合。
8. **执行测试降噪**：`mvn test` 降噪输出（`-q` + 重定向后 `grep` 关键行），**不全文回传 stdout**；失败读 `target/surefire-reports/*.txt` 定位、`-Dtest` 单测重跑，不反复全量、不每次 `clean`（命令细节见 `references/08`）。

## 使用流程

1. **第 0 步探测**：工具栈 + 测试场景 + curl 检测。
2. **读 `references/01`**：确认测试层次（切片 / 集成 / 冒烟 / E2E）。
3. **定位工具 reference**：按路由表读 `02`-`05` 对应文件。
4. **隔离策略**：读 `references/06`，确定数据清理方案（`@Transactional` / `@Sql` / Testcontainers 重置 / WireMock）。
5. **执行效率**：读 `references/08`——`mvn test` 降噪输出、`-Dtest` 单测迭代、失败读 surefire 报告，不全文读输出。
6. **输出前自检 S 级**：尤其"是否有 curl""`@Transactional` 是否用于 RANDOM_PORT""是否 H2 测 PostgreSQL 生产""是否有结构化断言"。

## 版本与范围

- Spring Boot 2.7.x / 3.x / 4.x 均适用；3.1+ 新增 `@ServiceConnection`（Testcontainers 自动连接），3.0 及以下用 `@DynamicPropertySource`。
- JUnit 5（Jupiter）为主。JUnit 4 遗留项目：用 `@RunWith(SpringRunner.class)` 替代 `@ExtendWith`，断言用 `org.junit.Assert`，生命周期注解为 `@Before`/`@After`；其余写法与本技能示例一致。
- **与 `java-unit-test` 的边界**：纯单元测试（`@Mock`+`@InjectMocks`，毫秒级，不起容器，单类逻辑）→ java-unit-test。跨层协作（Controller→Service→Repository）、真实依赖（DB/Redis/Kafka）、进程内 HTTP 断言、冒烟测试、API 级 E2E → 本技能。`@MockBean` 的分界线：纯单测用 `@Mock`（→ java-unit-test），切片 / 集成测试用 `@MockBean`（→ 本技能）。
- **不适用**：前端 E2E（Selenium / Playwright / Cypress）、性能测试（JMeter / Gatling）、安全测试。
