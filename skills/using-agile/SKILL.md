---
name: using-agile
slug: using-agile
displayName: 敏捷管理入口
description: |
  当用户说"开始项目""敏捷""Sprint""待办""Backlog""用户故事""迭代""架构决策""ADR""C4""需求变了""要改故事""依赖检查"或进入含 agile-docs/ 目录的项目时触发。不适用于：纯运维部署、需要与 Jira/Trello 深度集成。
agent_created: true
version: 4.3.0
---

# 敏捷管理入口 (Using Agile)

## 1. 定位

本技能是敏捷套件的**唯一入口**，承担三件事：
- **初始化**：项目无 `agile-docs/` 时，建空骨架 + `DOD.md` 模板 + `interfaces/sprint-schema.yaml`。
- **检测路由**：项目有 `agile-docs/` 时，扫描三层状态 → 输出状态表 → 逐层询问"更新 or 继续" → 路由到对应业务技能。
- **变更协调**：当用户说"需求变了"时，引用 `references/change-matrix.md` 评估影响面 → 路由到对应业务技能就地更新。

**本技能绝不自己 Write 任何业务 `.md` 文档**（VISION / ARCHITECTURE / ADR / PRODUCT-BACKLOG / Sprint 等）。所有业务文档由对应业务技能在用户确认后产出。

## 2. 三层模型与业务技能路由

| 层 | 产出物 | 负责技能 |
|----|--------|----------|
| **战略与约束层** | 愿景 VISION、架构图 ARCHITECTURE、决策 ADR | `agile-strategic`（两阶段一体化） |
| **执行层** | DoD、PRODUCT-BACKLOG（.md + .yaml）、Sprint（规划/关闭） | `agile-backlog` / `agile-sprint` |
| **跨层（变更协调）** | 变更传播矩阵评估 + 路由 | `using-agile`（本技能，引用 `change-matrix.md`） |

**Sprint 规划由 `agile-sprint` 承担**：纯规划器（规划→DoD关闭），不含执行态追踪。关闭后保留作历史，闭环即止。

## 3. 激活流程（有 agile-docs/ 时）

1. 检测 `agile-docs/` 下各文件存在性：
   - `VISION.md` + `ARCHITECTURE.md` + `ADR.md` → 战略层
   - `PRODUCT-BACKLOG.md` + `PRODUCT-BACKLOG.yaml` → 执行层待办池
   - `DOD.md` → 完成定义
   - `sprints/` 下未关闭的 `.md` → 活跃 Sprint
2. **双文件一致性检查**：若 `PRODUCT-BACKLOG.md` 和 `.yaml` 均存在，对比 id 集合和 status 是否一致。不一致 → 停下报告差异（列出 id 缺失/status 不一致的条目），请用户确认以哪份为准后再继续路由。
3. **额外检测 — .done.yaml**：扫描 `sprints/*.done.yaml`
   - 存在 + 对应 Sprint 文件状态为"已关闭" → 路由决策表追加一行"待同步到 Backlog"（自动路由到 `agile-backlog` 执行同步）
   - 存在 + 对应 Sprint 文件状态非"已关闭"（即仍活跃） → 提示"消费 Agent 已回传结果，是否先关 Sprint？"，确认后路由到 `agile-sprint`
4. 输出三层状态表（见 `references/status-routing.md`）。
5. **逐层询问**"更新 or 继续下一步"（话术见 reference）。
6. 按用户选择路由到对应业务技能，**不自己写**。

## 4. 初始化流程（无 agile-docs/ 时）

1. **最小项目画像采集**（下游三个业务技能探询的公共输入，提问节奏遵循 `references/probing-protocol.md §三`，分两轮）：
   - 第一轮：项目名称 / 一句话定位 / 项目类型（Web 应用、API 服务、工具库…）
   - 第二轮：团队人数与主要技能栈 / 全新项目还是存量代码
   - 采集结果写入 `agile-docs/DOD.md` 头部「项目画像」备注区，供下游技能读取；用户明确跳过的项标 `{待确认}`
2. 建 `agile-docs/` 目录骨架（仅目录 + `DOD.md` 模板 + `interfaces/sprint-schema.yaml`）+ 项目根建 `sprints/` 空目录。**不创建业务文档占位文件**（VISION/ARCHITECTURE/ADR/PRODUCT-BACKLOG.* 由对应技能在用户确认后产出）——路由以文件存在性为准，占位文件会误判状态已就绪。
3. 生成 `agile-docs/DOD.md` 模板（含项目画像备注）+ `agile-docs/interfaces/sprint-schema.yaml`。
4. **停**，问："骨架已就绪。是否调用 `agile-strategic` 产出愿景？"
5. ❌ **不写任何业务文档**（VISION / ARCHITECTURE / ADR / PRODUCT-BACKLOG / Sprint）。不生成 meta.json。

## 5. 写前战略门禁（最高优先级）

在路由到任何业务技能产出前，若检测到以下情况**立即停下**，按 `references/strategy-conflict-template.md` 生成 `STRATEGY_CONFLICT.md`，用表格列冲突/歧义清单请用户裁决：
- 多份输入文档战略方向矛盾；
- 需求存在未界定的关键规则（MVP 边界、核心流程等）；
- 待写内容与现有 Vision / ADR 冲突。

**缺失即问**：若目标层的必答话题存在未覆盖项（用户没提 ≠ 不需要），同样属于门禁触发，但动作是**停下探询**而非停下裁决，提问/追问规则见 `references/probing-protocol.md`。

在用户裁决前，不写任何产物文件（仅允许建目录骨架或写 `STRATEGY_CONFLICT.md`）。详见 `references/gate-protocol.md`。

## 6. 变更协调

当用户说"需求变了""要改故事""依赖检查"时：

1. 引用 `references/change-matrix.md` 识别变更类型与影响面
2. 用表格呈现"改 X 会影响 Y、Z"，请用户确认范围
3. 用户确认后，**路由到对应业务技能就地更新**（本入口不自己改业务正文）：
   - 改 VISION / ARCHITECTURE / ADR → `agile-strategic`
   - 改 PRODUCT-BACKLOG 任务 / 加新任务到 Backlog → `agile-backlog`（即使 Sprint 执行中提出，不路由到 agile-sprint）
   - 改 Sprint 规划 / 关闭 → `agile-sprint`（执行期状态变更由消费 Agent 自行处理，不进规范层）
   - 改 DoD 模板 → 本入口（DoD 模板就是本技能生成的）
   - 同步 Sprint 执行结果到 Backlog → `agile-backlog`（检测 .done.yaml 文件后触发）
4. **跨层变更按依赖顺序逐层路由**：如改 VISION 原则影响 Backlog 排序 → 先 agile-strategic 改 VISION，再回本入口做状态检测，再路由 agile-backlog 改标注（不要并行触发多个业务技能）
5. **不重新生成全部 `agile-docs/` 内容**——只改受影响文件
6. **ADR 走替代而非 in-place**（门禁 ②，详见 `gate-protocol.md`）

## 7. 硬约束

- ❌ **绝不自己 Write 业务 `.md`**（VISION / ARCHITECTURE / ADR / PRODUCT-BACKLOG / Sprint）。
- ✅ 只做：检测状态 → 询问 → 路由 → 变更协调（引用矩阵，不直接改业务正文）。
- ✅ 每次激活后**逐层询问**"更新 or 继续"，不替用户决定走向。
- ✅ 渐进式：业务技能产出即停；下一步须用户再次调用本技能或下个业务技能。
- ✅ 路由到业务技能时提示其遵循 `references/probing-protocol.md`（探询协议，与 `references/gate-protocol.md` 门禁协议同级配套）。
