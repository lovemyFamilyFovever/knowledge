---
title: "生成对抗网络(GAN)"
tags: []
source: "baike"
source_path: "开发术语 / 数据科学与大数据"
collected: "2026-09-05"
status: "imported"
---

# 生成对抗网络(GAN)


> 📌 **导航**：本文是 **生成对抗网络(GAN)** 词条，属于 data-science 术语集。相关枢纽：[[A B测试与实验设计]]、[[ETL]]、[[MLOps实践]]、[[RNN LSTM GRU]]、[[卷积神经网络(CNN)]]。

## 核心思想

两个网络博弈：Generator（生成器）从噪声生成数据，Discriminator（判别器）判断真假。

**类比：** 造假币者(G)和警察(D)的博弈——造假者不断提升伪造技术，警察不断提升鉴别能力。

## 训练过程

```python
# 判别器训练：最大化log(D(x)) + log(1-D(G(z)))
def train_discriminator(real_data, fake_data):
    d_real = discriminator(real_data)
    d_fake = discriminator(fake_data)
    loss = -(torch.log(d_real) + torch.log(1 - d_fake)).mean()
    return loss

# 生成器训练：最大化log(D(G(z)))
def train_generator(noise):
    fake = generator(noise)
    d_fake = discriminator(fake)
    loss = -torch.log(d_fake).mean()
    return loss
```

## GAN变体演进

| 模型 | 年份 | 创新 | 应用 |
|------|------|------|------|
| 原始GAN | 2014 | 对抗训练 | 理论奠基 |
| DCGAN | 2015 | CNN架构 | 图像生成 |
| WGAN | 2017 | Wasserstein距离 | 训练稳定 |
| StyleGAN | 2019 | 风格控制 | 人脸生成 |
| StyleGAN2 | 2020 | 权重解调 | 高质量人脸 |
| CycleGAN | 2017 | 无配对转换 | 风格迁移 |
| Pix2Pix | 2017 | 配对转换 | 图像翻译 |

## StyleGAN架构

```
z(噪声) -> Mapping Network -> w(中间向量)
                                    ↓
w -> AdaIN注入到每一层 -> 逐步生成 2x2 -> 4x4 -> ... -> 1024x1024
```

## 训练难点与解决

| 问题 | 症状 | 解决方案 |
|------|------|----------|
| 模式崩塌 | 只生成少数类型 | Minibatch Discrimination |
| 训练不稳定 | loss震荡 | WGAN、谱归一化 |
| 梯度消失 | G无法学习 | WGAN、Least Square GAN |
| 评估困难 | 无明确指标 | FID、IS |

## GAN vs Diffusion

| 特性 | GAN | Diffusion |
|------|-----|-----------|
| 生成速度 | 极快（单次前向） | 慢（多步去噪） |
| 训练稳定性 | 不稳定 | 稳定 |
| 多样性 | 易模式崩塌 | 高多样性 |
| 质量上限 | 高 | 极高 |
| 主流趋势 | 下降 | 上升 |

## 相关术语

[[A B测试与实验设计]]、[[ETL]]、[[MLOps实践]]、[[RNN LSTM GRU]]、[[卷积神经网络(CNN)]]、[[可解释AI(XAI)]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
