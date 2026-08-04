# 工具链与导出（agile-report 参考）

## 一、产出策略

```
环节 C（HTML 生成后）：
  1. 必产：reports/stage-report-{日期}.html（浏览器打开即所见即所得，A4 纸张样式）
  2. 询问用户："需要转成图片（PNG）或 PDF 吗？"
     - 选 PNG → §三 截图命令
     - 选 PDF → §四 PDF 命令
     - 都不要 / 都要 → 按用户选择
     - Playwright 不可用 → 提示浏览器打开 HTML 手动 Ctrl+P 导出（§五）
```

**为什么 HTML 是唯一必产物**：Playwright CLI 的 PDF/截图有硬限制（不支持 `--margin`/`--print-background`/`deviceScaleFactor`，见 §六陷阱）。HTML 本身是 A4 纸张样式（body 固定 186mm 宽），浏览器打开即所见即所得，用户自行导出最稳定。

## 二、Playwright 安装（可选——只有用户要 PNG/PDF 时才需要）

### 2.1 包名辨析

| 包名 | 是什么 | 用不用 |
|---|---|---|
| **`playwright`** | 标准 Playwright 包，含 `pdf`/`screenshot` 子命令 | ✅ **用这个** |
| `@playwright/cli` | Agent CLI，为 AI agent 设计的**浏览器控制**工具 | ❌ 不要用 |

### 2.2 安装（全局，复用系统浏览器，零浏览器下载）

```bash
set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1   # 跳过 chromium 下载（用系统 Edge，不需要 150MB+ 下载）
npm install -g playwright
```

- `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`：**必须设**——否则触发 chromium 150MB+ 下载，大陆网络常超时。用 `--channel msedge` 复用系统 Edge 根本不需要这个下载。
- `npm install -g playwright`：**全局**装（`-g` 不是 `-D`）——本技能受众是 Java 项目，`-D` 会污染项目 node_modules；Playwright 是系统级工具，全局装一次所有项目共用。

### 2.3 检测（fail-loud，不要用 --version）

⚠️ **不要用 `npx playwright --version` 检测**——`npx` 会静默自动安装 playwright 包，`--version` 永不报错，得到虚假"已就绪"信号。

直接尝试真正要用的命令：
```bash
npx playwright screenshot --channel msedge --help
```
- 正常输出 → 就绪
- `command not found` → 跑 §2.2 安装
- `Executable doesn't exist` → 跑 `npx playwright install msedge`（或用 `--channel chrome`）

## 三、PNG 截图导出（用户选 PNG 时）

```bash
npx playwright screenshot --channel msedge --wait-for-timeout 2000 --full-page \
  reports/stage-report-{YYYYMMDD}.html reports/stage-report-{YYYYMMDD}.png
```

| 参数 | 作用 |
|---|---|
| `--channel msedge` | 复用系统 Edge，零浏览器下载 |
| `--wait-for-timeout 2000` | 等 2 秒让 ECharts SVG 渲染完（**毫秒**，不是秒） |
| `--full-page` | 截整页（不加只截视口 720px 高） |

⚠️ **CLI 截图限制**：不支持 `deviceScaleFactor`（高 DPI），固定 1280px 宽，放大看会糊。若用户要超清图，提示用浏览器打开 HTML 后手动截图，或接受 PDF（矢量清晰）。

## 四、PDF 导出（用户选 PDF 时）

```bash
npx playwright pdf --channel msedge --wait-for-timeout 2000 --paper-format A4 \
  reports/stage-report-{YYYYMMDD}.html reports/stage-report-{YYYYMMDD}.pdf
```

CLI PDF 的已知限制（margin/background/分页）见 §六陷阱 #7——HTML 须已用 CSS 预处理，不能靠命令参数补救。

## 五、降级：浏览器手动导出（Playwright 不可用时）

触发：用户环境装不上 Playwright（无 Node / 公司网络限制），或用户不要 PNG/PDF 只要 HTML。

方案：技能只产 HTML，提示用户：
1. 用浏览器（Edge/Chrome）打开 `reports/stage-report-{YYYYMMDD}.html`
2. `Ctrl+P` → 纸张大小选 A4 → 边距选"无"或"默认" → 另存为 PDF
3. HTML 的 body 已是 A4 宽度样式（186mm），所见即所得

HTML 已内嵌 `@media print` 打印适配（见 `report-template.md §三`），浏览器原生导出效果稳定。

## 六、核心陷阱汇总

| # | 陷阱 | 后果 | 对策 |
|---|---|---|---|
| 1 | `--wait-for-timeout` 单位是**毫秒** | 写 `2` = 2ms，图表没渲染就截 → 空白 | 写 `2000`（=2秒） |
| 2 | JS 图表库（ECharts）**必须 headless 浏览器**渲染 | 用 weasyprint/wkhtmltopdf → ES6+ JS 跑不了，图表空白 | 只用 Playwright（截图/PDF），不用纯 HTML→PDF 工具 |
| 3 | `playwright` ≠ `@playwright/cli` | 用错包 → 没有 `screenshot`/`pdf` 子命令 | 用标准 `playwright` 包 |
| 4 | `npm install` 默认触发 chromium 下载 | 150MB+ 大陆网络超时失败 | **必须设 `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`**，用 `--channel msedge` 复用系统 Edge |
| 5 | `npm install -D` 污染 Java 项目 | `-D` 装进项目 node_modules | 必须 `-g`（全局） |
| 6 | `npx playwright --version` **静默自动安装** | 检测失效——永不报错，虚假"已就绪" | 直接尝试 `screenshot`/`pdf` 命令按报错分流 |
| 7 | CLI 不支持 `--margin`/`--print-background` | PDF 页边距/背景色无法命令行控制 | 用 CSS `@page` + `print-color-adjust: exact` |
