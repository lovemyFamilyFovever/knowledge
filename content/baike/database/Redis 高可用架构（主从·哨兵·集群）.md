---
title: "Redis 高可用架构（主从·哨兵·集群）"
tags: []
source: "baike"
source_path: "技术文章 / 数据库与存储"
collected: "2026-09-05"
status: "imported"
---

# Redis 高可用架构（主从·哨兵·集群）

> 📌 **导航**：本文是 **Redis 高可用架构（主从·哨兵·集群）** 词条，属于 database 术语集。相关枢纽：[[Redis深度解析与实战指南]]、[[Redis深入]]、[[读写分离]]、[[分布式锁]]、[[CAP 定理]]。

## 定义

**一句话定义：** Redis 高可用架构是逐级递进的三层能力——主从复制做数据冗余与读扩展、Sentinel 做故障自动探测与主从切换、Cluster 用 16384 个哈希槽做去中心化分片，合起来解决"单点会挂、单机装不下"两个问题。

**通俗类比：** 主从像给主管配备份（抄一份、还能帮忙接单）；哨兵像值班小组（盯着谁失联了，把备份提拔成主管并通知大家）；集群则像连锁分店（按区域分单、各自管一片，谁都不是一座孤店）。

## 为什么需要它

单实例 Redis 既是可用性单点，又是容量与吞吐上限。主从让读可扩、写有副本备份；但主挂了要人工切、且主从不能扩写。Sentinel 把故障检测与自动 failover 自动化解决可用；仍受限于单主写入规模。Cluster 用哈希槽把数据分片到多主节点，突破容量与写吞吐，并把 failover 内建。三层按需叠加。

## 核心机制

- **主从复制：** 从节点 `replicaof` 建立连接；首次全量同步（主 BGSAVE 发 RDB + 缓冲增量），断线重连走 PSYNC + 复制积压缓冲区做部分重同步（`repl-backlog-size` 要够覆盖断线时长）。
- **Sentinel：** 每秒 PING 检测，达 `down-after-milliseconds` 记主观下线 SDOWN，多数哨兵认同记客观下线 OOWN；哨兵间用类 Raft 选领导者、按优先级/复制偏移/runid 选从提主、改写其余从与通知客户端。
- **Cluster：** key 经 `CRC16(key) mod 16384` 映射到槽、槽分配给各主节点；请求落错节点返回 MOVED（永久重定向、更新本地槽表），槽迁移中返回 ASK（临时、先 ASKING 再试）；每主可挂从，主挂从升，`cluster-node-timeout` 控制判死。

## 具体示例

三主三从 Cluster：`redis-cli --cluster create ... --cluster-replicas 1` 把 16384 槽分给三主；某主失联超 node-timeout，其从升主接管槽。若用主从 + Sentinel 而非 Cluster，则写入仍集中单主、容量受单机限，只换来自动故障切换——扩写才需要 Cluster。无盘复制 `repl-diskless-sync` 让从多时不从盘各读一份 RDB，省 IO。

## 何时用 / 何时不用

- **用：** 主从做读扩展与热备；Sentinel 要在"单写 + 自动切换"下要高可用；Cluster 在数据/写吞吐超单机、可接受多键操作跨槽受限（同 slot/`{tag}`）时。
- **不用：** 数据量小、可用性要求不高用单实例 + 持久化即可；强一致多键事务跨分片不适用 Cluster；强一致写要求高时注意主从异步复制的丢数据窗口。

## 优劣与代价

✅ 分层递进：冗余→自动切换→水平分片，读扩展与可用性逐级增强。
⚠️ 主从/Sentinel 单写瓶颈、异步复制切换可能丢已确认写；Cluster 跨槽 mset/事务受限、扩容要迁槽。
⚠️ 节点与运维复杂度、脑裂与客户端重定向处理都需设计。

## 与相关概念的区别

- **Sentinel vs Cluster：** 前者单主 + 自动 failover（不扩写），后者多主分片 + 内建 failover（扩写扩容量）。
- **vs [[读写分离]]：** 读写分离用主从做读分流；本文是 Redis 侧的复制/切换/分片全栈，含写扩展与自动化故障转移。
- **vs [[分布式锁]]：** 高可用复制不保证锁语义，主从切换会丢锁状态，锁的正确性另需 Redlock/看门狗（见 [[Redis 分布式锁]]）。

## 常见误区

- 部署了主从复制就自动实现了主节点宕机的无感切换。
- Redis Cluster 可以像单机一样随意对多个 key 执行跨槽事务。
- Sentinel 集群里只要一个哨兵发现主节点失联就会立刻切主。

## 面试速答

> 🎯 三层高可用：主从(全量 BGSAVE+缓冲、断线 PSYNC+backlog)做读扩展热备；Sentinel 靠 SDOWN/OOWN+选主自动 failover 但单写瓶颈；Cluster 用 CRC16 哈希槽分片、MOVED/ASK 重定向扩写。主从异步切换可能丢已确认写、Cluster 跨槽事务受限。

## 相关术语

[[Redis深度解析与实战指南]]、[[Redis深入]]、[[读写分离]]、[[分布式锁]]、[[CAP 定理]]

## 参考资料

建议人工核验：可参考 Redis 官方文档（Replication、Sentinel、Redis Cluster、PSYNC）与《Redis 实战》(Josiah Carlson)；未编造文献编号或 URL。
