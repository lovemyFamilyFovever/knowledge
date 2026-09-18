---
title: "AI Agent 技术面试题库 - 扩展部分2：NLP基础与文本处理"
tags: []
source: "baike"
source_path: "技术题库 / AI Agent面试专题"
collected: "2026-09-05"
status: "imported"
---

# AI Agent 技术面试题库 - 扩展部分2：NLP基础与文本处理

> NLP 基础与文本处理（15 题）｜涵盖词嵌入、序列模型、文本分类、命名实体识别等核心领域。
> 每题标注难度（初级 / 中级 / 高级），编号 1–15 连续，附参考解答与关键要点。

## 主题1：词嵌入与语言表示（5 题）

### 1. 解释 Word2Vec 的两种训练模式：CBOW 和 Skip-gram。｜中级

Word2Vec 是经典的词嵌入方法，通过预测上下文或目标词来学习词向量。

- **CBOW（Continuous Bag of Words）**：输入为上下文词，输出为预测目标词；训练速度快，适合高频词
- **Skip-gram**：输入为目标词，输出为预测上下文词；适合低频词，语义表示更好

```python
# Word2Vec示例
from gensim.models import Word2Vec

sentences = [["我", "喜欢", "自然语言处理"], ...]
model = Word2Vec(sentences, vector_size=100, window=5, sg=1)  # sg=1: Skip-gram

# 获取词向量
vector = model.wv["自然语言"]
```

> 🎯 关键要点：Word2Vec 是静态词嵌入，一个词只有一个向量。
> Skip-gram 通常效果更好。
> 可以捕获词的语义关系。

### 2. 比较静态词嵌入和动态词嵌入（上下文词嵌入）的区别。｜中级

静态词嵌入为每个词分配固定的向量，动态词嵌入根据上下文生成不同的表示。

| 特性 | 静态词嵌入 | 动态词嵌入 |
|------|-----------|-----------|
| 代表方法 | Word2Vec, GloVe | BERT, ELMo |
| 一词多义 | 无法处理 | 可以处理 |
| 计算效率 | 高 | 低 |
| 使用方式 | 查表 | 需要模型推理 |

> 🎯 关键要点：动态词嵌入是 NLP 的主流方向。
> BERT 等预训练模型提供上下文表示。
> 静态嵌入在某些场景仍有价值。

### 3. 解释 GloVe 的训练原理。｜高级

GloVe（Global Vectors）通过矩阵分解的方式学习词向量，结合了全局统计信息和局部上下文。

**核心思想：**

- 构建词共现矩阵
- 优化词向量使它们的点积接近共现概率的对数

**目标函数：**

```text
J = Σ f(X_ij) (w_i^T w_j + b_i + b_j - log X_ij)²
```

其中 `X_ij` 是词 i 和 j 的共现次数，f 是权重函数。

> 🎯 关键要点：GloVe 结合了局部和全局信息。
> 训练效率高于 Word2Vec。
> 适合大规模语料。

### 4. 什么是子词嵌入？BPE 分词如何工作？｜中级

子词嵌入将词分解为更小的单元，解决 OOV（Out-of-Vocabulary）问题。

**BPE（Byte Pair Encoding）算法：**

1. 初始化：将所有词拆分为字符
2. 统计所有相邻字符对的频率
3. 合并最频繁的字符对为新符号
4. 重复步骤 2-3 直到达到目标词汇量

**优势：**

- 可以处理任意新词
- 词汇表大小可控
- 平衡字符级和词级表示

> 🎯 关键要点：BPE 是现代分词器的基础。
> GPT 使用 BPE，BERT 使用 WordPiece。
> 不同分词器的词汇量不同。

### 5. 解释位置编码的作用和不同类型。｜高级

位置编码为 Transformer 提供序列位置信息，因为自注意力机制本身不包含位置信息。

**常见类型：**

- **正弦位置编码**：使用正弦和余弦函数
- **可学习位置编码**：作为参数学习
- **相对位置编码**：编码相对距离
- **RoPE**：旋转位置编码，LLaMA 使用
- **ALiBi**：线性偏置注意力

```text
# 正弦位置编码
PE(pos, 2i) = sin(pos / 10000^(2i/d))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d))
```

> 🎯 关键要点：位置编码对长序列处理很重要。
> RoPE 支持长度外推。
> 不同模型使用不同的位置编码。

## 主题2：序列模型（5 题）

### 6. 解释 RNN 的原理及其局限性。｜中级

RNN（循环神经网络）通过隐藏状态处理序列数据，但存在梯度消失问题。

**RNN 公式：**

```text
h_t = tanh(W_hh h_{t-1} + W_xh x_t + b)
y_t = W_hy h_t + b_y
```

**局限性：**

- 梯度消失/爆炸问题
- 难以捕获长距离依赖
- 无法并行计算

> 🎯 关键要点：RNN 是序列模型的基础。
> LSTM/GRU 解决了部分问题。
> Transformer 已基本取代 RNN。

### 7. 解释 LSTM 的门机制。｜高级

LSTM 通过三个门（遗忘门、输入门、输出门）控制信息流，解决长距离依赖问题。

**门机制：**

```python
# 遗忘门：决定丢弃哪些信息
f_t = σ(W_f [h_{t-1}, x_t] + b_f)

# 输入门：决定添加哪些新信息
i_t = σ(W_i [h_{t-1}, x_t] + b_i)
c̃_t = tanh(W_c [h_{t-1}, x_t] + b_c)

# 输出门：决定输出哪些信息
o_t = σ(W_o [h_{t-1}, x_t] + b_o)

# 更新细胞状态
c_t = f_t * c_{t-1} + i_t * c̃_t
h_t = o_t * tanh(c_t)
```

> 🎯 关键要点：遗忘门是 LSTM 的核心创新。
> 细胞状态可以长期保存信息。
> GRU 是 LSTM 的简化版本。

### 8. 比较 LSTM 和 GRU 的区别。｜中级

GRU（Gated Recurrent Unit）是 LSTM 的简化版本，参数更少，训练更快。

| 特性 | LSTM | GRU |
|------|------|-----|
| 门数量 | 3 个（遗忘、输入、输出） | 2 个（重置、更新） |
| 参数量 | 较多 | 较少 |
| 细胞状态 | 有 | 无 |
| 训练速度 | 较慢 | 较快 |

> 🎯 关键要点：GRU 参数更少，训练更快。
> 效果通常相当。
> 选择取决于具体任务。

### 9. 什么是双向 RNN？它有什么优势？｜中级

双向 RNN 同时从前往后和从后往前处理序列，捕获更全面的上下文信息。

**结构：**

```text
# 正向RNN
h_t→ = f(W→ h_{t-1}→ + W_x→ x_t)

# 反向RNN
h_t← = f(W← h_{t+1}← + W_x← x_t)

# 合并
h_t = [h_t→; h_t←]
```

**优势：**

- 可以利用未来信息
- 适合需要全局信息的任务

> 🎯 关键要点：双向 RNN 不能用于自回归生成。
> BERT 使用双向 Transformer。
> GPT 使用单向 Transformer。

### 10. 解释 Seq2Seq 模型及其应用。｜中级

Seq2Seq（Sequence-to-Sequence）模型将一个序列映射到另一个序列，广泛用于机器翻译、文本摘要等任务。

**架构：**

- **编码器**：将输入序列编码为固定长度向量
- **解码器**：从向量生成输出序列

**注意力机制的引入：**

注意力机制允许解码器关注输入序列的不同部分，解决了信息瓶颈问题。

> 🎯 关键要点：Seq2Seq 是序列到序列任务的基础。
> 注意力机制是关键创新。
> Transformer 是 Seq2Seq 的现代实现。

## 主题3：NLP 任务（5 题）

### 11. 解释文本分类的常见方法。｜中级

文本分类是 NLP 的基础任务，有多种实现方法。

**常见方法：**

- **传统方法**：TF-IDF + SVM/朴素贝叶斯
- **深度学习**：CNN、RNN、LSTM
- **预训练模型**：BERT 微调
- **大模型**：LLM + Prompt

```python
# BERT微调示例
from transformers import BertForSequenceClassification

model = BertForSequenceClassification.from_pretrained('bert-base-chinese', num_labels=2)
outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
loss = outputs.loss
```

> 🎯 关键要点：BERT 微调是目前的主流方法。
> 小样本场景可以使用 LLM。
> 数据质量比模型选择更重要。

### 12. 什么是命名实体识别（NER）？｜中级

NER 是从文本中识别出人名、地名、组织名等实体的任务。

**标注方案：**

- **BIO**：B-实体开始，I-实体内部，O-非实体
- **BIOES**：增加 E-实体结束，S-单字实体

**常见方法：**

- CRF（条件随机场）
- BERT + CRF
- Span 抽取

> 🎯 关键要点：NER 是信息抽取的基础。
> 序列标注是最常用的方法。
> BERT + CRF 效果很好。

### 13. 解释文本生成中的解码策略。｜高级

解码策略决定了如何从模型的输出概率分布中选择 token。

**常见策略：**

- **贪心解码**：每次选择概率最高的 token
- **束搜索**：保留多个候选序列
- **采样**：按概率随机采样
- **Top-k 采样**：只从概率最高的 k 个 token 中采样
- **Top-p 采样**：从累积概率超过 p 的 token 中采样
- **Temperature**：调整概率分布的平滑度

```python
# Top-p采样
def top_p_sampling(logits, p=0.9):
    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
    # 移除累积概率超过p的token
    sorted_indices_to_remove = cumulative_probs > p
    # 保留第一个超过阈值的token
    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
    sorted_indices_to_remove[..., 0] = 0
    # 过滤logits
    indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
    logits[indices_to_remove] = float('-inf')
    return torch.multinomial(F.softmax(logits, dim=-1), num_samples=1)
```

> 🎯 关键要点：Temperature 控制创造性 vs 确定性。
> Top-p 通常比 Top-k 效果更好。
> 不同任务需要不同的解码策略。

### 14. 什么是文本相似度计算？有哪些方法？｜中级

文本相似度计算衡量两段文本的语义相似程度。

**常见方法：**

- **余弦相似度**：计算向量夹角
- **Jaccard 相似度**：基于词集合的交并比
- **编辑距离**：基于字符操作的相似度
- **语义相似度**：使用 Embedding 模型

```python
# 语义相似度计算
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["文本1", "文本2"])
similarity = cosine_similarity([embeddings[0]], [embeddings[1]])
```

> 🎯 关键要点：语义相似度比字面相似度更有意义。
> Embedding 模型是现代相似度计算的基础。
> 余弦相似度是最常用的度量。

### 15. 解释文本摘要的两种主要方法。｜中级

文本摘要分为抽取式和生成式两种方法。

**抽取式摘要：**

- 从原文中选择重要句子
- 方法：TextRank、BERT 抽取
- 优点：保持原文准确性
- 缺点：可能不够流畅

**生成式摘要：**

- 生成新的摘要文本
- 方法：Seq2Seq、BART、T5
- 优点：更流畅、概括性更强
- 缺点：可能产生幻觉

> 🎯 关键要点：生成式是目前的主流方向。
> 长文本摘要是挑战。
> 事实准确性是重要考量。
