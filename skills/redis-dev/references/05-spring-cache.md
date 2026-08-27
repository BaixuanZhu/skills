# 声明式缓存：@Cacheable 族

## 1. 注解速查

| 注解 | 语义 | 关键参数 |
|---|---|---|
| `@Cacheable` | 先查缓存，未命中执行方法并回填 | `cacheNames`、`key`、`unless`、`condition`、`sync` |
| `@CachePut` | 执行方法并**总是**回填（不查缓存） | 更新后刷新缓存 |
| `@CacheEvict` | 删除缓存 | `allEntries`（清整名）、`beforeInvocation`（默认 false=方法成功后删） |
| `@Caching` | 组合多个同型注解 | |
| `@CacheConfig` | 类级公共配置（cacheNames/keyGenerator） | |

启用：`@EnableCaching` + 依赖 `spring-boot-starter-data-redis` + `spring-boot-starter-cache`。

## 2. key 表达式（SpEL）

```java
@Cacheable(cacheNames = "user", key = "#id")                 // 参数
@Cacheable(cacheNames = "user", key = "#user.id")            // 参数属性
@Cacheable(cacheNames = "user", key = "#result.id")          // 返回值（unless 里用；key 里慎用）
@Cacheable(cacheNames = "user", key = "#root.methodName + ':' + #id")  // 方法名拼 key
```

- **默认 key**（不写 key）：全部参数值拼 `SimpleKey`——无参方法所有调用**共享同一个缓存项**（SimpleKey.EMPTY），极易出错；**显式写 key**。
- `condition`（执行**前**判断，false 则连方法照跑不缓存）、`unless`（执行**后**判断，true 则不回填）方向相反。

## 3. TTL 与序列化：默认配置的两个坑

**不配置 `RedisCacheManager` 时**：① TTL 永不过期（脏数据永驻 + 内存只增）；② value 用 JDK 序列化（key 前缀乱码，`03-serialization.md` §2 的坑原样复现）。**用 @Cacheable 必须显式配 CacheManager**：

```java
@EnableCaching
@Configuration
public class CacheConfig {

    public static final RedisCacheConfiguration BASE = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(30))                                // ① 兜底 TTL
            .computePrefixWith(name -> "cache:" + name + ":")                // key 前缀 cache:user:1001
            .serializeKeysWith(SerializationPair.fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(SerializationPair.fromSerializer(
                    RedisSerializer.json()));                                // ② GenericJackson2Json
    // 注：RedisSerializer.json() 的默认 mapper 不含 JavaTimeModule；实体含 LocalDateTime 时
    // 按 03-serialization.md §3 注入自定义 mapper 的序列化器，且必须补
    // GenericJackson2JsonRedisSerializer.registerNullValueSerializer(mapper, null)——
    // 否则 @Cacheable 缓存 null 时写入 NullValue 抛 "No serializer found"（仅默认构造自动注册）

    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory factory) {
        Map<String, RedisCacheConfiguration> perName = Map.of(
                "user", BASE.entryTtl(Duration.ofMinutes(10)),
                "dict", BASE.entryTtl(Duration.ofHours(24))
        );
        return RedisCacheManager.builder(factory)
                .cacheDefaults(BASE)
                .withInitialCacheConfigurations(perName)      // 每个缓存名单独 TTL
                .transactionAware()
                .build();
    }
}
```

- `@Cacheable` 的序列化与手动 `RedisTemplate` **是两套独立配置**——都显式设，且同一业务数据只走一条路（`03-serialization.md` §6.3）。
- **每个 `cacheNames` 都必须有 TTL**：没在 `perName` 里特判的名字落到 `cacheDefaults`——兜底值必须 > 0，不允许"忘了配就永不过期"。

## 4. 自调用失效（最高频的"不生效"）

```java
@Service
public class OrderService {
    @Cacheable(cacheNames = "order", key = "#id")
    public Order getOrder(long id) { ... }

    public Order view(long id) {
        return this.getOrder(id);   // ✗ 同类内部调用走的是 this，绕过代理，缓存不生效
    }
}
```

注解靠 Spring AOP 代理实现，`this` 调用不经过代理。修复任选其一：

| 方案 | 写法 | 取舍 |
|---|---|---|
| 拆 bean（推荐） | 查询方法挪到独立 `@Service` | 结构最清晰 |
| 注入自身 | `@Autowired private OrderService self;` 后调 `self.getOrder(id)` | 最小改动 |
| AopContext | `((OrderService) AopContext.currentProxy()).getOrder(id)` + `@EnableAspectJAutoProxy(exposeProxy = true)` | 侵入强，不推荐 |

同类失效的还有：`private`/`final` 方法上的注解（代理无法覆写）。

## 5. sync / condition / unless 的组合

- `sync = true`：同 key 未命中时**同 JVM 内**只放一个线程回源（其余等待），单机防击穿；限制：仅 `@Cacheable` 支持、**与 `unless` 互斥**（组合直接抛 `IllegalStateException`）；**多实例部署时每个实例各放一个线程**，分布式防击穿仍需分布式锁（`06-cache-consistency.md` §3）。
- 穿透防护要**缓存 null**：Spring 默认缓存 null 值（`NullValue` 占位）。此时**不要写** `unless = "#result == null"`——它恰好把 null 缓存关掉（写反即事故）。null 缓存建议单独 cacheName 配短 TTL（30s~5min）。

## 6. 更新与删除的搭配

```java
@CacheEvict(cacheNames = "user", key = "#id")          // 更新后删缓存（不是 @CachePut 更新）
public void updateUser(long id, UserPatch patch) { ... }

@CacheEvict(cacheNames = "dict", allEntries = true)    // 列表/模糊类缓存整名清空
public void refreshDict() { ... }
```

为什么删不更（并发写覆盖、懒加载）见 `06-cache-consistency.md` §2。`@CachePut` 仅用于"必须拿方法执行结果回填"的场景，常规更新一律 Evict。

## 7. 自检

- [ ] 配了 `RedisCacheManager`，`cacheDefaults` 的 `entryTtl` > 0，value 序列化非 JDK
- [ ] 所有 `@Cacheable` 显式 `key`；无参方法未裸奔
- [ ] 同类内部没有 `this.缓存方法()` 调用；注解方法非 private/final
- [ ] 需要防穿透时**没有**写 `unless = "#result == null"`
- [ ] 更新方法用 `@CacheEvict`（或明确的 `@CachePut` 理由），默认方法成功后才删
