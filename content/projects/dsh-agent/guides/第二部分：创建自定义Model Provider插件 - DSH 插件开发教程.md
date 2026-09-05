---
title: "第二部分：创建自定义Model Provider插件 - DSH 插件开发教程"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 插件开发教程"
collected: "2026-09-05"
status: "imported"
---

第二部分：创建自定义Model Provider插件 - DSH 插件开发教程
← 上一部分
下一部分 →
🔌 第二部分：创建自定义 Model Provider 插件
🎯 核心目标
本部分将详细介绍如何创建自定义的 LLM Provider 适配器和存储后端插件，以及如何进行插件测试。
1. LLM 抽象层接口
DSH 的 LLM 抽象层定义了模型提供商适配器需要实现的接口。核心是
LlmAdapter
类，它负责将 DSH 的通用请求转换为特定提供商的 API 调用。
1.1 核心类型定义
// 生成选项
interface GenerateOptions {
  provider: string           // 提供商路由键
  model: string              // 模型 ID
  messages: Message[]        // 消息历史
  tools?: ToolSchema[]       // 可用工具列表
  signal?: AbortSignal       // 取消信号
  maxTokens?: number         // 最大输出 token 数
  temperature?: number       // 温度参数
}

// 流式响应块
interface StreamChunk {
  type: 'content'
  index: number
  delta: {
    type: 'text' | 'reasoning' | 'tool-call'
    text?: string
    argumentsDelta?: string
  }
} | {
  type: 'usage'
  usage: TokenUsage
} | {
  type: 'finish'
  reason: FinishReason
  replayState?: JsonValue
}
1.2 适配器基类
abstract class LlmAdapter {
  /**
   * 流式生成响应
   * @param options - 生成选项
   * @returns 异步可迭代的流式响应块
   */
  abstract stream(options: GenerateOptions): AsyncIterable<StreamChunk>
  
  /**
   * 解析模型元数据（可选）
   */
  resolveModel?(provider: string, model: string): ModelMetadata | undefined
  
  /**
   * 列出可用模型（可选）
   */
  listModels?(): ModelInfo[]
}
2. 实现自定义 Provider
下面是一个完整的自定义 LLM Provider 适配器实现示例：
// packages/llm/llm-custom/src/adapter.ts
import { LlmAdapter, LlmError } from '@deepseek-ai/dsh-llm'
import type { GenerateOptions, StreamChunk } from '@deepseek-ai/dsh-llm'

// 连接配置
export interface CustomProviderConnection {
  apiKey: string
  baseUrl: string
  timeout?: number
}

export class CustomProviderAdapter extends LlmAdapter {
  constructor(
    private readonly connection: () => CustomProviderConnection,
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
            yield* this.processChunk(chunk)
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
  
  private * processChunk(chunk: any): Iterable<StreamChunk> {
    const choice = chunk.choices?.[0]
    if (!choice) return
    
    const delta = choice.delta
    
    if (delta?.content) {
      yield {
        type: 'content',
        index: 0,
        delta: { type: 'text', text: delta.content },
      }
    }
    
    if (delta?.tool_calls) {
      for (const toolCall of delta.tool_calls) {
        yield {
          type: 'content',
          index: toolCall.index ?? 0,
          delta: {
            type: 'tool-call',
            argumentsDelta: toolCall.function?.arguments,
          },
        }
      }
    }
    
    if (chunk.usage) {
      yield {
        type: 'usage',
        usage: {
          inputTokens: chunk.usage.prompt_tokens,
          outputTokens: chunk.usage.completion_tokens,
        },
      }
    }
    
    if (choice.finish_reason) {
      const reasonMap: Record<string, any> = {
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
3. 配置和使用
3.1 插件入口文件
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
  })).default([
    { id: 'custom-model-v1', name: 'Custom Model V1', contextWindow: 128000 },
  ]),
})

export type Config = z.infer<typeof Config>

export function apply(ctx: Context, config: Config) {
  // 创建适配器实例
  const adapter = new CustomProviderAdapter(
    () => ({
      apiKey: config.apiKey,
      baseUrl: config.baseUrl,
    }),
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
}
4. 创建存储后端插件
4.1 存储后端接口
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
4.2 Redis 存储后端实现
// packages/storage/storage-redis/src/backend.ts
import { StorageBackend, StorageError } from '@deepseek-ai/dsh-storage'
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
    return JSON.parse(value)
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
5. 插件测试方法
5.1 单元测试
// packages/tools/weather-tool/tests/weather-tool.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Context } from '@deepseek-ai/cordis'
import { apply } from '../src/index.ts'

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
  })
  
  it('should validate parameters', () => {
    const tools = ctx.get('tools')
    const tool = tools.get('get_weather')
    
    expect(() => tool.validateArgs({})).toThrow()
    expect(() => tool.validateArgs({ city: '北京' })).not.toThrow()
  })
  
  it('should execute successfully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        city: '北京',
        temperature: 25,
        condition: '晴',
      }),
    })
    
    const tools = ctx.get('tools')
    const result = await tools.execute('get_weather', { city: '北京' })
    
    expect(result.city).toBe('北京')
    expect(result.temperature).toBe(25)
  })
})
5.2 Mock 策略
// Mock 一个服务
ctx.provide('llm', {
  registerAdapter: vi.fn(),
  listProviders: vi.fn().mockReturnValue([]),
  listModels: vi.fn().mockReturnValue([]),
})

// Mock fetch
global.fetch = vi.fn()

// Mock 文件系统
vi.mock('node:fs/promises', () => ({
  readFile: vi.fn(),
  writeFile: vi.fn(),
}))
←
上一部分
|
下一部分 →
📄 DeepSeek Harness Plugin Development Tutorial - Part 2