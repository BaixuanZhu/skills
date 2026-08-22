# repo-init 盲评报告（v1.4.0-r2 回归）

> 评审角色：独立盲评员（未参与任何一方产出，与 r1 盲评同一立场）
> 评审对象：r2 带 skill 产出（`T-with-skill-r2.md`）vs r1 带 skill 产出（`T-with-skill.md`，对照）
> 测试定义：`test-prompts-v1.4.0.json`（T1 冷启动 / T2 迁移 / T3 双源去重 / T4 stub 幂等）
> 技能基准：`skills/repo-init/SKILL.md` + `references/01~05`（重点 `02` 语言规则、`03` §8、`05` 迁移）
> 本轮验证目标：R1 语言规则（正文与 README/代码注释一致）、R2 红线规则（红线进 Hard constraints 独立成行）
> 命令真实性已对照 `eval/repo-init/fixtures/` 逐条验证

---

## 一、R2 规则验证：summarize 签名红线是否进 Hard constraints 独立成行

**判定：生效（缺陷已修复）。** 逐场景证据：

| 场景 | r1（缺陷版） | r2 | 证据（r2 落盘） |
|---|---|---|---|
| T1 | ❌ 写进 Architecture 第 33 行「summarize 是…稳定接口」，Hard constraints 只有 CSV-UTF-8（r1 Top 问题 #1） | ✅ Hard constraints 独立成行 | L40「禁止修改 `summarize` 函数签名（`tests/test_main.py` 直接 `from demo_cli.main import summarize` 并按当前签名调用，改动即破坏测试）」 |
| T2 | ✅ 已在 Hard constraints（L73） | ✅ 独立成行 + **显式记录「红线提升」** | L61「CLAUDE.md 原把…写在叙述性的『注意事项』里 → 按 `03` §8 提升为 Hard constraints 独立成行（附破坏原因）」；L88 落盘 |
| T3 | ✅ 已在 Hard constraints（L119） | ✅ 独立成行（保留用户原内容） | L137 |
| T4 | ✅ 已在 Hard constraints（L162） | ✅ 独立成行 | L185 |

要点：
- **T1 是本轮关键修复点**。r1 盲评 Top 问题 #1 正是指 T1 该红线未独立成行、防护依赖推断；r2 T1 已进 Hard constraints，且带破坏原因（测试直接 import 并按当前签名调用），完全命中 `03` §8 的「✓ 正确做法」示例（「禁止改 summarize 函数签名，测试依赖它」）。
- T2 是 R2 规则在**迁移路径**上生效的最强证据：源 CLAUDE.md（fixture）确把该约束写在叙述性「注意事项」段（`demo-cli-migrate/CLAUDE.md:21`），r2 显式记录「提升」动作并落盘独立行——不是碰巧，而是规则被显式执行。
- 附加验证：`03` §8 反例描述（「签名约束写进 Architecture 的『稳定接口』后防护失效」）与 r1 T1 的失误逐字对应，说明 R2 正是针对 r1 实测缺陷设计的修复规则，且已闭环。

---

## 二、R1 规则验证：正文语言与 README/代码注释一致 + 决策显式记录

**判定：生效，且为显式遵循（优于 r1 的隐式默认）。**

证据链：
1. **fixture 实际语言**（已逐仓验证）：四个仓库 README 首行均为「一个 Python CLI 工具，从 CSV 文件生成汇总报表。」（中文）；`main.py:1` docstring「demo-cli: 从 CSV 生成汇总报表。」（中文）；`test_main.py:1`「demo_cli 主入口测试。」（中文）；CLAUDE.md 全中文。→ 团队工作语言 = 中文。
2. **r2 产出语言**：T1~T4 的 AGENTS.md 正文全中文，section 主标题用英文（Project overview / Setup commands…）——完全符合 `02` 语言规则「正文使用团队工作语言（与 README/代码注释一致）；section 主标题建议英文（工具解析更稳）」。
3. **显式记录**：r2 在两处显式落记录语言决策——头部「前提偏差记录」（明确按 `02` 规则以中文产出，并说明与「评测说明」宣称的英文项目前提不符）与回归结论第 210 行（「与 README『一个 Python CLI 工具…』及模块 docstring 完全一致」）。r1 正文同样是中文，但**未记录语言决策**，属隐式默认。本轮 r2 显式化，规则执行可验证。
4. 反事实检验：若 fixture 真为英文项目，规则要求写英文——r2 是按**实际信号**（中文）而非按评测预期（英文）执行，恰恰证明规则被遵循而非被猜测迎合。

---

## 三、整体回归：r2 是否引入新问题

**无功能性新问题。** 四项既有纪律复核通过：
- **stub 规范**：T2 单行 `@AGENTS.md`；T3 `@AGENTS.md` + `## Claude Code`（plan mode 属 Claude 专属，正确留 stub 不进 AGENTS.md，符合 `05` 三路分流与强约束 4）；T4 stub 未动（幂等，显式验证）。全部符合 `05` 模板与四条自查。
- **命令真实性**（对照 fixture 验证）：`pip install -e .`（setuptools backend）、`python -m demo_cli.main --input data.csv --output report.txt`（`if __name__ == "__main__"` 桥接）、`pytest`（`testpaths=["tests"]`）全部真实；T3 冲突裁决 `pytest -v`→`pytest` 依据正确（pyproject 无 addopts）。未自动 commit（强约束 6）。
- **非覆盖/幂等**：T4 Path B 增量补段、CLAUDE.md 不动；T3 用户有效内容原样保留。
- **无 CI/lint/安全信号 → 省略对应段**（强约束 8）执行一致。

三个观察点（非阻塞，详见 Top 问题）：
1. T1 丢失了 r1 有过的 `--input/--output required=True` gotcha（`main.py:16-17` 实测信号，r1 盲评曾记为加分项），换为「amount 列 / 无友好提示」两条——信息密度相对 r1 轻微回退。
2. T3 的 CSV-UTF-8 在 Hard constraints 与 Known gotchas 双处保留（r1 做了去重）。因 fixture 原 AGENTS.md 本就两处皆有，属 Path B「保留用户内容」的取舍，非错误，但冗余仍在。
3. 头部「评测说明称 fixture 是英文项目」的前提声明在本轮材料（test-prompts JSON / fixtures / 上轮报告）中无法溯源——不改变规则执行正确性（实际 fixture 确为中文、中文产出正确），但该引用建议补出处或删除，以免评审无法复核。

---

## 四、r2 vs r1 关键差异表

| 维度 | r1（v1.4.0） | r2（v1.4.0-r2） | 评价 |
|---|---|---|---|
| R2：T1 summarize 红线位置 | Architecture「稳定接口」 | Hard constraints 独立成行 | **缺陷修复**（r1 Top #1 闭环） |
| R2：T2 红线提升动作 | 未显式标注（默认带入） | 显式记录「叙述→Hard constraints 提升」 | r2 更可审计 |
| R1：语言决策记录 | 正文中文，未记录决策（隐式） | 正文中文 + 前置偏差记录 + 回归结论双重记录（显式） | **r2 显式遵循规则** |
| T1 Architecture 段 | 有（数据流叙述） | 无（强约束 8 省略，自然落短） | 设计取舍，均合规 |
| T1 gotchas 完整性 | 含 `--input/--output` 必填 | 不含（换 amount 列/无友好提示） | r2 轻微信息回退 |
| T3 CSV-UTF-8 冗余 | 去重（仅 gotchas） | 双处保留（Path B 保留用户内容） | 取舍不同，均自洽 |
| 规则自证 | 结尾点评 3 条（无新规则验证） | 新增 R1/R2 两条「已生效」结论 + 证据 | r2 更面向回归验证 |

---

## 五、整体判定

**v1.4.0-r2 相比 r1 是明确进步，两条新规则均真实生效：**

1. **R2 已生效**：r1 实测缺陷（T1 红线藏进 Architecture）被精准修复，四场景 summarize 红线全部在 Hard constraints 独立成行且带破坏原因；T2 迁移路径上红线从叙述段「提升」为独立行被显式记录，证明规则在非冷启动路径同样被执行。
2. **R1 已生效且显式化**：正文按 fixture 实际语言（中文）产出，与 README/代码注释一致；语言决策被显式记录（r1 仅隐式），且按实际信号而非评测预期执行，规则遵循可验证。

**仍需修的缺陷（均轻微，不阻塞发布）：**
1. T1 恢复 `--input/--output required=True` gotcha，与 r1 信息密度持平（源码信号真实存在，非取舍问题）。
2. AGENTS.md 正文内的过程性标注（T3 Setup 冲突裁决注、T1 Code style「本仓库用中文写」括注）属 r1 Top #3 同类噪音，建议移入报告/推理而非正文。
3. T3 CSV-UTF-8 双处冗余，建议保留一处（或在 Path B 时明确「去重」动作）。
4. 「评测说明称英文项目」前提引用无法溯源，建议补出处或删除。

---

## 六、各场景简评

- **T1（冷启动）**：R2 修复生效（summarize 独立成行，本轮核心）；R1 中文一致；命令真实；省 Architecture 合理。失：丢 `--input/--output` 必填 gotcha。
- **T2（迁移）**：本轮最强证据场景——红线提升动作显式记录且落盘正确，stub 单行规范，与 r1 的正确做法一致并补上「提升」的可审计性。
- **T3（双源去重）**：冲突裁决正确（`pytest` 弃 `-v`）、plan mode 正确留 stub 不污染 AGENTS.md；CSV-UTF-8 双处保留为路径取舍。失：内联裁决注属正文噪音。
- **T4（stub 幂等）**：CLAUDE.md 未动 + 显式验证幂等，Path B 增量补段正确，Hard constraints 红线独立成行——r1 的优势项无回退。
