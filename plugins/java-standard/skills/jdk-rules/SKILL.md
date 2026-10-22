---
name: jdk-rules
slug: jdk-rules
displayName: JDK 编码规则
description: >-
  JDK 标准库编码规范，不含第三方库 API 用法与工程分层。
  编写、修改、审查 Java 代码时使用，也用于确认某个 API 在目标 JDK 版本上是否可用。
  覆盖范围：判空与 Optional、集合与 Map 增改、字符串、数值精度与日期时间、
  Stream 与 Collectors、异常与资源管理、API 版本门控；附带 git pre-commit 门禁（PMD）的装配与说明。
  触发信号：containsKey 后紧跟 get、map.get 判空再 put、手写 if 求 max/min/abs、
  new ArrayList 后连续 add、new BigDecimal(double)、BigDecimal 用 equals 比较、
  裸 divide、split 不传 limit、Optional.get() 无检查、Collectors.toMap 无 merge、
  Arrays.asList(基本类型数组)、getter 直接返回内部集合。
  不适用：第三方库选型与 API 用法、Spring 分层与工程组织、测试框架、
  Sonar/Checkstyle 等其他门禁工具。
version: "1.1.1"
last_verified: "2026-10-22"
---

# JDK 编码规则

只覆盖两件事：**JDK 已有现成写法时不要手写**、**目标 JDK 版本决定能用什么**。

## 四条铁律

1. **门禁先行**：项目没有 `.qualitygate/pmd-pom.xml` 时，先按「静态检查」一节装好门禁再写代码，装完真跑一次 `git commit` 验证被拦。装不上就明说没装，不许当成已启用。
2. **先确认版本，再写语法**：目标 JDK 不明时读 `pom.xml` / `build.gradle`，禁止凭印象使用 `List.of` / `var` / `record`。
3. **标准库优先**：JDK 一行能写完的，不写循环和 if；动笔前对照「手写 → 标准库」表。这条只约束写法，不豁免判空——外部输入与公开方法的判空照做（见 `references/01-null-and-optional.md`「要不要判空」）。
4. **不引库，只推荐**：不给任何第三方库的 API 用法；项目缺能力时按下表推荐一次，用户拒绝就用 JDK 原生。

## 第 0 步：确认目标 JDK

读 `maven.compiler.release` / `<source>` / `sourceCompatibility` / `java.toolchain`；均读不到时询问一次目标 JDK 版本。
除版本外不需要其他项目信息。

## 版本门控

判据：`目标 JDK ≥ 特性最低版本` 可用，否则禁用。LTS 锚点 8 / 11 / 17 / 21 / 25。

| API / 语法 | 最低 JDK |
|---|---|
| `Objects.equals`、`Comparator.comparing`、`Map.getOrDefault`、`ThreadLocalRandom`、`Arrays.stream` | 8 |
| `List.of` / `Set.of` / `Map.of`、`Objects.requireNonNullElse`、`Optional.ifPresentOrElse`、`Stream.ofNullable`、`takeWhile` / `dropWhile` | 9 |
| `List.copyOf` / `Set.copyOf` / `Map.copyOf`、`Collectors.toUnmodifiableList`、`Optional.orElseThrow()` 无参 | 10 |
| `String.isBlank` / `strip` / `lines` / `repeat`、`Files.readString` / `writeString`、`Predicate.not` | 11 |
| `String.indent` / `transform`、`Collectors.teeing` | 12 |
| `switch` 表达式（箭头 / `yield`）、NPE 精确到变量名 | 14 |
| 文本块 `"""`、`String.formatted` | 15 |
| `record`、`Stream.toList()`（不可变）、`instanceof` 模式匹配 | 16 |
| `sealed` | 17 |
| `switch` 模式匹配 + 守卫、虚拟线程、`SequencedCollection`（`getFirst` / `getLast` / `reversed`）、`Math.clamp` | 21 |
| 未命名变量 `_` | 22 |
| `Stream.gather`（Gatherers，自定义中间操作） | 24 |

> 非 LTS 版本按版本号比较，不另设档位；preview / incubator 一律不用。同一意图在各版本的写法对照见 `references/07-jdk-version-matrix.md`。

## 手写 → 标准库

| 手写 | 换成 |
|---|---|
| `if (a > b) return a; return b;` | `Math.max(a, b)` |
| `if (x < 0) return -x; return x;` | `Math.abs(x)`（`Integer.MIN_VALUE` 除外） |
| 循环累加 | `Arrays.stream(arr).sum()`；怕溢出用 `Math.addExact` |
| 循环找元素 | `stream().filter(p).findFirst()` |
| `if (!map.containsKey(k)) map.put(k, new X()); return map.get(k);` | `map.computeIfAbsent(k, x -> new X())` |
| `Integer v = map.get(k); if (v == null) put(k, 1); else put(k, v + 1);` | `map.merge(k, 1, Integer::sum)` |
| `List l = new ArrayList<>(); l.add(a); l.add(b);` | `List.of(a, b)`；需可变用 `new ArrayList<>(List.of(a, b))` |
| 循环拼分隔符 | `String.join(",", list)` / `Collectors.joining(",")` |
| `s != null && !s.trim().isEmpty()` | `s != null && !s.isBlank()`（11+） |
| `(x, y) -> x.age - y.age` | `Comparator.comparingInt(Foo::getAge)` |
| 手写 `hashCode` 连乘 | `Objects.hash(a, b)` |
| `if (n == null) return 默认; return n;` | `Objects.requireNonNullElse(n, 默认)`（9+） |

完整清单见各域 reference，此处只列高频项。

## S 级：语法合法但运行期出错

以下 PMD 实测全部查不出（0/8 命中），必须自查。

| 陷阱 | 正确做法 |
|---|---|
| `bd1.equals(bd2)` —— 受 scale 影响，`1.0` 与 `1.00` 为 false | `bd1.compareTo(bd2) == 0` |
| 裸 `bd.divide(bd2)` —— 非整除抛 `ArithmeticException` | 给 scale + `RoundingMode` |
| `split(",")` 不传 limit —— 尾随空串被丢弃，下标错位 | 需全字段用 `split(",", -1)` |
| `Optional.get()` 无检查 | `orElse` / `orElseThrow` |
| `Collectors.toMap(k, v)` 无 merge —— 重复 key 抛 `IllegalStateException` | 第三参 `(a, b) -> a`，或改用 `groupingBy` |
| `subList` 结果当独立列表 | `new ArrayList<>(sub)` / `List.copyOf(sub)` |
| `Arrays.asList(基本类型数组)` —— 得到 `List<int[]>`，只有一个元素 | `Arrays.stream(arr).boxed().toList()` |
| `Math.abs(Integer.MIN_VALUE)` —— 仍为负 | `Math.abs((long) x)` 或先判边界 |
| `List.of` / `Arrays.asList` 结果做 `add` —— `UnsupportedOperationException` | 需要可变就 `new ArrayList<>(...)` |
| `getXxx()` 直接返回内部集合引用 | `List.copyOf(...)` |
| `new BigDecimal(0.1)` 用 double 构造 | `new BigDecimal("0.1")` / `BigDecimal.valueOf(0.1)` |
| `catch (InterruptedException e) {}` 空吞且不恢复中断 | 加 `Thread.currentThread().interrupt()` |

## 静态检查（PMD）

门禁挂在项目自己的 **git pre-commit** 上，任何来源的提交都生效，不依赖编辑器或 AI 工具。priority 达到阻断阈值的违规让 `pmd:check` 退出码为 1，`git commit` 中止并在终端列出「类名:行 规则 消息」——本技能不解析报告，阈值与打印在 pom 里配置。

- 模板默认 `failurePriority=1`，只拦 Blocker：空 catch、资源未关闭、`Executors` 建线程池、`@Transactional` 缺 `rollbackFor`。这四类在真实项目里数量可控（965 文件的 JDK 8 项目实测 8 条、5235 文件的 JDK 17 项目 20 条），且全是真问题。
- 设为 `2` 会同时拦 Critical（非穷尽 `switch`、`PreserveStackTrace`、字面量比较等），实测两个项目分别升到 18 / 40 条，需先治理存量。
- 跳过：`git commit --no-verify`，或 `JAVA_STANDARD_GATE=off git commit ...`。
- 写代码时不必主动跑 PMD，被拦按输出修。

**初始化**（项目首次且要提交 Java 时做，需用户同意）：

1. 复制 `assets/` 四个文件：`pmd-pom-template.xml` → `.qualitygate/pmd-pom.xml`；`pmd7-ruleset.xml` → `.qualitygate/`；`pre-commit` → `.qualitygate/hooks/`；`install-hook` → `.qualitygate/`。
2. 补 `compileSourceRoots`：Glob 列 `**/src/main/java/`（排除 `target/`），每个源码根一行 `${project.basedir}/../<模块>/src/main/java`；单模块保留模板默认行。
3. `maven.compiler.release` 填第 0 步确认的版本。
4. `.gitignore` 只加 `.qualitygate/target/`——pom、规则集、两个 sh 都要入库，团队共用同一份口径。
5. `git add -A` 后执行 `sh .qualitygate/install-hook`——先 add，索引里才有执行位可改。幂等，可重复执行：自动区分「已有 husky」「已有手写 pre-commit」「两者都没有」三种情况，不覆盖别人的 hook，并打印 git **实际会执行**的 hook 路径。
6. 真跑一次 `git commit` 验证（见下）。

脚本输出的提示要照做，两条都是静默失效的来源：索引里执行位是 `100644`（Windows `core.filemode=false`，`chmod` 不进索引，同事检出后 git 跳过 hook）；`core.hooksPath` 写在 `.git/config` 不入库，**必须明确告诉用户团队每人在克隆后各执行一次 `sh .qualitygate/install-hook`**。最容易出现的状态是「以为全组都在拦」。

**验证要真跑**：暂存一个含违规的 `.java`，真执行 `git commit`，确认退出码非 0 且终端打出 `PMD Failure: 类名:行 Rule:... Priority:1`，再确认 `git log` 里没有这次提交。只看配置文件对不对不算验证——漏列源码根、执行位丢失、`failOnViolation=false` 都会让门禁静默放行。

**存量先摸清**：初始化时先 `mvn -f .qualitygate/pmd-pom.xml pmd:pmd -q`，读 `.qualitygate/target/pmd.xml` 统计 priority 1 的条数：0 条直接启用；15 条以内连修复一起做，修完再装；更多则先不装 hook、只手动跑，清到阈值内再装。

**三个会静默失效的配置**：

- `compileSourceRoots` 只接受相对 `${project.basedir}` 的路径。写绝对路径（`I:/proj/x/src/main/java`）不报错，但 PMD 扫 0 个文件，报告为空——把绝对路径当成相对路径拼接后自然找不到。初始化后确认报告里有 `<file>` 节点，别只看 BUILD SUCCESS。
- 往 `pmd7-ruleset.xml` 加注释时不能出现连续两个减号（如命令行参数写法），XML 注释到此终止，规则集整份加载失败。改完用 `python -c "import xml.etree.ElementTree as ET; ET.parse('pmd7-ruleset.xml')"` 过一遍。
- 脚本行尾必须是 LF。`core.autocrlf=true` 的机器会把 `.qualitygate/hooks/pre-commit` 检出成 CRLF，shebang 变成 `#!/bin/sh\r`，Linux/macOS 上 git exec 直接失败，门禁**静默消失**（Windows 上看不出来）。在项目 `.gitattributes` 加 `/.qualitygate/hooks/pre-commit text eol=lf` 与 `/.qualitygate/install-hook text eol=lf`。

**第三方源码副本会被一起扫**：有些项目把框架类复制进 `src/main/java` 打补丁（实测见到 `org/springframework`、`liquibase`、`org/flowable` 三类）。这些代码不归团队维护，报出来的违规改不了。初始化时若发现此类目录，在 pom 里加 `<excludes><exclude>**/org/springframework/**</exclude></excludes>`，或直接不管——它们多是 Critical，默认阈值 1 不拦。

`pmd:pmd` 恒 exit 0（报告照常生成），只有 `pmd:check` 用退出码表达结果：全量体检用前者，门禁用后者。

**版本错配的报错不都说得清楚**（实测：目标版本低于写法时）：

| 写法 | 目标版本 | 报错 | 能看出是版本问题吗 |
|---|---|---|---|
| `record`、文本块 | ≤ 11 | `records are not supported in -source 11` | 能，明确说了版本 |
| PMD 侧 | — | `Record declarations are a feature of Java 16` | 能 |
| `var` | 8 | `cannot find symbol`，`symbol: class var` | **不能**，像漏了声明 |
| `List.of` / `Map.of` / `isBlank` | 8 | `cannot find symbol`，`symbol: method of(...)`，`location: interface List` | **不能**，像方法名写错 |

判据：报错是 `cannot find symbol`（中文环境为「找不到符号」，Maven 在中文 Windows 上输出 GBK）且 `symbol` 是 `class var`、或 `method` 名属于 JDK 9+ API 时，先怀疑版本再改代码——不要顺着报错去补 import 或改方法名，那会把版本问题改成一堆无用代码。

处理一律是把语法降到目标版本。禁止调高 `maven.compiler.release` / `source` 掩盖：那只会让项目在真实构建环境编译不过。同类 `ParseException` 报给用户一同说明。

## 库探测（只推荐，不教用法）

读 `pom.xml` / `build.gradle` 一次，只在下表能力**缺失且任务确实需要**时推荐一次：

| 能力 | 已探测到就不管 | 缺失时推荐 |
|---|---|---|
| 判空 / 集合 / 字符串 / 日期 | `hutool-*`、`commons-lang3`、`guava` | 国内栈 `cn.hutool:hutool-bom`；Spring 国际栈 `commons-lang3` |
| 加密 / 哈希 / 密码 | `hutool-crypto`、`spring-security-crypto`、`bcprov` | `cn.hutool:hutool-crypto`（含 BCrypt） |
| Bean 映射 | `mapstruct`、`spring-beans` | `org.mapstruct:mapstruct`（编译期生成） |
| JSON | `jackson-databind`、`gson`、`fastjson2` | 跟随项目；无则 Jackson |
| HTTP | `okhttp`、`httpclient5`、`spring-webflux` | Spring 项目跟随 Spring；纯 Java 用 OkHttp |

只给坐标加一句理由，**不给 API 示例**。用户拒绝就用 JDK 原生受控降级，不追问第二次。

## 项目播种

`.claude/rules/` 是比本技能更早生效的注入点：带 `paths` 的规则在 Read/Write/Edit 触及匹配文件时自动加载，不依赖 skill 是否被匹配到。种子只承担本技能做不到的一件事——**在写代码之前就把「门禁装没装」和「目标 JDK」摆到眼前**。

**触发**：项目无 `.claude/rules/jdk-rules.md`，或首行 `<!-- seeded: jdk-rules@x.y.z -->` 低于本技能版本 → 提议播种，一句话说明收益，等用户确认，不擅自写项目文件。

**落点**：`.claude/rules/jdk-rules.md`，模板 `assets/seed-template.md`，`paths` 固定 `"**/*.java"`；模板里的 `⟨版本⟩` 填本技能 frontmatter 的 `version`。Claude Code 原生递归加载 `.claude/rules/*.md`，不需要 `@import`，不碰 `CLAUDE.md`。已有文件无 `<!-- seeded:` 标记说明是用户自己写的，只补缺失事实、保留原文。

**写什么**：目标 JDK 一条事实 + 门禁装配、被拦怎么修两条流程 + 6 条最高频写法对照。**S 级陷阱清单不写**——A/B 实测模型本就全部避开，写进种子只是常驻上下文的噪音。

## 决策路由

| 场景 | 读 |
|---|---|
| 判空、`Optional`、null 约定 | `references/01-null-and-optional.md` |
| 集合选型、`Map` 增改、比较器、不可变 | `references/02-collections.md` |
| 字符串、格式化、`join` / `split` | `references/03-string.md` |
| 整数溢出、`BigDecimal`、日期时间 | `references/04-number-and-time.md` |
| `Stream` / `Collectors` 用法与误用 | `references/05-stream-collect.md` |
| `try-with-resources`、异常链、受检异常 | `references/06-exception-and-resources.md` |
| API→版本反查、同一意图×版本写法 | `references/07-jdk-version-matrix.md` |

## 使用流程

1. 确认目标 JDK（读 pom，均读不到时问一次）。项目没有种子时按「项目播种」提议。
2. 按决策路由读对应 reference，写作前完成阅读。
3. 写代码时对照「手写 → 标准库」与 S 级清单。
4. commit 由项目 pre-commit 把关：被拦按输出修后重新提交；版本错配按上表判据改代码，不调 `maven.compiler.release` 掩盖。
5. 缺能力时才查库探测表，推荐一次。
