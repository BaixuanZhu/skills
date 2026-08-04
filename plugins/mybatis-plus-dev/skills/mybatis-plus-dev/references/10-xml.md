# MyBatis XML Mapper 编写指南

> MP 擅长单表 CRUD，复杂 / 联表查询应写 XML。本章覆盖从配置到编写的完整链路，确保 Agent 能产出一个**配置正确、结构规范、可直接运行**的 XML Mapper。

## 1. mapper-locations 配置

MP 默认扫描 `classpath*:/mapper/**/*.xml`。若自定义路径，需在 `application.yml` 中声明：

```yaml
mybatis-plus:
  mapper-locations: classpath*:/mapper/**/*.xml
```

> ⚠️ 不配此项且 XML 不在默认路径下时，`Invalid bound statement (not found)` 报错。
> 多个路径用逗号分隔：`classpath*:/mapper/**/*.xml,classpath*:/mybatis/*.xml`。

XML 文件放 `src/main/resources/mapper/` 下，按业务分包（如 `mapper/user/UserMapper.xml`）。

## 2. XML 基本结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.example.mapper.UserMapper">

    <!-- resultMap 定义 -->
    <resultMap id="userResultMap" type="com.example.entity.User">
        <id property="id" column="id"/>
        <result property="name" column="user_name"/>
        <result property="age" column="age"/>
    </resultMap>

    <!-- 查询 -->
    <select id="selectById" resultMap="userResultMap">
        SELECT id, user_name, age FROM sys_user WHERE id = #{id}
    </select>

</mapper>
```

**关键规则**：
- `namespace` 必须与 Mapper 接口**全限定名完全一致**（如 `com.example.mapper.UserMapper`）。
- 每个 `<select>/<insert>/<update>/<delete>` 的 `id` 必须与 Mapper 接口方法名**一致**。
- `resultType` 用于自动映射（列名 = 属性名，驼峰自动转换）；`resultMap` 用于显式映射（列名 ≠ 属性名、联表嵌套、typeHandler）。

## 3. #{} vs ${}（防注入核心）

```xml
<!-- ✅ #{} 预编译占位，PreparedStatement 参数化，防注入 -->
<select id="selectByName" resultMap="userResultMap">
    SELECT * FROM sys_user WHERE user_name = #{name}
</select>

<!-- ❌ ${} 字符串拼接，有 SQL 注入风险 -->
<select id="selectByNameUnsafe" resultMap="userResultMap">
    SELECT * FROM sys_user WHERE user_name = '${name}'
</select>
```

| 写法 | 机制 | 安全 | 何时用 |
|---|---|---|---|
| `#{name}` | PreparedStatement `?` 占位 | ✅ | **几乎所有场景** |
| `${name}` | 直接字符串拼接 | ❌ | 仅排序字段 / 表名等**结构值**，且必须白名单校验 |

```xml
<!-- 排序字段：${} 不可避免，必须白名单校验 -->
<select id="selectPageSorted" resultMap="userResultMap">
    SELECT * FROM sys_user
    <where>
        <if test="name != null and name != ''">
            AND user_name LIKE CONCAT('%', #{name}, '%')
        </if>
    </where>
    ORDER BY ${sortField} ${sortOrder}
    <!-- sortField / sortOrder 必须在 Service 层白名单校验 -->
</select>
```

## 4. 动态 SQL 标签

### 4.1 if

```xml
<select id="selectByCondition" resultMap="userResultMap">
    SELECT * FROM sys_user
    <where>
        <if test="name != null and name != ''">
            AND user_name LIKE CONCAT('%', #{name}, '%')
        </if>
        <if test="age != null">
            AND age = #{age}
        </if>
        <if test="status != null">
            AND status = #{status}
        </if>
    </where>
</select>
```

### 4.2 where

`<where>` 自动处理首个条件的 `AND` / `OR` 前缀——条件全不满足时不生成 `WHERE`，有条件时自动去掉开头多余的 `AND`。

```xml
<!-- 等价手写 trim -->
<trim prefix="WHERE" prefixOverrides="AND |OR ">
    ...
</trim>
```

### 4.3 choose / when / otherwise（多条件分支）

```xml
<select id="selectByType" resultMap="userResultMap">
    SELECT * FROM sys_user
    <where>
        <choose>
            <when test="searchType == 'name'">
                AND user_name LIKE CONCAT('%', #{keyword}, '%')
            </when>
            <when test="searchType == 'phone'">
                AND phone = #{keyword}
            </when>
            <otherwise>
                AND email = #{keyword}
            </otherwise>
        </choose>
    </where>
</select>
```

### 4.4 foreach（批量 / IN 查询）

```xml
<!-- IN 查询 -->
<select id="selectByIds" resultMap="userResultMap">
    SELECT * FROM sys_user
    WHERE id IN
    <foreach collection="ids" item="id" open="(" separator="," close=")">
        #{id}
    </foreach>
</select>

<!-- 批量插入 -->
<insert id="batchInsert">
    INSERT INTO sys_user (user_name, age, email) VALUES
    <foreach collection="list" item="u" separator=",">
        (#{u.name}, #{u.age}, #{u.email})
    </foreach>
</insert>
```

| 属性 | 说明 |
|---|---|
| `collection` | 入参集合名：`list`（List）、`array`（数组）、或 `@Param("ids")` 指定的名称 |
| `item` | 迭代变量名 |
| `open` / `close` | 生成 SQL 的首尾包裹符 |
| `separator` | 每次迭代间的分隔符 |

### 4.5 set（动态更新）

```xml
<update id="updateSelective">
    UPDATE sys_user
    <set>
        <if test="name != null and name != ''">user_name = #{name},</if>
        <if test="age != null">age = #{age},</if>
        <if test="email != null">email = #{email},</if>
    </set>
    WHERE id = #{id}
</update>
```

`<set>` 自动去掉末尾多余的逗号。等价 `<trim prefix="SET" suffixOverrides=",">`。

### 4.6 trim（灵活版 where/set）

```xml
<!-- 自定义前缀后缀裁剪 -->
<trim prefix="WHERE" prefixOverrides="AND |OR " suffixOverrides=",">
    ...
</trim>
```

## 5. resultMap 结果映射

### 5.1 基本映射

```xml
<resultMap id="userResultMap" type="com.example.entity.User">
    <id property="id" column="id"/>           <!-- 主键 -->
    <result property="name" column="user_name"/>
    <result property="age" column="age"/>
    <result property="createTime" column="create_time"/>
</resultMap>
```

- `<id>` 标记主键，MyBatis 用它做对象身份比较（嵌套结果去重依赖此标签）。
- `<result>` 普通字段映射。
- 若开 `map-underscore-to-camel-case: true`（默认），列名与属性名驼峰一致时可省略 `resultMap`，直接用 `resultType`。

### 5.2 联表一对一（association）

```xml
<resultMap id="userWithDeptResultMap" type="com.example.vo.UserVO">
    <id property="id" column="u_id"/>
    <result property="name" column="u_name"/>
    <association property="dept" javaType="com.example.entity.Dept">
        <id property="id" column="d_id"/>
        <result property="deptName" column="d_name"/>
    </association>
</resultMap>

<select id="selectUserWithDept" resultMap="userWithDeptResultMap">
    SELECT u.id AS u_id, u.user_name AS u_name,
           d.id AS d_id, d.dept_name AS d_name
    FROM sys_user u
    LEFT JOIN sys_dept d ON u.dept_id = d.id
    WHERE u.id = #{id}
</select>
```

### 5.3 联表一对多（collection）

```xml
<resultMap id="deptWithUsersResultMap" type="com.example.vo.DeptVO">
    <id property="id" column="d_id"/>
    <result property="deptName" column="d_name"/>
    <collection property="users" ofType="com.example.entity.User">
        <id property="id" column="u_id"/>
        <result property="name" column="u_name"/>
    </collection>
</resultMap>

<select id="selectDeptWithUsers" resultMap="deptWithUsersResultMap">
    SELECT d.id AS d_id, d.dept_name AS d_name,
           u.id AS u_id, u.user_name AS u_name
    FROM sys_dept d
    LEFT JOIN sys_user u ON u.dept_id = d.id
    WHERE d.id = #{deptId}
</select>
```

> ⚠️ 一对多查询必须用 `<id>` 标签做主键去重，否则嵌套结果合并时会产生重复行。

### 5.4 typeHandler 在 XML 中声明

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

## 6. 联表分页 XML（配合 IPage）

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

## 7. 增删改 XML 完整示例

```xml
<!-- 插入（含动态字段） -->
<insert id="insertUser" parameterType="com.example.entity.User" useGeneratedKeys="true" keyProperty="id">
    INSERT INTO sys_user
    <set>
        <if test="name != null and name != ''">user_name = #{name},</if>
        <if test="age != null">age = #{age},</if>
        <if test="email != null">email = #{email},</if>
        <if test="deptId != null">dept_id = #{deptId},</if>
    </set>
</insert>

<!-- 更新：`set` 内的 `<if>` 分支与上方插入完全一致，仅外层换 `<update>` 并加 `WHERE id = #{id}` -->

<!-- 批量插入 -->
<insert id="batchInsert" parameterType="java.util.List">
    INSERT INTO sys_user (user_name, age, email) VALUES
    <foreach collection="list" item="u" separator=",">
        (#{u.name}, #{u.age}, #{u.email})
    </foreach>
</insert>

<!-- 软删除（配合逻辑删除，直接用 MP 的 removeById 即可，无需 XML） -->
<!-- 物理删除 -->
<delete id="physicalDelete">
    DELETE FROM sys_user WHERE id = #{id}
</delete>
```

> `useGeneratedKeys="true" keyProperty="id"`：插入后自动回填自增主键到实体对象。
> MP 已开启逻辑删除时，XML 中的 `delete` 标签**不会被自动改写**为逻辑删除——需自行处理或用 MP 的 `removeById`。

## 8. 常见坑

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

## 9. XML vs @Select 注解

| 维度 | XML | `@Select` 注解 |
|---|---|---|
| 复杂度 | 支持动态 SQL 全套标签 | 复杂动态 SQL 需 `<script>` 包裹，可读性差 |
| 可维护性 | 独立文件，SQL 与 Java 分离 | SQL 嵌入 Java，修改需重新编译 |
| resultMap | 支持完整 resultMap / 嵌套映射 | 支持 `@Results`，但联表嵌套不便 |
| 适用 | **联表、动态条件、批量操作** | **简单单表查询、快速验证** |

> 约定：简单查询可用 `@Select`；联表、动态条件、批量操作一律写 XML。
