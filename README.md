# BaixuanZhu Skills

面向**中文 Java / Spring 生态**的 Agent Skills 套装。覆盖编码规范、质量门禁、单元测试、主流框架（Sa-Token / MyBatis-Plus）开发、敏捷流程、项目初始化——让 AI 编码助手在中文 Java 项目里表现得更专业。

## 安装

支持两种安装方式，**任选其一**。两种方式安装的是同一份技能内容。

### 方式一：Claude Code（推荐）

作为 Claude Code plugin 安装——托管只读，随插件统一更新：

```
/plugin marketplace add BaixuanZhu/skills
/plugin install baixuanzhu-skills
```

### 方式二：npx skills（其他 Agent 通用）

适用于 Cursor / Codex / Zed / Windsurf / Gemini CLI 等 41+ agent。会把技能文件**复制到你的项目**（可自行编辑）：

```bash
npx skills add BaixuanZhu/skills
```

> **两者区别**：Claude Code plugin 是托管只读包，更新随插件走；`npx skills` 给你的是可编辑文件副本，更灵活但需自己跟进更新。

## 包含的技能

| 技能 | 用途 | 适用场景 |
|------|------|----------|
| **repo-init** | 生成/更新跨工具通用的 `AGENTS.md` 项目简报 | 新项目冷启动、让任意 AI 工具快速理解项目 |
| **java-coding-guide-pro** | Java 编码规范与避坑（JDK 8~25、阿里手册、SonarQube） | 编写 / 修改 / 审查任何 Java/Spring 代码 |
| **java-coding-quality** | Java 代码质量与安全门禁（PMD7 + SpotBugs/FindSecBugs） | 提交前检查、代码审查、安全扫描 |
| **java-unit-test** | Java 单元测试规范对齐（设计方法 + 工程默认值） | 编写 / 评审 / 补全单元测试 |
| **sa-token-dev** | Sa-Token 权限认证框架开发助手 | 登录鉴权、权限角色、SSO、JWT、会话管理 |
| **mybatis-plus-dev** | MyBatis-Plus ORM 增强框架开发助手 | CRUD、分页查询、Mapper/Service 层、事务、逻辑删除 |
| **using-agile** | 敏捷管理入口（路由 + 状态检测） | 进入含 `agile-docs/` 的项目、开始敏捷流程 |
| **agile-strategic** | 敏捷战略层（愿景 + 架构 C4 + ADR） | 写愿景、技术选型、架构决策记录 |
| **agile-backlog** | 敏捷产品待办（双文件 Backlog） | 拆任务、排优先级、迭代规划输入 |
| **agile-sprint** | Sprint 全周期规划器 | 开 Sprint、规划迭代、关闭 Sprint |

### 分层建议

- **通用底座**（几乎必装）：`repo-init` + `java-coding-guide-pro` + `java-coding-quality` + `java-unit-test`
- **框架增强**（按技术栈选）：`sa-token-dev` / `mybatis-plus-dev`
- **敏捷流程**（团队选装）：`using-agile`（入口）→ `agile-strategic` / `agile-backlog` / `agile-sprint`

## 维护

本仓库的技能内容由开发仓库同步而来，通过同步脚本更新。新增技能时在开发仓库的同步脚本白名单加一行即可，无需手动改本仓库。

## License

MIT © BaixuanZhu
