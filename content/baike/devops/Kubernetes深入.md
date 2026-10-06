---
title: "Kubernetes深入"
tags: []
source: "baike"
source_path: "开发术语 / DevOps与云原生"
collected: "2026-09-05"
status: "imported"
---

# Kubernetes深入

> 📌 **导航**：本文是 **Kubernetes深入** 词条，属于 devops 术语集。相关枢纽：[[Docker容器化完全指南]]、[[Kubernetes云原生实战指南]]、[[Kubernetes深入]]、[[Web安全攻防实战指南]]、[[云服务详解]]。

## 定义

**一句话定义：** Kubernetes（K8s）是容器编排平台，自动管理跨主机容器的部署、扩缩容、自愈与运维。

**通俗类比：** 如果 Docker 容器是标准化集装箱，K8s 就是自动化港口调度系统——决定每个箱子放哪条船、坏了自动换、忙时自动加船。

## 为什么需要它

单个 Docker 只能管一台机器上的容器。当规模涨到几十上百个容器、跨多台主机时，谁来决定容器调度到哪台机器、实例挂了谁重启、流量变了谁扩容、版本升级怎么不停机？这些"编排"问题手工做不可持续。K8s 用声明式 API 把这些交给控制面自动收敛：你只描述期望状态，它负责让现实逼近期望。

## 核心能力

控制面由 API Server（唯一入口）、Scheduler（调度）、etcd（状态存储）、Controller Manager（调和循环）组成；工作负载与网络能力落在以下抽象上：

| 概念 | 作用 |
|------|------|
| Pod | 最小部署单元，可含多个共享网络的容器 |
| Service | 为一组 Pod 提供稳定入口与负载均衡 |
| Deployment | 声明式管理副本数与滚动更新 |
| ConfigMap / Secret | 配置与敏感数据 |
| Ingress | 外部 HTTP 流量入口 |
| Namespace | 资源与权限隔离 |

## 具体示例

下面是一份最小 Deployment 清单，演示 K8s 最核心的用法：声明"web 应用跑 3 副本、镜像 myapp:1.0"，控制器便自动把它调度上集群并维持 3 副本。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels: {app: web}
  template:
    metadata:
      labels: {app: web}
    spec:
      containers:
      - {name: web, image: myapp:1.0, ports: [{containerPort: 5000}]}
```

配套的日常操作集中在 `kubectl`：`get pods` 看状态、`describe pod` 查详情、`logs` 看日志、`scale` 改副本、`rollout restart` 滚动重启。

## 何时用与何时不用

- **用**：多服务、多主机的微服务集群，需要自动扩缩容、滚动发布、自愈与统一调度。
- **不用**：单机跑一两个服务、流量平稳的简单应用——K8s 自身的运维与学习成本会盖过收益，Docker Compose 或直接部署更划算。

## 优劣与代价

✅ 生态最强、可扩展、声明式自愈，是云原生事实标准。
✅ 滚动更新、Service 负载均衡、探针自愈开箱即用。
⚠️ 学习与运维门槛高，控制面本身也是需要维护的分布式系统。
⚠️ 资源开销与抽象层次多，小规模场景属于杀鸡用牛刀。

## 与相关概念的区别

- **K8s vs Docker**：Docker 是"造并跑单个容器"的运行时；K8s 是"跨主机编排一大堆容器"的平台，二者是互补而非替代。
- **K8s vs Docker Swarm**：都是编排器，Swarm 上手更简单，K8s 在扩展性、生态和社区上占绝对优势。
- **Service vs Ingress**：Service 提供集群内稳定的四层网络入口，Ingress 在其上做七层 HTTP 路由与外部暴露。

## 常见误区

- Kubernetes 就是 Docker 的另一个名字，用了 K8s 就不用理解容器运行时。
- 任何项目哪怕单机跑一个服务也应该上 Kubernetes。
- 建好 Deployment 就永久高可用，不需要配就绪 / 存活探针。

## 面试速答

> 🎯 K8s 是容器编排平台：以 Pod 为最小单元，用 Deployment / Service 声明式地管理部署、扩缩容、自愈与负载均衡，把跨主机的容器当一台机器来调度。
> 🔍 追问：K8s 和 Docker 是什么关系？
> 🔍 追问：liveness 探针和 readiness 探针作用有何不同？

## 相关术语

[[Kubernetes云原生实战指南]]、[[API设计最佳实践]]、[[Docker容器化完全指南]]、[[Linux系统管理高级指南]]、[[Web安全攻防实战指南]]、[[云服务详解]]

## 参考资料

建议人工核验：本词条内容建议对照 Kubernetes 官方文档做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
