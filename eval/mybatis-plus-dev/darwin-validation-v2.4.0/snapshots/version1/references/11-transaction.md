# 事务管理

> MyBatis-Plus 本身不提供事务管理器，事务由 **Spring**（`@Transactional`）或 MyBatis 的 `SqlSession` 机制提供。MP 在此基础上与 Spring 事务无缝集成，但有几个关键交互点（saveBatch、多数据源、逻辑删除）容易踩坑。

## 1. 声明式事务（@Transactional）

### 基本用法

```java
@Service
public class OrderService extends ServiceImpl<OrderMapper, Order> {

    @Transactional(rollbackFor = Exception.class)
    public void createOrder(OrderDTO dto) {
        Order order = new Order();
        BeanUtils.copyProperties(dto, order);
        save(order);                          // MP IService 方法

        OrderItem item = new OrderItem();
        item.setOrderId(order.getId());
        orderItemService.save(item);          // 跨 Service 调用

        // 此处抛异常 → order + orderItem 全部回滚
    }
}
```

### rollbackFor 必须显式指定

| 配置 | 回滚范围 | 风险 |
|------|---------|------|
| `@Transactional`（无参） | 仅 `RuntimeException` + `Error` | **checked exception 不回滚**（如 `IOException`、自定义业务异常继承 Exception） |
| `@Transactional(rollbackFor = Exception.class)` | 所有 `Exception` 子类 | **推荐**，覆盖业务异常 |

```java
// ❌ 业务异常继承 Exception（非 RuntimeException），默认不回滚
public class BizException extends Exception { ... }

@Transactional  // 抛出 BizException 不会回滚！
public void doSomething() throws BizException {
    save(entity);
    throw new BizException("库存不足");
}

// ✅ 显式指定 rollbackFor
@Transactional(rollbackFor = Exception.class)
public void doSomething() throws BizException {
    save(entity);
    throw new BizException("库存不足");  // 回滚
}
```

> **强约束**：所有 `@Transactional` 一律写 `rollbackFor = Exception.class`，不留默认行为。

## 2. 事务传播行为（Propagation）

| 传播行为 | 含义 | 典型场景 |
|---------|------|---------|
| `REQUIRED`（默认） | 有事务则加入，无则新建 | 90% 场景用这个 |
| `REQUIRES_NEW` | 挂起当前事务，始终新建独立事务 | 日志记录（不受主事务回滚影响） |
| `NESTED` | 嵌套事务（savepoint） | 部分失败可回滚到 savepoint，外层仍可继续 |
| `SUPPORTS` | 有事务则加入，无则非事务运行 | 查询方法 |
| `NOT_SUPPORTED` | 挂起当前事务，以非事务方式运行 | 耗时操作避免长事务 |

```java
@Service
public class OrderService extends ServiceImpl<OrderMapper, Order> {

    @Transactional(rollbackFor = Exception.class)
    public void batchProcess(List<OrderDTO> dtos) {
        for (OrderDTO dto : dtos) {
            try {
                processOne(dto);  // 子方法
            } catch (Exception e) {
                log.error("处理失败: {}", dto.getId(), e);
                // 不影响整体，继续处理下一条
            }
        }
    }

    // REQUIRES_NEW：即使外层回滚，日志也保留
    @Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
    public void saveLog(String action, String detail) {
        Log log = new Log();
        log.setAction(action);
        log.setDetail(detail);
        logService.save(log);
    }
}
```

> **注意**：`REQUIRES_NEW` 会获取**新的数据库连接**，若连接池容量不足可能死锁。大批量场景慎用。

## 3. 事务失效的 7 大场景（重点）

### 场景 1：自调用（同类内部方法调用）

```java
@Service
public class UserService extends ServiceImpl<UserMapper, User> {

    @Transactional(rollbackFor = Exception.class)
    public void outer() {
        // ...
        inner();  // ❌ 直接调用 this.inner()，AOP 代理不生效，事务不回滚
    }

    @Transactional(rollbackFor = Exception.class)
    public void inner() {
        save(new User());
        throw new RuntimeException("boom");
    }
}
```

**原因**：`@Transactional` 基于 Spring AOP 代理，内部调用走 `this`，不经过代理对象。

**解决方案**：
```java
// 方案 A：注入自身代理
@Service
public class UserService extends ServiceImpl<UserMapper, User> {
    @Autowired
    @Lazy
    private UserService self;  // 自注入（需 @Lazy 避免循环依赖）

    public void outer() {
        self.inner();  // ✅ 走代理，事务生效
    }
}

// 方案 B：从 AopContext 获取代理
public void outer() {
    ((UserService) AopContext.currentProxy()).inner();  // 需开启 exposeProxy
}
// 启动类加：@EnableAspectJAutoProxy(exposeProxy = true)

// 方案 C（推荐）：拆分到不同 Service
```

### 场景 2：方法非 public

```java
@Transactional(rollbackFor = Exception.class)  // ❌ private 方法，代理不拦截
private void doSomething() { ... }

@Transactional(rollbackFor = Exception.class)  // ❌ 默认只代理 public
void doSomething() { ... }  // 包级可见
```

> `@Transactional` 加在非 public 方法上**静默失效**，不报错但不回滚。

### 场景 3：异常被 catch 吞掉

```java
@Transactional(rollbackFor = Exception.class)
public void doSomething() {
    save(entity);
    try {
        riskyCall();
    } catch (Exception e) {
        log.error("出错", e);
        // ❌ 异常被吞，Spring 感知不到异常，不回滚
    }
}

// ✅ 要回滚就重新抛出，或手动标记
@Transactional(rollbackFor = Exception.class)
public void doSomething() {
    save(entity);
    try {
        riskyCall();
    } catch (Exception e) {
        log.error("出错", e);
        TransactionAspectSupport.currentTransactionStatus()
            .setRollbackOnly();  // 手动标记回滚
        throw e;  // 或重新抛出
    }
}
```

### 场景 4：数据库引擎不支持事务

- MySQL **InnoDB** 支持事务；**MyISAM** 不支持。
- 若建表时用了 MyISAM，`@Transactional` 无效且不报错。
- 检查：`SHOW TABLE STATUS WHERE Name = 'your_table';` 查看 Engine 列。

### 场景 5：异常类型不匹配（rollbackFor 缺失）

见 §1 的 `rollbackFor` 说明。默认只回滚 `RuntimeException`，checked exception 默认不回滚。

### 场景 6：类未被 Spring 管理

```java
// ❌ 没有 @Service / @Component，Spring 不管理，代理不生效
public class OrderHelper {
    @Transactional(rollbackFor = Exception.class)
    public void doSomething() { ... }
}
```

### 场景 7：传播行为配置不当

```java
@Transactional(rollbackFor = Exception.class)
public void outer() {
    save(a);
    inner();  // inner 用 NOT_SUPPORTED，内部异常不回滚
}

@Transactional(propagation = Propagation.NOT_SUPPORTED)
public void inner() {
    save(b);
    throw new RuntimeException("boom");  // b 不回滚（非事务执行），a 也不回滚（inner 抛异常后 outer 捕获则 a 回滚）
}
```

## 4. saveBatch 与事务的关系

> 这是 MP 特有的交互点，容易踩坑。

### saveBatch 需要在事务内才能真正批量

```java
// ❌ 无事务：saveBatch 仍可执行，但每条 insert 独立提交，性能差
public void importUsers(List<User> users) {
    saveBatch(users);  // 能跑，但逐条提交
}

// ✅ 有事务：saveBatch 在同一 SqlSession 内，配合 rewriteBatchedStatements=true
@Transactional(rollbackFor = Exception.class)
public void importUsers(List<User> users) {
    saveBatch(users);  // 批量提交，性能提升 5-10 倍
}
```

### rewriteBatchedStatements 配置

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/db?rewriteBatchedStatements=true
```

> MySQL 驱动层面合并批量 SQL。不开此参数，即使 `saveBatch` 在事务内也只是逐条发 SQL。
> **PostgreSQL** 不需要此参数，驱动原生支持批量。

### 大批量数据分批提交

```java
@Transactional(rollbackFor = Exception.class)
public void importLarge(List<User> users) {
    int batchSize = 500;
    for (int i = 0; i < users.size(); i += batchSize) {
        List<User> batch = users.subList(i, Math.min(i + batchSize, users.size()));
        saveBatch(batch, batchSize);
        // 大批量时注意：单事务过长会导致 Undo Log 膨胀、锁竞争
    }
}

// 超大批量（10万+）建议分事务：每 N 条一个独立事务
public void importHuge(List<User> users) {
    int batchSize = 1000;
    for (int i = 0; i < users.size(); i += batchSize) {
        List<User> batch = users.subList(i, Math.min(i + batchSize, users.size()));
        self.importBatch(batch);  // self 是代理对象
    }
}

@Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
public void importBatch(List<User> batch) {
    saveBatch(batch, 1000);
}
```

## 5. 编程式事务

### TransactionTemplate

```java
@Autowired
private TransactionTemplate transactionTemplate;

public void conditionalUpdate(User user) {
    transactionTemplate.execute(status -> {
        save(user);
        if (someCondition) {
            status.setRollbackOnly();  // 条件性回滚
            return null;
        }
        updateRelated(user);
        return null;
    });
}

// 带返回值
public User createAndReturn(User user) {
    return transactionTemplate.execute(status -> {
        save(user);
        return user;  // 返回保存后的实体（含 ID）
    });
}
```

### PlatformTransactionManager（低频，按需）

> 更低层的 `PlatformTransactionManager` 手动 API（`getTransaction` / `commit` / `rollback`）仅在需要超细粒度控制时使用，日常几乎不需要。需要时注入 `PlatformTransactionManager`，按标准 Spring 写法（`DefaultTransactionDefinition` 设传播/隔离/超时 → `getTransaction` → `commit`/`rollback`）操作即可。

> 编程式事务适用于：条件性回滚、动态传播行为、超细粒度事务控制。日常用声明式 `@Transactional` 即可。

## 6. 多数据源与事务

### @DS + 事务的陷阱

```java
@DS("master")
@Transactional(rollbackFor = Exception.class)
public void crossDsMethod() {
    save(entity);                    // 写 master
    otherMapper.insert(other);       // 默认也走 master（事务内切换数据源需注意）
}

// ❌ 多数据源 + 单一 @Transactional 无法实现 XA 事务
@DS("master")
@Transactional(rollbackFor = Exception.class)
public void crossDsFail() {
    save(entity);           // master
    dsSlaveService.save(s); // slave —— 此处切换数据源后，Spring 事务管理器管不到新连接
    // slave 异常 → master 回滚，slave 不回滚（除非用 XA / Seata）
}
```

> **强约束**：
> - 多数据源场景下，单一 `@Transactional` **只能保证单库事务**。
> - 跨库事务需要 **Seata / XA** 等分布式事务方案。
> - `@DS` 切换数据源时，`@Transactional` 持有的 Connection 不会随之切换，可能导致 SQL 执行在错误的数据源上。

### 正确的多数据源事务做法

```java
// 方案 A：同一数据源内完成所有操作，最后切换
@DS("master")
@Transactional(rollbackFor = Exception.class)
public void masterOnly() {
    save(entity);
    relatedService.save(related);  // relatedService 内部也 @DS("master")
}

// 方案 B：需要跨库一致性 → 引入 Seata
// 方案 C：拆分为独立事务 + 补偿机制（最终一致性）
```

## 7. 逻辑删除与事务

```java
@Transactional(rollbackFor = Exception.class)
public void softDeleteAndArchive(Long id) {
    // 逻辑删除（UPDATE deleted = <timestamp> WHERE id = ?）
    removeById(id);

    // 归档到历史表
    historyService.save(buildHistory(id));

    // 两者在同一事务内：归档失败 → 逻辑删除回滚
}
```

> 逻辑删除本质是 `UPDATE`，与事务交互无特殊问题。但注意：若在事务内逻辑删除后查询，**查询仍会追加 `deleted = 0`**，查不到刚删除的行。

## 8. 事务隔离级别

```java
@Transactional(
    rollbackFor = Exception.class,
    isolation = Isolation.READ_COMMITTED  // 可选
)
```

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 说明 |
|---------|------|-----------|------|------|
| `DEFAULT` | — | — | — | 用数据库默认（MySQL InnoDB = REPEATABLE_READ） |
| `READ_UNCOMMITTED` | ✓ | ✓ | ✓ | 生产禁用 |
| `READ_COMMITTED` | ✗ | ✓ | ✓ | Oracle/PostgreSQL 默认 |
| `REPEATABLE_READ` | ✗ | ✗ | ✓（InnoDB 快照读+间隙锁可防） | MySQL 默认 |
| `SERIALIZABLE` | ✗ | ✗ | ✗ | 性能最差，极少使用 |

> **建议**：一般不需要在 `@Transactional` 上手动指定隔离级别，用数据库默认即可。仅在特定场景（如读已提交需求、避免幻读）时调整。

## 9. 事务超时

```java
@Transactional(
    rollbackFor = Exception.class,
    timeout = 30  // 30 秒，超时自动回滚
)
public void longRunningTask() { ... }
```

> 超时从事务开始时计算，超时后 Spring 会标记事务为回滚。注意：这不会强制中断正在执行的 SQL，而是在下一次 SQL 执行时抛出 `TransactionTimedOutException`。

## 10. 事务最佳实践速查

| 实践 | 说明 |
|------|------|
| `rollbackFor = Exception.class` | 一律显式指定，不依赖默认行为 |
| 事务方法 public | 非 public 静默失效 |
| 不要自调用 | 同类内部方法调用不走代理，事务不生效 |
| 不要吞异常 | catch 后若要回滚，必须 `throw` 或 `setRollbackOnly()` |
| 事务粒度最小化 | 一个事务只做必须原子化的操作，不要把远程调用/文件 IO 塞进事务 |
| 避免长事务 | 长事务占连接、锁竞争、Undo Log 膨胀；大批量分批提交 |
| saveBatch 加事务 | 事务外 saveBatch 性能差且无原子性 |
| 多数据源不用单 @Transactional | 跨库用 Seata 或补偿 |
| 只读事务 | `@Transactional(readOnly = true)` 可优化查询（部分数据库 + 驱动生效） |
