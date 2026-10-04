---
name: java-integration-test
slug: java-integration-test
displayName: Java 集成测试
description: >-
  Java/Spring Boot 集成测试 / 冒烟测试 / API 级 E2E 助手——在功能稳定后（需求冻结 /
  特性过验收 / 发布准备）补集成测试层时使用本技能，无论用户是否提到具体框架
  （集成测试 / 接口测试 / E2E / 冒烟测试 / @SpringBootTest / MockMvc /
  REST Assured / Testcontainers / WireMock）。测试三级分级：T1 纯单测
  （@Mock + @InjectMocks，毫秒）→ java-unit-test；T2 Spring 切片测试
  （@WebMvcTest / @JsonTest，秒级，不触真实依赖——参数校验 / JSON / 权限逻辑
  最多到这层）；T3 真实依赖（Testcontainers——断言 SQL / 迁移 / 事务传播 /
  缓存语义等离开真实 DB/Redis/Kafka 就不成立的行为，每特性 1~3 条）。
  开发期（需求未稳定）默认只写 T1 单测，本技能不介入宽覆盖。核心：消灭仿真测试
  ——用可断言、可重复、可版本控制的测试替代 curl 调接口 + 肉眼判断。
  次级触发信号：功能已稳定要补集成层、用 curl 或手动启动应用调接口"测试"、
  @SpringBootTest 全量上下文测单层 Controller、业务分支矩阵铺进容器测试、
  测试间数据互相污染、@Transactional 回滚失效、测试基础设施待搭建（生产
  PostgreSQL / MySQL / Redis）、测试用 H2 替代生产数据库、外部 API 真调、
  "返回 200 就是通过了"、跑测试太慢（反复全量 / 全文读输出）。
  边界：开发期与纯单测（@Mock + @InjectMocks，毫秒级，不起容器）→
  java-unit-test；前端 E2E（Selenium / Playwright）/ 性能 / 安全 → 不适用。
version: "1.4.0"
last_verified: "2026-08-21"
---

# Java 集成测试

面向 Java/Spring Boot 的**集成测试 / 冒烟测试 / API 级 E2E** 助手——**在功能稳定后补集成测试层**。两个核心模型：**测试三级分级（T1/T2/T3）**与**阶段闸门**（开发期只写 T1 单测，稳定期才写 T2/T3）。测试重量必须与需求稳定度匹配：重测试写在还在变动的行为上，需求每变一次都要连带重写十秒级测试——这是"测试久过开发"的根源。核心仍是消灭 curl 仿真测试（无断言 / 不可重复 / 不进版本控制，详见铁律 1 + `references/01`）。每条规则含「✗ 错误做法 → ✓ 正确做法」。

## 四条铁律

1. **curl 结果不是测试**：测试必须有结构化断言（HTTP status + response body + jsonPath），而非"看起来返回正常"。curl 是调试工具——开发期探索性验证合法，但其结果不是测试，稳定期必须落成测试代码（时机由阶段闸门定）。
2. **阶段匹配**：开发期（需求未稳定）只写 T1 纯单测（→ java-unit-test），验证靠本地手动跑应用；T2/T3 集成层等稳定期触发点（需求冻结 / 特性过验收 / 发布准备）到了再补。
3. **分级准入**：T3（Testcontainers）只收「离开真实依赖就不成立」的行为；T2 封顶清单内的功能永远不进 T3；Service 业务分支矩阵永远铺在 T1（mock Repository）。
4. **隔离优先**：测试间数据不污染。`@Transactional` 回滚（注意失效场景）、Testcontainers 重置、`@Sql` 清理——一个测试的副作用不能影响另一个。

## 测试三级分级

| 级 | 名称 | 工具 | 起容器 | 速度 | 归属 / 详见 |
|---|---|---|---|---|---|
| **T1** | 纯单元测试 | `@Mock`+`@InjectMocks` | 否（无 Spring） | 毫秒 | → **java-unit-test** |
| **T2** | Spring 切片测试 | `@WebMvcTest` / `@JsonTest` / `@RestClientTest` | 否 | 秒 | 本技能 `03` |
| **T3** | 真实依赖测试 | Testcontainers + `@DataJpaTest` / `@SpringBootTest`；冒烟 / E2E | 是 | 十秒+ | 本技能 `02`+`04`+`07` |

**T2 封顶清单**（最多到切片，永远不进 T3）：Controller 参数校验 / 路由 / 异常处理、JSON 序列化、HTTP 客户端调用逻辑（`@RestClientTest`）、权限控制逻辑。

**T3 准入判据**（机械化自问——每条 T3 用例写前过一遍）：**这条断言离开真实 DB / Redis / Kafka 就不成立吗？**
- 成立（→ T3）：SQL 实际语句与方言特性（`jsonb`/`ARRAY`/`ENUM`）、Flyway / Liquibase 迁移脚本、事务传播实际效果、缓存过期 / 序列化语义、消息协议。
- 不成立（→ T1/T2）：业务规则、多条件分支矩阵、DTO 映射、参数校验、权限逻辑。

**数量锚点**：T3 用例每特性 1~3 条锚定真实行为；分支矩阵（决策表 / 四维度）铺 T1，不铺 T2/T3；E2E 全套件 3~10 条（见 `07`）。

## 阶段闸门

| 阶段 | 判定 | 写什么 | 怎么跑 |
|---|---|---|---|
| **开发期** | 需求未稳定 / 功能还在改 | 只写 T1；存量 T2/T3 照跑照修，不新增宽覆盖 | T1 全量（秒级）+ 本地手动跑应用探索（curl 合法） |
| **稳定期** | 触发点任一：需求冻结 / 特性过验收（DoD）/ 进入发布准备 | 补齐该特性：① T3 锚（迁移可跑 + 启动冒烟 + 核心 SQL 1~3 条）② T2 协议层（参数校验 / 异常处理 / JSON）③ 特性级 T3 用例 1~3 条 | 全量 T1 + T2 + T3 |

- **阶段判定**：一次性问用户"当前是开发期还是稳定期？"，不猜；拿不准默认开发期（从轻）。次级信号：用户说"先这样 / 后面还要改"→ 开发期；"需求定了 / 准备发版"→ 稳定期。
- **运行调度**：内环只跑改动类（`-Dtest`）；提交前全量 T1；CI / 发布门禁全量 T1+T2+T3 + 稳定期补齐检查（该特性集成层未补 → 挡下）。命令细节见 `references/08` §3。
- **不删存量**：判定为开发期不删除既有 T2/T3——它们继续在 CI 跑；只是不新增。

## 测试路由（稳定期；T1 行全周期适用）

| 场景 | 级 | 工具 | 详见 |
|---|---|---|---|
| 单类业务逻辑（含 Service 分支矩阵，调 Repository） | T1 | `@Mock`+`@InjectMocks` | → **java-unit-test** |
| Controller 参数校验 / 路由 / 异常处理 / 权限逻辑 | T2 | `@WebMvcTest` + MockMvc | `03` |
| JSON 序列化 / 反序列化 | T2 | `@JsonTest` | `03` |
| HTTP 客户端调用逻辑（外部 API client） | T2 | `@RestClientTest`（需真 HTTP 隔离时 WireMock） | `03`+`06` |
| Repository SQL / 查询 / 分页 | T3 | `@DataJpaTest` + Testcontainers | `03`+`04` |
| 跨层真实协作 / 事务传播验证 | T3 | `@SpringBootTest(MOCK)` + Testcontainers + `@Transactional` | `02`+`04`+`06` |
| 完整 HTTP API（含过滤器 / 拦截器 / 序列化管道） | T3 | `@SpringBootTest(RANDOM_PORT)` + REST Assured | `02`+`05` |
| "服务能不能启动"冒烟 | T3 | `@SpringBootTest` + Actuator health | `07` |
| 多接口串联业务流程（E2E） | T3 | `@SpringBootTest(RANDOM_PORT)` + REST Assured 多步 | `05`+`07` |
| 外部 HTTP 依赖隔离 | — | WireMock stub（配 T2/T3 均可） | `06` |

> "跨层协作"指验证协作本身（SQL 实际执行 / 事务传播 / 序列化管道）——不是"Service 调了 Repository"（那属 T1，mock Repository 铺分支矩阵）。

## 快速入门

| 你想做的 | 看这份 | 读多少 |
|---|---|---|
| 不知道现在该不该写集成测试 / 用哪级 | `references/01` 阶段闸门 + 分级 + curl 反模式 | 各前 40 行 |
| 写 @SpringBootTest / MockMvc / WebTestClient | `references/02` | 通读 |
| 只测单层 Controller 或 Repository（切片） | `references/03` | 通读 |
| 用真实数据库 / Redis / Kafka 测 | `references/04` | 通读 |
| 写 API 断言（REST Assured given/when/then） | `references/05` | 通读 |
| 测试隔离 / @Transactional 失效 / WireMock | `references/06` | 通读 |
| 冒烟测试 / 多接口串联 E2E | `references/07` | 通读 |
| 跑测试烧 token / 反复全量 / 输出太多 | `references/08` | 通读 |

> `01` 根文件（阶段闸门 + 分级，选层前必读）；`02`-`05` 工具链落地；`06` 隔离陷阱；`07` 冒烟与 E2E；`08` 执行效率与调度。

## 第 0 步：探测项目与场景（激活时先执行）

读项目 `pom.xml` / `build.gradle` 和测试代码，一次性判断：

1. **阶段判定**（最优先）：问用户当前开发期 / 稳定期（判定方式见「阶段闸门」）。**开发期 → 本技能不新增 T2/T3 用例**：新功能测试引导 → java-unit-test；存量集成测试的评审 / 修复照常。
2. **工具栈**：
   - Spring Boot 版本（`pom.xml` 读 `spring-boot-starter-parent`）→ 决定 `@ServiceConnection` 可用性（3.1+）、命名空间（`javax.*` vs `jakarta.*`）、HTTP 测试客户端选型（≤3.x：TestRestTemplate 可用；4.x：TestRestTemplate 废弃，用 RestTestClient——依赖坐标与迁移见 `references/02`）。
   - 是否已有 `testcontainers` / `rest-assured` / `wiremock` 依赖（`grep` 探 `pom.xml`）→ 决定是否需引导引入。
3. **测试场景**（稳定期；每条用例先过 T3 准入判据，再按路由表选行）。
4. **curl 检测**：稳定期正在用 curl 或手动启动应用"测试"→ **立即拦截**，按路由表落成代码；开发期 curl 探索 → 合法调试，提醒稳定期落成。
5. **真实依赖需求判定**（T3 准入判据通过后）：**默认 Testcontainers**——不取决于项目当前是否已引 H2（项目没用 H2、测试未搭，同样引入；H2 只是反例，不是触发前提，详见 `04`）。依赖选择（探测生产 → 询问用户）见「使用流程」第 2 步。

## S 级反模式表（致命——测试存在但测不出问题，或测试成本反超开发）

> S 级：导致"测试存在但测不出问题"或"测试拖垮迭代"——新测试禁止；审查既有测试命中 → 立即指出补全。

| ✗ 错误做法 | ✓ 正确做法 |
|---|---|
| 开发期（需求未稳定）铺 T2/T3 宽覆盖 / E2E | 开发期只写 T1 单测；集成层等稳定期触发点（阶段闸门）——重测试写在变动行为上 = 需求变更放大重写成本 |
| 业务分支矩阵 / 参数校验写进 T3 容器测试 | 分支矩阵铺 T1（mock Repository，毫秒级）；T3 每特性 1~3 条锚定真实行为（准入判据） |
| 用 `curl` 调接口 + 肉眼判断输出 | 用 MockMvc / REST Assured / WebTestClient 写可断言测试（statusCode + body + jsonPath）；开发期 curl 探索合法，稳定期必须落成代码 |
| 手动启动应用再 curl "测试" | `@SpringBootTest(webEnvironment=RANDOM_PORT)` 进程内启动 + 自动断言 |
| 全量 `@SpringBootTest` 测单层 Controller | `@WebMvcTest` 切片测试（T2）——只加载 Web 层，秒级启动 |
| `@Transactional` 回滚用于 `RANDOM_PORT` 场景 | `RANDOM_PORT` 下 HTTP 请求走独立线程，`@Transactional` 回滚**失效**→ 用 `@Sql` 清理 or Testcontainers 重置（见 `06`） |
| 断言真实行为的测试用 H2 替代生产数据库（无论当前是否已引 H2） | T3 测试**默认** Testcontainers 真实容器——消除方言差异（`jsonb`/`ARRAY`/`SERIAL` 等 H2 不支持）；H2 仅限 CI 无 Docker 降级（见 `04`） |
| 外部 API 真调（第三方支付 / 短信） | WireMock stub——可控、可重复、不产生费用 |
| 无断言测试（调一下接口即算"覆盖"） | 每个测试必须有结构化断言：HTTP status + 响应体字段值 |
| `@DirtiesContext` 每个测试都加 | 只在 Context 状态确实被污染时用——它会重建整个 Spring Context（十秒级），优先 `@Sql` / `@Transactional` |
| 启动日志有 WARN/ERROR 但测试绿 | 日志报错 = 测试失败信号，必须排查——Bean 创建失败、Flyway 迁移失败常被 Mock 遮掩 |

## A 级规则表（约定——约束新生成测试）

| ✗ 错误做法 | ✓ 正确做法 |
|---|---|
| 测试间共享数据，互相污染 | 每个 `@Test` 自包含；`@AfterEach` / `@Sql` 清理 |
| 测试依赖执行顺序 | 可乱序执行（JUnit 5 默认）；不依赖 `@Order` |
| `@MockitoBean` 替换大量 Bean | 每组不同 `@MockitoBean` 组合重建 Context → 测试极慢；尽量统一 mock 配置，或用 `@Import` + `@TestConfiguration` |
| `@DataJpaTest` 默认用 H2 但生产是 PostgreSQL | `@AutoConfigureTestDatabase(replace = NONE)` + Testcontainers（见 `04`） |
| `@WebMvcTest` 不 mock Service 导致启动失败 | `@WebMvcTest` 只加载 Web 层——Service 需 `@MockitoBean` 或 `@Import` |
| REST Assured `RestAssuredMockMvc` 当真实 HTTP 用 | `RestAssuredMockMvc` 走 MockMvc（进程内，无真实 HTTP）；要真实 HTTP 用 `RestAssured` + `RANDOM_PORT`（见 `05`） |
| Testcontainers 容器每个测试方法启停 | `@Container` + `static` → 容器全类共享；或 `testcontainers.reuse.enable=true` 跨类复用 |
| WireMock 固定端口，并行测试端口冲突 | WireMock 随机端口（`options().dynamicPort()`）+ `@DynamicPropertySource` 注入 |

## 核心强约束（Agent 必须遵守）

1. **阶段闸门**：开发期不新增 T2/T3 用例（存量照跑照修，不删）；稳定期触发点到达后按「阶段闸门」表补齐三件套（T3 锚 + T2 协议层 + 特性级 T3 用例）。发布门禁核对补齐状态。
2. **T3 分级准入**：每条 T3 用例写前自问"断言离开真实依赖就不成立吗"（SQL / 迁移 / 事务传播 / 缓存语义 / 消息协议）——不成立回 T1/T2。T2 封顶清单（参数校验 / JSON / 权限逻辑 / HTTP 客户端逻辑）永远不进 T3；T3 每特性 1~3 条，分支矩阵不铺容器层。
3. **禁止 curl 测试**：生成测试不得用 `curl` / `httpie` / 手动 HTTP 客户端；必须用 MockMvc / WebTestClient / REST Assured / RestTestClient（Boot 4+，替代 TestRestTemplate）编写含结构化断言的测试（本质见铁律 1）。
4. **`@Transactional` 回滚仅限 `MOCK` 模式**：MOCK 有效、`RANDOM_PORT` 失效（根因见 S 级表 + `references/06`），改用 `@Sql(execution=AFTER_TEST_METHOD)` 或 Testcontainers 重置。
5. **真实依赖默认 Testcontainers**：T3 准入判据通过的测试 → **默认**用 Testcontainers 起同款容器——**不取决于项目当前是否已引 H2**（没用 H2、测试未搭，同样引入）。H2 仅限 CI 无 Docker 时的显式降级（见 `references/04` checklist）；方言差异是"测试绿生产炸"头号来源。
6. **外部依赖必须 stub**：调用外部 HTTP API（支付 / 短信 / 第三方认证）必须用 WireMock stub，不得真调（理由见 S 级表）。
7. **`@DirtiesContext` 是最后手段**：重建整个 Context（十秒级，代价见 S 级表），仅在 Bean 内部状态被污染且无法用 `@Sql` / `@Transactional` / Testcontainers 重置时才用。
8. **Context 缓存友好**：`@MockitoBean` / `@MockitoSpyBean` / `@SpringBootTest` 属性的组合变化会导致 Context 缓存失效并重建。统一测试的 mock 配置，避免每个测试类用不同 `@MockitoBean` 组合。
9. **执行降噪 + 分层调度**：`mvn test` 分层降噪——`-B -ntp`（下载噪声）+ `-q` 或 `org.slf4j.simpleLogger` 级别（Maven 日志）+ `logging.level.root`（Spring 日志，`-q` 管不到它）；**不全文回传 stdout**；失败读 `target/surefire-reports/*.txt` 定位、`-Dtest` 单测重跑，不反复全量、不每次 `clean`。内环只跑改动类、提交前全量 T1、CI 全量（调度表见 `references/08` §3）。

## 使用流程

1. **第 0 步探测**：阶段判定（最优先）→ 工具栈 → 测试场景 → curl 检测 → 真实依赖需求判定。
2. **依赖选择询问**：涉及真实依赖时——探测生产依赖（驱动 / datasource / docker-compose）→ 给候选版本询问用户（对齐生产优先，推荐值见 `04` §依赖选择）→ 落定后写代码。**不静默选镜像 tag。**
3. **读 `references/01`**：确认阶段与分级（T2 / T3）。
4. **定位工具 reference**：按路由表读 `02`-`05` 对应文件。
5. **隔离策略**：读 `references/06`，确定数据清理方案（`@Transactional` / `@Sql` / Testcontainers 重置 / WireMock）。
6. **执行效率**：读 `references/08`——分层调度、`mvn test` 降噪输出、`-Dtest` 单测迭代，不全文读输出。
7. **输出前自检**：逐项核对下方「输出前自检清单」——任一项未过，不得交付。

## 输出前自检清单（交付测试代码前逐项核对，任一未过不得交付）

- [ ] 已过阶段闸门——当前稳定期（或本任务是对存量测试的评审 / 修复）；开发期未新增 T2/T3 用例
- [ ] 每条 T3 用例过准入判据（断言离开真实依赖就不成立）；每特性 ≤3 条；分支矩阵未铺在容器层
- [ ] 无 `curl` / `httpie` / 手动启动应用调接口——测试用 MockMvc / WebTestClient / REST Assured / RestTestClient（Boot 4+）编写
- [ ] 每个测试有结构化断言：HTTP status + 响应体字段值（jsonPath / expectBody）
- [ ] `@Transactional` 回滚仅用于 `MOCK` 模式——`RANDOM_PORT` / `DEFINED_PORT` 场景已改 `@Sql` / Testcontainers 重置
- [ ] T3 测试用 Testcontainers 真实容器——未静默用 H2 替代；容器镜像版本已探测生产 + 询问用户确认（`04` §依赖选择）
- [ ] 外部 HTTP 依赖（支付 / 短信 / 三方认证）全部 WireMock stub，无真调
- [ ] 单层测试用切片（`@WebMvcTest` / `@JsonTest`），未用全量 `@SpringBootTest` 测单层
- [ ] `@DirtiesContext` 仅在状态无法用 `@Sql` / `@Transactional` / Testcontainers 重置时使用
- [ ] 启动日志无未排查的 WARN / ERROR
- [ ] 依赖坐标与 Boot 版本匹配：Boot 4 → RestTestClient（非 TestRestTemplate）、`@MockitoBean`（非 `@MockBean`，已移除）、`@AutoConfigureMockMvc` 显式标注、Testcontainers 2.x 新模块名（`testcontainers-*`）、rest-assured 手写 6.x；Boot ≤3.x → 旧坐标、BOM 已管的不写 `<version>`（`references/02` / `04` / `05`）

## 版本与范围

- Spring Boot 2.7.x / 3.x / 4.x 均适用；3.1+ 新增 `@ServiceConnection`（Testcontainers 自动连接），3.0 及以下用 `@DynamicPropertySource`。
- **Boot 4 测试工具链变化**：① `TestRestTemplate` 废弃——拆到独立模块 `org.springframework.boot:spring-boot-resttestclient`（test scope），升级 Boot 4 后原注入直接失败；新测试用 `RestTestClient` + `@AutoConfigureRestTestClient`（迁移对照见 `references/02`）。② Testcontainers 跳到 2.x——模块加 `testcontainers-` 前缀（旧名 2.x 下 404）、容器类移独立包且无泛型（对照表见 `references/04`）。③ `@MockBean` / `@SpyBean` **已移除**（编译错误）→ 换 `@MockitoBean` / `@MockitoSpyBean`（Boot 3.4+ 可用，字段直接替换；不能声明在 `@Configuration` 类里，见 `references/02`）。④ `@SpringBootTest` 不再自动配置 MockMvc——必须显式 `@AutoConfigureMockMvc`。
- JUnit 版本不手选——由 `spring-boot-starter-test` 传递：Boot ≤3.x = JUnit 5，Boot 4 = JUnit 6；坐标均为 `org.junit.jupiter:junit-jupiter`，写法一致。JUnit 4 遗留项目：用 `@RunWith(SpringRunner.class)` 替代 `@ExtendWith`，断言用 `org.junit.Assert`，生命周期注解为 `@Before`/`@After`；其余写法与本技能示例一致。
- **与 `java-unit-test` 的边界与接力**：开发期只写 T1 纯单测（`@Mock`+`@InjectMocks`，毫秒级，不起 Spring、不起容器，单类逻辑含 Service 分支矩阵）→ java-unit-test；稳定期由阶段闸门进入本技能——T2 切片、T3 真实依赖、冒烟、E2E。"跨层协作"指验证协作本身（SQL 实际执行 / 事务传播 / 序列化管道），不是"Service 调了 Repository"。Context 内替换 Bean 的注解分界（`@MockitoBean`，Boot ≤3.3 遗留写法为 `@MockBean`）：纯单测用 `@Mock`（→ java-unit-test），切片 / 集成测试用 `@MockitoBean`（→ 本技能）。
- **不适用**：前端 E2E（Selenium / Playwright / Cypress）、性能测试（JMeter / Gatling）、安全测试。
