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

## 定义

**一句话定义：** CrewAI 是以"角色扮演"组织多 Agent 协作的开源框架，用 Agent / Task / Crew / Process 抽象，把"谁来干、干什么、按什么顺序干"声明式地拼成一个团队。

**通俗类比：** 像组建项目组并写岗位说明书——招一位"资深研究员"、一位"写手"，各领一张任务单，再按流程（顺序推进或由经理分派）开工。

## 为什么需要它

单个 Agent 什么都干，容易杂而不专；真实复杂任务本就像团队分工。CrewAI 把"角色 + 任务 + 协作流程"抽象成可声明的组件，让多 Agent 协作无需手写调度与通信逻辑，显著降低编排门槛。

## 核心能力

五个核心概念撑起整套抽象：

| 概念 | 说明 | 类比 |
|------|------|------|
| Agent | 有特定角色的智能体 | 团队成员 |
| Task | 具体工作任务 | 工作单 |
| Crew | Agent + Task 的组织 | 项目团队 |
| Process | 任务编排方式 | 工作流程 |
| Tool | Agent 可用的工具 | 工具箱 |

它的标志性用法是"三件套"声明角色：用 role / goal / backstory 刻画一个人设，再挂上工具与模型——下面的片段演示的就是"招一名研究员"：

```python
researcher = Agent(
    role='高级研究分析师',
    goal='发现 {topic} 的最新趋势和洞察',
    backstory='你有 10 年研究经验，擅长数据提取与趋势分析。',
    tools=[search_tool, scrape_tool],
    llm=ChatOpenAI(model='gpt-4o'),
)
```

Task 用 description 与 expected_output 定义工作单并指派 agent；Crew 再把 agents、tasks、process 组装起来 `kickoff` 启动。协作有两条流程线：

| 模式 | 说明 | 适用场景 |
|------|------|--------|
| Sequential | 任务按顺序依次执行 | 线性工作流 |
| Hierarchical | Manager Agent 动态分派协调 | 复杂项目 |

## 具体示例

内容创作团队"研究员 + 写手 + 编辑"按研究→写作→审核顺序交付；软件团队"架构师 + 开发者 + 测试"按设计→编码→测试接力。这类天然可拆成专家流水线的任务，正适合用 Crew 组织。

## 何时用 / 何时不用

- **用**：任务能自然拆成多个专家角色、按流水线或经理分派协作时。
- **不用**：单 Agent 已够用，或需要极精细的图级控制流与状态定制时——那更适合 LangGraph 一类框架。

## 优劣与代价

✅ 抽象直观、上手快、模板丰富，多角色协作写起来像填岗位表。
⚠️ 封装层次深，复杂控制流与状态定制不如显式建图的框架灵活。
⚠️ 调度被框架托管，出问题时调试偏"黑箱"。

## 与相关概念的区别

- **vs [[Agent 编排框架对比]]**：那是跨框架的横向选型视角，本词条聚焦 CrewAI 本身的设计与用法。
- **vs LangGraph**：LangGraph 显式建图、精确掌控状态流转；CrewAI 用"角色 + 任务"的高层抽象更省心，但控制粒度更粗。

## 常见误区

- CrewAI 只能按 Sequential 顺序执行任务，不支持层级式协作。
- CrewAI 里每个 Agent 只能挂一个固定工具，无法组合多个工具。
- 用 CrewAI 就必须手写 Agent 之间的调度与通信代码。

## 面试速答

> 🎯 CrewAI 用"角色扮演"把多 Agent 协作组件化：Agent 靠 role/goal/backstory 定人设并挂工具，Task 是带预期输出的工作单，Crew 按 Sequential 或 Hierarchical 编排后 kickoff。代价是抽象较深、图级控制不如 LangGraph。
> 🔍 追问：Sequential 与 Hierarchical 有何区别？（前者按序执行任务，后者由 Manager Agent 动态分派协调）
> 🔍 追问：Agent 的 backstory 起什么作用？（提供角色背景与风格，影响其决策口吻与专业视角）

## 相关术语

[[多 Agent 协作系统]]、[[Agent 编排框架对比]]、[[LangChain 框架全解析]]、[[AI Agent 概述与核心架构]]、[[LlamaIndex 框架指南]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
