---
title: "Flutter路由与导航"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Flutter路由与导航

> 📌 **导航**：本文是 **Flutter 路由与导航** 词条，属 [[Flutter跨平台开发实战]] 子词条。数据流见 [[Flutter状态管理]]。

## 定义

**一句话定义：** Flutter 路由与导航负责在不同页面/Screen 之间切换并管理返回栈；GoRouter 以声明式的 route 树 + 路径模板 + 重定向，提供深链、命名路由与鉴权守卫等能力。

**通俗类比：** 像"带地址栏和重定向规则的浏览器"：每条 route 是一个可寻址的 URL，进不去的页会被自动 redirect 到登录页。

## 为什么需要它

命令式 Navigator 用栈 push/pop 管理页面简单，但复杂 App 需要：可分享的深链、按路径参数解析、进入某页前的鉴权重定向、底部导航+嵌套路由。GoRouter 把这些用声明式配置统一起来，减少手工栈管理出错。

## 核心机制

- **route 树**：`GoRoute(path, builder)` 声明式注册，支持嵌套与 `pathParameters`/`queryParameters` 解析。
- **导航 API**：`context.go('/path')`（替换栈）、`push`（入栈）、`pop`；配合 ShellRoute 做底部 tab 等布局壳。
- **重定向 redirect**：进入前按登录态/权限把用户导去登录页或回跳，实现路由级守卫。
- 深链：URL → 匹配 route → 直达对应页面（配合平台 deep link 配置）。

## 具体示例

声明式路由 + 未登录重定向：

```dart
GoRouter(
  redirect: (c, state) =>
      loggedIn ? null : (state.matchedLocation == '/login' ? null : '/login'),
  routes: [
    GoRoute(path: '/', builder: (_, __) => Home()),
    GoRoute(path: '/user/:id',
      builder: (_, s) => UserProfile(id: s.pathParameters['id']!)),
  ],
);
```

## 何时用与何时不用

- **用**：多页、需深链/参数/守卫/嵌套 tab 的中大型 App（GoRouter）；简单栈式跳转用原生 Navigator 即可。
- **不用**：一两屏的小工具别引入整套路由配置的复杂度。

## 优劣与代价

✅ 声明式、可深链、集中守卫，替代易错的命令式栈管理。
✅ ShellRoute/嵌套路由贴合底部导航等真实形态。
⚠️ 学习曲线、配置样板比裸 Navigator 多；重定向逻辑易成环。
⚠️ 依赖第三方包（GoRouter），需随版本维护。

## 与相关概念的区别

- **go vs push**：go 把导航栈"重置到目标"、push 在栈上压新页、pop 回退。
- **GoRouter vs 命名路由**：后者只提供 name→page 映射，缺参数/重定向/深链等能力。
- 与 Web 前端路由（见 [[MVC 与 MVVM]]）思想同源：路径驱动视图 + 守卫。

## 常见误区

- `context.go()` 和 `Navigator.push()` 效果完全一样。
- redirect 里想跳哪就跳哪，不用担心循环。
- 有了命名路由就等于有了深链与鉴权守卫。

## 面试速答

> 🎯 Flutter 路由管理页面栈与寻址；GoRouter 用声明式 route 树 + 路径/查询参数 + redirect 守卫 + ShellRoute 嵌套，支持深链与集中鉴权。go 重置栈、push 入栈、pop 回退；redirect 做路由级权限、注意别成环。简单 App 用原生 Navigator 即可。
> 🔍 追问：go 和 push 的区别？
> 🔍 追问：路由守卫靠什么机制实现？

## 相关术语

[[Flutter跨平台开发实战]]、[[Flutter状态管理]]、[[MVC 与 MVVM]]

## 参考资料

建议人工核验：以 GoRouter 官方文档与 Flutter Navigation 文档为准；未编造文献编号。
