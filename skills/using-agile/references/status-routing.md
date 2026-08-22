# 状态检测与路由（using-agile 参考）

## 一、路由决策原则

路由决策以 `agile-docs/` 下文件存在性为准，不依赖中心化状态文件。文件存在即状态，不存在即需生成。

**路由注意 — .done.yaml**：扫描 `sprints/*.done.yaml` 是激活流程第 1 步（必做）。存在即默认执行回填闭环（DoD 关闭 → Backlog 同步 → 反馈处理），**不询问"是否先关 Sprint"**——用户把回填文件交给入口本身就是明确指令。闭环完成后（`.done.processed.yaml` 留痕）再输出状态表继续常规路由。

检测清单：

| 文件 | 含义 | 负责技能 |
|------|------|----------|
| `agile-docs/VISION.md` | 愿景已产出 | agile-strategic（阶段 A） |
| `agile-docs/ARCHITECTURE.md` | 架构图已产出 | agile-strategic（阶段 B） |
| `agile-docs/ADR.md` | ADR 决策已产出 | agile-strategic（阶段 B） |
| `agile-docs/STRATEGY_CONFLICT.md` | 战略冲突待裁决 | using-agile（写前门禁生成，裁决后吸收可删） |
| `agile-docs/PRODUCT-BACKLOG.yaml` | 待办池已产出（Agent 读） | agile-backlog |
| `agile-docs/PRODUCT-BACKLOG.md` | 待办池已产出（人读） | agile-backlog |
| `agile-docs/DOD.md` | 完成定义已就绪 | using-agile（初始化） |
| `sprints/*.done.yaml` | Sprint 执行结果已回传 | using-agile（本入口，默认执行回填闭环：agile-sprint 关闭 → agile-backlog 同步 + 反馈处理） |
| `sprints/` 下含状态非"已关闭"的 `.md` | 活跃 Sprint | agile-sprint |

## 二、三层状态表（using-agile 输出模板）

```markdown
## 项目状态：{project_name}

| 层 | 维度 | 状态 |
|----|------|------|
| 战略 | 愿景 | {VISION.md: ✅/❌} |
| 战略 | 架构图 | {ARCHITECTURE.md: ✅/❌} |
| 战略 | ADR | {ADR.md: N 条决策} |
| 战略 | 冲突待裁决 | {STRATEGY_CONFLICT.md: 有（待裁决）/无} |
| 执行 | DoD | {DOD.md: ✅/❌} |
| 执行 | Backlog MD | {PRODUCT-BACKLOG.md: ✅/❌，N 条} |
| 执行 | Backlog YAML | {PRODUCT-BACKLOG.yaml: ✅/❌} |
| 执行 | 活跃 Sprint | {有/无，文件名} |
| 执行 | Sprint 回填 | {sprints/*.done.yaml: N 个待闭环处理（闭环后为 .done.processed.yaml）} |
| 执行 | 执行反馈 | {.done.yaml feedback: N 条待处理（issue/decision）} |
```

> ⚠️ 若检测到 >1 个活跃 Sprint（状态非"已关闭"），警告并请用户选择关闭/合并其一后再继续。

## 三、路由决策

| 用户表态 | 路由到 |
|----------|--------|
| STRATEGY_CONFLICT.md 存在（待裁决） | 先裁决冲突再继续（写前门禁，见 `references/gate-protocol.md §一`） |
| VISION ❌ | agile-strategic 阶段 A |
| VISION ✅ 但 ARCHITECTURE 或 ADR ❌ | agile-strategic 阶段 B |
| 战略层已就绪 + 想拆待办 | agile-backlog |
| Backlog 非空 + 想开冲刺 | agile-sprint |
| 想改已有文档（任意类型） | using-agile §6 变更协调（按 change-matrix 路由到对应业务技能） |
| .done.yaml 存在（任意 Sprint 状态） | **默认执行回填闭环**：agile-sprint 环节 B/C 关闭（如未关闭）→ agile-backlog 阶段 5 同步 + 反馈处理 → `.done.processed.yaml` 留痕；机械步骤自动，裁决点停下 |
