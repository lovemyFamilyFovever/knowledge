---
title: "VPN与隧道加密"
tags: []
source: "baike"
source_path: "开发术语 / 网络与协议"
collected: "2026-09-05"
status: "imported"
---

# VPN与隧道加密

> 📌 **导航**：本文是 **VPN与隧道加密** 词条，由 [[网络安全协议]] 拆分而来。TLS/证书见 [[HTTPS 与 TLS]]。

## 定义

**一句话定义：** VPN 在公共网络上用加密隧道建立私有通道、IPSec 在网络层为 IP 流量提供加密与认证——IPSec 分传输模式（护载荷）与隧道模式（护整个 IP 包），常见 VPN 协议有 PPTP / L2TP-IPSec / OpenVPN / WireGuard。

**通俗类比：** VPN 像一条加密传送带——你从这头进、那头出来已在内网，外面看不到带里运了什么；IPSec 隧道模式就是把整封信再套一个新信封。

## 为什么需要它

公网不可信，远程办公、跨站点互联、公共 Wi-Fi 下须防窃听与篡改。IPSec / VPN 在 IP 或专用通道层加密封与认证，把不安全的公网当作安全链路来用。

## 核心机制

- **IPSec：** AH 只认证不加密、ESP 加密 + 认证 + 完整性、IKE 协商密钥；传输模式端到端、隧道模式保护整个 IP 包（站点到站点）。
- **VPN 协议：** PPTP(1723，弱、已弃用)、L2TP/IPSec(500/4500，强、兼容好)、OpenVPN(1194，OpenSSL，通用)、WireGuard(51820/UDP，ChaCha20 + Curve25519，内核级、现代首选)。

## 具体示例

现代组网首选 WireGuard：配置极简、内核态转发快，AllowedIPs 决定是全局代理还是仅回内网；企业站点互联用 IPSec 隧道模式，公网上只暴露 ESP。

## 何时用与何时不用

- **用：** 远程访问内网、站点到站点、跨公网加密传输选 WireGuard / OpenVPN / IPSec。
- **不用：** PPTP 已不安全别用；只需访问个别内网服务时，用 [[SSH与远程登录]] 端口转发比全局 VPN 暴露面更小。

## 优劣与代价

✅ 把公网变成安全的私有链路；WireGuard 快而简、IPSec 是企业级通用方案。
⚠️ IPSec 配置复杂、穿越 NAT 需隧道 / NAT-T；VPN 出口集中易成瓶颈，也常被用于绕过管控、需注意合规。

## 与相关概念的区别

vs [[HTTPS 与 TLS]]：TLS 在传输 / 应用层给特定应用加密，VPN / IPSec 在网络层给所有 IP 流量加密；vs [[网络地址转换]]：IPSec 穿越 NAT 要靠隧道模式 / NAT-T。

## 常见误区

- 用了 VPN 就不需要 TLS，二者取其一即可。
- WireGuard 和 PPTP 都是 VPN、安全性差不多。
- IPSec 的传输模式和隧道模式一样。

## 面试速答

> 🎯 VPN 与隧道加密：IPSec(网络层；AH 认证/ESP 加密/IKE 协商；传输模式护载荷、隧道模式护整包) 之上跑 VPN——PPTP 弱弃用、L2TP/IPSec 兼容、OpenVPN 通用、WireGuard(内核级、ChaCha20) 现代首选；与 TLS 是"网络层全流量 vs 应用层单应用"之别。
> 🔍 追问：IPSec 传输模式和隧道模式差在哪？
> 🔍 追问：为什么 WireGuard 比 OpenVPN 快？

## 相关术语

[[HTTPS 与 TLS]]、[[网络地址转换]]、[[SSH与远程登录]]、[[网络安全协议]]
