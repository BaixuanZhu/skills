# repo-init 基线对照产出（不带 skill）

> 对照组：无任何 skill / 参考文档，仅凭通用知识处理 4 个真实场景。
> 处理对象：`I:\GitDownload\skills\tmp\repo-init-eval\base\` 下 4 个仓库。
> 基线事实（判断依据）：Claude Code 主要读取 `CLAUDE.md`（仅保留 `@AGENTS.md` 引用 stub 时通过 import 语法读取 AGENTS.md）；而 Cursor / Codex / 多数 AI 工具只读取 `AGENTS.md`。因此「单一事实源放 AGENTS.md + CLAUDE.md 保留 `@AGENTS.md` 引用」是同时满足「所有工具可读」与「Claude Code 兼容」的最小方案。

---

## T1 冷启动初始化（demo-cli/）

**场景说明**：仓库无 AGENTS.md、无 CLAUDE.md，需从零生成一份 AGENTS.md。可依据的材料：README.md（安装/运行/测试命令）、pyproject.toml（Python 3.10+、pytest、testpaths）、src/demo_cli/main.py（argparse 入口、`encoding="utf-8"` 显式读 CSV）、tests/test_main.py（summarize 行为）。

**决策**：直接基于代码与配置推导生成 AGENTS.md，不臆造内容。结构采用「项目概述 / 命令 / 布局 / 代码规范 / 约束 / 测试注意」。从源码归纳出两处仅看 README 得不到的约束：CSV 必须 UTF-8（源码显式指定编码，非 UTF-8 会抛 UnicodeDecodeError）、不得改 summarize 签名（tests 直接 import 依赖其行为）。

**落盘文件**：`I:\GitDownload\skills\tmp\repo-init-eval\base\demo-cli\AGENTS.md`（新建）

```markdown
# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表（行数与 amount 列合计）。

- 语言：Python 3.10+
- 包管理：pip（setuptools，`pip install -e .`）
- 测试框架：pytest（testpaths = `tests`）

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`

## Project layout

- `src/demo_cli/main.py`：CLI 入口与 `summarize()` 核心逻辑
- `tests/test_main.py`：pytest 单测

## Code style

- 模块必须有 docstring
- CLI 参数用 argparse（`--input` / `--output` 均为必填）
- 文件读写统一显式指定 `encoding="utf-8"`

## Constraints

- 不要改动 `src/demo_cli/main.py` 中 `summarize` 的函数签名（tests 依赖其行为）
- 输入 CSV 必须为 UTF-8 编码，否则 `csv.DictReader` 读取会抛 `UnicodeDecodeError`

## Testing notes

- 修改 `summarize` 后须运行 `pytest` 回归（现有用例：空列表、金额累加）
```

---

## T2 仅 CLAUDE.md → 迁移（demo-cli-migrate/）

**场景说明**：仓库只有 CLAUDE.md（含实质内容），无 AGENTS.md。要求「让所有工具能读到项目说明」+「保持 Claude Code 兼容」。

**决策**：考虑了「Claude Code 只读 CLAUDE.md」这一事实。方案：① 把 CLAUDE.md 的实质内容整体迁入新 AGENTS.md（作为所有工具共读的事实源）；② CLAUDE.md 简化为一行 `@AGENTS.md` 引用 stub——Claude Code 仍能通过 import 语法读到完整项目说明，其余工具直接读 AGENTS.md。这样既不丢信息、又避免双份内容后续漂移。迁移时保留原 CLAUDE.md 的全部要点（概述、命令、docstring/argparse 不用 click、UTF-8、summarize 签名）。

**落盘文件**：
- `I:\GitDownload\skills\tmp\repo-init-eval\base\demo-cli-migrate\AGENTS.md`（新建）
- `I:\GitDownload\skills\tmp\repo-init-eval\base\demo-cli-migrate\CLAUDE.md`（覆盖为引用 stub）

AGENTS.md（新建）：

```markdown
# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表。

- 语言：Python 3.10+
- 包管理：pip（setuptools）
- 测试框架：pytest

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`

## Code style

- 模块必须有 docstring
- CLI 参数用 argparse，不用 click

## Constraints

- 输入 CSV 必须为 UTF-8 编码，否则会报 `UnicodeDecodeError`
- 不允许直接改 `src/demo_cli/main.py` 的 `summarize` 函数签名
```

CLAUDE.md（覆盖后全文）：

```markdown
@AGENTS.md
```

---

## T3 双源去重（demo-cli-dup/）

**场景说明**：AGENTS.md 与 CLAUDE.md 同时存在且都有实质内容，信息部分重叠且存在冲突。要求「单一事实源」+「Claude Code 兼容」。

**冲突/差异盘点**：
- 测试命令冲突：AGENTS.md 写 `pytest -v`，CLAUDE.md 写 `pytest`。以 pyproject.toml（`testpaths=["tests"]`、无 addopts）为准 → 默认 `pytest`，`-v` 降为可选提示。
- Code style 缺失：AGENTS.md 只写 argparse，CLAUDE.md 更完整（argparse、不用 click）→ 取完整版。
- 信息重复：AGENTS.md 把「CSV 必须 UTF-8」同时放进 Hard constraints 与 Known gotchas → 去重合并到一处。
- Claude 特有信息：CLAUDE.md 的「默认启用 plan mode 后再做结构性改动」→ 泛化保留进 AGENTS.md 的 Working process（stub 化后 CLAUDE.md 不再承载正文，不能丢弃）。

**决策**：同样考虑了「Claude Code 只读 CLAUDE.md」。合并成单一事实源 AGENTS.md（消解上述冲突/重复/缺失），CLAUDE.md 覆盖为 `@AGENTS.md` 引用 stub，保证 Claude Code 通过 import 仍读到全部内容——单一事实源与 Claude Code 兼容同时满足。

**落盘文件**：
- `I:\GitDownload\skills\tmp\repo-init-eval\base\demo-cli-dup\AGENTS.md`（覆盖为合并后版本）
- `I:\GitDownload\skills\tmp\repo-init-eval\base\demo-cli-dup\CLAUDE.md`（覆盖为引用 stub）

AGENTS.md（合并后全文）：

```markdown
# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表。

- 语言：Python 3.10+
- 包管理：pip（setuptools）
- 测试框架：pytest（testpaths = `tests`）

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`（需要详细输出时可加 `-v`）

## Code style

- 模块必须有 docstring
- CLI 参数用 argparse，不用 click

## Hard constraints

- 不允许直接改 `src/demo_cli/main.py` 的 `summarize` 函数签名
- 输入 CSV 必须为 UTF-8 编码，否则会报 `UnicodeDecodeError`

## Working process

- 结构性改动（如重构、改动入口/签名）前，先输出改动计划并征得确认后再动手
```

CLAUDE.md（覆盖后全文）：

```markdown
@AGENTS.md
```

---

## T4 stub 幂等（demo-cli-stub/）

**场景说明**：已有 AGENTS.md，CLAUDE.md 首行是 `@AGENTS.md` 引用 stub（已是正确引用形态）。任务是对项目上下文做一次「更新优化」。

**决策**：CLAUDE.md stub 已符合约定，保持不动（幂等——不重建、不改写 stub）。仅对 AGENTS.md 做增量完善，补齐当前缺失且可从代码推导的信息：
- Code style 补「argparse，不用 click」；
- 补 Known gotchas（CSV 必须 UTF-8，源码 `encoding="utf-8"` 显式指定）；
- 补 Project layout 与 Testing notes（便于后续 Agent 快速定位与回归）。
更新收敛、无破坏性改动，重复执行不会再次产生变更。

**落盘文件**：
- `I:\GitDownload\skills\tmp\repo-init-eval\base\demo-cli-stub\AGENTS.md`（覆盖为优化后版本）
- `I:\GitDownload\skills\tmp\repo-init-eval\base\demo-cli-stub\CLAUDE.md`（保持 `@AGENTS.md` 不动）

AGENTS.md（优化后全文）：

```markdown
# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表。

- 语言：Python 3.10+
- 包管理：pip（setuptools）
- 测试框架：pytest（testpaths = `tests`）

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`

## Project layout

- `src/demo_cli/main.py`：CLI 入口与 `summarize()` 核心逻辑
- `tests/test_main.py`：pytest 单测

## Code style

- 模块必须有 docstring
- CLI 参数用 argparse，不用 click
- 文件读写统一显式指定 `encoding="utf-8"`

## Hard constraints

- 不允许直接改 `src/demo_cli/main.py` 的 `summarize` 函数签名

## Known gotchas

- 输入 CSV 必须为 UTF-8 编码，否则 `csv.DictReader` 读取会抛 `UnicodeDecodeError`

## Testing notes

- 修改 `summarize` 后须运行 `pytest` 回归（现有用例：空列表、金额累加）
```

---

## 总结：各场景正确产出判断

- T1 正确产出：一份从代码+配置推导的 AGENTS.md（命令、规范、可从源码归纳的硬约束如 UTF-8 / summarize 签名），本产出基本达标。
- T2 正确产出：CLAUDE.md 实质内容迁入 AGENTS.md 作单一事实源，CLAUDE.md 降级为 `@AGENTS.md` 引用 stub（已考虑「Claude Code 只读 CLAUDE.md」），本产出符合。
- T3 正确产出：合并两文件为单一 AGENTS.md 事实源（按 pyproject 消解 `pytest` vs `pytest -v` 冲突、补齐「不用 click」、去重、保留 plan mode 信息），CLAUDE.md 降级为 `@AGENTS.md` stub，本产出符合。
- T4 正确产出：保持 `@AGENTS.md` stub 不变、只对 AGENTS.md 做幂等增量优化（补 gotchas/规范，不破坏结构），本产出符合。
