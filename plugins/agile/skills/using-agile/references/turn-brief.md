# 每轮提示文本（hook 的真源）

`agile.py` 的 `hook-prompt` / `hook-session` 按当前阶段读这里的一段注入上下文。脚本只判断阶段、不内置文案：改提示词改这个文件即可，不用动代码。

**只被读取的块**：`[agile-brief:阶段]` … `[/agile-brief:阶段]`，其它内容不会进上下文，可以随意写给人看的说明。

## 编写规则

1. **一段只给下一步 + 这一步最容易漏的那条铁律。** 提示是每轮通道，不是技能摘要——把 SKILL.md 抄进来就没人看了。
2. **长度上限约 200 字**。这一行每轮都进上下文，累积成本按轮数线性增长。
3. **必须带来源指针**（`→ 技能 §节`）。技能改了要回来对账，指针是唯一能让你发现漂移的东西。
4. 阶段名与 `agile.py` 的 `detect_stage()` 一一对应，增删阶段要同步改代码与 `tests/`。

阶段判定顺序（先到先得）：

| 阶段 | 判据 | 对应技能 |
|---|---|---|
| `conflict` | `agile-docs/STRATEGY_CONFLICT.md` 存在 | using-agile §5 |
| `backfill` | `sprints/*.done.yaml` 存在 | using-agile §3 → agile-sprint §3 环节 B/C → agile-backlog §3 阶段 4 |
| `sprint` | `backlog.json` 有条目、无进行中 Sprint | agile-sprint §2 |
| `active` | 有状态非「已关闭」的 Sprint | agile-sprint §5 |
| `init` | 无 `VISION.md` | agile-strategic §2 |
| `architecture` | 有 VISION，缺 ARCHITECTURE 或 ADR | agile-strategic §3 |
| `backlog` | 战略齐、`backlog.json` 不存在或没有条目 | agile-backlog §2b/§3 |

**看最靠后的里程碑，不按层顺序。** 套件允许显式跳层（`agile-backlog §0`），所以「已有条目」优先于「VISION 在不在」——否则跳层项目会被判回「战略层未起步」。

[agile-brief:conflict]
有冲突待裁决：读 `STRATEGY_CONFLICT.md` 按表逐项请用户拍板，裁决前不写任何产物（骨架与冲突记录除外），吸收后删除该文件。不要在下一次写文件中"顺手"绕开它。→ using-agile §5
[/agile-brief:conflict]

[agile-brief:backfill]
有未闭环回填：过 DoD 关闭 Sprint → 同步 backlog 状态与 feedback → 文件改后缀 `.done.processed.yaml` 留痕。机械步骤直接做，只在 issue / decision 处停下请用户裁决。→ using-agile §3
[/agile-brief:backfill]

[agile-brief:init]
战略层未起步：先走 agile-strategic 阶段 A（先问项目画像三项，再按决策点一次一问），只写 VISION.md，写完即停。决策点未确认不落盘。→ agile-strategic §2
[/agile-brief:init]

[agile-brief:architecture]
VISION 已就绪、架构层缺件：走 agile-strategic 阶段 B。每项选型必须给 2-3 候选 + 权衡 + 推荐，**用户裁决后才写 ADR**；ADR 只 4 行，实现细节不进 ADR。→ agile-strategic §3
[/agile-brief:architecture]

[agile-brief:backlog]
待办池未建或为空：走 agile-backlog。先用 VISION/ADR 自检，再按三决策点（MVP 范围 / 估点 / 验收）一次一问；**三点没确认完不写 backlog.json**。md 由脚本渲染，不手写。→ agile-backlog §2b
[/agile-brief:backlog]

[agile-brief:sprint]
Backlog 已就绪、无进行中 Sprint：走 agile-sprint。取条前先反问 Sprint 目标能否一句话说清；容量三项（人数 / 工作日 / 专注系数）必问，**禁止静默按 0.6**；`confirmed=false` 条目不许纳入。→ agile-sprint §2
[/agile-brief:sprint]

[agile-brief:active]
Sprint 进行中：执行归消费 Agent，本套件不追 checkbox。新需求先比对 backlog 已有条目（已覆盖就补记来源，别另立重复条目），**不改进当前 Sprint**；要关 Sprint 先逐条过 DoD。→ agile-sprint §3 环节 B
[/agile-brief:active]
