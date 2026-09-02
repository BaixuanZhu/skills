# 盲评报告 B（v3.6.0 达尔文验证）

## 方法节（配对证据）

本 agent 只读了 `snapshots/versionA/`、`snapshots/versionB/` 两个快照目录 + rubric + test-prompts，未读任何其他 eval 子目录、skills/ 源目录或 git 历史。两个快照 frontmatter 的 `version:` 字面值：

- **versionA 目录** → `version: "3.6.0"`（versionA/SKILL.md L22）
- **versionB 目录** → `version: "3.5.0"`（versionB/SKILL.md L22）

按铁律，版本字面值不影响打分；下文所有「版本 A / 版本 B」指目录，不指新旧。

两版体量：versionA 共 1844 行（references），versionB 共 2136 行。结构性差异（打分依据，均经逐文件核对）：

| 差异点 | versionA | versionB |
|---|---|---|
| 各 reference 尾部「推荐示例」节 | 全删（01/02/04/05/06/07/08/10） | 保留（8 个文件各一段复述性示例） |
| 独有判据位置 | 迁入速查表行内注（01 subAfter 第三参 L21、06 拷贝忽略 null L15、10 千分位 L18 + String.format 边界 blockquote L20） | 留在文件尾示例节（01 L107、06 L106、10 L135-139） |
| 09-modern-java | 108 行：门控表 + 3 antipattern + JDK 25 新特性示例；Stream.toList/ScopedValue 判据外移至 02/05 | 255 行：门控表含 Class-File API 等 23 行 + 6 antipattern（含 JDK 8 等价写法、Stream.toList 不可变、ScopedValue vs ThreadLocal）+ 按版本通用语法示例 |
| 11-conventions 常量规则 | §8/§9（≥2 处判据）/§10（五级放置表 + 禁 Constants 万能类 + private 构造） | 仅 §8 禁魔法值单条 + §9 大写 L |
| SKILL 路由表 L93 | 「命名/OOP 规约/格式/**常量与字面量**」 | 「命名/OOP 规约/格式」（无常量信号词） |
| Sonar 规则号 | 全删 | 保留约 15 处（S8688/S1128/S3776/S6373/S2133/S1181/S1166/S2142/S2221/S3037/S2200） |
| 12→11 交叉引用 | 规则名引用（「『复杂布尔表达式先赋具名变量』的做法」12 L133）；05→09 亦按 antipattern 名（05 L162） | 纯编号引用（「第 15 条」12 L133；「antipattern 3」05 L162） |

---

## 逐 prompt 打分

### Prompt T1（字符串判空 + Optional 取值）

**versionA**
- 拿到的技能：版本 A（frontmatter `version: "3.6.0"`）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 99/100
- 关键依据：
  1. 01 速查表 L10-11「字符串判空白/非空白」直接命中 `str != null && !str.trim().isEmpty()` 手写形态；
  2. Optional 节 L79-97：`findUser(id).get()` → `orElse`/`orElseThrow` + 链式示例，与 prompt 的 `User u = findUser(id).get()` 一一对应；
  3. antipattern 1（L31-38）点名 isBlank vs isEmpty 空格陷阱。
- 扣分主因：无实质扣分（D6 给 11？不——A 的 01 无冗余尾节，仅 D6 维度内严格主义扣 1：Optional 节 L89「Optional 作字段/参数类型」为注释断言无代码，轻微）。

**versionB**
- 拿到的技能：版本 B（frontmatter `version: "3.5.0"`）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 98/100
- 关键依据：
  1. 正文与 A 完全相同（速查表 L10-11、antipattern 1 L31-38、Optional 节 L77-95）；
  2. 尾部「推荐示例」节 L97-115：`blankToDefault`/`format`/`join`/`toUnderlineCase` 全部为速查表已有行的复述，拖累定位；
  3. L107 `subAfter(fileName, ".", true)` 注释承载第三参语义（本题用不到，但使文件更长）。
- 扣分主因：D6——「推荐示例」尾节与速查表逐行重复，agent 需多扫 19 行才确认无新信息。

### Prompt T2（集合分块 + 分组）

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 99/100
- 关键依据：
  1. 文件头 L3-5 blockquote：「`partition`/`split`/`page` 在 `ListUtil`……**不在 `CollUtil`**——`CollUtil` 无这些方法」——rubric 特别盯的警告仍在，且位于文件第一屏；
  2. antipattern 2（L45-59）+ L60 blockquote：`CollUtil.groupBy` 不存在（编译错误）、`CollUtil.shuffle` 用 `Collections.shuffle`——prompt 的两问直接可答；
  3. 速查表 L16-19：分块 `ListUtil.partition(list, size)`、分组 `Collectors.groupingBy`。
- 扣分主因：D6 微扣——速查表分块行未带「CollUtil.partition 不存在」行内注，该警告只在文件头一处（可查性无损，密度微欠）。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 9  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 97/100
- 关键依据：
  1. 同一警告在 B 中出现三处：文件头 L5 + 速查表 L16 行内注「（**`CollUtil.partition` 不存在**，分块在 `ListUtil`）」+ antipattern 1 L39 括号注——查表即得（D2 不输 A）；
  2. `CollUtil.groupBy`/`shuffle` 判据同 A（L45-60）；
  3. 尾部「推荐示例」L172-192：判空/新建/分块/分组/交并差全部复述速查表。
- 扣分主因：D6——同一警告三处重复 + 19 行复述尾节，是 12 个域文件中冗余最重的之一。

### Prompt T3（日期格式化 + 当前时间）

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 100/100
- 关键依据：
  1. antipattern 1（L27-41）：`private static final SimpleDateFormat SDF` 正中 prompt 写法，含「ThreadLocal workaround 别用」的隐性坑；
  2. antipattern 6（L86-102）：裸 `LocalDateTime.now()` 隐式 JVM 默认时区（容器 UTC vs 开发机 GMT+8）+ Clock 注入可测性；
  3. 遗留 Date 场景：DateUtil 节 L127-138 + 速查表 L12-13。
- 扣分主因：无。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 11  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 99/100
- 关键依据：
  1. 正文与 A 完全相同（两版 03 均 138 行，antipattern 1/6、DateUtil 节逐字一致）；
  2. 差异仅两处 Sonar 规则号：L5「（Sonar java:S8688）」与 L86 标题「（Sonar java:S8688）」——对编码 agent 无行动价值的门禁元数据。
- 扣分主因：D6——两处无行动价值的规则号标注。

### Prompt T4（文件读写 + HTTP + JSON，纯 Java）

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 98/100
- 关键依据：
  1. rubric 盯的 OkHttp 单例 + 超时示例完整保留：04 L70-93（`OkHttpClient.Builder().connectTimeout(5s).readTimeout(30s)` + GET/POST + try-with-resources）；
  2. 文件 IO 速查表 L13-24：`readUtf8String`/`readUtf8Lines`/`copyFile`/`IoUtil.copy` 直接对应读 UTF-8/复制/流拷贝三问；
  3. antipattern 1（L28-44）手搓 `FileInputStream` ✗ 正中 prompt 现状。
- 扣分主因：D4/D5 各扣 1——「JSON 手拼字符串」在 A 的 04 无 ✗ 反例代码（只有 `new ObjectMapper` 反例），判据仅存于 SKILL 规则表 S 级行（L115）的断言 + 04 Jackson 规范的 ✓ 写法，缺手拼转义坑的展示。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 98/100
- 关键依据：
  1. OkHttp 单例 + 超时示例与 A 逐字相同（L70-93）；
  2. JSON antipattern L125-132 多一段手拼 JSON 的 ✗ 代码（`"{\"id\":" + id ...`）——手拼坑有具体形态（D4/D5 优于 A）；
  3. 尾部「推荐示例（HTTP + JSON 组合）」L136-148：`fetchUser` 组合示例，404→null、byteStream 反序列化均复述 HTTP/JSON 两节已有内容。
- 扣分主因：D6——13 行组合示例尾节为正文复述（byteStream 直接反序列化在正文 L118 已有）。

### Prompt T5（线程池 + 异步）

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 100/100
- 关键依据：
  1. rubric 盯的完整线程池代码在 antipattern 正文非尾节：antipattern 1 L30-42（显式 ThreadPoolExecutor + 有界队列 + 命名工厂 + CallerRunsPolicy）+ 拒绝策略表 L47-55；
  2. antipattern 3 L72-75 优雅关闭（`shutdown` + `awaitTermination`）；antipattern 6 L107-115 命名 ThreadFactory；
  3. CompletableFuture 节 L140-148：`supplyAsync` 必传自定义池 + L148「不要在 commonPool 跑阻塞 IO」正中 prompt 的无参 supplyAsync。
- 扣分主因：无。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 98/100
- 关键依据：
  1. 正文与 A 相同（antipattern 1/3/6、CompletableFuture 节、commonPool 警告逐字一致）；
  2. 尾部「推荐示例」TaskRunner L193-227：判空 + 池构造 + 异常隔离 + 优雅关闭的组合模板——要素全部来自正文三个 antipattern，属组合复述；
  3. L120/L132 带「SonarQube S6373」标注。
- 扣分主因：D6——35 行 TaskRunner 尾节复述正文 + Sonar 号元数据。

### Prompt T6（BigDecimal 除法 + 比较）

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 100/100
- 关键依据：
  1. rubric 盯的三判据全部速查表即得：L12 `divide(bd2, scale, RoundingMode.HALF_UP)`、L13 `compareTo == 0`、L18 千分位 `String.format(Locale.US, "%,.2f", bd)`；
  2. antipattern 3（L47-54）解释除法抛 `ArithmeticException`（非终止小数展开）——正中「为什么除法有时抛异常」；
  3. antipattern 4（L56-63）：`1.0` vs `1.00` equals 比较 scale——正中「为什么比较不对」。
- 扣分主因：无。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 11  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 98/100
- 关键依据：
  1. divide/compareTo 判据同 A（速查表 L12-13、antipattern 3/4）；
  2. 千分位写法在文件尾「推荐示例」L135-136（`String.format(java.util.Locale.US, "%,.2f", total)` + 「避免欧洲逗号小数点」注释）+ L139 String.format 边界 blockquote——可查但需翻到文件尾；
  3. L90/L105 antipattern 标题带「SonarQube S2133」「S3037」。
- 扣分主因：D6——尾节大部分（构造→运算→定精度链 L118-134）复述 antipattern，仅千分位两行是独有信息却埋在尾部（D2 同因扣 1）。

### Prompt T7（加密 + 密码哈希）

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 100/100
- 关键依据：
  1. antipattern 1（L23-34）：手搓 `MessageDigest` + `Integer.toHexString` 漏 `%02x`——正中 prompt 现状，含哈希碰撞后果；
  2. antipattern 2（L36-44）：`SecureUtil.md5(rawPassword)` 存密码 ✗ → `BCrypt.hashpw/checkpw`；
  3. 密钥管理 L67-76：硬编码密钥禁令（计算 MD5 与存密码两问之外的安全兜底）。
- 扣分主因：无。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 98/100
- 关键依据：
  1. 速查表 + 4 个 antipattern + 密钥管理与 A 逐字相同；
  2. 尾部「推荐示例」L67-87：`SecureUtil.md5`/`sha256`/文件 MD5/Base64/BCrypt/AES 全部为速查表 L10-19 的复述（无一条新判据）。
- 扣分主因：D6——21 行纯复述尾节。

### Prompt T8（异常处理 + 日志 + 随机）

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 100/100
- 关键依据：
  1. rubric 盯的判据仍在：antipattern「Math.random() 强转充当序号」L203「✓ 唯一性由单调发号器承担（Redis INCR 按天自增 / DB 序列 / 雪花 ID）」+ L198 生日悖论碰撞概率；
  2. 空 catch 吞异常 L48-65（含 `e.getMessage()` 可能 null）正中 prompt 空吞；
  3. 日志表 L9-14 + 异常日志 antipattern L27-35：`log.error("失败: " + e.getMessage())` ✗ → 占位符 + 异常作末参。
- 扣分主因：无。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 98/100
- 关键依据：
  1. 发号器判据同 A（L203），三问正文逐字同；
  2. 五处 Sonar 号：L75（S2142）、L91（S1181）、L107（S1166）、L141（S2221）、L203（java:S8688）；
  3. 尾部「推荐示例」L223-245：Assert/占位符/SecureRandom 组合复述。
- 扣分主因：D6——5 处规则号 + 23 行复述尾节。

### Prompt T9（对抗·「推荐示例」节删除后独有判据迁移）

四判据定位核查：① `subAfter` 第三参；② 拷贝已有对象忽略 null；③ 千分位；④ String.format 允许/禁用边界。**两版四条全部可查，无功能性缺失，不触发重扣。**

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 11  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 99/100
- 关键依据：
  1. ① 在速查表行内：01 L21「`StrUtil.subAfter(s, sep, isLast)`（`true` 取最后一个分隔符）」——查表即得；
  2. ② 在速查表：06 L15「拷贝到已有对象（忽略 null）→ `BeanUtil.copyProperties(source, target, CopyOptions.create().ignoreNullValue())`」；
  3. ③④ 在速查表 + 紧邻 blockquote：10 L18 千分位行 + L20「String.format 边界：数字/货币格式化**允许**……`%s` 字符串插值**禁用**」。
- 扣分主因：D5 扣 1——「欧洲逗号小数点」具体失败模式未写出（速查表 ✗ 列只有「依赖默认 locale」）。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 11  D3: 12  D4: 12  D5: 12  D6: 9  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 96/100
- 关键依据：
  1. ① 在文件尾示例节：01 L107「`StrUtil.subAfter(fileName, ".", true); // isLastSeparator=true 取最后一个点`」（速查表 L21 无第三参语义）；
  2. ② 在「BeanUtil 运行时示例」节：06 L106；③④ 在「推荐示例」尾节：10 L135-136（含「避免欧洲逗号小数点」注释，D5 优于 A）+ L139 blockquote；
  3. 四判据全部可查但全部位于各文件尾部复述性示例节内，需翻过整个 antipattern 正文才到达。
- 扣分主因：D6——独有判据埋在复述尾节里，尾节其余内容（L99-113、L102-110、L118-134）与速查表/antipattern 重复；判据可达性也因位置靠后打折（D2 扣 1）。

### Prompt T10（对抗·09 精简后门控与迁移判据可查性）

四问核查：① JDK 8 门控判据；② Stream.toList 不可变；③ ScopedValue 替代 ThreadLocal；④ synchronized 21/25。**A 版四问在全部文件内均可查（①SKILL/09、②SKILL/02、③05、④09），不触发 D3/D5 重扣。**

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 10  D3: 11  D4: 11  D5: 10  D6: 12  D7: 11  D8: 12  D9: 4
- 该 prompt 小计: 93/100
- 关键依据：
  1. ① 判据明确：SKILL L49「目标 JDK ≥ 特性最低版本 → 可用」+ 09 门控表 L12/L15/L16（var 10 / 文本块 15 / record 16）+ 09 头部 L4「JDK 8 项目全部禁用本文件特性」；
  2. ② 需跳 02：SKILL L58「`Stream.toList()`（不可变）| 16」行内注 + 02 L171 blockquote「返回不可变；`Collectors.toList()` 返回可变。按需选择，JDK 8 项目只能用后者」——判据可查但**未点名 `add` 抛 `UnsupportedOperationException`**；
  3. ③ 需跳 05：09 L88「虚拟线程与 Scoped Values 详见 05-concurrency.md」→ 05 L164-192 Scoped Values 节 + L186-192 对比表（不可变/作用域自动清理/无串值/25+）。
- 扣分主因：②③ 各多一跳（D2/D7），② 缺具体异常行为（D3/D5）；D6 因 108 行高密度组织得满。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 9  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 97/100
- 关键依据：
  1. 四问全部在 09 文件内一步可查：① antipattern 1 L39-58（JDK 8 误用 + **等价低版本写法代码**）；② antipattern 2 L60-68（`names.add("x"); // ✗ UnsupportedOperationException` + Collectors.toList 改法）；③ antipattern 4 L89-99 + 指针到 05 对比表；④ antipattern 3 L70-87（21 pin / 25 解除，JEP 491）；
  2. 门控表 L7-35 含 Class-File API、Compact Object Headers、Module Import、KDF 等——覆盖面显著更广（追问 JVM 内部特性也能答）；
  3. D6 扣分依据：09 内 ScopedValue 代码（L225-234）与 05（L169-184）、虚拟线程代码（L197-203）与 05（L152-159）跨文件重复。
- 扣分主因：D6——255 行且与 05 存在两段近乎相同的代码，密度低于精简组织。

### Prompt T11（对抗·常量与字面量新规则）

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 100/100
- 关键依据：
  1. 11 §9（L92-104）：L95-97 示例正是 prompt 场景（`"PENDING"` 在 OrderService/RefundService 各写一遍）→ L104 判据「同一字面量出现 **≥2 处**即提取……状态/类型码 → 枚举；阈值/配置 → 常量类」——机械可执行；
  2. 11 §10（L106-131）：五级放置表（L108-114：仅本类/同包/跨包/enum/配置）+ L117-122 ✗「实现类里堆常量，其他 Service 要用只能复制一份」正中 prompt 的重试次数/超时写法 + L128 `private OrderConstants()` 禁实例化 + L131「✗ 禁 `Constants` 万能类（改一处全量重编译）」——prompt 第四问「建 Constants 类行不行」有明确禁令；
  3. SKILL 三处联动：路由表 L93「常量与字面量」→ 11、规则表 L128「字面量 ≥2 处未提取；常量堆在实现类中不共享」、自检 L162「常量提取与放置」。
- 扣分主因：无。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 9  D3: 6  D4: 6  D5: 7  D6: 12  D7: 8  D8: 12  D9: 4
- 该 prompt 小计: 76/100
- 关键依据：
  1. 11 §8（L86-100）是唯一常量规则：「禁魔法值」单条 + L100「状态/类型码优先用**枚举**，全局配置用常量类」——能答「要提取」，但**无 ≥2 处判据、无放置规则、无 Constants 万能类禁令、无 private 构造**；
  2. SKILL 路由表 L93 无「常量与字面量」信号词（仅「命名/OOP 规约/格式」），规则表 L127 仅「魔法值直出 → 抽 static final 常量或枚举」单行，自检 L161 无常量项——三问（何时必须提/放哪/万能类行不行）中两问半无判据；
  3. prompt 的坑「我想建一个 Constants 类把所有常量放一起行不行」在 B 中查不到任何禁令——agent 无法拒绝该反模式（判据丢失，按对抗集规则 D3/D4/D5 重扣）。
- 扣分主因：常量规则本体缺失（D3 6 / D4 6 / D5 7）+ 路由入口缺失（D2 9 / D7 8）。

### Prompt T12（对抗·Sonar 规则号删除后规则本体存活）

六条本体逐条核查（两版位置相同，全部存活）：① 无用 import 四类 + 同步删（A 11 §21 L309-319 / B 11 §19 L278-288，内容逐字同，且 SKILL L129/L128 均有「删掉某类最后一处使用时同步删 import」）；② 阈值 15 + 三种重构手法（两版 12 L3/L24-29 同）；③ SimpleDateFormat（两版 03 antipattern 1 + 05 antipattern 7）；④ `Math.abs(Integer.MIN_VALUE)` 返回自身 + 转 long + `Math.absExact`（两版 10 antipattern 8，A L93-106 / B L90-103）；⑤ 裸 now() 隐式 JVM 默认时区（两版 03 antipattern 6）；⑥ finally 抛异常掩盖原始异常（两版 08 L91-105）。

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 100/100
- 关键依据：
  1. 六条本体全部完整可查（见上），删除的只有规则号；
  2. 12 L3「单方法认知复杂度 ≤ 15」阈值与手法无号存活；10 antipattern 8 连 `Math.absExact`（JDK 15+）都保留；
  3. 无一处 Sonar 号残留（grep 全文核实）——无门禁元数据拖累。
- 扣分主因：无。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 10  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 98/100
- 关键依据：
  1. 六条本体与 A 逐字相同（位置见上），全部可查——本体未随规则号丢失；
  2. 规则号约 15 处：SKILL L123（java:S8688）/L128（S1128）/L129（S3776）、03 L5/L86、05 L120/L132（S6373）、08 L75/L91/L107/L141、10 L90（S2133）/L105（S3037）、02 L93/L106（S2200）、11 L278、12 L1/L3；
  3. 这些号对「编码 agent 照做」无行动价值（prompt 本身即声明「已经不标 Sonar 规则号了」验证本体）。
- 扣分主因：D6——15 处无行动价值的规则号元数据。

### Prompt T13（对抗·编号顺移与交叉引用完整性）

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 100/100
- 关键依据：
  1. ① 12 L133 按规则名引用「11-conventions『复杂布尔表达式先赋具名变量』的做法」→ 11 §17（L239）同名标题存在，可解析且抗重排；
  2. ② 05 L162「详见 `09-modern-java.md`『synchronized LTS 版本陷阱』antipattern」→ 09 antipattern 1「虚拟线程 + synchronized 的 LTS 版本陷阱（JDK 21 vs 25）」（L32）名称匹配可解析；
  3. ③ SKILL L93「命名/OOP 规约/格式/**常量与字面量**」→ 11 L74「## 常量与字面量」节存在（含 §9/§10 提取与放置规则）；④ 11 编号 §1（L8）→ §21（L309）连续无断号（逐节核对：1-7 命名、8-11 常量、12-16 OOP、17-18 控制、19-21 格式）。
- 扣分主因：无。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 11  D3: 11  D4: 11  D5: 11  D6: 10  D7: 10  D8: 12  D9: 3
- 该 prompt 小计: 91/100
- 关键依据：
  1. ① 12 L133 纯编号引用「11-conventions **第 15 条**的做法」→ B 的 11 §15（L208）当前恰好是布尔规则，可解析；但 11 内部规则增删后编号即错位（脆弱引用，D9）；
  2. ② 05 L162「详见 09-modern-java.md **antipattern 3**」→ B 的 09 antipattern 3（L70）当前正确——同为纯编号；
  3. ③ SKILL L93 路由表**无「常量与字面量」字样**（只有「命名/OOP 规约/格式」）——prompt ③按该信号词查路由落空，需推断才能到达 11 的「常量定义」节（L84）；④ §1（L8）→ §19（L278）连续无断号 ✓。
- 扣分主因：③路由信号词缺失（D2/D7）+ 两处纯编号引用脆弱（D9 3/4）+ 该题涉及文件内残留 Sonar 号（D6 10）。

### Prompt T14（对抗·示例删除后的综合可执行性——五块兜底）

五块核查：**两版全部可查到可照抄写法，无缺块，不触发 D4 重扣——「删示例」改动无损失（rubric 预期持平成立）。**
① 判空守卫：两版 02 速查表 L11-13（`CollUtil.isEmpty/isNotEmpty`）；② 分块：两版 02 L16 + 文件头 L5（`ListUtil.partition(list, 100)`，在 ListUtil 非 CollUtil）；③ 线程池：两版 05 antipattern 1 L30-42（完整构造）+ antipattern 3 L72-75（优雅关闭）+ antipattern 6 L107-115（命名工厂）；④ 金额：两版 10 速查表 L11/L12/L14 + antipattern（`new BigDecimal("...")`、`setScale(2, HALF_UP)`、`compareTo`）；⑤ 拷贝忽略 null：A 06 速查表 L15 / B 06 L106。

**versionA**
- 拿到的技能：版本 A
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 12  D6: 12  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 99/100
- 关键依据：
  1. ③的「单任务异常隔离记日志」：A 无专门组合模板，落点是 05 L140-145 CompletableFuture 的 `.exceptionally(ex -> { log.error("failed", ex); ... })` + 08 的 catch 记日志——每一块可照抄，但需 agent 自行拼装 submit+try-catch 形态；
  2. ⑤拷贝忽略 null 在 06 速查表 L15 一行即得；
  3. ②分块的「非 CollUtil」警告在 02 文件头 L5 第一屏。
- 扣分主因：D4 扣 1——③异常隔离无现成整块模板，拼装多一步（判据与代码均全，非功能缺陷）。

**versionB**
- 拿到的技能：版本 B
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 12  D6: 9  D7: 12  D8: 12  D9: 4
- 该 prompt 小计: 99/100
- 关键依据：
  1. ③有整块模板：05 尾节 TaskRunner L215-218「`pool.submit(() -> { try { tasks.get(idx).run(); } catch (Throwable t) { log.error("任务 #{} 失败", idx, t); } })  // 异常隔离`」——D4 优于 A；
  2. 五块其余落点与 A 相同（①②④⑤）；
  3. D6：本题横跨 5 个文件，B 在其中每个文件都有复述性尾节（01 L97-115、02 L172-192、05 L193-227、10 L116-137、06 L100-119），累计拖累最重。
- 扣分主因：D6——五文件尾节累计复述（与 D4 的模板优势相抵，总分持平）。

---

## 总分表

| Prompt | versionA | versionB | 差值（A−B） |
|---|---|---|---|
| T1 判空 + Optional | 99 | 98 | +1 |
| T2 集合分块 + 分组 | 99 | 97 | +2 |
| T3 日期 + 时区 | 100 | 99 | +1 |
| T4 IO + HTTP + JSON | 98 | 98 | 0 |
| T5 线程池 + 异步 | 100 | 98 | +2 |
| T6 BigDecimal | 100 | 98 | +2 |
| T7 加密 + 密码哈希 | 100 | 98 | +2 |
| T8 异常 + 日志 + 随机 | 100 | 98 | +2 |
| T9 判据迁移（对抗） | 99 | 96 | +3 |
| T10 09 精简（对抗） | 93 | 97 | **−4** |
| T11 常量规则（对抗） | 100 | 76 | **+24** |
| T12 规则本体存活（对抗） | 100 | 98 | +2 |
| T13 交叉引用（对抗） | 100 | 91 | **+9** |
| T14 综合可执行性（对抗） | 99 | 99 | 0 |
| **合计** | **1387** | **1341** | **+46** |

## 最大分歧点小结

1. **T11 常量规则（+24，A 胜）**：B 对「何时必须提取（≥2 处判据）/ 放哪（五级放置表）/ Constants 万能类行不行（禁令）」三问全部无判据（11 仅 §8 单条 L86-100），且 SKILL 路由表 L93 无「常量与字面量」入口、自检项无常量——prompt 的「建 Constants 类行不行」这一坑 B 无法拒绝，属判据丢失的功能性缺陷（D3/D4/D5/D2/D7 重扣）。A 的 11 §9/§10 与 SKILL 三处联动机械可执行，示例与 prompt 场景一一对应。
2. **T13 交叉引用（+9，A 胜）**：B 两处纯编号引用（12 L133「第 15 条」、05 L162「antipattern 3」）当前可解析但脆弱（D9 3/4）；且 SKILL 路由表无「常量与字面量」信号词，prompt ③ 的路由查询落空。A 全部语义（规则名/antipattern 名）引用，四处全部可解析。
3. **T10 09 精简（−4，B 胜，唯一 B 反超题）**：B 的 09 一步可查四问全部，含 A 缺失的行为细节——② `Stream.toList()` 的 `add` 抛 `UnsupportedOperationException` 具体异常（B 09 antipattern 2 L64，A 仅「不可变」三字，散在 SKILL L58 与 02 L171）、① JDK 8 等价低版本写法代码（B antipattern 1）——且门控表覆盖 Class-File API / Compact Object Headers 等 JVM 内部特性。A 虽 D6 满分（108 行高密度），D2/D3/D5 的跳转与细节缺口使总分落后。
4. **回归集 T2/T5/T6/T7/T8（各 +2，A 胜）**：rubric 特别盯的判据（CollUtil.partition 不存在、OkHttp 单例+超时、antipattern 6 线程池完整代码、divide/compareTo/千分位、发号器承担唯一性）两版全部在正片可查——A 的删改未造成回归；差值全部来自 B 的「推荐示例」尾节复述与 Sonar 规则号元数据（D6）。
5. **T9 判据迁移（+3，A 胜）与 T14 兜底（0）**：四条独有判据（subAfter 第三参、拷贝忽略 null、千分位、String.format 边界）与综合五块两版均无缺——删除「推荐示例」无信息损失；差值仅在可达性：A 已迁入速查表行内注（01 L21、06 L15、10 L18+L20）查表即得，B 埋在各文件尾部示例节。
