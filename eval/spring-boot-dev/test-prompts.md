# 10 条 test-prompt（达尔文评估输入）

> 这些 prompt 模拟真实用户场景。盲评 agent 假设自己是"接到这个用户请求的 coding agent，手里只有 spring-boot-dev 技能"，判断能否产出合格代码/解答。
>
> 设计原则：每个 prompt 针对一条或多条核心强约束 + 隐性陷阱。T1-T5 是高频开发场景（竞争场景，验证触发 + 边界）；T6-T10 是独占陷阱场景（验证技能的核心价值）。

## T1 — 写注册接口（竞争场景·三层架构 + 校验 + 边界让位）

```
帮我写一个用户注册接口：POST /api/users
入参：username（3-20字符）、phone（手机号）、email（邮箱）、password（8-32字符）
要求：参数校验失败返回明确错误信息
```

**验证点**：
- 三层架构写法（Controller → Service → Repository，依赖单向）—— `02-layered-arch.md`
- 入参用 DTO（非 Entity），带 `@Valid` + `@NotBlank`/`@Pattern`/`@Email`/`@Length` —— `04-validation.md`
- Controller 返回 `Result<UserVO>`（非 Entity）—— 强约束 7
- **边界让位**：存库部分应指向 mybatis-plus-dev（不越界包办 ORM）—— SKILL.md 第 0 步
- **边界让位**：若涉及登录/token，指向 sa-token-dev

## T2 — @Transactional 不生效排障（独占陷阱·自调用 + rollbackFor）

```
我这段代码，saveBatch 里第二条 insert 失败时第一条没回滚，为什么？
@Transactional
public void saveBatch(List<User> users) {
    for (User u : users) {
        this.insert(u);
    }
}
@Transactional
public void insert(User u) { userMapper.insert(u); }
```

**验证点**（强约束 2 + 3，`06-transaction.md` 坑 1/3）：
- 能否识别**自调用失效**（`this.insert()` 不走代理）—— 这是根因
- 能否给出解法（自注入代理 `@Lazy` / 拆到另一个 Bean / `AopContext.currentProxy()`）
- 是否提醒 `@Transactional` 默认只回滚 `RuntimeException`（受检异常须 `rollbackFor = Exception.class`）

## T3 — @Async 线程池坑（独占陷阱·SimpleAsyncTaskExecutor）

```
我用 @Async 做异步发邮件，上线后高并发时线程数暴涨到几千，OOM 了。
@Async
public void sendEmail(String to) { mailSender.send(to); }
我没自定义线程池，@EnableAsync 已经加了。
```

**验证点**（强约束 4，`07-async-schedule.md` 坑 1）：
- 能否识别默认用 `SimpleAsyncTaskExecutor`（每次新建线程，不复用）
- 能否给出自定义 `ThreadPoolTaskExecutor` 的正确配置（corePoolSize/maxPoolSize/queueCapacity/拒绝策略）
- 是否推荐 `CallerRunsPolicy` 拒绝策略（反压限流）
- 是否提醒 `@Async("executor名")` 显式指定

## T4 — 参数校验不触发（独占陷阱·分组校验 + 非 Bean 参数）

```
我在 Controller 上加了 @Validated，为什么 @RequestParam 的 @Min 校验没生效？
@RestController
@Validated
public class UserController {
    @GetMapping("/search")
    public Result search(@RequestParam @Min(1) Integer size) { ... }
}
```

**验证点**（强约束 6，`04-validation.md`）：
- 能否识别：类级 `@Validated` **已经**是正确的（非 Bean 参数校验必须类级 `@Validated`）—— 这题是反向验证，代码其实是对的，看 agent 是否误判
- **如果用户说"没生效"**：能否排查真实原因（可能是缺 `spring-boot-starter-validation` 依赖；3.x 命名空间用 `jakarta.validation`）

## T5 — 全局异常处理（竞争场景·@ExceptionHandler 顺序）

```
帮我写一个全局异常处理：业务异常返回业务码，参数校验异常返回400，其他返回500。
我现在的写法是先写 @ExceptionHandler(Exception.class) 兜底，再写业务异常的，但有同事说顺序不对。
```

**验证点**（强约束 5，`05-exception-handling.md`）：
- 能否纠正"顺序"误区：**同类内按异常类型最近匹配，与代码声明顺序无关**
- 能否说明**跨类**（多个 `@RestControllerAdvice`）时 `@Order` 才决定优先级
- 能否给出兜底类应 `@Order(Ordered.LOWEST_PRECEDENCE)` 的正确做法
- 是否处理 `MethodArgumentNotValidException`（`@RequestBody` 校验失败）

## T6 — 循环依赖报错（独占陷阱·2.6+ 禁令 + 构造器注入）

```
启动报错：BeanCurrentlyInCreationException: userService ↔ orderService form a cycle
我用了字段注入 @Autowired，为什么还报循环依赖？不是说字段注入能容忍循环吗？
```

**验证点**（强约束 8，`09-autowiring.md`）：
- 能否识别 SpringBoot **2.6+ 默认禁用循环依赖**（无论字段/构造器注入都报错）
- 能否说明解法优先级：**重构消除 > `@Lazy` > `allow-circular-references=true`（不推荐）**
- 是否推荐构造器注入（启动期暴露循环依赖是优点）

## T7 — 配置读不到（独占陷阱·@Value 松散绑定 + 静态字段）

```
application.yml 里配了 app.user-name: alice
我用 @Value("${app.userName}") 读，启动报 Could not resolve placeholder
改成注入静态字段 @Value("${app.user-name}") static String name 又是 null
```

**验证点**（`03-config-properties.md` 坑 1/2）：
- 能否识别 `@Value` **不支持松散绑定**（须严格匹配 yml 的 `user-name`，不能写 `userName`）
- 能否识别**静态字段注入失效**（须通过构造器/setter 中转）
- 是否推荐 `@ConfigurationProperties`（支持松散绑定，适合 ≥3 项）

## T8 — 3.x 自动装配不生效（独占陷阱·AutoConfiguration.imports）

```
我在 META-INF/spring.factories 里配了自动装配类，SpringBoot 3.x 项目启动后没生效。
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
  com.app.MyAutoConfiguration
```

**验证点**（强约束 9，`10-condition-bean.md`）：
- 能否识别 3.x 已废弃 `spring.factories` 的 `EnableAutoConfiguration` key
- 能否给出正确文件：`META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（每行一个全限定类名）
- 是否说明 `@ConditionalOnBean` 跨配置类的顺序依赖陷阱

## T9 — 事件机制（独占陷阱·@TransactionalEventListener）

```
用户注册成功后要发欢迎邮件。我现在这样写，但注册事务回滚时邮件还是发了：
publisher.publishEvent(new UserRegisteredEvent(user));
// listener
@EventListener
public void sendWelcome(UserRegisteredEvent e) { emailService.send(...); }
```

**验证点**（`08-events.md`）：
- 能否识别 `@EventListener` 默认**同步且无事务感知**（publishEvent 时立即触发，不管事务）
- 能否给出正确解法：`@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)`
- 是否说明 `@TransactionalEventListener` 在无事务环境默认不触发（须 `fallbackExecution = true`）

## T10 — 范围边界（多技能竞争·让位判定）

```
帮我写一个完整用户注册功能：
1. 接口接收参数并校验
2. 存入数据库（项目用 MyBatis-Plus）
3. 注册成功后自动登录返回 token（项目用 Sa-Token）
4. 写单元测试
```

**验证点**（SKILL.md 第 0 步边界判定 + 何时使用表）：
- 能否正确**拆解边界**：本技能只负责①接口+校验；②→mybatis-plus-dev；③→sa-token-dev；④→java-unit-test
- 是否**越界**（试图包办 ORM CRUD / Sa-Token 登录 / 单测设计）—— 越界 = 扣分
- 是否在输出中明确指向对应技能（不默默做完）
