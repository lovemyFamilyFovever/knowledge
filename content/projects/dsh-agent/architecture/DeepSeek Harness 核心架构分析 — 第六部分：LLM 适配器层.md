---
title: "DeepSeek Harness 核心架构分析 — 第六部分：LLM 适配器层"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 核心架构分析

第六部分：LLM 适配器层深度分析

## 17. LLM 层总体架构

### 17.1 子包组成

| 子包 | 职责 | `ctx` 键 |
| --- | --- | --- |
| `llm` | 核心 LLM 服务：适配器注册表、流式调用 API、类型定义、错误处理、块组装器 | `ctx.llm` |
| `llm-deepseek` | DeepSeek 适配器实现（OpenAI 兼容 SSE 协议） | — |
| `llm-pi-ai` | Pi AI 适配器实现 | — |
| `llm-retry` | 重试策略执行器插件 | — |
| `token-meter` | Token 使用量计量与投影服务 | `ctx.tokenMeter` |

### 17.2 核心抽象

LLM 层的核心抽象是 provider 路由 + 适配器注册 + 流式 waterfall：

Agent Loop
  ↓ ctx.llm.stream(options)
LlmRuntime
  ↓ 查找 provider → AdapterRegistration
  ↓ llm/stream waterfall（插件可拦截）
  ↓ adapterStream()（适配器边界）
  ↓ SSE 解析 → StreamChunk 流
BlockAssembler
  ↓ 组装完整 ContentBlock[]
Session.append('assistant/message')

## 18. 核心类与接口

### 18.1 LlmRuntime 服务

LlmRuntime（ctx.llm）是 LLM 层的核心服务：

| 方法 | 职责 |
| --- | --- |
| `registerAdapter()` | 注册适配器到 provider 路由，返回可原子替换的句柄 |
| `registerConfigurableProviders()` | 声明可通过配置激活的 provider 目录 |
| `registerModelDiscovery()` | 注册模型发现回调 |
| `stream()` | 流式调用模型，经过 `llm/stream` waterfall |
| `prepareCall()` | 绑定适配器注册的一次性调用句柄 |
| `listProviders()` | 列出已注册的 provider |
| `listModels()` | 列出 provider 的模型目录 |
| `resolveModelInfo()` | 解析精确模型元数据 |
| `resolveCallConfig()` | 验证并默认化调用配置 |

关键设计：registerAdapter() 返回的 AdapterRegistrationHandle 支持原子性路由替换（replace()），确保在 HMR 期间不会出现注册间隙。

### 18.2 LlmAdapter 抽象类

LlmAdapter 是 provider 后端的抽象基类，唯一的必须实现方法是 stream()：

```
abstract class LlmAdapter {
  providerInfo(provider: string): LlmProviderInfo
  providerRetryPolicy(provider: string): ResolvedRetryPolicy | undefined
  listModels(provider: string): Promise<readonly LlmModelInfo[]>
  resolveModel(provider: string, model: string, signal?: AbortSignal): Promise<LlmResolvedModelInfo>
  prepareCall(provider: string, model: string, signal?: AbortSignal): Promise<PreparedAdapterCall>
  abstract stream(options: GenerateOptions): AsyncIterable<StreamChunk>
}
```

关键设计：prepareCall() 方法将模型元数据和流式调度绑定到同一个适配器代次，防止设置变更在准备和调度之间组合不同代次的能力。

### 18.3 BlockAssembler

增量 chunk 到消息的组装器，是 Agent Loop 构建 assistant 消息的唯一规范算法：

| 方法 | 职责 |
| --- | --- |
| `push(chunk)` | 喂入一个 chunk，增量更新组装状态 |
| `blocks()` | 组装所有已见的块（max-token 截断时丢弃不安全的 tool-call） |
| `interruptedBlocks()` | 中断流的安全前缀（只保留有内容的 text/reasoning） |
| `usage` | 来自 `usage` chunk 的 token 计量 |
| `finish` | 完成原因（默认 `{kind: 'stop'}`） |
| `replayState` | 重放元数据，按块裁剪对齐 |
| `message()` | 组装的 assistant 消息 |

### 18.4 PreparedLlmCall

一次性的调用句柄，绑定适配器注册。只能调度一次，且调度时的配置必须与准备时一致。

## 19. 流式传输机制

### 19.1 StreamChunk 协议

| Chunk 类型 | 说明 |
| --- | --- |
| `block-start` | 开启一个块（`index` + `blockType`） |
| `text-delta` | 文本增量（`index` + `text`） |
| `reasoning-delta` | 推理增量（`index` + `text`） |
| `tool-call-delta` | 工具调用增量（`index` + `id` + `argumentsDelta`） |
| `block-end` | 关闭一个块（权威性，先到先得） |
| `usage` | Token 计量（在 finish 之前） |
| `finish` | 终端完成（`reason` + 可选 `replayState`） |

### 19.2 llm/stream Waterfall

插件可以拦截、替换或短路任何模型调用：

```
private streamWithRegistration(options, prepared?) {
  return this.ctx.waterfall(
    this, 'llm/stream', options,
    () => this.adapterStream(options, prepared),
  )
}
```

### 19.3 适配器边界

adapterStream() 是最终的适配器边界。关键设计：适配器选择、调度和迭代器构建中的异常都转换为流协议的终端 finish chunk，而不是抛出。中间件和下游消费者的异常保持抛出。

## 20. 适配器注册与路由

### 20.1 注册流程

- 验证 provider 名称非空且唯一

- 调用 `adapter.providerInfo()` 获取元数据

- 解析重试策略（适配器提供或使用默认值）

- 原子性提交到注册表

- 发出 `llm/adapters-updated` 事件

### 20.2 可配置 Provider 目录

目录是适配器插件可以通过配置激活的 provider 列表。配置表面将此目录与 listProviders() 合并，提供每个可配置 provider 的在线/离线状态。

## 21. 错误处理体系

### 21.1 错误层次

```
Error
  └── HarnessError（基础错误，携带稳定 code）
        ├── LlmError（LLM 相关失败）
        │     ├── NO_ADAPTER / DUPLICATE_ADAPTER / INVALID_ADAPTER
        │     ├── INVALID_CREDENTIAL / MISSING_CREDENTIAL
        │     ├── RATE_LIMIT / SERVER / TIMEOUT / TRANSPORT
        │     ├── CONTEXT_WINDOW_EXCEEDED / QUOTA / EMPTY_RESPONSE
        │     ├── UNSUPPORTED_REASONING_EFFORT
        │     └── INVALID_PREPARED_CALL
        ├── ToolNotFoundError
        └── ToolOutputError
```

### 21.2 LlmFailure 结构

所有适配器异常最终标准化为 LlmFailure，包含 message、code、可选的 status、providerRetryAfterMs 和 requestId。

### 21.3 上下文溢出检测

isContextWindowExceededError() 通过正则表达式匹配多种 provider 的上下文溢出措辞，包括结构化码、最大限制、请求过大和超过模型上下文等模式。

## 22. 重试策略

### 22.1 策略配置

| 模式 | 说明 | 配置 |
| --- | --- | --- |
| `normal` | 只重试配置的瞬态失败码 | `maxRetries`（默认 5）、`retryableCodes`、`backoff` |
| `always` | 重试所有失败直到成功、取消或处置 | `backoff` |

### 22.2 退避算法

有界指数退避 + 对称抖动：

- 默认初始延迟：500ms

- 默认最大延迟：10,000ms

- 默认抖动比率：0.1（±10%）

- 指数退避，上限 1024 次方

### 22.3 默认可重试码

- `EMPTY_RESPONSE` — 空响应（安全重试）

- `RATE_LIMIT` — 速率限制

- `SERVER` — 服务器错误

- `TIMEOUT` — 超时

- `TRANSPORT` — 传输错误

## 23. DeepSeek 适配器实现

### 23.1 架构

DeepSeek 适配器是 transport-only：连接事实通过 thunk 解析，bearer token 通过 per-request 解析器获取。注册插件拥有验证、分层和凭据策略。

### 23.2 推理努力级别

DeepSeek 支持 4 个推理努力级别：off（关闭推理）、low（低推理）、high（高推理）、max（最大推理）。

### 23.3 图片处理

- 收集请求中的图片引用

- 通过 Files API 上传图片（可配置超时和配额恢复）

- 如果 Files API 失败，回退到 base64 内联

- 按像素预算和字节上限裁剪图片

- 不支持图片的模型自动转换为文本描述

### 23.4 默认值

| 参数 | 默认值 |
| --- | --- |
| 流空闲超时 | 300,000ms（5 分钟） |
| 上下文窗口 | 1,000,000 tokens |
| 最大输出 | 256,000 tokens |
| 最大文件字节 | 128 MB |
| 最大内联图片字节 | 20 MB |
| 最大图片数 | 600 |

## 24. Token 计量服务

### 24.1 TokenMeter 服务

TokenMeter（ctx.tokenMeter）是全应用范围的 token 计量服务，具有重放感知和增量同步能力。

### 24.2 计量模型

Token 使用量是不相交的：inputTokens 是未缓存的输入，缓存输入单独报告为 cacheReadTokens/cacheWriteTokens。

## 25. 设计模式总结

| 模式 | 应用 | 说明 |
| --- | --- | --- |
| **Waterfall 拦截** | `llm/stream` | 插件可拦截、替换或短路任何模型调用 |
| **Prepared Call** | `prepareCall()` | 绑定适配器注册的一次性调用句柄 |
| **深度冻结** | `deepFreeze()` | 迭代式深度冻结，跳过 AbortSignal |
| **失败标准化** | `normalizeLlmFailure()` | 任意异常 → 结构化 `LlmFailure` |
| **指数退避 + 抖动** | `localDelay()` | 可配置的退避策略 |
| **增量组装** | `BlockAssembler` | chunk → 块 → 消息的增量构建 |
| **原子替换** | `handle.replace()` | 注册路由的原子性热替换 |
| **模态投影** | `projectImagesForTextModel()` | 不支持图片的模型自动降级 |
| **重放保真** | `ReplayEnvelope` | 适配器私有的重放元数据 |

DeepSeek Harness 核心架构分析 — 第六部分：LLM 适配器层 | 生成日期：2026-08-29
