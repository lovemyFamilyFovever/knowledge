---
title: "DeepSeek Harness (DSH) 插件开发教程"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 插件开发教程"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness (DSH) 插件开发教程
🚀 DeepSeek Harness (DSH) 插件开发教程
本教程详细介绍了如何为 DeepSeek Harness 开发自定义插件。DSH 是 DeepSeek AI 开源的智能 Agent 框架，采用"一切皆插件"的极致模块化架构。
📚 目录
第一部分：基础架构
"一切皆插件"的设计哲学
Cordis 依赖注入框架简介
插件的分类（Tool、Provider、UI、Storage、Service）
从零创建一个 Tool 插件
插件间通信机制
第二部分：高级插件开发
LLM 抽象层接口
实现自定义 Provider
创建存储后端插件
插件测试方法
第三部分：发布和最佳实践
插件发布和分发流程
高级模式（组合、条件加载、热重载）
现有插件源码分析
常见错误和解决方案
最佳实践总结
⚡ 快速开始
环境要求
Node.js >= 18
pnpm >= 8
TypeScript >= 5
创建你的第一个插件
// packages/tools/my-tool/src/index.ts
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'my-tool'
export const inject = ['tools']

export function apply(ctx: Context) {
  ctx.tools.register(defineTool({
    name: 'hello',
    description: 'Say hello',
    parameters: {
      name: { type: 'string', required: true },
    },
    async execute(args) {
      return { message: `Hello, ${args.name}!` }
    },
  }))
}
配置插件
# cordis.yml
- id: my-tool
  config: {}
运行测试
pnpm test
🔗 相关资源
DSH 官方文档
Cordis 框架文档
GitHub 仓库
🤝 贡献指南
欢迎贡献代码和文档！请遵循以下步骤：
Fork 仓库
创建功能分支
提交更改
创建 Pull Request
📄 MIT License | DeepSeek Harness Plugin Development Tutorial