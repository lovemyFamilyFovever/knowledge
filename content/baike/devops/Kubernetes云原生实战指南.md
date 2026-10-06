---
title: "Kubernetes云原生实战指南"
tags: []
source: "baike"
source_path: "技术文章 / DevOps与运维"
collected: "2026-09-05"
status: "imported"
---

# Kubernetes云原生实战指南

> 📌 **导航**：本页是 **Kubernetes 云原生** 枢纽。容器基础、Pod/Deployment 基础已收敛到专条，本页索引 K8s 进阶主题。

## 定义

**一句话定义：** Kubernetes 云原生实战，是在容器基础（镜像/隔离）之上，用声明式工作负载、网络与服务发现、配置与存储等原语，把应用可靠地调度到集群中运行的工程实践。

**通俗类比：** 容器是"标准集装箱"，[[Kubernetes深入]] 是"自动化港口"；本页进阶则像"特种货柜的处理规程"——有状态货(StatefulSet)、每层楼巡检(DaemonSet)、对外报关口(Service/Ingress)。

## 为什么需要它

会起一个 Deployment 只是开始。真正上生产会碰到：数据库这类有状态服务 Deployment 管不好、节点级监控/日志 Agent 要每台都跑、一堆 HTTP 服务对外入口乱且证书难管。这些进阶主题不解决，集群就跑不稳、上不了生产。

## 核心机制

| 主题 | 归口 |
|---|---|
| 容器 vs VM、镜像分层、Namespace/Cgroups 隔离、Dockerfile 基础 | [[容器与编排技术详解]]、[[Docker 镜像构建与分发]] |
| Pod、Service/Deployment/ConfigMap/探针 等 K8s 基础原语 | [[Kubernetes深入]] |
| 有状态与节点守护工作负载（StatefulSet / DaemonSet） | [[Kubernetes 工作负载（StatefulSet 与 DaemonSet）]] |
| Service 四类型与 Ingress 七层路由/TLS | [[Kubernetes 网络（Service 与 Ingress）]] |
| 跨主机容器网络模型（bridge/overlay/macvlan） | [[容器网络与数据持久化]] |

## 具体示例

部署一个 MySQL 集群的取舍：用 [[Kubernetes 工作负载（StatefulSet 与 DaemonSet）]] 拿到稳定标识与一对一持久卷，集群内互访走 headless Service，HTTP 应用再经 [[Kubernetes 网络（Service 与 Ingress）]] 的 Ingress 统一暴露、cert-manager 签 TLS；无状态部分用 [[Kubernetes深入]] 的 Deployment。

## 何时用与何时不用

- **用**：单机 Compose 之外的多机生产：需要调度、自愈、伸缩、服务发现、七层入口与有状态编排时。
- **不用**：几个固定容器、无需跨机调度时，Docker/Compose 足够；K8s 自身控制面与运维成本不小（见 [[云服务详解]] 的托管 K8s）。

## 优劣与代价

✅ 声明式 + 控制面调和带来自愈、伸缩、可移植的部署模型。
✅ 原语分工清晰：工作负载/网络/配置/存储各司其职。
⚠️ 概念多、心智模型陡峭、有状态与网络尤其吃经验。
⚠️ 控制面与插件（Ingress/CNI/存储）本身是需要运维的组件。

## 与相关概念的区别

- **K8s vs Docker/Compose**：Docker/Compose 管单机，K8s 管跨机调度与自愈（见 [[容器与编排技术详解]]）。
- **工作负载 vs 网络**：前者定义"跑什么、几份、有没有状态"，后者定义"怎么被稳定访问"，见上述两子词条。

## 常见误区

- 有了 K8s，任何单机小项目都必须上集群才"云原生"。
- StatefulSet 只是"带存储的 Deployment"，没有更稳定的身份语义。
- 集群对外只靠 LoadBalancer，Ingress 可有可无。

## 面试速答

> 🎯 K8s 云原生进阶：有状态用 StatefulSet、节点守护用 DaemonSet，Service 四类型 + Ingress 七层入口/TLS；容器基础见 [[容器与编排技术详解]]、Pod/Deployment 见 [[Kubernetes深入]]。跨机调度与自愈才是 K8s 相对 Compose 的价值。
> 🔍 追问：什么时候 K8s 是过度设计？
> 🔍 追问：有状态服务为何不能简单用 Deployment？

## 相关术语

[[Kubernetes深入]]、[[容器与编排技术详解]]、[[Docker 镜像构建与分发]]、[[Docker容器化完全指南]]、[[Kubernetes 工作负载（StatefulSet 与 DaemonSet）]]、[[Kubernetes 网络（Service 与 Ingress）]]、[[容器网络与数据持久化]]、[[API设计最佳实践]]、[[Linux系统管理高级指南]]、[[Web安全攻防实战指南]]、[[云服务详解]]

## 参考资料

建议人工核验：以 Kubernetes 官方文档为准；本原稿 Ingress 示例末尾被导入截断，配置以官方文档为准（见 v1.2 §5，未据推测补写）。
