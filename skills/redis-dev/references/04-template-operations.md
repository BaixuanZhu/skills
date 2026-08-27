# 数据结构选型与 RedisTemplate 操作

## 1. 结构选型表（场景 → 结构 → 核心 API）

| 场景 | 结构 | ops API | 要点 |
|---|---|---|---|
| 对象缓存 | String | `opsForValue().set/get` | value 是 JSON 字符串（序列化见 `03-serialization.md`） |
| 计数器 / 限流 | String | `opsForValue().increment` | 原子自增；限流需配 TTL，见 §5 |
| 对象部分字段读写 | Hash | `opsForHash().put/get/entries` | 只读写字段不动整体；无字段级 TTL（字段级 `HEXPIRE` 需 Redis 7.4+，勿按它设计——TTL 挂整个 key） |
| 简单队列 | List | `opsForList().leftPush/rightPop` | 无 ack，消费者处理失败消息即丢；可靠场景用 Stream（`09-messaging.md` §3）或 MQ |
| 去重 / 共同关注 | Set | `opsForSet().add/isMember/intersect` | |
| 排行榜 | ZSet | `opsForZSet().incrementScore/reverseRangeWithScores` | 分数同值按字典序，需要时间戳搅局时 `score = 分数*1e13 + (MAX-时间戳)` |
| 签到 / 活跃位图 | Bitmap | `opsForValue().setBit/bitCount` | 按用户存签到 31 bit/人/月；全局日活位图（用户 id 作偏移）1 亿用户约 12.5MB/日 |
| UV 去重统计 | HyperLogLog | `opsForHyperLogLog().add/size` | 固定 ~12KB，误差 0.81%；要精确用 Set（吃内存） |
| 附近的人 | Geo | `opsForGeo().add/radius` | 底层 ZSet |

**String 存对象 vs Hash 存对象**：整体读写/整体过期 → String；频繁改单个字段（如 `stock`、`status`）→ Hash。Hash 没有 field 级 TTL（`HEXPIRE` 需 Redis 7.4+、客户端支持滞后），要"不同字段不同过期"就拆成多个 String key。

## 2. String 精用

set 族语义（写入一律显式带 TTL）：

| API | 命令语义 | 典型用途 |
|---|---|---|
| `set(key, value, ttl)` | SET + EX | 常规写入 |
| `setIfAbsent(key, value, ttl)` | SET NX EX | 幂等占位 / 防重（false = 已有并发在跑）；也是锁的底层命令 |
| `setIfPresent(key, value, ttl)` | SET XX | 仅覆盖已存在的 key |
| `getAndSet(key, value)` | GETSET | 读旧写新（**无 TTL 参数**，覆盖后原 TTL 消失） |

- **set 覆盖会清掉原 TTL**：不带 TTL 的 `set`（含 `getAndSet`）覆盖后 key 变永不过期——"先查再写"的刷新代码最容易踩。查剩余：`getExpire(key)`；取消过期：`persist(key)`。
- `increment(key, delta)` 原子，但**浮点 delta 有精度误差**（0.1 累加不准）——计数场景一律整数（金额用分）。

## 3. Hash 精用

```java
// 字段级原子自增：把同类计数器收拢进一个 key（省 key 数，好按天整体过期）
Long pv = stringRedisTemplate.opsForHash()
        .increment("stat:pv:20260827", "product:1001", 1);

// 大 Hash 遍历用 hscan 游标，不要 entries() 一次全拉
try (Cursor<Map.Entry<String, String>> c = stringRedisTemplate.opsForHash()
        .scan("stat:pv:20260827", ScanOptions.scanOptions().count(500).build())) {
    c.forEachRemaining(e -> process(e.getKey(), e.getValue()));
}
```

- `delete(key, field)` 删字段、`delete(key)` 删整个 key——只差一个参数的重载，别混用。
- 签到这类"字段=天"的玩法用 Bitmap（§1 表），别拿 Hash 硬做。

## 4. Set / ZSet 精用

Set：

| API | 用途 |
|---|---|
| `add / remove / members / isMember` | 基础去重 |
| `intersect(k1, k2)` | 共同关注 / 交集筛选 |
| `randomMembers(key, n)` | 抽奖（只取不删，可重复中奖场景） |
| `move(source, value, dest)` | 集合间挪元素（SMOVE，状态流转：待处理 → 处理中） |

ZSet：

```java
// 滑动窗口限流（完整版）：成员 = 请求标识，分数 = 时间戳
ZSetOperations<String, String> z = stringRedisTemplate.opsForZSet();
z.add(key, uuid, System.currentTimeMillis());
z.removeRangeByScore(key, 0, System.currentTimeMillis() - windowMs);   // 清窗外
long inWindow = z.zCard(key);                                          // 窗内计数
```

| API | 用途 |
|---|---|
| `add(key, member, score)` / `incrementScore` | 上榜 / 加分（原子） |
| `reverseRangeWithScores(key, 0, 9)` | Top 10（带分数） |
| `reverseRank(key, member)` | 查某成员名次（0 起） |
| `removeRangeByScore` | 按分数区间删（滑窗清理 / 淘汰低分） |

## 5. incr 的原子性与限流陷阱

```java
Long count = stringRedisTemplate.opsForValue().increment("rate:login:" + ip);  // 原子
if (count == 1) {                                    // 首次
    stringRedisTemplate.expire("rate:login:" + ip, Duration.ofMinutes(1));
}
```

- `increment` 本身原子，但 **`increment` + `expire` 是两步**：首请求自增后进程崩溃 → key 永不过期，该 IP 永远被限。要求严格时用 Lua 原子化：

```java
private static final String RATE_LIMIT_LUA = """
        local c = redis.call('INCR', KEYS[1])
        if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
        return c
        """;
Long count = stringRedisTemplate.execute(
        new DefaultRedisScript<>(RATE_LIMIT_LUA, Long.class),
        List.of("rate:login:" + ip), "60");
```

- 滑动窗口限流（更平滑）用 ZSet，完整代码见 §4。

## 6. 禁 keys：scan 与批量删除

```java
// ✗ 禁止：keys("*") 阻塞 Redis 单线程，key 越多卡得越久
// ✓ scan 游标迭代
List<String> keys = new ArrayList<>();
ScanOptions options = ScanOptions.scanOptions().match("mall:order:*").count(500).build();
try (Cursor<String> cursor = stringRedisTemplate.scan(options)) {
    cursor.forEachRemaining(keys::add);
}
```

- `count` 是每次往返的**提示值**（非精确页大小，非总数上限）。
- scan 过程中 key 可能变化：**可能返回重复**，需要去重（Set 收集）；与 keys 的瞬时快照语义不同。
- 集群模式 scan 自动扇出到所有 master（`01-connection.md` §3.2）。
- 批量删除一律 `unlink`（异步释放内存，大 value 不阻塞主线程），不要 `del`：

```java
try (Cursor<String> cursor = stringRedisTemplate.scan(options)) {
    cursor.forEachRemaining(key -> stringRedisTemplate.unlink(key));
}
```

## 7. mget / pipeline / 事务

```java
// 多个已知 key 一次取回（服务端一次往返）
List<String> values = stringRedisTemplate.opsForValue().multiGet(List.of("a", "b", "c"));

// 不同命令打包一次往返
List<Object> results = stringRedisTemplate.executePipelined((RedisCallback<Object>) conn -> {
    byte[] k1 = "mall:stock:1".getBytes(), k2 = "mall:stock:2".getBytes();
    conn.stringCommands().get(k1);
    conn.stringCommands().get(k2);
    return null;                                   // pipeline 内返回值忽略，结果按序在返回列表
});
```

| 方式 | 适用 |
|---|---|
| `multiGet` / `multiSet` | 同类命令批量（cluster 模式受 slot 限制，`01-connection.md` §3.2） |
| `executePipelined` | 混合命令打包，减少网络往返（N 次 → 1 次） |
| `SessionCallback` + `multi()/exec()` | 要**原子串行**（事务）时才用 |
| 循环单发 | ✗ N 次网络往返，批量场景禁止 |

- **pipeline ≠ 事务**：pipeline 只省网络往返，命令之间可插入其他客户端命令；要原子串行用 `SessionCallback` 事务——事务独占连接（Lettuce 下走池，`02-pool.md` §1），且**集群模式不可用**（`01-connection.md` §3.2），要原子性改 Lua。

## 8. 自检

- [ ] 计数 / 限流 key 首建即有 TTL（或 Lua 原子化）；滑窗 ZSet 定期清窗外成员
- [ ] 每次 set 都带 TTL（防覆盖写洗掉 TTL）；计数 / 金额是整数
- [ ] 大集合遍历用 scan / hscan 游标；批量删除用 unlink
- [ ] 没有 `keys`；scan 结果已按可能重复处理
- [ ] 批量读用 multiGet / pipeline 而非循环；要原子串行用的是事务 / Lua 而不是 pipeline
- [ ] List 只用于可容忍丢失的简单队列（可靠消息 → Stream `09-messaging.md` §3 / MQ）
