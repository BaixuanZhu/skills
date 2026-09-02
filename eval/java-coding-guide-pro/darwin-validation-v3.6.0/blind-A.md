# 盲评报告 A（v3.6.0 达尔文验证）

## 方法

- 评分人：独立盲评 agent A。只读 `snapshots/version1/` 与 `snapshots/version2/` 两个快照目录 + `rubric.md` + `test-prompts.md`，未读其他 eval 子目录、skills/ 源目录与 git 历史。
- 两快照 frontmatter `version:` 字面值（配对证据）：
  - `snapshots/version1/SKILL.md` 第 22 行：`version: "3.5.0"`
  - `snapshots/version2/SKILL.md` 第 22 行：`version: "3.6.0"`
- 按 rubric 9 维度（D1~D8 各 12 分、D9 4 分，满分 100）对 14 条 prompt 两版分别打分；版本字面值不影响打分。
- 主要客观差异（打分依据基础，均经全文比对 + grep 复核）：
  1. version1 的 8 个 reference（01/02/04/05/06/07/08/10）带「推荐示例」尾节，内容与各自速查表/antipattern 复述；version2 全部删除，其中 subAfter 第三参语义、拷贝忽略 null、千分位 Locale.US、String.format 边界四条独有判据折入了速查表（01:21 / 06:15 / 10:18+20）。
  2. version1 全套附带 19 处 Sonar 规则号（S1128/S2200/S3037/S1166/S1181/S2133/S2142/S2221/S3776/S6373/S8688）；version2 grep 为零，规则本体全部存活。
  3. version1/09-modern-java 255 行（含 JDK 8~21 通用语法示例逐条 + toList/ScopedValue antipattern + 完整特性表含 Class-File API 等）；version2/09 精简至 108 行，只剩门控表 + 3 个 antipattern + JDK 25 新特性示例，toList/ScopedValue 判据移至 02/05 查。
  4. version2/11-conventions 新增「常量与字面量」两条规则（§9 ≥2 处判据、§10 五级放置表 + 禁 Constants 万能类 + private 构造），编号 §1–21 连续；version1 仅 §8 禁魔法值（§1–19 连续）。
  5. 交叉引用：version1/12 手法 5 用纯编号引用 11（「第 15 条」）、05:162 用「antipattern 3」；version2 改用规则名/标题名（「复杂布尔表达式先赋具名变量」「synchronized LTS 版本陷阱」），均可解析，version2 抗重排。
  6. version2 删除后仅两处独有内容消失：04 的「手拼 JSON 字符串」反例（SKILL S 级表仍在）与 05 TaskRunner 的「submit 内 catch (Throwable) 异常隔离记日志」整段（池构造/命名工厂/优雅关闭仍在 antipattern 1/3/6 正片）。

---

## T1 · 字符串判空 + Optional 取值

### version1（"3.5.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 94/100
- 关键依据:
  1. `01-null-and-string.md` 速查表 10-11 行「判空白/判非空白 → StrUtil.isBlank/isNotBlank」直接命中 prompt 的手写判空。
  2. `01` 79-87 行 Optional 节：`findUser(id).get()` 标 ✗ NoSuchElementException，`orElse`/`orElseThrow` 可照抄。
  3. D6 扣分：`01` 97-115 行「推荐示例」尾节（blankToDefault/format/subAfter/join/命名转换）与速查表 13/17/21/23/24/25 行逐条重复。
- 扣分主因: 推荐示例尾节复述速查表（D6）。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 关键依据:
  1. `01` 速查表 10-11 行与 Optional 节（79-97 行）与 v1 相同，判空 + get() 两问全覆盖。
  2. antipattern 1（31-39 行）「纯空格判为非空」陷阱点名，防手写判空回潮。
  3. 无推荐示例尾节，subAfter 第三参语义上移至速查表 21 行，无信息损失。
- 扣分主因: 无明显失分点（D4/D5 为锚点保留分）。

**差值: +2（v2 胜，删冗余尾节）**

---

## T2 · 集合分块 + 分组 + groupBy/shuffle

### version1（"3.5.0"）
- D1: 12  D2: 11  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 93/100
- 关键依据:
  1. `02` 速查表 16 行「分块 → `ListUtil.partition(list, size)`（**`CollUtil.partition` 不存在**，分块在 `ListUtil`）」——rubric 特别盯的警告在查表行内即得。
  2. `02` antipattern 2（45-60 行）明示 `CollUtil.groupBy` 编译错误 + 60 行 blockquote 列 `CollUtil.shuffle` 同类误用，直接回答 prompt 第三问。
  3. D6 扣分：172-192 行「推荐示例」（partition/groupingBy/交并差）与速查表 16/18/20-22 行重复。
- 扣分主因: 推荐示例尾节复述（D6）。

### version2（"3.6.0"）
- D1: 12  D2: 11  D3: 12  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 95/100
- 关键依据:
  1. 「CollUtil.partition 不存在」警告仍在文件头 5 行 blockquote（「`partition`/`split`/`page` 在 `ListUtil`……**不在 `CollUtil`**——`CollUtil` 无这些方法」），rubric 要求的「任一处可查」满足。
  2. antipattern 1（33-43 行）`ListUtil.partition(list, 50)` 代码块与 antipattern 2 blockquote（60 行）groupBy/shuffle 误用警告与 v1 相同。
  3. 速查表 16 行删去行内括号注后警告仅剩头部一处——仍在一跳内，D2 不扣（与 v1 同分）。
- 扣分主因: 无明显失分点。

**差值: +2（v2 胜，删冗余；partition 警告保留在文件头，未退步）**

---

## T3 · 日期格式化 + 当前时间 + 遗留 Date

### version1（"3.5.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 11  D7: 11  D8: 11  D9: 4
- 小计: 95/100
- 关键依据:
  1. `03` antipattern 1（27-41 行）：static SDF 多线程数据错乱 + ThreadLocal workaround 禁用 + DateTimeFormatter/DateUtil 双方案，正中 prompt。
  2. antipattern 6（86-102 行）：裸 `now()` 容器 UTC 时区坑 + `now(ZONE)`/注入 Clock 两方案；速查表 12 行覆盖遗留 Date。
  3. D6 微扣：03 文件头 5 行、86 行标题及 SKILL:123 行三处附 `Sonar java:S8688` 规则号（无行动价值元数据）。
- 扣分主因: Sonar 规则号标注（D6 微扣）。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 关键依据:
  1. `03` 全文与 v1 实质相同（antipattern 1/6、速查表、java.time/DateUtil 推荐段全在），仅 5 行与 86 行标题去掉 S8688 号。
  2. SKILL:123 行 A 级表「裸 now() 隐式 JVM 默认时区 → now(zoneId)/now(clock)」本体保留。
  3. 无尾节冗余、无规则号。
- 扣分主因: 无明显失分点。

**差值: +1（v2 胜，仅规则号差异，场景无退步）**

---

## T4 · 文件读写 + HTTP + JSON（纯 Java）

### version1（"3.5.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 94/100
- 关键依据:
  1. `04` 速查表 13/21 行（readUtf8String/copyFile）+ HTTP 规范 70-93 行（OkHttp 单例 + connectTimeout/readTimeout + try-with-resources）完整，rubric 盯的点在。
  2. 126-128 行 JSON antipattern 含「手拼 JSON 字符串（转义/嵌套易错）」反例 + 118 行 `MAPPER.readValue(resp.body().byteStream(), User.class)`。
  3. D6 扣分：136-148 行「推荐示例（HTTP + JSON 组合）」fetchUser 与 get()/readValue 复述。
- 扣分主因: 推荐示例尾节复述（D6）。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 10  D5: 10  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 94/100
- 关键依据:
  1. OkHttp 单例 + 超时完整代码（70-93 行）、Jackson 单例 + `readValue(resp.body().byteStream())`（107-118 行）与 v1 相同，组合场景可拼。
  2. D5 扣分：125-129 行 JSON antipattern 只剩「每次 new ObjectMapper」，v1 的「手拼 JSON 字符串」反例从 04 消失（仅 SKILL:115 S 级表保留一行）。
  3. D4 扣分：HTTP+JSON 整合示例（fetchUser，含 404 处理）删除，需 agent 自行组合 get() 与 readValue。
- 扣分主因: 手拼 JSON 反例与整合示例从本域文件消失（D4/D5 各 −1），与删冗余的 D6 +2 相抵。

**差值: 0（持平：删示例小损 D4/D5，删冗余补 D6）**

---

## T5 · 线程池 + 异步

### version1（"3.5.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 94/100
- 关键依据:
  1. `05` antipattern 1（22-43 行）：newFixedThreadPool 无界队列 OOM + 完整 ThreadPoolExecutor（有界队列 100 + 命名 ThreadFactory + CallerRunsPolicy）。
  2. 134-148 行 CompletableFuture：supplyAsync 传自定义池 + 「不要在 commonPool 跑阻塞 IO」+ exceptionally，正中 prompt 第二问。
  3. D6 扣分：193-227 行 TaskRunner「推荐示例」的池构造与 antipattern 1 逐参数重复。
- 扣分主因: TaskRunner 尾节复述 antipattern 1/3/6（D6）。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 关键依据:
  1. rubric 盯的三件全在正片：池构造（antipattern 1，29-43 行）、命名工厂（antipattern 6，100-118 行）、shutdown+awaitTermination（antipattern 3，66-76 行）——不是被删的尾节。
  2. CompletableFuture 段（134-148 行）与拒绝策略表（47-55 行）与 v1 相同。
  3. 删 TaskRunner 无判据损失（其要素全部在 antipattern 正片）。
- 扣分主因: 无明显失分点。

**差值: +2（v2 胜：核心代码在 antipattern 节未动，纯删冗余）**

---

## T6 · BigDecimal 除法 + 比较

### version1（"3.5.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 94/100
- 关键依据:
  1. `10` antipattern 3（44-51 行）divide 裸除抛 Non-terminating + `divide(bd2, 2, RoundingMode.HALF_UP)`；antipattern 4（53-60 行）equals 比 scale / compareTo。
  2. 千分位 `String.format(java.util.Locale.US, "%,.2f", total)`（135-136 行注释「避免欧洲逗号小数点」）+ 139 行 String.format 边界 blockquote。
  3. D6 扣分：116-137 行「推荐示例」的构造/运算/setScale/compareTo 与 antipattern 1-6 重复。
- 扣分主因: 推荐示例尾节复述（D6）。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 关键依据:
  1. antipattern 3/4 与速查表 12/13 行（divide/compareTo）与 v1 相同。
  2. 千分位判据上移至速查表 18 行「`String.format(Locale.US, "%,.2f", bd)`」+ 紧随 blockquote（20 行），查表即得，比 v1 文件尾更快。
  3. rubric 盯的三点（divide 显式 scale、compareTo vs equals、千分位）全部可查。
- 扣分主因: 无明显失分点。

**差值: +2（v2 胜：判据前移 + 删冗余）**

---

## T7 · 加密 + 密码哈希

### version1（"3.5.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 94/100
- 关键依据:
  1. `07` antipattern 1（23-34 行）手搓 MessageDigest 漏 `%02x` 丢前导零 → `SecureUtil.md5/sha256`。
  2. antipattern 2（36-44 行）`SecureUtil.md5(rawPassword)` 标 ✗ 彩虹表 → `BCrypt.hashpw/checkpw`。
  3. D6 扣分：67-87 行「推荐示例」（md5/sha256/文件 MD5/Base64/BCrypt/AES）与速查表 12-19 行逐条重复。
- 扣分主因: 推荐示例尾节复述速查表（D6）。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 关键依据:
  1. antipattern 1/2 与 v1 完全相同；文件哈希 `SecureUtil.md5(file)` 在速查表 14 行（两版同）。
  2. antipattern 4（59-65 行）SecureUtil.sha256 vs DigestUtil.sha256 返回类型混淆陷阱保留。
  3. 删尾节无判据损失（AES 在速查表 19 行、密钥管理节 67-76 行保留）。
- 扣分主因: 无明显失分点。

**差值: +2（v2 胜，纯删冗余）**

---

## T8 · 异常处理 + 日志 + 随机序号

### version1（"3.5.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 94/100
- 关键依据:
  1. `08` 48-65 行空 catch 吞异常 + 26-35 行 `log.error("失败: " + e.getMessage())` 丢堆栈/getMessage 可能 null。
  2. 196-207 行 Math.random 当序号 antipattern：「随机≠唯一：10 万空间约 400 次即 50% 碰撞」+「✓ 唯一性由单调发号器承担（Redis INCR / DB 序列 / 雪花 ID）」——rubric 盯的判据在。
  3. D6 扣分：223-245 行「推荐示例」（验证码代码与 209-221 行 antipattern 重复）+ 4 处 Sonar 号标题（75/91/107/141 行）。
- 扣分主因: 推荐示例复述 + Sonar 号（D6）。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 关键依据:
  1. 三个 antipattern（空吞/日志拼接/随机序号）与 v1 逐行相同，「唯一性由发号器承担」判据 203 行原样保留。
  2. Sonar 号标题全部去除，本体（finally 抛异常掩盖原始异常 91-105 行等）完整。
  3. 删尾节后安全凭证写法仍在 antipattern（209-221 行 SecureRandom + Base64 urlEncoder）。
- 扣分主因: 无明显失分点。

**差值: +2（v2 胜，纯删冗余 + 去规则号）**

---

## T9 · 对抗：推荐示例删除后独有判据是否迁移

### version1（"3.5.0"）
- D1: 12  D2: 10  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 92/100
- 关键依据:
  1. 四条判据全部可查（无 D3 重扣情形）：① `01` 推荐示例 107 行 `subAfter(fileName, ".", true) // isLastSeparator=true 取最后一个点`；② `06` 106 行 `copyProperties(source, target, CopyOptions.create().ignoreNullValue())`；③ `10` 135 行 `String.format(Locale.US, "%,.2f", total)`；④ `10` 139 行 String.format 边界 blockquote。
  2. D2 扣分：四条中三条（①③④）在文件**尾部**推荐示例/尾注里，速查表 21 行的 subAfter 行未注第三参语义——查表得不到，需通读到尾节。
  3. D6 扣分：承载判据的推荐示例节本身是与正文复述的混合体。
- 扣分主因: 独有判据藏在文件尾，速查表查不到（D2/D6）。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 关键依据:
  1. 四条判据全部折入文件头部：① `01` 速查表 21 行 `StrUtil.subAfter(s, sep, isLast)`（`true` 取最后一个分隔符）；② `06` 速查表 15 行「拷贝到已有对象（忽略 null）」完整 CopyOptions 写法；③ `10` 速查表 18 行千分位；④ `10` 20 行 String.format 边界 blockquote 紧随速查表。
  2. 查表即得，一步命中——rubric 预期「查表即得的一版 D2/D6 应更高」成立。
  3. D4 与 v1 同分：v2 的 subAfter 为泛化形式（无 fileName 具体调用），v1 有具体调用但位置深，互有短长。
- 扣分主因: 无明显失分点。

**差值: +4（v2 胜：判据从文件尾迁入速查表）**

---

## T10 · 对抗：09 精简后门控与迁移判据是否仍可查

### version1（"3.5.0"）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 11  D6: 10  D7: 11  D8: 11  D9: 3
- 小计: 94/100
- 关键依据:
  1. 四问在 09 一个文件内一步可查：① §1（39-58 行）var/record/文本块编译失败反例 + JDK 8 等价写法；② §2（60-68 行）`names.add("x"); // ✗ UnsupportedOperationException` + Collectors.toList() 替代；③ §4（89-99 行）ScopedValue + 指路 05 对比表；④ §3（70-87 行）synchronized 21 pin / 25 解除双代码。
  2. 门控判据双保险：SKILL:49-61 + 09 门控表（11-35 行）；门控表还含 Class-File API / Compact Object Headers 等 JVM 特性行（28-33 行）。
  3. D6 扣分：09 的通用语法示例段（136-255 行）与 SKILL 门控表及 02/05 内容重复，ScopedValue 在 09/05 双写；D9 扣分：05:162 用纯编号「详见 09 antipattern 3」引用（当前编号正确但脆弱）。
- 扣分主因: 09 内重复内容多（D6）；纯编号交叉引用（D9）。

### version2（"3.6.0"）
- D1: 12  D2: 10  D3: 12  D4: 10  D5: 10  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 92/100
- 关键依据:
  1. 四问判据全部仍可查（无 D3 重扣）：① SKILL:49-61 门控表 + 09 头部 3-4 行「JDK 8 项目全部禁用本文件特性」+ 门控表 12-15 行；② `02` 171 行「`Stream.toList()` 返回**不可变**列表；`Collectors.toList()` 返回可变」+ SKILL:58 括号注；③ `05` 164-191 行 Scoped Values 节含对比表；④ `09` §1（32-49 行）synchronized LTS 陷阱完整保留。
  2. D2 扣分：②③ 从 09 正文消失，需跳 02/05（09:88 行有指路）——rubric 预期「入口多一跳」。
  3. D4/D5 扣分：JDK 8 等价写法反例与 toList 的 `UnsupportedOperationException` 异常名明示均随 09 §1/§2 删除，需 agent 由「不可变」推断或自行降级；D9 满分：05:162 改语义引用「详见 09『synchronized LTS 版本陷阱』antipattern」，与 09 §1 标题可对上，抗重排。
- 扣分主因: ②③ 入口多一跳 + toList 异常名/降级写法需自行推断（D2/D4/D5）。

**差值: −2（v1 胜：09 内一步全查且示例可照抄；v2 靠 D6/D9 找回部分）**

---

## T11 · 对抗：常量与字面量规则

### version1（"3.5.0"）
- D1: 11  D2: 9  D3: 7  D4: 7  D5: 7  D6: 11  D7: 10  D8: 11  D9: 4
- 小计: 77/100
- 关键依据:
  1. 仅有 SKILL:127「魔法值直出 → 抽 static final 常量或枚举」+ `11` §8（86-100 行）禁魔法值示例（STATUS_LOCKED/TIMEOUT_MS/ROLE_ADMIN）+ 尾注「状态/类型码优先枚举，全局配置用常量类」——能答「要提取」。
  2. 三问答不出：无「≥2 处必须提取」机械判据（只有 `"ADMIN"` 散落多处」的模糊提示）；无常量放置判据（本类/包级/跨包/enum/配置五级）；无「Constants 万能类」禁令与 private 构造要求 → D3/D4 扣。
  3. SKILL:93 路由行为「命名/OOP 规约/格式」，无「常量」场景词——agent 需自行猜测归入 11 → D2/D7 扣。
- 扣分主因: 常量规则只有单行泛则，判据/放置/禁令三问全缺（D3/D4/D5/D2）。

### version2（"3.6.0"）
- D1: 11  D2: 12  D3: 12  D4: 12  D5: 11  D6: 12  D7: 12  D8: 11  D9: 4
- 小计: 97/100
- 关键依据:
  1. `11` §9（92-104 行）：「同一字面量出现 **≥2 处**即提取，不分同类跨类」+ `"PENDING"` 两类示例（与 prompt 场景完全同构）→ `OrderStatus.PENDING` / `OrderConstants.MAX_RETRY`。
  2. `11` §10（106-131 行）：五级放置判据表（本类/包级/跨包按域/enum/配置）+ 实现类堆常量反例（正中 prompt 的 `private static final` 不共享问题）+ `private OrderConstants() {}` 禁实例化 + 「✗ 禁 `Constants` 万能类（改一处全量重编译）」。
  3. 三处联动：SKILL:93 路由「常量与字面量」、SKILL:128 新规则行「字面量 ≥2 处未提取；常量堆在实现类中不共享」、SKILL:162 自检项「常量提取与放置」。
- 扣分主因: 无明显失分点（D5=11：private 构造仅代码注释一行，未展开）。

**差值: +20（v2 大胜：新规则机械可执行且三处联动；v1 仅单行泛则）**

---

## T12 · 对抗：Sonar 规则号删除后规则本体是否存活

### version1（"3.5.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 94/100
- 关键依据:
  1. 六条本体全部可查：① `11` §19（278-288 行）四类无用 import + SKILL:128「删掉最后一处使用同步删」；② `12` 行 3 阈值 ≤15 + 手法 1-5；③ `03` §1 + `05` §7（120-132 行）；④ `10` §8（90-103 行）MIN_VALUE 溢出返回自身 + `Math.absExact`；⑤ `03` §6 + SKILL:123；⑥ `08` 91-105 行 finally 抛异常掩盖原始异常。
  2. D6 扣分：全套 19 处 Sonar 规则号标注（`grep "S[0-9]{4}"` 命中 SKILL/02/03/05/08/10/11/12 共 19 行），对编码 agent 无行动价值——rubric 明示 D6 微扣。
  3. 无本体缺失（不触发 D3/D5 重扣）。
- 扣分主因: 19 处规则号元数据（D6）。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 11  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 96/100
- 关键依据:
  1. `grep "S[0-9]{4}" version2/` 零命中——规则号全删。
  2. 六条本体逐条核对全部存活且位置不变：① `11` §21（309-319 行）四类 import 原文相同；② `12` 行 3「≤ 15」；③ `05` §7 + `03` §1；④ `10` §8 含 `Math.absExact`；⑤ `03` §6 + SKILL:123（去号留本体）；⑥ `08` finally antipattern 原样。
  3. rubric 预期「另一版无号、本体完整 → D6 微升」成立。
- 扣分主因: 无明显失分点。

**差值: +2（v2 胜：本体零损失，去掉无行动价值元数据）**

---

## T13 · 对抗：编号顺移与交叉引用完整性

### version1（"3.5.0"）
- D1: 12  D2: 9  D3: 9  D4: 10  D5: 11  D6: 11  D7: 9  D8: 11  D9: 3
- 小计: 85/100
- 关键依据:
  1. ①④ 可解析：`12` 手法 5（134 行）「11-conventions 第 15 条」→ `11` §15 确为「复杂布尔表达式先赋具名变量」（超 3 个逻辑子条件必须拆，224 行）；`11` §1–19 连续无断号。② 可解析：`05` 162 行「详见 09 antipattern 3」→ 09 §3 为 synchronized LTS 陷阱。
  2. ③ 落空：SKILL:93 路由行为「命名/OOP 规约/格式」，全文无「常量与字面量」场景词，`11` 也无同名节（仅「常量定义」小节）——顺着题面查路由查不到 → D2/D3 扣。
  3. D9/D7 扣分：①② 均为**纯编号**引用（「第 15 条」「antipattern 3」），11 内部规则增删后即错位——rubric 判「脆弱」，当前虽对但抗演化差。
- 扣分主因: 路由表无「常量与字面量」条目（③ 不可查）+ 纯编号引用脆弱。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 11  D6: 11  D7: 12  D8: 11  D9: 4
- 小计: 97/100
- 关键依据:
  1. ① 语义引用：`12` 133 行「11-conventions『复杂布尔表达式先赋具名变量』」→ `11` §17（239 行）同名标题精确命中，抗重排。
  2. ② `05` 162 行「详见 09『synchronized LTS 版本陷阱』antipattern」→ `09` §1 标题「虚拟线程 + synchronized 的 LTS 版本陷阱」可对上。③ SKILL:93 路由「命名/OOP 规约/格式/**常量与字面量**」→ `11` 74 行同名节标题存在。④ `11` §1–21 连续无断号（新增 §9/§10 插入后整体顺移，无跳号）。
  3. 全套无悬空引用（02→09 Gatherers、09:88→05、10:20→01 均可解析）。
- 扣分主因: 无明显失分点。

**差值: +12（v2 胜：路由补词 + 语义化引用 + 编号顺移无断号）**

---

## T14 · 对抗：示例删除后的综合可执行性（兜底）

### version1（"3.5.0"）
- D1: 12  D2: 12  D3: 12  D4: 12  D5: 11  D6: 10  D7: 11  D8: 11  D9: 4
- 小计: 95/100
- 关键依据:
  1. 五块全可照抄：判空（`02` 速查 11-13 行）；分块（antipattern 1 的 `ListUtil.partition(list, 50)`）；线程池（`05` antipattern 1 构造 + §3 关闭 + **TaskRunner 215-218 行 `pool.submit(() -> { try {...} catch (Throwable t) { log.error("任务 #{} 失败", idx, t); } })` 单任务异常隔离**）；金额（`10` 推荐示例 119-134 行 multiply → setScale(2, HALF_UP) → compareTo 整合链）；拷贝（`06` 106 行 ignoreNullValue）。
  2. D6 扣分：上述可照抄代码一半来自与正文复述的推荐示例尾节。
  3. 无任何一块缺失。
- 扣分主因: 承载照抄代码的尾节本身冗余（D6）。

### version2（"3.6.0"）
- D1: 12  D2: 12  D3: 12  D4: 10  D5: 11  D6: 12  D7: 11  D8: 11  D9: 4
- 小计: 95/100
- 关键依据:
  1. 五块知识全在：判空/分块同 v1；线程池完整形态在 `05` antipattern 1（构造+命名工厂+拒绝策略）+ §3（shutdown/awaitTermination）；拷贝忽略 null 在 `06` 速查表 15 行（比 v1 更靠前）。
  2. D4 扣分两处：①「单任务异常隔离记日志」的 submit 内 try-catch 模式从全部文件消失（grep `catch (Throwable` 在 v2/05 零命中），需 agent 用 08 的 catch+log 范式自行组合；②金额 multiply→setScale 整合链拆在 `10` §1（32 行 multiply）与速查 16/18 行（setScale），无一行整合示例。
  3. 不构成 rubric 的重扣级缺陷：线程池完整形态与拷贝忽略 null（rubric 点名的两处）都在；属「拼装成本上升」而非「查不到」。
- 扣分主因: 异常隔离模式与金额整合链需拼装（D4 −2），被删冗余的 D6 +2 找平。

**差值: 0（持平：删示例的 D4 损失与删冗余的 D6 收益对冲——rubric「删除无损失」基本成立，唯异常隔离模式小降）**

---

## 总分表

| Prompt | version1（"3.5.0"） | version2（"3.6.0"） | 差值（v2 − v1） |
|---|---|---|---|
| T1 判空+Optional | 94 | 96 | +2 |
| T2 集合分块分组 | 93 | 95 | +2 |
| T3 日期时间 | 95 | 96 | +1 |
| T4 IO/HTTP/JSON | 94 | 94 | 0 |
| T5 线程池异步 | 94 | 96 | +2 |
| T6 BigDecimal | 94 | 96 | +2 |
| T7 加密哈希 | 94 | 96 | +2 |
| T8 异常日志随机 | 94 | 96 | +2 |
| T9 判据迁移 | 92 | 96 | +4 |
| T10 09 精简 | 94 | 92 | −2 |
| T11 常量规则 | 77 | 97 | +20 |
| T12 规则本体 | 94 | 96 | +2 |
| T13 交叉引用 | 85 | 97 | +12 |
| T14 综合可执行 | 95 | 95 | 0 |
| **合计** | **1289** | **1338** | **+49** |

## 最大分歧点小结（≤5 条）

1. **T11 常量规则（+20，最大分歧）**：v2 的 `11` 新增 §9（≥2 处判据 + "PENDING" 双类示例）与 §10（五级放置表 + 禁 Constants 万能类 + private 构造），并有 SKILL 路由行（93 行）/规则行（128 行）/自检项（162 行）三处联动；v1 仅 SKILL:127 一行泛则，判据、放置、禁令三问全答不出。
2. **T13 交叉引用（+12）**：v2 路由表补「常量与字面量」词、`12`→`11` 与 `05`→`09` 改语义引用（规则名/标题名）、`11` 重编号 §1–21 无断号；v1 路由无该词致 T13③ 不可查，且「第 15 条」「antipattern 3」纯编号引用脆弱（D9 3/4）。
3. **T9 判据迁移（+4）**：v2 把 subAfter isLast（01:21）、拷贝忽略 null（06:15）、千分位 Locale.US + String.format 边界（10:18+20）全部折入头部速查表查表即得；v1 同四条判据埋在文件尾推荐示例（01:107、06:106、10:135/139），需通读全文件。
4. **T10 09 精简（−2，唯一 v1 胜）**：v1 的 09 自带 JDK 8 误用反例 + 等价写法（§1）、toList `UnsupportedOperationException` 明示（§2）、ScopedValue antipattern（§4），四问一步可查；v2 判据仍全可查但 ②③ 需跳 02/05，toList 异常名与降级写法要自行推断——v2 靠 D6（精简）与 D9（语义引用）追回大部分。
5. **回归集普遍 +1~2（T1/T2/T3/T5/T6/T7/T8/T12）**：v2 删除 8 个 reference 的「推荐示例」复述尾节与 19 处 Sonar 规则号，D6 普涨而判据本体（partition 警告在 02 文件头、线程池完整形态在 05 antipattern 1/3/6、发号器判据在 08:203、千分位在 10 速查）无一缺失；唯 T4/T14 两处小损（04 手拼 JSON 反例、05 TaskRunner 异常隔离模式）使这两条 prompt 持平。
