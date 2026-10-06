---
title: "Cookie、Session 与 Token"
tags: [八股文, 网络与浏览器]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# Cookie、Session 与 Token

## 一句话定义

cookie 是浏览器存的一小条，session 在服务端，token 自带身份。

## 面试官为什么问它

他实际要问的是「你的登录态怎么做的、退出登录怎么让 token 失效」——这是有无真实后端经验的照妖镜。

## 30 秒版回答

传统做法是服务端存 session，把 sessionId 写进 cookie，请求带 cookie 找回上下文——好处能服务端主动踢人，坏处是要共享存储、跨域麻烦。Token（JWT）把身份写进令牌本身并用签名防篡改，服务端不存状态，横向扩展容易。代价是签发后不能主动撤销，所以要做短有效期加刷新令牌，或者额外维护黑名单。安全上 cookie 要 HttpOnly 防脚本读、Secure 只在 HTTPS 走、SameSite 控制跨站是否携带。

## 被追问三层时的诚实边界

我实际做的是 JWT 加服务端刷新与 RLS 行级安全联动，也把 CSRF token 放在同源校验里；SSO/OIDC 的完整授权码流程我没有从零接过，我的理解是它本质还是「换到短命 token」这一套。

## 本库深挖

- [[OAuth 与 JWT]] —— 令牌格式与授权流程
- [[Cookie与Session]] —— 服务端会话的实现细节
- [[API Key 与 Basic 与 Bearer 认证方式]] —— 三种认证头怎么选
