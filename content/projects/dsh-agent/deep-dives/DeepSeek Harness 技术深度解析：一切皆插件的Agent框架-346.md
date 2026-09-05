---
title: "DeepSeek Harness 技术深度解析：一切皆插件的Agent框架"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 技术深度解析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 技术深度解析：一切皆插件的Agent框架

> 从Cordis依赖注入到可组合智能体的完整架构剖析
>
> **标签**：TypeScript | Agent Framework | Open Source | Cordis
>
> 2026年8月

---

## 目录

- **第一部分：架构哲学与基础**
  - [1. 引言：AI Agent框架的发展历程](#1-引言ai-agent框架的发展历程)
  - [2. DSH的诞生背景和设计理念](#2-dsh的诞生背景和设计理念)
  - [3. "一切皆插件"架构的哲学和实现](#3-一切皆插件架构的哲学和实现)
  - [4. Cordis依赖注入框架深度剖析](#4-cordis依赖注入框架深度剖析)
- **第二部分：核心执行引擎**
  - [5. Agent执行引擎的核心机制](#5-agent执行引擎的核心机制)
  - [6. 多模型接入层的抽象设计](#6-多模型接入层的抽象设计)
  - [7. 安全沙箱机制](#7-安全沙箱机制)
- **第三部分：能力扩展与生态**
  - [8. 文件系统抽象层](#8-文件系统抽象层)
  - [9. 终端和进程管理](#9-终端和进程管理)
  - [10. Web UI的实时通信架构](#10-web-ui的实时通信架构)
  - [11. MCP和ACP协议适配](#11-mcp和acp协议适配)
  - [12. 技能系统的自演化能力](#12-技能系统的自演化能力)
  - [13. 与其他Agent框架的深度技术对比](#13-与其他agent框架的深度技术对比)
  - [14. 生产环境部署考量](#14-生产环境部署考量)
  - [15. 未来展望和总结](#15-未来展望和总结)

---

## 第一部分：架构哲学与基础

## 1. 引言：AI Agent框架的发展历程

### 1.1 从ChatBot到Agent的演进

2022年底ChatGPT的发布标志着大语言模型（LLM）进入主流视野，但最初的交互模式极为简单——用户输入文本，模型返回文本，双方在一个无状态的对话窗口中来回交流。这种**ChatBot范式**的核心局限在于：模型无法主动执行任何操作，无法访问外部数据，也无法维持跨会话的任务状态。它是一个被动的问答机器，而非主动的问题解决者。

2023年，随着ReAct（Reasoning + Acting）论文的广泛传播，业界开始意识到LLM可以通过"思考-行动-观察"的循环来与外部世界交互。这一认知催生了第一代Agent框架：AutoGPT在2023年3月横空出世，一周内获得超过10万GitHub星标，其核心思想是让GPT-4自主分解任务、调用工具、观察结果并迭代执行。同期，LangChain从一个简单的LLM封装库迅速演化为包含Agent、工具链、记忆系统和文档检索的全栈框架。BabyAGI则提出了任务驱动自主Agent的概念，通过任务队列来组织和优先排序Agent的工作。

2024年是Agent框架的**分化之年**。LangGraph将图计算引入Agent编排，用状态机替代了简单的线性循环；CrewAI引入了多Agent协作的概念，让不同角色的Agent组成"团队"来完成复杂任务；AutoGen则专注于多Agent对话模式，允许Agent之间进行结构化的讨论和辩论。与此同时，OpenAI在2025年推出了Agents SDK，Anthropic推出了Claude Agent SDK，模型厂商开始从底层模型向上游的Agent框架延伸。

进入2025-2026年，Agent框架的竞争焦点从"能不能用"转向了"怎么用好"。DSH（DeepSeek Harness）正是在这一背景下诞生的，它代表了一种全新的思考方式：不追求功能的堆叠，而是追求架构的极致可组合性。

### 1.2 Agent框架的核心需求

一个成熟的AI Agent框架需要解决以下核心问题：

**模型抽象**：不同厂商的API接口、参数格式、流式响应协议各不相同。框架必须提供统一的模型接入层，使得上层应用无需感知底层差异。更重要的是，模型切换应该是配置级别的变更，而不是代码级别的重构。

**工具编排**：Agent的核心能力来自工具。框架需要定义工具的注册、发现、调用和结果处理的标准流程。工具不仅仅是API调用——文件操作、代码执行、终端命令、Web浏览都是工具的形态。

**上下文管理**：Agent的对话历史会随交互不断增长，但模型的上下文窗口是有限的。框架需要管理会话状态、执行历史压缩（compaction）、维护持久化日志，并确保上下文在Agent重启后可恢复。

**安全隔离**：Agent执行代码、操作文件系统、运行终端命令——这些操作如果不受限制，可能造成灾难性后果。框架必须提供沙箱机制，在文件系统、进程、网络层面实施细粒度的权限控制。

**可观测性**：Agent的行为是非确定性的。框架需要提供完整的事件日志、工具调用追踪、模型请求/响应记录，使得开发者和用户能够理解和调试Agent的每一个决策。

**可扩展性**：框架必须是开放的。用户应该能够添加新的模型适配器、新的工具、新的存储后端、新的UI组件，而无需修改框架核心代码。这种扩展性不是通过钩子函数或回调来实现的——它应该是架构本身的属性。

### 1.3 当前市场格局

当前Agent框架市场呈现出明显的分层格局。在底层，OpenAI的Agents SDK和Anthropic的Claude Agent SDK各自构建了与自家模型深度集成的Agent运行时。在中层，LangGraph以其图编排能力占据了复杂工作流的生态位，CrewAI则以多Agent协作为卖点吸引了大量用户。在上层，各种低代码Agent构建平台（如Dify、Coze）降低了Agent开发的门槛。

DSH选择了一条与众不同的路线——它不是在现有框架之上叠加功能，而是从依赖注入和插件化架构的根基重新设计Agent运行时。这一选择源于DeepSeek团队对现有框架痛点的深刻洞察：当框架的每个组件都是硬编码耦合的，扩展和替换的成本就会呈指数增长。

## 2. DSH的诞生背景和设计理念

### 2.1 DeepSeek AI的技术路线

DeepSeek AI自成立以来，其技术路线可以概括为"模型与工程并重"。在模型层面，DeepSeek-V2引入了Multi-head Latent Attention（MLA）和DeepSeekMoE架构，在保持性能的同时大幅降低了推理成本；DeepSeek-R1则通过强化学习训练出了强大的推理能力。在工程层面，DeepSeek较早地认识到：一个好的Agent框架不仅仅是模型能力的延伸，更是一个独立的软件工程挑战。

DSH的设计始于一个核心观察：**当前所有Agent框架都存在一个隐含假设——框架作者比用户更了解Agent应该如何工作**。这种假设导致了框架的僵化：LangChain的Chain/Agent模式无法轻易跳出循环；AutoGen的多Agent对话模式无法灵活地重新编排；即使是LangGraph，其图结构的定义方式也带有强烈的预设。

DSH的回应是：与其告诉用户Agent应该如何工作，不如提供一个可组合的基础设施（Harness），让用户自己定义Agent的行为。这就是"Harness"这个名字的由来——它不是Agent本身，而是承载Agent的底座。

### 2.2 "一切皆插件"的哲学来源

"一切皆插件"（Everything is a Plugin）并非DSH首创的概念。Eclipse IDE在2001年就以OSGi为基础构建了完全插件化的架构；Koishi的作者Shigma同时也是Cordis框架的作者，他在Koishi中实践了"一切皆服务"的理念；VSCode的插件系统同样是"一切皆可扩展"的成功案例。

DSH的独特之处在于，它将这一理念推向了Agent框架的每一个角落。在DSH中，以下组件全部是可替换的插件：

- **模型适配器**：不仅不同厂商（OpenAI、Anthropic、DeepSeek、Google）是不同的插件，同一厂商的不同模型系列也可以是不同的插件
- **工具系统**：文件操作、Shell执行、Web搜索、代码运行——每个工具都是独立的插件
- **存储后端**：会话持久化、文件系统访问、附件管理——每个存储层都是可替换的插件
- **沙箱机制**：Landlock（Linux）、Seatbelt（macOS）、ACL（Windows）——每个平台的安全后端都是独立的插件
- **UI层**：Web界面的每个组件——对话视图、工具调用展示、设置面板——都是独立的客户端插件
- **Agent循环本身**：是的，就连Agent的思考-执行循环也是通过插件实现的

这种极致的插件化带来的直接后果是：DSH没有一个传统意义上的"核心"。它的"核心"仅仅是一个依赖注入容器和一组服务接口定义。所有的行为都是通过插件挂载到这个容器中来实现的。

### 2.3 与传统框架的差异

| 维度 | 传统框架（LangChain/AutoGen） | DSH |
|---|---|---|
| 扩展方式 | 继承基类、注册回调、配置选项 | 注册Cordis服务、发布类型化事件 |
| 组件耦合 | 框架核心直接依赖具体实现 | 核心仅依赖服务接口，实现通过DI注入 |
| 运行时修改 | 通常需要重启 | 支持HMR热重载，插件可运行时装卸 |
| 类型安全 | 运行时类型检查为主 | TypeScript编译期类型推导+运行时验证 |
| 事件系统 | 简单的回调/钩子 | 类型化事件，支持emit/waterfall/parallel/serial四种模式 |
| 撤销/回滚 | 不支持或手动实现 | 所有注册都是可逆效果（reversible effects） |
| 作用域隔离 | 全局单例为主 | 每个Agent拥有独立的作用域（scope） |

## 3. "一切皆插件"架构的哲学和实现

### 3.1 什么是"一切皆插件"

在DSH的语境中，"一切皆插件"有三层递进的含义：

**第一层：所有功能模块都是插件。** 这是最直观的理解——模型适配器、工具、存储后端、UI组件都是独立的包，可以单独安装、升级和替换。

**第二层：框架的基础设施也是插件。** Agent循环、会话管理、系统提示词组装——这些在其他框架中被视为"核心"的组件，在DSH中同样是插件。它们通过Cordis的Service机制注册，可以在不修改框架代码的情况下被替换。

**第三层：插件的组合方式也是可配置的。** DSH引入了Profile（配置文件）和Bundle（分发包）的概念。一个Profile定义了要加载哪些Bundle，每个Bundle又是一组Cordis配置行和它们挂载的代码。通过不同的Profile组合，同一套代码可以表现为完全不同的产品形态。

### 3.2 插件化的层次

#### 模型层（Model Layer）

DSH支持的模型提供商包括OpenAI、Anthropic、DeepSeek、Google Gemini、Mistral、AWS Bedrock等。每个提供商是一个独立的LLM适配器插件，注册在`ctx.llm`服务上。适配器需要实现统一的`LlmAdapter`接口，包括`stream()`方法用于流式请求和`capabilities`属性用于声明支持的特性。

#### 工具层（Tool Layer）

工具注册在`ctx.tools`服务上。每个工具是一个`ToolDefinition`，包含名称、描述、参数Schema、输出Schema、执行函数和可选的UI呈现器。工具的参数和输出使用统一的JSON Schema DSL定义，支持类型推导。

#### 存储层（Storage Layer）

会话持久化、文件系统访问、附件管理都是可替换的服务。`ctx.sessions`管理会话日志，`ctx.fs`提供文件系统抽象。

#### UI层（UI Layer）

DSH的Web前端由30多个独立的客户端模块组成，每个模块是一个Cordis插件。前端使用Vite构建，支持HMR热重载。

#### 调度逻辑层（Scheduling Layer）

Agent的执行调度——何时开始新的turn、何时执行工具、何时压缩上下文——都是通过事件和插件组合实现的，而非硬编码在框架核心中。

### 3.3 极致模块化的利弊分析

**优势：**
- **可替换性**：任何组件都可以被替换，使得DSH可以适应极其多样的部署场景
- **可测试性**：每个模块都是独立的，可以单独测试
- **团队协作**：不同的团队可以并行开发不同的模块
- **增量升级**：可以单独升级某个模块而不影响其他模块
- **社区贡献**：第三方开发者可以轻松地为DSH编写插件

**挑战：**
- **认知负担**：新开发者面对40+个包会感到困惑
- **接口设计**：每个服务接口的设计都需要极其谨慎
- **调试复杂度**：当问题跨越多个插件时，追踪问题的根源更加困难
- **初始化开销**：依赖注入容器的启动和解析需要一定的时间
- **文档负担**：每个子系统都需要完整的文档

## 4. Cordis依赖注入框架深度剖析

### 4.1 IoC容器的设计

Cordis是DSH的根基框架，其设计思想在论文《A Programming Paradigm for Spatiotemporal Composability》中有详细阐述。核心理念可以用五个要点概括：

**插件是实现Service接口的对象。** 一个插件可以是一个带有`inject`和`apply(ctx)`字段的函数，也可以是一个`Service`子类。

**上下文（Context）是服务的仓库。** 一个服务通过`ctx.<key>`的形式声明自己在上下文中的位置，如`ctx.tools`、`ctx.llm`、`ctx.sessions`。

**通过`inject`声明服务依赖。** 加载顺序通过服务依赖关系自动推导：

```typescript
const myPlugin: Plugin = {
  inject: ['tools', 'llm'],
  apply(ctx) {
    // 此时ctx.tools和ctx.llm已经就绪
    ctx.tools.register({ ... })
  }
}
```

**类型化事件用于通信。** 每种分发模式有不同的语义：

| 模式 | 是否等待 | 分发顺序 | 有返回值 | 用途 |
|---|---|---|---|---|
| `emit` | 否 | 注册顺序 | 否 | 通知观察者 |
| `waterfall` | 否 | 注册顺序 | 是 | 中间件链 |
| `parallel` | 是 | 并行 | 否 | 并行扇出 |
| `serial` | 是 | 注册顺序 | 是 | 有序执行 |

**注册是可逆效果。** 所有通过`ctx.effect()`或`ctx.on()`安装的注册在插件卸载时都会自动撤销。

### 4.2 服务生命周期

Cordis中的服务有明确的生命周期状态机。一个服务从"未注册"开始，经过"等待依赖"、"就绪"、"活跃"等状态，最终在插件卸载时进入"已销毁"状态。一个重要的不变式：**一个插件的效果永远不会在其自身被卸载后仍然存在**。

### 4.3 作用域和继承

Cordis的作用域系统是DSH实现per-agent隔离的基础。每个Agent在创建时会获得自己的作用域（`agent.ctx`），这个作用域继承了全局的服务，但可以注册Agent特有的服务。

### 4.4 与NestJS/InversifyJS的对比

| 特性 | NestJS | InversifyJS | Cordis |
|---|---|---|---|
| 定位 | Web应用框架 | 通用DI容器 | 插件化运行时框架 |
| 装饰器 | 重度依赖 | 使用装饰器 | 不使用（纯函数/对象） |
| 生命周期 | 模块级别 | 手动管理 | 自动效果撤销 |
| HMR支持 | 不原生支持 | 不支持 | 核心特性 |
| 事件系统 | 简单EventEmitter | 无内置事件 | 类型化事件，四种模式 |
| 作用域 | Request scope | 自定义scope | 层次化scope，per-agent隔离 |

> **关键设计决策**：DSH的Cordis配置使用YAML格式（`cordis.yml`），支持`!!js`表达式节点。配置文件不仅仅是静态声明——它可以包含动态逻辑，根据环境变量、运行时状态来决定加载哪些插件。

---

## 第二部分：核心执行引擎

## 5. Agent执行引擎的核心机制

### 5.1 Turn和Step：执行的基本单元

DSH的Agent执行循环建立在两个核心概念之上：**Turn**（轮次）和**Step**（步骤）。一个Turn代表Agent处理一个用户输入的完整过程；一个Step代表一次模型请求加上该请求触发的所有工具调用。一个Turn可以包含零个或多个Step。

```
turn/start
  claim next-step input + one queued message
  assemble prompt sections + tool schemas
  -> agent/pre-step                   reject | enter(messages)
     step/start
     append entered messages as user/message
     derive model history from the log
     agent/request -> llm/stream -> assistant/chunk* -> assistant/message
     tool/call* -> tools/pre-execute -> tools/execute -> tools/post-execute -> tool/result*
     step/end
     tools owe another request, or next-step input arrived -> next step
  -> agent/turn-stopping
turn/end
```

### 5.2 Session管理和上下文传播

DSH的Session是一个**追加式日志**（append-only log），记录了Agent交互的每一个事实。模型的对话历史是从日志中**派生**的，而不是单独存储的。

Session日志中的事件类型包括：
- `turn/start`和`turn/end`：标记每个Turn的开始和结束
- `step/start`和`step/end`：标记每个Step的开始和结束
- `user/message`：用户输入消息（包括直接输入和注入的上下文）
- `assistant/chunk`：模型响应的原始流式块
- `assistant/message`：组装完成的助手消息
- `tool/call`和`tool/result`：工具调用和结果
- `request/header`：完整的请求信封
- `request/context`：路由元数据

重要不变式：**模型可见即已记录**（Model-visible means logged）。

### 5.3 Inbox和消息路由

DSH的Agent拥有双列表Inbox系统——`next-turn`和`next-step`。Agent的公开API提供三种消息发送方式：
- `followup(message)`：发送完整的用户消息作为下一个Turn
- `steer(message)`：发送引导消息到最近的Step
- `inject(message)`：注入上下文到下一个pre-step

### 5.4 并发任务调度

工具调用的并发由工具管道管理：`isConcurrencySafe`返回true的工具可以并行执行。DSH还支持后台任务通过`ctx.jobs`服务注册。

## 6. 多模型接入层的抽象设计

### 6.1 Provider模式

每个模型提供商是一个Cordis插件，通过`ctx.llm`服务注册自己的适配器。多个实现可以在同一个上下文中注册，按名称查找。重复的provider id会被`DUPLICATE_ADAPTER`错误拒绝。

### 6.2 统一的ChatCompletion接口

`Message`是不可变的、带标识的角色/内容值，由`ContentBlock`数组组成：
- `TextBlock`：文本内容
- `ReasoningBlock`：推理/思考内容
- `ImageBlock`：图片附件
- `ToolCallBlock`：工具调用请求
- `ToolResultBlock`：工具调用结果

ContentBlockMap是**可合并扩展**的——插件可以通过TypeScript声明合并来添加新的块类型。

### 6.3 流式响应处理

`StreamChunk`是一个封闭的区分联合类型，支持多个块的交错增量传输：

```typescript
type StreamChunk =
  | { type: 'block-start'; index: number; blockType: ContentBlockType }
  | { type: 'text-delta'; index: number; text: string }
  | { type: 'reasoning-delta'; index: number; text: string }
  | { type: 'tool-call-delta'; index: number; id: CallId; name?: string; argumentsDelta: string }
  | { type: 'block-end'; index: number; block: ContentBlock }
  | { type: 'usage'; usage: TokenUsage }
  | { type: 'finish'; reason: FinishReason; replay?: ReplayEnvelope }
```

由于是封闭联合，添加新变体会导致所有消费端编译失败——这迫使开发者在添加新变体时必须处理所有消费者。

### 6.4 模型路由

Agent的`AgentOptions`中包含`provider`和`model`字段。路由结果记录在`request/context`事件中。适配器报告的上下文窗口大小用于后续的上下文压缩决策。

## 7. 安全沙箱机制

### 7.1 代码执行沙箱

沙箱是一个**能力接缝**，策略由`SandboxMode`控制：
- `read-only`：只允许读取
- `workspace-write`：允许在workspace目录和临时目录下写入
- `danger-full-access`：完全绕过沙箱限制

**静默的无限制透传对于confined策略是不合法的**——如果无法创建沙箱，必须抛出错误。

### 7.2 文件系统隔离

沙箱的文件系统隔离是per-call的。每次工具调用都携带完整的`SandboxExecutionPolicy`。workspaceRoot从调用session的不可变cwd中派生。

### 7.3 Landlock安全机制

在Linux上，DSH使用Landlock——Linux 5.13引入的内核安全模块——来实施文件系统访问控制。Landlock允许非特权进程限制自己的文件系统访问权限，即使进程被提权也无法突破这些限制。

### 7.4 跨平台安全后端

| 平台 | 机制 | 完整性 |
|---|---|---|
| Linux | Landlock + bubblewrap | full（新内核）/ partial（旧ABI） |
| macOS | Seatbelt（sandbox-exec） | full |
| Windows | ACL Restricted Token | partial |

每个后端有自己的拒绝方言（denial dialect）——Landlock产生`EACCES`，bubblewrap产生`EROFS`文本，Seatbelt产生`EPERM`。

---

## 第三部分：能力扩展与生态

## 8. 文件系统抽象层

### 8.1 虚拟文件系统

DSH的文件系统分为四个包：
- `dsh-fs`：Service Definition（`ctx.fs`）
- `dsh-fs-local`：本地磁盘Provider
- `dsh-fs-observation-policy`：观察策略插件
- `dsh-tool-fs`：模型面向的Consumer

关键设计是**目标身份与元数据的抽象**——`FsTarget`包含不透明的`targetKey`和用于显示的`displayPath`。文件版本通过不透明的`FsVersion`令牌管理。

### 8.2 Diff和Patch机制

`editText`是一个**提供者级别的原子操作**：验证版本 → 字面量匹配 → 原子替换写入。编辑结果包含编辑前后的完整内容，消费者可以计算上下文差异。

### 8.3 观察策略和新鲜度规则

默认行为是"先读后写/编辑"——防止基于过时信息的覆盖写入。通过三个waterfall事件控制：`fs/write-intent`、`fs/edit-intent`、`fs/observed`。

## 9. 终端和进程管理

### 9.1 终端抽象

DSH提供持久化的PTY会话，支持交互式Shell操作。核心接口`TerminalBackend`定义了如何启动终端会话和检测就绪状态。

### 9.2 进程生命周期

Shell执行经过`resolve()`转化为完全解析的`ShellExecSpec`。前台运行结果独立报告正交的结果：exitCode、signal、timedOut和aborted。

### 9.3 输出流处理

`CollectedOutput`在截断时保留尾部内容，完整流溢出到私有文件——确保模型面对的输出有界，同时不丢失数据。

## 10. Web UI的实时通信架构

### 10.1 前端模块化

30多个独立客户端模块，包括`client/connection`、`ui-conversation`、`ui-tool`、`ui-settings`、`ui-theme`等。

### 10.2 事件驱动的UI更新

前端通过WebSocket接收`session/event`事件流。每种事件类型有对应的UI渲染器。

### 10.3 Vite和HMR

结合Cordis的可逆效果机制，前端代码修改可在不刷新页面的情况下生效。

## 11. MCP和ACP协议适配

### 11.1 MCP协议

MCP客户端连接到任意MCP服务器，发现工具并自动转换为DSH的`ToolDefinition`。

### 11.2 ACP协议

ACP用于Agent之间的通信，使DSH Agent可以作为ACP服务器被外部客户端调用。

### 11.3 工具发现和调用

工具执行经过可扩展的waterfall管道：`tools/pre-execute` → 单调守卫 → `tools/execute` → `tools/post-execute` → `finalizeContent` → `tools/result`。

## 12. 技能系统的自演化能力

### 12.1 技能注册和发现

技能发现按6级优先级分层：project-dsh (100) → project-agents (200) → custom (300) → user-dsh (400) → user-agents (500) → bundled (600)。

### 12.2 动态技能创建

通过`ctx.skills.register()`可以运行时添加新技能，实现自演化。

### 12.3 技能组合

技能使用Markdown格式定义（`SKILL.md`），支持frontmatter元数据。通过目录分组实现组合。

## 13. 与其他Agent框架的深度技术对比

### vs LangGraph

| 维度 | LangGraph | DSH |
|---|---|---|
| 编排模型 | 有向图（状态机） | 事件驱动的插件组合 |
| 状态管理 | 图的全局状态对象 | 事件溯源的Session日志 |
| 扩展方式 | 自定义节点和边 | Cordis插件和服务注册 |
| 工具系统 | Python函数装饰器 | 类型化JSON Schema DSL |

### vs CrewAI

| 维度 | CrewAI | DSH |
|---|---|---|
| 核心模式 | 多Agent角色协作 | 单Agent + 子Agent委派 |
| 语言 | Python | TypeScript |
| 安全 | 无内置沙箱 | Landlock/Seatbelt/ACL |

### vs AutoGen

| 维度 | AutoGen | DSH |
|---|---|---|
| 核心模式 | 多Agent对话 | 单Agent + 工具调用循环 |
| 代码执行 | Docker容器 | 原生沙箱 |
| 可替换性 | 有限扩展点 | 所有组件可替换 |

### vs OpenAI Agents SDK

| 维度 | OpenAI Agents SDK | DSH |
|---|---|---|
| 模型支持 | OpenAI为主 | 多提供商 |
| 架构 | 单体SDK | 插件化monorepo |
| 部署 | OpenAI平台 | 自托管 |

## 14. 生产环境部署考量

### 14.1 启动和配置

通过Profile和Bundle管理不同部署配置。内置Profile包括`web`和`headless`。

### 14.2 监控和遥测

集成OpenTelemetry。Token计量通过`ctx.tokenMeter`服务管理。

### 14.3 测试体系

完善的测试体系：单元测试、快照测试、Web测试、E2E测试、性能测试、压力测试。

### 14.4 多平台支持

支持Linux、macOS和Windows。Node.js 22.19.0+，pnpm 11.7.0。

## 15. 未来展望和总结

### 15.1 Agent Teams

实验性支持Agent Teams——基于可继续子Agent的协调接缝，提供持久化的花名册、任务板和邮箱。

### 15.2 更多模型和协议支持

插件化架构使得添加新模型提供商和协议支持变得简单。

### 15.3 总结

DeepSeek Harness代表了Agent框架设计的一种新范式。它不是在功能层面做加法，而是在架构层面做乘法——通过Cordis依赖注入框架和"一切皆插件"的理念，将Agent框架的可组合性推向了极致。

DSH的核心洞察是：**Agent框架的价值不在于它内置了多少功能，而在于它为用户提供了多少自由度来定义自己的Agent行为**。模型是插件、工具是插件、存储是插件、沙箱是插件、UI是插件、甚至Agent循环本身也是插件——这种极致的模块化使得DSH不仅仅是一个Agent框架，更是一个构建Agent框架的框架。

正如DSH的README所说：**Model + Harness = Agent**。模型提供智能，Harness提供结构，两者的组合才是一个完整的Agent。DSH所做的，是把这个Harness做到尽可能通用、尽可能可组合、尽可能不设限。

---

> 本文基于 DeepSeek Harness 开源代码库深度分析撰写
> 项目地址：github.com/deepseek-ai/deepseek-harness | MIT License
> 技术栈：TypeScript | pnpm monorepo | Cordis DI | Vite | Vitest
