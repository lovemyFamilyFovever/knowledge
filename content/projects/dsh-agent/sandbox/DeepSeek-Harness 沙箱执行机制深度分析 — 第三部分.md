---
title: "DeepSeek-Harness 沙箱执行机制深度分析 — 第三部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 沙箱执行机制"
collected: "2026-09-05"
status: "imported"
---

DeepSeek-Harness 沙箱执行机制深度分析 — 第三部分
☰
目录导航
第三部分
7. Landlock 安全机制
7.1 Landlock 是什么
7.2 在 DSH 中的应用
7.3 文件系统访问控制
8. 安全模型总结
8.1 多层防御策略
8.2 权限最小化原则
8.3 已知安全边界
9. 改进建议和最佳实践
9.1 安全增强建议
9.2 架构改进建议
9.3 最佳实践
DeepSeek-Harness 沙箱执行机制深度分析
第三部分：Landlock 安全机制、安全模型总结与改进建议
全部报告：
第一部分
|
第二部分
|
第三部分
7. Landlock 安全机制
7.1 Landlock 是什么
Landlock 是 Linux 内核自 5.13 版本起引入的一个
安全模块（LSM）
，提供无需特权的文件系统访问控制。关键特性：
非特权使用
：任何进程都可以对自己的子进程施加文件系统限制，无需 root 权限
可叠加性
：多个规则集可以叠加，后续规则集只能进一步收紧权限
继承性
：通过
execve
继承——限制传播到所有子进程
允许列表模型
：未明确授予的访问被拒绝
无容器依赖
：独立的系统调用族，不需要用户命名空间或挂载命名空间
Landlock ABI 版本
ABI
新增访问位
ABI 1
execute, write_file, read_file, read_dir, remove_dir, remove_file, make_*, 等 13 个位
ABI 2
refer
（跨目录移动/链接）
ABI 3
truncate
ABI 4
仅 TCP 相关位
ABI 5
ioctl_dev
DSH 的
landlock-run
启动器通过
LANDLOCK_CREATE_RULESET_VERSION
系统调用协商运行内核的 ABI，然后将规则集缩小到内核支持的范围。
7.2 在 DSH 中的应用
native/landlock-run/
是一个独立的 C11 启动器程序，作为 Linux 沙箱运行器链中的第二选择（bwrap 优先）。
两层包架构
入口包
（
@deepseek-ai/node-addon-landlock-run
）：ESM JavaScript，拥有 CLI 合约——路径解析、功能探测、授权参数构建
平台包
（
@deepseek-ai/node-addon-landlock-run-linux-{x64,arm64}
）：预构建的静态二进制文件（musl-gcc 编译，无 libc 依赖）
CLI 合约
landlock-run [--ro <path>]... [--rw <path>]... -- <argv>...
landlock-run --probe
C 实现流程
ABI 协商
：调用
landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION)
获取内核支持的 ABI 版本
规则集创建
：根据协商的 ABI 构建
handled_access_fs
位掩码
规则添加
：
--ro
路径添加只读规则（execute + read_file + read_dir），
--rw
路径添加完全访问规则
no_new_privs
设置
：
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)
——中和 setuid/setgid 提升
限制自身
：
landlock_restrict_self(ruleset_fd, 0)
将规则集应用到当前线程
执行命令
：
execvp(cli.command[0], cli.command)
——规则集通过 execve 继承
失败关闭设计
：如果规则集无法创建或未被内核强制执行，启动器以退出码 125 退出，
不执行命令
。部分强制执行（旧 ABI）在 stderr 上报告但接受。
7.3 文件系统访问控制
沙箱配置文件
read-only 模式
：
--ro / --rw /dev/null
（整个文件系统只读 +
/dev/null
可写）
workspace-write 模式
：
--ro / --rw /dev/null --rw /tmp --rw <workspaceRoot>
与 bwrap 的差异
：Landlock 使用标志授予（
--ro
/
--rw
），无法创建新的
/tmp
；bwrap 使用挂载绑定（
--tmpfs /tmp
），可以创建全新的空
/tmp
，隔离性更强。
8. 安全模型总结
8.1 多层防御策略
DSH 的安全模型采用深度防御策略，在多个层面实现隔离：
5
升级审批 (approveEscalation)
严格更宽检查 + 用户审批 + 失败关闭
4
文件系统策略 (dsh-fs-sandbox)
进程内路径包含检查 + FS_SANDBOX_DENIED
3
观察策略 (dsh-fs-observation-policy)
读前写/编辑 + 过期保护 + 版本守卫
2
进程沙箱 (dsh-sandbox-local)
bwrap / Landlock / Seatbelt / windows-acl 运行器
1
原子操作 (dsh-fs-local)
暂存-发布 + per-target 锁 + 行尾规范化
8.2 权限最小化原则
环境清理
：
scrubbedParentEnv
移除所有凭据相关和
DSH_*
环境变量
Landlock 的
no_new_privs
：中和沙箱内的 setuid/setgid 提升
Bwrap 的
--die-with-parent
：父进程退出时终止所有沙箱内进程
进程身份验证
：
ProcessIdentity
（pid + started）防止 PID 重用误信号
Per-session 隔离
（Windows ACL）：每个会话获得随机私有临时目录和独立 SID
文件写入权限
：新文件
0o600
，暂存目录
0o700
，spill 文件使用
O_EXCL
+ 随机后缀
8.3 已知安全边界
1. 进程内文件系统栅栏不是安全边界
SandboxedFileSystem
是受信任代码中的策略检查，不是内核级隔离。残留的 TOCTOU 窗口虽然被缩小，但在此威胁模型中被接受。
2. Windows ACL 的部分强制执行
WRITE_RESTRICTED
需要 Everyone 在限制列表中；NTFS 硬链接可以别名文件。Windows 报告
partial
强制执行完整性。
3. Landlock 旧 ABI 的部分强制执行
ABI 2 之前没有
refer
位（跨目录
rename
不受控制）；ABI 3 之前没有
truncate
位。
4. 网络和进程可见性不在治理范围
SandboxMode
只治理文件系统效果。网络访问和进程可见性不在词汇表中。
9. 改进建议和最佳实践
9.1 安全增强建议
安全
网络隔离
增加可选的网络隔离：Linux 使用
bwrap --unshare-net
或 Landlock ABI 4+ TCP 限制；macOS 在 Seatbelt 中添加网络拒绝
安全
资源限制集成
在沙箱策略中集成 CPU 时间、内存、进程数量和文件描述符限制（通过 cgroup v2 或 setrlimit）
增强
Landlock ABI 版本报告
增加具体的 ABI 版本号报告，让消费者可以做出更精确的决策，而非仅 full/partial/unusable
增强
进程内栅栏的内核备份
为文件系统操作添加可选的内核级备份（例如通过 seccomp-bpf 过滤 open/openat 系统调用的路径参数）
9.2 架构改进建议
架构
沙箱配置文件热重载
支持运行时调整沙箱策略而无需重启，允许配置文件的热重载
架构
运行器性能基准
增加运行器性能基准，自动选择最快的可用运行器而非固定的优先级链
架构
跨平台一致性测试
增加跨平台一致性测试套件，确保 bwrap、Landlock、Seatbelt 和 windows-acl 行为一致
架构
沙箱审计日志
增加可选的沙箱审计日志，记录所有被拒绝的文件访问尝试，用于安全分析和调试
9.3 最佳实践
始终使用
read-only
作为默认模式
——除非明确需要写入，否则应最小化攻击面
使用
workspace-write
而非
danger-full-access
——即使需要写入，也应限制写入范围
定期审查升级请求
——异常频繁的升级可能表明策略配置不当
保持内核更新
——建议使用 ABI 3+ 的内核以获得
truncate
控制
测试沙箱边界
——定期尝试绕过限制，确保安全模型按预期工作
监控强制执行完整性
——对于
partial
环境，明确记录哪些访问不受控制
← 上一部分：沙箱执行环境、终端管理
DeepSeek-Harness 沙箱执行机制深度分析 — 第三部分 | 基于源码分析生成
↑