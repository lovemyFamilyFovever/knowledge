---
title: "OAuth 与 JWT"
tags: [信息安全, OAuth, JWT]
source: "baike"
source_path: "开发术语 / 信息安全"
collected: "2026-09-12"
status: "imported"
---

# OAuth 与 JWT


> 📌 **导航**：本文是 **OAuth 与 JWT** 词条，属于 security 术语集。相关枢纽：[[公钥基础设施]]、[[密码学基础篇]]、[[零信任安全架构]]。

## 定义

**一句话定义：** OAuth 是一个**授权**框架,允许用户授权第三方应用在有限范围内访问其在另一服务上的资源,而无需交出密码;JWT(JSON Web Token)是一种紧凑、自包含的令牌格式,用签名承载声明(claims),常在 OAuth / OpenID Connect 中传递身份与权限。

**通俗类比：** OAuth 像"代客泊车钥匙"——你把只能开车门、启动却开不了后备箱的有限钥匙(令牌)交给泊车员(第三方应用),而不必交出全部家当(账号密码);JWT 则像一张盖了防伪章的通行证,写明"持证人可做什么",验证方凭章即可确认真伪,无需回总部查询。

## 为什么需要它

OAuth 之前,第三方要读你的 GitHub 仓库只能索要账号密码——一次交出全部权限,既无法限定范围也无法单独回收。OAuth 把"你是谁"和"你能替我做什么"拆开,用短期令牌承载可撤销的窄权限。而服务端若为此保存会话,横向扩容就要共享 session;JWT 用签名把状态写进令牌本身,验证方本地验签即可,顺手解决了无状态扩缩容这半个问题。

## 核心机制

- **OAuth 2.0 角色:** 资源所有者(用户)、客户端(第三方应用)、授权服务器、资源服务器。
- **授权模式:** 授权码模式(authorization code,最安全,配合 PKCE)、客户端凭证模式、密码模式;隐式模式已不推荐。
- **令牌分工:** access token 访问资源、短期有效;refresh token 只用来换取新的 access token。
- **JWT 结构:** `Header.Payload.Signature` 三段 Base64URL;Payload 含 claims(iss/sub/exp/aud 等);用 HMAC(对称)或 RSA/ECDSA(非对称)签名防篡改。

## 具体示例

你在 Notion 点"用 GitHub 登录":Notion 生成随机 code_verifier,把它的 SHA-256 摘要作为 code_challenge 随跳转带上;你在 GitHub 侧确认授权(scope 只给读),GitHub 带一次性 code 重定向回 Notion;Notion 再附上原始 code_verifier 去令牌端点,GitHub 校验摘要对得上才签发 access token + refresh token。此后每次调用都带 `Authorization: Bearer <token>`;若这个令牌是 JWT,exp 到期就得靠 refresh token 续期,而不是重新登录。

## 何时用与何时不用

- **用:** 第三方登录("用 GitHub / 微信登录")、单点登录(SSO,配合 OpenID Connect)、微服务与 API 鉴权、移动端与 SPA 的无状态认证。
- **不用:** 需要即时封号/强会话控制的场景(纯无状态 JWT 做不到,别硬套);无用户参与的机器对机器调用直接走客户端凭证模式;不要把 JWT 当加密信封来装敏感数据。

## 优劣与代价

✅ 不暴露密码,权限按 scope 细分且能单独回收。
✅ JWT 自包含、服务端不存会话,天然利于水平扩展。
⚠️ 主动注销困难:这是无状态的代价,需黑名单或短有效期 + refresh token 轮换兜底。
⚠️ 配置链条长、易出错(重定向 URI、scope、PKCE 一处配错即成漏洞);令牌一旦泄露在有效期内可被直接复用。

## 与相关概念的区别

- **vs OpenID Connect:** OIDC 建在 OAuth 2.0 之上,额外签发 id_token 来回答"你是谁";OAuth 本身只回答"你能做什么"。
- **vs SAML:** SAML 用 XML 断言、面向企业 Web SSO;JWT 紧凑、适合移动端与 API 场景。
- **vs 传统 session + Cookie:** 会话状态存服务端、能即时失效;JWT 状态在令牌里,撤销必须另建机制。

## 常见误区

- JWT 的 Payload 是加密的,别人拿到令牌也读不到里面的内容。
- 走通了 OAuth 登录,就等于完成了用户身份认证。
- JWT 签发后服务端随时可以把它注销掉。

## 面试速答

> 🎯 OAuth 解决授权不解决认证,JWT 是签名而非加密的自包含令牌;换令牌用授权码+PKCE,代价是主动吊销困难。
> 🔍 追问：为什么隐式模式被废弃、而推荐授权码 + PKCE?
> 🔍 追问：无状态 JWT 想做主动注销,黑名单方案的代价是什么?
> 🔍 追问：access token 与 refresh token 的职责边界在哪里?

## 相关术语

[[认证与授权篇]]、[[数字签名]]、[[公钥基础设施]]、[[HTTP协议]]、[[Web安全攻防]]

## 参考资料

建议人工核验:OAuth 2.0 见 RFC 6749、授权码 PKCE 见 RFC 7636、JWT 见 RFC 7519、OpenID Connect 由 OpenID Foundation 规范;具体编号建议人工核验。
