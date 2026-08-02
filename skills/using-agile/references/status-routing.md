# 状态检测与路由（using-agile 参考）

## 一、路由决策原则

路由决策以 `agile-docs/` 下文件存在性为准，不依赖中心化状态文件。文件存在即状态，不存在即需生成。

**路由注意 — .done.yaml**：扫描 `sprints/*.done.yaml`，若存在且对应 Sprint 已关闭，状态表中追加"待同步"行，路由决策表中自动追加 agile-backlog 路由。该路由不跳过状态表——先输出完整状态，再追加待同步提示。

检测清单：

| 文件 | 含义 | 负责技能 |
|------|------|----------|
| `agile-docs/VISION.md` | 愿景已产出 | agile-strategic（阶段 A） |
| `agile-docs/ARCHITECTURE.md` | 架构图已产出 | agile-strategic（阶段 B） |
| `agile-docs/ADR.md` | ADR 决策已产出 | agile-strategic（阶段 B） |
| `agile-docs/PRODUCT-BACKLOG.yaml` | 待办池已产出（Agent 读） | agile-backlog |
| `agile-docs/PRODUCT-BACKLOG.md` | 待办池已产出（人读） | agile-backlog |
| `agile-docs/DOD.md` | 完成定义已就绪 | using-agile（初始化） |
| `sprints/*.done.yaml` | Sprint 执行结果已回传 | using-agile（本入口，根据 Sprint 状态决定路由 agile-sprint 或 agile-backlog） |
| `sprints/` 下含状态非"已关闭"的 `.md` | 活跃 Sprint | agile-sprint |

## 二、三层状态表（using-agile 输出模板）

```markdown
## 项目状态：{project_name}

| 层 | 维度 | 状态 |
|----|------|------|
| 战略 | 愿景 | {VISION.md: ✅/❌} |
| 战略 | 架构图 | {ARCHITECTURE.md: ✅/❌} |
| 战略 | ADR | {ADR.md: N 条决策} |
| 执行 | DoD | {DOD.md: ✅/❌} |
| 执行 | Backlog MD | {PRODUCT-BACKLOG.md: ✅/❌，N 条} |
| 执行 | Backlog YAML | {PRODUCT-BACKLOG.yaml: ✅/❌} |
| 执行 | 活跃 Sprint | {有/无，文件名} |
| 执行 | Sprint 待同步 | {sprints/*.done.yaml: N 个待处理} |
```

> ⚠️ 若检测到 >1 个活跃 Sprint（状态非"已关闭"），警告并请用户选择关闭/合并其一后再继续。

## 三、路由决策

| 用户表态 | 路由到 |
|----------|--------|
| VISION ❌ | agile-strategic 阶段 A |
| VISION ✅ 但 ARCHITECTURE 或 ADR ❌ | agile-strategic 阶段 B |
| 战略层已就绪 + 想拆待办 | agile-backlog |
| Backlog 非空 + 想开冲刺 | agile-sprint |
| 想改已有文档（任意类型） | using-agile §6 变更协调（按 change-matrix 路由到对应业务技能） |
| .done.yaml 存在 + Sprint 已关闭 | agile-backlog（执行同步） |
| .done.yaml 存在 + Sprint 状态非已关闭 | agile-sprint（先关 Sprint） |
