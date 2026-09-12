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

## 原理与机制

- **单线程命令执行 + I/O 多路复用**：命令执行主线程单线程，避免锁竞争与上下文切换；Redis 6.0 起网络 I/O 可多线程，但命令执行仍单线程（保证原子性）。
- **内存 + 持久化**：数据在内存，靠 RDB/AOF 落盘以防丢失。
- **过期与淘汰**：键可设 TTL；内存满时按 `maxmemory-policy`（如 allkeys-lru、volatile-lru、noeviction）淘汰。

## 关键组成

### 数据结构与底层实现

| 类型 | 底层实现 | 典型用途 |
|------|----------|----------|
| String | SDS（简单动态字符串） | 缓存、计数器、分布式锁 |
| List | quicklist（listpack + 链表） | 消息队列、最新列表 |
| Hash | listpack / hashtable | 对象存储 |
| Set | intset / hashtable | 去重、交并差 |
| ZSet | listpack / skiplist（跳表） | 排行榜、延迟队列 |
| Stream | radix tree + listpack | 持久化消息队列 |
| Bitmap / HyperLogLog / Geo | 基于 String / 特殊编码 | 签到、基数统计、地理位置 |

> 注：Redis 7.0 起，小数据量的 Hash/ZSet/List 用 **listpack** 取代了早期的 ziplist。跳表原理见 [[高级数据结构]]。

### 持久化

| 方式 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| RDB | 定时全量快照（fork 子进程） | 文件紧凑、恢复快 | 两次快照间可能丢数据 |
| AOF | 追加写命令日志（含 fsync 策略） | 数据更安全 | 文件大、恢复较慢 |
| 混合持久化 | RDB + 增量 AOF（4.0+） | 兼顾恢复速度与安全 | — |

### 高可用与扩展

| 模式 | 特点 |
|------|------|
| 主从复制 | 读写分离、数据冗余 |
| 哨兵 Sentinel | 监控 + 自动故障转移 |
| Cluster | 数据分片（16384 个 slot）+ 去中心化 |

### Lua 脚本（原子操作）

```lua
-- 限流：INCR + 首次设过期，整个过程原子执行
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
if current > tonumber(ARGV[2]) then
    return 0
end
return 1
```

### Stream 消息队列

```bash
XADD mystream * name "hello" value "world"        # 生产
XGROUP CREATE mystream mygroup $                  # 建消费者组
XREADGROUP GROUP mygroup consumer1 COUNT 1 BLOCK 0 STREAMS mystream >   # 消费
```

## 应用场景

- 缓存（最常用）、分布式锁、计数器/限流、排行榜、会话存储、消息队列（List/Stream）、地理位置（Geo）。

## 优点与局限

- 优点：读写极快（内存）、数据结构丰富、支持持久化与集群、生态成熟。
- 局限：受内存容量与成本限制；单线程命令执行下大 key / 慢命令（如 `KEYS *`）会阻塞；主从异步复制可能丢数据；缓存一致性需业务侧处理。

## 常见误区

- 生产环境用 `KEYS *` 遍历：会阻塞主线程，应改用 `SCAN` 渐进式遍历。
- 认为「开了持久化就绝不丢数据」：RDB 会丢快照间隔的数据、AOF 取决于 fsync 策略，主从切换也可能丢。
- 忽视大 key / 热 key：单个大 key 或删除大集合会阻塞，热 key 会打满单分片（对策见 [[分布式缓存]]）。

## 相关术语

[[Redis深度解析与实战指南]]、[[分布式缓存]]、[[高级数据结构]]、[[NoSQL 数据库术语]]、[[分布式ID与缓存术语百科]]

## 参考资料

建议人工核验：可参考 Redis 官方文档（数据结构、持久化、Cluster、Stream）与《Redis 设计与实现》(黄健宏)。
