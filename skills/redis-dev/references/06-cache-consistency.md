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
| 击穿 | **单个热点 key** 过期瞬间，并发未命中全部回源 | 热点 + 过期叠加 | ① **互斥锁回源**：拿到分布式锁的线程查库回填，其余等待后重读缓存（代码见下）② 逻辑过期：value 内嵌过期时间，读到"已过期"返回旧值 + 异步线程刷新（不阻塞请求，接受短暂旧值）③ 单实例场景 `sync = true`（`05-spring-cache.md` §5） |
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

## 5. 击穿的互斥锁回源（完整模板）

```java
private static final ObjectMapper MAPPER = new ObjectMapper().registerModule(new JavaTimeModule());
private static final String NULL_MARK = "<null>";   // 哨兵：序列化产物是 JSON（{ 或 [ 开头），不会撞型

public User getUser(long id) throws InterruptedException {
    String key = "user:" + id;
    String cached = stringRedisTemplate.opsForValue().get(key);
    if (cached != null) {
        return NULL_MARK.equals(cached) ? null : fromJson(cached);      // null 缓存命中（防穿透）
    }
    RLock lock = redissonClient.getLock("lock:" + key);
    if (!lock.tryLock(3, TimeUnit.SECONDS)) {                            // 最多等 3s；看门狗续期（07-redisson.md §4）
        TimeUnit.MILLISECONDS.sleep(200);                                // 拿不到锁：稍候重读一次缓存
        cached = stringRedisTemplate.opsForValue().get(key);
        return cached == null || NULL_MARK.equals(cached)
                ? null : fromJson(cached);                               // 仍无 → 降级（null / 默认值 / 提示稍后，按业务定）
    }
    try {
        cached = stringRedisTemplate.opsForValue().get(key);             // DoubleCheck：等锁期间别人可能已回填
        if (cached != null) {
            return NULL_MARK.equals(cached) ? null : fromJson(cached);
        }
        User user = userMapper.selectById(id);                           // 唯一回源点
        if (user == null) {
            stringRedisTemplate.opsForValue().set(key, NULL_MARK, Duration.ofSeconds(60));  // 短 TTL 防穿透
            return null;
        }
        stringRedisTemplate.opsForValue().set(key, toJson(user), ttlWithJitter(Duration.ofMinutes(30)));
        return user;
    } finally {
        if (lock.isHeldByCurrentThread()) lock.unlock();
    }
}

private User fromJson(String json) {
    try { return MAPPER.readValue(json, User.class); }
    catch (JsonProcessingException e) { throw new IllegalStateException("缓存反序列化失败", e); }
}

private String toJson(User user) {
    try { return MAPPER.writeValueAsString(user); }
    catch (JsonProcessingException e) { throw new IllegalStateException("缓存序列化失败", e); }
}
```

要点：**DoubleCheck**（拿锁后再查一次）、null 短 TTL、`finally` + `isHeldByCurrentThread` 解锁（强约束 7）；拿不到锁不无限等——重读一次仍无就降级返回（`ttlWithJitter` 见 §4）。

## 6. 自检

- [ ] 所有 set 带 TTL 且含随机抖动（含 null 缓存——短且抖动可省）
- [ ] 写路径是「先更 DB，再删缓存」；高一致场景评估过延迟双删/Canal
- [ ] 热点 key 回源有互斥（多实例不用 `sync=true` 当分布式锁）
- [ ] 布隆过滤器仅用于"判不存在"拦截，且知道误判与不可删除的代价
- [ ] DB 挂了 / Redis 挂了有降级出口（熔断、默认值），不是 500
