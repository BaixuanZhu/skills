# 排错路由

通用报错（网络不通 / 密码错 / 依赖冲突 / 客户端版本过老）按报错信息直接处理，不占表。同一事实只在归属文件写一份——本表只做**症状 → 去哪节查**，不复述原因与修复；命中后读目标节处理，改完代码对照 SKILL.md「核心强约束」自检。

## 1. 症状 → 路由

| 症状（报错 / 现象） | 去查 |
|---|---|
| `Unable to connect`，但地址密码都对 | `01-connection.md` §4 |
| 哨兵模式连不上 / 连的不是数据节点 | `01-connection.md` §3.1 |
| `CROSSSLOT` / 集群多 key 命令报错 | `01-connection.md` §3.2 |
| `Could not get a resource from the pool` | `02-pool.md` §5（先确认 client-type：Jedis 与 Lettuce 的处置完全不同） |
| scan 结果有重复 | `04-template-operations.md` §1 |
| key 前缀 `\xac\xed` 乱码、`match` 模式匹配失效 | `03-serialization.md` §2 |
| `InvalidDefinitionException: Java 8 date/time ...` | `03-serialization.md` §3 |
| 读回 `LinkedHashMap`，强转实体报 `ClassCastException` | `03-serialization.md` §3-§4 |
| `No serializer found ... NullValue`（`@Cacheable` 缓存 null 触发） | `03-serialization.md` §3 |
| 换序列化方案后旧 key 全部读不回 | `03-serialization.md` §6 |
| `@Cacheable` 不生效（每次都查库） | `05-spring-cache.md` §4（自调用 + 失效清单） |
| `@Cacheable` 永不过期 / 缓存 value 是二进制 | `05-spring-cache.md` §3 |
| `IllegalMonitorStateException`（unlock 时） | `07-redisson.md` §4 |
| 业务执行中途并发进入（锁"失效"） | `07-redisson.md` §4 |
| Redisson starter 引入后 RedisTemplate 行为异常 | `07-redisson.md` §1 |

## 2. 表内即答案（无归属文件）

| 症状 | 结论 |
|---|---|
| TTL 已到期的 key 在 `scan` / `dbsize` 里还在 | 惰性 + 定期删除，物理删除滞后——**无需处理**，读不到即正确语义（键空间通知不准时也因它，`09-messaging.md` §4） |
