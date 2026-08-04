# Test Prompts（v3.4.0 达尔文盲评）

> 11 条 prompt：T1-T8 回归集（覆盖 12 域核心 antipattern，确保精简无退步）+ T9-T11 对抗集（直击五类问题根因）。

## 回归集（T1-T8）

### T1 · 字符串判空 + Optional 取值（域 01）
我在校验用户输入，写了 `if (str != null && !str.trim().isEmpty())`，还有一处 `User u = findUser(id).get();`。这样写有什么问题？项目有 Hutool。

### T2 · 集合分块 + 分组（域 02，回归重点）
我要把一个 list 按每 50 个一组分块处理，还要按部门分组转 Map。现在我用了 `list.subList(from, to)`。另外想确认 `CollUtil.groupBy` 和 `CollUtil.shuffle` 能不能用。

### T3 · 日期格式化 + 当前时间（域 03）
我用了 `private static final SimpleDateFormat SDF` 做共享格式化，取当前时间用 `LocalDateTime.now()`。项目里还在用遗留 `java.util.Date`。

### T4 · 文件读写 + HTTP + JSON（域 04）
我要读 UTF-8 文本文件、复制文件、发 HTTP GET 拿 JSON 反序列化成对象。现在手搓了 `FileInputStream`+`readLine` 循环和 `HttpURLConnection`，JSON 手拼字符串。项目是纯 Java（无 Spring）。

### T5 · 线程池 + 异步（域 05）
我用 `Executors.newFixedThreadPool(10)` 跑并发任务，还有一个 `CompletableFuture.supplyAsync(() -> fetchUser(id))` 链式调用。这样写有什么风险？

### T6 · BigDecimal 除法 + 比较（域 10，回归重点）
金额计算：`bd1.divide(bd2)` 和 `new BigDecimal("1.0").equals(new BigDecimal("1.00"))`。为什么除法有时抛异常？为什么比较不对？

### T7 · 加密 + 密码哈希（域 07）
我要算 MD5 和存用户密码。现在手搓了 `MessageDigest` + `Integer.toHexString`，密码用 `SecureUtil.md5(rawPassword)`。

### T8 · 异常处理 + 日志 + 随机（域 08）
我写了 `catch (Exception e) {}` 空吞、`log.error("失败:" + e.getMessage())`、还有 `(int)(Math.random()*100000)` 当订单序号。逐个指出问题。

## 对抗集（T9-T11）

### T9 · 对抗·悬空引用（根因 1：坐标走断链）
我要在项目里用 MapStruct 做 Bean 映射 + OkHttp3 做 HTTP 调用。请告诉我 MapStruct 1.5.5.Final 的完整 Maven 坐标（含 annotation processor 配置）和 OkHttp3 的坐标。技能里哪里能找到？

### T10 · 对抗·删强约束提醒（根因 2：规则判据是否丢失）
我要写金额计算的 BigDecimal 代码：除法、比较、舍入。请把所有相关规则一次给我（除法怎么写、为什么 equals 不行、RoundingMode 怎么选、Math.abs 边界坑）。这些规则在技能的哪些位置？

### T11 · 对抗·跨文件去重（根因 4：ScopedValue 真值源）
JDK 25 项目，我要用 ScopedValue 替代 ThreadLocal 传请求上下文。请给我完整用法（基本绑定、嵌套绑定、与 ThreadLocal 的对比）。这些在哪个 reference 文件？另一个文件（09）里有没有重复？
