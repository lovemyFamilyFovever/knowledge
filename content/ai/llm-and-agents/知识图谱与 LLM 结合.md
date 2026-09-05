---
title: "知识图谱与 LLM 结合"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# 知识图谱与 LLM 结合

## 概述
将**知识图谱（KG）** 的结构化知识与LLM的推理能力结合，可以实现更准确、可解释的AI系统。

## KG + RAG
传统RAG基于文本块检索，KG-RAG基于实体关系检索：
```
传统RAG: 问题 → 文本相似度 → 相关段落 → 生成答案
KG-RAG: 问题 → 实体识别 → 图遍历 → 结构化知识 → 生成答案
```

## 实体提取
```python
def extract_entities(text: str, llm) -> list:
    prompt = f"""
    从以下文本中提取实体，标注类型：

    文本：{text}

    输出格式：[{{"name": "...", "type": "人物/组织/技术/概念"}}]
    """
    return json.loads(llm.generate(prompt))
```

## 关系提取
```python
def extract_relations(text: str, entities: list, llm) -> list:
    prompt = f"""
    基于实体列表，提取实体间的关系：

    文本：{text}
    实体：{entities}

    输出格式：[{{"source": "...", "relation": "...", "target": "..."}}]
    """
    return json.loads(llm.generate(prompt))
```

## 知识图谱构建
```python
class KnowledgeGraph:
    def __init__(self):
        self.entities = {}
        self.relations = []

    def add_entity(self, name, entity_type, properties=None):
        self.entities[name] = {'type': entity_type, 'properties': properties or {}}

    def add_relation(self, source, relation, target):
        self.relations.append({'source': source, 'relation': relation, 'target': target})

    def query_related(self, entity: str, depth=1) -> list:
        """查询与实体相关的知识"""
        results = []
        for r in self.relations:
            if r['source'] == entity or r['target'] == entity:
                results.append(r)
        return results
```

## 图数据库 Neo4j
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

def create_entity(tx, name, entity_type):
    tx.run('MERGE (e:Entity {name: $name, type: $type})', name=name, type=entity_type)

def create_relation(tx, source, relation, target):
    tx.run(f'MATCH (a:Entity {{name: $src}}), (b:Entity {{name: $tgt}}) '
           f'MERGE (a)-[:{relation}]->(b)', src=source, tgt=target)

def query_kg(tx, entity, depth=2):
    result = tx.run(
        'MATCH (e:Entity {name: $name})-[*1..{depth}]-(related) '
        'RETURN related.name, related.type', name=entity, depth=depth
    )
    return [record.data() for record in result]
```

## 知识图谱 vs 向量数据库

| 维度 | 知识图谱 | 向量数据库 |
|------|---------|-----------|
| **数据结构** | 图（节点+边） | 向量空间 |
| **查询方式** | 图遍历/SPARQL | 相似度搜索 |
| **优势** | 关系推理 | 语义搜索 |
| **劣势** | 构建成本高 | 缺乏关系 |
| **适用场景** | 多跳推理 | 相似匹配 |

## 小结
KG+LLM结合兼顾了结构化推理和语义理解。知识图谱提供精确的关系知识，LLM提供灵活的自然语言理解能力。
