---
title: "Redis 数据结构与底层实现"
tags: []
source: "baike"
source_path: "技术文章 / 数据库与存储"
collected: "2026-09-05"
status: "imported"
---

# Redis 数据结构与底层实现

> 📌 **导航**：本文是 **Redis 数据结构与底层实现** 词条，属于 database 术语集。相关枢纽：[[Redis深度解析与实战指南]]、[[Redis深入]]、[[高级数据结构]]、[[B+树]]、[[LSM 树]]。

## 定义

**一句话定义：** Redis 数据结构与底层实现，指对外的九种类型（String/Hash/List/Set/ZSet/Stream/Bitmap/HyperLogLog/Geo）与它们按元素规模自动切换的内部编码（SDS、listpack、quicklist、skiplist、intset、hashtable、radix tree）之间的对应关系，兼顾内存占用与操作复杂度。

**通俗类比：** 像收纳衣柜：东西少时用真空压缩袋（listpack 紧凑省空间），东西多了换成开放式衣架（hashtable/跳表 方便查找）。Redis 按件数自动帮你换收纳法，不用你操心。

## 为什么需要它

缓存层对内存极其敏感，小对象若都用通用结构，指针与哈希开销会成倍浪费。Redis 让每个类型"元素少时用紧凑编码、超阈值转通用编码"，既省内存又保住操作复杂度。理解这层编码，才能解释大 key 为何让命令退化、为什么单个 Hash 塞太多 field 反而更糟、以及 `maxmemory` 该怎么估。

## 核心机制

| 类型 | 元素少时编码 | 超阈值转 | 典型用途 |
|------|--------------|----------|----------|
| String | int / embstr | raw(SDS) | 缓存对象、计数器、分布式锁、Session |
| Hash | listpack | hashtable | 对象字段、购物车、配置 |
| List | listpack | quicklist | 消息队列、最新动态 |
| Set | intset | hashtable | 标签、共同好友、抽奖去重 |
| ZSet | listpack | skiplist + hashtable | 排行榜、延迟队列、Geo |
| Stream | listpack 节点 | radix tree + listpack | 可靠消息、事件溯源 |

- **SDS：** 记录已用/空闲长度 → O(1) 取长度、二进制安全、空间预分配与惰性释放减少重分配、杜绝缓冲区溢出。
- **listpack（7.0 起取代 ziplist）：** 连续内存省指针；旧 ziplist 因存前驱长度有"连锁更新"最坏 O(N²) 隐患，listpack 去掉该字段消除连锁。
- **quicklist：** listpack 节点组成的双向链表，两端操作快、限制单节点大小。
- **skiplist：** ZSet 用跳表而非红黑树——实现简单、范围查询（ZRANGEBYSCORE）高效、便于按 score 定位；配 hashtable 提供 O(1) 求成员分数。
- **intset：** 有序去重，遇到更大整数自动升级编码（16/32/64）。
- **hashtable：** 双表 + 渐进式 rehash，每次读写迁移一桶，避免一次性重排卡顿。

## 具体示例

一个 ZSet 排行榜：成员很少时整体存 listpack，元素或成员变长超过 `zset-max-listpack-entries/element` 阈值后自动转成 skiplist + hashtable——`ZRANGE`/`ZRANK` 走跳表有序遍历、`ZSCORE` 走哈希 O(1)。同理把海量小对象塞进一个超大 Hash 会让该 key 的 rehash 与内存尖峰集中，拆成多片小 Hash（如 `user:{id%100}`）更稳。

## 何时用 / 何时不用

- **用：** 需内存高效的缓存/计数/排行/关系集合时，按数据形状选类型并留意编码阈值、避免造大 key。
- **不用：** 复杂多维查询与事务（用关系库）；无界增长的大集合（改用 Stream/分页或外部存储）；需要精确统计且不能容忍近似时别用 HyperLogLog。

## 优劣与代价

✅ 小对象紧凑编码省内存、通用编码保住 O(1)/O(log n)，类型语义贴合缓存场景。
⚠️ 编码自动切换有隐性阈值；大 key、单 Hash 元素过多会引发卡顿与内存尖峰。
⚠️ HyperLogLog/Bitmap 是概率/位结构，用错场景会得近似或失真结果。

## 与相关概念的区别

- **vs [[Redis深入]]：** 那篇是含持久化/集群的速览，本篇专注类型与其内部编码的映射与切换机制。
- **vs 通用 [[高级数据结构]]：** 跳表/哈希/基数树在此是 Redis 特定编码角色，非泛论其原理。

## 常见误区

- Redis 的每种数据类型永远固定用同一种底层编码。
- 把所有小字段塞进一个大 Hash 一定比多个 key 省内存，无需关心单 Hash 元素数。
- Redis 7.0 之后 ziplist 仍是默认的紧凑编码。

## 面试速答

> 🎯 Redis 每类型按规模自动换编码：小时 listpack/intset 紧凑、大时转 hashtable/skiplist；SDS O(1) 取长且二进制安全，hashtable 渐进式 rehash，7.0 起 listpack 取代有连锁更新隐患的 ziplist。懂编码才懂大 key 与拆 Hash。

## 相关术语

[[Redis深度解析与实战指南]]、[[Redis深入]]、[[高级数据结构]]、[[B+树]]、[[LSM 树]]

## 参考资料

建议人工核验：可参考 Redis 官方文档与《Redis 设计与实现》(黄健宏) 数据结构章节核实各编码与转换阈值；未编造文献编号或 URL。
