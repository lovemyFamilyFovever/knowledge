---
title: "可解释AI(XAI)"
tags: []
source: "baike"
source_path: "开发术语 / 数据科学与大数据"
collected: "2026-09-05"
status: "imported"
---

# 可解释AI

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
