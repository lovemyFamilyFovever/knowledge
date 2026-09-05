---
title: "DeepSeek-Harness 沙箱执行机制深度分析 — 第二部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 沙箱执行机制"
collected: "2026-09-05"
status: "imported"
---

DeepSeek-Harness 沙箱执行机制深度分析 — 第二部分
目录导航
第二部分
4. 沙箱执行环境
4.1 沙箱的隔离级别
4.2 进程隔离机制
4.3 资源限制
5. 终端管理
5.1 终端的创建和销毁
5.2 命令执行流程
5.3 输出流的捕获和处理
6. 子进程管理
6.1 进程生命周期
6.2 信号处理
6.3 并发控制
DeepSeek-Harness 沙箱执行机制深度分析
第二部分：沙箱执行环境、终端管理与子进程管理
全部报告：
第一部分
|
第二部分
|
第三部分
4. 沙箱执行环境
4.1 沙箱的隔离级别
DSH 的沙箱系统定义了三个递进的文件效果模式（
SandboxMode
）：
read-only
最强隔离
仅允许只读文件系统访问（加上
/dev/null
等必需的 sink）
workspace-write
中等隔离
允许对工作区根目录和平台临时目录的写入
danger-full-access
无隔离
绕过所有限制，直接 spawn 原始 argv
关键设计决策
：
read-only
和
workspace-write
是可发送给 provider 的 confining 模式（
ConfinedSandboxMode
），而
danger-full-access
的消费者直接 spawn 原始 argv，不调用
ctx.sandbox
。网络和进程可见性不在这个词汇表中。
Per-call 策略
SandboxExecutionPolicy
包含
mode
、
workspaceRoot
（绝对根目录）和可选的
sessionId
。策略在每次能力调用时解析和携带——两个消费者可以在同一瞬间以不同策略运行。
升级机制
实现了严格更宽的升级阶梯：
read-only
→
workspace-write
→
danger-full-access
升级请求通过
approveEscalation
的有序失败关闭序列：严格更宽检查 → 审批服务可用性 → 代理存在性 → 用户审批 → 授予。模型面对的拒绝标记
[sandbox: file access denied under <mode> mode]
和升级提示在 bash 和 fs 之间保持一致。
4.2 进程隔离机制
SandboxProvider
（
packages/sandbox/sandbox/src/index.ts
）是抽象的进程沙箱服务。
confine(argv, policy)
必须返回强制执行的 argv 或失败关闭——
静默的无限制透传是被禁止的
。
本地后端的多运行器链
平台
运行器链
强制执行完整性
Linux
bwrap
→
landlock
bwrap:
full
, landlock:
full/partial
macOS
seatbelt
full
Windows
windows-acl
partial
功能探测策略
：单候选者不需要探测（其执行时拒绝仍然是失败关闭的）；多候选者按链顺序探测——第一个通过的被选择。探测是同步的（
spawnSync
），有超时（默认 5 秒），结果被缓存。
Bwrap 配置文件
--ro-bind / /
（整个文件系统只读绑定）+
--dev /dev
+
--unshare-pid
+
--proc /proc
+
--die-with-parent
。
workspace-write
模式额外添加
--tmpfs /tmp
和
--bind <workspaceRoot> <workspaceRoot>
。
Seatbelt 配置文件
使用 SBPL 语法：
(deny file-write*)
拒绝所有写入，然后
(allow file-write* (subpath <root>) ...)
为可写根添加例外。可写根来自共享的
writableRoots
函数——与进程内 fs 栅栏使用同一个函数。
拒绝签名和运行器失败规则
每个运行器携带自己的拒绝方言和结构化的运行器失败证据规则：
bwrap
：
read-only file system
landlock
：
permission denied
seatbelt
：
operation not permitted
windows-acl
：
access is denied
/
access to the path
/
permission denied
消费者先检查运行器失败（命令没有运行），再检查拒绝（限制工作了并阻止了它）。
4.3 资源限制
沙箱系统本身
不直接限制 CPU 和内存
——它专注于文件系统访问控制。资源限制由以下机制间接提供：
执行超时
：由
@deepseek-ai/dsh-tool-call-timeout-policy
管理
Grace 期
：SIGTERM → grace → SIGKILL 的升级链
输出大小限制
：
OutputCollector
的
maxBytes
和
maxSpillBytes
文件读取限制
：
readBytes
的
maxBytes
、
READ_LIMIT
行数、
STREAM_MIN_SIZE
流式阈值
5. 终端管理
5.1 终端的创建和销毁
终端管理采用三层架构：
TerminalSessionService
注册表
→
TerminalBackend
后端
→
TerminalBackendSession
会话
注册表特性
每个会话有精确的所有者（
Agent
），只有所有者可以操作它
会话 ID 由注册表铸造（
pty-${++this.nextId}
）
支持命名会话（每个所有者唯一）
后端类型通过
registerBackend
注册
创建流程
断言服务活跃且所有者存活
查找注册的后端
预留名称（防止并发创建同名会话）
预留 spawn（用于在取消时回滚未发布的设置）
调用
backend.spawn(spec)
创建未发布的会话
检查取消、服务disposing、所有者存活
发布会话到注册表
返回快照（包含 MOTD）
销毁策略
单个销毁
（
kill
）：停止活跃 send →
session.close(reason)
→ 等待后端清理 → 从注册表删除
所有者销毁
（
disposeOwned
）：中止所有待处理 spawn → 关闭所有属于该所有者的会话
全部销毁
（
disposeAll
）：标记 disposing → 中止所有 spawn → 关闭所有会话 → 清理所有后端和所有者清理器
5.2 命令执行流程
BashTerminalBackend
（
packages/terminal/terminal-bash/src/index.ts
）是本地 shell PTY 后端。
Spawn 流程
检查信号是否已中止
确保沙箱模式栅栏（防止在持久终端会话打开时更改沙箱模式）
解析沙箱策略
构建 spawn argv（非
danger-full-access
时通过
ctx.sandbox.confine
包装）
调用
ctx.subprocess.spawnTerminal
分配真正的终端
创建
LocalPtySession
包装
执行启动会话（bash:
initialize
；pwsh: 循环发送编码前言 + 提示函数，等待受控提示可见）
沙箱模式栅栏
ensureSandboxModeFence
监听
session/event
事件，当检测到
sandbox/mode
变更且有活跃的终端会话时抛出错误——防止在终端运行时更改隔离级别。
5.3 输出流的捕获和处理
输出处理管道
node-pty 数据事件
→
TextDecoder 流解码
→
TerminalSanitizer 清理
→
BoundedTextBuffer
→
活跃 Send 操作
BoundedTextBuffer
：尾部保留的有界缓冲区。超过最大行数时从头部丢弃行；超过最大字节数时使用
utf8Tail
从头部裁剪 UTF-8 字符。
Send 操作生命周期
创建
：
startSend
检查无活跃 send、非关闭/已退出状态
写入
：检查前台状态 → 写入文本 + 可选 Enter → 等待写入完成
轮询就绪
：定期检查进程退出/提示可见/空闲时间/精确探测
超时
：
timeoutMs
后强制 settle
取消
：发送 SIGINT 到前台进程组 → 恢复轮询
6. 子进程管理
6.1 进程生命周期
LocalSubprocessRuntime
管理分离的进程树。每个 spawn 创建一个分离的进程树（POSIX 上
detached: true
获得自己的进程组；Windows 上通过
taskkill /T
终止）。
环境清理
scrubbedParentEnv
移除所有匹配
KEY|PASSWORD|SECRET|TOKEN
的环境变量和所有
DSH_*
前缀的变量。
childEnv
在此基础上合并调用者的显式环境条目。
可执行文件解析
绝对路径：直接验证（
stat
+
access X_OK
）
bare PATH 名称：遍历 PATH 目录（Windows 上还尝试 PATHEXT 扩展名）
相对路径包含分隔符：被拒绝
输出收集器（OutputCollector）
尾部保留的有界内存缓冲，配合溢出到磁盘的 spill 文件：
内存内保留最后
maxBytes
字节的尾部
首次溢出时创建 spill 文件（
O_EXCL
+ 0o600 权限 + 随机后缀）
readFrom(fromByte)
增量读取：偏移量已在内存窗口外时报告
lossy
seal()
关闭 spill 文件；
finalize()
返回最终输出
6.2 信号处理
终止升级链
SIGTERM
→ grace期 →
SIGKILL
terminate()
触发时：启动树退出观察器 → 发送 SIGTERM 到进程组 → 设置 grace 定时器
Grace 定时器触发时：重新检查树存活状态 → 如果仍存活，发送 SIGKILL
树存活检测
Windows
：检查直接子进程的
exitCode
和
signalCode
POSIX
：
process.kill(-pid, 0)
探测进程组；Linux 上还检查
/proc
确认非僵尸成员
Terminal 终止
采用分层清理策略：
停止后代
：扫描进程树和会话 → SIGTERM → 等待 grace → 再次扫描 → SIGKILL → 等待 grace
停止 shell
：SIGTERM → 等待 grace → SIGKILL → 等待 grace
再次停止后代
（shell 退出可能释放子进程）
6.3 并发控制
Per-target 锁
：
withLock(targetKey, op)
通过 Promise 链提供 FIFO 排他访问
PTY Send 排他性
：每个会话同一时间只能有一个活跃 send
Spawn 预留
：在后端 spawn 开始前创建预留，设置 AbortController
名称预留
：在会话创建期间锁定名称
进程身份验证
：每个追踪的进程携带
pid
+
started
时间戳，信号前重新检查身份
进程身份验证（ProcessIdentity）
：每个追踪的进程携带
pid
+
started
时间戳。信号前重新检查身份——PID 重用后不会误信号无关进程。后代采用只在根 PID 仍然携带启动身份时进行。
← 上一部分：文件系统抽象层
下一部分：Landlock 与安全模型 →
DeepSeek-Harness 沙箱执行机制深度分析 — 第二部分 | 基于源码分析生成
▲