---
title: "DeepSeek Harness 核心架构分析 — 第十部分：客户端与扩展"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 核心架构分析 — 第十部分：客户端与扩展
DeepSeek Harness 核心架构分析
第十部分：客户端架构与扩展系统
41. 客户端架构
41.1 子包组成
packages/client/
包含 30+ 个 UI 模块包，每个负责一个 UI 功能域：
子包
职责
client/connection
客户端-主机连接
client/runtime
客户端运行时
client/modules
模块注册
client/locale
国际化
client/hmr
热模块替换
client/ui-layout
布局框架
client/ui-conversation
对话 UI
client/ui-tool
工具 UI
client/ui-settings
设置 UI
client/web
Web 入口
41.2 连接模型
客户端通过 JSON-RPC 或 WebSocket 连接到主机进程。主机运行 Cordis 服务树，客户端通过投影访问状态。
session/event
实时推送到客户端。
42. 扩展系统
42.1 Cordis 插件模型
export const name = 'my-plugin'
export const inject = ['agents', 'sessions']
export function apply(ctx: Context, config: Config): void {
  // 注册服务、监听事件、注册工具等
}
42.2 扩展点总览
扩展点
机制
说明
添加模型提供方
ctx.llm.registerAdapter()
注册 LLM 适配器
添加工具
ctx.tools
注册
注册
ToolDefinition
添加提示词
ctx.systemPrompt.section()
注册系统提示词片段
添加沙箱后端
ctx.sandbox
注册
注册
SandboxProvider
添加持久化后端
ctx.sessionPersistence
注册
注册
SessionPersistence
添加存储后端
ctx.storage.backend.register()
注册
StorageBackend
添加代码运行时
ctx.codeRuntime
注册
注册
CodeRuntime
拦截工具执行
tools/pre-execute
审批和守卫
拦截模型请求
agent/request
替换调用配置
拦截步骤
agent/pre-step
改写或拒绝步骤
监听会话事件
session/event
持久化、遥测、UI
43-44. 命令与后台作业
命令（
ctx.commands
）无需模型轮次即可分派。后台作业（
ctx.jobs
）通过
job_*
工具收集或停止。
45. 全局架构视图
┌─────────────────────────────────────────────────────────────┐
│                     Cordis 框架                              │
├─────────────────────────────────────────────────────────────┤
│  Profile → Bundle → Patch → 插件树                           │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  LLM     │  Session │  Agent   │  Tools   │  Context        │
│  适配器   │  持久化   │  循环    │  执行    │  注入           │
├──────────┼──────────┼──────────┼──────────┼─────────────────┤
│  Sandbox │  Storage │  Creds   │  Settings│  Code Runtime   │
│  沙箱    │  存储    │  凭据    │  设置    │  代码运行时      │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                     Client / Web UI                          │
└─────────────────────────────────────────────────────────────┘
46. 文档体系
文档
说明
docs/architecture.md
架构总览
docs/cordis-primer.md
Cordis 入门
docs/cordis-tutorial/
Cordis 教程（7 章）
docs/subsystems/
子系统文档（40+ 篇）
docs/cookbook/
扩展实操手册
.agents/notes/
Agent 笔记（实现决策记录）
DeepSeek Harness 核心架构分析 — 第十部分 | 生成日期：2026-08-29