---
title: "Rust Web 认证与授权"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Rust Web 认证与授权

> 📌 **导航**：本文是 **Rust Web 认证与授权** 词条，属 [[Rust Web开发实战]] 子词条。中间件机制见 [[Axum 路由与中间件]]。

## 定义

**一句话定义：** Rust Web 的认证授权=用 JWT（自包含签名令牌，`jsonwebtoken`）验证"你是谁"、用 OAuth2（授权码流程，`oauth2`）经第三方身份提供方委托登录，再在 Axum 中间件里把校验过的用户注入请求供 handler 做授权判断。

**通俗类比：** JWT 像一张带防伪公章的"临时工牌"（自己就能验真伪、免查后端）；OAuth2 像"用微信/谷歌扫码替你开门"（把身份验证外包给可信平台，本服务只拿回授权码换令牌）。

## 为什么需要它

HTTP 无状态，服务必须每次请求都能确认调用者身份与权限，否则任何接口都裸奔。JWT 让无状态服务无需会话存储即可验签取身份；OAuth2 让用户不必把密码交给第三方 App、由可信 IdP 统一认证。二者是 Web API 安全的标配组合，也直接影响越权、盗用等 OWASP 高危项。

## 核心机制

- **JWT 签发**：`Claims{ sub, email, role, exp, iat }` → `encode(Header::default(), &claims, EncodingKey::from_secret(secret))` 得到字符串令牌。
- **JWT 校验**：`decode::<Claims>(token, DecodingKey::from_secret(secret), &Validation::new(HS256))`，`set_required_spec_claims(&["exp","sub"])` 强制过期与主体，签名或过期即失败。
- **认证中间件**：从 `Authorization: Bearer <token>` 取串、验签得 `claims`、`request.extensions_mut().insert(claims)`，失败返 `401`（见 [[Axum 路由与中间件]]）。
- **OAuth2 授权码流程**：`client.authorize_url(CsrfToken::new_random).add_scope(...)` 生成跳转 URL → 用户同意回调带 `code`+`state` → 服务端校验 `state` 防 CSRF → `exchange_code(code)` 换 `access_token` → 拉用户信息建/更用户 → 再签本方 JWT。

## 具体示例

```rust
// 校验 JWT 并注入用户
fn validate(secret:&str, token:&str)->Result<Claims,jsonwebtoken::errors::Error>{
  let mut v=Validation::new(Algorithm::HS256);
  v.set_required_spec_claims(&["exp","sub"]);
  Ok(decode::<Claims>(token,&DecodingKey::from_secret(secret.as_bytes()),&v)?.claims)
}
```

## 何时用与何时不用

- **用**：无状态 API / 微服务用 JWT（配短过期 + 刷新令牌）；需"用 Google/微信登录"或对接企业 SSO 用 OAuth2/OIDC。
- **不用**：需要即时吊销、强会话控制的场景，纯 JWT 难即时失效（要靠黑名单/短 TTL）；内部完全可信网络外的公开只读接口不必强上认证。

## 优劣与代价

✅ JWT 无状态、跨服务易传递、验签便宜；OAuth2 委托认证、用户不暴露密码给第三方。
✅ 与 tower 中间件天然结合，鉴权集中、handler 只取已验证的 claims。
⚠️ 密钥泄露=令牌可伪造；HS256 共享密钥扩到多服务时宜用 RS256 非对称。
⚠️ JWT 难即时吊销、体积大；OAuth2 回调/state/时钟偏移等安全细节多，易出错。

## 与相关概念的区别

- **认证 vs 授权**：认证回答"你是谁"（JWT/OAuth2 确认身份）；授权回答"你能做什么"（据 `role`/scope 判权限）。
- **JWT vs 会话 Cookie**：前者自包含无服务端态、后者服务端存 session 便于即时失效。
- **OAuth2 vs OIDC**：OAuth2 是"授权框架"，OIDC 在其上加了一层身份层（`id_token`）。

## 常见误区

- JWT 是加密的，别人看不到里面内容，所以可以放密码。
- 只要验签通过就是有效令牌，不用管 `exp`。
- OAuth2 的 `state` 参数可有可无，不影响安全。

## 面试速答

> 🎯 认证授权两件套：JWT（`jsonwebtoken` 签验 `Claims{sub,exp}`、Bearer 中间件注入用户、无状态）；OAuth2 授权码流程（带 state 防 CSRF、回调换 token、再签本方 JWT）。认证=谁、授权=能干啥，别忘校验 exp 与 state。
> 🔍 追问：为什么 JWT 难做即时吊销？
> 🔍 追问：HS256 与 RS256 何时选哪个？

## 相关术语

[[Rust Web开发实战]]、[[Axum 路由与中间件]]、[[API 错误处理规范]]、[[serde 序列化与反序列化]]、[[密码学基础]]

## 参考资料

建议人工核验：以 jsonwebtoken / oauth2 crate 与 RFC 6749/7519 为准；未编造具体 URL，如需引用请补充出处。
