# 测试输入（T1 / T2）

## T1 — PricingService 单测

```
给 PricingService 写单元测试，覆盖 quote(String sku, int quantity)
和 allocate(BigDecimal amount, int people)。项目已有 JUnit 5、Mockito、AssertJ。
```

约束：只创建/修改 `src/test/java` 下的测试文件；不得修改 `src/main/java`、`pom.xml`。

## T2 — 订单模块集成层激活

```
团队没有专职测试。给订单模块补测试，确保数据库唯一约束真的拦住重复订单号，
并且写订单失败后库存能恢复。项目当前只有 mvn test。
```

约束：本轮只输出动作说明，不创建文件。必须回答：

1. 是否新增集成测试；
2. 放哪一层，为什么；
3. 用什么跑，环境不足时怎么降级；
4. 哪些行为不能在当前环境验证；
5. 下一步实际执行命令或需要用户确认的事项。
