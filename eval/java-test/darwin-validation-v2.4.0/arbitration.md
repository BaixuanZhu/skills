# 仲裁报告 · darwin-validation-v2.4.0

> 独立仲裁。证据仅取 `snapshots/`、`mutation-results.json`、`rubric.md`、`fixture/` 源码；测试名/行号/命令/引文按原文逐一核对。不依据文件内自述标签推断实验组来源，S1–S4 仅按测试名/行号与 mutation 记录锚定。

## 1. 引用真实性核对

### 1.1 mutation ↔ 快照映射（全部吻合，两盲评 M=30/30 正确）

| mutation tail 点名 | 对应快照行号（断言行） | Tests run | 判定 |
|---|---|---|---|
| `$QuotePricing.thresholdUsesCompareToNotEquals:131`、`$QuoteValidation.nonPositiveQuantityThrowsIllegalArgumentException:66`、`$AllocateRounding.negativeHalfCentRoundsAwayFromZero:302` | S1/PricingServiceTest.java 131/66/302 | 33 = 9+9+2+5+8 | 一致 |
| `quote_roundsHalfUpToTwoDecimals:110`、`quote_throwsOnNonPositiveQuantity:153`、`allocate_roundsUp:195`、`allocate_roundsHalfUpOnTie:204` | S2 110/153/195/204 | 27 | 一致 |
| `quote_roundsHalfUpToTwoDecimalsAfterDiscount:120->assertAmount:47`、`…WithoutDiscount:130->assertAmount:47`、`allocate_roundsHalfUpAtMidpoint:188->assertAmount:47` | S3 120/130/188 → assertAmount:47 | 27 | 一致 |
| `exactlyAtDiscountThreshold_appliesDiscount:117`、`zeroQuantity_throwsIllegalArgumentException:73`、`quantityOne_returnsUnitPrice:170`、`rounding_halfUpRoundsUp:236` | S4 117/73/170/236 | 24 = 14+10 | 一致 |

M1–M4 四组记录全部 `killed: true`、baseline `exit_code 0`。失败值与用例断言吻合（S1 M3 `expected: 90.00 but was: 90` 对 `isEqualTo(new BigDecimal("90.00"))`；S4 M3 `12.34/12` 对 `quantityOne`、M4 `0.03/0.02` 对 `rounding_halfUpRoundsUp`）。

### 1.2 报告引文核对（抽样全过，无虚构）

- S2 反证：`>= 0`→`> 0` 后 `expected: 90.00 but was: 100.00`（t2 同目录 t1:70）、scale 突变 `expected: 0.67 but was: 0.667`、`expected: 2 but was: 3`（t1:71）、恢复后 27 全绿（t1:62）——A/B 引用属实。
- S3 反证：`PricingService.java:35` `>= 0`→`> 0`、`Tests run: 27, Failures: 1` 点名 `quote_appliesDiscountExactlyAtThreshold:110->assertAmount:47`、md5 `0a436cd1…`（t1:43-47）——属实。
- S4 反证：`expected: 90.00 but was: 100.00`、`Tests run: 14, Failures: 1`、sha256 `d2e4cf41…`（t1:64-74）——属实。fixture 核对：`PricingService.java:35` `>= 0`、`:48` `divide(..., 2, ...)`、`OrderService.java:24-27` exists-then-insert、`:18-23` 入参校验，与引文逐行相符。
- T2 引文：S1「约束异常/业务异常」（t2:36）、S2「禁止测试级 @Transactional」「必须实际 insert 同一 orderNo 两次」「不执行≠通过」（t2:26/27/54）、S3「若只测 service 层二次调用，属假绿」（t2:19）、S4「TOCTOU 竞态」「没有任何库存读写」「BUILD SUCCESS 不是执行证据」（t2:27/76/56）——均属实。

### 1.3 引用/记账偏差（4 处）

1. B·S3 T2 X−1 称「未展开…独立连接读终态机制」——**不实**：S3 t2:23「（用新连接/新事务独立读回）」、t2:26「以独立查询确认最终状态」已写明。
2. A·S4 T1 F−3 称「M3 类 scale 变异在这些点上会假绿」——**过头**：mutation 数据显示 M3 实际被 `quantityOne`（12.34→12）等杀死；仅 `exactlyAtDiscountThreshold`（90.00→90，compareTo 相等）在纯值断言下真会假绿。扣分方向成立（scale 合同未钉死），论据不准。
3. B·S2 T2「6 项移交真库清单」——实为 5 项盲区 + 1 项 failsafe 配置前提（t2:49-54）。
4. 记账不完整：A·S1 的 T1-F（24/25）与 T2-G（27/30）扣了分但正文未列扣分点；B·S1 同有 G=27 未列。

## 2. 分差定性（严度差 vs 误判）

| 分歧 | A | B | 定性 | 仲裁 |
|---|---|---|---|---|
| `isInstanceOf` vs `isExactlyInstanceOf`（S2/S3 F） | 不扣 | 各 −1 | 严度差（B 偏严） | 不扣：锚点「异常断具体类与消息」由 `isInstanceOf(IllegalArgumentException)+hasMessage` 满足 |
| S3 C「核对仅一句话」 | 满分 | −1 | 严度差 | 可不扣：S3 t1:29 一句已含分支+等价类双核对；S2 的逐项版是加分形态 |
| S4 C「等价类未核对」 | 满分 | −1 | **误判（A 偏松）** | 应扣：S4 t1:37 仅分支核对，全文无等价类核对，半份说明 |
| S3 T2 L「未指派分支矩阵归单测层」 | −1 | 满分 | 严度差（A 偏严） | 不扣：锚点是「不塞集成层」，t2:16「不铺分支矩阵」已满足 |
| S3 T2 X | 满分 | −1 | **误判为主（B）** | 基本不扣：failsafe+verify、结构化断言、判红（t2:26/30/37）齐备；「独立连接」论据不实 |
| S3 T2 G | 29 | 30 | 严度差（A 偏严） | 30：「须用户确认后下一轮才动手」正中 G 锚点 |
| S1 T2 R | 8 | 10 | 内容对、归维可议（A） | 维持扣分：S1 t2:26 预设「真实 Spring 上下文」（fixture 无 Spring）且未披露库存缺口（见 §3.3）；B 漏 |
| S1 T1 C | 14 | 15 | **误判（B）**＋A 偏松 | 应 12–13：S1 报告全文无分支/等价类核对说明 |
| S1 T1 F | 24 | 25 | 混合 | 应 23–24：3 处桩值恒等于期望（§3.1）；B 满分偏松，A 方向对但未记账 |
| S3 T1 F | 25 | 23 | **误判（A 偏松）** | 应 24：S3 也有 99.99→99.99 恒等桩，A 在 S2/S4 都扣、唯 S3 没扣；B 多扣的 isInstanceOf −1 剔除 |
| S4 T1 R「评审口径术语」 | 10 | 9 | 严度差（B 偏严） | 10：R 锚点为准确/不越界/区分反证语义，t1:13 自注未违反 |
| G 对「明示，直接开始」扣 2–3（S1/S2/S4） | 扣 | 扣 | 一致、略偏严 | prompt 明示「数据库唯一约束真的拦住」的 DB 语义目标，「补集成测试」近直读而非纯推断；口径一致，不影响排序 |

## 3. 两盲评共同漏掉的问题

1. **S1 的桩值恒等于期望（3 处）双双未点名**：`belowThresholdNoDiscount`（stub 19.99、qty 1、断言 19.99，PricingServiceTest.java:103-110）、`stubPerSku`（10.00→10.00、20.00→20.00，:218-230）——透传桩值即绿。A 在 S2/S4、B 在 S2/S3/S4 均使用「桩值不恒等于期望」锚点，唯 S1 缺席。
2. **S2/S3 报告绝对化声明被自家用例反证，均未按 R「不夸大」评**：S2 t1:34「桩值与期望值不恒等…实现改坏必红」（被 20.00→20.00、99.99→99.99 反证）；S3 t1:20「桩值与期望值不重合」（被 99.99→99.99 反证）。两盲评 R 均给满分。
3. **库存缺口口径未一致执行**：fixture `OrderRepository` 仅 `exists/insert`（OrderRepository.java:5-8），「库存恢复」在被测类上无落点。仅 S4 发现并披露（t2:76「特性 B 只能定设计、落不了代码」）。S1 直接设计 `place_insertFails_thenInventoryRestored`、S2 断言清单含「库存未扣」（t2:50）、S3 设计 B1/B2（库存 N→N-k），三者均未发现缺口；A 只对 S1 扣、B 全未按此扣，S2/S3 该扣未扣。
4. **S1 隔离方案自相矛盾未被点破**：S1 t2:46 提议「每用例事务回滚」，正落入测试级事务假绿陷阱（回滚断言恒真），与其用例 2「库存回到初值」冲突（须独立连接读终态）。B 仅以「未提 @Transactional 陷阱」带过（并误写「未提 failsafe」——S1 t2:33/45 明确写了 failsafe/verify），A 未提。
5. **负数舍入口径**（次级）：S3、S4 均无负数金额/舍入方向（HALF_UP 远离零）用例，S1 的 `-0.025→-0.03` 为四份唯一覆盖。B 仅对 S4 点了此问题、未对 S3 同口径扣分，A 两处均未点。

## 4. 仲裁后排序（不涉组别来源）

**T1：S2 与 S3 并列 > S4 > S1**（仲裁分带：S2/S3 96–98，S4 94–96，S1 85–88）
- 并列依据：S2 唯一给出分支+等价类逐项核对（C 最强），但 3 处缺 scale 断言、2 处恒等桩、报告「不恒等」夸大；S3 的 `assertAmount` 统一值+scale、桩 10.999→11.00 防透传、恒等桩仅 1 处（F 最强），但核对说明只一句话。修正 A 的 S3 F 满分、B 的 isInstanceOf 扣分与 S3 C 扣分后同带，不足以排序。
- S4 第三位次两盲评一致：精确 `withMessage`、sha256 级反证是亮点；3 处缺 scale 断言、等价类核对缺失、桩 12.34 恒等压低 F/C。
- S1 垫底明显（两盲评位次一致）：无「改坏→红→绿」反证且未披露、把区分性验证命名为「反证」、无核对说明、3 处恒等桩；`isExactlyInstanceOf`、equals+hasScaleOf、负数方向等细节拉不回 V/C 缺口。

**T2：S4 ≥ S2 > S3 > S1**（仲裁分带：S4 97–98，S2 96–97，S3 94–96，S1 83–86）
- 两盲评 T2 排序完全一致（A 98/97/94/84，B 98/97/95/86），仲裁维持。
- S4 微先于 S2：独有库存缺口发现 + TOCTOU 定性 + 按路径分列的移交表；S2 的测试级 `@Transactional` 陷阱、绕过 exists 直插、「不执行≠通过」同等有力并有盲区清单，两者同带。
- S3 第三：A1「exists 短路假绿」识别到位，但三条路径缺「本地实库」（S2/S4 均有），且库存缺口未发现。
- S1 垫底：`place_duplicateOrderNo` 走 `place` 被 `exists` 短路、打不到约束层；「库存恢复」落不了地未披露；预设「真实 Spring 上下文」；「每用例事务回滚」隔离与其回滚断言自相矛盾。

**误差总评**：两盲评无虚构的测试名、命令或 mutation 结果；分差 ≤3 的单项全部落在严度、记账、漏判三类。排序仅在 T1 的 S2/S3 间摇摆，仲裁判并列；S4/S1 的 T1 位次与全部 T2 位次两盲评一致。
