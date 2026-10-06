---
title: "跨域与 CORS"
tags: [八股文, 网络与浏览器]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# 跨域与 CORS

## 一句话定义

浏览器拦下不同源的请求，服务端用响应头明确放行。

## 面试官为什么问它

前端必问，因为他想听你把「预检」和「带 cookie」这两个真坑说清楚，而不是只会说加个头。

## 30 秒版回答

同源策略是浏览器加的（协议、域名、端口三者一致），跨域时请求其实发出去了，是响应被拦。CORS 靠服务端返回允许来源来放行：简单请求直接发；带自定义头、PUT/DELETE 或非表单 content-type 会先做一次 OPTIONS 预检，问 Allowed-Origin、Allowed-Methods、Allowed-Headers，预检结果可用 Max-Age 缓存。要带 cookie 必须两边都表态——服务端 Allow-Credentials 为 true 且 Origin 不能写星号，前端请求也要显式开启凭证。

## 被追问三层时的诚实边界

我实际做过的是在网关/Nginx 层统一加 CORS 头，也踩过带凭证时星号 Origin 被浏览器拒绝的坑；用 Postman 复现「服务端本来没问题」这类判断我做得多，我的理解是开发期代理和 CORS 是两件事，别用代理掩盖线上配置缺失。

## 本库深挖

- [[跨域资源共享（CORS）]] —— 预检与凭证的规则细节
- [[HTTP请求方法]] —— 哪些方法会触发预检
- [[XSS 与内容安全]] —— 同源策略防的另一半
