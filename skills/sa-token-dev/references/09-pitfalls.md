# 常见坑与排错

## 1. NotLoginException 场景值

未登录时获取 loginId 会抛 `NotLoginException`，同为未登录有 7 种场景：

| 场景值 | 常量 | 含义 |
|---|---|---|
| -1 | `NOT_TOKEN` | 未从请求读到 token |
| -2 | `INVALID_TOKEN` | token 无效 |
| -3 | `TOKEN_TIMEOUT` | token 已过期 |
| -4 | `BE_REPLACED` | token 已被顶下线 |
| -5 | `KICK_OUT` | token 已被踢下线 |
| -6 | `TOKEN_FREEZE` | token 已被冻结（active-timeout 超时）|
| -7 | `NO_PREFIX` | 未按指定前缀提交 token |

## 2. 异常细分状态码 code

所有异常继承 `SaTokenException`，均可 `e.getCode()` 获取细分码，用于同类异常的不同情形区分（尤其 SSO/OAuth2）。

常用码段：核心包 11011~11016（token 无效/过期/被顶/被踢/冻结）、11041 缺角色、11051 缺权限、11071 二级认证未过；SSO 30001~30011；OAuth2 30101+；JWT 30201+。

## 3. 注解不生效

排查顺序：
1. 是否注册了 `SaInterceptor`（注解鉴权依赖它，默认关闭）。见 `04-annotation.md`。
2. 高版本 SpringBoot（≥2.6.x）配置类是否加了 `@EnableWebMvc`。
3. 注解是否被写在被 Spring 管理的 Bean（Controller）上。

## 4. SaSession 取不到值

`SaSession` 与 `HttpSession` 无关，互不通。全程只用 `SaSession`（`StpUtil.getSession()`），勿混用 `HttpSession`。

## 5. Redis 集成后仍丢数据 / 报错

- 是否配置了 Redis 连接信息（仅引依赖不够）。
- SpringBoot 3.x 前缀须为 `spring.data.redis`。
- Redis 集成包版本与 starter 版本尽量一致。

## 6. 跨域 CORS

前后端分离常见。两种方案：

**方案一：Sa-Token 内置 CORS 处理**
```java
@Configuration
public class SaTokenConfigure {
    @Bean
    public SaCorsHandleFunction corsHandle() {
        return (req, res, sto) -> {
            res.setHeader("Access-Control-Allow-Origin", "*")
               .setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE")
               .setHeader("Access-Control-Max-Age", "3600")
               .setHeader("Access-Control-Allow-Headers", "*");
            SaRouter.match(SaHttpMethod.OPTIONS).free(r -> {}).back();
        };
    }
}
```

**方案二：Spring CORS 配置 + 过滤器异常处理**
```java
// 过滤器中异常需手动加 CORS 头
.setError(e -> {
    SaHolder.getResponse()
        .setHeader("Access-Control-Allow-Origin", "*");
    return SaResult.error(e.getMessage());
})
```

> **注意**：过滤器异常不进 `@ExceptionHandler`，跨域场景必须在 `setError` 中处理 CORS 头，否则前端收到 CORS 错误而非业务错误。见 `10-antipattern.md` §17。

## 7. 反向代理后 uri 丢失

Nginx 反代后 `SaHolder.getRequest().getUrl()` 可能不对（影响 SSO 等）。两种方案：
- Nginx 加 `proxy_set_header Public-Network-URL http://$http_host$request_uri;` 并重写 `SaTokenContext.getRequest().getUrl()`。
- 或直接在 yml 配置 `sa-token.curr-domain: http://your-domain/api`。

## 8. 过滤器异常不进 @ExceptionHandler

`SaServletFilter` / `SaReactorFilter` 在 DispatcherServlet 之前执行，抛出的异常不进入 Spring 全局异常处理器。

```java
// ❌ 过滤器中异常不会被这里捕获
@ExceptionHandler(NotLoginException.class)
public SaResult handler(NotLoginException e) { ... }

// ✅ 必须在过滤器中配置 setError
new SaServletFilter()
    .setAuth(obj -> { StpUtil.checkLogin(); })
    .setError(e -> { return SaResult.error(e.getMessage()); });  // 这里处理
```

## 9. 排错流程

```
问题 → 排查路径
├─ 注解不生效 → ① 注册了 SaInterceptor？② SB≥2.6 加了 @EnableWebMvc？③ 注解在 Spring Bean 上？
├─ token 读不到 → ① 前端传了 token？② token-name 对应？③ 配了 token-prefix 但前端没加？
├─ Redis 丢数据 → ① 配了 Redis 连接？② SB3 用 spring.data.redis？③ 版本一致？
├─ 跨域报错 → ① 配了 CORS？② 过滤器 setError 加了 CORS 头？
├─ SSO 回调 URL 不对 → 反代 uri 丢失，配 sa-token.curr-domain
├─ 踢人后仍可访问 → 封禁未踢下线，先 kickout 再 disable
├─ active-timeout 莫名冻结 → 未触发自动续签（接口未走 Sa-Token 鉴权链）
└─ loginId 含冒号报错 → v1.46.0+ 默认禁止，配 allowLoginIdColon: true（见 §10）
```

## 10. 版本破坏性更新

| 版本 | 变更 | 现象 | 处理 |
|---|---|---|---|
| v1.46.0 | `StpInterface.isDisabled` 新增 `loginType` 参数 | 实现类编译失败 | 改 3 参（`11-advanced.md` §3.5）|
| v1.46.0 | `allowLoginIdColon` 默认 `false` | loginId 含冒号 `:` 登录/校验失败 | 配 `allowLoginIdColon: true`（见下）|
| v1.46.0 | JWT 集成 `extraData` 禁止保留字段 | 运行时抛异常 | 删保留字段（`14-plugin.md`）|

**allowLoginIdColon 详解**：v1.46.0 新增配置默认 `false`，loginId 含冒号直接报错——Sa-Token 持久化 key 用冒号分段，含冒号难以解析。

```yaml
sa-token:
  allowLoginIdColon: true    # 存量项目 loginId 含冒号时开启（如 "user:001" 风格）
```

- 升级到 v1.46.0+ 后登录突然失败，优先排查 loginId 是否含 `:`。
- 新项目**不要**用含冒号的 loginId；需要分隔符场景改用下划线等其他字符。

> **更多常见错误**：见 `10-antipattern.md`（28 条 Agent 常见错误纠偏）。
