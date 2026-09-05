---
title: "DeepSeek Harness 核心架构分析 — 第七部分：沙箱与安全机制"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 核心架构分析 — 第七部分：沙箱与安全机制
DeepSeek Harness 核心架构分析
第七部分：沙箱与安全机制
26. 沙箱架构总览
26.1 子包组成
子包
职责
sandbox
沙箱服务定义：
SandboxProvider
抽象类、策略词汇表、升级机制
sandbox-local
本地沙箱实现：Landlock（Linux）、Seatbelt（macOS）、bwrap（Linux）
sandbox-policy
沙箱策略解析：会话模式、组合配置
sandbox-windows-acl
Windows ACL 受限令牌实现
26.2 核心抽象
abstract class SandboxProvider extends Service {
  abstract confine(argv: readonly string[], policy: SandboxPolicy): ConfinedArgv
}
沙箱是
same-world
的进程限制能力：共享宿主内核和文件系统。容器、微虚拟机和远程执行通过替换整个能力 seam 实现。
26.3 沙箱模式
模式
说明
read-only
只允许必需的接收器（如
/dev/null
）
workspace-write
允许工作区和后端定义的临时区域写入
danger-full-access
绕过限制（完全访问）
27. 策略与执行
27.1 SandboxPolicy
策略是
per-call
的：两个消费者可以在同一时刻以不同策略限制执行。
interface SandboxPolicy extends SandboxExecutionPolicy {
  mode: ConfinedSandboxMode  // 'read-only' | 'workspace-write'
}
interface SandboxExecutionPolicy {
  mode: SandboxMode
  workspaceRoot: string
  sessionId?: SessionId
}
27.2 ConfinedArgv
interface ConfinedArgv {
  argv: string[]                        // 包装后的 argv
  enforcement: SandboxEnforcement       // 'full' | 'partial'
  denialSignatures: readonly string[]   // 拒绝签名
  runnerFailureRules: readonly RunnerFailureRule[]  // 运行器失败规则
}
28. 升级机制（Escalation）
28.1 严格更宽表
const WIDER_MODES = {
  'read-only': ['workspace-write', 'danger-full-access'],
  'workspace-write': ['danger-full-access'],
}
升级只允许向更宽的模式移动，且在执行时检查，不烘焙到工具 schema 中。
28.2 模型面对的标记
sandboxDenialMarker(mode)
—
[sandbox: file access denied under {mode} mode]
escalationHintMarker(subject)
—
[sandbox: escalation available — retry...]
29. 平台实现
平台
实现
Linux
Landlock + bwrap（Bubblewrap）链
macOS
sandbox-exec（Seatbelt）
Windows
ACL 受限令牌（per-session/per-workspace SID）
30. 安全设计原则
失败关闭
：无后端可用时拒绝运行，不静默通过
Per-call 策略
：策略按调用携带，不固定在提供者上
升级需审批
：更宽的模式需要用户明确批准
拒绝签名隔离
：每个后端有自己的拒绝方言
运行器失败 vs 拒绝
：运行器失败 ≠ 拒绝（限制工作并阻止了命令）
DeepSeek Harness 核心架构分析 — 第七部分 | 生成日期：2026-08-29