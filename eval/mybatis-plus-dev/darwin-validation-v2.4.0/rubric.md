# 评分标准（v2.4.0 达尔文盲评用）

> 你是独立盲评 agent。你**不知道**两个版本哪个是旧/新，也**不知道**技能的修改历史。**只根据手里拿到的技能内容，对每个 test-prompt 给出判断。**
>
> 本次是 **v2.3.1 → v2.4.0** 的回归 + 对抗验证。共 14 条 prompt：T1-T8 回归集（确保修剪没让原场景退步）、T9-T14 对抗集（直击本轮五类 API 修正与三项修剪的根本原因）。

## 9 维度评分（SkillLens 风格，满分 100）

每个维度 0–12 分（D9 为 4 分），按"agent 拿着这套技能执行 prompt，能否产出合格结果"打分：

| 维度 | 权重 | 判分锚点 |
|------|------|---------|
| D1 触发精度 | 12 | description 里的关键词/场景，能否让 agent 在该用时用、不该用时不用 |
| D2 可发现性 | 12 | 想找的信息（命令/规则/范例），在合理跳转步数内能找到 |
| D3 覆盖完整 | 12 | prompt 涉及的知识点，技能是否有答案（无盲点） |
| D4 可执行性 | 12 | 给出的命令/代码/判据，agent 能否直接照做（不悬空、不模糊、**能编译**） |
| D5 防错/陷阱 | 12 | 隐蔽坑（不 fail loud 的错）是否点名 |
| D6 信息密度 | 12 | 有无冗余表达/重复内容/纯说理段落拖累 agent |
| D7 内部导航 | 12 | 路由表/交叉引用是否清晰，agent 知道下一步看哪 |
| D8 范围明确 | 12 | 不适用场景是否声明（不让 agent 越界） |
| D9 整体一致性 | 4 | 术语/规则是否前后一致、无自相矛盾 |

---

## 回归集（T1-T8）判分要点

这 8 条覆盖技能核心域。重点：**v2.4.0 的三项修剪（决策路由删「关键提醒」列、删「组合场景阅读顺序」块、版本号集中化）是否让这些场景退步**。修剪版把独占判据并入了「核心强约束」（#4 全局 ALWAYS 误清数据、#5 唯一索引含 deleted、新增 #12 自定义 XML 分页）。若某判据在修剪版两处都找不到 → D3/D5 扣分。两版同分属正常（改动没碰该场景）。

**特别盯**：
- T1（starter 选择 + JDK8）：修剪版 01-start 只保留一个完整依赖块；SB2/SB4/JDK8 用户的 artifactId 指引必须仍可达。
- T6（枚举）：决策路由表修剪版不再有「枚举 @EnumValue+@JsonValue；XML 每处 typeHandler」提醒——该判据必须能从核心强约束 #9 或 03-entity §7 找到。
- T8（排错）：「事务+多数据源」的「组合场景阅读顺序」块已删——多数据源规则必须仍能从路由表 11 行或 11-transaction §6 找到。

## 对抗集（T9-T14）判分要点

对抗集的目标是**验证真实 API 与语义**。判分时尤其关注：**某版本是否会给出编译失败的代码或语义错误的建议**。

### T9（数据权限插件）
用户要配 DataPermissionInterceptor 按部门过滤。
**判分锚点**：给出的示例代码必须与 MyBatis-Plus 3.5.x 真实 API 匹配——`MultiDataPermissionHandler` 的方法签名是 `getSqlSegment(Table table, Expression where, String mappedStatementId)` 返回**单个 Expression**（net.sf.jsqlparser）。若某版本示例使用了不存在的类（如 `ExecutionStatement`、`DataPermissionRule`）或不存在的签名（返回 `List<>`）→ D4 重扣（≤4 分，agent 照写编译失败）。示例含正确 import 行 → D4 加分。

### T10（按月分表）
用户要用 DynamicTableNameInnerInterceptor 做按月分表。
**判分锚点**：`TableNameHandler.dynamicTableName(String sql, String tableName)` 是**两参**函数式接口。单参 lambda（`tableName -> ...`）无法通过编译 → D4 重扣。两参写法 → 高分。

### T11（防注入校验怎么写）
用户问 `SqlInjectionUtils.check` 怎么用、apply 怎么传外部输入。
**判分锚点**：`check(String)` **只返回 boolean（true=疑似注入），自身不抛异常**。正确模式是 `if (SqlInjectionUtils.check(x)) throw ...` 由调用方拦截 + `{0}` 占位传原值。若某版本声称 check 会抛异常、或示例裸调用 `check(x);`（返回值被忽略，校验形同虚设）→ D3/D5 重扣（安全语义错误）。排序字段场景 `if (check(sortField)) throw` 是正确用法。

### T12（3.4.x 升级 3.5.x）
用户项目在 3.4.x，要升级。
**判分锚点**：升级步骤必须全部对应真实存在的类/配置。`PaginationInterceptor`→`MybatisPlusInterceptor`、引 jsqlparser、`IGNORED`→`ALWAYS` 都是真变更。若某版本的 breaking change 表或升级步骤中出现 `Page.MybatisPlusLang` 这类**不存在的类**（该项目从无此类）→ D3/D4 重扣（虚构 breaking change 误导排查）。3.4.x 勿引 jsqlparser 的提醒应在。

### T13（Oracle 项目适配）
用户要上 Oracle：分页、主键、保留字列名。
**判分锚点**：非 MySQL 显式 `DbType`；Oracle 无自增列 → `INPUT`+`@KeySequence` 或 `ASSIGN_ID`；保留字列名需手写引用符。若某版本声称 MP 的 DbType 内置 `keywordFit` 自动关键字转义 → D5 扣分（虚构能力，MyBatis-Plus 的 DbType 枚举无此方法）。

### T14（只读 SKILL.md 的分页链路）
假设 agent 只读 SKILL.md（不打开 reference）：新项目要分页，需要知道 ①引哪个额外依赖 ②插件怎么配 ③自定义 XML 分页方法怎么写。
**判分锚点**：①`mybatis-plus-jsqlparser`（v3.5.9+ 拆分，不引则静默失效）②`MybatisPlusInterceptor` + 分页最后 ③返回 `IPage` / 入参非 null。三者必须都能在 SKILL.md 本体找到（版本与依赖节/强约束/自检清单）。若修剪版丢了某条 → D2/D3 扣分。description 是否含分页相关触发词 → D1。

---

## 打分输出格式（每个 prompt 必填）

```
### Prompt Tx（一句话场景描述）
- 拿到的技能：版本 [X|Y]
- D1: x  D2: x  D3: x  D4: x  D5: x  D6: x  D7: x  D8: x  D9: x
- 该 prompt 小计: xx/100
- 关键依据（≤3 条，引用具体文件与行号/标题/代码块）:
  1. ...
  2. ...
  3. ...
- 扣分主因:
```

**铁律**：
- 每条依据必须能指向技能里的具体位置（行号 / 标题 / 代码块）。禁止泛泛说"覆盖全面"。
- **方法自证**：报告开头必须原样贴出你拿到的两份 SKILL.md 的 frontmatter `version:` 字面值，并声明你按版本字面值称呼它们、不猜新旧。
- D4（可执行性）：代码示例用了不存在的类/方法/构造器 → 重扣（≤4 分）。API 名称与签名正确性优先于代码长度。
- D6（信息密度）：同一规则在同一文件复述多遍、维护者元信息（"本技能写作时…"之类）、指向不存在主题的指针 → 扣分。
- **对抗集（T9-T14）特别规则**：某版本会产出**编译失败或语义错误**建议的，相应维度重扣（≤4 分），不能因"文字通顺"给中庸分。
- 不要因为版本号高低影响打分。版本号是元数据，与内容质量无关。你不知道 X/Y 哪个是 v2.3.1 哪个是 v2.4.0，按你看到的字面值打分即可，不要猜。
