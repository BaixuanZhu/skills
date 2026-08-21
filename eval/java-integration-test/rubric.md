# 评分标准（java-integration-test 达尔文盲评用）

> 你是独立盲评 agent。你手里有：java-integration-test 技能（SKILL.md + 8 个 references）、11 条 test-prompt。
>
> 对每个 prompt，假设你是"接到该请求的 coding agent，手里只有这套技能"，判断能否产出合格结果。按 9 维度打分。

## 9 维度评分（SkillLens 风格，满分 100）

每个维度 0–12 分（D9 为 4 分），按"agent 拿着这套技能执行 prompt，能否产出合格结果"打分：

| 维度 | 权重 | 判分锚点 |
|------|------|---------|
| D1 触发精度 | 12 | description 的关键词/场景，能否让 agent 在该用时用、不该用时不用；边界让位是否清晰 |
| D2 可发现性 | 12 | 想找的信息（注解语义/陷阱/代码模式），在合理跳转步数内能找到 |
| D3 覆盖完整 | 12 | prompt 涉及的知识点，技能是否有答案（无盲点） |
| D4 可执行性 | 12 | 给出的代码/配置/判据，agent 能否直接照做（不悬空、不模糊） |
| D5 防错/陷阱 | 12 | 隐蔽坑（不 fail loud 的错）是否点名 |
| D6 信息密度 | 12 | 有无冗余表达/重复内容/纯说理段落拖累 agent |
| D7 内部导航 | 12 | 路由表/交叉引用是否清晰，agent 知道下一步看哪 |
| D8 范围明确 | 12 | 不适用场景是否声明（不让 agent 越界到纯单测/前端 E2E/性能测试） |
| D9 整体一致性 | 4 | 术语/规则/版本号是否前后一致、无自相矛盾 |

## 各 prompt 判分要点

### T1（写 Controller 测试·竞争场景）—— 重点 D1/D3/D4

验证切片优先 + 选层次：
- **D1 触发**：能否在"写测试"这种宽泛场景下激活（竞争过 java-unit-test / spring-boot-dev）
- **D3 覆盖**：@WebMvcTest 切片、@MockBean mock Service、MockMvc 断言是否齐全
- **D4 可执行**：给出的注解组合是否正确（@WebMvcTest + @MockBean + MockMvc）

**判分锚点**：用全量 `@SpringBootTest` 测单层 Controller（未选切片）→ D3/D4 重扣（≤4）。@WebMvcTest 不 mock Service 导致启动失败未提醒 → D5 扣。

### T2（测 Service 全链路·竞争场景）—— 重点 D3/D4/D8

验证真实依赖 + 边界：
- **D3 覆盖**：@SpringBootTest + Testcontainers + @ServiceConnection 是否齐全
- **D4 可执行**：@ServiceConnection 语法正确（Spring Boot 3.1+），隔离策略明确
- **D8 范围**：是否把「发消息」这类跨外部依赖正确交给 WireMock（不真调）

**判分锚点**：默认用 H2 替代 PostgreSQL（未用 Testcontainers）→ D3/D5 重扣。未说明 @ServiceConnection 的版本门槛（3.1+）→ D4 扣。**未探测生产依赖 + 询问用户镜像版本（静默写死 tag）→ D4 扣**。

### T3（curl 反模式·独占陷阱）—— 重点 D1/D5

技能核心价值，权重最高：
- **D1 触发**：能否在"curl 看起来没问题"这种场景下识别这是反模式（不是附和"对，接口是好的"）
- **D5 防错**：能否点名 curl 的本质缺陷（无断言/不可重复/不进版本控制/无隔离）

**判分锚点**：附和 curl（"返回 200 说明接口正常"）→ D1/D5 重扣（≤4）。这是技能存在的根本理由，失守 = 技能失败。

### T4（手动启动再测·独占陷阱）—— 重点 D4/D5

curl 前置动作反模式：
- **D4**：能否识别「手动 spring-boot:run + curl」是反模式，引导进程内 @SpringBootTest(RANDOM_PORT)
- **D5**：是否点名手动启动的代价（不可重复、依赖手动、不可版本控制）

**判分锚点**：认可"手动启动最真实"（未识别反模式）→ D4/D5 重扣。与 T3 混淆（只提断言不提启动方式）→ D5 扣。

### T5（边界让位·多技能竞争）—— 重点 D1/D8

技能边界判定的终极测试：
- **D1**：能否在多技能竞争下正确拆解职责（①单测 ②集成 ③前端 E2E）
- **D8**：是否明确让位单测→java-unit-test、前端 E2E→不适用（Selenium/Playwright/Cypress）

**判分锚点**：越界包办单元测试设计（@Mock+@InjectMocks 展开）或前端 E2E（引导 Playwright）→ D8 重扣（≤4）。

### T6（@Transactional 失效·独占陷阱）—— 重点 D4/D5

头号坑，直击隔离核心：
- **D4**：能否识别 RANDOM_PORT 下 HTTP 走独立线程、@Transactional 回滚失效——这是根因
- **D5**：能否给出 @Sql(AFTER) / Testcontainers 重置的正确替代

**判分锚点**：未识别根因（如建议"检查事务传播配置"）→ D4/D5 重扣（≤4）。这是技能最隐蔽的坑，漏 = 技能核心价值缺失。

### T7（H2 方言陷阱·独占陷阱）—— 重点 D4/D5

- **D4**：能否识别 H2 ≠ PostgreSQL（jsonb/ARRAY/序列/函数），根因是方言差异
- **D5**：能否给出 Testcontainers 真实库（@AutoConfigureTestDatabase(NONE) + @ServiceConnection）

**判分锚点**：建议"改 SQL 让 H2 也兼容"（治标不治本）→ D4/D5 扣。未提方言差异表 → D3 扣。

### T8（@MockBean vs @Mock·独占陷阱）—— 重点 D4/D5

- **D4**：能否识别 @MockBean 启动 Context（慢），纯单测应用 @Mock（不起容器）
- **D5**：是否点明分界线（纯单测 @Mock → java-unit-test；切片/集成 @MockBean → 本技能）

**判分锚点**：只答"@MockBean 慢"但给不出正确替代 → D4 扣。未指向 java-unit-test 边界 → D8 扣。

### T9（WireMock vs @MockBean·独占陷阱）—— 重点 D4/D5

- **D4**：能否识别 @MockBean 跳过 HTTP 序列化，WireMock 才能测序列化/超时/重试
- **D5**：是否给出正确选择判据（内部 Bean → @MockBean；外部 HTTP → WireMock）

**判分锚点**：答"@MockBean 就够了"（未识别序列化/超时/重试测不到）→ D4/D5 重扣。

### T10（执行效率·独占陷阱）—— 重点 D3/D4

新补维度，验证 08 是否到位：
- **D3 覆盖**：mvn test（不 clean）、-Dtest 单测、-q 降噪、surefire 报告定位是否齐全
- **D4 可执行**：命令是否可直接照做（具体 flag、路径）

**判分锚点**：只答"用 IDE 跑"或"减少测试数量"（未命中 -Dtest/-q/报告定位）→ D3/D4 扣。

### T11（无 H2 项目搭集成测试·定位回归核心）—— 重点 D1/D4/D5

v1.3.0 定位修复的核心验证（此前技能以「H2 已存在」为前提，导致无 H2 项目被跳过）：
- **D1 触发**：项目没引 H2、测试未搭 → 技能是否仍激活（不被「没 H2 就不需要」误导跳过）
- **D4 可执行**：是否探测生产依赖（驱动 / datasource）→ 给候选版本**询问用户**（不静默写死镜像 tag）
- **D5 防错**：是否默认 Testcontainers 而非默认 H2；无 Docker 时是否显式降级声明（非静默）

**判分锚点**：以「项目没引 H2」为由跳过 / 默认引 H2 → D1/D5 重扣（≤4）。静默写死镜像 tag 未询问用户 → D4 扣。把「询问版本」做成开放式提问（无候选无推荐）→ D4 扣。

## 打分输出格式（每个 prompt 必填）

```
### Prompt Tx（一句话场景描述）
- D1: x  D2: x  D3: x  D4: x  D5: x  D6: x  D7: x  D8: x  D9: x
- 该 prompt 小计: xx/100
- 关键依据（≤3 条，引用技能里的具体位置：行号/标题/代码块）:
  1. ...
  2. ...
  3. ...
- 扣分主因（这个 prompt 最大的失分点）:
```

## 铁律

- 每条依据必须能指向技能里的具体位置（行号/标题/代码块）。禁止泛泛说"覆盖全面"。
- **功能性缺陷重扣**：错误根因、错误代码、越界包办 → 对应维度 ≤4 分，不能因"文字通顺"给中庸分。
- **陷阱遗漏重扣**：隐性陷阱（curl 反模式/@Transactional 失效/H2 方言/@MockBean 分界/WireMock）是技能核心价值，漏任何一个 → D5 扣 2-3 分。
- **越界重扣**：T5 的边界让位是核心判据，越界写纯单测/前端 E2E → D8 ≤4。
- D6（信息密度）：冗余越多扣分越重。本技能刚从 2031 行缩到 1986 行又补 08 到 2071 行，重点核查补丁是否留了残余重复。
