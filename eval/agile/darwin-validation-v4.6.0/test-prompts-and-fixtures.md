# v4.6.0 达尔文评测 —— fixtures 与实跑记录（2026-09-11）

> 对象：v4.6.0 两脚本（inventory.mjs / check-consistency.mjs）的实跑验证。
> fixtures 在 `/c/Users/zbxComputer/AppData/Local/Temp/agile-eval-v4.6.0/agile-docs/`（本仓库 `tmp/` 外，scratch 性质）。

## 一、fixtures 列表

| fixture | 内容 | 验证目标 |
|---|---|---|
| F1-healthy | 7 条（1 已撤回 + 1 confirmed=false），覆盖 Must/Should/Could 优先级与 待办/已撤回 状态 | inventory 分桶准确 / strict consistency 通过 |
| F2-drift-priority-status | F1 + yaml 改 T-101 priority=Must→Should + F-101 status=待办→已完成 | strict consistency 检出 priority + status 2 处 |
| F3-id-drift | F1 + yaml 新增 F-DUP 不在 md | strict consistency 检出 id 集合 + 条目数 2 处 |

## 二、实跑脚本命令

```bash
# F1-healthy: 全过
node assets/scripts/inventory.mjs
node assets/scripts/check-consistency.mjs --strict   # exit 0

# F2-drift-priority-status: --strict 阻塞
node assets/scripts/check-consistency.mjs --strict   # exit 1

# F3-id-drift: --strict 阻塞
node assets/scripts/check-consistency.mjs --strict   # exit 1
```

## 三、F1 inventory 样本输出（完整）

```
## Backlog 盘点快照

**总条目**    7 条 / 25 点
**有效条目**(排除已撤回)  7 条 / 25 点

### 按优先级
- Must     3 条 / 10 点
- Should   2 条 / 5 点
- Could    2 条 / 10 点

### 按状态
- 待办       6 条 / 23 点
- 已撤回      1 条 / 2 点

### 按类型
- 技术       2 条 / 10 点
- 功能       5 条 / 15 点

### ADR 关联覆盖
- 7 / 7 (100%) 有效条目有关联 ADR

⚠ **未确认条目**: 1 条状态为「待办」且 confirmed=false——Sprint 取用前需显式确认
```

JSON 输出版本（前 20 行）：

```json
{
  "total": {
    "count": 7,
    "points": 25
  },
  "active": {
    "count": 7,
    "points": 25,
    "note": "排除已撤回条目,等于\"参与排序的有效条目\""
  },
  "by_priority": {
    "Must": { "count": 3, "points": 10 },
    "Should": { "count": 2, "points": 5 },
    "Could": { "count": 2, "points": 10 }
  },
  ...
  "unconfirmed_active": 1
}
```

> 「有效条目」与「总条目」数字相同是因为本 fixture 中 1 条 withdrawn 仍计入总数但归到「已撤回」分桶——脚本设计如此（撤回条目仍留痕可见），输出文案需 polish 为「N 条 active，扣除 M 条 withdrawn」，已记 v4.6.0 遗留。

## 四、实跑发现的 2 处脚本缺陷（已修）

### S1：md「关联」列的条目 id 被误当 ADR ref

- **场景**：md 表格「关联」列既可能写 ADR 编号（`ADR-001`），也可能写条目 id（`T-101` 表示下游依赖）。
- **原行为**：脚本无差别拆分全部比对 yaml `adr_refs[]`，所以 F-101（md 写 `T-101`）yaml 没存 → 报 `.md 含 T-101 但 .yaml 无`。
- **修法**：仅保留 `^ADR[-]?\d+$` 模式，跳过条目 id 类引用。

### S2：md 人类用语「已撤回」 vs yaml schema 枚举 `withdrawn`

- **场景**：契约规定 md 写人类用语「已撤回」、yaml 写 schema 枚举 `withdrawn`（机器可识别）。
- **原行为**：脚本严格字符串比对 → 报 `.md="已撤回" vs yaml="withdrawn"`。
- **修法**：加 statusAlias `{ '待办':'待办', '已完成':'已完成', '已撤回':'withdrawn' }`，md 端先映射再比对。

两处修复同步到 `plugins/agile/skills/agile-backlog/assets/scripts/check-consistency.mjs` 镜像。
