---
name: agile-backlog
slug: agile-backlog
displayName: 敏捷产品待办
description: |
  当用户说"写待办""拆任务""Backlog""Product Backlog""使能项""优先级排序""排迭代"或 using-agile 路由到此，且战略层（VISION + ARCHITECTURE/ADR）已确认时触发。
agent_created: true
version: 4.3.1
dependencies:
  - skill: using-agile
    reason: 提供初始化骨架与路由
  - skill: agile-strategic
    reason: VISION 核心原则与 ADR 决策是 Backlog 校验与 T-NNN 关联的来源
---

# 产品待办 (Agile Backlog)

## 0. 前置条件（缺失则路由回退）

| 条件 | 缺失时路由 |
|------|-----------|
| `agile-docs/` 目录存在 | → using-agile 初始化 |
| `agile-docs/VISION.md` 存在 | → agile-strategic 阶段 A |

## 1. 定位
本技能是执行层中枢，产出**两个文件**：`agile-docs/PRODUCT-BACKLOG.md`（人读）+ `agile-docs/PRODUCT-BACKLOG.yaml`（Agent 轻量读取）。

它是**待办池**（to-do list）。技术任务（T-NNN）和功能需求（F-NNN）**平级**进入待办池。不强制 INVEST/Given-When-Then 仪式。

## 2. 写前对齐（渐进式：先探询，再产出）

### 2a. 机械校验（agent 自检，不需用户参与）

- 用 VISION 的"核心原则 / 战略红线"校验每个条目的归属（不服务愿景的不进 Backlog）
- 用 ADR.md 中的决策推导技术任务（T-NNN），每条 T-NNN 关联对应 ADR 章节
- 确认优先级排序逻辑（见 `references/backlog-rules.md`）
- **双文件一致性校验**：若 .yaml 与 .md 均存在，对比 id/priority/status 三字段。不一致 → 停下报告差异，请用户确认以哪份为准后再继续

### 2b. 探询对话（与用户必走，姿态与节奏遵循 `using-agile/references/probing-protocol.md`）

1. **MVP 范围挑战**：对每个 Must 条目问"这项不做，首版会怎样？"——答不出具体后果的建议降为 Should/Could（降不降由用户裁决）；Must 占比超过总条目 60% 时必须提出质疑（"全都 Must 等于没有优先级"）
2. **估点确认**：每个条目的点数由 agent 给出建议值 + 一句理由；点数 ≥5 或复杂度存疑的条目，须向用户核对复杂度信号（涉及几个模块？有无外部依赖？团队做过类似的吗？）后再定
3. **验收含糊追问**："非显然"条目的验收标准写不出可观察行为时，向用户追问（"这条交付后，用户/系统能看到什么变化？"），**不许自行脑补**；用户明确跳过 → 验收栏标 `{待确认}`

## 3. 产出（双文件）

### 3a. `agile-docs/PRODUCT-BACKLOG.md`（人读）

```markdown
# Product Backlog

> 维护说明：待办池，按优先级排序。技术任务与功能需求平级。

## 优先级排序表

| ID | 标题 | 类型 | 点 | 优先级 | 状态 | 关联 |
|----|------|------|---|--------|------|------|
| T-001 | {标题} | 技术 | 5 | Must | 待办 | ADR-001/005 |
| F-001 | {标题} | 功能 | 2 | Must | 待办 | — |
...

## 任务详情（仅非显然条目展开）

### F-NNN {标题}
- 验收: {1-3 条}
- 关联: {ADR 或其他条目}

### T-NNN {标题}
- 要求: {1-3 条约束}
- 关联: {ADR}
```

详细规则见 `references/backlog-rules.md`。

### 3b. `agile-docs/PRODUCT-BACKLOG.yaml`（Agent 读）

轻量接口文件，仅含消费 Agent 需要的排序字段。每次编辑 Backlog 后自动同步。

```yaml
version: "1.0"
items:
  - id: "F-001"
    priority: "Must"
    status: "待办"
  - id: "T-001"
    priority: "Must"
    status: "待办"
    adr_refs: ["ADR-003"]
  - id: "T-002"
    priority: "Should"
    status: "已完成"
```

**同步规则**：每次写入/更新 PRODUCT-BACKLOG.md 时，同步生成/更新 PRODUCT-BACKLOG.yaml。YAML 始终反映最新排序和状态，不含 acceptance/constraints 等描述详情。消费 Agent 读 YAML 拿排序，按需回读 `.md` 取详情。

### 3c. 接受 .done 同步

当 using-agile 检测到 `sprints/*.done.yaml` 存在且对应 Sprint 已关闭，路由到本技能：

1. 读取 `.done.yaml`，按 completed / moved_next 批量更新 PRODUCT-BACKLOG.yaml（status 字段）
   - completed 条目 → status: "已完成"
   - moved_next 条目 → status: "待办"，**仅改 status，priority 字段保持原值不动**（原属顶部条目，状态复位后自然回到取用顺序前列；禁止为"保回顶部"擅自调高优先级）
2. 同步更新 PRODUCT-BACKLOG.md 表格
3. 将 `.done.yaml` 文件后缀改为 `.done.processed`（留痕，不删除）
4. 完成后停下，报告同步结果

## 4. 写完即停（结构化审阅）

按 `using-agile/references/probing-protocol.md §四` 输出决策点确认清单（重点列排序依据 / 优先级判断 / agent 自估点数及理由 × 来源），问"**继续下一步**（agile-sprint）还是**更新**本层？"。

## 5. 硬约束
- ✅ 产出 `PRODUCT-BACKLOG.md` + `PRODUCT-BACKLOG.yaml` 双文件；❌ **不顺手写** VISION / ARCHITECTURE / ADR / Sprint。
- ✅ 技术任务（T-NNN）和功能需求（F-NNN）平级；仅"非显然"条目展开（验收/约束/关联非显然）。
- ❌ 不使用 INVEST / Given-When-Then 仪式，不拆 epics/enablers 子目录，不用 US/EN/EPIC 命名。
- ✅ 涉及架构决策的 T-NNN 必须关联 ADR（门禁 ①）；F-NNN 默认不强制关联（判定细则见 `using-agile/references/gate-protocol.md §二 ①`）。
- ✅ 写前探询遵循 `using-agile/references/probing-protocol.md`：Must 级条目须经范围挑战（§2b）；估点为 agent 建议值，须经用户确认；验收写不出可观察行为时追问而非脑补。
- ✅ 每次编辑 .md 后必须同步更新 .yaml（id/priority/status 字段）。
- ✅ 接受 Sprint 执行结果（.done.yaml），按 completed/moved_next 批量同步 .yaml + .md，同步后改后缀 .done.processed 留痕。

## 6. 门禁
- **T-NNN 无 ADR**：技术任务涉及架构决策但未关联 ADR.md 章节 → 停下，先回 agile-strategic 阶段 B 补 ADR 章节，再回填关联字段。现有 ADR 无合适章节时同样回阶段 B 补，**禁止发明"待 ADR-NNN 确认"之类的占位关联**（判定细则见 `using-agile/references/gate-protocol.md §二 ①`）。
- **条目过大无法估点**：用拆分法降为多个 T-/F- 条目再估点（边界异常 ⑥）。
- 冲突 / 歧义即停（见 `using-agile/references/gate-protocol.md`）。
