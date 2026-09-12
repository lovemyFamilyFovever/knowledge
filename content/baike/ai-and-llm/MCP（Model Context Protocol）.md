---
title: "MCP（Model Context Protocol）"
tags: [人工智能, 协议]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# MCP（Model Context Protocol）


> 📌 **导航**：本文是 **MCP（Model Context Protocol）** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## 概述
**MCP（Model Context Protocol）** 是 Anthropic 提出的开放协议，标准化了 LLM 与外部工具/数据源的连接方式。

## 协议架构

```
LLM应用(Client) ←→ MCP协议 ←→ MCP Server（提供工具/资源）
```

| 组件 | 角色 | 说明 |
|------|------|------|
| **Client** | LLM应用 | 发起工具调用请求 |
| **Server** | 工具提供者 | 暴露工具和资源 |
| **Protocol** | 通信协议 | JSON-RPC 2.0 |

## Server 端实现
```python
from mcp import Server, Tool

server = Server('my-tools')

@server.tool()
def search_database(query: str, limit: int = 10) -> str:
    """搜索数据库中的记录"""
    results = db.search(query, limit=limit)
    return json.dumps(results, ensure_ascii=False)

@server.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """发送电子邮件"""
    email_client.send(to=to, subject=subject, body=body)
    return f'邮件已发送至 {to}'

@server.resource('docs://')
def get_documentation(path: str) -> str:
    """获取文档内容"""
    return read_file(f'./docs/{path}')
```

## Client 端使用
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 连接MCP Server
server_params = StdioServerParameters(command='python', args=['my_server.py'])
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # 发现可用工具
        tools = await session.list_tools()

        # 调用工具
        result = await session.call_tool('search_database', {'query': 'AI Agent'})

        # 读取资源
        doc = await session.read_resource('docs://api-reference')
```

## MCP vs Function Calling

| 维度 | MCP | Function Calling |
|------|-----|-----------------|
| **标准化** | 开放协议 | 厂商特定 |
| **可发现性** | 运行时发现工具 | 预定义工具 |
| **跨平台** | 任意Client/Server | 绑定特定LLM |
| **资源访问** | 支持资源订阅 | 仅函数调用 |
| **传输方式** | stdio/SSE/HTTP | API请求 |

## 工具发现
```python
# Client在运行时发现Server提供的工具
tools = await session.list_tools()
for tool in tools:
    print(f"工具: {tool.name}, 描述: {tool.description}")
    print(f"参数: {tool.inputSchema}")
```

## 生态系统

| Server | 功能 | 来源 |
|--------|------|------|
| **GitHub MCP** | GitHub操作 | 官方 |
| **PostgreSQL MCP** | 数据库操作 | 官方 |
| **Filesystem MCP** | 文件操作 | 官方 |
| **Slack MCP** | Slack消息 | 社区 |
| **自定义MCP** | 自有工具 | 自建 |

## 小结
MCP通过标准化协议连接LLM与外部工具，实现工具的可发现性和跨平台互操作。它正在成为AI Agent工具连接的事实标准。

## 相关术语

[[Function Calling 与 Tool Use]]、[[AI Agent 概述与核心架构]]、[[Agent 架构模式详解]]、[[LangChain 框架全解析]]、[[多 Agent 协作系统]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
