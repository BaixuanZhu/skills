# A 组评估报告 — PricingService 单元测试

## 交付物

- 新增（未修改任何其他文件）：
  - `src/test/java/com/example/eval/PricingServiceTest.java`（33 个测试用例）
- 未触碰：`src/main/java/**`、`pom.xml`（生产代码零改动，测试全部针对现有行为编写）。

## 实际运行命令与结果

```text
cd I:/GitDownload/skills/eval/java-test/darwin-validation-v2.4.0/runs/A
mvn test
```

结果（2026-11-19）：

```text
Tests run: 33, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS   (Total time: 8.930 s)
```

按嵌套类分布：
- `QuoteValidation` 9 个、`QuotePricing` 9 个、`QuoteRepositoryInteraction` 2 个
- `AllocateValidation` 5 个、`AllocateRounding` 8 个

环境：Maven 3.10.0 / JDK 25（pom 指定 `maven.compiler.release=17`）/ JUnit 5.11.4 / Mockito 5.14.2 / AssertJ 3.26.3。

## 覆盖内容

### quote(String sku, int quantity)

| 维度 | 用例 |
| --- | --- |
| sku 为 null / 空串 / 纯空白 | 抛 `IllegalArgumentException("sku must not be blank")`，且不触达 repository |
| quantity ≤ 0（0、-1、Integer.MIN_VALUE） | 抛 `IllegalArgumentException("quantity must be positive")`，且不触达 repository |
| 校验顺序 | sku 与 quantity 同时非法 → 先报 sku 错 |
| 价格缺失 | 抛 `NoSuchElementException("price not found: SKU-404")`（精确类型，非 IllegalArgumentException） |
| 折扣阈值边界 | 50.00×2=100.00 → 打 9 折得 90.00；49.99×2=99.98 → 不打折 |
| 折扣后舍入 | 50.01×2=100.02×0.9=90.018 → 90.02；19.99×6=119.94×0.9=107.946 → 107.95 |
| HALF_UP 舍入模式 | 0.005 → 0.01（HALF_EVEN 会得 0.00）；0.004 → 0.00 |
| 金额口径 scale=2 | 所有断言同时用 `isEqualTo(new BigDecimal(...))`（equals 校验 scale）+ `hasScaleOf(2)`；整数价 30×1 → "30.00" |
| mock 交互 | `verify(times(1)).findPrice("SKU-9")` + `verifyNoMoreInteractions`；不同 sku 各自命中 stub |

### allocate(BigDecimal amount, int people)

| 维度 | 用例 |
| --- | --- |
| amount 为 null | 抛 `IllegalArgumentException("amount must not be null")` |
| people ≤ 0（0、-1、MIN_VALUE） | 抛 `IllegalArgumentException("people must be positive")` |
| 校验顺序 | amount 与 people 同时非法 → 先报 amount 错 |
| 整除 | 100/4 → 25.00（补齐 scale=2） |
| 除不尽截断 | 10.00/3 → 3.33 |
| 半分进位 | 0.05/2=0.025 → 0.03（HALF_EVEN 会得 0.02） |
| 负数舍入方向 | -0.05/2=-0.025 → -0.03（HALF_UP 远离零）；-10.00/3 → -3.33 |
| 零金额 / 单人 | 0.00/5 → 0.00；1.00/1 → 1.00 |
| 纯计算 | allocate 全程 `verifyNoInteractions(priceRepository)` |

### 技术要点

- pom 只有 `mockito-core`（无 `mockito-junit-jupiter`），故不使用 `@ExtendWith(MockitoExtension.class)`，改为 `@BeforeEach` 中手动 `mock(PriceRepository.class)` 注入。
- 异常断言一律 `isExactlyInstanceOf(...)` + `hasMessage(...)` 精确匹配，避免 `isInstanceOf(RuntimeException.class)` 之类的宽松匹配放走错误异常类型。

## 反证（主动构造的区分性验证）

1. **HALF_UP vs HALF_EVEN**：`0.005 → 0.01`、`0.05/2 = 0.025 → 0.03`。若实现误用 HALF_EVEN 或 HALF_DOWN，这两条会失败。负数方向用 `-0.025 → -0.03` 区分 HALF_UP（远离零）与 HALF_DOWN（趋向零）。
2. **阈值比较语义**：`compareTo >= 0` vs `equals`。用 scale=0 的 `new BigDecimal("100")`（总价 100）验证：`equals("100.00")` 为 false 但 `compareTo` 为 0，实现仍应打折 → 断言结果 90.00，防住误用 equals 判断阈值的退化。
3. **异常类型不可偷懒**：价格缺失必须是 `NoSuchElementException` 而不是笼统 RuntimeException/IllegalArgumentException；入参非法必须是 `IllegalArgumentException`。均用精确类型断言。
4. **校验顺序**：`quote("", 0)` 断言报 sku 错、`allocate(null, 0)` 断言报 amount 错，固定校验顺序防止实现调换后测试仍绿。
5. **金额口径**：所有金额断言额外用 `hasScaleOf(2)` + `equals` 语义（scale 敏感），防止实现返回 scale=0/1 的"等值"金额蒙混过关（如返回 `25` 而非 `25.00`）。
6. **副作用边界**：入参非法路径与 allocate 路径均断言 `verifyNoInteractions(priceRepository)`，反证"非法输入不该打到仓储层"。

写测试前先用 jshell 独立验证了 BigDecimal HALF_UP 在正/负半分点的行为（-0.025→-0.03、0.025→0.03、90.018→90.02 等），确认期望值与 Java 实际语义一致，避免把"我以为的舍入"写成断言。

## 无法验证 / 范围外项

1. **Mockito 自附着代理告警**：JDK 25 下 Mockito 5.14.2 通过 dynamic agent 加载 byte-buddy-agent，Maven 输出有 "will no longer work in future releases of the JDK" 警告。当前测试全部通过，但这是环境级隐患，无法用测试本身验证或消除（需改 pom 加 `-javaagent`，而 pom 不允许修改）。
2. **折扣常量本身**：`DISCOUNT_THRESHOLD=100.00`、`DISCOUNT_RATE=0.9` 是私有常量，只能通过公共 API 行为间接验证（边界 100.00 折后 90.00、107.946→107.95），无法直接断言常量值。
3. **构造器依赖为 null 的行为**：`new PricingService(null)` 后调用 allocate 可以工作、调用 quote 会 NPE——这不是公开契约，未写测试固化该行为。
4. **并发/性能**：被测类为无状态纯计算 + 仓储调用，无并发契约，未覆盖。
