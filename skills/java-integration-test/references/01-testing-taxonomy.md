# 01 · 测试分级与 curl 反模式

> 根文件，决定"现在写不写集成测试、写哪级"前必读。所有工具链 reference（02-05）建立在本文件的分级模型上。示例注解 `@MockitoBean` 需 Boot 3.4+（≤3.3 写作 `@MockBean`，4.0 已移除旧注解——版本口径见 `02`）。

## 阶段闸门：现在写不写集成测试？

集成测试是十秒级/条的重资产，写在还在变动的行为上 = 需求每变一次就多付一次重写成本（"测试久过开发"的根源）。因此**先判阶段，再选级**：

| 阶段 | 判定 | 测试动作 |
|---|---|---|
| **开发期** | 需求未稳定 / 功能还在改 | 只写 T1 纯单测（→ java-unit-test）；验证靠本地手动跑应用 + curl 探索（调试合法） |
| **稳定期** | 触发点任一：需求冻结 / 特性过验收（DoD）/ 进入发布准备 | 补齐该特性集成层：T3 锚（迁移可跑 + 启动冒烟 + 核心 SQL 1~3 条）+ T2 协议层 + 特性级 T3 用例 1~3 条 |

> 阶段判定一次性问用户，不猜；拿不准默认开发期（从轻）。开发期不删存量集成测试（照跑照修），只是不新增。运行调度（内环 / 提交 / CI 分层跑）见 `08` §3。

## 测试三级分级模型

| 级 | 测什么 | 起容器 | 速度 | 本技能覆盖 | 对应技能 |
|---|---|---|---|---|---|
| **T1 单元测试** | 单类逻辑，依赖全 Mock（含 Service 业务分支矩阵） | 否（无 Spring） | 毫秒 | ✗ | java-unit-test |
| **T2 Spring 切片测试** | 单层协议行为：参数校验 / 路由 / 异常处理 / JSON / HTTP 客户端逻辑 / 权限逻辑 | 否 | 秒 | ✓ `03` | 本技能 |
| **T3 真实依赖测试** | 离开真实依赖就不成立的行为：SQL / 方言 / 迁移 / 事务传播 / 缓存语义 / 消息协议；冒烟；E2E | 是 | 十秒+ | ✓ `02`+`04`+`07` | 本技能 |

> 前端 E2E（Selenium / Playwright）和性能测试不在本技能范围。

**T3 准入判据**（机械化）：**这条断言离开真实 DB / Redis / Kafka 就不成立吗？**——SQL 实际语句与方言特性、Flyway / Liquibase 迁移脚本、事务传播实际效果、缓存过期 / 序列化语义、消息协议 → T3；业务规则、多条件分支矩阵、DTO 映射、参数校验、权限逻辑 → T1 / T2。

**T2 封顶清单**（最多到切片，永远不进 T3）：Controller 参数校验 / 路由 / 异常处理、JSON 序列化、HTTP 客户端调用逻辑（`@RestClientTest`）、权限控制逻辑。

**数量结构**（防"测试久过开发"）：T1 数十~数百（主力）；T2 十~数十（每层关键行为）；T3 每特性 1~3 条锚定真实行为；E2E 全套件 3~10 条（见 `07`）。

## 决策树：选哪一级？

```
先过阶段闸门：当前是开发期（需求未稳定）吗？
├─ 是 → 只写 T1 纯单测（@Mock + @InjectMocks）→ java-unit-test
│        探索验证用本地跑应用 + curl（调试合法），不写 T2/T3
└─ 否（稳定期）→ 你要测什么？
   ├─ 单个类的方法逻辑（Service / Util / 计算，含分支矩阵）
   │  → 仍是 T1 单元测试 → java-unit-test
   ├─ 断言离开真实依赖就不成立？（SQL / 迁移 / 事务传播 / 缓存语义 / 消息协议）
   │  ├─ Repository SQL / 查询 / 分页 → @DataJpaTest + Testcontainers → 03 + 04
   │  ├─ 跨层真实协作 / 事务传播 → @SpringBootTest(MOCK) + Testcontainers → 02 + 04 + 06
   │  ├─ "服务能不能正常启动" → Actuator health 冒烟 → 07
   │  └─ 多接口串联业务流程 → API 级 E2E → 05 + 07
   └─ 其余单层行为
      ├─ Controller 参数校验 / 路由 / 异常处理 / 权限 → @WebMvcTest → 03
      ├─ JSON 序列化 / 反序列化 → @JsonTest → 03
      └─ HTTP 客户端调用逻辑 → @RestClientTest（真 HTTP 隔离 WireMock）→ 03 + 06
```

## curl 反模式（核心护栏）

### 为什么 curl 不是测试

测试的 FIRST 原则中，curl 至少违反三条：

| 原则 | curl 违反方式 | 后果 |
|---|---|---|
| **S**elf-validating | curl 输出靠肉眼判断"看起来对"——无断言 | 200 + 错误 JSON 体 = "通过"；字段缺失无人发现 |
| **R**epeatable | 依赖手动启动应用 + 手动执行 | 换人 / 换机器跑不了；CI 中不存在 |
| **T**horough | curl one-liner 随手写、随手丢 | 不进版本控制；测试覆盖不可追溯 |

### curl 仿真测试的典型翻车场景

**场景 1：返回 200 但业务逻辑错**

```bash
# ✗ curl 测试：看到 200 就觉得没问题
curl -X POST http://localhost:8080/api/orders -d '{"productId":1,"qty":2}'
# 返回 {"code":200,"msg":"success"} → "测试通过"
# 实际：订单金额算错、库存没扣、关联地址没存——全被 200 掩盖
```

```java
// ✓ REST Assured 测试：逐字段断言
given()
    .contentType(ContentType.JSON)
    .body(Map.of("productId", 1, "qty", 2))
.when()
    .post("/api/orders")
.then()
    .statusCode(200)
    .body("data.orderId", notNullValue())
    .body("data.totalAmount", equalTo(new BigDecimal("199.00")))
    .body("data.status", equalTo("CREATED"));
```

**场景 2：curl 测试不可重复**

```bash
# ✗ 第一次跑：创建用户成功
curl -X POST http://localhost:8080/api/users -d '{"name":"test"}'
# 第二次跑：用户名冲突 → 409 → "测试失败"
# 但代码没变——测试结果取决于数据库残留状态
```

```java
// ✓ @Sql 清理 + 每次干净状态
@Test
@Sql(scripts = "/sql/cleanup-users.sql", executionPhase = BEFORE_TEST_METHOD)
void should_create_user_when_name_available() {
    // ...
}
```

**场景 3：curl 不在 CI 中存在**

curl one-liner 存在终端历史里，不在代码仓库里。CI 跑不了 → 回归保护为零。

## curl 的合理用途

curl 本身没有错——它是**调试工具**和**探索工具**。以下场景用 curl 合理：

- **开发期探索性验证**（合法主场）：需求未稳定时，本地跑应用 + curl 探索比写十秒级测试经济——这正是阶段闸门把集成测试推迟到稳定期的配套用法
- 排查问题时查看实际响应内容
- 文档中展示 API 调用示例

**但 curl 的结果不是测试**——稳定期触发点（需求冻结 / 特性验收 / 发布准备）到达后，必须把探索过的行为落成有断言的测试代码（分级见上文决策树）。

## 与 java-unit-test 的边界

| 维度 | java-unit-test | 本技能 |
|---|---|---|
| 阶段 | 全周期（开发期唯一层） | 稳定期起 |
| 被测范围 | 单类方法逻辑（含 Service 分支矩阵） | 单层协议行为（T2）/ 真实依赖行为（T3） |
| 容器 | 不起（`@Mock`+`@InjectMocks`，无 Spring） | T2 不起；T3 起 |
| 速度 | 毫秒 | 秒（T2）/ 十秒+（T3） |
| Mock 方式 | `@Mock`（Mockito 原生） | `@MockitoBean`（Spring Context 内替换 Bean） |
| 典型场景 | `divide(a,b)` 四维度测试；Service 决策表分支矩阵 | Controller 参数校验（T2）；jsonb 查询 / 迁移（T3） |

> **`@MockitoBean` 分界线**：纯单测用 `@Mock`（不起容器）→ java-unit-test；切片 / 集成测试中替换 Bean 用 `@MockitoBean`（在 Spring Context 内）→ 本技能。`@MockitoBean` 用于纯单测会启动整个 Context，是 java-unit-test 的 S 级反模式。
