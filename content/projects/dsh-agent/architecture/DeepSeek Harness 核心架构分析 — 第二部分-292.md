---
title: "DeepSeek Harness 核心架构分析 — 第二部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 核心架构分析 — 第二部分

## Session 生命周期、Scope 和依赖注入、事件系统

---

## 4. Session 生命周期

### 4.1 Session 的创建、初始化、运行、暂停、恢复、销毁

Session 的生命周期管理采用**三阶段发布协议**：

#### 创建阶段

1. **prepare**（`SessionStore.prepare()`）：构建一个未发布的 `Session` 对象
   - 验证 ID 唯一性
   - 验证 `cwd` 为绝对路径
   - 创建 `SessionHeader`（版本号、创建时间、血统等）
   - 如果有 seed，验证每个事件的 JSON 可序列性、序列号连续性

2. **enter**（`SessionStore.enter()`）：将 Session 安装到 store
   - 再次检查 ID 唯一性（prepare 和 enter 之间可能有并发操作）
   - 设置 `WeakMap<Session, SessionEntry>` 附件
   - 返回幂等的 detach 析构器
   - detach 在 `announcing` 或 `appending` 期间被延迟

3. **announce**（`SessionStore.announce()`）：发出 `session/created` 事件
   - 标记 `announced = true` 在派发之前
   - 同步监听器的 throw 可以否决发布

#### 运行阶段 — `Session.append()`

`append()` 方法是整个系统的写入热路径：

1. 快照化数据（`snapshotJsonValue`），确保 lossless-JSON 合规
2. 检查表面转换合法性（`surfaceManager.validateNext()`）
3. 在发布前收集监听器快照
4. 推入日志，使事件立即可见
5. 通知所有 `session/event` 监听器

#### 恢复阶段 — `PersistenceCoordinator.prepare()`

1. 等待同一 ID 的退役完成
2. 通过 `SessionPreparations` 预约机制获取或创建冷源
3. `prepareCore()`：从后端加载 → 验证 → 修复中断的 turn → 冻结
4. 修订检查：如果存储修订发生变化，重试
5. 包装为 `SessionPreparation`，支持 `using` 语义的自动释放

#### 销毁阶段

1. `SessionStore.detachEntered()`：从 store 移除，发出 `session/disposed`
2. `PersistenceCoordinator.retire()`：等待写后缓冲排空，清理状态

### 4.2 Session 状态的持久化机制

持久化采用**事件源模式 + 写后缓冲**：

**写路径**：
1. `Session.append()` 触发 `session/event` 事件
2. `PersistenceCoordinator` 的监听器将事件入队到 `SessionWriteBehind`
3. `SessionWriteBehind` 在延迟窗口（默认 200ms）后批量提交
4. `session/flush` 事件触发立即排空

**读路径**：
1. `SessionPersistence.load()` / `prepare()` 从后端加载完整日志
2. 验证事件格式版本、事件类型支持
3. 修复中断的 turn（合成 `turn/end` 和 `step/end`）
4. 通过 `Session.fromRestore()` 构造冻结的 Session 对象

### 4.3 并发 Session 管理

并发控制通过**三层序列化**实现：

1. **Per-ID 链**：`PersistenceCoordinator.serialize()` 为每个 session ID 维护一个 Promise 链
2. **预约机制**：`SessionPreparations` 管理冷读的共享、未发布预约和 LRU 缓存
3. **退役等待**：`waitForRetirement()` 确保退役完成前不会重新创建同 ID 的 session

---

## 5. Scope 和依赖注入

### 5.1 Scope 的层级结构

Scope 系统实现了**基于 WeakMap 的作用域链**：

- `scopeParents: WeakMap<ScopeKey, ScopeKey>` — 存储子→父的关系
- `carrierKeys: WeakMap<object, ScopeKey | undefined>` — 存储载体→密钥的关系
- `bindScopeParent(key, parent)` — 绑定父作用域（带循环检查）
- `scopeChainOf(key)` — 返回从 key 到根的完整链

**注册视图继承**方向：子作用域可以看到祖先的层（DOWN 链）
**事件准入**方向：祖先的监听器可以接收后代的事件（UP 链）

### 5.2 服务的注册和发现

服务注册通过 Cordis 的 Service 机制：

```typescript
export class SessionStore extends Service {
  constructor(ctx: Context) {
    super(ctx, 'sessions')  // 注册为 ctx.sessions
  }
}

export class AgentLoop extends Service {
  static inject = ['agents', 'sessions', 'llm', 'tools', 'systemPrompt']
}
```

`ScopedLayers` 管理作用域化的注册：
- `effect(ctx, action, options)` — 将注册绑定到上下文的作用域
- `merge(scope, pick)` — 按作用域链合并命名条目
- 自动清理：当作用域层变空时删除

### 5.3 作用域继承和隔离

`scopeTarget()` 函数是作用域事件路由的核心：

```typescript
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

事件**只向上流动，从不向下**。

---

## 6. 事件系统

### 6.1 事件的定义和触发

事件分为三大域：

**会话事件**（`SessionEventMap`）— 持久化事实：
- `turn/start`, `turn/end` — 轮次边界
- `step/start`, `step/end` — 步骤边界
- `user/message`, `assistant/message`, `tool/result` — 模型可见消息
- `assistant/chunk` — 流式 token 级保真
- `request/header`, `request/context` — 请求状态

**Agent 事件**（`agent/*`）— 实时扩展点：
- 生命周期：`agent/created`, `agent/disposed`, `agent/status`
- Inbox：`agent/inbox/inserted`, `agent/inbox/claimed`, `agent/inbox/discarded`
- 机器：`agent/pre-step`, `agent/request`, `agent/request-error`, `agent/turn-stopping`

**能力事件**（`tools/*` 等）— 无导入循环的 seam 附加：
- `tools/pre-execute`, `tools/execute`, `tools/post-execute` — 工具执行流水线
- `tools/result` — 工具结果通知

### 6.2 事件的传播机制

**emit（火并忘）** — 每个监听器都被调用，失败被记录和遏制

**serial（串行等待）** — 按顺序调用每个监听器，等待其完成

**waterfall（瀑布式）** — 中间件模式，监听器必须调用 `next()` 委托

### 6.3 事件的消费模式

```typescript
// 观察模式
ctx.on('session/event', (session, event) => { /* 持久化、遥测 */ })

// 拦截模式
ctx.on('agent/pre-step', async ({ agent, messages, signal }, next) => {
  const decision = await next()
  return { kind: 'enter', messages: [...decision.messages, extraContext] }
})

// 包装模式
ctx.on('tools/execute', async (exec, next) => {
  return await next()  // 超时、重试、指标
})
```
