# AGENTS.md

This is a **skills development + distribution repository**. It authors, evaluates, and distributes "Agent Skills" (SKILL.md content packages) targeting Chinese Java/Spring ecosystems (Sa-Token, MyBatis-Plus, Java coding standards, agile workflows, etc.). There is no application to build, run, or deploy — the product is the skill content itself.

## Repository layout

- `skills/<name>/` — the skills. Each has a `SKILL.md` (frontmatter: `name`, `description`, `version`, usually `slug` + `displayName`) plus `references/` (numbered `NN-topic.md`) and sometimes `assets/`. **This is the primary thing being edited.**
- `eval/<skill-name>/` — Darwin evaluation artifacts (test prompts, isolated agent snapshots, scoring records). Organized per-skill; commit artifacts here after running an evaluation.
- `.claude-plugin/` — Claude Code plugin marketplace manifests (`marketplace.json` + `plugin.json`). Each skill is listed as an independent plugin entry so users can install selectively.
- `README.md` — public-facing install guide (dual-protocol: Claude Code plugin + `npx skills`).

## Distribution — dual protocol, shared `skills/`

The single `skills/` directory feeds two install protocols simultaneously:

| Protocol | Recognizes | User command |
|----------|-----------|--------------|
| Claude Code plugin | `.claude-plugin/marketplace.json` (plugins array) | `/plugin marketplace add BaixuanZhu/skills` → `/plugin install <skill-name>` |
| npx skills (Vercel CLI) | `skills/<name>/SKILL.md` (auto-scan) | `npx skills add BaixuanZhu/skills` |

**Adding a new skill requires updating `marketplace.json`** — append a `{name, source: "./skills/<name>", description, category, keywords}` entry to the `plugins` array. Without this, the skill installs via `npx skills` but is invisible in the Claude Code marketplace. (npx skills needs no manifest change — it auto-scans.)

## Conventions for editing skills

- **SKILL.md is the entry/router layer, not the knowledge layer.** Keep it short; push detail into `references/NN-*.md`. A sustained goal has been to *shrink* files — don't bloat them.
- Frontmatter `version` must be bumped when republishing. The live published version is tracked locally (see `PUBLISH.local.md`, not in git) — check it before any version bump.
- Numbered references are ordered by reading priority; cross-reference between files with pointers rather than duplicating content.
- Content style: rules written as `✗ forbidden → ✓ recommended → why`. Match the existing bilingual (Chinese-primary) tone of each skill.
- Editing principle: **don't explain why something is *not* included; don't re-justify already-made decisions; don't keep "optional appendix" sections you wouldn't recommend.** Remove such prose when encountered.

## Architecture / layer rules

- **Skills are self-contained.** A skill must not hard-depend on another skill (no "requires java-coding-guide-pro as a prerequisite" prose). Verify with `grep` before claiming self-containment.
- **`eval/` is downstream of `skills/`.** Evaluations *consume* skill content; they are not imported by the skills. Don't add product code under `eval/`.
- Commit subjects use `S0/S1/...` "slimdown round" prefixes and `P0/P1/P2/P3` priority tags — follow that style when committing skill edits.

## Evaluation workflow

- Darwin evaluations run inside this repo; artifacts (prompts, snapshots, scoring) commit directly to `eval/<skill-name>/`.
- Evaluation is transparent and reproducible: community can read inputs and challenge results.
- See `eval/README.md` for the per-skill subdirectory convention.

## Publishing

Publishing to SkillHub / 虾评 involves platform credentials, IDs, and version tracking that **must not enter git**. The publish playbook lives in `PUBLISH.local.md` (gitignored). **Always read it before any version bump or publish attempt.** Publishing is outward-facing and irreversible — confirm with the user before either platform.

## Platform / environment notes

- Shell is Git Bash on Windows. Gotcha: invoking `mvn` (a Unix script under Git Bash) feeds `/g/...` or `/i/...` paths to Windows `java.exe`, causing `ClassNotFound`. Use PowerShell + `mvn.cmd` when a real Maven build is needed.
- LF→CRLF warnings on commit are benign (Windows default `core.autocrlf`); add a `.gitattributes` if cross-platform LF consistency matters.

## Before changing sensitive areas, read

- `PUBLISH.local.md` (local, gitignored) — current published versions, platform IDs, publish flow. **Always check before version bumps or publishing.**
- `skills/repo-init/SKILL.md` + `references/03-antipatterns.md` — if editing this `AGENTS.md` (the antipatterns file enumerates exactly the mistakes to avoid here).
