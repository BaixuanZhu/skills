# 条件构造器 Wrapper

## 1. 字段引用方式与 Wrapper 能力边界

### 1.1 字段引用：必须用方法引用（Lambda）

```java
// ✗ 禁止：字符串字段名硬编码，重构改名无校验
new QueryWrapper<User>().eq("name", "Tom").ge("age", 18);

// ✓ 必须：方法引用，编译期检查字段
new LambdaQueryWrapper<User>().eq(User::getName, "Tom").ge(User::getAge, 18);
```

Lambda 用实体 getter 引用，字段改名时**编译报错**而非运行时 SQL 错误（`Unknown column`）；字符串字面量与实体属性无关联，IDE/编译器都无法追踪 rename。

**例外**：动态列名 / 动态表名 / 方言函数等**运行时才知道的列**，Lambda 无法表达，此时用 `QueryWrapper` / `UpdateWrapper` 字符串形式 + 注释说明理由，且拼接外部输入走 §5 `{0}` 占位防注入。

### 1.2 Wrapper 能力边界——超界转 XML

Wrapper 适合**单表 + 标准比较/排序/聚合条件**（`eq`/`ne`/`gt`/`lt`/`like`/`in`/`between`/`isNull`/`orderBy`/`groupBy`/`having` …）。以下场景 Wrapper **表达不了**，必须改写 XML（见 `10-xml.md`）：

| 场景 | 为什么 Wrapper 不行 |
|---|---|
| **联表**（JOIN，含子查询关联） | Wrapper 是单表构造器，硬堆 join 语义不可读且分页改写易错 |
| **窗口函数**（`ROW_NUMBER()`/`RANK()`/`SUM() OVER(...)`） | 无对应 API，`apply` 拼字符串失去类型安全与可移植性 |
| **聚合函数 + GROUP BY/HAVING**（`SUM(cnt)`/`COUNT(DISTINCT …)`） | 聚合结果需专用 resultMap 映射计算列，Wrapper 实体映射不适用 |
| **数据库专有函数 / 复杂表达式**（`DATE_FORMAT()`/`JSON_EXTRACT()`/`CASE WHEN`） | 跨库不可移植（`DATE_FORMAT` 在 Oracle 报错），应封装在 XML 中按库分支 |
| **自定义列别名 / 投影计算列**（`amount*2 AS double_amount`） | 实体无对应属性，需 resultMap + 计算列映射 |

```java
// ✗ 禁止：用 apply/last 拼 SQL 函数片段
w.apply("ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY id) = 1")
 .last("GROUP BY dept_id HAVING COUNT(*) > 5");

// ✓ 改写 XML（见 10-xml.md）
```

用 `apply()` / `last()` 拼函数片段是反模式：注入风险 + 跨库不可移植 + 语义不可读（见 `08-antipattern.md` #25）。

## 2. apply 与 SQL 注入防护（重点）

```java
// ❌ 危险：字符串拼接，可被注入
w.apply("date_format(create_time,'%Y-%m-%d') = '" + inputDate + "'");

// ✅ 安全：check 拦截恶意输入 + {0} 占位参数化
if (SqlInjectionUtils.check(inputDate)) {
    throw new IllegalArgumentException("非法输入");
}
w.apply("date_format(create_time,'%Y-%m-%d') = {0}", inputDate);
```
> `SqlInjectionUtils.check(String)` 返回 boolean（true=疑似注入），**自身不抛异常、不返回安全化后的值**——必须由调用方 `if (check(x)) throw` 拦截，裸调用 `check(x);` 会被编译/告警忽略返回值，校验形同虚设。拦截后用 `{0}` 占位符传原值（PreparedStatement 参数化）。任何把外部输入拼进 SQL 片段的地方都照此处理。

## 3. last 慎用

`last("limit 1")` 直接拼接在 SQL 末尾，会**覆盖** MP 自己生成的分页 / 排序，且同样有注入风险。非必要不用。

## 4. 空值语义（重点）

- **`eq / ge / like ...` 传 `null` 不会忽略条件**：默认 `condition=true`，生成 `col = NULL`，而 `NULL = NULL` 在 SQL 中为 unknown → **匹配 0 行**（不是"忽略返回全部"，也不是"查到 null 行"）。
- 想条件性跳过：用三参重载 `eq(name != null, User::getName, name)`（`condition=false` 时该条件不加入 SQL）。
- 想查"字段 IS NULL"：用 `isNull(...)`；3.5.17+ 也可用 `eqOrIsNull(col, val)`（值为 null 时自动转 IS NULL）。
- **集合参数例外**：`in(col, list)` / `allEq(map)` 当集合/Map 为空时，对应条件**才会**自动跳过。

```java
// ❌ name 为 null 时生成 WHERE name = NULL，匹配 0 行（非忽略）
w.eq(User::getName, name);

// ✓ 条件性跳过：name 为 null 时 condition=false，不拼该条件
w.eq(name != null, User::getName, name);

// ✓ 正确表达"name 为空"
w.isNull(User::getName);
```

> 此前版本曾误记「eq 传 null 自动被忽略」——经实跑核实不成立。

## 5. Wrapper 不可复用

同一 `Wrapper` 实例多次 `selectList` 会**叠加**条件。每次查询 `new` 一个新的。

```java
// ❌ 复用导致第二次查询条件翻倍
LambdaQueryWrapper<User> w = ...;
mapper.selectList(w); mapper.selectList(w);

// ✅
mapper.selectList(new LambdaQueryWrapper<User>().eq(User::getAge, 18));
```
