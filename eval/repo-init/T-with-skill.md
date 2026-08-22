# repo-init 带 skill 产出

> 评估方式：严格按 `skills/repo-init/SKILL.md` 主文件 + `references/01~05` 指引执行，对 4 个测试场景逐一落盘产出。评估员与 skill 无绑定，纯按文档执行。

## T1 · 冷启动初始化（demo-cli/）

- **路径 / 象限**：Path A 冷启动（C1 五象限矩阵「无 AGENTS.md 无 CLAUDE.md → Path A」，SKILL.md 检查点表）
- **关键决策**：
  - C2 命令真实（SKILL.md C2 + `01` §1/§2）：Install/Run/Test 从 pyproject.toml 与 README 实际提取——`pip install -e .`（setuptools build backend）、`python -m demo_cli.main`（源码 `if __name__ == "__main__"`）、`pytest`（`[tool.pytest.ini_options].testpaths`）。无 lock 文件→pip，未臆造。
  - 强约束 8（无信号不写空段）：无 CI/linter/i18n/安全敏感信号 → 省略 PR instructions / Security considerations / Testing instructions 独立段，自然落短（约 30 行）。
  - 强约束 7（无状态）：只写 must-know，无待办/进度。
  - C3（`04`）：单仓非 monorepo → 不嵌套；C4（工具无关）：无工具专属指令。
  - Known gotchas 两条来自源码实测（`encoding="utf-8"` 硬编码、argparse `required=True`），非 README 表面信息。
- **落盘**：`I:\GitDownload\skills\tmp\repo-init-eval\with\demo-cli\AGENTS.md`
- **产物全文**：
```markdown
# AGENTS.md

## Project overview
demo-cli 是一个 Python 3.10+ 命令行工具，从 CSV 输入文件生成汇总报表（条目数与金额合计）。无运行时第三方依赖，仅 dev 依赖 pytest（pyproject.toml 中 `[project.optional-dependencies].dev`）。

## Setup commands
- Install: `pip install -e .`（setuptools 构建后端，pyproject.toml 实测）
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`（`[tool.pytest.ini_options].testpaths = ["tests"]` 已配置）

## Code style
- 模块必须有 docstring（`src/demo_cli/main.py` 现状）
- 命令行参数用 argparse，入口约定 `main(argv=None)` + `if __name__ == "__main__"` 桥接

## Architecture
- `src/demo_cli/main.py`：argparse 解析必填 `--input/--output` → `csv.DictReader` 读取 → `summarize(rows)` 聚合 `{"count": int, "total": float}` → 写 UTF-8 输出文件
- `tests/test_main.py` 直接 `from demo_cli.main import summarize` 并断言返回结构，`summarize` 是该模块的可测核心/稳定接口

## Hard constraints
- 输入 CSV 读取硬编码 `open(..., encoding="utf-8")`：非 UTF-8 文件会抛 `UnicodeDecodeError`（见 Known gotchas）

## Known gotchas
- CSV 必须为 UTF-8 编码：main.py 第 20 行硬编码 `encoding="utf-8"`，非 UTF-8 输入直接报 `UnicodeDecodeError`
- `--input` 与 `--output` 均为必填（argparse `required=True`），缺少任一参数会在解析时直接退出
```

## T2 · 仅 CLAUDE.md → 迁移（demo-cli-migrate/）

- **路径 / 象限**：迁移路径（C1 矩阵「无 AGENTS.md、CLAUDE.md 有实质内容 → 迁移」，`05` 决策矩阵）
- **关键决策**：
  - 按 `05` 迁移 5 步执行：①读 CLAUDE.md 全文（无 `@import` 链，无需展开）→ ②三路分流：项目事实（概述/命令/代码规范/注意事项）全部进 AGENTS.md 对应 section；**无 Claude 专属内容**（无 hooks/plan mode/permissions）→ stub 按 `05` 模板「无则整节省略」，仅留一行引用；无状态类 → 无丢弃项。③无 AGENTS.md → 无冲突。④stub 首行 `@AGENTS.md` 相对路径。⑤四条自查通过。
  - `05` 边界：**不删除 CLAUDE.md 文件本身**——降级为适配指针 stub，Claude Code 仍可加载上下文。
  - 强约束 1：不生成第二份实质内容记忆，单一事实源 = AGENTS.md。
  - C2：命令与 pyproject.toml 交叉验证一致。
- **落盘**：`I:\GitDownload\skills\tmp\repo-init-eval\with\demo-cli-migrate\AGENTS.md`、`...\demo-cli-migrate\CLAUDE.md`（降 stub）
- **产物全文（AGENTS.md）**：
```markdown
# AGENTS.md

## Project overview
demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表。Python 3.10+、pip 安装、setuptools 构建后端，仅 dev 依赖 pytest。

## Setup commands
- Install: `pip install -e .`（迁移自原 CLAUDE.md，pyproject.toml 验证一致）
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`（pyproject.toml `testpaths = ["tests"]` 已配置）

## Code style
- 模块 docstring 必须存在
- 命令行参数用 argparse，不用 click

## Architecture
- `src/demo_cli/main.py`：argparse 解析 `--input/--output` → `csv.DictReader` → `summarize(rows)` 聚合（count/total）→ 写输出文件
- `tests/test_main.py` 直接导入并断言 `summarize` 返回结构，为稳定接口

## Hard constraints
- 不允许直接改 `src/demo_cli/main.py` 的 summarize 函数签名（迁移自原 CLAUDE.md）

## Known gotchas
- 输入 CSV 必须是 UTF-8：main.py 硬编码 `encoding="utf-8"`，非 UTF-8 会报 UnicodeDecodeError（迁移自原 CLAUDE.md）
```
**产物全文（CLAUDE.md stub）**：
```markdown
@AGENTS.md
```

## T3 · 双源去重（demo-cli-dup/）

- **路径 / 象限**：双源去重（C1 矩阵「两者皆有实质内容 → 双源去重」，`05` 决策矩阵）
- **关键决策**：
  - 独有内容并入：CLAUDE.md 独有的「plan mode 指令」按 `05` 三路分流属 **Claude 专属** → 进 stub `## Claude Code` 小节，**不进 AGENTS.md**（C4 工具无关 + `03` §2）。
  - 冲突裁决（`05` §3：默认以构建文件/CI 真实信号为准）：`pytest -v`（AGENTS.md）vs `pytest`（CLAUDE.md）→ pyproject.toml 无 `addopts` 佐证 `-v`，且 `testpaths` 已配置 → 裁决取 `pytest`，丢弃无佐证的「-v 全量」说明。
  - 重复去重：CSV-UTF-8 在 AGENTS.md 的 Hard constraints 与 Known gotchas 重复、CLAUDE.md 注意事项也有 → 只在 Known gotchas 保留一次（含报错机理），Hard constraints 去重。
  - 相同事实（overview / summarize 签名约束）各保留一次，未重复堆叠。
  - stub 校验（`05` 四条自查）：AGENTS.md 无工具专属语法；stub 只含 `@AGENTS.md` + Claude 专属小节，无项目事实副本；import 行无反引号、相对路径。
- **落盘**：`I:\GitDownload\skills\tmp\repo-init-eval\with\demo-cli-dup\AGENTS.md`、`...\demo-cli-dup\CLAUDE.md`（降 stub）
- **产物全文（AGENTS.md）**：
```markdown
# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表。技术栈：Python 3.10+、pip、setuptools。

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`（pyproject.toml `testpaths = ["tests"]` 已配置；原 AGENTS.md 的 "-v 输出" 无构建文件佐证，未采纳）

## Code style

- 模块 docstring 必须存在
- 命令行参数用 argparse，不用 click

## Architecture

- `src/demo_cli/main.py`：argparse 解析 `--input/--output` → `csv.DictReader` → `summarize(rows)` 聚合（count/total）→ 写 UTF-8 输出文件
- `tests/test_main.py` 直接导入并断言 `summarize` 返回结构，为稳定接口

## Hard constraints

- 不允许直接改 `src/demo_cli/main.py` 的 summarize 函数签名

## Known gotchas

- 输入 CSV 必须是 UTF-8：main.py 硬编码 `encoding="utf-8"`，非 UTF-8 会报 UnicodeDecodeError
```
**产物全文（CLAUDE.md stub）**：
```markdown
@AGENTS.md

## Claude Code
- 在 Claude Code 里默认启用 plan mode 后再做结构性改动
```

## T4 · stub 幂等 + 增量更新（demo-cli-stub/）

- **路径 / 象限**：Path B 增量更新（C1 矩阵「CLAUDE.md 已是 stub → Path B 且 stub 不动」，`05` 决策矩阵 + SKILL.md Path B）
- **关键决策**：
  - Git 增量铁律（`01` §0 铁律 6）：fixture 目录无独立 git 提交历史（属父仓库未跟踪副本）→ 无法 diff，回退为对小型仓库的有界全扫（无 node_modules/dist，成本极低）。
  - 逐 section 三类标注（Path B 步骤 2）：🟢 overview / Setup（Install·Run·Test 与 pyproject·README·源码全一致）/ Code style / Hard constraints 均仍准确，**用户手写内容全部保留**；🟡 缺失 Known gotchas——CSV UTF-8 硬编码报错、`--input/--output` 必填，均为源码实测信号；🔴 过期/失真：无。
  - 强约束 2：增量 diff 追加缺失段，**绝不整份覆盖**；未改动用户原有任何内容。
  - 幂等（`05` 决策矩阵末行）：CLAUDE.md 已是 `@AGENTS.md` stub → **完全不动**，不二次追加、不重写。
- **落盘**：`I:\GitDownload\skills\tmp\repo-init-eval\with\demo-cli-stub\AGENTS.md`（追加 Known gotchas）；`...\demo-cli-stub\CLAUDE.md`（未动）
- **产物全文（AGENTS.md 修订后）**：
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

- 不允许直接改 `src/demo_cli/main.py` 的 summarize 函数签名

## Known gotchas

- 输入 CSV 必须是 UTF-8：main.py 硬编码 `open(..., encoding="utf-8")`，非 UTF-8 会报 UnicodeDecodeError
- `--input` 与 `--output` 均为必填（argparse `required=True`），缺少任一参数会在解析时直接退出
```
**CLAUDE.md（未改动，验证幂等）**：
```markdown
@AGENTS.md
```

---

## 结尾点评（skill 指引中）

1. 最有价值：`05` CLAUDE.md 迁移「搬运 + 降级、不删除文件」——在维护单一事实源的同时保住 Claude Code 兼容，是同类技能最容易做错（直接删文件或双份并存）的环节。
2. 最有价值：Path B 增量 diff 三态标注（🔴🟡🟢）+ 强约束 2「绝不整份覆盖」——真实避免了更新时丢弃用户手写上下文与「推倒重来」式重写。
3. 最冗余：`01` Token 经济学 7 铁律对本类小型仓库（4~5 个文件）几乎无约束力，正常扫描本就廉价；文档还同时维护「判定表 + 检查点 + 反模式 + 铁律」四套规则，存在叠加，小项目执行时边际价值低。
