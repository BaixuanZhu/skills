# java-coding-guide-pro 达尔文验证报告：v3.4.1 → v3.5.0（回归 + 对抗 + 实跑）

> **目的**：用达尔文「独立盲评 + 独立仲裁 + 棘轮 + 实跑测试」原则，证明 v3.5.0 相比线上 v3.4.1 **无质量下降**，且六类清理改动的根因真正生效。
> **日期**：2026-08-23
> **方法**：最小 Maven 项目实跑 43 项（JDK 21 + Hutool 5.8.47 BOM + 本轮新增四构件坐标）+ 2 个独立盲评 agent（A/B）+ 仲裁 agent + 棘轮。
> **结论**：✅ **PASS** —— 实跑 43/43 通过；回归集 T1-T8 双盲评零退步；对抗集 T9-T14 六类改动全部生效（T11 仲裁为中性，属设计预期）；A/B 总分方向一致（+52 / +56）；仲裁 0 虚构、0 独有判据丢失。

## 一、本轮改动概览（v3.4.1 → v3.5.0，4 个 commit：7f14c73 / 55b5c16 / 1c1ea3e / b301eaa）

| # | 改动 | 类型 |
|---|---|---|
| 1 | 删出处引用与 IDE 指引：11 头部「阿里巴巴手册吸收/来源/收录哲学」、11:291 IDE Optimize Imports（规则本体已在 SKILL A 级行）、7 处「阿里」标签（02/05/08/SKILL 路由） | 冗余清理 |
| 2 | JDK 版本策略：五档累加记法（+ 号串联、档位/实际版本双编号混排、非 LTS 无判据）→ 「特性 → 最低 JDK」平表 + 单条比较判据 | 表达机械化 |
| 3 | 高风险场景表 → 「风险分级与构件选择」两行清单（why 列与 S 级行重复、推荐列与域→默认表重复）；唯一独有规则「HTTP 超时必设」先行迁入 04 OkHttp 示例 | 冗余压缩 + 规则迁移 |
| 4 | 删 Sonar S3252 策略段（SKILL C-CHECK 节尾 + 01 整节）；字符串默认统一 StrUtil；构件版本一行 prose → 三列小表，SLF4J/Logback 门控对齐 08（补 Logback 1.5.x 版本、JDK 8 组合、禁混用） | 策略简化 + 口径对齐 |
| 5 | 规则表删「为什么」列：21 行纯论证删（reference 已有），6 处技术判据折入 ✗/✓ 单元格（月从 0 / 参数顺序相反 / 隐式时区+S8688 / 半开区间 / S1128 / S3776 阈值 15） | 冗余压缩 |
| 6 | description 次级触发信号具体化：判断语复合短语 → 字面可匹配 API 令牌 + 新增用户任务词通道 | 触发精度 |

## 二、实跑代码验证（达尔文强制项：实跑而非空想）

最小 Maven 项目（JDK 21，Hutool 5.8.47 BOM，**用本轮新表声明的全部构件坐标**：OkHttp 4.12.0 / Jackson 2.17.1 / SLF4J 2.0.13 + Logback 1.5.6 / MapStruct 1.5.5.Final + annotation processor），JUnit 断言 42 项全过 + JDK 8 日志组合 1 项 = **43/43 PASS**：

- **上轮 37 项全量回归**：BigDecimal 12（精度/compareTo/equals 连 scale/裸 divide 抛异常/scale+RoundingMode/不可变/Math.abs(MIN_VALUE)/byte&0xFF）、日期 3（DateUtil 并发安全/now(ZoneId)/currentSeconds）、线程池 1（手写有界+命名工厂+CallerRuns+优雅关闭）、加密 6（md5/sha256 已知向量/BCrypt 加盐校验/Base64 往返/手搓 hex 丢前导零演示）、随机 2（randomInt 半开 10 万次采样/SecureRandom 6 位验证码）、字符串集合 13（isBlank/blankToDefault vs emptyToDefault/subAfter/split/命名转换/join/ObjectUtil.equal/CollUtil.isEmpty/ListUtil.partition/Arrays.asList 固定大小/BeanUtil 拷贝顺序/format/trimToNull）
- **本轮新增 5 项（v3.5.0 新声明的实跑验证）**：
  1. **OkHttp 超时真实生效**：本地 HttpServer 延迟 2s + `.readTimeout(300ms)` → 实测抛 `SocketTimeoutException`——04 新示例代码可直接照抄且行为符合声明
  2. **SLF4J 2.0.13 绑定 Logback 1.5.6**：占位符日志运行，ILoggerFactory 确认 Logback 绑定
  3. **Jackson 2.17.1**：ObjectMapper 序列化/反序列化往返
  4. **MapStruct 1.5.5.Final**：annotation processor 编译期生成 Impl，映射字段正确（同时验证 T9 坐标可执行）
  5. **StrUtil / CharSequenceUtil API 事实一致**（01 删「继承」注后 API 行为不变）
- **JDK 8 日志组合 1 项**：`javac --release 8` 编译 + 运行 `slf4j-api 1.7.36 + logback 1.2.13`，输出 `[main] INFO TinyLog8 - jdk8 combo ok`——新版本表「JDK 8 用 1.7.36 + 1.2.x」组合真实可用
- **交叉验证**：技能 06:5 声明的 `cn.hutool.core.bean.BeanUtil` 包名在实跑中验证正确（评估脚手架第一次反而写错成 core.util）

**脚手架插曲（3 bug 均与技能内容无关，如实记录）**：测试代码 import 包名错 2 处（BeanUtil 应在 core.bean、CharSequenceUtil 应在 core.text）+ `CollUtil.isEmpty(null)` 重载歧义 1 处；环境坑 2 处（Git Bash 需 Windows 格式 classpath、Scoop Maven 的 localRepository 在 `G:\Scoop\apps\maven\3.9.16\repository` 而非 `~/.m2`）。

## 三、三层独立验证

| 层 | agent | 角色 | 独立性 |
|----|-------|------|--------|
| 1 | Agent A | 双盲打分（version1=v3.4.1, version2=v3.5.0） | 完全独立，不知 B 存在 |
| 2 | Agent B | 双盲打分（应拿 versionA=v3.5.0, versionB=v3.4.1，实际读对内容但**报告标签写反**，见 §六） | 完全独立，不知 A 存在 |
| 3 | 仲裁 agent | 复核 A/B 证据（全量 ~145 处）+ 标签复核 + T11 裁决 + 查漏 + 棘轮 | 读 A/B 报告，独立 grep/diff 实测核实 |

## 四、盲评结果

### 总分对比（两 agent 一致判定 v3.5.0 优于 v3.4.1）

| | Agent A | Agent B |
|---|---|---|
| v3.4.1 | 1263/1400（90.2 均） | 1231/1400（87.9 均） |
| v3.5.0 | **1315/1400（93.9 均）** | **1287/1400（91.9 均）** |
| **差值（新−旧）** | **+52** | **+56** |

> B 比 A 严约 2.3 分/版，属评分尺度差；方向完全一致。基线轮（v3.4.0）双盲评 96.7/94.5 均分——本轮口径新增 6 条对抗 prompt（14 vs 11 条）、且旧版承担了本轮对抗集的全部失分，均分不直接跨轮可比，**差值**才是关键。

### 单 prompt 差值（新−旧；A = version2−version1，B 按其配对 = 新−旧）

| Prompt | 场景 | A | B | 共识 |
|---|---|---:|---:|---|
| T1 判空+Optional | +1 | +1 | ✅ 无退步（删 S3252 段后默认唯一） |
| T2 集合分块/分组 | 0 | +1 | ✅ 无退步 |
| T3 日期+now | 0 | 0 | ✅ 未碰 |
| **T4 文件+HTTP+JSON** | **+13** | **+8** | ✅ 旧版 OkHttp 示例无超时（最大退步点之一） |
| T5 线程池+异步 | 0 | +1 | ✅ 无退步（删 Guava 备注无损失） |
| T6 BigDecimal | 0 | 0 | ✅ 未碰 |
| T7 加密+密码 | 0 | +2 | ✅ 无退步 |
| T8 异常+日志+随机 | +1 | +1 | ✅ why 列删后判据在 reference 可查 |
| T9 规约/import 可查性 | +3 | +3 | ✅ 删出处/IDE 行后规则本体完整 |
| **T10 JDK 门控判据** | **+6** | **+11** | ✅ 五档累加 → 平表单判据，非 LTS（JDK 16）有明确答案 |
| T11 S3252/StrUtil | +1 | −2 | ⚖ 分歧→仲裁裁 ≈0 中性（见 §六） |
| **T12 C-CHECK+HTTP 超时** | **+14** | **+15** | ✅ 超时规则从断言变落地代码 |
| T13 六判据折入 | +1 | +2 | ✅ 0 丢失 |
| **T14 构件版本/日志门控** | **+12** | **+13** | ✅ Logback 版本补全、两套组合一次查全 |

## 五、对抗集核心证据（仲裁全量核实，0 虚构）

- **T4/T12（HTTP 超时）**：旧版 04:68 `new OkHttpClient()` 裸建、全文件无任何超时；「超时缺省」仅作为 SKILL 高风险表 why 列的断言存在——断言与示例脱节。新版 04:67 规则行 + 70-73 行 `.connectTimeout/.readTimeout` 可直接照抄，实跑证明超时真实触发。
- **T10（JDK 门控）**：旧版回答「JDK 16 能否用 record」需自行串联「JDK 17：+ record(16)」并倒推，非 LTS 无 SKILL 级判据；新版平表一次比较（16 ≥ 16 → 可用），判据句明示「非 LTS 同样按版本比较」。
- **T14（版本表）**：旧版一行 prose 无 Logback 版本号、JDK 8 组合要跳 08 才拼得出；新版三列表 `SLF4J 2.0.13 + Logback 1.5.x（JDK 11+）；JDK 8 用 1.7.36 + 1.2.x，禁混用` 一次查全，两套组合均实跑验证。
- **T9/T13（删而不丢）**：19 条命名规约、import 同步删除规则、六折入判据全部可查，出处标注/IDE 快捷键/收录哲学行删除后无一条规则丢失。

## 六、透明记录：标签缺陷与 T11 分歧

1. **blind-B 标签写反**：其报告自述「versionA=3.4.1」与目录映射（versionA=3.5.0）相反。仲裁逐条核验其全部行号引用：所有「A」引用命中 v3.4.1 独有内容（多数行号在 v3.5.0 中越界不存在）、所有「B」引用命中 v3.5.0 独有内容——**评的是对的内容，只是报告内标签反了，配对有效**（1231/1287 可直接对齐 A 的 1263/1315）。四个打乱目录经 `diff -r` 字节级核实与真快照一致。后续轮改进：要求盲评 agent 粘贴 frontmatter 原文作为方法节证据。
2. **T11 分歧裁决**：A 判新版 +1（删 S3252 后默认唯一、密度升），B 判旧版 +2（保留该段能回答「门禁扫出来怎么办」的追问）。仲裁裁决 ≈0 中性：写判空主路径无损失、密度 +1~+2；门禁追问边缘路径覆盖 −2~~3（rubric 明示该职责外追问不重罚，B 的三处扣罚与其本人在 T1 的判定不自洽）。删除属设计预期（用户决策：S3252 不属编码指南职责），**不构成退步**。

## 七、仲裁结论：PASS

1. **证据真实性**：A/B 合计 ~145 处行号引用全量核验——虚构 0；偏差 1（blind-A 一处 off-by-one，不影响结论）。
2. **回归集**：T1-T8 双盲评零退步（旧版无一项高于新版）。
3. **对抗集**：六类改动全部生效；T11 中性属设计预期。
4. **独立查漏**：0 独有技术判据丢失——旧 S3252 节「同类门面」句自洽删除无孤儿引用；11 的「聚焦 X/Y/Z」由五个节标题逐词承接；「纯 JDK 无额外依赖」保留在 05:29；高风险表 why 列 6 行信息 5 行完整承接、「连接泄漏」词面消失但其操作判据（try-with-resources、单例连接池）在 04 保留；彩虹表/中断丢失/日志关闭拼接/锁竞争/生日悖论在 07/05/08/03/12 等义或原文可查。
5. **观察项（非阻断）**：12-complexity.md 为 CRLF 行尾（内容与旧版逐字一致），建议下轮统一 LF。

**v3.5.0 可作为 v3.4.1 的净改进保留，可发版。**

## 八、产物清单

- `rubric.md` — 9 维度评分标准 + 对抗集 T9-T14 判分锚点
- `test-prompts.md` — 14 条 prompt（8 回归沿用上轮原文 + 6 对抗直击本轮根因）
- `snapshots/v3.4.1/`、`snapshots/v3.5.0/` — 两版真快照
- `snapshots/version{1,2,A,B}/` — 标签打乱副本（仲裁 diff -r 核实与真快照字节级一致）
- `blind-A.md`、`blind-B.md` — 双盲评报告（B 的标签缺陷见 §六）
- `arbitration.md` — 仲裁报告（证据核实 / 标签复核 / T11 裁决 / 查漏 / 棘轮）
- `real-run/` — 实跑项目存档（pom.xml + 4 测试类 + User/UserVO/UserMapper + TinyLog8，可复现 43 项）

## 九、复现指引

```bash
# 1. 实跑：cd real-run && mvn test（JDK 21；42 项断言）
#    JDK 8 日志组合：javac --release 8 + java -cp 三 jar 运行 TinyLog8
# 2. 盲评：拿 rubric.md + test-prompts.md + version1/2（A）与 versionA/B（B），独立打分
# 3. 仲裁：读两份盲评 + v3.4.1/v3.5.0 真快照，独立 grep 核实证据、查漏、棘轮判定
```
