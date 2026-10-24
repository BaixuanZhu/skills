---
name: java-integration-test
slug: java-integration-test
displayName: Java 重型测试
description: >-
  Java/Spring Boot 重型测试助手——测试自管真实依赖：Testcontainers 起真实
  PostgreSQL / MySQL / Redis / Kafka、迁移可重放、事务传播真实效果、冒烟测试、
  API 级 E2E、WireMock 隔离外部调用、契约切片层（@WebMvcTest / @JsonTest /
  @RestClientTest）。仅当需求明确需要重型 / 真实环境测试时使用本技能：用户明示
  （"补集成测试 / 需求冻结 / 准备发版"）→ 直接开始；仅能推断出需要 → 先询问
  "是否开始写重型测试"，确认后动手；无信号 → 不写，新功能测试 → java-unit-test
  （纯单测）。核心：可断言、可重复、可版本控制，替代 curl 调接口 + 肉眼判断；
  断言真实行为的测试默认 Testcontainers 真实容器，不用 H2 替代（方言差异是
  "测试绿生产炸"头号来源）。分层由一条判据决定——这条断言离开真实
  DB / Redis / Kafka 就不成立吗？
  次级触发信号：功能已稳定要补集成层、用 curl 或手动启动应用调接口"测试"、
  @SpringBootTest 全量上下文测单层 Controller、业务分支矩阵铺进容器测试、
  测试间数据互相污染、@Transactional 回滚失效、测试用 H2 替代生产数据库、
  @DataJpaTest 默认换了内嵌库、外部 API 真调、"返回 200 就是通过了"、
  启动日志有 WARN/ERROR 但测试全绿。
  边界：纯单测（开发期默认层，零外部基础设施）→ java-unit-test；
  前端 E2E（Selenium / Playwright）/ 性能 / 安全 → 不适用。
version: "2.1.0"
last_verified: "2026-10-24"
---

# Java 重型测试（集成 / 冒烟 / E2E）

本技能管理**测试自管依赖**的重型测试：Testcontainers、迁移可重放、真实事务传播、冒烟、E2E、外部依赖 WireMock 隔离，以及功能稳定后补齐的契约切片层。与开发期测试的分界沿**依赖轴**——开发期测试只用内存 mock、零外部基础设施（→ java-unit-test）；本技能的测试自己拉起并管理真实依赖，CI 无预置环境也可重复跑。

## 激活协议

| 信号 | 判定 | 动作 |
|---|---|---|
| **明示**：用户说"补集成测试 / 需求冻结 / 特性验收了 / 准备发版 / 要 Testcontainers" | 需求明确要重型测试 | 直接开始，不再追问 |
| **推断**：特性已稳定 + SQL 密集 + 集成覆盖为零，但用户没说 | 可能需要，未确认 | 先问"是否开始为 X 补重型集成测试"，确认后动手 |
| **无信号**：开发期常规写码 / 新功能开发 | 不需要 | 不新增重型测试；新功能测试 → java-unit-test；存量照跑照修 |

> 重型测试是十秒级/条的重资产，写在还在变动的行为上 = 需求每变一次连带重写。默认永远从轻，重的东西等人开口。

## 该用哪一层

**容器准入判据**：这条断言**离开真实 DB / Redis / Kafka 就不成立吗？**

- 成立 → 容器：SQL 方言特性（`jsonb` / `ARRAY` / `ENUM`）、迁移脚本、事务传播实际效果、缓存过期与序列化语义、消息协议。
- 不成立 → 不进容器：业务规则、多条件分支矩阵、DTO 映射、参数校验、权限逻辑、JSON 编解码、HTTP 客户端逻辑。

| 测什么 | 层 | 工具 |
|---|---|---|
| Service 分支矩阵（mock Repository） | 纯单测 | → java-unit-test |
| Controller 参数校验 / 路由 / 异常处理 / JSON | 契约切片 | `@WebMvcTest` / `@JsonTest` / `@RestClientTest` |
| SQL 实际执行 / 迁移 / 事务传播 | 容器 | `@SpringBootTest` 或 `@DataJpaTest` + Testcontainers |
| 完整 HTTP 管道（过滤器 / 拦截器 / 序列化） | 容器 | `@SpringBootTest(RANDOM_PORT)` |
| 服务能不能启动 | 容器 | `@SpringBootTest` + Actuator health |
| 多接口串联业务流程 | 容器 | `RANDOM_PORT` 多步 |
| 外部 HTTP 依赖隔离 | — | WireMock stub，不真调 |

容器用例每特性 1~3 条锚定真实行为；分支矩阵铺纯单测，不铺容器层。集成测试类名 `*IT`（failsafe，`mvn verify`），`mvn test` 保持开发期轻量。

**curl 结果不是测试**：必须有结构化断言（status + body 字段），"看起来返回正常"不算。手动启动应用再肉眼判断同样不算。

## 静默陷阱（写错不报警，测试仍然绿）

下表是索引。命中任一条时读 `references/01-pitfalls.md`——那里有完整代码与**怎么验证自己不是假绿**。

| ✗ 写法 | 为什么绿 | ✓ 改法 |
|---|---|---|
| 测试方法加 `@Transactional` 验证回滚 | 被测 Service 的 `REQUIRED` 事务并入测试事务，异常只标记 rollback-only；对同一连接扣减仍可见，回滚断言永远通过 | 测试不加 `@Transactional`，让 Service 自己提交 / 回滚，再用 `@AfterEach` 或独立库名清理 |
| `@Transactional` 配 `RANDOM_PORT` | HTTP 请求走独立线程，测试事务根本不生效——以为隔离了，实际脏数据留在库里 | `RANDOM_PORT` 场景一律显式清理：`@Sql` / 精确 `DELETE` / 每类独立库名 |
| `@DataJpaTest` / `@JdbcTest` 默认换内嵌库 | 自动把 `DataSource` 替换成 H2，生产库才有的方言行为（`jsonb`、`ARRAY`、`ON CONFLICT`）测不到 | `@AutoConfigureTestDatabase(replace = NONE)` + Testcontainers 同款镜像 |
| 用 H2 跑"集成测试" | 方言差异只在生产暴露；`SERIAL` / 序列 / 排序 / 大小写敏感性都可能不同 | 断言真实行为的测试默认 Testcontainers；H2 仅在 CI 无 Docker 时显式降级，并在报告里写明 |
| `RestAssuredMockMvc` 当真实 HTTP 用 | 走进程内 MockMvc，过滤器、序列化、线程模型都没经过 | 要真实 HTTP 用 `RANDOM_PORT` + 真实客户端 |
| 启动日志里有 WARN / ERROR 但测试全绿 | Bean 创建失败、迁移失败常被 Mock 遮掩，测试看起来正常 | 日志报错即失败信号，必须排查，不能因为绿就放过 |
| 外部 API 真调（支付 / 短信 / 三方认证） | 测试依赖对方可用性，产生费用，结果不可重复 | WireMock stub，随机端口 + `@DynamicPropertySource` 注入 |
| `@DirtiesContext` 每个测试都加 | 不是错，是每用一次重建整个 Context（十秒级） | 只在 Bean 内部状态被污染且无法用 `@Sql` / Testcontainers 重置时用 |
| `@MockitoBean` 组合频繁变化 | 每组不同组合生成一个新 Context，缓存失效，全量套件越跑越慢 | 统一 mock 配置；能用 `@TestConfiguration` 固定装配就别分散 |

## 数据隔离三选一

| 手段 | 适用 | 代价 |
|---|---|---|
| 测试方法 `@Transactional` 回滚 | 只有 `MOCK` 模式的 `@SpringBootTest` 与切片测试 | `RANDOM_PORT` 下失效（见上表） |
| `@Sql` / 精确 `DELETE` 清理 | 任何模式 | 要写清理语句，漏表就残留 |
| 每个测试类独立库名 / 独立容器 | 需要并行、需要真提交的用例 | 上下文或容器多一份，启动更慢 |

## 交付前自检

- [ ] 已过激活协议（用户明示或确认）；未激活时没有新增重型用例
- [ ] 每条容器用例过准入判据，每特性 ≤3 条，分支矩阵不在容器层
- [ ] 类名 `*IT`，没混进 `mvn test`
- [ ] 每个测试有结构化断言（status + 响应体字段），没有 curl / 肉眼判断
- [ ] 验证回滚的用例**没有**用测试级 `@Transactional`；`RANDOM_PORT` 场景已改为显式清理
- [ ] 断言真实行为时用的是同款容器，没静默换 H2；镜像版本对齐生产并告知用户
- [ ] 启动日志里的 WARN / ERROR 已排查

## 版本与范围

- Spring Boot 2.7 / 3.x / 4.x 均适用。Boot 4 的测试工具链有破坏性变化（`TestRestTemplate` 废弃、`@MockBean` 移除、Testcontainers 模块改名），这些都是**编译错误**，升级时会立刻暴露，按编译提示改即可。
- 镜像 tag 一律对齐生产版本，不硬编码某个 patch 号——具体数值写在项目配置里，不在技能里。
- **与 `java-unit-test` 的边界（依赖轴）**：纯单测（`@Mock`+`@InjectMocks` 或只装 mock 的 `@TestConfiguration`，毫秒级，零外部基础设施）→ java-unit-test；测试**自管**真实依赖 → 本技能，明示或确认后激活。注解分界：无 Context 的 `@Mock`、只装 mock 的 `@TestConfiguration` 属前者；`@SpringBootTest` / `@MockitoBean` / 切片注解属本技能。
- **不适用**：前端 E2E（Selenium / Playwright / Cypress）、性能测试、安全测试。
