---
title: "DeepSeek Harness (DSH) 插件开发教程 - 第一部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 插件开发教程"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness (DSH) 插件开发教程 - 第一部分

## 插件系统架构总览

### 1. "一切皆插件"的设计哲学

DeepSeek Harness 采用了一种极致的模块化架构设计，其核心理念可以概括为"一切皆插件"（Everything is a Plugin）。这意味着 DSH 的每一个功能组件——从模型适配器、工具注册表、会话日志，到 Agent 循环本身——都是以插件的形式存在，可以自由替换和组合。

这种设计哲学带来了几个关键优势：

**完全可替换性**：任何组件都可以被替换，无需修改核心代码。例如，如果你想更换 LLM 提供商，只需替换对应的适配器插件；如果你想改变文件系统访问方式，只需替换文件系统提供者插件。

**无特权核心**：DSH 没有一个不可修改的"核心"。所有功能都通过插件注册到共享上下文中，注册本身是一种可逆的效果（reversible effect），当插件卸载时，其所有注册会自动清理。

**配置驱动组合**：运行时的 DSH 实例是从有序的配置层组合而成的插件树。通过配置文件（`cordis.yml`）和补丁文件（`cordis.patch.yml`），用户可以精确控制加载哪些插件以及如何配置它们。

**依赖注入**：插件通过声明依赖（`inject`）来表达对其他服务的需求，Cordis 框架会自动处理加载顺序，确保依赖的服务在需要时已经可用。

### 2. Cordis 依赖注入框架简介

Cordis 是 DSH 底层的插件框架，它提供了以下核心概念：

#### 2.1 插件（Plugin）

一个插件是一个实现了 Service 接口的对象。它可以是一个带有可选 `inject` 和 `apply(ctx)` 字段的函数，也可以是一个 `Service` 子类，其生命周期由 Cordis 自动挂载到当前上下文中。

```typescript
// 函数式插件
export const name = 'my-plugin'
export const inject = ['tools']  // 声明依赖

export function apply(ctx: Context) {
  // 插件逻辑
}
```

#### 2.2 上下文（Context）

上下文是一个服务仓库。服务通过稳定的 `ctx.<key>`（如 `ctx.tools`、`ctx.llm`、`ctx.sessions`）来声明其在上下文中的位置；其他插件通过 key 来查找服务，而不是导入具体实现。

```typescript
// 访问工具注册服务
ctx.tools.register(myTool)

// 访问 LLM 服务
ctx.llm.registerAdapter(['my-provider'], myAdapter)
```

#### 2.3 服务依赖声明

通过 `inject` 字段声明服务依赖。声明了所需服务的插件会等待这些服务存在后才加载，因此加载顺序通过服务需求来表达，而不是手动的启动顺序编排。

```typescript
export const inject = ['tools', 'llm', 'sessions']  // 依赖三个服务
```

#### 2.4 类型化事件

服务通过 TypeScript 声明合并来声明事件名称，然后根据设计意图使用 `emit`、`waterfall`、`parallel` 或 `serial` 方法来分发事件。

```typescript
declare module '@deepseek-ai/cordis' {
  interface Events {
    'my-event'(data: MyData): void
  }
}

// 分发事件
ctx.emit('my-event', data)
```

#### 2.5 可逆效果

提示词部分、工具模式、适配器、提供者和监听器都通过 `ctx.effect()` 或 `ctx.on()` 安装，这样重载和卸载时可以预测地清理它们。

```typescript
// 注册一个效果，当插件卸载时自动清理
ctx.effect(() => {
  const tool = ctx.tools.register(myTool)
  return () => tool.dispose()  // 清理函数
})
```

#### 2.6 事件分发模式

每个事件只能有一种分发模式：

| 模式 | 是否等待 | 分发顺序 | 有返回值 |
|------|----------|----------|----------|
| `emit` | 否 | 监听器按注册顺序观察 | 无 |
| `waterfall` | 否 | 监听器按注册顺序观察 | 有 |
| `parallel` | 是 | 所有监听器并行观察 | 无 |
| `serial` | 是 | 监听器按注册顺序观察 | 有 |

### 3. 插件的分类

DSH 中的插件可以根据其功能角色分为以下几类：

#### 3.1 Tool 插件

Tool 插件向模型注册可调用的工具。这些工具的 schema 会自动流入系统提示词组装，使模型能够理解和调用它们。

```typescript
// 示例：文件读取工具
ctx.tools.register(defineTool({
  name: 'read_file',
  description: '从磁盘读取文件',
  parameters: {
    path: { type: 'string', required: true, description: '绝对路径' },
  },
  async execute(args, exec) {
    return readFile(args.path, { encoding: 'utf8', signal: exec.signal })
  },
}))
```

#### 3.2 Provider 插件

Provider 插件实现可替换的能力提供者。一个能力（capability）通常由三个角色组成：服务定义（Service Definition）、服务提供者（Service Provider）和消费者（Consumer）。

例如，LLM 适配器就是一个 Provider 插件：

```typescript
class MyAdapter extends LlmAdapter {
  async * stream(options: GenerateOptions): AsyncIterable<StreamChunk> {
    // 流式生成实现
  }
}

export function apply(ctx: Context, config: Config) {
  ctx.llm.registerAdapter(['my-provider'], new MyAdapter())
}
```

#### 3.3 UI 插件

UI 插件负责用户界面渲染。在 DSH 的客户端包中，每个 UI 组件都是一个独立的插件，如 `ui-conversation`、`ui-settings`、`ui-tool` 等。

#### 3.4 Storage 插件

Storage 插件提供数据持久化能力。DSH 的存储抽象层允许不同的存储后端（如本地文件系统、云存储等）通过插件形式接入。

#### 3.5 Service 插件

Service 插件提供核心服务功能，如会话管理（`session`）、计划管理（`plan`）、目标管理（`goal`）等。

---

## 从零创建一个 Tool 插件

### 1. 项目结构搭建

创建一个新的 Tool 插件需要以下文件结构：

```
packages/<group>/<my-tool>/
  package.json     # 包配置
  tsconfig.json    # TypeScript 配置
  src/
    index.ts       # 插件入口
    types.ts       # 类型定义（可选）
  tests/
    *.spec.ts      # 测试文件
  README.md        # 文档
```

#### 1.1 package.json 配置

```json
{
  "name": "@deepseek-ai/dsh-my-tool",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/types/index.d.ts",
  "exports": {
    ".": {
      "types": "./lib/types/index.d.ts",
      "default": "./lib/index.js"
    }
  },
  "files": [
    "lib/index.js",
    "lib/invariant.js",
    "lib/types/**/*.d.ts"
  ],
  "peerDependencies": {
    "@deepseek-ai/cordis": "*",
    "@deepseek-ai/dsh-tools": "*"
  },
  "devDependencies": {
    "@deepseek-ai/cordis": "*",
    "@deepseek-ai/dsh-tools": "*",
    "@deepseek-ai/schemastery": "*"
  },
  "dependencies": {
    "@deepseek-ai/schemastery": "*"
  }
}
```

#### 1.2 tsconfig.json 配置

```json
{
  "extends": "../../../tsconfig.base.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "lib/types"
  },
  "references": [
    { "path": "../../../vendor/cosmokit" },
    { "path": "../../../vendor/cordis" },
    { "path": "../../../vendor/schemastery" },
    { "path": "../../core/tools" }
  ]
}
```

### 2. 接口定义和类型

DSH 提供了 `defineTool` 辅助函数来定义工具。一个完整的工具定义包含以下部分：

```typescript
import { defineTool } from '@deepseek-ai/dsh-tools'

interface MyToolArgs {
  query: string
  limit?: number
}

interface MyToolResult {
  items: Array<{ id: string; name: string }>
  total: number
}

const myTool = defineTool<MyToolArgs, MyToolResult>({
  // 工具名称，模型会使用这个名称来调用
  name: 'search_items',
  
  // 工具描述，帮助模型理解何时使用这个工具
  description: '搜索项目列表',
  
  // 参数模式定义
  parameters: {
    query: { 
      type: 'string', 
      required: true, 
      description: '搜索关键词' 
    },
    limit: { 
      type: 'number', 
      description: '返回结果数量限制' 
    },
  },
  
  // 输出模式定义
  output: {
    schema: { type: 'object' },
    render: (_args, value) => [{ 
      type: 'text', 
      text: JSON.stringify(value, null, 2) 
    }],
  },
  
  // 执行函数
  async execute(args, exec) {
    // args 是经过类型验证的参数
    // exec 包含执行上下文（agent、signal 等）
    
    const results = await searchItems(args.query, args.limit ?? 10)
    return {
      items: results,
      total: results.length,
    }
  },
})
```

### 3. 注册和生命周期

工具的注册是基于效果的：当插件卸载时，工具会自动取消注册。Schema 会自动流入系统提示词组装。

```typescript
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'my-search-tool'
export const inject = ['tools']  // 依赖工具注册服务

export function apply(ctx: Context) {
  // 注册工具，返回一个可处置的对象
  const registration = ctx.tools.register(defineTool({
    name: 'search_items',
    description: '搜索项目列表',
    parameters: {
      query: { type: 'string', required: true, description: '搜索关键词' },
      limit: { type: 'number', description: '返回结果数量限制' },
    },
    async execute(args, exec) {
      return await performSearch(args.query, args.limit)
    },
  }))
  
  // 当插件卸载时，registration 会自动清理
  // 也可以手动调用 registration.dispose() 来提前取消注册
}
```

### 4. 完整代码示例

下面是一个完整的天气查询工具插件示例：

```typescript
// packages/tools/weather-tool/src/index.ts
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import z from '@deepseek-ai/schemastery'

// 配置模式
export const Config = z.object({
  apiKey: z.string().role('secret'),
  baseUrl: z.string().default('https://api.weather.com'),
})

export type Config = z.infer<typeof Config>

export const name = 'weather-tool'
export const inject = ['tools']

interface WeatherArgs {
  city: string
  unit?: 'celsius' | 'fahrenheit'
}

interface WeatherResult {
  city: string
  temperature: number
  unit: string
  condition: string
  humidity: number
}

export function apply(ctx: Context, config: Config) {
  ctx.tools.register(defineTool<WeatherArgs, WeatherResult>({
    name: 'get_weather',
    description: '获取指定城市的当前天气信息',
    parameters: {
      city: { 
        type: 'string', 
        required: true, 
        description: '城市名称，如"北京"、"上海"' 
      },
      unit: { 
        type: 'string', 
        description: '温度单位，celsius 或 fahrenheit' 
      },
    },
    output: {
      schema: { type: 'object' },
      render: (_args, value) => [{
        type: 'text',
        text: `${value.city}当前天气：${value.condition}，温度 ${value.temperature}°${value.unit === 'celsius' ? 'C' : 'F'}，湿度 ${value.humidity}%`,
      }],
    },
    async execute(args, exec) {
      const unit = args.unit ?? 'celsius'
      const url = `${config.baseUrl}/weather?city=${encodeURIComponent(args.city)}&unit=${unit}`
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${config.apiKey}` },
        signal: exec.signal,
      })
      
      if (!response.ok) {
        throw new Error(`Weather API error: ${response.status}`)
      }
      
      return await response.json()
    },
  }))
}
```

---

## 插件间通信机制

### 1. 事件系统

DSH 的事件系统是插件间通信的主要方式。事件可以分为三类：

#### 1.1 会话事件（Session Events）

会话事件是持久化的事实，附加到日志中并通过 `session/event` 广播。当一个事实必须在重载后仍然存在时使用会话事件。

```typescript
declare module '@deepseek-ai/cordis' {
  interface Events {
    'session/event'(event: SessionEvent): void
  }
}
```

#### 1.2 Agent 事件（Agent Events）

Agent 事件携带一个活的 `Agent` 实例，用于观察或拦截正在进行的工作。

```typescript
declare module '@deepseek-ai/cordis' {
  interface Events {
    'agent/inbox'(agent: Agent, message: UserMessage): void
    'agent/step'(agent: Agent, step: Step): void
    'agent/request'(agent: Agent, request: Request): void
    'agent/status'(agent: Agent, status: AgentStatus): void
  }
}
```

#### 1.3 能力事件（Capability Events）

能力事件将策略和适配器附加到一个接缝（seam）上，而不导入循环本身。

```typescript
// 工具执行管道事件
declare module '@deepseek-ai/cordis' {
  interface Events {
    'tools/pre-execute'(exec: ToolExecution, next: () => Promise<PreToolDecision>): Promise<PreToolDecision>
    'tools/execute'(exec: ToolDispatchExecution, next: () => Promise<ToolExecutionResult>): Promise<ToolExecutionResult>
    'tools/post-execute'(exec: ToolExecution, result: Readonly<ToolExecutionResult>, next: () => Promise<PostToolDecision>): Promise<PostToolDecision>
    'tools/result'(exec: Readonly<ToolExecution>, result: Readonly<ToolExecutionResult>): void
  }
}
```

### 2. 服务注入

服务注入是插件间通信的另一种方式。通过 `ctx.get()` 或直接访问 `ctx.<key>`，插件可以获取其他插件提供的服务。

```typescript
// 获取工具注册服务
const tools = ctx.get('tools')

// 获取 LLM 服务
const llm = ctx.get('llm')

// 获取会话服务
const sessions = ctx.get('sessions')
```

服务注入的一个重要特性是**懒加载**：如果所需的服务尚未注册，插件会等待服务可用后再执行。

### 3. 共享状态

插件可以通过以下方式共享状态：

#### 3.1 通过服务方法

```typescript
// 定义一个共享状态服务
class MyStateService extends Service {
  private state = new Map<string, any>()
  
  get(key: string) { return this.state.get(key) }
  set(key: string, value: any) { this.state.set(key, value) }
}

// 在其他插件中使用
ctx.get('myState').set('key', 'value')
```

#### 3.2 通过事件传递

```typescript
// 发送状态更新事件
ctx.emit('my-state-updated', { key: 'value' })

// 监听状态更新
ctx.on('my-state-updated', (data) => {
  console.log('State updated:', data)
})
```

#### 3.3 通过配置共享

```typescript
// 在 cordis.yml 中定义共享配置
export const Config = z.object({
  sharedSetting: z.string().default('default'),
})

// 在插件中访问配置
export function apply(ctx: Context, config: Config) {
  console.log(config.sharedSetting)
}
```

### 4. Waterfall 语义

Waterfall 是一种特殊的事件分发模式，用于实现中间件模式。监听器接收 `(...args, next)` 参数，调用 `next()` 委托给下一个监听器，不调用 `next()` 则短路。

```typescript
// 监听工具执行前的事件
ctx.on('tools/pre-execute', async (exec, next) => {
  // 检查权限
  if (!hasPermission(exec.agent, exec.name)) {
    return { decision: 'deny', reason: 'No permission' }
  }
  
  // 委托给下一个监听器
  return next()
})

// 监听工具执行后的事件
ctx.on('tools/post-execute', async (exec, result, next) => {
  // 记录执行日志
  logToolExecution(exec, result)
  
  // 委托给下一个监听器
  return next()
})
```
