---
title: "Pinia"
tags: [八股文, Vue 与前端框架]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# Pinia

## 一句话定义

以组合式函数为形态的状态层，模块各自持有 state 与 action。

## 面试官为什么问它

他实际问的是「你为什么要全局状态、怎么防止它变成上帝对象」，这是架构品味题。

## 30 秒版回答

Pinia 每个 store 就是一个 setup 函数，state、getter、action 都在里面，没有 Vuex 那套 mutation 的双层仪式。它靠 Vue 的响应式做状态，按需拿模块，天然支持 TS 推断和分模块拆分。我的分工是：跨路由共享且需要持久或需要多处读同一份数据才进 store，父子传值仍走 props 和 emit，否则 store 会吞掉数据流向。

## 被追问三层时的诚实边界

我实际用它管用户态、权限和列表缓存，也做过 store 拆分与避免循环引用；SSR 下的状态序列化我没有实操过，我的理解是 Pinia 那套 toRefs 与 hydration 约定就是为它设计的。

## 本库深挖

- [[前端状态管理]] —— 为什么需要状态层与各方案对比
- [[use]] —— Pinia 的落地写法
- [[pinia-vs-component-props]] —— 什么该进 store 的判据
