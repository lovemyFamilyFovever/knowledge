---
title: "DeepSeek Harness 模型接入层深度分析 — 第一部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 模型接入层"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 模型接入层深度分析 — 第一部分

## 1. LLM 抽象层设计

### 1.1 统一接口设计

DeepSeek Harness 的 LLM 抽象层采用了精心设计的**适配器模式 + Waterfall 拦截链**架构，核心定义在 `packages/llm/llm/src/index.ts` 中。

**核心类层次结构：**

```
HarnessError (error.ts)
  └── LlmError (index.ts)

Service (cordis)
  └── LlmRuntime (index.ts) — 注册表 + 流式调用 API

LlmAdapter (index.ts) — 抽象基类
  ├── DeepSeekAdapter (llm-deepseek/adapter.ts) — 直连 DeepSeek API
  └── PiAiAdapter (llm-pi-ai/adapter.ts) — 通过 pi-ai 库多 Provider
```

**`LlmRuntime`** 是整个 LLM 子系统的服务入口，继承自 Cordis 的 `Service`，注册为 `ctx.llm`。它承担三个核心职责：

1. **适配器注册表** — `registerAdapter(providers, adapter)` 将一个 `LlmAdapter` 实例绑定到一组 provider 路由上。注册是全有或全无的（all-or-nothing），任何路由冲突都会导致整个注册失败，错误码为 `DUPLICATE_ADAPTER`。返回的 `AdapterRegistrationHandle` 既是一个同步释放器，又携带 `replace(providers)` 方法，支持原子性的路由替换。

2. **可配置 Provider 目录** — `registerConfigurableProviders(entries)` 管理一个"目录"，记录哪些 provider 路由可以通过配置激活。目录条目包含 `provider`（路由键）、`displayName`（显示名）、`settingsNs`（设置命名空间）、`settingsPath`（设置路径）和可选的 `declared` 标记。

3. **流式模型调用 API** — `stream(options)` 和 `prepareCall(config)` 是核心调用入口。`stream` 方法通过 Cordis 的 `waterfall` 机制将实际的适配器流包装在 `llm/stream` 事件中，允许中间件（如重试、replay、路由）拦截或修改请求。

**统一请求模型** `GenerateOptions`（`types.ts`）定义了所有 provider 通用的请求结构：

```typescript
interface GenerateOptions {
  provider: string          // 注册的 provider 路由
  model: string             // 模型 id
  reasoningEffort?: ReasoningEffortId  // 推理努力级别
  messages: Message[]       // 对话消息
  system?: string           // 系统提示
  tools?: ToolSchema[]      // 工具定义
  temperature?: number
  maxTokens?: number
  stop?: string[]           // 停止序列
  signal?: AbortSignal      // 取消信号
  sessionId?: Branded<'SessionId'>
  purpose?: 'compaction' | 'session-title'
}
```

**统一响应模型** 采用流式 chunk 协议 `StreamChunk`（`types.ts`），这是一个封闭的联合类型：

```typescript
type StreamChunk =
  | { type: 'block-start'; index: number; blockType: ContentBlockType }
  | { type: 'text-delta'; index: number; text: string }
  | { type: 'reasoning-delta'; index: number; text: string }
  | { type: 'tool-call-delta'; index: number; id: CallId; name?: string; argumentsDelta: string }
  | { type: 'block-end'; index: number; block: ContentBlock }
  | { type: 'usage'; usage: TokenUsage }
  | { type: 'finish'; reason: FinishReason; replayState?: ReplayEnvelope }
```

这个设计的精妙之处在于：
- **Block 索引机制** — 多个内容块通过 `index` 交织，支持并行的文本、推理和工具调用流
- **Delta + Block-end 双重语义** — 增量推送的同时，`block-end` 携带最终组装的完整块
- **Finish 原因的可扩展性** — `FinishReasonMap` 通过声明合并扩展
- **Replay 状态分离** — `ReplayEnvelope` 将响应级和块级的适配器私有状态分离

### 1.2 模型 Provider 的注册机制

注册机制遵循几个关键原则：

**原子性与一致性**：`prepareRoutes` 方法在提交前验证整个候选路由集，冲突检测在写入前完成。`commitRoutes` 方法在一个同步区间内完成旧路由的删除和新路由的写入。

**生命周期管理**：注册通过 `ctx.effect()` 绑定到 Cordis fiber 的生命周期，fiber 释放时自动注销。`replace` 方法在同一 fiber 上原子替换路由。

**拓扑通知**：`emitAdaptersUpdated()` 发布 `llm/adapters-updated` 事件。关键设计：通知失败是隔离的——单个监听器的异常不会阻断后续监听器。

**`PreparedLlmCall` 机制**：将模型解析、配置验证和适配器注册绑定到一次调用中，确保配置变更不会在 prepare 和 dispatch 之间产生不一致。

### 1.3 请求/响应类型定义

**内容块类型系统** 采用声明合并的 `ContentBlockMap`：

```typescript
interface ContentBlockMap {
  'text': TextBlock          // 可见文本
  'reasoning': ReasoningBlock // 推理/思考内容
  'image': ImageBlock        // 图片引用
  'tool-call': ToolCallBlock // 工具调用请求
  'tool-result': ToolResultBlock // 工具调用结果
}
```

**消息系统** 定义了统一的消息模型，每条消息都有 `id`（稳定标识）、`role`、`content`（内容块）和 `source`（生产者归因）。消息创建后立即深冻结，确保不可变性。

**Token 使用量** 采用不相交计数：`inputTokens` 仅计未缓存输入，缓存读写分别报告。

---

## 2. 支持的模型类型

### 2.1 已支持的模型 Provider

**A. `llm-deepseek` — DeepSeek 官方适配器**

注册路由：`deepseek-official`

| 模型 ID | 名称 | Context Window | 输入模态 | 特殊能力 |
|---------|------|---------------|----------|----------|
| `deepseek-v4-flash` | DeepSeek-V4-Flash | 1,000,000 | text | — |
| `deepseek-v4-pro` | DeepSeek-V4-Pro | 1,000,000 | text | — |
| `deepseek-v4-flash-vision-exp` | DeepSeek-V4-Flash-Vision-Exp | 1,000,000 | text + image | 图像像素预算 640K |

推理努力级别：`off`、`low`、`high`、`max`（默认 `high`）

**B. `llm-pi-ai` — 通用 pi-ai 适配器**

通过 `@earendil-works/pi-ai` 库支持多个 provider：

| Provider 路由 | 说明 | 认证方式 |
|--------------|------|----------|
| `openai` | OpenAI 官方 | `OPENAI_API_KEY` |
| `anthropic` | Anthropic 官方 | `ANTHROPIC_API_KEY` |
| 任意自定义路由 | 如 `acme-gateway` | 自定义 `apiKeyEnv` |

### 2.2 每个 Provider 的配置方式

**DeepSeek 配置** 支持 `apiKeyEnv`（凭据引用）、`baseURL`（端点）、`thinking`（思维模式）、`reasoningEffort`（默认推理努力）、`maxTokens`、`models`（自定义模型目录）、`retryPolicy`（重试策略）等。

**Pi-AI 配置** 通过 `providers` 字典配置多个 provider，每个支持 `apiKeyEnv`、`api`（协议）、`baseURL`、`compat`（兼容性设置）、`models`、`reasoningEfforts` 等。

### 2.3 模型能力声明

能力元数据通过 `LlmResolvedModelInfo` 承载，包含 `context`（上下文窗口）、`defaultMaxTokens`（默认输出上限）、`reasoning`（推理能力）。输入模态通过 `ModelModality` 类型声明，支持 `'text'` 和 `'image'`。

---

## 3. 流式响应处理

### 3.1 Streaming 的实现方式

**DeepSeek 适配器的流式管道：**

```
HTTP fetch (POST /chat/completions, stream: true)
  → response.body (ReadableStream<BufferSource>)
    → parseSse() — SSE 帧解析 (eventsource-parser)
      → translate() — Wire chunks → StreamChunk 协议
        → LlmRuntime.adapterStream() — 错误规范化
          → ctx.waterfall('llm/stream') — 中间件拦截
            → 消费者
```

**Pi-AI 适配器的流式管道：**

```
pi-ai Models.streamSimple() → AssistantMessageEvent 流
  → toStreamChunks() — 事件翻译
    → LlmRuntime.adapterStream()
      → ctx.waterfall('llm/stream')
        → 消费者
```

### 3.2 事件流的处理管道

**Waterfall 拦截机制**：`LlmRuntime.streamWithRegistration` 通过 `ctx.waterfall` 将适配器流包装。Waterfall 监听器可以调用 `next()` 到达底层适配器流、yield 自己的 chunks 来短路、或修改 options 后再调用 next。

**不变量验证**：安装在 waterfall 的最前面，对每个 chunk 进行语法验证，包括块索引非负、delta 类型匹配、usage 唯一性、finish 后无 chunk 等。

**错误规范化**：`adapterStream` 方法将适配器抛出的异常捕获并转换为终端 `error` 或 `aborted` finish chunk。

### 3.3 背压控制

- **AsyncGenerator 背压**：JavaScript 的 AsyncGenerator 协议天然提供背压
- **空闲看门狗**：`idleWatchdog` 监控流的空闲状态，超时映射为 `TIMEOUT` 错误码
- **消费者中断**：`AbortController` 管理消费者生命周期
- **图片背压**：确定性的卸载策略，最旧图片替换为文本占位符
