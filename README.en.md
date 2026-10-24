# BaixuanZhu Skills

**English** | [中文](./README.md)

An Agent Skills suite for the **Chinese Java / Spring ecosystem**. Covers coding contracts, unit & integration testing, mainstream framework development (Sa-Token / MyBatis-Plus), and agile workflows — making AI coding assistants sharper on Chinese-team Java projects.

> **Note:** Skill content is written in **Chinese** (rules, references, examples). The skill descriptions that trigger an agent are also Chinese. If you work on Chinese Java codebases, this is intentional; if your stack is English-only, be aware the skills will inject Chinese context.

## Installation

Two install paths are supported — **pick one**. Both ship the same skill content.

### Option A: Claude Code (recommended)

Each skill is a standalone plugin you install individually:

```
/plugin marketplace add BaixuanZhu/skills
/plugin install java-standard         # install by PLUGIN name; one plugin may bundle several skills
/plugin install java-test
```

> Plugin names are in the table below. Repeat `/plugin install <plugin-name>` for each.

### Option B: npx skills (agent-agnostic)

For Cursor / Codex / Zed / Windsurf / Gemini CLI and 41+ other agents. Copies editable skill files into your project:

```bash
npx skills add BaixuanZhu/skills
```

> **Difference:** the Claude Code plugin is a managed, read-only package that updates with the plugin; `npx skills` gives you editable file copies — more flexible, but you track updates yourself.

## Included plugins

| Plugin | Bundled skills | Purpose | Use when |
|------|----------------|---------|----------|
| **java-standard** | `java-contract` | Reads the pom to pin the target JDK, records boundary decisions (eight items) into `.claude/rules/java-contract.md` — read it before coding (it is not auto-injected), compile right after writing; plus a seven-group review checklist for legacy code | Setting ground rules for a new project; deciding null vs empty collection; reviewing legacy code |
| **java-test** | `java-unit-test`<br>`java-integration-test` | Not how to write test code, but **when a green build is lying**: millisecond unit tests (`@Mock`) + three integration decisions (who owns the regression, which layer, how to run it) and three false-green mechanisms (wrong path / wrong timing / failure not counted) | Writing / reviewing / backfilling tests; adding an integration layer once features stabilize |
| **sa-token-dev** | `sa-token-dev` | Sa-Token auth framework dev assistant | Login/auth, roles & permissions, SSO, JWT, session management |
| **mybatis-plus-dev** | `mybatis-plus-dev` | MyBatis-Plus ORM enhancement dev assistant + project seeding | CRUD, pagination, Mapper/Service layers, transactions, logical delete |
| **agile** | `using-agile`<br>`agile-strategic`<br>`agile-backlog`<br>`agile-sprint` | Agile suite (4-in-1): entry routing → vision / C4 architecture / ADR → product backlog → sprint planning. The backlog's source of truth is `backlog.json`; the human-readable `PRODUCT-BACKLOG.md` is rendered from it. **Ships three hooks**: every turn it injects "what this step is + the rule most often skipped here" according to the project's current stage (conflict to resolve / backfill to close / vision / architecture / backlog / sprint planning / sprint running); projects without `agile-docs/` get a one-time entry hint only on planning-style prompts, so you never invoke the entry skill by hand. Writing `backlog.json` validates the structure, re-renders the view, and reconciles sprint points (no more model-computed stats, and hand-edits to the rendered file are reverted) | Greenfield project planning, iteration management, architecture decision records |

### Recommended layering

- **Base** (near-essential): `java-standard` + `java-test`
- **Framework boost** (match your stack): `sa-token-dev` / `mybatis-plus-dev`
- **Agile flow** (teams): `agile` (the `using-agile` entry routes to the other three)

## Maintenance

Skill content is edited directly in `skills/<name>/`. The `plugins/<name>/` directory is a mirror for the Claude Code / ZCode plugin spec (nested `.claude-plugin/plugin.json` + `skills/<name>/`), kept in sync automatically by a pre-commit hook (`scripts/sync-plugins.mjs`), with a GitHub Actions check on push. **To change a skill, edit only `skills/`.**

## Testing & evaluation

Darwin-style evaluation artifacts (test prompts, output snapshots, scoring records) for each skill are public under [`eval/`](./eval/), organized by skill — feel free to inspect and reproduce.

## License

MIT © BaixuanZhu
