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

## 概述

**LlamaIndex** 是专注于数据连接和检索的 LLM 框架，核心优势在于**将私有数据与 LLM 连接**，特别适合构建 RAG 应用。

## 核心概念

| 概念 | 说明 | 对应类 |
|------|------|--------|
| **Data Connectors** | 连接数据源 | SimpleDirectoryReader |
| **Documents** | 原始数据容器 | Document |
| **Nodes** | 分割后数据块 | TextNode |
| **Index** | 索引结构 | VectorStoreIndex |
| **Retriever** | 检索器 | VectorIndexRetriever |
| **Query Engine** | 问答引擎 | RetrieverQueryEngine |

## 数据连接

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    input_dir='./data', recursive=True,
    required_exts=['.pdf', '.txt'],
).load_data()
```

## 索引构建

```python
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.llm = OpenAI(model='gpt-4o', temperature=0)
Settings.embed_model = OpenAIEmbedding(model='text-embedding-3-small')
Settings.chunk_size = 1024

index = VectorStoreIndex.from_documents(documents, show_progress=True)
index.storage_context.persist(persist_dir='./storage')
```

### 索引类型对比

| 索引类型 | 检索方式 | 适用场景 |
|---------|---------|--------|
| **VectorStoreIndex** | 向量相似度 | 语义搜索 |
| **SummaryIndex** | 遍历所有节点 | 全文摘要 |
| **TreeIndex** | 层级树结构 | 多级摘要 |
| **KeywordTableIndex** | 关键词匹配 | 精确检索 |

## 查询引擎

```python
query_engine = index.as_query_engine(
    similarity_top_k=5,
    response_mode='tree_summarize',
)
response = query_engine.query('核心竞争优势是什么？')
```

## Chat Engine

```python
chat_engine = index.as_chat_engine(
    chat_mode='context',
    system_prompt='你是一个专业的技术顾问。',
)
r1 = chat_engine.chat('介绍项目背景')
r2 = chat_engine.chat('核心技术栈是什么？')  # 保持上下文
```

## 与LangChain对比

| 维度 | LlamaIndex | LangChain |
|------|-----------|------------|
| **核心优势** | 数据索引和检索 | 通用Agent开发 |
| **RAG能力** | ★★★★★ | ★★★★☆ |
| **Agent能力** | ★★★☆☆ | ★★★★★ |
| **学习曲线** | 较低 | 较高 |

## 小结

LlamaIndex是构建RAG应用的首选框架，数据连接、索引构建和查询引擎覆盖了完整链路。

## 相关术语

[[LangChain 框架全解析]]、[[RAG 与检索技术详解]]、[[RAG 检索增强生成]]、[[CrewAI 多 Agent 框架]]、[[Agent 编排框架对比]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
