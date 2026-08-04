# 条件构造器 Wrapper

## 1. QueryWrapper vs LambdaQueryWrapper（推荐 Lambda）

```java
// 不推荐：字段名硬编码，重构易错
new QueryWrapper<User>().eq("name", "Tom").ge("age", 18);

// 推荐：方法引用，编译期检查字段
new LambdaQueryWrapper<User>().eq(User::getName, "Tom").ge(User::getAge, 18);
```
Lambda 用实体 getter 引用，字段改名时编译报错而非运行时 SQL 错误。

## 2. 常用条件

```java
LambdaQueryWrapper<User> w = new LambdaQueryWrapper<>();
w.eq(User::getName, "Tom")          // =
 .ne(User::getStatus, 0)            // !=
 .gt(User::getAge, 18)              // >
 .ge(...) .lt(...) .le(...)         // >= / < / <=
 .like(User::getName, "张")         // LIKE %张%
 .likeLeft(...) .likeRight(...)
 .in(User::getId, Arrays.asList(1, 2, 3))
 .between(User::getAge, 18, 30)
 .isNull(User::getDeleted)          // IS NULL
 .isNotNull(...)
 .groupBy(...) .having(...)
 .orderByDesc(User::getCreateTime);
```

## 3. 字段投影 select

```java
// 只查部分字段
mapper.selectList(
    new LambdaQueryWrapper<User>().select(User::getId, User::getName).eq(User::getAge, 18));

// 排除字段
.select(User.class, info -> !info.getColumn().equals("age"))
```

## 4. apply 与 SQL 注入防护（重点）

```java
// ❌ 危险：字符串拼接，可被注入
w.apply("date_format(create_time,'%Y-%m-%d') = '" + inputDate + "'");

// ✅ 安全：先校验后占位（check 检测到注入则抛异常，{0} 参数化防注入）
SqlInjectionUtils.check(inputDate);
w.apply("date_format(create_time,'%Y-%m-%d') = {0}", inputDate);
```
> `SqlInjectionUtils.check()` 返回 boolean（true=检测到注入并抛异常），**不返回安全化后的值**。正确流程：先 `check` 校验，再用 `{0}` 占位符传原值（PreparedStatement 参数化）。任何把外部输入拼进 SQL 片段的地方都照此处理。

## 5. last 慎用

`last("limit 1")` 直接拼接在 SQL 末尾，会**覆盖** MP 自己生成的分页 / 排序，且同样有注入风险。非必要不用。

## 6. 空值语义（重点）

- `eq / ge / like ...` 传入 `null` 时，该条件**自动被忽略**（不加入 SQL）。
- 想查“字段为 null”：用 `isNull(...)`，而非 `eq(field, null)`（后者会被忽略）。

```java
// 下面这句若 name 为 null，等价于无过滤
w.eq(User::getName, name);

// 正确表达“name 为空”
w.isNull(User::getName);
```

## 7. Wrapper 不可复用

同一 `Wrapper` 实例多次 `selectList` 会**叠加**条件。每次查询 `new` 一个新的。

```java
// ❌ 复用导致第二次查询条件翻倍
LambdaQueryWrapper<User> w = ...;
mapper.selectList(w); mapper.selectList(w);

// ✅
mapper.selectList(new LambdaQueryWrapper<User>().eq(User::getAge, 18));
```
