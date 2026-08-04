# 达尔文盲评报告（Agent B，独立盲评）

> **标签映射**：versionA = v3.4.0（新版），versionB = v3.3.0（旧版）。打分时不知此映射。
> **独立性**：完全独立，不知 Agent A 存在。

## 两版系统性差异速览（打分依据基础）

通过逐文件对比，定位到两版 5 类系统性差异：

1. **「强约束提醒」节**：versionB 的 01/02/03/04/05/06/07/08/09/10 每个 reference 末尾都有「强约束提醒」节，逐条复述上方速查表/antipattern 已表达的规则（信息冗余，D6 扣分）；versionA 全部无此节。
2. **`> 铁律`/`> 为什么` 重述**：versionB 在 08 等文件的 antipattern 后追加多条 `> **铁律**：...` blockquote，重述代码注释已表达的规则（D6 扣分）；versionA 这些位置更精简或无。
3. **坐标指针悬空（功能性缺陷）**：versionB 的 04(L96,L129)/06(L98)/07(L102)/08(L254) 坐标指针指向 SKILL.md「必选依赖」/「依赖坐标」——**SKILL.md 无此两节**（坐标在「C-CHECK 询问（仅高风险能力缺失时触发）」节的 blockquote，SKILL.md L128/L135-141）；versionA 同四处指针均指向「C-CHECK 询问（仅高风险能力缺失时触发）」——该节真实存在，含坐标表。
4. **02 集合分块错误（功能性 bug）**：versionB 02 速查表 L15、antipattern 1(L39)、推荐示例 L180 用 `CollUtil.partition`——但 `partition` 在 `ListUtil` 不在 `CollUtil`，且 versionB L198「强约束提醒」自己又说 `CollUtil.shuffle 不存在`，构成自相矛盾（分块用不存在的 CollUtil.partition，却提醒 shuffle 不存在）。versionA 正确用 `ListUtil.partition` 并多处声明 `CollUtil.partition 不存在`。
5. **09 ScopedValue 跨文件冗余**：versionB 09 antipattern 4(L90-102) 重复贴完整 `ScopedValue.newInstance()`+`where().run()` 代码与解释，且推荐示例 L228-236 又贴一遍，与 05 真值源重复；versionA 09 antipattern 4 精简为 ✗/✓ 对照 + 指针「详见 05」。

---

### Prompt T1（字符串判空 + Optional.get 不判空，域 01）
- **versionA**: D1:11 D2:11 D3:11 D4:11 D5:11 D6:11 D7:11 D8:11 D9:4 = 92/100
  依据: 1. SKILL.md L74 路由表「判 null / Optional 取值 → 01」，01 L10/L15 速查表直击 `str==null||trim().isEmpty()` 与 `a.equals(b)`；2. 01 L80-95 Optional 规范节直击 `findUser(id).get()` → `orElse/orElseThrow`；3. 无「强约束提醒」冗余节，D6 满分。
- **versionB**: D1:11 D2:11 D3:11 D4:11 D5:11 D6:8 D7:11 D8:11 D9:4 = 89/100
  依据: 主体内容与 A 完全一致；L127-135「强约束提醒」节 6 条逐字复述速查表（L129「必须 StrUtil.isBlank」= L10；L133「Optional.get() 前 must isPresent」= L80）——纯冗余，D6 扣 3。

### Prompt T2（集合分块 + 分组 + CollUtil.groupBy/shuffle 确认，域 02，回归重点）
- **versionA**: D1:12 D2:11 D3:12 D4:12 D5:12 D6:11 D7:11 D8:11 D9:4 = 96/100
  依据: 02 速查表 L16「分块 → ListUtil.partition（CollUtil.partition 不存在）」正确且点名陷阱；antipattern 1(L39-40) `ListUtil.partition(list,50)` 可直接照抄，L60 同类误用提醒含 `CollUtil.shuffle 不存在`；antipattern 2(L52) `CollUtil.groupBy` 编译错误 + Stream 正解。
- **versionB**: D1:11 D2:10 D3:8 D4:5 D5:5 D6:7 D7:10 D8:11 D9:2 = 69/100
  依据: **功能性 bug**：速查表 L15、antipattern 1 L39、推荐示例 L180 均推荐 `CollUtil.partition`——实际在 `ListUtil`，agent 照抄编译错误（D4/D5 重扣）；**自相矛盾**：L198「强约束提醒」写「CollUtil.shuffle 不存在」却用不存在的 CollUtil.partition 做分块（D9 仅 2 分）；L60 的 shuffle 提醒仍在但核心判据被错误示例污染。

### Prompt T3（SimpleDateFormat 共享 + 裸 now() + 遗留 Date，域 03）
- **versionA**: D1:11 D2:11 D3:12 D4:11 D5:12 D6:11 D7:11 D8:11 D9:4 = 94/100
  依据: 03 antipattern 1(L27-41) 直击 `static SimpleDateFormat SDF` → DateTimeFormatter/DateUtil；antipattern 6(L86-102) 直击裸 `now()` → `now(ZONE)`/`now(clock)`，含 Sonar S8688 + 容器 UTC 错 8 小时；DateUtil 推荐节(L127-138) 覆盖遗留 Date。
- **versionB**: D1:11 D2:11 D3:12 D4:11 D5:12 D6:8 D7:11 D8:11 D9:4 = 91/100
  依据: 主体与 A 完全一致；L140-146「强约束提醒」节 6 条逐字复述速查表/antipattern ——纯冗余，D6 扣 3。

### Prompt T4（文件读写 + HTTP + JSON 手搓，域 04）
- **versionA**: D1:11 D2:11 D3:12 D4:12 D5:11 D6:11 D7:11 D8:11 D9:4 = 94/100
  依据: 04 速查表 L13-24 覆盖读 UTF-8/复制/流拷贝；antipattern 1(L28-44) 直击手搓 FileInputStream + close 不兜底；HTTP(L65-96) + JSON(L98-129) 完整；L96/L129 坐标指针指向「C-CHECK 询问」——真实存在（SKILL.md L128），坐标在 L141 blockquote。
- **versionB**: D1:11 D2:8 D3:12 D4:8 D5:11 D6:8 D7:7 D8:11 D9:4 = 80/100
  依据: 主体内容与 A 一致；**悬空引用**：L96「坐标见 SKILL.md「必选依赖」」、L129「Jackson 坐标见「必选依赖」」——SKILL.md **无「必选依赖」节**（坐标在「C-CHECK 询问」L141），agent 跟指针走断链（D2/D4/D7 扣）；L145-151「强约束提醒」节冗余（D6 扣）。

### Prompt T5（Executors.newFixedThreadPool + CompletableFuture.supplyAsync，域 05）
- **versionA**: D1:11 D2:11 D3:12 D4:11 D5:12 D6:11 D7:11 D8:11 D9:4 = 93/100
  依据: 05 antipattern 1(L22-43) 直击 `Executors.newFixedThreadPool(10)` 无界 OOM → 显式 ThreadPoolExecutor + 有界队列 + 命名工厂 + CallerRunsPolicy；L134-148 CompletableFuture 节直击 `supplyAsync` 不传 executor 用 commonPool → 必传自定义池；拒绝策略表(L47-54) + 覆盖默认说明(L55)。
- **versionB**: D1:11 D2:11 D3:12 D4:11 D5:12 D6:8 D7:11 D8:11 D9:4 = 90/100
  依据: 主体与 A 完全一致；L229-239「强约束提醒」节 9 条逐字复述速查表/antipattern ——纯冗余，D6 扣 3。

### Prompt T6（BigDecimal divide 裸除 + equals 比 scale，域 10，回归重点）
- **versionA**: D1:11 D2:11 D3:12 D4:12 D5:12 D6:11 D7:11 D8:11 D9:4 = 95/100
  依据: 10 速查表 L12「除法 → divide(bd2, scale, RoundingMode.HALF_UP)」、L13「相等 → compareTo()==0」；antipattern 3(L44) 除法、4(L53) equals、8(L90) Math.abs(MIN_VALUE)、9(L105) byte&0xFF 均在主体——回归判据无丢失。
- **versionB**: D1:11 D2:11 D3:12 D4:12 D5:12 D6:8 D7:11 D8:11 D9:4 = 92/100
  依据: antipattern 8/9 与 A 完全一致，判据无丢失（D3 满分）；L153-162「强约束提醒」节 8 条逐字复述速查表/antipattern ——纯冗余，D6 扣 4。

### Prompt T7（手搓 MessageDigest + SecureUtil.md5 存密码，域 07）
- **versionA**: D1:11 D2:11 D3:12 D4:11 D5:12 D6:11 D7:11 D8:11 D9:4 = 93/100
  依据: 07 antipattern 1(L23-34) 直击手搓 MessageDigest 漏 `%02x`；antipattern 2(L36-44) 直击无盐 MD5 存密码 → BCrypt.hashpw；L102 坐标指针指向「C-CHECK 询问」——真实存在，含 hutool-crypto 坐标。
- **versionB**: D1:11 D2:8 D3:12 D4:8 D5:12 D6:8 D7:7 D8:11 D9:4 = 81/100
  依据: 主体与 A 一致；**悬空引用**：L102「Hutool BOM 见 SKILL.md「依赖坐标」」——SKILL.md **无「依赖坐标」节**（BOM 在「C-CHECK 询问」L137），agent 跟指针断链（D2/D4/D7 扣）；L104-109「强约束提醒」节冗余（D6 扣）。

### Prompt T8（空 catch 吞 + log.error 拼接 + Math.random 当序号，域 08）
- **versionA**: D1:11 D2:11 D3:12 D4:11 D5:12 D6:10 D7:11 D8:11 D9:4 = 93/100
  依据: 08 L11-12 日志速查表直击 `log.error("失败:"+e.getMessage())`；L48-65 吞异常 antipattern、L75-89 InterruptedException、L121-139 catch Throwable；L196-207 Math.random 当序号 S 级（生日悖论碰撞）、L209-221 安全凭证 SecureRandom；L249 坐标指针指向「C-CHECK 询问」——真实存在。
- **versionB**: D1:11 D2:8 D3:12 D4:8 D5:12 D6:6 D7:7 D8:11 D9:4 = 79/100
  依据: 主体与 A 一致；**悬空引用**：L254「坐标见 SKILL.md「必选依赖」」——不存在（D2/D4/D7 扣）；**D6 重扣**：L75/L91/L108/L122/L143/L159 六处 `> **铁律**` 重述代码注释 + L257-267「强约束提醒」节再复述一遍——三重冗余。

### Prompt T9（对抗·悬空引用：MapStruct + OkHttp3 Maven 坐标）
- **versionA**: D1:11 D2:12 D3:12 D4:12 D5:11 D6:11 D7:12 D8:11 D9:4 = 96/100
  依据: 04 L96/L129、06 L98 坐标指针均指向「C-CHECK 询问（仅高风险能力缺失时触发）」——SKILL.md L128 真实存在；SKILL.md L141 blockquote 含完整坐标「MapStruct 1.5.5.Final（需 annotation processor）、Jackson 2.17.1、OkHttp3 4.12.0」；06 L80-98 MapStruct 完整示例。agent 一跳到位。
- **versionB**: D1:11 D2:4 D3:10 D4:4 D5:10 D6:8 D7:4 D8:11 D9:4 = 56/100
  依据: **功能性缺陷/断链**：04 L96/L129、06 L98 坐标指针指向「必选依赖」——SKILL.md **无此节**（grep 全文只有「C-CHECK 询问」「域→默认」「规则表」等节，无「必选依赖」）；agent 跟任一指针走都找不到节，坐标虽在 L141 blockquote 但指针没指向那里 → 断链。按 rubric 对抗集锚点「指针指了不存在的节名 → D2/D4/D7 重扣 ≤4」。

### Prompt T10（对抗·删强约束提醒：BigDecimal 除法/比较/RoundingMode/Math.abs 边界规则位置）
- **versionA**: D1:11 D2:12 D3:12 D4:12 D5:12 D6:12 D7:11 D8:11 D9:4 = 97/100
  依据: 速查表 L12-17 覆盖除法/比较/舍入；antipattern 3(L44)/4(L53)/6(L72)/8(L90)/9(L105) 全在主体；无「强约束提醒」节，规则集中在速查表+antipattern，D6 满分（判据零丢失，符合 rubric「删冗余节不扣分」）。
- **versionB**: D1:11 D2:12 D3:12 D4:12 D5:12 D6:8 D7:11 D8:11 D9:4 = 93/100
  依据: 判据完整性同 A（antipattern 8/9 都在，无丢失，D3 满分）；L153-162「强约束提醒」节 8 条逐字复述速查表/antipattern ——D6 扣 4。

### Prompt T11（对抗·跨文件去重：JDK 25 ScopedValue 完整 API 在哪 + 09 是否重复）
- **versionA**: D1:11 D2:12 D3:12 D4:11 D5:11 D6:12 D7:12 D8:11 D9:4 = 96/100
  依据: 05 L164-191「Scoped Values」节为真值源——含基本用法(L170-176)、嵌套绑定(L178-184)、对比表(L186-191)，完整；09 antipattern 4(L89-99) 精简为 ✗/✓ 一行对照 + 指针「API 细节、对比表、嵌套绑定示例见 05」——无跨文件重复；09 L225-234 推荐示例虽贴基本用法但带「详见 05」且无对比表重复。
- **versionB**: D1:11 D2:12 D3:12 D4:11 D5:11 D6:7 D7:11 D8:11 D9:4 = 90/100
  依据: 05 真值源完整（L164-191 与 A 一致，未误删，D3 满分）；**跨文件冗余**：09 antipattern 4(L90-102) 重复贴完整 `ScopedValue.newInstance()`+`where().run()` 代码 + 解释（与 05 L170-176 重复），且 09 L228-236 推荐示例又贴一遍；L260-269「强约束提醒」节再复述一遍 ScopedValue 要点。三处重复，D6 扣 5。

---

## 汇总表

| Prompt | 场景 | versionA 小计 | versionB 小计 | 差值 (A−B) |
|--------|------|---------------|---------------|-----------|
| T1 | 字符串判空 + Optional | 92 | 89 | +3 |
| T2 | 集合分块 + 分组（回归重点） | 96 | 69 | +27 |
| T3 | 日期格式化 + 裸 now() | 94 | 91 | +3 |
| T4 | 文件 IO + HTTP + JSON | 94 | 80 | +14 |
| T5 | 线程池 + 异步 | 93 | 90 | +3 |
| T6 | BigDecimal 除法/比较（回归重点） | 95 | 92 | +3 |
| T7 | 加密 + 密码哈希 | 93 | 81 | +12 |
| T8 | 异常 + 日志 + 随机 | 93 | 79 | +14 |
| T9 | 对抗·悬空引用（坐标断链） | 96 | 56 | +40 |
| T10 | 对抗·删强约束提醒（判据位置） | 97 | 93 | +4 |
| T11 | 对抗·跨文件去重（ScopedValue） | 96 | 90 | +6 |
| **合计** | | **1040** | **910** | **+130** |
| **平均** | | **94.5** | **82.7** | **+11.8** |

## 关键结论

**versionA 全面优于 versionB**，差距集中在两类问题：

1. **功能性缺陷（versionB 独有，重扣）**：
   - **坐标指针悬空**（T9/T4/T7/T8）：versionB 的 04/06/07/08 四个 reference 把坐标指针指向 SKILL.md 不存在的「必选依赖」/「依赖坐标」节（实际在「C-CHECK 询问」节）。agent 跟指针走断链，找不到 MapStruct/OkHttp3/Jackson/SLF4J/hutool-crypto 坐标。T9 因此失 40 分。
   - **集合分块错误**（T2）：versionB 推荐 `CollUtil.partition`（实际在 `ListUtil`），agent 照抄编译失败，且与自身「CollUtil.shuffle 不存在」提醒自相矛盾。T2 因此失 27 分。

2. **信息密度冗余（versionB 独有，普适性扣分）**：
   - versionB 每个 reference 末尾都有「强约束提醒」节逐字复述速查表/antipattern；08 还有多条 `> 铁律` blockquote 重述代码注释；09 重复贴 ScopedValue 完整代码。三重冗余导致 D6 在所有 prompt 上被扣 3-5 分，累积失分约 33 分。

**回归集（T1-T8）**：versionA 无退步；versionB 因 T2 分块 bug + T4/T7/T8 坐标断链在回归集上就已明显落后。

**对抗集（T9-T11）**：T9（悬空引用）两版差异最大（+40），正是 rubric 预期的「断链 vs 一跳到位」分化；T10（删强约束提醒）判据两版均完整未丢失，差异仅在 D6 冗余；T11（跨文件去重）真值源两版均在，差异在 09 是否重复（versionA 去重、versionB 重复）。
