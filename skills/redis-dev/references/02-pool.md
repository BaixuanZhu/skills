# 连接池：Lettuce 共享连接与参数语义

## 1. 先判对：Lettuce 普通命令根本不走池

**最大认知坑**：Lettuce 的连接是 Netty 多路复用的、线程安全的，Spring 的 `LettuceConnectionFactory` 默认 `shareNativeConnection=true`——**所有普通命令（get/set/incr…）共用一条连接**，并发能力不取决于连接数。

因此 `lettuce.pool.*` 参数只在三种场景真正被用到：

| # | 场景 | 为什么需要独立连接 |
|---|---|---|
| 1 | 事务（`MULTI`/`EXEC`，`SessionCallback`/`multi()`） | 事务独占连接至提交 |
| 2 | 阻塞命令（`BLPOP`/`BRPOP`） | 命令阻塞期间连接不能服务他人 |
| 3 | 显式 `shareNativeConnection=false` | 人为关闭共享 |

> **结论**：没有这三种用法的普通 Web 服务，配连接池是无效功（配了也不生效，不是 bug）；反之，用到事务 / 阻塞命令而不配池，并发下会出现"排队等一条被占住的连接"。Jedis 则完全不同——见 §4。

## 2. 启用池

```xml
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-pool2</artifactId>
</dependency>
```

```yaml
spring:
  data:
    redis:
      lettuce:
        pool:                  # 需要 commons-pool2，缺失时启动报错
          max-active: 16       # 可借出连接上限（并发上限）
          max-idle: 8          # 池中最大空闲连接
          min-idle: 2          # 池中常驻最小空闲（预热 + 避免抖动）
          max-wait: 3s         # 借连接最长等待；超时抛异常。-1 = 无限等（危险）
```

**commons-pool2 缺失**：配了 `pool.*` 但没引依赖 → 启动或首次借连接时报 `NoClassDefFoundError: GenericObjectPool` 一族错误（不同 Boot 版本表现时机不同）。引入即解。

## 3. 参数语义（逐个）

| 参数 | 语义 | 调错了的症状 |
|---|---|---|
| `max-active` | 同时**借出**的连接上限；超过的请求进入等待 | 并发事务/阻塞命令多于 max-active 时吞吐封顶 |
| `max-wait` | 借连接的**排队等待上限**（不是命令超时！） | 设太短 → 高峰期 `Could not get a resource from the pool`；设 `-1` 无限等 → 线程堆积 |
| `max-idle` / `min-idle` | 空闲连接的保持区间，控制建连/销毁抖动 | min-idle=0 → 突发时集中建连，出现毛刺 |
| `time-between-eviction-runs` | 空闲检测周期（驱逐多余空闲连接） | 默认即可，一般不动 |

> **`max-wait` ≠ 命令超时**：`max-wait` 是从池里**借连接**的等待时间（`01-connection.md` §2 的 `timeout` 才是命令超时）。"pool exhausted" 类报错先看这里，不要去调 `timeout`。

## 4. Jedis（存量项目识别；新项目不选）

Boot 2.0（2018）起 starter 默认 Lettuce，Jedis 仍在维护但新项目基本不选。本节用于接手存量 Jedis 项目时对上行为差异——**§1"普通命令不走池"的结论只对 Lettuce 成立**，Jedis 每个操作从池借还连接、池必配。存量迁移到 Lettuce 的依赖写法：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
    <exclusions>
        <exclusion>
            <groupId>io.lettuce</groupId>
            <artifactId>lettuce-core</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>redis.clients</groupId>
    <artifactId>jedis</artifactId>
</dependency>
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-pool2</artifactId>
</dependency>
```

```yaml
spring:
  data:
    redis:
      client-type: jedis
      jedis:
        pool: { max-active: 32, max-idle: 16, min-idle: 4, max-wait: 3s }
```

| | Lettuce（默认） | Jedis |
|---|---|---|
| 连接模型 | 一条共享连接多路复用 | **每个操作从池借还一条连接** |
| 池是否必配 | 仅事务/阻塞命令需要 | **必配**，池参数直接决定并发 |
| 新项目默认 | ✓ | 一般不选 |

## 5. 排错速查

| 症状 | 定位 |
|---|---|
| 配了 `pool.*` 感觉没生效 | 正常——普通命令共享连接不走池（§1）；确认是否真用到事务/阻塞命令 |
| `Could not get a resource from the pool` / pool exhausted | ① `max-wait` 太短（借连接排队超时）② `max-active` 太小（并发事务/阻塞命令 > 上限）③ 连接泄漏：`SessionCallback` 内长时间阻塞、阻塞命令没超时控制 |
| 命令偶尔超时但池没问题 | 查命令超时配置与慢命令（`keys *`/大 value），见 `09-troubleshoot.md` |

## 6. 决策表

| 项目形态 | 池配置 |
|---|---|
| 普通缓存读写（无事务无阻塞命令） | 不配池；只设 `timeout` |
| 用 `SessionCallback`/事务 | `max-active` ≥ 并发事务数 + 余量 |
| 用 `BLPOP` 类阻塞命令 | 阻塞连接数计入 `max-active`，且阻塞命令必须带超时参数 |
| Jedis 客户端 | 必配池，参数按并发压测调 |
