---
title: "Agent 评估与基准"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Agent 评估与基准

## 概述
Agent评估衡量Agent在特定任务上的表现。本文介绍主流评估基准和方法。

## 主流基准

| 基准 | 评估内容 | 任务类型 | 难度 |
|------|---------|---------|------|
| **AgentBench** | 综合Agent能力 | 8种环境 | 高 |
| **WebArena** | 网页交互 | 真实网站 | 很高 |
| **SWE-bench** | 软件工程 | GitHub Issues | 很高 |
| **GAIA** | 通用AI助手 | 多步骤任务 | 高 |
| **ToolBench** | 工具使用 | API调用 | 中 |
| **MMLU** | 知识理解 | 多选题 | 中 |

## AgentBench
评估Agent在8种环境中的表现：
```python
environments = [
    '操作系统',     # bash命令执行
    '数据库',       # SQL查询
    '知识图谱',     # 图查询
    '网页浏览',     # 网页交互
    '游戏环境',     # 策略游戏
    '家居环境',     # 智能家居
    '购物环境',     # 电商操作
    '编程环境',     # 代码生成
]
```

## SWE-bench
评估Agent解决真实GitHub Issues的能力：
```python
class SWEBenchEval:
    def evaluate(self, agent, issue):
        # 1. 给Agent展示Issue描述
        # 2. Agent阅读代码并生成补丁
        patch = agent.solve(issue)
        # 3. 应用补丁并运行测试
        result = self.apply_patch_and_test(patch, issue)
        return {
            'resolved': result.tests_passed,
            'patch_quality': self.evaluate_patch(patch),
        }
```

## 评估指标

| 指标 | 说明 | 计算方式 |
|------|------|---------|
| **成功率** | 完成任务的比例 | 正确数/总数 |
| **效率** | 完成任务的步骤数 | 平均步骤数 |
| **成本** | Token消耗 | 平均Token数 |
| **延迟** | 响应时间 | 平均秒数 |
| **可靠性** | 一致性表现 | 多次运行方差 |

## 评估方法

```python
def evaluate_agent(agent, test_cases):
    results = []
    for case in test_cases:
        try:
            output = agent.run(case['input'])
            score = case['evaluate'](output)
            results.append({
                'input': case['input'],
                'output': output,
                'score': score,
                'success': score > 0.8,
            })
        except Exception as e:
            results.append({'error': str(e), 'success': False})

    return {
        'success_rate': sum(r['success'] for r in results) / len(results),
        'avg_score': sum(r.get('score', 0) for r in results) / len(results),
    }
```

## 当前SOTA表现

| 基准 | GPT-4o | Claude 3.5 | 开源最佳 |
|------|--------|-----------|---------|
| **AgentBench** | 72% | 70% | 58% |
| **SWE-bench** | 38% | 49% | 42% |
| **WebArena** | 35% | 38% | 28% |
| **GAIA L1** | 75% | 78% | 60% |

## 小结
Agent评估需要多维度、多环境的综合基准。SWE-bench检验编码能力，WebArena检验网页交互，AgentBench提供全面评估。
