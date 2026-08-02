# Agent 常见错误与最佳实践（核心价值）

> 每条结构：**错误写法 → 正确写法 → 为什么**。AI 生成 Sa-Token 代码前应主动核对本章，避免"能跑但有坑"。

## 1. 未注册 SaInterceptor 就用注解（最高频）
- ❌ 直接在 Controller 上写 `@SaCheckLogin` / `@SaCheckPermission`，未注册 `SaInterceptor`。
- ✅ 先注册拦截器，注解才生效：
```java
@Configuration
public class SaTokenConfigure implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new SaInterceptor()).addPathPatterns("/**");
    }
}
```
- 为什么：`@SaCheck*` 注解的解析依赖 `SaInterceptor`，默认关闭。不注册则注解被完全忽略，鉴权形同虚设。

## 2. SaSession 与 HttpSession 混用
- ❌ `request.getSession().setAttribute("user", user)` 和 `StpUtil.getSession().set("user", user)` 交替使用，期望数据互通。
- ✅ 全程只用 `StpUtil.getSession()`（`SaSession`），不要用 `HttpSession`。
- 为什么：`SaSession` 是 Sa-Token 自己的会话模型，与 `HttpSession` 无任何关系，数据互不通。混用导致取不到值。

## 3. 前后端分离未返回 tokenValue
- ❌ 前后端分离项目用 `StpUtil.login(id)` 后直接返回"登录成功"，前端拿不到 token。
- ✅ 登录后返回 token 信息：
```java
StpUtil.login(10001);
SaTokenInfo tokenInfo = StpUtil.getTokenInfo();
return SaResult.data(tokenInfo);  // 含 tokenName 和 tokenValue
```
- 为什么：Cookie 模式下框架自动注入 token 到 Cookie，但前后端分离（App/小程序）无 Cookie，需后端手动返回。前端存本地后每次请求塞 header。

## 4. 权限校验只在前端做
- ❌ 前端根据权限码控制按钮显示，后端接口不做权限校验。
- ✅ 前端辅助显示 + 后端必须校验：`StpUtil.checkPermission("user.add")` 或 `@SaCheckPermission("user.add")`。
- 为什么：前端校验可被轻松绕过（直接调 API）。后端不校验等于裸奔。

## 5. timeout 与 active-timeout 误解
- ❌ 以为配了 `timeout: 2592000`（30天）就不会过期，不理解 `active-timeout` 的作用。
- ✅ 理解两者独立：
  - `timeout`：长久有效期，到期必须重新登录。`-1` 永久。
  - `active-timeout`：最低活跃频率，超时未操作被冻结（非删除）。`-1` 不限制。
  - 任一过期 token 不可用。
- 为什么：用户 30 天没访问但 token 没到 timeout，如果 active-timeout 配了 7 天，token 已被冻结。两个机制独立运行。

## 6. is-share / is-concurrent 配置误解
- ❌ 配了 `is-share: true` 后期望踢人下线能精准踢某个设备的 token。
- ✅ 理解配置语义：
  - `is-concurrent: true`（默认）= 允许同一账号多端同时登录。
  - `is-share: true` = 多次登录共用一个 token（踢人语义变化，因为只有一个 token）。
  - 需要同端互斥 → `is-concurrent: false` + `StpUtil.login(id, device)`。
- 为什么：`is-share: true` 时所有登录共用同一 token，`kickout` 踢的是这个共享 token，无法区分设备。

## 7. 踢人 vs 注销 vs 顶人混淆
- ❌ 把 `logout`、`kickout`、`replaced` 当成同一件事。
- ✅ 区分三种下线方式：
  - `StpUtil.logout(id)` = 正常注销（场景值无，token 自然失效）。
  - `StpUtil.kickout(id)` = 踢人下线（场景值 -5，`KICK_OUT`）。
  - `StpUtil.replaced(id, "PC")` = 顶人下线（场景值 -4，`BE_REPLACED`，同端互斥场景）。
- 为什么：前端可以根据不同场景值显示不同提示（"您已在其他设备登录" vs "您已被管理员下线" vs "正常退出"）。

## 8. 封禁后未踢下线
- ❌ `StpUtil.disable(10001, 86400)` 后期望用户立即下线。
- ✅ 先踢下线再封禁：
```java
StpUtil.kickout(10001);        // 先踢下线
StpUtil.disable(10001, 86400); // 再封禁
```
- 为什么：`disable` 只标记账号被封禁，不会让已登录的 token 失效。用户在封禁后仍可操作，直到 token 自然过期或被踢。

## 9. v1.31.0+ login 不校验封禁
- ❌ `StpUtil.login(id)` 后期望被封禁的账号无法登录。
- ✅ 登录前显式校验：
```java
StpUtil.checkDisable(10001);  // 被封禁抛 DisableServiceException
StpUtil.login(10001);
```
- 为什么：v1.31.0 起将校验封禁和登录分离成两个方法，`login()` 不再自动校验。不显式调用则被封禁账号仍可登录。

## 10. Redis 前缀配错
- ❌ SpringBoot 3.x 项目用 `spring.redis.*` 配置 Redis 连接。
- ✅ SpringBoot 3.x 用 `spring.data.redis.*`：
```yaml
spring:
  data:        # SB3.x
    redis:
      host: 127.0.0.1
      port: 6379
# spring:      # SB2.x
#   redis:
#     host: 127.0.0.1
```
- 为什么：SpringBoot 3.x 将 Redis 配置前缀从 `spring.redis` 改为 `spring.data.redis`。配错导致 Sa-Token 连不上 Redis，数据存内存（重启丢失、分布式不一致）。

## 11. Starter 混用（Servlet + Reactor）
- ❌ 同一项目同时引入 `sa-token-spring-boot-starter` 和 `sa-token-reactor-spring-boot-starter`。
- ✅ 根据项目模型二选一：
  - SpringMVC（Servlet）→ `sa-token-spring-boot-starter`
  - WebFlux / Gateway（Reactor）→ `sa-token-reactor-spring-boot-starter`
- 为什么：两个 starter 注册不同的上下文实现，同时引入导致 Bean 冲突，项目无法启动。

## 12. 过滤器异常未用 setError
- ❌ 用 `SaServletFilter` 做鉴权，异常处理只配了 `@ExceptionHandler`。
- ✅ 过滤器必须配 `.setError()`：
```java
@Bean
public SaServletFilter getSaServletFilter() {
    return new SaServletFilter()
        .addInclude("/**")
        .setAuth(obj -> { SaRouter.match("/**", "/user/doLogin", r -> StpUtil.checkLogin()); })
        .setError(e -> { return SaResult.error(e.getMessage()); });  // 必须配
}
```
- 为什么：过滤器在 Spring MVC DispatcherServlet 之前执行，抛出的异常不进入 `@ExceptionHandler`。不配 `setError` 则异常直接 500。

## 13. JWT Stateless 模式误用
- ❌ 选了 `StpLogicJwtForStateless`（无状态模式），然后需要踢人下线 / Session / active-timeout。
- ✅ 按需选模式：
  - 需要踢人/顶人/Session → `StpLogicJwtForSimple`（推荐）
  - 需要登录数据放 Token + Session → `StpLogicJwtForMixin`
  - 完全无状态、不需要 Session → `StpLogicJwtForStateless`
- 为什么：Stateless 模式完全舍弃 Redis，无 Session 存储，不支持踢人/顶人/active-timeout/id反查Token。功能受限，不适合需要会话管理的场景。

## 14. SSO allow-url 配 "*"
- ❌ SSO-Server 配置 `allow-url: "*"` 直接上生产。
- ✅ 测试用 `"*"`，生产必须配置详细 URL：
```yaml
sa-token:
  sso-server:
    clients:
      sso-client1:
        client: sso-client1
        allow-url: https://app1.example.com/sso/login  # 精确地址
```
- 为什么：`allow-url: "*"` 允许任意来源的 SSO 授权请求，存在安全风险（Ticket 劫持）。生产环境必须白名单。

## 15. SaRouter 匹配顺序错误
- ❌ 把精确路由放在通配路由后面：
```java
SaRouter.match("/**", r -> StpUtil.checkLogin());      // 先匹配了所有
SaRouter.match("/user/doLogin", r -> {});               // 永远不会执行
```
- ✅ 精确路由放前面，或用 `notMatch` 排除：
```java
SaRouter.match("/**", "/user/doLogin", r -> StpUtil.checkLogin());  // 排除登录接口
// 或
SaRouter.match("/user/doLogin").stop();                  // 先 stop 跳过
SaRouter.match("/**", r -> StpUtil.checkLogin());        // 再拦截全部
```
- 为什么：`SaRouter.match` 按代码顺序依次匹配，前面的通配规则会"吞掉"后面的精确规则。

## 16. @SaIgnore 与路由拦截混淆
- ❌ 以为 `@SaIgnore` 能忽略自定义拦截器/过滤器中的鉴权。
- ✅ `@SaIgnore` 只忽略 **Sa-Token 注解鉴权** 和 **SaInterceptor 中的路由拦截鉴权**，对自定义拦截器/过滤器不生效。
- 为什么：`@SaIgnore` 的作用域是 Sa-Token 框架内部的鉴权链，自定义代码不受框架管控。

## 17. 跨域 + 过滤器异常处理
- ❌ 前后端分离跨域请求，Sa-Token 过滤器抛异常后前端收到 CORS 错误而非业务错误。
- ✅ 在 `setError` 中处理 CORS 响应头：
```java
.setError(e -> {
    SaHolder.getResponse()
        .setHeader("Access-Control-Allow-Origin", "*")
        .setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE");
    return SaResult.error(e.getMessage());
})
```
- 为什么：浏览器 CORS 预检失败时不会读取响应体。过滤器异常如果没设置 CORS 头，浏览器直接报 CORS 错误，前端拿不到实际错误信息。

## 18. 反向代理后 uri 丢失
- ❌ Nginx 反代后 SSO 回调 URL 不对。
- ✅ 两种方案：
  - Nginx 加 `proxy_set_header Public-Network-URL http://$http_host$request_uri;`
  - 或 yml 配置 `sa-token.curr-domain: http://your-domain/api`
- 为什么：Nginx 反代后 `SaHolder.getRequest().getUrl()` 获取的是内网地址，影响 SSO 重定向。

## 19. Token 前缀与值之间无空格
- ❌ 配了 `token-prefix: Bearer`，前端提交 `Bearersatokenxxx`（前缀和值连在一起）。
- ✅ 前缀与值之间**必须有一个空格**：`Bearer satokenxxx`。
- 为什么：框架按空格分割前缀和 token 值。无空格则无法正确裁剪前缀，token 读取失败。

## 20. SSO 模式一 Cookie domain 未清理
- ❌ 测试 SSO 模式一时配了 `sa-token.cookie.domain: stp.com`，切换到模式二/三后未注释掉。
- ✅ 模式一测完后**必须注释掉** `cookie.domain` 配置，否则影响模式二/三。
- 为什么：模式二/三不依赖共享 Cookie，配了 `cookie.domain` 会导致 Cookie 作用域异常，干扰跨域流程。

## 21. 多账号 LoginType 运行时修改
- ❌ 在代码运行时动态修改 `StpLogic` 的 `loginType`。
- ✅ `LoginType` 只在项目启动时指定（如 `new StpLogic("user")`），运行时不可更改。
- 为什么：运行时修改 `LoginType` 会造成线程安全问题和严重的逻辑错误。多账号体系应在启动时通过 `StpKit` 门面模式定义好。

## 22. Same-Token 多服务同时刷新
- ❌ 多个微服务都调用 `SaSameUtil.refreshToken()`。
- ✅ 专门起一个服务用定时任务刷新：
```java
@Scheduled(cron = "0 0/5 * * * ?")
public void refreshToken() {
    SaSameUtil.refreshToken();
}
```
- 为什么：多服务同时刷新会造成毫秒级短暂服务失效（Token 更换瞬间旧 Token 可能失效）。应集中刷新，且刷新间隔须低于有效期（默认一天）。

## 23. 全局侦听器未 try-catch
- ❌ `SaTokenListener` 的回调方法中直接写业务逻辑，异常未捕获。
- ✅ 不安全代码用 try-catch 包裹：
```java
@Override
public void doLogin(String loginType, Object loginId, String tokenValue, SaLoginParameter loginParameter) {
    try {
        // 业务逻辑（如发消息、写日志）
    } catch (Exception e) {
        e.printStackTrace();
    }
}
```
- 为什么：侦听器异常会中断 Sa-Token 整个登录流程，导致登录失败。try-catch 隔离业务异常。

## 24. StpInterface 未加 @Component
- ❌ 实现了 `StpInterface` 接口但忘记加 `@Component`，权限校验时找不到实现类。
- ✅ 必须加 `@Component` 让 SpringBoot 扫描：
```java
@Component
public class StpInterfaceImpl implements StpInterface {
    // ...
}
```
- 为什么：Sa-Token 通过 Spring 依赖注入获取 `StpInterface` 实现。未被 Spring 管理的类不会被扫描，鉴权时找不到数据源。

## 25. active-timeout 续签机制不理解
- ❌ 配了 `active-timeout: 1800`（30分钟），以为定时器自动续签，不理解为什么用户操作中仍被冻结。
- ✅ 理解自动续签触发时机：
  - 框架在调用 `getLoginId()`、`getTokenSession()`、`checkLogin()`、`hasRole()`、`checkPermission()` 及 `@SaCheckLogin` 等注解时**自动执行冻结检查与续签**。
  - 如果接口未被 Sa-Token 拦截/注解保护，则不会触发续签。
  - 关闭自动续签：`autoRenew=false`。手动续签：`StpUtil.updateLastActiveToNow()`。
- 为什么：active-timeout 的续签不是定时器，而是"按需触发"。如果某些接口不走 Sa-Token 鉴权链，最后活跃时间不会更新。

## 26. JWT hutool 版本冲突
- ❌ 引入 `sa-token-jwt` 后项目已有 `hutool 5.8.13` 或 `5.8.14`，出现类型转换异常。
- ✅ 要么不引入 hutool，要么引入版本 >= 5.7.14 且避开 5.8.13/5.8.14。
- 为什么：`sa-token-jwt` 显式依赖 `hutool-jwt 5.7.14`，而 hutool 5.8.13 和 5.8.14 存在已知的类型转换问题。

## 27. 网关用 Servlet 依赖
- ❌ SpringCloud Gateway 项目引入 `sa-token-spring-boot-starter`（Servlet 依赖）。
- ✅ SpringCloud Gateway 是 Reactor 模型，必须用 `sa-token-reactor-spring-boot-starter`。
- 为什么：Gateway 基于 WebFlux（Reactor），与 Servlet 模型不兼容。用错依赖导致 Sa-Token 无法注册过滤器。

## 28. JWT Simple 模式 is-share 恒为 false
- ❌ JWT Simple 模式配了 `is-share: true`，期望多端共用 token。
- ✅ JWT Simple 模式下 `is-share` **恒为 `false`**，配置无效。
- 为什么：`is-share=true` 与 JWT per-token Extra 数据机制不兼容，框架强制设为 false。同理，JWT Mixin 模式 `is-concurrent` 恒为 `true`。
