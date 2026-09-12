---
title: "Tokenizer 技术"
tags: [人工智能, 分词]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Tokenizer 技术


> 📌 **导航**：本文是 **Tokenizer 技术** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## 概述
**Tokenizer** 将文本分割为模型可处理的token序列。不同tokenizer的分词策略直接影响模型性能。

## 主流算法

| 算法 | 原理 | 代表模型 |
|------|------|---------|
| **BPE** | 字节对编码 | GPT系列 |
| **WordPiece** | 最大似然子词 | BERT |
| **SentencePiece** | 语言无关分词 | Llama, T5 |
| **Unigram** | 概率模型 | T5 |

## BPE算法
```python
def learn_bpe(corpus, num_merges=1000):
    # 1. 初始词汇表为所有字符
    vocab = set(c for word in corpus for c in word)

    # 2. 统计相邻token对频率
    for i in range(num_merges):
        pairs = count_pairs(corpus)
        best_pair = max(pairs, key=pairs.get)
        # 3. 合并最频繁的token对
        corpus = merge_pair(corpus, best_pair)
        vocab.add(''.join(best_pair))

    return vocab
```

## 中文分词挑战

| 挑战 | 说明 | 示例 |
|------|------|------|
| **无空格分隔** | 中文词之间无空格 | '人工智能' |
| **歧义切分** | 多种切分可能 | '研究生命科学' |
| **新词识别** | 网络新词 | '内卷' |

## Tokenizer对模型的影响

| 方面 | 影响 |
|------|------|
| **词汇表大小** | 大→覆盖广，小→效率高 |
| **分词粒度** | 细→长序列，粗→语义损失 |
| **中文效率** | 不同tokenizer的中文token效率差异很大 |
| **多语言支持** | 影响非英语语言的性能 |

## 常见Tokenizer对比

| Tokenizer | 词汇表 | 中文效率 | 模型 |
|-----------|--------|---------|------|
| GPT-4 | 100K | 中 | GPT-4 |
| Llama 3 | 128K | 好 | Llama 3 |
| Qwen | 152K | 很好 | Qwen |
| DeepSeek | 102K | 好 | DeepSeek |

```python
# 查看token数量
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained('meta-llama/Llama-3-8B')
tokens = tokenizer.encode('人工智能代理是未来趋势')
print(f'Token数量: {len(tokens)}')
```

## 小结
Tokenizer是LLM的'眼睛'，决定了模型如何'看'文本。中文场景需特别关注tokenizer的中文效率。

## 相关术语

[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[Embedding 技术详解]]、[[词向量]]、[[大模型预训练技术]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
