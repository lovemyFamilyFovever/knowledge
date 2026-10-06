---
title: "Redis 面试题 9 道精讲"
tags: ["Redis", "缓存", "中间件"]
source: "github"
source_path: "interview_internal_reference / 10.Redis篇"
collected: "2026-09-23"
status: "stable"
---

本页收录 9 道 Redis 面试题，覆盖定位与选型、内存淘汰与持久化、主从复制、性能治理与集群；难度分布为初级 2 题、中级 4 题、高级 3 题，每题附核心结论、关键要点与面试官追问。

> 💡 说明
> 语料来自开源仓库 `interview_internal_reference` 的 Redis 篇（约 2015 年口径）。本库按现行 Redis（7.x）行为重写：淘汰策略由 6 种补为 8 种，value 上限由「1GB」修正为 512MB，并把原稿中重复的两道「与 Memcached 比较」合并为一题。

## 定位与选型（3 题）

### 1. 使用 Redis 有哪些好处？为什么它这么快？｜初级

核心结论：内存读写 + 单线程命令执行 + 自带高效数据结构与事件循环，三件事叠加带来低延迟；但"快"的前提是数据能装进内存，Redis 的定位是内存数据结构服务器，不是数据库的替代品。

- 低延迟：数据常驻内存，单次命令是 O(1)/O(logN) 的指针与数组操作，没有磁盘寻道。
- 数据结构丰富：String、Hash、List、Set、ZSet、Bitmap、HyperLogLog、Stream、Geo，很多"业务逻辑"可以直接用结构表达，省掉应用层计算。
- 单线程执行命令：所有命令串行处理，天然原子，不需要加锁，也不受线程上下文切换与锁竞争拖累。
- 原子操作齐全：`INCR`、`LPUSH`、`SADD`、`ZADD`、`GETSET`、`SETNX` 直接在服务端完成，省掉一次读一次写。
- 过期与淘汰：按 key 设 TTL，内存不足时按策略驱逐，适合做缓存层。
- 附带能力：持久化（RDB/AOF）、主从复制、Sentinel 高可用、Cluster 分片、发布订阅、Lua 脚本、管道（pipeline）。
- 为什么快（更准确的说法）：① 纯内存；② 单线程避免竞态与切换；③ epoll 事件循环 + 自己管理的缓冲区，网络模型轻量；④ 数据结构针对场景做过优化（listpack/intset/quicklist/skiplist）。真正的瓶颈通常在网络往返和大 key，而不是 CPU。

| 能力 | Redis | 关系型数据库 |
|---|---|---|
| 数据位置 | 内存（磁盘用于持久化） | 磁盘 |
| 单机 QPS 量级 | 10 万级 | 千级～万级 |
| 事务 | 命令打包，不回滚 | ACID，可回滚 |
| 复杂查询 | 无 JOIN，按 key 取 | 支持 |

> ⚠️ 注意
> 原稿把 Redis 的"事务"说成"要么全执行要么全不执行"，这不准确。`MULTI/EXEC` 只是把命令排队后连续执行，**没有回滚**：队列里某条命令执行出错（如对 String 执行 `LPUSH`），其余命令照常执行。它的价值是原子批处理和隔离，不是 ACID 的事务。

> 🎯 关键要点
> - 快来自内存 + 单线程 + 事件循环，不是魔法
> - 数据结构能替掉应用层逻辑，这才是主要收益
> - `MULTI/EXEC` 无回滚，别当数据库事务用
> - 单线程指命令执行，6.0 后网络 IO 可多线程
> - 容量受内存上限约束，超出要靠淘汰或分片

> 🔍 追问
> - Redis 单线程为什么还能跑满 10 万 QPS？瓶颈一般在哪？
> - 6.0 引入的多线程 I/O 和"命令单线程"矛盾吗？
> - 你的项目里哪块逻辑本来写在应用层，其实是靠 Redis 结构省掉的？

### 2. Redis 和 Memcached 有什么区别？现在该怎么选？｜初级

核心结论：差异不在"谁更快"，而在定位——Memcached 是纯内存 KV 缓存，Redis 是内存数据结构服务器。今天新项目多数直接选 Redis；Memcached 的价值在于极致简单的 KV 场景、成熟的多线程横向扩展和更低的运维心智。

- 数据模型：Memcached 只有 `key → 不透明字节`；Redis 有 9 类结构，且能在服务端对结构做原子操作。
- 持久化：Memcached 无持久化，进程重启数据全丢；Redis 有 RDB 快照 + AOF 日志（但仍是"尽力而为"，AOF `everysec` 最多丢 1 秒）。
- 多线程 vs 单线程：Memcached 是多线程 worker，核数堆上去吞吐线性增长；Redis 命令单线程，**要靠 Cluster 分片才能吃满多核**。这是原稿"Redis 快得多"在今天的边界。
- 协议与值大小：两者都是文本协议；Memcached 单值默认上限 1MB、key 上限 250 字节且不能含空格；Redis String 上限 512MB（`proto-max-bulk-len`），key 上限同为 512MB。
- 附加能力：Redis 有发布订阅、Stream、Lua、主从与哨兵/集群、`SCAN` 增量遍历；Memcached 只有 CAS 与 get/set/add/replace/incr/decr。
- 选型建议：只做"查询结果缓存、丢了就回源"→ 两者都行，Memcached 更省内存开销且多线程好扩；需要计数器、排行榜、分布式锁、会话、限流、消息队列 → Redis。已有 Memcached 且只跑纯 KV，没有理由为了"换新的"去迁移。

| 维度 | Redis | Memcached |
|---|---|---|
| 数据模型 | 多结构 | 纯 KV |
| 持久化 | RDB / AOF | 无 |
| 并发模型 | 命令单线程 + IO 多线程 | 多线程 |
| 单值上限 | 512MB | 1MB（默认） |
| 高可用 | Sentinel / Cluster | 靠客户端一致性哈希 |
| 典型场景 | 缓存 + 数据结构 + 锁 | 纯结果缓存 |

> 💡 提示
> Memcached 的分布式是**客户端**用一致性哈希完成的，服务端之间互不通信；Redis Cluster 是**服务端**自己分片并会返回 `MOVED` 重定向。所以"Memcached 挂一台"和"Redis 挂一个 master"的故障表现完全不同，谈高可用时别把两者混为一谈。

> 🎯 关键要点
> - 选型的分水岭是"需不需要数据结构和原子操作"
> - 纯 KV 大流量下 Memcached 多线程未必输给 Redis
> - Redis 的持久化不是可靠性保证，只是重启不自愈丢失
> - Memcached 无 HA 概念，靠客户端散列自然容错
> - value 上限 1MB 是 Memcached 硬伤，大对象要自己切

> 🔍 追问
> - 只做缓存的话，Memcached 相比 Redis 有什么实质优势？
> - 为什么很多公司两套都在用？各自承担什么？
> - 从 Memcached 迁到 Redis，你会怎么处理一致性哈希到 Cluster 的变化？

### 3. Redis 适合哪些场景？哪些场景不该用 Redis？｜中级

核心结论：适合"读多写少、能容忍短暂不一致、数据结构能简化逻辑"的场景；不适合当主存储、不适合强一致账务、不适合放不下的全量数据。

- 缓存（最主要）：把 DB 查询结果、页面片段、渲染好的 HTML 放进来，用 TTL + 主动失效。
- 计数器与排行：`INCR` 做浏览量/点赞/库存扣减，`ZSET` 做排行榜、延迟队列（score 存时间戳）。
- 分布式锁：`SET key val NX PX 30000` + Lua 释放；Redlock 有争议，高并发下慎用（见追问）。
- 会话与限流：Session 共享；用 `INCR` + TTL 或滑动窗口 `ZSET` 做限流。
- 消息与广播：`SUBSCRIBE/PUBLISH`（不持久、掉线即丢）、`LIST` 做简单队列、`Stream` 做带 ACK 与消费组的持久消息。
- 去重与统计：`SET`/`BITMAP` 做签到与布隆过滤器，`HyperLogLog` 用 12KB 估算上基数。
- 不该用的场景：① 唯一数据源（内存贵且淘汰会丢数据）；② 强一致的账务/订单状态机；③ 需要复杂查询、多表关联、范围扫描与分析；④ 单 value 数百 MB 的大对象（阻塞、复制放大）；⑤ 数据量远超内存且不能容忍命中率下降。

| 场景 | 结构 | 为什么用它 |
|---|---|---|
| 商品详情缓存 | String + TTL | 省 DB 查询 |
| 点赞/库存 | INCR / DECR | 天然原子 |
| 排行榜 | ZSET | 有序 + 分页 |
| 延迟任务 | ZSET(score=时间) | 按时间取 |
| 唯一性签到 | BITMAP | 一天一位 |
| 独立访客 | HyperLogLog | 误差 0.81%、常数内存 |

> ⚠️ 注意
> 缓存不是"加了就快"。用 Redis 会引入缓存与 DB 的双写一致性问题（先更新 DB 还是先删缓存、延迟双删、binlog 订阅），并带来穿透、击穿、雪崩三类故障。面试里说出"我把 Redis 当缓存，就必须回答一致性和失效怎么办"，比背十个特性更加分。

> 🎯 关键要点
> - 判断标准：数据可丢/可回源 + 结构能简化逻辑 → 适合
> - 计数/排行/锁是 Redis 独有红利，别用 DB 硬做
> - PUBLISH 掉线即丢，要可靠就上 Stream 或 MQ
> - 上缓存必配套：穿透、击穿、雪崩与双写方案
> - 别拿 Redis 当唯一存储

> 🔍 追问
> - 你的缓存怎么处理"缓存和数据库不一致"？
> - 缓存穿透、击穿、雪崩分别怎么防？
> - 为什么库存扣减用 Redis 还要回到 DB 落库？

## 内存与持久化（2 题）

### 4. MySQL 有 2000 万行，Redis 只放 20 万，怎么保证里面都是热点数据？｜中级

核心结论：靠"最大内存 + 淘汰策略"让 Redis 自己驱逐冷数据，再配合 key 设计（版本号、短前缀）、TTL 和访问局部性；缓存命中率的真正保障是回源与更新链路，不是把数据"提前塞满"。

- 先设上限：`maxmemory 8gb`（容器里留出 1.5～2 倍给子进程 COW 与复制缓冲区，别设成物理内存全部）。
- 选策略：`maxmemory-policy` 共 8 种，纯缓存用 `allkeys-lru`；热点有明显时效用 `allkeys-lfu`（Redis 4.0 引入，按访问频次衰减计数，比 LRU 更抗"偶发大批量扫描"污染）；只有带 TTL 的 key 才考虑 `volatile-*` 系列。
- 8 种策略：`noeviction`（写就报错，默认值，队列场景用它）、`allkeys-lru`、`allkeys-lfu`、`allkeys-random`、`volatile-lru`、`volatile-lfu`、`volatile-random`、`volatile-ttl`。
- 让 LRU 生效的细节：Redis 的 LRU 是**近似 LRU**——随机采样 `maxmemory-samples`（默认 5）个 key 淘汰其中最久未访问的；LFU 则用 16 位计数器（8 位对数计数器 + 8 位衰减时间）+ `lfu-log-factor` / `lfu-decay-time` 调参。
- TTL 兜底：热点会漂移，给 key 设合理过期时间比"等它被淘汰"更可控；批量打散过期时间（`TTL + random(0,300)`）避免同时失效造成雪崩。
- 主动预热 vs 被动回源：缓存刚上线或重启后先"预热"高频 key（`OBJECT FREQ`、离线统计），其余靠请求回源时 `SET` 回填；回填务必加互斥（`SETNX` 单飞）防击穿。
- 观测：`INFO memory`（`used_memory` / `evicted_keys`）、`INFO stats`（`keyspace_hits/misses`）、`redis-cli --hotkeys`（需要 LFU 或 `maxmemory-policy` 为 lru 且开启 `lfu`）、`MEMORY USAGE key`、`--bigkeys`。

| 策略 | 候选集 | 适用 |
|---|---|---|
| allkeys-lru | 全部 key | 通用缓存 |
| allkeys-lfu | 全部 key | 热点稳定、防扫描污染 |
| volatile-ttl | 有过期时间的 | 让"快过期的先走" |
| allkeys-random | 全部 key | 数据均匀随机访问 |
| noeviction | 不淘汰 | 队列/写多不许丢 |

> 💡 提示
> 原稿列的是 6 种策略（Redis 4.0 之前）。今天答"8 种 + 为什么 LRU 会被偶发扫描污染、所以有 LFU"，才是符合现行版本的口径。

> 🎯 关键要点
> - maxmemory 留出 fork 的 COW 余量
> - 缓存优先 allkeys-lfu 而非默认的 noeviction
> - Redis 是近似 LRU，samples 值决定精度与开销
> - TTL 打散随机量，避免同时失效
> - 命中率靠回源单飞 + 预热，不靠塞满

> 🔍 追问
> - LRU 和 LFU 各自什么时候更合适？为什么 Redis 不做精确 LRU？
> - 淘汰掉的 key 和过期的 key，删除时机有什么不同？（惰性 + 定期任务）
> - 缓存刚重启时 2000 万行的 DB 被瞬间打穿，怎么防？

### 5. Redis 的持久化是怎么做的？RDB 和 AOF 各自有什么代价？｜中级

核心结论：RDB 是某时刻的内存快照（fork + COW，恢复快、可能丢数据），AOF 是写命令追加日志（丢得少、文件大、恢复慢）；两者可以叠加，但持久化在缓存场景常被关掉或只做副本。

- RDB 流程：`SAVE` 阻塞主线程（生产禁用）；`BGSAVE` fork 出子进程把内存写成压缩二进制文件，父进程靠 COW 继续服务。默认策略示例：`save 3600 1 / save 300 100 / save 60 10000`。
- RDB 的代价：fork 大实例时会有毫秒到秒级停顿（要复制页表）；COW 期间内存写多会让内存占用翻倍；两次快照之间的数据会丢。
- AOF 流程：写命令追加到 `aof_buf`，按 `appendfsync` 落盘——`always`（每条命令 fsync，最安全最慢）、`everysec`（默认，最多丢 1 秒）、`no`（交给 OS）。Redis 7.0 起 AOF 与 RDB 统一为 **multi-part AOF**：manifest + 基础文件（base，RDB 编码）+ 增量文件（incr）。
- AOF 重写：文件膨胀后用 `BGREWRITEAOF` 按当前数据重生成最小命令集；重写期间新命令写入 `aof_rewrite_buf`，重写完成一起落盘，因此 fork + 编码 + 缓冲区三重开销，**开销通常比 RDB 更大**。
- 启动恢复优先级：有 AOF 用 AOF（`appendonly yes`），否则用 RDB。`aof-load-truncated` 允许 AOF 尾部不完整时截断加载。
- 数据安全性排序：AOF `always` > AOF `everysec` > RDB > 关闭持久化；代价正好相反。
- 生产上的三种常见取舍：① 纯缓存：只开 RDB 甚至都不开，重启靠回源自愈；② 重要数据：RDB + AOF `everysec`，RDB 传对象存储做异地备份；③ 高可用：主库关持久化，某个副本开 AOF（原稿的建议），代价是主库崩溃时只能靠副本，且副本重启期间数据不可用。

| 方式 | 形态 | 恢复速度 | 最大丢失 | 主要代价 |
|---|---|---|---|---|
| RDB | 快照 | 快 | 一个周期 | fork + COW 内存 |
| AOF everysec | 命令日志 | 慢 | 1 秒 | 文件大、重写开销 |
| AOF always | 命令日志 | 慢 | 0 | 吞吐显著下降 |
| 关闭 | 无 | — | 全部 | 只能当缓存 |

> ⚠️ 注意
> 别把"主库关持久化、副本开 AOF"当成万能方案。Redis 4 之后有个真实坑：主库重启后自身数据为空，副本会跟着全量同步一份空数据，而它自己那份 AOF 里还有数据但不会自动生效——所以要么主库也留一份持久化，要么用 `rdb-last-save`/监控卡住"空主库"重启。面试能说出这个细节，比只说"关主库持久化提升性能"要值钱。

> 🎯 关键要点
> - RDB 会丢一个快照周期，AOF 看 fsync 策略
> - fork 停顿与 COW 是大实例真实风险
> - 7.0 multi-part AOF 合并了 base + incr
> - AOF 重写比 RDB 快照更吃 CPU 与内存
> - 主库关持久化要防"空主库传染副本"

> 🔍 追问
> - 实例几 GB 时 fork 会造成明显延迟，你怎么定位和缓解？
> - AOF 和 RDB 同时开启时重启读哪个？为什么？
> - 你的数据能容忍丢多少？据此该怎么配？

## 复制与高可用（4 题）

### 6. 讲一下 Redis 主从同步的完整流程。｜中级

核心结论：首次连接做全量同步（RDB + 缓冲区命令重放），之后靠命令传播增量维护；断线后能用复制积压缓冲区做部分同步，否则退化为全量。

- 建立：副本执行 `REPLCONF` 上报监听端口与能力，再发 `PSYNC <replid> <offset>`。
- 全量同步（`FULLRESYNC`）：主库 `bgsave` 生成 RDB；期间新写命令进入 **repl_backlog**（复制积压缓冲区）；主库把 RDB 发给副本，副本清空自己、加载 RDB；随后 backlog 里缓冲的增量命令重放，追平后进入持续传播。
- 部分同步（`PSYNC` 命中）：主从各自的 `replid`（runid）+ `master_repl_offset` 一致或落在 backlog 范围内时，主库只发送缺失的偏移区间，返回 `CONTINUE`。Redis 4.5 引入 **replid2** 解决主库故障切换后旧副本重新接入时的无盘/部分同步问题。
- 命令传播：主库把写命令异步写入副本客户端输出缓冲区，副本 `REPLCONF ACK <offset>` 回报进度，主库据此知道每个副本的复制延迟。
- 心跳：`PING`（`repl-ping-replica-period`，默认 1 秒）维持连接；`repl-backlog-size` 决定能容忍多长的断线（按"每秒写入量 × 可容忍断线秒数"估算，别用默认 1MB）。
- 副本只读：`replica-read-only yes`（默认），写请求必须走主库。
- 无盘复制：`repl-diskless-sync` 让 RDB 直接流式发送不落盘，适合本地磁盘慢但网络快的环境。

| 阶段 | 传输内容 | 触发条件 |
|---|---|---|
| 全量 | RDB + backlog 增量 | 首次连接 / offset 太旧 |
| 部分 | 缺失的 offset 区间 | 断线短、backlog 覆盖到 |
| 传播 | 逐条写命令 | 稳态 |

> 💡 提示
> 答这题的正确顺序是"全量 → 传播 → 断线怎么办"，把 `replid + offset + backlog` 三个词讲清楚，比背诵"主节点做一次 bgsave"更能证明你懂。原稿只描述了全量同步，缺断线续传，这是面试真正的分水岭。

> 🎯 关键要点
> - 全量 = RDB + 缓冲区重放
> - 部分同步三要素：replid、offset、backlog
> - backlog 大小决定可容忍断线时长
> - ACK 偏移是判断复制延迟的唯一依据
> - 主库重启清空自己会传染给副本

> 🔍 追问
> - 复制积压缓冲区太小会怎样？怎么估一个合适的值？
> - 主从数据一定一致吗？异步复制会带来什么问题？
> - 全量同步期间主库的内存和延迟会发生什么变化？

### 7. 主从复制会有延迟，业务上怎么处理"刚写入却读不到"？｜高级

核心结论：Redis 复制默认异步，副本可能落后；处理"写后读"要么读主库、要么用 `WAIT` 等副本确认、要么给关键读打标签，本质是在一致性和延迟之间显式做选择。

- 读写分离的路由规则：查询类走副本，**同一请求链路里"写完之后立刻读"走主库**（session 粘连 / 强制主库标记）。这是最常见的落地做法。
- `WAIT numreplicas timeout`：写命令后阻塞等待 N 个副本 ACK 到该偏移，超时返回实际确认数。它只保证"已送达副本"，不保证副本已执行完，且不阻止主库在无人确认时崩溃丢数据——不是多数派提交。
- `min-slaves-to-write`（4.0 后为 `replica-serve-stale-data` + Sentinel 的 `min-replicas-to-write`/`min-replicas-max-lag`）：可用副本数不足时主库拒绝写入，缩小丢失窗口。
- 半同步思路：把关键写同时落 DB（binlog 订阅回灌缓存），Redis 只做加速层，读到旧值可由 DB 兜底。
- 监控指标：`master_repl_offset - slave_repl_offset`、`replica_lag_in_seconds`（`INFO replication`）、ACK 分布；延迟告警比事后排查重要。
- 全量同步风暴：副本重启或网络抖动触发全量，会给主库带来 fork + 大文件传输的双重压力，严重时雪崩。缓解：调大 backlog、副本分批启动、用无盘复制、避免把多个副本挂在同一次重启窗口。

| 手段 | 一致性提升 | 代价 |
|---|---|---|
| 关键读走主库 | 读己之写 | 主库压力 |
| WAIT | 副本已收到 | 延迟、非强保证 |
| 限制副本落后 | 防过度降级 | 可能拒写 |
| DB 兜底 | 最终一致 | 多一跳 |

> ⚠️ 注意
> 不要说"用 `WAIT` 就保证不丢数据"。`WAIT` 不改变异步复制的本质：主库被 `SIGKILL` 时，即使有副本收到命令未重放完，故障切换后仍可能丢；它只把窗口收窄。要真正的多数派语义得用 Redis Raft（Redis 8/Valkey 方向的 raft 实验特性）或换组件，面试时把边界说清楚比给一个漂亮结论更可信。

> 🎯 关键要点
> - 默认异步复制，副本天然可能旧
> - "写后立刻读"必须在应用层路由到主库
> - WAIT 是"送达确认"不是"多数派提交"
> - 复制延迟要作为一等指标监控
> - 全量同步风暴是真实的生产事故来源

> 🔍 追问
> - 你们的读写分离里，哪些接口必须读主库？为什么？
> - 副本挂了导致读流量全打到主库，怎么防止主库被压垮？
> - `WAIT` 和数据库的半同步复制差别在哪？

### 8. Redis 常见的性能问题有哪些？怎么定位和解决？｜高级

核心结论：性能问题几乎都出在"单线程被一件长任务占住"和"fork 带来的抖动"上，所以治理主线是大 key、热 key、慢命令、持久化抖动四类，配合可观测指标定位。

- **大 key**：value 上百 MB 或元素数十万。删除、序列化、复制、`HGETALL` 都会长时间阻塞主线程，并造成网络风暴。处理：`redis-cli --bigkeys` / `--memkeys` / `MEMORY USAGE` 定位，`UNLINK` 异步删除，业务上把大 hash 拆成多个小 key 或改用外部存储 + Redis 存索引。
- **热 key**：单个 key 的 QPS 超过单分片承载能力（如秒杀商品详情）。处理：本地缓存（Caffeine）+ 多级缓存、把 key 打散（`key_{0..N}` 随机读）、读写分离分摊副本、必要时提前预热 + 限流。
- **慢命令**：`KEYS *`（禁用，用 `SCAN`）、对大集合的 `SMEMBERS/HGETALL/ZRANGEBYSCORE 0 -1`、Lua 里的循环、`FLUSHALL`（用 `ASYNC`）。用 `SLOWLOG GET` + `slowlog-log-slower-than` 抓，别依赖 `MONITOR`（它自己就是性能杀手）。
- **fork 与持久化抖动**：`BGSAVE`/`AOF rewrite` 期间延迟毛刺。对策：主库不做 RDB 快照（或把快照挪到副本）、`appendfsync everysec`、避开业务高峰、透明大页设 `madvise`（`thp` 未关闭会让 fork 内存翻倍）。
- **客户端缓冲区**：慢消费者导致 `client-output-buffer-limit replica` 涨满，主库 OOM 或强制断开副本（复制反复全量）。对策：加内存、拆副本、用级联拓扑分散压力、限制大 value 的读取。
- **管道与批量**：多次 `GET` 用 `MGET`/pipeline 合并往返；一次一往返的调用在跨机房会慢 10 倍。
- **连接与线程池**：短连接反复握手 → 用连接池（Lettuce/JedisPool）并配超时与重试；`maxclients` 默认 10000。
- **内存碎片**：`mem_fragmentation_ratio > 1.5` 时考虑 `activedefrag yes` 或重启迁移。
- **拓扑经验**：主库下挂过多从库会增加 fork、复制缓冲区与网络压力；原稿"用单向链表（级联）而不是图状结构"在今天依然成立——级联能显著降低主库扇出，但代价是末端副本延迟更长，要按业务能接受的延迟选拓扑。

| 现象 | 大概率原因 | 定位手段 |
|---|---|---|
| 周期性毫秒级毛刺 | fork / COW | `LATEST_FORK_USEC`、`INFO persistence` |
| 单条命令超时 | 大 key、慢命令 | `SLOWLOG`、`--bigkeys` |
| 副本反复全量 | backlog 太小、网络 | `master_repl_offset`、backlog hit/miss |
| OOM 但 used_memory 不高 | 输出缓冲、碎片 | `client-output-buffer`、`mem_fragmentation_ratio` |

> 💡 提示
> 性能题的答法要"现象 → 定位 → 解法"三段闭环，只报解法会被追问"你怎么发现的"。手上能报出的工具就四个：`SLOWLOG`、`INFO`、`--bigkeys/--hotkeys`、`LATENCY DOCTOR`（`latency-monitor-threshold` 打开后 `latency history` 能直接看到 fork、命令、过期删除各阶段的耗时分布）。

> 🎯 关键要点
> - 单线程意味着一个慢操作就是全员等待
> - 大 key 和热 key 是两个不同维度的问题
> - fork 抖动是内存型服务绕不开的一课
> - `MONITOR` 不能上生产，`KEYS` 必须禁用
> - 级联复制换主库压力，但要付延迟

> 🔍 追问
> - 线上出现偶发 100ms 毛刺，你的排查顺序是什么？
> - 一个大 hash 拆不开，还有哪些办法降低它的影响？
> - 热 key 用本地缓存后，怎么保证不会读到明显过期的数据？

### 9. Redis 集群的原理是什么？Sentinel 和 Cluster 分别解决什么问题？｜高级

核心结论：Sentinel 解决"可用性"——主库挂了自动选新主并通知客户端；Cluster 解决"扩展性"——用 16384 个哈希槽分片，把数据摊到多个节点。两者层次不同，可叠加使用。

- **Sentinel（哨兵）**：独立进程集群，对主从做心跳与健康检查；主观下线（`down-after-milliseconds`）→ 哨兵 quorum 投票达到客观下线（ODOWN）→ 哨兵之间用 Raft 式选举领头 → 执行故障转移：从健康副本里按优先级、复制偏移、runid 排序选新主 → 其余副本改指向新主，旧主回来降为副本 → 通过 `+switch-master` 频道通知客户端。
- Sentinel 的边界：**不做数据分片**，单实例内存仍是上限；客户端仍要自己维护"当前 master 是谁"（依赖客户端库订阅订阅变更）。
- **Cluster**：每个节点负责 `16384` 个哈希槽中的一部分，`CRC16(key) % 16384` 定位槽；节点间用 Gossip（`cluster-node-timeout`）互相感知状态与槽位映射；迁移以槽为单位，客户端收到 `MOVED`（槽已迁走，需更新缓存）或 `ASK`（迁移中，本次去目标节点）；客户端本地缓存 slot map，命中失败才更新。
- 为什么是 16384 个槽：心跳包要携带槽位图，16384 bit = 2KB，正好一个包；且节点数建议在 1000 以内。
- 跨槽限制：多 key 命令（`MGET`、Lua 多 key、事务）要求所有 key 落同一槽，用 **hash tag** `{user1}` 强制同槽；这是 Cluster 最容易被忽略的设计约束。
- 高可用：每个分片主从，主挂则该分片副本升主；`cluster-require-full-coverage` 决定槽不全时是否整体拒写；仲裁由从节点投票（多数派），所以生产至少 3 主 3 从。
- 选哪套：数据量与并发单实例扛得住、只要不挂 → Sentinel；内存装不下或吞吐超单实例 → Cluster（代价：多 key 操作受限、运维更复杂、迁移期毛刺）。

| 维度 | Sentinel | Cluster |
|---|---|---|
| 解决 | 自动故障转移 | 水平分片 |
| 容量 | 仍是单实例 | 多实例相加 |
| 数据分布 | 全量复制到每副本 | 按槽分片 |
| 客户端 | 需支持订阅主地址变更 | 需支持重定向与 slot 缓存 |
| 最少节点 | 3 哨兵 + 1 主 N 从 | 3 主 3 从 |

> 💡 提示
> 一句能立住的话："Sentinel 是主从的守夜人，Cluster 是主从的分片版。" 再补 hash tag 和 `MOVED`/`ASK` 的区别，基本就到这题的上限了。

> 🎯 关键要点
> - 哨兵管可用性，Cluster 管容量与吞吐
> - 16384 槽 + CRC16 决定 key 归属
> - hash tag 是多 key 操作的唯一逃生口
> - MOVED 要更新本地缓存，ASK 只是本次转发
> - Cluster 生产建议 3 主 3 从、副本数一致

> 🔍 追问
> - Cluster 下如何做数据迁移？迁移期间读写怎么处理？
> - 为什么 Cluster 不用一致性哈希而用固定槽？
> - 分片后 `KEYS`/监控/备份怎么做？和单实例有什么不同？
