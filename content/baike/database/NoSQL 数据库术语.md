---
title: "NoSQL 数据库术语"
tags: [数据库, NoSQL, Redis, MongoDB]
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# NoSQL 数据库术语

> 📌 **导航**：本文是 **NoSQL 数据库全景**（键值 Redis/Memcached、文档 MongoDB、搜索 Elasticsearch、宽列 HBase/Cassandra、图 Neo4j、时序 InfluxDB 等）与 SQL/NoSQL 选型对比。其中 Redis 详见 [[Redis深入]]、MongoDB 详见 [[MongoDB实践]]、Elasticsearch 详见 [[ElasticSearch搜索]]；CAP 取舍见 [[CAP 定理]]。

---

## Redis（String/Hash/List/Set/ZSet）

**一句话定义（大白话）：** 基于内存的高性能键值数据库，支持多种数据结构，常用于缓存、会话管理、排行榜等场景。

**通俗类比（生活场景）：** 一个超级多功能的工具箱——既能存单个值（String），又能存对象（Hash），又能存列表（List），又能去重（Set），又能排排行榜（ZSet）。

**具体示例：**

```bash
# String：最基础的类型，存字符串、数字
SET user:1:name "张三"
GET user:1:name              # "张三"
INCR article:1:views         # 阅读量 +1
SET token:abc123 "user_1" EX 3600  # 设置过期时间 1 小时

# Hash：适合存储对象
HSET user:1 name "张三" age 25 email "zhangsan@example.com"
HGET user:1 name             # "张三"
HGETALL user:1               # 获取所有字段
HINCRBY user:1 age 1         # age +1

# List：有序列表，支持两端操作
LPUSH queue:tasks "task1"    # 左侧插入
RPUSH queue:tasks "task2"    # 右侧插入
LPOP queue:tasks             # 左侧弹出
BRPOP queue:tasks 30         # 阻塞弹出（消息队列）

# Set：无序集合，自动去重
SADD tags:article:1 "数据库" "Redis" "缓存"
SMEMBERS tags:article:1      # 获取所有标签
SISMEMBER tags:article:1 "Redis"  # 判断是否存在
SINTER tags:article:1 tags:article:2  # 交集（共同标签）

# ZSet（Sorted Set）：有序集合，带分数
ZADD leaderboard 100 "player1"
ZADD leaderboard 200 "player2"
ZADD leaderboard 150 "player3"
ZREVRANGE leaderboard 0 9 WITHSCORES  # Top 10 排行榜
ZRANK leaderboard "player2"   # 排名
```

**为什么需要它：** 内存操作比磁盘快几个数量级（纳秒级 vs 毫秒级），Redis 是最快的数据库之一，适合高并发、低延迟场景。

**与相关术语的对比和区分：** Redis 是"多数据结构缓存"，Memcached 是"简单键值缓存"。Redis 数据结构更丰富，支持持久化，Memcached 更轻量但功能少。

---

## MongoDB（文档数据库）

**一句话定义（大白话）：** 以 JSON/BSON 文档为存储单元的 NoSQL 数据库，schema 灵活，适合半结构化数据。

**通俗类比（生活场景）：** 一个超大的文件柜——每个抽屉（集合）里放不同类型的文件（文档），文件格式可以不一样，不用提前规定。

**具体示例：**

```javascript
// 插入文档（不需要先建表）
db.users.insertOne({
    name: "张三",
    age: 25,
    hobbies: ["编程", "游泳"],
    address: {
        city: "北京",
        street: "朝阳路"
    }
});

// 查询：嵌套文档也能查
db.users.find({ "address.city": "北京" });

// 更新：灵活修改字段
db.users.updateOne(
    { name: "张三" },
    { $set: { age: 26 }, $push: { hobbies: "跑步" } }
);

// 聚合管道（类似 SQL 的 GROUP BY）
db.orders.aggregate([
    { $match: { status: "completed" } },
    { $group: {
        _id: "$user_id",
        totalAmount: { $sum: "$amount" },
        orderCount: { $sum: 1 }
    }},
    { $sort: { totalAmount: -1 } }
]);

// 索引
db.users.createIndex({ "address.city": 1 });
```

**为什么需要它：** 关系型数据库需要预先定义 schema，MongoDB 不需要。字段随时加减，嵌套结构直接存储，开发效率高。

**与相关术语的对比和区分：** MongoDB 是"文档模型"，MySQL 是"关系模型"。MongoDB 适合 schema 不固定、快速迭代的场景；MySQL 适合结构固定、需要强一致性的场景。

---

## Elasticsearch（搜索引擎）

**一句话定义（大白话）：** 基于 Lucene 的分布式全文搜索引擎，擅长文本搜索、日志分析、数据分析。

**通俗类比（生活场景）：** 超级加强版的书后索引——不仅告诉你关键词在哪页，还能按相关性排序、支持模糊搜索、同义词、聚合统计。

**具体示例：**

```json
// 创建索引
PUT /products
{
  "mappings": {
    "properties": {
      "name": { "type": "text", "analyzer": "ik_max_word" },
      "price": { "type": "float" },
      "category": { "type": "keyword" },
      "description": { "type": "text" }
    }
  }
}

// 插入文档
POST /products/_doc/1
{
  "name": "MySQL数据库设计与优化",
  "price": 59.9,
  "category": "技术",
  "description": "深入讲解MySQL索引优化和事务"
}

// 全文搜索
GET /products/_search
{
  "query": {
    "multi_match": {
      "query": "数据库优化",
      "fields": ["name", "description"]
    }
  },
  "highlight": {
    "fields": { "name": {}, "description": {} }
  }
}

// 聚合分析
GET /products/_search
{
  "aggs": {
    "avg_price": { "avg": { "field": "price" } },
    "categories": { "terms": { "field": "category" } }
  }
}
```

**为什么需要它：** MySQL 的 LIKE '%keyword%' 全文搜索很慢，Elasticsearch 通过倒排索引实现毫秒级全文搜索，还能做复杂的聚合分析。

**与相关术语的对比和区分：** Elasticsearch 是"搜索引擎"，不是"数据库"。通常和 MySQL 配合使用：MySQL 存储原始数据，Elasticsearch 提供搜索和分析能力。

---

## Memcached

**一句话定义（大白话）：** 简单的高性能分布式内存缓存系统，只支持简单的键值对存储。

**通俗类比（生活场景）：** 一个超快的便签墙——贴上去（SET）就存好了，撕下来（GET）就读到了。但便签只能写一行字，不能贴照片。

**具体示例：**

```bash
# 存储
SET user:1:name 3600 张三
# key:user:1:name  超时:3600秒  value:张三

# 读取
GET user:1:name    # 返回 "张三"

# 删除
DELETE user:1:name

# 批量读取（减少网络往返）
GETS user:1:name user:1:email user:1:phone

# 递增计数器
INCR article:1:views 1

# Memcached 特点：
# - 只支持 String 类型
# - 最大 1MB 的 value
# - 不支持持久化，重启数据丢失
# - 天然分布式（客户端分片）
# - 多线程架构，充分利用多核 CPU
```

**为什么需要它：** 比 Redis 更简单、更快（单机性能）、更节省内存。适合纯缓存场景，不需要复杂数据结构。

**与相关术语的对比和区分：** Memcached 是"简单缓存"，Redis 是"数据结构缓存"。Memcached 没有持久化、没有复制、数据结构单一，但更轻量更快。

---

## HBase（列式存储）

**一句话定义（大白话）：** 基于 Hadoop 的分布式列式数据库，适合海量数据的随机读写。

**通俗类比（生活场景）：** 一个超大的 Excel——但和普通 Excel 不同，它是按"列族"组织的。你可以只读某一列的数据，不用扫整行。

**具体示例：**

```bash
# 创建表（指定列族）
create 'users', 'info', 'activity'

# 插入数据
put 'users', 'user1', 'info:name', '张三'
put 'users', 'user1', 'info:age', '25'
put 'users', 'user1', 'info:email', 'zhangsan@example.com'
put 'users', 'user1', 'activity:login', '2025-01-15'

# 读取整行
get 'users', 'user1'

# 读取特定列
get 'users', 'user1', {COLUMNS => ['info:name', 'info:email']}

# 扫描范围
scan 'users', {STARTROW => 'user1', STOPROW => 'user10'}

# 删除数据
delete 'users', 'user1', 'info:email'
```

**为什么需要它：** HBase 适合超大规模数据（百亿行级别），支持海量数据的随机实时读写。列式存储让稀疏数据（很多字段为空）存储效率更高。

**与相关术语的对比和区分：** HBase 是"列族存储"，不是"列式存储"（ClickHouse 那种）。HBase 适合稀疏数据，Cassandra 适合写密集，两者都是宽列存储。

---

## Neo4j（图数据库）

**一句话定义（大白话）：** 以图结构（节点和关系）存储数据的数据库，擅长处理复杂的关系网络。

**通俗类比（生活场景）：** 你的人脉关系网——每个人是一个节点，"朋友"、"同事"、"家人"是关系。Neo4j 就是帮你存储和查询这种关系网的工具。

**具体示例：**

```cypher
// 创建节点
CREATE (zhangsan:Person {name: "张三", age: 25})
CREATE (lisi:Person {name: "李四", age: 30})
CREATE (company:Company {name: "某科技公司"})

// 创建关系
CREATE (zhangsan)-[:FRIEND_WITH]->(lisi)
CREATE (zhangsan)-[:WORKS_AT]->(company)
CREATE (lisi)-[:MANAGES]->(zhangsan)

// 查询：找出张三的所有朋友的朋友（2度人脉）
MATCH (zhangsan:Person {name: "张三"})-[:FRIEND_WITH]->(friend)-[:FRIEND_WITH]->(fof)
RETURN fof.name

// 查询：最短路径
MATCH path = shortestPath(
    (zhangsan:Person {name: "张三"})-[*]-(target:Person {name: "王五"})
)
RETURN path

// 社区发现
CALL gds.louvain.stream('myGraph')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).name, communityId
```

**为什么需要它：** 关系型数据库用 JOIN 处理多对多关系很慢（多次 JOIN），Neo4j 直接沿关系遍历，关系越复杂性能优势越大。

**与相关术语的对比和区分：** Neo4j 是"图数据库"，MySQL 是"关系数据库"。关系数据库的"关系"是表之间的逻辑关联，Neo4j 的"关系"是数据本身的一部分，是一等公民。

---

## InfluxDB（时序数据库）

**一句话定义（大白话）：** 专门处理时间序列数据的数据库，优化了按时间写入和查询的场景。

**通俗类比（生活场景）：** 一个自动记录的日记本——每分钟自动记录温度、湿度、CPU 使用率等数据。你要查"昨天下午 3 点的温度"，它能极快地找出来。

**具体示例：**

```bash
# 写入数据点
# measurement: cpu_usage
# tags: host=server1, region=cn
# fields: value=65.5
# timestamp: 自动或指定

curl -XPOST 'http://localhost:8086/write?db=mydb' \
  -d 'cpu_usage,host=server1,region=cn value=65.5 1705334400000000000'

# 查询：最近 1 小时的平均 CPU 使用率
SELECT mean(value) FROM cpu_usage
WHERE time > now() - 1h
GROUP BY time(5m), host

# 查询：每天的最大值
SELECT max(value) FROM cpu_usage
WHERE time > now() - 7d
GROUP BY time(1d)

# 保留策略（自动删除过期数据）
CREATE RETENTION POLICY "30d" ON "mydb" DURATION 30d REPLICATION 1

# 连续查询（自动聚合）
CREATE CONTINUOUS QUERY "cq_hourly" ON "mydb"
BEGIN
    SELECT mean(value) INTO "cpu_hourly" FROM "cpu_usage"
    GROUP BY time(1h), host
END
```

**为什么需要它：** 传统数据库存储时间序列数据效率低（百万级数据点写入慢，按时间范围查询也慢）。InfluxDB 针对这些场景做了极致优化。

**与相关术语的对比和区分：** InfluxDB 是"时序数据库"，Prometheus 是"监控系统+时序数据库"。InfluxDB 更通用，Prometheus 更专注于监控告警。

---

## Cassandra

**一句话定义（大白话）：** 分布式、高可用、无中心节点的宽列存储数据库，适合写密集型场景。

**通俗类比（生活场景）：** 一个没有总部的连锁超市——每家店都能独立收银（无中心节点），店越多处理能力越强（线性扩展），任何一家店关门不影响其他店（高可用）。

**具体示例：**

```cql
-- 创建键空间（类似数据库）
CREATE KEYSPACE myapp
WITH REPLICATION = {
    'class': 'NetworkTopologyStrategy',
    'cn': 3,
    'us': 3
};

-- 创建表
CREATE TABLE myapp.user_events (
    user_id UUID,
    event_time TIMESTAMP,
    event_type TEXT,
    event_data MAP<TEXT, TEXT>,
    PRIMARY KEY (user_id, event_time)
) WITH CLUSTERING ORDER BY (event_time DESC);

-- 插入数据
INSERT INTO myapp.user_events (user_id, event_time, event_type, event_data)
VALUES (uuid(), now(), 'login', {'ip': '192.168.1.1', 'device': 'mobile'});

-- 查询：某个用户最近 100 个事件
SELECT * FROM myapp.user_events
WHERE user_id = some_uuid
LIMIT 100;

-- Cassandra 特点：
-- 1. AP 系统（可用性 + 分区容错性，放弃强一致性）
-- 2. 无中心节点，任何节点都能读写
-- 3. 写入性能极高（顺序写磁盘）
-- 4. 适合时序数据、事件日志、IoT 数据
```

**为什么需要它：** 需要跨数据中心部署、写入量极大、不能接受单点故障的场景。Cassandra 的无中心架构让它天然支持多活部署。

**与相关术语的对比和区分：** Cassandra 是"AP 系统"（高可用），HBase 是"CP 系统"（强一致）。Cassandra 写入快但读取慢，HBase 读取快但写入相对慢。

---

## PynamoDB

**一句话定义（大白话）：** Python 的 DynamoDB ORM 库，让你用 Python 对象的方式操作 AWS DynamoDB。

**通俗类比（生活场景）：** DynamoDB 是 AWS 的托管数据库，但操作它需要写复杂的 JSON。PynamoDB 就像给你配了一个翻译，让你用 Python 代码直接操作，就像用 SQLAlchemy 操作 MySQL 一样。

**具体示例：**

```python
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute

# 定义模型
class User(Model):
    class Meta:
        table_name = 'users'
        region = 'us-east-1'

    user_id = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()
    age = NumberAttribute()
    email = UnicodeAttribute()

# 创建表
User.create_table(read_capacity_units=5, write_capacity_units=5)

# 插入数据
user = User()
user.user_id = 'user_001'
user.name = '张三'
user.age = 25
user.email = 'zhangsan@example.com'
user.save()

# 查询
user = User.get('user_001')
print(user.name)  # 张三

# 条件查询
from pynamodb.expressions import Key
users = User.query().filter(Key('age').gte(18))

# 批量操作
with User.batch_write() as batch:
    for i in range(100):
        user = User()
        user.user_id = f'user_{i:03d}'
        user.name = f'用户{i}'
        user.age = 20 + (i % 30)
        batch.save(user)
```

**为什么需要它：** DynamoDB 的原生 API 是 JSON 格式，写起来繁琐。PynamoDB 提供了 Pythonic 的接口，集成到项目中更方便。

**与相关术语的对比和区分：** PynamoDB 是"客户端库"，不是数据库。它操作的是 DynamoDB（AWS 托管的 NoSQL），类似于 SQLAlchemy 操作 MySQL。

---

## NoSQL vs SQL 对比

**一句话定义（大白话）：** SQL 是关系型数据库（表结构、ACID、JOIN），NoSQL 是非关系型数据库（灵活结构、高扩展、最终一致性）。

**通俗类比（生活场景）：** SQL 像正装——正式、规范、适合正式场合。NoSQL 像休闲装——灵活、舒适、适合快速运动。没有好坏，看场合。

**具体示例：**

```
对比维度          SQL (MySQL/PostgreSQL)         NoSQL (Redis/MongoDB/Cassandra)
数据模型          表/行/列                        文档/键值/图/列族
Schema           固定（先定义后使用）              灵活（随时可变）
事务支持          完整 ACID                       部分支持（最终一致性为主）
扩展方式          垂直扩展（加 CPU/内存）           水平扩展（加机器）
JOIN             支持（核心能力）                  不支持或弱支持
查询语言          SQL（标准化）                    各自 API（不统一）
一致性            强一致性                         最终一致性（BASE）
适合场景          事务、报表、复杂查询              高并发、大数据、快速迭代
```

```sql
-- SQL 方式：用户 + 订单 + 商品
SELECT u.name, o.id, p.name, oi.quantity
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE u.id = 1;

-- NoSQL（MongoDB）方式：冗余存储，一次查询
db.orders.find({
    user_id: 1
}).populate('items.product');
-- 或者直接把用户信息冗余到订单文档中
```

**为什么需要它：** 没有万能的数据库。SQL 适合需要强一致性和复杂查询的场景，NoSQL 适合需要高扩展性和灵活 schema 的场景。实际系统常常混合使用。

**与相关术语的对比和区分：** CAP 定理是理解 SQL vs NoSQL 的理论基础——分布式系统中一致性(C)、可用性(A)、分区容错性(P) 三者只能满足两个。SQL 通常选 CP，NoSQL 通常选 AP。

---

## 相关术语

[[Redis深入]]、[[MongoDB实践]]、[[ElasticSearch搜索]]、[[CAP 定理]]、[[数据库设计术语]]、[[分布式存储术语百科]]

## 参考资料

建议人工核验：可参考各数据库官方文档（Redis / MongoDB / Elasticsearch / HBase / Cassandra / Neo4j / InfluxDB），以及《NoSQL 精粹》(Martin Fowler, *NoSQL Distilled*)、Brewer 的 CAP 猜想。
