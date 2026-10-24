# AGENTS.md

**技能(Skill)开发 + 分发仓库**：编写、评估、分发面向中文 Java/Spring 生态（Sa-Token、MyBatis-Plus、Java 编码规范、敏捷流程）的 Agent Skills（SKILL.md 内容包）。**没有要构建/运行/部署的应用——产品就是技能内容本身。**

## 仓库结构

两个内容目录是核心，其余是配套：

- `skills/<name>/` —— **技能内容唯一编辑源**（npx skills / SkillHub / ZCode-npx 扫描这里）。每个含 `SKILL.md`（YAML frontmatter：`name`/`description`/`version`/`slug`/`displayName`，敏捷族另有 `dependencies`）+ `references/`（编号 `NN-topic.md`，1~14 个）+ 个别有 `assets/`（如 `java-contract` 含契约模板）。sync hook 自动同步整个 `assets/` 子树到 `plugins/`。
- `plugins/<name>/` —— **skills/ 的镜像**（Claude Code / ZCode / Codex 插件规范要求 manifest + `skills/<name>/` 嵌套，故与扁平的 `skills/` 分开存放）。每个含 `.claude-plugin/plugin.json`（Claude Code / ZCode 读）+ `.codex-plugin/plugin.json`（Codex 读）。支持「多 skill 合并入 1 个 plugin」（agile / java-test 两个 group，见下文「group 映射」）。**除 `hooks/`、`scripts/` 外不要手改这里**——pre-commit hook 从 `skills/` 自动同步。
- `.claude-plugin/marketplace.json` —— Claude Code / ZCode 插件市场清单，`plugins[]` 每条 `source` 指 `./plugins/<name>`。
- `.agents/plugins/marketplace.json` —— Codex 插件市场清单，`plugins[]` 每条 `source` 是对象（`{"source":"local","path":"./plugins/<name>"}` + `policy` + `category`），与 Claude 的字符串 `source` 不同。
- `eval/<skill-name>/` —— 达尔文评估产物（`eval/` 下游于 `skills/`，技能不从 eval 导入）。
- `PUBLISH.local.md` —— **gitignored**，线上版本/平台 ID/发布流程的唯一真相来源。
- `.zcode/` —— 用户本地第三方技能，**gitignored，绝不提交**。

## 分发与同步

### 三协议，共享 `skills/` 内容

| 协议 | 识别依据 | 用户命令 |
|---|---|---|
| Claude Code / ZCode 插件 | `.claude-plugin/marketplace.json` + `plugins/<name>/` | `/plugin marketplace add BaixuanZhu/skills` → `/plugin install <name>` |
| Codex 插件 | `.agents/plugins/marketplace.json` + `plugins/<name>/`（兼容读 `.claude-plugin/marketplace.json`） | `codex plugin marketplace add BaixuanZhu/skills` |
| npx skills（Vercel CLI，41+ agent 通用） | `skills/<name>/SKILL.md`（自动扫描） | `npx skills add BaixuanZhu/skills` |

### plugins/ 是 skills/ 的镜像 —— hook 自动同步

改技能**只改 `skills/<name>/`**。pre-commit hook（`scripts/sync-plugins.mjs`）自动把内容 + version 同步到 `plugins/`（`.claude-plugin` + `.codex-plugin` 双 manifest）+ 两份 `marketplace.json`，加进本次 commit（单 commit，干净）。GitHub Actions（`.github/workflows/verify-sync.yml`）push 时兑底校验，未同步则 CI 失败拦截。

- **装 hook**：`npm install`（`postinstall` 自动装到 `.git/hooks/pre-commit`）。换机器 / 新 clone 后跑一次。
- **手动跑同步**（不 commit）：`node scripts/sync-plugins.mjs`
- **references 交叉引用校验**：`node scripts/check-refs.mjs skills/<name>/references`（严格，悬空即退出 1）；不带参数扫全仓只报告（各 skill 标题风格不统一，全量难免残留噪音，别拿来当门禁）。`-v` 打印每处引用的实际标题——删减章节后重编号会复用旧编号，此时 §N 依然"可达"但指向已换，纯可达性检查抓不到这种语义错位。
- **新增 / 删除技能**：hook 不自动建 / 删 `plugins/` 结构。需手动①在 `skills/<name>/` 建内容 → ②在 `plugins/<name>/` 建合规包（`.claude-plugin/plugin.json` + `.codex-plugin/plugin.json` + `skills/<name>/` 嵌套）→ ③在**两份** `marketplace.json`（`.claude-plugin/` 与 `.agents/plugins/`）的 `plugins[]` 各追加条目。之后同步自动。归入既有 group 的技能只需在 `plugin-map.json` 的 `groups.<group>.skills[]` 加名字，无需另建 plugin。
- **group 映射**（`scripts/plugin-map.json`）：声明多个 skill 合并到 1 个 plugin。现有 2 个 group：`agile`（using-agile / agile-strategic / agile-backlog / agile-sprint）、`java-test`（java-unit-test / java-integration-test）。sync hook 据此把组内各 skill 同步到 `plugins/<group>/skills/<skill名>/`；group 插件版本取组内 skill 版本的 max（`"version": "max"`），**组内容有变化但 max 未超过当前插件版本时（低版本成员更新），hook 自动 bump patch**——否则插件市场版本号不动、已装用户收不到更新提示。不在 group 里的 skill 走默认 1:1（`plugins/<name>/skills/<name>/`）。
- **aliases 映射**：单技能但插件名与技能名不同时（如 `java-contract` → `java-standard`），在 `plugin-map.json` 的 `aliases` 登记。仍走 1:1 版本逻辑、**不 bump patch**（与 `groups` 语义不同：aliases 只是换插件名，groups 是内容合并）。**插件名与技能名不得共用同一实词**，否则菜单显示成 `/x:x`。
- **marketplace.json 的 `description`/`category`/`keywords`/`source` 独立维护**（hook 不动）——因为 SKILL.md 的 `description` 是长触发器文本，与 marketplace 的一句话简述不是同一内容。
- **例外：插件级 `hooks/` 与 `scripts/` 不镜像、不清理**（现有 `plugins/mybatis-plus-dev/` 的 PostToolUse 症状提示、`plugins/agile/` 的两个门禁）。sync 只镜像 `plugins/<name>/skills/<skill>/` 子树，`rmSync` 范围也限于该路径，所以这两个目录**既不会被误删，也不会被同步**——改它们要直接改 `plugins/` 侧，那是仓库里唯一的单副本资产。钩子用 exec form（不过 shell，路径无需引号），`${CLAUDE_PLUGIN_ROOT}` 由平台注入：解释器确定时直接 `"command": "node"` + `"args": ["${CLAUDE_PLUGIN_ROOT}/scripts/x.mjs"]`；解释器可能缺席时（`python` 在 macOS/部分 Linux 上不存在）套一层 `"command": "sh"` + `"args": ["${CLAUDE_PLUGIN_ROOT}/scripts/run-python.sh", "子命令"]`，由 shell 脚本探测并 `exec`，**exec 才能把 exit 2 原样传出**——`cmd || cmd2` 这种写法会把 exit 2 变成 cmd2 的退出码，门禁语义当场失效。
- **钩子挂点按作用域选，不按方便选**：要求「任何来源的提交都生效」的门禁 → 装到项目自己的 git pre-commit（`core.hooksPath` 或往已有 hook 追加一行），模板放插件 `assets/`、由技能引导初始化一次；只关心 AI 行为的提示 → Claude Code 的 PreToolUse / PostToolUse。**PreToolUse 看不见 IDE、终端、`gh` 发起的提交**，用它做质量门禁等于只拦一半。
- **门禁不写解析脚本**：阈值、打印明细、是否失败都先用构建工具的现成参数（maven-pmd-plugin 的 `failurePriority` / `printFailingErrors` / `failOnViolation`），退出码原样交给 git。脚本一旦开始解析构建报告，就是第二份实现，跟着上游格式变而腐坏。
- **症状索引钩子（PostToolUse）只在前述条件同时成立时才做**：① 报错文案里**不含**排查方向，必须靠领域知识补（如 `BindingException` 不说「接口与 XML 的 id 要同名同参」）；② 匹配的 token 是**框架/数据库给的英文异常名**，不随 locale 变化。反例：javac 诊断是本地化的（中文 `找不到符号` / 英文 `cannot find symbol`），且 `records are not supported in -source 11` 这类已直接说明原因——这类写进技能文档的判据表，比随插件分发一个要维护两套 token 的脚本更稳。
- **注入点按内容性质选**：静态事实与约定 → `.claude/rules/` 带 `paths`（只对相关文件生效，落盘可 review、可团队共享、不依赖运行时）；需要现算才有的动态状态（当前分支、CI 状态、存量违规数）→ SessionStart；强制阻断 → 项目 git hook 或 PreToolUse。**静态内容不要用 SessionStart**：官方文档明确说静态上下文用 CLAUDE.md 即可、不必跑脚本，而且 SessionStart 只在 Claude Code 内有效、每次会话启动都要等它跑完。
- **要机器读的产出，真源用 JSON，人读视图由脚本渲染**：别把同一份数据写成「人也能读、脚本也要解析」的 Markdown 表格——解析器得容错列数漂移、全角空格、`\|` 转义，容错越多越脆，最后整段正则就是第二份实现。`agile-docs/backlog.json` 单向渲染出 `PRODUCT-BACKLOG.md`（md 从不回写 json），因此没有 v4.x 那种双写漂移，也不存在「两边保持一致」的负担。脚本标准库 only、**结构化数据一律走 `json` 模块，不写正则**；只有迁移旧格式这种一次性动作才需要解析表格。
- **种子/模板里不写会腐坏的状态值**，只写指令。写成「`.qualitygate/pmd-pom.xml` 不存在就先装配」而不是「门禁未安装」——后者在装完之后变成假话，前者永远成立。版本标记同理，模板用占位符 `⟨版本⟩`，播种时从 SKILL.md frontmatter 取，避免模板里的数字随技能升级漂移。

### 新增 plugin / marketplace 条目的字段要求

`plugins[]` 每条：`{name, version, author: {name, email}, source: "./plugins/<name>", description, category, keywords}`
- `source` 必须**指 `./plugins/<name>`**（不是 `./skills/<name>`）——指向 skills/ 会导致 Claude Code / ZCode "装上但不触发"（加载器进 source 找 `.claude-plugin/plugin.json` + `skills/<name>/SKILL.md`，扁平目录缺这俩）。
- `author` 用隐私邮箱 `66127517+BaixuanZhu@users.noreply.github.com`（noreply，不暴露真实地址）。
- 缺 `version`/`author` → 市场只显示插件名，看不到版本号和开发者。
- 每个 plugin 需**两份 manifest**：`.claude-plugin/plugin.json`（`name`/`version`/`description`/`author`）+ `.codex-plugin/plugin.json`（Claude 版超集，多 `license`/`keywords`/`skills`(指向 `./skills/`)/`interface` 展示字段）。Codex 的 `marketplace.json` 独立放 `.agents/plugins/`，`source` 是对象格式（见上文）。

### 版本号真值源

**只改 `skills/<name>/SKILL.md` frontmatter 的 `version`**，hook 自动同步到：① `plugins/<name>/.claude-plugin/plugin.json`（Claude Code / ZCode 安装后读）② `plugins/<name>/.codex-plugin/plugin.json`（Codex 安装后读）③ 两份 `marketplace.json` 对应条目（市场列表展示读，不同步则版本落后）。

- **独立插件**（1:1）：skill version 直接写入对应 plugin.json + marketplace 条目。
- **group 插件**（多 skill 合一，如 agile）：plugin 版本取组内所有 skill version 的 max。各 skill 自己的 version 独立维护（`skills/<name>/SKILL.md`），plugin 版本跟随最高的那个。

- 线上当前版本在 `PUBLISH.local.md`（gitignored，**不看 git tag**），版本号调整前先读它。SkillHub 对等于或低于线上的版本号**静默拒收**（不报错、不更新）。

## 编辑技能内容的约定

- **权威外部参考**：<https://agentskills.io/home> —— 拿不准结构 / frontmatter / 最佳实践时查阅。
- `description` 两种 YAML 风格都存在：`>-`（折叠，长触发描述）与 `|`（字面量，较短）。与该技能现有风格一致。
- 编号 references 按阅读优先级排序；文件间用指针交叉引用，**不要复制内容**。
- 规则风格 `✗ 禁止 → ✓ 推荐`，匹配每个技能双语（中文为主）语调。
- 编辑原则：不重复论证已成定局的决策；不留"可选附录"——发现就删。

## 技能内容质量标准（创建 / 更新 / 优化任何技能时适用）

**判据**：删掉这段文字，执行中的 agent 会产出不同（更差）的结果吗？会 → 必须保留；不会 → 冗余。

- **必须保留**：阈值、触发条件、命令、映射表、防漂移的机械判据、隐性陷阱（错误不显式报错——如 spy/doReturn、verify 次数语义、mockito-inline 依赖坑）、边界 / 范围声明。
- **冗余模式**（多为散文论证，删或压缩）：
  1. **原理前言**（"核心立场"/"X 的核心价值"——论证方法为何重要）→ 删论证留步骤。
  2. **学术渊源**（"Chow 1978"、"杀虫剂悖论"等典故）→ 删引用留规则。
  3. **ASCII 可视化复述相邻表格**（决策树 / 数轴 / 矩阵紧跟具体示例前）→ 删图，除非编码了表格没有的决策。
  4. **励志引用块**（`>` 重述上下文加语气）→ 删。
  5. **自我辩护**（"此法可机械执行——防漂移关键"）→ 删自夸留规则。
  6. **跨文件重复**（同规则在 SKILL.md + 各 reference 重述）→ 定义一次，余处用指针。
  7. **代码块与 tools 文件重复**（方法 reference 与 tools 文件贴同样完整代码）→ 方法文件留设计表，规范代码放 tools 文件。
  8. **维护者元信息**（"本文件存在的唯一意义…"/收录哲学）→ 从技能内容删（本 AGENTS.md 才是放策展规则的位置）。
- **反例（`✗`）取舍**：*没有这条反例，agent 仅凭正向规则能区分对错吗？* 能 → 删；不能（错误形式是正向规则的常见误读）→ 留。
- **范围声明保留**（"本技能只覆盖单元测试；集成 / 性能 / 前端不在此范围"是操作性的，区别于"为什么不收录 X"的辩护——后者删）。
- **规则表的 "why" 列通常冗余**（重述 ✓ 的解释性散文）→ 删，除非携带 agent 需要的技术判据（如"@MockBean 重建 Spring Context"），此时折进 ✓ 单元格。

## 一致性防回归清单（编辑技能时逐条自查）

历轮达尔文评估（`eval/agile/`）反复出现的错误形态——多数不是"写得差"而是"**改漏了**"。编辑任何技能（尤其套件）时：

1. **改规则先 grep 旧口径**：新增/修改一条规则时，grep 该规则在套件内的全部出现处（含「硬约束」节——复述重灾区），注意非字面量变体（如 `PRODUCT-BACKLOG（.md + .yaml）` 这种写法 replace_all 扫不到）。旧规则要么删、要么显式限定适用范围；新旧并存互斥是历轮 P1 的主要形态。
2. **每个 reference 必须被 SKILL.md 指针引用**：agent 只读 SKILL.md 也应能发现全部 references——孤儿 reference = 内容不可达（曾致整个 DOD 模板不可见）。
3. **要求落盘必查承接字段**：凡写"标注 X / 记录 Y / 文件头标注 Z"，检查模板、表格列、schema 枚举确有对应位置；没有就先加字段。反向同理：改状态枚举时 grep 引用它的 schema / 模板 / 同步规则（曾出现永不被写入的死枚举）。
4. **新增产物文件同步所有清单**：新文件产物（如 STRATEGY_CONFLICT.md）要同步进检测清单 / 状态表 / 路由决策——否则产物存在而链路对它不可见。
5. **编号引用带语义**：引用他节 / 门禁写"编号 + 语义"（如"边界异常 ⑤（过大拆分）"），纯编号引用在权威源重排后必错位（⑤/⑥、§二/§三 错位皆因此起）。
6. **术语一处定义、改口径全套件 grep**：同一概念（状态名、方向词、角色称谓、来源分类）只用一种写法。典型分裂：上游/上层/下游混用、"产品负责人" vs "用户（唯一拍板人）"、来源三分类 vs 两分类。
7. **示例三查**：示例之间一致（同 id 同值）、示例与 schema/字段表一致、不含特定项目专名（yudao / "815 Market" 之类不进通用技能）。
8. **话术对齐生命周期**：问"是否继续下一步"时，"下一步"必须是该时刻真实存在的下一步（曾出现规划刚完成即问"是否进入关闭"）。

## 依赖 / 分层

- **技能大多自包含——敏捷族例外**：java / sa-token / mybatis 技能不得硬依赖另一个技能（声明自包含前 `grep` 核实）。敏捷技能（`agile-backlog`/`agile-sprint`/`agile-strategic`）在 `using-agile` / 彼此之间声明显式 `dependencies:`——这条依赖链有意为之。

## 提交 / 评估 / 发布

- **提交风格**（混合，非严格）：`S<n> <skill>: <摘要>`（slimdown 轮）/ `fix:` / `init:` / `add ...`。拿不准跟最近一次提交风格。**未经用户确认不要 amend / push。**
- **达尔文评估**：在本仓库内进行，产物 commit 到 `eval/<skill-name>/`。流程：独立子 agent 打分（避免自评偏差）→ 改进 → **实跑测试**（搭最小 Maven 项目跑代码，不要空想）→ 独立盲评重打分 → 棘轮（只保留已验证改进）。透明可复现。跑或提交评估前先读 `eval/README.md`。
- **发布**：仅到 SkillHub（腾讯），涉及平台凭证、ID、版本追踪，**绝不能进 git**。手册即 `PUBLISH.local.md`。**发布外发且不可逆——发布前要先与用户确认。**

## 平台 / 环境坑

- **Shell 是 Windows 上的 Git Bash。**
- **`grep -E "a|b"`（正则交替）稳定失败**，报 `conflicting matchers specified`——不是偶发，每次都中。变通：多次 `grep`，或 `grep -e a -e b`，或 `git grep`，或 `rg`（若有）。
- **`mvn`（Git Bash 下 Unix 脚本）把 `/g/...` 或 `/i/...` 路径喂给 Windows `java.exe` → `ClassNotFound`**。真要跑 Maven 构建，直接用 `mvn.cmd`（已在 PATH）并重定向输出到日志再读——经 `powershell -Command` 包一层会把 stderr 染红掩盖结果。
- **GBK 编码的 Maven 错误输出**：中文编译错误以 GBK 返回；用 `iconv -f gbk -t utf-8` 转码，或 `strings`。
- LF→CRLF 警告无害（Windows `core.autocrlf`）；只在跨平台 LF 一致性有要求时才加 `.gitattributes`。

## 改动敏感区前，先读

- `PUBLISH.local.md`（本地，gitignored）—— 线上版本、平台 ID、发布流程。**版本号调整或发布前必读。**
- `eval/README.md` —— 跑或提交达尔文评估前。
