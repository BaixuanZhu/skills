# T2 · A 组评估响应（订单模块补测试）

> 范围：仅输出动作说明，本轮不创建任何测试文件。
> 约束：未读取 skills/、plugins/、eval/ 下任何内容；未调用 Skill 工具。
> 依据：仅基于需求描述与已知被测类 `OrderService.place(String orderNo, List<String> skus)`（经 `OrderRepository.exists/insert` 保存订单）。

---

## 1. 是否新增集成测试

**是，新增集成测试（IT）。**

理由：两个验收目标都属于数据库语义，mock/单测无法真实覆盖。

| 目标 | 为什么单测不够 |
|------|----------------|
| 唯一约束真的拦住重复订单号 | Mock `OrderRepository` 只能验证"代码调用了 exists/insert"，验证不了 DB 真的拒绝重复插入（约束是否建在正确列、异常类型/错误码、并发下的真实行为） |
| 写订单失败后库存能恢复 | 这是"扣库存 → 插订单失败 → 整个事务回滚"的跨表事务行为，必须有真实事务管理器 + 真实（或嵌入式）DB 才能把回滚链路跑起来 |

结论：保留现有 `mvn test` 单测（验证编排逻辑/分支），**另增集成测试层**验证 DB 约束与事务回滚，二者分层互补。

---

## 2. 放哪一层，为什么

**放在服务集成测试层：`OrderService` 级别的 `*IT.java`**（如 `OrderServicePlaceIT`），以 `OrderService.place(...)` 为入口，走真实 Spring 上下文 + 真实/嵌入式数据库 + 真实事务管理器。

- **放 Service 层的原因**
  - 唯一约束是 schema 行为，必须经过 `OrderService → OrderRepository → JDBC/ORM → DB` 完整链路才能触发约束。
  - "库存恢复"的语义是 `OrderService.place` 内部"扣库存 + 插订单"的事务编排结果；只有在这一层让真实事务跑起来，才能断言失败后库存回到初值。
- **不放 Controller 层**：HTTP/序列化/参数校验会引入噪音，约束仍在 DB，测试价值不增、稳定性下降。
- **不放 Repository 层单测**：单独测 `insert` 只能看到一条 insert 报错，看不到"库存已扣却要回滚"的业务语义；且"先查 exists 再 insert"的编排逻辑属于 Service。
- **目录与命名**：`src/test/java` 下对应包，类名 `*IT.java` 与单测（`*Test.java`）区分，用 maven-failsafe 分流；后续如需要也可拆到 `src/test/java/it` 独立 sourceSet。

建议最小用例集（仅描述，不建文件）：
1. `place_duplicateOrderNo_thenConstraintRejects`：首次下单成功；同 `orderNo` 再次下单 → 断言抛出约束异常/业务异常，且订单表仍只有 1 条。
2. `place_insertFails_thenInventoryRestored`：构造"库存已扣、订单插入必失败"场景（重复 orderNo / 注入异常 / 非法 sku），断言库存数量回到初值、订单表无脏行。

---

## 3. 用什么跑，环境不足时怎么降级

### 首选（完整 DB 语义）
- **真实数据库**：Testcontainers 启动与生产同版本的 MySQL/PostgreSQL（或 CI 内置 DB 服务）。
- **跑法**：`maven-failsafe-plugin` 执行 `*IT.java`，`mvn verify` 触发；日常 `mvn test` 仍只跑单测，保持反馈速度。
- **隔离**：每用例事务回滚 / `@Sql` 清理 / 唯一化 `orderNo`（如 UUID）避免互相污染。

### 降级路径（按环境可用性从高到低）
1. **无 Docker**：改用 H2/hsqldb 嵌入式库（`MODE=MySQL` 或 PostgreSQL 兼容模式），显式建 `UNIQUE` 约束 + 真实事务。
   - 能验证：约束存在并报错、事务回滚链路、库存恢复。
   - 结论降级为"约束与回滚链路正确"，**不等同于**"生产库能拦住"（异常类型、隔离级别、DDL 细节与生产有差异）。
2. **H2 也不便引入**：只保留 mock 单测验证"先 exists 后 insert、失败时不抛出未处理异常"的调用编排，并在用例名/注释里明确标注 **未覆盖 DB 语义**——这是兜底，不算集成测试。
3. **本机无 Java/Maven**：先探测环境（见第 5 节命令），改为在 CI 中跑，或请用户补齐本地 JDK/Maven。

### Maven 侧改动方向（本轮只描述，不落地）
- pom 增加：`testcontainers`（或 `h2`）测试依赖 + `maven-failsafe-plugin`；可用 profile（`-P it`）隔离，默认 `mvn test` 不跑 IT。

---

## 4. 哪些行为不能在当前环境验证

- **生产库真实约束细节**：约束名、错误码/duplicate key 文本、异常类型（MySQL `Duplicate entry` vs H2 约束异常不同）；H2 降级下无法证明生产库拦截行为。
- **并发唯一性竞争**：两线程/两请求同时插入同一 `orderNo` 的竞态结果，依赖真实库隔离级别与约束实现；H2 与生产可能不一致，需真实库 + 并发用例。
- **分布式/跨库场景**：若库存与订单不在同库同事务（跨服务、消息最终一致性），"库存恢复"不能用单库回滚验证——需要用户先确认架构（见第 5 节）。
- **连接池、事务超时、死锁重试、多数据源事务传播**等生产边界行为。
- **性能/批量压力**：约束在高并发写入下的表现。
- **当前工具链缺口**：若本机缺 JDK/Maven/Docker，本轮连 H2 用例也无法执行，只能给方案；且本轮按要求不创建测试文件，故任何行为在本轮均未实际验证。

---

## 5. 下一步实际执行命令 / 需用户确认事项

### 需要用户确认（阻塞项）
1. **生产数据库类型与版本**（MySQL 8.x / PostgreSQL x.x？）→ 决定 Testcontainers 镜像或 H2 兼容模式。
2. **是否允许改 pom.xml 引入测试依赖**（testcontainers/h2、failsafe 插件）。
3. **是否有 Docker 可用** → 决定走真实库还是 H2 降级。
4. **库存与订单是否同库同事务** → 决定"库存恢复"的验证口径（同事务回滚 vs 需补偿/对账）。
5. **失败注入点**：重复 `orderNo` 二次插入即可触发约束；但"订单失败后库存恢复"需要确认可让 insert 抛错的注入方式（重复号复用 / 非法 sku / 测试用异常注入）。

### 环境探测与执行命令（确认后）
```bash
java -version
mvn -version
docker --version          # 决定能否走 Testcontainers
mvn test                  # 先保证现有单测绿（当前唯一的测试入口）
# 新增 IT 落地后：
mvn verify                # 或 mvn -P it verify，跑集成测试
```

### 本轮产出与边界
- 产出：本文件（动作说明）。
- 未做：未创建测试文件、未改 pom、未调用 Skill、未读取 skills/plugins/eval 内容。
- 下一轮（待用户确认后）：落地 `OrderServicePlaceIT` 两个用例 + pom 测试依赖/failsafe 配置，按降级路径选真实库或 H2。

—— 完 ——
