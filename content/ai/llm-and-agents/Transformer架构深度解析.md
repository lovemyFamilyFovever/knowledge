---
title: "Transformer架构深度解析"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Transformer架构深度解析

## 概述

Transformer是2017年Google在论文《Attention Is All You Need》中提出的架构，彻底取代了RNN/CNN在NLP领域的统治地位。

## Self-Attention（自注意力）

**公式：** `Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V`

| 向量 | 含义 | 类比 |
|------|------|------|
| Q(Query) | 查询，"我在找什么" | 图书馆的问题 |
| K(Key) | 键，"我有什么标签" | 书的目录关键词 |
| V(Value) | 值，"我的实际内容" | 书的正文 |

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def forward(self, Q, K, V, mask=None):
        batch_size = Q.size(0)
        Q = self.W_q(Q).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        K = self.W_k(K).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = self.W_v(V).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        attn = torch.softmax(scores, dim=-1)
        output = torch.matmul(attn, V)
        output = output.transpose(1, 2).contiguous().view(batch_size, -1, self.n_heads * self.d_k)
        return self.W_o(output)
```

## 位置编码方案对比

| 方案 | 优点 | 缺点 | 代表模型 |
|------|------|------|----------|
| 正弦位置编码 | 简单可外推 | 外推效果有限 | 原始Transformer |
| 可学习位置编码 | 灵活 | 不能外推 | BERT, GPT-2 |
| RoPE旋转编码 | 相对位置，可外推 | 实现复杂 | LLaMA, Qwen |
| ALiBi | 极简外推好 | 信息有限 | BLOOM |

## Feed-Forward Network

`FFN(x) = max(0, xW1 + b1)W2 + b2`，中间维度通常是d_model的4倍。

## 完整前向传播流程

```
输入 -> Embedding + PosEncoding
     -> [Encoder Layer x N]
         -> Multi-Head Self-Attention -> Add&Norm
         -> FFN -> Add&Norm
     -> [Decoder Layer x N]
         -> Masked Self-Attention -> Add&Norm
         -> Cross-Attention -> Add&Norm
         -> FFN -> Add&Norm
     -> Linear -> Softmax -> 输出
```

## 计算复杂度

| 组件 | 时间复杂度 | 空间复杂度 |
|------|-----------|-----------|
| Self-Attention | O(n^2 * d) | O(n^2 + n*d) |
| FFN | O(n * d^2) | O(n * d) |

## Transformer 架构可视化

<svg viewBox="0 0 700 550" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;font-family:Arial,sans-serif">
  <rect width="700" height="550" fill="#f8fafc" rx="12"/>
  <text x="350" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#1e293b">Transformer 架构</text>
  <rect x="50" y="50" width="280" height="450" rx="8" fill="#dbeafe" stroke="#3b82f6" stroke-width="1" opacity="0.3"/>
  <text x="190" y="75" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e40af">Encoder (x6)</text>
  <rect x="370" y="50" width="280" height="450" rx="8" fill="#fef3c7" stroke="#f59e0b" stroke-width="1" opacity="0.3"/>
  <text x="510" y="75" text-anchor="middle" font-size="14" font-weight="bold" fill="#92400e">Decoder (x6)</text>
  <rect x="80" y="100" width="220" height="45" rx="6" fill="#93c5fd" stroke="#3b82f6"/>
  <text x="190" y="128" text-anchor="middle" font-size="12" fill="#1e3a8a">Multi-Head Self-Attention</text>
  <rect x="130" y="155" width="120" height="28" rx="4" fill="#bfdbfe"/>
  <text x="190" y="174" text-anchor="middle" font-size="11" fill="#1e40af">Add &amp; Norm</text>
  <rect x="80" y="195" width="220" height="45" rx="6" fill="#93c5fd" stroke="#3b82f6"/>
  <text x="190" y="223" text-anchor="middle" font-size="12" fill="#1e3a8a">Feed Forward Network</text>
  <rect x="130" y="250" width="120" height="28" rx="4" fill="#bfdbfe"/>
  <text x="190" y="269" text-anchor="middle" font-size="11" fill="#1e40af">Add &amp; Norm</text>
  <rect x="400" y="100" width="220" height="45" rx="6" fill="#fcd34d" stroke="#f59e0b"/>
  <text x="510" y="128" text-anchor="middle" font-size="12" fill="#78350f">Masked Self-Attention</text>
  <rect x="450" y="155" width="120" height="28" rx="4" fill="#fde68a"/>
  <text x="510" y="174" text-anchor="middle" font-size="11" fill="#92400e">Add &amp; Norm</text>
  <rect x="400" y="195" width="220" height="45" rx="6" fill="#fcd34d" stroke="#f59e0b"/>
  <text x="510" y="223" text-anchor="middle" font-size="12" fill="#78350f">Cross-Attention (K,V from Encoder)</text>
  <rect x="450" y="250" width="120" height="28" rx="4" fill="#fde68a"/>
  <text x="510" y="269" text-anchor="middle" font-size="11" fill="#92400e">Add &amp; Norm</text>
  <rect x="400" y="290" width="220" height="45" rx="6" fill="#fcd34d" stroke="#f59e0b"/>
  <text x="510" y="318" text-anchor="middle" font-size="12" fill="#78350f">Feed Forward Network</text>
  <rect x="450" y="345" width="120" height="28" rx="4" fill="#fde68a"/>
  <text x="510" y="364" text-anchor="middle" font-size="11" fill="#92400e">Add &amp; Norm</text>
  <rect x="130" y="400" width="120" height="35" rx="6" fill="#60a5fa"/>
  <text x="190" y="422" text-anchor="middle" font-size="11" fill="white">Input + PosEnc</text>
  <rect x="450" y="400" width="120" height="35" rx="6" fill="#f59e0b"/>
  <text x="510" y="422" text-anchor="middle" font-size="11" fill="white">Output + PosEnc</text>
  <rect x="450" y="460" width="120" height="35" rx="6" fill="#22c55e"/>
  <text x="510" y="482" text-anchor="middle" font-size="11" fill="white">Linear + Softmax</text>
  <line x1="190" y1="278" x2="190" y2="400" stroke="#64748b" stroke-width="2"/>
  <line x1="510" y1="373" x2="510" y2="400" stroke="#64748b" stroke-width="2"/>
  <line x1="510" y1="435" x2="510" y2="460" stroke="#64748b" stroke-width="2"/>
  <line x1="300" y1="218" x2="400" y2="218" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="350" y="212" text-anchor="middle" font-size="10" fill="#ef4444">K,V</text>
</svg>
