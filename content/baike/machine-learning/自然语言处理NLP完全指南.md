---
title: "自然语言处理NLP完全指南"
tags: []
source: "baike"
source_path: "技术文章 / AI与机器学习"
collected: "2026-09-05"
status: "imported"
---

# 自然语言处理NLP完全指南


> 📌 **导航**：本文是 **自然语言处理NLP完全指南** 词条，属于 machine-learning 术语集。相关枢纽：[[LLM应用开发完全指南]]、[[强化学习从入门到实践]]、[[自然语言处理NLP完全指南]]、[[计算机视觉入门到实战]]。

## NLP完全指南：从基础原理到大语言模型实战

## 1. 文本预处理

### 1.1 分词（Tokenization）

**中文分词挑战**：
中文没有天然的空格分隔，需要专门算法识别词语边界。分词是NLP的基石，直接影响后续所有任务。

**常用算法**：
- **基于词典的分词**：最大匹配法（正向/逆向/双向）
- **基于统计的分词**：隐马尔可夫模型（HMM）、条件随机场（CRF）
- **深度学习分词**：BiLSTM-CRF

**实战案例 - 使用jieba分词**：
```python
import jieba
import jieba.posseg as pseg

text = "自然语言处理是人工智能领域的重要方向"

# 基础分词
words = jieba.lcut(text)
print("基础分词:", words)
# ['自然语言', '处理', '是', '人工智能', '领域', '的', '重要', '方向']

# 精确模式 vs 搜索引擎模式
words_exact = jieba.lcut(text, cut_all=False)
words_search = jieba.lcut_for_search(text)
print("精确模式:", words_exact)
print("搜索模式:", words_search)

# 自定义词典
jieba.add_word("自然语言处理", freq=1000, tag='n')
words_custom = jieba.lcut("我正在学习自然语言处理技术")
print("自定义词典分词:", words_custom)
# ['我', '正在', '学习', '自然语言处理', '技术']
```

### 1.2 词性标注（Part-of-Speech Tagging）

**词性体系**：
- 名词(n)、动词(v)、形容词(a)、副词(d)、介词(p)等
- 不同语料库有不同的标注体系，如CTB、PKU、ICTCLAS

**标注算法**：
1. **规则方法**：基于语言学规则
2. **统计方法**：HMM、最大熵模型
3. **深度学习**：BiLSTM、Transformer

**代码示例**：
```python
import spacy
from spacy import displacy

# 加载英文模型
nlp = spacy.load("en_core_web_sm")
text = "Apple is looking at buying U.K. startup for $1 billion"
doc = nlp(text)

# 词性标注
print("词性标注结果:")
for token in doc:
    print(f"{token.text:12} {token.pos_:6} {token.tag_:6} {spacy.explain(token.tag_)}")

# 可视化
displacy.serve(doc, style="dep", port=5000)

# 中文词性标注（使用jieba）
import jieba.posseg as pseg
text_cn = "我喜欢在苹果电脑上使用Python编程"
words = pseg.lcut(text_cn)
print("\n中文词性标注:")
for word, flag in words:
    print(f"{word:6} {flag}")
```

### 1.3 命名实体识别（NER）

**NER任务定义**：
识别文本中具有特定意义的实体，如人名、地名、机构名、时间等。

**主流方法**：
1. **传统方法**：基于规则、词典匹配
2. **统计方法**：CRF、SVM
3. **深度学习**：BiLSTM-CRF、BERT-CRF

**CoNLL-2003数据集标签**：
- PER（人名）
- LOC（地名）
- ORG（机构名）
- MISC（其他）

**实战示例**：
```python
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
from transformers import pipeline

# 使用预训练BERT模型进行NER
tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")

nlp = pipeline("ner", model=model, tokenizer=tokenizer)

text = "Apple is planning to open a new store in San Francisco next month"
results = nlp(text)

print("NER结果:")
for entity in results:
    print(f"实体: {entity['word']:15} 类型: {entity['entity']:6} 分数: {entity['score']:.3f}")

# 输出示例:
# 实体: Apple           类型: B-ORG  分数: 0.998
# 实体: San             类型: B-LOC  分数: 0.999
# 实体: Francisco       类型: I-LOC  分数: 0.999
```

## 2. 词向量（Word Embeddings）

### 2.1 Word2Vec

**两种架构**：
1. **CBOW（连续词袋）**：通过上下文预测中心词
2. **Skip-gram**：通过中心词预测上下文

**训练目标**：
最大化对数似然函数：
$$
\mathcal{L} = \sum_{t=1}^{T} \sum_{-m \leq j \leq m, j \neq 0} \log P(w_{t+j} | w_t)
$$

**实现代码**：
```python
from gensim.models import Word2Vec
import numpy as np

# 准备语料
sentences = [
    ['natural', 'language', 'processing', 'is', 'fun'],
    ['machine', 'learning', 'is', 'powerful'],
    ['deep', 'learning', 'revolution', 'ai'],
    ['word', 'embeddings', 'capture', 'semantics'],
    ['neural', 'networks', 'learn', 'patterns']
]

# 训练Word2Vec模型
model = Word2Vec(
    sentences,
    vector_size=100,      # 词向量维度
    window=5,             # 上下文窗口大小
    min_count=1,          # 最小词频
    sg=1,                 # 1: Skip-gram, 0: CBOW
    workers=4,
    epochs=100
)

# 获取词向量
print("Word2Vec向量维度:", model.wv.vector_size)
print("'learning'的向量:", model.wv['learning'][:10])

# 相似词查找
print("\n与'learning'最相似的词:")
for word, similarity in model.wv.most_similar('learning', topn=3):
    print(f"{word}: {similarity:.3f}")

# 词向量运算 - 经典例子: king - man + woman ≈ queen
try:
    result = model.wv.most_similar(
        positive=['king', 'woman'],
        negative=['man'],
        topn=1
    )
    print(f"\nking - man + woman ≈ {result[0][0]}")
except KeyError:
    print("词汇表中缺少某些词")
```

### 2.2 GloVe（Global Vectors）

**核心思想**：
结合全局矩阵分解和局部上下文窗口的优势，基于词共现矩阵。

**共现概率**：
$$
P_{ij} = \frac{X_{ij}}{X_i} = \frac{\text{词}j\text{出现在词}i\text{上下文的次数}}{\text{词}i\text{出现的总次数}}
$$

**训练目标**：
最小化加权最小二乘损失：
$$
J = \sum_{i,j=1}^{V} f(X_{ij})(w_i^T \tilde{w}_j + b_i + \tilde{b}_j - \log X_{ij})^2
$$

**GloVe与Word2Vec对比**：
```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 加载预训练GloVe向量（示例数据）
def load_glove(path):
    embeddings_dict = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            values = line.split()
            word = values[0]
            vector = np.asarray(values[1:], "float32")
            embeddings_dict[word] = vector
    return embeddings_dict

# 模拟GloVe向量
glove_vectors = {
    'king': np.array([0.2, 0.4, 0.1, 0.8]),
    'queen': np.array([0.3, 0.5, 0.2, 0.7]),
    'man': np.array([0.1, 0.3, 0.0, 0.6]),
    'woman': np.array([0.4, 0.6, 0.3, 0.5])
}

# 计算相似度
def cosine_sim(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

print("GloVe向量相似度:")
print(f"king - queen: {cosine_sim(glove_vectors['king'], glove_vectors['queen']):.3f}")
print(f"king - man: {cosine_sim(glove_vectors['king'], glove_vectors['man']):.3f}")

# 词向量平均
sentence = "the king and queen"
words = sentence.split()
word_vecs = [glove_vectors.get(w, np.zeros(4)) for w in words]
sentence_vector = np.mean(word_vecs, axis=0)
print(f"句子平均向量: {sentence_vector}")
```

### 2.3 FastText

**创新点**：
1. **子词信息**：将词拆分为字符n-gram
2. **形态学建模**：特别适合形态丰富的语言
3. **OOV处理**：可以通过子词构建未登录词向量

**FastText vs Word2Vec**：
- Word2Vec: 每个词一个向量
- FastText: 词向量 = 子词向量之和

```python
from gensim.models import FastText

# 训练FastText模型
model_ft = FastText(
    sentences,
    vector_size=100,
    window=5,
    min_count=1,
    min_n=2,       # 最小n-gram长度
    max_n=5,       # 最大n-gram长度
    sg=1,
    workers=4,
    epochs=100
)

# FastText处理未登录词
oov_word = "unfriendliness"
if oov_word not in model_ft.wv:
    print(f"'{oov_word}'不在词汇表中，但FastText可以生成向量")
    vector = model_ft.wv[oov_word]  # 通过子词信息生成
    print(f"生成的向量维度: {len(vector)}")

# 形态学分析
print("\nFastText子词信息:")
word = "unfriendliness"
subwords = model_ft.wv.get_subwords(word)
print(f"词'{word}'的子词:", subwords[0][:5])  # 显示前5个子词
```

## 3. 语言模型演进

### 3.1 N-gram语言模型

**N-gram原理**：
基于马尔可夫假设，下一个词只依赖于前n-1个词：
$$
P(w_n | w_1, ..., w_{n-1}) \approx P(w_n | w_{n-N+1}, ..., w_{n-1})
$$

**平滑技术**：
1. **加法平滑（Laplace）**：$P_{add}(w_i|w_{i-1}) = \frac{c(w_{i-1}, w_i) + \alpha}{c(w_{i-1}) + \alpha V}$
2. **Kneser-Ney平滑**：考虑低阶模型中的概率分布

```python
import nltk
from nltk import bigrams, trigrams
from collections import Counter, defaultdict
import numpy as np

class NgramLanguageModel:
    def __init__(self, n=2):
        self.n = n
        self.ngrams = defaultdict(Counter)
        self.context_counts = Counter()
    
    def train(self, corpus):
        """训练N-gram模型"""
        for sentence in corpus:
            tokens = ['<s>'] * (self.n - 1) + sentence + ['</s>']
            for ngram in zip(*[tokens[i:] for i in range(self.n)]):
                context = tuple(ngram[:-1])
                word = ngram[-1]
                self.ngrams[context][word] += 1
                self.context_counts[context] += 1
    
    def probability(self, context, word, alpha=0.01):
        """计算条件概率（带平滑）"""
        context = tuple(context[-(self.n-1):])
        count = self.ngrams[context].get(word, 0)
        total = self.context_counts[context]
        vocab_size = len(set(w for cnt in self.ngrams.values() for w in cnt))
        
        # Laplace平滑
        return (count + alpha) / (total + alpha * vocab_size)
    
    def generate_text(self, start_tokens, length=10):
        """生成文本"""
        current = list(start_tokens[-(self.n-1):])
        generated = list(start_tokens)
        
        for _ in range(length):
            context = tuple(current[-(self.n-1):])
            word_probs = {}
            for word in set(w for cnt in self.ngrams.values() for w in cnt):
                word_probs[word] = self.probability(context, word)
            
            # 选择概率最高的词
            next_word = max(word_probs, key=word_probs.get)
            generated.append(next_word)
            current.append(next_word)
            
            if next_word == '</s>':
                break
        
        return generated

# 示例语料
corpus = [
    ['the', 'cat', 'sat', 'on', 'the', 'mat'],
    ['the', 'dog', 'lay', 'on', 'the', 'rug'],
    ['a', 'cat', 'played', 'with', 'a', 'ball'],
    ['the', 'dog', 'barked', 'at', 'the', 'cat']
]

# 训练三元模型
trigram_model = NgramLanguageModel(n=3)
trigram_model.train(corpus)

# 生成文本
start = ['the', 'cat']
generated = trigram_model.generate_text(start, length=5)
print("生成的文本:", ' '.join(generated))
```

### 3.2 RNN语言模型

**循环神经网络结构**：
$$
h_t = \tanh(W_{hh}h_{t-1} + W_{xh}x_t + b_h)
$$
$$
P(w_t | w_{<t}) = \text{softmax}(W_{ho}h_t + b_o)
$$

**梯度消失/爆炸问题**：
- 梯度消失：$||\frac{\partial h_t}{\partial h_k}|| \leq \gamma^{t-k}$
- 需要门控机制：LSTM、GRU

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class RNNLanguageModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers=1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.rnn = nn.RNN(embed_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)
        self.hidden_dim = hidden_dim
    
    def forward(self, x, hidden=None):
        # x: (batch_size, seq_len)
        embeds = self.embedding(x)  # (batch_size, seq_len, embed_dim)
        output, hidden = self.rnn(embeds, hidden)  # (batch_size, seq_len, hidden_dim)
        logits = self.fc(output)  # (batch_size, seq_len, vocab_size)
        return logits, hidden
    
    def generate(self, start_token, length, temperature=1.0):
        """生成序列"""
        self.eval()
        tokens = [start_token]
        hidden = None
        
        with torch.no_grad():
            for _ in range(length):
                x = torch.tensor([[tokens[-1]]])
                logits, hidden = self(x, hidden)
                logits = logits[:, -1, :] / temperature
                
                # 采样
                probs = torch.softmax(logits, dim=-1)
                next_token = torch.multinomial(probs, 1).item()
                tokens.append(next_token)
        
        return tokens

# 示例使用
vocab_size = 10000
model = RNNLanguageModel(vocab_size, embed_dim=128, hidden_dim=256)
print(f"模型参数量: {sum(p.numel() for p in model.parameters()):,}")
```

### 3.3 Transformer架构

**核心创新**：
1. **自注意力机制**：$\text{Attention}(Q,K,V) = \text{softmax}(\frac{QK^T}{\sqrt{d_k}})V$
2. **位置编码**：$PE_{(pos,2i)} = \sin(pos/10000^{2i/d_{model}})$
3. **多头注意力**：$\text{MultiHead}(Q,K,V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$

```python
import torch
import torch.nn as nn
import math

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads, dropout=0.1):
        super().__init__()
        assert d_model % num_heads == 0
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
    
    def scaled_dot_product_attention(self, Q, K, V, mask=None):
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attn_weights = torch.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        return torch.matmul(attn_weights, V), attn_weights
    
    def forward(self, Q, K, V, mask=None):
        batch_size = Q.size(0)
        
        # 线性变换并分头
        Q = self.W_q(Q).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(K).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(V).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        
        # 注意力计算
        attn_output, attn_weights = self.scaled_dot_product_attention(Q, K, V, mask)
        
        # 合并多头
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        output = self.W_o(attn_output)
        
        return output, attn_weights

# Transformer编码器层
class TransformerEncoderLayer(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, num_heads, dropout)
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x, mask=None):
        # 自注意力
        attn_output, _ = self.self_attn(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_output))
        
        # 前馈网络
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))
        
        return x

# 测试Transformer
d_model = 512
num_heads = 8
encoder_layer = TransformerEncoderLayer(d_model, num_heads, d_ff=2048)

# 创建示例输入
batch_size, seq_len = 2, 10
x = torch.randn(batch_size, seq_len, d_model)
output = encoder_layer(x)

print(f"输入形状: {x.shape}")
print(f"输出形状: {output.shape}")
```

## 4. 文本分类

### 4.1 情感分析

**任务定义**：
判断文本表达的情感倾向（正面/负面/中性）

**方法演进**：
1. **基于规则**：情感词典 + 否定词处理
2. **机器学习**：朴素贝叶斯、SVM、随机森林
3. **深度学习**：CNN、RNN、Transformer

```python
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import BertTokenizer, BertForSequenceClassification
import pandas as pd
from sklearn.model_selection import train_test_split

# 情感分析数据集
class SentimentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(self.labels[idx], dtype=torch.long)
        }

# 使用BERT进行情感分析
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained(
    'bert-base-uncased',
    num_labels=2  # 二分类：正面/负面
)

# 示例数据
texts = [
    "This movie is absolutely fantastic!",
    "I really hated this product, it was terrible.",
    "The food was okay, nothing special.",
    "Best experience I've ever had!"
]
labels = [1, 0, 0, 1]  # 1:正面, 0:负面

# 训练准备
train_dataset = SentimentDataset(texts, labels, tokenizer)
train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True)

# 训练循环（简化版）
optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
criterion = torch.nn.CrossEntropyLoss()

for epoch in range(3):
    model.train()
    total_loss = 0
    
    for batch in train_loader:
        outputs = model(
            input_ids=batch['input_ids'],
            attention_mask=batch['attention_mask'],
            labels=batch['labels']
        )
        
        loss = outputs.loss
        total_loss += loss.item()
        
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
    
    print(f"Epoch {epoch+1}, Loss: {total_loss/len(train_loader):.4f}")

# 预测函数
def predict_sentiment(text, model, tokenizer):
    model.eval()
    encoding = tokenizer(text, return_tensors='pt', max_length=128, truncation=True)
    
    with torch.no_grad():
        outputs = model(**encoding)
        prediction = torch.argmax(outputs.logits, dim=1).item()
    
    return "正面" if prediction == 1 else "负面"

# 测试预测
test_text = "I love this restaurant, the service was amazing!"
print(f"文本: {test_text}")
print(f"情感: {predict_sentiment(test_text, model, tokenizer)}")
```

### 4.2 主题分类

**任务定义**：
将文档分配到预定义的主题类别

**经典数据集**：20 Newsgroups、AG News、DBpedia

**LDA主题模型**：
```python
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np

# 示例文档
documents = [
    "machine learning algorithms neural networks deep learning",
    "football soccer world cup championship tournament",
    "cooking recipes ingredients food preparation kitchen",
    "stock market financial trading investments economy",
    "tennis racket match grand slam tournament player",
    "baking cake cookies oven dessert sweet",
    "artificial intelligence robotics automation technology",
    "basketball NBA championship playoffs finals"
]

# 文档-词矩阵
vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words='english')
doc_term_matrix = vectorizer.fit_transform(documents)

# LDA模型
num_topics = 3
lda = LatentDirichletAllocation(
    n_components=num_topics,
    max_iter=20,
    learning_method='online',
    random_state=42
)

lda.fit(doc_term_matrix)

# 显示主题
feature_names = vectorizer.get_feature_names_out()
for topic_idx, topic in enumerate(lda.components_):
    print(f"主题 {topic_idx}:")
    top_words_idx = topic.argsort()[:-6:-1]
    top_words = [feature_names[i] for i in top_words_idx]
    print(f"  关键词: {', '.join(top_words)}")

# 文档主题分布
doc_topics = lda.transform(doc_term_matrix)
print("\n文档主题分布:")
for i, doc in enumerate(documents):
    print(f"文档 {i}: {doc_topics[i].round(2)}")
```

## 5. 序列标注

### 5.1 命名实体识别（NER）

**BIO标注体系**：
- B-PER：人名开始
- I-PER：人名内部
- O：非实体

**BiLSTM-CRF模型**：
```python
import torch
import torch.nn as nn
from torchcrf import CRF

class BiLSTMCRF(nn.Module):
    def __init__(self, vocab_size, tag_to_ix, embedding_dim, hidden_dim, num_layers=1):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.vocab_size = vocab_size
        self.tag_to_ix = tag_to_ix
        self.tagset_size = len(tag_to_ix)
        
        self.word_embeds = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(
            embedding_dim, 
            hidden_dim // 2,
            num_layers=num_layers,
            bidirectional=True,
            batch_first=True
        )
        self.hidden2tag = nn.Linear(hidden_dim, self.tagset_size)
        
        # CRF层
        self.crf = CRF(self.tagset_size, batch_first=True)
    
    def _get_emissions(self, sentence):
        embeds = self.word_embeds(sentence)
        lstm_out, _ = self.lstm(embeds)
        emissions = self.hidden2tag(lstm_out)
        return emissions
    
    def forward(self, sentence, tags=None, mask=None):
        emissions = self._get_emissions(sentence)
        
        if tags is not None:
            # 训练模式：计算损失
            loss = -self.crf(emissions, tags, mask=mask, reduction='mean')
            return loss
        else:
            # 预测模式：解码最佳序列
            best_tags = self.crf.decode(emissions, mask=mask)
            return best_tags

# 示例使用
tag_to_ix = {"O": 0, "B-PER": 1, "I-PER": 2, "B-LOC": 3, "I-LOC": 4}
vocab_size = 10000

model = BiLSTMCRF(vocab_size, tag_to_ix, embedding_dim=128, hidden_dim=256)
print(f"模型参数量: {sum(p.numel() for p in model.parameters()):,}")

# 示例输入
batch_size, seq_len = 2, 10
x = torch.randint(0, vocab_size, (batch_size, seq_len))
tags = torch.randint(0, len(tag_to_ix), (batch_size, seq_len))
mask = torch.ones(batch_size, seq_len, dtype=torch.bool)

# 计算损失
loss = model(x, tags, mask)
print(f"CRF损失: {loss.item():.4f}")

# 预测
predictions = model(x, mask=mask)
print(f"预测结果形状: {len(predictions[0])}")
```

### 5.2 词性标注（POS Tagging）

**使用Hugging Face Transformers**：
```python
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch

# 加载预训练的词性标注模型
tokenizer = AutoTokenizer.from_pretrained("vblagoje/bert-english-uncased-finetuned-pos")
model = AutoModelForTokenClassification.from_pretrained("vblagoje/bert-english-uncased-finetuned-pos")

# POS标签映射
pos_labels = ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", 
              "NUM", "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB", "X"]

def pos_tag_sentence(sentence):
    inputs = tokenizer(sentence, return_tensors="pt", is_split_into_words=False)
    
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.argmax(outputs.logits, dim=2)
    
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    predicted_tags = [pos_labels[pred] for pred in predictions[0].numpy()]
    
    # 对齐subword tokens
    aligned_results = []
    current_word = ""
    current_tag = ""
    
    for token, tag in zip(tokens, predicted_tags):
        if token.startswith("##"):
            current_word += token[2:]
        else:
            if current_word:
                aligned_results.append((current_word, current_tag))
            current_word = token
            current_tag = tag
    
    if current_word:
        aligned_results.append((current_word, current_tag))
    
    return aligned_results

# 测试
sentence = "The quick brown fox jumps over the lazy dog."
results = pos_tag_sentence(sentence)

print(f"句子: {sentence}")
print("词性标注结果:")
for word, tag in results:
    if word not in ["[CLS]", "[SEP]", "[PAD]"]:
        print(f"  {word:10} {tag}")
```

## 6. 机器翻译

### 6.1 Seq2Seq模型

**编码器-解码器架构**：
```python
import torch
import torch.nn as nn
import random

class Encoder(nn.Module):
    def __init__(self, input_dim, emb_dim, hidden_dim, num_layers, dropout):
        super().__init__()
        self.embedding = nn.Embedding(input_dim, emb_dim)
        self.rnn = nn.LSTM(emb_dim, hidden_dim, num_layers, 
                          dropout=dropout, batch_first=True)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, src):
        # src: (batch_size, src_len)
        embedded = self.dropout(self.embedding(src))  # (batch_size, src_len, emb_dim)
        outputs, (hidden, cell) = self.rnn(embedded)  # outputs: (batch_size, src_len, hidden_dim)
        return hidden, cell

class Decoder(nn.Module):
    def __init__(self, output_dim, emb_dim, hidden_dim, num_layers, dropout):
        super().__init__()
        self.embedding = nn.Embedding(output_dim, emb_dim)
        self.rnn = nn.LSTM(emb_dim, hidden_dim, num_layers,
                          dropout=dropout, batch_first=True)
        self.fc_out = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, trg, hidden, cell):
        # trg: (batch_size, 1)
        embedded = self.dropout(self.embedding(trg))  # (batch_size, 1, emb_dim)
        output, (hidden, cell) = self.rnn(embedded, (hidden, cell))
        prediction = self.fc_out(output.squeeze(1))  # (batch_size, output_dim)
        return prediction, hidden, cell

class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder, device):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.device = device
    
    def forward(self, src, trg, teacher_forcing_ratio=0.5):
        batch_size = src.shape[0]
        trg_len = trg.shape[1]
        trg_vocab_size = self.decoder.fc_out.out_features
        
        # 存储解码器输出
        outputs = torch.zeros(batch_size, trg_len, trg_vocab_size).to(self.device)
        
        # 编码器输出
        hidden, cell = self.encoder(src)
        
        # 第一个输入是<sos> token
        input = trg[:, 0]
        
        for t in range(1, trg_len):
            output, hidden, cell = self.decoder(input, hidden, cell)
            outputs[:, t] = output
            
            # Teacher forcing
            teacher_force = random.random() < teacher_forcing_ratio
            top1 = output.argmax(1)
            input = trg[:, t] if teacher_force else top1
        
        return outputs

# 参数设置
INPUT_DIM = 5000   # 源语言词汇量
OUTPUT_DIM = 5000  # 目标语言词汇量
EMB_DIM = 256
HIDDEN_DIM = 512
NUM_LAYERS = 2
DROPOUT = 0.5
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 创建模型
enc = Encoder(INPUT_DIM, EMB_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT)
dec = Decoder(OUTPUT_DIM, EMB_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT)
model = Seq2Seq(enc, dec, device).to(device)

# 参数初始化
def init_weights(m):
    for name, param in m.named_parameters():
        nn.init.uniform_(param, -0.08, 0.08)

model.apply(init_weights)
print(f"模型参数量: {sum(p.numel() for p in model.parameters()):,}")
```

### 6.2 注意力机制

**Bahdanau注意力**：
$$
e_{ij} = v^T \tanh(W_1 h_i + W_2 s_j)
$$
$$
\alpha_{ij} = \frac{\exp(e_{ij})}{\sum_{k=1}^{T_x} \exp(e_{ik})}
$$
$$
c_i = \sum_{j=1}^{T_x} \alpha_{ij} h_j
$$

```python
class BahdanauAttention(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.W1 = nn.Linear(hidden_dim, hidden_dim)
        self.W2 = nn.Linear(hidden_dim, hidden_dim)
        self.V = nn
```

## 相关术语

[[2026年AI技术全景图]]、[[AI是否会取代人类辩论]]、[[Dropout]]、[[K均值聚类]]、[[K近邻算法]]、[[LLM应用开发完全指南]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
