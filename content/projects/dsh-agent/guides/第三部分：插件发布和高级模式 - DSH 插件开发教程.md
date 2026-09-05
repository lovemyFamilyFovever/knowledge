---
title: "第三部分：插件发布和高级模式 - DSH 插件开发教程"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 插件开发教程"
collected: "2026-09-05"
status: "imported"
---

第三部分：插件发布和高级模式 - DSH 插件开发教程
← 上一部分
返回目录
🚀 第三部分：插件发布和高级模式
🎯 核心内容
本部分将介绍插件发布流程、高级开发模式、现有插件源码分析、常见错误和最佳实践总结。
1. 插件发布和分发
1.1 npm 发布流程
DSH 使用 pnpm monorepo 结构，插件发布需要遵循特定的流程：
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
1.2 package.json 配置
确保你的
package.json
包含正确的发布配置：
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
1.3 插件注册和发现
插件可以通过以下方式注册到 DSH：
方式一：在 cordis.yml 中配置
# cordis.yml
- id: my-plugin
  config:
    apiKey: '!!js process.env.MY_API_KEY'
    someOption: true
方式二：通过命令行参数
dsh --plugin my-plugin --config '{"apiKey": "xxx"}'
方式三：在代码中动态加载
import { Context } from '@deepseek-ai/cordis'
import { apply as myPlugin } from '@deepseek-ai/dsh-my-plugin'

const ctx = new Context()
ctx.plugin(myPlugin, { apiKey: 'xxx' })
2. 高级模式
2.1 插件组合和继承
插件可以通过组合多个小插件来创建更复杂的功能：
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
2.2 条件加载
根据环境或配置条件加载插件：
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
在
cordis.yml
中使用
disabled
字段：
# cordis.yml
- id: debug-tools
  disabled: '!!js process.env.NODE_ENV === "production"'
  config: {}

- id: redis-storage
  disabled: '!!js !process.env.REDIS_HOST'
  config:
    host: '!!js process.env.REDIS_HOST'
2.3 热重载
DSH 的所有注册都是基于效果的（effect-based），这意味着热重载（HMR）可以无缝工作：
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
✅ 热重载工作原理：
旧的清理函数会被调用，移除所有旧的注册
新的
apply
函数执行，注册新的功能
所有依赖此插件的服务会自动更新
3. 现有插件源码分析
3.1 分析 packages/fs
packages/fs
是文件系统访问插件，它展示了典型的能力接缝（capability seam）模式：
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
3.2 核心代码示例
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
4. 常见错误和解决方案
4.1 循环依赖
⚠️ 问题：
两个插件互相依赖对方的服务。
解决方案：
使用事件系统进行松耦合通信
引入第三个插件作为中介
使用延迟初始化模式
// 正确示例：使用事件通信
export function apply(ctx: Context) {
  ctx.on('plugin-b-event', (data) => {
    // 处理来自 pluginB 的事件
  })
  
  // 发送事件给 pluginA
  ctx.emit('plugin-a-event', { data: 'xxx' })
}
4.2 服务未注册
⚠️ 问题：
尝试访问未注册的服务。
解决方案：
使用
inject
声明依赖
使用
ctx.get()
检查服务是否存在
使用可选依赖模式
// 使用可选依赖
export function apply(ctx: Context) {
  const llm = ctx.get('llm')
  if (!llm) {
    console.warn('LLM service not available, some features disabled')
    return
  }
  
  // 使用 llm 服务
}
4.3 内存泄漏
⚠️ 问题：
插件卸载后，注册的监听器或定时器仍然存在。
解决方案：
始终使用
ctx.effect()
注册可清理的资源
使用
ctx.on()
而不是原生
addEventListener
确保异步操作支持取消
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
5. 最佳实践总结
5.1 设计原则
🎯 单一职责
每个插件只负责一个功能领域
🔗 松耦合
通过事件和服务接口进行通信，避免直接依赖
🔄 可替换性
设计接口时考虑多种实现可能
⚙️ 配置驱动
通过配置控制行为，而不是硬编码
5.2 代码规范
类型安全
：充分利用 TypeScript 的类型系统
错误处理
：使用
LlmError
、
StorageError
等领域错误类型
资源管理
：始终清理注册的资源，使用
ctx.effect()
测试覆盖
：编写单元测试和集成测试
5.3 插件清单
创建一个新插件时，请确保：
☐ 正确的
package.json
配置
☐ 正确的
tsconfig.json
配置
☐ 导出
name
、
inject
、
apply
函数
☐ 使用
ctx.effect()
管理资源
☐ 处理所有错误情况
☐ 编写测试用例
☐ 编写 README 文档
☐ 遵循 DSH 的命名规范
←
上一部分
|
返回目录
📄 DeepSeek Harness Plugin Development Tutorial - Part 3