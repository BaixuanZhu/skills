# 全局配置与插件

> 所有插件以 `MybatisPlusInterceptor` 为容器，通过 `addInnerInterceptor` 添加。分页插件务必最后添加。

## 1. 插件主体与分页插件

```java
@Configuration
@MapperScan("com.example.mapper")
public class MybatisPlusConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        // 乐观锁
        interceptor.addInnerInterceptor(new OptimisticLockerInnerInterceptor());
        // 防全表更新与删除
        interceptor.addInnerInterceptor(new BlockAttackInnerInterceptor());
        // 分页插件：必须最后添加
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }
}
```

> ⚠️ **分页插件必须最后添加**：若多租户 / 动态表名等在其后，COUNT SQL 可能被错误改写导致分页总数不准。
> 分页依赖 `mybatis-plus-jsqlparser`（v3.5.9+ 已拆分），未引则分页**静默失效、无报错**（见 `01-start.md`）。

`PaginationInnerInterceptor` 常用属性：
| 属性 | 默认 | 说明 |
|---|---|---|
| `overflow` | false | 超出总页数是否回到首页 |
| `maxLimit` | 无 | 单页最大条数限制（防恶意大分页） |
| `dbType` | 无 | 数据库类型，单库建议显式指定 |

## 2. 逻辑删除（全局）

> **推荐 0+时间戳方案**（而非 0/1）：字段类型 `Long`，未删除 = `0`，删除时写入当前时间戳。好处：删除时间即逻辑删除标记，可追溯何时删除，无需额外 `delete_time` 字段；且非零值天然区分未删除行。

```yaml
mybatis-plus:
  global-config:
    db-config:
      logic-delete-field: deleted                    # 全局逻辑删除字段名（实体属性名）
      logic-not-delete-value: 0                      # 未删除 = 0
      logic-delete-value: "UNIX_TIMESTAMP(now())*1000"  # 已删除 = 当前毫秒时间戳（MySQL）
```
- `logic-delete-value` 的值是**直接拼入 SQL 的字符串**，支持写 SQL 函数。删除时生成 SQL 为 `UPDATE table SET deleted = UNIX_TIMESTAMP(now())*1000 WHERE id = ?`。
- 字段类型 `Long`；查询自动追加 `deleted = 0` 过滤已删除行。
- 也可在字段上用 `@TableLogic` 单独配置（见 `03-entity.md`）。
- 启用后：查询自动过滤已删除行；`update` 不会更新已删除行；`delete` 变为 `UPDATE SET deleted = <时间戳>`。
- **唯一索引**须包含 `deleted` 字段（如 `UNIQUE(username, deleted)`），否则逻辑删除后同值插入报 Duplicate。
- **毫秒时间戳方言表**（`logic-delete-value` 是字符串，原样拼入 SQL）：

| 数据库 | 表达式 |
|---|---|
| MySQL | `UNIX_TIMESTAMP(now())*1000` |
| PostgreSQL | `floor(extract(epoch from now())*1000)` |
| SQL Server | `DATEDIFF_BIG(millisecond,'1970-01-01',GETUTCDATE())` |
| Oracle | `(SYSTIMESTAMP - DATE '1970-01-01') * 86400000` |
| SQLite | `unixepoch()*1000`（旧版 `strftime('%s','now')*1000`） |
| 达梦 | 兼容 Oracle 表达式 |

> ⚠️ 换数据库必须改该表达式（方言绑定）。
- 备选方案（不推荐）：`LocalDateTime` + null，`logic-not-delete-value: 'null'`（yaml 单引号转义）、`logic-delete-value: "now()"`，字段类型 `LocalDateTime`。不如 0+时间戳直观。

## 3. 乐观锁插件

在 §1 插件容器中已注册 `OptimisticLockerInnerInterceptor`；实体字段加 `@Version`（见 `03-entity.md` §5），更新时自动 `set version = version + 1 where version = ?`，版本不符则影响行数为 0。

## 4. 自动填充

```java
@Slf4j
@Component
public class MyMetaObjectHandler implements MetaObjectHandler {
    @Override
    public void insertFill(MetaObject metaObject) {
        strictInsertFill(metaObject, "createTime", LocalDateTime.class, LocalDateTime.now());
        strictInsertFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
    }
    @Override
    public void updateFill(MetaObject metaObject) {
        strictUpdateFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
    }
}
```
实体字段：`@TableField(fill = FieldFill.INSERT)` / `FieldFill.UPDATE` / `FieldFill.INSERT_UPDATE`。
> 自动填充是直接给实体属性设值；若属性本身已有值，strict 模式**默认不覆盖**。

## 5. 防全表更新 / 删除

`BlockAttackInnerInterceptor`：拦截无 WHERE 条件的 `update` / `delete`，防止误清表。生产环境建议开启。

## 6. 其它常用配置

```yaml
mybatis-plus:
  configuration:
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl   # 打印 SQL（调试用，生产关闭）
    map-underscore-to-camel-case: true                      # 下划线→驼峰（默认即 true）
  global-config:
    banner: false                                           # 关闭启动 banner
    db-config:
      id-type: auto                                         # 全局主键策略（DB 自增，详见 03-entity.md §2）
      table-prefix: t_                                      # 表前缀
      column-underline: true
```

## 7. 字段策略全局配置（insertStrategy / updateStrategy / whereStrategy）

> 核心问题：`updateById(entity)` 中 entity 的 `null` 字段默认不参与 SQL——根因就是全局 `updateStrategy` 默认 `NOT_NULL`。

### FieldStrategy 枚举值

| 策略 | insert 时 | update 时 | where 时 | 说明 |
|------|----------|----------|---------|------|
| `DEFAULT` | 跟随全局 | 跟随全局 | 跟随全局 | 字段级默认，回退到全局配置 |
| `NOT_NULL`（**全局默认**） | null 不插入 | null 不更新 | null 不作条件 | 最常用，防止误置空 |
| `NOT_EMPTY` | null / 空串不插入 | null / 空串不更新 | null / 空串不作条件 | 字符串场景防空串 |
| `ALWAYS` | 总是插入（含 null） | 总是更新（含 null） | 总是作条件 | 等价于旧 `IGNORED` |
| `NEVER` | 不插入 | 不更新 | 不作条件 | 只读字段 |
| `IGNORED` | 同 `ALWAYS` | 同 `ALWAYS` | 同 `ALWAYS` | **@Deprecated**，用 `ALWAYS` 替代 |

### 全局配置（yml）

```yaml
mybatis-plus:
  global-config:
    db-config:
      insert-strategy: NOT_NULL        # 默认值，null 字段不插入
      update-strategy: NOT_NULL        # 默认值，null 字段不更新（★ "null 不更新"根因）
      where-strategy: NOT_NULL         # 默认值，null 不生成 WHERE 条件
```

### 字段级覆盖（@TableField）

全局策略可被单个字段覆盖：

```java
public class User {
    // 该字段无论 null 与否都参与更新（慎用，会绕过 null 不更新保护）
    @TableField(updateStrategy = FieldStrategy.ALWAYS)
    private String remark;

    // 该字段插入时 null 也写入
    @TableField(insertStrategy = FieldStrategy.ALWAYS)
    private LocalDateTime deleteTime;

    // 该字段永远不参与更新（只读）
    @TableField(updateStrategy = FieldStrategy.NEVER)
    private Date createTime;
}
```

### 三个策略的作用域

| 配置项 | 作用阶段 | 影响方法 |
|--------|---------|---------|
| `insertStrategy` | INSERT 语句生成 | `insert` / `save` / `saveBatch` |
| `updateStrategy` | UPDATE 语句生成 | `updateById` / `update(entity, wrapper)` |
| `whereStrategy` | WHERE 条件生成（Entity 作为条件时） | `update(entity, wrapper)` 中 entity 部分生成的条件 |

> ⚠️ `whereStrategy` 仅影响**通过 Entity 自动生成 WHERE 条件**的场景（如 `update(entity, wrapper)` 中 entity 非空字段自动作为等值条件）。手动 `Wrapper.eq(...)` 不受此配置影响。

### 常见误区

- **全局改 `update-strategy: ALWAYS`**：会让所有 `updateById` 都把 null 字段写入数据库，可能误清数据。**不推荐全局改**，应在需要的字段上用 `@TableField(updateStrategy = FieldStrategy.ALWAYS)` 单独覆盖。
- **想置空单个字段**：不要改全局策略，用 `UpdateWrapper.set(User::getAge, null)` 精准置空（见 `08-antipattern.md` §2）。
- **`IGNORED` 已废弃**：旧代码中的 `FieldStrategy.IGNORED` 等价于 `ALWAYS`，应迁移。

## 8. 其他全局配置项速查

### DbConfig（global-config.db-config 下）

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `id-type` | `IdType` | `ASSIGN_ID` | 全局主键策略（推荐改 `AUTO`，见 `03-entity.md` §2） |
| `table-prefix` | `String` | null | 表名前缀（如 `t_`） |
| `table-format` | `String` | null | 表名格式化（如 `tbl_%s`），@since 3.5.3.2 |
| `column-format` | `String` | null | 字段名格式化（如 `%s_field`） |
| `property-format` | `String` | null | 属性名格式化，@since 3.3.0 |
| `table-underline` | `boolean` | true | 表名驼峰转下划线 |
| `capital-mode` | `boolean` | false | 大写命名模式 |
| `logic-delete-field` | `String` | null | 全局逻辑删除字段名（见 §2） |
| `logic-delete-value` | `String` | "1" | 逻辑已删除值 |
| `logic-not-delete-value` | `String` | "0" | 逻辑未删除值 |

### GlobalConfig（global-config 下，非 db-config）

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `banner` | `boolean` | true | 控制台打印 MP LOGO |
| `enable-sql-runner` | `boolean` | false | 是否初始化 `SqlRunner` |
| `super-mapper-class` | `Class` | `Mapper.class` | 通用 Mapper 父类（仅子类注入通用方法） |
| `meta-object-handler` | `MetaObjectHandler` | null | 自动填充处理器（见 §4，推荐 `@Bean` 注入） |
| `identifier-generator` | `IdentifierGenerator` | `DefaultIdentifierGenerator` | ID 生成器（雪花算法等） |

### Configuration（configuration 下，MyBatis 原生）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `map-underscore-to-camel-case` | true | 下划线转驼峰 |
| `default-enum-type-handler` | `EnumTypeHandler` | 默认枚举处理器（3.5.2+ 为 `CompositeEnumTypeHandler`，见 `03-entity.md` §6） |
| `auto-mapping-behavior` | `PARTIAL` | 自动映射策略（`NONE`/`PARTIAL`/`FULL`） |
| `local-cache-scope` | `SESSION` | 一级缓存范围（微服务建议 `STATEMENT` 关闭） |
| `cache-enabled` | true | 二级缓存开关 |
| `call-setters-on-nulls` | false | null 时是否调用 setter（Map 场景用） |
| `log-impl` | null | SQL 日志实现（调试用 `StdOutImpl`） |
| `executor-type` | `SIMPLE` | 执行器类型（`SIMPLE`/`REUSE`/`BATCH`） |
