---
title: "卷积神经网络(CNN)"
tags: []
source: "baike"
source_path: "开发术语 / 数据科学与大数据"
collected: "2026-09-05"
status: "imported"
---

# 卷积神经网络

```python
conv = nn.Conv2d(3, 64, kernel_size=3, padding=1)
# 输入: [B, 3, 224, 224] -> 输出: [B, 64, 224, 224]
```

## 经典架构

| 模型 | 年份 | Top-1 | 参数量 | 创新 |
|------|------|-------|--------|------|
| AlexNet | 2012 | 63.3% | 61M | ReLU, Dropout |
| VGG-16 | 2014 | 74.5% | 138M | 小卷积核 |
| ResNet-50 | 2015 | 76.1% | 25M | 残差连接 |
| EfficientNet | 2019 | 84.3% | 66M | 复合缩放 |

## ResNet残差连接

```python
class ResBlock(nn.Module):
    def forward(self, x):
        return F.relu(x + self.conv2(F.relu(self.conv1(x))))
```

梯度可通过跳跃连接直接回传，解决深层网络梯度消失。
