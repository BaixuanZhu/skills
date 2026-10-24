---
name: java-unit-test
slug: java-unit-test
displayName: Java 开发期测试
description: >-
  Java 开发期测试（纯单元测试）助手——@Mock + @InjectMocks 或项目既有的
  @TestConfiguration 轻量 mock 装配，AssertJ 断言，毫秒级，零外部基础设施
  （不连真实 DB / 容器 / 中间件）。在编写、评审、补全、重构单元测试时使用
  本技能，无论用户是否提到具体框架（unit test / JUnit / Mockito / 测试用例 /
  怎么测 / 测哪些 / 写多少）。
  次级触发信号——代码或 pom 中出现：spring-boot-starter-test、junit-jupiter、
  @Test / @BeforeEach / @ParameterizedTest / @MethodSource、
  assertEquals(new BigDecimal、BigDecimal 比金额、
  assertThat / isEqualByComparingTo / assertThatThrownBy（AssertJ）、
  @Mock / @InjectMocks / MockitoAnnotations.openMocks、spy( / mockStatic /
  MockedStatic / mockito-core、@MockBean / @MockitoBean 用于纯单测；
  用户任务词或痛点出现：只写 happy path、补测试不知道写几个、@MockBean 用于纯单测、
  测够了没 / 写到什么程度算够、mock 不到内部 new 的对象、异常断言断 RuntimeException。
  核心默认：AssertJ 断言（金额用 isEqualByComparingTo / compareTo，不用 equals）、
  一个方法四维度必检（正向/反向/边界/异常）、栈中立跟随项目既有（JUnit 4/5 均支持）。
  接口级验证（接口通不通）不写测试、不属本技能范围。
  不适用：切片 / 集成 / 冒烟 / E2E 测试（@SpringBootTest / @WebMvcTest /
  Testcontainers / REST Assured / WireMock）→ java-integration-test
  （明示或确认后激活）；性能测试、前端测试。
version: "2.1.1"
last_verified: "2026-10-24"
---

# Java 开发期测试

开发期测试 = **纯单元测试**：被测对象是真实对象，外部依赖用 mock，毫秒级，`mvn test` 秒级跑完——零外部基础设施（不连真实 DB / 容器 / 中间件）。默认 `@Mock`+`@InjectMocks`；项目既有 `@TestConfiguration` 手写 `@Bean` mock + `@Import` 的轻量装配惯例时跟随，但上下文里只允许 mock 与纯内存对象。

> 接口级验证（"接口通不通"）不写测试、不属本技能范围；需要真实依赖断言 / 可重复回归的集成测试 → java-integration-test，明示或确认后激活。

## 三条硬规则

1. **只 mock 外部依赖**（DB / RPC / 时间 / 第三方），不 mock 被测对象，也不指望 mock 被测类内部 `new` 出来的对象——那种情况测试会假绿，必须先把依赖改成构造器注入。
2. **金额与小数用 `compareTo`**：`assertThat(actual).isEqualByComparingTo("90.00")`。`BigDecimal.equals` 连 scale 一起比，实现改一次 `setScale` 断言就假红，scale 恰好一致时又掩盖了「本该固定两位小数」的问题。全项目一律不用 `assertEquals(BigDecimal, BigDecimal)`。
3. **异常断言到具体异常类 + 消息**，不断 `RuntimeException` / `Exception` 根父类——断根父类等于任何异常都能过。

## 断言库

**默认 AssertJ**（`spring-boot-starter-test` 已传递，非 Spring 项目按需引 `assertj-core`）：

| 场景 | 写法 |
|---|---|
| 金额、小数 | `isEqualByComparingTo("90.00")` |
| 抛异常 | `assertThatThrownBy(() -> ...).isInstanceOf(X.class).hasMessage("...")` |
| 集合内容 | `containsExactlyInAnyOrder(...)` / `extracting(Foo::getId)` |
| 简单值 | `isEqualTo(...)` |

项目已有测试统一用 JUnit 原生 `Assertions` 时跟随，但金额仍要 `compareTo(actual, expected) == 0`，不用 `assertEquals`。

## 写完自检四项

被测方法四维度各至少一条：**正向**（合法输入）/ **反向**（非法输入被拒绝）/ **边界**（端点、空、`null`、极值）/ **异常**（契约指定的异常类）。缺一维即设计漏洞。

多条件逻辑画决策表，列数即用例数；有状态对象按迁移列表走，合法与非法都要覆盖。这两件事不需要方法论——列出组合、逐列写用例即可。

## 静默陷阱（写错不报警，测试仍然绿）

下表是索引。遇到命中项或需要改法细节时读 `references/01-pitfalls.md`——那里有完整代码与**怎么判断自己是不是正在假绿**。

| ✗ 写法 | 为什么绿 | ✓ 改法 |
|---|---|---|
| `assertEquals(new BigDecimal("90.00"), actual)` | scale 恰好一致时全绿，实现改 scale 才红；真正该固定的小数位反而没人管 | `isEqualByComparingTo`；需要校小数位另断 `scale()` |
| 被测类内部 `new` 依赖，测试照样跑通 | mock 注入的是另一个实例，被测代码用的是自己 new 的，断言看的是假对象 | 重构为构造器注入再 mock；改不动就说明这个类不可测，先拆 |
| `when(spy.size()).thenReturn(10)` | `when()` 会先执行真实方法，副作用已经发生，再回放桩值 | 对 spy 与会抛异常的方法一律 `doReturn(10).when(spy).size()` |
| `when(mapper.selectOne(any()))` 后只断返回值 | `any()` 放过了 wrapper 构造错误（`.eq(User::getId, ...)` 字段写错也不报） | 需要校条件时用 `ArgumentCaptor` 捕获再 `verify` |
| `mockStatic` 不包 try-with-resources | 静态 mock 泄漏到同线程后续测试，失败点漂移到别的类 | `try (MockedStatic<X> m = mockStatic(X.class)) { ... }` |
| 异常断言用 `RuntimeException.class` | 任何异常都满足，被测代码抛 NPE 也算通过 | 断契约指定的具体类 + `hasMessage` |
| 无断言，调一下方法就算「覆盖」 | 全部通过，什么都没验 | 每个测试至少一条行为断言 |
| `@MockBean` / `@SpringBootTest` 用于纯单测 | 不是错，是拉全量 Context——慢、且掩盖了依赖关系 | 纯单测用 `@Mock`；只装 mock 的轻量装配用 `@TestConfiguration` + `@Bean` |

其余 Mockito 细节（`verify` 默认恰好 1 次、严格桩模式的多余 stub）会让测试**变红**，agent 当场就会改对，不必预先记。

## 与 java-integration-test 的边界

本技能 = 纯单测（`@Mock`+`@InjectMocks` 或只装 mock 的 `@TestConfiguration`，毫秒级，零外部基础设施，全周期默认）。需要真实依赖才能断言的行为（SQL 实际执行、唯一约束、事务回滚、序列化、迁移）→ java-integration-test，明示或确认后激活。

注解分界：无 Context 的 `@Mock`、只装 mock 的 `@TestConfiguration` 属本技能；`@SpringBootTest` / `@MockitoBean` / 切片注解（`@WebMvcTest` / `@JdbcTest` / `@DataJpaTest`）→ java-integration-test。

## 完成判定（DoD 锚点）

供外部 PR / checklist 直接引用，三条同时满足才算最小充分：

- [ ] 四维度各至少一个代表用例（正向 / 反向 / 边界 / 异常）。
- [ ] 被测方法的每个 `if/switch` 分支至少被一个用例走到。
- [ ] 有效 / 无效等价类清单已逐项打勾（`null`、空串、越界最易漏）。

三条全勾即判完成——不以「覆盖率 ≥ 80%」为目标（那会催生凑数测试），也不以「还没写集成测试」为由继续加。

## 版本与范围

- JUnit 5 为主，JUnit 4 项目按既有写法跟随，同一模块不混用（生命周期注解不互通）。
- 版本跟随项目既有；Spring Boot 项目测试依赖一行 `spring-boot-starter-test`，非 Spring 项目按需引 `junit-jupiter` / `mockito-core` / `assertj-core`。
- 不适用：性能测试、前端测试。
