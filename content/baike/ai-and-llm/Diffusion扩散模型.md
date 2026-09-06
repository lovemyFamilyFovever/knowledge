---
title: "Diffusion扩散模型"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Diffusion扩散模型

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
