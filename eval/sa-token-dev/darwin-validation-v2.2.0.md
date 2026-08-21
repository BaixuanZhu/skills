# sa-token-dev v2.2.0 达尔文验证报告（盲评 + 实跑）

> **验证日期**：2026-08-21
> **版本**：v2.1.1 → v2.2.0（1.46.0 跟版 + 精简轮 + 版本收敛）
> **方法**：① 两份独立子代理盲评（9 维度 rubric，12 场景）② 最小 SpringBoot 3.5 + Sa-Token 1.46.0 + Redis 项目实跑验证关键示例（编译 + 运行期语义）
> **结论**：盲评 A 92.8 / B 92.9（双盲评交叉一致）；实跑 **5/5 PASS**，发现并修复 2 处确定性缺陷（StpKit 编译错误、SaJsonStrategy 注册时机）+ 1 处 import 缺失

## 一、盲评结果

| 盲评员 | 12 场景均分 | 关键发现 |
|---|---|---|
| A | 92.8/100 | StpKit 编译错误（T8 最低分 82）、SaJsonStrategy 软性待核 |
| B | 92.9/100 | StpKit 配置不生效（T8 最低分 86）、redis 序列化疑点 |

**双盲评共识**：唯一确定性缺陷是 `11-advanced.md:324` 的 `StpKit.USER.setStpLogic(new StpLogic("user").setConfig(userConfig))`——StpLogic 无 `setStpLogic` 方法。两份盲评均给 T8（多账号）最低分，根因一致。

**维度信号**：D5 防错（28 条 antipattern + 12 强约束 + 破坏性变更表）最强；1.46.0 三项破坏性变更在 SKILL.md / 09 / 11 / 14 四处形成闭环；14 个 reference 全部被决策路由表覆盖，无孤儿文件。

## 二、实跑验证（5/5 PASS）

### 环境

| 组件 | 版本 |
|---|---|
| JDK | 21 |
| SpringBoot | 3.5.0（RANDOM_PORT） |
| Sa-Token | 1.46.0（`${sa-token.version}` 占位符） |
| Redis | 7-alpine（Docker，端口 16379） |
| 序列化 | sa-token-redis-template 默认 `SaSerializerTemplateForJson` |

### 测试用例

| # | 验证点 | 对应 skill 内容 | 结果 |
|---|---|---|---|
| 1 | `StpInterface.isDisabled(loginId, service, loginType)` 三参编译 | 11-advanced §3.5（v1.46.0 破坏性变更） | ✅ |
| 2 | `SaTokenListenerForSimple` 的 `doBeforeLogout` 钩子运行触发 | 11-advanced §10（v1.46.0+） | ✅ |
| 3 | `SaSession.getList/getSet/getMap` lazy 语义（含二次命中缓存） | 06-session §4（v1.46.0+） | ✅ |
| 4 | `SaJsonType` 白名单方式：业务实体 Session 存取不报错 | 07-redis §序列化安全 | ✅ |
| 5 | `SaJsonStrategy` 初始化后不可注册（时序说明） | 07-redis §序列化安全 | ✅ |
| 6 | `StpKit.USER.setConfig(userConfig)` 修正写法可执行 | 11-advanced §6（修复后） | ✅ |
| 7 | redis-template 默认序列化器 = JSON | 07-redis §3 | ✅ |
| 8 | `${sa-token.version}` pom 占位符生效 | 01-setup §0 | ✅ |

### 实跑发现（盲评遗漏，实跑独有）

1. **`SaDisableWrapperInfo` import 包名**：正确包为 `cn.dev33.satoken.model.wrapperInfo`（非 `stp` 包）。skill 示例缺 import，agent 照抄猜错包名即编译失败 → 已补 import + 包名提示。
2. **`SaJsonStrategy.registerAllowType` 时机**：官方推荐 `main` 方法里 `SpringApplication.run` **之前**注册，或实体实现 `SaJsonType`、或 SPI 文件（`META-INF/satoken/sa-json-type.list`）。skill 原文的 `@PostConstruct` 示例在集成 Redis 时**必然失败**（实跑确认：JSON 插件已初始化，报「已初始化，无法再注册」）→ 已重写为官方三种方式 + 时序警告。

## 三、盲评疑点裁决

| 疑点 | 来源 | 裁决 |
|---|---|---|
| `StpKit.USER.setStpLogic(...)` 编译错误 | A+B 共识 | ✅ 确认（源码：StpLogic 无此方法），已修 |
| redis-template 默认「JDK 序列化」 | 盲评 B | ❌ **否决**（实跑：`SaSerializerTemplateForJson`，官方文档 L2242「json 存储」） |
| 03-permission 示例未实现 isDisabled 无法编译 | 盲评 A | ❌ **否决**（源码：isDisabled 是 default 方法） |
| 异常码段应含 11017（NO_PREFIX） | 盲评 B | ❌ **否决**（官方表 11011~11016 仅 6 个 token 码，无 11017） |

## 四、修复清单

| # | 位置 | 问题 | 修复 |
|---|---|---|---|
| 1 | 11-advanced §6 L324 | `StpKit.USER.setStpLogic(new StpLogic("user").setConfig(...))` 编译错误 | 改为 `StpKit.USER.setConfig(userConfig)` + 反例说明 |
| 2 | 11-advanced §3.5 | 缺 `SaDisableWrapperInfo` import（包名易猜错） | 补 `model.wrapperInfo` import + default 方法说明 |
| 3 | 07-redis §序列化安全 | `@PostConstruct` 注册时机太晚（实跑失败） | 重写为官方三种方式（SaJsonType 推荐 / main 前注册 / SPI）+ 时序警告 |
| 4 | 07-redis §一/2 | 主示例 Redis 前缀 SB2 风格 | 改 `spring.data.redis`（SB3 主推）+ 注明 SB2 |
| 5 | 12-sso §7 模式三 | yml `spring.redis` 前缀 | 改 `spring.data.redis` |
| 6 | 11-advanced §7 | BCrypt 缺 import/来源 | 补 `cn.dev33.satoken.secure.BCrypt` + 与 Spring Security 区分 |
| 7 | 13-micro §1 | 章节编号 1.1→1.4 跳跃 | 重编号为 1.2，同步引用 |
| 8 | 09-pitfalls §2 | 异常码段语义缺 11011 | 补「未读取到 token」语义 |

## 五、存疑未修（记录待核）

- **JWT Mixin 行 `active-timeout ✅`**（盲评 A 低置信）：官方聚合文档未收录三模式 active-timeout 对照，无证据不擅改。
- **OAuth2 client_credentials / 隐藏式无示例**（盲评 A 覆盖度提示）：四种授权模式表已有描述，暂不扩写。

## 六、实跑环境陷阱记录

1. **测试线程无 HTTP 上下文**：`@SpringBootTest` 直接调 `StpUtil.login()` 报「SaTokenContext 上下文尚未初始化」——需 `RANDOM_PORT` + HTTP 请求驱动（TestRestTemplate）。
2. **StpKitConfig 会改默认体系 tokenName**：验证 `StpKit.DEFAULT.setConfig` 生效时，默认 tokenName 变为自定义值，测试需动态取 `StpUtil.getTokenName()` 而非硬编码 `satoken`。
3. **Windows 6379 端口 bind 失败**（Hyper-V 保留端口段）——改用 16379 映射。
4. **中文测试方法名 + `-Dtest=`**：Git Bash 传参编码丢失，全量跑从日志 grep。

## 七、结论

v2.2.0 通过双盲评（92.8 / 92.9）与实跑（5/5）。盲评确认 1.46.0 跟版质量，实跑额外揪出 3 处盲评无法发现的问题（import 包名、注册时机、序列化器事实），其中 2 处会让 agent 产出错误代码。修复后净减 44 行（精简轮）基础上本轮 +净修复，未膨胀。
