---
title: "Workflow Agent"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Workflow Agent

## 概述
**Workflow Agent** 将AI Agent能力嵌入业务流程，实现自动化编排和执行。

## 核心概念

| 概念 | 说明 | 类比 |
|------|------|------|
| **Workflow** | 完整的业务流程 | 工作手册 |
| **Step** | 流程中的一个步骤 | 工作步骤 |
| **Trigger** | 流程启动条件 | 开始按钮 |
| **Condition** | 步骤执行条件 | 判断规则 |
| **Action** | 具体执行动作 | 操作动作 |

## LangGraph 工作流
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    input: str
    analysis: str
    decision: str
    result: str

def analyze(state):
    return {'analysis': llm.analyze(state['input'])}

def decide(state):
    decision = llm.decide(state['analysis'])
    return {'decision': decision}

def execute_action(state):
    return {'result': f'执行了{state["decision"]}'}

# 构建图
graph = StateGraph(State)
graph.add_node('analyze', analyze)
graph.add_node('decide', decide)
graph.add_node('execute', execute_action)

graph.set_entry_point('analyze')
graph.add_edge('analyze', 'decide')
graph.add_conditional_edges('decide', lambda s: s['decision'], {
    'action_a': 'execute',
    'action_b': 'some_other_node',
})
graph.add_edge('execute', END)

workflow = graph.compile()
result = workflow.invoke({'input': '用户请求'})
```

## 工作流模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| **顺序执行** | 按步骤依次执行 | 线性流程 |
| **条件分支** | 根据条件选择路径 | 决策流程 |
| **并行执行** | 多步骤同时执行 | 独立任务 |
| **循环执行** | 重复直到满足条件 | 迭代优化 |
| **人机协作** | 关键节点人工确认 | 审批流程 |

## 业务场景

| 场景 | 流程 | Agent作用 |
|------|------|----------|
| **客户支持** | 接收→分类→路由→处理→反馈 | 智能分类和自动回复 |
| **内容审核** | 提交→初审→人工复审→发布 | 自动化初筛 |
| **审批流程** | 申请→审核→批准→执行 | 智能审核建议 |
| **数据分析** | 收集→清洗→分析→报告 | 自动化分析 |

## 小结
Workflow Agent将AI能力编排为结构化的业务流程，实现端到端的自动化。LangGraph是最常用的编排框架。
