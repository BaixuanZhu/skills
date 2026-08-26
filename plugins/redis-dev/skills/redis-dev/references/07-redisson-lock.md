# 分布式锁：Redisson 与看门狗

## 1. 依赖引入

```xml
<!-- 方式一：starter（⚠️ 会把 RedisConnectionFactory 替换为 Redisson 实现，
     RedisTemplate 底层随之切换，全局生效——团队需知情） -->
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
    <version>3.27.2</version>
</dependency>

<!-- 方式二：仅锁/同步器，不动既有 Lettuce 连接（多数据源或不想全局替换时选这个） -->
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson</artifactId>
    <version>3.27.2</version>
</dependency>
```

- 方式一自动装配 `RedissonClient`，复用 `spring.data.redis.*` 连接配置；**版本必须与 Boot 大版本匹配**（Boot 3 用近期 3.x 版本；过老版本只认 `spring.redis.*` 前缀，连不上先查这里，`09-troubleshoot.md`）。
- 方式二手动建 bean：

```java
@Bean(destroyMethod = "shutdown")
public RedissonClient redissonClient() {
    return Redisson.create(Config.fromYAML(getClass().getResourceAsStream("/redisson.yaml")));
}
```

## 2. 自实现的最低正确线（不用 Redisson 时）

```java
// ✗ 错误：setnx + expire 两步——进程在两步之间崩溃 → 死锁永不过期
redisTemplate.opsForValue().setIfAbsent(key, "1");
redisTemplate.expire(key, Duration.ofSeconds(10));

// ✓ 最低正确：一条原子命令；value 放唯一标识；释放必须 Lua 校验
String token = UUID.randomUUID().toString();
Boolean ok = stringRedisTemplate.opsForValue()
        .setIfAbsent(key, token, Duration.ofSeconds(10));   // SET key token NX EX 10
if (Boolean.TRUE.equals(ok)) {
    try {
        doBusiness();
    } finally {
        // 校验是自己的锁才能删，防止误删别人的锁（自己租期已过、锁已被他人持有时）
        stringRedisTemplate.execute(new DefaultRedisScript<>("""
                if redis.call('get', KEYS[1]) == ARGV[1] then
                    return redis.call('del', KEYS[1])
                else
                    return 0
                end
                """, Long.class), List.of(key), token);
    }
}
```

自实现没有自动续期：业务超 10s 锁已释放 → 并发进入。**业务时长不可预估，用 Redisson 看门狗**——这是引入它的核心理由。

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

- [ ] 没有出现 `setnx` + `expire` 两步；自实现释放是 Lua 校验后删
- [ ] `leaseTime` 决策：不可预估就不传（看门狗）；传了就知道没有续期
- [ ] `finally` 中 `isHeldByCurrentThread()` 判断后 `unlock()`
- [ ] `tryLock` 拿不到的分支有真实处理（繁忙返回/降级），不是 while 空转
- [ ] 锁 key 粒度与业务互斥粒度一致（用户级锁别用全局 key，全局互斥别按用户分 key）
- [ ] 资金/库存类强互斥有 DB 层兜底，不裸信 Redis 锁
