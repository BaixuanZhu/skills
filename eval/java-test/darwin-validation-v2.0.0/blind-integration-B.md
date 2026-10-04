# java-integration-test 双盲评分报告（integration-B 组）

- 评分人：独立盲评 agent（不知道 versionA/versionB 哪个旧哪个新，不按篇幅推断，按目录字面标签打分）
- 评分对象：`snapshots/blind/integration-B/versionA/` 与 `versionB/`（各含 SKILL.md + references/01~08）
- 评的 prompt：R6-R10（回归集）+ A3-A6（对抗集），共 9 条
- 事实核验（grep/diff 完成）：
  - `failsafe` / `*IT` 在 versionB 全文 **0 处**；versionA 有 6 处（SKILL.md L16/L55/L134/L146/L162 + 08 L110/L120）
  - 「离开真实（依赖）」准入判据、「每特性 1~3」、「分支矩阵」在 versionB 全文 **0 处**；versionA 在 SKILL L15/L18/L49-53/L61/L93/L103/L111/L139/L161 + 01/04 多处落地
  - 「激活」在 versionB 仅 SKILL.md L48「（激活时先执行）」一处悬空引用，无激活协议定义；versionA 有完整协议（SKILL L32-38 + 01 L5-15）
  - 两版 `references/04-testcontainers.md` 正文逐字相同（仅头注差：A 多"两个前提"句）；`references/08` 除 A 多出的 §3 分层跑法表与 `*IT` 两条外相同
  - 篇幅：versionA 共 1138 行，versionB 共 2230 行

## 汇总表

| Prompt | 场景 | versionA | versionB |
|---|---|---:|---:|
| R6 | @WebMvcTest 切片报错 + Security | 98 | 95 |
| R7 | @Transactional 失效 + @Async 清理 | 97 | 96 |
| R8 | Testcontainers 依赖 + static 容器 | 98 | 98 |
| R9 | Boot 4 迁移三连 | 97 | 95 |
| R10 | WireMock + 异步等待 | 97 | 96 |
| A3 | 无信号不写重型测试 | 96 | **57** |
| A4 | 容器准入 + 数量锚点 | 98 | **62** |
| A5 | 命名分离（mvn test 轻量） | 96 | **63** |
| A6 | 明示信号放行 + 规模锚点 | 98 | 87 |
| **回归集小计（R6-R10，500 满）** | | **487** | **480** |
| **对抗集小计（A3-A6，400 满）** | | **388** | **269** |
| **总分（900 满）** | | **875（97.2%）** | **749（83.2%）** |

**判定：versionA 整体更好。** 回归集两版打平（差 7 分，源于 versionB 教学冗余的 D6 与 description 精度，无承重内容缺失）；胜负完全由对抗集决定——A3/A4/A5 三条行为目标上 versionB 给出误导方向或缺根治方案（功能性缺陷），versionA 全部正确拦截或正确放行。

---

## 回归集（R6-R10）

### Prompt R6（@WebMvcTest 启动报 NoSuchBeanDefinitionException + Spring Security 切片处理）

- 拿到的技能：版本 versionA
- 推演产出要点：
  1. 定性：切片"轻"= 只加载 Web 层，Service 本就不在上下文——报错是机制而非配置错误
  2. 病因点名：`@WebMvcTest` 只扫描 `@Controller`/`@RestController`，Controller 依赖的 Service 不会注入 → `NoSuchBeanDefinitionException`
  3. 解法二选一：`@MockitoBean OrderService`（首选，测 Controller 逻辑）或 `@Import(OrderService.class)`（其依赖仍需 mock），03 有最小代码块
  4. Security：切片加载 `SecurityFilterChain` 未认证 401 → 排除 `SecurityAutoConfiguration` 或 `@WithMockUser`（权限测试细节交叉引用 07 认证节）；Sa-Token 项目另有 MockMvc 不过滤器的提示
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 小计: 98/100
- 关键依据：
  1. `references/03-slice-tests.md` L22「头号隐蔽坑」段 + L24-30 代码块（`@MockitoBean OrderService orderService; // 不在切片范围，必须 mock`）
  2. `references/03-slice-tests.md` L34「@WebMvcTest 与 Security」：排除 SecurityAutoConfiguration / @WithMockUser 两条路
  3. SKILL.md L130 A 级行「@WebMvcTest 不 mock Service 导致启动失败」——SKILL 层即可拦住
- 扣分主因: Security 处理仅两行 + 外链 07 认证节，细节需跳一步（D2/D7 已微量计入）；D1 靠次级信号间接命中"切片报错排查"场景。

- 拿到的技能：版本 versionB
- 推演产出要点：
  1. 与 A 同质的病因解释：「@WebMvcTest 只加载 @Controller/@RestController，不扫描 @Service」→ 同样的报错链
  2. 解法带完整代码：① @MockitoBean Service（推荐）② @Import(OrderService.class) + @MockitoBean OrderRepository
  3. Security 两方案带代码：excludeAutoConfiguration / @WithMockUser(roles="ADMIN")
  4. 附带完整可运行的双测试用例示例（400 校验 + 正常返回），agent 可直接仿写
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 小计: 95/100
- 关键依据：
  1. `references/03-slice-tests.md` L51-72「隐蔽坑：@WebMvcTest 不加载 Service」+ 两个解法代码块
  2. `references/03-slice-tests.md` L74-92「@WebMvcTest 与 Security」双方案代码
  3. SKILL.md L106 A 级行「@WebMvcTest 不 mock Service 导致启动失败」
- 扣分主因: D6——03 同文件混有 @JsonTest/@RestClientTest 完整教学示例与全套测试用例代码，本题检索路径上存在无关承重内容；D1 description 无切片关键词（仅 MockMvc），命中略钝。

### Prompt R7（RANDOM_PORT 下 @Transactional 不回滚 + 清理方案 + @Async 注意点）

- 拿到的技能：版本 versionA
- 推演产出要点：
  1. 病因：MOCK 请求在测试线程内经 MockMvc 分发（同线程事务→回滚有效）；RANDOM_PORT 请求走真实 Servlet 容器线程，与测试线程不在同一事务→提交不受回滚控制
  2. 清理方案：`@Sql(execution=AFTER_TEST_METHOD)` 或 Testcontainers 专用容器 `@AfterEach` `TRUNCATE TABLE a, b CASCADE`
  3. `@Sql(BEFORE)` 预置数据的差异：MOCK+事务下随回滚走；RANDOM_PORT 下必须显式 AFTER 清理
  4. @Async：失效场景全集表命中「异步线程独立事务」——回滚管不到；正确姿势 Awaitility `untilAsserted` 等完成再断言，且异步已提交 → 断言后仍需 `@AfterEach` 显式清理
  5. 选型参考：重置策略对比表（@Transactional 零开销 / @Sql 快 / TRUNCATE / DirtiesContext 极慢最后手段）
- D1: 11  D2: 12  D3: 12  D4: 11  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 小计: 97/100
- 关键依据：
  1. `references/06-test-isolation.md` L12-19「失效场景全集」表（含 L17 `@Async` 行、L18 多线程行）+ L21-25 替代清理
  2. `references/06-test-isolation.md` L7-9（MOCK 有效 / RANDOM_PORT 容器线程失效的根因表述）+ L68-80 Awaitility（L80「异步线程已独立提交事务 → 仍需 @AfterEach 显式清理」）
  3. SKILL.md L115 S 级行 + L141 强约束 4（回滚仅限 MOCK）
- 扣分主因: D4 11——`@Sql`/TRUNCATE 清理为要点式一行，无完整代码块（判据、注解形式齐全，可执行但需 agent 自行组装）。

- 拿到的技能：版本 versionB
- 推演产出要点：
  1. 同 A 的病因与方案；06 有「方案 1：@Sql / 方案 2：Testcontainers+TRUNCATE」双完整代码块
  2. 失效场景全集表同样含 @Async / CompletableFuture / AFTER_COMMIT 行
  3. @Async 专项：完整异步测试示例（Awaitility 等待 + 断言 + @AfterEach TRUNCATE 清理），并解释「异步线程提交事务，@Transactional 回滚无法触及」
  4. `@Sql` 与 `@Transactional` 共存规则（MOCK 下 BEFORE 插入随回滚清理，无需 AFTER）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 小计: 96/100
- 关键依据：
  1. `references/06-test-isolation.md` L28-46（RANDOM_PORT 失效根因）+ L50-77（两个替代方案完整代码）
  2. `references/06-test-isolation.md` L79-88 失效场景表 + L315-343「与 @Transactional 回滚失效的关系」完整异步示例
  3. SKILL.md L114 强约束 2（回滚仅限 MOCK 模式）
- 扣分主因: D6 10——06 中 Thread.sleep 反模式 rationale 在「为什么不用」与正文注释两处重复；教学示例占比高（本题对口的部分反而不冗，但文件整体密度低）。

### Prompt R8（Testcontainers 依赖选择 + 镜像版本 + 容器每方法重启）

- 拿到的技能：版本 versionA
- 推演产出要点：
  1. 依赖：`spring-boot-testcontainers`（BOM 管版本）+ Boot ≤3.x 用 `org.testcontainers:postgresql` + `junit-jupiter`；Boot 4 全部加 `testcontainers-` 前缀（旧名 2.x 下 404）——附 TC 1.x→2.x 三差异对照表（模块名/import 包名/无泛型）
  2. 镜像版本：探测生产（pom datasource/docker-compose）→ 给候选+推荐（`postgres:17.11-alpine`）→ 询问用户，不静默照抄
  3. 每方法重启病因：`@Container` 字段未加 `static` → 每方法启停（十秒级 × N）；修法 static 全类共享；可选 `withReuse(true)` + `testcontainers.reuse.enable=true` 跨类复用
  4. 头注双前提（已激活 + 过准入判据）本题已天然满足（用户明示要 TC），无行为差异
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 小计: 98/100
- 关键依据：
  1. `references/04-testcontainers.md` L5-37「依赖选择：探测 → 推荐 → 询问用户」三步 + 推荐版本表
  2. `references/04-testcontainers.md` L43-95（依赖 xml + BOM 口径 + TC 2.x 差异表）；L300-313「隐蔽坑① 容器不写 static」
  3. SKILL.md L132 A 级行「Testcontainers 容器每个测试方法启停 → @Container + static」
- 扣分主因: 无实质失分（D8 11 为常态刻度：不适用清单与本题无交集）。

- 拿到的技能：版本 versionB
- 推演产出要点：与 versionA 完全同质——04 正文两版逐字相同（diff 已核），agent 产出相同的依赖坐标、镜像三步流程、static 修法与复用建议。
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 小计: 98/100
- 关键依据：
  1. `references/04-testcontainers.md` L5-37 依赖选择（与 A 逐字同）
  2. `references/04-testcontainers.md` L64-74（Boot 4 `testcontainers-` 前缀坐标）、L302-313（static 隐蔽坑）
  3. SKILL.md L108 A 级行（容器每方法启停 → static）
- 扣分主因: 无。两版在该题等分属正常（核心文件逐字保留）。

### Prompt R9（Boot 4 迁移：TestRestTemplate 注入失败 / @MockBean 编译错 / TC 依赖 404）

- 拿到的技能：版本 versionA
- 推演产出要点：
  1. TestRestTemplate：Boot 4 废弃拆到 `spring-boot-resttestclient` 独立模块 → 原 `@Autowired` 直接失败；新写 `@Autowired RestTestClient` + 类上 `@AutoConfigureRestTestClient`；暂留旧类代价三条（import 失效 + `@AutoConfigureTestRestTemplate` + runtime `spring-boot-restclient`）——不推荐
  2. @MockBean：4.0 已移除（编译错）→ `@MockitoBean`/`@MockitoSpyBean`（3.4+）；关键差异「不能声明在 @Configuration/@TestConfiguration 类里」点名，跨类共享给替代写法
  3. TC 404：TC 2.x 模块加 `testcontainers-` 前缀 + 容器类换独立包 import + 无泛型；JUnit 4 `@Rule` 移除
  4. 附带第四坑：`@SpringBootTest` 不再自动配置 MockMvc → 显式 `@AutoConfigureMockMvc`；rest-assured Boot 4 手写 6.0.1
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 小计: 97/100
- 关键依据：
  1. `references/02-spring-boot-test.md` L32-46「TestRestTemplate → RestTestClient 迁移（Boot 4）」（坐标 xml + 注入写法 + 暂留代价）
  2. `references/02-spring-boot-test.md` L65 版本口径块（@MockBean 移除 + @Configuration 限制）+ L30「Boot 4 两个必知」
  3. SKILL.md L176「Boot 4 测试工具链变化」①②③④ 汇总 + `references/04` L79-95 TC 2.x 对照表 + `references/05` L8-19 rest-assured 版本分流
- 扣分主因: D1 10——description 无迁移类关键词，靠"集成测试"语境间接命中（两版同此）。

- 拿到的技能：版本 versionB
- 推演产出要点：
  1. 三问答案与 A 同质且代码更全：RestTestClient 完整使用示例（L117-133）+ 迁移要点四条（L135-140）
  2. @MockBean → @MockitoBean：L168 版本口径块同样含「不能声明在 @Configuration 类里」
  3. TC 404 → `testcontainers-` 前缀 + 新 import + 无泛型（04 与 A 逐字同）
  4. @AutoConfigureMockMvc 显式化（02 L81）
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 小计: 95/100
- 关键依据：
  1. `references/02-spring-boot-test.md` L103-140（RestTestClient 依赖/示例/迁移要点/暂留代价）
  2. `references/02-spring-boot-test.md` L168 版本口径 + SKILL.md L147 Boot 4 ①②③④
  3. `references/04-testcontainers.md` L79-95 TC 2.x 差异表
- 扣分主因: D6 10——迁移要点分散在 02（257 行）/05（302 行）的教学代码之间，agent 需在长文件中穿行提取版本事实。

### Prompt R10（第三方支付 API 不能真调 + Thread.sleep 不稳定）

- 拿到的技能：版本 versionA
- 推演产出要点：
  1. 支付 API 必须 WireMock stub（强约束 6 + S 级「外部 API 真调」行）；判据：内部 Bean → @MockitoBean，外部 HTTP（序列化/超时/重试）→ WireMock
  2. 搭法：`options().dynamicPort()` + `@DynamicPropertySource` 注入 `payment.api.url` + `@AfterEach resetAll()`；能力表覆盖 okJson/withFixedDelay/withStatus/withFault/verify/scenario
  3. Thread.sleep 反模式点名（等待时长与实际执行无关——必然 flaky）→ Awaitility `atMost + pollInterval + untilAsserted`（首选 untilAsserted）
  4. 异步事务残留：断言完仍需 `@AfterEach` 显式清理
- D1: 11  D2: 12  D3: 12  D4: 11  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 小计: 97/100
- 关键依据：
  1. `references/06-test-isolation.md` L38-48（WireMock 判据 + 能力表）+ L50-65（dynamicPort/@DynamicPropertySource/resetAll 片段）
  2. `references/06-test-isolation.md` L68-80（Awaitility：不用 Thread.sleep 的根因 + untilAsserted 代码 + 依赖坐标）
  3. SKILL.md L143 强约束 6「外部依赖必须 stub」+ L117 S 级「外部 API 真调」行
- 扣分主因: D4 11——WireMock 无完整 `stubFor` 测试用例（能力表 + 片段可推写出，依赖坐标写"版本取当前稳定"未给具体版本）。

- 拿到的技能：版本 versionB
- 推演产出要点：
  1. 同判据同方案；06 有完整双用例示例：支付成功 stub（`stubFor(post(urlEqualTo(...)).willReturn(okJson(...)))`）+ 超时重试 stub（`withFixedDelay(5000).withStatus(503)`）
  2. WireMock 依赖带具体坐标 `org.wiremock:wiremock-standalone:3.13.2`
  3. Awaitility：Thread.sleep 反例代码 + untilAsserted/until/事件等待三模式 + 异步清理完整示例
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 小计: 96/100
- 关键依据：
  1. `references/06-test-isolation.md` L178-226 WireMock 完整示例（成功 + 重试两用例）；L171-176 依赖坐标
  2. `references/06-test-isolation.md` L244-272（Thread.sleep 反例 + Awaitility 正例）；L274-311 三种模式
  3. SKILL.md L117 强约束 5「外部依赖必须 stub」
- 扣分主因: D6 10——05/06 教学代码冗长（本题主口内容不冗，但同文件密度低）。

---

## 对抗集（A3-A6）

### Prompt A3（用户贴新写的 OrderService.createOrder()，"帮我补测试"，无任何集成/Testcontainers 表述）

- 拿到的技能：版本 versionA
- 推演产出要点：
  1. 激活协议判定（最优先）：无信号（开发期新写代码，无明示/推断信号）→ 不写重型测试
  2. 路由表首行直接命中：「单类业务逻辑（含 Service 分支矩阵，调 Repository）→ 开发期 @Mock+@InjectMocks → java-unit-test」
  3. 产出：纯单测方案——@Mock OrderRepository + @Mock PaymentClient + @InjectMocks OrderService，分支矩阵铺单测；明确不新增 @SpringBootTest/@DataJpaTest/Testcontainers
  4. 脚注消歧：「跨层协作」指验证协作本身（SQL 实际执行/事务传播/序列化管道）——不是"Service 调了 Repository"
  5. 若用户后续要验事务传播/SQL 真实效果 → 那时才走真实依赖层
- D1: 12  D2: 11  D3: 11  D4: 11  D5: 12  D6: 12  D7: 11  D8: 12  D9: 4
- 小计: 96/100
- 关键依据：
  1. SKILL.md L38 激活协议「无信号」行：「不写重型测试；新功能测试 → java-unit-test」+ L12 description 同口径（"无信号 → 不写"）
  2. SKILL.md L93 路由表首行 + L103 脚注（「不是 Service 调了 Repository」——正对本 prompt 的诱导点）
  3. SKILL.md L60 铁律 2「激活才写」+ L81 第 0 步「激活判定（最优先）」
- 扣分主因: D3/D4 11——单测用例设计（四维度/等价类）不在本技能内，靠指针移交 java-unit-test；边界行为本身无瑕疵。

- 拿到的技能：版本 versionB
- 推演产出要点：
  1. 无激活判定步骤：SKILL 第 0 步直接进"工具栈/场景"探测；description 首句「在编写、评审、补全集成测试时使用本技能」+「需要真实数据库时默认 Testcontainers」——"帮我补测试"被顺接管
  2. 「OrderService 调 OrderRepository 存订单」命中路由行「Service + Repository 跨层协作 → @SpringBootTest(MOCK) + @Transactional」
  3. 产出倾向：@SpringBootTest(MOCK) 集成测试 + OrderRepository 配 Testcontainers 真库（"默认 Testcontainers"）+ PaymentClient @MockitoBean——把还在变动的行为铺上十秒级测试
  4. 01 决策树第一分支（"单个类的方法逻辑 → 单元测试"）虽可正确路由，但其「跨层协作」定义为 Controller→Service→Repository→DB 全链，与 SKILL 路由行（Service+Repository 即命中）口径分裂——agent 两处取哪个都"有依据"
- D1: 8  D2: 9  D3: 5  D4: 6  D5: 3  D6: 10  D7: 9  D8: 4  D9: 3
- 小计: 57/100
- 关键依据：
  1. SKILL.md L75 路由行「Service + Repository 跨层协作 → @SpringBootTest(MOCK) + @Transactional」——用户代码直接命中，无任何拦截文本（全文 grep「激活」仅 L48 悬空一处）
  2. SKILL.md L5-18 description：无负面门槛（无"无信号不写"），L10-11「需要真实数据库 / Redis / Kafka 时默认 Testcontainers」助推
  3. `references/01-testing-taxonomy.md` L33-34 决策树「跨层协作（Controller → Service → Repository → DB）」与 SKILL L75 行口径不一致（D9 断链）
- 扣分主因: D5 重扣（3）——主动引导起草 @SpringBootTest/Testcontainers 方案，正是 rubric 点名的"测试久过开发"文本根源；D8 4 越界（把单类业务逻辑写成重型测试，违反其自declared边界"纯单测 → java-unit-test"）；D3 5 缺"无信号不写"判据。

### Prompt A4（需求冻结准备发版，明示"补集成测试"：20 种折扣条件组合 + jsonb 自定义 SQL）

- 拿到的技能：版本 versionA
- 推演产出要点：
  1. 明示信号（"需求冻结/准备发版/补集成测试"）→ 激活协议「直接开始（不再追问）」——正确放行，不反问
  2. ① 20 种组合过准入自问：「这条断言离开真实 DB 就不成立吗？」——折扣规则是业务分支矩阵，离开真实 DB 仍成立 → 不进容器，铺纯单测（→ java-unit-test）；S 级首行「业务分支矩阵写进容器测试」明令禁止
  3. ② jsonb SQL：离开真实 PostgreSQL 不成立（H2 不支持 `->>`）→ `@DataJpaTest` + Testcontainers + `replace=NONE`，04 有 jsonb 完整示例
  4. 数量锚：容器每特性 **1~3 条**锚定真实行为，不是 20 条全铺
  5. 镜像版本走 探测→推荐→询问 流程；补齐顺序：容器锚（迁移+冒烟+核心 SQL 1~3）→ 切片 → 特性级容器用例
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 小计: 98/100
- 关键依据：
  1. SKILL.md L49-51 容器准入判据（「不成立 → 开发期测试/切片：业务规则、多条件分支矩阵」——正对 20 组合）+ L36 明示行「直接开始」
  2. SKILL.md L111 S 级首行「业务分支矩阵 / 参数校验写进容器测试 ✗」+ L53 数量锚点「容器每特性 1~3 条」
  3. `references/04-testcontainers.md` L149-176 jsonb 完整示例（`@DataJpaTest + @ServiceConnection + replace=NONE` + `findByCategory` jsonb 用例）
- 扣分主因: D4 11——20 组合部分移交 java-unit-test（边界正确），本题两半的"怎么写"分别落在两技能，integration 侧自身只承接 jsonb 半边。

- 拿到的技能：版本 versionB
- 推演产出要点：
  1. 无激活概念——用户明示集成测试，直接开始（行为上不构成过紧，OK）
  2. ① 20 种组合：全文无「分支矩阵/准入判据/每特性」任何文本（grep 0 处）→ 无判据可依，自然落路由行「Service + Repository 跨层协作 → @SpringBootTest(MOCK)」+ 真库（"默认 Testcontainers"），20 组合大概率参数化铺进容器/全量上下文
  3. ② jsonb → `@DataJpaTest` + Testcontainers（03/04 内容正确、有完整示例）
  4. 无容器用例数量锚——仅 07 有 E2E 3~10，管不到容器层；规模无控制
  5. 结果：容器套件膨胀（20 条 × 十秒级），需求一变连带重写
- D1: 11  D2: 10  D3: 4  D4: 6  D5: 3  D6: 10  D7: 10  D8: 5  D9: 3
- 小计: 62/100
- 关键依据：
  1. SKILL.md L75 路由行（PricingService+Repository → @SpringBootTest(MOCK)）+ L10-11「需要真实数据库时默认 Testcontainers」——无任何分流判据
  2. 全文 grep「分支矩阵」「每特性」「离开真实」均 0 处（S 级表 L86-96 无对应行）——rubric 锚点「把 20 种组合写进容器 → D5 重扣」命中
  3. `references/03-slice-tests.md` L117-139 与 `references/04` L149-176：jsonb 半边答案正确（D3/D4 部分分来源）
- 扣分主因: D5 3（无拦截——20 组合进容器是本题最大功能性缺陷）；D3 4（缺准入判据这一 prompt 核心判据）；D8 5（容器规模无锚）。

### Prompt A5（加了 Testcontainers 后 mvn test 十几分钟，开发流被打断）

- 拿到的技能：版本 versionA
- 推演产出要点：
  1. 根因定位：集成测试类名 `*Test` 混进 surefire（`mvn test`）→ 命名分离根治：集成测试类名改 **`*IT`**（failsafe，`mvn verify` 才跑）
  2. `mvn test` 从此永远只含 `*Test` 开发期轻量套件（毫秒~秒级）——改一行代码跑一次不再等十几分钟
  3. 配套分层跑法：内环 `mvn test -Dtest=改动类` / 提交前 `mvn test`（全量 *Test）/ CI `mvn verify`（*Test + *IT 含容器）
  4. 存量 `*Test` 集成测试建议改名迁移，不强制一次性完成
  5. 辅助：static 容器 / `testcontainers.reuse.enable=true` / 降噪输出
- D1: 12  D2: 12  D3: 12  D4: 10  D5: 11  D6: 12  D7: 12  D8: 11  D9: 4
- 小计: 96/100
- 关键依据：
  1. SKILL.md L55「命名分离」节 + L134 A 级行「集成测试类名用 *Test 混进 mvn test ✗ → 类名 *IT（failsafe，mvn verify 跑）」
  2. `references/08-test-execution-efficiency.md` L104-110 分层跑法表（内环/提交前/CI 三行）+ L120 `*IT` 说明
  3. SKILL.md L16 description「集成测试类名 *IT（mvn verify），不混进 mvn test」+ L21 次级触发「跑测试太慢」——触发即携带答案
- 扣分主因: D4 10——未给 `maven-failsafe-plugin` 的 pom 声明片段（failsafe 并非 Maven 默认绑定，agent 需自行补插件声明）；D5 11 同源（未点名"failsafe 需显式声明"这一小坑）。

- 拿到的技能：版本 versionB
- 推演产出要点：
  1. 从 08 能取到的全部：`-Dtest=OrderServiceTest` 单类/单方法迭代、不 `clean`、失败读 surefire-reports、`-B -ntp -q` 降噪、Spring 日志抑制
  2. A 级行「容器每个测试方法启停 → @Container + static」可修"拉容器慢"的一半
  3. 全文 grep `failsafe`/`*IT` **0 处**——不存在命名分离知识，无法命中根治方案
  4. 结果：`mvn test` 仍跑全部容器测试（十几分钟），只教会开发者绕开它——缓解不根治，团队抱怨的根子还在
- D1: 9  D2: 10  D3: 4  D4: 6  D5: 5  D6: 10  D7: 9  D8: 7  D9: 3
- 小计: 63/100
- 关键依据：
  1. `references/08-test-execution-efficiency.md` L102-111「§3 迭代策略」——仅 `-Dtest`/报告定位，无分层调度表、无 `*IT`（与 A 版 08 的差异已 diff 核实）
  2. SKILL.md L5-18 description 次级触发含「跑测试太慢（反复全量 / 全文读输出）」——触发命中但所指内容不含根治（该触发语义只覆盖 token/输出维度）
  3. 全文 0 处 failsafe/`*IT`（grep 核实）——rubric 锚点「只给降噪/-Dtest 不给命名分离 → D3 扣」命中
- 扣分主因: D3 4（缺根治方案——命名分离全技能不存在）；D4 6（建议可执行但解决不了"mvn test 十几分钟"的结构问题）；D5 5（static 行命中一半，全量上下文进 mvn test 的结构性问题未识别）。

### Prompt A6（一直 curl 肉眼验收，发版前明示"系统性补齐订单模块接口测试，可重复回归，你来做"）

- 拿到的技能：版本 versionA
- 推演产出要点：
  1. 拦截 curl 模式：铁律 1「curl 结果不是测试」（无断言/不可重复/不进版本控制）+ 01 典型翻车（200 掩盖金额算错/库存没扣）
  2. 明示信号判定：「准备发版 + 系统性补齐 + 可重复回归」→ 激活协议明示行「直接开始（不再追问）」——不过度反问、不缩为纯单测
  3. 方案：订单模块核心流程 API 级 E2E——`@SpringBootTest(RANDOM_PORT)` + REST Assured 多步串联（登录拿 token → 下单 → 支付 → 查询终态，逐步 statusCode + body 字段断言）；07 骨架 + 05 串联语法/认证探测表拼合
  4. 规模锚：E2E 全套件 **3~10 条**（核心路径 + 1~2 关键异常）；容器每特性 1~3；外部支付依赖 WireMock stub；RANDOM_PORT 下 @Transactional 失效 → TRUNCATE/@Sql 清理
  5. 类名 `*IT`（failsafe）；认证方式先探测（Sa-Token token-name 从配置读）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 小计: 98/100
- 关键依据：
  1. SKILL.md L36 激活协议明示行「直接开始（不再追问）」+ L59 铁律 1 + L112-113 S 级 curl 两行——拦截与放行双向都在
  2. SKILL.md L53 数量锚点「E2E 全套件 3~10 条（见 07）」+ L143 强约束 6（支付类外部依赖 WireMock）；`references/07` L70-84 设计原则与数量表
  3. `references/05-rest-assured.md` L43-60 多步串联骨架 + L33-41 认证探测表（token 名从项目配置读，不硬编码）
- 扣分主因: D4 11——E2E 骨架在 07 为注释式步骤 + 语法外链 05，需两文件拼装（判据与断言要求齐全）。

- 拿到的技能：版本 versionB
- 推演产出要点：
  1. 拦截 curl：同等强力（铁律 1 + S 级 + 01 三场景翻车分析）
  2. 无激活协议 → 不存在"协议过紧拒写"风险，直接开始（本题两版行为一致，控制组通过）
  3. 方案同向：RANDOM_PORT + REST Assured；07 有**完整可抄的电商下单 E2E 代码**（注册→浏览→下单→支付→查询，逐步断言 + @Sql 预置 + TRUNCATE 清理 + 异常流程用例）——可执行性最强
  4. E2E 数量锚 3~10 在 07「E2E 测试数量控制」节存在——核心规模可控
  5. 缺口：无容器每特性 1~3 锚；示例类名 `OrderFlowE2ETest`/`SmokeTest` 仍是 `*Test` 后缀（无命名分离概念，新测试继续混进 mvn test）
- D1: 11  D2: 11  D3: 10  D4: 12  D5: 10  D6: 10  D7: 11  D8: 9  D9: 3
- 小计: 87/100
- 关键依据：
  1. SKILL.md L29 铁律 1 + L88-89 S 级 curl 行（拦截不弱于 A）
  2. `references/07-smoke-and-e2e.md` L117-218 完整 E2E 示例 + L228-239 数量表（E2E 3~10）
  3. `references/07` L124 示例类名 `OrderFlowE2ETest`（*Test 后缀）+ 全文无 `*IT`——规模与命名两个次级锚缺失
- 扣分主因: D3 10/D5 10——仅 E2E 层有数量锚（容器层无 1~3 锚），且产出的重型测试继续以 `*Test` 命名混进 `mvn test`（与 A5 问题无缝衔接）；主体行为（拦截 + 开始 + 规模大体可控）正确，故不重扣。

---

## 总体判定与关键差异

**总分：versionA 875/900（97.2%） vs versionB 749/900（83.2%）——versionA 整体更好。**

三条最关键的判据：

1. **对抗集拦截能力是胜负手（388 vs 269 / 400）**：A3（无信号）、A4（容器准入 + 1~3 锚）、A5（命名分离）三个行为目标上，versionA 分别由「激活协议表 + 路由首行 + 跨层协作脚注」（SKILL.md L32-38/L93/L103）、「容器准入自问 + S 级首行 + 每特性 1~3」（L49-53/L111）、「*IT + failsafe 四处落地」（L16/L55/L134/L146/L162 + 08 §3）承住；versionB 三项对应文本 **grep 全为 0 处**，A3/A4 给出误导方向（D5 ≤3），A5 缺根治方案（D3 4）——按 rubric 均属功能性缺陷重扣。
2. **回归集精简不退步（487 vs 480 / 500）**：两版 `references/04` 逐字相同，02/03/05/06/07 判据、版本事实、陷阱表在 versionA 全部保留（删的是教学代码与论证散文）；7 分差全部来自 versionB 的 D6 教学冗余与 D1 description 精度，无一条 prompt 因精简丢承重判据——符合本轮"删教学内容不降产出质量"的核心主张。
3. **versionB 存在真实断链（D9）**：SKILL.md L48「第 0 步（激活时先执行）」悬空引用一个全文未定义的"激活"概念；路由表 L75「Service + Repository 跨层协作 → @SpringBootTest(MOCK)」与 `references/01` 决策树「跨层协作 = Controller→Service→Repository→DB 全链」（L33-34）口径分裂——后者正是 A3 失分的文本根源，前者是改漏残留的机械证据。

（附：versionB 在 A6 上主体正确——curl 拦截、直接开始、E2E 3~10 锚与完整可抄示例均在，是四条对抗题中两版差距最小的一条；这佐予对抗集分差来自判据缺失而非整体能力差。）
