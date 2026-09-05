---
title: "DeepSeek Harness (DSH) API 参考手册"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / API参考手册"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness (DSH) API 参考手册
快速导航
快速入门
创建 Agent
流式调用 LLM
读写文件
架构概念
1. dsh-core
AgentRegistry
Agent 接口
Session 类
2. dsh-llm
LlmRuntime
核心类型
3. dsh-fs
4. dsh-terminal
5. dsh-skill
6. dsh-goal
8. dsh-schedule
9. 事件系统
10. 作用域
11. 错误码
12. 配置
⇧
DeepSeek Harness (DSH) API 参考手册
TypeScript Monorepo 架构 | 包命名空间:
@deepseek-ai/dsh-*
| 基于 Cordis 服务框架
目录
快速入门指南
环境准备
1. 创建最小 Agent
2. 发送消息并等待响应
3. 流式调用 LLM
4. 读写文件
5. 监听事件
6. 注册自定义技能
7. 管理目标
8. 使用终端
9. 创建定时提醒
架构概念速览
第一部分：核心 API
1. @deepseek-ai/dsh-core API
1.1 AgentRegistry 服务
1.2 Agent 接口
1.3 Session 类
1.4 SessionStore 服务
2. @deepseek-ai/dsh-llm API
2.1 LlmRuntime 服务
2.2 LlmAdapter 抽象类
2.3 核心类型
2.4 LlmError
2.5 工具函数
3. @deepseek-ai/dsh-fs API
3.1 FileSystem 抽象类
3.2 核心类型
3.3 事件
第二部分：功能模块 API
4. @deepseek-ai/dsh-terminal API
4.1 TerminalSessionService
4.2 类型定义
5. @deepseek-ai/dsh-skill API
5.1 SkillRegistry
5.2 核心类型
5.3 事件
5.4 工具函数
6. @deepseek-ai/dsh-goal API
6.1 GoalService
6.2 核心类型
7. @deepseek-ai/dsh-plan API
8. @deepseek-ai/dsh-schedule API
8.1 ScheduleRecord 类型
8.2 ScheduleView
8.3 变更类型
8.4 错误类型
第三部分：扩展与集成
9. 事件系统 API
9.1 Agent 生命周期事件
9.2 Session 事件
9.3 LLM 事件
9.4 其他事件
10. 作用域系统 API
11. 错误码和异常类型
11.1 LLM 错误
11.2 文件系统错误
11.3 终端错误
11.4 目标错误
11.5 会话分叉错误
12. 配置文件格式
12.1 cordis.yml 配置
12.2 AgentOptions 配置
12.3 环境变量
12.4 设置文件
快速入门指南
本指南帮助您快速上手 DeepSeek Harness 的核心 API，从创建第一个 Agent 到实现完整的对话循环。
环境准备
# 克隆仓库
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness

# 安装依赖
pnpm install

# 启动 Web UI
pnpm dsh web
1. 创建最小 Agent
以下示例展示如何通过 Cordis 上下文创建一个最基本的 Agent：
import { Context } from '@deepseek-ai/cordis'
import { SessionId } from '@deepseek-ai/dsh-session'

// 假设 ctx 已通过 Cordis 应用启动获得
async function createMinimalAgent(ctx: Context) {
  // 创建 Agent（需要 dsh-agent-loop 插件已加载）
  const handle = await ctx.agents.create({
    sessionId: SessionId('my-first-session'),
    agentOptions: {
      provider: 'deepseek',
      model: 'deepseek-chat',
    },
  })

  console.log(`Agent created: ${handle.agent.id}`)
  console.log(`Status: ${handle.agent.status}`)  // 'idle'

  // 使用完毕后释放
  await handle.dispose()
}
2. 发送消息并等待响应
async function sendMessage(agent: Agent, text: string) {
  // 构造 UserMessage
  const message: UserMessage = {
    id: `msg-${Date.now()}`,
    role: 'user',
    source: { kind: 'user' },
    content: [{ type: 'text', text }],
  }

  // 发送到 next-turn inbox 并唤醒驱动器
  agent.followup(message)

  // 等待 Agent 完成响应
  await agent.whenIdle()

  // 读取最新的派生消息历史
  const history = agent.session.deriveMessages()
  const lastAssistant = history.filter(m => m.role === 'assistant').at(-1)
  return lastAssistant?.content
}
3. 流式调用 LLM
直接使用 LLM 服务进行一次性流式调用：
import { type GenerateOptions, type StreamChunk } from '@deepseek-ai/dsh-llm'

async function streamChat(ctx: Context, prompt: string) {
  const options: GenerateOptions = {
    provider: 'deepseek',
    model: 'deepseek-chat',
    messages: [{
      id: 'user-1',
      role: 'user',
      source: { kind: 'user' },
      content: [{ type: 'text', text: prompt }],
    }],
    system: 'You are a helpful assistant.',
  }

  const stream: AsyncIterable<StreamChunk> = ctx.llm.stream(options)

  for await (const chunk of stream) {
    switch (chunk.type) {
      case 'text-delta':
        process.stdout.write(chunk.text)
        break
      case 'reasoning-delta':
        // 思考过程
        break
      case 'finish':
        console.log('\n---')
        console.log('Finish reason:', chunk.reason.kind)
        break
    }
  }
}
4. 读写文件
import { type FsTarget } from '@deepseek-ai/dsh-fs'

async function fileOperations(ctx: Context, workspace: string) {
  // 解析路径
  const target = await ctx.fs.resolve('hello.txt', { cwd: workspace })
  console.log('Display path:', target.displayPath)

  // 写入文件
  const writeResult = await ctx.fs.writeText(target, 'Hello, DSH!')
  console.log('Operation:', writeResult.operation)  // 'create' 或 'update'

  // 读取文件
  const content = await ctx.fs.readText(target)
  console.log('Content:', content)

  // 编辑文件（字面替换）
  const editResult = await ctx.fs.editText(target, {
    oldString: 'Hello',
    newString: 'Hi',
    replaceAll: false,
  })
  console.log('Before:', editResult.before)
  console.log('After:', editResult.after)
}
5. 监听事件
// 监听 Agent 状态变更
ctx.on('agent/status', ({ agent, status }) => {
  console.log(`Agent ${agent.id} is now ${status}`)
})

// 监听会话事件（持久化插件用）
ctx.on('session/event', (session, event) => {
  if (event.type === 'user/message') {
    console.log('User said:', event.data.content[0])
  }
})

// 拦截 LLM 请求（修改配置）
ctx.on('llm/stream', async (options, next) => {
  console.log(`Calling ${options.provider}/${options.model}`)
  return next()  // 继续到适配器
})
6. 注册自定义技能
// 注册运行时技能
ctx.skills.register({
  name: 'my-helper',
  description: 'A helpful custom skill',
  whenToUse: 'When the user asks for custom help',
  content: `# My Helper Skill

This skill helps with custom tasks.

## Steps
1. Analyze the request
2. Provide a solution`,
  invocation: { modelInvocable: true, userInvocable: true },
})
7. 管理目标
// 创建目标
const goal = ctx.goals.create(agent, {
  objective: 'Refactor the authentication module',
  maxGoalRounds: 100,
})
console.log('Goal:', goal.objective)
console.log('Phase:', goal.phase)  // 'active'

// 暂停目标
const paused = ctx.goals.pause(agent, {
  id: goal.id,
  revision: goal.revision,
})

// 恢复目标
const resumed = ctx.goals.resume(agent, {
  id: paused.id,
  revision: paused.revision,
})
8. 使用终端
// 创建 PTY 会话
const termResult = await ctx.terminals.spawn(agent, {
  type: 'bash',
  name: 'my-shell',
  cwd: '/workspace',
})
console.log('Terminal ID:', termResult.sessionId)
console.log('MOTD:', termResult.motd)

// 发送命令
const sendOp = ctx.terminals.startSend(agent, termResult.sessionId, {
  text: 'ls -la',
  submit: true,
})
const result = await sendOp.done
console.log('Output:', result.viewport)
9. 创建定时提醒
// 通过 session 事件创建（schedule 工具内部使用）
agent.session.append('schedule/change', {
  version: 1,
  operation: 'create',
  schedule: {
    id: ScheduleId('reminder-1'),
    kind: 'at',
    prompt: 'Check deployment status',
    scheduledAt: '2026-08-29T15:00:00Z',
  },
})
架构概念速览
概念
说明
Cordis
依赖注入框架。所有服务通过
ctx.xxx
访问。
Service
注册到 Context 上的单例。生命周期由 Cordis 管理。
Scope
带标签的上下文，实现 Agent 级别的注册隔离。
Session
事件溯源日志。所有对话数据作为不可变事件存储。
Agent
驱动 Session 的运行时实体，管理 inbox 和驱动循环。
Waterfall
链式拦截器模式，
next()
传递到下一个监听器。
Emit
火并遗忘通知模式，观察者失败不影响主流程。
第一部分：核心 API
1. @deepseek-ai/dsh-core API
dsh-core 是 DeepSeek Harness 的核心层，由多个子包组成：
dsh-agent
（Agent 生命周期）、
dsh-session
（会话管理）、
dsh-scope
（作用域系统）。所有服务通过 Cordis 依赖注入框架暴露在
Context
上。
1.1 AgentRegistry 服务
ctx.agents
class
AgentRegistry extends Service
Agent 注册中心，管理所有活跃 Agent 的生命周期，提供 Agent 创建/恢复工厂委托，以及进程级发起者作用域追踪。
构造函数
constructor(ctx: Context)
通过 Cordis 服务机制自动注入，注册为
ctx.agents
。同时注册
ctx.agent
访问器（默认
undefined
），并在 Agent 的作用域上下文中设置为当前 Agent 实例。
方法
create(options: CreateAgentOptions): Promise<AgentHandle>
通过注册的工厂创建新 Agent。工厂由
dsh-agent-loop
插件实现。创建过程包括：验证 sessionId、构建会话、执行 setup 钩子、发布 Agent 和 Session、启动 Agent 循环。
resume(options: ResumeAgentOptions): Promise<AgentHandle>
加载持久化会话并恢复 Agent。需要
sessionPersistence
服务已存在。
register(agent: Agent): () => void
注册一个已构建的 Agent。返回 Cordis 效果释放器。触发
agent/created
事件，释放时触发
agent/disposed
。
get(id: SessionId): Agent | undefined
按 ID 查找活跃 Agent。
list(): Agent[]
返回所有活跃 Agent 数组（按注册顺序）。
roots(): Agent[]
返回所有顶层 Agent（无拥有者的 Agent）。
withInitiator<T>(agent: Agent, operation: () => T): T
在指定 Agent 作为进程级发起者的上下文中运行操作。用于因果归因（日志、追踪、指标）。
withoutInitiator<T>(operation: () => T): T
在清除发起者归属的边界中运行操作。用于共享定时器、队列泵等不应继承 Agent 归属的场景。
currentInitiator(): Agent | undefined
读取当前继承的发起者 Agent（可选形式，用于日志/追踪）。
requireInitiator(): Agent
读取发起者 Agent，无活跃发起者时抛出异常。
接口定义
CreateAgentOptions
字段
类型
必填
说明
sessionId
SessionId
必填
Agent/Session 共享身份标识
meta
object
可选
会话创建元数据（cwd、parentSession、seedLength、origin、delegationDepth、agentPreset）
seed
readonly SessionEvent[]
可选
初始回放/分叉历史事件
agentOptions
AgentOptions
可选
Agent 级选项（provider、model、maxTokens）
signal
AbortSignal
可选
创建时取消信号
setup
AgentSetup
可选
创建时的组合回调，在 Agent 发布前执行
AgentHandle
字段
类型
说明
agent
Agent
创建的 Agent 实例
dispose()
Promise<void>
停止循环、注销 Agent、移除会话、释放作用域
1.2 Agent 接口
interface
Agent
活跃 Agent 的公共句柄，提供生命周期控制和消息路由。
属性
类型
说明
id
SessionId
与 session 共享的唯一标识
options
AgentOptions
当前 provider/model 配置
session
Session
该 Agent 驱动的活跃会话
inbox
Inbox
持久待处理工作的投影
status
AgentStatus
'idle' | 'running'
当前生命周期状态
ctx
Context
Agent 作用域上下文
Agent 方法
cancel(cause: AgentCancelCause, options?: CancelOptions): void
取消当前活跃的轮次或轮次间任务。第一个原因对该活动生效。
options.keepInbox
为 true 时保留排队的 inbox 消息。
whenIdle(): Promise<void>
等待当前整个 Agent 活动达到静止状态。
runMaintenance<T>(task: (signal: AbortSignal) => Promise<T>): Promise<T>
在真正空闲阶段运行一个非轮次维护任务。任务开始后，后续唤醒输入保留在 inbox 中。
send(message: UserMessage, target: InboxTarget, wakeup: boolean): void
将标识输入路由到 inbox 边界并可选唤醒驱动器。
target
为
'next-turn'
或
'next-step'
。
followup(message: UserMessage): void
排队一个普通后续轮次并唤醒驱动器。
steer(message: UserMessage): void
为最近的步骤提交引导消息。空闲驱动器开始一个轮次；运行中的驱动器在下一步边界消费它。
inject(message: UserMessage): void
排队模型可见的上下文消息，不唤醒驱动器。运行中的驱动器在最近的步骤边界消费。
AgentOptions
interface AgentOptions {
  provider?: string    // Provider 路由
  model?: string       // 模型 ID
  maxTokens?: number   // 每次请求最大输出 token
}
AgentCancelCause
type AgentCancelCause =
  | { kind: 'user' }
  | { kind: 'parent' }
  | { kind: 'hook'; reason: string }
  | { kind: 'disposed' }
1.3 Session 类
class
Session
事件溯源会话：一个仅追加的
SessionEvent
日志。通过
ctx.sessions.create()
创建活跃实例，或通过
Session.create()
创建分离实例。
静态方法
Session.create(id: SessionId, seed?: readonly SessionEvent[], header?: SessionHeader): Session
创建分离会话，验证并快照借用的种子事件和存储元数据。
Session.fromRestore(id: SessionId, seed: readonly SessionEvent[], header: SessionHeader): Session
通过接管新鲜的持久化值恢复分离会话。验证存储格式、事件信封、序列连续性。
实例属性
属性
类型
说明
id
SessionId
会话标识（派生自 header）
header
SessionHeader
分离的、深度冻结的创建元数据
events
readonly SessionEvent[]
事件日志的不可变快照
seq
number
下一个事件的序列号（日志长度）
firstLiveSeq
number
本进程中追加的第一个事件的 seq
surface
SessionSurface
有序表面（消息产生的事件序列）
实例方法
append<T extends SessionEventType>(type: T, data: SessionEventMap[T], ...opts): SessionEvent<T>
追加一个类型化事件到日志。数据必须是无损 JSON 可序列化的。表面事件类型（
user/message
、
assistant/message
、
tool/result
）必须提供
SurfaceIntent
。返回已记录的事件（分配的
seq
/
time
加数据快照）。
deriveMessages(): Message[]
通过遍历
surfaceOp
标记维护的有序序列来推导 LLM 消息历史。缓存：每个表面节点仅投影一次。返回共享的、深度冻结的
Message
数组的新快照。
requestHeader(): EpochHeader | undefined
返回日志中最后一个 header 事件后生效的
EpochHeader
。增量维护。
requestContext(): RequestContext | undefined
返回最新的路由元数据。
SessionHeader
interface SessionHeader {
  readonly version: number           // 磁盘格式版本 (当前 0)
  readonly id: SessionId
  readonly createdAt: number         // Unix 毫秒
  readonly cwd?: string              // 绝对工作目录
  readonly parentSession?: SessionId // 分叉来源
  readonly seedLength?: number       // 继承的前缀长度
  readonly origin?: 'subagent'       // 子 Agent 分类
  readonly delegationDepth?: number  // 递归预算
  readonly agentPreset?: string      // Agent 预设 ID
}
SessionEvent
类型联合
interface SessionEventMap {
  'turn/start':    { turn: number }
  'turn/end':      { turn: number; reason: TurnEndReason }
  'step/start':    { turn: number; step: number }
  'step/end':      { turn: number; step: number }
  'user/message':  UserMessage
  'assistant/chunk': { turn: number; step: number; chunk: StreamChunk }
  'assistant/message': { turn: number; step: number; message: AssistantMessage; usage?: TokenUsage; interrupted?: true }
  'tool/call':     { turn: number; step: number; callId: CallId; name: string; arguments: string }
  'tool/result':   { turn: number; step: number; message: ToolResultMessage; error?: ...; meta?: JsonValue }
  'todo/write':    { todos: TodoItem[] }
  'request/header': { header: EpochHeader; reason: RequestHeaderReason }
  'request/context': RequestContext
  'session/end-seed': Record<string, never>
}
1.4 SessionStore 服务
ctx.sessions
class
SessionStore extends Service
内存会话存储。持久化由插件负责（订阅
session/event
，在
session/flush
时刷新）。
方法
create(id?: SessionId, options?: CreateSessionOptions): Session
创建并发布会话。省略 id 时自动计数生成。返回已进入存储并公布的活跃会话。
prepare(id?: SessionId, options?: PrepareSessionOptions): Session
构建会话但不进入存储。配对
enter()
+
announce()
用于复合效果。
enter(session: Session): () => void
将准备好的会话插入存储，安装发布钩子。返回分离释放器。
announce(session: Session): void
公布已进入的会话，触发
session/created
事件。
fork(source: Session | SessionId, boundary?: number, childSessionId?: SessionId): Session
从活跃源创建子会话。
boundary
为包含的源事件 seq。
get(id: SessionId): Session | undefined
查找活跃会话。
list(): Session[]
返回所有活跃会话。
flush(session: Session): Promise<boolean>
分发
session/flush
持久性检查点。
2. @deepseek-ai/dsh-llm API
LLM 服务层：适配器注册中心 + 可拦截的流式模型调用 API。通过
ctx.llm
暴露。
2.1 LlmRuntime 服务
ctx.llm
class
LlmRuntime extends Service
方法
registerAdapter(providers: string[], adapter: LlmAdapter): AdapterRegistrationHandle
注册适配器到指定的 provider 路由。返回释放器 + 原子路由替换。抛出
LlmError
（
DUPLICATE_ADAPTER
）当 provider 已有适配器。
stream(options: GenerateOptions): AsyncIterable<StreamChunk>
流式调用模型。通过
llm/stream
waterfall 拦截。适配器选择、分发和迭代失败转为终端
error
或
aborted
finish 块。
prepareCall(config: LlmCallConfig, signal?: AbortSignal): Promise<PreparedLlmCall>
在当前适配器注册下解析一次调用。返回的句柄保持注册跨 header 日志和分发。
listProviders(): LlmProviderInfo[]
列出已注册适配器的 provider 路由。
listModels(provider: string): Promise<LlmModelInfo[]>
发现 provider 广告的模型。
resolveModelInfo(provider: string, model: string, signal?: AbortSignal): Promise<LlmResolvedModelInfo>
解析精确模型的全部元数据。
resolveCallConfig(config: LlmCallConfig, signal?: AbortSignal): Promise<LlmCallConfig>
验证对话调用配置并物化适配器默认值。
providerRetryPolicy(provider: string): ResolvedRetryPolicy
获取 provider 注册时捕获的重试策略。
registerConfigurableProviders(entries: readonly LlmConfigurableProvider[]): DirectoryRegistrationHandle
声明可通过配置激活的 provider 路由目录。
listConfigurableProviders(): LlmConfigurableProvider[]
列出所有声明的可配置 provider。
registerModelDiscovery(settingsNs: string, discover: (request: LlmModelDiscoveryRequest) => Promise<readonly LlmDiscoveredModel[]>): () => void
注册模型发现回调。
discoverModels(settingsNs: string, request: LlmModelDiscoveryRequest): Promise<LlmDiscoveredModel[]>
查询 provider 端点的模型列表。
2.2 LlmAdapter 抽象类
abstract class
LlmAdapter
Provider 线协议适配器。通过
ctx.llm.registerAdapter()
注册。
方法
返回类型
说明
providerInfo(provider)
LlmProviderInfo
描述 provider 路由的显示元数据
providerRetryPolicy(provider)
ResolvedRetryPolicy | undefined
Provider 拥有的重试策略
listModels(provider)
Promise<readonly LlmModelInfo[]>
列出可发现的模型
resolveModel(provider, model, signal?)
Promise<LlmResolvedModelInfo>
解析精确模型的全部元数据
prepareCall(provider, model, signal?)
Promise<PreparedAdapterCall>
绑定模型元数据到流分发
stream(options)
abstract
AsyncIterable<StreamChunk>
流式调用模型（唯一必需方法）
2.3 核心类型
GenerateOptions
— 完整的模型请求
interface GenerateOptions {
  provider: string                    // 注册的 provider 路由
  model: string                       // 模型 ID
  reasoningEffort?: ReasoningEffortId // 推理努力级别
  messages: Message[]                 // 对话消息（模型可见）
  system?: string                     // 系统提示文本
  tools?: ToolSchema[]                // 工具 JSON Schema
  temperature?: number
  maxTokens?: number
  stop?: string[]                     // 停止序列
  signal?: AbortSignal
  sessionId?: SessionId               // 请求路由用
  purpose?: 'compaction' | 'session-title'  // 辅助用途分类
}
LlmCallConfig
— 对话调用配置
interface LlmCallConfig {
  provider: string
  model: string
  reasoningEffort?: ReasoningEffortId
  temperature?: number
  maxTokens?: number
  stop?: string[]
}
StreamChunk
— 流式协议块
type StreamChunk =
  | { type: 'block-start';  index: number; blockType: ContentBlockType }
  | { type: 'text-delta';   index: number; text: string }
  | { type: 'reasoning-delta'; index: number; text: string }
  | { type: 'tool-call-delta'; index: number; id: CallId; name?: string; argumentsDelta: string }
  | { type: 'block-end';    index: number; block: ContentBlock }
  | { type: 'usage';        usage: TokenUsage }
  | { type: 'finish';       reason: FinishReason; replayState?: ReplayEnvelope }
ContentBlock
— 内容块类型
type ContentBlock =
  | { type: 'text';        text: string }
  | { type: 'reasoning';   text: string }
  | { type: 'image';       attachment: ImageAttachmentRef }
  | { type: 'tool-call';   id: CallId; name: string; arguments: string }
  | { type: 'tool-result'; toolCallId: CallId; content: ContentBlock[]; isError?: boolean }
TokenUsage
interface TokenUsage {
  inputTokens: number       // 未缓存输入
  outputTokens: number
  cacheReadTokens?: number  // 缓存读取
  cacheWriteTokens?: number // 缓存写入
  reasoningTokens?: number
}
LlmFailure
— 序列化失败事实
interface LlmFailure {
  readonly message: string
  readonly code: string                 // 稳定的机器路由码
  readonly status?: number              // HTTP 状态码
  readonly providerRetryAfterMs?: number
  readonly requestId?: ProviderRequestId
}
ToolSchema
interface ToolSchema {
  name: string
  description: string
  parameters: Record<string, unknown>  // JSON Schema
}
2.4 LlmError
class
LlmError extends HarnessError
LLM 相关失败的类型化错误。携带
LlmFailure
可序列化事实。
class LlmError extends HarnessError {
  readonly failure: LlmFailure
  constructor(message: string, code: string, options?: LlmErrorOptions)
}

interface LlmErrorOptions extends ErrorOptions {
  status?: number
  providerRetryAfterMs?: number
  requestId?: ProviderRequestId
}
2.5 工具函数
deepFreeze<T>(value: T): T
迭代式深度冻结，跳过 AbortSignal。用于请求数据不可变性保证。
callConfigEquals(a: LlmCallConfig, b: LlmCallConfig): boolean
字段级相等比较，包括 stop 列表的逐元素比较。
contentHasImage(content: readonly ContentBlock[]): boolean
递归检查内容是否包含图像块。
3. @deepseek-ai/dsh-fs API
文件系统抽象层。后端拥有稳定的 target 身份、路径处理、文本读写和原子变更。通过
ctx.fs
暴露。
3.1 FileSystem 抽象类
ctx.fs
abstract class
FileSystem extends Service
属性
get sandboxMode(): SandboxMode | undefined
此后端默认执行的沙箱模式。基类返回
undefined
；沙箱后端覆盖为部署默认值。
抽象方法
resolve(path: string, opts?: { cwd?: string; signal?: AbortSignal }): Promise<FsTarget>
将模型/插件提供的路径解析为稳定的
FsTarget
。相对路径根据
opts.cwd
解析。
processPath(target: FsTarget): string
返回子进程可打开的规范绝对路径。
fileUrl(target: FsTarget): string
返回目标的规范
file:
URI。
contains(parent: FsTarget, child: FsTarget): boolean
测试规范包含关系（不暴露后端 target key）。
stat(target: FsTarget, signal?: AbortSignal): Promise<FsInfo | undefined>
返回目标元数据，不存在时返回
undefined
。
lstat(path: string, opts?: { cwd?: string }, signal?: AbortSignal): Promise<FsPathInfo | undefined>
返回路径元数据（不跟随最终符号链接）。
readText(target: FsTarget, signal?: AbortSignal): Promise<string>
读取整个 UTF-8 文本文件。
streamText(target: FsTarget, signal?: AbortSignal): Promise<AsyncIterable<string>>
流式读取文本文件（大文件用）。
readBytes(target: FsTarget, signal: AbortSignal | undefined, maxBytes: number): Promise<Uint8Array>
读取原始字节（无解码/二进制拒绝）。
listDir(target: FsTarget, signal?: AbortSignal): Promise<FsDirEntry[]>
按稳定名称顺序列出直接子项。
writeText(target: FsTarget, content: string, expected?: FsWriteIntent, signal?: AbortSignal, sandboxPolicy?: SandboxExecutionPolicy): Promise<FsWriteOutcome>
原子创建或替换 UTF-8 文本。
expected
守护写入意图和过期检查。
editText(target: FsTarget, edit: FsEditRequest, expected?: { version: FsVersion }, signal?: AbortSignal, sandboxPolicy?: SandboxExecutionPolicy): Promise<FsEditOutcome>
原子编辑字面文本。版本守护在匹配前检查。
3.2 核心类型
FsTarget
interface FsTarget {
  targetKey: FsTargetKey   // 不透明的稳定标识（不可解析为路径）
  displayPath: string       // 模型/UI 面输出路径
}
FsInfo
/
FsPathInfo
interface FsInfo {
  version: FsVersion
  type: 'file' | 'directory' | 'other'
  size?: number
}

interface FsPathInfo {
  version: FsVersion
  type: 'file' | 'directory' | 'symlink' | 'other'
  size?: number
}
FsWriteIntent
type FsWriteIntent =
  | { kind: 'createIfAbsent' }                    // 目标必须不存在
  | { kind: 'replaceIfVersion'; version: FsVersion }  // 版本匹配才能替换
FsWriteOutcome
/
FsEditOutcome
interface FsWriteOutcome {
  operation: 'create' | 'update'
  version: FsVersion
  before: string | null   // 写入前内容（LF 规范化）
  after: string           // 写入后内容
}

interface FsEditOutcome {
  version: FsVersion
  before: string
  after: string
}
FsEditRequest
interface FsEditRequest {
  oldString: string    // 要替换的字面非空文本
  newString: string    // 替换文本（空字符串删除）
  replaceAll: boolean  // 是否替换所有匹配
}
FsErrorCode
type FsErrorCode =
  | 'FS_NOT_FOUND' | 'FS_NOT_DIRECTORY' | 'FS_NOT_TEXT'
  | 'FS_NOT_REGULAR_FILE' | 'FS_TOO_LARGE' | 'FS_PERMISSION_DENIED'
  | 'FS_SANDBOX_DENIED' | 'FS_IO_ERROR' | 'FS_STALE_VERSION'
  | 'FS_NOT_OBSERVED' | 'FS_AMBIGUOUS_EDIT' | 'FS_EDIT_NOT_FOUND'
  | 'FS_ABORTED'
3.3 事件
事件名
模式
说明
fs/write-intent
waterfall
下一次
writeText
的单槽决策
fs/edit-intent
waterfall
下一次
editText
的单槽决策
fs/observed
emit
记录权威观察（存在/不存在）
第二部分：功能模块 API
4. @deepseek-ai/dsh-terminal API
所有者作用域的持久 PTY 注册中心。后端拥有终端机制，此服务拥有 ID、发布、授权和等待清理。通过
ctx.terminals
暴露。
4.1 TerminalSessionService
ctx.terminals
class
TerminalSessionService extends Service
方法
registerBackend(backend: TerminalBackend): () => void
注册一个 PTY 后端类型。后端
type
必须非空且唯一。
listBackends(): string[]
列出已注册后端类型。
spawn(owner: Agent, request: TerminalSpawnRequest, signal?: AbortSignal): Promise<TerminalSpawnResult>
创建并发布一个所有者作用域的 PTY 会话。返回发布身份、元数据、状态和 MOTD。
startSend(owner: Agent, id: TerminalSessionId, request: TerminalSendRequest): TerminalSendOperation
启动一个独占交互式发送。
TerminalSendOperation.done
在就绪/超时/取消/退出时解析。
read(owner: Agent, id: TerminalSessionId, request?: TerminalReadRequest): TerminalReadResult
读取一个有界回滚页面。
signal(owner: Agent, id: TerminalSessionId, signal: TerminalSignal): Promise<TerminalSignalResult>
向验证的前台进程组发送信号。
kill(owner: Agent, id: TerminalSessionId, reason?: string): Promise<boolean>
关闭一个拥有的会话。返回
true
表示新关闭。
list(owner: Agent): TerminalSessionSnapshot[]
列出指定所有者的会话快照。
4.2 类型定义
TerminalSpawnRequest
interface TerminalSpawnRequest {
  type: string       // 已注册后端类型
  name?: string      // 所有者本地显示名
  cwd?: string       // 初始工作目录
}
TerminalSendRequest
/
TerminalSendResult
interface TerminalSendRequest {
  text: string       // UTF-8 文本
  submit: boolean    // 是否发送 Enter
  signal?: AbortSignal
}

interface TerminalSendResult {
  viewport: string                       // 有界终端输出
  waitReason: TerminalWaitReason         // 'stdin_read' | 'inferred_idle' | 'timeout' | 'session_exit'
  sessionStatus: TerminalSessionStatus
  truncated: boolean
}
TerminalSignal
type TerminalSignal = 'SIGINT' | 'SIGTERM' | 'SIGKILL' | 'SIGTSTP' | 'SIGHUP'
TerminalBackend
接口
interface TerminalBackend {
  readonly type: string
  spawn(spec: TerminalBackendSpawnSpec): Promise<TerminalBackendSession>
}

interface TerminalBackendSession {
  readonly motd: string
  readonly pid?: number
  startSend(request: TerminalSendRequest): TerminalSendOperation
  read(request: TerminalReadRequest): TerminalReadResult
  signal(signal: TerminalSignal): Promise<TerminalSignalResult>
  status(): TerminalSessionStatus
  close(reason: string): Promise<void>
}
TerminalErrorCode
type TerminalErrorCode =
  | 'DUPLICATE_BACKEND' | 'DUPLICATE_NAME' | 'FOREIGN_SESSION'
  | 'NO_BACKEND' | 'NO_SESSION' | 'OWNER_NOT_LIVE'
  | 'SEND_ACTIVE' | 'SERVICE_DISPOSING'
5. @deepseek-ai/dsh-skill API
Agent 技能提供者注册中心。合并提供者目录、解析获胜技能、暴露摘要和定义。通过
ctx.skills
暴露。
5.1 SkillRegistry
ctx.skills
class
SkillRegistry extends Service
方法
registerProvider(create: (control: SkillProviderControl) => SkillProvider): () => void
注册一个借用的同进程提供者。进入调用上下文的层级。远程初始化属于
list()
。
register(skill: SkillRegistration): () => void
注册运行时技能到调用上下文的层级。项目条目优先于运行时条目。
list(options?: SkillViewOptions): Promise<SkillSummary[]>
列出工作区的调用中性技能摘要。
snapshot(options?: SkillViewOptions): Promise<SkillCatalogSnapshot>
观察当前目录及发现完成状态。
get(name: string, options?: SkillViewOptions): Promise<SkillDefinition | undefined>
加载并验证获胜候选的完整技能体。
5.2 核心类型
SkillSummary
interface SkillSummary {
  readonly name: string              // kebab-case 标识
  readonly description: string       // 短路由描述
  readonly whenToUse?: string        // 额外路由指导
  readonly invocation: SkillInvocationPolicy
  readonly source: SkillSource
  readonly provider: string
  readonly resourceBase?: SkillResourceBase
}
SkillDefinition
interface SkillDefinition extends SkillSummary {
  readonly content: string           // Markdown 指令体
  readonly path?: string             // 绝对文件路径
  readonly metadata?: Readonly<Record<string, unknown>>
}
SkillProvider
interface SkillProvider {
  readonly name: string
  readonly list: (options: SkillLookupOptions) => Promise<readonly SkillCandidate[] | SkillProviderObservation>
  readonly get: (candidate: SkillCandidate, options: SkillLookupOptions) => Promise<SkillDefinition | undefined>
}
SkillInvocationPolicy
interface SkillInvocationPolicy {
  readonly modelInvocable: boolean   // 模型是否可调用
  readonly userInvocable: boolean    // 用户命令是否可调用
}
SkillSource
type SkillSource = 'project-dsh' | 'project-agents' | 'runtime'
  | 'user-dsh' | 'user-agents' | 'custom' | 'bundled' | (string & {})
5.3 事件
事件名
模式
说明
skills/change
emit
技能提供者或运行时贡献可能已变更
5.4 工具函数
isSkillName(name: string): boolean
验证 kebab-case 技能名称。
isModelInvocable(skill: Pick<SkillSummary, 'invocation'>): boolean
技能是否允许模型调用。
isUserInvocable(skill: Pick<SkillSummary, 'invocation'>): boolean
技能是否允许用户命令调用。
renderSkillContent(skill: Pick<SkillDefinition, 'name' | 'provider' | 'resourceBase' | 'content'>): string
渲染模型可见的
<skill_content>
块。
6. @deepseek-ai/dsh-goal API
同会话目标域：事件溯源状态、比较并设置变更、进程级继续激活。通过
ctx.goals
暴露。
6.1 GoalService
ctx.goals
class
GoalService extends TypertRemoteService
方法
get(agent: Agent): GoalView | undefined
读取指定活跃 Agent 的当前目标。
create(agent: Agent, request: CreateGoalRequest): GoalView
创建并激活目标。已完成的目标可被替换；其他阶段必须先清除或恢复。
edit(agent: Agent, ref: GoalRef, request: EditGoalRequest): GoalView
编辑目标和/或轮次上限，不改变阶段。
pause(agent: Agent, ref: GoalRef): GoalView
暂停活跃目标并解除自动继续。
resume(agent: Agent, ref: GoalRef): GoalView
恢复并激活已停止的目标。轮次预算耗尽时抛出异常。
complete(agent: Agent, ref: GoalRef): GoalView
标记当前非完成目标为完成。
block(agent: Agent, ref: GoalRef, reason: GoalBlockReason): GoalView
标记活跃目标为阻塞，附带原因。
clear(agent: Agent, ref: GoalRef): GoalRef
清除当前目标，保留持久墓碑和历史。
disarm(agent: Agent): GoalView | undefined
移除进程级继续权限，不改变持久阶段。
6.2 核心类型
GoalSnapshot
interface GoalSnapshot extends GoalRef {
  readonly objective: string
  readonly phase: GoalPhase           // 'active' | 'paused' | 'blocked' | 'complete'
  readonly blockedReason?: GoalBlockReason
  readonly maxGoalRounds: number
}
GoalView
interface GoalView extends GoalSnapshot {
  readonly roundsStarted: number
  readonly createdAt: number
  readonly updatedAt: number
  readonly activation: GoalActivation  // 'armed' | 'disarmed'
}
CreateGoalRequest
interface CreateGoalRequest {
  readonly objective: string
  readonly maxGoalRounds?: number
}
GoalBlockReason
interface GoalBlockReason {
  readonly code: string     // lower-kebab-case 分类
  readonly message: string  // 人类可读解释
}
7. @deepseek-ai/dsh-plan API
计划模式投影：
active
（日志中生效的状态）和
pending
（选择目标状态但尚未完成）。
7.1 PlanProjection
interface PlanProjection {
  active: boolean    // 日志中生效的计划状态
  pending: boolean   // 有待完成的 /plan 选择
}
通过
SessionProjectionMap.plan
投影键访问。能力缺失（计划模式未组合）为键的缺失，而非值。
8. @deepseek-ai/dsh-schedule API
会话本地的持久提醒系统：支持延迟一次性、绝对一次性、固定频率循环提醒。
8.1 ScheduleRecord 类型
// 延迟一次性提醒
interface AfterScheduleRecord {
  readonly id: ScheduleId
  readonly kind: 'after'
  readonly prompt: string
  readonly afterSeconds: number        // 正安全整数
  readonly scheduledAt: string         // RFC 3339 UTC
}

// 绝对时间一次性提醒
interface AtScheduleRecord {
  readonly id: ScheduleId
  readonly kind: 'at'
  readonly prompt: string
  readonly scheduledAt: string
}

// 固定频率循环提醒
interface EveryScheduleRecord {
  readonly id: ScheduleId
  readonly kind: 'every'
  readonly prompt: string
  readonly everySeconds: number        // 不低于 5 分钟
  readonly scheduledAt: string
}
8.2 ScheduleView
type ScheduleView = ScheduleRecord & {
  readonly state: 'scheduled' | 'overdue'
  readonly deliveryMode: 'session-local'
}
8.3 变更类型
type ScheduleChange =
  | { version: 1; operation: 'create';  schedule: ScheduleRecord }
  | { version: 1; operation: 'delete';  id: ScheduleId }
  | { version: 1; operation: 'dispatch'; id: ScheduleId; ... }
8.4 错误类型
错误码
说明
invalid_prompt
空提醒内容
invalid_selector
缺失/冲突/不支持的选择器
invalid_rule
无效规则或管理参数
invalid_time_zone
无效或不支持的 IANA 时区
not_future
绝对目标不在严格未来
frequency_too_high
固定频率规则过快
persistence_uncertain
必需持久化检查点未完成
第三部分：扩展与集成
9. 事件系统 API
DSH 使用 Cordis 事件系统，支持三种分发模式：
emit
（火并遗忘）、
waterfall
（链式拦截）、
serial
（顺序执行）。
9.1 Agent 生命周期事件
事件名
模式
说明
agent/created
emit
Agent 发布后触发。同步失败可否决发布。
agent/disposed
emit
Agent 离开注册中心时触发。
agent/status
emit
状态变更（
idle
⇄
running
）。
agent/session-start
emit
会话生命周期开始（首次轮次前）。
agent/inbox/inserted
emit
消息进入实时 inbox。
agent/inbox/claimed
emit
消息从 inbox 中被认领。
agent/inbox/discarded
emit
消息从 inbox 中被丢弃。
agent/pre-step
waterfall
拒绝或替换进入步骤的消息。
agent/request
waterfall
替换冻结的调用配置。
agent/request-error
waterfall
处理失败的模型请求。
agent/turn-stopping
serial
轮次即将关闭。
agent/error
emit
步骤或轮次出错。
9.2 Session 事件
事件名
模式
说明
session/created
emit
会话发布。同步失败可否决。
session/disposed
emit
会话离开存储。
session/event
emit
事件追加后的通知（提交后、异步通知）。
session/flush
parallel
等待的持久性检查点。
9.3 LLM 事件
事件名
模式
说明
llm/stream
waterfall
每次流式模型调用的拦截点。
llm/adapters-updated
emit
适配器拓扑变更通知。
9.4 其他事件
事件名
模式
说明
skills/change
emit
技能提供者或目录变更。
fs/write-intent
waterfall
写入意图决策。
fs/edit-intent
waterfall
编辑意图决策。
fs/observed
emit
文件观察记录。
10. 作用域系统 API
@deepseek-ai/dsh-scope
提供带标签的上下文原语：创建标记注册的 Cordis 上下文，并为该身份构建路由专用的事件载体。
10.1 核心函数
createScope(ctx: Context, key: ScopeKey, options?: CreateScopeOptions): Scope
在
ctx
下铸造作用域。作用域上下文继承铸造插件的依赖 API 并拥有通过它进行的所有注册。
interface Scope {
  ctx: Context
  rawDispose: () => Promise<void> | void
  dispose(): Promise<void>
}
scopeTarget<T extends object>(base: T, key: ScopeKey | undefined): Scoped<T>
构建不透明接收器，保留基础过滤器，全局接纳未标记监听器，并接纳匹配 key 或其任何祖先的标记监听器。事件向上流动，永不向下。
scopeOf(ctx: Context): ScopeKey | undefined
读取上下文继承的最近作用域标签。
bindScopeParent(key: ScopeKey, parent: ScopeKey): ScopeParentBinding
将
parent
绑定为
key
的封闭作用域。返回可重新绑定的句柄。
scopeParentOf(key: ScopeKey): ScopeKey | undefined
读取 key 的封闭作用域。
scopeChainOf(key: ScopeKey | undefined): ScopeKey[]
从 key 到根祖先的链（最近优先）。
isScopeCarrier(value: unknown): value is Scoped<object>
测试值是否为作用域载体。
carrierKeyOf(value: unknown): ScopeKey | undefined
读取载体的路由 key。
11. 错误码和异常类型
11.1 LLM 错误
class
LlmError extends HarnessError
错误码
说明
AUTH
认证失败
RATE_LIMIT
速率限制
NO_ADAPTER
无适配器注册
DUPLICATE_ADAPTER
适配器重复注册
INVALID_ADAPTER
适配器验证失败
INVALID_CREDENTIAL
凭证无效
UNSUPPORTED_REASONING_EFFORT
不支持的推理努力级别
INVALID_PREPARED_CALL
预准备调用状态无效
REGISTRATION_DISPOSED
已释放的注册尝试替换
DUPLICATE_DIRECTORY
可配置 provider 重复
INVALID_DIRECTORY
可配置 provider 验证失败
ABORTED
操作被中止
11.2 文件系统错误
class
FsError extends HarnessError
错误码
说明
FS_NOT_FOUND
目标不存在
FS_NOT_TEXT
非文本文件
FS_TOO_LARGE
文件过大
FS_PERMISSION_DENIED
权限拒绝
FS_SANDBOX_DENIED
沙箱策略拒绝
FS_STALE_VERSION
版本过期
FS_NOT_OBSERVED
目标未被观察
FS_AMBIGUOUS_EDIT
编辑匹配不明确
FS_EDIT_NOT_FOUND
编辑目标文本未找到
11.3 终端错误
class
TerminalError extends Error
错误码
说明
DUPLICATE_BACKEND
后端类型重复
DUPLICATE_NAME
会话名称重复
FOREIGN_SESSION
会话属于其他 Agent
NO_BACKEND
未找到后端
NO_SESSION
会话不存在
OWNER_NOT_LIVE
所有者不再存活
SEND_ACTIVE
已有活跃发送操作
SERVICE_DISPOSING
服务正在释放
11.4 目标错误
class
GoalError extends Error
错误码
说明
GOAL_NOT_FOUND
无当前目标
GOAL_ALREADY_EXISTS
目标已存在且非完成
GOAL_STALE_REVISION
过期的 CAS 引用
GOAL_INVALID_TRANSITION
无效的阶段转换
GOAL_INVALID_OBJECTIVE
无效的目标内容
GOAL_INVALID_MAX_ROUNDS
无效的轮次上限
GOAL_INVALID_EDIT
编辑缺少变更字段
GOAL_AGENT_NOT_LIVE
Agent 不在注册中心
11.5 会话分叉错误
class
SessionForkError extends Error
错误码
说明
SESSION_NOT_FOUND
源会话不存在
SESSION_NOT_LIVE
源对象非活跃实例
SESSION_ALREADY_EXISTS
子会话 ID 已占用
INVALID_BOUNDARY
边界非连续现有 seq
OPEN_TURN
选中的前缀结束在开放轮次内
12. 配置文件格式
12.1 cordis.yml 配置
DSH 使用 Cordis 配置系统，支持 YAML 格式的声明式插件组合。配置文件通常命名为
cordis.yml
或
cordis.snapshot.yml
。
# cordis.yml 示例结构
plugins:
  - name: '@deepseek-ai/dsh-agent-loop'
    config:
      # 插件配置
  - name: '@deepseek-ai/dsh-llm-deepseek'
    config:
      apiKey: '${DEEPSEEK_API_KEY}'

services:
  llm:
    # LLM 服务配置
  fs:
    # 文件系统配置
    sandboxMode: 'landlock'
12.2 AgentOptions 配置
interface AgentOptions {
  provider?: string    // 如 'deepseek', 'pi-ai'
  model?: string       // 如 'deepseek-chat', 'claude-sonnet-4-20250514'
  maxTokens?: number   // 如 16384
}
12.3 环境变量
变量名
说明
DEEPSEEK_API_KEY
DeepSeek API 密钥
PI_AI_API_KEY
Pi AI (OpenAI 兼容) API 密钥
DSH_WORKSPACE
默认工作区路径
DSH_CONFIG_PATH
配置文件路径覆盖
12.4 设置文件
用户设置通过 Web UI 的设置面板管理，存储在用户配置目录中。主要命名空间：
general
— 通用设置
models
— 模型配置和 API 密钥
plugins
— 插件管理
附录：包结构概览
DSH 采用 pnpm monorepo 结构，主要包按功能域组织：
包路径
服务注入
说明
packages/core/agent
ctx.agents
Agent 注册中心和生命周期
packages/core/session
ctx.sessions
会话存储和事件溯源
packages/core/scope
—
作用域原语（函数式导出）
packages/core/tools
—
工具 Schema 和类型
packages/core/system-prompt
—
系统提示组装
packages/llm/llm
ctx.llm
LLM 运行时和适配器注册
packages/llm/llm-deepseek
—
DeepSeek 适配器
packages/llm/llm-pi-ai
—
Pi AI 适配器（OpenAI 兼容）
packages/llm/token-meter
—
Token 计量
packages/fs/fs
ctx.fs
文件系统抽象
packages/fs/fs-local
—
本地文件系统后端
packages/fs/fs-sandbox
—
沙箱文件系统后端
packages/terminal/terminal
ctx.terminals
PTY 会话服务
packages/skill/skill
ctx.skills
技能注册中心
packages/goal/goal
ctx.goals
目标管理服务
packages/plan/plan-mode
—
计划模式投影
packages/schedule/schedule
—
定时提醒服务
DeepSeek Harness API 参考手册 | 基于源码分析生成 | 2026-08-28