# 图表配置与视觉编码（agile-report 参考）

本文件定义图表选型、ECharts 配置骨架、配色规则、术语去技术化映射。

## 一、渲染器：必须用 SVG（矢量）

```javascript
// 所有 echarts.init 必须传第三参数 { renderer: 'svg' }
echarts.init(document.getElementById('chart-xxx'), null, { renderer: 'svg' })
```

⚠️ 不能用默认 canvas——栅格图截图/打印放大糊；SVG 矢量任意缩放清晰。

## 二、图表选型映射（数据 → 图表类型）

| 数据 | 图表类型 | ECharts type | 容器 class | 选型理由 |
|---|---|---|---|---|
| 阶段整体完成度 | **进度条**（HTML/CSS，非 ECharts） | — | `.progress` | 比 gauge 环形更紧凑，信息密度高 |
| 各迭代完成率 | 柱状图 | `bar` | `.chart` | 趋势上升 = "在变好"的感知 |
| 承诺 vs 完成任务量 | 分组柱状 | `bar`（多 series） | `.chart` | 容易理解"承诺多少、做到多少" |
| 待办分布 | 饼图 | `pie` | `.chart-pie` | "剩下哪些重要的没做" |
| 移出/阻塞任务 | **卡片**（HTML，非图表） | — | `.blocked-item` | 详细信息图表反而不清 |

**阶段完成度用进度条而非 gauge 环形**——环形占面积大、密度低；横条进度条一行够，能嵌文字。见 `report-template.md §4.2`。

## 三、配色规则

### 3.1 完成率三色（贯穿进度条 + 柱状图）

| 完成率区间 | 颜色 | 色值 | 语义 | CSS class |
|---|---|---|---|---|
| `< 60%` | 红 | `#e74c3c` | 风险/滞后 | `.red` |
| `60% ~ 85%` | 橙 | `#f39c12` | 关注/在途 | `.yellow` |
| `> 85%` | 绿 | `#27ae60` | 健康/达成 | `.green` |

⚠️ **用纯色，不用渐变**。深色背景配**白字**（`color: #fff`），不配黑字。

### 3.2 柱状图动态取色（按各柱完成率落区间）

```javascript
itemStyle: {
  color: function(params) {
    return params.value < 60 ? '#e74c3c' : params.value <= 85 ? '#f39c12' : '#27ae60';
  }
}
```

### 3.3 图例与标注

- ✅ 所有 legend / axis label / tooltip 用**中文**
- ❌ 禁用纯英文 legend（`Must/Should/Could` 须显示为"核心/次要/可选需求"）
- 字号统一 `fontSize: 11`（报告紧凑，不用 ECharts 默认 12）

## 四、术语去技术化映射（强制——写入 HTML 前转换）

| 技术术语（内部） | 甲方术语（报告里） |
|---|---|
| 故事点 / point | 任务量 |
| T-NNN / F-NNN | 任务编号 |
| MoSCoW · Must | 核心需求 |
| MoSCoW · Should | 次要需求 |
| MoSCoW · Could | 可选需求 |
| ADR | 技术决策记录 |
| DoD | 验收标准 |
| Sprint | 迭代周期 |
| Backlog | 待办清单 |
| completed（.done.yaml） | 已完成 |
| moved_next（.done.yaml） | 移至下期 |

**转换时机**：环节 B 生成 HTML 时，所有从数据源读出的字段值在写入 HTML 前过一遍此表。

## 五、ECharts 配置骨架

### 5.1 柱状图 —— 迭代周期完成趋势

```javascript
echarts.init(document.getElementById('chart-sprint-bar'), null, { renderer: 'svg' }).setOption({
  grid: { left: 40, right: 20, top: 20, bottom: 30 },   // 紧凑边距
  xAxis: { type: 'category', data: ['迭代周期 001', '迭代周期 002', '迭代周期 003'], axisLabel: { interval: 0, fontSize: 11 } },
  yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%', fontSize: 11 } },
  series: [{
    type: 'bar', barWidth: '40%', data: [100, 80, 75],
    itemStyle: { color: p => p.value < 60 ? '#dc3545' : p.value <= 85 ? '#ffc107' : '#198754' },
    label: { show: true, position: 'top', formatter: '{c}%', fontSize: 11 }
  }]
});
```

### 5.2 分组柱状 —— 承诺 vs 完成任务量

```javascript
echarts.init(document.getElementById('chart-burndown'), null, { renderer: 'svg' }).setOption({
  grid: { left: 40, right: 20, top: 30, bottom: 30 },
  legend: { data: ['承诺任务量', '完成任务量'], textStyle: { fontSize: 11 }, top: 0 },
  xAxis: { type: 'category', data: ['迭代周期 001', '迭代周期 002', '迭代周期 003'], axisLabel: { fontSize: 11 } },
  yAxis: { type: 'value', name: '任务量', nameTextStyle: { fontSize: 11 }, axisLabel: { fontSize: 11 } },
  series: [
    { name: '承诺任务量', type: 'bar', data: [17, 24, 18], itemStyle: { color: '#0d6efd' } },
    { name: '完成任务量', type: 'bar', data: [17, 16, 10], itemStyle: { color: '#198754' } }
  ]
});
```

### 5.3 饼图 —— 待办分布

```javascript
echarts.init(document.getElementById('chart-backlog-pie'), null, { renderer: 'svg' }).setOption({
  legend: { bottom: 0, itemWidth: 14, itemHeight: 14, textStyle: { fontSize: 11 } },
  series: [{
    type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
    minAngle: 5,              // 最小扇区角度，防小切片 label 叠在一起
    minShowLabelAngle: 2,     // 小于该角度不显示 label（防重叠）
    data: [
      { value: 1, name: '核心需求·待开展', itemStyle: { color: '#dc3545' } },
      { value: 5, name: '核心需求·已完成', itemStyle: { color: '#198754' } },
      { value: 7, name: '次要需求·已完成', itemStyle: { color: '#82c91e' } },
      { value: 1, name: '可选需求·待开展', itemStyle: { color: '#adb5bd' } }
    ].filter(d => d.value > 0),   // ⚠️ 必须过滤 0 值扇区——0 值无意义还占位致 label 重叠
    label: {
      formatter: '{b}\n{c}项 ({d}%)', fontSize: 10,
      lineHeight: 14            // ⚠️ 必须设——没这条 \n 不换行（ECharts 默认不认 \n）
    },
    labelLine: { length: 8, length2: 10 }
  }]
});
```

## 六、饼图陷阱

| 陷阱 | 后果 | 对策 |
|---|---|---|
| 不过滤 0 值扇区 | 0 值无意义还占位，label 挤在一起重叠 | `.filter(d => d.value > 0)` |
| `formatter` 写 `\n` 不换行 | label 显示成"名称\n数值"一坨 | 必须配 `label: { lineHeight: 14 }` 才触发换行 |
| 用 `legend: { type: 'scroll' }` | 图例变翻页箭头（像分页器），难看 | 用默认平铺 legend，4 个图例项放得下 |
