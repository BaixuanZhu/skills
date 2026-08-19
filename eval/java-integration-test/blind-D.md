# 盲评 D · java-integration-test（工作区当前版本）

日期：2026-08-19
盲评员：D（独立盲评，无修改历史信息）
被评对象：`skills/java-integration-test/SKILL.md`（146 行）+ `references/01~08`（共 2053 行），工作区合计 2199 行（rubric 记载的 2071 行之后又增长约 128 行，本评按当前状态核查）。

## 汇总

- **10 prompt 平均总分：96.0 / 100**
- 各 prompt：T1 96 · T2 95 · T3 97 · T4 97 · T5 95 · T6 95 · T7 96 · T8 95 · T9 97 · T10 97
- 9 维度均分：D1 11.6 · D2 11.9 · D3 12.0 · D4 11.8 · D5 11.8 · **D6 9.4** · D7 12.0 · D8 11.5 · D9 4.0
- 结论：10 条 prompt 的功能性要求（根因识别、正确代码、边界让位、陷阱点名）全部命中，无一处错误根因或越界包办；失分集中在 **D6 信息密度**（系统性跨/内文件规则复述）与两处示例代码缺陷。

---

## 逐 prompt 评分

### Prompt T1（写订单 Controller 测试——参数校验 + 返回格式，不关心 DB）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 9  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 96/100
- 关键依据:
  1. SKILL.md 路由表 L70「单层 Controller + 参数校验 / 异常 → `@WebMvcTest` + MockMvc → `03`」直接命中；S 级表 L87 明确"全量 `@SpringBootTest` 测单层 Controller"是 S 级反模式——判分锚点（未选切片重扣项）反向排除。
  2. `03` L22-48 完整 `@WebMvcTest(OrderController.class)` + `@MockitoBean OrderService` + MockMvc 断言示例，且场景就是 POST /api/orders qty=0 → 400 + jsonPath——agent 可直接照抄（D4）。
  3. `03` L51-57 点名隐蔽坑：`@WebMvcTest` 只加载 `@Controller`，Service 不注入 → `NoSuchBeanDefinitionException`（D5）；另有 Security 401 坑（L74-92）。
- 扣分主因: D6——"切片优先"规则在 SKILL.md 铁律 2（L28）/路由表（L70）/强约束 3（L112）/自检（L135）、01 决策树（L26-27）、03 §切片 vs 全量（L7-16）、03 §速度对比（L186-196）共 6 处复述；"@WebMvcTest 不 mock Service"在 SKILL.md A 级表 L103 与 03 §隐蔽坑双写。D1 扣 1：宽泛"写测试"场景与 java-unit-test 竞争，靠 description 边界句（L15-16）兜住但非绝对。

### Prompt T2（Service→Repository 全链路，生产 PostgreSQL）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 8  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据:
  1. 04 L93-108 `@ServiceConnection` 完整代码 + 版本门槛双声明（SKILL.md L142"3.1+ 新增…3.0 及以下用 `@DynamicPropertySource`"；04 L112-126 两套写法并列）——锚点"未说明 3.1+ 门槛扣 D4"不成立。
  2. H2 替代被三重拦截：SKILL.md 强约束 4（L113）+ S 级表 L89 + 04 §为什么不用 H2 方言差异表（L7-16）——锚点"默认 H2 重扣"排除；隔离策略 06 L11-26 MOCK + `@Transactional` 回滚示例可执行。
  3. 04 L22-54 依赖坐标 TC 1.x / 2.x 双版本齐全；"发消息"→ KafkaContainer（04 L183 速查表 + L110 声明 `@ServiceConnection` 支持 Kafka）或外部 HTTP → WireMock（SKILL.md 强约束 5，L114）。
- 扣分主因: D6 全场最低——04 文件内部"容器不写 static"规则重复两遍（L76-91 正文 + L274-285 隐蔽坑①，含近同 ✗/✓ 代码）；"测试绿生产炸"短语在 SKILL.md L113 / 03 L119 / 04 L16 / 04 L214 四处复述。D8 扣 1：Kafka 只有速查表条目无 `@ServiceConnection` 示例代码，"发消息"场景需 agent 按 PostgreSQL 例类推。

### Prompt T3（curl 返回 200 求确认——核心价值）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 97/100
- 关键依据:
  1. description 次级信号（L12-14）原文即"用 curl 测接口…'返回 200 就是通过了'"；SKILL.md 第 0 步第 3 条（L61）"curl 检测→立即拦截"——触发即拦截，无附和空间（D1 锚点全中）。
  2. 01 §curl 反模式 FIRST 表（L50-56）点名四缺陷：无断言（"200 + 错误 JSON 体 = 通过"）/ 不可重复（"换人 / 换机器跑不了；CI 中不存在"）/ 不进版本控制 / 依赖手动；L60-81"场景 1：返回 200 但业务逻辑错"与 prompt 逐字对位，含完整 REST Assured 反例（statusCode + body + jsonPath 逐字段断言，D4）。
  3. 01 L105-113"curl 的合理用途"（调试 / 探索可用，结果不是测试）防止一刀切禁 curl——范围克制（D8）。
- 扣分主因: D6——curl 禁令在 SKILL.md 内 5+ 处（L23/L27/L61/L85/L110/L130，分属导语/铁律/探测/反模式表/强约束/自检清单）+ 01 专节 + 05 §curl vs REST Assured 对照表（L257-266 的"可重复/CI/版本控制"三行与 01 FIRST 表同信息）+ 07 §curl 冒烟反模式（L72-77），同一规则全文 9 处。

### Prompt T4（手动 spring-boot:run + curl"最真实"求优化）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 97/100
- 关键依据:
  1. S 级表第 2 行（L86）专列"手动启动应用再 curl → `@SpringBootTest(RANDOM_PORT)` 进程内启动 + 自动断言"——启动方式反模式独立成行，未与 T3 的断言缺失混淆（锚点"混淆扣 D5"排除）；08 反模式表 L13"手动 mvn spring-boot:run 再测"同步。
  2. description L12-13 次级信号"手动启动应用再调接口"原文命中；01 场景 2（L83-99）+ FIRST 表 R 行点名手动启动代价："依赖手动启动应用 + 手动执行""结果取决于数据库残留状态"（D5）。
  3. 05 L31-39 `RestAssured.port = port` 启动模板 + given/when/then 完整（D4）；02 webEnvironment 表 L26 + 06 L30"真实 Servlet 容器线程"可用于反驳"手动启动才最真实"。
- 扣分主因: D6（curl 复述叠加 RANDOM_PORT 概念在 02/05/06 三文件各述一遍）；D8 扣 1 属保守——无越界，仅"部署后连外部服务冒烟"（07 §末）与"进程内启动"的边界未在拦截话术中显式区分。

### Prompt T5（三段式：单测 / 集成 / 前端 E2E——边界让位终极测试）
- D1: 11  D2: 12  D3: 12  D4: 11  D5: 11  D6: 10  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 95/100
- 关键依据:
  1. SKILL.md L146"**不适用**：前端 E2E（Selenium / Playwright / Cypress）、性能测试（JMeter / Gatling）、安全测试" + 01 L15 同声明——③显式拒绝而非引导 Playwright（D8 锚点全中，未越界）。
  2. ①让位：SKILL.md L145 + 01 §与 java-unit-test 的边界表（L116-125）——纯单测归 java-unit-test；02 L154-160 的 `@Mock`+`@InjectMocks` 示例仅 3 行且带"→ java-unit-test"注释，属边界示意而非包办单测设计（锚点"越界包办重扣"排除）。
  3. ②本技能：01 决策树 L33-37（跨层协作 → 02+06）+ 路由表 L72-73 + Testcontainers（04）+ REST Assured（05）完整路径。
- 扣分主因: D4 扣 1——对③只声明不适用，未给任何"下一步"指引（虽无对应技能可指，但话术留白）；D1 扣 1——混合 prompt 需 agent 自行拆三段分别路由，第 0 步（L46-61）按单一场景设计，无"一请求多场景"的显式处理说明。

### Prompt T6（RANDOM_PORT + @Transactional 不回滚求因——头号坑）
- D1: 11  D2: 12  D3: 12  D4: 11  D5: 12  D6: 9  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 95/100
- 关键依据:
  1. 06 §RANDOM_PORT（L28-44）根因逐句命中锚点："HTTP 请求走**真实 Servlet 容器线程**，与测试线程**不在同一事务**。测试线程的 `@Transactional` 只回滚测试线程的事务"——非"检查事务传播配置"类错误答案。
  2. 06 L46 点名典型症状："测试'绿'但数据库有残留数据，下一个测试依赖干净状态时突然失败——'上次跑过了这次报错'的典型表现"——与 prompt 描述完全对位，"不 fail loud"特性显式点名（D5）。
  3. 替代方案双给且锚点对齐：`@Sql(AFTER_TEST_METHOD)` 完整代码（06 L50-61）+ Testcontainers `TRUNCATE`（06 L63-74）；失效场景表（L79-87）还扩展到 `@Async` / `CompletableFuture` / `AFTER_COMMIT`。
- 扣分主因: D4 扣 1——06 方案 2 代码块（L63-74）在 `@AfterEach` 中使用 `jdbcTemplate` 但类内未声明 `@Autowired JdbcTemplate` 字段，照抄编译不过；D6——根因全文复述 3 处（SKILL.md S 级表 L88 含完整根因、02 L30 含完整根因、06 L30+L82 权威源），违反仓库自身"定义一次、余处指针"标准。

### Prompt T7（@DataJpaTest 默认 H2 全绿、生产 PostgreSQL 报错求因）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 9  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 96/100
- 关键依据:
  1. 04 §为什么不用 H2（L7-16）方言差异表：`jsonb` / `ARRAY` / `SERIAL` / 大小写敏感 / 窗口函数 / 存储过程——锚点要求的差异表齐全；L16 点名"方言差异是'测试绿生产炸'的头号来源"。
  2. 修复路径完整可执行：04 L130-153 `@DataJpaTest + @Testcontainers + @AutoConfigureTestDatabase(replace = NONE) + @ServiceConnection` 完整代码（含 jsonb 查询测试）；隐蔽坑"不写 replace=NONE 容器白启动"双处点名（03 L135 / 04 L155）——非"改 SQL 迁就 H2"的治标方案。
  3. description L13 次级信号"H2 测试 + PostgreSQL 生产"原文命中；04 §Flyway（L204-214）补第二张 DDL 差异表（`CREATE TYPE AS ENUM` / `CREATE EXTENSION` / `ALTER TYPE ADD VALUE`）。
- 扣分主因: D6——H2 陷阱在 SKILL.md L113、03 L117-135（散文复述 04 结论，代码块自身截断转指针 L132）、04 §为什么不用 H2、04 L214 四处铺开；04 内两张 DDL 表（L7-14 与 L208-212）部分行语义重叠（大小写 / 类型支持类信息）。

### Prompt T8（纯单测用 @MockBean 很慢求因）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 9  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 95/100
- 关键依据:
  1. 02 §@MockitoBean vs @Mock 对比表（L146-153）直击根因：容器"不起 vs 启动 / 重建 Spring Context"、开销"毫秒 vs 秒级"——锚点"只答慢不给替代"不成立：L154-160 给出 `@ExtendWith(MockitoExtension.class)` + `@Mock` + `@InjectMocks` 替代代码。
  2. 01 L125 逐字命中锚点第三条："`@MockitoBean` 用于纯单测会启动整个 Context，是 java-unit-test 的 S 级反模式"；SKILL.md L145 注解分界句同口径（"纯单测用 `@Mock`（→ java-unit-test），切片 / 集成测试用 `@MockitoBean`（→ 本技能）"）。
  3. 版本口径一致无矛盾：`@MockBean` ≤3.3 遗留写法、4.0 已移除（SKILL.md L143 / 02 L170 / 各 reference 头注）。
- 扣分主因: D2 扣 1——"为什么慢"是诊断型 prompt，快速入门表（L33-42）无"注解选择 / 慢"行，需经 SKILL.md L145 版本与范围段或通读 02 才达对比表，两跳且入口非显式；D6——01 边界表（L116-125）与 02 对比表（L146-153）近乎同构双写（被测范围 / 容器 / 速度 / Mock 方式四行重复）。

### Prompt T9（@MockBean 替换 PaymentClient 可否——WireMock 分界）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 97/100
- 关键依据:
  1. 06 §为什么不用 @MockitoBean 替代外部调用（L155-163）对比表逐字命中锚点：替换层级"Spring Bean vs HTTP 端点"、测到什么"Bean 调用逻辑 vs **HTTP 序列化 / 反序列化 / 超时 / 重试**"；L163 展开机制（WireMock 下 PaymentClient 真发 HTTP、返回可控响应）。
  2. 06 L238-240 判据句："内部 Bean 依赖 → `@MockitoBean`；外部 HTTP API（序列化 / 超时 / 重试）→ WireMock"；L176-223 完整 WireMock 示例恰以支付为对象，含超时重试测试（`withFixedDelay(5000)` + 503 stub）。
  3. `dynamicPort()` + `@DynamicPropertySource` 注入 + `resetAll()` 防跨测试污染（06 L180-192）——可执行性完整。
- 扣分主因: D6 轻度——WireMock 判据在 SKILL.md 三处摘要（L76/L90/L114）+ 06 表 / 判据句 / 示例四层出现；D8 扣 1 属保守——判据为二分硬边界，未补"只测 Bean 编排逻辑时 `@MockitoBean` 亦可"的场景化降级说明（严格说无错，但"可以吗"类提问的完整答案应含此分支）。

### Prompt T10（mvn clean test 全量 + 输出多求快——新补维度）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 11  D6: 10  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 97/100
- 关键依据:
  1. 08 反模式表（L7-14）六行直击，四验证点全中：不 clean / `-Dtest` 单测迭代 / 读 `target/surefire-reports/*.txt` 定位 / `@Timeout` 兜底；§3（L104-111）"首次全量 → `mvn test -Dtest=OrderServiceTest#should_create_order` → 修 → -Dtest 重跑"命令可直接照抄。
  2. §1 分层降噪精确到坑：`-B -ntp`（传输行，注明"`-B` 单用不压传输行"）/ `-q`（注明副作用"成功时连 Tests run 摘要一并压掉"）/ `redirectTestOutputToFile`（fork JVM 直写 stdout，`-q` 管不到）；重定向 + grep 模板（L62-66）。
  3. description L14 次级信号"反复全量 mvn test、全文读测试输出、跑测试太慢"原文命中；§4 `@Timeout` + `junit-platform.properties` 全局兜底；§2 Spring 日志闸门（`-q` 压不到）与 Maven 层参数分治。
- 扣分主因: D5 扣 1——未提 `-Dtest=X` 在类名拼错 / 不存在时 Maven 直接报 "No tests matching pattern" 的常见迭代坑（agent 高频踩的静默失败形态，与本技能"不 fail loud"关注点同源）；§5 并行警告齐全但此点缺位。

---

## 前 3 个问题（按严重度）

1. **D6 系统性规则复述（跨文件 + 文件内双形态）**：① `@Transactional` RANDOM_PORT 失效根因全文复述 3 处（SKILL.md L88、02 L30、06 L30/L82——06 应为唯一权威源）；② 04 文件内"容器不写 static"规则 + 近同 ✗/✓ 代码重复两遍（L76-91 vs L274-285）；③ 01 边界表与 02 §@MockitoBean vs @Mock 对比表近乎同构双写；④ "测试绿生产炸"短语 4 处（SKILL.md L113 / 03 L119 / 04 L16 / 04 L214）；⑤ curl 禁令全文 9 处。与 rubric 点名的"补丁残余重复"方向一致——多轮增量（现 2199 行，较 rubric 记载的 2071 又增 128 行）持续在做加法。
2. **两处示例代码缺陷（会被 agent 直接复制）**：① 07 L354 `@Test` 标注在类 `DeployedSmokeTest` 上——JUnit 5 类级 `@Test` 无效，照抄会导致该类"No tests found"；② 06 L63-74 方案 2 代码块使用未声明的 `jdbcTemplate` 字段，照抄编译不过。均为局部 snippet 缺陷，未误导根因判断，但违反自检清单"可直接照做"标准。
3. **执行效率域留一个高频静默坑 + Kafka 无示例**：① 08 未提 `-Dtest` 匹配失败（类名拼错）时 Maven 报 "No tests matching pattern" 的兜底（`-Dsurefire.failIfNoSpecifiedTests=false` 或先列类名）——agent 迭代循环的高频卡点；② 04 对 Kafka 仅速查表一行 + "支持 `@ServiceConnection`"一句话，T2 类"发消息"场景需 agent 按 PostgreSQL 例自行类推，无最小示例锚定。
