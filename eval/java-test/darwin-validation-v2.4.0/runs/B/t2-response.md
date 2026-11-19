# T2 · B 组评估回复（订单模块补测试 · 动作说明，本轮不创建测试文件）

依据：`skills/java-integration-test/SKILL.md` v2.4.0 三决策 + `references/01-pitfalls.md`。

---

## 1. 是否新增集成测试 —— 是

走决策 ①：

- **值守情况**：团队没有专职测试 → 属"无专职测试（个人 / 小团队）"，动作是**建**，但只做冒烟 + 核心链路（本例就是那两条断言），不铺分支矩阵。
- **激活时机**：用户明示"给订单模块补测试"，且明确要验数据库语义（唯一约束、失败回滚）→ 属"明示"信号，直接开始，不追问。
- 两条目标断言（唯一约束拦重复订单号、写订单失败库存恢复）都**离开真实依赖不成立**（mock Repository 无法产生 DB 约束拒绝与事务回滚），必须落在集成层，单测层守不住。因此**新增集成测试，不新增单测替代**（Service 分支矩阵如需补，归 java-unit-test，本轮不在范围）。

## 2. 放哪层 —— 集成层（SQL/事务语义层），断言打在 Service → DB 的最终状态上

走决策 ②，两条断言均命中"集成层"判据：

| 断言 | 依赖什么 | 层 |
|---|---|---|
| 重复 `orderNo` 插入被数据库唯一约束拒绝 | 真实约束语义（不是 `exists` 的应用层判断） | 集成层 |
| `place` 失败后库存恢复 | 事务传播与回滚的**最终状态**（Service `@Transactional` 真实生效） | 集成层 |

- 用 `@SpringBootTest`（或 `@DataJpaTest` + `replace = NONE`）+ 真实库，直接调 `OrderService.place(...)`，**不做** `@WebMvcTest`/MockMvc——被测类是 Service，不涉及 HTTP 管道。
- 断言设计要点（防假绿，对应 pitfalls）：
  - 回滚断言**禁止**在测试类/方法上加 `@Transactional`（陷阱：测试事务并入 Service 的 `REQUIRED` 事务，回滚断言恒真）。测试不带事务，让 Service 自己提交/回滚，测试只读**最终状态**，用 `@AfterEach` 精确 `DELETE` 或独立 schema 清理。
  - 重复订单号断言不能只靠 `OrderRepository.exists` 为 true——那测的是应用层查询，不是约束。必须**实际 insert 同一 `orderNo` 两次（或绕过 `exists` 直插），断言第二次被 DB 拒绝**（异常类型见第 4 条盲区说明）。
  - 每条断言能答"这行代码坏了哪条变红"：`@Transactional` 删掉 → 回滚用例必须变红（反证项）；唯一索引删掉 → 重复订单号用例必须变红。
- 每特性 1~3 条锚定用例即可，分支矩阵不进这一层。

## 3. 用什么跑，环境不足时怎么降级 —— 决策 ③ 三条路径，按环境选一条并写明

**执行机制（与环境无关，先固定）**：项目当前只有 `mvn test`，集成用例**不得混进 `mvn test`**。约定：类名 `*IT` 后缀 + Maven Failsafe 绑 `verify` 阶段，用 `mvn verify`（或 `mvn failsafe:integration-test`）跑集成层；Surefire（`mvn test`）只跑单测。

**环境路径（按序探测，选中哪条必须在回复/交付里写明）**：

| 优先级 | 环境 | 路径 | 标注 |
|---|---|---|---|
| 1 | 有 Docker（本机或 CI） | Testcontainers 起真实库，镜像 tag 对齐生产版本；容器 `static` 复用 | 首选，可重复 |
| 2 | 无 Docker，本机能起真实库 | 连本地实库 + **每测试类独立 schema/库名（`_ittest` 后缀）**，并满足 pitfalls 三条：测试专属 profile（不动 `application.yml`）、库账号无权碰其它库、启动时断言 `getMetaData().getURL()` | 降级路径一，**不可重复**：换机器/上 CI 就挂，库版本可能与生产不一致 |
| 3 | 都没有 | **同族嵌入式替身**：H2 且 `MODE` 对齐目标库（MySQL→`MODE=MySQL`，PG→`MODE=PostgreSQL`），配 `@AutoConfigureTestDatabase(replace = NONE)` 之反——此处恰是要替身，则显式用 H2 并**标注「非生产方言」** | 降级路径二，有盲区，必须带移交清单（见第 4 条） |

按 pitfalls 的能力表，**替身上能验**的恰好覆盖本轮两条断言：事务传播与回滚的最终状态（JDBC/Spring 语义，与方言无关）、唯一约束是否真的拦住。所以即使环境最差，这两条也不放弃、不空手说"不写"；不能验的逐条列清单移交真库。

## 4. 当前环境不能验证的行为（盲区 / 移交真库清单）

若走路径 2/3（无 Docker），以下**不在本轮验证范围**，移交真库/生产同版本库补验：

1. **SQL 方言特性**：`ON CONFLICT`、`jsonb`/`ARRAY`、序列/自增行为、排序与大小写敏感性、唯一索引对 NULL/空串的处理差异（H2 与 MySQL/PG 语义不同）。
2. **具体错误码与异常类型**：驱动异常层次两边不同——H2 拒绝重复键抛的异常类型/错误码与 MySQL（1062）/PG（23505）不一致，故断言**不锚定具体驱动异常类**，只断"插入被拒绝 + 库中无第二条 + 库存未扣"，异常映射逻辑若业务依赖精确类型，移交真库验。
3. **生产库版本行为**：路径 2 本机库版本可能与生产不一致；路径 3 完全无版本对齐。
4. **迁移脚本**（若用 Flyway/Liquibase）：唯一索引 DDL 在 H2 上可执行 ≠ 生产方言正确（如索引类型、`NULLS NOT DISTINCT`），DDL 正确性移交真库。
5. **并发双插（race condition）**：`exists` 后 `insert` 的 check-then-act 竞态需并发测试配合真库隔离级别验证，本轮两条用例只锚定单线程下约束生效。
6. 另注意（不算盲区，是配置前提）：**failsafe 未配置前，本轮用例在 `mvn test` 下根本不执行**——不执行≠通过。

## 5. 下一步实际执行命令 / 需用户确认事项

**需要用户确认（阻塞项，动手前问清）**：

1. **生产数据库类型与版本**（MySQL x.x / PostgreSQL x.x）——决定 Testcontainers 镜像 tag 或 H2 `MODE`。
2. **环境能力**：本机有没有 Docker？没有的话有没有可用本地实库（连接串、专用测试账号）？——决定走决策 ③ 哪条路径。
3. **库存表结构与扣减方式**：`place` 失败链路里库存是同事务内扣减（单库事务可回滚）还是发消息/调外部服务（需 WireMock/事务外补偿，方案不同）？
4. 确认 `OrderService.place` 上的事务边界（有无 `@Transactional`、异常类型是否触发回滚，默认 RuntimeException 才回滚）。

**确认后实际执行的命令序列（本轮只列动作，不建文件）**：

```bash
# 1) 补 pom.xml：failsafe 插件绑 verify（类名 *IT 隔离出 mvn test）
mvn -q test              # 先保证存量单测仍绿（集成层不混入）
mvn verify               # 跑新增的 *IT，从输出/报告确认 OrderServiceIT 确实被执行
```

**交付前自检中必须实际执行的验证（写测试后做）**：

```bash
# 反证 1：临时删掉 OrderService 上的 @Transactional → 库存恢复用例必须变红，恢复后重跑为绿
# 反证 2：临时去掉订单表唯一索引（迁移里注掉）→ 重复订单号用例必须变红，恢复后为绿
mvn verify               # 反证前后各跑一次，比对结果
```

同时：读启动日志确认无 WARN/ERROR；数据清理用 `@AfterEach`/精确 `DELETE`（不用测试级 `@Transactional`）；若路径 2，启动时断言 `getMetaData().getURL()` 含 `_ittest` 库名。

---

**结论**：新增集成测试（决策①过：无专职测试 + 明示信号）；放集成层验 DB 唯一约束与事务回滚最终状态（决策②）；执行走 `*IT` + Failsafe `mvn verify`，环境按 Testcontainers → 本地实库+独立 schema → H2 同族替身降级并标注盲区（决策③）；方言特性与驱动错误码等 6 项列移交清单；下一步先向用户确认 DB 版本与环境能力，再动 pom 与测试代码。
