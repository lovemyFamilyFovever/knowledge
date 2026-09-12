---
title: "Diffusion扩散模型"
tags: [人工智能, 生成模型]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Diffusion扩散模型


> 📌 **导航**：本文是 **Diffusion扩散模型** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## 核心思想

前向过程（加噪）：逐步向数据添加高斯噪声直到变成纯噪声。
反向过程（去噪）：学习从噪声逐步恢复数据。

**类比：** 前向=往清水里滴墨水，反向=学习如何把浑水变清。

```python
def training_step(x0):
    t = torch.randint(0, T, (batch_size,))
    noise = torch.randn_like(x0)
    x_t = q_sample(x0, t, noise)
    predicted_noise = model(x_t, t)
    return F.mse_loss(predicted_noise, noise)
```

## Stable Diffusion架构

```
文本 -> CLIP Text Encoder -> 文本嵌入
                              |
随机噪声 -> Latent Space -> UNet(文本嵌入) -> 去噪 -> VAE Decoder -> 图像
```

| 组件 | 作用 |
|------|------|
| CLIP | 文本编码 |
| UNet | 噪声预测 |
| VAE | 图像编解码 |
| Scheduler | 噪声调度 |

## ControlNet

在SD基础上添加条件控制：Canny边缘 -> 控制轮廓，OpenPose骨架 -> 控制姿态，深度图 -> 控制空间关系。

## 相关术语

[[多模态大模型]]、[[NeRF与3D生成]]、[[大模型基础术语详解]]、[[机器学习基础]]、[[Transformer架构深度解析]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
