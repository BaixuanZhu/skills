# spring-boot-init 第三轮评估（R3，结构零逃逸冲刺轮）

> 目标（用户定）：**静态错误清零才能上线——产出的项目结构必须是对的。**
> 方法：R2 遗留 P2（com.example.* groupId 主类丢失）修复 → rubric 盲评 → 5 轮独立对抗测试（每轮换新子 agent、不告知改动）→ 逃逸逐条修复复测 → 棘轮
> 日期：2026-08-16 · 技能版本 1.5.0（自 1.4.1 升）

## 结论

- **init 生成侧：5 轮对抗测试、累计 60+ 攻击、零逃逸**——合法输入全部产出结构正确的工程（四向一致：modules ↔ 目录 ↔ GAV ↔ 打印坐标；主类 package 行 = 目录；mvn validate / package 实测通过），非法 / 冲突 / 未知输入全部 exit 2 + 原因，不存在「exit 0 却产出坏结构」的路径。**上线标准（产出结构正确）达成。**
- **self-check：规格内 26 类篡改全拦截、基线零误报**，另修复 4 个超纲伪造（未闭合块注释、reporting 节、全限定签名误报）。
- rubric 盲评 87.5 / 100（与 R2 的 92.2 不可直接比：不同评审员、本轮探测边界深得多；两个 P2 均已在本轮修复）。

## 本轮改动（skills/spring-boot-init/，v1.4.1 → v1.5.0）

| # | 改动 | 动因（发现轮） |
|---|---|---|
| 1 | 挪包改「暂存主类 → 清整个模板包壳 `com/` → 落位」：groupId 为 `com.example.*` / 精确 `com.example` 时主类不再被误删 | R2 遗留 P1 级 |
| 2 | init 终检新增：主类存在断言 + **顶层目录恰为模块集**断言 | R2 / 对抗轮 |
| 3 | 输入防线：groupId 合法包名（正则 + **Java 保留字包段黑名单** + 每段 ≤64 / 总长 ≤200）；artifact / 模块名（路径安全、非尾点、非同名、非仅大小写不同、不撞 sample-core/sample-app（含大小写变体）/ pom.xml / target / 根 artifactId）；--boot/--jdk/--version 格式；--single 与 --core 互斥；**严格参数解析**（未知参数 / 缺值 / 多余位置参数 / `=` 语法支持） | 盲评 + 对抗轮 1/3/4 |
| 4 | **替换顺序换位：token 改写（shape，函数替换不回扫）先于占位符展开（ph）**——用户值（artifact 含 sample-app 子串等）写入后永不再被回扫，整类坐标腐蚀消失 | 对抗轮 3（根因修复） |
| 5 | 目标目录须为空（隐藏条目如 .git 不影响）——对齐「空目录全新初始化」承诺，消灭合并语义不一致 | 对抗轮 3 |
| 6 | self-check 三查 → **六查**：③模块目录 ↔ `<modules>`（剥 XML 注释后提取）；④可执行模块存在且含主类（激活判定剥注释 / pluginManagement / profiles / properties / reporting，须真实 `<plugin>` 声明序列；主类检测解码 \uXXXX → 剥闭合注释 / 文本块 / 字符串 / **未闭合注释尾巴**后按签名匹配，兼容全限定 `java.lang.String[]`）；⑤package 声明 ↔ 目录路径（走同一降噪链）；⑥mvn validate | 对抗轮 1/2/4/5 |
| 7 | 残留扫描：com.example 剥离改为**仅当 groupId 自身包含 com.example**（剥离只移除 groupId 精确出现，短 groupId 如 com 不再遮蔽真残留）；扫描点文件（.gitignore 等），点目录跳过收敛为 .git/.idea/.vscode；src 树内名为 target 的包段不误跳 | 对抗轮 1/2/5 |
| 8 | 文档口径同步（SKILL.md 六查 ×2、reference 参数表 / 内部步骤 / 拒绝清单） | — |

R2 遗留第 3 项（依赖真实性脚本校验）维持不动作。

## 实测证据（主 agent，全部临时目录真实执行）

| 验证项 | 结果 |
|--------|------|
| `com.example.demo --single`：主类落 `com/example/demo/`、package 行正确 | ✅（R2 坏例修复）+ `mvn package` 产出 fat jar |
| `com.example`（精确）`--single` | ✅ 结构正确 + validate 通过 |
| 黄金 8 场景（常规单/多、com.example 各形态、com.target.x、artifact=sample-app、--app pom）六查 + `--validate` | ✅ 8/8 PASS |
| 负向输入矩阵（保留字 / 空段 / 数字段 / 连字符 / 超长 / 尾点 / 同名 / 大小写撞名 / 模板名变体 / pom.xml / target / 根 artifactId 同名 / --single+--core / 版本畸形 / 未知参数 / 缺值 / 目标为文件 / 非空 / 已有 pom） | ✅ 全部 exit 2 + 原因，零目录残留 |
| 对抗复测（每轮逃逸逐条回归）：E1–E9、F1–F5、G1–G5、H1–H6、X1/X2/X4/误报 | ✅ 全部命中预期（拦截或正确生成） |
| 篡改套件：删主类 / 删插件 / pluginManagement / profile / properties / reporting 降级 / 删根 pom / 注释 module 行 / 孤儿目录 / 改 package 行（含 5 种伪造掩护）/ 假 main（含 5 种伪造）/ 残留植点文件与点目录 | ✅ 全部 exit 1 |

## 独立盲评（rubric，子 agent 不知改动、自行实跑）

| # | 维度 | 权重 | 得分 | 一句话判据 |
|---|------|-----|------|-----------|
| 1 | Frontmatter 质量 | 8 | 9 | 字段齐全，description 结构清晰，仅略夹实现细节 |
| 2 | 工作流清晰度 | 15 | 9 | 0~5 步编号、输入输出明确、唯一路径可机械执行 |
| 3 | 边界条件覆盖 | 10 | 8 | 不适用路由 + 脚本级拒绝矩阵覆盖充分（保留字 / 设备名为其扣分点，本轮已修保留字） |
| 4 | 检查点设计 | 7 | 9 | C1~C4 一轮问完 + 默认推荐 + 防静默默认 |
| 5 | 指令具体性 | 15 | 9 | 参数表 / 示例 / 占位符表 / 依赖组合表齐备 |
| 6 | 资源整合度 | 5 | 9 | 指针全可达，文档承诺与脚本行为实测一致 |
| 7 | 整体架构 | 15 | 8 | 主文件克制；SKILL.md 硬约束与 reference ✗/✓ 表有跨文件重复（留给内容打磨轮） |
| 8 | 实测表现 | 25 | 9 | 标准 + 5 组边界 groupId + 7 类非法输入全按文档行为，注损验证自检能抓缺陷 |
| | **合计** | 100 | **87.5** | |

## 对抗测试时间线（5 轮，每轮独立新 agent）

| 轮 | 发现 | 处置 |
|----|------|------|
| 1 | core/app 同名崩溃留残骸；尾点模块名 Win32 假成功；self-check 根 pom 缺失 / package↔目录 / 剥离遮蔽 / 删插件绕过盲区 | 全修 + 复测 ✅ |
| 2 | `--core` 含 sample-app 子串二次改写（确定性逃逸）；注释伪造主类；com.target 假阳性 | 单遍函数替换（根因）+ 签名匹配 + src 树感知，全修 ✅ |
| 3 | `--app pom.xml` 顶替根 pom；artifact 含模板子串坐标腐蚀（替换顺序根因）；文本块伪造；大小写变体崩溃 | **shape 先于 ph 换位（根因）** + 黑名单 + 文本块剥离，全修 ✅ |
| 4 | 模块名 target；与根 artifactId 同名（reactor 重复）；--single=true 吞参；unicode 转义注释伪造；pluginManagement 骗激活；点文件残留逃检 | 全修 + 严格参数解析 ✅ |
| 5 | **init 侧 60+ 攻击零逃逸（生成侧收官）**；self-check 规格内 26/26 拦截；超纲 3 逃逸（未闭合注释 ×2、reporting 节）+ 1 误报（全限定签名） | 超纲 4 项亦全修 + 复测 ✅；聚焦终判「可上线」 |

## 设计权衡残留（记录不修，均非「产出结构错误」类）

1. **篡改根 pom groupId 为 com.example\* 可遮蔽 com.example 残留查**：与「合法支持 com.example 作 groupId」不可区分（无第二真相源）；init 生成侧无此问题（剥离基准来自命令行参数）。
2. **旧版 Windows 设备名**（模块名 / 包段叫 con、nul 等）：Win11 实测可建可构建；老系统工具链有风险，不设防。
3. **非 pom 杂散目录**（如 stray/note.txt）self-check 不报：Maven 不可见、可能是用户有意添加；init 生成时刻由「顶层目录恰为模块集」断言兜住。
4. **src 树外 target/ 跳过**：构建产物，设计如此。
5. **保守误拒**：`--artifact sample --single` 因派生 app 名撞 sample-app 被拒（安全方向）；`--app=` 空值静默用默认名（产物仍正确）。
6. SKILL.md 硬约束与 reference ✗/✓ 表跨文件重复（维度 7 扣分项）：内容打磨项，不影响产出，留下轮。

## 棘轮结论

- ✅ 保留：R2 全部改进 + 本轮 8 项（含 2 个根因级修复：挪包暂存落位、替换顺序换位）。
- ⏭ 推迟：跨文件文档去重（维度 7）→ 内容打磨轮。
- **上线判定：生成侧结构零逃逸 + 自检篡改全拦截，达到「静态错误清零」标准。发布需用户确认后走 PUBLISH.local.md 流程。**

---

*附：测试 prompt 复用 `../test-prompts.json`；本轮全部对抗 agent 与盲评 agent 相互独立、均不读 eval/ 目录。*
