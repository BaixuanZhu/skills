# DbType 适配速查（非 MySQL 项目必读）

> 本 skill 示例默认 MySQL，但 MP 支持 PostgreSQL / Oracle / SQL Server / 达梦 / 人大金仓 等。**跨库的坑集中在「分页方言、主键策略、标识符引用符、逻辑删除函数、批量语法」五处**，其余 CRUD/Wrapper/插件用法与 MySQL 一致。

## 1. 速查表

| 维度 | MySQL | PostgreSQL | Oracle | SQL Server | 达梦/金仓 |
|---|---|---|---|---|---|
| 分页方言（MP 自动，但需 `DbType`） | `LIMIT ?` | `LIMIT ?` | `ROWNUM` 嵌套 | `OFFSET ? ROWS FETCH` / `TOP` | 同 Oracle / PG |
| 推荐主键策略 | `AUTO`（自增）/ `ASSIGN_ID` | `ASSIGN_ID` / `IDENTITY` | `INPUT` + `@KeySequence`（序列） | `ASSIGN_ID` / `IDENTITY` | 同 Oracle / PG |
| 标识符引用符 | `` `col` `` | `"col"` | `"col"` | `[col]` / `"col"` | `"col"` |
| 逻辑删除函数（见 `02-config.md §2`） | `UNIX_TIMESTAMP(now())*1000` | `floor(extract(epoch from now())*1000)` | `(SYSTIMESTAMP - DATE '1970-01-01')*86400000` | `DATEDIFF_BIG(ms,'1970...',GETUTCDATE())` | 兼容 Oracle |
| 批量 insert 语法 | 多值 `VALUES (),( )`（`InsertBatchSomeColumn` 适用） | 多值 / `COPY` | `INSERT ALL` / BATCH executor | 多值 / BATCH executor | 同 Oracle / PG |
| 常用函数差异 | `NOW()` / `IFNULL` / `CONCAT` | `NOW()` / `COALESCE` / `||` | `SYSDATE` / `NVL` / `||` | `GETDATE()` / `ISNULL` / `+` | 同 Oracle / PG |

## 2. 强约束：非 MySQL 必须显式指定 DbType

> 见 SKILL.md 核心强约束 #6。多数据源 / 非 MySQL 单库，必须在 `PaginationInnerInterceptor` 显式传 `DbType`，否则分页 SQL 方言可能生成错误（COUNT 错或语法错）。

```java
// 非 MySQL 必须显式 DbType，不要依赖默认
interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.POSTGRE_SQL));
// 或 Oracle：DbType.ORACLE；SQL Server：DbType.SQL_SERVER
```

## 3. 主键策略（最容易踩坑）

- **Oracle / 人大金仓（类 Oracle）**：`AUTO` 不适用（无自增列），用序列：
  ```java
  @KeySequence("SEQ_USER")            // 数据库序列名
  public class User {
      @TableId(type = IdType.INPUT)   // 由序列赋值，勿用 AUTO
      private Long id;
  }
  ```
  或全局统一用 `ASSIGN_ID`（雪花算法，跨库无侵入，推荐微服务）。
- **PostgreSQL / 达梦**：`IDENTITY`（基于 `SERIAL`/`IDENTITY` 列）或 `ASSIGN_ID`。
- **SQL Server**：`IDENTITY` 或 `ASSIGN_ID`。

> ⚠️ 在 Oracle 上用 `IdType.AUTO` → 启动或插入报「自增列不支持」，应改 `INPUT`+`@KeySequence` 或 `ASSIGN_ID`。

## 4. 标识符引用符 / 保留字

- 列名含保留字（如 `order` / `user` / `desc`）时，需按库用引用符包裹：`@TableField("\"order\"")`(Oracle/PG/达梦) 或 `` @TableField("`order`") ``(MySQL)。
- MP 的 `DbType` 内置 `keywordFit` 关键字转义，但仅覆盖**已知关键字**；自定义保留字列名仍需手写引用符。

## 5. 逻辑删除函数（方言绑定）

`logic-delete-value` 是「原样拼入 SQL 的字符串」，换数据库必须改表达式（见 `02-config.md §2` 毫秒时间戳方言表）。**不要**把 MySQL 的 `UNIX_TIMESTAMP(now())*1000` 直接用到 Oracle/PG，否则删除时报函数不存在。

## 6. 反模式（高频踩坑）

- ❌ **漏 DbType**：非 MySQL 未显式指定 `DbType` → 分页生成错误方言（如给 Oracle 生成 `LIMIT`），`selectPage` 报 SQL 语法错或 total 恒为 0。✅ 显式 `DbType.XXX`（强约束 #6）。
- ❌ **Oracle/PG 用 `IdType.AUTO`**：无自增列支持，插入失败。✅ `INPUT`+`@KeySequence` 或 `ASSIGN_ID`。
- ❌ **引用符写死反引号**：XML/注解里写 `` `col` `` 在 Oracle/PG 报标识符错。✅ 按库改用 `"col"`。
- ❌ **`apply` 写 MySQL 函数**：`w.apply("create_time >= NOW()")` 在 Oracle 报 `NOW` 无效。✅ 用与 DbType 匹配的函数（`SYSDATE` / `NOW()`），或优先用 Wrapper 标准 API 避免手写函数。
- ❌ **`InsertBatchSomeColumn` 当通用批量**：其多值语法主要适配 MySQL；Oracle/SQL Server 应走 `BATCH` executor（见 `04-crud.md §3`）。
