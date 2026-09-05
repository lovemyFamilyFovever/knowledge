---
title: "DSH 插件体系图谱 - DeepSeek Harness 完整架构解析"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 插件体系图谱"
collected: "2026-09-05"
status: "imported"
---

DSH 插件体系图谱 - DeepSeek Harness 完整架构解析
DSH 插件体系图谱
DeepSeek Harness 完整架构解析 - 从核心引擎到扩展生态的全景式技术蓝图
基于 100+ 个官方插件包的深度分析 | 2026年8月29日
概览
架构分层
核心层
能力层
工具层
协议层
UI层
依赖关系
接口规范
开发指南
Part 01
体系概览
DeepSeek Harness (DSH) 采用高度模块化的插件架构，将复杂 AI 代理系统分解为可组合、可替换的功能单元。整个体系由 100+ 个独立包组成，通过 Cordis 依赖注入框架实现松耦合集成。
100+
插件包总数
6
架构层次
40+
能力家族
30+
模型工具
设计哲学
DSH 的插件体系遵循"能力接缝"(Capability Seam) 设计模式：每个能力领域都有清晰的服务定义(Service Definition)、可替换的提供商(Provider)、以及面向模型的工具(Tool)。这种分层设计使得系统既能保持核心稳定，又能灵活扩展新能力。
插件分类体系
⚙️
核心层 Core
产品级
系统运行的基础骨架，包括会话管理、LLM 集成、文件系统、沙箱隔离等。这些是整个架构的基石，其他所有层都依赖于核心层提供的服务。
core
产品 API 主干：会话日志、系统提示、工具注册、代理循环
session
持久化会话数据平面：持久化、投影、标题、遥测
llm
LLM 能力家族：服务定义、内容块、流式组装
fs
文件系统能力家族：原子读写、版本守卫、沙箱
sandbox
进程沙箱能力家族：会话级隔离策略
subprocess
子进程能力家族：可执行文件查找、进程树管理
storage
非会话存储家族：JSON/SQLite 后端、域记录
🔧
能力层 Capability
产品级
为代理提供特定领域能力的服务集合，每个能力家族都遵循"服务定义 + 可替换提供商"的设计模式。能力层依赖核心层提供的基础设施。
shell
Bash/PowerShell 执行能力
web
Web 搜索和获取能力
skill
可复用代理指令发现和加载
subagent
子代理委托和控制能力
workflow
动态工作流编排能力
terminal
持久 PTY 终端能力
lsp
语言服务器协议能力
compaction
会话压缩和摘要能力
🛠️
工具层 Tool
产品级
面向模型的工具接口，将底层能力暴露给 AI 代理调用。每个工具都是能力层服务的模型友好封装，提供标准化的 JSON Schema 接口。
tool-fs
文件读写编辑工具
tool-bash
Bash 命令执行工具
tool-web
Web 搜索获取工具
tool-skill
技能加载工具
tool-subagent
子代理委托工具
tool-goal
目标管理工具
tool-todo
待办事项工具
🔌
协议层 Protocol
互操作
外部协议集成和进程间通信层，使 DSH 能够与其他 AI 系统和客户端无缝对接。协议层是系统对外暴露能力的桥梁。
mcp
MCP 协议客户端桥接
acp
ACP 自动化协议服务器
api
远程 API 网关层
sdk
TypeScript SDK 协议栈
🖥️
UI 层 Interface
交互
用户界面和交互层，提供 Web GUI、命令行界面和人类协作平面。UI 层是用户与 AI 代理交互的入口。
client
Web GUI 浏览器端（40+ UI 组件）
host
Web GUI 主机端
interaction
人类协作平面：命令、审批、权限、问答
boot
应用启动粘合代码
📦
支撑层 Support
基础设施
开发工具、测试支持、配置管理和扩展机制，为整个插件体系提供开发和运维支撑。
util
底层共享工具库
typert
类型反射和加载器系统
settings
用户设置能力家族
credentials
凭证和授权家族
test-support
开发和测试基础设施
experimental
私有实验包
Part 02
架构分层详解
DSH 采用经典的分层架构，每一层都有明确的职责边界和依赖关系。从底层的基础设施到顶层的用户界面，形成了一条清晰的能力传递链。
DSH 插件架构分层图
UI 层 - 用户交互
client (40+ 组件)
host
interaction
feedback
协议层 - 外部集成
mcp
acp
api
sdk
工具层 - 模型接口
tool-fs
tool-bash
tool-web
tool-skill
tool-subagent
tool-goal
tool-workflow
tool-lsp
tool-terminal
tool-session-query
能力层 - 领域服务
shell
web
skill
subagent
workflow
terminal
lsp
compaction
session-query
goal
plan
schedule
jobs
核心层 - 基础设施
core
session
llm
fs
sandbox
subprocess
storage
依赖流向原则
向下依赖
上层可以依赖下层，但下层不能依赖上层。例如，工具层依赖能力层和核心层，但核心层不依赖任何上层。这种单向依赖确保了系统的稳定性和可测试性。
同层隔离
同一层内的插件通常不直接相互依赖，而是通过上层的组合来协调。例如，`fs` 和 `shell` 都是核心层插件，它们之间不直接依赖，而是在能力层通过组合使用。
Part 03
核心层详解
核心层是整个 DSH 架构的基石，提供了系统运行所需的基础服务。这些服务包括会话管理、LLM 集成、文件系统操作、沙箱隔离等。核心层的设计特点是高度稳定、接口清晰、可替换实现。
core/ - 产品 API 主干
职责
：`core` 包组是整个系统的控制脊柱，包含会话日志、系统提示组装、工具注册表、代理词汇表、部署默认模型选择和具体的代理循环。
子包
职责
ctx 键
scope/
作用域上下文注册原语
库 - 无 ctx 键
session/
事件源会话日志和内存存储
ctx.sessions
system-prompt/
提示词和工具模式组装注册
ctx.systemPrompt
tools/
作用域工具注册和执行管道
ctx.tools
agent/
代理接口、注册和事件词汇
ctx.agents
agent-default-model/
代理入口点共享的默认模型选择
ctx.agentDefaultModel
agent-loop/
默认的具体代理驱动器
ctx.agentLoop
session/ - 持久化会话数据平面
职责
：`session` 包组围绕 `core/session` 的实时内存服务构建，包括持久化接缝及其存储后端、检查点策略、投影接缝、标题生成和会话遥测。
持久化子系统
session-persistence
定义持久化服务和共享写入协调
ctx.sessionPersistence
session-checkpoint-policy
应用语义持久化检查点
session-persistence-jsonl
JSONL 文件持久化后端
session-persistence-sqlite
SQLite 持久化后端
投影子系统
session-projection
定义和驱动会话投影单元
ctx.sessionProjections
session-projection-cache
持久化和恢复投影检查点
ctx.sessionProjectionCache
session-stats
提供全日志对话计数和时间统计
llm/ - LLM 能力家族
职责
：`llm` 包组拥有 LLM 接缝及其提供商适配器。它同时承担服务定义和消费者角色：抽象服务、内容块词汇和流块组装器。
llm
LLM 服务和共享流式词汇
ctx.llm
token-meter
重放感知的令牌测量
ctx.tokenMeter
llm-retry
提供商级重试策略
llm-deepseek
直接 DeepSeek 适配器
llm-pi-ai
多提供商 pi-ai 适配器
fs/ - 文件系统能力家族
职责
：`fs` 包组提供文件系统栈：提供商契约（执行世界路径、有界文本 IO、原子突变）、本地实现、策略门插件、面向模型的文件工具和 ripgrep 支持的发现工具。
fs
服务定义：路径/URI/包含、文本 IO、原子突变原语
ctx.fs
fs-local
本地文件系统实现
fs-sandbox
沙箱执行文件系统：扩展 fs-local
fs-observation-policy
策略门插件：观察状态 + 编辑前读取 + 版本守卫
tool-fs
面向模型的 read/write/edit 工具和执行器
tool-fs-search
面向模型的 glob/grep 发现工具
sandbox/ - 进程沙箱能力家族
职责
：`sandbox` 包组将每会话的隔离策略应用于进程执行。它覆盖同世界子进程；隔离环境替换完整的能力实现而不是在这里注册。
sandbox
定义进程沙箱服务和共享升级词汇
ctx.sandbox
sandbox-local
提供本地平台隔离后端
sandbox-policy
解析持久的每会话沙箱策略
ctx.sandboxPolicy
Part 04
能力层详解
能力层是 DSH 的核心价值所在，它为 AI 代理提供了丰富的领域能力。每个能力家族都遵循"服务定义 + 可替换提供商"的设计模式，确保系统的灵活性和可扩展性。
shell/ - Bash 执行能力
职责
：shell 能力家族跨越规范的执行器接缝、其实现、共享 shell 环境和面向模型的工具。所有都是产品包。
shell
定义服务提供商和消费者共享的执行器契约
ctx.shell
bash-local
通过本地 subprocess 服务执行命令
bash-sandbox
在本地执行前应用配置的沙箱后端
pwsh-local
执行 PowerShell 命令
shell-env
提供 shell 工具共享的 DSH_* 环境
ctx.shellEnv
tool-bash
向模型暴露 Bash 执行和后台任务集成
tool-pwsh
向模型暴露 PowerShell 执行
web/ - Web 能力家族
职责
：web 能力家族提供提供商中立的 Web 搜索和获取操作，以及消费它们的面向模型的工具。
web
定义 Web 提供商注册、选择和共享错误
ctx.web
web-search-exa
通过 Exa 提供 Web 搜索
web-search-perplexity
通过 Perplexity 提供 Web 搜索
web-search-deepseek
原生 DeepSeek Web 搜索
web-fetch-http
获取公共 HTTP/HTTPS 资源
tool-web
向模型暴露 Web 搜索和获取
subagent/ - 子代理能力家族
职责
：subagent 能力家族让代理能够将工作委托给子代理。多个命名的提供商可以在一个上下文中共存。
subagent
定义提供商注册、委托和继续
ctx.subagents
subagent-inprocess
提供共享的进程内运行驱动器
subagent-spawn-in-process
启动新的进程内子代理
subagent-fork-in-process
从父代理完成的历史启动进程内子代理
subagent-acp
通过 ACP 启动进程外子代理
subagent-codex
启动真实的 Codex 应用服务器子代理
subagent-claude-code
通过 Claude Agent SDK 启动 Claude Code 子代理
tool-subagent
向模型暴露委托功能
其他能力家族概览
能力家族
职责描述
关键 ctx 键
workflow/
运行模型编排的工作流，暴露通用和固定策略工具
ctx.workflowEngine
terminal/
提供持久、所有者范围的 PTY 终端会话
ctx.terminals
lsp/
语言服务器能力接缝：goToDefinition、findReferences 等
ctx.lsp
compaction/
会话压缩：令牌压力、摘要、工具结果修剪
ctx.compaction
session-query/
会话检索：授权读取、关系查询、搜索操作
ctx.sessionQuery
goal/
持久化的会话内目标状态管理
ctx.goals
plan/
计划模式：记录的每代理协作状态
ctx.planMode
schedule/
会话本地提醒：持久状态在会话日志中
-
jobs/
后台任务：观察、取消、等待、完成通知
ctx.jobs
skill/
可复用代理指令发现和加载
ctx.skills
Part 05
工具层详解
工具层是 AI 代理与底层能力交互的桥梁。每个工具都提供标准化的 JSON Schema 接口，使模型能够清晰地理解和调用系统能力。工具层的设计遵循"一个工具一个职责"的原则。
完整工具清单
工具包
模型工具名
功能描述
依赖能力
tool-fs
read, write, edit
文件读取、写入和编辑
fs
tool-fs-search
glob, grep
文件发现和内容搜索
subprocess
tool-bash
run_command
Bash 命令执行
shell
tool-pwsh
run_command
PowerShell 命令执行
shell
tool-web
web_search, web_fetch
Web 搜索和获取
web
tool-skill
skill
技能目录和加载
skill
tool-subagent
task
子代理委托
subagent
tool-subagent-control
subagent_message, subagent_list
子代理消息和列表
subagent
tool-subagent-report
report
子代理到父代理的报告通道
subagent
tool-workflow
workflow
通用工作流执行
workflow
tool-ralph
ralph
固定的新代理 Ralph 工作流
workflow
tool-goal
create_goal, update_goal, get_goal
目标创建、更新、查询
goal
tool-todo
todo_write
待办事项管理
session
tool-session-query
session_query
会话历史查询
session-query
tool-terminal
terminal_*
6 个终端操作工具
terminal
tool-lsp
lsp
语言服务器导航操作
lsp
tool-jobs
job_*
后台任务控制
jobs
tool-ask-user
ask_user
向用户提问
interaction
tool-cordis
cordis_*
运行时检查和动态包
extensions
tool-spill
-
工具输出溢出策略
spill
工具注册机制
所有工具通过
ctx.tools
注册服务注册到系统中。工具注册时需要提供：
工具名称
：模型调用时使用的唯一标识
JSON Schema
：参数的完整类型定义
执行函数
：工具的实际执行逻辑
描述
：帮助模型理解工具用途的自然语言描述
Part 06
协议层详解
协议层是 DSH 与外部系统交互的桥梁，支持多种标准协议和自定义协议。通过协议层，DSH 能够与 MCP 生态系统、其他 AI 代理、以及各种客户端无缝对接。
mcp/ - Model Context Protocol
职责
：MCP 包桥接 harness 到 MCP 生态系统。MCP 是一个开放标准，用于在 AI 模型和外部工具/数据源之间建立标准化的通信接口。
mcp-client
MCP 客户端桥接，将外部服务器工具注册到 ctx.tools
MCP 客户端的核心功能包括：
自动发现和连接 MCP 服务器
将 MCP 工具转换为 DSH 内部工具格式
处理 MCP 协议的生命周期管理
提供工具调用的代理和错误处理
acp/ - Agent Client Protocol
职责
：ACP 组通过 Agent Client Protocol 向编程客户端暴露 harness 代理。它是一个互操作传输层，而不是表示层或人类交互层。
acp
仅自动化的 ACP 服务器
ACP 的主要用途：
允许外部程序控制 DSH 代理
支持自动化的测试和集成场景
提供标准化的代理交互协议
api/ - 远程 API 层
职责
：应用层面向的远程栈。`remotes` 拥有 BFF 策略和选定的业务 API，而 `gateway` 实现 Host 和 Client 环境共享的 Typert 一元 RPC 端点。
remotes
Host Agent/Session 查找策略和 Client Remote 贡献组装
gateway
Host Typert 调度器和 Client Remote 端点
sdk/ - TypeScript SDK
职责
：从另一个进程驱动 Harness 运行时的协议栈。调用者提供运行时可执行文件和其 `cordis.yml`；此组不创建、配置、构建或启动开发者项目。
protocol
定义 SDK 运行时线协议
client
通过 TypeScript 客户端 API 驱动 Harness 运行时
server
通过 stdio JSON-RPC 服务进程外 SDK 客户端
Part 07
UI 层详解
UI 层是用户与 DSH 交互的入口，提供了丰富的 Web GUI 组件和人类协作工具。client 包组包含 40+ 个 UI 组件，覆盖了从基础布局到高级功能的完整界面需求。
client/ - Web GUI 浏览器端
职责
：dsh web GUI 的浏览器端：shell 启动、浏览器-主机通信、共享 UI 服务和功能插件。
核心组件
web
从客户端入口图启动浏览器 shell
ui-renderer
将插槽数据绑定到 React 并挂载组装的应用
modules
加载浏览器端客户端模块
connection
维护浏览器-主机 RPC 通信和事件传递
runtime
提供会话、工作区和 UI 组合的共享客户端服务
UI 功能组件
ui-slots
UI 功能注册和组合扩展槽
ui-theme
应用选定的颜色主题
ui-primitives
共享的 React 控件、图标和内容渲染器
ui-layout
排列主要应用区域
ui-sidebar
呈现工作区和会话导航
ui-conversation
呈现活动对话及其输入界面
ui-tool
组合工具调用树和按键的工具视图
ui-goal
呈现和管理当前目标
ui-plan
呈现活动计划模式状态和退出控制
ui-commands
提供会话感知的命令发现和调度
ui-input-trigger
协调内联命令和引用建议
ui-skill
向内联建议添加技能引用
ui-reference
统一的 Web @file/@session 引用源
ui-subagent
提供子代理导航和内联引用
ui-model-selection
提供模型选择界面
ui-settings
托管设置界面及其扩展区域
ui-user-questions
呈现代理请求的交互式问题
ui-agent-preset
选择会话的代理预设
host/ - Web GUI 主机端
职责
：dsh web GUI 的主机端：每个客户端形状共享的 API 网关，以及它运行的普通 HTTP 服务器。
apiproxy
共享的主机 API 网关和线协议
ctx.apiProxy
webserver
HTTP 路由载体
ctx.webServer
frontend-static
webserver 回退席位上的 SPA 分发服务器
directory-picker
工作区目录选择接缝
ctx.directoryPicker
plugin-inventory
当前加载器条目的只读投影
interaction/ - 人类协作平面
职责
：人类与运行中的代理协作的服务和插件——问题、审批、权限预设、命令。这些都是产品包：真实的人驱动的接口。
commands
为交互式适配器注册和调度人类命令
ctx.commands
user-approval
协调一次性审批决策
ctx.approval
permission
呈现和持久化面向用户的权限预设
ctx.permissionPresets
user-questions
定义提供商中立的人类问题/答案接缝
ctx.userQuestions
tool-ask-user
向模型暴露人类问题
Part 08
依赖关系分析
理解插件之间的依赖关系对于系统的维护和扩展至关重要。DSH 的依赖关系呈现出清晰的层次结构，核心层被广泛依赖，而上层插件通常是叶子节点。
基础依赖（被多个插件依赖）
这些是系统中最核心的插件，被大量上层插件依赖。它们的稳定性直接影响整个系统的可靠性。
一级基础依赖
core
被几乎所有插件依赖的基础骨架
session
会话状态管理的核心依赖
llm
所有需要模型调用的插件依赖
fs
文件操作相关的插件依赖
二级基础依赖
subprocess
进程执行能力的基础
storage
持久化存储的基础
util
共享工具库
typert
类型系统和加载器
叶子节点（只依赖其他插件，不被依赖）
叶子节点通常是最终的功能实现，它们消费其他服务但不提供被消费的服务。这使得它们更容易被替换或移除。
tool-fs
文件工具 - 消费 fs 服务
tool-bash
Bash 工具 - 消费 shell 服务
tool-web
Web 工具 - 消费 web 服务
tool-subagent
子代理工具 - 消费 subagent 服务
llm-deepseek
DeepSeek 适配器 - 注册到 llm 服务
fs-local
本地文件系统 - 注册到 fs 服务
sandbox-local
本地沙箱 - 注册到 sandbox 服务
依赖层次图
DSH 核心依赖关系图
graph TD
    subgraph Core["核心层"]
        CORE[core]
        SESSION[session]
        LLM[llm]
        FS[fs]
        SANDBOX[sandbox]
        SUBPROCESS[subprocess]
        STORAGE[storage]
    end

    subgraph Capability["能力层"]
        SHELL[shell]
        WEB[web]
        SKILL[skill]
        SUBAGENT[subagent]
        WORKFLOW[workflow]
        TERMINAL[terminal]
        LSP[lsp]
    end

    subgraph Tool["工具层"]
        TOOL_FS[tool-fs]
        TOOL_BASH[tool-bash]
        TOOL_WEB[tool-web]
        TOOL_SKILL[tool-skill]
        TOOL_SUBAGENT[tool-subagent]
    end

    CORE --> SESSION
    CORE --> LLM
    CORE --> FS
    CORE --> SANDBOX
    
    SESSION --> LLM
    FS --> SUBPROCESS
    SANDBOX --> SUBPROCESS
    
    SHELL --> SUBPROCESS
    SHELL --> SANDBOX
    WEB --> LLM
    SKILL --> SESSION
    SUBAGENT --> SESSION
    SUBAGENT --> LLM
    WORKFLOW --> SUBAGENT
    TERMINAL --> SUBPROCESS
    LSP --> FS
    LSP --> SUBPROCESS
    
    TOOL_FS --> FS
    TOOL_BASH --> SHELL
    TOOL_WEB --> WEB
    TOOL_SKILL --> SKILL
    TOOL_SUBAGENT --> SUBAGENT
Part 09
接口规范
DSH 的插件接口遵循统一的规范，确保不同插件之间能够无缝协作。每个插件类型都有明确的接口要求和生命周期钩子。
Cordis 服务接口
DSH 基于 Cordis 依赖注入框架，所有服务都通过
ctx
上下文对象注册和访问。服务接口遵循以下规范：
接口类型
描述
示例
服务定义
定义能力的抽象接口和类型
ctx.fs
,
ctx.llm
,
ctx.shell
服务提供商
实现服务定义的具体后端
fs-local
,
llm-deepseek
,
bash-local
服务消费者
使用服务的插件
tool-fs
,
tool-bash
,
compaction
事件监听
监听特定事件的插件
fs-observation-policy
,
session-checkpoint-policy
插件生命周期
DSH 插件遵循标准的生命周期钩子：
apply
：插件被加载时调用，用于注册服务和初始化
dispose
：插件被卸载时调用，用于清理资源
ready
：所有依赖的插件都已加载完成
fork
：创建子作用域时调用
// 插件示例
export default class MyPlugin {
  static inject = ['fs', 'llm']; // 声明依赖

  constructor(ctx) {
    // apply 阶段
    ctx.on('dispose', () => {
      // dispose 阶段清理
    });
  }

  async doSomething() {
    // 使用注入的服务
    const content = await this.fs.readFile('...');
    const result = await this.llm.chat({ ... });
  }
}
工具接口规范
面向模型的工具需要实现标准的接口规范：
// 工具定义示例
{
  name: 'my_tool',                    // 工具名称
  description: '工具功能描述',          // 帮助模型理解的描述
  parameters: {                       // JSON Schema 参数定义
    type: 'object',
    properties: {
      input: {
        type: 'string',
        description: '输入参数描述'
      }
    },
    required: ['input']
  },
  execute: async (params, context) => { // 执行函数
    // 工具逻辑
    return { result: '...' };
  }
}
配置格式
插件配置通过
cordis.yml
文件定义：
# cordis.yml 示例
name: my-plugin
version: 1.0.0

# 插件依赖
dependencies:
  - dsh-core
  - dsh-session
  - dsh-llm

# 服务注册
provides:
  - ctx.myService

# 配置模式
config:
  type: object
  properties:
    apiKey:
      type: string
      description: API 密钥
    timeout:
      type: number
      default: 30000
Part 10
插件开发指南
本节提供 DSH 插件开发的实用指南，帮助开发者快速上手并遵循最佳实践。
如何选择插件类型
创建新的能力家族
当你需要引入一个全新的能力领域时（如数据库访问、特定 API 集成等），应该创建新的能力家族。
定义服务接口（Service Definition）
实现至少一个提供商
创建面向模型的工具
扩展现有能力
当你需要为现有能力添加新的提供商时（如新的 LLM 适配器、新的存储后端等），应该创建提供商插件。
实现现有服务接口
注册到对应的 ctx 键
不需要创建新的工具
最小化插件模板
提供商插件模板
// packages/my-capability/my-provider/index.ts
import { Context } from 'cordis';

export default class MyProvider {
  static inject = ['myCapability']; // 依赖的服务

  constructor(ctx: Context) {
    // 注册到服务
    ctx.myCapability.register({
      id: 'my-provider',
      // 实现服务接口
      async doSomething(params) {
        // 实现逻辑
      }
    });

    // 清理
    ctx.on('dispose', () => {
      ctx.myCapability.unregister('my-provider');
    });
  }
}
工具插件模板
// packages/tools/my-tool/index.ts
import { Context } from 'cordis';

export default class MyTool {
  static inject = ['tools', 'myCapability'];

  constructor(ctx: Context) {
    // 注册工具
    ctx.tools.register({
      name: 'my_tool',
      description: '我的自定义工具',
      parameters: {
        type: 'object',
        properties: {
          input: { type: 'string', description: '输入' }
        },
        required: ['input']
      },
      execute: async (params) => {
        return await ctx.myCapability.doSomething(params);
      }
    });
  }
}
测试策略
DSH 提供了完善的测试支持：
test-support
：开发和测试基础设施包
agent-loop-testkit
：AgentLoop 测试套件
llm-mock-server
：确定性的 OpenAI 兼容故障服务器
llm-replay
：重放记录的模型响应
测试建议：
使用 mock 服务器隔离外部依赖
使用 replay 机制进行端到端测试
为每个提供商编写独立的集成测试
使用 snapshot 测试验证工具输出格式
发布流程
插件发布的标准流程：
开发
：在本地开发和测试插件
文档
：编写 README.md 和 API 文档
审查
：提交 PR 进行代码审查
集成
：确保与现有系统的兼容性
发布
：合并到主分支后自动发布
最佳实践
遵循"能力接缝"设计模式，确保你的插件有清晰的服务定义和可替换的提供商。这样其他开发者可以轻松地扩展或替换你的实现。
常见问题解答
Q: 如何调试插件？
使用
ctx.on('debug', ...)
监听调试事件，或使用
tool-cordis
工具检查运行时状态。
Q: 插件之间如何通信？
通过 Cordis 的事件系统或直接调用注入的服务。避免直接依赖其他插件的内部实现。
Q: 如何处理配置？
使用
ctx.settings
服务管理配置，支持分层解析和热更新。
Q: 如何贡献到 DSH？
遵循项目的贡献指南，确保代码符合 AGENTS.md 中定义的规范和标准。
DSH 插件体系图谱 - DeepSeek Harness 完整架构解析
基于 100+ 个官方插件包的深度分析 | 2026年8月29日
本文档基于 E:\chen\code\deepseek-harness/packages/ 目录下的 README.md 文件生成