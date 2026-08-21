# Sa-Token 开发助手（sa-token-dev）回归核验报告 v2.2.0

- 评审人：独立回归评审员（未参与上一轮编写与修复）
- 评审对象：`I:\GitDownload\skills\skills\sa-token-dev\`（SKILL.md + 14 个 references）
- 版本基准：Sa-Token **1.46.0**（skill 版本声明 v2.2.0）
- 评审方式：逐项读源码比对（GitHub v1.46.0 / v1.45.0 tag 源码）、官方聚合文档（`I:\GitDownload\Sa-Token\llm-wiki\llms-full.txt`）、实跑复验（fixture 项目 + Docker Redis）
- 结论：**PASS（可发布）**

---

## 0. 评审过程摘要

| 步骤 | 说明 | 结果 |
|---|---|---|
| 内容包全读 | SKILL.md + 14 个 references 全文阅读 | 完成 |
| 官方源码比对 | GitHub `dromara/Sa-Token` `v1.46.0` / `v1.45.0` tag 拉取 `StpLogic` / `StpInterface` / `SaJsonStrategy` / `SaJsonType` / `SaSetValueInterface` / `SaErrorCode` 相关 / `BCrypt` / `NotLoginException` 等源码 | 完成 |
| 官方文档比对 | llms-full.txt 序列化白名单、封禁持久化、密码加密、多账号配置等章节 | 完成 |
| 实跑复验 | `docker run -d --name satoken-reg-redis -p 16379:6379 redis:7-alpine` + `mvn.cmd test` | **Tests run: 5, Failures: 0, Errors: 0, Skipped: 0** |

实跑日志关键证据：
- `默认序列化器: cn.dev33.satoken.serializer.impl.SaSerializerTemplateForJson`（07 §3 声明成立）
- `doLogin token=..., tokenName=satoken-admin`（`StpKit.DEFAULT.setConfig(adminConfig)` 生效，Fix 1 写法成立）
- `注册异常信息: SaJsonStrategy 已初始化，无法再注册允许反序列化的类型：com.example.demo.SysUser`（Fix 3 的 @PostConstruct 时序警告与实际报错文案一致）

---

## 1. 逐项核验表（8 处修复）

### ✅ 修复 1｜`11-advanced.md` §6：`StpKit.USER.setStpLogic(...)` → `StpKit.USER.setConfig(userConfig)` + 反例说明

| 核验点 | 证据 | 判定 |
|---|---|---|
| `StpLogic.setConfig(SaTokenConfig)` 存在 | v1.46.0 `StpLogic.java` L122 `public StpLogic setConfig(SaTokenConfig config)` | ✅ |
| `StpLogic` 无 `setStpLogic` 方法 | v1.46.0 `StpLogic.java` 全文 `setStpLogic` 出现 **0 次**；`StpUtil.java` 有 `public static void setStpLogic(StpLogic)`（这是 StpUtil 的静态方法，非 StpLogic 实例方法） | ✅ |
| 反例说明表述准确 | `11-advanced.md` L333：「`StpLogic` 没有 `setStpLogic` 方法（编译错误）…配置体系直接对实例调 `setConfig`」与源码一致；官方文档同款写法 `StpUtil.stpLogic.setConfig(config1)`（llms-full.txt L4489/L4497） | ✅ |
| 与实跑一致 | fixture `StpKitConfig.java` L21/L27 用 `StpKit.DEFAULT.setConfig(adminConfig)` / `StpKit.USER.setConfig(userConfig)`，编译通过且运行日志 `tokenName=satoken-admin` 证明配置生效 | ✅ |

**结论：✅ 正确，无残留**（全包仅剩两处 `setStpLogic`：L333 有意保留的反例说明；`14-plugin.md` L82 `StpUserUtil.setStpLogic(...)` 为合法静态方法用法，与官方文档 llms-full.txt L12642 一致）。

### ✅ 修复 2｜`11-advanced.md` §3.5：补 `SaDisableWrapperInfo` import + isDisabled default 方法说明

| 核验点 | 证据 | 判定 |
|---|---|---|
| import 包名 `cn.dev33.satoken.model.wrapperInfo.SaDisableWrapperInfo` | v1.46.0 `StpInterface.java` 源码 import 语句 `import cn.dev33.satoken.model.wrapperInfo.SaDisableWrapperInfo;`（本文件顶部） | ✅ |
| 三参签名 | v1.46.0 `StpInterface.java`：`default SaDisableWrapperInfo isDisabled(Object loginId, String service, String loginType)` | ✅ |
| isDisabled 是 default 方法 | 同源码：带 `default` 修饰符，默认返回 `SaDisableWrapperInfo.createNotDisabled()`，「不实现也能编译」说明准确 | ✅ |
| 版本差异声明「v1.46.0 以下为 2 参」 | v1.45.0 `StpInterface.java`：`default SaDisableWrapperInfo isDisabled(Object loginId, String service)` | ✅ |
| 快捷工厂方法 | `createDisabled(86400,1)` / `createNotDisabled()` / `createNotDisabled(86400)` 均存在于 v1.46.0（llms-full.txt L3459-3470 同款） | ✅ |
| 与实跑一致 | fixture `StpInterfaceImpl.java` L27 三参重写 + `SaDisableWrapperInfo.createNotDisabled()`，编译通过 | ✅ |

**结论：✅ 正确。**

### ✅ 修复 3｜`07-redis-frontsep.md` §序列化安全：重写为官方三种注册方式

| 核验点 | 证据 | 判定 |
|---|---|---|
| 方式 1：`SaJsonType` 标记接口 | v1.46.0 `cn.dev33.satoken.json.SaJsonType` 存在（`@since 1.46.0`，空标记接口）；官方文档「实体类实现 SaJsonType（推荐）」llms-full.txt L11843-11851；fixture `SysUser implements SaJsonType` 编译 + `saJsonType_白名单_业务实体存取Session` 测试通过 | ✅ |
| 方式 2：`SaJsonStrategy.instance.registerAllowType(Class)` 且须在 `SpringApplication.run` 之前 | v1.46.0 `SaJsonStrategy.java` L101 `public void registerAllowType(Class<?> type)`；官方文档 L11855「Spring Boot 请在 main 方法里、SpringApplication.run 之前」 | ✅ |
| @PostConstruct 太晚警告 | `SaJsonStrategy.java` L103-104 `if (isInit) throw new SaTokenException("SaJsonStrategy 已初始化，无法再注册…")`；实跑日志原文确认（见 §0）；官方文档 L11839「初始化之后不可再注册类型」 | ✅ |
| 方式 3：SPI 文件 `resources/META-INF/satoken/sa-json-type.list` | 官方文档 L11868-11876 路径与格式（`#` 注释、按行类名）完全一致；`SaJsonStrategy.java` L216 存在「加载 sa-json-type.list 失败」分支 | ✅ |
| 「fastjson2/snack3/fory-json 默认不写类型信息」 | 官方文档 L11837 覆盖 fastjson / fastjson2 / fory-json / snack3（skill 为子集，见 §2 观察项 N1，不影响正确性） | ✅ |

**结论：✅ 正确。**

### ✅ 修复 4｜`07-redis-frontsep.md` §一/2：主示例 `spring.redis` → `spring.data.redis`

- 当前主示例（L31-45）为 `spring.data.redis`，带注释「SB3.x / SB4.x 前缀；SB2.x 用 spring.redis」。
- SpringBoot 3.x 使用 `spring.data.redis` 为官方既定事实；fixture 使用 SB 3.5.0 + `spring.data.redis` 实跑通过（application.yml）。
- SKILL.md L39/L110、`01-setup.md` L122、`09-pitfalls.md` L37 等多处版本前缀说明彼此一致，无矛盾。
- 全包检索：`spring.redis` 仅出现在 SB2.x 说明语境（如 14-plugin §6.1 标注「业务 Redis（SB2.x）」、antipattern §10 反例），无残留错误主示例。

**结论：✅ 正确。**

### ✅ 修复 5｜`12-sso-oauth2.md` §7 模式三：yml `spring.redis` → `spring.data.redis`

- 当前（L195-201）为 `spring.data.redis`，带注释「SB3.x 前缀；SB2.x 用 spring.redis。Client 自己的 Redis（与 Server 不同）」。
- 与 SKILL.md 版本前缀规则、模式三「后端不同 Redis」语义一致。

**结论：✅ 正确。**

### ✅ 修复 6｜`11-advanced.md` §7：BCrypt 补来源说明

| 核验点 | 证据 | 判定 |
|---|---|---|
| 类所在包 `cn.dev33.satoken.secure.BCrypt` | v1.46.0 `sa-token-core/.../secure/BCrypt.java` 存在，`package cn.dev33.satoken.secure;` | ✅ |
| 静态方法签名 | `hashpw(String)` / `hashpw(String,String)` / `checkpw(String,String)` / `gensalt()` / `gensalt(int)` 均存在；示例 `BCrypt.hashpw("123456", BCrypt.gensalt())`、`BCrypt.checkpw("123456", hash)`、`BCrypt.gensalt(12)` 合法 | ✅ |
| 与 Spring Security BCrypt 区分 | Spring Security 的类为 `org.springframework.security.crypto.bcrypt.BCrypt`，包名不同，skill 表述正确 | ✅ |
| 与官方文档一致 | llms-full.txt L3609-3619 同款 API（`hashpw` / `checkpw` / `gensalt(10)` / `gensalt(12)`） | ✅ |

**结论：✅ 正确。**

### ✅ 修复 7｜`13-micro-service.md`：`### 1.4` → `### 1.2`（重编号）

| 核验点 | 证据 | 判定 |
|---|---|---|
| 重编号完成 | 当前章节为 `### 1.1 依赖选择` / `### 1.2 Redis 集成（必须）`，无 `1.4` 残留 | ✅ |
| 内部引用一致性 | L72 注释「另需引入 §1.2 的 Redis 集成依赖（必须）」→ 指向存在的 §1.2「Redis 集成」，自洽 | ✅ |
| 跨文件引用无漏改 | 全包检索 `1.4`：仅命中 `14-plugin.md` L43「### 1.4 三种模式功能对比」（JWT 自身章节号，与 13-micro-service 无关）；无任何文件引用「13-micro-service §1.4」 | ✅ |
| 外部引用 | SKILL.md L82/L95、`01-setup.md` L33 仅引用文件级（`13-micro-service.md`），未绑定具体章节号 | ✅ |

**结论：✅ 正确。**

### ✅ 修复 8｜`09-pitfalls.md` §2：异常码段补 11011「未读取到 token」语义

| 核验点 | 证据 | 判定 |
|---|---|---|
| 11011 = NOT_TOKEN（未读取到 token） | v1.46.0 `StpLogic.java` L1136 `throw NotLoginException.newInstance(loginType, NOT_TOKEN, NOT_TOKEN_MESSAGE, null).setCode(SaErrorCode.CODE_11011)`；`NotLoginException.java` `NOT_TOKEN="-1"`、`NOT_TOKEN_MESSAGE="未能读取到有效 token"` | ✅ |
| 11012~11016 对应关系 | 同文件 L1142/L1147/L1152/L1157/L1785 分别 setCode 11012(INVALID_TOKEN)/11013(TOKEN_TIMEOUT)/11014(BE_REPLACED)/11015(KICK_OUT)/11016(TOKEN_FREEZE) | ✅ |
| 11041 缺角色 / 11051 缺权限 / 11071 二级认证未过 | 同文件 L2135/L2157/L2186 `NotRoleException(...).setCode(CODE_11041)`；L2273/L2295/L2324 `NotPermissionException(...).setCode(CODE_11051)`；L2998 `NotSafeException(...).setCode(CODE_11071)` | ✅ |

**结论：✅ 正确。**

---

## 2. 新引入问题清单

未发现阻塞性新问题（无编译错误、无 API 错误、无引用错位、无版本标注缺失）。以下为观察项（非缺陷，不阻塞发布）：

- **N1（轻微）**：`07-redis-frontsep.md` L55「`fastjson2`/`snack3`/`fory-json` 默认不写类型信息」是官方文档（L11837）所列 `fastjson / fastjson2 / fory-json / snack3` 的子集（遗漏 `fastjson`，且 v1.46.0 另有 `sa-token-snack4` 插件）。skill 对已列出项的描述均正确，不影响使用，仅建议后续可补全。

---

## 3. 交叉引用与版本标注核验

| 检查项 | 结果 |
|---|---|
| SKILL.md 决策路由表 14 个 reference 指针 | 全部有效，对应文件均存在（`01-setup` ~ `14-plugin`） |
| SKILL.md L145「1.46.0 升级必查」三处指针 | `11-advanced.md §3.5`（数据库持久化/isDisabled）✅、`09-pitfalls.md §10`（allowLoginIdColon）✅、`14-plugin.md`（JWT extraData）✅ |
| 对修改文件的交叉引用 | `09-pitfalls.md`→`10-antipattern.md §17`✅；`07`→`10-antipattern §10/§3`✅、`14-plugin §8`✅；`04-annotation`→`11-advanced §6`✅；`01-setup`/`12-sso`/`13-micro`→各文件级引用✅ |
| 章节重编号副作用 | 无（Fix 7 已单独核验） |
| 版本标注 | `v1.46.0+` 标注抽查：`SaJsonType`（@since 1.46.0）✅、`getList/getSet/getMap` lazy（v1.45.0 源码无此方法 → v1.46.0 新增，标注准确）✅、`isDisabled` 3 参（v1.45.0 为 2 参）✅、`SaSerializerTemplateForJson`（实跑日志确认）✅、`registerAllowType` 初始化报错文案（实跑日志确认）✅ |
| 重复/矛盾表述 | 未发现；SKILL.md L76 仍以「SaJsonStrategy 白名单」概括（白名单本就由 SaJsonStrategy 管理），与 07 三种方式不矛盾 |

---

## 4. 实跑复验（可选步骤，已执行）

- 环境：Docker `redis:7-alpine`（映射 16379）→ fixture `sa-token-demo`（SB 3.5.0 + sa-token 1.46.0，`spring.data.redis`）→ `mvn.cmd test`
- 结果：**Tests run: 5, Failures: 0, Errors: 0, Skipped: 0**
- 5 个用例：`redisTemplate_默认序列化器类型` ✅ / `listener_注销前钩子触发` ✅ / `saJsonType_白名单_业务实体存取Session` ✅ / `session_集合类型安全读取_getList_getSet_getMap` ✅ / `saJsonStrategy_已初始化后不可注册` ✅
- 与 skill 文档一致性：fixture 的 `StpKit.USER.setConfig(userConfig)`（Fix 1）、`isDisabled` 三参 + `SaDisableWrapperInfo`（Fix 2）、`SysUser implements SaJsonType`（Fix 3）、`spring.data.redis`（Fix 4）、`getList/getSet/getMap` lazy 签名（06-session L53-55 与 TestController 逐字一致）全部与文档示例一致。

---

## 5. 结论

**PASS（可发布）。**

8 处修复全部核验通过，均有官方源码 / 官方文档 / 实跑三者之一的直接证据支撑；未发现修复引入的新问题；交叉引用与版本标注完整一致。N1 为可选的表述补全建议，不构成发布阻塞。

> 复验环境为一次性：Redis 容器已停止（`docker rm -f satoken-reg-redis`），评审期间产生的临时 JSON 已清理；skill 内容包未做任何修改。
