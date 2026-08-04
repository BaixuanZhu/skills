# AGENTS.md

本仓库是一个**技能（Skill）开发 + 分发仓库**：编写、评估、分发面向中文 Java/Spring 生态（Sa-Token、MyBatis-Plus、Java 编码规范、敏捷流程等）的"Agent Skills"（SKILL.md 内容包）。**没有需要构建/运行/部署的应用——产品就是技能内容本身。**

## 仓库结构

- `skills/<name>/` —— 技能目录，**本仓库编辑的核心**。每个技能含：
  - `SKILL.md`：YAML frontmatter（`name`、`description`、`version`，通常还有 `slug` + `displayName`；敏捷族技能另有 `dependencies`）。
  - `references/`：编号文件 `NN-topic.md`，按阅读优先级排序；数量从 1（agile-backlog）到 14（sa-token-dev / mybatis-plus-dev）不等。
  - 个别含 `assets/`（如 java-coding-quality）。
- `eval/<skill-name>/` —— 达尔文评估产物（测试 prompt、产出快照、判分记录），按技能分子目录；评估后提交到此。见 `eval/README.md`。
- `.claude-plugin/` —— Claude Code 插件市场清单（`marketplace.json`、`plugin.json`），每个技能对应一个 plugin 条目。
- `README.md` —— 对外安装指南（双协议：Claude Code 插件 + `npx skills`）。
- `PUBLISH.local.md` —— **已 gitignore**，线上发布版本、平台 ID、发布流程的唯一真相来源。

## 分发 —— 双协议共享同一个 `skills/`

一份 `skills/` 同时喂两种安装协议：

| 协议 | 识别依据 | 用户命令 |
|---|---|---|
| Claude Code 插件 | `.claude-plugin/marketplace.json`（`plugins[]`） | `/plugin marketplace add BaixuanZhu/skills` → `/plugin install <name>` |
| npx skills（Vercel CLI） | `skills/<name>/SKILL.md`（自动扫描） | `npx skills add BaixuanZhu/skills` |

**新增技能必须更新 `marketplace.json`** —— 把 `{name, version, author: {name, email}, source: "./skills/<name>", description, category, keywords}` 追加到 `plugins` 数组：
- `version` 必须与对应 `SKILL.md` frontmatter 一致（见下文「版本号两个源头」）；
- `author` 用隐私邮箱 `66127517+BaixuanZhu@users.noreply.github.com`（noreply，不暴露真实地址）。
- 缺 `version`/`author` → Claude Code 市场只显示插件名，看不到版本号和开发者。技能能通过 `npx skills` 安装但市场列表信息不全。（npx skills 无需改清单。）

## 编辑技能内容的约定

- **技能编写的权威外部参考**：<https://agentskills.io/home> —— 拿不准结构 / frontmatter / 最佳实践时查阅。
- **重发必须 bump `version`，且版本号有**两个源头**必须同步：**
  1. `skills/<name>/SKILL.md` 的 frontmatter `version`（npx skills / SkillHub / 虾评 读这个）；
  2. `.claude-plugin/marketplace.json` 对应 plugin 条目的 `version`（**Claude Code 市场列表展示读这个**——只改 SKILL.md 不改 marketplace.json，市场显示的版本会落后，用户无法判断是否更新）。
  - 线上当前版本在 `PUBLISH.local.md`（gitignored），不在 git——任何版本号调整前先读它。SkillHub 对等于或低于线上的版本号**静默拒收**（不报错、不更新）。
- `description` 字段两种 YAML 风格都存在：`>-`（折叠，适合列很多关键词的长触发描述）与 `|`（字面量，适合较短的）。与该技能现有风格保持一致。
- 编号 references 按阅读优先级排序；文件之间用指针交叉引用，**不要复制内容**。
- 规则风格：`✗ 禁止 → ✓ 推荐`。匹配每个技能双语（中文为主）的语调。（规则表的"why"列——见下文质量标准；通常冗余。）
- 编辑原则：不重复论证已成定局的决策；不留"可选附录"之类的章节——发现就删。

## 技能内容质量标准（创建 / 更新 / 优化任何技能时适用）

以下标准提炼自多轮评审，**每次都要应用**，不必逐技能提醒。

### "必须保留" vs "冗余"的唯一判据

一句话测试：**删掉这段文字，执行中的 agent 会产出不同（更差）的结果吗？**

- **必须保留**：阈值、触发条件、命令、映射表、防漂移的机械判据、隐性陷阱（错误不会显式报错——如 spy/doReturn、verify 次数语义、mockito-inline 依赖坑）、边界 / 范围声明。
- **冗余**（删除或压缩）：见下方"表达 / 冗余模式"的具体清单。

### 表达 / 冗余模式（评审中反复出现，多为冗余）

遇到时套用上面的判据——多数应删或压缩：

1. **原理 / 理论前言** —— 标题为"核心立场"/"为什么不能…"/"X 的核心价值"、在*论证方法为何重要*的章节。agent 需要执行方法，不是被说服它的价值。删论证，留步骤 / 阈值。（如"价值排序图"、"为什么不能想到哪测到哪"、"决策表的核心价值：防组合遗漏"。）
2. **学术 / 历史渊源** —— 论文引用（"Chow 1978"）、把 ISTQB 公理当典故背诵（"杀虫剂悖论"）、缩写词源。agent 不需知道出处也能执行规则。删引用，留规则。
3. **ASCII 可视化复述了相邻表格已说的内容** —— 决策树、价值排序图、区间数轴、抽象 Y/N 矩阵，紧跟在具体示例 / 表格前。agent 复制的是具体产物；图是给人读的。除非图编码了表格没有的决策，否则删。
4. **励志 / 重述型引用块** —— `>` 引用用更强语气重述上下文（"覆盖率是探照灯不是合格证"、"非法迁移比合法还重要"、"设计是主角，工具是配角"）。相邻表格 / 规则已说过，引用只加了语气没加信息。删。
5. **"此法为何好"的自我辩护** —— "升级标准可机械执行——这是防漂移的关键"、"这是消除'测不了'根因的正解"。这是在替规则辩护而非陈述规则。删自夸，留规则。
6. **跨文件重复** —— 同一条规则在 SKILL.md *和* 各 reference 里重述（java-unit-test 的断言库规则重复 5+ 次，Mock 边界规则 3 次）。规则只定义一次（跨切面默认通常在 SKILL.md，方法级细节在对应 reference）；其余地方用指针指过去，别再粘贴。
7. **完整代码块与 tools 文件重复** —— 当方法 reference（02/03/04）展示了完整 `@ParameterizedTest`/`assertThrows` 代码、而 tools 文件（06）有同样模式时：方法文件保留设计表，规范代码放 tools 文件。别两边都贴。
8. **面向维护者的元信息** —— "本文件存在的唯一意义…"、"本表只导航，不重复内容"、收录哲学（"只固化 A 类坑 / 不收 B 类"）。这些告诉*编辑者*如何策展，而非告诉 *agent* 做什么。从技能内容里删（本 AGENTS.md 才是放策展规则的正确位置）。

**反模式（不要删）**：携带*新操作事实*的 `>` 引用或旁注——如"测试不过时 JaCoCo 报告不生成（report 绑 test phase）"、"Mockito 4.x 需 mockito-inline"、"LocalDate.now() 首选 Clock 注入而非 mockStatic"。删掉它会让 agent 踩真坑，那就保留（可压缩）。

### 正向规则 + 反例（antipattern）协同——不要机械删反例

只告诉 agent *做什么* 往往不够。**错误做法常与正确做法表面相似**；一个 `✗` 反例能钉住正向规则单独无法区分的确切失败模式。每条反例 / 负面清单项用这个判据评估：

> *没有这条反例，agent 仅凭正向规则能区分对错吗？*
> - **能**（正向规则已足够精确，或反例与别处重复）→ 删。
> - **不能**（错误形式是正向规则的常见、合理误读）→ 留。

java-unit-test 的例子："coverage ≥ 80% is enough" 值得作为 `✗` 保留——哪怕别处已有"覆盖率是反向诊断指标而非目标"——没有这条显式反例，agent 仍会把数字当停止线。反之 S/A 表已禁止测试框架胶水代码后，"不要测 getter"就冗余了。

### 范围 / 边界声明不是"负面清单"——保留

范围声明（"本技能只覆盖单元测试；集成 / 性能 / 前端不在此范围内"）告诉 agent *不要往哪里跑*。这在操作上区别于"为什么不收录 X"的辩护（那是给维护者看的，应删）。前者保留，后者删除。

### 规则表里的"why"列通常冗余

一对 `✗ → ✓` 通常是完整、可执行的规则。尾随的"why"列往往用解释性散文重述 ✓。例外：当 why 列携带 *agent 需要的技术判据*（如"@MockBean 会重建 Spring Context"）时，把该事实折进 ✓ 单元格，而不是保留单独一列。

## 依赖 / 分层规则

- **技能大多自包含——敏捷族例外。** java / sa-token / mybatis 技能不得硬依赖另一个技能（声明自包含前用 `grep` 核实）。但敏捷技能（`agile-backlog`、`agile-sprint`、`agile-strategic`）在 `using-agile` / 彼此之间声明了显式 `dependencies:` frontmatter——这条依赖链是有意为之。
- **`eval/` 在 `skills/` 下游。** 评估*消费*技能内容；技能绝不从 `eval/` 导入。`eval/` 下没有产品代码。

## 提交风格（混合，非严格）

本仓库提交标题混用：`S1 <skill>: ...`（S0/S1/... = "slimdown 轮"）、`fix:`、`init:`、`add ...`。没有强制的单一方案。拿不准时跟最近一次提交的风格，或用 `S<n> <skill>: <摘要>` 表示一轮内容精简。**未经用户确认不要 amend / push。**

## 评估流程（达尔文）

- 达尔文评估在本仓库内进行；产物直接 commit 到 `eval/<skill-name>/`。
- 流程：打分（独立子 agent，避免自评偏差）→ 改进 → 测试（**实跑**，不要空想）→ 独立盲评重打分 → 棘轮（只保留已验证的改进）。
- 评估透明可复现——社区可读输入并质疑结果。
- 当某条反馈或修复可验证时**必须实跑测试**（搭最小 Maven 项目，跑代码）。不要仅凭阅读断言"这个示例能跑"——本仓库环境有真坑（见下）。

## 发布

发布到 SkillHub（腾讯）/ 虾评涉及平台凭证、ID、版本追踪，**绝不能进 git**。手册即 `PUBLISH.local.md`（gitignored）。**任何版本号调整或发布尝试前必读。** 发布是外发且不可逆——**两个平台发布前都要先与用户确认**。两套平台版本号相互独立，不要混。

## 平台 / 环境坑

- **Shell 是 Windows 上的 Git Bash。**
- **`grep -E "a|b"`（正则交替）在本 Git Bash 里稳定失败**，报 `conflicting matchers specified`——不是偶发，每次都中。变通：多次 `grep` 调用，或 `grep -e a -e b`，或 `git grep`，或 `rg`（若有）。
- **`mvn`（Git Bash 下的 Unix 脚本）会把 `/g/...` 或 `/i/...` 路径喂给 Windows `java.exe` → `ClassNotFound`。** 真要跑 Maven 构建，直接用 `mvn.cmd`（已在 PATH）并把输出重定向到日志文件再读——经 `powershell -Command` 包一层会把 stderr 染成红色错误文本，掩盖结果。
- **GBK 编码的 Maven 错误输出**：中文编译错误以 GBK 返回；用 `iconv -f gbk -t utf-8` 转码再读，或用 `strings`。
- 提交时的 LF→CRLF 警告无害（Windows `core.autocrlf`）；只在跨平台 LF 一致性有要求时才加 `.gitattributes`。
- `.zcode/` 是用户本地装的第三方技能（评估工具等）——已 gitignore，不属于本仓库，绝不提交。

## 改动敏感区前，先读

- `PUBLISH.local.md`（本地，gitignored）—— 当前线上版本、平台 ID、发布流程。**版本号调整或发布前必读。**
- `skills/repo-init/SKILL.md` + `references/03-antipatterns.md` —— 若要编辑*本* `AGENTS.md`（antipatterns 文件列举了此处要避免的错误）。
- `eval/README.md` —— 跑或提交达尔文评估前。
