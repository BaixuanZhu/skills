# 决策展开（C1–C6）

每节 = 一个检查点的判据、路线差异、能力损失。API 写法不在此处，需要示例时看官方源码或自行生成。
陷阱（会绿的错）统一在 `02-traps.md`，此处只给指针。

## §0 starter 选型

| 环境 | 坐标 |
|---|---|
| SpringBoot 2.x / 3.x / 4.x（Servlet） | `sa-token-spring-boot-starter` / `sa-token-spring-boot3-starter` / `sa-token-spring-boot4-starter` |
| WebFlux / Gateway（Reactor） | `sa-token-reactor-spring-boot{,3,4}-starter` |

- Servlet 与 Reactor 两个 starter **不可共存**（Bean 冲突，起不来——这是会红的，列在这里只为一次选对）。
- 微服务：网关用 Reactor、子服务用 Servlet，各自引入，不要父 pom 统一管理。
- 分布式必须 `sa-token-redis-template` + `commons-pool2`；不接 Redis 数据落内存，重启丢失、多实例各一套。

## §1 C1 token 风格与有无状态：能力矩阵

**两个正交维度**：token 风格（simple-uuid / jwt）× 状态（有状态走 Redis / 无状态本地验签）。
「无状态」的实现手段是 JWT，但引入 `sa-token-jwt` ≠ 无状态——Simple 模式就是 JWT + Redis 的有状态方案。

| 能力 | simple-uuid + Redis | JWT Simple | JWT Mixin | JWT Stateless |
|---|---|---|---|---|
| 踢人 / 顶人下线 | ✅ | ✅ | ❌ | ❌ |
| Session | ✅ | ✅ | 部分 | ❌ |
| active-timeout | ✅ | ✅ | ✅ | ❌ |
| 账号封禁 disable | ✅ | ✅ | ✅ | ❌ |
| id 反查 token | ✅ | ✅ | ✅ | ❌ |
| 依赖 Redis | 是 | 是 | Session 需要 | 否 |

**选型三问**：① 要不要踢人/封禁/Session？→ 要就别选无状态。② token 要不要人可读/自包含？→ 不要就
simple-uuid，**默认就是它，多数项目根本不用引 JWT**。③ 真无状态时接受能力损失清单并在回复里向用户声明。

**另一条无状态路径**：纯网关验签场景可不走 `StpUtil.login()`，直接用 `SaJwtUtil.createToken/getLoginId`
签发与验签（不落 SaTokenDao，无需 Redis）——能力损失与 Stateless 相同，同样要在回复里声明不支持踢人。
选哪条都行，但**能力损失不许静默**。

**已知陷阱指针**：JWT Simple 模式 `is-share` 恒为 false（`02-traps.md` 组二）；Mixin 登录数据内嵌 token，
改不动已发出的 token。

## §2 C2 SSO 三模式

| 模式 | 条件 | 机制 | 代价 |
|---|---|---|---|
| 一 | 同域 + 同 Redis | 共享 Cookie | 只适用同域；子系统登出要清理各自 Cookie domain |
| 二 | 跨域 + 同 Redis | URL 重定向 + Ticket | 每次跨域跳转换 Ticket，前端要有回跳处理 |
| 三 | 跨域 + 异 Redis | HTTP 请求校验 | 子系统各自独立会话，状态同步靠接口调用 |

判定就两问：前端同域吗？后端共享 Redis 吗？——四个象限里只有「同域+异 Redis」没有对应模式（同域就该共享 Redis）。
OAuth2 授权模式选型跟 SSO 模式正交，按「要给第三方发令牌还是自己人登录」分：自己人登录用不上 OAuth2。

**陷阱指针**：模式二/三 `allow-url` 配 `"*"`（组五）；模式一 Cookie domain 残留导致换账号串号（组五）。

## §3 C3 token 传递通道

| 通道 | 适用 | 要点 |
|---|---|---|
| Cookie | 浏览器同域/子域 | `login()` 后框架自动注入，前端零代码；跨域要配 CORS + credentials |
| Header | App / 小程序 / SPA 前后端分离 | 登录响应必须带 tokenValue（强约束 7），前端每次请求塞 header（参数名即 `tokenName`） |

混合形态（浏览器 + App 并存）：两个通道都开（`is-read-cookie` 与 `is-read-header` 同时 true），
登录接口按 User-Agent 或显式参数决定返回形态。token 前缀（如 `Bearer `）由 `token-prefix` 配置，
前缀与值之间**一个空格**，多空格或无空格都会验签失败（组四）。

## §4 C4 注解 vs 路由

| 方式 | 粒度 | 适用 |
|---|---|---|
| 路由（SaInterceptor + SaRouter） | 路径级 | 全局白名单、按模块粗粒度拦截 |
| 注解（@SaCheck*） | 方法级 | 精确到接口的登录/角色/权限校验 |

混用是常态（路由管白名单 + 注解管细粒度），但**收口必须只有一套白名单**：注解侧 `@SaIgnore`、
路由侧 `SaRouter.free()` 各管各的，两边都写白名单必然出现「两边都以为对方拦了」的洞（强约束 2）。
`SaRouter` 按书写顺序匹配，`stop()` 短路、`free()` 跳出后不再走后续 match——顺序错会静默放行（组一）。

## §5 C5 微服务鉴权

| 路线 | 机制 | 什么时候选 |
|---|---|---|
| Redis 共享会话 | 各服务连同一 Redis，`StpUtil.checkLogin()` 就地校验 | 要踢人/封禁/active-timeout（默认） |
| 网关统一校验 + 透传用户标识 | 网关验 token，下游信头部；下游仍建议二次验签 | 下游服务多、想收敛鉴权点 |
| JWT Stateless | 各服务本地验签 | 无 Redis、接受能力损失（§1） |

**服务间互信**：子服务接口不想暴露给外网时用 Same-Token（内部标识）区分内外流量——注意多服务同时
刷新 Same-Token 的并发问题（组五）。网关与下游的「信任边界」判定：头部用户标识是**可伪造的**，
跨网关的请求必须由网关强制校验，下游直接信 `X-User-Id` 之类头 = 任何人可冒充（组一）。

## §6 C6 多账号体系

| 路线 | 机制 | 什么时候选 |
|---|---|---|
| StpKit 多体系 | 每体系独立 StpLogic，独立 timeout/配置 | ≥2 套互不相干的登录体系（用户端 + 商家端） |
| 单体系 + device | `login(id, device)` 区分设备类型 | 同一批账号的多端（App/PC/小程序） |

判定问一句：两套体系的「人」是同一批吗？同一批 → device；不同批（商家 vs 用户）→ StpKit。
**LoginType 运行期不可改**：`StpUtil.TYPE` 之类体系标识必须在启动期定死，运行时修改行为未定义（组五）。
多体系各自维护 StpInterface 实现（`StpKit.of("user").getRoleList(...)` 走的还是同一个 StpInterface，
按 loginType 区分）。
