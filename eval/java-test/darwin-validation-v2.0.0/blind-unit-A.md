# 盲评报告 · java-unit-test（unit-A 组，R1-R5 + A1 + A2）

> 独立盲评：只依据两个快照的文本内容推演打分，不预判新旧。每条 prompt 对两版分别推演"agent 拿这版技能会给出的方案"后再打分。维度分值：D1-D8 各 12 分、D9 4 分，满分 100/prompt。

## 汇总表

| Prompt | version1 | version2 | 差值 (v2-v1) |
|---|---:|---:|---:|
| R1 等价类+边界值设计 | 92 | 97 | +5 |
| R2 决策表 | 96 | 96 | 0 |
| R3 状态机 | 96 | 96 | 0 |
| R4 Mockito 陷阱 | 97 | 97 | 0 |
| R5 覆盖率立场 + JaCoCo | 95 | 98 | +3 |
| A1 单测引入 H2/内嵌库（对抗） | 73 | 97 | +24 |
| A2 开发期接口验证路由（对抗） | 76 | 96 | +20 |
| **总分（700）** | **625** | **677** | **+52** |

**结论：version2 整体更好（677 vs 625）。** 回归集 R2/R3/R4 完全打平、R1/R5 v2 微胜（判据保留 + 内部一致性更佳）；差距主要由对抗集 A1/A2 拉开——version2 的"零基础设施"铁律与"接口级验证不写测试 + 激活门槛"边界在 version1 中无对应文本。

---

### Prompt R1（calcPrice：qty 1~99 越界抛 IAE / vip 8 折 / couponCode null/空=无券）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 路由表命中"纯计算/校验 → references/02"，agent 通读 02（含 calculateDiscountPrice 完整 9 用例示范）。
  2. 划等价类：qty 有效 [1,99] + 无效 `<1`/`>99`（抛 IAE）；vip true/false 两行为类；couponCode null/空串=无券（同一处理分支可合并）、有值=查券表类。
  3. 边界值取 qty 0,1,99,100（闭区间四点），字符串边界套 02 的边界表（`""`/`null`）；有效类组合成正向用例，无效类单独测（一次只让一个输入非法）。
  4. 计数给"3~8 有效/边界 + 每无效类 1 反向，共 5~10"；但 SKILL 路由表写"典型 3~6"，与 02/铁律 2 的"3~8"打架，agent 需自行裁决。
  5. 券表查询按 Mock 边界 mock 掉；BigDecimal 断言两版都未提示 equals 的 scale 敏感性（共同盲点）。
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 10  D6: 9  D7: 11  D8: 12  D9: 3
- 小计: 92/100
- 关键依据：
  1. `references/02-equivalence-and-boundary.md` L23（闭区间必测 min-1/min/max/max+1）、L27-33（边界值表）、L104（计数 3~8）——判据齐全。
  2. 同文件 L44-96 为 ~50 行完整示范（教学性，判据已被表格承载）→ D6 拖累。
  3. `SKILL.md` L76 路由表"3~6" vs 铁律 2（L32）与 02 L104 的"3~8"——同版本内口径冲突 → D9/D4 扣。
- 扣分主因：计数口径内部矛盾（3~6 vs 3~8）+ 完整范例占 02 近半篇幅，属可删教学内容；BigDecimal 断言陷阱两版共同缺失（D5 封顶 10）。

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 路由表命中"references/02 设计方法速查"等价类节，直接取判据：按行为切分、一类一代表、无效类比有效类多。
  2. 边界值表逐字保留（数值区间四点 / 字符串 `""`/null/maxLength+1 / 高风险域金额优先）——qty 0/1/99/100 与 couponCode null/"" 全覆盖。
  3. 计数"3~8 有效/边界 + 每无效类 1 反向（通常共 5~10）"与 SKILL 路由表 L73"3~8"一致，无歧义。
  4. "两个输入的无效类单独测"、浮点 `==` 反模式（改 delta 或整数单位）均在，产出与 version1 等价。
- D1: 12  D2: 11  D3: 12  D4: 12  D5: 10  D6: 12  D7: 12  D8: 12  D9: 4
- 小计: 97/100
- 关键依据：
  1. `references/02-design-methods.md` L9-12（划分规则 + 计数）、L14-23（边界值表逐字保留）、L30（一次一个非法输入）。
  2. `SKILL.md` L73 路由表"3~8"与 02 L11 一致，无 v1 的口径冲突。
  3. 02 为等价类/决策表/状态机合并文件，R1 场景需跳过后两节——D2 轻微让位于 v1 的专文件。
- 扣分主因：合并文件带来少量无关内容（D2-1）；BigDecimal 断言陷阱未点名（D5-2，与 v1 同）。

---

### Prompt R2（满减+折扣券叠加：newUser × over100 × stackable，8 种组合都要测吗）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 路由表命中"多条件组合 → references/03"，agent 拿到与 prompt 场景几乎同构的完整示范（会员/满100/有券，8 列→化简 5 列）。
  2. 先穷尽 3 条件 × 2 值 = 8 列；观察动作相同的列合并、无关条件标"—"；化简后列数 = 用例数，"不漏不重"。
  3. 明确回答"8 种不必都测"——动作相同的合并；但"不过度化简"，可顺手补一列确认无关条件确实被忽略。
  4. 落地：每列一个 `@Test` 或 `@ParameterizedTest`+`@CsvSource`，不塞单个测试。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 11  D6: 10  D7: 11  D8: 12  D9: 4
- 小计: 96/100
- 关键依据：
  1. `references/03-decision-table.md` L33-42（8 列原始表）、L44-57（化简为 5 列、"—"无关项）、L75-79（化简三规则含不过度化简）。
  2. L86-91 antipatterns（忘化简 / 只测全Y全N / 不可能组合）直接命中"8 种都要测吗"。
- 扣分主因：完整示范 ~40 行属教学内容（判据已由化简规则承载），D6 轻度拖累；对"漏"与"重"的判据无实质缺失。

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 路由表命中 02 §决策表；判据（组合语言信号、组合数 ≥4）、结构（列=用例）齐备。
  2. 应用化简规则：动作相同且某条件一列 Y 一列 N → 无关，合并标"—"；动作不同的列保留——得出"先列 8 列再合并，化简后列数=用例数"。
  3. 反例（`discount = price*rate` 不组合 → 等价类）帮助确认本 prompt 确属决策表。
  4. 落地同 v1（每列一 Test 或 CsvSource）；"不过度化简 + 顺手补一列验证无关项"保留。
- D1: 12  D2: 11  D3: 12  D4: 12  D5: 11  D6: 12  D7: 11  D8: 12  D9: 4
- 小计: 96/100
- 关键依据：
  1. `references/02-design-methods.md` L35-37（判据 + 反例）、L39（列数=用例数）、L41-44（化简三规则，含"顺手补一列确认无关条件"）。
  2. L46（落地方式）、L50-53（antipatterns 三条与 v1 实质等价）。
- 扣分主因：合并文件定位到决策表节需多扫两屏（D2-1）；无 8→5 的分步演示（D4 由规则的机械性补足，不另扣）。

---

### Prompt R3（退款状态机：PENDING_REVIEW → APPROVED → REFUNDING → SUCCESS/FAILED，非终态可 CANCELLED）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 路由表命中"有状态对象 → references/04"，拿到订单状态机完整示范（与退款状态机同构）。
  2. 0-覆盖列合法迁移：7 条边（PENDING_REVIEW→APPROVED / →CANCELLED；APPROVED→REFUNDING / →CANCELLED；REFUNDING→SUCCESS / →FAILED / →CANCELLED），每条断言终态 + 迁移动作。
  3. 非法迁移全部拦截：跳跃转移（PENDING_REVIEW 直接 REFUNDING 等）、重复操作、三终态（SUCCESS/FAILED/CANCELLED）发起任何操作全拒绝——用全矩阵速查表逐格打勾。
  4. 明确重点在非法迁移（"bug 几乎都不在正常流转"）；退款涉及钱 → 按 N-switch 节加测一条完整链路一致性。
  5. 落地有 3 个现成 `@Test` 代码样例可仿写。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 9  D7: 11  D8: 12  D9: 4
- 小计: 96/100
- 关键依据：
  1. `references/04-state-transition.md` L33-42（0-覆盖合法迁移表）、L44-52（非法迁移表）、L54-56（终态验证）、L97-107（全矩阵"每个 ✓/✗ 都是用例"）。
  2. L81-88（N-switch：钱相关加测完整链路）直接命中"退款"场景的重点判断。
  3. L60-79 三个 Java 代码样例属教学示范 → D6。
- 扣分主因：代码样例与状态图 ASCII 属可删教学内容（~40 行），判据（必测三件 + 矩阵 + N-switch 条件）本身无缺失。

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 路由表命中 02 §状态迁移；"必测三件"直接给出结构：合法迁移 0-覆盖 / 非法迁移拒绝 / 终态全拒绝。
  2. 同样列 7 条合法边 + 全部非法跳跃 + 三终态矩阵拒绝；全矩阵速查表逐字保留（每个 ✓/✗ 都是用例）。
  3. 重点判断同 v1："bug 几乎都不在正常流转，而在非法转移/终态泄漏"；枚举实现的 `canTransitTo()` 全矩阵 `@ParameterizedTest` 建议保留。
  4. 退款涉及钱 → N-switch 条件（钱相关/并发敏感）保留，加测完整链路。
  5. 落地走 03 §2 映射表（合法 `assertEquals(终态,…)` / 非法 `assertThrows(IllegalStateException,…)`）。
- D1: 12  D2: 11  D3: 12  D4: 11  D5: 12  D6: 12  D7: 11  D8: 12  D9: 4
- 小计: 96/100
- 关键依据：
  1. `references/02-design-methods.md` L59-63（必测三件，含防重复支付/防僵尸复活/防跳跃/防终态回退）、L65-74（全矩阵速查表逐字保留）。
  2. L76-77（枚举 canTransitTo 全矩阵 + N-switch 触发条件）保留。
  3. `references/03-tools-lean.md` L48-49（状态机合法/非法迁移的落地断言写法）。
- 扣分主因：无可仿写代码样例（映射表承载落地写法，D4-1）；合并文件定位成本（D2-1）。判据无缺失，与 v1 产出等价。

---

### Prompt R4（Mockito 三问：spy stub 触发真实方法 / verify 调两次变红 / 4.x mockStatic 依赖）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. ① 命中 06 §3 坑①：对 spy 用 `when().thenReturn()` 会先执行真实方法——必须 `doReturn().when(obj)`"do 先行"；附 ✗/✓ 代码对照。
  2. ② 命中坑②：`verify(repo).save(order)` 等价 `times(1)` 且是"恰好"非"至少"——被调两次即红；给 `never()`/`atLeast(2)` 语义差。
  3. ③ 命中 §1 栈基线表：`mockito-core` 4.x 且需 mockStatic → 额外引入 `mockito-inline`（仅 mockito-core 不够）；5.x 起才默认 inline。
  4. 顺带提示 mockStatic 必须 try-with-resources（S 级表 + §3）。
- D1: 12  D2: 11  D3: 12  D4: 12  D5: 12  D6: 12  D7: 11  D8: 12  D9: 4
- 小计: 97/100
- 关键依据：
  1. `references/06-tools-lean.md` L165-178（spy 坑 ✗/✓ 代码 + "do 先行"规则）、L180-187（verify times 恰好语义）。
  2. 同文件 L11（栈基线表"4.x + mockStatic → mockito-inline"）。
- 扣分主因：SKILL 的 Mock 边界（L123）未点名"spy/doReturn"关键词，agent 需进 06 §3 后才能定位（D2-1）；三问本身全部直接命中，几乎无失分。

- 拿到的技能：版本 version2
- 推演产出要点：与 version1 逐条相同——
  1. ① 03 §3 坑① doReturn/doThrow"do 先行"；② 坑② verify 默认 times(1) 恰好语义；③ §1 表 4.x → `mockito-inline`。
  2. SKILL Mock 边界额外点名"spy/doReturn"指针，发现路径更短。
  3. mockStatic try-with-resources 约束在 S 级表 L103 与 §3 兜底代码双处保留。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 11  D8: 12  D9: 3
- 小计: 97/100
- 关键依据：
  1. `references/03-tools-lean.md` L162-176（三坑与 v1 06 逐字相同）、L11（4.x → mockito-inline）。
  2. `SKILL.md` L119（Mock 边界明确列出"spy/doReturn"指针）→ D2 优于 v1。
  3. 同文件 L22 注释"ArchUnit 仅'架构守护询问'（见 SKILL.md）触发时引入"——但 v2 SKILL 已无该节，断链 → D9-1。
- 扣分主因：03 §1 的 ArchUnit 注释指向 SKILL 中已不存在的"架构守护询问"节（死链，D9-1）。

---

### Prompt R5（组长要求行覆盖 ≥80% 挂 CI 门禁，现在 62%；项目还没接 JaCoCo）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 路由表"写到什么程度算够 → references/05"；立场：覆盖率是反向诊断不是目标——分支盲区清零为硬项，不设百分比；80% 行覆盖既不必要（测 getter 可凑）也不充分（`if(x>0)` 跑 x=5 即"行覆盖"）。
  2. 对"要求合理吗"：antipattern 给出双分支答案——团队既有门禁：照做但设计标准不降；从零定策略：仅对"重点测试"象限设分支覆盖阈值，胶水/POJO 豁免。
  3. JaCoCo 接入：plugin XML（prepare-agent + report），版本显式写现场查最新（留空会告警，spring-boot-parent 不管 jacoco 版本）；坑：report 绑 test phase 时测试失败不出报告 → 改 verify 或 `mvn jacoco:report`。
  4. 辅以四种粒度表（行/分支/路径/MC-DC）论证"以分支覆盖为口径"。
- D1: 12  D2: 11  D3: 12  D4: 12  D5: 11  D6: 10  D7: 11  D8: 12  D9: 4
- 小计: 95/100
- 关键依据：
  1. `references/05-coverage-and-quantity.md` L5（一句话立场）、L38-58（JaCoCo XML + 版本坑 + `mvn test` 后看报告路径）。
  2. 同文件 L60（"测试不过时报告不生成"坑 + verify 逃生门）、L112（80% 一刀切门禁的双分支处理）。
  3. L8-16 四粒度表 + L64-73 成本收益 ASCII 矩阵——对本 prompt 在题内，但部分内容与 SKILL DoD 节复述 → D6-2。
- 扣分主因：立场文本在 SKILL DoD、05 L5、05 antipatterns 三处重复表述（D6-2）；发现路径需经路由表二跳（D2-1）。

- 拿到的技能：版本 version2
- 推演产出要点：与 version1 相同的三层答案——
  1. 立场（01 根文件，必读即见）：分支盲区清零为 DoD 硬项、不设百分比、以分支覆盖（C1）为口径、不追求路径/MC-DC。
  2. 80% 门禁双分支处理逐字保留（既有门禁照做不降标准 / 从零定策略仅重点象限设分支阈值）。
  3. JaCoCo XML 与两个坑（版本显式写 + 失败不出报告的 verify 逃生门）完整保留，`target/site/jacoco/index.html` 路径在。
  4. 成本收益矩阵改表格形式保留，"重点/轻量"清单在——回答"62%→80% 期间往哪补"有依据（先补重点象限盲区而非全量凑数）。
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 11  D6: 12  D7: 11  D8: 12  D9: 4
- 小计: 98/100
- 关键依据：
  1. `references/01-test-design-foundations.md` L26-30（立场 + 反向校验流程）、L32-48（JaCoCo XML + 两坑 + 报告路径）。
  2. 同文件 L81（"✗ 覆盖率 ≥80% 写进 CI 一刀切 → ✓ 双分支处理"）——prompt 第一问的直接答案。
  3. 覆盖率内容并入"设计前必读"根文件，快速入门表 L57 直接点名"覆盖率立场 + DoD 锚点"→ D2 优于 v1 的专文件二跳。
- 扣分主因：四粒度对比表压缩成一行结论（决策所需信息保留，仅"行 vs 分支"的教学展开没了，不构成扣分项）；实质失分仅 D5-1（无新增坑）与 D7-1。

---

### Prompt A1（对抗 · InventoryService 依赖 JPA Repository + RedisTemplate，想给单测配 H2 + embedded-redis 跑真的）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 技能正常触发（"写单测"）；Mock 边界（SKILL L122）主张"只 Mock 外部依赖（DB/RPC/时间/第三方）"——JPA 与 RedisTemplate 属外部依赖，应 `@Mock` + `@InjectMocks`，这条正确路径存在（06 §3 标准样例）。
  2. 但用户明示"心里没底，测不出真的存取，帮我配 H2 和 embedded-redis"——全技能**无任何一条规则禁止为单测引入 H2/内嵌库**：铁律只有设计优先/最小充分/栈中立；S 级表无对应行；不适用清单（description L19-20、06 §4 L215）只列 @SpringBootTest 全量上下文/Testcontainers/REST Assured/WireMock——**H2 与 embedded-redis 均不在列**。
  3. "H2 算不算集成测试"在本版口径下模糊：H2 直连不起 Spring Context，不命中任何不适用条款——agent 很可能顺着用户要求给出 H2 + embedded-redis 的依赖坐标与配置（这正是 rubric 预期的失败形态：单测变集成测试、毫秒级变秒级）。
  4. 即使 agent 选择 mock 路线，也没有"必须真实 Redis 语义才成立的断言 → 集成测试"的升级路由文本支撑其拒绝用户的理由。
- D1: 11  D2: 11  D3: 8  D4: 8  D5: 4  D6: 11  D7: 10  D8: 6  D9: 4
- 小计: 73/100
- 关键依据：
  1. `SKILL.md` L19-20（description 不适用清单无 H2/内嵌库）、L29-33（三条铁律无零基础设施）——拦截文本缺失的实证。
  2. `references/06-tools-lean.md` L213-219（§4 范围边界枚举的排除项同样不含 H2/embedded-redis）。
  3. `SKILL.md` L122-123（Mock 边界给出正确替代方案，是本版唯一的正确牵制力）。
- 扣分主因：功能性地未能拦截——用户推着走时，技能对"H2/内嵌库"零覆盖，给出接入步骤且未拦截 = D5 重扣（4）；范围边界恰在本场景存在漏洞（D8-6）。

- 拿到的技能：版本 version2
- 推演产出要点：
  1. 铁律 3（SKILL L39）"零基础设施：纯单测不起 Spring、不引 Testcontainers / **H2 / 内嵌库**"——第一屏即拦截；description（L5-8）与正文开头（L31）同口径。
  2. S 级表 L104 专项："✗ 为跑单测引入 Testcontainers / H2 / 内嵌库 → ✓ 纯单测零基础设施；需要真实依赖才能断言的行为（SQL 实际执行/迁移/缓存语义）→ java-integration-test（激活后）"——精确命中 RedisTemplate 的"缓存语义"。
  3. 给出的正确方案：`@Mock InventoryRepository` + `@Mock RedisTemplate` + `@InjectMocks InventoryService`，验证的是 InventoryService 自己的扣减逻辑（03 §3 标准样例 + Mock 边界）。
  4. 升级路由明确：若断言依赖真实 Redis 语义（过期/序列化）→ 属集成测试，明示或确认后由 java-integration-test 处理，不混进单测。
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 12  D7: 11  D8: 12  D9: 3
- 小计: 97/100
- 关键依据：
  1. `SKILL.md` L39（铁律 3 点名 H2/内嵌库）、L104（S 级表专项行，含"缓存语义 → integration 激活后"）。
  2. `SKILL.md` L5-8（description 开篇即"不起 Spring Context、不起容器、零测试基础设施"）+ L145（版本与范围的注解分界）。
  3. `references/03-tools-lean.md` L58-74（标准注入式 Mock 样例，替代方案可直接照抄）。
- 扣分主因：仅两处轻微失分——RedisTemplate 的 stub 细节（opsForValue 链式）无专项样例（D4-1）；03 §1 的 ArchUnit 死链注释在本文件内（D9-1）。拦截本身无懈可击。

---

### Prompt A2（对抗 · 开发期刚写完 POST /orders，该写 @SpringBootTest(RANDOM_PORT) 真调一下验证吗）

- 拿到的技能：版本 version1
- 推演产出要点：
  1. 技能触发后能识别"@SpringBootTest 属不适用"（description L19-20）——不至于在 unit 技能内起草该测试。
  2. 但处置止步于"建议切换 java-integration-test 技能"（06 §4 L219"用户问及时……建议切换"）——这等于**背书去写这个重型测试**：没有"开发期接口验证不写测试"的口径，没有"明示或确认后激活"的门槛，也没有"手动验证"的替代方案。
  3. 对"参数校验对不对"这一半问题无答案：参数校验逻辑若在被测方法内，本可走纯单测；v1 文本无此路由，agent 大概率整体外推给 integration。
  4. 预期行为 = rubric 所述"含糊路由"：把用户送往重型测试而非拦截，测试久过开发的文本根源未被堵住。
- D1: 10  D2: 11  D3: 7  D4: 7  D5: 8  D6: 11  D7: 10  D8: 8  D9: 4
- 小计: 76/100
- 关键依据：
  1. `SKILL.md` L19-20（不适用清单仅"→ java-integration-test"一句，无激活条件、无开发期口径）。
  2. `references/06-tools-lean.md` L219（"建议切换"——对本 prompt 是放行而非拦截）。
  3. 全文（SKILL + 6 refs）无"接口级验证/手动验证/RANDOM_PORT"任何相关文本。
- 扣分主因：路由不含激活门槛与开发期手动验证口径，倾向直接放行起草 @SpringBootTest 接口测试（D3/D4/D8 三处失分）——对抗锚点认定的功能性缺陷。

- 拿到的技能：版本 version2
- 推演产出要点：
  1. description L19-21 直接作答："接口级验证（接口通不通）**不写测试**、不属本技能范围；需要真实依赖断言 / 可重复回归的重型测试（Testcontainers / E2E）→ java-integration-test（**明示或确认后激活**）"；正文开头 blockquote（L33）同口径复述。
  2. agent 的回答形态：开发期不写 @SpringBootTest(RANDOM_PORT)——"通不通"用项目既有接口工具手动验证即可；明确不主动起草接口测试。
  3. 升级有门槛：确需可重复回归的真实接口测试 → 与用户确认后走 java-integration-test，不是无条件切技能。
  4. DoD 注（L137）补刀："三条全勾即判完成——开发期不以'还没写集成/接口测试'为由继续加测试"，堵住"顺手多写"的口子。
- D1: 12  D2: 12  D3: 11  D4: 11  D5: 11  D6: 12  D7: 11  D8: 12  D9: 4
- 小计: 96/100
- 关键依据：
  1. `SKILL.md` L19-21（description 边界三要素：不写测试 / 手动域 / 激活门槛）、L33（正文开头 blockquote）。
  2. `SKILL.md` L137（DoD 后注：开发期不以未写接口测试为由加测）。
  3. `SKILL.md` L145（与 integration 的边界 + "明示或确认后激活"复现，口径一处定义多处一致）。
- 扣分主因："手动验证用什么工具"（curl/Swagger 等）未落成具体建议，依赖 agent 自行补白（D3-1、D4-1）；"参数校验对不对"若指 Bean Validation 注解行为，单测侧未给切片归属提示（属 integration 的 @WebMvcTest 域，本技能只说不属己，D5-1）。

---

## 裁定与关键判据

**整体更好的版本：version2（677/700 vs 625/700，+52）。**

三条最关键判据：

1. **A1 拦截力（单 prompt 差 +24，本轮最大分歧点）**：version2 在三处落同一口径——铁律 3（`SKILL.md` L39 点名 "Testcontainers / H2 / 内嵌库"）、S 级表专项行（L104，含"缓存语义 → integration 激活后"）、description 开篇（L5-8"零测试基础设施"）；version1 的不适用清单（description L19-20、`06` §4 L213-219）通篇不含 H2/embedded-redis，也无零基础设施铁律——用户明示要配 H2 时无任何拦截依据，属 rubric 定义的"给了接入步骤且未拦截"功能性缺陷（D5=4、D8=6）。

2. **A2 路由门槛（+20）**：version2 有"接口级验证不写测试 + 重型测试明示或确认后激活"的完整边界（description L19-21、正文 L33、DoD 注 L137、范围节 L145 四处一致）；version1 只有"→ java-integration-test"的单句外推（且 `06` L219 主动"建议切换"），等于放行起草 @SpringBootTest 接口测试——正是本轮要消灭的行为。

3. **回归集不退步 + 一致性更优**：R2/R3/R4 两版完全打平（决策表化简规则、状态机必测三件与全矩阵、Mockito 三坑与栈基线表在 version2 的 `02`/`03` 中逐字或近逐字保留）；R1/R5 version2 微胜并非因短，而是 version1 自身有口径冲突（SKILL 路由表"3~6" vs 铁律 2/`02`"3~8"，D9-1、D4-1）且覆盖率立场三处复述（D6）——version2 统一为 3~8 并单点定义。同时记录 version2 自身一处瑕疵：`references/03-tools-lean.md` L22 的 ArchUnit 注释指向 SKILL 中已不存在的"架构守护询问"节（死链，已在 R4/A1 的 D9 各扣 1）。
