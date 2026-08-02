# Agent 常见错误与最佳实践（核心价值）

> 每条结构：**错误写法 → 正确写法 → 为什么**。AI 生成 MyBatis-Plus 代码前应主动核对本章，避免“能跑但有坑”。

## 1. 分页失效（最隐蔽）
- ❌ 引 `mybatis-plus-boot-starter` 后直接 `selectPage`，未引 `mybatis-plus-jsqlparser`，也未注册 `PaginationInnerInterceptor`。
- ✅ 引 `mybatis-plus-jsqlparser` + 注册 `MybatisPlusInterceptor`（分页插件最后添加，见 `02-config.md` §1）。
- 为什么：v3.5.9+ 分页插件已拆分；未配置时 `selectPage` 静默返回全量、`total` 错误且无异常。

## 2. null 字段不更新
- ❌ `userMapper.updateById(new User().setId(1L).setAge(null))` 想清空 age，结果 age 不变。
- ✅ 用 `UpdateWrapper.set(User::getAge, null)`（见 `04-crud.md` §4）。
- 为什么：默认字段策略 `NOT_NULL`，null 不参与 UPDATE。

## 3. selectObjs 误用
- ❌ `selectObjs(wrapper)` 后当 `User` 对象用。
- ✅ 取整行用 `selectList`，取单列用 `selectObjs`（仅返回首列 `Object`）。
- 为什么：`selectObjs` 仅返回每行**第一列**。

## 4. saveBatch 当真批量
- ❌ 以为 `saveBatch` 是 JDBC 批量，性能达标。
- ✅ 默认分批逐条 insert；真正批量需 `rewriteBatchedStatements=true` + 批处理 SqlSession，或 `InsertBatchSomeColumn`（见 `04-crud.md` §3）。
- 为什么：默认实现并非 BATCH executor，网络往返未减少。

## 5. apply 字符串拼接注入
- ❌ `w.apply("create_time >= '" + userInput + "'")`。
- ✅ `SqlInjectionUtils.check(userInput); w.apply("create_time >= {0}", userInput);`（先校验后占位，见 `05-wrapper.md` §4）。
- 为什么：拼接外部输入即留 SQL 注入后门；`{0}` 占位符走 PreparedStatement 参数化，`check` 前置校验拦截恶意输入。

## 6. 逻辑删除 + 唯一索引冲突
- ❌ 对 `(username)` 建唯一索引，逻辑删除后同 username 再次插入报 Duplicate。
- ✅ 唯一索引包含 `deleted` 字段（如 `UNIQUE(username, deleted)`）。推荐 0+时间戳方案时，每条删除记录的 `deleted` 值不同（时间戳），天然避免冲突。
- 为什么：逻辑删除只置 `deleted` 为非零值，原行仍在；若唯一索引不含 `deleted`，约束仍命中。

## 7. 乐观锁不生效
- ❌ 用了 `@Version` 但没注册 `OptimisticLockerInnerInterceptor`；或在自定义 update 中遗漏版本字段。
- ✅ 注册插件 + 走 `updateById` / `update` / `saveOrUpdate`（见 `02-config.md` §3、`03-entity.md` §5）。
- 为什么：乐观锁由插件在 UPDATE 时自动追加 `where version=?` 并 `+1`，缺插件即普通更新。

## 8. Wrapper 复用叠加条件
- ❌ 同一 `Wrapper` 实例多次 `selectList`，第二次条件翻倍。
- ✅ 每次查询 `new` 一个新 Wrapper（见 `05-wrapper.md` §7）。

## 9. 用 eq(field, null) 查空值
- ❌ `w.eq(User::getDeleted, null)` 想查未删除，结果该条件被忽略（查全表）。
- ✅ `w.isNull(User::getDeleted)`。

## 10. 联表分页硬堆 Wrapper
- ❌ 用 `QueryWrapper` 拼 join + 手写分页。
- ✅ 写 XML（入参 `IPage` 不可为 null），见 `06-page.md` §4。

## 11. 重复引入 MyBatis
- ❌ 同时引 `mybatis-spring-boot-starter` 和 `mybatis-plus-boot-starter`。
- ✅ 只引 MP starter（MP 自带 MyBatis）。

## 12. 自动填充不生效
- ❌ `MetaObjectHandler` 没加 `@Component`；或实体已有值却期望被覆盖。
- ✅ 处理器交给 Spring 管理；strict 模式不覆盖已有值（见 `02-config.md` §4）。

## 13. 驼峰 / 字段名对不上
- ❌ 数据库列 `user_name`，实体属性 `userName` 却另起名 `name` 又不标 `@TableField`。
- ✅ 开启 `map-underscore-to-camel-case: true`（默认开）；不一致显式 `@TableField("user_name")`。

## 14. IPage 入参为 null
- ❌ 自定义联表分页方法调用时 `page` 传 null，分页不生效。
- ✅ `IPage` 入参必须非 null（见 `06-page.md` §4）。

## 15. last 覆盖分页 / 排序
- ❌ `wrapper.last("limit 1")` 后又依赖 `Page` 分页。
- ✅ `last` 直接拼 SQL 末尾，会覆盖 MP 生成的分页 / 排序；非必要不用（见 `05-wrapper.md` §5）。

## 16. 枚举映射失效
- ❌ 数据库存 `1`/`2`，枚举没标 `@EnumValue` 也没实现 `IEnum`，查出来是 `null`；或前端收到 `"MALE"` 而非 `1`。
- ✅ 枚举值字段标 `@EnumValue` + JSON 序列化字段标 `@JsonValue`（见 `03-entity.md` §7）。
- 为什么：MP 默认用 `MybatisEnumTypeHandler` 按 `@EnumValue`/`IEnum` 属性映射；未标注则按枚举名称（`MALE`/`FEMALE`）匹配，与数据库的 `1`/`2` 对不上。Jackson 默认序列化枚举名，需 `@JsonValue` 指定输出值。

## 17. XML 中枚举 typeHandler 漏声明
- ❌ 自定义 XML 查询中，枚举字段只在 resultMap 声明了 typeHandler，查询条件 `#{gender}` 没声明。
- ✅ 枚举字段在 XML 的**每个位置**（resultMap、条件 `#{}`、插入 `#{}`）都要写 `typeHandler=MybatisEnumTypeHandler`（见 `10-xml.md` §5.4）。
- 为什么：XML 不继承实体注解，typeHandler 必须逐处显式声明。

## 18. @Transactional 未指定 rollbackFor
- ❌ `@Transactional` 不写 `rollbackFor`，业务异常继承 `Exception`（非 RuntimeException），抛出后不回滚。
- ✅ 一律写 `@Transactional(rollbackFor = Exception.class)`（见 `11-transaction.md` §1）。
- 为什么：Spring 默认只回滚 `RuntimeException` + `Error`，checked exception 默认提交。

## 19. 事务自调用失效
- ❌ 同类中 `methodA` 直接调用 `this.methodB()`，`methodB` 上的 `@Transactional` 不生效。
- ✅ 注入自身代理（`@Lazy` 自注入）或拆分到不同 Service（见 `11-transaction.md` §3 场景1）。
- 为什么：`@Transactional` 基于 Spring AOP 代理，内部调用走 `this`，不经过代理对象，事务被跳过。

## 20. 异常被 catch 吞掉导致不回滚
- ❌ `@Transactional` 方法内 `try-catch` 吞掉异常，Spring 感知不到异常，事务正常提交。
- ✅ catch 后 `throw` 重新抛出，或 `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()` 手动标记（见 `11-transaction.md` §3 场景3）。
- 为什么：Spring 通过检测方法是否抛出异常来决定回滚；异常被吞，方法正常返回，Spring 认为事务成功。

## 21. @Transactional 加在非 public 方法
- ❌ `@Transactional` 加在 `private` / 包级可见方法上，静默失效。
- ✅ 事务方法必须 `public`（见 `11-transaction.md` §3 场景2）。
- 为什么：Spring AOP 默认只代理 public 方法；非 public 方法上的 `@Transactional` 不报错但不生效。

## 22. saveBatch 在事务外执行
- ❌ 无 `@Transactional` 直接 `saveBatch(list)`，每条 insert 独立提交，性能差且无原子性。
- ✅ 加 `@Transactional(rollbackFor = Exception.class)` + JDBC URL `rewriteBatchedStatements=true`（见 `11-transaction.md` §4）。
- 为什么：事务外 `saveBatch` 每条 SQL 独立提交，无法利用 JDBC 批量合并；事务内同 SqlSession + rewriteBatchedStatements 才是真正批量。

## 23. 多数据源 + 单一 @Transactional 期望跨库一致性
- ❌ `@DS("master")` + `@Transactional` 中跨 `@DS("slave")` 操作，以为跨库也原子。
- ✅ 跨库一致性用 Seata / XA 或补偿机制；同一事务内不要切换数据源（见 `11-transaction.md` §6）。
- 为什么：Spring 事务管理器绑定单个 Connection，`@DS` 切换数据源后新连接不在原事务内，原库回滚不影响新库。
