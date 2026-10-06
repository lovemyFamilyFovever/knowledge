---
title: "Next.js App Router 与渲染策略"
tags: []
source: "baike"
source_path: "技术文章 / Web开发框架"
collected: "2026-09-05"
status: "imported"
---

# Next.js App Router 与渲染策略

> 📌 **导航**：本文是 **Next.js App Router 与渲染策略** 词条，属于 frontend-frameworks 术语集。相关枢纽：[[Next.js全栈开发实战]]、[[前端框架核心概念]]。

## 定义

**一句话定义：** App Router 是 Next.js 用文件系统即路由的架构——`app/` 下 layout/page/loading/error/not-found 各成路由树一个节点；渲染策略不再全局设定，而由页面或组件用 `fetch` 选项、`revalidate` 与 `Suspense` 就地声明"这段 HTML 何时、在哪生成"。

**通俗类比：** 文件树像楼层图纸，放对牌子框架就自动装配电梯（路由）；渲染策略像每层自选"工厂预制、现场浇筑还是住户自装"，同栋楼里预制与现浇可共存。

## 为什么需要它

Pages Router 的 getServerSideProps/getStaticProps 绑死在页面一级、一页只能选一种策略，局部动态被迫整页 SSR。App Router 把粒度下沉到组件：静态壳与动态片段可同页并存、布局跨导航不重渲染、加载与错误成一等文件约定；代价是渲染时机从集中配置变处处决策，选错影响首屏、SEO 与成本。

## 核心机制

文件约定是骨架：`layout.tsx` 共享 UI 且不重渲染、`page.tsx` 是路由终点、`loading.tsx` 给流式骨架屏、`error.tsx`（须 Client Component）捕获子树错误、`not-found.tsx` 承载 404、`route.ts` 把目录变 API 端点；括号路由组 `(dashboard)` 只组织目录、不改 URL。渲染策略是血肉，五档按数据何时确定排布：

| 策略 | HTML 何时生成 | 数据新鲜度 | 典型场景 | 开关 |
|---|---|---|---|---|
| SSG | 构建时 | 静态 | 文档、营销页 | 默认无动态 API |
| ISR | 构建时+后台刷新 | 可配 TTL | 商品页、博客 | `revalidate=N` |
| SSR | 每次请求 | 实时 | 个性化、强动态 | `cache:'no-store'` |
| CSR | 客户端 | 实时 | 高度交互 | `'use client'`+effect |
| PPR | 静态壳+动态流 | 混合 | 多静少动 | `Suspense` 边界 |

- **流式渲染**：`loading.tsx`/`<Suspense fallback>` 先吐静态壳与骨架，慢数据就绪再以 chunk 流式补上，解耦首字节与可交互（加载时机见 [[资源加载优化]]）。
- **PPR**：静态壳构建时定稿、动态区请求时流式填充，是 SSG 与 SSR 同页合流，免去为一小块动态整页 SSR。
- **动态 API 隐式切 SSR**：页面一旦读 `cookies()`/`headers()` 或用 `no-store`，该路由落出完整路由缓存、每次动态渲染，是易误伤的隐式选择（分层见 [[Next.js 缓存与再验证]]）。

## 具体示例

```tsx
export const revalidate = 3600      // 整页 ISR：每小时后台再生
export default async function Page({ params }) {
  const product = await getProduct(params.id)   // 静态：构建/再生时取
  return (<>
    <ProductImages product={product} />
    <Suspense fallback={<StockSkeleton />}><LiveStock id={params.id} /></Suspense>
  </>)
}
```

## 何时用与何时不用

- **用**：内容/营销站优先 SSG+ISR；实时个性化或会话片段用 SSR/PPR 局部降级；需共享布局与每路由独立错误/加载态用文件约定。
- **不用**：全站纯客户端交互（后台）用 [[前端路由]] 的 SPA 更轻；数据每次必须全实时则直接 SSR。

## 优劣与代价

✅ 渲染粒度下沉到组件，静态快与动态新可同页共存；文件约定让路由/加载/错误/布局零配置。
✅ 流式与 PPR 改善感知性能与首字节，缓存随部署或再验证自动更新。
⚠️ "隐式动态"陷阱——一处 `cookies()` 就让整路由变 SSR、静态缓存失效不易察觉；策略档位多而交叉，选型要判断数据变化频率。

## 与相关概念的区别

- **vs [[前端框架核心概念]]**：那里给 SSR/SSG/CSR 的跨框架定义，本页只讲 App Router 如何落地。
- **vs Pages Router**：后者一页绑死一种 data-fetching 方法，App Router 让每组件自选渲染时机并支持流式。
- **vs [[React Server Components 与数据获取]]**：本页管"何时出 HTML"、RSC 管"组件在哪跑"，两者正交。

## 常见误区

- 以为 App Router 只能整页选一种策略，其实 PPR/Suspense 允许静态壳与动态片段并存。
- 随手用了 `cookies()`，没意识到它把整条路由从静态降级成每次请求的 SSR。
- 把 `error.tsx` 写成 Server Component，导致无法捕获运行时错误——它必须是 Client Component。

## 面试速答

> 🎯 App Router 用文件约定把路由/布局/加载/错误组织成树，渲染策略下沉到组件级：SSG/ISR 靠 revalidate、SSR 靠 no-store、CSR 靠 use client，PPR 让静态壳与动态流同页共存；注意 cookies() 会隐式把整路由变成 SSR。

## 相关术语

[[Next.js全栈开发实战]]、[[前端框架核心概念]]、[[React Server Components 与数据获取]]、[[Next.js 缓存与再验证]]、[[资源加载优化]]、[[前端路由]]、[[Web性能优化]]

## 参考资料

建议人工核验：可对照 Next.js 官方 App Router / 渲染策略文档复核。本篇取自原《Next.js全栈开发实战》§1 App Router 架构 与 §2 渲染策略，原稿多段 tsx 示例按 v1.2 §8.1 收敛为散文、策略表与一段最小示例，未新增原稿没有的性能数字。
