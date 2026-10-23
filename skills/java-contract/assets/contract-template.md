---
paths:
  - "**/*.java"
---
<!-- seeded: java-contract@⟨版本⟩ -->

# Java 编码契约 · ⟨项目名⟩

> 由 `java-contract` 播种，可整文件重新生成。`paths` 决定加载时机：Read/Write/Edit 触及任何 `.java` 时注入。
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
| 必填参数为 null | `Objects.requireNonNull`，不编默认值 | |
| 集合中的 null 元素 | 跳过，不参与计算 | |
| 重复 key | `putIfAbsent` 保留首条；覆盖需 `put` + 注释 | |
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
