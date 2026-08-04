# 权限认证与角色认证

> 核心：实现 `StpInterface` 告诉框架每个账号拥有的「权限码」和「角色」集合，再用 `StpUtil.checkXxx` 校验。

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
- 该接口不在启动时执行，每次鉴权时才调用。

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

## 4. 权限通配符

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

## 要点
- 前端按钮级权限只是辅助显示，**后端接口必须再次校验**，前端校验可被轻松绕过。

## RBAC 设计模式

### 权限码命名规范

```
模块.操作     → user.add, user.delete, art.update
模块.*        → art.*（art 模块全部权限）
*.操作        → *.delete（所有模块的删除权限）
*             → 超级管理员（通过任何权限码）
```

### 典型 RBAC 实现

```java
@Component
public class StpInterfaceImpl implements StpInterface {
    @Autowired
    private RoleMapper roleMapper;
    @Autowired
    private PermissionMapper permissionMapper;

    @Override
    public List<String> getPermissionList(Object loginId, String loginType) {
        // 1. 查用户角色
        List<String> roleIds = roleMapper.getRoleIdsByUserId(Long.parseLong(loginId.toString()));
        // 2. 查角色对应权限码
        return permissionMapper.getPermissionCodesByRoleIds(roleIds);
    }

    @Override
    public List<String> getRoleList(Object loginId, String loginType) {
        return roleMapper.getRoleCodesByUserId(Long.parseLong(loginId.toString()));
    }
}
```

### 权限缓存优化

`StpInterface` 每次鉴权时调用，频繁查库影响性能。优化方案：

```java
@Override
public List<String> getPermissionList(Object loginId, String loginType) {
    // 方案一：Sa-Token Session 缓存
    SaSession session = StpUtil.getSessionByLoginId(loginId);
    return session.get("permissionList", () -> {
        return permissionMapper.getPermissionCodesByUserId(loginId);  // 无值时查库
    });

    // 方案二：Redis 缓存 + TTL
    // String key = "perm:" + loginId;
    // List<String> list = redisTemplate.opsForValue().get(key);
    // if (list == null) { list = permissionMapper...; redisTemplate.set(key, list, 30, MINUTES); }
    // return list;
}
```

### 最佳实践
- **权限码统一命名**：`模块.操作` 格式，便于通配符匹配。
- **缓存权限列表**：`StpInterface` 每次鉴权调用，务必缓存。
- **角色和权限独立**：角色不自动继承权限，需在 `getPermissionList` 中查角色对应权限。
- **通配符 * 谨慎使用**：拥有 `*` 表示通过任何权限码校验，仅限超级管理员。

> **常见错误**：StpInterface 未加 @Component、权限校验只在前端做 → 见 `10-antipattern.md` §24、§4。
