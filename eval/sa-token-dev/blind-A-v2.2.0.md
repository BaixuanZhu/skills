# Sa-Token 开发助手 Skill 盲评报告（盲评员 A）

> 本报告由**盲评员 A**（独立评审员）撰写，未参与该 Skill 内容包的任何编写工作。
>
> - **评审对象**：`I:\GitDownload\skills\skills\sa-token-dev\`（SKILL.md + references/ 下 14 个文件：01-setup ~ 14-plugin）
> - **测试输入**：`I:\GitDownload\skills\eval\sa-token-dev\test-prompts-v2.2.0.json`（12 个真实开发场景 T1~T12）
> - **版本基准**：内容包声明跟版 Sa-Token 1.46.0（SKILL.md:23），推荐 1.46.0+，1.40.x 及以上全线适用
> - **评审日期**：2026-08-21

---

## 一、总体结论

| 指标 | 结果 |
|---|---|
| **12 场景总分均值** | **92.8 / 100** |
| **9 维度合计** | **89.5 / 100** |
| 判定 | 高质量可用。结构完备、防错意识极强、1.46.0 跟版到位；主要缺陷集中在个别高级示例的 API 签名（见 Top 问题 #1） |

整体评价：这是一个「决策路由表 + 14 个分域 reference + 28 条 antipattern + 12 条核心强约束 + 6 个关键决策检查点」的多层结构 skill。相比同类编码助手，其突出优点有三：(1) 依赖探测与激活分支（SKILL.md:42-50）做对了触发边界；(2) 以 `10-antipattern.md` 形式沉淀「AI 常见错误」是实际编码辅助价值最高的设计；(3) 对 1.46.0 的三项破坏性变更（`isDisabled` 3 参 / `allowLoginIdColon` / JWT `extraData` 保留字段）在 SKILL.md:145、09-pitfalls §10、11-advanced §3.5、14-plugin §1.7 四处形成闭环，直接命中 T11 场景。

主要短板：`11-advanced.md` §6「不同体系不同配置」示例存在一处**确定性的编译错误**（`StpKit.USER.setStpLogic(...)` 调用不存在的 `StpLogic#setStpLogic` 方法），该段落恰是 T8 场景的答案路径。

---

## 二、逐场景评分表

| 场景 | 内容 | 得分 |
|---|---|---|
| T1 | 登录认证基础（SB3 + Maven 依赖/最小配置/登录登出） | 93 |
| T2 | 注解鉴权 + 自定义 StpInterface | 93 |
| T3 | 前后端分离（小程序 header 传 token） | 95 |
| T4 | Redis 集成 + 自定义对象存 Session（序列化安全） | 96 |
| T5 | SSO 模式二（前端异域 + 后端同 Redis） | 94 |
| T6 | OAuth2 授权码 + 数据库加载 Client | 92 |
| T7 | JWT 无状态（不依赖 Redis、自包含 token、踢人？） | 95 |
| T8 | 多账号体系（用户端/管理员端两套 + 不同 timeout） | 82 |
| T9 | 封禁/踢下线/DB 封禁数据/二级认证 | 93 |
| T10 | 微服务网关统一鉴权 + Same-Token | 94 |
| T11 | 1.45.0 → 1.46.0 升级适配（isDisabled 签名 + loginId 冒号） | 95 |
| T12 | 多模块版本统一管理 | 92 |
| **均值** | | **92.8** |

---

## 三、逐场景详细评估

### T1 登录认证基础 —— 93/100

- **依据**：路由表（SKILL.md:70）将「依赖、starter 选择、yml 配置、最小示例」指向 `01-setup.md`。01-setup §1 明确 SB3 → `sa-token-spring-boot3-starter`（01-setup.md:31），§2 给出零配置 yml，§3 给出最小登录示例；`02-login-auth.md` §1/§5 给出 `StpUtil.login(id)` 与 `StpUtil.logout()` 示例，满足"登录/登出"要求。
- **加分**：01-setup §0 提供 `${sa-token.version}` 统一管理，与 T12 呼应；SKILL.md:100 强约束 #1 提醒注解需注册拦截器。
- **扣分点**：01-setup §1 默认代码块展示的是 SB2 坐标 `sa-token-spring-boot-starter`，仅在下方用一行注释提示 SB3 应替换为 `sa-token-spring-boot3-starter`（01-setup.md:31）。对"SB3 项目"场景，Agent 需自行替换坐标；有轻微误抄风险，建议默认块直接按 SB3 或做成版本选择表。

### T2 注解鉴权 + StpInterface —— 93/100

- **依据**：路由表（SKILL.md:73）指向 `04-annotation.md`：§1 强调"必须先注册 SaInterceptor 注解才生效"并给出完整配置类（04-annotation.md:18-27），§2 给出 `@SaCheckPermission("user-add")` / `@SaCheckRole("super-admin")` 用法；`03-permission.md` §1 给出带 `@Component` 的 `StpInterfaceImpl` 完整实现（03-permission.md:7-31）。
- **加分**：10-antipattern §1（未注册拦截器）与 §24（StpInterface 未加 @Component）为最高频错误的双保险；04-annotation §7 提供注解 vs 路由选型，可引导 Agent 不盲目堆注解。
- **扣分点**：03-permission §1 示例只实现 `getPermissionList` / `getRoleList` 两方法。若 1.46.0 的 `StpInterface.isDisabled` 为抽象方法（SKILL.md 自身将"升级编译失败"归因于实现类需改 3 参签名），则该示例在 1.46.0 下无法编译（未实现抽象方法）。属需与官方源码核对的隐性风险，skill 内未作说明。

### T3 前后端分离（小程序 header 传 token）—— 95/100

- **依据**：路由表（SKILL.md:76）指向 `07-redis-frontsep.md`：§二/1 后端返回 `SaTokenInfo`（07-redis-frontsep.md:67-74），§二/2 给出 uni-app 前端塞 header 的完整示例，并强调"参数名即 tokenName（默认 satoken）"、封装进统一请求函数（07-redis-frontsep.md:90-98）；`02-login-auth.md` §登录流程「前后端分离（Header 模式）」给出带 `checkDisable` 的完整 doLogin（02-login-auth.md:105-119）。
- **加分**：10-antipattern §3 专门纠"前后端分离未返回 tokenValue"这一 AI 高频错误；SKILL.md C3 检查点要求先确认 Cookie/Header 模式，避免擅自决策。
- **扣分点**：无实质问题。小程序场景下 skill 用 uni-app 示例是最贴近的写法；若 Agent 照抄需自行换成小程序原生 API，属可接受的示例边界。

### T4 Redis 集成 + 自定义对象存 Session —— 96/100

- **依据**：路由表（SKILL.md:76）警告列直接点出"自定义类型存 Session 需注册 `SaJsonStrategy` 白名单（v1.46.0+，防 RCE）"；`07-redis-frontsep.md` §一给出 `sa-token-redis-template` + `commons-pool2` 依赖、SB3 `spring.data.redis` 前缀提醒（07-redis-frontsep.md:46）、以及 **1.46.0 Jackson 多态反序列化 RCE 修复与 `SaJsonStrategy.instance.registerAllowType(SysUser.class)` 白名单示例**（07-redis-frontsep.md:52-57）；`06-session.md` §4 提供 Session 存取与 lazy 读取。
- **加分**：该场景是 1.46.0 跟版的核心测试点，skill 在路由表、reference、最佳实践三层都覆盖了白名单机制，且提示了"白名单首次构建 JSON 插件时初始化，之后不可再注册"这一极易踩中的时序陷阱。
- **扣分点**：`registerAllowType` 的具体 API 与官方 1.46.0 源码的一致性无法离线核实（软性提示）；07 §一/2 主示例 Redis 配置用 SB2 前缀 `spring.redis`（见 Top 问题 #5）。

### T5 SSO 模式二（前端异域 + 后端同 Redis）—— 94/100

- **依据**：`12-sso-oauth2.md` §2 三种模式选型表明确"前端不同域 + 后端同 Redis → **模式二**"（12-sso-oauth2.md:14），选型规则给出了判定逻辑；§6 给出模式二 Client 的 Controller（`SaSsoClientProcessor.instance.dister()`）、配置（`secret-key` 与 Server 一致、`alone-redis` 必须与 Server 同 Redis）与完整 ticket 流程（12-sso-oauth2.md:141-180）；§4 给出 Server 端 `SaSsoServerProcessor` + yml `sso-server.clients` 配置。
- **加分**：SKILL.md C2 检查点要求在动手前确认"前端是否同域 + 后端是否同 Redis"，本场景恰好命中且 skill 的判定规则直接给出答案；12-sso-oauth2 最佳实践强调 `allow-url` 生产必须配详细地址（12-sso-oauth2.md:424）。
- **扣分点**：模式二示例中 Client 的 `server-url`、`alone-redis` 与 secret-key 需用户自行替换为实际域名；Server 端 `allow-url: "*"` 在生产安全提示上已处理。整体完整，扣分仅为示例配置占位符场景。

### T6 OAuth2 授权码 + 数据库加载 Client —— 92/100

- **依据**：`12-sso-oauth2.md` §13 给出 `SaOAuth2ServerConfig.addClient(new SaClientModel()...)` 代码声明与 YAML 声明两种方式（12-sso-oauth2.md:318-345），§14 给出授权码模式 `/oauth2/authorize` 与 `/oauth2/token` 完整流程，§15 给出"生产环境用 `SaOAuth2DataLoader` 从数据库加载 Client 信息，不要硬编码"的实现骨架（12-sso-oauth2.md:371-387）——直接回答"客户端配置在哪声明"。
- **加分**：三种声明位置（代码/YAML/DB loader）齐备，最佳实践 #6 明确生产应走数据库模式；SKILL.md 路由表与 C2 检查点覆盖。
- **扣分点**：① 授权码流程仅给 GET 示例，未提示 OAuth2 规范要求 token 端点用 POST（与官方文档一致则无碍，属低置信度疑点）；② `addContractScopes` / `addAllowGrantTypes` 等链式 API 与官方 1.46.0 源码的一致性无法离线核对（软性提示）。

### T7 JWT 无状态（不依赖 Redis、自包含 token、踢人？）—— 95/100

- **依据**：SKILL.md 核心强约束 #12 明确"无状态场景必须 JWT（`StpLogicJwtForStateless`，不要 Redis，不支持踢人/active-timeout）"（SKILL.md:111）；`14-plugin.md` §1 三种模式对比表给出 Stateless 踢人/顶人/Session/active-timeout 全 ❌（14-plugin.md:45-55），并强调"JWT 只是 token 风格，不等于无状态"（14-plugin.md:7）；10-antipattern §13 专门纠"Stateless 误用——选了 Stateless 又需要踢人/Session"。
- **加分**：SKILL.md C1 检查点强制 Agent 先向用户确认"是否要无状态 / 是否要 JWT 风格"，默认推荐"有状态 + simple-uuid token"，杜绝了 AI 默认上 JWT 的通病；对"踢人还支持吗"给出明确答案——不支持。
- **扣分点**：14-plugin §1.4 对比表中 Mixin 行 `active-timeout ✅` 与官方文档"续期 token ❌"表述的对应关系存疑（低置信度，见 Top 问题 #6）。

### T8 多账号体系（两套独立登录体系 + 不同 timeout）—— 82/100（全场景最低）

- **依据**：`11-advanced.md` §6「多账号认证」给出推荐方案——StpKit 门面模式（`StpKit.DEFAULT/ADMIN/USER` 三个 `StpLogic`，11-advanced.md:259-275），并给出「不同体系不同配置」示例（11-advanced.md:311-325）。
- **加分**：方案选型正确（≥2 套体系 → StpKit）；SKILL.md C6 检查点要求确认体系数量与各自配置。
- **扣分点（关键）**：「不同体系不同配置」示例存在**确定性编译错误**：
  ```java
  StpKit.USER.setStpLogic(new StpLogic("user").setConfig(userConfig));  // 11-advanced.md:324
  ```
  ① `StpKit.USER` 是 `StpLogic` 实例（且 StpKit 字段定义为 `static final`，11-advanced.md:262-266），`StpLogic` 类上**不存在 `setStpLogic` 方法**（该方法是 `StpUtil` 的静态方法），必然编译失败；② 即便外层正确，`new StpLogic("user").setConfig(...)` 的链式返回依赖 `setConfig` 返回 `StpLogic`，官方 API 是否流畅返回未确认。官方正确做法应是 `SaManager.setConfig(StpKit.USER, userConfig)`。**该示例直接位于 T8 的答案路径上，若 Agent 照抄将产出不可编译代码**——这是本次评审在 12 个场景中发现的唯一"能误导产出坏代码"的实质性缺陷。

### T9 封禁/踢下线/DB 封禁数据/二级认证 —— 93/100

- **依据**：`11-advanced.md` §3.1「先踢下线再封禁」最佳实践 + v1.31.0+ `login()` 不再自动校验封禁（11-advanced.md:103）；§3.5 数据库持久化给出 1.46.0 三参签名 `isDisabled(Object loginId, String service, String loginType)` 返回 `SaDisableWrapperInfo` 的完整示例（11-advanced.md:141-153），正好命中"封禁信息从数据库读取而非 Redis"；§4 二级认证给出 `openSafe`/`checkSafe`/`isSafe` API 与完整流程（11-advanced.md:168-216）。
- **加分**：三参签名示例同时带 `createDisabled` / `createNotDisabled` / `createNotDisabled(86400)`（带缓存）三种返回，信息完整；10-antipattern §8 强化"先 kickout 再 disable"。
- **扣分点**：无实质问题。`SaDisableWrapperInfo` 工厂方法命名与官方源码一致性属软性核对项。

### T10 微服务网关统一鉴权 + Same-Token —— 94/100

- **依据**：`13-micro-service.md` §1 依赖引入规则明确"网关用 Reactor、子服务用 Servlet，不要在父 pom 统一引入"（13-micro-service.md:5-15），§3.3 给出 `SaReactorFilter` 全局过滤器完整示例，§4 给出 Same-Token 两环节：网关 GlobalFilter 转发携带 `SaSameUtil.SAME_TOKEN` + 子服务 `SaSameUtil.checkCurrentRequestToken()` 校验（13-micro-service.md:145-174），以及 Feign 调用传 Same-Token（13-micro-service.md:180-204）。
- **加分**：10-antipattern §27 纠"网关用 Servlet 依赖"；§22 纠"多服务同时刷新 Same-Token"，给出集中定时刷新最佳实践（13-micro-service.md:221-227）；SKILL.md C5 检查点确认 Redis 有状态方案。
- **扣分点**：无实质问题。示例中的 `ServerWebExchange.mutate()` 链式写法与 SpringCloud Gateway 现行 API 一致。

### T11 1.45.0 → 1.46.0 升级适配 —— 95/100

- **依据**：本场景是 1.46.0 跟版的直接测试点，skill 三处闭环覆盖：SKILL.md「版本注意」明确"`StpInterface.isDisabled` 改 3 参（`11-advanced.md` §3.5）；`allowLoginIdColon` 默认禁 loginId 冒号（`09-pitfalls.md` §10）"（SKILL.md:145）；`09-pitfalls.md` §10 破坏性更新表逐条列出现象与处理（09-pitfalls.md:110-114），并详解 `allowLoginIdColon` 配置（09-pitfalls.md:116-124）；`11-advanced.md` §3.5 给出三参实现示例。
- **加分**：对"登录突然报 loginId 含冒号"不仅给配置开关，还给出建议"新项目不要用含冒号的 loginId，改用下划线"（09-pitfalls.md:124）；`allowLoginIdColon: true` 的 yml 片段直接可抄。
- **扣分点**：无实质问题。仅提示 Agent 需同时检查用户是否真的需要"存量项目含冒号 loginId"这一前提。

### T12 多模块版本统一管理 —— 92/100

- **依据**：`01-setup.md` §0「版本统一管理（升级只改一处）」给出 Maven `${sa-token.version}` 占位符 + 父 pom `<properties>` 方案与 Gradle `ext` 方案（01-setup.md:5-17），并声明"各 reference 的依赖示例均用 `${sa-token.version}` 占位符"。
- **加分**：验证该声明属实——07/12/13/14 各 reference 的依赖示例均使用 `${sa-token.version}`，skill 内部一致；SSO/Redis 插件版本同管理。
- **扣分点**：`01-setup.md:11` 注释要求"升级时与 SKILL.md 声明同步"——即版本值在 **reference 与 SKILL.md 两处重复声明**，未真正实现"只改一处"（SKILL.md:23 为"推荐 1.46.0+"的散文式声明，非可解析版本号，故尚可接受；但若未来 SKILL.md 也写死版本号则会出现双源漂移）。属轻微设计瑕疵。

---

## 四、9 维度均分表

| 维度 | 满分 | 得分 | 评分依据摘要 |
|---|---|---|---|
| D1 触发精度 | 12 | **11** | description 关键词覆盖登录/权限/会话/SSO/OAuth2/JWT/多账号/微服务等全量信号，且"无论用户是否提到 Sa-Token"；负向边界清晰（Spring Security/Shiro 不适用、非 Java 不适用、纯 JWT 自实现不适用）；「第 0 步依赖探测与激活分支」（SKILL.md:42-50）把"无框架→主动询问是否引入"做成了标准动作，误触发有兜底。扣 1 分：description 偏长，且触发词未含"注册"以外的低频词（如"单点注销""应用授权"），嵌入式匹配对长描述有截断风险。 |
| D2 可发现性 | 12 | **11** | 「决策路由表」（SKILL.md:68-83）一行一域、关键词→文件→同时警告三列，是全包导航主干；「核心强约束」12 条前置、「关键决策检查点」C1~C6、「使用流程」7 步串联。14 个 reference 文件名按主题编号，01 为 setup 入口。扣 1 分：路由表警告列信息密度高（如 11 行同时含 8 个要点），Agent 需二次定位；无"reference 速查索引"式的独立总览。 |
| D3 覆盖完整 | 12 | **10.5** | 登录/登出/会话/权限/注解/路由/Redis/前后端分离/SSO 三模式/OAuth2 四模式/JWT 三模式/多账号/封禁/二级认证/记住我/微服务/Same-Token/API-Key/API 签名/临时 Token/SpEL 等全覆盖，12 个测试场景全部可路由到具体章节。扣 1.5 分：① OAuth2 客户端凭证/隐藏式仅一句带过，无单独示例；② `isDisabled` 数据库封禁模式仅 11-advanced §3.5 一处，路由表未将该场景显式列出行；③ 多账号体系「不同配置」段落有缺陷（见 T8）。 |
| D4 可执行性 | 12 | **9.5** | 绝大多数示例签名正确、配置完整（SB2/3/4 坐标、`spring.data.redis` 前缀、`commons-pool2`、`setError`、`@EnableWebMvc` 等生产细节都齐）。扣 2.5 分：① **确定性错误**——`11-advanced.md:324` `StpKit.USER.setStpLogic(...)` 调用不存在的 `StpLogic#setStpLogic`，该行是 T8 唯一路径；② 若干 API 与官方源码一致性无法离线核实（`SaJsonStrategy.registerAllowType`、`SaCorsHandleFunction`、`SaDisableWrapperInfo` 工厂方法、`StpLogic.setConfig` 链式返回、`SaSession.getList/getSet/getMap` 精确签名、`StpInterface.isDisabled` 参数顺序），建议逐项对照官方源码；③ 03-permission §1 示例未实现 `isDisabled` 的潜在编译问题（见 T2）。 |
| D5 防错/陷阱 | 12 | **11.5** | 全包最强维度：`09-pitfalls.md`（NotLoginException 7 场景值、异常细分码、CORS、反代 uri、过滤器异常）+ `10-antipattern.md` **28 条** AI 常见错误（每条均"❌→✅→为什么"结构）+ SKILL.md:90-96「主动行为触发」护栏表 + 12 条核心强约束 + 版本破坏性更新表。1.46.0 三项破坏性变更全部预警。扣 0.5 分：09-pitfalls §2 异常细分状态码（11011~11016 / 11041 / 11051 / 11071）未给出核对依据，数值需对照官方源码确认。 |
| D6 信息密度 | 12 | **10** | 无大段废话，代码示例均有注释，每文件以"核心一句话"开头。扣 2 分（轻微）：① CORS 处理在 09-pitfalls §6 与 10-antipattern §17 双份且内容几乎一致；② "过滤器异常不进 @ExceptionHandler"在 09 §8、antipattern §12、11-advanced §11 出现三遍；③ "封禁需先踢下线"在强约束 #7、08-api、antipattern §8、11-advanced §3 出现四遍；④ `allow-url` 安全警告在 SKILL.md 护栏表、12-sso-oauth2 §4、最佳实践 #2 三处。属强化性重复、删任何一份不影响正确性，但存在轻度冗余。 |
| D7 内部导航 | 12 | **11.5** | ① 14 个 reference **全部**被 SKILL.md 决策路由表覆盖（逐行核实，无孤儿文件）；② 交叉引用全部有效——抽查 04→14 §4/§7、05→antipattern §15/§16、06→antipattern §2、07→01 §0/14 §8、09→11 §3.5、13→14 §1/§6、12→09 §6 等，章节号均准确；③ 编号引用（§0/§1.4/§3.5/§8 等）与实际文件章节对应无误。扣 0.5 分：SKILL.md:83 与 :80 两行"同时警告"列信息过载（单行 8~10 个要点），Agent 解析长单元格有遗漏风险。 |
| D8 范围明确 | 12 | **11** | 适用/不适用边界在 frontmatter、路由表、第 0 步三处一致："已使用 Spring Security / Shiro 不适用（不建议迁移）""非 Java 不适用""纯 JWT 自实现不适用"；依赖缺失时"主动询问是否引入"而非硬编码；「不适用→建议退出」有明确检查点（SKILL.md:64）。扣 1 分：对"项目尚无认证框架且用户不想引入"的分支，退出信号只写"告知用户并建议退出"，未给 Agent 一条可复用的"最小引导话术模板"。 |
| D9 整体一致性 | 4 | **3.5** | 版本声明统一（SKILL.md:23 基准 1.46.0+，references 不重复标注，新 API 以 v1.xx.0+ 内联标注，抽查 20+ 处标注齐全且与内容对应）；术语统一（SaSession/StpUtil/StpLogic/踢人/顶人）；示例风格统一（都带"为什么/最佳实践"尾注）。扣 0.5 分：① 07-redis-frontsep §一/2 主示例 Redis 配置用 SB2 前缀 `spring.redis`（07-redis-frontsep.md:30-44），而 §三、13-micro-service 均用 SB3 前缀 `spring.data.redis`，且 skill 主推 SB3/4，风格未对齐（有文字提示，故非错误）；② 01-setup 版本号与 SKILL.md 散文式声明存在轻微双源（见 T12）。 |
| **合计** | **100** | **89.5** | |

---

## 五、Top 问题清单（按影响排序）

1. **【D4 确定性编译错误 / 影响 T8】`11-advanced.md:324`**（§6「不同体系不同配置」）
   `StpKit.USER.setStpLogic(new StpLogic("user").setConfig(userConfig));` —— `StpLogic` 类不存在 `setStpLogic` 方法（该方法是 `StpUtil` 的静态方法），且 `StpKit` 的字段为 `static final`（11-advanced.md:262-266），照抄必然编译失败。正确写法应为 `SaManager.setConfig(StpKit.USER, userConfig)`。这是全包中唯一能直接误导 Agent 产出坏代码的缺陷，且恰好命中 T8 测试场景，建议修复。

2. **【D4 潜在编译问题 / 影响 T2、T11】`03-permission.md:7-31`**（§1 StpInterface 实现示例）
   示例仅实现 `getPermissionList` / `getRoleList` 两方法。若 1.46.0 的 `StpInterface.isDisabled` 为抽象方法（SKILL.md:145 称升级导致"实现类编译失败"），则此示例在 1.46.0 下无法编译。需与官方源码确认 `isDisabled` 是否有默认实现，并建议在示例中注明。

3. **【D4 软性 / 影响 T4、T6、T9】若干 1.46.0 新 API 签名未离线核实**
   - `SaJsonStrategy.instance.registerAllowType(Class)`（07-redis-frontsep.md:55）
   - `StpInterface.isDisabled(Object, String, String)` 参数顺序与返回类型 `SaDisableWrapperInfo`（11-advanced.md:145-151）
   - `SaDisableWrapperInfo.createDisabled/createNotDisabled` 工厂方法（11-advanced.md:148-150）
   - `SaSession.getList/getSet/getMap` 的 lazy 参数精确类型（06-session.md:53-55）
   - `SaCorsHandleFunction`（09-pitfalls.md:49）
   建议逐项对照 1.46.0 官方 `StpInterface` / `SaJsonStrategy` / `SaSession` / `StpLogic` 源码核对；本报告因离线评审无法定论。

4. **【D3 覆盖缺口】OAuth2 客户端凭证/隐藏式授权模式仅一句话带过**（12-sso-oauth2.md:291-294）
   T6 场景只测授权码模式所以未扣分，但作为"四种授权模式"的声称覆盖，另两种（尤其 client_credentials）无示例，用户问到时 Agent 只能靠 SKILL.md 泛化描述兜底。

5. **【D6/D9 一致性】Redis 配置示例前缀风格不统一**
   `07-redis-frontsep.md:30-44` 主示例用 SB2 前缀 `spring.redis`，而 skill 主推 SB3/4，且 §三/集群示例、13-micro-service.md:51-58 均用 `spring.data.redis`。虽文内有"SB3.x 前缀改 spring.data.redis"提示，但 SB3 用户照抄主示例会直接连接失败。建议主示例直接改为 `spring.data.redis` 并在注释中注明 SB2 写法。

6. **【低置信度】`14-plugin.md:45-55` JWT 三模式对比表 Mixin 行**
   "Mixin `active-timeout ✅`"与官方文档"续期 token ❌"的对应关系存疑；"Mixin `id 反查 Token ✅`"是否成立也需核对（Mixin 登录数据内嵌 token 且不持久化 token 索引时，`getTokenValueByLoginId` 行为待确认）。建议对照官方 JWT 集成文档核表。

7. **【低置信度】`09-pitfalls.md:17-21` 异常细分状态码数值**
   "核心包 11011~11016 / 11041 缺角色 / 11051 缺权限 / 11071 二级认证未过；SSO 30001~30011；OAuth2 30101+；JWT 30201+"——数值段无法离线核实，建议在 reference 内注明核对来源，避免 Agent 用错 code 分支。

---

## 六、专项核对记录（评审步骤要求项）

| 核对项 | 结果 | 证据位置 |
|---|---|---|
| 14 个 reference 是否全部被 SKILL.md 决策路由表引用 | ✅ 全部覆盖，无孤儿文件 | SKILL.md:68-83（01~14 逐行存在） |
| 版本基准声明与 v1.xx.0+ 内联标注是否齐全 | ✅ 20+ 处标注，均与内容对应 | SKILL.md:23/145；02:72（v1.29.0+）；02:94、10:72、11:103/157（v1.31.0+）；06:52、07:52/157、09:105-123、11:146/502-504/637、14:90/278/354-385（v1.46.0+） |
| `StpInterface.isDisabled` 三参签名 | ✅ 3 参示例正确给出（loginId, service, loginType）+ 2 参历史说明 | 11-advanced.md:145-151；09-pitfalls.md:112 |
| `doBeforeLogout` 等新钩子 | ✅ 列出 doBeforeLogout/doBeforeKickout/doBeforeReplaced（v1.46.0+）及用途说明 | 11-advanced.md:502-513 |
| `SaJsonStrategy` 白名单 | ✅ registerAllowType + 时序陷阱（首次构建后不可再注册）+ fory-json 无此问题 | 07-redis-frontsep.md:52-57；14-plugin.md:368 |
| `SaSession.getList/getSet/getMap` 1.46.0 新 API | ✅ 三类方法 + lazy 语义完整示例 | 06-session.md:52-55 |
| 1.46.0 破坏性变更闭环 | ✅ 三处（isDisabled/allowLoginIdColon/extraData）在 SKILL.md 版本注意、09-pitfalls §10、14-plugin §1.7 形成闭环 | SKILL.md:145；09-pitfalls.md:110-124；14-plugin.md:90 |
| 交叉引用有效性抽查 | ✅ 全部可解析，章节号准确 | 04→14 §4/§7；05→antipattern §15/§16；07→01 §0、14 §8/§6；09→11 §3.5；12→09 §6；13→14 §1/§6 |

---

## 七、评审结论

本 Skill 内容包整体达到**高可用水平**（12 场景均值 92.8，9 维度 89.5/100）。作为 Sa-Token 1.46.0 跟版编码助手，其"决策路由 + 分域 reference + antipattern 护栏 + 版本破坏性变更闭环"的结构设计优于多数同类 skill；12 个测试场景中有 11 个可被完整、正确地引导到答案，唯一明显短板是 `11-advanced.md:324` 的多账号配置示例编译错误（T8）。

**优先修复建议**（按性价比排序）：
1. 修复 `11-advanced.md:324` `StpKit.USER.setStpLogic(...)` → `SaManager.setConfig(StpKit.USER, userConfig)`；
2. 核验 03-permission §1 在 1.46.0 下的可编译性（isDisabled 默认实现确认）；
3. 将 07-redis-frontsep §一/2 主示例 Redis 前缀统一为 `spring.data.redis`；
4. 对照官方源码核实 Top 问题 #3/#6/#7 列出的软性 API/数值项。

> 本报告所有评分均基于对内容包文件的逐行阅读与 12 个测试场景的独立推演；引用位置以文件+章节+行号标注，未修改 skill 内容包任何文件。
