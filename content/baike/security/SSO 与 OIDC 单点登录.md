---
title: "SSO 与 OIDC 单点登录"
tags: []
source: "baike"
source_path: "开发术语 / 安全与加密"
collected: "2026-09-05"
status: "imported"
---

# SSO 与 OIDC 单点登录

> 📌 **导航**：本文是 **SSO 与 OIDC 单点登录** 词条，属于 security 术语集，由 [[认证与授权篇]] 拆分而来。

## 定义

**一句话定义：** SSO(单点登录)让用户只需登录一次即可访问多个互相信任的系统；OIDC(OpenID Connect)则是建在 OAuth 2.0 之上的身份认证层，用一枚 id_token 回答"你是谁"，是实现 SSO 的现代标准之一。

**通俗类比：** SSO 像校园一卡通，刷一次就能进宿舍、图书馆、食堂；OIDC 则像"驾照+身份证"的组合——OAuth 只证明你能开车(授权)，OIDC 还额外亮出姓名与证件号(身份)。

## 为什么需要它

企业内十几个系统各要一次账号密码，既造成"密码疲劳"、逼用户把弱密码复用到处处，也让离职回收权限变成噩梦。SSO 把"证明身份"这件事收敛到一个中心(身份提供商 IdP)，各业务系统只信任它签发的凭据；而 OAuth 2.0 本身只管授权、不定义身份，于是需要在其上补一层 OIDC 来标准化"认证"。

## 核心机制

| 维度 | CAS 式 SSO | OIDC(基于 OAuth 2.0) |
|------|-----------|----------------------|
| 登录产物 | 一次性票据 Ticket(ST) | id_token(JWT) + access_token |
| 应用校验方式 | 后端回调 validate 验票 | 验 id_token 签名与 claims |
| 适配套路 | 传统企业 Web 系统 | 社交登录、移动与 SPA |
| 身份表达 | 票据里带用户标识 | claims:sub / name / email |

- **SSO 的根是一个可信 IdP：** 用户访问应用 A 时未登录，被重定向到 SSO 中心，登录后中心发一张票据回到 A，A 再回中心验票；此后访问应用 B，中心发现会话已存在就直接发票、无需再输密码——"信任同一 IdP"是这一切成立的前提。
- **OIDC 的关键增量是 id_token：** 授权码流程与 OAuth 几乎一致，区别在 `scope` 带上 `openid`，令牌响应里多回一枚 JWT 格式的 id_token，其中 `sub` 是用户在 IdP 侧的稳定标识，应用据此建立本地会话。
- **SSO 是目标，OIDC 是手段之一：** 实现 SSO 还可走 SAML(XML、偏企业 Web)，OIDC 更轻量、更适合移动端与 API(见 [[OAuth 与 JWT]])。

## 具体示例

用户点"用某大厂账号登录"：应用把浏览器重定向到 IdP 的 `/authorize?response_type=code&scope=openid profile email`；用户在 IdP 完成登录(可能已登录则直接放行)；IdP 带一次性 code 回跳，应用用 code 去 `/token` 换回 `{access_token, id_token, token_type: Bearer}`；应用验签 id_token、读出 `name` 与 `email`，随后在自己域内下发会话 Cookie(见 [[Cookie与Session]])。企业多系统场景里，这一跳登录态被多个应用共享，就是 SSO 的体现。

## 何时用与何时不用

- **用：** 企业内部多系统统一登录、减少密码疲劳与集中权限回收；接入社交登录(Google / Microsoft)、需要跨应用免重复登录；只要"授权第三方访问资源"不需要身份时，纯 OAuth 2.0 即可、无需 OIDC。
- **不用：** 单一独立系统别引入 SSO 的中心化复杂度与 IdP 单点故障；只关心机器间授权不必叠加身份层。

## 优劣与代价

✅ 一次登录处处可用，降低弱密码复用风险，权限随 IdP 集中管控、离职即时回收。
✅ OIDC 借 OAuth 成熟流程叠加身份，标准统一、对移动与 SPA 友好。
⚠️ IdP 成为单点故障与高价值攻击目标，一旦被攻破等于所有下游系统失守。
⚠️ 信任链与令牌校验配置链条长(重定向 URI、scope、签名算法)，错一环即成漏洞。

## 与相关概念的区别

- **vs OAuth 2.0：** OAuth 是"授权"(能替我做什么)，OIDC 在其上加"认证"(你是谁)；把"走通 OAuth 登录"当成"完成身份认证"是常见混淆。
- **vs SAML：** SAML 用 XML 断言、面向传统企业 Web SSO；OIDC 用 JSON/JWT、更适合移动端与 API。
- **vs 多因子认证：** SSO 管"登录一次跨多系统"，[[MFA 多因素认证]] 管"这一次登录要用几类因子证明"，二者正交、可叠加。

## 常见误区

- 以为接了 OAuth 2.0 登录，就等于做好了用户身份认证。
- 把 id_token 当 access_token 拿去调资源 API。
- 认为 SSO 只是 OAuth 的另一个名字。

## 面试速答

> 🎯 SSO 让一次登录访问多个互信系统，根在统一可信的 IdP；OIDC 是在 OAuth 2.0 授权之上加的身份认证层，用带 openid scope 换回的 id_token(JWT) 回答"我是谁"，比 SAML 更轻量、适合移动与 SPA。
> 🔍 追问：为什么说 OAuth 本身不做身份认证？
> 🔍 追问：id_token 与 access_token 各自用途是什么？
> 🔍 追问：SSO 相比 SAML，OIDC 的优势体现在哪？

## 相关术语

[[认证与授权篇]]、[[OAuth 与 JWT]]、[[Cookie与Session]]、[[MFA 多因素认证]]、[[访问控制]]、[[认证与安全实践]]

## 参考资料

建议人工核验：本词条内容建议对照 CAS 协议与 OpenID Connect 官方规范做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
