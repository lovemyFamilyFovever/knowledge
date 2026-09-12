---
title: "RabbitMQ vs Kafka vs Pulsar"
tags: [消息与中间件, 消息队列, Kafka, RabbitMQ]
source: "baike"
source_path: "开发术语 / 消息与中间件"
collected: "2026-09-05"
status: "imported"
---

# RabbitMQ vs Kafka vs Pulsar


> 📌 **导航**：本文是 **RabbitMQ vs Kafka vs Pulsar** 词条，属于 middleware 术语集。相关枢纽：[[ESB 与服务网格（Service Mesh）]]、[[GraphQL实践]]、[[Kafka深入]]、[[RabbitMQ vs Kafka vs Pulsar]]、[[gRPC深入]]。

## 定义

**一句话定义：** 本文对比三款主流消息/流处理系统——RabbitMQ（灵活路由的消息代理）、Kafka（高吞吐的分布式日志/流平台）、Pulsar（计算存储分离的云原生统一消息系统），帮助按场景选型。

**通俗类比：** 三者都像「快递系统」但定位不同：RabbitMQ 是**智能邮局**（按地址灵活投递）、Kafka 是**超大日志仓库**（顺序存取、可回溯、吞吐极高）、Pulsar 是**云原生弹性仓库**（库房与门店分离、多租户、按需伸缩）。

> 多义说明：三者边界在融合（RabbitMQ 加了流插件，Kafka/Pulsar 也支持队列语义），本文按各自**典型定位**对比；消息队列通用概念见 [[消息队列（Message Queue）]]，Kafka 细节见 [[Kafka深入]]。

## 三者简介

- **RabbitMQ**：基于 AMQP、Erlang 编写；以 Exchange（Direct/Fanout/Topic/Headers）实现灵活路由，延迟低，适合业务消息与复杂路由。
- **Kafka**：分布式分区日志；高吞吐、可持久化与重放，适合日志、事件流、大数据管道（详见 [[Kafka深入]]）。
- **Pulsar**：Apache 顶级项目（源自 Yahoo）；**计算（Broker）与存储（BookKeeper）分离**，原生多租户、分层存储、跨地域复制，统一「队列 + 流」。

## 对比

| 特性 | RabbitMQ | Kafka | Pulsar |
|------|----------|-------|--------|
| 核心模型 | 消息代理（队列/交换机） | 分布式分区日志 | 计算存储分离的统一消息 |
| 协议 | AMQP/STOMP/MQTT | 自有协议 | 自有协议（兼容多 API） |
| 吞吐 | 万级/秒 | 百万级/秒 | 百万级/秒 |
| 延迟 | 低（微秒~毫秒） | 毫秒级 | 毫秒级 |
| 消费模式 | Push/Pull | Pull | Push/Pull |
| 消息顺序 | 队列级有序 | 分区级有序 | 分区级有序 |
| 持久化/重放 | 可选，重放弱 | 天然持久化、可重放 | 天然持久化、可重放 |
| 延迟消息 | 插件支持 | 原生不支持 | 原生支持 |
| 多租户 | 弱（vhost） | 弱 | 原生（tenant/namespace） |
| 存储扩展 | 与计算耦合 | 与计算耦合（分区） | 存储独立扩展（BookKeeper） |
| 适用场景 | 业务解耦、复杂路由、RPC | 大数据/日志/流处理 | 云原生、多租户、统一消息 |

> 说明：吞吐/延迟为**量级参考**，实际取决于硬件、配置与消息大小。「Kafka 不支持延迟消息」指原生（可借外部方案实现），Pulsar/RocketMQ 原生支持。

## 选型建议

- **业务消息 / 复杂路由 / RPC / 灵活投递**：RabbitMQ。
- **大数据 / 日志 / 事件流 / 流处理 / 需重放**：Kafka。
- **云原生 / 多租户 / 存算分离 / 队列与流统一 / 跨地域**：Pulsar。

## 优点与局限

- **RabbitMQ**：路由灵活、延迟低、易上手；但吞吐与消息堆积能力弱于 Kafka/Pulsar，历史消息重放能力有限。
- **Kafka**：吞吐与生态最强、可重放；但延迟消息/多租户弱，分区与再平衡有运维复杂度。
- **Pulsar**：架构先进（存算分离、多租户、分层存储）；但生态与运维经验相对年轻，组件（Broker + BookKeeper + ZooKeeper）更多。

## 常见误区

- 「谁一定更好」：三者定位不同，应按**吞吐/延迟/路由/多租户/重放**等需求选型，而非一概而论。
- 把 Kafka 当普通队列用（频繁删已消费消息、追求单条超低延迟）：Kafka 强项是高吞吐日志与重放，此类场景 RabbitMQ 更合适。
- 忽视运维成本：Pulsar 组件多、Kafka 分区/副本调优、RabbitMQ 镜像队列各有门槛。

## 相关术语

[[消息队列（Message Queue）]]、[[Kafka深入]]、[[死信队列]]、[[任务调度（Task Scheduling）]]、[[幂等性]]

## 参考资料

建议人工核验：可参考 RabbitMQ、Apache Kafka、Apache Pulsar 三者官方文档与基准测试；实际选型以自身场景压测为准。
