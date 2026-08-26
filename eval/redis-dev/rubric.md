# 评分标准（redis-dev 达尔文盲评用）

> 你是独立盲评 agent。你手里有：redis-dev 技能（SKILL.md + 9 个 references，`skills/redis-dev/`）、12 条 test-prompt（`eval/redis-dev/test-prompts-v1.0.0.json`）。
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

- **D2**：从症状到 `09-troubleshoot.md` 乱码行的跳转是否直达
- **D4/D5**：修复是否完整——改 String 序列化器**并清理旧 key**（残留旧乱码 key 的后患是否点名）

**判分锚点**：只改序列化器不提旧数据清理 → D5 扣。

### T3（Redisson 锁+看门狗）—— 重点 D4/D5

- **D4**：40 多秒下游调用 → 是否走到"业务时长不可预估 → 不传 leaseTime → 看门狗"决策
- **D5**：try-finally + `isHeldByCurrentThread`、拿不到锁的真实处理（非空转）

**判分锚点**：给出 `tryLock(wait, 40, SECONDS)` 之类固定租约 → D4/D5 重扣（看门狗失效）。

### T4（自实现锁）—— 重点 D4/D5

- **D4**：`SET NX EX` 原子 + 唯一 value + Lua 校验释放三件套是否齐
- **D5**：setnx+expire 两步的崩溃窗口是否点名；无续期的局限是否说明

**判分锚点**：接受 `setIfAbsent` 后补 `expire` 的两步写法 → D4/D5 重扣。

### T5（@Cacheable 不生效）—— 重点 D2/D4

- **D2**：症状能否路由到 05 §4 / 09 排查清单
- **D4**：自调用根因 + 三种解法是否可执行

**判分锚点**：错误根因（如"没配 CacheManager"当第一嫌疑）→ D4 扣。

### T6（一致性整体设计）—— 重点 D3/D5

- **D3**：读路径（回源+TTL 抖动）/ 写路径（先更 DB 再删）/ 击穿（互斥回源 DoubleCheck）/ 穿透（null 缓存）是否成体系
- **D5**：延迟双删的局限、"先删缓存"的反例是否讲清

**判分锚点**：写路径推荐"更新缓存"或"先删缓存" → D5 重扣。

### T7（连接配置）—— 重点 D3/D4

- **D3**：Boot 3 前缀 `spring.data.redis.*`、命令超时默认值
- **D4**：哨兵配置语义（nodes=哨兵地址、master=名称）是否可直接照抄

**判分锚点**：哨兵 nodes 写成数据节点地址 → D4 重扣。

### T8（共库随机掉线）—— 重点 D2/D5

- **D2**：从"随机掉线"症状到 08 §2 的路由是否直达（排错表有该行）
- **D5**：淘汰机制解释 + `evicted_keys` 排查 + 分实例/容量方案；前缀隔离防不了淘汰是否点破

**判分锚点**：归因为 Sa-Token 配置问题（timeout 等）而不查淘汰 → D2/D5 重扣。

### T9（incr 限流）—— 重点 D4/D5

- **D4**：计数+窗口方案可执行（incr + TTL / ZSet 滑动窗口）
- **D5**：incr 与 expire 两步的竞态（首请求崩溃 key 永不过期）→ Lua 原子化是否点名

**判分锚点**：裸 incr+expire 不提竞态 → D5 扣。

### T10（LocalDateTime 报错）—— 重点 D2/D4

- **D2**：症状→09 表→03 §3 的跳转
- **D4**：JavaTimeModule + 三个必须项（default typing / 忽略未知字段）是否齐

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
