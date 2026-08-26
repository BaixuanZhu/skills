# 权限认证与角色认证

> 核心：`StpInterface.getPermissionList / getRoleList` 返回的集合是 `StpUtil.checkPermission / checkRole` 的**检查源**——校验是否通过，取决于集合中是否包含对应权限码/角色。本文件只讲如何提供这个集合、如何校验；集合怎么来（库表设计、权限建模）是业务侧的事。

## 1. 实现权限数据源 StpInterface（必做）

```java
@Component  // 必须被 SpringBoot 扫描
public class StpInterfaceImpl implements StpInterface {

    // 返回一个账号拥有的权限码集合
    @Override
    public List<String> getPermissionList(Object loginId, String loginType) {
        // 实际项目按业务查库
        List<String> list = new ArrayList<>();
        list.add("user.add");
        list.add("user.update");
        list.add("art.*");
        return list;
    }

    // 返回一个账号拥有的角色标识集合
    @Override
    public List<String> getRoleList(Object loginId, String loginType) {
        List<String> list = new ArrayList<>();
        list.add("admin");
        list.add("super-admin");
        return list;
    }
}
```

- `loginId`：即 `StpUtil.login(id)` 写入的唯一标识。
- `loginType`：账号体系标识（多账号认证用，单账号可忽略）。
- 该接口不在启动时执行，**每次鉴权时才调用** → 生产环境必须缓存（见 §6）。

## 2. 权限校验 API

```java
StpUtil.getPermissionList();                    // 当前账号权限集合
StpUtil.hasPermission("user.add");              // 判断，返回 true/false
StpUtil.checkPermission("user.add");            // 校验，失败抛 NotPermissionException
StpUtil.checkPermissionAnd("user.add", "user.get");  // 必须全部通过
StpUtil.checkPermissionOr("user.add", "user.get");   // 满足其一即可
```

## 3. 角色校验 API（与权限独立）

```java
StpUtil.getRoleList();
StpUtil.hasRole("super-admin");            // 返回 true/false
StpUtil.checkRole("super-admin");          // 失败抛 NotRoleException
StpUtil.checkRoleAnd("super-admin", "shop-admin");
StpUtil.checkRoleOr("super-admin", "shop-admin");
```

- **角色不自动继承权限**：`checkRole` 只查 `getRoleList`，与 `getPermissionList` 无任何关联。若角色需对应权限，须在业务侧把角色映射的权限码算进 `getPermissionList` 的返回值。

## 4. 权限通配符与权限码命名

权限码统一命名 `模块.操作`（如 `user.add` / `art.update`）——通配符语义依赖该格式：

```
模块.操作     → user.add, user.delete, art.update
模块.*        → art.*（art 模块全部权限）
*.操作        → *.delete（所有模块的删除权限）
*             → 超级管理员（通过任何权限码）
```

```java
// 拥有 art.*
StpUtil.hasPermission("art.add");     // true
StpUtil.hasPermission("goods.add");   // false

// 拥有 *.delete
StpUtil.hasPermission("user.delete"); // true

// 拥有 "*" —— 通过任何权限码（角色同理）
```

> **⚠️ 通配符授权红线**：`*`（全通配）**仅限超级管理员账号**持有——它会通过任何权限码校验，普通角色一旦误配等于全站放行。`模块.*` 也应仅授予该模块的管理角色。给任何角色配通配符前，先自问"这个角色是否应该拥有该范围内未来新增的所有权限"。

## 5. 全局异常拦截

鉴权失败抛出的异常不可直接给用户看，统一拦截：
```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler
    public SaResult handler(Exception e) {
        e.printStackTrace();
        return SaResult.error(e.getMessage());
    }
}
```

> `NotPermissionException` / `NotRoleException` 均可通过 `getLoginType()` 获取是哪个 StpLogic 抛出。

## 6. 权限缓存（生产必做）

`StpInterface` 每次鉴权时调用，直接查库会产生高频 SQL。用 SaSession 缓存：

```java
@Override
public List<String> getPermissionList(Object loginId, String loginType) {
    SaSession session = StpUtil.getSessionByLoginId(loginId);
    return session.get("permissionList", () -> {
        return permissionMapper.getPermissionCodesByUserId(loginId);  // 无值时查库
    });
}
```

（Redis + TTL 缓存效果等价，任选其一。）

## 要点

- 前端按钮级权限只是辅助显示，**后端接口必须再次校验**，前端校验可被轻松绕过。

> **常见错误**：StpInterface 未加 @Component、权限校验只在前端做 → 见 `10-antipattern.md` §24、§4。
