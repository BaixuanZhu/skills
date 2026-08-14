# AGENTS.md

**技能(Skill)开发 + 分发仓库**：编写、评估、分发面向中文 Java/Spring 生态（Sa-Token、MyBatis-Plus、Java 编码规范、敏捷流程）的 Agent Skills（SKILL.md 内容包）。**没有要构建/运行/部署的应用——产品就是技能内容本身。**

## 仓库结构

两个内容目录是核心，其余是配套：

- `skills/<name>/` —— **技能内容唯一编辑源**（npx skills / SkillHub / ZCode-npx 扫描这里）。每个含 `SKILL.md`（YAML frontmatter：`name`/`description`/`version`/`slug`/`displayName`，敏捷族另有 `dependencies`）+ `references/`（编号 `NN-topic.md`，1~14 个）+ 个别有 `assets/`（仅 java-coding-quality）。
- `plugins/<name>/` —— **skills/ 的镜像**（Claude Code / ZCode 插件规范要求 `.claude-plugin/plugin.json` + `skills/<name>/` 嵌套，故与扁平的 `skills/` 分开存放）。支持「多 skill 合并入 1 个 plugin」（如 4 个敏捷 skill 归入 `plugins/agile/`，见下文「group 映射」）。**不要手改这里**——pre-commit hook 从 `skills/` 自动同步。
- `.claude-plugin/marketplace.json` —— Claude Code 插件市场清单，`plugins[]` 每条 `source` 指 `./plugins/<name>`。
- `eval/<skill-name>/` —— 达尔文评估产物（`eval/` 下游于 `skills/`，技能不从 eval 导入）。
- `PUBLISH.local.md` —— **gitignored**，线上版本/平台 ID/发布流程的唯一真相来源。
- `.zcode/` —— 用户本地第三方技能，**gitignored，绝不提交**。

## 分发与同步

### 双协议，共享 `skills/` 内容

| 协议 | 识别依据 | 用户命令 |
|---|---|---|
| Claude Code / ZCode 插件 | `.claude-plugin/marketplace.json` + `plugins/<name>/` | `/plugin marketplace add BaixuanZhu/skills` → `/plugin install <name>` |
| npx skills（Vercel CLI，41+ agent 通用） | `skills/<name>/SKILL.md`（自动扫描） | `npx skills add BaixuanZhu/skills` |

### plugins/ 是 skills/ 的镜像 —— hook 自动同步

改技能**只改 `skills/<name>/`**。pre-commit hook（`scripts/sync-plugins.mjs`）自动把内容 + version 同步到 `plugins/` + `marketplace.json`，加进本次 commit（单 commit，干净）。GitHub Actions（`.github/workflows/verify-sync.yml`）push 时兑底校验，未同步则 CI 失败拦截。

- **装 hook**：`npm install`（`postinstall` 自动装到 `.git/hooks/pre-commit`）。换机器 / 新 clone 后跑一次。
- **手动跑同步**（不 commit）：`node scripts/sync-plugins.mjs`
- **新增 / 删除技能**：hook 不自动建 / 删 `plugins/` 结构。需手动①在 `skills/<name>/` 建内容 → ②在 `plugins/<name>/` 建合规包（`.claude-plugin/plugin.json` + `skills/<name>/` 嵌套）→ ③在 `marketplace.json` 的 `plugins[]` 追加条目。之后同步自动。归入既有 group 的技能只需在 `plugin-map.json` 的 `groups.<group>.skills[]` 加名字，无需另建 plugin。
- **group 映射**（`scripts/plugin-map.json`）：声明多个 skill 合并到 1 个 plugin（如敏捷 4 技能 → `plugins/agile/`）。sync hook 据此把组内各 skill 同步到 `plugins/<group>/skills/<skill名>/`；group 插件版本取组内 skill 版本的 max（`"version": "max"`）。不在 group 里的 skill 走默认 1:1（`plugins/<name>/skills/<name>/`）。
- **marketplace.json 的 `description`/`category`/`keywords`/`source` 独立维护**（hook 不动）——因为 SKILL.md 的 `description` 是长触发器文本，与 marketplace 的一句话简述不是同一内容。

### 新增 plugin / marketplace 条目的字段要求

`plugins[]` 每条：`{name, version, author: {name, email}, source: "./plugins/<name>", description, category, keywords}`
- `source` 必须**指 `./plugins/<name>`**（不是 `./skills/<name>`）——指向 skills/ 会导致 Claude Code / ZCode "装上但不触发"（加载器进 source 找 `.claude-plugin/plugin.json` + `skills/<name>/SKILL.md`，扁平目录缺这俩）。
- `author` 用隐私邮箱 `66127517+BaixuanZhu@users.noreply.github.com`（noreply，不暴露真实地址）。
- 缺 `version`/`author` → 市场只显示插件名，看不到版本号和开发者。

### 版本号真值源

**只改 `skills/<name>/SKILL.md` frontmatter 的 `version`**，hook 自动同步到：① `plugins/<name>/.claude-plugin/plugin.json`（Claude Code / ZCode 安装后读）② `marketplace.json` 对应条目（市场列表展示读，不同步则版本落后）。

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
- `skills/repo-init/SKILL.md` + `references/03-antipatterns.md` —— 若编辑*本* `AGENTS.md`（antipatterns 文件列举了此处要避免的错误）。
- `eval/README.md` —— 跑或提交达尔文评估前。
