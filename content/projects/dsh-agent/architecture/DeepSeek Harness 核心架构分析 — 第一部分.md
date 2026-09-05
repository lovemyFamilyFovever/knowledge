---
title: "DeepSeek Harness 核心架构分析 — 第一部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 核心架构分析 — 第一部分
DeepSeek Harness 核心架构分析
第一部分：模块职责与边界、核心类清单、Agent 执行循环
1. 模块职责与边界
1.1 包的单一职责
packages/core/ — Agent 运行时内核
core
包群是整个 Harness 的"大脑"，由 7 个子包组成，每个子包负责 Agent 运行时的一个正交维度：
子包
职责
ctx
键
core/session
事件溯源的会话日志：追加式
SessionEvent
日志、内存存储、模型消息历史派生
ctx.sessions
core/agent
Agent 接口定义、活跃 Agent 注册表、事件派发器以及 inbox 投影
ctx.agents
core/agent-loop
实现 Agent 接口的默认驱动器
ReactLoopAgent
，以及 Agent 工厂服务
ctx.agentLoop
core/scope
按 Agent 划分作用域的注册原语，纯库
—
core/tools
作用域化的工具注册表以及 pre/execute/post 三阶段执行流水线
ctx.tools
core/system-prompt
提示词片段与工具 schema 的组装引擎
ctx.systemPrompt
core/agent-default-model
默认模型选择逻辑
—
packages/session/ — 持久化与投影
子包
职责
session-persistence
SessionPersistence
抽象服务定义以及
PersistenceCoordinator
写路径协调器
session-persistence-jsonl
JSONL 格式的持久化后端实现（支持 zstd 压缩）
session-persistence-sqlite
SQLite 格式的持久化后端实现
session-projection
会话投影注册表
session-projection-cache
投影缓存（增量计算优化）
session-title
/
session-title-llm
会话标题服务及 LLM 生成策略
session-stats
会话统计投影（token 计量等）
session-telemetry
遥测与 OpenTelemetry 集成
session-checkpoint-policy
检查点策略（何时触发 flush）
packages/context/ — 运行时上下文注入
子包
职责
agent-instructions
加载
AGENTS.md
等工作区指令文件，在首个请求前进入持久上下文
file-reference
/
file-reference-local
文件引用解析服务
session-reference
会话引用解析（跨会话引用）
time-context
请求时钟上下文注入（时间戳、时区、耗时）
tmux-context
tmux 终端上下文注入
1.2 包之间的依赖方向
依赖关系严格遵循
单向依赖、接口隔离
的原则：
context/*  ──→  core/agent (Agent, PreStepDecision)
                  ↑
session/*  ──→  core/session (Session, SessionEvent, SessionId)
                  ↑
core/agent-loop  ──→  core/agent + core/session + core/scope + core/system-prompt + core/tools
core/agent       ──→  core/session + core/scope
core/tools       ──→  core/agent + core/session + core/scope + core/code-runtime
core/scope       ──→  (无内部依赖，纯库)
core/session     ──→  (无内部依赖，基础层)
关键设计点：
core/session
是最底层，不依赖任何其他
core
子包
core/scope
也是底层库，只依赖外部的
@deepseek-ai/cordis
core/agent-loop
是最高层，依赖几乎所有
core
子包
session/*
持久化包只依赖
core/session
context/*
只依赖
core/agent
的接口类型
1.3 公共接口 vs 内部实现
公共接口
：
Session
、
SessionStore
、
Agent
（接口）、
AgentRegistry
、
AgentLoop
、
ToolRuntime
、
Scope
、
ScopedLayers
、
Inbox
、
SessionPersistence
内部实现
：
ReactLoopAgent
（具体驱动器类）、
FactoryOwnership
（生命周期管理）、
RuntimeContextProjection
（运行时上下文投影）、
SurfaceManager
（表面管理器）
2. 核心类/接口清单
2.1 core/session 包
类/接口
一句话职责
关键方法
Session
事件溯源的追加式会话日志，是整个系统模型上下文的唯一来源
append()
,
deriveMessages()
,
requestHeader()
,
surface
SessionStore
内存会话存储服务（
ctx.sessions
），管理 Session 的生命周期
create()
,
prepare()
,
enter()
,
announce()
,
fork()
,
flush()
SessionId
品牌化字符串类型，标识一个 Session
构造函数
SessionHeader
不可变的会话元数据（版本、ID、创建时间、工作目录、血统）
纯数据接口
SessionEventMap
会话事件类型的完整词汇表（可扩展）
联合类型
SessionPreparation
未发布的会话准备包装，支持
using
语义的自动释放
create()
,
[Symbol.dispose]()
2.2 core/agent 包
类/接口
一句话职责
关键方法
Agent
（接口）
Agent 的公共运行时接口，暴露会话、inbox、状态和控制方法
send()
,
followup()
,
steer()
,
inject()
,
cancel()
,
whenIdle()
AgentRegistry
活跃 Agent 注册表服务（
ctx.agents
），维护发起者作用域链
create()
,
resume()
,
register()
,
withInitiator()
AgentFactory
（接口）
Agent 创建工厂的抽象接口
createAgent()
,
resume()
AgentHandle
拥有的 Agent 加上其析构器的句柄
agent
,
dispose()
AgentEventDispatch
熔合了 Agent 主体和作用域载体的事件派发器
emit()
,
serial()
,
waterfall()
Inbox
Agent 持久化 inbox 事件的增量投影
splice()
,
claim()
,
clear()
2.3 core/agent-loop 包
类/接口
一句话职责
关键方法
ReactLoopAgent
Agent 接口的默认实现，驱动一个 Session 经历 turn/step 边界
send()
,
followup()
,
steer()
,
cancel()
,
whenIdle()
AgentLoop
Agent 工厂服务（
ctx.agentLoop
），负责创建、恢复和生命周期管理
create()
,
createAgent()
,
resume()
FactoryOwnership
工厂级别的所有权管理，跟踪活跃 Agent 和启动任务
track()
,
dispose()
,
waitWhileActive()
2.4 core/scope 包
类/接口
一句话职责
关键方法
Scope
（接口）
一个已铸造的注册作用域及其静默析构边界
ctx
,
dispose()
,
rawDispose
ScopedLayers
管理全局和精确作用域层的容器
effect()
,
peek()
,
chainLayers()
,
merge()
NamedEntries
带重复诊断的命名条目表
insert()
,
get()
,
has()
AnonymousEntries
带独立注册标识的匿名条目表
append()
3. Agent 执行循环
3.1 主循环实现
Agent 的主循环实现在
ReactLoopAgent
（
packages/core/agent-loop/src/agent.ts
）中，采用经典的
ReAct（Reasoning + Acting）模式
：
kick() → 循环调用 turn() 直到无待处理消息
  turn() → 开启 turn/start，循环调用 preStep + step
    preStep() → 组装系统提示词 + 声明工具 → agent/pre-step waterfall
    step() → 构建请求 → llm.stream → 收集响应 → 执行工具调用
  turn() → 关闭 turn/end
核心驱动逻辑在
kick()
方法中：
private async kick(): Promise<void> {
  try {
    while (await this.turn()) {}  // 持续驱动直到无待处理消息
  } catch (_error) {
    // 失败和取消在驱动器边界被遏制
  } finally {
    if (this.phase.kind === 'running') {
      const { turn, wakeRequested } = this.phase
      this.setPhase({ kind: 'idle', lastTurn: turn })
      if (wakeRequested && this.inbox.hasPending) this.wakeDriver()
    }
  }
}
3.2 思考→规划→执行→观察的流转
阶段一：思考（Pre-Step 决策）
从 inbox 领取目标批次消息（
inbox.claim()
）
组装系统提示词（
ctx.systemPrompt.assemble()
）
渲染上下文片段，生成运行时上下文快照
通过
agent/pre-step
waterfall 让插件改写或拒绝
阶段二：规划（请求构建）
从会话日志恢复持久化的请求头
通过
agent/request
waterfall 让插件替换调用配置
调用
ctx.llm.prepareCall()
解析适配器和默认值
比较头信息变化，按需记录
request/header
事件
阶段三：执行（模型调用 + 工具执行）
调用
llm.stream()
发起流式请求
逐 chunk 收集响应，记录
assistant/chunk
事件
使用
BlockAssembler
组装完整消息
有工具调用时执行
executeToolCalls()
阶段四：观察（工具结果 + Inbox 状态）
工具结果记录为
tool/result
事件
如果工具产生新的上下文，注入到 inbox 的
next-step
检查
concluded
标记决定是否继续
3.3 错误处理和重试机制
五层错误防护体系：
层一：信号中断
— 每个操作都检查
signal.throwIfAborted()
，确保取消可以及时生效
层二：请求错误 waterfall
—
agent/request-error
事件允许插件决定是否重试
层三：轮次边界错误
— 标准化为
LlmFailure
并记录为
turn/end
的
error
原因
层四：驱动器边界
—
kick()
方法的 catch/finally 确保 phase 转换和 wake 检查
层五：工厂级安全网
—
FactoryOwnership
跟踪所有活跃 Agent 的析构，在工厂卸载时中止所有活跃操作
DeepSeek Harness 核心架构分析 — 第一部分 | 生成日期：2026-08-29