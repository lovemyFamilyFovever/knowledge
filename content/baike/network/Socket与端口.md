---
title: "Socket与端口"
tags: []
source: "baike"
source_path: "开发术语 / 网络与协议"
collected: "2026-09-05"
status: "imported"
---

# Socket与端口

> 📌 **导航**：本文是 **Socket与端口** 词条，由 [[网络基础]] 拆分而来。

## 定义

**一句话定义：** 端口号是设备内区分应用的"房间号"（IP 定位主机、端口定位进程），Socket 则是"IP + 端口"构成的通信端点及其编程接口，让程序收发网络数据。

**通俗类比：** IP 是大楼地址、端口是房间号、Socket 就是"某楼某房"这个完整收件点，也是你拨出 / 接听的那部电话。

## 为什么需要它

一台主机同时跑 Web / DB / 缓存等多个服务，靠端口把到达的包分给正确进程；Socket 把传输层（TCP/UDP）的建连、收发、关闭封装成统一 API，是几乎所有网络编程的基础。

## 核心机制

- **端口区间：** 0–1023 公认端口（HTTP 80、HTTPS 443、SSH 22、MySQL 3306），49152–65535 动态端口；`netstat -tlnp` / `lsof -i :80` 查监听与占用。
- **Socket 模型：** 服务端 socket()→bind()→listen()→accept()，客户端 socket()→connect()；面向流用 SOCK_STREAM（TCP）、面向数据报用 SOCK_DGRAM（UDP）。
- **五元组：** 协议 + 源 IP + 源端口 + 目的 IP + 目的端口，唯一确定一条连接。

## 具体示例

写一个 echo 服务：TCP 下 `socket(SOCK_STREAM)`、bind 8080、listen、accept 取连接、recv/sendall；同一台机上 Web 占 80、DB 占 3306，端口就是它们的分流依据。

## 何时用与何时不用

- **用：** 网络编程与端口排查都绕不开 Socket；服务端选监听端口避开公认端口、防冲突。
- **注意：** 用 Socket 直写 TCP 协议时要自定消息边界（字节流，见 [[TCP粘包与拆包]]）；监听 1024 以下端口通常需特权。

## 优劣与代价

✅ 端口 + Socket 把"到哪台机、给哪个进程、怎么收发"标准化，跨语言通用。
⚠️ 端口冲突与防火墙放行要管理；Socket 是底层 API，边界 / 阻塞 / 错误处理易出错。

## 与相关概念的区别

vs [[TCP深入]] / [[用户数据报协议]]：那两者是传输协议，Socket 是使用它们的编程接口；IP 定位主机、端口定位进程，Socket = 二者组合的端点。

## 常见误区

- 端口可以随便占用、不会冲突也不需要权限。
- Socket 就等于一条 TCP 连接（UDP 也用 Socket）。
- 同一端口能被任意多个进程同时无限制监听。

## 面试速答

> 🎯 Socket 与端口：IP 定位主机、端口定位进程（0-1023 公认、动态 49152-65535），Socket 是"IP+端口"的通信端点与编程 API——TCP 走 SOCK_STREAM(bind/listen/accept)、UDP 走 SOCK_DGRAM；五元组唯一确定一条连接。
> 🔍 追问：TCP 与 UDP 的 Socket 编程差异？
> 🔍 追问：为什么服务端 bind/listen/accept、客户端只需 connect？

## 相关术语

[[TCP深入]]、[[用户数据报协议]]、[[TCP粘包与拆包]]、[[网络基础]]
