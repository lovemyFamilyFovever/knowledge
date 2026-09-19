---
title: "CSRF 与 SSRF"
tags: []
source: "baike"
source_path: "技术文章 / DevOps与运维"
collected: "2026-09-05"
status: "imported"
---

# CSRF 与 SSRF

> 📌 **导航**：本文是 **CSRF 与 SSRF** 词条，属 [[Web安全攻防实战指南]] 子词条。

## 定义

**一句话定义：** CSRF（跨站请求伪造）借受害者浏览器自动携带的 Cookie，冒充其身份向已登录站点发非本意请求；SSRF（服务器端请求伪造）则诱使服务器代替攻击者向内网/外系统发请求，用于打内网、读云元数据。

**通俗类比：** CSRF 像"骗子趁你登录着网银、用你的身份按下转账按钮"；SSRF 像"骗公司前台替你给内部部门跑一趟"——外人进不去内网，但服务器能。

## 为什么需要它

CSRF 利用"浏览器自动带 Cookie"这一默认行为，一个 `<img>`/自动提交表单就能以受害者身份改密、转账。SSRF 在云与微服务时代尤其危险：应用常能访问内网和云元数据端点，被诱导后成为打内网的跳板、泄露临时凭证。

## 核心机制

- **CSRF 防御**：① **Anti-CSRF Token**（表单与会话存随机 token、提交时校验，最推荐）；② **SameSite Cookie**（Lax 阻断大部分第三方 POST、Strict 更严）；③ Origin/Referer 校验（不可单独依赖）；④ 关键操作二次验证。
- **SSRF 防御**：① URL 白名单（协议/域名/IP）；② 禁 `file://`/`gopher://`/`dict://` 等非必要协议；③ 网络隔离——限制服务器可达内网范围；④ 云元数据 `169.254.169.254` 用 IMDSv2（需令牌）并禁止直接访问；⑤ 不把目标响应原样回显。

## 具体示例

`SameSite=Lax` + CSRF Token 是 CSRF 的主力防线：

```http
Set-Cookie: session=xyz; SameSite=Lax; Secure; HttpOnly
```

SSRF 侧务必校验解析后的 URL 并限制协议，禁止对内网/元数据 IP 发起请求。

## 何时用与何时不用

- **用**：所有改变状态的接口都要 CSRF Token + SameSite；任何"根据用户提供的 URL 去请求"的功能都要 SSRF 白名单 + 网络隔离。
- **不用**：别只靠 Referer 判 CSRF（可缺省/伪造）；别只把 URL 里的 `127.0.0.1` 字符串过滤掉就以为防住 SSRF（可用内网 IP、DNS 重绑定绕过）。

## 优劣与代价

✅ Token+SameSite 对 CSRF 近乎根治；SSRF 白名单+网络隔离大幅收窄内网面。
✅ 多为可统一实施的中间件/网关策略。
⚠️ SameSite=Strict 影响外链体验；Token 需在所有改状态接口覆盖、易漏。
⚠️ SSRF 白名单需解析后 IP 校验、防 DNS 重绑定，纯字符串过滤易被绕。

## 与相关概念的区别

- **CSRF vs XSS**：CSRF 是"借你已登录的身份发请求"（无需读页面）；XSS 是"注入脚本盗取/操作"（见 [[XSS 与内容安全]]）。
- **CSRF vs SSRF**：前者让受害者浏览器发请求、冒充用户；后者让服务器自己发请求、打服务端可达的内网。
- **SameSite vs Token**：SameSite 是浏览器侧强兜底，Token 是服务端校验，二者叠加。

## 常见误区

- 校验了 Referer/Origin 头就能单独、可靠地防住 CSRF。
- 把 URL 里的 127.0.0.1 过滤掉就防住了 SSRF。
- SameSite=Lax 已经能挡住所有 CSRF 场景，无需再上 Token。

## 面试速答

> 🎯 CSRF=浏览器自动带 Cookie 冒充用户发请求，防御靠 Anti-CSRF Token+SameSite+Origin 校验+关键操作二次验证；SSRF=诱使服务端向内/外发请求(读云元数据)，防御靠 URL 白名单+禁危险协议+网络隔离+IMDSv2。一个冒充用户、一个借服务器之手。
> 🔍 追问：CSRF 和 SSRF 分别"借用"了谁的身份？
> 🔍 追问：为什么过滤 127.0.0.1 挡不住 SSRF？

## 相关术语

[[Web安全攻防实战指南]]、[[XSS 与内容安全]]、[[Linux 网络管理]]

## 参考资料

建议人工核验：以 OWASP CSRF Prevention / SSRF Prevention Cheat Sheet 为准；未编造文献编号。
