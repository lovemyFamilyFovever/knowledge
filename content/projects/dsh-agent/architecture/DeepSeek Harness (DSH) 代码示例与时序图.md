---
title: "DeepSeek Harness (DSH) 代码示例与时序图"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 架构设计文档"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness (DSH) 代码示例与时序图

本文档为架构设计文档的补充材料，包含具体的代码示例和时序图描述。

---

## 一、核心时序图

### 1.1 Agent 请求处理时序图

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  User   │    │ Session │    │  Agent  │    │   LLM   │    │  Tools  │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     │              │              │              │              │
     │ 1.发送消息    │              │              │              │
     │─────────────>│              │              │              │
     │              │              │              │              │
     │              │ 2.记录事件    │              │              │
     │              │──────────┐   │              │              │
     │              │          │   │              │              │
     │              │<─────────┘   │              │              │
     │              │              │              │              │
     │              │ 3.触发Agent  │              │              │
     │              │─────────────>│              │              │
     │              │              │              │              │
     │              │              │ 4.组装提示词   │              │
     │              │              │──────────┐   │              │
     │              │              │          │   │              │
     │              │              │<─────────┘   │              │
     │              │              │              │              │
     │              │              │ 5.调用模型    │              │
     │              │              │─────────────>│              │
     │              │              │              │              │
     │              │              │ 6.返回响应    │              │
     │              │              │<─────────────│              │
     │              │              │              │              │
     │              │              │ 7.解析工具调用 │              │
     │              │              │──────────┐   │              │
     │              │              │          │   │              │
     │              │              │<─────────┘   │              │
     │              │              │              │              │
     │              │              │ 8.执行工具    │              │
     │              │              │─────────────────────────────>│
     │              │              │              │              │
     │              │              │ 9.返回结果    │              │
     │              │              │<─────────────────────────────│
     │              │              │              │              │
     │              │              │ 10.记录事件   │              │
     │              │              │──────────┐   │              │
     │              │              │          │   │              │
     │              │              │<─────────┘   │              │
     │              │              │              │              │
     │              │ 11.返回响应   │              │              │
     │              │<─────────────│              │              │
     │              │              │              │              │
     │ 12.显示结果   │              │              │              │
     │<─────────────│              │              │              │
     │              │              │              │              │
```

### 1.2 插件加载时序图

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Loader │    │  Graph  │    │  Fiber  │    │ Plugin  │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     │              │              │              │
     │ 1.读取配置    │              │              │
     │──────────┐   │              │              │
     │          │   │              │              │
     │<─────────┘   │              │              │
     │              │              │              │
     │ 2.解析依赖    │              │              │
     │─────────────>│              │              │
     │              │              │              │
     │ 3.拓扑排序    │              │              │
     │              │──────────┐   │              │
     │              │          │   │              │
     │              │<─────────┘   │              │
     │              │              │              │
     │ 4.返回加载顺序 │              │              │
     │<─────────────│              │              │
     │              │              │              │
     │ 5.创建Fiber   │              │              │
     │─────────────────────────────>│              │
     │              │              │              │
     │              │              │ 6.验证配置    │
     │              │              │──────────┐   │
     │              │              │          │   │
     │              │              │<─────────┘   │
     │              │              │              │
     │              │              │ 7.等待依赖    │
     │              │              │──────────┐   │
     │              │              │          │   │
     │              │              │<─────────┘   │
     │              │              │              │
     │              │              │ 8.调用apply   │
     │              │              │─────────────>│
     │              │              │              │
     │              │              │ 9.注册副作用   │
     │              │              │<─────────────│
     │              │              │              │
     │              │              │ 10.状态→ACTIVE│
     │              │              │──────────┐   │
     │              │              │          │   │
     │              │              │<─────────┘   │
     │              │              │              │
```

### 1.3 会话生命周期时序图

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  User   │    │ Session │    │ Storage │    │  Agent  │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     │              │              │              │
     │ 1.创建会话    │              │              │
     │─────────────>│              │              │
     │              │              │              │
     │              │ 2.生成ID      │              │
     │              │──────────┐   │              │
     │              │          │   │              │
     │              │<─────────┘   │              │
     │              │              │              │
     │              │ 3.持久化      │              │
     │              │─────────────>│              │
     │              │              │              │
     │              │ 4.确认        │              │
     │              │<─────────────│              │
     │              │              │              │
     │ 5.返回会话    │              │              │
     │<─────────────│              │              │
     │              │              │              │
     │ 6.发送消息    │              │              │
     │─────────────>│              │              │
     │              │              │              │
     │              │ 7.记录事件    │              │
     │              │─────────────>│              │
     │              │              │              │
     │              │ 8.触发Agent   │              │
     │              │─────────────────────────────>│
     │              │              │              │
     │              │              │ 9.处理完成    │
     │              │<─────────────────────────────│
     │              │              │              │
     │              │ 10.保存快照   │              │
     │              │─────────────>│              │
     │              │              │              │
     │ 11.返回结果   │              │              │
     │<─────────────│              │              │
     │              │              │              │
```

### 1.4 热重载时序图

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Watcher │    │   HMR   │    │  Fiber  │    │ Plugin  │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     │              │              │              │
     │ 1.检测文件变更 │              │              │
     │─────────────>│              │              │
     │              │              │              │
     │              │ 2.查找受影响插件│              │
     │              │──────────┐   │              │
     │              │          │   │              │
     │              │<─────────┘   │              │
     │              │              │              │
     │              │ 3.暂停事件处理 │              │
     │              │─────────────>│              │
     │              │              │              │
     │              │              │ 4.清理副作用   │
     │              │              │──────────┐   │
     │              │              │          │   │
     │              │              │<─────────┘   │
     │              │              │              │
     │              │ 5.重新加载代码 │              │
     │              │─────────────────────────────>│
     │              │              │              │
     │              │              │ 6.验证新代码   │
     │              │              │<─────────────│
     │              │              │              │
     │              │              │ 7.执行apply   │
     │              │              │─────────────>│
     │              │              │              │
     │              │              │ 8.注册新副作用  │
     │              │              │<─────────────│
     │              │              │              │
     │              │ 9.恢复事件处理 │              │
     │              │<─────────────│              │
     │              │              │              │
```

---

## 二、核心代码示例

### 2.1 创建自定义 Agent

```typescript
import { Service, Context, Disposable } from 'cordis'

// 定义 Agent 接口
interface MyAgentConfig {
  name: string
  model: string
  temperature?: number
}

// 实现自定义 Agent
export class MyAgent extends Service {
  private config: MyAgentConfig
  private conversations: Map<string, Conversation> = new Map()

  constructor(ctx: Context, config: MyAgentConfig) {
    super(ctx, 'myAgent')
    this.config = config
  }

  // 创建新会话
  async createConversation(userId: string): Promise<Conversation> {
    const conversation: Conversation = {
      id: this.generateId(),
      userId,
      messages: [],
      createdAt: Date.now()
    }
    
    this.conversations.set(conversation.id, conversation)
    
    // 触发事件
    this.ctx.emit('conversation/created', conversation)
    
    return conversation
  }

  // 发送消息并获取响应
  async chat(conversationId: string, message: string): Promise<string> {
    const conversation = this.conversations.get(conversationId)
    if (!conversation) {
      throw new Error(`Conversation ${conversationId} not found`)
    }

    // 添加用户消息
    conversation.messages.push({
      role: 'user',
      content: message,
      timestamp: Date.now()
    })

    // 调用 LLM
    const response = await this.ctx.llm.chat({
      model: this.config.model,
      messages: conversation.messages,
      temperature: this.config.temperature ?? 0.7
    })

    // 添加助手消息
    conversation.messages.push({
      role: 'assistant',
      content: response.content,
      timestamp: Date.now()
    })

    // 触发事件
    this.ctx.emit('conversation/message', {
      conversationId,
      message: response.content
    })

    return response.content
  }

  // 获取会话历史
  getHistory(conversationId: string): Message[] {
    const conversation = this.conversations.get(conversationId)
    return conversation?.messages ?? []
  }

  private generateId(): string {
    return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
}

// 类型声明合并
declare module 'cordis' {
  interface Context {
    myAgent: MyAgent
  }
}

// 插件导出
export const name = 'my-agent'
export const inject = ['llm']

export function apply(ctx: Context, config: MyAgentConfig) {
  ctx.plugin(MyAgent, config)
}
```

### 2.2 创建自定义工具

```typescript
import { Context, Disposable } from 'cordis'

// 工具定义
interface ToolDefinition {
  name: string
  description: string
  parameters: {
    type: 'object'
    properties: Record<string, any>
    required?: string[]
  }
  execute: (params: any) => Promise<any>
}

// 文件读取工具
export const readFileTool: ToolDefinition = {
  name: 'read_file',
  description: '读取指定路径的文件内容',
  parameters: {
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: '文件路径'
      },
      encoding: {
        type: 'string',
        description: '文件编码',
        default: 'utf-8'
      }
    },
    required: ['path']
  },
  execute: async (params) => {
    const { path, encoding = 'utf-8' } = params
    
    // 安全检查
    if (!ctx.fs.isAllowed(path)) {
      throw new Error(`Access denied: ${path}`)
    }
    
    const content = await ctx.fs.readFile(path, encoding)
    return { content, path }
  }
}

// 代码执行工具
export const codeExecTool: ToolDefinition = {
  name: 'execute_code',
  description: '在沙箱中执行代码',
  parameters: {
    type: 'object',
    properties: {
      language: {
        type: 'string',
        enum: ['javascript', 'python', 'typescript'],
        description: '编程语言'
      },
      code: {
        type: 'string',
        description: '要执行的代码'
      },
      timeout: {
        type: 'number',
        description: '超时时间（毫秒）',
        default: 5000
      }
    },
    required: ['language', 'code']
  },
  execute: async (params) => {
    const { language, code, timeout = 5000 } = params
    
    // 在沙箱中执行
    const result = await ctx.sandbox.execute({
      language,
      code,
      timeout
    })
    
    return {
      output: result.stdout,
      error: result.stderr,
      exitCode: result.exitCode
    }
  }
}

// 工具注册插件
export const name = 'custom-tools'
export const inject = ['tools', 'fs', 'sandbox']

export function apply(ctx: Context) {
  // 注册工具
  const disposables: Disposable[] = []
  
  disposables.push(ctx.tools.register(readFileTool))
  disposables.push(ctx.tools.register(codeExecTool))
  
  // 返回清理函数
  return () => {
    disposables.forEach(d => d())
  }
}
```

### 2.3 实现事件驱动的中间件

```typescript
import { Context } from 'cordis'

// 请求日志中间件
export function requestLogger(ctx: Context) {
  ctx.on('agent/pre-request', async (request, next) => {
    const startTime = Date.now()
    
    console.log(`[${new Date().toISOString()}] Request started`)
    console.log(`  Model: ${request.model}`)
    console.log(`  Messages: ${request.messages.length}`)
    
    // 继续执行
    const response = await next()
    
    const duration = Date.now() - startTime
    console.log(`[${new Date().toISOString()}] Request completed in ${duration}ms`)
    console.log(`  Tokens: ${response.usage?.total_tokens ?? 'N/A'}`)
    
    return response
  })
}

// 请求限流中间件
export function rateLimiter(ctx: Context, options: { maxRequests: number; windowMs: number }) {
  const requests: number[] = []
  
  ctx.on('agent/pre-request', async (request, next) => {
    const now = Date.now()
    
    // 清理过期记录
    while (requests.length > 0 && requests[0] < now - options.windowMs) {
      requests.shift()
    }
    
    // 检查限流
    if (requests.length >= options.maxRequests) {
      const waitTime = requests[0] + options.windowMs - now
      console.log(`Rate limit reached, waiting ${waitTime}ms...`)
      await new Promise(resolve => setTimeout(resolve, waitTime))
    }
    
    // 记录请求
    requests.push(now)
    
    return next()
  })
}

// 错误重试中间件
export function retryOnError(ctx: Context, options: { maxRetries: number; delayMs: number }) {
  ctx.on('agent/pre-request', async (request, next) => {
    let lastError: Error | null = null
    
    for (let attempt = 0; attempt <= options.maxRetries; attempt++) {
      try {
        return await next()
      } catch (error) {
        lastError = error as Error
        
        if (attempt < options.maxRetries) {
          console.log(`Request failed, retrying (${attempt + 1}/${options.maxRetries})...`)
          await new Promise(resolve => setTimeout(resolve, options.delayMs * (attempt + 1)))
        }
      }
    }
    
    throw lastError
  })
}

// 插件导出
export const name = 'middleware-stack'
export const inject = ['agent']

export function apply(ctx: Context) {
  // 注册中间件
  requestLogger(ctx)
  
  rateLimiter(ctx, {
    maxRequests: 10,
    windowMs: 60000 // 1分钟
  })
  
  retryOnError(ctx, {
    maxRetries: 3,
    delayMs: 1000
  })
}
```

### 2.4 实现自定义存储后端

```typescript
import { Service, Context } from 'cordis'

// 存储接口
interface StorageBackend {
  get(key: string): Promise<string | null>
  set(key: string, value: string, ttl?: number): Promise<void>
  delete(key: string): Promise<void>
  has(key: string): Promise<boolean>
  clear(): Promise<void>
}

// Redis 存储实现
export class RedisStorage extends Service implements StorageBackend {
  private client: any

  constructor(ctx: Context, config: { url: string }) {
    super(ctx, 'storage')
    this.initClient(config.url)
  }

  private async initClient(url: string) {
    // 初始化 Redis 客户端
    this.client = await createRedisClient(url)
  }

  async get(key: string): Promise<string | null> {
    return this.client.get(key)
  }

  async set(key: string, value: string, ttl?: number): Promise<void> {
    if (ttl) {
      await this.client.setex(key, ttl, value)
    } else {
      await this.client.set(key, value)
    }
  }

  async delete(key: string): Promise<void> {
    await this.client.del(key)
  }

  async has(key: string): Promise<boolean> {
    return (await this.client.exists(key)) === 1
  }

  async clear(): Promise<void> {
    await this.client.flushdb()
  }
}

// 内存存储实现（用于测试）
export class MemoryStorage extends Service implements StorageBackend {
  private store: Map<string, { value: string; expiresAt?: number }> = new Map()

  constructor(ctx: Context) {
    super(ctx, 'storage')
  }

  async get(key: string): Promise<string | null> {
    const item = this.store.get(key)
    
    if (!item) return null
    
    // 检查是否过期
    if (item.expiresAt && Date.now() > item.expiresAt) {
      this.store.delete(key)
      return null
    }
    
    return item.value
  }

  async set(key: string, value: string, ttl?: number): Promise<void> {
    this.store.set(key, {
      value,
      expiresAt: ttl ? Date.now() + ttl * 1000 : undefined
    })
  }

  async delete(key: string): Promise<void> {
    this.store.delete(key)
  }

  async has(key: string): Promise<boolean> {
    const value = await this.get(key)
    return value !== null
  }

  async clear(): Promise<void> {
    this.store.clear()
  }
}

// 类型声明
declare module 'cordis' {
  interface Context {
    storage: StorageBackend
  }
}

// 插件配置
interface StorageConfig {
  backend: 'redis' | 'memory'
  redis?: {
    url: string
  }
}

// 插件导出
export const name = 'storage-plugin'

export function apply(ctx: Context, config: StorageConfig) {
  if (config.backend === 'redis' && config.redis) {
    ctx.plugin(RedisStorage, config.redis)
  } else {
    ctx.plugin(MemoryStorage)
  }
}
```

### 2.5 实现会话持久化

```typescript
import { Service, Context } from 'cordis'
import * as fs from 'fs/promises'
import * as path from 'path'

// 会话数据结构
interface SessionData {
  id: string
  userId: string
  messages: Message[]
  metadata: Record<string, any>
  createdAt: number
  updatedAt: number
}

// 会话存储服务
export class SessionStore extends Service {
  private basePath: string

  constructor(ctx: Context, config: { basePath: string }) {
    super(ctx, 'sessionStore')
    this.basePath = config.basePath
  }

  // 保存会话
  async save(session: SessionData): Promise<void> {
    const filePath = this.getFilePath(session.id)
    const dirPath = path.dirname(filePath)

    // 确保目录存在
    await fs.mkdir(dirPath, { recursive: true })

    // 更新时间戳
    session.updatedAt = Date.now()

    // 写入文件
    await fs.writeFile(filePath, JSON.stringify(session, null, 2), 'utf-8')

    // 触发事件
    this.ctx.emit('session/saved', session)
  }

  // 加载会话
  async load(sessionId: string): Promise<SessionData | null> {
    const filePath = this.getFilePath(sessionId)

    try {
      const content = await fs.readFile(filePath, 'utf-8')
      return JSON.parse(content)
    } catch (error) {
      if ((error as any).code === 'ENOENT') {
        return null
      }
      throw error
    }
  }

  // 删除会话
  async delete(sessionId: string): Promise<void> {
    const filePath = this.getFilePath(sessionId)

    try {
      await fs.unlink(filePath)
      this.ctx.emit('session/deleted', sessionId)
    } catch (error) {
      if ((error as any).code !== 'ENOENT') {
        throw error
      }
    }
  }

  // 列出用户的所有会话
  async listByUser(userId: string): Promise<SessionData[]> {
    const userDir = path.join(this.basePath, userId)

    try {
      const files = await fs.readdir(userDir)
      const sessions: SessionData[] = []

      for (const file of files) {
        if (file.endsWith('.json')) {
          const session = await this.load(file.replace('.json', ''))
          if (session) {
            sessions.push(session)
          }
        }
      }

      return sessions.sort((a, b) => b.updatedAt - a.updatedAt)
    } catch (error) {
      if ((error as any).code === 'ENOENT') {
        return []
      }
      throw error
    }
  }

  // 获取文件路径
  private getFilePath(sessionId: string): string {
    // 从 sessionId 中提取 userId
    const parts = sessionId.split('_')
    const userId = parts[0] || 'default'

    return path.join(this.basePath, userId, `${sessionId}.json`)
  }
}

// 类型声明
declare module 'cordis' {
  interface Context {
    sessionStore: SessionStore
  }
}

// 插件导出
export const name = 'session-store'
export const inject = []

interface SessionStoreConfig {
  basePath: string
}

export function apply(ctx: Context, config: SessionStoreConfig) {
  ctx.plugin(SessionStore, config)
}
```

### 2.6 实现工具执行管道

```typescript
import { Context, Disposable } from 'cordis'

// 工具执行上下文
interface ToolExecutionContext {
  toolName: string
  parameters: any
  userId: string
  sessionId: string
  startTime: number
}

// 工具执行结果
interface ToolExecutionResult {
  success: boolean
  result?: any
  error?: string
  duration: number
}

// 工具执行管道
export class ToolPipeline {
  private middlewares: Array<(ctx: ToolExecutionContext, next: () => Promise<ToolExecutionResult>) => Promise<ToolExecutionResult>> = []

  // 添加中间件
  use(middleware: (ctx: ToolExecutionContext, next: () => Promise<ToolExecutionResult>) => Promise<ToolExecutionResult>) {
    this.middlewares.push(middleware)
  }

  // 执行管道
  async execute(context: ToolExecutionContext, handler: () => Promise<any>): Promise<ToolExecutionResult> {
    let index = 0

    const next = async (): Promise<ToolExecutionResult> => {
      if (index >= this.middlewares.length) {
        // 执行实际的工具处理器
        const startTime = Date.now()
        try {
          const result = await handler()
          return {
            success: true,
            result,
            duration: Date.now() - startTime
          }
        } catch (error) {
          return {
            success: false,
            error: (error as Error).message,
            duration: Date.now() - startTime
          }
        }
      }

      const middleware = this.middlewares[index++]
      return middleware(context, next)
    }

    return next()
  }
}

// 工具执行插件
export const name = 'tool-pipeline'
export const inject = ['tools']

export function apply(ctx: Context) {
  const pipeline = new ToolPipeline()

  // 添加日志中间件
  pipeline.use(async (context, next) => {
    console.log(`[Tool] Executing ${context.toolName}`)
    const result = await next()
    console.log(`[Tool] ${context.toolName} completed in ${result.duration}ms`)
    return result
  })

  // 添加权限检查中间件
  pipeline.use(async (context, next) => {
    const hasPermission = await ctx.permissions.check(
      context.userId,
      'tool',
      context.toolName
    )

    if (!hasPermission) {
      return {
        success: false,
        error: 'Permission denied',
        duration: 0
      }
    }

    return next()
  })

  // 添加超时中间件
  pipeline.use(async (context, next) => {
    const timeout = 30000 // 30秒

    return Promise.race([
      next(),
      new Promise<ToolExecutionResult>((_, reject) => {
        setTimeout(() => {
          reject(new Error(`Tool execution timed out after ${timeout}ms`))
        }, timeout)
      })
    ])
  })

  // 拦截工具执行
  ctx.on('tools/pre-execute', async (event) => {
    const context: ToolExecutionContext = {
      toolName: event.tool.name,
      parameters: event.parameters,
      userId: event.userId,
      sessionId: event.sessionId,
      startTime: Date.now()
    }

    const result = await pipeline.execute(context, async () => {
      return event.tool.execute(event.parameters)
    })

    if (!result.success) {
      throw new Error(result.error)
    }

    // 替换原始执行
    event.result = result.result
    event.preventDefault()
  })
}
```

### 2.7 实现 Agent 预设配置

```typescript
// presets/code-assistant.yml
/*
name: code-assistant
description: 代码助手 Agent 预设

model:
  provider: deepseek
  name: deepseek-coder
  temperature: 0.3

system_prompt: |
  你是一个专业的代码助手。你的职责是：
  1. 帮助用户编写、审查和优化代码
  2. 解释代码逻辑和最佳实践
  3. 协助调试和解决问题
  
  请始终遵循以下原则：
  - 编写清晰、可维护的代码
  - 添加适当的注释和文档
  - 考虑性能和安全性
  - 遵循项目的编码规范

tools:
  - read_file
  - write_file
  - execute_code
  - search_code
  - git_status

middleware:
  - name: request-logger
  - name: rate-limiter
    config:
      maxRequests: 20
      windowMs: 60000

settings:
  max_tokens: 4096
  auto_save: true
  session_timeout: 3600
*/

// 加载预设的插件
import { Context } from 'cordis'
import * as yaml from 'yaml'
import * as fs from 'fs/promises'

interface PresetConfig {
  name: string
  description: string
  model: {
    provider: string
    name: string
    temperature: number
  }
  system_prompt: string
  tools: string[]
  middleware: Array<{
    name: string
    config?: any
  }>
  settings: Record<string, any>
}

export const name = 'preset-loader'
export const inject = ['llm', 'tools', 'agent']

export function apply(ctx: Context) {
  // 注册加载预设的方法
  ctx.provide('loadPreset', async (presetPath: string) => {
    // 读取预设文件
    const content = await fs.readFile(presetPath, 'utf-8')
    const preset: PresetConfig = yaml.parse(content)

    // 配置模型
    ctx.llm.configure({
      provider: preset.model.provider,
      model: preset.model.name,
      temperature: preset.model.temperature
    })

    // 注册系统提示词
    ctx.agent.setSystemPrompt(preset.system_prompt)

    // 注册工具
    for (const toolName of preset.tools) {
      const tool = ctx.tools.get(toolName)
      if (tool) {
        ctx.agent.registerTool(tool)
      }
    }

    // 应用中间件
    for (const middleware of preset.middleware) {
      await ctx.plugin(middleware.name, middleware.config)
    }

    // 应用设置
    for (const [key, value] of Object.entries(preset.settings)) {
      ctx.settings.set(key, value)
    }

    return preset
  })
}
```

---

## 三、完整工作流示例

### 3.1 构建一个简单的聊天机器人

```typescript
// index.ts
import { Context } from 'cordis'
import { createApp } from '@deepseek-ai/dsh'

async function main() {
  // 创建应用
  const app = await createApp({
    profile: 'headless',
    plugins: [
      // LLM 配置
      {
        name: '@deepseek-ai/dsh-llm-deepseek',
        config: {
          apiKey: process.env.DEEPSEEK_API_KEY,
          model: 'deepseek-chat'
        }
      },
      // 自定义 Agent
      {
        name: './my-agent.ts',
        config: {
          name: 'chat-bot',
          model: 'deepseek-chat',
          temperature: 0.7
        }
      },
      // 工具集
      {
        name: './custom-tools.ts'
      }
    ]
  })

  // 获取 Agent
  const agent = app.ctx.myAgent

  // 创建会话
  const conversation = await agent.createConversation('user-123')

  // 进行对话
  console.log('Bot: 你好！有什么我可以帮助你的吗？')

  // 模拟用户输入
  const userMessage = '请帮我写一个快速排序算法'
  console.log(`User: ${userMessage}`)

  const response = await agent.chat(conversation.id, userMessage)
  console.log(`Bot: ${response}`)

  // 关闭应用
  await app.stop()
}

main().catch(console.error)
```

### 3.2 运行结果示例

```
Bot: 你好！有什么我可以帮助你的吗？
User: 请帮我写一个快速排序算法
Bot: 好的，这是一个 TypeScript 实现的快速排序算法：

```typescript
function quickSort(arr: number[]): number[] {
  if (arr.length <= 1) {
    return arr
  }

  const pivot = arr[Math.floor(arr.length / 2)]
  const left = arr.filter(x => x < pivot)
  const middle = arr.filter(x => x === pivot)
  const right = arr.filter(x => x > pivot)

  return [...quickSort(left), ...middle, ...quickSort(right)]
}

// 使用示例
const numbers = [64, 34, 25, 12, 22, 11, 90]
console.log('排序前:', numbers)
console.log('排序后:', quickSort(numbers))
```

这个实现的特点：
1. **简洁清晰**：使用函数式编程风格，易于理解
2. **稳定排序**：相等元素保持原有顺序
3. **递归实现**：代码结构清晰

时间复杂度：
- 平均情况：O(n log n)
- 最坏情况：O(n²)

空间复杂度：O(n)

需要我进一步解释代码逻辑或者提供其他语言的实现吗？
```

---

## 四、调试和测试示例

### 4.1 单元测试示例

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { Context } from 'cordis'
import { MyAgent } from './my-agent'

describe('MyAgent', () => {
  let ctx: Context
  let agent: MyAgent

  beforeEach(async () => {
    ctx = new Context()
    
    // Mock LLM 服务
    ctx.provide('llm', {
      chat: async (request) => ({
        content: `Echo: ${request.messages[request.messages.length - 1].content}`,
        usage: { total_tokens: 100 }
      })
    })

    // 创建 Agent
    agent = new MyAgent(ctx, {
      name: 'test-agent',
      model: 'test-model'
    })
  })

  it('should create conversation', async () => {
    const conversation = await agent.createConversation('user-1')
    
    expect(conversation.id).toBeDefined()
    expect(conversation.userId).toBe('user-1')
    expect(conversation.messages).toHaveLength(0)
  })

  it('should handle chat messages', async () => {
    const conversation = await agent.createConversation('user-1')
    
    const response = await agent.chat(conversation.id, 'Hello')
    
    expect(response).toBe('Echo: Hello')
    
    const history = agent.getHistory(conversation.id)
    expect(history).toHaveLength(2)
    expect(history[0].role).toBe('user')
    expect(history[1].role).toBe('assistant')
  })

  it('should throw error for non-existent conversation', async () => {
    await expect(
      agent.chat('non-existent', 'Hello')
    ).rejects.toThrow('Conversation non-existent not found')
  })
})
```

### 4.2 集成测试示例

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { createApp } from '@deepseek-ai/dsh'

describe('Integration Tests', () => {
  let app: any

  beforeAll(async () => {
    app = await createApp({
      profile: 'headless',
      plugins: [
        {
          name: '@deepseek-ai/dsh-llm-deepseek',
          config: {
            apiKey: process.env.DEEPSEEK_API_KEY
          }
        }
      ]
    })
  })

  afterAll(async () => {
    await app.stop()
  })

  it('should complete a full conversation flow', async () => {
    const session = await app.ctx.sessions.create({
      userId: 'test-user'
    })

    // 发送消息
    const response = await app.ctx.agent.sendMessage(session.id, {
      content: 'What is 2 + 2?'
    })

    expect(response.content).toContain('4')
    expect(response.sessionId).toBe(session.id)

    // 验证会话历史
    const history = await app.ctx.sessions.getHistory(session.id)
    expect(history.length).toBeGreaterThanOrEqual(2)
  }, 30000) // 30秒超时
})
```

---

## 五、性能优化示例

### 5.1 批量处理优化

```typescript
import { Context } from 'cordis'

export const name = 'batch-optimizer'
export const inject = ['llm']

export function apply(ctx: Context) {
  // 批量消息队列
  const messageQueue: Array<{
    messages: any[]
    resolve: (response: any) => void
    reject: (error: Error) => void
  }> = []

  let batchTimer: NodeJS.Timeout | null = null

  // 批量处理函数
  async function processBatch() {
    if (messageQueue.length === 0) return

    const batch = messageQueue.splice(0, 10) // 最多处理10条
    const allMessages = batch.map(item => item.messages)

    try {
      // 并行处理
      const responses = await Promise.all(
        allMessages.map(messages => ctx.llm.chat({ messages }))
      )

      // 分发结果
      responses.forEach((response, index) => {
        batch[index].resolve(response)
      })
    } catch (error) {
      // 分发错误
      batch.forEach(item => {
        item.reject(error as Error)
      })
    }
  }

  // 拦截 LLM 调用
  ctx.intercept('llm', {
    chat: async (request) => {
      return new Promise((resolve, reject) => {
        messageQueue.push({
          messages: request.messages,
          resolve,
          reject
        })

        // 设置批量处理定时器
        if (!batchTimer) {
          batchTimer = setTimeout(() => {
            batchTimer = null
            processBatch()
          }, 100) // 100ms 批处理窗口
        }

        // 如果队列满了，立即处理
        if (messageQueue.length >= 10) {
          if (batchTimer) {
            clearTimeout(batchTimer)
            batchTimer = null
          }
          processBatch()
        }
      })
    }
  })
}
```

### 5.2 缓存优化

```typescript
import { Context } from 'cordis'

interface CacheEntry {
  value: any
  expiresAt: number
}

export const name = 'cache-optimizer'
export const inject = ['llm']

export function apply(ctx: Context) {
  const cache = new Map<string, CacheEntry>()
  const maxCacheSize = 1000
  const defaultTTL = 3600000 // 1小时

  // 生成缓存键
  function getCacheKey(messages: any[]): string {
    return JSON.stringify(messages)
  }

  // 清理过期缓存
  function cleanupCache() {
    const now = Date.now()
    for (const [key, entry] of cache.entries()) {
      if (entry.expiresAt < now) {
        cache.delete(key)
      }
    }
  }

  // 拦截 LLM 调用
  ctx.intercept('llm', {
    chat: async (request, original) => {
      const cacheKey = getCacheKey(request.messages)
      
      // 检查缓存
      const cached = cache.get(cacheKey)
      if (cached && cached.expiresAt > Date.now()) {
        console.log('Cache hit')
        return cached.value
      }

      // 调用原始方法
      const response = await original(request)

      // 存入缓存
      if (cache.size >= maxCacheSize) {
        cleanupCache()
        
        if (cache.size >= maxCacheSize) {
          // 删除最旧的条目
          const firstKey = cache.keys().next().value
          cache.delete(firstKey)
        }
      }

      cache.set(cacheKey, {
        value: response,
        expiresAt: Date.now() + defaultTTL
      })

      return response
    }
  })

  // 定期清理缓存
  setInterval(cleanupCache, 60000) // 每分钟清理一次
}
```

---

## 六、部署配置示例

### 6.1 Docker 部署

```dockerfile
# Dockerfile
FROM node:22-alpine

WORKDIR /app

# 安装依赖
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

# 复制源码
COPY . .

# 构建
RUN pnpm build

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["node", "dist/cli.js", "--profile", "web"]
```

### 6.2 环境变量配置

```bash
# .env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 服务配置
PORT=3000
HOST=0.0.0.0

# 存储配置
STORAGE_BACKEND=redis
REDIS_URL=redis://localhost:6379

# 安全配置
SESSION_SECRET=your_session_secret
CORS_ORIGIN=http://localhost:3000

# 日志配置
LOG_LEVEL=info
LOG_FORMAT=json
```

### 6.3 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  dsh:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./data:/app/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

---

以上是 DeepSeek Harness 架构文档的补充材料，包含了详细的代码示例、时序图描述和实际使用场景。这些示例可以帮助开发者快速上手并深入理解 DSH 的架构设计。