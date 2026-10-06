---
title: "LangChain 框架全解析"
tags: [人工智能, 框架]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# LangChain 框架全解析


> 📌 **导航**：本文是 **LangChain 框架全解析** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## 定义

**一句话定义：** LangChain 是最流行的 LLM 应用开发框架，用模型、提示、链、Agent、工具、记忆、检索、解析等模块化组件，把大模型标准化地拼成应用。

**通俗类比：** 一套 LLM 应用的"标准积木盒 + 拼装说明书"——每块组件接口统一，用管道一接就能跑，不必为换模型、加检索、接工具各造一次轮子。

## 为什么需要它

裸调 API 时，换模型、加检索、接工具都要重写胶水代码。LangChain 把这些共性抽象成可组合组件，尤其 LCEL 用"管道"统一了 invoke / stream / batch 等接口，让原型到生产之间的复用与替换成本大幅下降。

## 核心能力

八大模块撑起一个应用：

| 模块 | 功能 | 关键类 |
|------|------|--------|
| Models | LLM 封装 | ChatOpenAI、Ollama |
| Prompts | 提示词管理 | ChatPromptTemplate |
| Chains | 组件串联 | LCEL Runnable |
| Agents | 自主决策与工具调用 | AgentExecutor |
| Tools | 工具定义 | Tool、StructuredTool |
| Memory | 对话历史管理 | Conversation*Memory |
| Retrievers | 文档检索 | VectorStoreRetriever |
| Parsers | 输出格式化 | JsonOutputParser |

**LCEL 组合**是它的灵魂语法：用 `|` 把提示、模型、解析器串成链，就得到一个统一支持 invoke / stream / batch 的可运行对象，换模型只改一处：

```python
chain = prompt | llm | StrOutputParser()
result = chain.invoke({'concept': '向量数据库'})
```

**Agent** 用 `create_tool_calling_agent` + `AgentExecutor` 驱动，靠 `max_iterations` 防死循环、`handle_parsing_errors` 兜底解析错误。**Tool** 用 `@tool` 装饰器或 `StructuredTool` 配 Pydantic `args_schema` 描述参数。**RAG** 走 loader → `RecursiveCharacterTextSplitter`（chunk_size、overlap）→ 向量库 → `RetrievalQA` 检索器 Top-K。对话历史按场景选记忆类型：

| 类型 | 特点 | 适用 |
|------|------|------|
| BufferMemory | 保留完整历史 | 短对话 |
| SummaryMemory | 自动摘要 | 长对话 |
| BufferWindowMemory | 最近 N 轮 | 有限上下文 |
| VectorStoreRetrieverMemory | 向量检索 | 海量历史 |

## 具体示例

一行 `prompt | llm | StrOutputParser()` 就把"填模板 → 调模型 → 取纯文本"接成一条链，直接 `.invoke` / `.stream` / `.batch`；把 `llm` 从 ChatOpenAI 换成 Ollama 就切到本地模型，其余不动——这正体现组件解耦的价值。

## 何时用 / 何时不用

- **用**：快速搭建 RAG / Agent 原型、需要多供应商可插拔与丰富现成组件时。
- **不用**：逻辑极简或追求极致可控、低依赖时，直连 SDK 或自建更透明（框架抽象厚、版本迭代快）。

## 优劣与代价

✅ 组件齐全、生态庞大，LCEL 让组合与替换高度一致。
⚠️ 抽象层厚重，出问题要穿透多层调试。
⚠️ API 迭代快、旧类（如老 Chain）与新范式并存，易踩废弃坑。

## 与相关概念的区别

- **vs [[LlamaIndex 框架指南]]**：LlamaIndex 强在数据 / 索引 / 检索，LangChain 强在通用编排与 Agent。
- **vs [[CrewAI 多 Agent 框架]]**：CrewAI 专注多角色协作，LangChain 是更底层、更通用的组件库。

## 常见误区

- LangChain 组合组件只能靠旧的 LLMChain 类，LCEL 只是无关紧要的语法糖。
- AgentExecutor 不设 `max_iterations`，也能保证 Agent 永不陷入无限循环。
- LangChain 只能配合 OpenAI 的模型，无法接入本地或其它厂商模型。

## 面试速答

> 🎯 LangChain 把 LLM 应用拆成可组合模块：Models/Prompts/Chains/Agents/Tools/Memory/Retrievers。核心是 LCEL——用 prompt | llm | parser 管道统一 invoke/stream/batch，换供应商只改一处。代价是抽象厚、版本迭代快。
> 🔍 追问：LCEL 相比旧 Chain 类的好处？（统一调用/流式/批处理/并行接口，组合与复用更一致）
> 🔍 追问：为什么 Agent 要设 max_iterations？（LLM 可能反复调工具不收敛，需上限兜底防死循环）

## 相关术语

[[LlamaIndex 框架指南]]、[[CrewAI 多 Agent 框架]]、[[Agent 编排框架对比]]、[[Function Calling 与 Tool Use]]、[[AI Agent 概述与核心架构]]、[[RAG 与检索技术详解]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
