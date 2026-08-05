# 10 · 条件装配与自动装配

> `@Conditional` 系列、`@Profile`、自动装配机制、SpringBoot 2.x vs 3.x 自动装配文件格式差异、Bean 生命周期、自定义 starter。

## 一、`@Conditional` 系列注解

| 注解 | 条件 | 典型场景 |
|---|---|---|
| `@ConditionalOnClass` | classpath 存在指定类 | 引了某依赖才装配 |
| `@ConditionalOnMissingClass` | classpath 不存在指定类 | 未引某依赖才装配 |
| `@ConditionalOnBean` | 容器存在指定 Bean | 某 Bean 已配置才装配 |
| `@ConditionalOnMissingBean` | 容器不存在指定 Bean | 用户未自定义时给默认实现 |
| `@ConditionalOnProperty` | 配置项满足条件 | 按开关启用功能 |
| `@ConditionalOnResource` | 存在指定资源文件 | 配置文件存在才装配 |
| `@ConditionalOnWebApplication` | 是 Web 应用 | Web 环境才装配 |
| `@ConditionalOnNotWebApplication` | 非 Web 应用 | 非才装配 |
| `@ConditionalOnExpression` | SpEL 表达式为 true | 复合条件 |

### `@ConditionalOnProperty`

```java
@Configuration
@ConditionalOnProperty(
    prefix = "app.cache",
    name = "enabled",
    havingValue = "true",
    matchIfMissing = false                  // 配置项缺失时是否匹配（false=不装配）
)
public class CacheConfig { ... }
```

- `havingValue`：指定值匹配（不写则"存在即匹配"）。
- `matchIfMissing = true`：配置项**完全缺失**时也算匹配（提供默认开启）。

### `@ConditionalOnMissingBean`（自定义 starter 核心）

```java
@Configuration
public class MyStarterAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean                // 用户没自定义 MyService 时给默认实现
    public MyService myService() {
        return new DefaultMyService();
    }
}
```

> **starter 惯例**：默认 Bean 标 `@ConditionalOnMissingBean`——用户自定义的同类型 Bean 会覆盖默认的（用户优先）。

### 坑：`@ConditionalOnBean` 的顺序依赖

```java
@Configuration
public class ConfigA {
    @Bean
    public Foo foo() { return new Foo(); }
}

@Configuration
@ConditionalOnBean(Foo.class)               // ✗ 可能失效：条件求值时 Foo 可能尚未注册
public class ConfigB {
    @Bean
    public Bar bar() { return new Bar(foo); }
}
```

**原因**：`@ConditionalOnBean` 在 Bean 定义注册阶段求值，此时 `Foo` 可能还未被处理（顺序不确定）。Spring 官方文档明确警告：`@ConditionalOnBean` 依赖 Bean 定义顺序，**不可靠**。

**解法**：
```java
// 改用 @ConditionalOnClass（条件求值不依赖运行顺序）
@ConditionalOnClass(Foo.class)

// 或合并到同一配置类（同类的 @Bean 顺序确定）
@Configuration
public class ConfigAB {
    @Bean
    public Foo foo() { return new Foo(); }

    @Bean
    @ConditionalOnBean(Foo.class)           // 同类内，foo() 先注册，可靠
    public Bar bar(Foo foo) { return new Bar(foo); }
}
```

## 二、`@Profile` vs `@ConditionalOnProperty`

| 维度 | `@Profile` | `@ConditionalOnProperty` |
|---|---|---|
| 匹配依据 | profile 名（`dev` / `prod`） | 配置项值 |
| 粒度 | 整组配置（按环境切换） | 单开关（功能级） |
| 典型场景 | dev 用 H2、prod 用 MySQL | 按开关启用缓存 |

```java
// 按环境切换
@Configuration
@Profile("dev")
public class DevDataSourceConfig { ... }

// 按开关启用
@Configuration
@ConditionalOnProperty(name = "app.feature.email.enabled", havingValue = "true")
public class EmailConfig { ... }
```

## 三、自动装配机制

### `@EnableAutoConfiguration` 做什么

启动时扫描 `META-INF` 下的自动装配文件，按 `@Conditional*` 条件装配。`@SpringBootApplication` 内含 `@EnableAutoConfiguration`。

### 文件格式：SpringBoot 2.x vs 3.x（关键差异）

**SpringBoot 2.x（含 2.7）**：
```
META-INF/spring.factories

org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
  com.app.AutoConfigA,\
  com.app.AutoConfigB
```

**SpringBoot 3.x 起（3.0+）**：
```
META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports

com.app.AutoConfigA
com.app.AutoConfigB
```

> **3.x 废弃 `spring.factories` 中的 `EnableAutoConfiguration` key**。3.x 项目仍用 `spring.factories` 注册自动装配 → **不生效**（静默失效，不报错）。
>
> 3.x 的 `spring.factories` 仍可用于其他功能（`EnvironmentPostProcessor` / `ApplicationContextInitializer` 等），但**自动装配**改用 `AutoConfiguration.imports`。

### 自定义自动配置类

```java
@AutoConfiguration                          // 3.x 新注解（= @Configuration + @AutoConfigureBefore/After）
@ConditionalOnClass(MyService.class)
@ConditionalOnProperty(prefix = "my", name = "enabled", havingValue = "true", matchIfMissing = true)
@EnableConfigurationProperties(MyProperties.class)
public class MyAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public MyService myService(MyProperties props) {
        return new DefaultMyService(props);
    }
}
```

> `@AutoConfiguration`（3.0+）替代 `@Configuration`，明确标记为自动配置类，支持 `@AutoConfigureBefore` / `@AutoConfigureAfter` 控制加载顺序。2.x 用 `@Configuration` 即可。

## 四、Bean 生命周期

```
实例化（构造器）→ 属性注入 → Aware 回调 → BeanPostProcessor#BeforeInit
→ 初始化（@PostConstruct / afterPropertiesSet / initMethod）
→ BeanPostProcessor#AfterInit（AOP 代理生成）→ 使用 → 销毁（@PreDestroy）
```

### 初始化回调（三选一，优先 `@PostConstruct`）

```java
@PostConstruct                              // 推荐：标准注解，属性注入完成后、使用前执行
public void init() { ... }
// 备选：InitializingBean#afterPropertiesSet（侵入式）/ @Bean(initMethod="init")（第三方类）
```

> **隐性坑：不要在构造器里调用 `@Autowired` 字段**——构造器执行时注入未完成，字段为 null。初始化逻辑放 `@PostConstruct`。

### 命名空间

```java
import jakarta.annotation.PostConstruct;    // 3.x（jakarta）；2.x 用 javax.annotation.PostConstruct
```

## 五、排除自动装配

见 `01-startup-config.md` 第二节（`@SpringBootApplication(exclude=...)`）。本处补充：引了 `spring-boot-starter-data-jpa` 但项目用 MyBatis → 排除 JPA 自动装配避免冲突。

## 六、自定义 starter（最小示例）

```java
@AutoConfiguration                          // 3.x（= @Configuration + 顺序控制）
@ConditionalOnClass(MyService.class)
@EnableConfigurationProperties(MyProperties.class)
public class MyAutoConfiguration {
    @Bean
    @ConditionalOnMissingBean               // 用户未自定义时给默认实现（starter 惯例）
    public MyService myService(MyProperties props) { return new MyService(props); }
}
// MyProperties: @ConfigurationProperties(prefix="my"), 字段 name/timeout + getter/setter
// MyService: 普通 Bean，构造器注入 MyProperties
```

注册文件（3.x，每行一个全限定类名）：
```
# src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
com.example.auto.MyAutoConfiguration
```

> **命名约定**：第三方用 `xxx-spring-boot-starter`；官方保留 `spring-boot-starter-xxx` 前缀（勿占用）。

