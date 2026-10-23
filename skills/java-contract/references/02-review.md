# 02 · 存量代码审查

靶子是**已有的、别人写的**代码。写新代码时不必逐条对照——这些坑生成时基本不犯，对照只是消耗上下文。

用法是**提问**，不是逐组扫表：拿每节标题那句问题去追代码路径，比按 API 名去 grep 更容易撞上值钱的坑。
按 API 分组扫（数值一组、字符串一组）会把范围收窄到分组枚举过的写法，真实存量代码里最贵的问题往往落在分组之外。

## 审查顺序

按失效后果排，前四组是存量代码真正烧钱的地方：

| 顺序 | 问什么 |
|---|---|
| 1 | 同一份数据，是不是在两处各算了一遍？ |
| 2 | 同一件事实还有第二份副本吗（调度器 / 对象存储 / 缓存 / 外部系统），这次更新碰了哪一个？ |
| 3 | 有没有绕过信任边界的入口？ |
| 4 | 有什么会随运行时间累积（客户端、连接、临时文件、日志表）？ |
| 5 | 返回契约和调用方期望一致吗？ |
| 6 | 并发与遍历顺序有没有被当成确定的？ |
| 7 | 只有模块真的处理金额 / 除法 / 时区转换时才看这一组 |

## 一、同一份数据在两处各算一遍

**判据：两个来源的值做比较，基准不是同一套**——0 起 vs 1 起、含尾 vs 不含、旧对象 vs 刚提交的 VO。
恒不等的比较不会抛异常，它只会让「判作变更」的逻辑永远走变更分支。

```java
// ordinalPosition 入库时从 1 开始（index++），这里 index 从 0 起 → 每列都判成「变了」
if (!primaryKeyPredicate.test(tableField, column) || column.getOrdinalPosition() != index) {
    return columnName;
}
```
后果是同步时「全删 + 全量重建」：用户手配的字段被默认值覆盖，字段 id 换新，引用这些 id 的配置全部悬空。

同一类的另外两种形态：

- **同名覆盖**：落盘路径是「日期 + 原名」且覆盖开关关着，后写的静默替换先写的，DB 却新增一条记录；删对象时另一条记录跟着 404。
- **先算派生结果、后改输入**：`buildColumns()` 之后才 `setPrimaryKey(true)`，此前按「非主键」算好的 operation 标志全部是错的，生成物能编译、语义错。

**怎么查**：找「比较两个来源」的分支，问两边基准是否同一套；找路径生成（落盘、下载、导出、解压），问重名会怎样。

## 二、两处状态不同步

**判据：同一件事实有第二份副本**——调度器里的 job key、对象存储里的对象、缓存里的客户端、外部系统的单据。
更新路径只改一份，另一份指望「以后会同步」。

```java
// 落库用新名，Quartz 用旧名
jobMapper.updateById(BeanUtils.toBean(updateReqVO, JobDO.class));
schedulerManager.updateJob(job.getHandlerName(), ...);   // job 是库里的旧记录
```
Quartz 对不存在的 key 静默 no-op：暂停、删除、立即执行全部无效，接口照样返回成功。此后每次「同步」还会多出一个 JobDetail，任务跑两份。

另两种形态：

- **缓存刷新只看配置内容差、不看客户端类型**：`storage` 从 Local 改成 S3，运行期仍是旧 client，上传时 `ClassCastException`；DB 已写新值，重启也不会自愈。
- **事务里做外部系统操作**：`@Transactional` 里先 `deleteJob` 再 `addJob`，DB 回滚了调度器不回滚；多节点同时点「同步」还会互相踩。

**怎么查**：对每个写方法列出它改了哪几份副本；`grep` 出 `get旧字段()` 与 VO 新值同时出现的方法。

## 三、信任边界被绕过

**判据：入口的输入能不能决定「读写哪个对象」**。能，就必须校验归属，否则任何拿到路径/名字的人都能操作别人的数据。

典型入口（都不是「静默失败的 Java 写法」，但存量代码里代价最高，任何静态检查都不报）：

| 形态 | 后果 |
|---|---|
| 下载/预览接口 `@PermitAll` + `@TenantIgnore`，按路径直取 | 未登录按「日期/文件名」枚举即可拖走全部文件 |
| `/actuator/**`、`/druid/**` 一律 `permitAll` | `/actuator/env`、`heapdump` 匿名可读，含数据库口令 |
| 配置查询接口把 `accessKey` / `accessSecret` 原样返回 | 只读角色即可读写整个 bucket |
| zip 条目名来自可编辑字段（`className`、`businessName`） | `../` 穿越（Zip Slip），解压写出目录外 |
| 预签名 URL 不约束 `Content-Type` 与大小 | 上传 HTML 即同域存储型 XSS |
| 「按文件名推的类型」与「按路径推的类型」互比 | 两个值都由调用方给，等于没校验 |

**怎么查**：`grep -n "permitAll\|@PermitAll\|@TenantIgnore"`，逐个入口写一句「谁能调、能操作谁的数据」。

## 四、随运行时间累积

**判据：对象在运行期被反复创建而旧的不释放；临时文件靠 `deleteOnExit`；连接被多线程共享。**

- 配置定时刷新，命中「变了」就重建客户端与签名器，旧对象没有 `close()`（接口上压根没有这个方法），跑几天耗光连接与 FD。日志只是 `info("配置发生变化")`，看着一切正常。
- `createTempFile` + `deleteOnExit`：进程不退出就永不删除，几周后写满临时目录。
- `synchronized` 只加在 `reconnect()` 上，`upload` / `download` / `delete` 共用同一个 socket 裸跑；并发低时完全正常，并发起来了才会串包或 `session is down`。

**怎么查**：`grep` 定时任务与 `new .*Client`，逐个问「旧的那个谁关」；`grep deleteOnExit`。

## 五、返回契约与调用方期望不一致

| 写法 | 何时才暴露 |
|---|---|
| 查不到返回 `null` | 调用方 `.size()` NPE，或各处补判空 |
| `BeanUtils.toBean(null, X.class)` 直接返回给前端 | `code=0, data=null`，前端无法区分「不存在」与「字段全空」 |
| 工厂/查找方法失败 `return null` | 调用方一半判空一半不判，漏判处 NPE 指向调用行而非根因 |
| 空集合聚合返回 `0` | 报表多出一条 0 值假数据，永不报错 |
| 必填参数 `null` 编默认值 | 方法恒返回同一结果（`threshold` 当 0 时，「是否存在金额 > 0」几乎恒为 true） |
| `put` 与 `putIfAbsent` 混用 | 同一份导入保留首条还是末条取决于写法 |
| `list.size() != ids.size()` 判「全部存在」 | ids 里有重复时（`?ids=1,1`）明明存在也报错；ids 为空直接失败 |
| `update` 的影响行数被丢弃，`updateWhen*` 干脆返回 `void` | 状态 CAS 命中 0 行照常提交：钱已动、单据没动；只重复回调/并发时出现 |
| `selectOne` 假定唯一，业务唯一键（`bizId + bizType`）没建唯一索引 | 出现第二条时抛 `TooManyResultsException`，把整条同步链路打死 |
| 终态（CLOSED / REFUNDED）收到成功通知时抛异常，或只打一行日志 | 渠道当失败继续重投，外层事务还可能回滚已成功的处理；日志滚掉后这笔钱在库里没有落点，对账对不上 |
| 丢弃 `boolean` 返回值 | 下载失败返回 0 字节还带 200，日志干净，前端表现为图片裂开 |
| `@Async` 里 `catch` 只 `log.error(msg)`，不传 `ex` | 无堆栈；状态列永远停在 RUNNING，监控把执行完的任务算成执行中 |

## 六、并发与遍历顺序

| 写法 | 何时才暴露 |
|---|---|
| 共享可变字段无线程安全措施 | 可见性与竞态，压测才暴露 |
| `containsKey` + `put`、`get` 判空再 `put` | 并发丢更新，单测不出现 |
| `groupingBy` / `toMap` 结果直接对外返回 | 换 JDK 或 key 分布变化后分组顺序变，数值不变 |
| 遍历 `HashMap` 做的映射表取 `findFirst` | 后缀同时命中多个 key 时，这次生成 A 控件、下次 B，无报错 |
| `forEach` 里做累积、`parallelStream()` 默认用、`findAny` 当 `findFirst` | 顺序不定，结果不稳 |
| `subList` 当独立列表、`Arrays.asList(基本类型数组)`、`unmodifiableList` 包原集合 | 改子列表改到原列表；`List<int[]>` 的 `size()` 恒 1；视图穿透 |
| 可变字段做 `HashMap` 的 key | 改字段后再也查不到 |

## 七、数值与时间（条件组）

**只有模块真的处理金额、除法、时区换算或日期解析时才看这一组。** 纯 CRUD 与平台类代码跳过——这些条目在那里一条都不会命中。

`BigDecimal` 用 `equals` 比（受 scale 影响）→ `compareTo`；裸 `divide` 不给 scale 与 `RoundingMode`；`new BigDecimal(double 变量)`；金额 `toString()` 出指数形式；`LocalDateTime.now()` 记事件时间；共享 `SimpleDateFormat`；`Integer` / `Long` 用 `==`；`int v = map.get(k)` 直接拆箱；`Math.abs(Integer.MIN_VALUE)` 仍为负。

## 明确不看

- 命名、注释、未用变量、空 catch、`printStackTrace`、静态 `SimpleDateFormat` 字段、魔法值：静态检查能查。
- `split(",")` 不传 limit、`trim()` 当去空白、循环内 `s += x`、`replaceAll` 传字面量、`toLowerCase()` 不传 `Locale`：写代码时本能会做对，审查时顺带扫一眼即可，不单独立组。

## 边界

本文件只收 **PMD 查不出、出错也不报错** 的写法。能静态判定的交给项目的静态检查；空指针解引用、资源泄漏、
弱加密 / SQL 注入等字节码级问题需 SpotBugs / Semgrep。这两类本技能都不含。
