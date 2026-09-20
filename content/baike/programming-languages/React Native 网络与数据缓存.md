---
title: "React Native 网络与数据缓存"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# React Native 网络与数据缓存

> 📌 **导航**：本文是 **React Native 网络与数据缓存** 词条，属 [[React Native移动应用开发]] 子词条。

## 定义

**一句话定义：** RN 网络层把 `fetch`/axios 封装成统一客户端（拦截器、超时/重试、鉴权注入），数据缓存用 TanStack Query / Apollo 管理服务端状态（缓存、失效、后台刷新、乐观更新），减少重复请求并改善离线与加载体验。

**通俗类比：** 像给 App 装"前台 + 仓库"：网络层统一收发、贴工牌（token）、失败重打；缓存层把取过的数据存仓、按新鲜度决定复用还是刷新，用户下次秒开。

## 为什么需要它

移动端网络慢、断线多、重复请求费流量与电量；散落的 fetch 难统一错误/鉴权/取消。把传输与"服务端状态缓存"分层：统一拦截、按 key 缓存去重、失效重取、乐观更新——既省请求又让加载/离线体验一致。

## 核心机制

- **网络客户端**：baseURL、请求/响应拦截器注入 token 与统一报错、超时/AbortController 取消、重试与错误分类。
- **服务端状态（TanStack Query）**：`useQuery(key, fn)` 缓存 + `staleTime`/`gcTime` 控制新鲜度、`refetchOnFocus` 前台刷新、`mutation` 乐观更新与回滚、按 key 去重。
- **本地持久化**：AsyncStorage/MMKV 存键值（与"服务端状态缓存"区分）。
- GraphQL 则用 Apollo 做规范化缓存与分页。

## 具体示例

```javascript
// 拦截器统一注入鉴权 + TanStack Query 缓存
api.interceptors.request.use(c => { c.headers.Authorization = `Bearer ${token}`; return c; });
const { data } = useQuery({ queryKey: ['user', id], queryFn: () => api.get(`/users/${id}`).then(r=>r.data), staleTime: 60_000 });
```

## 何时用与何时不用

- **用**：反复读取的远端资源用 Query 缓存 + staleTime；跨屏统一鉴权/错误用拦截器；需乐观更新提升手感。
- **不用**：一次性/不缓存的数据别过度包装；本地 UI 状态交给状态管理（见 [[React Native 导航与状态管理]]），别塞进缓存层。

## 优劣与代价

✅ 请求去重、缓存秒开、失效/后台刷新、错误与鉴权集中处理。
✅ 乐观更新让交互更跟手。
⚠️ 缓存一致性/失效策略需设计，错配会显示陈旧数据。
⚠️ 引入抽象与库，调试链路变长。

## 与相关概念的区别

- **服务端状态 vs 客户端状态**：前者来自后端、需缓存/同步（Query）；后者纯本地 UI 态（[[React Native 导航与状态管理]]）。
- **Query 缓存 vs AsyncStorage**：前者管"接口数据的新鲜度"、后者管"键值持久化"。
- 与后端 [[API 分页与版本控制]]、[[API 错误处理规范]] 协同。

## 常见误区

- 所有请求都该缓存、设越长的 staleTime 越好。
- 乐观更新失败不需要回滚与提示。
- 客户端状态和服务端状态该混在一个全局 store 里管理。

## 面试速答

> 🎯 网络层：封装 fetch/axios + 拦截器（注入鉴权、统一错误/超时/取消/重试）。数据缓存：TanStack Query 按 key 管服务端状态——缓存+staleTime/gcTime、焦点重取、mutation 乐观更新、去重；本地持久化用 AsyncStorage/MMKV，与缓存层分工、防陈旧。
> 🔍 追问：为什么服务端状态要单独用 Query 管、不放 Redux/Zustand？
> 🔍 追问：staleTime 与 gcTime 有何不同？

## 相关术语

[[React Native移动应用开发]]、[[React Native 导航与状态管理]]、[[API 分页与版本控制]]、[[API 错误处理规范]]

## 参考资料

建议人工核验：以 axios/TanStack Query 文档为准；未编造文献编号。
