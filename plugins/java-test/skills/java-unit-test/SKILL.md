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
version: "2.5.0"
last_verified: "2026-10-24"
---

# Java 开发期测试

开发期测试 = **纯单元测试**：被测对象是真实对象，外部依赖用 mock，毫秒级，`mvn test` / `gradle test` 秒级跑完——零外部基础设施（不连真实 DB / 容器 / 中间件）。默认 `@Mock`+`@InjectMocks`；项目既有 `@TestConfiguration` 手写 `@Bean` mock + `@Import` 的轻量装配惯例时跟随，但上下文里只允许 mock 与纯内存对象。

> 接口级验证（"接口通不通"）不写测试、不属本技能范围；需要真实依赖断言 / 可重复回归的集成测试 → java-integration-test，明示或确认后激活。

## 唯一判据：把被测代码改坏，这条测试会红吗

答不出会红在哪一行，这条测试就是装饰品。写测试代码不难，难的是知道自己写的测试**在什么情况下是假的**。三个检查点覆盖全部已知假绿来源，命中任一条读 `references/01-pitfalls.md`。

### 一、mock 注入的，是被测代码真正用的那个实例吗

| 断在哪 | 表现 |
|---|---|
| 被测类内部 `new` 依赖 | mock 注入的是另一个实例，被测代码安静地用自己的，断言对着假对象跑，全程无报错。判别：桩值没生效 / `verify` 从不命中 / 断言全过 → 先查 `new` |
| 对 `spy` 用 `when()` 打桩 | `when()` 先执行真实方法，副作用已经发生，再回放桩值。真实方法有副作用时，失败点漂移到毫不相干的断言上 |
| `mockStatic` 不包 `try-with-resources` | 静态 mock 泄漏到同线程后续测试，失败点漂移到别的类 |

`LocalDate.now()` / `UUID.randomUUID()` / `new ObjectMapper()` 这类调用点在**你自己代码里**就不算够不着——注入 `Clock.fixed(...)` 或 `IdGenerator` 接口，不要上 `mockStatic`。

### 二、断言比的，是你真正要保证的东西吗

| 断在哪 | 表现 |
|---|---|
| 金额用 `assertEquals(BigDecimal, BigDecimal)` | `equals` 连 scale 一起比。scale 恰好一致时全绿，把「金额固定两位小数」这个要求掩盖了；真正该固定的小数位反而没人管 |
| 异常断在 `RuntimeException` / `Exception` 根父类 | 任何异常都满足，被测代码抛 NPE 也算通过。断契约指定的具体类 + `hasMessage` |
| `any()` 放过参数构造 | 被测代码构造的 wrapper 字段写错也不报。需要校条件时用 `ArgumentCaptor` 捕获再 `verify` |
| 只断返回值，没断协作者副作用 | 把扣库存 / 发消息的调用整行删掉，返回值断言照样过。副作用必须 `verify` 捕获调用（参数用 `ArgumentCaptor`），或用假对象状态断言——只 stub 不 verify 的副作用等于没测 |

### 三、这条断言有任何可能失败吗

| 断在哪 | 表现 |
|---|---|
| 无断言，调一下方法不抛异常就算覆盖 | 全部通过，什么都没验。只验「不抛异常」时显式写 `assertThatCode(...).doesNotThrowAnyException()`，让意图可见 |
| 桩返回恒等于期望值 | 任何实现都能过 |

## 断言库（项目取值）

**默认 AssertJ**（`spring-boot-starter-test` 已传递，非 Spring 项目按需引 `assertj-core`）：

| 场景 | 写法 |
|---|---|
| 金额、小数 | `isEqualByComparingTo("90.00")`；要校小数位另断 `scale()` |
| 抛异常 | `assertThatThrownBy(() -> ...).isInstanceOf(X.class).hasMessage("...")` |
| 集合内容 | `containsExactlyInAnyOrder(...)` / `extracting(Foo::getId)` |
| 简单值 | `isEqualTo(...)` |

项目已有测试统一用 JUnit 原生 `Assertions` 时跟随，但金额仍要 `compareTo(actual, expected) == 0`，不用 `assertEquals`。

## 覆盖到什么程度算够

**设计先于编码**：先列出用例清单（等价类代表、边界点、决策表列、状态迁移），再落 `@Test`；上来就写、想到哪测到哪，得到的是覆盖率幻觉，不是测试设计。

被测方法四维度各至少一条：**正向**（合法输入，有效等价类代表）/ **反向**（非法输入被拒绝，无效等价类代表）/ **边界**（端点、空、`null`、极值，边界值分析高发区）/ **异常**（契约指定的异常类）。缺一维即设计漏洞。多条件逻辑画决策表，**列数即用例数**——只对存在业务组合规则的逻辑画表；条件相互独立、无组合效应时各取等价类代表值，不展开全排列，组合规模大时用 pairwise 压缩。有状态对象按迁移列表走，合法与非法都要覆盖。

**最小充分集**：一个方法的用例通常 3~8 条——等价类合并代表无穷输入，边界值钉住 off-by-one。超出先自问是不是在凑同质变体（那是冗余，不是覆盖）。

**代表值复核**：同区间换一个代表值，期望行为应不变；变了就是等价类划错。每条代表用例至少触发一条与相邻等价类不同的分支——没区分就不是代表。

**确定性**：时间与随机源注入（`Clock.fixed(...)`、固定种子、`IdGenerator`），禁 `Thread.sleep` 等待，不依赖执行顺序与共享状态。flaky 的绿和假绿一样不可信。

- [ ] 用例清单先于测试代码存在
- [ ] 四维度各至少一个代表用例，每个 `if/switch` 分支至少被一个用例走到
- [ ] 有效 / 无效等价类清单逐项打勾（`null`、空串、越界最易漏）
- [ ] 代表值复核通过，用例数在最小充分集内
- [ ] 测试可重复：固定 Clock/种子，无 `Thread.sleep`，不靠执行顺序与共享状态

五条全勾只说明用例设计完成——不以「覆盖率 ≥ 80%」为目标（那会催生凑数测试），也不以「还没写集成测试」为由继续加。

## 交付前验证

1. 实际跑 `mvn test` / `./gradlew test`（或项目既有单测任务），从输出或报告确认本次用例被执行；`BUILD SUCCESS` 本身不是执行证据。无法运行时必须写明哪项没跑及原因。
2. 至少选一条本次核心断言做反证：临时改坏对应实现，目标用例必须变红；恢复实现后重跑为绿。项目已配变异测试门禁时，同时以其结果为准。

## 与 java-integration-test 的边界

本技能 = 纯单测（`@Mock`+`@InjectMocks` 或只装 mock 的 `@TestConfiguration`，毫秒级，零外部基础设施，全周期默认）。需要真实依赖才能断言的行为（SQL 实际执行、唯一约束、事务回滚、序列化、迁移）→ java-integration-test，明示或确认后激活。

注解分界：无 Context 的 `@Mock`、只装 mock 的 `@TestConfiguration` 属本技能；`@SpringBootTest` / `@MockitoBean` / 切片注解（`@WebMvcTest` / `@JdbcTest` / `@DataJpaTest`）→ java-integration-test。

`@TestConfiguration` + `@Import` + `@Autowired` 起的仍是 Spring 上下文（不是全量，但也不是无）。允许，条件是上下文里**只有 mock 与纯内存对象**——不出现真实 `DataSource`、中间件客户端，不拉 `@SpringBootApplication` 扫描。出现这些就跨到集成测试。

## 版本与范围

- JUnit 5 为主，JUnit 4 项目按既有写法跟随，同一模块不混用（生命周期注解不互通）。
- 版本跟随项目既有；Spring Boot 项目测试依赖一行 `spring-boot-starter-test`，非 Spring 项目按需引 `junit-jupiter` / `mockito-core` / `assertj-core`。
- 不适用：性能测试、前端测试。
