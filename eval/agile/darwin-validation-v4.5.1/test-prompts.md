# v4.5.1 达尔文评测 —— 测试设计与 fixtures（2026-08-22）

> 对象：敏捷套件 4 技能（本地 v4.5.1 已 commit 未发布）。
> 方法：结构维度（1-7，/75）主 agent 静态打分 + 效果维度（8，/25）独立子 agent 实跑。
> 评测重点：**v4.5.1 三个真实场景升级是否在真实执行中生效**——
> ① .done.yaml 一键闭环（默认检查/关闭/同步/反馈处理）
> ② 多仓库交接契约（跨仓库任务组 → 交接文档）
> ③ Backlog 只定范围（需求探索 + 范围 vs 实现边界）
> 另含 feedback 处理（issue 转条目 / decision 停下裁决）与 3 条回归（初始化/backlog/sprint）。

## 一、fixtures（tmp/agile-eval-v4.5.1/）

公共战略层：VISION（电商后台：订单/会员/数据导出，前后端分离 api-server + web-app）、ARCHITECTURE、ADR-001（REST 契约）/ADR-002（订单状态机）、DOD。

| fixture | 状态 | 用途 |
|---|---|---|
| N1-done-closure | Sprint-001 未关闭 + .done.yaml（completed T-001/F-001、moved_next T-002、feedback: F-002 issue + T-002 reason） | N1 一键闭环 |
| N2-handoff | backlog 含跨仓库：T-003 订单接口[api-server] 被 F-002 订单列表页[web-app] 依赖 | N2 交接契约 |
| N3-scope | 完整战略层 + 单仓库 backlog（T-001/F-001/T-002/F-002） | N3 范围边界 / R3 sprint 回归 |
| N4-feedback | Sprint-001 已关闭 + .done.yaml（completed T-001/F-001 + feedback: decision 微信支付账单） | N4 feedback 裁决 |
| R-init | 空目录（无 agile-docs） | R1 初始化回归 |
| R-regress | 战略层齐、无 backlog | R2 backlog 回归 |

## 二、测试 prompt（新功能 4 条 A/B，回归 3 条 with_skill）

| # | 类型 | fixture | 用户输入 | 期望关键动作 |
|---|---|---|---|---|
| N1 | 新功能 A/B | N1-with/base | "这是上个 Sprint 消费 Agent 回填的执行结果文件 sprints/sprint-001-20260810.done.yaml，你处理一下。" | 默认执行闭环：DoD 核对→关 Sprint→同步 Backlog（completed 已完成 / moved_next 待办）→处理 feedback（F-002 issue 转新条目候选）→ .done.processed.yaml 留痕 |
| N2 | 新功能 A/B | N2-with/base | "开一个 Sprint，团队 2 人、5 个工作日，从 Backlog 取任务。" | 跨仓库识别：任务清单标 [repo: xxx] + 生成「交接契约」段（H-001：T-003 上游 → F-002 下游）+ 交接文档模板引用 |
| N3 | 新功能 A/B | N3-with/base | "客户提了新需求：运营想把订单数据导出成 Excel 文件。把它加进 Backlog。" | 需求探索（背景/场景/验收/边界/优先级/关联）+ 条目只写范围（验收行为/边界），不写实现（框架/SQL/代码结构） |
| N4 | 新功能 A/B | N4-with/base | "这是上个 Sprint 的回填文件 sprints/sprint-001-20260810.done.yaml（Sprint 已关闭），处理一下。" | 同步 completed → Backlog；decision feedback 停下请用户裁决（不静默落盘） |
| R1 | 回归 with | R1-with | "新项目，帮我开始用敏捷方式管理。做电商后台管理系统，Java + Vue，2 人团队，全新项目。" | 建骨架 + 画像采集（选择题）+ 不写业务文档 |
| R2 | 回归 with | R2-with | "把待办拆出来，排出优先级。" | 分阶段产出 + MoSCoW + T-NNN 关联 ADR + 范围不写实现 |
| R3 | 回归 with | R3-with | "开一个 Sprint，团队 2 人、5 个工作日。" | 容量参数确认 + Sprint 目标反问 + 回填要求段 + 单仓库无交接契约段 |

## 三、判定口径

- 新功能 with_skill：关键动作齐 → 高分；缺失 → 记录缺项。
- baseline：看是否落入套件反模式（不默认闭环 / 直接写实现 / 无交接概念 / 静默处理决策）——量化 skill 增量。
- 回归：with_skill 行为与 v4.4.1 基线一致（无回退）即可。
