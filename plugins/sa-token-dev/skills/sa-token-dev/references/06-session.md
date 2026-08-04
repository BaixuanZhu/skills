# Session 会话与三大作用域

## Session 三种类型
- `Account-Session`：框架为每个「账号 id」分配的 Session。
- `Token-Session`：框架为每个「token」分配的 Session。
- `Custom-Session`：以任意「特定值」作为 SessionId 分配的 Session。

三者获取到的都是 `SaSession` 对象。

## 1. Account-Session

```java
StpUtil.getSession();                       // 当前账号 Session（登录后才能调用）
StpUtil.getSession(true);                   // isCreate=是否在未创建时新建
StpUtil.getSessionByLoginId(10001);         // 指定账号 Session
StpUtil.getSessionBySessionId("xxxx-xxxx"); // 指定 SessionId，无则返回 null
```

## 2. Token-Session

```java
StpUtil.getTokenSession();                  // 当前 token 的 Session
StpUtil.getTokenSessionByToken(token);      // 指定 token 的 Session
StpUtil.getAnonTokenSession();              // 匿名 Token-Session（未登录可用）
```

> 默认未登录无法用 `getTokenSession()`。放开：配置 `tokenSessionCheckLogin=false`，或用 `getAnonTokenSession()`。

## 3. Custom-Session（如按商品 id 缓存）

```java
SaSessionCustomUtil.isExists("goods-10001");
SaSessionCustomUtil.getSessionById("goods-10001");          // 无则新建
SaSessionCustomUtil.getSessionById("goods-10001", false);   // 第二参数决定是否新建
SaSessionCustomUtil.deleteSessionById("goods-10001");
```

## 4. 在 SaSession 上存取值

```java
session.set("name", "zhang");
session.setDefaultValue("name", "zhang");   // 仅当无值时写入
session.get("name");
session.get("name", "default");             // 指定默认值
session.get("name", () -> compute());       // 无值时执行并缓存结果

// 类型转换
session.getInt("age");
session.getLong("age");
session.getString("name");
session.getModel("key", Student.class);

session.has("key");
session.delete("name");
session.clear();
session.keys();          // Set<String>

// 其它
session.getId();
session.update();        // 从持久库更新
session.logout();        // 注销此 Session
```

## 5. 三大作用域

| 作用域 | 类 | 生命周期 | 需登录 |
|---|---|---|---|
| 请求作用域 | `SaStorage` | 一次请求 | 否 |
| 会话作用域 | `SaSession` | 一次会话 | 是 |
| 全局作用域 | `SaApplication` | 全局（集成 Redis 则至 Redis 关闭） | 否 |

```java
SaHolder.getStorage().set("key", "value");      // 请求级
StpUtil.getSession().set("key", "value");        // 会话级
SaHolder.getApplication().set("key", "value");   // 全局级
```

## 常见坑
- `SaSession` 与 `HttpSession` 无任何关系，互不通。用 Sa-Token 时统一使用 `SaSession`，不要用 `HttpSession`。
- 修改 `session.getDataMap()` 里的值后需调用 `session.update()` 避免脏数据。

## Session 使用决策

| 需求 | 用哪个 Session |
|------|---------------|
| 存用户信息（跨请求共享） | `StpUtil.getSession()`（Account-Session） |
| 存 token 级别数据（如设备信息） | `StpUtil.getTokenSession()`（Token-Session） |
| 未登录时存临时数据 | `StpUtil.getAnonTokenSession()` 或配 `tokenSessionCheckLogin=false` |
| 按业务 id 缓存（如商品信息） | `SaSessionCustomUtil.getSessionById("goods-10001")`（Custom-Session） |
| 请求内传值 | `SaHolder.getStorage()`（请求作用域，请求结束销毁） |
| 全局共享数据 | `SaHolder.getApplication()`（全局作用域） |

### 最佳实践
- **不要存大对象**：Session 数据存 Redis，大对象影响性能。用户信息建议存 id，用时查库。
- **lazy 加载**：`session.get("key", () -> queryFromDb())` 无值时执行并缓存，避免每次查库。
- **修改后 update**：直接修改 `session.getDataMap()` 里的值需调 `session.update()` 同步到 Redis。
- **区分 Session 类型**：Account-Session 随账号生命周期，Token-Session 随 token 生命周期。

> **常见错误**：SaSession 与 HttpSession 混用 → 见 `10-antipattern.md` §2。
