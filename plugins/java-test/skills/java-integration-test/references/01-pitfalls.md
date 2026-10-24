# 01 · 静默陷阱

收录标准：**写错后测试是绿的**。会让测试变红的（类名没加 `*IT` 导致混进 `mvn test`、`@WebMvcTest` 漏 mock 导致启动失败、Boot 4 注解编译不过）不收录——当场暴露，按报错改即可。

按假绿机制分组，不按 API 分类。分组的意义在于：本模块一条都没命中时，仍然要过一遍三个机制问题；平铺清单只会让人逐条勾完就收工。

## 机制一 · 测的不是生产那条路径

### 测试级 `@Transactional` 让回滚断言恒真

想验证「写订单失败时库存回滚」，却在测试类上加了 `@Transactional`。

Service 上的 `@Transactional` 默认 `REQUIRED`，遇到测试已开的事务就加入，不再新开。异常把整个事务标成 rollback-only，但**回滚发生在测试方法结束时**——断言执行时，扣减对同一连接仍然可见。所以「库存恢复了」在任何情况下都通过，包括 `OrderService` 上根本没有 `@Transactional` 的时候。

改法：测试不加 `@Transactional`，让 Service 自己提交或回滚，测试只读最终状态，用 `@AfterEach` 或独立库名清理。

**验证方法**：临时删掉被测 Service 上的 `@Transactional`，这条用例必须变红。不红就是假绿。

### `@DataJpaTest` / `@JdbcTest` 默认换掉数据源

默认 `@AutoConfigureTestDatabase(replace = ANY)`，把项目配置的真实 `DataSource` 静默换成内嵌库。`jsonb`、`ARRAY`、`ON CONFLICT`、序列、排序大小写敏感性——要么不支持，要么行为不同，测试全绿，上线才炸。

改法：`replace = NONE` + 决策 ③ 选定的依赖。Boot 3.1+ 用 `@ServiceConnection` 省掉手工注入连接信息。

### `RestAssuredMockMvc` 不是真实 HTTP

走进程内 MockMvc。断言全绿，但过滤器、拦截器、消息转换器、错误处理、线程模型都没经过。要验证「HTTP 这条管道通不通」，用 `RANDOM_PORT` + 真实客户端（`TestRestTemplate` / `RestTestClient` / `RestAssured`）。

### `any()` 放过参数构造

被测代码构造的 wrapper 是它的**参数**，不是外部依赖——不要去 mock wrapper 本身（重建不出同一实例）。但 `any()` 会让「查询条件写错字段」这类 bug 静默通过。需要校条件时用 `ArgumentCaptor` 捕获再 `verify`。

### 外部 API 真调

支付、短信、三方认证真调：测试依赖对方可用性、产生费用、结果不可重复。WireMock stub，**端口必须动态**——固定端口并行跑会撞车，也会撞上本机已占用的端口。端口经 `@DynamicPropertySource` 注入配置。

## 机制二 · 验的时间点不对

### `RANDOM_PORT` 下测试事务完全不生效

HTTP 请求由容器线程处理，与测试线程不是同一个事务、也不是同一个连接——测试事务回滚不了请求写进去的数据。**这一种连"假绿"都算不上，是隔离完全失效**：脏数据留在库里，下一个测试或下一次运行撞唯一约束。

改法：`RANDOM_PORT` / `DEFINED_PORT` 场景一律显式清理——`@Sql(executionPhase = AFTER_TEST_METHOD)`、精确 `DELETE`，或每个测试类独立库名。

## 机制三 · 失败没被算成失败

### 启动日志的 WARN / ERROR

Bean 创建失败被条件装配跳过、Flyway 迁移部分失败、连接池初始化降级——这些常常只打日志不抛异常，测试照绿。交付前读一遍启动日志，报错即失败信号。

### 能验和不能验的边界要说出来

用同族嵌入式替身时，**不说出来就是骗自己**。事务与约束语义可以验，方言断言必须移交真库，并在回复里写明「非生产方言，以下行为未验」。空手说"不写"和"拿替身冒充真库"一样不合格。

## 附带 · 慢到被放弃

不是假绿，是让人不想跑。四处最贵：容器不是 `static`（每个方法启停一次）、起了用不到的容器（注掉它还绿就是多余的）、Context 缓存失效（统一 `@MockitoBean` 组合、少用 `@DirtiesContext`）、首跑拉镜像（CI 预拉）。

连接数最费排查：`max_connections` 默认值随库不同（PostgreSQL 100、MySQL 151），Hikari 池默认 10。并行跑的上限是「并行类数 × 池大小」，打满表现为随机卡住且与本次改动无关。调 `spring.datasource.hikari.maximum-pool-size` 对齐。

`withReuse(true)` 跨类复用会留着上一轮的脏数据——单跑通过、全量失败，失败点与本次改动无关。用复用就必须自己保证每个用例的清理。

## 附 · 降级到本地实库时连错了库

无 Docker 时走「本地实库 + 独立 schema」。这条路径最大的风险不是不可重复，是**读到的配置不是你写的那份**——测试连上了开发库甚至生产库，还顺手把数据清了。

只在注解里写 `properties = "spring.datasource.url=..."` 不够：会被 `application-prod.yml` 里的 `${DB_URL}` 或环境变量覆盖，实际连哪台不确定。

三条必须同时满足：

1. **测试专属 profile**，不在 `application.yml` 上改——那份开发时也在用。
2. **库名带 `_ittest` 后缀**，且该库账号没有权限碰其它库。只靠命名约定不够，权限才是硬边界。
3. **启动时断言 `getMetaData().getURL()`**。配置文件写对了、环境变量覆盖了，只有连上之后才知道。

清理数据同理：`DELETE` 只能跑在确认过 URL 的连接上，否则一次配置漂移就是一次误删。
