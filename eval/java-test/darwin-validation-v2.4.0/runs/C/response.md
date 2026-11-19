# C 组交付 · PricingServiceTest

工程目录：`I:/GitDownload/skills/eval/java-test/darwin-validation-v2.4.0/runs/C`
被测类：`com.example.eval.PricingService`（纯单测，无 Spring/真实依赖，适用 java-unit-test 规范 v2.3.0）

## 1. 交付文件

| 文件 | 操作 |
|---|---|
| `src/test/java/com/example/eval/PricingServiceTest.java` | 创建并按技能规范修订 |
| `response.md` | 本文件 |

`src/main/java`、`pom.xml` 最终无任何改动（反证期间的临时改坏已恢复，见 §4）。

## 2. 测试设计（对照 java-unit-test 规范）

- **mock 注入**：`@Mock PriceRepository` + `@InjectMocks PricingService`，`MockitoAnnotations.openMocks` 装配（项目仅有 mockito-core，无 mockito-junit-jupiter，故不使用 MockitoExtension）。被测类构造器注入 `PriceRepository`，mock 即被测代码真正使用的实例；断言路径上有 `verify(priceRepository).findPrice(...)` / `verifyNoInteractions(...)` 可证桩值真实生效。
- **金额口径**：不用 `equals`/`isEqualTo(BigDecimal)`（连 scale 一起比），统一 `assertAmount()` 助手 = `isEqualByComparingTo`（比值）+ `scale()==2`（固定两位小数合同单断）。
- **异常断言**：断契约指定的具体异常类 + `hasMessage`（IllegalArgumentException / NoSuchElementException），不退化到 RuntimeException。
- **断言可失败性**：无恒真断言；桩值与期望值不重合（如 `10.999 → 11.00`、`0.025 → 0.03`）；舍入边界用恰好半值用例区分 HALF_UP 与 HALF_EVEN。

### 四维覆盖

| 方法 | 正向 | 反向 | 边界 | 异常 |
|---|---|---|---|---|
| `quote` | 无折扣总价、有折扣总价、整数金额保持 scale 2 | 阈值下 99.99 不打折 | 恰好达阈值 100.00 打折（`>=`）、数量 1、折后 HALF_UP 进位（90.018→90.02）、无折 HALF_UP 半值（0.125→0.13） | sku null/空/全空白（5 例）、quantity 0/-1/-10（3 例）、价格缺失 NoSuchElementException + 消息 |
| `allocate` | 整除、非整除截位 | amount null | 半值 HALF_UP（0.025→0.03）、恰好整除保持 scale 2、单人归一 scale（5→5.00）、零金额 0.00 | amount null、people 0/-1/-3（3 例） |

`quote`/`allocate` 每个 if 分支均被至少一条用例走到；有效/无效等价类（null、空串、越界）逐项覆盖。参数化用例展开后共 27 个执行单元。

## 3. 执行证据

命令：`mvn -f .../runs/C/pom.xml test`（Maven 3.10.0 / JDK 25 / surefire 3.5.2 / JUnit 5.11.4）

- 输出：`Tests run: 27, Failures: 0, Errors: 0, Skipped: 0`，`BUILD SUCCESS`。
- 逐用例执行确认（非仅 BUILD SUCCESS）：`target/surefire-reports/TEST-com.example.eval.PricingServiceTest.xml` 含 27 个 `<testcase>`，与测试方法一一对应（含参数化展开 `[1]..[5]`）。
- Mockito 自附着 agent 的 JDK 25 警告 1 条（WARNING，非错误，不影响结果）。

## 4. 反证记录（改坏实现 → 目标测试变红 → 恢复变绿）

目标断言：`quote_appliesDiscountExactlyAtThreshold`（阈值边界 `>= 100.00` 打 9 折，期望 90.00）。

1. **改坏**：`PricingService.java:35` 临时把 `total.compareTo(DISCOUNT_THRESHOLD) >= 0` 改为 `> 0`（边界判定收窄一档）。该改动为反证临时操作，结束后立即恢复。
2. **变红**：`mvn test` → `Tests run: 27, Failures: 1`，唯一点名失败即目标用例：
   `PricingServiceTest.quote_appliesDiscountExactlyAtThreshold:110->assertAmount:47 expected: 90.00`，`BUILD FAILURE`。
3. **恢复**：还原为 `>= 0`；md5 校验 `0a436cd1cdea87a1e6510381ff2260a6`，与改坏前完全一致。
4. **重跑变绿**：`mvn test` → `Tests run: 27, Failures: 0, Errors: 0, Skipped: 0`，`BUILD SUCCESS`。

结论：该核心断言对折扣边界实现真实敏感，非假绿。

## 5. 披露

- 反证按规程对 `src/main/java` 做过一次临时改坏并已恢复，md5 与原始一致，最终交付状态无残留改动；`pom.xml` 全程未动。
- 无未执行项：mvn test 已实际运行三次（基线绿 / 改坏红 / 恢复绿），反证已完成。
