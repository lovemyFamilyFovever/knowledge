---
title: "DSH 架构图与时序图集"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 技术深度解析"
collected: "2026-09-05"
status: "imported"
---

DSH 架构图与时序图集
DeepSeek Harness 架构图与时序图集
配合《DeepSeek Harness 技术深度解析》文章使用的 Mermaid 图表代码与渲染预览
图表目录
DSH 整体架构分层图
Cordis 依赖注入容器原理
Agent Turn/Step 生命周期时序图
工具执行管道流程图
能力接缝模式图
多模型接入层架构图
沙箱安全架构图
Session 事件溯源架构图
Profile/Bundle 组合图
技能系统发现与注册流程
1
DSH 整体架构分层图
展示 DSH 从底层 Cordis 到顶层应用的完整分层结构
Mermaid 源码
复制代码
graph TB
    subgraph APP["应用层 (Application Layer)"]
        WEB["Web UI
(30+ client modules)"]
        CLI["CLI
(dsh bin)"]
        HEADLESS["Headless Runner"]
        SDK["SDK / ACP Server"]
    end

    subgraph BUNDLE["分发层 (Bundle Layer)"]
        BASE["dsh-base
模型适配器 | 工具 | 持久化 | 沙箱
审批策略 | 设置 | 凭证 | 遥测"]
        WEBAPP["dsh-web-app
浏览器应用"]
        HLESS["dsh-headless
无服务器运行器"]
    end

    subgraph CORE["核心服务层 (Core Services)"]
        SESSION["ctx.sessions
Session 日志"]
        AGENTS["ctx.agents
Agent 注册"]
        LOOP["ctx.agentLoop
Agent 循环"]
        TOOLS["ctx.tools
工具注册"]
        PROMPT["ctx.systemPrompt
提示词组装"]
        LLM["ctx.llm
模型接入"]
    end

    subgraph CAP["能力接缝层 (Capability Seams)"]
        FS["ctx.fs
文件系统"]
        SHELL["ctx.shell
Shell 执行"]
        SANDBOX["ctx.sandbox
进程沙箱"]
        WEBSEAM["ctx.web
Web 访问"]
        SKILL["ctx.skills
技能系统"]
        SUBAGENT["ctx.subagents
子Agent"]
        TERM["ctx.terminals
终端"]
        COMPACT["ctx.compaction
上下文压缩"]
    end

    subgraph INFRA["基础设施层 (Infrastructure)"]
        CORDIS["Cordis DI 框架
IoC 容器 | 事件系统 | HMR"]
        SCOPE["Scope 原语
作用域隔离"]
        PERSIST["持久化
JSONL 日志"]
    end

    APP --> BUNDLE
    BUNDLE --> CORE
    CORE --> CAP
    CAP --> INFRA
    WEB --> WEBAPP
    CLI --> BASE
    HEADLESS --> HLESS

    style APP fill:#1a1a2e,stroke:#58a6ff,color:#e6edf3
    style BUNDLE fill:#162032,stroke:#3fb950,color:#e6edf3
    style CORE fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style CAP fill:#1c2333,stroke:#f0883e,color:#e6edf3
    style INFRA fill:#1a1a2e,stroke:#8b949e,color:#e6edf3
渲染预览
graph TB
    subgraph APP["应用层 (Application Layer)"]
        WEB["Web UI
(30+ client modules)"]
        CLI["CLI
(dsh bin)"]
        HEADLESS["Headless Runner"]
        SDK["SDK / ACP Server"]
    end
    subgraph BUNDLE["分发层 (Bundle Layer)"]
        BASE["dsh-base
模型适配器 | 工具 | 持久化 | 沙箱
审批策略 | 设置 | 凭证 | 遥测"]
        WEBAPP["dsh-web-app
浏览器应用"]
        HLESS["dsh-headless
无服务器运行器"]
    end
    subgraph CORE["核心服务层 (Core Services)"]
        SESSION["ctx.sessions
Session 日志"]
        AGENTS["ctx.agents
Agent 注册"]
        LOOP["ctx.agentLoop
Agent 循环"]
        TOOLS["ctx.tools
工具注册"]
        PROMPT["ctx.systemPrompt
提示词组装"]
        LLM["ctx.llm
模型接入"]
    end
    subgraph CAP["能力接缝层 (Capability Seams)"]
        FS["ctx.fs
文件系统"]
        SHELL["ctx.shell
Shell 执行"]
        SANDBOX["ctx.sandbox
进程沙箱"]
        WEBSEAM["ctx.web
Web 访问"]
        SKILL["ctx.skills
技能系统"]
        SUBAGENT["ctx.subagents
子Agent"]
        TERM["ctx.terminals
终端"]
        COMPACT["ctx.compaction
上下文压缩"]
    end
    subgraph INFRA["基础设施层 (Infrastructure)"]
        CORDIS["Cordis DI 框架
IoC 容器 | 事件系统 | HMR"]
        SCOPE["Scope 原语
作用域隔离"]
        PERSIST["持久化
JSONL 日志"]
    end
    APP --> BUNDLE
    BUNDLE --> CORE
    CORE --> CAP
    CAP --> INFRA
    WEB --> WEBAPP
    CLI --> BASE
    HEADLESS --> HLESS
    style APP fill:#1a1a2e,stroke:#58a6ff,color:#e6edf3
    style BUNDLE fill:#162032,stroke:#3fb950,color:#e6edf3
    style CORE fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style CAP fill:#1c2333,stroke:#f0883e,color:#e6edf3
    style INFRA fill:#1a1a2e,stroke:#8b949e,color:#e6edf3
2
Cordis 依赖注入容器原理
展示插件如何通过 inject 声明依赖、服务如何注册到 Context 上
Mermaid 源码
复制代码
graph LR
    subgraph CTX["Context (ctx)"]
        TOOLS_S["ctx.tools"]
        LLM_S["ctx.llm"]
        FS_S["ctx.fs"]
        SESSION_S["ctx.sessions"]
    end

    P1["Plugin A
inject: ['tools','llm']
apply(ctx) { ... }"] -->|注册工具| TOOLS_S
    P1 -->|注册适配器| LLM_S
    P2["Plugin B
inject: ['tools','fs']
apply(ctx) { ... }"] -->|监听工具事件| TOOLS_S
    P2 -->|注册Provider| FS_S
    P3["Plugin C
inject: ['sessions']
apply(ctx) { ... }"] -->|注册持久化| SESSION_S

    CTX -->|"ctx.effect()
自动撤销"| DISPOSE["插件卸载时
撤销所有注册"]

    style CTX fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style P1 fill:#1a1a2e,stroke:#58a6ff,color:#e6edf3
    style P2 fill:#1a1a2e,stroke:#3fb950,color:#e6edf3
    style P3 fill:#1a1a2e,stroke:#f0883e,color:#e6edf3
    style DISPOSE fill:#2d1b1b,stroke:#f85149,color:#e6edf3
渲染预览
graph LR
    subgraph CTX["Context (ctx)"]
        TOOLS_S["ctx.tools"]
        LLM_S["ctx.llm"]
        FS_S["ctx.fs"]
        SESSION_S["ctx.sessions"]
    end
    P1["Plugin A
inject: ['tools','llm']
apply(ctx) { ... }"] -->|注册工具| TOOLS_S
    P1 -->|注册适配器| LLM_S
    P2["Plugin B
inject: ['tools','fs']
apply(ctx) { ... }"] -->|监听工具事件| TOOLS_S
    P2 -->|注册Provider| FS_S
    P3["Plugin C
inject: ['sessions']
apply(ctx) { ... }"] -->|注册持久化| SESSION_S
    CTX -->|"ctx.effect()
自动撤销"| DISPOSE["插件卸载时
撤销所有注册"]
    style CTX fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style P1 fill:#1a1a2e,stroke:#58a6ff,color:#e6edf3
    style P2 fill:#1a1a2e,stroke:#3fb950,color:#e6edf3
    style P3 fill:#1a1a2e,stroke:#f0883e,color:#e6edf3
    style DISPOSE fill:#2d1b1b,stroke:#f85149,color:#e6edf3
3
Agent Turn/Step 生命周期时序图
核心执行循环：用户输入 → Turn → Step → 模型请求 → 工具调用 → 结果返回
Mermaid 源码
复制代码
sequenceDiagram
    participant User as 用户
    participant Agent as Agent
    participant Driver as Driver
    participant Hooks as Hook 监听器
    participant Prompt as ctx.systemPrompt
    participant LLM as ctx.llm
    participant Tools as ctx.tools
    participant Session as Session 日志

    User->>Agent: followup(message)
    Agent->>Session: agent/inbox/inserted
    Agent->>Driver: 唤醒驱动器

    Driver->>Session: turn/start
    Driver->>Driver: claim pending input
    Driver->>Hooks: agent/pre-step (waterfall)
    Hooks-->>Driver: enter(messages)

    Driver->>Session: step/start
    Driver->>Session: user/message
    Driver->>Prompt: system-prompt/assemble (waterfall)

    Driver->>LLM: agent/request → llm/stream
    LLM-->>Driver: StreamChunk* (text/tool-call)
    Driver->>Session: assistant/chunk*
    Driver->>Session: assistant/message

    loop 工具调用循环
        Driver->>Session: tool/call
        Driver->>Tools: tools/pre-execute → execute → post-execute
        Tools-->>Driver: 工具结果
        Driver->>Session: tool/result
    end

    Driver->>Session: step/end

    alt 还有待处理的 step input
        Driver->>Driver: 进入下一个 step
    else 自然停止
        Driver->>Hooks: agent/turn-stopping
    end

    Driver->>Session: turn/end
    Driver-->>Agent: status: idle
渲染预览
sequenceDiagram
    participant User as 用户
    participant Agent as Agent
    participant Driver as Driver
    participant Hooks as Hook 监听器
    participant Prompt as ctx.systemPrompt
    participant LLM as ctx.llm
    participant Tools as ctx.tools
    participant Session as Session 日志
    User->>Agent: followup(message)
    Agent->>Session: agent/inbox/inserted
    Agent->>Driver: 唤醒驱动器
    Driver->>Session: turn/start
    Driver->>Driver: claim pending input
    Driver->>Hooks: agent/pre-step (waterfall)
    Hooks-->>Driver: enter(messages)
    Driver->>Session: step/start
    Driver->>Session: user/message
    Driver->>Prompt: system-prompt/assemble
    Driver->>LLM: agent/request → llm/stream
    LLM-->>Driver: StreamChunk*
    Driver->>Session: assistant/chunk*
    Driver->>Session: assistant/message
    loop 工具调用
        Driver->>Session: tool/call
        Driver->>Tools: pre-execute→execute→post-execute
        Tools-->>Driver: 工具结果
        Driver->>Session: tool/result
    end
    Driver->>Session: step/end
    Driver->>Hooks: agent/turn-stopping
    Driver->>Session: turn/end
    Driver-->>Agent: status: idle
4
工具执行管道流程图
从模型请求到工具结果返回的完整执行管道
Mermaid 源码
复制代码
flowchart TD
    A["模型返回 tool_call"] --> B["tools/pre-execute
(waterfall: allow/deny/ask)"]
    B -->|允许| C["单调守卫检查
(Monotonic Guards)"]
    B -->|拒绝| ERR["返回错误结果"]
    C --> D["tools/execute
(around-dispatch wrappers)"]
    D --> E["ToolDefinition.execute()
执行工具逻辑"]
    E --> F["tools/post-execute
(inspect/replace result)"]
    F --> G["finalizeContent
(可选的最终内容变换)"]
    G --> H["tools/result
(不可变权威结果)"]
    H --> I["写入 Session 日志
tool/result"]
    I --> J["返回给模型
作为下一步输入"]

    style A fill:#1a1a2e,stroke:#58a6ff,color:#e6edf3
    style B fill:#1c2333,stroke:#f0883e,color:#e6edf3
    style C fill:#1c2333,stroke:#f0883e,color:#e6edf3
    style D fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style E fill:#162032,stroke:#3fb950,color:#e6edf3
    style F fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style G fill:#1c2333,stroke:#8b949e,color:#e6edf3
    style H fill:#1c2333,stroke:#58a6ff,color:#e6edf3
    style I fill:#162032,stroke:#3fb950,color:#e6edf3
    style J fill:#1a1a2e,stroke:#58a6ff,color:#e6edf3
    style ERR fill:#2d1b1b,stroke:#f85149,color:#e6edf3
渲染预览
flowchart TD
    A["模型返回 tool_call"] --> B["tools/pre-execute
(waterfall: allow/deny/ask)"]
    B -->|允许| C["单调守卫检查"]
    B -->|拒绝| ERR["返回错误结果"]
    C --> D["tools/execute
(around-dispatch)"]
    D --> E["ToolDefinition.execute()"]
    E --> F["tools/post-execute"]
    F --> G["finalizeContent"]
    G --> H["tools/result"]
    H --> I["写入 Session 日志"]
    I --> J["返回给模型"]
    style A fill:#1a1a2e,stroke:#58a6ff,color:#e6edf3
    style B fill:#1c2333,stroke:#f0883e,color:#e6edf3
    style E fill:#162032,stroke:#3fb950,color:#e6edf3
    style H fill:#1c2333,stroke:#58a6ff,color:#e6edf3
    style ERR fill:#2d1b1b,stroke:#f85149,color:#e6edf3
5
能力接缝模式图
Service Definition → Service Provider → Consumer 的三角色模式
Mermaid 源码
复制代码
graph TB
    subgraph SEAM["能力接缝: ctx.shell (Bash 执行)"]
        direction TB
        DEF["Service Definition
(dsh-shell)
接口契约 + 类型定义"]
        PROV1["Service Provider A
(dsh-bash-local)
本地 Shell 实现"]
        PROV2["Service Provider B
(dsh-bash-sandbox)
沙箱 Shell 实现"]
        CONSUMER["Consumer
(dsh-tool-bash)
模型面向的 bash 工具"]
    end

    subgraph SEAM2["能力接缝: ctx.fs (文件系统)"]
        direction TB
        DEF2["Service Definition
(dsh-fs)"]
        PROV2A["Provider
(dsh-fs-local)"]
        OBS["Policy Plugin
(dsh-fs-observation-policy)"]
        CONSUMER2["Consumer
(dsh-tool-fs)"]
    end

    MODEL["模型"] -->|"tool_call: bash"| CONSUMER
    CONSUMER -->|"ctx.shell.resolve() → run()"| PROV1
    CONSUMER -->|"ctx.shell.resolve() → run()"| PROV2
    PROV1 -.->|"替换"| PROV2

    MODEL2["模型"] -->|"tool_call: read/write/edit"| CONSUMER2
    CONSUMER2 -->|"ctx.fs.readText() / writeText()"| PROV2A
    OBS -->|"fs/write-intent 决策"| CONSUMER2

    style DEF fill:#1c2333,stroke:#58a6ff,color:#e6edf3
    style PROV1 fill:#162032,stroke:#3fb950,color:#e6edf3
    style PROV2 fill:#162032,stroke:#3fb950,color:#e6edf3
    style CONSUMER fill:#1a1a2e,stroke:#f0883e,color:#e6edf3
    style DEF2 fill:#1c2333,stroke:#58a6ff,color:#e6edf3
    style PROV2A fill:#162032,stroke:#3fb950,color:#e6edf3
    style OBS fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style CONSUMER2 fill:#1a1a2e,stroke:#f0883e,color:#e6edf3
渲染预览
graph TB
    subgraph SEAM["能力接缝: ctx.shell"]
        DEF["Service Definition
(dsh-shell)"]
        PROV1["Provider A
(dsh-bash-local)"]
        PROV2["Provider B
(dsh-bash-sandbox)"]
        CONSUMER["Consumer
(dsh-tool-bash)"]
    end
    subgraph SEAM2["能力接缝: ctx.fs"]
        DEF2["Service Definition
(dsh-fs)"]
        PROV2A["Provider
(dsh-fs-local)"]
        OBS["Policy Plugin"]
        CONSUMER2["Consumer
(dsh-tool-fs)"]
    end
    MODEL["模型"] -->|tool_call: bash| CONSUMER
    CONSUMER --> PROV1
    CONSUMER --> PROV2
    PROV1 -.->|替换| PROV2
    MODEL2["模型"] -->|tool_call: read/write| CONSUMER2
    CONSUMER2 --> PROV2A
    OBS --> CONSUMER2
    style DEF fill:#1c2333,stroke:#58a6ff,color:#e6edf3
    style PROV1 fill:#162032,stroke:#3fb950,color:#e6edf3
    style PROV2 fill:#162032,stroke:#3fb950,color:#e6edf3
    style CONSUMER fill:#1a1a2e,stroke:#f0883e,color:#e6edf3
6
多模型接入层架构图
Provider 注册表模式：多个适配器注册到 ctx.llm，统一的 StreamChunk 协议
Mermaid 源码
复制代码
graph LR
    subgraph AGENT_LOOP["Agent Loop"]
        REQ["agent/request
waterfall"]
    end

    REQ -->|"provider: 'openai'"| OA["OpenAI 适配器
GPT-4o / o1 / o3"]
    REQ -->|"provider: 'anthropic'"| ANT["Anthropic 适配器
Claude 4 / Sonnet"]
    REQ -->|"provider: 'deepseek'"| DS["DeepSeek 适配器
V3 / R1"]
    REQ -->|"provider: 'google'"| GG["Google 适配器
Gemini 2.5"]
    REQ -->|"provider: 'mistral'"| MIST["Mistral 适配器"]

    OA --> STREAM["统一 StreamChunk 协议"]
    ANT --> STREAM
    DS --> STREAM
    GG --> STREAM
    MIST --> STREAM

    STREAM -->|"text-delta"| ASSEMB["块组装器"]
    STREAM -->|"tool-call-delta"| ASSEMB
    STREAM -->|"reasoning-delta"| ASSEMB
    STREAM -->|"block-end"| ASSEMB
    ASSEMB -->|"assistant/message"| SESSION["Session 日志"]

    style REQ fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style OA fill:#1a1a2e,stroke:#3fb950,color:#e6edf3
    style ANT fill:#1a1a2e,stroke:#f0883e,color:#e6edf3
    style DS fill:#1a1a2e,stroke:#58a6ff,color:#e6edf3
    style GG fill:#1a1a2e,stroke:#d2a8ff,color:#e6edf3
    style MIST fill:#1a1a2e,stroke:#8b949e,color:#e6edf3
    style STREAM fill:#162032,stroke:#3fb950,color:#e6edf3
    style SESSION fill:#1c2333,stroke:#58a6ff,color:#e6edf3
渲染预览
graph LR
    subgraph AGENT_LOOP["Agent Loop"]
        REQ["agent/request"]
    end
    REQ -->|provider: openai| OA["OpenAI 适配器"]
    REQ -->|provider: anthropic| ANT["Anthropic 适配器"]
    REQ -->|provider: deepseek| DS["DeepSeek 适配器"]
    REQ -->|provider: google| GG["Google 适配器"]
    OA --> STREAM["统一 StreamChunk"]
    ANT --> STREAM
    DS --> STREAM
    GG --> STREAM
    STREAM --> ASSEMB["块组装器"]
    ASSEMB --> SESSION["Session 日志"]
    style REQ fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style STREAM fill:#162032,stroke:#3fb950,color:#e6edf3
    style SESSION fill:#1c2333,stroke:#58a6ff,color:#e6edf3
7
沙箱安全架构图
跨平台沙箱后端：Landlock (Linux) / Seatbelt (macOS) / ACL (Windows)
Mermaid 源码
复制代码
graph TB
    TOOL["工具调用
(bash / pwsh)"] --> POLICY["SandboxPolicyService
ctx.sandboxPolicy"]
    POLICY -->|"resolve(mode, session)"| MODE{"SandboxMode?"}

    MODE -->|read-only| CONFINED["confine(argv, policy)"]
    MODE -->|workspace-write| CONFINED
    MODE -->|danger-full-access| BYPASS["直接执行原始 argv
(不调用 ctx.sandbox)"]

    CONFINED --> SELECT{"平台检测"}

    SELECT -->|Linux| LANDLOCK["Landlock + bwrap
内核级文件策略"]
    SELECT -->|macOS| SEATBELT["Seatbelt
(sandbox-exec)"]
    SELECT -->|Windows| ACL["ACL Restricted Token
受限访问令牌"]

    LANDLOCK --> WRAPPED["ConfinedArgv
包装后的 argv + 执行完整性"]
    SEATBELT --> WRAPPED
    ACL --> WRAPPED

    WRAPPED --> SPAWN["spawn(包装后的 argv)"]
    SPAWN --> RESULT["ShellRunResult
+ ShellSandboxInfo"]

    style TOOL fill:#1a1a2e,stroke:#58a6ff,color:#e6edf3
    style POLICY fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style MODE fill:#1c2333,stroke:#f0883e,color:#e6edf3
    style CONFINED fill:#162032,stroke:#3fb950,color:#e6edf3
    style BYPASS fill:#2d1b1b,stroke:#f85149,color:#e6edf3
    style LANDLOCK fill:#162032,stroke:#3fb950,color:#e6edf3
    style SEATBELT fill:#162032,stroke:#3fb950,color:#e6edf3
    style ACL fill:#162032,stroke:#3fb950,color:#e6edf3
渲染预览
graph TB
    TOOL["工具调用"] --> POLICY["SandboxPolicyService"]
    POLICY --> MODE{"SandboxMode?"}
    MODE -->|read-only| CONFINED["confine(argv, policy)"]
    MODE -->|workspace-write| CONFINED
    MODE -->|full-access| BYPASS["直接执行"]
    CONFINED --> SELECT{"平台?"}
    SELECT -->|Linux| LANDLOCK["Landlock + bwrap"]
    SELECT -->|macOS| SEATBELT["Seatbelt"]
    SELECT -->|Windows| ACL["ACL Token"]
    LANDLOCK --> WRAPPED["ConfinedArgv"]
    SEATBELT --> WRAPPED
    ACL --> WRAPPED
    WRAPPED --> SPAWN["spawn()"]
    BYPASS --> SPAWN
    style POLICY fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style BYPASS fill:#2d1b1b,stroke:#f85149,color:#e6edf3
    style LANDLOCK fill:#162032,stroke:#3fb950,color:#e6edf3
    style SEATBELT fill:#162032,stroke:#3fb950,color:#e6edf3
    style ACL fill:#162032,stroke:#3fb950,color:#e6edf3
8
Session 事件溯源架构图
Session 日志作为唯一事实来源，所有可见历史从日志派生
Mermaid 源码
复制代码
graph LR
    subgraph LOG["Session 事件日志 (append-only)"]
        E1["turn/start"]
        E2["step/start"]
        E3["user/message"]
        E4["assistant/chunk*"]
        E5["assistant/message"]
        E6["tool/call"]
        E7["tool/result"]
        E8["step/end"]
        E9["turn/end"]
        E10["request/header"]
        E11["request/context"]
    end

    LOG -->|"deriveMessages()"| HISTORY["模型可见的
对话历史"]
    LOG -->|"Session 持久化"| DISK["JSONL 磁盘文件"]
    LOG -->|"session/event 广播"| UI["Web UI
实时渲染"]
    LOG -->|"遥测消费"| TELEM["OpenTelemetry
监控分析"]
    LOG -->|"fork() 派生"| FORK["新的分叉 Session"]

    style LOG fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style HISTORY fill:#162032,stroke:#3fb950,color:#e6edf3
    style DISK fill:#162032,stroke:#58a6ff,color:#e6edf3
    style UI fill:#1a1a2e,stroke:#f0883e,color:#e6edf3
    style TELEM fill:#1a1a2e,stroke:#8b949e,color:#e6edf3
    style FORK fill:#1a1a2e,stroke:#d2a8ff,color:#e6edf3
渲染预览
graph LR
    subgraph LOG["Session 事件日志"]
        E1["turn/start"] --> E2["step/start"]
        E2 --> E3["user/message"]
        E3 --> E4["assistant/chunk*"]
        E4 --> E5["assistant/message"]
        E5 --> E6["tool/call → result"]
        E6 --> E8["step/end"]
        E8 --> E9["turn/end"]
    end
    LOG -->|deriveMessages| HISTORY["对话历史"]
    LOG -->|持久化| DISK["JSONL 文件"]
    LOG -->|广播| UI["Web UI"]
    LOG -->|fork| FORK["分叉 Session"]
    style LOG fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style HISTORY fill:#162032,stroke:#3fb950,color:#e6edf3
    style UI fill:#1a1a2e,stroke:#f0883e,color:#e6edf3
9
Profile / Bundle 组合图
不同 Profile 通过堆叠不同 Bundle 实现不同的产品形态
Mermaid 源码
复制代码
graph TB
    subgraph WEB_PROFILE["Profile: web"]
        direction TB
        W_PATCH["cordis.patch.yml
(Profile 级覆盖)"]
        W_WEBAPP["Bundle: dsh-web-app
浏览器 UI 模块"]
        W_BASE["Bundle: dsh-base
模型 | 工具 | 沙箱 | 持久化"]
    end

    subgraph HEADLESS_PROFILE["Profile: headless"]
        direction TB
        H_PATCH["cordis.patch.yml"]
        H_LESS["Bundle: dsh-headless
一次性运行器"]
        H_BASE["Bundle: dsh-base"]
    end

    subgraph CUSTOM_PROFILE["Profile: custom"]
        direction TB
        C_PATCH["cordis.patch.yml
+ 用户 home patch
+ --patch overlay"]
        C_BASE["Bundle: dsh-base"]
        C_EXTRA["第三方插件
自定义 Provider"]
    end

    EMPTY["空 Cordis 配置"] --> W_BASE
    W_BASE --> W_WEBAPP
    W_WEBAPP --> W_PATCH
    W_PATCH --> WEB_APP["Web 应用
http://localhost:3080"]

    EMPTY --> H_BASE
    H_BASE --> H_LESS
    H_LESS --> H_PATCH
    H_PATCH --> HEADLESS_APP["Headless Agent
一次性执行"]

    EMPTY --> C_BASE
    C_BASE --> C_EXTRA
    C_EXTRA --> C_PATCH
    C_PATCH --> CUSTOM_APP["自定义部署"]

    style WEB_APP fill:#162032,stroke:#3fb950,color:#e6edf3
    style HEADLESS_APP fill:#162032,stroke:#58a6ff,color:#e6edf3
    style CUSTOM_APP fill:#162032,stroke:#d2a8ff,color:#e6edf3
    style W_BASE fill:#1c2333,stroke:#8b949e,color:#e6edf3
    style H_BASE fill:#1c2333,stroke:#8b949e,color:#e6edf3
    style C_BASE fill:#1c2333,stroke:#8b949e,color:#e6edf3
渲染预览
graph TB
    subgraph WP["Profile: web"]
        W_BASE["dsh-base"] --> W_WEBAPP["dsh-web-app"]
        W_WEBAPP --> W_PATCH["patch.yml"]
    end
    subgraph HP["Profile: headless"]
        H_BASE["dsh-base"] --> H_LESS["dsh-headless"]
        H_LESS --> H_PATCH["patch.yml"]
    end
    W_PATCH --> WEB_APP["Web 应用 :3080"]
    H_PATCH --> HEADLESS_APP["Headless Agent"]
    style WEB_APP fill:#162032,stroke:#3fb950,color:#e6edf3
    style HEADLESS_APP fill:#162032,stroke:#58a6ff,color:#e6edf3
10
技能系统发现与注册流程
多 Provider 分层发现 → 合并 → 模型调用
Mermaid 源码
复制代码
flowchart TD
    subgraph DISCOVER["发现阶段"]
        P1["Provider: project-dsh
rank 100"]
        P2["Provider: project-agents
rank 200"]
        P3["Provider: user-dsh
rank 400"]
        P4["Provider: bundled
rank 600"]
    end

    P1 --> MERGE["ctx.skills.list()
合并所有 Provider 的候选"]
    P2 --> MERGE
    P3 --> MERGE
    P4 --> MERGE

    MERGE --> SNAPSHOT["SkillCatalogSnapshot
sorted summaries"]
    SNAPSHOT --> CATALOG["模型可见的技能目录
(name + description)"]

    MODEL["模型"] -->|"tool_call: skill"| TOOL_SKILL["dsh-tool-skill"]
    TOOL_SKILL -->|"ctx.skills.get(candidate)"| LOAD["加载完整技能体
SkillDefinition"]
    LOAD --> INJECT["注入技能内容到
下一轮 prompt"]

    subgraph CACHE["缓存和失效"]
        WATCH["Chokidar 文件监听"]
        WRITE["模型 write/edit 观察"]
        WATCH -->|"文件变更"| INVALIDATE["invalidate()"]
        WRITE -->|"目标匹配"| INVALIDATE
    end

    INVALIDATE -->|"skills/change 事件"| MERGE

    style MERGE fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style CATALOG fill:#162032,stroke:#3fb950,color:#e6edf3
    style TOOL_SKILL fill:#1a1a2e,stroke:#f0883e,color:#e6edf3
    style INJECT fill:#162032,stroke:#58a6ff,color:#e6edf3
    style INVALIDATE fill:#2d1b1b,stroke:#f85149,color:#e6edf3
渲染预览
flowchart TD
    P1["project-dsh (100)"] --> MERGE["ctx.skills.list()"]
    P2["project-agents (200)"] --> MERGE
    P3["user-dsh (400)"] --> MERGE
    P4["bundled (600)"] --> MERGE
    MERGE --> SNAPSHOT["CatalogSnapshot"]
    SNAPSHOT --> CATALOG["模型技能目录"]
    MODEL["模型"] -->|skill tool_call| TS["dsh-tool-skill"]
    TS --> LOAD["get(candidate)"]
    LOAD --> INJECT["注入 prompt"]
    WATCH["文件监听"] -->|变更| INV["invalidate()"]
    INV --> MERGE
    style MERGE fill:#1c2333,stroke:#d2a8ff,color:#e6edf3
    style CATALOG fill:#162032,stroke:#3fb950,color:#e6edf3
    style INJECT fill:#162032,stroke:#58a6ff,color:#e6edf3
配合《DeepSeek Harness 技术深度解析：一切皆插件的Agent框架》使用
所有图表使用 Mermaid.js 渲染 | 可直接复制源码到任何支持 Mermaid 的平台