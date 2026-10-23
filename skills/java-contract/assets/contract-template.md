---
paths:
  - "**/*.java"
---
<!-- seeded: java-contract@⟨版本⟩ -->

# Java 编码契约 · ⟨项目名⟩

> 由 `java-contract` 播种，可整文件重新生成。它**不会自动进上下文**——动手前需主动读一次。
> 「本项目」列有内容时以它为准，为空则取默认。这一列由本项目维护，改它不需要动技能。

## 事实

| 项 | 值 |
|---|---|
| 目标 JDK | ⟨版本⟩ —— 更高版本才有的 API 与语法一律不用 |
| 编译验证 | `⟨mvn -q compile / ./gradlew compileJava⟩` |

## 边界契约

| 分歧点 | 默认 | 本项目 |
|---|---|---|
| 无结果 | 单条 `Optional`；列表空集合；聚合看 0 是否有业务含义（求和→0，平均/最大→`Optional`）。不用 null | |
| null 参数 | 必填标量 `requireNonNull`，不编默认值；集合参数按空处理，业务要求非空用 `isEmpty()` 校验 | |
| 集合里的 null | `null` 元素跳过；字段无值：累加/平均跳过整条记录，拼接跳该值，排序/分页保留排末尾；**先剔除再切页** | |
| 重复 key | `putIfAbsent` 保留首条；覆盖需 `put` + 注释 | |
| 返回集合的形态 | 对外返回的 `Map` 保插入顺序，字典序用 `TreeMap`；默认不可变，`Map.copyOf` 不保序（用 `unmodifiableMap(new LinkedHashMap<>(x))`），8 用 `unmodifiableList(new ArrayList<>(x))` | |
| 非法参数 | 展示层容错（`pageNo < 1` 纠正为 1），领域层 fail fast | |
| 静态还是实例 | 纯函数 `static`，依赖注入用实例，同一个类不混用 | |

## 流程

- 写方法前先定返回契约；需求没说明按上表
- 写完编译：`⟨编译命令⟩`；契约相关分支（空入参 / 无结果 / 重复 key）至少跑一次
- 合并前跑门禁：`mvn -f .qualitygate/pmd-pom.xml pmd:check -B`（项目无 `.qualitygate/` 时跳过）
- 新 API 不确定版本 → 查技能 `java-contract` 的 `references/02-version-matrix.md`
- 审存量代码按 `references/03-review.md` 的顺序走，与生成分开做

## 边界

- 第三方库 API 用法与选型不在本契约内；工程分层见对应框架技能
- 完整规则见技能 `java-contract`
