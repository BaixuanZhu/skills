# 评分标准（redis-dev 达尔文盲评用）

> 你是独立盲评 agent。你手里有：redis-dev 技能（SKILL.md + 9 个 references，`skills/redis-dev/`）、12 条 test-prompt（`eval/redis-dev/test-prompts-v1.1.0.json`）。
>
> 对每个 prompt，假设你是"接到该请求的 coding agent，手里只有这套技能"，逐步走技能的流程（触发判定 → 依赖探测 → 决策检查点 → 决策路由 → 读 reference），判断能否产出合格结果。按 9 维度打分。

## 9 维度评分（SkillLens 风格，满分 100）

每个维度 0–12 分（D9 为 4 分），按"agent 拿着这套技能执行 prompt，能否产出合格结果"打分：

| 维度 | 权重 | 判分锚点 |
|------|------|---------|
| D1 触发精度 | 12 | description 的关键词/场景，能否让 agent 在该用时用、不该用时不用；宽泛场景（"加个缓存"）能否激活 |
| D2 可发现性 | 12 | 想找的信息（配置前缀/陷阱/报错含义），在合理跳转步数内能找到（决策路由/排错表是否直达） |
| D3 覆盖完整 | 12 | prompt 涉及的知识点，技能是否有答案（无盲点） |
| D4 可执行性 | 12 | 给出的代码/配置/判据，agent 能否直接照做（不悬空、不模糊） |
| D5 防错/陷阱 | 12 | 隐蔽坑（不 fail loud 的错）是否点名：序列化乱码、看门狗/leaseTime、自调用、默认永不过期、noeviction |
| D6 信息密度 | 12 | 有无冗余表达/重复内容/纯说理段落拖累 agent |
| D7 内部导航 | 12 | 路由表/交叉引用是否清晰，agent 知道下一步看哪 |
| D8 范围明确 | 12 | 不适用场景是否声明并让位（Sa-Token 集成 → sa-token-dev；测试容器 → java-integration-test；服务器运维明确拒绝）；不越界写别人的内容 |
| D9 整体一致性 | 4 | 术语/规则/版本号是否前后一致、无自相矛盾；**技术事实是否有虚构**（默认值/API 签名/报错文案/参数名与真实 Spring Data Redis / Redisson 不符视为一致性缺陷） |

## 各 prompt 判分要点

### T1（加缓存·竞争场景）—— 重点 D1/D3/D8

- **D1 触发**："加个缓存"没提 Redis——description 与 C1 检查点能否接住宽泛场景（与 spring-boot-dev / java-coding-guide-pro 竞争时不漏触发）
- **D3 覆盖**：C1 选择题（声明式 vs 手动、TTL 确认）→ @Cacheable + cacheManager TTL 配置是否齐
- **D8 范围**：查询接口本身的三层写法不越界（让位 spring-boot-dev）

**判分锚点**：不问 C1 直接甩代码 → D1 扣；给出 @Cacheable 但不配 cacheManager TTL（默认永不过期坑未提示）→ D5 重扣。

### T2（key 乱码反向题）—— 重点 D2/D4/D5

- **D2**：从症状（`\xac\xed` 前缀、模式匹配失效）到 03 §2 的直达（SKILL 强约束 1 是常读层兜底）
- **D4/D5**：修复完整 = key 改 String 序列化器**并清理旧乱码 key**（03 §6 第 4 条：scan+unlink 或等 TTL）

**判分锚点**：只改序列化器不提旧数据清理 → D5 扣。

### T3（Redisson 锁+leaseTime 决策）—— 重点 D4/D5

- **D4**：40 多秒下游调用 → `leaseTime` 必须**显式且大于业务上界**（如 60s+ 余量）；waitTime 另算
- **D5**：try-finally + `isHeldByCurrentThread`、拿不到锁的真实处理（非空转）

**判分锚点**：不传 leaseTime 裸靠看门狗（业务挂死=锁被无限续期）或 leaseTime 小于业务上界（如 30s < 40s 业务）→ D4/D5 重扣。

### T4（自实现锁）—— 重点 D4/D5

- **D4**：答案应是**迁移成熟实现**，不是"教他写对的自实现"——裸 `org.redisson:redisson` 不引 starter、不动 Lettuce，"不想为一个锁引 Redisson"的顾虑已不成立
- **D5**：setnx+expire 两步的崩溃窗口、自实现缺续期/可重入/校验释放——作为"为什么迁移"的论据出现

**判分锚点**：接受手写并把 SET NX EX+Lua 三件套当答案 → D4/D5 重扣（修复方向是迁移不是打补丁）。

### T5（@Cacheable 不生效）—— 重点 D2/D4

- **D2**：症状能否路由到 05 §4（自调用 + 失效清单）
- **D4**：自调用根因 + 三种解法是否可执行

**判分锚点**：错误根因（如"没配 CacheManager"当第一嫌疑）→ D4 扣。

### T6（一致性整体设计）—— 重点 D3/D5

- **D3**：读路径（回源+TTL 抖动）/ 写路径（先更 DB 再删）/ 击穿（互斥回源 DoubleCheck 或逻辑过期异步重建）/ 穿透（null 缓存）是否成体系
- **D5**：延迟双删的局限、"先删缓存"的反例是否讲清

**判分锚点**：写路径推荐"更新缓存"或"先删缓存" → D5 重扣。

### T7（连接配置）—— 重点 D3/D4

- **D3**：Boot 3 前缀 `spring.data.redis.*`、命令超时默认值
- **D4**：哨兵配置语义（nodes=哨兵地址、master=名称）是否可直接照抄

**判分锚点**：哨兵 nodes 写成数据节点地址 → D4 重扣。

### T8（延迟任务选型）—— 重点 D2/D4/D5

- **D2**：从"订单 30 分钟未支付自动关闭"到 09 §1 选型表 → 07 §7 的路由是否直达
- **D4**：RDelayedQueue 双队列写法可执行（getBlockingQueue + getDelayedQueue + offer(延迟) + take）
- **D5**：三个坑是否点名——到期搬运由客户端实例驱动（重启须重建、消费方也要常驻创建）、无 ack 取走即丢（高可靠走 MQ/定时兜底）、别用键空间通知做订单超时

**判分锚点**：推荐键空间通知（TTL 过期回调）做订单超时 → D5 重扣；只写 offer 不提消费方重建实例 → D5 扣。

### T9（incr 限流）—— 重点 D4/D5

- **D4**：计数+窗口方案可执行（INCR + TTL 固定窗口，Lua 原子化）
- **D5**：incr 与 expire 两步的竞态（首请求崩溃 key 永不过期）→ Lua 原子化是否点名

**判分锚点**：裸 incr+expire 不提竞态 → D5 扣。

### T10（LocalDateTime 报错）—— 重点 D2/D4

- **D2**：症状→08 排错路由→03 §3 的跳转
- **D4**：JavaTimeModule + 三个必须项（default typing / 忽略未知字段 / NullValueSerializer）是否齐

**判分锚点**：只给 registerModule 不提 default typing 的连锁坑 → D5 扣。

### T11（pool exhausted）—— 重点 D4/D5

- **D4**：借连接等待 vs 命令超时的区分；max-wait/max-active 排查路径
- **D5**：Lettuce 普通命令不走池的认知（"配了 16 还是报"的真正原因定位：事务/阻塞命令占用 or 连接泄漏）

**判分锚点**：只建议调大 max-active → D4/D5 扣。

### T12（边界让位三合一）—— 重点 D1/D8

- **D1/D8**：①Testcontainers → java-integration-test；②大 key 巡检 → 明确运维范围拒绝；③搭主从集群 → 同上。三件都让位且给出理由

**判分锚点**：越界自己写 Testcontainers 配置/巡检命令/集群搭建 → D8 重扣（每越界一件扣一档）。

## 输出要求

1. 维度评分汇总表（9 维度 + 总分）。
2. 逐 prompt 评分表 + 详评（每个 prompt 引用具体证据位置，格式 `文件名:行号` 或 `文件名 §节`）。
3. **技术事实核查**：对技能中可独立验证的断言（属性名/默认值/报错文案/API 签名/机制描述）逐条判真伪，虚构或错误列出——这是 D9 的主要扣分来源。
4. Top 问题清单（按影响排序）与改进建议。
