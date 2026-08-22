# 05 · CLAUDE.md 迁移与适配指针

Claude Code **只读 `CLAUDE.md` 家族，不原生读 `AGENTS.md`**（官方文档化的兼容做法是让 CLAUDE.md 引用它）。
本文件定义「迁移 + 降级」流程：把 CLAUDE.md 的实质内容搬进 AGENTS.md，再把 CLAUDE.md 降为**零内容适配指针**，
保证 Claude Code 仍能加载全部项目上下文，同时维持 AGENTS.md 单一事实源。**不删除 CLAUDE.md 文件本身**——直接删会让 Claude Code 丢失上下文。

## 决策矩阵（替代旧 C1：AGENTS.md / CLAUDE.md 存在与否的四种组合 + 幂等）

| AGENTS.md | CLAUDE.md | 处理 |
|---|---|---|
| 无 | 无 | Path A 冷启动 |
| 无 | 有**实质内容** | **迁移**：内容分流进 AGENTS.md（+扫描补全）→ CLAUDE.md 降为 stub |
| 有 | 无 | Path B 增量更新；询问是否补 stub（不擅自新建） |
| 有 | 有**实质内容** | **双源去重**：独有内容并入，冲突项列给用户裁决（默认以构建文件/CI 真实信号为准） |
| 有 | 已是 stub | Path B；stub **不动**（幂等，禁止二次追加） |

## 迁移 5 步

1. **读全文并展开 import 链**：读 `CLAUDE.md` 全部内容，**同时展开其 `@path` 引用的每个文件**（相对路径相对 CLAUDE.md 所在目录解析），否则漏内容。
2. **三路分流**：
   - 项目事实（命令 / 约定 / 架构 / 硬约束 / 陷阱）→ 进 AGENTS.md 对应 section。
   - Claude 专属（hooks、permissions、slash commands、plan mode 指令）→ 留在 stub 的 `## Claude Code` 小节，**不**进 AGENTS.md。
   - 状态类（待办 / 进度 / 未决问题）→ 不迁移；列出清单让用户确认丢弃（遵循强约束 7 无状态原则）。
3. **冲突裁决**：AGENTS.md 与 CLAUDE.md 同项但矛盾时，**列 diff 给用户**，默认以构建文件 / CI 实际信号为准，不擅自定夺。
4. **写 stub**：CLAUDE.md 首行写 `@AGENTS.md`（同目录相对路径），Claude 专属内容放其后；**保留原文件**。
5. **四条自查**：
   - AGENTS.md 无任何工具专属语法（`@` 引用 / Claude 指令）
   - stub 不含任何项目事实副本（判据：出现重复内容即违规）
   - import 行未被反引号包裹、路径相对本文件且可解析
   - 子目录 `CLAUDE.md` 用同样流程成对处理（相对路径各指各的 `@AGENTS.md`）

## 适配指针 stub 模板

```markdown
@AGENTS.md

## Claude Code
（Claude 专属指令，如 plan mode / hooks / permissions；无则整节省略）
```

## import 陷阱（硬价值）

- 反引号或代码块内的 `@path` **不导入**（写作时用反引号包裹路径可禁用导入；反之正文裸写路径会误导入整份文件）。
- 相对路径相对**导入文件所在目录**解析，不相对工作目录。
- 嵌套导入有深度上限（社区实测口径 4~5 跳不一致，不写死数字；本方案只用单层 `@AGENTS.md`，不受影响）。
- 指向工作目录**外**的 import（如 `@~/.claude/...`）首次会弹审批框；**拒绝后永久静默禁用**且不再询问。stub 只用同目录相对路径即可规避。
- 验证：Claude Code 会话内 `/memory` 应列出 CLAUDE.md 及其导入的 AGENTS.md；未列出则按上述陷阱排查。

## symlink 备选（不推荐）

`ln -s AGENTS.md CLAUDE.md` 让 Claude Code 逐字节读取同一文件，但 **Windows 需管理员 / 开发者模式**，失败时静默无提示；无法在 stub 里加 Claude 专属内容。默认用 `@AGENTS.md` import，symlink 仅作 macOS/Linux 无专属内容时的备选。

## 边界

- **不处理**：`CLAUDE.local.md`（gitignored 的本地个人文件）、`~/.claude/CLAUDE.md`（用户级全局记忆）。
- **其他工具文件**：Cursor / Windsurf 已原生读 AGENTS.md，迁移后 `.cursorrules` / `.windsurfrules` 直接删；无 import 机制的工具不做 stub。
- 迁移是「搬运 + 降级」而非删除：CLAUDE.md 文件必须保留（即使内容全空也有 `@AGENTS.md` 一行）。
- monorepo：子目录 `CLAUDE.md` 同样成对迁移（本目录 `AGENTS.md` + 本目录 stub），不并入根文件（见 `04`）。
