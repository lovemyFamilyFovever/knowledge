---
title: "K8s 最小集 Pod、Deployment、Service"
tags: [八股文, 工程化与 DevOps]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# K8s 最小集 Pod、Deployment、Service

## 一句话定义

编排三件套：跑的单位、副本与升级的管理者、稳定的访问入口。

## 面试官为什么问它

他不需要你是运维，只想确认你说的「部署在 K8s 上」不是空话——三个词能各答一句就够。

## 30 秒版回答

Pod 是最小部署单位，里面是一个或多个共享网络与存储的容器，同 Pod 内容器用 localhost 互访，但 Pod 会随时被销毁重建、IP 不稳定。Deployment 声明要几个副本、用哪个镜像，负责滚动升级与回滚，它通过 ReplicaSet 保证期望副本数。Service 给一组 Pod 一个固定的 Cluster IP 和名字，靠标签选择器把流量负载均衡过去，对外访问再靠 Ingress 或 LoadBalancer 接进来。

## 被追问三层时的诚实边界

我实际是把服务部署到平台容器环境（由平台侧管编排），所以我讲得清概念与用途；手写 StatefulSet、存储卷声明与探针调参我没有实操过，我的理解是有状态服务才需要 StatefulSet 的稳定身份与顺序。

## 本库深挖

- [[Kubernetes深入]] —— 对象模型与调度
- [[Kubernetes 网络（Service 与 Ingress）]] —— 流量怎么进来
- [[Kubernetes 工作负载（StatefulSet 与 DaemonSet）]] —— 其余工作负载形态
