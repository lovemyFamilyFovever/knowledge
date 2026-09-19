---
title: "跨域资源共享（CORS）"
tags: []
source: "baike"
source_path: "开发术语 / 安全与加密"
collected: "2026-09-05"
status: "imported"
---

# 跨域资源共享（CORS）


> 📌 **导航**：本文是 **跨域资源共享（CORS）** 词条，属于 security 术语集。归口枢纽：[[网络安全篇]]；同源身份与凭证的攻防在 [[CSRF与SSRF]]。

## 定义

**一句话定义：** 跨域资源共享(CORS)是浏览器同源策略的受控放行机制：默认禁止一个源的脚本读取另一个源的资源，服务器用一组 `Access-Control-*` 响应头显式声明"哪个源可以跨源读"，浏览器据此放行或拦截——它约束的是浏览器对响应的"读"，不是服务器对请求的"访问"。

**通俗类比：** 像小区门禁的白名单登记：外来快递(跨源脚本)默认进不了门，只有物业(服务器)提前登记"某公司工牌可进"，门禁才认这张卡；没登记的照样被拦在门外。

## 为什么需要它

前端页面常要调另一个域的 API(如 `app.example.com` 调 `api.other.com`)。若没有同源策略，任意网站脚本都能带着你的登录态去悄悄读别的站点数据；一刀切禁止又让合法的跨源集成无法进行。CORS 提供折中：由资源服务器精确指定许可范围，浏览器在读取侧把关，把"跨源"从"全禁/全放"变成可按源、方法、头逐项授权的灰名单。

## 核心机制

| 请求类型 | 触发条件 | 浏览器行为 |
|----------|----------|------------|
| 简单请求 | GET/POST/HEAD + 受限头与 content-type | 直接发出并带 Origin，按响应头决定能否读 |
| 预检请求 | 非简单方法(PUT/DELETE) 或自定义头 | 先发 OPTIONS 问权限，通过才发真实请求 |
| 带凭证请求 | `withCredentials=true` | `Allow-Origin` 不能用 `*`，须精确回源 |

- **同源=协议+主机+端口三者全等**：`https://a.com` 与 `http://a.com`、`https://api.a.com` 都算跨源；同源策略约束的是"脚本读响应"，服务器其实照常返回了数据，是浏览器拦住了 JS 拿它(底层语义见 [[HTTP协议]]、凭证侧见 [[Cookie与Session]])。
- **放行靠响应头逐项授权**：`Access-Control-Allow-Origin` 指定许可源，配 `-Methods`/`-Headers` 放方法与自定义头、`-Max-Age` 缓存预检结果、`-Credentials` 允许带 Cookie；预检的 OPTIONS 必须先答齐这些头，真实请求才会发出。
- **凭证与通配互斥**：一旦 `withCredentials=true`，`Allow-Origin` 就不能回 `*`，服务端要么精确回显来源、要么拒绝——这与 CSRF 争夺的正是"请求带不带 Cookie"同一块地(见 [[CSRF与SSRF]])。

## 具体示例

服务端对 `Origin: https://app.example.com` 的请求回一组头即可放行该源读取：

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 86400
```

OPTIONS 预检要单独应答 `-Methods` 与 `-Headers`；漏应答会让浏览器在真实请求前就报 CORS 错，表现为接口 200 却读不到。

## 何时用与何时不用

- **该做**：跨源 API 明确列出许可源白名单、按需最小放行方法与头、带 Cookie 时精确回源而非开 `*`、生产环境禁用通配；前端把 OPTIONS 失败当配置问题排查。
- **不该指望**：别把 CORS 当服务器安全边界——它只挡浏览器 JS 读，挡不住 curl 或服务端直连；真正的鉴权在应用层(攻防概览见 [[Web安全攻防]])。

## 优劣与代价

✅ 细粒度按源/方法/头授权，让合法跨源集成与恶意读取可区分，规则由浏览器统一执行。
✅ `-Max-Age` 缓存预检，省掉重复 OPTIONS 往返。
⚠️ 只对浏览器有效，非浏览器客户端可完全绕过，极易被误当成访问控制手段。
⚠️ 预检多一次往返、配置复杂，通配与凭证冲突时新手常配崩。

## 与相关概念的区别

- **vs [[CSRF与SSRF]]**：CORS 管"哪个源能读我的响应"，CSRF 管"冒充已登录用户发写请求"；一个在读端设卡，一个在写端验身份。
- **vs [[XSS 与内容安全]]**：CSP 约束"页面能加载哪些资源"，CORS 约束"能读哪个源的响应"，方向相反且互补。
- **vs JSONP**：JSONP 靠 `<script>` 不受同源限制、只支持 GET、无错误处理，是 CORS 普及前的历史 hack。

## 常见误区

- 配了 CORS 就等于给接口加了鉴权，别人再也拿不到我的数据。
- `Access-Control-Allow-Origin: *` 配合 `withCredentials` 一起用没问题。
- 控制台报 CORS 错误，就说明服务器拒绝了这次请求。

## 面试速答

> 🎯 CORS 是浏览器同源策略的受控放行：默认禁跨源读响应，服务器用 Access-Control-* 头逐项授权源/方法/头，非简单请求先发 OPTIONS 预检，带凭证时 Allow-Origin 不能用 *；它只约束浏览器读取，不是服务器访问控制。
> 🔍 追问：CORS 报错时服务器到底有没有把数据发回来？
> 🔍 追问：为什么带 Cookie 的跨源请求不能让 Allow-Origin 回 `*`？
> 🔍 追问：CSP 与 CORS 分别管哪个方向的跨源？

## 相关术语

[[网络安全篇]]、[[CSRF与SSRF]]、[[XSS 与内容安全]]、[[Web安全攻防]]、[[HTTP协议]]、[[Cookie与Session]]

## 参考资料

建议人工核验：CORS 语义以 WHATWG Fetch / MDN 与对应 RFC 为准；未编造编号与 URL，如需引用请补充具体出处。
