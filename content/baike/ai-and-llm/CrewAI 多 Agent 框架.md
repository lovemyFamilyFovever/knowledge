---
title: "CrewAI 多 Agent 框架"
tags: [人工智能, Agent]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# CrewAI 多 Agent 框架


> 📌 **导航**：本文是 **CrewAI 多 Agent 框架** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## 概述

**CrewAI** 专注于多Agent协作——多个专业角色组成团队，各司其职，共同完成复杂任务。核心设计理念是**角色扮演（Role-Playing）**。

## 核心概念

| 概念 | 说明 | 类比 |
|------|------|------|
| **Agent** | 有特定角色的智能体 | 团队成员 |
| **Task** | 具体工作任务 | 工作单 |
| **Crew** | Agent+Task的组织结构 | 项目团队 |
| **Process** | 任务编排方式 | 工作流程 |
| **Tool** | Agent可用的工具 | 工具箱 |

## 定义Agent

```python
from crewai import Agent

researcher = Agent(
    role='高级研究分析师',
    goal='发现{topic}的最新趋势和洞察',
    backstory='你是一位有10年经验的研究分析师，擅长数据提取和趋势分析。',
    verbose=True,
    allow_delegation=False,
    tools=[search_tool, scrape_tool],
    llm=ChatOpenAI(model='gpt-4o'),
)
```

## 定义Task

```python
from crewai import Task

research_task = Task(
    description='深入研究{topic}的最新发展',
    expected_output='详细研究报告，包含数据和来源引用',
    agent=researcher,
)
```

## 组建Crew并执行

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    verbose=True,
)
result = crew.kickoff(inputs={'topic': 'AI Agent发展'})
```

## 执行流程模式

| 模式 | 说明 | 适用场景 |
|------|------|--------|
| **Sequential** | 按顺序依次执行 | 线性工作流 |
| **Hierarchical** | Manager Agent分配协调 | 复杂项目 |

## 实际应用场景

| 场景 | Agent组合 | 工作流 |
|------|----------|--------|
| **内容创作** | 研究员+写手+编辑 | 研究→写作→审核 |
| **软件开发** | 架构师+开发者+测试 | 设计→编码→测试 |
| **市场分析** | 数据分析师+竞品分析师+报告撰写 | 收集→分析→报告 |

## 小结

CrewAI通过角色扮演和任务编排的抽象，让多Agent协作变得直观强大。

## 相关术语

[[多 Agent 协作系统]]、[[Agent 编排框架对比]]、[[LangChain 框架全解析]]、[[AI Agent 概述与核心架构]]、[[LlamaIndex 框架指南]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
