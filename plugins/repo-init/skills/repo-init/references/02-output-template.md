# 02 · 输出模板

> 行数护栏：标准模式**目标 ≤150 行、硬上限 ≤200 行**；超过 150 行先自查能否合并冗余段（如 Architecture 与 Overview 重叠、多个 gotcha 合并为一条）。"≤200 行"是 Claude Code 实践参考（非官方硬限）。section 主标题建议英文（工具解析更稳）。

## 标准模式（目标 ≤150 / 上限 ≤200 行）

各 section 写法要点已内联为注释，按实际项目替换占位内容：

```markdown
# AGENTS.md

## Project overview
（2-4 句：这是什么、解决什么、技术栈一句话。不写"高性能、可扩展"等营销词。）

## Setup commands
- Install: `<从构建文件真实提取，禁止臆造>`
- Dev / Build / Test: `<真实命令，复制即可跑>`
（包管理器与实际 lock 文件一致；命令不真实就标「需核实」。）

## Code style
- 只写团队实际遵守的；CI 强制项优先，不写理想规则（如"禁止 any"但团队从不执行）。
- 格式化 / 命名 / 提交规范 / 错误处理（如"禁止吞异常"）。

## Architecture
（讲"为什么这么分"与模块间数据流，不列文件树——AI 能自己 Glob。）

## Hard constraints
（不可违背的红线，违反即 bug 或安全事故；每条独立一行。命中 i18n 信号 → 禁硬编码文案，见 `01` §7。）

## Security considerations
（认证/鉴权/支付/加密/数据合规等**安全敏感项目始终单列此段**，不并入 Hard constraints；
记录权限边界、密钥处理、注入防护、审计要求。安全信号几乎总是真实存在，即使小项目也保留。）

## Known gotchas
（老手才知道的坑，是 AGENTS.md 区别于 README 的高价值部分。如环境变量注入方式，见 `01` §6。）

## Testing instructions
（单测命令 + 覆盖率门槛，从 CI 配置提取，不凭印象。）

## PR instructions
（分支策略 + CI 门禁，从 CONTRIBUTING.md 提取。）
```

## 可选 · 超简骨架（小项目参考，非强制模式）

小项目可只保留 must-know（命令 + 关键约束），省略无信号段；非触发式，按需采用：

```markdown
# AGENTS.md

## Project overview
（2-3 句：这是什么、技术栈一句话）

## Setup commands
- Run: `node index.js`（或 `python main.py` / `./main`）
- Test: `<若有，无则省略>`

## Code style
- <1-2 条不可违背约定，如"纯函数优先 / 输入须校验">

## Hard constraints
- <红线如"不提交凭证"；无则省略>
```
