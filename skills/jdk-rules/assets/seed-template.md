---
paths:
  - "**/*.java"
---
<!-- seeded: jdk-rules@⟨版本⟩ -->

# Java 编码基线

> 由 `jdk-rules` 播种，可整文件重新生成。`paths` 决定加载时机：Read/Write/Edit 触及任何 `.java` 时注入。

## 事实

- 目标 JDK ⟨版本⟩：更高版本才有的 API 与语法一律不用（`List.of` 9+、`record` 16+、虚拟线程 21+）

## 流程

- 写方法前先定返回契约：无结果返回什么、null 参数怎么办、重复 key 留谁；需求没说明按下方边界基线
- 合并前跑 PMD：项目有 `.qualitygate/pmd-pom.xml` 就 `mvn -f .qualitygate/pmd-pom.xml pmd:check -B`，有违规按输出修代码，不改规则集
- 新 API 不确定版本 → 查技能 `jdk-rules` 的 `references/07-jdk-version-matrix.md`

## 边界基线

| 分歧点 | 默认 |
|---|---|
| 无结果 | 单条 `Optional`；列表空集合；不用 null、不用 0 代替无数据 |
| 必填参数为 null | `Objects.requireNonNull`，不编默认值 |
| 集合中的 null 元素 | 跳过 |
| 重复 key | `putIfAbsent` 保留首条 |
| 非法参数 | 展示层容错，领域层 fail fast |

## 写法基线

| 手写 | 换成 |
|---|---|
| `if (a > b) return a; return b;` | `Math.max(a, b)` |
| 循环累加 / 求最值 | `Arrays.stream(...).sum()` / `max()` |
| `containsKey` + `get` 两段式 | `computeIfAbsent` |
| `get` 判空再 `put` 累加 | `merge(k, 1, Integer::sum)` |
| `new ArrayList` 后连续 `add` | `List.of(...)`，需可变再包一层 |
| 循环拼分隔符 | `String.join` / `Collectors.joining` |

## 边界

- 第三方库的 API 用法与坐标选型不在本规则内；工程分层见对应框架技能
- 完整规则见技能 `jdk-rules`
