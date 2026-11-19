---
name: agile-sprint
slug: agile-sprint
displayName: Sprint规划
description: |
  当用户说"开 Sprint""规划迭代""工作包交付""回执验收""关闭 Sprint"或 using-agile 路由到此，且 backlog.json 已有条目时触发。
agent_created: true
version: 6.0.0
dependencies:
  - skill: using-agile
    reason: 提供 DOD.md 模板、工作包交付流程与接口契约
  - skill: agile-backlog
    reason: backlog.json 是 Sprint 取条目的来源
---

# Sprint 规划 (Agile Sprint)

## 0. 前置条件（缺失则路由回退）

| 条件 | 缺失时路由 |
|------|-----------|
| `agile-docs/backlog.json` 存在且 ≥1 条「待办」 | → agile-backlog |
| `agile-docs/DOD.md` 存在 | → using-agile 补 DoD 模板 |

以上是新规划前置条件；齐备时直接从 §2 开始，不必先经 `using-agile` 做状态检测。已有 Sprint 的回执、验收与关闭按当前计划处理，不因条目已整体完成而要求新建待办。所有写入仍须遵守 `using-agile/references/gate-protocol.md §一（写前战略门禁）`。

**条目来源硬约束**：Sprint 任务清单必须从 `agile-docs/backlog.json` 按 priority 取顶部条目。条目须经 `agile-backlog` 流程产出并写入 json；**口头/临时任务清单不能直接进入 Sprint**。若用户跳过 agile-backlog 给临时清单且坚持不回退，按渐进式节奏停下提示风险（`using-agile/references/gate-protocol.md §四`），由用户显式确认是否仍要回 agile-backlog 走正规流程。

## 1. 定位

本技能做 **Sprint 规划与关闭**；跨仓库或多接收方可显式启用 **WORK PACKAGE（工作包）模式**，补充包依赖、回执与验收的最小全局协调。消费 Agent 仍自行拆本地子任务、记 checkbox 与实现进度、处理本地阻塞，不把它们写回共享 Sprint。

**共享计划**：`sprints/sprint-{序号:03d}-{日期}.md`。保留全项目 PRD/C4/ADR、业务 Backlog 与同一个 Sprint；不按仓库拆产品需求或重复计点。默认单执行者仍接收 Sprint 文件并回填 `.done.json`，不迁移旧流程；工作包模式只分发面向接收方的版本化快照，**不整份分发 Sprint**。

工作包流程以 `using-agile/references/workflow.md §三（工作包交付）`、字段以 `using-agile/references/sprint-schema.yaml` 的 `work_delivery` 为单一权威。该模式必须有插件脚本；仅 `npx skills` 安装时沿用单执行者路径或先取得脚本，禁止手工仿造工作包协议。

**Sprint 闭环即止**——不自动改战略层。执行中发现愿景/架构/ADR 变更，按 `using-agile/references/change-matrix.md` 评估并请用户裁决；`feedback.issue/decision` 随时路由 agile-backlog，不必等 `.done`，回执汇总不能替代产品决策。

## 2. 写前对齐（先问询，再产出；选择题）

姿态遵循 `using-agile/references/probing-protocol.md`（一次一问，含糊必追问）；需要你拍板的决策点用「候选 + 推荐 + 自定义」选择题问。

- 确认取哪些 backlog.json 顶部条目（按 priority 排序）
- **`confirmed: false` 的条目不许纳入**：跳过并告警，先回 agile-backlog 请用户确认；不私自默认成 `true`（agent 推荐 ≠ 用户确认）
- **Sprint 目标反问**：取完候选条目后，先向用户确认"这 {N} 条能否支撑一个可陈述的 Sprint 目标？用一句话说是什么？"——目标说不出来 → 建议调整取用条目（换入/换出由用户裁决），不开"杂项堆" Sprint
- **技术任务（T-NNN）需关联 ADR 章节编号**；若关联缺失，按 `using-agile/references/gate-protocol.md §二 ①` 拦截，先回 agile-strategic 阶段 B 补 ADR
- **容量参数必问**：团队人数 / Sprint 工作日 / 团队成熟度（决定专注系数）——三者任一未知就问（可先读 `agile-docs/DOD.md` 头部项目画像取团队人数），**禁止静默按 0.6 默认**；专注系数给选项 + 推荐（A 0.5 新团队 / B 0.6 成熟 / C 0.7-0.75 全职专注），确认后使用并在 Sprint 文件中标注"agent 推荐"
- **容量检查**：点数直接读条目的 `points`（priority 与 points 同源），计算承诺点是否 ≤ 可用点。可用点计算见 `references/sprint-rules.md §一`
- 确认本 Sprint 序号：扫描 `sprints/` **与 `sprints/archive/`（归档历史）**下已有 `sprint-NNN-*.md`，取两处最大序号 +1——归档后 `sprints/` 顶层可能为空，只扫活目录会让序号从 001 重来、与归档撞号；两处全空才从 001 起（用于命名 `sprint-{序号:03d}-{日期}.md`）
- 确认起始日期（用于命名）
- **交付方式与交接点**：跨仓库或多接收方时确认是否启用工作包，并确认各包接收方、仓库、范围与具体依赖；同一 `F-001` 可映射后端 `WP-001` 与前端 `WP-002`，条目与点数仍只算一次。`backlog.repo` 只表示可选的单仓归属；跨仓业务条目省略，不改成数组或逗号串，实际仓库写入包。工作包用 `depends_on` 明确依赖的交付包，不以仓库先后代替；单执行者沿用跨仓依赖「交接契约」段（`references/sprint-template.md`）。产物正文复用 `references/handoff-template.md`，已有版本化契约不另强制生成第二份交接文档。
- **过一遍活跃风险**：读 `agile-docs/risks.json`（存在时）的「活跃」条目列给用户，可把应对工作转成条目纳入本 Sprint；无文件或无活跃风险 → 跳过。**只展示与建议，不写 risks.json**（写权限归 agile-backlog 风险管理入口，见 `agile-backlog/references/risk-rules.md`）
- 确认 DoD（读 `agile-docs/DOD.md`，若缺失回 using-agile 补）

## 3. 产出（按环节，在决策点停）

### 环节 A：规划
- 从 `agile-docs/backlog.json` 按 priority 取顶部条目（经 §2 Sprint 目标反问确认），读取 `points` 与可选 `repo`，容量只按业务条目去重计点
- 在 `sprints/` 下新建 `sprint-{序号:03d}-{日期}.md`，按 `references/sprint-template.md` 填周期/目标/容量/任务清单（纯列表）/交付与回填要求/闭环检查；仅已有单仓归属的条目标注 `[repo: xxx]`
- **单执行者**：跨仓且有先后依赖时生成模板「交接契约」段；写完按 §4 审阅，确认后问"是否交付消费 Agent 执行？"；执行完回填 `.done.json` 后走环节 B
- **工作包**：共享计划留中枢，按下列命令登记、导出包。用户已确认范围/目标、接收方与依赖并授权交付后，同次授权内创建计划、导入与导出等机械步骤连续完成，不因每个派生文件重复停问；新增决策、战略冲突与实际验收不得自动通过

#### 工作包交付（仅启用时）

命令与版本规则统一见 `using-agile/references/workflow.md §三（工作包交付）`，JSON 字段见 `work_delivery`；`--root` 始终指中枢，不是执行仓库。

1. 用户确认后导入计划，按 `work status` 仅导出依赖就绪的包；分发内容保留共同设计、该包范围与已验收上游产物，不附另一端实现指令。
2. 收到独立回执后 `submit`；验收者核验已完成回执并 `accept`，才释放下游依赖。提交成功不等于验收通过。
3. 同一业务条目全部包已验收后，路由 agile-backlog「工作包整体验收」，由 `work finish` 写整体结果，不以包的完成比例代替业务验收。
4. 仅用户要求关轮时 `work close`，全部未完成条目须逐一显式 `--move ITEM`；它只生成规范 `.done.json`，之后走环节 B/C 与 agile-backlog 阶段 4。

全局产物只存中枢；接收方只获版本化快照、独立回执。产物来源与实际正文采集一次（复用 `references/handoff-template.md`）；`issue/decision` 随时回 agile-backlog，不等所有包回执或 Sprint 关闭。

### 环节 B：DoD 关闭
- 读取 `sprints/{sprint文件}.done.json`：
  - 存在 → 工作包模式**先跑 `python <plugin>/scripts/agile.py check HUB` 再核对 DoD**；任何 completed 业务条目缺整体验收都拒绝继续，不凭包回执补写验收。按 completed / moved_next 读取 feedback：`reason` 展示未完成原因，`issue/decision` 路由 agile-backlog（已即时处理的不重复建条目），本环节不代产品裁决
  - 不存在 → 单执行者可请用户人工确认每条完成情况；工作包模式必须先按环节 A 的 `work close` 生成，不允许人工绕过
- 逐条过 `agile-docs/DOD.md` 的 Sprint 完成标准；单执行者含交接契约的任务须已产出交接文档，否则归入 moved_next。工作包模式核对已验收产物与整体验收；发现不一致即停，不改写规范 `.done`，不把已整体验收条目降回待办或删验收记录
- 在本 Sprint 文件内追加「条目状态建议」（通过 → 已完成；未完成 → 移至下个Sprint），格式见 `references/sprint-template.md §二`；工作包模式必须与 `work close` 结果一致
- 写完停，问"是否关闭本 Sprint？"；工作包模式若用户已明确要求关闭且无新增决策，完成上述门禁后接环节 C，不重复询问

### 环节 C：关闭
- 改写文件头 `- 执行结果:` 行的值（`.done.json` 文件路径 或 "人工确认"）——模板已带此行，不新增行，也不把来源并入状态值
- 将 Sprint 文件头 `- 状态:` 改为 `已关闭`，只写状态词（需要备注用全角括号另附，不夹带其它键值）
- **统计快照重算**：跑 `agile.py stats`，输出附进本 Sprint 文件「变更记录」段（没有脚本时才自己全量重算，禁止在旧数字上增量加减）
- **发布提示**：问用户"本 Sprint 完成条目是否并入 release（`releases.json`）或明确不发布"——**只提示路由到 agile-backlog 发布管理入口，不写 releases.json**（写权限归它，见 `agile-backlog/references/release-rules.md`）
- 提示用户完整闭环：入口下次激活时检测到 `.done.json` 即**默认执行闭环**——Sprint 已由本环节关闭，剩下的「同步 backlog → 处理 feedback → 改后缀 `.done.processed.json` → 移入 `archive/` 归档」由 agile-backlog 阶段 4 执行，**本技能不碰**。链路见 `using-agile/references/sprint-schema.yaml` 的 `lifecycle`
- 仅单执行者可无 `.done.json` 人工确认关闭：由本环节提示用户路由 agile-backlog 阶段 4，按文件内「条目状态建议」同步（含 `planned_sprints` 戳记）与归档，不由本技能代劳；工作包模式阶段 4 同样维护戳记，但保留 `work finish` 写入的整体验收，不覆盖或降级

## 4. 写完即停（结构化审阅）

按 `using-agile/references/probing-protocol.md §四` 结构化审阅（重点列：容量参数 / 取条依据 / Sprint 目标 / 交接点或包依赖 × 来源）。决策未确认即停；已授权工作包机械步骤按 `using-agile/references/workflow.md §三（工作包交付）` 连续完成后汇报，不逐文件再停。

## 5. 硬约束
- 规划写 `sprints/sprint-{序号:03d}-{日期}.md`（命名含序号+日期，不用 `current.md`）；工作包的全局状态与导出快照只经环节 A 脚本生成，不顺手改全局 PRD / VISION / ARCHITECTURE / ADR。
- ✅ 写前问询遵循 `using-agile/references/probing-protocol.md`：容量参数（人数/工作日/专注系数）必经用户确认，禁止静默默认；Sprint 目标须可陈述（§2）。
- ✅ 关闭 Sprint 前逐条过 DoD（独立出口门禁 ③）；关闭即把 `- 状态:` 改为 `已关闭`（值只写状态词）、改写 `- 执行结果:` 行，不删除。
- ❌ 不写 RETRO.md / RELEASE.md / FB-NNN.md。`archive/` 子目录（Sprint 归档位）由 agile-backlog 阶段 4 在闭环归档时创建，规划期不预建、也不在它之外发明别的目录。❌ 不写 `risks.json` / `releases.json` / `decisions.json`（归 agile-backlog，本技能只在规划/关闭时展示与提示路由）。
- 不在 Sprint 文件中追踪本地 checkbox、子任务与阻塞；工作包依赖/回执/验收的全局状态只由 `delivery.json` 脚本维护，不能借此绕过重规划与战略冲突门禁。
- ✅ 「闭环检查」清单用 `- [ ]` checkbox，关闭前逐项核对（这是关闭核对清单，非执行态追踪）。
- 不直接修改 `backlog.json` 的 `status` 或 `delivery_acceptance`；工作包整体验收仅 `work finish` 写，单执行者与后续 `.done` 闭环同步归 agile-backlog 阶段 4。

## 6. 门禁
- **DoD 出口门禁（③）**：有未估算/未过 DoD/未验收条目时要关闭 Sprint → 停下，逐条过 DoD。
- **冲突 / 歧义即停**（见 `using-agile/references/gate-protocol.md`）。
