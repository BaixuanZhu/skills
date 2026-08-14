# 01 · 测试层次与 curl 反模式

> 根文件，选择测试层次前必读。所有工具链 reference（02-05）建立在本文件的层次模型上。

## 测试层次模型

| 层次 | 测什么 | 起容器？ | 速度 | 本技能覆盖 | 对应技能 |
|---|---|---|---|---|---|
| **单元测试** | 单类逻辑，依赖全 Mock | 否 | 毫秒 | ✗ | java-unit-test |
| **切片测试** | 单层（Web / JPA / JSON），最小 Context | 部分 | 秒 | ✓ `03` | 本技能 |
| **集成测试** | 跨层协作 + 真实依赖（DB / 缓存） | 是 | 秒~十秒 | ✓ `02`+`04` | 本技能 |
| **冒烟测试** | "服务能启动 + 核心端点活着" | 是 | 十秒 | ✓ `07` | 本技能 |
| **API 级 E2E** | 完整业务流程（多接口串联） | 是 | 十秒+ | ✓ `05`+`07` | 本技能 |

> 前端 E2E（Selenium / Playwright）和性能测试不在本技能范围。

## 决策树：选哪一层？

```
你要测什么？
│
├─ 单个类的方法逻辑（Service / Util / 计算）
│  → 单元测试（@Mock + @InjectMocks）→ java-unit-test
│
├─ 单层行为
│  ├─ Controller 参数校验 / 路由 / 异常处理
│  │  → @WebMvcTest 切片 → references/03
│  ├─ Repository SQL / 查询 / 分页
│  │  → @DataJpaTest + Testcontainers → references/03 + 04
│  └─ JSON 序列化 / 反序列化
│     → @JsonTest → references/03
│
├─ 跨层协作（Controller → Service → Repository → DB）
│  → @SpringBootTest(MOCK) + @Transactional → references/02 + 06
│
├─ 完整 HTTP API（含过滤器 / 拦截器 / 序列化）
│  → @SpringBootTest(RANDOM_PORT) + REST Assured → references/02 + 05
│
├─ "服务能不能正常启动"
│  → @SpringBootTest + Actuator health 冒烟 → references/07
│
└─ 多接口串联的业务流程（注册 → 登录 → 下单 → 查询）
   → @SpringBootTest(RANDOM_PORT) + REST Assured 多步 → references/05 + 07
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

- 开发时快速验证接口能不能通（探索性测试）
- 排查问题时查看实际响应内容
- 文档中展示 API 调用示例

**但 curl 的结果不是测试**——探索完接口后，必须落成有断言的测试代码。

## 与 java-unit-test 的边界

| 维度 | java-unit-test | 本技能 |
|---|---|---|
| 被测范围 | 单类方法逻辑 | 跨层协作 / 真实依赖 / HTTP 断言 |
| 容器 | 不起（`@Mock`+`@InjectMocks`） | 起（`@SpringBootTest` / 切片测试） |
| 速度 | 毫秒 | 秒~十秒 |
| Mock 方式 | `@Mock`（Mockito 原生） | `@MockBean`（Spring Context 内替换 Bean） |
| 典型场景 | `divide(a,b)` 四维度测试 | Controller→Service→Repository 全链路 |

> **`@MockBean` 分界线**：纯单测用 `@Mock`（不起容器）→ java-unit-test；切片 / 集成测试中替换 Bean 用 `@MockBean`（在 Spring Context 内）→ 本技能。`@MockBean` 用于纯单测会启动整个 Context，是 java-unit-test 的 S 级反模式。
