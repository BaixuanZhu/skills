---
name: java-integration-test
slug: java-integration-test
displayName: Java 集成测试
description: >-
  Java/Spring Boot 集成测试助手——测试自管真实依赖：真实 PostgreSQL / MySQL /
  Redis / Kafka、迁移可重放、事务传播真实效果、冒烟测试、API 级 E2E、WireMock
  隔离外部调用、契约切片层（@WebMvcTest / @JsonTest / @RestClientTest）。
  三个决策按序：① 建不建（这段代码的回归由谁值守——有专职测试就不自建，个人/
  小团队自动化是唯一回归网）② 放哪层（断言离开真实依赖还成立吗）③ 用什么跑
  （Docker → Testcontainers / 本地实库 + 独立 schema / 都没有 → 事务与约束用 H2
  验、方言相关列清单移交真库）。
  Testcontainers 是首选执行方式，不是本技能定义；降级必须写明走了哪条与环境盲区，
  不许静默拿 H2 当生产方言。仅当需求明确需要这一层时使用：用户明示（"补集成
  测试 / 需求冻结 / 准备发版"）→ 直接开始；仅能推断 → 先问一句；无信号 → 不写，
  新功能测试 → java-unit-test。
  次级触发信号：功能已稳定要补集成层、用 curl 或手动启动应用调接口"测试"、
  @SpringBootTest 全量上下文测单层 Controller、业务分支矩阵铺进容器测试、
  测试间数据互相污染、@Transactional 回滚失效、测试用 H2 替代生产数据库、
  @DataJpaTest 默认换了内嵌库、外部 API 真调、"返回 200 就是通过了"、
  启动日志有 WARN/ERROR 但测试全绿、本机没有 Docker 或 CI 没有 DinD。
  边界：纯单测（开发期默认层，零外部基础设施）→ java-unit-test；
  前端 E2E（Selenium / Playwright）/ 性能 / 安全 → 不适用。
version: "2.2.0"
last_verified: "2026-10-24"
---

# Java 集成测试（真实依赖 / 冒烟 / E2E）

本技能管**测试自己拉起并管理真实依赖**的那一层：真实数据库与中间件、迁移可重放、事务传播的实际效果、冒烟、API 级 E2E、外部调用隔离。与开发期测试的分界沿**依赖轴**——开发期零外部基础设施（→ java-unit-test），本层自己起依赖，CI 无预置环境也能重复跑。

**Testcontainers 是首选执行方式，不是本层定义。** 它属回归阶段，开发阶段要的是毫秒级反馈。没有 Docker 时本层仍有合法路径，见决策 ③。

## 三个决策，按序走完

跳过 ① 直接问"怎么起容器"，等于假定这一层一定要有。

### ① 建不建 —— 这段代码的回归由谁值守

| 值守情况 | 动作 |
|---|---|
| 有专职测试 / QA | 不自建，开发只保证单测绿；用户明示要才写 |
| 无专职测试（个人 / 小团队） | 建，但优先**冒烟 + 核心链路**，不铺分支矩阵 |
| 判断不了 | 先问"这个模块的回归谁跑"，再决定 |

不自建不是偷懒——专职同学的用例会长期维护，你写的那份下次需求变更就烂在那。

> ① 只决定**集成层**建不建。契约切片（`@WebMvcTest` / `@JsonTest` / `@RestClientTest`）秒级、不碰真实依赖，不受 ① 排除——有专职测试也照写。

**激活时机**（与上表叠加）：

| 信号 | 动作 |
|---|---|
| **明示**：用户说"补集成测试 / 需求冻结 / 准备发版 / 要 Testcontainers" | 直接开始，不追问 |
| **推断**：特性已稳 + SQL 密集 + 覆盖为零，用户没说 | 先问一句，确认后动手 |
| **无信号**：开发期常规写码 / 新功能开发 | 不新增；新测试 → java-unit-test；存量照跑照修 |

> 这一层是十秒级/条的重资产，写在还变动的行为上 = 需求每变一次连带重写。默认永远从轻，重的东西等人开口。

### ② 放哪层 —— 这条断言离开真实依赖还成立吗

- 成立 → 集成层：SQL 方言特性（`jsonb` / `ARRAY` / `ENUM`）、迁移脚本、事务传播实际效果、缓存过期与序列化语义、消息协议。
- 不成立 → 不进集成层：业务规则、多条件分支矩阵、DTO 映射、参数校验、权限逻辑、JSON 编解码、HTTP 客户端逻辑。

| 测什么 | 层 | 工具 |
|---|---|---|
| Service 分支矩阵（mock Repository） | 纯单测 | → java-unit-test |
| Controller 参数校验 / 路由 / 异常处理 / JSON | 契约切片 | `@WebMvcTest` / `@JsonTest` / `@RestClientTest` |
| SQL 实际执行 / 迁移 / 事务传播 | 集成层 | `@SpringBootTest` 或 `@DataJpaTest` + 真实库 |
| 完整 HTTP 管道（过滤器 / 拦截器 / 序列化） | 集成层 | `@SpringBootTest(RANDOM_PORT)` |
| 服务起得来 + 核心链路通（冒烟 / 多接口串联） | 集成层 | `@SpringBootTest` + Actuator health、`RANDOM_PORT` 多步 |
| 外部 HTTP 依赖隔离 | — | WireMock stub，不真调 |

集成用例每特性 1~3 条锚定真实行为；分支矩阵铺纯单测，不铺集成层。无专职测试时冒烟优先于逐特性用例——部署炸比逻辑错更致命。类名 `*IT`（failsafe，`mvn verify`），`mvn test` 保持开发期轻量。

**curl 结果不是测试**：必须有结构化断言（status + body 字段），"看起来返回正常"不算。手动启动应用再肉眼判断同样不算。

### ③ 用什么跑 —— 环境起得起容器

| 环境 | 路径 | 代价 |
|---|---|---|
| 有 Docker（本机或 CI） | Testcontainers，镜像 tag 对齐生产 | 单条十秒级，首次拉镜像慢 |
| 无 Docker，本机能起真实库 | 连本地实库 + 每个测试类独立 schema | **不可重复**：换机器 / 上 CI 就挂，库版本可能与生产不一致 |
| 都没有 | 能验的用 H2 验，不能验的列清单移交真库 | 有盲区，必须逐条写明 |

第三条怎么切，看**这条断言依赖什么**：

| 断言依赖什么 | H2 能验吗 | 例子 |
|---|---|---|
| 事务传播与回滚的最终状态 | 能 | 写订单失败后库存是否恢复 |
| 唯一约束是否真的拦住 | 能 | 重复订单号插入被拒 |
| SQL 方言特性 | 不能 | `jsonb` / `ARRAY` / `ON CONFLICT` / 排序与大小写敏感性 |
| 具体错误码与异常类型 | 不能 | 驱动异常层次与错误码两边不同 |

**选了哪条必须写进回复**（例："走第二条，依赖本机 MySQL，不可重复"）。用 H2 时同样要标注：「非生产方言，以下行为未验」并列出移交清单。

**空手说"不写"和"用 H2 冒充真库"一样不合格**——前者放弃了本来能自动兜住的回滚与约束。事务提交/回滚的最终状态是 JDBC/Spring 语义，与方言无关，H2 上验是有效的；只有方言特征必须等真库。

## 静默陷阱（写错不报警，测试仍然绿）

下表是索引。命中任一条时读 `references/01-pitfalls.md`——那里有完整代码与**怎么验证自己不是假绿**。

| ✗ 写法 | 为什么绿 | ✓ 改法 |
|---|---|---|
| 测试方法加 `@Transactional` 验证回滚 | 被测 Service 的 `REQUIRED` 事务并入测试事务，异常只标记 rollback-only；对同一连接扣减仍可见，回滚断言永远通过 | 测试不加 `@Transactional`，让 Service 自己提交 / 回滚，再用 `@AfterEach` 或独立库名清理 |
| `@Transactional` 配 `RANDOM_PORT` | HTTP 请求走独立线程，测试事务根本不生效——以为隔离了，实际脏数据留在库里 | `RANDOM_PORT` 场景一律显式清理：`@Sql` / 精确 `DELETE` / 每类独立库名 |
| `@DataJpaTest` / `@JdbcTest` 默认换内嵌库 | 自动把 `DataSource` 替换成 H2，生产库才有的方言行为（`jsonb`、`ARRAY`、`ON CONFLICT`）测不到 | `@AutoConfigureTestDatabase(replace = NONE)` + 决策 ③ 选定的路径 |
| 用 H2 跑方言相关断言且不声明 | 方言差异只在生产暴露，测试绿生产炸 | 事务与约束语义可用 H2；方言断言必须真库验，回复里写明 H2 的盲区 |
| `RestAssuredMockMvc` 当真实 HTTP 用 | 走进程内 MockMvc，过滤器、序列化、线程模型都没经过 | 要真实 HTTP 用 `RANDOM_PORT` + 真实客户端 |
| 启动日志里有 WARN / ERROR 但测试全绿 | Bean 创建失败、迁移失败常被 Mock 遮掩，测试看起来正常 | 日志报错即失败信号，必须排查，不能因为绿就放过 |
| 外部 API 真调（支付 / 短信 / 三方认证） | 测试依赖对方可用性，产生费用，结果不可重复 | WireMock stub，随机端口 + `@DynamicPropertySource` 注入 |
| `@DirtiesContext` 每个测试都加 | 不是错，是每用一次重建整个 Context（十秒级） | 只在 Bean 内部状态被污染且无法用 `@Sql` / 容器重置时用 |
| `@MockitoBean` 组合频繁变化 | 每组不同组合生成一个新 Context，缓存失效，全量套件越跑越慢 | 统一 mock 配置；能用 `@TestConfiguration` 固定装配就别分散 |

## 数据隔离三选一

| 手段 | 适用 | 代价 |
|---|---|---|
| 测试方法 `@Transactional` 回滚 | 只有 `MOCK` 模式的 `@SpringBootTest` 与切片测试 | `RANDOM_PORT` 下失效（见上表） |
| `@Sql` / 精确 `DELETE` 清理 | 任何模式 | 要写清理语句，漏表就残留 |
| 每个测试类独立库名 / 独立容器 | 需要并行、需要真提交的用例 | 上下文或容器多一份，启动更慢 |

## 交付前自检

- [ ] 已过决策 ①（值守 + 时机）；没通过时没有新增集成用例
- [ ] 回复里写明了决策 ③ 走的是哪条路径；用 H2 时标了盲区并列出移交真库的清单
- [ ] 每条用例过准入判据，每特性 ≤3 条，分支矩阵不在这一层
- [ ] 类名 `*IT`，没混进 `mvn test`
- [ ] 每个测试有结构化断言（status + 响应体字段），没有 curl / 肉眼判断
- [ ] 验证回滚的用例**没有**用测试级 `@Transactional`；`RANDOM_PORT` 场景已改为显式清理
- [ ] 断言真实行为时用的是真实库，没静默换 H2
- [ ] 启动日志里的 WARN / ERROR 已排查
- [ ] 外部依赖走 WireMock，没有真调

## 版本与范围

- Spring Boot 2.7 / 3.x / 4.x 均适用。Boot 4 的测试工具链有破坏性变化（`TestRestTemplate` 废弃、`@MockBean` 移除、Testcontainers 模块改名），这些都是**编译错误**，升级时会立刻暴露，按编译提示改即可。
- 镜像 tag 一律对齐生产版本，不硬编码某个 patch 号——具体数值写在项目配置里，不在技能里。
- **注解分界**：无 Context 的 `@Mock`、只装 mock 的 `@TestConfiguration` → java-unit-test；`@SpringBootTest` / `@MockitoBean` / 切片注解 → 本技能。过了决策 ① 才动手。
- **不适用**：前端 E2E（Selenium / Playwright / Cypress）、性能测试、安全测试。
