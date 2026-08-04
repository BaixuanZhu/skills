# agile-report 达尔文验证报告：v1.0.0 首次评估（实跑 + 双盲评 + 仲裁）

> **目的**：用达尔文「实跑 + 独立盲评 + 独立仲裁 + 棘轮」原则，验证新技能 agile-report v1.0.0 的核心能力成立，并定位可修复缺陷。
> **日期**：2026-08-04
> **方法**：工具链命令实跑 + 2 个独立盲评 agent（A/B）+ 仲裁 agent + 棘轮。
> **结论**：✅ **PASS（条件性）** —— 核心价值成立（数据聚合/陷阱知识/术语映射/定位均强项），4 个必修项为局部可修复缺陷，修完后保留。

## 一、本轮评估概览

agile-report 是新技能（无旧版对比），评估采用「实跑验证 + 双盲评质量打分」模式：
- **实跑**：工具链命令（Playwright pdf）真实执行，验证陷阱描述准确性
- **双盲评**：2 个独立 agent 按 9 维度对 7 条 test-prompt 打分，对照 ground-truth 核对数值
- **仲裁**：独立核实证据 + 查漏 + 棘轮判定

## 二、工具链实跑验证（达尔文强制项）

### 2.1 第一轮实跑（chromium 下载方案）——暴露根本问题

实跑 toolchain.md v1 的 `--browser chromium` 主命令 + 检测步骤，**确证 2 个真实问题**：

| 实跑项 | 结果 | 价值 |
|---|---|---|
| `npx playwright pdf --browser chromium ...` | 报 `Executable doesn't exist`（运行时错，非参数错） | ✅ 命令参数准确；确证陷阱 #4（装包≠装浏览器） |
| `npx playwright install chromium` | **下载超时失败**（用户网络环境） | ⚠️ **根本问题**：chromium 150MB+ 下载在目标环境不可行 |
| `npx playwright --version` 检测 | npx **自动安装** playwright@1.62.1，不报错 | ⚠️ 发现 1：检测步骤失效 |
| `-D` vs `-g` | 用户审视发现 | ⚠️ 发现 2：`-D` 污染 Java 项目 |

**关键转折**：用户指出"装个 playwright 依赖的浏览器都装不上，网络问题太严重"——这暴露了 v1 主方案的根本缺陷：**在目标用户环境（大陆 Java 开发者）下，chromium 下载是死路**。一个"主方案跑不通、降级才是常态"的设计是本末倒置。

### 2.2 第二轮实跑（--channel msedge 方案）——根本性修复

用户提出改用系统浏览器。实跑 `--channel msedge` 方案：

| 实跑项 | 结果 |
|---|---|
| `npx playwright pdf --channel msedge --wait-for-timeout 2000 ...` | ✅ **PDF 成功生成**（33KB，exit=0，零浏览器下载） |
| `npx playwright screenshot --channel msedge ...` | ✅ PNG 生成（1280×720） |
| 视觉验证（AI 图像分析） | ✅ 仪表盘图表正确渲染（指针指 85，标"完成率 85%"），非空白 |

**v2 方案完全跑通**：零浏览器下载（复用系统 Edge），ECharts 图表正确渲染，命令语法简单。

### 2.3 实跑驱动的工具链重写

基于两轮实跑，重写 toolchain.md：
- 主方案：`--channel msedge`（零下载，实跑验证通过）
- 降级 1：手动打印（无 Playwright 时）
- 降级 2：git log 纯文本（无敏捷产物时）
- chromium 下载（`--browser chromium`）**从主方案降为不再推荐**——实跑证明在目标环境不可行

**v1 必修项 #1（检测步骤）、#2（-D/-g）随主方案变更自然演化为 v2 的陷阱 #5/#6/#7**（PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD、-g、npx 自动安装）。


## 三、双盲评结果

### 总分对比（两 agent 方向一致，B 比 A 严）

| | Agent A | Agent B | 一致性 |
|---|---|---|---|
| 总分 | 665/700 (95.0%) | 627/700 (89.6%) | B 比 A 严 5.4 分/prompt |
| 数值正确性（T1/T4） | ✓ 全通过 | ✓ 全通过 | ✅ 双方独立核对一致 |
| 方向 | 失分集中 toolchain + chart-config 语法 | 同 | ✅ 完全一致 |

### 单 prompt 评分

| Prompt | A | B | 共识 |
|---|---:|---:|---|
| T1 完整态核心路径 | 90 | 82 | 工具链检测失效 + `{[...]}` 语法拖累 D4 |
| T2 工具链陷阱 | 91 | 84 | 5 大陷阱全到，但检测失效 + `-D` 错配扣 D4/D5 |
| T3 降级态 | 97 | 91 | 强项（git log 解析完整） |
| T4 阻塞项识别 | 97 | 88 | T-003 正确识别，原因取数路径偏弱 |
| T5 范围边界 | 98 | 95 | 最强项（按需衍生定位三处强化） |
| T6 术语映射 | 97 | 96 | 强项（11 行映射无遗漏） |
| T7 一致性校验 | 95 | 91 | 规则完整，跨技能引用是软肋 |

### 双方独立命中的同一批关键证据（交叉验证）

| 能力点 | 技能位置 | A+B 确认 |
|---|---|---|
| 完成率公式 85.7% | report-rules §2.1 | A+B 均核算通过 |
| 点数回读 59/43 | report-rules §2.3 | A+B 均核算通过 |
| T-003 阻塞识别（移出 2 次） | template §2.6 | A+B 均命中 |
| 术语映射 11 行 | chart-config §三 | A+B 均确认完整 |
| 5 大陷阱 | toolchain §四 | A+B 均确认全到 |

## 四、仲裁结论

### 证据真实性：全部 ✓

仲裁独立 grep + Node.js 实测核实 A/B 引用的全部证据——**0 条虚构、0 条方向偏差**。

### 仲裁独立查漏：2 个

| 漏报 | 发现者 | 严重度 | 核实方式 |
|---|---|---|---|
| chart-config `{[...]}` 非法 JS（5 处） | A 发现，B 漏报 | 🔴 必修 | Node.js 实测 `SyntaxError` |
| report-rules §2.1 分母未限定节范围 | 仲裁独立发现（A 列次级） | 🟡 必修（升格） | fixture sprint-*.md「条目状态建议」节有同格式行 |

## 五、棘轮判定：✅ PASS

### 必修清单（4 项 + 1 根本性重写，全部完成）

| # | 问题 | 修复 | 状态 |
|---|---|---|---|
| 1 | toolchain 检测步骤失效（npx 自动安装） | 改为直接尝试 pdf 命令按报错分流 | ✅ v2 重写吸收 |
| 2 | `-D` 污染 Java 项目 | 改 `-g` + 陷阱表补条目 | ✅ v2 重写吸收 |
| 3 | chart-config `{[...]}` 非法 JS（5 处） | 改 `[...]` + 注释占位，Node 验证通过 | ✅ 已修 |
| 4 | report-rules §2.1 分母未限定节范围 | 补"仅 `## 任务清单` 节内" | ✅ 已修 |
| **5** | **chromium 下载在目标网络环境不可行（根本性）** | **主方案改 `--channel msedge` 复用系统 Edge，零下载，实跑验证通过** | ✅ **v2 重写** |

### 强项确认（无需改）

- 数据聚合层（report-rules §二）：公式机械可执行，数值正确
- 视觉编码层（chart-config §一/§二/§三）：选型映射 + 配色 + 术语去技术化完整
- 定位层（SKILL §0/§1/§5）：按需衍生边界清晰
- 陷阱知识（toolchain §四）：5 大陷阱全到，命令参数实跑确证

## 六、产物清单

- `test-prompts.md` — 7 条 test-prompt
- `rubric.md` — 9 维度评分标准 + 各 prompt 判分锚点
- `fixtures/` — 测试数据（3 Sprint + Backlog + ground-truth）
- `toolchain-realrun.md` — 工具链命令实跑记录（含 2 个发现）
- `blind-A.md` — Agent A 盲评（665/700）
- `blind-B.md` — Agent B 盲评（627/700，从严）
- `arbitration.md` — 仲裁报告（证据核实 + 查漏 + 棘轮判定）
- `report.md` — 本报告

## 七、复现指引

```bash
# 1. 工具链实跑：node + npx playwright screenshot/pdf（见 toolchain-realrun.md / toolchain-realrun-v2.md）
# 2. 盲评：agent 拿 rubric.md + test-prompts.md + skills/agile-report/ + fixtures/
# 3. 数值核对：对照 fixtures/ground-truth.md
# 4. 仲裁：读 blind-A/B.md，独立 grep + Node 实测核实
# 5. 棘轮：必修项是否修复 + 强项是否保留
# 6. 端到端实跑：见 realrun/stage-verification.md（HTML 生成 + 截图验证）
```

## 八、第三轮迭代：渲染样式调优（达尔文式持续验证）

评估完成后，用户对实跑产物 PDF 做了多轮样式审视，驱动技能演进（每轮都实跑验证）：

### 8.1 遇到的渲染问题与修复

| # | 问题 | 根因 | 修复 |
|---|---|---|---|
| 1 | chromium 下载不可行（网络） | 主方案 `--browser chromium` 需 150MB 下载 | 改 `--channel msedge` 复用系统 Edge，零下载 |
| 2 | PDF 页边距不可控 | CLI 不支持 `--margin` | CSS `@page { margin }` 规则 |
| 3 | 表格在页边截断 | `section { page-break-inside: avoid }` 失效 | section 不设 avoid，改 `tr` + 图表容器分层 avoid |
| 4 | 图表左右溢出 | ECharts `width:100%` 按视口算 canvas | body 固定 A4 宽度 186mm，图表 100% 永不溢出 |
| 5 | 背景色丢失 | CLI 不支持 `--print-background` | CSS `print-color-adjust: exact` |
| 6 | 清晰度糊 | ECharts canvas 栅格化 | 改 `renderer: 'svg'` 矢量 |
| 7 | 饼图 label 重叠 | 0 值扇区占位 + `\n` 不换行 | `.filter(d => d.value > 0)` + `label.lineHeight` |
| 8 | 留白大、博客感 | Pico.css line-height 1.5 + 桌面字号放大 | 改 **Pure.css**（line-height 1.15，密度高） |
| 9 | 难点项表格难看 | 长文本"原因"被列宽限制 | 改卡片布局 `.blocked-item` |
| 10 | 下阶段计划表格行高乱 | `pure-table` padding 撑乱徽章 | 改 flex 布局 `.plan-item` |
| 11 | 进度条橙+黑不协调 | 纯黄 `#ffc107` 配黑字 | 改 `#f39c12` + 白字，纯色不渐变 |

### 8.2 产物策略演进

| 阶段 | 策略 | 问题 |
|---|---|---|
| v1 | Playwright PDF 为主产物 | CLI 限制多（margin/background/清晰度全踩坑） |
| v2 | 浏览器手动导出 PDF | 用户反馈"样式也有问题" |
| **v3（定稿）** | **HTML 唯一必产物，PNG/PDF 可选询问** | HTML 是 A4 纸张样式所见即所得，导出由用户按需选 |

### 8.3 最终产物

`eval/agile-report/fixtures/project-root/reports/stage-report-20260804.html`（Pure.css 版，7.4KB）：
- 浏览器打开即所见即所得（A4 纸张样式，居中带阴影）
- ECharts SVG 矢量图表，截图/打印清晰
- 信息密度高（相比 Pico 版高度 2748px → Pure 版 1566px）
- 用户自行 Ctrl+P 导出 PDF 或用 Playwright 截图/PDF（可选）

**达尔文验证的最大收益**：不是评估框架本身发现的，而是**用户对实跑产物的连续审视**驱动的——每一轮"样式不好看"的反馈都定位到具体根因（CLI 限制/CSS 框架选型/ECharts 配置），并实跑验证修复。这证明"评估不是一次性打分，而是持续到产物达标的迭代"。
