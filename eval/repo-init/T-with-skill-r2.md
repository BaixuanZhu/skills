# repo-init 带 skill 产出（v1.4.0-r2）

> 执行方式：严格按 `skills/repo-init/SKILL.md` 流程 + `references/01~05` 逐场景落盘。四个仓库为同一 codebase（demo-cli）的四种状态，位于 `tmp/repo-init-eval/with/`，与 `eval/repo-init/fixtures/` 逐字节一致。
> **前提偏差记录**：评测说明称「fixture 是英文项目（英文 README/pyproject）」——实际四仓库 README、模块 docstring、CLAUDE.md 正文**全部为中文**（已验证 fixtures 与 tmp 副本 diff 为空）。按 `02-output-template.md` 语言规则（正文与 README / 代码注释一致），正文以**中文**产出（section 主标题按 `02` 建议用英文，工具解析更稳）。此偏差不影响本版两条新规则的验证，语言规则本身按实际信号执行。

---

## T1 · demo-cli（Path A 冷启动初始化）

- **象限**（`05` 决策矩阵）：AGENTS.md 无 + CLAUDE.md 无 → **Path A 冷启动**。
- **扫描信号**（`01` §1/§2/§4）：`pyproject.toml`（Python ≥3.10、setuptools、dev=`pytest>=7.0`、`testpaths=["tests"]`）；无 CI / 无 linter / 无 i18n / 非 monorepo / 非安全敏感项目。
- **关键决策**：
  - 命令从构建文件/README 实际提取（C2、强约束 5）：`pip install -e .`、`python -m demo_cli.main --input data.csv --output report.txt`、`pytest`，全部可验证。
  - 无 CI/lint/monorepo/安全信号 → 按强约束 8 省略 Architecture / Security / PR instructions 段，自然落短。
  - 红线识别（`01` §6 + `03` §8）：`tests/test_main.py` 直接 `from demo_cli.main import summarize` 并按签名调用 → 「禁止修改 `summarize` 函数签名」作为 **Hard constraints 独立成行**。
  - 语言：正文中文，与 README / 代码注释一致（`02` 语言规则）。
- **落盘**：`tmp/repo-init-eval/with/demo-cli/AGENTS.md`（32 行）。不 commit（强约束 6）。

```markdown
# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表（行数与金额合计）。
技术栈：Python 3.10+、setuptools、pip；无运行时依赖，测试用 pytest。

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`

## Code style

- 每个模块文件以 docstring 开头，说明模块用途（本仓库用中文写）
- 命令行参数用 argparse（`src/demo_cli/main.py` 当前实现）

## Hard constraints

- 禁止修改 `summarize` 函数签名（`tests/test_main.py` 直接 `from demo_cli.main import summarize` 并按当前签名调用，改动即破坏测试）
- 输入 CSV 必须为 UTF-8（代码以 `encoding="utf-8"` 读取，非 UTF-8 会抛 `UnicodeDecodeError`）

## Known gotchas

- `csv.DictReader` 依赖表头含 `amount` 列，缺列时 `summarize` 抛 `KeyError`；金额须可转 `float`
- 输入文件路径错误或列格式非法时无友好提示，直接抛异常

## Testing instructions

- 运行 `pytest`（`pyproject.toml` 已配置 `testpaths = ["tests"]`）
- 测试直接调用 `summarize`，改动需保证 `test_summarize_empty`、`test_summarize_basic` 通过
```

---

## T2 · demo-cli-migrate（仅 CLAUDE.md → 迁移）

- **象限**（`05` 矩阵第 2 行）：AGENTS.md 无 + CLAUDE.md 有**实质内容** → **迁移**。
- **关键决策**：
  - `05` 迁移 5 步：读全文（无 `@import` 链）→ 三路分流（项目事实全进 AGENTS.md；无 Claude 专属指令；无状态类内容）→ 无冲突 → 写 stub → 自查（stub 零内容、import 行 `@AGENTS.md` 相对同目录、未反引号包裹）。
  - **红线提升**：CLAUDE.md 原把「不允许直接改 summarize 函数签名」写在叙述性的「注意事项」里 → 按 `03` §8 提升为 **Hard constraints 独立成行**（附破坏原因）。
  - C4 自查：AGENTS.md 无任何工具专属语法；stub 不含项目事实副本。
- **落盘**：
  - `tmp/repo-init-eval/with/demo-cli-migrate/AGENTS.md`（30 行）
  - `tmp/repo-init-eval/with/demo-cli-migrate/CLAUDE.md`（降为 `@AGENTS.md` 单行 stub，原文件保留，见 `05` §边界）

```markdown
# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表（行数与金额合计）。
技术栈：Python 3.10+、setuptools、pip；无运行时依赖，测试用 pytest。

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`

## Code style

- 模块 docstring 必须存在
- 命令行参数用 argparse，不用 click

## Hard constraints

- 禁止修改 `summarize` 函数签名（`tests/test_main.py` 直接导入并调用，改动即破坏测试）
- 输入 CSV 必须为 UTF-8（代码以 `encoding="utf-8"` 读取，非 UTF-8 会抛 `UnicodeDecodeError`）

## Known gotchas

- `csv.DictReader` 依赖表头含 `amount` 列，缺列时 `summarize` 抛 `KeyError`；金额须可转 `float`

## Testing instructions

- 运行 `pytest`（`pyproject.toml` 已配置 `testpaths = ["tests"]`）
```

```markdown
@AGENTS.md
```

---

## T3 · demo-cli-dup（双源去重）

- **象限**（`05` 矩阵第 4 行）：AGENTS.md 有实质内容 + CLAUDE.md 有实质内容 → **双源去重**。
- **关键决策**：
  - 逐项比对：CLAUDE.md 的项目事实（overview/命令/docstring/argparse/CSV UTF-8/summarize）在 AGENTS.md 中**全部已覆盖** → 无新增事实；独有项仅「Claude Code 里结构性改动前默认先启用 plan mode」→ **Claude 专属，留 stub `## Claude Code` 小节，不进 AGENTS.md**（`05` 三路分流、强约束 4）。
  - **冲突裁决**（`05` §冲突裁决 + C2）：AGENTS.md 写 `pytest -v`（附臆造注「全量测试用 -v 输出」），CLAUDE.md/README/pyproject 均为 `pytest` → 以构建文件/README 真实信号为准，修订为 `pytest`，并在 Setup 中留一行裁决依据。
  - 用户有效内容（Hard constraints 两条、Known gotchas）原样保留（Path B 不整份覆盖，`03` §12）。
- **落盘**：
  - `tmp/repo-init-eval/with/demo-cli-dup/AGENTS.md`（25 行）
  - `tmp/repo-init-eval/with/demo-cli-dup/CLAUDE.md`（stub + Claude 专属小节）

```markdown
# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表。技术栈：Python 3.10+、pip。

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`（冲突裁决：原 AGENTS.md 写 `pytest -v`，与 README/CLAUDE.md/pyproject 的真实信号 `pytest` 不符，按构建文件为准）

## Code style

- 模块 docstring 必须存在
- 命令行参数用 argparse

## Hard constraints

- 禁止修改 `summarize` 函数签名（`tests/test_main.py` 直接导入并调用，改动即破坏测试）
- 输入 CSV 必须为 UTF-8（非 UTF-8 会抛 `UnicodeDecodeError`）

## Known gotchas

- CSV 非 UTF-8 编码会抛 `UnicodeDecodeError`
```

```markdown
@AGENTS.md

## Claude Code

- 结构性改动前默认先启用 plan mode
```

---

## T4 · demo-cli-stub（Path B 增量 + stub 幂等）

- **象限**（`05` 矩阵第 5 行）：AGENTS.md 有 + CLAUDE.md **已是 stub**（首行 `@AGENTS.md`）→ **Path B 增量；stub 不动（幂等，禁止二次追加）**。
- **关键决策**：
  - Path B 逐 section 标注（`02` §Path B）：overview / setup / code style / Hard constraints 🟢 仍准确 → 原样保留用户内容；🟡 缺失 → 补 `Known gotchas`（CSV UTF-8、`amount` 列，均从代码 `encoding="utf-8"` 与 `r["amount"]` 实测信号取得）与官方 5 section 中的 `Testing instructions`（`testpaths=["tests"]`，从 pyproject 提取）。
  - Git 增量（`01` §0 铁律 6）：fixture 目录在父仓库下未跟踪，无逐文件变更面可用 → 退化为对 5 个小文件的全量定向重扫，成本可忽略。
  - **stub 幂等**：`CLAUDE.md` 保持 `@AGENTS.md` 原样，未重写、未二次追加任何内容（`05` 矩阵第 5 行 + 强约束 1）。
- **落盘**：
  - `tmp/repo-init-eval/with/demo-cli-stub/AGENTS.md`（28 行）
  - `tmp/repo-init-eval/with/demo-cli-stub/CLAUDE.md`（未改动，仍为 `@AGENTS.md`）

```markdown
# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表。技术栈：Python 3.10+、pip。

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`

## Code style

- 模块 docstring 必须存在

## Hard constraints

- 禁止修改 `summarize` 函数签名（`tests/test_main.py` 直接导入并调用，改动即破坏测试）

## Known gotchas

- 输入 CSV 必须为 UTF-8（代码以 `encoding="utf-8"` 读取，非 UTF-8 会抛 `UnicodeDecodeError`）
- `csv.DictReader` 依赖表头含 `amount` 列，缺列时 `summarize` 抛 `KeyError`；金额须可转 `float`

## Testing instructions

- 运行 `pytest`（`pyproject.toml` 已配置 `testpaths = ["tests"]`）
```

---

## 回归结论

| 场景 | 路径/象限 | 落盘 | 行数 |
|------|-----------|------|------|
| T1 | Path A 冷启动 | demo-cli/AGENTS.md | 32 |
| T2 | 仅 CLAUDE.md → 迁移 | demo-cli-migrate/{AGENTS.md, CLAUDE.md stub} | 30 |
| T3 | 双源去重 | demo-cli-dup/{AGENTS.md, CLAUDE.md stub} | 25 |
| T4 | Path B 增量 + stub 幂等 | demo-cli-stub/AGENTS.md（CLAUDE.md 未动） | 28 |

全部 ≤ 150 行目标；命令均从构建文件/README 提取（C2 通过）；无工具专属 hack 进 AGENTS.md（C4 通过）；未自动 commit（强约束 6）。

**新规则 1（正文使用团队工作语言）——已生效。** 证据：T1 AGENTS.md 正文以中文书写，与 README「一个 Python CLI 工具…」及模块 docstring 完全一致（`02` 规则：与 README/代码注释一致）；注意评测说明「英文项目」前提与实际 fixture（中文）不符，按实际信号执行中文，规则本身正确。
**新规则 2（红线必须进 Hard constraints 独立成行）——已生效。** 证据：T2 CLAUDE.md 原文把「不允许直接改 summarize 函数签名」写在叙述性「注意事项」里，迁移后提升为 AGENTS.md `## Hard constraints` 下独立一行（`03` §8 反例规避）；T1/T3/T4 同样在 Hard constraints 独立成行，未混入 Architecture/叙述段。
