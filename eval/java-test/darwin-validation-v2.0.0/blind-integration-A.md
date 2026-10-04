# java-integration-test 双盲评分报告（integration-A）

> 独立盲评：同一技能两个版本快照（`version1` / `version2`），评 R6-R10 + A3-A6 共 9 条 prompt。
> 按盲评铁律：不猜新旧、不按篇幅打分；每条先独立推演两版产出，后按 9 维度打分；依据均指向技能文件具体位置。
> 事实核验（grep）：version1 全文无 "failsafe"、无 `*IT` 命名约定、无激活协议、无"每特性 1~3"数量锚点；version2 的 `references/04` 与 version1 逐字相同（仅文件头多两行准入前提）。

## 汇总表

| Prompt | 场景 | version1 小计 | version2 小计 |
|---|---|---:|---:|
| R6 | @WebMvcTest 切片报错 + Security | 96 | 99 |
| R7 | @Transactional 失效 + 清理 + @Async | 98 | 99 |
| R8 | Testcontainers 依赖选择 + static 容器 | 98 | 98 |
| R9 | Boot 4 迁移三连修 | 98 | 99 |
| R10 | WireMock + 异步等待 | 98 | 99 |
| A3 | 无信号不写重型测试 | 61 | 99 |
| A4 | 容器准入 + 数量锚点 | 71 | 99 |
| A5 | 命名分离，mvn test 保持轻量 | 76 | 99 |
| A6 | 明示信号放行 + 规模锚点 | 90 | 99 |
| **总分** | | **786 / 900** | **890 / 900** |

- 回归集 R6-R10：v1 488 / 500，v2 494 / 500（基本持平——删掉完整范例未造成回归性失分）。
- 对抗集 A3-A6：v1 298 / 400，v2 396 / 400（差距全部来自这里）。
- 判定整体更好的版本：**version2**。

---

## 回归集

### Prompt R6（@WebMvcTest 切片报 NoSuchBeanDefinitionException + Spring Security 特殊处理）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 定位病因：`@WebMvcTest` 只加载 `@Controller`/`@RestController`，不扫描 `@Service` → OrderService 无 Bean 定义 → 报 `NoSuchBeanDefinitionException`（03「隐蔽坑」节直接点名此异常）。
  2. 给修法①：`@MockitoBean OrderService`（最常见，测 Controller 逻辑）；修法②：`@Import(OrderService.class)` 载真实 Service、其依赖再 mock——两方案均有完整代码。
  3. Security 子问：切片会加载 `SecurityFilterChain`，未认证 401；给排除 `SecurityAutoConfiguration` 与 `@WithMockUser(roles=...)` 两套完整代码；附 Sa-Token 项目警示（MockMvc 不经过 Sa-Token 过滤器 → 用 RANDOM_PORT）。
  4. 补充：切片 vs 全量对照表 + 速度表，说明"切片轻"与"报错"不矛盾（轻 = 只加载 Web 层，Service 本就不在）。
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 9  D7: 12  D8: 12  D9: 4
- 小计: 96/100
- 关键依据：
  1. `version1/references/03-slice-tests.md` L51-57「隐蔽坑：@WebMvcTest 不加载 Service」——精确点名该异常与根因；L59-71 两方案代码。
  2. `version1/references/03-slice-tests.md` L74-92「@WebMvcTest 与 Security」——排除法 + @WithMockUser 完整代码 + Sa-Token 注记。
  3. `version1/SKILL.md` L106 A 级表行「@WebMvcTest 不 mock Service 导致启动失败」。
- 扣分主因：D6——同一修法（@MockitoBean Service）在 03 中以代码形式出现 3 次（L27 完整示例内、L63 ①、L68-71 ②旁），完整教学示例（L24-48）与隐蔽坑节重复陈述，通读有拖累。

---

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 同样定位病因：03「头号隐蔽坑」一段话讲清"只扫描 @Controller → Service 不注入 → NoSuchBeanDefinitionException"。
  2. 给修法：`@MockitoBean OrderService`（附 5 行最小示例）或 `@Import(MyService.class)`（其依赖仍需 mock）。
  3. Security 子问：两条路——排除 `excludeAutoConfiguration = SecurityAutoConfiguration.class` 或 `@WithMockUser`（细写法指向 07 认证节的判据表）；Sa-Token 警示保留（切片鉴权行为与生产不同 → RANDOM_PORT）。
  4. 回答"不是说切片轻吗"：03 开头「切片只加载某一层…不起全量 Context」+ 速度对比表，逻辑自洽。
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 小计: 99/100
- 关键依据：
  1. `version2/references/03-slice-tests.md` L22「头号隐蔽坑」——异常名 + 根因 + 两解法压缩为一段，无重复。
  2. `version2/references/03-slice-tests.md` L32-36 Security 两方案 + Sa-Token 注记；`version2/references/07-smoke-and-e2e.md` L86-94 认证判据表（@WithMockUser 适用边界）。
  3. `version2/SKILL.md` L5-8 description 显式列出 `@WebMvcTest / @JsonTest / @RestClientTest` 触发词——触发比 v1 更精准（v1 只列 MockMvc）。
- 扣分主因：D4——@WithMockUser 的完整写法需跳一步到 07 认证节（v1 在 03 内联完整代码）；对能自行写代码的 agent 影响有限，扣 1。

---

### Prompt R7（RANDOM_PORT 下 @Transactional 不回滚 + 清理方案 + @Async 注意点）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 解释根因：RANDOM_PORT 下 HTTP 请求走真实 Servlet 容器线程，与测试线程不在同一事务——测试线程回滚管不到请求线程的提交；MOCK 模式走 MockMvc 同线程所以有效（06 两节对照 + 02 webEnvironment 表）。
  2. 清理方案：`@Sql(executionPhase = AFTER_TEST_METHOD)` 删残留（推荐）或 Testcontainers + `@AfterEach` TRUNCATE——两者均有完整代码。
  3. @Async 注意点：失效场景全集表明确列「`@Async` 异步方法 + @Transactional → ✗ 异步线程独立事务」；专节给 Awaitility `untilAsserted` 等待 + `@AfterEach` TRUNCATE 显式清理的完整示例，并解释"异步线程已提交事务 → 数据残留"。
  4. 附 `@Sql(BEFORE)` 与 @Transactional 共存规则（MOCK 下随事务回滚无需 AFTER）。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 小计: 98/100
- 关键依据：
  1. `version1/references/06-test-isolation.md` L28-46「RANDOM_PORT 模式：回滚失效（头号陷阱）」根因 + ✗ 示例；L48-77 两套替代清理完整代码。
  2. `version1/references/06-test-isolation.md` L79-89 失效场景全集表（L85 @Async 行）；L315-343 异步测试完整示例（untilAsserted + @AfterEach 清理）。
  3. `version1/SKILL.md` L91 S 级表行 + L114 强约束 2（@Transactional 回滚仅限 MOCK）。
- 扣分主因：D6——TRUNCATE 清理代码在 L63-77（方案 2）与 L336-340（异步 cleanup）重复出现；异步注意事项在表格（L85+L89）与专节（L315-343）两次完整陈述。

---

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 同样根因解释：MOCK 有效 / RANDOM_PORT 失效的两段对照 prose（容器线程 vs 测试线程），加 webEnvironment 表。
  2. 清理方案：`@Sql(AFTER_TEST_METHOD)`、Testcontainers + `@AfterEach` `TRUNCATE TABLE ... CASCADE`、`@Sql(BEFORE)` 共存规则（MOCK 随回滚、RANDOM_PORT 必须显式 AFTER）——规则全部在，代码片段级。
  3. @Async 注意点：失效场景全集表**原样保留**（含 @Async / CompletableFuture / AFTER_COMMIT 三行），Awaitility 节明说"异步线程已独立提交事务 → 数据残留，`untilAsserted` 断言完仍需 `@AfterEach` 显式清理"——组合方案（await + 清理）完整可拼装。
  4. 复位策略对比表指引按场景选清理。
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 小计: 99/100
- 关键依据：
  1. `version2/references/06-test-isolation.md` L11-19「失效场景全集」表——@Async 行 L17 保留；L7-9 根因两段。
  2. `version2/references/06-test-isolation.md` L67-81 Awaitility 节：L75 untilAsserted 示例 + L80 异步残留 → 显式清理规则；L21-25 替代清理清单。
  3. `version2/references/02-spring-boot-test.md` L5-13 webEnvironment 表（RANDOM_PORT 行「✗ 失效」）。
- 扣分主因：D4——异步 + 清理的组合无整段可抄示例（v1 有），判据与零件齐全、需 agent 自行拼装，扣 1。

---

### Prompt R8（Testcontainers 依赖怎么选/镜像版本怎么定 + 容器每方法重启哪里错）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. ①依赖/镜像：走「依赖选择」三步——探测生产（pom/datasource/docker-compose 对照表）→ 给候选选择题式询问（推荐 `postgres:17.11-alpine`，对齐生产优先）→ 不答复用推荐值并明示；坐标按 Boot 版本二选一（≤3.x 旧名 / 4.x `testcontainers-*` 前缀），BOM 管版本不手写。
  2. ②每方法重启根因：`@Container` 缺 `static` → 每测试方法启停一次；修法 `static` 全类共享（✗/✓ 对照代码），或 `testcontainers.reuse.enable=true` 跨类复用。
  3. 附 BOM 版本陷阱（Boot 3.5 BOM 管 1.21.3，Docker v29 需 ≥1.21.4 属性 override）与 `@ServiceConnection` 依赖坑。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 小计: 98/100
- 关键依据：
  1. `version1/references/04-testcontainers.md` L5-37「依赖选择：探测 → 推荐 → 询问用户」三步 + 探测表 + 推荐镜像表。
  2. `version1/references/04-testcontainers.md` L302-313「隐蔽坑① 容器不写 static → 每个测试方法启停」✗/✓ 代码；L97-112 `@Container + static` 机制说明。
  3. `version1/SKILL.md` L108 A 级表行「容器每个测试方法启停 → static / reuse」；L125 使用流程第 2 步「不静默选镜像 tag」。
- 扣分主因：D6——static 陷阱在 L97-112 与 L302-313 两处完整重复（正文 + 隐蔽坑各一遍代码）。

---

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 前置判定：用户说"要给 JPA 测试引入 Testcontainers"——命中激活协议明示行（"要 Testcontainers"）→ 直接开始，无摩擦；JPA/SQL 断言天然过容器准入判据。
  2. ①依赖/镜像：与 v1 完全相同的三步流程 + 探测表 + 推荐表 + Boot 4/≤3.x 坐标对照（`04` 文件除文件头两行准入前提外逐字相同）。
  3. ②static 根因与修法：同 v1（✗/✓ 代码 + reuse），A 级表同款行。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 小计: 98/100
- 关键依据：
  1. `version2/references/04-testcontainers.md` L5-37 依赖选择三步（与 v1 同文）；L302-313 static 隐蔽坑。
  2. `version2/references/04-testcontainers.md` L3 文件头「两个前提」——明示信号（"要 Testcontainers"）在 `version2/SKILL.md` L36 激活表明示行，本 prompt 不被拦。
  3. `version2/SKILL.md` L132 A 级表 static 行（与 v1 L108 同文）。
- 扣分主因：与 v1 相同的 D6（static 陷阱两处重复）——`04` 两版逐字相同，得分相同属正常（内容逐字保留）。

---

### Prompt R9（Boot 3.3 → 4.0：TestRestTemplate 注入失败 / @MockBean 编译错误 / TC 依赖 404）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. TestRestTemplate：Boot 4 废弃、拆到 `spring-boot-resttestclient` 独立模块（test scope）→ 加依赖 + 换 `@Autowired RestTestClient` + `@AutoConfigureRestTestClient`；附暂留旧类的代价清单（包移动 + `@AutoConfigureTestRestTemplate` + `spring-boot-restclient` 依赖——不比迁移少）。
  2. @MockBean：4.0 已移除（编译错误）→ 字段直接替换 `@MockitoBean` / `@MockitoSpyBean`；关键差异"不能声明在 @Configuration / @TestConfiguration 类里"，跨类共享改 `@MockitoBean(types={...})`。
  3. TC 404：Testcontainers 2.x 模块加 `testcontainers-` 前缀、容器类换独立包且无泛型——对照表 + 写法对照代码；BOM 管 2.0.x 无需手写版本。
  4. 附带：`@SpringBootTest` 不再自动配 MockMvc → 显式 `@AutoConfigureMockMvc`（自检清单兜底核对全部坐标）。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 小计: 98/100
- 关键依据：
  1. `version1/SKILL.md` L147「Boot 4 测试工具链变化」①②③④——三个报错逐一对应，入口文件即含全部判据；L142 自检清单同款核对行。
  2. `version1/references/02-spring-boot-test.md` L103-140 RestTestClient 依赖 XML + 迁移要点（L135-139，含暂留代价）。
  3. `version1/references/04-testcontainers.md` L79-95 TC 1.x→2.x 差异表 + 2.x 写法对照；`02` L168 @MockitoBean 版本口径（@Configuration 禁区）。
- 扣分主因：D6——Boot 4 事实在 SKILL L147、02、04、自检清单四处重述；02 相关段落嵌在含大量教学示例（MockMvc/WebTestClient/@TestConfiguration/@ActiveProfiles 完整代码）的长文件里，定位需翻找。

---

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 前置：修存量测试报错属"存量照跑照修"（激活协议无信号行的放行范围），不新增重型用例，直接修。
  2. 三个修复判据与 v1 完全一致：RestTestClient 坐标 + `@AutoConfigureRestTestClient`（02 迁移节 + "Boot 4 两个必知"）；`@MockitoBean` 替换 + @Configuration 禁区；TC 2.x 前缀/包名/无泛型对照表（04 与 v1 同文）。
  3. v2 的 02 把「HTTP 测试客户端不再自动配置（@AutoConfigureRestTestClient / @AutoConfigureWebTestClient）」提为正文 prose（v1 藏在代码注释里），迁移提示更直接。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 12  D9: 4
- 小计: 99/100
- 关键依据：
  1. `version2/references/02-spring-boot-test.md` L32-46「TestRestTemplate → RestTestClient 迁移」——坐标、注解、暂留代价三要点齐全；L30「Boot 4 两个必知」。
  2. `version2/references/02-spring-boot-test.md` L65 @MockitoBean 版本口径（4.0 已移除 → 编译错误 + @Configuration 禁区）。
  3. `version2/SKILL.md` L176 Boot 4 ①②③④ + L171 自检清单；`04`（与 v1 同文）L79-95 TC 对照表。
- 扣分主因：D6——Boot 4 事实同样四处重述（SKILL/02/04/清单），与 v1 同构；仅 02 周边教学内容更少、定位更快，故 11 而非 10。

---

### Prompt R10（第三方支付 API 不能真调 + Kafka 消费者 Thread.sleep 不稳）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 支付 API：外部 HTTP 依赖必须 stub——WireMock 判据（要测序列化/超时/重试，@MockitoBean 跳过 HTTP 层不够）；完整示例含 `dynamicPort()` + `@DynamicPropertySource` 注入 + `@AfterEach resetAll()` + stub 成功/超时重试两条用例；依赖坐标钉死 `wiremock-standalone:3.13.2`。
  2. Thread.sleep：本质是等待时长与执行时长无关 → 必然 flaky；换 Awaitility `atMost + pollInterval + untilAsserted`（完整代码），首选 untilAsserted（报错清晰）。
  3. 附 capabilities 表（延迟/500/scenario/verify）与 S 级表「外部 API 真调」行、A 级表「固定端口冲突」行兜底。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 小计: 98/100
- 关键依据：
  1. `version1/references/06-test-isolation.md` L157-176 WireMock 判据表 + 依赖 XML（L169-176 钉版本）；L178-225 完整可抄示例（stub + 重试 + resetAll）。
  2. `version1/references/06-test-isolation.md` L248-272「为什么不用 Thread.sleep」✗/✓ 对照代码；L286-311 三种 await 模式。
  3. `version1/SKILL.md` L93 S 级表行（外部 API 真调 → WireMock）+ L109 A 级表行（固定端口 → dynamicPort）。
- 扣分主因：D6——06 是两版中最长文件；untilAsserted 模式在模式清单（L288-292）与异步节（L325-332）两次完整出现，WireMock 大示例教学性强、对只需判据的场景偏重。

---

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 同判据：内部 Bean → @MockitoBean；外部支付 API（序列化/超时/重试）→ WireMock 真发 HTTP 打可控 Mock Server；S/A 级表同款行拦截真调与固定端口。
  2. WireMock 骨架：`dynamicPort()` + `@DynamicPropertySource` 注入 + `@AfterEach resetAll()` 代码片段；capabilities 表保留（willReturn/withFixedDelay/withStatus/withFault/verify/scenario）；依赖写 `org.wiremock:wiremock-standalone（test scope，版本取当前稳定）`——不钉版本号。
  3. Awaitility：同款"不用 Thread.sleep"根因 + untilAsserted 示例 + until 变体 + 依赖说明（Boot 3.x starter-test 已传递）。
  4. stub DSL 细节（stubFor/urlEqualTo）由 capabilities 表的方法名 + agent 自身知识补齐。
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 小计: 99/100
- 关键依据：
  1. `version2/references/06-test-isolation.md` L39 判据一句话 + L50-63 WireMock 骨架代码（dynamicPort/注入/resetAll 三坑全在）+ L65 依赖。
  2. `version2/references/06-test-isolation.md` L67-80 Awaitility：L69 Thread.sleep 根因 + L72-75 untilAsserted 示例。
  3. `version2/SKILL.md` L117 S 级表行 + L133 A 级表行（与 v1 同文）。
- 扣分主因：D4——无完整 `stubFor` 用例可抄、WireMock 版本号不钉（"取当前稳定"）；陷阱与判据齐全，代码需 agent 自产，扣 1。

---

## 对抗集

### Prompt A3（用户贴新写的 OrderService.createOrder()，"帮我补测试"，无任何集成信号）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 技能被"代码里有 Repository/PaymentClient"拉入后，SKILL 路由表行「Service + Repository 跨层协作 → @SpringBootTest(MOCK) + @Transactional（秒~十秒）」直接命中——createOrder 调 OrderRepository 字面即匹配"Service + Repository 跨层协作"。
  2. 全技能无激活门槛、无"新功能先写纯单测"的规则：description 反而写"需要真实数据库时默认 Testcontainers"、"覆盖：跨层协作（Controller→Service→Repository）"——倾向加码而非收敛。
  3. 最可能的产出：为 createOrder 起草 `@SpringBootTest(MOCK)` + `@Transactional` 集成测试（PaymentClient 用 @MockitoBean），或单测/集成测并给；正是本轮要拦截的"测试久过开发"方案。
  4. 技能内存在一条反向路径（01 决策树首支"单个类的方法逻辑 → 单元测试 → java-unit-test"），但与路由表行无优先级规则、无消歧文本——两规则同命中一个场景，agent 取舍随机。
- D1: 8  D2: 11  D3: 6  D4: 6  D5: 4  D6: 10  D7: 8  D8: 5  D9: 3
- 小计: 61/100
- 关键依据：
  1. `version1/SKILL.md` L75 路由表行「Service + Repository 跨层协作 | @SpringBootTest(MOCK) + @Transactional | 02+06」——无任何"仅限验证协作本身"限定；L59 第 0 步同款倾向（"测 Service + Repository + 真实 DB → @SpringBootTest + Testcontainers"）。
  2. `version1/references/01-testing-taxonomy.md` L22-23 决策树「单个类的方法逻辑 → 单元测试」——与上条同场景冲突命中，全文件无优先级/消歧规则（对照 v2 L103 脚注）。
  3. 全 version1 grep 无"激活协议/无信号"类文本（仅 SKILL L48 标题"激活时先执行"指技能自身启动动作，非用户信号判定）。
- 扣分主因：D5/D8 重扣（对抗锚点）——无信号场景下技能文本主动把 agent 推向 @SpringBootTest 全量上下文方案，且与自身决策树互相矛盾（D9 同扣）；这正是"测试久过开发"的文本根源。

---

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 首先过激活协议：「无信号（开发期常规写码/新功能开发）→ 不写重型测试；新功能测试 → java-unit-test（纯单测）；存量照跑照修，不删不新增」——本 prompt 无任何集成/Testcontainers 表述，判定无信号。
  2. 路由表首行显式覆盖本场景：「单类业务逻辑（含 Service 分支矩阵，调 Repository）→ 开发期 → @Mock+@InjectMocks → java-unit-test"——"调 Repository"被点名属纯单测。
  3. 脚注消歧：""跨层协作"指验证协作本身（SQL 实际执行/事务传播/序列化管道）——不是"Service 调了 Repository"（那属纯单测，mock Repository 铺分支矩阵）"——封死 v1 式误读。
  4. 产出：@Mock OrderRepository + PaymentClient 的纯单测（分支/等价类设计），明示不新增 @SpringBootTest/Testcontainers；可附一句"需求冻结后可按激活协议补集成层"。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 12  D9: 4
- 小计: 99/100
- 关键依据：
  1. `version2/SKILL.md` L33-38 激活协议表（无信号行动作）；L9-12 description 同款判定（触发层即编码该门槛）。
  2. `version2/SKILL.md` L93 路由表首行（"含 Service 分支矩阵，调 Repository"→ java-unit-test）+ L103 脚注（"跨层协作"消歧）。
  3. `version2/SKILL.md` L40 铁律前注""测试久过开发"的根源" + L61 铁律 2「激活才写」。
- 扣分主因：仅 D6 微扣——纯路由决策场景下入口文件含大量本次用不到的 S/A 表与工具节（结构清晰、不构成误导）。

---

### Prompt A4（需求冻结准备发版，明示"补集成测试"：① 20 种折扣条件组合 ② jsonb 自定义 SQL）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 明示补集成测试 → 技能全速前进（v1 无门槛，此点无碍）。
  2. ② jsonb：v1 强项——路由到 @DataJpaTest + Testcontainers，04 有同场景可抄示例（jsonb 操作符 + `@AutoConfigureTestDatabase(replace=NONE)` + H2 方言陷阱），处理正确。
  3. ① 20 种组合：无"断言离开真实 DB 是否成立"准入判据、无"分支矩阵不进容器/全量上下文"拦截文本——PricingService 调 Repository 即命中 L75「Service + Repository 跨层协作 → @SpringBootTest(MOCK) + @Transactional」，20 个条件组合最可能铺成 20 条全量上下文测试（用户明说"补集成测试"更强化此走向）。
  4. 唯一沾边的收敛文本是 07 的 E2E 设计原则（"不求全覆盖，那是单测的职责"）——只管 E2E 层，管不到本场景。
- D1: 12  D2: 11  D3: 6  D4: 7  D5: 4  D6: 10  D7: 11  D8: 7  D9: 3
- 小计: 71/100
- 关键依据：
  1. `version1/SKILL.md` L75 路由行 + grep 全文无"每特性 1~3 / 准入判据 / 分支矩阵"文本——① 无任何拦截。
  2. `version1/references/04-testcontainers.md` L149-176 jsonb 用例完整示例（② 部分满分水平）。
  3. `version1/references/01-testing-taxonomy.md` L22-23 单类逻辑→单测 与 SKILL L75 的同场景冲突（D9）。
- 扣分主因：D5 重扣（锚点："20 种组合写进容器/全量上下文测试"）——① 的方案方向错误且无拦截；D3/D4/D8 连带：一半被测对象（分支矩阵）缺正确判据，可执行的是误导性方案。

---

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 激活：明示行命中（"补集成测试 / 需求冻结 / 准备发版"）→ **直接开始，不再追问**——不过紧。
  2. ① 20 种组合过容器准入自问："这条断言离开真实 DB 就不成立吗？"——折扣规则是业务分支矩阵，离开真实 DB 仍成立 → 不进容器，铺纯单测（mock Repository，毫秒级），S 级表首行明令禁止写进容器测试。
  3. ② jsonb SQL：断言依赖 PostgreSQL 方言特性 → 容器，`@DataJpaTest` + Testcontainers + `replace=NONE`（04 同场景示例），**每特性 1~3 条**锚定——明示"不是越多越好"。
  4. 交付按强约束 1 顺序：容器锚（迁移可跑 + 冒烟 + 核心 SQL 1~3 条）→ 契约切片 → 特性级容器用例；自检清单逐项兜底（准入/≤3 条/矩阵未铺容器）。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 12  D9: 4
- 小计: 99/100
- 关键依据：
  1. `version2/SKILL.md` L49-52 容器准入判据（机械化自问 + 成立/不成立双向清单）+ L53 数量锚点（每特性 1~3 / 矩阵不铺容器）。
  2. `version2/SKILL.md` L111 S 级表首行「业务分支矩阵 / 参数校验写进容器测试 ✗ → 铺纯单测；容器每特性 1~3 条」——精确拦截①、放行②。
  3. `version2/references/04-testcontainers.md` L149-176 jsonb 完整示例（与 v1 同文）+ L3 文件头两前提（准入判据复述）。
- 扣分主因：仅 D6 微扣——② 需通读与 v1 等长的 04（共享文件，Flyway/Docker checklist 等节本次不用）。

---

### Prompt A5（Testcontainers 集成测试拖垮 mvn test 十几分钟，开发流被打断）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 触发 08（"跑测试太慢"是 description 次级触发信号）→ 给降噪方案：`-B -ntp` + `-q` / simpleLogger + `logging.level.root` 分层压日志，`.mvn/maven.config` 持久化。
  2. 给迭代方案：`-Dtest=改动类` 单测重跑、不 clean、失败读 surefire 报告——缓解"改一行跑一次"，但 `mvn test` 仍包含全部 Testcontainers 测试，根因未除。
  3. 全文（SKILL + 08 + 其余 references）无 failsafe、无 `*IT` 命名分离、无"mvn test 只留开发期套件"规则（grep 核实为零命中）——根治方案在技能内不存在；唯一的线索是 07 L97 CI 流水线草图里一行裸的"mvn verify → 集成测试 + 冒烟"，无命名约定与插件机制，agent 无法据此落地。
  4. A 级表 static/reuse 行可稍降容器重启开销，但救不了"全量容器套件在 mvn test 里"。
- D1: 12  D2: 11  D3: 5  D4: 8  D5: 6  D6: 10  D7: 10  D8: 10  D9: 4
- 小计: 76/100
- 关键依据：
  1. grep 全 version1：`failsafe` 零命中、`*IT` 作为命名约定零命中（仅 `OrderRepositoryIT` 出现在 04 示例类名中，无任何规则文本解释）；`version1/references/07-smoke-and-e2e.md` L97 是唯一 "mvn verify" 提及（CI 草图，无机制）。
  2. `version1/references/08-test-execution-efficiency.md` L5-15 反模式表 + §3（L102-111）——只有降噪/-Dtest/不 clean，无命名分离。
  3. `version1/SKILL.md` L120 强约束 8——同款降噪口径，无调度分层。
- 扣分主因：D3（锚点："只给降噪/-Dtest 不给命名分离 → 缺根治方案"）——用户的核心痛点（mvn test 被容器套件拖垮）在该版技能里没有答案；D5 连带："`*Test` 命名混入 mvn test"这一静默结构坑从未点名。

---

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 根治：集成测试类名改 `*IT`（failsafe，`mvn verify` 才跑）——`mvn test` 从此只含 `*Test` 开发期轻量套件；存量叫 `*Test` 的建议改名迁移，不强制一次性。
  2. 分层跑法表：内环 `mvn test -Dtest=改动类` / 提交前 `mvn test`（全量 *Test）/ CI·发布门禁 `mvn verify`（*Test + *IT 全量）——开发流即刻恢复。
  3. 三处联动兜底：SKILL「命名分离」节 + A 级表行（"*Test 混进 mvn test" ✗）+ 输出前自检清单（类名 *IT 项）——新生成测试不会再犯。
  4. 叠加 v1 同款降噪/-Dtest 建议作为辅助。
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 小计: 99/100
- 关键依据：
  1. `version2/SKILL.md` L55「命名分离」节（*IT + failsafe + mvn verify + 存量迁移口径）；L134 A 级表行；L162 自检项——三处落地。
  2. `version2/references/08-test-execution-efficiency.md` L104-110 分层跑法表（内环/提交前/CI 三行命令级）+ L120 *IT 规则复述。
  3. `version2/SKILL.md` L146 强约束 9（降噪 + 调度 + 命名分离合一）。
- 扣分主因：D4 微扣——failsafe 的 pom 配置片段（goal 绑定）未给出，靠 agent 标准知识补齐；命名约定与运行语义本身无悬空。

---

### Prompt A6（一直 curl + 肉眼验收；本次发版明示"订单模块接口测试系统性补齐，要可重复回归"）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 拦截 curl 模式：铁律 1 + S 级表两行 + 01 curl 反模式专节（FIRST 三违反 + 翻车场景）——明确"curl 结果不是测试"，改为可断言/可重复/进版本控制的测试。此点 v1 是强项。
  2. 直接开工（v1 无任何激活协议，不存在拒写/过度反问风险——控制组通过）。
  3. 方案：`@SpringBootTest(RANDOM_PORT)` + REST Assured + Testcontainers（订单模块依赖），05 认证探测表 + 多步串联骨架、07 完整电商 E2E 示例可整段改造复用；清理用 @Sql/TRUNCATE（RANDOM_PORT 回滚失效有拦截）。
  4. 规模控制**不完整**：07 数量表给"E2E 3~10 条、E2E 只测核心路径 + 1~2 异常"，能约束 E2E 层；但无"容器每特性 1~3 条"、无"业务分支矩阵不进接口/容器层"判据——"系统性补齐"下的订单业务规则组合很可能被铺进 API 测试，套件规模无上限锚。
- D1: 12  D2: 12  D3: 9  D4: 11  D5: 10  D6: 9  D7: 12  D8: 11  D9: 4
- 小计: 90/100
- 关键依据：
  1. `version1/SKILL.md` L29 铁律 1 + L88-89 S 级表前两行（curl/手动启动）——拦截有力。
  2. `version1/references/07-smoke-and-e2e.md` L230-239 E2E 数量表（3~10）+ 设计原则 5——规模锚仅覆盖 E2E 层。
  3. grep 全文无"每特性 1~3"、无分支矩阵分层规则——接口级/容器级用例数量无锚（rubric A6 第③点只部分满足）。
- 扣分主因：D3/D5——缺容器每特性数量锚与矩阵分流规则，"系统性补齐"易膨胀为大规模重型套件；D6——07 完整 E2E 百行示例教学占比高（对 D4 有帮助、对密度有拖累）。

---

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 拦截 curl：同强度（铁律 1 + S 表 + 01 反模式），且 description 首句即"消灭仿真测试——替代 curl 调接口 + 肉眼判断"。
  2. 激活判定：明示行命中（"准备发版 / 系统性补齐"）→ **直接开始，不再追问**——激活协议在该放行处放行，无过紧。
  3. 规模有锚：E2E 全套件 3~10 条（SKILL L53 + 07 表）；容器每特性 1~3 条；订单业务规则的分支矩阵 → 纯单测（java-unit-test），接口套件只收核心流程 + 1~2 关键异常；支付等外部依赖 WireMock stub。
  4. 交付形态：`*IT` 命名 + failsafe（mvn verify 跑回归），`@Sql`/TRUNCATE 清理，自检清单（激活已过/准入已过/数量上限/命名/断言结构化）逐项核对。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 12  D9: 4
- 小计: 99/100
- 关键依据：
  1. `version2/SKILL.md` L36 激活表明示行（"准备发版"→直接开始）——控制组通过；L59 铁律 1 拦 curl。
  2. `version2/SKILL.md` L53 数量锚点（E2E 3~10 / 容器每特性 1~3 / 矩阵不铺）+ `version2/references/07-smoke-and-e2e.md` L77-84 数量表同口径。
  3. `version2/SKILL.md` L162 自检「类名 *IT」+ `08` L104-110 分层调度——"可重复回归"落在 mvn verify 门禁。
- 扣分主因：仅 D6 微扣——完整链路需通读 SKILL + 01 + 05 + 06 + 07 + 08 多文件（重型任务本身所需，内容无冗余重复）。

---

## 总结判据（version2 整体更优的三条关键理由）

1. **对抗集 A3/A4 的功能性差异（v1 61/71 vs v2 99/99）**：version1 的路由表行「Service + Repository 跨层协作 → @SpringBootTest(MOCK) + @Transactional」（`version1/SKILL.md` L75）无激活门槛、无准入判据制衡——新功能"帮我补测试"与"20 种折扣组合"两类场景被该行直接推向全量上下文/容器测试，且与其自身 01 决策树（L22-23）同场景冲突无消歧（D5 按锚点重扣至 4）。version2 用激活协议（L33-38）+ 容器准入自问（L49-52）+ S 级表首行（L111）+ 路由脚注（L103）四件套在两处精确拦截，且明示信号照常放行（A4/A6 无过紧）。
2. **A5 的根治方案缺失（v1 76 vs v2 99）**：version1 全文 grep 零命中 failsafe / `*IT` 命名约定（仅 `07:97` CI 草图一行裸 "mvn verify"），`mvn test` 被容器套件拖垮只能给降噪/-Dtest 缓解；version2 在 SKILL L55 + A 级表 L134 + 自检 L162 + `08` §3 分层调度表（L104-110）四处落地命名分离。
3. **回归集持平佐证"删教学不降质"（488 vs 494 / 500）**：version2 删掉 02/03/05/06/07 的完整教学示例后，R6-R10 无一承重缺失——版本坐标、失效场景全集表、依赖选择三步、TC 1.x/2.x 对照、jsonb 示例等判据逐字保留（`04` 两版逐字相同，R8 同分 98 即为对照证据）；唯一可见代价是 WireMock 完整示例与钉死版本（R10）、异步组合示例（R7）、Security 内联代码（R6）各扣 1 分 D4，均由 D6 密度增益补回有余。
