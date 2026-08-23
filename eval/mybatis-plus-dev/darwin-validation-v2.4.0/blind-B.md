# 达尔文盲评报告（独立盲评 agent B）

## 0. 方法自证

本报告只读了 rubric.md、test-prompts.md 与两份快照（versionA/、versionB/ 各 14 文件，全文）。两份 SKILL.md frontmatter 的 `version:` 字面值原样贴出：

```
versionA/SKILL.md 第 23 行：version: 2.4.0
versionB/SKILL.md 第 17 行：version: 2.3.1
```

声明：我不知道哪个版本是旧/新，全文按字面值称呼「2.4.0」（= versionA 目录）与「2.3.1」（= versionB 目录），不猜测、不受版本号数值影响打分。每条依据均指向具体文件与行号/标题。对抗集（T9-T14）按 rubric 重扣规则执行：会编译失败/语义错误的建议，相应维度 ≤4 分。

---

## 1. 逐 prompt 打分

### Prompt T1（新项目引入 + SB2.7/SB3.4/JDK8 三场景 starter 选择）
- 拿到的技能：版本 2.4.0
- D1: 11  D2: 11  D3: 11  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 92/100
- 关键依据：
  1. SKILL.md L34-43「版本与依赖」表：SB2→`mybatis-plus-boot-starter`、SB3→`spring-boot3-starter`、SB4→`spring-boot4-starter`；L43 明确「JDK8 项目用 `mybatis-plus-jsqlparser-4.9`」——三场景一次命中。
  2. references/01-start.md L9-27：一个完整依赖块（SB3）+ L17 文字映射 SB2/SB4（「映射见 SKILL.md『版本与依赖』表」）+ L19-27 jsqlparser 块与 JDK8 变体、静默失效警告。
  3. SKILL.md L42 + 01-start.md L7：勿同时引 `mybatis` / `mybatis-spring-boot-starter` 冲突警告（陷阱点名）。
- 扣分主因：01-start 仅保留一个完整坐标块，SB2/SB4 靠一行文字回指 SKILL.md 表，可执行性略经一次跳转（D4 边际）。

### Prompt T1（同场景）
- 拿到的技能：版本 2.3.1
- D1: 11  D2: 11  D3: 11  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 91/100
- 关键依据：
  1. references/01-start.md L9-34：SB2/SB3/SB4 三个完整 XML 依赖块，可直接复制。
  2. 01-start.md L36-50：jsqlparser 两块（JDK11+ 与 JDK8 `mybatis-plus-jsqlparser-4.9`），L51 静默失效警告。
  3. SKILL.md L126-129「版本注意」节：重复 L27-36 版本与依赖节及 13-migration 已有的 jsqlparser / PaginationInterceptor 信息（冗余）。
- 扣分主因：D6——「版本注意」节与版本依赖表/13-migration 三处重复同一信息；三个近乎相同的依赖块亦有体量冗余（但可直接复制的价值部分抵消）。

### Prompt T2（updateById 置 null 不生效 + 全局 update-strategy 询问）
- 拿到的技能：版本 2.4.0
- D1: 12  D2: 11  D3: 11  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 93/100
- 关键依据：
  1. SKILL.md L14 description 含触发词「更新后字段没变 / 字段置 null 不生效」（错误话术直接命中，D1 满档基础）。
  2. SKILL.md 强约束 #4（L87）：根因（`updateStrategy` 默认 `NOT_NULL`）+ 修法（`UpdateWrapper.set` / 字段级 `ALWAYS`）+ **全局改 `ALWAYS` 会让所有 null 字段写库误清数据——只允许字段级覆盖**（用户第三问的答案就在强约束正文）。
  3. 02-config.md §7（L110-171）：FieldStrategy 全表、yml 全局配置、字段级覆盖代码、「常见误区」L166-170 三条；05-wrapper.md §2（L45-56）`set(User::getAge, null)` 可编译代码。
- 扣分主因：D6——null 不更新规则散布于 SKILL #4、02 §7、03 §4、04 §4、08 #2 五处（各有分工但复述仍多）。

### Prompt T2（同场景）
- 拿到的技能：版本 2.3.1
- D1: 10  D2: 11  D3: 11  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 90/100
- 关键依据：
  1. SKILL.md 强约束 #4（L80）与路由「关键提醒」列 L94（「字段策略全局改 ALWAYS 会误清数据」）——判据在 SKILL.md 本体可达。
  2. 02-config.md §7 L166-170 常见误区（全局 ALWAYS 误清数据 / `UpdateWrapper.set` 精准置空 / `IGNORED` 废弃）。
  3. 03-entity.md §4 L65-70 内联 `LambdaUpdateWrapper.set` 代码 + 05-wrapper.md §2 L45-56 同代码（重复）。
- 扣分主因：D1——description 无「更新后字段没变/置 null 不生效」类错误触发词（依赖泛化 CRUD 词触发，命中力弱一档）；D6——03 §4 与 05 §2 代码重复（2.4.0 已收敛为指针）。

### Prompt T3（ROW_NUMBER 窗口 + GROUP BY COUNT 用 apply/last 拼 Wrapper）
- 拿到的技能：版本 2.4.0
- D1: 11  D2: 12  D3: 11  D4: 10  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 91/100
- 关键依据：
  1. SKILL.md 强约束 #3（L79-86）：窗口函数 / 聚合 + GROUP BY/HAVING 列入「必须改写 XML」，并直接点名 `apply()/last()` 拼片段是反模式。
  2. 05-wrapper.md §1.2（L19-39）：五类超界场景表（含用户两个场景）+ L31-37 反例代码**逐字就是用户想写的写法**（`w.apply("ROW_NUMBER() OVER (PARTITION BY dept_id...)").last("GROUP BY...")`），随后指向 10-xml。
  3. 08-antipattern.md #25（L118-125）：注入/跨库/语义三重理由 + resultMap 映射计算列的出路。
- 扣分主因：D4——给出「禁止」与「转 XML」的判据充分，但 10-xml 无一个窗口函数 XML 正例，agent 需自行组装（可做但多一步推理）。

### Prompt T3（同场景）
- 拿到的技能：版本 2.3.1
- D1: 11  D2: 12  D3: 11  D4: 10  D5: 11  D6: 9  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 90/100
- 关键依据：
  1. SKILL.md 强约束 #3（L72-79）+ 路由「关键提醒」L97（「SQL 函数表达式(窗口/聚合/GROUP BY/专有函数)转 XML，勿用 apply 拼」）。
  2. 05-wrapper.md §1.2（L19-39）与 08-antipattern #25 同 2.4.0 内容。
  3. 05-wrapper.md L125：末尾留有「（见 `eval/mybatis-plus-dev/` 达尔文验证）」维护者元信息指针——对运行 agent 是无效引用（该目录不属于技能内容）。
- 扣分主因：D6——同一规则在 SKILL #3 + 路由提醒列 + 05 §1.2 + 08 #25 四处复述（2.4.0 删提醒列后为三处）；eval 指针属维护者元信息。

### Prompt T4（逻辑删除全局配置 + 唯一索引冲突）
- 拿到的技能：版本 2.4.0
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. SKILL.md 强约束 #5（L88）：0+毫秒时间戳方案、全局 `logic-delete-field`/`@TableLogic`，且**「唯一索引须含 deleted（如 UNIQUE(username, deleted)），否则删除后同值插入报 Duplicate」并入强约束正文**（修剪「关键提醒」列后判据未丢失——rubric 特别盯的点通过）。
  2. 02-config.md §2（L36-65）：完整 yml + 语义解释（删除时生成 SQL）+ 六方言时间戳表 + 唯一索引 L52。
  3. 08-antipattern.md #6（L30-33）：时间戳方案下「每条删除记录 deleted 值不同，天然避免冲突」——直接回答「同名再插入会不会冲突」。
- 扣分主因：D6——逻辑删除规则分布于 SKILL #5 / 02 §2 / 03 §6 / 08 #6 四文件。

### Prompt T4（同场景）
- 拿到的技能：版本 2.3.1
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. SKILL.md 路由「关键提醒」L94：「逻辑删除推荐 0+时间戳；唯一索引含 deleted」——判据在 SKILL.md 本体可达。
  2. 02-config.md §2 L36-65 与 08 #6 L30-33：同 2.4.0 的完整覆盖。
  3. 03-entity.md §6（L82-90）：@TableLogic + Long 字段注解写法。
- 扣分主因：D6——同规则较 2.4.0 多一路由提醒列复述（五处）。两版同分属正常：改动未伤该场景。

### Prompt T5（@Transactional 不回滚：try-catch 吞异常 + this 自调用）
- 拿到的技能：版本 2.4.0
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. SKILL.md L17 description 触发词含「事务不回滚」——报错式求助直接命中。
  2. 11-transaction.md §3 场景 3（L155-179）：try-catch 吞异常 → `throw` 或 `setRollbackOnly()` 双修法带代码；场景 1（L96-139）：自调用三方案（@Lazy 自注入 / AopContext / 拆 Service）。
  3. SKILL.md 主动行为触发 L71（「@Transactional 无 rollbackFor → 显式 rollbackFor」）+ 11 §1 L28-53 checked exception 不回滚表——「逐个指出原因」的完整原因谱系（7 场景）都在 §3。
- 扣分主因：D6——08-antipattern #18-#21 四条与 11 §3 逐条重复（纠偏定位的代价）。

### Prompt T5（同场景）
- 拿到的技能：版本 2.3.1
- D1: 10  D2: 12  D3: 12  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 93/100
- 关键依据：
  1. 11-transaction.md §3 场景 1/3 与 08 #19/#20：内容与 2.4.0 逐字一致，覆盖完整。
  2. SKILL.md L107「组合场景阅读顺序」含「事务回滚排查→先 11 后 08」——多文件路由明确。
  3. description（L4-15）无「事务不回滚」类报错触发词，仅「事务管理」泛化词。
- 扣分主因：D1——报错话术命中力弱于 2.4.0 的显式触发词。

### Prompt T6（gender 枚举 1/2 映射：BaseMapper + 自定义 XML，前端收数字）
- 拿到的技能：版本 2.4.0
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 9  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 94/100
- 关键依据：
  1. SKILL.md 强约束 #9（L92）：`@EnumValue`+`@JsonValue` 与「XML 每处 typeHandler」双判据都在强约束正文（rubric 盯的修剪回归点通过）；description L16 含「枚举存数据库」触发词。
  2. 03-entity.md §7（L85-162）：GenderEnum(1,"男")/(2,"女") 代码与 prompt 数字完全对齐；「前端收到枚举名→加 @JsonValue」坑（L160）直接回答前端诉求。
  3. 10-xml.md §5.4（L261-275）：resultMap / 条件 #{} / 插入 #{} 三位置 typeHandler 全示例。
- 扣分主因：D6——枚举 XML 声明在 03 §7 与 10-xml §5.4 两处贴近同代码，加 SKILL #9、08 #16/#17 共五处。

### Prompt T6（同场景）
- 拿到的技能：版本 2.3.1
- D1: 10  D2: 12  D3: 12  D4: 11  D5: 12  D6: 9  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 92/100
- 关键依据：
  1. SKILL.md 路由「关键提醒」L95：「枚举 @EnumValue+@JsonValue；XML 每处 typeHandler」——判据可达（rubric 盯的点通过）。
  2. 03-entity.md §7 L92-169 + 10-xml §5.4：与 2.4.0 相同的完整覆盖。
  3. description（L4-13）无枚举相关触发词，靠「实体类与表映射」泛化命中。
- 扣分主因：D1 缺枚举触发词；D6 同五处 + 路由提醒列第六处复述。

### Prompt T7（10 万导入：saveBatch 是否真批量 / 提速 / 要否事务）
- 拿到的技能：版本 2.4.0
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. SKILL.md description L15「批量插入 / 批量导入 / saveBatch 慢」+ 主动行为触发 L72——双入口命中。
  2. 04-crud.md §3（L25-57）：saveBatch 逐条 insert 真相、真正批量三法（BATCH executor + rewriteBatchedStatements / InsertBatchSomeColumn / foreach）、一级缓存、流式 ResultHandler；L37 增补「批量与事务的交互……见 11-transaction.md §4」指针。
  3. 11-transaction.md §4（L218-273）：事务内 saveBatch 代码、URL 参数 yml、`importHuge` 10 万+ 分事务示例（REQUIRES_NEW 每 1000 条）——「要在事务里吗」有分场景答案（长事务 Undo Log 膨胀提醒）。
- 扣分主因：D6——04 §3 与 11 §4 存在主题交叠（2.4.0 已加指针缓解）。

### Prompt T7（同场景）
- 拿到的技能：版本 2.3.1
- D1: 11  D2: 12  D3: 12  D4: 11  D5: 12  D6: 10  D7: 10  D8: 11  D9: 4
- 该 prompt 小计: 93/100
- 关键依据：
  1. description L6「批量插入」+ L11 `saveBatch` 令牌——可命中但无「saveBatch 慢」话术。
  2. 04-crud.md §3 L25-57、11-transaction §4 L218-273：内容与 2.4.0 一致。
  3. 11-transaction.md §4 头部（L220）仅一句「容易踩坑」，无指向 04 §3 批量机制全貌的指针（2.4.0 已补）。
- 扣分主因：D1 触发词弱一档；D7 缺 11→04 的批量交叉指针。

### Prompt T8（排错三连：Invalid bound statement / total=0 / @DS 跨库不回滚）
- 拿到的技能：版本 2.4.0
- D1: 12  D2: 11  D3: 11  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 93/100
- 关键依据：
  1. SKILL.md description L14/L17 直接含「Invalid bound statement (not found)」「分页失效 / total 为 0」「事务不回滚」三个报错原文——三连排错全部关键词级命中。
  2. 09-troubleshoot.md §2 表（L16-26）+ §3 分页失效五步清单（L28-34，jsqlparser 依赖/插件注册/DbType/Page 非 null）；10-xml.md §1（L5-17）mapper-locations 与 namespace 双排查路径。
  3. 11-transaction.md §6（L311-351）：@DS+@Transactional 单库事务限制、Connection 不随切换、Seata/XA/补偿三方案——「组合场景阅读顺序」块已删，但路由行 L113「事务管理（…多数据源…）」仍可达（rubric 盯的点通过）。
- 扣分主因：D6——Invalid bound statement 在 09 §2 与 10-xml §8 两张表重复；多子问题需跳 4 个文件（D2 轻微）。

### Prompt T8（同场景）
- 拿到的技能：版本 2.3.1
- D1: 9  D2: 12  D3: 11  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 91/100
- 关键依据：
  1. SKILL.md L107「组合场景阅读顺序」：含「事务+多数据源→先 11 后 02」「事务回滚排查→先 11 后 08」——对这类三连排错的导航最优。
  2. 09-troubleshoot §2/§3、10-xml §1/§8、11 §6：内容与 2.4.0 一致，覆盖完整。
  3. description（L4-15）：无「Invalid bound statement」「total 为 0」「事务不回滚」任一报错话术（仅 `selectPage` 令牌可部分命中第二个子问题）。
- 扣分主因：D1——报错式求助的描述层命中显著弱于 2.4.0。

### Prompt T9（对抗·DataPermissionInterceptor 按部门过滤，要完整配置代码）
- 拿到的技能：版本 2.4.0
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 97/100
- 关键依据：
  1. 07-plugin.md §4 L60-63：`MultiDataPermissionHandler.getSqlSegment(Table table, Expression where, String mappedStatementId)` 返回**单个 Expression**——与 MyBatis-Plus 3.5.x 真实签名一致（rubric 锚点）；L53-58 列出 net.sf.jsqlparser 正确 import 行（rubric 加分项）。
  2. L72-73：`new InExpression(new Column("dept_id"), new ExpressionList(deptIds...))` 用 jsqlparser AST 构造 `dept_id IN (...)`——可编译、防注入，正是 prompt 要的 handler 写法。
  3. SKILL.md description L16 含「数据权限」触发词；强约束 #10（L93）+ 07 §5 L92 插件顺序（数据权限在分页之前，COUNT 未改写→总数泄露越权）。
- 扣分主因：D6——§4 要点 + 反模式两轮陈述略有重叠（轻微）。

### Prompt T9（同场景）
- 拿到的技能：版本 2.3.1
- D1: 9  D2: 11  D3: 4  D4: 3  D5: 9  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 72/100
- 关键依据：
  1. 07-plugin.md §4 L55：`public List<DataPermissionRule> getSqlSegment(ExecutionStatement stmt)` ——**`ExecutionStatement` 与 `DataPermissionRule` 两个类在 MyBatis-Plus 中不存在**，且真实签名返回单个 `Expression` 而非 `List<>`、参数是 `(Table, Expression, String)`。agent 照写必编译失败 → 按 rubric D4 重扣。
  2. L62-69：`DataPermissionRule rule = new DataPermissionRule(); rule.setColumn(...); rule.setExpression(new InExpression(..., false))` ——虚构的 fluent API；`new InExpression(col, list, false)` 三参构造亦非真实签名。
  3. description（L4-13）无「数据权限/多租户」触发词；插件顺序（L74、L79）与白名单/注入告诫本身正确。
- 扣分主因：D4≤4（虚构类 + 错误签名，编译失败）；D3 重扣（给出的「完整配置代码」知识本体即错）；D1 缺触发词。

### Prompt T10（对抗·DynamicTableNameInnerInterceptor 按月分表 user_1~user_12）
- 拿到的技能：版本 2.4.0
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 10  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. 07-plugin.md §3 L42-44：`// TableNameHandler.dynamicTableName(String sql, String tableName) 是两参函数式接口` + `(sql, tableName) -> "user_" + LocalDate.now().getMonthValue()` ——**两参 lambda，与真实 API 一致**（rubric 锚点），getMonthValue() 恰好产出 1-12 对应 user_1~user_12。
  2. SKILL.md description L16 含「分表 / 动态表名」触发词；路由行 L107 指向 07-plugin。
  3. §5 L92：插件顺序链（动态表名在分页之前 + 原因说明），强约束 #10 交叉引用。
- 扣分主因：D5——§3 内「不做 SQL 改写的靠后」措辞含糊，顺序判据需到 §5 才完全清晰。

### Prompt T10（同场景）
- 拿到的技能：版本 2.3.1
- D1: 9  D2: 12  D3: 5  D4: 3  D5: 10  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 76/100
- 关键依据：
  1. 07-plugin.md §3 L43：`tableName -> "user_" + LocalDate.now().getMonthValue()` ——**单参 lambda**；`TableNameHandler.dynamicTableName(String sql, String tableName)` 是两参函数式接口，单参 lambda 无法通过编译 → rubric D4 重扣。
  2. L45 顺序提示与 §5（L88）顺序链本身正确。
  3. description（L4-13）无「分表/动态表名」触发词。
- 扣分主因：D4≤4（单参 lambda 编译失败，正是对抗集靶点）；D3 重扣（示例即错误写法）；D1 缺触发词。

### Prompt T11（对抗·SqlInjectionUtils.check 语义：会抛异常吗？apply 传外部输入正确写法）
- 拿到的技能：版本 2.4.0
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 95/100
- 关键依据：
  1. SKILL.md 强约束 #7（L90）：「`check(String)` 返回 boolean（true=疑似注入）且**自身不抛异常**——必须 `if (SqlInjectionUtils.check(x)) throw ...` 由调用方拦截，禁止裸调用（返回值被忽略＝校验形同虚设）」——对 prompt 两个问题（怎么用/会抛吗）给出**语义正确**的直接答案。
  2. 05-wrapper.md §5 L97-101：`if (SqlInjectionUtils.check(inputDate)) { throw new IllegalArgumentException(...); } w.apply("date_format(create_time,'%Y-%m-%d') = {0}", inputDate);` ——与 prompt 场景逐字对应（date_format apply + 外部输入），`{0}` 占位传原值。
  3. 08-antipattern.md #5（L25-28）与 06-page.md §5（L51-59，排序字段 `if (check) throw`）同口径一致。
- 扣分主因：D6——同一规则三处（SKILL #7 / 05 §5 / 08 #5）复述。

### Prompt T11（同场景）
- 拿到的技能：版本 2.3.1
- D1: 10  D2: 12  D3: 4  D4: 4  D5: 4  D6: 10  D7: 11  D8: 11  D9: 2
- 该 prompt 小计: 68/100
- 关键依据：
  1. 05-wrapper.md §5 L98-99：`SqlInjectionUtils.check(inputDate); w.apply(...)` ——**裸调用，返回值被忽略，校验形同虚设**；L101 注释「check 返回 boolean（true=检测到注入并抛异常）」——**check 实际只返回 boolean、不抛异常**（rubric 锚点：安全语义错误）→ D3/D4/D5 重扣。
  2. SKILL.md 强约束 #7（L83）：「check 返回 boolean 并抛异常，不返回安全值」——同样的错误语义写进强约束，agent 会据此向用户回答「会抛异常」（错）。
  3. 自相矛盾：06-page.md §5 L56-58 用 `if (SqlInjectionUtils.check(sortField)) { throw ... }`（暗示 check 不抛、需调用方拦），与 05 §5/强约束 #7 的「check 自己抛」口径冲突 → D9 扣。
- 扣分主因：D3/D4/D5 均 ≤4——错误语义 + 无效校验模式直接命中对抗靶心；D9 跨文件口径冲突。

### Prompt T12（对抗·3.4.2 升 3.5.x：breaking change + 升级步骤）
- 拿到的技能：版本 2.4.0
- D1: 11  D2: 12  D3: 11  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 92/100
- 关键依据：
  1. 13-migration.md §2 表（L13-19）：四条 breaking change——分页拦截器重构 / jsqlparser 拆依赖 / `IGNORED`→`ALWAYS` / SQL 注入器重构——**全部对应真实存在的类与配置**，无虚构条目。
  2. §3 升级步骤（L42-49）六步全部真实可执行；§1 L8「**不要**在 3.4.x 引 mybatis-plus-jsqlparser（3.5.9 才拆分）」——rubric 要求的提醒在。
  3. SKILL.md 路由 L109 直达；§2.1 新旧 Bean 代码可编译。
- 扣分主因：D6——IGNORED/jsqlparser 信息与 02 §7、01-start 交叠（有指针）。

### Prompt T12（同场景）
- 拿到的技能：版本 2.3.1
- D1: 11  D2: 12  D3: 5  D4: 4  D5: 11  D6: 9  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 78/100
- 关键依据：
  1. 13-migration.md §2 表 L17：breaking change #3「`Page.MybatisPlusLang` 移除（3.5.0，无 @Deprecated 过渡）」——**MyBatis-Plus 从无 `Page.MybatisPlusLang` 类**，虚构 breaking change（rubric 靶点）→ D3/D4 重扣。
  2. §2.2（L39-49）：为该虚构类给出前后代码示例；§3 步骤 5（L61）「删除所有 Page.MybatisPlusLang.* 调用」——误导用户在 3.4.x 代码库排查不存在的符号。
  3. 真实变更（#1/#2/#4/#5 与步骤 1-4/6/7、3.4.x 勿引 jsqlparser 提醒 L8）本身正确完整。
- 扣分主因：D3/D4——breaking change 表混入一条虚构项，整份升级清单的可信度受损；D6——「版本注意」节（SKILL L126-129）与本章重复。

### Prompt T13（对抗·迁 Oracle：分页 / 主键 AUTO / desc 保留字自动转义？）
- 拿到的技能：版本 2.4.0
- D1: 10  D2: 12  D3: 12  D4: 11  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 94/100
- 关键依据：
  1. 12-dbtype.md §4 L45：「保留字列名**无自动转义**——MP 不会按 DbType 自动包裹关键字，引用符必须手写」+ `@TableField("\"desc\"")` 式写法——对「MP 会自动转义吗」给出**正确**否定答案（rubric 锚点）。
  2. §2 L20-24：`PaginationInnerInterceptor(DbType.ORACLE)` 显式指定；§3 L28-40：Oracle 无自增列 → `INPUT`+`@KeySequence` 或 `ASSIGN_ID`，AUTO 报错警告——三问全覆盖。
  3. §1 表 L9-14：Oracle ROWNUM 分页方言 / 引用符 `"col"` / 逻辑删除函数 / INSERT ALL 批量；§6 反模式四条。
- 扣分主因：D1——description 无 Oracle/DbType 触发词（两版同弱）；D4 轻微（@KeySequence 示例完整但需与 03 §2 拼装主键结论）。

### Prompt T13（同场景）
- 拿到的技能：版本 2.3.1
- D1: 10  D2: 12  D3: 9  D4: 11  D5: 5  D6: 11  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 84/100
- 关键依据：
  1. 12-dbtype.md §4 L45：「MP 的 DbType 内置 `keywordFit` 关键字转义，但仅覆盖已知关键字；自定义保留字列名仍需手写引用符」——**DbType 枚举无 keywordFit 能力**，虚构（rubric 锚点：D5 扣分）；对用户「MP 会自动转义吗」会给出「部分会」的错误答案。
  2. §2/§3 的 DbType.ORACLE 显式指定、`INPUT`+`@KeySequence`、AUTO 报错警告与 2.4.0 相同（正确）。
  3. 路由「关键提醒」L100「非 MySQL 必须显式 DbType；Oracle/PG 勿用 AUTO 主键」——SKILL.md 层判据可达。
- 扣分主因：D5 重扣（虚构自动转义能力，恰是本 prompt 第三问的陷阱）；D3 连带（保留字知识点半错）。

### Prompt T14（对抗·只读 SKILL.md 的分页链路：依赖/插件/自定义 XML 分页/触发词）
- 拿到的技能：版本 2.4.0
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 96/100
- 关键依据：
  1. SKILL.md L43：①`mybatis-plus-jsqlparser`（v3.5.9+ 拆分、**不引则分页静默失效**、JDK8 用 -4.9）——「版本与依赖」节直接命中；强约束 #6（L89）：②`MybatisPlusInterceptor` + `PaginationInnerInterceptor(DbType.MYSQL)` 完整代码 + **最后添加** + 非 MySQL 显式 DbType。
  2. 强约束 #12（L95）：③「自定义 XML 分页：Mapper 方法返回 IPage（返回 List 则 MP 不改写分页）、入参 page 非 null（MP 靠它追加 LIMIT/COUNT）、ORDER BY 写在 XML」——签名硬性要求在强约束正文；自检清单 L131 第 10 项复现。
  3. description L14：「分页失效 / total 为 0 / 返回全量」触发词原文——④报错式求助关键词级命中。
- 扣分主因：D6——jsqlparser 规则在版本依赖节/主动触发/自检清单三处短复述（操作性内容，扣分轻微）。

### Prompt T14（同场景）
- 拿到的技能：版本 2.3.1
- D1: 8  D2: 11  D3: 11  D4: 11  D5: 11  D6: 9  D7: 11  D8: 11  D9: 4
- 该 prompt 小计: 87/100
- 关键依据：
  1. SKILL.md L36：①jsqlparser 依赖与静默失效——与 2.4.0 同等可达；强约束 #6（L82）：②插件配置+顺序同等可达。
  2. ③自定义 XML 分页：无对应强约束，仅路由「关键提醒」L98「IPage 非 null 非 List；ORDER BY 写 XML」——SKILL.md 本体可达但降格为表格附注，且自检清单（L115-124，9 项）无此条。
  3. description（L4-15）：无「分页失效 / total 为 0」类触发词——④该类求助在描述层不命中（rubric D1 判分点未过）。
- 扣分主因：D1（④触发词缺失，直接判分点失败）；D6——「版本注意」节（L126-129）重复版本依赖信息增加 SKILL.md 体量；③判据仅存于路由附注。

---

## 2. 总分表

| Prompt | 2.4.0（versionA） | 2.3.1（versionB） | 差值 |
|---|---|---|---|
| T1 starter 选择 | 92 | 91 | +1 |
| T2 null 不更新 | 93 | 90 | +3 |
| T3 Wrapper 超界 | 91 | 90 | +1 |
| T4 逻辑删除 | 95 | 95 | 0 |
| T5 事务失效 | 95 | 93 | +2 |
| T6 枚举映射 | 94 | 92 | +2 |
| T7 批量性能 | 95 | 93 | +2 |
| T8 排错三连 | 93 | 91 | +2 |
| T9 数据权限（对抗） | 97 | 72 | +25 |
| T10 动态表名（对抗） | 95 | 76 | +19 |
| T11 防注入语义（对抗） | 95 | 68 | +27 |
| T12 3.4→3.5 升级（对抗） | 92 | 78 | +14 |
| T13 Oracle 适配（对抗） | 94 | 84 | +10 |
| T14 只读 SKILL 分页链路（对抗） | 96 | 87 | +9 |
| **回归集小计（T1-T8）** | **748** | **735** | +13 |
| **对抗集小计（T9-T14）** | **569** | **465** | +104 |
| **总分** | **1317** | **1200** | **+117** |

（每条满分 100；回归集满分 800、对抗集满分 600。）

## 3. 一句话方向判断

按字面值：2.4.0 总分 1317 明显优于 2.3.1 的 1200——差距几乎全部来自对抗集（+104）：2.3.1 在数据权限 handler（虚构 `ExecutionStatement`/`DataPermissionRule`）、动态表名（单参 lambda）、`SqlInjectionUtils.check` 语义（误称抛异常 + 裸调用示例，且与 06-page 口径自相矛盾）、迁移表（虚构 `Page.MybatisPlusLang`）、DbType 保留字（虚构 `keywordFit`）五处会产出编译失败或语义错误的建议，2.4.0 对应位置全部为真实 API 与正确语义；回归集两版基本持平（748 vs 735），2.4.0 的小幅优势来自 description 报错触发词（事务不回滚 / total 为 0 / Invalid bound statement 等）与冗余修剪（「版本注意」节、路由提醒列、eval 元指针），未发现修剪导致的判据丢失（强约束 #4/#5/#12 均承接）。
