# 工具链实跑验证 v2（--channel msedge 方案）

> 日期：2026-08-04
> 背景：v1 实跑发现 chromium 下载因网络问题无法完成（用户环境）。改用 `--channel msedge` 复用系统浏览器，重新实跑验证。

## 一、方案变更

| 项 | v1（chromium 下载） | v2（--channel msedge） |
|---|---|---|
| 浏览器来源 | 下载 Playwright bundled chromium（150MB+，Google 服务器） | 复用系统已装的 Microsoft Edge |
| 网络依赖 | ❌ 重度（chromium 下载常超时/失败） | ✅ 零（Edge Windows 自带） |
| 安装步骤 | `npm install -g playwright` + `npx playwright install chromium` | 仅 `npm install -g playwright`（设 `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` 跳过下载） |
| 命令 | `npx playwright pdf --browser chromium ...` | `npx playwright pdf --channel msedge ...` |

## 二、实跑结果

### 2.1 环境检测

```
Edge 路径: /c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe  ✓ 已装
```

### 2.2 PDF 生成（主命令）

```bash
npx playwright pdf --channel msedge --wait-for-timeout 2000 --paper-format A4 test.html test.pdf
```

**输出**：
```
Navigating to ...test.html
Waiting for timeout 2000...
Saving as pdf into ...test.pdf
exit=0
文件: test.pdf (33160 bytes, PDF v1.4, 1 page)
```

✅ **PDF 成功生成**，零浏览器下载。

### 2.3 截图验证（确认图表非空白）

```bash
npx playwright screenshot --channel msedge --wait-for-timeout 2000 test.html test.png
```

**输出**：PNG 1280×720, 25088 bytes。

**视觉验证**（AI 图像分析）：图片含清晰渲染的仪表盘图表，指针指向 85，标注"完成率 85%"。**图表非空白**。

✅ 确证 ECharts 异步渲染在 `--wait-for-timeout 2000` 下正常完成。

## 三、结论

`--channel msedge` 方案**实跑完全跑通**：
- 零浏览器下载（绕开网络问题）
- PDF + 截图都能生成
- ECharts 图表正确渲染（视觉验证）
- 命令语法简单（`--channel msedge` 替代 `--browser chromium`）

**v1 的 4 个必修项中，#1（检测步骤）、#2（-D/-g）随主方案变更自然消解**——v2 不再需要检测 chromium 是否下载、不再纠结 -D 还是 -g（只装 npm 包，不装浏览器）。

**保留的陷阱**（v2 仍适用）：
- `--wait-for-timeout` 是毫秒（已视觉验证：有 wait 图表渲染、验证通过）
- `playwright` ≠ `@playwright/cli`
- ECharts 必须 headless 浏览器渲染
- JS 图表库不能用 weasyprint/wkhtmltopdf

**新增要点**：
- `--channel msedge`（Windows）/ `--channel chrome`（若装了 Chrome）复用系统浏览器
- 设 `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` 彻底跳过 chromium 下载
- Edge 是 Windows 10/11 自带，无需额外安装
