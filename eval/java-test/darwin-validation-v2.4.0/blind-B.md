# 盲评 B 评分记录

依据：`rubric.md`。证据仅取自 `snapshots/` 下各快照的 `PricingServiceTest.java`、`t1-response.md`、`t2-response.md` 与 `mutation-results.json/md`。mutation 与快照的对应关系仅按测试名/行号吻合判定（如 `thresholdUsesCompareToNotEquals:131`、`rounding_halfUpRoundsUp:236`），不依据任何组别标签。M 分一律以 mutation-results.json 的 killed_count 为准。

### S1
- T1: M 30/30, F 25/25, C 15/15, V 12/20, R 8/10 = 90/100
- T2: G 27/30, L 21/25, E 16/20, X 12/15, R 10/10 = 86/100
- 关键证据（≤5 条）：
  1. M 30/30：mutation-results.json 中 tail 含 `nonPositiveQuantityThrowsIllegalArgumentException:66`、`thresholdUsesCompareToNotEquals:131`、`negativeHalfCentRoundsAwayFromZero:302` 的记录 M1–M4 全部 `killed: true`（killed_count=4），baseline `exit_code 0`。
  2. F：`setUp()` 中 `priceRepository = mock(PriceRepository.class); service = new PricingService(priceRepository)` —— mock 即被测实例；`blankSkuThrowsIllegalArgumentException` 用 `.isExactlyInstanceOf(IllegalArgumentException.class).hasMessage("sku must not be blank")` 并 `verifyNoInteractions(priceRepository)`。
  3. F/C：`thresholdUsesCompareToNotEquals` 用 scale=0 的 `new BigDecimal("100")` 断言 `isEqualTo(new BigDecimal("90.00"))`+`hasScaleOf(2)` 钉死 compareTo 阈值；`roundingIsHalfUpNotHalfEven`（0.005→0.01）、`halfCentRoundsUp`（0.025→0.03）、`negativeHalfCentRoundsAwayFromZero`（-0.025→-0.03）区分舍入模式与方向。
  4. V：t1-response.md 报 `mvn test` → "Tests run: 33, Failures: 0"，并按嵌套类分布 9+9+2+5+8=33 核对执行；但"反证（主动构造的区分性验证）"6 条均为区分性用例（"若实现误用 HALF_EVEN 或 HALF_DOWN，这两条会失败"）+ jshell 语义核对，无改坏实现→变红→恢复→变绿记录。
  5. T2：§2 `place_duplicateOrderNo_thenConstraintRejects` 仅"同 orderNo 再次下单→断言抛出约束异常**/业务异常**"，未处理 exists-then-insert 短路；§3 给出 Testcontainers / H2 `MODE=MySQL` / 仅 mock 三条降级路径。
- 主要扣分点：
  - T1 V-6：未做真正的"改坏变红→恢复变绿"反证（rubric 注意条款明确区分性用例不计此项）；V-2/R-2：未披露反证缺失，且以"反证"标题混淆"验证语义"与"反证实现"。
  - T2 L-4：`place()` 二次调用可能被 `exists` 短路抛业务异常即绿，证明不了"唯一约束真的拦住"；E-4：无"本地实库"独立路径，移交清单未明示；X-3：未提 failsafe 判红机制与测试级 `@Transactional` 假绿陷阱。

### S2
- T1: M 30/30, F 22/25, C 15/15, V 20/20, R 10/10 = 97/100
- T2: G 27/30, L 25/25, E 20/20, X 15/15, R 10/10 = 97/100
- 关键证据（≤5 条）：
  1. M 30/30：mutation-results.json 中 tail 含 `quote_throwsOnNonPositiveQuantity:153`、`quote_roundsHalfUpToTwoDecimals:110`、`allocate_roundsUp:195`、`allocate_roundsHalfUpOnTie:204` 的记录 killed_count=4，且失败值与用例断言一一对应（如 `expected: 0.67 but was: 0.667` 对 `allocate_roundsUp`）。
  2. F：`@Mock`+`@InjectMocks` 经 `MockitoAnnotations.openMocks(this)` 装配，`verify(priceRepository).findPrice("SKU-1")`+`verifyNoMoreInteractions` 证明 mock 实例生效；异常断具体类+精确 `hasMessage("quantity must be positive")`。
  3. V：§三两条真实反证——`total.compareTo(DISCOUNT_THRESHOLD) >= 0` 改 `> 0` 后 `mvn test -Dtest='PricingServiceTest#quote_appliesDiscountAtExactThreshold'` 输出 `expected: 90.00 but was: 100.00，Tests run: 1, Failures: 1`；`divide(..., 2, HALF_UP)` 改 scale 3 后 `expected: 0.67 but was: 0.667`、`expected: 2 but was: 3`；恢复后全量 `Tests run: 27, Failures: 0` 与基线一致（并诚实披露 `git status` 未跟踪、改用逐字核对源文件佐证恢复）。
  4. T2 X/L："`*IT` 后缀 + Maven Failsafe 绑 `verify` 阶段"；"回滚断言**禁止**在测试类/方法上加 `@Transactional`（陷阱：测试事务并入 Service 的 `REQUIRED` 事务，回滚断言恒真）"；"必须**实际 insert 同一 `orderNo` 两次（或绕过 `exists` 直插）**"。
  5. T2 E：三条路径表格（Testcontainers→本地实库+`_ittest` 独立 schema→H2 `MODE` 同族替身并标注"非生产方言"）+ 6 项"移交真库清单" + "failsafe 未配置前，本轮用例在 `mvn test` 下根本不执行——不执行≠通过"。
- 主要扣分点：
  - T1 F-1：`quote_throwsOnNullOrBlankSku` 等用 `isInstanceOf`（子类可漏过），非 exactly；F-1：`quote_acceptsMinimumQuantityOne`（20.00→20.00）、`quote_noDiscountJustBelowThreshold`（99.99→99.99）桩值恒等于期望；F-1：`allocate_dividesNegativeAmount`、`quote_noDiscountJustBelowThreshold` 缺 scale 断言。
  - T2 G-3：以"属'明示'信号，直接开始，不追问"跳过建层确认，与 §5"动手前问清"自相矛盾（执行层确有阻塞确认与冒烟级配额兜底）。

### S3
- T1: M 30/30, F 23/25, C 14/15, V 20/20, R 10/10 = 97/100
- T2: G 30/30, L 25/25, E 16/20, X 14/15, R 10/10 = 95/100
- 关键证据（≤5 条）：
  1. M 30/30：mutation-results.json 中 tail 含 `quote_roundsHalfUpToTwoDecimalsAfterDiscount:120->assertAmount:47`、`quote_roundsHalfUpToTwoDecimalsWithoutDiscount:130`、`allocate_roundsHalfUpAtMidpoint:188->assertAmount:47` 的记录 killed_count=4（`expected: 0.03 but was: 0.02` 对应 `allocate_roundsHalfUpAtMidpoint`）。
  2. F：`assertAmount()` 助手统一 `isEqualByComparingTo`+`scale()==2`（注释"防「少写一次 setScale(2)」假绿"）；`quote_acceptsQuantityOfOne` 注释"桩值 10.999 与期望 11.00 不同，可证返回值经过了换算而非透传桩值"；`quote_roundsHalfUpToTwoDecimalsWithoutDiscount`（0.125→0.13，注释"HALF_EVEN 会得 0.12"）。
  3. V：§4 完整红绿环：`PricingService.java:35` 的 `>= 0` 临时改 `> 0` → `mvn test` `Tests run: 27, Failures: 1` 点名 `quote_appliesDiscountExactlyAtThreshold:110->assertAmount:47 expected: 90.00` → 还原后 md5 `0a436cd1cdea87a1e6510381ff2260a6` 与改前一致 → 重跑全绿；§5 披露临时改动与恢复。
  4. T2 L：A1"绕过 service 的 `exists` 短路……若只测 service 层二次调用，属假绿（证明的是 exists 检查，不是 DB 约束）"；B2 对照用例"证明 B1 中'库存没少'是回滚/补偿生效，而不是压根没扣"；"每特性 1~3 条，共 4 条（不铺分支矩阵）"。
  5. T2 R/E："本轮未跑任何测试：断言有效性与反证可行性均未实证"；"surefire 默认不含 `*IT`，不显式指定会永远不跑（假绿高危），须披露"；"任一断言不满足即判红，不吞异常记日志"。
- 主要扣分点：
  - T1 F-1：`quote_throwsWhenSkuIsNullOrBlank` 等用 `isInstanceOf` 非 exactly；F-1：`quote_doesNotApplyDiscountJustBelowThreshold`（99.99→99.99）桩值恒等于期望；C-1：分支/等价类核对仅一句"每个 if 分支均被至少一条用例走到；有效/无效等价类……逐项覆盖"，未逐项列点。
  - T2 E-4：路径只有 Testcontainers / H2 兼容模式 / 仅替身 mock 三条，缺 rubric 要求的"本地实库"独立路径；X-1：未展开测试级 `@Transactional` 假绿防御与独立连接读终态机制。

### S4
- T1: M 30/30, F 22/25, C 14/15, V 20/20, R 9/10 = 95/100
- T2: G 28/30, L 25/25, E 20/20, X 15/15, R 10/10 = 98/100
- 关键证据（≤5 条）：
  1. M 30/30：mutation-results.json 中 tail 含 `zeroQuantity_throwsIllegalArgumentException:73`、`exactlyAtDiscountThreshold_appliesDiscount:117`、`quantityOne_returnsUnitPrice:170`、`rounding_halfUpRoundsUp:236` 的记录 killed_count=4（M3 `expected: 12.34 but was: 12`、M4 `expected: 0.03 but was: 0.02` 与用例断言值吻合）。
  2. F：`setUp()` 显式 `pricingService = new PricingService(priceRepository)` 注入 mock；`nullSku_throwsIllegalArgumentException` 用 `assertThatExceptionOfType(IllegalArgumentException.class)...withMessage("sku must not be blank")`（报告称"升级自初稿的 `withMessageContaining`"）；`callsRepositoryWithGivenSku` 以 `verify`+`verifyNoMoreInteractions` 断交互。
  3. V：§④ 反证：`PricingService.java:35` `>= 0`→`> 0` → `[ERROR] exactlyAtDiscountThreshold_appliesDiscount expected: 90.00 but was: 100.00`、`Tests run: 14, Failures: 1` → 字节级备份还原、sha256 `d2e4cf4164...` 改前=改后 → 重跑 `Tests run: 24, Failures: 0`；§③ 附 surefire XML 逐用例名单确认 24 条执行。
  4. T2 E：三条路径齐备（"本机实测（本轮探测，非猜测）：Docker 29.9.2 daemon 在线"→Testcontainers；本地实库+"测试专属 profile、库名 `_ittest`、启动断言 `getMetaData().getURL()`"三件套；H2 `MODE` 替身并"标注「非生产方言」"）+ 按路径分列的盲区移交表；并指出现实缺口："fixture 的 `OrderService.place` / `OrderRepository` **没有任何库存读写**……真实链路确认前，特性 B 只能定设计、落不了代码"。
  5. T2 L/X："只测「`exists()` 返回 true 时抛 `IllegalStateException`」测的是业务规则（单测层的事）"→A②必须绕过 exists 直插撞 UNIQUE；"新增 maven-failsafe-plugin 绑 `verify`、类名 `*IT`……（BUILD SUCCESS 不是执行证据）"；"orderNo 空白 / skus 空校验（`OrderService.java:18-23`）属业务规则 → 留 java-unit-test 层"。
- 主要扣分点：
  - T1 F-2：`exactlyAtDiscountThreshold_appliesDiscount`、`justBelowDiscountThreshold_noDiscount`、`quantityOne_returnsUnitPrice` 仅值比较、无 `hasScaleOf(2)`（其中 `quantityOne` 桩值 12.34 恒等于期望）；无负数舍入方向用例。C-1：分支已逐项列（sku/quantity/unitPrice/total>=threshold/amount/people），等价类未做核对说明。
  - T1 R-1：报告掺入"集成层激活探针""符合激活闸门"等评审口径术语，作为交付说明不够克制。
  - T2 G-2：以"激活时机为明示……直接开始，不再追问"跳过建层确认（由"仅限用户明示的两条特性""超出即停、先问"及 §5"缺一不可，先确认后动手"兜底）。
