---
title: "DeepSeek Harness 模型接入层深度分析 — 第三部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 模型接入层"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 模型接入层深度分析 — 第三部分

## 7. 与各主流模型 API 的兼容性

### 7.1 OpenAI API 兼容性

DeepSeek 适配器直接实现了 OpenAI Chat Completions API 的有线格式（`llm-deepseek/types.ts`）：

**请求兼容**：
- `POST /chat/completions` 端点
- `stream: true` + `stream_options: { include_usage: true }`
- OpenAI 格式的 messages（system/user/assistant/tool 角色）
- OpenAI 格式的 tools（`type: 'function'`）
- `stop` 停止序列
- `temperature`、`max_tokens`

**DeepSeek 特有扩展**：
- `thinking: { type: 'enabled' | 'disabled' }` — 思维模式开关（顶层，非 extra_body）
- `reasoning_effort: 'low' | 'high' | 'max'` — 推理努力级别
- `reasoning_content` — assistant 历史消息中的 CoT 回传
- `file` 类型内容部分 — Files API 引用

**SSE 格式**：
- 标准 OpenAI SSE 格式（`data: {...}\n\n`）
- `[DONE]` 终止符
- finish_reason 映射：`stop` → stop、`tool_calls` → tool-calls、`length` → max-tokens

**Token 使用量**：
- `prompt_tokens` 包含缓存命中（需减去 `prompt_cache_hit_tokens`）
- `prompt_tokens_details.cached_tokens` — OpenAI 兼容拼写
- `completion_tokens_details.reasoning_tokens` — 推理 token

### 7.2 Anthropic API 兼容性

Anthropic 支持通过 pi-ai 适配器实现，pi-ai 库内部处理 Anthropic Messages API 的有线格式翻译。Harness 层面的特殊处理：

- 推理能力：pi-ai 的 `getSupportedThinkingLevels` 查询模型支持的思考级别
- 上下文溢出：pi-ai 的 `isContextOverflow` 函数检测，加上 Harness 自己的正则匹配
- 流事件翻译：pi-ai 的 `AssistantMessageEvent` 流翻译为 Harness `StreamChunk`

### 7.3 自定义 Provider 的扩展方式

**方式一：通过 pi-ai 手动声明路由**

```yaml
providers:
  my-gateway:
    displayName: My Gateway
    apiKeyEnv: MY_API_KEY
    api: openai-completions
    baseURL: https://gateway.example/v1
    compat:
      thinkingFormat: deepseek
    models:
      - id: my-model
        name: My Model
        contextWindow: 131072
        maxTokens: 8192
        reasoningEfforts:
          off:
          high: high
```

**方式二：实现 `LlmAdapter` 抽象类**

需要实现的唯一必需方法：
```typescript
abstract stream(options: GenerateOptions): AsyncIterable<StreamChunk>
```

可选覆盖：
- `providerInfo(provider)` — 显示元数据
- `providerRetryPolicy(provider)` — 重试策略
- `listModels(provider)` — 模型目录
- `resolveModel(provider, model, signal)` — 精确模型元数据
- `prepareCall(provider, model, signal)` — 绑定一代的调用准备

然后注册：
```typescript
ctx.llm.registerAdapter(['my-provider'], new MyAdapter())
ctx.llm.registerConfigurableProviders([{
  provider: 'my-provider',
  displayName: 'My Provider',
  settingsNs: 'my-plugin',
  settingsPath: [],
}])
```

**内容块的可扩展性**：`ContentBlockMap` 和 `FinishReasonMap` 都支持声明合并，插件可以添加新的块类型和终止原因。消费者处理时应 fall through 未知变体。

---

## 8. 性能和成本优化

### 8.1 缓存机制

**Token 缓存跟踪**（`TokenUsage`）：

```typescript
interface TokenUsage {
  inputTokens: number       // 未缓存输入
  outputTokens: number      // 输出
  cacheReadTokens?: number  // 缓存读取
  cacheWriteTokens?: number // 缓存写入
  reasoningTokens?: number  // 推理 token
}
```

DeepSeek 的 `prompt_tokens` 包含缓存命中，Harness 在 `translate.ts` 的 `mapUsage` 中减去。

**配置缓存**：适配器选项通过 `lastRaw` / `lastGood` 模式缓存，只有当原始配置快照的引用身份变化时才重新解析。

**文件上传复用**（DeepSeek）：`DeepSeekFileStore` 维护已上传文件的索引，在 `fileRefreshMarginSeconds`（默认 1 小时）内复用。配额耗尽时清理最旧的 harness 拥有文件（默认 100 个一批）。

### 8.2 Token 计量

**`TokenMeter` 服务** 提供：

1. **请求压力测量** — `measure(session, requestHeader)` 返回当前的 token 消耗估算
2. **Provider 使用量锚点** — 当最后一次成功调用的 provider 使用量 ≥ 启发式估算时，使用 provider 报告的精确值
3. **表面增量跟踪** — `surfaceDeltaTokens` 跟踪锚点之后的表面变化
4. **启发式估价** — `estimateMessage` / `estimateHeader` 对消息和请求头进行 token 估价

Token 计量采用**回放式同步**：通过 `_sync(session)` 逐事件回放，维护 header、surface、stepStart、anchor 状态。

**三个投影定义**：
- `tokenUsageProjection` — 累积 token 使用量
- `contextPressureProjection` — 上下文压力百分比
- `contextBreakdownProjection` — 按类别的 token 分解

### 8.3 请求合并

当前架构中没有显式的请求合并机制。每个 `GenerateOptions` 产生一个独立的 HTTP 请求。这是合理的——LLM 请求通常需要完整的对话上下文，合并的收益有限。

**请求批处理的隐式支持**：
- 工具调用可以并行执行（多个 tool-call 块在同一响应中）
- 子 agent 可以并行运行（通过 `subagent` 服务）

---

## 9. 改进建议

### 9.1 架构层面

**A. HTTP 客户端抽象**

DeepSeek 适配器直接使用 `fetch`，有一个 TODO 标注：
```typescript
// TODO(http): adopt the Cordis HTTP service when shared transport configuration
// outweighs its additional runtime dependencies.
```

建议：引入统一的 HTTP 客户端服务，支持连接池、代理、TLS 配置；统一 User-Agent、请求 ID 等头部注入。

**B. 流式传输标准化**

DeepSeek 和 Pi-AI 的流式管道虽然功能等价，但实现路径不同。可以考虑定义一个 `StreamTranslator` 抽象，统一翻译层的接口。

**C. 模型发现增强**

当前的 `registerModelDiscovery` 机制是简单的异步函数注册。可以增强为缓存发现结果（带 TTL）、批量发现（多个端点并行）、发现结果的结构化验证。

### 9.2 错误处理

**A. 错误码标准化**

Pi-AI 适配器的 `classifyPiAiError` 依赖文本模式匹配，这是脆弱的。建议 pi-ai 库提供结构化的错误代码，建立 provider 错误到 Harness 错误码的映射注册表。

**B. 错误恢复策略增强**

- **部分重试** — 对于并行工具调用中的单个失败，只重试失败的调用
- **降级策略** — 当首选模型不可用时自动切换到备用模型
- **断路器** — 对持续失败的 provider 短路，避免无谓的重试

### 9.3 性能优化

**A. 流式 Token 计数**

当前的 TokenMeter 使用启发式估算 + provider 使用量锚点。可以集成 tiktoken/cl100k 等 tokenizer 进行精确预估，在流式传输过程中实时更新 token 计数。

**B. 图片处理优化**

当前图片处理流程：附件存储 → 请求版本准备 → 文件 API 上传/内联 base64 → 卸载。可以：图片预处理（缩放、压缩）在附件存储侧完成；文件 API 上传的并发控制；增量上传（只上传变更的图片）。

**C. 连接复用**

DeepSeek 适配器每次请求都发起新的 fetch。可以使用 HTTP/2 连接池，优化 SSE 连接的 keep-alive。

### 9.4 开发体验

**A. 调试工具**

- 流式 chunk 的可视化追踪
- 请求/响应的结构化日志
- 适配器行为的 replay 测试框架

**B. 类型安全增强**

- `ContentBlockMap` 的声明合并验证
- Provider 配置的编译时验证
- 流式 chunk 类型的编译时穷尽检查

**C. 文档**

- 每个适配器的 wire format 对照表
- 错误码的完整参考
- 自定义适配器的教程

---

## 总结

DeepSeek Harness 模型接入层的核心优势在于：

1. **Provider-neutral 的统一抽象** — 所有 provider 共享相同的请求/响应/错误模型
2. **声明合并的可扩展类型系统** — ContentBlockMap、FinishReasonMap 等通过 TypeScript 声明合并扩展
3. **原子性的热更新注册机制** — 配置变更可在不中断服务的情况下生效
4. **多层防御性的错误处理** — 从适配器边界到 SDK 客户端，每层都有独立的错误规范化
5. **确定性的流式处理** — AsyncGenerator 背压 + 空闲看门狗 + 消费者中断的三层保护

这些设计使得系统能够以最小的代码变动支持新的模型 provider，同时保持生产级别的可靠性。
