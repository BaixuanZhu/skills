# Sprint 模板（agile-sprint 参考）

Sprint 是全项目共享计划，不记录消费 Agent 的本地 checkbox/子任务。默认单执行者使用下方原 `.done` 路径；显式工作包模式按 `using-agile/references/workflow.md §三（工作包交付）` 与 `using-agile/references/sprint-schema.yaml` 的 `work_delivery`，计划留中枢，不整份分发。生成时只保留所选模式的交付/回填段。

## 一、Sprint 文件命名

    sprints/sprint-{序号:03d}-{起始日期}.md

- **序号**：扫描 `sprints/` 与 `sprints/archive/`（归档历史）下已有 `sprint-NNN-*.md`，取两处最大序号 +1；两处全空才从 001 起（只扫活目录会在归档后从 001 重来、与归档撞号）。三位补零
- **起始日期**：ISO YYYYMMDD（仅年月日）
- **示例**：`sprint-001-20260727.md`

## 二、Sprint 文件模板

```markdown
# Sprint: {主题中文描述}

- 文件名: sprint-{序号:03d}-{日期}
- 状态: 规划完成
- 周期: {YYYY-MM-DD} ~ {YYYY-MM-DD}
- 目标: {一句 Sprint 目标}
- 容量: 团队 {N} 人 × {D} 天 × {专注系数} ≈ {可用点} 点
- 估点体系: 斐波那契（默认）/ 线性（仅纯研究型 Sprint，见 `references/sprint-rules.md §二`）
- 来源: agile-docs/backlog.json（按 priority 顶部取条目）
- 消费方: {单执行者：交付本文件；工作包：本文件留中枢，仅导出各接收方快照；本地任务由消费 Agent 自行追踪}
- 执行结果: 待回填（单执行者写 .done.yaml；工作包由中枢 work close 生成，见所选模式回填段）

## 任务清单

- T-001 {标题} ({点}) → ADR-{NNN}
- T-002 {标题} ({点})
- F-001 {标题} ({点})
...

> `backlog.repo` 仅为可选单仓归属；有值才标 `[repo: {仓库名}]`。跨仓业务条目省略 repo，实际接收方仓库在工作包内。任务清单不按仓库拆需求、不重复计点。

## 工作包交付（仅工作包模式保留）

- 同一业务条目可对应多个包：如 F-001 对应 WP-001 后端与 WP-002 前端；此处不另算点数。接收方、具体包依赖与版本身份见中枢 delivery.json，字段不在本文件另定义。
- 全项目 PRD/C4/ADR 与本计划留中枢；执行者仅接收该包选定的冻结上下文与已验收上游产物正文，不读其他包实现细节。
- 产物正文复用 `references/handoff-template.md`，记录来源与实际内容一次；已有版本化契约不额外要求交接文档。
- 回填独立 JSON 回执，由中枢导入并逐包验收；全部包通过后再整体业务验收，不能凭回执汇总标完成。执行者不直接改全局 Backlog/delivery 或生成 Sprint .done。
- `feedback.issue/decision` 随时回 agile-backlog，不等待本 Sprint 关闭；回执汇总不替代产品裁决。
- 用户要求关闭时，中枢逐项显式指定未完成条目，用 work close 生成规范 .done.yaml，再走 DoD 与通常闭环。命令见 `agile-sprint/SKILL.md §3（工作包交付）`，协议见 `using-agile/references/workflow.md §三（工作包交付）` 与 `using-agile/references/sprint-schema.yaml` 的 `work_delivery`。

## 交接契约（仅单执行者路径，存在跨仓先后依赖时生成）

> 仅当已独立成立的业务/技术条目有跨仓先后依赖时生成；不为了套此表把一个业务需求拆成前后端需求。交接文档模板见 `references/handoff-template.md`。

| 交接点 | 上游任务（产出方） | 下游任务（消费方） | 交接文档 |
|--------|--------------------|--------------------|----------|
| H-001 | T-003 后端接口 [repo: api-server] | F-002 前端页面 [repo: web-app] | `sprints/handoffs/sprint-{序号}-H001.md` |

- **上游任务完成条件**：任务完成 + 已按 `references/handoff-template.md` 产出对应交接文档（未产出 → DoD 关闭时归入 moved_next）
- **下游任务开始条件**：开始前必须读取对应交接文档（消费 Agent 执行义务，写入本 Sprint「回填要求」段同属硬性义务）
- 交接文档随本 Sprint 归档（`sprints/handoffs/`），不随某个具体仓库提交

## 回填要求（仅单执行者路径，消费 Agent 必读）

> 本段仅随单执行者 Sprint 文件交付；工作包模式用上方「工作包交付」段，不要求各执行者回填整个 Sprint。

单执行者在任务执行完毕后，**必须**生成执行结果回填文件，否则规范层无法关闭本 Sprint、Backlog 状态无法同步：

- **回填文件**：`sprints/sprint-{序号:03d}-{日期}.done.yaml`（与本文件同名、同目录）
- **时机**：执行完毕后即回填（含部分完成——完成的进 completed，未完成的进 moved_next）
- **格式**（字段定义见 `agile-docs/interfaces/sprint-schema.yaml`）：

  ```yaml
  completed:
    - T-001
    - F-002
  moved_next:
    - T-003
  feedback:
    - item: "T-003"
      type: "reason"        # reason=未完成原因 / issue=新问题 / decision=需产品裁决
      note: "第三方 API 配额不足，需产品确认降级方案"
```

- **约束**：只能回填本文件「任务清单」中出现的 ID；清单内未出现在 completed/moved_next 的条目视为未执行，DoD 关闭时归入 moved_next；**含「交接契约」的任务**，进 completed 前须已产出对应交接文档
- **feedback 可选但鼓励**：执行中发现的问题、未完成原因、需产品层裁决的事项写在这里，闭环时由规范层处理（issue 转 Backlog 新条目、decision 请用户裁决并记 `decisions.json`）——不写则视为无反馈
- **执行中随时回流**：发现风险、缺陷或需产品裁决的事项**不必等回填**——随时路由 agile-backlog 对应入口（风险管理 / 发布管理 / 决策记录，见 `using-agile/references/workflow.md`）；与 feedback 重复的不重复建条目
- **回填即触发闭环**：回填文件放入 `sprints/` 后，用户调用入口 → 入口检测到 `.done.yaml` **默认执行闭环**：DoD 检查 → 关闭 Sprint → 同步 Backlog → 处理 feedback

## 闭环检查（关闭前逐项核对，全部通过方可关闭）

- [ ] 关联的 .done.yaml 已存在并读取（仅单执行者可无 .done 人工确认；工作包须由 work close 生成）
- [ ] 工作包模式：DoD 前已跑 agile.py check，无 completed 条目缺整体验收；规范 .done 与 delivery_acceptance 一致（单执行者跳过本项）
- [ ] DoD 全部通过
- [ ] 统计快照已重算（`agile.py stats` 输出附在「变更记录」段）
- [ ] `- 执行结果:` 行的值改为 .done 路径或"人工确认"（模板已带此行：改写，不新增行、不并入状态值）
- [ ] 本文件头 `- 状态:` 的值改为 `已关闭`（只写状态词，备注另起一行）

## 条目状态建议（环节 B DoD 关闭时追加，规划时不写）

- T-001：已完成（DoD 全部通过）
- T-003：移至下个Sprint（未过：{具体 DoD 条目}）
- F-001：已完成（DoD 全部通过）

> 关闭后本文件为只读历史。入口检测 .done.yaml 默认闭环（agile-backlog 阶段 4 同步与维护 planned_sprints；工作包既有 delivery_acceptance 不覆盖、不删除，不把已整体验收条目降回待办），完成后本文件连同留痕移入 `sprints/archive/`。

## 变更记录（关闭后追加；本 Sprint 期间的所有变更按时间顺序记录）

| 时间 | 变更 | 来源 |
|------|------|------|
| {YYYY-MM-DD HH:MM} | Sprint 关闭：本批完成 {N} 条 / 移下 Sprint {M} 条 / 反馈 {K} 条 | agile-sprint 关闭环节（脚本 + 人工裁决） |
| {YYYY-MM-DD HH:MM} | 统计快照：总 {X} 条 {Y} 点 / 有效 {X'} 条 {Y'} 点 / ADR 覆盖 {P}% | `agile.py stats` 输出 |
| {YYYY-MM-DD HH:MM} | {其它裁决/追加注记} | {用户裁决 / agent 推荐} |

> **变更日志与统计区分区**：统计快照只保留当前一句口径；历史快照与全部变更走本段。禁止把历史快照累计进统计区。
```

## 三、环节定义

Sprint 生命周期 3 环节（规划/DoD 关闭/关闭）的定义详见 `SKILL.md §3`。本文件只提供文件模板，不重复环节细则。

## 四、执行结果回传（.done.yaml）

单执行者执行完毕后在 `sprints/` 下生成同名 `.done.yaml`；工作包模式仅由中枢 `work close` 生成。该文件是 DoD 检查与阶段 4 同步依据，不是工作包回执，也不能替代整体验收。

### 格式与约束

`.done.yaml` 的字段格式、命名、路径与约束见 `using-agile/references/sprint-schema.yaml`（初始化时复制到 `agile-docs/interfaces/`），本文件不重复。

### 闭环链路（不在此展开）

`.done.yaml` 的生命周期见 `using-agile/references/sprint-schema.yaml` 的 `lifecycle`（工作包另见 `work_delivery`）与 `SKILL.md §3 环节 B/C`：写入后经过校验、DoD、关闭、Backlog 同步与反馈处理，再改 `.done.processed.yaml` 留痕归档。
