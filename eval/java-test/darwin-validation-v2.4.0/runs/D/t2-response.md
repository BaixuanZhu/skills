# T2 · D 组 · 集成测试动作说明（java-integration-test v2.4.0）

日期：2026-11-19
本轮性质：**只输出动作说明，不创建任何测试文件、不改动 src / pom**；所有执行与反证推迟到实施轮，并在下方明确披露。
被测场景：`OrderService.place(String orderNo, List<String> skus)`（`src/main/java/com/example/eval/OrderService.java:17`）——用户要求保证 ① 数据库唯一约束真的拦住重复订单号 ② 写订单失败后库存能恢复。

## 0. 技能加载

- 已读取 `plugins/java-test/skills/java-integration-test/SKILL.md`（v2.4.0，三个决策全文在手）。
- 命中假绿症状（测试级 `@Transactional` 回滚断言恒真——机制一，正中「库存恢复」场景），已补读同目录 `references/01-pitfalls.md`。
- 本 fixture 为无 Spring 的纯 Java + 接口持久层（`OrderRepository.java:5` 仅 `exists/insert`），层判据按「测试自管真实依赖」走，不依赖注解形态。

---

## 1. 是否新增集成测试：**是（仅限用户明示的两条特性）**

**决策①（建不建）——值守情况：团队没有专职测试 → 建，优先冒烟 + 核心链路。**
激活时机为**明示**：用户直接要求「给订单模块补测试」，且两条目标行为（DB 唯一约束、事务回滚最终状态）按决策②判据均属集成层 → 直接开始，不再追问。

范围与配额（hook ②③：不扩展、每特性 1~3 条、不铺分支矩阵）：

| 特性 | 条数 | 内容 |
|---|---|---|
| A · 唯一约束拦住重复订单号 | 2 | ① 走生产链路 `place()` 重复下单被拒、库内该 orderNo 仅一行；② **绕过应用层 exists 检查**直插（或并发双插）重复 orderNo，撞库上 UNIQUE 约束被拒 |
| B · 写订单失败后库存恢复 | 1 | 同事务「扣库存 → 写订单（注入失败）」，`place()` 抛出后库存终态 = 初始值、订单表无残留行 |

- 为什么必须有 ②：`OrderService.java:24-27` 是 exists-then-insert 的 check-then-act，**存在 TOCTOU 竞态**——应用层检查不是防线，UNIQUE 约束才是。只测「`exists()` 返回 true 时抛 `IllegalStateException`」测的是业务规则（单测层的事），验不了「约束**真的**拦住」（mock 的 insert 不抛就绿，schema 丢了约束测试也不知道）。
- **不新增**：`orderNo` 空白 / `skus` 空校验（`OrderService.java:18-23`）属业务规则 → 留 java-unit-test 层；分支矩阵、DTO、参数校验一律不进集成层。契约切片（`@WebMvcTest` 等）本项目无 Controller，不适用。
- 超出上述两条特性的任何新集成用例：**不扩展，先向用户确认**（hook ②）。

## 2. 放哪层，为什么：**集成层（真实库语义）**

**决策②判据：断言离开真实依赖还成立吗？——不成立，进集成层。**

- 「唯一约束是否真的拦住」：约束定义在 schema 上，是数据库语义 → 对应表中「SQL 实际执行 / 迁移 / 事务传播 → 集成层」。
- 「写订单失败后库存恢复」：验的是事务回滚的**最终状态**（决策③表中明确标注「能验」，但必须有真实事务管理与真实连接）。
- 反例对照：mock Repository 的单测两条都验不了——mock insert 不会撞约束、mock 不存在事务，绿灯是假的。

**三个假绿机制逐项核对（hook ③）：**

- **生产路径**（机制一）：
  - 回滚用例的测试**绝不加**测试级 `@Transactional`——否则 Service 的 `REQUIRED` 并入测试事务，异常只标 rollback-only，「库存恢复了」恒真，连 `OrderService` 根本没有 `@Transactional` 都能绿（pitfalls 机制一第 1 条）。改法：测试不带事务，让 Service 自己提交/回滚，测试只读终态，独立 schema 或显式清理。
  - 断言必须走真实调用链 `OrderService.place(...)`（含扣库存的真实生产实现），禁止直操 DAO「模拟失败」造回滚假象。
  - 约束用例必须含绕过应用层 `exists` 的直插路径（特性 A ②），否则测的不是约束。
- **断言时间点**（机制二）：`place()` 同步返回后再断言；库存/订单终态用**独立连接/新事务**读取，确保读到已提交或已回滚的终态而非未提交中间态。本场景无异步，无 `RANDOM_PORT` 事务陷阱。
- **失败会判红**（机制三）：一律结构化断言——
  - 约束用例：`assertThatThrownBy(...)` 断**具体**约束违例异常/上层封装（不断 `Exception` 根父类）+ 断库内该 orderNo 恰好 1 行；
  - 回滚用例：断库存数量 `isEqualTo` 初始值（精确数值）+ 订单表 0 残留；
  - 「改坏哪行会红」可回答：删 UNIQUE 约束 → A ② 红；删 Service 事务边界 → B 红（反证即用这两刀）。
  - 无 curl / 肉眼判断，全部断言进 JUnit。

## 3. 用什么跑，环境不足时怎么降级：**决策③ 第一条 Testcontainers**

**本机实测（本轮探测，非猜测）**：Docker 29.9.2 daemon 在线、Apache Maven 3.10.0 可用 → **走第一条：Testcontainers，镜像 tag 对齐生产库版本**（生产库类型/版本待确认，见 §5）。容器 `static` 复用，单测试类起一次。

- **执行入口**：项目当前只有 surefire `mvn test`。集成用例**不混进 `mvn test`**——新增 maven-failsafe-plugin 绑 `verify`、类名 `*IT`，用 `mvn verify` 跑；从 `target/failsafe-reports` / 控制台用例计数确认 `*IT` 真被执行（BUILD SUCCESS 不是执行证据）。surefire 与 `mvn test` 语义不动。
- **降级路径（写明，不静默替换）**：
  - 无 Docker 但有本地实库 → 第二条：本地实库 + 每测试类独立 schema。标注**不可重复**（换机器/上 CI 就挂，库版本可能与生产不一致）。pitfalls 附录三件套必须齐：测试专属 profile、库名 `_ittest` 后缀 + 账号无权碰其它库、启动断言 `getMetaData().getURL()`（防连错库误删）。
  - 两条都没有 → 第三条：同族嵌入式替身 **H2（`MODE` 对齐生产方言）**。按决策③表格，本场景两条断言在替身上**能验**（事务回滚最终状态、唯一约束是否真的拦住——均为 JDBC/事务语义，与方言无关）。必须标注「**非生产方言**，以下行为未验」并附移交清单（§4）。空手说「不写」与「拿替身冒充真库」同样不合格。
- 外部依赖（支付/短信等）本场景不涉及；若真实项目链路里有，一律 WireMock 动态端口，不真调。

## 4. 哪些行为不能在当前环境验证（盲区披露）

**本轮（动作说明轮）执行披露（hook ⑤）：本轮不创建测试文件，`mvn verify` 未执行、存量 `mvn test` 未重跑、反证（改坏实现→变红→恢复→变绿）未做——全部推迟到实施轮，届时必须补做并附报告。此为「无法执行」的明确披露。**

实施后仍存在的盲区（按路径分列）：

| 行为 | Testcontainers 真库 | H2 替身路径 |
|---|---|---|
| 唯一约束拦截、回滚终态 | 可验 | 可验（JDBC/事务语义） |
| SQL 方言特性（`jsonb`/`ARRAY`/`ON CONFLICT`/排序与大小写敏感） | 可验 | **不能验** → 移交真库 |
| 具体错误码与异常类型（H2 23505 vs MySQL 1062 vs PG 驱动异常层次） | 可验 | **不能验** → 移交真库，断言只锁上层语义 |
| 迁移脚本在生产方言下的可重放性 | 可验 | **不能验** → 移交真库 |
| 高并发下 exists-then-insert 竞态真实表现（隔离级别差异） | 部分可验 | **不能验** → 移交真库（正因如此特性 A ② 要直插验约束） |

**代码侧缺口（当前环境无法验证的根因）**：fixture 的 `OrderService.place` / `OrderRepository` **没有任何库存读写**（仅 `exists/insert`，`OrderRepository.java:5-8`）。「写订单失败后库存能恢复」需要生产上**同一事务内扣库存 + 写订单**的真实方法链路与一个可注入的失败点；fixture 只是集成层激活探针。真实链路确认前，特性 B 只能定设计、落不了代码（见 §5 确认项）。

## 5. 下一步：实际执行命令 / 需用户确认事项

**需要用户确认（缺一不可，先确认后动手）：**

1. **生产数据库类型与版本**（决定 Testcontainers 镜像 tag / H2 `MODE` 对齐目标，镜像 tag 对齐生产、不硬编码 patch 号）。
2. **真实项目中「扣库存 + 写订单」的事务边界与调用链**（fixture 无库存逻辑），以及「写订单失败」的可注入失败点（如第二步抛错的位置）。
3. **schema 归属**：UNIQUE 约束与库存表定义在既有迁移脚本（Flyway/Liquibase）里，还是测试自建 schema。
4. **范围确认**：本轮集成用例仅特性 A（2 条）+ 特性 B（1 条）；超出即停、先问（hook ②）。

**实施轮的实际执行命令（本轮不执行，仅列出）：**

1. 基线：`mvn test` —— 确认存量 `PricingServiceTest` 绿，不回归。
2. 正跑：`mvn verify` —— 从 `target/failsafe-reports` 确认 `*IT`（约 `OrderConstraintIT` / `OrderTxIT`）被执行且计数正确。
3. **反证**（至少覆盖两条特性各一）：
   - 临时删表上 `UNIQUE` 约束 → 特性 A ② 必须变红 → 恢复约束重跑变绿；
   - 临时删 Service 的事务边界（`@Transactional` 或等价事务模板）→ 特性 B 必须变红 → 恢复重跑变绿。
   - 恢复后 `git diff` 干净（src / pom / 迁移零残留改动）；项目若配变异测试门禁，以其结果一并为准。
4. 交付前自检按 SKILL「交付前自检」清单逐项过，尤其：回滚用例无测试级 `@Transactional`、启动日志 WARN/ERROR 已排查、断言可答「改坏哪行会红」。

**pom 改动预告（实施轮，本轮不动）**：加 `maven-failsafe-plugin`（bind `verify`）；按确认结果加 Testcontainers（首选）或 H2 + 对齐 `MODE`（test scope）；surefire 配置保持不变。
