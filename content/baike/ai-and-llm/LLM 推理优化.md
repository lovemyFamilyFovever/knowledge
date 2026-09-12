---
title: "LLM 推理优化"
tags: [人工智能, 推理优化]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# LLM 推理优化


> 📌 **导航**：本文是 **LLM 推理优化** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## 概述
LLM推理优化旨在降低延迟和成本。本文介绍关键技术：KV Cache、FlashAttention、量化和投机采样。

## KV Cache
在自回归生成中缓存已计算的Key-Value，避免重复计算：
```python
# 无KV Cache: 每步重新计算所有token的K,V → O(n^2)
# 有KV Cache: 只计算新token的K,V → O(n)
# 内存占用: 2 * num_layers * hidden_dim * seq_len * batch_size * precision_bytes
```

## FlashAttention
通过IO感知的分块计算，减少HBM访问次数：
```
传统Attention: O(N^2) 内存, 多次HBM读写
FlashAttention: O(N) 内存, 分块计算减少HBM访问
加速比: 2-4x, 内存节省: 5-20x
```

## 模型量化

| 方法 | 位数 | 精度损失 | 速度提升 | 工具 |
|------|------|---------|---------|------|
| **GPTQ** | 4-bit | 极小 | 2-3x | AutoGPTQ |
| **AWQ** | 4-bit | 极小 | 2-3x | AutoAWQ |
| **GGUF** | 2-8bit | 可调 | 2-4x | llama.cpp |
| **FP8** | 8-bit | 无 | 1.5x | TensorRT-LLM |
| **INT8** | 8-bit | 极小 | 1.5x | bitsandbytes |

```python
# GPTQ量化示例
from transformers import AutoModelForCausalLM, GPTQConfig

quantization_config = GPTQConfig(bits=4, dataset='c4', group_size=128)
model = AutoModelForCausalLM.from_pretrained(
    'model_name', quantization_config=quantization_config
)
```

## vLLM 高性能推理引擎
```python
from vllm import LLM, SamplingParams

llm = LLM(model='meta-llama/Llama-3-8B', tensor_parallel_size=2)
params = SamplingParams(temperature=0.7, max_tokens=512)
outputs = llm.generate(['什么是AI Agent？'], params)
# PagedAttention: 动态分配KV Cache内存，吞吐量提升2-4x
```

## 投机采样（Speculative Decoding）
用小模型快速生成草稿，大模型并行验证：
```python
# 小模型(快)生成5个token → 大模型(准)一次验证 → 接受匹配的token
# 加速比: 2-3x (保持输出质量不变)
```

## 推理优化技术对比

| 技术 | 加速比 | 精度影响 | 实现复杂度 |
|------|--------|---------|-----------|
| **KV Cache** | 2-10x | 无 | 低 |
| **FlashAttention** | 2-4x | 无 | 中 |
| **INT8量化** | 1.5x | 极小 | 低 |
| **4-bit量化** | 2-3x | 小 | 低 |
| **投机采样** | 2-3x | 无 | 高 |
| **PagedAttention** | 2-4x | 无 | 中 |

## 小结
推理优化是LLM生产部署的关键。KV Cache和FlashAttention是标配，量化降低资源需求，投机采样和vLLM提升吞吐量。

## 相关术语

[[大模型基础术语详解]]、[[大语言模型架构演进]]、[[Transformer架构深度解析]]、[[长上下文技术]]、[[MoE 混合专家模型]]、[[小模型与端侧 Agent]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
