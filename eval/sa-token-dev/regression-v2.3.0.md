# Sa-Token 开发助手（sa-token-dev）回归核验报告 v2.3.0

- 评审人：独立回归评审员（未参与本轮编写与修复）
- 评审对象：`I:\GitDownload\skills\skills\sa-token-dev\`（SKILL.md + 14 个 references）+ `plugins\sa-token-dev\` 镜像
- 版本基准：Sa-Token **1.46.0**（skill 版本声明 v2.3.0）
- 评审范围：本轮改动全部为**结构/冗余清理**，声明未动任何技术事实（API 签名、坐标、版本标注、示例正确性）。本报告据此核验「删得干净、引得不破、事实没丢、口径自洽」。
- 评审方式：HEAD(v2.2.0) vs 工作树(v2.3.0) 的 git diff 逐处比对 + 官方聚合文档（`I:\GitDownload\Sa-Token\llm-wiki\llms-full.txt`）技术事实比对 + 实跑复验（fixture 项目 + Docker Redis）
- 结论：**PASS（可发布）**

---

## 0. 评审过程摘要

| 步骤 | 说明 | 结果 |
|---|---|---|
| 全量阅读 | SKILL.md + 14 个 references 全文阅读；plugins/ 镜像 15 文件与 skills/ 逐字节 diff | 完成 |
| 变更比对 | `git diff`（工作树 vs HEAD）：本轮实际触碰 7 个文件（SKILL.md + 02/03/10/12/13/14），与改动清单吻合；09/11 等未被触碰 | 完成 |
| 删除零残留 | 8 个被删词全包 grep；12 处标题清理词在 HEAD 中存在性反查（`git grep HEAD`） | 完成 |
| 官方文档比对 | llms-full.txt：通配符语义、StpInterface 检查源、SaSession lazy get、getSessionByLoginId、checkRoleAnd/Or 等 | 完成 |
| 实跑复验 | `docker run -d -p 16379:6379 redis:7-alpine` + `mvn.cmd test`（SB 3.5.0 + sa-token 1.46.0） | **基线 Tests run: 5, Failures: 0；新增 §6 API 用例后 Tests run: 6, Failures: 0** |

---

## 1. 逐项核验表（R1–R8）

### ✅ R1 结构完整性与指针有效性

| 核验点 | 证据 | 判定 |
|---|---|---|
| 决策路由表 14 行指针 → 文件均存在 | SKILL.md L92-105 共 14 行，对应 `references/01-setup.md`~`14-plugin.md` 14 个文件，`find` 确认全部存在；文件级指针无绑定章节号 | ✅ |
| 核心强约束恰好 12 条且编号连续 | SKILL.md L109-120，编号 1–12 连续无跳号、无第 13 条 | ✅ |
| 使用流程 7 步引用章节与改后标题一致 | 第 1 步引「第 0 步：依赖探测与激活分支」/「何时使用本技能」、第 2 步「关键决策检查点」、第 3 步「决策路由」、第 5 步「核心强约束」——与 SKILL.md 实际章节标题（L42/L52/L66/L107）逐字一致（标题改名的同时引用已同步） | ✅ |
| 版本注意三处指针仍有效 | SKILL.md L144：`11-advanced.md §3.5`（数据库持久化/isDisabled，11-advanced L137 存在）✅；`09-pitfalls.md §10`（版本破坏性更新/allowLoginIdColon，09-pitfalls L108 存在）✅；`14-plugin.md`（JWT extraData，§1.7 L90 存在）✅ | ✅ |

### ✅ R2 删除零残留

| 核验点 | 证据 | 判定 |
|---|---|---|
| 8 词全包 grep 零命中 | `同时警告`/`主动行为触发`/`代码审查护栏`/`RBAC 设计模式`/`典型登录接口`/`核心价值`/`硬门禁`/`全部本地` 在 v2.3.0 工作树全包 grep **0 命中**；`zhang` 仅剩 01-setup L83/86（最小示例）、06-session L41/42、11-advanced L278/390、14-plugin L67/320 的合法示例，02 中已删净 | ✅ |
| 12 处清理确认非「凭空消失」 | `git grep HEAD`：12 处在 v2.2.0 均存在（版本与依赖/第 0 步/决策路由/核心强约束/10-antipattern 标题/12-sso §2/13-micro §1/14-plugin §1.3 等后缀），工作树全部删除 | ✅ |
| 删除依据成立（5 条「主动行为触发」等价覆盖） | ① `is-share:true`+踢人 → 10-antipattern §6（共用 token 踢人语义）+ §7（踢人/顶人区分）+ §28（JWT Simple is-share 恒 false）；② `allow-url:"*"` → 10-antipattern §14（生产必配详细 URL）；③ active-timeout 自动续签 → 10-antipattern §5/§25 + 02-login-auth「Token 有效期」节（触发时机/autoRenew=false）；④ Feign 未传 Same-Token → 13-micro-service §4.3/§4.6；⑤ `@SaCheckDisable` 不指定 service → 11-advanced §3.4。5 条全部有等价的强制表述 | ✅ |
| 同时警告列（另 14 行）内容无丢失 | 该列全部警告逐条比对：timeout/active-timeout（强约束 #5+02）、StpInterface 必实现（#4+03）、后端再校验（#3+03）、通配符 *（03 §4）、SaInterceptor（#1+04）、SaSession≠HttpSession（#2）、spring.data.redis（#11）、场景值（#6+08+09）、封禁先踢下线（#7）、记住我/同端互斥/二级认证/StpKit/Token 前缀（11-advanced 对应节）、allow-url（10 §14+12）、Reactor/Redis/Same-Token（13）、JWT 正交（#12+14 §1）、v1.46.0 新插件（14 §8）——**全部在强约束或 references 中有等价表述，无技术事实丢失** | ✅ |

### ✅ R3 03-permission.md 技术事实

| 核验点 | 证据 | 判定 |
|---|---|---|
| ①「getPermissionList 集合是 checkPermission 的检查源」心智模型 | 官方文档 L791「在进行具体的权限校验之前，你需要实现 StpInterface 接口，告诉框架指定账号拥有的权限码集合是哪些」；L14306 SaSession lazy get 语义；模型正确 | ✅ |
| ② 通配符语义 | llms-full.txt L903-925 逐条对照：`art.*` → `art.add` true / `goods.add` false（L908-910）；`*.delete` → `user.delete` true（L913-914）；`"*"` 上帝权限通过任何权限码（L923-924「拥有 `"*"` 权限时，他可以验证通过任何权限码（角色认证同理）」）——与 03 §4 完全一致 | ✅ |
| ③「角色不自动继承权限，checkRole 只查 getRoleList」 | 官方缓存示例 L15595 将「角色→权限码」映射放在 `getPermissionList` 业务代码内手工完成，证实框架不自动继承；03 §3 表述正确 | ✅ |
| ④ §6 缓存示例 API 真实 | `StpUtil.getSessionByLoginId(loginId)`（llms L1526/L3140/L14106 存在）；`session.get(key, () -> ...)` lazy（llms L14306「如果值为 null，则执行 fun 函数获取值，并把函数返回值写入缓存」）；**实跑新增用例验证**（见 §4）编译运行 + 二次读取命中缓存 | ✅ |
| ⑤ §1/§2/§3 无虚构方法 | `getPermissionList/getRoleList(Object,String)` 两参签名（llms L804/L820）；`hasPermission/checkPermission/checkPermissionAnd/checkPermissionOr`（L845-857）；`hasRole/checkRole/checkRoleAnd/checkRoleOr`（L870-879）——全部真实；§6 中 `permissionMapper` 为业务侧未声明字段，属片段惯例（官方示例同款），非框架方法虚构 | ✅ |

### ✅ R4 02-login-auth.md 完整性

| 核验点 | 证据 | 判定 |
|---|---|---|
| §1~§5 编号连续 | diff 仅在 §1 内删除「典型登录接口」代码块并以引导句替代（现 L12「完整登录流程…见下方『登录流程最佳实践』」），章节号 1-5 未受影响 | ✅ |
| 两个完整示例保留且含判据 | 「标准 Web 应用（Cookie 模式）」含 `StpUtil.checkDisable`（L85）；「前后端分离（Header 模式）」含 `checkDisable`（L103）+ `SaResult.data(StpUtil.getTokenInfo())` 返回 tokenValue（L107） | ✅ |
| 与 10-antipattern 指针有效 | L121「前后端分离未返回 tokenValue、封禁未踢下线 → 10-antipattern.md §3、§8」——§3/§8 均存在且主题吻合 | ✅ |

### ✅ R5 章节重编号/标题改名副作用

| 核验点 | 证据 | 判定 |
|---|---|---|
| 被清理的 12 处无「编号+标题」外部引用 | 全包 grep：`三种模式选型`（12-sso）、`关键选型`（14-plugin §1.3）、`依赖引入规则`（13-micro §1）、`核心价值`（10-antipattern）仅命中自身标题行，无任何跨文件引用；SKILL.md 对 12/13/14 均为文件级引用，未绑定章节号 | ✅ |
| 03 新 §6 无旧章节号引用 | 全包 grep `权限缓存优化`/`RBAC 设计模式`/`典型 RBAC` 零命中；对 03 的引用仅 08-api-stputil L59「详见 03-permission」（文件级）与 03 内部 L35「见 §6」（指向新 §6，正确） | ✅ |
| 全包 26 处 `§n` 引用逐一有效 | 系统检索所有 `§` 引用（SKILL.md 3 处、references 23 处）：01-setup §0、10-antipattern §1/§2/§3/§4/§8/§10/§11/§15/§16/§17/§24、09-pitfalls §6/§10、11-advanced §3.5/§6、14-plugin §1/§4/§6/§7/§8、13-micro §1.2 内部引用——全部指向存在的章节，无失效指针 | ✅ |

### ✅ R6 门禁自洽性（重点）

| 核验点 | 证据 | 判定 |
|---|---|---|
| 6 条执行规则无内部矛盾 | 规则 1（逐字扫描）→ 规则 2（命中即只问）→ 规则 3（选择题形式）→ 规则 4（未答用默认）→ 规则 5（确认即生成）→ 规则 6（多检查点一次问完）为顺序互补关系，无两两冲突 | ✅ |
| C1 默认 vs 强约束 #12 vs 14-plugin §1 口径一致 | C1 默认「有状态 + simple-uuid」= 强约束 #12「有状态默认 simple-uuid + Redis，无需引入 JWT」= 14-plugin §1 概念段「有状态场景用默认 simple-uuid token + Redis 即可，根本无需引入本插件」；C1 无状态=Stateless JWT（不支持踢人/Session/active-timeout）= 强约束 #12 同款 = 14-plugin §1.4 对比表（Stateless：踢人/顶人❌、active-timeout❌、id 反查❌、会话管理❌、封禁❌）；C1/C2/C5 与 12-sso §2 三种模式、14-plugin §1.4 无出入 | ✅ |
| 「用户显式声明无状态/不要 Redis 视为已确认直接 Stateless」与规则 4/5 不冲突 | 规则 5「用户确认方向 → 按选择生成代码」：显式声明本身就是「已确认方向」，走规则 5；规则 4 仅覆盖「未明确回答」情形（此时用默认 simple-uuid 并标注），两者取的是不同用户行为分支，不冲突 | ✅ |
| 自检 9 项与执行规则对应 | 第 1 项（C1–C6 已扫描/已确认/已标默认）对应执行规则 1/2/4；其余 8 项分别对应强约束 #1/#2/#7/#8/#9/#10/#11/#12。9 项中 8 项对应强约束，缺 #3（后端必校验）/ #4（StpInterface 必实现）/ #5（timeout 独立）/ #6（踢人/注销/顶人）——与 v2.2.0 自检清单完全一致，非本轮新引入（见观察项 N2） | ✅ |
| T1 心智推演（登录） | prompt 命中 C3（「登录」+未明确前后端分离）；不命中 C1/C2/C4/C5/C6。按规则 2：本轮只输出确认选择题——① 前端是浏览器渲染页面还是 App/小程序/SPA？② 是否前后端分离？选项 A Cookie 模式（浏览器，推荐）/ B Header 模式（分离），一句话理由；用户答后按规则 5 生成，不答按规则 4 用默认并标注。**流程可执行** | ✅ |
| T7 心智推演（JWT 无状态） | prompt 命中 C1（「无状态」「不依赖 Redis」「自包含可读」），且用户已显式声明无状态+不要 Redis+自包含 → 按 C1 注记视为已确认，直接给 Stateless JWT（`StpLogicJwtForStateless`）方案并明确回答「踢人不支持」（与强约束 #12 / 14-plugin §1.4 一致）。**流程可执行** | ✅ |

### ✅ R7 版本声明一致

| 位置 | 版本 | 判定 |
|---|---|---|
| `skills/sa-token-dev/SKILL.md` front matter `version:` | 2.3.0 | ✅ |
| `plugins/sa-token-dev/.claude-plugin/plugin.json` | 2.3.0 | ✅ |
| `plugins/sa-token-dev/.codex-plugin/plugin.json` | 2.3.0 | ✅ |
| `.claude-plugin/marketplace.json` sa-token-dev 条目 | 2.3.0 | ✅ |
| `.agents/plugins/marketplace.json` sa-token-dev 条目 | 2.3.0 | ✅ |

补充：镜像内容同步核验——`skills/sa-token-dev` 与 `plugins/sa-token-dev/skills/sa-token-dev` 的 SKILL.md 及 02/03/10 等本轮改动文件逐字节 `diff` 一致，两侧文件数均 15。

### ✅ R8 内容包其他一致性

| 核验点 | 证据 | 判定 |
|---|---|---|
| 未触碰文件交叉引用抽查（01/04/06/07/08/09/11） | 01→13-micro 文件级✅、01→07/08/11 文件级✅、01→10-antipattern §1/§10/§11✅、04→14-plugin §4/§7 + 11-advanced §6✅、06→10-antipattern §2✅、07→01-setup §0 + 14-plugin §8 + 10-antipattern §10/§3✅、09→04-annotation + 10-antipattern §17 + 11-advanced §3.5 + 14-plugin✅、08→11-advanced + 03-permission 文件级✅——全部有效，无指向 02 被删示例或 03 旧章节号的失效指针 | ✅ |
| 示例间一致性 | `checkDisable → login` 顺序在 02 两示例、10-antipattern §9、11-advanced §3.5 一致；前后端分离返回 `StpUtil.getTokenInfo()` 在 02/07/10 §3 一致；SB3 `spring.data.redis` 在 SKILL.md/01/07/09/10 §10/12-sso/13-micro 一致（14-plugin §6.1 的 `spring.redis` 明确标注「SB2.x」语境，与前缀规则自洽）；03 §4 通配符示例与官方文档同款 art/goods 写法 | ✅ |
| 无项目专名混入 | 全包 grep `yudao`/`若依`/`ruoyi`/`mall`/`pig-cloud`/外部博客站点 均零命中 | ✅ |

---

## 2. 新引入问题清单

**Defect（阻塞级）：无。** 未发现任何本轮引入的编译错误、API 错误、引用错位、版本标注缺失或技术事实偏差。

观察项（非缺陷，不阻塞发布）：

- **N1（轻微）**：执行规则 2 措辞为「命中任一检查点 → 本轮回复只做一件事：输出确认问题」，而 C1 默认推荐列注记「用户显式声明『无状态/不要 Redis』视为已确认，直接 Stateless」——当用户原始消息即含 C1 触发词时，字面上规则 2 与「直接生成」存在张力。但合理读法可将「显式声明」视为规则 5 的「已确认」，从而不触发规则 2；且该注记内容自 v2.2.0 原样保留，本轮只是把规则 2 措辞加强，非新引入的实质矛盾。建议后续可在规则 2 补充「用户消息中已含明确方向声明的除外」以免歧义。
- **N2（轻微）**：输出前自检 9 项未覆盖核心强约束 #3（后端权限必校验）、#4（StpInterface 必实现）、#5（timeout vs active-timeout 独立）、#6（踢人/注销/顶人区分）。与 v2.2.0 自检清单逐项相同，属既有设计（v2.2.0 措辞为「对照 12 条强约束」而实列 9 项，本轮改为「二值核对 9 项」反而更诚实），非本轮引入。
- **N3（极轻微）**：02 删除的「典型登录接口」（zhang/123456 硬编码）与 01-setup L83-91 最小示例代码几乎相同，后者保留属 setup 文件的最小演示定位，合理；且全包无任何引用指向已删示例。无需处理。

---

## 3. 交叉引用核验

| 检查项 | 结果 |
|---|---|
| SKILL.md 决策路由表 14 个 reference 指针 | 全部有效，对应文件均存在 |
| SKILL.md 使用流程引用（第 0 步/关键决策检查点/决策路由/核心强约束/09/10） | 全部与实际标题一致 |
| SKILL.md「1.46.0 升级必查」三处指针 | `11-advanced.md §3.5`✅ / `09-pitfalls.md §10`✅ / `14-plugin.md`（extraData）✅ |
| 被清理标题（12 处）的外部引用 | 无任何「编号+标题」引用残留 |
| 03 新 §6 / 02 删示例的残留引用 | 无（03 内部「见 §6」指向正确；02 无孤儿指针） |
| 全包 26 处 `§n` 引用 | 逐一核对全部有效 |
| 版本标注 | 5 个 manifest 全部 2.3.0；镜像内容与 skills/ 逐字节一致 |

---

## 4. 实跑复验

- 环境：Docker `redis:7-alpine`（映射 16379）→ fixture `sa-token-demo`（SB 3.5.0 + sa-token 1.46.0，`spring.data.redis`）→ `mvn.cmd test`
- 基线（未改 fixture）：**Tests run: 5, Failures: 0, Errors: 0, Skipped: 0**（与 v2.2.0 相同的 5 用例全绿）
- 现有用例覆盖判断：`session.getList/getSet/getMap`（lazy 重载）已覆盖，但**未覆盖** `session.get(key, supplier)` 与 `getSessionByLoginId` —— 按任务允许在 fixture 增加轻量用例验证 03 §6 示例（改动保留，报告注明）：
  - 新增端点 `permCacheOps`（TestController.java）：逐字复刻 03 §6 模式 `StpUtil.getSessionByLoginId(loginId)` + `session.get("permissionList", () -> List.of("user.add","user.delete"))`，二次读取返回不同 supplier 值以验证缓存命中。
  - 新增测试 `permCache_03_section6_getSessionByLoginId_and_get_supplier`（SessionApiTest.java）：断言首次 supplier 执行并缓存、二次读取命中缓存。
  - 结果：**Tests run: 6, Failures: 0, Errors: 0, Skipped: 0** —— 03 §6 示例在 sa-token 1.46.0 上**可编译、可运行、lazy 语义正确**，直接支撑 R3④。
- 环境清理：Redis 容器已 `docker rm -f`；评审期间生成日志（`mvn-baseline.log` / `mvn-added-test2.log`）保留在 fixture 目录作证据；skill 内容包（skills/ 与 plugins/）未做任何修改。

---

## 5. 结论

**PASS（可发布）。**

R1–R8 八项核验全部通过，均有 git diff / 官方文档 / 实跑三者之一的直接证据支撑：

1. 本轮改动与「纯结构/冗余清理」声明一致：被删内容（同时警告列、主动行为触发 5 条、RBAC 设计模式、典型登录接口、12 处强调后缀）全部删除干净，且其技术事实均能在强约束或其余 references 中找到等价表述，无事实丢失。
2. 未引入新问题：章节重编号/标题改名无跨文件失效指针（全包 26 处 `§n` 引用逐一有效）；03 §6 新增章节无旧引用残留；门禁 6 条执行规则自洽，T1/T7 心智推演流程可执行；版本 5 处声明一致且镜像同步。
3. 实跑支撑：基线 5 用例全绿；新增用例直接验证了 03 §6 缓存示例的 `getSessionByLoginId` + `session.get(key, supplier)` 为 sa-token 1.46.0 真实 API 且 lazy 语义正确。

N1/N2/N3 三个观察项均为既有设计的表述层面事项，不构成发布阻塞。

> 评审期间未修改 skills/ 与 plugins/ 任何内容；仅按任务授权在 eval fixture 中新增了一个验证用例（保留，已注明），Redis 临时容器已清理。
