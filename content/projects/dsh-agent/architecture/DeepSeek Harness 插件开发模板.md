---
title: "DeepSeek Harness 插件开发模板"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 架构设计文档"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 插件开发模板

## 一、插件开发概述

### 1.1 什么是 DSH 插件

DSH 插件是基于 Cordis 框架的可扩展模块，通过注册服务、事件监听、工具提供等方式扩展系统功能。每个插件都是独立的功能单元，可以被动态加载、卸载和替换。

### 1.2 插件类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 服务插件 | 提供可复用的服务能力 | LLM 适配器、存储服务 |
| 工具插件 | 提供模型可调用的工具 | 文件操作、代码执行 |
| 中间件插件 | 拦截和处理请求 | 日志、限流、认证 |
| 预设插件 | 组合多个插件的配置 | 代码助手、写作助手 |

### 1.3 开发环境要求

- Node.js ≥ 22.19
- pnpm ≥ 8.0
- TypeScript ≥ 5.0
- 熟悉 Cordis 框架基本概念

---

## 二、插件结构规范

### 2.1 目录结构

```
my-plugin/
├── src/
│   ├── index.ts          # 插件入口
│   ├── service.ts        # 服务实现
│   ├── tools/            # 工具定义
│   │   ├── index.ts
│   │   └── ...
│   ├── types/            # 类型定义
│   │   └── index.ts
│   └── utils/            # 工具函数
│       └── index.ts
├── tests/                # 测试文件
│   ├── unit/
│   └── integration/
├── docs/                 # 文档
│   └── README.md
├── package.json          # 包配置
├── tsconfig.json         # TypeScript 配置
└── cordis.yml            # 插件配置（可选）
```

### 2.2 package.json 规范

```json
{
  "name": "@deepseek-ai/dsh-my-plugin",
  "version": "1.0.0",
  "description": "My DSH Plugin",
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/index.d.ts",
  "exports": {
    ".": {
      "import": "./lib/index.js",
      "types": "./lib/index.d.ts"
    }
  },
  "scripts": {
    "build": "tsc",
    "test": "vitest",
    "lint": "eslint src --ext .ts",
    "clean": "rm -rf lib"
  },
  "dependencies": {
    "@deepseek-ai/cordis": "workspace:*",
    "cosmokit": "^1.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "vitest": "^1.0.0",
    "@types/node": "^22.0.0"
  },
  "peerDependencies": {
    "@deepseek-ai/cordis": ">=4.0.0"
  },
  "dsh": {
    "plugin": true,
    "inject": ["llm", "tools"]
  }
}
```

### 2.3 tsconfig.json 规范

```json
{
  "compilerOptions": {
    "target": "ES2024",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "lib",
    "rootDir": "src",
    "declaration": true,
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "lib", "tests"]
}
```

---

## 三、从零创建插件

### 3.1 步骤一：初始化项目

```bash
# 创建插件目录
mkdir my-plugin
cd my-plugin

# 初始化 package.json
pnpm init

# 安装依赖
pnpm add @deepseek-ai/cordis cosmokit
pnpm add -D typescript vitest @types/node

# 创建目录结构
mkdir -p src/tools src/types src/utils tests/unit tests/integration docs
```

### 3.2 步骤二：定义类型

创建 `src/types/index.ts`：

```typescript
// 插件配置类型
export interface MyPluginConfig {
  enabled: boolean
  apiKey?: string
  baseUrl?: string
  timeout?: number
  maxRetries?: number
}

// 服务接口类型
export interface MyServiceOptions {
  model: string
  temperature?: number
  maxTokens?: number
}

// 工具参数类型
export interface MyToolParams {
  input: string
  options?: {
    format?: 'text' | 'json'
    verbose?: boolean
  }
}

// 工具结果类型
export interface MyToolResult {
  success: boolean
  data?: any
  error?: string
  duration: number
}

// 事件类型
export interface MyPluginEvents {
  'my-plugin/request': (params: MyToolParams) => void
  'my-plugin/response': (result: MyToolResult) => void
  'my-plugin/error': (error: Error) => void
}

// 扩展 Cordis Context 类型
declare module 'cordis' {
  interface Context {
    myService: MyService
  }
  
  interface Events extends MyPluginEvents {}
}
```

### 3.3 步骤三：实现服务

创建 `src/service.ts`：

```typescript
import { Service, Context } from 'cordis'
import type { MyPluginConfig, MyServiceOptions, MyToolResult } from './types/index.js'

export class MyService extends Service {
  static inject = ['llm', 'tools']
  
  private config: MyPluginConfig
  private requestCount = 0

  constructor(ctx: Context, config: MyPluginConfig) {
    super(ctx, 'myService')
    this.config = config
  }

  // 生命周期钩子：服务启动时调用
  async start() {
    this.ctx.logger.info('MyService starting...')
    
    // 注册事件监听
    this.ctx.on('my-plugin/request', (params) => {
      this.requestCount++
      this.ctx.logger.debug(`Request received: ${params.input}`)
    })
    
    this.ctx.logger.info(`MyService started (requests: ${this.requestCount})`)
  }

  // 生命周期钩子：服务停止时调用
  async stop() {
    this.ctx.logger.info('MyService stopping...')
    // 清理资源
  }

  // 核心方法：处理请求
  async process(input: string, options?: MyServiceOptions): Promise<MyToolResult> {
    const startTime = Date.now()
    
    try {
      // 触发请求事件
      this.ctx.emit('my-plugin/request', { input })
      
      // 调用 LLM 服务
      const response = await this.ctx.llm.chat({
        model: options?.model ?? 'deepseek-chat',
        messages: [
          { role: 'system', content: 'You are a helpful assistant.' },
          { role: 'user', content: input }
        ],
        temperature: options?.temperature ?? 0.7,
        maxTokens: options?.maxTokens ?? 1000
      })
      
      const result: MyToolResult = {
        success: true,
        data: response.content,
        duration: Date.now() - startTime
      }
      
      // 触发响应事件
      this.ctx.emit('my-plugin/response', result)
      
      return result
    } catch (error) {
      const result: MyToolResult = {
        success: false,
        error: (error as Error).message,
        duration: Date.now() - startTime
      }
      
      // 触发错误事件
      this.ctx.emit('my-plugin/error', error as Error)
      
      return result
    }
  }

  // 获取统计信息
  getStats() {
    return {
      requestCount: this.requestCount,
      uptime: process.uptime()
    }
  }
}
```

### 3.4 步骤四：定义工具

创建 `src/tools/index.ts`：

```typescript
import type { Context } from 'cordis'
import type { MyToolParams, MyToolResult } from '../types/index.js'

// 工具定义
export const myToolDefinition = {
  name: 'my_tool',
  description: '处理用户输入并返回结果',
  parameters: {
    type: 'object' as const,
    properties: {
      input: {
        type: 'string',
        description: '用户输入内容'
      },
      options: {
        type: 'object',
        properties: {
          format: {
            type: 'string',
            enum: ['text', 'json'],
            description: '输出格式'
          },
          verbose: {
            type: 'boolean',
            description: '是否详细输出'
          }
        },
        description: '处理选项'
      }
    },
    required: ['input']
  }
}

// 工具执行器
export function createMyTool(ctx: Context) {
  return async (params: MyToolParams): Promise<MyToolResult> => {
    ctx.logger.info(`Executing my_tool with input: ${params.input}`)
    
    // 参数验证
    if (!params.input || params.input.trim().length === 0) {
      return {
        success: false,
        error: 'Input cannot be empty',
        duration: 0
      }
    }
    
    // 调用服务处理
    const result = await ctx.myService.process(params.input, {
      model: 'deepseek-chat'
    })
    
    // 格式化输出
    if (params.options?.format === 'json') {
      return {
        ...result,
        data: JSON.stringify(result.data, null, 2)
      }
    }
    
    return result
  }
}

// 注册工具
export function registerTools(ctx: Context) {
  const tool = createMyTool(ctx)
  
  return ctx.tools.register({
    ...myToolDefinition,
    execute: tool
  })
}
```

### 3.5 步骤五：创建插件入口

创建 `src/index.ts`：

```typescript
import { Context } from 'cordis'
import { MyService } from './service.js'
import { registerTools } from './tools/index.js'
import type { MyPluginConfig } from './types/index.js'

// 插件元数据
export const name = 'my-plugin'
export const inject = ['llm', 'tools']

// 插件配置 Schema（可选）
export const Config = {
  type: 'object',
  properties: {
    enabled: { type: 'boolean', default: true },
    apiKey: { type: 'string' },
    baseUrl: { type: 'string' },
    timeout: { type: 'number', default: 30000 },
    maxRetries: { type: 'number', default: 3 }
  }
}

// 插件应用函数
export function apply(ctx: Context, config: MyPluginConfig) {
  // 检查是否启用
  if (!config.enabled) {
    ctx.logger.info('MyPlugin is disabled')
    return
  }
  
  ctx.logger.info('MyPlugin applying...')
  
  // 注册服务
  ctx.plugin(MyService, config)
  
  // 注册工具
  const disposeTool = registerTools(ctx)
  
  // 注册事件监听
  const disposeListener = ctx.on('my-plugin/error', (error) => {
    ctx.logger.error(`MyPlugin error: ${error.message}`)
  })
  
  // 返回清理函数（插件卸载时调用）
  return () => {
    ctx.logger.info('MyPlugin disposing...')
    disposeTool()
    disposeListener()
  }
}

// 导出类型
export type { MyPluginConfig, MyToolParams, MyToolResult } from './types/index.js'
export { MyService } from './service.js'
```

---

## 四、插件注册和使用

### 4.1 方式一：配置文件注册

创建 `cordis.yml`：

```yaml
plugins:
  # 注册插件
  - name: '@deepseek-ai/dsh-my-plugin'
    config:
      enabled: true
      apiKey: '${MY_API_KEY}'
      timeout: 60000
      maxRetries: 5

  # 其他插件...
  - name: '@deepseek-ai/dsh-llm-deepseek'
    config:
      apiKey: '${DEEPSEEK_API_KEY}'
```

### 4.2 方式二：代码注册

```typescript
import { createApp } from '@deepseek-ai/dsh'
import { apply as myPlugin } from './my-plugin/index.js'

async function main() {
  const app = await createApp({
    plugins: [
      // 内置插件
      {
        name: '@deepseek-ai/dsh-llm-deepseek',
        config: {
          apiKey: process.env.DEEPSEEK_API_KEY
        }
      },
      
      // 自定义插件
      {
        name: 'my-plugin',
        apply: myPlugin,
        config: {
          enabled: true,
          timeout: 30000
        }
      }
    ]
  })
  
  // 使用插件服务
  const result = await app.ctx.myService.process('Hello, World!')
  console.log(result)
  
  await app.stop()
}

main().catch(console.error)
```

### 4.3 方式三：动态注册

```typescript
import { Context } from 'cordis'
import { apply as myPlugin } from './my-plugin/index.js'

export function apply(ctx: Context) {
  // 动态注册插件
  ctx.plugin(myPlugin, {
    enabled: true,
    apiKey: ctx.config.get('myPlugin.apiKey')
  })
  
  // 监听插件加载
  ctx.on('internal/before-service', (name) => {
    if (name === 'myService') {
      ctx.logger.info('MyService is about to be registered')
    }
  })
}
```

---

## 五、完整示例：天气查询插件

### 5.1 插件结构

```
weather-plugin/
├── src/
│   ├── index.ts
│   ├── service.ts
│   ├── tools/
│   │   ├── get-weather.ts
│   │   └── forecast.ts
│   ├── types/
│   │   └── index.ts
│   └── utils/
│       └── api-client.ts
├── tests/
├── package.json
└── tsconfig.json
```

### 5.2 类型定义

`src/types/index.ts`：

```typescript
export interface WeatherConfig {
  apiKey: string
  baseUrl?: string
  units?: 'metric' | 'imperial'
  lang?: string
}

export interface WeatherData {
  location: string
  temperature: number
  humidity: number
  description: string
  windSpeed: number
  timestamp: number
}

export interface ForecastData {
  location: string
  forecasts: Array<{
    date: string
    tempHigh: number
    tempLow: number
    description: string
    precipitation: number
  }>
}

export interface GetWeatherParams {
  city: string
  units?: 'metric' | 'imperial'
}

export interface GetForecastParams {
  city: string
  days?: number
}

declare module 'cordis' {
  interface Context {
    weather: WeatherService
  }
}
```

### 5.3 服务实现

`src/service.ts`：

```typescript
import { Service, Context } from 'cordis'
import type { WeatherConfig, WeatherData, ForecastData } from './types/index.js'

export class WeatherService extends Service {
  private config: WeatherConfig
  private cache = new Map<string, { data: any; expiresAt: number }>()
  private cacheTTL = 10 * 60 * 1000 // 10分钟

  constructor(ctx: Context, config: WeatherConfig) {
    super(ctx, 'weather')
    this.config = {
      baseUrl: 'https://api.weatherapi.com/v1',
      units: 'metric',
      lang: 'zh',
      ...config
    }
  }

  async getWeather(city: string): Promise<WeatherData> {
    const cacheKey = `weather:${city}`
    const cached = this.getFromCache(cacheKey)
    if (cached) return cached

    const url = `${this.config.baseUrl}/current.json?key=${this.config.apiKey}&q=${encodeURIComponent(city)}&lang=${this.config.lang}`
    
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Weather API error: ${response.status}`)
    }
    
    const data = await response.json()
    
    const result: WeatherData = {
      location: data.location.name,
      temperature: data.current.temp_c,
      humidity: data.current.humidity,
      description: data.current.condition.text,
      windSpeed: data.current.wind_kph,
      timestamp: Date.now()
    }
    
    this.setCache(cacheKey, result)
    return result
  }

  async getForecast(city: string, days = 3): Promise<ForecastData> {
    const cacheKey = `forecast:${city}:${days}`
    const cached = this.getFromCache(cacheKey)
    if (cached) return cached

    const url = `${this.config.baseUrl}/forecast.json?key=${this.config.apiKey}&q=${encodeURIComponent(city)}&days=${days}&lang=${this.config.lang}`
    
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Weather API error: ${response.status}`)
    }
    
    const data = await response.json()
    
    const result: ForecastData = {
      location: data.location.name,
      forecasts: data.forecast.forecastday.map((day: any) => ({
        date: day.date,
        tempHigh: day.day.maxtemp_c,
        tempLow: day.day.mintemp_c,
        description: day.day.condition.text,
        precipitation: day.day.totalprecip_mm
      }))
    }
    
    this.setCache(cacheKey, result)
    return result
  }

  private getFromCache(key: string): any | null {
    const entry = this.cache.get(key)
    if (entry && entry.expiresAt > Date.now()) {
      return entry.data
    }
    if (entry) {
      this.cache.delete(key)
    }
    return null
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      expiresAt: Date.now() + this.cacheTTL
    })
  }
}
```

### 5.4 工具定义

`src/tools/get-weather.ts`：

```typescript
import type { Context } from 'cordis'
import type { GetWeatherParams } from '../types/index.js'

export const getWeatherTool = {
  name: 'get_weather',
  description: '获取指定城市的当前天气信息',
  parameters: {
    type: 'object' as const,
    properties: {
      city: {
        type: 'string',
        description: '城市名称，如"北京"、"上海"'
      },
      units: {
        type: 'string',
        enum: ['metric', 'imperial'],
        description: '温度单位，metric为摄氏度，imperial为华氏度'
      }
    },
    required: ['city']
  },
  execute: async (ctx: Context, params: GetWeatherParams) => {
    try {
      const weather = await ctx.weather.getWeather(params.city)
      
      return {
        success: true,
        data: {
          location: weather.location,
          temperature: `${weather.temperature}°C`,
          humidity: `${weather.humidity}%`,
          description: weather.description,
          windSpeed: `${weather.windSpeed} km/h`
        }
      }
    } catch (error) {
      return {
        success: false,
        error: (error as Error).message
      }
    }
  }
}
```

`src/tools/forecast.ts`：

```typescript
import type { Context } from 'cordis'
import type { GetForecastParams } from '../types/index.js'

export const getForecastTool = {
  name: 'get_forecast',
  description: '获取指定城市的未来天气预报',
  parameters: {
    type: 'object' as const,
    properties: {
      city: {
        type: 'string',
        description: '城市名称'
      },
      days: {
        type: 'number',
        description: '预报天数（1-7）',
        default: 3
      }
    },
    required: ['city']
  },
  execute: async (ctx: Context, params: GetForecastParams) => {
    try {
      const forecast = await ctx.weather.getForecast(params.city, params.days || 3)
      
      return {
        success: true,
        data: {
          location: forecast.location,
          forecasts: forecast.forecasts.map(f => ({
            date: f.date,
            high: `${f.tempHigh}°C`,
            low: `${f.tempLow}°C`,
            description: f.description,
            precipitation: `${f.precipitation}mm`
          }))
        }
      }
    } catch (error) {
      return {
        success: false,
        error: (error as Error).message
      }
    }
  }
}
```

### 5.5 插件入口

`src/index.ts`：

```typescript
import { Context } from 'cordis'
import { WeatherService } from './service.js'
import { getWeatherTool } from './tools/get-weather.js'
import { getForecastTool } from './tools/forecast.js'
import type { WeatherConfig } from './types/index.js'

export const name = 'weather-plugin'
export const inject = ['tools']

export const Config = {
  type: 'object',
  properties: {
    apiKey: { type: 'string', required: true },
    baseUrl: { type: 'string' },
    units: { type: 'string', enum: ['metric', 'imperial'], default: 'metric' },
    lang: { type: 'string', default: 'zh' }
  },
  required: ['apiKey']
}

export function apply(ctx: Context, config: WeatherConfig) {
  // 注册服务
  ctx.plugin(WeatherService, config)
  
  // 注册工具
  const dispose1 = ctx.tools.register({
    ...getWeatherTool,
    execute: (params) => getWeatherTool.execute(ctx, params)
  })
  
  const dispose2 = ctx.tools.register({
    ...getForecastTool,
    execute: (params) => getForecastTool.execute(ctx, params)
  })
  
  // 返回清理函数
  return () => {
    dispose1()
    dispose2()
  }
}
```

### 5.6 使用示例

```typescript
import { createApp } from '@deepseek-ai/dsh'

async function main() {
  const app = await createApp({
    plugins: [
      {
        name: '@deepseek-ai/dsh-llm-deepseek',
        config: { apiKey: process.env.DEEPSEEK_API_KEY }
      },
      {
        name: 'weather-plugin',
        apply: (await import('./weather-plugin/index.js')).apply,
        config: { apiKey: process.env.WEATHER_API_KEY }
      }
    ]
  })

  // 创建会话
  const session = await app.ctx.sessions.create({ userId: 'test' })

  // 发送消息（模型会自动调用天气工具）
  const response = await app.ctx.agent.sendMessage(session.id, {
    content: '北京今天天气怎么样？'
  })

  console.log(response.content)
  // 输出：北京今天天气晴朗，温度25°C，湿度45%，微风...

  await app.stop()
}

main().catch(console.error)
```

---

## 六、测试指南

### 6.1 单元测试

`tests/unit/service.test.ts`：

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { Context } from 'cordis'
import { WeatherService } from '../../src/service.js'

describe('WeatherService', () => {
  let ctx: Context
  let service: WeatherService

  beforeEach(() => {
    ctx = new Context()
    service = new WeatherService(ctx, {
      apiKey: 'test-key',
      units: 'metric',
      lang: 'zh'
    })
  })

  it('should get weather data', async () => {
    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        location: { name: 'Beijing' },
        current: {
          temp_c: 25,
          humidity: 45,
          condition: { text: 'Sunny' },
          wind_kph: 10
        }
      })
    })

    const weather = await service.getWeather('Beijing')

    expect(weather.location).toBe('Beijing')
    expect(weather.temperature).toBe(25)
    expect(weather.humidity).toBe(45)
    expect(weather.description).toBe('Sunny')
  })

  it('should use cache', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        location: { name: 'Beijing' },
        current: { temp_c: 25, humidity: 45, condition: { text: 'Sunny' }, wind_kph: 10 }
      })
    })

    // 第一次调用
    await service.getWeather('Beijing')
    // 第二次调用（应该使用缓存）
    await service.getWeather('Beijing')

    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('should handle API errors', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401
    })

    await expect(service.getWeather('Beijing')).rejects.toThrow('Weather API error: 401')
  })
})
```

### 6.2 集成测试

`tests/integration/plugin.test.ts`：

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { createApp } from '@deepseek-ai/dsh'
import { apply as weatherPlugin } from '../../src/index.js'

describe('Weather Plugin Integration', () => {
  let app: any

  beforeAll(async () => {
    app = await createApp({
      plugins: [
        {
          name: '@deepseek-ai/dsh-llm-deepseek',
          config: { apiKey: process.env.DEEPSEEK_API_KEY }
        },
        {
          name: 'weather-plugin',
          apply: weatherPlugin,
          config: { apiKey: process.env.WEATHER_API_KEY }
        }
      ]
    })
  })

  afterAll(async () => {
    await app.stop()
  })

  it('should complete weather query flow', async () => {
    const session = await app.ctx.sessions.create({ userId: 'test' })

    const response = await app.ctx.agent.sendMessage(session.id, {
      content: '上海今天天气怎么样？'
    })

    expect(response.content).toBeDefined()
    expect(response.content.length).toBeGreaterThan(0)
  }, 30000)
})
```

---

## 七、最佳实践

### 7.1 错误处理

```typescript
// 使用自定义错误类
export class WeatherAPIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public response?: any
  ) {
    super(message)
    this.name = 'WeatherAPIError'
  }
}

// 在服务中使用
async getWeather(city: string): Promise<WeatherData> {
  try {
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new WeatherAPIError(
        `Weather API error: ${response.status}`,
        response.status
      )
    }
    
    // ...
  } catch (error) {
    if (error instanceof WeatherAPIError) {
      throw error
    }
    throw new WeatherAPIError(
      `Failed to fetch weather: ${(error as Error).message}`,
      500
    )
  }
}
```

### 7.2 日志记录

```typescript
export class MyService extends Service {
  async process(input: string) {
    this.ctx.logger.info(`Processing request: ${input}`)
    
    try {
      const result = await this.doProcess(input)
      this.ctx.logger.info(`Request completed successfully`)
      return result
    } catch (error) {
      this.ctx.logger.error(`Request failed: ${(error as Error).message}`)
      throw error
    }
  }
}
```

### 7.3 资源清理

```typescript
export function apply(ctx: Context, config: Config) {
  const resources: Array<() => void> = []
  
  // 注册资源
  const timer = setInterval(() => {
    // 定期任务
  }, 60000)
  resources.push(() => clearInterval(timer))
  
  // 注册事件监听
  const dispose = ctx.on('some-event', handler)
  resources.push(dispose)
  
  // 返回清理函数
  return () => {
    resources.forEach(cleanup => cleanup())
  }
}
```

### 7.4 配置验证

```typescript
export const Config = {
  type: 'object',
  properties: {
    apiKey: { type: 'string', minLength: 1 },
    timeout: { type: 'number', minimum: 1000, maximum: 60000 },
    retries: { type: 'integer', minimum: 0, maximum: 5 }
  },
  required: ['apiKey'],
  additionalProperties: false
}

export function apply(ctx: Context, config: Config) {
  // 配置已经过验证
  // ...
}
```

---

## 八、常见问题

### 8.1 插件加载失败

**问题**：插件无法加载，提示依赖未找到

**解决**：
1. 检查 `inject` 声明是否正确
2. 确保依赖的插件已注册
3. 检查依赖服务是否处于 ACTIVE 状态

### 8.2 工具未被调用

**问题**：注册了工具但模型不调用

**解决**：
1. 检查工具名称和描述是否清晰
2. 确保参数 Schema 定义正确
3. 在系统提示词中引导模型使用工具

### 8.3 内存泄漏

**问题**：插件卸载后内存未释放

**解决**：
1. 确保返回清理函数
2. 清理所有事件监听器
3. 清理定时器和异步任务

### 8.4 类型错误

**问题**：TypeScript 编译报错

**解决**：
1. 确保声明合并正确
2. 检查 `peerDependencies` 版本
3. 使用 `declare module` 扩展类型

---

## 九、参考资源

- [Cordis 框架文档](https://github.com/cordiverse/cordis)
- [DSH 架构设计文档](./deepseek-harness-architecture.md)
- [DSH 实施路线图](./实施路线图.md)
- [安全沙箱配置指南](./安全配置指南.md)