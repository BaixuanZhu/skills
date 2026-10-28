# 决策展开（D1–D5）

## §0 前置：接受 at-least-once

RabbitMQ 的投递语义是 at-least-once。exactly-once 是应用层幂等造出来的效果，不是 broker 给的。
所有决策都建立在这个前提上。

## §1 D1 可靠性级别：丢了会怎样

| 级别 | 场景 | 配置 |
|---|---|---|
| 可丢 | 监控埋点、点击流 | 不开 confirm，AUTO ack |
| 尽力而为 | 一般业务事件 | confirm + persistent + AUTO ack |
| 不可丢 | 订单、支付、状态变更 | confirm + persistent + 手动 ack + DLQ 告警 |

**默认取「不可丢」。** 宁可多配，不要丢消息。

checklist（不可丢级别全勾）：

- [ ] `publisher-confirm-type: correlated` + ConfirmCallback 处理 nack
- [ ] `publisher-returns: true` + `template.mandatory: true` + ReturnsCallback
- [ ] 队列 durable、消息 persistent
- [ ] 消费端 ack 策略明确（AUTO + 幂等，或 MANUAL）
- [ ] DLQ 有消费者或告警

## §2 D2 幂等策略：处理两次会怎样

按副作用类型选策略：

| 副作用类型 | 例子 | 策略 |
|---|---|---|
| 覆盖型（set） | 更新状态、写快照 | upsert 天然幂等，可不额外去重 |
| 累加型（increment） | 加比分、加积分、计数器 | **必须去重**：DB 唯一键 / sequenceNo 状态机 |
| 副作用型（side-effect） | 发通知、调 HTTP、扣款 | **必须去重**：去重表 + 业务唯一键，或下游书面约定去重键 |

去重位置：

- **消费端去重**（推荐）：业务唯一键 + DB 唯一索引 / Redis setnx / 状态机
- **下游去重**：必须书面约定去重键和语义，不能只写注释「下游自行去重」

⚠️ **累加型操作的 upsert 不是幂等**——select 然后 score+1 再 update，重复投递会翻倍。
唯一可靠的累加幂等：先按业务唯一键去重，去重成功才累加。

业务写操作的重复到达语义（返回上次结果、不抛异常）见 java-contract「重复到达」条目。

## §3 D3 重试与死信：失败了去哪

基础配置（模型本能全对）：有限重试 + 指数退避、`default-requeue-rejected: false`、DLX + DLQ 拓扑。

**真正的缺口：DLQ 必须有人管。** 消息进死信不是终点，是静默消失的起点。三选一：

1. **DLQ 消费者**：告警 / 人工处理 / 补偿重试
2. **DLQ 告警**：队列深度 > 0 时通知
3. **定期巡检**：定时查 DLQ 长度

不配 DLQ 监控 = 不如不配 DLQ——不配至少会阻塞队列被人发现。

## §4 D4 顺序保障：要顺序吗

先问：这些消息**真的**需要按顺序吗？

- 状态机流转（KICKOFF → GOAL → FULL_TIME）→ 要
- 独立通知、埋点 → 不要

要顺序时，三选一：

1. **单队列单消费者**：最简单，吞吐受限
2. **按业务键分片 + `x-single-active-consumer`**：同一业务键进同一队列，多队列并行
3. **应用层序号状态机**：sequenceNo + lastApplied，重复跳过、缺口报警

分片参考：`matchId % shardCount` 路由到分片队列，队列开 `x-single-active-consumer`，
容器 `concurrentConsumers = 1`。

⚠️ prefetch > 1 时，重投的消息可能与后续消息交错。要顺序就把 prefetch 设小（1~10）。

## §5 D5 积压预案：生产快过消费怎么办

三个杠杆：

1. **prefetch**：按「单条消费耗时 × 期望吞吐」定。太小吞吐上不去，太大撑爆消费者内存
2. **并行度**：分片数 > 同队列消费者数（同队列多消费者会破坏顺序）
3. **降级**：积压超阈值时丢弃低优先级消息 / 切换到批量模式

**必须有积压监控**：队列深度告警阈值（如 > 10000 条持续 5 分钟）+ 消费速率 vs 生产速率。
不监控 = 积压 10 万条才被用户投诉发现。
