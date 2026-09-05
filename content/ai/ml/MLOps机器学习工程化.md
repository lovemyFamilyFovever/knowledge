---
title: "MLOps机器学习工程化"
tags: []
source: "baike"
source_path: "技术文章 / AI与机器学习"
collected: "2026-09-05"
status: "imported"
---

# MLOps机器学习工程化

# MLOps 终极指南：从理论到实践的完整工程体系

## 1. MLOps 成熟度模型：0-2级深度解析

MLOps 成熟度模型是评估组织机器学习运维能力的关键框架。Google 的 ML Maturity Model 将 MLOps 划分为三个主要级别，每个级别代表了不同的流程成熟度和自动化程度。

### 1.1 级别0：手动过程（Manual Process）

**特征：**
- **实验管理：** 手动进行实验，代码和结果分散在不同目录、笔记本和服务器中
- **模型训练：** 在本地机器或单个服务器上手动执行训练脚本
- **部署流程：** 手动将训练好的模型复制到生产环境
- **监控系统：** 基本不存在或仅限于简单的日志记录

**典型代码结构：**
```python
# 级别0的典型项目结构
project/
├── notebooks/
│   ├── EDA.ipynb
│   ├── training_v1.ipynb
│   └── training_v2.ipynb
├── data/
│   ├── raw/
│   └── processed/
├── models/
│   ├── model_v1.pkl
│   └── model_v2.pkl
└── app.py  # 手动复制的部署脚本

# 手动执行训练
import pickle
from sklearn.ensemble import RandomForestClassifier

# 1. 手动加载数据
train_data = pd.read_csv('data/processed/train.csv')

# 2. 手动训练模型
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# 3. 手动保存模型
with open('models/model_final.pkl', 'wb') as f:
    pickle.dump(model, f)

# 4. 手动部署到服务器
# scp models/model_final.pkl user@production-server:/models/
```

**挑战：**
- 版本控制混乱，难以重现实验
- 部署过程容易出错，依赖人工操作
- 缺乏模型性能监控，问题发现滞后
- 团队协作困难，知识无法共享

### 1.2 级别1：ML管道自动化（ML Pipeline Automation）

**核心特征：**
- **自动化训练管道：** 从数据准备到模型部署的整个过程自动化
- **持续训练（CT）：** 定期或触发式重新训练模型
- **实验跟踪：** 使用MLflow、W&B等工具系统化记录实验
- **基本监控：** 模型性能指标的基本监控

**实现示例：**
```python
# 级别1的自动化管道示例
from datetime import datetime
import mlflow
import mlflow.sklearn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# 定义自动化的训练管道
def automated_training_pipeline():
    """
    自动化的机器学习训练管道
    """
    # 1. 数据版本化和准备
    with mlflow.start_run(run_name=f"training_{datetime.now().strftime('%Y%m%d')}"):
        
        # 记录数据版本
        data_version = mlflow.log_param("data_version", "2024-01-15")
        
        # 自动数据准备
        df = load_latest_data()  # 从数据存储加载最新数据
        X_train, X_test, y_train, y_test = prepare_data(df)
        
        # 2. 特征工程（自动化的）
        feature_pipeline = create_feature_pipeline()
        X_train_transformed = feature_pipeline.fit_transform(X_train)
        
        # 记录特征数量
        mlflow.log_metric("num_features", X_train_transformed.shape[1])
        
        # 3. 模型训练（自动参数搜索）
        model_params = {
            "n_estimators": mlflow.search_runs()[0].data.params.get("best_n_estimators", 100),
            "max_depth": mlflow.search_runs()[0].data.params.get("best_max_depth", 10)
        }
        
        model = RandomForestClassifier(**model_params)
        model.fit(X_train_transformed, y_train)
        
        # 4. 模型评估
        X_test_transformed = feature_pipeline.transform(X_test)
        accuracy = model.score(X_test_transformed, y_test)
        mlflow.log_metric("accuracy", accuracy)
        
        # 5. 模型保存和注册
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name="production_model"
        )
        
        # 保存特征管道
        joblib.dump(feature_pipeline, "feature_pipeline.joblib")
        mlflow.log_artifact("feature_pipeline.joblib")
        
        return model, feature_pipeline, accuracy

# 自动化触发机制
def check_for_new_data():
    """检查是否有新数据需要处理"""
    latest_data_time = get_latest_data_time()
    last_training_time = get_last_training_time()
    
    if latest_data_time > last_training_time:
        # 触发重新训练
        automated_training_pipeline()
        deploy_model()
```

**关键组件：**
1. **自动化数据管道：** 定期从源系统提取数据
2. **特征工程管道：** 标准化、转换特征
3. **训练和验证循环：** 自动训练、评估、选择最佳模型
4. **部署自动化：** 自动将新模型部署到生产环境

### 1.3 级别2：CI/CD/CT 的自动化管道

**核心特征：**
- **完整的CI/CD/CT：** 持续集成、持续部署、持续训练
- **自动化测试：** 数据测试、模型测试、集成测试
- **高级监控：** 实时性能监控和漂移检测
- **基础设施即代码：** 使用Terraform、CloudFormation管理基础设施

**CI/CD/CT 流程实现：**
```yaml
# GitHub Actions 配置文件示例
# .github/workflows/ml-pipeline.yml
name: ML Pipeline CI/CD/CT

on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点运行
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  data-validation:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Validate data quality
      run: python tests/data_validation.py
      
    - name: Check for data drift
      run: python monitoring/data_drift_detection.py

  model-training:
    needs: data-validation
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup MLflow
      run: |
        pip install mlflow
        mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./artifacts &
    
    - name: Train and evaluate model
      run: python training/train_model.py
      
    - name: Run model tests
      run: python tests/model_tests.py
      
    - name: Register model if better
      run: python scripts/model_registration.py

  deployment:
    needs: model-training
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to staging
      run: python deployment/deploy_to_staging.py
      
    - name: Run integration tests
      run: python tests/integration_tests.py
      
    - name: Deploy to production (manual approval)
      uses: trstringer/manual-approval@v1
      with:
        secret: ${{ github.TOKEN }}
        approvers: mlops-team
```

**级别2的关键自动化组件：**

1. **自动化测试套件：**
```python
# tests/model_tests.py
import pytest
import mlflow.pyfunc
import numpy as np

class TestModelQuality:
    """模型质量测试"""
    
    @pytest.fixture
    def model(self):
        """加载最新注册的模型"""
        model_name = "production_model"
        model_version = "latest"
        model = mlflow.pyfunc.load_model(
            model_uri=f"models:/{model_name}/{model_version}"
        )
        return model
    
    @pytest.fixture
    def test_data(self):
        """准备测试数据"""
        X_test, y_test = load_test_data()
        return X_test, y_test
    
    def test_model_accuracy(self, model, test_data):
        """测试模型准确率"""
        X_test, y_test = test_data
        predictions = model.predict(X_test)
        accuracy = np.mean(predictions == y_test)
        assert accuracy >= 0.85, f"模型准确率过低: {accuracy}"
    
    def test_model_latency(self, model, test_data):
        """测试模型推理延迟"""
        X_test, _ = test_data
        sample = X_test.iloc[:100]  # 取100个样本
        
        import time
        start = time.time()
        model.predict(sample)
        latency = (time.time() - start) / len(sample)
        
        assert latency < 0.1, f"推理延迟过高: {latency}秒/样本"
    
    def test_model_fairness(self, model, test_data):
        """测试模型公平性"""
        X_test, y_test = test_data
        
        # 测试不同群体间的性能差异
        groups = get_demographic_groups(X_test)
        accuracies = []
        
        for group_name, group_indices in groups.items():
            group_acc = model.score(X_test.iloc[group_indices], 
                                   y_test.iloc[group_indices])
            accuracies.append((group_name, group_acc))
        
        # 检查最大差异
        max_acc = max(acc for _, acc in accuracies)
        min_acc = min(acc for _, acc in accuracies)
        fairness_gap = max_acc - min_acc
        
        assert fairness_gap < 0.1, f"公平性差距过大: {fairness_gap}"
```

2. **自动化监控系统：**
```python
# monitoring/automated_monitoring.py
from prometheus_client import start_http_server, Summary, Gauge, Counter
import time
import numpy as np
from datetime import datetime

# Prometheus指标
PREDICTION_LATENCY = Summary('prediction_latency_seconds', 'Time spent processing predictions')
MODEL_ACCURACY = Gauge('model_accuracy', 'Current model accuracy')
DATA_DRIFT_SCORE = Gauge('data_drift_score', 'Current data drift score')
PREDICTION_COUNT = Counter('prediction_count', 'Total number of predictions')

class AutomatedMonitor:
    """自动化监控系统"""
    
    def __init__(self, model_name):
        self.model_name = model_name
        self.baseline_stats = self.load_baseline_stats()
        self.recent_predictions = []
        
    @PREDICTION_LATENCY.time()
    def track_prediction(self, input_data, prediction, latency):
        """跟踪预测结果"""
        self.recent_predictions.append({
            'timestamp': datetime.now(),
            'input': input_data,
            'prediction': prediction,
            'latency': latency
        })
        
        PREDICTION_COUNT.inc()
        
        # 定期检查模型性能
        if len(self.recent_predictions) % 100 == 0:
            self.check_model_performance()
            self.check_data_drift()
    
    def check_model_performance(self):
        """检查模型性能"""
        if len(self.recent_predictions) < 50:
            return
        
        # 模拟获取真实标签（实际中需要延迟反馈）
        recent_with_labels = self.get_recent_predictions_with_labels()
        
        if recent_with_labels:
            accuracy = self.calculate_accuracy(recent_with_labels)
            MODEL_ACCURACY.set(accuracy)
            
            # 如果性能下降，触发重新训练
            if accuracy < self.baseline_stats['accuracy'] * 0.95:
                self.trigger_retraining()
    
    def check_data_drift(self):
        """检查数据漂移"""
        if len(self.recent_predictions) < 100:
            return
        
        recent_inputs = [p['input'] for p in self.recent_predictions[-100:]]
        drift_score = self.calculate_data_drift_score(recent_inputs)
        
        DATA_DRIFT_SCORE.set(drift_score)
        
        # 如果漂移严重，触发特征工程重新评估
        if drift_score > 0.3:
            self.trigger_feature_engineering_review()
    
    def trigger_retraining(self):
        """触发模型重新训练"""
        print(f"⚠️ 模型性能下降，触发重新训练: {self.model_name}")
        # 这里调用重新训练的API或发送消息到队列
        send_retraining_job(self.model_name)
    
    def trigger_feature_engineering_review(self):
        """触发特征工程审查"""
        print(f"⚠️ 检测到数据漂移，触发特征工程审查: {self.model_name}")
        send_feature_review_job(self.model_name)

# 启动监控服务器
if __name__ == "__main__":
    start_http_server(8000)
    monitor = AutomatedMonitor("production_model")
    
    # 在实际应用中，这里会接收预测请求并调用track_prediction
    while True:
        time.sleep(1)
```

**成熟度对比表：**

| 特性 | 级别0 | 级别1 | 级别2 |
|------|-------|-------|-------|
| **实验管理** | 手动，无跟踪 | 使用MLflow等工具 | 集成版本控制 |
| **特征工程** | 代码中硬编码 | 管道化，可重用 | 特征存储，集中管理 |
| **模型训练** | 手动脚本 | 自动化管道 | CI/CD集成 |
| **模型部署** | 手动复制 | 自动部署到生产 | 蓝绿部署，金丝雀发布 |
| **监控系统** | 无 | 基本日志 | 实时监控，自动告警 |
| **团队协作** | 困难 | 部分协作 | 完整的团队工作流 |

## 2. 实验管理：MLflow 与 Weights & Biases 深度对比

实验管理是MLOps的核心支柱，它确保了机器学习工作的可重现性、可比性和协作性。

### 2.1 MLflow：开源实验管理平台

**核心组件：**
1. **MLflow Tracking：** 记录实验参数、指标、代码和结果
2. **MLflow Projects：** 可重现的实验包
3. **MLflow Models：** 统一的模型打包格式
4. **MLflow Model Registry：** 模型版本管理

**完整实验管理示例：**
```python
# mlflow_experiment.py
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
import os

class MLflowExperimentManager:
    def __init__(self, experiment_name, tracking_uri="http://localhost:5000"):
        """
        初始化MLflow实验管理器
        
        Args:
            experiment_name: 实验名称
            tracking_uri: MLflow跟踪服务器URI
        """
        self.experiment_name = experiment_name
        mlflow.set_tracking_uri(tracking_uri)
        
        # 创建或获取实验
        mlflow.set_experiment(experiment_name)
        
        print(f"MLflow实验已设置: {experiment_name}")
        print(f"跟踪URI: {tracking_uri}")
    
    def create_feature_pipeline(self, df):
        """创建特征工程管道"""
        # 这里简化示例，实际项目中会更复杂
        feature_pipeline = Pipeline([
            ('scaler', StandardScaler()),
            # 可以添加更多特征工程步骤
        ])
        
        return feature_pipeline
    
    def train_with_tracking(self, X_train, y_train, X_test, y_test, 
                           params=None, model_type='random_forest'):
        """
        带跟踪的模型训练
        
        Args:
            X_train, y_train: 训练数据
            X_test, y_test: 测试数据
            params: 模型参数
            model_type: 模型类型
        
        Returns:
            训练好的模型和运行ID
        """
        # 开始MLflow运行
        with mlflow.start_run(run_name=f"{model_type}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}"):
            # 1. 记录数据信息
            mlflow.log_param("dataset_size", len(X_train) + len(X_test))
            mlflow.log_param("feature_count", X_train.shape[1])
            mlflow.log_param("train_test_split", f"{len(X_train)}:{len(X_test)}")
            
            # 2. 特征工程
            feature_pipeline = self.create_feature_pipeline(X_train)
            X_train_processed = feature_pipeline.fit_transform(X_train)
            X_test_processed = feature_pipeline.transform(X_test)
            
            # 3. 记录模型参数
            if params:
                mlflow.log_params(params)
            
            # 4. 选择模型
            if model_type == 'random_forest':
                model = RandomForestClassifier(**(params or {}))
            elif model_type == 'gradient_boosting':
                model = GradientBoostingClassifier(**(params or {}))
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
            
            # 5. 训练模型
            model.fit(X_train_processed, y_train)
            
            # 6. 计算指标
            y_pred = model.predict(X_test_processed)
            
            metrics = {
                "accuracy": accuracy_score(y_test, y_pred),
                "precision": precision_score(y_test, y_pred, average='weighted'),
                "recall": recall_score(y_test, y_pred, average='weighted'),
                "f1_score": f1_score(y_test, y_pred, average='weighted')
            }
            
            # 7. 记录指标
            mlflow.log_metrics(metrics)
            
            # 8. 记录特征重要性
            if hasattr(model, 'feature_importances_'):
                # 记录前10个最重要的特征
                feature_importance = model.feature_importances_
                top_indices = np.argsort(feature_importance)[-10:][::-1]
                for i, idx in enumerate(top_indices):
                    mlflow.log_metric(f"feature_importance_{i}", feature_importance[idx])
            
            # 9. 记录模型
            # 使用mlflow的签名功能记录模型
            signature = infer_signature(X_train_processed, model.predict(X_train_processed))
            
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                signature=signature,
                input_example=X_train_processed[:5],
                registered_model_name=f"{model_type}_model"
            )
            
            # 10. 记录特征管道
            joblib.dump(feature_pipeline, "feature_pipeline.joblib")
            mlflow.log_artifact("feature_pipeline.joblib")
            
            # 11. 记录其他元数据
            mlflow.set_tag("model_type", model_type)
            mlflow.set_tag("experiment_phase", "training")
            
            print(f"训练完成! 准确率: {metrics['accuracy']:.4f}")
            print(f"运行ID: {mlflow.active_run().info.run_id}")
            
            return model, feature_pipeline, mlflow.active_run().info.run_id
    
    def hyperparameter_tuning(self, X_train, y_train, param_grid, 
                             model_type='random_forest', n_iter=10):
        """
        超参数调优
        
        Args:
            X_train, y_train: 训练数据
            param_grid: 参数网格
            model_type: 模型类型
            n_iter: 随机搜索迭代次数
        """
        from sklearn.model_selection import RandomizedSearchCV
        
        # 创建基础模型
        if model_type == 'random_forest':
            base_model = RandomForestClassifier(random_state=42)
        else:
            base_model = GradientBoostingClassifier(random_state=42)
        
        # 创建随机搜索对象
        random_search = RandomizedSearchCV(
            estimator=base_model,
            param_distributions=param_grid,
            n_iter=n_iter,
            cv=3,
            scoring='accuracy',
            random_state=42,
            n_jobs=-1
        )
        
        # 准备数据
        feature_pipeline = self.create_feature_pipeline(X_train)
        X_processed = feature_pipeline.fit_transform(X_train)
        
        # 开始MLflow运行
        with mlflow.start_run(run_name=f"hyperparameter_tuning_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}"):
            # 执行搜索
            random_search.fit(X_processed, y_train)
            
            # 记录最佳参数
            best_params = random_search.best_params_
            mlflow.log_params(best_params)
            mlflow.log_metric("best_score", random_search.best_score_)
            
            # 记录所有尝试的参数
            cv_results = random_search.cv_results_
            for i in range(n_iter):
                params = cv_results['params'][i]
                score = cv_results['mean_test_score'][i]
                
                with mlflow.start_run(run_name=f"trial_{i}", nested=True):
                    mlflow.log_params(params)
                    mlflow.log_metric("cv_score", score)
            
            print(f"最佳参数: {best_params}")
            print(f"最佳得分: {random_search.best_score_:.4f}")
            
            return random_search.best_estimator_, best_params
    
    def compare_experiments(self):
        """比较不同实验的结果"""
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        
        if not experiment:
            print("没有找到实验")
            return
        
        # 搜索所有运行
        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
        
        # 按准确率排序
        runs_sorted = runs.sort_values("metrics.accuracy", ascending=False)
        
        print("\n实验结果比较:")
        print("=" * 80)
        print(f"{'运行ID':<30} {'模型类型':<20} {'准确率':<10} {'F1分数':<10}")
        print("-" * 80)
        
        for _, run in runs_sorted.head(10).iterrows():
            run_id = run['run_id'][:28]
            model_type = run['tags.model_type']
            accuracy = run['metrics.accuracy']
            f1 = run.get('metrics.f1_score', 0)
            
            print(f"{run_id:<30} {model_type:<20} {accuracy:<10.4f} {f1:<10.4f}")
        
        return runs_sorted

# 使用示例
if __name__ == "__main__":
    # 初始化实验管理器
    manager = MLflowExperimentManager("customer_churn_prediction")
    
    # 准备数据（示例）
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 1. 训练随机森林模型
    rf_params = {
        "n_estimators": 100,
        "max_depth": 10,
        "min_samples_split": 5,
        "random_state": 42
    }
    
    rf_model, rf_pipeline, rf_run_id = manager.train_with_tracking(
        X_train, y_train, X_test, y_test,
        params=rf_params,
        model_type='random_forest'
    )
    
    # 2. 训练梯度提升模型
    gb_params = {
        "n_estimators": 200,
        "max_depth": 5,
        "learning_rate": 0.1,
        "random_state": 42
    }
    
    gb_model, gb_pipeline, gb_run_id = manager.train_with_tracking(
        X_train, y_train, X_test, y_test,
        params=gb_params,
        model_type='gradient_boosting'
    )
    
    # 3. 超参数调优
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [3, 5, 10, None],
        'min_samples_split': [2, 5, 10]
    }
    
    best_model, best_params = manager.hyperparameter_tuning(
        X_train, y_train, param_grid, n_iter=20
    )
    
    # 4. 比较实验结果
    manager.compare_experiments()
```

### 2.2 Weights & Biases (W&B)：协作式实验管理平台

W&B 提供了更丰富的可视化、团队协作和实验管理功能。

**W&B 高级功能示例：**
```python
# wandb_experiment.py
import wandb
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns

class WandbExperimentManager:
    def __init__(self, project_name, entity=None):
        """
        初始化W&B实验管理器
        
        Args:
            project_name: 项目名称
            entity: 团队或用户名称
        """
        self.project_name = project_name
        self.entity = entity
        
        # 初始化W&B
        wandb.init(
            project=project_name,
            entity=entity,
            settings=wandb.Settings(start_method="fork")
        )
        
        # 创建自定义指标
        wandb.define_metric("train/loss", step_metric="epoch")
        wandb.define_metric("val/loss", step_metric="epoch")
        wandb.define_metric("train/accuracy", step_metric="epoch")
        wandb.define_metric("val/accuracy", step_metric="epoch")
    
    def log_dataset_info(self, X_train, y_train, X_test, y_test):
        """记录数据集信息"""
        # 创建数据集描述
        dataset_info = {
            "train_size": len(X_train),
            "test_size": len(X_test),
            "num_features": X_train.shape[1],
            "class_distribution": {
                "train": dict(zip(*np.unique(y_train, return_counts=True))),
                "test": dict(zip(*np.unique(y_test, return_counts=True)))
            }
        }
        
        wandb.config.update({"dataset": dataset_info})
        
        # 记录样本数据分布
        self.log_data_distribution(X_train, y_train, "train")
        self.log_data_distribution(X_test, y_test, "test")
    
    def log_data_distribution(self, X, y, prefix="train"):
        """记录数据分布"""
        # 为每个特征创建直方图
        for i in range(min(X.shape[1], 5)):  # 只记录前5个特征
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.histplot(X[:, i], kde=True, ax=ax)
            ax.set_title(f"特征 {i} 分布 ({prefix}集)")
            ax.set_xlabel(f"特征值")
            ax.set_ylabel("频率")
            
            wandb.log({f"{prefix}/feature_{i}_distribution": wandb.Image(fig)})
            plt.close(fig)
        
        # 创建特征相关性矩阵
        if X.shape[1] <= 20:  # 如果特征不太多
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(pd.DataFrame(X).corr(), annot=True, cmap='coolwarm', 
                       center=0, ax=ax, fmt='.2f')
            ax.set_title(f"特征相关性矩阵 ({prefix}集)")
            
            wandb.log({f"{prefix}/feature_correlation": wandb.Image(fig)})
            plt.close(fig)
    
    def train_with_wandb(self, X_train, y_train, X_test, y_test, 
                        config=None, epochs=100):
        """
        使用W&B进行训练
        
        Args:
            X_train, y_train: 训练数据
            X_test, y_test: 测试数据
            config: 配置参数
            epochs: 训练轮数
        """
        # 合并配置
        if config is None:
            config = {
                "n_estimators": 100,
                "max_depth": 10,
                "learning_rate": 0.1,
                "optimizer": "sgd"
            }
        
        wandb.config.update(config)
        
        # 记录数据集信息
        self.log_dataset_info(X_train, y_train, X_test, y_test)
        
        # 创建模型
        model = RandomForestClassifier(
            n_estimators=config["n_estimators"],
            max_depth=config["max_depth"],
            random_state=42
        )
        
        # 模拟训练过程（实际中会有更多逻辑）
        for epoch in range(epochs):
            # 模拟训练损失和准确率
            train_loss = np.random.uniform(0.1, 0.5) * (1 - epoch/epochs)
            train_acc = 1 - train_loss + np.random.normal(0, 0.02)
            
            val_loss = train_loss + np.random.normal(0, 0.01)
            val_acc = train_acc - np.random.normal(0, 0.02)
            
            # 记录训练指标
            wandb.log({
                "train/loss": train_loss,
                "train/accuracy": train_acc,
                "val/loss": val_loss,
                "val/accuracy": val_acc,
                "epoch": epoch
            })
            
            # 记录梯度和权重分布（每10轮）
            if epoch % 10 == 0:
                self.log_model_weights(model, epoch)
            
            # 记录预测样本（每20轮）
            if epoch % 20 == 0:
                self.log_predictions(model, X_test, y_test, epoch)
        
        # 训练完成后记录最终模型
        model.fit(X_train, y_train)
        
        # 评估模型
        test_acc = model.score(X_test, y_test)
        wandb.log({"final/test_accuracy": test_acc})
        
        # 保存模型
        model_artifact = wandb.Artifact(
            name=f"model_{wandb.run.id}",
            type="model",
            description="训练好的随机森林模型",
            metadata=config
        )
        
        # 保存模型文件
        import joblib
        joblib.dump(model, "model.joblib")
        model_artifact.add_file("model.joblib")
        
        # 记录特征重要性
        self.log_feature_importance(model, X_train.shape[1])
        
        # 记录混淆矩阵
        self.log_confusion_matrix(model, X_test, y_test)
        
        # 完成运行
        wandb.log_artifact(model_artifact)
        wandb.finish()
        
        return model
    
    def log_model_weights(self, model, epoch):
        """记录模型权重分布"""
        if hasattr(model, 'estimators_'):
            # 对于随机森林，记录第一个决策树的权重
            tree = model.estimators_[0]
            
            # 创建权重直方图
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.histplot(tree.feature_importances_, kde=True, ax=ax)
            ax.set_title(f"特征重要性分布 (Epoch {epoch})")
            ax.set_xlabel("重要性")
            ax.set_ylabel("频率")
            
            wandb.log({f"weights/feature_importance_{epoch}": wandb.Image(fig)})
            plt.close(fig)
    
    def log_predictions(self, model, X_test, y_test, epoch):
        """记录预测样本"""
        # 随机选择一些样本
        sample_indices = np.random.choice(len(X_test), 5, replace=False)
        sample_X = X_test[sample_indices]
        sample_y = y_test[sample_indices]
        
        predictions = model.predict(sample_X)
        
        # 创建预测表格
        table = wandb.Table(columns=["样本ID", "真实标签", "预测标签", "正确"])
        
        for i, (true, pred) in enumerate(zip(sample_y, predictions)):
            table.add_data(i, true, pred, true == pred)
        
        wandb.log({f"predictions/samples_{epoch}": table})
    
    def log_feature_importance(self, model, num_features):
        """记录特征重要性"""
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            indices = np.argsort(importance)[::-1]
            
            # 创建特征重要性条形图
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(range(min(num_features, 20)), importance[indices[:20]])
            ax.set_xlabel("特征")
            ax.set_ylabel("重要性")
            ax.set_title("Top 20 特征重要性")
            ax.set_xticks(range(min(num_features, 20)))
            ax.set_xticklabels([f"特征{i}" for i in indices[:20]], rotation=45)
            
            wandb.log({"plots/feature_importance": wandb.Image(fig)})
            plt.close(fig)
            
            # 记录为表格
            feature_table = wandb.Table(columns=["特征ID", "重要性"])
            for i, idx in enumerate(indices[:20]):
                feature_table.add_data(f"特征{idx}", importance[idx])
            
            wandb.log({"data/feature_importance": feature_table})
    
    def log_confusion_matrix(self, model, X_test, y_test):
        """记录混淆矩阵"""
        from sklearn.metrics import confusion_matrix
        import seaborn as sns
        
        predictions = model.predict(X_test)
        cm = confusion_matrix(y_test, predictions)
        
        # 创建混淆矩阵图
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
        ax.set_xlabel('预测标签')
        ax.set_ylabel('真实标签')
        ax.set_title('混淆矩阵')
        
        wandb.log({"plots/confusion_matrix": wandb.Image(fig)})
        plt.close(fig)
    
    def create_sweep(self, sweep_config):
        """创建超参数搜索"""
        sweep_id = wandb.sweep(sweep_config, project=self.project_name)
        
        def train_sweep():
            """
            超参数搜索的训练函数
            """
            # 初始化运行
            run = wandb.init()
            config = run.config
            
            # 生成数据
            X, y = make_classification(
                n_samples=1000,
                n_features=config.get('n_features', 20),
                random_state=42
            )
            X_train, X_test, y_train, y_test = train_test_split(X