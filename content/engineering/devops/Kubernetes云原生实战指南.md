---
title: "Kubernetes云原生实战指南"
tags: []
source: "baike"
source_path: "技术文章 / DevOps与运维"
collected: "2026-09-05"
status: "imported"
---

# Kubernetes云原生实战指南

# Kubernetes云原生实战指南

## 1. 容器基础

### 1.1 Docker原理深度解析

Docker是一个开源的应用容器引擎，它将应用及其所有依赖打包成一个轻量级、可移植的容器。

**Docker架构核心组件：**
- **Docker Client**：用户与Docker交互的命令行工具
- **Docker Daemon**：常驻后台进程，负责构建、运行和分发容器
- **Docker Registry**：存储镜像的仓库（如Docker Hub）

**Docker关键技术原理：**

1. **Namespace隔离**：为容器提供进程、网络、文件系统、用户、主机名等资源的隔离
   - PID Namespace：进程隔离
   - NET Namespace：网络隔离
   - MNT Namespace：文件系统隔离
   - UTS Namespace：主机名隔离
   - IPC Namespace：进程间通信隔离
   - USER Namespace：用户隔离

2. **Cgroups资源限制**：对容器使用的CPU、内存、I/O等资源进行限制和计量

3. **Union FS（联合文件系统）**：分层存储镜像，实现镜像的共享和增量更新

### 1.2 镜像构建最佳实践

**高效Dockerfile编写原则：**

```dockerfile
# 基础镜像选择
FROM node:18-alpine AS base

# 设置工作目录
WORKDIR /app

# 先复制依赖文件，利用构建缓存
COPY package*.json ./

# 安装生产依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 设置环境变量
ENV NODE_ENV=production
ENV PORT=3000

# 创建非root用户
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 && \
    chown -R nextjs:nodejs /app
USER nextjs

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# 启动命令
CMD ["node", "server.js"]
```

### 1.3 多阶段构建实战

多阶段构建可以显著减小最终镜像大小，避免将构建工具和中间文件打包到生产镜像中。

```dockerfile
# 第一阶段：构建
FROM golang:1.21 AS builder

WORKDIR /app

# 先复制go.mod和go.sum下载依赖
COPY go.mod go.sum ./
RUN go mod download

# 复制源代码
COPY . .

# 构建二进制文件
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# 第二阶段：生产环境
FROM alpine:3.18

# 安装必要的运行时依赖
RUN apk --no-cache add ca-certificates tzdata

WORKDIR /root/

# 从构建阶段复制二进制文件
COPY --from=builder /app/main .
COPY --from=builder /app/configs ./configs

# 设置时区
ENV TZ=Asia/Shanghai

# 暴露端口
EXPOSE 8080

# 启动应用
CMD ["./main"]
```

**构建优化技巧：**
1. 合理安排COPY指令顺序，利用构建缓存
2. 使用`.dockerignore`排除不需要的文件
3. 合并RUN指令减少镜像层数
4. 选择合适的基础镜像（Alpine vs Debian vs Ubuntu）
5. 使用多阶段构建分离构建环境和运行环境

## 2. Kubernetes核心概念

### 2.1 Pod - 最小部署单元

Pod是Kubernetes的最小可部署单元，包含一个或多个容器，它们共享网络和存储资源。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: myapp
    version: v1
spec:
  # 初始化容器
  initContainers:
  - name: init-db
    image: busybox:1.36
    command: ['sh', '-c', 'until nslookup mysql-service; do echo waiting for mysql; sleep 2; done;']
    
  # 主容器
  containers:
  - name: main-container
    image: nginx:1.25
    ports:
    - containerPort: 80
    # 资源限制
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
    # 存活探针
    livenessProbe:
      httpGet:
        path: /healthz
        port: 80
      initialDelaySeconds: 3
      periodSeconds: 3
    # 就绪探针
    readinessProbe:
      httpGet:
        path: /ready
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
    # 启动探针
    startupProbe:
      httpGet:
        path: /healthz
        port: 80
      failureThreshold: 30
      periodSeconds: 10
    
  - name: sidecar-container
    image: fluent/fluentd:v1.16
    volumeMounts:
    - name: varlog
      mountPath: /var/log
      
  # 卷定义
  volumes:
  - name: varlog
    emptyDir: {}
```

### 2.2 Deployment - 声明式管理

Deployment提供声明式的更新能力，支持滚动更新、回滚和扩缩容。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deployment
  labels:
    app: myapp
spec:
  replicas: 3
  # 更新策略
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # 滚动更新时最大超出副本数
      maxUnavailable: 0  # 滚动更新时最大不可用副本数
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
        version: v1
    spec:
      containers:
      - name: myapp
        image: myapp:1.0.0
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: myapp-config
        - secretRef:
            name: myapp-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      # 亲和性配置
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - myapp
              topologyKey: kubernetes.io/hostname
      # 容忍度
      tolerations:
      - key: "node-role.kubernetes.io/master"
        operator: "Exists"
        effect: "NoSchedule"
```

### 2.3 StatefulSet - 有状态应用

StatefulSet用于管理有状态应用，提供稳定的网络标识、持久存储和有序部署。

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: "mysql"
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        ports:
        - containerPort: 3306
          name: mysql
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        readinessProbe:
          exec:
            command:
            - mysql
            - -h
            - localhost
            - -u
            - root
            - -p$(MYSQL_ROOT_PASSWORD)
            - -e
            - "SELECT 1"
          initialDelaySeconds: 15
          periodSeconds: 10
  # 持久卷声明模板
  volumeClaimTemplates:
  - metadata:
      name: mysql-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "standard"
      resources:
        requests:
          storage: 20Gi
```

### 2.4 DaemonSet - 节点守护进程

DaemonSet确保所有节点运行特定Pod副本，常用于日志收集、监控代理、存储守护进程等。

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
  labels:
    app: node-exporter
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      hostNetwork: true
      hostPID: true
      containers:
      - name: node-exporter
        image: prom/node-exporter:v1.6.1
        args:
        - --path.procfs=/host/proc
        - --path.sysfs=/host/sys
        - --path.rootfs=/host/root
        - --collector.filesystem.mount-points-exclude=^/(dev|proc|sys|var/lib/docker/.+|var/lib/kubelet/.+)($|/)
        ports:
        - containerPort: 9100
          hostPort: 9100
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "250m"
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
        - name: rootfs
          mountPath: /host/root
          mountPropagation: HostToContainer
          readOnly: true
      tolerations:
      - effect: NoSchedule
        operator: Exists
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
      - name: rootfs
        hostPath:
          path: /
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
```

## 3. 网络模型

### 3.1 Service类型详解

Kubernetes Service提供稳定的网络端点，支持四种类型：

```yaml
# 1. ClusterIP（默认）- 集群内部访问
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP

---

# 2. NodePort - 通过节点端口暴露
apiVersion: v1
kind: Service
metadata:
  name: frontend-nodeport
spec:
  selector:
    app: frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
    nodePort: 30080
  type: NodePort

---

# 3. LoadBalancer - 云负载均衡器
apiVersion: v1
kind: Service
metadata:
  name: web-loadbalancer
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-internal: "false"
spec:
  selector:
    app: web
  ports:
  - protocol: TCP
    port: 443
    targetPort: 8443
  type: LoadBalancer
  externalTrafficPolicy: Cluster

---

# 4. ExternalName - 外部服务CNAME记录
apiVersion: v1
kind: Service
metadata:
  name: external-service
spec:
  type: ExternalName
  externalName: external.example.com
```

### 3.2 Ingress控制器实战

Ingress管理外部访问集群服务的HTTP/HTTPS路由。

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/limit-rps: "10"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - myapp.example.com
    - api.myapp.example.com
    secretName: myapp-tls
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8080
  - host: api.myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port