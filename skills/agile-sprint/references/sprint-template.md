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
- 来源: PRODUCT-BACKLOG.yaml（按 priority 顶部取条目）
- 消费方: 本文件是单向交付，任务状态由消费 Agent 自行追踪
- 执行结果: sprints/sprint-{序号:03d}-{日期}.done.yaml（由消费 Agent 生成）

## 任务清单

- T-001 {标题} ({点}) → ADR-{NNN}
- T-002 {标题} ({点})
- F-001 {标题} ({点})
...

## 闭环检查（关闭前过，纯列表，不使用 checkbox）

- 关联的 .done.yaml 已存在并读取（或无 .done 时用户已人工确认完成情况）
- DoD 全部通过
- 本文件头"状态"改为"已关闭"
- 文件头标注执行结果来源（.done 路径或"人工确认"）

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

### 格式与约束（单一权威源）

`.done.yaml` 的字段格式、命名、路径与约束以 `using-agile/references/sprint-schema.yaml`（初始化时复制到 `agile-docs/interfaces/`，消费 Agent 读取的接口契约）为**唯一权威定义**，本文件不重复维护。

### 使用流程

```
消费 Agent 读 sprint-NNN-YYYYMMDD.md → 执行 → 产出 sprint-NNN-YYYYMMDD.done.yaml

用户将 .done 放入 sprints/ → 调用入口"关 Sprint"
    → agile-sprint 读 .done → DoD 检查 → 关文件
    → 入口下次检测到 .done + sprint 已关闭 → 路由到 agile-backlog 同步
    → 同步后改后缀为 .done.processed，留痕
```
