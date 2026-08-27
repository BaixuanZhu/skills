# 分布式锁：Redisson 与看门狗

## 1. 依赖与选型（一律用成熟实现）

```xml
<!-- 方式一：starter（⚠️ 会把 RedisConnectionFactory 替换为 Redisson 实现，
     RedisTemplate 底层随之切换，全局生效——团队需知情） -->
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
    <version>3.27.2</version>
</dependency>

<!-- 方式二：仅锁/同步器，不动既有 Lettuce 连接（不想全局替换时选这个） -->
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson</artifactId>
    <version>3.27.2</version>
</dependency>

<!-- 方式三：lock4j 注解式（底层默认 Redisson） -->
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>lock4j-redisson-spring-boot-starter</artifactId>
    <version>${lock4j.version}</version>
</dependency>
```

- 方式一自动装配 `RedissonClient`，复用 `spring.data.redis.*` 连接配置；**starter 版本随 Boot 大版本走**：Boot 3 → 近期 3.x，Boot 4 → 4.x 线（2025-12 起；3.x starter 在 Boot 4 下启动报错）；过老版本只认 `spring.redis.*` 前缀、连不上先查这里（`08-troubleshoot.md`）。
- 方式二手动建 bean：

```java
@Bean(destroyMethod = "shutdown")
public RedissonClient redissonClient() {
    return Redisson.create(Config.fromYAML(getClass().getResourceAsStream("/redisson.yaml")));
}
```

方式三声明式用法（`@Lock4j`，方法上加注解即锁）：

```java
@Lock4j(keys = "#orderId", acquireTimeout = 3000, expire = 10000)
public void processOrder(Long orderId) { ... }
```

- `keys` 支持 SpEL（决定锁粒度）；`acquireTimeout` 获取等待（默认 3000ms，超时抛获取失败异常）；`expire` **固定租期**（默认 30000ms）——**显式 expire 即 leaseTime 语义、无看门狗续期**（§4），必须按业务执行时长上界设置。

## 2. 禁止自实现（存量识别与迁移方向）

存量代码里的自写锁形态：`setnx` + `expire` 两步（崩溃间隔留下永不过期的死锁），或一条 `SET NX EX` 加自写 Lua 校验释放。**修复方向一律是迁移本节的成熟实现，不是继续打补丁**——"正确的自实现"还缺：持有者唯一标识 + 校验释放（防误删他人的锁）、业务超时自动续期、可重入、主从切换语义（§7），每一项都是造轮子的新坑位。`SET NX EX` 的原子性留作 review 存量代码的识别知识即可，不是自实现的邀请。

## 3. Redisson 标准用法

```java
RLock lock = redissonClient.getLock("lock:order:" + orderId);   // key 粒度 = 业务互斥粒度

if (lock.tryLock(3, TimeUnit.SECONDS)) {         // 等锁最多 3s；未传 leaseTime → 看门狗
    try {
        doBusiness();
    } finally {
        if (lock.isHeldByCurrentThread()) {      // 强约束 7：先判持有再解
            lock.unlock();
        }
    }
} else {
    // 3s 内没拿到锁：不要空转重试压垮 Redis——返回繁忙/读旧值/提示稍后
    throw new BizException("操作繁忙，请稍后重试");
}
```

## 4. 看门狗与 leaseTime（本技能最高频的坑）

**看门狗机制**：`tryLock(wait)` / `lock()` 不传 `leaseTime` 时——锁租期默认 **30s**（`lockWatchdogTimeout=30000ms`），Redisson 后台任务每 **10s**（租期/3）自动续期，直到 `unlock` 或客户端崩溃（崩溃后续期停止，30s 后锁自动释放——不死锁）。

**一旦显式传 `leaseTime`，看门狗立即失效**：

| 调用 | 等待 | 租期 | 看门狗 | 后果 |
|---|---|---|---|---|
| `tryLock()` | 不等待 | 30s | ✓ | 拿不到立即返回 false |
| `tryLock(3, SECONDS)` | 3s | 30s | ✓ | **默认推荐** |
| `tryLock(3, 10, SECONDS)` | 3s | 固定 10s | **✗** | 业务超 10s → 锁已易主，并发进入（且 unlock 抛异常） |
| lock4j `@Lock4j(expire = 10000)` | acquireTimeout | 固定 expire | **✗** | 与显式 leaseTime 同语义（§1 方式三）——业务超 expire 并发进入 |
| `lock()` | 不等待 | 30s | ✓ | 拿不到永久等，一般别用 |

> 传 `leaseTime` 的唯一正当理由：**明确希望到期强制释放**（防持锁方长期占用），且业务时长有把握上界。拿不准 → 不传。

## 5. 可重入与公平锁

- **可重入**：同线程重复 `lock/unlock` 同名锁嵌套安全（Redis hash 结构记录线程标识与计数）。仅限**同线程**；跨线程（如异步任务里解锁）不可重入且可能抛 `IllegalMonitorStateException`。
- `getFairLock(key)`：按等待顺序获取（吞吐低），排队语义必须时才用。

## 6. 其他同步器

| 工具 | 场景 | 一句话边界 |
|---|---|---|
| `RReadWriteLock` | 读多写少（字典/配置缓存重建） | 写锁期间读全阻塞；读锁内禁止再拿写锁 |
| `RSemaphore` | 资源池限并发（如同时跑 N 个导入） | 信号量不防重，只限总量 |
| `RCountDownLatch` | 多任务汇合后放行 | 不可重用（`countDown` 归零即废） |
| `RDelayedQueue` | 延迟任务（订单 30min 未支付关闭） | 替代定时轮询全表；**需要消费方常驻 + 队列数据落 Redis**，可靠性弱于 MQ 延迟消息 |

## 7. 边界：主从切换可能丢锁

Redis 主从复制是异步的：加锁落在 master、未同步到 replica 时 master 宕机 → 新 master 上锁不存在 → 第二个客户端加锁成功，**互斥被打破**。Redisson 的处理：默认不等同步确认；`RedLock`（多实例多数派）争议大且 Redisson 已不推荐。结论按场景选：

- **可容忍极小概率并发**（防重复提交、缓存回源互斥）→ Redisson 单实例锁足够。
- **绝对互斥**（资金扣减）→ 数据库乐观锁/唯一约束兜底（Redis 锁只当第一道闸），或 fencing token。

## 8. 自检

- [ ] 锁全部走 Redisson / lock4j；存量自写 setnx+expire / Lua 锁已列迁移计划（不是修补）
- [ ] `leaseTime` 决策：不可预估就不传（看门狗）；传了就知道没有续期
- [ ] `finally` 中 `isHeldByCurrentThread()` 判断后 `unlock()`
- [ ] `tryLock` 拿不到的分支有真实处理（繁忙返回/降级），不是 while 空转
- [ ] 锁 key 粒度与业务互斥粒度一致（用户级锁别用全局 key，全局互斥别按用户分 key）
- [ ] 资金/库存类强互斥有 DB 层兜底，不裸信 Redis 锁
