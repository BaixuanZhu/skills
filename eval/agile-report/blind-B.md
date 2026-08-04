# 盲评报告 B（独立打分，从严）

> 独立盲评，从严。功能性缺陷（数值错、命令错、漏陷阱）零容忍。每个依据指向技能具体位置（行号/标题/代码块）。
>
> 对照基线：fixture 数据已自行核验——S001(5任务/5完成/0移出)、S002(5/4/1)、S003(4/3/1)；阶段 14/12/2=85.7%；点数回读 59 承诺/43 完成；T-003 在 S002+S003 两份 .done.yaml 的 moved_next 中各 1 次 = 2 次。与 ground-truth.md 一致。

## 评分总览

| Prompt | 场景 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | 小计 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | 完整态核心路径 | 11 | 11 | 10 | 7 | 8 | 9 | 11 | 11 | 4 | **82** |
| T2 | 工具链陷阱对抗 | 10 | 12 | 11 | 7 | 8 | 10 | 11 | 11 | 4 | **84** |
| T3 | 降级态对抗 | 11 | 11 | 12 | 11 | 10 | 9 | 11 | 12 | 4 | **91** |
| T4 | 阻塞项识别 | 9 | 11 | 11 | 10 | 11 | 10 | 11 | 11 | 4 | **88** |
| T5 | 按需衍生定位 | 12 | 12 | 12 | 11 | 11 | 10 | 11 | 12 | 4 | **95** |
| T6 | 术语映射视觉编码 | 11 | 12 | 12 | 12 | 12 | 11 | 11 | 11 | 4 | **96** |
| T7 | 一致性校验边界 | 9 | 11 | 12 | 11 | 12 | 11 | 10 | 11 | 4 | **91** |
| **合计** | | | | | | | | | | | **627/700** |

---

## 各 Prompt 详评

### Prompt T1（完整态·核心路径：3 个已关闭 Sprint 生成图表化阶段报告 + PDF）
- D1: 11  D2: 11  D3: 10  D4: 7  D5: 8  D6: 9  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **82/100**
- 关键依据：
  1. 完成率/点数/三态公式齐备——`references/report-rules.md §二`（行 26-78）：§2.1 行 30-32 阶段整体完成率 = Σcompleted/Σ任务总数；§2.3 行 48-54 承诺/完成点按 id 从 PRODUCT-BACKLOG.md 回读（明确"YAML 不含 point"）；§2.4 行 56-66 三态判定表。按此公式对 fixture 计算：12/14=85.7%、59/43、12 完成/2 移出/0 未执行，全部正确。
  2. HTML 主路径可照做——`SKILL.md §3 环节 A/B/C`（行 61-86）+ `report-template.md` 七 section 骨架 + `chart-config.md §四` ECharts 配置骨架（行 56-154）。PDF 主命令在 `toolchain.md §1.1`（行 9-11）。
  3. PDF 主命令参数经实跑确证准确（`toolchain-realrun.md §1.2`），但 `toolchain.md §2.1` 环境检测步骤与安装命令有实跑确证的缺陷（见扣分主因）。
- 扣分主因：工具链可执行性硬伤。① `toolchain.md §2.1` 步骤 1（行 29-36）写"`npx playwright --version`→报错才装"，实跑发现 npx 会静默自动安装 playwright 包，`--version` 不报错，**检测分支永远走不到"装"**，agent 照做会卡在"以为已装但浏览器未装"。② §2.1 步骤 2（行 38-41）`npm install -D playwright` 把包装进项目 node_modules，本技能受众是 Java 开发者（DOD.md 项目画像是 Java/Vue），`-D` 会在 Java 项目凭空多出 node_modules/package.json 污染项目，应改 `-g`。这两点共同压低 D4/D5。
- 产出正确性（对照 ground-truth.md）：
  - 完成率计算: ✓（report-rules §2.1 公式 → agent 算出 85.7%，与正确值一致）
  - 点数回读: ✓（§2.3 按 id 从 .md 回读 → 59 承诺/43 完成，一致）

### Prompt T2（工具链陷阱·对抗：已有 HTML，直接给转 PDF 命令，Windows+Node）
- D1: 10  D2: 12  D3: 11  D4: 7  D5: 8  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **84/100**
- 关键依据：
  1. 主命令一字不差——`toolchain.md §1.1`（行 9-11）：`npx playwright pdf --browser chromium --wait-for-timeout 2000 --paper-format A4 <html> <pdf>`。实跑（toolchain-realrun §1.2）确证**参数语法完全正确**（报的是浏览器未找到的运行时错，非命令解析错）。
  2. 5 大陷阱全部点到——`toolchain.md §四 核心陷阱汇总`（行 96-105）：#1 PDF 只 Chromium（行 100）、#2 `--wait-for-timeout` 是毫秒非秒（行 101）、#3 JS 必须 headless 浏览器（行 102）、#4 装包≠装浏览器（行 103）、#5 `playwright`≠`@playwright/cli`（行 104）。另 §1.2 包名辨析表（行 16-23）对 #5 有专表展开。这是技能最强项。
  3. 毫秒坑在 §四行 101 + §一行 45 两处强调；两步装在 §2.1 行 38-45 + §四行 103 两处强调。
- 扣分主因：5 大陷阱虽全到，但实跑暴露了 2 个技能未防御的隐蔽坑，按"陷阱遗漏重扣"压 D5，并连带 D4。① `§2.1` 检测步骤失效（npx 自动安装，实跑 toolchain-realrun §1.1 确证）——agent 照此检测会误判"已装"。② `-D` 应改 `-g`（toolchain-realrun §二发现 2）——本技能是 Java 项目的系统级 HTML→PDF 工具，`-D` 污染项目 node_modules。这 2 个都是"不 fail loud 的错"，属 D5 防错范畴；同时使给出的安装/检测命令不可直接照做，属 D4。主 pdf 命令本身满分（参数实跑确证），故 D4 未跌入 ≤4 的重扣区。
- 产出正确性：N/A（T2 不核数值；命令经实跑语法正确）

### Prompt T3（降级态·对抗：老项目无敏捷文档，有 git 历史，出报告）
- D1: 11  D2: 11  D3: 12  D4: 11  D5: 10  D6: 9  D7: 11  D8: 12  D9: 4
- 该 prompt 小计: **91/100**
- 关键依据：
  1. 明确不拒绝——`SKILL.md §0`（行 20-30）三态表 + 行 30"绝不因数据不全就拒绝产出——降级并明确标注来源即可"；本场景命中状态 ③（无 agile-docs/ 无 sprints/）。
  2. git log 解析规则完整——`report-rules.md §3.2`（行 90-112）：bash 命令 `git log --since --until --pretty=format:"%h|%ad|%s" --date=short`（行 94-96）+ commit message 分类启发式表（行 98-106：feat/fix/refactor/test/docs/chore/其他）。
  3. 降级报告限制与标注齐——`report-rules.md §3.2`（行 108-112）封面 disclaimer"数据来源：git log（简化版）"、无完成率%改"提交趋势"、无 Backlog 分布改"提交类型分布"饼图；`report-template.md §2.1`（行 49）封面降级标识、§2.2（行 74）/§2.3（行 90）降级态 section 替换规则。
- 扣分主因：D6 轻微冗余——降级规则分散在 SKILL.md §0（简表）、report-rules §三（详述）、template 各 section（替换说明）三处，各有侧重但存在表述重叠（如"数据来源：git log（简化版）"在 3 个文件出现）。D5 扣 2：git log 分类启发式属"关键词二次匹配，匹配不上标其他"（§3.2 行 106），对无前缀 commit 的归类有主观空间，技能未给更强约束。

### Prompt T4（数据聚合·阻塞项：哪些任务反复没完成）
- D1: 9  D2: 11  D3: 11  D4: 10  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **88/100**
- 关键依据：
  1. 阻塞识别规则清晰可执行——`report-template.md §2.6`（行 124-142）："遍历所有纳入 Sprint 的 `.done.yaml`，统计每个 id 出现在 `moved_next` 的次数，出现 ≥2 次 → 列入此表"。对 fixture：T-003 在 sprint-002.done.yaml 的 moved_next（1 次）+ sprint-003.done.yaml 的 moved_next（1 次）= 2 次 ≥2 → 唯一阻塞项。规则正确，能识别。
  2. 强制表格非图表——`chart-config.md §一`（行 13）"移出/阻塞任务→表格（非图表）"+ §一行 15 选型理由"详细信息图表反而不清"；`report-template.md §2.6`（行 128-135）用 `<table>` 四列（编号/标题/移出次数/原因）。防 agent 误用饼图/柱状图。
  3. 三态分类支撑——`report-rules.md §2.4`（行 56-66）三态判定表（已完成/移出/未执行）。
- 扣分主因：阻塞项"原因"列提取路径模糊。`report-template.md §2.6`（行 132）写"原因：{从 moved_next 历史推断}"——但 moved_next 只给次数不给文本原因；真正的原因文本在 Sprint 文件的「条目状态建议」节（fixture sprint-002.md 行 25、sprint-003.md 行 24 写明"admin/app 两套分离尚未调通"/"过滤器顺序"）。技能只在 `report-rules.md §2.4`（行 66）针对**降级态 ②（无 .done.yaml）**提了「条目状态建议」节，对**完整态 ①**的阻塞原因提取未明确指向该节，agent 可能拿不到原因文案。D3/D4 各扣 1-2。D1 扣：description 无"阻塞/卡住/反复"触发词，阻塞项是报告内置环节而非独立触发。
- 产出正确性（对照 ground-truth.md）：
  - 完成率计算: ✓（report-rules §2.1 → 85.7%）
  - 阻塞项识别: ✓（report-template §2.6 规则 → T-003，移出 2 次，与正确值一致）

### Prompt T5（范围边界·按需衍生：是否每 Sprint 自动生成/作为流程必须环节）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 12  D9: 4
- 该 prompt 小计: **95/100**
- 关键依据：
  1. 按需衍生定位明确——`SKILL.md §0`（行 22）"本技能是按需衍生技能，不要求项目跑完整敏捷流程"；§1（行 34）"敏捷套件的按需衍生层，非流程闭环环节"。
  2. 不参与 using-agile 路由——`SKILL.md §1`（行 34）"using-agile 的三层模型（战略/执行/变更协调）不包含本技能——它靠自己的触发词激活"。
  3. 只在对外汇报时触发 + 不主动建议——`SKILL.md §5`（行 104）"按需触发，不主动建议'该汇报了'——汇报时机由用户决定"。直接否定 T5 的"自动生成/加入闭环"错误设想。
- 扣分主因：轻微。D6 扣 2——"按需衍生/非流程闭环/靠触发词激活"在 §0、§1、§5 三处重复表述（同一定位的多次申明）。D4/D5 各扣 1——定位是声明性内容，可执行性/防错维度本身权重有限。

### Prompt T6（视觉编码·术语映射：领导不懂故事点/MoSCoW/ADR，怎么改）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **96/100**
- 关键依据：
  1. 术语映射表完整无缺——`chart-config.md §三`（行 36-53）共 11 行映射，rubric 要求的 5 条全部命中：故事点/point→任务量（行 41）、MoSCoW·Must→核心需求（行 43）/Should→次要需求（行 44）/Could→可选需求（行 45）、ADR→技术决策记录（行 46）、DoD→验收标准（行 47）、Sprint→迭代周期（行 48）。无任何遗漏，D3 满分。
  2. 转换时机明确——`chart-config.md §三`（行 52-53）"转换时机：环节 B 生成 HTML 时，所有从数据源读出的字段值在写入 HTML 前过一遍此表"；`SKILL.md §3 环节 B`（行 77）"写入 HTML 前强制按 chart-config.md §三 映射表转换"。双处锚定。
  3. 配色规则明确——`chart-config.md §2.1`（行 19-26）三色表：红 `<60%` `#e74c3c` / 黄 `60-85%` `#f39c12` / 绿 `>85%` `#27ae60`；`SKILL.md §5`（行 103）同规则。`§5`（行 102）硬约束"不在报告中暴露 故事点/T-NNN/MoSCoW/ADR/DoD 原文"是强防错。
- 扣分主因：极轻微。D1 扣 1——description 无"术语/看不懂/去技术化"直接触发词，去技术化是报告生成内置环节；但"给甲方/给领导看"触发词能间接触发。D6 扣 1——配色规则在 chart-config §2.1 与 SKILL.md §5 两处复述。整体接近满分。

### Prompt T7（一致性校验·边界：手改 yaml 没同步 .md，会怎样）
- D1: 9  D2: 11  D3: 12  D4: 11  D5: 12  D6: 11  D7: 10  D8: 11  D9: 4
- 该 prompt 小计: **91/100**
- 关键依据：
  1. 三项校验规则齐备——`SKILL.md §2a`（行 47）"执行双文件一致性校验（PRODUCT-BACKLOG.md 与 .yaml 的 id 集合 / 条目数 / 同 id 的 priority+status 是否一致）"；`report-rules.md §四`（行 114-122）三项展开：id 集合一致 / 条目数一致 / 同 id 的 priority+status 一致。
  2. 不一致停下报告 + 列具体差异——`report-rules.md §四`（行 122）"停下报告差异（列出 id 缺失/字段不一致的条目）"。
  3. 不静默挑一份——`report-rules.md §四`（行 122）"请用户确认以哪份为准后再继续聚合。禁止在不一致状态下强行挑一份算下去"。这是关键防错（不 fail loud 的错），D5 满分。
- 扣分主因：D7 扣 2——`SKILL.md §2a`（行 47）与 `report-rules.md §四`（行 114-122）都说"复用 agile-backlog/references/backlog-rules.md §七规则"，但盲评 agent 手里**只有 agile-report 技能**，agile-backlog 不在本次评估的只读范围内，该跨技能引用在独立使用场景下悬空。好在 report-rules §四 已把三项规则复述完整，不依赖外部也能跑，故未重扣。D1 扣 3——一致性校验是报告生成内置步骤（§2a），无独立触发词，description 也未提"一致性/校验/同步"。

---

## 最严重 3 个问题

1. **toolchain.md §2.1 环境检测步骤失效（实跑确证）**——行 29-36 写"`npx playwright --version`→报错才进步骤 2 装包"，但 `toolchain-realrun.md §1.1` 实跑发现 npx 会静默自动下载临时安装 playwright 包，`--version` 不报错直接输出版本号，导致**检测分支永远走不到"装包"**，agent 照做会误判"工具链就绪"然后卡在浏览器未找到。直接拉低 T1/T2 的 D4（可执行性）和 D5（防错）。建议改为直接尝试 `npx playwright pdf --browser chromium --help` 按报错决定补装。

2. **toolchain.md §2.1 `npm install -D playwright` 应改 `-g`（实跑/审视发现）**——行 38-41。本技能受众是 Java 开发者（fixture DOD.md 项目画像"Java/Vue"），Playwright 在这里是**系统级 HTML→PDF 工具**而非项目依赖。`-D` 会把 playwright 装进 Java 项目的 node_modules，凭空多出 node_modules/package.json/package-lock.json 污染项目。`toolchain-realrun.md §二 发现 2` 已明确建议改 `npm install -g playwright`（浏览器二进制无论 -D/-g 都装同一全局位置，区别只在包本身）。影响 T1/T2 的 D4/D5。

3. **T4 阻塞项"原因"列提取路径模糊**——`report-template.md §2.6`（行 132）写"原因：{从 moved_next 历史推断}"，但 moved_next 只提供移出次数，不提供文本原因。真正的阻塞原因（如 T-003 的"admin/app 两套分离未调通"/"过滤器顺序"）在 Sprint 文件的「条目状态建议」节。技能只在 `report-rules.md §2.4`（行 66）针对**降级态 ②**指了该节，对**完整态 ①**的阻塞原因提取未明确指向，agent 可能填不出原因列。影响 T4 的 D3/D4。

---

## 备注

- **数值正确性（T1/T4）全部通过**：report-rules §二的公式清晰且机械可执行，对 fixture 计算结果与 ground-truth.md 完全一致（85.7% / 59-43 / T-003×2）。这是技能的数据层强项。
- **术语映射（T6）完整无缺**：chart-config §三 11 行映射表覆盖 rubric 要求的全部 5 条 + 6 条额外，D3 满分。
- **5 大工具链陷阱（T2）全部点名**：toolchain §四 表格完整。技能失分主要来自实跑/审视新发现的 2 个未防御坑（检测失效 + -D 污染），而非已有陷阱遗漏。
- **跨技能引用隐患**：SKILL.md §2a 与 report-rules §四 引用 agile-backlog 的 backlog-rules §七，但本次盲评只读 agile-report 技能；好在关键规则已在 report-rules §四 内复述，未致硬伤。
