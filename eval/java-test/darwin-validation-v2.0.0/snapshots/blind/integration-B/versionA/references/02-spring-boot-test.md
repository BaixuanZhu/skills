# 02 · Spring Boot Test 核心

> `@SpringBootTest` 的 `webEnvironment` 选型、测试客户端版本事实、`@MockitoBean` 用法与 Context 缓存——只留选型判据与陷阱，写法 agent 均熟。

## webEnvironment 决策表

| 模式 | HTTP？ | MockMvc？ | `@Transactional` 回滚？ | 适用场景 |
|---|---|---|---|---|
| `MOCK`（默认） | 否（Mock Servlet） | ✓ 自动配置 | ✓ 有效 | 跨层真实协作 / 事务传播验证（触 DB 配 Testcontainers）；不需要真实 HTTP 的集成测试 |
| `RANDOM_PORT` | ✓ 真实（随机端口） | ✗ | **✗ 失效** | 完整 HTTP API 测试（含过滤器 / 序列化）；REST Assured / WebTestClient |
| `DEFINED_PORT` | ✓ 真实（固定端口） | ✗ | **✗ 失效** | 需要固定端口（外部工具对接）——一般不用，端口冲突风险 |
| `NONE` | 否 | ✗ | ✓ 有效 | 只启动 Context，不做 Web 测试（批处理 / 定时任务） |

> **`@Transactional` 在 `RANDOM_PORT` 下失效**：HTTP 请求走 Servlet 容器线程，与测试线程不在同一事务——最隐蔽的隔离坑，替代方案见 `references/06`。

## 测试客户端选择（版本事实）

| 工具 | 模式 | 适合 | 真实 HTTP？ |
|---|---|---|---|
| **MockMvc** | MOCK | Spring MVC（Servlet）测试，最轻量 | 否（进程内 Mock Servlet） |
| **WebTestClient** | RANDOM_PORT | Servlet + Reactive 通用，流式断言 | ✓ |
| **RestTestClient**（Boot 4+） | MOCK / RANDOM_PORT | Servlet 统一客户端：MOCK 底层走 MockMvc、RANDOM_PORT 直打真实服务器 | 按 webEnvironment |
| **TestRestTemplate**（≤3.x） | RANDOM_PORT | Servlet 简单场景；Boot 4 起废弃（遗留项目才见） | ✓ |

**选择规则**：
- `MOCK` 模式 → MockMvc（最轻量，秒级）。
- `RANDOM_PORT`：Boot 4+ Servlet 栈 → RestTestClient；WebFlux → WebTestClient；复杂多步 given/when/then 断言 → REST Assured（见 `05`）。
- TestRestTemplate 仅限 Boot ≤3.x 遗留项目。

**Boot 4 两个必知**：① `@SpringBootTest` 不再自动配置 MockMvc——**必须显式 `@AutoConfigureMockMvc`**（≤3.x 省略也能注入是旧行为）；② HTTP 测试客户端同样不再自动配置（`@AutoConfigureRestTestClient` / `@AutoConfigureWebTestClient` 显式开启）。

### TestRestTemplate → RestTestClient 迁移（Boot 4）

Boot 4 起 `TestRestTemplate` 废弃：拆到独立模块，升级后原 `@Autowired TestRestTemplate` **直接注入失败**。新测试用 `RestTestClient`：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-resttestclient</artifactId>
    <scope>test</scope>
</dependency>
```

- 注入：`@Autowired RestTestClient` + 类上 `@AutoConfigureRestTestClient`；API 风格与 WebTestClient 一致（流式 `exchange().expectStatus().expectBody()`；拿对象用 `.expectBody(T.class).returnResult().getResponseBody()`）。
- 暂留 TestRestTemplate 的代价：类移到 `org.springframework.boot.resttestclient.TestRestTemplate`（原 import 失效）+ 需 `@AutoConfigureTestRestTemplate` + runtime 依赖 `spring-boot-restclient`——改动不比迁移少，不推荐。
- WebFlux 栈不用它——仍用 WebTestClient。

## @MockitoBean vs @Mock（关键区分）

| | `@Mock` | `@MockitoBean` |
|---|---|---|
| 来源 | Mockito 原生 | Spring Framework 6.2+（`org.springframework.test.context.bean.override.mockito`） |
| 范围 | 纯单元测试（→ java-unit-test） | 切片 / 集成测试（本技能） |
| 作用 | 替换被测对象的依赖字段 | 替换 Spring Context 中的 Bean 定义 |
| 开销 | 毫秒 | 启动 / 重建 Spring Context（秒级） |

```java
@SpringBootTest
class OrderIntegrationTest {
    @MockitoBean PaymentClient paymentClient;  // 替换 Context 中的 Bean
    @Autowired OrderService orderService;      // 真实 Bean，PaymentClient 被 mock
}
```

> **版本口径**：Boot 3.4+ 用 `@MockitoBean` / `@MockitoSpyBean`；旧的 `@MockBean` / `@SpyBean` 是 ≤3.3 写法（3.4 废弃，**4.0 已移除——编译错误**）。关键差异：**`@MockitoBean` 不能声明在 `@Configuration` / `@TestConfiguration` 类里**（旧 `@MockBean` 可以）——跨测试类共享 mock 改为测试类上重复标注 `@MockitoBean(types = {...})` 或自定义组合注解。
>
> **`@MockitoSpyBean`**：对真实 Bean 创建 spy——真实方法照常执行，可 `verify` 调用 / `doReturn` 桩特定方法（对 spy 桩必须 `doReturn().when()`，不能用 `when().thenReturn()`——陷阱详见 java-unit-test 工具篇）。

## @TestConfiguration（一行判据）

测试专用 Bean（固定 `Clock` / mock 外部客户端 / 测试数据初始化）放 `@TestConfiguration` 类 + `@Import` 导入——它**不被 `@ComponentScan` 扫描**，须显式导入；同类型覆盖生产 Bean 加 `@Primary`。

## Context 缓存机制

Spring Test 缓存 ApplicationContext——**相同配置的测试类共享一个 Context**，缓存命中 = 零启动开销。**破坏缓存（每次十秒重建）**：不同的 `@MockitoBean` / `@MockitoSpyBean` 组合、不同的 `@SpringBootTest` 属性（`properties` / `webEnvironment`）、不同的 `@ActiveProfiles`、`@DirtiesContext`。

**优化**：统一所有测试类的 mock 配置与 profile——抽 Base 类共享一个 Context：

```java
@SpringBootTest
abstract class BaseIntegrationTest {
    @MockitoBean Repo repo;
    @MockitoBean Service service;
}
class TestA extends BaseIntegrationTest { }   // 共享 1 个 Context
```

## @DirtiesContext：核弹级重置

`@DirtiesContext` 每次触发**重建整个 Context**（十秒级）。仅用于 Bean 内部状态被测试修改且无法用 `@Sql` / `@Transactional` / Testcontainers 重置的场景（典型：测试改了 `@ConfigurationProperties` 绑定的单例 Bean 内部状态）。`classMode` 中 `AFTER_CLASS`（1 次重建）可接受，`*_EACH_TEST_METHOD`（×N 重建）基本不该用。
