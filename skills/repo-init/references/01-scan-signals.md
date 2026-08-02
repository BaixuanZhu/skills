# 01 · 扫描信号清单

init 的核心动作是**探测**：用 `Glob` / `Read` / `Grep` 系统性扫描下列信号，不要凭印象写；遗漏信号会导致 AGENTS.md 内容失真。高频聚合场景用一次 `Bash`（见 §0 铁律 4）。

## 0. Token 经济学铁律（执行本 Skill 前必读）

扫描整个仓库以生成 / 更新 AGENTS.md 时，放任原生 `Glob` / `Read` / `Grep` 漫无目的调用，会导致
**Token 浪费、上下文污染（Context Rot）、执行延迟**。下列铁律约束扫描行为：

> Bash 聚合命令为**按需复制执行的一次性命令**，直接调用即可，无需写脚本文件。

### 铁律 1 · 拒绝盲人摸象（限定范围，禁止无界扫描）
- ❌ `Glob("**/*")` / 全目录 `Grep("x", ".")`——会命中 `node_modules` / `dist` 的几万文件，瞬间撑爆上下文。
- ✅ 所有搜索**锚定根目录或特定配置目录**（`.github/` / `scripts/` / `src/` 入口层），并排除噪音目录。
  - `Grep` 基于 ripgrep，**默认遵循 `.gitignore`**（已自动跳过 `node_modules`）；仍须用 `glob` 限定文件类型、
    `head_limit` 收敛条数（如 `Grep('TODO', glob='*.{ts,tsx}', output_mode='files_with_matches', head_limit=20)`）。
  - `Glob` 避免根目录 `**` 全量；用根级窄模式（如 `Glob('*.{json,toml,yaml}')`）+ 必要子目录 `path` 限定深度。

### 铁律 2 · 元数据优先（读"配置"而非"源码"）
- 永远优先读**元数据文件**：`package.json` / `pom.xml` / `build.gradle` / `pyproject.toml` / `Makefile` /
  `Cargo.toml` / `go.mod` 的字段，比全仓库 `Grep` 命令名高效 100 倍。
- 例：读 `package.json` 的 `scripts` 拿构建/测试命令；读 `.github/workflows/*.yml` 拿 CI 门禁，而非去读各个测试文件。

### 铁律 3 · 懒加载读取（禁止全量 Read 大文件）
- 读大文件（`README.md` / `webpack.config.js` / 长 `AGENTS.md`）时 **只读前 N 行**（`Read` 带 `limit`，如 `limit=50`），
  或用 `Grep` 带 `context`（`-C 3`）抽取关键片段。**严禁**为"看一眼结构"而全量 `Read` 长文件。

### 铁律 4 · Bash 聚合优先（一次调用替代十次 Read）
- 用**一次** `Bash` 调用聚合信息，替代 LLM 循环 10+ 次 `Glob` / `Read`：
  - 目录骨架：`tree -L 2 -I 'node_modules|dist|.git' --dirsfirst`（或 `ls -d */`）
  - 字段精准提取：`jq '{name,scripts,dependencies}' package.json`
  - 入口定位：`grep -rl "export default" src --include='*.ts' | head -20`
- 环境差异：Windows/Git Bash 可能无 `tree` / `jq`。改用便携写法——抽取 JSON 字段用
  `python -c "import json;print(json.load(open('package.json')).get('scripts'))"`；目录骨架用 `ls -d */`
  或 `powershell Get-ChildItem -Depth 2`。
- 若运行环境提供高阶扫描工具（如 `scan_project` MCP / AST 提取器），优先用它替代多次低阶调用。

### 铁律 5 · 架构理解用"签名提取"而非全文

- 如需理解模块结构，**只提取** import 区、class / function 签名、导出列表；丢弃函数体实现与注释。
- 用 `Grep` 匹配 `^(export |import |class |def |func )` 或 `Read` 配合 `limit` 取文件头，不做全文读取。

### 铁律 6 · Path B 走 Git 增量（绝不重复全扫）
- 更新阶段（`02` Path B）**禁止全量重扫**：先 `git diff --name-only main..HEAD` / `git log --stat` 看变更面。
- 只对**发生变更的文件** `Read` / `Grep`；未变文件（如 `package.json` 没动）直接复用上一版 AGENTS.md 的命令，**零 Token**。
- 无 Git 时：`find . -type f -newermt '2026-01-01' -name '*.toml' -not -path '*/node_modules/*'` 仅扫近期配置。

### 铁律 7 · 信号先聚后出（内部草稿，不刷屏）
- 扫描过程中**不要**在对话里罗列每一个找到的文件。把信号整理成极简 JSON 对象（在内部推理中），
  再基于它生成最终 AGENTS.md，避免把原始扫描日志灌进上下文。

> 违反任一铁律 → 自检见 `03` §15。

## 1. 构建与依赖（决定 Setup commands）

| 文件 | 提取什么 |
|------|---------|
| `package.json` | scripts（dev/build/test/lint）、依赖、包管理器（`pnpm-lock.yaml`→pnpm，`yarn.lock`→yarn，无 lock→npm） |
| `pom.xml` | 构建命令（`mvn`）、JDK 版本、`spring-boot-maven-plugin` 的 run 目标 |
| `build.gradle` / `build.gradle.kts` | `gradle` / `./gradlew`、tasks、JDK |
| `Cargo.toml` | `cargo build` / `cargo test` |
| `go.mod` | `go build` / `go test`、`go version` 需求 |
| `requirements.txt` / `pyproject.toml` / `poetry.lock` | `pip install -r` / `poetry install` / `uv` |
| `Makefile` | 顶层 `make <target>` 常用入口 |
| `Dockerfile` / `docker-compose.yml` | 容器化启动方式 |

> **无构建元数据 fallback**：若上表文件**全部缺失**（纯 `.sh` 脚本集合、无 `pyproject.toml` 的零散 `.py`、
> 无构建步骤的前端 `index.html` 等），**不要臆造命令**——显式问用户"运行 / 部署命令是什么"，
> 或仅写已确认事实、命令栏标「需核实」。此类项目仍走标准模式（见强约束 8：无信号 section 直接省略），
> 不强行套 5 section。

> **命令真实性**（强约束 C2）：安装/构建/测试命令**必须**从上述文件实际提取。
> 例：`package.json` 有 `"test": "vitest"` → 写 `pnpm test`（若 lock 是 pnpm）；不要写 `npm run test` 若项目用 pnpm。
> 无法确认时标注「需核实」或询问，不臆造。

## 2. 入口与测试（决定 Testing instructions）

- 主入口：`main` 函数、`index.ts`/`app.ts`、框架启动类（`@SpringBootApplication`）。
- 测试目录：`*test*` / `tests/` / `__tests__/` / `src/test/`；测试框架（`vitest` / `jest` / `pytest` / `junit`）。
- 测试命令：优先取 `scripts.test`；无则按框架惯例（如 `cargo test`）。

## 3. CI / CD（决定约定与发布）

- `.github/workflows/*.yml`、` .gitlab-ci.yml`、`Jenkinsfile`、`.circleci/config.yml`：
  读取 lint / build / test / deploy 步骤，确认团队强制的检查项。

## 4. Linter / 格式化（决定 Code style）

- `eslintrc*` / `.eslintrc` / `eslint.config.*`、`prettier*`、`.editorconfig`
- `checkstyle*.xml`、`spotless`、`google-java-format`、`black` / `ruff` / `flake8`、`gofmt` / `golangci-lint`
- 约定信号：单引号 vs 双引号、分号、行宽、命名（`camelCase` / `snake_case`）、import 顺序。

## 5. 已有上下文文件（决定增量 vs 覆盖）

| 文件 | 含义 |
|------|------|
| `AGENTS.md` | 已采用通用标准 → **增量改进，不覆盖**（C1） |
| `CLAUDE.md` | Claude Code 专属 → 内容可合并进 AGENTS.md，不重复维护两份 |
| `.cursorrules` / `.windsurfrules` / `.clinerules` | 工具专属 → 同上，并入 AGENTS.md |
| `README.md` / `README.zh-CN.md` | 项目概述、快速开始，提取 Setup 与架构要点 |
| `CONTRIBUTING.md` | PR 流程、分支策略、提交规范 |
| `.workbuddy/` 记忆 | 团队既有约定，可参考但不写入 AGENTS.md（工具专属，非通用） |
| `CODEOWNERS` | 模块负责人，判断是否需要子目录就近覆盖（见 `04`） |

## 6. 陷阱信号（决定 Hard constraints / Known gotchas）

- 框架特定约束：如「禁止编辑 `generated/` 与 proto 生成物」「`migrations/` 只能由 CLI 生成」。
- **环境变量注入方式（AI 极易写错，重点探测）**：前端打包器决定前缀与注入时机，扫描 `vite.config.*`、
  `next.config.*` / `next.config.mjs`、`vue.config.*`、`craco.config.*`，以及代码里 `import.meta.env` 与
  `process.env` 的实际用法，区分**构建时**与**运行时**注入：
  - **Vite**：`import.meta.env.VITE_*`，**构建时**静态替换（改值需重建，不读运行时进程环境；非 `VITE_` 前缀不暴露给前端）。
  - **Next.js**：客户端 `process.env.NEXT_PUBLIC_*`（构建时）；服务端 `process.env.*`（**运行时**）。
  - **Vue CLI**：`process.env.VUE_APP_*`（构建时）；**CRA**：`process.env.REACT_APP_*`（构建时）。
  - **后端 Node**：`process.env.*`（**运行时**注入，常由 `dotenv` 启动时加载 `.env`）。
  - 探测 `.env*` 文件（`.env` / `.env.example` / `.env.production`）：必填项、是否分环境。
  - 结论写进 AGENTS.md 的 **Known gotchas**：明确「前端用 X（构建时）/ 后端用 Y（运行时）」，杜绝混用。
- 已知坑：`node` 版本要求（`.nvmrc` / `engines`）、`monorepo` 必须用 `--filter`、
  切换包管理器的禁忌、特定平台编译依赖。
- 安全红线：`secrets` 不得提交、`master`/`main` 保护分支、禁止 `--no-verify` 绕过 hook。

## 7. 国际化（i18n）信号（决定 Hard constraints）

- 探测 i18n 配置与资源：
  - 配置：`i18next.config.js/.ts`、`next-i18next.config.js`、`i18n.ts`、`vue-i18n` 配置、`lingui.config.js`、`next-intl` 配置。
  - 资源目录：`messages/`、`locales/`、`translations/`、`i18n/`、`public/locales/` 下的 `*.json` / `*.po` / `*.yaml`。
  - 依赖：`i18next` / `react-i18next` / `vue-i18n` / `@lingui/core` / `next-intl` / `formatjs`（查 `package.json`）。
- 命中 → AGENTS.md **必须**写入 **Hard constraints**：「禁止硬编码中/英文字符串，所有用户可见文案走 i18n 函数
  （`t('key')` / `<Trans>` / `intl.formatMessage`）」；并标注默认语言与资源目录位置，防止 AI 在组件里直接写死文案。

> 扫描完上述 7 类信号，再进入 `02-output-template.md` 草拟。信号不全 → 宁可标注「需核实」，不臆造。
