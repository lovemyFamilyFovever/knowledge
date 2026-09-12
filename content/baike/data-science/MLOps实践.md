---
title: "MLOps实践"
tags: []
source: "baike"
source_path: "开发术语 / 数据科学与大数据"
collected: "2026-09-05"
status: "imported"
---

# MLOps实践


> 📌 **导航**：本文是 **MLOps实践** 词条，属于 data-science 术语集。相关枢纽：[[A B测试与实验设计]]、[[ETL]]、[[MLOps实践]]、[[RNN LSTM GRU]]、[[卷积神经网络(CNN)]]。

| 组件 | 工具 | 功能 |
|------|------|------|
| 实验追踪 | MLflow, W&B | 记录参数/指标 |
| 模型注册 | MLflow | 版本管理 |
| 特征存储 | Feast | 特征复用 |
| 模型服务 | vLLM, Triton | 在线推理 |
| 监控 | Evidently | 模型漂移 |

```python
import mlflow
mlflow.set_experiment("my_experiment")
with mlflow.start_run():
    mlflow.log_param("lr", 0.001)
    mlflow.log_metric("acc", 0.95)
```

## 相关术语

[[A B测试与实验设计]]、[[ETL]]、[[RNN LSTM GRU]]、[[卷积神经网络(CNN)]]、[[可解释AI(XAI)]]、[[因果推断]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
