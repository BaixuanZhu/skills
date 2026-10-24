---
name: agile-backlog
slug: agile-backlog
displayName: 敏捷产品待办
description: |
  当用户说"写待办""拆任务""Backlog""Product Backlog""使能项""优先级排序""排迭代"或 using-agile 路由到此，且战略层（VISION + ARCHITECTURE/ADR）已确认时触发。
agent_created: true
version: 5.3.0
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

前置条件缺失才回退；齐备时直接从 §2 开始，不必先经 `using-agile` 做状态检测。

## 1. 定位
本技能是执行层中枢，产出 `agile-docs/backlog.json`——**唯一的机器真源**，字段定义见 `references/backlog-rules.md §二`。同目录的 `PRODUCT-BACKLOG.md` 由脚本从它渲染，供人读，不手写、不反向写。

> **为什么不是单文件。** v5.0.0 曾规定「不另建机器侧副本」，那是针对 v4.x 的 `.yaml` + `.json` 双写——两份都手维护，必然漂移。这里的形态不同：**json 单向生成 md**，md 从不回写 json，不存在「保持一致」这件事，所以没有漂移可发生。人读视图和白纸黑字的结构化数据各归各位。

它是**待办池**（to-do list）。技术任务（T-NNN）和功能需求（F-NNN）**平级**进入待办池。不强制 INVEST/Given-When-Then 仪式。

**产出分阶段，每阶段写完即停**（不再一次性出全部）：

| 阶段 | 产出 | 前置 |
|------|------|------|
| 阶段 0 | （无文件）决策问询 | 读 VISION/ADR + 项目画像 |
| 阶段 1 | 条目 + 估点建议写入 `backlog.json`（§3 阶段 1，**json 是唯一结构**，多阶段分组落 `phases[]`） | 阶段 0 完成 |
| 阶段 2 | 任务详情展开 + 验收标准（§3 阶段 2） | 阶段 1 确认 |
| 阶段 3 | 下游影响评估（§3 阶段 3，仅更新已有 Backlog 时） | 阶段 2 确认 |
| 阶段 4 | 接受 .done 同步（§3 阶段 4，仅 .done.yaml 回传时） | `.done.yaml` 存在（入口闭环路由；Sprint 未关闭时先经 agile-sprint 关闭） |

**决策用选择题问**（`using-agile/references/interview-protocol.md`）：先读 VISION/ADR 补事实（文档优先），只把真决策（范围/优先级/估点/验收）用「候选 + 推荐 + 自定义」一次一问地喂给用户。变更时先分级（`using-agile/references/change-matrix.md §二`），禁止整层重访。

## 2. 写前对齐（先问询，再产出）

### 2a. agent 自检 checklist（机械项，不需用户参与）

- 用 VISION 的"核心原则 / 战略红线"校验每个条目的归属（不服务愿景的不进 Backlog）
- 用 ADR.md 中的决策推导技术任务（T-NNN），每条 T-NNN 关联对应 ADR 章节
- 确认优先级排序逻辑（见 `references/backlog-rules.md`）
- **旧格式迁移检测**：`agile-docs/backlog.json` 不存在、而 `PRODUCT-BACKLOG.md` 里还是表格 → 跑 `agile.py migrate`（一次性，脚本在插件 `scripts/` 下）；v4.x 的 `.yaml` / `.json` 双文件把其中仅机器侧持有的信息（adr_refs / confirmed / withdrawn）核对进 json 后删除
- **统计不手算**：条目数 / 点数 / 分组统计由 `agile.py stats` 全量重算，命令见 `references/backlog-rules.md §七.3`。没有脚本时才自己按覆盖式重算，**禁止在旧数字上增量加减**

### 2b. 决策问询（写前必跑，`using-agile/references/interview-protocol.md`）

按 `using-agile/references/interview-protocol.md` 用选择题问，本技能落点：

0. **需求探索（新增需求场景必跑；更新已有 Backlog 按 `change-matrix.md` 分级，L2 只重问受影响项）**

   先读 VISION/ADR/项目画像补事实（文档优先），**自检六项 checklist**（机械项不需用户参与）——每项能查则查、查不到用选择题问，缺项标 `{待确认}` 不许脑补：

   | # | 探索项 | 查 / 问 |
   |---|--------|---------|
   | 1 | 背景与目标：解决什么问题 | VISION 原则/画像可解释 → 查；否则问 |
   | 2 | 用户与使用场景：谁用、何时触发 | 现有条目可推断 → 查；否则问 |
   | 3 | 验收行为：交付后可观察的行为 | 必问——给 2-3 版候选写法供选（这是后续决策点 3 的素材） |
   | 4 | 边界与不做：显式排除范围 | 从目标反推候选 → 确认；不明确 → 问 |
   | 5 | 优先级信号：Must 依据 | 给 Must/Should 建议 + 依据（业务价值/依赖/风险）→ 确认 |
   | 6 | 关联约束：依赖其他条目/外部系统 | grep 现有 Backlog + ADR → 列候选确认 |

   探索确认 → 进入决策问询。

1. **文档优先**：读 `agile-docs/VISION.md`（原则/红线）、`ADR.md`、`DOD.md` 头部项目画像；VISION 已确认的定位/原则不重问，只问待办层缺口。
2. **一次一问 + 给推荐**：三个决策点逐个问（候选 + 推荐 + 自定义兜底），答完再问下一个：

| # | 决策点 | 候选选项方向（结合实际填，给推荐 + 理由） | 追问触发 | 兜底 |
|---|--------|------------------------------------------|----------|------|
| 1 | **MVP 范围** | 对每个 Must 条目给「保留 / 降为 Should / 降为 Could」选项 + 推荐 | 答不出"不做首版会怎样" → 推荐降级；Must 占比 >60% 时质疑"全都 Must 等于没有优先级" | 用户"你看着办" → 按推荐降级，标 agent 推荐 |
| 2 | **估点** | agent 给建议值 + 一句理由，给「接受 / 调整」选项 | 点数 ≥5 或复杂度存疑 → 给复杂度信号选项（涉及几个模块？外部依赖？） | 用户"你看着办"→ 按建议值 + 标"agent 推荐" |
| 3 | **验收** | "非显然"条目给 2-3 版可观察行为的验收写法供选（素材来自需求探索③） | 答不出 → 继续追问，**不许自行脑补** | 用户明确跳过 → 验收栏标 `{待确认}` |

3. **共识后落盘**：三决策点确认 → 进入 §3 产出；未确认不写 Backlog 文件。

**变更快速响应**：已产出后遇「需求变了」，先按 `using-agile/references/change-matrix.md §二` 分级——L1 措辞就地改、L2 只重问受影响条目、L3 才走完整问询；L1/L2 禁止整层重访。

## 3. 产出（分阶段，每阶段写完即停）

### 阶段 1：条目 + 估点建议（先出排序，不展开详情）

`backlog.json` 的 `phases[]` 就是唯一结构——条目按阶段分块。**不另立「待办池 / 优先级排序表」**，那只是各阶段的并集。

写 `agile-docs/backlog.json`，`detail` 先留空，其余字段写全（定义见 `references/backlog-rules.md §二`）：

```json
{
  "schema": 1,
  "phases": [
    {
      "id": 1,
      "title": "止血",
      "items": [
        {
          "id": "T-001",
          "title": "{标题}",
          "type": "技术",
          "repo": "api-server",
          "points": 5,
          "priority": "Must",
          "status": "待办",
          "refs": "ADR-001、ADR-005",
          "basis": "用户确认 / 依赖优先",
          "confirmed": true
        }
      ]
    }
  ]
}
```

- `basis` 承载两个标注：点的来源（`agent 推荐` / `用户确认`）+ 优先级依据（开发顺序 / MoSCoW / 依赖 / ADR 优先级，见 `references/backlog-rules.md §三`）。
- `repo` 仅多仓库项目填（供 Sprint 识别跨仓库交接点），单仓库省略。
- `confirmed`：`true` 已与用户确认，`false` agent 推荐待确认；Sprint 取用前必须显式转 `true`（否则 `agile-sprint` 跳过并告警）。
- **统计不用自己算**：保存时 hook 会重渲染 `PRODUCT-BACKLOG.md` 并把统计写进去；没装插件就跑 `agile.py render`。写完停，结构化审阅后再进阶段 2。

### 阶段 2：任务详情展开 + 验收标准（仅非显然条目）

把展开内容写进对应条目的 `detail` 数组，仅非显然条目需要（验收/约束/关联），判定标准见 `references/backlog-rules.md §四`。写完停，结构化审阅后再进阶段 3。

```json
{
  "id": "F-NNN",
  "detail": [
    "验收：{1-3 条可观察行为}（来源：{用户给出 / 待确认}）",
    "关联：{ADR 或其他条目}"
  ]
}
```

- 验收写不出可观察行为 → 回决策问询追问（§2b 决策点 3），不许脑补；用户明确跳过 → 标 `{待确认}`。

### 阶段 3：下游影响评估（更新已有 Backlog 时的审阅清单项）

**首次产出跳过**；本次若是「更新已有 Backlog」，作为**结构化审阅清单的一项**评估下游 Sprint 是否需要改变（`using-agile/references/change-matrix.md §四`），不单独成环节：

- 本次变更是否涉及「活跃 Sprint 已引用的条目」的点数 / 优先级 / 状态 / 删除？
  - 是 → 评估承诺点是否仍 ≤ 可用点、任务清单是否需换入/换出；给调整建议，由用户裁决是否触发 `agile-sprint` 重规划。
  - 否 → 审阅清单记「下游无影响」。
- 增删条目 → 检查活跃 Sprint 任务清单是否受影响。

### 阶段 4：接受 .done 同步

当 using-agile 检测到 `sprints/*.done.yaml`（默认执行回填闭环）并路由到本技能：

1. 读取 `.done.yaml`，按 completed / moved_next 批量更新 `backlog.json` 里对应条目的 `status`
   - completed 条目 → `已完成`
   - moved_next 条目 → `待办`，**仅改状态，`priority` 保持原值不动**（原属顶部条目，状态复位后自然回到取用顺序前列；禁止为"保回顶部"擅自调高优先级）
2. **处理 feedback**（`.done.yaml` 的 feedback 列表）：
   - `reason`（未完成原因）→ 已由 agile-sprint 在关闭环节展示，此处无需处理
   - `issue`（执行中发现的新问题）→ 转为 Backlog **新条目候选**：列出建议条目（标题 / 类型 / 优先级建议 / 来源标注"消费 Agent 反馈"），请用户确认后新增进 `backlog.json`
   - `decision`（需产品层裁决）→ 停下请用户裁决；裁决结果落盘为条目或明确忽略
3. 将 `.done.yaml` 文件后缀改为 `.done.processed.yaml`（留痕，不删除）
4. 完成后停下，报告同步结果 + 反馈处理结果

## 4. 写完即停（结构化审阅，每阶段都走）

每个产出阶段写完即停，按 `using-agile/references/probing-protocol.md §四` 输出决策点确认清单（重点列排序依据 / 优先级判断 / agent 自估点数及理由 × 来源；阶段 3 追加「下游影响评估」结论），问"**继续下一阶段 / 下一步**（agile-sprint）还是**更新**本层？"。

## 5. 硬约束
- ✅ 产出 `agile-docs/backlog.json`（机器真源）；`PRODUCT-BACKLOG.md` 由脚本渲染，**不手写**；❌ **不顺手写** VISION / ARCHITECTURE / ADR / Sprint。
- ✅ **决策问询是产出前环节**（§2b，口径见 `using-agile/references/interview-protocol.md`），决策点未确认不落盘。
- ✅ **产出分阶段**（排序+估点 → 详情+验收，§3），每阶段写完即停；❌ 禁止一次性出全部。
- ✅ **`phases[]` 即唯一结构**（§3 阶段 1），**禁止**单独维护"优先级排序表 / 待办池"等平级结构；字段名与取值严格按 `references/backlog-rules.md §二`，不自由增删。
- ✅ 技术任务（T-NNN）和功能需求（F-NNN）平级；仅"非显然"条目展开（§3 阶段2）。
- ❌ 不使用 INVEST / Given-When-Then 仪式，不拆 epics/enablers 子目录，不用 US/EN/EPIC 命名。
- ✅ 涉及架构决策的 T-NNN 必须关联 ADR（门禁 ①，判定细则见 `using-agile/references/gate-protocol.md §二 ①`）。
- ✅ **关键决策落盘带来源标注**（用户给出 / agent 推断 / agent 推荐待确认）。
- ✅ **Backlog 条目只写范围**（可观察验收行为 / 业务与非功能约束 / 边界 / 依赖关联），❌ **不写实现**（技术方案 / 框架选型 / 代码结构 / SQL / 伪代码）——技术决策由 ADR 承载，实现归消费 Agent 判断（细则见 `references/backlog-rules.md §四`）。
- ✅ **统计不手算**：条目数 / 点数 / 分组统计交给 `agile.py stats`（§2a），禁止在旧数字上加减。
- ✅ **未确认条目 Sprint 取用前必须显式 confirm**：`confirmed: false` 的「待办」条目，`agile-sprint` 取用时跳过并告警；不私自默认成 `true`（agent 推荐 ≠ 用户确认）。

## 6. 门禁
- **T-NNN 无 ADR**：技术任务涉及架构决策但未关联 ADR.md 章节 → 停下，先回 agile-strategic 阶段 B 补 ADR 章节，再回填关联字段。现有 ADR 无合适章节时同样回阶段 B 补，**禁止发明"待 ADR-NNN 确认"之类的占位关联**（判定细则见 `using-agile/references/gate-protocol.md §二 ①`）。
- **条目过大无法估点**：用拆分法降为多个 T-/F- 条目再估点（边界异常 ⑤）。
- 冲突 / 歧义即停（见 `using-agile/references/gate-protocol.md`）。
