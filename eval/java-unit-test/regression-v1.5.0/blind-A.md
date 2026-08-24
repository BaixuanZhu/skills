# 盲评报告 A 组（version1 vs version2）— java-unit-test 回归 v1.5.0

- 打分日期：2026-08-24
- 评分者：独立盲评 agent A（只依据 snapshots/version1 与 snapshots/version2 的实际内容打分，不猜新旧）
- 依据文件：rubric.md（9 维度 + 对抗集特别规则）、test-prompts.md（R1-R7 + A1-A4）
- 文件差异盘点（打分前核实）：01/03/04 两版完全相同；差异集中在 SKILL.md（description 重写、DoD 第二条、guide-pro 节删除）、02（删 2 处 guide-pro 括注）、05（覆盖率立场改写、JaCoCo 节、遗留代码阈值自包含、antipattern 改写）、06（重组为 §1 栈基线决策表 + JUnit4 表移入 §1 + §3 静态两节合并 + §4 范围、非 Spring 坐标块补 assertj-core）

## 总分汇总

| 口径 | version1 | version2 | 差值（v2−v1） |
|---|---|---|---|
| 总分（11 条 × 100） | 912 | 1056 | **+144** |
| 回归集 R1-R7（700 满） | 630 | 675 | **+45** |
| 对抗集 A1-A4（400 满） | 282 | 381 | **+99** |

---

## 逐条打分

### Prompt R1（Spring Boot 项目主动问 JaCoCo 接入）
- 拿到的技能：版本 version1（A 组）
- D1: 11  D2: 11  D3: 11  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 91/100
- 关键依据（≤3 条）:
  1. 05 L38-62「JaCoCo 接入（仅项目未有时，且用户问及覆盖率才提）」给出完整 plugin XML（L42-58）+ `mvn test` → `target/site/jacoco/index.html`（L60）+ L62「测试不过时报告不生成」坑及 verify/`mvn jacoco:report` 解法——用户主动问，条件满足，直接可用。
  2. 06 §5（L216-218）与 05 双路标互指，导航不丢；description L13「覆盖率反向校验」命中用户"覆盖率"用词。
  3. 扣分点：L46 硬编码 `<version>0.8.12</version>` 存在陈旧漂移风险（L40 还称 parent "内置 JaCoCo profile"，与 v2 的 pluginManagement 表述相比不够准）。
- 扣分主因: 硬编码插件版本 + parent 机制表述略旧，长线可执行性打折（D3/D4/D5 各扣 1）。

### Prompt R1（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据（≤3 条）:
  1. 05 L34-59「JaCoCo 接入（用户问覆盖率时才给方案）」：XML 无版本号 + L55 明确「Spring Boot parent 的 pluginManagement 已管理版本，可不写 `<version>`；独立项目取当前最新稳定，勿照抄旧教程数字」——对 R1 的 Spring Boot 场景是精确答案且防陈旧。
  2. L36「盲区核对不依赖本工具……仅当用户问……才给接入方案，并向用户说明定位：机械核对手段，不是合格证」——触发条件与回答姿态一致，无 v1 的口径矛盾。
  3. L59 保留「测试不过报告不生成」坑 + 解法，无内容丢失。
- 扣分主因: 仅剩极轻微冗余（05 L3-5 一句话立场段较长但信息密度高），无实质失分点。

### Prompt R2（五年遗留 Service：static 满地 + new 依赖，怎么开始补测）
- 拿到的技能：版本 version1（A 组）
- D1: 11  D2: 10  D3: 11  D4: 11  D5: 11  D6: 10  D7: 10  D8: 11  D9: 3
- 该 prompt 小计: 88/100
- 关键依据（≤3 条）:
  1. 05 L96-107「遗留代码：先特征测试锁现状」三步路线（录当前输出当期望值 → 小步重构消除测不了的根因 → 回四维度）+ 切片策略，直接回答"怎么开始"；06 L88-105 头号陷阱（内部 new → 构造器注入）、L110 PowerMock 禁令配套。
  2. 05 L108「严重超标方法（认知复杂度 ≥~30）……见 `java-coding-guide-pro/references/12-complexity.md`」——跨插件文件，只装本技能（java-test 插件）的环境中不存在，400 行类大概率触达该句，agent 追链即断（D2=10、D9=3）。
  3. SKILL L171 guide-pro 关系段对 R2 回答无增量，属轻度冗余（D6=10）。
- 扣分主因: 05 L108 断链（外部文件依赖）+ guide-pro 残留引用拖累导航与一致性。

### Prompt R2（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 96/100
- 关键依据（≤3 条）:
  1. 05 L93-107 特征测试三步 + 切片策略与 v1 等价，回答"第一步"完整可执行。
  2. L105 判据自包含：「认知复杂度 ≥~30 的方法判为『严重超标』，其重构同样要求『先特征测试锁现状，再拆解』——阈值是机械判据，防止主观摇摆」，无外部文件依赖（grep 证实 v2 全文 guide-pro 引用为 0）。
  3. 02 L37/L116 已删 guide-pro 括注，全技能无断链点（D9=4）。
- 扣分主因: 无实质失分；仅 05 L3-5 立场段与 L16 机械判据句有少量语义重叠（D6=11）。

### Prompt R3（提交前自查 review 清单，重点"分支测到没怎么检查"）
- 拿到的技能：版本 version1（A 组）
- D1: 11  D2: 11  D3: 11  D4: 8  D5: 9  D6: 10  D7: 11  D8: 11  D9: 2
- 该 prompt 小计: 84/100
- 关键依据（≤3 条）:
  1. SKILL L157-165「测试完成判定（DoD 锚点）」三条勾选即用户要的 checklist，L161/L163 两条可机械执行。
  2. L162 第二条对"分支测到没"的回答分两截：有 JaCoCo 时看 Branch 列红色（`BRANCH_MISSED > 0`）可执行；**无 JaCoCo 时只有一句"人工核对分支表"，无任何步骤**（怎么列、对照什么、勾什么都没说），另给"或按成本收益决定是否接入"的岔路——用户要的是自查动作，得到的是决策分叉（D4=8）。
  3. L162「或按成本收益决定是否接入」与 05 L60「仅当用户问……才提接入」**互相矛盾**（D9=2）：DoD 引导 agent 主动评估接入，05 禁止主动提，回答口径摇摆（D5=9）。
- 扣分主因: DoD 第二条无工具路径无步骤 + 与 05 接入口径自相矛盾，正是"分支怎么检查"这一核心问题的含糊处。

### Prompt R3（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据（≤3 条）:
  1. SKILL L161 第二条改写为「分支盲区清零」：机械判据前置（JaCoCo 口径 = Branch 列 Missed = 0，无 JaCoCo 时人工分支清单全勾），再分两路径——有 JaCoCo → `mvn test` 看报告 Missed>0 逐条补；无 JaCoCo → **读被测方法源码列分支清单逐分支对照已设计用例**，动作、对象、判据齐备。
  2. 05 L16 同口径复述（「分支盲区清零 = JaCoCo Branch 列 Missed = 0（无工具时人工分支清单全勾），不设百分比目标」），SKILL/05 术语一致（grep 证实 5 处均为"分支盲区清零"）。
  3. 05 L34/L36 接入条件唯一（仅用户问时给方案），与 DoD「默认路径不依赖工具」无矛盾——v1 的摇摆消除。
- 扣分主因: 无实质失分；仍完整回答"分支测到没怎么检查"且更可执行。

### Prompt R4（非 Spring Maven，junit-jupiter + mockito-core 4.11.0，问版本差异 + mockStatic 可用性）
- 拿到的技能：版本 version1（A 组）
- D1: 10  D2: 9  D3: 11  D4: 10  D5: 11  D6: 9  D7: 9  D8: 11  D9: 4
- 该 prompt 小计: 83/100
- 关键依据（≤3 条）:
  1. 答案存在但散布三处：06 §1 L21-22 坐标基线（junit 5.10.2 / mockito 5.11.0）；**mockito 4.x 需 mockito-inline 的工件坑在 §3 L106**（静态方法小节内）；JUnit 4 差异在 §4 L201+。对"4.11.0 能否 mockStatic"要翻到 Mock 章节才能回答。
  2. SKILL L62 指针只写「见 06」无节号，第 0 步落点不精确（D7=9）；description 无 mockStatic/mockito-core 令牌（L5-20 仅 JUnit/Mockito 任务词），触发靠语义近似（D1=10）。
  3. 版本知识三处散布导致轻度重复阅读（§1 坐标版本 vs §3 工件坑 vs §4 差异表），D6=9。
- 扣分主因: 版本知识未集中，SKILL→06 的指针无节号，回答 R4 需要多跳拼装。

### Prompt R4（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 97/100
- 关键依据（≤3 条）:
  1. SKILL L61「（决定 mockStatic 能否用、是否需 mockito-inline，**见 06 §1 栈基线决策表**）」→ 06 §1 决策表 L10-12 一步命中：`mockito-core 5.x → mockStatic 直接用` / **`mockito-core 4.x 且需 mockStatic → 额外引入 mockito-inline（仅 mockito-core 不够）`**（对 4.11.0 正中）/ `< 3.4 → 不可用 → 重构注入或升级`——用户两问（版本差异 + mockStatic）一表全答。
  2. 06 L3 开篇即声明「§1 是第 0 步探测后的栈基线决策表——**版本差异唯一集中地**」，导航承诺明确；L25「坐标一律不写版本号」政策自洽（用户已有坐标，不受影响）。
  3. description L12 含 `mockStatic / MockedStatic、mockito-core` 令牌，用户消息原文即含 "mockito-core 4.11.0" 与 "mockStatic"——触发直接命中（D1=12）。
- 扣分主因: 仅 D8=11（范围边界节内容不变、与本 prompt 关联弱）。

### Prompt R5（JUnit 4 遗留项目 @RunWith，新写测试注意什么、与 JUnit 5 差异）
- 拿到的技能：版本 version1（A 组）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据（≤3 条）:
  1. SKILL L169「JUnit 4 项目的写法差异见 `references/06-tools-lean.md` §4」→ 06 §4 L201-214 差异表 6 行全覆盖（注解包名/`@Before`/`Assert`/`@Test(expected=)`/`@RunWith(Parameterized.class)`/`MockitoJUnitRunner`），指针节号精确。
  2. L214「同一模块禁止 JUnit 4 与 5 混用——生命周期注解不互通」直接回答"新写测试注意什么"；SKILL 铁律 3（L33 栈中立）+ §4 开头「跟随既有，不强升」给出姿态。
  3. S/A 表 L114「JUnit4 `@Before` 与 JUnit5 混用」行与 §4 呼应，防错到位。
- 扣分主因: 无明显失分；§4 与铁律 3 有少量重复（D6=11）。

### Prompt R5（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据（≤3 条）:
  1. JUnit 4 差异表移至 06 §1 末（L27-38「JUnit 4 差异表（探测到 `junit:junit` / `@RunWith` 时使用）」），内容与 v1 逐行等价；决策表 L13 行「`junit:junit`（JUnit 4）| 跟随既有，不强升 | 按本节末『JUnit 4 差异表』」形成表内路由。
  2. SKILL L168 指针「见 `references/06-tools-lean.md` §1 栈基线决策表」——差异表在 §1 内可达（一跳），且 §1 标题即"版本差异唯一集中地"，与 R4/R5 同入口。
  3. L38 保留「禁止 JUnit 4 与 5 混用」警示；SKILL 铁律 3 不变。
- 扣分主因: 无退步——两版得分相同属正常（内容等价、可达性等价）。

### Prompt R6（Service 内 MyBatis-Plus lambdaQuery().eq().one() 链式 + 工具类静态方法，复杂 Mock 范例）
- 拿到的技能：版本 version1（A 组）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据（≤3 条）:
  1. 06 L110-126「链式调用 / 参数对象 mock（MyBatis-Plus、JPA Query）」正中：wrapper 是被测方构造的参数对象不 mock、对 mapper 用 `any()`（L119），L126 再补 `ArgumentCaptor` 捕获防 `any()` 放过构造 bug——原则可平移到 `.one()` 链。
  2. 静态方法两节分置：L95-108「静态方法 mock（最后手段）」给 mockStatic 代码；L128-150「静态方法：重构为可注入实例」给 IdGenerator 注入范例 + L150「LocalDate.now()/UUID 常见误判」——两个问题各有答案。
  3. spy/doReturn（L156-168）、verify times（L170-177）、严格桩（L179-191）、@MockBean 区分表（L193-199）全部在位，坑无丢失。
- 扣分主因: 静态方法知识拆两节、mockStatic 用法（L95）排在"优先重构"理念（L128）之前，阅读顺序与决策顺序相反（D7=11）。

### Prompt R6（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 98/100
- 关键依据（≤3 条）:
  1. 06 L107-123 链式 wrapper 节逐行保留（any() 范例 L116 + ArgumentCaptor 补丁 L123），MyBatis-Plus 场景直接命中。
  2. L125-160 静态两节合并为「静态调用：先重构注入，够不着才 mockStatic」——标题即决策顺序，注入范例（L129-143）在前、兜底 mockStatic（L149-158）在后，L149 版本门槛经指针回 §1 决策表，一处不丢。
  3. rubric 点名的坑全部仍在且可发现：spy/doReturn L166-178、verify times L180-187、严格桩 L189-201、wrapper any()/ArgumentCaptor L109-123、try-with-resources L151-160——D5 满分。
- 扣分主因: 仅 D8=11（范围边界节与本 prompt 关联弱），无内容丢失。

### Prompt R7（第一次用 mockStatic mock IdUtil.getId()，注意事项、怎么不污染其他测试）
- 拿到的技能：版本 version1（A 组）
- D1: 10  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 94/100
- 关键依据（≤3 条）:
  1. 06 L97-104 mockStatic 完整范例（try-with-resources + `m.when(IdUtil::getId)`——与用户场景同款 IdUtil）；L106 版本门槛与工件坑一段全给：3.4+ / **4.x 需 mockito-inline** / 5.x 默认 inline；L107「必须 try-with-resources，否则静态 mock 泄漏到同线程其他测试」正答"怎么不污染"。
  2. SKILL S/A 表 L108 mockStatic 行 + L128-150「优先重构注入」给出前置建议（IdUtil 可改接口注入时别用 mockStatic）。
  3. description（L5-20）无 mockStatic 令牌，触发靠 "Mock/Mockito" 任务词近似（D1=10）。
- 扣分主因: 触发令牌缺失（description 无 mockStatic/MockedStatic）为唯一失分；正文一站式回答完整。

### Prompt R7（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 99/100
- 关键依据（≤3 条）:
  1. 06 L149-160 兜底 mockStatic：try-with-resources 范例（L151-158，含 IdUtil 同款）+ L160 泄漏警告原样保留；L125-127「先重构注入」前置建议与 L147 常见误判（能改调用点就不算够不着）齐备。
  2. 版本门槛与工件坑移至 §1 决策表 L10-12，§3 L149 显式指针「版本门槛与工件见 §1 决策表」——同文件一跳可达，知识无丢失（符合 rubric"丢了任何一个 → D5 扣分"的检查，未丢）。
  3. description L12 显式列出 `mockStatic / MockedStatic`——用户原话"第一次用 mockStatic"直接命中（D1=12）。
- 扣分主因: 仅 D8=11；§3→§1 一跳换取消除跨节重复，净收益为正。

### Prompt A1（对抗 · CI 80% 门禁配合 + 无 JaCoCo 不加插件的分支核对）
- 拿到的技能：版本 version1（A 组）
- D1: 11  D2: 8  D3: 7  D4: 3  D5: 4  D6: 9  D7: 8  D8: 11  D9: 1
- 该 prompt 小计: 62/100
- 关键依据（≤3 条）:
  1. **(a) 功能性缺陷**：05 L114 antipattern「✗ 把『覆盖率 ≥ 80%』写进 CI 当硬门禁 → ✓ 覆盖率作报告+趋势监控，关键模块设阈值，胶水代码豁免」——四选项套餐且姿态是"拆掉门禁"，无"团队既有门禁：照做 + 设计标准不降"的默认答案，与用户"我不想动这条门禁"正面冲突，agent 会给出去门禁化建议（D4=3，按对抗集特别规则重扣）。
  2. **(b) 摇摆**：SKILL L162「项目无 JaCoCo 时：人工核对分支表，**或按成本收益决定是否接入**」与 05 L60「仅当用户问……才提——普通设计用例不必主动推接入」互相矛盾；用户明说"不想往 pom 里加新插件"，DoD 岔路仍引导评估接入 → agent 可能推插件，违背用户诉求（D5=4、D9=1）。
  3. "人工核对分支表"（L162）无步骤（列什么、对照什么、怎么算过），(b) 的核对路径实际悬空（D3=7、D2=8）。
- 扣分主因: 覆盖率立场三处（SKILL DoD / 05 定位表 / 05 antipattern）互相打架，(a) 无配合姿态、(b) 无工具路径不可执行——典型误导 + 摇摆，按特别规则重扣。

### Prompt A1（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 96/100
- 关键依据（≤3 条）:
  1. (a) 05 L111 antipattern 改为两场景各一个默认：「团队既有此门禁：**照做，但设计标准不降**（四维度 + 分支盲区清零，不写凑数测试）；从零定策略：仅对『成本收益』矩阵重点测试象限设**分支覆盖**阈值，胶水/POJO 豁免」——正中 rubric 预期答案。
  2. (b) SKILL L161「无 JaCoCo → 读被测方法源码列分支清单逐分支对照已设计用例（设计时本就要数分支，默认路径不依赖工具）」+ 05 L36「盲区核对不依赖本工具……仅当用户问……才给接入方案」——不推插件、动作明确；05 L16 机械判据「Missed = 0 / 人工分支清单全勾」可核对。
  3. 05 L3-5 一句话立场定死（要求分支盲区清零、不要求百分比、JaCoCo 是手段不是目标），与 SKILL DoD、antipattern 三处口径统一（D9=4）。
- 扣分主因: 仅 05 L3-5 单段信息量大需细读（D6=11），无功能性缺陷。

### Prompt A2（对抗 · 非 Spring 项目要 AssertJ extracting 的依赖坐标）
- 拿到的技能：版本 version1（A 组）
- D1: 11  D2: 4  D3: 8  D4: 3  D5: 5  D6: 9  D7: 6  D8: 11  D9: 2
- 该 prompt 小计: 59/100
- 关键依据（≤3 条）:
  1. **指针悬空（功能性缺陷，重扣）**：SKILL L44「非 Spring 项目首次触发时按 `references/06` §1 引入 `assertj-core`」→ 06 §1 非 Spring 坐标块 L20-24 **只有 junit-jupiter / mockito-core 两条坐标**，L23 注释仅一句"……时才升级 AssertJ"；grep 全文件证实 version1 任何位置都没有 org.assertj 坐标——agent 被指到空处，须自行拼 groupId/artifactId（D4=3、D2=4）。
  2. 升级条件本身完整（SKILL L37-44"字段分组断言（同一逻辑组，如坐标 x/y/z）→ extracting().containsExactly()"，恰是用户场景），但"给坐标"这最后一公里断掉（D3=8）。
  3. 悬空指针还诱发臆造风险：agent 可能编版本号/坐标而不自知（D5=5）；SKILL 承诺与 06 落空构成事实上的不一致（D9=2）。
- 扣分主因: assertj-core 坐标指针悬空——被指向的位置查不到该坐标，按对抗集规则重扣 D4/D2。

### Prompt A2（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 9  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据（≤3 条）:
  1. 06 §1 L20-21 注释块内含完整坐标：`<dependency><groupId>org.assertj</groupId><artifactId>assertj-core</artifactId><scope>test</scope></dependency>`，且注释写明触发条件指回 SKILL 断言库策略——SKILL L43 指针落地兑现（D4=12、D2=12）。
  2. L25「坐标一律不写版本号：版本跟随项目既有；新项目取当前最新稳定」——版本策略显式，符合 rubric 预期（"版本跟随项目/取最新稳定"）。
  3. 小瑕疵（不构成缺陷）：description（L5-19）删掉了 v1 的「字段分组断言……升级到 AssertJ」触发句（对比 v1 SKILL L17-18），A2 用户原话含"字段分组断言/AssertJ"时 v2 触发只能靠"测一个方法/断言"语义通道，D1=9（v1 为 11）——诚实记入。
- 扣分主因: description 收窄后丢失 AssertJ/字段分组断言触发信号（D1=9），为该版本在此 prompt 的唯一失分。

### Prompt A3（对抗 · 500 行圈复杂度 40+ 祖传方法，重构第一步 + 锁行为标准）
- 拿到的技能：版本 version1（A 组）
- D1: 10  D2: 8  D3: 10  D4: 8  D5: 8  D6: 10  D7: 8  D8: 11  D9: 3
- 该 prompt 小计: 76/100
- 关键依据（≤3 条）:
  1. "第一步"可答：05 L97-104 特征测试路线（把当前实际输出录下来当期望值 → 小步重构 → 再补设计用例）完整且与 R2 共用；阈值也在行内——L108「严重超标方法（认知复杂度 **≥~30**）」。
  2. **但同句紧跟「见 `java-coding-guide-pro/references/12-complexity.md`」——跨插件文件，只装本技能的环境中不存在**：用户问"有没有判断标准"，agent 顺链去读会落空，判据的权威出处断掉（D4=8、D2=8、D5=8）。
  3. 圈复杂度 40+ 与"认知复杂度 ≥~30"口径不同，v1 无换算说明也无"祖传大方法"专门判读，D3=10。
- 扣分主因: 判据虽在行内但权威指涉指向不存在的文件，半自包含状态——按对抗集规则对"判据依赖不存在文件"扣 D4。

### Prompt A3（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 96/100
- 关键依据（≤3 条）:
  1. 05 L105 完全自包含：「认知复杂度 ≥~30 的方法判为『严重超标』，其重构同样要求『先特征测试锁现状，再拆解』——**阈值是机械判据，防止『觉得复杂』的主观摇摆**」——既给标准又给标准的用法，正答用户第二问。
  2. 05 L93-103 三步路线 + 切片策略（按成本收益矩阵挑最高风险单方法先闭环）完整回答"第一步该干什么"；L107 PowerMock/反射禁令防错。
  3. grep 证实 v2 全文 guide-pro 引用为 0，无任何断链点（D2=12、D9=4）。
- 扣分主因: 仅 D6=11（L105 与 L93-103 略有重叠）；圈复杂度/认知复杂度换算仍未显式（两版同），影响极小。

### Prompt A4（对抗 · 贴测试代码求 review，不提框架名）
- 拿到的技能：版本 version1（A 组）
- D1: 7  D2: 11  D3: 11  D4: 11  D5: 11  D6: 8  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 85/100
- 关键依据（≤3 条）:
  1. **D1 弱匹配**：description（SKILL L5-20）以任务词为主（unit test / JUnit / Mockito / 测试用例 / 怎么测），**无代码令牌通道**——prompt 代码里的 `@InjectMocks`、`@ParameterizedTest`、`@MethodSource`、`when(...)`、`assertEquals` 在 description 无对应信号；仅 L15「手写一堆重复 @Test」、L16「@MockBean 用于纯单测」与代码有微弱字面交集（且语义并不匹配——用户代码恰是合规的参数化写法）。触发只能靠 L6「评审……单元测试」对"review 这段测试"的语义近似（D1=7）。
  2. 触发后正文可用：S/A 表 L106-107（@Mock/@InjectMocks 默认与容器装配例外）、L108（AI 采信复核）、L112（@ParameterizedTest 推荐）、06 §3 verify/spy/严格桩——review 素材齐全（D3-D5 高）。
  3. description L9-13 价值论证散文（「核心：统一团队的测试规范……可溯源、可审计，而非每次碰运气。覆盖：……」）对触发无贡献、稀释令牌密度（D6=8，按 rubric A4 锚点扣）。
- 扣分主因: description 无代码令牌通道，纯贴代码场景触发靠运气；营销段落拖累密度。

### Prompt A4（同场景）
- 拿到的技能：版本 version2（A 组）
- D1: 12  D2: 11  D3: 11  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 94/100
- 关键依据（≤3 条）:
  1. description L9-12 显式代码令牌通道：「代码或 pom 中出现：……@Test / @BeforeEach / **@ParameterizedTest / @MethodSource**、**assertEquals** / assertThrows、**@Mock / @InjectMocks** / MockitoAnnotations.openMocks、mockStatic / MockedStatic、mockito-core」——prompt 代码五个关键令牌（@Mock/@InjectMocks/@ParameterizedTest/@MethodSource/assertEquals）全部直接命中（D1=12）。
  2. 无价值论证段落：description 只剩触发信号 + 核心默认一行 + 不适用声明，令牌密度高（D6=12，符合 rubric「无营销话术」锚点）。
  3. review 正文与 v1 相同（S/A 表 + 06 §3），触发后表现等价（D3-D5 与 v1 同分）。
- 扣分主因: 仅正文层面无专门"参数化测试 review 清单"（两版同），差异全在触发层。

---

## 差值表与结论

| Prompt | version1 | version2 | 差值（v2−v1） |
|---|---|---|---|
| R1 JaCoCo 接入 | 91 | 95 | +4 |
| R2 遗留代码补测 | 88 | 96 | +8 |
| R3 DoD/分支检查 | 84 | 95 | +11 |
| R4 栈基线导航 | 83 | 97 | +14 |
| R5 JUnit 4 差异 | 95 | 95 | 0 |
| R6 Mock 复杂场景 | 95 | 98 | +3 |
| R7 mockStatic 注意 | 94 | 99 | +5 |
| **回归集小计** | **630** | **675** | **+45** |
| A1 覆盖率立场 | 62 | 96 | +34 |
| A2 AssertJ 坐标 | 59 | 95 | +36 |
| A3 祖传大方法 | 76 | 96 | +20 |
| A4 触发令牌 | 85 | 94 | +9 |
| **对抗集小计** | **282** | **381** | **+99** |
| **总分** | **912** | **1056** | **+144** |

**一句话结论**：version2 整体更好（总分 1056 vs 912，+144），回归集 7 条无任何退步条目（R5 持平、其余 6 条均进步），对抗集 4 条因 version1 存在覆盖率立场摇摆（A1）、assertj-core 坐标指针悬空（A2）、判据外链断链（A3）、description 无代码令牌（A4）四类功能性缺陷被重扣而大幅落后；version2 唯一的小损失是 description 删去 AssertJ/字段分组断言触发句使 A2 触发略弱（D1 11→9），不影响其正文满分兑现。
