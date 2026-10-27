# agile 插件回归

仓库级测试，不随插件分发——marketplace 的 `source` 指向整个 `plugins/agile/`
目录、安装时整目录拷贝，所以测试放仓库侧。三套互相独立的脚本，只依赖
POSIX sh + Python（3.9+，标准库 only）。改 `plugins/agile/scripts/agile.py`、
`plugins/agile/hooks/hooks.json` 或 `skills/using-agile/references/turn-brief.md`
之后跑全套（解释器叫 python3 的环境前置 `PY=python3`）：

| 脚本 | 覆盖 | 条数 |
|---|---|---|
| `stage.sh` | 七阶段 + 池耗尽边界，每阶段独立 fixture，断言注入的是对应 brief 块 | 10 |
| `suite.sh` | hook-prompt 行为矩阵（规划词 / 静默 / no-agile / 去重 / 状态行有界）+ hooks.json 命令串按宿主形态直跑（sh 与 cmd `/d /s /c` verbatim，防 `args` 形态在 ZCode 复发；坏 json 断言 `decision:block`，写坏 Sprint 状态词断言 `additionalContext`） | 23 |
| `regress.sh` | agile.py 历史真实 bug 逐条回归（两位数序号 / 布尔点数 / 退出码 / 遗留 md 只提示不判错 / 键值行取最早冒号 / 已关闭 Sprint 判定与状态行渲染 / 状态三态 / 裸键值 / 命名混用排序 / 未知状态显式标注 / Sprint 头校验不依赖 backlog） | 32 |

- 阶段判定顺序、判据与 brief 块的对应关系真源在
  `skills/using-agile/references/turn-brief.md` 的阶段表；增删阶段要同步改
  `agile.py` 与本目录（表自己也会这么提醒你）。
- `ab/` 是注入文案 AB 实测的 fixture 生成器；结论与方法论见 `ab-notes.md`，
  **改 brief 文案后按它复验**——注入的作用域严格等于写下的那句话。
- cmd 宿主形态用例走 node 按宿主同款 spawn 复刻（命令串过环境变量，避开
  MSYS 对内层引号的转义）；无 node 或非 Windows 自动跳过。
