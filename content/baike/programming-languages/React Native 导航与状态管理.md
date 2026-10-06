---
title: "React Native 导航与状态管理"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# React Native 导航与状态管理

> 📌 **导航**：本文是 **React Native 导航与状态管理** 词条，属 [[React Native移动应用开发]] 子词条。组件见 [[React Native 组件与布局]]。

## 定义

**一句话定义：** RN 用 React Navigation 以"导航器嵌套"组织页面栈并支持深链，用 Zustand/Jotai 等轻量库管理应用状态——前者管"在哪个屏、如何跳转"，后者管"共享数据与状态更新"。

**通俗类比：** 导航像 App 的"路由与页面栈"（点进详情、返回、外链直达某页）；状态管理像"共享的白板"——各屏读同一份数据、谁改了就受控更新。

## 为什么需要它

移动 App 是"多屏 + 栈式导航 + 深链进入"，需要声明式、可嵌套的路由管理。同时跨屏共享的状态（登录、购物车）若层层传 props 会"prop drilling"，需要外部状态库以最小订阅更新。二者是 RN 应用骨架。

## 核心机制

- **React Navigation**：Stack/Tab/Drawer 导航器，可多层嵌套；`Navigator` 定义路由，`navigation.push/navigate/goBack` 控栈；`Linking` 配置 URL→screen 深链；`useFocusEffect` 感知聚焦。
- **Zustand**：`create` 一个 store（函数式 set/get），组件 `useStore(selector)` 仅订阅所需切片，更新自动触发重渲染，无需 Provider 样板。
- **Jotai**：原子模型，多个可组合的小 atom、按依赖最小更新，适合细粒度派生状态。
- 与 Redux（重一些、actions/中间件）相比更轻，选型看规模与团队。

## 具体示例

Zustand store + 导航跳转：

```jsx
const useCart = create((set) => ({
  items: [], add: (x) => set(s => ({ items: [...s.items, x] })),
}));
// 组件： useCart(s=>s.items) 只订阅 items；点击 navigation.push('Detail',{id})
```

## 何时用与何时不用

- **用**：多屏/标签/抽屉 + 深链进入用 React Navigation；跨屏共享状态用 Zustand（全局）或 Jotai（细粒度原子）。
- **不用**：单屏或极小 App 用本地 state 即可；别为"时髦"把简单状态外部化增加心智。

## 优劣与代价

✅ 声明式可嵌套导航 + 深链、原生手势转场；轻量状态库少样板、按切片订阅省渲染。
✅ 关注点分离：导航与状态各自独立演进。
⚠️ 深嵌套导航器性能/返回栈管理有坑；state 选库多、团队需统一。
⚠️ 不当的订阅粒度仍会引发不必要重渲染。

## 与相关概念的区别

- **Stack vs Tab vs Drawer 导航器**：栈式前进后退 / 平级切换 / 侧滑抽屉。
- **Zustand vs Jotai**：中心化 store+selector vs 原子组合。
- 与 [[MVC 与 MVVM]]：状态管理是"共享状态与视图同步"的工程化落地。

## 常见误区

- 所有状态都必须放全局 store，才叫规范。
- 导航嵌套越深越灵活，不影响性能。
- Zustand 和 Redux 是一回事、没有样板与心智差别。

## 面试速答

> 🎯 导航用 React Navigation：Stack/Tab/Drawer 可嵌套、Linking 做深链、管前进后退栈；状态用 Zustand（create+selector、少样板）或 Jotai（原子组合、细粒度）。导航管"哪个屏/怎么跳"、状态管"共享数据/如何更新"，注意订阅粒度与嵌套导航性能。
> 🔍 追问：为什么需要 selector 订阅而不是整份 store？
> 🔍 追问：深链进入某页大致怎么配？

## 相关术语

[[React Native移动应用开发]]、[[React Native 组件与布局]]、[[MVC 与 MVVM]]、[[Flutter状态管理]]

## 参考资料

建议人工核验：以 React Navigation / Zustand / Jotai 官方文档为准；未编造文献编号。
