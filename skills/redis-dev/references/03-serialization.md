# 序列化：key 乱码、JSON 与类型还原

## 1. 三种方案对比（先选路线）

| 方案 | key 可读 | value 可读 | 类型还原 | 适用 |
|---|---|---|---|---|
| 默认 `JdkSerializationRedisSerializer` | ✗ 二进制前缀 | ✗ 二进制 | ✓ | **禁止用于新代码**（单服务内部遗留除外） |
| `GenericJackson2JsonRedisSerializer` | ✓（key 配 String） | ✓ JSON | ✓ 自动（写入 `@class`） | **单服务默认** |
| `StringRedisTemplate` + 手动 JSON | ✓ | ✓ JSON | 手写目标类型 | **跨服务 / 跨语言 / 契约对外** |

> **类型信息三来源**：payload 里的 `@class` / template 固定类型（`Jackson2JsonRedisSerializer<T>`，一类一个 template）/ 读侧显式给出（`readValue` / `convertValue`）。去掉 `@class` 就必须从后两者补——干净 payload 与自动还原类型不可兼得，这是 §4 跨服务禁止 `@class` 的根因。

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
    GenericJackson2JsonRedisSerializer.registerNullValueSerializer(mapper, null); // @Cacheable 缓存 null 用（下表第 4 行）
    GenericJackson2JsonRedisSerializer jsonSer = new GenericJackson2JsonRedisSerializer(mapper);

    template.setValueSerializer(jsonSer);
    template.setHashValueSerializer(jsonSer);
    return template;
}
```

四个必须项的坑（漏一个就是一个线上问题）：

| 配置 | 漏掉的报错/症状 |
|---|---|
| `JavaTimeModule` | 写含 `LocalDateTime` 字段的对象抛 `InvalidDefinitionException: Java 8 date/time type not supported by default`——`GenericJackson2JsonRedisSerializer` 默认 mapper **不带** JSR310 模块 |
| `activateDefaultTyping` | 读回 `LinkedHashMap` 而不是目标类型（无 `@class` 信息，Jackson 只能还原成 Map） |
| `FAIL_ON_UNKNOWN_PROPERTIES` disable | 实体加字段后，旧缓存里少这个字段 → 读回抛 `UnrecognizedPropertyException`；无法平滑演进 |
| `registerNullValueSerializer` | 序列化器被 `@Cacheable` 复用且缓存 null 时，写入 `NullValue` 抛 `No serializer found`——**仅默认构造自动注册，自定义 mapper 不会**（2.7 / 3.x / 4.x 源码一致） |

> 读回 `LinkedHashMap` 的另一来源：`Jackson2JsonRedisSerializer<>(Object.class)`（无类型信息）——需要 `Jackson2JsonRedisSerializer<>(User.class)` 固定类型或改用 Generic 版。

## 4. 跨服务 / 跨语言：禁止 @class

- ✗ **禁止**：跨服务 / 跨语言共享的数据使用 `@class` 自动类型还原（`GenericJackson2JsonRedisSerializer` + defaultTyping 那套）——payload 携带 Java 包名，其他语言读不懂、类一迁移旧数据即断。
- ✓ **要求**：payload 为干净 JSON，目标类型由读侧显式给出（`StringRedisTemplate` + 手动映射，集合用 `new TypeReference<List<User>>() {}`）。契约 = 字段名与类型，与包结构解耦。
- 代价必然存在（§1 类型三来源）：去掉 `@class`，读侧显式给类型这一步省不掉——封装成一对 get/set helper 写一次即可，不是每个调用点手写序列化。

## 5. key 规范：命名空间与框架前缀

- **业务 key 统一前缀**：`<app>:<模块>:<业务id>`，如 `mall:order:1001`、`mall:stock:{1001}`（集群 hash tag）——前缀即命名空间，`scan` / 监控 / 清理都靠它。
- 共用实例时先盘点**所有写入方**的前缀体系，避免撞名互相覆盖：

| 写入方 | 前缀体系 |
|---|---|
| 本服务 | 自定 `<app>:` 命名空间（上行规范） |
| Sa-Token | 集成包前缀封装（可重写 `wrapKey` 定制，见 sa-token-dev `references/07-redis-frontsep.md`） |
| Spring Session | `spring:session:*` |
| Spring Cache | 默认 `cacheName::key`（本技能配置为 `cache:name:key`，`05-spring-cache.md` §3） |
| Redisson | 无自动前缀——锁 / 限流 key 与业务 key 同一空间，注意撞名 |

## 6. 强约束与自检

1. key / hashKey 序列化器 = `StringRedisSerializer`（SKILL.md 强约束 1）。
2. `GenericJackson2JsonRedisSerializer` 一律用**自定义 mapper**（JavaTime + defaultTyping + 忽略未知字段），不用默认构造。
3. **两套序列化互不通用**：手动 `RedisTemplate` 写入的数据，`@Cacheable`（另一套配置，见 `05-spring-cache.md` §3）读出的类型可能对不上——同一份业务数据只从一条路读写。
4. 序列化方案变更（如 JDK → JSON）后，**旧 key 读不回**：上线前按前缀清理（`scan` + `unlink`，见 `04-template-operations.md` §4）或等 TTL 自然过期，不要让两种方案读同一批 key。
