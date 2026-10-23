---
name: java-contract
slug: java-contract
displayName: Java 编码契约
description: >-
  为项目建立并执行 Java 编码契约：读 pom 定目标 JDK，把需求没说明的边界决策（空结果 / null 参数 /
  重复 key / 非法参数 / 静态还是实例）落成 .claude/rules/java-contract.md，写完即编译验证，
  审查时按静默陷阱清单逐条对照。
  在编写、修改、审查 Java 代码时使用；也用于确认某个 API 在目标 JDK 上是否可用、
  决定方法该返回 null 还是空集合、为项目配置 CI 静态检查。
  触发信号：新写工具类或 Service 方法、containsKey 后紧跟 get、map.get 判空再 put、
  put 与 putIfAbsent 混用、分页参数校验、cannot find symbol 且 symbol 是 var 或 JDK 9+ 方法名、
  split 不传 limit、BigDecimal 用 equals 比较、Collectors.toMap 无 merge、catch 块有语句但无处理。
  不适用：第三方库 API 用法与选型、Spring 分层与工程组织、测试框架、前端代码。
version: "2.0.0"
last_verified: "2026-10-23"
---

# Java 编码契约

模型对 JDK 写法的判断已经够准（实测语法陷阱 3/3、7/7 全部避开），真正的分歧在**需求文档不写、
几个实现会给几种答案**的地方。本技能只做三件事：把这些决策定下来并落成项目文件、把版本约束住、写完验证。

## 三条原则

1. **契约先落盘**。第一次在项目里写 Java 时，把六项边界决策写进 `.claude/rules/java-contract.md`。
   之后每次触碰 `.java` 该文件自动注入，跨会话、跨并行 agent 拿到同一套答案。不落盘的决策等于没定。
2. **版本从 pom 来**。读 `maven.compiler.release` / `<source>` / `sourceCompatibility` / `java.toolchain`，
   四者都读不到才问一次。禁止凭印象用 `List.of` / `var` / `record`。
3. **写完即编译**。一个类写完就 `mvn -q compile`（Gradle：`./gradlew compileJava`）。版本不匹配在这一步
   暴露，比背着规则表写 200 行再让 CI 拦下来便宜。

## 第一步：读项目

三件事都在仓库里，做完再动笔：

| 读什么 | 得到什么 |
|---|---|
| `pom.xml` / `build.gradle` | 目标 JDK；`<modules>` 说明是否多模块 |
| `.claude/rules/java-contract.md` | 已有契约。存在就遵守，不重新提议 |
| 同包下 2~3 个同类方法 | 既有惯例：返回 `Optional` 还是裸值、抛异常还是错误码 |

**项目惯例与下表默认冲突时，惯例优先。** 契约的作用是消除分歧，不是推行新风格。

## 契约六项

需求没说明时按下表取；项目已有不同做法就记进契约文件，不在代码里另搞一套。

| 分歧点 | 默认 |
|---|---|
| 无结果 | 单条 → `Optional`；列表 → 空集合；聚合值 → `Optional` 或抛异常。不返回 null，不用 0 代替「无数据」 |
| 必填参数为 null | `Objects.requireNonNull` 抛异常，不编默认值 |
| 集合中的 null 元素 | 跳过，不参与计算 |
| 重复 key | `putIfAbsent` 保留首条；要覆盖用 `put` 并在注释写明原因 |
| 非法参数 | 展示层容错（`pageNo < 1` 纠正为 1），领域层 fail fast（状态码不认识就抛） |
| 静态还是实例 | 纯函数 `static`；依赖注入用实例；同一个类不混用 |

每项的判断依据与反例见 `references/01-contract.md`。

**落盘**：模板 `assets/contract-template.md` → `.claude/rules/java-contract.md`，`paths` 固定
`"**/*.java"`，首行标记 `<!-- seeded: java-contract@⟨版本⟩ -->`，`⟨版本⟩` 填本文件 frontmatter 的 `version`。
文件已存在且无该标记，说明是用户自己写的——只补缺失事实，不改原文。

## 版本门控

判据：`目标 JDK ≥ 特性最低版本` 可用，否则禁用。LTS 锚点 8 / 11 / 17 / 21 / 25；非 LTS 按版本号比较，
preview / incubator 一律不用。

| 特性 | 最低 JDK |
|---|---|
| `Objects.equals`、`Comparator.comparing`、`Map.getOrDefault`、`ThreadLocalRandom`、`Arrays.stream` | 8 |
| `List.of` / `Set.of` / `Map.of`、`Objects.requireNonNullElse`、`Optional.ifPresentOrElse`、`Stream.ofNullable`、`takeWhile` / `dropWhile` | 9 |
| `List.copyOf` / `Map.copyOf`、`Collectors.toUnmodifiableList`、`Optional.orElseThrow()` 无参 | 10 |
| `String.isBlank` / `strip` / `lines` / `repeat`、`Files.readString` / `writeString`、`Predicate.not` | 11 |
| `switch` 表达式（箭头 / `yield`）、NPE 精确到变量名 | 14 |
| 文本块 `"""`、`String.formatted` | 15 |
| `record`、`Stream.toList()`（不可变）、`instanceof` 模式匹配 | 16 |
| `sealed` | 17 |
| 虚拟线程、`switch` 模式匹配 + 守卫、`SequencedCollection`、`Math.clamp` | 21 |
| 未命名变量 `_` | 22 |

按 API 反查（集合 / 字符串 / 数值 / 语法 / 并发）、以及「同一意图 × 版本写法」见 `references/02-version-matrix.md`。

**报错判据**：`cannot find symbol` 且 `symbol` 是 `class var`、或方法名属于 JDK 9+ API 时，先怀疑版本，
不要顺着报错去补 import 或改名——那会把版本问题改成一堆无用代码。`record` / 文本块 / `switch` 表达式会
直接提示 `are not supported in -source N`，按提示降级写法。一律改代码，不改 `maven.compiler.release`，
那只会让产物在目标运行时 `UnsupportedClassVersionError`。

## 写完即验证

1. 编译：`mvn -q compile`。版本问题在这一步暴露，别留到 CI。
2. 契约相关分支至少跑一次：空入参、无结果、重复 key 三类各一个调用或用例。没有测试的，说明原因。
3. 项目有门禁就跑 `mvn -f .qualitygate/pmd-pom.xml pmd:check -B`，被拦按输出修。

## 审查（独立动作）

审查与生成分开做：写完立刻自审会顺着自己的思路看，最容易漏的是「返回契约与调用方期望不一致」。
审查时读 `references/03-review.md`，按它的顺序逐条对照——那份清单收的是 PMD 查不出、出错也不报错的写法。
可交给子代理执行，rubric 用项目里的契约文件。

## 门禁（可选，项目级）

一次性配置，之后由 CI 执行。`--no-verify` 能绕过的 git hook 不算强制，本技能不装钩子。

1. 复制 `assets/gate/pmd-pom-template.xml` → `.qualitygate/pmd-pom.xml`、`assets/gate/pmd7-ruleset.xml` → `.qualitygate/pmd7-ruleset.xml`。
2. 改两个字段：`maven.compiler.release` 填项目 JDK；`compileSourceRoots` 每个源码根一行，
   **必须相对 `${project.basedir}`**——写绝对路径不报错，但 PMD 扫 0 个文件、报告为空。
3. CI 加一步 `mvn -f .qualitygate/pmd-pom.xml pmd:check -B`；`.gitignore` 只加 `.qualitygate/target/`，其余入库共用。

默认 `failurePriority=1` 只拦 Blocker。接之前先 `pmd:pmd` 读 `.qualitygate/target/pmd.xml` 摸存量：
0 条直接接；15 条以内连修复一起做；更多先只手动跑，清到阈值内再接。

往 `pmd7-ruleset.xml` 加注释时不能出现连续两个减号，XML 注释到此终止，整份规则集加载失败。

## 库边界

读 `pom.xml` 一次，只在下表能力缺失且任务确实需要时推荐一次：

| 能力 | 缺失时推荐 |
|---|---|
| 判空 / 集合 / 字符串 / 日期 | 国内栈 `cn.hutool:hutool-bom`；Spring 国际栈 `commons-lang3` |
| Bean 映射 | `org.mapstruct:mapstruct`（编译期生成） |
| 加密 / 哈希 | `cn.hutool:hutool-crypto` |
| JSON / HTTP | 跟随项目既有栈；都没有则 Jackson / OkHttp |

只给坐标加一句理由，不给 API 示例。用户拒绝就用 JDK 原生，不追问第二次。

## 使用流程

1. 读项目（pom、契约文件、同类方法），确认目标 JDK。
2. 无契约文件时按「契约六项」提议落盘，等用户确认。
3. 定本次方法的返回契约，再动手。
4. 写代码；不熟悉的 API 查 `references/02-version-matrix.md`。
5. 写完编译，契约分支跑一次。
6. 需要审查时按 `references/03-review.md` 独立执行。
