# spring-boot-dev 真实场景触发测试

> 模拟一个真实 agent 在收到 5 个用户 prompt 时，从已安装的 6 个 Java 后端技能中加载哪些。
> 重点观测：**spring-boot-dev 是否被加载**，以及 T5 反向测试中它是否正确"让位"给 sa-token-dev。

## 技能清单（仅 name + description 可见）

| 技能 | 核心领域 | 让位条款（主动让位给） |
|---|---|---|
| spring-boot-dev | 三层架构 / 注解陷阱 / 参数校验 / 事务 / 异步 / 定时 / 配置 | ORM CRUD·分页·Mapper→mybatis-plus-dev；认证·权限·token·SSO→sa-token-dev；Java 语言层→java-coding-guide-pro；单测→java-unit-test |
| java-coding-guide-pro | 判空/集合/并发/日期/IO/异常日志/金额（Java 语言层，全量 catch-all） | 不适用：业务架构/选型/DDL/算法/前端 |
| mybatis-plus-dev | CRUD / 分页 / 条件查询 / 实体映射 / 批量 | 不适用：JPA/Hibernate 项目 |
| sa-token-dev | 登录/认证/鉴权/权限/token/会话/SSO/OAuth2/JWT | （未声明让位） |
| java-unit-test | 单元测试规范 | （未声明让位） |
| java-coding-quality | 编写后/提交前的质量门禁/静态扫描/安全扫描 | （未声明让位） |

---

## T1：写订单查询接口

> 帮我写一个订单查询接口：GET /api/orders，按状态和日期范围筛选，结果分页。项目用 MyBatis-Plus，数据库是 MySQL

### 会加载的技能（按优先级）

1. **mybatis-plus-dev（主）** — 分页查询 + 条件查询是它的核心领域；用户显式声明"项目用 MyBatis-Plus"；spring-boot-dev 的让位条款明确把"ORM CRUD / 分页 / Mapper / 实体映射"让给它。
2. **spring-boot-dev（辅助）** — "写接口 / 写 Controller"是它的直接触发词（description 原文："无论用户是否提到 Spring Boot（写接口 / 写 Controller…）"）。请求字面是"写一个订单查询接口：GET /api/orders"，Controller 骨架 + 参数绑定 + 日期范围参数校验仍归它。
3. **java-coding-guide-pro（边缘辅助）** — 日期范围参数的解析/格式化写法（DateTimeFormatter）。

### spring-boot-dev 是否被加载

**是（辅助）。** 让位条款只覆盖"持久层（ORM CRUD/分页/Mapper）"，不覆盖 Controller 层与参数校验。一个完整的"写接口"垂直切片里，spring-boot-dev 负责 Controller/参数校验那一刀，mybatis-plus-dev 负责 Mapper/分页那一刀，二者共存而非互斥。

### 理由

请求同时命中两条触发链：写接口/Controller（spring-boot-dev）+ 分页/条件查询/项目声明用 MyBatis-Plus（mybatis-plus-dev）；让位仅在持久层生效，故 spring-boot-dev 不被压制。

---

## T2：日期参数校验

> 我的接口接收日期参数（startDate / endDate），用户传了乱七八糟的格式。怎么校验让参数格式统一？

### 会加载的技能（按优先级）

1. **spring-boot-dev（主）** — "参数校验 / validation"是它的核心触发词；次级信号含"@Validated 分组校验不触发"。用户问的是"怎么校验让参数格式统一"，这是参数校验问题（自定义校验注解 / @DateTimeFormat / @Validated）。
2. **java-coding-guide-pro（辅助）** — 日期格式化/解析的具体写法（DateTimeFormatter vs 反模式 SimpleDateFormat）。

### spring-boot-dev 是否被加载

**是（主）。** 这是 spring-boot-dev 描述里点名的高优先级场景，无让位干扰（日期参数校验不属于 ORM/认证/语言层 catch-all 的任何一个让位目标）。

### 理由

关键词"校验"+"接口参数"直击 spring-boot-dev 的 validation 领域；java-coding-guide-pro 只在"日期格式化底层写法"上做辅助。

---

## T3：事务方法里调另一个方法，事务没生效

> OrderService.createOrder 标了 @Transactional，里面调 this.recordLog()（也标了 @Transactional），recordLog 失败时 createOrder 没回滚，为什么？

### 会加载的技能（按优先级）

1. **spring-boot-dev（主，唯一相关）** — 教科书级触发。

### spring-boot-dev 是否被加载

**是（主，强触发）。** description 明确列出三条命中：
- 主触发词：`@Transactional / 事务失效 / 事务不生效 / 回滚`
- 次级触发信号：`@Transactional 自调用失效`（精确命中——this.recordLog() 就是自调用）
- 次级触发信号：`@Transactional 标在 private 方法`（相关家族问题）

这是 spring-boot-dev 全部 5 个 prompt 里匹配度最高、最无歧义的一个。

### 理由

问题描述与"@Transactional 自调用失效"次级信号几乎一字不差；这是 Spring AOP 代理机制问题，纯框架层，java-coding-guide-pro（Java 语言层）不介入。

---

## T4：配置改了不生效

> application.yml 把 server.port 改成 9090，启动后还是 8080，配置没生效。

### 会加载的技能（按优先级）

1. **spring-boot-dev（主，唯一相关）** — description 主触发词含"配置读不到 / 配置不生效"，次级信号含"@Value 配置读不到"。application.yml + server.port 是 Spring Boot 配置体系的典型物。

### spring-boot-dev 是否被加载

**是（主）。** 典型 Spring Boot 配置加载问题（profile 覆盖 / 多 yml / 打包旧配置 / 启动参数覆盖），属 spring-boot-dev 的"配置 / 自动装配"领域。

### 理由

"配置不生效"+ application.yml 直接命中；无让位竞争。

---

## T5：用户登录后存信息（反向测试）

> 用户登录后我想把用户信息存起来，下次请求能拿到当前登录用户。用 Spring Boot 怎么实现？

### 会加载的技能（按优先级）

1. **sa-token-dev（主）** — 命中核心触发词："登录 / 会话管理 / 当前登录用户 / token"。用户要的正是"登录后存用户信息 + 后续请求取回当前用户"，即会话/认证状态保持，是 sa-token-dev 的看家场景。
2. **spring-boot-dev（应让位 / 边缘或不加载）** — 见下方专门判断。

### spring-boot-dev 是否被加载

**否（让位）/ 边缘。** 见下。

### 对 T5 的特别判断：spring-boot-dev 该不该让位？让位成功吗？

**该让位。** spring-boot-dev 的让位条款原文："认证 / 权限 / token / SSO → sa-token-dev"。用户的诉求（登录后存信息、下次请求拿当前用户）= 会话状态保持 = 认证/会话领域，落进让位范围。

**让位应成功。** sa-token-dev 的关键词命中度极高："登录""当前登录用户""会话管理"三连击；spring-boot-dev 这边唯一的"命中"是用户口头的"用 Spring Boot 怎么实现"——但那是项目运行环境说明，不是 Spring Boot 框架机制问题（不涉及注解陷阱/三层架构/参数校验/事务/配置等 spring-boot-dev 的真正领域）。一个遵循 description 让位规则的 agent 应当：主答 sa-token-dev（StpUtil.login / StpUtil.getSession / StpUtil.getLoginId），spring-boot-dev 退到背景板。

**越界风险（反向测试要抓的 bug）：** 如果 agent 忽略让位条款、被"用 Spring Boot 怎么实现"诱导，用裸 Spring Boot 原语作答（HttpSession、ThreadLocal + HandlerInterceptor、@RequestAttribute、Spring Security Context）——那就是 spring-boot-dev **越界**，抢了 sa-token-dev 的活。这正是反向测试设计的初衷：description 里写了让位规则，但用户句式（"用 Spring Boot 怎么实现"）是一个强诱导陷阱。

**预判：** 鉴于让位条款写得明确（"认证/权限/token/SSO → sa-token-dev"），规范的 agent 应让位成功；但陷阱句式 + sa-token 是否在项目依赖里未被声明，会让弱 agent 回退到 Spring Boot 原语（越界）。

### 理由

会话/认证是 sa-token-dev 核心；spring-boot-dev 让位条款覆盖此场景，应退居二线或不加载。

---

## 汇总

### spring-boot-dev 在 5 个 prompt 上的命中率

| Prompt | 应加载? | 实际预测加载 | 角色 | 命中? |
|---|---|---|---|---|
| T1 订单查询接口 | 是 | 是 | 辅助（mybatis-plus-dev 主） | ✓ |
| T2 日期参数校验 | 是 | 是 | 主 | ✓ |
| T3 事务自调用失效 | 是 | 是 | 主（强） | ✓ |
| T4 配置不生效 | 是 | 是 | 主 | ✓ |
| T5 登录后存用户信息 | 否（应让位） | 否（让位 sa-token-dev） | — | ✓（正确让位） |

**正向命中率（T1–T4，应触发场景）：4/4 = 100%。**
**反向正确率（T5，应让位场景）：1/1 = 100%（预判让位成功，前提是 agent 遵守让位条款）。**

### 是否有漏触发 / description 缺词分析

**无漏触发。** T1–T4 全部正确加载。逐项核对 description 覆盖：

- T1：写接口/写 Controller ✓、参数校验 ✓（日期范围）；分页让位给 mybatis-plus-dev ✓ —— 覆盖完整。
- T2：参数校验/validation/@Validated ✓ —— 覆盖完整。唯一可补强的词：**"@DateTimeFormat"** 与 **"自定义校验注解 / ConstraintValidator"** 这两个具体技术词没在 description 里出现，agent 需要从"参数校验"自行泛化。但"参数校验 / validation"已足够触发，不算漏。
- T3：@Transactional / 事务失效 / 回滚 ✓，且次级信号"@Transactional 自调用失效"几乎逐字命中 —— 覆盖最完整。
- T4：配置读不到 / 配置不生效 ✓ —— 覆盖完整。可补强词：**"application.yml / application.properties / profile / 启动参数覆盖 / jar 包内配置"**，但"配置不生效"已足够。

**潜在边缘风险（非漏触发，是泛化风险）：** description 里 validation 相关只写到"@Validated 分组校验不触发"，对"日期格式校验""自定义注解校验"这类具体子场景没列词，弱 agent 可能仅在用户说出"validation"原文时才触发。T2 用户说的是"校验"（中文），靠的是"参数校验"同义命中——目前 description 里有"参数校验"，安全。

### T5 反向测试结论：会不会越界？

**预判不会越界（前提：agent 遵守让位条款）。** 理由：

1. spring-boot-dev 让位条款明确写了"认证 / 权限 / token / SSO → sa-token-dev"，覆盖面足够（"认证"一词兜住了"登录后存用户信息"）。
2. sa-token-dev 对"登录""会话管理""当前登录用户"的命中度远高于 spring-boot-dev 对"用 Spring Boot 怎么实现"的命中度（后者只是环境说明，不是领域词）。
3. 信号强度对比：sa-token-dev 命中 3 个领域词 vs spring-boot-dev 命中 0 个领域词（仅 1 个环境词）。

**越界会发生的条件（失败模式）：**
- agent 不读让位条款，只做关键词加权 → "Spring Boot"字面命中 spring-boot-dev → 用 HttpSession/ThreadLocal 作答 → 越界。
- 项目上下文里没声明 sa-token 依赖、也没出现 StpUtil → agent 不敢假设 sa-token 存在 → 回退到 Spring Boot 原语 → 越界。这是最现实的失败路径：**用户问"用 Spring Boot 怎么实现"，可能就是没用 sa-token**，此时 spring-boot-dev 接答反而合理——但 description 把"认证"整体让给了 sa-token-dev，没留"项目无 sa-token 时回退 spring-boot-dev"的口子。这是 description 的一个**潜在过度让位**：让位条款无条件化，没有"仅当项目已引入 sa-token 时才让位"的前置条件。

**改进建议（针对 description）：** 在让位条款里加条件化边界，例如：
> 认证/权限/token/SSO → sa-token-dev（仅当项目依赖含 sa-token 或代码出现 StpUtil 时；否则由 spring-boot-dev 提供基于 HttpSession/ThreadLocal 的最小可用方案）。

这样既能避免 T5 的越界（项目有 sa-token 时让位），又能避免"项目没 sa-token 但 description 把认证整体踢出 spring-boot-dev"导致的真空。

---

## 一句话总结

spring-boot-dev 的 description 在 4 个正向场景（写接口/参数校验/事务/配置）上触发精准、无漏词；在 1 个反向场景（登录会话）上让位规则方向正确，但让位条款**无条件化**是唯一隐患——项目无 sa-token 时可能制造回答真空，建议给让位加"依赖存在"前置条件。
