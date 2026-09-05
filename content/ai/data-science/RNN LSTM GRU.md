---
title: "RNN/LSTM/GRU"
tags: []
source: "baike"
source_path: "开发术语 / 数据科学与大数据"
collected: "2026-09-05"
status: "imported"
---

# RNN/LSTM/GRU

## RNN（循环神经网络）

```python
# RNN前向传播
h_t = tanh(W_hh @ h_{t-1} + W_xh @ x_t + b)
```

**问题：** 长序列中梯度消失/爆炸（梯度需要连乘，指数衰减或增长）。

## LSTM（长短期记忆网络）

三个门控机制控制信息流：

```python
class LSTMCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        self.W = nn.Linear(input_size + hidden_size, 4 * hidden_size)

    def forward(self, x, h_prev, c_prev):
        gates = torch.sigmoid(self.W(torch.cat([x, h_prev], dim=1)))
        i, f, o, g = gates.chunk(4, dim=1)
        c_new = f * c_prev + i * torch.tanh(g)  # 遗忘旧信息 + 写入新信息
        h_new = o * torch.tanh(c_new)            # 输出
        return h_new, c_new
```

| 门 | 公式 | 作用 | 类比 |
|----|------|------|------|
| 遗忘门f | σ(W_f·[h,x]+b_f) | 决定丢弃什么 | 擦黑板 |
| 输入门i | σ(W_i·[h,x]+b_i) | 决定写入什么 | 写笔记 |
| 输出门o | σ(W_o·[h,x]+b_o) | 决定输出什么 | 回答问题 |
| 候选值g | tanh(W_g·[h,x]+b_g) | 候选新信息 | 新知识 |

## GRU（门控循环单元）

LSTM的简化版，合并遗忘门和输入门：

```python
# GRU
z = sigmoid(W_z @ [h, x])  # 更新门
r = sigmoid(W_r @ [h, x])  # 重置门
h_new = (1-z) * h + z * tanh(W @ [r*h, x])
```

| 特性 | LSTM | GRU |
|------|------|-----|
| 门数量 | 3个 | 2个 |
| 参数量 | 较多 | 较少 |
| 性能 | 长序列更好 | 短序列够用 |
| 训练速度 | 较慢 | 较快 |

## 双向RNN

```python
# 正向和反向分别编码，拼接
h_forward = rnn_forward(x)
h_backward = rnn_backward(x[::-1])
h_concat = torch.cat([h_forward, h_backward], dim=-1)
```

## RNN vs Transformer

| 特性 | RNN/LSTM | Transformer |
|------|----------|-------------|
| 长距离依赖 | 弱（梯度消失） | 强（直接注意力） |
| 并行化 | 不可（串行） | 可（并行） |
| 训练速度 | 慢 | 快 |
| 内存 | O(n) | O(n^2) |
| 推理效率 | O(n)逐步 | O(1)并行(需KV Cache) |
| 适用场景 | 小数据/流式 | 大数据/长序列 |

## 实际应用

| 任务 | 模型选择 | 原因 |
|------|----------|------|
| 实时语音识别 | LSTM | 流式处理 |
| 机器翻译 | Transformer | 长依赖+并行 |
| 情感分析 | BERT(Transformer) | 预训练优势 |
| 股票预测 | LSTM+Attention | 时序+重要时刻 |
