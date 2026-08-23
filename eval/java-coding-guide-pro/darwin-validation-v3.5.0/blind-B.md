# Blind-B 独立盲评报告（darwin-validation-v3.5.0）

## ① 方法说明

- 只读了 4 个允许位置：`rubric.md`、`test-prompts.md`、`snapshots/versionA/`（SKILL.md + references 01~12）、`snapshots/versionB/`（同构 13 个文件），共 26 个文件全文。未读 git 历史、仓库其他目录、eval/ 其他内容。
- 两版 frontmatter 字面值：versionA = `3.4.1`，versionB = `3.5.0`。按 rubric 铁律，版本号只作标识、不影响打分，我也不知道（也不猜）哪个是旧/新。
- 打分方式：把每版整套技能（SKILL.md + 12 个 references）当作 agent 手里的全部材料，对 14 条 prompt 按 9 维度（D1~D8 各 12 分、D9 4 分）独立打分；每条给 ≤3 条带文件:行号的依据。
- 两版 references 大部分文件逐字相同（03/06/07/09/10/12 完全一致；02/05/08 仅差出处标注；01 差 S3252 节；04 差 HTTP 超时；11 差来源头与 IDE 指引）。差异集中在 SKILL.md 与 01/04/11。

## ② 逐 prompt 打分

### Prompt T1（字符串判空 + Optional.get 取值，域 01）

**versionA（3.4.1）**
- D1: 11  D2: 10  D3: 11  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 90/100
- 依据:
  1. `references/01-null-and-string.md:10-11` 规范速查两行精确命中 prompt 代码形态（`str != null && !str.trim().isEmpty()` → `StrUtil.isNotBlank`）。
  2. `01:79-95` Optional 节含 `findUser(id).get()` 原样反例 → `orElse`/`orElseThrow` 可照抄代码。
  3. SKILL.md:108（S 级 `Optional.get()` 行）与 :115（A 级手写判空行）双层兜底，路由 :74-75 指向 01。
- 扣分主因: D6——SKILL.md:143 + `01:117-125` 的 Sonar S3252 策略段对「写判空」主路径是额外分支负担（判空默认本身未受影响，符合 rubric「主路径不受影响」的判定）。

**versionB（3.5.0）**
- D1: 11  D2: 10  D3: 11  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 91/100
- 依据:
  1. `references/01-null-and-string.md:10-11` 同 A，判空速查表完全保留；:31-38 空格陷阱反例仍在。
  2. `01:77-95` Optional 节与 A 逐字一致，get()/orElse 代码可直接照抄。
  3. SKILL.md:112/119（S 级 Optional.get、A 级手写判空行）仍在；01 文件更短（115 行 vs A 的 125 行），无 S3252 尾巴。
- 扣分主因: 仅常规往返跳转成本（SKILL 路由表 → 01 两步），无功能性损失；判空默认 `StrUtil.isBlank` 全表唯一。

### Prompt T2（集合分块 + 分组 + groupBy/shuffle 可用性，域 02）

**versionA（3.4.1）**
- D1: 11  D2: 10  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 91/100
- 依据:
  1. `references/02-collection-stream.md:16` + :33-43：`subList` 视图陷阱与 `ListUtil.partition(list, 50)` 修正代码（prompt 原参数 50）。
  2. `02:52-53` 直接回答 `CollUtil.groupBy` 不存在（编译错误）→ `Collectors.groupingBy`；:60 直接回答 `CollUtil.shuffle` 不存在（用 `Collections.shuffle`）。
  3. `02:18-19` 分组/转 Map 默认 JDK Stream，SKILL.md:76-77 路由一致。
- 扣分主因: D6——`02:118`、`:137` 标题带「（阿里）」出处标注（无行动信息）；其余与 B 逐字相同。

**versionB（3.5.0）**
- D1: 11  D2: 10  D3: 12  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 92/100
- 依据:
  1. `references/02-collection-stream.md:16`、:39-42 分块在 `ListUtil` 的强调与示例与 A 一致。
  2. `02:45-60` `groupBy`/`shuffle`/`toMap` 三个「CollUtil 上不存在」误用逐一点名（prompt 的两个问句都有直接答案）。
  3. 同 A 的 :149-170 Stream 节（含 toList() 不可变门控）。
- 扣分主因: 无明显失分；出处标注已去除，仅余常规两步跳转。

### Prompt T3（共享 SimpleDateFormat + 裸 now() + 遗留 Date，域 03）

**versionA（3.4.1）**
- D1: 11  D2: 10  D3: 12  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 92/100
- 依据:
  1. `references/03-date-time.md:27-41` antipattern 1 原样命中 `private static final SimpleDateFormat SDF`，并点名 ThreadLocal workaround 别用。
  2. `03:86-102` antipattern 6 裸 `now()` 隐式 JVM 默认时区 + S8688 + `now(ZONE)`/注入 Clock 两套修正代码。
  3. `03:12`、:127-138 遗留 `Date` → `DateUtil`（prompt 第三问）。
- 扣分主因: 无退步迹象；仅常规跳转成本。

**versionB（3.5.0）**
- D1: 11  D2: 10  D3: 12  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 92/100
- 依据: `references/03-date-time.md` 与 versionA 逐字相同（1-139 行比对一致）。
- 扣分主因: 同 A（文件级无差异，分数持平）。

### Prompt T4（UTF-8 读文件 + 复制 + HTTP GET + JSON 反序列化，纯 Java，域 04）

**versionA（3.4.1）**
- D1: 11  D2: 10  D3: 11  D4: 9  D5: 8  D6: 11  D7: 11  D8: 11  D9: 3
- 小计: 85/100
- 依据:
  1. `references/04-io-http-json.md:13-23` 文件 IO 速查（readUtf8String/copyFile）+ :98-118 Jackson 单例与 `readValue(byteStream)` 完整覆盖 prompt 前半。
  2. `04:68` HTTP 客户端示例为 `new OkHttpClient()`——**未设任何超时**；prompt 涉及发 HTTP，SKILL.md:63 虽断言「连接泄漏、超时缺省」危险，但域文件无可照抄的超时代码。
  3. SKILL.md:63（高风险表「超时缺省」）与 04:68 示例自相矛盾——照抄示例即违反自家断言。
- 扣分主因: D4/D5/D9——超时规则「只有断言没有落地」，agent 按域文件示例写出的客户端无超时（隐蔽不 fail loud），且 SKILL 断言与 04 示例内部打架。

**versionB（3.5.0）**
- D1: 11  D2: 10  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 依据:
  1. `references/04-io-http-json.md:67` 规则行「客户端必须显式设置连接/读超时——默认无超时＝无限等待；实例复用单例」。
  2. `04:70-73` 示例含 `.connectTimeout(5, TimeUnit.SECONDS).readTimeout(30, TimeUnit.SECONDS)`，可直接照抄；GET/try-with-resources/404 处理齐备。
  3. 文件 IO 与 JSON 节与 A 相同（:13-23、:105-122），prompt 四个子任务全部一次命中。
- 扣分主因: 无功能性失分；仅 SKILL→04 两步跳转的常规成本。

### Prompt T5（newFixedThreadPool(10) + supplyAsync 链，域 05）

**versionA（3.4.1）**
- D1: 11  D2: 10  D3: 12  D4: 12  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 92/100
- 依据:
  1. `references/05-concurrency.md:22-43` 无界队列 OOM 反例 + 显式 `ThreadPoolExecutor`（有界队列+命名工厂+CallerRunsPolicy）完整模板，prompt 的 `newFixedThreadPool(10)` 原样出现。
  2. `05:134-148` `supplyAsync` 必传自定义池（commonPool 禁跑阻塞 IO）+ `future.get(5, TimeUnit.SECONDS)` 显式超时。
  3. SKILL.md:100 S 级行与 05 一致。
- 扣分主因: D6——`05:100`、:118「（阿里规约）」标注 + :229-231「## 依赖」Guava 备注段（对 T5 无行动价值）+ :35/:204 代码注释里的「（不依赖 Guava）」。

**versionB（3.5.0）**
- D1: 11  D2: 10  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 依据:
  1. `references/05-concurrency.md:22-55` 与 A 主体逐字相同（模板、拒绝策略表、覆盖默认说明）。
  2. `05:134-148` CompletableFuture 节同 A；:150-162 虚拟线程门控 + synchronized pin 21/25 差异齐备。
  3. 文件尾无 Guava 备注段（A 的 229-231 已去除），代码注释只剩必要语义。
- 扣分主因: 无；仅常规跳转成本。

### Prompt T6（bd1.divide 裸除 + BigDecimal.equals 比较，域 10）

**versionA（3.4.1）**
- D1: 11  D2: 10  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 依据:
  1. `references/10-bigdecimal.md:44-51` 裸 `divide` → `ArithmeticException`（Non-terminating decimal expansion）+ `divide(bd2, scale, RoundingMode.HALF_UP)` 修正——prompt 第一问直接答案。
  2. `10:53-60` `equals` 连 scale 一起比（1.0 ≠ 1.00）→ `compareTo`——prompt 第二问直接答案，示例值与 prompt 相同。
  3. SKILL.md:102 S 级行（裸 divide/bd.equals）双层兜底。
- 扣分主因: 无明显失分。

**versionB（3.5.0）**
- D1: 11  D2: 10  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 依据: `references/10-bigdecimal.md` 与 versionA 逐字相同（1-152 行一致）。
- 扣分主因: 同 A（文件级无差异，分数持平）。

### Prompt T7（手搓 MessageDigest + SecureUtil.md5 存密码，域 07）

**versionA（3.4.1）**
- D1: 10  D2: 10  D3: 12  D4: 12  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 91/100
- 依据:
  1. `references/07-crypto.md:23-34` 手搓 `MessageDigest` 漏 `%02x` 前导零丢失 → `SecureUtil.md5/sha256`，prompt 代码原样命中。
  2. `07:36-44` `SecureUtil.md5(rawPassword)` 存密码 → `BCrypt.hashpw/checkpw`（含 log_rounds 说明）。
  3. SKILL.md:128-133 C-CHECK 触发条件（加密能力缺失才询问）+ :135-139 hutool-crypto 坐标表。
- 扣分主因: D1（description 无「密码/哈希存储」任务词，仅代码信号）+ D6（SKILL.md:59 高风险表 why 列与 07 内容部分重复）。

**versionB（3.5.0）**
- D1: 11  D2: 10  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 依据:
  1. `references/07-crypto.md` 与 A 逐字相同（%02x 陷阱 :23-34、BCrypt :36-44、密钥管理 :89-98）。
  2. SKILL.md:18-19 description 明确含任务词「生成验证码 / token / 盐、密码加密 / 哈希存储」——T7 这类提问更容易命中触发。
  3. SKILL.md:69 风险分级把「加密缺能力 → C-CHECK 询问」压成一句可执行规则；:139-143 坐标表同 A。
- 扣分主因: 无功能性失分。

### Prompt T8（空吞 catch + log.error 拼接 + Math.random 当订单号，域 08）

**versionA（3.4.1）**
- D1: 11  D2: 10  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 91/100
- 依据:
  1. `references/08-exception-logging.md:28-35` `log.error("失败: " + e.getMessage())` 原样反例 → 占位符 + 异常作末参（丢堆栈 + getMessage 可能 null 双陷阱点名）。
  2. `08:48-65` 空 catch → 记日志+透传/包装；SKILL.md:107 S 级行兜底。
  3. `08:196-207` `(Math.random()*100000)` 当序号 → 随机≠唯一（10 万空间约 400 次 50% 碰撞）+ 单调发号器修正代码——prompt 第三个问题的完整答案在 reference 层保留（rubric T8 特别盯项：判据未消失，不扣 D3/D5）。
- 扣分主因: D6——`08:67`、:121「（阿里规约）」「（阿里 + SonarQube）」出处标注；SKILL.md:112 why 列与 08 重复（「随机≠唯一」两处出现）。

**versionB（3.5.0）**
- D1: 11  D2: 10  D3: 12  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 92/100
- 依据:
  1. `references/08-exception-logging.md` 与 A 逐字相同（除两处出处标注已删）；:186-194 `randomInt(min,max)` [min, max) 半开判据、:196-207 随机≠唯一判据均在。
  2. SKILL.md:116-117 S 级行删 why 列后判据「（如 `(int)(Math.random()*100000)` 当 seq）」折入 ✗ 单元格；生日悖论判据在 08:198 完整保留——技术判据无丢失。
  3. SKILL.md:122 日志拼接行修正写法（`log.error("x={}", x, e)`）可直接照抄。
- 扣分主因: 无；仅 SKILL→08 两步跳转。

### Prompt T9（对抗：删最后一处使用后 import 怎么办 + 命名规约在哪）

**versionA（3.4.1）**
- D1: 9  D2: 11  D3: 12  D4: 10  D5: 10  D6: 9  D7: 10  D8: 11  D9: 4
- 小计: 86/100
- 依据:
  1. SKILL.md:124 A 级行「无用 import…｜移除；删掉某类最后一处使用时同步删 import」——①问的规则在（且 `11:280-291` 第 19 条四类无用 import + Agent 高频坑注释重复出现）。
  2. `references/11-conventions.md:10-23`（布尔禁 is）、:35-43（Abstract|Base）、:45-54（Exception 结尾）、:76-84（常量全大写下划线）、:104-110（long 大写 L）——②问五项全部可查。
  3. `11:291`「IDE `Optimize Imports`（IDEA: Ctrl+Alt+O）可一键清理」——agent 无法执行 IDE 快捷键，属不可执行指引。
- 扣分主因: D6/D4——11 文件头部「来源：阿里巴巴 Java 开发手册（泰山版）精选」出处行（:1-4）+ 同步删 import 规则跨文件重复（SKILL:124 与 11:291 两处）+ IDE 快捷键指引；规则本体可查但被噪音包裹。

**versionB（3.5.0）**
- D1: 9  D2: 11  D3: 12  D4: 11  D5: 10  D6: 11  D7: 10  D8: 11  D9: 4
- 小计: 89/100
- 依据:
  1. SKILL.md:128 A 级行「无用 import（未使用/重复/java.lang/同包；Sonar java:S1128）残留｜移除；**删掉某类最后一处使用时同步删 import**」——判据折入单元格后规则完整保留（rubric T9 正确回答①）。
  2. `references/11-conventions.md` 19 条规则本体与 A 逐字相同（:8-19、:33-41、:43-51、:74-82、:102-108），布尔/抽象类/异常类/常量/long 五项全中。
  3. `11:278-288` 第 19 条结尾无 IDE 指引、无出处行（标题从「（阿里巴巴 Java 开发手册吸收）」改为「命名与编码规约」），规则可查性与 A 相同但更干净。
- 扣分主因: D1——description 未收录「命名规约/import」类触发词（两版同样，靠通用「审查任何 Java 代码」兜底）。

### Prompt T10（对抗：JDK 8/11/16/17/21/25 逐档可用性 + record@16 + synchronized@21/25）

**versionA（3.4.1）**
- D1: 11  D2: 10  D3: 12  D4: 7  D5: 9  D6: 10  D7: 11  D8: 11  D9: 3
- 小计: 84/100
- 依据:
  1. SKILL.md:43-51「五档 LTS 语义」：`record(16)` 列在「**JDK 17**」档下（:47），档位编号与括号内实际版本两套混排——对「JDK 16 能否用 record」需自行串联并甄别两套编号，第一站表述易误导为「record 需要 17」。
  2. SKILL 层非 LTS 目标（如 JDK 16）无明确判据；:51 只说「门控只标 LTS」。要到 `09-modern-java.md:18`（record 门控 16 平表行）才能一次比较出结果。
  3. `09:70-87` synchronized pin 21/25（JEP 491）两版都有，T10 后半问可答。
- 扣分主因: D4——判据需多行累加心算 + 档位/实际版本双编号，非机械可执行；SKILL:47 的归类方式对 JDK 16 目标构成误导风险（D9 同因：SKILL 五档与 09 平表两套口径并存）。

**versionB（3.5.0）**
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 95/100
- 依据:
  1. SKILL.md:49 单条判据「目标 JDK ≥ 特性最低版本 → 可用；低于 → 禁用」+「非 LTS 目标同样按版本比较，不另设档位」——JDK 16 用 record：16 ≥ 16 → 可用，一次比较出结果。
  2. SKILL.md:51-61「特性 → 最低 JDK」平表：var 10 / HttpClient 11 / switch 14 / 文本块 15 / record+toList 16 / sealed 17 / 虚拟线程 21 / `_`+Gatherers 25，七问逐个直查。
  3. SKILL.md:63 虚拟线程 synchronized「21 钉住（改 ReentrantLock），25 解除（JEP 491）」内联在门控节，无需跳转即答后半问。
- 扣分主因: 无明显失分。

### Prompt T11（对抗：StrUtil 还是 CharSequenceUtil + S3252 扫出来怎么处理）

**versionA（3.4.1）**
- D1: 10  D2: 11  D3: 11  D4: 11  D5: 12  D6: 9  D7: 10  D8: 11  D9: 4
- 小计: 89/100
- 依据:
  1. SKILL.md:143-145 + `references/01-null-and-string.md:117-125`：S3252 策略段完整——默认保留 `StrUtil`（官方门面），仅当门禁启用且阻断时二选一（标 Accepted/配例外（推荐）或全局换 `CharSequenceUtil`），禁混用、禁逐处 NOSONAR——T11 两问都有技能内答案。
  2. `01:4` 头部注明「StrUtil（继承 CharSequenceUtil）」背景信息；判空速查 :10-11 全表唯一默认 `StrUtil.isBlank`。
  3. `01:125` 还覆盖同类门面（DateUtil/ArrayUtil）同策略。
- 扣分主因: D6——该策略段为「写判空」高频动作引入条件分支（门禁阻断才动作），且 SKILL 与 01 双文件重复；但作为防错信息有效（判其为有效陷阱知识，故 D5 给满）。

**versionB（3.5.0）**
- D1: 10  D2: 10  D3: 9  D4: 11  D5: 10  D6: 12  D7: 10  D8: 11  D9: 4
- 小计: 87/100
- 依据:
  1. `references/01-null-and-string.md:10-11` 判空默认唯一且明确：`StrUtil.isBlank`/`isNotBlank`；SKILL.md:78-79 路由同口径——T11 第一问回答干净（「一域一默认」铁律 SKILL.md:33）。
  2. 全套件 grep 无任何 S3252/CharSequenceUtil 内容（01 止于 :115，SKILL 无该节）——「Sonar 门禁开了 S3252 怎么处理」在技能内无方案。
  3. 按 rubric T11 判定：该追问不属编码指南职责、无该节不扣重分——故 D3 中度扣而非重扣。
- 扣分主因: D3——S3252 追问在技能内不可查（对照 A 版可答）；主路径默认明确性优于 A（D6 满分）。

### Prompt T12（对抗：C-CHECK 触发范围 + OkHttp3 客户端与超时在哪）

**versionA（3.4.1）**
- D1: 10  D2: 10  D3: 9  D4: 7  D5: 7  D6: 11  D7: 10  D8: 11  D9: 3
- 小计: 78/100
- 依据:
  1. ①问可答：SKILL.md:128-130 C-CHECK 节「加密/哈希/密码 或 Bean 映射 才询问；低风险场景永不询问」；:57-66 表格同口径（低风险 :66 明示不询问）。
  2. ②问半残：SKILL.md:63 断言 HTTP「连接泄漏、超时缺省」危险，但 `references/04-io-http-json.md:68` 的 OkHttp 单例示例 `new OkHttpClient()` **未设任何超时**——「超时怎么设」无规则行、无示例，属断言无落地（rubric 判 D4/D5 扣）。
  3. SKILL:63 与 04:68 的矛盾同时伤一致性（agent 若先读 04 会得出「不需要设超时」的错误结论）。
- 扣分主因: D4/D5/D9——HTTP 超时为功能性缺口：示例代码与技能自身断言相反，照抄即产出缺省无限等待的客户端（隐蔽不 fail loud）。

**versionB（3.5.0）**
- D1: 10  D2: 11  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 依据:
  1. ①问：SKILL.md:69「项目缺**加密**或 **Bean 映射**能力时触发 C-CHECK 询问；其余场景 JDK 原生 / Spring 自带即可覆盖，不询问」+ :70 低风险「零打断、不询问」+ :132-134 C-CHECK 节——范围一次说清。
  2. ②问：`references/04-io-http-json.md:67` 规则行（默认无超时＝无限等待）+ :70-73 Builder 超时代码 + 单例说明——规则与示例齐备可直接照抄。
  3. 04 的「坐标见 SKILL.md C-CHECK 节」回链（:101）与 SKILL:151 OkHttp3 4.12.0 行闭环。
- 扣分主因: 无功能性失分。

### Prompt T13（对抗：六个技术判据删 why 列后是否仍可查）

**versionA（3.4.1）**
- D1: 9  D2: 11  D3: 12  D4: 11  D5: 11  D6: 9  D7: 11  D8: 11  D9: 4
- 小计: 89/100
- 依据:
  1. 六判据全部在「为什么」列可查：① Calendar 月从 0（SKILL:101「月从 0」+ `03:43-48`）；② Spring/Apache 顺序相反（SKILL:109 why 列 + `06:27-29`）；⑥ S3776 阈值 15（SKILL:125 + `12:3`）。
  2. ⑤ S1128（SKILL:124 + `11:280`）；④ 裸 now() 隐式 JVM 默认时区 + S8688（SKILL:119 + `03:86-102`）。
  3. ③ `randomInt` 半开：SKILL:120 why 列只写「手算边界易错（半开区间）」未指明是哪个 API 半开，需到 `08:191-194` 才明确 `[min, max)`——可查但指代含糊。
- 扣分主因: D6——why 列与 reference 大面积复述（六条中五条在 reference 有更完整版本），SKILL 规则表每行多一列拖累扫描；③的 why 表述指代不清。

**versionB（3.5.0）**
- D1: 9  D2: 11  D3: 12  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 91/100
- 依据:
  1. 删列后判据折入单元格且无丢失：① SKILL:105「`Calendar` 手算（月份从 0 起）」；② SKILL:113「（Spring 与 Apache 参数顺序相反）」折入 ✗ 格；⑥ SKILL:129「（Sonar java:S3776 认知复杂度阈值 15）」。
  2. ③ SKILL:124「`RandomUtil.randomInt(min, max)`（[min, max) 半开）」——比 A 的 why 列指代更明确；⑤ SKILL:128「（…；Sonar java:S1128）」。
  3. ④ SKILL:123「（隐式 JVM 默认时区；Sonar java:S8688）」折入；reference 层（03/06/08/11/12）判据与 A 逐字相同，双保险。
- 扣分主因: 无判据丢失（六条全可查，且 ③ 的折入写法比 A 版 why 列更准确）；D1 同 A（此类「验证位置」型提问无专属触发词）。

### Prompt T14（对抗：JDK 8/17 日志坐标 + 混用 + 四构件版本在哪）

**versionA（3.4.1）**
- D1: 9  D2: 9  D3: 9  D4: 9  D5: 9  D6: 10  D7: 10  D8: 11  D9: 4
- 小计: 80/100
- 依据:
  1. SKILL.md:141 全部版本挤一行 prose：「MapStruct 1.5.5.Final（需 annotation processor）、Jackson 2.17.1、OkHttp3 4.12.0、Lombok 1.18.34、SLF4J 2.0.13（JDK 8 用 1.7.36）+ Logback」——**Logback 无版本号、无两套禁混用警示**。
  2. Logback 门控要跳 `08:249-250` 才拼出全貌（1.5.x 需 JDK 11+、1.2.x 不绑定 2.0、两套不可混用）——JDK 8 的完整坐标组合在单一位置查不齐。
  3. MapStruct/Jackson/OkHttp/Lombok 四版本号本身可查（SKILL:141）。
- 扣分主因: D3/D4——SLF4J+Logback 组合信息不全（SKILL 缺 Logback 版本与混用警示，需跨文件拼接），JDK 8 场景有选错依赖组合的风险。

**versionB（3.5.0）**
- D1: 9  D2: 12  D3: 12  D4: 12  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 依据:
  1. SKILL.md:147-153 三列小表（构件/参考版本/门控备注），:153 SLF4J+Logback 行含两套组合与禁混用警示：「2.0.13 + 1.5.x｜需 JDK 11+；JDK 8 用 SLF4J 1.7.36 + Logback 1.2.x，两套禁混用」——JDK 8 与 JDK 17 两个答案一次查全。
  2. :149-152 MapStruct 1.5.5.Final（需 annotation processor）/Jackson 2.17.1/OkHttp3 4.12.0/Lombok 1.18.34 逐行可查。
  3. 混用后果（"no SLF4J provider"）在 `08:250` 保留，与 SKILL 行通过「（见 references/08）」显式回链。
- 扣分主因: 无功能性失分；D1 同 A（版本/坐标类提问无专属触发词）。

## ③ 汇总表

| Prompt | versionA 小计 | versionB 小计 | 差值（B−A） |
|---|---|---|---|
| T1 判空/Optional | 90 | 91 | +1 |
| T2 集合分块/分组 | 91 | 92 | +1 |
| T3 日期 | 92 | 92 | 0 |
| T4 IO/HTTP/JSON | 85 | 93 | +8 |
| T5 线程池/异步 | 92 | 93 | +1 |
| T6 BigDecimal | 93 | 93 | 0 |
| T7 加密/密码 | 91 | 93 | +2 |
| T8 异常/日志/随机 | 91 | 92 | +1 |
| T9 规约/import 可查性 | 86 | 89 | +3 |
| T10 JDK 门控判据 | 84 | 95 | +11 |
| T11 字符串默认/S3252 | 89 | 87 | −2 |
| T12 C-CHECK/HTTP 超时 | 78 | 93 | +15 |
| T13 六判据折入 | 89 | 91 | +2 |
| T14 构件版本/日志门控 | 80 | 93 | +13 |
| **总分（/1400）** | **1231** | **1287** | **+56** |

## ④ 两版最大差异点（客观陈述）

1. **HTTP 超时规则落地（最大分差来源，T4/T12）**：versionA 的 `04-io-http-json.md:68` OkHttp 单例示例未设任何超时，SKILL.md:63 只有「超时缺省」断言——断言与示例脱节；versionB 的 `04:67-73` 有规则行 + `.connectTimeout(5s)/.readTimeout(30s)` 可照抄代码。
2. **JDK 门控表述（T10）**：versionA SKILL:43-51 用「五档累加 + 括号实际版本」双编号混排，非 LTS（如 JDK 16）在 SKILL 层无明确判据（需跳 09 平表补救）；versionB SKILL:47-63 为「特性 → 最低 JDK」平表 + 单条「≥ 即可用」判据 + 「非 LTS 同样按版本比较」明示。
3. **构件版本呈现（T14）**：versionA SKILL:141 一行 prose，Logback 无版本、无禁混用警示；versionB SKILL:147-153 三列小表，SLF4J+Logback 行含两套组合与禁混用。
4. **S3252 策略段（T11，唯一 A 高于 B 的点）**：versionA 在 SKILL:143 + `01:117-125` 有完整 S3252 处置策略（能回答「Sonar 扫出来怎么办」的追问），但对判空主路径引入条件分支；versionB 全件无 S3252 内容，默认 `StrUtil` 唯一、更干净，追问则超出技能范围。
5. **出处标注与 IDE 指引（T9 等，全局性）**：versionA 在 02/05/08 标题带「（阿里）/（阿里规约）」、11 文件头有「来源：阿里巴巴 Java 开发手册（泰山版）」+ 结尾 IDEA Ctrl+Alt+O 快捷键、05 尾部有 Guava 备注段；versionB 全部去除，规则本体（含 11 的 19 条、import 同步删除规则 SKILL:128）完整保留。
6. **规则表列数（T13）**：versionA 规则表带「为什么」列（判据在列内）；versionB 删列后把判据折入 ✗/✓ 单元格（如「月份从 0 起」「[min, max) 半开」「S3776 阈值 15」），六项技术判据两版均无丢失，reference 层（03/06/08/11/12）两版逐字相同。
7. **description 触发面（T7/T8 等）**：versionB 的 frontmatter description 多出一段「用户任务词」（生成订单号/唯一 ID、验证码/token/盐、密码加密/哈希存储、金额计算、线程池/异步、日期格式化/时区），任务型提问的触发精度略高；versionA 仅代码信号列表。
