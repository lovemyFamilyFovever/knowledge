---
title: "React Server Components 与数据获取"
tags: []
source: "baike"
source_path: "技术文章 / Web开发框架"
collected: "2026-09-05"
status: "imported"
---

# React Server Components 与数据获取

> 📌 **导航**：本文是 **React Server Components 与数据获取** 词条，属于 frontend-frameworks 术语集。相关枢纽：[[Next.js全栈开发实战]]、[[React深入]]。

## 定义

**一句话定义：** React Server Components（RSC）是默认在服务器渲染、不向客户端发送自身 JS 的组件；`'use client'` 标客户端交互边界、`'use server'` 标可从客户端调用的服务端函数（Server Actions），Route Handler 提供 HTTP 端点——App Router 用这套指令统一"组件在哪跑、数据怎么取、变更怎么提交"。

**通俗类比：** 像餐厅后厨与大堂分工——多数菜（数据、逻辑、密钥）在后厨（服务器）做好端上，只有要顾客自己加辣、互动的才把调料台（客户端 JS）放进大堂。

## 为什么需要它

传统 SPA 把取数、鉴权、ORM 全塞进客户端，带来首屏瀑布、包体积膨胀、敏感逻辑暴露三个问题。RSC 把数据获取下沉到组件就地 `await`（可直连数据库），减往返与打包 JS、密钥不出服务器；要交互才划 `'use client'` 边界、把副作用隔离到最小。这条"能留服务器就留服务器"是 App Router 相对传统 React 最核心的心智转变（组件与 Hooks 本体见 [[React深入]]）。

## 核心机制

| 维度 | Server Component（默认） | Client Component |
|---|---|---|
| 执行环境 | 只在服务器 | 服务器预渲染 + 客户端 hydration |
| 可用能力 | async/await 直连数据源、读密钥 | `useState`/`useEffect`、事件、浏览器 API |
| 是否进客户端 bundle | 否（零自身 JS） | 是 |
| 标记方式 | 无需指令 | 文件顶部 `'use client'` |

- **边界由叶子向上传染**：一旦某模块标 `'use client'`，其 import 图内组件都进入客户端上下文；故把交互隔离成最小客户端叶子、由服务端组件包裹，才最大化服务器渲染收益。
- **数据获取就地化**：服务端组件直接 `const users = await db.query(...)`，多取数在同组件内并发、不再形成客户端→API→服务器→DB 瀑布；跨边界 props 必须可序列化，函数与 Class 实例传不过去（Server Action 引用除外）。
- **Server Actions 改数据**：`'use server'` 函数可从客户端表单直接调用做 mutation，成功后 `revalidatePath`/`revalidateTag` 触发缓存失效（详见 [[Next.js 缓存与再验证]]），无需手写 fetch + 状态管理。
- **Route Handlers 对外端点**：`app/**/route.ts` 导出 `GET`/`POST` 等，用于 webhooks、第三方集成等非 RSC 消费场景（REST 语义见 [[RESTful API 设计]]）。

## 具体示例

一个"用户列表 + 计数按钮"：`page.tsx`（服务端）`await db.user.findMany()` 取数渲染，把 `Counter` 标 `'use client'` 作最小交互叶子嵌进去，其 onClick 调 `'use server'` 的 `increment()`、末尾 `revalidatePath('/users')`——取数在服务端、交互在叶子、变更走 Action、失效靠 revalidate。

## 何时用与何时不用

- **用**：首屏/SEO 关键、需直连数据库或内部服务、含敏感逻辑——留服务端；只有交互（表单、点击、依赖 `window`）才 `'use client'`。
- **不用**：全站高度交互、几乎无服务端数据时，纯客户端 React 更直观，别为用 RSC 强行拆分。

## 优劣与代价

✅ 减少客户端 JS 与网络瀑布，敏感逻辑与密钥留服务器，数据获取贴近使用处、组合简单。
✅ Server Actions 让 mutation 从"写表单+fetch+更新缓存+setState"收敛成一次函数调用。
⚠️ 两套运行时的边界规则（序列化限制、指令传染）是主要复杂度来源，划错边界会把整棵子树拖进客户端；服务端组件不能用 state/effect，依赖浏览器 API 的逻辑必须下沉。

## 与相关概念的区别

- **vs [[React深入]]**：React 提供组件/Hooks/Fiber 且跑客户端；RSC 是其上的"服务器优先渲染"。
- **vs 传统 API + SPA**：那边以 HTTP 为边界、数据客户端取；这边以组件树为边界、数据服务端就地取。
- **vs [[前端状态管理]]**：客户端状态仍归状态库；RSC 管"渲染在哪发生、数据从哪来"，二者互补。

## 常见误区

- 以为 `'use client'` 组件就不在服务器跑——它仍服务器预渲染，只是多把 JS 发到客户端做 hydration。
- 把整页标成 Client Component 图方便，结果 RSC 的"零客户端 JS、服务器直连数据"收益全丢。
- 试图把函数或 Class 实例当 props 越过服务器→客户端边界传递，违反序列化限制而报错。

## 面试速答

> 🎯 RSC 默认在服务器渲染、不发自身 JS，能 await 直连数据源、藏密钥；交互用最小 `'use client'` 边界下探、变更用 `'use server'` 的 Server Action（配合 revalidate 失效缓存），对外端点用 Route Handler，跨边界 props 必须可序列化。

## 相关术语

[[Next.js全栈开发实战]]、[[Next.js App Router 与渲染策略]]、[[Next.js 缓存与再验证]]、[[React深入]]、[[前端状态管理]]、[[RESTful API 设计]]、[[认证与安全实践]]

## 参考资料

建议人工核验：可对照 Next.js 官方 Server Components / Server Actions 文档复核。本篇取自原稿 §3 Server vs Client Components 与 §4 数据获取，原稿十余段 tsx 示例按 v1.2 §8.1 收敛为对照表与散文，未新增原稿没有的数据。
