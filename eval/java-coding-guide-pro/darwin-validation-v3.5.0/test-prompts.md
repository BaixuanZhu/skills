# Test Prompts（v3.5.0 达尔文回归盲评）

> 14 条 prompt：T1-T8 回归集（沿用 v3.4.0 轮的 8 条，覆盖 12 域核心 antipattern，确保三处内容压缩无退步）+ T9-T14 对抗集（直击本轮六类改动根因）。

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

### T9 · 对抗·出处引用与 IDE 指引删除（根因：规约/import 规则是否仍可查）
两个问题：① 我重构删掉了 `OrderVO` 在这个文件的最后一处使用，`import com.demo.order.OrderVO;` 要不要动？有什么规则？② 帮我过一遍命名规约：POJO 布尔属性、抽象类命名、异常类命名、常量定义、`long` 字面量。这些规则在技能哪里？

### T10 · 对抗·JDK 版本门控新判据（根因：五档累加 → 特性最低版本）
项目分别用 JDK 8 / 11 / 16 / 17 / 21 / 25，逐个告诉我：能不能用 `var`、`record`、文本块、`switch` 表达式、`sealed`、`Stream.toList()`、虚拟线程？特别地：JDK 16（非 LTS）能不能用 `record`？JDK 21 虚拟线程里能不能用 `synchronized`，JDK 25 呢？判据是什么？

### T11 · 对抗·S3252 策略段删除（根因：字符串工具默认是否明确）
项目有 Hutool。写 Hutool 字符串判空用 `StrUtil.isBlank` 还是 `CharSequenceUtil.isBlank`？如果团队 Sonar 门禁开了 S3252 把 `StrUtil.isBlank` 扫出来了，按这个技能该怎么处理？

### T12 · 对抗·高风险表压缩（根因：C-CHECK 触发范围 + HTTP 超时规则是否丢失）
两个问题：① 哪些场景在项目缺对应能力时必须先问用户再引入新库？哪些场景永远不问？② 纯 Java 项目用 OkHttp3 发请求，客户端实例怎么建？超时怎么设？规则和示例代码在技能哪里？

### T13 · 对抗·规则表 why 列删除（根因：技术判据折入是否完整）
规则表没有「为什么」列了，请验证这些判据还能不能查到，逐条给出技能内位置：① `Calendar` 的月份从几开始；② Spring 与 Apache 的 `BeanUtils.copyProperties` 有什么区别；③ `RandomUtil.randomInt(min, max)` 含不含上界 max；④ 裸 `LocalDateTime.now()` 隐式依赖什么；⑤ 无用 import 对应的 Sonar 规则号；⑥ 认知复杂度对应的 Sonar 规则号和阈值。

### T14 · 对抗·构件版本表与日志门控（根因：坐标可查性 + JDK 8 日志组合）
JDK 8 的纯 Java 项目要引入日志，坐标怎么写？JDK 17 的项目呢？两套能不能混用？另外给我 MapStruct 1.5.5.Final、Jackson、OkHttp3、Lombok 的参考版本。这些在技能哪里？
