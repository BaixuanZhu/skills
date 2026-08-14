# spring-boot-dev 盲评打分（agent A）

> 独立盲评。评估对象：`skills/spring-boot-dev/`（SKILL.md + 12 references，共约 2393 行）。
> 评分依据：`eval/spring-boot-dev/rubric.md`（9 维度，D9 满分 4，其余满分 12）。
> 评分原则：功能性缺陷 / 越界 / 陷阱遗漏重扣；每条依据引用具体位置。

## 维度评分汇总（先给结论，详见各 prompt）

| 维度 | 平均 | 说明 |
|---|---|---|
| D1 触发精度 | 11.5 | description 关键词覆盖密集，边界让位清晰 |
| D2 可发现性 | 11.5 | 决策路由表命中率高，几乎一对一 |
| D3 覆盖完整 | 11.6 | 10 个 prompt 涉及知识点几乎无盲点 |
| D4 可执行性 | 11.1 | 代码示例可直接照搬，少数诊断流略浅 |
| D5 防错/陷阱 | 11.2 | 核心陷阱点名到位（自调用/rollbackFor/默认线程池/3.x imports） |
| D6 信息密度 | 8.1 | 残余重复明显（12-pitfalls 大段复述；AOP 自调用 7+ 处重复） |
| D7 内部导航 | 11.0 | 路由表 + 同时警告列 + 交叉引用清晰 |
| D8 范围明确 | 11.1 | 让位规则 4 处声明，T1/T10 边界判定稳 |
| D9 整体一致性 | 4.0 | 满分，术语/版本号前后一致 |

**总分（10 prompt 平均）：91.1 / 100**

---

## 各 prompt 详评

### Prompt T1（写注册接口·竞争场景·三层架构+校验+边界让位）
- D1: 11  D2: 11  D3: 11  D4: 11  D5: 11  D6: 8  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **89/100**
- 关键依据:
  1. `SKILL.md:6-13` description 含「写接口 / 写 Controller / 写 Service / 参数校验 / validation」+ 依赖信号 `spring-boot-starter-web` → 在宽泛「写注册接口」场景下能竞争过 java-coding-guide-pro
  2. `02-layered-arch.md:34-55` 给出 DTO 入参 + VO 出参 + `@Valid @RequestBody UserCreateDTO` 完整示例；`04-validation.md:40-62` DTO 上 `@NotBlank/@Length/@Pattern/@Email` 一应俱全（用户名 3-20、手机号正则、邮箱、密码 8-32 直接套用）
  3. `SKILL.md:56` 边界冲突处理段 + `02-layered-arch.md:3,136` 明确「ORM 层（Mapper/BaseMapper/IService）→ mybatis-plus-dev」，强约束 7（`SKILL.md:120`）禁止 Controller 返回 Entity
- 扣分主因: D6 — 注册接口场景的信息在 SKILL 路由行 84/86、强约束 6/7、主动行为表行 109、04、05、12 多处分布，agent 需读 3 个文件才能拼齐「DTO+校验+全局异常+VO」全套，存在跨文件重复（04 校验失败异常处理 ↔ 05 异常处理 ↔ 12 section 5）

### Prompt T2（@Transactional 自调用失效）
- D1: 12  D2: 11  D3: 11  D4: 11  D5: 11  D6: 7  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **89/100**
- 关键依据:
  1. `06-transaction.md:11-45` 坑 1 几乎复刻该 prompt 的 `batchInsert + this.insert()` 代码，并给出 3 种解法（`@Lazy` 自注入 / 拆 Bean / `AopContext.currentProxy()` 含 `@EnableAspectJAutoProxy(exposeProxy=true)`）
  2. `SKILL.md:115` 强约束 2「自调用不走代理」一锤定音；`SKILL.md:103` 主动行为表「同类内 this.xxx() 调用带 @Transactional」命中
  3. `06-transaction.md:64-82` 坑 3 + `SKILL.md:116` 强约束 3 提醒「默认只回滚 RuntimeException+Error，受检异常须 `rollbackFor=Exception.class`」
- 扣分主因: D6 — AOP 自调用失效模式在 7 处重复（SKILL 强约束 2 / 主动行为表行 103 / 决策路由行 88/89/90 / 06 坑 1 / 07 坑 2 line 86-88 / 08 六 line 164-180 / 12 section 1），且 07:88 自己承认「原因与解法同 06-transaction.md 坑 1」却仍展开一节

### Prompt T3（@Async 线程池坑·SimpleAsyncTaskExecutor）
- D1: 12  D2: 11  D3: 12  D4: 12  D5: 11  D6: 8  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **92/100**
- 关键依据:
  1. `07-async-schedule.md:29-67` 完整 `AsyncConfig` + `ThreadPoolTaskExecutor` 示例（corePoolSize/maxPoolSize/queueCapacity/keepAlive/threadNamePrefix/`CallerRunsPolicy`），可直接照搬
  2. `07-async-schedule.md:69-78` 拒绝策略 4 种对比表，明确「CallerRunsPolicy 推荐（反压限流）」
  3. `SKILL.md:117` 强约束 4 + `07:265-267` 最佳实践 1 提醒「`@Async("executor名")` 显式指定，不指定仍用默认 SimpleAsyncTaskExecutor」
- 扣分主因: D6 — `@Async` 默认线程池警告在 SKILL 强约束 4 / 主动行为表行 104 / 决策路由行 89 / 07 坑 1 / 12 section 7 表第 2 行 5 处重复

### Prompt T4（参数校验不触发·反向题，代码其实对）
- D1: 11  D2: 11  D3: 11  D4: 11  D5: 11  D6: 8  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **89/100**
- 关键依据:
  1. `04-validation.md:69-87` 四、非 Bean 参数校验——明确「类级 `@Validated` ✗✗✗ 必须类级标」+ 给出与 prompt 几乎一致的代码（`@RestController @Validated` + `@RequestParam @Min(1)`），即技能明确认定该写法**正确**，agent 不会误判成「改参数级」
  2. `04-validation.md:14-16` 一、前置依赖——「3.x 必须引 `spring-boot-starter-validation`（`spring-boot-starter-web` 不再传递）」，对应 prompt「没生效」的真实根因之一
  3. `12-pitfalls.md:25-31` 命名空间对照表（`javax.validation` vs `jakarta.validation`）覆盖 3.x 第二个真实根因
- 扣分主因: D5/D6 — `12-pitfalls.md:73-82` 五、校验不触发排查表未把「缺 spring-boot-starter-validation 依赖」作为独立行（虽然 04:14-16 提到，但排障清单里漏行），且校验失效内容在 SKILL 强约束 6 / 主动行为表行 106 / 04 四/五 / 12 section 5 四处分布

### Prompt T5（全局异常·@ExceptionHandler 顺序误区）
- D1: 11  D2: 12  D3: 12  D4: 11  D5: 12  D6: 8  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **92/100**
- 关键依据:
  1. `05-exception-handling.md:50-72` 三、核心坑——明确「同类内按异常类型**最近匹配**，**非代码顺序**」「代码声明顺序不影响同类匹配结果」，直接纠正 prompt 中同事的误区
  2. `05-exception-handling.md:56-72` 跨类（多 `@RestControllerAdvice`）`@Order` 决定查找顺序 + 「兜底类 `@Order(Ordered.LOWEST_PRECEDENCE)`」明确给出
  3. `05-exception-handling.md:14-39` 最小 `@RestControllerAdvice` 示例已含 `MethodArgumentNotValidException`（`@RequestBody` 校验失败 → 400 + 字段消息拼接）
- 扣分主因: D6 — 顺序陷阱在 SKILL 强约束 5 / 主动行为表行 105 / 决策路由行 87 / 05 三 / 12 section 8 五处重复

### Prompt T6（循环依赖·2.6+ 禁令）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 9  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **94/100**
- 关键依据:
  1. `09-autowiring.md:106-116` 明确「SpringBoot **2.6+ 默认禁用循环依赖**，无论字段/构造器注入都报错」+ `BeanCurrentlyInCreationException` 报错片段，直接回答 prompt「为什么字段注入也报错」
  2. `09-autowiring.md:117-156` 解法优先级清晰：解法 1 重构消除（首选）> 解法 2 `@Lazy`（过渡）> 解法 3 `allow-circular-references=true`（**不推荐，掩盖设计问题**）
  3. `09-autowiring.md:8-32` 构造器注入推荐理由「启动期发现循环依赖是**优点**」直接回应用户「字段注入能容忍循环」的误解
- 扣分主因: D4 略低（解法 1 重构示例 `UserOrderFacade` 偏抽象，对「userService ↔ orderService」这种业务循环没给具体重构路径）；D6 较好（循环依赖重复较少）

### Prompt T7（配置读不到·@Value 松散绑定 + 静态字段双坑）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 8  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **92/100**
- 关键依据:
  1. `03-config-properties.md:55-64` 坑 2「松散绑定不支持」——直接复刻 prompt（`app.user-name` yml + `@Value("${app.userName}")` 读不到），明确「`@Value` 须严格匹配 yml 的 key」
  2. `03-config-properties.md:33-53` 坑 1「静态字段注入失效」——`@Value` 不能直接注入 static，给出 setter 中转解法（与 prompt「静态字段又是 null」对应）
  3. `03-config-properties.md:5-16` 决策表 + `SKILL.md:135` C5 检查点推荐 `@ConfigurationProperties`（支持松散绑定，≥3 项用）
- 扣分主因: D6 — 配置读不到在 SKILL 路由行 85 / 主动行为表行 107 / 03 五 / 12 section 4 四处分布，12 section 4 表几乎逐行复述 03:188-194

### Prompt T8（3.x 自动装配不生效·AutoConfiguration.imports）
- D1: 11  D2: 12  D3: 12  D4: 11  D5: 11  D6: 8  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **91/100**
- 关键依据:
  1. `10-condition-bean.md:113-134` 三、文件格式 2.x vs 3.x——给出正确路径 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（每行一个全限定类名）+ 「3.x 废弃 `spring.factories` 的 `EnableAutoConfiguration` key，仍用则**静默失效**」
  2. `10-condition-bean.md:52-85` 坑：`@ConditionalOnBean` 顺序依赖——「条件求值时 Bean 可能尚未注册」「Spring 官方明确警告不可靠」+ 解法（改 `@ConditionalOnClass` 或合并配置类）
  3. `SKILL.md:122` 强约束 9 + `SKILL.md:108` 主动行为表行 108（spring.factories 在 3.x 项目→警告）
- 扣分主因: D6 — 3.x imports 在 SKILL 强约束 9 / 主动行为表行 108 / 决策路由行 92 / 10 三 / 12 section 9 五处重复；D4 略低——prompt 给的是 2.x 的 `EnableAutoConfiguration=\\` 多值写法，技能未明确「3.x 不支持 `key=value` 形式，每行纯类名」这一格式差异（虽然在示例里展示了，但没在文字上对比强调）

### Prompt T9（事件机制·@TransactionalEventListener）
- D1: 11  D2: 12  D3: 12  D4: 11  D5: 11  D6: 9  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: **92/100**
- 关键依据:
  1. `08-events.md:93-137` 五、`@TransactionalEventListener`——`AFTER_COMMIT` 默认阶段 + 与 `@EventListener` 对比表「事务感知 ✗ vs ✓」+ 完整 publisher/listener 代码示例，直接对应 prompt「注册回滚时邮件还是发了」
  2. `08-events.md:141-162` 坑：`@TransactionalEventListener` 在无事务时**默认不触发**（`fallbackExecution = false`），给出 `fallbackExecution = true` 解法
  3. `SKILL.md:90` 决策路由行 90 警告列 + `SKILL.md:134` C4 检查点「涉及事务 → `@TransactionalEventListener`」
- 扣分主因: D4 略低——`@EventListener` 默认同步 + 默认无事务感知两点在 `08:64-77` 与 `08:93-105` 分两节阐述，agent 需读完两节才能完整回答；D6 较好（事件主题在 12 中无独立 section，重复最少）

### Prompt T10（范围边界·多技能竞争·终极让位判定）
- D1: 12  D2: 11  D3: 11  D4: 11  D5: 11  D6: 8  D7: 11  D8: 12  D9: 4
- 该 prompt 小计: **91/100**
- 关键依据:
  1. `SKILL.md:17-20` description「不适用（主动让位）」段 + `SKILL.md:31`「只管框架层…不管 ORM/认证/Java 语言层/单测」+ `SKILL.md:56` 边界冲突处理段（混合任务只做框架层部分）+ `SKILL.md:74-75` 何时使用表「不适用 → mybatis-plus-dev / sa-token-dev / java-unit-test」——4 处一致声明
  2. `02-layered-arch.md:3,90,136` 三处明确「Mapper / BaseMapper / IService → mybatis-plus-dev」「ORM 细节不碰」
  3. `11-springdoc.md:124` JWT 鉴权配置段虽涉及 token，但明确「鉴权框架本身（Sa-Token）→ sa-token-dev」——示范了即便在边缘场景也守住边界
- 扣分主因: D6 — 让位规则在 description / 第 0 步 / 何时使用 / 边界冲突处理 / 各 reference 头部多处声明，对 agent 单次执行是冗余（虽然对一致性有益）

---

## 跨 prompt 汇总

### 最严重的 3 个问题

1. **D6 残余重复严重——`references/12-pitfalls.md`（142 行）大量复述其他 reference**
   - section 3 启动报错速查表 = `01-startup-config.md:113-119` 五、启动失败速查的扩写
   - section 4 配置不生效排查 = `03-config-properties.md:186-194` 五、排障清单的逐行复制
   - section 5 校验不触发排查 = `04-validation.md` 各坑的表格化重排
   - section 6 事务不生效排查 = `06-transaction.md` 各坑的浓缩
   - section 7 异步/定时排查 = `07-async-schedule.md` 各坑的浓缩
   - section 8 异常处理陷阱 = `05-exception-handling.md:90-98` 五、的复制
   - section 9 自动装配陷阱 = `10-condition-bean.md` 的浓缩
   - section 10 生成代码前必对照清单 = `SKILL.md:112-123` 核心强约束 10 条的复述
   - 整文件几乎是一个「目录索引 + 复述」，agent 读完专篇再读 12 是纯冗余。建议保留 section 1（AOP 统一根因，有抽象价值）和 section 2（命名空间对照，跨主题），其余改为纯跳转链接。

2. **AOP 自调用失效模式在 7+ 处重复，且部分是「明知重复仍展开」**
   - `SKILL.md:115` 强约束 2（规则 + 3 解法）
   - `SKILL.md:103` 主动行为表行 103（命中模式）
   - `SKILL.md:88-90` 决策路由行 88/89/90 警告列（3 处）
   - `06-transaction.md:11-45` 坑 1（完整代码 + 3 解法）
   - `07-async-schedule.md:86-88` 坑 2（自己写「原因与解法同 06 坑 1」却仍占一节）
   - `08-events.md:164-180` 六（事件场景下的自调用，部分新增但大量重复）
   - `12-pitfalls.md:5-22` section 1（统一抽象，有抽象价值但与各专篇重合）
   - 建议：自调用失效的完整解释集中在 12 section 1（AOP 统一根因），各专篇只留 1 行链接 + 该主题特有的失效变体（如事务的「受检异常不回滚」、异步的「默认线程池」）。

3. **T4 反向题的诊断流程略浅——校验排障清单漏依赖项**
   - `12-pitfalls.md:73-82` 五、校验不触发排查表 5 行（缺 `@Valid` / 缺类级 `@Validated` / 用 `@Valid` 而非 `@Validated(Group)` / 默认组跳过 / 嵌套缺 `@Valid`），**唯独没有「缺 `spring-boot-starter-validation` 依赖」这一行**
   - 而 `04-validation.md:14-16` 明确说了「3.x 必须引此 starter」，但这条关键排障线索没进 12 的速查表
   - T4 是反向题（代码对、真因在外部），agent 排查时第一反应会查 12 的速查表，漏这一行会导致 agent 在「类级 @Validated 对不对」上反复纠缠，错失真因
   - 建议：12 section 5 增补一行「全部配置正确但校验仍失效 → 查 `spring-boot-starter-validation` 依赖（3.x web 不传递）+ 查 `javax` vs `jakarta` 命名空间」

### 最有价值的 3 个亮点

1. **「核心强约束 10 条」+「主动行为触发表」+「生成代码前必对照清单」三层护栏**
   - `SKILL.md:112-123` 强约束（规则） + `SKILL.md:100-110` 主动行为表（命中模式 → 提醒） + `12-pitfalls.md:130-142` 交付前清单（10 项核对）
   - 三层从「写前学规则」「读到危险代码提醒」「交付前自检」覆盖 agent 全流程，是这套技能区别于普通文档的核心价值
   - 例：T2 自调用、T3 默认线程池、T8 spring.factories 都被多层捕获，agent 几乎不可能漏

2. **「决策路由」+「关键决策检查点 C1-C6」防 agent 擅自决策**
   - `SKILL.md:81-94` 决策路由表（关键词 → reference + 同时警告）一对一命中
   - `SKILL.md:128-141` C1-C6 检查点（统一返回体 vs ResponseEntity / 默认 vs 自定义线程池 / 传播行为 / 事件机制 / 配置读取 / 循环依赖）—— 多技术路线场景强制「先问用户，不直接生成代码」
   - 例：T1 写注册接口时，C1 会先问「团队是否有 Result 约定」而不是直接造一个；T5 会先 grep 现有 Advice 风格。这是高级 agent 行为的正确建模

3. **边界让位规则在 4 处一致声明 + 各 reference 头部再次声明**
   - `SKILL.md:17-20`（description）/ `SKILL.md:31`（开篇）/ `SKILL.md:56`（边界冲突处理）/ `SKILL.md:74-75`（何时使用表）+ 各 reference 头部（如 `02:3`、`11:124`）
   - 这让 T1/T10 这种多技能竞争场景下，agent 无论从哪入口都能撞到让位规则
   - T10 涉及 4 项任务（接口+存库+登录+单测），技能明确只做第 1 项，其余 3 项指向 mybatis-plus-dev / sa-token-dev / java-unit-test——是这套技能最成熟的边界设计

---

## 备注

- **D9 一致性 4 分（满分）**：版本号（3.5.x 推荐 / 2.7.x 仍适用 / 4.x GA）、命名空间（jakarta vs javax）、依赖坐标（springdoc-openapi-starter-webmvc-ui）、让位目标（mybatis-plus-dev / sa-token-dev / java-coding-guide-pro / java-unit-test）在 SKILL.md 与 12 个 reference 间前后一致，无自相矛盾。
- **未发现功能性错误代码**：抽查 06 事务解法、07 线程池配置、10 AutoConfiguration.imports 路径、08 TransactionalEventListener 用法，均与 Spring Boot 3.x 官方语义一致。
- **T2 prompt 与技能教学的微妙张力**：prompt 描述「saveBatch 里第二条失败时第一条没回滚」——但 saveBatch 自身 `@Transactional` 已开事务，自调用只是让 insert() 的 `@Transactional` 失效（默认 REQUIRED 无行为差异），严格说 prompt 描述的症状与自调用根因不完全对应。但技能教学自调用失效本身是正确的，rubric 也以自调用为预期答案，故未扣分。这是 prompt 设计问题，非技能问题。
