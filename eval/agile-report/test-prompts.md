# 7 条 test-prompt（达尔文评估输入）

> 这些 prompt 模拟真实用户场景。盲评 agent 假设自己是"接到这个用户请求的 coding agent，手里只有 agile-report 技能 + fixture 数据"，判断能否产出合格报告。
>
> fixture 根目录：`eval/agile-report/fixtures/project-root/`（含 agile-docs/ + sprints/，模拟 3 个已关闭 Sprint）
> 正确答案见 `fixtures/ground-truth.md`（盲评 agent 不读，仅供主 agent/仲裁核对）。

## T1 — 完整态：生成阶段报告（核心路径）

```
我刚关闭了最近 3 个 Sprint（001/002/003），下周一要给甲方做阶段汇报。
项目数据都在 agile-docs/ 和 sprints/ 下，帮我生成一份图表化的阶段进度报告，
要能转成 PDF 带过去。项目根目录：eval/agile-report/fixtures/project-root/
```

**验证点**：
- 能否正确判定状态①（完整态）
- 数据聚合：阶段整体完成率 85.7%（黄）、3 个 Sprint 完成率 100%/80%/75%、承诺 59 点 vs 完成 43 点
- 术语去技术化：报告里不出现"故事点/Sprint/Must"，改用"任务量/迭代周期/核心需求"
- HTML→PDF：能否给出正确的 Playwright pdf 命令（含 --browser chromium + --wait-for-timeout 2000）

## T2 — 工具链陷阱：HTML→PDF 命令准确性（对抗）

```
我已经用 ECharts 生成好报告的 HTML 了（reports/stage-report-20260804.html），
现在要转成 PDF。你直接告诉我用什么命令，我环境是 Windows + Node。
```

**验证点**（直击 toolchain.md 的核心陷阱知识）：
- 命令是否准确：`npx playwright pdf --browser chromium --wait-for-timeout 2000 --paper-format A4 ...`
- 是否点明 `--wait-for-timeout` 是**毫秒**（不是秒）——写 `2` 会图表空白
- 是否点明 PDF **只有 Chromium 支持**（不能 firefox/webkit）
- 是否区分 `playwright` ≠ `@playwright/cli`（Agent CLI 不能直接 pdf）
- 是否提示 `npm install -D playwright` 后**还要** `npx playwright install chromium`（两步）

## T3 — 降级态：无敏捷产物（对抗）

```
我有个老项目，没用过你们那套敏捷文档（没有 agile-docs/ 也没有 sprints/），
但是有 git 历史。下周要给领导汇报最近 2 个月的进度，能帮我出个报告吗？
```

**验证点**（状态③全降级）：
- 能否判定降级到 git log 模式（不拒绝产出）
- 是否用 git log 解析（按日期范围、commit message 分类：feat/fix/refactor）
- 报告封面是否标注"数据来源：git log（简化版）"
- 是否说明降级报告无完成率%（改为提交趋势）

## T4 — 数据聚合准确性：阻塞项识别

```
基于 fixtures/project-root/ 的数据，我想重点看看这阶段哪些任务卡住了。
哪些任务反复没完成？给我列出来。
```

**验证点**（直击 report-rules.md §2.4 三态 + 阻塞表）：
- 能否识别 T-003 在 Sprint 002 + 003 都出现在 moved_next（2 次）
- 是否列入阻塞项表并给出移出次数 + 原因
- 是否用**表格**（非图表）呈现——chart-config.md §一 明确移出任务用表格

## T5 — 范围边界：按需衍生定位

```
我们刚用 using-agile 初始化了敏捷文档，接下来是不是每个 Sprint 关闭后都要
自动生成一份报告？报告应该作为敏捷流程的必须环节吗？
```

**验证点**（SKILL.md §1 定位 + §5 硬约束）：
- 是否明确说明 agile-report 是**按需衍生**，不是流程必须环节
- 是否说明不参与 using-agile 路由检测
- 是否说明只在用户需要对外汇报时才触发
- ❌ 错误回答：建议每个 Sprint 自动生成 / 建议加入流程闭环

## T6 — 视觉编码：非技术受众适配

```
我领导对技术完全不懂，报告里的"故事点""MoSCoW""ADR"这些词他看不懂。
报告要怎么改才能让他看得明白？
```

**验证点**（chart-config.md §三 术语去技术化表）：
- 是否给出完整映射表（故事点→任务量、MoSCoW·Must→核心需求、ADR→技术决策记录、DoD→验收标准、Sprint→迭代周期）
- 是否说明转换时机（写入 HTML 前强制转换）
- 配色规则：是否说明红/黄/绿三色按完成率区间（<60%/60-85%/>85%）

## T7 — 一致性校验：YAML/.md 不一致时（边界）

```
我手改了 PRODUCT-BACKLOG.yaml 的一个条目状态，但忘了同步到 .md。
现在要生成报告，会怎样？
```

**验证点**（report-rules.md §四 + SKILL.md §2a）：
- 是否说明读 YAML 前必跑一致性校验（id 集合 / 条目数 / priority+status 一致）
- 不一致时是否**停下报告差异**（列出具体哪个 id 哪个字段不一致）
- 是否请用户确认以哪份为准后再继续（不静默挑一份算下去）
