# 敏捷套件 test-prompts（v4.4.1 rubric 评分用）

> 评估对象：`using-agile` / `agile-strategic` / `agile-backlog` / `agile-sprint`（敏捷套件，本地 v4.4.1 未发布）。
> 8 条 prompt = 核心链路 6（T1–T6，回归）+ 本轮改动 2（T7–T8：.done 闭环链路 / strategy-conflict 去重守卫）。
> 用途：维度 8「实测表现」——独立子 agent 分别以 with_skill / baseline 执行同一 prompt，对比输出质量。

## T1 · 全新项目初始化（using-agile happy path）

**用户说**：「帮我用敏捷方式管理这个新项目，项目是一个给独立开发者用的本地笔记工具。」

**验证点**：using-agile 检测到无 `agile-docs/` → 建空骨架 + 最小项目画像采集（**选择题形式**，非开放式）→ 路由到 agile-strategic。**不该替用户写任何业务文档**（VISION/ARCHITECTURE/ADR/PRODUCT-BACKLOG）。

## T2 · 产生产品愿景（agile-strategic 阶段 A）

**用户说**：「我要做一个给独立开发者用的任务管理 + 时间追踪工具，帮我先写愿景。」

**验证点**：阶段 0 用**选择题问询**（定位/核心原则/红线/指标，给候选 + 推荐），非开放式提问；关键决策落盘带来源标注（用户给出 / agent 推断 / agent 推荐待确认）；写完 VISION **即停**，不跨阶段写架构。

## T3 · 拆 backlog（agile-backlog，分阶段）

**用户说**：「愿景定了，帮我把待办拆出来。」

**验证点**：分阶段产出（排序表+估点 → 详情+验收 → YAML），每阶段即停；估点用选择题确认；技术任务 T-NNN 关联 ADR；md/yaml 双文件一致。

## T4 · 规划 Sprint（agile-sprint，容量 + 回填）

**用户说**：「这轮 sprint 排一下，3 个人 5 个工作日。」

**验证点**：从 Backlog 顶部取条目；容量参数（专注系数）用选择题确认**而非静默默认**；Sprint 目标可陈述（反问）；Sprint 文件内置「回填要求」段（明确 .done.yaml 义务）。

## T5 · 需求变更（change-matrix 分级 + 下游影响评估）

**用户说**：「需求变了，之前定的『交付速度优先于完美架构』这条核心原则要改成『稳定性优先于交付速度』。」

**验证点**：using-agile 引用 change-matrix 分级（这是 **L2 同层变更**，只重访受影响维度）；agile-strategic 就地更新 VISION 并做**下游影响评估**（改原则 → Backlog 排序是否受影响）；不整层重访。

## T6 · 架构选型 ADR（agile-strategic 阶段 B）

**用户说**：「技术选型帮我定一下，团队只会 Java。」

**验证点**：选型辩论（候选 + 推荐 + 裁决），非把用户口述直接写成 ADR；ADR 严格 4 行结构（状态/背景/决策/后果），决策行带依据标注（用户拍板 vs agent 推荐）。

## T7 · 关 Sprint 闭环（agile-sprint + agile-backlog 协同，本轮改动）

**用户说**：「Sprint 做完了，帮我关闭并同步回 Backlog。」（前提：`sprints/sprint-001-*.done.yaml` 已由消费 Agent 回传）

**验证点**：agile-sprint 读 .done → **DoD 逐项核对（闭环检查 checklist）** → 文件头标注执行结果来源 → 状态改「已关闭」→ 提示完整闭环：`.done.yaml` 由入口下次激活检测 → 路由 agile-backlog 同步 → **同步后改后缀 `.done.processed.yaml` 留痕（不删除，防重复同步）**。全链路终态表述完整，不含「同步即止」的断裂。

## T8 · 冲突去重（strategy-conflict 去重守卫，本轮改动）

**用户说**：「先写愿景。」（前提：using-agile 已因检测到多份矛盾输入生成 `agile-docs/STRATEGY_CONFLICT.md` 待裁决）

**验证点**：agile-strategic 激活时检测到 `STRATEGY_CONFLICT.md` **已存在** → **跳过不重复生成**，仅引用其内容继续等待用户裁决；**禁止覆盖已有裁决记录**。
