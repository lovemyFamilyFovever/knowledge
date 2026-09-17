---
title: "DeepSeek-Harness 沙箱执行机制深度分析 — 第三部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 沙箱执行机制"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek-Harness 沙箱执行机制深度分析 — 第三部分

## Landlock 安全机制、安全模型总结与改进建议

---

## 7. Landlock 安全机制

### 7.1 Landlock 是什么

Landlock 是 Linux 内核自 5.13 版本起引入的一个**安全模块（LSM）**，提供无需特权的文件系统访问控制。与传统的 seccomp-bpf 或 SELinux 不同，Landlock 的关键特性包括：

- **非特权使用**：任何进程都可以对自己的子进程施加文件系统限制，无需 root 权限或 CAP_SYS_ADMIN。
- **可叠加性**：多个 Landlock 规则集可以叠加，后续规则集只能进一步收紧权限，不能放松。
- **继承性**：通过 `execve` 继承——一旦进程被限制，其所有子进程（包括 exec 的新程序）都受到同样的限制。
- **允许列表模型**：Landlock 规则集是允许列表——未明确授予的访问被拒绝。
- **无容器依赖**：不需要用户命名空间、挂载命名空间或任何容器技术——独立的系统调用族。

**Landlock ABI 版本**：随着内核演进，Landlock 引入了新的文件系统访问位：

| ABI | 新增访问位 |
|-----|-----------|
| ABI 1 | execute, write_file, read_file, read_dir, remove_dir, remove_file, make_*, 等 13 个位 |
| ABI 2 | refer（跨目录移动/链接） |
| ABI 3 | truncate |
| ABI 4 | 仅 TCP 相关位 |
| ABI 5 | ioctl_dev |

DSH 的 `landlock-run` 启动器通过 `LANDLOCK_CREATE_RULESET_VERSION` 系统调用协商运行内核的 ABI，然后将规则集缩小到内核支持的范围。旧 ABI 意味着部分强制执行——例如 ABI 2 之前没有 `refer` 位，跨目录的 `rename` 不受控制。

### 7.2 在 DSH 中的应用

`native/landlock-run/` 是一个独立的 C11 启动器程序，作为 Linux 沙箱运行器链中的第二选择（bwrap 优先）。

**架构**（`docs/architecture.md`）：

启动器采用两层包模型：
- **入口包**（`@deepseek-ai/node-addon-landlock-run`）：ESM JavaScript，拥有 CLI 合约——路径解析、功能探测、授权参数构建。
- **平台包**（`@deepseek-ai/node-addon-landlock-run-linux-{x64,arm64}`）：预构建的静态二进制文件（musl-gcc 编译，无 libc 依赖），npm 的 `os`/`cpu` 字段在安装时选择匹配的包。

**CLI 合约**：

```
landlock-run [--ro <path>]... [--rw <path>]... -- <argv>...
landlock-run --probe
```

- `--ro` 授予路径下的读+执行权限
- `--rw` 授予路径下的完全文件系统访问权限
- 未授予的一切被拒绝（Landlock 是允许列表）
- `--probe` 构建并强制执行最大规则集，报告内核是否实际强制执行

**C 实现细节**（`main.c`）：

1. **ABI 协商**：调用 `landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION)` 获取内核支持的 ABI 版本。
2. **规则集创建**：根据协商的 ABI 构建 `handled_access_fs` 位掩码。
3. **规则添加**：对每个 `--ro` 路径添加只读规则（execute + read_file + read_dir），对每个 `--rw` 路径添加完全访问规则。
4. **`no_new_privs` 设置**：`prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)` ——必须在 `landlock_restrict_self` 之前设置，同时中和沙箱内的 setuid/setgid 提升。
5. **限制自身**：`landlock_restrict_self(ruleset_fd, 0)` 将规则集应用到当前线程。
6. **执行命令**：`execvp(cli.command[0], cli.command)` ——规则集通过 execve 继承。

**失败关闭设计**：如果规则集无法创建或未被内核强制执行，启动器以退出码 125 退出，**不执行命令**。部分强制执行（旧 ABI）在 stderr 上报告，但接受——消费者根据 ABI 级别决定其模式词汇承诺什么。

**功能探测**（`--probe`）：在短命子进程中构建并强制执行最大规则集，然后报告强制执行状态。退出 0 且输出包含 `partially enforced` 则为 `partial`；退出 0 且无该标记则为 `full`；退出非 0 则为 `unusable`。

### 7.3 文件系统访问控制

**授权参数构建**（`grantArgs` in `index.ts`）：

```typescript
export function grantArgs(grants: LauncherGrants): string[] {
  return [
    ...(grants.readOnly ?? []).flatMap(root => ['--ro', root]),
    ...(grants.readWrite ?? []).flatMap(root => ['--rw', root]),
  ]
}
```

**沙箱配置文件**（`landlockProfileArgs` in `profiles.ts`）：

```typescript
export function landlockProfileArgs(policy: SandboxPolicy): string[] {
  const readWrite = ['/dev/null']
  if (policy.mode === 'workspace-write') {
    readWrite.push('/tmp', policy.workspaceRoot)
  }
  return landlockGrantArgs({ readOnly: ['/'], readWrite })
}
```

这意味着：
- `read-only` 模式：`--ro / --rw /dev/null`（整个文件系统只读 + `/dev/null` 可写）
- `workspace-write` 模式：`--ro / --rw /dev/null --rw /tmp --rw <workspaceRoot>`

**与 bwrap 的差异**：Landlock 使用标志授予（`--ro`/`--rw`），bwrap 使用挂载绑定（`--ro-bind`/`--bind`/`--tmpfs`）。Landlock 无法创建新的 `/tmp`（它是标志，不是挂载），所以 `workspace-write` 模式授予现有 `/tmp` 的写入权限。bwrap 可以用 `--tmpfs /tmp` 创建全新的空 `/tmp`，隔离性更强。

**拒绝方言**：Landlock 拒绝文件访问时返回 `EACCES`（`permission denied`），而 bwrap 返回 `EROFS`（`read-only file system`），seatbelt 返回 `EPERM`（`operation not permitted`）。消费者使用运行器特定的拒绝签名来分类。

---

## 8. 安全模型总结

### 8.1 多层防御策略

DSH 的安全模型采用深度防御策略，在多个层面实现隔离：

```
┌─────────────────────────────────────────────────┐
│ Layer 5: 升级审批 (approveEscalation)           │
│   严格更宽检查 + 用户审批 + 失败关闭             │
├─────────────────────────────────────────────────┤
│ Layer 4: 文件系统策略 (dsh-fs-sandbox)          │
│   进程内路径包含检查 + FS_SANDBOX_DENIED         │
├─────────────────────────────────────────────────┤
│ Layer 3: 观察策略 (dsh-fs-observation-policy)   │
│   读前写/编辑 + 过期保护 + 版本守卫              │
├─────────────────────────────────────────────────┤
│ Layer 2: 进程沙箱 (dsh-sandbox-local)           │
│   bwrap/Landlock/Seatbelt/windows-acl 运行器     │
├─────────────────────────────────────────────────┤
│ Layer 1: 原子操作 (dsh-fs-local)                │
│   暂存-发布 + per-target 锁 + 行尾规范化         │
└─────────────────────────────────────────────────┘
```

**Layer 1 — 原子操作**：`writeFileAtomic` 通过暂存目录 + 独占创建 + 原子 rename 确保写入的原子性。per-target 锁确保并发编辑的确定性排序。行尾规范化确保跨平台的一致性。

**Layer 2 — 进程沙箱**：`ctx.sandbox.confine(argv, policy)` 将命令包装在平台特定的沙箱运行器中。功能探测确保运行器可用；失败关闭确保不可用时不透传。

**Layer 3 — 观察策略**：`dsh-fs-observation-policy` 通过 `fs/*` 事件记录文件的观察状态（present/absent），强制执行读前写/编辑的默认行为。未观察的文件不能被编辑（`FS_NOT_OBSERVED`），过期的版本不能被替换（`FS_STALE_VERSION`）。

**Layer 4 — 文件系统策略**：`SandboxedFileSystem` 在每次写入/编辑前检查目标路径是否在允许的可写根下。使用 `isPathUnder` 进行词法快速路径 + 文件系统身份回退的包含检查。`read-only` 模式拒绝所有突变。

**Layer 5 — 升级审批**：`approveEscalation` 实现了严格的升级序列：验证请求的模式严格更宽于当前模式 → 确认审批服务可用 → 确认代理存在 → 发送审批请求给用户 → 根据结果授予或拒绝。

### 8.2 权限最小化原则

DSH 在多个维度体现了权限最小化原则：

**环境清理**：`scrubbedParentEnv` 移除所有 `KEY|PASSWORD|SECRET|TOKEN` 匹配的环境变量和所有 `DSH_*` 前缀的变量。子进程不会隐式继承宿主的凭据。

**Landlock 的 `no_new_privs`**：启动器在限制自身前设置 `PR_SET_NO_NEW_PRIVS`，中和沙箱内的 setuid/setgid 提升。

**Bwrap 的 `--die-with-parent`**：父进程退出时，沙箱内的所有进程也被终止——防止孤儿进程。

**进程身份验证**：`ProcessIdentity`（pid + started 时间戳）确保信号不会误发给 PID 重用后的无关进程。

**Per-session 隔离**（Windows ACL）：每个活跃的会话/工作区对获得一个随机的私有临时目录和独立的 SID。临时 ACE 在 dispose 时撤销。

**文件写入权限**：新文件使用 `0o600`（仅所有者读写），暂存目录使用 `0o700`。Spill 文件使用 `O_EXCL` + 随机后缀 + 0o600，防止路径预测和符号链接攻击。

**命名空间隔离**：bwrap 使用 `--unshare-pid` + `--proc /proc` 提供进程可见性隔离。

### 8.3 已知安全边界

DSH 的安全模型有几个已知的边界和限制：

**1. 进程内文件系统栅栏不是安全边界**

`SandboxedFileSystem` 的注释明确说明："This fence is a policy check in TRUSTED code over a MODEL-CONTROLLED path, NOT a kernel boundary." 包含检查在受信任代码中运行，只验证模型控制的路径——它不是内核级的隔离。残留的 TOCTOU（祖先符号链接在包含检查和系统调用之间被交换）被通过在委托前重新规范化来缩小，但在此威胁模型中被接受。

**2. Windows ACL 的部分强制执行**

- `WRITE_RESTRICTED` 需要 Everyone 在限制列表中——外部授予 Everyone 写入权限的对象仍然可写。
- NTFS 硬链接可以将一个工作区文件别名到工作区外的路径。
- 因此 Windows 报告 `partial` 强制执行完整性。

**3. Landlock 旧 ABI 的部分强制执行**

- ABI 2 之前没有 `refer` 位——跨目录的 `rename` 不受控制。
- ABI 3 之前没有 `truncate` 位。
- 启动器在 stderr 上报告 `partial enforcement (older Landlock ABI)`。

**4. 网络和进程可见性不在治理范围**

`SandboxMode` 只治理文件系统效果。网络访问和进程可见性不在词汇表中——一个 `read-only` 沙箱中的进程仍然可以进行网络请求和查看其他进程。

**5. 终端模式的沙箱限制**

`ensureSandboxModeFence` 防止在持久终端会话打开时更改沙箱模式，但不防止终端内的进程访问网络或进行其他非文件系统操作。

**6. 符号链接攻击的缓解**

- `resolve` 使用 realpath 解析符号链接
- `isPathUnder` 在词法检查失败后使用文件系统身份（dev:ino）回退
- `writeFileAtomic` 使用 `open('wx')` 防止符号链接竞态
- `lstat` 允许在 resolve 之前检测符号链接
- 但 TOCTOU 窗口仍然存在（虽然被缩小）

---

## 9. 改进建议和最佳实践

### 9.1 安全增强建议

**1. 网络隔离**

当前的沙箱模式不治理网络访问。建议增加可选的网络隔离：
- Linux：使用 `bwrap --unshare-net` 或 Landlock ABI 4+ 的 TCP 限制
- macOS：在 Seatbelt 配置文件中添加网络拒绝
- Windows：使用 Windows 防火墙 API 或进程令牌的网络限制

**2. 资源限制集成**

建议在沙箱策略中集成显式的资源限制：
- CPU 时间限制（`setrlimit` 或 cgroup）
- 内存限制（cgroup v2 memory.max）
- 进程数量限制（cgroup v2 pids.max）
- 文件描述符限制

**3. Landlock ABI 版本报告**

当前 `probe()` 只报告 `full`/`partial`/`unusable`。建议增加具体的 ABI 版本号报告，让消费者可以做出更精确的决策。

**4. 进程内栅栏的内核备份**

虽然 `SandboxedFileSystem` 不是安全边界，但可以在进程内栅栏之外，为文件系统操作添加一层可选的内核级备份（例如通过 seccomp-bpf 过滤 `open`/`openat` 系统调用的路径参数）。

### 9.2 架构改进建议

**1. 沙箱配置文件的热重载**

当前的运行器链在 provider 生命周期内缓存。建议支持配置文件的热重载，允许在运行时调整沙箱策略而无需重启。

**2. 运行器性能基准**

功能探测是同步的（`spawnSync`），有超时。建议增加运行器性能基准，自动选择最快的可用运行器。

**3. 跨平台一致性测试**

建议增加跨平台的一致性测试套件，确保 bwrap、Landlock、Seatbelt 和 windows-acl 在相同策略下的行为一致。

**4. 沙箱审计日志**

建议增加可选的沙箱审计日志，记录所有被拒绝的文件访问尝试，用于安全分析和调试。

### 9.3 最佳实践

**1. 始终使用 `read-only` 作为默认模式**

除非明确需要写入，否则应使用 `read-only` 模式。这最小化了攻击面。

**2. 使用 `workspace-write` 而非 `danger-full-access`**

即使需要写入，也应使用 `workspace-write` 限制写入范围，而非完全开放。

**3. 定期审查升级请求**

升级请求（`sandbox_permissions` + `justification`）应被记录和审查。异常频繁的升级可能表明策略配置不当。

**4. 保持内核更新**

较新的 Landlock ABI 提供更完整的文件系统访问控制。建议使用 ABI 3+ 的内核以获得 `truncate` 控制。

**5. 测试沙箱边界**

定期测试沙箱边界——尝试访问工作区外的文件、创建符号链接到受限区域、使用硬链接绕过限制等——确保安全模型按预期工作。

**6. 监控强制执行完整性**

对于报告 `partial` 强制执行的环境，应明确记录和理解哪些访问不受控制，并评估风险。
