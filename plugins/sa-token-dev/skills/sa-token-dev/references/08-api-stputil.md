# StpUtil 常用 API 速查

> Sa-Token 核心工具类，大多数功能由此提供。以下为高频 API 速查，高级用法见 `11-advanced.md`。

## 登录 / 注销

```java
StpUtil.login(10001);                 // 登录
StpUtil.login(10001, "APP");          // 登录并指定设备类型
StpUtil.login(10001, true);           // 登录并 [记住我]
StpUtil.login(10001, 86400);          // 登录并指定本次 token 有效期（秒）
StpUtil.logout();                     // 当前会话注销
StpUtil.logout(10001);                // 按账号 id 注销
StpUtil.logout(10001, "PC");          // 按账号 id + 设备类型注销
```

## 踢人 / 顶人下线

```java
StpUtil.kickout(10001);               // 踢人下线（按账号 id）
StpUtil.kickout(10001, "PC");         // 踢指定设备
StpUtil.kickoutByTokenValue(token);   // 按 token 踢
StpUtil.replaced(10001, "PC");        // 顶人下线（同端互斥）
StpUtil.logoutByTokenValue(token);    // 按 token 强制注销
```

> 区别：注销=正常退出；踢下线(KICK_OUT)/顶下线(BE_REPLACED)=被动下线，场景值不同（见 09-pitfalls）。

## 会话查询

```java
StpUtil.isLogin();                    // 是否已登录
StpUtil.isLogin(10001);               // 指定账号是否已登录
StpUtil.checkLogin();                 // 未登录抛异常
StpUtil.getLoginId();                 // 当前账号 id（未登录抛异常）
StpUtil.getLoginIdAsLong();           // 转 long
StpUtil.getLoginIdDefaultNull();      // 未登录返回 null
StpUtil.getLoginIdByToken(token);     // token 反查账号 id
```

## Token 信息

```java
StpUtil.getTokenValue();              // 当前 token 值
StpUtil.getTokenName();               // token 名称
StpUtil.getTokenInfo();               // token 详细参数
StpUtil.getTokenTimeout();            // token 剩余有效期（秒）
StpUtil.renewTimeout(timeout);        // 对当前 token 续期
```

## id 反查 token / 设备

```java
StpUtil.getTokenValueByLoginId(10001);        // 账号 id 对应的 token
StpUtil.getTokenValueListByLoginId(10001);    // token 集合
StpUtil.getTerminalListByLoginId(10001);      // 已登录设备信息集合
```

## 角色 / 权限（详见 03-permission）

```java
StpUtil.hasRole("admin");
StpUtil.checkRole("admin");
StpUtil.hasPermission("user.add");
StpUtil.checkPermission("user.add");
```

## Session（详见 06-session）

```java
StpUtil.getSession();                 // Account-Session
StpUtil.getTokenSession();            // Token-Session
```

## 账号封禁

```java
StpUtil.disable(10001, 1200);              // 封禁账号 1200 秒
StpUtil.isDisable(10001);                  // 是否被封禁
StpUtil.getDisableTime(10001);             // 剩余封禁时间（-1=永久，-2=未封禁）
StpUtil.untieDisable(10001);               // 解封
// 分类封禁（按业务标识）
StpUtil.disable(10001, "comment", 86400);
StpUtil.checkDisable(10001, "comment");    // 抛 DisableServiceException
```

## 二级认证

```java
StpUtil.openSafe(safeTime);           // 开启二级认证
StpUtil.isSafe();                     // 是否在二级认证有效期内
StpUtil.checkSafe();                  // 未通过抛异常
StpUtil.closeSafe();                  // 结束二级认证
```

## 身份切换

```java
StpUtil.switchTo(10044);              // 临时切换身份
StpUtil.endSwitch();                  // 结束切换
StpUtil.switchTo(10044, () -> { });   // 代码段内临时切换
```
