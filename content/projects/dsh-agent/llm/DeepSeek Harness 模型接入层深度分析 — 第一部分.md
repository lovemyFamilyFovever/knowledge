---
title: "DeepSeek Harness 模型接入层深度分析 — 第一部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 模型接入层"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 模型接入层深度分析 — 第一部分
目录导航
第一部分
第二部分
第三部分
↑
DeepSeek Harness 模型接入层深度分析
第一部分：核心架构、模型类型与流式处理  |  分析日期：2026-08-29
1. LLM 抽象层设计
1.1 统一接口设计
DeepSeek Harness 的 LLM 抽象层采用了精心设计的
适配器模式 + Waterfall 拦截链
架构，核心定义在
packages/llm/llm/src/index.ts
中。
HarnessError (error.ts)
  └── LlmError (index.ts)

Service (cordis)
  └── LlmRuntime (index.ts) — 注册表 + 流式调用 API

LlmAdapter (index.ts) — 抽象基类
  ├── DeepSeekAdapter (llm-deepseek/adapter.ts) — 直连 DeepSeek API
  └── PiAiAdapter (llm-pi-ai/adapter.ts) — 通过 pi-ai 库多 Provider
LlmRuntime
是整个 LLM 子系统的服务入口，继承自 Cordis 的
Service
，注册为
ctx.llm
。它承担三个核心职责：
职责一：适配器注册表
—
registerAdapter(providers, adapter)
将一个
LlmAdapter
实例绑定到一组 provider 路由上。注册是全有或全无的（all-or-nothing），任何路由冲突都会导致整个注册失败，错误码为
DUPLICATE_ADAPTER
。返回的
AdapterRegistrationHandle
既是一个同步释放器，又携带
replace(providers)
方法，支持原子性的路由替换——这使得配置变更时可以在不中断服务的情况下热更新路由集合。
职责二：可配置 Provider 目录
—
registerConfigurableProviders(entries)
管理一个"目录"，记录哪些 provider 路由可以通过配置激活。配置界面通过合并
listConfigurableProviders()
和
listProviders()
来展示所有可配置 provider 及其当前活跃/休眠状态。
职责三：流式模型调用 API
—
stream(options)
和
prepareCall(config)
是核心调用入口。
stream
方法通过 Cordis 的
waterfall
机制将实际的适配器流包装在
llm/stream
事件中，允许中间件拦截或修改请求。
统一请求模型 GenerateOptions
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
统一响应模型 StreamChunk
type StreamChunk =
  | { type: 'block-start'; index: number; blockType: ContentBlockType }
  | { type: 'text-delta'; index: number; text: string }
  | { type: 'reasoning-delta'; index: number; text: string }
  | { type: 'tool-call-delta'; index: number; id: CallId; name?: string; argumentsDelta: string }
  | { type: 'block-end'; index: number; block: ContentBlock }
  | { type: 'usage'; usage: TokenUsage }
  | { type: 'finish'; reason: FinishReason; replayState?: ReplayEnvelope }
这个设计的精妙之处在于：
Block 索引机制
— 多个内容块通过
index
交织，支持并行的文本、推理和工具调用流
Delta + Block-end 双重语义
— 增量推送的同时，
block-end
携带最终组装的完整块
Finish 原因的可扩展性
—
FinishReasonMap
通过声明合并扩展
Replay 状态分离
—
ReplayEnvelope
将响应级和块级的适配器私有状态分离
1.2 模型 Provider 的注册机制
注册机制遵循几个关键原则：
原子性与一致性
：
prepareRoutes
方法在提交前验证整个候选路由集，冲突检测在写入前完成。
commitRoutes
方法在一个同步区间内完成旧路由的删除和新路由的写入，确保没有观察者能看到中间状态。
生命周期管理
：注册通过
ctx.effect()
绑定到 Cordis fiber 的生命周期，fiber 释放时自动注销。
replace
方法在同一 fiber 上原子替换路由，避免了 dispose-then-register 间隙中出现的路由真空。
拓扑通知
：
emitAdaptersUpdated()
发布
llm/adapters-updated
事件。关键设计：通知失败是隔离的——单个监听器的异常不会阻断后续监听器，也不会回滚注册变更。
1.3 请求/响应类型定义
内容块类型系统
采用声明合并的
ContentBlockMap
：
类型
结构体
说明
'text'
TextBlock
可见文本
'reasoning'
ReasoningBlock
推理/思考内容
'image'
ImageBlock
图片引用（持久化附件）
'tool-call'
ToolCallBlock
工具调用请求
'tool-result'
ToolResultBlock
工具调用结果
消息系统
（
message.ts
）定义了统一的消息模型，每条消息都有
id: MessageId
（稳定跨边界标识）、
role
、
content: ContentBlock[]
和
source: MessageSource
（生产者归因，支持
user
、
plugin
、
model
、
tool
四种来源）。消息创建后立即深冻结，确保不可变性。
Token 使用量
采用不相交计数：
inputTokens
仅计未缓存输入，缓存读写分别报告为
cacheReadTokens
和
cacheWriteTokens
。
2. 支持的模型类型
2.1 已支持的模型 Provider
A
llm-deepseek — DeepSeek 官方适配器
注册路由：
deepseek-official
模型 ID
名称
Context Window
输入模态
特殊能力
deepseek-v4-flash
DeepSeek-V4-Flash
1,000,000
text
—
deepseek-v4-pro
DeepSeek-V4-Pro
1,000,000
text
—
deepseek-v4-flash-vision-exp
DeepSeek-V4-Flash-Vision-Exp
1,000,000
text + image
图像像素预算 640K
推理努力级别：
off
、
low
、
high
、
max
（默认
high
）
B
llm-pi-ai — 通用 pi-ai 适配器
通过
@earendil-works/pi-ai
库支持多个 provider：
Provider 路由
说明
认证方式
openai
OpenAI 官方
OPENAI_API_KEY
anthropic
Anthropic 官方
ANTHROPIC_API_KEY
任意自定义路由
如
acme-gateway
自定义
apiKeyEnv
2.2 每个 Provider 的配置方式
DeepSeek 配置
支持
apiKeyEnv
（凭据引用）、
baseURL
（端点）、
thinking
（思维模式）、
reasoningEffort
（默认推理努力）、
maxTokens
、
models
（自定义模型目录）、
retryPolicy
（重试策略）等。
Pi-AI 配置
通过
providers
字典配置多个 provider，每个支持
apiKeyEnv
、
api
（协议）、
baseURL
、
compat
（兼容性设置）、
models
、
reasoningEfforts
等。
2.3 模型能力声明
能力元数据通过
LlmResolvedModelInfo
承载：
字段
类型
说明
context
LlmModelContext
上下文窗口大小（tokens）
defaultMaxTokens
number
适配器配置的默认输出上限
reasoning
LlmModelReasoningInfo
推理能力（努力级别列表 + 默认值）
inputModalities
ModelModality[]
输入模态（text / image）
3. 流式响应处理
3.1 Streaming 的实现方式
DeepSeek 适配器的流式管道
HTTP fetch (POST /chat/completions, stream: true)
  → response.body (ReadableStream<BufferSource>)
    → parseSse() — SSE 帧解析 (eventsource-parser)
      → translate() — Wire chunks → StreamChunk 协议
        → LlmRuntime.adapterStream() — 错误规范化
          → ctx.waterfall('llm/stream') — 中间件拦截
            → 消费者
Pi-AI 适配器的流式管道
pi-ai Models.streamSimple() → AssistantMessageEvent 流
  → toStreamChunks() — 事件翻译
    → LlmRuntime.adapterStream()
      → ctx.waterfall('llm/stream')
        → 消费者
3.2 事件流的处理管道
Waterfall 拦截机制
：
LlmRuntime.streamWithRegistration
通过
ctx.waterfall
将适配器流包装。Waterfall 监听器可以调用
next()
到达底层适配器流、yield 自己的 chunks 来短路、或修改 options 后再调用 next。
不变量验证
（
llm/invariant.ts
）：安装在 waterfall 的最前面（
prepend: true
），对每个 chunk 进行语法验证：块索引必须是非负安全整数；delta 必须指向已打开的匹配类型块；
usage
只能出现一次；
finish
之后不能再有 chunk。
错误规范化
（
adapter-failure.ts
）：
adapterStream
方法将适配器抛出的异常捕获并转换为终端
error
或
aborted
finish chunk。
normalizeLlmFailure
处理各种异常来源，包括 HarnessError、SDK 错误的安全读取、非 Error 值的安全字符串化。
3.3 背压控制
AsyncGenerator 背压
：JavaScript 的 AsyncGenerator 协议天然提供背压——当消费者不调用
next()
时，生产者的
yield
会暂停
空闲看门狗
：DeepSeek 和 Pi-AI 适配器都使用
idleWatchdog
监控流的空闲状态，超时映射为
TIMEOUT
错误码
消费者中断
：两个适配器都使用
AbortController
管理消费者生命周期
图片背压
：确定性的卸载策略——当请求图片超过字节或数量限制时，最旧的图片被替换为文本占位符
← 上一部分
下一部分 →
DeepSeek Harness 模型接入层深度分析 · 第一部分 · 生成于 2026-08-29