# agile 插件回归

仓库级测试，不随插件分发——marketplace 的 `source` 指向整个 `plugins/agile/`
目录、安装时整目录拷贝，所以测试放仓库侧。四套 shell 回归与工作包 unittest，只依赖
POSIX sh + Python（3.9+，标准库 only）。改 `plugins/agile/scripts/agile.py`、`plugins/agile/scripts/delivery.py`、
`plugins/agile/hooks/hooks.json` 或 `skills/using-agile/references/turn-brief.md`
之后跑全套（解释器叫 python3 的环境前置 `PY=python3`）：

| 脚本 | 覆盖 | 条数 |
|---|---|---|
| `stage.sh` | 七阶段 + 池耗尽边界，每阶段独立 fixture，断言注入的是对应 brief 块 | 10 |
| `suite.sh` | hook-prompt 行为矩阵（规划词 / 静默 / no-agile / 去重 / 状态行有界 / 长期待办同日一次 / 活跃 Sprint 排除）+ hooks.json 命令串按宿主形态直跑（sh 与 cmd `/d /s /c` verbatim，防 `args` 形态在 ZCode 复发；坏 json 断言 `decision:block`，写坏 Sprint 状态词断言 `additionalContext`） | 30 |
| `regress.sh` | agile.py 历史真实 bug 逐条回归（两位数序号 / 布尔点数 / 退出码 / 遗留 md 只提示不判错 / 键值行取最早冒号 / 已关闭 Sprint 判定与状态行渲染 / 状态三态 / 裸键值 / 命名混用排序 / 未知状态显式标注 / Sprint 头校验不依赖 backlog / 长期待办固定日期与复核边界 / Sprint 归档：archive 不进任何扫描、曾纳入只剩 planned_sprints 戳记、移动改指纹强制重算、迟到回填仍判 backfill） | 47 |
| `cache.sh` | 长期待办日缓存专项：首算一次后续命中、负缓存、跨日重算、mtime 指纹失效（内容不变也重算）、reviewed_at 更新、外部改写、损坏 / 版本不符降级自愈、marker `O_CREAT\|O_EXCL` 原子领取（线程 + 进程并发唯一展开）、no-agile 不留痕、SessionStart 暖缓存不领额度、PostToolUse 主动失效但不删 marker、review/stats 永远读实时文件 | 32 |

工作包回归：`python -B tests/agile/test_delivery.py`，所有读写均在临时中枢，前后端目录仅作不应被改动的哨兵；覆盖共同设计保留、按执行者裁剪、依赖与验收、幂等、版本失效、路径越界、锁与提前关轮拦截，不运行真实业务应用或外部执行器。

解释器矩阵：`python -B tests/agile/test_launchers.py`，Linux 上隔离 PATH，只放指定的 python/python3 启动器，直接执行 hooks.json 命令串；验证单名称、双名称、都缺失、启动失败回退、业务校验不重复运行。Windows 本地跳过此矩阵，cmd 宿主兼容由 suite.sh 覆盖。

GitHub Actions 的 agile-regression 在 Ubuntu / Python 3.9、3.12 运行上述全部回归，设置 `PYTHONIOENCODING=utf-8`、`PYTHONDONTWRITEBYTECODE=1` 与 `AGILE_REQUIRE_SYMLINK=1`；后者使真实符号链接无法建立时直接失败，不允许跳过。工作流监听 main、`ci/agile-*` 测试分支与相关 PR。

- 阶段判定顺序、判据与 brief 块的对应关系真源在
  `skills/using-agile/references/turn-brief.md` 的阶段表；增删阶段要同步改
  `agile.py` 与本目录（表自己也会这么提醒你）。
- `ab/` 是注入文案 AB 实测的 fixture 生成器；结论与方法论见 `ab-notes.md`，
  **改 brief 文案后按它复验**——注入的作用域严格等于写下的那句话。
- cmd 宿主形态用例走 node 按宿主同款 spawn 复刻（命令串过环境变量，避开
  MSYS 对内层引号的转义）；无 node 或非 Windows 自动跳过。
