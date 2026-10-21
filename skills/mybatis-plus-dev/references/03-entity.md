# 实体与字段映射

> 实体类通过注解建立与表的映射。最常见的坑是 **null 不更新** 与 **主键 / 字段名对不上**。

## 1. 主键 @TableId

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

## 2. 字段策略与 null 不更新（重点）

`FieldStrategy` 决定字段何时进入 SQL，**完整策略清单与全局配置见 `02-config.md` §6**（含 `ALWAYS`/`NEVER`/`IGNORED` 弃用说明）。

**默认情况下 `updateById(entity)` 中 `null` 字段不会写入 SQL**，这正是"为什么 update 后某些字段没变"的根因（全局 `updateStrategy` 默认 `NOT_NULL`）。

- 想把某字段显式置为 `null`：用 `LambdaUpdateWrapper.set(User::getAge, null)`（方法引用版，代码示例见 `05-wrapper.md` §2）。
- 想某字段随时可 null：字段标 `@TableField(updateStrategy = FieldStrategy.ALWAYS)`（慎用，会绕过 null 不更新保护）。

## 3. 乐观锁 @Version

`@Version` 字段 + 注册 `OptimisticLockerInnerInterceptor`（见 `02-config.md` §3）。

只在 `updateById` / `update(entity, wrapper)` / `saveOrUpdate` 生效。**走 `update(null, wrapper)` 不触发**——这是"乐观锁没报错但也没拦住"的常见原因（影响行数为 0 而非抛异常）。

## 4. 逻辑删除 @TableLogic

```java
@TableLogic
private Long deleted;    // 推荐 Long 类型，0=未删除，时间戳=已删除
```
- 不配全局时，用注解单独指定；全局配了则无需注解。
- 推荐方案：`Long` 字段 + `logic-not-delete-value: 0` + `logic-delete-value: "UNIX_TIMESTAMP(now())*1000"`（详见 `02-config.md` §2）。
- 删除变更新、查询自动过滤，详见 `02-config.md`。

## 5. 枚举映射（重点）

MP 的 `MybatisEnumTypeHandler` 按枚举里的自定义属性映射，优于 MyBatis 原生的 `EnumTypeHandler`（按**名称**存）和 `EnumOrdinalTypeHandler`（按**序号**存，枚举加值就整体错位）。

```java
@Getter @AllArgsConstructor
public enum GenderEnum {
    MALE(1, "男"), FEMALE(2, "女");

    @EnumValue    // 标记存库的值
    @JsonValue    // 标记返回前端的值（否则 Jackson 输出 "MALE"）
    private final int code;
    private final String desc;
}

@TableName("sys_user")
public class User { private GenderEnum gender; }   // MP 自动转换
```

> 另一种写法是实现 `IEnum<T>` 并重写 `getValue()`，效果等价，二选一即可。

**全局默认处理器**：`configuration.default-enum-type-handler: MybatisEnumTypeHandler` 可覆盖未标注的枚举。但配了之后，**所有枚举都必须有 `@EnumValue` 或实现 `IEnum`，否则启动报错**。

**XML 中的枚举（反直觉点）**：MP 自动 CRUD（`BaseMapper` / `IService`）**不需要**声明 typeHandler；但**自定义 XML 的每一处**（resultMap、条件 `#{}`、插入 `#{}`）都要显式声明，漏一处就静默映射成 null 或报类型错误：

```xml
<result property="gender" column="gender" typeHandler="...MybatisEnumTypeHandler"/>
WHERE gender = #{gender, typeHandler=...MybatisEnumTypeHandler}
```

**常见坑**

- 库里存 `1`/`2` 但查不出 → 枚举没标 `@EnumValue`，MP 按名称 `"MALE"` 去匹配
- 前端收到 `"MALE"` 而非 `1` → 缺 `@JsonValue`
- 启动报枚举处理器相关错误 → 配了全局处理器但该枚举没有 `@EnumValue`
- `String` 类型的枚举值同样支持（`@EnumValue` 标在 `String code` 上）


## 6. JSON 字段

```java
@TableField(typeHandler = JacksonTypeHandler.class)
private OtherInfo otherInfo;
```
- 依赖 jackson（Spring Boot 默认引入）。
- PostgreSQL `jsonb` 需自定义 `JsonbTypeHandler` 或用 MP 的 `JacksonTypeHandler`。
- XML 中需显式声明 `typeHandler`（见 `10-xml.md` §4.1）。
