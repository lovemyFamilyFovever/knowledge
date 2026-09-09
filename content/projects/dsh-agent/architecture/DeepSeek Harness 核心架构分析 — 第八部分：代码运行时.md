---
title: "DeepSeek Harness 核心架构分析 — 第八部分：代码运行时"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 核心架构分析

第八部分：代码运行时（Code Runtime）

## 31. Code Runtime 架构

### 31.1 子包组成

| 子包 | 职责 |
| --- | --- |
| `code-runtime` | 服务定义：`CodeRuntime` 抽象类、绑定词汇表、可移植标识符规则 |
| `code-runtime-worker-thread` | TypeScript Worker Thread 实现 |
| `code-runtime-python` | Python 运行时实现 |

### 31.2 核心抽象

```
abstract class CodeRuntime extends Service {
  abstract readonly language: string    // 'typescript' | 'python'
  abstract readonly isolation: string   // 'worker-thread' | 'process' | 'container'
  abstract run(request: CodeRunRequest): Promise<CodeRunResult>
}
```

## 32. 执行模型

### 32.1 CodeRunRequest

```
interface CodeRunRequest {
  program: string           // 源代码（作为 async 函数体运行）
  bindings: CodeBindingNamespace[]  // 暴露给程序的宿主函数
  signal?: AbortSignal      // 中止运行
}
```

程序作为 async 函数体运行：顶层 await 和 return 可用。

### 32.2 失败分类

| 类型 | 说明 |
| --- | --- |
| `exception` | 程序抛出或解析/转换失败 |
| `timeout` | 实现拥有的预算到期 |
| `abort` | `signal` 触发 |
| `worker-exit` | 执行基底死亡（如 OOM） |
| `invalid-output` | 完成值不是 lossless JSON |
| `output-limit` | 序列化输出超过配置上限 |

## 33. Worker Thread 实现

### 33.1 配置

| 参数 | 说明 |
| --- | --- |
| `computeMs` | 忙碌时间预算（事件循环活跃时间） |
| `maxWallMs` | 墙钟上限 |
| `maxOutputBytes` | 输出字节上限 |
| `maxOldGenerationSizeMb` | 堆上限（MiB） |

### 33.2 类型剥离

程序被包装为 async function __dsh_program__() { ... }，然后通过 stripTypeScriptTypes() 剥离类型。剥离模式是位置保持的。

## 34. 可移植标识符规则

全局标识符必须匹配 [A-Za-z_][A-Za-z0-9_]*，且不能是 ECMAScript ∪ Python 的保留字联合集。一个在 TypeScript 后端有效的命名空间列表在 Python 后端也有效。

## 35. Code Mode 集成

- 模型只能调用 `run_code` 工具

- 其他工具通过 SDK 在程序内部调用

- 子调度通过 `TOOL_RUNTIME_SCHEDULER` 接口

- 每个子调度记录为 `tool/code-dispatch-start` 和 `tool/code-dispatch` 事件

## 36. 安全模型

- **包含而非安全边界**：Worker Thread 是包含，不是安全边界

- **空环境**：模型代码具有 bash 等效信任

- **预算限制**：忙碌时间、墙钟、输出字节、堆大小

- **中止能力**：`signal` 可以停止程序（甚至中循环）

- **隔离**：每次运行独立的 worker，不共享状态

DeepSeek Harness 核心架构分析 — 第八部分 | 生成日期：2026-08-29
