# Redisson：分布式锁与分布式对象

Redisson 不只是锁库——它是在 Redis 上实现的一组**带语义的分布式对象与服务**：锁 / 读写锁 / 信号量 / 限流器 / 阻塞与延迟队列 / 布隆过滤器。选型口径：普通 KV / 缓存读写继续 `RedisTemplate`；需要这些语义化能力时用 Redisson（`RedissonClient` 直接注入）。两套可共存——下方方式二不动既有 Lettuce 连接。

## 1. 依赖与选型（一律用成熟实现）

```xml
<!-- 方式一：starter（⚠️ 会把 RedisConnectionFactory 替换为 Redisson 实现，
     RedisTemplate 底层随之切换，全局生效——团队需知情） -->
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
    <version>3.27.2</version>
</dependency>

<!-- 方式二：仅分布式对象、不动既有 Lettuce 连接（不想全局替换时选这个） -->
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson</artifactId>
    <version>3.27.2</version>
</dependency>

<!-- 方式三：lock4j 注解式（底层默认 Redisson，仅锁场景） -->
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

- `keys` 支持 SpEL（决定锁粒度）；`acquireTimeout` 获取等待（默认 3000ms，超时抛获取失败异常）；`expire` **固定租期**（默认 30000ms），即 §4 推荐的显式 leaseTime 语义——必须按业务执行时长上界（× 余量）设置。

## 2. 禁止自实现锁（存量识别与迁移方向）

存量代码里的自写锁形态：`setnx` + `expire` 两步（崩溃间隔留下永不过期的死锁），或一条 `SET NX EX` 加自写 Lua 校验释放。**修复方向一律是迁移本节的成熟实现，不是继续打补丁**——"正确的自实现"还缺：持有者唯一标识 + 校验释放（防误删他人的锁）、业务超时自动续期、可重入、主从切换语义（§9），每一项都是造轮子的新坑位。`SET NX EX` 的原子性留作 review 存量代码的识别知识即可，不是自实现的邀请。

## 3. RLock 标准用法

```java
RLock lock = redissonClient.getLock("lock:order:" + orderId);   // key 粒度 = 业务互斥粒度

if (lock.tryLock(3, 30, TimeUnit.SECONDS)) {     // 等锁最多 3s；持锁硬上限 30s（§4 推荐写法）
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

## 4. tryLock 参数语义与推荐写法

| 调用 | waitTime（等多久拿锁） | leaseTime（持锁多久） | 看门狗 |
|---|---|---|---|
| `tryLock()` | 0，立即返回 | 默认 30s | ✓ 每 10s 自动续期 |
| `tryLock(3, SECONDS)` | 最多等 3s | 默认 30s | ✓ |
| `tryLock(3, 30, SECONDS)` | 最多等 3s | 固定 30s，到期自动释放 | ✗ |
| `lock()` | 无限等（别用） | 默认 30s | ✓ |
| `lock(30, SECONDS)` | 无限等（别用） | 固定 30s | ✗ |
| lock4j `@Lock4j` | acquireTimeout（默认 3000ms） | expire（默认 30000ms，固定） | ✗ |

waitTime 与 leaseTime 是两件事：**waitTime** 限「拿不到就放弃」的等待上限（拿不到返回 false）；**leaseTime** 限「拿到后最多持有多久」的租期上限——到期**自动释放，无论业务是否跑完**。

推荐写法——**两个时间都显式**：

```java
lock.tryLock(3, 30, TimeUnit.SECONDS);   // 等锁最多 3s；持锁硬上限 30s（完整模式见 §3）
```

- **leaseTime 必须显式，防等效死锁**：不传时看门狗给默认 30s 租期、每 10s（租期/3）续期，JVM 存活就一直续。业务线程挂死（死循环 / 业务自身死锁）而客户端健康时，锁被**无限续期、永不释放**，其他节点永远拿不到。显式 leaseTime 是硬上限——挂死也在到期后放锁。
- **leaseTime 必须大于业务执行上界**（上界 × 安全余量）：业务没跑完锁先到期 → 并发进入（互斥被破），且 unlock 抛 `IllegalMonitorStateException`。上界估不出来给大值（60s / 5min），**宁可长不可短**——互斥正确性靠 DB 兜底（§9），不靠锁精确到期。
- 看门狗（`lockWatchdogTimeout` 默认 30000ms）是「不传 leaseTime 时」的兜底机制：业务时长波动大时不用猜租期，代价就是上面的无限续期——存量代码识别它即可，新代码按推荐写法显式传。

## 5. 可重入与公平锁

- **可重入**：同线程重复 `lock/unlock` 同名锁嵌套安全（Redis hash 结构记录线程标识与计数）。仅限**同线程**；跨线程（如异步任务里解锁）不可重入且可能抛 `IllegalMonitorStateException`。
- `getFairLock(key)`：按等待顺序获取（吞吐低），排队语义必须时才用。

## 6. 限流：RRateLimiter

```java
RRateLimiter limiter = redissonClient.getRateLimiter("rate:api:" + apiId);
limiter.trySetRate(RateType.OVERALL, 100, 1, RateIntervalUnit.SECONDS);   // 全部实例共享 100/s；已配置则忽略（幂等）
if (!limiter.tryAcquire()) {                     // 非阻塞拿 1 个许可
    throw new BizException("请求过于频繁");
}
```

- `RateType.OVERALL`：所有实例共享同一额度（全局限频用这个）；`PER_CLIENT`：**每个 Redisson 实例独立额度**——总流量按实例数放大，慎用。
- `trySetRate` 仅在未配置时生效（应用重复启动安全）；改配置用 `setRate`（覆盖）。
- `acquire()` 阻塞等待；`tryAcquire()` 立即返回；`tryAcquire(timeout, unit)` 限时等待。
- 与 RedisTemplate 计数限流的分工：单维度简单限次（每 IP 每分钟 5 次）`INCR`+TTL / Lua 就够（`04-template-operations.md` §4）；**多实例共享一个额度的全局限频**（保护下游 / 对接第三方配额）用 RRateLimiter——不用自己管 TTL 与原子性。

## 7. 延迟队列：RDelayedQueue（订单超时关闭等延迟任务）

```java
RBlockingQueue<String> closeQueue = redissonClient.getBlockingQueue("order:close:queue");
RDelayedQueue<String> delayed = redissonClient.getDelayedQueue(closeQueue);
delayed.offer(orderId, 30, TimeUnit.MINUTES);    // 30min 后元素进入 closeQueue

// 消费方（常驻线程）：take() 阻塞等待到期元素
String orderId = closeQueue.take();
```

- **到期搬运由持有 `RDelayedQueue` 实例的客户端驱动**：应用重启后必须重新 `getDelayedQueue(...)`，否则已投递的到期元素滞留、进不了目标队列——**消费方应用也要创建该实例**（常驻），多实例部署天然互备。
- 实例弃用时 `destroy()`；应用生命周期内常驻的不用。
- 数据在 Redis 但**无消费确认（ack）**：`take()` 取走后进程崩溃即丢；可靠性要求高用 MQ 延迟消息或定时扫描兜底（选型对比 `09-messaging.md` §1）。

## 8. 其他分布式对象速查

| 对象 | 场景 | 一句话边界 |
|---|---|---|
| `RReadWriteLock` | 读多写少（字典/配置缓存重建） | 写锁期间读全阻塞；读锁内禁止再拿写锁 |
| `RSemaphore` | 资源池限并发（如同时跑 N 个导入） | 信号量不防重，只限总量 |
| `RCountDownLatch` | 多任务汇合后放行 | 不可重用（`countDown` 归零即废） |
| `RBloomFilter` | 缓存穿透拦截（判存在再查库） | `tryInit(预期量, 误判率)` 仅首次生效；**判无一定无、判有概率误判**；不支持删元素 |
| `RMapCache` | 要**条目级 TTL** 的 Map | `put(k, v, 60, SECONDS)` 每条独立过期——RedisTemplate Hash 做不到（`04-template-operations.md` §5） |
| `RTopic` | Pub/Sub 的 Redisson 侧 API | 语义同 `09-messaging.md` §2，已有监听容器就不必换 |

```java
RBloomFilter<Long> bf = redissonClient.getBloomFilter("bf:sku:exists");
bf.tryInit(1_000_000L, 0.01);                     // 预期元素量 / 误判率，仅首次生效
bf.add(skuId);
if (!bf.contains(skuId)) { return EMPTY; }        // 判无一定无——拦截穿透
```

## 9. 边界：主从切换可能丢锁

Redis 主从复制是异步的：加锁落在 master、未同步到 replica 时 master 宕机 → 新 master 上锁不存在 → 第二个客户端加锁成功，**互斥被打破**。Redisson 的处理：默认不等同步确认；`RedLock`（多实例多数派）争议大且 Redisson 已不推荐。结论按场景选：

- **可容忍极小概率并发**（防重复提交、缓存回源互斥）→ Redisson 单实例锁足够。
- **绝对互斥**（资金扣减）→ 数据库乐观锁/唯一约束兜底（Redis 锁只当第一道闸），或 fencing token。

## 10. 自检

- [ ] 锁全部走 Redisson / lock4j；存量自写 setnx+expire / Lua 锁已列迁移计划（不是修补）
- [ ] `tryLock` 两个时间都显式：waitTime 限等待、leaseTime（> 业务上界）做持锁硬上限——不裸用看门狗模式（挂死会被无限续期）
- [ ] `finally` 中 `isHeldByCurrentThread()` 判断后 `unlock()`
- [ ] `tryLock` 拿不到的分支有真实处理（繁忙返回/降级），不是 while 空转
- [ ] 锁 key 粒度与业务互斥粒度一致（用户级锁别用全局 key，全局互斥别按用户分 key）
- [ ] 资金/库存类强互斥有 DB 层兜底，不裸信 Redis 锁
- [ ] RRateLimiter 的 `RateType` 明确：多实例共享额度用 `OVERALL`（`PER_CLIENT` 总量按实例数放大）
- [ ] 延迟任务不裸信 RDelayedQueue（无 ack）：高可靠场景有 MQ 延迟消息 / 定时扫描兜底
