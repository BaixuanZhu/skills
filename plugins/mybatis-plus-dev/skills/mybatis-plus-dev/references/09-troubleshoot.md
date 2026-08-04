# 排错与 SQL 日志

## 1. 开启 SQL 日志

**方式一：MP 配置（最常用）**
```yaml
mybatis-plus:
  configuration:
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl
```
控制台打印完整 SQL 与参数，调试完关闭（有性能开销）。

**方式二：p6spy（格式化）**
引入 `p6spy` 依赖，配置 `driver-class-name` 走 `P6SpyDriver`，输出带占位符与耗时。

## 2. 常见异常定位

| 现象 | 原因 | 排查 |
|---|---|---|
| `Invalid bound statement (not found)` | Mapper 未扫描 / 方法无对应 XML | 检查 `@MapperScan` 包路径、XML `namespace` |
| `BindingException: Parameter 'xxx' not found` | 多参未 `@Param` | Mapper 方法参数加 `@Param("x")` |
| 分页 `total=0` / 返回全量 | 未配分页插件或未引 jsqlparser | 见 `02-config.md` §1、`06-page.md` §2 |
| 更新后某字段没变 | null 不更新 | 见 `04-crud.md` §4、`03-entity.md` §4 |
| 逻辑删除后仍能查到 | `@TableLogic`/全局未生效 | 检查字段名与配置是否一致 |
| 乐观锁永远成功 | 未注册插件 | 见 `02-config.md` §3 |
| 字段值全为 null | 列名/属性名映射错 | 检查驼峰配置与 `@TableField` |

## 3. 分页失效快速排查清单

1. 是否引 `mybatis-plus-jsqlparser`（v3.5.9+ 必须）？
2. 是否注册 `MybatisPlusInterceptor` 且 `PaginationInnerInterceptor` **最后添加**？
3. 单库是否指定 `DbType`？
4. `selectPage` 入参 `Page` 是否正确 `new`（非 null）？
5. XML 联表分页入参 `IPage` 是否非 null？

## 4. 建议

- 调试先开 SQL 日志，看真实执行的 SQL。
- 涉及易错点先翻 `08-antipattern.md`。
- 复杂查询优先 XML，避免 Wrapper 黑盒。
