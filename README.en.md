# BaixuanZhu Skills

**English** | [中文](./README.md)

An Agent Skills suite for the **Chinese Java / Spring ecosystem**. Covers coding standards, quality gates, unit testing, mainstream framework development (Sa-Token / MyBatis-Plus), agile workflows, and project bootstrap — making AI coding assistants sharper on Chinese-team Java projects.

> **Note:** Skill content is written in **Chinese** (rules, references, examples). The skill descriptions that trigger an agent are also Chinese. If you work on Chinese Java codebases, this is intentional; if your stack is English-only, be aware the skills will inject Chinese context.

## Installation

Two install paths are supported — **pick one**. Both ship the same skill content.

### Option A: Claude Code (recommended)

Each skill is a standalone plugin you install individually:

```
/plugin marketplace add BaixuanZhu/skills
/plugin install repo-init              # install only what you need
/plugin install java-coding-guide-pro
```

> Skill names are in the table below. Repeat `/plugin install <name>` for each.

### Option B: npx skills (agent-agnostic)

For Cursor / Codex / Zed / Windsurf / Gemini CLI and 41+ other agents. Copies editable skill files into your project:

```bash
npx skills add BaixuanZhu/skills
```

> **Difference:** the Claude Code plugin is a managed, read-only package that updates with the plugin; `npx skills` gives you editable file copies — more flexible, but you track updates yourself.

## Included skills

| Skill | Purpose | Use when |
|------|------|----------|
| **repo-init** | Generate / update a cross-tool `AGENTS.md` project brief | Bootstrapping a new project so any AI tool understands it fast |
| **java-coding-guide-pro** | Java coding standards & pitfalls (JDK 8–25, Alibaba handbook, SonarQube) | Writing / modifying / reviewing any Java/Spring code |
| **java-coding-quality** | Java code quality & security gate (PMD7 + SpotBugs/FindSecBugs) | Pre-commit checks, code review, security scanning |
| **java-unit-test** | Java unit-test standards alignment (design method + engineering defaults) | Writing / reviewing / backfilling unit tests |
| **sa-token-dev** | Sa-Token auth framework dev assistant | Login/auth, roles & permissions, SSO, JWT, session management |
| **mybatis-plus-dev** | MyBatis-Plus ORM enhancement dev assistant | CRUD, pagination, Mapper/Service layers, transactions, logical delete |
| **using-agile** | Agile management entry point (routing + state detection) | Entering a project with `agile-docs/`, starting the agile flow |
| **agile-strategic** | Agile strategy layer (vision + C4 architecture + ADR) | Writing vision, tech selection, architecture decision records |
| **agile-backlog** | Agile product backlog (dual-file Backlog) | Breaking down work, prioritizing, feeding sprint planning |
| **agile-sprint** | Full-cycle Sprint planner | Opening, planning, and closing a Sprint |

### Recommended layering

- **Base** (near-essential): `repo-init` + `java-coding-guide-pro` + `java-coding-quality` + `java-unit-test`
- **Framework boost** (match your stack): `sa-token-dev` / `mybatis-plus-dev`
- **Agile flow** (teams): `using-agile` (entry) → `agile-strategic` / `agile-backlog` / `agile-sprint`

## Maintenance

Skill content is edited directly in `skills/<name>/`. The `plugins/<name>/` directory is a mirror for the Claude Code / ZCode plugin spec (nested `.claude-plugin/plugin.json` + `skills/<name>/`), kept in sync automatically by a pre-commit hook (`scripts/sync-plugins.mjs`), with a GitHub Actions check on push. **To change a skill, edit only `skills/`.**

## Testing & evaluation

Darwin-style evaluation artifacts (test prompts, output snapshots, scoring records) for each skill are public under [`eval/`](./eval/), organized by skill — feel free to inspect and reproduce.

## License

MIT © BaixuanZhu
