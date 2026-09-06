---
title: "MoE 混合专家模型"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# MoE 混合专家模型

## 概述
**MoE（Mixture of Experts）** 通过稀疏激活实现"大参数、小计算"——模型总参数量大，但每个token只激活一小部分参数。

## 核心原理
```
输入 → Router(门控网络) → 选择Top-K专家 → 加权输出

总参数: 671B (DeepSeek V3)
每token激活参数: 37B
计算效率: 接近37B模型，性能接近671B模型
```

## Switch Transformer
Google 2021年提出的简化MoE：
```python
class SwitchTransformer(nn.Module):
    def __init__(self, num_experts, d_model):
        self.experts = [FFN(d_model) for _ in range(num_experts)]
        self.router = nn.Linear(d_model, num_experts)

    def forward(self, x):
        # 计算路由权重
        router_logits = self.router(x)
        weights, indices = torch.topk(router_logits, k=1)  # Top-1路由
        weights = F.softmax(weights, dim=-1)

        # 只计算被选中的专家
        output = self.experts[indices](x) * weights
        return output
```

## Mixtral 架构
Mistral的MoE模型，8个专家每次激活2个：
```python
class MixtralBlock(nn.Module):
    def __init__(self):
        self.attention = MultiHeadAttention()
        self.experts = nn.ModuleList([FFN() for _ in range(8)])
        self.gate = nn.Linear(d_model, 8)

    def forward(self, x):
        h = self.attention(x)
        # Top-2路由
        gate_logits = self.gate(h)
        weights, indices = torch.topk(gate_logits, k=2)
        weights = F.softmax(weights, dim=-1)

        # 加权组合2个专家的输出
        expert_output = sum(
            w * self.experts[i](h)
            for w, i in zip(weights, indices)
        )
        return h + expert_output
```

## DeepSeek MoE
DeepSeek V3的创新MoE架构：
```
特点:
1. 细粒度专家: 256个小专家（而非8个大专家）
2. 共享专家: 1个始终激活的共享专家
3. 更细的路由: Top-6从256个中选择
```

## 主流MoE模型对比

| 模型 | 总参数 | 激活参数 | 专家数 | Top-K |
|------|--------|---------|--------|-------|
| Switch Transformer | 1.6T | ~100B | 128 | 1 |
| Mixtral 8x7B | 46.7B | 12.9B | 8 | 2 |
| DeepSeek V2 | 236B | 21B | 160 | 6 |
| DeepSeek V3 | 671B | 37B | 256 | 6 |
| Qwen MoE | 14.3B | 2.7B | 60 | 4 |

## 训练挑战

| 挑战 | 说明 | 解决方案 |
|------|------|---------|
| **负载均衡** | 部分专家过载 | 辅助损失函数 |
| **专家坍缩** | 大部分token路由到少数专家 | 路由正则化 |
| **通信开销** | 专家分布在不同GPU | 优化通信策略 |
| **训练不稳定** | 路由决策的离散性 | Z-loss正则化 |

```python
# 负载均衡损失
def load_balancing_loss(router_probs, expert_mask, num_experts):
    # 鼓励均匀路由
    fraction_tokens = expert_mask.float().mean(0)
    fraction_probs = router_probs.mean(0)
    balance_loss = num_experts * (fraction_tokens * fraction_probs).sum()
    return balance_loss
```

## 小结
MoE通过稀疏激活实现了参数效率的突破。DeepSeek V3的细粒度MoE设计代表了最新进展。MoE正在成为大模型的主流架构。
