# 盲评报告 A（独立打分）

> 评估对象：`skills/agile-report/`（SKILL.md + 4 references）
> 评分依据：`eval/agile-report/rubric.md`（9 维度，单 prompt 满分 100，7 prompt 总分 700）
> 评分人：盲评 agent A（独立打分，未参考其他评审）
> 评分日期：2026-08-04
> 评分前先核对：fixture 3 个已关闭 Sprint + ground-truth.md 数值（85.7% / 59 承诺 / 43 完成 / T-003 移出 2 次）均按技能规则可机械复现，下面打分即以"agent 按技能指引能否算出这些值"为准。

---

### Prompt T1（完整态·生成阶段报告·核心路径）
- D1: 12  D2: 12  D3: 10  D4: 8  D5: 9  D6: 11  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 90/100
- 关键依据：
  1. 完整路径三环节齐全：SKILL.md §3 环节 A/B/C（行 61-86）+ §0 三态表（行 24-28）明确状态①判据；report-rules.md §2.1-2.5 给出完成率/三态/点数回读全部公式，85.7% 可机械算出。
  2. HTML 骨架 report-template.md §一/§二 + 图表配置 chart-config.md §四 一一对应（容器 id 表 §一 chart-config 行 7-13）；Playwright pdf 命令在 toolchain.md §1.1（行 9-11）+ SKILL.md §3 C（行 84-85）两次给出且一致。
  3. 术语去技术化强制：SKILL.md §5 硬约束（行 102）+ chart-config.md §三 映射表，写入 HTML 前转换。
- 扣分主因：
  - D3-1：report-rules.md §2.1（行 36）分母写"各 Sprint 任务清单行数之和（`- T-NNN`/`- F-NNN` 行）"——**未限定必须在 `## 任务清单` 节内**。而 fixture 每个 sprint-*.md 的「条目状态建议」节同样有 `- T-001：已完成` 开头的行（见 sprint-001.md 行 25-29），朴素正则会把 5+5+4 误算成 10+10+8，完成率从 85.7% 算成 ~43%。这是数值硬伤隐患。技能 §一字段速查（行 13）虽定义了任务清单行格式 `- T-001 {标题} ({点}) → ADR-{NNN}` 可与状态建议行区分，但 §2.1 的措辞未强调节范围，扣。
  - D4-1：toolchain.md §2.1 检测步骤失效（见 toolchain-realrun.md 发现 1）——`npx playwright --version` 因 npx 自动安装永不报错，agent 跟着走会得到错误的"已装"信号，直到真正跑 pdf 才报 `Executable doesn't exist`。
  - D4-2：chart-config.md §4.1/4.2/4.3/4.4 多处 ECharts 配置骨架用 `data: {['迭代周期 001',...]}`、`data: {[各 Sprint 完成率]}` 这种 `{[...]}` **非法 JS 语法**（行 79/100/106/125/128/144-149），照抄会语法错误，图表渲染失败。
- 产出正确性（对照 ground-truth.md）：
  - 完成率计算: ✓（按 §2.1 公式 + 正确节范围 → 12/14 = 85.7%，黄）。风险见扣分主因 D3-1。
  - 点数回读: ✓（§2.3 + §一关键陷阱"YAML 不含 point"，从 PRODUCT-BACKLOG.md 按 id 回读 → 59 承诺 / 43 完成）。注意 T-003 在 002/003 两 Sprint 均入承诺但未完成，点数 8 被计两次承诺、零次完成，符合 §2.3"Σ本 Sprint 任务清单条目 point"按 Sprint 聚合的语义。
  - 阻塞项识别: —（T1 不聚焦此）

---

### Prompt T2（工具链陷阱·HTML→PDF 命令·对抗）
- D1: 12  D2: 12  D3: 11  D4: 7  D5: 10  D6: 11  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 91/100
- 关键依据：
  1. 5 大陷阱全部点到：toolchain.md §四 核心陷阱汇总表（行 98-105）6 行覆盖——#1 Chromium-only（行 100）、#2 `--wait-for-timeout` 毫秒（行 101）、#3 ECharts 必须 headless（行 102）、#4 装包≠装浏览器两步（行 103）、#5 `playwright`≠`@playwright/cli`（行 104）、#6 ECharts 异步（行 105）。rubric 要求的 5 条一条不漏。
  2. 主命令一字不差：toolchain.md §1.1（行 9-11）`npx playwright pdf --browser chromium --wait-for-timeout 2000 --paper-format A4 ...`——toolchain-realrun.md §1.2 实跑确认参数完全准确（报的是运行时"浏览器未找到"而非参数解析错）。
  3. 包名辨析表 toolchain.md §1.2（行 16-23）把 `playwright` / `@playwright/cli` / `playwright-core` 三者差异讲清，并给出 npmjs 链接。
- 扣分主因：
  - D4-1（重）：toolchain.md §2.1 步骤 1 检测逻辑失效。toolchain-realrun.md 发现 1 实跑证实 `npx playwright --version` 会触发 npx 自动临时安装，**永不报错**，技能假设的"报错→进入步骤 2"分支永远走不到。agent 跟随技能会得到虚假的"已就绪"信号。
  - D4-2（重）：§2.1 步骤 2（行 39）`npm install -D playwright` 用 `-D`（devDependencies），会把 playwright 装进**当前项目** node_modules。但本技能受众是 Java 项目（fixture 即 yudao Spring Boot 工程），`-D` 会凭空在 Java 项目里多出 `node_modules/` + `package.json` + `package-lock.json`，污染项目。realrun 发现 2 明确建议改 `-g`。这是与技能实际使用场景错配的可执行性缺陷。
  - D5-1：§四陷阱表恰好**没有**"npx 自动安装会掩盖未装状态"这一条——而这恰是检测步骤失效的根因，属防错盲点。
- 产出正确性：不适用（T2 非数值题）

---

### Prompt T3（降级态·无敏捷产物·git log·对抗）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 11  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 97/100
- 关键依据：
  1. 降级判据机械可执行：report-rules.md §3.1（行 84-88）三态扫描表 + SKILL.md §0（行 24-28）——"无 agile-docs/ 或无 sprints/ → ③全降级"，且 SKILL.md §5（行 101）"绝不因数据不全就拒绝产出"，明确不拒绝。
  2. git log 解析规则完整：report-rules.md §3.2（行 91-112）给出 `git log --since/--until/--pretty=format` 命令 + commit message 分类启发式表（feat/fix/refactor/test+docs+chore/无前缀，行 100-106），分类归到报告术语。
  3. 降级报告限制显式声明：§3.2（行 108-112）封面"数据来源：git log（简化版）"、无完成率%改"提交趋势"、无 Backlog 分布改"提交类型分布"饼图、顶部 disclaimer——rubric T3 四个验证点全覆盖。
- 扣分主因：
  - D4-1：§3.2 git log 命令的 `{起始日期}`/`{结束日期}` 占位符未与 SKILL.md §2b 范围探询（"日期范围"）显式串起来，agent 需自行把用户给的日期填入。
  - D5-1：commit 分类"无前缀→按关键词二次匹配，匹配不上标其他"（行 106）偏启发式，对中文 commit message 的二次匹配规则未给关键词词表，agent 可能归不准。但技能明确"不脑补"，可接受。
- 产出正确性：不适用

---

### Prompt T4（数据聚合·阻塞项识别·T-003）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 10  D6: 11  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 97/100
- 关键依据：
  1. 阻塞判据精确：report-template.md §2.6（行 138-142）"遍历所有纳入 Sprint 的 `.done.yaml`，统计每个 id 出现在 `moved_next` 的次数；出现 ≥2 次 → 列入此表"。fixture 中 T-003 在 sprint-002.done.yaml（行 6-7）+ sprint-003.done.yaml（行 4-5）各出现一次 = 2 次，命中阈值。ground-truth 吻合。
  2. 表格而非图表：report-template.md §2.6（行 141）"用表格不用图表——详细信息图表反而不清（chart-config.md §一 判定）"，chart-config.md §一（行 13）选型映射表明确"移出/阻塞任务 → 表格（非图表）"。rubric T4 验证点"用表格非图表"满足。
  3. 表格骨架 report-template.md §2.6（行 127-135）已给出列：任务编号/标题/移出次数/原因。
- 扣分主因：
  - D5-1：§2.6 原因列写"{从 moved_next 历史推断}"，但真正可读的原因文本（"admin/app 两套分离尚未调通" / "过滤器顺序问题"）实际在 sprint-*.md 的「条目状态建议」节（sprint-002.md 行 25、sprint-003.md 行 24）。技能 §2.4（行 66）只在"无 .done.yaml 时"才指向「条目状态建议」节，未明确说**有 .done.yaml 时**取阻塞原因也要回读该节。agent 可能只给"移出 2 次"而漏具体原因文本。
- 产出正确性（对照 ground-truth.md）：
  - 阻塞项识别: ✓（T-003，2 次，标题"双 SecurityFilterChain"）。原因文本需 agent 自行回读 sprint .md 条目状态建议节，技能指引偏弱但可达。

---

### Prompt T5（范围边界·按需衍生定位）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 11  D6: 12  D7: 11  D8: 12  D9: 4
- 该 prompt 小计: 98/100
- 关键依据：
  1. 定位声明三处强化：SKILL.md §1（行 32-34）"按需衍生层，非流程闭环环节"+"using-agile 的三层模型（战略/执行/变更协调）不包含本技能——它靠自己的触发词激活"；SKILL.md description（行 6）"按需衍生，不属于敏捷流程必须环节"；SKILL.md §5（行 104）"按需触发，不主动建议'该汇报了'——汇报时机由用户决定"。
  2. 不参与路由：§1 明确"非流程闭环环节"，与 using-agile 解耦。rubric T5 三个验证点（按需衍生/不参与路由/只在对外汇报触发）全部命中。
  3. 错误回答明确被禁止：§5 行 104 直接否定"主动建议该汇报了"，不会出现"每个 Sprint 自动生成/加入流程闭环"的错误建议。
- 扣分主因：
  - D7-1：定位信息分散在 SKILL.md §0/§1/§5 三处，无单一"边界声明"小节集中索引，agent 拼凑完整边界需跳 3 处（但都在 SKILL.md 内，跳转成本不高）。
- 产出正确性：不适用

---

### Prompt T6（视觉编码·术语去技术化映射）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 11  D7: 12  D8: 11  D9: 4
- 该 prompt 小计: 97/100
- 关键依据：
  1. 映射表完整：chart-config.md §三（行 39-51）11 行覆盖全部要求项——故事点→任务量、T-NNN/F-NNN→任务编号、MoSCoW·Must→核心需求、Should→次要需求、Could→可选需求、ADR→技术决策记录、DoD→验收标准、Sprint→迭代周期、Backlog→待办清单、completed→已完成、moved_next→移至下期。rubric 要求的 5 条一条不漏。
  2. 转换时机明确：§三（行 53）"转换时机：环节 B 生成 HTML 时，所有从数据源读出的字段值在写入 HTML 前过一遍此表"，并给例 `Sprint 001 完成率 85% → 迭代周期 001 完成率 85%`。
  3. 配色规则明确：chart-config.md §2.1（行 21-25）三色表 红`<60%`/黄`60-85%`/绿`>85%`，并贯穿所有图表（§2.1 行 27"柱状图、环形进度条的颜色按各数据点的完成率落区间动态取色"）；SKILL.md §5（行 103）二次强调。
- 扣分主因：
  - D4-1：chart-config.md §4.x ECharts 骨架普遍用 `data: {['迭代周期 001',...]}`、`data: {[各 Sprint 完成率]}`、`data: {[承诺点数组]}` 这种 `{[...]}` **非法 JS 语法**（§4.1 行 79、§4.2 行 100+106、§4.3 行 125+128-129、§4.4 行 144-149）。映射表本身正确，但包围它的配置骨架若被照抄会导致整段 JS 语法错误、图表不渲染。属可执行性瑕疵。
  - D8-1：§三未声明"哪些术语可保留不映射"（如项目名、人名），边界略宽，但不影响本 prompt。
- 产出正确性：不适用

---

### Prompt T7（一致性校验·YAML/.md 不一致·边界）
- D1: 12  D2: 12  D3: 11  D4: 10  D5: 12  D6: 11  D7: 11  D8: 12  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. 校验规则三项明确：report-rules.md §四（行 116-120）id 集合一致 / 条目数一致 / 同 id 的 priority+status 一致；SKILL.md §2a（行 47）"读 YAML 前必跑"。
  2. 不一致处理防错到位：§四（行 122）"任一不符 → 停下报告差异（列出 id 缺失/字段不一致的条目），请用户确认以哪份为准后再继续聚合。**禁止**在不一致状态下强行挑一份算下去"。rubric T7"不静默挑一份"硬要求满足。
  3. 字段差异提示：report-rules.md §一关键陷阱（行 21-24）priority 英文 / status 中文 / YAML 无 point——为一致性比对提供字段口径。
- 扣分主因：
  - D4-1：§四三项校验依赖"复用 agile-backlog/references/backlog-rules.md §七"（行 116），但该文件不在本技能包内（属上游依赖）。好在 §四行内已重述三项规则，agent 无外部文件也能跑，但"条目数一致"与"id 集合一致"的判别细节（如重复 id 算几个）未展开。
  - D7-1：跨技能引用 `agile-backlog/references/backlog-rules.md §七`，对本技能"独立持有"的 agent 是不可直达的导航断点（除非依赖技能也被加载）。
- 产出正确性：不适用

---

## 总结表

| Prompt | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | 小计 |
|--------|----|----|----|----|----|----|----|----|----|------|
| T1 完整态核心路径 | 12 | 12 | 10 | 8  | 9  | 11 | 12 | 12 | 4 | **90** |
| T2 工具链陷阱     | 12 | 12 | 11 | 7  | 10 | 11 | 12 | 12 | 4 | **91** |
| T3 降级态         | 12 | 12 | 12 | 11 | 11 | 11 | 12 | 12 | 4 | **97** |
| T4 阻塞项识别     | 12 | 12 | 12 | 12 | 10 | 11 | 12 | 12 | 4 | **97** |
| T5 范围边界       | 12 | 12 | 12 | 12 | 11 | 12 | 11 | 12 | 4 | **98** |
| T6 术语映射       | 12 | 12 | 12 | 11 | 12 | 11 | 12 | 11 | 4 | **97** |
| T7 一致性校验     | 12 | 12 | 11 | 10 | 12 | 11 | 11 | 12 | 4 | **95** |
| **总分**          |    |    |    |    |    |    |    |    |    | **665 / 700 (95.0%)** |

单维度横向看：D1/D2/D8/D9 几乎满分（触发词、可发现性、范围边界、内部一致性是本技能强项）；失分集中在 **D4（可执行性）和 D5（防错）**——根因都在 toolchain.md 与 chart-config.md 的几处具体缺陷（见下）。

---

## 最严重的 3 个问题（按严重度排序）

### 问题 1（最严重）：toolchain.md §2.1 环境检测步骤失效——npx 自动安装使 `--version` 永不报错
- **位置**：`references/toolchain.md` 行 30-47（§2.1 检测顺序）+ SKILL.md 行 84（§3 环节 C 步骤 1）
- **实跑证据**：`eval/agile-report/toolchain-realrun.md` §1.1 发现 1——`npx playwright --version` 实际会触发 npx 自动临时安装 playwright@1.62.1 并输出版本号，**不报错**。
- **后果**：技能假设的"步骤 1 报错 → 进入步骤 2 安装"分支**永远走不到**。agent 跟随技能会得到虚假的"工具链已就绪"信号，直接跳到生成 PDF，然后撞上 `Executable doesn't exist` 运行时错误。同时 §四核心陷阱表（行 98-105）6 条里**没有**"npx 自动安装会掩盖未装状态"这一条——这恰是检测失效的根因，属防错盲点。
- **波及**：T1（核心路径含工具链）、T2（工具链对抗主靶）。两 prompt 的 D4/D5 均因此下调。
- **建议**：把检测改为直接尝试 `npx playwright pdf --browser chromium --help`（realrun 已给方案），或在陷阱表补第 7 条。

### 问题 2：`npm install -D playwright` 用 `-D` 与技能受众（Java 项目）错配
- **位置**：`references/toolchain.md` 行 39（§2.1 步骤 2 第一条）
- **证据**：`toolchain-realrun.md` 发现 2 明确建议改 `-g`。
- **后果**：`-D`（devDependencies）把 playwright 装进**当前项目** node_modules，会在 Java 项目（fixture 即 yudao Spring Boot 工程）里凭空多出 `node_modules/` + `package.json` + `package-lock.json`，污染项目。Playwright 在本技能场景下是**系统级 HTML→PDF 工具**，不是项目依赖。浏览器二进制无论 `-D`/`-g` 都装到同一个全局 `%LOCALAPPDATA%\ms-playwright\`，所以改 `-g` 不影响浏览器可用性。
- **波及**：T2（D4 重扣主因之一）。
- **建议**：`npm install -g playwright`。

### 问题 3：chart-config.md §4.x ECharts 配置骨架普遍使用 `{[...]}` 非法 JS 语法
- **位置**：`references/chart-config.md` §4.1（行 79 `data`）、§4.2（行 100 xAxis.data、行 106 series.data）、§4.3（行 125 xAxis.data、行 128-129 series）、§4.4（行 144-149 pie.data）——共 7+ 处。
- **后果**：`data: {['迭代周期 001','迭代周期 002','迭代周期 003']}` 和 `data: {[各 Sprint 完成率]}` 是**无效 JavaScript**（`{[...]}` 是对象字面量包数组，但又不是合法对象）。agent 若照抄骨架填数据，整段 `setOption` 会语法错误，ECharts 不渲染 → 图表空白（恰好踩中技能自己反复警告的"图表空白"陷阱，只是这次源头是模板本身）。
- **波及**：T1（HTML 生成）、T6（视觉编码配置）。
- **建议**：把 `{[...]}` 改为 `[...]` 或显式占位注释 `/* [各 Sprint 完成率] */`。

---

### 附：值得记的次级问题（未进 Top3，但影响 D3/D4）

- **report-rules.md §2.1 分母措辞未限定节范围**（行 36）：写"各 Sprint 任务清单行数之和（`- T-NNN`/`- F-NNN` 行）"，但 fixture sprint-*.md 的「条目状态建议」节同样有 `- T-001：已完成` 开头的行。朴素正则会把任务数 5+5+4 误算成 10+10+8，完成率从 85.7% 算成 ~43%（D3 数值硬伤隐患）。§一（行 13）虽定义了任务清单行格式可区分，但 §2.1 未强调"仅 `## 任务清单` 节内"，建议补一句节范围限定。
- **T4 阻塞原因取数路径偏弱**：report-template.md §2.6（行 132）原因列写"{从 moved_next 历史推断}"，但真正可读原因文本在 sprint-*.md「条目状态建议」节，§2.4（行 66）只在"无 .done.yaml 时"指向该节，未明确"有 .done.yaml 时取阻塞原因也要回读该节"。
- **T7 跨技能导航断点**：§四校验规则引用 `agile-backlog/references/backlog-rules.md §七`，本技能包内不可直达（好在 §四行内已重述三项规则，agent 仍可执行）。
