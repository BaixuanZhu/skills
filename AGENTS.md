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
- Rule style: `✗ forbidden → ✓ recommended → why`. Match the bilingual (Chinese-primary) tone of each skill.
- Editing principle: don't explain why something is *not* included; don't re-justify already-made decisions; don't keep "optional appendix" sections you wouldn't recommend — remove such prose when found.

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
