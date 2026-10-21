---
name: mybatis-plus-dev
description: >-
  MyBatis-Plus 开发助手。在 Java / Spring Boot 项目中开发任何数据库
  增删改查（CRUD）、分页查询、条件查询、Mapper / DAO / Service 层、实体类与表映射、
  联表 / 复杂查询写 XML、事务相关功能时使用本技能——无论用户是否提到 MyBatis-Plus
  （MyBatis-Plus / MyBatis Plus / MP / baomidou / CRUD / pagination / ORM / DAO / entity mapping）。
  次级触发信号——代码或 pom 中出现：mybatis-plus-boot-starter、
  extends BaseMapper / IService / ServiceImpl、
  QueryWrapper / LambdaQueryWrapper / LambdaUpdateWrapper、
  @TableName / @TableId / @TableField / @TableLogic、
  MybatisPlusInterceptor / MetaObjectHandler、
  selectPage / saveBatch / IPage、logic-delete-field / mapper-locations / @DS；
  用户任务词或报错出现：分页失效 / total 为 0 / 返回全量、更新后字段没变 / 字段置 null 不生效、
  逻辑删除 / 软删除、批量插入 / 批量导入 / saveBatch 慢、乐观锁、创建时间自动填充、
  多租户 / 数据权限 / 分表 / 动态表名、雪花 ID / 主键策略、枚举存数据库、联表查询、
  事务不回滚、Invalid bound statement (not found)。
  依赖含 mybatis-plus-* 或代码出现上述令牌时必须使用；纯 MyBatis、无 ORM 或 ORM 未知，
  先询问用户是否引入 MyBatis-Plus 再开发。
  不适用于：已使用 JPA / Hibernate 的项目（不建议迁移）、表结构设计 / DDL、纯 SQL 性能调优
  （连接池 / 索引 / 慢查询属 DBA 层）。
agent_created: true
version: 3.0.0
last_verified: "2026-10-21"
slug: mybatis-plus-dev
displayName: MyBatis-Plus 开发助手
---

# MyBatis-Plus 开发助手

面向日常 Java 开发的 MyBatis-Plus 编码助手。**推荐 3.5.x 最新版（全线适用）**，3.4.x 大部分兼容（差异处已注明）。
采用**完全本地自包含**策略：所有知识沉淀于本地 `references/`，运行时不依赖任何外部文档站点。

## 版本与依赖（先判 SpringBoot 版本）

| SpringBoot | starter 坐标 |
|---|---|
| 2.x | `mybatis-plus-boot-starter` |
| 3.x | `mybatis-plus-spring-boot3-starter` |
| 4.x (^3.5.13) | `mybatis-plus-spring-boot4-starter` |

- **切勿**同时引入 `mybatis` / `mybatis-spring-boot-starter` / `mybatis-spring`，会与 MP 版本冲突。
- **分页必引** `mybatis-plus-jsqlparser`（自 v3.5.9 起 `PaginationInnerInterceptor` 已从核心拆分，单独成依赖；否则分页静默失效）。JDK8 项目用 `mybatis-plus-jsqlparser-4.9`。

## 第 0 步：依赖探测与激活分支（收到数据库访问类任务先做这一步）

任务涉及增删改查、分页、条件查询、Mapper/DAO/Service 层、实体映射、事务等编码——**即使用户没提 MyBatis-Plus**——先检索项目依赖（在 `pom.xml` / `build.gradle` 中搜 `mybatis-plus`、`mybatis`、`spring-boot-starter-data-jpa`、`hibernate`）：

| 探测结果 | 动作 |
|---|---|
| 依赖含 `mybatis-plus-*` | 直接激活本技能，走下方流程 |
| 纯 MyBatis 原生（无 MP） | 按「部分适用」规则（仅 `10-xml.md` + `11-transaction.md`），同时**询问**用户是否引入 MyBatis-Plus（单表 CRUD 免写 SQL，与现有 XML 共存） |
| 无任何 ORM | **主动询问**用户是否引入 MyBatis-Plus；同意 → 按「版本与依赖」表 + `references/01-start.md` 引入后继续；拒绝 → 退出本技能，不再打扰 |
| 已使用 JPA / Hibernate | 告知不适用并退出，**不建议迁移** |

## 何时使用本技能

| 信号 | 判定 |
|------|------|
| Java/SpringBoot 项目中的 CRUD/分页/条件查询/Mapper 层/实体映射/事务任务（未指明框架） | 激活，先执行「第 0 步」依赖探测 |
| 依赖含 `mybatis-plus-*` / 代码 `extends BaseMapper` / `extends ServiceImpl` / 使用 Wrapper / `IService` / `saveBatch` / `selectPage` | 激活 |
| 提到 `@TableLogic` / `@TableField` / `@EnumValue` / `@Version` / `@TableId` / "MyBatis-Plus" / "MP" / "baomidou" | 激活 |
| 纯 MyBatis 原生（无 MP），仅问 XML / 事务 | 部分适用（仅 `references/10-xml.md` + `11-transaction.md`） |
| JPA / Hibernate（不建议迁移）/ 表结构设计 / DDL / 纯 SQL 调优 | 不适用 |

> **检查点**：判定为「不适用」→ 告知用户当前问题不在 MyBatis-Plus 范围，建议退出本技能。判定为「部分适用」→ 告知仅 `10-xml.md` + `11-transaction.md` 可参考，其余不适用，让用户确认是否继续。

## 核心强约束

1. **Wrapper 能力边界——超界转 XML**：Wrapper 只适合单表 + 标准比较/排序。以下必须写 XML：联表、窗口函数、`GROUP BY`/`HAVING` 聚合、数据库专有函数（`DATE_FORMAT`/`JSON_EXTRACT`/`CASE WHEN`）、计算列投影。用 `apply()`/`last()` 硬拼函数片段是反模式（注入风险 + 跨库不可移植）。

2. **插件顺序：分页永远最后**：`PaginationInnerInterceptor` 必须在所有会改写 SQL 的拦截器**之后**（多租户 → 数据权限 → 动态表名 → 乐观锁 → 防全表 → 分页）。顺序错的后果是 **COUNT 语句不被改写**，分页 total 不准或数据权限漏过滤。**非 MySQL（PG/Oracle/达梦/金仓）必须显式指定 `DbType`**，否则方言生成错误。另外 3.5.9+ 必须引 `mybatis-plus-jsqlparser`，不引则分页插件静默不工作。

3. **`updateById` 的 null 不更新**：根因是全局 `updateStrategy` 默认 `NOT_NULL`（见 `references/02-config.md` §6）。要置空用 `UpdateWrapper.set(...)` 或字段级 `@TableField(updateStrategy = ALWAYS)`。全局改 `ALWAYS` 会让所有 null 字段写库、可能误清数据——只允许字段级覆盖。

4. **逻辑删除的唯一索引必须含删除标记列**：`UNIQUE(username, deleted)`。否则删掉一条后同用户名再插入会撞唯一约束——被删的行其实还在表里。

5. **`SqlInjectionUtils.check()` 返回 boolean 且不抛异常**：裸调用等于没校验。必须 `if (SqlInjectionUtils.check(x)) throw new IllegalArgumentException(...)`。`apply` 拼接走 `{0}` 占位符，禁止字符串拼接。

6. **枚举在自定义 XML 的每一处都要声明 typeHandler**：resultMap、条件 `#{}`、插入 `#{}` 三处，漏一处就映射成 null 或报类型错误。MP 自动 CRUD 不需要声明。

7. **字段引用用方法引用（Lambda）**：`User::getName` 编译期校验，字段改名会编译报错；字符串字段名（`eq("name", ...)`）改名后不报错，只静默查错数据。例外是动态列名/表名——此时按第 5 条做占位符防护。

8. **自定义 XML 分页的方法签名**：返回 `IPage`（返回 `List` 则 MP 不改写分页，静默返回全量）、入参 `page` 非 null、`ORDER BY` 写在 XML 里。

9. **`@Transactional` 一律写 `rollbackFor = Exception.class`**：默认只回滚 `RuntimeException`，checked exception 不回滚且不报错。另外同类内部调用（`this.inner()`）不走 AOP 代理，事务静默失效——见 `references/11-transaction.md` §2。


## 决策路由（全部本地，无在线 fetch）

| 需求场景 | 读取文件 |
|---|---|
| 依赖与 starter 选择（boot2/3/4、`mybatis-plus-jsqlparser` 拆分） | `references/01-start.md` |
| 全局配置：插件链顺序与显式 DbType、逻辑删除全局、乐观锁、自动填充、防全表、**字段策略** | `references/02-config.md` |
| 实体映射：@TableId 策略、字段策略与 null、**枚举映射(@EnumValue/IEnum/@JsonValue)**、@Version、@TableLogic、JSON 字段 | `references/03-entity.md` |
| saveBatch 伪批量真相、null 更新语义、`selectObjs` 返回值易错点 | `references/04-crud.md` |
| Wrapper 字段引用方式与能力边界、apply 防注入、`last` 慎用、空值语义、不可复用 | `references/05-wrapper.md` |
| 分页插件前提、自定义 count、联表分页（必须返回 `IPage`）、排序注入 | `references/06-page.md` |
| 进阶插件：多租户 / 动态表名 / 数据权限 / 防全表 + 插件顺序 | `references/07-plugin.md` |
| **数据库适配：DbType/分页方言/主键策略/标识符引用符/逻辑删除函数/批量语法** | `references/12-dbtype.md` |
| **Agent 常见错误（症状入口，每条即一个失败模式）** | `references/08-antipattern.md` |
| SQL 日志开启、常见异常定位、分页失效排查清单 | `references/09-troubleshoot.md` |
| **MyBatis XML：mapper-locations / 结构 / `#{}` vs `${}` / resultMap+typeHandler / 联表分页 / 常见坑** | `references/10-xml.md` |
| **事务管理（@Transactional / 失效 7 场景 / saveBatch 事务 / 编程式 / 多数据源 / 超时）** | `references/11-transaction.md` |

## 使用流程

1. **确认 MP 适用性**：先执行「第 0 步：依赖探测与激活分支」；依赖缺失时主动询问是否引入 MyBatis-Plus。不适用 → 告知用户并建议退出；部分适用 → 告知范围并让用户确认；正常 → 继续。
2. **检查项目约定**：见下节「项目播种」。项目没有 `.claude/rules/mybatis-plus.md` 或文件首行版本落后时，**提议**播种（不要直接写文件，先问）。
3. **定位 reference**：查上方「决策路由」表，读对应文件。
4. **编码遵循强约束**：先看 9 条核心强约束，再读 reference 给代码。
5. **遇异常先查排错**：`references/09-troubleshoot.md` + `references/08-antipattern.md`。装了插件版时，构建失败后 hook 会自动注入症状指针，按指针读文件即可。
6. **输出前自检（10 项）**：
   - [ ] starter 坐标对应 SpringBoot 版本？（2.x / 3.x / 4.x）
   - [ ] 分页场景引了 `mybatis-plus-jsqlparser`？
   - [ ] `updateById` 需置 null？→ 改用 `LambdaUpdateWrapper.set()`
   - [ ] XML 中枚举字段每处 `#{}` 都声明了 `typeHandler=MybatisEnumTypeHandler`？
   - [ ] Wrapper 每次 `new` 新实例？
   - [ ] Wrapper 条件用方法引用（`User::getXxx`）？字符串字段名仅限动态列名/动态表名例外
   - [ ] 窗口/聚合/GROUP BY/专有函数/计算列场景 → 改写 XML，未用 `apply`/`last` 拼？
   - [ ] `@Transactional` 显式写了 `rollbackFor = Exception.class`？
   - [ ] 事务方法无自调用？
   - [ ] 自定义 XML 分页：方法返回 `IPage`、入参 `page` 非 null？

## 项目播种

种子文件只写两样东西：**项目事实**（版本、DbType、配置类位置、逻辑删除字段名）与**有知识但不会主动做的流程**（新增 Mapper 时必须同名同参）。模型本来就会的 MP 用法一律不写。

**触发**：依赖含 `mybatis-plus-*`，且项目无 `.claude/rules/mybatis-plus.md`，或该文件首行注释 `<!-- seeded: mybatis-plus-dev@x.y.z -->` 的版本低于本技能 → **提议**播种，一句话说明收益，等用户确认。不要未经同意就写项目文件。**2.x 时代的旧种子首行是 `> 版本：v1`，同样算落后**（旧种子没有 `paths`，不会按需加载，等于白占上下文）。

**落点只有一个**：`.claude/rules/mybatis-plus.md`。Claude Code 原生递归加载 `.claude/rules/*.md`，**不需要在 `CLAUDE.md` 里 `@import`**，所以**不碰 `CLAUDE.md`**——改它既污染用户文件，又没有任何收益。

**从 2.x 升级**：老项目 `CLAUDE.md` 里可能残留一行 `@.claude/rules/mybatis-plus.md`（2.x 播种时写的）。3.0.0 起不需要，**提示用户可删，不擅自改**。

带 `paths` frontmatter 的规则只在 Read/Write/Edit 触及匹配文件时加载，不带则启动即加载、常驻上下文——MP 约定必须带 `paths`。

**流程**（模板见 `assets/seed-template.md`）：

| 步 | 动作 |
|---|---|
| 1 | 按下方槽位表读出模板里的 `⟨⟩`；**读不到就删掉那一行，不留占位符、不留默认值** |
| 2 | 读项目现有 `.claude/rules/*.md` 与 `CLAUDE.md`：已有同主题约定（逻辑删除字段、Mapper 扫描等）→ 跳过该槽位，以项目既有写法为准 |
| 3 | 按项目真实文件名校准模板里的 `paths`，不照抄 |
| 4 | 落盘判归属：文件不存在 → 新建；首行有 `<!-- seeded:` → 整文件重写；**无该标记说明是用户自己写的 → 不覆盖**，只补缺失事实并保留原文 |
| 5 | 写入 `.claude/rules/mybatis-plus.md`；**不改 `CLAUDE.md`** |

槽位探测位置：

| 槽位 | 从哪读 |
|---|---|
| MP 版本 / SpringBoot 版本 | `pom.xml` 里 `mybatis-plus-*starter` 与 `spring-boot-starter-parent` 的 version；多模块看父 pom 的 `dependencyManagement` |
| DbType | 数据源 URL 的 scheme（`jdbc:postgresql` → `POSTGRE_SQL`）或 `application.y*ml` 的 `db-type` |
| 拦截器注册类 | grep `MybatisPlusInterceptor` / `PaginationInnerInterceptor` |
| Mapper 扫描 | grep `@MapperScan`；无注解时看启动类包路径 |
| XML 位置 | `application.y*ml` 的 `mapper-locations`，或 `src/main/resources` 下 `*.xml` 的实际目录 |
| 逻辑删除 | grep `@TableLogic` 与 `logic-delete-field` / `logic-not-delete-value`（值为时间戳时要记实际值，不是 0/1） |
| 多数据源 | grep `@DS` 与 `dynamic-datasource` 依赖；有则记切换入口类名 |

**`paths` 必须匹配真实文件**：模板默认 `**/*Mapper.java` / `**/*Mapper.xml` / `**/*ServiceImpl.java`。XML 命名不是 `*Mapper.xml`（如 `user-mapper.xml`、`User.xml`）时，按 `mapper-locations` 的实际目录改成 `**/mapper/**/*.xml`。glob 写错是**静默失效**——不报错、不加载，看起来像生效了。播种后确认它至少能匹配到一个真实文件。

**种子失控的形态**：一旦需要二级标题分节、出现代码块、出现「推荐 / 最佳实践」，说明它在退化成知识手册，那部分该搬进 `references/`。单个槽位去留问两问——① 能在代码里被违反吗？② 违反了模型自己会发现吗？两问皆否就删。
