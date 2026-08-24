# 实跑验证记录（v1.5.0 回归轮）

> 环境：Windows Git Bash + JDK 21（Temurin 21.0.12）+ Maven 3.9.16（mvn.cmd）。日期：2026-08-24。
> 目的：验证 v1.5.0 新写的 06 §1 栈基线决策表（坐标组合与版本分界）与 §3 关键写法、05 JaCoCo 接入指引在真实 Maven 项目中成立。不空想。

## 实跑一：非 Spring 最小项目（06 §1 非 Spring 分支 + §3 写法）

项目：`/tmp/jut-live-run`（scratch，不入 git）。坐标按 §1 指引现场填稳定版：junit-jupiter 5.11.0 + mockito-core 5.11.0 + assertj-core 3.26.3（均 scope=test）。

测试类覆盖 06 §1/§3 + SKILL.md 断言策略的全部关键写法：

| 验证点 | 来源 | 结果 |
|---|---|---|
| `@Mock` + `@InjectMocks` + `MockitoAnnotations.openMocks` 标准注入 | 06 §3.1 | ✅ 绿 |
| `verify(mock, times(1))` 恰好一次语义 | 06 §3 隐蔽坑② | ✅ 绿 |
| `assertThrows` 验类型 + 消息 | 06 §2 映射表 | ✅ 绿 |
| `@ParameterizedTest` + `@MethodSource` | 06 §2 映射表 | ✅ 绿 |
| `mockStatic` + try-with-resources（**Mockito 5.x 仅 mockito-core，无 mockito-inline**） | 06 §1 决策表 + §3.4 | ✅ 绿 |
| `spy` + `doReturn().when()`（不用 when().thenReturn()） | 06 §3 隐蔽坑① | ✅ 绿 |
| AssertJ `extracting(三个方法引用).containsExactly(...)` 字段分组断言 | SKILL.md 断言库策略 | ✅ 绿（注：需对**单个对象**断言；包进 List 会走 Tuple 重载编译失败——写法示例见本记录附注） |

**结果：`Tests run: 8, Failures: 0, Errors: 0`**（surefire 报告）。§1 非 Spring 坐标组合与版本分界（5.x 免 inline）实测成立。

实跑中踩掉的两个测试代码自身错误（非技能问题，记录备查）：
1. `extracting` 多参对 List 包裹对象走 `containsExactly(Tuple...)` 重载 → 编译失败；改为对单对象断言后通过。技能内示例写法（`extracting(...).containsExactly(...)`）对应单对象用法，成立。
2. 对已有 spy 再 `spy()` 二次包装 → Mockito 5 抛 "Spy is not allowed on mock"；单层 spy 后通过。

## 实跑二：Spring Boot parent + JaCoCo 接入（05 JaCoCo 节）

项目：`/tmp/jut-boot-run`（scratch）。parent spring-boot-starter-parent 3.5.0 + `spring-boot-starter-test`（无版本，BOM 管）+ jacoco-maven-plugin（prepare-agent + report 绑 test phase）。

| 验证点 | 结果 |
|---|---|
| starter-test 无版本坐标（BOM 管理） | ✅ 成立 |
| `mvn test` 后 `target/site/jacoco/index.html` 生成 | ✅（前提：**项目须有 main classes**——纯 test-only 项目 report 执行但无输出，本实跑先踩到后补 main 类验证） |
| Branch 判据可机械读取 | ✅ csv：`BRANCH_MISSED=2, BRANCH_COVERED=4`，与故意留的 2 个分支盲区（负数 throw / 0-99 return）精确对应——SKILL.md DoD「Branch 列 Missed = 0」判据在真实报告成立 |
| **插件无 `<version>` 的行为** | ❌ **推翻 v1.5.0 原表述**——见下 |

### 实跑发现的事实错误（已修复）

v1.5.0 原 05 写"spring-boot-starter-parent 的 pluginManagement 已管理 JaCoCo 插件版本，可不写 `<version>`"。实测：

- 插件留空版本时 Maven 发 `WARNING: 'build.plugins.plugin.version' for org.jacoco:jacoco-maven-plugin is missing ... threaten the stability of your build`，并去仓库下载 `maven-metadata.xml` 解析 **latest release（0.8.15）**；
- `help:effective-pom` 核实：parent 的 pluginManagement **不含** jacoco 条目——版本是 metadata 解析结果，非 parent 管理。

**修复**（落 `skills/java-unit-test/references/05-coverage-and-quantity.md`）：插件 `<version>` 建议显式写（填当前最新稳定），并注明实测依据；同时澄清 06 §1"坐标不硬编码版本数字"的语义（agent 现场填数字，非 XML 省略标签）。修复随本轮评估 commit 提交，v1.5.0 未发布、无需 bump。

## 结论

- 06 §1 决策表坐标组合与版本分界：**实测成立**（8/8 + 2/2 绿）。
- 05 Branch Missed 判据：**实测可机械执行**。
- 实跑抓出 1 个事实错误（pluginManagement 表述）并已修复——本轮"不空想"的直接收益。
