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

## 定义

**一句话定义：** MCP（Model Context Protocol）是 Anthropic 提出的开放协议，用统一方式让 LLM 应用（Client）发现并调用外部工具与资源（Server），把"接工具"变成跨厂商可互操作的标准件。

**通俗类比：** 像 AI 界的 USB 接口——工具方按同一接口做"USB 设备（MCP Server）"，任何支持 MCP 的模型应用都能即插即用，不必为每个模型各写一套驱动。

## 为什么需要它

各家的 Function Calling 接口不一、工具与模型绑定，导致重复集成、难以复用。MCP 让工具与数据以标准协议对外暴露一次，任何 Client 都能在运行时发现并调用，从而形成生态级的复用，而非一个个孤岛。

## 核心机制

架构上是一个 Client ↔ Server 的会话，底座是 JSON-RPC 2.0：

| 组件 | 角色 | 说明 |
|------|------|------|
| Client | LLM 应用 | 发起工具调用请求 |
| Server | 工具/数据提供方 | 暴露工具与资源 |
| Protocol | 通信协议 | JSON-RPC 2.0，传输可走 stdio / SSE / HTTP |

Server 侧用装饰器把函数注册为工具、把文件/文档注册为资源；Client 侧在运行时 `list_tools` 发现可用工具（含 name、description、inputSchema），用 `call_tool` 调用、`read_resource` 读取，还能订阅资源变化。它对外暴露三类原语：**Tools（可调用函数）、Resources（可读数据）、Prompts（模板）**。

与原生 Function Calling 的关键差异：

| 维度 | MCP | Function Calling |
|------|-----|-----------------|
| 标准化 | 开放协议 | 厂商特定 |
| 可发现性 | 运行时发现工具 | 预定义工具 |
| 跨平台 | 任意 Client/Server | 绑定特定 LLM |
| 资源访问 | 支持资源与订阅 | 仅函数调用 |
| 传输方式 | stdio / SSE / HTTP | API 请求 |

## 具体示例

一个 GitHub MCP Server 暴露 `create_issue`、`search_code` 等工具；任何接入它的 MCP Client 都能自动列出这些工具并调用，无需为每个模型重写一套集成。官方与社区已有 GitHub、PostgreSQL、Filesystem、Slack 等一批现成 Server，也可自建接入自有工具。

## 何时用 / 何时不用

- **用**：希望工具 / 数据一次接入、跨多个模型应用复用，或搭建开放的工具生态时。
- **不用**：单一封闭应用、只需厂商原生 Function Calling 且不需跨平台时。

## 优劣与代价

✅ 标准化、运行时可发现、跨厂商互操作，促进工具生态复用。
⚠️ 协议较新，生态与安全边界仍在成型。
⚠️ "运行时发现并调用外部 Server"引入信任与权限治理问题——接入不可信 Server 有安全风险。

## 与相关概念的区别

- **vs [[Function Calling 与 Tool Use]]**：Function Calling 是"模型决定调哪个函数"的能力、常绑定厂商；MCP 是"工具如何被标准化暴露与发现"的开放协议层，二者互补。
- **vs [[Agent 架构模式详解]]**：MCP 提供工具接入的基础设施，架构模式提供任务的控制流。

## 常见误区

- MCP 是某家厂商私有的 Function Calling API，换个模型厂商就用不了。
- MCP Server 只能暴露可调用的工具，无法提供可读取的资源。
- 接入任意第三方 MCP Server 都是安全的，不必做权限与信任治理。

## 面试速答

> 🎯 MCP 是 Anthropic 提出的开放协议：把 LLM 应用当 Client、工具与数据方当 Server，Server 一次性暴露 Tools/Resources/Prompts，Client 运行时 list_tools 发现、call_tool 调用；代价是协议较新、需治理接入信任与权限。
> 🔍 追问：MCP 和 Function Calling 什么关系？（互补：FC 是模型选函数的能力，MCP 是工具如何标准化暴露 / 发现的协议层）
> 🔍 追问：MCP 除了工具还提供什么原语？（Resources 可读资源、Prompts 模板，且支持运行时订阅）

## 相关术语

[[Function Calling 与 Tool Use]]、[[AI Agent 概述与核心架构]]、[[Agent 架构模式详解]]、[[LangChain 框架全解析]]、[[多 Agent 协作系统]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
