---
title: "可解释AI(XAI)"
tags: []
source: "baike"
source_path: "开发术语 / 数据科学与大数据"
collected: "2026-09-05"
status: "imported"
---

# 可解释AI(XAI)


> 📌 **导航**：本文是 **可解释AI(XAI)** 词条，属于 data-science 术语集。相关枢纽：[[A B测试与实验设计]]、[[ETL]]、[[MLOps实践]]、[[RNN LSTM GRU]]、[[卷积神经网络(CNN)]]。

## SHAP

```python
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test)
```

## 方法对比

| 方法 | 原理 | 适用 |
|------|------|------|
| SHAP | 博弈论 | 任何模型 |
| LIME | 局部线性近似 | 任何模型 |
| Grad-CAM | 梯度加权特征图 | CNN |
| 注意力可视化 | 注意力权重 | Transformer |

## 相关术语

[[A B测试与实验设计]]、[[ETL]]、[[MLOps实践]]、[[RNN LSTM GRU]]、[[卷积神经网络(CNN)]]、[[因果推断]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
