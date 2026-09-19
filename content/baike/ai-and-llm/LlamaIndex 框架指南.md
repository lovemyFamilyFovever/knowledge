---
title: "LlamaIndex 框架指南"
tags: [人工智能, 框架]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# LlamaIndex 框架指南


> 📌 **导航**：本文是 **LlamaIndex 框架指南** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## 定义

**一句话定义：** LlamaIndex 是专注数据连接与检索的 LLM 框架，把私有数据高效接入大模型，是构建 RAG 应用的首选工具链之一。

**通俗类比：** 给大模型配一位"随身图书馆管理员"——把你的 PDF、网页、数据库整理成索引，问到什么就精准取相关几页递给它，让它基于你的资料作答。

## 为什么需要它

模型不知道你的私有或最新数据。LlamaIndex 把"读文档 → 切块 → 嵌入 → 建索引 → 检索 → 问答"这条 RAG 链路标准化，几行代码就能把一堆语料变成可问答的知识库，省去手写检索管道。

## 核心能力

六个核心概念对应一条完整数据流：

| 概念 | 说明 | 对应类 |
|------|------|--------|
| Data Connectors | 连接数据源 | SimpleDirectoryReader |
| Documents | 原始数据容器 | Document |
| Nodes | 分割后的数据块 | TextNode |
| Index | 索引结构 | VectorStoreIndex |
| Retriever | 检索器 | VectorIndexRetriever |
| Query Engine | 问答引擎 | RetrieverQueryEngine |

索引按检索方式分四类：VectorStoreIndex（向量相似度，语义搜索）、SummaryIndex（遍历所有节点，全文摘要）、TreeIndex（层级树，多级摘要）、KeywordTableIndex（关键词匹配，精确检索）。

用量的配置集中在 `Settings`（llm、embed_model、chunk_size 如 1024）。问答侧：`as_query_engine` 设 `similarity_top_k` 与 `response_mode`（如 `tree_summarize` 做多级摘要）做单轮问答；`as_chat_engine` 设 `chat_mode='context'` 保持多轮上下文。

## 具体示例

把一堆产品 PDF 用 SimpleDirectoryReader 读入 → `VectorStoreIndex.from_documents` 建索引 → `as_query_engine(similarity_top_k=5)` → 问"核心竞争优势是什么"，检索出相关块并综合成答案，全程无需手写切块与向量库。

它与 LangChain 的分工很清楚：

| 维度 | LlamaIndex | LangChain |
|------|-----------|------------|
| 核心优势 | 数据索引与检索 | 通用 Agent 开发 |
| RAG 能力 | 强 | 较强 |
| Agent 能力 | 中 | 强 |
| 学习曲线 | 较低 | 较高 |

## 何时用 / 何时不用

- **用**：以私有文档问答、RAG 为核心诉求时。
- **不用**：以复杂 Agent 编排、多工具协作为主时——LangChain / CrewAI 更合适；二者可组合：LlamaIndex 管检索、LangChain 管编排。

## 优劣与代价

✅ RAG 链路开箱即用，索引类型丰富，上手快。
⚠️ 通用编排与 Agent 能力弱于 LangChain。
⚠️ 检索质量高度依赖切块策略与 embedding 配置，调不好就"答非所问"。

## 与相关概念的区别

- **vs [[LangChain 框架全解析]]**：LangChain 偏通用编排与 Agent，LlamaIndex 偏数据 / 索引 / 检索。
- **vs [[RAG 与检索技术详解]]**：RAG 是方法论，LlamaIndex 是实现它的一个框架。

## 常见误区

- LlamaIndex 的核心优势是复杂的多 Agent 编排，比 LangChain 更擅长做 Agent。
- VectorStoreIndex 是唯一支持的索引类型，无法做关键词或树形检索。
- 用了 LlamaIndex 就不必关心切块与嵌入，它会自动跳过 embedding 步骤。

## 面试速答

> 🎯 LlamaIndex 把 RAG 整条链路标准化：SimpleDirectoryReader 连数据 → Document/Node 切块 → VectorStoreIndex 建索引 → Retriever 检索 → Query/Chat Engine 问答。RAG 强、通用 Agent 编排弱于 LangChain。
> 🔍 追问：四种索引各适合什么？（向量做语义搜索、Summary 做全文摘要、Tree 做多级摘要、Keyword 做精确匹配）
> 🔍 追问：query engine 与 chat engine 区别？（前者单轮问答，后者用 chat_mode 保持多轮上下文）

## 相关术语

[[LangChain 框架全解析]]、[[RAG 与检索技术详解]]、[[RAG 检索增强生成]]、[[CrewAI 多 Agent 框架]]、[[Agent 编排框架对比]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
