# 仲裁报告：java-coding-guide-pro v3.3.0 → v3.4.0

> **仲裁 agent**：读 A/B 两份盲评报告 + 真版本快照，独立实测核实证据真实性 + 独立查漏 + 棘轮判定。
> **日期**：2026-08-04
> **结论**：✅ **PASS** —— 回归集 0 退步，对抗集 3 条全部达预期，A/B 方向完全一致，无阻断性新引入问题。

## 一、标签解盲

- **Agent A**：version1 = v3.3.0，version2 = v3.4.0
- **Agent B**：versionA = v3.4.0，versionB = v3.3.0（标签反转）
- 两 agent 标签独立、方向反转，均判定"新版（v3.4.0）全面优于旧版（v3.3.0）"——方向一致，无标签污染。

## 二、证据真实性核实（独立 diff + 读源文件）

仲裁独立跑 grep + 读 v3.3.0/v3.4.0 快照源文件，核实 A/B 引用的关键证据：

### ✅ 全部精确命中

| 证据 | A/B 主张 | 仲裁核实结果 |
|------|----------|-------------|
| v3.3.0 悬空引用 5 处 | A(version1): 04 L96/L129, 06 L98, 07 L102, 08 L254 指向「必选依赖」/「依赖坐标」 | ✅ 5 处全部精确命中（grep v3.3.0 实证） |
| v3.4.0 修复 5 处 | A(version2): 同 5 处改指「C-CHECK 询问（仅高风险能力缺失时触发）」 | ✅ 5 处全部修复（grep v3.4.0 实证） |
| SKILL.md 真实节标题 | A: L128「C-CHECK 询问（仅高风险能力缺失时触发）」；**无**「必选依赖」「依赖坐标」 | ✅ v3.3.0 SKILL.md 9 个 ## 节标题，确认无这两个 |
| `CollUtil.partition` bug | B(versionB): v3.3.0 02 L15/L39/L180/L196 + SKILL.md L110 用 CollUtil.partition | ✅ 5 处全部命中（v3.3.0 grep） |
| `ListUtil.partition` fix | B(versionA): v3.4.0 统一改 ListUtil.partition + 标注「CollUtil.partition 不存在」 | ✅ v3.4.0 grep 实证 |
| ScopedValue 真值源 | A/B: v3.4.0/05 L164-191 完整（基本用法+嵌套+对比表） | ✅ 完整保留，未被误删 |
| ScopedValue 09 去重 | A: v3.4.0/09 antipattern 4 精简为单行 + 指针 | ✅ L89-99 精简版 + 指针「见 05」 |
| 「强约束提醒」节删除 | A/B: v3.4.0 全部 12 reference 删 | ✅ grep `## 强约束提醒` 在 v3.4.0 为 0 |

**0 条虚构，0 条方向性偏差。** A/B 两份报告引用的行号证据全部经独立核实成立。

## 三、A/B 方向一致性

两份报告在所有 11 条 prompt 的方向判断上**完全一致**：

| | Agent A 差值 (v2-v1) | Agent B 差值 (A-B) | 一致性 |
|---|---:|---:|---|
| T1 | +2 | +3 | ✅ 新版优 |
| T2 | +11 | +27 | ✅ 新版优（B 扣 v3.3.0 更狠：把 CollUtil.partition 当功能性 bug） |
| T3 | +2 | +3 | ✅ 新版优 |
| T4 | +12 | +14 | ✅ 新版优 |
| T5 | +2 | +3 | ✅ 新版优 |
| T6 | +3 | +3 | ✅ 新版优 |
| T7 | +9 | +12 | ✅ 新版优 |
| T8 | +9 | +14 | ✅ 新版优 |
| T9（对抗·悬空引用） | +26 | +40 | ✅ 新版优（差距最大） |
| T10（对抗·删强约束） | +3 | +4 | ✅ 新版优 |
| T11（对抗·跨文件去重） | +6 | +6 | ✅ 新版优 |
| **合计** | **+96** | **+130** | ✅ 一致 |

> 绝对分差异（B 总差值 +130 > A 总差值 +96）源于 B 的评分尺度更两极化（对功能性 bug 扣分更狠，如 T2 扣 v3.3.0 到 69、T9 扣到 56；A 更保守，T2 扣到 85、T9 扣到 69）。这是评分尺度差，不影响方向判定——两版被同等方向评价，**方向一致**才是关键。

## 四、仲裁独立查漏

仲裁额外核实 A/B 是否共同漏报：

### 判据保留完整性（删「强约束提醒」节是否误删独有判据）

| v3.3.0「强约束提醒」独有判据 | v3.4.0 是否保留 | 仲裁判定 |
|---|---|---|
| 02 `CollUtil.shuffle 不存在 → Collections.shuffle` | ✅ 并入 antipattern 2 末尾 L60 | 保留 |
| 02 `CollUtil.groupBy 不存在` | ✅ antipattern 2 L52 | 保留（非独有） |
| 06 `不引 commons-lang3 ToStringBuilder/Validate` | ✅ 并入速查表 L21 | 保留 |
| 10 `Math.abs(MIN_VALUE) 仍为负`（S2133） | ✅ antipattern 8 L90-103（两版都有） | 保留（非独有，antipattern 是真值源） |
| 10 `byte & 0xFF`（S3037） | ✅ antipattern 9 L105-114 | 保留（非独有） |
| 05 `CompletableFuture 禁用 commonPool` | ✅ L134-148 CompletableFuture 节 | 保留（非独有） |

**结论：0 条独有判据丢失。** 所有「强约束提醒」的内容要么是 antipattern/速查表的复述（删之无碍），要么是独有判据（已全部并入对应 antipattern 或速查表）。

### 潜在漏报核查

仲裁独立检查了 A/B 是否漏报以下：
1. **SKILL.md S/A 表 why 列精简**（本次改动之一）：A/B 均未直接评 T1-T8 的 SKILL.md 表格 why 列变化（因回归集 prompt 不专门测表格列）。仲裁抽查：v3.4.0 SKILL.md L106/L107/L108/L110/L111/L114/L115/L116/L117/L121/L122/L123/L126 的 why 列改为「—」，但携带技术判据的行（L100 无界 OOM、L109 顺序相反、L112 生日悖论等）保留。无关键判据丢失。
2. **`> 为什么`/`> 铁律` 精简**（11/08/09）：A 在 T8 扣 v3.3.0 D6 时提及「三重冗余（铁律 blockquote + 强约束提醒节 + 速查表）」，B 也独立命中。无漏报。
3. **09 的两处 `> 铁律` 精简**：A/B 均在 T11 评到 09 变化，无漏报。

**无共同漏报。**

## 五、棘轮判定

### ✅ PASS

**理由**：

1. **回归集 T1-T8 无任何退步**（核心要求满足）：两 agent 一致判定 v3.4.0 ≥ v3.3.0 全部 8 条。差距来源纯粹是"删冗余节 + 修 CollUtil.partition bug + 修悬空引用"带来的提升，无任何 antipattern 判据丢失（经仲裁独立 grep 核实）。**特别盯的 T2（CollUtil.shuffle 判据）和 T6（Math.abs/byte&0xFF）判据全部保留。**

2. **对抗集 T9/T10/T11 全部达预期**（五类问题根因真被修掉）：
   - **T9（悬空引用）**：v3.3.0 的 5 处指针指向不存在的「必选依赖」/「依赖坐标」节——经仲裁 grep 独立实证，**断链真实存在**；v3.4.0 全部修正为指向真实存在的「C-CHECK 询问」节。两 agent 独立命中（A +26，B +40），仲裁核实，三层确认。
   - **T10（删强约束提醒）**：v3.4.0 删 12 个「强约束提醒」节后，规则仍在速查表 + antipattern 完整覆盖——经仲裁独立 grep 核实，**0 条独有判据丢失**。两 agent 一致判定 v3.4.0 D6 反而提升。
   - **T11（跨文件去重）**：v3.4.0 保留 05 作为 ScopedValue 真值源（完整 API + 对比表 + 嵌套绑定），09 antipattern 4 精简为单行 + 指针——仲裁核实真值源未丢、冗余已去。两 agent 一致（A/B 均 +6）。
   - **额外：CollUtil.partition bug**（实跑测试发现，非原计划五类之一）：v3.3.0 推荐 `CollUtil.partition`（实际不存在，在 `ListUtil`），v3.4.0 已修正。两 agent 均命中（A T2 +11，B T2 +27）——这是达尔文"实跑测试不要空想"原则的直接收益。

3. **新引入问题：0 阻断。** 无功能性退步、无判据丢失、无断链新增。

4. **证据真实性**：A/B 两份报告引用的关键行号证据全部经仲裁独立 grep 核实（0 虚构、0 方向偏差）。两份报告独立得出一致方向结论，可信度高。

**结论**：v3.4.0 相比 v3.3.0 **不存在质量下降**，且成功修复了悬空引用（功能性缺陷）、CollUtil.partition API bug（实跑发现）、删冗余 150 行、去跨文件重复。仲裁无新引入阻断问题。**v3.4.0 可作为 v3.3.0 的净改进保留，可发版。**

## 六、附：实跑代码验证（达尔文强制项，无空想）

v3.4.0 发版前搭最小 Maven 项目（JDK 21 + Hutool 5.8.47 BOM）实跑 37 个高风险代码片段，全部 PASS：
- BigDecimal 精度/compareTo/divide/equals/不可变（12 项）
- DateUtil 线程安全/now(ZoneId)/currentSeconds（3 项）
- ThreadPoolExecutor + CallerRunsPolicy 优雅关闭（1 项）
- SecureUtil.md5/sha256 补零 + BCrypt 自带盐/checkpw + Base64（6 项）
- RandomUtil.randomInt 半开区间 + SecureRandom 验证码（2 项）
- StrUtil.isBlank/ObjectUtil.equal/split + CollUtil.isEmpty + ListUtil.partition + Arrays.asList 固定大小 + BeanUtil（13 项）
- **实跑发现 `CollUtil.partition` 不存在（编译失败）→ 改 `ListUtil.partition`**（这正是达尔文"实跑而非空想"的价值，已在技能内容修复）

ScopedValue（JDK 25）因本地仅 JDK 21 未实跑，标 last_verified=2026-08-04 含此项除外说明。虚拟线程 newVirtualThreadPerTaskExecutor（JDK 21）已实跑通过。
