# 消息与事件：Pub/Sub、Stream、键空间通知

## 1. 选型表（先选模型）

| 需求 | 模型 | 边界 |
|---|---|---|
| 在线广播 / 事件通知（丢了可容忍） | **Pub/Sub**（§2） | 不持久化：发布瞬间无订阅者即丢，离线 / 重连窗口必丢 |
| 可靠队列（至少处理一次） | **Stream + 消费组**（§3） | 持久化 + ack + 掉线接管；堆积治理 / 重试策略弱于 MQ |
| 延迟 / 定时任务 | `RDelayedQueue`（`07-redisson.md` §7） | 需消费方常驻；可靠性弱于 MQ 延迟消息 |
| key 过期 / 删除回调 | 键空间通知（§4） | 时延不准、不持久，只做辅助联动 |
| 跨服务异步解耦主链路 | MQ（RocketMQ / Kafka） | Redis 消息是轻量替代，不是 MQ 竞品——规模上去就换 |

## 2. Pub/Sub

```java
@Bean
RedisMessageListenerContainer redisMessageListenerContainer(RedisConnectionFactory factory,
        MessageListenerAdapter chatListener) {
    RedisMessageListenerContainer container = new RedisMessageListenerContainer();
    container.setConnectionFactory(factory);
    container.addMessageListener(chatListener, new ChannelTopic("chat:room:1001"));
    // 模式订阅：new PatternTopic("chat:room:*")
    return container;
}

@Bean
MessageListenerAdapter chatListener(ChatSubscriber subscriber) {   // 订阅逻辑委托给普通 bean 的方法
    return new MessageListenerAdapter(subscriber, "onMessage");
}

// 发布端
stringRedisTemplate.convertAndSend("chat:room:1001", "hello");
```

- `ChannelTopic` 精确频道（SUBSCRIBE）；`PatternTopic` 通配（PSUBSCRIBE）。
- **坑 1（必丢设计）**：消息不落盘、无堆积——发布时订阅者不在线（掉线重连中、消费端刚重启）就永久丢。要求不丢 → Stream（§3）。
- **坑 2**：订阅走**专用连接**（Lettuce 共享连接不用于订阅），订阅数与频道数计入连接规划（`02-pool.md` §1）。
- 集群模式：经典 `PUBLISH` 在集群内自动广播到所有节点，订阅任一节点即可收到；Redis 7+ 的 sharded pub/sub（`SSUBSCRIBE`）不跨节点广播、省带宽，但订阅端要连对节点。

## 3. Stream（可靠队列）

生产端（`add` 返回消息 id）：

```java
RecordId id = stringRedisTemplate.opsForStream()
        .add("stream:order-events", Map.of("orderId", "1001", "type", "PAID"));
```

持续消费（消费组 + 手动 ack，`StreamMessageListenerContainer`）：

```java
StreamMessageListenerContainerOptions<String, MapRecord<String, String, String>> options =
        StreamMessageListenerContainerOptions.builder()
                .pollTimeout(Duration.ofMillis(100))     // 无消息时的轮询间隔
                .build();

StreamMessageListenerContainer<String, MapRecord<String, String, String>> container =
        StreamMessageListenerContainer.create(redisConnectionFactory, options);

container.receive(                                                         // receiveAutoAck = 收到即 ack
        Consumer.from("order-group", "consumer-1"),
        StreamOffset.create("stream:order-events", ReadOffset.lastConsumed()),
        msg -> {
            handle(msg);                                                   // 业务处理
            stringRedisTemplate.opsForStream()
                    .acknowledge("stream:order-events", "order-group", msg.getId());
        });
container.start();                                                         // 别忘了
```

必知语义与坑：

1. **消费组初始化**：向不存在的 stream 建组会报错（Redis 要求 stream 已存在；`XGROUP CREATE` 的 `MKSTREAM` 选项可顺带建空流——确认所用 API / 版本是否传了它，不确定就先 `add` 一条占位消息再建组）。
2. **处理完必须 ack**：未 ack 的消息留在 PEL（Pending Entries List）——忘 ack → PEL 无限增长 + 重复消费隐患。`receiveAutoAck` 是"收到即 ack"，处理抛异常**不会**重投——至少一次语义要手动 ack。
3. **掉线接管**：消费者宕机后，其 PEL 消息要由其他消费者接管（`XAUTOCLAIM` 按 min-idle-time 判闲置；Java 侧 `opsForStream().pending() / claim()`）——不做接管，掉线消费者的消息永远 pending。
4. **长度控制**：大流量必须修剪（`XADD` 带 `MAXLEN ~ N` 近似修剪，或定期 `XTRIM`）——stream 只增不减会吃满内存。
5. **没有内建死信 / 重试策略**：消费失败 N 次转死信要自己做（记失败计数，超限挪死信 stream）；要现成的 → MQ。
6. 容器持续轮询占用一条专用连接，连接语义同 `02-pool.md` §1 的阻塞命令。

## 4. 键空间通知（keyspace notifications）

key 的过期 / 删除 / 修改事件通过 Pub/Sub 广播，应用侧可订阅。**默认关闭**——需要服务器配置 `notify-keyspace-events`（如 `Ex` = 过期事件）——少数必须运维配合改配置的应用侧功能。

```java
@Bean
public KeyExpirationEventMessageListener keyExpiredListener(
        RedisMessageListenerContainer container) {          // 复用 §2 的容器或另建
    return new KeyExpirationEventMessageListener(container) {
        @Override
        public void onMessage(Message message, byte[] pattern) {
            String expiredKey = message.toString();          // 消息体就是 key 名
        }
    };
}
```

坑（决定了它的定位是"辅助联动"，不是可靠机制）：

1. **过期事件不准时**：由惰性 / 定期删除触发（同 `08-troubleshoot.md` 总表"TTL 到期的 key 还在"一行的机制）——实际触发可能晚很多。
2. **不持久化**：监听端重启窗口内的事件永久丢。
3. **订单超时关闭别押它**——用 `RDelayedQueue` / 定时扫描兜底（选型表 §1）；它适合缓存失效联动、本地缓存失效通知这类"丢了也没事"的场景。

## 5. 自检

- [ ] 消息模型按选型表选过：可丢 → Pub/Sub；不可丢 → Stream / MQ
- [ ] Stream 消费是消费组 + 手动 ack，且有 PEL 掉线接管与长度修剪方案
- [ ] 键空间通知只用于可容忍丢失的联动场景，服务器配置已确认开启
