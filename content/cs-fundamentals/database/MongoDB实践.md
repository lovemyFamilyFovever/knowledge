---
title: "MongoDB实践"
tags: []
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# MongoDB实践

## 文档模型

```json
{
    "_id": ObjectId("..."),
    "name": "张三",
    "age": 25,
    "address": {
        "city": "北京",
        "district": "朝阳"
    },
    "tags": ["developer", "python"]
}
```

## 聚合管道

```javascript
db.orders.aggregate([
    { $match: { status: "completed" } },
    { $group: {
        _id: "$user_id",
        totalAmount: { $sum: "$amount" },
        orderCount: { $sum: 1 }
    }},
    { $sort: { totalAmount: -1 } },
    { $limit: 10 }
])
```

## 分片

```
mongos(路由) -> config server(元数据) -> shard1(数据分片)
                                      -> shard2
                                      -> shard3
```

分片键选择：高基数、低频变化、查询常用。

## Change Stream

```javascript
const changeStream = db.collection('orders').watch();
changeStream.on('change', (change) => {
    console.log('Order changed:', change);
    // 实时同步、触发下游处理
});
```
