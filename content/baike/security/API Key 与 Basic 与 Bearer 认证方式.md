---
title: "API Key 与 Basic 与 Bearer 认证方式"
tags: []
source: "baike"
source_path: "开发术语 / 安全与加密"
collected: "2026-09-05"
status: "imported"
---

# API Key 与 Basic 与 Bearer 认证方式

> 📌 **导航**：本文是 **API Key 与 Basic 与 Bearer 认证方式** 词条，属于 security 术语集，由 [[认证与授权篇]] 拆分而来。

## 定义

**一句话定义：** 三者都是在 HTTP 请求里携带"凭证"来证明调用方身份的方式——API Key 是一枚静态密钥串、Basic Auth 把 `用户名:密码` 做 Base64 放进头部、Bearer Token 则是"谁持有谁有效"的令牌。

**通俗类比：** API Key 像借书证号，凭号就能认出是谁在借；Basic Auth 像用明信片寄密码，虽然编码了但任何人都能读；Bearer Token 像现金，谁拿到就能花，所以必须贴身保管。

## 为什么需要它

服务端每收到一个请求都得知道"这是谁、允不允许调"。OAuth 与 JWT 解决的是"怎么签发与校验令牌"，而令牌与密钥最终要以某种格式附在请求上——这三种就是最常见的携带方式，也是接口鉴权里被问得最多的"你到底把凭证放哪"。

## 核心机制

| 方式 | 凭证形态 | 放在哪 | 能否主动失效 | 典型场景 |
|------|----------|--------|--------------|----------|
| API Key | 静态长随机串 | `X-API-Key` 头或 Query | 需服务端存表才能吊销 | 服务端对服务端调用、配额计费 |
| Basic Auth | `user:pass` 的 Base64 | `Authorization: Basic <b64>` | 随密码变更 | 内部系统、临时调试 |
| Bearer Token | 短期令牌(常为 JWT) | `Authorization: Bearer <token>` | 靠过期或黑名单 | 登录后 / OAuth 换取的 API 访问 |

- **API Key：** 用密码学随机数生成(如 `secrets.token_urlsafe`)，放 Header 优于 Query——Query 会被访问日志与浏览器历史留存，泄漏面更大；它标识"哪个应用在调"，粒度粗、轮换难。
- **Basic Auth：** Base64 只是编码不是加密，任何人抓包即可解回明文，因此必须叠加 HTTPS；优点是实现极简，缺点是把密码反复送上网络。
- **Bearer Token：** 令牌通常由登录接口或 OAuth 客户端凭证模式换得，响应里带 `token_type: Bearer` 与 `expires_in`；过期后用 refresh token 续期，而它本身多是 JWT 承载(见 [[OAuth 与 JWT]])。

## 具体示例

同一个 `GET /api/data`，三种写法依次是：`X-API-Key: <key>`；`Authorization: Basic dXNlcjpwYXNz`(即 `user:pass` 的 Base64)；`Authorization: Bearer eyJhbGciOi...`。curl 里 `curl -u user:pass URL` 等价于自动帮你拼好 Basic 头。用 Bearer 前一般先 `POST /token` 带 `grant_type=client_credentials` 换一枚 access token，再附在后续请求头上。

## 何时用与何时不用

- **用：** 机器对机器或服务端持有密钥的调用用 API Key；确需简单认证且有 HTTPS 保障时临时用 Basic；凡走 OAuth / 登录换取短期令牌的 API 一律用 Bearer。
- **不用：** 别把 API Key 或密码塞进浏览器端 JS(源码可见即泄漏)；别在生产长期用 Basic 裸传密码；Bearer 令牌泄露即在有效期内可被直接复用，别用超长期令牌图省事。

## 优劣与代价

✅ 三种方式实现成本低、无需前端配合复杂流程，能覆盖从内部调用到公开 API 的大部分鉴权需求。
✅ Bearer 令牌可设短有效期 + refresh 轮换，比静态密钥更接近"可控可撤销"。
⚠️ API Key 与 Basic 都是"给了就一直有效"，泄漏即等于失守，轮换与吊销全靠服务端额外记账。
⚠️ Query 里放密钥、Base64 当加密，是把便捷误当安全的典型事故来源。

## 与相关概念的区别

- **vs [[OAuth 与 JWT]]：** OAuth 2.0 是"怎么安全发令牌"的授权框架、JWT 是令牌的格式，Bearer 只是把已签好的令牌附到请求上的传法。
- **vs [[Cookie与Session]]：** 会话靠浏览器自动携带 Cookie 维持登录态；本族三种都要调用方主动把凭证写进 Header，常见于无 Cookie 的 API/移动端。
- **vs [[访问控制]]：** 本族解决"你是谁/有没有资格进来"(认证)，进来之后"能操作哪些资源"(授权) 才交给访问控制。

## 常见误区

- 以为 Basic Auth 的 Base64 是加密，明文密码没被保护。
- 把 API Key 写进前端代码或放在 Query 参数里长期对外暴露。
- 觉得 Bearer 令牌反正会过期，泄露了也没什么关系。

## 面试速答

> 🎯 三种携带凭证的方式：API Key 是静态串(放头优于放 Query)、Basic 是 Base64(user:pass) 须配 HTTPS、Bearer 是持有即有效的短期令牌(常为 JWT，多由 OAuth 换得)；共同软肋是泄露即可复用，Bearer 靠过期与 refresh 缓解。
> 🔍 追问：为什么 API Key 放 Header 比放 Query 安全？
> 🔍 追问：Basic Auth 的 Base64 和加密差在哪？
> 🔍 追问：Bearer 令牌与 refresh token 的职责如何分工？

## 相关术语

[[认证与授权篇]]、[[OAuth 与 JWT]]、[[Cookie与Session]]、[[访问控制]]、[[认证与安全实践]]、[[HTTPS 与 TLS]]

## 参考资料

建议人工核验：本词条内容建议对照 HTTP 认证相关官方规范（Basic 认证、Bearer 令牌使用）做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
