# 01 · 静默陷阱（写错不报警，测试仍然绿）

收录标准：**写错后测试是绿的**。会让测试变红的（类名没加 `*IT` 导致混进 `mvn test`、`@WebMvcTest` 漏 mock 导致启动失败、Boot 4 注解编译不过）不收录——这些当场暴露，按报错改即可。

## 一、测试级 `@Transactional` 让回滚断言假绿

```java
// ✗ 想验证「写订单失败时库存回滚」，却在测试方法上加了 @Transactional
@SpringBootTest
@Transactional                                  // 这个事务把 Service 的 REQUIRED 事务并了进来
class OrderRollbackTest {
    @Test
    void should_rollback_stock_when_insert_fails() {
        assertThatThrownBy(() -> orderService.createOrder(badRequest)).isInstanceOf(...);
        assertThat(stockRepository.quantityOf(skuId)).isEqualTo(10);   // 永远通过
    }
}
```

**为什么绿**：Service 上的 `@Transactional` 默认 `REQUIRED`，遇到测试已开的事务就加入，不再新开。异常把整个事务标成 rollback-only，但**回滚发生在测试方法结束时**——断言执行时，扣减对同一连接仍然可见。所以「库存恢复了」这个断言在任何情况下都通过，包括 `OrderService` 上根本没有 `@Transactional` 的时候。

```java
// ✓ 让 Service 自己开事务、自己提交或回滚，测试只读最终状态
@SpringBootTest          // 数据源由决策 ③ 选定：容器 / 本地实库，不用 H2 顶替
class OrderRollbackTest {
    @AfterEach
    void cleanUp() { jdbcTemplate.update("DELETE FROM t_order"); jdbcTemplate.update("DELETE FROM t_stock"); }

    @Test
    void should_rollback_stock_when_insert_fails() {
        assertThatThrownBy(() -> orderService.createOrder(badRequest)).isInstanceOf(...);
        assertThat(stockRepository.quantityOf(skuId)).isEqualTo(10);   // 现在这条真的会红
    }
}
```

**验证方法**：临时删掉 `OrderService` 上的 `@Transactional`，这条用例必须变红。不红就是假绿。

## 二、`RANDOM_PORT` 下测试事务完全不生效

```java
// ✗ 以为隔离了
@SpringBootTest(webEnvironment = RANDOM_PORT)
@Transactional
class OrderApiTest { ... }
```

HTTP 请求由容器线程处理，与测试线程不是同一个事务、也不是同一个连接——测试事务回滚不了请求写进去的数据。**这一种连"假绿"都算不上，是隔离完全失效**：脏数据留在库里，下一个测试或下一次运行撞唯一约束。

`RANDOM_PORT` / `DEFINED_PORT` 场景一律显式清理：`@Sql(executionPhase = AFTER_TEST_METHOD)`、精确 `DELETE`，或每个测试类用独立库名。

## 三、`@DataJpaTest` / `@JdbcTest` 默认把数据源换成内嵌库

```java
// ✗ 以为在测生产同款 SQL
@DataJpaTest
class OrderRepositoryTest { ... }        // 自动 replace 成 H2
```

`@DataJpaTest` 默认 `@AutoConfigureTestDatabase(replace = ANY)`，把项目配置的真实 `DataSource` 换成内嵌 H2。`jsonb`、`ARRAY`、`ON CONFLICT`、序列、排序大小写敏感性——H2 要么不支持，要么行为不同，测试全绿，上线才炸。

```java
// ✓ 同款容器
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)
@Testcontainers
class OrderRepositoryTest {
    @Container
    static PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", pg::getJdbcUrl);
        registry.add("spring.datasource.username", pg::getUsername);
        registry.add("spring.datasource.password", pg::getPassword);
    }
}
```

Boot 3.1+ 用 `@ServiceConnection` 可省掉 `@DynamicPropertySource`。镜像 tag 对齐生产——生产是 `postgres:16.3` 就写 16.3，不要凭印象写 `latest`。

## 四、容器的生命周期与复用

```java
// ✗ 每个测试方法启停一次：单条十秒级，整个套件跑半小时
@Container
PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:16-alpine");

// ✓ static：容器全类共享，类结束才停
@Container
static PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:16-alpine");
```

`withReuse(true)` 能跨类复用，但**复用意味着上一轮的脏数据还在**——单跑一个测试通过，全量跑失败，且失败点与本次改动无关。用复用就必须自己保证每个用例的清理。

## 五、`RestAssuredMockMvc` 不是真实 HTTP

`RestAssuredMockMvc` 走进程内 MockMvc。断言全绿，但过滤器、拦截器、消息转换器、错误处理、线程模型都没真正经过。要验证「HTTP 这条管道通不通」，用 `RANDOM_PORT` + 真实客户端（`TestRestTemplate` / `RestTestClient` / `RestAssured`）。

## 六、启动日志的 WARN / ERROR

Bean 创建失败被条件装配跳过、Flyway 迁移部分失败、连接池初始化降级——这些常常只打日志不抛异常，测试照绿。交付前读一遍启动日志，报错即失败信号。

## 七、WireMock 固定端口

```java
// ✗ 并行跑测试时端口冲突，或撞上本机已占用的端口
WireMockServer server = new WireMockServer(8089);

// ✓ 动态端口 + 注入
WireMockServer server = new WireMockServer(options().dynamicPort());
@DynamicPropertySource
static void props(DynamicPropertyRegistry registry) {
    registry.add("payment.base-url", () -> "http://localhost:" + server.port());
}
```

## 八、降级到本地实库时连错了库

无 Docker 时走「本地实库 + 独立 schema」。这条路径最大的风险不是不可重复，是**读到的配置不是你写的那份**——测试连上了开发库甚至生产库，还顺手把数据清了。

```java
// ✗ 只在注解里写 url，被 application.yml / 环境变量覆盖
@SpringBootTest(properties = "spring.datasource.url=jdbc:mysql://localhost:3306/app")
class OrderIT { ... }        // 项目里 application-prod.yml 用了 ${DB_URL}，实际连的是哪台不确定
```

```java
// ✓ 测试专属 profile + 显式库名 + 启动时自检
@SpringBootTest
@ActiveProfiles("ittest")    // src/test/resources/application-ittest.yml 里写死测试库
class OrderIT {

    @BeforeAll
    static void assertNotProduction(@Autowired DataSource ds) throws Exception {
        try (Connection c = ds.getConnection()) {
            String url = c.getMetaData().getURL();
            assertThat(url).as("测试连到了预期之外的库").contains("/app_ittest");
        }
    }
}
```

三条必须同时满足，缺一条就会连错：

1. **测试专属 profile**，不在 `application.yml` 上改——那份文件开发时也在用。
2. **库名带 `_ittest` 后缀**，且该库的账号没有权限碰其它库。只靠命名约定不够，权限才是硬边界。
3. **启动时断言 `getMetaData().getURL()`**。配置文件写对了、环境变量覆盖了，只有连上之后才知道。

清理数据同理：`DELETE` 语句只能跑在确认过 URL 的连接上，否则一次配置漂移就是一次误删。

## 九、单条十秒级是从哪来的

集成测试慢不是因为容器慢，是因为每次重建了不该重建的东西。按代价排序：

| 来源 | 代价 | 处理 |
|---|---|---|
| 容器不是 `static` | 每个测试方法启停一次 | 改 `static`（见第四节） |
| 起了用不到的容器 | 每多一个容器多 3~5 秒 | 删掉它，测试还绿就是多余的 |
| Context 缓存失效 | 整个上下文重建 | 统一 `@MockitoBean` 组合，别每组换配置 |
| 首跑拉镜像 | CI 上几十秒到几分钟 | 流水线预拉，或镜像缓存层 |
| 连接数打满 | 卡住而非变慢，报 `too many connections` | 见下 |

**起了用不到的容器**的判据只有一条：把这个 `@Container` 注掉，测试还绿吗？绿就是这个容器没在验证任何东西。

**连接数**这一条实测最费时间排查：PostgreSQL 容器默认 `max_connections=100`，Hikari 默认池大小 10，10 个测试类并行就是 100——刚好打满，表现为随机卡住或偶发失败，且和本次改动无关。

```java
// ✓ 池大小对齐容器上限，别各按默认值走
@DynamicPropertySource
static void props(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.hikari.maximum-pool-size", () -> "2");
}
```

并行跑时上限算的是「并行测试类数 × 池大小」，不是单个类的池大小。
