# 敏捷套件 v4.4.0 终评（盲评 Agent B）

> 评分对象：r3 修复后的当前工作区。rubric 复用 `../darwin-validation-v4.4.0/rubric.md`。本报告由盲评子 agent 原样归档。

## 1. using-agile（88.5）

D1 9 / D2 9 / D3 9 / D4 9 / D5 9 / D6 9 / D7 8 / D8 9。

- D6：8 个 references 全部被正文引用且路径可达（change-matrix:89、gate-protocol:83、init-template:70、interview/probing:108、sprint-schema:70、status-routing:59、strategy-conflict-template:76）。
- D7 扣分：§5 门禁触发三 bullet（SKILL.md:77-79）与 gate-protocol.md:9-11 近乎逐字重复。

## 2. agile-strategic（88.0）

D1 9 / D2 9 / D3 9 / D4 9 / D5 9 / D6 8 / D7 8 / D8 9。

- D7 扣分：vision-template.md:1/:3 残留特定项目名「815 Market」；来源分类法与 probing-protocol 不一致（P3）。

## 3. agile-backlog（88.0）

D1 9 / D2 9 / D3 9 / D4 9 / D5 9 / D6 8 / D7 8 / D8 9。

- D7 扣分：SKILL.md:133「评估**上游** Sprint 是否需要改变」——Sprint 是 Backlog 的下游消费方，方向词错误（见 P2-2）。

## 4. agile-sprint（88.0）

D1 9 / D2 9 / D3 9 / D4 9 / D5 9 / D6 8 / D7 9 / D8 9。

- D7 满分层：所有权边界干净（§5 不直接改 PRODUCT-BACKLOG）；估点定义权威显式让渡给 backlog-rules（sprint-rules.md:34），无规则重复。

## 套件均值

(88.5 + 88.0 + 88.0 + 88.0) / 4 = **88.1**

## 问题清单

**P1：无 P1。**

### P2（2 条）
1. `vision-template.md:1,3` —— 「815 Market 愿景硬结构」「815 融合版」特定项目残留，通用技能不应携带。
2. `change-matrix.md:32-38` + `agile-backlog/SKILL.md:133` —— 方向术语错乱：节标题「下游影响评估（底层变更 → 上层是否需要改）」、正文「评估依赖它的上层（如 Sprint）」、表头「上游评估点」、backlog:133「评估上游 Sprint」——按分层模型 Sprint 是下游；且表中混入「VISION 原则→Backlog 排序」行（顶层→下层，属 §一 传播方向）。各行规则自明，agent 大概率不会执行错，但上游/上层/下游三词在套件内无一致定义。

### P3（5 条）
1. `using-agile/SKILL.md:77-79` vs `gate-protocol.md:9-11` 写前门禁触发条件跨文件近乎逐字重复。
2. 来源标注分类法不一致：probing-protocol:38-40 三分类 vs c4-adr.md:55 两分类。
3. 跨技能相对路径 npx 单独安装时断裂（dependencies 已声明，记风险不计缺陷）。
4. `status-routing.md:16`（负责技能=using-agile）vs `strategy-conflict-template.md:14`（using-agile 或 agile-strategic 生成）字面不一致（列语义是路由非生成方，实际不冲突）。
5. `agile-strategic/SKILL.md:62` 决策点 3「终稿（不可逆，变更走 ADR 替代）」——定位声明变更走 ADR 语义牵强，易误路由。

## D8 干跑

6/6 通过（T1–T6），无卡住、无跨层越权、无静默默认路径。
