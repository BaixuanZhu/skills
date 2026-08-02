# 架构产出参考（agile-strategic 阶段 B）

本技能产出两个独立文件：`agile-docs/ARCHITECTURE.md`（C4 图，可演进覆盖）和 `agile-docs/ADR.md`（架构决策记录，章节式不可篡改）。

## 一、ARCHITECTURE.md 模板（C4 合并）

```markdown
# 架构图（C4）

> 维护说明：本文件可演进覆盖更新。Git 已记录历史，无需在文件内保留版本冗余。

## Level 1: 系统上下文图（Context）

{Mermaid C4 Context Diagram}

> 显示系统边界、外部用户、外部系统。每个外部实体 1 个节点。

## Level 2: 容器图（Containers）

{Mermaid C4 Container Diagram}

> 显示系统内部容器（Web / API / 数据库 / 缓存 / 消息队列等）及其交互。
```

**演进规则**：架构变化时**直接覆盖**本文件。不新建版本文件、不保留旧版本章节。Git diff 即历史。

## 二、ADR.md 模板（章节式 + 强制 4 行结构）

### 顶部索引（可选但推荐）

```markdown
# 架构决策记录（ADR）

> 维护说明：每个 ADR 一章节，状态变更只能改「状态/被替代」字段，不可改决策内容。

## 索引

| ADR | 标题 | 状态 | 日期 |
|-----|------|------|------|
| ADR-001 | {标题} | Accepted | 2026-07 |
| ADR-002 | ~~{原标题}~~ | Superseded by ADR-005 | 2026-07 |
...

---

```

### 单条 ADR 强制 4 行结构

```markdown
## ADR-006 {标题}

- 状态: {Proposed/Accepted/Superseded by ADR-XXX/Deprecated} ({YYYY-MM-DD}) · 替代: {原 ADR 编号 或 —} · 被替代: {新 ADR 编号 或 —}
- 背景: {1-3 句，问题陈述，为什么需要决策}
- 决策: {1-3 句，结论 + 关键约束，决策了什么}
- 后果: + {正面 1-3 bullet} / - {负面 1-3 bullet} / 缓解: {缓解措施}
```

### 替代机制

- 在 ADR.md **底部追加新章节** `## ADR-013 {新标题}`
- 在旧章节 `状态:` 字段改为 `Superseded by ADR-013`
- 在旧章节 `被替代:` 字段填 `ADR-013`
- **旧章节"背景/决策/后果"内容不动**（不可篡改）
- 顶部索引表对应行状态列同步更新

## 三、ADR 禁止内容清单

权威清单见 `using-agile/references/gate-protocol.md §二 ④`。写 ADR 时若包含禁止内容 → 立即停下，按清单引导到正确归属。

## 四、选型辩论产物去向

选型辩论（SKILL.md §3.1 步骤 4）中产生的候选对比表与权衡过程，各有固定去向，不进 ADR（与门禁 ④ 兼容）：

| 产物 | 去向 |
|------|------|
| 候选对比表、权衡过程 | 留在对话中，不落盘 |
| 裁决结论 + 关键约束 | ADR 4 行结构（背景可一句带过"已评估 X/Y，因 Z 选定"） |
| 用户要求对比表留档 | 代码仓库 `docs/research/`，不进 agile-docs/ |
| 用户坚持与约束矛盾的选择 | 在 ADR 背景行如实记录质疑点与用户裁决 |

## 五、C4 图资源（参考）

- Mermaid C4 Context：https://mermaid.js.org/syntax/c4.html#c4-context-diagram-c4context
- Mermaid C4 Container：https://mermaid.js.org/syntax/c4.html#c4-container-diagram-c4container
- 命名约定：节点用 PascalCase，关系用动词描述
