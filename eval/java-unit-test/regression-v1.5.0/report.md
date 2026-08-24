# java-unit-test 全量回归验证报告：v1.4.1 → v1.5.0（回归 + 对抗 + 实跑）

> **目的**：验证 v1.5.0 五处定向修复（description 触发信号化 / 06 重组为栈基线决策表 / 覆盖率立场定死 / guide-pro 依赖清零 / DoD fallback 口径统一）**无质量下降**且五处根因真被修掉。
> **日期**：2026-08-24
> **方法**：双盲评（标签反转）+ 仲裁 + 实跑（两个 Maven 项目），11 条 prompt（R1-R7 回归集 + A1-A4 对抗集）。
> **结论**：✅ **PASS** —— 回归集零退步（双盲评逐条核实），对抗集 4 条全部达预期，131 条行号证据 0 虚构；实跑 10/10 绿并揪出 1 个盲评双双漏掉的事实错误（已修），仲裁查漏 4 条全部处置。

## 一、验证设计

v1.4.1 → v1.5.0 改了 5 处（详见 commit ecf3c0f）。验证分三层：

| 层 | 执行者 | 内容 |
|----|--------|------|
| 双盲评 | Agent A（version1=v1.4.1 / version2=v1.5.0）、Agent B（versionA=v1.5.0 / versionB=v1.4.1，标签反转） | 11 prompt × 2 版本 × 9 维度打分 |
| 实跑 | 主 agent | 两个 Maven 项目：非 Spring（06 §1 坐标 + §3 全部关键写法）+ Spring Boot/JaCoCo（05 接入指引 + Branch 判据） |
| 仲裁 | Agent C | 证据核实 + 独立查漏 + 棘轮判定 |

## 二、盲评结果（两份独立报告方向完全一致）

### 总分

| | Agent A | Agent B | 一致性 |
|---|---|---|---|
| v1.4.1 | 912/1100 | 917/1100 | 尺度接近 |
| v1.5.0 | 1056/1100 | 1030/1100 | A 略宽松，差值才是关键 |
| **总差值（v1.5.0−v1.4.1）** | **+144** | **+113** | ✅ 同向，量级差 2.8% 属尺度噪声 |
| **回归集差值** | +45 | +29 | ✅ 无退步条目（R5 双报告持平，其余 6 条均升，R4 +14 最大） |
| **对抗集差值** | +99 | +84 | ✅ 占总量 70%+ |

### 单 prompt 方向（11/11 一致：10 升 1 平）

对抗集四条对应五处改动的根因，两 agent 独立命中 + 仲裁核实：

| Prompt | 直击根因 | v1.4.1 缺陷（仲裁核实为真） | v1.5.0 修复（行号可验） |
|---|---|---|---|
| A1 覆盖率立场 | 改动③⑤ | DoD L162"或按成本收益决定是否接入"与 05/06"用户问才提"互斥 → agent 摇摆；antipattern 四选项套餐无默认答案 | L161 机械判据（Branch Missed=0/清单全勾）+ 有/无 JaCoCo 双路径；antipattern 两场景各一默认答案 |
| A2 AssertJ 坐标 | 改动② | SKILL L44 指引"按 06 §1 引入 assertj-core"但 §1 全文无 org.assertj 坐标——指针悬空 | 06 §1 非 Spring 坐标块含 assertj-core 完整坐标 |
| A3 严重超标判据 | 改动① | 05 L108 指 `java-coding-guide-pro/references/12-complexity.md`——跨插件文件，只装 java-test 时不可达 | 判据自包含（认知复杂度 ≥~30 + 先特征测试再拆解），guide-pro 全套件 0 残留 |
| A4 触发令牌 | 改动④ | description 无代码令牌通道，纯贴代码求 review 场景匹配弱 | L9-13 令牌通道（@InjectMocks/@ParameterizedTest/mockStatic 等）全命中 |

## 三、实跑结果（10/10 绿 + 抓出 1 个事实错误）

详见 `live-run.md`。两个 scratch 项目（/tmp，不入 git）：

1. **非 Spring 项目**（junit-jupiter 5.11.0 + mockito-core 5.11.0 + assertj-core 3.26.3，scope=test）：**8/8 绿**。覆盖 06 §3 全部关键写法——标准注入 / mockStatic+try-with-resources（5.x 仅 mockito-core，版本分界实测成立）/ @ParameterizedTest / spy+doReturn / verify times / assertThrows / AssertJ extracting 分组断言。
2. **Spring Boot 3.5.0 + JaCoCo**：**2/2 绿**，`target/site/jacoco/index.html` 生成（前提：项目须有 main classes，纯 test-only 项目 report 无输出）；csv 判据可机械读取：`BRANCH_MISSED=2, BRANCH_COVERED=4`，与故意留的 2 个分支盲区精确对应——**DoD「Branch 列 Missed = 0」判据真实可执行**。

### 实跑揪出的事实错误（双盲评均漏且被反向加分）

v1.5.0 原 05 写"spring-boot-starter-parent 的 pluginManagement 已管理 JaCoCo 插件版本，可不写 `<version>`"。实测：无版本插件触发 Maven stability WARNING + 下载 maven-metadata 解析 latest release（0.8.15）；`help:effective-pom` 核实 parent pluginManagement **不含** jacoco 条目。**两份盲评都被通顺文本骗过（A 给 D4=12、B 称"可执行且不 staleness"）——文本可信度 ≠ 事实正确性，实跑环节的价值直接证成。**

## 四、仲裁结论（PASS）

- **证据真实性**：blind-A 65 条（62 精确 / 3 偏差 / 0 虚构）、blind-B 66 条（65 / 1 / 0）；两报告共同引用的 v1.4.1 四缺陷点全部真实、v1.5.0 修复全部落地。
- **方向一致性**：11 条 prompt 全部同向（10 升 1 平），回归集 R1-R7 逐条逐维度无退步。
- **独立查漏 4 条，全部处置**：

| 级别 | 问题 | 处置 |
|------|------|------|
| P1 | 05 pluginManagement 事实错误（快照缺陷） | ✅ 实跑发现并修复（05：插件 version 显式写 + 实测依据） |
| P2 | 06"坐标一律不写版本号"字面误导（会被读成 XML 省略标签） | ✅ 同批修复（"agent 现场填数字，不是省略 `<version>` 标签"） |
| P3 | description 丢 AssertJ/extracting 触发令牌（blind-A D1 11→9 属实） | ✅ 本轮顺手修（令牌通道补 `assertThat / extracting（AssertJ）`） |
| P3 | SKILL L50「DoD 锚点」三停止信号术语混搭（既有、非本轮引入） | ✅ 本轮顺手修（改「三条勾选项」；指向 05 节名的引用保留） |

- **查过无问题项**：「分支盲区清零」6 处写法统一、12 处 § 引用无悬空、01-06 无孤儿引用、原 06 §5 删除后无残留指针、extracting Tuple 编译期坑按 06 收录标准（fail loud 不收）合理不收。

## 五、棘轮判定

### ✅ PASS

1. 回归集 R1-R7 双盲评下无任何退步条目（最低持平 R5）。
2. 对抗集 A1-A4 全部达预期：五处改动的根因在 v1.4.1 中真实存在、在 v1.5.0 中全部正确修复，三层（两盲评 + 仲裁）确认。
3. 新引入问题（P1/P2/P3×2）全部非阻断且已修复——v1.5.0 未发布，修复随本 commit 落地，无线上影响。

**结论**：v1.5.0 相比 v1.4.1 是净改进，可保留、可发版（发布另行确认）。

## 六、方法论附记（下轮可用）

1. 双盲评抓结构性缺陷（四类全命中、0 虚构），实跑抓事实性错误（pluginManagement）——两通道互补，本轮均不可省。
2. 盲评提示词可加一条"对版本/坐标类事实主张降信任、要求引外部依据"，缓解本轮暴露的盲评局限。

## 七、产物清单

- `rubric.md` — 9 维度评分标准 + 对抗集判分锚点
- `test-prompts.md` — 11 条 prompt（R1-R7 + A1-A4）
- `snapshots/` — 4 份标签反转快照（version1/versionB=v1.4.1，version2/versionA=v1.5.0 原样，不含后续修复）
- `blind-A.md`、`blind-B.md` — 两份独立盲评
- `live-run.md` — 实跑记录（含事实错误发现与修复）
- `arbitration.md` — 仲裁报告（证据核实 + 查漏 + 棘轮）
- `report.md` — 本报告

## 八、复现指引

```bash
# 1. 快照已就绪（snapshots/ 四目录，标签对应见上）
# 2. 盲评 agent 拿 rubric + test-prompts + 两份标签快照 → blind-A/B.md
# 3. 实跑：非 Spring（06 §1 坐标 + §3 写法）与 Boot+JaCoCo 两项目（live-run.md 记录）
# 4. 仲裁 agent 拿两份盲评 + 真实对应关系 + live-run → arbitration.md
# 5. 棘轮判定：回归零退步 + 对抗达预期 + 新引入问题非阻断
```
