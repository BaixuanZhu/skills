# 插件

> **依赖引入通用规则**：所有插件 Maven 坐标均为 `cn.dev33:<artifactId>`，artifactId 见文末「插件汇总」表，版本与核心 sa-token 依赖保持一致。除特别说明（JWT、temp-jwt）外，下文不再逐个列依赖 XML。

## 1. JWT 整合（sa-token-jwt）

> **先明确概念：无状态与 JWT 是两个正交维度**。JWT 只是一种 token 风格（自包含/可读），不等于无状态：Simple 模式就是「JWT + Redis」的有状态方案；反过来，有状态场景用默认 `simple-uuid` token + Redis 即可，**根本无需引入本插件**。真正需要本插件的只有两类诉求：① 用户明确要 JWT 格式 token（选 Simple/Mixin）；② 无状态架构（不要 Redis，选 Stateless——这是 Sa-Token 实现无状态的唯一路径，JWT 在此只是实现手段）。只有 Mixin 是 JWT 与 Redis 两者都要。

### 1.1 依赖

```xml
<!-- 版本由 sa-token.version 统一管理（见 01-setup.md §0） -->
<dependency>
    <groupId>cn.dev33</groupId>
    <artifactId>sa-token-jwt</artifactId>
    <version>${sa-token.version}</version>
</dependency>
```

> **注意**：`sa-token-jwt` 依赖 `hutool-jwt`。项目中 hutool 版本须 >= 5.7.14，**避开 5.8.13 和 5.8.14**（存在类型转换问题）。

### 1.2 配置

```yaml
sa-token:
  jwt-secret-key: your-secret-key-do-not-copy  # 必填
```

### 1.3 三种模式（关键选型）

注入对应的 `StpLogic` Bean：

```java
@Configuration
public class SaTokenConfigure {
    @Bean
    public StpLogic getStpLogicJwt() {
        return new StpLogicJwtForSimple();       // Simple / Mixin / Stateless
    }
}
```

### 1.4 三种模式功能对比

| 功能 | Simple | Mixin | Stateless |
|------|--------|-------|-----------|
| Token 风格 | jwt | jwt | jwt |
| 登录数据存储 | Redis | Token | Token |
| Session 存储 | Redis | Redis | 无 |
| 踢人/顶人下线 | ✅ 支持 | ❌ 不支持 | ❌ 不支持 |
| active-timeout | ✅ 支持 | ✅ 支持 | ❌ 不支持 |
| id 反查 Token | ✅ 支持 | ✅ 支持 | ❌ 不支持 |
| 会话管理 | ✅ 支持 | 部分支持 | ❌ 不支持 |
| 注解/路由鉴权 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| 账号封禁 | ✅ 支持 | ✅ 支持 | ❌ 不支持 |

**选型建议**：
- **Simple（推荐）**：需要 jwt 风格 + 完整会话管理（踢人/Session）。
- **Mixin**：希望登录数据放 Token 减少 Redis 访问，仍需 Session。
- **Stateless**：完全无状态，不使用 Redis。不适用需踢人/Session/active-timeout 场景。

### 1.5 扩展参数

```java
// 登录时追加扩展参数
StpUtil.login(10001, new SaLoginParameter()
    .setExtra("name", "zhangsan")
    .setExtra("role", "admin"));

// 获取当前 Token 扩展参数
String name = StpUtil.getExtra("name");

// 获取任意 Token 的扩展参数
String name = StpUtil.getExtra("tokenValue", "name");
```

### 1.6 多账号模式 + JWT

```java
@PostConstruct
public void setUserStpLogic() {
    StpUserUtil.setStpLogic(new StpLogicJwtForSimple(StpUserUtil.TYPE));
}
```

### 1.7 注意事项
- **Simple 模式 `is-share` 恒为 `false`**：与 per-token Extra 数据不兼容。
- **Mixin 模式 `is-concurrent` 必须为 `true`**：token 不记录在持久库，无法踢/顶。
- **Mixin 模式 `max-try-times` 恒为 `-1`**：防止框架错误判断 token 唯一性。
- **v1.46.0+ 不向下兼容**：集成 JWT 时 `extraData` 禁止包含保留字段（如 `tokenValue`、`loginId` 等框架内部字段），写入会直接报错。

---

## 2. API Key 认证（sa-token-apikey）

随机字符串 Key 与用户 id 绑定；一个用户可创建多个 Key，每个 Key 可赋不同 scope 权限、可设有效期、随时删除回收。

### 2.1 创建与查询

```java
// 创建
ApiKeyModel akModel = SaApiKeyUtil.createApiKeyModel(10001).setTitle("test");
SaApiKeyUtil.saveApiKey(akModel);
String apiKey = akModel.getApiKey();  // 获取 Key 值

// 查询
ApiKeyModel model = SaApiKeyUtil.getApiKey("AK-xxx");
Object loginId = SaApiKeyUtil.getLoginIdByApiKey("AK-xxx");
List<ApiKeyModel> list = SaApiKeyUtil.getApiKeyList(10001);

// 删除
SaApiKeyUtil.deleteApiKey("AK-xxx");
```

### 2.2 校验

```java
SaApiKeyUtil.checkApiKey("AK-xxx");                    // 校验有效性
SaApiKeyUtil.checkApiKeyScope("AK-xxx", "userinfo");   // 校验 scope
boolean has = SaApiKeyUtil.hasApiKeyScope("AK-xxx", "userinfo");  // 返回 boolean
SaApiKeyUtil.checkApiKeyLoginId("AK-xxx", 10001);      // 校验归属
```

### 2.3 注解鉴权

```java
@SaCheckApiKey                                         // 必须携带有效 ApiKey
@SaCheckApiKey(scope = "userinfo")                     // 必须有 userinfo 权限
@SaCheckApiKey(scope = {"userinfo", "chat"})           // 同时具有（AND）
@SaCheckApiKey(scope = {"userinfo", "chat"}, mode = SaMode.OR)  // 任一即可
```

### 2.4 前端提交方式

```
# 方式一：请求参数或 header，参数名 apikey（全小写）
/user/getInfo?apikey=AK-xxx

# 方式二：Basic 认证格式
http://AK-xxx@localhost:8081/user/getInfo
```

### 2.5 数据库模式

```java
@Component
public class SaApiKeyDataLoaderImpl implements SaApiKeyDataLoader {
    @Override
    public Boolean getIsRecordIndex() { return false; }

    @Override
    public ApiKeyModel getApiKeyModelFromDatabase(String namespace, String apiKey) {
        return apiKeyMapper.getApiKeyModel(apiKey);
    }
}
```

### 2.6 适用场景
- **适用**：第三方应用代替用户调用特定 API，可控授权、随时回收。
- **不适用**：用户登录认证（用 `StpUtil`）。

---

## 3. API 接口签名（sa-token-sign）

### 3.1 配置

```yaml
sa-token:
  sign:
    secret-key: kQwIOrYvnXmSDkwEiFngrKidMcdrgKor  # 发起端和接收端须一致
```

### 3.2 签名原理（三重防护）

1. **sign 签名**：所有参数按字典序排列 + secretKey 计算 MD5，防篡改
2. **nonce 随机串**：32 位，一次性使用，防重放
3. **timestamp 时间戳**：限定请求有效期（默认 15 分钟），防过期重放

```
sign = md5(所有参数按字典序排列 + "&key=" + secretKey)
```

### 3.3 请求发起端

```java
Map<String, Object> paramMap = new LinkedHashMap<>();
paramMap.put("userId", 10001);
paramMap.put("money", 1000);

// 自动补全 timestamp、nonce、sign
String paramStr = SaSignUtil.addSignParamsAndJoin(paramMap);
String url = "http://b.com/api/addMoney?" + paramStr;
```

### 3.4 请求接收端

```java
@RequestMapping("addMoney")
public SaResult addMoney(long userId, long money) {
    SaSignUtil.checkRequest(SaHolder.getRequest());  // 一句校验
    return SaResult.ok();
}
```

### 3.5 注解校验

```java
@SaCheckSign                                          // 校验全部参数
@SaCheckSign(verifyParams = {"id", "name"})           // 指定参与签名的参数
@SaCheckSign(appid = "xm-shop")                       // 多应用模式
```

### 3.6 多应用模式

```yaml
sa-token:
  sign-many:
    xm-shop:
      secret-key: 0123456789abcdefg
      digest-algo: md5
    xm-forum:
      secret-key: 0123456789hijklmnopq
      digest-algo: sha256
```

### 3.7 适用场景
- **适用**：跨系统接口调用，防伪造、防篡改、防重放。
- **不适用**：浏览器到后端的常规请求（用会话 token 或 API Key）。

---

## 4. AOP 注解鉴权（sa-token-spring-aop）

默认拦截器模式只能在 **Controller 层** 使用注解；引入 AOP 插件后可在**任意层级**（Service/Manager）使用。

> **关键注意：拦截器模式和 AOP 模式不可同时使用**，否则 Controller 层注解校验两次。

### 4.1 适用场景
- **适用**：需在 Service 层等非 Controller 层做注解鉴权。
- **不适用**：只在 Controller 鉴权（用默认拦截器即可）。**绝对不要与拦截器模式同时使用。**

---

## 5. 临时 Token（sa-token-temp）

### 5.1 核心 API（已内嵌核心包）

```java
// 创建 token（有效期 200 秒）/ 解析 / 剩余有效期 / 删除
String token = SaTempUtil.createToken("10014", 200);
String value = SaTempUtil.parseToken(token, String.class);
long timeout = SaTempUtil.getTimeout(token);
SaTempUtil.deleteToken(token);

// 前缀拼接：解析时裁剪前缀，错误前缀返回 null
String token2 = SaTempUtil.createToken("shop_1001", 1200);
Long value2 = SaTempUtil.parseToken(token2, "shop_", Long.class);

// 反查：第三个参数 true = 保存 value→token 映射
SaTempUtil.createToken(10004, 1200, true);
List<String> tokens = SaTempUtil.getTempTokenList(10004);
```

### 5.2 集成 JWT（可选）

引入 `sa-token-temp-jwt` 插件（坐标规则同上），并配置 `sa-token.jwt-secret-key`（必填）。

### 5.3 适用场景
- **适用**：邀请链接、短时效授权（5 分钟~半小时）、邮件验证、临时下载链接。
- **不适用**：用户登录会话（用 `StpUtil.login()`）。

---

## 6. Alone 独立 Redis（sa-token-alone-redis）

> Spring Boot 4.x 用 `sa-token-alone-redis-by-spring-boot4` 替代。
> **Redisson 用户**（非 RedisTemplate）：v1.46.0+ 用 `sa-token-alone-redisson` 插件（支持指定 Codec，update 用 `setAndKeepTTL` 原子保留原过期时间），见 §8。

### 6.1 配置

```yaml
sa-token:
  alone-redis:        # Sa-Token 专用 Redis
    database: 2
    host: 127.0.0.1
    port: 6379

spring:
  redis:              # 业务 Redis（SB2.x）
    database: 0
    host: 127.0.0.1
    port: 6379
```

### 6.2 适用场景
- **适用**：权限数据与业务缓存物理隔离（不同 Redis 实例/database），权限数据独立扩容/备份。
- **不适用**：单 Redis 且数据量不大的项目。
- SSO 场景：Client 用 Alone-Redis 连接与 Server 同一个 Redis，业务数据用另一个。

---

## 7. SpEL 表达式注解（sa-token-spring-el）

### 7.1 使用

```java
// 登录/权限校验
@SaCheckEL("stp.checkLogin()")
@SaCheckEL("stp.checkPermission('user:edit')")

// 参数校验
@SaCheckEL("NEED( #name.length() > 3 )")
@RequestMapping("test5")
public SaResult test5(@RequestParam(defaultValue = "") String name) {
    return SaResult.ok().set("name", name);
}

// Session 取值校验
@SaCheckEL("NEED( stp.getSession().get('name') == 'zhangsan' )")
@RequestMapping("test8")
public SaResult test8() { return SaResult.ok(); }
```

### 7.2 根对象

| 根对象 | 说明 |
|--------|------|
| `stp` | 默认 StpLogic 实例 |
| `NEED(...)` | 布尔条件，true 通过 |
| `#参数名` | 方法参数引用 |
| `this.成员变量` | 本类成员变量 |

### 7.3 多账号体系

```java
@PostConstruct
public void rewriteSaStrategy() {
    SaAnnotationStrategy.instance.checkELRootMapExtendFunction = rootMap -> {
        rootMap.put("stpUser", StpUserUtil.getStpLogic());
    };
}

// 使用
@SaCheckEL("stpUser.checkLogin()")
```

### 7.4 适用场景
- **适用**：复杂条件组合鉴权（参数校验、Session 取值、自定义逻辑）。
- **不适用**：简单单一权限/角色校验（直接用 `@SaCheckPermission` / `@SaCheckRole`）。

---

## 8. v1.46.0+ 新增插件

| 插件 | 说明 |
|------|------|
| `sa-token-fory-json` | 集成 Apache Fory JSON（高性能 JSON 编解码），**不在 JSON 中写入类型信息**，用法同 Fastjson2 |
| `sa-token-rest-template` | 整合 Spring `RestTemplate` 作为 HTTP 请求处理器，SB 2/3/4 可用 |
| `sa-token-rest-client` | 整合 Spring `RestClient` 作为 HTTP 请求处理器，SB 3.2+ / Spring Framework 6.1+ 可用 |
| `sa-token-alone-redisson` | Redisson 版独立连接插件（权限缓存与业务缓存分离），含 Boot 3/4 示例 |

**典型用途**：
- **fory-json**：对 JSON 序列化有高性能要求、或不想在存储中携带类型信息时，替代默认 Jackson 序列化。
- **rest-template / rest-client**：替换 `sa-token-forest` 作为 SSO 模式三 / 单点注销的 HTTP 请求处理器（跟随项目现有 Spring HTTP 客户端技术栈）。
- **alone-redisson**：项目已用 Redisson 时，做权限缓存与业务缓存隔离（`SaTokenDaoForRedisson` 支持指定 Codec；update 改用 `setAndKeepTTL` 原子保留原过期时间，避免 TTL 偏移）。

> **安全提示**：fory-json 默认不写类型信息，配合 v1.46.0+ 的 `SaJsonStrategy` 白名单机制，多态反序列化更安全（见 `07-redis-frontsep.md`）。

---

## 插件汇总

| 插件 | artifactId | 核心场景 |
|------|------------|---------|
| JWT | `sa-token-jwt` | Token 风格替换为 JWT |
| API Key | `sa-token-apikey` | 第三方应用代替用户调 API |
| API 签名 | `sa-token-sign` | 跨系统接口防伪造/篡改/重放 |
| AOP 注解 | `sa-token-spring-aop` | Service 层注解鉴权 |
| 临时 Token | `sa-token-temp`（内嵌） | 短时效授权/邀请链接 |
| 独立 Redis | `sa-token-alone-redis` | 权限缓存与业务缓存隔离 |
| SpEL 表达式 | `sa-token-spring-el` | 复杂条件组合鉴权 |
| Fory JSON | `sa-token-fory-json`（v1.46.0+） | 高性能 JSON 序列化，不写类型信息 |
| HTTP 扩展 | `sa-token-rest-template` / `sa-token-rest-client`（v1.46.0+） | 替换 forest 的 HTTP 请求处理器 |
| 独立 Redisson | `sa-token-alone-redisson`（v1.46.0+） | Redisson 版权限/业务缓存隔离 |
