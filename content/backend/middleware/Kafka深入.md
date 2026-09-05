---
title: "Kafka深入"
tags: []
source: "baike"
source_path: "开发术语 / 消息与中间件"
collected: "2026-09-05"
status: "imported"
---

# Kafka深入

## 核心概念

```
Producer -> Topic -> Partition(分区) -> Consumer Group -> Consumer
```

| 概念 | 说明 |
|------|------|
| Topic | 消息主题 |
| Partition | 分区，有序，不可变 |
| Offset | 消费位移 |
| Consumer Group | 消费组，组内竞争消费 |
| Broker | Kafka服务器节点 |
| Replica | 副本，Leader/Follower |

## 消费者组

```
Topic有3个分区(P0, P1, P2)
Consumer Group有2个消费者
-> C1消费P0,P1  C2消费P2
如果C1挂了 -> C2消费P0,P1,P2(再平衡)
```

## Exactly-Once语义

```
Producer: 幂等(enable.idempotence=true) + 事务
Consumer: 手动提交offset + 幂等处理
```

## 性能优化

- 批量发送(batch.size)
- 压缩(compression.type=lz4/zstd)
- 零拷贝(sendfile)
- 顺序写磁盘
