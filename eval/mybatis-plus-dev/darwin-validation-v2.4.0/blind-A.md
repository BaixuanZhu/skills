# 盲评报告 A（mybatis-plus-dev，v2.4.0 达尔文验证）

## 方法自证

两份 SKILL.md frontmatter 的 `version:` 字面值（原样照抄）：

- snapshots/version1/SKILL.md → `version: 2.3.1`
- snapshots/version2/SKILL.md → `version: 2.4.0`

本报告按版本字面值称呼两版（「2.3.1」= snapshots/version1，「2.4.0」= snapshots/version2），不知道、也不猜测哪个是旧/新；版本号仅作标识，不影响打分。已全文读取两版各 14 个文件（SKILL.md + 13 个 references），并逐文件做了内容比对（02-config / 06-page / 09-troubleshoot / 10-xml 两版完全一致；04-crud / 08-antipattern / 11-transaction 仅指针级微调；实质差异集中在 SKILL.md、01-start、05-wrapper §5、07-plugin §3/§4、12-dbtype §4、13-migration）。

---

## 回归集（T1-T8）

### Prompt T1（SB2.7 / SB3.4 / JDK8 三个项目引依赖 + 分页额外依赖）

**版本 2.3.1**
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 小计: 96/100
- 依据：
  1. SKILL.md L29-36「版本与依赖」表给出 SB2/3/4 三套 artifactId + 分页必引 jsqlparser（JDK8 用 `-4.9`）；01-start.md L9-50 三个完整依赖块 + JDK11/JDK8 双 jsqlparser 块，全部真实坐标。
  2. 01-start.md L7 / L51：勿引 mybatis-spring 冲突警告、不引 jsqlparser「静默失效无报错」——两个隐蔽坑都点名。
  3. 冗余：01-start.md L10-34 三段几乎相同的 XML 块 + SKILL.md L36 与 L128-129「版本注意」三处重复 jsqlparser 提醒 → D6 扣。
- 扣分主因：依赖块三重复述（D6）。

**版本 2.4.0**
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 97/100
- 依据：
  1. 01-start.md L9-27 只留 SB3 一个完整块，但 L17 一行内联给出 SB2/SB4 的 artifactId（`mybatis-plus-boot-starter` / `mybatis-plus-spring-boot4-starter`），L27 注明 JDK8 改用 `mybatis-plus-jsqlparser-4.9`——修剪后仍零跳转可达，无退步。
  2. SKILL.md L42-43 保留冲突警告 + 静默失效警告；L40 表含 SB4 需 ≥3.5.13。
  3. D7 略降：决策路由表（L99-113）删掉「关键提醒」列，路由行不再内联「SB3 用 spring-boot3-starter」提醒，需回看「版本与依赖」节。
- 扣分主因：路由表内联提醒丢失（D7）。

### Prompt T2（updateById 置 null 失败 + 全局 update-strategy 能不能改）

**版本 2.3.1**
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 小计: 95/100
- 依据：
  1. 02-config.md §7（L110-170，两版一致）完整回答三连问：FieldStrategy 表、根因 NOT_NULL、常见误区「全局改 ALWAYS 误清数据，只允许字段级覆盖」。
  2. 置 null 代码出现在 03-entity.md §4 L65-70 与 05-wrapper.md §2 L46-49 **两处全文重复** → D6 扣；08-antipattern #2 仅指针，合规。
  3. D1 扣：description 无「更新后字段没变 / 置 null 不生效」症状词，仅靠 CRUD 泛场景触发。
- 扣分主因：set-null 代码跨文件重复（D6）、description 缺症状触发词（D1）。

**版本 2.4.0**
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 98/100
- 依据：
  1. SKILL.md frontmatter L15「更新后字段没变 / 字段置 null 不生效」症状词直接命中本 prompt（D1 满分）。
  2. 03-entity.md §4 删掉重复代码块，改指针「代码示例见 05-wrapper.md §2」（L62），去重成功；SKILL.md #4（L87）新增「全局改 update-strategy: ALWAYS 会让所有 null 字段写库误清数据——只允许字段级覆盖」，强约束层即可答第三问。
  3. D7 略降：路由表删「字段策略全局改 ALWAYS 会误清数据」提醒（2.3.1 版 L94 有），但 SKILL #4 承接。
- 扣分主因：路由表内联提醒丢失（D7）。

### Prompt T3（ROW_NUMBER 窗口 + GROUP BY COUNT 用 apply/last 拼 Wrapper）

**版本 2.3.1**
- D1: 11  D2: 12  D3: 10  D4: 10  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 小计: 92/100
- 依据：
  1. SKILL.md #3（L72-79）与 05-wrapper.md §1.2（L19-39）逐条列出窗口函数 / 聚合+GROUP BY 必须转 XML，05-wrapper L32-34 的 ✗ 示例与用户写法一字不差——直接判「不可以」。
  2. 08-antipattern #25（L118-125）补齐「为什么」（注入 + 跨库 + 聚合需专用 resultMap）。
  3. 覆盖缺口（两版同）：10-xml.md 只有通用 XML 范式，没有窗口函数/聚合查询的具体 XML 正面示例（如 ROW_NUMBER 子查询套外层、GROUP BY + resultMap 映射计算列），agent 需自行组装 → D3/D4 各扣 2。
- 扣分主因：缺正面 XML 改写示例（D3/D4）；SKILL #3 与 05-wrapper §1.2 同一清单双写（D6）。

**版本 2.4.0**
- D1: 11  D2: 12  D3: 10  D4: 10  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 91/100
- 依据：
  1. 与 2.3.1 相同：05-wrapper §1.2、10-xml、08-antipattern #25 三处内容两版一致，判据完整。
  2. D7 略降：路由行（L105）删「SQL 函数表达式转 XML，勿用 apply 拼」提醒（2.3.1 版 L97 有），需靠 SKILL #3 兜底——仍可达。
  3. 同样缺正面 XML 示例（D3/D4 同扣）。
- 扣分主因：同 2.3.1 的覆盖缺口 + 路由提醒丢失。

### Prompt T4（逻辑删除全局配置 + 0/1 方案 + 唯一索引冲突）

**版本 2.3.1**
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 11  D9: 4
- 小计: 98/100
- 依据：
  1. 02-config.md §2（L36-65，两版一致）：0+毫秒时间戳推荐方案 + yaml + 方言表 + 备选（LocalDateTime+null）——三连问全覆盖。
  2. 08-antipattern #6（L30-33）专答唯一索引冲突（UNIQUE(username, deleted)，时间戳天然去重）。
  3. 路由行 L94 提醒「逻辑删除推荐 0+时间戳；唯一索引含 deleted」内联直达（D7 满分）。
- 扣分主因：仅 02-config §2 篇幅略长（D6 微扣）。

**版本 2.4.0**
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 97/100
- 依据：
  1. description L16 含「逻辑删除 / 软删除」触发词（2.3.1 的 scope 行也有「逻辑删除」，同分）。
  2. SKILL.md #5（L88）把「唯一索引须含 deleted，否则同值插入报 Duplicate」并入强约束——即使不进 02-config 也可答（对冲了提醒列删除）。
  3. D7 略降：路由行 L102 删「逻辑删除推荐 0+时间戳；唯一索引含 deleted」提醒。
- 扣分主因：路由表内联提醒丢失（D7）。

### Prompt T5（事务不回滚：try-catch 吞异常 + this 自调用 + rollbackFor）

**版本 2.3.1**
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 11  D9: 4
- 小计: 96/100
- 依据：
  1. 11-transaction.md §3（L94-216，两版一致）「7 大失效场景」逐一命中：场景1 自调用（@Lazy 自注入/AopContext/拆 Service 三方案）、场景3 catch 吞异常（rethrow 或 setRollbackOnly）、场景5 rollbackFor 缺失。
  2. 08-antipattern #18/#19/#20（L83-96）三连反例与用户场景一一对应。
  3. 路由行 L105 提醒「rollbackFor 必须显式；自调用不走代理」直接命中（D7 满分）；D1 扣：description 无「事务不回滚」症状词。
- 扣分主因：description 缺症状触发词（D1）。

**版本 2.4.0**
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 97/100
- 依据：
  1. description L17「事务不回滚」症状词精确命中（D1 满分）。
  2. 11-transaction.md 全文与 2.3.1 一致（仅 L220 加了指回 04-crud §3 的指针），内容无退步。
  3. D7 略降：路由行 L113 删「rollbackFor 必须显式；自调用不走代理」提醒（主动行为触发节仍有 rollbackFor 一条，部分对冲）。
- 扣分主因：路由表内联提醒丢失（D7）。

### Prompt T6（gender 枚举 1/2，前端收数字，BaseMapper + XML 双场景）

**版本 2.3.1**
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 小计: 95/100
- 依据：
  1. 03-entity.md §7（L92-169，两版一致）：@EnumValue+@JsonValue 完整枚举、IEnum 方式、XML 每处 typeHandler、常见坑含「前端收到 MALE 而非 1」（L167）正中用户第三问。
  2. SKILL.md #9（L85）+ 路由行 L95 提醒「枚举 @EnumValue+@JsonValue；XML 每处 typeHandler」双保险。
  3. D1 扣：description 无「枚举」相关词（@EnumValue 也不在 frontmatter），靠实体映射泛场景触发；D6 扣：「每处声明 typeHandler」规则在 SKILL #9 / 03-entity §7 / 10-xml §5.4 / 08 #17 四处重述。
- 扣分主因：description 缺枚举触发词（D1）、typeHandler 规则四处重复（D6）。

**版本 2.4.0**
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 依据：
  1. description L16「枚举存数据库」触发词直接命中（D1 满分）。
  2. rubric 特别盯的回归点验证通过：路由表虽删「枚举 @EnumValue+@JsonValue；XML 每处 typeHandler」提醒，但 SKILL.md #9（L92）全文保留该判据 + 路由行 L103 场景列仍含「**枚举映射(@EnumValue/IEnum/@JsonValue)**」加粗关键词 + 03-entity §7 完整——两处以上可达，无盲点。
  3. D7 略降：路由行提醒列删除（靠 #9 与场景列关键词补偿）。
- 扣分主因：路由表内联提醒丢失（D7）；typeHandler 规则多处重复与 2.3.1 同（D6）。

### Prompt T7（10 万导入，saveBatch 是不是真批量，怎么提速，要不要事务）

**版本 2.3.1**
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 11  D9: 4
- 小计: 97/100
- 依据：
  1. 04-crud.md §3（L25-57）：saveBatch 逐条真相 + 真批量三法（BATCH executor / InsertBatchSomeColumn / foreach）+ rewriteBatchedStatements。
  2. 11-transaction.md §4（L248-274）：10万+ 分事务示例（REQUIRES_NEW importBatch + 代理自调用）正面回答「要不要事务」。
  3. 「组合场景阅读顺序」（SKILL.md L107）「批量+事务→先 04 后 11」正中本组合 prompt（D7 满分）；D6 扣：04-crud §3 与 11-transaction §4 对 saveBatch+事务+rewrite 的机制各讲一遍，交叉重复。
- 扣分主因：批量+事务机制双文件重复（D6）。

**版本 2.4.0**
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 97/100
- 依据：
  1. description L15-16「批量插入 / 批量导入 / saveBatch 慢」症状词命中（D1 满分；2.3.1 也有 saveBatch token，同分）。
  2. 04-crud.md L37 新增指针「批量与事务的交互见 11-transaction.md §4」、11-transaction L220 反向指针「批量机制全貌见 04-crud.md §3」——交叉重复被显式指针替代（D6 +1）。
  3. D7 略降：「组合场景阅读顺序」块删除（SKILL.md 无「批量+事务」组合指引），靠 04-crud 行内指针补偿。
- 扣分主因：组合阅读顺序块删除（D7）。

### Prompt T8（排错三连：Invalid bound statement / total=0 / @DS 跨库回滚）

**版本 2.3.1**
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 11  D9: 4
- 小计: 96/100
- 依据：
  1. 09-troubleshoot.md §2 表（L20-26，两版一致）：Invalid bound statement → @MapperScan/namespace；total=0 → 02-config §1 + 06-page §2；§3 五步分页排查清单。
  2. 11-transaction.md §6（L311-351）：@DS+@Transactional 单库限制 + Seata/补偿方案，正中第三问。
  3. 「组合场景阅读顺序」L107「事务+多数据源→先 11 后 02」直接给出本组合的阅读路径（D7 满分）；路由行 L105 提醒「多数据源单 @Transactional 限单库」。D1 扣：description 无「Invalid bound statement / total 为 0」报错词。
- 扣分主因：description 缺报错串触发词（D1）。

**版本 2.4.0**
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 97/100
- 依据：
  1. description L14-17「分页失效 / total 为 0 / 返回全量」「Invalid bound statement (not found)」两个报错串逐字命中（D1 满分）。
  2. rubric 特别盯的回归点验证通过：「组合场景阅读顺序」块已删，但路由行 L113 场景列仍含「多数据源」字样，11-transaction §6 完整——两跳内可达，无盲点。
  3. D7 略降：路由行删「多数据源单 @Transactional 限单库」提醒 + 组合阅读顺序块删除。
- 扣分主因：组合阅读顺序与路由提醒均删（D7）。

---

## 对抗集（T9-T14）

### Prompt T9（DataPermissionInterceptor 按部门过滤，完整配置代码）

**版本 2.3.1**
- D1: 9  D2: 12  D3: 5  D4: 3  D5: 8  D6: 10  D7: 11  D8: 11  D9: 3
- 小计: 72/100
- 依据：
  1. **07-plugin.md §4 L52-71 使用虚构 API**：`public List<DataPermissionRule> getSqlSegment(ExecutionStatement stmt)`——`ExecutionStatement`、`DataPermissionRule` 两类不存在，且 `MultiDataPermissionHandler.getSqlSegment` 真实签名是 `(Table table, Expression where, String mappedStatementId)` 返回**单个 Expression**。agent 照抄必然编译失败 → 按 rubric D4 重扣（3 分）。
  2. 反模式行 L78 同样引用虚构的「用 `DataPermissionRule` + InExpression 参数化构造」；插件顺序、可信来源、防自过滤三条概念性建议本身正确（D5 部分保留）。
  3. description 无「数据权限」触发词（D1 扣）；正确 API 全套缺失（D3 重扣）。
- 扣分主因：handler 签名与两个类均虚构，示例不可编译（D4/D3 重扣）。

**版本 2.4.0**
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 依据：
  1. 07-plugin.md §4 L53-76：签名 `public Expression getSqlSegment(Table table, Expression where, String mappedStatementId)` 与 3.5.x 真实 API 一致；返回 null 表示该表不追加；`new DataPermissionInterceptor(new MultiDataPermissionHandler(){...})` 配置完整。
  2. L53-58 含正确 import 行（net.sf.jsqlparser 的 Expression/LongValue/ExpressionList/InExpression/Column/Table）→ 按 rubric D4 加分；deptIds 用 `InExpression + ExpressionList + LongValue` AST 构造，与官方示例同型。
  3. description L16「多租户 / 数据权限 / 分表 / 动态表名」触发词命中（D1 满分）。
- 扣分主因：仅路由提醒列删除的通病（D7）；§4 代码块略长（D6 微扣）。

### Prompt T10（DynamicTableNameInnerInterceptor 按月分表配置）

**版本 2.3.1**
- D1: 9  D2: 12  D3: 6  D4: 3  D5: 8  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 75/100
- 依据：
  1. 07-plugin.md §3 L43：`tableName -> "user_" + LocalDate.now().getMonthValue()` ——**单参 lambda**。`TableNameHandler.dynamicTableName(String sql, String tableName)` 是两参函数式接口，单参写法无法通过编译 → 按 rubric D4 重扣（3 分）。
  2. 「用于分表路由」的定位与插件顺序提醒正确（D3/D5 部分保留），但核心 handler 写法错误。
  3. description 无「分表 / 动态表名」触发词（D1 扣）。
- 扣分主因：单参 lambda 编译失败（D4 重扣）。

**版本 2.4.0**
- D1: 12  D2: 12  D3: 11  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 95/100
- 依据：
  1. 07-plugin.md §3 L42-44：`(sql, tableName) -> "user_" + LocalDate.now().getMonthValue()` 两参写法 + L42 注释明示「TableNameHandler.dynamicTableName(String sql, String tableName) 是两参函数式接口」——正中 rubric 锚点（D4 满分）。
  2. description L16「分表 / 动态表名」触发词命中（D1 满分）。
  3. D5 微扣：仅一句顺序提醒（与多租户同用关注顺序），未展开动态表名自身的隐蔽坑（如 handler 返回原表名与否的语义）。
- 扣分主因：§3 仅 3 行，陷阱覆盖薄（D5 微扣）。

### Prompt T11（SqlInjectionUtils.check 怎么用、会不会抛异常、apply 正确写法）

**版本 2.3.1**
- D1: 10  D2: 12  D3: 4  D4: 4  D5: 3  D6: 11  D7: 12  D8: 11  D9: 2
- 小计: 69/100
- 依据：
  1. **语义错误三连**：SKILL.md #7 L83「`check` 返回 boolean 并抛异常」；05-wrapper.md §5 L98 **裸调用** `SqlInjectionUtils.check(inputDate);`（返回值被忽略，校验形同虚设）+ L101「true=检测到注入并抛异常」；08-antipattern #5 L27 同样裸调用。真实语义是 `check(String)` 只返回 boolean、**自身不抛异常**——用户问「会抛异常吗」，本版主导答案恰好答反 → 按 rubric D3/D5 重扣。
  2. **内部自相矛盾**：06-page.md §5 L56-58 却是正确的 `if (SqlInjectionUtils.check(sortField)) throw ...` 写法——同一技能两套互斥口径（D9 重扣至 2）。
  3. 唯一正确面：`{0}` 占位传原值的写法两个版本都正确。
- 扣分主因：check 抛异常的错误语义 + 裸调用示例（D3/D4/D5 重扣）、与 06-page 自相矛盾（D9）。

**版本 2.4.0**
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 依据：
  1. SKILL.md #7 L90：`check(String)` 返回 boolean（true=疑似注入）且**自身不抛异常**——必须 `if (check(x)) throw` 由调用方拦截，**禁止裸调用**——语义完全正确且点名隐蔽坑（D5 满分）。
  2. 05-wrapper.md §5 L97-100 改为 if-throw 完整示例；08-antipattern #5 L27 同步修正——三处口径统一（D9 满分），06-page §5 原本正确保持不动。
  3. `{0}` 占位 + 排序字段场景（06-page §5）均覆盖。
- 扣分主因：仅路由提醒列删除的通病（D7）。

### Prompt T12（3.4.2 升 3.5.x，breaking change + 升级步骤清单）

**版本 2.3.1**
- D1: 10  D2: 12  D3: 5  D4: 4  D5: 10  D6: 10  D7: 12  D8: 11  D9: 3
- 小计: 77/100
- 依据：
  1. **虚构 breaking change**：13-migration.md L17 表 #3「`Page.MybatisPlusLang` 移除」——该项目从无此类；L39-49 §2.2 还配了完整示例代码，L61 升级清单第 5 步要求「删除所有 `Page.MybatisPlusLang.*` 调用」。agent 照此输出会教用户排查一个不存在的类 → 按 rubric D3/D4 重扣。
  2. 真实变更均正确：`PaginationInterceptor`→`MybatisPlusInterceptor`（§2.1）、3.5.9+ 引 jsqlparser、`IGNORED`→`ALWAYS`；3.4.x 勿引 jsqlparser 提醒在 §1 L8 + SKILL.md L129 双处（D5 保留）。
  3. §2.2 整节围绕虚构类展开，纯废段（D6 扣）。
- 扣分主因：虚构 `Page.MybatisPlusLang` 进入 breaking 表、示例与升级清单三处（D3/D4 重扣）。

**版本 2.4.0**
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 94/100
- 依据：
  1. 13-migration.md L17-18：虚构条目整体删除，表重编号为 4 条（分页重构 / 拆依赖 / IGNORED / 注入器），全部对应真实类与配置。
  2. 升级清单 6 步（L44-49）全部真实可执行：统一 3.5.x（≥3.5.9）、替换拦截器、补 jsqlparser、IGNORED→ALWAYS、注入器、`mvn dependency:tree` 清残留。
  3. L8「不要在 3.4.x 引 `mybatis-plus-jsqlparser`（3.5.9 才拆分）」保留（rubric 要求项）。
- 扣分主因：description 无迁移/升级触发词（D1）、路由提醒列删除（D7）。

### Prompt T13（MySQL 迁 Oracle：分页 / 主键 / desc 保留字自动转义？）

**版本 2.3.1**
- D1: 10  D2: 12  D3: 8  D4: 11  D5: 5  D6: 11  D7: 12  D8: 11  D9: 3
- 小计: 83/100
- 依据：
  1. **虚构能力**：12-dbtype.md L45「MP 的 `DbType` 内置 `keywordFit` 关键字转义，但仅覆盖已知关键字」——DbType 枚举无此方法。用户问「desc 保留字 MP 会自动转义吗」，`desc` 恰是已知关键字，本版答案会变成「会（keywordFit 兜底）」→ 答反 → 按 rubric D5 扣。
  2. L44「需按库用引用符包裹 `@TableField("\"desc\"")`」与 L45 自动转义声明**同节自相矛盾**（手写必须 vs 自动兜底）（D9 扣）。
  3. 正确部分：§2 强制显式 `DbType.ORACLE`、§3 `INPUT`+`@KeySequence` / `ASSIGN_ID`（AUTO 不适用警告 L40）、§6 反模式——分页与主键两问答对。
- 扣分主因：`keywordFit` 虚构且直接答错第三问（D5/D3 扣）、节内口径矛盾（D9）。

**版本 2.4.0**
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 依据：
  1. 12-dbtype.md L45 修正为「保留字列名**无自动转义**——MP 不会按 `DbType` 自动包裹关键字，引用符必须手写」——正中用户第三问且语义正确。
  2. §2/§3/§6 与 2.3.1 相同的正确内容（显式 DbType、@KeySequence、反模式表），三问全对。
  3. D7 略降：路由行删「非 MySQL 必须显式 DbType；Oracle/PG 勿用 AUTO 主键」提醒（SKILL #6 仍兜底）。
- 扣分主因：description 无 Oracle/跨库触发词（D1）、路由提醒删除（D7）。

### Prompt T14（只读 SKILL.md：分页依赖 / 插件顺序 / 自定义 XML 分页签名 / description 触发词）

**版本 2.3.1**
- D1: 9  D2: 10  D3: 11  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 89/100
- 依据：
  1. ①③②可达性：① jsqlparser（SKILL.md L36「分页必引…否则分页静默失效」）✓；② 强约束 #6（L82）含 `MybatisPlusInterceptor…最后` + 显式 DbType ✓；③ **仅藏在路由表 L98「关键提醒」列**（「IPage 非 null 非 List；ORDER BY 写 XML」）——既不在强约束也不在 9 项自检清单，只读 SKILL.md 的 agent 若只扫约束+清单会漏（D2 扣）。
  2. ④ description 有「分页查询 / pagination / selectPage」泛触发词，但无「分页失效 / total 为 0」症状词 → 该类求助命中不稳（D1 扣）。
  3. D6 扣：「版本注意」L126-129 与 L36 重复 jsqlparser 信息第三遍；「组合场景阅读顺序」L107 对本单一场景是噪音。
- 扣分主因：③ 仅存在于关键提醒列（D2）、description 缺症状词（D1）。

**版本 2.4.0**
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 11  D9: 4
- 小计: 98/100
- 依据：
  1. 三要素全在 SKILL.md 显著位置：① L43 分页必引 jsqlparser + 静默失效；② 强约束 #6（L89）；③ **新增强约束 #12**（L95「返回 `IPage`（返回 `List` 则 MP 不改写分页）、入参 `page` 非 null、`ORDER BY` 写在 XML」）+ 自检清单第 10 项（L131）双保险——修剪（删提醒列）被 #12 完全承接。
  2. ④ description L14「分页失效 / total 为 0 / 返回全量」逐字可命中（D1 满分）。
  3. 版本号集中化后「版本注意」节删除，SKILL.md 内不再有 jsqlparser 三重复述（D6 改善）。
- 扣分主因：仅 description 较长（D6 微扣）。

---

## 总分表

| Prompt | 2.3.1 | 2.4.0 | Δ |
|---|---|---|---|
| T1 starter 选择 | 96 | 97 | +1 |
| T2 null 不更新 | 95 | 98 | +3 |
| T3 Wrapper 超界 | 92 | 91 | -1 |
| T4 逻辑删除 | 98 | 97 | -1 |
| T5 事务失效 | 96 | 97 | +1 |
| T6 枚举映射 | 95 | 96 | +1 |
| T7 批量插入 | 97 | 97 | 0 |
| T8 排错三连 | 96 | 97 | +1 |
| **回归集小计** | **765** | **770** | **+5** |
| T9 数据权限 | 72 | 96 | +24 |
| T10 动态表名 | 75 | 95 | +20 |
| T11 防注入语义 | 69 | 96 | +27 |
| T12 3.4→3.5 升级 | 77 | 94 | +17 |
| T13 Oracle 适配 | 83 | 93 | +10 |
| T14 只读 SKILL 分页链路 | 89 | 98 | +9 |
| **对抗集小计** | **465** | **572** | **+107** |
| **总分（14×100）** | **1230** | **1342** | **+112** |

## 方向判断（一句话）

2.4.0 全面优于 2.3.1（1342 vs 1230）：对抗集 +107 来自五处真实 API/语义修正（MultiDataPermissionHandler 签名、两参 TableNameHandler、SqlInjectionUtils.check 不抛异常、删除虚构的 Page.MybatisPlusLang、删除虚构的 DbType.keywordFit），而回归集仅 -1~0 的 D7 微损（关键提醒列与组合阅读顺序删除被强约束 #4/#5/#12 与 description 症状词扩张完全对冲，净 +5）——修剪无退步，修正全是净收益。
