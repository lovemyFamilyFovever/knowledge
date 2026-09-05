---
title: "Prompt Engineering 高级技巧"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Prompt Engineering 高级技巧

## 概述
**Prompt Engineering** 是通过设计高质量的提示词来引导LLM产生期望输出的技术。本文介绍高级提示技巧。

## Few-shot Prompting
通过在提示中提供少量示例来引导模型：
```python
prompt = """
请将文本分类为正面/负面情感。

文本：这个产品太棒了！
情感：正面

文本：服务态度非常差
情感：负面

文本：效果还可以，但价格偏贵
情感：
"""
```

## Chain-of-Thought (CoT)
引导模型逐步推理，显著提高复杂问题的准确率：
```python
# 零样本 CoT
prompt = """问题：一个果园有15棵苹果树，每棵树平均产60个苹果。
如果每个苹果卖2元，总收入是多少？

让我们一步步思考：
1. 苹果总数 = 15棵 x 60个/棵 = 900个
2. 总收入 = 900个 x 2元/个 = 1800元

答案：1800元"""
```

## Tree-of-Thought (ToT)
在多个推理分支中搜索最优路径：
```python
class ToTNode:
    def __init__(self, thought, parent=None):
        self.thought = thought
        self.parent = parent
        self.children = []
        self.score = 0

def tree_of_thought(problem, llm, breadth=3, depth=3):
    root = ToTNode(problem)
    for d in range(depth):
        nodes = get_leaves(root)
        for node in nodes:
            # 生成多个推理分支
            thoughts = llm.generate_thoughts(node.thought, n=breadth)
            for t in thoughts:
                child = ToTNode(t, parent=node)
                child.score = llm.evaluate(t)
                node.children.append(child)
        # 保留最优分支
        best = max(get_leaves(root), key=lambda n: n.score)
    return best.thought
```

## Self-Consistency
多次采样后投票选择最一致的答案：
```python
def self_consistency(problem, llm, n_samples=5):
    answers = []
    for _ in range(n_samples):
        # 每次用不同的温度采样
        response = llm.generate(problem, temperature=0.7)
        answer = extract_answer(response)
        answers.append(answer)
    # 多数投票
    from collections import Counter
    most_common = Counter(answers).most_common(1)[0][0]
    return most_common
```

## 技巧对比

| 技巧 | 适用场景 | 准确率提升 | Token消耗 | 复杂度 |
|------|---------|-----------|----------|--------|
| **Zero-shot** | 简单任务 | 基准 | 低 | 最低 |
| **Few-shot** | 格式要求 | 中 | 中 | 低 |
| **CoT** | 推理任务 | 高 | 中 | 低 |
| **ToT** | 创造性任务 | 很高 | 高 | 高 |
| **Self-Consistency** | 需要可靠答案 | 高 | 很高 | 中 |

## Prompt 设计原则
1. **明确指令**：清楚说明期望的输出格式
2. **提供上下文**：给模型足够的背景信息
3. **分步引导**：复杂任务分解为步骤
4. **约束边界**：说明不要做什么
5. **迭代优化**：根据输出持续改进prompt

## 小结
Prompt Engineering是使用LLM的核心技能。CoT适合推理，ToT适合搜索，Self-Consistency提高可靠性。实践中往往组合多种技巧。
