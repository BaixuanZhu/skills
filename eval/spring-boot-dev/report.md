# spring-boot-dev 达尔文评估报告

> **评估日期**：2026-08-05
> **技能版本**：v1.0.0
> **评估对象**：`skills/spring-boot-dev/`（SKILL.md + 12 references，2391 行）
> **方法**：独立盲评 A/B + 实跑测试（最小 Maven 项目 SpringBoot 3.5.0 + JDK 17）

## 一、评估流程

```
test-prompts（10 条对抗 prompt）
    ↓
rubric（9 维度评分标准）
    ↓
独立盲评 A / B（并行，互不知晓）→ 仲裁
    ↓
实跑测试（Maven 编译 + 启动 + API 验证）
    ↓
棘轮（只保留已验证改进）
```

## 二、评分汇总

| 维度 | A 打分 | B 打分 | 仲裁采纳 | 说明 |
|---|---|---|---|---|
| D1 触发精度 | 11.5 | 11.9 | **11.7** | 边界让位在 4 处一致声明，T1/T10 多技能竞争下不越界 |
| D2 可发现性 | 11.5 | 11.5 | **11.5** | 决策路由表清晰（B 指出 SKILL:88 曾误指 06，已修） |
| D3 覆盖完整 | 11.6 | 11.5 | **11.6** | 10 prompt 无盲点 |
| D4 可执行性 | 11.1 | 11.0 | **11.1** | 代码片段可直接照做（实跑验证通过） |
| D5 防错/陷阱 | 11.2 | 10.6 | **10.9** | B 发现 ListenableFuture 废弃 + 字段注入矛盾，已修 |
| **D6 信息密度** | **8.1** | **9.1** | **8.6** | **最低分**——残余重复（见下方仲裁） |
| D7 内部导航 | 11.0 | 11.0 | **11.0** | 路由表 + 交叉引用清晰 |
| D8 范围明确 | 11.1 | 11.9 | **11.5** | 不适用项指向 4 个兄弟技能 |
| D9 整体一致性 | 4.0 | 3.5 | **3.8** | B 扣分因 ListenableFuture/字段注入矛盾，已修 |
| **总分** | **91.1** | **92.2** | **91.7** | |

## 三、实跑测试结果（AGENTS.md 要求「不要空想」）

### 测试环境
- SpringBoot **3.5.0** + JDK 17（实跑用 JDK 21）
- 最小 Maven 项目：`eval/spring-boot-dev/fixtures/maven-test/`

### 验证项（全部通过，最终回归 2026-08-05）

| # | 验证项 | 结果 | 证据 |
|---|---|---|---|
| 1 | Maven 编译（clean compile） | ✅ | 退出码 0，无报错 |
| 2 | 应用启动 | ✅ | `Started DarwinTestApplication in 1.387 seconds` + Tomcat 8080 |
| 3 | profile 加载（01） | ✅ | `Profile is active: "dev"` |
| 4 | Bean 参数校验 + 组合注解 + properties 插值（T1） | ✅ | `{"code":400,"message":"phone: 手机号格式不正确; username: 用户名长度需在 3-20 字符; email: 邮箱格式不正确; password: 长度需要在8和32之间"}` |
| 5 | 组合注解单报（`@ReportAsSingleViolation`） | ✅ | `@ValidPhone` 只报 1 条（非 Pattern+Size 各报） |
| 6 | 非 Bean 参数校验 `@RequestParam @Min`（T4） | ✅ | `size=0` → `{"code":400,"message":"search.size: 最小不能小于1"}`；`size=5` → 200 |
| 7 | 全局异常（Bean 校验 + 非 Bean 校验 + 兜底，T5） | ✅ | `ConstraintViolationException` 返回 400（非 500） |
| 8 | 校验通过返回 VO（无 password 泄漏，T1b） | ✅ | `{"code":200,"data":{"id":null,"username":null}}`（无 password 字段） |
| 9 | SpringDoc api-docs + swagger-ui（T11） | ✅ | 两个端点均 HTTP 200 |
| 10 | 自动装配 `AutoConfiguration.imports`（T8） | ✅ | 启动无报错，`MyService` Bean 注册 |
| 11 | `@ConfigurationProperties` 松散绑定（03） | ✅ | `app.user-name` → `userName` 字段绑定 |
| 12 | `@Lazy` 自注入手写构造器（事务解法 2，T2） | ✅ | 启动无循环依赖报错 |

### ⚠️ 实跑发现的 Bug（盲评未发现，实跑揪出）

#### Bug 1：`@Lazy` 自注入 + Lombok `@RequiredArgsConstructor` 启动失败

- **现象**：`UserService` 用 `@RequiredArgsConstructor` + `private final UserService self`（字段上加 `@Lazy`），启动报 `BeanCurrentlyInCreationException`（循环依赖）
- **根因**：Lombok 生成的构造器**不会把字段上的 `@Lazy` 传到构造器参数**，Spring 拿不到 `@Lazy` 语义，按普通构造器注入处理 → 循环依赖
- **正确写法**：手写构造器 `public UserService(@Lazy UserService self)`
- **修复**：已在 06/09/SKILL.md 强约束 2 三处补警告；同时应用户反馈，解法优先级改为「拆 Bean（推荐）> @Lazy（次选）> AopContext（不推荐）」

#### Bug 2：组合注解默认多报（`@ReportAsSingleViolation` 缺失）

- **现象**：`@ValidPhone`（组合 `@Pattern` + `@Size`）校验失败时返回两条错误（「手机号格式不正确」+「个数必须在11和11之间」）
- **根因**：组合注解（`@Constraint(validatedBy={})`）默认报告每个组成注解的违反
- **正确写法**：加 `@ReportAsSingleViolation`，只报组合注解自身的 message
- **修复**：04-validation.md「组合注解的『多报一』坑」一节；实跑验证加注解后只报一条

> **两个 bug 都是盲评未发现、实跑揪出的**——印证 AGENTS.md「实跑测试，不要空想」的铁律。盲评能抓语义/事实错误（如 ListenableFuture 废弃），但抓不了运行时行为（如注解多报）。

## 四、修复清单（本轮共修复 10 项）

### 实跑驱动修复（2 项）

| # | 问题 | 修复位置 | 修复内容 |
|---|---|---|---|
| F1 | `@Lazy` + `@RequiredArgsConstructor` 启动失败 | 06-transaction.md 坑 1 / 09-autowiring.md 解法 2 / SKILL.md 强约束 2 | 三处补「`@Lazy` 须手写构造器」警告；解法优先级改为拆 Bean 首位 |
| F2 | 组合注解默认多报 | 04-validation.md 组合注解节 | 补「`@ReportAsSingleViolation`」坑 + 实跑验证 |

### 用户反馈驱动修复（3 项）

| # | 问题 | 修复位置 | 修复内容 |
|---|---|---|---|
| F9 | 事务解法应优先拆 Bean | 06/09/SKILL.md | 解法重排：拆 Bean（推荐）> @Lazy（次选）> AopContext（不推荐） |
| F10 | SpringDoc 应区分带 UI / 纯 JSON 两版本 | 11-springdoc.md | 补 `-webmvc-ui` vs `-webmvc-api` 选择表 + 适用场景 |
| F11 | 校验应支持 properties 插值 + 组合注解 | 04-validation.md | 补 `ValidationMessages.properties` 插值 + 组合注解（`@Constraint(validatedBy={})`）+ `@ReportAsSingleViolation` |
| F12 | fixture 全局异常漏 `ConstraintViolationException`（最终回归发现） | eval fixture GlobalExceptionHandler | 补 `@ExceptionHandler(ConstraintViolationException.class)` 返回 400；技能文档 05 已正确覆盖，属 fixture 实现遗漏 |

### 盲评驱动修复（6 项）

| # | 问题 | 来源 | 修复位置 | 修复内容 |
|---|---|---|---|---|
| F2 | `ListenableFuture` 3.x 已 `@Deprecated` 却标 ✓ | B | 07-async-schedule.md | 删除 `ListenableFuture` 示例，注明推荐 `CompletableFuture` |
| F3 | 字段注入缺点「允许循环依赖」与强约束 8 矛盾 | B | 09-autowiring.md 第一节表 + 循环依赖容忍表 | 删「允许循环依赖」，补「2.6+ 全禁」 |
| F4 | 决策路由把 `@TransactionalEventListener` 误指 06 | B | SKILL.md 决策路由 | 从 06 行删 `@TransactionalEventListener`（08 已覆盖） |
| F5 | `@ConditionalOnBean` 措辞「单例实例化期」不准 | B | SKILL.md 决策路由 | 改「Bean 定义注册阶段」 |
| F6 | 「web 不传递校验依赖」措辞模糊 | B | 04-validation.md | 改「2.4 起拆分，2.x/3.x 均须显式引入」 |
| F7 | T4 排障漏「缺 validation 依赖」 | A | 12-pitfalls.md 第五节 | 补首行「所有校验注解不触发 → 缺 starter」 |

### 版本号修复（1 项，用户反馈）

| # | 问题 | 修复 |
|---|---|---|
| F8 | SKILL.md 推荐 3.3/3.4（滞后） | 改 3.5.x（3.x 末线，2025-05 GA） |

## 五、仲裁：12-pitfalls.md 是否冗余（A/B 分歧点）

**分歧**：
- 盲评 A：12-pitfalls section 3-10 是专篇的表格化重排，建议改纯跳转链接（D6 给 8.1）
- 盲评 B：12-pitfalls 与各专篇 80% 重叠（D6 给 9.1）
- 审计 agent（冗余清理阶段）：12-pitfalls 是「横向聚合指针，结构正确，几乎无冗余」

**仲裁结论：保留 12-pitfalls 结构，不做大改**。

**理由**：
1. **排障视角 ≠ 机制讲解视角**。专篇按"机制 → 坑 → 解法"纵向展开；12-pitfalls 按"症状 → 根因 → 解法"横向聚合。agent 排障时查一个表比翻 6 个专篇快——这是独特价值。
2. **判据验证**：删掉 12-pitfalls，agent 在 T2（事务不生效）、T7（配置读不到）这种"我遇到 X 症状"的排障场景下，需要读 2-3 个专篇才能定位——产出会更差。满足"必须保留"判据。
3. **A/B 的扣分合理但不致命**：重复确实存在（D6 是最低分维度），但这是"排障速查表"与"机制详解"的**必要冗余**（类似 API 文档与教程的关系）。已通过补「缺依赖」排障行（F7）提升其独立价值。

**后续优化方向**（未做，记档）：可进一步压缩 12-pitfalls 各排障表的解释列，只留"症状 → 根因关键词 → 指向专篇章节号"，把详细解法留在专篇。但当前 2391 行的体量已在合理范围（sa-token 14 refs、mybatis-plus 13 refs 同量级），不强求。

## 六、结论

**spring-boot-dev v1.0.0 通过达尔文评估**。

- **仲裁总分 91.7 / 100**（A 91.1 / B 92.2，一致性良好）
- **实跑 8/8 通过**（编译 + 启动 + API）
- **修复 8 项**（1 实跑驱动 + 6 盲评驱动 + 1 版本号），其中 F1（@Lazy Lombok bug）是关键——盲评未发现，实跑揪出
- **棘轮**：所有修复已回填到 `skills/spring-boot-dev/`，镜像已同步

### 与兄弟技能对比

| 技能 | 达尔文得分 | 实跑 | 关键产出 |
|---|---|---|---|
| java-coding-guide-pro v3.4.0 | 96.7 / 94.5 | 37/37 | 修 CollUtil.partition bug（实跑发现） |
| java-coding-quality | 95.5 | - | PMD7 规则集 |
| **spring-boot-dev v1.0.0** | **91.7** | **8/8** | **修 @Lazy+Lombok bug（实跑发现）+ ListenableFuture 废弃 + 字段注入矛盾** |

首版 91.7 略低于两个 v3+ 技能（它们经过多轮优化），但考虑到：
- 这是 v1.0.0 首版（它们是 v3+）
- 实跑揪出了盲评漏掉的代码级 bug（最有价值的发现）
- D6 信息密度是主要拉分项（瘦身后仍需后续优化）

**结论：达标，可进入发布流程（待用户确认）。**
