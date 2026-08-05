# 02 · 三层架构与分层规范

> Controller / Service / Repository 分层职责、Entity / DTO / VO 分层、包命名、依赖方向。本技能只讲**框架层分层写法**；ORM 层（Mapper / BaseMapper / IService）→ mybatis-plus-dev。

## 一、三层职责（铁律：依赖单向）

```
Controller ──→ Service ──→ Repository
  (协议)        (业务)        (数据)
```

| 层 | 职责 | 禁止 |
|---|---|---|
| **Controller** | 协议适配：接 HTTP 参数、校验（`@Valid`）、调 Service、包装返回值 | 写业务逻辑、直接操作 Repository、返回 Entity |
| **Service** | 业务逻辑：编排领域规则、事务边界（`@Transactional`）、调 Repository | 直接返回 Entity 给 Controller（应转 DTO/VO）、接 HTTP 类型（`HttpServletRequest` 等） |
| **Repository** | 数据访问 | 写业务逻辑（仅数据存取） |

> **依赖方向严格单向**：Controller → Service → Repository。Repository 不允许反向调 Service（否则循环依赖）。

## 二、数据模型分层：Entity / DTO / VO

| 类型 | 位置 | 用途 | 示例字段 |
|---|---|---|---|
| **Entity** | 数据库映射 | 对应数据库表，Service 内部传递 | `id` / `createTime` / `deleted` / `version`（含数据库字段） |
| **DTO** | 服务间 / 入参 | 接收前端请求参数 | `UserCreateDTO`（`username` / `password` / `email`，带校验注解） |
| **VO** | 出参 | 返回给前端的视图对象 | `UserVO`（`id` / `username`，**不返回 password** / `deleted`） |

### 核心规则

1. **Controller 不返回 Entity**：泄漏数据库结构、产生循环引用（`@ManyToOne` 懒加载序列化触发 N+1 查询）、安全风险（泄漏敏感字段）。
2. **DTO 入、VO 出**：入参用 DTO（带校验），出参用 VO（脱敏）。
3. **Entity 不出 Service 层**：Service 内部可用 Entity，传给 Controller 前转 VO。

### 示例

```java
// ✗ 禁止：Controller 返回 Entity
@GetMapping("/{id}")
public User getUser(@PathVariable Long id) {       // User 是 Entity
    return userService.getById(id);                // 泄漏 password / deleted 等字段
}

// ✓ 推荐：Controller 返回 VO
@GetMapping("/{id}")
public UserVO getUser(@PathVariable Long id) {
    User user = userService.getById(id);
    return UserConvert.toVO(user);                 // 转 VO（脱敏）
}

// ✓ 推荐：入参用 DTO + 校验
@PostMapping
public UserVO create(@Valid @RequestBody UserCreateDTO dto) {
    return userService.create(dto);
}
```

### 转换方式（Bean 拷贝）

| 方式 | 说明 | 注意 |
|---|---|---|
| 手写 Convert 类 | `UserConvert.toVO(user)` | 最清晰、可控，字段少时首选 |
| MapStruct | 编译期生成转换代码 | 字段多、转换频繁时推荐；见 java-coding-guide-pro `06-object-mapping.md` |
| `BeanUtils.copyProperties` | 反射拷贝（Spring / Hutool） | **慎用**：字段名不一致漏拷、类型不匹配静默失败、性能差；见 java-coding-guide-pro |

> Bean 拷贝的坑（同名字段 / 浅拷贝 / 类型不匹配）属 Java 语言层，详见 **java-coding-guide-pro** `06-object-mapping.md`。本技能不重复。

## 三、包命名规约

### 推荐结构（按层分包）

```
com.app
├── Application.java                  # 主类（根包）
├── controller/                       # Controller
├── service/impl/                     # Service 接口 + 实现
├── mapper/                           # Mapper（→ mybatis-plus-dev）
├── entity/  dto/  vo/                # Entity / DTO(入参) / VO(出参)
├── config/                           # 配置类
├── exception/                        # 自定义异常 + 全局异常处理
└── common/                           # Result / PageResult / 常量 / 枚举
```

### 命名约定

| 类型 | 命名 | 示例 |
|---|---|---|
| Controller | `XxxController` | `UserController` |
| Service 接口 | `XxxService` | `UserService` |
| Service 实现 | `XxxServiceImpl` | `UserServiceImpl` |
| Mapper | `XxxMapper` | `UserMapper`（mybatis-plus-dev 范围） |
| Entity | 单数、对应表名 | `User`（表 `user`） |
| DTO | `Xxx<场景>DTO` | `UserCreateDTO` / `UserQueryDTO` |
| VO | `XxxVO` | `UserVO` / `UserDetailVO` |
| 配置类 | `XxxConfig` | `WebMvcConfig` / `RedisConfig` |
| 自定义异常 | `XxxException` | `BusinessException` |

## 四、Controller 写法规范

```java
@RestController                          // = @Controller + @ResponseBody（返回 JSON）
@RequestMapping("/api/users")            // 类级路径前缀
@RequiredArgsConstructor                 // Lombok 构造器注入（推荐）
public class UserController {
    private final UserService userService;

    @GetMapping("/{id}")                 // GET /api/users/{id}
    public Result<UserVO> getUser(@PathVariable Long id) {
        return Result.success(userService.getById(id));
    }
    // @PostMapping create(@Valid @RequestBody DTO) / @GetMapping page(PageQuery)
}
```

### Controller 禁止项（仅列三层职责表未含项）

| ✗ 禁止 | ✓ 推荐 |
|---|---|
| Controller 接 `HttpServletRequest` 取参数 | 用 `@RequestParam` / `@PathVariable` / `@RequestBody` |
| 一个方法处理多个 HTTP 方法 | 一个方法一个 HTTP 方法 + 路径 |

## 五、Service 写法规范

```java
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {
    private final UserMapper userMapper;             // ORM 层（→ mybatis-plus-dev）

    @Transactional(rollbackFor = Exception.class)    // 事务边界在 Service（见 06-transaction.md）
    public UserVO create(UserCreateDTO dto) {
        // 业务校验 → DTO 转 Entity → userMapper.insert → Entity 转 VO
    }
}
```

> `UserMapper` / `insert` 属 mybatis-plus-dev 范围（`BaseMapper` / `IService`）。本技能只管 Service 的**事务边界 + 分层**写法，ORM 细节不碰。

## 六、RESTful 路径与 HTTP 方法约定

| 操作 | HTTP 方法 | 路径 | 示例 |
|---|---|---|---|
| 查列表 | GET | `/api/users` | `?page=1&size=10` |
| 查详情 | GET | `/api/users/{id}` | |
| 新增 | POST | `/api/users` | body = DTO |
| 全量更新 | PUT | `/api/users/{id}` | body = DTO |
| 部分更新 | PATCH | `/api/users/{id}` | body = DTO |
| 删除 | DELETE | `/api/users/{id}` | |

> **路径命名**：复数（`/users` 非 `/user`），小写，连字符分隔多词（`/user-profiles` 非 `/userProfiles`）。
