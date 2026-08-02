# 路由拦截鉴权

> 适用场景：批量鉴权（如「除登录接口外全部需登录」），比逐个加注解代码量小。

## 1. 注册路由拦截器

```java
@Configuration
public class SaTokenConfigure implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // 全局登录校验，排除登录接口
        registry.addInterceptor(new SaInterceptor(handle -> StpUtil.checkLogin()))
                .addPathPatterns("/**")
                .excludePathPatterns("/user/doLogin");
    }
}
```

## 2. 使用 SaRouter 定义详细规则

```java
registry.addInterceptor(new SaInterceptor(handler -> {
    // 登录校验：拦截所有，排除登录接口
    SaRouter.match("/**", "/user/doLogin", r -> StpUtil.checkLogin());

    // 角色校验：admin 开头需 admin 或 super-admin 角色
    SaRouter.match("/admin/**", r -> StpUtil.checkRoleOr("admin", "super-admin"));

    // 按模块分权限
    SaRouter.match("/user/**", r -> StpUtil.checkPermission("user"));
    SaRouter.match("/goods/**", r -> StpUtil.checkPermission("goods"));
})).addPathPatterns("/**");
```

`SaRouter.match(path, fun)`：参数一为匹配路由，参数二为校验函数（内可写任意代码）。

## 3. 匹配特征

```java
// 基础：匹配 path，执行 check
SaRouter.match("/user/**").check(r -> StpUtil.checkLogin());

// 多 path + restful
SaRouter.match("/user/**", "/goods/**", "/art/get/{id}").check(/* ... */);

// 排除匹配
SaRouter.match("/**").notMatch("*.html", "*.css", "*.js").check(/* ... */);

// 按请求类型
SaRouter.match(SaHttpMethod.GET).check(/* ... */);

// 按 boolean / lambda 条件
SaRouter.match(StpUtil.isLogin()).check(/* ... */);
SaRouter.match(r -> StpUtil.isLogin()).check(/* ... */);

// 连缀（AND 关系）
SaRouter.match(SaHttpMethod.GET).match("/user/**").check(/* ... */);
```

## 4. 退出匹配链

```java
SaRouter.match("/user/back").back("直接返回前端的内容");  // 停止匹配并直接返回前端
```
- `stop()`：停止匹配，但仍进入 Controller。
- `back()`：停止匹配，直接返回结果给前端，不进 Controller。

## 5. free 独立作用域

```java
SaRouter.match("/**").free(r -> {
    SaRouter.match("/a/**").check(/* ... */);
    SaRouter.match("/b/**").check(/* ... */).stop();  // 仅跳出 free 作用域
});
SaRouter.match("/**").check(/* ... */);  // 继续执行
```

## 6. 与注解配合
- `@SaIgnore` 可忽略路由拦截校验（对自定义拦截器/过滤器不生效）。
- `SaInterceptor` 注册后默认同时开启注解校验；关闭注解校验：`new SaInterceptor(...).isAnnotation(false)`。
- `setBeforeAuth(...)` 注册认证前置函数（其中的 `SaRouter.stop()` 可跳过后续鉴权）。

## 7. 常见路由模式

### 全局登录校验 + 白名单

```java
registry.addInterceptor(new SaInterceptor(handler -> {
    SaRouter.match("/**")
        .notMatch("/user/doLogin", "/user/register", "/favicon.ico")
        .notMatch("*.html", "*.css", "*.js")
        .check(r -> StpUtil.checkLogin());
})).addPathPatterns("/**");
```

### 按模块分权限

```java
SaRouter.match("/user/**", r -> StpUtil.checkPermission("user"));
SaRouter.match("/admin/**", r -> StpUtil.checkRoleOr("admin", "super-admin"));
SaRouter.match("/goods/**", r -> StpUtil.checkPermission("goods"));
```

### 动态权限（从数据库加载规则）

```java
List<RouteRule> rules = routeRuleService.getAll();
for (RouteRule rule : rules) {
    SaRouter.match(rule.getPattern(), r -> StpUtil.checkPermission(rule.getPermission()));
}
```

## 最佳实践
- **匹配顺序**：精确路由放前面，通配路由放后面。`SaRouter.match` 按代码顺序依次匹配。
- **notMatch 排除**：用 `.notMatch()` 排除静态资源和公开接口，比在 match 中列排除路径更清晰。
- **stop vs back**：`stop()` 停止匹配但仍进 Controller；`back()` 直接返回前端不进 Controller。
- **过滤器 vs 拦截器**：WebFlux/Gateway 必须用过滤器（`SaReactorFilter`），Servlet 环境推荐用拦截器。

> **常见错误**：SaRouter 匹配顺序错误、@SaIgnore 对自定义过滤器不生效 → 见 `10-antipattern.md` §15、§16。
