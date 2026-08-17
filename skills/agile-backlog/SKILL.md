---
name: agile-backlog
slug: agile-backlog
displayName: 敏捷产品待办
description: |
  当用户说"写待办""拆任务""Backlog""Product Backlog""使能项""优先级排序""排迭代"或 using-agile 路由到此，且战略层（VISION + ARCHITECTURE/ADR）已确认时触发。
agent_created: true
version: 4.4.1
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
| `agile-docs/ARCHITECTURE.md` + `ADR.md` 存在 | → agile-strategic 阶段 B（用户明确跳层时可缺，T-NNN 由门禁 ① 拦截） |

## 1. 定位
本技能是执行层中枢，产出**两个文件**：`agile-docs/PRODUCT-BACKLOG.md`（人读）+ `agile-docs/PRODUCT-BACKLOG.yaml`（Agent 轻量读取）。

它是**待办池**（to-do list）。技术任务（T-NNN）和功能需求（F-NNN）**平级**进入待办池。不强制 INVEST/Given-When-Then 仪式。

**产出分阶段，每阶段写完即停**（不再一次性出全部）：

| 阶段 | 产出 | 前置 |
|------|------|------|
| 阶段 0 | （无文件）决策问询 | 读 VISION/ADR + 项目画像 |
| 阶段 1 | 优先级排序表 + 估点建议（§3 阶段1） | 阶段 0 完成 |
| 阶段 2 | 任务详情展开 + 验收标准（§3 阶段2） | 阶段 1 确认 |
| 阶段 3 | 生成/同步 `PRODUCT-BACKLOG.yaml`（§3 阶段3） | 阶段 2 确认 |
| 阶段 4 | 下游影响评估（§3 阶段4，仅更新已有 Backlog 时） | 阶段 3 完成 |
| 阶段 5 | 接受 .done 同步（§3 阶段5，仅 .done.yaml 回传时） | `.done.yaml` 存在 + Sprint 已关闭 |

**决策用选择题问**（`using-agile/references/interview-protocol.md`）：先读 VISION/ADR 补事实（文档优先），只把真决策（范围/优先级/估点/验收）用「候选 + 推荐 + 自定义」一次一问地喂给用户。变更时先分级（`using-agile/references/change-matrix.md §二`），禁止整层重访。

## 2. 写前对齐（先问询，再产出）

### 2a. agent 自检 checklist（机械项，不需用户参与）

- 用 VISION 的"核心原则 / 战略红线"校验每个条目的归属（不服务愿景的不进 Backlog）
- 用 ADR.md 中的决策推导技术任务（T-NNN），每条 T-NNN 关联对应 ADR 章节
- 确认优先级排序逻辑（见 `references/backlog-rules.md`）
- **双文件一致性校验**：若 .yaml 与 .md 均存在，对比 id 集合、条目数、同 id 的 priority/status（权威口径见 `references/backlog-rules.md §七`）。不一致 → 停下报告差异，请用户确认以哪份为准后再继续

### 2b. 决策问询（写前必跑，`using-agile/references/interview-protocol.md`）

按 `using-agile/references/interview-protocol.md` 用选择题问，本技能落点：

1. **文档优先**：读 `agile-docs/VISION.md`（原则/红线）、`ADR.md`、`DOD.md` 头部项目画像；VISION 已确认的定位/原则不重问，只问待办层缺口。
2. **一次一问 + 给推荐**：三个决策点逐个问（候选 + 推荐 + 自定义兜底），答完再问下一个：

| # | 决策点 | 候选选项方向（结合实际填，给推荐 + 理由） | 追问触发 | 兜底 |
|---|--------|------------------------------------------|----------|------|
| 1 | **MVP 范围** | 对每个 Must 条目给「保留 / 降为 Should / 降为 Could」选项 + 推荐 | 答不出"不做首版会怎样" → 推荐降级；Must 占比 >60% 时质疑"全都 Must 等于没有优先级" | 用户"你看着办" → 按推荐降级，标 agent 推荐 |
| 2 | **估点** | agent 给建议值 + 一句理由，给「接受 / 调整」选项 | 点数 ≥5 或复杂度存疑 → 给复杂度信号选项（涉及几个模块？外部依赖？） | 用户"你看着办"→ 按建议值 + 标"agent 推荐" |
| 3 | **验收** | "非显然"条目给 2-3 版可观察行为的验收写法供选 | 答不出 → 继续追问，**不许自行脑补** | 用户明确跳过 → 验收栏标 `{待确认}` |

3. **共识后落盘**：三决策点确认 → 进入 §3 产出；未确认不写 Backlog 文件。

**变更快速响应**：已产出后遇「需求变了」，先按 `using-agile/references/change-matrix.md §二` 分级——L1 措辞就地改、L2 只重问受影响条目、L3 才走完整问询；L1/L2 禁止整层重访。

## 3. 产出（分阶段，每阶段写完即停）

### 阶段 1：优先级排序表 + 估点建议（先出排序，不展开详情）

先写 `PRODUCT-BACKLOG.md` 的「优先级排序表」段（含 id/标题/类型/点/优先级/状态/关联/来源），**暂不写「任务详情」段**。写完停，结构化审阅后再进阶段 2。

```markdown
# Product Backlog

> 维护说明：待办池，按优先级排序。技术任务与功能需求平级。

## 优先级排序表

| ID | 标题 | 类型 | 点 | 优先级 | 状态 | 关联 | 来源/依据 |
|----|------|------|---|--------|------|------|-----------|
| T-001 | {标题} | 技术 | 5 | Must | 待办 | ADR-001/005 | 用户确认 / 依赖优先 |
| F-001 | {标题} | 功能 | 2 | Must | 待办 | — | agent 推荐 / MoSCoW |
...
```

- 「来源/依据」列承载两个标注：点的来源（`agent 推荐` 或 `用户确认`）+ 优先级依据（开发顺序 / MoSCoW / 依赖 / ADR 优先级，见 `references/backlog-rules.md §三`）。

### 阶段 2：任务详情展开 + 验收标准（仅非显然条目）

在 `PRODUCT-BACKLOG.md` 追加「任务详情」段，仅非显然条目展开（验收/约束/关联），判定标准见 `references/backlog-rules.md §四`。写完停，结构化审阅后再进阶段 3。

```markdown
## 任务详情（仅非显然条目展开）

### F-NNN {标题}
- 验收: {1-3 条可观察行为}（来源：{用户给出 / 待确认}）
- 关联: {ADR 或其他条目}

### T-NNN {标题}
- 要求: {1-3 条约束}
- 关联: {ADR}
```

- 验收写不出可观察行为 → 回决策问询追问（§2b 决策点 3），不许脑补；用户明确跳过 → 标 `{待确认}`。

### 阶段 3：生成/同步 `agile-docs/PRODUCT-BACKLOG.yaml`（Agent 读）

轻量接口文件，仅含消费 Agent 需要的排序字段。**在前两阶段确认后生成/同步**，避免提前出 YAML 导致排序未定就落盘。

```yaml
version: "1.0"
items:
  - id: "F-001"
    priority: "Must"
    status: "待办"
  - id: "T-001"
    priority: "Must"
    status: "待办"
    adr_refs: ["ADR-001", "ADR-005"]
  - id: "T-002"
    priority: "Should"
    status: "已完成"
```

**同步规则**：首次产出时阶段 1/2 只写 `.md`，阶段 3 才生成 `.yaml`；**`.yaml` 生成后**，每次编辑 `.md` 同步更新 `.yaml`。YAML 始终反映最新排序和状态，不含 acceptance/constraints 等描述详情。消费 Agent 读 YAML 拿排序，按需回读 `.md` 取详情。

### 阶段 4：下游影响评估（更新已有 Backlog 时的审阅清单项）

**首次产出跳过**；本次若是「更新已有 Backlog」，作为**结构化审阅清单的一项**评估下游 Sprint 是否需要改变（`using-agile/references/change-matrix.md §四`），不单独成环节：

- 本次变更是否涉及「活跃 Sprint 已引用的条目」的点数 / 优先级 / 状态 / 删除？
  - 是 → 评估承诺点是否仍 ≤ 可用点、任务清单是否需换入/换出；给调整建议，由用户裁决是否触发 `agile-sprint` 重规划。
  - 否 → 审阅清单记「下游无影响」。
- 增删条目 → 检查活跃 Sprint 任务清单是否受影响。

### 阶段 5：接受 .done 同步

当 using-agile 检测到 `sprints/*.done.yaml` 存在且对应 Sprint 已关闭，路由到本技能：

1. 读取 `.done.yaml`，按 completed / moved_next 批量更新 PRODUCT-BACKLOG.yaml（status 字段）
   - completed 条目 → status: "已完成"
   - moved_next 条目 → status: "待办"，**仅改 status，priority 字段保持原值不动**（原属顶部条目，状态复位后自然回到取用顺序前列；禁止为"保回顶部"擅自调高优先级）
2. 同步更新 PRODUCT-BACKLOG.md 表格
3. 将 `.done.yaml` 文件后缀改为 `.done.processed.yaml`（留痕，不删除）
4. 完成后停下，报告同步结果

## 4. 写完即停（结构化审阅，每阶段都走）

每个产出阶段写完即停，按 `using-agile/references/probing-protocol.md §四` 输出决策点确认清单（重点列排序依据 / 优先级判断 / agent 自估点数及理由 × 来源；阶段 4 追加「下游影响评估」结论），问"**继续下一阶段 / 下一步**（agile-sprint）还是**更新**本层？"。

## 5. 硬约束
- ✅ 产出 `PRODUCT-BACKLOG.md` + `PRODUCT-BACKLOG.yaml` 双文件；❌ **不顺手写** VISION / ARCHITECTURE / ADR / Sprint。
- ✅ **决策问询是产出前环节**（§2b，口径见 `using-agile/references/interview-protocol.md`），决策点未确认不落盘。
- ✅ **产出分阶段**（排序+估点 → 详情+验收 → YAML，§3），每阶段写完即停；❌ 禁止一次性出全部。
- ✅ 技术任务（T-NNN）和功能需求（F-NNN）平级；仅"非显然"条目展开（§3 阶段2）。
- ❌ 不使用 INVEST / Given-When-Then 仪式，不拆 epics/enablers 子目录，不用 US/EN/EPIC 命名。
- ✅ 涉及架构决策的 T-NNN 必须关联 ADR（门禁 ①，判定细则见 `using-agile/references/gate-protocol.md §二 ①`）。
- ✅ **关键决策落盘带来源标注**（用户给出 / agent 推断 / agent 推荐待确认）。
- ✅ `.yaml` 已存在后，每次编辑 .md 必须同步更新 .yaml（id/priority/status 字段）。

## 6. 门禁
- **T-NNN 无 ADR**：技术任务涉及架构决策但未关联 ADR.md 章节 → 停下，先回 agile-strategic 阶段 B 补 ADR 章节，再回填关联字段。现有 ADR 无合适章节时同样回阶段 B 补，**禁止发明"待 ADR-NNN 确认"之类的占位关联**（判定细则见 `using-agile/references/gate-protocol.md §二 ①`）。
- **条目过大无法估点**：用拆分法降为多个 T-/F- 条目再估点（边界异常 ⑤）。
- 冲突 / 歧义即停（见 `using-agile/references/gate-protocol.md`）。
