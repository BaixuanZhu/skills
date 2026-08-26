# 序列化：key 乱码、JSON 与类型还原

## 1. 三种方案对比（先选路线）

| 方案 | key 可读 | value 可读 | 类型还原 | 适用 |
|---|---|---|---|---|
| 默认 `JdkSerializationRedisSerializer` | ✗ 二进制前缀 | ✗ 二进制 | ✓ | **禁止用于新代码**（单服务内部遗留除外） |
| `GenericJackson2JsonRedisSerializer` | ✓（key 配 String） | ✓ JSON | ✓ 自动（写入 `@class`） | **单服务默认** |
| `StringRedisTemplate` + 手动 JSON | ✓ | ✓ JSON | 手写目标类型 | **跨服务 / 跨语言 / 契约对外** |

## 2. 默认配置的三个坑（为什么必须显式配）

自动配置的 `RedisTemplate<String, Object>`（`redisTemplate` bean）key 与 value 都用 JDK 序列化：

1. **key 乱码**：`user:1001` 实际存储为 `\xac\xed\x00\x05t\x00\x09user:1001`——redis-cli 里不可读、`keys user:*` 匹配不到、`ttl` 查询要带二进制前缀才能敲。
2. **value 二进制**：其他语言 / 其他序列化方案的服务读不懂。
3. **类结构变更反序列化炸**：改包名/类名 → 旧缓存数据反序列化 `ClassCastException`/`InvalidClassException`，且报错点在读缓存的业务代码里，难定位。

## 3. 推荐配置：单服务（GenericJackson2Json）

```java
@Bean
public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory factory) {
    RedisTemplate<String, Object> template = new RedisTemplate<>();
    template.setConnectionFactory(factory);

    // key / hashKey 一律 String —— 强约束第 1 条
    StringRedisSerializer stringSer = new StringRedisSerializer();
    template.setKeySerializer(stringSer);
    template.setHashKeySerializer(stringSer);

    ObjectMapper mapper = new ObjectMapper();
    mapper.registerModule(new JavaTimeModule());                    // LocalDateTime 支持
    mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS); // 日期输出 "2026-08-26T10:00:00" 而非数组
    mapper.activateDefaultTyping(                                   // 写入 @class，读回自动还原类型
            LaissezFaireSubTypeValidator.instance,
            ObjectMapper.DefaultTyping.NON_FINAL,
            JsonTypeInfo.As.PROPERTY);
    mapper.disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES); // 加字段后旧数据仍可读
    GenericJackson2JsonRedisSerializer jsonSer = new GenericJackson2JsonRedisSerializer(mapper);

    template.setValueSerializer(jsonSer);
    template.setHashValueSerializer(jsonSer);
    return template;
}
```

三个必须项的坑（漏一个就是一个线上问题）：

| 配置 | 漏掉的报错/症状 |
|---|---|
| `JavaTimeModule` | 写含 `LocalDateTime` 字段的对象抛 `InvalidDefinitionException: Java 8 date/time type not supported by default`——`GenericJackson2JsonRedisSerializer` 默认 mapper **不带** JSR310 模块 |
| `activateDefaultTyping` | 读回 `LinkedHashMap` 而不是目标类型（无 `@class` 信息，Jackson 只能还原成 Map） |
| `FAIL_ON_UNKNOWN_PROPERTIES` disable | 实体加字段后，旧缓存里少这个字段 → 读回抛 `UnrecognizedPropertyException`；无法平滑演进 |

> 读回 `LinkedHashMap` 的另一来源：`Jackson2JsonRedisSerializer<>(Object.class)`（无类型信息）——需要 `Jackson2JsonRedisSerializer<>(User.class)` 固定类型或改用 Generic 版。

## 4. 推荐配置：跨服务 / 跨语言（String + 手动 JSON）

跨服务共享的数据**不要依赖 `@class` 自动类型**（包名耦合、其他语言读不懂、类迁移即断）：

```java
@Autowired
private StringRedisTemplate stringRedisTemplate;   // Spring 自动配置直接可用，两边都是 String

private static final ObjectMapper MAPPER = new ObjectMapper()
        .registerModule(new JavaTimeModule())
        .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

public void cacheUser(User user) {
    try {
        stringRedisTemplate.opsForValue()
                .set("user:" + user.getId(), MAPPER.writeValueAsString(user), Duration.ofMinutes(30));
    } catch (JsonProcessingException e) {
        throw new IllegalStateException("user 序列化失败: " + user.getId(), e);
    }
}

public User getUser(long id) throws JsonProcessingException {
    String json = stringRedisTemplate.opsForValue().get("user:" + id);
    return json == null ? null : MAPPER.readValue(json, User.class);   // 目标类型显式写死
}
```

集合用 `new TypeReference<List<User>>() {}` 指定泛型。契约 = 字段名与类型，与类的包结构解耦。

## 5. key 规范（与 Sa-Token 共库）

- **统一业务前缀**：`<app>:<模块>:<业务id>`，如 `mall:order:1001`、`mall:stock:{1001}`——前缀即命名空间，`scan` / 监控 / 清理都靠它。
- 与 Sa-Token 共实例：Sa-Token 集成包对自己的 key 做了前缀封装（可重写 `wrapKey` 定制，见 sa-token-dev `references/07-redis-frontsep.md`），业务侧做好自己的前缀即可避免**覆盖**；但**淘汰策略仍可能挤掉 session**（随机掉线），那是容量/策略问题，前缀解决不了 → `08-server-policy.md` §2。

## 6. 强约束与自检

1. key / hashKey 序列化器 = `StringRedisSerializer`（SKILL.md 强约束 1）。
2. `GenericJackson2JsonRedisSerializer` 一律用**自定义 mapper**（JavaTime + defaultTyping + 忽略未知字段），不用默认构造。
3. **两套序列化互不通用**：手动 `RedisTemplate` 写入的数据，`@Cacheable`（另一套配置，见 `05-spring-cache.md` §3）读出的类型可能对不上——同一份业务数据只从一条路读写。
4. 序列化方案变更（如 JDK → JSON）后，**旧 key 读不回**：上线前按前缀清理（`scan` + `unlink`，见 `04-template-operations.md` §4）或等 TTL 自然过期，不要让两种方案读同一批 key。
