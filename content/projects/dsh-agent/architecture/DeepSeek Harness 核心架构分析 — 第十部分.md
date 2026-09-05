---
title: "DeepSeek Harness 核心架构分析 — 第十部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 核心架构分析 — 第十部分

## 客户端架构与扩展系统

---

## 41. 客户端架构

### 41.1 子包组成

`packages/client/` 包含 30+ 个 UI 模块包，每个负责一个 UI 功能域：

| 子包 | 职责 |
|---|---|
| `client/connection` | 客户端-主机连接 |
| `client/runtime` | 客户端运行时 |
| `client/modules` | 模块注册 |
| `client/locale` | 国际化 |
| `client/hmr` | 热模块替换 |
| `client/ui-layout` | 布局框架 |
| `client/ui-conversation` | 对话 UI |
| `client/ui-tool` | 工具 UI |
| `client/ui-plan` | 计划 UI |
| `client/ui-settings` | 设置 UI |
| `client/ui-sidebar` | 侧边栏 |
| `client/ui-theme` | 主题 |
| `client/web` | Web 入口 |

### 41.2 连接模型

客户端通过 JSON-RPC 或 WebSocket 连接到主机进程：
- 主机运行 Cordis 服务树
- 客户端通过 `ctx.sessions`、`ctx.agents` 等服务的投影访问状态
- `session/event` 实时推送到客户端

### 41.3 UI 模块架构

每个 UI 模块是一个 Cordis 插件：
- 注册 `ConversationNodeDefinition`（对话节点定义）
- 注册渲染器
- 注册设置卡片
- 注册命令

---

## 42. 扩展系统

### 42.1 Cordis 插件模型

DeepSeek Harness 的扩展完全基于 Cordis 插件模型：

```typescript
// 插件定义
export const name = 'my-plugin'
export const inject = ['agents', 'sessions']
export function apply(ctx: Context, config: Config): void {
  // 注册服务、监听事件、注册工具等
}
```

### 42.2 扩展点总览

| 扩展点 | 机制 | 说明 |
|---|---|---|
| 添加模型提供方 | `ctx.llm.registerAdapter()` | 注册 LLM 适配器 |
| 添加工具 | `ctx.tools` 注册 | 注册 `ToolDefinition` |
| 添加提示词 | `ctx.systemPrompt.section()` | 注册系统提示词片段 |
| 添加运行时上下文 | `ctx.systemPrompt.context()` | 注册动态上下文 |
| 添加变量 | `ctx.systemPrompt.variable()` | 注册模板变量 |
| 添加沙箱后端 | `ctx.sandbox` 注册 | 注册 `SandboxProvider` |
| 添加持久化后端 | `ctx.sessionPersistence` 注册 | 注册 `SessionPersistence` |
| 添加存储后端 | `ctx.storage.backend.register()` | 注册 `StorageBackend` |
| 添加凭据提供者 | `ctx.credentials` 注册 | 注册凭据解析 |
| 添加代码运行时 | `ctx.codeRuntime` 注册 | 注册 `CodeRuntime` |
| 拦截工具执行 | `tools/pre-execute` | 审批和守卫 |
| 拦截模型请求 | `agent/request` | 替换调用配置 |
| 拦截步骤 | `agent/pre-step` | 改写或拒绝步骤 |
| 监听会话事件 | `session/event` | 持久化、遥测、UI |
| 监听工具结果 | `tools/result` | 后处理 |

### 42.3 组合包（Bundle）

组合包是 Cordis 配置项及其挂载代码的分发格式：

```yaml
# cordis.patch.yml
- id: my-agent
  config:
    provider: deepseek
    model: deepseek-chat
```

### 42.4 Profile

Profile 是存放在 Harness home 中的具名组装：
- 列出叠放的组合包
- 存放树外插件
- 保存用户的 `cordis.patch.yml`

---

## 43. 命令系统

### 43.1 命令注册

```typescript
ctx.commands.register({
  name: 'compact',
  description: '压缩会话历史',
  execute: async (agent) => { /* ... */ }
})
```

命令无需模型轮次即可分派。

---

## 44. 后台作业系统

### 44.1 作业注册

```typescript
ctx.jobs.register({
  name: 'export',
  execute: async (signal) => { /* ... */ }
})
```

`job_*` 工具负责收集或停止作业。

---

## 45. 全局架构视图

```
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
```

---

## 46. 文档体系

项目维护了完善的文档体系：

| 文档 | 说明 |
|---|---|
| `docs/architecture.md` | 架构总览 |
| `docs/cordis-primer.md` | Cordis 入门 |
| `docs/cordis-tutorial/` | Cordis 教程（7 章） |
| `docs/subsystems/` | 子系统文档（40+ 篇） |
| `docs/cookbook/` | 扩展实操手册 |
| `docs/postmortem/` | 事后分析 |
| `.agents/notes/` | Agent 笔记（实现决策记录） |
| `AGENTS.md` | 代码库约定 |
