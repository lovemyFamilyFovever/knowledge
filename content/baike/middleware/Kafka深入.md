---
title: "Kafka深入"
tags: [消息与中间件, Kafka, 消息队列, 流处理]
source: "baike"
source_path: "开发术语 / 消息与中间件"
collected: "2026-09-05"
status: "imported"
---

# Kafka深入


> 📌 **导航**：本文是 **Kafka深入** 词条，属于 middleware 术语集。相关枢纽：[[ESB 与服务网格（Service Mesh）]]、[[GraphQL实践]]、[[Kafka深入]]、[[RabbitMQ vs Kafka vs Pulsar]]、[[gRPC深入]]。

## 定义

**一句话定义：** Kafka 是一个分布式、可持久化、可水平扩展的**流处理平台/消息系统**，以"分区日志（partitioned log）"为核心模型，具备高吞吐、可重放、生态完善的特点，广泛用于日志、事件流与数据管道。

**通俗类比：** Kafka 像一座超大的日志图书馆——消息按主题（Topic）分区（Partition）顺序存放、每条有页码（Offset）；多个读者（Consumer Group）可各自翻阅，读完也不撤架（可保留、可重放）。

> 多义说明：Kafka 既是消息队列（MQ），也是流平台（配合 Kafka Streams/Flink）；本文侧重其核心概念、可靠性语义与性能原理。消息队列通用概念见 [[消息队列（Message Queue）]]。

## 为什么需要它

传统 MQ 取完即删、吞吐与扩展有限，扛不住日志/事件流这种"海量、要持久、要多方重复消费、要重放回溯"的场景。Kafka 把数据组织成分区内追加、有序、不可变的日志：分区让读写并行横向扩展，持久化 + Offset 让多个消费组各读各的、可随时重放，成为事件流与数据管道的事实标准。

## 核心机制

- **分区日志模型：** 每个 Topic 分多个 Partition，分区内追加写、有序、不可变，用 Offset 定位；分区是并行与扩展的基本单位。

```
Producer -> Topic -> Partition(有序不可变) -> Consumer Group -> Consumer
```

| 概念 | 说明 |
|------|------|
| Topic | 消息的逻辑主题 |
| Partition | 分区，有序不可变，是并行单位 |
| Offset | 分区内消息的位移（消费进度） |
| Consumer Group | 消费组，组内分摊分区、组间各自独立 |
| Broker | Kafka 服务器节点 |
| Replica / ISR | 副本（Leader/Follower）/ 同步副本集合 |

- **副本与 ISR：** 每个分区有 Leader 与若干 Follower；ISR（In-Sync Replicas）是与 Leader 同步的副本集合，`acks=all` 时要求 ISR 全部确认才返回成功。
- **投递语义：** at-most-once / at-least-once / exactly-once，后者靠幂等生产者（`enable.idempotence=true`，PID + 序列号去重）与事务实现。
- **性能为何高：** 顺序写磁盘 + Page Cache、零拷贝（sendfile）、批量发送/拉取（batch.size、linger.ms）+ 压缩（lz4/zstd）、分区并行横向扩展。
- **架构演进：** 早期依赖 ZooKeeper 管元数据，KIP-500 引入 KRaft（内置 Raft 取代 ZooKeeper，Kafka 3.3+ 生产可用），简化部署并提升元数据可扩展性。

## 具体示例

Topic 有 3 个分区 (P0,P1,P2)、消费组有 2 个消费者：再平衡后 C1 消费 P0、P1，C2 消费 P2；若 C1 宕机触发 Rebalance，C2 接手全部三个分区。可见"组内消费者数 > 分区数"时多出的消费者会空闲——并行度上限由分区数决定。

## 何时用 / 何时不用

- **用：** 日志/指标聚合、事件溯源、流式处理（Kafka Streams/Flink）、数据管道（CDC 入湖入仓）、削峰填谷、系统解耦与异步。
- **不用：** 需要复杂路由/超低延迟的点对点任务（RabbitMQ 更灵活，见 [[RabbitMQ vs Kafka vs Pulsar]]）；要全局严格有序（须牺牲并行用单分区，代价大）。

## 优劣与代价

✅ 极高吞吐、持久化可重放、水平扩展、生态成熟（Connect/Streams/Schema Registry）。
⚠️ 只单分区有序、非全局有序；分区扩容后不可缩减且影响按 key 路由一致性。
⚠️ 副本/再平衡/磁盘运维有复杂度。

## 与相关概念的区别

- **vs 传统 MQ（RabbitMQ）：** Kafka 是持久化分区日志、重放强、吞吐高、路由相对简单；RabbitMQ 灵活路由、低延迟、消息取走即删。
- **vs [[消息队列（Message Queue）]]：** 通用队列概念在其词条，本文是 Kafka 的日志式实现细节。
- **顺序性：** 单分区有序；要"同一 key 有序"须按 key 路由到固定分区，全局有序则只能单分区。

## 常见误区

- Kafka 能保证所有消息在全局范围内严格有序。
- 在同一个消费者组里，消费者数量越多，消费就一定越快。
- 只要设置 acks=all，Kafka 就绝不会丢失任何消息。

## 面试速答

> 🎯 Kafka=分区日志式高吞吐消息平台：Topic 分 Partition（追加有序、Offset 定位），Consumer Group 分摊分区、可重放；可靠性靠 ISR+acks=all，exactly-once 靠幂等+事务。快在顺序写+Page Cache+零拷贝+批量压缩。坑：仅单分区有序，并行度=分区数。
> 🔍 追问：acks=all 为什么还要配 min.insync.replicas？
> 🔍 追问：Kafka 为什么吞吐这么高？
> 🔍 追问：怎么实现"同一用户消息有序"？

## 相关术语

[[消息队列（Message Queue）]]、[[RabbitMQ vs Kafka vs Pulsar]]、[[死信队列]]、[[幂等性]]、[[一致性算法]]

## 参考资料

建议人工核验：可参考 Apache Kafka 官方文档（设计、KIP-500/KRaft、Exactly-Once 语义）、《Kafka 权威指南》(Kafka: The Definitive Guide)；副本与一致性机制参见 [[一致性算法]]。
