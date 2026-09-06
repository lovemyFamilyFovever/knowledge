---
title: "RabbitMQ vs Kafka vs Pulsar"
tags: []
source: "baike"
source_path: "开发术语 / 消息与中间件"
collected: "2026-09-05"
status: "imported"
---

# 消息队列对比

| 特性 | RabbitMQ | Kafka | Pulsar |
|------|----------|-------|--------|
| 协议 | AMQP | 自定义 | 自定义 |
| 吞吐 | 万级 | 百万级 | 百万级 |
| 延迟 | 微秒级 | 毫秒级 | 毫秒级 |
| 消息模型 | 队列 | 发布/订阅 | 统一 |
| 持久化 | 可选 | 必须 | 必须 |
| 消费模式 | Push/Pull | Pull | Push/Pull |
| 事务 | 支持 | 支持 | 支持 |
| 延迟消息 | 插件 | 不支持 | 原生支持 |
| 多租户 | 不支持 | 不支持 | 原生支持 |
| 适用场景 | 业务解耦 | 大数据/日志 | 云原生 |

## 选型建议

- 业务消息/RPC：RabbitMQ
- 大数据/日志/流处理：Kafka
- 多租户/云原生/统一消息：Pulsar
