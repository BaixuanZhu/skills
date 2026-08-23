# 分页查询

## 1. Page 与 IPage

```java
// 第 1 页，每页 10 条
Page<User> page = new Page<>(1, 10);
IPage<User> result = userMapper.selectPage(page,
    new LambdaQueryWrapper<User>().ge(User::getAge, 18));

result.getRecords();   // 当前页数据
result.getTotal();     // 总记录数
result.getPages();     // 总页数
result.getCurrent();   // 当前页
```

## 2. 前提：分页插件已配置

分页依赖 `MybatisPlusInterceptor` + `PaginationInnerInterceptor`（见 `02-config.md`）。
未配置时 `selectPage` 返回的是**全量数据**（`total` 错误或仍为 0），**不会报错**——这是最隐蔽的坑。

## 3. 自定义 count

```java
// 不查总数（只返回列表，提升性能）
Page<User> page = new Page<>(1, 10, false);   // 第三参 searchCount=false

// 自定义 count 语句：在分页 statementId 后加 _mpCount
// <select id="selectPageVo_mpCount" ...>
```

## 4. 联表分页（放 XML）

MP 单表分页简单，但**联表分页必须写 XML**：

```java
// Mapper
IPage<UserVo> selectUserPage(IPage<UserVo> page, @Param("state") Integer state);
```
```xml
<select id="selectUserPage" resultType="com.xxx.UserVo">
    SELECT u.id, u.name, d.dept_name
    FROM user u LEFT JOIN dept d ON u.dept_id = d.id
    WHERE u.state = #{state}
</select>
```
- 入参 `IPage` **不可为 null**（MP 靠它改写分页）。
- XML 中如需取分页参数，用 `page.属性`（如 `page.size`）；联表建议给表 / 字段加别名。
- 若 Mapper 方法返回 `List` 而非 `IPage`，MP 不会自动分页；需改为返回 `IPage`，或手动 `page.setRecords(list)` 再返回 `page`。

## 5. 排序与注入

前端传入排序字段时，严禁直接拼 `orderBy ${sort}`。校验白名单或用 `SqlInjectionUtils.check(...)`：

```java
if (SqlInjectionUtils.check(sortField)) {
    throw new IllegalArgumentException("非法排序字段");
}
```
