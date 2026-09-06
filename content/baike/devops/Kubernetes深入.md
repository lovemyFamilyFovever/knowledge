---
title: "Kubernetes深入"
tags: []
source: "baike"
source_path: "开发术语 / DevOps与云原生"
collected: "2026-09-05"
status: "imported"
---

# Kubernetes深入

## Kubernetes (K8s)

**一句话定义：** K8s是容器编排平台，自动管理容器的部署、扩缩容和运维。

**通俗类比：** 如果Docker容器是标准化的集装箱，K8s就是自动化港口管理系统——自动决定每个集装箱放在哪艘船上、坏了自动替换、忙时自动增加船只。

### 核心概念

| 概念 | 说明 |
|------|------|
| Pod | 最小部署单元，包含一个或多个容器 |
| Service | 稳定的网络入口，负载均衡 |
| Deployment | 管理Pod的副本数和滚动更新 |
| ConfigMap/Secret | 配置和敏感数据 |
| Ingress | 外部流量入口 |
| Namespace | 资源隔离 |

### Deployment示例

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: myapp:1.0
        ports:
        - containerPort: 5000
        resources:
          requests:
            memory: "128Mi"
            cpu: "250m"
          limits:
            memory: "256Mi"
            cpu: "500m"
```

### 常用命令

```bash
kubectl get pods                    # 查看Pod
kubectl get services                # 查看Service
kubectl describe pod <name>         # 详细信息
kubectl logs <pod-name>             # 查看日志
kubectl exec -it <pod> -- bash      # 进入Pod
kubectl scale deployment web --replicas=5  # 扩缩容
kubectl rollout restart deploy/web  # 滚动重启
```

### 服务发现与负载均衡

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

Service自动在匹配的Pod之间负载均衡。

### 健康检查

```yaml
livenessProbe:    # 存活检查：失败则重启容器
  httpGet:
    path: /health
    port: 5000
  periodSeconds: 10

readinessProbe:   # 就绪检查：失败则从Service移除
  httpGet:
    path: /ready
    port: 5000
```
