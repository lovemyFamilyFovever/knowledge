---
title: "RAG 检索增强生成"
tags: [人工智能, RAG]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# RAG 检索增强生成


> 📌 **导航**：本文是 **RAG 检索增强生成** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## 概述

**RAG（Retrieval-Augmented Generation）** 将外部知识检索与LLM生成相结合，解决LLM的**知识时效性**和**幻觉**问题。

## 基础架构

```
用户问题 → 检索模块(Retriever) → 相关文档 → 生成模块(Generator) → 最终回答
```

## 基础RAG实现

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 加载和分割
documents = TextLoader('knowledge.txt').load()
chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(documents)

# 向量存储
vectorstore = Chroma.from_documents(chunks, OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_kwargs={'k': 3})

# RAG Chain
template = '基于上下文回答:\n{context}\n\n问题：{question}\n回答：'
prompt = ChatPromptTemplate.from_template(template)

rag_chain = (
    {'context': retriever, 'question': RunnablePassthrough()}
    | prompt | ChatOpenAI(model='gpt-4o') | StrOutputParser()
)
result = rag_chain.invoke('什么是向量数据库？')
```

## Advanced RAG 技术

| 技术 | 说明 | 效果 |
|------|------|------|
| **HyDE** | 用假设答案检索 | 提高语义匹配 |
| **Multi-Query** | 多角度查询 | 提高召回率 |
| **Re-ranking** | 结果重排序 | 提高精确度 |
| **Sentence Window** | 扩展上下文 | 提高完整性 |
| **Parent-Child** | 子块检索父块返回 | 平衡粒度 |

## Graph RAG

将知识图谱与RAG结合，处理复杂实体关系查询。

```python
class GraphRAG:
    def __init__(self, kg, vectorstore):
        self.kg = kg
        self.vectorstore = vectorstore

    def query(self, question: str) -> str:
        vector_results = self.vectorstore.similarity_search(question, k=3)
        entities = self.extract_entities(question)
        graph_results = [self.kg.query_related(e) for e in entities]
        combined = self.merge_results(vector_results, graph_results)
        return self.llm.generate(question, combined)
```

## RAG vs Fine-tuning

| 维度 | RAG | Fine-tuning |
|------|-----|-------------|
| **知识更新** | 实时 | 需重新训练 |
| **成本** | 低 | 高 |
| **准确性** | 依赖检索质量 | 依赖训练数据 |
| **幻觉** | 较少 | 仍有风险 |
| **适用场景** | 知识密集型 | 风格调整 |

## RAG评估指标

| 指标 | 含义 |
|------|------|
| **Context Precision** | 检索文档的相关比例 |
| **Context Recall** | 相关文档的检索覆盖率 |
| **Faithfulness** | 回答是否忠实于上下文 |
| **Answer Relevancy** | 回答与问题的相关性 |

## 小结

RAG是最实用的LLM增强技术。基础RAG提供事实依据，Advanced RAG通过查询转换等提升质量，Graph RAG引入知识图谱处理复杂关系。
## RAG 完整流程图

<svg viewBox="0 0 800 350" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;font-family:Arial,sans-serif">
  <rect width="800" height="350" fill="#f8fafc" rx="12"/>
  <text x="400" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#1e293b">RAG (检索增强生成) 流程</text>
  <rect x="30" y="50" width="340" height="130" rx="8" fill="#dbeafe" stroke="#3b82f6" opacity="0.3"/>
  <text x="200" y="75" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e40af">离线索引阶段</text>
  <rect x="50" y="90" width="80" height="35" rx="6" fill="#93c5fd"/>
  <text x="90" y="112" text-anchor="middle" font-size="11" fill="#1e3a8a">文档库</text>
  <rect x="160" y="90" width="80" height="35" rx="6" fill="#93c5fd"/>
  <text x="200" y="112" text-anchor="middle" font-size="11" fill="#1e3a8a">文本分块</text>
  <rect x="270" y="90" width="80" height="35" rx="6" fill="#93c5fd"/>
  <text x="310" y="112" text-anchor="middle" font-size="11" fill="#1e3a8a">Embedding</text>
  <rect x="240" y="140" width="110" height="30" rx="4" fill="#60a5fa"/>
  <text x="295" y="160" text-anchor="middle" font-size="11" fill="white">向量数据库</text>
  <line x1="130" y1="107" x2="160" y2="107" stroke="#3b82f6" stroke-width="2"/>
  <line x1="240" y1="107" x2="270" y2="107" stroke="#3b82f6" stroke-width="2"/>
  <line x1="310" y1="125" x2="295" y2="140" stroke="#3b82f6" stroke-width="2"/>
  <rect x="420" y="50" width="360" height="250" rx="8" fill="#dcfce7" stroke="#22c55e" opacity="0.3"/>
  <text x="600" y="75" text-anchor="middle" font-size="13" font-weight="bold" fill="#166534">在线查询阶段</text>
  <rect x="440" y="90" width="80" height="35" rx="6" fill="#86efac"/>
  <text x="480" y="112" text-anchor="middle" font-size="11" fill="#166534">用户问题</text>
  <rect x="550" y="90" width="80" height="35" rx="6" fill="#86efac"/>
  <text x="590" y="112" text-anchor="middle" font-size="11" fill="#166534">Embedding</text>
  <rect x="660" y="90" width="100" height="35" rx="6" fill="#86efac"/>
  <text x="710" y="112" text-anchor="middle" font-size="11" fill="#166534">向量检索Top-K</text>
  <rect x="440" y="150" width="130" height="35" rx="6" fill="#86efac"/>
  <text x="505" y="172" text-anchor="middle" font-size="11" fill="#166534">拼接: 问题+上下文</text>
  <rect x="610" y="150" width="150" height="35" rx="6" fill="#4ade80"/>
  <text x="685" y="172" text-anchor="middle" font-size="12" font-weight="bold" fill="#14532d">LLM 生成答案</text>
  <rect x="610" y="220" width="150" height="35" rx="6" fill="#22c55e"/>
  <text x="685" y="242" text-anchor="middle" font-size="12" fill="white">最终回答</text>
  <line x1="530" y1="107" x2="550" y2="107" stroke="#22c55e" stroke-width="2"/>
  <line x1="630" y1="107" x2="660" y2="107" stroke="#22c55e" stroke-width="2"/>
  <line x1="570" y1="167" x2="610" y2="167" stroke="#22c55e" stroke-width="2"/>
  <line x1="685" y1="185" x2="685" y2="220" stroke="#22c55e" stroke-width="2"/>
  <path d="M 350 155 C 390 155, 410 155, 440 155" stroke="#64748b" stroke-width="2" stroke-dasharray="5,5"/>
  <text x="395" y="148" text-anchor="middle" font-size="10" fill="#64748b">检索</text>
  <text x="400" y="330" text-anchor="middle" font-size="12" fill="#475569">文档离线索引 + 在线检索增强生成 = RAG</text>
</svg>

## 相关术语

[[RAG 与检索技术详解]]、[[向量数据库技术]]、[[Embedding 技术详解]]、[[LangChain 框架全解析]]、[[LlamaIndex 框架指南]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
