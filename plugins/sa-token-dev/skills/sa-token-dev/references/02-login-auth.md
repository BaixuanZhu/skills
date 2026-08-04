# 登录认证

> 核心：登录本质是把「唯一标识 userId」交给框架，框架生成 token + session 并返回前端。

## 1. 登录

```java
// 参数为账号 id，建议类型：long | int | String，不可传 User/Admin 等复杂对象
StpUtil.login(Object userId);
```

典型登录接口：
```java
@RequestMapping("doLogin")
public SaResult doLogin(String name, String pwd) {
    if ("zhang".equals(name) && "123456".equals(pwd)) {   // 真实项目查库比对
        StpUtil.login(10001);
        return SaResult.ok("登录成功");
    }
    return SaResult.error("登录失败");
}
```

## 2. 校验是否登录

```java
StpUtil.isLogin();     // 返回 true/false
StpUtil.checkLogin();  // 未登录则抛出 NotLoginException
```

配合全局异常处理器统一返回：
```java
@RestControllerAdvice
public class GlobalException {
    @ExceptionHandler(NotLoginException.class)
    public SaResult handler(NotLoginException e) {
        return SaResult.error(e.getMessage());
    }
}
```

> `NotLoginException` 有 7 种场景值（未提交/无效/过期/被顶/被踢/被冻结/无前缀），精细化处理见 `09-pitfalls.md`。

## 3. 会话查询

```java
StpUtil.getLoginId();              // 未登录抛异常
StpUtil.getLoginIdAsString();     // 转 String
StpUtil.getLoginIdAsInt();        // 转 int
StpUtil.getLoginIdAsLong();       // 转 long
StpUtil.getLoginIdDefaultNull();  // 未登录返回 null
StpUtil.getLoginId(T defaultValue); // 未登录返回默认值
```

## 4. Token 查询

```java
StpUtil.getTokenValue();               // 当前会话 token 值
StpUtil.getTokenName();                // token 名称
StpUtil.getLoginIdByToken(tokenValue); // token 反查账号 id，无效返回 null
StpUtil.getTokenTimeout();             // 剩余有效期（秒，-1=永久）
StpUtil.getTokenInfo();                // token 详细参数 SaTokenInfo
```

## 5. 注销

```java
StpUtil.logout();
```

## Token 有效期：timeout vs active-timeout
- `timeout`：长久有效期（默认 30 天）。到期必须重新登录。v1.29.0+ 可用 `StpUtil.renewTimeout(seconds)` 续期。`-1` 永久。
- `active-timeout`：最低活跃频率。超过此时长无操作则被「冻结」（非删除）。有操作自动续签。`-1` 不限制。
- 两者独立，任一过期 token 即不可用。
- 自动续签：框架在直接/间接调用 `getLoginId()`、`getTokenSession()`（含 `checkLogin`、`hasRole`、`checkPermission` 及 `@SaCheckLogin` 等注解）时执行冻结检查与续签。
- 手动续签：
```java
StpUtil.checkActiveTimeout();     // 检查是否已冻结，是则抛异常
StpUtil.updateLastActiveToNow();  // 续签（更新最后操作时间）
```
- 关闭自动续签：配置 `autoRenew=false`。

## 登录流程最佳实践

### 标准 Web 应用（Cookie 模式）

```java
@RequestMapping("doLogin")
public SaResult doLogin(String name, String pwd) {
    // 1. 校验账号密码（查库）
    User user = userService.login(name, pwd);
    if (user == null) return SaResult.error("账号或密码错误");

    // 2. 校验封禁状态（v1.31.0+ 必须手动）
    StpUtil.checkDisable(user.getId());

    // 3. 登录
    StpUtil.login(user.getId());

    // 4. Cookie 模式自动注入，无需手动返回 token
    return SaResult.ok("登录成功");
}
```

### 前后端分离（Header 模式）

```java
@RequestMapping("doLogin")
public SaResult doLogin(String name, String pwd) {
    User user = userService.login(name, pwd);
    if (user == null) return SaResult.error("账号或密码错误");

    StpUtil.checkDisable(user.getId());
    StpUtil.login(user.getId());

    // 必须返回 tokenValue，前端存本地后塞 header
    return SaResult.data(StpUtil.getTokenInfo());
}
```

### 登录方式决策

| 场景 | 方案 |
|------|------|
| Web 应用 | Cookie 自动注入，`login(id)` 即可 |
| 前后端分离 / App / 小程序 | 返回 `SaTokenInfo`，前端塞 header |
| 记住我 | `login(id, true)`（默认）或 `login(id, false)`（非记住我） |
| 同端互斥 | `is-concurrent: false` + `login(id, device)` |
| 指定 token 有效期 | `login(id, new SaLoginParameter().setTimeout(seconds))` |

> **常见错误**：前后端分离未返回 tokenValue、封禁未踢下线 → 见 `10-antipattern.md` §3、§8。
