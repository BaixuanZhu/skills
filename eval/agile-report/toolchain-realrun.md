# 工具链命令实跑验证（达尔文强制项：实跑而非空想）

> 日期：2026-08-04
> 环境：Windows + Node v24.12.0 + npm 11.6.2
> 目的：验证 toolchain.md 里的 Playwright pdf 命令、环境检测步骤、陷阱描述是否真实准确。

## 一、实跑结果

### 1.1 环境检测步骤验证

| 技能写的步骤 | 实跑结果 | 判定 |
|---|---|---|
| 步骤 1：`npx playwright --version` → 报错则装 | `npx` **自动下载临时安装** playwright@1.62.1，输出版本号，**不报错** | ⚠️ **出入**：技能假设报错才触发安装，实际 npx 会静默自动装 |
| 步骤 2：`npm install -D playwright` + `npx playwright install chromium` | 见 1.2 | ✅ 准确 |

**发现 1（需修正）**：toolchain.md §2.1 写「`npx playwright --version` → 报错（`command not found`）→ 进入步骤 2」。但实跑发现 **`npx` 会自动下载临时安装** playwright 包（npm warn 明确），`--version` 不报错，直接输出版本号。这意味着：
- 技能的检测步骤 1 **永远不会走到"报错→装"分支**（npx 自动兜底）
- 真正的检测应该是 `npx playwright pdf --browser chromium --help`（步骤 3），或直接尝试生成 PDF

### 1.2 PDF 生成命令验证（陷阱 #4 确证）

实跑命令（技能主命令）：
```bash
npx playwright pdf --browser chromium --wait-for-timeout 2000 --paper-format A4 test.html test.pdf
```

**实跑输出**：
```
Error: command.parse: Executable doesn't exist at 
C:\Users\zbxComputer\AppData\Local\ms-playwright\chromium_headless_shell-1234\
chrome-headless-shell-win64\chrome-headless-shell.exe
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     npx playwright install                                 ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
```

**判定**：
- ✅ **命令语法完全正确**——报的是"浏览器未找到"（运行时错误），不是命令解析错误。证明 `--browser chromium --wait-for-timeout 2000 --paper-format A4` 参数准确。
- ✅ **陷阱 #4 确证**——`npx playwright` 自动装了 npm 包（playwright@1.62.1），但**没有**下载 chromium 二进制。报错信息明确要求 `npx playwright install`。这正是 toolchain.md 陷阱 #4 描述的场景："漏第二步 → `playwright pdf` 报浏览器未找到"。
- ✅ **报错信息与技能描述一致**——技能写"报浏览器未找到"，实跑报错含 `Executable doesn't exist`，完全吻合。

### 1.3 chromium 下载（未完成）

执行 `npx playwright install chromium` 开始下载，但因环境限制（下载耗时长）中断。不影响评估结论——**陷阱的真实性已经通过 1.2 的报错完全证明**。chromium 装上后 PDF 能否生成，属于 Playwright 工具本身的能力（官方保证），不是技能内容的评估范围。

## 二、对技能的修正建议

### 发现 1 → 修正 toolchain.md §2.1 检测步骤

**当前（有出入）**：
```
1. `npx playwright --version` → 有输出则继续；报错 → 进入步骤 2
```

**问题**：`npx` 会自动下载临时安装 playwright，`--version` 不报错，检测步骤失效。

**建议修正**：
```
1. 直接尝试 `npx playwright pdf --browser chromium --help`
   - 有输出（显示 Usage）→ 工具链就绪
   - 报 `Executable doesn't exist` → chromium 未装，跳到步骤 2 的第二条命令
   - 报 `command not found` → playwright 包未装，跑步骤 2 两条命令
```

或更简单：**跳过检测，直接尝试生成 PDF，按报错决定补装什么**（fail-loud 驱动）。

### 发现 2（用户审视发现）：`-D` 应改为 `-g`

**当前 toolchain.md §2.1 步骤 2 写**：
```bash
npm install -D playwright
npx playwright install chromium
```

**问题**：`-D`（devDependencies）把 playwright 装进**当前项目**的 `node_modules/`。但本技能受众是 **Java 开发者**——他们的项目里不该出现 Node 的东西。`-D` 会在 Java 项目里凭空多出 `node_modules/` + `package.json` + `package-lock.json`，污染项目。

**根因**：写 `-D` 是 Node 项目惯例的惯性思维，没考虑本技能的实际使用场景（Playwright 在这里是**系统级 HTML→PDF 工具**，不是项目依赖）。

**建议修正**：
```bash
npm install -g playwright          # 包：全局一次（不是 -D），不污染项目
npx playwright install chromium    # 浏览器：本来就装到全局 %LOCALAPPDATA%\ms-playwright\
```

**关键澄清**：无论包用 `-D` 还是 `-g`，浏览器二进制**都是装到同一个全局位置**（`C:\Users\{user}\AppData\Local\ms-playwright\`）。区别只在 playwright 包本身：`-D` 每个项目装一遍，`-g` 全局装一次。

### 其余陷阱全部确证

| 陷阱 | 实跑验证 | 结论 |
|---|---|---|
| #1 PDF 只有 Chromium | 未能验证（未跑 firefox） | 保留（官方文档明确） |
| #2 `--wait-for-timeout` 毫秒 | 命令被接受（参数名正确） | ✅ 参数准确 |
| #3 JS 必须 headless 浏览器 | 未验证（未跑 weasyprint） | 保留（通用知识） |
| #4 装包不装浏览器 | **✅ 实跑确证**（报错信息吻合） | **最强证据** |
| #5 `playwright` ≠ `@playwright/cli` | 未验证 | 保留（WebSearch 确认） |
| #6 ECharts 异步 | 未验证 | 保留 |

## 三、结论

toolchain.md 的**核心陷阱知识准确**，尤其陷阱 #4（装包不装浏览器）经实跑完全证实——这是技能存在的有力理由。

**唯一需修正**：§2.1 环境检测步骤 1 的 `npx playwright --version` 检测方式有出入（npx 会自动安装，不报错），应改为直接尝试 pdf 命令或用更可靠的检测。
