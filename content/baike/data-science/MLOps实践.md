---
title: "MLOps实践"
tags: []
source: "baike"
source_path: "开发术语 / 数据科学与大数据"
collected: "2026-09-05"
status: "imported"
---

# MLOps实践

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
