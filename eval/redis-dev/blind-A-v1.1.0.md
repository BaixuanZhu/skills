# redis-dev v1.1.0 达尔文双盲评报告（blind-A）

**评分手册**：`eval/redis-dev/rubric.md` · **测试集**：`eval/redis-dev/test-prompts-v1.1.0.json`（12 条）· **被评物**：`skills/redis-dev/`（SKILL.md + references/01~09）

## 1. 维度评分汇总

| 维度 | 满分 | 得分 | 评语 |
|---|---|---|---|
| D1 触发精度 | 12 | **12** | 宽泛场景（"加个缓存"）、次级信号（pom token / 报错文案）、不适用清单三层齐备，T1/T12 两端都接得住 |
| D2 可发现性 | 12 | **11** | 决策路由 9 行全覆盖；唯一缺口：08 排错表漏了 `key 乱码`、`LocalDateTime 报错` 两个高频症状行（恰是 T2/T10 症状），需经 SKILL 路由表兜底两跳 |
| D3 覆盖完整 | 12 | **12** | 12 条 prompt 逐一走查无知识盲点，rubric 各判分要点均有落点 |
| D4 可执行性 | 12 | **12** | 哨兵 YAML、CacheManager、Lua 脚本、锁模板、双队列均可直接照抄；C1–C3 逐字关键词 + 选择题 + 默认推荐是可机械执行的 |
| D5 防错/陷阱 | 12 | **12** | 乱码、看门狗/leaseTime、自调用、默认永不过期、set 覆盖洗 TTL、sync/unless 互斥、PER_CLIENT 放大、RDelayedQueue 重启重建……密度极高且全是"不 fail loud"型 |
| D6 信息密度 | 12 | **11.5** | 无原理前言/励志块/学术典故；SKILL 强约束 5/6 与 07 §2/§4 存在论证性复述（约 100 字同列表写两遍）；09:60 `receiveAutoAck` 注释挂在 `receive` 调用行上方，位置有误导 |
| D7 内部导航 | 12 | **12** | 无孤儿 reference；节号指针带语义；07 §7 ↔ 09 §1 双向互指；自检清单尾部有出口指针 |
| D8 范围明确 | 12 | **12** | T12 三件全部让位且四处（description/探测分支/何时使用/检查点）声明；01 §3.1 只教连接不教搭建，零越界 |
| D9 整体一致性 | 4 | **3.5** | 抽查 40+ 条可验证断言**未发现虚构**，4 项存疑断言经 web 核实全部为真；扣分见下方一致性小节 |
| **总分** | **100** | **98** | |

## 2. 逐 prompt 评分与详评

### T1 订单查询加缓存（宽泛，未提 Redis）— 通过

流程走位：description"无论用户是否提到 Redis（cache / caching）"命中（SKILL.md:4-11）→ 第 0 步依赖探测（SKILL.md:46-55，无依赖时主动询问含 Caffeine 替代）→ **C1 命中"加缓存"，SKILL.md:81 明令"本轮只输出确认问题，禁止输出代码"**——rubric 锚点"不问 C1 直接甩代码→D1 扣"被机械规则堵死。确认后 C1 默认推荐 `@Cacheable` + TTL 30min（SKILL.md:89）→ 05 §3 完整 CacheManager（`entryTtl` + `StringRedisSerializer` + `RedisSerializer.json()`，05-spring-cache.md:36-57）——rubric 锚点"不配 TTL → D5 重扣"由 SKILL.md:110 强约束 2 + 05:29"不配 RedisCacheManager 时 TTL 永不过期"双重覆盖。`@EnableCaching`/`spring-boot-starter-cache` 依赖在 SKILL.md:39。订单查询接口本身的三层写法不越界。**D1/D3/D8 全额**。

### T2 key 乱码反向题 — 通过（D2 小扣已计入全局）

症状 `\xac\xed\x00\x05` 在 description 报错信号（SKILL.md:17）和强约束 1（SKILL.md:109）双层出现；决策路由行"序列化方案、key 乱码"（SKILL.md:99）直达 03 §2，其中 03-serialization.md:17 逐字节解释 `\xac\xed\x00\x05t\x00\x09user:1001`（JDK 序列化魔数+String 类型标记+长度 9，技术上准确）并直接点明"`keys user:*` 匹配不到"正是本题第二症状。修复完整：03 §3 配置代码 + **rubric 锚点要求的旧 key 清理**在 03-serialization.md:86（scan+unlink 或等 TTL）。唯一缺口：08 症状表没有乱码行（08-troubleshoot.md:8-21 全表无 `\xac\xed`），而 SKILL.md:122 规定"报错类任务直接从 08 入手"——第一落点落空，靠常读层兜回。

### T3 Redisson 锁 + 40 秒下游 — 通过（D4/D5 全额，本题是技能口径的主场）

C2 命中"防重复"（SKILL.md:90），确认问题①②与 prompt 信息互补。核心锚点"leaseTime 小于业务上界→重扣"被三重覆盖：SKILL.md:114 强约束 6（"leaseTime 取业务执行上界 × 安全余量"）、07-redisson.md:97 antipattern 行（"leaseTime ≤ 业务执行上界 → ✗ 业务没跑完锁先到期 + unlock 抛 IllegalMonitorStateException"）、07:98 ✓ 行（"60s / 5min，宁可长不可短"）——40s 业务照规则必然推出 60s+。`try-finally` + `isHeldByCurrentThread` 在 07:72-74；拿不到锁的真实处理（非空转）在 07:76-78（throw BizException）；防重复提交场景"可容忍极小并发 → 单实例锁 + DB 兜底"在 07:157。裸 `org.redisson:redisson` 与 Lettuce 共存的引入路径（07 §1 表 + 24-33 行从 `RedisProperties` 建 Config）可直接照抄。

### T4 不想引 Redisson、手写 setnx — 通过（口径与 rubric 期望完全一致）

rubric 锚点"接受手写并把 SET NX EX+Lua 当答案 → 重扣"——技能口径正面翻转：SKILL.md:113 强约束 5"禁止自写 SET NX + Lua"，07-redisson.md:61"修复方向一律是迁移，不是继续打补丁……`SET NX EX` 的原子性留作 review 存量代码的识别知识，不是自实现的邀请"。用户顾虑（"不想为一个锁引 Redisson"）被 07:11 正面拆解：裸依赖"无——Lettuce / RedisTemplate / @Cacheable 原样"，不动既有连接层。"为什么迁移"论据（持有者校验/续期/可重入/主从切换四缺口）在 07:61。**D4/D5 全额**。

### T5 @Cacheable 自调用 — 通过（D2/D4 满分示范）

08 症状表直达行："`@Cacheable` 不生效（每次都查库）→ 05 §4（自调用 + 失效清单）"（08-troubleshoot.md:17）。05 §4 示例与 prompt 场景逐字同构（`getOrder` + 同类 `view` 调用，05-spring-cache.md:66-75），rubric 锚点"错误根因→D4 扣"不存在——自调用被标注为"最高频的不生效"（05:64），三种修复（拆 bean / `@Autowired self` / AopContext）带取舍表（05:80-84），`private/final` 变体与按序排查清单（05:86-88）齐备。

### T6 商品详情缓存一致性 — 通过（D3/D5 全额）

路由"缓存一致性"直达 06。读路径（§1 Cache Aside + §4 TTL 抖动 10%~30% 代码）、写路径（§2 表格中"更新缓存""先删缓存"均标 ✗，"先更 DB 再删缓存" ✓ 默认——rubric 锚点"推荐更新缓存/先删缓存→D5 重扣"不可能命中）、击穿双方案（§5 互斥 DoubleCheck 伪代码含 null 哨兵与降级出口、§6 逻辑过期异步重建含兜底刷新提醒）、穿透（null 短 TTL + 布隆）、雪崩（抖动 + 降级）成体系。延迟双删局限单独点名（06:21"它是缓解不是消除"+ Canal 指路）。"热门商品过期瞬间别打挂 DB"精确对应 06:28 击穿行。

### T7 Boot 3.2 连不上 + 哨兵 — 通过（D3/D4 全额）

"连不上但地址密码都对"→ 08:9 直达 01 §4（Boot 3/4 `spring.data.redis.*` vs 2.x `spring.redis.*`，配错即静默不生效——正是 Boot 3.2 项目第一嫌疑）。哨兵 YAML（01:46-56）`master: mymaster` + `nodes: 哨兵:26379` 可直接照抄，rubric 锚点"nodes 写成数据节点地址→D4 重扣"被 01:58 易错框专门点名（"填的是哨兵地址，不是数据节点地址"），且区分了 `sentinel.password`（哨兵自身）与顶层 `password`（数据节点）——这是真实易错点。D3 锚点"命令超时默认值"在 01:25（Lettuce 默认 60s，核实为真）；附加嫌疑 `password: ""` 空串 AUTH 坑（01:31）也覆盖。

### T8 订单 30 分钟超时关闭 — 通过（D2/D4/D5 全额，v1.1.0 换题后覆盖完整）

路由"延迟队列 RDelayedQueue"（SKILL.md:103）→ 07 §7；09 §1 选型表"延迟/定时任务 → RDelayedQueue"反向互指。双队列写法（07:123-128：`getBlockingQueue` + `getDelayedQueue` + `offer(30, MINUTES)` + `take`）可执行。rubric 三坑逐一验证：①到期搬运由客户端实例驱动、重启须重建、**消费方也要常驻创建**（07:131）②无 ack 取走即丢 → MQ/定时兜底（07:133 + 09:10 选型表）③**订单超时关闭别押键空间通知**（09:101 逐字点名）。锚点"推荐键空间通知→D5 重扣"不可能命中——09 §4 坑 3 直接封死该路线，且 08:27 惰性删除条目从机制侧补充了"为什么不准时"。库存释放强互斥 → 07:158-159 DB 兜底收尾。

### T9 IP 限流 5 次/分钟 — 通过

07 §6 分工判据（07:118）："单维度简单限次（每 IP 每分钟 5 次）INCR+TTL / Lua 就够（04 §4）"→ 04:81-88 `RATE_LIMIT_LUA` 现成代码且示例 key 正是 `rate:login:{ip}` + 60s。rubric D5 锚点"裸 incr+expire 不提竞态→扣"不成立：04:80 注释逐字写明"首请求自增后崩溃 → key 永不过期、该维度永久被限"。多实例全局限频走 RRateLimiter 的边界（OVERALL vs PER_CLIENT 放大）在 07:115。429 返回是 Spring 通用知识，无需技能覆盖。轻微保留：固定窗口在窗口边界的双倍突发未提（rubric 未要求，不扣）。

### T10 LocalDateTime 报错 — 通过（08 缺行小扣已计入 D2）

报错文案逐字匹配 03:55 表行（`InvalidDefinitionException: Java 8 date/time type not supported`），SKILL.md:99 路由行含"GenericJackson2Json、LocalDateTime"直达 03 §3。rubric D4 锚点"三个必须项是否齐"——03 §3 代码四件套全配（`JavaTimeModule` :36、禁 TIMESTAMPS :37、`activateDefaultTyping` :38-40、禁 FAIL_ON_UNKNOWN_PROPERTIES :41、`registerNullValueSerializer` :42），且表格逐行给出"漏掉的报错/症状"；D5 锚点"只给 registerModule 不提 default typing 连锁坑"由 03:56（`LinkedHashMap` 行）覆盖，附带 03:58"自定义 mapper 不注册 NullValueSerializer"这一源码级冷知识（核实为真）。缺憾同 T2：08 症状表无该症状行，rubric 期望的"症状→08→03 §3"路径实际是"症状→SKILL 路由→03 §3"。

### T11 pool exhausted — 通过（D4/D5 全额）

08:12 直达 02 §5 且带"先确认 client-type"预处理。"配了 max-active=16 还是报"的真正机制正是 02 §1 核心认知：**Lettuce 普通命令共享一条连接根本不走池**（02:5-15），报池错说明真用了事务/阻塞命令或泄漏。rubric 锚点"只建议调大 max-active→扣"不成立：02:86 三因排查（max-wait 太短 / max-active 太小 / SessionCallback 长阻塞·阻塞命令泄漏）+ 02 §3 参数表区分"借连接等待 vs 命令超时"两个参数（02:45 明确"报池错别去调 timeout"）。Jedis 分支（02 §4：默认 max-wait=-1 无限等、借出不还泄漏、迁移决策表）完整覆盖 client-type 分流。

### T12 边界让位三合一 — 通过（D1/D8 全额）

①Testcontainers：SKILL.md:19-20"不适用于：测试容器化 Redis" + 探测分支"起 Redis 测试容器 → 退出本技能（属集成测试领域）"（SKILL.md:55）。②大 key 巡检：SKILL.md:69 逐字点名"慢查询监控 / 大 key 巡检 / 内存淘汰治理 → 不适用（运维范围）"。③搭主从+哨兵：SKILL.md:69"Redis 服务器安装 / 主从搭建……不适用"。检查点（SKILL.md:72）"判定为不适用 → 告知用户并建议退出"给出统一出口。**零越界**：01 §3.1 只教客户端连接哨兵（无搭建内容）、04 §1 的 scan/unlink 是应用侧批量删除而非巡检命令，agent 无从越权发挥。锚点"每越界一件扣一档"——一件都不会发生。

## 3. 技术事实核查（D9 主要依据）

### 核实为真（含 web 验证）

| # | 断言 | 位置 | 结论 |
|---|---|---|---|
| 1 | JDK 序列化 String 前缀 `\xac\xed\x00\x05t\x00\x09`（9 字符串） | 03:17 | 真：AC ED 魔数 + 00 05 版本 + 0x74 String 标记 + 长度 9 |
| 2 | Lettuce 未配 timeout 默认 60s 命令超时 | 01:25,30 | 真（`RedisURI` 默认 60s） |
| 3 | `password: ""` 空串触发 `ERR Client sent AUTH, but no password is set` | 01:31 | 真：Redis 真实报错文案，空串非 null 会参与 AUTH |
| 4 | Boot 3.0 `ssl` 布尔、3.1+ `ssl.enabled` 对象型 | 01:34 | 真（Boot 3.1 SSL bundle 改型） |
| 5 | cluster `max-redirects` Boot 层无默认、Lettuce 驱动默认 5 | 01:68 | 真（`ClusterClientOptions.DEFAULT_MAX_REDIRECTS=5`，`RedisProperties.Cluster.maxRedirects` 默认 null） |
| 6 | cluster 不支持 SELECT、`database` 静默无效 | 01:69 | 真 |
| 7 | `CROSSSLOT` 报错、hash tag `{}` 同 slot | 01:77 | 真 |
| 8 | 哨兵默认端口 26379、`sentinel.password`=哨兵密码、数据节点密码在顶层 | 01:52-58 | 真（Boot 属性语义正确） |
| 9 | Lettuce `shareNativeConnection` 默认 true、普通命令不走池；池仅事务/阻塞命令/显式关闭三场景 | 02:5-15 | 真 |
| 10 | Jedis 默认 max-active=8、max-wait=-1 无限等 | 02:75 | 真（commons-pool2 默认值） |
| 11 | Boot 2.0（2018）起 starter 默认 Lettuce | 02:51 | 真 |
| 12 | `GenericJackson2JsonRedisSerializer` 默认 mapper 不带 JSR310 | 03:55 | 真（默认构造只注册 NullValue serializer） |
| 13 | 报错文案 `Java 8 date/time type ... not supported by default` | 03:55 | 真（Jackson 原文） |
| 14 | 自定义 mapper 构造不注册 NullValueSerializer（2.7/3.x/4.x 源码一致） | 03:58 | 真（2.7/3.x 确认；4.x 未逐一验证，**低风险存疑**但方向无误） |
| 15 | Sa-Token 前缀"可重写 wrapKey 定制" | 03:77 | **web 核实为真**：v1.46.0 官方新增 RedisTemplate Dao 重写 `wrapKey` |
| 16 | Spring Cache 默认前缀 `cacheName::key`、Spring Session `spring:session:*` | 03:78-79 | 真 |
| 17 | scan count 为提示值、可能返回重复需去重；unlink 异步释放 | 04:17-26 | 真 |
| 18 | multiGet 按位对齐、缺失位为 null | 04:52 | 真 |
| 19 | Redis 事务无回滚、exec 时单条报错其余照常生效 | 04:72 | 真 |
| 20 | watch 冲突时 exec 返回 null | 04:67 | 真（SDR 丢弃事务返回 null） |
| 21 | EVALSHA 首次自动、NoScript 降级 EVAL | 04:91 | 真 |
| 22 | Lua 结果 1/0 自动映射 Boolean | 04:93 | 真 |
| 23 | `set`/`getAndSet` 覆盖清除 TTL | 04:100 | 真 |
| 24 | `HEXPIRE` 需 Redis 7.4+ | 04:102 | 真 |
| 25 | 1 亿用户位图约 12.5MB/日；HLL ~12KB、误差 0.81% | 04:111-112 | 真（100M/8=12.5MB；Redis 官方 0.81%） |
| 26 | RedisCacheManager 默认永不过期、`RedisSerializer.json()` 即 Generic 版 | 05:29,41 | 真 |
| 27 | 无参方法默认 SimpleKey.EMPTY 同名互相顶替 | 05:24,88 | 真 |
| 28 | `sync=true` 与 `unless` 互斥、组合抛 `IllegalStateException` | 05:92 | 真（Spring 注解校验行为） |
| 29 | 看门狗默认租期 30s、每 10s 续期（lockWatchdogTimeout/3） | SKILL:114, 07:96 | 真 |
| 30 | lock4j 坐标/默认值（acquireTimeout=3000ms、expire=30000ms 固定租期、抛 LockFailureException、`lock4j.*` 全局配置） | 07:43-56 | 真（官方文档口径）；pom 对 redisson 为 provided——**web 核实与官方"需自行引入 redisson"的集成方式一致** |
| 31 | lock4j 是注解门面，非第三种坐标 | 07:39-40 | 真 |
| 32 | `redisson-spring-boot-starter` 整体替换 RedisConnectionFactory | SKILL:44, 07:12 | 真（RedissonConnectionFactory 自动装配） |
| 33 | Boot 4 → Redisson 4.x 线、**3.x starter 在 Boot 4 下启动报错** | 07:36 | **web 核实为真**：issue [#6863](https://github.com/redisson/redisson/issues/6863) 记录该失败；starter 4.0.0 已发布。唯"2025-12 起"与 4.0.0 实际上架 2025-09 略有出入（口径差，非机制错） |
| 34 | 版本基准 Boot 3/4 = SDR 3/4 + Lettuce 6/7 | SKILL:30 | 真（SDR 4.0.x 已配 Lettuce 7.6，[官方 releases](https://github.com/spring-projects/spring-data-redis/releases)） |
| 35 | RDelayedQueue 到期搬运由客户端实例驱动、重启须重建、消费方也要常驻；无 ack | 07:131-133 | 真（Redisson javadoc 明示调度在客户端侧） |
| 36 | `trySetRate` 仅首次生效（幂等）、`setRate` 覆盖、`PER_CLIENT` 按实例放大 | 07:115-116 | 真 |
| 37 | RBloomFilter 判无一定无/判有概率误判、不可删除、`tryInit` 仅首次 | 07:142 | 真 |
| 38 | 主从异步复制切换可能丢锁、RedLock 争议 | 07:153-155 | 真 |
| 39 | 可重入基于 hash 记线程标识+计数；跨线程 unlock 抛 IllegalMonitorState | 07:102 | 真 |
| 40 | Pub/Sub 不落盘必丢、Lettuce 订阅走专用连接、集群 PUBLISH 全节点广播、Redis 7 SSUBSCRIBE | 09:36-38 | 真 |
| 41 | XGROUP CREATE 需 stream 存在、MKSTREAM 可建空流（含"确认所用 API 是否传了它"的稳妥措辞） | 09:73 | 真 |
| 42 | PEL 忘 ack 增长、`receiveAutoAck` 收到即 ack 处理异常不重投、XAUTOCLAIM 按 min-idle-time | 09:74-75 | 真 |
| 43 | 键空间通知默认关闭需 `notify-keyspace-events Ex`、过期事件由惰性/定期删除触发不准时 | 09:82,99 | 真 |
| 44 | 已过期未物理删除的 key 仍占内存、scan/dbsize 可见 | 08:27 | 真（SCAN 不检查逻辑过期） |
| 45 | RedisProperties 从 `org.springframework.boot.autoconfigure.data.redis` 注入（裸 redisson 场景） | 07:26 | 真 |
| 46 | TTL 抖动公式 10%~30%（`0.1 + random*0.2`） | 06:37 | 真 |

**结论：未发现虚构或错误的技术事实。** 4 项初始存疑项（Sa-Token wrapKey、lock4j provided、Redisson 4.x 线、Boot4/SDR4/Lettuce7 版本基准）经检索全部为真。

### D9 扣分点（-0.5）

1. **SKILL.md:30 版本基准行只写"+ Redisson 3.x"**，未涵盖 07:36 已声明的"Boot 4 → starter 4.x 线"——同文件内版本口径不同步（轻）。
2. **08 症状表与 SKILL 路由表覆盖不对称**：SKILL 承诺"报错类任务直接从 08 症状表入手"（SKILL.md:122），但 `\xac\xed` 乱码与 LocalDateTime 报错这两个 description 明列的报错信号（SKILL.md:17-18）在 08 表无对应行。
3. frontmatter `version: 1.0.0`（SKILL.md:22）而本轮被评物按 eval 记录已是审查轮删改后的 v1.1.0 内容——内容变更未 bump 版本号（仓库流程瑕疵，非内容矛盾，记录在案）。

## 4. Top 问题清单与改进建议（按影响排序）

1. **08 排错表缺 2 个高频症状行**（影响 D2/D9，全局 -1）。建议在 08 §1 表补两行：`key 前缀 \xac\xed 乱码 / 模式匹配失效 → 03-serialization.md §2`、`InvalidDefinitionException: Java 8 date/time type ... → 03-serialization.md §3`。这两个症状在 description（SKILL.md:17-18）里是触发信号，排错第一落点却找不到，是当前唯一"承诺的入口没兑现"处。
2. **SKILL 版本基准行与 07 的 Redisson 版本口径不同步**（D9）。SKILL.md:30 "…Lettuce 6.x/7.x）+ Redisson 3.x" 建议改为 "Redisson 3.x/4.x"或加"(Boot 4 下 starter 用 4.x 线，见 07 §1)"，消除同文件内新旧口径并存的风险。
3. **SKILL 强约束 5 与 07 §2 的论证复述**（D6 轻微）。SKILL.md:113 的"即便补成一条原子命令，续期、可重入、持有者校验释放仍是自己扛的坑位"与 07:61 的缺口列表几乎同构——常读层保留结论（"禁止自写，修复方向是迁移"）+ 指针即可，论据列表留 07 一处。
4. **09:60 注释位置**：`// receiveAutoAck = 收到即 ack` 挂在 `container.receive(` 调用行上方，易被误读为该行默认行为；移到 §3 语义清单第 2 条旁更准确。
5. **frontmatter version 未随审查轮变更 bump**：按仓库"版本号真值源"规约，内容删改后应升 1.1.0（发布侧 SkillHub 会静默拒收同号）。
6. （可选）T9 场景可在 04 §4 附近补一句"固定窗口在窗口交界有双倍突发、可接受即用，严格平滑换滑动窗口/RRateLimiter"，堵住限流常识缺口——rubric 未要求，优先级最低。

## 总评

**98 / 100**。该技能在 v1.0.0 全量审查轮后的状态：rubric 全部 12 个 prompt 的判分锚点（尤其是锁口径翻转、T8 换题后的三坑覆盖、T12 零越界）均有明确落点，C1–C3 的机械判据流程和输出前自检清单是可被 agent 严格执行的；40+ 条可独立验证的技术断言无一虚构。剩余失分集中在排错表两行缺口与两处版本/复述口径的收尾，均为低成本修复。
