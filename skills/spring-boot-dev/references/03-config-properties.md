# 03 · 配置读取：`@ConfigurationProperties` vs `@Value`

> 外部化配置读取两种方式、松散绑定、SpEL、profile、静态字段注入坑、配置读不到的排障。

## 一、两种方式对比（决策表）

| 维度 | `@Value` | `@ConfigurationProperties` |
|---|---|---|
| 用途 | 单值注入 | 结构化（多字段）配置类 |
| 松散绑定 | ✗（须严格匹配 key） | ✓（`my-config` / `myConfig` / `MY_CONFIG` 互通） |
| SpEL | ✓（`#{...}`） | ✗ |
| 校验 | ✗ | ✓（`@Validated` + JSR303 约束注解） |
| 元数据（IDE 提示） | ✗ | ✓（配 `spring-boot-configuration-processor`） |
| 推荐 | 1~2 个单值 | ≥3 个字段的结构化配置 |

**选型**：1~2 个单值用 `@Value`；3 个以上 / 需校验 / 需分组的用 `@ConfigurationProperties`。

## 二、`@Value` 用法与坑

### 基本用法

```java
@Service
public class MyService {
    @Value("${app.timeout:3000}")        // 默认值 3000（冒号后）
    private long timeout;

    @Value("${app.name}")                // 无默认值，key 不存在 → 启动失败
    private String name;
}
```

### 坑 1：静态字段注入失效

```java
// ✗ 失效：@Value 不能直接注入静态字段（启动期 Spring 注入时静态字段已初始化）
@Service
public class MyService {
    @Value("${app.timeout}")
    private static long timeout;         // 永远是 0
}

// ✓ 正确：通过构造器 / setter 中转
@Service
public class MyService {
    private static long timeout;

    @Value("${app.timeout:3000}")
    public void setTimeout(long timeout) {       // setter 注入（Spring 调实例方法）
        MyService.timeout = timeout;
    }
}
```

### 坑 2：松散绑定不支持

```yaml
app:
  user-name: alice                        # yml 用 kebab-case
```
```java
@Value("${app.userName}")                 // ✗ 读不到（@Value 不松散绑定）
@Value("${app.user-name}")                // ✓ 须严格匹配 yml 的 key
```

### 坑 3：SpEL 用 `#{}`（非 `${}`）

```java
@Value("#{systemProperties['user.home']}")        // SpEL：运行时求值
private String home;

@Value("${app.name}")                             // 占位符：配置值替换
private String name;

@Value("#{${app.values:{a:1,b:2}}}")              // SpEL + 占位符混合
private Map<String,Integer> map;
```

> **`${}` vs `#{}`**：`${}` 是属性占位符（启动时替换）；`#{}` 是 SpEL（运行时求值）。`@Value` 两者都支持，`@ConfigurationProperties` 只支持 `${}`（字段值绑定，非 SpEL）。

## 三、`@ConfigurationProperties` 用法

### 基本用法

```yaml
# application.yml
app:
  name: "MyApp"
  pool:
    max-size: 20
    min-idle: 5
    timeout: 3000
  tags:
    - dev
    - test
```

```java
@Component                               // 注册为 Bean
@ConfigurationProperties(prefix = "app") // 绑定 app.* 下的属性
@Validated                               // 开启 JSR303 校验（须引 spring-boot-starter-validation）
public class AppProperties {

    @NotBlank
    private String name;

    private Pool pool = new Pool();      // 嵌套对象（须有默认构造 + setter）
    private List<String> tags = new ArrayList<>();

    // getter / setter 必须有（松散绑定靠 setter）
    public static class Pool {
        @Min(1) @Max(100)
        private int maxSize;
        @Min(0)
        private int minIdle;
        @Positive
        private long timeout;
        // getter / setter
    }
}
```

### 松散绑定（relaxed binding）

`@ConfigurationProperties` 支持 key 的多种写法互通（`@Value` 不支持）：

| yml 写法 | 绑定字段 |
|---|---|
| `max-size`（kebab-case，**推荐**） | `maxSize` |
| `maxSize`（camelCase） | `maxSize` |
| `MAX_SIZE`（UPPER_SNAKE，环境变量常用） | `maxSize` |

> **推荐 yml 用 kebab-case**（`max-size`），Java 字段用 camelCase（`maxSize`）。Spring 源码与官方文档均用 kebab-case。

### `@ConfigurationProperties` + `@Bean`（第三方类）

目标类无法加 `@Component` 时（如第三方库的类），用 `@Bean` 方式绑定：

```java
@Configuration
public class AppConfig {
    @Bean
    @ConfigurationProperties(prefix = "app.pool")
    public ThreadPoolTaskExecutor appExecutor() {
        return new ThreadPoolTaskExecutor();   // Spring 把 app.pool.* set 进去
    }
}
```

### `@EnableConfigurationProperties`（注册 + 使用）

```java
// 方式 A：目标类加 @Component（自管理 Bean）—— 上文示例
// 方式 B：目标类不加 @Component，用 @EnableConfigurationProperties 注册
@Configuration
@EnableConfigurationProperties(AppProperties.class)   // 显式注册
public class AppConfig { }
```

两种二选一，**不要同时用**（否则 Bean 重复注册警告）。

## 四、Profile 与配置组合

```yaml
# application.yml（公共）
app:
  name: MyApp
  pool:
    max-size: 10

# application-prod.yml（prod 覆盖）
app:
  pool:
    max-size: 50                          # 只覆盖 max-size，其他继承公共
```

```java
@ConfigurationProperties(prefix = "app")
@Profile("prod")                          // ✗ 无效：@Profile 不作用于 @ConfigurationProperties 的绑定
public class AppProperties { }
```

> **陷阱**：`@Profile` 不影响配置文件的绑定逻辑——profile 决定**加载哪个 yml 文件**，不是决定**哪个 Properties 类生效**。要按 profile 切换配置值，写多个 `application-{profile}.yml` 覆盖同一个 key。

## 五、配置读不到的排障清单

| 症状 | 排查 |
|---|---|
| `@Value("${key}")` 启动报 `Could not resolve placeholder` | key 不存在且无默认值 → 加 `:默认值` 或确认 key 拼写 |
| `@Value` 注入为 `null` 或 0 | 静态字段（坑 1）；key 用了松散绑定但 `@Value` 不支持（坑 2） |
| `@ConfigurationProperties` 字段为 null | 缺 getter/setter；prefix 拼错；yml 缩进错 |
| profile 下的配置不生效 | profile 未激活（`--spring.profiles.active=xxx`）；yml 文件名错（须 `application-{profile}.yml`） |
| 环境变量读不到 | 环境变量名规则：点号→下划线，全大写（`APP_POOL_MAX_SIZE` → `app.pool.max-size`）；SpringBoot 2.4+ 支持环境变量松散绑定 |
| 配置改了不生效 | 用了打包进 jar 的 `application.yml`，未用外部配置；或命令行参数未传对 |

## 六、配置元数据（IDE 提示，可选）

```xml
<!-- pom.xml：生成配置元数据，IDE 才能提示 application.yml 的 key -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-configuration-processor</artifactId>
    <optional>true</optional>
</dependency>
```

加完依赖编译后，IDE 在 yml 里输入 `app.` 会有自动补全 + Javadoc 提示（从 `@ConfigurationProperties` 类的 Javadoc 生成）。
