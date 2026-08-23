# mybatis-plus-dev v2.4.0 达尔文验证报告（实跑 + 双盲评 + 仲裁）

> **验证日期**：2026-08-23
> **版本**：v2.3.1 → v2.4.0
> **方法**：对照本地真实 jar（MP 3.5.17 / 3.5.16 / 3.5.5 + Maven Central 3.4.3 + jsqlparser 5.2，javap 签名 + 二进制串搜）核实全部疑点 API → 修复 → 三层验证（实跑 + 双盲评标签反转 + 仲裁）。
> **结论**：✅ **PASS** —— 实跑 20/20；双盲评 A +112 / B +117 方向完全一致；仲裁约 120 条证据 0 虚构、棘轮 PASS。本轮发现并修复 **5 处 API 级事实错误**（均不在上轮实跑覆盖范围内）。

## 〇、三层验证结构

| 层 | 角色 | 独立性 |
|----|------|--------|
| 1 | 实跑（fixtures 扩展，20 测试，SpringBoot 3.5.0 + MP 3.5.17 + H2 + JDK 21） | 编译 + 运行期语义 |
| 2 | 盲评 A（version1=2.3.1 / version2=2.4.0）+ 盲评 B（versionA=2.4.0 / versionB=2.3.1，标签反转） | 各自只读 rubric + prompts + 两份盲化快照，不知对方存在；报告开头贴 frontmatter 字面值自证（上轮 blind-B 标签缺陷的改进项） |
| 3 | 仲裁 | 读两份盲评 + 真标签快照，独立 grep 抽查核实 + 查漏 + 棘轮判定 |

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

## 三、双盲评结果（标签反转，两 agent 独立）

### 总分对比

| | Agent A | Agent B | 一致性 |
|---|---|---|---|
| v2.3.1 | 1230/1400（回归 765 / 对抗 465） | 1200/1400（回归 735 / 对抗 465） | B 略严，尺度差 |
| v2.4.0 | 1342/1400（回归 770 / 对抗 572） | 1317/1400（回归 748 / 对抗 569） | 同上 |
| **Δ（2.4.0−2.3.1）** | **+112** | **+117** | ✅ 方向完全一致 |

**增益结构两报告一致**：对抗集贡献 +104~107（五处 API 修正各就各位——数据权限真实签名、两参 lambda、check 不抛异常且消除与 06-page 的自相矛盾、删虚构 MybatisPlusLang、删虚构 keywordFit）；回归集 +5~13（修剪无退步，description 报错触发词有小幅正贡献）。

### 修剪回归的特别盯点（rubric 预设三处，双报告均通过）

- T1：01-start 收敛后 SB2/SB4/JDK8 的 artifactId 指引零跳转可达 ✅
- T6：路由提醒列删除后枚举判据经强约束 #9 / 03-entity §7 可达 ✅
- T8：「组合场景」块删除后多数据源规则经路由 11 行 / 11-transaction §6 可达 ✅

A 仅 T3/T4 各 −1（D7 主观微扣）；B 全部 Δ≥0。两份完整逐条表见 `blind-A.md` / `blind-B.md`。

## 四、仲裁结论：PASS

- **方法自证**：两份盲评 frontmatter 字面值与快照实测一致；盲化目录与真标签快照 14 文件 md5 全量相同，无标签错位（上轮 blind-B 标签缺陷未复发——「贴 frontmatter 为证」的改进项生效）。
- **证据抽查**：合计约 120 条（对抗集 36 条全抽 + 回归集抽样），**虚构 0 条**；仅 3 处行号/引文微偏，结论均成立。
- **独立查漏**：七项旧口径 grep 全 0 残留；强约束编号引用语义完好；13-migration 重编号无旧引用残留；SB2/SB4/JDK8 零跳转可达。双盲评共同漏报仅元信息级（非阻断）：4 个文件混入 CRLF 行尾（建议下轮统一 EOL）、01-start 坐标钉 3.5.17（可辩护——写作时即为 Maven Central latest）。
- **棘轮判定**：回归集无实质退步（A 的 -1×2 均为 D7 主观微扣）+ 对抗集六条全部达预期 + 实跑 20/20 佐证 + 新引入阻断问题 0 → **PASS，v2.4.0 保留，棘轮前进**。

## 五、一致性自查（AGENTS.md 防回归清单）

- 旧口径 grep 0 残留：`ExecutionStatement`/`DataPermissionRule`/`MybatisPlusLang`/`keywordFit`/`并抛异常`/`组合场景阅读顺序`/`版本注意`/`重点看`/`核心价值`
- 强约束编号引用无错位：07-plugin 的 #7/#10、12-dbtype 的 #6、05-wrapper 的 #4 全部指向未变主题（#4/#5 仅追加判据，#12 为纯新增）
- jsqlparser 规则在 SKILL.md 内 6 处→3 处（版本与依赖真值 / 主动行为触发 / 自检清单）
- 13 个 reference 全部仍被决策路由表覆盖；13-migration 重编号后 §2.2 引用无残留

## 六、方法学备注

本轮最大教训与上轮 v2.3.0（eq 传 null 语义 bug）同源：**未被实跑覆盖的区域会积累虚构 API**。上轮 17 项测试集中在 05-wrapper/强约束 #3/#4/#6/#9/#11，07-plugin 的两个插件示例、13-migration 的 breaking change 表、SqlInjectionUtils 语义全部在盲区。下轮扩展方向：02-config 插件链全量行为、11-transaction 失效场景实证。

另：Git Bash 下 `grep -l`（不带 `--text`）会静默跳过 class 二进制文件，曾导致「eqOrIsNull 不存在于 3.5.17」的假阴性结论（后经 `grep --text` 复核推翻）——二进制搜索必须显式 `--text`；正则中 `Page\$` 的 `$` 是行尾锚，匹配文件名应用 `Page.` 而非 `Page\$`。

## 七、产物清单

- `report.md` — 本报告（三层结果汇总）
- `rubric.md` — 9 维度评分标准 + 对抗集 T9-T14 判分锚点（含 jar 核实的 API 基准）
- `test-prompts.md` — 14 条 prompt（8 回归 + 6 对抗）
- `snapshots/v2.3.1/`、`snapshots/v2.4.0/` — 两版隔离快照（git show fae36a2 / 工作树）
- `snapshots/version{1,2,A,B}/` — 标签打乱副本（version1=v2.3.1/version2=v2.4.0；versionA=v2.4.0/versionB=v2.3.1）
- `blind-A.md`、`blind-B.md` — 两份独立盲评（开头贴 frontmatter 自证）
- `arbitration.md` — 仲裁报告（约 120 条证据核实 + 查漏 + 棘轮判定）
- `../fixtures/maven-test/` — 实跑项目（20 测试；本轮新增 PluginV240Test 3 项）
