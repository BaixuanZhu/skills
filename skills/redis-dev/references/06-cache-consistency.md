# 缓存一致性：Cache Aside 与穿透 / 击穿 / 雪崩

## 1. Cache Aside 标准流程（读写路径）

```
读：cache.get(key)
    ├─ 命中 → 返回
    └─ 未命中 → DB 查询 → cache.set(key, value, ttl=基础+随机抖动) → 返回
写：DB 更新（事务提交）→ cache.delete(key)        ← 删，不是改
```

## 2. 写路径决策：为什么「先更 DB，再删缓存」

| 方案 | 并发时序问题 | 结论 |
|---|---|---|
| 更新缓存（非删除） | 写 A 与写 B 并发，B 后落库先写缓存 → 缓存停留旧值；且未读先算浪费 | ✗ |
| 先删缓存，再更新 DB | 删后、库未更完时并发读未命中 → 回源读到**旧库值**并回填 → 缓存停留旧值 | ✗ |
| **先更新 DB，再删缓存**（默认） | 读回填旧值窗口极小（需"读先于写开始、回填晚于删除完成"的交错），通常可接受 | ✓ 默认 |
| 延迟双删 | 先删 → 更库 → sleep(主从延迟+余量) → 再删一次，清掉窗口期回填的旧值 | ✓ 高一致要求 |

延迟双删的局限：延迟只能估计；sleep 占用请求线程（异步化则引入新的时序问题）。它是**缓解**不是消除——要强一致就不该用缓存，或走 binlog 订阅（Canal 监听变更删缓存，业务代码零侵入）。

## 3. 三件套对照表

| # | 现象 | 根因 | 方案（按优先级） |
|---|---|---|---|
| 穿透 | 反复查**不存在**的数据，每次都打到 DB（恶意构造 id / 脏链接） | 缓存只挡"存在"的数据 | ① 参数校验拦非法 id ② **缓存 null + 短 TTL**（30s~5min，`05-spring-cache.md` §5）③ 高频场景布隆过滤器前置（Redisson `RBloomFilter`，判"一定不存在"才有效；误判率换内存，有添加无删除需定期重建） |
| 击穿 | **单个热点 key** 过期瞬间，并发未命中全部回源 | 热点 + 过期叠加 | ① **互斥锁回源（同步，§5）**：拿到分布式锁的线程查库回填，其余等待后重读缓存 ② **逻辑过期 + 异步重建（§6）**：读到"已过期"返回旧值 + 后台线程刷新，请求不阻塞 ③ 单实例场景 `sync = true`（`05-spring-cache.md` §5） |
| 雪崩 | **大批 key 同时过期** / Redis 实例宕机，DB 被打垮 | TTL 同值 / 实例单点 | ① **TTL 随机抖动**（基础值 + 10%~30% 随机，写缓存的统一规则）② 实例宕机：多级缓存（Caffeine 本地兜底）+ 接口熔断限流降级 ③ 高可用部署（哨兵/集群，`01-connection.md` §3） |

三者区分一句话：穿透是**数据不存在**，击穿是**一个热 key**，雪崩是**一大片 key 或整个实例**。

## 4. TTL 抖动（写进所有 set）

```java
public static Duration ttlWithJitter(Duration base) {
    long jitter = (long) (base.toMillis() * (0.1 + Math.random() * 0.2));  // 10%~30%
    return base.plusMillis(jitter);
}

stringRedisTemplate.opsForValue().set(key, json, ttlWithJitter(Duration.ofMinutes(30)));
```

`@Cacheable` 无法逐次抖动（TTL 挂在 cacheName 级）——同批部署的注解缓存靠 `perName` 错开 TTL 数值缓解。

## 5. 击穿的同步回源：互斥锁 + DoubleCheck（伪代码）

```
读 key：
  cached = GET(key)
  cached ≠ null → 是 "<null>" 哨兵 ? 返回 null（穿透防护已含） : 返回 JSON 反序列化值

  未命中 → lock = getLock("lock:" + key)，tryLock(wait=3s, lease=30s)   // lease > 回源耗时上界（07-redisson.md §4）
    拿不到锁 → 等 200ms 重读缓存一次；仍无 → 降级返回（null / 默认值 / 提示稍后，别空转重试）
    拿到锁 →
      try:
        DoubleCheck：再 GET 一次——等锁期间别人可能已回填，有值直接返回
        value = 查库（唯一回源点）
        value == null → SETEX(key, "<null>", 60s)                // 短 TTL 防穿透
        否则         → SETEX(key, JSON(value), 30min + 抖动 §4)
        返回 value
      finally: isHeldByCurrentThread() 才 unlock（强约束 7）
```

- `"<null>"` 哨兵：JSON 序列化产物以 `{` / `[` 开头，字符串哨兵不会撞型——null 命中与未命中靠它区分。
- 拿不到锁的分支必须有降级出口，不是 while 空转压垮 Redis。

## 6. 击穿的异步回源：逻辑过期 + 后台重建

互斥锁回源（§5）里等锁请求会排队；热点 key 不接受等待时用逻辑过期——**读请求永不阻塞**，代价是过期窗口内返回旧值。

```
value 结构：JSON{ data: 原值, expireAt: 逻辑过期时间戳 }；物理 TTL 设长（如 1 天，只做兜底）

读：
  entry = GET(key)
  entry == null（冷 key）→ 同步回源一次或降级
  entry.expireAt > now   → 返回 entry.data
  已逻辑过期 →
    返回 entry.data（旧值照常服务）
    tryLock 成功 → 提交异步任务（独立线程池，非请求线程）：查库 → 写回新 data + 新 expireAt → unlock
    tryLock 失败 → 已有人在重建，本次直接返回旧值
```

- 这里的锁防的是**重复回源**，不是互斥读——用途与 §5 不同。
- 重建失败旧值继续服务 + 告警，读路径不感知。
- 需要**兜底刷新**（启动预热 / 定时任务）：无人访问的 key 逻辑过期后会一直旧值下去。

## 7. 自检

- [ ] 所有 set 带 TTL 且含随机抖动（含 null 缓存——短且抖动可省）
- [ ] 写路径是「先更 DB，再删缓存」；高一致场景评估过延迟双删/Canal
- [ ] 热点 key 回源有互斥（同步，§5）或逻辑过期异步重建（§6），不是裸回源；多实例不用 `sync=true` 当分布式锁
- [ ] 布隆过滤器仅用于"判不存在"拦截，且知道误判与不可删除的代价
- [ ] DB 挂了 / Redis 挂了有降级出口（熔断、默认值），不是 500
