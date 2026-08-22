# repo-init 盲评报告

> 评审角色：独立盲评员（未参与任何一方产出）
> 评审对象：基线（不带 skill，`T-baseline.md`）vs 带 skill（`T-with-skill.md`）
> 测试定义：`test-prompts-v1.4.0.json`（T1 冷启动 / T2 仅 CLAUDE.md 迁移 / T3 双源去重 / T4 stub 幂等）
> 技能基准：`skills/repo-init/SKILL.md` + `references/01~05`
> 命令真实性已对照 `eval/repo-init/fixtures/` 全部源码与构建文件逐条验证

---

## 一、总体结论表

### 分维度得分（0-100）

| 场景 | 维度 | 基线 | 带 skill |
|---|---|---|---|
| **T1 冷启动** | 迁移/生成正确性 | 95 | 98 |
| | 单一事实源 | 100 | 100 |
| | 非覆盖原则 | 100 | 100 |
| | 命令真实性 | 100 | 100 |
| | stub 规范性 | 100 | 100 |
| | 幂等性 | 90 | 92 |
| | 信息密度与行数 | 88 | 95 |
| | 决策质量 | 90 | 96 |
| | **场景均值** | **95.4** | **97.6** |
| **T2 迁移** | 迁移/生成正确性 | 95 | 98 |
| | 单一事实源 | 96 | 98 |
| | 非覆盖原则 | 95 | 96 |
| | 命令真实性 | 100 | 100 |
| | stub 规范性 | 98 | 100 |
| | 幂等性 | 90 | 92 |
| | 信息密度与行数 | 90 | 93 |
| | 决策质量 | 92 | 96 |
| | **场景均值** | **94.5** | **96.6** |
| **T3 双源去重** | 迁移/生成正确性 | 93 | 96 |
| | 单一事实源 | 95 | 98 |
| | 非覆盖原则 | 92 | 94 |
| | 命令真实性 | 100 | 100 |
| | stub 规范性 | 95 | 100 |
| | 幂等性 | 88 | 90 |
| | 信息密度与行数 | 90 | 93 |
| | 决策质量 | 90 | 96 |
| | **场景均值** | **92.9** | **95.9** |
| **T4 stub 幂等** | 迁移/生成正确性 | 90 | 96 |
| | 单一事实源 | 95 | 98 |
| | 非覆盖原则 | 85 | 100 |
| | 命令真实性 | 100 | 100 |
| | stub 规范性 | 100 | 100 |
| | 幂等性 | 92 | 98 |
| | 信息密度与行数 | 90 | 95 |
| | 决策质量 | 88 | 96 |
| | **场景均值** | **92.5** | **97.9** |

### 总体均值

| 方 | 总均值 |
|---|---|
| 基线（不带 skill） | **93.8** |
| 带 skill | **97.0** |

带 skill 总体领先 **+3.2 分**。差距主要集中在：T4（+5.4，非覆盖原则 85 vs 100）、T3（+3.0，决策质量与 stub 规范性）、T1（+2.2，信息密度）。

---

## 二、逐场景差异分析

### T1 · 冷启动初始化（demo-cli/）

**基线做了什么**：直接基于 README + pyproject + 源码生成 AGENTS.md，6 段结构（Overview / Setup / Project layout / Code style / Constraints / Testing notes）。从源码归纳出 UTF-8 编码硬约束与 summarize 签名约束，命令与 pyproject 完全一致。约 45 行。

**带 skill 做了什么**：走 Path A 流程，7 段结构（Overview / Setup / Code style / Architecture / Hard constraints / Known gotchas）。gotchas 含两条源码实测信号（UTF-8 硬编码、`--input/--output` 必填）；Architecture 讲数据流（argparse → DictReader → summarize → UTF-8 写出）而非文件树；Overview 指出「无运行时第三方依赖」。约 30 行。

**各自得失**：
- 基线得：识别源码级约束准确；Testing notes 与命令回归提示有实用价值。失：Project layout 罗列文件树（触 03 §6 反模式边缘）；`--input/--output` 必填这条实测信号未进 gotchas。
- 带 skill 得：信息密度更高、gotchas 更全、Hard constraints 聚焦真正红线，符合强约束 8「无信号不写空段」。失：summarize 签名约束被表述为 Architecture 中的「稳定接口」而非 Hard constraints 红线，对「改动签名」的防护强度依赖读者推断。

### T2 · 仅 CLAUDE.md → 迁移（demo-cli-migrate/）

**基线做了什么**：把 CLAUDE.md 全部要点（概述/命令/docstring/不用 click/UTF-8/summarize 签名）迁入新 AGENTS.md，CLAUDE.md 覆盖为一行 `@AGENTS.md` stub，并显式说明「考虑 Claude Code 只读 CLAUDE.md」这一事实。

**带 skill 做了什么**：按 05 迁移 5 步执行——读全文（无 import 链）、三路分流（无 Claude 专属内容 → stub 按模板「无则整节省略」，仅留引用行）、无冲突、写 stub、四条自查；明确不删除 CLAUDE.md 文件本身。

**各自得失**：
- 基线得：方案正确、信息完整。失：无 Architecture 数据流叙述；stub 未显式走模板自查。
- 带 skill 得：流程显式化，产出的 AGENTS.md 多了 Architecture 段（数据流），gotchas 有出处标注；stub 严格符合模板。失：差异仅在细节润色，无实质增量。

### T3 · 双源去重（demo-cli-dup/）

**基线做了什么**：冲突盘点完整（`pytest -v` vs `pytest` 以 pyproject 为准裁决取 `pytest`、Code style 取完整版、CSV-UTF-8 重复合并、plan mode 信息泛化保留）。将 Claude 特有的 plan mode 指令**泛化**为「结构性改动前先输出改动计划并征得确认」写入 AGENTS.md 的 Working process 段。

**带 skill 做了什么**：冲突裁决同基线（pyproject 无 `addopts` 佐证 `-v` → 取 `pytest`），去重同基线；但 plan mode 指令按 05 三路分流判为 **Claude 专属 → 留在 stub 的 `## Claude Code` 小节，不进 AGENTS.md**（C4 工具无关）。

**各自得失**：
- 基线得：冲突裁决依据扎实；plan mode 泛化后所有工具均可读该约定。失：从技能设计看，Claude 专属内容进入 AGENTS.md 正文偏离 05「Claude 专属留 stub」的规定，弱化了工具无关性；且 stub 仅一行 `@AGENTS.md`，plan mode 指令的 Claude Code 可达性依赖 import 机制。
- 带 skill 得：严格符合 05 三路分流与 C4，AGENTS.md 保持纯项目事实，stub 规范（`@AGENTS.md` 首行 + Claude Code 专属小节、无项目事实副本）。失：丢弃「-v 可作可选提示」的等价说明（裁决正确，但 `-v` 本身并非错误命令，信息保留上略激进）。

### T4 · stub 幂等（demo-cli-stub/）

**基线做了什么**：CLAUDE.md stub 保持不动；对 AGENTS.md 做「覆盖为优化后版本」——保留全部原内容并追加 Code style 补充、Known gotchas、Project layout、Testing notes。声明重复执行不会再有变更。

**带 skill 做了什么**：严格 Path B 增量 diff——逐 section 三类标注（🟢 保留用户手写全部内容 / 🟡 缺失 Known gotchas / 🔴 无），只追加两条源码实测 gotchas（CSV UTF-8、`--input/--output` 必填），**绝不整份覆盖**；CLAUDE.md 已为 stub → 完全不动并显式验证幂等。

**各自得失**：
- 基线得：补齐内容更激进（含 layout/testing notes），本次无信息丢失。失：手法是**全量重写**而非增量追加，破坏技能强约束 2（03 §11 反模式）；在含用户手写上下文的真实仓库中，重写存在丢失「人脑上下文」的结构性风险——本次恰好全部保留了原内容，纯属侥幸。
- 带 skill 得：最符合技能意图，克制追加、密度更高，非覆盖与幂等均有显式执行与验证。失：无（T4 带 skill 全面占优）。

---

## 三、明确判定

**带 skill 相比基线有实质增量的场景：**

1. **T4（+5.4）**——差异最大。基线用「全量重写」手法更新已有 AGENTS.md，带 skill 严格 diff 追加、验证 stub 幂等。非覆盖原则 85 vs 100，是全部维度中最大的单项分差。
2. **T3（+3.0）**——决策质量分水岭。对 Claude 专属 plan mode 的处置：基线泛化进 AGENTS.md，带 skill 按 05 正确分流至 stub 的 Claude Code 小节，AGENTS.md 保持工具无关。
3. **T1（+2.2）**——信息密度与 gotchas 完整度：带 skill 多一条源码实测 gotcha（`--input/--output` 必填），Architecture 叙述优于文件树，行数更少。

**带 skill 相比基线无明显差异的场景：**

1. **T2（+2.1，同质）**——两者迁移结果实质趋同：内容完整迁入 AGENTS.md、CLAUDE.md 降为一行 `@AGENTS.md` stub、命令一致。带 skill 只是流程显式化 + Architecture 段润色，不构成方法论层面的增量。T2 也是基线表现最接近技能设计的场景——说明「Claude Code 只读 CLAUDE.md、单一事实源放 AGENTS.md + stub 引用」这一核心认知，不带 skill 也能凭通用知识达成。

**判语**：带 skill 的增量不在于「生成质量」而在于「过程纪律」——非覆盖、Claude 专属分流、stub 幂等这三类约束，恰好是基线在 T3/T4 暴露认知缺口的地方（T4 全量重写、T3 工具专属内容入正文）。生成命令与迁移方案本身，基线质量已相当高。

---

## 四、Top 问题清单（带 skill 产出的残留缺陷）

1. **summarize 签名约束跨场景表述不一致**：T1 放 Architecture「稳定接口」、T3/T4 放 Hard constraints——对「改动签名即破坏测试」这一红线，T1 的防护强度被弱化，依赖读者自行推断。建议统一进 Hard constraints。
2. **T3 对 `-v` 信息处置过激进**：裁决取 `pytest` 正确，但 `-v` 非错误命令，可在 Setup 注释保留「非默认可选」等价说明（基线做到了），避免信息净损失。
3. **过程性标注入正文**：AGENTS.md 中出现「迁移自原 CLAUDE.md」「pyproject.toml 实测」等出处标注，属轻量噪音，与「纯项目事实、无状态」的理想状态有微小偏离。
4. **无用户交互记录**：05 要求冲突项「列 diff 给用户裁决」，评估为单次非交互执行故无法体现；真实使用中须注意克制询问与自主裁决的边界。
5. **技能文档层面（非产出）**：SKILL.md 同时维护判定表/检查点/反模式/铁律四套规则，对小规模仓库存在叠加冗余——带 skill 执行者自评亦承认（01 Token 经济学铁律对 4~5 文件仓库边际价值低）。属技能可优化项。

---

## 附：命令真实性核查记录（两份产出均无臆造）

| 命令 | 验证依据 | 结果 |
|---|---|---|
| `pip install -e .` | pyproject `build-backend = setuptools.build_meta` | 真实 |
| `python -m demo_cli.main --input data.csv --output report.txt` | main.py `if __name__ == "__main__"` 桥接 | 真实 |
| `pytest` | pyproject `[tool.pytest.ini_options].testpaths = ["tests"]` | 真实 |
| T3 裁决 `pytest` 弃 `pytest -v` | pyproject 无 `addopts`，`-v` 无构建文件佐证 | 裁决正确 |
| UTF-8 约束 | main.py:20 `open(..., encoding="utf-8")` 硬编码 | 真实 |
| `--input/--output` 必填 | main.py:16-17 `required=True` | 真实 |
