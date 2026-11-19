# java-test v2.3.0 / v2.4.0 + hook 达尔文评估设计

> 目的：验证**技能正文**与**分层短注入 hook** 在 AI 写 Java 测试时的实际增益，而非自评文档质量。
> 日期：2026-11-19
> 原则：隔离 agent 产出、双盲判分、可复现的变异检出率、棘轮只保留实测改进。

## 一、被测对象

- `skills/java-unit-test` 2.3.0：纯单测判据、交付前运行与反证。
- `skills/java-integration-test` 2.4.0：三决策、集成层激活闸门、环境盲区与交付验证。
- `plugins/java-test/hooks/hooks.json` + `scripts/test-criteria-watch.py`：PostToolUse 分层短注入。

## 二、固定 fixture

`fixture/` 是一个最小 Maven 工程，刻意放入以下**可客观检出**的陷阱：

| 陷阱 | 被测代码 | 合格测试应命中 |
|---|---|---|
| BigDecimal 金额口径 | `quote` 返回 `setScale(2, HALF_UP)` | 金额断言不能只比 `equals`；应能识别 scale / 舍入口径 |
| 异常过宽 | `quote` 对空 sku、非法数量、缺价分别抛具体异常 | 不得只断言 `RuntimeException` |
| mock 注入 | `PricingService` 依赖 `PriceRepository` | mock 必须注入构造器使用的实例，且 stub 真正被调用 |
| 无断言/恒真 | 自由生成的测试 | 调用后必须有结构化断言，桩值不能等于期望后不 verify |
| 四维覆盖 | `quote` / `allocate` | 正向、反向、边界、异常至少各有代表用例 |

`OrderService` + `OrderRepository` 只用于**集成层激活判断**，不要求本机起数据库。

## 三、四个实验组

| 组 | 条件 | 要回答的问题 |
|---|---|---|
| **A** | 无技能、无注入 | 现代 Java 模型裸写测试的基线 |
| **B** | 提供 `java-unit-test` SKILL + `references/01-pitfalls.md` | 技能正文本身是否提高假绿识别与交付验证 |
| **C** | 先只写测试；写完后收到 hook 分层短注入 | hook 是否把 agent 拉回完整技能与反证闭环 |
| **D** | 模拟 compact：新上下文只剩任务摘要，再收到 hook 注入 | compact 后 hook 是否重新武装规范 |

A/B/C/D 都必须遵守：**只创建/修改 `src/test/java` 下的测试文件；不得改 `src/main/java`、`pom.xml`**。

## 四、测试任务

### T1 单测主任务

```
给 PricingService 写单元测试，覆盖 quote(String sku, int quantity)
和 allocate(BigDecimal amount, int people)。项目已有 JUnit 5、Mockito、AssertJ。
```

### T2 集成层激活任务

```
团队没有专职测试。给订单模块补测试，确保数据库唯一约束真的拦住重复订单号，
并且写订单失败后库存能恢复。项目当前只有 mvn test。
```

T2 **不要求写文件**，只要求给出动作说明：是否新增集成测试、放哪层、用什么跑、盲区是什么。

## 五、硬指标（T1）

1. **原实现可跑**：生成测试在原始 fixture 上必须通过。
2. **变异检出率**：将 `PricingService` 替换为 4 个 mutant，统计被测试杀死的数量：
   - M1：满 100 折扣分支失效；
   - M2：非法数量改为返回 `0.00` 而不是抛异常；
   - M3：结果 scale 从 2 改为 0；
   - M4：除法舍入从 `HALF_UP` 改为 `DOWN`。
3. **假绿判据静态命中**：mock 实例、具体异常、BigDecimal 口径、结构化断言、四维覆盖。
4. **交付证据**：是否实际运行测试、是否做“改坏变红→恢复变绿”反证、无法运行是否披露。

## 六、盲评 rubric（T1，满分 100）

| 维度 | 分值 | 判分锚点 |
|---|---:|---|
| M 变异检出 | 30 | mutant 杀死 0/4=0，1/4=7，2/4=15，3/4=23，4/4=30 |
| F 假绿防御 | 25 | mock 实例 6；具体异常 6；BigDecimal/舍入 7；无恒真/空断言 6 |
| C 覆盖设计 | 15 | 正向/反向/边界/异常四维各 3，分支/等价类说明 3 |
| V 验证闭环 | 20 | 实际运行 8；执行证据 4；反证 6；无法运行披露 2 |
| R 清晰与克制 | 10 | 回复准确、无夸大、无越界修改 10 |

## 七、T2 rubric（满分 100）

| 维度 | 分值 | 判分锚点 |
|---|---:|---|
| G 激活闸门 | 30 | 无明示信号时先确认；不擅自铺重型集成测试 |
| L 分层判断 | 25 | 唯一约束/事务回滚归集成层；分支矩阵不塞集成层 |
| E 环境与盲区 | 20 | Testcontainers/实库/替身路径与不可验证项说明 |
| X 执行与断言 | 15 | `verify/check`、结构化断言、失败判红 |
| R 清晰与克制 | 10 | 不把 curl/肉眼当测试，不虚构已执行 |

## 八、独立性与防自评

- 生成 agent 不得读取 `I:/GitDownload/skills` 下的技能、eval 或其他组产物。
- A/B/C/D 产物落盘后，启动两个互不知情的盲评 agent，只看匿名快照。
- 仲裁 agent 核对引用行号、变异结果和判分尺度，再查漏。
- 主 agent 只负责组装、运行 mutant、修复评估工具问题，不给生成结果打印象分。
