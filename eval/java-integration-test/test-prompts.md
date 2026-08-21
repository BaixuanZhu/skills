# 10 条 test-prompt（java-integration-test 达尔文评估输入）

> 这些 prompt 模拟真实用户场景。盲评 agent 假设自己是"接到这个用户请求的 coding agent，手里只有 java-integration-test 技能"，判断能否产出合格代码/解答。
>
> 设计原则：每个 prompt 针对一条或多条核心强约束 + 隐性陷阱。T1-T5 是竞争场景（验证触发 + 选层次 + 边界让位）；T6-T10 是独占陷阱场景（验证技能的核心价值，尤其是 curl 反模式、@Transactional 失效、执行效率）。

## T1 — 写 Controller 测试（竞争场景·选层次 + 切片优先）

```
帮我给订单接口写测试。POST /api/orders 接收参数并校验，我主要想测
Controller 的参数校验和返回格式是否正确，不关心数据库。
```

**验证点**：
- 选 `@WebMvcTest` 切片（非全量 `@SpringBootTest`）—— 强约束 3「切片测试优先」
- Service 用 `@MockBean`（`@WebMvcTest` 只加载 Web 层）—— A 级规则表
- MockMvc 断言 statusCode + jsonPath —— `02`/`03`
- **边界让位**：若测 Service 到数据库全链路 → `@SpringBootTest` + Testcontainers（`03`+`04`）

## T2 — 测 Service 到数据库全链路（竞争场景·真实依赖）

```
订单服务创建订单会写数据库、扣库存、发消息。我想测 Service 到 Repository
的完整流程，生产环境用 PostgreSQL。
```

**验证点**：
- `@SpringBootTest` 全量上下文 —— `02`
- **Testcontainers 真实 PostgreSQL**（不用 H2；默认选择，不取决于项目是否已引 H2）—— 强约束 4 + `04`
- **探测生产依赖后询问用户确认镜像版本**（候选 + 推荐，不静默写 tag）—— `04` §依赖选择
- `@ServiceConnection`（Spring Boot 3.1+）—— `04`
- 隔离策略（`@Transactional` MOCK 模式 / `@Sql` 清理）—— `06`

## T3 — curl 反模式拦截（独占陷阱·核心价值）

```
我用 curl 调了下 /api/orders，返回 200 和正确的 JSON，看起来没问题。
帮我确认下这个接口是不是好的。
```

**验证点**：
- **拦截 curl**——识别 curl 不是测试（无断言、不可重复、不进版本控制、无隔离）—— 铁律 1 + S 级表
- 引导到 MockMvc / REST Assured / WebTestClient 写可断言测试 —— `05`
- 强调结构化断言：statusCode + body + jsonPath，非"看起来返回正常"

## T4 — 手动启动应用再测（独占陷阱·curl 前置动作）

```
我 mvn spring-boot:run 把服务跑起来，然后用 curl 一个个接口调过去测，
这样测全链路最真实。帮我优化下这个测试流程。
```

**验证点**：
- 识别「手动启动 + curl」是反模式 —— S 级表第 2 行
- 引导 `@SpringBootTest(webEnvironment=RANDOM_PORT)` 进程内启动 —— `02`
- REST Assured / WebTestClient 写断言（含序列化 / 过滤器）—— `05`
- 与 T3 的区别：这条是「启动方式」的反模式，不只是「断言缺失」

## T5 — 边界让位（多技能竞争·拆解职责）

```
帮我写完整的订单功能测试：
1. 订单服务的单元测试
2. Controller 到数据库的集成测试
3. 前端页面点击下单的端到端测试
```

**验证点**（SKILL.md 第 0 步边界判定 + 版本与范围）：
- ①单元测试 → **让位 java-unit-test**（不越界包办 @Mock 纯单测设计）
- ②集成测试 → 本技能（@SpringBootTest + Testcontainers + REST Assured）
- ③前端页面点击 → **前端 E2E（Selenium/Playwright/Cypress），明确声明不适用** —— SKILL.md 第 130 行
- 越界包办单元测试设计或前端 E2E → 扣分

## T6 — @Transactional 在 RANDOM_PORT 失效（独占陷阱·头号坑）

```
我用 @SpringBootTest(webEnvironment=RANDOM_PORT) + @Transactional 测 HTTP 接口，
测试跑完数据库有残留数据，下一个测试报错。为什么 @Transactional 没回滚？
```

**验证点**（强约束 2 + `06` §1）：
- 识别 RANDOM_PORT 下 HTTP 请求走独立 Servlet 线程，`@Transactional` 回滚**失效** —— 这是根因
- 给出替代方案：`@Sql(AFTER_TEST_METHOD)` 清理 / Testcontainers 重置 —— `06`
- 是否说明「测试绿但数据残留，下次跑报错」是典型症状

## T7 — H2 vs PostgreSQL 方言陷阱（独占陷阱）

```
我用 @DataJpaTest 默认用 H2 测，全绿。但部署到生产 PostgreSQL 后，
有一段 SQL 报错了。为什么？
```

**验证点**（`03` 隐蔽坑 + `04` 依赖选择）：
- 识别 H2 方言 ≠ PostgreSQL（`jsonb` / `ARRAY` / 序列 / 函数 / 大小写）—— 强约束 4
- 给出 Testcontainers 真实数据库替代 H2 —— `@AutoConfigureTestDatabase(replace = NONE)` + `@ServiceConnection`
- 是否点明「测试绿生产炸」是 H2 替代的头号来源

## T8 — @MockBean vs @Mock 分界（独占陷阱）

```
我在纯单元测试里用 @MockBean 替换依赖，为什么测试跑得特别慢？
```

**验证点**（`02` §@MockBean vs @Mock + `01` 边界）：
- 识别 `@MockBean` 启动/重建 Spring Context（秒级），纯单测应用 `@Mock`（毫秒级）—— 分界线
- 纯单测 → `@ExtendWith(MockitoExtension.class)` + `@Mock` + `@InjectMocks` → 让位 java-unit-test
- 是否说明「@MockBean 用于纯单测」是 java-unit-test 的 S 级反模式

## T9 — WireMock vs @MockBean 外部依赖（独占陷阱）

```
订单支付要调第三方支付 API。测试时我想 mock 掉这个外部调用，
用 @MockBean 替换 PaymentClient 可以吗？
```

**验证点**（`06` §WireMock）：
- 识别 `@MockBean` 替换 Bean → 跳过 HTTP 序列化/超时/重试，测不到这些
- WireMock stub HTTP → 测 JSON 序列化、连接超时、重试逻辑 —— 这才是「测完整链路」
- 给出选择判据：内部 Bean 依赖用 @MockBean，外部 HTTP API 用 WireMock

## T10 — 执行效率（独占陷阱·新补维度）

```
每次改完代码我都 mvn clean test 全量跑，输出特别多要等很久，有办法快点吗？
```

**验证点**（`08`）：
- 只 `mvn test`（不 clean，增量编译）+ `-Dtest=类名` 单测迭代 —— §3
- `-q` 降噪 + 重定向 grep/tail，不全文读输出 —— §1
- 失败读 `target/surefire-reports/*.txt` 定位，不瞎改重跑 —— §3
- 是否提及 `@Timeout` 兜底防挂住 —— §4

## T11 — 无 H2 项目搭建集成测试（竞争场景·定位回归核心）

```
项目里没引 H2，测试也还没搭。订单服务生产用 PostgreSQL，有积分变动、库存扣减。
帮我写 Service 到数据库的集成测试，把测试基础设施一起搭起来。
```

**验证点**（第 0 步第 4 项 + `04` §依赖选择）：
- **技能不被跳过**：项目没用 H2 ≠ 不需要本技能——需要真实依赖 → **默认** Testcontainers（强约束 4）
- 探测生产依赖（`org.postgresql:postgresql` / `spring.datasource.url`）→ 给候选版本**询问用户**（不静默写镜像 tag）—— `04` §依赖选择
- 落定后：`@SpringBootTest` + Testcontainers + `@ServiceConnection` + 隔离策略全套 —— `02`+`04`+`06`
- Docker 环境 checklist 核对（daemon 可用 / 无 Docker 则显式降级声明）—— `04` §Docker checklist
