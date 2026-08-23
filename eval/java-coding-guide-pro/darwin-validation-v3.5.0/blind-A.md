# Blind-A 独立盲评报告（darwin-validation-v3.5.0）

## ① 方法说明

- **读了什么**：`rubric.md`（9 维度标准 + 对抗集判分要点）、`test-prompts.md`（T1–T14 共 14 条 prompt）、`snapshots/version1/`（SKILL.md + references/01–12 共 13 个文件）、`snapshots/version2/`（同构 13 个文件）。全部通读，逐文件比对。
- **版本标识**：version1 快照 frontmatter `version: "3.4.1"`，version2 快照 frontmatter `version: "3.5.0"`。按 rubric 铁律，**不知道也不猜哪个是旧/新**，仅按字面值引用，版本号不影响打分。
- **打分方式**：对每条 prompt，分别把两个快照当作「agent 手里的技能」按 D1–D9（D9 满分 4，其余 12）打分。锚定基准：本技能整体路由清晰、规则密度高，references 完全相同且覆盖完美的 prompt 两版均落 94–95 区间；差异全部来自两版实际存在的文本差异（行号以我读到的快照为准）。
- **个人校准说明**：D1 对「查询规约/坐标」类 prompt（T9/T12/T13/T14）给 10——两版 description 的覆盖清单均未列「命名规约/构件版本」触发词，属两版共同小缺口，不影响两版间比较。

## ② 逐 prompt 打分

### Prompt T1（字符串判空手写 + Optional.get() 裸调）

**版本 1（3.4.1）**
- D1: 11  D2: 11  D3: 11  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: **91/100**
- 依据：
  1. `references/01-null-and-string.md:10-11` 规范速查直接命中 prompt 原句 `str != null && !str.trim().isEmpty()` → `StrUtil.isNotBlank`。
  2. `01:79-95` Optional 节：`findUser(id).get()` → `orElse`/`orElseThrow` 可直接照抄，链式示例齐全。
  3. `01:117-125` + `SKILL.md:143` 含整节「Sonar S3252 与 StrUtil」策略（默认保留 StrUtil，阻断时二选一）——T1 未问此点，但对「写判空」这一高频读取动作附带了条件分支讨论。
- 扣分主因：D6——S3252 策略段在 SKILL.md 主文件与 01 双处出现，对判空主路径是决策噪音（默认虽唯一，段内仍列两套处置选项）。

**版本 2（3.5.0）**
- D1: 11  D2: 11  D3: 11  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **92/100**
- 依据：
  1. `references/01-null-and-string.md:10-11` 速查表与版本 1 相同，`StrUtil.isBlank/isNotBlank` 唯一默认。
  2. `01:77-95` Optional 规范完整（get 禁 → orElse/orElseThrow + 链式）。
  3. `SKILL.md:119` 规则表 A 级行 `== null || .trim().isEmpty()` → 工具方法，与 01 一致。
- 扣分主因：无单点失分；S3252 节删除后判空默认不受影响（符合回归集「特别盯 T1」的判据），仅 D2/D6/D7 按整体基准留 1 分余量。

### Prompt T2（subList 分块 + 分组转 Map + CollUtil.groupBy/shuffle 存在性）

**版本 1（3.4.1）** 与 **版本 2（3.5.0）**（references/02 两版逐字相同）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **95/100**（两版相同）
- 依据：
  1. `references/02-collection-stream.md:16` 分块行：`ListUtil.partition(list, size)`，且点名「`CollUtil.partition` 不存在」；`:33-43` antipattern 1 完整解释 subList 视图/越界。
  2. `02:45-59` antipattern 2 明确「`CollUtil.groupBy` 不存在（编译错误）」→ 默认 `Collectors.groupingBy`；`:60` 直接回答 `CollUtil.shuffle`（用 `Collections.shuffle`）——prompt 三问全部有答案。
  3. `SKILL.md:76-77`（v1）/ `:80-81`（v2）路由表分块/分组两行直达。
- 扣分主因：无显著失分；D2/D6–D8 按整体基准各留 1 分余量（路由表 17 行需扫视等）。

### Prompt T3（static SimpleDateFormat + 裸 LocalDateTime.now() + 遗留 Date）

**版本 1（3.4.1）** 与 **版本 2（3.5.0）**（references/03 两版逐字相同）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **95/100**（两版相同）
- 依据：
  1. `03:27-41` antipattern 1：static SDF 线程不安全 + 明确「ThreadLocal workaround 别用」+ DateTimeFormatter/DateUtil 双方案可抄。
  2. `03:86-100` antipattern 6：裸 `now()` 隐式 JVM 默认时区（S8688）+ ZoneId 常量 / 注入 Clock 两种改法。
  3. `03:127-138` DateUtil 遗留 Date 场景完整（format/parse/offset/between）。
- 扣分主因：无显著失分。

### Prompt T4（UTF-8 读文件 + 复制 + OkHttp GET + JSON 反序列化，纯 Java 项目）

**版本 1（3.4.1）**
- D1: 11  D2: 10  D3: 9  D4: 9  D5: 8  D6: 11  D7: 10  D8: 11  D9: 3
- 小计: **82/100**
- 依据：
  1. `references/04-io-http-json.md:68` HTTP 示例 `private final OkHttpClient client = new OkHttpClient();`——**无任何超时设置**；整个 HTTP 节（`:65-96`）没有「必须显式设超时」的规则行（仅在 `:3` 栈适配注释里以「规则精神（超时必设…）」一笔带过）。
  2. `SKILL.md:63` 高风险表 HTTP 行写着「连接泄漏、**超时缺省**」——断言了危险却在 04 无落地代码，agent 照抄示例会产出无超时客户端，属功能性缺陷（断言与自身示例脱节，D9 同步扣）。
  3. 文件 IO 与 JSON 部分（`04:9-63`、`:98-129`）完整可抄：readUtf8String/copyFile/writeUtf8String 参数顺序陷阱、ObjectMapper 单例 + `readValue(byteStream())` 均齐。
- 扣分主因：D5/D4/D3——HTTP 超时规则缺失 + 示例无超时（超时缺省是不报错、无限等待的隐蔽坑，此版未在 HTTP 节点名），D9 因 SKILL 断言与 04 示例矛盾扣 1。

**版本 2（3.5.0）**
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **95/100**
- 依据：
  1. `04:67` 规则行「客户端必须**显式设置连接/读超时**——默认无超时＝无限等待；实例复用单例」。
  2. `04:70-73` 示例 `new OkHttpClient.Builder().connectTimeout(5, TimeUnit.SECONDS).readTimeout(30, TimeUnit.SECONDS).build()`——可直接照抄。
  3. 文件 IO / JSON 部分与另一版相同（`04:9-63`、`:103-134`），Jackson 反序列化 HTTP 响应 `readValue(resp.body().byteStream())` 齐全。
- 扣分主因：无单点失分，按整体基准留余量。

### Prompt T5（Executors.newFixedThreadPool + CompletableFuture.supplyAsync 链）

**版本 1（3.4.1）** 与 **版本 2（3.5.0）**（references/05 仅差末尾两行 Guava 备注，对 T5 场景无实质影响）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **95/100**（两版相同）
- 依据：
  1. `05:22-43` antipattern 1：newFixedThreadPool 无界队列 OOM + 完整 `ThreadPoolExecutor`（有界队列/命名工厂/CallerRunsPolicy）可抄模板，拒绝策略选择表 `:47-55`。
  2. `05:136-148` CompletableFuture：supplyAsync 必传自定义池、**commonPool 跑阻塞 IO 拖垮全局**的隐蔽坑点名，`get(5, TimeUnit.SECONDS)` 显式超时。
  3. `SKILL.md:100/104`（v1/v2 规则表 S 级行）`Executors.newXxx` → 显式 ThreadPoolExecutor。
- 扣分主因：无显著失分（v1 `05:229-231` 末尾「不引入 Guava」依赖注记为轻量防错信息，不构成扣分差异）。

### Prompt T6（BigDecimal 裸 divide + equals 比较）

**版本 1（3.4.1）** 与 **版本 2（3.5.0）**（references/10 两版逐字相同）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **95/100**（两版相同）
- 依据：
  1. `10:44-51` antipattern 3：裸 divide 除不尽抛 `ArithmeticException`（Non-terminating decimal expansion）→ `divide(bd2, scale, RoundingMode.HALF_UP)`。
  2. `10:53-60` antipattern 4：`equals` 连 scale 一起比（1.0 ≠ 1.00）→ `compareTo == 0`，直接回答 prompt 第二问。
  3. `10:33-42` 构造陷阱（`new BigDecimal(0.1)` 长尾误差）+ 推荐示例 `:116-137` 完整。
- 扣分主因：无显著失分。

### Prompt T7（手搓 MessageDigest + SecureUtil.md5 存密码）

**版本 1（3.4.1）** 与 **版本 2（3.5.0）**（references/07 两版逐字相同）
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **95/100**（两版相同）
- 依据：
  1. `07:23-34` antipattern 1：手搓 hex 漏 `%02x` 前导零丢失致碰撞 → `SecureUtil.md5/sha256`。
  2. `07:36-44` antipattern 2：`SecureUtil.md5(rawPassword)` 存密码=无盐彩虹表 → `BCrypt.hashpw/checkpw`（prompt 原句直接命中）。
  3. `SKILL.md:130-133`（v1）/ `:132-137`（v2）C-CHECK：项目无 crypto 时先询问 + hutool-crypto 坐标（BOM 表 `:135-139` / `:139-143`）。
- 扣分主因：无显著失分。

### Prompt T8（catch 空吞 + log.error 拼接 + Math.random 当订单号）

**版本 1（3.4.1）**
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: **94/100**
- 依据：
  1. `08:48-65` 空 catch 吞异常 + `getMessage()` 可能 null → `ExceptionUtil.getMessage`；`:26-35` 异常日志拼接丢堆栈 → 占位符 + 异常作末参。
  2. `08:196-207` Math.random 当序号：「随机≠唯一，10 万空间约 400 次即 50% 碰撞（生日悖论）」→ 单调发号器完整改法。
  3. `SKILL.md:112-113`（v1）规则表 S 级行带「为什么」列完整复述上述判据——判据在 SKILL.md 与 08 双份重复。
- 扣分主因：D6——规则表 why 列长句（如生日悖论完整论述）与 08 的 antipattern 重复复述，SKILL.md 自称「规则表只是摘要」却承载了正文级论述。

**版本 2（3.5.0）**
- D1: 11  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **95/100**
- 依据：
  1. 08 与另一版逐字相同（`:48-65`、`:26-35`、`:196-207`），三问技术判据全部在 reference 完整保留——符合 rubric「判据在 reference 仍在 → 不扣分」。
  2. `SKILL.md:116-117` 规则表 S 级行为三列结构（无 why 列），判据由 08 承载，摘要定位准确。
  3. `SKILL.md:123` 日志拼接行（A 级）`log.error("x=" + e)` → 占位符 + 异常末参。
- 扣分主因：无单点失分，按整体基准留余量。

### Prompt T9（删最后一处使用后 import 处置 + 五条命名规约在哪）

**版本 1（3.4.1）**
- D1: 10  D2: 11  D3: 12  D4: 10  D5: 11  D6: 9  D7: 11  D8: 11  D9: 4
- 小计: **89/100**
- 依据：
  1. `SKILL.md:124` 规则表 A 级行：「无用 import…移除；**删掉某类最后一处使用时同步删 import**」+ why 列 Sonar java:S1128——第一问规则可查。
  2. `references/11-conventions.md:10-21/35-43/45-54/76-84/103-109`：布尔禁 is（第 1 条）、Abstract|Base（第 3 条）、Exception 结尾（第 4 条）、常量全大写下划线（第 7 条）、long 大写 L（第 9 条）——五问全部覆盖，19 条编号清晰。
  3. `11:1-3` 文件头「来源：阿里巴巴 Java 开发手册（泰山版）精选…」出处行 + `11:291` 第 19 条附「IDE `Optimize Imports`（IDEA: Ctrl+Alt+O）可一键清理」——前者无行动信息，后者是 agent 无法执行的 IDE 快捷键指引。
- 扣分主因：D6（出处标注 + 收录说明占文件头）与 D4（IDE 快捷键指引不可机械执行）。

**版本 2（3.5.0）**
- D1: 10  D2: 11  D3: 12  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **92/100**
- 依据：
  1. `SKILL.md:128` 规则表 A 级行：「无用 import（未使用/重复/java.lang/同包；Sonar java:S1128）残留 → 移除；删掉某类最后一处使用时同步删 import」——判据折入单元格，第一问一次可查。
  2. `references/11-conventions.md` 19 条规则本体与另一版逐字相同（第 1/3/4/7/9 条见 `:8-20/33-41/43-51/74-81/102-107`）。
  3. `11:1-4` 文件头仅剩「与现有 reference 不重复」的交叉引用指针，无出处行；`:278-288` 第 19 条无 IDE 指引。
- 扣分主因：无单点失分（D1 的 10 为两版共同缺口：description 未列「命名规约」触发词）。

### Prompt T10（JDK 8/11/16/17/21/25 × 7 特性逐一判定 + VT synchronized）

**版本 1（3.4.1）**
- D1: 10  D2: 10  D3: 12  D4: 8  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: **87/100**
- 依据：
  1. `SKILL.md:43-51`「JDK 版本策略（五档 LTS 语义）」为累加式表述：「JDK 11：+ var(10)、HttpClient(11)」「JDK 17：+ switch 表达式(14)、文本块(15)、record(16)、sealed(17)…」——档位编号与括号内实际版本**两套编号混排**，回答「JDK 17 能用什么」需串联 8+11+17 三行，回答 JDK 11 需串联两行。
  2. 「JDK 16（非 LTS）能否用 record」在此版 SKILL.md 无判据：五档只有 8/11/17/21/25，`references/09-modern-java.md:5`「非 LTS 不单独门控」也未给出非 LTS 目标的比较规则——只能靠 `09:18` 特性表（record 门控 16）由 agent 自行推断 16 ≥ 16。
  3. VT synchronized 21 钉住/25 解除（JEP 491）在 `09:70-87` antipattern 3 完整（含两版对比代码）——该子问题答案不缺。
- 扣分主因：D4——门控判据需多行串联心算且非 LTS 目标无明确判据语句（特性→最低版本的单条比较规则此版 SKILL.md 未给出，只在 09 隐含）。

**版本 2（3.5.0）**
- D1: 10  D2: 11  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **93/100**
- 依据：
  1. `SKILL.md:49` 单条判据「**目标 JDK ≥ 特性最低版本 → 可用；低于 → 禁用**」+「非 LTS 目标同样按版本比较，不另设档位」——JDK 16 vs record(16)：一次比较出结果。
  2. `SKILL.md:51-61` 特性→最低 JDK 平表（var 10 / HttpClient 11 / switch 14 / 文本块 15 / record+toList 16 / sealed 17 / VT 21 / 22–24 转正 25），7 个待查特性全覆盖。
  3. `SKILL.md:63` 直接给出「虚拟线程 + synchronized 在 21 会钉住载体线程（改 ReentrantLock），25 解除（JEP 491）」——SKILL.md 层即可答，无需跳 09。
- 扣分主因：无单点失分（D1 的 10 为查询类 prompt 的共同余量）。

### Prompt T11（StrUtil vs CharSequenceUtil + S3252 门禁处理）

**版本 1（3.4.1）**
- D1: 10  D2: 11  D3: 12  D4: 11  D5: 11  D6: 9  D7: 11  D8: 11  D9: 4
- 小计: **90/100**
- 依据：
  1. `01:10` 速查表唯一默认 `StrUtil.isBlank`；`01:117-119` 明确「默认继续写 StrUtil，不主动改写」——第一问答案明确。
  2. `01:121-125` + `SKILL.md:143`：S3252 门禁阻断时的完整处置（① 平台标 Accepted/配规则例外（推荐）② 全局换 `CharSequenceUtil`；禁混用、禁逐处 NOSONAR）——第二问技能内有方案可答。
  3. 同一策略段在 SKILL.md 主文件与 01 双处出现，且含条件分支（「仅当门禁启用且阻断时」）与两套选项——对「写判空」这一高频动作附加了决策路径。
- 扣分主因：D6——高频动作上的策略分支讨论双处复述（虽默认唯一，rubric 预期的决策疲劳形态在此版成立，扣 2 分并部分抵消其 D3 优势）。

**版本 2（3.5.0）**
- D1: 10  D2: 11  D3: 10  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: **91/100**
- 依据：
  1. `01:10` 唯一默认 `StrUtil.isBlank(str)`；`SKILL.md:79` 路由行「有 Hutool 用 StrUtil」——第一问无歧义、零分支。
  2. 全文（SKILL.md + 01 + 全部 references）无 S3252 / CharSequenceUtil 任何出现——第二问「门禁扫出来怎么办」技能内无方案（按 rubric：该知识不属编码指南职责，不扣重分，D3 扣 2）。
  3. `SKILL.md:28-33` 三条铁律之「一域一默认：每个场景只给唯一推荐…不列举或 A 或 B」与本文件实际行为一致。
- 扣分主因：D3——prompt 第二问在技能内不可答（职责外，轻扣）。

### Prompt T12（C-CHECK 触发范围 + OkHttp3 客户端建法与超时）

**版本 1（3.4.1）**
- D1: 10  D2: 10  D3: 9  D4: 8  D5: 8  D6: 11  D7: 10  D8: 11  D9: 3
- 小计: **80/100**
- 依据：
  1. 第一问可答：`SKILL.md:130`「任务确实需要加密/哈希/密码…或 Bean 映射…才向用户询问；低风险场景永不询问」+ `:66` 低风险四类列举（判空/集合/随机/日期）。
  2. 第二问功能性缺陷：`04:68` 示例 `new OkHttpClient()` 无超时，HTTP 节无超时规则行——「客户端怎么建？超时怎么设？」照抄示例即产出无限等待的客户端；`SKILL.md:63` 高风险表反而把「超时缺省」列为手写危险，断言与示例自相矛盾（D9 扣 1）。
  3. `04:3` 仅栈适配注释提到「规则精神（超时必设…）仍然适用」——无规则行、无落地代码，属「只有断言没有可照抄代码」。
- 扣分主因：D4/D5/D3 重扣（rubric 对抗集规则：超时规则只有断言无落地 = 功能性缺陷，≤4 分档）。

**版本 2（3.5.0）**
- D1: 10  D2: 11  D3: 12  D4: 12  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **94/100**
- 依据：
  1. 第一问：`SKILL.md:134` 触发条件（仅加密/Bean 映射询问、低风险永不）+ `:69-70` 风险分级重申「其余场景 JDK 原生/Spring 自带即可覆盖，不询问」——两问范围一次说清。
  2. 第二问：`04:67` 规则行（必须显式设连接/读超时，默认无超时=无限等待）+ `04:70-73` 带超时的 Builder 单例示例，可直接照抄。
  3. `SKILL.md:151` 构件表 OkHttp3 4.12.0（纯 Java 项目 HTTP）与 04 呼应，坐标与代码同版可查。
- 扣分主因：无单点失分（D1 查询类余量）。

### Prompt T13（六个技术判据删除 why 列后是否仍可查）

**版本 1（3.4.1）**
- D1: 10  D2: 12  D3: 12  D4: 11  D5: 12  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: **93/100**
- 依据（六判据全部位于 SKILL.md 规则表「为什么」列，一次全查到）：
  1. `SKILL.md:101`「线程不安全；**月从 0**」（①）；`:109`「Spring 与 Apache 参数顺序相反，记错静默拷空」（②）。
  2. `SKILL.md:120` why 列「手算边界易错（**半开区间**）」+ `08:191-194`「[min, max) 半开，不含 max」（③）；`:119`「隐式依赖 JVM 默认时区…Sonar java:S8688」（④）。
  3. `SKILL.md:124`「Sonar java:S1128」（⑤）；`:125`「Sonar java:S3776（阈值 15）」（⑥）——六条无一丢失。
- 扣分主因：D6——why 列混合了技术判据与复述性散文（如 `:118`「拼接在日志关闭时也执行」重述 08 已有内容），列内信息密度低于折入式。

**版本 2（3.5.0）**
- D1: 10  D2: 12  D3: 12  D4: 11  D5: 12  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **94/100**
- 依据（六判据全部折入 ✗/✓ 单元格，一次全查到）：
  1. `SKILL.md:105`「Calendar 手算（**月份从 0 起**）」（①）；`:113`「BeanUtils.copyProperties 未确认源/目标顺序（**Spring 与 Apache 参数顺序相反**）」（②）。
  2. `SKILL.md:124`「RandomUtil.randomInt(min, max)（**[min, max) 半开**）」（③）；`:123`「裸 LocalDateTime.now()…（**隐式 JVM 默认时区**；Sonar java:S8688）」（④）。
  3. `SKILL.md:128`「（…Sonar java:S1128）」（⑤）；`:129`「（Sonar java:S3776 认知复杂度阈值 15）」（⑥）——无一条判据因删列而消失，且全部保留在摘要层。
- 扣分主因：无单点失分；折入完整、密度更高（D6 较四列版 +1）。

### Prompt T14（JDK 8 / JDK 17 日志坐标 + 禁混用 + 四构件版本）

**版本 1（3.4.1）**
- D1: 10  D2: 9  D3: 9  D4: 9  D5: 10  D6: 11  D7: 9  D8: 11  D9: 4
- 小计: **82/100**
- 依据：
  1. `SKILL.md:141` 全部版本挤一行 blockquote prose：「MapStruct 1.5.5.Final（需 annotation processor）、Jackson 2.17.1、OkHttp3 4.12.0、Lombok 1.18.34、SLF4J 2.0.13（JDK 8 用 1.7.36）**+ Logback**」——Logback 无版本号、无「两套禁混用」警示。
  2. JDK 8 的完整组合（SLF4J 1.7.36 + **Logback 1.2.x**）与禁混用警示只在 `08:250`（「Logback 1.5.x 需 JDK 11+…1.2.x 已 EOL…两套不可混用」）——回答需跨 SKILL.md + 08 两处拼接。
  3. `08:249` 写「坐标与 JDK 门控见 SKILL.md『C-CHECK』」而 SKILL.md 该处并无 Logback 门控全貌——形成 SKILL→08→SKILL 的循环跳转（D7 扣）。
- 扣分主因：D3/D4——Logback 版本与 JDK 8 组合在 SKILL.md 不全，跨文件拼接有选错依赖组合风险（rubric 对抗集功能性缺陷档）。

**版本 2（3.5.0）**
- D1: 10  D2: 12  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: **94/100**
- 依据：
  1. `SKILL.md:145-153` 构件三列小表（构件/参考版本/门控备注）：MapStruct 1.5.5.Final（需 annotation processor）、Jackson 2.17.1、OkHttp3 4.12.0、Lombok 1.18.34 逐行可查。
  2. `SKILL.md:153` SLF4J + Logback 行：「2.0.13 + 1.5.x｜需 JDK 11+；**JDK 8 用 SLF4J 1.7.36 + Logback 1.2.x，两套禁混用**（见 references/08）」——两套组合 + 禁混用一次查全。
  3. `08:250` 保留禁混用原因（运行期 "no SLF4J provider"）作深层依据，与 SKILL.md 表形成「摘要→详情」单向导航。
- 扣分主因：无单点失分（D1 查询类余量；D5 的 11 因禁混用后果细节仍在 08）。

## ③ 汇总表

| Prompt | 场景 | version1 小计 | version2 小计 | 差值 (v2−v1) |
|---|---|---|---|---|
| T1 | 判空 + Optional | 91 | 92 | +1 |
| T2 | 集合分块/分组 | 95 | 95 | 0 |
| T3 | 日期格式化/now | 95 | 95 | 0 |
| T4 | IO/HTTP/JSON | 82 | 95 | +13 |
| T5 | 线程池/异步 | 95 | 95 | 0 |
| T6 | BigDecimal | 95 | 95 | 0 |
| T7 | 加密/密码 | 95 | 95 | 0 |
| T8 | 异常/日志/随机 | 94 | 95 | +1 |
| T9 | import/命名规约可查性 | 89 | 92 | +3 |
| T10 | JDK 门控判据 | 87 | 93 | +6 |
| T11 | StrUtil 默认/S3252 | 90 | 91 | +1 |
| T12 | C-CHECK 范围/HTTP 超时 | 80 | 94 | +14 |
| T13 | 六判据可查性 | 93 | 94 | +1 |
| T14 | 构件版本/日志门控 | 82 | 94 | +12 |
| **总分（14 条 × 100）** | | **1263** | **1315** | **+52** |

## ④ 两版最大差异点（客观陈述，不判新旧）

1. **HTTP 超时（影响 T4/T12，单条差 13–14 分，最大差异）**：version1 的 `04-io-http-json.md:68` OkHttp 示例为 `new OkHttpClient()` 且 HTTP 节无任何超时规则行，而其 SKILL.md 高风险表（`:63`）自己声明「HTTP 调用｜连接泄漏、超时缺省」——断言与示例脱节；version2 在 `04:67` 增加规则行、`:70-73` 示例改为带 `connectTimeout(5s)/readTimeout(30s)` 的 Builder。
2. **构件版本表（影响 T14，差 12 分）**：version1 把全部版本压缩为 SKILL.md 一行 prose，Logback 无版本号、无禁混用警示，完整门控要跳 08 拼接（且 08 反向指回 SKILL.md 形成循环）；version2 改为三列表，SLF4J+Logback 行含两套组合与「两套禁混用」。
3. **JDK 门控表述（影响 T10，差 6 分）**：version1 为「五档累加 + 括号内实际版本」双编号混排，非 LTS（如 JDK 16）无明确判据语句；version2 为「特性→最低 JDK」平表 + 单条比较判据 + 「非 LTS 同样按版本比较」，且 VT+synchronized 的 21/25 差异上提到 SKILL.md 层。
4. **规则表结构（影响 T8/T13，各差 1 分）**：version1 四列（含「为什么」列，判据与复述散文混排）；version2 三列，六条技术判据全部折入 ✗/✓ 单元格，无一条丢失（T13 逐一核验：月份从 0、参数顺序相反、半开区间、隐式时区/S8688、S1128、S3776 阈值 15 两版均可查）。
5. **S3252 策略段（影响 T11，净差仅 1 分）**：version1 在 SKILL.md 尾注 + 01 末节双处保留完整处置方案（可答「门禁扫出来怎么办」，但对高频判空引入分支讨论）；version2 完全删除，默认唯一 StrUtil、密度更高，代价是门禁追问技能内无答案——两向相抵。
6. **11-conventions 文件头（影响 T9，差 3 分）**：version1 带「来源：阿里巴巴 Java 开发手册（泰山版）」出处行与 IDE `Ctrl+Alt+O` 快捷键指引；version2 均删，19 条规则本体两版逐字相同。
7. **高风险场景表（影响小）**：version1 为六行三列表（含「为什么手写危险」列）；version2 压缩为高风险/低风险两个 bullet 段，C-CHECK 触发范围反而更集中明确（T12 第一问两版均可答）。
8. **其他**：version2 的 description 次级触发信号分「代码信号/用户任务词」两组且更细；version1 的 `05-concurrency.md` 末尾多两行「不引入 Guava」依赖注记（version2 删）；两版 references 中 02/03/05(除末尾)/06/07/08/09/10/12 逐字或近乎逐字相同。

**总体观察**：version1 的失分集中在三处「断言无落地 / 信息不全需跨文件拼接」（HTTP 超时、构件版本、JDK 非 LTS 判据）与三处冗余（why 列散文、出处/IDE 指引、S3252 双段）；version2 在全部 14 条 prompt 上不低于 version1（6 条持平、8 条更高），未发现 version2 相对 version1 的任何退步点。
