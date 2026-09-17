---
title: "DeepSeek Harness 模型接入层深度分析 — 第二部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 模型接入层"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 模型接入层深度分析 — 第二部分

## 4. SDK 客户端 API

### 4.1 客户端封装的设计

SDK 客户端分为两层：

**底层：`HarnessClient`**（`sdk/client/src/client.ts`）

这是一个 JSON-RPC 客户端，通过子进程 stdio 与 Harness 运行时通信。核心设计：

- **懒启动** — `start()` 在第一次请求时自动调用，幂等
- **子进程所有权** — 客户端完全拥有子进程的生命周期
- **通知订阅** — `subscribe(filter)` 返回 `NotificationSubscription`，支持异步迭代、队列和等待者模式
- **会话树订阅** — `subscribeSessionTree(sessionId)` 通过 `subagent.started` 的父/子关系边自动发现后代会话

`NotificationSubscriptionImpl` 实现了生产者-消费者模式：
- `push(notification)` — 过滤匹配后推送给等待者或入队
- `next()` — 从队列取或注册等待者
- `tryNext()` — 非阻塞出队
- `close()` — 断开并丢弃队列
- `fail(error)` — 终端失败，拒绝待处理的等待者

**高层：`DeepSeekHarness`**（`sdk/client/src/api.ts`）

封装了启动握手、会话管理和运行 API：

```typescript
const harness = new DeepSeekHarness({
  launch: { command: 'dsh-jsonrpc-agent', args: ['--config', 'cordis.yml'] },
  provider: 'deepseek-official',
  model: 'deepseek-v4-flash',
})

// 一行完成 prompt → 等待 idle → 获取结果
const result = await harness.run('Hello, world!')
console.log(result.finalResponse)
```

`HarnessSession.run()` 的流程：
1. 确保 harness 已初始化
2. 订阅会话树通知
3. 发送 prompt，获取 messageId
4. 等待 inbox receipt 确认消息已入队
5. 收集所有 session.event 和通知
6. 等待 session.status == 'idle' 终止
7. 返回 `RunResult`（sessionId、finalResponse、events、notifications）

`DeepSeekHarness` 实现了 `AsyncDisposable`，支持 `await using` 语法自动关闭。

### 4.2 请求重试和错误处理

**SDK 客户端层的错误处理**：

三种错误类型：
- `TransportClosedError` — 子进程死亡或不可用，消息包含退出码和 stderr 尾部
- `RequestTimeoutError` — 请求超时，超时后放弃（abandon）而非取消
- `SdkProtocolError` — 运行时返回协议外的响应

**请求超时机制**：
- 可配置的 `requestTimeoutMs`
- 使用 `AbortController` 实现放弃语义——超时后传输丢弃待处理条目
- 运行时死亡时快速失败而非等到超时

**LLM 层的重试机制**（`llm-retry` 插件）：

`llm-retry` 插件安装在 `agent/request-error` waterfall 上，实现 provider 路由的请求恢复。两种重试模式：

- **normal** — 仅重试配置的瞬态失败码，默认最多 5 次
- **always** — 重试所有失败，直到成功、取消或处置

重试延迟采用**有界指数退避 + 对称抖动**。默认可重试错误码：`EMPTY_RESPONSE`、`RATE_LIMIT`、`SERVER`、`TIMEOUT`、`TRANSPORT`。

关键设计决策：
- 重试前先持久化 `llm/retry` 事件，再等待延迟，确保可恢复性
- 尊重 provider 返回的 `Retry-After` 头，但限制在 `maxDelayMs` 内
- 插件处置时取消所有活跃等待并排空

### 4.3 超时和取消机制

**多层取消信号融合**：

DeepSeek 适配器中：
```typescript
const upstream = options.signal === undefined
  ? consumer.signal
  : AbortSignal.any([options.signal, consumer.signal])
using watchdog = idleWatchdog(upstream, timeoutMs, 'LLM_STREAM_IDLE_TIMEOUT')
```

三层信号：
1. `options.signal` — 调用者取消
2. `consumer.signal` — 消费者停止消费
3. `watchdog.signal` — 空闲超时

**子进程处置梯子**（`sdk/client/src/dispose.ts`）：

```
stdin EOF（合作式退出，等待 disposeEofGraceMs）
  → SIGTERM（POSIX 优雅终止，等待 disposeGraceMs）
    → SIGKILL（强制终止，等待 disposeGraceMs）
```

Windows 平台跳过 SIGTERM，直接使用强制终止。

---

## 5. SDK 服务端 API

### 5.1 服务端接口定义

**`HarnessSdkJsonRpcServer`**（`sdk/server/src/server.ts`）是运行时侧的 JSON-RPC 服务器。

三个 RPC 方法：

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `initialize` | `InitializeParams` | `InitializeResult` | 进程级握手，配置 cwd/provider/model |
| `session/prompt` | `SessionPromptParams` | `SessionPromptResult` | 入队一个用户消息 |
| `shutdown` | — | `{}` | 处置 agent、适配器和订阅 |

**协议类型**（`sdk/protocol/src/types.ts`）定义了 4 种服务端通知：

| 通知方法 | 载荷 | 触发时机 |
|---------|------|---------|
| `session.event` | `SessionEventNotification` | 会话日志事件记录时 |
| `session.status` | `SessionStatusNotification` | agent 状态变化（idle/running） |
| `subagent.started` | `SubagentStartedNotification` | 子会话创建 |
| `subagent.finished` | `SubagentFinishedNotification` | 子 agent 运行结束 |

### 5.2 认证和授权

**Provider 认证**：
- DeepSeek 适配器：通过 `ctx.credentials` 解析 `CredentialRef`，或从 launch environment 获取
- Pi-AI 适配器：支持三种认证路径——harbor credentials seam、环境变量、pi-ai 自身的 ambient discovery

**凭据引用机制**（`CredentialRef`）：配置中只存储引用名称（如 `DEEPSEEK_API_KEY`），实际密钥在每次请求时解析。

### 5.3 请求验证

**协议传输层**（`sdk/protocol/src/transport.ts`）：

`JsonRpcLineTransport` 实现了换行分隔的 JSON-RPC 2.0：
- 帧分类：有 `id` + `method` 是请求，仅 `id` 是响应，仅 `method` 是通知
- 畸形行静默忽略
- 处理器失败返回 `-32603` 错误

---

## 6. 错误处理体系

### 6.1 错误类型层次

```
Error
  └── HarnessError — 稳定的机器路由 code + cause 链
        └── LlmError — LLM 相关失败，携带 LlmFailure 序列化数据

Error
  └── TransportClosedError — 子进程死亡
  └── RequestTimeoutError — 请求超时
  └── SdkProtocolError — 协议违规
  └── JsonRpcResponseError — JSON-RPC 错误响应
  └── SessionQueryError — 查询错误
```

### 6.2 错误码定义

| 错误码 | 含义 | 可重试 |
|--------|------|--------|
| `AUTH` | 认证失败 (401/403) | 否 |
| `RATE_LIMIT` | 速率限制 (429) | 是 |
| `SERVER` | 服务端错误 (5xx) | 是 |
| `TIMEOUT` | 超时 | 是 |
| `TRANSPORT` | 传输层失败 | 是 |
| `INVALID_REQUEST` | 请求无效 (400/413) | 否 |
| `CONTEXT_WINDOW_EXCEEDED` | 上下文窗口超限 | 否 |
| `QUOTA` | 配额/余额耗尽 | 否 |
| `EMPTY_RESPONSE` | 空响应 | 是 |
| `INVALID_CREDENTIAL` | 凭据格式错误 | 否 |
| `MISSING_CREDENTIAL` | 缺少凭据 | 否 |
| `ABORTED` | 调用者取消 | 否 |
| `STREAM_CLOSED` | 流未正常终止 | 是 |
| `NO_ADAPTER` | 无适配器注册 | 否 |
| `DUPLICATE_ADAPTER` | 路由冲突 | 否 |
| `UNSUPPORTED_REASONING_EFFORT` | 不支持的推理级别 | 否 |
| `UNSUPPORTED_CONTENT` | 不支持的内容类型 | 否 |

### 6.3 错误恢复策略

**适配器边界错误规范化**（`adapter-failure.ts`）：

`normalizeLlmFailure` 处理任意抛出值：
1. 非 Error 值 → 包装为 `HarnessError('UNKNOWN')`
2. 检查 Error 的 `failure` own property（避免 SDK 定义的 getter）
3. 验证 failure 结构的完整性
4. 只信任 Harness 拥有的 code，第三方 SDK code 不进入分类

**上下文窗口检测**（`error.ts`）：`isContextWindowExceededError` 通过正则匹配多种 provider 错误措辞，包括结构化上下文溢出、请求过大措辞、超限措辞等。

**配额检测**（`error.ts`）：`isQuotaExceededError` 匹配 `insufficient_quota`、`quota_exceeded`、`balance_depleted`、`out_of_credits` 等。

**文件 ID 过期恢复**（DeepSeek adapter）：当 provider 拒绝一个文件 ID 时，adapter 使失效的文件映射，最多重试一次（重新上传后重发）。

**Pi-AI 错误分类**（`stream.ts`）：由于 pi-ai 扁平化了原始 Error，适配器通过模式匹配分类，涵盖 AUTH、QUOTA、RATE_LIMIT、INVALID_REQUEST、SERVER、TIMEOUT、TRANSPORT 等。
