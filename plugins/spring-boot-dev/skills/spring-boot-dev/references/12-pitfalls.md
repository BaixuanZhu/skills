# 12 · 横向隐性陷阱合集

> 跨主题的高频误用、启动报错速查、生成代码前必对照。按"症状 → 根因 → 解法"组织。

## 一、AOP 注解失效的统一根因

**所有靠代理的注解，自调用 / 非 public / static / final 都失效。**

| 注解 | 失效条件 |
|---|---|
| `@Transactional` | 自调用 / private / static / final / 异常被吞 / 多线程 |
| `@Async` | 自调用 / private / static / final |
| `@EventListener`（带 `@Async`） | 自调用（绕过 `@Async` 代理） |
| `@Cacheable` / `@CacheEvict` | 自调用 / private / static / final |
| `@Retryable` | 同上 |

**统一解法**：
1. 注解方法必须 `public` 非 `final` 非 `static`。
2. 同类调用须注入自身代理（`@Lazy Self self`）或拆到另一个 Bean。
3. 方法内不 try-catch 吞异常（事务 / 重试靠异常感知）。

> 详见各专篇：`06-transaction.md`（事务）、`07-async-schedule.md`（异步）、`08-events.md`（事件）。

## 二、命名空间坑（SpringBoot 3.x）

```
java.lang.ClassNotFoundException: javax.servlet.http.HttpServletRequest
java.lang.ClassNotFoundException: javax.validation.constraints.NotNull
```

**根因**：3.x 起 `javax.*` → `jakarta.*`，混用即 `ClassNotFoundException`。

**对照表**：

| 用途 | 2.x（javax） | 3.x（jakarta） |
|---|---|---|
| Servlet | `javax.servlet.*` | `jakarta.servlet.*` |
| 校验 | `javax.validation.*` | `jakarta.validation.*` |
| 持久化（JPA） | `javax.persistence.*` | `jakarta.persistence.*` |
| 注解（`@PostConstruct`/`@PreDestroy`） | `javax.annotation.*` | `jakarta.annotation.*` |

**解法**：项目内统一与 SpringBoot 版本一致的命名空间。依赖（如旧版 Sa-Token / 旧版 MyBatis）若用 `javax.*`，须升级到支持 3.x 的版本（见 sa-token-dev / mybatis-plus-dev）。

## 三、启动报错速查

| 报错 | 根因 | 解法 |
|---|---|---|
| `Failed to determine a suitable driver class` | 引数据库 starter 但无数据源 | 排除 `DataSourceAutoConfiguration`，或配 `spring.datasource` |
| `BeanNotFoundException` / `NoSuchBeanDefinitionException` | 主类不在根包 / `@ComponentScan` 覆盖默认 / 缺 `@Component` | 移主类到根包；检查扫描配置；加注解 |
| `BeanCurrentlyInCreationException` | 循环依赖（2.6+ 默认禁用） | 重构消除 / `@Lazy`；见 `09-autowiring.md` |
| `ClassNotFoundException: javax.xxx` | 3.x 用了 `javax.*` | 改 `jakarta.*` |
| `Port 8080 already in use` | 端口占用 | `server.port=其他`，或杀进程 |
| `NoUniqueBeanDefinitionException` | 同类型多个 Bean 未指定 | `@Qualifier` 或 `@Primary`；见 `09-autowiring.md` |
| `UnsatisfiedDependencyException` | Bean 创建时依赖注入失败 | 看嵌套 cause（多为类型不匹配 / 找不到 Bean） |
| `Could not resolve placeholder 'xxx'` | `@Value("${xxx}")` 无默认值且 key 不存在 | 加 `:默认值` 或确认 key |
| `Malformed \uXXXX escape` | yml / properties 编码 | 用 UTF-8；中文用引号包裹 |
| `Neither BindingResult nor plain target object` | 表单校验缺 `@ModelAttribute` | `@Valid @ModelAttribute` |
| `MappedByException` (JPA) | → mybatis-plus-dev 或 JPA 范围 | 切换技能 |

## 四、配置不生效排查

| 症状 | 排查 |
|---|---|
| 改了 yml 不生效 | 用了 jar 内配置（需重新打包）；外部配置路径不对；命令行参数覆盖 |
| profile 配置不生效 | profile 未激活（`--spring.profiles.active=xxx`） |
| `@Value` 读 null / 0 | 静态字段（坑）；`@Value` 不松散绑定，key 须严格匹配 yml |
| `@ConfigurationProperties` 字段 null | 缺 getter/setter；prefix 错；yml 缩进错 |
| 环境变量不生效 | 环境变量名规则：`APP_POOL_MAX_SIZE` → `app.pool.max-size`（点→下划线，全大写） |

> 详见 `01-startup-config.md`（启动配置） + `03-config-properties.md`（配置读取）。

## 五、校验不触发排查

| 症状 | 根因 | 解法 |
|---|---|---|
| **所有校验注解都不触发**（`@NotNull`/`@NotBlank` 等无效） | 缺 `spring-boot-starter-validation` 依赖（`-web` 不传递它） | 引入 `spring-boot-starter-validation`；确认 3.x 用 `jakarta.validation.*`（非 `javax.*`） |
| Bean 参数校验不触发 | 缺 `@Valid`（参数前） | `@Valid @RequestBody DTO` |
| 非 Bean 参数（`@RequestParam`）校验不触发 | 类上缺 `@Validated` | 类级 `@Validated` + 参数级约束注解 |
| 分组校验不触发 | 用了 `@Valid`（无分组）而非 `@Validated(Group.class)` | 参数前 `@Validated(Group.class)` |
| 默认组（无 group 的约束）被跳过 | 指定了 `groups` 的约束与 `Default` 独立 | 分组接口 `extends Default`，或 `@Validated({Default.class, Group.class})` |
| 嵌套对象不校验 | 缺 `@Valid` 在嵌套字段 | 字段上加 `@Valid` |

> 详见 `04-validation.md`。

## 六、事务不生效排查

| 症状 | 根因 | 解法 |
|---|---|---|
| 事务方法异常未回滚 | 自调用 / private / 异常被吞 | 拆 Bean / 改 public / 重新抛或 `setRollbackOnly` |
| 受检异常未回滚 | 默认只回滚 RuntimeException | `@Transactional(rollbackFor = Exception.class)` |
| 多线程不回滚 | 事务靠 ThreadLocal 绑连接，多线程不同连接 | 事务方法内不开多线程 |
| 事务完全失效 | 数据库引擎不支持（MyISAM） | 改 InnoDB |

> 详见 `06-transaction.md`。

## 七、异步 / 定时排查

| 症状 | 根因 | 解法 |
|---|---|---|
| `@Async` 不生效（同步执行） | 缺 `@EnableAsync` / 自调用 / private | 加 `@EnableAsync`；拆 Bean；改 public |
| `@Async` 线程爆炸 | 默认 `SimpleAsyncTaskExecutor` | 自定义 `ThreadPoolTaskExecutor` + `@Async("名字")` |
| `@Async` 异常未捕获 | 异步异常不进 `@ExceptionHandler` | `AsyncUncaughtExceptionHandler` 或 `CompletableFuture` |
| `@Scheduled` 不触发 | 缺 `@EnableScheduling` | 加 `@EnableScheduling` |
| 多个 `@Scheduled` 串行 | 默认单线程 | 自定义 `ThreadPoolTaskScheduler` |
| `@Scheduled(fixedRate)` 补跑 | 任务耗时 > 间隔，单线程串行 | 用并行调度器；或 `fixedDelay` |

> 详见 `07-async-schedule.md`。

## 八、异常处理陷阱

| 陷阱 | 说明 | 解法 |
|---|---|---|
| 父类异常吞子类 | 多个 `@RestControllerAdvice` 时，兜底类（`Exception.class`）的 `@Order` 高 | 兜底类 `@Order(Ordered.LOWEST_PRECEDENCE)` |
| Filter 抛异常不进 `@ExceptionHandler` | Filter 在 DispatcherServlet 前 | 自定义 `ErrorController` 或 Filter 内 try-catch |
| 异步异常不进 `@ExceptionHandler` | 异步线程异常不传播 | `AsyncUncaughtExceptionHandler` |
| Sa-Token 过滤器异常不进 `@ExceptionHandler` | → sa-token-dev | 用 `.setError()` 处理 |

> 详见 `05-exception-handling.md`。

## 九、自动装配与条件注解陷阱

| 陷阱 | 说明 | 解法 |
|---|---|---|
| 3.x `spring.factories` 不生效 | 3.x 自动装配改 `AutoConfiguration.imports` | 见 `10-condition-bean.md` |
| `@ConditionalOnBean` 跨类失效 | 条件求值顺序不确定 | 改 `@ConditionalOnClass` 或合并配置类 |
| `@ConditionalOnProperty` 不生效 | 配置项拼写错 / `matchIfMissing` 设错 | 查 prefix/name/havingValue；缺失时是否匹配 |

> 详见 `10-condition-bean.md`。

## 十、生成代码前必对照清单

写完任何 Spring Boot 代码，交付前逐项核对：

1. **命名空间一致**：`javax.*`（2.x） vs `jakarta.*`（3.x），与 SpringBoot 版本匹配。
2. **AOP 注解方法**：`public` 非 `final` 非 `static`，非自调用。
3. **`@Transactional`**：带 `rollbackFor = Exception.class`；方法内未 try-catch 吞异常；未开多线程。
4. **`@Async`**：带 `@EnableAsync`；指定自定义线程池 `@Async("名字")`；异常有处理器。
5. **`@ExceptionHandler` 顺序**：兜底 `Exception.class` 在最低 `@Order`；父类不吞子类。
6. **校验**：Bean 参数 `@Valid`；非 Bean 参数类级 `@Validated`；分组用 `@Validated(Group.class)`。
7. **Controller 返回 VO/DTO**，不返回 Entity。
8. **循环依赖**：用构造器注入暴露；解法是重构或 `@Lazy`，不开 `allow-circular-references`。
9. **3.x 自动装配**用 `AutoConfiguration.imports`，非 `spring.factories`。
10. **SpringDoc 版本**：3.x 用 `springdoc-openapi-starter-webmvc-ui`（2.x 系）；2.x 用 `springdoc-openapi-ui`（1.x 系）。不引入 Knife4j。
