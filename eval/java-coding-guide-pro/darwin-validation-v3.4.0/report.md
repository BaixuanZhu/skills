# java-coding-guide-pro 达尔文验证报告：v3.3.0 → v3.4.0（回归 + 对抗 + 实跑）

> **目的**：用达尔文「独立盲评 + 独立仲裁 + 棘轮 + 实跑测试」原则，证明 v3.4.0 相比 v3.3.0 **无质量下降**，且五类问题的根本原因被真正修掉。
> **日期**：2026-08-04
> **方法**：最小 Maven 项目实跑 37 片段 + 2 个独立盲评 agent（A/B，标签反转）+ 仲裁 agent + 棘轮。
> **结论**：✅ **PASS** —— 实跑 37/37 通过且发现 1 个真 bug；回归集 0 退步；对抗集 3 条全部达预期；A/B 方向完全一致；仲裁 0 虚构 0 漏报。

## 一、本轮改动概览（v3.3.0 → v3.4.0，2432 → 2303 行，-5.3%）

按 java-unit-test 精简总结出的通用方针 + AGENTS.md 质量标准，处理 5 类问题 + 1 个实跑发现的 bug：

| # | 改动 | 类型 | 量级 |
|---|---|---|---|
| 1 | **修悬空引用**：4 文件 5 处指针从「必选依赖」/「依赖坐标」（不存在的节）→「C-CHECK 询问（仅高风险能力缺失时触发）」 | 功能性缺陷 | 5 行 |
| 2 | **删「强约束提醒」节**：12 个 reference 末尾逐字复述上方速查表的节全部删除（独有判据已并入 antipattern/速查表） | 冗余 #6 | ~150 行 |
| 3 | **精简重述引用块**：11 的 19 处 `> 为什么`（删纯说理，留技术判据）、08 的 6 处 `> 铁律`（同）、09 的 2 处 `> 铁律`（同） | 冗余 #4 | ~50 行 |
| 4 | **去跨文件重复**：ScopedValue 真值源定在 05，09 antipattern 4 精简为单行 + 指针 | 冗余 #6 | ~40 行 |
| 5 | **SKILL.md S/A 表 why 列精简**：纯解释散文 why 列改「—」，携带技术判据的保留 | 冗余 #6 | ~13 单元格 |
| 6 | **修 CollUtil.partition bug**（实跑发现）：`CollUtil.partition` 在 Hutool 5.8.x **不存在**，正确为 `ListUtil.partition`——v3.3.0 4 处误用，v3.4.0 全部修正并加防漂移标注 | 功能性 bug | 5 处 |

## 二、实跑代码验证（达尔文强制项：实跑而非空想）

搭最小 Maven 项目（JDK 21 + Hutool 5.8.47 BOM），实跑 37 个高风险代码片段，**全部 PASS**：

- BigDecimal 精度/compareTo/divide/equals/不可变 + Math.abs(MIN_VALUE) + byte&0xFF（12 项）
- DateUtil 线程安全 + now(ZoneId) + currentSeconds（3 项）
- ThreadPoolExecutor 有界队列 + 命名工厂 + CallerRunsPolicy 优雅关闭（1 项）
- SecureUtil.md5/sha256 补零 + BCrypt 自带盐/checkpw + Base64 往返（6 项）
- RandomUtil.randomInt 半开区间 + SecureRandom 6 位验证码（2 项）
- StrUtil.isBlank/ObjectUtil.equal/split + CollUtil.isEmpty + ListUtil.partition + Arrays.asList 固定大小 + BeanUtil（13 项）

**实跑的最大收益**：编译期发现 `CollUtil.partition(list, size)` 在 Hutool 5.8.x **不存在**（javap 确认 `partition` 在 `ListUtil` 不在 `CollUtil`）→ 技能内容 4 处误用全部修正为 `ListUtil.partition` + 防漂移标注「CollUtil.partition 不存在」。这正是 AGENTS.md「实跑测试——不要空想」原则的直接价值——空想不会发现这个 API 归属错误。

> ScopedValue（JDK 25）因本地仅 JDK 21 未实跑，last_verified=2026-08-04 含此项除外。虚拟线程 newVirtualThreadPerTaskExecutor（JDK 21）已实跑通过。

## 三、三层独立验证

| 层 | agent | 角色 | 独立性 |
|----|-------|------|--------|
| 1 | Agent A | 双盲打分（version1=v3.3.0, version2=v3.4.0） | 完全独立，不知 B 存在 |
| 2 | Agent B | 双盲打分（versionA=v3.4.0, versionB=v3.3.0，标签反转） | 完全独立，不知 A 存在 |
| 3 | 仲裁 agent | 复核 A/B 证据真实性 + 独立查漏 + 棘轮判定 | 读 A/B 报告，但独立 grep 实测核实 |

## 四、盲评结果（两份独立报告的核心数据）

### 总分对比（两 agent 一致判定 v3.4.0 优于 v3.3.0）

| | Agent A | Agent B | 一致性 |
|---|---|---|---|
| v3.3.0 | 968/1100（87.9 均） | 910/1100（82.7 均） | B 比 A 严约 5 分/版（评分别倾向） |
| v3.4.0 | 1064/1100（96.7 均） | 1040/1100（94.5 均） | 同上 |
| **差值（v3.4.0−v3.3.0）** | **+96** | **+130** | ✅ 一致（B 扣 v3.3.0 功能性 bug 更狠） |

> 绝对分差异（B 比 A 严）是评分尺度差，不是方向分歧。两版被同等方向评价，**差值**才是关键——两份报告方向完全一致（11 条全正）。

### 单 prompt 差值（两 agent 独立打分）

| Prompt | 场景 | A 差值 | B 差值 | 共识 |
|---|---|---:|---:|---|
| T1 判空+Optional | +2 | +3 | ✅ v3.4.0 优（删冗余节 D6 升） |
| **T2 集合分块（回归重点）** | **+11** | **+27** | ✅ v3.4.0 优（修 CollUtil.partition bug，B 扣更狠） |
| T3 日期+now | +2 | +3 | ✅ v3.4.0 优（删冗余） |
| T4 文件+HTTP+JSON | +12 | +14 | ✅ v3.4.0 优（修悬空引用） |
| T5 线程池+异步 | +2 | +3 | ✅ v3.4.0 优（删冗余） |
| **T6 BigDecimal（回归重点）** | +3 | +3 | ✅ 完全一致（删冗余，判据 0 丢失） |
| T7 加密+密码 | +9 | +12 | ✅ v3.4.0 优（修悬空引用） |
| T8 异常+日志+随机 | +9 | +14 | ✅ v3.4.0 优（修悬空引用 + 删铁律重述） |
| **T9 对抗·悬空引用** | **+26** | **+40** | ✅ v3.4.0 优（断链全修，差距最大） |
| **T10 对抗·删强约束提醒** | **+3** | **+4** | ✅ v3.4.0 优（判据 0 丢失，D6 升） |
| **T11 对抗·跨文件去重** | **+6** | **+6** | ✅ 完全一致（真值源保留 + 09 去重） |

## 五、对抗集核心证据（两 agent 独立命中 + 仲裁核实）

### T9（悬空引用——MapStruct/OkHttp/Jackson/SLF4J 坐标走断链）

| 版本 | 坐标指针原文 | agent 行为 | 判定 |
|---|---|---|---|
| v3.3.0 | 04 L96/L129, 06 L98, 07 L102, 08 L254 指向 `SKILL.md「必选依赖」/「依赖坐标」` | SKILL.md **无此两节**（9 个 ## 节，grep 实证）→ agent 跟指针走断链，找不到坐标 | ❌ 功能性缺陷 |
| v3.4.0 | 同 5 处改为 `SKILL.md「C-CHECK 询问（仅高风险能力缺失时触发）」` | 该节**真实存在**（SKILL.md L128），blockquote L141 含全部坐标 → agent 一跳到位 | ✅ 正确修复 |

### T10（删强约束提醒后判据是否丢失）

| 判据 | v3.3.0 位置 | v3.4.0 去向 | 仲裁核实 |
|---|---|---|---|
| `CollUtil.shuffle 不存在` | 02 强约束提醒 L198 | 并入 02 antipattern 2 末尾 L60 | ✅ 保留 |
| `commons-lang3 Validate 不引` | 06 强约束提醒 L127 | 并入 06 速查表 L21 | ✅ 保留 |
| `Math.abs(MIN_VALUE)` | 10 强约束提醒 L161 | antipattern 8 L90-103（真值源） | ✅ 保留（非独有） |
| `byte & 0xFF` | 10 强约束提醒 L162 | antipattern 9 L105-114 | ✅ 保留（非独有） |

**0 条独有判据丢失**——删的 150 行全是速查表/antipattern 的逐字复述。

### T11（ScopedValue 跨文件去重）

| 版本 | ScopedValue 真值源 | 09 antipattern 4 | 判定 |
|---|---|---|---|
| v3.3.0 | 05 L164-191 完整 | 09 antipattern 4 **重复贴完整代码** + 推荐示例又贴一遍（四处重复） | ⚠️ D6 冗余 |
| v3.4.0 | 05 L164-191 **完整保留**（未误删） | 09 antipattern 4 精简为单行 + 指针「详见 05」 | ✅ 真值源保留 + 冗余去除 |

## 六、额外发现：CollUtil.partition API bug（实跑 + 盲评双重确认）

这是本次达尔文验证的最大净收益——**实跑测试发现的功能性 bug**，不在原计划五类问题之内：

| 版本 | 分块推荐 API | 实跑/javap 验证 | 判定 |
|---|---|---|---|
| v3.3.0 | `CollUtil.partition(list, size)`（SKILL.md L110 + 02 L15/L39/L180/L196 共 5 处） | javap 确认 `CollUtil` **无 partition 方法**，在 `ListUtil`（`cn.hutool.core.collection.ListUtil`） | ❌ agent 照写编译失败 |
| v3.4.0 | `ListUtil.partition` + 标注「CollUtil.partition 不存在」 | 实跑编译通过，`ListUtil.partition(nums, 2)` 返回 3 组 | ✅ 正确 |

两盲评 agent 均独立命中（A T2 +11，B T2 +27）+ 仲裁 javap 核实——三层确认。**这正是 AGENTS.md「实跑测试——不要空想」原则的直接价值**：不实跑，这个 API 归属错误永远不会被发现。

## 七、仲裁结论：PASS

### 证据真实性：全部核实
仲裁独立 grep v3.3.0/v3.4.0 源文件，核实 A/B 引用的全部关键证据——**0 条虚构、0 条方向偏差**。

### A/B 方向一致性：11 条全正
两份报告在所有 11 条 prompt 的方向判断上**完全一致**（v3.4.0 全面优于 v3.3.0）。绝对分差异（B 比 A 严）属评分尺度差，不影响判定。

### 仲裁独立查漏：0 共同漏报
仲裁额外核实"删强约束提醒节是否误删独有判据"——经独立 grep，所有独有判据已全部并入对应 antipattern 或速查表，**0 条丢失**。

### 棘轮判定：✅ PASS
1. 回归集 T1-T8 无任何退步（两 agent 一致，仲裁核实判据 0 丢失）。
2. 对抗集 T9/T10/T11 全部达预期（悬空引用全修、判据 0 丢失、真值源保留 + 去重）。
3. 额外：CollUtil.partition bug 经实跑发现并修复。
4. 新引入阻断问题：0。

**v3.4.0 可作为 v3.3.0 的净改进保留，可发版。**

## 八、产物清单

- `rubric.md` — 9 维度评分标准 + 对抗集 T9/T10/T11 判分锚点
- `test-prompts.md` — 11 条 test-prompt（8 回归 + 3 对抗）
- `snapshots/v3.3.0/`、`snapshots/v3.4.0/` — 两版隔离快照（v3.4.0 含 CollUtil.partition 修复）
- `snapshots/version{1,2,A,B}/` — 标签打乱副本（供盲评）
- `blind-A.md` — Agent A 盲评（version1=v3.3.0, version2=v3.4.0）
- `blind-B.md` — Agent B 盲评（versionA=v3.4.0, versionB=v3.3.0，标签反转）
- `arbitration.md` — 仲裁报告（证据核实 + 查漏 + 棘轮判定）
- `report.md` — 本报告

## 九、复现指引

```bash
# 1. 两版快照已就绪（snapshots/v3.3.0、snapshots/v3.4.0）
# 2. 盲评 agent 拿 rubric.md + test-prompts.md + 两份打乱标签快照（version1/2、versionA/B）
# 3. 仲裁 agent 拿两份盲评 + 真版本快照，独立 grep 实测核实
# 4. 实跑验证：最小 Maven 项目（JDK 21 + Hutool 5.8.47 BOM）跑高风险片段
# 5. 棘轮判定：回归集 8 条是否无退步 + 对抗集 3 条是否达预期 + 新引入问题是否阻断
```
