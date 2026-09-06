---
title: "Embedding 技术详解"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Embedding 技术详解

## 概述
**Embedding（嵌入）** 是将文本、图像等数据转换为高维数值向量的技术。向量之间的距离反映语义相似度，是 RAG、搜索、推荐系统的基础。

## 技术演进

| 技术 | 年代 | 原理 | 特点 |
|------|------|------|------|
| **Word2Vec** | 2013 | Skip-gram/CBOW | 静态词向量 |
| **GloVe** | 2014 | 全局矩阵分解 | 统计共现 |
| **ELMo** | 2018 | 双向LSTM | 上下文相关 |
| **BERT** | 2018 | Transformer编码器 | 双向上下文 |
| **OpenAI Embedding** | 2022 | 对比学习 | API服务 |

## Word2Vec 原理
```python
# Skip-gram: 用中心词预测上下文
from gensim.models import Word2Vec
sentences = [['AI','agent','framework'], ['vector','database','search']]
model = Word2Vec(sentences, vector_size=100, window=5, min_count=1)
vector = model.wv['AI']  # 获取词向量
similar = model.wv.most_similar('AI', topn=5)  # 相似词
```

## BERT Embedding
```python
from transformers import AutoTokenizer, AutoModel
import torch

tokenizer = AutoTokenizer.from_pretrained('bert-base-chinese')
model = AutoModel.from_pretrained('bert-base-chinese')

inputs = tokenizer('人工智能代理', return_tensors='pt')
with torch.no_grad():
    outputs = model(**inputs)
# [CLS] token的输出作为句子向量
embedding = outputs.last_hidden_state[:, 0, :]
```

## OpenAI Embedding
```python
from openai import OpenAI
client = OpenAI()

response = client.embeddings.create(
    model='text-embedding-3-small',
    input='AI Agent是能够自主执行任务的智能系统',
)
vector = response.data[0].embedding  # 1536维向量
```

## 对比学习训练 Embedding
```python
# InfoNCE Loss: 拉近正样本对，推远负样本对
class ContrastiveLoss:
    def __call__(self, anchor, positive, negatives, temperature=0.07):
        pos_sim = cosine_similarity(anchor, positive) / temperature
        neg_sims = [cosine_similarity(anchor, neg) / temperature for neg in negatives]
        logits = torch.cat([pos_sim.unsqueeze(0), torch.stack(neg_sims)])
        labels = torch.tensor([0])  # 正样本在第0位
        return F.cross_entropy(logits.unsqueeze(0), labels)
```

## Embedding 模型对比

| 模型 | 维度 | 中文支持 | MTEB得分 | 延迟 |
|------|------|---------|---------|------|
| text-embedding-3-small | 1536 | 是 | 62.3 | 低 |
| text-embedding-3-large | 3072 | 是 | 64.6 | 中 |
| bge-large-zh-v1.5 | 1024 | 优化 | 64.5 | 低 |
| e5-mistral-7b | 4096 | 是 | 66.6 | 高 |
| jina-embeddings-v2 | 768 | 是 | 60.4 | 低 |

## 小结
Embedding是AI系统中连接文本与数学空间的桥梁。从Word2Vec到现代对比学习模型，质量持续提升。选择模型时需权衡质量、速度和成本。
