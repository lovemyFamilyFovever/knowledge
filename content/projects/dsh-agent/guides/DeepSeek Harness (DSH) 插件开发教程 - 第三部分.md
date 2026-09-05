---
title: "DeepSeek Harness (DSH) 插件开发教程 - 第三部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 插件开发教程"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness (DSH) 插件开发教程 - 第三部分

## 插件发布和分发

### 1. npm 发布流程

DSH 使用 pnpm monorepo 结构，插件发布需要遵循特定的流程：

#### 1.1 准备发布

```bash
# 1. 确保所有测试通过
pnpm run test

# 2. 运行类型检查
pnpm run typecheck

# 3. 运行 lint 检查
pnpm run lint

# 4. 构建项目
pnpm run build

# 5. 运行卫生检查
pnpm run hygiene
```

#### 1.2 package.json 配置

确保你的 `package.json` 包含正确的发布配置：

```json
{
  "name": "@deepseek-ai/dsh-my-plugin",
  "version": "1.0.0",
  "private": false,
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
  "scripts": {
    "build": "tsdown",
    "test": "vitest run",
    "lint": "oxlint .",
    "typecheck": "tsc --noEmit"
  },
  "keywords": ["dsh", "plugin", "deepseek-harness"],
  "repository": {
    "type": "git",
    "url": "https://github.com/deepseek-ai/deepseek-harness.git",
    "directory": "packages/my-group/my-plugin"
  },
  "license": "MIT"
}
```

#### 1.3 发布命令

```bash
# 使用 pnpm 发布
pnpm publish --access public

# 或者使用 npm
npm publish --access public
```

### 2. 插件注册和发现

#### 2.1 在 DSH 中注册插件

插件可以通过以下方式注册到 DSH：

**方式一：在 cordis.yml 中配置**

```yaml
# cordis.yml
- id: my-plugin
  config:
    apiKey: '!!js process.env.MY_API_KEY'
    someOption: true
```

**方式二：通过命令行参数**

```bash
dsh --plugin my-plugin --config '{"apiKey": "xxx"}'
```

**方式三：在代码中动态加载**

```typescript
import { Context } from '@deepseek-ai/cordis'
import { apply as myPlugin } from '@deepseek-ai/dsh-my-plugin'

const ctx = new Context()
ctx.plugin(myPlugin, { apiKey: 'xxx' })
```

#### 2.2 插件发现机制

DSH 通过以下机制发现和加载插件：

1. **包发现**：通过 `package.json` 中的 `dsh` 字段声明插件类型
2. **配置发现**：通过 `cordis.yml` 文件中的 `id` 字段匹配
3. **依赖注入**：通过 `inject` 字段声明依赖关系

```json
// package.json 中的 dsh 字段
{
  "dsh": {
    "type": "plugin",
    "category": "tool"
  }
}
```

---

## 高级模式

### 1. 插件组合和继承

#### 1.1 插件组合

插件可以通过组合多个小插件来创建更复杂的功能：

```typescript
// packages/bundles/my-bundle/src/index.ts
import type { Context } from '@deepseek-ai/cordis'
import { apply as applyTool1 } from '@deepseek-ai/dsh-tool-1'
import { apply as applyTool2 } from '@deepseek-ai/dsh-tool-2'
import { apply as applyProvider } from '@deepseek-ai/dsh-provider'

export const name = 'my-bundle'

export function apply(ctx: Context) {
  // 组合多个插件
  ctx.plugin(applyTool1)
  ctx.plugin(applyTool2)
  ctx.plugin(applyProvider, { apiKey: 'xxx' })
}
```

#### 1.2 插件继承

通过类继承实现插件的功能扩展：

```typescript
// 基础工具类
abstract class BaseTool {
  abstract name: string
  abstract execute(args: any): Promise<any>
  
  protected validateArgs(args: any): void {
    // 通用验证逻辑
  }
}

// 具体工具实现
class SearchTool extends BaseTool {
  name = 'search'
  
  async execute(args: { query: string }) {
    this.validateArgs(args)
    return await this.performSearch(args.query)
  }
  
  private async performSearch(query: string) {
    // 搜索实现
  }
}
```

### 2. 条件加载

根据环境或配置条件加载插件：

```typescript
// 条件加载插件
export function apply(ctx: Context, config: Config) {
  // 根据配置决定是否加载调试工具
  if (config.debug) {
    ctx.plugin(applyDebugTools)
  }
  
  // 根据环境决定加载哪个存储后端
  if (process.env.NODE_ENV === 'production') {
    ctx.plugin(applyRedisStorage, config.redis)
  } else {
    ctx.plugin(applyLocalStorage)
  }
}
```

#### 2.1 使用 disabled 字段

在 `cordis.yml` 中使用 `disabled` 字段：

```yaml
# cordis.yml
- id: debug-tools
  disabled: '!!js process.env.NODE_ENV === "production"'
  config: {}

- id: redis-storage
  disabled: '!!js !process.env.REDIS_HOST'
  config:
    host: '!!js process.env.REDIS_HOST'
```

### 3. 热重载

DSH 的所有注册都是基于效果的（effect-based），这意味着热重载（HMR）可以无缝工作：

```typescript
export function apply(ctx: Context) {
  // 注册一个效果
  ctx.effect(() => {
    const tool = ctx.tools.register(myTool)
    const listener = ctx.on('my-event', handler)
    
    // 返回清理函数
    return () => {
      tool.dispose()
      listener.dispose()
    }
  })
}
```

当插件重新加载时：
1. 旧的清理函数会被调用，移除所有旧的注册
2. 新的 `apply` 函数执行，注册新的功能
3. 所有依赖此插件的服务会自动更新

---

## 现有插件源码分析

### 1. 分析 packages/fs

`packages/fs` 是文件系统访问插件，它展示了典型的能力接缝（capability seam）模式：

#### 1.1 结构分析

```
packages/fs/
  fs/                  # 服务定义
    src/
      index.ts         # FileSystemService 接口和注册
      types.ts         # 类型定义
  fs-local/            # 本地文件系统实现
    src/
      index.ts         # 本地后端实现
  fs-search/           # 文件搜索工具
    src/
      index.ts         # grep/glob 工具
```

#### 1.2 核心代码

```typescript
// fs/src/index.ts - 服务定义
import { Context, Service } from '@deepseek-ai/cordis'

export class FileSystemService extends Service {
  constructor(ctx: Context) {
    super(ctx, 'fs')
  }
  
  // 注册文件系统后端
  registerBackend(backend: FsBackend): Disposable {
    // 注册逻辑
  }
  
  // 读取文件
  async readFile(path: string): Promise<string> {
    const backend = this.getBackend(path)
    return backend.readFile(path)
  }
  
  // 写入文件
  async writeFile(path: string, content: string): Promise<void> {
    const backend = this.getBackend(path)
    return backend.writeFile(path, content)
  }
}
```

```typescript
// fs-local/src/index.ts - 本地后端实现
import { FsBackend } from '@deepseek-ai/dsh-fs'
import { readFile, writeFile } from 'node:fs/promises'

export class LocalFsBackend implements FsBackend {
  name = 'local'
  
  async readFile(path: string): Promise<string> {
    return readFile(path, { encoding: 'utf8' })
  }
  
  async writeFile(path: string, content: string): Promise<void> {
    await writeFile(path, content, { encoding: 'utf8' })
  }
}

export function apply(ctx: Context) {
  const backend = new LocalFsBackend()
  ctx.fs.registerBackend(backend)
}
```

### 2. 分析 packages/llm

`packages/llm` 展示了 LLM 适配器的完整实现模式：

#### 2.1 结构分析

```
packages/llm/
  llm/                 # 核心抽象层
    src/
      index.ts         # LlmRuntime 服务
      types.ts         # 类型定义
      message.ts       # 消息类型
      adapter.ts       # 适配器基类
  llm-deepseek/        # DeepSeek 实现
    src/
      index.ts         # 插件入口
      adapter.ts       # 适配器实现
      translate.ts     # 消息转换
      sse.ts           # SSE 解析
  llm-pi-ai/           # Pi AI 实现
    src/
      index.ts
      adapter.ts
```

#### 2.2 核心代码

```typescript
// llm/src/index.ts - LLM 运行时服务
export class LlmRuntime extends Service {
  private adapters = new Map<string, LlmAdapter>()
  
  constructor(ctx: Context) {
    super(ctx, 'llm')
  }
  
  // 注册适配器
  registerAdapter(providers: string[], adapter: LlmAdapter): Disposable {
    for (const provider of providers) {
      if (this.adapters.has(provider)) {
        throw new Error(`Adapter already registered for provider: ${provider}`)
      }
      this.adapters.set(provider, adapter)
    }
    
    return () => {
      for (const provider of providers) {
        this.adapters.delete(provider)
      }
    }
  }
  
  // 生成响应
  async * stream(options: GenerateOptions): AsyncIterable<StreamChunk> {
    const adapter = this.adapters.get(options.provider)
    if (!adapter) {
      throw new Error(`No adapter registered for provider: ${options.provider}`)
    }
    
    yield * adapter.stream(options)
  }
}
```

### 3. 分析 packages/skill

`packages/skill` 展示了技能系统的插件模式：

#### 3.1 结构分析

```
packages/skill/
  skill/               # 技能注册服务
    src/
      index.ts         # SkillRegistry 服务
      types.ts         # 技能类型定义
  skill-*/             # 具体技能实现
    src/
      index.ts
```

#### 3.2 核心代码

```typescript
// skill/src/index.ts - 技能注册服务
export class SkillRegistry extends Service {
  private skills = new Map<string, Skill>()
  
  constructor(ctx: Context) {
    super(ctx, 'skills')
  }
  
  // 注册技能
  register(skill: Skill): Disposable {
    if (this.skills.has(skill.name)) {
      throw new Error(`Skill already registered: ${skill.name}`)
    }
    
    this.skills.set(skill.name, skill)
    
    // 注册技能提供的工具
    const toolDisposables = skill.tools?.map(tool => 
      this.ctx.tools.register(tool)
    ) ?? []
    
    // 注册技能提供的提示词部分
    const sectionDisposables = skill.sections?.map(section =>
      this.ctx.systemPrompt.section(section)
    ) ?? []
    
    return () => {
      this.skills.delete(skill.name)
      toolDisposables.forEach(d => d.dispose())
      sectionDisposables.forEach(d => d.dispose())
    }
  }
  
  // 获取技能
  get(name: string): Skill | undefined {
    return this.skills.get(name)
  }
}
```

---

## 常见错误和解决方案

### 1. 循环依赖

**问题**：两个插件互相依赖对方的服务。

**解决方案**：
- 使用事件系统进行松耦合通信
- 引入第三个插件作为中介
- 使用延迟初始化模式

```typescript
// 错误示例：循环依赖
// pluginA 依赖 pluginB，pluginB 依赖 pluginA

// 正确示例：使用事件通信
export function apply(ctx: Context) {
  ctx.on('plugin-b-event', (data) => {
    // 处理来自 pluginB 的事件
  })
  
  // 发送事件给 pluginA
  ctx.emit('plugin-a-event', { data: 'xxx' })
}
```

### 2. 服务未注册

**问题**：尝试访问未注册的服务。

**解决方案**：
- 使用 `inject` 声明依赖
- 使用 `ctx.get()` 检查服务是否存在
- 使用可选依赖模式

```typescript
// 使用可选依赖
export function apply(ctx: Context) {
  const llm = ctx.get('llm')
  if (!llm) {
    console.warn('LLM service not available, some features disabled')
    return
  }
  
  // 使用 llm 服务
}
```

### 3. 内存泄漏

**问题**：插件卸载后，注册的监听器或定时器仍然存在。

**解决方案**：
- 始终使用 `ctx.effect()` 注册可清理的资源
- 使用 `ctx.on()` 而不是原生 `addEventListener`
- 确保异步操作支持取消

```typescript
export function apply(ctx: Context) {
  // 正确：使用 ctx.effect 管理资源
  ctx.effect(() => {
    const interval = setInterval(() => {
      // 定期任务
    }, 1000)
    
    return () => {
      clearInterval(interval)  // 清理定时器
    }
  })
  
  // 正确：使用 ctx.on 管理事件监听
  ctx.on('my-event', handler)  // 插件卸载时自动移除
}
```

### 4. 类型错误

**问题**：TypeScript 类型不匹配。

**解决方案**：
- 使用 `declare module` 扩展类型
- 正确使用泛型参数
- 导出正确的类型定义

```typescript
// 扩展 Context 类型
declare module '@deepseek-ai/cordis' {
  interface Context {
    myService: MyService
  }
}

// 扩展 Events 类型
declare module '@deepseek-ai/cordis' {
  interface Events {
    'my-event'(data: MyData): void
  }
}
```

---

## 最佳实践总结

### 1. 设计原则

1. **单一职责**：每个插件只负责一个功能领域
2. **松耦合**：通过事件和服务接口进行通信，避免直接依赖
3. **可替换性**：设计接口时考虑多种实现可能
4. **配置驱动**：通过配置控制行为，而不是硬编码

### 2. 代码规范

1. **类型安全**：充分利用 TypeScript 的类型系统
2. **错误处理**：使用 `LlmError`、`StorageError` 等领域错误类型
3. **资源管理**：始终清理注册的资源，使用 `ctx.effect()`
4. **测试覆盖**：编写单元测试和集成测试

### 3. 性能优化

1. **懒加载**：延迟初始化昂贵的资源
2. **缓存**：适当缓存计算结果
3. **流式处理**：使用 `AsyncIterable` 处理大数据
4. **取消支持**：所有异步操作支持 `AbortSignal`

### 4. 文档和维护

1. **README**：每个包都需要详细的 README
2. **类型文档**：使用 JSDoc 注释关键接口
3. **变更日志**：记录重要的变更
4. **版本管理**：遵循语义化版本规范

### 5. 插件清单

创建一个新插件时，请确保：

- [ ] 正确的 `package.json` 配置
- [ ] 正确的 `tsconfig.json` 配置
- [ ] 导出 `name`、`inject`、`apply` 函数
- [ ] 使用 `ctx.effect()` 管理资源
- [ ] 处理所有错误情况
- [ ] 编写测试用例
- [ ] 编写 README 文档
- [ ] 遵循 DSH 的命名规范

---

## 附录：完整示例项目

### 天气查询插件完整示例

```typescript
// packages/tools/weather-tool/src/index.ts
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import z from '@deepseek-ai/schemastery'

// 配置模式
export const Config = z.object({
  apiKey: z.string().role('secret'),
  baseUrl: z.string().default('https://api.weather.com'),
  timeout: z.number().default(5000),
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
  wind: {
    speed: number
    direction: string
  }
}

export function apply(ctx: Context, config: Config) {
  const registration = ctx.tools.register(defineTool<WeatherArgs, WeatherResult>({
    name: 'get_weather',
    description: '获取指定城市的当前天气信息，包括温度、湿度和风力',
    parameters: {
      city: { 
        type: 'string', 
        required: true, 
        description: '城市名称，如"北京"、"上海"、"New York"' 
      },
      unit: { 
        type: 'string', 
        description: '温度单位：celsius（摄氏度）或 fahrenheit（华氏度），默认为摄氏度' 
      },
    },
    output: {
      schema: { type: 'object' },
      render: (_args, value) => [{
        type: 'text',
        text: formatWeatherOutput(value),
      }],
    },
    async execute(args, exec) {
      const unit = args.unit ?? 'celsius'
      const url = `${config.baseUrl}/weather?city=${encodeURIComponent(args.city)}&unit=${unit}`
      
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), config.timeout)
      
      try {
        const response = await fetch(url, {
          headers: { 
            'Authorization': `Bearer ${config.apiKey}`,
            'Accept': 'application/json',
          },
          signal: controller.signal,
        })
        
        if (!response.ok) {
          const error = await response.text()
          throw new Error(`Weather API error (${response.status}): ${error}`)
        }
        
        const data = await response.json()
        
        return {
          city: args.city,
          temperature: data.temperature,
          unit: unit === 'celsius' ? '°C' : '°F',
          condition: data.condition,
          humidity: data.humidity,
          wind: {
            speed: data.wind_speed,
            direction: data.wind_direction,
          },
        }
      } finally {
        clearTimeout(timeoutId)
      }
    },
  }))
  
  // 返回清理函数（可选，Cordis 会自动处理）
  return () => {
    registration.dispose()
  }
}

function formatWeatherOutput(weather: WeatherResult): string {
  return [
    `🌤 ${weather.city}当前天气`,
    `温度: ${weather.temperature}${weather.unit}`,
    `天气: ${weather.condition}`,
    `湿度: ${weather.humidity}%`,
    `风力: ${weather.wind.speed}km/h ${weather.wind.direction}`,
  ].join('\n')
}
```

### 测试文件

```typescript
// packages/tools/weather-tool/tests/weather-tool.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
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
  
  afterEach(async () => {
    await ctx.stop()
  })
  
  it('should register the tool', () => {
    const tools = ctx.get('tools')
    const tool = tools.get('get_weather')
    
    expect(tool).toBeDefined()
    expect(tool.name).toBe('get_weather')
    expect(tool.description).toContain('天气')
  })
  
  it('should validate required parameters', () => {
    const tools = ctx.get('tools')
    const tool = tools.get('get_weather')
    
    expect(() => tool.validateArgs({})).toThrow('city')
  })
  
  it('should accept valid parameters', () => {
    const tools = ctx.get('tools')
    const tool = tools.get('get_weather')
    
    expect(() => tool.validateArgs({ city: '北京' })).not.toThrow()
    expect(() => tool.validateArgs({ city: '北京', unit: 'celsius' })).not.toThrow()
  })
  
  it('should execute successfully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        temperature: 25,
        condition: '晴',
        humidity: 40,
        wind_speed: 10,
        wind_direction: '东北',
      }),
    })
    
    const tools = ctx.get('tools')
    const result = await tools.execute('get_weather', { city: '北京' })
    
    expect(result.city).toBe('北京')
    expect(result.temperature).toBe(25)
    expect(result.condition).toBe('晴')
  })
  
  it('should handle API errors', async () => {
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
  
  it('should handle timeout', async () => {
    global.fetch = vi.fn().mockImplementation(() => 
      new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Abort')), 100)
      })
    )
    
    const tools = ctx.get('tools')
    
    await expect(
      tools.execute('get_weather', { city: '北京' })
    ).rejects.toThrow()
  })
})
```

---

## 总结

本教程详细介绍了 DeepSeek Harness 插件开发的各个方面：

1. **架构理解**：掌握了"一切皆插件"的设计哲学和 Cordis 依赖注入框架
2. **Tool 插件**：学会了创建自定义工具插件，包括参数定义、执行逻辑和结果渲染
3. **Provider 插件**：理解了 LLM 适配器和存储后端的实现模式
4. **通信机制**：掌握了事件系统、服务注入和共享状态的使用方法
5. **测试策略**：学会了单元测试、集成测试和 Mock 策略
6. **最佳实践**：了解了插件设计、代码规范和性能优化的最佳实践

通过遵循这些指南，你可以创建高质量、可维护、可扩展的 DSH 插件。
