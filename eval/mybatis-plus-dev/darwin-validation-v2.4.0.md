# mybatis-plus-dev v2.4.0 达尔文实跑验证

> **验证日期**：2026-08-23
> **版本**：v2.3.1 → v2.4.0
> **方法**：对照本地真实 jar（MP 3.5.17 / 3.5.16 / 3.5.5 + Maven Central 3.4.3 + jsqlparser 5.2，javap 签名 + 二进制串搜）核实全部疑点 API → 修复 → 在上轮 fixtures（SpringBoot 3.5.0 + MP 3.5.17 + H2 + JDK 21）扩展实跑。
> **结论**：**20/20 测试 PASS**（上轮 17 项回归零退化 + 本轮新增 3 项）。本轮发现并修复 **5 处 API 级事实错误**（均不在上轮实跑覆盖范围内）。

## 一、本轮改动（v2.4.0）

### A. API 事实修正（功能性，5 处）

| # | 位置 | v2.3.1 所写 | 真实 API（核实方式） | 修复 |
|---|---|---|---|---|
| 1 | 07-plugin §4 | `MultiDataPermissionHandler.getSqlSegment(ExecutionStatement)` 返回 `List<DataPermissionRule>`，`rule.setColumn/setExpression`，`InExpression(col, list, false)` 三参 | 真实签名 `getSqlSegment(Table, Expression, String)` 返回**单个 Expression**；`ExecutionStatement` / `DataPermissionRule` 类不存在（javap jsqlparser jar 全类清单） | 整段示例按真实 API 重写（含 import 行），反模式行同步改 |
| 2 | 13-migration #3/§2.2/步骤5 | `Page.MybatisPlusLang` 3.5.0 移除（breaking change） | Page 在 3.4.3/3.5.5/3.5.17 从无内部类；3.4.3 全 jar 二进制搜零命中；全网零命中——**从未存在** | 删表行、§2.2 整节、升级步骤 5，重编号 |
| 3 | SKILL 强约束#7 + 05 §5 + 08 #5 | 「`check` 返回 boolean **并抛异常**」 | `SqlInjectionUtils.check(String)` 只返回 boolean、无 throws（javap core jar）；06 §5 的 `if (check(x)) throw` 用法本就正确 | 统一为 `if (check(x)) throw` 调用方拦截模式；裸调用明确标注禁止 |
| 4 | 07-plugin §3 | `tableName -> ...` 单参 lambda | `TableNameHandler.dynamicTableName(String sql, String tableName)` 两参（javap extension jar） | 改两参 lambda + 注明接口签名 |
| 5 | 12-dbtype §4 | 「DbType 内置 keywordFit 关键字转义」 | DbType 枚举无 keywordFit（javap annotation jar 全方法清单） | 改为「保留字列名无自动转义，引用符手写」 |

核实中同时验证为**准确**的既有内容：`eqOrIsNull` 确为 3.5.17 新增（3.5.16/3.5.5 均无，05 §7 的「3.5.17+」门槛正确）；07 §2 TenantLine 三方法与真实接口一致；`InsertBatchSomeColumn` 真实存在。

### B. 冗余修剪（对照用户目视三项 + java-coding-guide-pro v3.5.0 轮标准）

1. **路由表「关键提醒」列删除**：13 行中约 10 行是 20 行上方「核心强约束」的复述（05 行一格塞 4 条），且已现口径漂移（Wrapper 超界五项枚举在 SKILL 内 4 处 3 口径）。独占判据并入：#4 加「全局 update-strategy: ALWAYS 误清数据」、#5 加「唯一索引含 deleted」、新增 **#12 自定义 XML 分页**（返回 IPage/入参非 null/ORDER BY 写 XML）。表变 2 列只管路由；自检清单保留（执行时机非阅读冗余）并补 #12 项（9→10 项）。
2. **删「组合场景阅读顺序」块**：自我矛盾（机制/落地分类被自身 6 例违反）+ 悬空指针（「事务+多数据源→后 02」——02-config 无多数据源内容）+ 6 组示例对是路由表微缩复述；两个百行文件组合场景本会全读，顺序不影响产出。
3. **版本号集中化**：`3.5.17` 从 14 处降为 4 处（SKILL 真值源 1 + 01 XML 2 + 05 §7 API 门槛 1——该门槛准确故保留）。删「版本注意」节（3 要点均他处可达）；01-start 三 starter 块收敛为 SB3 一块 + SB2/SB4 一行换用说明，jsqlparser 同理（5 个 version 标签→2 个）。

### C. 小项

- 03 §4 与 05 §2 重复的置 null 代码块去重（03 改指针）
- 04 §3 ↔ 11 §4 互加指针（批量故事两半互相可见）
- 删维护者元信息标签：08 标题「（核心价值）」、路由行「（重点看）」、05 §7「（重点·实跑验证）」→「（重点）」、05 §7 纠正注的「MP 3.5.17 实跑 + 见 eval/」→「经实跑核实」

## 二、实跑验证（20/20 PASS）

```
[INFO] Tests run: 17, Failures: 0, Errors: 0, Skipped: 0 -- in com.eval.darwin.WrapperV230Test
[INFO] Tests run: 20, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

### 新增测试（PluginV240Test，3 项）

| # | 测试方法 | 验证点 | 对应修复 |
|---|---|---|---|
| 18 | `dataPermission_真实API_返回单个Expression` | MultiDataPermissionHandler 真实签名编译 + 非业务表返回 null + `new InExpression(new Column(..), new ExpressionList(..))` 生成 dept_id IN 条件 + 带 handler 构造器存在 | A1 |
| 19 | `dynamicTableName_两参handler_表名替换生效` | 两参 `(sql, tableName) ->` lambda 匹配 TableNameHandler 接口 + `changeTable` 表名替换生效 | A4 |
| 20 | `sqlInjectionUtils_check只返回boolean_不抛异常` | 注入特征串 `check` 返回 true **且不抛异常**、正常日期串返回 false、`if (check) throw` 拦截模式行为正确 | A3 |

### 回归（上轮 17 项全绿）

WrapperV230Test 17 项（Lambda 方法引用/能力边界/XML 改写/分页插件/空值语义/eqOrIsNull/枚举映射/Wrapper 复用）零退化。

## 三、一致性自查（AGENTS.md 防回归清单）

- 旧口径 grep 0 残留：`ExecutionStatement`/`DataPermissionRule`/`MybatisPlusLang`/`keywordFit`/`并抛异常`/`组合场景阅读顺序`/`版本注意`/`重点看`/`核心价值`
- 强约束编号引用无错位：07-plugin 的 #7/#10、12-dbtype 的 #6、05-wrapper 的 #4 全部指向未变主题（#4/#5 仅追加判据，#12 为纯新增）
- jsqlparser 规则在 SKILL.md 内 6 处→3 处（版本与依赖真值 / 主动行为触发 / 自检清单）
- 13 个 reference 全部仍被决策路由表覆盖；13-migration 重编号后 §2.2 引用无残留

## 四、方法学备注

本轮最大教训与上轮 v2.3.0（eq 传 null 语义 bug）同源：**未被实跑覆盖的区域会积累虚构 API**。上轮 17 项测试集中在 05-wrapper/强约束 #3/#4/#6/#9/#11，07-plugin 的两个插件示例、13-migration 的 breaking change 表、SqlInjectionUtils 语义全部在盲区。下轮扩展方向：02-config 插件链全量行为、11-transaction 失效场景实证。

另：Git Bash 下 `grep -l`（不带 `--text`）会静默跳过 class 二进制文件，曾导致「eqOrIsNull 不存在于 3.5.17」的假阴性结论（后经 `grep --text` 复核推翻）——二进制搜索必须显式 `--text`；正则中 `Page\$` 的 `$` 是行尾锚，匹配文件名应用 `Page.` 而非 `Page\$`。
