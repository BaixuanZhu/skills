# 达尔文盲评报告（Agent A）

> **标签映射**：version1 = v3.3.0（旧版），version2 = v3.4.0（新版）。打分时不知此映射。
> **独立性**：完全独立，不知 Agent B 存在。仅依据快照字面内容打分。

## 关键事实核验（先于打分，作为判分基础）

- **SKILL.md 真实存在的节标题**（两版 SKILL.md 标题完全一致）：`## C-CHECK 询问（仅高风险能力缺失时触发）`（SKILL.md L128）。**不存在**「必选依赖」「依赖坐标」这两个节。
- **坐标真值源位置**：SKILL.md L141 的 blockquote（"其他构件参考版本：MapStruct 1.5.5.Final...OkHttp3 4.12.0...SLF4J 2.0.13..."）—— 在「C-CHECK 询问」节内。
- **version1 悬空引用 5 处**（grep 实证）：04 L96「必选依赖」、04 L129「必选依赖」、06 L98「必选依赖」、07 L102「依赖坐标」、08 L254「必选依赖」—— 全部指向不存在的节。
- **version2**：同 5 处指针全部改为「C-CHECK 询问（仅高风险能力缺失时触发）」，节真实存在。
- **「强约束提醒」节**：version1 在 01/02/03/04/05/06/07/08/09/10 末尾普遍存在；version2 全部删除（精简冗余）。
- **真值源未丢**：version2/05 L164「Scoped Values」节完整保留（基本用法 L169-176、嵌套绑定 L178-184、对比表 L186-191）。

---

### Prompt T1（字符串判空手写 + Optional.get() 不判空，项目有 Hutool）
- **version1**: D1:12 D2:11 D3:12 D4:12 D5:11 D6:9 D7:11 D8:11 D9:4 = 93/100
  依据: 1. SKILL.md L74-75 路由 + L115 A 级 `trim().isEmpty()` 行直接命中；2. version1/01 L80-95 Optional 节明确 `findUser(id).get()` ✗ → `orElse/orElseThrow` ✓（L84-85）；3. version1/01 L9-10 速查表命中 `isBlank`。
  扣分主因: D6——01 末尾「强约束提醒」节 L127-134 逐条复述速查表/antipattern 已表达的规则（如 L129「必须 StrUtil.isBlank」与 L10/L37 重复）。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:11 D6:11 D7:11 D8:11 D9:4 = 95/100
  依据: 1. 路由同 v1（SKILL.md L74-75/L115）；2. version2/01 L80-95 Optional 节内容与 v1 逐字一致；3. version2/01 删除冗余「强约束提醒」节（文件止于 L125），核心规则仍在速查表+antipattern。
  扣分主因: 同 v1 主体内容，差异仅在去掉冗余节，故 D6 略升；其余维度持平。

---

### Prompt T2（subList 分块 + 分组转 Map + 确认 CollUtil.groupBy/shuffle，回归重点）
- **version1**: D1:12 D2:11 D3:10 D4:8 D5:11 D6:8 D7:11 D8:11 D9:3 = 85/100
  依据: 1. version1/02 L15/L39 推荐 `CollUtil.partition(list, size)`——但据 version2/02 L5/L16，`partition` 在 `ListUtil` 不在 `CollUtil`，v1 给出的 API 名错误，agent 照写会编译失败（D4 重扣）；2. version1/02 L52/L197 保留 `CollUtil.groupBy 不存在` 判据，L198 保留 `CollUtil.shuffle 不存在 → Collections.shuffle`（回归重点判据未丢）；3. version1/02 L44-58 antipattern 2 覆盖分组，L60-68 antipattern 3 覆盖 toMap。
  扣分主因: D4——`CollUtil.partition` 是错误 API（正确为 `ListUtil.partition`），可执行性受损；D6——末尾「强约束提醒」L192-201 整段重复速查表。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:11 D7:11 D8:11 D9:4 = 96/100
  依据: 1. version2/02 L5/L16/L39/L182 统一改为 `ListUtil.partition`，并显式标注「CollUtil 无 partition」；2. version2/02 L60 把 `CollUtil.shuffle 不存在` 与 `CollUtil.toMap 签名` 合并进 antipattern 2 注释，判据保留；3. version2/02 删冗余「强约束提醒」节。
  扣分主因: 仅 D2/D7 微扣（`ListUtil`/`CollUtil` 拆类后需多读 L5 提示），整体正确且更准。

---

### Prompt T3（SimpleDateFormat 共享 + 裸 LocalDateTime.now() + 遗留 Date）
- **version1**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:9 D7:11 D8:11 D9:4 = 94/100
  依据: 1. version1/03 L27-41 antipattern 1 命中 `static SimpleDateFormat SDF`，给 DateTimeFormatter + DateUtil 双方案；2. version1/03 L86-102 antipattern 6 命中裸 `now()`，含 UTC 容器 8 小时坑 + Sonar S8688 + Clock 注入；3. version1/03 L127-138 DateUtil 遗留 Date 场景。
  扣分主因: D6——L140-146「强约束提醒」复述 antipattern 1/6 已写清的规则。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:11 D7:11 D8:11 D9:4 = 96/100
  依据: version2/03 核心内容（antipattern 1/6、DateUtil 节）与 v1 逐字一致（L27-41、L86-102、L127-138），仅删 L140-146 冗余节。
  扣分主因: 与 v1 相同主体，D6 因去冗余微升。

---

### Prompt T4（读 UTF-8 文件 + 复制文件 + HTTP GET 拿 JSON 反序列化，纯 Java 无 Spring）
- **version1**: D1:12 D2:10 D3:12 D4:8 D5:11 D6:9 D7:7 D8:11 D9:3 = 83/100
  依据: 1. version1/04 L9-24 速查表覆盖 readUtf8String/copyFile/IoUtil.copy；2. version1/04 L65-88 OkHttp3 GET + L98-118 Jackson 反序列化完整；3. **悬空引用**：version1/04 L96「坐标见 SKILL.md「必选依赖」」、L129「Jackson 坐标见 SKILL.md「必选依赖」」——SKILL.md 无此节，坐标实际在「C-CHECK 询问」blockquote（L141），agent 跟指针走断链找不到 OkHttp3/Jackson 坐标（D4/D7 重扣）。
  扣分主因: D4+D7——HTTP/JSON 依赖坐标指针走断链（功能性缺陷），纯 Java 项目无坐标无法落地 OkHttp3/Jackson。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:11 D6:11 D7:11 D8:11 D9:4 = 95/100
  依据: version2/04 L96/L129 改为「坐标见 SKILL.md「C-CHECK 询问（仅高风险能力缺失时触发）」」——节真实存在，一跳到位（SKILL.md L141 给出 OkHttp3 4.12.0 / Jackson 2.17.1）；其余内容与 v1 一致。
  扣分主因: 仅 D2/D5 微扣（坐标在 SKILL.md 而非本文件，需一次跳转）。

---

### Prompt T5（Executors.newFixedThreadPool(10) + CompletableFuture.supplyAsync 链式）
- **version1**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:9 D7:11 D8:11 D9:4 = 94/100
  依据: 1. version1/05 L22-43 antipattern 1 命中 `Executors.newFixedThreadPool`，给完整 ThreadPoolExecutor + 有界队列 + 命名工厂 + CallerRunsPolicy；2. version1/05 L134-148 CompletableFuture 节明确 `supplyAsync` 不传 executor 会用 commonPool 跑阻塞 IO（命中 prompt 的 `supplyAsync(() -> fetchUser)`）；3. version1/05 L47-55 拒绝策略表 + L55 覆盖默认说明。
  扣分主因: D6——L229-239「强约束提醒」整段复述 antipattern 1 + CompletableFuture 节。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:11 D7:11 D8:11 D9:4 = 96/100
  依据: version2/05 核心（antipattern 1、CompletableFuture 节、拒绝策略表）与 v1 逐字一致，仅删 L229-239 冗余节。
  扣分主因: 与 v1 相同主体，D6 因去冗余微升。

---

### Prompt T6（bd1.divide(bd2) + equals 比较 scale，回归重点）
- **version1**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:8 D7:11 D8:11 D9:4 = 93/100
  依据: 1. version1/10 L44-51 antipattern 3 命中裸 divide 抛 ArithmeticException，给 `divide(bd2, scale, RoundingMode.HALF_UP)`；2. version1/10 L53-60 antipattern 4 命中 `equals` 比 scale，给 `compareTo == 0`；3. **回归重点判据全保留**：L90-102 antipattern 8 `Math.abs(Integer.MIN_VALUE)` 仍为负（S2133）、L105-114 antipattern 9 `byte & 0xFF` 符号扩展（S3037）—— v1 末尾「强约束提醒」L161/L162 也有，属冗余但判据未丢。
  扣分主因: D6——L153-162「强约束提醒」逐条复述 antipattern 3/4/8/9 与速查表，冗余明显。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:11 D7:11 D8:11 D9:4 = 96/100
  依据: version2/10 保留全部 antipattern 3/4/8/9（L44-51、L53-60、L90-102、L105-114）—— 回归重点判据 `Math.abs(MIN_VALUE)` 与 `byte & 0xFF` 均在；删 L153-162 冗余节后规则仍完整覆盖。
  扣分主因: 与 v1 相同主体，D6 因去冗余升至 11；判据零丢失（符合 rubric T10 预期）。

---

### Prompt T7（手搓 MessageDigest + Integer.toHexString；密码用 SecureUtil.md5）
- **version1**: D1:12 D2:10 D3:12 D4:10 D5:12 D6:9 D7:8 D8:11 D9:3 = 87/100
  依据: 1. version1/07 L23-34 antipattern 1 命中手搓 MessageDigest 漏 `%02x`，给 SecureUtil.md5/sha256；2. version1/07 L36-44 antipattern 2 命中无盐 MD5 存密码，给 BCrypt.hashpw；3. **悬空引用**：version1/07 L102「Hutool BOM 见 SKILL.md「依赖坐标」」——SKILL.md 无「依赖坐标」节（坐标在「C-CHECK 询问」），agent 跟指针断链（D4/D7 扣）。
  扣分主因: D4+D7——crypto 模块坐标指针走断链（虽本文件 L102 已说明 `SecureUtil/DigestUtil/BCrypt/AES 均在 hutool-crypto`，但 BOM 版本号取不到）；D6 末尾「强约束提醒」L104-109 复述。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:11 D7:11 D8:11 D9:4 = 96/100
  依据: version2/07 L102 改为「见 SKILL.md「C-CHECK 询问（仅高风险能力缺失时触发）」」——节真实存在，可取 hutool-bom 5.8.47；其余 antipattern 1/2 内容与 v1 逐字一致；删 L104-109 冗余节。
  扣分主因: 仅 D2/D5 微扣。

---

### Prompt T8（catch(Exception){} 空吞 + log.error 拼接 + Math.random 当订单序号）
- **version1**: D1:12 D2:10 D3:12 D4:10 D5:12 D6:9 D7:8 D8:11 D9:3 = 87/100
  依据: 1. version1/08 L48-65 antipattern 命中空 catch + getMessage() NPE；2. version1/08 L16-35 命中 `log.error("失败:" + e.getMessage())` 拼接，给占位符 + 异常末参；3. version1/08 L201-212 命中 `(int)(Math.random()*100000)` 当序号，给 Redis INCR/雪花 ID；4. **悬空引用**：version1/08 L254「坐标与 JDK 门控见 SKILL.md「必选依赖」」——节不存在（D4/D7 扣）。
  扣分主因: D4+D7——SLF4J/Logback 坐标 + JDK 门控指针走断链；D6 末尾「强约束提醒」L257-267 整段复述。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:11 D7:11 D8:11 D9:4 = 96/100
  依据: version2/08 L249 改为「见 SKILL.md「C-CHECK 询问...」」——节真实存在（SKILL.md L141 给 SLF4J 2.0.13 + Logback，JDK 8 用 1.7.36）；三个 antipattern 内容与 v1 逐字一致；删 L257-267 冗余节。
  扣分主因: 仅 D2/D5 微扣。

---

### Prompt T9（对抗·悬空引用：MapStruct 1.5.5.Final 完整坐标 + annotation processor + OkHttp3 坐标，技能里哪里找）
- **version1**: D1:12 D2:4 D3:12 D4:4 D5:10 D6:9 D7:4 D8:11 D9:3 = 69/100
  依据: 1. **断链实证**：version1/06 L98「MapStruct 坐标与 annotation processor 配置见 SKILL.md「必选依赖」」、version1/04 L96「OkHttp3...坐标见 SKILL.md「必选依赖」」——SKILL.md 标题列表（L22-156）**无「必选依赖」节**，agent 跟指针走不到坐标；2. 坐标真值实际在 SKILL.md L141「C-CHECK 询问」节的 blockquote（MapStruct 1.5.5.Final/OkHttp3 4.12.0），但 v1 指针未指向该节；3. prompt 明确问「技能里哪里能找到」，v1 给出的定位是错误节名。
  扣分主因: **功能性缺陷**——D2/D4/D7 重扣（指针指了不存在的节，agent 走断链找不到坐标，符合 rubric T9「≤4 分」锚点）。坐标本身在 SKILL.md 里有（D3 不扣），但定位不到。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:11 D6:11 D7:11 D8:11 D9:4 = 95/100
  依据: version2/06 L98 + version2/04 L96/L129 全部改为「见 SKILL.md「C-CHECK 询问（仅高风险能力缺失时触发）」」——该节真实存在（SKILL.md L128），blockquote（L141）含 MapStruct 1.5.5.Final（含 annotation processor 提示）+ OkHttp3 4.12.0 + Jackson 2.17.1 + SLF4J 2.0.13。agent 一跳到位。
  扣分主因: 仅 D2/D5/D7 微扣（坐标在 SKILL.md 而非 reference 本文件，需一次跨文件跳转）。

---

### Prompt T10（对抗·删强约束提醒：BigDecimal 除法/比较/RoundingMode/Math.abs 边界，规则在哪）
- **version1**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:8 D7:11 D8:11 D9:4 = 93/100
  依据: 1. version1/10 速查表 L8-17 + antipattern 3（L44-51 除法）+ antipattern 4（L53-60 equals/compareTo）+ antipattern 6（L72-79 ROUND_*/RoundingMode）+ antipattern 8（L90-102 Math.abs MIN_VALUE）+ antipattern 9（L105-114 byte & 0xFF）——全部判据都在；2. 规则定位清晰（速查表 + antipattern 双层）。
  扣分主因: D6——L153-162「强约束提醒」节逐字复述 antipattern 3/4/6/8/9 + 速查表（如 L157「除法必须给 scale」与 L12/L50 重复，L161「Math.abs(MIN_VALUE)」与 L90-103 重复），信息密度受损。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:11 D7:11 D8:11 D9:4 = 96/100
  依据: version2/10 删 L153-162「强约束提醒」节后，全部判据仍在速查表 + antipattern 3/4/6/8/9（行号同 v1）—— **零判据丢失**（符合 rubric T10「删冗余节本身不扣分，D6 反而微升」）。规则定位不受影响。
  扣分主因: 与 v1 相同主体，D6 因去冗余升至 11。

---

### Prompt T11（对抗·跨文件去重：JDK 25 ScopedValue 完整用法 + 嵌套绑定 + 与 ThreadLocal 对比表，哪个 reference，09 有无重复）
- **version1**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:7 D7:10 D8:11 D9:3 = 90/100
  依据: 1. **真值源在 05**：version1/05 L164-191「Scoped Values」节完整（基本用法 L169-176 + 嵌套绑定 L178-184 + 对比表 L186-191）—— prompt 三项需求全覆盖；2. **跨文件冗余**：version1/09 antipattern 4（L90-102）重复贴 `ScopedValue.where(...)` 完整代码 + ThreadLocal 三害详述，且 version1/09 L228-237「推荐示例」又贴第三份完整 ScopedValue 代码——同内容三处出现（D6 重扣）；3. version1/05 L87-98 antipattern 5 也有一份 ThreadLocal→ScopedValue 对照（第四处）。
  扣分主因: D6——ScopedValue 完整代码/解释在 05（L164-191）+ 05 antipattern 5（L87-98）+ 09 antipattern 4（L90-102）+ 09 推荐示例（L228-237）四处重复，agent 易困惑真值源；D7 略扣（多份重复时定位"权威"需判断）。
- **version2**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:11 D7:11 D8:11 D9:4 = 96/100
  依据: 1. **真值源仍在 05**：version2/05 L164-191 与 v1 逐字一致（完整 API + 嵌套 + 表），未被误删（符合 rubric「真值源不丢」）；2. **09 去重**：version2/09 antipattern 4（L89-99）精简为单行 `ScopedValue.where(CTX, context).run(...)` + 指针「API 细节、对比表、嵌套绑定示例见 05-concurrency.md「Scoped Values」」（L99）；3. version2/09 推荐示例 L225-234 保留一份基础代码（作为版本门控示例，非纯重复）。
  扣分主因: 仅 D6/D7 微扣（09 推荐示例仍有一份 ScopedValue 代码，但属示例必要性，非冗余）。

---

## 汇总表

| Prompt | version1 小计 | version2 小计 | 差值 (v2 - v1) |
|--------|--------------:|--------------:|---------------:|
| T1  (判空+Optional)        | 93 | 95 | +2 |
| T2  (集合分块+groupBy/shuffle) | 85 | 96 | +11 |
| T3  (日期格式化+now)        | 94 | 96 | +2 |
| T4  (文件+HTTP+JSON)        | 83 | 95 | +12 |
| T5  (线程池+异步)           | 94 | 96 | +2 |
| T6  (BigDecimal 除法/比较)  | 93 | 96 | +3 |
| T7  (加密+密码哈希)         | 87 | 96 | +9 |
| T8  (异常+日志+随机序号)    | 87 | 96 | +9 |
| T9  (对抗·悬空引用坐标)     | 69 | 95 | +26 |
| T10 (对抗·删强约束提醒)     | 93 | 96 | +3 |
| T11 (对抗·跨文件去重 ScopedValue) | 90 | 96 | +6 |
| **合计** | **968** | **1064** | **+96** |

## 总体结论（基于内容，不预设版本对应）

- **version2 在全部 11 条上均 ≥ version1**，无任何回归。
- **回归集（T1-T8）**：T1/T3/T5/T6/T10 差距小（+2~+3），纯粹来自删除冗余「强约束提醒」节带来的 D6 提升，核心 antipattern 判据零丢失（T2 的 `CollUtil.shuffle 不存在`、T6 的 `Math.abs(MIN_VALUE)` + `byte & 0xFF` 在两版均保留）。T2 额外有 `CollUtil.partition` → `ListUtil.partition` 的 API 正确性修正（+11）。
- **对抗集（T9/T11）拉开最大差距**：T9 +26 是因为 version1 在 04/06/07/08 有 5 处指针指向 SKILL.md 不存在的「必选依赖」/「依赖坐标」节（坐标实际在「C-CHECK 询问」blockquote），agent 跟指针走断链找不到 MapStruct/OkHttp3/Jackson/SLF4J 坐标——这是 rubric 定义的功能性缺陷；version2 全部修正为指向真实存在的「C-CHECK 询问」节。T11 +6 是因为 version1 在 05 + 09 间有四处 ScopedValue 完整代码重复（D6 重扣），version2 将 09 antipattern 4 精简为单行 + 指针、保留 05 作为唯一真值源。
