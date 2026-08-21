# 集成与配置（SpringBoot）

> 适用于 Sa-Token 1.46.0+（1.40.x 及以上，核心 API 向后兼容）。核心一句话：引依赖 → （可选）配 yml → 直接用 `StpUtil`。

## 1. 添加依赖

**Maven：**
```xml
<!-- Sa-Token 权限认证 -->
<!-- 版本号请使用最新稳定版，1.40.x+ 均适用；各 sa-token-* 依赖版本保持一致 -->
<dependency>
    <groupId>cn.dev33</groupId>
    <artifactId>sa-token-spring-boot-starter</artifactId>
    <version>1.46.0</version>
</dependency>
```

- SpringBoot 3.x → 用 `sa-token-spring-boot3-starter`
- SpringBoot 4.x → 用 `sa-token-spring-boot4-starter`
- WebFlux 响应式环境 → 用 `sa-token-reactor-spring-boot-starter`（见 `13-micro-service.md`）

**Gradle：**
```gradle
// 版本号请使用最新稳定版，1.40.x+ 均适用
implementation 'cn.dev33:sa-token-spring-boot-starter:1.46.0'
```

## 2. 配置文件（可零配置启动）

`application.yml`：
```yaml
server:
  port: 8081
sa-token:
  # token 名称（同时也是 cookie 名称）
  token-name: satoken
  # token 有效期（单位：秒），默认 30 天，-1 代表永久有效
  timeout: 2592000
  # token 最低活跃频率（单位：秒），超过此时间未访问会被冻结，-1 代表永不冻结
  active-timeout: -1
  # 是否允许同一账号多地同时登录（true=一起登录，false=新登录挤掉旧登录）
  is-concurrent: true
  # 多人登录同一账号时是否共用一个 token（true=共用，false=每次登录新建）
  is-share: false
  # token 风格：uuid / simple-uuid / random-32 / random-64 / random-128 / tik
  token-style: uuid
  # 是否输出操作日志
  is-log: true
```

> `properties` 风格同名，形如 `sa-token.token-name=satoken`。

## 3. 启动类与最小示例

```java
@SpringBootApplication
public class SaTokenDemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(SaTokenDemoApplication.class, args);
        System.out.println("启动成功，Sa-Token 配置：" + SaManager.getConfig());
    }
}
```

```java
@RestController
@RequestMapping("/user/")
public class UserController {

    // http://localhost:8081/user/doLogin?username=zhang&password=123456
    @RequestMapping("doLogin")
    public String doLogin(String username, String password) {
        if ("zhang".equals(username) && "123456".equals(password)) {
            StpUtil.login(10001);   // 真实项目应先查库比对
            return "登录成功";
        }
        return "登录失败";
    }

    @RequestMapping("isLogin")
    public String isLogin() {
        return "当前会话是否登录：" + StpUtil.isLogin();
    }
}
```

## 关键说明
- `StpUtil.login(id)` 利用 Cookie 自动注入把 token 返回前端，因此 Web 端无需手写返回 token。前后端分离场景见 `07-redis-frontsep.md`。
- 完整可配置项见 `08-api-stputil.md` 及高级特性 `11-advanced.md`。

## 生产配置清单

| 配置项 | 开发默认值 | 生产建议 | 原因 |
|--------|-----------|---------|------|
| `timeout` | 2592000（30天） | 按业务定（如 86400=1天） | 过长增加 token 泄露风险 |
| `active-timeout` | -1（不限制） | 1800（30分钟） | 限制闲置会话 |
| `is-concurrent` | true | 按业务定 | 多端同时登录需评估安全 |
| `is-share` | false | false（推荐） | true 时多端共用 token，踢人语义变化 |
| `token-style` | uuid | random-64 / tik | 更难猜测 |
| `is-log` | true | false | 生产关闭日志输出 |
| Redis | 内存 | 必须集成 | 分布式场景必须 |
| `autoRenew` | true | true | active-timeout 自动续签 |

## 版本选型决策树

```
SpringBoot 版本？
├─ 2.x → sa-token-spring-boot-starter
├─ 3.x → sa-token-spring-boot3-starter（Redis 前缀 spring.data.redis）
└─ 4.x → sa-token-spring-boot4-starter

环境类型？
├─ SpringMVC (Servlet) → sa-token-spring-boot*-starter
├─ WebFlux / Gateway (Reactor) → sa-token-reactor-spring-boot*-starter
└─ 微服务网关 + 子服务 → 网关用 Reactor，子服务用 Servlet（各自单独引入）
```

> **常见错误**：Starter 混用、Redis 前缀配错、未注册 SaInterceptor → 见 `10-antipattern.md` §1、§10、§11。
