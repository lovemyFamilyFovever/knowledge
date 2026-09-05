---
title: "DeepSeek Harness (DSH) 插件开发教程 - 第二部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 插件开发教程"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness (DSH) 插件开发教程 - 第二部分

## 创建自定义 Model Provider 插件

### 1. LLM 抽象层接口

DSH 的 LLM 抽象层定义了模型提供商适配器需要实现的接口。核心是 `LlmAdapter` 类，它负责将 DSH 的通用请求转换为特定提供商的 API 调用，并将响应流转换回 DSH 的通用格式。

#### 1.1 核心类型定义

```typescript
// 生成选项
interface GenerateOptions {
  provider: string           // 提供商路由键
  model: string              // 模型 ID
  messages: Message[]        // 消息历史
  tools?: ToolSchema[]       // 可用工具列表
  signal?: AbortSignal       // 取消信号
  maxTokens?: number         // 最大输出 token 数
  temperature?: number       // 温度参数
  // ... 其他选项
}

// 流式响应块
interface StreamChunk {
  // 内容块
  type: 'content'
  index: number
  delta: {
    type: 'text' | 'reasoning' | 'tool-call'
    text?: string
    argumentsDelta?: string
  }
} | {
  // 使用量统计
  type: 'usage'
  usage: TokenUsage
} | {
  // 完成信号
  type: 'finish'
  reason: FinishReason
  replayState?: JsonValue
}

// Token 使用量
interface TokenUsage {
  inputTokens: number
  outputTokens: number
  cacheReadTokens?: number
  cacheWriteTokens?: number
  reasoningTokens?: number
}
```

#### 1.2 适配器基类

```typescript
abstract class LlmAdapter {
  /**
   * 流式生成响应
   * @param options - 生成选项
   * @returns 异步可迭代的流式响应块
   */
  abstract stream(options: GenerateOptions): AsyncIterable<StreamChunk>
  
  /**
   * 解析模型元数据（可选）
   * @param provider - 提供商路由键
   * @param model - 模型 ID
   * @returns 模型能力信息
   */
  resolveModel?(provider: string, model: string): ModelMetadata | undefined
  
  /**
   * 列出可用模型（可选）
   * @returns 模型列表
   */
  listModels?(): ModelInfo[]
}
```

### 2. 实现自定义 Provider

下面是一个完整的自定义 LLM Provider 适配器实现示例：

```typescript
// packages/llm/llm-custom/src/adapter.ts
import { LlmAdapter, LlmError } from '@deepseek-ai/dsh-llm'
import type { 
  GenerateOptions, 
  StreamChunk, 
  TokenUsage,
  FinishReason,
  ContentBlock 
} from '@deepseek-ai/dsh-llm'

// 连接配置
export interface CustomProviderConnection {
  apiKey: string
  baseUrl: string
  timeout?: number
}

// 模型配置
export interface CustomProviderModel {
  id: string
  name: string
  contextWindow: number
  maxTokens?: number
}

export class CustomProviderAdapter extends LlmAdapter {
  constructor(
    private readonly connection: () => CustomProviderConnection,
    private readonly models: CustomProviderModel[],
  ) {
    super()
  }
  
  async * stream(options: GenerateOptions): AsyncIterable<StreamChunk> {
    const conn = this.connection()
    
    // 构建请求体
    const body = {
      model: options.model,
      messages: this.formatMessages(options.messages),
      stream: true,
      max_tokens: options.maxTokens,
      temperature: options.temperature,
      tools: options.tools?.length ? this.formatTools(options.tools) : undefined,
    }
    
    // 发送请求
    const response = await fetch(`${conn.baseUrl}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${conn.apiKey}`,
      },
      body: JSON.stringify(body),
      signal: options.signal,
    })
    
    if (!response.ok) {
      const error = await response.text()
      throw new LlmError(
        `Custom provider error: ${response.status} - ${error}`,
        'PROVIDER_ERROR',
        { status: response.status }
      )
    }
    
    // 解析 SSE 流
    const reader = response.body?.getReader()
    if (!reader) throw new LlmError('No response body', 'STREAM_ERROR')
    
    const decoder = new TextDecoder()
    let buffer = ''
    let blockIndex = 0
    
    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') continue
          
          try {
            const chunk = JSON.parse(data)
            yield* this.processChunk(chunk, blockIndex)
            
            // 更新块索引
            if (chunk.choices?.[0]?.delta?.content) {
              blockIndex++
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }
  
  private formatMessages(messages: any[]): any[] {
    return messages.map(msg => ({
      role: msg.role,
      content: msg.content,
      // 根据需要转换消息格式
    }))
  }
  
  private formatTools(tools: any[]): any[] {
    return tools.map(tool => ({
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters,
      },
    }))
  }
  
  private * processChunk(chunk: any, blockIndex: number): Iterable<StreamChunk> {
    const choice = chunk.choices?.[0]
    if (!choice) return
    
    const delta = choice.delta
    
    // 文本内容
    if (delta?.content) {
      yield {
        type: 'content',
        index: blockIndex,
        delta: { type: 'text', text: delta.content },
      }
    }
    
    // 工具调用
    if (delta?.tool_calls) {
      for (const toolCall of delta.tool_calls) {
        yield {
          type: 'content',
          index: toolCall.index ?? blockIndex,
          delta: {
            type: 'tool-call',
            argumentsDelta: toolCall.function?.arguments,
          },
        }
      }
    }
    
    // 使用量统计（通常在最后一个块）
    if (chunk.usage) {
      yield {
        type: 'usage',
        usage: {
          inputTokens: chunk.usage.prompt_tokens,
          outputTokens: chunk.usage.completion_tokens,
        },
      }
    }
    
    // 完成信号
    if (choice.finish_reason) {
      const reasonMap: Record<string, FinishReason> = {
        'stop': { kind: 'stop' },
        'tool_calls': { kind: 'tool-calls' },
        'length': { kind: 'max-tokens' },
      }
      
      yield {
        type: 'finish',
        reason: reasonMap[choice.finish_reason] || { kind: 'stop' },
      }
    }
  }
}
```

### 3. 配置和使用

#### 3.1 插件入口文件

```typescript
// packages/llm/llm-custom/src/index.ts
import type { Context } from '@deepseek-ai/cordis'
import z from '@deepseek-ai/schemastery'
import { CustomProviderAdapter } from './adapter.ts'

export const name = 'llm-custom'
export const inject = ['llm']

// 配置模式
export const Config = z.object({
  apiKey: z.string().role('secret'),
  baseUrl: z.string().default('https://api.custom-llm.com'),
  models: z.array(z.object({
    id: z.string().required(),
    name: z.string(),
    contextWindow: z.number().default(128000),
    maxTokens: z.number(),
  })).default([
    { id: 'custom-model-v1', name: 'Custom Model V1', contextWindow: 128000 },
  ]),
  timeout: z.number().default(300000),
})

export type Config = z.infer<typeof Config>

export function apply(ctx: Context, config: Config) {
  // 创建适配器实例
  const adapter = new CustomProviderAdapter(
    () => ({
      apiKey: config.apiKey,
      baseUrl: config.baseUrl,
      timeout: config.timeout,
    }),
    config.models,
  )
  
  // 注册可配置的提供商
  ctx.llm.registerConfigurableProviders([{
    provider: 'custom-provider',
    displayName: 'Custom LLM Provider',
    settingsNs: 'llm-custom',
    settingsPath: [],
  }])
  
  // 注册适配器
  const registration = ctx.llm.registerAdapter(['custom-provider'], adapter)
  
  // 清理函数（可选，通常不需要因为 Cordis 会自动处理）
  return () => {
    registration.dispose()
  }
}
```

#### 3.2 配置文件示例

```yaml
# cordis.yml
- id: llm-custom
  config:
    apiKey: '!!js process.env.CUSTOM_LLM_API_KEY'
    baseUrl: 'https://api.custom-llm.com'
    models:
      - id: 'custom-model-v1'
        name: 'Custom Model V1'
        contextWindow: 128000
      - id: 'custom-model-v2'
        name: 'Custom Model V2'
        contextWindow: 256000
        maxTokens: 32000
```

#### 3.3 在代码中使用

```typescript
// 在其他插件中使用注册的 LLM
export function apply(ctx: Context) {
  // 列出所有可用的提供商
  const providers = ctx.llm.listProviders()
  console.log('Available providers:', providers)
  
  // 列出所有可用的模型
  const models = ctx.llm.listModels()
  console.log('Available models:', models)
  
  // 监听适配器更新事件
  ctx.on('llm/adapters-updated', () => {
    console.log('LLM adapters updated')
  })
}
```

---

## 创建存储后端插件

### 1. 存储抽象层

DSH 的存储系统由以下几个层次组成：

1. **Storage Hub** (`ctx.storage`) - 存储中心，管理后端注册和数据表单挂载
2. **Backend** - 存储后端，负责实际的数据持久化
3. **Domain** - 数据域，定义数据的语义和操作

#### 1.1 存储后端接口

```typescript
// 存储后端接口
interface StorageBackend {
  /** 后端名称 */
  readonly name: string
  
  /** 读取数据 */
  read(unit: string, key: string): Promise<JsonValue | undefined>
  
  /** 写入数据 */
  write(unit: string, key: string, value: JsonValue): Promise<void>
  
  /** 删除数据 */
  delete(unit: string, key: string): Promise<boolean>
  
  /** 列出所有键 */
  keys(unit: string): Promise<string[]>
  
  /** 检查键是否存在 */
  has(unit: string, key: string): Promise<boolean>
  
  /** 清空单元 */
  clear(unit: string): Promise<void>
}

// KV 单元描述符
interface KvUnitDescriptor {
  /** 单元名称 */
  name: string
  /** 单元描述 */
  description?: string
}
```

### 2. 实现自定义存储

下面是一个完整的自定义存储后端实现示例（基于 Redis）：

```typescript
// packages/storage/storage-redis/src/backend.ts
import { StorageBackend, StorageError } from '@deepseek-ai/dsh-storage'
import type { JsonValue } from '@deepseek-ai/dsh-session'
import Redis from 'ioredis'

export interface RedisBackendConfig {
  host: string
  port: number
  password?: string
  db?: number
  keyPrefix?: string
}

export class RedisStorageBackend implements StorageBackend {
  readonly name = 'redis'
  private readonly client: Redis
  private readonly prefix: string
  
  constructor(config: RedisBackendConfig) {
    this.client = new Redis({
      host: config.host,
      port: config.port,
      password: config.password,
      db: config.db ?? 0,
    })
    this.prefix = config.keyPrefix ?? 'dsh:'
  }
  
  private getKey(unit: string, key: string): string {
    return `${this.prefix}${unit}:${key}`
  }
  
  async read(unit: string, key: string): Promise<JsonValue | undefined> {
    const value = await this.client.get(this.getKey(unit, key))
    if (value === null) return undefined
    try {
      return JSON.parse(value)
    } catch {
      throw new StorageError('parse-error', `Failed to parse stored value for ${unit}/${key}`)
    }
  }
  
  async write(unit: string, key: string, value: JsonValue): Promise<void> {
    await this.client.set(this.getKey(unit, key), JSON.stringify(value))
  }
  
  async delete(unit: string, key: string): Promise<boolean> {
    const result = await this.client.del(this.getKey(unit, key))
    return result > 0
  }
  
  async keys(unit: string): Promise<string[]> {
    const pattern = `${this.prefix}${unit}:*`
    const keys = await this.client.keys(pattern)
    return keys.map(k => k.slice(`${this.prefix}${unit}:`.length))
  }
  
  async has(unit: string, key: string): Promise<boolean> {
    const result = await this.client.exists(this.getKey(unit, key))
    return result > 0
  }
  
  async clear(unit: string): Promise<void> {
    const keys = await this.keys(unit)
    if (keys.length === 0) return
    
    const pipeline = this.client.pipeline()
    for (const key of keys) {
      pipeline.del(this.getKey(unit, key))
    }
    await pipeline.exec()
  }
  
  async disconnect(): Promise<void> {
    await this.client.quit()
  }
}
```

#### 2.1 插件入口文件

```typescript
// packages/storage/storage-redis/src/index.ts
import type { Context } from '@deepseek-ai/cordis'
import z from '@deepseek-ai/schemastery'
import { RedisStorageBackend } from './backend.ts'

export const name = 'storage-redis'
export const inject = ['storage']

export const Config = z.object({
  host: z.string().default('localhost'),
  port: z.number().default(6379),
  password: z.string().role('secret'),
  db: z.number().default(0),
  keyPrefix: z.string().default('dsh:'),
})

export type Config = z.infer<typeof Config>

export function apply(ctx: Context, config: Config) {
  // 创建后端实例
  const backend = new RedisStorageBackend({
    host: config.host,
    port: config.port,
    password: config.password,
    db: config.db,
    keyPrefix: config.keyPrefix,
  })
  
  // 注册后端
  const registration = ctx.storage.backend.register(backend.name, backend)
  
  // 注册生命周期服务（用于依赖管理）
  const serviceKey = `storage.backend.${backend.name}`
  ctx.provide(serviceKey, true)
  
  // 清理函数
  return () => {
    registration.dispose()
    backend.disconnect().catch(() => {})
    ctx.dispose(serviceKey)
  }
}
```

#### 2.2 配置文件示例

```yaml
# cordis.yml
- id: storage-redis
  config:
    host: '!!js process.env.REDIS_HOST || "localhost"'
    port: '!!js process.env.REDIS_PORT || 6379'
    password: '!!js process.env.REDIS_PASSWORD'
    db: 0
    keyPrefix: 'dsh:'
```

#### 2.3 使用存储后端

```typescript
// 在其他插件中使用存储
export function apply(ctx: Context) {
  // 通过存储域访问数据
  const domain = ctx.storage.domain
  
  // 读取数据
  const value = await domain.read('my-unit', 'my-key')
  
  // 写入数据
  await domain.write('my-unit', 'my-key', { foo: 'bar' })
  
  // 列出所有键
  const keys = await domain.keys('my-unit')
}
```

---

## 插件测试方法

### 1. 单元测试

DSH 使用 Vitest 作为测试框架。下面是一个典型的单元测试示例：

```typescript
// packages/tools/weather-tool/tests/weather-tool.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Context } from '@deepseek-ai/cordis'
import { apply, Config } from '../src/index.ts'

describe('weather-tool', () => {
  let ctx: Context
  
  beforeEach(() => {
    ctx = new Context()
    ctx.plugin(apply, {
      apiKey: 'test-api-key',
      baseUrl: 'https://api.test-weather.com',
    })
  })
  
  it('should register the tool', () => {
    const tools = ctx.get('tools')
    const tool = tools.get('get_weather')
    
    expect(tool).toBeDefined()
    expect(tool.name).toBe('get_weather')
    expect(tool.description).toContain('天气')
  })
  
  it('should validate parameters', () => {
    const tools = ctx.get('tools')
    const tool = tools.get('get_weather')
    
    // 测试必需参数
    expect(() => tool.validateArgs({})).toThrow()
    
    // 测试有效参数
    expect(() => tool.validateArgs({ city: '北京' })).not.toThrow()
    
    // 测试可选参数
    expect(() => tool.validateArgs({ city: '北京', unit: 'celsius' })).not.toThrow()
  })
  
  it('should execute successfully', async () => {
    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        city: '北京',
        temperature: 25,
        unit: 'celsius',
        condition: '晴',
        humidity: 40,
      }),
    })
    
    const tools = ctx.get('tools')
    const result = await tools.execute('get_weather', { city: '北京' })
    
    expect(result.city).toBe('北京')
    expect(result.temperature).toBe(25)
  })
  
  it('should handle API errors', async () => {
    // Mock fetch 错误
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: () => Promise.resolve('Internal Server Error'),
    })
    
    const tools = ctx.get('tools')
    
    await expect(
      tools.execute('get_weather', { city: '北京' })
    ).rejects.toThrow('Weather API error')
  })
})
```

### 2. 集成测试

集成测试验证多个插件之间的交互：

```typescript
// tests/integration/llm-tool-integration.spec.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Context } from '@deepseek-ai/cordis'
import { apply as applyLlm } from '../../packages/llm/llm-custom/src/index.ts'
import { apply as applyTool } from '../../packages/tools/weather-tool/src/index.ts'

describe('LLM and Tool Integration', () => {
  let ctx: Context
  
  beforeAll(async () => {
    ctx = new Context()
    
    // 加载 LLM 插件
    ctx.plugin(applyLlm, {
      apiKey: 'test-key',
      baseUrl: 'https://api.test.com',
    })
    
    // 加载工具插件
    ctx.plugin(applyTool, {
      apiKey: 'test-weather-key',
      baseUrl: 'https://api.test-weather.com',
    })
    
    // 等待插件初始化
    await ctx.start()
  })
  
  afterAll(async () => {
    await ctx.stop()
  })
  
  it('should have both LLM and tools available', () => {
    const llm = ctx.get('llm')
    const tools = ctx.get('tools')
    
    expect(llm).toBeDefined()
    expect(tools).toBeDefined()
  })
  
  it('should list tools in LLM context', () => {
    const tools = ctx.get('tools')
    const toolList = tools.list()
    
    expect(toolList).toContainEqual(
      expect.objectContaining({ name: 'get_weather' })
    )
  })
})
```

### 3. Mock 策略

#### 3.1 服务 Mock

```typescript
// 使用 Cordis 的 provide/mock 机制
import { Context } from '@deepseek-ai/cordis'

// Mock 一个服务
ctx.provide('llm', {
  registerAdapter: vi.fn(),
  listProviders: vi.fn().mockReturnValue([]),
  listModels: vi.fn().mockReturnValue([]),
})

// 或者使用完整的 Mock 类
class MockLlmService {
  registerAdapter = vi.fn()
  listProviders = vi.fn().mockReturnValue([])
  listModels = vi.fn().mockReturnValue([])
}

ctx.plugin((ctx) => {
  ctx.provide('llm', new MockLlmService())
})
```

#### 3.2 外部依赖 Mock

```typescript
// Mock fetch
global.fetch = vi.fn()

// Mock 文件系统
vi.mock('node:fs/promises', () => ({
  readFile: vi.fn(),
  writeFile: vi.fn(),
}))

// Mock 子进程
vi.mock('node:child_process', () => ({
  spawn: vi.fn(),
}))
```

#### 3.3 测试工具辅助函数

```typescript
// test-support/helpers.ts
import { Context } from '@deepseek-ai/cordis'

/**
 * 创建测试上下文
 */
export function createTestContext(): Context {
  const ctx = new Context()
  // 加载最小必要的插件集合
  return ctx
}

/**
 * 等待服务可用
 */
export async function waitForService(ctx: Context, key: string, timeout = 5000): Promise<void> {
  const start = Date.now()
  while (!ctx.get(key)) {
    if (Date.now() - start > timeout) {
      throw new Error(`Timeout waiting for service: ${key}`)
    }
    await new Promise(resolve => setTimeout(resolve, 100))
  }
}

/**
 * 创建 Mock 工具
 */
export function createMockTool(name: string, execute?: Function) {
  return {
    name,
    description: `Mock tool: ${name}`,
    parameters: {},
    execute: execute || vi.fn().mockResolvedValue({ success: true }),
  }
}
```
