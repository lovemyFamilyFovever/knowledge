---
title: "LLM 微调技术"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# LLM 微调技术

## 概述
**微调（Fine-tuning）** 是在预训练模型基础上，用特定领域数据进一步训练以适应下游任务。本文介绍主流微调技术。

## 微调方法对比

| 方法 | 可训练参数 | GPU需求 | 效果 | 适用场景 |
|------|-----------|---------|------|---------|
| **Full Fine-tuning** | 全部参数 | 很高 | 最好 | 数据充足、资源充裕 |
| **LoRA** | 低秩矩阵 | 低 | 好 | 最常用 |
| **QLoRA** | 量化+低秩 | 很低 | 好 | 资源受限 |
| **Prefix Tuning** | 前缀向量 | 低 | 中 | 生成任务 |
| **Adapter** | 小型适配层 | 低 | 中 | 多任务 |

## LoRA（Low-Rank Adaptation）
冻结原始权重，仅训练低秩分解矩阵：
```python
from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=16,                    # 秩
    lora_alpha=32,           # 缩放因子
    target_modules=['q_proj', 'v_proj'],  # 目标层
    lora_dropout=0.05,
    task_type='CAUSAL_LM',
)

model = AutoModelForCausalLM.from_pretrained('meta-llama/Llama-3-8B')
model = get_peft_model(model, config)
model.print_trainable_parameters()
# 输出: trainable params: 4,194,304 || all params: 8,030,261,248 || trainable%: 0.0522
```

## QLoRA
4-bit量化 + LoRA，极大降低显存需求：
```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    'meta-llama/Llama-3-8B',
    quantization_config=bnb_config,
    device_map='auto',
)
# 然后应用LoRA
model = get_peft_model(model, lora_config)
```

## RLHF（人类反馈强化学习）
```
SFT模型 → 训练奖励模型(RM) → PPO优化策略
  ↑                                ↓
  └── 人类偏好数据 ←── 生成多个回答 ←┘
```

## DPO（Direct Preference Optimization）
绕过奖励模型，直接用偏好数据优化：
```python
from trl import DPOTrainer, DPOConfig

config = DPOConfig(
    output_dir='./dpo_output',
    per_device_train_batch_size=4,
    learning_rate=5e-7,
    beta=0.1,  # KL散度约束
)

trainer = DPOTrainer(
    model=model,
    args=config,
    train_dataset=preference_dataset,  # chosen/rejected pairs
    tokenizer=tokenizer,
)
trainer.train()
```

## 微调数据准备
```python
# 训练数据格式示例
training_data = [
    {
        "instruction": "请总结以下文本",
        "input": "人工智能代理是...",
        "output": "AI Agent是一种智能系统..."
    },
]
```

## 小结
LoRA是最实用的微调方法，QLoRA适合资源受限场景。RLHF和DPO用于对齐人类偏好。选择方法需考虑数据量、计算资源和任务需求。
