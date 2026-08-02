# 插件与进阶能力

> 本 skill 完全本地化，以下全部为内置知识，无在线 fetch。基础三件套（逻辑删除 / 自动填充 / 乐观锁）配置见 `02-config.md` 与 `03-entity.md`，此处补充进阶插件。

## 1. 逻辑删除 / 自动填充 / 乐观锁

- 逻辑删除：全局 `logic-delete-field` 或 `@TableLogic`（`02-config.md` §2 / `03-entity.md` §6）
- 自动填充：`MetaObjectHandler` + `@TableField(fill=...)`（`02-config.md` §4 / `03-entity.md` §3）
- 乐观锁：`@Version` + `OptimisticLockerInnerInterceptor`（`02-config.md` §3 / `03-entity.md` §5）

## 2. 多租户 TenantLineInnerInterceptor

自动在每张表的 SQL 上追加 `tenant_id = ?` 条件，实现行级租户隔离。

```java
interceptor.addInnerInterceptor(new TenantLineInnerInterceptor(
    new TenantLineHandler() {
        @Override public Expression getTenantId() {
            // 租户ID必须非 null，从登录上下文/ThreadLocal 取，勿硬编码
            return new LongValue(TenantContext.getTenantId());
        }
        @Override public String getTenantIdColumn() { return "tenant_id"; }
        @Override public boolean ignoreTable(String tableName) {
            return "sys_config".equals(tableName); // 公共表跳过租户条件
        }
    }));
```

- **在插件链中先于分页添加**（顺序见 §5 / 强约束 #10）。
- **租户 ID 来源**：从请求上下文取（如 `TenantContext` / `LoginUser` 持有的 tenantId），由登录拦截器写入 `ThreadLocal`；`getTenantId()` 返回 **null 会拼出 `tenant_id = null` 导致所有数据查空**，务必保证非空。
- **与逻辑删除共存**：两者都改写 WHERE，MP 内部按顺序拼接，无需手动处理；`ignoreTable` 的表两者都跳过。
- **方法级跳过**：个别 Mapper 方法用 `@InterceptorIgnore(tenantLine = "true")` 跳过租户条件（如跨租户管理后台）。
- **`ignoreTable` 策略**：字典、配置等公共表必须返回 true，否则会因无 `tenant_id` 列报错或被错过滤。
- 反模式：
  - ❌ `getTenantId()` 返回 null → 全部 `tenant_id = null`，数据全空。✅ 上下文必填校验。
  - ❌ 公共表未进 `ignoreTable` → 拼 `tenant_id` 报「未知列」。✅ 公共表加忽略。
  - ❌ 多租户放在分页之后 → COUNT SQL 未被改写，分页总数不准。✅ 先于分页（强约束 #10）。

## 3. 动态表名 DynamicTableNameInnerInterceptor

```java
interceptor.addInnerInterceptor(new DynamicTableNameInnerInterceptor(
    tableName -> "user_" + LocalDate.now().getMonthValue()));  // 按月分表
```
- 用于分表路由；与多租户同用时要关注插件顺序（不做 SQL 改写的靠后）。

## 4. 数据权限 DataPermissionInterceptor

按当前用户的数据范围（部门/角色）自动追加行级过滤条件（如 `dept_id IN (...)`）。

```java
interceptor.addInnerInterceptor(new DataPermissionInterceptor(
    new MultiDataPermissionHandler() {
        @Override
        public List<DataPermissionRule> getSqlSegment(ExecutionStatement stmt) {
            // 范围来自登录上下文（可信），不要拼接未校验的外部输入
            List<Long> deptIds = UserContext.getDeptIds();
            if (deptIds == null || deptIds.isEmpty()) return Collections.emptyList();
            // 权限表/字典表自身不应被过滤，按表名白名单跳过
            if (!isBizTable(stmt.getTableName())) return Collections.emptyList();

            DataPermissionRule rule = new DataPermissionRule();
            rule.setColumn("dept_id");
            // 用 jsqlparser AST 构造（InExpression/Column/LongValue），勿字符串拼接 → 防注入
            rule.setExpression(new InExpression(
                new Column("dept_id"),
                new ExpressionList(deptIds.stream().map(LongValue::new).collect(Collectors.toList())),
                false));
            return Collections.singletonList(rule);
        }
    }));
```

- **必须放在多租户之后、分页之前**（顺序见 §5 / 强约束 #10）；与逻辑删除共存时 MP 顺序拼接，无需手动处理。
- **条件来源必须可信**：部门/角色范围来自登录上下文；若含外部输入，须先 `SqlInjectionUtils.check`（对应强约束 #7）。**禁止字符串拼接** SQL 片段（注入后门）。
- **避免权限表自过滤**：数据权限表/字典表自身不应被追加条件，用表名白名单或 `@InterceptorIgnore` 跳过。
- 反模式：
  - ❌ 拼 `"dept_id IN ('" + userInput + "')"` → SQL 注入。✅ 用 `DataPermissionRule` + `InExpression` 参数化构造。
  - ❌ 数据权限放在分页之后 → COUNT 未被过滤，总数泄露越权数据。✅ 先于分页（强约束 #10）。
  - ❌ 对权限/字典表也追加条件 → 自身被过滤查不到。✅ 表名白名单跳过。

## 5. 防全表 / 非法 SQL

- `BlockAttackInnerInterceptor`：拦截无 WHERE 的 update/delete（见 `02-config.md` §5）。
- `IllegalSQLInnerInterceptor`：检查全表扫描、索引缺失等风险 SQL。
- 二者均在插件链中按需在分页之前添加。

> 插件顺序建议：**多租户 → 数据权限 → 动态表名 → 乐观锁 → 防全表 / 非法 SQL → 分页（最后）**。分页放最后是因为多租户 / 数据权限 / 动态表名都会改写 SQL，若在分页之后添加，则 COUNT 语句不会被改写，导致总数不准或权限漏过滤。简单场景（仅乐观锁 + 防全表 + 分页）只需保证分页最后即可（见 `02-config.md` §1）。
