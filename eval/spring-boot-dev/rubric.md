# 评分标准（spring-boot-dev 达尔文盲评用）

> 你是独立盲评 agent。你手里有：spring-boot-dev 技能（SKILL.md + 12 个 references）、10 条 test-prompt。
>
> 对每个 prompt，假设你是"接到该请求的 coding agent，手里只有这套技能"，判断能否产出合格结果。按 9 维度打分。

## 9 维度评分（SkillLens 风格，满分 100）

每个维度 0–12 分（D9 为 4 分），按"agent 拿着这套技能执行 prompt，能否产出合格结果"打分：

| 维度 | 权重 | 判分锚点 |
|------|------|---------|
| D1 触发精度 | 12 | description 的关键词/场景，能否让 agent 在该用时用、不该用时不用；边界让位是否清晰 |
| D2 可发现性 | 12 | 想找的信息（注解语义/陷阱/代码模式），在合理跳转步数内能找到 |
| D3 覆盖完整 | 12 | prompt 涉及的知识点，技能是否有答案（无盲点） |
| D4 可执行性 | 12 | 给出的代码/配置/判据，agent 能否直接照做（不悬空、不模糊） |
| D5 防错/陷阱 | 12 | 隐蔽坑（不 fail loud 的错）是否点名 |
| D6 信息密度 | 12 | 有无冗余表达/重复内容/纯说理段落拖累 agent |
| D7 内部导航 | 12 | 路由表/交叉引用是否清晰，agent 知道下一步看哪 |
| D8 范围明确 | 12 | 不适用场景是否声明（不让 agent 越界到 ORM/认证/单测/前端） |
| D9 整体一致性 | 4 | 术语/规则/版本号是否前后一致、无自相矛盾 |

## 各 prompt 判分要点

### T1（写注册接口·竞争场景）—— 重点 D1/D3/D8

最高权重之一。验证触发 + 三层架构 + 边界让位：
- **D1 触发**：能否在"写接口"这种宽泛场景下激活（竞争过 java-coding-guide-pro）
- **D3 覆盖**：三层架构写法、DTO+校验注解、Controller 返回 VO 是否齐全
- **D8 范围**：存库是否指向 mybatis-plus-dev（不越界写 BaseMapper）

**判分锚点**：越界写 ORM CRUD（BaseMapper/IService）→ D8 重扣（≤4）。Controller 直接返回 Entity → D3 扣。

### T2（@Transactional 自调用）—— 重点 D4/D5

直击事务核心陷阱：
- **D4**：能否识别 `this.insert()` 自调用是根因，并给出 3 种解法之一
- **D5**：是否提醒默认只回滚 RuntimeException（rollbackFor 坑）

**判分锚点**：未识别自调用（给出错误根因，如"忘加 @EnableTransactionManagement"）→ D4/D5 重扣（≤4）。

### T3（@Async 线程池）—— 重点 D4/D5

直击异步核心陷阱：
- **D4**：能否识别默认 SimpleAsyncTaskExecutor，给出自定义 ThreadPoolTaskExecutor 配置
- **D5**：是否推荐 CallerRunsPolicy + 提醒 @Async("名字")

**判分锚点**：未识别默认线程池问题 → D4/D5 重扣。

### T4（校验不触发·反向题）—— 重点 D4/D5

这是**反向题**——代码其实是对的（类级 @Validated 正确），看 agent 是否误判：
- **D4**：能否识别代码本身正确，真实原因是缺依赖（spring-boot-starter-validation）或命名空间（jakarta vs javax）
- **D5**：能否区分 Bean 参数（@Valid）vs 非 Bean 参数（类级 @Validated）的差异

**判分锚点**：误判"类级 @Validated 不对，要改成参数级" → D4/D5 重扣（这是技能明确纠正的坑）。

### T5（全局异常顺序）—— 重点 D4/D5

验证 @ExceptionHandler 匹配机制理解：
- **D4**：能否纠正"代码顺序"误区（同类内按类型最近匹配，非代码顺序）
- **D5**：能否说明跨类时 @Order 才决定优先级；兜底类 @Order(LOWEST_PRECEDENCE)

**判分锚点**：附和"顺序不对，要把兜底放后面"（错误归因）→ D4 扣。

### T6（循环依赖）—— 重点 D4/D5

验证 2.6+ 禁令 + 解法优先级：
- **D4**：能否识别 2.6+ 默认禁用（无论字段/构造器注入）
- **D5**：解法优先级是否正确（重构 > @Lazy > allow-circular-references 不推荐）

**判分锚点**：建议直接 `allow-circular-references=true` 而不说明风险 → D5 扣。

### T7（配置读不到）—— 重点 D4/D5

两个叠加坑（松散绑定 + 静态字段）：
- **D4**：能否同时识别两个独立问题（@Value 不松散绑定 + 静态字段注入失效）
- **D5**：是否给出两个独立的解法

**判分锚点**：只识别一个坑（漏另一个）→ D5 扣 3-4 分。

### T8（3.x 自动装配）—— 重点 D4/D5

版本敏感陷阱：
- **D4**：能否识别 3.x 废弃 spring.factories，给出 AutoConfiguration.imports 正确路径
- **D5**：是否说明 @ConditionalOnBean 顺序陷阱

**判分锚点**：仍建议用 spring.factories（未识别 3.x 变更）→ D4/D5 重扣。

### T9（事件机制）—— 重点 D4/D5

事务感知事件：
- **D4**：能否识别 @EventListener 默认无事务感知，给出 @TransactionalEventListener(AFTER_COMMIT)
- **D5**：是否说明 fallbackExecution 坑

**判分锚点**：未提到 @TransactionalEventListener（只用 @EventListener）→ D4/D5 重扣。

### T10（范围边界·多技能竞争）—— 重点 D1/D8

技能边界判定的终极测试：
- **D1**：能否在多技能竞争场景下正确拆解职责
- **D8**：是否明确让位 ORM→mybatis-plus、认证→sa-token、单测→java-unit-test

**判分锚点**：越界包办（自己写 BaseMapper CRUD / StpUtil.login / @Test 单测）→ D8 重扣（≤4）。

## 打分输出格式（每个 prompt 必填）

```
### Prompt Tx（一句话场景描述）
- D1: x  D2: x  D3: x  D4: x  D5: x  D6: x  D7: x  D8: x  D9: x
- 该 prompt 小计: xx/100
- 关键依据（≤3 条，引用技能里的具体位置：行号/标题/代码块）:
  1. ...
  2. ...
  3. ...
- 扣分主因（这个 prompt 最大的失分点）:
```

## 铁律

- 每条依据必须能指向技能里的具体位置（行号/标题/代码块）。禁止泛泛说"覆盖全面"。
- **功能性缺陷重扣**：错误根因、错误代码、越界包办 → 对应维度 ≤4 分，不能因"文字通顺"给中庸分。
- **陷阱遗漏重扣**：隐性陷阱（自调用/默认线程池/rollbackFor/校验分组/自动装配文件）是技能核心价值，漏任何一个 → D5 扣 2-3 分。
- **越界重扣**：T1/T10 的边界让位是核心判据，越界写 ORM/认证/单测 → D8 ≤4。
- D6（信息密度）：冗余越多扣分越重。本技能刚做完整瘦身（2774→2391 行），重点核查瘦身是否留了残余重复。
