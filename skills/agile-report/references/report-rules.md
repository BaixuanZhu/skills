# 报告数据规则（agile-report 参考）

## 一、数据源字段速查

报告读取的字段名严格照搬上游技能产物，**不改写**：

| 数据源文件 | 字段 | 取值 | 字段定义源 |
|---|---|---|---|
| `sprints/sprint-NNN-*.md` 文件头 | `- 状态:` | `规划完成` / `已关闭` | agile-sprint/sprint-template.md §一 |
| `sprints/sprint-NNN-*.md` 文件头 | `- 周期:` | `YYYY-MM-DD ~ YYYY-MM-DD` | 同上 |
| `sprints/sprint-NNN-*.md` 任务清单 | 行格式 | `- T-001 {标题} ({点}) → ADR-{NNN}` | sprint-template.md §二 |
| `sprints/sprint-NNN-*.done.yaml` | `completed:` | ID 列表 | using-agile/sprint-schema.yaml |
| `sprints/sprint-NNN-*.done.yaml` | `moved_next:` | ID 列表 | 同上 |
| `agile-docs/PRODUCT-BACKLOG.yaml` | `items[].priority` | `Must`/`Should`/`Could`/`Won't`（**英文首大写**） | backlog-rules.md §七 |
| `agile-docs/PRODUCT-BACKLOG.yaml` | `items[].status` | `待办`/`已完成`/`移至下个Sprint`（**中文**） | 同上 |
| `agile-docs/PRODUCT-BACKLOG.md` 表格 | `点` 列 | 斐波那契 `1/2/3/5/8/13` | backlog-rules.md §二 |
| `agile-docs/DOD.md` | `## 项目画像` 表 | `项目类型`/`团队人数与技能栈`/`代码基础` | using-agile/init-template.md §二 |

**关键陷阱**：
- `priority` 取值是**英文**（Must/Should），`status` 取值是**中文**（待办/已完成）——别混。
- YAML **不含** `point` / `title` 字段——要拿点数/标题必须回读 `.md` 表格（按 id 定位）。
- `.done.yaml` 同步完成后会改名 `.done.processed`（留痕）——报告遍历时两者都要扫，`.done.yaml` 是未同步的、`.done.processed` 是已同步的，内容相同。

## 二、聚合公式

### 2.1 阶段整体完成率

```
阶段整体完成率 = Σ(各纳入 Sprint 的 completed 数) / Σ(各纳入 Sprint 的任务总数) × 100%
```

- 分子：各 Sprint `.done.yaml` 的 `completed` 列表长度之和
- 分母：各 Sprint **`## 任务清单` 节内**的任务行数之和（仅 `- T-NNN {标题} ({点})` / `- F-NNN {标题} ({点})` 格式行）
- ⚠️ **必须限定在 `## 任务清单` 节内**——同文件「条目状态建议」节也有 `- T-001：已完成` 开头的行，朴素正则会把任务数误算翻倍。区分依据：任务清单行含 `{点}` 和 `→ ADR`（见 §一）
- 纳入范围由 §2b 用户确认（最近 N 个已关闭 Sprint / 日期范围 / 里程碑）

### 2.2 单 Sprint 完成率（用于趋势柱状图）

```
Sprint 完成率 = len(completed) / 任务总数 × 100%
```

各 Sprint 独立计算，按文件名日期排序成趋势序列。

### 2.3 承诺 vs 完成点数

```
承诺点 = Σ(本 Sprint 所有任务清单条目的 point)
完成点 = Σ(completed 列表中条目的 point)
```

- point 从 `PRODUCT-BACKLOG.md` 表格按 id 回读（YAML 无 point）
- 找不到 id 对应 point（Backlog 已删条目等）→ 该条目 point 计 0，但在报告中标注"点数缺失 N 条"

### 2.4 三态分布

每个纳入 Sprint 的任务分三态：

| 态 | 判定 | 数据源 |
|---|---|---|
| **已完成** | 在 `.done.yaml` 的 `completed` 列表 | `.done.yaml` |
| **移出** | 在 `.done.yaml` 的 `moved_next` 列表 | `.done.yaml` |
| **未执行** | 在 Sprint 任务清单内，但 `completed` 与 `moved_next` 两列表都无 | 清单 ∖ (completed ∪ moved_next) |

**无 `.done.yaml` 时**（状态 ②）：读 Sprint 文件的「条目状态建议」节（agile-sprint 环节 B 追加）——格式 `- T-001：已完成` / `- T-003：移至下个Sprint`。该节也不存在 → 整个 Sprint 标"完成度未知"，不脑补数字。

**阻塞原因取数（完整态 ① 同样适用）**：`moved_next` 列表只给 id 不给原因文本。阻塞项表的"原因"列须回读对应 Sprint 文件的「条目状态建议」节——该节格式为 `- T-003：移至下个Sprint（未过：{具体 DoD 条目}）`，括号内的 `{具体 DoD 条目}` 就是原因。无论完整态 ① 还是降级态 ②，取阻塞原因都走这个路径。

### 2.5 Backlog 优先级分布（用于饼图）

从 `PRODUCT-BACKLOG.yaml` 的 `items[]` 统计 priority × status 交叉：

| | 待办 | 已完成 | 移至下个Sprint |
|---|---|---|---|
| Must | ? | ? | ? |
| Should | ? | ? | ? |
| Could | ? | ? | ? |

报告重点展示"Must 待办数"（甲方最关心"核心需求还剩多少没做"）。

## 三、降级判据与 git log 解析

### 3.1 降级态判定（按 §0 三态表机械执行）

| 扫描结果 | 降级态 |
|---|---|
| `agile-docs/` 存在 + `sprints/*.done.yaml`（或 `.done.processed`）≥1 | ① 完整 |
| `agile-docs/` 存在 + `sprints/` 有 `.md` 但无 `.done.*` | ② 部分 |
| `agile-docs/` 不存在 或 `sprints/` 不存在/为空 | ③ 全降级 |

### 3.2 git log 解析规则（状态 ③ 用）

无敏捷产物时，从 git log 提取进度信号：

```bash
git log --since="{起始日期}" --until="{结束日期}" --pretty=format:"%h|%ad|%s" --date=short
```

**分类启发式**（按 commit message 前缀归类，不脑补）：

| message 模式 | 归类 | 报告术语 |
|---|---|---|
| `feat:` / `add` / `新增` | 新功能 | "本期新增功能 N 项" |
| `fix:` / `修复` / `修正` | 缺陷修复 | "本期修复问题 N 项" |
| `refactor:` / `重构` | 重构 | "技术优化 N 项" |
| `test:` / `docs:` / `chore:` | 工程维护 | 不单独计数，合并进"工程维护" |
| 无前缀 | 其他 | 按关键词二次匹配，匹配不上标"其他" |

**降级报告内容**（比完整报告精简）：
- 封面标"数据来源：git log（简化版）"
- 无完成率%（git log 算不出）→ 改展示"提交趋势"（按周/双周聚合 commit 数）
- 无 Backlog 分布 → 改展示"提交类型分布"饼图（feat/fix/refactor/其他）
- 顶部 disclaimer："本报告基于 git 提交记录生成，不含任务级完成度数据"

## 四、一致性校验（复用 agile-backlog 规则）

读 `PRODUCT-BACKLOG.yaml` 前必跑（规则源自 `agile-backlog/references/backlog-rules.md §七`）：

1. id 集合一致（.md 表格行与 .yaml items 无遗漏/多余）
2. 条目数一致
3. 同 id 的 priority+status 一致

任一不符 → 停下报告差异（列出 id 缺失/字段不一致的条目），请用户确认以哪份为准后再继续聚合。**禁止**在不一致状态下强行挑一份算下去。
