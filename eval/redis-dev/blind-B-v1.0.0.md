# Redis 开发助手 Skill 盲评报告（盲评员 B）

> **评审对象**：`skills/redis-dev/`（SKILL.md + references/ 01~09，共 10 个文件，v1.0.0）
> **测试输入**：`eval/redis-dev/test-prompts-v1.0.0.json`（12 条对抗 prompt T1~T12）
> **评分标准**：`eval/redis-dev/rubric.md`（D1~D8 各 12 分，D9 4 分，满分 100）
> **评审日期**：2026-08-26
> **评审方式**：独立盲评（未参与编写）；通读全部文件后逐 prompt 模拟"只有这套技能的 agent"走流程（触发 → 依赖探测 → C1~C4 → 决策路由 → reference）；对可独立验证的技术断言做外部核查（Lettuce/Spring/Redis 官方文档与源码线索，来源见 §五末尾）。

---

## 一、总体结论

**总分：91 / 100**

这是一套完成度很高的技能。流程设计（第 0 步依赖探测 → C1~C4 强制选择题 → 决策路由 → 10 条强约束 → 输出前二值自检）机械可执行，12 条对抗 prompt 无一落入判分锚点的重扣项：T1 不会甩代码而是先问 C1、T3/T4 的看门狗与两步 setnx 陷阱被表格化拦截、T5 自调用根因与 prompt 场景逐字对应、T8 不会误归因 Sa-Token、T12 三件边界事全部让位。排错总表（09 §1，20 行症状→原因→修复→详见）是全技能的枢纽，D2 表现突出。技术断言绝大多数为真（JDK 序列化前缀 `\xac\xed\x00\x05t\x00\x09` 连字节级细节都对；watchdog 30s/10s、noeviction 报错文案、Boot2/3 前缀、Lettuce 60s 默认超时、sync+unless 抛 IllegalStateException 等均核实为真）。扣分集中在：① 一个**经外部核实的实质缺口**——自定义 ObjectMapper 传入 `GenericJackson2JsonRedisSerializer` 不注册 `NullValueSerializer` 时，@Cacheable 缓存 null 会抛 `No serializer found for NullValue`，而技能恰好同时建议"缓存 null（别写 unless）"与"按 03 §3 注入自定义 mapper"，两条建议组合即触发该错（05-spring-cache.md:42-43）；② 三处轻微事实错误（aof-use-rdb-preamble 默认版本写错、"缺 cluster 节点→slot 路由失败"因果不成立、Hash 字段级 TTL 未覆盖 Redis 7.4 HEXPIRE）；③ 个别排错路径少一跳（T11 报错文案的客户端来源未区分）。

---

## 二、逐场景评分表

| Prompt | 场景 | 综合分（/10） | 主维度表现 | 判分锚点命中情况 |
|---|---|---|---|---|
| T1 | 触发竞争+缓存路线 | 9.5 | D1/D3/D8 全达成 | 未踩任何锚点：先 C1 选择题（SKILL.md:87），默认路径含 cacheManager 显式 TTL（05 §3） |
| T2 | key 乱码反向题 | 10 | D2/D4/D5 全达成 | 未踩锚点：09:11 直达 + **旧 key 清理有点名**（09:11 修复列加粗、03 §6.4） |
| T3 | Redisson 锁+看门狗 | 10 | D4/D5 全达成 | 未踩锚点：`tryLock(3,10,SECONDS)` 被表格明确判死（07:90），40s 业务由看门狗覆盖 |
| T4 | 自实现锁 | 10 | D4/D5 全达成 | 未踩锚点：两步 setnx+expire 崩溃窗口点名（07:35），三件套齐 |
| T5 | @Cacheable 自调用 | 9.5 | D2/D4 全达成 | 未踩锚点：根因第一嫌疑是自调用（05 §4 标题"最高频"、09:16 列首位） |
| T6 | 一致性整体设计 | 9 | D3/D5 良好 | 未踩锚点：写路径默认"先更 DB 再删缓存"（06:18） | 
| T7 | 连接配置+哨兵 | 9.5 | D3/D4 全达成 | 未踩锚点：哨兵 yaml 可照抄，nodes=哨兵 26379（01:50-57） |
| T8 | 共库随机掉线 | 10 | D2/D5 全达成 | 未踩锚点：直达 08 §2，`evicted_keys` 实锤 + "前缀防不了淘汰"点破（08:40） |
| T9 | incr 限流原子性 | 9.5 | D4/D5 全达成 | 未踩锚点：两步竞态点名（04:28）+ Lua 原子版（04:31-39） |
| T10 | LocalDateTime 报错 | 9.5 | D2/D4 全达成 | 未踩锚点：三个必须项全齐（03:48-54），default typing 连锁坑点名 |
| T11 | pool exhausted | 9 | D4/D5 良好 | 未踩锚点："Lettuce 普通命令不走池"认知到位（02 §1），非"只调大 max-active" |
| T12 | 边界让位三合一 | 10 | D1/D8 全达成 | 未踩锚点：三件全部让位并给理由（SKILL.md:54、67） |

---

## 三、维度评分汇总

| 维度 | 满分 | 得分 | 简要依据 |
|---|---|---|---|
| D1 触发精度 | 12 | 11.5 | description 主场景 + "无论用户是否提到 Redis" + 次级代码/报错信号 + 不适用清单，宽泛场景（T1"加个缓存"）稳接；-0.5 为"缓存"一词对非 Redis 缓存场景（Caffeine）的过度触发风险（第 0 步的 Caffeine 分支基本兜住） |
| D2 可发现性 | 12 | 11.5 | 09 §1 症状表是优秀枢纽，T2/T5/T8/T10/T11 全部一步直达对应 reference 小节；SKILL.md 决策路由 9 行覆盖全部 9 文件 |
| D3 覆盖完整 | 12 | 10.5 | 12 条 prompt 知识点无硬盲区；-1.5：NullValueSerializer 缺口（T1/T6/T10 的 LocalDateTime+缓存 null 组合路径无答案）、T11 报错文案客户端来源区分缺失、cluster 拓扑发现语义未讲 |
| D4 可执行性 | 12 | 11 | 代码/配置块完整可照抄（哨兵 yaml、CacheManager、锁模板、Lua 脚本）；-1：06 §5 互斥回源模板引用未定义的 `serialize/deserialize/NULL_MARK/retryOnceOrFallback` 占位方法，需 agent 自行补 |
| D5 防错/陷阱 | 12 | 10 | 陷阱清单极全（看门狗/leaseTime、自调用、默认永不过期、unless 写反、noeviction、两套序列化、isHeldByCurrentThread、scan 重复）；-2：漏 NullValueSerializer 这个"不 fail loud"的隐蔽坑（且被自家两条建议组合触发）、Jedis/Lettuce 池报错文案来源未区分 |
| D6 信息密度 | 12 | 10.5 | 以表为主、说理极少；02 §3 与 §5 有轻度重叠，09 §1 修复列与 reference 一句话重复（属索引功能，可接受） |
| D7 内部导航 | 12 | 11.5 | 路由表 + 全部交叉引用编号经核对均有效（03 §6.3/§6.4、08 §2 等指向实存）；每文件尾部自检清单形成闭环；-0.5 为个别文件间指针需二次跳转（09→02→01） |
| D8 范围明确 | 12 | 11.5 | 不适用三行（运维/Sa-Token/测试容器）+ 08 开头范围声明 + 主动让位指针；08 §4 本地 docker-compose 示例贴边但服务于应用行为验证，未越界 |
| D9 整体一致性 | 4 | 3 | 术语/规则/版本号全套件一致（30s/10s、两套序列化措辞、Boot2/3 前缀各处统一）；-1：3 处轻微事实错误 + 1 处版本边界未核实（详见 §五） |
| **总分** | **100** | **91** | |

---

## 四、各 prompt 详评（含证据位置）

### T1（加缓存·宽泛场景）
- **触发**：description "在 Java / Spring Boot 项目中开发任何缓存……无论用户是否提到 Redis"（SKILL.md:4-10）+ "何时使用"首行"写 / 改缓存逻辑"（SKILL.md:60）→ 稳定激活。
- **流程**：第 0 步要求先 grep pom/代码（SKILL.md:47）；无依赖时主动询问并给出 Caffeine 备选（SKILL.md:52）。"缓存"命中 C1（SKILL.md:87）→ 执行规则 2 强制本轮只出选择题（声明式 vs 手动 + TTL 脏读窗口），规则 4 提供单轮场景的默认回退并标注。默认推荐 = @Cacheable + 显式 TTL 30min。
- **产出**：05 §3 给出完整 `RedisCacheManager`（entryTtl 兜底 + perName + StringRedisSerializer + JSON value），强约束 2/3（SKILL.md:109-110）双保险"默认永不过期"与"两套序列化"。
- **D8**：技能内无三层接口写法内容，自然不越界。
- **小瑕疵**：若用户实体含 LocalDateTime，05:42-43 引导改用 03 §3 自定义 mapper —— 该路径有 §五.E 的 NullValue 缺口。
- **结论**：D1/D3/D8 全达成，锚点未踩。9.5/10。

### T2（key 乱码反向题）
- **路由**：报错类直接进 09 症状表（SKILL.md:121 步骤 1）；09:11 行 `key 显示 \xac\xed\x00\x05t\x00\x03... 乱码` 与 prompt 症状逐字匹配 → 03 §2。
- **解释**：03:15 完整解释 `\xac\xed\x00\x05t\x00\x09user:1001` 形态、`keys user:*` 匹配不到、ttl 要带前缀——正面回答"怎么回事"。
- **修复完整性（锚点重点）**：09:11 修复列加粗"**按前缀清掉旧 key**"；03 §6.4 给出 scan+unlink 清理或等 TTL；03:15 警告两种方案读同一批 key。锚点"只改序列化器不提旧数据清理"未命中。
- **结论**：D2/D4/D5 全达成。10/10。

### T3（Redisson 锁 + 40s 下游调用）
- **检查点**："分布式锁"命中 C2（SKILL.md:88），确认问题含"业务执行时长是否可预估"——正是本 prompt 的隐藏决策点。
- **决策正确性（锚点重点）**：07:88-93 表格把 `tryLock(3, 10, SECONDS)`（固定租约）明确判"业务超 10s → 锁已易主，并发进入"；40s 业务对应的正确解"不传 leaseTime → 看门狗 30s 初租、每 10s 续期"（07:82，SKILL.md:113/138）与强约束 6 三处一致。锚点"给出固定租约"未命中。
- **细节**：07:64-77 完整模板含 try-finally + `isHeldByCurrentThread()` + 拿不到锁抛"操作繁忙"（非空转）；07 §1 两种依赖引入方式及 starter 全局替换的知情提示。
- **结论**：D4/D5 全达成。10/10。

### T4（自实现 setnx 锁）
- 07:35-59：`setIfAbsent`+补 `expire` 的两步写法标 ✗ 并说明崩溃窗口（锚点"接受两步写法"未命中）；✓ 版本三件套齐——原子 `setIfAbsent(key, token, Duration)`（01 处即带 EX）、value 唯一标识、Lua 校验后删（防误删他人锁）；:59 点名自实现无续期的局限并给出升级路径（Redisson 看门狗）。
- 08 自检清单第 1 条再次拦截两步写法。
- **结论**：D4/D5 全达成。10/10。

### T5（@Cacheable 自调用不生效）
- **路由**：09:16 行"@Cacheable 完全不生效（每次都查库）"直达 05 §4；09 §2 排查清单按序（EnableCaching → 代理路径 → bean → cacheNames → condition → key 冲突）。
- **根因**：prompt 描述与 05:66-74 示例**完全同构**（OrderService.getOrder 被同类 view 调用，this 绕过代理）；锚点"错误根因（没配 CacheManager 当第一嫌疑）"未命中——09:16 行首列就是"自调用绕过代理"。
- **修复**：三解法表（拆 bean / 注入自身 / AopContext+exposeProxy）+ private/final 同类失效补充（05:85），均可执行。
- **结论**：D2/D4 全达成。9.5/10。

### T6（一致性整体设计）
- **读路径**：06 §1 Cache Aside 流程 + §4 `ttlWithJitter`（10%~30% 抖动公式可用）。
- **写路径**：§2 决策表含"更新缓存 ✗ / 先删缓存 ✗"反例与并发时序解释，默认"先更新 DB 再删缓存"（锚点"推荐更新缓存或先删缓存"未命中）；延迟双删及其局限（:21）。
- **击穿**：§3 互斥锁回源 + §5 完整模板（DoubleCheck、null 短 TTL、finally+isHeldByCurrentThread、拿不到锁降级）——正面回答"热门商品过期瞬间别打挂数据库"。
- **穿透**：§3 参数校验 → null 缓存 30s~5min → 布隆过滤器（误判与不可删除的代价点名）。
- **雪崩**：抖动 + 多级缓存 + 高可用，三件套区分一句话（:31）。
- **小扣**：§5 模板的 `serialize()/deserialize()/NULL_MARK/retryOnceOrFallback` 为未定义占位（D4）；若配 LocalDateTime cacheManager 走 05:42-43 注释路径则踩 NullValue 缺口（§五.E）。
- **结论**：D3/D5 良好。9/10。

### T7（Boot 3.2 连不上 + 哨兵配置）
- **排错**："地址密码都对但连不上" → 09 §3 清单第 2 位即"配置前缀 vs Boot 版本"（Boot 3.x `spring.data.redis.*`，01 §4 对照表）；09:7 症状行同指。
- **哨兵（锚点重点）**：01:46-55 yaml 可直接照抄，`master: mymaster`（prompt 给的名字原样可用）、`nodes` 明确标注"哨兵节点地址（26379 是哨兵端口）不是数据节点"、哨兵密码与数据节点密码区分——锚点"nodes 写成数据节点地址"未命中。
- **事实**：max-redirects 默认 3（01:67）为真/低风险；connect-timeout 与 timeout 语义区分（01:29）准确。
- **结论**：D3/D4 全达成。9.5/10。

### T8（共库随机掉线）
- **路由**：09:20 行"用户随机掉线（与 Sa-Token 共库）"——症状级直达；description 也把该症状列为必须触发信号（SKILL.md:16-17）。
- **归因正确性（锚点重点）**：技能不往 Sa-Token 配置（timeout 等）上引，而是给淘汰机制（08 §2）、排查命令（`info memory` 贴 maxmemory、`evicted_keys` 非零即实锤）、三方案（分实例 > 容量 30% 余量 > volatile-lru 自保）；08:40 明确"key 前缀隔离只能防覆盖，防不了淘汰"。锚点"归因 Sa-Token 配置"未命中。
- C4 检查点（SKILL.md:90）与 08 §2 方案互为呼应，术语一致（"分实例/前缀隔离/容量"）。
- **结论**：D2/D5 全达成。10/10。

### T9（IP 限流）
- 04 §2：先给朴素 `increment + if(count==1) expire`，**随即点名两步竞态**（"首请求自增后进程崩溃 → key 永不过期，该 IP 永远被限"，04:28）并给 Lua 原子版（`INCR` + `EXPIRE` 单脚本，04:31-39）+ ZSet 滑动窗口备选（04:41）。锚点"裸 incr+expire 不提竞态"未命中。
- key 命名 `rate:login:{ip}`、超限返回 429 的业务逻辑技能不管（属应用层，非越界问题）。
- 06 自检"计数/限流 key 首建即有 TTL"双保险。
- **结论**：D4/D5 全达成。9.5/10。

### T10（LocalDateTime 报错）
- **路由**：09:12 精确症状行（报错文案与 prompt 逐字一致）→ 03 §3。
- **修复完整性（锚点重点）**：03:48-54 "三个必须项"表——JavaTimeModule（对症）、`activateDefaultTyping`（漏掉读回 LinkedHashMap 的连锁坑，锚点"只给 registerModule"未命中）、`FAIL_ON_UNKNOWN_PROPERTIES` disable（实体演进出 UnrecognizedPropertyException）；`disable(WRITE_DATES_AS_TIMESTAMPS)` 也给了。03 §3 完整代码块可照抄。
- **附带缺口**：该 mapper 若被 05:42-43 引去配 cacheManager，NullValue 缺口暴露（§五.E）。
- **结论**：D2/D4 全达成。9.5/10。

### T11（pool exhausted）
- **核心认知（锚点重点）**：02 §1 开篇即"Lettuce 普通命令根本不走池"（shareNativeConnection 默认 true，池仅在事务/阻塞命令/关闭共享时使用）——正面解释"配了 16 还是报"的第一重认知；02 §5 排查路径（max-wait 太短 / max-active 不足 / 连接泄漏）；§3 强调 `max-wait ≠ 命令超时`；§6 决策表给"无事务无阻塞 → 不配池"的收敛结论。锚点"只建议调大 max-active"未命中。
- **小扣（D3/D5）**：`Could not get a resource from the pool` 是 Jedis 的异常文案；Lettuce+commons-pool2 的池耗尽文案不同（Pool exhausted / Cannot allocate a new connection）。技能未提示"见到该文案先确认 client-type 是不是其实是 Jedis"——02 §4 的 Jedis 对照表可辅助推断但需要 agent 自己连点。
- **结论**：D4/D5 良好。9/10。

### T12（边界让位三合一）
- ① Testcontainers：SKILL.md:54 "起 Redis 测试容器 → 退出本技能 → java-integration-test references/04-testcontainers.md"；description 不适用清单同（SKILL.md:17-18）。
- ② 大 key 巡检：SKILL.md:67 "Redis 服务器安装 / 主从搭建 / 慢查询监控 / 大 key 巡检 → 不适用（运维范围）"；08:3 开头范围声明再兜底。注意技能内确有 UNLINK/lazyfree 等应用侧相关内容（08 §5、04 §4），但那是"删除阻塞对应用的影响"，与巡检运维边界分得清。
- ③ 主从+哨兵搭建：同 SKILL.md:67 行"主从搭建"。
- 三件全部让位且给理由，锚点"越界自己写"未命中。
- **结论**：D1/D8 全达成。10/10。

---

## 五、技术事实核查清单

### 判真（经外部来源或字节级推演核实）

| # | 断言 | 位置 | 判定 | 依据 |
|---|---|---|---|---|
| 1 | Boot 3.x `spring.data.redis.*` / Boot 2.x `spring.redis.*` | SKILL.md:41,137；01 §4 | **真** | Spring Boot 3.0 迁移指南（属性平移） |
| 2 | Lettuce 未配 timeout 时命令超时默认 60s | 01:24,29 | **真** | Lettuce 官方文档 "global timeout value of 60 seconds"；spring-boot#26472 维护者确认 |
| 3 | `GenericJackson2JsonRedisSerializer` 默认 mapper 不含 JSR310，LocalDateTime 抛 `InvalidDefinitionException` | 03:52；05:42；09:12 | **真** | Spring Data Redis 源码（默认 mapper 仅注册 NullValueSerializer + default typing）与广泛社区报告 |
| 4 | `sync=true` 与 `unless` 组合直接抛 `IllegalStateException` | 05:89 | **真** | Spring @Cacheable javadoc："unless() is not supported"；CacheAspectSupport 显式抛出（已 web 核实） |
| 5 | `unless="#result == null"` 恰好关闭 null 缓存 | SKILL.md:116；05:90 | **真** | unless=true 不回填 + Spring 默认 allowNullValues 缓存 NullValue |
| 6 | `RedisCacheManager` 默认永不过期 | SKILL.md:109；05:29 | **真** | entryTtl 缺省 null → 不过期 |
| 7 | Redisson watchdog：默认租期 30s（`lockWatchdogTimeout=30000`）、每 10s（租期/3）续期、显式 leaseTime 即失效 | SKILL.md:113,138；07:82-93 | **真** | Redisson 官方文档与源码（RedissonLock/ExpirationRenewal） |
| 8 | `redisson-spring-boot-starter` 把 RedisConnectionFactory 替换为 Redisson 实现 | SKILL.md:42；07:6-7；09:26 | **真** | RedissonAutoConfiguration 注册 RedissonConnectionFactory |
| 9 | JDK 序列化 key 形态 `\xac\xed\x00\x05t\x00\x09user:1001` | 03:15 | **真** | JDK 流头 AC ED 00 05 + TC_STRING('t'=0x74) + 2 字节长度 0x0009 与 "user:1001"（9 字符）吻合——字节级正确 |
| 10 | `setIfAbsent(key, token, Duration)` = `SET key val NX EX`；释放须 Lua 校验 | 07:39-56 | **真** | Spring Data Redis API + 标准 Redis 分布式锁写法 |
| 11 | noeviction 为默认策略；写满报 `OOM command not allowed when used memory > 'maxmemory'`（读不受影响） | 08:9-18 | **真** | Redis 默认配置 + 报错文案与 Redis 源码逐字一致 |
| 12 | `evicted_keys`（INFO stats）/ `used_memory`（INFO memory） | 08:34 | **真** | Redis INFO 文档 |
| 13 | 8 种淘汰策略清单及 volatile-* 只淘汰有 TTL 的 key | 08 §1 | **真** | Redis 文档（noeviction + allkeys/volatile × lru/lfu/random + volatile-ttl = 8） |
| 14 | `ERR Client sent AUTH, but no password is set`（password 空串触发） | 01:30；09:8 | **真** | Redis 6 前报错原文一致（6+ 附带提示后缀，技能写法兼容） |
| 15 | Cluster 不支持 SELECT/MULTI、CROSSSLOT、hash tag `{}` 绑 slot | 01:41,68,74 | **真** | Redis Cluster 规范 |
| 16 | Lettuce `shareNativeConnection=true` 默认共享单连接，池仅事务/阻塞命令/显式关闭时使用 | 02 §1 | **真** | Spring Data Redis LettuceConnectionFactory 文档 |
| 17 | pool 配置需 commons-pool2，缺失报 NoClassDefFoundError | 02:38 | **真** | GenericObjectPoolConfig 类不在 classpath |
| 18 | `max-wait=-1` 无限等；max-wait 是借连接等待非命令超时 | 02:35,49 | **真** | commons-pool2 语义 |
| 19 | SimpleKey 无参方法共享同一缓存项；condition 前判 / unless 后判 | 05:24-25 | **真** | Spring Cache 文档 |
| 20 | 自调用绕过代理；AopContext 需 exposeProxy；private/final 失效 | 05 §4 | **真** | Spring AOP 代理机制 |
| 21 | `sync=true` 仅单 JVM 防击穿，多实例各放一个线程 | 05:89 | **真** | RedisCache#get(key, loader) 为本地锁实现 |
| 22 | Redisson 可重入 = Redis hash 线程标识+计数；跨线程 unlock 抛 IllegalMonitorStateException | 07:97 | **真** | Redisson 实现 |
| 23 | 主从异步复制可丢锁；RedLock 有争议不推荐 | 07 §7 | **真** | Kleppmann/antirez 之争，Redisson 文档立场一致 |
| 24 | RDB 默认开 / AOF 默认关（appendonly no） | 08:57 | **真** | Redis 默认配置 |
| 25 | UNLINK 异步释放；lazyfree-lazy-expire/eviction/del 配置名 | 08 §5；04:67 | **真** | Redis 文档 |
| 26 | SCAN count 为提示值、结果可能重复；HLL ~12KB/0.81% 误差；1 亿 bit=12.5MB | 04 §1,§3 | **真** | Redis 文档（HLL 标准误差 0.81%） |
| 27 | LFU 需 Redis 4.0+、Stream 需 5.0+ | SKILL.md:139 | **真** | Redis 版本历史 |
| 28 | Redis TTL 惰性+定期删除；到期即不可读但物理删除滞后 | 08 §3 | **真** | Redis 过期删除机制 |

### 判误 / 存疑

| # | 断言 | 位置 | 判定 | 依据 |
|---|---|---|---|---|
| E1 | `aof-use-rdb-preamble` "Redis 4+ 默认" | 08:62 | **误（轻微）** | 4.0 引入时默认 `no`，**5.0 起才默认 `yes`**（已 web 核实：OneUptime/官方文档）。技能版本基准 6.x/7.x 下实践影响≈0，但版本归属写错 |
| E2 | "cluster.nodes 应填全部 master，缺节点时部分 slot 路由失败" | 09:43 | **部分不准确** | Lettuce/Spring Data Redis 支持 seed 节点子集 + `CLUSTER SLOTS` 拓扑自动发现；"缺节点→路由失败"的因果不成立（填全是稳妥实践，但理由错了）。标"待实跑验证"保守处理 |
| E3 | "Hash 没有字段级 TTL" | 04:9,17 | **过时（对 7.4+）** | Redis 7.4 引入 HEXPIRE（hash field TTL）；技能自声明"Redis 服务器 6.x/7.x"基准。Spring Data Redis 侧 API 支持仍有限，实践建议（拆 String key）仍成立，但绝对化表述对 7.4+ 不再为真 |
| E4 | "scan/keys 可能列出已过期未物理删除的 key（**Redis 7 之前**）" | 08:47 | **待实跑验证** | 机制本身为真（惰性删除）；但"Redis 7 起 scan 会过滤过期 key"的暗示未能核实（社区资料表明 Redis 7 下 SCAN 仍可能返回过期 key、需客户端按 TTL 过滤）。版本边界括注存疑 |
| E5 | 自定义 ObjectMapper 传入 `GenericJackson2JsonRedisSerializer` 即可安全用于 @Cacheable | 03:36-45 + 05:42-43 组合路径 | **缺口（可复现错误）** | 官方 javadoc：custom-configured mapper **必须**调用 `registerNullValueSerializer(mapper, ...)`，否则缓存 null（NullValue 占位）抛 `InvalidDefinitionException: No serializer found for NullValue`（已 web 核实）。技能 03 §3 的 mapper 未注册该 serializer，05 §3 注释又把含 LocalDateTime 的 cacheManager 场景引到这条路径，叠加"要缓存 null（别写 unless）"的建议（05:90）——三条建议组合即触发线上异常。manual RedisTemplate 路径不受影响（不会写 NullValue） |
| E6 | "Could not get a resource from the pool" 作为通用池耗尽症状 | 02:94-95；09:10 | **欠精确（非虚构）** | 该文案是 Jedis 异常原文；Lettuce+commons-pool2 池耗尽文案为 "Pool exhausted"/"Cannot allocate a new connection"。未提示先确认 client-type，T11 场景（自述 Lettuce + Jedis 文案）少一跳 |

**核查参考来源**：
- Lettuce 生产使用文档（默认 60s 超时）：https://redis.io/docs/latest/develop/clients/lettuce/produsage/
- Spring Boot Issue #26472（Lettuce 默认 60s 确认）：https://github.com/spring-projects/spring-boot/issues/26472
- Spring @Cacheable javadoc（sync 限制 unless）：https://docs.spring.io/spring-framework/docs/5.0.1.RELEASE/javadoc-api/index.html?org/springframework/cache/annotation/Cacheable.html
- GenericJackson2JsonRedisSerializer javadoc/源码（registerNullValueSerializer 说明）：https://docs.spring.io/spring-data-redis/reference/api/java/org/springframework/data/redis/serializer/GenericJackson2JsonRedisSerializer.html 、https://github.com/spring-projects/spring-data-redis/blob/main/src/main/java/org/springframework/data/redis/serializer/GenericJackson2JsonRedisSerializer.java
- NullValue 序列化报错实录：https://lifelongprogrammer.blogspot.com/2017/01/caching-data-in-spring-using-redis.html 、https://stackoverflow.com/questions/65886082/how-to-use-genericjackson2jsonredisserializer
- aof-use-rdb-preamble 默认版本：https://oneuptime.com/blog/post/2026-03-31-redis-aof-use-rdb-preamble-hybrid/view 、https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/

---

## 六、Top 问题与改进建议

### Top 问题（按对 agent 产出的影响排序）

1. **NullValueSerializer 缺口（§五.E5，影响 T1/T6/T10 的推荐组合路径）**：03 §3 自定义 mapper + 05 §3"含 LocalDateTime 时按 03 §3 注入" + 05 §90"要缓存 null 别写 unless"三条建议组合，会产出缓存 null 即抛 `No serializer found for NullValue` 的配置——这是技能自己的防错建议引爆的坑，且报错点在读缓存序列化处，不 fail loud，正中本技能 D5 要防的类别。
2. **三处轻微技术事实错误（§五.E1~E3，影响 D9）**：aof-use-rdb-preamble 默认版本 4+→实为 5.0+；"缺 cluster 节点→slot 路由失败"因果不成立（拓扑自动发现）；"Hash 无字段级 TTL"对 Redis 7.4+（HEXPIRE）过时——绝对化表述与技能自声明"6.x/7.x 基准"冲突。
3. **T11 少一跳：池报错文案未区分客户端来源（§五.E6）**：`Could not get a resource from the pool` 是 Jedis 文案；用户自述配了 Lettuce 池却报 Jedis 文案，第一动作应是确认 `client-type`/实际生效客户端，技能 02 §5 直接进入池参数排查——多绕一步，偶发误诊。

### 次要问题

4. 06:48-80 互斥回源模板引用未定义的 `serialize()/deserialize()/NULL_MARK/retryOnceOrFallback` 占位方法，非可直接编译（D4）。
5. 08:47 "（Redis 7 之前）"版本边界括注未能核实，建议实跑或删括注（D9）。
6. C1~C4 触发信号为逐字关键词匹配（SKILL.md:78），诊断类 prompt（T2"存了对象"、T10 报序列化异常）也会命中 C3 而先抛选择题——规则 4 的默认回退兜得住，但对"怎么回事？"式求助多一轮交互，可在执行规则里补一句"诊断/排错类任务先给诊断，检查点问题并入修复方案确认"。

### 改进建议

1. **03 §3 mapper 配方补一行**：`GenericJackson2JsonRedisSerializer.registerNullValueSerializer(mapper, "@class")`（或注明"该 mapper 仅用于手动 RedisTemplate；用于 @Cacheable 必须注册 NullValueSerializer"），并在 05 §3 注释处同步改写——一处修复消除 Top1。
2. 修订 08:62 为"Redis 5.0+ 默认"；09:43 改为"建议列出全部 master（稳妥），但客户端具备拓扑自动发现能力"；04:9 补"（Redis 7.4 前无字段级 TTL；7.4 HEXPIRE 应用侧生态支持有限，拆 key 仍是通用解）"。
3. 02 §5 / 09:10 的池耗尽行补一句"该文案多见于 Jedis；配的是 Lettuce 却见此文案 → 先确认 client-type 与实际生效客户端"。
4. 06 §5 模板为 `serialize` 等占位方法补最小定义（一行函数签名或注明"按 03 §4 的 MAPPER 实现"）。
5. （可选）08:47 括注"Redis 7 之前"改为不带版本断言的中性表述，或实跑 Redis 6/7 各验证一次后保留。

---

*盲评员 B，2026-08-26。本报告基于当次全量阅读与外部核查，未修改 skills/ 下任何文件。*
