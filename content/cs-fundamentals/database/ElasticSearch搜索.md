---
title: "ElasticSearch搜索"
tags: []
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# ElasticSearch搜索

## 倒排索引

```
文档1: "机器学习入门"
文档2: "深度学习实践"
文档3: "机器学习进阶"

倒排索引:
"机器" -> [文档1, 文档3]
"学习" -> [文档1, 文档2, 文档3]
"深度" -> [文档2]
"入门" -> [文档1]
"实践" -> [文档2]
```

## 查询DSL

```json
{
    "query": {
        "bool": {
            "must": [
                { "match": { "title": "机器学习" } }
            ],
            "filter": [
                { "range": { "price": { "gte": 50 } } }
            ],
            "should": [
                { "term": { "category": "AI" } }
            ]
        }
    }
}
```

## 分词器

| 分词器 | 特点 | 适用 |
|--------|------|------|
| standard | 按空格/标点 | 英文 |
| ik_max_word | 最细粒度 | 中文索引 |
| ik_smart | 智能粒度 | 中文搜索 |

## 向量搜索

```json
// kNN向量搜索
{
    "knn": {
        "field": "embedding",
        "query_vector": [0.1, 0.2, ...],
        "k": 10,
        "num_candidates": 100
    }
}
```
