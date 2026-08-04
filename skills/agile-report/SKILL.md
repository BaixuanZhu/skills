---
name: agile-report
slug: agile-report
displayName: 阶段进度汇报
description: |
  当用户说"汇报""进度报告""给甲方看""给领导看""阶段总结""生成报告""可视化进度"或需要把 Sprint/Backlog 完成情况转为图表 HTML→PDF 对外汇报时触发。按需衍生，不属于敏捷流程必须环节——只在需要对外汇报时调用。支持无 agile-docs/ 时降级读 git log。
agent_created: true
version: 1.0.0
dependencies:
  - skill: using-agile
    reason: 提供 DOD.md 项目画像 + agile-docs/ 目录骨架
  - skill: agile-backlog
    reason: PRODUCT-BACKLOG.yaml/.md 是全局进度的数据源
  - skill: agile-sprint
    reason: sprints/*.md + *.done.yaml 是各 Sprint 完成度数据源
---

# 阶段进度汇报 (Agile Report)

## 0. 前置条件（缺失则降级，不回退路由）

本技能是**按需衍生**技能，不要求项目跑完整敏捷流程。按数据源齐全度三态降级：

| 状态 | 数据源 | 产出 |
|------|--------|------|
| ① 完整 | `agile-docs/`（DOD + BACKLOG.md + .yaml）+ `sprints/*.md` + `*.done.yaml` | 完整图表报告（Sprint 趋势 + 燃尽 + 待办分布） |
| ② 部分 | `agile-docs/` 有但 `sprints/` 无 `.done.yaml` | "计划 vs 在途"报告（Backlog 进度 + 已规划 Sprint，无完成度） |
| ③ 降级 | 无 `agile-docs/` 或无 `sprints/` | git log 纯文本报告，封面须标"数据来源：git log（简化版）" |

**绝不因数据不全就拒绝产出**——降级并明确标注来源即可。降级判据与 git log 解析规则见 `references/report-rules.md §三`。

## 1. 定位

本技能是敏捷套件的**按需衍生层**，非流程闭环环节。`using-agile` 的三层模型（战略/执行/变更协调）不包含本技能——它靠自己的触发词激活，只在用户需要对外汇报时调用。

**产物**：`reports/stage-report-{YYYYMMDD}.html` + `.pdf`（项目根 `reports/` 目录，与 `agile-docs/`、`sprints/` 平级）

**受众**：甲方/领导（非技术方）。视觉编码面向"感知进度"，不追求技术准确——故事点在报告里必须转成"任务量"，ADR 转成"技术决策记录"。术语映射见 `references/chart-config.md §三`。

**只读不写**：本技能读取 `agile-docs/` 与 `sprints/` 所有产物，但**绝不修改**它们（所有权分属 using-agile/agile-backlog/agile-sprint）。

## 2. 数据采集与范围确认

### 2a. 机械扫描（agent 自检，不需用户参与）

- 扫描 `agile-docs/` 与 `sprints/` 文件存在性 → 判定降级态（§0 三态表）
- 若处于状态 ①②：执行**双文件一致性校验**（PRODUCT-BACKLOG.md 与 .yaml 的 id 集合 / 条目数 / 同 id 的 priority+status 是否一致）——复用 `agile-backlog/references/backlog-rules.md §七` 规则；不一致 → 停下报告差异，请用户确认以哪份为准
- 若处于状态 ①：遍历 `sprints/sprint-*.md`，按文件头 `- 状态:` 行筛"已关闭"，按文件名日期排序

### 2b. 范围探询（与用户必走，姿态遵循 `using-agile/references/probing-protocol.md`）

确认阶段范围——以下任一方式，由用户选：
- **最近 N 个已关闭 Sprint**（默认 N=3，即"最近一个阶段"）
- **日期范围**（如 2026-06-01 ~ 2026-08-01）
- **里程碑名**（用户自定义阶段名，如"一期交付"）

范围确认后输出数据源清单（哪些 Sprint 文件、哪些 Backlog 条目将纳入），请用户确认再进入产出。

## 3. 产出（按环节，每环节写完即停）

### 环节 A：数据聚合

按 `references/report-rules.md` 计算以下指标：
- **阶段整体完成率**：`Σ(各 Sprint completed 数) / Σ(各 Sprint 任务总数) × 100%`
- **各 Sprint 完成率**：单个 Sprint 的 completed / 任务总数
- **承诺 vs 完成点数**：Σ承诺点 vs Σ完成点（点数从 PRODUCT-BACKLOG.md 按 id 回读，**YAML 不含 point 字段**）
- **三态分布**：completed / moved_next / 未执行（清单内但两列表都无）
- **Backlog 优先级分布**：从 .yaml 统计 Must/Should/Could 各自的 待办/已完成 数

聚合完输出数据表（不写文件），列计算依据，请用户确认后进入环节 B。

### 环节 B：生成 HTML

套 `references/report-template.md` 骨架，注入 `references/chart-config.md` 的 ECharts 配置：
- 每个 section 填入环节 A 的聚合数据
- 图表容器 id 必须与 chart-config.md 的配置一一对应
- **术语去技术化**：写入 HTML 前强制按 `chart-config.md §三` 映射表转换（故事点→任务量、Sprint→迭代周期…）

产物：`reports/stage-report-{YYYYMMDD}.html`（A4 纸张样式，浏览器打开即所见即所得）。写完停，进入环节 C 询问导出需求。

### 环节 C：可选导出（PNG/PDF）

HTML 是唯一必产物。写完 HTML 后**询问用户**："需要转成图片（PNG）或 PDF 吗？"
- 选 PNG → `npx playwright screenshot --channel msedge --wait-for-timeout 2000 --full-page ...`（见 toolchain §三）
- 选 PDF → `npx playwright pdf --channel msedge --wait-for-timeout 2000 --paper-format A4 ...`（见 toolchain §四）
- 都不要 → 仅交付 HTML
- Playwright 不可用 → 提示浏览器打开 HTML 手动 Ctrl+P 导出（见 toolchain §五）

详细命令、安装、陷阱见 `references/toolchain.md`。

## 4. 写完即停（结构化审阅）

输出决策点确认清单：
- **阶段范围**：N 个 Sprint / 日期范围 / 里程碑名
- **数据源清单**：纳入的 Sprint 文件、Backlog 条目数
- **关键指标**：阶段整体完成率、承诺 vs 完成点数、降级态（若适用）
- **导出需求**：仅 HTML / HTML+PNG / HTML+PDF（按用户环节 C 的选择）

问"**重新生成**（换范围/换数据）还是**交付**（确认输出）？"。

## 5. 硬约束

- ✅ 必产物仅 `reports/stage-report-{YYYYMMDD}.html`；PNG/PDF 按用户环节 C 选择才生成；❌ **绝不修改** `agile-docs/` 与 `sprints/` 任何文件（所有权分属上游技能）。
- ✅ 数据不全时降级产出并标注来源（"数据来源：git log（简化版）"）；❌ **不编造**未采集的数据（缺 `.done.yaml` 就如实显示"完成度未知"，不脑补数字）。
- ✅ 报告面向非技术方，术语强制按 `chart-config.md §三` 去技术化；❌ **不在报告中暴露** 故事点/T-NNN/MoSCoW/ADR/DoD 等内部黑话原文。
- ✅ 图表配色按完成率三色（红<60% / 黄 60-85% / 绿>85%），中文标注；❌ 禁用纯英文 legend。
- ✅ 按需触发，不主动建议"该汇报了"——汇报时机由用户决定。

## 6. 工具链与导出

HTML 生成（必产）+ 可选 PNG/PDF 导出的工具链见 `references/toolchain.md`。CSS/图表配置见 `report-template.md` + `chart-config.md`。

**硬性前提**：
- ECharts 必须 `renderer: 'svg'`（矢量）——canvas 栅格化截图/打印会糊
- HTML body 固定 A4 内容宽度（186mm）居中——图表 `width:100%` 不溢出，屏幕预览=打印效果
- PNG/PDF 导出复用系统 Edge（`--channel msedge`，零浏览器下载，为大陆网络环境设计）
