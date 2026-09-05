---
title: "DeepSeek Harness 核心架构分析 — 第八部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 核心架构分析 — 第八部分

## 代码运行时（Code Runtime）

---

## 31. Code Runtime 架构

### 31.1 子包组成

| 子包 | 职责 |
|---|---|
| `code-runtime` | 服务定义：`CodeRuntime` 抽象类、绑定词汇表、可移植标识符规则 |
| `code-runtime-worker-thread` | TypeScript Worker Thread 实现 |
| `code-runtime-python` | Python 运行时实现 |

### 31.2 核心抽象

```typescript
abstract class CodeRuntime extends Service {
  abstract readonly language: string    // 'typescript' | 'python'
  abstract readonly isolation: string   // 'worker-thread' | 'process' | 'container'
  abstract run(request: CodeRunRequest): Promise<CodeRunResult>
}
```

运行时对工具和会话一无所知；消费者拥有这些关注点。

### 31.3 绑定模型

```typescript
interface CodeBindingNamespace {
  global: string                              // 全局标识符
  functions: Record<string, CodeBindingFunction>  // 可调用成员
  errorClass?: CodeBindingErrorClass          // 可选的拒绝契约
}
```

绑定是 **structured-cloneable** 的：运行时跨序列化边界桥接调用。

---

## 32. 执行模型

### 32.1 CodeRunRequest

```typescript
interface CodeRunRequest {
  program: string           // 源代码（作为 async 函数体运行）
  bindings: CodeBindingNamespace[]  // 暴露给程序的宿主函数
  signal?: AbortSignal      // 中止运行
}
```

程序作为 async 函数体运行：顶层 `await` 和 `return` 可用，完成值成为 `CodeRunResult.value`。

### 32.2 CodeRunResult

```typescript
interface CodeRunResult {
  value?: CodeJsonValue     // 程序的完成值
  logs: string[]            // 程序发出的文本，按顺序
  error?: CodeRunFailure    // 失败（如果有）
}
```

**关键设计**：错误是结果的字段，永远不是 `run()` 的拒绝——报告失败的程序是调用者的工作，不是异常路径。

### 32.3 失败分类

| 类型 | 说明 |
|---|---|
| `exception` | 程序抛出或解析/转换失败 |
| `timeout` | 实现拥有的预算到期 |
| `abort` | `signal` 触发 |
| `worker-exit` | 执行基底死亡（如 OOM） |
| `invalid-output` | 完成值不是 lossless JSON |
| `output-limit` | 序列化的外部日志/值/诊断超过配置上限 |

---

## 33. Worker Thread 实现

### 33.1 配置

```typescript
interface Config {
  computeMs?: number           // 忙碌时间预算（毫秒）
  maxWallMs?: number           // 墙钟上限（毫秒）
  maxOutputBytes?: number      // 输出字节上限
  maxOldGenerationSizeMb?: number  // 堆上限（MiB）
}
```

### 33.2 资源限制

- **忙碌时间预算**：通过 `worker.performance.eventLoopUtilization()` 测量的事件循环活跃时间
- **墙钟上限**：从不暂停的后备（程序等待无人会 resolve 的 promise 时）
- **输出限制**：序列化的日志数组、完成值和失败消息的硬上限
- **堆限制**：`resourceLimits`，溢出杀死 worker

### 33.3 类型剥离

程序被包装为 `async function __dsh_program__() { ... }`，然后通过 `stripTypeScriptTypes()` 剥离类型。剥离模式是位置保持的（移除的语法变为空白，什么都不移动）。

### 33.4 轮询机制

```typescript
const ELU_POLL_INTERVAL_MS = 25  // 事件循环利用率轮询间隔
```

主机每 25ms 采样一次 worker 的事件循环利用率，用于 `computeMs` 预算。

---

## 34. 可移植标识符规则

### 34.1 全局标识符

`CodeBindingNamespace.global` 必须匹配 `[A-Za-z_][A-Za-z0-9_]*`，且不能是任何语言的保留字。

### 34.2 保留绑定全局

```typescript
RESERVED_BINDING_GLOBALS = new Set([
  'console',
  '__dsh_main__', '__builtins__', '__name__', '__debug__',
])
```

### 34.3 保留错误成员

```typescript
RESERVED_ERROR_MEMBERS = new Set([
  'name', 'message', 'stack',
  'args', 'with_traceback', 'add_note',
])
```

### 34.4 可移植保留字

ECMAScript ∪ Python 的保留字联合集——一个在 TypeScript 后端有效的命名空间列表在 Python 后端也有效。

---

## 35. Code Mode 集成

Code Mode 通过 `run_code` 工具暴露给模型：

1. 模型只能调用 `run_code` 工具
2. 其他工具通过 SDK 在程序内部调用
3. 子调度通过 `TOOL_RUNTIME_SCHEDULER` 接口
4. 每个子调度记录为 `tool/code-dispatch-start` 和 `tool/code-dispatch` 事件

---

## 36. 安全模型

- **包含而非安全边界**：Worker Thread 是包含，不是安全边界
- **空环境**：模型代码具有 bash 等效信任
- **预算限制**：忙碌时间、墙钟、输出字节、堆大小
- **中止能力**：`signal` 可以停止程序（甚至中循环）
- **隔离**：每次运行独立的 worker，不共享状态
