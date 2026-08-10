# mybatis-plus-dev v2.3.0 达尔文实跑验证

> **验证日期**：2026-08-10
> **版本**：v2.2.1 → v2.3.0
> **方法**：搭最小 SpringBoot 3.5.0 + MyBatis-Plus 3.5.17 + H2 项目，实跑 JUnit 测试验证技能中所有代码片段的编译性与语义正确性（非空想）。
> **结论**：**17/17 测试 PASS**。实跑过程中发现并修正 1 个既有事实性 bug（§7 空值语义）。

## 一、验证环境

| 组件 | 版本 |
|---|---|
| JDK | 21 |
| SpringBoot | 3.5.0 |
| MyBatis-Plus | 3.5.17 |
| mybatis-plus-jsqlparser | 3.5.17 |
| H2 | 2.x（SpringBoot 托管，MySQL 模式） |
| Lombok | SpringBoot 托管 |

## 二、本次改动（v2.3.0）

针对两个实际开发痛点（Agent 不用方法引用 + 该写 XML 时硬堆 Wrapper 拼函数），统一为「Wrapper 能力边界」判据缺失的根因：

1. **强约束 #3 重写**：从「联表进 XML」扩展为完整 Wrapper 能力边界（联表/窗口/聚合+GROUP BY-HAVING/专有函数/计算列 → XML）。
2. **新增强约束 #11**：字段引用必须用方法引用（Lambda），字符串字段名仅限动态列名例外。
3. **05-wrapper.md §1 重写 + 新增 §2**：字段引用（禁止→必须）+ 能力边界；补 LambdaUpdateWrapper 覆盖更新侧。
4. **08-antipattern.md 新增 #24/#25**：字符串字段名 + SQL 函数硬堆 Wrapper。
5. **删除 10-xml.md §9**：`@Select` 与 XML 收口为单一事实源（XML）。
6. **实跑发现并修正 §7 空值语义 bug**（见下文第三节）。

## 三、实跑发现：§7 空值语义事实性 bug（关键）

### 现象

测试 `eq传null条件被忽略` 初版断言 `all.size() >= 5`（预期 `eq(col, null)` 被忽略，返回全部）。实跑返回 **0 条**。

### 根因（MP 官方文档核实）

技能原文（v2.2.1 §7）：
> `eq / ge / like ...` 传入 null 时，该条件**自动被忽略**（不加入 SQL）。

**MP 3.5.17 实际行为**（官方文档 `baomidou.com/guides/wrapper/` 明确）：
- `eq(col, val)` 默认 `condition=true`，无条件生成 `col = ?`，传 null 即 `col = NULL`。
- SQL 中 `NULL = NULL` 为 unknown → **匹配 0 行**（既非忽略，也非查到 null 行）。
- 要条件性跳过：三参重载 `eq(name != null, User::getName, name)`（`condition=false` 时不拼）。
- 要查 IS NULL：`isNull(col)`；3.5.17+ 新增 `eqOrIsNull(col, val)`（值为 null 自动转 IS NULL）。
- **集合参数例外**：`in(col, list)` / `allEq(map)` 集合为空时才自动跳过（标量 eq 不在此列）。

### 修正

- **05-wrapper.md §7** 重写为正确语义 + 三参重载正解 + `eqOrIsNull` + 集合例外说明，并加「此前版本曾误记，经实跑+官方文档核实」注。
- **08-antipattern.md #9** 同步修正（原「后者会被忽略」改为「生成 `deleted = NULL` 匹配 0 行」）。
- 新增 3 个测试验证修正后的语义：
  - `eq传null生成等于NULL匹配0行`（验证错误行为确实如此）
  - `eq三参重载condition为false时跳过`（验证正解）
  - `eqOrIsNull值为null时转ISNULL`（验证 3.5.17+ 新 API）

> **价值印证**：这正是达尔文评估「实跑测试，不要空想」的价值——一个存活了多个版本的事实性错误，被一次真实编译运行揪出。

## 四、测试用例清单（17 项）

| # | 测试方法 | 验证点 | 对应技能内容 |
|---|---|---|---|
| 1 | `lambdaQueryWrapper_方法引用_查询正确` | Lambda + 方法引用查询单条 | 强约束 #11 / 05 §1.1 / antipattern #24 正例 |
| 2 | `lambdaQueryWrapper_链式条件` | eq/ge/orderByDesc 链式 | 05 §3 |
| 3 | `lambdaQueryWrapper_select投影` | select(SFunction...) 部分字段 | 05 §4 |
| 4 | `lambdaUpdateWrapper_set置null` | LambdaUpdateWrapper.set 置 null | 强约束 #4 方法引用版 / 05 §2 / antipattern #2 |
| 5 | `lambdaUpdateWrapper_setSql原生片段` | setSql("version = version + 1") | 05 §2 |
| 6 | `聚合查询走XML` | GROUP BY + HAVING → XML | 强约束 #3 / antipattern #25 |
| 7 | `窗口函数走XML` | ROW_NUMBER() OVER → XML | 强约束 #3 / antipattern #25 |
| 8 | `联表分页走XML` | IPage 非null，MP 改写 LIMIT+COUNT | 强约束 #3 / 06-page §4 |
| 9 | `分页插件生效` | selectPage total 正确，非全量 | 强约束 #6 / 02-config §1 |
| 10 | `eq传null生成等于NULL匹配0行` | eq(col,null) 匹配 0 行（实跑纠正） | 05 §7（修正后） |
| 11 | `eq三参重载condition为false时跳过` | 三参重载条件性跳过（正解） | 05 §7（修正后） |
| 12 | `eqOrIsNull值为null时转ISNULL` | 3.5.17+ eqOrIsNull 转 IS NULL | 05 §7（修正后） |
| 13 | `查空值用isNull` | isNull 查 age=null 记录 | 05 §7 / antipattern #9 |
| 14 | `枚举映射正确` | @EnumValue 数据库 1/2 → MALE/FEMALE | 强约束 #9 / 03-entity §7 |
| 15 | `枚举字段作为查询条件` | eq(UserDO::getGender, GenderEnum.MALE) | 强约束 #9 / #11 |
| 16 | `wrapper不可复用_每次new新的` | 每次 new 新实例结果一致 | 05 §8 / antipattern #8 |
| 17 | `方法引用编译期检查` | Wrappers.lambdaQuery().eq(::getter) 编译通过 | 强约束 #11（编译期价值） |

## 五、实跑结果

```
[INFO] Tests run: 17, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 3.948 s
[INFO] BUILD SUCCESS
```

全部 17 项 PASS。验证覆盖：强约束 #3/#4/#6/#9/#11、05-wrapper.md §1-§8 全部章节、08-antipattern.md #2/#8/#9/#24/#25。

## 六、实跑环境陷阱记录

1. **H2 schema.sql 重复 INSERT**：`CREATE TABLE IF NOT EXISTS` + `INSERT` 在 `DB_CLOSE_DELAY=-1` 下跨测试累加数据。修正：改为 `DROP TABLE IF EXISTS` + `CREATE TABLE`（每次连接重建）+ 类级 `@Transactional`（方法间隔离）。
2. **insert null 字段不写入**：MP insert 默认 `NOT_NULL` 策略，`setDeleted(null)` 不写入 SQL，H2 DEFAULT 0 生效。要强制置 null 需 `LambdaUpdateWrapper.set`（正是强约束 #4 场景）。
3. **中文测试方法名 + `-Dtest=`**：Git Bash 下传中文方法名给 mvn.cmd 编码丢失，单测指定失败。解法：全量跑，从日志 grep。

## 七、后续建议

- 本次为**实跑验证**（编译 + 运行期语义），未做独立盲评（prompt 对抗）。若要完整达尔文三层，可补 5-10 条 test-prompt + 两层独立 agent 盲评。
- §7 bug 修正说明 v2.2.1 及更早版本的 `05-wrapper.md §7` 与 `08-antipattern.md #9` 存在事实性错误，发布 v2.3.0 时应在 changelog 点明此修正。
