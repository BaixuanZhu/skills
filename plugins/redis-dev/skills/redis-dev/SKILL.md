---
name: redis-dev
description: >-
  Redis 开发助手（Java / Spring Boot）。在 Java / Spring Boot 项目中开发任何
  缓存（@Cacheable 声明式 / RedisTemplate 手动）、分布式锁（Redisson / SET NX EX）、
  Redis 连接与配置（单机 / 哨兵 / 集群 / 连接池）、序列化（key 乱码 / JSON / LocalDateTime）、
  缓存一致性（穿透 / 击穿 / 雪崩 / 先更库再删缓存）、以及用 Redis 数据结构实现业务功能
  （计数器 / 排行榜 / 签到 / 去重 / 延迟队列 / UV 统计）时使用本技能——
  无论用户是否提到 Redis（cache / caching / 分布式锁 / distributed lock / 看门狗 /
  watch dog / 缓存一致 / hot key / cache aside）。
  次级触发信号——代码或 pom 中出现：spring-boot-starter-data-redis、redisson、
  RedisTemplate / StringRedisTemplate、@Cacheable / @CacheEvict / @CachePut / @EnableCaching、
  RLock / RedissonClient / tryLock、opsForValue / opsForHash / opsForZSet 时必须使用本技能；
  用户报错出现：key 乱码（\xac\xed）、序列化 / 反序列化异常、连不上 Redis / command timeout /
  pool exhausted、OOM command not allowed、@Cacheable 不生效、读回 LinkedHashMap、
  用户随机掉线（与 Sa-Token 共库）时必须使用本技能。
  不适用于：Sa-Token 自身的 Redis 集成与 session 存储（→ sa-token-dev）、测试容器化 Redis
  （→ java-integration-test）、Redis 服务器安装部署 / 主从搭建 / 监控指标调优（运维范围）、非 Java 语言。
agent_created: true
version: 1.0.0
slug: redis-dev
displayName: Redis 开发助手
---

# Redis 开发助手

面向 Java / Spring Boot 的 Redis 编码助手：缓存、分布式锁、序列化配置、连接配置、缓存一致性。
版本基准：**Spring Data Redis 3.x（Spring Boot 3.x 自带，Lettuce 6.x）+ Redisson 3.x，Redis 服务器 6.x/7.x**。
Spring Boot 2.7（Spring Data Redis 2.x）差异在文中以 `Boot2.x` 标注（主要是 `spring.redis.*` vs `spring.data.redis.*`）。
采用**完全本地自包含**策略：所有知识沉淀于本地 `references/`，运行时不依赖任何外部文档站点。

## 版本与依赖

| 场景 | 依赖 | 说明 |
|---|---|---|
| 缓存 / 任意 Redis 读写 | `spring-boot-starter-data-redis` | 默认 Lettuce 客户端，自带 |
| 声明式缓存 @Cacheable | `spring-boot-starter-data-redis` + `spring-boot-starter-cache` | 还需 `@EnableCaching` |
| 分布式锁 / 布隆过滤器 / 延迟队列 | `redisson-spring-boot-starter`（或仅 `org.redisson:redisson` 手动配置） | 仅缓存场景**不要**引入 |
| 连接池（池参数生效） | `org.apache.commons:commons-pool2` | 配了 `pool.*` 才需要 |

- **配置命名空间**：Boot 3.x 用 `spring.data.redis.*`，Boot 2.x 用 `spring.redis.*`——配错导致连不上（症状见 `references/09-troubleshoot.md`）。
- **redisson-spring-boot-starter 会把 RedisConnectionFactory 替换为 Redisson 实现**（RedisTemplate 底层随之切换），引入即全局生效，详见 `references/07-redisson-lock.md` §1。
- **与 Sa-Token 共库**：Sa-Token 集成包（sa-token-redis-template）自带 key 前缀隔离；但**淘汰策略会波及 session**（用户随机掉线的头号嫌疑），见 `references/08-server-policy.md` §2。

## 第 0 步：依赖探测与激活分支

任务涉及缓存、分布式锁、Redis 配置、序列化、数据结构实现——**即使用户没提 Redis**——先检索项目依赖与代码（pom / build.gradle 搜 `data-redis`、`redisson`；代码搜 `RedisTemplate`、`@Cacheable`、`RLock`）：

| 探测结果 | 动作 |
|---|---|
| 已有 `data-redis` 或 `RedisTemplate` / `@Cacheable` | 直接激活，走「关键决策检查点」→「决策路由」 |
| 无任何 Redis 依赖，但任务要求缓存 / 锁 / 计数 / 排行 | **主动询问**是否引入 Redis（说明：进程内缓存 Caffeine 也可能是答案——单实例部署、无共享需求时）；同意 → 按「版本与依赖」表引入后继续 |
| 任务其实是 Sa-Token 的会话 / 登录存储问题 | 退出本技能 → sa-token-dev `references/07-redis-frontsep.md` |
| 任务是起 Redis 测试容器 / 测试隔离 | 退出本技能 → java-integration-test `references/04-testcontainers.md` |

## 何时使用本技能

| 信号 | 判定 |
|------|------|
| 写 / 改缓存逻辑（@Cacheable、手动 RedisTemplate 读写） | 激活 |
| 分布式锁、防重复提交、幂等、并发扣减互斥 | 激活 |
| Redis 连接 / 连接池 / 超时 / 哨兵 / 集群配置 | 激活 |
| 序列化：存对象、key 乱码、跨服务共享数据 | 激活 |
| 缓存穿透 / 击穿 / 雪崩、先更新库还是先删缓存 | 激活 |
| 用 Redis 做计数器 / 排行榜 / 签到 / 去重 / 延迟队列 / UV | 激活 |
| 报错：连不上、command timeout、pool exhausted、OOM command not allowed、序列化异常、`@Cacheable` 不生效、读回 `LinkedHashMap` | 激活，先查 `references/09-troubleshoot.md` |
| Redis 服务器安装 / 主从搭建 / 慢查询监控 / 大 key 巡检 | 不适用（运维范围，本技能只覆盖配置对应用行为的影响） |
| Sa-Token 登录 / 会话 / 踢人相关 | 不适用（→ sa-token-dev） |

> **检查点**：判定为「不适用」→ 告知用户当前问题不在本技能范围并建议退出。

## 关键决策检查点

以下 4 个场景存在多条技术路线，Agent **不可擅自替用户选择**。

**执行规则（机械判据，逐条执行）：**

1. 拿到任务后、写任何代码前，先扫描用户消息与上下文是否命中下表「触发信号」列的关键词（逐字匹配）。
2. 命中任一检查点 → **本轮回复只做一件事：输出确认问题**。禁止输出业务代码块、依赖坐标、配置片段。
3. 确认问题必须是**选择题**：列出候选方案 + 标注推荐项 + 一句话理由。禁止开放式提问。
4. 用户未明确回答 → 使用「默认推荐」列策略，并在输出开头标注「未确认，已使用默认方案」。
5. 用户确认方向 → 按选择生成代码，不再重复追问。
6. 一个需求命中多个检查点 → 一次性列出全部确认问题，全部完成后才生成代码。

| # | 触发信号（逐字关键词） | 必须确认的问题 | 方案差异（一句话） | 默认推荐 |
|---|---|---|---|---|
| C1 | "加缓存" / "缓存" / "cache"（未指明方式） | ① 声明式 `@Cacheable` 还是手动 `RedisTemplate`？② 缓存能接受多长的脏读窗口（TTL）？ | 声明式：简洁、注解即生效，适合整对象读缓存；手动：精细控制（部分更新 / 计数 / 锁配合），适合复杂逻辑。见 `references/05-spring-cache.md` §1 | 简单查询缓存用 `@Cacheable` + 显式 TTL 30min |
| C2 | "锁" / "分布式锁" / "防重复" / "幂等" / "并发" | ① 项目是否已有 Redisson？没有 → 是否同意引入？② 业务执行时长是否可预估？ | Redisson `RLock`：看门狗自动续期，业务时长不定时不传 `leaseTime`；`SET NX EX` 自实现：零依赖但需自己处理续期与安全释放。见 `references/07-redisson-lock.md` | 引入 Redisson，`tryLock(wait)` 不指定 `leaseTime`（看门狗续期） |
| C3 | "存对象" / "序列化" / "跨服务共享" / "key 可读" | 数据是否需要跨服务 / 跨语言读取？ | `GenericJackson2Json`：写入 `@class` 自动还原类型，单服务最省事；`StringRedisTemplate` + 手动 JSON：无类型标记、契约清晰，跨服务首选。见 `references/03-serialization.md` §1 | 单服务 `GenericJackson2Json`（含 JavaTimeModule），跨服务手动 JSON |
| C4 | "共用 Redis" / "同一个实例" / 与 Sa-Token / session 共库 | 业务缓存与登录 session / 持久数据是否必须同实例？ | 同实例：key 前缀隔离只能防覆盖，**防不了淘汰策略挤掉 session**（随机掉线）；分实例：彻底隔离，多一个运维对象。见 `references/08-server-policy.md` §2 | 提示风险；有条件 → 分实例，无条件 → 前缀隔离 + 容量留余量 |

## 决策路由

| 需求场景（关键词） | 读取文件 |
|---|---|
| 依赖引入、单机 / 哨兵 / 集群连接配置、超时、ACL、多数据源 | `references/01-connection.md` |
| 连接池参数、Lettuce 共享连接、pool exhausted、Jedis 切换 | `references/02-pool.md` |
| 序列化方案、key 乱码、GenericJackson2Json、LocalDateTime、LinkedHashMap、跨服务契约 | `references/03-serialization.md` |
| 数据结构选型（计数 / 排行 / 签到 / 去重 / UV / 队列）、scan / pipeline、incr 原子性 | `references/04-template-operations.md` |
| @Cacheable / @CacheEvict、TTL 配置（默认永不过期坑）、自调用失效、多缓存名不同 TTL | `references/05-spring-cache.md` |
| 缓存一致性：先更库还是先删缓存、穿透 / 击穿 / 雪崩三件套、延迟双删 | `references/06-cache-consistency.md` |
| 分布式锁：SET NX EX、Redisson tryLock、看门狗 / leaseTime 互斥、同步器、延迟队列 | `references/07-redisson-lock.md` |
| 淘汰策略（allkeys-lru 挤掉 session）、maxmemory、持久化取舍、lazyfree、TTL 删除时机 | `references/08-server-policy.md` |
| 排错：连不上 / 超时 / 乱码 / 序列化异常 / @Cacheable 不生效 / 随机掉线，症状 → 原因 → 修复 | `references/09-troubleshoot.md` |

## 核心强约束

1. **key 序列化器必须 `StringRedisSerializer`**：用默认 JDK 序列化，key 带二进制前缀（`\xac\xed...`），redis-cli 不可读、`keys`/`scan` 模式匹配失效。配置见 `references/03-serialization.md` §2。
2. **缓存必须显式 TTL**：`RedisCacheManager` 默认**永不过期**、手动 `set` 不传过期参数同理——内存只增不减 + 脏数据永驻。TTL 加 10%~30% 随机抖动防雪崩（`references/06-cache-consistency.md` §4）。
3. **`@Cacheable` 的序列化也要显式配**：`RedisCacheConfiguration.defaultCacheConfig()` 默认 value 也是 JDK 序列化——注解缓存与手动 RedisTemplate 是**两套独立序列化配置**，都要设。
4. **禁止 `keys *`**：全量遍历阻塞单线程 Redis，生产禁用；用 `scan` 游标迭代（`references/04-template-operations.md` §3）。
5. **加锁必须 `SET key value NX EX seconds` 原子命令**：`setnx` + `expire` 两步在进程崩溃时留下永不过期的死锁；value 必须放唯一标识，释放用 Lua 校验后删（`references/07-redisson-lock.md` §2）。
6. **显式传 `leaseTime` → 看门狗失效**：Redisson `tryLock(wait, leaseTime, unit)` 到期自动释放、不再续期；业务时长不可预估时**不传 `leaseTime`**，靠看门狗（默认 30s 租期、每 10s 续期）。
7. **unlock 必须 try-finally 且先判持有**：`if (lock.isHeldByCurrentThread()) lock.unlock()`，防租期已过被别人持有时抛 `IllegalMonitorStateException`。
8. **写一致性默认「先更新 DB，再删缓存」**：不更新缓存（并发写覆盖）、不先删缓存（并发读回填旧值）。要更低脏读率 → 延迟双删，见 `references/06-cache-consistency.md` §2。
9. **null 缓存必须短 TTL**：穿透防护里缓存空值 TTL 控制在 30s~5min，且 `unless="#result == null"` 会**关闭** null 缓存——别写反。
10. **配置命名空间随 Boot 版本**：Boot 3.x `spring.data.redis.*`、Boot 2.x `spring.redis.*`；哨兵/集群拓扑下 `database` 仅哨兵/单机有效，**cluster 模式不支持 SELECT、配置静默无效**（`references/01-connection.md` §3）。

## 使用流程

1. **确认适用性**：先执行「第 0 步：依赖探测」，再对照「何时使用本技能」；报错类任务直接从 `references/09-troubleshoot.md` 症状表入手。
2. **关键决策检查点**：逐字扫描 C1–C4 触发信号；命中 → 本轮只输出确认选择题，禁止生成代码。
3. **定位 reference**：查「决策路由」表，读对应文件。
4. **编码前过强约束**：10 条核心强约束逐条对照，尤其 TTL（第 2/9 条）与序列化（第 1/3 条）。
5. **遇异常先查排错**：`references/09-troubleshoot.md`。
6. **输出前自检（二值核对，任一为「否」即违规，必须返工）**：
   - C1–C4 已逐项扫描：命中的检查点均已确认，或已标注「未确认，已使用默认方案」？
   - 所有写入（set / cacheManager / increment 初始化）都带显式 TTL（含 null 缓存短 TTL）？
   - key 序列化器为 String？`@Cacheable` 与 RedisTemplate 两套序列化都配了？
   - 锁：try-finally + isHeldByCurrentThread 判断 + leaseTime 决策（预估不了就不传）？
   - 没有出现 `keys *`、`setnx`+`expire` 两步、先删缓存后更新 DB？
   - 配置前缀与 Boot 版本一致（spring.data.redis vs spring.redis）？
   - 与 Sa-Token / session 共库场景已提示淘汰策略风险（C4）？

## 版本注意

- **Spring Data Redis 3.x**（Boot 3.x）：配置前缀 `spring.data.redis.*`；2.x（Boot 2.7）为 `spring.redis.*`，其余 API 一致。
- **Redisson 3.x**：`lockWatchdogTimeout` 默认 30000ms；`redisson-spring-boot-starter` 版本需与 Boot 大版本匹配（过老版本只认 `spring.redis.*` 前缀，Boot 3 下连不上）。
- **LFU 淘汰策略需 Redis 4.0+**，Stream 需 5.0+，本文数据结构以 6.x/7.x 为基准。
