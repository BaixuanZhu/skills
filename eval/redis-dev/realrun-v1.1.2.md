# redis-dev 三件套实跑验证（v1.1.2 技能态）

- **日期**：2026-08-28
- **环境**：JDK 21.0.12 / Maven 3.9.16 / Spring Boot **3.3.13** / Redisson **3.45.0**（裸依赖，无 starter）/ spring-data-redis 3.3.x / Redis 7（docker `redis:7-alpine`，本机 6379，容器名 `redis-eval`）
- **测试项目**：`outputs/redis-realtest/`（仓库外 scratch，未提交）——20 条 JUnit 用例，代码形状逐行镜像技能处方：`TestConfig` = 03 §3 mapper 四件套 + 05 §3 CacheManager（BASE 30min + user 10min / dict 24h perName + 前缀 `cache:name:key`）+ 07 §1 裸 redisson 从 `RedisProperties` 建 Config。

## 结论

**20/20 全绿（BUILD SUCCESS）**。三处处方照抄可跑。实跑揪出 2 处技能内容问题，已修复并升 v1.1.3：

1. **03 §3 表第 3 行坑方向写反（P1 事实错误）**：原文「实体加字段后，旧缓存里少这个字段 → 读回抛 `UnrecognizedPropertyException`」。实测（严格 Jackson）：**加字段、旧 JSON 少字段不抛**（字段 null 兜底）；真抛的是**字段改名 / 删除**（旧 JSON 残留类没有的字段）。→ 已改写该行。
2. **jackson-datatype-jsr310 依赖盲点（P2）**：纯 data-redis 项目（无 starter-web / starter-json）`new JavaTimeModule()` **编译失败**（jsr310 不在 classpath，实测 Boot 3.3）。→ 03 §3 补一行依赖说明（Boot 管版本）。

## 用例矩阵（全部 PASS）

### T1 序列化全链路（8 条）——03-serialization §2/§3

| 用例 | 验证的声明 | 结果 |
|---|---|---|
| jdkKeyBinaryPrefix | JDK 序列化 key 前缀 `\xac\xed\x00\x05t\x00\x09`（16 字节逐位比对） | PASS |
| defaultGenericJacksonLacksJavaTime | 默认构造 GenericJackson 不带 JSR310 → `Java 8 date/time type ... not supported` | PASS |
| fullChainRoundTrip | 处方 mapper 全链路：`@class` 写入、日期 ISO 可读（`2026-08-28T10:00`）、读回 `User` 精确类型且 equals | PASS |
| withoutDefaultTypingReadsAsLinkedHashMap | 无 defaultTyping → 读回 `LinkedHashMap` | PASS |
| missingFieldDoesNotThrowEvenWithStrictJackson | 加字段、旧 JSON 少字段 → 严格 Jackson **不抛**（null 兜底）→ 推翻技能原表述 | PASS |
| renamedFieldThrowsOnStrictMapperButNotSkillMapper | 字段改名（JSON 多出 `name`、类只有 `nickname`）→ 严格 Jackson 抛 `UnrecognizedPropertyException`；技能 mapper 不抛 | PASS |
| nullValueSerializerMissing | 自定义 mapper 不注册 NullValueSerializer → 序列化 `NullValue` 抛 `No serializer found` | PASS |
| nullValueRoundTripWithSkillSerializer | 注册后 NullValue 可往返 | PASS |

### T2 @Cacheable（5 条）——05-spring-cache §3-§5

| 用例 | 验证的声明 | 结果 |
|---|---|---|
| externalCallHitsCacheWithPerNameTtl | 外部两次调用只回源一次；key 为 `cache:user:1`（computePrefixWith）；user 走 perName TTL ≤600s | PASS |
| selfInvocationBypassesCache | 同类 `this.` 调用每次穿透（计数 2）；外部直调第二次命中（计数只 +1） | PASS |
| perCacheNameTtlAndFallback | dict 24h（86400 档）；未特判 order 落 cacheDefaults 30min（1800 档） | PASS |
| noTtlConfigMeansEternal | 不配 entryTtl 的 CacheManager → 写入 `ttl = -1` 永不过期 | PASS |
| nullCachingDefaultVsUnless | null 默认被缓存（第二次命中，计数 1）；`unless="#result == null"` 关闭 null 缓存（每次回源，计数 2） | PASS |

### T3 Redisson（7 条）——07-redisson §1/§3-§7

| 用例 | 验证的声明 | 结果 |
|---|---|---|
| propsBasedClientWorks | 从 Boot `RedisProperties` 建 Config 的裸 client 可正常读写（07 §1 处方） | PASS |
| basicMutex | 持锁期间他线程 `tryLock(0, 30s)` 拿不到；释放后可拿 | PASS |
| reentrantSameThread | 同线程重入成功（计数），他线程仍被挡（07 §5） | PASS |
| leaseExpiryReleasesLockAndStaleUnlockThrows | `tryLock(0, 1s)` 不 unlock，1.6s 后他线程可拿（**租期硬上限，业务没跑完也释放**）；原持有者再 unlock 抛 `IllegalMonitorStateException`（强约束 7 的来由） | PASS |
| watchdogRenewsIndefinitely | `lockWatchdogTimeout=3s` 下不传 leaseTime 持锁 4.5s 仍锁着（**看门狗续期**，超过初始租期） | PASS |
| rateLimiterOverall | OVERALL 2/s：第 3 个 `tryAcquire` 被拒；窗口过后恢复；`trySetRate` 幂等（二次调用不抛） | PASS |
| delayedQueueDeliversAfterDelay | `offer(x, 2s)`：目标队列未到期取不到；offer→可见 ≈1.9s 守时 | PASS |

## 测试侧发现（不改技能，留档）

- **@Cacheable CGLIB 代理不暴露目标对象字段**：测试里对代理直接读计数器字段得 null，须走方法——业务代码无此形态，属测试写法问题。
- **RBlockingQueue.poll 亚秒超时按整秒生效**（Redis BLPOP 粒度）：`poll(200ms)` 实际阻塞 ~1s；延迟本身守时（测量起点须从 offer 起算）。
- **NullValue 经自定义 mapper 反序列化非单例实例**，但 @Cacheable 命中判定不受影响（nullCachingDefaultVsUnless 第二次调用未回源，实测）。

## 修复对照（v1.1.3）

- `skills/redis-dev/references/03-serialization.md`：§3 表第 3 行方向改写 + §3 补 jsr310 依赖行。
- `skills/redis-dev/SKILL.md`：version 1.1.2 → 1.1.3。
