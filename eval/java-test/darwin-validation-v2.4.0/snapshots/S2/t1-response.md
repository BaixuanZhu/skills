# B 组交付说明 · PricingService 单元测试

- 被测类：`src/main/java/com/example/eval/PricingService.java`（`quote(String sku, int quantity)`、`allocate(BigDecimal amount, int people)`）
- 测试类：`src/test/java/com/example/eval/PricingServiceTest.java`（新增，唯一改动文件）
- 栈：JUnit 5.11.4 + Mockito 5.14.2 + AssertJ 3.26.3（均来自工程既有 pom，未改 pom.xml、未改 src/main/java）

## 一、覆盖了什么

共 27 个用例执行（12 个测试方法，含参数化展开），被测方法四维度全覆盖。

### quote(sku, quantity)

| 维度 | 用例 | 要点 |
|---|---|---|
| 正向 | `quote_belowThresholdReturnsTotalWithoutDiscount`（10×5→50.00）、`quote_appliesDiscountAboveThreshold`（30×4=120→108.00）、`quote_acceptsMinimumQuantityOne`（quantity=1） | 值断言 `isEqualByComparingTo` + `scale()==2` |
| 边界 | `quote_appliesDiscountAtExactThreshold`（总额恰 100.00，折扣生效，钉死 `>=` 语义）、`quote_noDiscountJustBelowThreshold`（99.99 不打折）、`quote_roundsHalfUpToTwoDecimals`（11.15×9=100.35→×0.9=90.315→90.32，钉死 HALF_UP）、`quote_forcesScaleTwoOnWholeResult`（5→5.00，scale 断言专抓漏写 setScale(2)） | 阈值两侧 + 舍入 + 强制两位小数 |
| 反向 | `quote_throwsOnNullOrBlankSku`（null/空串/空白串 5 组参数化）、`quote_throwsOnNonPositiveQuantity`（0/-1/MIN_VALUE 3 组） | 具体异常类 + 精确 `hasMessage`，并 `verifyNoInteractions(priceRepository)` 证明未走到查询 |
| 异常 | `quote_throwsWhenPriceNotFound`（repo 返回 null→`NoSuchElementException`，消息 `"price not found: UNKNOWN-1"`） | 断具体异常类而非 RuntimeException 根父类 |

### allocate(amount, people)

| 维度 | 用例 | 要点 |
|---|---|---|
| 正向 | `allocate_dividesEvenly`（100/4→25.00） | 值 + scale 双断言 |
| 边界 | `allocate_roundsDown`（1/3→0.33）、`allocate_roundsUp`（2/3→0.67）、`allocate_roundsHalfUpOnTie`（0.005/1→0.01，钉死 tie 远离零）、`allocate_singlePersonKeepsAmount`（people=1，42.5→42.50）、`allocate_zeroAmount`（0→0.00）、`allocate_dividesNegativeAmount`（-100/3→-33.33，现状记录） | 舍入方向 + scale 强制 + 端点 |
| 反向 | `allocate_throwsOnNullAmount`、`allocate_throwsOnNonPositivePeople`（0/-1/MIN_VALUE） | 具体异常类 + 精确 `hasMessage` |

分支核对：quote 的 sku 判空 / quantity 判非正 / 价格缺失 / 折扣与不折扣 / setScale，allocate 的 amount 判空 / people 判非正 / divide——每个 `if` 分支至少一个用例走到。等价类核对：null、空串、空白串、越界极值、阈值端点、tie 舍入均已打勾。

### 技能三检查点落实

1. **mock 注入有效性**：`PriceRepository` 构造器注入（被测类无内部 `new`），`@Mock`+`@InjectMocks` 经 `MockitoAnnotations.openMocks` 装配（pom 仅含 mockito-core，无 mockito-junit-jupiter，故不用 `MockitoExtension`；`@AfterEach` close 防 mock 泄漏）。核心用例用桩值驱动断言（桩 10 得 50.00），并 `verify(priceRepository).findPrice("SKU-1")` + `verifyNoMoreInteractions` 证明被测代码用的就是该 mock 实例。
2. **断言口径**：金额一律 `isEqualByComparingTo` 比值，另断 `scale()==2` 固定两位小数要求（不用 `equals`，避免 scale 恰好一致时假绿）；异常断 `IllegalArgumentException` / `NoSuchElementException` 具体类 + `hasMessage` 精确消息，不落在根父类。
3. **断言有效性**：无「只调用不断言」用例；桩值与期望值不恒等（如 10.00→50.00、11.15→90.32），实现改坏必红。

## 二、实际运行命令与结果

工作目录：`I:/GitDownload/skills/eval/java-test/darwin-validation-v2.4.0/runs/B`

1. 基线全量：

```
mvn test
```

结果（surefire 摘要，非仅 BUILD SUCCESS）：

```
[INFO] Tests run: 27, Failures: 0, Errors: 0, Skipped: 0 -- in com.example.eval.PricingServiceTest
[INFO] Tests run: 27, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

执行证据：`target/surefire-reports/TEST-com.example.eval.PricingServiceTest.xml` 内逐条列出 27 个 `<testcase>`（含参数化展开名，如 `quote_throwsOnNullOrBlankSku(String)[1..5]`），与 `Tests run: 27` 吻合，确认本次用例逐条被执行。

2. 反证后恢复再全量：

```
mvn test
```

结果：`Tests run: 27, Failures: 0, Errors: 0, Skipped: 0` + `BUILD SUCCESS`，与基线一致。

## 三、反证（变异验证）——已做，两条

按技能要求「临时改坏实现→目标用例变红→恢复→重跑为绿」：

| 突变 | 改动（临时） | 运行命令 | 预期/实际 |
|---|---|---|---|
| A：折扣边界 | `quote` 中 `total.compareTo(DISCOUNT_THRESHOLD) >= 0` 改为 `> 0` | `mvn test -Dtest='PricingServiceTest#quote_appliesDiscountAtExactThreshold' -DfailIfNoTests=false` | 预期红/实际红：`expected: 90.00 but was: 100.00`，`Tests run: 1, Failures: 1` |
| B：分摊 scale | `allocate` 中 `divide(..., 2, HALF_UP)` 的 scale 2 改为 3 | `mvn test -Dtest='PricingServiceTest#allocate_roundsUp+allocate_dividesEvenly' -DfailIfNoTests=false` | 预期红/实际红：`expected: 0.67 but was: 0.667`、`expected: 2 but was: 3`，`Tests run: 2, Failures: 2` |

两次突变均已恢复（Edit 反向回改）。恢复核验：工程目录在 git 中未被跟踪（`git status` 显示 `??`，`git diff` 无输出，无法用 git 佐证），改为逐字核对源文件——`PricingService.java` 第 35 行为 `>= 0`、第 48 行为 `divide(..., 2, ...)`，全文 50 行与改动前读入的原文一致；且恢复后全量 27 用例重跑全绿，与基线一致。生产代码、pom.xml 均未留任何改动。

## 四、无法验证项 / 说明

- 无未跑项：`mvn test` 基线、两次突变单测、恢复后全量，均已实际执行，见上文命令与输出。
- 未做变异测试门禁（PIT 等）：工程未配置 mutation-testing 插件（pom 只有 surefire），按技能「项目已配变异测试门禁时同时以其结果为准」，未配置即以上述手工反证为准。
- 不追求覆盖率数字（技能明确以「四维度 + 分支 + 等价类」三条清单为完成判据）；未写集成/切片测试，不属本技能范围。
- 现状记录（非测试缺陷）：`allocate` 不拒绝负数金额，`allocate_dividesNegativeAmount` 仅记录当前行为（-100/3→-33.33）；若契约要求拒绝负数金额需改生产代码，本任务禁改生产代码，故未加会失败的反向断言，留待产品决策。
- 环境告警（不影响结果）：Mockito self-attaching agent 在 JDK 25 下有 `Dynamic loading of agents will be disallowed` 警告，属 mockito-core 环境提示，与用例正确性无关。
