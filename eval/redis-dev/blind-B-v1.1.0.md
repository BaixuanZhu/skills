# redis-dev 达尔文双盲评报告（blind-B，v1.1.0 轮）

评分方式：逐 prompt 按 D1–D8（各 12 分）模拟执行打分，维度分 = 12 条平均；D9 为全局维度（4 分制，依据技术事实核查）。满分 100。

## 一、维度评分汇总

| 维度 | 得分 | 简评 |
|---|---|---|
| D1 触发精度 | 11.8 | description 显式覆盖"未提 Redis 的宽泛场景"（SKILL.md:10-11）与报错信号（SKILL.md:17-18），12 条全部正确激活/正确不激活；仅 T6/T8 类自然语汇需一步语义映射 |
| D2 可发现性 | 11.0 | 08 排错表对 5/7 个报错类 prompt 直达；但缺 `key 乱码`、`InvalidDefinitionException` 两个高频症状行（T2/T10 需回退 SKILL.md:99 路由行兜底）；决策路由表无"延迟任务"显式词（T8） |
| D3 覆盖完整 | 11.9 | 12 条涉及知识点无实质盲点；T8 三坑、T6 三件套、T11 池认知框架全部有答案 |
| D4 可执行性 | 11.8 | 代码/配置全部可直接照抄且与 prompt 参数逐一对应（如 T7 哨兵 yaml 与 mymaster/3 节点直接吻合） |
| D5 防错/陷阱 | 11.7 | 隐蔽坑点名密度极高（看门狗无限续期、unless 反写、默认永不过期、scan 重复、multiGet 错位）；rubric 全部 D5 锚点零命中扣分项 |
| D6 信息密度 | 11.1 | 整体密度高；SKILL 强约束与 references 存在刻意压缩复述（带指针，当前无口径漂移）；少量跨文件重复为可控成本 |
| D7 内部导航 | 11.3 | 路由表 + 交叉引用 + 每文件自检清单，跳转基本 ≤2 步 |
| D8 范围明确 | 11.0 | 排除项三处声明一致（SKILL.md:19-20 / 69-70 / 54-55）；Testcontainers 让位只说"属集成测试领域"未指名目标技能，属轻微不足 |
| D9 整体一致性 | 3.5/4 | 5 组高风险断言经 web 核实全部为真，未发现虚构；2 处存疑、2 处轻微不准确、1 处自家规则自相矛盾（详见核查清单） |
| **总分** | **95 / 100** | |

## 二、逐 prompt 评分与详评

### T1 加缓存（宽泛场景未提 Redis）

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 12 | 11 | 12 | 11 | 12 | 11 | 11 | 11 |

- D1：description 明确"无论用户是否提到 Redis（cache / caching / 缓存一致）"接住"加个缓存"（SKILL.md:10-11）；第 0 步对"无任何 Redis 依赖但任务要求缓存"有专门分支且主动提示 Caffeine 替代（SKILL.md:53）。
- rubric 锚点核验：**不问 C1 直接甩代码**——不会发生。C1 触发信号逐字命中"加缓存"/"缓存"（SKILL.md:89），执行规则 2 强制本轮只输出确认问题（SKILL.md:81）。
- **默认永不过期坑未提示**——D5 不扣：强约束 2（SKILL.md:110）+ 05-spring-cache.md:29-36（"不配置 RedisCacheManager 时 TTL 永不过期"）双保险；用户选 @Cacheable 路线后有完整 CacheConfig（05-spring-cache.md:31-58，含 entryTtl/computePrefixWith/perName）。
- D8：技能不含查询接口业务写法，无越界。
- 扣分点：D4 给 11——用户若选手动 RedisTemplate 路线，03 §3 配置齐但"订单对象读写"仍需 agent 自行组装（可接受）；D6 的 11 反映 C1 确认问题 ② 本身是开放式提问（见 Top 问题 3）。

### T2 key 乱码反向题

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 12 | 10 | 12 | 12 | 12 | 11 | 11 | 11 |

- D1 12：description 报错信号明确列"key 乱码（\xac\xed）"（SKILL.md:17）。
- D2 10（主要扣分）：SKILL.md:122 称"报错类任务直接从 08 症状表入手"，但 08-troubleshoot.md:7-22 路由表**没有** `key 乱码` 行；agent 需回退到 SKILL.md:99 决策路由行（"序列化方案、key 乱码 → 03"）或强约束 1（SKILL.md:109）才到 03 §2。功能可达但入口承诺有落差。
- D4 12：03-serialization.md:17 的乱码字节串 `\xac\xed\x00\x05t\x00\x09user:1001` 与 prompt 症状逐字节吻合（经字节级验证：AC ED magic + 版本 0005 + TC_STRING + UTF 长度 0009 + 9 字符，完全正确）；修复配置 03 §3 完整可照抄。
- rubric 锚点核验：**只改序列化器不提旧数据清理**——不发生。03-serialization.md:86 明确"序列化方案变更后旧 key 读不回：上线前按前缀清理（scan + unlink）或等 TTL"。

### T3 Redisson 锁 + 40 秒下游调用

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 12 | 11 | 12 | 12 | 12 | 11 | 11 | 11 |

- rubric 锚点核验：**裸靠看门狗 / leaseTime < 业务上界**——不会发生。07-redisson.md:97 明确"leaseTime ≤ 业务执行上界 → 业务没跑完锁先到期 → 并发进入 + unlock 抛 IllegalMonitorStateException"；07-redisson.md:98 给出"业务上界 × 安全余量，估不出给大值（60s / 5min），宁可长不可短"——40 秒业务直接推导出 leaseTime ≥ 60s 级，可执行。
- D5 12：try-finally + isHeldByCurrentThread（07:72-74）、拿不到锁抛 BizException 而非空转（07:76-79）、强约束 6 的看门狗无限续期等效死锁描述（SKILL.md:114）全齐。
- D2 11：C2 命中（"防重复提交"，SKILL.md:90）→ 07 §3/§4 直达。轻微保留：用户消息已含 C2 两个确认点的答案（指定 Redisson、给出 40s），执行规则未明说"已答则跳过"（SKILL.md:85 规则 5 仅蕴含），agent 需自行判断不再追问——按常识可解，不重扣。

### T4 不想引 Redisson，手写 setnx

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 12 | 11 | 12 | 12 | 12 | 11 | 11 | 11 |

- rubric 锚点核验：**把 SET NX EX + Lua 三件套当答案**——不会发生。07-redisson.md:61 明确"修复方向一律是迁移本节的成熟实现，不是继续打补丁……`SET NX EX` 的原子性留作 review 存量代码的识别知识即可，不是自实现的邀请"；强约束 5 同口径（SKILL.md:113）。
- "顾虑已不成立"的论据完整：裸 `org.redisson:redisson` 与 Lettuce 共存、不动数据面（07:7、07:11），引依赖 XML + 从 RedisProperties 建 client 代码可直接照抄（07:14-33）。
- D5 12：setnx+expire 两步崩溃窗口（SKILL.md:113）+ 自实现四缺口清单（持有者校验/续期/可重入/主从切换，07:61）作为"为什么迁移"论据出现，与 rubric 期望完全一致。

### T5 @Cacheable 不生效（自调用）

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 12 | 12 | 12 | 12 | 11 | 12 | 12 | 11 |

- D2 12：08-troubleshoot.md:17 一行直达 `@Cacheable 不生效 → 05-spring-cache.md §4`，零绕路。
- D4 12：05-spring-cache.md:66-76 的示例（getOrder + 同类 view 调用）与 prompt 场景**逐字对应**；根因（this 绕过代理）+ 三解法表（拆 bean / 注入自身 / AopContext，05:80-84）+ 同类失效 private/final（05:86）全可执行。
- rubric 锚点核验：**错误根因（"没配 CacheManager"当第一嫌疑）**——不发生，05 §4 标题即"自调用失效（最高频的'不生效'）"，其余原因排在 05:88 清单后位。

### T6 缓存一致性整体设计

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 11 | 11 | 12 | 11 | 12 | 11 | 12 | 11 |

- D3 12：rubric 四要素全齐——读路径回源 + TTL 抖动（06:8、06:34-44）、写路径先更 DB 再删（06:18）、击穿互斥回源 DoubleCheck（06 §5）与逻辑过期异步重建（06 §6）、穿透 null 缓存 + 布隆（06:27）。成体系。
- rubric 锚点核验：**推荐"更新缓存"或"先删缓存"**——不发生，06:15-17 两行均标 ✗ 并给出并发时序反例；延迟双删局限（延迟只能估、sleep 占线程、是缓解非消除，06:21）讲清。
- D4 11：§5 是伪代码 + §4 抖动是真代码，组合后可落地；`"<null>"` 哨兵与 JSON 撞型区分（06:65）有判据。@Cacheable 路线的抖动限制有诚实声明（06:44）。
- D1 11：设计题需经 C1 确认（声明式 vs 手动）——对"整体设计"类 prompt，C1 的两个选项均偏窄（设计题答案常是手动路线 + 06 全景），但 C1 默认推荐不阻碍路由到 06。

### T7 Boot 3.2 连不上 + 哨兵配置

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 12 | 12 | 12 | 12 | 11 | 11 | 12 | 11 |

- D2 12：08-troubleshoot.md:9 首行直达 `Unable to connect，但地址密码都对 → 01-connection.md §4`——精确匹配"地址密码都检查过没问题"的表述。
- D4 12：01-connection.md:46-56 哨兵 yaml 与 prompt 参数逐一对应（`master: mymaster` 01:51、3 个 `host:26379` nodes 01:52）。
- rubric 锚点核验：**哨兵 nodes 写成数据节点地址**——不会发生，01:58"易错"段明确"`sentinel.nodes` 填的是哨兵地址（默认端口 26379），不是数据节点地址"，且区分 sentinel.password 与顶层 password。
- D3 12：Boot 3 前缀（01 §4 对照表）、命令超时默认 60s（01:25，经 web 核实为真）齐备。

### T8 延迟任务选型（订单 30 分钟关单）

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 11 | 10 | 12 | 12 | 12 | 11 | 11 | 11 |

- D2 10（主要扣分）：SKILL.md:103 决策路由的 07 行关键词是"Redisson：分布式锁…延迟队列 RDelayedQueue"，SKILL.md:105 的 09 行是"发布订阅、Stream、键空间通知"——从"订单 30 分钟未支付自动关闭"的自然语汇到 07 §7 / 09 §1 选型表需要一步语义推断（description SKILL.md:8 有"延迟队列"可助激活）。建议路由表补"延迟任务 / 超时关单 / 定时关闭"关键词。
- rubric D5 三坑核验全部命中：①到期搬运由客户端实例驱动、重启须重建、**消费方应用也要常驻创建**（07:131）②无 ack 取走即丢、高可靠走 MQ/定时兜底（07:133）③别用键空间通知做订单超时（09-messaging.md:101"订单超时关闭别押它"，09:99 过期事件不准时的根因联动 08:27）。
- D4 12：双队列写法完整可执行（getBlockingQueue + getDelayedQueue + offer(30, MINUTES) + take，07:123-128）。

### T9 incr 限流

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 12 | 11 | 12 | 12 | 11 | 11 | 11 | 11 |

- D4 12：04-template-operations.md:81-88 的 RATE_LIMIT_LUA + `rate:login:` + ip + ARGV "60" 几乎为本题定制，可直接产出"计数 > 5 → 429"。
- rubric 锚点核验：**裸 incr+expire 不提竞态**——不发生，04:80 注释点名"首请求自增后崩溃 → key 永不过期、该维度永久被限"，Lua 原子化为标准答案；04:120 自检再次兜底。
- D2 11：路由表"限流 RRateLimiter → 07"先到 07 §6，再经分工判据"每 IP 每分钟 5 次 INCR+TTL / Lua 就够（04 §4）"跳回 04（07:118）——两跳但判据明确、方向无歧义。
- D5 11：固定窗口的边界突刺（窗口切换瞬间 2 倍流量）未提。rubric 未列为锚点，不按锚点扣，作为改进建议。

### T10 LocalDateTime 报错

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 12 | 10 | 12 | 12 | 12 | 11 | 11 | 11 |

- D2 10：08-troubleshoot.md:7-22 路由表**没有** `InvalidDefinitionException` / `LocalDateTime` 行（有 LinkedHashMap、NullValue 行）；回退 SKILL.md:99 路由行（"序列化方案…LocalDateTime → 03"）后，03-serialization.md:55 表行的报错文案与 prompt **逐字匹配**（"InvalidDefinitionException: Java 8 date/time type not supported by default"），命中后无歧义。
- rubric 锚点核验：**只给 registerModule 不提 default typing 连锁坑**——不发生，03 §3 四必须项表中 activateDefaultTyping 缺失 → LinkedHashMap（03:56）与 FAIL_ON_UNKNOWN_PROPERTIES 缺失 → UnrecognizedPropertyException（03:57）连锁坑全列，且 §3 代码一次配齐四项。

### T11 pool exhausted

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 12 | 12 | 12 | 12 | 12 | 11 | 12 | 11 |

- D2 12：08-troubleshoot.md:12 直达 02-pool.md §5，且提示"先确认 client-type：Jedis 与 Lettuce 的处置完全不同"。
- rubric 锚点核验：**只建议调大 max-active**——不会发生。02 §1"先判对：Lettuce 普通命令根本不走池"（02:3-5）直接解释"配了 16 还是报"的认知前提；02:86 定位表给三分支（max-wait 太短 / max-active 太小 / 连接泄漏）。
- D5 12：借连接等待 vs 命令超时的区分在 02:45 明确（"max-wait…不是命令超时！……报池错别去调它"），Jedis 分支 antipattern（默认 8/-1 无限等，02:75）覆盖另一种客户端可能。

### T12 边界让位三合一

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|
| 12 | 11 | 11 | 11 | 11 | 11 | 11 | 11 |

- rubric 锚点核验：**越界自己写**——不会发生。三件分别命中：①Testcontainers → SKILL.md:55"起 Redis 测试容器 / 测试隔离 → 退出本技能（属集成测试领域）"+ SKILL.md:19；②大 key 巡检 → SKILL.md:69"大 key 巡检 → 不适用（运维范围）"；③搭主从集群 → SKILL.md:69"主从搭建 → 不适用"+ description SKILL.md:20。三处声明（description / 何时使用表 / 第 0 步表）口径一致，SKILL.md:72 还有"判定为不适用 → 告知用户并建议退出"的动作指令。
- D8 给 11 而非 12：①的让位只说"属集成测试领域"，未指名 java-integration-test 技能（rubric 期望的让位目标）——考虑本技能自包含分发约束（不硬编码兄弟技能名也合理），轻微不足；②③为明确运维拒绝，符合期望。

## 三、技术事实核查

### A. 经独立验证为真（web 核实 / 字节级验证）

| # | 断言 | 位置 | 结论 |
|---|---|---|---|
| 1 | Lettuce 命令超时默认 60s | 01-connection.md:25,30 | 真。`RedisURI.DEFAULT_TIMEOUT = 60s`（Lettuce 官方文档） |
| 2 | redisson-spring-boot-starter 存在 4.x 线，2025-12 起；3.x starter 在 Boot 4 下启动报错 | 07-redisson.md:36 | 真。starter 4.0.0 发布于 2025-12-16；GitHub issue #6863 确认 3.x starter 升 Boot 4 报错 |
| 3 | `@Cacheable sync=true` 与 `unless` 互斥，组合抛 `IllegalStateException` | 05-spring-cache.md:92 | 真。Spring javadoc 明示 unless 不支持与 sync 组合，SPR-16410 确认 |
| 4 | RedLock 争议大且 Redisson 已不推荐 | 07-redisson.md:157 | 真。Redisson 官方 wiki 标注 "This object is deprecated"，`RedissonRedLock` 在 3.27.1/4.x javadoc deprecated-list 中 |
| 5 | lock4j `acquireTimeout` 默认 3000ms、`expire` 默认 30000ms（固定租期）；其对 redisson 依赖为 provided | 07-redisson.md:55,90 | 真。lock4j 官方仓库默认值与依赖 scope 均吻合 |
| 6 | JDK 序列化 String key 前缀 `\xac\xed\x00\x05t\x00\x09user:1001` | 03-serialization.md:17 | 真。逐字节验证：AC ED（magic）+ 00 05（版本）+ 74（TC_STRING）+ 00 09（UTF 长度 9）+ 9 字符，全对 |

### B. 高置信为真（与 Spring Data Redis / Redisson / Redis 官方机制交叉验证）

- Boot 3/4 `spring.data.redis.*` vs Boot 2 `spring.redis.*`（SKILL.md:43、01 §4）
- RedisCacheManager 默认永不过期；默认 cacheName 前缀 `name::key`（SKILL.md:110、05:29、03:78）
- `GenericJackson2JsonRedisSerializer` 写 `@class`；默认构造自动注册 NullValueSerializer、自定义 mapper 不会；`registerNullValueSerializer(mapper, null)` 静态方法存在；默认 mapper 不带 JSR310（03 §3，含 03:58）
- `unless="#result == null"` 恰好关闭 null 缓存（SKILL.md:117、05:93）
- Redisson 看门狗默认 30s 租期、每 10s（= watchdog/3）续期；`lockWatchdogTimeout` 默认 30000（SKILL.md:114、07:87,96）
- `tryLock(wait, lease)` 显式 leaseTime 则无看门狗；lease 到期无论业务是否跑完即释放；非持有线程 unlock 抛 `IllegalMonitorStateException`（07 §4 表、SKILL.md:115）
- cluster 不支持 SELECT（配置静默无效）、16384 slot、hash tag `{}` 收拢 slot、跨 slot 报 `CROSSSLOT`、集群不支持 MULTI/EXEC（01:42,69,77-78）
- `max-redirects` Boot 层无默认值、Lettuce 驱动默认 5（01:68）
- 哨兵默认端口 26379；`sentinel.password`（哨兵自身）与顶层 `password`（数据节点）分离（01:52-58）
- Lettuce `shareNativeConnection=true` 默认、普通命令不走池、池仅在事务/阻塞命令/显式关闭共享时使用（02:5-13）
- commons-pool2 默认 maxTotal=8、maxWait=-1；Boot 2.0 起默认 Lettuce（02:51,75）
- scan：count 为提示值、可能返回重复需去重；`unlink` 异步释放（04:17-18,20）
- multiGet 按位对齐、缺失位为 null（04:52）
- Redis 事务无回滚；watch 冲突 exec 丢弃（04:67,72）
- DefaultRedisScript 首次 EVALSHA、未缓存降级 EVAL；KEYS/ARGV 规则与集群同 slot 约束（04:91-92）
- Hash 字段级 TTL 需 Redis 7.4+（HEXPIRE）（04:102）；HyperLogLog ~12KB / 0.81% 标准误差；1 亿 bit ≈ 12.5MB（04 §6，算术正确）
- `SimpleKey.EMPTY` 无参方法共享缓存项；`AopContext.currentProxy()` 需 `exposeProxy = true`（05:24,84）
- `computePrefixWith` / `transactionAware()` / `withInitialCacheConfigurations` API 真实（05 §3）
- RRateLimiter `trySetRate` 幂等 / `OVERALL` vs `PER_CLIENT` 语义（07:109,115-116）；`RateIntervalUnit` 枚举存在
- RDelayedQueue 到期搬运由客户端实例驱动（07:131）；RBloomFilter `tryInit` 仅首次生效、判无一定无（07:142,150）；RMapCache 条目级 TTL（07:143）；RLock 可重入基于 hash 线程标识与计数（07:102）；RCountDownLatch 不可重用（07:141）
- Stream 需 Redis 5.0+；向不存在 stream 建组报错、`MKSTREAM` 可顺带建；PEL / `XAUTOCLAIM` min-idle-time；`XADD MAXLEN ~` 近似修剪（09 §3）
- 键空间通知默认关闭、`notify-keyspace-events Ex` = keyevent + expired；消息体即 key 名（09:82,90）；惰性/定期删除导致过期事件不准时与 scan 中残留（08:27）
- 订阅走专用连接（09:37）；集群 PUBLISH 广播所有节点、Redis 7+ SSUBSCRIBE 不跨节点（09:38）
- `RedisProperties` FQN（org.springframework.boot.autoconfigure.data.redis）、双工厂代码 API、`@Bean(destroyMethod="shutdown")`（01 §5、07:25）

### C. 存疑（无法完全核实，不判错）

1. **03-serialization.md:77 "Sa-Token 集成包前缀封装（可重写 wrapKey 定制）"**——Sa-Token 新版有 key 包装机制，但具体方法名 `wrapKey` 未能核实。邻接生态的提示性内容，非本技能核心断言。
2. **03-serialization.md:58 "2.7 / 3.x / 4.x 源码一致"**——默认构造注册 NullValueSerializer 的行为方向正确，跨版本逐一比对无法完成。
3. **SKILL.md:30 "Lettuce 6.x/7.x、Spring Data Redis 3.x/4.x"**——SDR 4.x 随 Boot 4（2025-11 GA）成立；Lettuce 7.x 到 2026-08 是否已发布未核实，写法为前瞻覆盖，不判虚构。

### D. 轻微不准确 / 瑕疵（不构成虚构，未按虚构扣 D9，仅累计致 D9 = 3.5）

1. **03-serialization.md:15 "自动配置的 `RedisTemplate<String, Object>`（redisTemplate bean）"**——自动配置的 bean 实为 `RedisTemplate<Object, Object>`（RedisAutoConfiguration 签名）。核心断言（key/value 均 JDK 序列化）正确，泛型标注不准。
2. **09-messaging.md:60 行内注释** `container.receive(  // receiveAutoAck = 收到即 ack`——注释锚定在 `receive()` 调用上却解释 `receiveAutoAck` 的语义，代码本身正确（receive + 回调手动 acknowledge），但注释位置易让读者误读"receive 即自动 ack"。
3. **C1 确认问题 ②（SKILL.md:89）"缓存能接受多长的脏读窗口（TTL）？"与 C2 ②（SKILL.md:90）"业务执行时长上界是多少？"是开放式提问**，与执行规则 3（SKILL.md:82）"确认问题必须是选择题……禁止开放式提问"自相矛盾。
4. **07-redisson.md:18 示例版本 3.27.2**（2024-04）到 2026-08 已偏旧（3.5x / 4.x 线），agent 照抄会引入老版本；正文 07:36 有版本线意识，示例未注明"按版本线取最新"。

## 四、Top 问题清单与改进建议（按影响排序）

1. **08 排错路由表缺两个高频症状行（key 乱码 `\xac\xed`、`InvalidDefinitionException`/LocalDateTime）**。SKILL.md:122 承诺"报错类任务直接从 08 症状表入手"，T2/T10 的症状在 08-troubleshoot.md:7-22 无行，依赖 SKILL.md:99 决策路由行兜底。影响：报错直达承诺落空，多一步回退。建议：08 表补两行 `key 乱码 \xac\xed 前缀、模式匹配失效 → 03 §2`、`InvalidDefinitionException: Java 8 date/time → 03 §3`。
2. **决策路由表缺"延迟任务"显式关键词**。T8"订单 30 分钟自动关闭"需 agent 自行语义映射到 RDelayedQueue（SKILL.md:103）或 09 §1 选型表。建议：SKILL.md:103 或 105 行关键词补"延迟任务 / 超时关单 / 定时关闭"。
3. **C1②/C2② 开放式提问与自家规则 3 冲突**（SKILL.md:89-90 vs SKILL.md:82）。建议改为带推荐值的选项（如"TTL：30min（推荐）/ 1h / 自定义"）。
4. **T9 固定窗口限流的边界突刺未提**（04 §4）。建议在 04 §4 补一句"固定窗口在窗口切换瞬间可能放行 2 倍流量，临界场景用滑动窗口（ZSET）或令牌桶"。
5. **09-messaging.md:60 注释位置歧义**（receive 行内写 receiveAutoAck 语义）。建议把该注释移到坑 2 段落或改为 `// 手动 ack；另有 receiveAutoAck 变体=收到即 ack`。
6. **03-serialization.md:15 泛型标注不准**（`RedisTemplate<String, Object>` → 实为 `<Object, Object>`）。
7. **07-redisson.md:18 示例版本 3.27.2 偏旧**，建议注明"示例坐标，版本按 07:36 的版本线取最新"。
8. **SKILL.md frontmatter `version: 1.0.0` 与审查轮后已翻转的锁类口径不匹配**（test-prompts note 明示"期望答案随技能口径翻转"）——版本未 bump 属仓库流程问题，不影响内容正确性，但按仓库发布规则（SkillHub 静默拒收同版本号）会阻碍已验证改进触达用户。

## 五、结论

技能在 12 条 prompt 上无一条会产出错误结果或卡死：rubric 设定的全部重扣锚点（不问 C1 甩代码、不清理旧 key、裸看门狗、教手写锁、错误根因、更新缓存/先删缓存、哨兵 nodes 填数据节点、键空间通知做订单超时、裸 incr+expire、只调 max-active、越界 T12 三件）**零命中**。D9 层面经 5 组 web 核实 + 全量断言过检，未发现任何虚构事实，仅存 2 处存疑、4 处轻微瑕疵。主要失分集中在可发现性的三个入口缺口（08 两行、路由一行）与 D9 的自相矛盾小点。总分 **95/100**。

事实核查来源：[Redisson starter 4.x / Boot 4 issue #6863](https://github.com/redisson/redisson/issues/6863)、[MVNRepository redisson-spring-boot-starter](https://mvnrepository.com/artifact/org.redisson/redisson-spring-boot-starter/4.0.0)、[Spring @Cacheable javadoc](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/cache/annotation/Cacheable.html)、[SPR-16410 sync does not support unless](https://github.com/spring-projects/spring-framework/issues/20956)、[Redisson Locks and Synchronizers（RedLock deprecated）](https://redisson.pro/docs/data-and-services/locks-and-synchronizers/)、[RedissonRedLock javadoc (4.1.0)](https://www.javadoc.io/static/org.redisson/redisson/4.1.0/org/redisson/RedissonRedLock.html)、[lock4j GitHub](https://github.com/baomidou/lock4j)、[Lettuce Production usage（默认 60s）](https://redis.io/docs/latest/develop/clients/lettuce/produsage/)、[RedisURI javadoc](https://www.javadoc.io/doc/io.lettuce/lettuce-core/6.3.2.RELEASE/io/lettuce/core/RedisURI.html)。
