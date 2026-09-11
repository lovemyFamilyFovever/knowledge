---
title: "OAuth 与 JWT"
tags: [信息安全, OAuth, JWT]
source: "baike"
source_path: "开发术语 / 信息安全"
collected: "2026-09-12"
status: "imported"
---

# OAuth 与 JWT

## 定义

**一句话定义：** OAuth 是一个**授权**框架,允许用户授权第三方应用在有限范围内访问其在另一服务上的资源,而无需交出密码;JWT(JSON Web Token)是一种紧凑、自包含的令牌格式,用签名承载声明(claims),常在 OAuth / OpenID Connect 中传递身份与权限。

**通俗类比：** OAuth 像"代客泊车钥匙"——你把只能开车门、启动、却开不了后备箱的有限钥匙(令牌)交给泊车员(第三方应用),而不必交出全部家当(账号密码);JWT 则像一张盖了防伪章的通行证,写明"持证人可做什么",验证方凭章即可确认真伪,无需回总部查询。

> 多义说明:OAuth 解决**授权**(authorization),OpenID Connect(基于 OAuth 2.0)解决**认证**(authentication);JWT 是令牌的一种**格式**。三者常一起使用但概念不同。

## 原理与机制

- **OAuth 2.0 角色:** 资源所有者(用户)、客户端(第三方应用)、授权服务器、资源服务器。
- **授权模式:** 授权码模式(authorization code,最安全,配合 PKCE)、客户端凭证模式、密码模式;隐式模式已不推荐。
- **令牌:** access token(访问资源,短期有效)+ refresh token(换取新的 access token)。
- **JWT 结构:** `Header.Payload.Signature` 三段 Base64URL;Payload 含 claims(iss/sub/exp/aud 等);用 HMAC(对称)或 RSA/ECDSA(非对称)签名防篡改。

## 关键组成

| 组成 | 作用 |
|------|------|
| OAuth 角色 | 用户/客户端/授权服务器/资源服务器 |
| 授权码 + PKCE | 安全的令牌获取流程 |
| access / refresh token | 访问与续期 |
| JWT 三段结构 | Header / Payload / Signature |
| claims | 令牌携带的声明(主体、有效期等) |

## 应用场景

- 第三方登录("用 GitHub / 微信登录")
- 单点登录(SSO,配合 OpenID Connect)
- 微服务与 API 鉴权
- 移动端与 SPA 的无状态认证

## 优点与局限

- 优点:不暴露密码、细粒度授权;JWT 无状态、易水平扩展(服务端无需存会话)。
- 局限:配置复杂、易出错;JWT 主动注销/失效困难(无状态的代价,需黑名单或短有效期);令牌泄露有风险;OAuth 本身不等于认证(需 OIDC)。

## 常见误区

- OAuth 是"授权"不是"认证",认证应使用 OpenID Connect。
- JWT 的 Payload 只是 Base64URL **编码**而非加密,任何人可解码读取,故不能放敏感明文。
- JWT "无状态"导致主动吊销困难,应设短有效期 + refresh token 轮换。

## 相关术语

[[认证与授权篇]]、[[数字签名]]、[[公钥基础设施]]、[[HTTP协议]]、[[Web安全攻防]]

## 参考资料

建议人工核验:OAuth 2.0 见 RFC 6749、授权码 PKCE 见 RFC 7636、JWT 见 RFC 7519、OpenID Connect 由 OpenID Foundation 规范;具体编号建议人工核验。
