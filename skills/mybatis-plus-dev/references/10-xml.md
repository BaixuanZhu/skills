# MyBatis XML Mapper 编写指南

> MP 擅长单表 CRUD，复杂 / 联表查询应写 XML。

## 1. mapper-locations 配置

MP 默认扫描 `classpath*:/mapper/**/*.xml`。若自定义路径，需在 `application.yml` 中声明：

```yaml
mybatis-plus:
  mapper-locations: classpath*:/mapper/**/*.xml
```

> ⚠️ 不配此项且 XML 不在默认路径下时，`Invalid bound statement (not found)` 报错。
> 多个路径用逗号分隔：`classpath*:/mapper/**/*.xml,classpath*:/mybatis/*.xml`。

XML 文件放 `src/main/resources/mapper/` 下，按业务分包（如 `mapper/user/UserMapper.xml`）。

## 2. XML 结构的三条硬规则

```xml
<mapper namespace="com.example.mapper.UserMapper">   <!-- 必须是 Mapper 接口全限定名 -->
    <select id="selectById" resultMap="userResultMap"> <!-- id 必须是方法名 -->
        SELECT id, user_name FROM sys_user WHERE id = #{id}
    </select>
</mapper>
```

- `namespace` = Mapper 接口**全限定名**，`id` = **方法名**，二者任一不符就抛 `Invalid bound statement`
- `resultType` 走自动映射（列名=属性名，下划线驼峰自动转换）；`resultMap` 用于列名≠属性名、联表嵌套、typeHandler

## 3. `#{}` vs `${}`

| 写法 | 机制 | 安全 | 何时用 |
|---|---|---|---|
| `#{name}` | PreparedStatement `?` 占位 | ✅ | **绝大多数场景** |
| `${name}` | 字符串拼接 | ❌ | 仅**结构值**（排序列、表名），且必须白名单校验 |

排序是唯一常见例外——`ORDER BY ${sortField}` 无法参数化，因此**排序列必须在 Service 层用白名单枚举校验**，禁止直接透传前端传来的字段名。


## 4. resultMap 结果映射

### 4.1 typeHandler 在 XML 中声明

实体字段标了 `@TableField(typeHandler = ...)` 或使用枚举类型时，XML 中需显式声明 typeHandler：

**JSON 字段：**
```xml
<!-- resultMap 中 -->
<result property="otherInfo" column="other_info"
        typeHandler="com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler"/>

<!-- insert 中 -->
INSERT INTO sys_user (other_info) VALUES (#{otherInfo, typeHandler=com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler})
```

**枚举字段（重点）：**
```xml
<!-- resultMap 中 -->
<result property="gender" column="gender"
        typeHandler="com.baomidou.mybatisplus.core.handlers.MybatisEnumTypeHandler"/>

<!-- 查询条件中也要声明，否则不转换 -->
WHERE gender = #{gender, typeHandler=com.baomidou.mybatisplus.core.handlers.MybatisEnumTypeHandler}

<!-- insert 中同理 -->
INSERT INTO sys_user (gender) VALUES (#{gender, typeHandler=com.baomidou.mybatisplus.core.handlers.MybatisEnumTypeHandler})
```

> ⚠️ 枚举字段在 XML 中的**每个出现位置**（resultMap、`#{}` 条件、`#{}` 插入）都要声明 typeHandler，漏一处即转换失败。
> MP 自动 CRUD（BaseMapper / IService）无需声明，仅自定义 XML 需要。

## 5. 联表分页 XML（配合 IPage）

MP 分页插件自动改写 XML 中的 select 语句，添加 `LIMIT` 和 `COUNT`。Mapper 方法入参 `IPage` **不可为 null**：

```java
// Mapper 接口
IPage<UserVO> selectUserPage(IPage<UserVO> page, @Param("query") UserQueryDTO query);
```

```xml
<select id="selectUserPage" resultMap="userWithDeptResultMap">
    SELECT u.id AS u_id, u.user_name AS u_name,
           d.id AS d_id, d.dept_name AS d_name
    FROM sys_user u
    LEFT JOIN sys_dept d ON u.dept_id = d.id
    <where>
        <if test="query.name != null and query.name != ''">
            AND u.user_name LIKE CONCAT('%', #{query.name}, '%')
        </if>
        <if test="query.deptId != null">
            AND u.dept_id = #{query.deptId}
        </if>
    </where>
    ORDER BY u.id DESC
</select>
```

**关键点**：
- 返回类型必须是 `IPage<UserVO>`（不是 `List`），MP 靠它判断需要分页改写。
- MP 自动生成 `SELECT COUNT(*)` 查询总数；若 SQL 复杂导致 count 不准，可用自定义 count（见 `06-page.md` §3）。
- `ORDER BY` 写在 XML 中即可，分页插件在 `ORDER BY` 后追加 `LIMIT`。
- 联表查询的列名必须用别名（`AS`），避免多表同名列冲突。

## 6. 常见坑

| 问题 | 原因 | 解决 |
|---|---|---|
| `Invalid bound statement (not found)` | XML 未被扫描 / namespace 不一致 / 方法名不匹配 | 检查 `mapper-locations` 路径、namespace 全限定名、id 与方法名 |
| `BindingException: Parameter 'xxx' not found` | 多参数未 `@Param` | Mapper 方法参数加 `@Param("xxx")` |
| 联表查重复行 | 一对多未用 `<id>` 去重 | resultMap 中必须声明 `<id>` |
| `${}` 注入 | 排序字段 / 表名用了 `${}` | 白名单校验 + `SqlInjectionUtils.check()` |
| typeHandler 不生效 | XML 中未显式声明 | resultMap 和 `#{}` 中都要写 `typeHandler=...` |
| 逻辑删除 XML 不自动改写 | MP 仅改写 `select`，`delete` 标签不自动转软删 | 软删除用 `removeById`，XML 中写物理删除 |
| 批量插入性能差 | `foreach` 生成超长 SQL | 分批（如 500 条一次），或用 `InsertBatchSomeColumn` |
| 列名冲突 | 联表多表同名列 | 所有列用 `AS` 别名，resultMap 中 `column` 对应别名 |
