# 01 · 启动类与配置加载

> 主类位置、`@SpringBootApplication` 组合语义、组件扫描、profile 激活、配置文件加载顺序。启动失败 / Bean 找不到 / 配置不生效先查本文。

## 一、主类位置（最高频启动坑）

### 规则：主类须在**根包**

`@SpringBootApplication` 默认扫描**主类所在包及其子包**。主类不在根包 → 大量 Bean 找不到。

```
✗ com.app/
     ├── controller/UserController     ← 扫不到（在 bootstrap 同级，非子包）
     ├── service/UserService           ← 扫不到
     └── bootstrap/Application         ← 主类在此，只扫 bootstrap.*

✓ com.app/
     ├── Application                   ← 主类在根包，扫 com.app.* 全部
     ├── controller/UserController     ← 扫到
     └── service/UserService           ← 扫到
```

### 显式指定扫描范围（主类无法移到根包时）

```java
@SpringBootApplication(scanBasePackages = "com.app")
// 或
@ComponentScan(basePackages = {"com.app", "com.common"})
```

> **陷阱**：显式写 `@ComponentScan` 会**覆盖** `@SpringBootApplication` 自带的扫描——`@SpringBootApplication` 内含 `@ComponentScan`（无参 = 扫主类包），显式加一个 `@ComponentScan` 后默认的被替换。若显式 `@ComponentScan(basePackages="com.app.controller")`，则 service / repository 全扫不到。解法：要么不写（用默认），要么写全所有包。

## 二、`@SpringBootApplication` 组合语义

`@SpringBootApplication` = `@SpringBootConfiguration` + `@EnableAutoConfiguration` + `@ComponentScan`（无参 = 扫主类包）。

| 注解 | 作用 | 常用定制 |
|---|---|---|
| `@SpringBootConfiguration` | 标记配置类（等同 `@Configuration`） | 通常不动 |
| `@EnableAutoConfiguration` | 根据 classpath 自动装配（DataSource / MVC / Jackson 等） | `exclude` 排除不想要的 |
| `@ComponentScan` | 扫描 `@Component` / `@Service` / `@Controller` / `@Repository` / `@Configuration` | `scanBasePackages` / `excludeFilters` |

### 排除自动装配（启动报错时常用）

```java
// 排除数据源自动装配（项目暂时不要数据库）
@SpringBootApplication(exclude = {
    DataSourceAutoConfiguration.class,
    HibernateJpaAutoConfiguration.class
})
// 排除后仍报错？用 excludeName 写全限定名（避免类不在 classpath 时编译失败）
@SpringBootApplication(excludeName = {
    "org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration"
})
```

**何时需要排除**：启动报 `Failed to determine a suitable driver class`（引了数据库 starter 但没配数据源）→ 排除 `DataSourceAutoConfiguration`，或配数据源。

## 三、Profile 激活与配置文件加载

### profile 激活方式（优先级从高到低）

| 方式 | 示例 | 场景 |
|---|---|---|
| 命令行参数 | `java -jar app.jar --spring.profiles.active=prod` | 生产部署最常用 |
| 环境变量 | `SPRING_PROFILES_ACTIVE=prod`（下划线 = 大写点号分隔） | Docker / K8s |
| `application.yml` | `spring.profiles.active: dev` | **默认值**（被上述覆盖） |
| JVM 参数 | `-Dspring.profiles.active=prod` | 调试 |

### 配置文件加载顺序（高覆盖低）

SpringBoot 加载多份配置，**后者覆盖前者**（精确：按优先级，高的覆盖低的）：

1. 命令行 `--key=value`
2. `SPRING_APPLICATION_JSON`（环境变量里的 JSON）
3. `ServletConfig` / `ServletContext` init param
4. JNDI
5. Java 系统属性 `-Dkey=value`
6. 操作系统环境变量
7. `application-{profile}.yml` / `.properties`（**外部**，jar 包同目录的 config/ 子目录或当前目录）
8. `application-{profile}.yml` / `.properties`（**jar 内**，classpath:config/）
9. `application-{profile}.yml` / `.properties`（jar 内，classpath 根）
10. `application.yml` / `.properties`（无 profile，最低）

> **常见误判**：「我在 `application.yml` 写了 `server.port: 8080`，又在 `application-dev.yml` 写了 `server.port: 9090`，启动后为什么是 8080？」——因为 profile 没激活。须 `--spring.profiles.active=dev` 才会加载 `application-dev.yml`。

### profile 不激活时的默认

- 不指定 profile → 只加载 `application.yml`，**不加载** `application-dev.yml`。
- `spring.profiles.active: dev` 写在 `application.yml` → 始终激活 dev（除非命令行覆盖）。
- 多 profile：`--spring.profiles.active=dev,redis`（逗号分隔，后者覆盖前者）。

## 四、`@Profile` 条件装配

```java
@Configuration
@Profile("prod")          // 仅 prod 激活此配置类
public class ProdConfig { ... }

@Configuration
@Profile("!prod")         // 非 prod 激活
public class DevConfig { ... }

@Service
@Profile({"dev", "test"}) // dev 或 test 激活
public class MockEmailService { ... }
```

> **`@Profile` vs `@ConditionalOnProperty`**：`@Profile` 按 profile 名匹配；`@ConditionalOnProperty` 按配置项值匹配。前者粒度粗（整组配置），后者粒度细（单开关）。见 `10-condition-bean.md`。

## 五、启动失败速查（启动类相关）

| 报错 | 根因 | 解法 |
|---|---|---|
| `Failed to determine a suitable driver class` | 引数据库 starter 但无数据源 | 排除 `DataSourceAutoConfiguration`，或配 `spring.datasource` |
| `BeanNotFoundException` / `NoSuchBeanDefinitionException` | 主类不在根包 / `@ComponentScan` 覆盖默认 / 缺 `@Component` | 移主类到根包；检查扫描配置 |
| `ClassNotFoundException: javax.xxx` | 3.x 用了 `javax.*` | 改 `jakarta.*` |

> 完整启动报错速查（循环依赖 / 端口占用 / 数据源错误 / MyBatis Bean 等）见 `12-pitfalls.md` 第二节。

