---
title: "DeepSeek Harness 协议适配层深度分析"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 协议适配层"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 协议适配层深度分析
DeepSeek Harness
协议适配层深度分析
深入剖析 MCP、ACP、Typert API Gateway 三大协议适配层的架构设计、实现细节、交互模式与扩展策略
目录
P1
MCP协议概述
— Model Context Protocol 核心概念与 DSH 角色
P1
MCP适配层实现
— Server注册、工具发现、调用流程、资源管理
P1
ACP协议概述
— Agent Client Protocol 编解码与消息类型
P2
ACP适配层实现
— 序列化、连接管理、错误处理
P2
API网关
— Typert Gateway 路由、转发、认证授权
P2
远程调用
— Agent发现、RPC机制、超时重试
P3
协议对比
— MCP vs ACP vs OpenAPI 适用场景
P3
扩展性设计
— 新协议接入、版本管理、兼容策略
P3
改进建议
— 架构优化与工程实践建议
1. MCP协议概述
1.1 MCP是什么（Model Context Protocol）
Model Context Protocol (MCP)
是由 Anthropic 主导制定的开放协议标准，旨在为大语言模型（LLM）提供一个统一的外部工具与数据源接入框架。MCP 定义了一套基于 JSON-RPC 2.0 的请求/响应/通知消息格式，使得任意 LLM 客户端能够以标准化的方式发现、调用远程服务器暴露的工具（Tools），并读取其提供的资源（Resources）。
在 DeepSeek Harness（DSH）项目中，MCP 扮演着
外部工具生态桥梁
的角色。DSH 作为 LLM Agent 运行时，需要连接各种外部 MCP Server（如浏览器控制、内存管理、文件系统等），将这些服务器暴露的工具无缝注册到自身的工具注册表中，使 Agent 模型能够在推理过程中自动发现并调用这些能力。
1.2 MCP的核心概念
Server
MCP Server 是工具和资源的提供方。它通过 stdio 或 HTTP 传输层暴露一组命名工具和可读资源。每个 Server 拥有唯一的
serverName
，作为命名空间前缀。
Client
MCP Client 是消费方，负责连接 Server、发现工具列表（
tools/list
）、调用工具（
tools/call
），并管理传输层生命周期和重连策略。
Tool
Tool 是 Server 暴露的可调用能力单元。每个 Tool 有名称、描述、JSON Schema 输入参数和可选的输出 Schema。Client 通过
tools/call
发送参数并接收结构化结果。
Resource（资源）
Resource 是 Server 提供的只读数据，通过 URI 标识。Client 可以列出资源（
resources/list
）、读取内容（
resources/read
）并订阅变更通知（
resources/subscribe
）。在 DSH 的 MCP 适配层中，资源管理主要通过内容块类型
resource_link
和
resource
来处理——当 MCP 工具返回包含资源链接的结果时，适配层会将其转换为文本描述嵌入到模型上下文中。
1.3 MCP在DSH中的角色
DSH 项目的 MCP 适配层位于
packages/mcp/mcp-client/
，它是一个
Cordis 插件
（命名导出，无默认导出），以 effect-scoped 生命周期运行。每个插件实例连接一个 MCP Server，多个实例通过
cordis.yml
配置加载多个 Server。
关键设计决策：
DSH 不实现 MCP Server 端，仅作为 Client 连接外部 Server。这意味着 DSH 是 MCP 生态的纯消费者，其适配层专注于：连接管理、工具桥接、结果转换三大职责。
从架构定位看，MCP 适配层位于 DSH 的工具管道（Tool Pipeline）最外层，它将外部 MCP Server 的工具以
mcp__<serverName>__<rawName>
的命名约定注册到
ctx.tools
，使 Agent 的工具选择和调用逻辑对 MCP 工具完全透明——Agent 无需知道某个工具是原生工具还是 MCP 远程工具。
2. MCP适配层实现
2.1 MCP Server的注册和管理
插件入口与配置
MCP 客户端插件的入口在
packages/mcp/mcp-client/src/index.ts
。插件声明
inject = ['tools']
，依赖 DSH 的工具注册服务。配置通过 Schemastery 进行运行时校验，支持两种传输模式：
配置字段
StdioConfig
StreamableHttpConfig
transport
'stdio'
'streamable-http'
serverName
必填，匹配
/^[A-Za-z0-9_-]{1,32}$/
，用于生成公共工具名前缀
连接参数
command
,
args
,
env
,
cwd
url
,
headers
toolCallTimeoutMs
默认 60000ms，单次工具调用超时
failOnStartupError
默认 false；true 时初始连接失败会拒绝插件激活
reconnect
自动重连策略（enabled, initialDelayMs, maxDelayMs, maxAttempts）
命名空间隔离
DSH 使用
WeakMap<Context, Set<string>>
管理活跃的
serverName
预留。当同一进程中有多个应用实例（如测试场景），每个应用的命名空间相互隔离。重复的
serverName
会在插件加载时抛出明确的错误信息，而不是静默覆盖：
// 源码引用：packages/mcp/mcp-client/src/index.ts:148-161
ctx.effect(() => {
  let names = activeServerNames.get(ctx.root)
  if (!names) {
    names = new Set()
    activeServerNames.set(ctx.root, names)
  }
  if (names.has(config.serverName)) {
    throw new Error(
      `mcp-client: serverName "${config.serverName}" is already in use ...`
    )
  }
  names.add(config.serverName)
  return () => void names.delete(config.serverName)
}, 'mcp-client.serverName')
这种设计遵循了 DSH 的
effect-scoped 生命周期
模式：当插件被 dispose 时（包括 HMR 热替换），命名空间自动释放，新的实例可以重新使用相同的
serverName
。
2.2 工具发现和调用流程
连接监督器（Connection Supervisor）
connection.ts
实现了一个
连接监督器
模式，它是整个 MCP 适配层最复杂的组件。监督器负责：
代际管理
：每个连接尝试产生一个新的
Client
实例（"代际"），MCP SDK 的设计要求一个 Protocol 绑定一个 Transport 终身不变
工具同步串行化
：通过
syncChain
Promise 链确保所有
syncTools
调用不会交错执行
指数退避重连
：从
initialDelayMs
（默认500ms）开始，每次失败翻倍，上限
maxDelayMs
（默认30s）
稳定性窗口
：连接存活时间超过
maxDelayMs
后重置失败计数器，避免长期运行后的一次断连耗尽重连预算
┌──────────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  Plugin Load │───▶│  Start      │───▶│  Connect     │───▶│  Sync Tools  │
│  Config      │    │  Connection │    │  Generation  │    │  (Phase 1:   │
│  Validation  │    │  Supervisor │    │  (new Client)│    │   fetch list)│
└──────────────┘    └──────┬──────┘    └──────┬───────┘    └──────┬───────┘
                           │                  │                   │
                           │           ┌──────▼───────┐    ┌──────▼───────┐
                           │           │  Tool List   │    │  Phase 2:    │
                           │           │  Changed     │    │  Swap Genera-│
                           │           │  Notification│    │  tions (old  │
                           │           └──────┬───────┘    │  dispose +   │
                           │                  │            │  new register│
                           │                  ▼            └──────────────┘
                           │           ┌──────────────┐
                           │           │  Re-sync     │
                           │           │  (enqueue)   │
                           │           └──────────────┘
                           │
                    ┌──────▼──────┐
                    │  Disconnect │◀── onclose / error
                    │  Detected   │
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │  scheduleReconnect()    │
              │  - Check stability      │
              │  - Update failedAttempts│
              │  - Compute delay        │
              │  - setTimeout retry     │
              └─────────────────────────┘
工具名转换规则（Naming Contract）
MCP 工具在 DSH 中的公共名称由
publicToolName()
函数确定性地生成：
// 源码引用：packages/mcp/mcp-client/src/tools.ts:111-117
export function publicToolName(serverName: string, rawName: string): string {
  const joined = `mcp__${serverName}__${rawName}`
  const normalized = joined.replace(INVALID_NAME_CHARS, '_')
  if (normalized === joined && normalized.length <= MAX_PUBLIC_NAME_LENGTH) return normalized
  const hash = createHash('sha256')
    .update(`${serverName}\0${rawName}`).digest('hex').slice(0, 12)
  return `${normalized.slice(0, MAX_PUBLIC_NAME_LENGTH - 12 - 1)}_${hash}`
}
转换规则分三步：（1）拼接
mcp__{serverName}__{rawName}
；（2）将非法字符（非
[A-Za-z0-9_-]
）替换为下划线；（3）若名称超过 64 字符或发生了字符替换，则截断并附加 12 字符的 SHA-256 哈希后缀，确保不同 MCP 身份永远不会坍缩为相同的公共名称。
两阶段工具同步（Two-Phase Sync）
syncTools()
采用两阶段策略保证安全的工具列表更新：
Fetch 阶段
：通过非缓存的
tools/list
分页请求获取完整的工具列表，构建下一代
ToolDefinition
映射。任何失败（网络错误、重复工具名）都直接拒绝，上一代工具保持注册不变。
Swap 阶段
：先 dispose 上一代的所有注册器，再注册新一代。如果注册时发生命名冲突（说明有外部注册占用了该 Server 的命名空间），则回滚——注销已注册的工具，记录错误日志。
工具调用流程
当 Agent 调用一个 MCP 工具时，执行流程如下：
Agent 推理选定工具，输出工具名（如
mcp__memory__save
）和 JSON 参数
DSH 的 ToolRuntime 通过公共名称查找
ToolDefinition
createExecutor()
创建的闭包函数被调用，它用
原始 MCP 工具名
（非公共名）发送
tools/call
请求
请求附带 AbortSignal 和超时（
toolCallTimeoutMs
）
返回的 MCP 内容块经过
projectContent()
映射为 DSH 的
ContentBlock[]
如果结果包含图片，进入图片准入管线（解码、验证 base64、检查模型图像能力、持久化存储）
MCP 的
isError: true
结果被转换为 throw，由 ToolRuntime 的 catch 路径产生
isError
结果供模型学习
2.3 资源的读取和订阅
DSH 的 MCP 适配层对资源（Resource）的处理相对轻量。当 MCP 工具返回的内容块中包含
resource_link
类型时，适配层将其转换为文本描述：
// 源码引用：packages/mcp/mcp-client/src/tools.ts:538-541
case 'resource_link':
  if (block.name === undefined || block.uri === undefined) {
    text.push('[resource link unavailable: the MCP block is missing its name or URI]')
  } else {
    text.push(`Resource link: ${block.name} (${block.uri})`)
  }
对于嵌入式资源（
resource
类型）和音频（
audio
类型），当前仅输出占位文本，原始数据仍可供程序化调用者访问。这体现了 DSH 的
渐进式适配策略
：优先支持文本和图片（LLM 最常见的输入输出模态），对其他模态预留接口但不阻塞核心流程。
图片处理管线
MCP 适配层的图片处理是最精密的部分之一。当工具返回包含
image
类型内容块的结果时：
解码验证
：严格校验
mimeType
（仅接受 PNG/JPEG/WebP/GIF）和 base64 数据（拒绝 URL-safe 变体和空白符）
模型能力检查
：通过
resolveImageAdmission()
查询当前路由的模型是否支持图像输入
持久化存储
：通过
attachments.saveImages()
将图片写入持久存储，获得
ImageAttachmentRef
延迟投影
：使用
WeakMap<ToolExecution, PreparedProjection>
在 execute 阶段预计算图片投影，在
finalizeContent
阶段才最终确认
安全边界：
MCP 工具返回的数据来自外部不可信的 MCP Server 进程（通过 JSON-RPC 传输）。适配层在处理每个字段时都进行了防御性验证——即使 MCP 规范声明某些字段为必填，代码也提供了回退值。
3. ACP协议概述
3.1 ACP是什么（Agent Client Protocol）
Agent Client Protocol (ACP)
是一个面向 Agent 自动化的通信协议，由
@agentclientprotocol/sdk
提供。与 MCP 面向工具/资源不同，ACP 关注的是
会话级别的 Agent 交互
——它定义了客户端如何创建 Agent 会话、发送提示（prompt）、接收流式输出、取消操作和处理权限请求。
ACP 的设计目标是为编程客户端（如
dsh-subagent-acp
）提供对 DSH Agent 的自动化访问能力。它是一个
纯自动化传输层
，不涉及人类交互或 UI 呈现——所有展示和人机交互特性留在 DSH 的 UI 模块中。
3.2 ACP的编解码器
协议版本
DSH 的 ACP 实现遵循
PROTOCOL_VERSION
常量（由 SDK 定义），在
initialize
响应中返回。DSH 是单版本 Agent，对"相同版本则支持、否则返回最新支持版本"的规范要求，两者都解析为当前服务器的唯一版本。
传输层
ACP 使用
NDJSON 流
（Newline-Delimited JSON）作为传输格式。生产环境通过
ndJsonStream()
连接标准输入/输出（
process.stdin
/
process.stdout
），测试环境可注入自定义的
Stream
对象。每条消息是一个独立的 JSON 对象，以换行符分隔。
TurnEndReason 到 StopReason 的映射
codec.ts
实现了 DSH 内部生命周期到 ACP 线协议的纯翻译函数：
// 源码引用：packages/acp/acp/src/codec.ts:14-33
export function turnEndToStopReason(reason: TurnEndReason): StopReason {
  switch (reason.kind) {
    case 'completed':   return 'end_turn'
    case 'max-tokens':  return 'max_tokens'
    case 'aborted':     return 'end_turn'  // 非显式取消
    case 'interrupted': return 'cancelled'  // 显式客户端取消
    case 'blocked':
    case 'error':       return 'end_turn'
    default:            return 'end_turn'
  }
}
关键语义区分：
cancelled
仅用于显式客户端取消（
session/cancel
）和 dispose，由 Hook 或其他所有者中断的 turn 视为普通静默，报告
end_turn
。
3.3 ACP消息类型
消息类型
方向
说明
initialize
Client → Server
协商协议版本、Agent 能力（图像/音频/嵌入上下文）、认证方法
authenticate
Client → Server
认证握手（DSH 实现为空操作）
session/new
Client → Server
创建新 Agent 会话，返回
sessionId
session/prompt
Client → Server
发送提示内容（文本/图片/resource_link），阻塞等待完成
session/cancel
Client → Server
取消当前进行中的提示或自主工作
session/update
(通知)
Server → Client
流式推送
agent_message_chunk
（助手文本/图片片段）
requestPermission
Server → Client
工具权限决策请求（allow-once / reject-once）
ACP vs MCP 的本质区别：
MCP 是
工具协议
（"调用这个工具"），ACP 是
会话协议
（"与这个 Agent 交互"）。MCP 的粒度是单次工具调用，ACP 的粒度是完整的 prompt-response 循环。在 DSH 中，MCP 让 Agent 获得能力，ACP 让外部程序使用 Agent。
能力协商
在
initialize
阶段，DSH 会动态检测当前配置的模型是否支持图像输入，据此设置
agentCapabilities.promptCapabilities.image
。这个检测通过
supportsAcpImagePrompts()
函数完成，它检查：
attachments
服务是否存在且支持兼容的媒体类型
llm
服务是否存在
provider 和 model 是否已配置
模型的
inputModalities
是否包含
'image'
只有所有条件满足时才在初始化响应中声明图像能力，确保协议承诺与实际能力一致。
4. ACP适配层实现
4.1 消息的序列化和反序列化
内容准入管线（Content Admission Pipeline）
ACP 适配层的内容处理由
content.ts
实现，包含两个方向的转换：
入站方向（Prompt 准入）：
admitAcpPrompt()
将 ACP 线协议内容块转换为 DSH 核心
ContentBlock[]
。转换过程经过严格的两遍扫描：
验证遍
：检查每个内容块的类型合法性（仅接受 text/image/resource_link），解码并验证图片的 mimeType 和 base64 数据。任何验证失败立即抛出
AcpContentError
重建遍
：验证通过后，将文本块合并、图片替换为持久化后的
ImageAttachmentRef
、resource_link 转换为格式化文本。空提示（无有效文本或图片）被拒绝
// 源码引用：packages/acp/acp/src/content.ts:124-205 (核心逻辑)
export async function admitAcpPrompt(
  ctx: Context, agent: Agent,
  prompt: readonly AcpContentBlock[],
  imageEnabled: boolean, signal: AbortSignal,
): Promise<ContentBlock[]> {
  // Phase 1: validate all blocks
  const images: SaveImageAttachment[] = []
  for (const block of prompt) {
    switch (block.type) {
      case 'text': case 'resource_link': break
      case 'image':
        if (!imageEnabled) throw new AcpContentError('...', 'invalid')
        images.push(decodeImage(block))  // strict base64 + mimeType check
        break
      case 'audio': throw new AcpContentError('audio not supported', 'invalid')
      case 'resource': throw new AcpContentError('embedded resource not supported', 'invalid')
    }
  }
  // Phase 2: persist images and rebuild ordered content
  // ... (attachment storage, content reconstruction)
}
出站方向（Assistant 输出）：
assistantBlockToAcp()
将 DSH 的助手内容块转换回 ACP 线格式。文本块直接映射，图片块需要从持久化存储中重新读取并进行完整性验证后编码为 base64：
// 源码引用：packages/acp/acp/src/content.ts:215-238
export async function assistantBlockToAcp(
  ctx: Context, block: ContentBlock,
): Promise<AcpContentBlock | undefined> {
  if (block.type === 'text') {
    return block.text.length === 0 ? undefined : { type: 'text', text: block.text }
  }
  if (block.type !== 'image') return undefined
  const stored = await attachments.readImage(block.attachment)
  return {
    type: 'image',
    data: Buffer.from(stored.data).toString('base64'),
    mimeType: stored.ref.mediaType,
  }
}
错误分类体系
AcpContentError
类引入了两级错误分类：
'invalid'
（请求参数无效，映射为 ACP 的
invalidParams
）和
'internal'
（内部故障，映射为
internalError
）。这种分类确保协议层面的错误报告精准反映问题根源——客户端可以通过
invalidParams
判断是否需要修改请求重试，而
internalError
则意味着服务器端问题。
4.2 连接管理
会话生命周期
ACP 桥接器通过
Map<SessionId, SessionRecord>
管理活跃会话。每个
SessionRecord
包含：
agent
：该会话对应的 DSH Agent 实例
dispose
：Agent 的完整销毁函数（包括注册表、循环和会话清理）
outputTail
：有序的助手输出投递 Promise 链，确保跨异步附件读取的消息/块顺序
inflight
：当前进行中的 prompt 生命周期状态（包含准入、队列、turn、结算各阶段）
Prompt 生命周期状态机
每个 prompt 在
inflight
中经历以下阶段：
┌─────────┐    ┌────────────┐    ┌──────────┐    ┌──────────┐    ┌───────────┐
│ Reserve │───▶│  Admission │───▶│  Queue   │───▶│  Agent   │───▶│  Settle   │
│ Slot    │    │  (content  │    │  Message │    │  Work    │    │  (quiesce)│
│         │    │   + image) │    │  to inbox│    │  + output│    │           │
└─────────┘    └─────┬──────┘    └──────────┘    └──────────┘    └─────┬─────┘
                     │                                                  │
              ┌──────▼──────┐                                    ┌──────▼──────┐
              │  Cancel?    │                                    │  Resolve    │
              │  Abort      │                                    │  StopReason │
              │  Controller │                                    │  or Reject  │
              └─────────────┘                                    └─────────────┘
结算（Settlement）
是 ACP 适配层最精密的同步机制。
settleAfterQuiescence()
等待三个条件同时满足才完成一个 prompt：
admissionDone
：内容准入（包括附件写入）完成
agent.whenIdle()
：Agent 处于空闲状态（所有模型调用和工具执行完毕）
outputTail
：所有有序的助手输出投递完成
连接关闭与资源清理
当 ACP 连接关闭时，
quiesce()
函数执行有序的全局清理：
标记
closed = true
，拒绝新请求
取消所有进行中的 prompt（abort admission controller + cancel agent）
等待所有会话的准入完成、Agent 空闲、输出投递完成
排水可续子 Agent（
drainContinuableDescendants
），子级先于父级销毁
调用每个会话的
dispose()
，聚合并报告失败
4.3 错误处理
ACP 适配层的错误处理遵循几个关键原则：
隔离性
：单个会话的输出转换失败不影响其他会话——
outputTail
的 catch 路径记录错误并设置
inflight.outputError
，但不阻塞链的后续任务
有序性
：通过
notify()
函数（
conn.sessionUpdate()
）的 try-catch 包装，确保传输层写入失败不会冒泡为业务错误
精确性
：权限请求通过
approval/request
事件处理，ACP 桥接器提供一次性选择（allow-once / reject-once），不从未知客户端响应推断持久授权
完整性
：
quiesce()
中的
AggregateError
聚合了所有会话的销毁失败，每个失败的因果链通过
errorChain()
完整嵌入消息
5. API网关
5.1 网关的路由机制
DSH 的 API 网关基于
Typert
（Type-safe Remote）协议实现，位于
packages/api/gateway/
。网关作为 Cordis 服务注册在
ctx.typertGateway
，通过 Connection 的 RPC 拦截器注册
/api
路由前缀。
端点声明与路由匹配
网关使用两段式端点格式
<namespace>/<method>
（如
goals/create
）。路由匹配通过
claimsEndpoint()
实现，它检查：
端点格式是否为合法的两段路径
是否有严格的生成描述符（
ctx.typert.local.get(endpoint)
）
是否曾被见过（
hasSeen
）——如果见过但当前不可用，拒绝 SRC 回退
是否有源码级 SRC 标记匹配——通过遍历所有 Cordis 服务的
typertRemote
绑定
// 源码引用：packages/api/gateway/src/index.ts:114-120
private claimsEndpoint(endpoint: string): boolean {
  const segments = endpoint.split('/')
  if (segments.length !== 2 || segments[0] === '' || segments[1] === '') return false
  if (this.ctx.typert.local.get(endpoint) !== undefined || this.ctx.typert.local.hasSeen(endpoint)) return true
  this.srcClaims ??= this.collectSrcClaims()
  return this.srcClaims.has(endpoint)
}
描述符解析层次
resolveDescriptor()
实现了三级描述符解析：
严格描述符
（Strict）：来自 Typert 编译器生成的
InvocationDescriptor
，包含完整的参数类型、编解码器和 Schema 验证。优先级最高
已撤回检查
：如果端点曾经有严格描述符但已被撤回（
hasSeen
），则拒绝——不允许从严格降级到 SRC
SRC 回退
：从运行时 JavaScript 原型中解析参数名，匹配查找提供者，构建临时描述符。仅在开发模式下可用
5.2 请求转发
参数解析与查找提供者
网关的参数处理分为两类：
JSON 参数
（
source: 'json'
）：直接从
args
中取值，经过编解码器验证后传入业务方法
Lookup 参数
（
source: 'lookup'
）：从
args
中获取线标识（如
agentId
），通过注册的查找提供者（如
ctx.typert.lookups.get('agent')
）解析为运行时对象（如
Agent
实例）
这种设计使得复杂 Host 对象（如 Agent、Session）可以通过线标识传递，而不需要跨线序列化整个对象图。查找提供者是可配置的——Host 组合可以使用
ctx.typert.lookups.configure()
覆盖解析策略。
上下文提供者
@RemoteScope
标记的方法使用
Context Provider
模式：通过
ctx.typert.contexts.getHost()
获取上下文提供者，将线标识解析为作用域 Context，再从该 Context 中获取服务实例。这使得方法调用可以自动绑定到正确的 Agent 作用域。
5.3 认证和授权
网关的信任模型建立在 Connection 层之上。RPC 拦截器在注册时声明
{ authority: 'trusted-host' }
，意味着
/api
路由的请求在到达网关之前已经通过了 Connection 的统一信任检查。网关本身不实现认证逻辑，而是依赖底层传输的安全保证。
对于参数级的授权，网关通过
hasApiRemoteSubagentOwner()
函数实现子 Agent 所有权围栏：如果目标会话的生命周期属于子 Agent 路由，则拒绝通用 Remote 调用，要求使用子 Agent 投递通道。
边界验证：
网关在业务方法执行前后都进行严格的边界验证。
assertExactArguments()
确保
args
的字段与描述符精确匹配（不多不少），
decode()
对入参和返回值都进行 Schema 解析和 JSON 安全性检查（
assertJsonValue
——递归检查循环引用、非有限数、Symbol 属性等）。
6. 远程调用
6.1 远程Agent的发现
远程 Agent 发现由
packages/api/remotes/src/agent-lookup.ts
实现。
createApiRemoteAgentResolver()
创建一个共享的 Agent 解析器，同时配置 Typert 查找和上下文提供者：
// 源码引用：packages/api/remotes/src/agent-lookup.ts:199-208
ctx.inject(['typert'], (typeCtx) => {
  const resolveAgent = async (sessionId: SessionId): Promise<Agent> => {
    const found = await agentFor(sessionId)
    if ('error' in found) throw new TypertLookupFailure(found.error)
    return found.agent
  }
  typeCtx.typert.lookups.configure('agent', resolveAgent)
  typeCtx.typert.lookups.configure('session', async sessionId =>
    (await resolveAgent(sessionId)).session)
  typeCtx.typert.contexts.configureHost('agent', async sessionId =>
    (await resolveAgent(sessionId)).ctx)
})
Agent 解析策略
agentFor()
函数实现了三级 Agent 查找：
活跃 Agent 复用
：检查
ctx.agents.get(sessionId)
，如果找到活跃 Agent 且不被子 Agent 路由拥有，则直接返回
冷恢复去重
：使用
resumes
Map 对并发的恢复请求去重——同一 sessionId 的多个调用者共享同一个恢复 Promise
持久化恢复
：通过
inspectApiRemoteSession()
从持久化存储中读取会话元数据和事件日志，调用
ctx.agents.resume()
恢复 Agent
恢复过程中还有多道安全检查：检查
origin === 'subagent'
、检查
parentSession
的活跃父级、检查在 setup 期间是否有其他路由抢占了所有权。
6.2 RPC调用机制
Client 端 Remote 命名空间
packages/api/gateway/src/client/index.ts
实现了 Client 端的
ctx.remote
服务。每个 Remote 命名空间（如
goals
）被注册为一个
RemoteNamespaceService
（Cordis 子服务，键为
remote.goals
），其方法通过
Object.defineProperty
定义为 getter，返回一个闭包函数。
方法调用流程：
Client 代码调用
ctx.remote.goals.create(agentId, request)
getter 闭包捕获当前 Context 和方法记录（direct + scoped）
invokeMethod()
优先尝试 scoped 调用（如果存在 Context binder），否则回退到 direct
参数经过严格编解码器验证后组装为
args
对象
通过
connection.rpc.call('/api', endpoint, { args }, signal)
发送 RPC 请求
返回值经过结果编解码器验证
Host 端 RPC 适配
Host 端的
dispatchRpc()
接收 Connection 转发的 RPC 请求，从 payload 中提取
namespace
、
method
和
args
，调用
invoke()
执行业务方法，最终返回标准化的
{ ok: true, value }
或
{ ok: false, error }
信封。
6.3 超时和重试
API 网关的超时和取消机制通过
AbortSignal
传递链实现：
Client 端
：每个挂载的 Remote 方法拥有一个
MountToken
（包含
AbortController
），贡献卸载时 abort 所有进行中的调用。调用者还可以传入额外的
AbortSignal
，通过
AbortSignal.any()
合并
传输层
：Connection RPC 将 signal 传递给 fetch 请求，实现端到端取消
Host 端
：如果描述符声明了
cancellation
参数，signal 被注入为最后一个参数传入业务方法。业务方法可以通过
signal.throwIfAborted()
实现协作式取消
超时处理
：API 网关本身不设固定超时（不同于 MCP 的
toolCallTimeoutMs
），超时由调用者通过 AbortSignal 控制。当 RPC 调用因取消而失败时，
RemoteInvocationCancelled
错误被转换为
{ code: 'cancelled' }
的 RPC 结果。
重试策略
：API 网关不实现自动重试。这与 MCP 适配层的设计不同——MCP 面向长期运行的外部进程连接，需要自动重连；而 API 网关面向同进程或可靠连接的 RPC 调用，失败通常意味着业务错误而非连接问题。对于需要重试的场景，策略由调用者或上层应用决定。
错误传播
错误来源
RPC 错误码
说明
参数不匹配、Schema 验证失败
arguments-invalid
/
input-invalid
客户端可修正
查找提供者不可用或未找到身份
lookup-unavailable
/
lookup-not-found
基础设施问题
服务不可用、方法不存在
service-unavailable
/
method-unavailable
Host 配置问题
子 Agent 所有权围栏
agent-busy
使用子 Agent 投递
Signal 取消
cancelled
正常操作
业务方法抛出异常
internal
保留原始错误消息
查找失败（TypertLookupFailure）
原始 failure
查找策略决定错误码
7. 协议对比
7.1 MCP vs ACP vs Typert API Gateway
维度
MCP (Model Context Protocol)
ACP (Agent Client Protocol)
Typert API Gateway
协议定位
工具/资源接入协议
Agent 会话自动化协议
类型安全的内部 RPC 协议
传输格式
JSON-RPC 2.0 over stdio/HTTP
NDJSON over stdio
JSON over Connection RPC (
/api
)
交互粒度
单次工具调用
完整 prompt-response 循环
单次方法调用（unary）
DSH 角色
Client（消费者）
Server（提供者）
Host 端 Server + Client 端 Consumer
类型安全
运行时 JSON Schema 验证
SDK 类型 + 运行时验证
编译时生成 + 运行时 Schema 双重验证
连接管理
指数退避重连、稳定性窗口
单连接生命周期、有序关闭
依赖 Connection 层
取消机制
AbortSignal + 超时
session/cancel 通知 + AbortController
AbortSignal 传递链
图片支持
base64 内联 + 持久化投影
base64 内联 + 持久化准入
不直接处理（业务层职责）
代码规模
~560 行（4 个源文件）
~545 行（4 个源文件）
~1320 行（6 个源文件，含 Client）
7.2 各协议的适用场景
MCP
适用：
连接外部工具生态系统（浏览器、文件系统、数据库、搜索引擎等），让 Agent 获得多样化的执行能力。跨语言、跨进程的工具标准化接入。
ACP
适用：
编程客户端自动化 Agent 交互（CI/CD 集成、批量处理、子 Agent 编排），需要会话管理和流式输出的场景。
Typert API
适用：
DSH 内部 Host-Client 通信（Web UI 与后端），需要类型安全的细粒度 RPC 调用，支持复杂对象图的查找解析。
7.3 互操作性
三个协议在 DSH 中形成了互补的层次结构：
MCP → DSH 工具注册表
：MCP 工具通过
mcp-client
插件桥接到
ctx.tools
，与原生工具统一注册。Agent 推理时无法区分工具来源
DSH Agent → ACP → 外部客户端
：ACP 桥接器将 DSH Agent 的完整能力暴露给编程客户端，包括会话管理、流式输出和权限协商
Client UI ↔ Typert API ↔ Host Services
：Typert 网关提供编译时类型安全的 RPC 通道，Web UI 通过
ctx.remote
调用 Host 业务方法
互操作的关键设计：
三个协议共享
ImageAttachmentRef
作为图片引用的通用标识。MCP 工具返回的图片、ACP prompt 中的图片、以及 Host 服务处理的图片，都通过同一套持久化附件系统（
attachments
服务）管理，确保跨协议的图片数据一致性。
8. 扩展性设计
8.1 如何添加新的协议支持
DSH 的协议适配层遵循 Cordis 插件架构，添加新协议的标准路径是：
创建包
：在
packages/
下新建目录，遵循
@deepseek-ai/dsh-<protocol>
命名
实现插件
：导出
name
、
inject
、
Config
、
apply(ctx, config)
四个命名导出
定义类型
：在独立的
types.ts
中声明
declare module '@deepseek-ai/cordis'
扩展，合并新服务到 Context
注册 invariant
：在
invariant.ts
中注册包级不变量检查（如 MCP 和 ACP 都有）
配置 cordis.yml
：在 bundle 的
cordis.yml
中声明插件实例和配置
新协议需要对接的 DSH 服务
DSH 服务
对接方式
示例
ctx.tools
注册 ToolDefinition
MCP:
ctx.tools.register(definition)
ctx.agents
创建/恢复 Agent
ACP:
agents.create({sessionId, ...})
ctx.sessions
会话事件监听
ACP:
ctx.on('session/event', ...)
ctx.typert
注册查找/上下文提供者
API:
typert.lookups.configure('agent', ...)
ctx.connection
RPC 拦截器
API:
connection.rpc.intercept('/api', ...)
8.2 协议版本管理
DSH 对三个协议采用不同的版本策略：
MCP
：通过
@modelcontextprotocol/sdk
依赖管理。SDK 版本更新可能引入新的消息类型或行为变更。DSH 使用非缓存请求（
listToolsUncached
、
callToolUncached
）绕过 SDK 的内部缓存，保持对协议行为的精确控制
ACP
：遵循
PROTOCOL_VERSION
常量。DSH 声明单一版本，初始化响应中的
protocolVersion
直接返回 SDK 定义的当前版本
Typert
：编译时生成的严格描述符是版本化的——每个
InvocationDescriptor
有唯一
id
。SRC 回退没有版本概念，仅在开发模式可用
8.3 向后兼容策略
MCP 兼容性
MCP 适配层通过以下机制保证向后兼容：
内容块处理的防御性编码——即使 MCP 服务器返回非标准内容，适配层也会输出占位文本而非崩溃
输出 Schema 的可选支持——
supportedOutputSchema()
捕获不支持的 Schema 而非抛出
Legacy
toolResult
形状的兼容处理——
createExecutor()
检查
Array.isArray(result.content)
并提供回退
ACP 兼容性
ACP 的兼容性通过 SDK 的
AgentSideConnection
保证。DSH 的实现只使用稳定的协议消息（initialize、newSession、prompt、cancel、sessionUpdate），不依赖实验性特性。认证方法返回空数组（
authMethods: []
），为未来添加认证预留空间。
Typert 兼容性
Typert 的兼容性最为严格：Client 端拒绝挂载非严格编解码器的描述符（
requireStrictDescriptor()
），这意味着 Host 端的描述符变更必须先重新生成 Client 贡献。SRC 回退仅在 Host 端可用，不进入 Client 的类型系统或运行时。
9. 改进建议
9.1 MCP 适配层
资源订阅支持
当前 MCP 适配层仅处理工具（Tools），未实现资源的主动列出和订阅能力。
resources/list
、
resources/read
和
resources/subscribe
是 MCP 规范的重要组成部分。建议在
mcp-client
插件中添加资源桥接功能，将 MCP 资源映射为 DSH 的可读数据源。
Prompt 模板支持
MCP 规范还定义了
prompts/list
和
prompts/get
，允许 Server 提供预定义的 prompt 模板。适配层可以将这些模板注册为 DSH 的技能（Skills），丰富 Agent 的交互能力。
工具描述的动态更新
虽然
ToolListChangedNotification
的处理已实现，但当前的 re-sync 是全量替换。对于拥有大量工具的 MCP Server，可以考虑实现差异同步（diff-based sync），减少不必要的工具注销和重新注册开销。
9.2 ACP 适配层
会话恢复能力
当前 ACP 桥接器创建的会话在连接关闭后即销毁。可以考虑添加会话持久化支持，使得 ACP 客户端断线重连后能够恢复之前的会话状态，而非从头开始。
并发 Prompt 支持
当前每个会话同时只允许一个 prompt（
if (record.inflight !== undefined) throw invalidParams(...)
）。对于长时间运行的任务，可以考虑支持排队或并行 prompt，提升客户端的使用灵活性。
更丰富的权限模型
当前权限请求仅提供
allow-once
和
reject-once
两种选择。可以扩展支持
allow-always
（本次会话内持续允许）和自定义权限范围，减少自动化客户端的交互频率。
9.3 API网关
流式 RPC 支持
当前 Typert 网关仅支持 unary 调用（一请求一响应）。对于增量数据推送（如 Agent 输出流、事件订阅），需要单独的数据协议。建议考虑将网关扩展为支持 server-streaming 模式，使 Remote 方法可以返回异步迭代器。
调用指标与追踪
网关是所有 Client-Host 通信的咽喉，但当前缺乏结构化的调用指标（延迟分布、错误率、吞吐量）。建议添加可选的遥测钩子，在
invoke()
方法的入口和出口采集指标，不侵入业务逻辑。
SRC 模式的安全加固
SRC 回退从 JavaScript 函数签名解析参数名（
methodParameterNames()
），使用
Function.prototype.toString()
获取源码。虽然仅在开发模式可用，但这种模式对压缩/混淆后的代码不健壮。建议添加环境检查，确保 SRC 仅在明确的开发标志下启用。
9.4 跨协议改进
统一的错误报告格式
三个协议使用不同的错误格式：MCP 使用
isError
布尔加文本，ACP 使用
RequestError
，Typert 使用
TypertGatewayError
。建议定义一个统一的 DSH 错误信封，包含
code
、
message
、
details
三层结构，便于监控和调试。
统一的配置验证
MCP 使用 Schemastery 进行配置验证，ACP 也使用 Schemastery 但结构更简单，Typert 的配置分散在生成器和注册器中。建议将所有协议适配层的配置统一到一个验证框架下，减少重复的边界检查代码。
共享的连接健康监控
MCP 有独立的连接监督器和重连逻辑，ACP 在连接关闭时执行全局清理，Typert 依赖 Connection 层。建议引入一个共享的连接健康服务，集中管理所有协议的连接状态、健康检查和故障恢复策略。
DeepSeek Harness 协议适配层深度分析 — 基于源码 packages/mcp/、packages/acp/、packages/api/ 的直接分析
生成日期：2026-08-29 | 全三部分完整版