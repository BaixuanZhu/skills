# 高级特性

> 适用于 Sa-Token 1.46.0+。

## 1. 记住我（Remember Me）

### 原理

Sa-Token 的登录授权**默认就是记住我模式**。利用 Cookie 的两种生命周期：
- **临时 Cookie**：有效期为本次会话，关闭浏览器即消失（非记住我）
- **持久 Cookie**：有效期为具体时间，关闭浏览器后仍存在（记住我）

### API

```java
// 非记住我：关闭浏览器后需重新登录
StpUtil.login(10001, false);

// 记住我（默认行为）
StpUtil.login(10001, true);

// 记住我 + 指定有效期 7 天
StpUtil.login(10001, new SaLoginParameter()
    .setIsLastingCookie(true)
    .setTimeout(60 * 60 * 24 * 7)
);
```

### 前后端分离模式

Cookie 方案在 App/小程序中无效，前端手动控制：
```javascript
// 记住我 → 持久存储
localStorage.setItem("satoken", tokenValue);
// 非记住我 → 临时存储
sessionStorage.setItem("satoken", tokenValue);
```

### 最佳实践
- Cookie 模式下 `login(id, false)` 即非记住我，`login(id, true)` 或 `login(id)` 即记住我。
- 前后端分离无 Cookie，记住我/非记住我由前端存储方式决定。
- `SaLoginParameter` 可同时设置 device、timeout、isLastingCookie 等多个参数。

---

## 2. 同端互斥登录（Mutex Login）

### 概念

类似 QQ：同一类型设备只允许单地点登录，不同类型设备允许同时在线。

### 配置

```yaml
sa-token:
  is-concurrent: false  # 关键：关闭多端同时登录
```

### API

```java
// 指定设备类型登录
StpUtil.login(10001, "PC");     // PC 登录，挤掉之前的 PC
StpUtil.login(10001, "APP");    // APP 登录，PC 不受影响

// 按设备类型注销
StpUtil.logout(10001, "PC");    // 注销 PC 端
StpUtil.logout(10001);          // 注销所有设备

// 查询当前登录设备
String device = StpUtil.getLoginDevice();

// 指定设备反查 token
String token = StpUtil.getTokenValueByLoginId(10001, "PC");
```

### 异常场景值

| 场景 | 场景值 | 含义 |
|------|--------|------|
| -4 | `BE_REPLACED` | 被顶下线（同设备新登录） |
| -5 | `KICK_OUT` | 被踢出（强制注销） |

### 最佳实践
- `is-concurrent: false` 是同端互斥的前提。不关闭则多端可同时登录，device 仅做标记。
- 前端可根据场景值 -4 显示"您的账号在其他设备登录"。
- 如需同时支持 PC + APP + 小程序多端在线，但每端只允许一个 → `is-concurrent: false` + 不同 device。

---

## 3. 账号封禁（Disable）

### 3.1 基础封禁

```java
StpUtil.disable(10001, 86400);      // 封禁 1 天
StpUtil.disable(10001, -1);         // 永久封禁

boolean isDisable = StpUtil.isDisable(10001);       // 是否被封禁
long remain = StpUtil.getDisableTime(10001);        // 剩余秒数（-1=永久，-2=未封禁）
StpUtil.untieDisable(10001);                        // 解封
StpUtil.checkDisable(10001);                        // 校验（被封禁抛 DisableServiceException）
```

> **v1.31.0+ 变更**：`StpUtil.login()` 不再自动校验封禁，需显式 `checkDisable`。

### 3.2 分类封禁（按业务标识）

```java
StpUtil.disable(10001, "comment", 86400);       // 封禁评论能力 1 天
StpUtil.disable(10001, "place-order", 604800);  // 封禁下单能力 7 天

StpUtil.checkDisable(10001, "comment");     // 抛异常
StpUtil.checkDisable(10001, "open-shop");   // 通过（未封禁）
```

### 3.3 阶梯封禁

```java
StpUtil.disableLevel(10001, 5, 86400);      // 封禁到 5 级，1 天
int level = StpUtil.getDisableLevel(10001); // 获取封禁级别（-2=未封禁）
StpUtil.checkDisableLevel(10001, 3);        // 实际级别 >= 3 则抛异常

// 分类 + 阶梯
StpUtil.disableLevel(10001, "comment", 5, 86400);
StpUtil.checkDisableLevel(10001, "comment", 3);
```

### 3.4 注解校验

```java
@SaCheckDisable                          // 校验全账号封禁
@SaCheckDisable("comment")               // 校验指定服务
@SaCheckDisable({"comment", "place-order"})  // 任一被封禁即拦截
@SaCheckDisable(level = 5)               // 阶梯：达到 5 级则拦截
@SaCheckDisable(value = "comment", level = 5)  // 分类 + 阶梯
```

### 3.5 数据库持久化

封禁信息默认存 Redis。如需查库，实现 `StpInterface.isDisabled`：

```java
@Component
public class StpInterfaceImpl implements StpInterface {
    @Override
    public SaDisableWrapperInfo isDisabled(Object loginId, String service, String loginType) {
        // v1.46.0+ 接口新增第三个参数 loginType（登录体系名）；v1.46.0 以下为 2 参
        // 查库...
        return SaDisableWrapperInfo.createDisabled(86400, 1);  // 被封禁
        // return SaDisableWrapperInfo.createNotDisabled();    // 未封禁
        // return SaDisableWrapperInfo.createNotDisabled(86400);  // 未封禁，缓存 86400 秒
    }
}
```

### 最佳实践
- **封禁前先踢下线**：`kickout(id)` → `disable(id, time)`，否则已登录用户仍可操作。
- **登录前显式校验**：`checkDisable(id)` → `login(id)`（v1.31.0+ 必须手动）。
- 分类封禁适合"封禁某项功能但允许使用其他功能"的场景（如禁言但可浏览）。

---

## 4. 二级认证（Safe Auth）

### 概念

在已登录基础上进行二次验证，用于敏感操作（如删除仓库需再次输入密码）。

### API

```java
StpUtil.openSafe(120);              // 开启二级认证，120 秒有效
boolean isSafe = StpUtil.isSafe();  // 是否在有效期内
StpUtil.checkSafe();                // 未通过抛 NotSafeException
long remain = StpUtil.getSafeTime();// 剩余秒数（-2=未开启）
StpUtil.closeSafe();                // 关闭

// 业务标识隔离（不同业务互不影响）
StpUtil.openSafe("client", 600);
StpUtil.checkSafe("shop");
```

### 完整流程

```java
// 敏感操作接口
@RequestMapping("deleteProject")
public SaResult deleteProject(String projectId) {
    if (!StpUtil.isSafe()) {
        return SaResult.error("请先完成二级认证");
    }
    // 执行业务...
    return SaResult.ok("删除成功");
}

// 二级认证接口（验证密码后开启）
@RequestMapping("openSafe")
public SaResult openSafe(String password) {
    if ("123456".equals(password)) {
        StpUtil.openSafe(120);
        return SaResult.ok("二级认证成功");
    }
    return SaResult.error("密码错误");
}
```

### 注解方式

```java
@SaCheckSafe
@RequestMapping("add")
public String add() { return "用户增加"; }

@SaCheckSafe("art")
@RequestMapping("add2")
public String add2() { return "文章增加"; }
```

### 最佳实践
- 二级认证有效期不宜过长（建议 2-5 分钟）。
- 不同业务用 service 标识隔离，避免一次认证通行所有敏感操作。

---

## 5. 身份切换（Mock Person）

### 临时切换

```java
// 方式一：手动开关
StpUtil.switchTo(10044);
// 此区间内 StpUtil.getLoginId() 返回 10044
StpUtil.endSwitch();

// 方式二：Lambda（自动结束，推荐）
StpUtil.switchTo(10044, () -> {
    System.out.println(StpUtil.getLoginId());  // 10044
    System.out.println(StpUtil.isSwitch());    // true
});
```

### 操作其它账号（不需切换身份）

```java
StpUtil.getTokenValueByLoginId(10001);          // 获取指定账号 token
StpUtil.logout(10001);                           // 注销指定账号
StpUtil.getSessionByLoginId(10001);              // 获取指定账号 Session
StpUtil.hasRole(10001, "admin");                 // 指定账号是否有角色
StpUtil.hasPermission(10001, "user.add");        // 指定账号是否有权限
```

### 最佳实践
- 优先用 Lambda 方式（`switchTo(id, () -> {...})`），避免忘记 `endSwitch()`。
- 身份切换仅影响 `getLoginId()` 等当前会话 API，不影响 Session 数据。

---

## 6. 多账号认证（Many Account）

### 方案一：StpKit 门面模式（推荐）

```java
public class StpKit {
    public static final StpLogic DEFAULT = StpUtil.stpLogic;
    public static final StpLogic ADMIN = new StpLogic("admin");
    public static final StpLogic USER = new StpLogic("user");
}
```

使用：
```java
StpKit.ADMIN.login(10001);
StpKit.USER.login(20001);
StpKit.ADMIN.checkPermission("article:add");
StpKit.USER.getSession().set("name", "zhang");
```

### 方案二：自定义 StpUtil（不推荐）

继承 `StpLogic` 复制 `StpUtil` 的全部方法并把 `loginId` 换成自定义 `TYPE`——代码冗余；仅在你**必须**脱离 StpKit 门面时才考虑，否则一律用方案一门面模式（见下方最佳实践）。

### 注解指定账号体系

```java
@SaCheckLogin(type = "user")
@RequestMapping("info")
public String info() { return "查询用户信息"; }
```

### 简化注解（自定义注解 + 注解合并）

```java
// 1. 重写注解策略支持合并
@PostConstruct
public void rewriteSaStrategy() {
    SaAnnotationStrategy.instance.getAnnotation = (element, annotationClass) ->
        AnnotatedElementUtils.getMergedAnnotation(element, annotationClass);
}

// 2. 自定义注解
@SaCheckLogin(type = "user")
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.METHOD, ElementType.TYPE})
public @interface SaUserCheckLogin {}

// 3. 使用
@SaUserCheckLogin
@RequestMapping("info")
public String info() { return "查询用户信息"; }
```

### 不同体系不同配置

```java
@PostConstruct
public void setSaTokenConfig() {
    SaTokenConfig adminConfig = new SaTokenConfig();
    adminConfig.setTokenName("satoken-admin");
    adminConfig.setTimeout(7200);
    StpUtil.stpLogic.setConfig(adminConfig);

    SaTokenConfig userConfig = new SaTokenConfig();
    userConfig.setTokenName("satoken-user");
    userConfig.setTimeout(2592000);
    StpKit.USER.setStpLogic(new StpLogic("user").setConfig(userConfig));
}
```

### 多账号混合鉴权（路由拦截）

```java
registry.addInterceptor(new SaInterceptor(handle -> {
    // Admin 或 User 任一登录即可
    SaRouter.match("/api/**").check(r -> {
        if (!StpUtil.isLogin() && !StpKit.USER.isLogin()) {
            throw new SaTokenException("请登录后再访问接口");
        }
    });
})).addPathPatterns("/**");
```

### 最佳实践
- **LoginType 不可在运行时更改**，只能在项目启动时指定。
- 推荐用 `StpKit` 门面模式，比自定义 `StpUserUtil` 更简洁。
- 同端多登录时重写 `splicingKeyTokenName` 使用不同 token 名称，防止 token 覆盖。

---

## 7. 密码加密（SaSecureUtil）

### 摘要加密

```java
SaSecureUtil.md5("123456");
SaSecureUtil.sha1("123456");
SaSecureUtil.sha256("123456");
```

### 对称加密（AES）

```java
String key = "123456";
String ciphertext = SaSecureUtil.aesEncrypt(key, "原始文本");
String plaintext = SaSecureUtil.aesDecrypt(key, ciphertext);
```

### BCrypt 加密（推荐用于密码存储）

```java
// 加密
String hash = BCrypt.hashpw("123456", BCrypt.gensalt());
// 验证
boolean match = BCrypt.checkpw("123456", hash);
// 指定加盐复杂度
String strongSalt = BCrypt.gensalt(12);
```

### TOTP 验证器

```java
String secretKey = SaTotpUtil.generateSecretKey();
String qrString = SaTotpUtil.generateGoogleSecretKey("zhangsan", secretKey);
String code = SaTotpUtil.generateTOTP(secretKey);
boolean isValid = SaTotpUtil.validateTOTP(secretKey, code, 1);  // 容差 1 个时间窗口
```

### Base64 / Base32

```java
String encoded = SaBase64Util.encode("文本");
String decoded = SaBase64Util.decode(encoded);
```

### 最佳实践
- 密码存储推荐 BCrypt（自带盐值，抗彩虹表）。
- AES 密钥不要硬编码在代码中，从配置或密钥管理服务获取。
- TOTP 适合二步验证（2FA）场景。

---

## 8. Token 风格（Token Style）

### 内置风格

| 风格 | 配置值 | 示例 |
|------|--------|------|
| uuid（默认） | `uuid` | `623368f0-ae5e-4475-a53f-93e4225f16ae` |
| uuid 无中划线 | `simple-uuid` | `6fd4221395024b5f87edd34bc3258ee8` |
| 随机 32 位 | `random-32` | `qEjyPsEA1Bkc9dr8YP6okFr5umCZNR6W` |
| 随机 64 位 | `random-64` | `v4ueNLEpPwMtmOPMBtOOeIQsvP8z9gkM...` |
| 随机 128 位 | `random-128` | 超长字符串 |
| tik 风格 | `tik` | `gr_SwoIN0MC1ewxHX_vfCW3BothWDZMMtx__` |

```yaml
sa-token:
  token-style: random-64
```

### 自定义 Token 生成策略

```java
@PostConstruct
public void rewriteSaStrategy() {
    SaStrategy.instance.createToken = (loginId, loginType) -> {
        return SaFoxUtil.getRandomString(60);
    };
}
```

### 最佳实践
- 生产环境建议 `random-64` 或 `tik`，比 uuid 更难猜测。
- 自定义策略可实现基于业务规则的 token 生成（如带前缀的 token）。

---

## 9. Token 前缀（Token Prefix）

### 配置

```yaml
sa-token:
  token-prefix: Bearer
```

### 规则

> **Token 前缀与 Token 值之间必须有一个空格**。例如：`Bearer xxxx-xxxx-xxxx-xxxx`

### Cookie 模式适配

Cookie 中无法存储空格，配置前缀后 Cookie 模式失效。解决方案：

```yaml
sa-token:
  token-prefix: Bearer
  cookie-auto-fill-prefix: true  # Cookie 自动填充前缀
```

### 最佳实践
- Token 前缀常用于前后端分离场景，前端提交 `Bearer <token>`。
- Cookie 模式下要么不配前缀，要么配 `cookie-auto-fill-prefix: true`。
- 前端读取 token 时注意裁剪前缀和空格。

---

## 10. 全局侦听器（Global Listener）

### 实现

```java
@Component
public class MySaTokenListener extends SaTokenListenerForSimple {
    @Override
    public void doLogin(String loginType, Object loginId, String tokenValue, SaLoginParameter loginParameter) {
        System.out.println("用户 " + loginId + " 登录");
    }

    @Override
    public void doLogout(String loginType, Object loginId, String tokenValue) {
        System.out.println("用户 " + loginId + " 登出");
    }

    @Override
    public void doKickout(String loginType, Object loginId, String tokenValue) {
        System.out.println("用户 " + loginId + " 被踢下线");
    }

    @Override
    public void doReplaced(String loginType, Object loginId, String tokenValue) {
        System.out.println("用户 " + loginId + " 被顶下线");
    }
}
```

### 完整事件列表

| 事件 | 方法 |
|------|------|
| 登录 | `doLogin(loginType, loginId, tokenValue, loginParameter)` |
| 注销 | `doLogout(loginType, loginId, tokenValue)` |
| 踢下线 | `doKickout(loginType, loginId, tokenValue)` |
| 顶下线 | `doReplaced(loginType, loginId, tokenValue)` |
| **注销前（v1.46.0+）** | `doBeforeLogout(loginType, loginId, tokenValue, logoutParameter)` |
| **踢下线前（v1.46.0+）** | `doBeforeKickout(loginType, loginId, tokenValue, logoutParameter)` |
| **顶下线前（v1.46.0+）** | `doBeforeReplaced(loginType, loginId, tokenValue, logoutParameter)` |
| 封禁 | `doDisable(loginType, loginId, service, level, disableTime)` |
| 解封 | `doUntieDisable(loginType, loginId, service)` |
| 开启二级认证 | `doOpenSafe(loginType, tokenValue, service, safeTime)` |
| 关闭二级认证 | `doCloseSafe(loginType, tokenValue, service)` |
| 创建 Session | `doCreateSession(id)` |
| 注销 Session | `doLogoutSession(id)` |
| 续期 | `doRenewTimeout(tokenValue, loginId, timeout)` |

> **注销前钩子用途**（v1.46.0+）：在会话真正失效前执行（如清理用户在线状态、记录操作日志）。可区分三个动作来源：登出（Logout）/ 踢下线（Kickout）/ 顶下线（Replaced）。

### 事件中心 API

```java
SaTokenEventCenter.registerListener(new MySaTokenListener());
SaTokenEventCenter.getListenerList();
SaTokenEventCenter.removeListener(listener);
SaTokenEventCenter.clearListener();
```

### 最佳实践
- **不安全代码用 try-catch 包裹**，防止异常中断 Sa-Token 整个登录流程。
- 继承 `SaTokenListenerForSimple` 只重写需要的方法，比实现完整接口更简洁。
- 加 `@Component` 后 SpringBoot 自动注册，无需手动调 `registerListener`。
- 可注册多个侦听器，按注册顺序依次执行，彼此独立。

---

## 11. 全局过滤器（Global Filter）

### 过滤器 vs 拦截器

| 特性 | 过滤器（SaServletFilter） | 拦截器（SaInterceptor） |
|------|--------------------------|------------------------|
| 执行时机 | 更靠前（DispatcherServlet 之前） | 较靠后 |
| 获取 HandlerMethod | 不支持 | 支持 |
| 异常处理 | 不进 @ExceptionHandler，必须用 setError | 进入 @ExceptionHandler |
| WebFlux 支持 | 支持（SaReactorFilter） | 不支持 |

### SpringBoot 注册

```java
@Bean
public SaServletFilter getSaServletFilter() {
    return new SaServletFilter()
        .addInclude("/**")
        .addExclude("/favicon.ico")
        .setAuth(obj -> {
            SaRouter.match("/**", "/user/doLogin", r -> StpUtil.checkLogin());
            SaRouter.match("/admin/**", r -> StpUtil.checkRole("admin"));
        })
        .setError(e -> {
            return SaResult.error(e.getMessage());
        })
        .setBeforeAuth(r -> {
            // 前置函数：所有请求都会进入（不受 include/exclude 限制）
            SaHolder.getResponse()
                .setHeader("X-Frame-Options", "SAMEORIGIN")
                .setHeader("X-XSS-Protection", "1; mode=block");
        });
}
```

### WebFlux 注册

WebFlux / Spring Cloud Gateway 项目把上方的 `SaServletFilter` 换成 `SaReactorFilter` 即可，配置项（`addInclude` / `addExclude` / `setAuth` / `setError` / `setBeforeAuth`）完全一致（强制要求见下方最佳实践「WebFlux 必须用 SaReactorFilter」）。

### 自定义响应格式

```java
.setError(e -> {
    SaHolder.getResponse()
        .setHeader("Content-Type", "application/json;charset=UTF-8");
    return JSONUtil.toJsonStr(SaResult.error(e.getMessage()));
})
```

### 最佳实践
- **过滤器异常必须用 setError**，不进 `@ExceptionHandler`。
- **前置函数 setBeforeAuth** 不受 include/exclude 限制，适合做安全头注入。
- 自定义执行顺序用 `FilterRegistrationBean`（默认 order=-100）。
- WebFlux/Gateway 必须用 `SaReactorFilter`，不能用 `SaServletFilter`。

---

## 12. HTTP Basic / Digest 认证

### Basic 认证

```yaml
sa-token:
  http-basic: sa:123456
```

```java
// 代码调用
SaHttpBasicUtil.check("sa:123456");
SaHttpBasicUtil.check();  // 用 yml 配置

// 注解
@SaCheckHttpBasic(account = "sa:123456")
@RequestMapping("test")
public SaResult test() { return SaResult.ok(); }

// 过滤器中
.setAuth(obj -> {
    SaRouter.match("/test/**", () -> SaHttpBasicUtil.check("sa:123456"));
})
```

### Digest 认证

```yaml
sa-token:
  http-digest: sa:123456
```

```java
SaHttpDigestUtil.check("sa", "123456");
SaHttpDigestUtil.check();  // 用 yml 配置

@SaCheckHttpDigest("sa:123456")
@RequestMapping("test")
public SaResult test() { return SaResult.ok(); }
```

### 最佳实践
- Digest 比 Basic 更安全（不明文传输密码）。
- 适合内部系统或 API 的简单认证，不适合面向用户的登录场景。
- URL 直接拼接：`http://sa:123456@127.0.0.1:8081/test`。

---

## 13. 配置来源自定义（v1.46.0+）

默认配置从 `application.yml` 的 `sa-token.*` 读取。v1.46.0+ 可通过 `SaStrategy.setGetSaTokenConfig` 重写配置获取策略，实现**从数据库动态读取配置**（如按租户/环境区分 timeout）：

```java
@Configuration
public class SaTokenConfigSource {
    @PostConstruct
    public void rewriteGetSaTokenConfig() {
        SaStrategy.instance.setGetSaTokenConfig(loginType -> {
            // 从数据库/配置中心读取配置，返回 SaTokenConfig
            SaTokenConfig config = configService.getByLoginType(loginType);
            return config != null ? config : new SaTokenConfig();  // null 时返回默认配置
        });
    }
}
```

### 注意
- 返回 `null` 会导致 NPE，数据库查无配置时必须返回默认 `new SaTokenConfig()`。
- 同一策略对登录、踢人、封禁等所有场景生效，配置项语义与 yml 一致。
