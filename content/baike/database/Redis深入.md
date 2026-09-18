---
title: "Redis深入"
tags: [数据库, Redis, 缓存, 数据结构]
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# Redis深入


> 📌 **导航**：本文是 **Redis深入** 词条，属于 database 术语集。相关枢纽：[[MySQL从入门到架构师]]、[[MySQL深入]]、[[Redis深入]]、[[Redis深度解析与实战指南]]、[[SQL 基础术语]]。

## 定义

**一句话定义：** Redis 是基于内存的高性能键值（Key-Value）数据库，提供多种数据结构、持久化、主从复制与集群能力，常用作缓存、消息队列与分布式协调组件。

**通俗类比：** Redis 像一张放在手边的便签墙——数据都在内存里、读写极快；便签有多种形状（字符串/列表/哈希/集合/有序集合），还能拍照存档（持久化）以防断电丢失。

> 多义说明：本文是 Redis 的**核心机制速览**；更系统的原理与实战见 [[Redis深度解析与实战指南]]，缓存三大问题（穿透/击穿/雪崩）见 [[分布式缓存]]。

## 为什么需要它

磁盘数据库扛不住热点读与高频计数：一次页面渲染、一个秒杀库存、一份会话，需要亚毫秒级读写和跨请求状态。Redis 把数据常驻内存、用单线程事件循环消除锁竞争，再以丰富数据结构（ZSet 排行、Set 去重、Stream 队列）把"要建表写 JOIN"的活压成一次 O(log n) 命令，成为缓存、限流、分布式锁与轻量 MQ 的事实标准。

## 核心机制

- **单线程命令执行 + I/O 多路复用：** 命令执行主线程单线程，避免锁竞争与上下文切换；Redis 6.0 起网络 I/O 可多线程，但命令执行仍单线程（保证原子性）。
- **内存 + 持久化：** 数据在内存，靠 RDB/AOF 落盘以防丢失。
- **过期与淘汰：** 键可设 TTL；内存满时按 `maxmemory-policy`（如 allkeys-lru、volatile-lru、noeviction）淘汰。

数据结构与底层实现：

| 类型 | 底层实现 | 典型用途 |
|------|----------|----------|
| String | SDS（简单动态字符串） | 缓存、计数器、分布式锁 |
| List | quicklist（listpack + 链表） | 消息队列、最新列表 |
| Hash | listpack / hashtable | 对象存储 |
| Set | intset / hashtable | 去重、交并差 |
| ZSet | listpack / skiplist（跳表） | 排行榜、延迟队列 |
| Stream | radix tree + listpack | 持久化消息队列 |

> 注：Redis 7.0 起小数据量的 Hash/ZSet/List 用 **listpack** 取代早期 ziplist；跳表原理见 [[高级数据结构]]。

持久化：

| 方式 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| RDB | 定时全量快照（fork 子进程） | 文件紧凑、恢复快 | 两次快照间可能丢数据 |
| AOF | 追加写命令日志（含 fsync 策略） | 数据更安全 | 文件大、恢复较慢 |
| 混合持久化 | RDB + 增量 AOF（4.0+） | 兼顾恢复速度与安全 | — |

高可用与扩展：主从复制做读写分离与数据冗余，哨兵 Sentinel 做监控 + 自动故障转移，Cluster 用 16384 个 slot 做数据分片 + 去中心化。

## 何时用 / 何时不用

- **用：** 缓存（最常用）、分布式锁、计数器/限流、排行榜、会话存储、消息队列（List/Stream）、地理位置（Geo）。
- **不用：** 需要远超内存容量且能容忍延迟的海量持久数据（放磁盘库，Redis 只作缓存）；强一致、复杂事务与多表分析（交给 MySQL/PG）；一次性离线批处理。

## 具体示例

用 Lua 把"计数 + 首次设过期 + 超限拒绝"合成一个原子操作做限流：

```lua
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
if current > tonumber(ARGV[2]) then return 0 end
return 1
```

用 Stream 做带消费者组的持久化消息队列：`XADD mystream * name hello` 生产，`XGROUP CREATE` 建组，`XREADGROUP` 阻塞消费。

## 优劣与代价

✅ 读写极快（内存）、数据结构丰富、支持持久化与集群、生态成熟。
⚠️ 受内存容量与成本限制；单线程命令执行下大 key / 慢命令（如 `KEYS *`）会阻塞主线程。
⚠️ 主从异步复制可能丢数据，缓存与库一致性需业务侧处理。

## 与相关概念的区别

- **vs Memcached：** Redis 数据结构丰富且支持持久化/复制/集群，Memcached 是简单 KV 内存缓存。
- **vs 磁盘关系库：** Redis 作旁路缓存与协调组件，不承担持久化主库与事务；一致性要回源数据库。
- **vs 专业 MQ（Kafka）：** Redis Stream 轻量、适合中小吞吐与低延迟；海量持久、高吞吐日志流用 Kafka。

## 常见误区

- 生产环境可以放心用 KEYS * 遍历所有键。
- 只要开启了持久化，Redis 就绝不会丢数据。
- 大 key 和热 key 对 Redis 性能没有实质影响。

## 面试速答

> 🎯 Redis=内存多结构 KV：单线程命令执行 + 多路复用保原子、RDB/AOF 持久化、主从/哨兵/Cluster 做高可用与分片，ZSet/Stream/Set 撑起排行/队列/去重；瓶颈在内存与大 key/慢命令阻塞主线程。
> 🔍 追问：为什么单线程还能这么快？
> 🔍 追问：RDB 和 AOF 各自什么时候丢数据？
> 🔍 追问：为什么用 SCAN 而不是 KEYS？

## 相关术语

[[Redis深度解析与实战指南]]、[[分布式缓存]]、[[高级数据结构]]、[[NoSQL 数据库术语]]、[[分布式ID与缓存术语百科]]

## 参考资料

建议人工核验：可参考 Redis 官方文档（数据结构、持久化、Cluster、Stream）与《Redis 设计与实现》(黄健宏)。
