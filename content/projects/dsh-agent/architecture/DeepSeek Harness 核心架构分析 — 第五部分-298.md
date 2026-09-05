---
title: "DeepSeek Harness 核心架构分析 — 第五部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 核心架构分析 — 第五部分

## Subagent 委派机制与 Compaction（压缩）机制

---

## 13. Subagent 委派机制

### 13.1 委派模型

DeepSeek Harness 的 subagent 委派通过 `AgentFactory` 接口实现。一个 Agent 可以通过 `ctx.agents.create()` 创建子 Agent，形成 Agent 树：

```
Root Agent (depth: 0)
  ├── Subagent A (depth: 1)
  │     └── Subagent A1 (depth: 2)
  └── Subagent B (depth: 1)
```

### 13.2 创建流程

子 Agent 的创建流程与顶级 Agent 相同，但增加了血统信息：

1. 父 Agent 调用 `ctx.agents.create(options)`
2. `options.meta` 携带血统信息：
   - `parentSession`：父 Session 的 ID
   - `delegationDepth`：递归深度预算（父深度 + 1）
   - `origin: 'subagent'`：标记为子 Agent
   - `agentPreset`：Agent 预设 ID
3. `options.seed` 可以传递父 Session 的历史前缀（fork 场景）
4. 工厂创建 Session + Agent，通过 `AgentSetup` 回调组合子 Agent 的世界

### 13.3 作用域继承

子 Agent 的作用域继承通过 `bindScopeParent()` 实现：

```typescript
// 在 createScope 时绑定父作用域
const scope = createScope(loopCtx, this, { parent: parentAgent })
```

这使得：
- 子 Agent 可以看到父 Agent 注册的工具、提示词片段和变量
- 父 Agent 的监听器可以接收子 Agent 的事件（事件向上流动）
- 子 Agent 的私有注册不会泄漏到父 Agent

### 13.4 发起者作用域链

`AgentRegistry` 通过 `AsyncLocalStorage` 维护发起者作用域链：

```typescript
// 设置发起者
ctx.agents.withInitiator(agent, () => {
  // 此回调内的所有异步操作都继承这个 agent 作为发起者
})

// 读取发起者
const initiator = ctx.agents.currentInitiator() // 可能为 undefined
const initiator = ctx.agents.requireInitiator()  // 必须存在
```

发起者作用域的特点：
- **进程本地**：仅用于日志、追踪和指标，不是身份证明
- **异步传播**：通过 `AsyncLocalStorage` 在 Promise 链中传播
- **嵌套支持**：子操作可以建立自己的发起者边界
- **清理机制**：`closeInitiators()` 拒绝新边界，`disposeInitiators()` 等待排水

### 13.5 模型选择

子 Agent 可以使用与父 Agent 不同的模型。`installModelSelection()` 函数将可变的模型选择耦合到 Agent 作用域的提示词组装和请求路由：

```typescript
interface ModelSelection {
  provider: string
  model: string
  reasoningEffort?: ReasoningEffortId
}
```

- 提示词组装时快照选中的模型
- 请求路由时应用选中的 provider/model 对
- 并发切换在后续步骤生效，不会分裂两个表面

### 13.6 消费工作记账

`foldConsumedWork()` 函数追踪 Agent 日志中已消费的工作：

```typescript
interface ConsumedWork {
  end?: SessionEvent<'turn/end'>  // 最新的已关闭轮次
  droppedUnrun: boolean           // 是否有工作被取消未运行
}
```

这解决了轮次词汇表无法回答的问题：一个在首个步骤前停止的轮次与一个平衡的空操作轮次形状相同。Inbox 的 `removedCount` 和 `outcome: 'canceled'` 标记提供了缺失的事实。

---

## 14. Compaction（压缩）机制

### 14.1 服务定义

`CompactionEngine` 是一个抽象服务（`ctx.compaction`），由具体的后端实现。它负责：

- 决定何时压缩
- 选择压缩范围
- 生成摘要
- 替换历史范围

### 14.2 压缩触发

两种触发方式：

| 触发类型 | 说明 | 调用方法 |
|---|---|---|
| `pressure` | 上下文窗口压力 | `compactIfNeeded(agent, 'pressure', signal)` |
| `context-overflow` | 提供者确认的上下文溢出 | `compactIfNeeded(agent, 'context-overflow', signal)` |
| 手动 | 用户命令 | `compactNow(agent, signal, commandId)` |

### 14.3 压缩流程

```
1. compaction/start → 记录锁定标记
2. 选择压缩范围（必须平衡：assistant tool calls 与 results 配对）
3. 调用 LLM 生成摘要
4. compaction/summary → 记录摘要和元数据
5. user/message (surfaceOp: replace) → 替换选定的表面范围
6. compaction/end → 释放锁定
```

### 14.4 会话事件

压缩引入了四个新的会话事件类型：

| 事件 | 说明 |
|---|---|
| `compaction/start` | 标记压缩开始，持有锁定直到 `compaction/end` |
| `compaction/summary` | 完成的摘要、输入和模型调用事实 |
| `compaction/end` | 标记压缩结束，释放锁定 |
| `compaction/prune` | 无模型的剪枝替换的影子价格 |

### 14.5 Surface 替换

压缩使用 `SurfaceOp` 的 `replace` 操作：

```typescript
type SurfaceOp = 'append' | { op: 'replace'; start: number; end: number }
```

替换操作：
- `start` 和 `end` 是表面位置（不是数字 seq 顺序）
- 替换可以使得可见 seq 非单调
- 两个边界必须平衡（assistant tool calls 与 results 配对）
- `sourceEventSeqs` 必须包含所有被遮蔽的表面节点

### 14.6 影子价格协议

压缩使用影子价格协议来追踪被替换内容的 token 成本：

- 表面 `replace` 事件的价格由其紧前面的计量事件声明
- `compaction/summary` 用于有摘要的压缩
- `compaction/prune` 用于无模型的剪枝
- 纯消费者可以减去它而不需要保留每个节点的价格

### 14.7 并发保护

压缩通过 `compaction/start` 和 `compaction/end` 事件对实现并发保护：

- 同一 Session 不能同时进行多次压缩
- `compaction/start` 是压缩锁定
- `compaction/end` 释放锁定
- 失败的尝试仍然在日志中可见

---

## 15. Surface 投影机制

### 15.1 Surface 概念

Surface 是 Session 日志之上的有序视图，只包含模型可见的消息事件。它由 `SurfaceManager` 维护：

- `user/message`
- `assistant/message`
- `tool/result`

这些事件类型称为 `SurfaceEventType`，它们可以携带 `surfaceOp` 和 `sourceEventSeqs`。

### 15.2 Surface 操作

| 操作 | 说明 |
|---|---|
| `append` | 添加到尾部 — 正常路径 |
| `{ op: 'replace', start, end }` | 替换从 `start` 到 `end`（含）的表面节点 |

### 15.3 消息历史派生

`Session.deriveMessages()` 从 Surface 派生 LLM 消息历史：

```typescript
deriveMessages(): Message[] {
  for (const seq of surface.nodes.slice(this.derivedNodes)) {
    const msg = this.deriveEventMessage(this.log[seq])
    if (msg) this.derived.push(msg)
  }
  this.derivedNodes = nodes.length
  return [...this.derived]
}
```

- 每个表面节点只投影一次（增量缓存）
- Surface 重写（`replace`）触发重建
- 返回的数组是新鲜快照，消息对象是共享且深度冻结的

### 15.4 表面事件过滤

`deriveEventMessage()` 根据事件类型投影：

- `user/message` → 直接使用
- `assistant/message` → 使用 `event.data.message`
- `tool/result` → 使用 `event.data.message`
- 空内容的 `assistant/message` → 返回 null（不进入转录）

---

## 16. 架构全景图

### 16.1 核心服务依赖关系

```
ctx.sessions (SessionStore)
  ↑
ctx.agents (AgentRegistry)
  ↑
ctx.agentLoop (AgentLoop / AgentFactory)
  ↑
ctx.systemPrompt (SystemPrompt) + ctx.tools (ToolRuntime) + ctx.llm (LlmService)
  ↑
ctx.compaction (CompactionEngine) + ctx.sessionPersistence (SessionPersistence)
```

### 16.2 事件域总结

| 域 | 持久化 | 用途 | 分发模式 |
|---|---|---|---|
| 会话事件 | 是 | 模型上下文的唯一来源 | emit（session/event） |
| Agent 事件 | 否 | 实时扩展点 | emit / serial / waterfall |
| 能力事件 | 否 | 无导入循环的 seam 附加 | waterfall / emit |

### 16.3 设计原则总结

1. **事件溯源**：一切模型可见的上下文都是已记录的事实
2. **插件化**：一切行为都是可替换的插件
3. **投影**：一切状态都是可投影的事件流
4. **作用域隔离**：私有注册不会泄漏
5. **并发安全**：三层序列化保护
6. **错误遏制**：每层边界都有独立的错误遏制机制
