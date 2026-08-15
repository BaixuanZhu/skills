# 敏捷套件达尔文评分 · 仲裁报告（v4.4.0）

> **仲裁角色**：独立复核两份盲评（Agent A / Agent B）的证据真实性，并独立 grep 实测核实。
> **日期**：2026-08-15
> **方法**：对每一条关键发现独立 grep 源文件，区分「真问题 / 误报 / 约定差异」。

## 一、证据核实表

| # | 发现 | 来源 | 仲裁判定 | 独立 grep 证据 |
|---|------|------|---------|---------------|
| 1 | DOD 模板含「至少 1 人 approve」「PO 已验收」，与「单人+agent」定位矛盾 | B | ✅ **真问题（最实质）** | `init-template.md:40-43` 含「已完成代码评审（至少 1 人 approve）」「产品负责人（PO）已验收」；`using-agile/SKILL.md:24` 声明「单人+agent，抛弃大团队重量级」 |
| 2 | gate-protocol 异常场景表编号跳号（①②③④⑥⑦，缺⑤） | B | ✅ **真问题** | `gate-protocol.md:50-55` 编号为 ①②③④⑥⑦，无 ⑤ |
| 3 | gate-protocol 引「§五」悬空引用 | A | ⚠️ **证据不足**（grep 全文无「§五」），方向成立但以 #2 的「⑤缺失」为准 | grep `§五` 无命中；§一~§四 均真实存在 |
| 4 | vision-template 标题写死「定位声明（终稿·不可逆）」vs SKILL 决策点 3 默认「探索中」 | A | ✅ **真问题（轻微）** | `vision-template.md:19`「## 定位声明（终稿 · 不可逆）」；`agile-strategic/SKILL.md:62` 决策点 3「选项 A 终稿 / B 探索中…默认『探索中』」 |
| 5 | backlog 定位表只列阶段 0-3，漏阶段 4/5 | B | ✅ **真问题（轻微）** | `agile-backlog/SKILL.md:34-37` 定位表仅阶段 0-3；`:128` 阶段 4（下游影响评估）、`:137` 阶段 5（.done 同步）未入表 |
| 6 | 画像采集字段（项目名称/一句话定位）在 DOD 模板无落盘列 | A | ✅ **真问题（轻微）** | `using-agile/SKILL.md:66-67` 采集「项目名称/一句话定位/项目类型/团队…」；`init-template.md:34-36` DOD 画像表仅「项目类型/团队人数与技能栈/代码基础」三行，缺「项目名称」「一句话定位」 |
| 7 | 四个技能 description 缺「做什么」概括句 | B | ⚠️ **符合本仓库约定，非缺陷** | AGENTS.md 明确「SKILL.md 的 description 是长触发器文本」，4 个 description 均为「触发词+何时用」式，符合约定 |
| 8 | 跨技能引用省略 `using-agile/` 前缀（裸文件名） | A | ✅ **轻微**（frontmatter `dependencies` 可解） | `interview-protocol.md`/`change-matrix.md` 等多处裸引用 |
| 9 | backlog 前置条件只约束 VISION，未显式约束 ADR/ARCHITECTURE | A | ⚠️ **设计选择**（门禁 ① 事后拦截兜底） | `agile-backlog/SKILL.md:22-23` 前置条件 + 门禁 ① T-NNN 无 ADR 拦截 |

## 二、两 agent 一致性判定

| | Agent A | Agent B | 一致性 |
|---|---|---|---|
| using-agile | 75.3 | 82.6 | 方向一致（均最低） |
| agile-strategic | 78.2 | 86.6 | 方向一致（最高档） |
| agile-backlog | 76.0 | 83.6 | 方向一致（次低） |
| agile-sprint | 80.7 | 85.1 | 方向一致（最高档） |

- **排名方向完全一致**：using-agile 最低、backlog 次低、strategic/sprint 最高。
- **绝对分差**（B 比 A 高约 5~8 分）是评分尺度差，不是方向分歧。
- **关键发现交叉命中**：#1（B）、#4（A）、#2（B）、#6（A）、#5（B）各自至少被 1 个 agent 命中，且均经仲裁独立 grep 核实为真。无共同漏报的实质性缺陷。

## 三、最终评分（两 agent 均值）

| 技能 | A | B | 均值 |
|------|---:|---:|-----:|
| agile-sprint | 80.7 | 85.1 | **82.9** |
| agile-strategic | 78.2 | 86.6 | **82.4** |
| agile-backlog | 76.0 | 83.6 | **79.8** |
| using-agile | 75.3 | 82.6 | **79.0** |
| **套件均值** | | | **≈ 81.0** |

## 四、待修项分级

**P1（实质缺陷，建议修）**
1. `init-template.md` DOD 模板的「至少 1 人 approve」「PO 已验收」是传统多角色残留，与单人+agent 定位直接矛盾——单人无法执行，需改为单人可执行的验收表述。

**P2（一致性/引用，建议修）**
2. `gate-protocol.md` 异常场景表编号跳号（缺 ⑤）。
3. `vision-template.md` 定位声明标题硬编码「终稿·不可逆」，与 SKILL 决策点 3「默认探索中、可选终稿」矛盾。
4. `agile-backlog/SKILL.md` 定位表漏阶段 4/5（表实不一致）。
5. `using-agile` 画像采集「项目名称/一句话定位」在 DOD 模板无落盘列。

**P3（可选）**
6. 跨技能裸引用省略 `using-agile/` 前缀。
7. backlog 前置条件未显式列出 ARCHITECTURE/ADR 约束。

**非缺陷（约定差异，不改）**
- description「缺做什么」——符合 AGENTS.md「description=长触发器文本」约定。
