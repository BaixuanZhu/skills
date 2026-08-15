# 敏捷套件 test-prompts（v4.4.0 基线 rubric 评分用）

> 评估对象：`using-agile` / `agile-strategic` / `agile-backlog` / `agile-sprint`（敏捷套件，version 4.4.0）。
> 6 条 prompt 覆盖套件核心链路 + 本轮改造点（grill-me 选择题问询 / 分阶段产出 / Sprint 回填 / 变更分级 / ADR 依据标注）。
> 用途：供独立评分子 agent 做「效果维度」干跑（dry_run）——想象 agent 拿着技能执行该 prompt，判断能否产出合格结果。

## T1 · 全新项目初始化（using-agile happy path）

**用户说**：「帮我用敏捷方式管理这个新项目，项目是一个给独立开发者用的本地笔记工具。」

**验证点**：using-agile 应检测到无 `agile-docs/` → 建空骨架 + 最小项目画像采集（选择题形式，非开放式）→ 路由到 agile-strategic。不该替用户写任何业务文档。

## T2 · 产生产品愿景（agile-strategic 阶段 A，grill-me 核心验证）

**用户说**：「我要做一个给独立开发者用的任务管理 + 时间追踪工具，帮我先写愿景。」

**验证点**：agile-strategic 阶段 0 应**用选择题问询**（定位/核心原则/红线/指标等，给候选 + 推荐 + 「你来说」），而非开放式提问；关键决策落盘带来源标注；写完 VISION 即停，不跨阶段写架构。

## T3 · 拆 backlog（agile-backlog，分阶段验证）

**用户说**：「愿景定了，帮我把待办拆出来。」

**验证点**：agile-backlog 应**分阶段产出**（排序表+估点 → 详情+验收 → YAML），每阶段即停；估点用选择题确认（agent 给建议值+理由）；技术任务 T-NNN 关联 ADR；md/yaml 双文件一致。

## T4 · 规划 Sprint（agile-sprint，回填 + 容量验证）

**用户说**：「这轮 sprint 排一下，3 个人 5 个工作日。」

**验证点**：agile-sprint 应从 Backlog 顶部取条目；容量参数（专注系数）用选择题确认而非静默默认；Sprint 文件**内置「回填要求」段**（消费 agent 必读，明确 .done.yaml 义务）；任务清单纯列表无 checkbox。

## T5 · 需求变更（change-matrix 变更分级 + 下游影响评估验证）

**用户说**：「需求变了，之前定的『交付速度优先于完美架构』这条核心原则要改成『稳定性优先于交付速度』。」

**验证点**：using-agile 应引用 change-matrix 分级（这是 L2 同层变更，只重访受影响维度）；agile-strategic 就地更新 VISION 并做**下游影响评估**（改原则 → Backlog 排序是否受影响）；不整层重访。

## T6 · 架构选型 ADR（agile-strategic 阶段 B 验证）

**用户说**：「技术选型帮我定一下，团队只会 Java。」

**验证点**：agile-strategic 阶段 B 应做选型辩论（候选 + 推荐 + 裁决），而非把用户口述直接写成 ADR；ADR 严格 4 行结构（状态/背景/决策/后果），决策行带依据标注（用户拍板 vs agent 推荐）。
