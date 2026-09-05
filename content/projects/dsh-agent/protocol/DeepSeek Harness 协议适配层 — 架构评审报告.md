---
title: "DeepSeek Harness 协议适配层 — 架构评审报告"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 协议适配层"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 协议适配层 — 架构评审报告
协议适配层
架构评审报告
基于源码直接审查，聚焦潜在风险、安全隐患、可靠性缺陷与优化机会
目录
评审摘要与风险总览
MCP 适配层风险分析
ACP 适配层风险分析
API 网关风险分析
跨协议系统性风险
安全评审
可靠性与容错评审
性能优化建议
可维护性与工程实践
改进路线图
1. 评审摘要与风险总览
本报告对 DeepSeek Harness 的三个协议适配层进行了基于源码的架构评审。评审范围覆盖
packages/mcp/mcp-client/
、
packages/acp/acp/
、
packages/api/gateway/
和
packages/api/remotes/
，结合测试覆盖、已知事故（postmortem）和代码结构分析，共识别
23 项风险
。
风险分布
严重程度
数量
典型领域
严重
3
安全边界、已知事故模式
高
6
可靠性、连接管理、数据一致性
中
8
性能、功能完整性、可扩展性
低
4
代码组织、文档、防御性编程
信息
2
架构观察、设计权衡
各层健康度
MCP 适配层
评分：7.5/10
连接监督器设计精良，测试覆盖充分（1200+ 行测试）。主要风险集中在外部信任边界和 SDK 依赖。
ACP 适配层
评分：7.0/10
结算状态机精密但复杂度高。已知事故（postmortem #1）暴露了插件加载路径的系统性盲区。单 prompt 槽位限制了扩展性。
API 网关
评分：8.0/10
类型安全设计领先，编译时+运行时双重验证。SRC 回退的健壮性和 Client 端复杂度是主要关注点。
跨协议整合
评分：7.0/10
三个协议共享 ImageAttachmentRef 是好的互操作设计。缺乏统一的错误格式和可观测性是系统性短板。
2. MCP 适配层风险分析
严重
R-MCP-01：外部 MCP Server 返回的 base64 图片数据的内存放大风险
位置：
tools.ts
decodeImage()
描述：
当 MCP Server 返回一个恶意构造的大图片（如声明
mimeType: 'image/png'
+ 100MB base64 字符串），
Buffer.from(block.data, 'base64')
会在内存中创建等大的解码缓冲区。虽然
attachments.saveImages()
有
maxImageBytes
限制，但解码发生在验证之前——内存峰值出现在准入管线的最早阶段。
影响：
恶意或异常的 MCP Server 可通过单个工具调用耗尽进程内存，导致 OOM 崩溃。
在
decodeImage()
中添加 base64 字符串长度的前置检查（如
block.data.length > MAX_BASE64_LENGTH
），在
Buffer.from()
之前拒绝过大的输入。或者考虑流式解码+大小限制。
高
R-MCP-02：MCP SDK 依赖的隐式行为契约
位置：
connection.ts:18-19
、
tools.ts:72-95
描述：
DSH 使用非缓存请求（
listToolsUncached
、
callToolUncached
）绕过 SDK 的内部页面缓存，直接调用
client.request()
。这依赖于 SDK 的
request()
方法接受自定义 schema 参数的内部实现——如果 SDK 在未来版本中修改
request()
的签名或缓存行为，这些旁路调用可能静默失败。
影响：
SDK 升级可能导致工具同步和调用行为异常，且难以通过单元测试发现。
为 SDK 的关键 API 调用添加集成测试（使用
InMemoryTransport
的真实 SDK 连接），并在 package.json 中锁定 SDK 主版本。考虑在 CI 中添加 SDK 新版本的兼容性检查。
高
R-MCP-03：重连状态机的代际竞争条件
位置：
connection.ts:162-170
（
enqueueSync
）
描述：
syncChain
串行化了所有
syncTools
调用，但
isCurrent
检查和
disposers
赋值之间存在微小的窗口。虽然当前的单线程 Node.js 模型使得这个窗口在实践中不会被穿透，但如果未来引入 Worker Threads 或异步调度策略变更，
disposers = await syncTools(...)
的赋值可能与另一个并发的
enqueueSync
竞争。
影响：
理论上可能导致工具注册泄漏或重复注销。
当前设计在单线程下安全。建议在
enqueueSync
中添加代际版本号检查，确保只有最新代际的 sync 结果被采纳。代码注释应明确标注此假设。
中
R-MCP-04：全量工具同步的性能开销
位置：
tools.ts:143-193
（
syncTools
）
描述：
每次
ToolListChangedNotification
触发时，
syncTools
执行完整的两阶段替换：dispose 所有旧工具 → 注册所有新工具。对于拥有数百个工具的 MCP Server（如某些数据库 Server 暴露所有表/视图的 CRUD 工具），这意味着每个变更通知都会产生数百次
ctx.tools.register()
和 dispose 调用。
影响：
在高频变更场景下（如动态数据库 schema），可能导致工具注册表的瞬时不一致和性能抖动。
实现差异同步（diff-based sync）：比较新旧工具列表，仅注销移除的工具、仅注册新增的工具、更新变更的工具。需要维护上一代工具列表的快照。
中
R-MCP-05：Streamable HTTP 传输的安全头泄露
位置：
transport.ts:45-48
描述：
StreamableHTTPClientTransport
的
headers
配置直接传递给 HTTP 请求。如果配置文件中包含敏感的认证令牌（如
Authorization: Bearer ...
），这些令牌会以明文形式存储在
cordis.yml
中。DSH 没有提供 secrets 引用机制（如环境变量占位符）。
影响：
配置文件的泄露（如 git 提交失误）会导致 MCP Server 认证令牌暴露。
支持
$env:VAR_NAME
语法的环境变量引用，或集成 DSH 的
credentials
服务来管理敏感头。
3. ACP 适配层风险分析
严重
R-ACP-01：插件加载路径的系统性测试盲区（已知事故模式）
位置：
postmortem #0001
描述：
历史事故表明，
export default apply
会导致 Cordis Loader 的
unwrapExports
丢弃
inject
，使插件在无注入服务的 fiber 中运行。虽然此具体 bug 已修复，但根本原因——
手挂插件的测试无法验证真实加载路径
——是一个系统性风险。当前 ACP 的测试仍使用
ctx.plugin({ name, inject, apply })
手挂模式。
影响：
未来任何命名导出的变更（如意外添加 default export、遗漏 inject 声明）都可能在生产环境中崩溃，而测试全部通过。
确保至少一个 e2e 测试通过真实 Loader 加载 ACP 插件（已有
examples/acp-agent/tests/acp.e2e.ts
）。建议在 CI 中强制运行此 e2e。考虑添加 lint 规则禁止 namespace 插件同时导出 default。
高
R-ACP-02：结算逻辑的隐式时序依赖
位置：
index.ts:169-216
（
settleAfterQuiescence
）
描述：
结算依赖三个异步条件的顺序等待：
admissionDone
→
agent.whenIdle()
→
outputTail
。其中
session/event
处理器中的
event.data.turn === inflight.turn
检查在
agent/inbox/claimed
事件中设置
inflight.turn
。如果事件到达顺序异常（如 turn/end 在 inbox/claimed 之前到达），
endReason
不会被设置，结算会回退到
'cancelled'
。
影响：
在极端事件竞争下，成功的 prompt 可能被报告为 cancelled。
添加
turn/end
事件的去重和兜底逻辑。如果结算时
endReason
未设置但
messageQueued
为 true 且 agent 已空闲，应报告
end_turn
而非
cancelled
。
中
R-ACP-03：单 Prompt 槽位限制
位置：
index.ts:338-339
描述：
每个会话同时只允许一个 prompt 在飞行中。对于自动化客户端发送快速连续请求的场景，客户端必须等待每个 prompt 完全结算后才能发送下一个。这显著限制了吞吐量。
影响：
无法流水线化 prompt 处理，客户端利用率低。
考虑实现 prompt 队列（最多 N 个排队），或明确文档化此限制并建议客户端使用多个会话实现并发。
中
R-ACP-04：权限模型过于简单
位置：
index.ts:271-285
描述：
权限请求仅提供
allow-once
和
reject-once
两种选择。对于长时间运行的自动化任务（如代码重构），Agent 可能需要对同一工具进行数十次调用，每次都触发权限请求，严重降低自动化效率。
影响：
自动化客户端被迫在交互频率和安全性之间做痛苦权衡。
添加
allow-session
选项（本次会话内持续允许），并通过
approval/request
的
options
数组暴露，让客户端根据上下文选择。
低
R-ACP-05：连接关闭时的 AggregateError 消息膨胀
位置：
index.ts:496-506
描述：
quiesce()
在多个会话销毁失败时创建
AggregateError
，将每个失败的完整
errorChain()
嵌入消息。对于大量会话同时关闭的场景（如连接异常断开），错误消息可能极长。
限制聚合错误消息的长度（如截断到前 N 个失败），或将详细错误写入日志而非嵌入消息。
4. API 网关风险分析
严重
R-API-01：SRC 回退的 Function.prototype.toString() 解析脆弱性
位置：
gateway/src/index.ts:542-576
（
methodParameterNames
）
描述：
SRC 回退使用
Function.prototype.toString()
获取方法源码，然后通过字符串操作（
indexOf('(')
、
indexOf(')')
、
split(',')
）解析参数名。这种解析对以下场景脆弱：（1）代码压缩/混淆后参数名丢失；（2）TypeScript 编译后的解构参数；（3）装饰器元数据与实际签名不一致。虽然 SRC 仅在开发模式可用，但缺少明确的环境检查来确保这一点。
影响：
如果 SRC 在非预期的生产环境中激活（如未正确设置 NODE_ENV），参数解析错误可能导致方法调用行为异常。
添加显式的开发模式检查（如
process.env.NODE_ENV !== 'production'
或 DSH 专有的开发标志），在生产环境中完全禁用 SRC 路径。考虑使用
ts-morph
替代字符串解析。
高
R-API-02：查找提供者的竞态与重复恢复
位置：
remotes/src/agent-lookup.ts:136-197
描述：
agentFor()
使用
resumes
Map 去重并发恢复请求。但
finally { resumes.delete(sessionId) }
在恢复完成后立即删除条目——如果在删除后、Agent 尚未注册到
ctx.agents
之前有新请求到达，会触发第二次恢复尝试。虽然
fencedLiveAgent()
的最终检查提供了安全网，但恢复过程的非原子性仍是一个设计弱点。
影响：
极端并发下可能出现同一会话的重复恢复，导致资源浪费。
将
resumes.delete()
移到 Agent 确认注册到
ctx.agents
之后。或使用
ctx.agents
的注册事件作为恢复完成的信号。
中
R-API-03：Client 端 Remote 命名空间的内存泄漏风险
位置：
gateway/src/client/index.ts:289-321
（
createNamespace
）
描述：
每个 Remote 命名空间创建一个 Cordis 子插件（
ctx.plugin()
），其生命周期由
RemoteNamespaceHandle
管理。如果
disposeNamespace()
中的
namespace.service.empty
检查因方法移除和新方法添加的竞争而返回 false，命名空间可能永远不会被清理。
添加命名空闲超时机制：如果命名空间在一段时间内无活跃方法，自动触发清理。
中
R-API-04：JSON 安全性检查的性能开销
位置：
gateway/src/index.ts:640-673
（
assertJsonValue
）
描述：
每次 RPC 调用的入参和返回值都经过递归的 JSON 安全性检查（
assertJsonValue
），包括循环引用检测（
ancestors
Set）、原型链检查、Symbol 属性检查等。对于大型返回值（如包含数百个嵌套对象的列表），这个检查可能成为性能瓶颈。
对于已知安全的返回值路径（如严格描述符的 Schema 验证已通过），可以跳过 JSON 安全性检查。或添加深度限制避免过深的递归。
5. 跨协议系统性风险
高
R-SYS-01：缺乏统一的可观测性基础设施
描述：
三个协议适配层各自使用
ctx.logger
记录日志，但没有结构化的指标采集（延迟分布、错误率、吞吐量）和分布式追踪支持。MCP 的连接监督器记录了重连事件，ACP 记录了会话生命周期，API 网关记录了 RPC 失败——但这些日志格式不统一，无法关联分析。
影响：
生产环境中的跨协议问题（如"MCP 工具调用超时导致 ACP prompt 结算延迟"）难以定位。
引入统一的遥测接口（如
ctx.telemetry.record(metric, tags, value)
），在关键路径（工具调用、prompt 结算、RPC 调度）添加计时和计数。支持 OpenTelemetry 导出。
中
R-SYS-02：错误格式碎片化
描述：
MCP 使用
isError + text
，ACP 使用
RequestError(code, message)
，Typert 使用
TypertGatewayError(code, endpoint, message)
。三种格式的错误码命名约定、消息结构和因果链表示各不相同。跨协议调用链中的错误传播需要在每个边界进行格式转换，容易丢失上下文。
定义统一的
DshProtocolError
基类，包含
code
、
message
、
protocol
、
cause
四层结构。各协议适配层在边界处转换为统一格式。
中
R-SYS-03：图片处理管线的代码重复
描述：
MCP 的
tools.ts:379-391
（
decodeImage
）和 ACP 的
content.ts:47-60
（
decodeImage
）实现了几乎完全相同的图片解码逻辑：相同的
IMAGE_MEDIA_TYPES
数组、相同的
CANONICAL_BASE64
正则、相同的
Buffer.from
+ 回编码验证。这种重复违反了 DRY 原则，任何安全修复（如添加新的图片格式支持）都需要在两处同步修改。
将图片解码逻辑提取到
dsh-attachment
包中作为共享函数。MCP 和 ACP 适配层都依赖此包（已有
SaveImageAttachment
类型），可以自然地复用解码函数。
6. 安全评审
6.1 信任边界分析
边界
信任级别
验证措施
评估
MCP Server → Client
不可信
防御性字段访问、base64 验证、mimeType 白名单
良好
但缺少大小前置检查
ACP Client → Server
可信（编程客户端）
协议版本协商、内容类型验证、空提示拒绝
充分
Web UI → API Gateway
trusted-host
Connection RPC 信任检查、参数精确匹配
充分
API Gateway → Business
内部
Schema 验证、JSON 安全性检查、查找解析
充分
6.2 凭证管理
MCP 适配层的
transport.ts
使用
scrubbedParentEnv()
清理环境变量中的凭证模式（
API_KEY
、
AUTH_TOKEN
等），防止子进程继承敏感信息。这是良好的安全实践。但 Streamable HTTP 的
headers
配置中的凭证仍以明文存储在配置文件中（R-MCP-05）。
6.3 拒绝服务防护
MCP：
有
toolCallTimeoutMs
（默认 60s）和重连
maxAttempts
（默认 10）限制
ACP：
单 prompt 槽位天然限制了并发，
admissionController
支持取消
API：
依赖 Connection 层的请求超时，网关本身无独立限流
中
R-SEC-01：API 网关缺少请求限流
网关的
invoke()
方法没有并发限制或速率限制。一个恶意或失控的 Client 可以通过高频 RPC 调用耗尽 Host 资源。
在
dispatchRpc()
中添加可配置的并发限制（如信号量）和速率限制（如令牌桶）。
7. 可靠性与容错评审
7.1 故障模式分析
故障场景
MCP
ACP
API
连接断开
指数退避重连（10次）+ 稳定性窗口
有序关闭 + 会话清理
依赖 Connection 层
服务崩溃
代际隔离 + 工具注销
Agent 取消 + 全局 quiesce
服务不可用错误
请求超时
AbortSignal + 超时
admissionController abort
Signal 传递链
数据格式错误
占位文本 + 日志
AcpContentError 抛出
TypertGatewayError 抛出
资源耗尽
无前置检查
风险
单 prompt 槽位限制
无限制
风险
7.2 MCP 连接监督器的精妙设计
连接监督器是整个协议适配层中最精密的组件，值得特别肯定的设计包括：
稳定性窗口
：连接存活超过
maxDelayMs
后重置失败计数器，防止长期运行后的一次断连耗尽预算
代际隔离
：每个连接尝试产生独立的 Client 实例，旧代际的
onclose
信号不会干扰新代际
syncChain 串行化
：所有工具同步操作排入 Promise 链，防止交错执行
关闭信号等待
：
waitForClose()
有 5 秒超时，避免损坏的传输层楔死清理
这些设计使得 MCP 适配层在面对各种异常场景时表现出色，测试覆盖了 15+ 种故障路径。
低
R-REL-01：重连失败后的静默工具注销
当重连预算耗尽时，监督器注销所有工具并记录错误日志，但不会通知上层应用（如 Agent 的工具列表变更回调）。Agent 可能在不知情的情况下失去了 MCP 工具能力。
考虑在工具注销时触发一个自定义事件（如
mcp-client/server-lost
），允许上层应用做出响应。
8. 性能优化建议
8.1 MCP 工具调用的序列化开销
每次 MCP 工具调用经过
callToolUncached()
发送 JSON-RPC 请求，结果经过
extractText()
→
projectContent()
的完整转换管线。对于高频调用的工具（如文件读取），
projectContent()
中的
isRecord()
类型守卫和
switch
分支会产生可观的 CPU 开销。
优化：
对于纯文本结果（最常见的场景），可以添加快速路径跳过
projectContent()
的完整扫描。
8.2 API 网关的描述符解析缓存
resolveDescriptor()
每次调用都查询
ctx.typert.local
注册表。对于高频 RPC 调用，可以考虑在描述符不变期间缓存解析结果。
8.3 ACP 输出投递的串行化
outputTail
Promise 链确保了输出顺序，但也意味着每个助手消息块的附件读取是串行的。对于包含多张图片的回复，可以考虑并行读取图片但在组装时保持顺序。
8.4 Client 端 Remote 的方法查找
每次
ctx.remote.goals.create()
调用都经过 getter → 闭包 →
invokeMethod()
→
invoke()
的完整链路。getter 内部的
this.methods.get(method)
查找虽然 O(1)，但闭包创建和 Context 捕获的开销在高频调用下累积可观。
9. 可维护性与工程实践
9.1 积极方面
注释质量极高
：每个函数都有详细的 JSDoc，解释了设计决策和边界条件
测试覆盖充分
：MCP 有 1200+ 行测试（含 15+ 故障路径），ACP 有完整的 bridge/codec/content 测试
v8 ignore 标注
：对防御性代码和不可达路径使用
v8 ignore
标注，保持覆盖率指标的有效性
jscpd 抑制
：对有意的代码重复（如 MCP/ACP 的图片解码）使用
jscpd:ignore
标注
Invariant 伴生插件
：MCP 和 ACP 都有独立的
invariant.ts
，为未来的运行时不变量检查预留了扩展点
9.2 改进机会
低
R-MNT-01：ACP 的 inflight 状态对象过于复杂
SessionRecord['inflight']
包含 13 个字段，涵盖准入、队列、turn、结算和错误五个生命周期阶段。这个对象本质上是一个隐式状态机，但没有显式的状态枚举和转换图。新开发者理解
settleAfterQuiescence()
的逻辑需要跟踪多个字段的组合状态。
考虑将
inflight
重构为显式状态机（如
{ state: 'admitting', ... } | { state: 'queued', ... } | { state: 'settling', ... }
），使状态转换更清晰。
低
R-MNT-02：API 网关的 SRC 路径代码量占比过高
gateway/src/index.ts
中约 40% 的代码（
resolveSrcDescriptor
、
srcDescriptor
、
collectSrcClaims
、
methodParameterNames
等）服务于 SRC 回退路径。这些代码在生产环境中永远不会执行，但增加了维护负担和代码审查的认知负荷。
将 SRC 相关代码提取到独立的
src-fallback.ts
模块，通过条件导入在开发模式下加载。
10. 改进路线图
短期（1-2 Sprint）
优先级
改进项
风险编号
工作量
P0
MCP 图片解码添加 base64 长度前置检查
R-MCP-01
0.5 天
P0
API 网关 SRC 回退添加生产环境禁用检查
R-API-01
0.5 天
P1
提取共享的图片解码函数到 dsh-attachment
R-SYS-03
1 天
P1
ACP 结算添加 endReason 兜底逻辑
R-ACP-02
1 天
中期（3-6 Sprint）
优先级
改进项
风险编号
工作量
P2
统一错误格式（DshProtocolError）
R-SYS-02
3 天
P2
添加结构化遥测接口
R-SYS-01
5 天
P2
MCP 工具差异同步
R-MCP-04
3 天
P2
API 网关请求限流
R-SEC-01
2 天
P2
ACP 权限模型扩展（allow-session）
R-ACP-04
2 天
长期（架构演进）
方向
描述
流式 RPC
扩展 Typert 网关支持 server-streaming，使 Remote 方法可返回异步迭代器
MCP 资源桥接
实现
resources/list
、
resources/read
和
resources/subscribe
ACP 会话持久化
支持 ACP 客户端断线重连后恢复会话状态
共享连接健康服务
集中管理所有协议的连接状态和故障恢复策略
DeepSeek Harness 协议适配层架构评审报告 — 基于源码直接审查
生成日期：2026-08-29 | 共识别 23 项风险（3 严重 / 6 高 / 8 中 / 4 低 / 2 信息）