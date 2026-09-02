# Test Prompts（v3.6.0 达尔文回归盲评）

> 14 条 prompt：T1-T8 回归集（沿用 v3.4.0/v3.5.0 两轮的 8 条，覆盖 12 域核心 antipattern，确保「推荐示例」节删除与 09 精简无退步）+ T9-T14 对抗集（直击本轮五类改动根因：推荐示例删除、09 大精简、常量规则新增、Sonar 规则号全删、编号顺移）。

## 回归集（T1-T8，沿用上轮原文）

### T1 · 字符串判空 + Optional 取值（域 01）
我在校验用户输入，写了 `if (str != null && !str.trim().isEmpty())`，还有一处 `User u = findUser(id).get();`。这样写有什么问题？项目有 Hutool。

### T2 · 集合分块 + 分组（域 02）
我要把一个 list 按每 50 个一组分块处理，还要按部门分组转 Map。现在我用了 `list.subList(from, to)`。另外想确认 `CollUtil.groupBy` 和 `CollUtil.shuffle` 能不能用。

### T3 · 日期格式化 + 当前时间（域 03）
我用了 `private static final SimpleDateFormat SDF` 做共享格式化，取当前时间用 `LocalDateTime.now()`。项目里还在用遗留 `java.util.Date`。

### T4 · 文件读写 + HTTP + JSON（域 04）
我要读 UTF-8 文本文件、复制文件、发 HTTP GET 拿 JSON 反序列化成对象。现在手搓了 `FileInputStream`+`readLine` 循环和 `HttpURLConnection`，JSON 手拼字符串。项目是纯 Java（无 Spring）。

### T5 · 线程池 + 异步（域 05）
我用 `Executors.newFixedThreadPool(10)` 跑并发任务，还有一个 `CompletableFuture.supplyAsync(() -> fetchUser(id))` 链式调用。这样写有什么风险？

### T6 · BigDecimal 除法 + 比较（域 10）
金额计算：`bd1.divide(bd2)` 和 `new BigDecimal("1.0").equals(new BigDecimal("1.00"))`。为什么除法有时抛异常？为什么比较不对？

### T7 · 加密 + 密码哈希（域 07）
我要算 MD5 和存用户密码。现在手搓了 `MessageDigest` + `Integer.toHexString`，密码用 `SecureUtil.md5(rawPassword)`。

### T8 · 异常处理 + 日志 + 随机（域 08）
我写了 `catch (Exception e) {}` 空吞、`log.error("失败:" + e.getMessage())`、还有 `(int)(Math.random()*100000)` 当订单序号。逐个指出问题。

## 对抗集（T9-T14，直击本轮改动根因）

### T9 · 对抗·「推荐示例」节删除（根因：删而不丢——独有判据是否已迁入速查表）
四个问题：① `StrUtil.subAfter` 的第三个参数是干什么的？我要取文件名最后一个 `.` 之后的扩展名怎么写？② 把 source 的属性拷到一个**已存在**的 target 对象上，但 source 里为 null 的字段不要覆盖 target 已有值，用 Hutool 怎么写？③ 金额要千分位展示（两位小数、逗号分组），怎么写？④ 什么时候允许用 `String.format`，什么时候禁用？

### T10 · 对抗·09-modern-java 精简（根因：通用语法示例删除 + antipattern 迁移后是否仍可查）
① JDK 8 项目里能不能写 `var` / `record` / 文本块？判据在哪里？② `Stream.toList()` 返回的列表能不能 `add`？这个坑在技能哪里写了？③ JDK 25 用什么替代 ThreadLocal 传请求上下文？对比表在哪里？④ 虚拟线程 + `synchronized` 在 JDK 21 和 25 分别什么行为？依据哪个 antipattern？

### T11 · 对抗·常量与字面量新规则（根因：新规则是否可查且可机械执行）
我的代码里 `"PENDING"` 这个字符串在 `OrderService` 和 `RefundService` 各写了一遍，还有重试次数 `3`、超时 `5000L` 直接写在实现类里当 `private static final` 常量，别的类要用只能复制一份。这有什么问题？按技能的规则该怎么改？常量到底该放哪——判据是什么？我想建一个 `Constants` 类把所有常量放一起行不行？

### T12 · 对抗·Sonar 规则号删除（根因：规则本体是否随规则号一起丢失）
技能里已经不标 Sonar 规则号了。验证这些规则**本体**还能不能查到，逐条给出位置：① 无用 import 有哪几类、什么时候必须同步删；② 认知复杂度阈值是多少、超了怎么办；③ `SimpleDateFormat` 静态共享为什么危险、替代是什么；④ `Math.abs(Integer.MIN_VALUE)` 的结果是什么；⑤ 裸 `LocalDateTime.now()` 隐式依赖什么；⑥ `finally` 块里抛异常会怎样。

### T13 · 对抗·编号顺移与交叉引用（根因：11 重编号后引用是否断裂）
① 12-complexity 里引用了 11-conventions 的一条布尔表达式规则，顺着这个引用能不能找到？② 05-concurrency 里说 synchronized 陷阱「详见 09 的某个 antipattern」，顺着找能不能找到？③ SKILL.md 路由表里「常量与字面量」指向哪个文件？那个文件里对应规则存在吗？④ 11-conventions 的规则编号从 §1 到最后一节是否连续无断号？

### T14 · 对抗·示例删除后的综合可执行性（根因：删「推荐示例」后 agent 能否拼出完整代码）
用纯 JDK + Hutool 写一个 `batchProcess(List<Order> orders)`：入参判空守卫；按 100 个分块；每块提交线程池（有界队列、命名线程工厂、异常不外泄只记日志）；金额汇总用 BigDecimal（单价 × 数量再 setScale(2, HALF_UP)）；最后把 `Order` 拷贝成 `OrderVO`（null 不覆盖）。技能里需要的每一块（判空/分块/线程池/金额/拷贝）是否都能查到可直接照抄的写法？哪一块查不到就是缺陷。
