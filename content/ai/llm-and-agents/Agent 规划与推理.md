---
title: "Agent 规划与推理"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Agent 规划与推理

## 概述
规划与推理是Agent完成复杂任务的核心能力，涉及任务分解、路径搜索和决策制定。

## 任务分解方法

| 方法 | 说明 | 适用场景 |
|------|------|---------|
| **LLM分解** | 用LLM将任务分解为子任务 | 通用任务 |
| **目标分解** | 按目标层级分解 | 复杂目标 |
| **依赖分析** | 识别子任务依赖关系 | 并行任务 |
| **MCTS搜索** | 蒙特卡洛树搜索最优路径 | 探索性任务 |

## LLM任务分解
```python
def decompose_task(task: str, llm) -> list:
    prompt = f"""
    请将以下任务分解为具体的子步骤：

    任务：{task}

    请以JSON格式返回：
    [{{"id": 1, "description": "...", "dependencies": [], "tools": ["..."]}}]
    """
    response = llm.generate(prompt)
    return json.loads(response)
```

## MCTS在Agent中的应用
蒙特卡洛树搜索（MCTS）将Agent决策建模为树搜索问题：
```
1. 选择(Selection): 用UCB公式选择最优子节点
2. 扩展(Expansion): 生成新的行动
3. 模拟(Simulation): LLM评估行动效果
4. 回传(Backpropagation): 更新路径上的统计信息
```

```python
class MCTSNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = 0

    def ucb1(self, c=1.4):
        if self.visits == 0:
            return float('inf')
        return self.value / self.visits + c * (math.log(self.parent.visits) / self.visits) ** 0.5

    def best_child(self):
        return max(self.children, key=lambda c: c.ucb1())
```

## 规划-执行-反思循环
```python
class PlanningAgent:
    def run(self, task):
        plan = self.create_plan(task)
        for step in plan:
            result = self.execute(step)
            if not self.is_satisfactory(result):
                # 反思并重新规划
                reflection = self.reflect(step, result)
                plan = self.revise_plan(plan, reflection)
        return self.summarize(plan)
```

## 推理策略

| 策略 | 说明 | Token效率 | 准确率 |
|------|------|----------|--------|
| **直接推理** | 一步到位 | 高 | 低 |
| **CoT推理** | 逐步思考 | 中 | 高 |
| **自洽性** | 多次采样投票 | 低 | 很高 |
| **MCTS** | 树搜索 | 很低 | 最高 |

## 小结
规划与推理是Agent智能的核心体现。LLM分解适合通用场景，MCTS适合探索性任务，规划-反思循环平衡效率和质量。
