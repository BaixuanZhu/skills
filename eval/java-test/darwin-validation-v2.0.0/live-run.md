# 实跑记录（v2.0.0 达尔文验证）

> 目的：盲评推演之外，用真实 Maven 项目验证 v2.0.0 新口径的**可执行性**——①「纯单测毫秒级 / mvn test 秒级」量级主张；②「*IT 命名分离 + failsafe」机械保障；③抽查 Boot 4 版本事实。scratch 项目：`outputs/java-test-v2-live/`（gitignored，不入 git）。
> 环境：JDK 21.0.12 / Spring Boot 4.0.5（parent）/ maven-failsafe-plugin（Boot parent 管版本）/ docker 29.8 在跑但本轮未用容器。
> 日期：2026-10-04

## 项目构成

- 主代码：`OrderService`（qty 1~99 校验 / 券与 vip 折扣 / 支付被拒抛 IllegalStateException）、`Order` + `OrderStatus` 状态机（`canTransitTo` 全矩阵）、`OrderRepository`（内存实现 Bean）、`PaymentClient`（外部依赖接口）。
- 测试（对应 v2 分级模型）：
  - `OrderServiceTest`（`*Test`，surefire）：@Mock+@InjectMocks 纯单测，四维度（正向 / qty 边界 0·1·99·100 参数化 / 券 null+空 / 支付被拒 / 非法单价）——**开发期层**。
  - `OrderStatusTest`（`*Test`，surefire）：状态机全矩阵 + 终态封锁 + 非法迁移 assertThrows——**开发期层**。
  - `OrderFlowIT`（`*IT`，failsafe）：@SpringBootTest + @MockitoBean PaymentClient + 真实 Bean 协作——**真实依赖层**的形态缩影（无容器版）。

## 结果 1：命名分离的机械保障实测成立

| 命令 | 执行的测试 | failsafe 触及 *IT？ |
|---|---|---|
| `mvn test` | 仅 `OrderServiceTest` + `OrderStatusTest`（18 个） | **否**（全日志 grep `failsafe\|OrderFlowIT` 零命中） |
| `mvn verify` | 18 个单测 + `OrderFlowIT`（failsafe 阶段执行） | 是 |

`mvn test` 永不跑 `*IT`——v2「命名分离（mvn test 保持轻量）」不是口号，是 surefire/failsafe 插件契约的机械结果。

## 结果 2：轻 vs 重的量级实测（"测试久过开发"的量化）

| 测试 | 个数 | surefire/failsafe 报告耗时 | 单条量级 |
|---|---|---|---|
| `OrderStatusTest`（纯单测，无 mock） | 9 | 0.030~0.045s | **≈3-5ms/条** |
| `OrderServiceTest`（纯单测，Mockito） | 9 | 4.5~4.7s/类 | ≈0.5s/条（含 Mockito+参数化框架首启） |
| `OrderFlowIT`（@SpringBootTest MOCK） | 1 | **2.376s** | 2.4s/条（几乎全是上下文启动） |

- **1 条 @SpringBootTest IT ≈ 800 条无 mock 单测 / ≈ 5 条 Mockito 单测的执行时间**；Testcontainers 再叠加容器拉起（十秒级）。
- 把 20 条业务分支矩阵写进容器层（v1 无准入判据时的典型走向）≈ 48s+；同样 20 条纯单测（含 Mockito 桩）≈ 10s 内，无 mock 版 < 0.1s——v2「容器每特性 1~3 条、分支矩阵永远铺纯单测」的数量锚点有直接的时间账支撑。
- 内环迭代（改动后 `mvn test`，热态离线 10s 全程含编译检查）vs `mvn verify` 16s（+1 条 IT）——开发期 `mvn test` 秒级主张成立。

## 结果 3：Boot 4 事实抽查

- `@MockitoBean`（org.springframework.test.context.bean.override.mockito）注入**上下文中无实现 Bean 的接口**（PaymentClient）：实测可用，mock Bean 直接供给真实 Bean 构造注入——v2 `02` 的口径成立。
- 首跑 `OrderFlowIT` 失败（exit=1）：`OrderService` 未标 `@Service`，上下文无该 Bean，`@Autowired` 失败。**这本身就是"重型测试的隐性装配成本"的现场证据**——纯单测直接 `@InjectMocks` 构造，对 Spring 装配注解零要求；重型层不仅慢，还把"类必须可被容器装配"变成测试的前置条件。修复（补 `@Service`）后全绿。

## 取舍说明

- 未实跑 Testcontainers 容器测试：`references/04` 两版**逐字相同**（321 行），无判别价值；容器拉起成本与本轮验证目标无关。docker 环境在跑，如需 TC 全链路验证可补。
- 未实测 Boot 4 `@MockBean` 编译错误 / TestRestTemplate 废弃坐标：属 `02`/`04` 未动部分，v1.3.0 轮已覆盖或非本轮口径变化。

## 结论

v2.0.0 的三条新口径——**零基础设施（毫秒级）**、**命名分离（mvn test 不碰 *IT）**、**数量锚点（分支矩阵不进容器）**——全部实测可执行，量级主张与时间账吻合。
