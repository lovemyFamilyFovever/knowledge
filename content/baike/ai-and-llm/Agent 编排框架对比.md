---
title: "Agent 编排框架对比"
tags: [人工智能, Agent]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Agent 编排框架对比

> 📌 **导航**：本文是 **Agent 编排框架对比** 词条，属于 ai-and-llm 术语集（Agent 方向）。相关枢纽：[[AI Agent 概述与核心架构]]、[[Agent 架构模式详解]]、[[多 Agent 协作系统]]、[[大模型基础术语详解]]、[[RAG 与检索技术详解]]。

## 概述
本文对比主流Agent编排框架：LangGraph、CrewAI、AutoGen、Swarm。

## 框架对比

| 维度 | LangGraph | CrewAI | AutoGen | Swarm |
|------|-----------|--------|---------|-------|
| **开发者** | LangChain | CrewAI | Microsoft | OpenAI |
| **核心理念** | 图结构工作流 | 角色扮演 | 多Agent对话 | 轻量编排 |
| **状态管理** | 图状态 | 任务状态 | 对话历史 | 上下文传递 |
| **多Agent** | 支持 | 原生支持 | 原生支持 | 支持 |
| **学习曲线** | 中 | 低 | 中 | 低 |
| **灵活性** | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| **适合场景** | 复杂流程 | 团队协作 | 对话式任务 | 简单编排 |

## LangGraph
```python
from langgraph.graph import StateGraph

graph = StateGraph(MyState)
graph.add_node('agent', agent_node)
graph.add_node('tool', tool_node)
graph.add_edge('agent', 'tool')
graph.add_conditional_edges('agent', should_continue)
app = graph.compile()
```

**优势**: 图结构灵活，支持循环和条件分支
**劣势**: 概念较复杂

## CrewAI
```python
crew = Crew(agents=[researcher, writer], tasks=[task1, task2])
result = crew.kickoff()
```

**优势**: 简单直观，角色设计丰富
**劣势**: 灵活性有限

## AutoGen
```python
assistant = AssistantAgent('assistant', llm_config=config)
user = UserProxyAgent('user')
user.initiate_chat(assistant, message='任务描述')
```

**优势**: 微软支持，研究导向
**劣势**: 对话式范式不适用于所有场景

## Swarm
```python
from swarm import Swarm, Agent

client = Swarm()
agent = Agent(name='Agent', instructions='...')
response = client.run(agent=agent, messages=[...])
```

**优势**: 极简轻量，OpenAI官方
**劣势**: 功能有限，不支持复杂状态

## 选择建议

| 需求 | 推荐框架 |
|------|---------|
| 复杂有状态流程 | LangGraph |
| 多角色团队协作 | CrewAI |
| 研究和对话式任务 | AutoGen |
| 快速原型/简单编排 | Swarm |
| 生产级通用应用 | LangGraph |

## 混合使用
实际项目中经常混合使用：
```python
# LlamaIndex处理数据检索 + LangGraph编排流程 + CrewAI多Agent协作
from llama_index.core import VectorStoreIndex
from langgraph.graph import StateGraph
from crewai import Crew
```

## 小结
选择框架取决于任务复杂度和团队偏好。LangGraph最灵活，CrewAI最易用，AutoGen适合研究，Swarm适合轻量场景。

## 相关术语

[[AI Agent 概述与核心架构]]、[[Agent 架构模式详解]]、[[Agent 规划与推理]]、[[Agent 记忆系统]]、[[Agent 评估与基准]]、[[多 Agent 协作系统]]、[[大模型基础术语详解]]、[[RAG 与检索技术详解]]、[[Prompt 工程与 Agent 详解]]

## 参考资料

建议人工核验：可参考各框架官方文档（LangChain / AutoGPT / CrewAI 等）、*AI Agents in Action* (Michael Landsman)、Anthropic 工程博客 *Building Effective Agents*，以及 OpenAI / Anthropic 官方 Agent 开发文档。
