---
title: "DeepSeek Harness 技术深度解析：一切皆插件的Agent框架"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 技术深度解析"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 技术深度解析：一切皆插件的Agent框架
DeepSeek Harness 技术深度解析
一切皆插件的Agent框架 —— 从Cordis依赖注入到可组合智能体的完整架构剖析
2026年8月
TypeScript
Agent Framework
Open Source
Cordis
目录
第一部分：架构哲学与基础
引言：AI Agent框架的发展历程
DSH的诞生背景和设计理念
"一切皆插件"架构的哲学和实现
Cordis依赖注入框架深度剖析
第二部分：核心执行引擎
Agent执行引擎的核心机制
多模型接入层的抽象设计
安全沙箱机制
第三部分：能力扩展与生态
文件系统抽象层
终端和进程管理
Web UI的实时通信架构
MCP和ACP协议适配
技能系统的自演化能力
与其他Agent框架的深度技术对比
生产环境部署考量
未来展望和总结
第一部分：架构哲学与基础
1. 引言：AI Agent框架的发展历程
1.1 从ChatBot到Agent的演进
2022年底ChatGPT的发布标志着大语言模型（LLM）进入主流视野，但最初的交互模式极为简单——用户输入文本，模型返回文本，双方在一个无状态的对话窗口中来回交流。这种
ChatBot范式
的核心局限在于：模型无法主动执行任何操作，无法访问外部数据，也无法维持跨会话的任务状态。它是一个被动的问答机器，而非主动的问题解决者。
2023年，随着ReAct（Reasoning + Acting）论文的广泛传播，业界开始意识到LLM可以通过"思考-行动-观察"的循环来与外部世界交互。这一认知催生了第一代Agent框架：AutoGPT在2023年3月横空出世，一周内获得超过10万GitHub星标，其核心思想是让GPT-4自主分解任务、调用工具、观察结果并迭代执行。同期，LangChain从一个简单的LLM封装库迅速演化为包含Agent、工具链、记忆系统和文档检索的全栈框架。BabyAGI则提出了任务驱动自主Agent的概念，通过任务队列来组织和优先排序Agent的工作。
2024年是Agent框架的
分化之年
。LangGraph将图计算引入Agent编排，用状态机替代了简单的线性循环；CrewAI引入了多Agent协作的概念，让不同角色的Agent组成"团队"来完成复杂任务；AutoGen则专注于多Agent对话模式，允许Agent之间进行结构化的讨论和辩论。与此同时，OpenAI在2025年推出了Agents SDK，Anthropic推出了Claude Agent SDK，模型厂商开始从底层模型向上游的Agent框架延伸。
进入2025-2026年，Agent框架的竞争焦点从"能不能用"转向了"怎么用好"。DSH（DeepSeek Harness）正是在这一背景下诞生的，它代表了一种全新的思考方式：不追求功能的堆叠，而是追求架构的极致可组合性。
1.2 Agent框架的核心需求
一个成熟的AI Agent框架需要解决以下核心问题：
模型抽象
：不同厂商的API接口、参数格式、流式响应协议各不相同。框架必须提供统一的模型接入层，使得上层应用无需感知底层差异。更重要的是，模型切换应该是配置级别的变更，而不是代码级别的重构。
工具编排
：Agent的核心能力来自工具。框架需要定义工具的注册、发现、调用和结果处理的标准流程。工具不仅仅是API调用——文件操作、代码执行、终端命令、Web浏览都是工具的形态。
上下文管理
：Agent的对话历史会随交互不断增长，但模型的上下文窗口是有限的。框架需要管理会话状态、执行历史压缩（compaction）、维护持久化日志，并确保上下文在Agent重启后可恢复。
安全隔离
：Agent执行代码、操作文件系统、运行终端命令——这些操作如果不受限制，可能造成灾难性后果。框架必须提供沙箱机制，在文件系统、进程、网络层面实施细粒度的权限控制。
可观测性
：Agent的行为是非确定性的。框架需要提供完整的事件日志、工具调用追踪、模型请求/响应记录，使得开发者和用户能够理解和调试Agent的每一个决策。
可扩展性
：框架必须是开放的。用户应该能够添加新的模型适配器、新的工具、新的存储后端、新的UI组件，而无需修改框架核心代码。这种扩展性不是通过钩子函数或回调来实现的——它应该是架构本身的属性。
1.3 当前市场格局
当前Agent框架市场呈现出明显的分层格局。在底层，OpenAI的Agents SDK和Anthropic的Claude Agent SDK各自构建了与自家模型深度集成的Agent运行时。在中层，LangGraph以其图编排能力占据了复杂工作流的生态位，CrewAI则以多Agent协作为卖点吸引了大量用户。在上层，各种低代码Agent构建平台（如Dify、Coze）降低了Agent开发的门槛。
DSH选择了一条与众不同的路线——它不是在现有框架之上叠加功能，而是从依赖注入和插件化架构的根基重新设计Agent运行时。这一选择源于DeepSeek团队对现有框架痛点的深刻洞察：当框架的每个组件都是硬编码耦合的，扩展和替换的成本就会呈指数增长。
2. DSH的诞生背景和设计理念
2.1 DeepSeek AI的技术路线
DeepSeek AI自成立以来，其技术路线可以概括为"模型与工程并重"。在模型层面，DeepSeek-V2引入了Multi-head Latent Attention（MLA）和DeepSeekMoE架构，在保持性能的同时大幅降低了推理成本；DeepSeek-R1则通过强化学习训练出了强大的推理能力。在工程层面，DeepSeek较早地认识到：一个好的Agent框架不仅仅是模型能力的延伸，更是一个独立的软件工程挑战。
DSH的设计始于一个核心观察：
当前所有Agent框架都存在一个隐含假设——框架作者比用户更了解Agent应该如何工作
。这种假设导致了框架的僵化：LangChain的Chain/Agent模式无法轻易跳出循环；AutoGen的多Agent对话模式无法灵活地重新编排；即使是LangGraph，其图结构的定义方式也带有强烈的预设。
DSH的回应是：与其告诉用户Agent应该如何工作，不如提供一个可组合的基础设施（Harness），让用户自己定义Agent的行为。这就是"Harness"这个名字的由来——它不是Agent本身，而是承载Agent的底座。
2.2 "一切皆插件"的哲学来源
"一切皆插件"（Everything is a Plugin）并非DSH首创的概念。Eclipse IDE在2001年就以OSGi为基础构建了完全插件化的架构；Koishi（一个Discord/Telegram机器人框架）的作者Shigma同时也是Cordis框架的作者，他在Koishi中实践了"一切皆服务"的理念；VSCode的插件系统同样是"一切皆可扩展"的成功案例。
DSH的独特之处在于，它将这一理念推向了Agent框架的每一个角落。在DSH中，以下组件全部是可替换的插件：
模型适配器
：不仅不同厂商（OpenAI、Anthropic、DeepSeek、Google）是不同的插件，同一厂商的不同模型系列也可以是不同的插件
工具系统
：文件操作、Shell执行、Web搜索、代码运行——每个工具都是独立的插件
存储后端
：会话持久化、文件系统访问、附件管理——每个存储层都是可替换的插件
沙箱机制
：Landlock（Linux）、Seatbelt（macOS）、ACL（Windows）——每个平台的安全后端都是独立的插件
UI层
：Web界面的每个组件——对话视图、工具调用展示、设置面板——都是独立的客户端插件
Agent循环本身
：是的，就连Agent的思考-执行循环也是通过插件实现的
这种极致的插件化带来的直接后果是：DSH没有一个传统意义上的"核心"。它的"核心"仅仅是一个依赖注入容器和一组服务接口定义。所有的行为都是通过插件挂载到这个容器中来实现的。
2.3 与传统框架的差异
为了理解DSH的与众不同，我们可以将其与传统Agent框架做一个对比：
维度
传统框架（LangChain/AutoGen）
DSH
扩展方式
继承基类、注册回调、配置选项
注册Cordis服务、发布类型化事件
组件耦合
框架核心直接依赖具体实现
核心仅依赖服务接口，实现通过DI注入
运行时修改
通常需要重启
支持HMR热重载，插件可运行时装卸
类型安全
运行时类型检查为主
TypeScript编译期类型推导+运行时验证
事件系统
简单的回调/钩子
类型化事件，支持emit/waterfall/parallel/serial四种模式
撤销/回滚
不支持或手动实现
所有注册都是可逆效果（reversible effects）
作用域隔离
全局单例为主
每个Agent拥有独立的作用域（scope）
这种差异不仅仅是工程实现上的，更是设计哲学上的。传统框架的扩展点是"框架作者预设的"——他们决定了你可以在哪些地方插入自定义逻辑。DSH的扩展点是"架构本身提供的"——任何服务都可以被替换，任何事件都可以被拦截，任何行为都可以被重新组合。
3. "一切皆插件"架构的哲学和实现
3.1 什么是"一切皆插件"
在DSH的语境中，"一切皆插件"有三层递进的含义：
第一层：所有功能模块都是插件。
这是最直观的理解——模型适配器、工具、存储后端、UI组件都是独立的包，可以单独安装、升级和替换。这一层在很多框架中都有体现。
第二层：框架的基础设施也是插件。
Agent循环、会话管理、系统提示词组装——这些在其他框架中被视为"核心"的组件，在DSH中同样是插件。它们通过Cordis的Service机制注册，可以在不修改框架代码的情况下被替换。例如，DSH的默认Agent循环（agent-loop）是一个具体的插件实现；如果你想用完全不同的推理策略（比如基于规划的执行模式），你可以写一个新的agent-loop插件来替换它。
第三层：插件的组合方式也是可配置的。
DSH引入了Profile（配置文件）和Bundle（分发包）的概念。一个Profile定义了要加载哪些Bundle，每个Bundle又是一组Cordis配置行和它们挂载的代码。通过不同的Profile组合，同一套代码可以表现为完全不同的产品形态：Web应用、命令行工具、无头Agent、API服务器。
3.2 插件化的层次
DSH的插件化覆盖了以下所有层次：
模型层（Model Layer）
DSH支持的模型提供商包括OpenAI、Anthropic、DeepSeek、Google Gemini、Mistral、AWS Bedrock等。每个提供商是一个独立的LLM适配器插件，注册在
ctx.llm
服务上。适配器需要实现统一的
LlmAdapter
接口，包括
stream()
方法用于流式请求和
capabilities
属性用于声明支持的特性。模型切换只需修改配置中的provider和model字段，无需任何代码变更。
工具层（Tool Layer）
工具注册在
ctx.tools
服务上。每个工具是一个
ToolDefinition
，包含名称、描述、参数Schema、输出Schema、执行函数和可选的UI呈现器。工具的参数和输出使用统一的JSON Schema DSL定义，支持类型推导——TypeScript编译器可以从Schema定义自动推导出参数和返回值的类型。DSH内置了数十个工具，包括文件读写、Shell执行、Web搜索、代码运行、技能调用等。
存储层（Storage Layer）
会话持久化、文件系统访问、附件管理都是可替换的服务。
ctx.sessions
管理会话日志，
ctx.fs
提供文件系统抽象，附件系统通过
ctx.attachment
服务管理。每个服务都可以有多个后端实现——本地磁盘、远程存储、沙箱内存储都是可能的选择。
UI层（UI Layer）
DSH的Web前端由30多个独立的客户端模块组成，每个模块是一个Cordis插件。对话视图（
ui-conversation
）、工具调用展示（
ui-tool
）、设置面板（
ui-settings
）、侧边栏（
ui-sidebar
）、主题系统（
ui-theme
）——每个UI组件都可以独立替换或扩展。前端使用Vite构建，支持HMR热重载。
调度逻辑层（Scheduling Layer）
Agent的执行调度——何时开始新的turn、何时执行工具、何时压缩上下文——都是通过事件和插件组合实现的，而非硬编码在框架核心中。
agent/pre-step
、
agent/request
、
agent/turn-stopping
等事件提供了多个拦截点，插件可以通过这些事件来修改Agent的行为。
3.3 极致模块化的利弊分析
优势：
可替换性
：任何组件都可以被替换，这使得DSH可以适应极其多样的部署场景
可测试性
：每个模块都是独立的，可以单独测试，也可以通过注入mock服务来进行集成测试
团队协作
：不同的团队可以并行开发不同的模块，只要接口定义不变就不会互相影响
增量升级
：可以单独升级某个模块而不影响其他模块
社区贡献
：第三方开发者可以轻松地为DSH编写插件，无需深入理解框架内部实现
挑战：
认知负担
：新开发者面对40+个包会感到困惑，不知道从哪里开始
接口设计
：每个服务接口的设计都需要极其谨慎，因为一旦发布就很难修改
调试复杂度
：当问题跨越多个插件时，追踪问题的根源变得更加困难
初始化开销
：依赖注入容器的启动和解析需要一定的时间开销
文档负担
：每个子系统都需要完整的文档，文档维护成本很高
DSH通过以下措施来缓解这些挑战：详细的架构文档（docs/目录下有50+篇文档）、自动生成的Cordis API目录、完善的Agent Note系统（记录设计决策和架构演变）、以及丰富的Cookbook教程。
4. Cordis依赖注入框架深度剖析
4.1 IoC容器的设计
Cordis是DSH的根基框架，由Koishi（一个流行的聊天机器人框架）的作者Shigma设计。其设计思想在论文《A Programming Paradigm for Spatiotemporal Composability》中有详细阐述。Cordis的核心理念可以用五个要点概括：
插件是实现Service接口的对象。
一个插件可以是一个带有
inject
和
apply(ctx)
字段的函数，也可以是一个
Service
子类。Cordis负责将插件的生命周期挂载到当前上下文中。
上下文（Context）是服务的仓库。
一个服务通过
ctx.<key>
的形式声明自己在上下文中的位置，如
ctx.tools
、
ctx.llm
、
ctx.sessions
。其他插件通过key来发现服务，而不是导入具体的实现类。
通过
inject
声明服务依赖。
一个声明了所需服务的插件会等待这些服务就绪后才加载。这意味着加载顺序是通过服务依赖关系自动推导的，而不是手动编排的。例如：
// 一个需要tools和llm服务的插件
const myPlugin: Plugin = {
  inject: ['tools', 'llm'],
  apply(ctx) {
    // 此时ctx.tools和ctx.llm已经就绪
    ctx.tools.register({ ... })
  }
}
类型化事件用于通信。
服务通过TypeScript的声明合并（declaration merging）来声明事件名称，然后通过
emit
、
waterfall
、
parallel
或
serial
来分发事件。每种分发模式有不同的语义：
模式
是否等待
分发顺序
有返回值
用途
emit
否
注册顺序
否
通知观察者
waterfall
否
注册顺序
是
中间件链（around-middleware）
parallel
是
并行
否
并行扇出
serial
是
注册顺序
是
有序执行
注册是可逆效果（Reversible Effects）。
所有通过
ctx.effect()
或
ctx.on()
安装的注册——提示词段落、工具Schema、适配器、提供者、监听器——在插件卸载时都会自动撤销。这是DSH支持HMR热重载的基础。
4.2 服务生命周期
Cordis中的服务有明确的生命周期状态机。一个服务从"未注册"开始，经过"等待依赖"、"就绪"、"活跃"等状态，最终在插件卸载时进入"已销毁"状态。关键的生命周期事件包括：
fork
：当一个插件被声明时，Cordis创建一个新的上下文（Context）来承载它
inject
：检查插件声明的依赖是否全部就绪
apply
：所有依赖就绪后，调用插件的apply函数
dispose
：插件卸载时，Cordis自动撤销所有通过该插件安装的效果
这个生命周期保证了一个重要的不变式（invariant）：
一个插件的效果永远不会在其自身被卸载后仍然存在
。这对于HMR场景至关重要——当开发者修改了某个插件的代码并保存时，Cordis会卸载旧版本的插件（撤销其所有效果），然后加载新版本的插件（安装新的效果）。
4.3 作用域和继承
Cordis的作用域系统是DSH实现per-agent隔离的基础。每个上下文（Context）都可以创建子上下文，子上下文继承父上下文的所有服务，但可以在自己的作用域内注册额外的服务或覆盖父上下文的服务。
在DSH中，这一机制被用于Agent的隔离。每个Agent在创建时会获得自己的作用域（
agent.ctx
），这个作用域继承了全局的服务（模型适配器、工具注册表等），但可以注册Agent特有的服务——比如自定义的工具集合、不同的模型配置、特定的系统提示词。
DSH在其核心包
packages/core/scope
中定义了作用域注册原语（
createScope
/
scopeOf
/
scopeTarget
），这是一个无依赖的纯库，位于模块图的最底层，确保session和system-prompt等包可以安全地使用它而不产生循环依赖。
4.4 与NestJS/InversifyJS的对比
特性
NestJS
InversifyJS
Cordis
定位
Web应用框架
通用DI容器
插件化运行时框架
装饰器
重度依赖装饰器
使用装饰器
不使用装饰器（纯函数/对象）
生命周期管理
模块级别的onModuleInit/Destroy
手动管理
自动效果撤销
HMR支持
不原生支持
不支持
核心特性
事件系统
简单的EventEmitter
无内置事件
类型化事件，四种分发模式
作用域
Request scope
自定义scope
层次化scope，per-agent隔离
运行时修改
不支持
有限支持
完全支持（Cordis config overlay）
配置管理
模块配置
手动绑定
YAML配置 + JS表达式插值
Cordis最大的差异化特征是其
时空可组合性
（Spatiotemporal Composability）——"空间"指的是作用域层次结构中的位置，"时间"指的是插件的加载和卸载时序。这两个维度的组合使得Cordis能够在运行时动态地重组Agent的行为，这是传统DI框架无法做到的。
关键设计决策
DSH的Cordis配置使用YAML格式（
cordis.yml
），支持
!!js
表达式节点。这意味着配置文件不仅仅是静态的声明——它可以包含动态逻辑，根据环境变量、运行时状态来决定加载哪些插件。这在多Profile场景中尤其有用：同一套代码通过不同的cordis.yml配置，可以表现为Web应用、CLI工具或无头Agent。
Cordis Loader解析配置中的
config
字段（在声明的注入激活后，针对该插件上下文——
ctx.serviceName
）和
disabled
字段（在每次挂载决策时，针对加载器上下文）。Include机制保留嵌套的行表达式直到目标激活。其他条目元数据保持字面量。这种设计使得环境可以通过overlay来选择性地启用或禁用插件。
第二部分：核心执行引擎
5. Agent执行引擎的核心机制
5.1 Turn和Step：执行的基本单元
DSH的Agent执行循环建立在两个核心概念之上：
Turn
（轮次）和
Step
（步骤）。一个Turn代表Agent处理一个用户输入的完整过程；一个Step代表一次模型请求加上该请求触发的所有工具调用。一个Turn可以包含零个或多个Step——当模型请求工具调用后，工具的结果需要再次发送给模型，这就产生了下一个Step。
整个执行流程可以概括为：
sequenceDiagram
    participant U as 用户输入
    participant D as Driver
    participant H as Hooks
    participant P as ctx.systemPrompt
    participant L as ctx.llm
    participant T as ctx.tools
    participant S as Session 日志

    U->>D: 唤醒 Driver
    D->>S: turn/start
    D->>D: claim pending input
    D->>H: agent/pre-step (waterfall)
    H-->>D: enter(messages)

    D->>S: step/start
    D->>S: user/message
    D->>P: system-prompt/assemble
    D->>L: agent/request → llm/stream
    L-->>D: StreamChunk* (text/tool-call)
    D->>S: assistant/chunk* → assistant/message

    loop 每个工具调用
        D->>S: tool/call
        D->>T: tools/pre-execute → execute → post-execute
        T-->>D: tool/result
        D->>S: tool/result
    end

    D->>S: step/end

    alt 还有 pending input
        D->>D: 进入下一个 step
    else 自然停止
        D->>H: agent/turn-stopping
    end

    D->>S: turn/end
这个流程中的每个阶段都是一个事件扩展点。
agent/pre-step
是一个waterfall事件，监听者可以修改即将发送给模型的消息，或者直接拒绝这个Step。
agent/request
和
llm/stream
也是waterfall事件，允许插件拦截和修改模型请求。
tools/pre-execute
、
tools/execute
、
tools/post-execute
构成了工具执行的三层管道。
5.2 Session管理和上下文传播
DSH的Session不仅仅是一个对话历史——它是一个
追加式日志
（append-only log），记录了Agent交互的每一个事实。这个日志是模型可见上下文的唯一来源（single source of truth）。模型的对话历史是从日志中
派生
（derived）的，而不是单独存储的。
Session日志中的事件类型包括：
turn/start
和
turn/end
：标记每个Turn的开始和结束
step/start
和
step/end
：标记每个Step的开始和结束
user/message
：用户输入消息（包括直接输入和注入的上下文）
assistant/chunk
：模型响应的原始流式块，保留token级别的回放保真度
assistant/message
：组装完成的助手消息，包含使用统计（token usage）
tool/call
和
tool/result
：工具调用和结果
request/header
：完整的请求信封（系统提示、工具Schema、模型配置）
request/context
：路由元数据（provider、model、contextWindow）
这种事件溯源（event-sourcing）架构带来了几个关键优势：
可重建性
：任何时刻的模型上下文都可以从日志中完整重建。这意味着Agent可以在崩溃后从持久化的日志中恢复，而不会丢失任何状态。
可分叉性
：从一个会话日志中可以派生出多个分叉（fork），每个分叉拥有自己的后续日志，但共享之前的完整历史。
可遥测性
：所有事件都可以被遥测系统消费，用于监控、分析和调试。
一个重要的不变式是：
模型可见即已记录
（Model-visible means logged）。任何到达模型请求的内容都必须能够从日志中重建。运行时不变式断言会验证这一点——如果一个插件试图注入模型可见的内容但没有将其记录到日志中，运行时会抛出错误。
5.3 Inbox和消息路由
DSH的Agent拥有一个双列表Inbox系统——
next-turn
和
next-step
。普通用户消息进入
next-turn
，成为下一个Turn的输入；注入的上下文（如文件变更通知、技能内容、定时任务通知）进入
next-step
，等待被下一个Step的
agent/pre-step
瀑布消费。
Agent的公开API提供了三种消息发送方式：
followup(message)
：发送一个完整的用户消息作为下一个Turn
steer(message)
：发送引导消息到最近的Step
inject(message)
：注入上下文到下一个pre-step，不唤醒驱动器
这种分离使得多个独立的上下文源（文件监听器、定时任务、子Agent报告）可以同时向Agent注入信息，而不会互相干扰或产生竞态条件。
5.4 并发任务调度
DSH的Agent驱动器（driver）在同一时间只处理一个活动（activity），但这不意味着系统是单线程的。工具调用的并发由工具管道管理：
isConcurrencySafe
返回true的工具可以并行执行。驱动器维护一个有界的滚动池（bounded rolling pool），在每个Step中对工具调用进行分类（串行 vs 并行），并在开始前重新分类。
此外，DSH支持后台任务（background jobs）通过
ctx.jobs
服务注册。
job_start
、
job_collect
、
job_stop
等工具允许Agent启动长时间运行的任务，在后续交互中收集结果或停止任务。这些任务与Agent的主循环解耦，不会阻塞用户交互。
6. 多模型接入层的抽象设计
6.1 Provider模式
DSH的LLM接入层采用了注册表模式（Registry Pattern）。每个模型提供商是一个Cordis插件，通过
ctx.llm
服务注册自己的适配器。注册时需要声明：
Provider标识
：唯一的提供商名称（如
openai
、
anthropic
、
deepseek
）
Capabilities
：适配器支持的特性（是否支持流式、是否支持工具调用、是否支持多模态等）
stream()方法
：接收统一的模型请求，返回
StreamChunk
流
DSH的LLM适配器注册表遵循与subagent注册表相同的模式——多个实现可以在同一个上下文中注册，按名称查找。这与bash执行器（只允许一个实现）形成对比。重复的provider id会被
DUPLICATE_ADAPTER
错误拒绝。
6.2 统一的ChatCompletion接口
DSH定义了统一的消息模型：
Message
是不可变的、带标识的角色/内容值。消息由
ContentBlock
数组组成，支持以下类型：
TextBlock
：文本内容
ReasoningBlock
：推理/思考内容（区别于可见文本）
ImageBlock
：图片附件
ToolCallBlock
：工具调用请求（id、name、raw JSON arguments）
ToolResultBlock
：工具调用结果
ContentBlockMap是
可合并扩展
的——插件可以通过TypeScript声明合并来添加新的块类型，但新类型必须获得适配器、UI和压缩（compaction）的支持。每个新模态的加入是一个协调变更，而不是一个简单的添加。
6.3 流式响应处理
DSH的流式协议定义了
StreamChunk
——一个
封闭
的区分联合类型（closed discriminated union）。每个chunk通过
index
字段关联到特定的块，支持多个块的交错增量传输（例如文本和工具调用可以交错进行）：
type StreamChunk =
  | { type: 'block-start'; index: number; blockType: ContentBlockType }
  | { type: 'text-delta'; index: number; text: string }
  | { type: 'reasoning-delta'; index: number; text: string }
  | { type: 'tool-call-delta'; index: number; id: CallId; name?: string; argumentsDelta: string }
  | { type: 'block-end'; index: number; block: ContentBlock }
  | { type: 'usage'; usage: TokenUsage }
  | { type: 'finish'; reason: FinishReason; replay?: ReplayEnvelope }
block-end
携带组装完成的块，消费者无需自己重新组装增量。
finish
携带可选的
ReplayEnvelope
——适配器私有的无损JSON状态，用于回放成功的响应。这个状态被存储在助手消息的model source中，只有拥有相同provider和model的适配器实例才能访问它。
由于StreamChunk是封闭联合，添加一个新的变体会导致所有消费端编译失败——这迫使开发者在添加新变体时必须处理所有消费者。
switch
语句以
assertNever
结尾，确保编译期的完备性检查。
6.4 模型路由和负载均衡
DSH支持在请求级别进行模型路由。Agent的
AgentOptions
中包含
provider
和
model
字段，决定了该Agent使用哪个提供商和哪个模型。路由的结果被记录在
request/context
事件中，包括provider、model和contextWindow。
当适配器报告了上下文窗口大小时，DSH会将其记录下来，用于后续的上下文压缩决策。每个请求的完整信封（系统提示、工具Schema、模型配置）通过
request/header
事件记录，确保请求的可重建性。
7. 安全沙箱机制
7.1 代码执行沙箱
DSH的沙箱系统是一个
能力接缝
（Capability Seam），分为三个角色：
Service Definition
：
ctx.sandbox
定义了沙箱的接口
Service Provider
：
dsh-sandbox-local
提供了平台特定的实现
Consumer
：
dsh-bash-sandbox
和
dsh-pwsh-sandbox
使用沙箱来包装Shell命令
沙箱的策略由
SandboxMode
控制，仅管理文件系统效果：
read-only
：只允许读取（POSIX后端额外授予
/dev/null
的写入权限）
workspace-write
：允许在workspace目录和临时目录下写入
danger-full-access
：完全绕过沙箱限制
只有前两种模式可以发送给沙箱提供者。
danger-full-access
的消费者直接使用原始命令，不调用
ctx.sandbox
。
静默的无限制透传对于confined策略是不合法的
——如果无法创建沙箱，必须抛出
SandboxUnavailableError
而不是默默地放弃限制。
7.2 文件系统隔离
沙箱的文件系统隔离是per-call的。每次工具调用都携带一个完整的
SandboxExecutionPolicy
，包含mode、workspaceRoot和sessionId。这意味着：
同一个session中的不同工具调用可以有不同的沙箱策略
并发的session可以有不同的workspace边界
用户审批的升级重试（escalated retry）是一次新的策略调用
workspaceRoot从调用session的不可变cwd中派生。路径在词汇归一化之前通过文件系统语义进行规范化，所以包含
symlink/..
的cwd能正确标识实际运行目录。
7.3 Landlock安全机制
在Linux上，DSH使用Landlock——Linux 5.13引入的内核安全模块——来实施文件系统访问控制。Landlock允许非特权进程限制自己的文件系统访问权限，即使进程被提权也无法突破这些限制。
DSH的Landlock实现在
native/landlock-run/
目录中，是一个独立的可执行文件。它作为沙箱的runner，包装要执行的命令并设置Landlock规则。Landlock规则在exec之前生效，因此即使是被包装的进程fork出的子进程也受到同样的限制。
DSH的CI系统包含专门的Landlock测试流水线（
landlock-run.yml
和
landlock-run-release.yml
），确保Landlock后端在不同内核版本上的行为一致性。
7.4 跨平台安全后端
DSH在三个平台上提供了不同的安全后端：
平台
机制
实现包
完整性
Linux
Landlock + bubblewrap
dsh-sandbox-local
full（新内核）/ partial（旧ABI）
macOS
Seatbelt（sandbox-exec）
dsh-sandbox-local
full
Windows
ACL Restricted Token
dsh-sandbox-local
partial（Everyone/hard-link边界）
SandboxEnforcement
类型区分
full
和
partial
两种执行完整性。
partial
意味着后端或旧内核ABI只能治理策略承诺的文件效果的子集。消费者可以检查这个值来决定是否接受不完全的保护。
每个后端有自己的拒绝方言（denial dialect）——Landlock产生
EACCES
，bubblewrap产生
EROFS
文本，Seatbelt产生
EPERM
。沙箱包装的命令携带
denialSignatures
，消费者使用这些签名来区分"沙箱正常工作并拒绝了操作"和"命令本身失败"。
第三部分：能力扩展与生态
8. 文件系统抽象层
8.1 虚拟文件系统
DSH的文件系统分为四个包：
dsh-fs
：Service Definition，拥有
ctx.fs
和原子文本操作
dsh-fs-local
：本地磁盘的Service Provider实现
dsh-fs-observation-policy
：观察策略插件，记录文件的存在/不存在并添加新鲜度规则
dsh-tool-fs
：模型面向的Consumer，直接执行读/写/编辑调用并渲染窗口
文件系统接缝的关键设计是
目标身份与元数据的抽象
。每个操作首先将用户提供的路径解析为不透明的后端目标（
FsTarget
）——包含一个不透明的
targetKey
和一个用于显示的
displayPath
。消费者不应该解析
targetKey
或假设它是本地绝对路径——对于远程后端，它可能是URI或文件ID。
文件版本通过不透明的
FsVersion
令牌管理。本地后端从高精度的stat身份和新鲜度字段中派生版本令牌；远程后端可能使用修订ID。策略层存储这些版本令牌用于过时检查，消费者不应该解释它们。
8.2 Diff和Patch机制
DSH的文件编辑操作
editText
是一个
提供者级别的原子操作
，而不是"读取+写入"的组合。它的执行流程是：
如果提供了版本守卫，先验证期望的版本（过时则报告
FS_STALE_VERSION
）
执行字面量匹配（literal matching）
原子地应用替换并写入
匹配、行尾处理、过时检查和原子替换都在一个变更关键区内完成。编辑结果（
FsEditOutcome
）包含编辑前后的完整内容，消费者可以从中计算上下文差异（contextual diff）。
写入操作
writeText
支持两种守卫模式：
createIfAbsent
（仅在文件不存在时创建）和
replaceIfVersion
（仅在版本匹配时替换）。这保证了并发修改的安全性。
8.3 观察策略和新鲜度规则
dsh-fs-observation-policy
通过事件（而非服务）来改变文件操作的行为。它监听三个waterfall事件：
fs/write-intent
：写入意图决策（单slot waterfall，first-wins）
fs/edit-intent
：编辑意图决策（单slot waterfall，first-wins）
fs/observed
：记录一次文件观察（fire-and-forget，emit）
默认行为是"先读后写/编辑"——在写入或编辑之前先读取文件的当前状态，记录版本令牌，然后在操作时使用版本守卫。这防止了基于过时信息的覆盖写入。
9. 终端和进程管理
9.1 终端抽象
DSH的终端系统提供了持久化的PTY（伪终端）会话。与普通的Shell执行不同，PTY会话是交互式的——它们保持一个活的Shell进程，支持连续的命令执行、环境变量累积和输出滚动。
终端系统的核心接口是
TerminalBackend
，它定义了如何启动一个终端会话和检测就绪状态。
TerminalBackendSession
是一个后端拥有的活会话，提供以下操作：
startSend()
：启动一个独占的发送操作（同一时间每个会话只能有一个活跃的发送）
read()
：从保留的滚动缓冲区读取一个有界页面
signal()
：向验证过的前台进程组发送信号
status()
：观察顶层进程状态
close()
：幂等地关闭捕获的进程树并等待静默
9.2 进程生命周期
每个Shell执行（
ShellExecRequest
）经过
resolve()
方法转化为完全解析的
ShellExecSpec
——填入默认的工作目录、超时、输出大小限制等。前台运行的结果（
ShellRunResult
）独立报告正交的结果：exitCode、signal、timedOut和aborted——一个进程可以同时超时并且退出码为0（如果它捕获了信号）。
9.3 输出流处理
输出流是
CollectedOutput
——可能被截断的文本加上恢复信息。截断时，
text
字段是
尾部
内容，完整的流溢出到一个私有文件。这确保了模型面对的输出是有界的，同时不丢失任何数据。
10. Web UI的实时通信架构
10.1 前端模块化
DSH的Web前端由30多个独立的客户端模块组成，每个模块是一个Cordis插件。这种极端的模块化使得前端可以像后端一样灵活地组合和替换。核心模块包括：
client/connection
：WebSocket连接管理
client/hmr
：开发时的热重载支持
client/runtime
：客户端运行时状态管理
ui-conversation
：对话视图
ui-tool
：工具调用展示
ui-settings
：设置面板
ui-theme
：主题系统
ui-sidebar
：侧边栏
ui-subagent
：子Agent管理
10.2 事件驱动的UI更新
前端通过WebSocket接收来自后端的
session/event
事件流。每个事件类型都有对应的UI渲染器——
assistant/chunk
事件驱动流式文本渲染，
tool/call
和
tool/result
事件驱动工具调用卡片的展示和更新，
agent/status
事件控制加载状态的显示。
DSH的对话视图使用
ConversationNodeDefinition
来注册新的聊天节点类型。每个节点类型有一个keyed renderer，可以根据事件数据选择不同的渲染方式。这使得同一个对话流可以展示文本消息、工具调用、代码执行结果、子Agent报告等不同类型的内容。
10.3 Vite和HMR
DSH使用Vite作为前端构建工具，支持开发时的模块热替换（HMR）。结合Cordis的可逆效果机制，前端代码的修改可以在不刷新页面的情况下生效——旧的UI组件被卸载（其效果被撤销），新的组件被加载并安装新的效果。
11. MCP和ACP协议适配
11.1 MCP协议概述
MCP（Model Context Protocol）是Anthropic提出的标准协议，用于模型与外部工具和数据源之间的通信。DSH通过
packages/mcp/
目录下的包实现了MCP适配层。MCP客户端可以连接到任意的MCP服务器，发现其提供的工具，并将这些工具注册到DSH的工具注册表中。
每个MCP服务器的工具在注册时会被自动转换为DSH的
ToolDefinition
，包括名称、描述、参数Schema和执行函数。MCP工具的执行通过MCP协议的call_tool消息完成，结果被转换回DSH的工具结果格式。
11.2 ACP协议
ACP（Agent Communication Protocol）是
@agentclientprotocol/sdk
实现的协议，用于Agent之间的通信。DSH通过
packages/acp/
包支持ACP，使得DSH Agent可以作为ACP服务器被外部客户端（如其他Agent或应用）调用。
ACP Agent的示例配置在
examples/acp-agent/
目录中，展示了多种配置模式：基本模式、高级模式、代码模式、子Agent模式等。每个示例都通过独立的
cordis.yml
文件定义了插件组合。
11.3 工具发现和调用
DSH的工具系统通过
ctx.tools
服务管理。工具注册是受信任的同进程契约——注册表借用类型化的定义作为只读输入，要求
output
字段，验证其原始Schema，并检查语义要求（如正有限的
timeoutMs
）。
schemas()
方法在构建请求时构造模型面向的投影，因此执行和呈现共享一个解析后的定义。
工具执行经过一个可扩展的waterfall管道：
tools/pre-execute
：可重排序的允许/拒绝/询问waterfall
注册的单调守卫（monotonic guards）
tools/execute
：环绕式分发包装器
tools/post-execute
：检查/替换结果
可选的定义拥有者
finalizeContent
tools/result
：不可变的权威结果
12. 技能系统的自演化能力
12.1 技能注册和发现
DSH的技能系统是一个独立的能力接缝，分为四个包：
dsh-skill
：Service Definition（
ctx.skills
）
dsh-skill-filesystem
：本地文件系统的Service Provider
dsh-skill-badge
：可选的打包徽章Provider
dsh-tool-skill
：模型面向的Consumer，拥有初始和替换目录以及模型面对的
skill
工具
技能发现是分层的，按照优先级从高到低：
排名
来源
根目录
100
project-dsh
<projectRoot>/.dsh/skills
200
project-agents
<projectRoot>/.agents/skills
300
custom
配置的customSkillDirs
400
user-dsh
<dshHome>/skills
500
user-agents
<agentsHome>/skills
600
bundled
配置的bundledSkillDir
技能注册表是
host+per-scope分层
的——全局层的注册和仓库插件的注册在全局层，Agent预设的插件在该预设的层中，读取时合并两层，最近层的同名条目胜出。
12.2 动态技能创建
DSH支持运行时技能注册——通过
ctx.skills.register()
方法可以动态地添加新的技能。返回的disposer可以移除该贡献并使发现缓存失效。这使得Agent可以在执行过程中创建新的技能，实现自演化。
12.3 技能组合
技能使用Markdown格式定义（
SKILL.md
），支持frontmatter元数据。每个技能包含名称、描述、使用条件、调用策略（模型可调用/用户可调用）和内容体。技能之间的组合通过目录分组实现——一个技能bundle可以包含多个相关技能的目录。
13. 与其他Agent框架的深度技术对比
13.1 vs LangGraph
维度
LangGraph
DSH
编排模型
有向图（状态机）
事件驱动的插件组合
状态管理
图的全局状态对象
事件溯源的Session日志
扩展方式
自定义节点和边
Cordis插件和服务注册
并发
图的并行分支
工具级别的并发池 + 后台任务
持久化
可选的checkpoint
内置的JSONL持久化
工具系统
基于Python函数装饰器
类型化的JSON Schema DSL + 执行管道
UI
LangGraph Studio（独立产品）
内置Web UI（模块化客户端插件）
13.2 vs CrewAI
维度
CrewAI
DSH
核心模式
多Agent角色协作
单Agent + 子Agent委派
语言
Python
TypeScript
模型支持
通过LangChain/LiteLLM
原生适配器注册
安全
无内置沙箱
Landlock/Seatbelt/ACL
事件系统
简单的回调
类型化事件，四种模式
适用场景
角色分工明确的团队任务
通用的单Agent/子Agent场景
13.3 vs AutoGen
维度
AutoGen
DSH
核心模式
多Agent对话
单Agent + 工具调用循环
通信模型
Agent之间的结构化消息
事件溯源的Session日志
代码执行
Docker容器
原生沙箱（Landlock/Seatbelt/ACL）
扩展性
自定义Agent类型
所有组件可替换（一切皆插件）
状态管理
对话历史
事件溯源 + 持久化日志
13.4 vs OpenAI Agents SDK
维度
OpenAI Agents SDK
DSH
模型支持
OpenAI模型为主
多提供商（OpenAI/Anthropic/DeepSeek/Google/Mistral）
架构
单体SDK
插件化monorepo（40+包）
工具系统
函数工具 + 内置工具
类型化Schema + 可扩展管道
沙箱
代码解释器（云端）
原生沙箱（本地+远程）
可替换性
有限的扩展点
所有组件可替换
部署
OpenAI平台
自托管
14. 生产环境部署考量
14.1 启动和配置
DSH通过Profile和Bundle系统来管理不同的部署配置。内置的Profile包括
web
（Web应用）和
headless
（无头模式）。每个Profile列出要堆叠的Bundle：
dsh-base
：基础层——模型适配器、工具、持久化、沙箱、审批策略、设置、凭证、遥测
dsh-web-app
：浏览器应用层
dsh-headless
：无服务器的一次性运行器
层的叠加顺序：Profile中列出的Bundle顺序 → Profile的
cordis.patch.yml
→ 用户home级别的patch →
--patch
覆盖层。每个patch通过id定位配置行并替换其完整配置，或插入新行。
14.2 监控和遥测
DSH集成了OpenTelemetry进行可观测性追踪。依赖包括
@opentelemetry/api
、
@opentelemetry/sdk-logs
、
@opentelemetry/sdk-trace
、
@opentelemetry/sdk-metrics
等。Token计量通过
ctx.tokenMeter
服务管理，每个助手消息携带
usage
字段记录token消耗。
14.3 测试体系
DSH拥有完善的测试体系：
单元测试
：Vitest运行的常规测试
快照测试
：独立的vitest配置（
vitest.snapshot.config.ts
），支持录制和回放
Web测试
：浏览器环境的集成测试
E2E测试
：端到端测试
性能测试
：Web UI的性能基准
压力测试
：高负载场景的稳定性测试
14.4 多平台支持
DSH支持Linux、macOS和Windows三个平台。CI系统包含专门的Windows测试流水线（
ci-windows-blocking
、
ci-windows-complete
、
ci-windows-observational
）。Node.js版本要求22.19.0或24.0.0以上，使用pnpm 11.7.0作为包管理器。
15. 未来展望和总结
15.1 Agent Teams
DSH已经在实验性地支持Agent Teams——一个基于可继续子Agent的协调接缝。Agent Teams提供了持久化的花名册（roster）、任务板（taskboard）和邮箱（mailbox），允许多个Agent在一个协调框架下协作。这一特性通过
ctx.agentTeams
服务提供，目前是私有的opt-in。
15.2 更多模型和协议支持
DSH的插件化架构使得添加新的模型提供商和协议支持变得简单。未来可以预见的支持包括更多的模型厂商、更多的工具协议（如MCP的后续版本）、以及更多的部署目标（如容器化、边缘设备等）。
15.3 总结
DeepSeek Harness代表了Agent框架设计的一种新范式。它不是在功能层面做加法，而是在架构层面做乘法——通过Cordis依赖注入框架和"一切皆插件"的理念，将Agent框架的可组合性推向了极致。
DSH的核心洞察是：
Agent框架的价值不在于它内置了多少功能，而在于它为用户提供了多少自由度来定义自己的Agent行为
。模型是插件、工具是插件、存储是插件、沙箱是插件、UI是插件、甚至Agent循环本身也是插件——这种极致的模块化使得DSH不仅仅是一个Agent框架，更是一个构建Agent框架的框架。
在当前AI Agent技术快速演进的背景下，DSH的插件化架构为其提供了强大的适应能力。当新的模型出现时，只需编写一个新的适配器插件；当新的安全机制出现时，只需实现一个新的沙箱后端；当新的交互模式出现时，只需注册新的UI模块。这种适应性，加上TypeScript的类型安全、Vitest的完善测试、和详细的架构文档，使得DSH有潜力成为Agent开发领域的重要基础设施。
正如DSH的README所说：Model + Harness = Agent。这个等式的含义是——模型提供智能，Harness提供结构，两者的组合才是一个完整的Agent。DSH所做的，是把这个Harness做到尽可能通用、尽可能可组合、尽可能不设限。
本文基于 DeepSeek Harness 开源代码库深度分析撰写 | 项目地址: github.com/deepseek-ai/deepseek-harness | MIT License
技术栈: TypeScript | pnpm monorepo | Cordis DI | Vite | Vitest
查看配套架构图与时序图集 →