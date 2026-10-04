# 01 · 激活协议、分级与 curl 反模式

> 根文件，决定"该不该写重型测试、写哪层"前必读。所有工具链 reference（02-05）建立在本文件的分级模型上。示例注解 `@MockitoBean` 需 Boot 3.4+（≤3.3 写作 `@MockBean`，4.0 已移除旧注解——版本口径见 `02`）。

## 激活协议：现在写不写重型测试？

重型测试是十秒级/条的重资产，测试自己拉起并管理真实依赖（Testcontainers）。写在还在变动的行为上 = 需求每变一次就多付一次重写成本（"测试久过开发"的根源）。因此**先过激活，再选层**：

| 信号 | 判定 | 动作 |
|---|---|---|
| **明示**（"补集成测试 / 需求冻结 / 验收 / 发版 / 要 Testcontainers"） | 需求明确 | 直接开始 |
| **推断**（特性稳定 + SQL 密集 + 集成覆盖为零） | 可能需要 | **询问确认**后动手 |
| **无信号**（开发期常规写码） | 不需要 | 不写；新功能测试 → java-unit-test；存量照跑照修 |

> 激活后补齐顺序：容器锚（迁移可跑 + 启动冒烟 + 核心 SQL 1~3 条）→ 契约切片层 → 特性级容器用例。运行调度（内环 / 提交 / CI 分层跑）见 `08` §3。

## 分级模型

| 层 | 测什么 | 起容器 | 速度 | 本技能覆盖 | 对应技能 |
|---|---|---|---|---|---|
| **纯单测**（开发期默认层） | 单类逻辑，依赖全 Mock（含 Service 分支矩阵） | 否（无 Spring） | 毫秒 | ✗ | java-unit-test |
| **契约切片层** | 单层协议行为：参数校验 / 路由 / 异常处理 / JSON / HTTP 客户端逻辑 / 权限逻辑 | 否 | 秒 | ✓ `03` | 本技能 |
| **真实依赖层** | 离开真实依赖就不成立的行为：SQL / 方言 / 迁移 / 事务传播 / 缓存语义 / 消息协议；冒烟；E2E | 是（Testcontainers） | 十秒+ | ✓ `02`+`04`+`07` | 本技能 |

> 前端 E2E（Selenium / Playwright）和性能测试不在本技能范围。

**容器准入判据**（机械化）：**这条断言离开真实 DB / Redis / Kafka 就不成立吗？**——SQL 实际语句与方言特性、Flyway / Liquibase 迁移脚本、事务传播实际效果、缓存过期 / 序列化语义、消息协议 → 容器；业务规则、多条件分支矩阵、DTO 映射、参数校验、权限逻辑 → 开发期测试 / 契约切片。

**数量结构**（防"测试久过开发"）：纯单测数十~数百（主力，→ java-unit-test）；切片十~数十（每层关键行为）；容器每特性 1~3 条；E2E 全套件 3~10 条（见 `07`）。

## 决策树：选哪一层？（激活后）

```
先过激活协议：明示 / 确认激活了吗？
├─ 否 → 纯单测 → java-unit-test，本技能不介入
└─ 是 → 你要测什么？
   ├─ 单个类的方法逻辑（Service / Util / 计算，含分支矩阵）
   │  → 仍是纯单测 → java-unit-test
   ├─ 断言离开真实依赖就不成立？（SQL / 迁移 / 事务传播 / 缓存语义 / 消息协议）
   │  ├─ Repository SQL / 查询 / 分页 → @DataJpaTest + Testcontainers → 03 + 04
   │  ├─ 跨层真实协作 / 事务传播 → @SpringBootTest(MOCK) + Testcontainers → 02 + 04 + 06
   │  ├─ "服务能不能正常启动" → Actuator health 冒烟 → 07
   │  └─ 多接口串联业务流程 → API 级 E2E → 05 + 07
   └─ 其余单层协议行为
      ├─ Controller 参数校验 / 路由 / 异常处理 / 权限 → @WebMvcTest → 03
      ├─ JSON 序列化 / 反序列化 → @JsonTest → 03
      └─ HTTP 客户端调用逻辑 → @RestClientTest（真 HTTP 隔离 WireMock）→ 03 + 06
```

## curl 反模式（核心护栏）

测试的 FIRST 原则中，curl 至少违反三条：**S**elf-validating（肉眼判断，无断言——200 + 错误 JSON 体 = "通过"）、**R**epeatable（依赖手动启动 + 手动执行，CI 中不存在）、**T**horough（one-liner 不进版本控制，回归保护为零）。

**典型翻车**：返回 200 但订单金额算错、库存没扣——全被 200 掩盖；第二次跑用户名冲突 409——代码没变，结果取决于数据库残留状态。

```bash
# ✗ curl "测试"
curl -X POST http://localhost:8080/api/orders -d '{"productId":1,"qty":2}'
```

```java
// ✓ 可断言测试（REST Assured；MockMvc / WebTestClient 同理）
given().contentType(ContentType.JSON)
    .body(Map.of("productId", 1, "qty", 2))
.when().post("/api/orders")
.then().statusCode(200)
    .body("data.orderId", notNullValue())
    .body("data.totalAmount", equalTo(new BigDecimal("199.00")));
```

**但 curl 的结果不是测试**——探索过的行为，激活后落成本技能的有断言用例（开发期只写纯单测）。

## 与 java-unit-test 的边界（依赖轴）

| 维度 | java-unit-test | 本技能 |
|---|---|---|
| 依赖 | 内存（mock），零基础设施 | 测试自管（Testcontainers 拉起 + 重置） |
| 激活 | 全周期默认 | 明示或确认后 |
| 速度 | 毫秒 | 秒（切片）/ 十秒+（容器） |
| Mock 方式 | `@Mock`（Mockito 原生） | `@MockitoBean`（Spring Context 内替换 Bean） |
| 典型场景 | Service 决策表分支矩阵；本地起服务打真 HTTP | jsonb 查询 / 迁移可重放 / E2E / WireMock 隔离外部调用 |

> **`@MockitoBean` 分界线**：纯单测用 `@Mock`（不起容器）→ java-unit-test；切片 / 集成测试中替换 Bean 用 `@MockitoBean`（在 Spring Context 内）→ 本技能。`@MockitoBean` 用于纯单测会启动整个 Context，是 java-unit-test 的 S 级反模式。
