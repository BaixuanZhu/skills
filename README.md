# BaixuanZhu Skills

[English](./README.en.md) | **中文**

面向**中文 Java / Spring 生态**的 Agent Skills 套装。覆盖编码契约、单元与集成测试、主流框架（Sa-Token / MyBatis-Plus）开发、敏捷流程——让 AI 编码助手在中文 Java 项目里表现得更专业。

## 安装

支持两种安装方式，**任选其一**。两种方式安装的是同一份技能内容。

### 方式一：Claude Code（推荐）

每个技能都是独立的 plugin，**可单独安装**你需要的：

```
/plugin marketplace add BaixuanZhu/skills
/plugin install java-standard         # 按「插件名」安装，一个插件可能含多个技能
/plugin install java-test
```

> 插件名见下方「包含的插件」表格。装多个就重复 `/plugin install <插件名>`。

### 方式二：npx skills（其他 Agent 通用）

适用于 Cursor / Codex / Zed / Windsurf / Gemini CLI 等 41+ agent。会把技能文件**复制到你的项目**（可自行编辑）：

```bash
npx skills add BaixuanZhu/skills
```

> **两者区别**：Claude Code plugin 是托管只读包，更新随插件走；`npx skills` 给你的是可编辑文件副本，更灵活但需自己跟进更新。

## 包含的插件

| 插件 | 包含技能 | 用途 | 适用场景 |
|------|----------|------|----------|
| **java-standard** | `java-contract` | 读 pom 定目标 JDK，把边界决策（八项）落成 `.claude/rules/java-contract.md`——用前主动读一次（不会自动注入），写完编译验证；附按失效模式追问的存量审查七组 | 新项目立规矩、定某个方法返回 null 还是空集合、审存量代码 |
| **java-test** | `java-unit-test`<br>`java-integration-test` | 不教测试代码怎么写，教**什么时候绿灯是假的**：开发期纯单测（`@Mock` 毫秒级）+ 集成测试三决策（回归谁值守 / 放哪层 / 环境用什么跑）与假绿三机制（路径不对 / 时间点不对 / 失败不算失败） | 编写 / 评审 / 补全测试；功能稳定后补集成层 |
| **sa-token-dev** | `sa-token-dev` | Sa-Token 权限认证框架开发助手 | 登录鉴权、权限角色、SSO、JWT、会话管理 |
| **mybatis-plus-dev** | `mybatis-plus-dev` | MyBatis-Plus ORM 增强框架开发助手 + 项目播种机制 | CRUD、分页查询、Mapper/Service 层、事务、逻辑删除 |
| **agile** | `using-agile`<br>`agile-strategic`<br>`agile-backlog`<br>`agile-sprint` | 敏捷套件（4 技能合一）：入口路由 → 愿景/架构 C4/ADR → 产品待办 → Sprint 规划。**附带两个 hook**：会话开始注入 Sprint/Backlog/ADR 状态，Backlog 写完后全量重算统计（不再由模型现场算） | 从零做项目规划、迭代管理、写架构决策记录 |

### 分层建议

- **通用底座**（几乎必装）：`java-standard` + `java-test`
- **框架增强**（按技术栈选）：`sa-token-dev` / `mybatis-plus-dev`
- **敏捷流程**（团队选装）：`agile`（入口 `using-agile` 自动路由到其余三个）

## 维护

技能内容在 `skills/<name>/` 直接编辑；`plugins/<name>/` 是为 Claude Code / ZCode 插件规范准备的镜像（嵌套 `.claude-plugin/plugin.json` + `skills/<name>/`），由 pre-commit hook（`scripts/sync-plugins.mjs`）自动同步，push 时 GitHub Actions 兑底校验。**改技能只改 `skills/`**。

## 测试与评估

各技能的达尔文评估产物（测试 prompt、产出快照、判分记录）公开在 [`eval/`](./eval/)，按技能分子目录，可自行查看与复现。

## License

MIT © BaixuanZhu
