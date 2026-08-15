# 敏捷四技能第五轮评审报告

已逐行通读全部 17 个文件。按约定，排除项（触发词措辞 / 问询口径复述 / .done 越界 ID / schema 空数组语义）未计入。

## P1（会导致 agent 执行错误）

### P1-1 L3 变更的问询口径在三处文件间直接矛盾：增量 vs 完整

- `using-agile/SKILL.md:98`：`5. **L2/L3 走增量问询**（references/change-matrix.md §三）：只重问受影响维度，已确认维度复用现有文档，不做整层重访。`
- `using-agile/references/change-matrix.md:27`：`## 三、增量问询（L2/L3 适用）`
- 但同一矩阵 `change-matrix.md:23`（L3 行）：`走完整问询 + 变更传播评估；跨层按依赖顺序逐层路由`
- `agile-strategic/SKILL.md:50`：`L3 才走完整问询`；`agile-strategic/SKILL.md:145`：`| L3 跨层/战略级… | 走完整问询（§2.0/§3.1）+ 下游影响评估… |`
- `agile-backlog/SKILL.md:68`：`L3 才走完整问询`——且同句末尾又写 `；禁止整层重访`，「L3 完整问询」与「禁止整层重访」在同一行内自相矛盾。

**为什么是问题**：变更分级的核心产出就是「决定重访粒度」（change-matrix §二明确写了这句定位）。现在 L2/L3 的分界口径分裂为两个互斥答案——照 `using-agile/SKILL.md:98` 执行，agent 对改定位/改架构选型的 L3 战略变更只做增量问询，跳过 §二、agile-strategic、agile-backlog 三处一致要求的完整问询；反向照 §二执行则违反入口 SKILL.md 的步骤 5。战略级变更被降级处理是实质执行错误。

**建议修法**：统一为「L2 增量、L3 完整」。① `change-matrix.md:27` 标题改为 `## 三、增量问询（L2 适用）`；② `using-agile/SKILL.md:98` 改为 `**L2 走增量问询**`，L3 另加一步指向 §二完整问询；③ `agile-backlog/SKILL.md:68` 的「禁止整层重访」限定为「L1/L2 禁止整层重访」（与 `agile-strategic/SKILL.md:154` 的写法对齐）。

## P2（明显不一致但不太会致错）

### P2-1 「定位声明终稿 → 变更走 ADR 替代」指向一个不存在于 VISION 的机制

- `agile-strategic/SKILL.md:62`：`| 3 | 定位声明 | 选项：A 终稿（不可逆，变更走 ADR 替代）/ B 探索中 | …`

**为什么是问题**：替代（supersede）机制只定义在 ADR.md 上（`agile-strategic/references/c4-adr.md:61-67` 替代机制；门禁 ②）。VISION.md 没有任何替代流程——按 `change-matrix.md §二/§五`，改定位是 L3 就地更新 VISION。用户选了「终稿」后要改定位时，agent 照此指令会去 ADR.md 新建「替代」章节，或无所适从（定位声明不在 ADR 里，无章可替）。`change-matrix.md:23` 的 `改定位/使命/战略红线/架构选型（触发 ADR 替代）` 括注同样把「触发 ADR 替代」笼统挂在四个改动源上，只有架构选型适用。

**建议修法**：`agile-strategic/SKILL.md:62` 选项 A 改为 `A 终稿（变更视为 L3，走完整问询 + 变更传播评估）`；`change-matrix.md:23` 把「（触发 ADR 替代）」移到仅修饰「架构选型」。

### P2-2 DOD.md「Sprint 完成标准」与 moved_next 关闭机制字面冲突

- `using-agile/references/init-template.md:47-49`：
  ```
  ## Sprint 完成标准（关闭 Sprint 前须全部满足）
  - [ ] 所有承诺任务满足上述「任务完成标准」
  - [ ] 无遗留未解决项
  ```
- 但 `agile-sprint/references/sprint-rules.md:20`：`任一条未达标 → 该条目归入 moved_next（退回 Backlog 或延续下 Sprint），不计入完成。`；`agile-sprint/SKILL.md` 环节 B/C 允许带 moved_next 条目关闭 Sprint；`gate-protocol.md:28`（门禁 ③）的合规路径也是「未完成项退回或延续 → **再关闭**」。

**为什么是问题**：DOD.md 是「独立出口门禁」，环节 B 要求「逐条过 DOD.md 的 Sprint 完成标准」。一个带 moved_next 条目的 Sprint 按模板字面必然不满足「所有承诺任务满足任务完成标准 / 无遗留未解决项」——`.done.yaml` 整套 moved_next 机制设计上支持的部分完成场景，被 DOD 模板的第一条标准否决。虽有门禁 ③ 可 reconcile，但两份都是 agent 机械执行的文本，口径应一致。

**建议修法**：DOD 模板 Sprint 完成标准第一条改为 `所有承诺任务已处置：通过 DoD，或明确退回 Backlog / 延续下 Sprint（moved_next）`，「无遗留未解决项」改为「无未处置条目」。

## P3（措辞/风格）

### P3-1 Sprint 关闭环节的两个动作顺序在三处两种排法

- `agile-sprint/SKILL.md:67-68`：①状态改「已关闭」→②追加执行结果来源
- `agile-sprint/references/sprint-rules.md:25-26`：①标注执行结果来源→②状态改「已关闭」
- `sprint-template.md:60-61` 闭环检查清单与 SKILL.md 同序。

功能无差，但同为「关闭流程」的机械步骤，顺序应统一。建议以 sprint-rules §三为准（先标来源再改状态，避免中途状态已闭但来源缺失的瞬间态），同步改 SKILL.md 环节 C 与模板清单顺序。

### P3-2 using-agile 反向引用 agile-backlog 的 reference，但未声明依赖

- `using-agile/SKILL.md:55`：`（唯一权威口径见 agile-backlog/references/backlog-rules.md §七）`

依赖链方向是业务技能 → using-agile（三个业务技能 frontmatter 均声明），入口反向引用下游技能的文件而无 `dependencies:`。单独加载 using-agile 的会话读不到该文件。因一致性检查口径已内联在句中，不致错；建议要么把三行判据直接写死在 status-routing.md，要么接受现状并在 AGENTS.md 分层说明中注明此例外。

### P3-3 「current Sprint」与「活跃 Sprint」术语分裂

- `using-agile/references/gate-protocol.md:52`：`本模型仅一个 current Sprint`
- 其余全部用「活跃 Sprint」（`status-routing.md:21/41`、`agile-backlog/SKILL.md` 等）。且 `agile-sprint/SKILL.md:76` 明令不用 `current.md`，英文 "current Sprint" 易与该禁令语境混淆。建议统一为「活跃 Sprint」。

### P3-4 「决策确认清单」与「决策点确认清单」同一产物两个名字

- `using-agile/references/interview-protocol.md:9`、`agile-strategic/SKILL.md:48`：「决策确认清单」
- `using-agile/references/probing-protocol.md:31` 及四个 SKILL.md 的结构化审阅段：「决策点确认清单」

同一审阅产物两种写法。建议统一为出现频率高的「决策点确认清单」。

### P3-5 示例残留特定源项目的业务域痕迹（无真实项目专名）

- `agile-backlog/references/backlog-rules.md:39`：`"F-002 审核身份升级" → 展开"5 种身份申请单 / ABN 校验 / 通过则附加身份到账号"`（ABN = 澳洲商业号码，明显来自澳洲身份审核源项目）
- `backlog-rules.md:43`：`"T-010 Stripe 集成" → 展开"3DS / Webhook / 仅 SaaS 订阅场景"`
- `agile-strategic/references/vision-template.md:36-39`：红线示例「不自营/不控货/不履约」「佣金」等带明显电商交易平台域色彩。

未发现真实项目名称，类别 7 严格意义上为「无」；但 ABN 一条属可直接指认的源项目残留，建议换成通用示例（如「营业执照校验」）。

## 核对清单与置信度

**核对过的文件对 / 交叉口径**（全部 17 文件逐行读毕）：
- using-agile/SKILL.md ↔ 其 7 个 references（§引用 22 处逐一验证指向与内容相符，无失效 §引用）
- using-agile ↔ agile-backlog：双文件一致性口径（SKILL.md:55 ↔ backlog §2a ↔ backlog-rules §七）一致；.done 同步流程（schema lifecycle ↔ sprint-template §四 ↔ backlog 阶段 5 ↔ status-routing）一致
- using-agile ↔ agile-sprint：容量参数/专注系数（SKILL §2 ↔ sprint-rules §一）一致；`*.done.yaml` glob 不误匹配 `.done.processed.yaml` 已验证
- agile-backlog：排序表字段 ↔ backlog-rules §二 ↔ YAML schema 枚举（Must/Should/Could/Won't、待办/已完成）一致；「移至下个Sprint」仅出现在 Sprint 文件条目状态建议，与 backlog-rules §五 的限定一致
- agile-strategic：ADR 4 行结构/替代机制（SKILL §6 ↔ c4-adr §二）一致；必答话题清单对接门禁预检第 4 条一致
- 状态机：Sprint「规划完成/已关闭」与「状态非已关闭 = 活跃」的检测口径一致
- 项目专名：全 17 文件 grep 无真实项目名

**置信度：高**（P1-1、P2-1、P2-2、P3-1 均有逐字引文与多文件交叉证据；P3 各项为低风险风格项）。最大不确定点：P1-1 若「L3 也做增量问询、完整问询仅指受影响层」是四轮修复后的有意设计，则降级为 P2——但现有文本（§三标题 vs §二动作列 + 两处业务技能「L3 才走完整问询」）无法读出该设计，且 backlog:68 同句自相矛盾，故仍按矛盾报。