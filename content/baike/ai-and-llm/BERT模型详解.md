---
title: "BERT模型详解"
tags: [人工智能, 模型]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# BERT模型详解


> 📌 **导航**：本文是 **BERT模型详解** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

BERT（Bidirectional Encoder Representations from Transformers）是Google于2018年发布的预训练语言模型。

## 预训练任务

### MLM（Masked Language Model）

随机遮盖15%的token：80%替换为[MASK]，10%替换为随机词，10%保持不变。

### NSP（Next Sentence Prediction）

判断两个句子是否连续。

## 模型变体对比

| 模型 | 参数量 | 层数 | 隐藏维度 | 特点 |
|------|--------|------|----------|------|
| BERT-Base | 110M | 12 | 768 | 基础版 |
| BERT-Large | 340M | 24 | 1024 | 大型版 |
| RoBERTa | 355M | 24 | 1024 | 去掉NSP，更多数据 |
| ALBERT | 12M | 12 | 768 | 参数共享，轻量 |
| DeBERTa | 350M | 24 | 1024 | 解耦注意力 |
| DistilBERT | 66M | 6 | 768 | 知识蒸馏，快60% |

```python
from transformers import BertForSequenceClassification, BertTokenizer
model = BertForSequenceClassification.from_pretrained('bert-base-chinese')
tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
inputs = tokenizer("这部电影真好看", return_tensors="pt")
outputs = model(**inputs)
```

## BERT vs GPT

| 特性 | BERT | GPT |
|------|------|-----|
| 架构 | Encoder-only | Decoder-only |
| 注意力 | 双向 | 单向 |
| 预训练 | MLM + NSP | 自回归语言模型 |
| 适合任务 | 理解类（分类/NER） | 生成类（对话/写作） |

## 相关术语

[[Transformer架构深度解析]]、[[大模型基础术语详解]]、[[词向量]]、[[Embedding 技术详解]]、[[注意力机制]]、[[大语言模型架构演进]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
