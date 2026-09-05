---
title: "Docker容器化完全指南"
tags: []
source: "baike"
source_path: "技术文章 / DevOps与运维"
collected: "2026-09-05"
status: "imported"
---

# Docker容器化完全指南

# Docker容器化完全指南

## 1. 容器vs虚拟机

### 1.1 架构差异深度解析

**传统虚拟机架构**：
- 包含完整的操作系统（Guest OS）
- 通过Hypervisor（如VMware、VirtualBox）进行硬件模拟
- 每个虚拟机都是完全独立的系统环境

**容器架构**：
- 共享宿主机操作系统内核
- 通过容器运行时（如containerd、runc）管理
- 使用操作系统级虚拟化技术

### 1.2 核心技术原理

#### 1.2.1 Linux Namespaces（命名空间）

Namespace是容器隔离的核心技术，提供6种隔离类型：

```c
// 查看当前系统的namespace支持情况
cat /proc/version
ls -la /proc/1/ns/
```

**6种Namespace详解**：

1. **PID Namespace**：进程ID隔离
```bash
# 使用nsenter进入容器的PID namespace
nsenter -t <PID> -p -m
```

2. **NET Namespace**：网络栈隔离
```bash
# 查看网络namespace
ip netns list
# 创建新的网络namespace
ip netns add mynet
```

3. **MNT Namespace**：文件系统挂载点隔离
```bash
# 使用unshare创建隔离环境
unshare --mount --uts --ipc --net --pid --fork /bin/bash
```

4. **UTS Namespace**：主机名和域名隔离
```bash
# 查看主机名隔离
hostnamectl set-hostname container1
```

5. **IPC Namespace**：进程间通信隔离

6. **USER Namespace**：用户和组ID隔离

#### 1.2.2 Control Groups (Cgroups)

Cgroups是资源限制的核心机制：

```bash
# 查看cgroup挂载点
mount -t cgroup
# 查看cgroup层次结构
systemd-cgls

# cgroup目录结构
/sys/fs/cgroup/
├── cpu/
├── memory/
├── blkio/
├── pids/
└── devices/
```

**CPU限制示例**：
```bash
# 创建cgroup
mkdir /sys/fs/cgroup/cpu/my_container

# 设置CPU配额（每100ms使用50ms CPU）
echo 50000 > /sys/fs/cgroup/cpu/my_container/cpu.cfs_quota_us
echo 100000 > /sys/fs/cgroup/cpu/my_container/cpu.cfs_period_us

# 将进程加入cgroup
echo <PID> > /sys/fs/cgroup/cpu/my_container/tasks
```

**内存限制示例**：
```bash
# 设置内存限制为256MB
echo 268435456 > /sys/fs/cgroup/memory/my_container/memory.limit_in_bytes

# 设置内存+swap限制
echo 536870912 > /sys/fs/cgroup/memory/my_container/memory.memsw.limit_in_bytes
```

#### 1.2.3 UnionFS（联合文件系统）

UnionFS是镜像分层存储的核心：

**OverlayFS结构**：
```
lowerdir (只读层)
├── base_image_layer
├── added_files_layer
└── ...
upperdir (可写层) - 容器运行时修改
merged (合并视图) - 最终呈现给用户
workdir (工作目录)
```

**查看镜像层**：
```bash
docker inspect --format='{{json .GraphDriver}}' <image_id>

# 使用docker history查看构建历史
docker history --no-trunc nginx:latest
```

**OverlayFS内部实现**：
```c
// 简化的OverlayFS数据结构
struct overlayfs_entry {
    struct inode *lower_inode;    // 只读层
    struct inode *upper_inode;    // 可写层
    struct inode *work_inode;     // 工作层
    struct dentry *dentry;        // 合并后条目
};

// 写时复制(Copy-on-Write)机制
static int overlayfs_write(struct file *file, const char __user *buf, size_t len, loff_t *ppos) {
    // 检查是否首次写入
    if (!file->f_inode->i_private) {
        // 复制文件到upper层
        copy_up_file(lower_inode, upper_inode);
    }
    // 写入upper层
    return vfs_write(upper_file, buf, len, ppos);
}
```

### 1.3 性能对比测试

```bash
# 启动时间对比
time docker run --rm alpine echo "hello"
# 典型结果：0.5-2秒

time qemu-system-x86_64 -m 512 -hda vm.qcow2 -daemonize
# 典型结果：10-30秒

# 资源开销对比
docker stats --no-stream
# 容器额外内存开销：几MB
# 虚拟机额外内存开销：几百MB
```

## 2. 镜像构建

### 2.1 Dockerfile最佳实践

#### 2.1.1 基础镜像选择

```dockerfile
# 不好的做法 - 使用完整版镜像
FROM python:3.9

# 好的做法 - 使用精简版镜像
FROM python:3.9-slim

# 更好 - 使用Alpine镜像（注意兼容性）
FROM python:3.9-alpine

# 多阶段构建专用基础镜像
FROM golang:1.19-alpine AS builder
```

#### 2.1.2 层优化策略

```dockerfile
# 不好的做法 - 多个RUN指令
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y wget

# 好的做法 - 合并RUN指令并清理缓存
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 使用.dockerignore文件
# .dockerignore
.git
node_modules
*.log
```

#### 2.1.3 安全最佳实践

```dockerfile
# 创建非root用户
RUN addgroup -S appgroup && \
    adduser -S appuser -G appgroup

# 设置工作目录
WORKDIR /app

# 复制应用文件并设置权限
COPY --chown=appuser:appgroup . .

# 切换用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8080/health || exit 1

# 使用exec形式避免shell注入
CMD ["node", "server.js"]
```

### 2.2 多阶段构建实战

#### 2.2.1 Go应用多阶段构建

```dockerfile
# 第一阶段：构建
FROM golang:1.19-alpine AS builder

# 安装必要工具
RUN apk add --no-cache git

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /app .

# 第二阶段：生产镜像
FROM scratch

# 从构建阶段复制二进制文件
COPY --from=builder /app /app

# 复制必要的配置文件
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

EXPOSE 8080
ENTRYPOINT ["/app"]
```

#### 2.2.2 前端应用多阶段构建

```dockerfile
# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 从构建阶段复制构建产物
COPY --from=builder /app/build /usr/share/nginx/html

# 自定义nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 2.3 镜像瘦身技巧

#### 2.3.1 分析镜像大小

```bash
# 安装分析工具
docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    wagoodman/dive <image_name>

# 使用docker-slim优化
docker-slim build --http-probe=false <image_name>
```

#### 2.3.2 静态二进制编译

```bash
# Go静态编译
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -ldflags='-extldflags "-static"' -o app .

# Rust静态编译
RUSTFLAGS='-C target-feature=+crt-static' cargo build --release --target x86_64-unknown-linux-gnu
```

#### 2.3.3 使用distroless镜像

```dockerfile
# 不使用Alpine，使用Google的distroless镜像
FROM gcr.io/distroless/static

COPY --from=builder /app /app
ENTRYPOINT ["/app"]
```

## 3. 容器网络

### 3.1 Bridge网络（默认）

```bash
# 查看bridge网络
docker network inspect bridge

# 创建自定义bridge网络
docker network create --driver bridge \
    --subnet 192.168.100.0/24 \
    --gateway 192.168.100.1 \
    my_bridge

# 连接容器到自定义网络
docker run --network my_bridge --name container1 alpine
docker run --network my_bridge --name container2 alpine

# 容器间通信（通过容器名）
docker exec container1 ping container2
```

### 3.2 Host网络

```bash
# 使用host网络模式
docker run --network host nginx

# 验证网络栈共享
docker exec <container> netstat -tlnp
# 看到与宿主机相同的网络接口
```

### 3.3 None网络

```bash
# 创建没有网络的容器
docker run --network none --name isolated alpine

# 查看网络接口
docker exec isolated ip a
# 只有loopback接口
```

### 3.4 Overlay网络（跨主机）

```bash
# 初始化Docker Swarm
docker swarm init

# 创建overlay网络
docker network create --driver overlay \
    --attachable \
    my_overlay

# 在不同主机上启动容器
docker service create --name web --network my_overlay nginx

# 测试跨主机通信
docker exec -it <container_id> ping <other_container_id>
```

### 3.5 Macvlan网络

```bash
# 创建macvlan网络
docker network create --driver macvlan \
    --subnet 10.0.0.0/24 \
    --gateway 10.0.0.1 \
    -o parent=eth0 \
    macvlan_net

# 创建具有独立IP的容器
docker run --network macvlan_net \
    --ip 10.0.0.100 \
    --name macvlan_container \
    -d nginx

# 验证MAC地址独立性
docker exec macvlan_container ip link show eth0
# 显示独立的MAC地址
```

### 3.6 网络调试工具

```bash
# 网络连通性测试
docker run --rm -it alpine ping <target>
docker run --rm -it nicolaka/netshoot

# 端口监听检查
docker run --rm -it nicolaka/netshoot ss -tlnp

# 网络抓包
docker run --rm -it --net container:<container_name> nicolaka/netshoot tcpdump -i eth0
```

## 4. 数据管理

### 4.1 Volume（卷）

```bash
# 创建命名卷
docker volume create my_data

# 查看卷详情
docker volume inspect my_data

# 使用卷启动容器
docker run -d \
    --name postgres \
    -v my_data:/var/lib/postgresql/data \
    postgres:14

# 备份卷数据
docker run --rm \
    -v my_data:/source:ro \
    -v $(pwd):/backup \
    alpine tar czf /backup/my_data_backup.tar.gz -C /source .

# 恢复卷数据
docker run --rm \
    -v my_data:/target \
    -v $(pwd):/backup \
    alpine sh -c "cd /target && tar xzf /backup/my_data_backup.tar.gz"
```

### 4.2 Bind Mount（绑定挂载）

```bash
# 开发环境使用bind mount
docker run -d \
    --name dev_app \
    -v $(pwd)/app:/app:rw \
    -v $(pwd)/config:/config:ro \
    node:18-alpine \
    sh -c "cd /app && npm install && node server.js"

# 权限问题解决
docker run -d \
    --name secure_app \
    -v $(pwd)/app:/app:rw \
    --user $(id -u):$(id -g) \
    node:18-alpine

# 使用selinux标签
docker run -d \
    --name selinux_app \
    -v $(pwd)/app:/app:Z \
    nginx
```

### 4.3 tmpfs挂载

```bash
# 创建tmpfs挂载
docker run -d \
    --name tmpfs_example \
    --tmpfs /tmp:rw,size=100m,mode=1777 \
    --tmpfs /run:rw,size=50m \
    redis

# 查看tmpfs挂载
docker exec tmpfs_example df -h | grep tmpfs
```

### 4.4 数据持久化策略

```yaml
# docker-compose.yml数据管理示例
version: '3.8'

services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data  # 命名卷
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro  # 绑定挂载
    tmpfs:
      - /run/postgresql:size=50m  # tmpfs

  cache:
    image: redis:alpine
    volumes:
      - redis_data:/data
    tmpfs:
      - /tmp:size=10m

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=10.0.0.1,rw
      device: ":/data/postgres"
  
  redis_data:
    driver: local
```

## 5. Docker Compose编排

### 5.1 完整应用编排示例

```yaml
version: '3.8'

services:
  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://api:8080
    depends_on:
      - api
    networks:
      - frontend_net
    restart: unless-stopped

  # API服务
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=app_user
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - REDIS_URL=redis://cache:6379
    depends_on:
      postgres:
        condition: service_healthy
      cache:
        condition: service_started
    secrets:
      - db_password
    networks:
      - frontend_net
      - backend_net
    restart: unless-stopped

  # 数据库
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=app_db
      - POSTGRES_USER_FILE=/run/secrets/postgres_user
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
    secrets:
      - postgres_user
      - postgres_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - backend_net
    restart: unless-stopped

  # 缓存
  cache:
    image: redis:alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - backend_net
    restart: unless-stopped

  # 消息队列
  rabbitmq:
    image: rabbitmq:3-management
    environment:
      - RABBITMQ_DEFAULT_USER_FILE=/run/secrets/rabbitmq_user
      - RABBITMQ_DEFAULT_PASS_FILE=/run/secrets/rabbitmq_password
    secrets:
      - rabbitmq_user
      - rabbitmq_password
    ports:
      - "15672:15672"  # 管理界面
      - "5672:5672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - backend_net
    restart: unless-stopped

# 网络配置
networks:
  frontend_net:
    driver: bridge
  backend_net:
    driver: bridge
    internal: true  # 内部网络，不对外暴露

# 卷配置
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  rabbitmq_data:
    driver: local

# 密钥管理
secrets:
  postgres_user:
    file: ./secrets/postgres_user.txt
  postgres_password:
    file: ./secrets/postgres_password.txt
  db_password:
    file: ./secrets/db_password.txt
  redis_password:
    environment: REDIS_PASSWORD
  rabbitmq_user:
    file: ./secrets/rabbitmq_user.txt
  rabbitmq_password:
    file: ./secrets/rabbitmq_password.txt
```

### 5.2 开发环境配置

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
      - "9229:9229"  # Node.js调试端口
    environment:
      - NODE_ENV=development
    command: npm start

  api:
    build:
      context: ./api
      dockerfile: Dockerfile.dev
    volumes:
      - ./api:/app
      - /app/node_modules
    ports:
      - "8080:8080"
      - "9228:9228"
    environment:
      - NODE_ENV=development
      - DEBUG=app:*
    command: npm run dev
```

### 5.3 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f --tail=100 api

# 扩展服务副本
docker-compose up -d --scale api=3

# 进入容器调试
docker-compose exec api bash

# 构建并启动
docker-compose up --build -d

# 清理停止的容器
docker-compose down --volumes --remove-orphans
```

## 6. Docker安全

### 6.1 Root权限控制

```bash
# 以非root用户运行容器
docker run --user 1000:1000 -d nginx

# Dockerfile中创建用户
FROM node:18-alpine

RUN addgroup -S appgroup && \
    adduser -S appuser -G appgroup -h /home/appuser

USER appuser
WORKDIR /home/appuser/app

COPY --chown=appuser:appgroup . .

CMD ["node", "server.js"]

# 检查容器内用户
docker exec <container> whoami
```

### 6.2 Seccomp配置

```json
// custom-seccomp.json
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": [
        "SCMP_ARCH_X86_64",
        "SCMP_ARCH_X86",
        "SCMP_ARCH_AARCH64"
    ],
    "syscalls": [
        {
            "names": [
                "accept",
                "accept4",
                "access",
                "alarm",
                "bind",
                "brk",
                "chdir",
                "chmod",
                "clock_getres",
                "clock_gettime",
                "clock_nanosleep",
                "close",
                "connect",
                "dup",
                "dup2",
                "dup3",
                "epoll_create",
                "epoll_create1",
                "epoll_ctl",
                "epoll_pwait",
                "epoll_wait",
                "execve",
                "exit",
                "exit_group",
                "fchmod",
                "fchown",
                "fcntl",
                "fstat",
                "fsync",
                "ftruncate",
                "futex",
                "getdents",
                "getdents64",
                "getegid",
                "geteuid",
                "getgid",
                "getgroups",
                "getpid",
                "getppid",
                "getsockname",
                "getsockopt",
                "getuid",
                "ioctl",
                "kill",
                "listen",
                "lseek",
                "madvise",
                "mmap",
                "mprotect",
                "munmap",
                "nanosleep",
                "newfstatat",
                "open",
                "openat",
                "pause",
                "pipe",
                "pipe2",
                "poll",
                "prctl",
                "pread64",
                "prlimit64",
                "pwrite64",
                "read",
                "readlink",
                "recvfrom",
                "recvmsg",
                "rename",
                "renameat",
                "restart_syscall",
                "rt_sigaction",
                "rt_sigpending",
                "rt_sigprocmask",
                "rt_sigqueueinfo",
                "rt_sigreturn",
                "rt_sigsuspend",
                "rt_sigtimedwait",
                "sched_yield",
                "select",
                "sendmsg",
                "sendto",
                "set_robust_list",
                "set_tid_address",
                "setsockopt",
                "shutdown",
                "sigaltstack",
                "socket",
                "stat",
                "statfs",
                "tgkill",
                "umask",
                "uname",
                "unlink",
                "wait4",
                "write",
                "writev"
            ],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
```

使用Seccomp配置：
```bash
docker run --security-opt seccomp=custom-seccomp.json nginx
```

### 6.3 AppArmor配置

```yaml
#include <tunables/global>

profile docker-custom flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # 网络访问
  network inet stream,
  network inet dgram,
  network inet6 stream,
  network inet6 dgram,

  # 文件系统访问
  / r,
  /** r,
  /tmp/** rw,
  /var/log/** rw,
  /app/** rw,

  # 拒绝访问敏感文件
  deny /etc/shadow rw,
  deny /etc/passwd rw,
  deny /root/** rw,

  # 信号
  signal (receive) peer=unconfined,
  signal (send,receive) peer=docker-custom,

  # 挂载
  mount options=(ro,remount),
  umount,
}
```

使用AppArmor配置：
```bash
# 加载AppArmor配置
sudo apparmor_parser -r docker-custom

# 运行容器
docker run --security-opt apparmor=docker-custom nginx
```

### 6.4 镜像扫描

```bash
# 使用Trivy扫描镜像
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image nginx:latest

# 使用Docker Scan
docker scan nginx:latest

# 使用Clair扫描
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    quay.io/coreos/clair-scanner:latest \
    --ip="192.168.1.1" nginx:latest

# 漏洞扫描报告
docker scan --json nginx:latest | jq '.vulnerabilities[] | {id, package, severity}'
```

### 6.5 安全最佳实践总结

1. **最小权限原则**：使用非root用户运行
2. **只读文件系统**：`--read-only`标志
3. **资源限制**：CPU、内存、PID限制
4. **网络隔离**：使用内部网络
5. **镜像扫描**：定期扫描漏洞
6. **使用secrets管理**：Docker secrets或外部密钥管理
7. **定期更新**：保持Docker和镜像更新

## 7. 私有镜像仓库（Harbor）

### 7.1 Harbor安装配置

```bash
# 下载Harbor离线安装包
wget https://github.com/goharbor/harbor/releases/download/v2.6.0/harbor-offline-installer-v2.6.0.tgz

# 解压安装包
tar xvf harbor-offline-installer-v2.6.0.tgz
cd harbor

# 复制配置文件
cp harbor.yml.tmpl harbor.yml

# 编辑配置
vi harbor.yml
```

### 7.2 Harbor配置示例

```yaml
# harbor.yml
hostname: harbor.example.com

# HTTP配置
http:
  port: 80

# HTTPS配置（推荐）
https:
  port: 443
  certificate: /data/cert/server.crt
  private_key: /data/cert/server.key

# 管理员密码
harbor_admin_password: Harbor12345

# 数据库配置
database:
  password: root123
  max_idle_conns: 100
  max_open_conns: 900

# 数据卷目录
data_volume: /data

# 存储配置
storage_service:
  s3:
    accesskey: AKIAIOSFODNN7EXAMPLE
    secretkey: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    region: us-east-1
    bucket: harbor-registry

# 邮件配置
email_identity: 
email_server: smtp.example.com
email_server_port: 25
email_username: user@example.com
email_password: abc123
email_from: admin <admin@example.com>
email_ssl: false
email_insecure: false

# 日志配置
log:
  level: info
  local:
    rotate_count: 50
    rotate_size: 200M
    location: /var/log/harbor
```

### 7.3 安装和启动

```bash
# 安装Harbor
sudo ./install.sh --with-trivy --with-chartmuseum

# 启动所有服务
docker-compose -f docker-compose.yml up -d

# 查看服务状态
docker-compose -f docker-compose.yml ps

# 管理Harbor
docker-compose -f docker-compose.yml down  # 停止
docker-compose -f docker-compose.yml restart  # 重启
```

### 7.4 Harbor使用

```bash
# 登录Harbor
docker login harbor.example.com

# 推送镜像
docker tag nginx:latest harbor.example.com/myproject/nginx:1.0
docker push harbor.example.com/myproject/nginx:1.0

# 拉取镜像
docker pull harbor.example.com/myproject/nginx:1.0

# 配置Docker daemon信任Harbor
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp ca.crt /etc/docker/certs.d/harbor.example.com/

# 重启Docker服务
sudo systemctl restart docker
```

### 7.5 Harbor高可用架构

```yaml
# harbor-ha.yml (示例)
version: '3.8'

services:
  harbor-core:
    image: goharbor/harbor-core:v2.6.0
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.role == worker
    environment:
      - CORE_SECRET=secret123
      - DATABASE_TYPE=postgresql
      - DATABASE_HOST=harbor-db
      - DATABASE_PORT=5432
      - DATABASE_USERNAME=harbor
      - DATABASE_PASSWORD=harbor123
    networks:
      - harbor_net
    volumes:
      - core_data:/data

  harbor-portal:
    image: goharbor/harbor-portal:v2.6.0
    deploy:
      replicas: 2
    networks:
      - harbor_net

  harbor-db:
    image: goharbor/harbor-db:v2.6.0
    deploy:
      placement:
        constraints:
          - node.labels.db == true
    environment:
      - POSTGRES_PASSWORD=harbor123
      - POSTGRES_USER=harbor
      - POSTGRES_DB=registry
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - harbor_net

  redis:
    image: redis:alpine
    deploy:
      placement:
        constraints:
          - node.labels.cache == true
    networks:
      - harbor_net

networks:
  harbor_net:
    driver: overlay
    attachable: true

volumes:
  core_data:
    driver: local
  db_data:
    driver: local
```

## 8. 容器日志管理

### 8.1 日志驱动选择

```bash
# 查看可用日志驱动
docker info | grep "Logging Driver"

# 日志驱动类型
# 1. json-file（默认）
# 2. syslog
# 3. journald
# 4. gelf
# 5. fluentd
# 6. awslogs
# 7. splunk
# 8. etwlogs
# 9. gcplogs
# 10. logentries
```

### 8.2 日志配置示例

```yaml
# docker-compose.yml日志配置
version: '3.8'

services:
  app:
    image: nginx
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service,status"
        env: "os,customer"
        compress: "true"

  api:
    image: node:18-alpine
    logging:
      driver: "fluentd"
      options:
        fluentd-address: localhost:24224
        tag: "docker.{{.Name}}"

  db:
    image: postgres:14
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://192.168.1.100:514"
        syslog-facility: "local0"
        tag: "postgres"
```

### 8.3 集中式日志收集

#### 8.3.1 EFK架构（Elasticsearch + Fluentd + Kibana）

```yaml
# docker-compose.efk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - logging_net

  fluentd:
    image: fluent/fluentd:v1.15-1
    volumes:
      - ./fluentd/conf:/fluentd/etc
    ports:
      - "24224:24224"
      - "24224:24224/udp"
    depends_on:
      - elasticsearch
    networks:
      - logging_net

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - logging_net

  # 应用服务
  web:
    image: nginx
    logging:
      driver: "fluentd"
      options:
        fluentd-address: localhost:24224
        tag: "docker.web"
    depends_on:
      - fluentd

networks:
  logging_net:
    driver: bridge

volumes:
  elasticsearch_data:
    driver: local
```

#### 8.3.2 Fluentd配置

```xml
# fluentd/conf/fluent.conf
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match docker.**>
  @type elasticsearch
  host elasticsearch
  port 9200