# 盲评员 B — java-integration-test 达尔文盲评

- **盲评员**：B
- **评估日期**：2026-08-14
- **技能版本**：1.0.0（`SKILL.md` frontmatter line 17）
- **盲态声明**：本评分仅基于 `rubric.md` + `test-prompts.md` + 技能内容（SKILL.md + 8 references）。未读取 `eval/java-integration-test/` 下的 `report.md`、任何 `blind-*.md`、`fixtures/`，独立判断。

---

## 逐 prompt 打分

### Prompt T1（写 Controller 测试·竞争场景·选层次 + 切片优先）
- D1: 11  D2: 11  D3: 12  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 关键依据:
  1. 路由表（`SKILL.md` line 70）明确 "单层 Controller + 参数校验 / 异常 → `@WebMvcTest` + MockMvc → `03`"，直指切片而非全量。
  2. `references/03` lines 22-49 给出完整 `@WebMvcTest(OrderController.class)` + `@MockBean OrderService` + MockMvc `andExpect(status().isBadRequest())` / `jsonPath` 代码，可直接照搬。
  3. `references/03` lines 51-57 点名隐蔽坑 "`@WebMvcTest` 只加载 `@Controller`，不扫描 `@Service` → `NoSuchBeanDefinitionException`"，A 级规则表（`SKILL.md` line 103）同步约束。
- 扣分主因：无功能性缺陷。D1/D2 略扣因 description 较长密集（见汇总"最严重问题 2"），路由本身精准。

### Prompt T2（测 Service 到数据库全链路·竞争场景·真实依赖）
- D1: 11  D2: 11  D3: 12  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 关键依据:
  1. 路由表（`SKILL.md` line 72）"Service + Repository 跨层协作 → `@SpringBootTest(MOCK)` + `@Transactional` → `02`+`06`"；line 77 "真实数据库 / Redis / Kafka → Testcontainers → `04`"。
  2. `references/04` lines 61-76 给出 `@ServiceConnection` + `@Container static` 完整代码，line 61 + `SKILL.md` line 130 声明版本门槛（Spring Boot 3.1+），3.0 及以下走 `@DynamicPropertySource`（lines 82-92）。
  3. "发消息"外部依赖 → WireMock（`06` §WireMock）/ Kafka → `KafkaContainer`（`04` 速查表 line 151）；强约束 5（`SKILL.md` line 114）"外部依赖必须 stub"。
- 扣分主因：D4 略扣——跨"消息"介质（Kafka vs HTTP 通知）的选择需 agent 自行判断，技能给了两套方案但未给一张"发消息属于哪种"的判别表（极轻微）。

### Prompt T3（curl 反模式拦截·独占陷阱·核心价值）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 95/100
- 关键依据:
  1. description（`SKILL.md` line 13）"用 curl 测接口"列为次级触发信号；第 0 步 line 61 "如果正在用 curl …立即拦截"；铁律 1（line 27）+ S 级表（line 85）双重拦截。
  2. `references/01` lines 48-57 用 FIRST 原则逐条拆解 curl 缺陷（Self-validating 无断言 / Repeatable 依赖手动 / 不进版本控制），lines 60-80 "返回 200 但业务逻辑错"翻车场景附 ✓ REST Assured 逐字段断言代码。
  3. `references/05` lines 256-265 curl vs REST Assured 对照表（状态码断言 / 可重复 / CI 集成 / 版本控制四列）+ given/when/then 三段式（lines 56-71）可直接落地。
- 扣分主因：D6——curl 反模式在 SKILL.md 内出现 3 处（铁律 1 line 27、S 级表 line 85、核心强约束 1 line 110），表述高度重叠，违反"定义一次余处用指针"原则（见汇总"最严重问题 1"）。

### Prompt T4（手动启动应用再测·独占陷阱·curl 前置动作）
- D1: 11  D2: 11  D3: 11  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 92/100
- 关键依据:
  1. S 级表第 2 行（`SKILL.md` line 86）"手动启动应用再 curl → `@SpringBootTest(webEnvironment=RANDOM_PORT)` 进程内启动 + 自动断言"——点名启动方式反模式并给替代。
  2. `references/08` 反模式表 line 12 "手动 `mvn spring-boot:run` 再测 → `@SpringBootTest` 进程内启动"再次独立列出。
  3. `references/02` webEnvironment 决策表（lines 22-29）RANDOM_PORT 适用"完整 HTTP API 测试"；`references/05` lines 29-38 给 `@LocalServerPort` + REST Assured 真实 HTTP 代码（含序列化 / 过滤器）。
- 扣分主因：D5 略扣——"手动启动"这一变体的代价（不可重复 / 依赖手动 / 不可版本控制）未独立成段，需 agent 从 curl 通用论述（`01`）推断；S 级表 row 2 与 08 表只给了 ✓ 修复，未单独点明启动方式变体的危害清单。D3 同步略扣（缺"启动方式反模式危害"的独立小节）。

### Prompt T5（边界让位·多技能竞争·拆解职责）
- D1: 11  D2: 11  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 12  D9: 4
- 小计: 93/100
- 关键依据:
  1. `references/01` 决策树（lines 19-44）首分支 "单个类的方法逻辑 → 单元测试（@Mock + @InjectMocks）→ java-unit-test"，明确让位单测。
  2. `SKILL.md` line 133 "不适用：前端 E2E（Selenium / Playwright / Cypress）、性能测试"；`references/01` line 15 同步声明。
  3. `references/01` lines 116-125 边界表 + line 125 "@MockBean 分界线：纯单测用 @Mock → java-unit-test；切片 / 集成用 @MockBean → 本技能"——②集成测试归本技能、③前端 E2E 明确不适用，无越界包办。
- 扣分主因：D6——边界信息在 SKILL.md（lines 132-133）与 `references/01`（lines 116-125 决策树 + 边界表 + line 15）多处重述，`01` 的决策树 ASCII（lines 19-44）与 SKILL.md 路由表（lines 67-78）映射高度重叠。

### Prompt T6（@Transactional 在 RANDOM_PORT 失效·独占陷阱·头号坑）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 11  D9: 4
- 小计: 97/100
- 关键依据:
  1. `references/06` lines 28-30 点明根因："HTTP 请求走真实 Servlet 容器线程，与测试线程不在同一事务。测试线程的 @Transactional 只回滚测试线程的事务，HTTP 请求线程的提交不受影响"——直击根因（独立线程），非泛泛"检查事务配置"。
  2. `references/06` line 46 点名典型症状："测试'绿'但数据库有残留数据，下一个测试依赖干净状态时突然失败——'上次跑过了这次报错'"。
  3. `references/06` lines 48-75 给两套替代：`@Sql(executionPhase=AFTER_TEST_METHOD)` 清理 + Testcontainers `@AfterEach` TRUNCATE，均附完整代码。
- 扣分主因：D6 略扣——该规则在 SKILL.md 出现 2 处（核心强约束 2 line 111 全句 + S 级表 line 88 表行），`02` line 30 又复述一遍原理（虽末尾"详见 06"用了指针，仍部分重复）。功能性无缺陷。

### Prompt T7（H2 方言陷阱·独占陷阱）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 95/100
- 关键依据:
  1. `references/04` lines 6-16 方言差异表（jsonb / ARRAY / SERIAL / 大小写 / 窗口函数 / 存储过程六维），line 16 "H2 与 PostgreSQL 的方言差异是'测试绿生产炸'的头号来源"。
  2. `references/03` lines 117-137 隐蔽坑："@DataJpaTest 默认 @AutoConfigureTestDatabase → 用 H2 替换"，✓ 解法 `@AutoConfigureTestDatabase(replace = NONE)` + `@ServiceConnection` + `PostgreSQLContainer`。
  3. `references/04` lines 166-180 追加 DDL 差异（CREATE TYPE AS ENUM / CONCURRENTLY / CREATE EXTENSION），强化"测试绿生产炸"覆盖。
- 扣分主因：D6——H2 规则在 SKILL.md 出现 3 处（核心强约束 4 line 113、S 级表 line 89、A 级规则表 line 102），三处表述重叠，是本技能 SKILL.md 内最显著的重复。

### Prompt T8（@MockBean vs @Mock 分界·独占陷阱）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 12  D9: 4
- 小计: 96/100
- 关键依据:
  1. `references/02` lines 110-118 @Mock vs @MockBean 对比表（来源 / 范围 / 作用 / 容器 / 开销五维）+ line 136 "@MockBean 会重建 Context → 额外十秒"——根因（Context 启动 / 重建）正确。
  2. `references/02` lines 120-134 给两套代码：纯单测 `@ExtendWith(MockitoExtension.class)` + `@Mock` + `@InjectMocks`；集成测试 `@MockBean`。
  3. `references/01` line 125 + `SKILL.md` line 132 声明分界 + 反模式："@MockBean 用于纯单测会启动整个 Context，是 java-unit-test 的 S 级反模式"——明确指向 java-unit-test 边界。
- 扣分主因：D5 略扣——"@MockBean 用于纯单测"作为 java-unit-test 的 S 级反模式仅在 `01` line 125 提一句，未进 SKILL.md 的 S 级反模式表（该表无此行），审查既有代码时发现概率略低。

### Prompt T9（WireMock vs @MockBean 外部依赖·独占陷阱）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 关键依据:
  1. `references/06` lines 155-163 对比表 + line 163 原文："@MockBean 替换 PaymentClient Bean → 跳过 HTTP 序列化。WireMock 起 Mock Server → PaymentClient 真发 HTTP…能测到 JSON 序列化、连接超时、重试逻辑"——直击 @MockBean 的盲区。
  2. `references/06` lines 238-245 选择判据表："内部 Service 逻辑 → @MockBean；HTTP 序列化 / 超时 / 重试 → WireMock"。
  3. `references/06` lines 194-223 WireMock 完整示例：`stubFor(post(...))` + `withFixedDelay(5000)` 测超时重试 + `dynamicPort()` 避并行冲突，可直接照搬。
- 扣分主因：无明显缺陷。D1/D7/D8 各 -1 属常规——触发信号存在但 description 密集；导航靠通读 `06`。

### Prompt T10（执行效率·独占陷阱·新补维度）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 11  D6: 11  D7: 12  D8: 11  D9: 4
- 小计: 96/100
- 关键依据:
  1. `references/08` 反模式表（lines 7-14）六行全覆盖：全文读输出→`-q`+grep；反复全量→`-Dtest`；每次 clean→只 `mvn test`；失败瞎改→读 surefire；无超时→`@Timeout`。
  2. `references/08` §3（lines 47-57）迭代策略：`mvn test -q` → `mvn test -Dtest=OrderServiceTest` → `mvn test -Dtest=...#should_create_order` → 失败读 `target/surefire-reports/*.txt`，命令可直接复制。
  3. `references/08` §4（lines 59-78）`@Timeout(10)` + `junit-platform.properties` 全局兜底，防死锁挂套件。
- 扣分主因：D5 略扣——`@Timeout` 仅作"兜底"提及，未点名"测试无超时 → 死锁静默挂住整个套件且不报错"这一隐性症状的完整阐述（反模式表 line 14 一句话带过）。功能性命令齐全。

---

## 汇总表

| Prompt | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | 小计/100 |
|--------|----|----|----|----|----|----|----|----|----|----------|
| T1 | 11 | 11 | 12 | 11 | 11 | 11 | 11 | 11 | 4 | 93 |
| T2 | 11 | 11 | 12 | 11 | 11 | 11 | 11 | 11 | 4 | 93 |
| T3 | 12 | 12 | 12 | 11 | 12 | 10 | 11 | 11 | 4 | 95 |
| T4 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 4 | 92 |
| T5 | 11 | 11 | 12 | 11 | 11 | 10 | 11 | 12 | 4 | 93 |
| T6 | 11 | 12 | 12 | 12 | 12 | 11 | 12 | 11 | 4 | 97 |
| T7 | 11 | 12 | 12 | 12 | 12 | 10 | 11 | 11 | 4 | 95 |
| T8 | 11 | 12 | 12 | 12 | 11 | 11 | 11 | 12 | 4 | 96 |
| T9 | 11 | 12 | 12 | 12 | 12 | 11 | 11 | 11 | 4 | 96 |
| T10 | 11 | 12 | 12 | 12 | 11 | 11 | 12 | 11 | 4 | 96 |

---

## 总分

10 个 prompt 小计算术平均 = (93+93+95+92+93+97+95+96+96+96) / 10 = 946 / 10 = **94.6 / 100**

---

## 最严重的 3 个问题（按对总分扣分影响排序）

### 1. D6 信息密度：SKILL.md 内同规则多处重复（影响 T3/T5/T6/T7，累计约 -5）

AGENTS.md 质量标准明令"跨文件重复 → 定义一次，余处用指针"，但 SKILL.md 自身就有规则在不同 section 反复出现：
- **curl 反模式 3 处**：铁律 1（line 27）、S 级表（line 85）、核心强约束 1（line 110）——三处都在 SKILL.md，表述高度重叠。
- **H2 方言规则 3 处**：核心强约束 4（line 113）、S 级表（line 89）、A 级规则表（line 102）——三处同义。
- **@Transactional 失效 2 处**：核心强约束 2（line 111 全句）、S 级表（line 88 表行）。

铁律 / 强约束 / S 级表 / A 级规则表 四个 section 的定位（生成约束 / 必守 / 致命审查 / 约定）有差异，但同一条规则在 SKILL.md 内出现 2-3 次仍属冗余。建议：致命项只在 S 级表留 ✓/✗ 对，铁律/强约束用一句话 + 指针。

### 2. D1 触发精度：description 过长密集，信噪比受影响（影响全部 10 个 prompt，累计约 -10 但单点轻微）

description（`SKILL.md` lines 5-16）是一个约 200 字的密集段落，把主场景、次级触发信号、边界全塞进 `>-` 折叠块。次级触发信号覆盖精准（curl / 手动启动 / H2 / 数据污染 / 外部 API 真调 / 反复全量 都有对应），但段落越长，agent 实际匹配关键词时的信噪比越低。每个 prompt D1 稳定 -1（11/12）。建议：次级触发信号拆成列表项，提升可解析度。

### 3. D5/D3 局部：个别独占陷阱的危害症状未独立成段（影响 T4/T8/T10，各 -1）

- **T4 手动启动反模式**：S 级表 row 2（line 86）+ 08 表（line 12）只给 ✓ 修复，"不可重复 / 依赖手动 / 不可版本控制"的危害清单未独立列出，需 agent 从 curl 通用论述推断，T4 与 T3 的区分度略弱。
- **T8 @MockBean 纯单测反模式**："`@MockBean` 用于纯单测是 java-unit-test 的 S 级反模式"仅在 `references/01` line 125 提一句，未进 SKILL.md 的 S 级反模式表（该表无此行），审查既有代码时命中概率降低。
- **T10 无超时挂套件**：`@Timeout` 仅作"兜底"提及，"死锁静默挂住整个套件且不报错"的隐性症状（反模式表 line 14）一句话带过。

---

## 结论

**通过盲评（94.6 ≥ 80 阈值）。**

10 个 prompt（含 6 个独占陷阱场景）全部命中正确根因与可执行方案：curl 反模式、@Transactional RANDOM_PORT 失效、H2 方言、@MockBean 分界、WireMock 选择、执行效率均给出正确代码与正确判据，无功能性缺陷、无越界包办。唯一系统性扣分来自 SKILL.md 内规则重复（D6）与 description 密度（D1），均为表达层优化，不影响 agent 产出合格结果。
