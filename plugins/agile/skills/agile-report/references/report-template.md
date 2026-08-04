# HTML 报告骨架（agile-report 参考）

本文件是报告的**结构模板**——定义 section 顺序、占位符、CSS 样式。agent 套此骨架填数据，图表配置从 `chart-config.md` 取。

**权威实跑样本**：`eval/agile-report/fixtures/project-root/reports/stage-report-20260804.html`（Pure.css 版，所有样式直接套用）。

## 一、技术栈选型

| 组件 | 选型 | 理由 |
|---|---|---|
| CSS 框架 | **Pure.css 3.0.0**（classless 基础 + 少量 class） | 信息密度高（line-height 1.15），不像 Pico/Sakura 那种博客风格大留白；CDN 仅 16KB |
| 图表库 | ECharts（`renderer: 'svg'`） | SVG 矢量渲染，截图/打印清晰；canvas 栅格化会糊 |
| 布局策略 | body 固定 A4 内容宽度（186mm）居中 | 图表 `width:100%` 永远等于 A4 宽度，不溢出截断；屏幕预览=打印效果 |

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/pure-min.css">
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
```

## 二、整体 HTML 结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>{项目名} · {阶段名}进度报告</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/pure-min.css">
  <style>/* 见 §三 */</style>
</head>
<body>
  <!-- §四 封面 -->
  <!-- §五 阶段总览（进度条）-->
  <!-- §六 迭代周期完成趋势（柱状）-->
  <!-- §七 工作量对比（分组柱状）-->
  <!-- §八 待办分布（饼图）-->
  <!-- §九 难点与阻塞项（卡片）-->
  <!-- §十 下阶段计划（flex 列表）-->
  <script>/* ECharts SVG 初始化，见 chart-config.md */</script>
</body>
</html>
```

## 三、CSS 样式（直接复制）

```css
@page { size: A4; margin: 12mm; }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; }
html { background: #e9ecef; line-height: 1.4; }
body {
  width: 186mm;              /* A4 内容宽度（210mm - 12mm×2 边距）*/
  margin: 16px auto;
  padding: 10mm 12mm;
  background: #fff;
  box-shadow: 0 0 16px rgba(0,0,0,0.08);  /* 屏幕预览纸张阴影 */
  font-size: 14px;
  color: #333;
}
h1 { font-size: 1.5rem; margin: 0 0 0.25rem; }
h2 { font-size: 1.1rem; margin: 1.2rem 0 0.5rem; padding-bottom: 0.3rem; border-bottom: 2px solid #dee2e6; }
p { margin: 0.4rem 0; }
ul { margin: 0.3rem 0; padding-left: 1.2rem; }
li { margin: 0.15rem 0; }

/* 封面——无边框（硬分隔线突兀），纯留白过渡 */
.cover { text-align: center; padding: 4mm 0 3mm; margin-bottom: 4px; }
.cover .meta { color: #6c757d; margin: 2px 0; font-size: 0.85rem; }

/* 进度条（Pure 无内置，手写）。三档纯色 + 白字，不用渐变（渐变更丑）*/
.progress { height: 22px; background: #e9ecef; border-radius: 11px; overflow: hidden; margin: 4px 0; }
.progress-bar { height: 100%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: bold; color: #fff; }
.progress-bar.yellow { background: #f39c12; }   /* 60-85% 关注 */
.progress-bar.red { background: #e74c3c; }       /* <60% 风险 */
.progress-bar.green { background: #27ae60; }     /* >85% 健康 */

/* 状态徽章（Pure 无内置）*/
.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; color: #fff; }
.badge-danger { background: #dc3545; }
.badge-secondary { background: #6c757d; }

.text-muted { color: #6c757d; }
.small { font-size: 0.85rem; }

/* 图表容器——固定高度，page-break 防切断 */
.chart { width: 100%; height: 220px; margin: 4px 0; page-break-inside: avoid; }
.chart-pie { width: 75%; height: 240px; margin: 4px auto; page-break-inside: avoid; }

/* 阻塞项——卡片而非表格（长文本"原因"在表格列里难看）*/
.blocked-item { border-left: 3px solid #dc3545; padding: 6px 10px; margin: 4px 0; background: #f8f9fa; border-radius: 3px; page-break-inside: avoid; }
.blocked-item .blocked-title { font-weight: 600; }
.blocked-item .blocked-meta { color: #6c757d; font-size: 0.8rem; }

/* 下阶段计划——flex 列表而非表格（表格行高会被徽章撑乱）*/
.plan-item { display: flex; align-items: baseline; gap: 10px; padding: 5px 0; }
.plan-item .badge { flex-shrink: 0; width: 70px; text-align: center; }

@media print {
  html { background: #fff; }
  body { margin: 0; padding: 0; box-shadow: none; width: auto; }
}
```

## 四、各 section 骨架

### 4.1 封面（精简，无边框）

```html
<header class="cover">
  <h1>{项目名}</h1>
  <div class="meta">{阶段名} · 阶段进度报告 · {YYYY-MM-DD} · {团队}</div>
</header>
```

**数据源**：项目名/团队 ← DOD.md 项目画像；阶段名 ← 用户确认；**降级态 ③** 加 `<div class="meta" style="color:#dc3545;">⚠️ 数据来源：git log（简化版）</div>`。

### 4.2 阶段总览（进度条替代环形仪表盘）

```html
<section>
  <h2>阶段总览</h2>
  <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
    <span style="font-weight:600;">整体完成率</span>
    <span class="text-muted" style="font-weight:bold;">{完成率}%（{红/黄/绿语义}）</span>
  </div>
  <div class="progress"><div class="progress-bar {red|yellow|green}" style="width:{完成率}%;">{完成率}%</div></div>
  <p class="small text-muted">{一句话结论}</p>
</section>
```

**配色档位**：`<60% red` / `60-85% yellow` / `>85% green`。progress-bar 的 class 按完成率落区间取。

### 4.3 迭代周期完成趋势（柱状）

```html
<section>
  <h2>迭代周期完成趋势</h2>
  <div id="chart-sprint-bar" class="chart"></div>
  <p class="small text-muted">{文字摘要}</p>
</section>
```

### 4.4 工作量对比（分组柱状）

```html
<section>
  <h2>工作量对比</h2>
  <div id="chart-burndown" class="chart"></div>
  <p class="small text-muted">承诺任务量 {X}，完成 {Y}（{Z}%）。{差距说明}</p>
</section>
```

### 4.5 待办分布（饼图）

```html
<section>
  <h2>待办分布</h2>
  <div id="chart-backlog-pie" class="chart-pie"></div>
  <p class="small"><span class="badge badge-danger">核心需求</span> 待开展 {N} 项（{说明}）</p>
</section>
```

### 4.6 难点与阻塞项（卡片，非表格）

```html
<section>
  <h2>难点与阻塞项</h2>
  <div class="blocked-item">
    <div class="blocked-title">{任务编号} · {标题} <span class="badge badge-danger">移出 {N} 次</span></div>
    <div class="blocked-meta">{涉及哪些迭代周期}</div>
    <div class="small" style="margin-top:4px;">{原因正文，从 sprint .md「条目状态建议」节回读}</div>
  </div>
</section>
```

**为什么用卡片不用表格**：长文本"原因"放表格列会被列宽限制导致难看；卡片正文区自然换行。

### 4.7 下阶段计划（flex 列表，非表格）

```html
<section>
  <h2>下阶段计划</h2>
  <div class="plan-item">
    <span class="badge badge-danger">核心需求</span>
    <span>{任务编号} {标题}（{说明}）</span>
  </div>
  <div class="plan-item">
    <span class="badge badge-secondary">可选需求</span>
    <span>{任务编号} {标题}（{说明}）</span>
  </div>
</section>
```

**为什么用 flex 不用表格**：表格行高会被徽章撑乱（Pure 的 `pure-table` 给 td 加 padding，徽章作为内联元素被拉伸）；flex 用 `align-items: baseline` 对齐更可控。
