# spring-boot-init 第二轮评估（R2，修复验证轮）

> 评估方法：达尔文棘轮——R1（`../EVALUATION.md`，80.7 分）定位问题 → 修复 → 主 agent 实跑复测 + 独立子 agent 盲评重打分（盲评不读 eval/、不告知改动内容）
> 日期：2026-08-16 · 技能版本 1.4.1（自 1.4.0 升）

## 结论

**总分 92.2 / 100**（R1 为 80.7，+11.5）。R1 唯一 P1（`--single` 残留孤儿 `sample-core/` 目录）已修复并通过双重独立验证；新增的自检第四查能双向抓住孤儿 / 缺失模块目录。盲评另发现一个**新 P2**（groupId 以 `com.example.` 开头时主类被误删，双检查均静默通过），留作 R3 候选，本轮不扩范围。

## 本轮改动（对应 R1 短板清单）

| R1 短板 | 改动 | 文件 |
|---|---|---|
| P1：`--single` 未删 sample-core 目录 | single 分支跳过写 corePom 并 `rmSync` 整个目录 | `scripts/init.mjs` |
| P1 漏检：自检三查不覆盖孤儿目录 | 增第四查：根 `<modules>` ↔ 一级子目录（含 pom.xml）双向一致 | `scripts/self-check.mjs` |
| P2：description 冗长 | 约 600 字精简至约 330 字，只留做什么 + 何时用 + 触发词 + 让位线索，细节已在正文 | `SKILL.md` |
| — | 「三查」→「四查」、`--single` 口径补「目录」，共 4 处文档同步 | `SKILL.md` + `references/01-template-usage.md` |
| — | 版本 1.4.0 → 1.4.1（未发布过，无静默拒收风险） | `SKILL.md` frontmatter |

R1 短板 #3（依赖真实性无脚本校验）维持原判：P2 可接受，`mvn compile` 兜底，不动作。

## 实跑记录（主 agent 复测，临时目录真实执行）

| 验证项 | 结果 |
|--------|------|
| `init.mjs --single`（com.acme.order:order-service） | ✅ **sample-core 目录不存在**、全部 pom 零 sample-core 引用、exit 0 |
| `init.mjs` 多模块（com.demo.mall:mall-service, --core/--app） | ✅ 目录重命名与 `<modules>` 对齐、`sample-` 字符串零残留 |
| 负向 1：手工造未列目录 `stray-module/`（含 pom.xml） | ✅ self-check 报「孤儿模块目录」exit 1 |
| 负向 2：挪走已列模块目录 `mall-core/` | ✅ self-check 报「目录缺失」exit 1 |
| 还原后 self-check（两项目，含 `--validate`） | ✅ 四查全过 exit 0 |
| `mvn.cmd -DskipTests compile`（单模块 / 多模块） | ✅ 均退出码 0 |

## 独立盲评（子 agent，不知改动内容，自行实跑）

| # | 维度 | 权重 | 得分(1-10) | R1 | 一句话判据 |
|---|------|-----|-----------|----|-----------|
| 1 | Frontmatter 质量 | 8 | 9 | 8 | description 含做什么+何时用+触发词+不适用转介，仅略混实现细节 |
| 2 | 工作流清晰度 | 15 | 9 | 9 | 5 步全序号、输入输出明确、唯一路径机械可执行 |
| 3 | 边界条件覆盖 | 10 | 9 | 8 | 8 条不适用路由 + 兼容表 + 拒绝重跑齐备 |
| 4 | 检查点设计 | 7 | 10 | 9 | C1~C4 一轮问完、默认推荐 + 快捷路径、防静默默认三处强调 |
| 5 | 指令具体性 | 15 | 10 | 9 | 参数表 / 双场景示例 / 占位符表 / 插件两档表 / 依赖组合表全齐 |
| 6 | 资源整合度 | 5 | 9 | 7 | 指针全可达；文档承诺与脚本行为逐项实测一致 |
| 7 | 整体架构 | 15 | 9 | 8 | 主文件 103 行克制；references 指针化不复制 |
| 8 | 实测表现 | 25 | 9 | 7 | 两标准场景生成物全对、validate 通过、4 类边界正确；新 P2 扣分 |
| | **合计** | 100 | **92.2** | 80.7 | |

盲评独立复测同样确认：单模块无孤儿目录、三处引用干净移除、多模块重命名对齐、拒绝已有 pom.xml、`com.example0.dev` 前缀不误伤。

## 新发现缺陷（P2，R3 候选）

**groupId 以 `com.example.` 开头时（如演示 / POC 常见的 `com.example.demo`），生成无主类的工程且两道检查均静默通过。**

- 现象：`--group com.example.demo --single` → init 报「✓ 成功 + 零残留」exit 0，但 `src/main/java/com/` 为空——`Application.java` 不存在；self-check 亦报通过（无文件即无残留可检；且 `com.example.demo` 作为声明 groupId 会被剥离，不触发 com.example 残留查）。
- 根因：`init.mjs` 步骤⑤ 目标包路径 `com/example/demo` 嵌套在模板包 `com/example` 之内，主类挪入后 `rmSync(java/com/example)` 连同刚挪入的主类一并删除。
- 建议修法（R3）：挪包前判断目标包是否位于 `com/example` 之下（先建目标目录树再挪、或对嵌套情形保留新建路径）；self-check 可加第 5 查「可执行模块存在主类」。
- 定级理由：触发条件罕见（正常工程不用 com.example 做 groupId），且 `mvn package`（repackage 找不到主类）终会暴露——但暴露点太晚，值得下轮修。

## 棘轮结论

- ✅ 保留：P1 孤儿目录修复（双路径验证）、self-check 第四查（负向用例双向命中）、description 精简（维度 1 得分 8→9）。
- ⏭ 推迟：`com.example.*` groupId 主类丢失（新 P2，本轮盲评发现）→ R3 首项。
- 维持不动：依赖真实性脚本校验（`mvn compile` 兜底）。

---

*附：测试 prompt 复用 `../test-prompts.json`；本轮改动清单见 git log（fix + refactor 两个 commit）。*
