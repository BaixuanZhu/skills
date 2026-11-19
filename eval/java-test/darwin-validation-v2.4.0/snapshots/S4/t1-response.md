# D 组 · 第二阶段交付报告（java-unit-test）

日期：2026-11-19
被测类：`com.example.eval.PricingService`（`quote(String, int)` / `allocate(BigDecimal, int)`）
测试文件：`src/test/java/com/example/eval/PricingServiceTest.java`
约束遵守：`src/main/java` 与 `pom.xml` 最终状态零改动（反证期间临时改动已恢复并逐字节校验）。

## ① 技能加载

- 已读取 `plugins/java-test/skills/java-unit-test/SKILL.md`（v2.3.0）。
- 基线运行命中编译失败与 mock 装配类问题，已补读同目录 `references/01-pitfalls.md`。
- 范围判定：被测类为纯内存对象 + 接口 mock，无 `@SpringBootTest` / 切片注解 / 真实 DB / 中间件 → 留在 **java-unit-test**，不切换 java-integration-test。
  （`OrderService` 是集成层激活探针，不在本次任务范围，未写其测试，符合激活闸门。）

## ② 生成核对（四维逐项）

### mock 实例一致性

- `@Mock PriceRepository` 经 `MockitoAnnotations.openMocks(this)` 创建后，**显式** `new PricingService(priceRepository)` 注入构造器（测试文件 29-34 行）——mock 就是被测代码真正使用的实例，非类内部 `new` 的影子实例。
- `verify`/`verifyNoMoreInteractions` 均能命中（`callsRepositoryWithGivenSku` 实测通过），不存在「桩值没生效/verify 从不命中」的假绿特征。

### 断言可失败性

- 金额：一律 `isEqualByComparingTo(...)` 比值 + `hasScaleOf(2)` 单独校 scale，不用 `equals`（规避 pitfalls #一）。
- 异常：断具体契约类（`IllegalArgumentException` / `NoSuchElementException`，非根父类）+ 精确 `hasMessage(...)`（升级自初稿的 `withMessageContaining`，规避 pitfalls #六）。
- 无恒真/空断言：`callsRepositoryWithGivenSku` 以 `verify`+`verifyNoMoreInteractions` 作断言；`noRepositoryInteraction` 显式 `assertThatNoException()`（规避 pitfalls #七）。桩值与期望值分属不同数据路径（如 33.33×5→149.985→HALF_UP→149.99），不存在「桩返回恒等于期望值」。

### 四维覆盖

| 维度 | quote | allocate |
|---|---|---|
| 正向 | 未过门槛原价（10×5=50.00）、过门槛 9 折（30×5→135.00）、quantity=1 | 整除分摊（100/4=25.00）、单人原样（123.45） |
| 反向 | null/空串/空白 sku、quantity=0/-3 | amount=null、people=0/-1 |
| 边界 | 恰好等于门槛 100.00 打折、99.99 不打折、HALF_UP 进位（149.985→149.99）与舍去（0.005→0.01） | 0 金额、1/300 得 0.00、HALF_UP 进位（0.025→0.03）与舍去（0.333…→0.33） |
| 异常 | `IllegalArgumentException`×5、`NoSuchElementException`（price not found: SKU-404） | `IllegalArgumentException`×3 |

分支核对：`sku null/blank`、`quantity<=0`、`unitPrice==null`、`total>=threshold` 两侧（打折/不打折）、`amount==null`、`people<=0` 每个分支至少一条用例走到。共 **24** 条用例（QuoteTest 14 + AllocateTest 10）。

### 本次修订内容

1. **修复编译失败（阻断项）**：原测试用 `@ExtendWith(MockitoExtension.class)`，但该扩展位于 `mockito-junit-jupiter` 独立构件，pom 仅有 `mockito-core`（且 pom 不可改）→ 基线 `mvn test` 编译报 `程序包org.mockito.junit.jupiter不存在`。改为 `mockito-core` 内的 `MockitoAnnotations.openMocks(this)` + `@AfterEach close()`。
2. 9 处异常断言 `withMessageContaining` → 精确 `withMessage`（消息契约：`sku must not be blank` / `quantity must be positive` / `price not found: SKU-404` / `amount must not be null` / `people must be positive`）。
3. 其余用例设计本身四维齐全、金额口径正确，未做多余改动。

## ③ 执行证据（非仅 BUILD SUCCESS）

命令：`mvn test`（Maven 3.10.0 / Temurin JDK 25，pom release 17）

```
[INFO] Running com.example.eval.PricingServiceTest$AllocateTest
[INFO] Tests run: 10, Failures: 0, Errors: 0, Skipped: 0 -- in ...$AllocateTest
[INFO] Running com.example.eval.PricingServiceTest$QuoteTest
[INFO] Tests run: 14, Failures: 0, Errors: 0, Skipped: 0 -- in ...$QuoteTest
[INFO] Tests run: 24, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

surefire XML 报告（`target/surefire-reports/TEST-*.xml`）逐用例名单确认 24 条目标用例全部实际执行（含 `exactlyAtDiscountThreshold_appliesDiscount`、`discountRounding_halfUp`、`rounding_halfUpRoundsUp`、`priceNotFound_throwsNoSuchElementException` 等），无跳过、无被过滤。

## ④ 反证（改坏实现 → 红 → 恢复 → 绿）

选核心断言：`exactlyAtDiscountThreshold_appliesDiscount`（折扣门槛边界，期望 90.00）。

1. **改坏实现**：`PricingService.java` 第 35 行折扣判定 `total.compareTo(DISCOUNT_THRESHOLD) >= 0` 临时改为 `> 0`（边界失效）。
2. **目标测试变红**（QuoteTest 14 条中仅目标失败）：
   ```
   [ERROR] ...exactlyAtDiscountThreshold_appliesDiscount -- <<< FAILURE!
   expected: 90.00
    but was: 100.00
   [ERROR] Tests run: 14, Failures: 1 ... BUILD FAILURE
   ```
3. **恢复实现**：从字节级备份还原，sha256 前后一致：
   `d2e4cf416495a4b326ae94757ad38acf0730d1c48ded6c5b64070bfae86f05b8`（改前 = 改后）。
4. **重跑变绿**：`mvn test` → Tests run: 24, Failures: 0, Errors: 0 → BUILD SUCCESS。

结论：该核心断言确实能捕获实现缺陷，非假绿。

## 交付状态

- 测试文件：24 用例全绿，已按技能规范修订（mock 装配、金额口径、具体异常+精确消息、四维覆盖）。
- `src/main/java`、`pom.xml`：零残留改动（哈希校验 + 全程未编辑 pom）。
- 无未披露事项；执行与反证均已实际完成，无需豁免。
