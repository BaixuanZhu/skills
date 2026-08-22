# 01 · 扫描信号清单

init 的核心动作是**探测**：用 `Glob` / `Read` / `Grep` 系统性扫描下列信号，不要凭印象写；遗漏信号会导致 AGENTS.md 内容失真。高频聚合场景用一次 `Bash`（见 §0 铁律 4）。

## 0. Token 经济学铁律（执行本 Skill 前必读）

放任原生 `Glob` / `Read` / `Grep` 漫无目的调用会导致 **Token 浪费、上下文污染（Context Rot）、执行延迟**。下列铁律约束扫描行为；Bash 聚合命令为**按需复制执行的一次性命令**，无需写脚本文件。

1. **限定范围（拒绝盲人摸象）**：❌ `Glob("**/*")` / 全目录 `Grep("x", ".")`——命中 `node_modules` / `dist` 几万文件撑爆上下文。✅ 锚定根目录或特定配置目录（`.github/` / `scripts/` / `src/` 入口层）；`Grep` 基于 ripgrep 默认遵循 `.gitignore`，仍用 `glob` 限文件类型 + `head_limit` 收敛（如 `Grep('TODO', glob='*.{ts,tsx}', output_mode='files_with_matches', head_limit=20)`）；`Glob` 用根级窄模式（`Glob('*.{json,toml,yaml}')`）+ 子目录 `path` 限深度。
2. **元数据优先（读配置而非源码）**：优先读 `package.json` / `pom.xml` / `build.gradle` / `pyproject.toml` / `Makefile` / `Cargo.toml` / `go.mod` 字段。例：`package.json` 的 `scripts` 拿构建/测试命令；`.github/workflows/*.yml` 拿 CI 门禁，不读测试文件。
3. **懒加载读取**：读大文件（`README.md` / 长 `AGENTS.md`）只读前 N 行（`Read` `limit=50`）或 `Grep` `-C 3` 抽片段；**严禁**为"看一眼结构"全量 `Read` 长文件。
4. **Bash 聚合优先（一次调用替代十次 Read）**：目录骨架 `tree -L 2 -I 'node_modules|dist|.git' --dirsfirst`（无 tree 用 `ls -d */`）；字段提取 `jq '{name,scripts,dependencies}' package.json`（无 jq 用 `python -c "import json;print(json.load(open('package.json')).get('scripts'))"`）；入口定位 `grep -rl "export default" src --include='*.ts' | head -20`。环境提供高阶扫描工具（`scan_project` MCP / AST 提取器）时优先用它。
5. **架构理解用签名提取而非全文**：只提取 import 区、class / function 签名、导出列表（`Grep` 匹配 `^(export |import |class |def |func )` 或 `Read` 取文件头），丢弃函数体与注释。
6. **Path B 走 Git 增量（绝不重复全扫）**：更新阶段（`02` Path B）先 `git diff --name-only main..HEAD` / `git log --stat` 看变更面，只扫变更文件，未变文件复用上一版命令。无 Git 时 `find . -type f -newermt '2026-01-01' -name '*.toml' -not -path '*/node_modules/*'` 仅扫近期配置。
7. **信号先聚后出**：扫描过程中**不**在对话里罗列找到的文件；信号整理成极简 JSON 对象（内部推理），再据此生成最终 AGENTS.md。

> 违反任一铁律 → 自检见 `03` §13（Token 爆炸）。

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

> **无构建元数据 fallback**：上表文件**全部缺失**（纯 `.sh` 脚本集合、无 `pyproject.toml` 的零散 `.py`、无构建步骤前端）→ **不要臆造命令**：显式问用户"运行 / 部署命令是什么"，或仅写已确认事实、命令栏标「需核实」。仍走标准模式（强约束 8：无信号 section 省略），不强行套 5 section。

> **命令真实性**（C2）：安装/构建/测试命令**必须**从上述文件实际提取。例：`package.json` 有 `"test": "vitest"` → 写 `pnpm test`（若 lock 是 pnpm）；不要写 `npm run test`。无法确认标「需核实」或询问。

## 2. 入口与测试（决定 Testing instructions）

- 主入口：`main` 函数、`index.ts`/`app.ts`、框架启动类（`@SpringBootApplication`）。
- 测试目录：`*test*` / `tests/` / `__tests__/` / `src/test/`；测试框架（`vitest` / `jest` / `pytest` / `junit`）。
- 测试命令：优先取 `scripts.test`；无则按框架惯例（如 `cargo test`）。

## 3. CI / CD（决定约定与发布）

- `.github/workflows/*.yml`、`.gitlab-ci.yml`、`Jenkinsfile`、`.circleci/config.yml`：读取 lint / build / test / deploy 步骤，确认团队强制检查项。

## 4. Linter / 格式化（决定 Code style）

- `eslintrc*` / `eslint.config.*`、`prettier*`、`.editorconfig`；`checkstyle*.xml`、`spotless`、`google-java-format`、`black` / `ruff` / `flake8`、`gofmt` / `golangci-lint`
- 约定信号：单引号 vs 双引号、分号、行宽、命名（`camelCase` / `snake_case`）、import 顺序。

## 5. 已有上下文文件（决定增量 vs 覆盖）

| 文件 | 含义 |
|------|------|
| `AGENTS.md` | 已采用通用标准 → **增量改进，不覆盖**（C1） |
| `CLAUDE.md` | Claude Code 专属 → **有实质内容则迁移进 AGENTS.md 并降为适配指针 stub**（见 `05`）；已是 stub（首行 `@AGENTS.md`）则不动 |
| `.cursorrules` / `.windsurfrules` / `.clinerules` | 工具专属 → 内容并入 AGENTS.md；Cursor/Windsurf 已原生读 AGENTS.md，迁移后直接删 |
| `README.md` / `README.zh-CN.md` | 项目概述、快速开始，提取 Setup 与架构要点 |
| `CONTRIBUTING.md` | PR 流程、分支策略、提交规范 |
| `.workbuddy/` 记忆 | 团队既有约定，可参考但不写入 AGENTS.md（工具专属，非通用） |
| `CODEOWNERS` | 模块负责人，判断是否需要子目录就近覆盖（见 `04`） |

## 6. 陷阱信号（决定 Hard constraints / Known gotchas）

- 框架特定约束：如「禁止编辑 `generated/` 与 proto 生成物」「`migrations/` 只能由 CLI 生成」。
- **环境变量注入方式（AI 极易写错，重点探测）**：扫描 `vite.config.*`、`next.config.*`、`vue.config.*`、`craco.config.*`，以及代码里 `import.meta.env` / `process.env` 实际用法，区分**构建时**与**运行时**：
  - **Vite**：`import.meta.env.VITE_*`，**构建时**静态替换（改值需重建，不读运行时进程环境；非 `VITE_` 前缀不暴露给前端）。
  - **Next.js**：客户端 `process.env.NEXT_PUBLIC_*`（构建时）；服务端 `process.env.*`（**运行时**）。
  - **Vue CLI**：`process.env.VUE_APP_*`（构建时）；**CRA**：`process.env.REACT_APP_*`（构建时）。
  - **后端 Node**：`process.env.*`（**运行时**，常由 `dotenv` 启动时加载 `.env`）。
  - 探测 `.env*`（`.env` / `.env.example` / `.env.production`）：必填项、是否分环境。
  - 结论写进 **Known gotchas**：「前端用 X（构建时）/ 后端用 Y（运行时）」，杜绝混用。
- 已知坑：`node` 版本要求（`.nvmrc` / `engines`）、`monorepo` 必须用 `--filter`、切换包管理器禁忌、特定平台编译依赖。
- 安全红线：`secrets` 不得提交、`master`/`main` 保护分支、禁止 `--no-verify` 绕过 hook。

## 7. 国际化（i18n）信号（决定 Hard constraints）

- 配置：`i18next.config.js/.ts`、`next-i18next.config.js`、`i18n.ts`、`vue-i18n`、`lingui.config.js`、`next-intl`。
- 资源目录：`messages/`、`locales/`、`translations/`、`i18n/`、`public/locales/` 下的 `*.json` / `*.po` / `*.yaml`。
- 依赖：`i18next` / `react-i18next` / `vue-i18n` / `@lingui/core` / `next-intl` / `formatjs`（查 `package.json`）。
- 命中 → **必须**写 **Hard constraints**：「禁止硬编码中/英文字符串，所有用户可见文案走 i18n 函数（`t('key')` / `<Trans>` / `intl.formatMessage`）」；标注默认语言与资源目录位置，防 AI 在组件里直接写死文案。

> 扫描完上述 7 类信号，再进入 `02-output-template.md` 草拟。信号不全 → 宁可标注「需核实」，不臆造。
