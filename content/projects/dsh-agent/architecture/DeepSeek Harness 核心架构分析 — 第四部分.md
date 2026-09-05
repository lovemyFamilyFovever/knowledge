---
title: "DeepSeek Harness 核心架构分析 — 第四部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 核心架构分析 — 第四部分
DeepSeek Harness 核心架构分析
第四部分：工具执行流水线与系统提示词组装
10. 工具执行流水线（Tool Execution Pipeline）
10.1 工具注册与定义
工具通过
ToolDefinition
接口注册到
ctx.tools
（
ToolRuntime
服务）。每个工具定义包含：
字段
类型
说明
name
string
工具名称（模型可见）
description
string
工具描述（模型可见）
parameters
JsonSchemaNode
JSON Schema 参数定义（模型可见）
output
ToolOutputDefinition
强制的规范化输出声明
execute
(args, exec) => Promise<unknown>
执行函数
finalizeContent
(exec, result) => ContentBlock[]
最后一英里内容变换
timeoutMs
number
协作超时预算（不发送给模型）
isConcurrencySafe
(args) => boolean
并行安全分类器
presentCall
(args) => ToolCallView
UI 挂起状态展示
presentResult
(args, result) => ToolResultView
UI 完成状态展示
工具注册是作用域化的：通过
agent.ctx
注册的工具只对该 Agent 可见，全局注册对所有 Agent 可见。
10.2 三阶段执行流水线
工具执行遵循
tools/pre-execute → tools/execute → tools/post-execute
三阶段流水线：
↓
模型输出 tool-call
↓
tools/pre-execute
— 审批和守卫（allow / deny / ask）
↓
tools/execute
— 围绕式中间件（超时、重试、指标）
↓
工具体执行
— execute(args, exec)
↓
tools/post-execute
— 结果后处理（accept / replace / block）
↓
output.render()
— 规范化投影为模型可见内容
↓
session.append('tool/result')
— 记入会话日志
pre-execute 阶段
审批和守卫。监听器可以允许（
next()
）、拒绝或请求用户审批。这是安全策略的第一道门。
execute 阶段
围绕式中间件。监听器可以包装执行（添加超时、重试、指标），但不能阻止执行。注册表重新融合调用者信号，确保包装器不能脱离取消。
post-execute 阶段
结果后处理。监听器可以接受、替换或阻止结果。错误结果也到达此瀑布。
10.3 并行调度器
工具调用的并行调度在
executeToolCalls()
中实现，采用
有界滚动池
模式：
调度模式
parallel
：可与其他调用重叠，使用有界滚动池
exclusive
：独占执行，形成排序屏障
async function runGroup(ctx, turn, step, group, mode, signal, acceptContext) {
  const { maxParallelToolCalls } = ctx.agentLoop.config
  // 并行池：最多 maxParallelToolCalls 个同时执行
  while (!aborted && nextToStart < group.length && inFlight.size < maxParallelToolCalls) {
    await startCall(nextToStart)
    nextToStart++
    await commitReady()  // 按模型顺序提交已完成的结果
  }
  // 等待飞行中的调用完成，补充新调用
  while (inFlight.size > 0) {
    const settledIndex = await Promise.race(inFlight.values())
    inFlight.delete(settledIndex)
    await commitReady()
    await fillPool()
  }
}
关键设计点：
模型顺序保证
：结果按模型输出顺序提交（
committed
只跨连续的已完成 slot 推进）
重新分类
：在每次提交后重新读取后续调用的模式，允许注册表变更创建屏障
取消处理
：已开始的调用等待完成，未开始的调用记录合成错误结果
调度器失败
：停止新调度，排空已开始的调度，不伪造结果
10.4 Code Mode（代码模式）
当工具配置为
mode: 'code'
时，模型只能调用
run_code
工具。其他工具通过 SDK 在代码程序内部调用：
模型 → run_code(program) → Code Runtime → SDK 调用 → 其他工具
                                              ↓
                                    tool/code-dispatch-start (日志)
                                    tool/code-dispatch (日志)
10.5 工具结果的规范化输出
每个工具必须声明
output
字段，包含 JSON Schema 验证和纯投影函数：
interface ToolOutputDefinition {
  schema: JsonSchemaNode        // 强制的 JSON Schema
  render(args, value): ContentBlock[]  // 纯投影：值 → 模型可见内容
  presentationMeta?(args, value): JsonValue  // 可选的 UI 展示元数据
}
11. 系统提示词组装（System Prompt Assembly）
11.1 组装架构
SystemPrompt
服务（
ctx.systemPrompt
）管理提示词的四种贡献类型：
贡献类型
注册方法
说明
Section
section()
系统提示词的有序片段
Context
context()
动态运行时上下文（用户消息角色）
Tools
tools()
工具 schema 提供者
Variable
variable()
{{name}}
模板变量
每种贡献都通过
ScopedLayers
管理，支持全局和作用域化的注册。作用域条目遮蔽同名全局条目。
11.2 Section 顺序约定
order: -100       →  harness:identity（"You are an AI agent powered by DeepSeek Harness."）
order: -99..-1    →  其他负序号片段
order:    0       →  deployment:persona（部署者定义的角色）
order:   1..99    →  通用片段
order:   99       →  Code Mode collapse 声明
order: 100..199   →  每个工具的指导片段
order: 200+       →  其他片段
11.3 组装流程
assemble()
方法的完整流程：
收集作用域链层
合并变量（全局 → 祖先 → 最近作用域，近者胜）
合并 Section（同名遮蔽）
合并 Context
收集工具 schema（全局 + 作用域提供者）
应用
toolOrder
排序
运行
system-prompt/assemble
waterfall
如果有 complete section，恢复为唯一片段
如果运行时上下文被抑制，清空 contexts
11.4 变量插值
变量使用
{{variable_name}}
语法，支持严格的验证：
变量名必须匹配
[a-z][a-z0-9_]*
未注册的变量会抛出错误
值为
undefined
的变量会抛出错误
{{
后没有
}}
的情况被视为字面文本
替换后的值不会被再次扫描
// 变量注册示例（在 AgentLoop 构造函数中）
ctx.systemPrompt.variable('provider', context => context.agent?.options.provider)
ctx.systemPrompt.variable('model', context => context.agent?.options.model)
ctx.systemPrompt.variable('cwd', context => context.agent?.session.header.cwd)
11.5 complete Section 机制
当一个 Section 标记
complete: true
时：
组装仍然运行完整的协作瀑布（工具、上下文、变量仍然可用）
但在瀑布结束后，恢复该 Section 作为唯一的提示词片段
多个 effective complete Section 会导致组装失败
这允许一个 agent preset 用完全自定义的提示词替换默认组装，同时保留工具注册和变量解析的能力。
11.6 运行时上下文抑制
ctx.systemPrompt.suppressRuntimeContext()
抑制所有动态运行时上下文贡献，而不改变拥有或执行这些事实的服务。多个抑制器独立可处置。这用于需要完全控制模型上下文的场景（如 agent preset）。
12. LLM 适配器与流式传输
12.1 适配器注册
LLM 适配器通过
ctx.llm
注册。每个适配器声明支持的 provider/model 路由、上下文窗口大小、默认值和重试策略。
12.2 流式传输机制
ReactLoopAgent.step()
中的流式处理：
const stream = preparedCall?.stream(request) ?? this.loopCtx.llm.stream(request)
for await (const chunk of stream) {
  signal.throwIfAborted()
  chunkSeqs.push(this.session.append('assistant/chunk', { turn, step, chunk }).seq)
  assembler.push(chunk)
}
每个 chunk 记录为
assistant/chunk
事件（token 级保真）
BlockAssembler
逐步组装完整的 assistant 消息
中断的流保留已交付的文本/推理前缀
使用
sourceEventSeqs
关联 chunk 和最终 message
12.3 请求头管理
每个模型调用前，
buildRequest()
管理请求头：
从日志恢复持久化头（
session.requestHeader()
）
移除适配器派生的默认值
通过
agent/request
waterfall 让插件替换
通过
ctx.llm.prepareCall()
解析适配器
比较变化，按需记录
request/header
事件
头变化的三种原因：
initial
：日志中的第一个头
resume
：循环实例在已有头事件的日志上的第一个请求
change
：后续请求使用了不同的头
DeepSeek Harness 核心架构分析 — 第四部分 | 生成日期：2026-08-29