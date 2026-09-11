---
title: "ElasticSearch搜索"
tags: [数据库, ElasticSearch, 搜索引擎, 倒排索引]
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# ElasticSearch搜索

## 定义

**一句话定义：** Elasticsearch（ES）是基于 Lucene 的分布式搜索与分析引擎，以**倒排索引**为核心，提供近实时的全文检索、结构化搜索、分析与聚合能力。

**通俗类比：** 普通数据库像逐页翻书找关键词；ES 像书末的「索引页」——先建好「词 → 出现在哪些文档」的倒排表，查词时直接定位，速度极快。

> 多义说明：本文是 ES 的**核心用法速览**；搜索引擎的完整原理（倒排索引、分词、相关性评分、Lucene 段合并等）见 [[搜索引擎技术详解]]。

## 原理与机制

- **倒排索引**：正排是「文档 → 词」，倒排是「词 → 文档列表（posting list）」，是全文检索的核心。
- **分词（Analysis）**：写入时对文本分词建倒排；查询时对查询串分词再匹配。
- **近实时（NRT）**：文档写入后需 refresh（默认约 1s）才可被搜索；底层 Lucene 段（segment）不可变，定期合并。

```
文档1: "机器学习入门"   文档2: "深度学习实践"   文档3: "机器学习进阶"
倒排索引:
  "机器" -> [文档1, 文档3]
  "学习" -> [文档1, 文档2, 文档3]
  "深度" -> [文档2]
  "入门" -> [文档1]        "实践" -> [文档2]
```

## 关键用法

### 查询 DSL（bool 组合查询）

```json
{
  "query": {
    "bool": {
      "must":   [ { "match": { "title": "机器学习" } } ],
      "filter": [ { "range": { "price": { "gte": 50 } } } ],
      "should": [ { "term": { "category": "AI" } } ]
    }
  }
}
```
> `must` 影响相关性评分、`filter` 只过滤不评分（可缓存、更快）。

### 分词器

| 分词器 | 特点 | 适用 |
|--------|------|------|
| standard | 按空格/标点切分 | 英文 |
| ik_max_word | 最细粒度穷举 | 中文**索引** |
| ik_smart | 智能粗粒度 | 中文**搜索** |

### 向量搜索（kNN）

```json
{
  "knn": {
    "field": "embedding",
    "query_vector": [0.1, 0.2, 0.3],
    "k": 10,
    "num_candidates": 100
  }
}
```
> 用于语义检索 / RAG（结合 [[向量数据库技术]]）。

## 应用场景

- 全文检索（站内搜索、日志检索 ELK）、可观测性（日志/指标/追踪）、聚合分析、向量语义检索。

## 优点与局限

- 优点：全文检索能力强、水平扩展、近实时、聚合分析丰富、生态完善（Kibana/Logstash/Beats）。
- 局限：非事务型（不适合做主库/OLTP）、写入有 refresh 延迟、资源消耗大、最终一致；深分页（from+size）性能差，需用 `search_after`。

## 常见误区

- 把 ES 当主数据库：ES 是**检索/分析**引擎，事务与强一致应由 MySQL 等承担，ES 作二级索引。
- `match` 与 `term` 混用：`match` 会分词、`term` 不分词（对 text 字段用 term 常查不到，应对 keyword 字段用）。
- 深分页用大 `from`：`from+size` 超过一定深度会慢/OOM，应改用 `search_after` 或 scroll。

## 相关术语

[[搜索引擎技术详解]]、[[数据库内核原理深度解析]]、[[NoSQL 数据库术语]]、[[向量数据库技术]]

## 参考资料

建议人工核验：可参考 Elasticsearch 官方文档（倒排索引、Query DSL、aggregations、kNN）、《Elasticsearch 权威指南》，以及 Apache Lucene 文档。
