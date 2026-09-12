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

**一句话定义：** Kafka 是一个分布式、可持久化、可水平扩展的**流处理平台/消息系统**，以「分区日志（partitioned log）」为核心模型，具备高吞吐、可重放、生态完善的特点，广泛用于日志、事件流与数据管道。

**通俗类比：** Kafka 像一座超大的日志图书馆——消息按主题（Topic）分区（Partition）顺序存放、每条有页码（Offset）；多个读者（Consumer Group）可各自翻阅，读完也不撤架（可保留、可重放）。

> 多义说明：Kafka 既是消息队列（MQ），也是流平台（配合 Kafka Streams/Flink）；本文侧重其核心概念、可靠性语义与性能原理。消息队列通用概念见 [[消息队列（Message Queue）]]。

## 原理与机制

- **分区日志模型**：每个 Topic 分为多个 Partition，分区内消息**追加写、有序、不可变**，用 Offset 定位；分区是并行与扩展的基本单位。
- **副本与 ISR**：每个分区有 Leader 与多个 Follower 副本；ISR（In-Sync Replicas）是与 Leader 保持同步的副本集合，`acks=all` 时要求 ISR 全部确认才返回成功。
- **消费与再平衡**：Consumer Group 内分区被组内消费者分摊；成员增减触发 **Rebalance**（再平衡）。
- **投递语义**：at-most-once / at-least-once / exactly-once；后者靠**幂等生产者**（`enable.idempotence=true`，PID + 序列号去重）与**事务**实现。

### 核心概念

```
Producer -> Topic -> Partition(分区，有序不可变) -> Consumer Group -> Consumer
```

| 概念 | 说明 |
|------|------|
| Topic | 消息的逻辑主题 |
| Partition | 分区，有序、不可变，是并行单位 |
| Offset | 分区内消息的位移（消费进度） |
| Consumer Group | 消费组，组内分摊分区、组间各自独立 |
| Broker | Kafka 服务器节点 |
| Replica / ISR | 副本（Leader/Follower）/ 同步副本集合 |

### 消费者组与分区分配

```
Topic 有 3 个分区(P0, P1, P2)，Consumer Group 有 2 个消费者
  → C1 消费 P0,P1；C2 消费 P2
若 C1 宕机 → 触发再平衡 → C2 消费 P0,P1,P2
（注意：同组内消费者数 > 分区数时，多出的消费者空闲）
```

### 性能为何高

- **顺序写磁盘** + **Page Cache**（利用操作系统页缓存，减少随机 I/O）。
- **零拷贝（sendfile）**：数据从页缓存直达网卡，避免用户态↔内核态多次拷贝。
- **批量发送/拉取**（`batch.size`、`linger.ms`）+ **压缩**（`compression.type=lz4/zstd`）。
- **分区并行**：多分区、多消费者横向扩展吞吐。

### 架构演进：KRaft

早期 Kafka 依赖 **ZooKeeper** 管理元数据与控制器选举；自 KIP-500 引入 **KRaft**（Kafka Raft）模式，用内置 Raft 取代 ZooKeeper（Kafka 3.3+ 起生产可用），简化部署并提升元数据操作的可扩展性。

## 应用场景

- 日志/指标聚合、事件溯源（event sourcing）、流式处理（Kafka Streams/Flink）、数据管道（CDC 入湖入仓）、削峰填谷、系统解耦与异步。

## 优点与局限

- 优点：极高吞吐、持久化与可重放、水平扩展、生态成熟（Connect/Streams/Schema Registry）。
- 局限：单分区有序而非全局有序；分区扩容后不可缩减、且影响按 key 路由的一致性；不适合超低延迟的复杂路由（RabbitMQ 更灵活）；副本/再平衡/磁盘运维有复杂度。

## 常见误区

- 「Kafka 保证全局有序」：只保证**单分区内**有序；要全局有序须用单分区（牺牲并行）或按 key 路由到同一分区。
- 「消费者越多越快」：同组内消费者数超过分区数时多余者空闲——并行度受分区数限制。
- 「`acks=all` 就绝不丢消息」：还需配合 `min.insync.replicas≥2` 与合理副本数，否则 ISR 收缩时仍可能丢。

## 相关术语

[[消息队列（Message Queue）]]、[[RabbitMQ vs Kafka vs Pulsar]]、[[死信队列]]、[[幂等性]]、[[一致性算法]]

## 参考资料

建议人工核验：可参考 Apache Kafka 官方文档（设计、KIP-500/KRaft、Exactly-Once 语义）、《Kafka 权威指南》(Kafka: The Definitive Guide)；副本与一致性机制参见 [[一致性算法]]。
