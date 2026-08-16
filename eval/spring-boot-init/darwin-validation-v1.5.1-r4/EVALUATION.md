# spring-boot-init 发版前评估（R4，发布验收轮）

> 目标（用户定）：发版前全面 rubric 评测——只报实质问题，小问题不报。
> 方法：独立子 agent 盲评（不读 eval/、不知历史改动）+ 主 agent 独立实跑（单/多模块、负向矩阵、mvn package 冒烟）双轨。
> 日期：2026-08-16 · 技能版本 1.5.1（自 1.5.0 升，改动为 C1 问询补工程坐标 + 强约束与 reference ✗/✓ 表去重指针化）

## 结论

- **独立盲评 90.5 / 100**（8 维度 9~10 分，唯一观察项为「JDK↔Boot 匹配依赖 C2 问询把关」——属明确设计，非缺陷）。
- **主 agent 实跑全过**：单/多模块生成结构全对、self-check 六查三场景通过、负向输入 4 类全拒、`com.example.demo` 边界保持、`mvn package` 产出 fat jar。
- **实质问题：无 P0 / P1。发版建议：可发。**

> 分数口径：R3 的 87.5 为另一评审员、更深探测边界的记录，与本轮不可直接比；本轮 1.5.1 已处理 R3 维度 7 扣分项（跨文件去重）。

## 独立盲评（rubric，子 agent 自行实跑、不读 eval/）

| # | 维度 | 权重 | 得分 | 一句话判据 |
|---|------|-----|------|-----------|
| 1 | Frontmatter 质量 | 8 | 9 | 做什么 + 何时用 + 触发词 + 不适用转接齐全，<1024 字符 |
| 2 | 工作流清晰度 | 15 | 9 | 5 步有序号、输入输出明确、C1~C4 问询表 + 示例话术 |
| 3 | 边界条件覆盖 | 10 | 9 | 脚本拒 10+ 类非法输入，残留终检 + 自检六查，无 mvn 时优雅降级 |
| 4 | 检查点设计 | 7 | 9 | 四检查点强制问询、禁静默默认、不适用时指引切换技能 |
| 5 | 指令具体性 | 15 | 9 | 参数表 / 占位符表 / 插件清单 / 依赖组合表 / XML 写法示例均可直接执行 |
| 6 | 资源整合度 | 5 | 10 | SKILL ↔ references ↔ scripts ↔ assets 交叉引用全对，路径实测可达 |
| 7 | 整体架构 | 15 | 9 | 主文件克制、references 分层、单/多模块一套模板不分叉 |
| 8 | 实测表现 | 25 | 9 | 两场景全通、6 类非法输入全拒、结构断言全部命中 |
| | **合计** | 100 | **90.5** | 无 P0/P1 |

## 主 agent 实跑证据（独立于盲评，临时目录真实执行）

| 验证项 | 结果 |
|--------|------|
| 单模块 `com.acme.order:order-service --single` | ✅ 根 pom packaging=pom + 仅 1 个 app 子模块；主类 package 行 = 目录；`mvn package` 产出 fat jar（exit 0） |
| 多模块 `com.demo.mall:mall-service --core mall-core --app mall-api` | ✅ `<modules>` 列全；repackage 只在 api 模块（core 0 处 / api 1 处） |
| self-check 六查（单/多/com.example.demo 三场景） | ✅ 全部 exit 0（含 `mvn validate` 真实通过） |
| `com.example.demo` groupId（R3 曾修 P1） | ✅ 主类保留在 `com/example/demo/`，剥离不误报 |
| 负向输入：保留字包段 `class` / `--single`+`--core` 互斥 / 未知参数 / 非空目录 | ✅ 全部 exit 2 + 原因，零目录残留 |
| `--artifact sample-app --single` | ✅ 合法生成 `sample-app-app`（派生名不撞保留名，行为与文档一致） |

## 实质问题清单

无。小问题按用户要求不报。

## 发版判定

- ✅ R3 全部改进保持有效（结构零逃逸、自检全拦截、com.example 修复、替换顺序根因换位）。
- ✅ 1.5.1 的 C1 工程坐标必问 + 跨文件去重未见回归。
- **达到发版标准。发布需用户确认后走 PUBLISH.local.md 流程。**

---

*附：测试 prompt 复用 `../test-prompts.json`；盲评 agent 与主 agent 独立，均不读 eval/ 目录。*
