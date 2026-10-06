---
title: "Linux 网络管理"
tags: []
source: "baike"
source_path: "技术文章 / DevOps与运维"
collected: "2026-09-05"
status: "imported"
---

# Linux 网络管理

> 📌 **导航**：本文是 **Linux 网络管理** 词条，属 [[Linux系统管理高级指南]] 子词条。内核网络协议栈机制见 [[操作系统内核原理]]。

## 定义

**一句话定义：** Linux 网络管理是用 iproute2 / nftables 等工具对主机网络做配置与治理——包过滤防火墙（nftables）、按源或属性选路的策略路由、隔离广播域的二层 VLAN 子接口、以及把虚拟机/容器接入局域网的网桥。

**通俗类比：** 像给一栋楼管网络：nftables 是门禁规则（谁能进、走哪门），策略路由是"按发件人分流的邮路"，VLAN 是"同一栋楼划出互不干扰的部门内网"，网桥是把各房间（虚机/容器）串进同一局域网。

## 为什么需要它

主机不只是"能上网"，还要控流量进出（防火墙）、多出口时按规则选路、把不同业务隔离到不同广播域、以及让容器/虚机以二层身份接入网络。iproute2 与 nftables 这些工具正是把这些管理需求落到内核网络栈上的手段。

## 核心机制

- **nftables**：取代 iptables 的后端防火墙，用 `table`/`chain`(带 hook/priority/policy)/`rule` 组织；基于集合与映射、支持原子替换，规则多时性能优于逐条匹配的 iptables。
- **策略路由**：`ip rule add from ... lookup <table>` + `/etc/iproute2/rt_tables`，按源 IP/标记等选不同路由表，而非只看目的 IP。
- **VLAN**：`ip link add link eth0 ... type vlan id 100` 在物理口上切子接口，隔离二层广播域。
- **网桥**：`ip link add name br0 type bridge` + `ip link set eth1 master br0`，把虚机/容器接到同一二层网络（也见 [[容器网络与数据持久化]]）。

## 具体示例

一条最小 nftables 入站链：默认丢弃，只放行已建立连接、回环、SSH、ICMP：

```bash
nft add table inet f
nft add chain inet f input '{ type filter hook input priority 0; policy drop; }'
nft add rule inet f input ct state established,related accept
nft add rule inet f input iif lo accept
nft add rule inet f input tcp dport 22 accept
```

## 何时用与何时不用

- **用**：主机级防火墙、多链路/多租户选路、VLAN 隔离、给容器/虚机搭桥。
- **不用**：集群级网络策略交给 [[Kubernetes 网络（Service 与 Ingress）]]/服务网格，别在每台主机手堆 iptables；跨机 overlay 用 CNI 而非手工 bridge。

## 优劣与代价

✅ nftables 语法统一、集合化、原子热更新、性能更好。
✅ iproute2 把地址/路由/VLAN/网桥收敛到 `ip` 一个命令族。
⚠️ 策略路由与 nftables 心智负担高，规则复杂后难审计。
⚠️ host 层 bridge/VLAN 与上层编排网络叠加时易冲突、排障难。

## 与相关概念的区别

- **iptables vs nftables**：同一 netfilter 框架的两代用户态；nftables 支持集合/映射、原子替换、更少线性遍历。
- **策略路由 vs 常规路由**：常规按目的 IP 查表；策略路由可"按源/入接口/标记"选不同表。
- **VLAN vs 网桥**：VLAN 在二层划分局域广播域；网桥把多接口/虚机二层互联。

## 常见误区

- nftables 只是 iptables 换了个命令名，能力完全一样。
- 策略路由和普通路由一样，只按目的 IP 选路。
- 配网桥必须依赖老的 bridge-utils，ip 命令做不到。

## 面试速答

> 🎯 Linux 网络管理：nftables(table/chain/rule + hook/policy，集合化、原子替换，优于逐条的 iptables)做主机防火墙；策略路由按源/属性查多张路由表；VLAN 子接口隔离广播域；bridge 把虚机/容器接入二层。内核协议栈机制见 [[操作系统内核原理]]。
> 🔍 追问：nftables 相比 iptables 强在哪？
> 🔍 追问：策略路由和常规路由的差别？

## 相关术语

[[Linux系统管理高级指南]]、[[操作系统内核原理]]、[[容器网络与数据持久化]]、[[Web安全攻防实战指南]]

## 参考资料

建议人工核验：以 iproute2 / nftables 官方文档为准；未编造文献编号或 URL。
