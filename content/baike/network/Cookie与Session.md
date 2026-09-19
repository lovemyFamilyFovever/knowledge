---
title: "Cookie与Session"
tags: []
source: "baike"
source_path: "开发术语 / 网络与协议"
collected: "2026-09-05"
status: "imported"
---

# Cookie与Session

> 📌 **导航**：本文是 **Cookie与Session** 词条，由 [[HTTP协议]] 拆分而来。

## 定义

**一句话定义：** Cookie 存在客户端浏览器、Session 存在服务器，二者用 Session ID 关联，为无状态的 HTTP 提供"认出用户、维持登录态"的机制。

**通俗类比：** Cookie 是超市给你的会员卡（你拿着），Session 是超市后台的会员档案（超市存着），卡号把两者关联起来。

## 为什么需要它

HTTP 是无状态协议，每次请求都像"初次见面"。要"登录一次、一路有效"，就得让客户端带一个凭证、服务端据此找回会话——Cookie / Session / JWT 正是三种主流做法。

## 核心机制

- **Cookie 属性：** 经 Set-Cookie 下发；HttpOnly（禁 JS 读，缓解 XSS 窃取）、Secure（仅 HTTPS）、SameSite=Lax/Strict/None（约束跨站携带、缓解 CSRF）、Path / Expires / Max-Age。
- **Session：** 服务端存 session_store，客户端只带 session_id；服务端可控失效，但占存储，分布式需共享（粘滞会话或集中存储如 Redis）。
- **JWT 对比：** 令牌自带签名与载荷、服务端免存储、利于水平扩展，但签发后难即时吊销、payload 只签名不加密。

## 具体示例

`Set-Cookie: session_id=abc; HttpOnly; Secure; SameSite=Lax` 下发后浏览器自动携带，服务器用 session_id 查出 user_id=1001。JWT 则把 user_id 签进令牌、经 `Authorization: Bearer` 带上，服务端验签即可、无需查存储。

## 何时用与何时不用

- **用：** 需登录态的传统 Web 应用用 Cookie + Session；跨域 API / 微服务无状态鉴权多用 JWT（Bearer）。
- **不用：** 无身份需求的接口不必设 Session；敏感权限判断不能只信前端可读的 Cookie。

## 优劣与代价

✅ 让无状态 HTTP 具备会话连续性：Session 易集中失效、JWT 易水平扩展。
⚠️ Cookie 有约 4KB 上限、存在被窃取（XSS/CSRF）风险、跨域受 SameSite 限制；Session 占服务端、集群要共享；JWT 难即时吊销、体积较大。

## 与相关概念的区别

vs [[HTTPS 与 TLS]]：TLS 保护传输通道，Cookie 是应用层凭证；vs 集中式 [[分布式缓存]]：Session 若外置到 Redis 正是用它做共享存储。

## 常见误区

- 设了 HttpOnly 就绝不会被 CSRF 攻击。
- JWT 的 payload 是加密的，可以放心放敏感信息。
- Session 只能存在本机内存、无法跨多实例共享。

## 面试速答

> 🎯 Cookie(客户端) ↔ Session(服务端) 用 session_id 关联、给无状态 HTTP 提供登录态；Cookie 靠 HttpOnly/Secure/SameSite 控安全，Session 占服务端需共享存储；JWT 自包含免存储、利于扩展但难即时吊销。
> 🔍 追问：HttpOnly 和 SameSite 各防什么攻击？
> 🔍 追问：为什么 JWT 难以即时失效、怎么缓解？

## 相关术语

[[HTTP头部与内容协商]]、[[HTTPS 与 TLS]]、[[分布式缓存]]、[[HTTP协议]]
