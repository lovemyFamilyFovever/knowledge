---
title: "NoSQL 数据库术语"
tags: [数据库, NoSQL, Redis, MongoDB]
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# NoSQL 数据库术语

> 📌 **导航**：本文是 **NoSQL 数据库术语** 枢纽页。键值看 [[Redis深入]]、文档看 [[MongoDB实践]]、搜索看 [[ElasticSearch搜索]]、列族看 [[列族数据库（HBase 与 Cassandra）]]、图看 [[图数据库 Neo4j]]、时序看 [[时序数据库 InfluxDB]]；本页只给类型全景与 SQL/NoSQL 选型。

## 定义

**一句话定义：** NoSQL 数据库术语是"非关系型数据库"的类型全景——按数据模型分为键值、文档、列族、图、时序、搜索等族，本页作为选型枢纽按类型索引各代表库，并给出 SQL 与 NoSQL 的取舍，不重复各专条内容。

**通俗类比：** 像一家家具卖场的分区导览：沙发区、床垫区、灯具区各归其类，本页告诉你要买的东西属于哪个区、去哪块看，而不是把每样家具的说明书都搬来重抄一遍。

## 为什么需要它

NoSQL 不是一个产品，而是一族按不同数据模型解决不同问题的系统；混淆它们（拿图库做报表、拿时序库做事务）会踩坑。先建立"类型 → 适用问题"的心智地图，再按数据形状选具体引擎，是数据库选型的第一步。

## 核心机制

| 类型 | 数据模型 | 代表 | 归口 |
|------|----------|------|------|
| 键值 | key→value | Redis、Memcached | [[Redis深入]]、本页内联 |
| 文档 | JSON/BSON 文档 | MongoDB、DynamoDB | [[MongoDB实践]]、本页内联 |
| 搜索 | 倒排索引 | Elasticsearch | [[ElasticSearch搜索]] |
| 列族 | 行键 + 列族宽表 | HBase、Cassandra | [[列族数据库（HBase 与 Cassandra）]] |
| 图 | 节点 + 关系 | Neo4j | [[图数据库 Neo4j]] |
| 时序 | 时间线指标 | InfluxDB、Prometheus | [[时序数据库 InfluxDB]] |

SQL vs NoSQL 取舍：

| 维度 | SQL（关系型） | NoSQL |
|------|---------------|-------|
| 数据模型 | 表/行/列、强 schema | 文档/键值/图/列族等 |
| 一致性 | 强一致、完整 ACID | 多为最终一致（BASE） |
| 扩展 | 垂直为主 | 水平分片为主 |
| 查询 | 标准 SQL、擅长 JOIN | 各引擎专用 API、弱或不支持 JOIN |

## 具体示例

选型判断链：数据是否有固定关系、要不要强事务与 JOIN → 是则关系型；是"按 key 秒查的缓存/会话" → 键值（Redis/Memcached）；"字段频繁变的半结构化对象" → 文档（MongoDB/DynamoDB）；"几十亿稀疏宽行写密集" → 列族（HBase/Cassandra）；"多跳关系网络" → 图（Neo4j）；"带时间戳的监控流" → 时序（InfluxDB）；"全文与聚合检索" → 搜索（Elasticsearch）。

## 何时用 / 何时不用

- **用本页：** 需要在多类 NoSQL 之间做类型级选型、先建立"按数据形状选引擎"的地图时。
- **不用本页（转专条）：** 已确定某具体库要深入时直接进对应专条；强一致多表事务仍以关系型为主。

## 优劣与代价

✅ 一表看清六类模型与各自边界，减少"用错库"的系统性错误。
⚠️ 枢纽只给类型级取舍，不展开任一库的内部机制。
⚠️ 真实系统常混合使用（关系库 + 缓存 + 搜索 + 时序），选型是组合题非单选。

## 与相关概念的区别

- **vs 关系型：** 关系型强 schema/ACID/JOIN、垂直扩展；NoSQL 换模型与水平扩展，多数牺牲强一致。
- **类型之间：** 键值求快与简单、文档求灵活半结构、列族求稀疏宽表海量写、图求多跳关系、时序求按时间聚合、搜索求全文——各解决一类形状。

## 常见误区

- NoSQL 就是"不用 SQL 的数据库"，彼此可以互相替代。
- 只要数据量大，就一定要从关系型换成 NoSQL。
- 所有 NoSQL 都只保证最终一致，没有强一致选项。

## 面试速答

> 🎯 NoSQL 按数据模型分族：键值(Redis)、文档(MongoDB)、列族(HBase/Cassandra)、图(Neo4j)、时序(InfluxDB)、搜索(ES)。相对 SQL 的强 schema/ACID/JOIN，多数换水平扩展与最终一致。选型看数据形状、JOIN 与事务、扩展与一致性。

## 相关术语

[[Redis深入]]、[[MongoDB实践]]、[[ElasticSearch搜索]]、[[列族数据库（HBase 与 Cassandra）]]、[[图数据库 Neo4j]]、[[时序数据库 InfluxDB]]、[[数据仓库]]

## 参考资料

建议人工核验：可对照各数据库官方文档（Redis/MongoDB/HBase/Cassandra/Neo4j/InfluxDB/Elasticsearch）与《NoSQL 精粹》(Martin Fowler, *NoSQL Distilled*)。
