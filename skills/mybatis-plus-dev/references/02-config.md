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

在 §1 插件容器中已注册 `OptimisticLockerInnerInterceptor`；实体字段加 `@Version`（见 `03-entity.md` §3），更新时自动 `set version = version + 1 where version = ?`，版本不符则影响行数为 0。

## 4. 自动填充

实现 `MetaObjectHandler`（标 `@Component`），在 `insertFill` / `updateFill` 中用 `strictInsertFill` / `strictUpdateFill` 填值；实体字段标 `@TableField(fill = FieldFill.INSERT | UPDATE | INSERT_UPDATE)`。

> `strict` 模式在**属性已有值时不覆盖**。

## 5. 防全表更新 / 删除

`BlockAttackInnerInterceptor` 拦截无 WHERE 条件的 `update` / `delete`，防误清表，生产建议开启。

## 6. 字段策略（`updateById` 的 null 不更新根因）

`updateById(entity)` 中 entity 的 `null` 字段不进 SQL——根因是全局 `updateStrategy` 默认 `NOT_NULL`。

| 策略 | 行为 | 说明 |
|---|---|---|
| `NOT_NULL`（**全局默认**） | null 不插入 / 不更新 / 不作条件 | 防误置空 |
| `NOT_EMPTY` | null 与空串都跳过 | 字符串场景 |
| `ALWAYS` | 含 null 也写入 | 等价于旧 `IGNORED`（已废弃） |
| `NEVER` | 永不参与 | 只读字段 |
| `DEFAULT` | 回退全局配置 | 字段级默认值 |

三个配置项对应三个阶段：`insert-strategy`（`insert`/`save`/`saveBatch`）、`update-strategy`（`updateById`/`update(entity,wrapper)`）、`where-strategy`（**只影响 Entity 自动生成的 WHERE 条件**，手动 `Wrapper.eq()` 不受它控制）。

字段级覆盖：

```java
@TableField(updateStrategy = FieldStrategy.ALWAYS)   // 含 null 也更新（慎用）
private String remark;

@TableField(updateStrategy = FieldStrategy.NEVER)    // 只读
private Date createTime;
```

**误区**

- **全局改 `update-strategy: ALWAYS`**：所有 `updateById` 都会把 null 字段写库，可能误清数据。只在需要的字段上单独覆盖。
- **想置空单个字段**：用 `UpdateWrapper.set(User::getAge, null)` 精准置空，不要为此改全局策略（见 `08-antipattern.md` §2）。
