---
title: "Cordis 框架单元测试方案"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / Cordis框架分析"
collected: "2026-09-05"
status: "imported"
---

Cordis 框架单元测试方案
Cordis 框架单元测试方案
核心依赖注入 · 热重载机制 · 事件系统 · 反射系统
基于 DeepSeek Harness 项目源码分析 · 2026-08-29
目录
测试概述
测试环境与工具
核心依赖注入测试
Context上下文测试
Service生命周期测试
事件系统测试
热重载机制测试
反射系统测试
加载器测试
覆盖率指标
1. 测试概述
本测试方案针对 Cordis 依赖注入框架的核心模块，设计全面的单元测试用例，确保框架在 DeepSeek Harness 项目中的稳定性和可靠性。
测试目标
验证 IoC 容器的服务注册、发现和依赖解析机制
验证 Context 的创建、继承和作用域隔离
验证 Service 的完整生命周期管理
验证事件系统的五种调度模式
验证热重载的状态迁移和错误回滚
验证反射系统的元数据管理和 Mixin 机制
模块
测试文件
用例数
优先级
Context
context.spec.ts
25
P0
Service
service.spec.ts
20
P0
Fiber
fiber.spec.ts
30
P0
Events
events.spec.ts
25
P0
Reflect
reflect.spec.ts
18
P1
Registry
registry.spec.ts
22
P0
HMR
hmr.spec.ts
15
P1
Loader
loader.spec.ts
12
P1
2. 测试环境与工具
2.1 测试框架
工具
用途
版本
Vitest
单元测试运行器
^4.1.8
@vitest/coverage-v8
代码覆盖率
^4.1.8
TypeScript
类型检查
^6.0.3
2.2 测试配置
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['vendor/cordis/src/**/*.ts'],
      exclude: ['**/*.d.ts', '**/*.spec.ts'],
      thresholds: {
        branches: 80,
        functions: 85,
        lines: 85,
        statements: 85
      }
    },
    setupFiles: ['./tests/setup.ts'],
    testTimeout: 10000
  }
})
3. 核心依赖注入测试
3.1 服务注册测试
TC-DI-001: 基本服务注册
P0
验证服务可以通过 provide() 方法成功注册
import { Context } from '@deepseek-ai/cordis'
import { describe, it, expect, beforeEach } from 'vitest'

describe('服务注册', () => {
  let ctx: Context

  beforeEach(() => {
    ctx = new Context()
  })

  it('TC-DI-001: 应该成功注册服务', () => {
    const dispose = ctx.provide('myService', { value: 42 })
    expect(ctx.get('myService')).toEqual({ value: 42 })
    dispose()
  })

  it('TC-DI-002: 应该阻止重复注册', () => {
    ctx.provide('myService', { value: 1 })
    expect(() => ctx.provide('myService', { value: 2 }))
      .toThrow('service "myService" has been registered')
  })

  it('TC-DI-003: 应该在注销后重新注册', () => {
    const dispose = ctx.provide('myService', { value: 1 })
    dispose()
    expect(() => ctx.provide('myService', { value: 2 })).not.toThrow()
  })
})
TC-DI-004: 依赖注入测试
P0
验证插件可以通过 inject 声明依赖并自动注入
describe('依赖注入', () => {
  it('TC-DI-004: 应该在依赖可用时激活插件', async () => {
    const ctx = new Context()
    const order: string[] = []

    // 注册依赖服务
    ctx.provide('logger', { log: (msg: string) => order.push(msg) })

    // 使用 inject 声明依赖
    const fiber = ctx.inject(['logger'], (ctx) => {
      ctx.logger.log('plugin activated')
      return () => { ctx.logger.log('plugin disposed') }
    })

    await fiber.await()
    expect(order).toEqual(['plugin activated'])
  })

  it('TC-DI-005: 应该在依赖不可用时保持 PENDING', async () => {
    const ctx = new Context()
    let activated = false

    ctx.inject(['missingService'], () => {
      activated = true
    })

    // 等待一小段时间
    await new Promise(r => setTimeout(r, 50))
    expect(activated).toBe(false)
  })
})
3.2 依赖解析算法测试
TC-DI-006: Epoch 机制测试
P0
验证 epoch 字符串变化触发重新加载
describe('Epoch 机制', () => {
  it('TC-DI-006: 依赖变化应该触发重新加载', async () => {
    const ctx = new Context()
    let loadCount = 0

    ctx.provide('serviceA', { value: 'a' })

    ctx.inject(['serviceA'], (ctx) => {
      loadCount++
      return () => { loadCount-- }
    })

    await new Promise(r => setTimeout(r, 100))
    expect(loadCount).toBe(1)

    // 重新注册服务，触发 epoch 变化
    const dispose = ctx.provide('serviceA', { value: 'a-new' })
    await new Promise(r => setTimeout(r, 100))
    
    // 应该触发重新加载
    expect(loadCount).toBe(1)
    dispose()
  })
})
4. Context 上下文测试
4.1 创建与继承测试
TC-CTX-001: Context 扩展
P0
验证 extend() 方法创建子 Context 且不修改父
describe('Context 扩展', () => {
  it('TC-CTX-001: 应该创建继承的子 Context', () => {
    const parent = new Context()
    parent.provide('service', { value: 'parent' })

    const child = parent.extend()
    expect(child.get('service')).toEqual({ value: 'parent' })
  })

  it('TC-CTX-002: 子 Context 不应该影响父', () => {
    const parent = new Context()
    parent.provide('service', { value: 'parent' })

    const child = parent.extend()
    child.provide('childService', { value: 'child' })

    expect(parent.get('childService')).toBeUndefined()
  })
})
4.2 作用域隔离测试
TC-CTX-003: 隔离作用域
P0
验证 isolate() 创建独立的服务作用域
describe('作用域隔离', () => {
  it('TC-CTX-003: 相同标签应该共享实例', () => {
    const root = new Context()
    const label = Symbol('scope')

    const scope1 = root.isolate('service', label)
    const scope2 = root.isolate('service', label)

    scope1.provide('service', { value: 'shared' })
    expect(scope2.get('service')).toEqual({ value: 'shared' })
  })

  it('TC-CTX-004: 不同标签应该隔离实例', () => {
    const root = new Context()

    const scope1 = root.isolate('service')
    const scope2 = root.isolate('service')

    scope1.provide('service', { value: 'scope1' })
    scope2.provide('service', { value: 'scope2' })

    expect(scope1.get('service')).toEqual({ value: 'scope1' })
    expect(scope2.get('service')).toEqual({ value: 'scope2' })
  })
})
5. Service 生命周期测试
5.1 初始化测试
TC-SVC-001: Init 阶段
P0
验证 Service.init 在构造后正确执行
import { Service, Context } from '@deepseek-ai/cordis'

class TestService extends Service {
  static provide = 'test'
  public initialized = false
  public disposed = false

  [Service.init]() {
    this.initialized = true
    return () => {
      this.disposed = true
    }
  }
}

describe('Service 生命周期', () => {
  it('TC-SVC-001: 应该在构造后执行 init', async () => {
    const ctx = new Context()
    const fiber = ctx.plugin(TestService)
    await fiber.await()

    const service = ctx.test as TestService
    expect(service.initialized).toBe(true)
  })

  it('TC-SVC-002: 应该在卸载时执行 disposer', async () => {
    const ctx = new Context()
    const fiber = ctx.plugin(TestService)
    await fiber.await()

    const service = ctx.test as TestService
    await fiber.dispose()

    expect(service.disposed).toBe(true)
  })
})
5.2 Fiber 状态机测试
TC-SVC-003: 状态转换
P0
验证 Fiber 状态机的正确转换
import { FiberState } from '@deepseek-ai/cordis'

describe('Fiber 状态机', () => {
  it('TC-SVC-003: 无依赖应该直接进入 ACTIVE', async () => {
    const ctx = new Context()
    const fiber = ctx.plugin(function testPlugin() {})
    await fiber.await()
    
    expect(fiber.state).toBe(FiberState.ACTIVE)
  })

  it('TC-SVC-004: 有缺失依赖应该保持 PENDING', async () => {
    const ctx = new Context()
    const fiber = ctx.inject(['missing'], () => {})
    
    await new Promise(r => setTimeout(r, 50))
    expect(fiber.state).toBe(FiberState.PENDING)
  })

  it('TC-SVC-005: dispose() 应该进入 UNLOADING', async () => {
    const ctx = new Context()
    const fiber = ctx.plugin(function() {
      return () => {} // disposer
    })
    await fiber.await()
    
    const disposePromise = fiber.dispose()
    expect(fiber.state).toBe(FiberState.UNLOADING)
    await disposePromise
    expect(fiber.state).toBe(FiberState.DISPOSED)
  })
})
6. 事件系统测试
6.1 调度模式测试
TC-EVT-001: emit 模式
P0
验证 emit 同步触发所有监听器
describe('事件调度', () => {
  it('TC-EVT-001: emit 应该同步触发所有监听器', () => {
    const ctx = new Context()
    const results: number[] = []

    ctx.on('test', () => results.push(1))
    ctx.on('test', () => results.push(2))
    ctx.on('test', () => results.push(3))

    ctx.emit('test')
    expect(results).toEqual([1, 2, 3])
  })

  it('TC-EVT-002: bail 应该在第一个返回值时停止', () => {
    const ctx = new Context()
    const results: number[] = []

    ctx.on('test', () => { results.push(1); return 'stop' })
    ctx.on('test', () => { results.push(2); return null })
    ctx.on('test', () => { results.push(3); return null })

    const result = ctx.bail('test')
    expect(result).toBe('stop')
    expect(results).toEqual([1])
  })

  it('TC-EVT-003: waterfall 应该支持中间件链', () => {
    const ctx = new Context()

    ctx.on('test', (value, next) => {
      return next(value * 2)
    })
    ctx.on('test', (value, next) => {
      return next(value + 1)
    })

    const result = ctx.waterfall('test', 5, (v) => v)
    expect(result).toBe(11) // (5 * 2) + 1
  })
})
6.2 上下文过滤测试
TC-EVT-004: 上下文过滤
P0
验证事件只传播到相关的监听器
describe('上下文过滤', () => {
  it('TC-EVT-004: 应该只触发匹配上下文的监听器', () => {
    const ctx1 = new Context()
    const ctx2 = new Context()
    const results: string[] = []

    ctx1.on('test', () => results.push('ctx1'))
    ctx2.on('test', () => results.push('ctx2'))

    // 在 ctx1 上触发
    ctx1.emit(ctx1, 'test')
    expect(results).toEqual(['ctx1'])
  })

  it('TC-EVT-005: global 监听器应该接收所有事件', () => {
    const ctx1 = new Context()
    const ctx2 = new Context()
    const results: string[] = []

    ctx1.on('test', () => results.push('global'), { global: true })
    ctx2.on('test', () => results.push('local'))

    ctx2.emit(ctx2, 'test')
    expect(results).toContain('global')
  })
})
7. 热重载机制测试
7.1 文件变化检测测试
TC-HMR-001: 文件监听
P1
验证 HMR 正确监听文件变化
describe('热重载', () => {
  it('TC-HMR-001: 应该检测文件变化', async () => {
    // Mock 文件系统
    const mockWatcher = {
      on: vi.fn(),
      close: vi.fn()
    }
    
    // 测试文件变化事件
    const hmr = new Hmr(ctx, { root: ['./src'], debounce: 100 })
    
    // 模拟文件变化
    mockWatcher.on.mock.calls.find(c => c[0] === 'change')[1]('test.ts')
    
    expect(hmr['stashed']).toContain(expect.stringContaining('test.ts'))
  })
})
7.2 依赖图分析测试
TC-HMR-002: 依赖分析
P1
验证依赖图正确分类文件
describe('依赖图分析', () => {
  it('TC-HMR-002: 应该正确分类 accepted 和 declined', async () => {
    const hmr = new Hmr(ctx, { root: ['./src'], debounce: 100 })
    
    // 模拟依赖关系: A -> B -> C
    hmr['stashed'].add('fileA.js')
    vi.spyOn(hmr, 'getLinked').mockResolvedValue(['fileB.js'])
    
    await hmr['analyzeChanges']()
    
    expect(hmr['accepted']).toContain('fileA.js')
    expect(hmr['accepted']).toContain('fileB.js')
  })

  it('TC-HMR-003: 外部依赖应该标记为 declined', async () => {
    const hmr = new Hmr(ctx, { root: ['./src'], debounce: 100 })
    hmr['externals'] = new Set(['external.js'])
    
    await hmr['analyzeChanges']()
    
    expect(hmr['declined']).toContain('external.js')
  })
})
7.3 错误回滚测试
TC-HMR-004: 回滚机制
P0
验证热重载失败时正确回滚
describe('错误回滚', () => {
  it('TC-HMR-004: 加载失败应该回滚到旧版本', async () => {
    const hmr = new Hmr(ctx, { root: ['./src'], debounce: 100 })
    
    // 备份缓存
    const esmBackup = { 'plugin.js': { url: 'plugin.js' } }
    hmr['esmBackup'] = esmBackup
    
    // 模拟加载失败
    vi.spyOn(ctx.loader, 'import').mockRejectedValue(new Error('Load failed'))
    
    // 执行回滚
    await hmr['rollback']()
    
    // 验证缓存已恢复
    expect(Map.prototype.get.call(
      ctx.loader.internal.loadCache, 'plugin.js'
    )).toBeDefined()
  })
})
8. 反射系统测试
8.1 Accessor 测试
TC-REF-001: 计算属性
P1
验证 Accessor 正确定义计算属性
describe('反射系统', () => {
  it('TC-REF-001: 应该定义计算属性', () => {
    const ctx = new Context()
    
    ctx.accessor('computed', {
      get() {
        return 42
      }
    })

    expect((ctx as any).computed).toBe(42)
  })

  it('TC-REF-002: setter 应该可选', () => {
    const ctx = new Context()
    
    ctx.accessor('readonly', {
      get() { return 'value' }
    })

    expect(() => { (ctx as any).readonly = 'new' }).toThrow()
  })
})
8.2 Mixin 测试
TC-REF-003: Mixin 转发
P1
验证 Mixin 正确转发服务方法
describe('Mixin 机制', () => {
  it('TC-REF-003: 应该转发服务方法到 ctx', () => {
    const ctx = new Context()
    
    // 内置 mixin 已经将 events 方法暴露到 ctx
    expect(typeof ctx.on).toBe('function')
    expect(typeof ctx.emit).toBe('function')
    expect(typeof ctx.waterfall).toBe('function')
  })

  it('TC-REF-004: mixin 应该绑定到正确的上下文', () => {
    const ctx = new Context()
    const child = ctx.extend()
    
    let calledCtx: any
    child.on('test', function() {
      calledCtx = this
    })
    
    child.emit('test')
    expect(calledCtx).toBe(child)
  })
})
9. 加载器测试
9.1 配置解析测试
TC-LDR-001: YAML 解析
P1
验证配置文件正确解析
describe('加载器', () => {
  it('TC-LDR-001: 应该解析 YAML 配置', async () => {
    const yaml = `
plugins:
  - name: test-plugin
    config:
      enabled: true
`
    // Mock 文件读取
    vi.spyOn(fs, 'readFile').mockResolvedValue(yaml)
    
    const include = new Include(ctx, { path: 'config.yaml' })
    await include.refresh()
    
    // 验证配置已应用
    expect(ctx.get('test-plugin')).toBeDefined()
  })
})
9.2 Entry 管理测试
TC-LDR-002: 条目禁用
P1
验证条目禁用和启用
describe('Entry 管理', () => {
  it('TC-LDR-002: 应该支持禁用条目', async () => {
    const ctx = new Context()
    ctx.plugin(Loader)
    
    // 添加条目
    const entry = ctx.loader.add({
      name: 'test-plugin',
      disabled: false
    })
    
    // 禁用条目
    entry.disabled = true
    await ctx.loader.update()
    
    // 验证插件已卸载
    expect(ctx.get('test-plugin')).toBeUndefined()
  })
})
10. 覆盖率指标
10.1 目标覆盖率
指标
目标
当前
状态
行覆盖率
≥ 85%
-
待测量
分支覆盖率
≥ 80%
-
待测量
函数覆盖率
≥ 85%
-
待测量
语句覆盖率
≥ 85%
-
待测量
10.2 执行命令
# 运行所有测试
pnpm test

# 运行带覆盖率的测试
pnpm test:coverage

# 运行特定模块测试
pnpm vitest run vendor/cordis/src/context.spec.ts

# 运行分区覆盖率
pnpm test:coverage:partitioned
测试执行流程
编写测试用例
运行
pnpm test
验证通过
运行
pnpm test:coverage
检查覆盖率
补充缺失的测试用例
提交代码前确保所有测试通过
参考文档
vendor/cordis/src/ — Cordis 框架核心源码
E:\chen\code\deepseek-harness\vendor\cordis\src\
vitest.config.ts — 测试配置文件
E:\chen\code\deepseek-harness\vitest.config.ts