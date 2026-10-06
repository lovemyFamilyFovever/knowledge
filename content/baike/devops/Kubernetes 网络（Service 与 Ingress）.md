---
title: "Kubernetes 网络（Service 与 Ingress）"
tags: []
source: "baike"
source_path: "技术文章 / DevOps与运维"
collected: "2026-09-05"
status: "imported"
---

# Kubernetes 网络（Service 与 Ingress）

> 📌 **导航**：本文是 **Kubernetes 网络** 词条，属 [[Kubernetes云原生实战指南]] 子词条。Service/Ingress 概览见 [[Kubernetes深入]]，本文讲类型与七层入口。

## 定义

**一句话定义：** Service 为一组动态 Pod 提供稳定的访问入口与负载均衡（ClusterIP/NodePort/LoadBalancer/ExternalName 四型），Ingress 则在其上做基于域名与路径的七层 HTTP/HTTPS 路由与 TLS 终结。

**通俗类比：** Service 像公司总机号码——总机不变，背后把电话转到当前空闲的分机（Pod）；Ingress 像前台按"域名/找哪个部门"把访客分流到不同楼层。

## 为什么需要它

Pod 是短暂的：重建后 IP 会变、且要多副本负载均衡。Service 用一个不变的虚拟 IP + 选择器把流量稳定地转发到后端 Pod 集合。而许多 HTTP 服务若各配一个 LoadBalancer 既贵又乱，Ingress 用"一个入口 + 按 host/path 路由"统一对外，并集中管 TLS。

## 核心机制

Service 四型：

| 类型 | 暴露范围 | 用途 |
|---|---|---|
| ClusterIP（默认） | 集群内虚拟 IP | 内部服务互访 |
| NodePort | 每节点一个端口 | 从集群外经节点端口访问 |
| LoadBalancer | 云厂商外部 LB | 对外生产入口 |
| ExternalName | CNAME 到外部域名 | 引用集群外服务 |

底层由 kube-proxy 依据 Endpoints 把 ClusterIP 流量转发到就绪 Pod；headless（`clusterIP: None`）直接返回 Pod IP，配 StatefulSet 给每个副本稳定域名。Ingress 通过 `ingressClassName` 选定控制器（如 NGINX），按 host+path 路由、用 `tls` + cert-manager 自动签发证书。

## 具体示例

Ingress 用一个域名+路径分流到不同 Service，并挂 TLS：

```yaml
kind: Ingress
spec:
  ingressClassName: nginx
  rules:
  - host: app.example.com
    http:
      paths:
      - {path: /,     pathType: Prefix, backend: {service: {name: frontend, port: {number: 80}}}}
      - {path: /api,  pathType: Prefix, backend: {service: {name: backend,  port: {number: 8080}}}}
```

## 何时用与何时不用

- **ClusterIP**：仅集群内互访；**NodePort**：临时对外/无云 LB；**LoadBalancer**：云上一键对外四层；**Ingress**：多个 HTTP(S) 服务统一七层入口 + TLS/路由。
- **不用**：非 HTTP 的四层协议（如数据库）走 LoadBalancer/NodePort，别硬塞 Ingress。

## 优劣与代价

✅ Service 让短暂 Pod 有稳定入口与负载均衡；Ingress 把大量 HTTP 服务收敛到一个带 TLS 的入口。
✅ headless 满足有状态集群的按副本寻址。
⚠️ 每服务一个 LoadBalancer 在云上贵且碎片化；Ingress 控制器本身要部署运维。
⚠️ NodePort 端口暴露面大，生产入口更宜 Ingress/LB。

## 与相关概念的区别

- **Service vs Ingress**：Service 是四层（TCP/UDP）稳定 VIP，按选择器转发；Ingress 是七层，按 host/path 把 HTTP 路由到多个 Service。
- **LoadBalancer Service vs Ingress**：前者一个服务配一个云 LB（成本高），后者一个 LB 后面按域名/路径分很多服务。

## 常见误区

- Ingress 就是四层负载均衡，和 LoadBalancer 型 Service 是一回事。
- Service 的 ClusterIP 是绑定在某台 Pod 上的真实固定 IP。
- 要让集群外访问服务，除了 LoadBalancer 没有别的办法。

## 面试速答

> 🎯 Service 用稳定 VIP 把流量转发到一组就绪 Pod（ClusterIP/NodePort/LoadBalancer/ExternalName 四型）；Ingress 在其上做七层域名/路径路由与 TLS。
> 🔍 追问：ClusterIP 背后到底把流量交给谁？
> 🔍 追问：什么时候用 Ingress 而不是 LoadBalancer Service？

## 相关术语

[[Kubernetes云原生实战指南]]、[[Kubernetes深入]]、[[Kubernetes 工作负载（StatefulSet 与 DaemonSet）]]、[[容器网络与数据持久化]]

## 参考资料

建议人工核验：以 Kubernetes Service / Ingress 官方文档为准；未编造文献编号或 URL。
