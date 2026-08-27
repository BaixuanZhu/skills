# 连接配置：单机 / 哨兵 / 集群

## 1. 依赖与客户端

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

默认客户端 **Lettuce**（Netty 实现、连接线程安全可共享，普通场景无需连接池——池的适用边界见 `02-pool.md`）。
注意 `commons-pool2` 不是客户端、starter 也不自带——它只是池实现库，仅配 `lettuce.pool.*` 时才需要引入（`02-pool.md` §2）。

## 2. 单机配置（基准写法）

```yaml
spring:
  data:
    redis:          # Boot2.x 前缀是 spring.redis（去掉 data 层）
      host: 127.0.0.1
      port: 6379
      password: secret          # 无密码则整行删除，不要写空串 password: ""
      database: 0               # 0~15，需与共用实例的其他服务约定错开
      timeout: 3s               # 命令超时（读写等待），未配置时 Lettuce 默认 60s
      connect-timeout: 2s       # TCP 连接建立超时
      client-name: my-app       # 可选，CLIENT LIST 中可辨识来源
```

- **超时语义**：`timeout` 是**命令超时**（发出命令到收到响应的等待上限，含慢命令阻塞），不是连接超时；`connect-timeout` 才是建连超时。命令超时建议 1~5s——默认 60s 意味着 Redis 卡顿时请求线程挂一分钟。
- `password: ""`（空串）在部分版本被当作密码参与 AUTH，导致 `ERR Client sent AUTH, but no password is set`——无密码就删掉这行。
- **Redis 6+ ACL**：有独立账号时加 `username: appuser`（与 `password` 成对）。
- **url 简写**：`spring.data.redis.url: redis://appuser:secret@host:6379/1`——设置了 url 会覆盖 host/port/password/database 的散装配置，混用时注意优先级。
- **TLS**：`ssl.enabled: true`（Boot 3.1+ 与 4.x；Boot 3.0 是布尔型 `ssl: true`；Boot 2.x 为 `spring.redis.ssl: true`）。

## 3. 三种拓扑

| 拓扑 | 适用 | database | 事务 MULTI | 说明 |
|---|---|---|---|---|
| 单机 | 开发 / 小规模生产 | ✓ | ✓ | 一切基准 |
| 哨兵 Sentinel | 主从高可用（自动故障转移） | ✓ | ✓（主节点） | 客户端先连哨兵问出主节点地址 |
| 集群 Cluster | 数据量 / 写入超单机 | **✗ 不支持 SELECT** | **✗ 不支持** | 分片到 16384 slot，多 key 操作受 slot 限制 |

### 3.1 哨兵

```yaml
spring:
  data:
    redis:
      sentinel:
        master: mymaster           # 哨兵监控的 master 名，不是主机地址
        nodes: host1:26379,host2:26379,host3:26379   # 哨兵节点地址（26379 是哨兵端口）
        password: sentinel-pwd     # 哨兵节点自身的密码（可选，与下行区分）
      password: data-node-pwd      # 数据节点（master/replica）的密码
      database: 0
```

**易错**：`sentinel.nodes` 填的是**哨兵**地址（默认端口 26379），不是 Redis 数据节点地址；`sentinel.password` 是哨兵自己的密码，数据节点密码仍在顶层 `password`。填反的症状是连接阶段直接失败。

### 3.2 集群

```yaml
spring:
  data:
    redis:
      cluster:
        nodes: host1:6379,host2:6379,host3:6379,host4:6379,host5:6379,host6:6379
        max-redirects: 3          # MOVED/ASK 重定向跟随上限；不配置时 Boot 层无默认值、走 Lettuce 驱动默认 5
      # database: 1               # ❌ 集群没有 SELECT，此配置静默无效
      timeout: 3s
```

集群模式的三个应用侧限制（写代码前必须知道）：

1. **多 key 命令要求同 slot**：`mget(k1, k2)`、Lua 脚本内访问多个 key、事务——key 分布在不同 slot 会报 `CROSSSLOT` 错误。需要绑定的 key 用 **hash tag**：`order:{1001}:detail` 与 `order:{1001}:stock`（`{}` 内相同 → 同 slot）。
2. **事务不可用**（`MULTI/EXEC` 集群不支持），`RedisTemplate#multi` 相关调用会失败；需要原子性的场景改 Lua（配合 hash tag）。
3. **`keys`/`scan` 语义**：Spring Data Redis 的 cluster 连接会向所有 master 节点扇出，结果为聚合——但生产仍禁 `keys`（`04-template-operations.md` §6）。

## 4. Boot 版本与前缀对照

| Boot 3.x / 4.x | Boot 2.x | 说明 |
|---|---|---|
| `spring.data.redis.*` | `spring.redis.*` | 全部属性平移，仅前缀不同（3.x 与 4.x 前缀相同） |
| `spring.data.redis.ssl.enabled` | `spring.redis.ssl` | TLS 开关（Boot 3.0 为布尔 `ssl`，3.1 起对象型） |
| 其余属性名 | 同名 | host/port/timeout/cluster/sentinel 等不变 |

配错的典型症状：`Unable to connect to Redis` 但地址密码都对——先查前缀与 Boot 版本是否匹配（排错表见 `08-troubleshoot.md`）。

## 5. 多数据源（两个 Redis 实例）

**先判对：仅当确需连接第二个物理实例才走这里**（如另一环境 / 独立资源的 Redis）。单实例内隔离用 `database` / key 前缀（§2、`03-serialization.md` §5）。

自动配置只认一套连接属性；第二实例手动建工厂。密码与命令超时必须在工厂里自带——**不走 `spring.data.redis.*`**：

```java
@Configuration
public class RedisConfig {

    @Bean
    @Primary
    public LettuceConnectionFactory defaultFactory(
            @Value("${spring.data.redis.host}") String host,
            @Value("${spring.data.redis.port}") int port,
            @Value("${spring.data.redis.password}") String password) {
        return factoryOf(host, port, password);
    }

    @Bean
    public LettuceConnectionFactory cacheFactory(
            @Value("${app.cache-redis.host}") String host,
            @Value("${app.cache-redis.port}") int port,
            @Value("${app.cache-redis.password}") String password) {
        return factoryOf(host, port, password);
    }

    // 仅 host/port 的构造不携带密码——有密码实例上直接 NOAUTH
    private LettuceConnectionFactory factoryOf(String host, int port, String password) {
        RedisStandaloneConfiguration conf = new RedisStandaloneConfiguration(host, port);
        conf.setPassword(password);
        LettuceClientConfiguration client = LettuceClientConfiguration.builder()
                .commandTimeout(Duration.ofSeconds(3))   // 命令超时也要自带
                .build();
        return new LettuceConnectionFactory(conf, client);
    }

    @Bean
    @Primary
    public StringRedisTemplate stringRedisTemplate(@Primary LettuceConnectionFactory factory) {
        return new StringRedisTemplate(factory);
    }

    @Bean
    public StringRedisTemplate cacheRedisTemplate(LettuceConnectionFactory cacheFactory) {
        return new StringRedisTemplate(cacheFactory);
    }
}
```

- 必须标 `@Primary`（自动配置与 `@Cacheable` 都按主 bean 走）；第二实例的属性用自定义前缀（如 `app.cache-redis.*`），不要复用 `spring.data.redis.*`。
- `@Bean` 方式 Spring 自动调用 `afterPropertiesSet()`，无需手动。

## 6. 生产配置清单

- [ ] `timeout` 已显式配置（1~5s），不依赖默认 60s
- [ ] `password` 不落明文进 git（环境变量 / 配置中心占位符 `${REDIS_PASSWORD}`）
- [ ] 共用实例时 `database` 或 key 前缀与其他写入方约定（框架前缀速查 `03-serialization.md` §5）
- [ ] 集群模式：确认没有用到事务 / 跨 slot 多 key 操作
- [ ] 连接池是否真需要（见 `02-pool.md` §1——多数场景 Lettuce 不需要）
