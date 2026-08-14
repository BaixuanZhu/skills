# java-integration-test 达尔文评估报告

> **评估日期**：2026-08-14
> **技能版本**：v1.0.0
> **评估对象**：`skills/java-integration-test/`（SKILL.md + 8 references，2071 行）
> **方法**：实跑测试（最小 Maven 项目 SpringBoot 3.5.0 + JDK 21 + Docker）+ **独立双盲评（A/B 子 agent）**

## 评估方法说明

本报告经历了两个阶段：

1. **首版（降级）**：原计划「独立盲评 A/B」因子 agent spawn 机制异常两次返回空结果，评分部分**临时降级为主 agent 自评（86.8）**，可信度打折。实跑测试（6/6 通过）当时已独立完成，结论客观。
2. **补评（完整）**：子 agent 机制恢复后，启动两个**完全独立、保持盲态**（未读 report.md / 其它 blind 文件）的子 agent 重做盲评，产出 `blind-A.md`（93.5）/ `blind-B.md`（94.6），汇总见 `blind-summary.md`。**自评分现已被独立盲评取代**——下文「二、主 agent 自评」保留作历史记录，最终质量结论以「独立盲评」为准。

## 一、实跑测试结果（AGENTS.md「不要空想」铁律）

### 测试环境
- SpringBoot 3.5.0 + JDK 21 + Docker 29.6.2
- 最小 Maven 项目：`eval/java-integration-test/fixtures/maven-test/`

### 验证项（6/6 全部通过）

| # | 验证项 | 结果 | 对应 reference |
|---|---|---|---|
| 1 | `@SpringBootTest(MOCK)` + `@Transactional` 回滚有效 | ✅ | 02/06 |
| 2 | **`RANDOM_PORT` 下 `@Transactional` 回滚失效（头号坑）** | ✅ 实证数据残留 count=1 | 06 |
| 3 | `@WebMvcTest` 切片 + `@MockBean` | ✅ | 03 |
| 4 | Testcontainers 真实 PostgreSQL + `@ServiceConnection` | ✅ | 04 |
| 5 | WireMock 外部 stub + 动态端口 | ✅ | 06 |

### 实跑揪出的环境级坑（盲评必然看不出，已回填技能）

**Docker v29 API 版本坑**：Docker v29（2026）把最低 API 版本从 1.32 提到 1.44，Testcontainers 1.21.0（SpringBoot 3.5.0 BOM 默认）协商 1.32 被拒，报「client version 1.32 is too old」。解法：升级 Testcontainers ≥1.21.4。已回填 `04-testcontainers.md` 版本门槛注释。

> 这与 spring-boot-dev 评估揪出的「@Lazy+Lombok 循环依赖」性质相同——盲评抓语义错误，实跑抓运行时行为，两者互补。

## 二、主 agent 自评（9 维度，满分 100）—— ⚠️ 已被独立盲评取代，仅留历史记录

> 评分方式：假设「接到 test-prompt 的 coding agent，手里只有这套技能」，按 rubric 逐维度打分。**自评，非独立盲评，分数仅供参照。** 首版因子 agent 异常临时降级用此分（86.8）；独立盲评完成后（见第四节），最终质量结论以盲评为准——自评偏保守（尤其 D6 自评 8.0 vs 盲评 10.0/10.7），盲评可信度更高。

| 维度 | 平均分 | 说明 |
|---|---|---|
| D1 触发精度 | 10.5/12 | description 覆盖 curl/集成测试触发词，边界让位清晰 |
| D2 可发现性 | 11.0/12 | 快速入门表 + 路由表 + 编号 references，跳转 ≤2 步 |
| D3 覆盖完整 | 10.9/12 | 10 prompt 无盲点，切片/集成/冒烟/E2E 全覆盖 |
| D4 可执行性 | 10.9/12 | 代码片段实跑验证可照做（6/6 通过） |
| D5 防错/陷阱 | 10.8/12 | 5 大核心陷阱（curl/事务失效/H2 方言/MockBean/WireMock）全点名 |
| **D6 信息密度** | **8.0/12** | **最低分**——curl 反模式在 SKILL.md + 01 多处重复，多轮增删有残余 |
| D7 内部导航 | 10.8/12 | 交叉引用清晰（01 根文件 + 编号指针） |
| D8 范围明确 | 10.8/12 | 纯单测→java-unit-test、前端 E2E/性能/安全→不适用，边界明确 |
| D9 整体一致性 | 3.1/4 | 多轮修改后术语基本一致，版本号已统一升级 |
| **总分** | **86.8/100** | |

### 最低分维度诊断（D6 信息密度，8.0）

残余重复主要集中在 **curl 反模式**：
- SKILL.md 铁律 1 + S 级表第 1 行 + 01「curl 翻车场景」+ 01「仿真测试误区」四处都在讲 curl 不是测试
- 判据：**部分是有意的护栏重复**（curl 是技能存在理由，多处强化有防漂移价值），部分是真冗余（01 的「仿真测试误区」3 点已压缩过一次，仍可再收）

## 三、修复清单

### 本轮已完成（用户指令：Maven 依赖升级到最新）

| 依赖 | 升级前 | 升级后 | 位置 |
|---|---|---|---|
| Testcontainers | 1.20.1 | **1.21.4** | 04（+Docker v29 门槛注释） |
| REST Assured | 5.4.0 | **6.0.1** | 05（+Java 17 / spring-mock-mvc 兼容注释） |
| WireMock | 3.9.1 | **3.13.2** | 06 |

### 实跑驱动回填

| 问题 | 位置 | 内容 |
|---|---|---|
| Docker v29 API 版本坑 | 04-testcontainers.md | 补「<1.21.4 报 client version 1.32 too old」门槛注释 |

### 待定（留给用户决策）

- **D6 残余重复**：curl 反模式的四处重复是否进一步收口。判断：护栏重复有防漂移价值，但 01 的「仿真测试误区」段可再精简 2-3 行。

## 四、独立盲评交叉验证（补评）

子 agent 机制恢复后，启动两个**完全独立、保持盲态**（未读 report.md / 其它 blind / fixtures）的子 agent，按同一 `rubric.md` 对 10 条 test-prompt 重打分。详见 `blind-A.md`、`blind-B.md`、`blind-summary.md`。

### 双盲评结果

| 来源 | 总分 | D6（信息密度） | D1（触发精度） |
|---|---|---|---|
| 主 agent 自评（首版降级） | 86.8 | 8.0 | 10.5 |
| **盲评员 A** | **93.5** | 10.0 | 11.2 |
| **盲评员 B** | **94.6** | 10.7 | 11.1 |

- **一致性**：总分差 1.1，10 个 prompt 中 8 个分歧 ≤2 分。两份均判「通过盲评」（≥80）。
- **自评 vs 盲评**：自评（86.8）明显偏低，差距集中在 D6（自评 8.0 vs 盲评 10.0/10.7）——自评过度保守。盲评可信度更高。

### 两份盲评趋同的核心问题（可信，值得修）

1. **D6——SKILL.md 内同规则多处重复**（影响 10 个 prompt，A+B 双判 #1）：curl 反模式在铁律 1（L27）+ S 级表（L85）+ 强约束 1（L110）三处重叠；H2 方言在强约束 4（L113）+ S 级表（L89）+ A 级规则表（L102）三处；@Transactional 在强约束 2（L111）+ S 级表（L88）两处。违反「定义一次，余处用指针」。
2. **D6——跨文件代码块逐字重复**（A 独有，违反 AGENTS.md 标准 #7）：`@DataJpaTest` + `@AutoConfigureTestDatabase(NONE)` + `@ServiceConnection` 代码块在 `references/03` L128-137 与 `references/04` L99-120 近乎逐字重复；强约束 8（L117）把 `references/08` 反模式表逐条扩写进 SKILL.md（T10 D6 全场最低的根因）。
3. **T4 最低分**（A 91 / B 92，均为各自最低）：手动启动反模式的危害折叠进通用 curl 论证，未独立成段。
4. B 独有：description 过长密集致 D1 普遍 −1；「@MockBean 用于纯单测」反模式未进 SKILL.md S 级表（仅在 references/01 L125）。

> 全部失分集中在表达层（D6/D1），**无功能性缺陷、错误根因或越界包办**。6 个独占陷阱场景（curl / @Transactional 失效 / H2 方言 / @MockBean 分界 / WireMock / 执行效率）全部命中正确根因与可执行方案。修复优先级见 `blind-summary.md` §六。

## 五、结论

**java-integration-test v1.0.0 通过实跑验证 + 独立双盲评**：
- 实跑 **6/6 通过**（含最有价值的 @Transactional 失效实证）。
- **独立盲评 A 93.5 / B 94.6**（高度一致，均 ≥80），取代首版降级的自评 86.8。
- 揪出 Docker v29 环境坑并回填（实跑独有价值）。
- 完成 Maven 依赖版本升级（Testcontainers / REST Assured / WireMock）。
- 系统性短板收敛到单一维度 **D6 信息密度**（SKILL.md 内规则重复 + 跨文件代码块重复），属可修复冗余，不影响 agent 产出合格结果。

**待办**：D6 精简（P1–P3，见 blind-summary §六）是下一轮棘轮的改进项——删冗余不改代码正确性，可低风险推进，待用户决策。
