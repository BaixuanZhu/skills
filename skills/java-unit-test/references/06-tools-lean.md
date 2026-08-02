# 06 · 工具落地（设计 → 代码的最小映射）

> 本文件只回答两个问题：**① 前面 01-05 设计好的用例，怎么映射成测试代码？② 哪些 API 坑值得固化？** 工具是为设计服务的，不是设计的目的。
>
> **API 内容的筛选标准**（决定本文件收录什么，也锁住未来扩展边界）：
> - ✅ **只固化"隐蔽型坑"（A 类）**：用错了**不报错**但埋雷——测试假绿/污染其他测试/掩盖耦合。这类"查文档也未必意识到严重性"，是技能存在的价值。
> - ❌ **不收"即时报错型"（B 类）**：用错了立刻编译失败/测试红（如注解拼错、参数顺序写反、source 注解全列表）——查官方文档 30 秒即得，固化它等于复印文档，违背"不解释冗余"原则。
>
> 判断一把尺：**这条 API 知识，是"省去查文档"，还是"省去踩一个查文档也发现不了的坑"？** 只有后者进本文件。

## §1 依赖：一句话定基线

**Spring Boot 项目**（第 0 步探测到 `spring-boot-starter-test` 或 parent）→ 什么都不用加，自带 JUnit 5 + Mockito：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
<!-- starter-test 还传递了 AssertJ / Hamcrest。断言默认用 JUnit 原生，仅在"3+字段断言/集合内容断言"时升级到 AssertJ（见 SKILL.md"断言库策略"） -->
```

**非 Spring Boot 项目** → 逐库声明（仅项目无时；按需取用，不强加）：

```xml
<dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId><version>5.10.2</version><scope>test</scope></dependency>
<dependency><groupId>org.mockito</groupId><artifactId>mockito-core</artifactId><version>5.11.0</version><scope>test</scope></dependency>
<!-- 断言默认 JUnit 原生，3+字段断言/集合内容断言时才升级 AssertJ；ArchUnit 仅 C-CHECK 触发时引入 -->
```

> 栈中立铁律：项目已有 TestNG / JUnit 4 → 跟随既有框架，不强求升 JUnit 5。断言库**默认 JUnit 原生**，仅在"3+ 字段断言 / 集合内容断言"时升级到 AssertJ（见 SKILL.md"断言库策略"）——升级标准是机械可判的，避免凭感觉漂移。下面写法以 JUnit 5（Jupiter）为主，§4 给 JUnit 4 差异。

## §2 设计用例 → 测试代码：映射表

| 用例设计形态（01-05） | 落地代码 | 关键点 |
|---|---|---|
| 正向用例（有效等价类） | `assertEquals(expected, actual)` | 一个用例一个断言焦点 |
| 反向/异常用例（无效等价类） | `assertThrows(XxxException.class, () -> ...)` | 验异常**类型 + 消息**，不止类型 |
| 同方法多输入（等价类代表/边界） | `@ParameterizedTest` + `@CsvSource`/`@MethodSource` | 用例即数据，设计意图显式化 |
| 决策表每列（03） | 一个 `@Test`，或并入 `@ParameterizedTest` | 列=用例，不要塞进单个测试 |
| 状态机合法迁移（04） | `assertEquals(终态, obj.getState())` | 通过业务方法触发，不直接 setStatus |
| 状态机非法迁移（04） | `assertThrows(IllegalStateException.class, obj::op)` | 这是状态机测试的核心 |
| 需固定外部依赖 | Mock（见 §3） | 只 mock 外部依赖，不 mock 被测对象 |

## §3 Mock 边界（最易错处）

**只 Mock 外部依赖**（DB / RPC / 时间 / 第三方服务），**绝不 Mock**：
- 被测对象自身。
- 被测类**内部 `new` 出来的对象**（这是头号陷阱，见下）。

### 标准注入式 Mock（推荐）

```java
class OrderServiceTest {
    @Mock OrderRepository repo;      // 外部依赖：mock
    @Mock PaymentClient client;      // 外部依赖：mock
    @InjectMocks OrderService service; // 被测对象：真实，依赖被注入

    @BeforeEach void setup() { MockitoAnnotations.openMocks(this); }

    @Test void should_save_when_valid() {
        when(repo.existsById(anyLong())).thenReturn(false);  // stub
        service.create(order);
        verify(repo).save(order);                             // verify
    }
}
```

### 何时改用手工构造注入

`@InjectMocks` 是默认写法（简洁、和构造器注入天然适配）。以下场景手工 `new` 构造更清晰，跟随项目既有风格即可：

- 被测类有**多个构造器**或字段/构造器注入混用 → `@InjectMocks` 注入行为难预测，手工 `new` 传 mock 更可靠。
- 需要在构造时传入**非 mock 的真实值**（如固定 `Clock`、真实 `ObjectMapper`）→ 手工构造显式可控。
- 团队既有测试统一用手工构造 → 跟随，不为"统一"而迁移。

> 同理，状态机的异常类型（`IllegalStateException` vs 自定义业务异常）也跟随项目——自定义异常对上层差异化处理更友好；默认 `IllegalStateException` 仅因其是 JDK 原生、无需额外定义。

### 头号陷阱：被测类内部 new 的对象不能 mock

```java
// ✗ 被测类自己 new 依赖
class BadService {
    public void doWork() {
        PaymentClient c = new PaymentClient();  // 内部 new，无法 mock
        c.pay();
    }
}
// 测试时无法干预 c → 测了等于没测，或要用 PowerMock 反射强插（坏味道）

// ✓ 重构为构造器注入，再 mock
class GoodService {
    private final PaymentClient client;          // 注入
    public GoodService(PaymentClient client) { this.client = client; }
}
```

> 当你发现"想 mock 但 mock 不了" → 这是**设计信号**：被测类耦合过重，应重构注入而非用反射强 mock。

### 静态方法 mock（最后手段）

```java
@Test void should_useMockedId() {
    try (MockedStatic<IdUtil> m = mockStatic(IdUtil.class)) {   // 必须 try-with-resources
        m.when(IdUtil::getId).thenReturn("FAKE_ID");
        assertEquals("FAKE_ID", service.genOrderId());
    }  // 离开块自动释放，不污染其他测试
}
```

- `mockStatic` 需 Mockito 3.4+（第 0 步探测版本）。
- **必须**包在 `try-with-resources`，否则静态 mock 泄漏到同线程其他测试。
- 优先重构为可注入实例方法；确需静态 mock 才用。

### Mockito stubbing / verify 隐蔽坑（用错不报错但埋雷）

以下三个坑都"查文档未必意识到严重性、用错了测试照样过"，是技能固化的价值点：

**① 对 `spy` 用 `when().thenReturn()` 会先触发真实方法**

```java
List<Object> real = spy(new ArrayList<>());

// ✗ 对 spy 用 when()：会先调用 real.size() 真实方法，若真实方法有副作用/NPE 就已经发生
when(real.size()).thenReturn(10);

// ✓ 对 spy 一律用 doReturn().when()：跳过真实方法直接返回桩值
doReturn(10).when(real).size();
```

规则：**stubbing `spy` 或会抛异常的方法，必须用 `doReturn/doThrow().when(obj)`**（"do 先行"），不能用 `when(obj).thenReturn()`。后者是先执行真实调用再回放，对 spy 会产生副作用。

**② `verify` 不传 times 默认 = 1，且是"恰好"不是"至少"**

```java
verify(repo).save(order);         // 等价于 verify(repo, times(1))，必须恰好 1 次
verify(repo, never()).save(any()); // 0 次
verify(repo, atLeast(2)).save(any()); // ≥2 次（注意 atLeast vs times 的语义差）
// 误以为"不写 times = 至少 1 次" → 实际被调 2 次时这个 verify 会失败
```

**③ 严格桩模式（`@MockitoSettings`/MockitoExtension）下多余 stub 抛异常**

```java
@ExtendWith(MockitoExtension.class)   // 严格模式
class XTest {
    @Mock Repo repo;
    @Test void t() {
        when(repo.findById(1L)).thenReturn(o);  // 若被测代码没调 findById(1L) → UnnecessaryStubbingException
    }
}
```

这是好事（逼桩值有用），但**调试式补的 stub 忘删**会让测试红。排查：确认桩值是否真被消费；确需"可能不用"的桩用 `lenient().when(...)` 显式标注（仅在必要时，别滥用）。

### `@MockBean` vs `@Mock`（关键区分）

| | `@Mock` | `@MockBean` |
|---|---|---|
| 范围 | 纯单元测试 | Spring 切片/集成测试 |
| 开销 | 毫秒，不起容器 | **启动/重建 Spring Context** |
| 用于 | 本技能的主战场 | `@WebMvcTest`/`@DataJpaTest` 等 |

> **纯单元测试禁用 `@MockBean`**——它会拉起 Spring 容器，让"单元测试"变成慢速集成测试。纯单测一律 `@Mock` + `@InjectMocks`。

## §4 JUnit 4 项目的写法差异（跟随既有）

探测到 JUnit 4（`junit:junit` / `@RunWith`）时，跟随既有，不强升。差异：

| 概念 | JUnit 5（默认） | JUnit 4（跟随） |
|---|---|---|
| 测试注解 | `@Test`（org.junit.jupiter） | `@Test`（org.junit，**勿混用**） |
| 前置 | `@BeforeEach` | `@Before` |
| 断言 | `Assertions.assertEquals` | `Assert.assertEquals` |
| 异常断言 | `assertThrows(...)` | `@Test(expected=...)` 或 `try/catch fail()` |
| 参数化 | `@ParameterizedTest` | `@RunWith(Parameterized.class)` |
| Mockito 注解 | `MockitoAnnotations.openMocks` | `@RunWith(MockitoJUnitRunner.class)` |

> 同一模块**禁止 JUnit 4 与 5 混用**——生命周期注解不互通，会导致测试不执行或乱序。

## §5 覆盖率工具（仅项目无且用户问时）

JaCoCo 接入见 `references/05-coverage-and-quantity.md`。**不要主动推覆盖率接入**——只在用户问"测够没/覆盖率"时提，且强调它是反向诊断而非合格证。

## §6 不做的事

- **断言库按阈值用**：默认 JUnit 原生 `Assertions`；仅在"3+ 字段断言 / 集合内容断言"时升级 AssertJ（见 SKILL.md"断言库策略"）。AssertJ 的流式语法只在这两个场景出现，不为简单断言引入。
- **不教集成测试/`@SpringBootTest`**——超出本技能范围（见 SKILL.md 不适用项）。
- **不教 TestNG**——跟随既有；无则不主动推荐引入。
- **不解释"为什么不用 XXX"**——不纳入的工具不解释原因（仓库原则）。

> 本文件存在的唯一意义：让 01-05 设计的用例能落地成可跑的代码。设计是主角，工具是配角。
