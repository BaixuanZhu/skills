# 注解鉴权

> 将鉴权与业务分离。**前提：必须注册 SaInterceptor 拦截器，注解才生效。**

## 注解清单

- `@SaCheckLogin`：登录校验
- `@SaCheckRole("admin")`：角色校验
- `@SaCheckPermission("user.add")`：权限校验
- `@SaCheckSafe`：二级认证校验
- `@SaCheckHttpBasic` / `@SaCheckHttpDigest`：HTTP Basic/Digest 校验
- `@SaCheckDisable("comment")`：账号服务封禁校验
- `@SaCheckSign`：API 签名校验
- `@SaIgnore`：忽略校验（最高优先级）

## 1. 注册拦截器（必做）

```java
@Configuration
public class SaTokenConfigure implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // 注册 Sa-Token 拦截器，打开注解式鉴权
        registry.addInterceptor(new SaInterceptor()).addPathPatterns("/**");
    }
}
```

> 高版本 SpringBoot（≥2.6.x）若注册失效，类上额外加 `@EnableWebMvc`。

## 2. 使用注解

```java
@SaCheckLogin
@RequestMapping("info")
public String info() { return "查询用户信息"; }

@SaCheckRole("super-admin")
@RequestMapping("add")
public String add() { return "用户增加"; }

@SaCheckPermission("user-add")
@RequestMapping("add2")
public String add2() { return "用户增加"; }
```

> 注解可加在类上，代表对该类所有方法生效。

## 3. 校验模式 AND / OR

```java
@SaCheckPermission(value = {"user-add", "user-all"}, mode = SaMode.OR)  // 满足其一
```
- `SaMode.AND`：必须全部具有（默认）。
- `SaMode.OR`：具有其一即可。

## 4. 权限 or 角色 双重校验

```java
// 具备权限 user.add 或角色 admin 即可通过
@SaCheckPermission(value = "user.add", orRole = "admin")
```
- `orRole = "admin"`：需拥有 admin。
- `orRole = {"admin", "manager"}`：三者其一。
- `orRole = {"admin, manager"}`：必须同时具有。

## 5. 忽略认证 @SaIgnore

```java
@SaCheckLogin
@RestController
public class TestController {
    @SaIgnore   // 此接口允许游客访问
    @RequestMapping("getList")
    public SaResult getList() { return SaResult.ok(); }
}
```
- `@SaIgnore` 优先级最高，与其它鉴权注解同时出现时后者被忽略。
- 同时可忽略路由拦截鉴权（对自定义拦截器/过滤器不生效）。

## 6. 批量注解 @SaCheckOr

```java
@SaCheckOr(
    login = @SaCheckLogin,
    role = @SaCheckRole("admin"),
    permission = @SaCheckPermission("user.add")
)
@RequestMapping("test")
public SaResult test() { return SaResult.ok(); }
```
- 满足其中任一注解即通过。
- 多个鉴权注解并列写 = 天然 AND 关系（故无 `@SaCheckAnd`）。

## 7. 注解鉴权 vs 路由拦截鉴权（选型指南）

| 特性 | 注解鉴权（@SaCheck*） | 路由拦截鉴权（SaRouter） |
|------|---------------------|------------------------|
| 粒度 | 方法级 / 类级 | 路径级 / 模块级 |
| 灵活性 | 声明式，写死在代码中 | 可编程，支持动态规则 |
| 适用 | 细粒度：单个接口需特定权限 | 粗粒度：整个模块统一鉴权 |
| 代码量 | 每个接口加注解 | 集中配置一处 |

**最佳实践**：
- **粗粒度用路由拦截**："除登录接口外全部需登录" → SaRouter 一行搞定。
- **细粒度用注解**："删除需要 user.delete 权限" → `@SaCheckPermission`。
- **两者可混用**：路由做全局登录校验，注解做细粒度权限校验。
- **不要重复校验**：路由已校验的，注解不要再重复。

```java
// 混用示例
@Configuration
public class SaTokenConfigure implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new SaInterceptor(handler -> {
            SaRouter.match("/**", "/user/doLogin", r -> StpUtil.checkLogin());
        })).addPathPatterns("/**");
    }
}

@RestController
public class UserController {
    @SaCheckPermission("user.delete")  // 细粒度
    @DeleteMapping("delete")
    public SaResult delete() { ... }
}
```

## 扩展
- Service 层注解：引入 `sa-token-spring-aop` 插件（见 `14-plugin.md` §4），**不可与拦截器模式同时使用**。
- 自定义注解：结合 `@SaCheckLogin(type = "user")` + 注解合并（见 `11-advanced.md` §6）。
- SpEL 表达式：`sa-token-spring-el` 插件支持复杂条件组合（见 `14-plugin.md` §7）。
