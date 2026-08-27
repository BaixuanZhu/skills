# RedisTemplate：低频 API 与易错陷阱

常规读写与结构选型（get/set、opsForHash / opsForZSet 日常操作）是通用知识，不在本文；本文只收**低频 API 的非直觉语义**与**高频踩坑点**。

## 1. 禁 keys：scan 家族与批量删除

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

- Hash / Set / ZSet 的大集合遍历同样禁全量拉（`entries()` / `members()` / `range()` 一次全返回），用各自的游标 scan：`opsForHash().scan(key, options)` / `opsForSet().scan(key, options)` / `opsForZSet().scan(key, options)`——游标语义同上。

## 2. 批量读写：mget / pipeline

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
| `SessionCallback` + `multi()/exec()` | 要**原子串行**（事务）时才用（§3） |
| 循环单发 | ✗ N 次网络往返，批量场景禁止 |

- **multiGet 结果与入参按位对齐**：缺失的 key 对应位置是 `null`——先过滤 null 再按索引对 key 是错位 bug 的常见来源。
- pipeline callback 里用 connection 层命令（`conn.stringCommands()`），callback 返回 null；结果按序在返回的 `List<Object>` 里，按命令预期类型转型（GET 回 `String`，INCR 回 `Long`）。
- **pipeline ≠ 事务**：pipeline 只省网络往返，命令之间可穿插其他客户端命令；要原子串行 → 事务（§3），要原子计算 → Lua（§4）。

## 3. 事务：SessionCallback + multi/exec

```java
List<Object> results = stringRedisTemplate.execute(new SessionCallback<List<Object>>() {
    @Override
    @SuppressWarnings({"unchecked", "rawtypes"})
    public List<Object> execute(RedisOperations operations) {
        operations.watch("stock:1");               // 乐观锁：exec 前被他人改动 → 事务丢弃
        operations.multi();
        operations.opsForValue().decrement("stock:1");
        operations.opsForList().rightPush("orders", "1001");
        return operations.exec();                  // 各命令结果按序；watch 冲突时返回 null
    }
});
```

- **Redis 事务没有回滚**：入队命令某条在 exec 时运行时报错（如对 String key 执行 `rightPush`），**其余命令照常生效**——事务只保证「执行期间不被其他客户端插队」，不保证全成功全失败。与关系型数据库直觉相反，别按"出错自动回滚"设计。
- `@Transactional` 与 Redis 事务无关——Spring 声明式事务不会自动包 multi/exec。
- 事务期间独占连接（需要池或专用连接，`02-pool.md` §1）；**集群模式不可用**（`01-connection.md` §3.2）——跨命令原子性改 Lua（§4）。
- 多数"看起来要事务"的场景：要么单命令本身原子（`increment` / `setIfAbsent`），要么 Lua，要么业务幂等——SessionCallback 是最后手段。

## 4. Lua：DefaultRedisScript

```java
// incr + expire 两步原子化：首请求自增后崩溃 → key 永不过期、该维度永久被限
private static final String RATE_LIMIT_LUA = """
        local c = redis.call('INCR', KEYS[1])
        if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
        return c
        """;
Long count = stringRedisTemplate.execute(
        new DefaultRedisScript<>(RATE_LIMIT_LUA, Long.class),
        List.of("rate:login:" + ip), "60");
```

- `DefaultRedisScript` 建成静态常量 / 单例 bean：SDR 首次自动用 EVALSHA，脚本未缓存时降级 EVAL，无需手工管理 sha。
- **key 一律走 KEYS、参数走 ARGV**：key 藏进 ARGV 单机能跑，集群下 slot 路由失效必错；集群下所有 KEYS 必须同 slot（跨 slot 用 hash tag `{...}` 收拢）。
- 结果类型支持 Long / Boolean / String / List——Lua 返回 1/0 时 Boolean 结果自动映射 true / false。
- 典型用途：incr+expire 原子化（上方）、解锁校验（识别存量自写锁用，`07-redisson.md` §2）。

## 5. 陷阱速查

| 陷阱 | 说明 / 修复 |
|---|---|
| set 覆盖清掉原 TTL | 不带 TTL 的 `set` / `getAndSet`（无 TTL 参数）覆盖后 key **永不过期**——"先查再写"刷新代码高发；写入一律显式带 TTL；查剩余 `getExpire`、取消过期 `persist` |
| increment 浮点误差 | 浮点 delta 按 double 累加，0.1 反复加不准；计数 / 金额一律整数（金额用分） |
| Hash 无字段级 TTL | TTL 挂整个 key（`HEXPIRE` 需 Redis 7.4+、客户端支持滞后，勿按它设计）；要字段级过期拆多个 String key，或 Redisson `RMapCache`（`07-redisson.md` §8） |
| Hash delete 重载 | `delete(key)` 删整个 key、`delete(key, field)` 删单字段——只差一个参数语义全变 |
| multiGet 含 null | 结果按位对齐，缺失 key 是 null（§2） |
| List 当可靠队列 | `leftPush`/`rightPop` 无 ack，消费失败即丢；可靠场景用 Stream（`09-messaging.md` §3）或 MQ |

## 6. 低频结构：Bitmap / HyperLogLog

| 场景 | API | 要点 |
|---|---|---|
| 签到 / 日活位图 | `opsForValue().setBit/getBit`、`bitCount(key)` | 每用户每月一个 key、天作偏移（31 bit/人/月）；全站日活用户 id 作偏移，1 亿用户约 12.5MB/日 |
| UV 去重统计 | `opsForHyperLogLog().add/size` | 固定 ~12KB、误差 0.81%；要精确用 Set（吃内存） |

## 7. 自检

- [ ] 没有 `keys`；大集合遍历用 scan 家族游标，批量删除用 unlink
- [ ] multiGet 结果按位对齐（含 null），没有过滤 null 后再对位
- [ ] pipeline 没被当事务用；用事务时知道「无回滚」
- [ ] Lua：key 走 KEYS；集群下同 slot
- [ ] 写入显式带 TTL（防覆盖洗掉原 TTL）；计数 / 金额整数；incr+expire 已 Lua 原子化
- [ ] List 只用于可容忍丢失的简单队列（可靠消息 → Stream `09-messaging.md` §3 / MQ）
