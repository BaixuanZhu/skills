# 盲评 C · java-integration-test（工作区当前版本）

日期：2026-08-19

被评对象：`skills/java-integration-test/SKILL.md`（146 行，version 1.2.0）+ `references/01~08`（共 2054 行）。
评分依据：`eval/java-integration-test/rubric.md`（9 维度，D1~D8 各 12 分、D9 满分 4 分）。

---

## 逐 prompt 打分

### Prompt T1（写 Controller 参数校验测试——切片优先）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 96/100
- 关键依据：
  1. `03` 第 22-48 行：`@WebMvcTest(OrderController.class)` + `@MockitoBean OrderService` + MockMvc `status().isBadRequest()` / `jsonPath("$.errors[0].field")` 完整可抄代码，400 与正向用例齐备。
  2. `03` 第 51-57 行「隐蔽坑：@WebMvcTest 不加载 Service」点名 `NoSuchBeanDefinitionException` 根因与两条解法（`@MockitoBean` / `@Import`）。
  3. SKILL.md 第 70 行路由表「单层 Controller + 参数校验 / 异常 → @WebMvcTest + MockMvc → 03」，且 description 第 12-14 行次级触发含「@SpringBootTest 全量上下文测单层 Controller」直接命中本题纠偏点。
- 扣分主因：无实质失分。D1 扣 1 是"帮我写测试"宽泛措辞下与 java-unit-test 的竞争需靠 description 第 15-16 行边界句裁决；D6 扣 1 是版本口径句「@MockitoBean 需 Boot 3.4+（≤3.3 写作 @MockBean…）」在 01/03/06/07 四个文件头逐字重复。

### Prompt T2（测 Service 到 DB 全链路，生产 PostgreSQL）
- D1: 11  D2: 11  D3: 11  D4: 12  D5: 11  D6: 10  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 93/100
- 关键依据：
  1. `04` 第 93-107 行 `@ServiceConnection`（标题即标 Spring Boot 3.1+）完整代码 + 第 112-126 行 3.0 及以下 `@DynamicPropertySource` 降级；SKILL.md 第 51 行第 0 步要求先读 parent 版本决定可用性——版本门槛三处闭环。
  2. `04` 第 7-16 行方言差异表 + 强约束 4（SKILL.md 第 113 行）杜绝 H2 替代；`06` 第 9-25 行 MOCK 模式 `@Transactional` 回滚有效示例覆盖隔离策略。
  3. 外部依赖分界明确：HTTP 类（支付/短信）→ 强约束 5 WireMock（SKILL.md 第 114 行），Kafka → `04` 第 183 行速查表 `KafkaContainer`。
- 扣分主因：D3 扣 1——「发消息」若为 MQ，`04` 对 Kafka 仅速查表一行 + 依赖坐标，无 `@ServiceConnection` Kafka 完整示例（PostgreSQL/Redis 有、Kafka 无）；D6 扣 2——`04` 全文 293 行，TC 1.x→2.x 对照表、Flyway/Liquibase 迁移节对本场景是背景负担，且 TC 2.x 前缀信息在文中出现 3 处（第 43/58-74/187 行）。

### Prompt T3（curl 返回 200 想确认接口是好的——curl 反模式拦截）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 96/100
- 关键依据：
  1. SKILL.md 第 27 行铁律 1 点名 curl 四缺陷（无断言/不可重复/不进版本控制/无隔离）；description 第 12-14 行次级触发「用 curl 测接口」「"返回 200 就是通过了"」与用户措辞几乎逐字对应——不会附和。
  2. `01` 第 60-81 行场景 1「返回 200 但业务逻辑错」正是本题形态（订单金额算错、库存没扣全被 200 掩盖），并附 REST Assured 逐字段断言（`data.totalAmount` equalTo 等）正确替代代码。
  3. `01` 第 50-57 行 FIRST 原则表 S/R/T 三行各带操作性后果列；`05` 第 257-266 行 curl vs REST Assured 六维对照表补齐可断言/可重复/CI/版本控制维度。
- 扣分主因：D6 扣 2——curl 反模式内容分布在 SKILL.md（铁律/S 级表/强约束 1/自检清单）、`01`（三场景）、`05`（对照表）、`07`（第 72-89 行冒烟 curl 段）四处，`07` 的 curl 冒烟示例与 `01` 场景重复度偏高；D7 扣 1——`01` 场景 1 代码后未直接指针到 `05`，需回路由表跳转。

### Prompt T4（手动 spring-boot:run + curl 逐接口测——启动方式反模式）
- D1: 12  D2: 11  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. SKILL.md 第 86 行 S 级表第 2 行「手动启动应用再 curl "测试" → `@SpringBootTest(webEnvironment=RANDOM_PORT)` 进程内启动 + 自动断言」——启动方式与断言缺失两个维度分开点名，与 T3 不混淆；description 第 13 行次级触发「手动启动应用再调接口」逐字命中。
  2. `01` 第 55 行 R 行点名手动启动代价：「依赖手动启动应用 + 手动执行 → 换人/换机跑不了；CI 中不存在」；`08` 第 12 行反模式表同款拦截（mvn spring-boot:run → @SpringBootTest 进程内）。
  3. 替代路径可执行：`02` 第 32-44 行 RANDOM_PORT 代码 + `05` 第 30-39 行 `RestAssured.port = port` 接法，序列化/过滤器场景由 `02` webEnvironment 决策表第 26 行路由到 RANDOM_PORT + REST Assured。
- 扣分主因：D5 扣 1——未有一处明确说破「手动启动并不比进程内更真实（同一份代码同一个内嵌服务器），只是把启动责任从测试框架挪到人」，需 agent 自行综合 01+08 两处；D6/D7 各扣 1——同一反模式在 S 级表、`01`、`08` 三处复述，导航分散。

### Prompt T5（单测 + 集成 + 前端 E2E 三段式——边界让位）
- D1: 11  D2: 12  D3: 12  D4: 11  D5: 11  D6: 11  D7: 11  D8: 12  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. SKILL.md 第 146 行「不适用：前端 E2E（Selenium / Playwright / Cypress）、性能测试、安全测试」明确挡掉③；第 145 行「纯单元测试（@Mock+@InjectMocks，毫秒级，不起容器）→ java-unit-test」让位①，且 description 第 15-16 行在触发层即有同款边界句。
  2. `01` 第 19-44 行决策树第一分支「单个类的方法逻辑 → 单元测试 → java-unit-test」，②类请求经「跨层协作 → @SpringBootTest(MOCK)+@Transactional」分支承接；`07` 第 119-218 行 E2E 完整示例（Testcontainers + REST Assured 多步串联）支撑②落地。
  3. `01` 第 117-125 行边界表五维对照 + 第 125 行警示「@MockitoBean 用于纯单测会启动整个 Context，是 java-unit-test 的 S 级反模式」——防止 agent 越界替①写 @Mock 展开设计。
- 扣分主因：D4 扣 1——让位后本技能对①不再给任何内容（设计使然，但 agent 需自行确认 java-unit-test 技能是否在环境可用，技能未提示该动作）；D5/D7 各扣 1 为边缘项。

### Prompt T6（@Transactional 在 RANDOM_PORT 下不回滚——头号坑）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 96/100
- 关键依据：
  1. `06` 第 28-46 行「RANDOM_PORT 模式：回滚失效（头号陷阱）」给出正确根因：HTTP 请求走真实 Servlet 容器线程、与测试线程不在同一事务，测试线程回滚触及不到容器线程已提交的数据——并配 ✗ 反例代码 + 第 46 行典型症状「测试"绿"但数据库有残留，下一个测试突然失败——"上次跑过了这次报错"」与用户描述完全对应。
  2. `06` 第 50-75 行两个替代方案完整可抄：`@Sql(executionPhase = AFTER_TEST_METHOD)` 与 Testcontainers `@AfterEach` TRUNCATE CASCADE；SKILL.md 第 88 行 S 级表、第 111 行强约束 2 同口径。
  3. `06` 第 79-87 行完整失效场景表额外覆盖 @Async / CompletableFuture / AFTER_COMMIT——同类根因一并拦截。
- 扣分主因：D6 扣 2——同一规则在 SKILL.md 内三层复述（铁律 3 / S 级表第 88 行 / 强约束 2 / 自检清单第 132 行共四处）之外，`02` 第 32-44 行的 RANDOM_PORT 空壳示例与 `06` 方案 1 结构同构（重复维护两份示例）；D1 扣 1——description 次级触发「测试间数据互相污染」命中场景但未点名 @Transactional 字样，需路由后才能确认。

### Prompt T7（H2 测试全绿、生产 PostgreSQL 报错——方言陷阱）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 96/100
- 关键依据：
  1. `04` 第 7-15 行「为什么不用 H2」方言差异表覆盖 jsonb / ARRAY / SERIAL / 大小写敏感 / 窗口函数 / 存储过程，第 16 行明示「H2 与 PostgreSQL 的方言差异是"测试绿生产炸"的头号来源」——直接回答用户"为什么"；description 第 13 行次级触发「H2 测试 + PostgreSQL 生产」逐字命中。
  2. `04` 第 130-153 行完整解法：`@DataJpaTest` + `@AutoConfigureTestDatabase(replace = NONE)` + `@ServiceConnection` + jsonb 查询测试；`03` 第 117-135 行隐蔽坑段给骨架 + 指针「完整可运行代码在 04」——不重复且可执行。
  3. 治本方向明确：强约束 4（SKILL.md 第 113 行）+ `04` 第 270 行「CI 无 Docker 降级 H2 须标注覆盖不完整」——不给"改 SQL 兼容 H2"的治标出路。
- 扣分主因：D6 扣 2——H2 反对论在 SKILL.md（S 级表第 89 行 + 强约束 4 + 自检清单）、`03`（§隐蔽坑）、`04`（两张差异表：第 7-15 行通用方言表与第 206-212 行迁移 DDL 表部分条目语义重叠）多处展开；D8 扣 1 为边缘项（未显式说"不要改 SQL 迁就 H2"，但整体方向无歧义）。

### Prompt T8（纯单测里用 @MockBean 很慢——注解分界）
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 97/100
- 关键依据：
  1. `02` 第 144-152 行 `@MockitoBean` vs `@Mock` 五维表直击根因：容器「不起 vs 启动/重建 Spring Context」、开销「毫秒 vs 秒级」；第 154-168 行两段并排代码给出正确替代（`@ExtendWith(MockitoExtension.class)` + `@Mock` + `@InjectMocks`）。
  2. `01` 第 125 行「@MockitoBean 用于纯单测会启动整个 Context，是 java-unit-test 的 S 级反模式」+ SKILL.md 第 145 行注解分界句（纯单测 @Mock → java-unit-test）完成让位，不越界包办单测设计。
  3. `02` 第 170 行版本口径处理用户旧注解名：@MockBean 是 Boot ≤3.3 写法、3.4 废弃、4.0 已移除（编译错误）——用户原文用 @MockBean 也能被正确接住并顺带纠偏。
- 扣分主因：D1 扣 2——description 第 14 行次级触发「跑测试太慢」语义上更导向 `08` 执行效率而非 `02` §注解分界，用户说"纯单元测试"时 java-unit-test 技能先触发是正确结局、但本技能内部定位该问题需经路由表二跳；其余为边缘项。

### Prompt T9（外部支付 API 用 @MockBean 替换行不行——WireMock 分界）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 97/100
- 关键依据：
  1. `06` 第 157-163 行机制对比表点破要害：`@MockitoBean` 替换 Bean → 跳过 HTTP 序列化；WireMock 替换 HTTP 端点 → 测得到序列化/反序列化/超时/重试——正面回答"可以吗"（不完全可以，会漏测传输层行为）。
  2. `06` 第 240 行判据句「内部 Bean 依赖 → @MockitoBean；外部 HTTP API → WireMock」一句话可执行；第 176-224 行完整代码含 `dynamicPort()` + `@DynamicPropertySource` 注入 + 超时重试 stub 用例（第 209-222 行）。
  3. 防污染细节到位：`resetAll()` in `@AfterEach`（第 189-192 行）+ SKILL.md 第 106 行 A 级表「WireMock 固定端口，并行测试端口冲突」。
- 扣分主因：D8 扣 1——`06` 判据处未交叉引用 `03` 第 162-183 行 `@RestClientTest`（若目的是测 PaymentClient 自身的序列化/解析，切片是更轻路径），需 agent 自行发现；D6 扣 1 为边缘项（06 内三个对比表对象各异，不算冗余）。

### Prompt T10（mvn clean test 全量跑太慢——执行效率）
- D1: 11  D2: 12  D3: 12  D4: 9  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 91/100
- 关键依据：
  1. `08` 第 104-109 行迭代策略直击本题：「首次 mvn test -q → 之后 mvn test -Dtest=OrderServiceTest（含 #方法 级）→ 失败读 target/surefire-reports/*.txt 定位」；第 111 行「mvn clean 触发全量重编译——日常迭代用 mvn test」正面回应用户的 clean 习惯。
  2. `08` 第 20-33 行降噪分层（`-B -ntp` 压传输行 / `-q` 压 Maven INFO 并警示会连 Tests run 摘要一起压掉 / simpleLogger 留 WARN）+ 第 63-66 行重定向 grep 关键行——命令全部可直接照做。
  3. `08` 第 119-124 行 `@Timeout` 兜底有覆盖（方法级 + 全局 junit-platform.properties）。
- 扣分主因：D4 扣 3——`08` 第 121-123 行「`@Timeout(30)` // 类级 class SlowIntegrationTest」是**错误代码**：JUnit 5 `@Timeout` 的 @Target 仅 METHOD/CONSTRUCTOR/ANNOTATION_TYPE，标注在类上直接编译失败（"annotation type not applicable to this kind of declaration"），agent 照抄即错；防挂死的兜底示例本身是个不 fail loud 的坑，D5 因此连带扣 1。D6 扣 2——SKILL.md 强约束 8（第 117 行）以约 200 字全文内联 `08` §1-2 细节（-B -ntp / simpleLogger / logging.level / maven.config 一行一参数 / surefire / -Dtest / 不 clean），与 `08` 重复度约六成，与其余强约束的"概要+指针"风格不一致，agent 会两处读同一内容。

---

## 汇总

### 10 prompt 总分

| T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 | 平均 |
|----|----|----|----|----|----|----|----|----|-----|------|
| 96 | 93 | 96 | 95 | 95 | 96 | 96 | 97 | 97 | 91 | **95.2/100** |

### 9 维度均分

| D1 触发精度 | D2 可发现性 | D3 覆盖完整 | D4 可执行性 | D5 防错陷阱 | D6 信息密度 | D7 内部导航 | D8 范围明确 | D9 一致性 |
|---|---|---|---|---|---|---|---|---|
| 11.1 | 11.7 | 11.9 | 11.6 | 11.6 | 10.5 | 11.6 | 11.2 | 4.0 |

### 前 3 个问题（按严重度）

1. **`08` 第 121-123 行类级 `@Timeout` 是错误代码（功能性缺陷，全套件唯一实锤代码错误）**：`@Timeout(30)` 标注在 `class SlowIntegrationTest` 上——JUnit 5 该注解 @Target 不含 TYPE，类级标注直接编译失败。超时兜底一节是 T10 的验证点之一，示例本身即坑。
2. **`07` 第 354-355 行 `@Test` 标注在 class 上（同类编译错误）**：部署后冒烟示例 `@Test class DeployedSmokeTest { @Test void … }`——外层 `@Test`（@Target 仅 METHOD）编译不过；该节是 curl→自动化冒烟引导（T3/T4 类场景）的落点之一。
3. **D6 残余重复（补丁痕迹）**：① SKILL.md 强约束 8 全文内联 `08` §1-2 约 200 字细节，重复度六成，与其余强约束"概要+指针"风格不一致；② 版本口径句「示例注解 @MockitoBean 需 Boot 3.4+（≤3.3 写作 @MockBean，4.0 已移除）」在 01/03/06/07 四个文件头逐字重复；③ SKILL.md 快速入门表（第 33-42 行）与测试层次路由表（第 67-77 行）功能同构，同一"场景→文件"映射维护两份；④ `02` 第 32-44 行 RANDOM_PORT 空壳示例与 `06` 方案 1（第 50-61 行）结构同构；⑤ `07` 第 81-89 行 health 断言片段复述第 19-42 行完整类。次级问题：Kafka「发消息」场景仅 `04` 速查表一行、无 `@ServiceConnection` 完整示例（T2 D3 扣分来源）。

### 附注（不计分）

- 版本一致性核实：skills/ 与 plugins/ 镜像 SKILL.md 完全一致（version 1.2.0）；marketplace/ plugin.json 的 java-test group 版本 1.4.1 = 组内 max（java-unit-test 1.4.1），符合组规则，无矛盾。
- rubric D9 全部 prompt 给 4 分：@MockitoBean 新旧口径全文统一（旧名仅在版本口径处显式标注）、"测试绿生产炸"等术语单一写法、强约束 8 与 `08` 参数细节逐项吻合。
