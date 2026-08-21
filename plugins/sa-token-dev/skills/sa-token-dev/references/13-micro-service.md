# 微服务架构

## 1. 依赖引入规则（关键）

> **核心原则：网关和内部服务必须分开引入 Sa-Token 依赖。不要在顶级父 pom 中统一引入。**

### 1.1 依赖选择（Servlet vs Reactor，按 SpringBoot 版本）

| SpringBoot | 内部服务 / Zuul（Servlet） | SpringCloud Gateway / ShenYu（Reactor） |
|---|---|---|
| 2.x | `sa-token-spring-boot-starter` | `sa-token-reactor-spring-boot-starter` |
| 3.x | `sa-token-spring-boot3-starter` | `sa-token-reactor-spring-boot3-starter` |
| 4.x | `sa-token-spring-boot4-starter` | `sa-token-reactor-spring-boot4-starter` |

> **Servlet 与 Reactor 依赖不可同时引入同一项目，否则项目无法启动。** 网关用 Reactor，子服务用 Servlet，各自单独引入。
> 其他相关依赖：`sa-token-forest`（HTTP 工具，SSO 模式三需要）、`sa-token-alone-redis`（权限缓存与业务缓存隔离，见 `14-plugin.md` §6）。

### 1.4 Redis 集成（必须）

网关和子服务通过 Redis 同步会话数据，Redis 集成包必须引入：
```xml
<!-- 版本号请使用最新稳定版，1.40.x+ 均适用；各 sa-token-* 依赖版本保持一致 -->
<dependency>
    <groupId>cn.dev33</groupId>
    <artifactId>sa-token-redis-template</artifactId>
    <version>1.46.0</version>
</dependency>
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-pool2</artifactId>
</dependency>
```

> SpringBoot 3.x：Redis 前缀用 `spring.data.redis`。

---

## 2. 分布式 Session 会话

多节点部署时单机 Session 无法跨节点共享（节点 A 登录，请求落到节点 B 被认为未登录）。四种方案：

| 方案 | 描述 | 评价 |
|---|---|---|
| Session 同步 | 节点数据改变时强制同步 | 性能消耗大，不推荐 |
| Session 粘滞 | 网关保证请求稳定落在同一节点 | 与框架无关，网关层处理 |
| **会话中心（Redis）** | Session 存 Redis，节点无状态 | **Sa-Token 推荐** |
| 无状态 Token（JWT） | 用户数据写入 Token 本身 | 功能受限，复杂业务不适用 |

**实现**：引 `sa-token-redis-template` + 配置 Redis 连接即可，上层 API 不变，框架自动将会话写入 Redis；所有节点无状态，可自由横向扩展。

```yaml
spring:
  data:           # SB3.x
    redis:
      host: 127.0.0.1
      port: 6379
      database: 1
```

- JWT Stateless 模式虽无状态，但不支持踢人/Session/active-timeout（见 `14-plugin.md` §1）。
- 如需权限缓存与业务缓存隔离，用 Alone-Redis 插件（见 `14-plugin.md` §6）。

---

## 3. 网关统一鉴权

鉴权模式二选一：各服务各自鉴权（与单体差别不大），或**网关统一鉴权**（推荐，网关集中处理所有鉴权逻辑）。

### 3.1 依赖（SpringCloud Gateway 为例）

```xml
<!-- Reactor 依赖（Gateway 是 WebFlux 模型）；另需引入 §1.4 的 Redis 集成依赖（必须） -->
<dependency>
    <groupId>cn.dev33</groupId>
    <artifactId>sa-token-reactor-spring-boot-starter</artifactId>
    <version>1.46.0</version>
</dependency>
```

### 3.2 实现 StpInterface（权限数据源）

```java
@Component
public class StpInterfaceImpl implements StpInterface {
    @Override
    public List<String> getPermissionList(Object loginId, String loginType) {
        // 方案一：网关集成 ORM 直接查库
        // 方案二：先查 Redis 缓存，未命中查库
        // 方案三：先查 Redis，未命中 RPC 调子服务
        return ...;
    }

    @Override
    public List<String> getRoleList(Object loginId, String loginType) {
        return ...;
    }
}
```

### 3.3 注册全局过滤器

```java
@Configuration
public class SaTokenConfigure {

    @Bean
    public SaReactorFilter getSaReactorFilter() {
        return new SaReactorFilter()
            .addInclude("/**")
            .addExclude("/favicon.ico")
            .setAuth(obj -> {
                // 登录校验
                SaRouter.match("/**", "/user/doLogin", r -> StpUtil.checkLogin());

                // 按模块校验权限
                SaRouter.match("/user/**", r -> StpUtil.checkPermission("user"));
                SaRouter.match("/admin/**", r -> StpUtil.checkPermission("admin"));
                SaRouter.match("/goods/**", r -> StpUtil.checkPermission("goods"));
            })
            .setError(e -> {
                return SaResult.error(e.getMessage());
            });
    }
}
```

### 3.4 最佳实践
- **Redis 必须**：网关通过 Redis 与子服务同步会话。
- **Reactor 依赖**：Gateway 用 `sa-token-reactor-spring-boot-starter`，不能用 Servlet 依赖。
- **登录接口排除**：`/user/doLogin` 需排除在登录校验之外。
- **setError 必须**：过滤器异常不进 `@ExceptionHandler`。
- 子服务无需重复鉴权（网关已校验），但建议保留注解作为二次防线。

---

## 4. 内部服务外网隔离（Same-Token）

### 4.1 场景与方案

子服务不应被外网直接访问，必须经网关转发。优先**物理隔离**（子服务部署内网，仅网关对外）；无法物理隔离时用 **Same-Token 逻辑隔离**（子服务只接受携带 Same-Token 的请求）。需覆盖两个环节：① 网关转发请求时携带 Same-Token、子服务校验；② Feign 等服务间 RPC 调用时携带 Same-Token。

### 4.2 环节一：网关转发鉴权

**网关添加 GlobalFilter**：
```java
@Component
public class ForwardAuthFilter implements GlobalFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest newRequest = exchange.getRequest().mutate()
            .header(SaSameUtil.SAME_TOKEN, SaSameUtil.getToken())
            .build();
        return chain.filter(exchange.mutate().request(newRequest).build());
    }
}
```

**子服务校验 Same-Token**：
```java
@Configuration
public class SaTokenConfigure {
    @Bean
    public SaServletFilter getSaServletFilter() {
        return new SaServletFilter()
            .addInclude("/**")
            .addExclude("/favicon.ico")
            .setAuth(obj -> {
                // 校验当前请求携带的 Same-Token（无效抛异常）
                SaSameUtil.checkCurrentRequestToken();
            })
            .setError(e -> SaResult.error(e.getMessage()));
    }
}
```

### 4.3 环节二：服务间 Feign 调用

**调用方添加 FeignInterceptor**：
```java
@Component
public class FeignInterceptor implements RequestInterceptor {
    @Override
    public void apply(RequestTemplate requestTemplate) {
        // 添加 Same-Token
        requestTemplate.header(SaSameUtil.SAME_TOKEN, SaSameUtil.getToken());

        // 如需被调用方有会话状态，还需传递 satoken
        // requestTemplate.header(StpUtil.getTokenName(), StpUtil.getTokenValue());
    }
}
```

**Feign 接口使用**：
```java
@FeignClient(
    name = "sp-home",
    configuration = FeignInterceptor.class,
    fallbackFactory = SpHomeFallback.class
)
public interface SpHomeInterface {
    @RequestMapping("/api/getConfig")
    String getConfig(@RequestParam("key") String key);
}
```

### 4.4 SaSameUtil API

| 方法 | 说明 |
|---|---|
| `getToken()` | 获取当前 Same-Token |
| `isValid(token)` | 判断是否有效 |
| `checkToken(token)` | 校验（无效抛异常） |
| `checkCurrentRequestToken()` | 校验当前请求的 Same-Token |
| `refreshToken()` | 刷新 Token |
| `SaSameUtil.SAME_TOKEN` | 储存 key 常量 |

### 4.5 Same-Token 刷新机制

- Token 默认存 Redis，有效期一天。
- **旧 Token 保留一个刷新周期**作为次级 Token，防止刷新瞬间服务中断。
- **生产环境**：专门起一个服务用定时任务刷新，不要多服务同时刷新：
```java
@Scheduled(cron = "0 0/5 * * * ?")
public void refreshToken() {
    SaSameUtil.refreshToken();
}
```

### 4.6 最佳实践
- **物理隔离优于逻辑隔离**：条件允许时子服务部署内网。
- **Same-Token 刷新集中化**：一个服务定时刷新，不要多服务同时调 `refreshToken()`。
- **刷新间隔**：须低于有效期（默认一天），建议 5 分钟 ~ 2 小时。
- **Feign 如需会话状态**：除 Same-Token 外还需传 `satoken`。
- **子服务校验可简化**：`SaSameUtil.checkCurrentRequestToken()` 一行搞定。

