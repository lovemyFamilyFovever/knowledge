---
title: "DeepSeek Harness 核心架构分析 — 第二部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 核心架构分析

第二部分：Session 生命周期、Scope 和依赖注入、事件系统

## 4. Session 生命周期

### 4.1 Session 的创建、初始化、运行、暂停、恢复、销毁

Session 的生命周期管理是整个系统中最精密的部分，设计采用了三阶段发布协议：

#### 创建阶段 — prepare → enter → announce

1. prepare（SessionStore.prepare()）：构建一个未发布的 Session 对象

- 验证 ID 唯一性

- 验证 `cwd` 为绝对路径

- 创建 `SessionHeader`（版本号、创建时间、血统等）

- 如果有 seed，验证每个事件的 JSON 可序列性、序列号连续性、表面转换合法性

2. enter（SessionStore.enter()）：将 Session 安装到 store，建立发布钩子

- 再次检查 ID 唯一性（prepare 和 enter 之间可能有并发操作）

- 设置 `WeakMap` 附件，使 `append()` 可以触发布通知

- 返回幂等的 detach 析构器

- 关键设计：detach 在 `announcing` 或 `appending` 期间被延迟，确保一致性

3. announce（SessionStore.announce()）：发出 session/created 事件

- 标记 `announced = true` 在派发之前，防止递归创建

- 同步监听器的 throw 可以否决发布（触发回滚）

- 返回的 promise rejection 只能被记录，不能追溯否决

#### 运行阶段 — Session.append()

append() 方法是整个系统的写入热路径：

- 快照化数据（`snapshotJsonValue`），确保 lossless-JSON 合规

- 检查表面转换合法性（`surfaceManager.validateNext()`）

- 在发布前收集监听器快照（确保一致性视图）

- 推入日志，使事件立即可见

- 通知所有 `session/event` 监听器（失败被遏制）

- 清除事件快照缓存，使 `events` getter 返回新鲜快照

#### 恢复阶段 — PersistenceCoordinator.prepare()

- 等待同一 ID 的退役完成

- 通过 `SessionPreparations` 预约机制获取或创建冷源

- `prepareCore()`：从后端加载 → 验证 → 修复中断的 turn → 冻结

- 修订检查：如果存储修订自上次读取后发生变化，重试

- 包装为 `SessionPreparation`，支持 `using` 语义的自动释放

#### 销毁阶段

- `SessionStore.detachEntered()`：从 store 移除，发出 `session/disposed`

- `PersistenceCoordinator.retire()`：等待写后缓冲排空，清理状态

### 4.2 Session 状态的持久化机制

持久化采用事件源模式 + 写后缓冲：

#### 写路径

- `Session.append()` 触发 `session/event` 事件

- `PersistenceCoordinator` 的监听器将事件入队到 `SessionWriteBehind`

- `SessionWriteBehind` 在延迟窗口（默认 200ms）后批量提交

- `session/flush` 事件触发立即排空

- `PersistenceCoordinator.appendCore()` 验证序列号连续性后调用后端 `appendBatch()`

#### 读路径

- `SessionPersistence.load()` / `prepare()` 从后端加载完整日志

- 验证事件格式版本、事件类型支持、JSON 可序列性

- 修复中断的 turn（合成 `turn/end` 和 `step/end`）

- 通过 `Session.fromRestore()` 构造冻结的 Session 对象

### 4.3 并发 Session 管理

三层序列化保护：

- **Per-ID 链**：`PersistenceCoordinator.serialize()` 为每个 session ID 维护一个 Promise 链，确保同一 session 的操作不会交错

- **预约机制**：`SessionPreparations` 管理冷读的共享、未发布预约和 LRU 缓存

- **退役等待**：`waitForRetirement()` 确保退役完成前不会重新创建同 ID 的 session

## 5. Scope 和依赖注入

### 5.1 Scope 的层级结构

Scope 系统实现了基于 WeakMap 的作用域链：

- `scopeParents: WeakMap` — 存储子→父的关系

- `carrierKeys: WeakMap` — 存储载体→密钥的关系

- `bindScopeParent(key, parent)` — 绑定父作用域（带循环检查）

- `scopeChainOf(key)` — 返回从 key 到根的完整链

双向继承规则：

- **注册视图继承**方向：子作用域可以看到祖先的层（DOWN 链）

- **事件准入**方向：祖先的监听器可以接收后代的事件（UP 链）

### 5.2 服务的注册和发现

服务注册通过 Cordis 的 Service 机制：

```
export class SessionStore extends Service {
  constructor(ctx: Context) {
    super(ctx, 'sessions')  // 注册为 ctx.sessions
  }
}

export class AgentLoop extends Service {
  static inject = ['agents', 'sessions', 'llm', 'tools', 'systemPrompt']
}
```

ScopedLayers 管理作用域化的注册：

- `effect(ctx, action, options)` — 将注册绑定到上下文的作用域

- `merge(scope, pick)` — 按作用域链合并命名条目

- 自动清理：当作用域层变空时删除

### 5.3 作用域继承和隔离

scopeTarget() 函数是作用域事件路由的核心：

```
export function scopeTarget<T extends object>(base: T, key: ScopeKey | undefined): Scoped<T> {
  const carrier = {
    [CordisContext.filter](ctx: Context): boolean {
      if (baseFilter !== undefined && !baseFilter.call(base, ctx)) return false
      const tag = scopeOf(ctx)
      if (tag === undefined) return true  // 未标记的监听器全局接收
      for (let cursor = key; cursor !== undefined; cursor = scopeParents.get(cursor)) {
        if (cursor === tag) return true  // 匹配 key 或任何祖先
      }
      return false  // 标签在 key 下方，排除
    },
  }
}
```

事件只向上流动，从不向下。这意味着一个 standing composition 可以观察其下所有 Agent 的事件，但一个 Agent 的监听器不会看到其他无关 Agent 的事件。

## 6. 事件系统

### 6.1 事件的定义和触发

事件分为三大域，每个域有明确的语义和用途：

#### 会话事件（SessionEventMap）— 持久化事实

| 事件类型 | 用途 |
| --- | --- |
| `turn/start`, `turn/end` | 轮次边界 |
| `step/start`, `step/end` | 步骤边界 |
| `user/message`, `assistant/message`, `tool/result` | 模型可见消息（Surface 事件） |
| `assistant/chunk` | 流式 token 级保真 |
| `request/header`, `request/context` | 请求状态 |
| `agent/inbox/spliced` | Inbox 变更 |
| `todo/write` | 待办列表快照 |
| `session/end-seed` | 种子边界标记 |

#### Agent 事件（agent/*）— 实时扩展点

| 事件类型 | 用途 | 分发模式 |
| --- | --- | --- |
| `agent/created`, `agent/disposed` | 生命周期通知 | emit |
| `agent/status` | 状态变更通知 | emit |
| `agent/inbox/inserted`, `agent/inbox/claimed`, `agent/inbox/discarded` | Inbox 变更 | emit |
| `agent/session-start` | Session 生命周期开始 | emit |
| `agent/pre-step` | 步骤前决策 | waterfall |
| `agent/request` | 请求配置替换 | waterfall |
| `agent/request-error` | 请求错误恢复 | waterfall |
| `agent/turn-stopping` | 轮次即将关闭 | serial |
| `agent/error` | 错误通知 | emit |

#### 能力事件（tools/* 等）— 无导入循环的 seam 附加

| 事件类型 | 用途 | 分发模式 |
| --- | --- | --- |
| `tools/pre-execute` | 工具执行前审批 | waterfall |
| `tools/execute` | 工具执行包装（超时、重试、指标） | waterfall |
| `tools/post-execute` | 工具执行后处理 | waterfall |
| `tools/result` | 工具结果通知 | emit |
| `tools/change` | 工具注册变更 | emit |

### 6.2 事件的传播机制

事件传播采用 Cordis 的三种分发模式：

#### emit（火并忘）

每个监听器都被调用，失败被记录和遏制。用于通知性事件，不影响控制流。

#### serial（串行等待）

按顺序调用每个监听器，等待其完成。用于 agent/turn-stopping 等需要协调的事件。

#### waterfall（瀑布式）

中间件模式，监听器必须调用 next() 委托。用于 agent/pre-step、agent/request、tools/execute 等需要拦截和改写的事件。

### 6.3 事件的消费模式

```
// 观察模式 — 监听 session/event
ctx.on('session/event', (session, event) => {
  // 持久化、遥测、UI 更新
})

// 拦截模式 — 监听 agent/pre-step
ctx.on('agent/pre-step', async ({ agent, messages, signal }, next) => {
  const decision = await next()
  return { kind: 'enter', messages: [...decision.messages, extraContext] }
})

// 包装模式 — 监听 tools/execute
ctx.on('tools/execute', async (exec, next) => {
  // 超时、重试、指标
  return await next()
})

// 通知模式 — 监听 tools/result
ctx.on('tools/result', (exec, result) => {
  // UI 更新、日志
})
```

DeepSeek Harness 核心架构分析 — 第二部分 | 生成日期：2026-08-29
