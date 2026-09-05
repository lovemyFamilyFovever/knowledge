---
title: "DeepSeek Harness 知识图谱"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 知识图谱"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 知识图谱
DeepSeek Harness 知识图谱
基于 DSH 官方文档全面提取 — 涵盖架构、概念、模块、数据流、配置、插件、用户旅程与API入口
核心概念
模块依赖
术语表
数据流
配置体系
插件能力
用户旅程
API入口
总结
目录
核心概念图谱
— Agent、Session、Scope、Context、Plugin、Tool、Skill、Plan、Goal 等
模块依赖图谱
— 子系统列表、依赖关系、层次图
术语表
— 中英文对照、全部术语定义
数据流图谱
— 用户输入、Agent处理、工具调用、模型请求流
配置体系图谱
— 配置分类、来源、作用域
插件能力图谱
— 内置插件、协作关系、外部接入
用户旅程图谱
— 新用户入门、开发者扩展、运维部署
API入口图谱
— CLI/Web/SDK入口与调用链
知识图谱总结
— 整体关系、关键路径、学习建议
一、核心概念图谱
1.1 核心概念定义
Agent（智能体）
中文：智能体
Agent 是 DSH 中最核心的运行时实体。每个 Agent 拥有一个唯一的
SessionId
，代表一个活跃的对话会话。Agent 由
ctx.agents
（AgentRegistry）管理，通过
ctx.agentLoop
（AgentLoop）驱动执行。Agent 的生命周期状态为
idle
（空闲）和
running
（运行中）。
Agent 提供
send()
、
followup()
、
steer()
、
inject()
四种消息投递方式，以及
cancel()
取消和
whenIdle()
等待空闲的操作。
ctx.agents
ctx.agentLoop
Session（会话）
中文：会话
Session 是一个
仅追加的事件日志
（append-only log），是 Agent 交互历史的
唯一真实来源
。LLM 消息历史从日志中
派生
（通过
deriveMessages()
），而非独立存储。每个
SessionEvent
包含单调递增的
seq
、时间戳和类型化载荷。
Session 支持12种事件类型：
turn/start
、
turn/end
、
step/start
、
step/end
、
user/message
、
assistant/chunk
、
assistant/message
、
tool/call
、
tool/result
、
steering/message
、
todo/write
、
request/header
。
ctx.sessions
Scope（作用域）
中文：作用域
Scope 是按 Agent 划分的注册单位。一项贡献（工具、提示词段、变量、限制、监听器）要么是
全局的
（对所有 Agent 可见），要么是
带作用域的
（归属于恰好一个 ScopeKey）。只有两层扁平结构：带作用域的注册不会向下继承给 subagent。
ScopeKey 是不透明的对象标识，harness 约定：活跃的 Agent 就是其自身 Scope 的 key。通过
scopeTarget(base, key)
构建路由载体。
库，无 ctx 键
Context（上下文）
中文：上下文
Context 是 Cordis 框架中的服务仓库。每个服务通过稳定的
ctx.<key>
（如
ctx.tools
、
ctx.llm
、
ctx.sessions
）声明自己；其他插件通过 key 查找服务，而非导入具体实现。Context 支持声明式依赖注入（
inject
），插件等待所需服务存在后才加载。
Plugin（插件）
中文：插件
在 Cordis 框架中，Plugin 是实现了 Service 接口的对象。它可以是带有可选
inject
和
apply(ctx)
字段的函数，也可以是
Service
子类。DSH 的每一部分都是插件，包括模型适配器、工具注册表、会话日志和 Agent Loop 本身。注册都是可逆副作用，卸载时自动撤销。
Tool（工具）
中文：工具
Tool 是面向模型的可调用能力。每个工具包含
ToolSchema
（模型可见的 schema）加上
execute
函数和可选的 UI 呈现回调。工具通过
ctx.tools
注册，支持作用域化注册、限制（restriction）和单调守卫（guard）。
工具执行流水线：
tools/pre-execute
→ 守卫 →
tools/execute
→
tools/post-execute
→
tools/result
。
ctx.tools
Skill（技能）
中文：技能
Skill 是可选的指令内容，不是会话事件。技能系统包含 Service Definition（
ctx.skills
）、本地文件系统 Provider（
dsh-skill-filesystem
）和 Consumer（
dsh-tool-skill
）。技能按优先级从项目目录、用户目录、捆绑目录等多级发现，支持模型调用和用户调用两种策略。
ctx.skills
Plan（计划模式）
中文：计划模式
Plan Mode 是按 Agent 记录的协作状态。激活时，每个模型请求包含部署级引导段落。Plan Mode 是
软引导
，与沙箱模式和审批策略独立。状态通过
plan/mode
会话事件持久化，支持恢复和 fork。通过
/plan
命令或
exit_plan_mode
工具控制。
ctx.planMode
Goal（目标）
中文：目标
Goal 是附着在现有会话上的持久完成目标。具有修订号演进的
active
/
paused
/
blocked
/
complete
阶段和 Goal Round 上限。Goal 是状态，不是调度器或独立对话。Goal Round 是为当前目标接纳的一次续行周期，具体化为一个由目标触发的轮次。
ctx.goals
Turn / Step / Round（轮次/步骤/回合）
中文：轮次 / 步骤 / 回合
Turn（轮次）
：会话中一次对已接纳输入的排空过程。
Step（步骤）
：一次模型请求加上它调用的工具；一个 Turn 包含零个或多个 Step。
Round（回合）
：承载一个 Turn 的外层策略迭代，如 Goal Round 或 Ralph Round。
Seam（能力接缝）
中文：能力接缝
Seam 是一种可替换能力，包含三种角色：Service Definition（声明接口）、Service Provider（实现接口）、Consumer（使用接口）。替换一个提供方就能改变整个产品。例如文件系统和进程提供方共享一个执行世界，指向远程沙箱就同时移动了 Bash、PTY 和 LSP。
Profile / Bundle（配置文件/组合包）
中文：配置文件 / 组合包
Profile
是存放在 Harness home 中的具名组装，列出叠放的组合包、树外插件和
cordis.patch.yml
。
Bundle
是 Cordis 配置项及其挂载代码的分发格式。
dsh-base
是每个 Profile 的第一层，
dsh-web-app
添加浏览器应用，
dsh-headless
添加无服务器运行器。
Subagent（子智能体）
中文：子智能体
Subagent 是 Agent 委派工作的子级。通过命名的提供方注册表（
ctx.subagents
）管理，支持多种后端：进程内 spawn、fork、ACP、Codex、Claude Code 等。支持一次性启动和可续行子 Agent 两种模式。可续行子 Agent 通过 Activation 管理器控制冷恢复和所有权图。
ctx.subagents
1.2 概念关系图
关系符号说明：
→
依赖/驱动
⊂
包含
↔
交互
⟹
创建/产生
源概念
关系
目标概念
说明
Cordis Framework
⟹
Context
Cordis 创建并管理 Context 服务仓库
Context
⊂
所有 Service
Context 包含所有注册的服务（ctx.*）
Plugin
→
Context
Plugin 通过 apply(ctx) 向 Context 贡献服务
Profile
⊂
Bundle
Profile 由多个 Bundle 按序叠加而成
Bundle
⊂
Plugin
Bundle 包含多个 Plugin 及其配置
AgentLoop
⟹
Agent
AgentLoop 创建并驱动 Agent
Agent
↔
Session
Agent 拥有 Session，Session 记录 Agent 历史
Agent
→
Scope
Agent 是其自身 Scope 的 key
Agent
⊂
AgentRegistry
Agent 注册在 ctx.agents 中
Turn
⊂
Session
Turn 是 Session 日志中的结构化区间
Step
⊂
Turn
Step 是 Turn 内的一次模型请求
Step
⟹
Tool Call
Step 的模型响应产生 Tool Call
Tool
→
ToolRegistry
Tool 注册在 ctx.tools 中
ToolRegistry
→
SystemPrompt
工具 schema 参与提示词组装
Agent
↔
Goal
Goal 附着在 Agent 的 Session 上
Agent
↔
Subagent
Agent 可创建和管理 Subagent
Agent
↔
Skill
Skill 为 Agent 提供可选指令
Agent
↔
Plan
Plan Mode 是 Agent 的协作状态
Session
→
Persistence
Session 通过 ctx.sessionPersistence 持久化
Seam
⊃
Service Definition
Seam 包含服务定义、提供方和消费方
Seam
⊃
Service Provider
Seam 包含一个或多个提供方实现
Seam
⊃
Consumer
Seam 包含消费方（通常是模型面对的工具）
二、模块依赖图谱
2.1 子系统完整列表
DSH 由 55+ 个子系统组成，按功能域分为以下类别：
类别
子系统
ctx 服务键
职责
核心骨架
core/session
ctx.sessions
仅追加的 SessionEvent 日志和内存存储
core/system-prompt
ctx.systemPrompt
提示词片段与工具 schema 组装
core/tools
ctx.tools
作用域化的工具注册表和执行流水线
core/agent
ctx.agents
Agent 接口、活跃注册表和 agent/* 事件
core/agent-loop
ctx.agentLoop
实现 Agent 接口的默认驱动器
core/scope
库，无键
按 agent 划分作用域的注册原语
core/agent-default-model
ctx.agentDefaultModel
默认模型选择
LLM 层
llm/llm
ctx.llm
消息与流式词汇表，适配器 seam
llm/token-meter
ctx.tokenMeter
不可变 token 测量
llm/compaction
ctx.compactionEngine
会话压缩引擎
llm/tool-result-pruner
ctx.toolResultPruner
无模型的工具结果裁剪
llm/llm-replay
-
LLM 重放适配器
持久化
session/session-persistence
ctx.sessionPersistence
持久化 seam：JSONL + SQLite 后端
session/session-query
ctx.sessionQuery
逻辑记录、语义过滤、全文搜索
session/session-title
ctx.sessionTitle
持久标题快照
session/session-reference
ctx.sessionReferenceResolver
跨会话引用
执行能力
shell/shell
ctx.shell
Bash 执行器 seam
subprocess
ctx.subprocess
子进程 seam
terminal
ctx.terminals
持久 PTY 终端
sandbox/sandbox
ctx.sandbox
进程沙箱 seam
code-runtime
ctx.codeRuntime
代码执行 seam
交互能力
interaction/commands
ctx.commands
人类命令注册表
interaction/user-questions
ctx.userQuestions
人类问答 seam
interaction/approval
ctx.approval
审批 seam
interaction/feedback
ctx.messageFeedback
消息反馈
plan/plan-mode
ctx.planMode
计划模式协作状态
扩展能力
subagent/subagent
ctx.subagents
子智能体 seam
skill/skill
ctx.skills
技能注册表
workflow/workflow
ctx.workflowEngine
工作流引擎
extensions
ctx.dynamicCordisRunner
动态插件运行时
Web 能力
web/web
ctx.web
Web 访问 seam
web-server
WebRoute
HTTP 载体
client-modules
dsh.client
Web 插件表
storage
ctx.storage
非会话存储
配置管理
settings
ctx.settings
用户设置 seam
credentials
ctx.credentials
凭据 seam
permission-presets
ctx.permissionPresets
权限预设层
其他
attachment
ctx.attachments
持久二进制附件存储
filesystem
ctx.fs
文件系统 seam
spill
ctx.spill
溢出存储 seam
2.2 依赖层次图
DSH 的模块按以下层次组织，从底层基础到顶层应用：
Layer 0 — 框架基础
Cordis Framework（插件框架、Context、事件系统、副作用管理）
dsh-brand
（品牌化 ID 类型）|
scope
（作用域原语）
Layer 1 — 核心骨架
session
→
system-prompt
→
tools
→
agent
→
agent-loop
这是驱动器脊柱，所有轮次流经这六个包
Layer 2 — LLM 与持久化
llm
（消息词汇表 + 适配器 seam）|
token-meter
|
compaction
session-persistence
（JSONL / SQLite）|
session-query
|
session-title
Layer 3 — 执行能力
subprocess
→
sandbox
→
shell
（bash/pwsh）|
terminal
|
code-runtime
filesystem
|
lsp
|
web
Layer 4 — 交互与扩展
commands
|
user-questions
|
approval
|
plan-mode
subagent
|
skill
|
workflow
|
extensions
|
goal
Layer 5 — 组合与应用
dsh-base
（模型适配器、工具、持久化、沙箱、设置、凭据、遥测）
dsh-web-app
（浏览器应用）|
dsh-headless
（一次性运行器）
agent-presets
（按会话的 Agent 组合）
2.3 核心包依赖关系
包
依赖
被依赖
scope
无（最底层库）
session, system-prompt, tools, agent
session
scope, llm
agent, agent-loop, persistence, query
system-prompt
scope, tools, llm
agent-loop
tools
scope, llm
agent-loop, 所有工具消费者
agent
session, scope
agent-loop, 所有插件
agent-loop
agent, session, system-prompt, tools, llm
组合包
llm
无（独立）
session, system-prompt, tools, agent-loop
subagent
agent, session, tools, llm
tool-subagent, workflow
shell
subprocess, sandbox
tool-bash, tool-pwsh
三、术语表
3.1 核心领域术语
Agent
智能体
DSH 中最核心的运行时实体，拥有 SessionId，由 AgentLoop 驱动
Session
会话
仅追加的事件日志，Agent 交互历史的唯一真实来源
Scope
作用域
按 Agent 划分的注册单位，两层扁平结构
Scope Key
作用域键
Scope 的不透明标识，按对象同一性比较；活跃 Agent 是自身 Scope 的 key
Agent Context (agent.ctx)
Agent 上下文
Agent 的带作用域上下文，注册既具有 scope 可见性，生命周期也绑定到该 scope
Scoped Dispatch
作用域过滤分发
关于某个 Agent 的活动的事件以该 Agent 的 carrier 进行分发
Shadowing
遮蔽
最具体者胜出的名称解析：带作用域的工具/片段/变量仅在该 scope 内替换同名全局对应项
Turn
轮次
会话中一次对已接纳输入的排空过程
Step
步骤
一次模型请求加上它调用的工具；Turn 包含零或多个 Step
Round
回合
承载一个 Turn 的外层策略迭代，如 Goal Round 或 Ralph Round
Seam
能力接缝
可替换能力，含 Service Definition + Provider + Consumer 三种角色
Service Definition
服务定义
拥有 ctx.key 和词汇类型的 Cordis Service
Service Provider
服务提供方
实现服务定义声明的接口
Consumer
消费方
使用服务的组件，通常是面向模型的工具
Profile
配置文件
存放在 Harness home 中的具名组装，列出叠放的 Bundle
Bundle
组合包
Cordis 配置项及其挂载代码的分发格式
Tool
工具
面向模型的可调用能力，包含 schema、execute 和 UI 回调
Skill
技能
可选的指令内容，从多级目录发现，不是会话事件
Goal
目标
附着在现有会话上的持久完成目标
Goal Round
目标回合
为当前目标接纳的一次续行周期，具体化为一个由目标触发的轮次
Goal Activation
目标激活
续行消费方接纳下一个 Goal Round 的进程本地权限
Human Command
人类命令
以斜杠开头的指令，由面向人类的适配器通过 ctx.commands 解释执行
Command Plane
命令平面
由 UI 适配器和命令插件负责的发现、解析、分发、取消与结果渲染机制
Plan Mode
计划模式
按 Agent 记录的协作状态，激活时每个模型请求包含引导段落
Subagent
子智能体
Agent 委派工作的子级，支持多种后端
Activation
激活
可续行子 Agent 的进程驻留期间，包含一个 AgentHandle
Ralph Loop
Ralph 循环
面向不可变目标的前台全新 Agent 工作流运行
Ralph Round
Ralph 回合
Ralph 循环中的一个全新子会话
Ralph Handoff
Ralph 交接
从一个 Ralph Round 传给下一个的规范化有界结构化报告
SessionEvent
会话事件
会话日志中的不可变条目，类型化判别联合
SessionHeader
会话头
独立于事件日志的持久化元数据
StreamChunk
流式块
适配器发出的原始流式协议
ToolSchema
工具 Schema
面向模型的工具描述字段
ToolDefinition
工具定义
注册表持有的完整工具：schema + execute + 回调
ContentBlock
内容块
消息中的类型化内容（text/reasoning/image/tool-call/tool-result）
Message
消息
不可变的角色/来源/内容值，投递、持久历史和模型请求共享
AgentHandle
Agent 句柄
拥有 Agent 加上其 disposer 的结构，只有持有者可拆卸
Inbox
收件箱
Agent 拥有的两个有序待处理消息列表（next-turn 和 next-step）
ToolGuard
工具守卫
作用域感知的最终调度前策略，只能拒绝不能允许
ToolRestriction
工具限制
每个 scope 对全局工具的过滤器
Branded ID
品牌化 ID
编译时品牌的字符串，不可互换（SessionId ≠ CallId）
deriveMessages()
派生消息
从会话日志投影出模型可见的消息历史
SandboxMode
沙箱模式
read-only / workspace-write / danger-full-access 三种文件效果策略
SessionPersistence
会话持久化
事件日志的持久化 seam，含 JSONL 和 SQLite 后端
AgentPreset
Agent 预设
按会话组合 Agent 的机制，决定工具和提示词
四、数据流图谱
4.1 用户输入 → Agent 处理 → 工具调用 → 结果返回
用户输入
(UI / CLI / SDK)
→
agent.followup(message)
/
agent.steer(message)
/
agent.inject(message)
→
Inbox
(next-turn / next-step 两个有序列表)
Turn 开始
(turn/start)
→
claim 领取 next-step 输入 + 一个 next-turn 消息
→
组装提示词段落 + 工具 schema
→
agent/pre-step
(waterfall: reject | enter)
Step 执行
(step/start)
→
追加 user/message 到日志
→
从日志派生模型历史 (deriveMessages)
→
agent/request
→
llm/stream
→
assistant/chunk*
→
assistant/message
工具调用
→
tool/call*
→
tools/pre-execute
(allow/deny/ask)
→
ToolGuard 单调守卫
→
tools/execute
(around-dispatch)
→
tools/post-execute
(accept/replace/block)
→
tool/result*
Step 结束
(step/end)
→
工具欠另一个请求，或 next-step 输入到达 → 领取 → 下一个 Step
Turn 结束判断
→
agent/turn-stopping
(serial: 数据决定)
→
如果有新 steering → 再执行一个 Step
→
否则 →
turn/end
4.2 模型请求 → Provider → LLM → 响应处理
模型请求组装
→
SystemPrompt.assemble(): 提示词段落 + 工具 schema + 变量插值
→
deriveMessages(): 从 SessionSurface 投影历史
→
组装 LlmCallConfig (provider, model, maxTokens, sampling params)
适配器选择
→
ctx.llm 根据 provider 路由查找注册的 LlmAdapter
→
agent/request waterfall 允许替换配置
流式响应
→
LlmAdapter.stream(messages, config, signal)
→
StreamChunk 序列:
    block-start → text-delta* → block-end
    block-start → reasoning-delta* → block-end
    block-start → tool-call-delta* → block-end
    usage → finish
响应组装
→
BlockAssembler 从 chunk 组装 ContentBlock[]
→
assistant/message 写入 Session 日志
→
派发 tool/call 事件给工具注册表
错误恢复
→
agent/request-error waterfall
→
监听器可返回 { kind: 'retry' } 拥有恢复权
→
默认 undefined 使失败终态
4.3 文件操作 → 沙箱 → 终端 → 输出
工具注册
→
dsh-tool-fs (Read/Write/Edit/Glob/Grep)
→
dsh-tool-bash (bash 命令)
→
dsh-tool-terminal (持久终端)
策略解析
→
ctx.sandboxPolicy.resolve(session, mode?)
→
SandboxExecutionPolicy { mode, workspaceRoot, sessionId }
沙箱包装
→
ctx.sandbox (仅限 confined 模式)
→
ConfinedArgv: 包装后的命令行
→
后端: Linux bwrap/Landlock | macOS Seatbelt | Windows ACL
进程执行
→
ctx.subprocess.spawn(spec)
→
管理 DSH_* 环境变量
→
输出捕获 + 超时控制
结果返回
→
SubprocessOutcome { exitCode, stdout, stderr }
→
工具渲染 (presentCall / presentResult)
→
tool/result 写入 Session 日志
五、配置体系图谱
5.1 配置分类
类别
配置项
说明
模型配置
provider
注册的模型提供方路由
model
提供方拥有的模型 ID
maxTokens
每次请求最大输出 token 数
reasoning effort / sampling params
推理强度和采样参数
Agent 配置
AgentOptions (provider, model, maxTokens)
Agent 级别的模型选择
AgentPreset 组合文件
按会话的工具和提示词组合
persona
部署级人格（系统提示词的一部分）
工具配置
ToolPresentationMode
工具呈现模式
ToolRestriction
每个 scope 的工具过滤器
toolBash config
Bash 工具配置
maxParallelToolCalls
最大并行工具调用数
安全配置
SandboxMode
沙箱文件效果策略
ApprovalPolicy
审批策略
PermissionPresets
权限预设层
持久化配置
persistenceRoot
会话持久化目录
packChunks
是否打包增量 chunk
persistenceCompression
JSONL 压缩格式
storage backend
存储后端（JSON / SQLite）
交互配置
workspaceContext
工作区上下文控制
skills config
技能注册和发现配置
goals config
目标系统配置
5.2 配置来源与层次
Layer 1 — 默认值
每个插件的内置默认配置
Layer 2 — Bundle 配置
dsh-base / dsh-web-app / dsh-headless 的 cordis.yml
Layer 3 — Profile 配置
Profile 的 cordis.patch.yml
Layer 4 — Home 级配置
Harness home 目录的 cordis.patch.yml
Layer 5 — 运行时覆盖
--patch overlay | 环境变量 | Settings UI
配置通过
cordis.yml
声明，每个条目有
config:
块。层级叠加顺序：Bundle → Profile patch → Home patch →
--patch
overlay。可通过
dsh --profile web --dump-config
查看实际启动的配置树。
5.3 配置作用域
作用域
说明
示例
进程全局
影响整个 DSH 进程
provider 路由、LLM 适配器
Profile 级
影响一个 Profile 下所有 Agent
dsh-web / dsh-headless 差异
Agent Preset 级
影响通过该 Preset 组合的 Agent
工具集、人格、技能
Session 级
影响单个会话
沙箱模式、工作区目录
Scope 级
影响单个 Agent 的 scope
scope-local 工具注册、限制
六、插件能力图谱
6.1 内置能力接缝（Capability Seams）
能力
Service Definition
已知 Provider
Consumer（工具）
LLM 适配器
ctx.llm
dsh-llm-deepseek, dsh-llm-replay
agent-loop 内部
Shell 执行
ctx.shell
dsh-bash-local, dsh-bash-sandbox
dsh-tool-bash, dsh-tool-pwsh
文件系统
ctx.fs
本地, dsh-fs-e2b, dsh-fs-sandbox
dsh-tool-fs (Read/Write/Edit/Glob/Grep)
子进程
ctx.subprocess
dsh-subprocess-local, dsh-subprocess-e2b
shell, lsp 等
沙箱
ctx.sandbox
dsh-sandbox-local (bwrap/Seatbelt/ACL)
bash-sandbox, pwsh-sandbox
Web 访问
ctx.web
Exa, Perplexity, DeepSeek(搜索); HTTP(抓取)
dsh-tool-web (web_search/web_fetch)
子智能体
ctx.subagents
in-process, fork, ACP, Codex, Claude Code, SDK
dsh-tool-subagent
工作流
ctx.workflowEngine
dsh-workflow-worker-thread
dsh-tool-workflow
会话持久化
ctx.sessionPersistence
JSONL, SQLite
session 事件流
设置
ctx.settings
dsh-settings-file
UI 和 Agent 配置
凭据
ctx.credentials
dsh-credentials-local
API key 管理
审批
ctx.approval
UI 适配器
tools/pre-execute 的 ask 决策
用户问答
ctx.userQuestions
UI 适配器
dsh-tool-ask-user
技能
ctx.skills
dsh-skill-filesystem, dsh-skill-badge
dsh-tool-skill
终端
ctx.terminals
dsh-terminal-bash
dsh-tool-terminal
附件
ctx.attachments
dsh-attachment-local
图像处理
代码运行
ctx.codeRuntime
各 Code Mode 实现
run_code 工具
LSP
ctx.lsp
dsh-lsp-stdio
代码导航
会话遥测
ctx.sessionTelemetry
dsh-session-telemetry-otel
监控
6.2 插件协作关系
DSH 的插件通过 Cordis 事件系统协作。关键协作链路：
协作场景
参与插件
协作机制
工具执行
tools → approval → sandbox → shell → subprocess
tools/pre-execute waterfall → ctx.sandbox 包装 → ctx.subprocess.spawn
模型调用
agent-loop → system-prompt → llm → token-meter
agent/request waterfall → ctx.llm.stream → token 计量
会话持久化
session → session-persistence → session-query
session/event emit → 异步写入 → session/flush checkpoint
子智能体委派
agent → subagent → scope → session
创建子 Agent → 继承父 scope → 独立 Session
技能加载
skills → skill-filesystem → system-prompt
技能发现 → 按优先级合并 → 注入提示词
目标驱动
goal → agent → commands
goal/changed → agent 轮次续行 → /goal 命令控制
计划模式
plan-mode → system-prompt → commands
plan/mode 事件 → 提示词段注入 → /plan 命令
6.3 外部插件接入点
接入方式
说明
典型场景
Cordis Plugin
实现 Service 接口，通过 cordis.yml 声明
自定义 LLM 适配器、工具、存储后端
Agent Preset
声明式 Agent 组合文件
不同的工具集、人格、技能组合
Bundle
Cordis 配置行 + 挂载代码
功能分发和组合
Dynamic Cordis Plugin
运行时通过 ctx.dynamicCordisRunner 定义
模型创建的扩展插件
MCP Server
通过 MCP 协议接入外部工具
Chrome DevTools、飞书等
Hook Bridge
通过 hook 协议桥接外部钩子
Claude Code / Codex 钩子
七、用户旅程图谱
7.1 新用户入门路径
第 1 步：安装与启动
→
安装 DSH CLI
→
运行
dsh --profile web
启动 Web UI
→
命令打印 URL，在浏览器中打开
第 2 步：配置模型
→
打开 Settings → Models
→
输入 DeepSeek API Key 或其他提供商密钥
→
保存后立即可用，无需重启
第 3 步：选择工作区
→
点击 "Choose workspace"
→
添加项目目录并选中
→
会话编写器变为可用
第 4 步：执行任务
→
创建会话并发送提示
→
Agent 读写文件、运行命令、委派工作
→
Web UI 在需要审批时询问用户
第 5 步：进阶使用
→
配置更多模型提供方
→
使用 /plan 命令进入计划模式
→
使用 Goal 管理长期目标
→
使用 Subagent 委派复杂任务
7.2 开发者扩展路径
入门：了解架构
→
阅读 architecture.md + cordis-primer.md
→
理解 Plugin/Context/Service/Event 模型
→
运行 Cordis Tutorial (7 个章节)
第 1 级：添加简单工具
→
使用 defineTool DSL 定义工具
→
通过 ctx.tools.register() 注册
→
工具自动出现在模型的工具列表中
第 2 级：添加 LLM 适配器
→
实现 LlmAdapter 接口
→
通过 ctx.llm 注册适配器
→
支持新的模型提供商
第 3 级：添加完整包
→
创建新的 npm 包
→
声明 dsh 字段
→
编写 cordis.yml 配置
第 4 级：创建能力接缝
→
设计 Service Definition
→
实现 Service Provider
→
创建 Consumer 工具
第 5 级：创建 Agent Preset
→
编写 Preset 组合文件
→
定义工具集、人格、技能
→
通过 ctx.agentPresets 管理
7.3 运维部署路径
选择部署模式
→
Web 模式 (dsh-web-app): 浏览器 UI + HTTP 服务器
→
Headless 模式 (dsh-headless): 无服务器一次性运行
→
ACP 模式: Agent Client Protocol 集成
配置管理
→
编写 cordis.patch.yml 自定义配置
→
配置模型提供商和 API Key
→
设置沙箱策略和审批策略
持久化配置
→
选择 JSONL 或 SQLite 后端
→
配置持久化目录
→
设置压缩策略
监控与维护
→
配置会话遥测 (OTel)
→
监控 Agent 状态和错误
→
管理会话生命周期
八、API入口图谱
8.1 CLI 命令入口
命令
说明
调用链
dsh
启动 DSH（默认 Web 模式）
app-boot → Profile 加载 → Bundle 叠加 → Agent 创建
dsh --profile web
使用 web Profile
dsh-base + dsh-web-app
dsh --profile headless
使用 headless Profile
dsh-base + dsh-headless
dsh --dump-config
打印实际配置树
解析所有层 → 输出 cordis 条目
dsh --patch overlay.yml
叠加额外配置
在所有层之上应用 patch
/plan
进入计划模式
ctx.planMode.set(active) → 提示词注入
/goal
目标管理
ctx.goals 创建/编辑/暂停/恢复目标
/clear
清除会话
ctx.sessions 创建新会话
8.2 Cordis 服务 API 入口
服务
关键方法
说明
ctx.agents
create(), resume(), get(), list(), roots()
Agent 生命周期管理
ctx.agentLoop
create(), createAgent(), resume()
Agent 工厂和驱动器
ctx.sessions
create(), prepare(), enter(), flush(), fork(), get()
Session 存储管理
ctx.tools
register(), restrict(), guard(), execute(), schemas()
工具注册和执行
ctx.llm
register() (适配器注册)
LLM 适配器注册
ctx.systemPrompt
section(), context(), tools(), variable()
提示词组装
ctx.goals
create(), edit(), pause(), resume(), complete(), disarm()
目标管理
ctx.skills
list(), get(), register()
技能发现和加载
ctx.subagents
start(), startContinuable(), followup(), interrupt()
子智能体管理
ctx.commands
register(), list(), dispatch()
人类命令管理
ctx.web
search(), fetch()
Web 搜索和抓取
ctx.shell
resolve(), run(), start()
Shell 命令执行
ctx.settings
get(), set(), commit()
用户设置管理
ctx.workflowEngine
start()
工作流执行
ctx.agentPresets
list(), resolve(), mount(), composeFrom()
Agent 预设管理
8.3 Agent 事件 API
事件
分发模式
说明
agent/created
emit
Agent 发布后通知
agent/disposed
emit
Agent 离开注册表
agent/session-start
emit
会话生命周期开始
agent/status
emit
Agent 状态变化 (idle ⇄ running)
agent/pre-step
waterfall
拒绝或替换进入步骤的消息
agent/request
waterfall
替换冻结的调用配置
agent/request-error
waterfall
处理失败的模型请求
agent/turn-stopping
serial
轮次即将关闭
agent/error
emit
步骤或轮次错误
agent/inbox/*
emit
收件箱变化（inserted/claimed/discarded）
8.4 工具事件 API
事件
分发模式
说明
tools/pre-execute
waterfall
调度前 allow/deny/ask 决策
tools/execute
waterfall
around-dispatch 包装器
tools/post-execute
waterfall
接受/替换/阻断结果
tools/result
emit
观察冻结的最终结果
tools/change
emit
工具注册变化通知
tools/code-dispatch-log
waterfall
Code Mode 子调度日志
九、知识图谱总结
9.1 整体关系总图
DSH 的架构可以用一句话概括：
Cordis 插件框架驱动的、事件源化的 Agent 系统，通过能力接缝实现完全可替换的模块化设计。
核心驱动链：
Cordis Framework → Context (服务仓库) → Plugin (贡献服务) → AgentLoop (驱动器) → Agent → Session (事件日志) → Turn → Step → LlmAdapter (模型调用) → Tool (工具执行) → 结果写回 Session
三大支柱：
事件源化会话
（Session）：所有状态从仅追加日志派生，保证可重放、可 fork、可持久化
能力接缝
（Seam）：每个能力三角色分离（定义/提供方/消费方），实现完全可替换
作用域化注册
（Scope）：两层扁平结构，per-agent 定制工具和提示词
设计哲学：
没有特权内核：所有功能都是插件，包括 Agent Loop 本身
注册即副作用：通过 ctx.effect() 安装，卸载时自动撤销
模型可见即已记录：到达模型请求的一切必须能从日志重建
替换一个提供方改变整个产品：Seam 设计的核心价值
9.2 关键路径
路径
涉及模块
重要性
Agent 创建 → 会话建立 → 首次提示词组装
agent-loop → session → system-prompt
最高
用户输入 → Inbox → Turn → Step → LLM 调用
agent → inbox → llm
最高
模型响应 → 工具调用 → 执行 → 结果写回
tools → shell/fs/subagent → session
最高
Session 事件 → 持久化 → 恢复/fork
session → persistence → fork
高
Scope 注册 → 提示词组装 → 工具可见性
scope → system-prompt → tools
高
Agent Preset → 组合 → 工具/提示词定制
agent-presets → scope → tools
中
Goal 创建 → 轮次驱动 → 自动续行
goal → agent → turn
中
9.3 学习建议
推荐学习顺序
第 1 周：基础概念
阅读
cordis-primer.md
— 理解 Plugin、Context、Service、Event 四大概念
完成
cordis-tutorial
7 个章节 — 动手实践 Cordis 框架
阅读
architecture.md
— 理解 DSH 整体架构
第 2 周：核心子系统
阅读
subsystems/session.md
— 理解事件源化会话
阅读
subsystems/core.md
— 理解 Agent 创建和驱动
阅读
subsystems/tools.md
— 理解工具注册和执行流水线
阅读
subsystems/scope.md
— 理解作用域化注册
第 3 周：能力接缝
阅读
capability-seams.md
— 理解 Seam 设计模式
阅读
subsystems/llm-streaming.md
— 理解 LLM 适配器
阅读
subsystems/shell.md
+
sandbox.md
— 理解执行能力
阅读
subsystems/subagent.md
— 理解子智能体
第 4 周：实践扩展
阅读
cookbook/
目录 — 按指南添加工具、适配器、包
阅读
user/develop/
— 插件开发实践
研究
agent-lifecycle.md
和
tool-execution-pipeline.md
— 深入理解生命周期
DSH 知识图谱 — 基于 E:\chen\code\deepseek-harness/docs/ 目录文档全面提取
生成时间：2026-08-29 — 涵盖 55+ 子系统、100+ 核心概念、200+ API 入口