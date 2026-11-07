# 跨技能信号路由（using-agile 参考）

执行中冒出的信号走哪个入口、落哪个文件、谁有写权。字段定义与生命周期归 `agile-backlog/references/` 下对应 rules 文件；统计与对账跑 `agile.py`（stats / trend / report / check）。

## 一、信号 → 入口 → 落点

| 信号 | 入口 | 落点 |
|------|------|------|
| 需求探索的隐患信号、strategic 架构预判瓶颈、条目反复顺延、用户主动提出 | agile-backlog 风险管理入口 | `risks.json`（R-NNN，`risk-rules.md`） |
| 执行中发现缺陷 | agile-backlog 转条目（type=缺陷） | `backlog.json`（B-NNN，`backlog-rules.md`） |
| 需产品层裁决（feedback.decision / L3 变更裁决） | agile-backlog 决策记录入口 | `decisions.json`（D-NNN，`decision-rules.md`） |
| 组版本 / 发布登记 | agile-backlog 发布管理入口 | `releases.json`（`release-rules.md`） |
| feedback.reason | 不转条目 | agile-sprint 关闭环节已展示 |

## 二、写权归属

| 文件 | 写（唯一） | 读 |
|------|-----------|----|
| `backlog.json` | agile-backlog | agile-sprint 取条、agile.py |
| `risks.json` / `releases.json` / `decisions.json` | agile-backlog 对应入口 | agile-sprint（规划过风险 / 关闭提示路由）、agile.py |
| `sprints/*.md`、`*.done.yaml` | agile-sprint / 消费 Agent | 闭环链路 |
