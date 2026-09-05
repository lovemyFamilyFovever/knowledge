---
title: "DeepSeek Harness 核心架构分析 — 第七部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 核心架构分析 — 第七部分

## 沙箱与安全机制

---

## 26. 沙箱架构总览

### 26.1 子包组成

| 子包 | 职责 |
|---|---|
| `sandbox` | 沙箱服务定义：`SandboxProvider` 抽象类、策略词汇表、升级机制 |
| `sandbox-local` | 本地沙箱实现：Landlock（Linux）、Seatbelt（macOS）、bwrap（Linux） |
| `sandbox-policy` | 沙箱策略解析：会话模式、组合配置 |
| `sandbox-windows-acl` | Windows ACL 受限令牌实现 |

### 26.2 核心抽象

```typescript
abstract class SandboxProvider extends Service {
  abstract confine(argv: readonly string[], policy: SandboxPolicy): ConfinedArgv
}
```

沙箱是 **same-world** 的进程限制能力：共享宿主内核和文件系统。容器、微虚拟机和远程执行通过替换整个能力 seam 实现。

### 26.3 沙箱模式

| 模式 | 说明 |
|---|---|
| `read-only` | 只允许必需的接收器（如 `/dev/null`） |
| `workspace-write` | 允许工作区和后端定义的临时区域写入 |
| `danger-full-access` | 绕过限制（完全访问） |

---

## 27. 策略与执行

### 27.1 SandboxPolicy

```typescript
interface SandboxPolicy extends SandboxExecutionPolicy {
  mode: ConfinedSandboxMode  // 'read-only' | 'workspace-write'
}

interface SandboxExecutionPolicy {
  mode: SandboxMode
  workspaceRoot: string
  sessionId?: SessionId
}
```

策略是 **per-call** 的：两个消费者可以在同一时刻以不同策略限制执行（bash 以 `read-only` 而子 agent 需要其状态目录可写）。

### 27.2 ConfinedArgv

```typescript
interface ConfinedArgv {
  argv: string[]                        // 包装后的 argv
  enforcement: SandboxEnforcement       // 'full' | 'partial'
  denialSignatures: readonly string[]   // 拒绝签名
  runnerFailureRules: readonly RunnerFailureRule[]  // 运行器失败规则
}
```

### 27.3 运行器失败检测

```typescript
interface RunnerFailureRule {
  allowedExitCodes?: readonly number[]
  fatalSignatures: readonly string[]
  informationalLines?: readonly string[]
}
```

检测流程：
1. 应用 `allowedExitCodes`（如果存在）
2. 移除 `informationalLines`（大小写精确匹配）
3. 匹配 `fatalSignatures`（大小写不敏感）
4. 退出状态本身永远不能证明运行器失败

---

## 28. 升级机制（Escalation）

### 28.1 严格更宽表

```typescript
const WIDER_MODES = {
  'read-only': ['workspace-write', 'danger-full-access'],
  'workspace-write': ['danger-full-access'],
}
```

升级只允许向更宽的模式移动，且在执行时检查，不烘焙到工具 schema 中。

### 28.2 升级参数验证

`validateEscalationArgs()` 强制：
- `sandbox_permissions` 和 `justification` 必须同时存在
- `justification` 必须是非空句子

### 28.3 模型面对的标记

```typescript
sandboxDenialMarker(mode)  // "[sandbox: file access denied under {mode} mode]"
escalationHintMarker(subject)  // "[sandbox: escalation available — retry...]"
```

### 28.4 升级审批流程

```typescript
approveEscalation(approval, request)
```

审批流程：
1. 验证升级参数
2. 检查目标模式是否严格更宽
3. 通过 `EscalationApprover.request()` 请求用户审批
4. 返回 `EscalationOutcome`：`allowed-once` | `rejected` | `cancelled` | `unavailable`

---

## 29. 平台实现

### 29.1 Linux

- **Landlock**：内核 ABI，文件系统限制
- **bwrap（Bubblewrap）**：容器化文件系统限制
- **Landlock + bwrap 链**：功能探测仲裁多运行器链

### 29.2 macOS

- **sandbox-exec**：Seatbelt 沙箱

### 29.3 Windows

- **ACL 受限令牌**：每个会话/工作区对的随机私有临时目录和 SID
- 工作区 SID 和常驻授权保持 per-workspace

---

## 30. 安全设计原则

1. **失败关闭**：无后端可用时拒绝运行，不静默通过
2. **Per-call 策略**：策略按调用携带，不固定在提供者上
3. **升级需审批**：更宽的模式需要用户明确批准
4. **拒绝签名隔离**：每个后端有自己的拒绝方言，不使用跨后端联合
5. **运行器失败 vs 拒绝**：运行器失败意味着命令从未运行；拒绝意味着限制工作并阻止了它
