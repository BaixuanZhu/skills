---
name: sa-token-dev
description: >-
  Sa-Token（cn.dev33）Java 权限认证框架开发助手。
  在 Java / Spring Boot 项目中开发任何登录、注册、登出、认证、鉴权、权限、角色、token、
  会话管理、接口保护、路由拦截、SSO 单点登录、OAuth2.0、JWT、踢人下线、账号封禁、记住我、
  二级认证、多账号体系、微服务网关鉴权相关功能时使用本技能——无论用户是否提到 Sa-Token
  （login / logout / authentication / authorization / permission / role / session / JWT /
  SSO / access control）。
  项目依赖已含 sa-token（sa-token-spring-boot*-starter 系列，覆盖 SpringBoot 2/3/4 与
  WebFlux 响应式变体）或代码出现 StpUtil / StpInterface / @SaCheckLogin / @SaCheckPermission /
  @SaCheckRole / SaInterceptor / SaRouter / SaSession 时必须使用本技能；
  项目尚无任何认证框架时，先主动询问用户是否引入 Sa-Token 再开发。
  次级触发信号（出现即异常）：封禁账号却自己写内存 Map 拦截、@SaCheck* 所在类没有
  SaInterceptor 注册、无状态方案却出现 kickout / getSession 调用。
  不适用于：已使用 Spring Security / Shiro 的项目（不建议迁移）、纯 JWT 自实现方案、非 Java 语言。
agent_created: true
version: 3.0.0
last_verified: "2026-10-28"
slug: sa-token-dev
displayName: Sa-Token 开发助手
---

# Sa-Token 开发助手

面向 Java 项目的 Sa-Token 认证开发。推荐 **1.46.0+**（最新稳定版），1.40.x 及以上适用。
本技能只做三件事：**把认证决策定下来落盘、把会绿的陷阱指出来、写完实测鉴权真的生效**。
API 写法模型自己会，不教——实测 4 组裸模型在注解拦截器注册、StpInterface、token 返回、
踢人场景值上零失误，这些不再占篇幅。

## 第 0 步：依赖探测与激活分支

任务涉及登录、认证、鉴权、权限、token、会话、SSO、OAuth2 等编码——**即使用户没提 Sa-Token**——先搜 `pom.xml` / `build.gradle`：

| 探测结果 | 动作 |
|---|---|
| 依赖含 `sa-token-*` | 激活本技能，走下方流程 |
| 无 sa-token，也无 Spring Security / Shiro | **询问**用户是否引入 Sa-Token；同意 → 按 `references/01-decisions.md` §0 引入后继续；拒绝 → 退出 |
| 已使用 Spring Security / Shiro | 告知不适用并退出，**不建议迁移** |

## 关键决策检查点

以下 6 个场景存在多条路线，**不可擅自替用户选择**；确认过的结果**落盘**（见「项目播种」），不再重复问。

1. 写任何代码前逐字扫描用户消息与上下文是否命中下表「触发信号」。
2. 命中 → 先出**选择题**（候选 + 标注推荐 + 一句话理由），禁止开放式提问。
3. 用户未回答 → 按「默认推荐」推进，并在输出开头标注「未确认，已使用默认方案 X」。**不阻塞**。
4. 一个需求命中多个 → 一次性列出全部问题。
5. 决策结果写入 `.claude/rules/sa-token.md`；下个会话先读它，读到就遵守，不重新提议。

| # | 触发信号（逐字关键词） | 必须确认的问题 | 方案差异（一句话） | 默认推荐 |
|---|---------|-------------|---------|----------------------|
| C1 | "JWT" / "无状态" / "不要 Redis" / "水平扩展" / "token 风格" | ① 是否无状态（不依赖 Redis）？② 是否要 JWT 风格 token？ | 有状态默认 simple-uuid + Redis；无状态 = Stateless JWT（丢踢人/Session/封禁）；能力矩阵见 `references/01-decisions.md` §1 | **有状态 + simple-uuid**；用户显式说"无状态/不要 Redis"视为已确认 |
| C2 | "SSO" / "单点登录" | ① 子系统前端是否同域？② 后端是否共享同一 Redis？ | 模式一同域同 Redis；模式二跨域同 Redis（Ticket）；模式三跨域异 Redis | 按条件自动判定（同域同 Redis → 模式一） |
| C3 | "登录"（未明确前后端分离） | 前端是浏览器页面，还是 App/小程序/SPA？ | Cookie 自动注入 vs Header 手动传 tokenValue | Cookie（浏览器）；Header（App/SPA） |
| C4 | "鉴权" / "权限" / "保护接口" | 粗粒度（路径）还是细粒度（方法）？有无全局白名单？ | 路由拦截 vs 注解，可混用；混用时收口规则见强约束 2 | **混用**（路由白名单 + 注解细粒度） |
| C5 | "微服务" / "网关" | 要不要无状态？要不要踢人/active-timeout？ | Redis 共享会话（功能全）vs JWT Stateless（无 Redis） | **Redis 共享会话** |
| C6 | "多账号" / "多体系" / "多端" | 几套独立登录体系？是否需独立 timeout？ | StpKit 多体系 vs 单体系 + device 区分设备 | ≥2 套 → StpKit |

## 项目播种

认证决策是典型的「模型拿不到的项目事实」——不落盘，下个会话重新问或直接猜。种子只写两样：
**项目事实**与**会被违反且不报警的流程**。API 用法一律不写。

**触发**：依赖含 `sa-token-*`，且项目无 `.claude/rules/sa-token.md`，或首行 `<!-- seeded: sa-token-dev@x.y.z -->`
版本低于本技能 → **提议**播种（一句话说明收益，等用户点头才落盘——未经同意不写项目文件，哪怕任务要求"把文件都写好"）。

**落点只有一个**：`.claude/rules/sa-token.md`，不碰 `CLAUDE.md`。带 `paths` frontmatter，只在
读写匹配文件时加载；glob 必须匹配项目真实文件名，写错是静默不加载。

**流程**（模板见 `assets/seed-template.md`）：

| 步 | 动作 |
|---|---|
| 1 | 按模板槽位读项目事实；**读不到就删掉那一行，不留占位符、不留默认值** |
| 2 | 读项目现有 `.claude/rules/*.md` 与 `CLAUDE.md`：已有同主题约定 → 以项目既有写法为准，跳过该槽位 |
| 3 | 按项目真实文件名校准 `paths`（Controller、Sa-Token 配置类） |
| 4 | 文件不存在 → 新建；首行有 `<!-- seeded:` → 整文件重写；无该标记是用户自己写的 → **不覆盖**，只补缺失事实 |

**加一道保险**：把最通用的三条同步写进认证入口类的 javadoc（受保护接口必须经注解或路由一处收口、
权限以后端校验为准、登录响应必须带 tokenValue）。实验证明类头比外部文件更可靠——代码跟着文件走，
任何工具读代码就看到；细粒度决策留种子文件。

**种子失控的形态**：一旦出现二级标题分节、代码块、「推荐/最佳实践」，说明它在退化成知识手册，
该部分删掉或搬进 `references/`。单个槽位去留问两问——① 能在代码里被违反吗？② 违反了模型自己会发现吗？
两问皆否就删。

## 核心强约束（只列会绿的——写错不报警，必须进自检）

1. **封禁用内置 API，不自造轮子**：`StpUtil.kickout(id)` 后 `StpUtil.disable(id, time)`，登录前
   `StpUtil.checkDisable(id)`（v1.31.0+ `login()` 不再校验封禁）。自己写内存 Map 拦截 = 重启即失效、
   多实例不一致、与 `NotLoginException` 的 DISABLE 语义脱节。
2. **注解生效依赖 SaInterceptor**：`@SaCheck*` 所在路径必须被 `SaInterceptor` 覆盖。**收口只留一处**：
   注解与路由混用时 `@SaIgnore` 只对注解生效、路由侧要 `SaRouter.free()`，两套白名单并存必然漏。
3. **StpInterface 是权限数据源**：不实现（或漏 `@Component`）则所有权限/角色校验**静默通过**。
4. **SaSession ≠ HttpSession**：互不通。用 Sa-Token 就全程 `StpUtil.getSession()`。
5. **JWT 是 token 风格，不是无状态的同义词**：有状态默认 simple-uuid + Redis，无需引入 JWT；
   Stateless 丢踢人/Session/封禁/active-timeout；能力矩阵见 `references/01-decisions.md` §1。
6. **is-share=true 时同账号共用一个 token**：`kickout` 踢的是共享 token，无法按设备区分。
7. **前后端分离登录响应必须带 tokenValue**：Cookie 模式框架自动注入，Header 模式不返回前端就拿不到凭证。
8. **SaServletFilter 异常不进 @ExceptionHandler**：必须 `.setError(e -> ...)`，否则直接 500。
9. **权限校验以后端为准**：前端按钮级显隐只是辅助，后端接口必须独立校验。

## 写完即验证（假绿判定）

鉴权代码写完，**发一次请求证明拦截真的在路径上**，不靠对照规则表自审：

- 不带 token 调受保护接口 → 必须未登录响应；带 token 调无权限接口 → 必须 403。
  返回 200 = 收口没生效（查强约束 2、3），这时任何"看起来对"的代码都是假绿。
- 封禁流程：封禁后旧 token 仍能访问 = 强约束 1 没做全（漏 kickout 或登录前 checkDisable）。
- 能力验证：宣称支持踢人的方案，写完真的调一次 kickout 证明旧 token 失效；做不到就别承诺。

## 使用流程

1. **确认适用性**：执行「第 0 步」，不适用 → 告知用户并退出。
2. **读项目种子**：`.claude/rules/sa-token.md` 有就先读（读到才生效）；没有则按 C1-C6 确认决策后提议播种。
3. **定位 reference**：决策细节 → `references/01-decisions.md`；陷阱 → `references/02-traps.md`。
4. **编码遵循强约束**，陷阱对照 `02-traps.md` 的失效模式分组。
5. **写完即验证**（上节），假绿一律返工。
6. **输出前自检**：强约束 9 条逐条过 + 决策已落盘/已标注默认方案 + 验证已执行。

## 决策路由

| 需求场景 | 读取文件 |
|---|---|
| starter 选择、C1-C6 展开：JWT 三模式能力矩阵、SSO 三模式判据、多账号选型、Cookie/Header、注解 vs 路由 | `references/01-decisions.md` |
| 假绿陷阱（按失效模式五组）与验证法：收口失效 / 状态语义 / 能力缺失 / 请求通道 / 配置与集成 | `references/02-traps.md` |

## 版本注意

- **前向兼容**：未覆盖的新增 API 以官方 `StpUtil` 源码为准；版本破坏性变更会直接报错，按报错改即可。
