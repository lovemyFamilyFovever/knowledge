---
tags: [AI资产, 大模型]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "artificialIntelligence/study.md"
---

# 大模型技术原理

> 从基础概念到核心技术，带你深入理解大语言模型的工作原理。

## 目录

- [基础概念](#基础概念)
- [模型架构](#模型架构)
- [训练技术](#训练技术)
- [推理优化](#推理优化)
- [评测与评估](#评测与评估)

---

## 基础概念

### 什么是大语言模型

大语言模型（Large Language Model，LLM）是一种基于深度学习的语言模型，其核心特征：

- **规模大**：参数数量从数十亿到数千亿不等
- **预训练**：在大规模无标注数据上学习通用知识
- **通用性**：通过提示词即可完成多种任务

### 涌现能力

当模型规模超过一定阈值时，会出现小模型不具备的能力：

- **思维链（Chain-of-Thought）**：逐步推理能力
- **上下文学习（In-Context Learning）**：通过示例学习新任务
- **指令遵循（Instruction Following）**：理解并执行复杂指令

---

## 模型架构

### Transformer

Transformer 是当今大模型的主流架构，由 Google 在 2017 年提出。

**核心组件**：
- **自注意力机制（Self-Attention）**：计算序列中每个 token 与其他 token 的关系
- **前馈网络（FFN）**：对每个位置的表示进行非线性变换
- **残差连接（Residual Connection）**：缓解梯度消失问题
- **层归一化（Layer Normalization）**：稳定训练过程

### 位置编码

Transformer 本身无法感知序列顺序，需要额外注入位置信息：

- **绝对位置编码**：Sinusoidal、Rotary Position Embedding（RoPE）
- **相对位置编码**：ALiBi、T5 Relative Attention

### 注意力变体

- **Multi-Query Attention（MQA）**：多头共享 K、V，减少推理显存
- **Grouped-Query Attention（GQA）**：分组共享 K、V，平衡效率和效果
- **Flash Attention**：IO 优化的注意力计算

---

## 训练技术

### 预训练

**目标**：在海量文本上预测下一个 token，学习通用语言知识

**数据处理**：
- 数据清洗（去重、过滤低质量内容）
- Tokenization（字节对编码 BPE、WordPiece）
- 数据混合策略（比例、领域分布）

**训练技巧**：
- 梯度累积（Gradient Accumulation）
- 混合精度训练（FP16/BF16）
- 分布式训练（数据并行、模型并行、流水线并行）

### 微调

**全参数微调（Full Fine-tuning）**：更新全部参数，适合数据量较大

**参数高效微调（PEFT）**：
- **LoRA**：低秩矩阵分解，减少可训练参数
- **Prefix Tuning**：在输入前添加可学习前缀
- **Prompt Tuning**：仅优化提示词向量
- **Adapter**：在 Transformer 层之间插入小型适配器

### RLHF

基于人类反馈的强化学习，让模型输出更符合人类偏好：

1. **SFT（监督微调）**：使用标注数据微调基座模型
2. **奖励模型（RM）**：训练一个奖励模型来评价生成质量
3. **PPO（近端策略优化）**：使用强化学习优化策略

### DPO

Direct Preference Optimization，直接优化人类偏好，无需显式的奖励模型：

$$
\nabla_\theta \mathcal{L}_{DPO} = - \mathbb{E}_{(x, y_w, y_l) \sim D} \left[ \log \sigma \left( r_\theta(x, y_w) - r_\theta(x, y_l) \right) \right]
$$

---

## 推理优化

### 量化

通过降低参数精度减少显存和加速推理：

- **PTQ（后训练量化）**：GPTQ、AWQ、GGML
- **QAT（量化感知训练）**：在训练中模拟量化效果

| 精度 | 显存降低 | 性能损失 |
|------|----------|----------|
| FP16 | 50% | 极小 |
| INT8 | 75% | 约 1-2% |
| INT4 | 87.5% | 约 2-5% |

### 投机解码

使用小模型预测多个 token，大模型验证并修正：

- **Speculative Decoding**
- **Eagle**
- **Medusa**

### KV Cache 优化

- **PagedAttention**（vLLM）：分页管理 KV 缓存，减少碎片
- **FlashDecoding**：分块加载 KV，提高长序列推理效率

---

## 评测与评估

### 评测维度

- **知识能力**：MMLU、CMMLU、C-Eval
- **推理能力**：GSM8K、BBH
- **代码能力**：HumanEval、MBPP
- **中文能力**：CLUE、SuperCLUE

### 评测方法

- **人工评估**：人工打分或排序
- **LLM 评估**：使用 GPT-4 等模型评估
- **自动化基准**：标准化测试集

---

## 总结

大模型技术涉及模型架构、训练算法、推理优化等多个维度。从 Transformer 到各种 Attention 变体，从预训练到 RLHF/DPO，从量化到投机解码，每一个环节都有大量值得深入研究的内容。

> 📝 内容持续更新中，欢迎补充指正。