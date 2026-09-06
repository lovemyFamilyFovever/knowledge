---
title: "Scaling Law"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Scaling Law

## 概述
**Scaling Law** 描述了模型性能与计算预算、数据量、参数量之间的幂律关系。

## Chinchilla 定律
DeepMind 2022年提出的最优训练配比：
```
最优参数: N ∝ C^0.5 (参数量与计算量的平方根成正比)
最优数据: D ∝ C^0.5 (数据量与计算量的平方根成正比)
最优比例: D ≈ 20N (每个参数约需20个token)
```

## Scaling Law 公式
```
L(N, D) = (Nc/N)^αN + (Dc/D)^αD + L∞

L: 损失
N: 参数量
D: 数据量
C: 计算量 (≈6ND)
αN ≈ 0.076, αD ≈ 0.095
```

## 计算预算分配

| 总算力(FLOPs) | 最优参数量 | 最优数据量 | 模型示例 |
|---------------|-----------|-----------|---------|
| 1e21 | 400M | 8B tokens | GPT-2 Small |
| 1e22 | 1B | 20B tokens | - |
| 1e23 | 3B | 60B tokens | - |
| 1e24 | 10B | 200B tokens | Llama-7B |
| 1e25 | 30B | 600B tokens | - |
| 1e26 | 70B | 1.4T tokens | Llama-70B |

## Emergent Abilities（涌现能力）
某些能力只在模型达到一定规模后突然出现：
```
参数量: 100M → 1B → 10B → 100B → 1T
能力:    无 → 简单问答 → 推理 → 复杂推理 → 接近人类
                 ↑                ↑
              涌现点1          涌现点2
```

## 训练效率优化

| 技术 | 效果 | 说明 |
|------|------|------|
| **混合精度** | 2x | FP16/BF16训练 |
| **梯度累积** | 减少显存 | 模拟大batch |
| **数据并行** | N倍 | 多GPU并行 |
| **张量并行** | 减少显存 | 层内并行 |
| **流水线并行** | 减少显存 | 层间并行 |

## 小结
Scaling Law为模型训练提供了理论指导：给定算力预算，应如何分配参数量和数据量。Chinchilla定律表明，许多模型训练是under-trained的。
