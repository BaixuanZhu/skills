# 变更传播矩阵（using-agile §6 变更协调参考）

## 一、变更 → 影响面

| 改动源 | 影响面（须同步检查） |
|----------|---------------------------|
| 改 VISION（核心原则/红线） | PRODUCT-BACKLOG 排序逻辑、现有任务归属、对齐检查基准 |
| 改 ARCHITECTURE | 关联 ADR、Sprint 技术任务、架构瓶颈条目 |
| 改 ADR（技术选型） | 关联 PRODUCT-BACKLOG 任务、Sprint 技术任务、ARCHITECTURE 图 |
| 改 PRODUCT-BACKLOG 任务 | 所在 Sprint 规划、`PRODUCT-BACKLOG.yaml`（同步 id/priority/status） |
| 加新任务到 Backlog（Sprint 执行中） | 对当前 Sprint 无直接影响（进 Backlog 池等待下个 Sprint 取用），需校验与 VISION/ADR 的对齐 | agile-backlog（不进入 agile-sprint 规划区） |
| 关 Sprint | `PRODUCT-BACKLOG.yaml`（相关条目 status 更新）、`PRODUCT-BACKLOG.md` 表格 |
| 改 DoD | Sprint 出口检查、已完成条目复核 |

## 二、处理原则

- 影响面**先列后改**，不静默全量重写。
- 变更尽量小步、可逆；ADR 走替代而非篡改。
- 改完后回到 using-agile 做状态检测，确认无遗漏。
