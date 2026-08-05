# 08 · 事件机制：`@EventListener` vs `@TransactionalEventListener`

> Spring 事件机制、`ApplicationEventPublisher`、同步 / 异步事件、`@TransactionalEventListener` 的事务阶段语义、自调用失效。事件用于副作用广播（发邮件 / 积分 / 日志 / 通知），发布方不关心谁来处理、处理结果如何。

## 一、发布事件

```java
@Service
public class UserService {
    private final ApplicationEventPublisher publisher;     // Spring 内置，直接注入

    public void register(User u) {
        userMapper.insert(u);
        publisher.publishEvent(new UserRegisteredEvent(u.getId(), u.getUsername()));
        // 发布方只管发，不关心谁来处理；加减 listener 不改 UserService
    }
}
```

## 二、定义事件

### Spring 4.2+（推荐，事件类无需继承 `ApplicationEvent`）

```java
public record UserRegisteredEvent(Long userId, String username, LocalDateTime at) {}

// 或普通类（Java 8 项目）
public class UserRegisteredEvent {
    private final Long userId;
    private final String username;
    // 构造器 + getter
}
```

> **4.2+ 事件类不必继承 `ApplicationEvent`**——任意 POJO 即可作为事件。继承 `ApplicationEvent` 是老写法，不必再沿用。

## 三、监听事件

### 方式 1：`@EventListener`（注解，推荐）

```java
@Component
public class EmailListener {

    @EventListener                              // 监听 UserRegisteredEvent
    public void onUserRegistered(UserRegisteredEvent event) {
        emailService.sendWelcome(event.username());
    }
}
```

### 方式 2：实现 `ApplicationListener`（接口，老写法）

```java
@Component
public class EmailListener implements ApplicationListener<UserRegisteredEvent> {
    @Override
    public void onApplicationEvent(UserRegisteredEvent event) { ... }
}
```

> 推荐用 `@EventListener`——一个类可监听多种事件（多个方法），接口方式一个类只能监听一种。

## 四、`@EventListener` 是**同步**的（重要坑）

```java
@Service
public class UserService {
    public void register(User u) {
        userMapper.insert(u);
        publisher.publishEvent(new UserRegisteredEvent(u));  // 同步：所有 listener 跑完才返回
        System.out.println("注册完成");                       // listener 全部执行后才打印
    }
}
```

**默认行为**：`publishEvent` **同步**调用所有 listener，等它们全部执行完才继续。listener 抛异常会传播给 `publishEvent` → 注册事务可能回滚。

### 异步事件（`@EventListener` + `@Async`）

```java
@Component
public class EmailListener {

    @Async("emailExecutor")                     // 异步执行（须 @EnableAsync + 线程池，见 07）
    @EventListener
    public void onUserRegistered(UserRegisteredEvent event) {
        emailService.sendWelcome(...);          // 异步，不阻塞 register
    }
}
```

## 五、`@TransactionalEventListener`（事务感知）

### 与 `@EventListener` 的关键差异

| 维度 | `@EventListener` | `@TransactionalEventListener` |
|---|---|---|
| 事务感知 | ✗ | ✓ |
| 触发时机 | 事件发布即触发 | 事务提交后 / 回滚后 / 提交前 / 完成后 |
| 无事务时 | 触发 | **默认不触发**（须 `fallbackExecution = true`） |

### 四个阶段

```java
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void onUserRegistered(UserRegisteredEvent event) { ... }
```

| 阶段 | 触发时机 |
|---|---|
| **`AFTER_COMMIT`**（默认） | 事务提交后 |
| `BEFORE_COMMIT` | 事务提交前 |
| `AFTER_ROLLBACK` | 事务回滚后 |
| `AFTER_COMPLETION` | 事务完成（提交或回滚）后 |

### 典型场景：注册成功后发邮件

```java
@Service
public class UserService {
    @Transactional
    public void register(User u) {
        userMapper.insert(u);
        publisher.publishEvent(new UserRegisteredEvent(u));  // 事件发在事务内
    }
}

@Component
public class EmailListener {

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)  // 事务提交后才发邮件
    public void onUserRegistered(UserRegisteredEvent event) {
        emailService.sendWelcome(event.username());         // 注册回滚 → 不发邮件
    }
}
```

> **关键价值**：`AFTER_COMMIT` 保证事务回滚时不触发副作用（避免「注册失败却发了欢迎邮件」）。`@EventListener` 做不到这点——它在 `publishEvent` 时立即触发，若后续事务回滚，副作用已执行。

### 坑：`@TransactionalEventListener` 在无事务时不触发

```java
@Service
public class UserService {
    // 无 @Transactional
    public void register(User u) {
        userMapper.insert(u);
        publisher.publishEvent(new UserRegisteredEvent(u));
    }
}

@Component
public class EmailListener {
    @TransactionalEventListener                   // 默认 fallbackExecution = false
    public void onUserRegistered(UserRegisteredEvent event) { ... }  // ✗ 不触发！无事务
}

// 解法：fallbackExecution = true（无事务时退化为普通 @EventListener）
@TransactionalEventListener(fallbackExecution = true)
public void onUserRegistered(UserRegisteredEvent event) { ... }      // ✓ 触发
```

## 六、坑：自调用失效（同 `@Transactional` / `@Async`）

```java
@Service
public class UserService {

    public void doSomething() {
        this.onLocalEvent();                    // ✗ 自调用不走代理
    }

    @EventListener
    public void onLocalEvent() { ... }          // 注意：@EventListener 不是 AOP 代理注解，
                                                 // 但若同时标 @Async / @Transactional 则失效
}
```

> `@EventListener` 本身靠 `ApplicationEventPublisher` 触发，不走代理。但若 listener 方法**同时**标了 `@Async` / `@Transactional`，自调用会绕过这些 AOP 注解（同前述坑）。

## 七、事件 vs 直接调用（何时用）

| 场景 | 推荐 |
|---|---|
| 副作用多且可能变化（发邮件 / 积分 / 日志 / 通知） | **事件**（解耦） |
| 严格顺序 / 强依赖（A 必须成功 B 才执行） | **直接调用**（事件是"通知"，不是"流程编排"） |
| 跨模块 / 跨团队协作 | **事件**（模块边界清晰） |
| 需要事务感知（提交后才动作） | **`@TransactionalEventListener`** |
| 性能敏感（纳秒级） | **直接调用**（事件有发布 / 分发开销） |

> **误区**：事件不是"万能解耦工具"。事件适合"通知"语义（发布方不关心谁来处理、处理结果如何），不适合"编排"语义（A → B → C 流程）。流程编排用编排（直接调用 / 状态机 / 工作流引擎），事件用于副作用广播。

## 八、最佳实践（仅列前文未详述项，其余对照各节）

1. **事件类用 POJO**（4.2+ 无需继承 `ApplicationEvent`），Java 14+ 用 `record` 更简洁。
2. **事件命名过去式**（`UserRegisteredEvent` 表示"已注册"）。
3. **事件不可变**：`record` 或 `final` 字段 + 构造器，listener 不应修改事件。
4. **listener 内异常**：`@EventListener` 异常传播给发布方；`@TransactionalEventListener(AFTER_COMMIT)` 的异常不影响已提交事务（但会丢入日志，须 try-catch）。

