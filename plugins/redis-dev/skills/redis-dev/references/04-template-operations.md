# 数据结构选型与 RedisTemplate 操作

## 1. 结构选型表（场景 → 结构 → 核心 API）

| 场景 | 结构 | ops API | 要点 |
|---|---|---|---|
| 对象缓存 | String | `opsForValue().set/get` | value 是 JSON 字符串（序列化见 `03-serialization.md`） |
| 计数器 / 限流 | String | `opsForValue().increment` | 原子自增；限流需配 TTL，见 §2 |
| 对象部分字段读写 | Hash | `opsForHash().put/get/entries` | 只读写字段不动整体；无字段级 TTL（TTL 挂整个 key） |
| 简单队列 | List | `opsForList().leftPush/rightPop` | 无 ack，消费者处理失败消息即丢；可靠场景用 Redis Stream 或 MQ |
| 去重 / 共同关注 | Set | `opsForSet().add/isMember/intersect` | |
| 排行榜 | ZSet | `opsForZSet().incrementScore/reverseRangeWithScores` | 分数同值按字典序，需要时间戳搅局时 `score = 分数*1e13 + (MAX-时间戳)` |
| 签到 / 活跃位图 | Bitmap | `opsForValue().setBit/bitCount` | 按用户存签到 31 bit/人/月；全局日活位图（用户 id 作偏移）1 亿用户约 12.5MB/日 |
| UV 去重统计 | HyperLogLog | `opsForHyperLogLog().add/size` | 固定 ~12KB，误差 0.81%；要精确用 Set（吃内存） |
| 附近的人 | Geo | `opsForGeo().add/radius` | 底层 ZSet |

**String 存对象 vs Hash 存对象**：整体读写/整体过期 → String；频繁改单个字段（如 `stock`、`status`）→ Hash。Hash 没有 field 级 TTL，要"不同字段不同过期"就拆成多个 String key。

## 2. incr 的原子性与限流陷阱

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

- 滑动窗口限流：ZSet（`add(成员, 当前毫秒)` + `removeRangeByScore` 清窗口外 + `zcard` 计数）。

## 3. 禁 keys，用 scan

```java
// ✗ 禁止：keys("*") 阻塞 Redis 单线程，key 越多卡得越久
// ✓ scan 游标迭代
List<String> keys = new ArrayList<>();
ScanOptions options = ScanOptions.scanOptions().match("mall:order:*").count(500).build();
try (Cursor<String> cursor = stringRedisTemplate.scan(options)) {   // Spring Data Redis 2.x+ 提供 scan
    cursor.forEachRemaining(keys::add);
}
```

- `count` 是每次往返的**提示值**（非精确页大小，非总数上限）。
- scan 过程中 key 可能变化：**可能返回重复**，需要去重（Set 收集）；与 keys 的瞬时快照语义不同。
- 集群模式 scan 自动扇出到所有 master（`01-connection.md` §3.2）。

## 4. 按模式批量删除（scan + unlink）

```java
try (Cursor<String> cursor = stringRedisTemplate.scan(options)) {
    cursor.forEachRemaining(key -> stringRedisTemplate.unlink(key));
}
```

`unlink` 异步释放内存（大 value 不阻塞主线程），批量删除一律用它替代 `del`。

## 5. pipeline 批量与 mget

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
| 循环单发 | ✗ N 次网络往返，批量场景禁止 |

## 6. 自检

- [ ] 计数/限流 key 首建即有 TTL（或 Lua 原子化）
- [ ] 没有 `keys`；`scan` 结果已按可能重复处理
- [ ] 批量删除用 `unlink`；批量读用 `multiGet`/pipeline 而非循环
- [ ] List 只用于可容忍丢失的简单队列（可靠消息 → MQ / Stream）
