---
title: "DeepSeek-Harness 沙箱执行机制深度分析 — 第二部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 沙箱执行机制"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek-Harness 沙箱执行机制深度分析 — 第二部分

## 沙箱执行环境、终端管理与子进程管理

---

## 4. 沙箱执行环境

### 4.1 沙箱的隔离级别

DSH 的沙箱系统定义了三个递进的文件效果模式（`SandboxMode`）：

| 模式 | 含义 | 隔离强度 |
|------|------|----------|
| `read-only` | 仅允许只读文件系统访问（加上 `/dev/null` 等必需的 sink） | 最强 |
| `workspace-write` | 允许对工作区根目录和平台临时目录的写入 | 中等 |
| `danger-full-access` | 绕过所有限制 | 无隔离 |

**关键设计决策**：`read-only` 和 `workspace-write` 是可发送给 provider 的 confining 模式（`ConfinedSandboxMode`），而 `danger-full-access` 的消费者直接 spawn 原始 argv，不调用 `ctx.sandbox`。网络和进程可见性不在这个词汇表中——文件效果是唯一被治理的维度。

**强制执行完整性**分为两种：`full`（后端治理模式承诺的每一个文件效果）和 `partial`（活动后端或旧内核 ABI 仅治理子集）。当前的 partial 场景包括旧版 Landlock ABI 和 Windows ACL runner 的 Everyone/硬链接边界。

**Per-call 策略**（`SandboxExecutionPolicy`）包含 `mode`、`workspaceRoot`（绝对根目录）和可选的 `sessionId`。策略在每次能力调用时解析和携带——两个消费者可以在同一瞬间以不同策略运行（bash 在 `read-only` 下，而一个受限子代理需要其状态目录可写）。

**升级机制**（`escalation.ts`）实现了严格更宽的升级阶梯：`read-only → workspace-write → danger-full-access`。升级请求必须通过 `approveEscalation` 的有序失败关闭序列：严格更宽检查 → 审批服务可用性 → 代理存在性 → 用户审批 → 授予。模型面对的拒绝标记 `[sandbox: file access denied under <mode> mode]` 和升级提示在两个工具家族（bash 和 fs）之间保持一致。

### 4.2 进程隔离机制

`SandboxProvider`（`packages/sandbox/sandbox/src/index.ts`）是抽象的进程沙箱服务。`confine(argv, policy)` 必须返回强制执行的 argv 或在包装/运行器执行时失败关闭——**静默的无限制透传是被禁止的**。

**本地后端的多运行器链**（`LocalSandboxProvider` in `sandbox-local/src/index.ts`）

本地后端根据平台选择运行器链，然后通过功能探测仲裁多个候选者：

| 平台 | 运行器链（优先级从高到低） | 强制执行完整性 |
|------|---------------------------|---------------|
| Linux | `bwrap` → `landlock` | bwrap: full, landlock: full/partial |
| macOS | `seatbelt` | full |
| Windows | `windows-acl` | partial |

**功能探测策略**：单候选者不需要探测（其执行时拒绝仍然是失败关闭的）；多候选者按链顺序探测——第一个通过的被选择。探测是同步的（`spawnSync`），有超时（默认 5 秒），结果被缓存为运行器生命周期。

**Bwrap 配置文件**（`profiles.ts`）：`--ro-bind / /`（整个文件系统只读绑定）+ `--dev /dev` + `--unshare-pid` + `--proc /proc` + `--die-with-parent`。`workspace-write` 模式额外添加 `--tmpfs /tmp` 和 `--bind <workspaceRoot> <workspaceRoot>`。

**Seatbelt 配置文件**：使用 SBPL 语法，`(deny file-write*)` 拒绝所有写入，然后 `(allow file-write* (subpath <root>) ...)` 为可写根添加例外。可写根来自共享的 `writableRoots` 函数——与进程内 fs 栅栏使用同一个函数，确保 bash 和 fs 不会漂移。

**Landlock 配置文件**：使用 `grantArgs` 生成 `--ro <path>` / `--rw <path>` 参数。`read-only` 路径获得读取侧（execute + read_file + read_dir），`read-write` 路径获得所有协商的 ABI 访问。

**Windows ACL**：每个活跃的会话/工作区对获得一个随机的私有临时目录和独立的 SID。工作区写入 SID（`workspaceWriteSid`）是基于规范化工作区路径的 per-WORKSPACE 身份。工作区根 ACE 材料化一次并在 provider 生命周期内持续（跨会话重用缓存）；临时 ACE 在 dispose 时撤销。

**拒绝签名和运行器失败规则**：每个运行器携带自己的拒绝方言（bwrap: `read-only file system`；landlock: `permission denied`；seatbelt: `operation not permitted`；windows-acl: `access is denied`/`access to the path`/`permission denied`）和结构化的运行器失败证据规则。消费者先检查运行器失败（命令没有运行），再检查拒绝（限制工作了并阻止了它）。

### 4.3 资源限制（CPU, 内存, 时间）

沙箱系统本身**不直接限制 CPU 和内存**——它专注于文件系统访问控制。资源限制由以下机制间接提供：

- **执行超时**：由 `@deepseek-ai/dsh-tool-call-timeout-policy` 管理，通过 `spec.signal` 的 `AbortSignal` 传递。
- **Grace 期**：SIGTERM → grace → SIGKILL 的升级链，`graceMs` 是必需的正有限数（不超过 `MAX_TIMER_DELAY_MS`）。
- **输出大小限制**：`OutputCollector` 的 `maxBytes` 和 `maxSpillBytes` 限制命令输出的内存占用。
- **文件读取限制**：`readBytes` 的 `maxBytes` 参数、`READ_LIMIT` 行数限制、`STREAM_MIN_SIZE` 流式阈值。

---

## 5. 终端管理

### 5.1 终端的创建和销毁

终端管理采用三层架构：`TerminalSessionService`（注册表）→ `TerminalBackend`（后端）→ `TerminalBackendSession`（会话）。

**注册表**（`TerminalSessionService` in `packages/terminal/terminal/src/index.ts`）：

- 管理可替换的 PTY 后端和精确 Agent 会话
- 每个会话有精确的所有者（`Agent`），只有所有者可以操作它
- 会话 ID 由注册表铸造（`pty-${++this.nextId}`）
- 后端类型通过 `registerBackend` 注册，一个效果范围内每种类型只能有一个
- 支持命名会话（每个所有者唯一）

**创建流程**（`spawn`）：

1. 断言服务活跃且所有者存活
2. 查找注册的后端
3. 预留名称（防止并发创建同名会话）
4. 预留 spawn（用于在取消时回滚未发布的设置）
5. 调用 `backend.spawn(spec)` 创建未发布的会话
6. 检查取消、服务disposing、所有者存活
7. 发布会话到注册表
8. 返回快照（包含 MOTD）

**销毁流程**：

- **单个销毁**（`kill`）：停止活跃的 send → 调用 `session.close(reason)` → 等待后端清理 → 从注册表删除
- **所有者销毁**（`disposeOwned`）：中止所有待处理的 spawn → 关闭所有属于该所有者的会话
- **全部销毁**（`disposeAll`）：标记 disposing → 中止所有 spawn → 关闭所有会话 → 清理所有后端和所有者清理器

**后端清理错误**（`TerminalBackendCleanupError`）：当 spawn 失败且清理也失败时，报告原始错误和清理错误的聚合。

### 5.2 命令执行流程

`BashTerminalBackend`（`packages/terminal/terminal-bash/src/index.ts`）是本地 shell PTY 后端。

**Spawn 流程**：

1. 检查信号是否已中止
2. 确保沙箱模式栅栏（防止在持久终端会话打开时更改沙箱模式）
3. 解析沙箱策略
4. 构建 spawn argv（如果非 `danger-full-access`，通过 `ctx.sandbox.confine` 包装）
5. 调用 `ctx.subprocess.spawnTerminal` 分配真正的终端
6. 创建 `LocalPtySession` 包装
7. 执行启动会话（bash: `initialize`；pwsh: 循环发送编码前言 + 提示函数，等待受控提示可见）

**环境变量**：终端特定的环境变量在子进程提供者的清理环境基础上叠加：`TERM=dumb`、`PAGER=cat`、`GIT_PAGER=cat`、`DSH_SHELL=1`、`DSH_SESSION_ID`、`DSH_PTY_SESSION_ID`。Bash 额外设置 `PS1`、`PROMPT_COMMAND`（发射 OSC 133;D 标记 + 重新设置 PS1）。

**沙箱模式栅栏**（`ensureSandboxModeFence`）：监听 `session/event` 事件，当检测到 `sandbox/mode` 变更且有活跃的终端会话时抛出错误——防止在终端运行时更改隔离级别。

### 5.3 输出流的捕获和处理

`LocalPtySession`（`packages/terminal/terminal-bash/src/session.ts`）是后端会话的实现。

**输出处理管道**：

1. **node-pty 数据事件** → `onTerminalData`（将 chunk 转为 Buffer 并解码）
2. **TextDecoder 流模式解码** → `onData`
3. **TerminalSanitizer 清理**（移除 ANSI 转义序列，检测提示标记）
4. **滚动缓冲区追加**（`BoundedTextBuffer`，有最大字节数和最大行数限制）
5. **活跃 send 操作追加**（如果有的话）

**BoundedTextBuffer**：尾部保留的有界缓冲区。当超过最大行数时，从头部丢弃行；当超过最大字节数时，使用 `utf8Tail` 从头部裁剪 UTF-8 字符直到满足限制。丢弃时设置 `dropped` 标志。

**提示检测**：通过 TerminalSanitizer 检测 OSC 133;D 标记（`promptSeen`）和受控提示文本（`promptTextSeen`）。提示标记的出现是就绪信号——bash 拥有前台。

**Send 操作生命周期**：

1. **创建**：`startSend` 检查无活跃 send、非关闭/已退出状态
2. **写入**：`beginSend` 检查前台状态 → 写入文本 + 可选的 Enter → 等待写入完成
3. **轮询就绪**：`pollReadiness` 定期检查：
   - 进程是否已退出 → `session_exit`
   - 提示可见 + 前台是 shell + 空闲足够长 → `stdin_read`
   - 精确探测阈值后的 stdin 等待 → `stdin_read`
   - 输出空闲超过 `idleSilenceMs` → `inferred_idle`
4. **超时**：`activeDeadlineTimer` 在 `timeoutMs` 后强制 settle → `timeout`
5. **取消**：发送 SIGINT 到前台进程组 → 恢复轮询

**Scrollback 读取**：`read(request)` 从滚动缓冲区返回有界的分页页面，从最新行反向偏移。

**信号传递**：`signal(signal)` 调用 `terminal.signalForeground(signal)`，后者通过 `ProcessInspector` 信号到验证的前台进程组。

---

## 6. 子进程管理

### 6.1 进程生命周期

`SubprocessRuntime`（`packages/subprocess/subprocess/src/index.ts`）是抽象子进程服务。`LocalSubprocessRuntime`（`subprocess-local/src/index.ts`）是本地实现。

**进程树管理**：

- 每个 spawn 创建一个分离的进程树（POSIX 上 `detached: true` 获得自己的进程组；Windows 上通过 `taskkill /T` 终止）
- `live` Set 追踪所有活跃句柄；`terminals` Set 追踪所有活跃终端
- 正常释放：只有整个树退出后才从 `live` 集合删除（不只是直接子进程的 settlement）

**Spawn 流程**（`spawnSubprocess` in `spawn.ts`）：

1. 验证 `graceMs` 是正有限数
2. 检查信号是否已中止
3. 构建子进程环境（`childEnv`：清理后的父环境 + 显式调用者条目）
4. 根据 stdio 配置创建 `ChildProcess`：stdin 的 `ignore`/`pipe`、stdout 的 `inherit`/`pipe`、stderr 的 `inherit`/`pipe`
5. 设置 collect 模式的 `OutputCollector`
6. 注册 abort 信号监听器（触发 `terminate`）

**环境清理**（`scrubbedParentEnv`）：移除所有匹配 `KEY|PASSWORD|SECRET|TOKEN` 的环境变量和所有 `DSH_*` 前缀的变量。`childEnv` 在此基础上合并调用者的显式环境条目（Windows 上进行大小写不敏感的合并）。

**可执行文件解析**（`resolveExecutable`）：绝对路径直接验证（`stat` + `access X_OK`）；bare PATH 名称遍历 PATH 目录（Windows 上还尝试 PATHEXT 扩展名）；相对路径包含分隔符被拒绝。

### 6.2 信号处理

**终止升级链**（SIGTERM → grace → SIGKILL）：

1. `terminate()` 触发时：
   - 启动树退出观察器（`observeTreeExit`，轮询树存活状态）
   - 发送 SIGTERM 到进程组（POSIX）或 `taskkill /T /F`（Windows）
   - 设置 grace 定时器（`graceMs` 后 SIGKILL）
2. Grace 定时器触发时：
   - 重新检查树存活状态（`treeAlive`）
   - 如果仍存活，发送 SIGKILL

**树存活检测**（`treeAlive`）：
- Windows：检查直接子进程的 `exitCode` 和 `signalCode`
- POSIX：`process.kill(-pid, 0)` 探测进程组；Linux 上还检查 `/proc` 确认非僵尸成员

**进程组信号**（`killGroup`）：`process.kill(-pid, sig)` 发送到负 PID（进程组）。失败被吞没——传递与进程退出竞争。

**Host exit 同步终止**：注册 `process.prependListener('exit', onHostExit)`，在 JavaScript 可观察的退出阶段同步地 SIGKILL 所有仍拥有的进程树。

**Terminal 终止**（`LocalTerminalHandle` in `terminal.ts`）：

采用分层清理策略：
1. **停止后代**：扫描进程树和会话 → SIGTERM → 等待 grace → 再次扫描 → SIGKILL → 等待 grace → 报告存活者
2. **停止 shell**：SIGTERM → 等待 grace → SIGKILL → 等待 grace → 报告失败
3. **再次停止后代**（shell 退出可能释放子进程）
4. **Windows 特殊路径**：使用进程身份（`ProcessIdentity`：pid + started 时间戳）进行精确信号，避免 PID 重用问题

### 6.3 并发控制

**Per-target 锁**（`LocalFileSystem.withLock`）：通过 Promise 链为每个 `targetKey` 提供 FIFO 排他访问。锁在操作完成后自动清理（如果当前 tail 仍然是自己）。

**PTY Send 排他性**：每个 PTY 会话同一时间只能有一个活跃的 send 操作。`startSend` 检查 `active !== undefined` 并抛出 `SEND_ACTIVE` 错误。

**Spawn 预留**（`reserveSpawn`）：在后端 spawn 开始前创建预留，设置 AbortController。如果所有者在 spawn 完成前被销毁，通过 abort 信号取消未发布的设置。

**名称预留**（`reserveName`）：在会话创建期间锁定名称，防止并发创建同名会话。

**输出收集器的线程安全**：`OutputCollector` 的 `push` 操作是同步的（Node.js 单线程模型保证），但 `readFrom` 使用偏移量坐标确保增量读取的一致性。

**树退出观察器**：`observeTreeExit` 返回共享的 Promise——多个调用者等待同一个观察，避免重复的进程表扫描。

**进程身份验证**（`ProcessIdentity`）：每个追踪的进程携带 `pid` + `started` 时间戳。信号前重新检查身份——PID 重用后不会误信号无关进程。后代采用（`descendants()`）只在根 PID 仍然携带启动身份时进行。
