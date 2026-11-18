---
name: agile-backlog
slug: agile-backlog
displayName: 敏捷产品待办
description: |
  当用户说"写待办""拆任务""Backlog""Product Backlog""使能项""优先级排序""排迭代""长期待办""待办复核""梳理积压""整体验收"或 using-agile 路由到此，且战略层（VISION + ARCHITECTURE/ADR）已确认时触发。
agent_created: true
version: 5.6.0
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
本技能是执行层中枢，产出 `agile-docs/backlog.json`——**唯一的 Backlog 文件**，字段定义见 `references/backlog-rules.md §二`。人读概况 = 问 agent 或跑 `agile.py stats`（5.6.0 起 PRODUCT-BACKLOG.md 渲染产物退役，遗留文件不再维护，确认无自定义内容后可删）。

它是全项目的**业务待办池**（to-do list），保留整体 PRD/C4/ADR 作为范围与决策依据。技术任务（T-NNN）和功能需求（F-NNN）**平级**进入待办池。不强制 INVEST/Given-When-Then 仪式；不因前后端仓库或接收方不同拆分产品需求、重复估点。

跨仓/多接收方可在同一个共享 Sprint 显式启用工作包（`using-agile/references/workflow.md §三（工作包交付）`，字段见 `using-agile/references/sprint-schema.yaml` 的 `work_delivery`）。包隔离接收方实现上下文并跟踪具体依赖/回执/验收；本地 checkbox、子任务仍归消费 Agent。默认单执行者 `.done.yaml` 路径保留，不强制迁移。

**Backlog 编制分阶段，每阶段写完即停**（工作包已授权机械步骤例外见 §4）：

| 阶段 | 产出 | 前置 |
|------|------|------|
| 阶段 0 | （无文件）决策问询 | 读 VISION/ADR + 项目画像 |
| 阶段 1 | 条目 + 估点建议写入 `backlog.json`（§3 阶段 1，**json 是唯一结构**，多阶段分组落 `phases[]`） | 阶段 0 完成 |
| 阶段 2 | 任务详情展开 + 验收标准（§3 阶段 2） | 阶段 1 确认 |
| 阶段 3 | 下游影响评估（§3 阶段 3，仅更新已有 Backlog 时） | 阶段 2 确认 |
| 阶段 4 | 接受 .done 同步（§3 阶段 4，仅 .done.yaml 回传时） | `.done.yaml` 存在（入口闭环路由；Sprint 未关闭时先经 agile-sprint 关闭） |

「工作包整体验收」「长期待办复核」「风险管理」「发布管理」「决策记录」都是**独立入口**，不是阶段 5/6/7：hook 提示或用户主动提起时直接走 §3 的对应小节，不重访创建流程。

**决策用选择题问**（问询纪律见 `using-agile/references/probing-protocol.md`）：只把真决策（范围/优先级/估点/验收）喂给用户，事实先读 VISION/ADR。变更时先分级（`using-agile/references/change-matrix.md §二`），禁止整层重访。跨技能数据流全貌见 `using-agile/references/workflow.md`。

## 2. 写前对齐（先问询，再产出）

### 2a. agent 自检 checklist（机械项，不需用户参与）

- 用 VISION 的"核心原则 / 战略红线"校验每个条目的归属（不服务愿景的不进 Backlog）
- 用 ADR.md 中的决策推导技术任务（T-NNN），每条 T-NNN 关联对应 ADR 章节
- 确认优先级排序逻辑（见 `references/backlog-rules.md`）
- **旧格式转写检测**：`agile-docs/backlog.json` 不存在、而 `PRODUCT-BACKLOG.md` 里还是表格 → 按字段规范由 agent 一次性转写（`references/backlog-rules.md §七.4`，写完 hook 校验兜底）；v4.x 的 `.yaml` / `.json` 双文件把其中仅机器侧持有的信息（adr_refs / confirmed / withdrawn）核对进 json 后删除
- **统计不手算**：条目数 / 点数 / 分组统计由 `agile.py stats` 全量重算，命令见 `references/backlog-rules.md §七.3`。没有脚本时才自己按覆盖式重算，**禁止在旧数字上增量加减**

### 2b. 决策问询（写前必跑，`using-agile/references/probing-protocol.md`）

问询纪律按 `using-agile/references/probing-protocol.md`，本技能落点：

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
   | 7 | 风险信号：这事最可能出什么岔子 | 仅涉及外部系统/新技术/数据迁移时问一句；有担忧 → 经确认登记 R-NNN（`references/risk-rules.md`），无 → 跳过不凑数 |

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
          "confirmed": true,
          "created_at": "2026-11-02"
        }
      ]
    }
  ]
}
```

- `basis` 承载两个标注：点的来源（`agent 推荐` / `用户确认`）+ 优先级依据（开发顺序 / MoSCoW / 依赖 / ADR 优先级，见 `references/backlog-rules.md §三`）。
- `repo` 是可选单仓归属字符串；单仓库项目可省略，跨仓业务条目必须省略，不写数组/逗号串。同一 `F-001` 可分配后端 `WP-001` 与前端 `WP-002`，实际接收方仓库在包中，不为仓库边界另建 F 条目或重复计点。
- `confirmed`：`true` 已与用户确认，`false` agent 推荐待确认；Sprint 取用前必须显式转 `true`（否则 `agile-sprint` 跳过并告警）。
- `created_at`：新条目写真实立项日期（`YYYY-MM-DD`）；更新旧条目时不得把当天倒填成立项日期。`last_reviewed_at` 只在长期待办复核后写，创建时不预填。
- **统计不用自己算**：`agile.py stats` 全量重算，hook 注入的状态行也带统计。写完停，结构化审阅后再进阶段 2。

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
- 工作包模式的范围/验收/依赖变更还须检查冻结计划；经用户确认重规划后，同 Sprint 全部旧包回执失效、保留历史，不承诺未改包版本不变。已有任一条目整体完成则拒绝重规划，新工作进入新 Sprint；战略冲突仍先走门禁，不能用包修订绕过。

### 阶段 4：接受 .done 同步

当 using-agile 检测到 `sprints/*.done.yaml` 并路由到本技能；单执行者无 `.done.yaml` 人工关闭时，仍按 Sprint「条目状态建议」同步与归档。工作包模式必须消费 `work close` 生成并已过 agile-sprint 校验/DoD 的规范 `.done`，不允许人工替代：

1. 读取 `.done.yaml`，按模式同步 `backlog.json`
   - 单执行者：completed → `已完成`；moved_next → `待办`
   - 工作包：先跑 `python <plugin>/scripts/agile.py check HUB`；completed 必须已经由 `work finish` 写入整体 `delivery_acceptance` 与 `status=已完成`，本阶段只核对保留，不补造/覆盖/删除验收记录。缺验收或 moved_next 含已整体验收条目 → 停下报冲突，不能降回待办；其余 moved_next 保持 `待办`
   - `priority` 均保持原值，禁止为"保回顶部"调高；两组条目仍在 `planned_sprints` 追加本 Sprint 序号。此字段只在阶段 4 维护，不能在 work finish 时提前盖闭环戳记（见 `references/backlog-rules.md §二`）
2. **处理 feedback**（`.done.yaml` 的 feedback 列表；执行中 issue/decision 可随时回本技能，不等 `.done`，已处理的不重复建条目；回执汇总不是产品裁决）：
   - `reason`（未完成原因）→ 已由 agile-sprint 在关闭环节展示，此处无需处理
   - `issue`（执行中发现的新问题）→ 转为 Backlog **新条目候选**：列出建议条目（标题 / 类型 / 优先级建议 / 来源标注"消费 Agent 反馈"），缺陷类建议 `type=缺陷`、前缀 B-NNN（`references/backlog-rules.md §一`），请用户确认后新增进 `backlog.json`
   - `decision`（需产品层裁决）→ 停下请用户裁决；裁决结果**记入 `decisions.json`**（做/不做都留痕，见 `references/decision-rules.md`），outcome=做 再建条目
3. 将 `.done.yaml` 文件后缀改为 `.done.processed.yaml`（留痕，不删除）。**必须排在第 1 步同步之后**——后缀一改，回填检测即视为已闭环；若中断在同步之前，会留下「留痕在、状态没同步」的假闭环，且没有任何机制会再触发补同步
4. **归档**：把留痕文件与对应 Sprint 文件一并移入 Sprint 所在目录的 `archive/` 子目录（如 `sprints/archive/`，目录不存在则创建）——`sprints/` 只留未闭环文件，状态检测与每轮扫描不进 `archive/`
5. 完成后停下，报告同步结果 + 反馈处理结果

### 工作包整体验收（独立入口）

工作包模式下，同一条目的所有包都验收后，按父条目验收行为和项目 DoD 核验整体交付；用户或其明确授权的验收者确认后调用 `work finish`，记录验收者与真实验证证据，不关闭 Sprint。包验收仅证明局部交付，不能省略前后端整体验收；未通过则报告差距，不手改完成状态。命令与修订限制见 `using-agile/references/workflow.md §三（工作包交付）`。

### 长期待办复核（独立入口）

当 hook 报告待复核条目，或用户主动要求梳理长期待办时：

1. 跑 `agile.py review` 获取完整清单；机械口径见 `references/backlog-rules.md §五.长期待办复核`，不根据标题或优先级猜测条目是否已失效
2. 向用户展示 ID / 标题 / 优先级 / 立项年龄 / 最近复核 / 从未纳入或曾纳入 Sprint，明确「年龄只是复核信号，不代表应该撤回」
3. 用户按 ID 选择处置，可一批多项：
   - **保留** → 仅把当天写入这些条目的 `last_reviewed_at`，年龄仍从 `created_at` 算
   - **调整优先级 / 范围** → 按 `using-agile/references/change-matrix.md` 分级更新，并写本次复核日期；不得因年龄自动升级 Could
   - **拆分** → 按边界异常 ⑤（过大拆分）重新估点；原条目按本次用户裁决走撤回留痕（原因注明替代条目 ID），新条目继承原 `created_at` 并写本次复核日期，不因拆分重置年龄
   - **撤回** → 用户明确确认后走 `references/backlog-rules.md §五` 撤回流程，记录时间 / 原因 / 决策来源
   - **只是知道了 / 本次不处理** → 不改 `last_reviewed_at`，不伪造复核记录
4. 创建时间未知的存量条目单独列出；能从 Git 历史确认才回填，不能确认则保留未知，不用迁移当天冒充
5. 写完即停，报告本次保留 / 调整 / 拆分 / 撤回结果；不顺势开 Sprint

### 风险管理（独立入口）

用户说"风险""风险登记"，或识别入口命中（需求探索信号 / strategic 瓶颈预判 / 条目反复顺延 / 同类 reason 重复）时进入，字段与生命周期见 `references/risk-rules.md`：

1. 识别入口命中的，用选择题确认"要不要登记为风险"；**用户确认才写 `risks.json`，不静默建**
2. 处置（用户按 ID 裁决）：已发生 → 按 `risk-rules.md §三` 转条目 + hit_ref；已解除 / 已接受 → 只改 status
3. **不打分、不自动升级、不按年龄处置**；Sprint 规划过一遍活跃风险是唯一例行复核
4. 写完即停，报告登记/处置结果

### 发布管理（独立入口）

用户说"发版""版本规划"，或 agile-sprint 关闭环节提示"完成条目并入哪个 release"时进入，字段与检查单见 `references/release-rules.md`：

1. 组版本：确认版本号（id）+ 构成条目（从已完成/计划条目选，须存在于 `backlog.json`）
2. checks 三项逐项确认（rollback / migration / notice，不适用的项确认后置 true）
3. 发布/取消由**用户裁决**后改 status + released_at；已发布的 items 不改写
4. 写完即停，报告组版本/发布结果

### 决策记录（独立入口）

用户说"记录决策"，或 feedback.decision / L3 变更裁决完成时进入，口径见 `references/decision-rules.md`：裁决结果写 `decisions.json`（做/不做都留痕，「明确忽略」= outcome 不做），outcome=做 的再转条目。只记结果不记讨论过程；推翻旧决策新记一条并注明替代。

## 4. 写完即停（结构化审阅，每阶段都走）

每个产出阶段按 `using-agile/references/probing-protocol.md §四` 结构化审阅（重点列：排序依据 / 优先级判断 / agent 自估点数及理由 × 来源，阶段 3 追加「下游影响评估」）。真决策未确认即停；已授权工作包创建/导入/导出等机械派生步骤不逐文件重复问询（`using-agile/references/workflow.md §三（工作包交付）`），不因此自动通过验收或战略冲突门禁。

## 5. 硬约束
- ✅ 产出 `agile-docs/backlog.json`（唯一 Backlog 文件）；❌ **不顺手写** VISION / ARCHITECTURE / ADR / Sprint / PRODUCT-BACKLOG.md。
- ✅ **决策问询是产出前环节**（§2b，口径见 `using-agile/references/probing-protocol.md`），决策点未确认不落盘。
- **Backlog 决策分阶段**（排序+估点 → 详情+验收，§3），未确认不一次性推进；工作包同次授权的机械派生步骤按 §4，不按文件数重复设停点。
- ✅ **`phases[]` 即唯一结构**（§3 阶段 1），**禁止**单独维护"优先级排序表 / 待办池"等平级结构；字段名与取值严格按 `references/backlog-rules.md §二`，不自由增删。
- ✅ 技术任务（T-NNN）和功能需求（F-NNN）平级；仅"非显然"条目展开（§3 阶段2）。
- ❌ 不使用 INVEST / Given-When-Then 仪式，不拆 epics/enablers 子目录，不用 US/EN/EPIC 命名。
- ✅ 涉及架构决策的 T-NNN 必须关联 ADR（门禁 ①，判定细则见 `using-agile/references/gate-protocol.md §二 ①`）。
- ✅ **关键决策落盘带来源标注**（用户给出 / agent 推断 / agent 推荐待确认）。
- **Backlog 条目只写整体范围**（可观察验收行为 / 业务与非功能约束 / 边界 / 依赖关联），不把前后端实现详情塞进条目；技术决策由全局 ADR 承载，接收方实现上下文与具体依赖由工作包隔离，本地实现归消费 Agent（`references/backlog-rules.md §四`）。
- 全局 Backlog/delivery 只存中枢，执行者不得直接编辑；`delivery.json` 归脚本，`delivery_acceptance` 只由 `work finish` 写，阶段 4 保留该记录与已整体验收状态。字段见 `references/backlog-rules.md §二`；工作包模式无插件脚本则不启用。
- ✅ **统计不手算**：条目数 / 点数 / 分组统计交给 `agile.py stats`（§2a），禁止在旧数字上加减。
- ✅ **未确认条目 Sprint 取用前必须显式 confirm**：`confirmed: false` 的「待办」条目，`agile-sprint` 取用时跳过并告警；不私自默认成 `true`（agent 推荐 ≠ 用户确认）。
- ✅ **长期待办只提示、不自动处置**：复核口径见 `references/backlog-rules.md §五.长期待办复核`；只有用户明确保留 / 调整后才写 `last_reviewed_at`，禁止按年龄自动改优先级、开 Sprint 或撤回。
- ✅ **`risks.json` / `releases.json` / `decisions.json` 归本技能写**（字段见 `references/` 下对应 rules），其他技能只读或提示路由。风险不打分、不自动升级；发布不自动标已发布；决策不记讨论过程、不改写已记条目。三文件缺省 = 能力未启用，不建空文件。

## 6. 门禁
- **T-NNN 无 ADR**：停下，回 agile-strategic 阶段 B 补章节后再填关联；「待 ADR-NNN 确认」这类占位关联不算数。判定细则（什么算架构决策、F-NNN 何时该改判 T-NNN）见 `using-agile/references/gate-protocol.md §二 ①`。
- **条目过大无法估点**：用拆分法降为多个条目再估点（边界异常 ⑤）。
- 冲突 / 歧义即停（见 `using-agile/references/gate-protocol.md`）。
