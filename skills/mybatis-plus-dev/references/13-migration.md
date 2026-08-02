# 3.4.x → 3.5.x 迁移与兼容速查

> 本 skill 主线基于 3.5.x（推荐 3.5.17）。若项目仍停留在 3.4.x 或需从 3.4.x 升级，本章给出**已验证的 breaking change 与前后代码**。3.5.x 的 breaking 多为「删废弃类 + 拆依赖」，机械替换即可，无行为语义重写。

## 1. 支持策略

- **3.5.x（主线）**：本 skill 全部 references 按其整理，直接适用。
- **3.4.x（legacy 兼容）**：`PaginationInterceptor` 在 3.4.0 起已被标记废弃但仍可用；**不要**在 3.4.x 用本 skill 提到的 `mybatis-plus-jsqlparser` 拆分依赖（那时尚未拆分）。升级到 3.5.x 后按本章改造。
- 更老的 3.3.x：先升到 3.4.x 再升 3.5.x（3.3→3.4 已引入 `MybatisPlusInterceptor`）。

## 2. Breaking Changes（前 → 后）

| # | 变更 | 版本 | 旧写法（3.4.x 及之前） | 新写法（3.5.x） |
|---|---|---|---|---|
| 1 | 分页拦截器重构 | 3.4.0 引入，3.5.x 移除旧类 | `new PaginationInterceptor()` | `new MybatisPlusInterceptor().addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL))` |
| 2 | 分页插件拆依赖 | 3.5.9+ | 分页随核心包 | 额外引 `mybatis-plus-jsqlparser`（否则分页静默失效，见 `01-start.md`） |
| 3 | `Page.MybatisPlusLang` 移除 | 3.5.0（**无 @Deprecated 过渡**） | `Page.MybatisPlusLang.like("张")` | `new LambdaQueryWrapper<>().like(User::getName,"张")` |
| 4 | `FieldStrategy.IGNORED` 废弃 | 3.5.x | `FieldStrategy.IGNORED` | `FieldStrategy.ALWAYS`（见 `02-config.md §7`） |
| 5 | SQL 注入器重构 | 3.5.x | 自定义 `extends SqlInjector` / `ISqlInjector` | `extends DefaultSqlInjector`（仅自定义方法注入场景） |

### 2.1 示例：分页拦截器（最典型）

```java
// ❌ 3.4.x 旧写法（3.5.x 编译失败：类已移除）
@Bean
public PaginationInterceptor paginationInterceptor() {
    return new PaginationInterceptor();
}

// ✅ 3.5.x 新写法
@Bean
public MybatisPlusInterceptor mybatisPlusInterceptor() {
    MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
    interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL)); // 分页最后
    return interceptor;
}
```

### 2.2 示例：`Page.MybatisPlusLang` 移除

```java
// ❌ 3.4.x（3.5.0+ 直接编译失败，无过渡）
Query query = new Query();
query.put("name", Page.MybatisPlusLang.like("张"));

// ✅ 3.5.x：用 Wrapper 链式构建（类型安全）
LambdaQueryWrapper<User> w = new LambdaQueryWrapper<>();
w.like(User::getName, "张").eq(User::getStatus, "ACTIVE");
```

### 2.3 逻辑删除配置项稳定

`logic-delete-field` / `logic-delete-value` / `logic-not-delete-value` 在 3.4→3.5 **未变**，无需改（配置示例见 `02-config.md §2`）。

## 3. 升级步骤清单

1. 升 `com.baomidou:mybatis-plus-*` 版本到 3.5.17（统一，勿混版本）。
2. 替换 `PaginationInterceptor` Bean → `MybatisPlusInterceptor` + `PaginationInnerInterceptor`（最后添加）。
3. 引 `mybatis-plus-jsqlparser`（v3.5.9+ 必引，否则分页失效）。
4. 全局替换 `FieldStrategy.IGNORED` → `FieldStrategy.ALWAYS`。
5. 删除所有 `Page.MybatisPlusLang.*` 调用，改 `QueryWrapper`/`LambdaQueryWrapper`。
6. 自定义 SQL 注入器：`extends SqlInjector` → `extends DefaultSqlInjector`。
7. 清理依赖树：`mvn dependency:tree` 确认无 3.3.x / 3.4.x `mybatis-plus-extension` 残留（避免类路径迁移导致的 `ClassNotFoundException`）。

## 4. 反模式（legacy 代码陷阱）

- ❌ **3.5.x 仍 `new PaginationInterceptor()`**：旧类在 3.5.x 已移除，编译失败。✅ 改用 `MybatisPlusInterceptor` 容器。
- ❌ **升级后分页不生效但不报错**：漏引 `mybatis-plus-jsqlparser`（3.5.9+ 拆分）。✅ 补依赖。
- ❌ **依赖碎片**：同时存在 `mybatis-plus-boot-starter:3.4.0` 与 `mybatis-plus-extension:3.5.7`，Maven 调解取低版本导致 `MybatisPlusInterceptor` 不可见。✅ 统一版本 + 清 `.m2` 残留。
- ❌ **`IGNORED` 当「忽略策略」继续用**：已废弃语义等价于 `ALWAYS`。✅ 显式 `ALWAYS`。
