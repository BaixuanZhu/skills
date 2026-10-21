# 事务管理

> MP 不提供事务管理器，事务由 Spring `@Transactional` 提供。MP 的交互坑集中在 saveBatch、多数据源、逻辑删除三处。

## 1. rollbackFor 必须显式指定

`@Transactional` 无参**只回滚 `RuntimeException` + `Error`**。checked exception（`IOException`、继承 `Exception` 的自定义业务异常）**默认不回滚，且不报错**。

```java
public class BizException extends Exception {}      // 继承 Exception，非 RuntimeException

@Transactional                                     // ❌ 抛 BizException 不回滚
public void create() throws BizException { save(e); throw new BizException("库存不足"); }

@Transactional(rollbackFor = Exception.class)      // ✅
public void create() throws BizException { save(e); throw new BizException("库存不足"); }
```

> **强约束**：所有 `@Transactional` 一律写 `rollbackFor = Exception.class`，不留默认行为。

## 2. 事务失效的 7 个场景（全部静默，不报错）

| # | 症状 | 根因 | 处置 |
|---|---|---|---|
| 1 | 同类内部 `inner()` 抛异常，但 inner 写入的数据已落库 | `@Transactional` 走 AOP 代理，`this.inner()` 不经过代理 | **拆到不同 Service**（首选）；或自注入 `@Autowired @Lazy UserService self` 后调 `self.inner()`；或 `AopContext.currentProxy()`（需 `exposeProxy = true`） |
| 2 | 注解写了却不生效 | 默认只代理 **public** 方法，`private` / 包级静默失效 | 改 public，或把事务边界上移到 public 方法 |
| 3 | try-catch 捕完后正常返回，数据未回滚 | 异常被吞，Spring 感知不到 | 重新 `throw`；或 `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()` |
| 4 | 注解写了但毫无事务效果 | 表引擎不支持（MySQL MyISAM） | `SHOW TABLE STATUS WHERE Name='t'` 查 Engine 列，改 InnoDB |
| 5 | checked exception 抛出后不回滚 | 缺 `rollbackFor` | 见 §1 |
| 6 | 工具类上加注解无效 | 类无 `@Service` / `@Component`，不归 Spring 管 | 加注解，或把事务方法挪进 Service |
| 7 | 内层方法异常，内层数据没回滚 | 传播行为语义误解 | `REQUIRES_NEW` 是独立事务（**独立连接，连接池不足会死锁**，大批量慎用）；`NOT_SUPPORTED` 根本不参与事务 |

> 排查顺序：先确认方法是不是 public（#2）→ 再看是不是自己调自己（#1）→ 再看异常有没有被吞（#3）。这三个占实际踩坑的绝大多数。

## 3. saveBatch 与事务

`saveBatch` **默认不是真批量**：按 `batchSize` 分批，批内仍逐条 `insert`。要真正批量，两个条件必须同时满足：

1. 在事务内调用（同一 `SqlSession`；无事务时每条独立提交）
2. MySQL 加 `rewriteBatchedStatements=true`（驱动层合并）——**PostgreSQL 不需要**，驱动原生支持

```java
@Transactional(rollbackFor = Exception.class)
public void importUsers(List<User> users) {
    saveBatch(users, 500);
}
```

> 超大批量（10 万+）单事务会导致 Undo Log 膨胀 + 锁竞争，应每 N 条一个独立事务（`Propagation.REQUIRES_NEW` + 自注入代理，见 §2 #1）。

## 4. 编程式事务

条件性回滚（不满足业务条件时主动回滚，而非靠抛异常）：

```java
@Autowired private TransactionTemplate transactionTemplate;

public void conditionalUpdate(User user) {
    transactionTemplate.execute(status -> {
        save(user);
        if (someCondition) { status.setRollbackOnly(); return null; }
        updateRelated(user);
        return null;
    });
}
```

更底层的 `PlatformTransactionManager`（`getTransaction` / `commit` / `rollback`）日常几乎不需要。

## 5. 多数据源与事务

**单一 `@Transactional` 只能保证单库事务**，这是硬限制：

- `@DS` 切换数据源时，`@Transactional` 已持有的 `Connection` **不会随之切换**——SQL 可能跑到错误的库上
- 跨库一致性必须用 **Seata / XA**，或拆成独立事务 + 补偿（最终一致性）
- 多数情况的最优解：把同一数据源的操作收进一个方法，`@DS` 标在类或方法上

## 6. 逻辑删除与事务

逻辑删除本质是 `UPDATE`，与事务无交互问题。但有一个反直觉行为：**事务内逻辑删除后再查询，仍会追加 `deleted = 0`，查不到刚删的行**。

## 7. 事务超时

```java
@Transactional(rollbackFor = Exception.class, timeout = 30)   // 单位：秒
```

> 超时**不会中断正在执行的 SQL**，而是标记回滚后在下一次 SQL 执行时抛 `TransactionTimedOutException`。因此不能靠它兜住单条慢 SQL。
