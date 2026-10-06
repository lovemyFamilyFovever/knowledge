---
title: "CSRF"
tags: [八股文, Node 与后端]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# CSRF

## 一句话定义

借用浏览器自动带上的凭证，骗你的身份发出去写请求。

## 面试官为什么问它

他想知道你的防护是「听说 SameSite 就行」还是真理解它挡不住哪一路。

## 30 秒版回答

CSRF 利用的是浏览器会替同源页面自动附带 cookie：攻击者自己的页面发一个指向你站点的表单或请求，凭证跟着过去，服务端就把它当成你。防御分四层：SameSite=Lax/Strict 限制跨站是否带 cookie；服务端校验 Origin/Referer；带一个攻击者读不到的 CSRF token 并在写操作校验；以及不把 GET 用于有副作用的操作。SameSite 挡的是大部分场景但不是全部，Strict 又会破坏正常的第三方跳转。

## 被追问三层时的诚实边界

我实际做过的是同源校验加 CSRF token 的组合（平台内核里就有一段 CSRF 与前缀的实现，我为了对接逆向过它）；BEAST、CRIME 这类与 TLS 相关的历史攻击我没有实操过，我的理解是它们与 CSRF 不同层。

## 本库深挖

- [[CSRF与SSRF]] —— CSRF 与 SSRF 的防御清单
- [[05-环境事实-2026-08-26-平台内核CSRF与前缀]] —— 我实际逆向过的平台 CSRF 形态
- [[Web安全攻防]] —— 攻击面全景
