# AGENTS.md

This is a **skills development + distribution repository**. It authors, evaluates, and distributes "Agent Skills" (SKILL.md content packages) targeting Chinese Java/Spring ecosystems (Sa-Token, MyBatis-Plus, Java coding standards, agile workflows, etc.). There is no application to build, run, or deploy — the product is the skill *content* itself.

## Repository layout

- `skills/<name>/` — the skills. **This is the primary thing being edited.** Each has:
  - `SKILL.md` with YAML frontmatter (`name`, `description`, `version`, usually `slug` + `displayName`; agile skills also use `dependencies`).
  - `references/` — numbered `NN-topic.md`, count varies from 1 (agile-backlog) to 14 (sa-token-dev / mybatis-plus-dev).
  - sometimes `assets/` (e.g. java-coding-quality).
- `eval/<skill-name>/` — Darwin evaluation artifacts (test prompts, snapshots, scoring). Per-skill subdirs; commit artifacts here after evaluating. See `eval/README.md`.
- `.claude-plugin/` — Claude Code plugin marketplace manifests (`marketplace.json`; `plugin.json`). Each skill = one plugin entry.
- `README.md` — public-facing install guide (dual-protocol: Claude Code plugin + `npx skills`).
- `PUBLISH.local.md` — **gitignored**, the source of truth for live published versions, platform IDs, publish flow.

## Distribution — dual protocol, shared `skills/`

One `skills/` dir feeds two install protocols:

| Protocol | Recognizes | User command |
|---|---|---|
| Claude Code plugin | `.claude-plugin/marketplace.json` (`plugins[]`) | `/plugin marketplace add BaixuanZhu/skills` → `/plugin install <name>` |
| npx skills (Vercel CLI) | `skills/<name>/SKILL.md` (auto-scan) | `npx skills add BaixuanZhu/skills` |

**Adding a new skill requires updating `marketplace.json`** — append `{name, source: "./skills/<name>", description, category, keywords}` to the `plugins` array. Without this, the skill installs via `npx skills` but is invisible in the Claude Code marketplace. (npx skills needs no manifest change.)

## Conventions for editing skill content

- **Authoritative external reference for skill-writing**: <https://agentskills.io/home> — the industry-standard guide for authoring skills. Consult it when unsure about skill structure, frontmatter, or best practices.
- **Frontmatter `version` must be bumped when republishing.** The live published version is in `PUBLISH.local.md` (gitignored), not git — check it before any version bump. SkillHub rejects equal/lower versions silently.
- `description` field: two YAML styles both appear — `>-` (folded, for long trigger descriptions listing many keywords) and `|` (literal, for shorter ones). Match the skill's existing style.
- Numbered references are ordered by reading priority; cross-reference between files with pointers, don't duplicate content.
- Rule style: `✗ forbidden → ✓ recommended`. Match the bilingual (Chinese-primary) tone of each skill. (On the "why" column — see the quality standards below; it is usually redundant.)
- Editing principle: don't re-justify already-made decisions; don't keep "optional appendix" sections you wouldn't recommend — remove such prose when found.

## Skill content quality standards (apply when creating / updating / optimizing any skill)

These standards were distilled from repeated review cycles. Apply them every time — don't need to be reminded per-skill.

### What counts as "must keep" vs "redundant"

The single test: **if you delete this text, will the executing agent produce a different (worse) result?**

- **Must keep**: thresholds, trigger conditions, commands, mapping tables, mechanical criteria that prevent drift, hidden traps (errors that don't fail loud — e.g. spy/doReturn, verify times semantics, mockito-inline artifact pitfall), boundary/scope declarations.
- **Redundant** (delete or compress): see the concrete patterns in "Expression / redundancy patterns" below.

### Expression / redundancy patterns (concrete, from review cycles)

These recur across skills. When you see them, apply the test above — most are redundant and should be cut or compressed:

1. **Principle / theory preamble** — sections titled "核心立场"/"为什么不能…"/"X 的核心价值" that *argue why the method matters*. The agent needs to execute the method, not be persuaded of its worth. Cut the argument; keep the steps/thresholds. (e.g. "价值排序图", "为什么不能想到哪测到哪", "决策表的核心价值：防组合遗漏".)
2. **Academic / historical origins** — paper citations ("Chow 1978"), ISTQB axiom names recited as lore ("杀虫剂悖论"), acronym etymology. The agent executes the rule without knowing its provenance. Cut the citation; keep the rule.
3. **ASCII visualizations of what a nearby table already states** — decision trees, value-ranking diagrams, interval number lines, abstract Y/N matrices placed right before the concrete example/table. The concrete artifact is what the agent copies; the diagram is for human reading. Cut unless it encodes a decision the table doesn't.
4. **Motivational / restating blockquotes** — `>` quotes that restate the row above/below them in more emphatic language ("覆盖率是探照灯不是合格证", "非法迁移比合法还重要", "设计是主角，工具是配角"). If the adjacent table or rule already states it, the blockquote adds emphasis, not information. Cut.
5. **"Why this approach is good" self-justification** — "升级标准可机械执行——这是防漂移的关键", "这是消除'测不了'根因的正解". These argue for the rule rather than stating it. Cut the self-praise; keep the rule.
6. **Cross-file duplication** — the same rule restated in SKILL.md *and* each reference (java-unit-test had the assertion-library rule repeated 5+ times, Mock-boundary rules 3 times). Define a rule once (usually SKILL.md for cross-cutting defaults, the reference for method-specific detail); elsewhere point to it. Don't paste the rule again.
7. **Full code blocks that duplicate the tools file** — when a method reference (02/03/04) shows the complete `@ParameterizedTest`/`assertThrows` code and the tools file (06) has the same pattern, keep the design tables in the method file and the canonical code in the tools file. Don't duplicate the code in both.
8. **Maintainer-facing meta** — "本文件存在的唯一意义…", "本表只导航，不重复内容",收录哲学 ("只固化 A 类坑 / 不收 B 类"). This tells *editors* how to curate, not the *agent* what to do. Cut from skill content (this AGENTS.md is the right place for curation rules).

**Counter-pattern (do NOT cut)**: a `>` quote or aside that carries a *new operational fact* — e.g. "测试不过时 JaCoCo 报告不生成（report 绑 test phase）", "Mockito 4.x 需 mockito-inline", "LocalDate.now() 首选 Clock 注入而非 mockStatic". If deleting it leaves the agent about to step on a real pitfall, keep it (possibly compressed).

### Positive rules + negative examples (antipatterns) work together — don't strip negative examples mechanically

Telling the agent only *what to do* is often insufficient. **Wrong approaches frequently look surface-similar to correct ones**; a `✗` counter-example pins down the exact failure mode that a positive rule alone cannot distinguish. Evaluate each antipattern / negative-list item by this test:

> *Without this counter-example, can the agent distinguish wrong from right using only the positive rule?*
> - **Yes** (positive rule is already precise, or the counter-example duplicates one elsewhere) → delete.
> - **No** (the wrong form is a common, plausible misreading of the positive rule) → keep.

Examples from java-unit-test: "coverage ≥ 80% is enough" is worth keeping as a `✗` even though "coverage is a reverse-diagnostic, not a target" exists elsewhere — agents still mistake the number for a stop-line without the explicit counter-example. Conversely "don't test getters" is redundant once the S/A table already forbids testing framework glue.

### Scope/boundary declarations are not "negative lists" — keep them

A scope statement ("this skill covers unit tests only; integration/perf/frontend are out of scope") tells the agent where *not* to venture. This is operationally distinct from a "why we don't include X" justification (which is for maintainers and should be removed). Keep the former; cut the latter.

### "Why" columns in rule tables are usually redundant

A `✗ → ✓` pair is typically a complete, executable rule. A trailing "why" column usually restates the ✓ in explanatory prose. Exceptions where the why carries a *technical criterion the agent needs* (e.g. "@MockBean rebuilds Spring Context"): fold that fact into the ✓ cell rather than keeping a separate column.

## Dependencies / layer rules

- **Skills are *mostly* self-contained — except the agile family.** java/sa-token/mybatis skills must not hard-depend on another skill (verify with `grep` before claiming self-containment). But the agile skills (`agile-backlog`, `agile-sprint`, `agile-strategic`) declare explicit `dependencies:` frontmatter on `using-agile` / each other — that dependency chain is intentional.
- **`eval/` is downstream of `skills/`.** Evaluations *consume* skill content; skills never import from `eval/`. No product code under `eval/`.

## Commit style (mixed, not strict)

Commit subjects in this repo use a mix: `S1 <skill>: ...` (S0/S1/... = "slimdown round"), `fix:`, `init:`, `add ...`. There is no enforced single scheme. When in doubt, follow the most recent commit's style or use `S<n> <skill>: <summary>` for a content-slimdown round. Do not amend/push without user confirmation.

## Evaluation workflow (Darwin)

- Darwin evaluations run inside this repo; artifacts commit directly to `eval/<skill-name>/`.
- The workflow is: score (independent sub-agents, to avoid self-scoring bias) → improve → test (actually run, don't theorize) → independent blind re-score → ratchet (keep only verified improvements).
- Evaluation is transparent and reproducible — community can read inputs and challenge results.
- **Actually run tests** when a feedback item or fix is verifiable (build a minimal Maven project, run the code). Do not assert "the example works" from reading alone — this repo's environment has real gotchas (see below).

## Publishing

Publishing to SkillHub (腾讯) / 虾评 involves platform credentials, IDs, version tracking that **must not enter git**. The playbook is `PUBLISH.local.md` (gitignored). **Always read it before any version bump or publish attempt.** Publishing is outward-facing and irreversible — confirm with the user before either platform. The two platforms have independent version numbering; do not mix them up.

## Platform / environment gotchas

- **Shell is Git Bash on Windows.**
- **`grep -E "a|b"` (regex alternation) reliably fails** with `conflicting matchers specified` in this Git Bash — not flaky, every time. Work around: use multiple `grep` calls, or `grep -e a -e b`, or `git grep`, or `rg` if available.
- **`mvn` (Unix script under Git Bash) feeds `/g/...` or `/i/...` paths to Windows `java.exe` → `ClassNotFound`.** For a real Maven build, use `mvn.cmd` directly (it's on PATH) and redirect output to a log file, then read it — running `mvn` via `powershell -Command` wraps stderr as red error text and obscures results.
- **GBK-encoded Maven error output**: Chinese compiler errors come back in GBK; pipe through `iconv -f gbk -t utf-8` to read them, or use `strings`.
- LF→CRLF warnings on commit are benign (Windows `core.autocrlf`); add a `.gitattributes` only if cross-platform LF consistency matters.
- `.zcode/` is the user's locally-installed third-party skills (evaluation tools etc.) — gitignored, not part of this repo. Never commit it.

## Before changing sensitive areas, read

- `PUBLISH.local.md` (local, gitignored) — current published versions, platform IDs, publish flow. **Always before version bumps or publishing.**
- `skills/repo-init/SKILL.md` + `references/03-antipatterns.md` — if editing *this* `AGENTS.md` (the antipatterns file enumerates the mistakes to avoid here).
- `eval/README.md` — before running or committing a Darwin evaluation.
