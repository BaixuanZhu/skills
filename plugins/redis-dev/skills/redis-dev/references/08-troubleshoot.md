# 排错：症状 → 原因 → 修复

## 1. 总表

| 症状（报错/现象） | 首查原因 | 修复 | 详见 |
|---|---|---|---|
| `Unable to connect to Redis` / `Connection refused` | 地址/端口/网络/防火墙；**Boot 2 与 3/4 配置前缀写错**（`spring.redis` vs `spring.data.redis`） | 核对前缀与版本；`redis-cli -h host -p port ping` 先通 | `01-connection.md` §4 |
| `ERR Client sent AUTH, but no password is set` | `password: ""` 空串被当密码；或老版本 `requirepass` 与 ACL 混用 | 无密码删掉配置行；ACL 配 `username` | `01-connection.md` §2 |
| `RedisCommandTimeoutException: Command timed out` | 命令超时配置过小 / 慢命令（`keys *`）/ 大 value / 网络 | 查超时配置与慢命令；禁 `keys` | `02-pool.md` §5、`04` §3 |
| `Could not get a resource from the pool` / pool exhausted | **先确认 client-type**：Jedis 每操作借还连接，`max-wait` 排队超时 / `max-active` 不足是常态原因；Lettuce 普通命令不走池，真报池错多半在事务 / 阻塞命令（`02-pool.md` §1） | 调池参数；阻塞命令加超时；确认真需要池 | `02-pool.md` §3-§5 |
| key 显示 `\xac\xed\x00\x05t\x00\x03...` 乱码 | key 用了 JDK 序列化 | key 序列化器改 `StringRedisSerializer`，**按前缀清掉旧 key** | `03-serialization.md` §2 |
| `InvalidDefinitionException: Java 8 date/time type ... not supported` | GenericJackson 的 mapper 没注册 `JavaTimeModule` | 按推荐配置注入自定义 mapper | `03-serialization.md` §3 |
| 读回 `LinkedHashMap`（强转 `User` 报 `ClassCastException`） | 未启用 `activateDefaultTyping` / 反序列化目标类型写 `Object.class` | 开 default typing 或显式 `readValue(json, User.class)` | `03-serialization.md` §3/§4 |
| `UnrecognizedPropertyException`（实体加字段后旧缓存报错） | mapper 默认拒绝未知字段 | `FAIL_ON_UNKNOWN_PROPERTIES` disable；或清旧缓存 | `03-serialization.md` §3 |
| `SerializationException` ... `No serializer found ... NullValue` | 自定义 mapper 的 GenericJackson2Json 未注册 NullValue 序列化器（仅默认构造注册），`@Cacheable` 缓存 null 触发 | `GenericJackson2JsonRedisSerializer.registerNullValueSerializer(mapper, null)` | `03-serialization.md` §3、`05-spring-cache.md` §3 |
| 换序列化方案后旧 key 全读失败 | 两种序列化互不通用 | 上线前按前缀 `scan`+`unlink` 清理或等 TTL | `03-serialization.md` §6.4 |
| `@Cacheable` 完全不生效（每次都查库） | 自调用绕过代理 / private/final 方法 / 没配 `@EnableCaching` | 按下方清单逐项排查 | `05-spring-cache.md` §4 |
| `@Cacheable` 缓存永不过期 | 没配 `RedisCacheManager` 的 `entryTtl` | 显式配 cacheDefaults + perName | `05-spring-cache.md` §3 |
| `@Cacheable` 缓存的 value 也是二进制乱码 | cacheManager 默认 JDK 序列化（与 RedisTemplate 是两套配置） | `serializeValuesWith` 显式配 JSON | `05-spring-cache.md` §3 |
| `IllegalMonitorStateException`（unlock 时） | 租期已过锁已易主 / 非持有线程解锁 | `isHeldByCurrentThread()` 判断后再解；查 leaseTime 决策 | `07-redisson.md` §4 |
| 业务执行中超时后并发进入（锁"失效"） | 显式传了 `leaseTime` → 无看门狗，到期自动释放 | 时长不可预估就不传 leaseTime | `07-redisson.md` §4 |
| TTL 到期的 key 在 `scan`/`dbsize` 里还在 | 惰性+定期删除机制，物理删除滞后 | 无需处理（不可读即正确语义） | — |
| `CROSSSLOT` / 多 key 命令报错 | 集群模式 key 不在同一 slot | hash tag `{userId}` 绑定；事务改 Lua | `01-connection.md` §3.2 |
| scan 结果有重复 | scan 语义允许重复 | 调用侧 Set 去重 | `04-template-operations.md` §1 |
| Redisson starter 引入后 RedisTemplate 行为异常 | starter 把连接工厂整体替换为 Redisson | 知情引入；不想要全局替换就用裸 `redisson` 依赖 | `07-redisson.md` §1 |

## 2. @Cacheable 不生效排查清单（按序执行）

1. 启动类/配置类有 `@EnableCaching`？
2. 调用路径是否**经过代理**：不是同类 `this.` 调用、方法非 private/final？
3. 方法所在类是 Spring bean（`@Service` 等注解扫描到）？
4. `cacheNames` 是否拼错（与 CacheManager 的 perName 不匹配会静默落默认配置）？
5. `condition` 是否把请求全拦了（执行前返回 false 时方法**正常执行但不缓存**）？
6. key 冲突：无参/默认 SimpleKey 时多个方法/参数共用了同一个缓存项？

## 3. 连接失败排查清单（按序执行）

1. `redis-cli -h <host> -p <port> ping` → 不通是网络/地址问题，与应用无关
2. 配置前缀 vs Boot 版本（`spring.data.redis.*` / `spring.redis.*`）
3. `password` 空串问题（无密码应删行）
4. 哨兵模式：`sentinel.nodes` 填的是哨兵（26379）不是数据节点；`master` 是名称不是地址
5. 集群模式：`cluster.nodes` 是**种子节点**——Lettuce 会自动发现完整拓扑，但至少一个可达；生产仍列全 master，避免种子单点
6. 云 Redis：白名单/安全组是否放行应用出口 IP

## 4. 使用规则

- 拿到 Redis 相关报错，**先在本表按症状匹配**，命中即按「修复」列动作，未命中再分析。
- 修复动作涉及代码修改的，改完对照 SKILL.md「核心强约束」自检，防止按下葫芦浮起瓢。
