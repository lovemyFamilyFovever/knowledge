---
title: "MongoDB实践"
tags: [数据库, MongoDB, NoSQL, 文档数据库]
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# MongoDB实践

## 定义

**一句话定义：** MongoDB 是以**文档（BSON）**为数据模型的 NoSQL 数据库，Schema 灵活、支持嵌套与数组、原生提供分片与副本集，适合结构多变、读多写多的业务。

**通俗类比：** 关系型数据库像 Excel 表格（每行列数固定）；MongoDB 像一叠 JSON 卡片，每张卡片字段可以不同、还能嵌套子卡片，存取贴近程序里的对象。

> 多义说明：本文是 MongoDB 的**实战要点**；NoSQL 各类型（KV / 文档 / 列族 / 图）与取舍见 [[NoSQL 数据库术语]]。

## 原理与机制

- **文档模型（BSON）**：数据以 BSON（二进制 JSON）文档存于集合（collection），字段可嵌套文档/数组，Schema 灵活（同集合文档结构可不同）。
- **副本集（Replica Set）**：一主多从 + 自动选主，提供高可用与读扩展。
- **分片（Sharding）**：按分片键把数据水平拆分到多个 shard，突破单机容量与吞吐。

## 关键用法

### 文档示例

```json
{
    "_id": "ObjectId(...)",
    "name": "张三",
    "age": 25,
    "address": { "city": "北京", "district": "朝阳" },
    "tags": ["developer", "python"]
}
```

### 聚合管道（Aggregation Pipeline）

```javascript
db.orders.aggregate([
    { $match:  { status: "completed" } },        // 过滤
    { $group:  { _id: "$user_id",                 // 分组聚合
                 totalAmount: { $sum: "$amount" },
                 orderCount:  { $sum: 1 } } },
    { $sort:   { totalAmount: -1 } },            // 排序
    { $limit:  10 }                              // 取前 10
])
```

### 分片架构

```
mongos(路由) ──> config server(元数据)
             └─> shard1 / shard2 / shard3 (数据分片，各自是一个副本集)
```
> 分片键选择原则：**高基数、低频变化、查询常用**；选错分片键会导致数据倾斜（jumbo chunk）。

### Change Stream（变更流）

```javascript
const changeStream = db.collection('orders').watch();
changeStream.on('change', (change) => {
    console.log('Order changed:', change);   // 实时同步、触发下游处理
});
```

## 应用场景

- 内容管理、商品/用户画像等**结构多变**的数据、物联网/日志、快速迭代的互联网业务、需要嵌套/数组的场景。

## 优点与局限

- 优点：Schema 灵活、开发友好（对象直存）、水平扩展（分片）、高可用（副本集）、聚合能力强。
- 局限：**多文档事务**虽已支持（4.0+ 副本集、4.2+ 分片）但性能与关系型有差距；不擅长复杂多表 JOIN；分片键设计不当会倾斜；内存占用较高。

## 常见误区

- 以为 MongoDB「无 Schema」：它是**灵活 Schema**，仍应设计合理的文档结构（内嵌 vs 引用）。
- 过度内嵌导致文档无限增长（如把全部评论内嵌进一篇文章）——应改引用或分页内嵌。
- 忽视分片键设计：一旦选定难以更改，低基数/单调递增键（如时间戳）会造成热点与倾斜。

## 相关术语

[[NoSQL 数据库术语]]、[[数据库设计术语]]、[[分库分表]]、[[读写分离]]、[[Redis深入]]

## 参考资料

建议人工核验：可参考 MongoDB 官方手册（文档模型、聚合管道、分片、副本集、Change Streams）与《MongoDB 权威指南》。
