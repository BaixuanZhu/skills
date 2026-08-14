# spring-boot-dev 独立盲评（agent B）

> 评者：agent B（独立第二盲评人，比 A 更严格）。判分依据：把 SKILL.md + 12 个 references 全部读完后，逐 prompt 自问"接到该请求、手里只有这套技能，能否产出合格代码"。
>
> 阅读范围：`I:\GitDownload\skills\skills\spring-boot-dev\SKILL.md`（152 行）+ `references/01..12-*.md`（共 2239 行）+ `eval/spring-boot-dev/{test-prompts.md, rubric.md}`。
>
> 评分锚点严格按 rubric.md。功能性缺陷（错误根因 / 错误代码 / 越界包办）对应维度 ≤4；陷阱遗漏 D5 扣 2-3 分；冗余 D6 按"瘦身后残余重复"判定。

---

## 先说找到的事实性问题（影响 D5/D9）

1. **`07-async-schedule.md:102` 把 deprecated API 标为 ✓**
   `public ListenableFuture<String> sendListenable(String to) { ... } // ✓ ListenableFuture`
   Spring 6.0（即 SpringBoot 3.x，本技能推荐 3.5.x）已 `@Deprecated` `ListenableFuture`，官方文档明确指向 `CompletableFuture`。技能把它列为"正确返回值类型"，与"3.5.x 推荐"自相矛盾。属事实性错误，会影响 D5/D9。

2. **`09-autowiring.md:9-12` 字段注入"优点/缺点"表与 2.6+ 禁令的口径冲突**
   第一节表里字段注入缺点写"允许循环依赖（掩盖问题）"——这是 2.5 时代行为。SKILL.md 强约束 8 与 09 第 106-110 节明确：2.6+ 字段注入循环依赖**也会启动失败**。第一节表没标注"历史/未禁用时"，agent 第一眼看到会形成错误心智模型。属口径不一致，影响 D5/D9。

3. **`SKILL.md:88` 事务路由表把 `@TransactionalEventListener` 关键词指向 `06-transaction.md`**
   第 88 行（事务行）的关键词列了 `@TransactionalEventListener`，路由指向 `06-transaction.md`，但 `@TransactionalEventListener` 详解实际在 `08-events.md`（06 文件里根本没有这个词）。同时第 90 行（事件行）也列了该关键词指向 `08-events.md`。冲突的指向会让 agent 想看事务感知事件时跑错文件。属内部导航瑕疵，影响 D7/D9。

4. **`04-validation.md:16` 措辞模糊（不算事实错误，仅表述风险）**
   "3.x 必须引此 starter（`spring-boot-starter-web` 不再传递校验依赖，2.x 也是独立 starter）"——容易让 agent 误读为"3.x 才不传递"。实际 2.4 起就不传递。措辞应改为"自 2.4 起 web starter 不传递校验依赖"。属表述缺陷，影响 D4（T4 场景）。

---

## 逐 prompt 打分

### Prompt T1（写注册接口·竞争场景：三层架构 + DTO 校验 + 边界让位）
- D1: 11  D2: 11  D3: 11  D4: 10  D5: 10  D6: 9  D7: 11  D8: 11  D9: 4
- 小计: 88/100
- 关键依据:
  1. `SKILL.md:60-77`「何时使用本技能」表第 1 行"写 Controller/Service/Repository 三层代码（未指明框架）"明确激活；第 64 行"参数校验"→ `references/04-validation.md`。触发精准。
  2. `SKILL.md:56` 第 0 步边界判定"写注册接口=Controller+校验+存库+登录...本技能只负责 Controller 写法 + 参数校验 + 全局异常，存库→mybatis-plus-dev，登录→sa-token-dev。**不越界包办。**"——边界让位明确（D8 优秀）。
  3. `02-layered-arch.md:34-55` 给出 `@Valid @RequestBody UserCreateDTO` → `UserVO` 的完整示例，`04-validation.md:33-62` 给 `@NotBlank`/`@Length`/`@Pattern`/`@Email` 注解 + messages。可执行性强。
- 扣分主因:
  - D6 扣 3：信息冗余。`02-layered-arch.md:1-3`「本技能只讲框架层分层写法；ORM 层→mybatis-plus-dev」与 `SKILL.md:31`、`SKILL.md:53`、`SKILL.md:74` 重复四次让位 ORM；`02:65` 又重述 Bean 拷贝坑指向 java-coding-guide-pro。瘦身没把这些"同义让位"压缩。
  - D4 扣 2：`02-layered-arch.md:131-132` 的 `create` 方法体只留了注释"业务校验 → DTO 转 Entity → userMapper.insert → Entity 转 VO"，没给具体 Convert 写法（指向 java-coding-guide-pro），对"只想快速产出注册接口骨架"的 agent 略空。
  - D5 扣 2：T1 没强制要求返回 VO 时检查懒加载/N+1，但 `02:30` 提到"@ManyToOne 懒加载序列化触发 N+1"，对存库后立即转 VO 的场景提示够。

### Prompt T2（@Transactional 自调用 + rollbackFor）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 12  D9: 4
- 小计: 97/100
- 关键依据:
  1. `SKILL.md:14-15` 次级触发信号直接列"@Transactional 自调用失效"——D1 满分。
  2. `06-transaction.md:11-45` 坑 1 完整命中 T2：代码模板与用户代码几乎一致（`this.insert(u)` 自调用），并给出 3 种解法（自注入 `@Lazy` / 拆 Bean / `AopContext.currentProxy()` + `@EnableAspectJAutoProxy(exposeProxy=true)`）。D4 满分。
  3. `06-transaction.md:64-82` 坑 3 命中 rollbackFor：明确"默认只回滚 RuntimeException + Error，受检异常提交不回滚"，并强调"永远写 `@Transactional(rollbackFor = Exception.class)`"。D5 满分。
- 扣分主因:
  - D6 扣 2：`12-pitfalls.md:84-93`「事务不生效排查」表与 `06-transaction.md:9-143` 全文几乎是同一组陷阱的二次清单化（自用/受检/多线程/引擎）。`12-pitfalls.md` 既已存在，`06` 完整罗列后 `12` 又抄一遍。
  - D7 扣 1：`SKILL.md:88` 事务路由行的关键词列了 `@TransactionalEventListener` 但指向 `06-transaction.md`，与 T9 用到的 `08-events.md` 路由冲突（详见事实性问题 #3）。

### Prompt T3（@Async 线程池坑·SimpleAsyncTaskExecutor）
- D1: 12  D2: 12  D3: 11  D4: 11  D5: 9  D6: 9  D7: 11  D8: 12  D9: 3
- 小计: 90/100
- 关键依据:
  1. `SKILL.md:8-9` description 关键词含"@Async / 线程池 / @Async 默认 SimpleAsyncTaskExecutor"，触发精准。
  2. `07-async-schedule.md:29-67` 坑 1 完整：默认 `SimpleAsyncTaskExecutor` + 自定义 `ThreadPoolTaskExecutor` 配置（core/max/queue/keepAlive/prefix/拒绝策略），并推荐 `CallerRunsPolicy`，最后 `@Async("emailExecutor")` 显式指定。D4 高分。
  3. `SKILL.md:104` 主动行为触发也命中"未配自定义 ThreadPoolTaskExecutor → 高并发打爆"。
- 扣分主因:
  - **D5 扣 3（事实性缺陷重扣）**：`07-async-schedule.md:102` 把 `ListenableFuture` 标为 ✓ 正确用法，但 SpringBoot 3.x（技能推荐 3.5.x）下 `ListenableFuture` 已 `@Deprecated`。agent 若照抄会给用户 deprecated 代码。
  - D3 扣 1：T3 的"高并发打爆"还涉及监控/线程池指标（`ThreadPoolTaskExecutor` 暴露 `getActiveCount`），技能未提。属次要缺口。
  - D9 扣 1：与 D5 同因——`ListenableFuture` 的"✓"标注与"推荐 3.5.x"自相矛盾。
  - D6 扣 3：`07-async-schedule.md:265-272`「最佳实践」第 1/3 条与第 29-67 节正文、第 267 节"自调用"再次重述，跨章重复。

### Prompt T4（校验不触发·反向题：类级 @Validated 是对的）
- D1: 12  D2: 11  D3: 11  D4: 9  D5: 11  D6: 9  D7: 11  D8: 12  D9: 3
- 小计: 89/100
- 关键依据:
  1. `SKILL.md:14-16` 次级触发含"@Validated 分组校验不触发"——激活精准。
  2. `04-validation.md:66-87` 非 Bean 参数校验须"**类级 @Validated** + 参数级约束"——直接命中 T4 代码片段（类级 `@Validated` 是**正确**的）。agent 读了这节不会误判。
  3. `04-validation.md:6-17` 前置依赖说明 + 命名空间注释覆盖了 T4 验证点里的"缺 spring-boot-starter-validation / jakarta vs javax"两条排查路径。
- 扣分主因:
  - D4 扣 3：`04-validation.md:16` 写"3.x 必须引此 starter（spring-boot-starter-web **不再传递**校验依赖，2.x 也是独立 starter）"——措辞模糊。T4 验证点明确要求 agent 识别"缺 starter"是真因，但这一行的措辞容易让 agent 误读为"3.x 才不传递"。技能没在依赖段直接说"2.4 起 web starter 不传递 validation"，对 T4 这种反向题不够锐利。
  - D5 扣 1：技能没明确点出"用户说没生效时，先 grep `spring-boot-starter-validation` 依赖是否在 pom"这一排查动作（仅在 `12-pitfalls.md:74-82` 提"类上缺 @Validated"等场景，没列"缺依赖"作为校验不触发的首要原因）。
  - D6 扣 3：`04-validation.md:119-140`「坑：分组校验不触发」表与 `12-pitfalls.md:74-82`「校验不触发排查」表内容 80% 重叠（同样列了"@Valid 无 groups / 类级 @Validated 不作用于参数 Bean / 参数前 @Validated(Group.class)"）。
  - D9 扣 1：同 D4——措辞模糊带来轻微不一致。

### Prompt T5（全局异常顺序：@ExceptionHandler 同类最近匹配 vs 跨类 @Order）
- D1: 12  D2: 12  D3: 11  D4: 12  D5: 11  D6: 9  D7: 11  D8: 12  D9: 4
- 小计: 94/100
- 关键依据:
  1. `SKILL.md:14-16` 次级触发"@ExceptionHandler 顺序错乱"命中。
  2. `05-exception-handling.md:50-72` 直接命中 T5：第 53-54 行"同类内：按异常类型「最近匹配」（**非代码顺序**）"+ 第 56-72 行"跨类：@Order 决定查找顺序"，第 71 行明确"兜底类 `@Order(Ordered.LOWEST_PRECEDENCE)`"。
  3. `05-exception-handling.md:14-39` 给出最小 `@RestControllerAdvice` 模板，含 `MethodArgumentNotValidException` 处理（T5 验证点要求）。
- 扣分主因:
  - D3 扣 1：T5 提到"参数校验异常返回 400"，技能 `05:24-30` 给了 `MethodArgumentNotValidException`，但没给 `ConstraintViolationException`（非 Bean 参数校验失败）的具体 handler 代码（只在 `05:46` 表里提了一句"返回 400 + 约束消息"）。
  - D5 扣 1：T5 没明确点"用户写法其实没真的错——同事说法只在跨 Advice 时才成立"。技能 `05:53-54` 强调"代码声明顺序不影响同类匹配"，足够让 agent 给出正确解释，但对"同事说错了"的归因点不够直接。
  - D6 扣 3：`12-pitfalls.md:108-117`「异常处理陷阱」表与 `05-exception-handling.md:90-98`「异常处理捕获不到的场景」表几乎完全同构（Filter/异步/Sa-Token 重复列两次）。

### Prompt T6（循环依赖：2.6+ 禁令 + 解法优先级）
- D1: 12  D2: 12  D3: 11  D4: 11  D5: 9  D6: 9  D7: 11  D8: 12  D9: 3
- 小计: 90/100
- 关键依据:
  1. `SKILL.md:14-16` 次级触发含"循环依赖报错（BeanCurrentlyInCreationException）"——精准。
  2. `09-autowiring.md:106-167` 命中：2.6+ 默认禁用（无论字段/构造器）、解法优先级"重构 > @Lazy > allow-circular-references（不推荐）"，第 122-129 行给出 Facade 重构示例。
  3. `SKILL.md:121` 强约束 8 + `SKILL.md:136` C6 检查点重申同一优先级。
- 扣分主因:
  - **D5 扣 3（事实性表述缺陷）**：`09-autowiring.md:9-12` 第一节字段注入缺点列"允许循环依赖（掩盖问题）"——这是 2.5 时代行为，与强约束 8（2.6+ 默认禁用，字段注入也报错）冲突。第 158 节有补充说明，但第一节表会让 agent 形成错误心智模型。T6 用户问"我用字段注入 @Autowired，为什么还报循环依赖？不是说字段注入能容忍循环吗？"——技能第 9-12 行恰好强化了这个错误观念。
  - D3 扣 1：T6 验证点要求"推荐构造器注入（启动期暴露循环依赖是优点）"，技能 `09:25-32` 有，但与第一节表的"字段注入允许循环依赖"表述打架，弱化了推荐力度。
  - D6 扣 3：循环依赖解法在 `SKILL.md:121`（强约束 8）、`SKILL.md:136`（C6 检查点）、`09:117-167`（解法 1/2/3）、`12-pitfalls.md:50`（速查表）共四处重述，瘦身后仍是同一规则的 4 次重复。
  - D9 扣 1：第一节表"允许循环依赖"与强约束 8"字段注入也报错"自相矛盾。

### Prompt T7（配置读不到：@Value 不松散绑定 + 静态字段注入失效）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 12  D9: 4
- 小计: 97/100
- 关键依据:
  1. `SKILL.md:9-10` description 含"@Value / 配置读不到 / 配置不生效"——精准触发。
  2. `03-config-properties.md:33-53` 坑 1（静态字段注入失效，给 setter 中转解法）+ `03:55-65` 坑 2（@Value 不松散绑定，必须严格匹配 `app.user-name`）——**两个独立坑都被点名**，T7 的"两个叠加坑"全部命中。
  3. `03:124-133` 推荐用 `@ConfigurationProperties` 支持松散绑定（T7 验证点"≥3 项推荐 ConfigurationProperties"）。
- 扣分主因:
  - D6 扣 2：`03:185-194`「配置读不到排障清单」与 `12-pitfalls.md:60-69`「配置不生效排查」表大量重叠（同样的 `Could not resolve placeholder` / 静态字段 / profile / 环境变量规则）。
  - D7 扣 1：T7 两个坑都在同一文件 `03-config-properties.md`，路由 OK，但 `SKILL.md:85` 路由行的"同时警告"列了"`@Value 不支持松散绑定与 @Validated 校验；静态字段注入须走构造器/setter`"已经把答案预告在路由表——agent 可能不点开文件就照抄，弱化了 `03` 文件内的完整说明。

### Prompt T8（3.x 自动装配：spring.factories 废弃 → AutoConfiguration.imports）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 11  D6: 9  D7: 11  D8: 12  D9: 4
- 小计: 95/100
- 关键依据:
  1. `SKILL.md:108` 主动行为触发"spring.factories 配自动装配（SpringBoot 3.x 项目）→ 3.x 已废弃，改用 AutoConfiguration.imports"——精准命中 T8 根因。
  2. `10-condition-bean.md:113-134` 给出 2.x vs 3.x 文件格式对比 + 完整路径 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（每行一个全限定类名）。
  3. `10-condition-bean.md:51-85` 坑"`@ConditionalOnBean` 的顺序依赖"——命中 T8 验证点"@ConditionalOnBean 跨配置类的顺序依赖陷阱"，并给解法（改 `@ConditionalOnClass` 或合并配置类）。
- 扣分主因:
  - D5 扣 1：T8 验证点要求"说明 @ConditionalOnBean 顺序陷阱"，技能 `10:60-85` 有，但 `SKILL.md:92` 路由表的"同时警告"写"`@ConditionalOnBean` 有顺序依赖陷阱（条件求值在单例实例化期，Bean 可能未注册）"——这句"条件求值在单例实例化期"措辞不准（实际是 Bean 定义注册阶段，`10:68` 写得对："Bean 定义注册阶段求值"）。SKILL 与 reference 内部措辞不一致。
  - D6 扣 3：3.x 自动装配规则在 `SKILL.md:108`（主动行为）、`SKILL.md:122`（强约束 9）、`10:113-134`（正文）、`10:198-202`（自定义 starter 段）、`12-pitfalls.md:123`（速查）共 5 处重述，瘦身未压缩。
  - D7 扣 1：`10-condition-bean.md:179-181`「五、排除自动装配」只写"见 01-startup-config.md 第二节"——交叉引用 OK，但同文件 `01:43-57` 已完整给过 exclude 写法，`10` 又单列一节略冗余。

### Prompt T9（事件机制：@TransactionalEventListener(AFTER_COMMIT) + fallbackExecution）
- D1: 12  D2: 10  D3: 12  D4: 12  D5: 12  D6: 9  D7: 10  D8: 12  D9: 3
- 小计: 92/100
- 关键依据:
  1. `SKILL.md:8` description 关键词"@EventListener"——触发。但**没列 @TransactionalEventListener**（只在第 68/90 行表里出现），对"事务回滚时邮件还是发了"这种症状描述的 prompt，触发依赖 agent 推理"事件 → 翻 08-events.md"。
  2. `08-events.md:93-139` 命中：`@EventListener` 默认同步无事务感知 + `@TransactionalEventListener(phase = AFTER_COMMIT)` 解法 + 关键价值"事务回滚则不发邮件"。
  3. `08-events.md:141-162` 坑"`@TransactionalEventListener` 在无事务时不触发"+ `fallbackExecution = true` 解法——T9 第三个验证点直接命中。
- 扣分主因:
  - **D7 扣 2（路由错误）**：`SKILL.md:88` 事务路由行把 `@TransactionalEventListener` 关键词指向 `06-transaction.md`，但实际详解在 `08-events.md`。agent 看到"事务感知事件"会先翻 `06`，扑空。
  - D2 扣 2：同因——`@TransactionalEventListener` 在 SKILL.md 出现两次（88/90），指向不同文件，发现性受影响。
  - D6 扣 3：`@EventListener` 默认同步的描述在 `SKILL.md:90`（路由警告）、`08:64-77`（正文）、`08:97-101`（对比表）、`12-pitfalls.md` 未单列但 `08:199` 又重述——同一规则在 08 文件内重复 3 次。
  - D9 扣 1：`SKILL.md:88` 与 `SKILL.md:90` 路由冲突（同关键词指向不同文件）。

### Prompt T10（范围边界：多技能竞争·让位 ORM/认证/单测）
- D1: 12  D2: 12  D3: 11  D4: 11  D5: 9  D6: 8  D7: 11  D8: 12  D9: 4
- 小计: 90/100
- 关键依据:
  1. `SKILL.md:44-57`「第 0 步：版本探测与边界判定」明确"任务同时触及框架层和 ORM/认证时（如**写注册接口**=Controller+校验+存库+登录），本技能只负责 Controller 写法 + 参数校验 + 全局异常，存库→mybatis-plus-dev，登录→sa-token-dev。**不越界包办。**"——直接命中 T10 场景。
  2. `SKILL.md:74-75` 「何时使用本技能」表底部明确让位映射：ORM→mybatis-plus-dev、认证→sa-token-dev、Java 语言层→java-coding-guide-pro、单测→java-unit-test、前端→—。
  3. `02-layered-arch.md:1-3`、`02:65`、`02:135-136` 三处再次声明 ORM/Bean 拷贝让位。
- 扣分主因:
  - D3 扣 1：T10 第 4 项"写单元测试"——技能 `SKILL.md:75` 让位 java-unit-test，但**没在「关键决策检查点」表里设单测触发信号**（C1-C6 都是框架层决策）。agent 知道让位，但不知道"接到 T10 时应该停下来先告知用户'单测需要切到 java-unit-test'"这个动作指引。
  - D4 扣 1：T10 要求"在输出中明确指向对应技能（不默默做完）"——技能 `SKILL.md:77` 检查点有"判定为不适用→告知用户该问题属哪个技能范围，建议切换"，但没给"在代码注释里标注 `// TODO: 单测见 java-unit-test`"这种可执行动作模板。
  - D5 扣 3：T10 是范围边界终极测试，但技能没明确点出"如果用户的项目里**没有** mybatis-plus-dev / sa-token-dev / java-unit-test 这几个技能怎么办"——agent 可能不知道"建议切换"后用户没装这些技能时的兜底（要不要自己写一份最小可用代码）。属边界模糊。
  - D6 扣 4（最严重）：让位声明在 `SKILL.md:17-20`（description 不适用段）、`SKILL.md:31`（开头总结）、`SKILL.md:53-54`（探测表）、`SKILL.md:56`（边界冲突处理）、`SKILL.md:74-75`（何时使用表底）、`02:1-3`、`02:65`、`02:135-136`、`05:98`（Sa-Token 异常让位）、`10:181`（排除装配让位）等**至少 9 处**重复声明"ORM→mybatis-plus-dev / 认证→sa-token-dev"。瘦身后残余重复严重，D6 重扣。

---

## 汇总

### 总分（10 个 prompt 平均）

| Prompt | 小计 |
|---|---|
| T1 | 88 |
| T2 | 97 |
| T3 | 90 |
| T4 | 89 |
| T5 | 94 |
| T6 | 90 |
| T7 | 97 |
| T8 | 95 |
| T9 | 92 |
| T10 | 90 |
| **总分（平均）** | **92.2 / 100** |

### 9 维度平均分

| 维度 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 | 平均 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D1（12） | 11 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | **11.9** |
| D2（12） | 11 | 12 | 12 | 11 | 12 | 12 | 12 | 12 | 10 | 12 | **11.6** |
| D3（12） | 11 | 12 | 11 | 11 | 11 | 11 | 12 | 12 | 12 | 11 | **11.4** |
| D4（12） | 10 | 12 | 11 | 9 | 12 | 11 | 12 | 12 | 12 | 11 | **11.2** |
| D5（12） | 10 | 12 | 9 | 11 | 11 | 9 | 12 | 11 | 12 | 9 | **10.6** |
| D6（12） | 9 | 10 | 9 | 9 | 9 | 9 | 10 | 9 | 9 | 8 | **9.1** |
| D7（12） | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 10 | 11 | **10.9** |
| D8（12） | 11 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | **11.9** |
| D9（4） | 4 | 4 | 3 | 3 | 4 | 3 | 4 | 4 | 3 | 4 | **3.6 / 4** |

**D6 是最弱维度**（平均 9.1/12，约 76%），主要因让位声明与陷阱速查表在多处文件重复。**D5 次弱**（10.6/12，约 88%），主要因 T3 deprecated API、T6 字段注入表述、T10 边界兜底缺失。

### 最严重的 3 个问题

1. **`07-async-schedule.md:102` 把 deprecated 的 `ListenableFuture` 标为 ✓ 正确用法**——技能推荐 SpringBoot 3.5.x，但 `ListenableFuture` 在 Spring 6.0（SpringBoot 3.x）已 `@Deprecated`。agent 照抄会给用户 deprecated 代码。**事实性错误**，影响 T3 的 D5/D9。

2. **`09-autowiring.md:9-12` 字段注入缺点表写"允许循环依赖（掩盖问题）"**，与 SKILL.md 强约束 8 + 09 第 106 节"2.6+ 默认禁用（字段注入也报错）"自相矛盾。第一节表会让 agent 形成错误心智模型——T6 用户问的恰恰是"我用字段注入为什么还报循环依赖"，技能第 9-12 行恰好强化了用户的错误观念。**口径不一致 + 表述缺陷**，影响 T6 的 D5/D9。

3. **跨文件残余重复严重（D6 系统性偏弱）**：
   - ORM/认证让位声明至少出现 9 处（SKILL.md 6 处 + references 3 处）。
   - 循环依赖解法优先级 4 处（强约束 8、C6、09 正文、12 速查）。
   - 3.x 自动装配 5 处（主动行为、强约束 9、10 正文、10 starter 段、12 速查）。
   - 校验不触发坑 2 处（04 坑表、12 排查表，80% 重叠）。
   - 事务不生效 2 处（06 全文、12 排查表）。
   - 异常处理陷阱 2 处（05 表、12 表，几乎完全同构）。
   
   瘦身（2774→2391 行）虽减了总量，但**没消除"同规则跨文件重复"**。`12-pitfalls.md` 作为"横向速查"本应只列 SKILL 未强调的，实际把各专篇的核心陷阱又抄了一遍。这是 D6 系统性失分的根因。

### 发现的事实性错误（汇总）

| # | 位置 | 错误 | 严重度 |
|---|---|---|---|
| 1 | `07-async-schedule.md:102` | `ListenableFuture` 标为 ✓ 正确用法，实际 SpringBoot 3.x 起 `@Deprecated` | **高**（会让 agent 产出 deprecated 代码） |
| 2 | `09-autowiring.md:9-12` | 字段注入缺点列"允许循环依赖（掩盖问题）"，与 2.6+ 禁令冲突 | **中**（错误心智模型，但 158 节有补充） |
| 3 | `SKILL.md:88` | 事务路由表把 `@TransactionalEventListener` 指向 `06-transaction.md`，详解实际在 `08-events.md` | **中**（导航错误，影响 T9 的 D7/D2） |
| 4 | `SKILL.md:92` | "@ConditionalOnBean 条件求值在单例实例化期" 措辞不准，应为"Bean 定义注册阶段"（`10:68` 写对了） | **低**（措辞瑕疵，不影响解法） |
| 5 | `04-validation.md:16` | "spring-boot-starter-web 不再传递校验依赖，2.x 也是独立 starter" 措辞模糊，易误读为"3.x 才不传递"（实际 2.4 起） | **低**（表述缺陷，T4 反向题不够锐利） |

---

## 整体结论

技能**核心陷阱覆盖完整、强约束清晰、决策检查点设计优秀**——10 个 prompt 中 8 个 ≥90 分，T2/T7 接近满分。但存在两类系统性问题：

- **D6 信息密度**：瘦身后残余重复严重，"横向速查 `12-pitfalls.md`"与各专篇正文大量重叠，是 9 维度里最弱的一项。
- **D5 个别事实/表述缺陷**：`ListenableFuture` 标 ✓（事实错误）、字段注入"允许循环"表述（口径冲突）、T10 边界兜底缺失。

**修复优先级**：① 删除 `07:102` 的 `ListenableFuture` 示例或改为 `CompletableFuture`（高）；② 修正 `09:9-12` 字段注入表，加注"2.6+ 默认禁令下字段注入也会启动失败"（中）；③ 修正 `SKILL.md:88` 路由表，把 `@TransactionalEventListener` 从事务行移除或改指 `08-events.md`（中）；④ 压缩 `12-pitfalls.md` 与各专篇的重复（中）。

做完这 4 项，预计总分可从 92.2 提到 95+，D6 从 9.1 提到 11+。
