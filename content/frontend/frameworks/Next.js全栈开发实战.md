---
title: "Next.js全栈开发实战"
tags: []
source: "baike"
source_path: "技术文章 / Web开发框架"
collected: "2026-09-05"
status: "imported"
---

# Next.js全栈开发实战

# Next.js 全栈开发实战指南（基于 App Router）

欢迎来到 Next.js 全栈开发的世界！Next.js 13 引入的 App Router 是一个革命性的框架重构，它基于 React Server Components (RSC)，提供了更强大的架构、更精细的性能优化和更优秀的开发体验。本指南将带你深入实战，从核心概念到部署上线，全方位掌握 Next.js 全栈开发。

---

## 1. App Router 架构

App Router 的核心理念是将路由、布局、页面、加载状态和错误处理作为独立的“文件约定”来构建，使得应用结构清晰、功能解耦。

### 1.1 布局 (`layout.tsx`)
布局是跨路由的共享 UI，它不会在页面导航时重新渲染，非常适合放置导航栏、侧边栏等。

```tsx
// app/layout.tsx
import './globals.css'
import { Inter } from 'next/font/google'
import Navbar from '@/components/Navbar'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'My SaaS App',
  description: 'A full-stack SaaS application',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Navbar /> {/* 全局导航栏，不会因页面变化而重新加载 */}
        <main>{children}</main>
      </body>
    </html>
  )
}
```

**嵌套布局**：你可以在子目录中创建 `layout.tsx`，它会包裹其子目录下的所有页面。

```tsx
// app/dashboard/layout.tsx
import Sidebar from '@/components/Sidebar'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex">
      <Sidebar />
      <div className="flex-1">{children}</div>
    </div>
  )
}
```

### 1.2 页面 (`page.tsx`)
页面是路由对应的 UI 组件。默认情况下，`page.tsx` 是 **Server Component**。

```tsx
// app/page.tsx (首页)
export default function Home() {
  return <h1>Welcome to my SaaS</h1>
}

// app/dashboard/page.tsx (仪表盘页面)
export default function DashboardPage() {
  return <div>Dashboard Content</div>
}
```

### 1.3 加载状态 (`loading.tsx`)
当页面数据正在加载时，会自动显示 `loading.tsx` 中的内容。这对于实现 **流式渲染** 和 **骨架屏** 至关重要。

```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
      <div className="h-4 bg-gray-200 rounded w-1/3"></div>
    </div>
  )
}
```

**工作流程**：
1. 用户导航到 `/dashboard`。
2. Next.js 发送 `layout.tsx` 和 `loading.tsx`。
3. `loading.tsx` 立即显示（骨架屏）。
4. `page.tsx` 的数据在服务器上准备好后，通过流式传输替换骨架屏。

### 1.4 错误处理 (`error.tsx`)
`error.tsx` 是一个 **Client Component**，用于捕获其目录及子目录中的运行时错误。

```tsx
// app/dashboard/error.tsx
'use client'

import { useEffect } from 'react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // 可以将错误记录到错误报告服务
    console.error(error)
  }, [error])

  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  )
}
```

---

## 2. 渲染策略

Next.js 提供了多种渲染策略，你可以根据页面的数据需求和用户交互模式灵活选择。

| 策略 | 执行时机 | 数据新鲜度 | 适用场景 |
| :--- | :--- | :--- | :--- |
| **SSR** | 每次请求 | 实时 | 频繁更新的数据、个性化内容 |
| **SSG** | 构建时 | 静态 | 内容不常变化的页面（博客、文档） |
| **ISR** | 构建时 + 间隔刷新 | 可配置 | 内容定期更新的页面（电商产品页） |
| **CSR** | 客户端 | 实时 | 高度交互、个性化仪表盘 |
| **PPR** | 静态壳 + 动态流 | 混合 | 大部分静态、部分动态的页面 |

### 2.1 SSR (Server-Side Rendering)
```tsx
// app/products/[id]/page.tsx
export default async function ProductPage({ params }: { params: { id: string } }) {
  // 数据在每次请求时在服务器获取
  const product = await fetch(`https://api.example.com/products/${params.id}`, {
    cache: 'no-store' // 关键：禁用缓存，强制每次请求都执行
  }).then(res => res.json())

  return <div>{product.name}</div>
}
```

### 2.2 SSG (Static Site Generation)
```tsx
// app/about/page.tsx
export default async function AboutPage() {
  // 数据在构建时获取
  const content = await fetch('https://api.example.com/about').then(res => res.json())

  return <div>{content.text}</div>
}
```

### 2.3 ISR (Incremental Static Regeneration)
```tsx
// app/blog/[slug]/page.tsx
export const revalidate = 60 // 每60秒重新生成页面

export default async function BlogPost({ params }: { params: { slug: string } }) {
  const post = await fetch(`https://api.example.com/posts/${params.slug}`).then(res => res.json())

  return <article>{post.content}</article>
}
```

### 2.4 CSR (Client-Side Rendering)
```tsx
'use client'

import { useState, useEffect } from 'react'

export default function LiveChat() {
  const [messages, setMessages] = useState([])

  useEffect(() => {
    // 数据在客户端获取
    const interval = setInterval(async () => {
      const res = await fetch('/api/messages')
      const data = await res.json()
      setMessages(data)
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return <div>{/* 渲染聊天消息 */}</div>
}
```

### 2.5 PPR (Partial Prerendering) - Next.js 14 新特性
PPR 将页面分为 **静态壳** 和 **动态部分**。静态壳在构建时生成，动态部分在请求时通过流式传输填充。

```tsx
// app/product/[id]/page.tsx
import { Suspense } from 'react'
import ProductInfo from './ProductInfo' // 动态组件
import ProductImages from './ProductImages' // 静态组件

export default async function ProductPage() {
  return (
    <div>
      {/* 静态部分 */}
      <ProductImages />
      
      {/* 动态部分，用 Suspense 包裹 */}
      <Suspense fallback={<div>Loading price...</div>}>
        <ProductInfo />
      </Suspense>
    </div>
  )
}
```

---

## 3. Server Components vs Client Components

这是理解 App Router 的关键。

### 3.1 Server Components (默认)
- **执行环境**：服务器
- **优势**：
  1. **零客户端 JavaScript**：减少包大小。
  2. **直接访问后端资源**：数据库、文件系统、微服务。
  3. **安全**：敏感逻辑（如密钥）不会发送到客户端。
  4. **数据获取性能**：避免客户端-服务器瀑布流。
- **限制**：不能使用 `useState`, `useEffect` 等客户端状态和副作用。

```tsx
// 这是一个 Server Component
export default async function UserList() {
  const users = await db.query('SELECT * FROM users') // 直接查询数据库

  return (
    <ul>
      {users.map(user => <li key={user.id}>{user.name}</li>)}
    </ul>
  )
}
```

### 3.2 Client Components
- **执行环境**：客户端
- **创建方式**：在文件顶部添加 `'use client'` 指令。
- **适用场景**：
  1. **交互**：使用 `useState`, `useReducer`, `useEffect`。
  2. **事件监听器**：`onClick`, `onChange`。
  3. **浏览器 API**：`localStorage`, `window`。
  4. **自定义 Hooks** 依赖以上功能。
  5. **类组件**。

```tsx
'use client'

import { useState } from 'react'

export default function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
}
```

### 3.3 交互最佳实践
将交互部分隔离成最小的 Client Component，从 Server Component 中导入它。

```tsx
// components/AddToCartButton.tsx
'use client'

import { useState } from 'react'

export default function AddToCartButton({ productId }: { productId: string }) {
  const [isAdding, setIsAdding] = useState(false)

  const handleAdd = async () => {
    setIsAdding(true)
    // ... 调用 Server Action
    setIsAdding(false)
  }

  return (
    <button disabled={isAdding} onClick={handleAdd}>
      {isAdding ? 'Adding...' : 'Add to Cart'}
    </button>
  )
}
```

```tsx
// app/products/[id]/page.tsx (Server Component)
import { db } from '@/lib/db'
import AddToCartButton from '@/components/AddToCartButton'

export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await db.product.findUnique({ where: { id: params.id } })

  return (
    <div>
      <h1>{product.name}</h1>
      <p>${product.price}</p>
      {/* 将交互组件嵌入 Server Component */}
      <AddToCartButton productId={product.id} />
    </div>
  )
}
```

---

## 4. 数据获取

App Router 统一了数据获取模式。

### 4.1 Server Actions
Server Actions 是可以直接在 Client Component 中调用的 **服务器端函数**。它们用于处理数据变更（mutations）。

```tsx
// app/actions.ts
'use server'

import { db } from '@/lib/db'
import { revalidatePath } from 'next/cache'

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string
  const content = formData.get('content') as string

  await db.post.create({
    data: { title, content }
  })

  revalidatePath('/posts') // 使相关路径的缓存失效
}
```

```tsx
// components/CreatePostForm.tsx
'use client'

import { createPost } from '@/app/actions'
import { useRef } from 'react'

export default function CreatePostForm() {
  const formRef = useRef<HTMLFormElement>(null)

  return (
    <form ref={formRef} action={async (formData) => {
      await createPost(formData)
      formRef.current?.reset() // 提交后重置表单
    }}>
      <input name="title" required />
      <textarea name="content" required />
      <button type="submit">Create Post</button>
    </form>
  )
}
```

### 4.2 Route Handlers (API Routes)
用于创建自定义的 API 端点。在 `app` 目录下创建 `route.ts` 文件。

```tsx
// app/api/users/route.ts
import { NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function GET() {
  const users = await db.user.findMany()
  return NextResponse.json(users)
}

export async function POST(request: Request) {
  const { name, email } = await request.json()
  const user = await db.user.create({ data: { name, email } })
  return NextResponse.json(user, { status: 201 })
}
```

```tsx
// app/api/users/[id]/route.ts
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const user = await db.user.findUnique({ where: { id: params.id } })
  if (!user) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 })
  }
  return NextResponse.json(user)
}
```

---

## 5. 缓存策略

缓存是 Next.js 性能的核心。

### 5.1 数据缓存 (Data Cache)
**全局、持久化**的 HTTP 缓存层。默认情况下，`fetch` 请求会被缓存。

```tsx
// 强制每次请求都执行（类似 SSR）
const data = await fetch('https://...', { cache: 'no-store' })

// 缓存特定时间（类似 ISR）
const data = await fetch('https://...', { next: { revalidate: 3600 } }) // 1小时
```

### 5.2 完整路由缓存 (Full Route Cache)
构建时，Next.js 会为 **静态路由** 生成 HTML 和 RSC 负载。这个缓存存储在 CDN 上。

- **失效方式**：
  1. 重新部署。
  2. 使用 `revalidatePath` 或 `revalidateTag` 进行按需重验证。
  3. 在动态函数（`cookies()`, `headers()`）或动态 `fetch` 选项中使用数据。

### 5.3 路由缓存 (Router Cache)
**客户端缓存**，用于在用户会话期间存储 RSC 负载。它提供了即时的后退/前进导航体验。

- **存储位置**：浏览器内存。
- **失效**：
  - **静态路由**：缓存5分钟（可通过 `staleTimes` 配置）。
  - **动态路由**：缓存30秒。
  - 当 Server Action 执行后，整个缓存会失效。

### 5.4 缓存策略决策树
```
数据需要非常实时吗？
  ├── 是 → 使用 `cache: 'no-store'` (SSR)
  └── 否 → 数据多久变化一次？
       ├── 变化频繁 → 使用 `revalidate: <seconds>` (ISR)
       └── 很少变化或构建时已知 → 使用默认缓存 (SSG)
```

---

## 6. 中间件和认证

### 6.1 中间件 (`middleware.ts`)
运行在请求完成之前，可用于重写、重定向、设置头信息、认证等。

```tsx
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  const { pathname } = request.nextUrl

  // 保护 dashboard 路由
  if (pathname.startsWith('/dashboard') && !token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // 记录访问日志
  console.log(`Accessed: ${pathname}`)

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*'],
}
```

### 6.2 认证实战 (使用 NextAuth.js)
```tsx
// app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth'
import GithubProvider from 'next-auth/providers/github'
import { PrismaAdapter } from '@auth/prisma-adapter'
import { db } from '@/lib/db'

const handler = NextAuth({
  adapter: PrismaAdapter(db),
  providers: [
    GithubProvider({
      clientId: process.env.GITHUB_ID!,
      clientSecret: process.env.GITHUB_SECRET!,
    }),
  ],
  callbacks: {
    async session({ session, user }) {
      if (session.user) {
        session.user.id = user.id
      }
      return session
    },
  },
})

export { handler as GET, handler as POST }
```

```tsx
// app/layout.tsx
import { SessionProvider } from 'next-auth/react'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <SessionProvider>
          {children}
        </SessionProvider>
      </body>
    </html>
  )
}
```

```tsx
// app/dashboard/page.tsx
import { getServerSession } from 'next-auth'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const session = await getServerSession()
  if (!session) {
    redirect('/login')
  }

  return <div>Welcome, {session.user?.name}!</div>
}
```

---

## 7. 图片和字体优化

### 7.1 图片优化 (`<Image>`)
```tsx
import Image from 'next/image'

export default function Profile() {
  return (
    <Image
      src="/profile.jpg" // 本地或远程图片
      alt="Profile Picture"
      width={500} // 宽度（必需）
      height={500} // 高度（必需）
      placeholder="blur" // 模糊占位符
      blurDataURL="data:image/..." // 可选，自定义占位符
      priority // 首屏图片，优先加载
    />
  )
}
```

**配置 `next.config.js`**：
```js
module.exports = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'example.com',
        pathname: '/account123/**',
      },
    ],
  },
}
```

### 7.2 字体优化
Next.js 自动优化字体，消除外部网络请求。

```tsx
// app/layout.tsx
import { Inter, Playfair_Display } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap', // 指定字体交换策略
})

const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-playfair', // 创建 CSS 变量
  display: 'swap',
})

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.className} ${playfair.variable}`}>
      <body>{children}</body>
    </html>
  )
}
```

```css
/* globals.css */
h1 {
  font-family: var(--font-playfair), serif;
}
```

---

## 8. 国际化 (i18n)

### 8.1 简单方案：使用中间件和路径前缀
```tsx
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const locales = ['en', 'zh', 'es']
const defaultLocale = 'en'

function getLocale(request: NextRequest) {
  const acceptLanguage = request.headers.get('accept-language')
  // 简单的语言检测逻辑
  return defaultLocale
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // 检查路径是否已包含语言前缀
  const pathnameHasLocale = locales.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  )

  if (pathnameHasLocale) return

  // 重定向到带语言前缀的路径
  const locale = getLocale(request)
  request.nextUrl.pathname = `/${locale}${pathname}`
  return NextResponse.redirect(request.nextUrl)
}

export const config = {
  matcher: ['/((?!_next).*)'],
}
```

### 8.2 高级方案：使用 `next-intl`
```tsx
// i18n.ts
export const locales = ['en', 'zh'] as const
export type Locale = (typeof locales)[number]

export const defaultLocale: Locale = 'en'

// messages/en.json
{
  "Home": {
    "title": "Welcome to my SaaS",
    "description": "The best SaaS ever."
  }
}

// app/[locale]/layout.tsx
import { notFound } from 'next/navigation'
import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'

export default async function LocaleLayout({
  children,
  params: { locale }
}: {
  children: React.ReactNode
  params: { locale: string }
}) {
  // 验证语言是否有效
  if (!locales.includes(locale as any)) notFound()

  const messages = await getMessages()

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  )
}

// app/[locale]/page.tsx
import { useTranslations } from 'next-intl'

export default function Home() {
  const t = useTranslations('Home')

  return (
    <div>
      <h1>{t('title')}</h1>
      <p>{t('description')}</p>
    </div>
  )
}
```

---

## 9. 部署

### 9.1 Vercel (最简单)
1. 将代码推送到 Git 仓库（GitHub, GitLab, Bitbucket）。
2. 访问 [vercel.com](https://vercel.com)，导入项目。
3. 配置环境变量。
4. 自动部署，每次 `git push` 都会触发部署。

**优点**：零配置、全球边缘网络、自动 HTTPS、预览部署。

### 9.2 Docker 部署
```dockerfile
# Dockerfile
FROM node:18-alpine AS base

# 安装依赖
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN \
  if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
  elif [ -f package-lock.json ]; then npm ci; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile; \
  else echo "Lockfile not found." && exit 1; \
  fi

# 构建
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN \
  if [ -f yarn.lock ]; then yarn build; \
  elif [ -f package-lock.json ]; then npm run build; \
  elif [ -f pnpm-lock.yaml ]; then pnpm run build; \
  else echo "Lockfile not found." && exit 1; \
  fi

# 生产
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# 自动缓存处理
RUN mkdir .next
RUN chown nextjs:nodejs .next

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

**next.config.js** 配置：
```js
module.exports = {
  output: 'standalone',
}
```

**构建和运行**：
```bash
docker build -t nextjs-docker .
docker run -p 3000:3000 nextjs-docker
```

### 9.3 自托管 (Node.js)
```bash
# 构建
npm run build

# 生产环境启动
NODE_ENV=production node server.js
```

---

## 10. 与 Prisma/Drizzle ORM 集成

### 10.1 Prisma 集成
```bash
# 安装
npm install prisma @prisma/client
npx prisma init
```

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  posts     Post[]
  createdAt DateTime @default(now())
}

model Post {
  id        String   @id @default(cuid())
  title     String
  content   String?
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  String
  createdAt DateTime @default(now())
}
```

```tsx
// lib/prisma.ts
import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const prisma = globalForPrisma.prisma ?? new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
```

```tsx
// app/page.tsx
import { prisma } from '@/lib/prisma'

export default async function Home() {
  const users = await prisma.user.findMany({
    include: { posts: true },
  })

  return (
    <div>
      {users.map(user => (
        <div key={user.id}>
          <h2>{user.name}</h2>
          <ul>
            {user.posts.map(post => (
              <li key={post.id}>{post.title}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
```

### 10.2 Drizzle ORM 集成
```bash
npm install drizzle-orm pg
npm install -D drizzle-kit @types/pg
```

```ts
// drizzle.config.ts
import { defineConfig } from 'drizzle-kit'

export default defineConfig({
  schema: './lib/schema.ts',
  out: './drizzle',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
})
```

```ts
// lib/schema.ts
import { pgTable, text, timestamp, boolean } from 'drizzle-orm/pg-core'

export const users = pgTable('users', {
  id: text('id').primaryKey(),
  name: text('name'),
  email: text('email').notNull().unique(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

export const posts = pgTable('posts', {
  id: text('id').primaryKey(),
  title: text('title').notNull(),
  content: text('content'),
  published: boolean('published').default(false),
  authorId: text('author_id')
    .notNull()
    .references(() => users.id),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})
```

```tsx
// lib/db.ts
import { drizzle } from 'drizzle-orm/node-postgres'
import { Pool } from 'pg'
import * as schema from './schema'

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
})

export const db = drizzle(pool, { schema })
```

```tsx
// app/page.tsx
import { db } from '@/lib/db'
import { users, posts } from '@/lib/schema'

export default async function Home() {
  const allUsers = await db.query.users.findMany({
    with: { posts: true },
  })

  return (
    <div>
      {allUsers.map(user => (
        <div key={user.id}>
          <h2>{user.name}</h2>
          <ul>
            {user.posts.map(post => (
              <li key={post.id}>{post.title}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
```

---

## 11. 实战：构建一个 SaaS 应用

让我们构建一个简化版的 SaaS 应用，包含认证、订阅支付和仪表盘。

### 11.1 项目结构
```
my-saas-app/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── dashboard/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── billing/page.tsx
│   │   └── settings/page.tsx
│   ├── api/
│   │   ├── auth/[...nextauth]/route.ts
│   │   ├── webhooks/stripe/route.ts
│   │   └── subscription/route.ts
│   ├── layout.tsx
│   ├── page.tsx (落地页)
│   └── globals.css
├── components/
│   ├── ui/ (Button, Input, Card 等)
│   ├── Navbar.tsx
│   ├── Sidebar.tsx
│   ├── PricingTable.tsx
│   └── SubscriptionButton.tsx
├── lib/
│   ├── auth.ts (NextAuth 配置)
│   ├── db.ts (Prisma 实例)
│   ├── stripe.ts
│   └── utils.ts
├── prisma/
│   └── schema.prisma
├── middleware.ts
├── next.config.js
└── package.json
```

### 11.2 数据库模型 (Prisma)
```prisma
// prisma/schema.prisma
model User {
  id            String    @id @default(cuid())
  email         String    @unique
  name          String?
  stripeCustomerId String? @unique
  subscriptions  Subscription[]
  createdAt     DateTime  @default(now())
}

model Subscription {
  id                String   @id @default(cuid())
  userId            String
  stripeSubscriptionId String @unique
  stripePriceId     String
  status            SubscriptionStatus
  currentPeriodStart DateTime
  currentPeriodEnd   DateTime
  user              User     @relation(fields: [userId], references: [id])
  createdAt         DateTime @default(now())
}

enum SubscriptionStatus {
  active
  canceled
  incomplete
  incomplete_expired
  past_due
  trialing
  unpaid
}

model Usage {
  id        String   @id @default(cuid())
  userId    String
  feature   String   // 例如: 'api_calls', 'storage_mb'
  amount    Int
  date      DateTime @default(now())
}
```

### 11.3 认证系统
```tsx
// lib/auth.ts
import { NextAuthOptions } from 'next-auth'
import { PrismaAdapter } from '@auth/prisma-adapter'
import GitHubProvider from 'next-auth/providers/github'
import GoogleProvider from 'next-auth/providers/google'
import CredentialsProvider from 'next-auth/providers/credentials'
import bcrypt from 'bcryptjs'
import { db } from './db'

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(db) as any,
  providers: [
    GitHubProvider({
      clientId: process.env.GITHUB_ID!,
      clientSecret: process.env.GITHUB_SECRET!,
    }),
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('Invalid credentials')
        }

        const user = await db.user.findUnique({
          where: { email: credentials.email }
        })

        if (!user || !user.hashedPassword) {
          throw new Error('Invalid credentials')
        }

        const isCorrectPassword = await bcrypt.compare(
          credentials.password,
          user.hashedPassword
        )

        if (!isCorrectPassword) {
          throw new Error('Invalid credentials')
        }

        return user
      }
    })
  ],
  pages: {
    signIn: '/login',
  },
  callbacks: {
    async session({ session, user }) {
      if (session.user) {
        session.user.id = user.id
        session.user.stripeCustomerId = user.stripeCustomerId
      }
      return session
    },
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id
      }
      return token
    }
  },
  session: {
    strategy: 'jwt',
  },
}
```

### 11.4 Stripe 支付集成
```tsx
// lib/stripe.ts
import Stripe from 'stripe'

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
  typescript: true,
})

export async function createOrRetrieveCustomer(email: string, stripeCustomerId?: string) {
  if (stripeCustomerId) {
    const customer = await stripe.customers.retrieve(stripeCustomerId)
    if (!customer.deleted) return customer
  }

  const customer = await stripe.customers.create({
    email,
  })

  return customer
}
```

```tsx
// app/api/webhooks/stripe/route.ts
import { headers } from 'next/headers'
import { stripe } from '@/lib/stripe'
import { db } from '@/lib/db'
import Stripe from 'stripe'

export async function POST(request: Request) {
  const body = await request.text()
  const signature = headers().get('stripe-signature')!

  let event: Stripe.Event

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    )
  } catch (error: any) {
    return new Response(`