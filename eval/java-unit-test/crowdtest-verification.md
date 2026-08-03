# java-unit-test 众测反馈验证（达尔文流程）

> 目的：用达尔文「实测验证 + 可证伪」原则，验证 8 条众测反馈**是否在真实使用中真的发生**，而非读文档脑补。
> 方法：每条反馈设计 test-prompt，模拟真实用户场景，**实际执行**当前 SKILL.md 流程，记录缺陷是否复现。
> 判定标准：✅ 复现（反馈成立）/ ⚠️ 部分复现 / ❌ 未复现（反馈不成立或描述偏差）。

## 测试基线

- 被测技能：`skills/java-unit-test` @ version 1.0.0
- 测试日期：2026-08-02
- 测试者：主 agent（遵循 SKILL.md 指引执行，不脑补）

## 测试 prompt 设计

每条反馈 → 1 个能**唯一触发该反馈所描述痛点**的 prompt。

### T1（反馈1·JaCoCo集成）
```
我在写一个 Spring Boot 项目，想给单元测试加覆盖率工具，帮我看怎么接入。
```
**验证点**：按 SKILL.md 流程，能否在合理步骤内拿到可用的 JaCoCo 接入方案。

### T2（反馈2·遗留代码）
```
我接手了一个五年前的 Java 项目，有个 Service 类 400 行，里面全是 static 调用和 new 出来的依赖，
现在要给它补单元测试。我该怎么开始？
```
**验证点**：SKILL.md 是否给出"遗留代码不可直接设计用例、需先建保护性测试再重构"的策略。

### T3（反馈3·review checklist）
```
我刚写完一批单元测试，提交前想自查质量。有没有一份测试代码的 review 清单？
```
**验证点**：SKILL.md 是否有可直接勾选的 review checklist。

### T4（反馈4·快速入门）
```
我第一次接触单元测试规范，这个技能文件很多，我该从哪开始看？
```
**验证点**：SKILL.md 是否给新人明确的入门路径（先看哪份、何时看哪份）。

### T5（反馈5·ArchUnit跨层）
```
我有个 Controller 直接调了 Repository，绕过了 Service 层。
怎么用测试或工具防止这种跨层违规？
```
**验证点**：SKILL.md 的 C-CHECK 在这个**最常见的真实场景**下能否触发、给出可用规则。

### T6（反馈6·停止信号可执行性）
```
我设计完用例了，按规范说要看"三个停止信号"判断够不够。
这三个信号具体怎么操作检查？我跑完测试后该看什么？
```
**验证点**：从 SKILL.md 跳到 references/05 后，能否在合理步骤内找到"怎么验 C1 无盲区"等执行动作。

### T7（反馈7·AI生成测试自欺）
```
用 AI 一次性给我生成了一批单元测试，看起来四维度都覆盖了。
我直接用这批测试可以吗？有没有风险要注意？
```
**验证点**：SKILL.md 是否警告"AI 生成测试的 happy path 偏向 / 自欺风险"。

### T8（反馈8·Mock复杂场景）
```
我要测一个 Service，它内部调用了 MyBatis-Plus 的链式查询 lambdaQuery().eq().one()，
还有个工具类的静态方法。这种复杂场景 Mock 怎么写？给个范例。
```
**验证点**：SKILL.md 是否有链式调用 mock + 静态方法重构的前后对比范例。

---

## 第二轮实测结论（2026-08-03，达尔文流程）

> 用达尔文「实测验证 + 独立盲评 + 棘轮」原则重做：代码类反馈建真实 Maven 工程跑，流程类反馈启动独立子 agent 盲测（不预设结论）。

### 8 条反馈的可证伪判定

| 反馈 | 判定 | 证据 |
|---|---|---|
| 1 JaCoCo 集成 | ⚠️ 描述偏差，藏真问题 | 配置块原样照搬能跑，全绿时 `index.html`+`jacoco.csv` 正常生成；**但实测发现测试失败时 BUILD FAILURE 中断 report phase，报告不生成**——技能未写明 |
| 2 遗留代码 | ✅ 部分成立 | 独立 agent 确认：点名的 `new`/static 痛点有答案；但"遗留代码"场景（特征测试/安全重构/大类切片）未专门讨论 |
| 3 review checklist | ⚠️ 基本不成立 | 独立 agent 确认：S/A 表 13 条 + 四维度 + FIRST + 三停止信号**素材齐全**，仅缺单页汇编（是组装不是知识缺口） |
| 4 快速入门 | ⚠️ 基本不成立 | 独立 agent 确认：01"必读"标注+路由表+5步流程+"05是核心"提示**路径清晰**，仅缺显式线性文字 |
| 5 ArchUnit 跨层 | ✅ 成立（强证据） | 真实违规代码 + 一行规则 `noClasses()...dependOn...` **精确抓 3 处违规**（构造器/字段/方法调用）；SKILL 只给坐标没给规则 |
| 6 停止信号 | ✅ 成立 | 独立 agent 逐信号拆解：信号2（分支）操作链完整；**信号3（等价类无遗漏）只有判据无操作**；`jacoco.csv` 实测确有 `BRANCH_MISSED/COVERED` 列 |
| 7 AI 自欺 | ✅ 成立（技能盲点） | 独立 agent 全文搜索：**唯一"AI"在 `01:7`**（泛指设计能力）；无 LLM/批量生成/自欺警告；技能定位（让 AI 写一致测试）与风险警告不闭环 |
| 8 Mock 复杂场景 | ✅ 成立 | 真实 MyBatis-Plus 链式代码：测试**靠经验补 `any(wrapper)` 才跑通**；`grep lambdaQuery/链式/selectOne/wrapper` 全技能零命中 |

### 实测工程证据

工程：Spring Boot 3.2.5 + MyBatis-Plus 3.5.5 + ArchUnit 1.3.0 + JaCoCo 0.8.12。

**ArchUnit 抓跨层违规**（T5）：
```
Architecture Violation - Rule 'no classes that reside in a package '..web..'
should depend on classes that reside in a package '..repo..'' was violated (3 times):
- Constructor <OrderController.<init>(OrderRepository)> has parameter of type <OrderRepository>
- Field <OrderController.orderRepository> has type <OrderRepository>
- Method <OrderController.get(long)> calls method <OrderRepository.findById(long)>
```

**JaCoCo 覆盖率 CSV**（T1/T6 反向校验实证，`jacoco.csv` 列）：
```
GROUP,PACKAGE,CLASS,...,BRANCH_MISSED,BRANCH_COVERED,LINE_MISSED,LINE_COVERED,...
darwin-test,com.demo.service,UserService,...,0,2,0,12,...
darwin-test,com.demo.web,OrderController,...,0,0,4,0,...   ← 0 覆盖=反向校验暴露盲区
```

**链式 mock**（T8）：`when(mapper.selectOne(any(LambdaQueryWrapper.class))).thenReturn(null)` —— 2 测全绿，但写法技能未教。

### v1.1 改进对照（棘轮验证）

改进后重建工程，**照搬新加到技能的范例**重跑：

| 反馈 | 改进位置 | 棘轮验证结果 |
|---|---|---|
| 5 ArchUnit | `SKILL.md` C-CHECK 补 2 条规则范例 | 照搬规则抓到同样的 3 处违规 ✅ |
| 7 AI 自欺 | `SKILL.md` S/A 表新增 1 行 S 级反模式 | （规则类，grep 确认存在）✅ |
| 8 Mock 链式 | `references/06` 补链式 stub + 静态重构范例 | 照搬范例 UserServiceTest **2 测全绿** ✅ |
| 6 停止信号 | `references/05` 三信号各补执行动作 | 措辞对齐实测的 `jacoco.csv` 列名 ✅ |
| 1 JaCoCo | `references/05` 补"测试不过报告不生成" | 描述对齐实测的 BUILD FAILURE 中断现象 ✅ |
| 2 遗留代码 | `references/05` 新增节 + 交叉引用 `java-coding-guide-pro/12-complexity.md` | 交叉引用目标存在（`12-complexity.md:148,157`）✅ |
| 3/4 | `SKILL.md` 补新手导航表（隐式汇编 S/A 入口） | 导航表所有指针指向存在的文件 ✅ |

**棘轮结论**：所有新增代码范例实测可跑、无悬空指针、无内容重复。v1.1 改进**只保留经实测验证的内容**，符合达尔文棘轮原则。

### 净增量

- `SKILL.md`：+新手导航表(8行) / +S级AI反模式(1行) / +C-CHECK规则范例(代码块) / 版本 1.0.0→1.1.0
- `references/05`：+三停止信号动作 / +JaCoCo坑提示 / +遗留代码节(~15行)
- `references/06`：+链式mock范例 / +静态重构前后对照
- 无新文件，marketplace.json 不变。
