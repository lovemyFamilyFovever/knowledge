---
title: "A/B测试与实验设计"
tags: []
source: "baike"
source_path: "开发术语 / 数据科学与大数据"
collected: "2026-09-05"
status: "imported"
---

# A/B测试与实验设计


> 📌 **导航**：本文是 **A/B测试与实验设计** 词条，属于 data-science 术语集。相关枢纽：[[A B测试与实验设计]]、[[ETL]]、[[MLOps实践]]、[[RNN LSTM GRU]]、[[卷积神经网络(CNN)]]。

## A/B测试完整流程

```
假设 -> 设计实验 -> 计算样本量 -> 随机分组 -> 数据收集 -> 统计检验 -> 决策
```

### 1. 提出假设

```
H0(零假设): 新版本与旧版本无差异
H1(备择假设): 新版本优于旧版本
```

### 2. 计算样本量

```python
from scipy import stats
import numpy as np

def sample_size(p1, p2, alpha=0.05, power=0.8):
    """计算A/B测试所需样本量"""
    effect_size = abs(p1 - p2) / np.sqrt(p1 * (1 - p1))
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    n = ((z_alpha + z_beta) / effect_size) ** 2
    return int(np.ceil(n))

# 例：基线转化率10%，期望检测到2%提升
n = sample_size(0.10, 0.12)  # 每组需要约3800用户
```

### 3. 随机分组

```python
import hashlib

def assign_group(user_id, salt="exp_001"):
    hash_val = hashlib.md5(f"{salt}:{user_id}".encode()).hexdigest()
    return "control" if int(hash_val, 16) % 2 == 0 else "treatment"
```

### 4. 统计检验

```python
from scipy.stats import chi2_contingency, ttest_ind

# 比例检验（转化率）
contingency = [[conv_a, n_a - conv_a], [conv_b, n_b - conv_b]]
chi2, p_value, dof, expected = chi2_contingency(contingency)

# 均值检验（客单价）
t_stat, p_value = ttest_ind(values_a, values_b)
```

## 多重比较问题

同时检验多个假设时，需要校正：

| 方法 | 校正方式 | 严格程度 |
|------|----------|----------|
| Bonferroni | alpha' = alpha / m | 最严格 |
| Holm-Bonferroni | 逐步校正 | 较严格 |
| Benjamini-Hochberg | 控制FDR | 较宽松 |

## 常见陷阱

| 陷阱 | 说明 | 解决方案 |
|------|------|----------|
| 偷看结果 | 提前终止实验 | 预设样本量 |
| Simpson悖论 | 分层数据结论相反 | 分层分析 |
| 新奇效应 | 用户因新鲜感短期提升 | 延长实验时间 |
| 样本污染 | 用户在两组间切换 | 确保独立性 |
| 季节性 | 不同时期行为不同 | 同期对照 |

## 相关术语

[[ETL]]、[[MLOps实践]]、[[RNN LSTM GRU]]、[[卷积神经网络(CNN)]]、[[可解释AI(XAI)]]、[[因果推断]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
