# SSO 单点登录与 OAuth2.0

## 一、SSO 单点登录

### 1. SSO 概述

在多个互相信任的系统中，用户只需登录一次，就可以访问所有系统。

### 2. 三种模式选型（关键决策）

| 系统架构 | 采用模式 | 原理 |
|:--|:--|:--|
| 前端同域 + 后端同 Redis | **模式一** | 共享 Cookie 同步会话 |
| 前端不同域 + 后端同 Redis | **模式二** | URL 重定向 + Ticket 传播会话 |
| 前端不同域 + 后端不同 Redis | **模式三** | HTTP 请求获取会话 |

**选型规则**：
- 子系统域名同属一个父域名？→ 可以模式一
- 子系统连同一个 Redis？→ 可以模式一或二
- 都不满足？→ 只能模式三

### 3. 依赖引入

**SSO-Server 端**：
```xml
<!-- 版本号请使用最新稳定版，1.40.x+ 均适用；各 sa-token-* 依赖版本保持一致 -->
<dependency>
    <groupId>cn.dev33</groupId>
    <artifactId>sa-token-spring-boot-starter</artifactId>
    <version>1.46.0</version>
</dependency>
<!-- SSO 模块 -->
<dependency>
    <groupId>cn.dev33</groupId>
    <artifactId>sa-token-sso</artifactId>
    <version>1.46.0</version>
</dependency>
<!-- Redis（必须） -->
<dependency>
    <groupId>cn.dev33</groupId>
    <artifactId>sa-token-redis-template</artifactId>
    <version>1.46.0</version>
</dependency>
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-pool2</artifactId>
</dependency>
<!-- HTTP 请求工具（模式三单点注销需要）；v1.46.0+ 可用 sa-token-rest-template / sa-token-rest-client 替代 -->
<dependency>
    <groupId>cn.dev33</groupId>
    <artifactId>sa-token-forest</artifactId>
    <version>1.46.0</version>
</dependency>
```

**SSO-Client 端**：同 Server，但模式三可去掉 `sa-token-redis-template`（不共享 Redis）。

> SpringBoot 3.x → `sa-token-spring-boot3-starter`；4.x → `sa-token-spring-boot4-starter`。

### 4. SSO-Server 搭建

```java
@RestController
public class SsoServerController {

    // 处理所有 SSO 请求：/sso/auth, /sso/doLogin, /sso/signout
    @RequestMapping("/sso/*")
    public Object ssoRequest() {
        return SaSsoServerProcessor.instance.dister();
    }

    @Autowired
    private void configSso(SaSsoServerTemplate ssoServerTemplate) {
        // 未登录时返回的视图
        ssoServerTemplate.strategy.notLoginView = () -> {
            return /* 登录页 HTML：用户名/密码输入 + doLogin() 提交 */;
        };

        // 登录处理
        ssoServerTemplate.strategy.doLoginHandle = (name, pwd) -> {
            if ("sa".equals(name) && "123456".equals(pwd)) {
                StpUtil.login(10001);
                return SaResult.ok("登录成功").setData(StpUtil.getTokenValue());
            }
            return SaResult.error("登录失败");
        };
    }
}
```

**SSO-Server 配置**：
```yaml
sa-token:
  sso-server:
    ticket-timeout: 300  # Ticket 有效期（秒），默认 5 分钟
    clients:
      sso-client1:                        # 模式一
        client: sso-client1
        allow-url: "*"
      sso-client2:                        # 模式二
        client: sso-client2
        allow-url: "*"
        secret-key: SSO-C2-kQwIOrYvnXmSDkwEiFngrKidMcdrgKor
      sso-client3:                        # 模式三
        client: sso-client3
        allow-url: "*"
        is-push: true
        push-url: http://sa-sso-client3.com:9003/sso/pushC
        secret-key: SSO-C3-kQwIOrYvnXmSDkwEiFngrKidMcdrgKor
```

> **安全警告**：`allow-url: "*"` 仅限测试。生产环境必须配置详细 URL 白名单。

### 5. SSO 模式一：共享 Cookie

**适用**：子系统域名同属一个父域名（如 `s1.stp.com`、`s2.stp.com`）。

**Server 端配置 Cookie 作用域**：
```yaml
sa-token:
  cookie:
    domain: stp.com  # 父域名共享 Cookie
```

> **重要**：模式一测完后必须注释掉 `cookie.domain`，否则影响模式二/三。

**Client 端配置**：
```yaml
sa-token:
  sso-client:
    client: sso-client1
    server-url: http://sso.stp.com:9000
  alone-redis:
    database: 1  # 必须与 Server 同 Redis
    host: 127.0.0.1
    port: 6379
```

**登录流程**：Client 重定向至 Server 登录 → Server 写入父域 Cookie（domain=stp.com）→ 重定向回 Client → Client 共享 Cookie 中的 Token + 共享 Redis 校验会话，即完成登录。

### 6. SSO 模式二：URL 重定向 + Ticket

**适用**：前端不同域，但后端共享 Redis。

**Client 端 Controller**：
```java
@RestController
public class SsoClientController {

    @RequestMapping("/sso/*")
    public Object ssoRequest() {
        return SaSsoClientProcessor.instance.dister();
    }
}
```

**Client 端配置**：
```yaml
sa-token:
  sso-client:
    client: sso-client2
    server-url: http://sa-sso-server.com:9000
    secret-key: SSO-C2-kQwIOrYvnXmSDkwEiFngrKidMcdrgKor  # 与 Server 一致
  alone-redis:
    database: 1  # 必须与 Server 同 Redis
    host: 127.0.0.1
    port: 6379
```

**登录流程**：
```
1. 用户在子系统点击登录 → /sso/login?back=xxx
2. 子系统重定向至 Server → /sso/auth?redirect=xxx
3. 用户在 Server 登录页输入账号密码
4. 登录成功 → Server 生成 ticket → 重定向回 Client → /sso/login?back=xxx&ticket=xxx
5. Client 用 ticket 从 Redis 中取账号 id → 在子系统登录
6. 重定向回 back 页面
```

> 第二次登录时（Server 已有会话），步骤 3-4 自动化，实现单点登录。

### 7. SSO 模式三：HTTP 请求获取会话

**适用**：前端不同域，后端也不共享 Redis。

**Client 端关键配置**：
```yaml
sa-token:
  sso-client:
    client: sso-client3
    server-url: http://sa-sso-server.com:9000
    is-http: true  # 模式三核心：用 HTTP 请求校验 ticket
    secret-key: SSO-C3-kQwIOrYvnXmSDkwEiFngrKidMcdrgKor

spring:
  redis:        # Client 自己的 Redis（与 Server 不同）
    database: 3
    host: 127.0.0.1
    port: 6379
```

**模式三特点**：
- Client 不直连 Redis 校验 ticket，而是通过 HTTP 请求 Server 校验。
- Client 需自行维护子会话。
- 单点注销需额外代码（跨 Redis 无法自动同步）。

### 8. SSO 前后端分离

**Client 端新增接口**：
```java
@RestController
public class H5Controller {

    @RequestMapping("/sso/isLogin")
    public Object isLogin() {
        return SaResult.data(StpUtil.isLogin())
            .set("loginId", StpUtil.getLoginIdDefaultNull());
    }

    @RequestMapping("/sso/getSsoAuthUrl")
    public SaResult getSsoAuthUrl(String clientLoginUrl) {
        String serverAuthUrl = SaSsoClientUtil.buildServerAuthUrl(clientLoginUrl, "");
        return SaResult.data(serverAuthUrl);
    }

    @RequestMapping("/sso/doLoginByTicket")
    public SaResult doLoginByTicket(String ticket) {
        SaCheckTicketResult ctr = SaSsoClientProcessor.instance.checkTicket(ticket);
        StpUtil.login(ctr.loginId, new SaLoginParameter()
            .setTimeout(ctr.remainTokenTimeout)
            .setDeviceId(ctr.deviceId)
        );
        return SaResult.data(StpUtil.getTokenValue());
    }
}
```

**前端流程**：
```
1. 用户点击登录 → 跳转 sso-login.html?back=当前页面
2. 检查 URL 是否有 ticket 参数
3. 无 ticket → 调 /sso/getSsoAuthUrl 获取 Server 地址 → 重定向
4. 有 ticket → 调 /sso/doLoginByTicket 完成登录
5. 登录成功 → localStorage 存储 satoken → 跳回 back 页面
```

### 9. SSO 单点注销

| 类型 | 说明 |
|:--|:--|
| 单端注销 | 只在当前应用注销，其它不受影响 |
| 全端注销 | 一处注销，全端下线（需 isSlo=true） |

```java
// 单端注销
@RequestMapping("/sso/logoutByAlone")
public Object logoutByAlone() {
    StpUtil.logout();
    return SaSsoClientProcessor.instance._ssoLogoutBack(
        SaHolder.getRequest(), SaHolder.getResponse());
}

// 全端注销：调用 /sso/logout?back=self
```

**全端注销链路**：Client 向 Server 发注销请求 → Server 遍历所有 Client 推送下线通知 → Server 自身注销 → 全端下线。

### 10. SSO 核心类速查

| 类名 | 说明 |
|:--|:--|
| `SaSsoServerProcessor` | Server 处理器（`instance.dister()` 分发请求） |
| `SaSsoServerTemplate` | Server 模板（配置策略） |
| `SaSsoClientProcessor` | Client 处理器（`instance.dister()` 分发请求） |
| `SaSsoClientConfig` | Client 配置类 |
| `SaSsoClientUtil` | Client 工具类（`buildServerAuthUrl()`） |
| `SaCheckTicketResult` | Ticket 校验结果（`loginId`、`remainTokenTimeout`、`deviceId`） |

---

## 二、OAuth2.0

### 11. OAuth2 概述

OAuth2 相比 SSO 增加了对**应用授权范围**的控制，适合搭建对外开放平台。

### 12. 四种授权模式

| 模式 | 说明 | 适用场景 |
|:--|:--|:--|
| **授权码** | Server 下发 Code，Client 用 Code 换 Token | 标准模式，最常用 |
| **隐藏式** | Server 直接下放 Access-Token 到 Client 页面 | 无后端的纯前端应用 |
| **密码式** | Client 直接拿用户账号密码换 Token | 高度信任的第一方应用 |
| **客户端凭证** | Server 对 Client 级别的 Token | 应用自身资源授权 |

### 13. OAuth2-Server 搭建

**依赖**：
```xml
<dependency>
    <groupId>cn.dev33</groupId>
    <artifactId>sa-token-oauth2</artifactId>
    <version>1.46.0</version>
</dependency>
```

**Controller**：
```java
@RestController
public class SaOAuth2ServerController {

    @RequestMapping("/oauth2/*")
    public Object request() {
        return SaOAuth2ServerProcessor.instance.dister();
    }

    @Autowired
    public void configOAuth2Server(SaOAuth2ServerConfig oauth2Server) {
        // 添加 client
        oauth2Server.addClient(
            new SaClientModel()
                .setClientId("1001")
                .setClientSecret("aaaa-bbbb-cccc-dddd-eeee")
                .addAllowRedirectUris("*")
                .addContractScopes("openid", "userid", "userinfo")
                .addAllowGrantTypes(
                    GrantType.authorization_code,
                    GrantType.implicit,
                    GrantType.refresh_token,
                    GrantType.password,
                    GrantType.client_credentials
                )
        );

        // 登录视图
        SaOAuth2Strategy.instance.notLoginView = () -> { /* 返回登录页 HTML */ };
        // 登录处理
        SaOAuth2Strategy.instance.doLoginHandle = (name, pwd) -> { /* 登录逻辑 */ };
        // 授权确认视图
        SaOAuth2Strategy.instance.confirmView = (clientId, scopes) -> { /* 返回确认页 HTML */ };
    }
}
```

> Client 也可用 YAML 配置替代代码方式（`sa-token.oauth2-server.clients.<id>` 下配 client-id/client-secret/allow-redirect-uris/contract-scopes/allow-grant-types，与上方 Java 字段一一对应）。

### 14. 授权码模式流程

**步骤 1：获取授权码**
```
GET /oauth2/authorize?response_type=code&client_id=1001&redirect_uri=https://example.com&scope=openid
```

**步骤 2：用 Code 换 Token**
```
GET /oauth2/token?grant_type=authorization_code&client_id=1001&client_secret=aaaa-bbbb-cccc-dddd-eeee&code={code}
```

**Token 响应**：
```json
{
  "access_token": "cAls8jnBLmeo5yuCUMwb8zxaSsQPPzGINXF3NOCjCqFHplr6hagdT6A5HeR2",
  "refresh_token": "L2rPbJ3aaOXwaB4Zu0EGWNz5EjVNpw5u2oMP9CS2IEap7rR3Hb76ZqqHS07J",
  "expires_in": 7199,
  "refresh_expires_in": 2591999,
  "scope": "openid",
  "openid": "ded91dc189a437dd1bac2274be167d50"
}
```

### 15. 数据库模式

实现 `SaOAuth2DataLoader` 接口：
```java
@Component
public class SaOAuth2DataLoaderImpl implements SaOAuth2DataLoader {
    @Override
    public SaClientModel getClientModel(String clientId) {
        // 查库返回 Client 信息
    }

    @Override
    public String getOpenid(String clientId, Object loginId) {
        // 查库返回 openid
    }
}
```

### 16. OAuth2 核心类速查

| 类名 | 说明 |
|:--|:--|
| `SaOAuth2ServerProcessor` | Server 处理器（`instance.dister()`） |
| `SaOAuth2ServerConfig` | 配置类（`addClient()`） |
| `SaOAuth2Strategy` | 策略类（`notLoginView`、`doLoginHandle`、`confirmView`） |
| `SaClientModel` | Client 模型 |
| `SaOAuth2DataLoader` | 数据加载器接口 |
| `GrantType` | 授权模式枚举 |

---

## 三、SSO vs OAuth2 选型

| 功能点 | SSO | OAuth2 |
|:--|:--|:--|
| 统一认证 | 强 | 强 |
| 统一注销 | 强 | 弱 |
| 多系统会话一致性 | 强一致 | 弱一致 |
| 第三方应用授权管理 | 不支持 | 强 |
| Client 级权限校验 | 不支持 | 强 |
| 集成简易度 | 较简单 | 中等 |
| **适合项目** | **企业内部多系统整合** | **对外开放平台** |

**选型建议**：
- 企业内部多系统整合 → **SSO**
- 对外提供开放平台服务、第三方授权 → **OAuth2**
- 两者都需要 → SSO 做内部 + OAuth2 做外部

---

## 最佳实践总结

1. **模式选型先判**：前端是否同域 + 后端是否同 Redis → 决定 SSO 模式。
2. **allow-url 生产必配**：测试用 `"*"`，生产必须详细 URL 白名单。v1.46.0+ 已修复 `redirect` 参数绕过 `allow-url` 校验的漏洞，但**白名单仍然必须**（Open Redirect 风险依然存在）。
3. **secret-key 一致**：Client 和 Server 的 secret-key 必须一致。
4. **alone-redis 同库**：模式一/二的 Client 和 Server 必须连同一个 Redis。
5. **模式一 cookie.domain 测完即删**：影响模式二/三。
6. **OAuth2 数据库模式**：生产环境用 `SaOAuth2DataLoader` 从数据库加载 Client 信息，不要硬编码。
7. **跨域处理**：前后端分离 SSO 需处理 CORS（见 `09-pitfalls.md` §6）。
