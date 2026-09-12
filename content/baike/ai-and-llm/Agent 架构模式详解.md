---
title: "Agent 架构模式详解"
tags: [人工智能, Agent]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Agent 架构模式详解

> 📌 **导航**：本文是 **Agent 架构模式详解** 词条，属于 ai-and-llm 术语集（Agent 方向）。相关枢纽：[[AI Agent 概述与核心架构]]、[[Agent 架构模式详解]]、[[多 Agent 协作系统]]、[[大模型基础术语详解]]、[[RAG 与检索技术详解]]。

## 概述

Agent 的架构模式决定了它如何思考、规划和执行任务。本文深入解析最主流的几种架构：**ReAct、Plan-and-Execute、Reflexion、LATS** 等。

## ReAct：推理与行动交替

**ReAct（Reasoning and Acting）** 是最经典、最广泛使用的 Agent 架构。核心思想是让 LLM 在推理（Thought）和行动（Action）之间交替进行。

### 工作流程

```
用户问题 → Thought(推理) → Action(行动) → Observation(观察) → Thought → ... → 最终答案
```

### 代码示例

```python
class ReActAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = {t.name: t for t in tools}

    def run(self, question: str, max_steps=10) -> str:
        prompt = self.build_prompt(question)
        for step in range(max_steps):
            response = self.llm.generate(prompt)
            action = self.parse_action(response)
            if action is None:
                return self.parse_final_answer(response)
            tool_name, tool_input = action
            observation = self.tools[tool_name].run(tool_input)
            prompt += f'\nObservation: {observation}\n'
        return '达到最大步骤数限制'
```

| 优势 | 劣势 |
|------|------|
| 直观易理解 | Token消耗大 |
| 调试方便 | 可能陷入循环 |
| 适用场景广泛 | 复杂任务效率低 |

## Plan-and-Execute：先规划后执行

将任务分为两阶段：先制定完整计划，再逐步执行。

```python
class PlanAndExecuteAgent:
    def __init__(self, planner_llm, executor_llm, tools):
        self.planner = planner_llm
        self.executor = executor_llm
        self.tools = tools

    def run(self, task: str) -> str:
        plan = self.create_plan(task)
        results = []
        for step in plan:
            result = self.execute_step(step, results)
            results.append({'step': step, 'result': result})
            if self.need_replan(step, result):
                plan = self.replan(task, results)
        return self.synthesize_results(results)
```

## Reflexion：自我反思

Agent 在执行失败后回顾错误，生成改进建议，然后重试。

```python
class ReflexionAgent:
    def __init__(self, llm, tools, max_retries=3):
        self.llm = llm
        self.tools = tools
        self.max_retries = max_retries
        self.reflections = []

    def run(self, task: str) -> str:
        for attempt in range(self.max_retries):
            result = self.execute(task, self.reflections)
            if self.evaluate(task, result).success:
                return result
            self.reflections.append(self.reflect(task, result))
        return '达到最大重试次数'
```

## LATS：语言Agent树搜索

**LATS（Language Agent Tree Search）** 结合蒙特卡洛树搜索和LLM推理，在多条行动路径中搜索最优解。

```
       初始状态
      /   |   \
   行动1  行动2  行动3
   /  \    |    /  \
 a1   a2  a3  a4   a5
 ↓    ↓    ↓   ↓    ↓
0.3  0.8  0.5 0.9  0.4   ← 评估得分
```

## 架构模式对比

| 架构模式 | 适用场景 | 复杂度 | 可靠性 | Token成本 |
|---------|---------|--------|--------|----------|
| **ReAct** | 通用任务、问答 | 低 | 中 | 中 |
| **Plan-and-Execute** | 多步骤复杂任务 | 中 | 高 | 中 |
| **Reflexion** | 需要精确性的任务 | 中 | 高 | 高 |
| **LATS** | 探索性、开放性任务 | 高 | 很高 | 很高 |
| **REWOO** | 效率优先场景 | 中 | 中 | 低 |

## REWOO：减少Token消耗

一次性生成所有工具调用计划，批量执行后生成答案。

```python
class REWOOAgent:
    def run(self, task):
        plan = self.planner.generate_plan(task)  # 一次性规划
        results = {}
        for i, tool_call in enumerate(plan):
            results[f'E{i+1}'] = self.execute(tool_call)
        return self.solver.solve(task, results)  # 一次性总结
```

## 选择建议

1. **简单任务** → ReAct
2. **复杂多步** → Plan-and-Execute
3. **高精度** → Reflexion
4. **Token受限** → REWOO
5. **开放探索** → LATS

## 小结

不同架构各有侧重。实际开发中常结合多种模式优势，根据场景灵活选择。
## 相关术语

[[AI Agent 概述与核心架构]]、[[Agent 架构模式详解]]、[[Agent 规划与推理]]、[[Agent 记忆系统]]、[[Agent 评估与基准]]、[[多 Agent 协作系统]]、[[大模型基础术语详解]]、[[RAG 与检索技术详解]]、[[Prompt 工程与 Agent 详解]]

## 参考资料

建议人工核验：可参考各框架官方文档（LangChain / AutoGPT / CrewAI 等）、*AI Agents in Action* (Michael Landsman)、Anthropic 工程博客 *Building Effective Agents*，以及 OpenAI / Anthropic 官方 Agent 开发文档。
