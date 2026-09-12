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

## 概述

**LangChain** 是最流行的 LLM 应用开发框架，提供模块化组件帮助快速构建 LLM 应用。

## 核心模块

| 模块 | 功能 | 关键类 |
|------|------|--------|
| **Models** | LLM封装 | ChatOpenAI, Ollama |
| **Prompts** | 提示词管理 | ChatPromptTemplate |
| **Chains** | 组件串联 | LLMChain, SequentialChain |
| **Agents** | 自主决策和工具调用 | AgentExecutor |
| **Tools** | 工具定义 | Tool, StructuredTool |
| **Memory** | 对话历史管理 | ConversationBufferMemory |
| **Retrievers** | 文档检索 | VectorStoreRetriever |
| **Parsers** | 输出格式化 | JsonOutputParser |

## Chain 模块

使用 LCEL（LangChain Expression Language）组合组件：

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template('请解释：{concept}')
llm = ChatOpenAI(model='gpt-4o')
chain = prompt | llm | StrOutputParser()
result = chain.invoke({'concept': '向量数据库'})
```

## Agent 模块

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    # 搜索互联网获取最新信息
    return f'搜索结果: {query}'

@tool
def calculate(expression: str) -> str:
    # 计算数学表达式
    return str(eval(expression))

llm = ChatOpenAI(model='gpt-4o', temperature=0)
tools = [search_web, calculate]
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(
    agent=agent, tools=tools,
    verbose=True, max_iterations=10,
    handle_parsing_errors=True,
)
result = executor.invoke({'input': '帮我计算2的10次方'})
```

## Tool 模块

```python
from langchain_core.tools import tool, StructuredTool
from pydantic import BaseModel, Field

@tool
def get_weather(city: str) -> str:
    # 获取指定城市的天气
    return f'{city}：晴，25C'

class SearchInput(BaseModel):
    query: str = Field(description='搜索关键词')
    num_results: int = Field(default=5)

search_tool = StructuredTool.from_function(
    func=lambda query, num_results=5: f'找到{num_results}条结果',
    name='web_search',
    description='搜索互联网',
    args_schema=SearchInput,
)
```

## Memory 模块

| 类型 | 特点 | 适用场景 |
|------|------|--------|
| **ConversationBufferMemory** | 完整历史 | 短对话 |
| **ConversationSummaryMemory** | 自动摘要 | 长对话 |
| **ConversationBufferWindowMemory** | 最近N轮 | 有限上下文 |
| **VectorStoreRetrieverMemory** | 向量检索 | 大量历史 |

```python
from langchain.memory import ConversationSummaryBufferMemory
memory = ConversationSummaryBufferMemory(
    llm=ChatOpenAI(model='gpt-4o-mini'),
    max_token_limit=2000,
    return_messages=True,
)
```

## RAG 集成

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

loader = PyPDFLoader('doc.pdf')
documents = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)
vectorstore = Chroma.from_documents(chunks, OpenAIEmbeddings())
qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model='gpt-4o'),
    retriever=vectorstore.as_retriever(search_kwargs={'k': 3}),
)
```

## 最佳实践

1. 优先使用LCEL而非旧Chain类
2. 工具描述要清晰无歧义
3. 设置max_iterations防止无限循环
4. 启用handle_parsing_errors提高鲁棒性

## 小结

LangChain 通过模块化设计标准化 LLM 应用开发。Chain串联组件，Agent自主决策，Tool扩展能力，Memory管理上下文。

## 相关术语

[[LlamaIndex 框架指南]]、[[CrewAI 多 Agent 框架]]、[[Agent 编排框架对比]]、[[Function Calling 与 Tool Use]]、[[AI Agent 概述与核心架构]]、[[RAG 与检索技术详解]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
