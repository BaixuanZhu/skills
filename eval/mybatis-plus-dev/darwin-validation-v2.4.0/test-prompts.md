# Test Prompts（v2.4.0 达尔文盲评）

> 14 条 prompt：T1-T8 回归集（覆盖核心域，确保修剪无退步）+ T9-T14 对抗集（直击本轮五处 API 修正与三项修剪根因）。

## 回归集（T1-T8）

### T1 · 新项目引入 + starter 选择（域 01/版本与依赖）
新 SpringBoot 项目要引入 MyBatis-Plus：我们是 SpringBoot 2.7 项目，还有个新项目是 SpringBoot 3.4，另外有个 JDK8 老项目也要用分页。分别怎么引依赖？分页需要额外引什么？

### T2 · null 不更新 + 显式置空（域 03/04/05）
我用 `updateById` 更新用户，想把 remark 字段清空成 null，结果执行后 remark 没变。为什么？怎么正确置 null？我能在 yml 里全局改 update-strategy 让 null 也更新吗？

### T3 · Wrapper 超界场景（域 05/10）
我要查每个部门的第一条记录（ROW_NUMBER() OVER (PARTITION BY dept_id)）和各部门总数（GROUP BY + COUNT），现在想用 QueryWrapper 的 apply/last 拼。可以吗？应该怎么写？

### T4 · 逻辑删除全局配置（域 02）
表要加逻辑删除：全局怎么配？用 0/1 还是别的方案？username 有唯一索引，逻辑删除后同名再插入会不会冲突？

### T5 · 事务失效排查（域 11）
我的 @Transactional 方法抛了异常但没回滚，方法里有 try-catch 记了日志，还有同类里 this.methodB() 的调用。逐个指出可能的原因和修法。

### T6 · 枚举映射（域 03/10）
用户表 gender 字段存 1/2，想用枚举 GenderEnum 映射，前端要收到数字而不是 "MALE"。BaseMapper 查询和自定义 XML 查询分别怎么配？

### T7 · 批量插入性能（域 04/11）
要导入 10 万用户，直接 saveBatch(list) 太慢了。saveBatch 到底是不是真批量？怎么提速？要在事务里吗？

### T8 · 排错两连（域 09/10/11）
启动后调接口报 `Invalid bound statement (not found)`；另一个项目 selectPage 返回的 total 一直是 0 但有数据；还有个 @DS 多数据源 + @Transactional 的跨库操作，主库回滚了从库没回滚。分别怎么排查？

## 对抗集（T9-T14）

### T9 · 对抗·数据权限插件（07-plugin §4）
要按登录用户的部门做数据权限过滤（dept_id IN (...)），给我 DataPermissionInterceptor 的完整配置代码，包括 handler 怎么写。

### T10 · 对抗·动态表名（07-plugin §3）
要按月分表（user_1 ~ user_12），给我 DynamicTableNameInnerInterceptor 的配置代码。

### T11 · 对抗·防注入校验语义（SKILL 强约束 #7 / 05 §5）
用户输入要拼进 `w.apply("date_format(create_time,'%Y-%m-%d') = ...")`，SqlInjectionUtils.check 到底怎么用？它检测到注入会抛异常吗？给我正确写法。

### T12 · 对抗·3.4.x 升级（13-migration）
项目还在 MyBatis-Plus 3.4.2，要升到 3.5.x。有哪些 breaking change？给我完整升级步骤清单。

### T13 · 对抗·Oracle 适配（12-dbtype）
MySQL 项目要迁到 Oracle：分页插件要改什么？主键能用 AUTO 自增吗？表里有个列名叫 `desc` 的保留字，MP 会自动转义吗？

### T14 · 对抗·只读 SKILL.md 的分页链路（修剪回归）
假设你只能读 SKILL.md 这一个文件（不打开任何 reference）：新 SpringBoot 3 项目要做用户分页列表。①需要额外引什么依赖、不引会怎样？②分页插件怎么配、注意什么顺序？③自定义 XML 联表分页的方法签名怎么写、有什么硬性要求？④你的 description 里的触发词能不能让"分页失效/total 为 0"这类求助命中本技能？
