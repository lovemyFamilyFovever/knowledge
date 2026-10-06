---
title: "Kubernetes 工作负载（StatefulSet 与 DaemonSet）"
tags: []
source: "baike"
source_path: "技术文章 / DevOps与运维"
collected: "2026-09-05"
status: "imported"
---

# Kubernetes 工作负载（StatefulSet 与 DaemonSet）

> 📌 **导航**：本文是 **Kubernetes 工作负载** 词条，属 [[Kubernetes云原生实战指南]] 子词条。Pod / Deployment 基础见 [[Kubernetes深入]]，本文讲两类专用工作负载。

## 定义

**一句话定义：** StatefulSet 为有状态应用提供稳定网络标识、有序部署与一对一持久卷；DaemonSet 则确保每个（或选定）节点都运行一份 Pod 副本，用于日志采集、监控、存储等节点级守护进程。

**通俗类比：** StatefulSet 像"有学号的学生"——编号固定（mysql-0/1/2）、各自专属储物柜（独立 PVC）、按序上下课；DaemonSet 像"每层楼配一名保洁"——有这层就得有一个，与业务请求数无关。

## 为什么需要它

Deployment 管理的是"可互换的无状态副本"，但数据库/消息队列这类有状态应用需要稳定身份（集群内互相寻址）、专属且跟随实例的存储、以及有序的启停与滚动——这些 Deployment 给不了。另一类需求是"每个节点都要跑一份"（node-exporter、日志 Agent、CNI），DaemonSet 正是为此而生。

## 核心机制

- **StatefulSet**：由 `serviceName` 关联稳定域名，Pod 获得有序序号主机名（name-0…N）与稳定网络标识；`volumeClaimTemplates` 为每个副本生成独占 PVC，删除重建仍绑定原卷；部署/伸缩/滚动更新按序进行。
- **DaemonSet**：在满足 nodeSelector 的每个节点跑一个副本；用 `tolerations`（如 `operator: Exists` 容忍 `NoSchedule`）可落到 master/control-plane；常配 `hostPath`/`hostNetwork` 读宿主指标。

## 具体示例

StatefulSet 的关键是"稳定身份 + 一对一持久卷"：

```yaml
kind: StatefulSet
spec:
  serviceName: mysql                 # 稳定网络标识 mysql-0..N
  volumeClaimTemplates:              # 每副本独占 PVC，重建仍绑回
  - metadata: {name: data}
    spec:
      accessModes: [ReadWriteOnce]
      resources: {requests: {storage: 20Gi}}
```

DaemonSet 则常给 node-exporter 这类加 hostPath 卷挂载宿主 /proc、/sys 并以 tolerations 覆盖全节点。

## 何时用与何时不用

- **StatefulSet**：数据库、消息队列、有状态集群（需稳定标识/有序/专属存储）。
- **DaemonSet**：节点级守护进程——监控、日志采集、存储/CNI 插件。
- **不用**：无状态可互换服务用 Deployment；一次性/定时任务用 Job/CronJob。

## 优劣与代价

✅ 有状态应用获得稳定网络与存储、可控的有序生命周期。
✅ 节点级后台任务随节点自动扩缩，无需手工铺。
⚠️ StatefulSet 编排更复杂、滚动更新更谨慎（按序、需就绪）。
⚠️ DaemonSet 抢占每节点资源，配 hostPath 时耦合宿主、需谨慎权限。

## 与相关概念的区别

- **StatefulSet vs Deployment**（见 [[Kubernetes深入]]）：Deployment 副本无状态、可互换、名字/IP 不稳定；StatefulSet 副本有序、有稳定标识与专属存储。
- **StatefulSet vs DaemonSet**：前者是"一组有状态、可复制的实例"（数量固定副本数），后者是"每节点一份"（数量随节点数）。

## 常见误区

- StatefulSet 和 Deployment 都能管数据库，二者没有本质区别。
- StatefulSet 的 Pod 重建后名字和存储都会变，和 Deployment 一样不可预测。
- master 节点有污点，DaemonSet 就无法在其上运行任何副本。

## 面试速答

> 🎯 StatefulSet 管有状态应用：稳定标识 name-0…N + 每副本独占、重建仍绑定的 PVC + 有序部署；DaemonSet 保证每节点跑一份 Pod（tolerations 可含 master），用于监控/日志/CNI 守护。无状态用 Deployment。
> 🔍 追问：StatefulSet 相比 Deployment 管数据库的关键差异？
> 🔍 追问：DaemonSet 和 Deployment 的"副本数"由什么决定？

## 相关术语

[[Kubernetes云原生实战指南]]、[[Kubernetes深入]]、[[Kubernetes 网络（Service 与 Ingress）]]

## 参考资料

建议人工核验：以 Kubernetes 官方 StatefulSet / DaemonSet 文档为准；未编造文献编号或 URL。
