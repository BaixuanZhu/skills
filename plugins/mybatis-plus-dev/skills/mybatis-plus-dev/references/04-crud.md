# CRUD 与 Service 层

## 1. BaseMapper vs IService

| 层 | 提供 | 适用 |
|---|---|---|
| `BaseMapper<T>` | 单表 CRUD 底层方法（selectById / insert / updateById / delete …） | Mapper 接口直接继承 |
| `IService<T>` + `ServiceImpl<M,T>` | 在 Mapper 之上封装的批量 / 链式 / 分页便利方法（saveBatch / getOne / list / page …） | Service 层继承 |

**优先用 `IService` 提供的方法**，它们已处理批量与空判断，避免自己写循环。

## 2. 正确继承范式

```java
public interface UserMapper extends BaseMapper<User> {}

public interface IUserService extends IService<User> {}

@Service
public class UserService extends ServiceImpl<UserMapper, User> implements IUserService {
    // 直接用 baseMapper / 父类的 save / page / list 等方法
}
```

## 3. saveBatch 真相（重点）

`IService.saveBatch(list)` **默认不是真正的 JDBC 批量**：它按 `batchSize`（默认 1000）分批，每批内仍是**逐条 `insert`**（除非底层 `SqlSession` 处于 BATCH 模式）。

要让它真正批量（减少网络往返）：
1. 配置 JDBC URL 参数 `rewriteBatchedStatements=true`（MySQL），让驱动真正合并批量语句。
2. 在 `@Transactional` 内调用，或使用 MP 的批处理 `SqlSession`。

```java
userService.saveBatch(userList);            // 默认 batchSize=1000
userService.saveBatch(userList, 500);       // 指定批次大小
```
> 若追求极致批量性能，复杂场景用 `InsertBatchSomeColumn` 注入器或原生 `foreach` 批量 SQL，而非依赖 `saveBatch` 的“伪批量”。

### MP 侧批量 / 性能要点（仅 MP 专属，非通用 DBA）

以下均为 MyBatis-Plus / MyBatis 层可掌控的性能点；**连接池调优、索引设计、慢查询分析属数据源 / DBA 层，不在本 skill 范围**（见 SKILL.md「不适用」边界）。

- **真正批量三法**（减少网络往返）：
  1. `BATCH` executor：`new SqlSessionTemplate(sqlSessionFactory, ExecutorType.BATCH)` + JDBC URL `rewriteBatchedStatements=true`（MySQL），循环 `insert` 后 `sqlSession.flushStatements()`。
  2. `InsertBatchSomeColumn` 注入器（MP 自带，生成多值 `INSERT`），主要适配 MySQL 多值语法；其他库见 `12-dbtype.md` 走 BATCH。
  3. 原生 XML `foreach` 多值 `INSERT`（简单可控，跨库兼容性最好）。
- **一级缓存范围**：`local-cache-scope=STATEMENT`（微服 / 分布式场景防跨请求脏读，见 `02-config.md §8`）；默认 `SESSION` 在长会话或集群中可能读到旧值。
- **大结果集流式**：避免 `selectList` 全量进内存（OOM 风险），用游标 / `ResultHandler`：
  ```java
  @Options(resultSetType = ResultSetType.FORWARD_ONLY, fetchSize = 1000)
  void scanBigTable(ResultHandler<User> handler);  // 逐批回调，不囤全量
  ```
- **分页防护**：`PaginationInnerInterceptor.maxLimit` 设单页上限，防恶意超大分页拖垮 DB（见 `02-config.md §1`）。
- 反模式：
  - ❌ `saveBatch` 当真批量 → 网络往返未减（见 `08-antipattern.md` #4/#22）。
  - ❌ `BATCH` executor 不在同一 `SqlSession` / 事务内 → 语句未合并，退化为逐条。
  - ❌ 大表 `selectList` 全量 → 内存溢出；改流式 / 分页游标。

## 4. updateById / update 的 null 语义

- `updateById(entity)`：`entity` 中 `null` 字段**不更新**（见 `03-entity.md` 字段策略）。
- 想把字段置 null：用 `UpdateWrapper.set(...)`。
- `update(entity, wrapper)`：`entity` 提供 SET 值，`wrapper` 提供 WHERE；`wrapper` 不可复用。

```java
// 只更新 name，age 不受影响（因 entity.age 为 null）
userMapper.updateById(new User().setId(1L).setName("New"));

// 显式置 age 为 null
userMapper.update(null, new LambdaUpdateWrapper<User>()
    .eq(User::getId, 1L).set(User::getAge, null));
```

## 5. 常用方法速查

```java
// IService
save(entity); saveBatch(list); saveOrUpdate(entity);
getById(id); getOne(wrapper); list(); list(wrapper); listByIds(ids);
page(page, wrapper); updateById(entity); update(entity, wrapper);
removeById(id); remove(wrapper); count(); count(wrapper);

// BaseMapper
selectById / selectList / selectOne / selectCount / selectMaps / selectObjs
insert / deleteById / delete / updateById / update
```
> `selectObjs` 返回**首列** `Object` 列表（非整行）；取整行用 `selectList`，取 Map 用 `selectMaps`。
