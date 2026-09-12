---
title: "GPT系列模型演进"
tags: [人工智能, 模型]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# GPT系列模型演进


> 📌 **导航**：本文是 **GPT系列模型演进** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

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

## 相关术语

[[大语言模型架构演进]]、[[Transformer架构深度解析]]、[[大模型基础术语详解]]、[[强化学习基础]]、[[多模态大模型]]、[[注意力机制]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
