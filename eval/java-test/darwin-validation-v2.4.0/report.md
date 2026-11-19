# java-test v2.3.0 / v2.4.0 + hook 达尔文验证报告

> 目的：验证技能正文与分层短注入 hook 在 AI 写 Java 测试时的实际增益。
> 日期：2026-11-19
> 方法：4 个隔离生成组 + 2 个独立盲评 agent + 1 个仲裁 agent + 可复现 mutation 检出率。
> 结论先行：**代码正确性在当前模型基线上已饱和；技能与 hook 的增益集中在验证闭环、假绿防御和集成层决策，而不是“会不会写 JUnit”。**

## 一、实验组映射

匿名快照映射如下，盲评阶段不知情：

| 快照 | 实验组 | 条件 |
|---|---|---|
| S1 | **A** | 无技能、无 hook |
| S2 | **B** | 提供 `java-unit-test` SKILL + `references/01-pitfalls.md` |
| S3 | **C** | 先只写测试；写完后收到 hook 分层短注入 |
| S4 | **D** | 模拟 compact：新上下文只剩任务摘要，再收到 hook 注入 |

T1：给 `PricingService` 写单测。  
T2：订单模块要求验证 DB 唯一约束与事务回滚，只输出动作说明。

## 二、客观 mutation 结果

`fixture/PricingService.java` 固定 4 个 mutant：

1. 满 100 折扣分支失效；
2. 非法数量改为返回 `0.00`；
3. 结果 scale 从 2 改为 0；
4. 除法舍入从 `HALF_UP` 改为 `DOWN`。

| 组 | baseline | M1 | M2 | M3 | M4 | 杀死数 |
|---|---|---|---|---|---|---:|
| A | PASS | KILLED | KILLED | KILLED | KILLED | 4/4 |
| B | PASS | KILLED | KILLED | KILLED | KILLED | 4/4 |
| C | PASS | KILLED | KILLED | KILLED | KILLED | 4/4 |
| D | PASS | KILLED | KILLED | KILLED | KILLED | 4/4 |

**解读**：四组都能杀死 mutant，说明这个规模的单测正确性已不是区分点。不能据此说“技能无用”，只能说明**技能价值不在生成正确代码，而在验证纪律与决策边界**。

## 三、T1：单测质量盲评

两份盲评原始分：

| 组 | Agent A | Agent B | 仲裁位次 |
|---|---:|---:|---|
| A | 88 | 90 | 第 4 |
| B | 98 | 97 | 并列第 1 |
| C | 100 | 97 | 并列第 1 |
| D | 97 | 95 | 第 3 |

### 关键差异

1. **验证闭环是最大分水岭**
   - A 组只做了区分性用例和 BigDecimal 语义验证，没有真正“改坏实现→目标测试变红→恢复变绿”。
   - B/C/D 都有真实反证记录，并带 surefire 输出、md5/sha256 恢复核验。
   - 这是技能正文与 hook 共同要求的“反证”真正落地的证据。

2. **假绿防御**
   - B/C/D 都识别 mock 注入、具体异常、金额口径、断言可失败性。
   - C/D 的 hook 注入让 agent 明确检查“mock 是被测对象真正使用的实例”“BUILD SUCCESS 不是执行证据”。
   - A 组测试也能杀 mutant，但报告把“验证语义”叫成“反证”，暴露流程口径不稳。

3. **hook 的作用是召回与修复，不是首次生成**
   - C 组第一阶段只写测试；注入后补读技能、修订金额断言、补执行证据和反证。
   - D 组在 compact 模拟后仍能靠注入恢复规范，还发现 `MockitoExtension` 缺少依赖导致编译失败，并改为 `MockitoAnnotations.openMocks`。
   - 这支持：hook 的价值发生在“写完之后、交付之前”，而不是替代模型的生成能力。

## 四、T2：集成层激活与假绿判断

两份盲评排序完全一致：**D ≥ B > C > A**。

| 组 | 盲评 A | 盲评 B | 关键表现 |
|---|---:|---:|---|
| A | 84 | 86 | 走 `OrderService.place` 可能被 `exists` 短路，测不到 DB 约束；未发现 fixture 没有库存读写 |
| B | 97 | 97 | 明确测试级 `@Transactional` 陷阱、绕过 `exists` 直插、三路径降级、failsafe `verify` |
| C | 94 | 95 | 识别 `exists` 短路假绿，要求用户确认后才扩展集成用例；缺“本地实库”独立路径 |
| D | 98 | 98 | 发现 `exists` 是 TOCTOU、fixture 无库存读写、Docker 可用性实测、移交清单最完整 |

### 关键结论

- **集成层判断的增益比单测代码质量更明显**：A 组最容易把“应用层重复检查”误当成“数据库唯一约束真的拦截”。
- **激活闸门的价值在动作边界**：C 组最克制，先确认再扩展；B/D 虽判断要建集成测试，但都要求先确认环境和事务链路。
- 本次 T2 prompt 提到“数据库唯一约束真的拦住”，已经接近明确的集成层目标，所以四组都倾向建集成测试；真正拉开差距的是：**是否识别假绿路径、是否披露环境盲区、是否把业务分支留在单测层**。

## 五、仲裁修正

仲裁 agent 核对测试名、行号、命令和 mutation 失败值，未发现虚构证据。主要修正：

1. S1 有 3 处桩值恒等于期望，两个盲评都漏报。
2. S2/S3 报告中“桩值不恒等”的绝对化声明被自己的用例反证，应按“夸大”轻扣。
3. A 对 S3 的 F 满分偏松；B 对 S3 的 X−1 论据不实。
4. T2 中只有 D 明确发现 fixture 没有库存读写；A/B/C 都在设计无法落地的库存恢复用例。

仲裁后的稳定排序：

- **T1：B ≈ C > D > A**
- **T2：D ≥ B > C > A**

## 六、对 java-test 的判断

### 已验证的增益

| 能力 | 证据 |
|---|---|
| 真实反证闭环 | B/C/D 有“改坏→红→恢复→绿”，A 没有 |
| 假绿防御 | B/C/D 对 mock 实例、具体异常、金额口径、断言可失败性更稳 |
| compact 后恢复 | D 在新上下文靠 hook 注入重新加载技能并修复问题 |
| 集成层决策 | B/C/D 识别 `exists` 短路、事务陷阱、环境降级与盲区 |
| hook 时机 | C 证明“写完后注入”能拉动修订和交付验证 |

### 不能过度宣称的部分

1. **hook 不能保证测试代码首次就写对**：A 与 B/C/D 的 mutation 检出率都是 4/4。
2. **hook 不是硬门禁**：它不会阻止 agent 先写出重型集成测试，只能在写完后要求确认、收敛和验证。
3. **T2 不是真实数据库实跑**：本轮验证的是决策与假绿识别，不是 Testcontainers 真实执行。
4. **样本量有限**：每组一个生成 agent、两个盲评、一个仲裁；结论是方向性证据，不是统计显著性结论。

## 七、棘轮落地

根据本次实测，已对 `plugins/java-test/scripts/test-criteria-watch.py` 做两处小改并重跑回归：

1. 单测注入明确：**区分性用例 / BigDecimal 语义验证不算反证**。
2. 集成注入明确：
   - 只有用户明示「补集成测试 / 需求冻结 / 发版」才直接开始；
   - 仅提到真实依赖行为（唯一约束、事务回滚）属于推断，先确认；
   - 应用层 `exists` / 前置检查不替代 DB 约束。

回归结果：**10/10 PASS**，`sync-plugins.mjs --check` 通过，`git diff --check` 通过。

## 八、产物清单

- `eval-design.md` — 实验设计
- `test-prompts.md` — T1/T2 输入
- `rubric.md` — 盲评标准
- `fixture/` — 固定 Maven 被测工程
- `runs/A-D/` — 四组隔离生成产物
- `mutation-results.json` / `mutation-results.md` — 客观 mutation 结果
- `blind-A.md` / `blind-B.md` — 双盲评记录
- `arbitration.md` — 仲裁记录
- `run-mutation-eval.py` — mutation 复现脚本

## 九、复现要点

```bash
cd eval/java-test/darwin-validation-v2.4.0
python run-mutation-eval.py
```

该脚本会复制各组测试到临时工程，逐一替换 `PricingService` mutant 并执行 `mvn test`，输出 `mutation-results.md`。

## 十、最终结论

**不移除 java-test，也不把 hook 当作“生成正确测试”的保证。**

本次评估支持这样的定位：

> **技能正文负责判断什么算有效测试；hook 负责在写完测试后把判断和验证闭环重新送到 agent 眼前；真正的质量证据来自实际运行和反证。**

在当前模型已经能写出高质量 JUnit 测试的前提下，java-test 的稀缺价值是：**把“测试通过”与“测试有效”分开，并把后者变成可执行动作。**
