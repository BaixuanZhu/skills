# 盲评 A · darwin-validation-v2.4.0

> 评分依据仅限 snapshots/（S1–S4 的 PricingServiceTest.java、t1-response.md、t2-response.md）与 mutation-results.json/md、rubric.md。
> M 维以 mutation-results.json 为准；各条目 tail 点名的用例名/行号与对应快照测试文件逐一吻合，且 4 个条目均为 4/4 KILLED，故各快照 M 均为 30/30。
> 引用均为测试名、代码、命令或报告原句；不推测实验组来源。

### S1
- T1: M 30/30, F 24/25, C 14/15, V 12/20, R 8/10 = 88/100
- T2: G 27/30, L 22/25, E 15/20, X 12/15, R 8/10 = 84/100
- 关键证据（≤5 条）：
  1. M=30：mutation tail 点名 `PricingServiceTest$QuotePricing.thresholdUsesCompareToNotEquals:131`、`PricingServiceTest$QuoteValidation.nonPositiveQuantityThrowsIllegalArgumentException:66`、`PricingServiceTest$AllocateRounding.negativeHalfCentRoundsAwayFromZero:302`，与本快照测试名/行号完全一致，M1–M4 全部 KILLED。
  2. F：`setUp()` 中 `priceRepository = mock(PriceRepository.class); service = new PricingService(priceRepository)`（mock 即被测实例）；异常 `isExactlyInstanceOf(IllegalArgumentException.class).hasMessage("sku must not be blank")`；金额 `isEqualTo(new BigDecimal("19.99"))`（注释"equals 校验 scale"）+ `hasScaleOf(2)`。
  3. C：`thresholdUsesCompareToNotEquals`（stub `new BigDecimal("100")` 断言 90.00，区分 compareTo 与 equals）、`roundingIsHalfUpNotHalfEven`（0.005→0.01，注释"HALF_EVEN 会得到 0.00"）、`blankSkuTakesPrecedenceOverBadQuantity`（校验顺序）等边界/口径/顺序用例齐全。
  4. V：实跑 `mvn test` 输出 `Tests run: 33, Failures: 0` 并给出嵌套类分布（9+9+2+5+8=33）；但"反证（主动构造的区分性验证）"节只有区分性用例与 jshell 语义验证（"若实现误用 HALF_EVEN 或 HALF_DOWN，这两条会失败"），全篇无改坏实现→变红→恢复→绿记录。
  5. T2：`place_duplicateOrderNo_thenConstraintRejects` 仅描述"同 orderNo 再次下单 → 断言抛出约束异常/业务异常"，走 `OrderService.place` 会被 `OrderRepository.exists` 短路，可能打不到 UNIQUE 约束（对比 S3/S4 均要求绕过 exists 直插）。
- 主要扣分点：
  - T1-V（−8）：无实现级"改坏→红→恢复→绿"反证（rubric 明示区分性用例/BigDecimal 语义验证不计此项），且未在"无法验证/范围外项"中披露该缺项（−6−2）。
  - T1-R（−2）：将"主动构造的区分性验证"直接命名为"反证"，未区分"验证语义"与"反证实现"。
  - T1-C（−1）：覆盖表格齐全，但无"每个分支至少一条用例走到"式的分支核对说明。
  - T2-L（−3）：唯一约束用例可被 exists 短路假绿（"唯一约束真实拦截"未真正落到约束层）；未识别被测类仅有 `exists/insert`、无库存读写而"库存恢复"落不了地。
  - T2-X（−3）："约束异常/业务异常"不锚定断言口径，未声明失败判红/不吞异常，未要求从 failsafe 报告确认 `*IT` 被执行。
  - T2-E（−5）：三路径缺"本地实库"（仅 Testcontainers → H2 → mock 兜底）；T2-R（−2）：默认"走真实 Spring 上下文"与已知被测类（纯 `exists/insert`）不符且未披露库存链路缺口。

### S2
- T1: M 30/30, F 23/25, C 15/15, V 20/20, R 10/10 = 98/100
- T2: G 27/30, L 25/25, E 20/20, X 15/15, R 10/10 = 97/100
- 关键证据（≤5 条）：
  1. M=30：mutation tail 点名 `quote_roundsHalfUpToTwoDecimals:110`、`quote_throwsOnNonPositiveQuantity:153`、`allocate_roundsUp:195`、`allocate_roundsHalfUpOnTie:204`，与本快照测试名/行号一致，4/4 KILLED。
  2. V 反证两条实做：突变 A `total.compareTo(DISCOUNT_THRESHOLD) >= 0` 改 `> 0`，`mvn test -Dtest='PricingServiceTest#quote_appliesDiscountAtExactThreshold'` 得 `expected: 90.00 but was: 100.00`；突变 B `divide(..., 2, HALF_UP)` scale 改 3，得 `expected: 0.67 but was: 0.667`、`expected: 2 but was: 3`；恢复后"全量 27 用例重跑全绿，与基线一致"。
  3. F：`@InjectMocks` 构造注入 + `verify(priceRepository).findPrice("SKU-1"); verifyNoMoreInteractions(priceRepository)`；`quote_forcesScaleTwoOnWholeResult` 注释"值比较对 5 与 5.00 都绿，scale() 断言才抓得住少写 setScale(2) 的回归"。
  4. C：报告原句"分支核对：quote 的 sku 判空 / quantity 判非正 / 价格缺失 / 折扣与不折扣 / setScale……每个 if 分支至少一个用例走到。等价类核对：null、空串、空白串、越界极值、阈值端点、tie 舍入均已打勾"。
  5. T2："回滚断言**禁止**在测试类/方法上加 `@Transactional`（陷阱：测试事务并入 Service 的 `REQUIRED` 事务，回滚断言恒真）"；"重复订单号断言不能只靠 `OrderRepository.exists` 为 true……必须**实际 insert 同一 `orderNo` 两次（或绕过 `exists` 直插）**"；三路径表（Testcontainers / 本地实库+每类独立 `_ittest` schema / H2 `MODE=MySQL` 标注"非生产方言"）+"failsafe 未配置前，本轮用例在 `mvn test` 下根本不执行——不执行≠通过"。
- 主要扣分点：
  - T1-F（−2）：`quote_noDiscountJustBelowThreshold`、`quote_acceptsMinimumQuantityOne`、`allocate_dividesNegativeAmount` 仅 `isEqualByComparingTo` 未断 `scale()==2`（与报告"另断 scale()==2"的口径声明不符）；`quote_acceptsMinimumQuantityOne`（20.00→20.00）等桩值恒等于期望。
  - T2-G（−3）：把"给订单模块补测试"判为明示并称"直接开始，不追问"，补集成测试实为由 DB 语义目标推断；实现侧已设 4 项阻塞确认、用例限 2~3 条，故轻扣。

### S3
- T1: M 30/30, F 25/25, C 15/15, V 20/20, R 10/10 = 100/100
- T2: G 29/30, L 24/25, E 16/20, X 15/15, R 10/10 = 94/100
- 关键证据（≤5 条）：
  1. M=30：mutation tail 点名 `quote_roundsHalfUpToTwoDecimalsAfterDiscount:120->assertAmount:47`、`quote_roundsHalfUpToTwoDecimalsWithoutDiscount:130->assertAmount:47`、`allocate_roundsHalfUpAtMidpoint:188->assertAmount:47`，与本快照一致，4/4 KILLED。
  2. F：`assertAmount` 助手统一 `isEqualByComparingTo` + `scale()==2`（注释"防『少写一次 setScale(2)』假绿"）；`quote_acceptsQuantityOfOne` 桩 10.999 期望 11.00，注释"桩值 10.999 与期望 11.00 不同，可证返回值经过了换算而非透传桩值"；异常 `isInstanceOf(IllegalArgumentException.class).hasMessage("quantity must be positive")`。
  3. V 反证闭环：改坏 `>= 0`→`> 0` → `Tests run: 27, Failures: 1` 点名 `PricingServiceTest.quote_appliesDiscountExactlyAtThreshold:110->assertAmount:47 expected: 90.00` → "md5 校验 0a436cd1cdea87a1e6510381ff2260a6，与改坏前完全一致" → 重跑 `Tests run: 27, Failures: 0`。
  4. C："quote/allocate 每个 if 分支均被至少一条用例走到；有效/无效等价类（null、空串、越界）逐项覆盖"，且 `quote_roundsHalfUpToTwoDecimalsWithoutDiscount`（0.125→0.13）注明"HALF_EVEN 会得 0.12，可区分舍入口径"。
  5. T2：A1"绕过 service 的 `exists` 短路，经 Repository/JDBC 模板对同 orderNo 连续 insert 两次……若只测 service 层二次调用，属假绿（证明的是 exists 检查，不是 DB 约束）"；"任一断言不满足即判红，不吞异常记日志"；"本轮未跑任何测试：断言有效性与反证可行性均未实证，全部属下一轮执行项"。
- 主要扣分点：
  - T1：无实质扣分（反证、披露、口径、分支核对均达标）。
  - T2-G（−1）：整体最克制（"须用户确认后下一轮才动手"、每特性 1~3 条），仅微调。
  - T2-L（−1）：以"不铺分支矩阵"作预算约束，未显式指派业务分支矩阵/参数校验归单测层。
  - T2-E（−4）：三路径为 Testcontainers / H2 兼容模式 / mock-fake 兜底，缺"本地实库"路径；盲区有列但未按"移交真库"逐项移交标注。

### S4
- T1: M 30/30, F 22/25, C 15/15, V 20/20, R 10/10 = 97/100
- T2: G 28/30, L 25/25, E 20/20, X 15/15, R 10/10 = 98/100
- 关键证据（≤5 条）：
  1. M=30：mutation tail 点名 `exactlyAtDiscountThreshold_appliesDiscount:117`、`zeroQuantity_throwsIllegalArgumentException:73`、`quantityOne_returnsUnitPrice:170`、`rounding_halfUpRoundsUp:236`，与本快照一致，4/4 KILLED。
  2. F：`setUp()` 显式 `pricingService = new PricingService(priceRepository)`（mock 即被测实例）+ `callsRepositoryWithGivenSku` 的 `verify(priceRepository).findPrice("SKU-H"); verifyNoMoreInteractions(priceRepository)`；异常 `assertThatExceptionOfType(IllegalArgumentException.class).isThrownBy(...).withMessage("quantity must be positive")`（报告注明由 `withMessageContaining` 升级为精确消息）。
  3. V 反证：改坏后 `[ERROR] ...exactlyAtDiscountThreshold_appliesDiscount -- <<< FAILURE! expected: 90.00 but was: 100.00`，"从字节级备份还原，sha256 前后一致：d2e4cf416495a4b326ae94757ad38acf0730d1c48ded6c5b64070bfae86f05b8"，重跑 `Tests run: 24, Failures: 0`。
  4. T2 分层与假绿："只测『`exists()` 返回 true 时抛 `IllegalStateException`』测的是业务规则（单测层的事），验不了『约束**真的**拦住』"；"`OrderService.java:24-27` 是 exists-then-insert 的 check-then-act，**存在 TOCTOU 竞态**"；"fixture 的 `OrderService.place` / `OrderRepository` **没有任何库存读写**……特性 B 只能定设计、落不了代码"。
  5. T2 执行："本机实测（本轮探测，非猜测）：Docker 29.9.2 daemon 在线"；"*IT + failsafe 绑 verify……BUILD SUCCESS 不是执行证据"；H2 盲区表按列标注"移交真库"，并声明"本轮不创建测试文件……反证未做——全部推迟到实施轮……此为『无法执行』的明确披露"。
- 主要扣分点：
  - T1-F（−3）：`exactlyAtDiscountThreshold_appliesDiscount`、`justBelowDiscountThreshold_noDiscount`、`quantityOne_returnsUnitPrice` 仅 `isEqualByComparingTo` 未断 `hasScaleOf(2)`（M3 类 scale 变异在这些点上会假绿）；`quantityOne_returnsUnitPrice` 桩值（12.34）恒等于期望值。
  - T2-G（−2）：称"激活时机为明示……直接开始，不再追问"，但"补集成测试"仍是由两条 DB 语义目标推断；实现侧设了"缺一不可，先确认后动手"门槛，故轻扣。
