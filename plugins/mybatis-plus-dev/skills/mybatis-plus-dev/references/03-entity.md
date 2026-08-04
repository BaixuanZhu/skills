# 实体与字段映射

> 实体类通过注解建立与表的映射。最常见的坑是 **null 不更新** 与 **主键 / 字段名对不上**。

## 1. 表名 @TableName

```java
@TableName("sys_user")          // 表名与类名不一致时指定
public class User { ... }
```
全局可配 `table-prefix: t_` 省去逐个标注。

## 2. 主键 @TableId

```java
@TableId(type = IdType.AUTO)   // DB 自增（推荐默认）
private Long id;
```
`IdType`：
| 值 | 说明 |
|---|---|
| `AUTO`（推荐默认） | 数据库自增，依赖表自增列（MySQL `AUTO_INCREMENT` / PG `BIGSERIAL` / SQL Server `IDENTITY`） |
| `ASSIGN_ID`（MP 全局默认） | 雪花算法，类型用 Long |
| `ASSIGN_UUID` | UUID 去横线，类型 String |
| `INPUT` | 自行赋值（不自动生成） |
| `NONE` | 无策略，随全局 `id-type` |

**为什么默认 `AUTO` 而非 MP 全局默认的 `ASSIGN_ID`（雪花）**：
- 简单、紧凑、可读、生成可靠（由 DB 兜底），前端无 Long 精度问题；
- MP 默认 `ASSIGN_ID` 是为分布式 / 分库兜底，单体单库项目用不上它的红利；
- 未来若扩展为分布式，`BIGINT` 让新老 id 兼容、切换成本低，不必现在提前上雪花。

## 3. 字段 @TableField

```java
public class User {
    @TableField("user_name")                 // 数据库列名与属性名不一致
    private String name;

    @TableField(exist = false)               // 非数据库字段（临时计算属性）
    private String temp;

    @TableField(fill = FieldFill.INSERT_UPDATE)   // 自动填充
    private LocalDateTime updateTime;

    @TableField(typeHandler = JacksonTypeHandler.class)  // JSON 字段
    private OtherInfo otherInfo;

    @TableField(condition = "%s > #{%s}")    // 自定义条件（仅 allEq / 实体构造时用）
    private Integer age;
}
```

> **时间字段推荐组合**：DB 列设 `DEFAULT now()` 兜底 + 实体 `@TableField(fill = FieldFill.INSERT / INSERT_UPDATE)` + `MetaObjectHandler` 统一填充（见 `02-config.md` §4）。业务代码**不得手动 `setCreateTime/setUpdateTime`**——统一交给自动填充，避免遗漏。

## 4. 字段策略与 null 不更新（重点）

`FieldStrategy` 决定字段何时进入 SQL，**完整策略清单与全局配置见 `02-config.md` §7**（含 `ALWAYS`/`NEVER`/`IGNORED` 弃用说明）。

**默认情况下 `updateById(entity)` 中 `null` 字段不会写入 SQL**，这正是"为什么 update 后某些字段没变"的根因（全局 `updateStrategy` 默认 `NOT_NULL`）。

- 想把某字段显式置为 `null`：用 `UpdateWrapper.set("age", null)`。
- 想某字段随时可 null：字段标 `@TableField(updateStrategy = FieldStrategy.ALWAYS)`（慎用，会绕过 null 不更新保护）。

```java
// 把 age 更新为 null
userMapper.update(null, new LambdaUpdateWrapper<User>()
    .eq(User::getId, 1L)
    .set(User::getAge, null));
```

## 5. 乐观锁 @Version

```java
@Version
private Integer version;
```
- 字段类型：`int` / `Integer` / `long` / `Long` / `Date` / `LocalDateTime`。
- 必须配合 `OptimisticLockerInnerInterceptor`（见 `02-config.md`）。
- 仅在 `updateById` / `update(entity, wrapper)` / `saveOrUpdate` 时生效；`wrapper` 不可复用。

## 6. 逻辑删除 @TableLogic

```java
@TableLogic
private Long deleted;    // 推荐 Long 类型，0=未删除，时间戳=已删除
```
- 不配全局时，用注解单独指定；全局配了则无需注解。
- 推荐方案：`Long` 字段 + `logic-not-delete-value: 0` + `logic-delete-value: "UNIX_TIMESTAMP(now())*1000"`（详见 `02-config.md` §2）。
- 删除变更新、查询自动过滤，详见 `02-config.md`。

## 7. 枚举映射（重点）

MP 提供 `MybatisEnumTypeHandler`（基于枚举常量属性），优于 MyBatis 原生的 `EnumOrdinalTypeHandler`（序号）和 `EnumTypeHandler`（名称）。**两种声明方式，任选其一：**

### 方式一：@EnumValue 注解（推荐）

```java
@Getter
@AllArgsConstructor
public enum GenderEnum {
    MALE(1, "男"),
    FEMALE(2, "女");

    @EnumValue              // 标记数据库存储的值
    @JsonValue              // 标记 JSON 序列化输出给前端的值（非枚举名）
    private final int code;
    private final String desc;
}
```

```java
@TableName("sys_user")
public class User {
    private GenderEnum gender;   // 实体直接用枚举类型，MP 自动转换
}
```

### 方式二：实现 IEnum 接口

```java
@Getter
@AllArgsConstructor
public enum AgeEnum implements IEnum<Integer> {
    ONE(1, "一岁"),
    TWO(2, "二岁");

    private final int value;
    private final String desc;

    @Override
    public Integer getValue() {
        return value;      // 返回数据库存储的值
    }
}
```

### 全局默认处理器

未用 `@EnumValue` / `IEnum` 的枚举，可通过全局配置指定处理器（不配则用 MyBatis 默认的 `EnumTypeHandler`，按枚举名称映射）：

```yaml
mybatis-plus:
  configuration:
    default-enum-type-handler: com.baomidou.mybatisplus.core.handlers.MybatisEnumTypeHandler
```

> 配了全局 `MybatisEnumTypeHandler` 后，枚举**必须**有 `@EnumValue` 或实现 `IEnum`，否则报错。

### XML 中的枚举

实体字段用枚举类型时，XML 中 resultMap 和 `#{}` 需显式声明 `typeHandler`：

```xml
<result property="gender" column="gender"
        typeHandler="com.baomidou.mybatisplus.core.handlers.MybatisEnumTypeHandler"/>

<!-- 条件参数也要声明 -->
WHERE gender = #{gender, typeHandler=com.baomidou.mybatisplus.core.handlers.MybatisEnumTypeHandler}
```

> ⚠️ MP 自动 CRUD（BaseMapper / IService）无需在 XML 声明 typeHandler，仅自定义 XML 查询需要。

### 常见坑

- **枚举值查不到**：数据库存的 `1`/`2`，但枚举没标 `@EnumValue`，MP 按名称（`MALE`/`FEMALE`）映射 → 查不出来。
- **前端收到枚举名**：没加 `@JsonValue`，Jackson 序列化输出 `"MALE"` 而非 `1`。
- **全局处理器冲突**：配了 `default-enum-type-handler: MybatisEnumTypeHandler` 但某些枚举没标 `@EnumValue` → 启动报错。
- **String 类型枚举值**：`@EnumValue` 标在 `String code` 上也支持（如 `"M"` / `"F"`）。

## 8. JSON 字段

```java
@TableField(typeHandler = JacksonTypeHandler.class)
private OtherInfo otherInfo;
```
- 依赖 jackson（Spring Boot 默认引入）。
- PostgreSQL `jsonb` 需自定义 `JsonbTypeHandler` 或用 MP 的 `JacksonTypeHandler`。
- XML 中需显式声明 `typeHandler`（见 `10-xml.md` §5.4）。
