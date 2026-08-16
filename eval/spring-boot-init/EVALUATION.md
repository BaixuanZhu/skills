# spring-boot-init 全面评估报告

> 评估方法：Darwin Skill 8 维度 rubric（结构维度 1-7 静态分析 + 维度 8 实测）
> 评分独立性：结构维度与效果维度均由独立子 agent 打分，脚本验证由主 agent 实跑
> 日期：2026-08-16 · 技能版本 1.4.0

## 结论

**总分 80.7 / 100**（结构维度 60 分制实际得 46.2，效果维度 40 分制实际得 34.5，均折算回百分制 80.7）。

技能定位清晰、工作流可机械执行、检查点设计到位，实测生成物能通过 Maven 构建。**核心缺陷是 `--single` 单模块模式残留孤儿 `sample-core/` 目录，且自检三查均无法捕获**——这是本次实测（而非空想）发现的唯一 P1 问题。

## 评分卡

| # | 维度 | 权重 | 得分(1-10) | 加权 | 一句话判据 |
|---|------|-----|-----------|------|-----------|
| 1 | Frontmatter 质量 | 8 | 8 | 64 | description 含做什么+何时用+触发词，但过长且混入不适用/铁律细节 |
| 2 | 工作流清晰度 | 15 | 9 | 135 | 第0步探测 + 生成1-5步有序号，输入输出明确 |
| 3 | 边界条件覆盖 | 10 | 8 | 80 | 不适用表/拒绝已有工程/缺 mvn 跳过覆盖充分，但 single 残留是真实缺口 |
| 4 | 检查点设计 | 7 | 9 | 63 | C1-C4 引导式一轮问询，禁止静默默认，防失控到位 |
| 5 | 指令具体性 | 15 | 9 | 135 | 参数表+命令示例+占位符表+依赖组合表齐备，可直接照做 |
| 6 | 资源整合度 | 5 | 7 | 35 | 引用路径全可达，但 single 未删库模块目录，与文档承诺不一致 |
| 7 | 整体架构 | 15 | 8 | 120 | 结构清晰不冗余，主文件偏长 |
| 8 | 实测表现 | 25 | 7 | 175 | 多模块/版本匹配/让位均强，单模块残留孤儿目录拉低 |
| | **合计** | **100** | | **807** | **80.7** |

## 实测记录（脚本硬验证，非推演）

| 验证项 | 结果 |
|--------|------|
| `init.mjs` 单模块生成（com.acme.order:order-service, Boot 3.5.16/JDK 21, `--single`） | ✅ 占位符零残留 |
| `init.mjs` 多模块生成（com.demo.mall:mall-service, core+app） | ✅ 占位符零残留 |
| `self-check.mjs` 前两查（占位符 / com.example） | ✅ 通过 |
| `mvn validate`（单模块 / 多模块） | ✅ 退出码 0 |
| `mvn -DskipTests compile`（多模块，验证 BOM/依赖坐标） | ✅ 退出码 0，12s |

## 发现的缺陷（P1）

**单模块 `--single` 残留孤儿 `sample-core/` 目录。**

- 现象：`init.mjs --single` 后，根 pom `<modules>` 正确只留 app 子模块、dependencyManagement 与 app 依赖三处引用也正确删除，但物理目录 `sample-core/` 及其 `pom.xml`（artifactId 仍为 `sample-core`）**未被删除**。
- 根因：`scripts/init.mjs` 第 94 行 `writeFileSync(corePom, core)` 无条件写回 sample-core/pom.xml；第 97 行 `if (!opt.single)` 只保护了「重命名」，没有「删除目录」分支。
- 危害：生成物与「单模块 = 只保留一个 app 子模块」的承诺自相矛盾；用户会看到多出来的脏目录，误导后续加模块操作。
- 漏检：`self-check.mjs` 三查（`{{}}` 残留 / `com.example` 残留 / `mvn validate`）均不覆盖「孤儿模块目录」，故自检通过但交付脏。

## 短板清单（按优先级）

1. **P1 脚本 bug**：`--single` 未删 `sample-core` 目录（见上）。修复只需在 single 分支补 `rmSync(join(target,'sample-core'), {recursive:true})` 并跳过写 corePom。
2. **Frontmatter description 冗长**：把「不适用场景 + 核心铁律」整段塞进 description，触发词与边界信息未分层，贴近 1024 字符上限。建议 description 只留「做什么+何时用+触发词」，细节下沉正文。
3. **依赖真实性无脚本校验**：强约束 #6「表外依赖先查 Maven Central」纯靠 agent 自觉，`self-check` 无脚本级校验。属 P2，可接受（有 `mvn compile` 兜底）。

## 建议下一步

评估仅定位问题，未改动技能。若进入优化（Darwin Phase 2），建议先修 P1 脚本 bug（一处改动、可立即复测回滚），再考虑 description 精简。

---

*附：测试 prompt 见同目录 `test-prompts.json`；本评估未修改 `skills/spring-boot-init/` 任何文件。*
