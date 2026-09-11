---
title: "消息队列（Message Queue）"
tags: [消息与中间件, 消息队列, Kafka, RabbitMQ]
source: "baike"
source_path: "开发术语 / 消息与中间件"
collected: "2026-09-05"
status: "imported"
---

# 消息队列（Message Queue）

> 📌 **导航**：本文是消息队列的**总览与选型 hub**（核心概念 + Kafka/RabbitMQ/RocketMQ/Pulsar + 可靠性/顺序/幂等）。其中 Kafka 深入见 [[Kafka深入]]，三者选型对比见 [[RabbitMQ vs Kafka vs Pulsar]]，死信见 [[死信队列]]，幂等见 [[幂等性]]，事务消息见 [[分布式事务]]。

## 消息队列核心概念

### 一句话定义
消息队列是一种**异步通信机制**，让生产者和消费者通过中间的"邮箱"来传递数据，双方不需要同时在线。

### 通俗类比
就像你寄快递：你把包裹放到快递柜（Broker），快递员不用在场就能取走配送（消费）。快递柜就是消息队列，你就是生产者，快递员就是消费者。

### 具体示例

```
Producer ──> Broker (Topic/Queue) ──> Consumer

生产者：订单系统发送"新订单"消息
Broker：Kafka/RabbitMQ/RocketMQ
消费者：库存系统、物流系统、通知系统
```

### 为什么需要它
- **解耦**：系统之间不直接依赖，改一个不影响另一个
- **削峰**：秒杀时大量请求先排队，系统按能力消费
- **异步**：用户下单后不用等库存扣减完成才返回

### 与相关术语的对比

| 概念 | 说明 |
|------|------|
| Topic | 消息的逻辑分类，如"订单"、"支付" |
| Queue | 物理队列，Topic的具体实现 |
| Partition | 分区，用于并行处理，提高吞吐量 |
| Offset | 消费位点，记录消费者读到第几条消息 |

---

## Kafka

### 一句话定义
Kafka 是一个**分布式流处理平台**，以高吞吐、持久化、水平扩展著称，适合大数据场景。

### 通俗类比
像一个超大的日志图书馆：所有书籍（消息）按类别（Topic）分区（Partition）存放，每本书有页码（Offset），多个管理员（Consumer Group）可以同时整理不同区域的书。

### 具体示例

```bash
# 创建Topic
kafka-topics.sh --create --topic order-events --partitions 6 --replication-factor 3

# 发送消息
kafka-console-producer.sh --topic order-events --broker-list localhost:9092

# 消费消息
kafka-console-consumer.sh --topic order-events --group order-service --from-beginning
```

### 核心架构

```
┌─────────────────────────────────────────────┐
│              Kafka Cluster                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Broker 0 │  │ Broker 1 │  │ Broker 2 │  │
│  │ P0(P)    │  │ P1(P)    │  │ P2(P)    │  │
│  │ P1(R)    │  │ P2(R)    │  │ P0(R)    │  │
│  │ P2(F)    │  │ P0(F)    │  │ P1(F)    │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
         │                │
    ┌────┴────┐      ┌────┴────┐
    │Consumer │      │Consumer │
    │Group A  │      │Group B  │
    │(订单服务)│      │(支付服务)│
    └─────────┘      └─────────┘
```

### Consumer Group 与 Offset 管理

| 特性 | 说明 |
|------|------|
| Consumer Group | 同一组内消费者分担消费，不同组各自独立消费 |
| Offset 提交 | 自动提交（auto.commit）或手动提交 |
| Offset 存储 | Kafka 0.8+ 存在内部 topic `__consumer_offsets` |
| Exactly-Once | 通过幂等生产者 + 事务实现 |

---

## RabbitMQ

### 一句话定义
RabbitMQ 是基于 **AMQP 协议**的消息中间件，灵活性高，支持多种消息路由策略。

### 通俗类比
像一个智能邮局：你寄信时可以选择"精准投递"（Direct）、"广播通知"（Fanout）、"关键词匹配"（Topic）等不同方式。

### 具体示例

```python
# Python - 使用 pika 连接 RabbitMQ
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# 声明交换机和队列
channel.exchange_declare(exchange='order_direct', exchange_type='direct')
channel.queue_declare(queue='order_queue', durable=True)
channel.queue_bind(exchange='order_direct', queue='order_queue', routing_key='order.new')

# 发送消息
channel.basic_publish(exchange='order_direct', routing_key='order.new', body='New order #12345')
```

### Exchange 类型对比

| 类型 | 路由规则 | 典型场景 |
|------|----------|----------|
| Direct | 精确匹配 routing_key | 订单系统按事件类型分发 |
| Fanout | 广播到所有绑定队列 | 日志同时发给多个处理系统 |
| Topic | 通配符匹配（*.log、#.error） | 按模块+级别过滤日志 |
| Headers | 按消息头属性匹配 | 复杂条件路由 |

### ACK 与 NACK 机制

```
消费者处理成功 → ACK → Broker删除消息
消费者处理失败 → NACK → 消息重新入队/进入死信队列
消费者拒绝 → reject → 消息重试或丢弃
```

---

## RocketMQ

### 一句话定义
RocketMQ 是**阿里开源**的分布式消息中间件，在电商场景经过大规模验证，支持事务消息和延迟消息。

### 通俗类比
像一个功能齐全的物流中心：不仅有普通快递通道，还有"到付件"（事务消息）、"定时达"（延迟消息）、"顺序件"（顺序消息）等特殊服务。

### 核心架构

```
┌─────────────────────────────────────────┐
│            RocketMQ Cluster              │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │         NameServer Cluster       │   │
│  │   (轻量级，节点间无通信)          │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌────────────┐    ┌────────────┐       │
│  │ Broker-M   │    │ Broker-S   │       │
│  │ (Master)   │───▶│ (Slave)    │       │
│  │ Topic-A    │    │ Topic-A    │       │
│  │ Topic-B    │    │ Topic-B    │       │
│  └────────────┘    └────────────┘       │
└─────────────────────────────────────────┘
```

### 特色功能

| 功能 | 说明 |
|------|------|
| 事务消息 | 半消息 + 本地事务 + 回查机制，实现分布式事务最终一致性 |
| 延迟消息 | 18个延迟级别（1s/5s/10s/30s/1m/2m/...），到期自动投递 |
| 顺序消息 | 同一 Queue 内 FIFO，适合订单状态流转 |

---

## Pulsar

### 一句话定义
Pulsar 是**下一代云原生消息系统**，采用计算存储分离架构，支持多租户和分层存储。

### 通俗类比
像一个弹性云仓库：货架（BookKeeper）和门市（Broker）分开，货物少时自动收缩，多时自动扩展，不同租户有独立的存储空间。

### 核心优势

| 特性 | 说明 |
|------|------|
| 分层存储 | 热数据在 BookKeeper，冷数据自动下沉到 S3/HDFS |
| 多租户 | 原生支持 namespace、tenant 级别的隔离 |
| 事务消息 | 支持 exactly-once 语义 |
| 跨地域复制 | Geo-Replication 天然支持多数据中心 |

---

## 消息模式

### 发布订阅 vs 点对点

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| 发布订阅 | 多个消费者各自收到完整消息 | 事件通知、日志分发 |
| 点对点 | 消息只被一个消费者消费 | 任务分发、负载均衡 |
| 请求应答 | 发送请求后同步等待响应 | RPC 调用 |

---

## 消息可靠性

### 一句话定义
消息可靠性确保消息**不丢失、不重复、不乱序**，是分布式系统的核心挑战。

### 可靠性保障措施

```
生产端 → Broker → 消费端
  │         │         │
  ▼         ▼         ▼
发送确认   持久化    ACK确认
(ACK)    (WAL/磁盘)  (手动提交)
重试机制   副本同步   重试/死信
```

| 环节 | 机制 |
|------|------|
| 生产端 | 发送失败重试 + 本地缓存 |
| Broker 端 | 同步刷盘 + 多副本 |
| 消费端 | 手动 ACK + 失败重试 + 死信队列 |
| 消息幂等 | 唯一消息ID + 去重表 |

---

## Kafka vs RabbitMQ 对比

| 维度 | Kafka | RabbitMQ |
|------|-------|----------|
| 模型 | 分布式日志 | 消息代理 |
| 吞吐量 | 百万级/秒 | 万级/秒 |
| 消息延迟 | 毫秒级 | 微秒级 |
| 消息持久化 | 天然持久化 | 可选 |
| 消息顺序 | 分区级有序 | 队列级有序 |
| 协议 | 自有协议 | AMQP/STOMP/MQTT |
| 适用场景 | 大数据流、日志、事件溯源 | 业务消息、复杂路由、RPC |
| 运维复杂度 | 中等 | 较低 |
| 消费模型 | 拉取（Pull） | 推送（Push） |

---

## 消息顺序性

### 一句话定义
消息顺序性保证消息按照**发送顺序被消费**，在分布式环境中是重要但有代价的特性。

### 实现方式

| 方案 | 优点 | 缺点 |
|------|------|------|
| 单分区/单队列 | 简单可靠 | 吞吐量受限 |
| 分区键路由 | 同键有序，兼顾吞吐 | 不同键间无序 |
| 全局顺序 | 完全有序 | 性能极差，不推荐 |

---

## 消息幂等性

### 一句话定义
消息幂等性保证**同一条消息被消费多次，结果与消费一次相同**。

### 常见实现

```java
// 唯一消息ID + 去重表
public void handleMessage(Message msg) {
    if (redis.setnx("msg:" + msg.getId(), "1", 24, TimeUnit.HOURS)) {
        process(msg);
    } else {
        log.warn("重复消息，跳过: {}", msg.getId());
    }
}
```

---

## 相关术语

[[Kafka深入]]、[[RabbitMQ vs Kafka vs Pulsar]]、[[死信队列]]、[[幂等性]]、[[分布式事务]]、[[任务调度（Task Scheduling）]]

## 参考资料

建议人工核验：可参考 Apache Kafka / RabbitMQ / Apache RocketMQ / Apache Pulsar 官方文档、《企业集成模式》(EIP, Hohpe & Woolf)，以及 AMQP 规范。
