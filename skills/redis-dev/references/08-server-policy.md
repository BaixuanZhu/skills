# 服务器策略对应用行为的影响

> 本章不是 Redis 运维手册——只覆盖**服务器配置如何反噬 Java 应用行为**：淘汰策略挤掉业务数据、TTL 删除时机、持久化取舍。安装 / 主从搭建 / 监控不在本技能范围。

## 1. maxmemory 与 8 种淘汰策略

`maxmemory` 是 Redis 可用内存上限；达到后写命令按 `maxmemory-policy` 处理，**读命令不受影响**。

| 策略 | 淘汰范围 | 行为 |
|---|---|---|
| `noeviction`（**默认**） | 不淘汰 | **写命令直接报错** `OOM command not allowed when used memory > 'maxmemory'` |
| `allkeys-lru` | 全部 key | 最久未访问的先淘汰 |
| `allkeys-lfu`（Redis 4+） | 全部 key | 访问频率低的先淘汰（偶发批量查询不易挤掉常驻热点） |
| `allkeys-random` | 全部 key | 随机淘汰（几乎不用） |
| `volatile-lru` / `volatile-lfu` / `volatile-random` | **仅设了 TTL 的 key** | 没设 TTL 的 key **永不淘汰** |
| `volatile-ttl` | 仅设了 TTL 的 key | 剩余存活时间短的先淘汰 |

**默认 `noeviction` 是头号暗雷**：内存写满后所有写（缓存 set、Sa-Token 登录写 session、锁的 SET NX）全报错，应用表现为一阵集中故障——且没人改过任何代码。生产实例必须显式设置 `maxmemory` + 策略。

### 选择决策

| 实例用途 | 策略 | 理由 |
|---|---|---|
| 纯缓存（数据可从 DB 重建） | `allkeys-lru` 或 `allkeys-lfu` | 满了挤掉冷的，应用无感 |
| 缓存 + 持久数据混用（不分实例时） | `volatile-lru` | 持久数据（不设 TTL）不被淘汰，可淘汰的只有缓存——**前提是强约束"缓存必须 TTL"**（没 TTL 的缓存又挤不掉） |
| 锁 / 限流 / 幂等专用 | `noeviction` + 容量规划 | 锁被 LRU 挤掉 = 互斥凭空消失；这类 key 小而少，规划得住 |

## 2. 共库反噬：allkeys-lru 挤掉 Sa-Token session

**症状**：用户使用中随机被登出，无规律、无法复现；重看代码毫无问题。

**机制**：业务缓存与 Sa-Token 共用实例且策略为 `allkeys-lru`（或 `volatile-*`）→ 内存到达上限时淘汰"最久未访问"的 key → 长时间未操作（但仍在 timeout 有效期内）的用户 session 被挤掉 → 下次请求 `NotLoginException`。

排查：`redis-cli info memory` 看 `used_memory` 是否贴着 `maxmemory`；`evicted_keys`（INFO stats）非零即发生过淘汰。

方案（按优先级）：

1. **分实例**：缓存单独一个实例开 `allkeys-lru`；session/持久数据独立实例 + 容量规划（C4 检查点的默认推荐）。
2. 无法分实例：session 所在实例策略退到 `volatile-lru` 只能自保（session 有 TTL，仍可能被挤——只是把无 TTL 的持久数据保住）；**根治靠容量**：`maxmemory` 按峰值预留 30%+ 余量，让淘汰根本不发生。
3. key 前缀隔离（`03-serialization.md` §5）**只能防覆盖，防不了淘汰**——不要把它当共库方案讲。

## 3. TTL 的删除时机：到期 ≠ 立即消失

Redis 过期删除 = **惰性**（访问该 key 时校验并删）+ **定期**（后台周期抽样删除）。含义：

- TTL 到期的 key **立刻不可读**（读到 null）——语义正确。
- 但 key 可能仍占内存（未被动过、未被抽样到）：`scan`/`keys` 可能列出已过期未物理删除的 key（Redis 7 之前），`dbsize` 偏大——**不是泄漏**，也不是"没过期成功"。
- 大量同时过期会触发定期删除任务变重（CPU 尖刺）——又是 TTL 随机抖动的理由（`06-cache-consistency.md` §4）。

## 4. 持久化取舍

| | RDB | AOF |
|---|---|---|
| 形态 | 周期全量快照 | 追加写命令日志 |
| 丢数据窗口 | 分钟级（`save 900 1` 一类规则） | `appendfsync everysec` 丢 ≤1s |
| 恢复速度 | 快 | 慢（重放） |
| 默认 | **开** | **关**（`appendonly no`） |

按实例用途定（不是无脑全开）：

- **纯缓存实例**：RDB/AOF 都可关——重启后从 DB 回源预热即可，省掉落盘开销。
- **session / 业务数据实例**：开 AOF（everysec）+ RDB 混合（`aof-use-rdb-preamble yes`，Redis 4+ 默认）——重启不丢登录态。
- 本地开发 docker-compose 示例（缓存用途）：

```yaml
services:
  redis:
    image: redis:7
    command: >
      redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
                   --save "" --appendonly no
    ports: ["6379:6379"]
```

## 5. lazyfree：大 value 的删除阻塞

同步 `DEL` 一个大 Hash/List（百万元素）会阻塞 Redis 主线程数百毫秒到秒级，期间**所有命令**排队。`lazyfree-lazy-expire/lazyfree-lazy-eviction/lazyfree-lazy-del yes`（服务器配置）改为后台线程释放。应用侧对应动作：批量删除用 `UNLINK`（`04-template-operations.md` §4）；排查"周期性整体卡顿"时想到它。

## 6. 自检

- [ ] 实例显式配置了 `maxmemory` + 策略（没在用默认 `noeviction` 裸奔）
- [ ] 共库场景评估过淘汰对 session / 持久数据的影响（`evicted_keys` 查证过或提醒过用户）
- [ ] "key 过期了还在"的疑问对过本章 §3（不是 bug）
- [ ] 应用侧全用 `UNLINK` 批删；实例开了 lazyfree
