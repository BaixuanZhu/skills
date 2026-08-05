# 06 · 事务：`@Transactional` 的隐性陷阱

> 自调用失效、传播行为、回滚规则、`rollbackFor`、`private`/`static`/`final` 方法代理失效。事务失效是 Spring 最高频隐性 bug 之一。

## 一、核心机制：`@Transactional` 靠 AOP 代理

`@Transactional` 本质是 Spring 用 **CGLIB / JDK 动态代理**在 Bean 外包一层：方法前开启事务、方法后提交 / 回滚。**一切失效都源于「没走代理」。**

## 二、事务失效场景（全部高发）

### 坑 1：自调用（同类 `this.method()`）

```java
@Service
public class UserService {

    public void batchInsert(List<User> users) {
        for (User u : users) {
            this.insert(u);                    // ✗ 自调用，不走代理，insert 的事务失效
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public void insert(User u) {
        userMapper.insert(u);
    }
}
```

**原因**：`this.insert()` 是直接调目标对象方法，**绕过代理**，`@Transactional` 没机会织入。

**解法**（按推荐度排序）：

```java
// 解法 1（推荐）：拆到另一个 Bean —— 架构清晰，无自引用怪味
// 把需要事务的方法移到独立 Bean（如 UserTxService），原 Service 注入它调用
@Service @RequiredArgsConstructor
public class UserService {
    private final UserTxService userTxService;     // 注入独立事务 Bean
    public void batchInsert(List<User> users) {
        for (User u : users) {
            userTxService.insert(u);               // ✓ 跨 Bean 调用，天然走代理
        }
    }
}

// 解法 2（次选）：注入自身代理 @Lazy —— 须手写构造器（见下方 Lombok 陷阱）
private final UserService self;
public UserService(@Lazy UserService self) { this.self = self; }
// 调用：self.insert(u);                           // ✓ 走代理

// 解法 3（不推荐）：AopContext —— 暴露代理到全局，侵入性强
// 须 @EnableAspectJAutoProxy(exposeProxy = true)
// 调用：((UserService) AopContext.currentProxy()).insert(u);
```

> **⚠️ 解法 2 的 Lombok 陷阱（实跑验证）**：`@Lazy` 必须在**手写构造器的参数**上。若用 `@RequiredArgsConstructor` + `private final UserService self`，Lombok 生成的构造器**不会把 `@Lazy` 传到参数**，启动报 `BeanCurrentlyInCreationException`（循环依赖）。**用解法 2 时必须手写构造器**。解法 1 无此问题（推荐）。

### 坑 2：`private` / `static` / `final` 方法

```java
@Transactional
private void insert(User u) { ... }            // ✗ private：代理无法覆盖，失效

@Transactional
public static void insert(User u) { ... }      // ✗ static：代理基于实例，失效

@Transactional
public final void insert(User u) { ... }       // ✗ final：CGLIB 无法覆盖 final 方法，失效
```

**原因**：CGLIB（子类继承）/ JDK 动态代理（接口实现）都无法覆盖 `private` / `static` / `final`。

**规则**：`@Transactional` 只标在 **`public` 非 `final` 非 `static`** 的方法上。

### 坑 3：默认不回滚受检异常

```java
@Transactional                                 // 默认 rollbackFor = RuntimeException.class + Error.class
public void upload() throws IOException {      // IOException 是受检异常
    file.write(...);
    throw new IOException("写失败");           // ✗ 默认提交不回滚！
}

// ✓ 显式指定
@Transactional(rollbackFor = Exception.class)  // 所有 Exception 都回滚
public void upload() throws IOException { ... }
```

**默认规则**：
- 抛 `RuntimeException` / `Error` → **回滚**
- 抛受检异常（`Exception` 的非 RuntimeException 子类，如 `IOException` / `SQLException`）→ **提交不回滚**

**生产实践**：**永远写 `@Transactional(rollbackFor = Exception.class)`**，不要用默认值。受检异常不回滚是 Spring 最隐蔽的 bug 之一。

### 坑 4：异常被 try-catch 吞掉

```java
@Transactional(rollbackFor = Exception.class)
public void create(User u) {
    try {
        userMapper.insert(u);
        throw new RuntimeException("模拟失败");
    } catch (Exception e) {
        log.error("失败", e);                  // ✗ 异常被吞，事务感知不到，提交不回滚
    }
}
```

**原因**：事务靠方法抛出异常触发回滚；异常被 catch 后没重新抛，代理层看不到异常 → 正常提交。

**解法**：
```java
@Transactional(rollbackFor = Exception.class)
public void create(User u) {
    try {
        userMapper.insert(u);
        riskyOperation();
    } catch (Exception e) {
        log.error("失败", e);
        throw new BusinessException("操作失败"); // ✓ 重新抛出（或 TransactionAspectSupport）
    }
}

// 或手动标记回滚
@Transactional(rollbackFor = Exception.class)
public void create(User u) {
    try { ... } catch (Exception e) {
        TransactionAspectSupport.currentTransactionStatus().setRollbackOnly(); // ✓ 手动标记
    }
}
```

### 坑 5：数据库引擎不支持事务

MySQL 用 `MyISAM` 引擎（不支持事务）→ `@Transactional` 完全失效。须 `InnoDB`。

```sql
SHOW TABLE STATUS FROM your_db WHERE Name = 'your_table';   -- 查 Engine 列
ALTER TABLE your_table ENGINE = InnoDB;                      -- 改引擎
```

### 坑 6：多线程跨连接

```java
@Transactional
public void batchInsert(List<User> users) {
    users.parallelStream().forEach(userMapper::insert);     // ✗ 多线程各拿各的连接，不在同一事务
}
```

**原因**：Spring 事务靠 `ThreadLocal` 绑定数据库连接，多线程各自拿不同连接 → 不在同一事务。

**解法**：事务方法内**不要开新线程**；要异步处理，事务提交后再 `@Async`。

## 三、传播行为（7 种，常用 3 种）

| 传播行为 | 外层有事务 | 外层无事务 | 常用场景 |
|---|---|---|---|
| **REQUIRED**（默认） | 加入外层 | 新建 | **绝大多数场景** |
| **REQUIRES_NEW** | 挂起外层，新建独立事务 | 新建 | 日志 / 审计（须独立提交，不受外层回滚影响） |
| **NESTED** | 创建保存点，部分回滚 | 新建 | 部分失败可回滚到保存点 |
| SUPPORTS | 加入外层 | 无事务执行 | 查询（可走事务也可不走） |
| NOT_SUPPORTED | 挂起外层，无事务执行 | 无事务执行 | 明确不要事务 |
| MANDATORY | 加入外层 | **抛异常** | 强制要求外层有事务 |
| NEVER | **抛异常** | 无事务执行 | 强制要求无事务 |

### REQUIRED vs REQUIRES_NEW vs NESTED

```java
@Service
public class UserService {
    @Transactional                                  // 外层 REQUIRED
    public void outer() {
        userMapper.insert(main);
        try {
            self.inner();                           // 内层传播行为决定行为
        } catch (Exception e) { ... }
    }

    // REQUIRED：inner 失败 → 外层也回滚（同一事务）
    @Transactional(propagation = Propagation.REQUIRED)
    public void inner() { ... }

    // REQUIRES_NEW：inner 失败 → 只回滚 inner，外层提交（独立事务）
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void inner() { ... }

    // NESTED：inner 失败 → 回滚到保存点，外层可继续 / 外层回滚则 inner 也回滚
    @Transactional(propagation = Propagation.NESTED)
    public void inner() { ... }
}
```

**决策**：
- 不确定 → **REQUIRED**（默认）。
- 操作日志 / 审计（外层失败也要记录）→ **REQUIRES_NEW**。
- 批量处理部分失败可跳过 → **NESTED**（保存点回滚单条，整体继续）。

## 四、事务隔离级别（4 种 + 默认）

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 备注 |
|---|---|---|---|---|
| DEFAULT | 用数据库默认 | | | **推荐**（跟随数据库） |
| READ_UNCOMMITTED | 可能 | 可能 | 可能 | 几乎不用 |
| READ_COMMITTED | ✗ | 可能 | 可能 | PostgreSQL / Oracle 默认 |
| REPEATABLE_READ | ✗ | ✗ | 可能 | **MySQL InnoDB 默认**（InnoDB 用间隙锁额外防幻读） |
| SERIALIZABLE | ✗ | ✗ | ✗ | 性能差，几乎不用 |

```java
@Transactional(isolation = Isolation.DEFAULT)        // 推荐：跟数据库
@Transactional(isolation = Isolation.READ_COMMITTED) // 显式指定（覆盖数据库）
```

> **生产实践**：隔离级别由**数据库 / DBA**统一定，应用层用 `DEFAULT`。应用层硬编码隔离级别会掩盖数据库配置，运维难排查。

## 五、事务超时与只读

```java
@Transactional(timeout = 30)                        // 30 秒超时
public void slowTask() { ... }

@Transactional(readOnly = true)                     // 只读提示（非保证）
public UserVO getById(Long id) { ... }
```

> **`readOnly = true`**：JDBC 仅提示（不强制）；JPA 强制（写操作抛异常）。**不是只读保证**，是优化提示。

