# Sa-Token 开发助手 Skill 盲评报告（v2.2.0）

- **评审员**：盲评员 B（独立评审，未参与编写，未参考其他评审员报告）
- **评审对象**：`I:\GitDownload\skills\skills\sa-token-dev\`（SKILL.md + references/ 14 个文件）
- **测试输入**：`I:\GitDownload\skills\eval\sa-token-dev\test-prompts-v2.2.0.json`（12 个场景 T1~T12）
- **评审日期**：2026-08-21
- **基准**：Sa-Token 1.46.0（skill 声明与跟版目标）

---

## 一、总评

| 项目 | 结果 |
|---|---|
| 场景均分（T1~T12 平均） | **92.9 / 100** |
| 九维度加总 | **92.5 / 100** |
| 综合总分 | **≈ 92.9 / 100** |
| 总体评价 | 内容扎实、跟版及时（1.46.0 破坏性变更全覆盖）、导航结构优秀；主要扣分集中在个别代码示例的签名/写法疑点与 1-2 处事实性偏差（序列化方式、多账号独立配置写法）。 |

**评分分布**：逐场景 86~95 分区间，无明显短板场景；T8（多账号独立配置）因示例写法踩坑风险最低，T11（1.46.0 升级适配）与 T9（封禁/二级认证）表现最佳。

---

## 二、逐场景评分表

| 场景 | 标题 | 得分 | 主要依据 | 扣分点 |
|---|---|---|---|---|
| T1 | 登录认证基础（SB3 + Maven） | **92** | `01-setup.md` 版本与依赖表给出 SB3→`sa-token-spring-boot3-starter` 正确坐标；`01-setup.md` §1 Maven/Gradle 示例、§2 yml、§3 最小登录示例完整；`02-login-auth.md` §1 登录/§5 注销；SKILL.md C3 检查点引导确认前后端分离 | 最小示例与登录流程示例风格略不统一（`01-setup` §3 用 String 返回，`02` 用 SaResult），不影响可用性 |
| T2 | 注解鉴权 + StpInterface | **94** | `04-annotation.md` §1 注册 SaInterceptor（必做前提）+ §2 `@SaCheckPermission`/`@SaCheckRole`；`03-permission.md` §1 StpInterface 双方法签名正确；`10-antipattern.md` §1 精准预警未注册拦截器 | 无实质扣分 |
| T3 | 小程序前后端分离 | **94** | `07-redis-frontsep.md` §二 后端返回 `SaTokenInfo` + 前端 uni-app header 塞 token（`{tokenName: tokenValue}`）完整闭环；`10-antipattern.md` §3 对应纠偏 | 无实质扣分 |
| T4 | Redis 集成 + 自定义对象存 Session | **90** | `07-redis-frontsep.md` §1 依赖/配置 + SB3 `spring.data.redis` 前缀提醒；v1.46.0 `SaJsonStrategy.instance.registerAllowType(SysUser.class)` 白名单机制抓得准（跟版重点） | **序列化方式表述存疑**（见 Top 问题 #2）：`07-redis-frontsep.md` §3 称 `sa-token-redis-template`「默认以 JSON 格式存储（Jackson）」，与官方该依赖为 JDK 序列化、Jackson 对应 `sa-token-redis-jackson` 的事实不符，白名单说明的依赖链路错位 |
| T5 | SSO 模式选型（异域 + 同 Redis） | **94** | `12-sso-oauth2.md` §2 选型表明确「前端不同域 + 后端同 Redis → 模式二」；§6 模式二 Client/Server 关键配置（server-url/secret-key/alone-redis 同库）完整 | 无实质扣分 |
| T6 | OAuth2 授权码 + 数据库 Client | **93** | `12-sso-oauth2.md` §13 `addClient` + `GrantType.authorization_code`；§14 授权码流程（/authorize + /oauth2/token）；§15 `SaOAuth2DataLoader` 数据库模式；客户端配置代码/YAML 双声明 | 轻微：授权码流程 `scope=openid` 单 scope 示例可再完整些；未提醒 SB3 Redis 前缀（OAuth2 非必须 Redis，影响小） |
| T7 | JWT 无状态 | **95** | `14-plugin.md` §1.3/§1.4 三模式对比表准确（Stateless 无 Redis、**不支持踢人/顶人/Session/active-timeout**，直接回答场景提问）；SKILL.md C1 检查点 + 强约束 #12 防止误推 JWT | 无实质扣分 |
| T8 | 多账号体系 + 不同 timeout | **86** | `11-advanced.md` §6 StpKit 门面主线正确（`StpUtil.stpLogic`/`new StpLogic("admin")` 与官方一致）；SKILL.md C6 检查点 | **示例写法踩坑**（见 Top 问题 #1）：§6「不同体系不同配置」用 `StpKit.USER.setStpLogic(new StpLogic("user").setConfig(userConfig))`，`setStpLogic` 为静态注册方法，新 StpLogic 与 `StpKit.USER` 字段解耦、配置不生效；官方正确写法为 `StpKit.USER.setConfig(userConfig)`（已核对官方文档 §9） |
| T9 | 封禁/踢下线/数据库读取/二级认证 | **95** | `11-advanced.md` §3.1 封禁 + §3.5 `isDisabled(Object, String, String)` 三参（v1.46.0+ 签名正确，含 `SaDisableWrapperInfo.createDisabled` 工厂）；§4 二级认证 `openSafe/checkSafe` + `@SaCheckSafe`；`10-antipattern.md` §8 封禁先踢下线、§9 v1.31.0+ 显式 checkDisable | 无实质扣分 |
| T10 | 微服务网关 + Same-Token | **94** | `13-micro-service.md` §1 网关 Reactor / 子服务 Servlet 依赖分离 + §3.3 `SaReactorFilter` 注册 + §4.2/§4.3 Same-Token 两环节（网关转发 + Feign `RequestInterceptor`）完整；`10-antipattern.md` §27 网关 Servlet 依赖预警 | 轻微：`13-micro-service.md` 章节编号 1.1→1.4 跳跃（缺 1.2/1.3） |
| T11 | 1.46.0 升级适配 | **95** | `09-pitfalls.md` §10 版本破坏性变更表（`isDisabled` 3 参 + `allowLoginIdColon` 默认 false）+ `11-advanced.md` §3.5 三参示例；SKILL.md「版本注意」节二次提示；场景两个报错点均被精确覆盖 | 无实质扣分 |
| T12 | 版本统一管理 | **93** | `01-setup.md` §0 `${sa-token.version}` 占位符 + 父 pom `<properties>` 单点声明 + Gradle `ext` 等价方案；07/12/13/14 依赖示例全部复用占位符，无散落硬编码 | 轻微：`01-setup.md` §0 示例中写死 `<sa-token.version>1.46.0</sa-token.version>`，虽有「与 SKILL.md 声明同步」注释，仍是唯一一处字面版本号，改 SKILL.md 声明时存在遗忘同步风险 |

---

## 三、九维度均分表

| 维度 | 满分 | 得分 | 评价依据 |
|---|---|---|---|
| D1 触发精度 | 12 | **11.5** | description 关键词覆盖登录/注销/认证/鉴权/权限/角色/token/会话/SSO/OAuth2/JWT/踢人/封禁/二级认证/多账号/微服务网关；明示排除 Spring Security/Shiro、非 Java、纯 JWT 自实现；「第 0 步依赖探测」分支设计（激活/询问/退出）有效防止误触发；激进激活策略（"无论用户是否提到 Sa-Token"）有 Java/SpringBoot + 认证类任务双重限定兜底 |
| D2 可发现性 | 12 | **11.5** | SKILL.md「决策路由表」14 行关键词→文件映射 + 每行附「同时警告」；文件编号 01~14 与主题对齐；每个 reference 开头有核心一句话；「关键决策检查点」C1~C6 提供决策路径 |
| D3 覆盖完整 | 12 | **11** | 登录/权限/会话/Redis/SSO/OAuth2/JWT/多账号/微服务/插件十大主题全覆盖；1.46.0 新增点（SaJsonStrategy、fory-json、rest-template/rest-client、alone-redisson、Session 集合读取、doBeforeLogout、isDisabled 三参、allowLoginIdColon、配置来源自定义）均有；扣分：Redis 序列化插件线不完整——未列 `sa-token-redis-jackson`（Jackson 序列化官方常用项），且 `sa-token-fastjson2` 名称不精确（官方为 `sa-token-redis-fastjson2`/`sa-token-redis-snack3`） |
| D4 可执行性 | 12 | **10** | 抽查 30+ 个 API 签名与官方一致（StpInterface 三参、SaTokenListener 钩子、SaSameUtil、SaSsoClientUtil.buildServerAuthUrl、SaOAuth2DataLoader、SaTempUtil、SaApiKeyUtil、SaSignUtil、SaTotpUtil、SaHttpDigestUtil 等）；扣分：① `11-advanced.md` §6 `StpKit.USER.setStpLogic(...)` 配置不生效（已确认官方用 `setConfig`）；② `07-redis-frontsep.md` §3 序列化方式表述与依赖不符；③ `11-advanced.md` §7 BCrypt 示例无 import/依赖来源（`cn.dev33.satoken.secure.BCrypt`，易与 Spring Security BCrypt 混淆）；④ `12-sso-oauth2.md` §7 模式三 yml 用 `spring.redis` 前缀未标注 SB 版本 |
| D5 防错/陷阱 | 12 | **11.5** | `10-antipattern.md` 28 条「错误→正确→为什么」结构（未注册拦截器、SaSession/HttpSession、Redis 前缀、Starter 混用、setError、SaRouter 顺序、@SaIgnore 边界、CORS、token 前缀空格、LoginType 运行时修改、Same-Token 刷新集中化、侦听器 try-catch、hutool 版本冲突、JWT is-share/is-concurrent）；`09-pitfalls.md` 7 种 NotLoginException 场景值 + 破坏性变更表；SKILL.md 12 条核心强约束 |
| D6 信息密度 | 12 | **10.5** | 各文件紧凑表格化，无注水段落；10-antipattern 每条含可运行正/反例；扣分：SKILL.md「主动行为触发」与「核心强约束」与 `09-pitfalls`/`10-antipattern` 存在主题重叠（is-share 语义、allow-url、setError、Redis 前缀在 4+ 处重复），属有意的多入口设计，但严格删减不影响产出 |
| D7 内部导航 | 12 | **11** | 决策路由表覆盖全部 14 个 references；交叉引用逐一核对准确（`10-antipattern.md` §1/§3/§8/§10/§15/§16/§17/§24、`11-advanced.md` §3.5/§6、`14-plugin.md` §1/§4/§6/§7/§8、`09-pitfalls.md` §6、`01-setup.md` §0 均能定位到正确章节）；references 头部无冗余版本声明，主版本号只在 SKILL.md frontmatter；扣分：`13-micro-service.md` 章节编号 1.1→1.4 跳跃 |
| D8 范围明确 | 12 | **12** | 适用/不适用边界在 description、SKILL.md「何时使用」表、第 0 步探测、以及各插件文件（`14-plugin.md` §2.6/§3.7/§4.1/§5.3/§6.2/§7.4 的适用/不适用声明）多处显式声明，边界无歧义 |
| D9 整体一致性 | 4 | **3.5** | 版本声明集中在 SKILL.md、references 统一 `${sa-token.version}` 占位符 + `v1.xx.0+` 功能级标注，术语与示例风格统一；扣分：`12-sso-oauth2.md` §7 模式三 `spring.redis`（SB2 风格）与全局 SB3 `spring.data.redis` 强调不一致；`01-setup.md` §0 字面版本号 1.46.0 |
| **合计** | **100** | **92.5** | |

---

## 四、Top 问题清单（按影响排序）

### 1.【高】`11-advanced.md` §6「不同体系不同配置」示例配置不生效
- **位置**：`references/11-advanced.md` §6（约 §6.5，代码块 `setSaTokenConfig`）
- **问题代码**：`StpKit.USER.setStpLogic(new StpLogic("user").setConfig(userConfig));`
- **依据**：官方多账号文档（sa-token.cc/doc.html#/up/many-account §9）的独立配置写法为 `StpUserUtil.stpLogic.setConfig(config2)`——即 **`StpLogic.setConfig()` 实例方法**。`setStpLogic` 是注册进 `SaManager` 的静态方法；本写法通过实例调用静态方法虽可编译，但把**新创建**的 StpLogic 注册进全局 map，而 `StpKit.USER` 字段仍指向构造时的旧 StpLogic，二者解耦，独立 timeout/tokenName 配置实际不生效。同时 `new StpLogic("user")` 与 `StpKit.USER = new StpLogic("user")` 重复创建实例。
- **影响**：T8（多账号 + 不同 timeout）场景下 agent 照抄该示例会产出"能跑但配置无效"的代码，直接命中 skill 自己强调的反模式。
- **建议**：改写为 `StpKit.ADMIN.setConfig(adminConfig); StpKit.USER.setConfig(userConfig);`。

### 2.【高，需核实】`07-redis-frontsep.md` §3 Redis 序列化方式表述与官方事实不符
- **位置**：`references/07-redis-frontsep.md` §一.3「要点」（"默认以 JSON 格式存储（Jackson）"）
- **依据**：官方 Redis 集成文档（sa-token.cc §up/integ-redis）：`sa-token-redis-template`（旧 `sa-token-redis`）为 **jdk 默认序列化**（二进制不可读）；**Jackson JSON 序列化对应 `sa-token-redis-jackson`**。skill 全包推荐 `sa-token-redis-template`（07 §1、12 §3、13 §1.4），却声称"默认以 JSON 格式存储（Jackson）"并据此引出 v1.46.0 `SaJsonStrategy` 白名单（防 Jackson 多态 RCE）。
- **影响**：T4（Redis + 自定义对象存 Session）场景下：① 若用户照抄依赖 `sa-token-redis-template`，实际是 JDK 序列化，"必须注册白名单否则报错"的说明不适用于该依赖（白名单机制对应 Jackson 序列化插件）；② 序列化选择建议（Jackson 可读性/白名单）漏掉了更常用的 `sa-token-redis-jackson` 依赖。
- **补充**：同节「引对应 `sa-token-fastjson2` 等依赖」名称不精确，官方为 `sa-token-redis-fastjson2` / `sa-token-redis-snack3`。
- **备注**：若 1.46.0 曾调整 `sa-token-redis-template` 默认序列化，则以该版本源码为准；按 1.38~1.39 起长期官方文档判断，现表述存在错位。

### 3.【中】`12-sso-oauth2.md` §7 SSO 模式三 yml 使用 `spring.redis` 前缀，未标注 SpringBoot 版本
- **位置**：`references/12-sso-oauth2.md` §7「Client 端关键配置」yaml（`spring.redis.database: 3`）
- **问题**：与 `07-redis-frontsep.md`、`01-setup.md`、SKILL.md 强约束 #11 反复强调的"SpringBoot 3.x 前缀改为 `spring.data.redis`"不一致。SB3 用户照抄该示例会连不上 Redis。
- **建议**：改为 `spring.data.redis` 或注明"SB2 写法，SB3 用 spring.data.redis"。

### 4.【中】`11-advanced.md` §7 BCrypt 示例缺 import 与依赖来源
- **位置**：`references/11-advanced.md` §7「BCrypt 加密（推荐用于密码存储）」
- **问题**：示例直接使用 `BCrypt.hashpw/gensalt`，未注明类全限定名（Sa-Token 自带 `cn.dev33.satoken.secure.BCrypt`，注意与 Spring Security 的 `org.springframework.security.crypto.bcrypt.BCrypt` 区分），也未说明是否需要额外依赖。
- **影响**：agent 生成代码时可能引入错误 import 或重复依赖。

### 5.【低】`13-micro-service.md` 章节编号跳跃
- **位置**：`references/13-micro-service.md` §1.1「依赖选择」→ §1.4「Redis 集成」，缺 §1.2/§1.3。
- **影响**：轻微影响目录观感与引用准确性（正文引用"见 §1.4"可定位，但编号断层）。

### 6.【低】`09-pitfalls.md` §2 异常码段表述略不完整
- **位置**：`references/09-pitfalls.md` §2
- **问题**：「常用码段：核心包 11011~11016（token 无效/过期/被顶/被踢/冻结）」——11011 实际对应 `NOT_TOKEN`（未读取到 token，即 §1 表格 -1 场景），其括号内语义概述未含 11011，且 7 种场景的 code 段应到 11017（含 `NO_PREFIX`），正文止于 11016。
- **影响**：极轻微，排错时可能漏查 11017。

### 7.【低，存疑】两处 `v1.46.0+` 功能版本标注偏严
- **位置**：`references/06-session.md` §4（`session.getList/getSet/getMap` 类型安全集合读取，标 v1.46.0+）；`references/11-advanced.md` §10（`doBeforeLogout/doBeforeKickout/doBeforeReplaced` 钩子，标 v1.46.0+）
- **说明**：上述能力在官方历史版本中的实际引入版本可能早于 1.46.0；标注偏严不产生误导（1.46.0 用户使用必然存在），仅提示团队维护时可核对。`11-advanced.md` §13 `SaStrategy.setGetSaTokenConfig`（v1.46.0+）为新 API，无法外部核实，按 skill 内部声明采信。

---

## 五、核查记录（与 Sa-Token 1.46.0 对照）

| 核查点 | 结论 |
|---|---|
| `StpInterface.isDisabled` 三参 `(Object, String, String)` 返回 `SaDisableWrapperInfo`（11-advanced §3.5 / 09-pitfalls §10） | ✅ 与 1.46.0 一致，示例含 `createDisabled/createNotDisabled` 工厂 |
| `SaTokenListener` 钩子签名 `doLogin(loginType, loginId, tokenValue, SaLoginParameter)`、`doLogout(loginType, loginId, tokenValue)`（11-advanced §10） | ✅ 签名一致；`SaTokenListenerForSimple` 抽象类存在 |
| `StpKit` 门面 `StpUtil.stpLogic` / `new StpLogic("admin")`（11-advanced §6） | ✅ 与官方 Kit 模式一致（官方文档 §5） |
| 独立体系配置写法（11-advanced §6） | ❌ `setStpLogic` 写法错误，官方为 `setConfig`（见 Top 问题 #1） |
| `SaJsonStrategy.instance.registerAllowType(...)`（07 §3） | ✅ 1.46.0 新增机制存在；但适用依赖应为 Jackson 序列化插件，见 Top 问题 #2 |
| `session.getList/getSet/getMap(key, Class, lazy)`（06 §4） | ⚠️ 存在，版本标注待核实 |
| `allowLoginIdColon` 默认 false + yml 配置（09 §10） | ⚠️ 1.46.0 新增，配置名驼峰写法待核实（skill 内部一致） |
| `SaReactorFilter` 以 `@Bean` 注册（13 §3.3、11 §11） | ✅ 与官方微服务文档一致 |
| `SaSameUtil` 六方法 + `SAME_TOKEN` 常量（13 §4.4） | ✅ 一致 |
| `SaSsoClientProcessor.instance.checkTicket` 返回 `SaCheckTicketResult{loginId, remainTokenTimeout, deviceId}`（12 §8） | ✅ 一致 |
| `SaOAuth2ServerConfig.addClient(SaClientModel)` + `SaOAuth2DataLoader`（12 §13/§15） | ✅ 一致 |
| `StpUtil` 高频 API（login/logout/kickout/replaced/disable/openSafe/switchTo/checkDisableLevel 等，08） | ✅ 抽查一致 |
| NotLoginException 七场景值 -1~-7（09 §1） | ✅ 与官方常量一致 |
| `SaTokenDaoRedisImpl` 默认序列化（07 §3） | ❌ 疑点，见 Top 问题 #2 |

---

## 六、结论

- **总体定级**：高质量、生产可用的编码辅助 skill，1.46.0 跟版是其突出优势（isDisabled 三参、allowLoginIdColon、SaJsonStrategy、Session 集合读取等新特性均有覆盖且有破坏性变更专项表）。
- **最大亮点**：D5 防错设计（28 条 antipattern + 12 条强约束 + 版本变更表）与 D8 范围界定（触发/排除/探测分支清晰）。
- **最需修复**：`11-advanced.md` §6 多账号独立配置示例（Top #1）——它会直接产出"配置不生效"的代码，属于"能编译但逻辑错"的高危反模式；其次是 `07-redis-frontsep.md` 序列化方式表述（Top #2）。
- **建议动作**：修复 Top #1/#2 后，本 skill 可视为针对 Sa-Token 1.46.0 的 A 级开发辅助包。
