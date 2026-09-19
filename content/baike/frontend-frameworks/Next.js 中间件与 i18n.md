---
title: "Next.js 中间件与 i18n"
tags: []
source: "baike"
source_path: "技术文章 / Web开发框架"
collected: "2026-09-05"
status: "imported"
---

# Next.js 中间件与 i18n

> 📌 **导航**：本文是 **Next.js 中间件与 i18n** 词条，属于 frontend-frameworks 术语集。相关枢纽：[[Next.js全栈开发实战]]、[[前端路由]]。

## 定义

**一句话定义：** Next.js 中间件（`middleware.ts`）是在请求到达页面/路由之前、运行于 Edge Runtime 的一次函数，可读请求、改写路径、重定向、增删头；国际化常借它做语言前缀（`/zh/...`）协商，再配合 `next-intl` 与 `[locale]` 动态段按语言加载文案。

**通俗类比：** 中间件像大楼门口的保安——在你进任何房间（页面）之前统一查一下证件（cookie）、决定放行/改道/贴个条；多语言像门牌，按你选的语言把你引到对应楼层，至于楼层里具体说哪句台词由页面组件负责。

## 为什么需要它

路由级横切需求——鉴权重定向、灰度分流、语言协商、统一安全头——若在每个页面重复判断会散落且发生在渲染之后。中间件在边缘、于响应产生前一次性拦截，就近低成本地改写或短路；i18n 希望 URL 带语言前缀以利 SEO 与静态预生成，也天然落在"改写路径"这一层。二者都建立在同一种能力（对 pathname/headers 的前置处理）上，故合并承载。

## 核心机制

- **运行时机与限制**：中间件在 `matcher` 命中的请求上、页面渲染之前执行，跑在 Edge Runtime，可返回 `NextResponse.redirect`/`rewrite`、读写 request/response 头，或 `NextResponse.next()` 放行；它读不到 React 上下文、不宜做重 I/O。
- **matcher 配置**：`export const config = { matcher: [...] }` 用路径模式限定生效范围（常排除 `_next/static`、图片等），把重定向/鉴权限定到需要的路由。
- **鉴权短路**：常见做法是读会话 cookie，未登录访问 `/dashboard` 就 `redirect('/login')`——但会话建立、令牌校验、字段级授权的机制本体不在这，归口 [[认证与安全实践]]·[[访问控制]]·[[OAuth 与 JWT]]，本页只用中间件做"进门前"的粗闸。
- **i18n 两档**：简单方案在中间件按 `accept-language`/cookie 检测、把路径重定向到 `/{locale}/...`；进阶用 `app/[locale]/layout.tsx` + `next-intl`，以 `generateStaticParams` 为每种语言预生成、`getMessages` 按 locale 载文案，无效语言 `notFound()`。

## 具体示例

一次 `/zh/dashboard` 请求：中间件先命中、读 cookie 判断是否登录，未登录 `redirect('/zh/login')`、已登录放行并把 `x-locale: zh` 写进请求头；`app/[locale]/layout.tsx` 据 locale 调 `getMessages()` 载中文文案、并用 `generateStaticParams` 预生成 `/zh`、`/en` 两套——拦截、协商、静态预生成三步一次走通。

## 何时用与何时不用

- **用**：路由级重定向/改写、语言与地区协商、灰度分流、统一安全响应头；URL 需带 locale 前缀做 SEO。
- **不用**：需要查库的细粒度授权与业务级数据过滤别塞进中间件（它无 React 上下文、且早于数据加载）；组件内的状态判断用组件逻辑即可，别滥用边缘拦截。

## 优劣与代价

✅ 边缘就近处理、于响应前短路，避免每页重复鉴权/协商逻辑，语言协商还能配合静态生成。
✅ 中间件 + i18n 前缀让多语言页既 SEO 友好又能 SSG（每种 locale 预生成）。
⚠️ Edge Runtime 能力受限（无 Node API、不宜重计算），把复杂鉴权逻辑塞进来会力不从心。
⚠️ `matcher` 写宽了会在所有请求（含静态资源）上空转，白白增加边缘开销。

## 与相关概念的区别

- **vs [[前端路由]]**：那是 SPA 的 hash/history 客户端路由；中间件是 Next.js 服务端/边缘对真实 URL 的前置改写，两者不同层。
- **vs [[认证与安全实践]]·[[访问控制]]**：认证授权是"谁能访问什么"的机制与策略；中间件只是把这些结论在"进门前"执行的落点之一。
- **vs App Router 布局**：布局管渲染结构，中间件管请求改写，二者都可作用在 `/dashboard` 上但职责正交。

## 常见误区

- 把需要查库的字段级授权写进中间件，既受 Edge 限制、又发生在数据加载之前，判断根本不成立。
- 以为写了 matcher 就万事大吉，matcher 过宽会在静态资源等所有请求上空转。
- i18n 只做重定向却不为 `[locale]` 配 `generateStaticParams`，导致本应静态的多语言页退化成运行时渲染。

## 面试速答

> 🎯 Next.js 中间件在匹配路由、页面渲染前于 Edge 运行，可读 cookie/头做重定向、改写、加头；i18n 借它做 /{locale} 前缀协商并配 next-intl+generateStaticParams 预生成，字段级授权与认证机制归口既有专条、别塞进中间件。

## 相关术语

[[Next.js全栈开发实战]]、[[Next.js App Router 与渲染策略]]、[[前端路由]]、[[认证与安全实践]]、[[访问控制]]、[[OAuth 与 JWT]]、[[Cookie与Session]]

## 参考资料

建议人工核验：可对照 Next.js 官方 Middleware 与 i18n 文档、next-intl 文档复核。本篇取自原稿 §6 中间件与 §8 国际化，原稿数段 tsx 示例按 v1.2 §8.1 收敛为要点散文；认证/授权机制本体归口既有 done 专条不重复承载。
