---
title: "DeepSeek Harness 核心架构分析 — 第六部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 核心架构分析 — 第六部分

## LLM 适配器层深度分析

---

## 17. LLM 层总体架构

### 17.1 子包组成

LLM 适配器层由 5 个子包组成，每个负责 LLM 交互的一个正交维度：

| 子包 | 职责 | `ctx` 键 |
|---|---|---|
| `llm` | 核心 LLM 服务：适配器注册表、流式调用 API、类型定义、错误处理、块组装器 | `ctx.llm` |
| `llm-deepseek` | DeepSeek 适配器实现（OpenAI 兼容 SSE 协议） | — |
| `llm-pi-ai` | Pi AI 适配器实现 | — |
| `llm-retry` | 重试策略执行器插件 | — |
| `token-meter` | Token 使用量计量与投影服务 | `ctx.tokenMeter` |

### 17.2 核心抽象

LLM 层的核心抽象是 **provider 路由 + 适配器注册 + 流式 waterfall**：

```
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
```

---

## 18. 核心类与接口

### 18.1 LlmRuntime 服务

`LlmRuntime`（`ctx.llm`）是 LLM 层的核心服务，职责包括：

| 方法 | 职责 |
|---|---|
| `registerAdapter()` | 注册适配器到 provider 路由，返回可替换的句柄 |
| `registerConfigurableProviders()` | 声明可通过配置激活的 provider 目录 |
| `registerModelDiscovery()` | 注册模型发现回调 |
| `stream()` | 流式调用模型，经过 `llm/stream` waterfall |
| `prepareCall()` | 绑定适配器注册的一次性调用句柄 |
| `listProviders()` | 列出已注册的 provider |
| `listModels()` | 列出 provider 的模型目录 |
| `resolveModelInfo()` | 解析精确模型元数据 |
| `resolveCallConfig()` | 验证并默认化调用配置 |

**关键设计**：`registerAdapter()` 返回的 `AdapterRegistrationHandle` 支持原子性路由替换（`replace()`），确保在 HMR（热模块替换）期间不会出现注册间隙。

### 18.2 LlmAdapter 抽象类

`LlmAdapter` 是 provider 后端的抽象基类：

```typescript
abstract class LlmAdapter {
  providerInfo(provider: string): LlmProviderInfo
  providerRetryPolicy(provider: string): ResolvedRetryPolicy | undefined
  listModels(provider: string): Promise<readonly LlmModelInfo[]>
  resolveModel(provider: string, model: string, signal?: AbortSignal): Promise<LlmResolvedModelInfo>
  prepareCall(provider: string, model: string, signal?: AbortSignal): Promise<PreparedAdapterCall>
  abstract stream(options: GenerateOptions): AsyncIterable<StreamChunk>
}
```

**关键设计**：`prepareCall()` 方法将模型元数据和流式调度绑定到同一个适配器代次，防止设置变更在准备和调度之间组合不同代次的能力。

### 18.3 BlockAssembler

`BlockAssembler` 是增量 chunk 到消息的组装器，是 Agent Loop 构建 assistant 消息的唯一规范算法：

```typescript
class BlockAssembler {
  push(chunk: StreamChunk): void
  blocks(): ContentBlock[]
  interruptedBlocks(): ContentBlock[]
  get usage(): TokenUsage | undefined
  get finish(): FinishReason
  get replayState(): ReplayEnvelope | undefined
  message(source?: MessageSource): Message
}
```

**关键设计**：
- 容忍无 `block-start`/`block-end` 的 delta-only 协议
- `block-end` 关闭后忽略迟到的 delta（防止恶意适配器增长内存）
- max-token 截断时丢弃不安全的 tool-call 块
- 中断流只保留有非空白内容的 text/reasoning 块

### 18.4 PreparedLlmCall

`PreparedLlmCall` 是一次性的调用句柄，绑定适配器注册：

```typescript
interface PreparedLlmCall {
  readonly config: LlmCallConfig
  readonly retryPolicy: ResolvedRetryPolicy
  readonly context?: LlmModelContext
  readonly adapterDefaults: LlmCallConfigAdapterDefaults
  stream(options: GenerateOptions): AsyncIterable<StreamChunk>
}
```

**关键约束**：只能调度一次（`dispatched` 标记），且调度时的配置必须与准备时一致（`callConfigEquals` 检查）。

---

## 19. 流式传输机制

### 19.1 StreamChunk 协议

适配器发出的原始流式协议：

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

**协议规则**：
- `block-start` 开启一个块，`block-end` 关闭它（权威性，先到先得）
- 交错的 delta 通过 `index` 关联到对应的块
- `usage` 在终端 `finish` 之前发出
- 工具参数保持原始 JSON 字符串
- `finish` 携带 `replayState` 用于重放保真

### 19.2 llm/stream Waterfall

`LlmRuntime.stream()` 通过 Cordis 的 `waterfall` 机制包装：

```typescript
private streamWithRegistration(options, prepared?) {
  return this.ctx.waterfall(
    this,
    'llm/stream',
    options,
    () => this.adapterStream(options, prepared),
  )
}
```

插件可以：
- **拦截请求**：替换 options（路由、模型、参数）
- **注入重试**：包装返回的 AsyncIterable
- **短路调用**：yield 自己的 chunks 替代适配器

### 19.3 适配器边界

`adapterStream()` 方法是最终的适配器边界：

1. 选择适配器（从准备的注册或按 provider 查找）
2. 调用 `adapter.prepareCall()` 获取模型元数据和调度函数
3. 验证配置一致性
4. 处理模态投影（不支持图片的模型自动转换图片为文本描述）
5. 过滤重放状态（只保留同一适配器的重放元数据）
6. 调用适配器的 `stream()` 方法
7. 将适配器异常转换为终端 `error` 或 `aborted` finish chunk

**关键设计**：适配器选择、调度和迭代器构建中的异常都转换为流协议的终端 finish chunk，而不是抛出。中间件和下游消费者的异常保持抛出。

---

## 20. 适配器注册与路由

### 20.1 注册流程

```typescript
const handle = ctx.llm.registerAdapter(['deepseek', 'deepseek-cn'], adapter)
// handle() - 释放所有路由
// handle.replace(['new-route']) - 原子性替换路由
```

注册流程：
1. 验证 provider 名称非空且唯一
2. 调用 `adapter.providerInfo()` 获取元数据
3. 解析重试策略（适配器提供或使用默认值）
4. 原子性提交到注册表
5. 发出 `llm/adapters-updated` 事件

### 20.2 可配置 Provider 目录

```typescript
const handle = ctx.llm.registerConfigurableProviders([
  { provider: 'deepseek', displayName: 'DeepSeek', settingsNs: 'deepseek', settingsPath: [] }
])
```

目录是适配器插件可以通过配置激活的 provider 列表。配置表面将此目录与 `listProviders()` 合并，提供每个可配置 provider 的在线/离线状态。

### 20.3 模型发现

```typescript
ctx.llm.registerModelDiscovery('deepseek', async (request) => {
  // 查询 endpoint 获取模型列表
  return [{ id: 'deepseek-chat', name: 'DeepSeek Chat' }]
})
```

模型发现用于配置表面在用户编辑 draft 时查询端点，不需要已存储的路由。

---

## 21. 错误处理体系

### 21.1 错误层次

```
Error
  └── HarnessError（基础错误，携带稳定 code）
        ├── LlmError（LLM 相关失败）
        │     ├── NO_ADAPTER
        │     ├── DUPLICATE_ADAPTER
        │     ├── INVALID_ADAPTER
        │     ├── INVALID_CREDENTIAL
        │     ├── MISSING_CREDENTIAL
        │     ├── RATE_LIMIT
        │     ├── SERVER
        │     ├── TIMEOUT
        │     ├── TRANSPORT
        │     ├── CONTEXT_WINDOW_EXCEEDED
        │     ├── QUOTA
        │     ├── EMPTY_RESPONSE
        │     ├── UNSUPPORTED_REASONING_EFFORT
        │     └── INVALID_PREPARED_CALL
        ├── ToolNotFoundError
        └── ToolOutputError
```

### 21.2 LlmFailure 结构

所有适配器异常最终标准化为 `LlmFailure`：

```typescript
interface LlmFailure {
  readonly message: string
  readonly code: string
  readonly status?: number
  readonly providerRetryAfterMs?: number
  readonly requestId?: ProviderRequestId
}
```

### 21.3 适配器失败标准化

`normalizeLlmFailure()` 函数处理任意适配器抛出的值：

1. 非 Error 值包装为 `HarnessError`（code: `UNKNOWN`）
2. 尝试读取 `error.failure` 的 own data property（避免 SDK getter 陷阱）
3. 验证 `failure.code` 与 `error.code` 一致
4. 只信任 Harness 拥有的 code，第三方 SDK code 不作为路由依据

### 21.4 上下文溢出检测

`isContextWindowExceededError()` 通过正则表达式匹配多种 provider 的上下文溢出措辞：

- 结构化：`context_length_exceeded`、`context_window_overflow`
- 最大限制：`maximum context length`、`max supported context window`
- 请求过大：`request too large for model context`
- 超过模型上下文：`input exceeds the model context window`

---

## 22. 重试策略

### 22.1 策略配置

两种重试模式：

| 模式 | 说明 | 配置 |
|---|---|---|
| `normal` | 只重试配置的瞬态失败码 | `maxRetries`（默认 5）、`retryableCodes`、`backoff` |
| `always` | 重试所有失败直到成功、取消或处置 | `backoff` |

### 22.2 退避算法

```typescript
function localDelay(config, retry, random) {
  const exponent = Math.min(retry - 1, 1024)
  const exponential = Math.min(config.initialDelayMs * 2 ** exponent, config.maxDelayMs)
  const jitter = 1 - config.jitterRatio + 2 * config.jitterRatio * random()
  return Math.min(exponential * jitter, config.maxDelayMs)
}
```

- 默认初始延迟：500ms
- 默认最大延迟：10,000ms
- 默认抖动比率：0.1（±10%）
- 指数退避，上限 1024 次方

### 22.3 Provider Retry-After 支持

当 `failure.providerRetryAfterMs` 存在且有效时：
- 如果不超过 `maxDelayMs`：使用 provider 延迟
- 如果超过 `maxDelayMs` 且模式为 `normal`：放弃重试
- 如果超过 `maxDelayMs` 且模式为 `always`：使用本地延迟

### 22.4 持久化重试记录

每次重试都记录为会话事件：
- `llm/retry`：重试调度（包含 failure、delay、policy）
- `llm/retry-started`：重试开始（延迟后）

这使得重试历史可重现、可调试。

### 22.5 默认可重试码

```typescript
const DEFAULT_RETRYABLE_CODES = [
  'EMPTY_RESPONSE',  // 空响应（安全重试）
  'RATE_LIMIT',      // 速率限制
  'SERVER',          // 服务器错误
  'TIMEOUT',         // 超时
  'TRANSPORT',       // 传输错误
]
```

---

## 23. DeepSeek 适配器实现

### 23.1 架构

DeepSeek 适配器是 **transport-only**：连接事实通过 thunk 解析，bearer token 通过 per-request 解析器获取。注册插件拥有验证、分层和凭据策略。

```
DeepSeekAdapterOptions
  ├── options: () => DeepSeekConnectionOptions（每次操作调用一次）
  ├── resolveApiKey: (connection) => Promise<string>
  ├── resolveUserId: () => AnonymousUserId
  ├── resolveAttachments?: () => AttachmentStore
  └── resolveFiles?: () => DeepSeekFileStore
```

### 23.2 连接选项

```typescript
interface DeepSeekConnectionOptions {
  baseURL: string                    // 端点基础 URL
  apiKeyEnv: CredentialRef           // 凭据引用（非明文）
  defaults: RequestDefaults          // 请求默认值
  maxTokens: number                  // 默认输出上限
  defaultContextWindow: number       // 默认上下文窗口
  models: DeepSeekCatalogModel[]     // 模型目录
  streamIdleTimeoutMs: number        // 流空闲超时
  retryPolicy: ResolvedRetryPolicy   // 重试策略
  // ... 图片处理选项
}
```

### 23.3 推理努力级别

DeepSeek 支持 4 个推理努力级别：
- `off`：关闭推理
- `low`：低推理
- `high`：高推理
- `max`：最大推理

### 23.4 图片处理

DeepSeek 适配器支持复杂的图片处理流水线：
1. 收集请求中的图片引用
2. 通过 Files API 上传图片（可配置超时和配额恢复）
3. 如果 Files API 失败，回退到 base64 内联
4. 按像素预算和字节上限裁剪图片
5. 不支持图片的模型自动转换为文本描述

### 23.5 流空闲超时

`DEFAULT_STREAM_IDLE_TIMEOUT_MS = 300_000`（5 分钟）

适配器使用 `idleWatchdog` 监控流读取的空闲时间，超过阈值时中止连接。

---

## 24. Token 计量服务

### 24.1 TokenMeter 服务

`TokenMeter`（`ctx.tokenMeter`）是全应用范围的 token 计量服务：

- 重放感知：从会话事件流重建 token 状态
- 增量同步：只处理新事件
- 投影注册：注册 token 使用量、上下文压力和上下文分解投影

### 24.2 计量模型

```typescript
function usageTokens(usage: TokenUsage): number {
  return usage.inputTokens
    + (usage.cacheReadTokens ?? 0)
    + (usage.cacheWriteTokens ?? 0)
    + usage.outputTokens
}
```

Token 使用量是**不相交**的：`inputTokens` 是未缓存的输入，缓存输入单独报告为 `cacheReadTokens`/`cacheWriteTokens`。

### 24.3 Surface Token 折叠

`foldSurfaceTokens()` 从 Surface 事件流增量构建 token 计量：
- 跟踪每个表面节点的 token 估算
- 处理 `replace` 操作（压缩）的 token 增减
- 维护请求头变化对 token 估算的影响

---

## 25. 设计模式总结

| 模式 | 应用 | 说明 |
|---|---|---|
| **Waterfall 拦截** | `llm/stream` | 插件可拦截、替换或短路任何模型调用 |
| **Prepared Call** | `prepareCall()` | 绑定适配器注册的一次性调用句柄 |
| **深度冻结** | `deepFreeze()` | 迭代式深度冻结，跳过 AbortSignal |
| **失败标准化** | `normalizeLlmFailure()` | 任意异常 → 结构化 `LlmFailure` |
| **指数退避 + 抖动** | `localDelay()` | 可配置的退避策略 |
| **增量组装** | `BlockAssembler` | chunk → 块 → 消息的增量构建 |
| **原子替换** | `handle.replace()` | 注册路由的原子性热替换 |
| **模态投影** | `projectImagesForTextModel()` | 不支持图片的模型自动降级 |
| **重放保真** | `ReplayEnvelope` | 适配器私有的重放元数据 |
