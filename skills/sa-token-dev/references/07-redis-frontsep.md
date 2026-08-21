# 集成 Redis 与前后端分离

## 一、集成 Redis

默认数据存内存（最快，但重启丢失、无法分布式共享）。集成 Redis 做到重启不丢 + 多节点会话一致。

### 1. 依赖

```xml
<!-- Sa-Token 整合 RedisTemplate（官方推荐） -->
<!-- 版本由 sa-token.version 统一管理（见 01-setup.md §0） -->
<dependency>
    <groupId>cn.dev33</groupId>
    <artifactId>sa-token-redis-template</artifactId>
    <version>${sa-token.version}</version>
</dependency>
<!-- Redis 连接池 -->
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-pool2</artifactId>
</dependency>
```

Gradle：`implementation "cn.dev33:sa-token-redis-template:${saTokenVersion}"` <!-- 版本由 saTokenVersion 统一管理（见 01-setup.md §0） -->

> Redis 集成包与 starter 共用同一 `sa-token.version`，勿单独指定版本。

### 2. 配置 Redis 连接（必须）

```yaml
spring:
  data:             # SB3.x / SB4.x 前缀；SB2.x 用 spring.redis
    redis:
      database: 1
      host: 127.0.0.1
      port: 6379
      # password:
      timeout: 10s
      lettuce:
        pool:
          max-active: 200
          max-wait: -1ms
          max-idle: 10
          min-idle: 0
```

### 3. 要点
- 引入依赖 + 配好 Redis 连接即可，**框架自动保存**，所有上层 API 不变。
- 默认以 JSON 格式存储（`sa-token-redis-template` 内部 `String 序列化 → JSON 序列化`，实跑确认序列化器为 `SaSerializerTemplateForJson`）。可换 Fastjson2/Snack3（引对应 `sa-token-redis-fastjson2` 等依赖）；或自定义 String 序列化（`SaManager.setSaSerializerTemplate(...)`）。

> **序列化安全（v1.46.0+）**：多态反序列化 RCE 已修复——业务实体默认**不在**类型白名单内，存入 Session 后反序列化会报「无法反序列化的类型，请先注册到 JSON 全局类型白名单」。注册白名单三种方式（任选其一）：
> 1. **实体实现 `SaJsonType` 标记接口（推荐，零配置）**：`public class SysUser implements SaJsonType {...}`，自动入白名单。
> 2. **启动前注册**：在 `main` 方法里、`SpringApplication.run` **之前**调 `SaJsonStrategy.instance.registerAllowType(SysUser.class)`。⚠️ **`@PostConstruct` 时机太晚**——集成 Redis 时 JSON 插件已初始化，会报「已初始化，无法再注册」。
> 3. **SPI 文件**：`resources/META-INF/satoken/sa-json-type.list` 按行写完整类名（`#` 开头为注释）。
> 白名单首次构建 JSON 插件时初始化，之后不可再注册；`fastjson2`/`snack3`/`fory-json` 默认不写类型信息，一般无此问题。

---

## 二、前后端分离（无 Cookie 模式）

App/小程序无 Cookie，需手动传递 token：后端返回 token，前端存本地，每次请求塞进 header。

### 1. 后端返回 token

```java
@RequestMapping("doLogin")
public SaResult doLogin() {
    StpUtil.login(10001);
    SaTokenInfo tokenInfo = StpUtil.getTokenInfo();  // 含 tokenName 与 tokenValue
    return SaResult.data(tokenInfo);
}
```

### 2. 前端提交 token（塞进 header，格式 {tokenName: tokenValue}）

```js
// uni-app 示例
uni.request({
    url: 'https://www.example.com/request',
    header: {
        "content-type": "application/x-www-form-urlencoded",
        "satoken": uni.getStorageSync('tokenValue')  // 参数名即 tokenName，默认 satoken
    },
    success: (res) => { console.log(res.data); }
});
```

更灵活写法（tokenName 也从后端返回值动态取）：
```js
var header = { "content-type": "application/x-www-form-urlencoded" };
var tokenName = uni.getStorageSync('tokenName');
var tokenValue = uni.getStorageSync('tokenValue');
if (tokenName) header[tokenName] = tokenValue;
```

> token 传递逻辑应封装进统一请求函数，避免每个请求重复写。
> 本质上 Cookie 只是一个特殊 header，无 Cookie 模式即手动模拟这一过程。

## 三、Redis 部署模式

### 单机模式（开发）

```yaml
spring:
  data:           # SB3.x
    redis:
      host: 127.0.0.1
      port: 6379
      database: 1
```

### 集群模式（生产）

```yaml
spring:
  data:
    redis:
      cluster:
        nodes: 192.168.1.1:6379, 192.168.1.2:6379, 192.168.1.3:6379
        max-redirects: 3
      lettuce:
        pool:
          max-active: 200
          max-wait: -1ms
          max-idle: 10
          min-idle: 0
```

### 权限缓存与业务缓存隔离（Alone-Redis）

```yaml
sa-token:
  alone-redis:        # Sa-Token 专用
    database: 2
    host: 127.0.0.1
    port: 6379

spring:
  data:
    redis:            # 业务用
      database: 0
      host: 127.0.0.1
      port: 6379
```

> Redisson 用户（非 RedisTemplate）做权限/业务缓存隔离时，用 v1.46.0+ 新增的 `sa-token-alone-redisson` 插件（见 `14-plugin.md` §8）。

## 最佳实践
- **生产必须集成 Redis**：内存模式重启丢失、无法分布式共享。
- **Redis 前缀注意版本**：SB2.x `spring.redis`，SB3.x `spring.data.redis`。
- **版本一致**：`sa-token-redis-template` 版本与 starter 保持一致。
- **序列化**：默认 JSON（Jackson），可换 Fastjson2（引 `sa-token-fastjson2`）。
- **连接池**：必须引 `commons-pool2`，配置 `lettuce.pool.*` 参数。
- **前后端分离**：token 传递封装进统一请求函数，参数名即 `tokenName`（默认 `satoken`）。
- **v1.46.0+**：`searchData` 改用 SCAN（大库不再阻塞）；RedisTemplate Dao 可重写 `wrapKey` 自定义键前缀。

> **常见错误**：Redis 前缀配错、前后端分离未返回 tokenValue → 见 `10-antipattern.md` §10、§3。
