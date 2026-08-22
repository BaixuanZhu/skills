# 04 · Monorepo 嵌套策略

大仓库（monorepo / 多包）下，单一根 `AGENTS.md` 会被稀释。AGENTS.md 规范**明确支持嵌套**：
子目录的 `AGENTS.md` 就近覆盖本目录及子孙，根文件管全局。这仍是同一套通用记忆的层级扩展，
**不违反"通用、工具无关"原则**（所有工具都读就近的 AGENTS.md）。

## 何时嵌套

| 条件 | 建议 |
|------|------|
| 单仓单服务 | 只根 `AGENTS.md` |
| monorepo，子包技术栈/约定差异大（如 `apps/web` React vs `packages/core` 纯 TS 库） | 根 + 子包各一份 |
| 子包有独立测试/构建/发布流程 | 子包放 `AGENTS.md` 写本包命令 |
| 仅根约定适用全仓、子包无特殊 | 不嵌套，避免碎片化 |

## 作用域与合并（叠加，非覆盖）

- 子目录 `AGENTS.md` 对其**所在目录及所有子孙目录**生效，工具取**最靠近目标文件**的那份；根文件写全局通用项（仓库级 style、安全红线、PR 流程），子包写本包特有项（本包 install/build/test、本包架构、本包硬约束）。
- **不是覆盖**：子包与根文件**叠加**生效，子包只写差异项，不重复全局约定；**不要**重写全局 Code style（除非本包有 CI 强制的例外）。
- 例：`apps/web/AGENTS.md` 只需写"本包用 `pnpm --filter web dev`""本包用 React Query 而非根约定的 zustand"等差异。

## 嵌套示例

```
repo-root/AGENTS.md                # 全局：仓库级 style、安全红线、PR 流程
repo-root/apps/web/AGENTS.md       # 本包：pnpm --filter web dev/build/test、React 约定
repo-root/apps/admin/AGENTS.md     # 本包：pnpm --filter admin ...、Vue 约定
repo-root/packages/core/AGENTS.md  # 本包：纯 TS 库、vitest、changeset 发布
```

**子目录 stub 规则**：monorepo 内子目录若有 `CLAUDE.md`，按 `05` 同法成对迁移——本目录 `AGENTS.md` + 本目录 stub（相对路径 `@AGENTS.md`），不并入根文件。

## 检查点（对应 SKILL.md C3）

- 检测到 monorepo（根有 `pnpm-workspace.yaml` / `lerna.json` / `packages/*` 多独立构建文件）→
  **询问用户**：是否需子包就近嵌套？默认推荐"根 + 差异子包"。
- 检测到已有子目录 `AGENTS.md` → 走增量，不覆盖、不重建。

## 反例（见 `03` §9）

✗ 大 monorepo 只在根放一份，把所有子包命令、架构、坑全堆进去 → 根文件 500 行、子包上下文被稀释。
✓ 根管全局 + 子包写差异项，每份尽量 ≤200 行（推荐上限，可超）、信息密集。
