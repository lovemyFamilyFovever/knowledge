---
title: "GPT系列模型演进"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# GPT系列模型演进

| 模型 | 年份 | 参数量 | 关键创新 |
|------|------|--------|----------|
| GPT-1 | 2018 | 117M | 预训练+微调范式 |
| GPT-2 | 2019 | 1.5B | Zero-shot能力 |
| GPT-3 | 2020 | 175B | In-context Learning |
| InstructGPT | 2022 | 175B | RLHF对齐 |
| GPT-4 | 2023 | ~1.8T(MoE) | 多模态，推理大幅提升 |
| GPT-4o | 2024 | - | 原生多模态 |

## InstructGPT训练流程

```
Step 1: SFT - 人工示范回答 -> 微调GPT-3
Step 2: RM - 人工排序多个回答 -> 训练奖励模型
Step 3: PPO - 用奖励模型分数 -> PPO优化策略
```

## Scaling Law与涌现能力

Kaplan发现：L(N) ∝ N^(-0.076)，Chinchilla定律建议模型大小与数据量等比增长。

涌现能力（超过阈值突然出现）：Chain-of-Thought推理、多步数学、代码生成、指令遵循。
