# Sprint 模板（agile-sprint 参考）

Sprint 规划文件模板。不含执行态字段，消费 Agent 自行追踪进度。

## 一、Sprint 文件命名

    sprints/sprint-{序号:03d}-{起始日期}.md

- **序号**：扫描 `sprints/` 目录下已有 `sprint-NNN-*.md`，取最大序号 +1；目录为空则从 001 起。三位补零
- **起始日期**：ISO YYYYMMDD（仅年月日）
- **示例**：`sprint-001-20260727.md`

## 二、Sprint 文件模板

```markdown
# Sprint: {主题中文描述}

- 文件名: sprint-{序号:03d}-{日期}
- 状态: 规划完成（关闭时改为"已关闭"）
- 周期: {YYYY-MM-DD} ~ {YYYY-MM-DD}
- 目标: {一句 Sprint 目标}
- 容量: 团队 {N} 人 × {D} 天 × {专注系数} ≈ {可用点} 点
- 估点体系: 斐波那契（默认）/ 线性（仅纯研究型 Sprint，见 `references/sprint-rules.md §四`）
- 来源: PRODUCT-BACKLOG.yaml（按 priority 顶部取条目）
- 消费方: 本文件是单向交付，任务状态由消费 Agent 自行追踪
- 执行结果: 待回填（消费 Agent 执行后生成 .done.yaml，见下方「回填要求」段）

## 任务清单

- T-001 {标题} ({点}) → ADR-{NNN}
- T-002 {标题} ({点})
- F-001 {标题} ({点})
...

## 回填要求（消费 Agent 必读 · 硬性义务）

> 本段随 Sprint 文件一并交付给消费 Agent，用于**免人工提醒地**完成执行结果回填。

执行本 Sprint 的消费 Agent 在任务执行完毕后，**必须**生成执行结果回填文件，否则规范层无法关闭本 Sprint、Backlog 状态无法同步：

- **回填文件**：`sprints/sprint-{序号:03d}-{日期}.done.yaml`（与本文件同名、同目录）
- **时机**：执行完毕后即回填（含部分完成——完成的进 completed，未完成的进 moved_next）
- **格式**（字段定义见 `agile-docs/interfaces/sprint-schema.yaml`）：

  ```yaml
  completed:
    - T-001
    - F-002
  moved_next:
    - T-003
```

- **约束**：只能回填本文件「任务清单」中出现的 ID；清单内未出现在 completed/moved_next 的条目视为未执行，DoD 关闭时归入 moved_next
- **回填即触发闭环**：回填文件放入 `sprints/` 后，用户调用入口 → 规范层据此做 DoD 检查 → 关闭 Sprint → 同步 Backlog

## 闭环检查（关闭前逐项核对，全部通过方可关闭）

- [ ] 关联的 .done.yaml 已存在并读取（或无 .done 时用户已人工确认完成情况）
- [ ] DoD 全部通过
- [ ] 文件头标注执行结果来源（.done 路径或"人工确认"）
- [ ] 本文件头"状态"改为"已关闭"

## 条目状态建议（环节 B DoD 关闭时追加，规划时不写）

- T-001：已完成（DoD 全部通过）
- T-003：移至下个Sprint（未过：{具体 DoD 条目}）
- F-001：已完成（DoD 全部通过）

> 关闭后本文件为只读历史归档。状态同步由入口检测 .done 后路由到 agile-backlog 执行。
```

## 三、环节定义

Sprint 生命周期 3 环节（规划/DoD 关闭/关闭）的定义详见 `SKILL.md §3`。本文件只提供文件模板，不重复环节细则。

## 四、执行结果回传（.done.yaml）

消费 Agent 执行完毕后，须在 `sprints/` 下生成 `.done.yaml` 文件，与 Sprint 文件同名。
该文件是规范层 DoD 检查和状态同步的依据。

### 格式与约束

`.done.yaml` 的字段格式、命名、路径与约束见 `using-agile/references/sprint-schema.yaml`（初始化时复制到 `agile-docs/interfaces/`），本文件不重复。

### 闭环链路（不在此展开）

`.done.yaml` 的完整生命周期——写入（消费 Agent）→ DoD 检查（agile-sprint 环节 B）→ 入口路由同步（.done + Sprint 已关闭 → agile-backlog）→ 改后缀 `.done.processed.yaml` 留痕——定义在 `using-agile/references/sprint-schema.yaml` 的 `lifecycle` 字段与 `SKILL.md §3 环节 C`。**行为细则归技能正文，模板只承载文件结构**，本段为指针非内容。
