---
title: "Redis 持久化与内存管理"
tags: []
source: "baike"
source_path: "技术文章 / 数据库与存储"
collected: "2026-09-05"
status: "imported"
---

# Redis 持久化与内存管理

> 📌 **导航**：本文是 **Redis 持久化与内存管理** 词条，属于 database 术语集。相关枢纽：[[Redis深度解析与实战指南]]、[[Redis深入]]、[[Redis 数据结构与底层实现]]、[[LSM 树]]、[[缓存策略]]。

## 定义

**一句话定义：** Redis 持久化与内存管理，指用 RDB 快照、AOF 日志、二者混合来保证断电不丢数据，并用内存淘汰策略与碎片整理在 `maxmemory` 上限内控制驻留与内存健康的一整套机制。

**通俗类比：** 持久化像给内存账本定期拍照（RDB）+ 记流水（AOF）：机器重启靠照片快速复原、再照流水补回最新几笔；内存管理则像柜子满了按"最久没碰/最不常翻"先腾地方，并顺手把塞歪的抽屉捋齐。

## 为什么需要它

数据全在内存意味着进程重启即清零，故需落盘恢复；内存有限又要求满了能按策略淘汰旧数据、避免 OOM 或让写失败；长期增删还会留下内存碎片使 RSS 虚高。持久化 + 淘汰 + 碎片整理三者共同把"内存数据库"变成能扛重启、可控内存、不失控膨胀的生产组件。

## 核心机制

- **RDB：** 按 `save` 规则或 `BGSAVE` fork 子进程做全量二进制快照，文件紧凑、恢复快，但两次快照间宕机会丢数据。
- **AOF：** 追加写命令日志，`appendfsync` 三档——always 最安全最慢、everysec 折中（推荐）、no 交给 OS；文件变大后 `BGREWRITEAOF` 重写压缩。
- **混合持久化（4.0+）：** `aof-use-rdb-preamble` 让 AOF 重写时先写 RDB 全量、再追加 AOF 增量，兼顾恢复速度与丢数据窗口。
- **内存淘汰 8 策略：** noeviction（默认，满则报错）、allkeys/volatile × lru/random/lfu、volatile-ttl——在 `maxmemory` 满时按"全体 vs 仅设过期的键 × LRU/随机/LFU/TTL"淘汰；近似 LRU 用 `maxmemory-samples` 采样。
- **碎片整理：** 监控 `mem_fragmentation_ratio`（>1.5 偏高），4.0+ 可 `activedefrag yes` 在线整理或 `MEMORY PURGE`。

## 具体示例

生产常见组合：开 AOF 且 `appendfsync everysec` + 混合持久化 + 定时 `BGSAVE` 冷备份 + 设 `maxmemory 4gb`、`maxmemory-policy allkeys-lfu` 做纯缓存。此时若 `mem_fragmentation_ratio` 长期 1.6+，开 activedefrag 在线压缩；要"绝不丢"则把策略改 volatile-lru 或 noeviction 并接受写失败告警。

## 何时用 / 何时不用

- **用：** Redis 作缓存/会话/计数需重启后尽量恢复、需容量硬上限与淘汰、长跑要治理碎片时。
- **不用/取舍：** 纯可重建缓存（源库为准）可弱化 AOF 甚至只留 RDB 换性能；把 Redis 当唯一持久存储做严格事务/不丢（不如关系型或带 WAL 的 [[LSM 树]] 引擎）。

## 优劣与代价

✅ 快照 + 日志 + 混合在"恢复速度 / 丢数据窗口 / 性能"间可调；淘汰策略让内存可控。
⚠️ everysec 仍可能丢约 1 秒；RDB fork 大内存实例有延迟毛刺；AOF 体积与重写开销。
⚠️ 碎片率高会白白占内存，但激进 defrag 又吃 CPU，需权衡阈值。

## 与相关概念的区别

- **RDB vs AOF：** 前者全量快照、恢复快、会丢一段；后者命令日志、按 fsync 档控丢量、恢复需重放。
- **vs 数据库 WAL/[[LSM 树]]：** Redis 持久化面向内存态恢复；传统 WAL/LSM 是磁盘引擎的写恢复与合并机制。
- **vs 复制：** 持久化解决"同机重启"，跨机高可用靠 [[Redis 高可用架构（主从·哨兵·集群）]]。

## 常见误区

- 只要开了 AOF，Redis 就绝对不会丢任何数据。
- maxmemory 一设，淘汰策略随便选效果都一样。
- RDB 和 AOF 只能二选一，不能同时用。

## 面试速答

> 🎯 持久化三态：RDB 全量快照恢复快但丢快照间隔、AOF 命令日志 everysec 折中、混合(RDB 头+AOF 尾)；内存靠 maxmemory 加淘汰策略(全体/仅过期 × LRU/随机/LFU)；碎片看 mem_fragmentation_ratio 用 activedefrag。everysec AOF 仍可能丢一秒。

## 相关术语

[[Redis深度解析与实战指南]]、[[Redis深入]]、[[Redis 数据结构与底层实现]]、[[LSM 树]]、[[缓存策略]]

## 参考资料

建议人工核验：可参考 Redis 官方文档（Persistence、Eviction、Memory Optimization）与《Redis 设计与实现》(黄健宏)持久化章节。
