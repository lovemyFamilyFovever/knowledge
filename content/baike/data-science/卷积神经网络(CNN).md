---
title: "卷积神经网络(CNN)"
tags: []
source: "baike"
source_path: "开发术语 / 数据科学与大数据"
collected: "2026-09-05"
status: "imported"
---

# 卷积神经网络(CNN)


> 📌 **导航**：本文是 **卷积神经网络(CNN)** 词条，属于 data-science 术语集。相关枢纽：[[A B测试与实验设计]]、[[ETL]]、[[MLOps实践]]、[[RNN LSTM GRU]]、[[卷积神经网络(CNN)]]。

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

## 相关术语

[[A B测试与实验设计]]、[[ETL]]、[[MLOps实践]]、[[RNN LSTM GRU]]、[[可解释AI(XAI)]]、[[因果推断]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
