# Redis 开发助手 Skill 盲评报告（盲评员 A）

> **评审对象**：`skills/redis-dev/`（SKILL.md + references/ 9 文件，version 1.0.0）
> **测试输入**：`eval/redis-dev/test-prompts-v1.0.0.json`（T1~T12 对抗 prompt）
> **评分标准**：`eval/redis-dev/rubric.md`（D1~D8 各 12 分，D9 4 分，满分 100）
> **评审日期**：2026-08-26
> **评审方法**：通读全部内容 → 逐 prompt 模拟"只有这套技能的 agent"走完整流程（触发→依赖探测→C1-C4→决策路由→reference）→ 锚点严格执行 → 关键技术断言对照 Spring Data Redis 3.2.x / Spring Boot 3.2.x 源码与 Lettuce/Redis 官方文档核查。未修改 skills/ 下任何文件。

---

## 一、总体结论

**总分 97.5 / 100。**

这是一套完成度极高的技能。12 条对抗 prompt 的判分锚点（rubric 点名的全部重扣项）**无一例外**被技能内容以"机械可执行"的方式防住：C1-C4 检查点拦住"不问就写代码"，强约束 6 + `07-redisson-lock.md §4` 的真值表拦住"固定 leaseTime 压死看门狗"，`09-troubleshoot.md` 的 20 行症状表让 6 条排错类 prompt 全部两跳直达答案，SKILL.md:67-68 与第 0 步表格让 T12 三件事全部正确让位（且两个跨技能指针目标文件经核实真实存在）。技术事实层面表现罕见地扎实：对约 45 条可独立验证断言（属性名、默认值、API 签名、报错文案、机制描述）逐条核查，仅 **1 条虚构**（cluster `max-redirects` "默认 3"）、1 条版本边界错误（`ssl.enabled` 对 Boot 3.0 不适用）、2 条存疑、2 条次要不严谨——高风险断言（Redisson 看门狗 30s/10s、GenericJackson2Json 默认不带 JSR310、`OOM command not allowed` 报错文案、noeviction 默认、Lettuce 60s 命令超时、sync/unless 互斥抛 IllegalStateException）全部属实。失分集中在 D9（虚构默认值）与轻微的可执行性残留（`06 §5` 模板 5 个未定义符号）。

---

## 二、逐场景评分表

| Prompt | 场景 | 得分 | 一句话判定 |
|---|---|---|---|
| T1 | 触发竞争+缓存路线 | 12 | description "无论用户是否提到 Redis" + C1 选择题 + 05 §3 TTL 配置全链路接住 |
| T2 | 序列化乱码反向题 | 12 | 09 症状表一行直达，修复含"按前缀清旧 key"（锚点满足） |
| T3 | Redisson 锁+看门狗 | 12 | 40s 不可预估 → 不传 leaseTime，07 §4 真值表明确 `tryLock(3,10,SECONDS)` 为 ✗ |
| T4 | 自实现锁 | 12 | SET NX EX 原子 + UUID token + Lua 校验释放三件套齐，两步法反例点名 |
| T5 | @Cacheable 自调用 | 12 | 05 §4 示例与 prompt 同构，根因直达，三种解法可执行 |
| T6 | 缓存一致性设计 | 12 | 读/写路径 + 三件套 + 互斥回源 DoubleCheck 模板成体系，"先删缓存"明确标 ✗ |
| T7 | 连接配置+哨兵 | 12 | Boot 3 前缀、sentinel.nodes=哨兵地址、命令超时默认 60s（已核真）全对 |
| T8 | 共库淘汰反噬 | 12 | "随机掉线"一行直达 08 §2，evicted_keys 排查 + 三方案 + "前缀防不了淘汰"点破 |
| T9 | incr 限流原子性 | 12 | incr+expire 竞态点名 + Lua 原子化 + ZSet 滑动窗口备选 |
| T10 | LocalDateTime 报错 | 12 | 09 表直达 03 §3，"三必须项"表格防住只给 registerModule 的半吊子修复 |
| T11 | pool exhausted | 12 | 02 §1 "Lettuce 普通命令根本不走池"正中"配了 16 还是报"，三真因齐 |
| T12 | 边界让位三合一 | 12 | 三件全部让位/拒绝且理由明确，指针目标文件真实存在 |

**12/12 条锚点全防住**——区分度体现在维度分（D4/D6/D9 扣分），见下。

---

## 三、维度评分汇总

| 维度 | 满分 | 得分 | 主要依据 |
|---|---|---|---|
| D1 触发精度 | 12 | **12** | 12 条 prompt 全部触发（含宽泛 T1）；误触发有第 0 步询问分支兜底 |
| D2 可发现性 | 12 | **12** | 决策路由 9 行 + 09 症状表 20 行四列，6 条排错 prompt 全部 ≤2 跳直达 |
| D3 覆盖完整 | 12 | **12** | 12 条 prompt 知识点无盲点，另有 pipeline/bitmap/多数据源/Jedis 切换等超纲储备 |
| D4 可执行性 | 12 | **11.5** | 代码/配置均可直接照抄；扣 06 §5 模板 5 个未定义符号（NULL_MARK、serialize、deserialize、retryOnceOrFallback、fallback） |
| D5 防错/陷阱 | 12 | **12** | rubric 点名 5 类隐蔽坑全覆盖，另覆盖 sync+unless 写反、SimpleKey.EMPTY、scan 重复、url 覆盖优先级等 |
| D6 信息密度 | 12 | **11.5** | 表格化极高、几乎无说理散文；强约束与各 reference 自检清单存在轻度重叠复述 |
| D7 内部导航 | 12 | **12** | 路由表全覆盖 9 文件无孤儿，交叉引用一律带节号，使用流程 6 步线性 |
| D8 范围明确 | 12 | **12** | T12 三件让位；08 开头显式声明"不是运维手册"；Sa-Token 让位但保留淘汰波及 session 的必要跨界知识并交叉引用 |
| D9 整体一致性 | 4 | **2.5** | 1 条虚构默认值（max-redirects=3）+ 1 条版本边界错（ssl.enabled 对 Boot 3.0）+ 2 条存疑 + 2 条次要不严谨；术语与规则口径全文一致，无自相矛盾 |
| **总分** | 100 | **97.5** | |

---

## 四、各 prompt 详评（含证据位置）

### T1 —— "加个缓存"（触发竞争）

- **流程走查**：description 明确"无论用户是否提到 Redis（cache / caching / …）"（SKILL.md:9-10）→ 触发 ✓。第 0 步依赖探测（SKILL.md:45-54）：已有 data-redis → 直接激活；无 → 主动询问且给出 Caffeine 备选（单实例部署）。"帮我加个缓存"逐字命中 C1 触发信号（SKILL.md:87），执行规则 2 强制"本轮只输出确认问题，禁止生成代码"（SKILL.md:79）→ agent 不会不问就甩代码。
- **锚点核对**：①不问 C1 直接甩代码 → 防住（SKILL.md:79、SKILL.md:122）。②@Cacheable 不配 TTL → 防住：强约束 2"缓存必须显式 TTL……默认永不过期"（SKILL.md:109），05-spring-cache.md §3 完整 CacheConfig（entryTtl 兜底 + perName + 序列化 + computePrefixWith），05-spring-cache.md:61"兜底值必须 > 0"。
- **D8**：全文无 Spring 三层写法/业务代码内容，不越界。
- **得分 12**。

### T2 —— key 乱码反向题

- **流程走查**：description 报错关键词"key 乱码（\xac\xed）"（SKILL.md:14）→ 09-troubleshoot.md:11 一行直达：症状 `\xac\xed\x00\x05t\x00\x03...` → 原因"key 用了 JDK 序列化" → 修复"key 序列化器改 StringRedisSerializer，**按前缀清掉旧 key**" → 详见 03 §2。修复代码在 03-serialization.md:22-45（完整 RedisTemplate 配置）。
- **锚点核对**：只改序列化器不提旧数据清理 → 防住（09:11 修复列 + 03-serialization.md:97"旧 key 读不回：上线前按前缀清理（scan + unlink）或等 TTL 自然过期"）。乱码字节序列 `\xac\xed\x00\x05` + `t\x00\x09`（0x74 String 标记 + 9 字符长度）与 JDK 序列化真实输出一致（"user:1001" 恰 9 字符）。
- **得分 12**。

### T3 —— Redisson 锁 + 40s 下游

- **流程走查**：C2 命中（"锁"/"防重复"）。prompt 已隐含回答 C2 两问（"用 Redisson 实现" = 同意引入；"偶尔要跑 40 多秒" = 时长不可预估），按执行规则 5（SKILL.md:83）直接生成代码不再追问。路由 → 07-redisson-lock.md。标准模板（07:64-77）：`tryLock(3, TimeUnit.SECONDS)` 不传 leaseTime + try-finally + `isHeldByCurrentThread()` + 拿不到锁抛 BizException（非空转）。
- **锚点核对**：给出 `tryLock(wait, 40, SECONDS)` 固定租约 → 防住且是本技能最强防线之一：强约束 6（SKILL.md:113）+ 07 §4 真值表把 `tryLock(3, 10, SECONDS)` 明确标 ✗ 并写明后果"业务超 10s → 锁已易主，并发进入（且 unlock 抛异常）"（07:90）+ 07:93"传 leaseTime 的唯一正当理由"。40s 场景下看门狗 30s 租期每 10s 续期覆盖（07:82，参数已核真）。
- **得分 12**。

### T4 —— 自实现锁

- **流程走查**：路由 → 07-redisson-lock.md §2"自实现的最低正确线"：✗ 反例 `setIfAbsent` + 后补 `expire`（07:36-37）→ ✓ 完整代码：`setIfAbsent(key, token, Duration.ofSeconds(10))` 一条原子命令（对应 SET NX EX）+ UUID 唯一 value + Lua 校验后删（07:41-56）+ 无续期局限说明"业务超 10s 锁已释放 → 并发进入……业务时长不可预估，用 Redisson 看门狗"（07:59）。
- **锚点核对**：接受两步写法 → 防住（反例置顶）。三件套齐 → 满足。
- **得分 12**。

### T5 —— @Cacheable 不生效（自调用）

- **流程走查**：description 报错关键词"@Cacheable 不生效"（SKILL.md:15）→ 09-troubleshoot.md:16 行指向 05 §4，09 §2 六步排查清单（EnableCaching → 代理路径 → bean → cacheNames → condition → key）。prompt 已给出"view 调 getOrder"明确线索，05-spring-cache.md §4 的示例与 prompt **完全同构**（`OrderService.view` 调 `this.getOrder`），根因一段命中 + 三解法表（拆 bean / `@Autowired self` / AopContext+exposeProxy，含取舍标注 05:79-83）+ 同类失效补充（private/final 方法）。
- **锚点核对**："没配 CacheManager 当第一嫌疑" → 未出现（清单第 1 项是 @EnableCaching，属合理排查而非错误根因）。
- **得分 12**。

### T6 —— 缓存一致性整体设计

- **流程走查**：路由"穿透/击穿/雪崩、先更库还是先删缓存" → 06-cache-consistency.md。读路径（§1 Cache Aside 流程 + §4 ttlWithJitter 代码）、写路径（§2 四方案对照表：更新缓存 ✗、先删缓存 ✗、**先更新 DB 再删缓存 ✓ 默认**、延迟双删 ✓ 高一致）、击穿（§3 表 + §5 互斥锁回源完整模板：tryLock + DoubleCheck + null 短 TTL + finally/isHeldByCurrentThread + 拿不到锁降级）、穿透（null 缓存 30s~5min + 布隆过滤器含误判/不可删除代价）、雪崩（TTL 抖动 + 多级缓存/熔断）。延迟双删局限独立成段（06:21"它是缓解不是消除"）。
- **锚点核对**：推荐"更新缓存"或"先删缓存" → 防住（§2 表格明确双 ✗ + 强约束 8 SKILL.md:115）。
- **得分 12**。

### T7 —— 连接配置（Boot 3.2 + 哨兵）

- **流程走查**：路由 → 01-connection.md。Boot 3 前缀 `spring.data.redis.*`（01 §2 基准 yaml + §4 对照表）；"连不上"部分走 09 §3 六步清单（ping → 前缀 → 密码空串 → 哨兵 → 集群 → 云白名单）。哨兵配置（01:45-55）语义明确：`master: mymaster # 哨兵监控的 master 名，不是主机地址`、`nodes: 哨兵节点地址（26379 是哨兵端口）`、`sentinel.password` 与数据节点顶层 `password` 分离——可直接照抄。命令超时"未配置时 Lettuce 默认 60s"（01:24，**已核真**：Lettuce `RedisURI.DEFAULT_TIMEOUT = 60s`）。
- **锚点核对**：哨兵 nodes 写成数据节点地址 → 防住（01:57"易错"段 + 09 §3.4）。
- **得分 12**。（01 §3.2 集群节存在的"max-redirects 默认 3"错误不在 T7 哨兵场景路径上，计入 D9。）

### T8 —— 共库随机掉线

- **流程走查**：description 报错关键词"用户随机掉线（与 Sa-Token 共库）"（SKILL.md:16）+ C4 检查点（SKILL.md:90）→ 09-troubleshoot.md:20 一行直达 08-server-policy.md §2：症状（无规律、无法复现）→ 机制（allkeys-lru/volatile-* 淘汰挤掉 timeout 有效期内未活跃的 session → NotLoginException）→ 排查（`info memory` 的 `used_memory` 贴顶 + `INFO stats` 的 `evicted_keys` 非零即实锤）→ 三方案（分实例 > volatile-lru 自保+容量根治 > 前缀只防覆盖）。"重启不解决""内存快满了"两特征与 08 §2 症状描述吻合。
- **锚点核对**：归因为 Sa-Token 配置（timeout 等）而不查淘汰 → 防住（SKILL.md:43"淘汰策略会波及 session（用户随机掉线的头号嫌疑）"+ 08 §2 全节）。
- **得分 12**。

### T9 —— incr 限流

- **流程走查**：路由"incr 原子性" → 04-template-operations.md §2：先展示 incr+TTL 常规写法，紧接点名"`increment` 本身原子，但 increment + expire 是两步：首请求自增后进程崩溃 → key 永不过期，该 IP 永远被限"（04:28）→ Lua 原子化完整代码（INCR + 首次 EXPIRE，04:31-39）→ 滑动窗口 ZSet 备选（04:41）。限流 key `rate:login:<ip>` 与 03 §5 前缀规范一致；04 §6 自检首条"计数/限流 key 首建即有 TTL（或 Lua 原子化）"。
- **锚点核对**：裸 incr+expire 不提竞态 → 防住（竞态点名 + Lua + 自检三重覆盖）。
- **得分 12**。

### T10 —— LocalDateTime 报错

- **流程走查**：09-troubleshoot.md:12 症状行（报错文案逐字匹配 prompt）→ 原因"GenericJackson 的 mapper 没注册 JavaTimeModule" → 03 §3。核心断言"GenericJackson2JsonRedisSerializer 默认 mapper **不带** JSR310 模块"经 3.2.x 与 main 分支源码双核实**属实**（默认构造仅注册 NullValueSerializer + defaultTyping，无任何 JSR310 引用）。03:48-54"三个必须项"表格：漏 JavaTimeModule → 本报错；漏 activateDefaultTyping → LinkedHashMap；漏 disable FAIL_ON_UNKNOWN_PROPERTIES → 加字段后旧缓存炸。
- **锚点核对**：只给 registerModule 不提 default typing 连锁坑 → 防住（三必须项以"漏一个就是一个线上问题"的表格形式强制齐全）。
- **得分 12**。

### T11 —— pool exhausted

- **流程走查**：路由"pool exhausted" → 02-pool.md。§1 开篇即正面回答 prompt 之惑："Lettuce 普通命令根本不走池"——`shareNativeConnection=true`（已核真，Spring Data Redis 默认），所有普通命令共用一条多路复用连接，池仅在事务/阻塞命令/显式关闭共享三场景被用到（02:9-13）→"配了 pool.* 感觉没生效：正常"（02:93）。§5 排错表给出三真因：max-wait 太短 / max-active 小于并发事务数 / 连接泄漏（SessionCallback 长阻塞、阻塞命令无超时）。§3 明确"`max-wait` ≠ 命令超时"。
- **锚点核对**：只建议调大 max-active → 防住（02 §1/§5 的归因路径直接绕开"调大参数"这种表面解）。
- **得分 12**。

### T12 —— 边界让位三合一

- **流程走查**：①Testcontainers → 第 0 步探测表"起 Redis 测试容器/测试隔离 → 退出本技能 → java-integration-test `references/04-testcontainers.md`"（SKILL.md:54）+ description 不适用段（SKILL.md:17-18）；②大 key 巡检 → "何时使用"表"Redis 服务器安装/主从搭建/慢查询监控/大 key 巡检 → 不适用（运维范围，本技能只覆盖配置对应用行为的影响）"（SKILL.md:67）+ 检查点"判定为不适用 → 告知用户当前问题不在本技能范围并建议退出"（SKILL.md:70）；③搭主从+哨兵集群 → 同 ② + 08 开头边界声明（08:3）。两个跨技能指针目标文件经核实**真实存在**（`skills/sa-token-dev/references/07-redis-frontsep.md`、`skills/java-integration-test/references/04-testcontainers.md`），让位不会落空。
- **锚点核对**：越界自己写 → 三件全部防住，且拒绝时给出理由（运维范围 vs 应用侧配置）。
- **得分 12**。

---

## 五、技术事实核查清单

### 5.1 判定为真（抽样列示，均经源码/官方文档或高置信知识核实）

| # | 断言（位置） | 判定 | 依据 |
|---|---|---|---|
| 1 | Lettuce 未配 timeout 时命令超时默认 60s（01-connection.md:24） | **真** | Lettuce `RedisURI.DEFAULT_TIMEOUT=60s`，官方文档"By default, Lettuce uses a global timeout value of 60 seconds"；Spring Boot `RedisProperties.timeout` 无默认（null）时不覆盖 |
| 2 | GenericJackson2JsonRedisSerializer 默认 mapper 不带 JSR310（03-serialization.md:52、05-spring-cache.md:43） | **真** | spring-data-redis 3.2.x 与 main 源码：默认构造链仅注册 NullValueSerializer 的 SimpleModule + defaultTyping，全文件无 JavaTimeModule 引用 |
| 3 | GenericJackson2Json 默认写入 `@class`（03-serialization.md §1） | **真** | 同上源码：`Id.CLASS` + `As.PROPERTY`，属性名默认 `@class` |
| 4 | `RedisCacheConfiguration.defaultCacheConfig()` 默认 TTL 不限、value 为 JDK 序列化（SKILL.md:110、05:29） | **真** | Spring Data Redis `TTL_UNLIMITED`；value 默认 JdkSerializationRedisSerializer |
| 5 | Redisson `lockWatchdogTimeout` 默认 30000ms、不传 leaseTime 时 30s 租期每 10s（租期/3）续期、传 leaseTime 看门狗失效（SKILL.md:113、138；07:82-93） | **真** | Redisson 官方文档与 Config 默认值；`tryLock(wait, lease, unit)` 签名族属实 |
| 6 | `tryLock()` 无参立即返回；`lock()` 无限等待（07 §4 表） | **真** | RLock API 语义 |
| 7 | `@Cacheable(sync=true)` 与 `unless` 互斥，组合抛 IllegalStateException（05:89） | **真** | Spring Framework SPR-16410 / 官方文档 "sync cannot be combined with unless"，运行时抛 IllegalStateException |
| 8 | Spring 默认缓存 null（NullValue 占位），`unless="#result == null"` 会关闭 null 缓存（SKILL.md:116、05:90） | **真** | NullValue 机制；unless 执行后判断为 true 则不回填 |
| 9 | 配 `lettuce.pool.*` 缺 commons-pool2 → NoClassDefFoundError（02:38） | **真** | Boot 3.2 `LettuceConnectionConfiguration`：`isPoolEnabled` 后走 `LettucePoolingClientConfiguration.builder().poolConfig(...)`，无 commons-pool2 守卫，bean 创建期 NoClassDefFoundError（"不同 Boot 版本表现时机不同"的模糊化合理） |
| 10 | Lettuce `shareNativeConnection` 默认 true，普通命令共用一条连接（02:5） | **真** | Spring Data Redis LettuceConnectionFactory 默认 |
| 11 | pool 参数语义：maxWait=-1 无限等、maxIdle/maxActive/minIdle 语义（02 §3） | **真** | Boot 3.2 RedisProperties.Pool 默认 maxWait=`-1ms`；commons-pool2 语义 |
| 12 | 哨兵：`sentinel.master` 是名称、`nodes` 是哨兵地址（26379）、`sentinel.password` 与数据节点顶层 `password` 分离（01:45-57） | **真** | Spring Boot RedisProperties 结构 + 官方文档 |
| 13 | `spring.data.redis.url` 覆盖散装 host/port/password/database（01:32） | **真** | RedisProperties 文档"overrides" |
| 14 | cluster 不支持 SELECT（database 静默无效）、MULTI 不可用、CROSSSLOT 报错与 hash tag（01 §3） | **真** | Redis Cluster 协议；报错文案属实 |
| 15 | noeviction 为默认淘汰策略、写报 `OOM command not allowed when used memory > 'maxmemory'`、读命令不受影响（08:7-18） | **真** | Redis 文档与真实报错文案逐字一致 |
| 16 | 8 种淘汰策略语义、volatile-* 仅淘汰有 TTL 的 key（08 §1 表） | **真** | Redis 文档 |
| 17 | `ERR Client sent AUTH, but no password is set`（01:30、09:8） | **真** | Redis 真实报错文案（技能已加"部分版本"限定，password 空串规范化行为随版本变化） |
| 18 | 惰性+定期过期删除；TTL 到期立刻不可读但可能仍占内存（08 §3） | **真** | Redis 文档 |
| 19 | RDB 默认开 / AOF 默认关（`appendonly no`）；`aof-use-rdb-preamble` Redis 4+ 默认（08 §4） | **真** | Redis 文档 |
| 20 | lazyfree 三参数名（`lazyfree-lazy-expire/eviction/del`）、UNLINK 异步释放（08 §5、04 §4） | **真** | Redis 配置项名属实 |
| 21 | HyperLogLog ~12KB / 标准误差 0.81%；1 亿 bit 位图 ≈ 12.5MB（04:14-15） | **真** | Redis 文档；算术正确 |
| 22 | ZSet 同分按字典序（04:13） | **真** | Redis 文档 |
| 23 | scan 游标可能返回重复需去重；count 是提示值（04 §3） | **真** | Redis SCAN 语义 |
| 24 | `redisson-spring-boot-starter` 替换 RedisConnectionFactory 为 Redisson 实现、全局生效（SKILL.md:42、07:6-7） | **真** | Redisson Spring Boot 集成行为 |
| 25 | RLock 可重入基于 Redis hash（线程标识+计数）；跨线程 unlock 抛 IllegalMonitorStateException（07:97） | **真** | Redisson 实现与 JVM 锁语义 |
| 26 | RCountDownLatch 不可重用；RedLock 争议大且 Redisson 不推荐（07 §6-§7） | **真** | Redisson 文档 / Kleppmann-antirez 之争 |
| 27 | LFU 需 Redis 4.0+、Stream 需 5.0+（SKILL.md:139） | **真** | Redis 版本史 |
| 28 | JDK 序列化 key 前缀 `\xac\xed\x00\x05t\x00\x09`（9 字符 key）（03:15） | **真** | JDK 序列化流格式：AC ED（magic）00 05（version）74（String）00 09（长度） |
| 29 | 主从异步复制切换可能丢锁（07 §7） | **真** | 分布式锁经典问题 |
| 30 | `multiGet`/`executePipelined`/`DefaultRedisScript` 用法（04 §2/§5） | **真** | Spring Data Redis API 签名 |

### 5.2 判定为假 / 错误

| # | 断言（位置） | 判定 | 依据 |
|---|---|---|---|
| 31 | `max-redirects: 3  # MOVED/ASK 重定向跟随上限，默认 3`（01-connection.md:67） | **假（虚构默认值）** | Spring Boot 3.2 `RedisProperties.Cluster.maxRedirects` **无默认（Integer null）**；未配置时 Lettuce 驱动默认为 **5**（ClusterClientOptions 默认 5，官方文档 "follow -ASK and -MOVED redirects up to 5 times"；Jedis 亦为 5）。"默认 3" 无任何来源 |

### 5.3 版本边界 / 不精确

| # | 断言（位置） | 判定 | 依据 |
|---|---|---|---|
| 32 | `ssl.enabled: true`（Boot 3.x；Boot 2.x 为 `spring.redis.ssl`）（01-connection.md:33） | **部分不精确** | `ssl.enabled` 嵌套属性为 Boot **3.1+**；Boot 3.0 是布尔型 `spring.data.redis.ssl`。技能版本基准声明覆盖整个 Boot 3.x，对 3.0 用户照抄无效（影响小：3.0 已 EOL） |

### 5.4 存疑（待实跑验证，不计入虚构）

| # | 断言（位置） | 存疑点 |
|---|---|---|
| 33 | "scan/keys 可能列出已过期未物理删除的 key（**Redis 7 之前**）"（08-server-policy.md:47） | 机制本身（惰性+定期删除导致物理删除滞后）为真；但"Redis 7 之前"暗示 7.x 起不再如此，未找到版本分界依据——现行 7.x 的 SCAN 同样可能返回逻辑过期 key。该限定疑为臆造的版本分界 |
| 34 | Sa-Token "可重写 `wrapKey` 定制"（03-serialization.md:90） | Sa-Token 的 key 封装 API 名待核（老版本集成包为固定 `satoken:` 前缀拼接；`wrapKey` 是否为真实扩展点名待实跑） |
| 35 | 排行榜 `score = 分数*1e13 + (MAX-时间戳)`（04-template-operations.md:13） | 公式思路成立，但 Redis score 为 IEEE754 double（53 位尾数 ≈ 9.0e15），分数超过 ~900 时 `*1e13` 精度丢失——适用边界未提示 |
| 36 | "cluster.nodes 缺节点时部分 slot 路由失败"（09-troubleshoot.md:44） | 对 Jedis 成立；Lettuce 默认开启集群拓扑自动刷新，缺个别种子节点通常仍可工作，表述过于绝对（保守建议无害） |

---

## 六、Top 问题与改进建议（按对 agent 产出的影响排序）

1. **【事实错误·D9 主扣分项】`01-connection.md:67` "max-redirects … 默认 3" 是虚构默认值**（真实：Spring Boot 层无默认，Lettuce 驱动默认 5）。agent 会在集群重定向调优场景向用户转述错误基准。**建议**：改为 `max-redirects: 3  # 重定向跟随上限；未配置时 Lettuce 驱动默认 5，显式配置以免歧义`。
2. **【可执行性残留】`06-cache-consistency.md §5` 互斥回源模板含 5 个未定义符号**（`NULL_MARK`、`serialize`、`deserialize`、`retryOnceOrFallback`、`fallback`）——agent 照抄即编译失败，语义虽有注释兜底但需自行补齐。**建议**：补一行 `NULL_MARK` 常量定义与降级方法的最小骨架，或将伪方法改为带 TODO 注释的明确占位。
3. **【版本边界】`01-connection.md:33` `ssl.enabled` 未区分 Boot 3.0 / 3.1+**。**建议**：标注"Boot 3.1+；3.0 为 `spring.data.redis.ssl`"。
4. **【存疑限定】`08-server-policy.md:47` "（Redis 7 之前）" 的版本分界无依据**，agent 可能把"7 不会"当事实转述。**建议**：删去年限限定，改为"现行版本（含 7.x）SCAN 均可能返回已逻辑过期未物理删除的 key"。
5. **【次要】`04-template-operations.md:13` 排行榜复合 score 公式未提示 double 精度上限**（分数 ≳900 时失真）。**建议**：加一句适用边界或改推荐 string 分值方案。
6. **【次要】`09-troubleshoot.md:44` 集群种子节点缺失的后果表述对 Lettuce 过于绝对**。**建议**：注明"Jedis 必须覆盖全部 master；Lettuce 依赖拓扑刷新但种子全挂则无法引导"。
7. **【维护性】"null 缓存"规则在 SKILL.md:116、05:90、06 §3/§5 四处出现，强约束与各 reference 自检清单有轻度重叠**——当前口径一致（30s~5min、抖动可省），但按仓库一致性清单第 6 条属于改口径时需全套件 grep 的分裂风险点。**建议**：保持现状可接受，若再增场景应收敛为"定义一处 + 指针"。

### 亮点（评估结论的平衡记录）

- 12 条对抗锚点（重扣项）100% 被机械判据防住，不含糊、不依赖 agent 自觉。
- 高风险技术断言（看门狗参数、GenericJackson JSR310 缺失、三类报错文案、noeviction 默认、Lettuce 60s/共享连接、sync/unless 互斥）经源码级核查全部属实——事实密度与准确率在本仓库已评技能中属第一梯队。
- `09-troubleshoot.md` 20 行"症状→原因→修复→详见"四列表 + C1-C4 选择题 + 输出前二值自检（SKILL.md:126-133）构成完整的可执行闭环。
- 跨技能让位指针全部指向真实存在的文件，让位可落地。

---

*盲评员 A，2026-08-26。本报告基于当日源码核查（spring-data-redis 3.2.x/main、spring-boot 3.2.x、Lettuce 官方文档、Redis 官方文档），标注"待实跑验证"的条目不作虚构处理。*
