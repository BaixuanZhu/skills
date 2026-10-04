# Test Prompts（v2.0.0 达尔文验证）

> 回归集 R1-R10（两版都应答好的场景——验证精简后不退步）；对抗集 A1-A6（本轮重构的行为目标——验证新口径真起作用）。
> unit 侧评 R1-R5 + A1 + A2（拿 java-unit-test 两版）；integration 侧评 R6-R10 + A3-A6（拿 java-integration-test 两版）。

## java-unit-test 部分

### R1（回归 · 等价类 + 边界值设计）

> 我写了个方法 `BigDecimal calcPrice(int qty, boolean vip, String couponCode)`：qty 合法范围 1~99（越界抛 IllegalArgumentException）；vip 为 true 打 8 折；couponCode 为 null 或空串表示无券，有值时查券表。帮我设计测试用例——要几个？分别是哪些？我不想写太多没用的。

### R2（回归 · 决策表）

> 优惠规则：是否能叠加使用"满减 + 折扣券"取决于三个条件——是否新用户（newUser）、订单金额是否超 100（over100）、折扣券是否可叠加（stackable）。这种逻辑测试怎么设计才不漏不重？8 种组合都要测吗？

### R3（回归 · 状态机）

> 退款单状态机：PENDING_REVIEW → APPROVED → REFUNDING → SUCCESS / FAILED，任意非终态可 CANCELLED。要写哪些测试？重点在哪？

### R4（回归 · Mockito 陷阱）

> 三个 Mockito 问题：① 对 spy 对象 stub 时真实方法好像被执行了一次，怎么回的事？② `verify(repo).save(order)` 被测代码调了两次 save 时这个 verify 为什么红？③ Mockito 4.x 项目要用 mockStatic，pom 里除了 mockito-core 还要加什么？

### R5（回归 · 覆盖率立场 + JaCoCo 接入）

> 组长要求行覆盖率 ≥ 80% 并挂 CI 门禁，我现在 62%。这个要求合理吗？另外项目还没接 JaCoCo，帮我接一下。

### A1（对抗 · 为跑单测引入 H2 / 内嵌库）

> 新写了 InventoryService，依赖 InventoryRepository（JPA）和 RedisTemplate（缓存扣减）。写单测时全 mock 觉得心里没底，测不出真的存取。我想给单测配个 H2 和 embedded-redis，让单测跑真的数据库和 Redis——依赖怎么加？配置怎么写？

### A2（对抗 · 开发期接口验证路由）

> 开发期刚写完 OrderController 的 POST /orders 接口，想验证一下接口通不通、参数校验对不对。我该写个 @SpringBootTest(RANDOM_PORT) 测试真实调一下本地接口吗？

## java-integration-test 部分

### R6（回归 · @WebMvcTest 切片）

> `@WebMvcTest(OrderController.class)` 启动直接报 `NoSuchBeanDefinitionException: OrderService`——不是说切片测试很轻吗，怎么还报错？另外项目里有 Spring Security，切片测试要不要特殊处理？

### R7（回归 · @Transactional 失效与清理）

> `@SpringBootTest(webEnvironment = RANDOM_PORT)` + `@Transactional` 的测试，跑完数据没回滚，表里留了脏数据。为什么 MOCK 模式下好好的？这个场景怎么清理数据？被测方法里还有个 @Async 的后续动作，回滚方案要注意什么？

### R8（回归 · Testcontainers 依赖与静态容器）

> 要给 JPA 测试引入 Testcontainers 起真实 PostgreSQL。① 依赖怎么选、镜像版本怎么定？② 我的容器现在每个测试方法都重启一次，一轮下来好几分钟——哪里错了？

### R9（回归 · Boot 4 迁移）

> 项目从 Boot 3.3 升到 4.0，测试代码一堆报错：TestRestTemplate 注入失败、@MockBean 编译错误、Testcontainers 依赖 404。分别怎么改？

### R10（回归 · WireMock + 异步等待）

> 集成测试里要调第三方支付 API，不能真调。另外有个测试等 Kafka 消费者处理完再断言，现在用 Thread.sleep(3000)，不稳定还慢。这两个怎么处理？

### A3（对抗 · 无信号不写重型测试）

> （用户贴出刚写完的代码）这是我新写的 OrderService.createOrder()，里面调了 OrderRepository 存订单、PaymentClient 走支付。帮我补测试。

### A4（对抗 · 容器准入 + 数量锚点）

> 需求冻结了，准备发版，帮我补集成测试。被测的 PricingService：① 折扣规则有 20 种条件组合（新客/满额/品类/券叠加…），之前只测过五六种；② 还有一条用了 PostgreSQL jsonb 列的自定义 SQL 查询没测过。

### A5（对抗 · 命名分离）

> 团队抱怨：自从加了 Testcontainers 集成测试，`mvn test` 一跑十几分钟（拉容器 + 全量上下文），开发过程中改一行代码跑一次测试完全等不起。怎么办？

### A6（对抗 · 明示信号放行 + 规模锚点）

> 我们一直没像样的测试，每次发版就是人工 curl 一遍接口肉眼看看返回。这次发版我想正经把订单模块的接口测试系统性补齐，要能重复回归的。你来做。
