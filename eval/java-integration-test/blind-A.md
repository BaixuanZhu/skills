# 盲评员 A · java-integration-test 达尔文盲评

- **盲评员**：A
- **评估日期**：2026-08-14
- **技能版本**：1.0.0（`SKILL.md` frontmatter `version: "1.0.0"`，`last_verified: 2026-08-13`）
- **规模**：SKILL.md 133 行 + 8 references（01:125 / 02:223 / 03:198 / 04:261 / 05:301 / 06:374 / 07:373 / 08:82）= 2070 行
- **盲态声明**：本次评分仅基于 SKILL.md + 8 references + rubric.md + test-prompts.md。未读 `eval/java-integration-test/` 下的 `report.md`、任何 `blind-*.md`、`fixtures/`，亦不知作者身份、不知是否存在过其他评分。

---

## 逐 prompt 打分

### Prompt T1（写 Controller 测试·竞争场景·选层次 + 切片优先）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 94/100
- 关键依据：
  1. `SKILL.md` 测试层次路由表（L67-78）"单层 Controller + 参数校验 / 异常 → `@WebMvcTest` + MockMvc → `03`"；description（L13）含"@SpringBootTest 全量上下文测单层 Controller"触发信号，竞争场景下能正确选切片。
  2. `references/03` L22-48 完整 `@WebMvcTest(OrderController.class)` + `@MockBean OrderService` + MockMvc `andExpect(status().isBadRequest())` / `jsonPath(...)` 代码，注解组合可直接照抄。
  3. `references/03` L51-72「隐蔽坑：@WebMvcTest 不加载 Service」+ `SKILL.md` A 级规则表（L103）点名 `@WebMvcTest` 不 mock Service 导致 `NoSuchBeanDefinitionException`，给出 `@MockBean` / `@Import` 两解法；S 级表（L87）反向拦截"全量 `@SpringBootTest` 测单层 Controller"。
- 扣分主因：无明显功能性缺陷。D5 保留 1 分余地——`@WebMvcTest` 与 Spring Security 的交互（L74-92）虽覆盖，但 Sa-Token 切片鉴权失真只一句带过（L92），对"参数校验"主场景非必需，故不重扣。

### Prompt T2（测 Service 全链路·竞争场景·真实依赖）
- D1: 11  D2: 11  D3: 11  D4: 11  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 93/100
- 关键依据：
  1. 路由表（`SKILL.md` L72）"Service + Repository 跨层协作 → `@SpringBootTest(MOCK)` + `@Transactional` → `02`+`06`"，L77"真实数据库 → Testcontainers → `04`"；`references/02` L6-18 给全量 Context 真实 Bean 注入示例。
  2. `references/04` L61-78 `@ServiceConnection`（标注"Spring Boot 3.1+"）+ L80-94 `@DynamicPropertySource`（3.0 及以下），版本门槛在三处点明（含 `SKILL.md` L130），`@AutoConfigureTestDatabase(replace=NONE)` 在 L101/123 强调。
  3. 强约束 4（`SKILL.md` L113）+ `references/04` L5-16 方言差异表拦截"H2 替代 PostgreSQL"；隔离策略 `references/06` L11-25 MOCK 模式 `@Transactional` 回滚有效。
- 扣分主因：D3 留 1 分——"发消息"跨外部依赖的归口（Kafka 走 Testcontainers L151 / 外部 HTTP 走 WireMock）需 agent 自行二选一推断，技能未在路由层显式区分"发消息"是 MQ 还是外部 API。

### Prompt T3（curl 反模式·独占陷阱·核心价值）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. description（L12-14）"消灭 curl 仿真测试"、"`返回 200 就是通过了`"为显式次级触发信号；`SKILL.md` L61 第 0 步"curl 检测 → 立即拦截"——触发与拦截动作明确，不会附和"接口是好的"。
  2. 铁律 1（L27）+ 强约束 1（L110）+ S 级表（L84-85）+ `references/01` L48-57 FIRST 原则表，curl 四宗罪（无断言 Self-validating / 不可重复 Repeatable / 不进版本控制 Thorough / 无隔离）逐条点名，并给"返回 200 但业务逻辑错"翻车场景（`references/01` L60-81）。
  3. `references/01` L70-81 + `references/05` L256-265 给出 REST Assured 替代（statusCode + body + jsonPath 逐字段断言），可执行。
- 扣分主因：D6 唯一失分点——curl 论证在 SKILL.md 内三处近乎复读：核心立场（L23）≈ 铁律 1（L27）≈ 强约束 1（L110），且 `references/01`、`references/05` 对照表、`references/07` L70-89 冒烟 curl 反模式再述。核心立场段（L23）属 AGENTS.md 标准的"原理前言"，论证可删留步骤。

### Prompt T4（手动启动再测·独占陷阱·curl 前置动作）
- D1: 11  D2: 11  D3: 11  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 91/100
- 关键依据：
  1. S 级表（`SKILL.md` L85-86）独立一行"手动启动应用再 curl → `@SpringBootTest(webEnvironment=RANDOM_PORT)` 进程内启动"，与 L84-85 的纯 curl 断言反模式分行，未混淆；`references/08` L12 反模式表再列"手动 `mvn spring-boot:run` 再测 → `@SpringBootTest` 进程内启动"。
  2. `references/02` L43-53 给 `@SpringBootTest(RANDOM_PORT)` + `@LocalServerPort` + `@Sql(AFTER_TEST_METHOD)` 可执行代码；`references/05` L29-38 REST Assured + `RestAssured.port = port` 落地。
  3. description（L13）"手动启动应用再调接口"为显式触发信号。
- 扣分主因：本 prompt 小计最低。D4/D5 各留 1 分——技能把"手动启动为何错"的代价（不可重复 / CI 中不存在）折叠进通用 curl 不可重复论证（`references/01` L52-57 R 列），未单独论证进程内启动相对手动 `spring-boot:run` 的优势（生命周期可控 / 测试间 teardown / 端口随机化），启动方式反模式的"why"偏薄，主要靠两张表的两行撑住。D6 因 S 级表与 `references/08` 反模式表对该条重复各述一次扣 2 分。

### Prompt T5（边界让位·多技能竞争·拆解职责）
- D1: 11  D2: 11  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 12  D9: 4
- 该 prompt 小计: 93/100
- 关键依据：
  1. `SKILL.md` L132"与 java-unit-test 的边界"明确：纯单元测试（`@Mock`+`@InjectMocks`，毫秒级，不起容器）→ java-unit-test；`@MockBean` 分界线（纯单测 `@Mock` → java-unit-test；切片/集成 `@MockBean` → 本技能）。
  2. `SKILL.md` L133"不适用：前端 E2E（Selenium / Playwright / Cypress）、性能测试、安全测试"——前端点击下单被正确让位；`references/01` L7-13 测试层次模型"对应技能"列 + L19-44 决策树"单类方法逻辑 → java-unit-test"。
  3. `references/01` L115-126 边界表 + `@MockBean` 分界线（L125"@MockBean 用于纯单测是 java-unit-test 的 S 级反模式"），三处一致防止越界包办 `@Mock`+`@InjectMocks` 设计。
- 扣分主因：D6——边界声明散落四处（`SKILL.md` L69 路由表 / L132-133 版本与范围 / `references/01` L9 层次模型 / L115-126 边界表），`@MockBean` 分界线在 L132 与 `references/01` L125 近乎逐字重复。功能上三路拆解（①让位单测 ②本技能 ③前端不适用）完全正确，D3/D8 满分/近满。

### Prompt T6（@Transactional 失效·独占陷阱·头号坑）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. 强约束 2（`SKILL.md` L111）直击根因："`RANDOM_PORT` 下 HTTP 请求走独立线程（Servlet 容器线程池），`@Transactional` 回滚不生效"——非"检查事务传播配置"误诊；`references/06` L28-46 头号陷阱节展开"测试线程事务 vs Servlet 容器线程非同一事务"。
  2. `references/06` L46 点名典型症状"测试绿但数据库有残留数据，下一个测试依赖干净状态时突然失败"，与 prompt 描述吻合；L48-75 给两套替代（`@Sql(AFTER_TEST_METHOD)` / Testcontainers `@AfterEach` TRUNCATE）。
  3. `references/06` L77-87 完整失效场景表覆盖 MOCK 有效 / RANDOM_PORT 失效 / `@Async` / 多线程 / `@TransactionalEventListener(AFTER_COMMIT)`，`references/02` L21-30 webEnvironment 决策表"回滚"列交叉印证。
- 扣分主因：仅 D6——`@Transactional` 失效的完整解释在强约束 2（L111）与 `references/06` L28-46 双处各述一遍较完整版本，S 级表 L88 再一行摘要，三层叠加略有冗余。根因、症状、替代方案均无缺陷，D3/D4/D5 满分。

### Prompt T7（H2 方言陷阱·独占陷阱）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 94/100
- 关键依据：
  1. `references/04` L5-16"为什么不用 H2"方言差异表（`jsonb` / `ARRAY` / `SERIAL` / 大小写 / 窗口函数 / 存储过程）+ L166-180 Flyway DDL 差异表（`CREATE TYPE AS ENUM` / `CONCURRENTLY` / `CREATE EXTENSION`），根因"方言差异"完整枚举，未建议"改 SQL 让 H2 兼容"治标方案。
  2. 强约束 4（`SKILL.md` L113）+ S 级表（L89）+ `references/03` L117-137 隐蔽坑三处点明"测试绿生产炸"头号来源；解法 `@AutoConfigureTestDatabase(replace=NONE)` + `@ServiceConnection` + Testcontainers 代码（`references/04` L99-121）。
  3. description（L14）"H2 测试 + PostgreSQL 生产"为显式触发信号。
- 扣分主因：D6——`@DataJpaTest` + Testcontainers + `@AutoConfigureTestDatabase(replace=NONE)` + `@ServiceConnection` 的代码块在 `references/03` L128-137 与 `references/04` L99-120 近乎逐字重复（仅类名 / `postgres:16` vs `16-alpine` 差异），违反 AGENTS.md 标准 #7（代码块与 tools 文件重复）。`references/03` 应指针指向 `04` 而非重贴。

### Prompt T8（@MockBean vs @Mock 分界·独占陷阱）
- D1: 11  D2: 11  D3: 11  D4: 12  D5: 11  D6: 10  D7: 11  D8: 12  D9: 4
- 该 prompt 小计: 93/100
- 关键依据：
  1. `references/02` L110-136 `@MockBean` vs `@Mock` 对照表 + 代码：`@MockBean`"启动 / 重建 Spring Context，开销秒级"vs `@Mock`"不起容器，毫秒"——直接回答"为什么特别慢"；L136"每次 `@MockBean` 配置变化 → Spring 重建 ApplicationContext → 额外十秒"。
  2. 正确替代代码（`references/02` L120-126）：`@ExtendWith(MockitoExtension.class)` + `@Mock` + `@InjectMocks`，并指向 java-unit-test；`references/01` L125"`@MockBean` 用于纯单测是 java-unit-test 的 S 级反模式"。
  3. `SKILL.md` L101 A 级规则表 + L116 强约束 7（Context 缓存友好）从性能角度补强；L132 分界线声明收口。
- 扣分主因：D6——`@MockBean` vs `@Mock` 对照内容在 `references/02` L112-118（机制/性能角度）与 `references/01` L122-125（边界角度）两表重叠，分界线语句在 `SKILL.md` L132 与 `references/01` L125 逐字重复。D3 留 1 分——对"纯单测为何不该起容器"的机制解释（Context 启动开销构成）点到为止，未深挖，但已足够 agent 给出正确替代。

### Prompt T9（WireMock vs @MockBean·独占陷阱）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 94/100
- 关键依据：
  1. `references/06` L155-163"为什么不用 @MockBean 替代外部调用"表：`@MockBean` 替换 Bean → 跳过 HTTP 序列化；WireMock 替换 HTTP 端点 → 测序列化 / 超时 / 重试——直接命中 prompt"用 @MockBean 替换 PaymentClient 可以吗"的根因（序列化 / 超时 / 重试测不到）。
  2. `references/06` L238-245 `@MockBean` vs WireMock 选择表（内部 Service 逻辑 → `@MockBean`；HTTP 序列化 / 超时 / 重试 → WireMock；完整 HTTP 链路 → WireMock）给出明确判据；L176-223 WireMock stub 代码（含 `withFixedDelay` 测超时 / 重试）。
  3. 强约束 5（`SKILL.md` L114）"外部依赖必须 stub，不得真调" + S 级表（L90）"外部 API 真调 → WireMock stub"；description（L13-14）"外部 API 真调"触发信号。
- 扣分主因：D6——外部依赖 stub 在 `SKILL.md`（S 级表 L90 / 强约束 5 L114）与 `references/06`（L155-163 why-not + L238-245 选择表）多处表述，why-not 与选择表内容部分重叠（都讲"内部 Bean vs 外部 HTTP"），可合并。功能层面根因、判据、代码均到位，D3/D4/D5 满分。

### Prompt T10（执行效率·独占陷阱·新补维度）
- D1: 12  D2: 11  D3: 12  D4: 12  D5: 11  D6: 9  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 93/100
- 关键依据：
  1. `references/08` L7-14 反模式表六行全覆盖验证点：全文读输出 → `-q` + `grep`/`tail`；反复全量 → `-Dtest`；每次 `clean test` → 只 `mvn test`；失败瞎改 → `target/surefire-reports/*.txt`；无超时 → `@Timeout`。
  2. `references/08` L16-30 降噪命令（`mvn test -q`、重定向 `> target/test.log 2>&1` + `grep -E "Tests run:|BUILD|ERROR|FAIL"`）、L47-57 迭代策略（首次全量 → `-Dtest=类名` → `-Dtest=类名#方法` → 失败读 surefire 报告）均为可直接照做的具体 flag / 路径。
  3. `references/08` L59-78 `@Timeout` 兜底 + `junit-platform.properties` 全局配置；description（L14）"反复全量 mvn test / 全文读测试输出 / 跑测试太慢"三连触发。
- 扣分主因：D6 全场最低（9）——`SKILL.md` 强约束 8（L117）几乎逐条复述 `references/08` 反模式表（`-q` 降噪 / `-Dtest` / 不 `clean` / surefire 报告 / 不全文回传），SKILL.md 内的强约束本应是一句话规则 + 指针，此处扩写成 mini 反模式表，与 `references/08` 高度重叠。这是"补 08 后留残余重复"的典型痕迹（rubric 铁律点名的核查项）。

---

## 汇总表

| Prompt | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | 小计/100 |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 Controller 切片 | 11 | 11 | 12 | 12 | 11 | 11 | 11 | 11 | 4 | **94** |
| T2 Service 全链路 | 11 | 11 | 11 | 11 | 12 | 11 | 11 | 11 | 4 | **93** |
| T3 curl 反模式 | 12 | 12 | 12 | 11 | 12 | 10 | 11 | 11 | 4 | **95** |
| T4 手动启动 | 11 | 11 | 11 | 11 | 11 | 10 | 11 | 11 | 4 | **91** |
| T5 边界让位 | 11 | 11 | 12 | 11 | 11 | 10 | 11 | 12 | 4 | **93** |
| T6 @Transactional 失效 | 11 | 12 | 12 | 12 | 12 | 10 | 11 | 11 | 4 | **95** |
| T7 H2 方言 | 11 | 11 | 12 | 12 | 12 | 10 | 11 | 11 | 4 | **94** |
| T8 @MockBean vs @Mock | 11 | 11 | 11 | 12 | 11 | 10 | 11 | 12 | 4 | **93** |
| T9 WireMock vs @MockBean | 11 | 11 | 12 | 12 | 12 | 10 | 11 | 11 | 4 | **94** |
| T10 执行效率 | 12 | 11 | 12 | 12 | 11 | 9 | 11 | 11 | 4 | **93** |

---

## 总分

**93.5 / 100**（10 个 prompt 小计算术平均：935 / 10）

维度均分：D1=11.2 · D2=11.2 · D3=11.8 · D4=11.6 · D5=11.5 · D6=10.0 · D7=11.0 · D8=11.2 · D9=4.0

---

## 最严重的 3 个问题（按对总分扣分影响排序）

### 1. D6 信息密度——curl 反模式跨文件 + SKILL.md 内三重复读（影响 T3/T4/T6/T7/T9，最普遍）
- `SKILL.md` 内：核心立场段（L23）≈ 铁律 1（L27）≈ 强约束 1（L110），三处均陈述"curl 不是测试 + 无断言 / 不可重复 / 不可版本控制"，核心立场段（L23）属 AGENTS.md 标准 #1「原理前言」（论证 FIRST 原则为何重要），可删论证留步骤。
- 跨文件：curl 在 SKILL.md（13 次）、`references/01`（17 次）、`references/05` 对照表（3 次）、`references/07` 冒烟反模式（5 次）四处展开。S 级表（L84-85）、`references/01` 深析、`references/05` 对照、`references/07` L70-89 各有侧重但 curl 核心论点（无断言 / 不可重复 / 不进版本控制）反复重述。
- 这是 5 个 prompt 的 D6 集中扣 2 分的主因，也是 rubric 铁律点名的"补丁残余重复"核查项命中点。

### 2. D6 信息密度——代码块与强约束跨文件逐字重复（影响 T7/T10，最具体）
- `@DataJpaTest` + `@AutoConfigureTestDatabase(replace=NONE)` + `@ServiceConnection` + `PostgreSQLContainer` 代码块在 `references/03` L128-137 与 `references/04` L99-120 近乎逐字重复（仅类名 / 镜像 tag 差异），违反 AGENTS.md 标准 #7（代码块与 tools 文件重复）。`references/03` 应指针指向 `04`。
- `SKILL.md` 强约束 8（L117）把 `references/08` L7-14 反模式表（`-q` / `-Dtest` / 不 `clean` / surefire 报告 / 不全文回传）扩写进 SKILL.md，本应一句话规则 + 指针，导致 T10 D6 全场最低（9）。
- `@MockBean` 分界线语句在 `SKILL.md` L132 与 `references/01` L125 逐字重复。

### 3. T4 手动启动反模式的"why"偏薄，启动方式与断言缺失的区分靠两行表撑（影响 T4，最低分 prompt 91）
- S 级表（`SKILL.md` L84-86）虽将"curl 断言反模式"与"手动启动反模式"分成两行（未混淆，符合 rubric 要求），但"手动 `spring-boot:run` 为何错"的代价折叠进通用 curl 不可重复论证（`references/01` L52-57 R 列"依赖手动启动应用 → 换人 / 换机器跑不了；CI 中不存在"），未单独论证进程内 `@SpringBootTest(RANDOM_PORT)` 相对手动启动的优势（测试生命周期可控 / 测试间 teardown / 端口随机化 / 与 Testcontainers 同 JVM 编排）。
- 可执行的替代代码（`references/02` L43-53）到位，故 D4/D11 不重扣，仅各留 1 分；但 T4 成为全场最低分 prompt，根因在此。

---

## 结论

**通过盲评**（总分 93.5 ≥ 阈值 80）。

理由：10 条 prompt 中无任何功能性缺陷——全部 5 个核心陷阱（curl 反模式 / `@Transactional` 失效 / H2 方言 / `@MockBean` 分界 / WireMock）的根因、症状、替代方案均正确且可执行，无错误根因、无错误代码、无越界包办（T5 三路拆解完全正确，前端 E2E 明确让位）。全部失分集中在 D6 信息密度（10 个 prompt D6 均 9-11），属"补 08 与多轮增删后留有跨文件 / 跨段重复"的可修复冗余，不影响 agent 产出合格结果的能力。
