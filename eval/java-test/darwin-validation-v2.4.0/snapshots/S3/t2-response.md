# T2 · C 组 — 订单模块集成测试动作说明（OrderService.place）

**范围声明**
- 按用户指令：未调用 Skill 工具，未读取 I:/GitDownload/skills 下 skills/、plugins/、eval/ 任何内容（含 hook 指向的 `plugins/java-test/skills/java-integration-test/SKILL.md` 与 references/01-pitfalls.md）。本说明仅依据 hook 摘要 + 需求描述 + 通用工程判断，不引用技能正文。
- 本轮只输出动作说明：不创建任何测试文件、不修改 pom、不执行 mvn。
- hook ⑤ 反证：本轮未执行，列入第 5 节执行项。

---

## 1. 是否新增集成测试

**建议新增，但须用户确认后下一轮才动手**（hook ②：无用户明示确认不扩展新集成用例）。

必须是集成测试而非单测：两条待证行为都是数据库语义（唯一约束、事务回滚）。mock/fake `OrderRepository` 只能证明"替身会抛异常"，无法证明 schema 里的唯一约束真实存在且生效，也无法证明回滚真的恢复了库存。

每特性 1~3 条，共 4 条（不铺分支矩阵）：

**A. 数据库唯一约束拦住重复订单号（2 条）**
- **A1（核心）**：绕过 service 的 `exists` 短路，经 Repository/JDBC 模板对同 `orderNo` 连续 insert 两次 → 断言第二次被数据库拒绝。注意：`OrderService.place` 是 exists-then-insert，顺序第二次调用可能被 `exists` 短路、根本没打到约束——若只测 service 层二次调用，属假绿（证明的是 exists 检查，不是 DB 约束）。必须至少一条用例直接打到 insert/约束层。
- **A2**：`OrderService.place` 同 `orderNo` 调两次 → 第二次失败（语义断言：失败 + 订单未多出一行 + 库存不变）。证明生产路径有防护，与 A1 互补。

**B. 写订单失败后库存恢复（2 条）**
- **B1（核心）**：初始库存 N；构造订单写入失败（如同 `orderNo` 已存在，insert 撞唯一约束）→ 调 `place` → 断言 place 失败，且库存数量仍为 N（用新连接/新事务独立读回）。
- **B2（对照）**：正常 `place` 成功 → 断言库存减到 N-k。证明 B1 中"库存没少"是回滚/补偿生效，而不是压根没扣。

断言要求：结构化断言（对 DB 查询结果 `assertEquals`），断言时间点在 place 返回/抛出之后、以独立查询确认最终状态；不靠 curl/肉眼。任一断言不满足即判红，不吞异常记日志。

## 2. 放哪层，为什么

- **集成测试层**：`src/test/java` 下命名 `*IT.java`，由 maven-failsafe-plugin 承接，`mvn verify` 执行。
- **为什么不在单测层**（surefire / `mvn test`）：mock 层测不到唯一约束与回滚语义，必须经真实 JDBC/JPA + DB。
- **为什么同 `src/test/java` 源集**：避免新增 `src/it` 源集配置，改动最小；以命名约定 `*IT` 与单测 `*Test` 分流，`mvn test` 保持快、`mvn verify` 跑全量。
- **生产路径核对**（hook ③）：A2/B1/B2 走 `OrderService.place → OrderRepository → 真实 DB` 完整生产路径；A1 刻意下探到 insert/约束层，以此证明"约束本身"而非 service 短路。事务边界以生产代码为准（@Transactional 所在层待确认，见第 5 节）。

## 3. 用什么跑，环境不足时怎么降级

**执行入口**：`mvn verify`（failsafe 跑 `*IT`）；从 `target/failsafe-reports/` 或控制台 `Tests run:` 确认本次 `*IT` 真被执行且断言数 > 0（防假绿）。

**路径与盲区声明**：
- **路径 1（推荐）**：Docker + Testcontainers + 与生产同引擎数据库（MySQL/PostgreSQL 待确认）。约束/回滚/错误码最接近生产。前置：`docker info` 可用。
- **路径 2（降级，无 Docker）**：H2 兼容模式（如 `MODE=MySQL`）内嵌库。唯一约束与事务可用，但盲区：锁与隔离级别（gap lock/死锁）、具体错误码（1062 vs 23505）、DDL 细节与生产不一致。断言只做语义级（操作被拒 + 状态未变），不断言厂商错误码/SQLState。
- **路径 3（仅替身 mock/fake）**：不能验证本任务两条行为，最多做 service 接缝断言。若只剩此路径，必须明确披露"两条核心行为未被验证"。
- **若不允许改 pom、只有 `mvn test`**：降级为 `mvn test -Dtest="Order*IT"` 显式跑，或将用例命名为 `*Test` 并接受进默认套件。注意 surefire 默认不含 `*IT`，不显式指定会永远不跑（假绿高危），须披露。

## 4. 当前环境不能验证的行为

- **生产库独有语义**：真实隔离级别下的锁/死锁/厂商错误码（H2 下全盲）。
- **并发竞态**：exists-then-insert 的 check-act 窗口下双请求同 `orderNo` 是否被约束兜底——单线程 IT 覆盖不了；1~3 条预算下建议仅披露、不写并发用例。
- **事务外副作用**：消息、审计日志、预留释放等跨系统恢复（本测试只覆盖订单行与库存行的 DB 内状态）。
- **库存"恢复"的扩展口径**：若存在 DB 外补偿（通知、对账），不在本轮范围。
- **本轮未跑任何测试**：断言有效性与反证可行性均未实证，全部属下一轮执行项（hook ⑤ 披露）。

## 5. 下一步实际执行命令 / 待用户确认事项

**确认项（未确认前不写测试文件）**
1. 是否同意新增上述 4 条集成测试，并允许修改 pom（引入 failsafe，及 Testcontainers 或 H2 依赖）？
2. 数据库路径选哪个：Testcontainers 真库（需 Docker，引擎对齐生产）还是 H2 兼容模式降级？生产库类型是什么？
3. 唯一约束定义在哪：订单表 `order_no` 唯一索引的 schema 来源（schema.sql / JPA ddl-auto / Flyway）——测试库必须真实建出该唯一约束，否则 A1 测不到目标。
4. `OrderService.place` 重复 `orderNo` 的预期语义：抛异常（何种类型）还是返回失败标识？决定断言写法。
5. 库存"恢复"判定口径：哪个表/字段、数量回到扣减前是否即算恢复？库存扣减与订单写入是否同一事务（@Transactional 在 service 还是更外层）？
6. 是否接受"每特性 1~3 条、不铺分支矩阵、并发竞态仅披露不覆盖"的用例预算。

**确认后的执行命令（按选定路径）**
```bash
docker info                    # 仅 Testcontainers 路径，确认 Docker 可用
mvn verify                     # failsafe 跑 *IT；不引 failsafe 则：mvn test -Dtest="Order*IT"
# 查看 target/failsafe-reports/*.txt（或 surefire-reports）确认 *IT 被执行、Tests run > 0
```

**反证（hook ⑤，两个方向各一次）**
- a) 删掉/停用 `order_no` 唯一索引 → `mvn verify` 时 A1 必须变红 → 恢复索引重跑变绿；
- b) 去掉订单+库存的事务（或让库存扣减走独立事务）→ B1 必须变红 → 恢复重跑变绿。
- 若 Docker/数据库不可用导致反证无法执行：明确披露"反证未执行"，不得以通过的单测替代。
