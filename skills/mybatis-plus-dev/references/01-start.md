# 依赖与快速开始

> 适用于 MyBatis-Plus 3.5.17。核心：选对 starter → 加 `@MapperScan` → 直接用 `BaseMapper`。

## 1. 添加依赖

> **依赖通用规则**：所有坐标 `com.baomidou:mybatis-plus-*`，版本统一 3.5.17；切勿同时引入 `mybatis` / `mybatis-spring-boot-starter` / `mybatis-spring`（会与 MP 自带 MyBatis 冲突）。

**SpringBoot 2.x（Maven）**
```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-boot-starter</artifactId>
    <version>3.5.17</version>
</dependency>
```

**SpringBoot 3.x**
```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
    <version>3.5.17</version>
</dependency>
```

**SpringBoot 4.x（需 MP ≥ 3.5.13）**
```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-spring-boot4-starter</artifactId>
    <version>3.5.17</version>
</dependency>
```

**分页必引（v3.5.9+）**：
```xml
<!-- JDK11+ -->
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-jsqlparser</artifactId>
    <version>3.5.17</version>
</dependency>
<!-- JDK8 用特定版本 -->
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-jsqlparser-4.9</artifactId>
    <version>3.5.17</version>
</dependency>
```
> 不引 jsqlparser，`PaginationInnerInterceptor` 无法工作（静默失效，无报错）。

## 2. 最小配置

```java
@SpringBootApplication
@MapperScan("com.example.mapper")   // 扫描 Mapper 接口所在包
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

数据源照常配 `spring.datasource.*`（url / username / password / driver-class-name）。MP 自动接手，无需额外 `SqlSessionFactoryBean`。

## 3. 实体与 Mapper

```java
@TableName("user")
public class User {
    @TableId
    private Long id;
    private String name;
    private Integer age;
    // getter / setter 必须有
}

public interface UserMapper extends BaseMapper<User> {
    // 无需写任何方法，CRUD 已具备
}
```

## 4. 基础 CRUD 跑通

**方式一：Service 层继承（推荐）**
```java
public interface IUserService extends IService<User> {}

@Service
public class UserService extends ServiceImpl<UserMapper, User> implements IUserService {
    public List<User> listAdults() {
        return this.lambdaQuery().ge(User::getAge, 18).list();
    }
}
```

**方式二：直接注入 Mapper**
```java
@Autowired
private UserMapper userMapper;

List<User> all = userMapper.selectList(null);   // null = 无过滤条件
User u = userMapper.selectById(1L);
userMapper.insert(new User().setName("Tom").setAge(20));
userMapper.updateById(new User().setId(1L).setAge(21));
userMapper.deleteById(1L);
```

## 关键说明
- Mapper 只需 `extends BaseMapper<T>`，**不要**再去写基础 CRUD 方法（除非自定义 SQL）。
- 复杂 / 联表查询放 XML 或 `@Select`，不要用 Wrapper 硬堆 join（见 `05-wrapper.md`、`06-page.md`）。
- 配置细节（分页插件、逻辑删除、自动填充、乐观锁等）见 `02-config.md`。
- 实体字段映射、主键策略、null 处理见 `03-entity.md`。
