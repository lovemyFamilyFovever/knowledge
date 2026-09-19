---
title: "DDoS攻击与防护"
tags: []
source: "baike"
source_path: "开发术语 / 网络与协议"
collected: "2026-09-05"
status: "imported"
---

# DDoS攻击与防护

> 📌 **导航**：本文是 **DDoS攻击与防护** 词条，由 [[网络安全协议]] 拆分而来。SYN Flood 的握手机理见 [[TCP深入]]。

## 定义

**一句话定义：** DDoS 用大量分布式主机向目标灌请求 / 流量，耗尽带宽、连接或计算资源使其无法服务正常用户；按层次分流量型、协议型、应用层型，防护靠清洗、限速、SYN Cookie、CDN 分散与云高防。

**通俗类比：** 像一万人同时拨打一家餐厅的电话占满所有线路、真客人打不进——问题不是"打进来的有问题"，而是"线路被占满"。

## 为什么需要它

攻击者租僵尸网络成本低、破坏力大，业务一旦被 DDoS 可用性直接归零。理解各层攻击才能对症：带宽型靠清洗、连接型靠 SYN Cookie、应用层靠人机校验与限频。

## 核心机制

- **流量型（网络层）：** UDP / ICMP Flood 耗尽带宽——大带宽清洗中心 / CDN 吸收。
- **协议型（传输层）：** SYN Flood、Ping of Death 耗尽连接资源——SYN Cookie、放大半连接队列、connlimit。
- **应用层：** HTTP Flood、CC、Slowloris 耗 CPU / 内存、伪装像真用户——频控、验证码、行为识别、WAF。
- **通用缓解：** 云 DDoS 高防、Anycast 就近分散、上行限速、隐藏真实源站 IP。

## 具体示例

SYN Flood 打半连接队列：开 `net.ipv4.tcp_syncookies=1` 用 cookie 无状态记录、收到合法 ACK 才建连；HTTP CC 攻击难在"看着都像真人"，靠 [[限流]] 按 IP / 用户限速 + 挑战验证 + CDN 挡在源站前。

## 何时用与何时不用

- **用：** 对外业务前置高防 / CDN；边界启用 SYN Cookie 与 connlimit；应用层做限频与人机校验。
- **注意：** 应用层 DDoS 最难区分真假、纯带宽清洗无效，需行为分析；源站 IP 一旦泄露可被绕过直打。

## 优劣与代价

✅ 分层防护能把攻击挡在源站之外、保住可用性。
⚠️ 高防 / 清洗有成本；应用层检测有误伤真实用户的风险；隐藏源站要求全链路不暴露真实 IP。

## 与相关概念的区别

vs [[防火墙与WAF]]：WAF 拦恶意内容、DDoS 防护扛"量"；vs [[TCP深入]]：SYN Flood 利用的正是三次握手半连接队列、SYN Cookie 是传输层缓解；vs [[限流]]：限流是应用层 DDoS 防护的一种手段。

## 常见误区

- DDoS 就是带宽被打满，加带宽即可解决。
- 应用层 CC 攻击很容易和真实流量区分。
- SYN Cookie 完全无损、不丢任何功能。

## 面试速答

> 🎯 DDoS：流量型(UDP/ICMP 耗带宽→清洗/CDN)、协议型(SYN Flood 耗连接→SYN Cookie/connlimit)、应用层(HTTP Flood/CC/Slowloris 耗 CPU、像真人→限流/验证码/行为识别/WAF)；云高防 + Anycast 分散 + 隐藏源站，应用层最难防因真假难辨。
> 🔍 追问：为什么应用层 DDoS 最难防？
> 🔍 追问：SYN Cookie 为什么能缓解 SYN Flood？

## 相关术语

[[TCP深入]]、[[防火墙与WAF]]、[[限流]]、[[内容分发网络]]
