---
title: "Vue2 与 Vue3 差异"
tags: [八股文, Vue 与前端框架]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# Vue2 与 Vue3 差异

## 一句话定义

响应式换成 Proxy，写法转向组合式，编译期做静态提升。

## 面试官为什么问它

简历同时声称 Vue2 和 Vue3，这是必答的对照题，也顺势验证你懂不懂响应式换代。

## 30 秒版回答

四个层面。响应式：Vue2 用 `Object.defineProperty` 递归劫持，监听不到新增删除属性和数组下标，要靠 `Vue.set`；Vue3 用 Proxy 拦整个对象、惰性深度代理，覆盖更好也更省。API：从 data/methods/created 的选项式转向 setup 组合式，逻辑按关注点组织、能抽 composables，替代了 mixin 的命名冲突问题。编译：静态提升、patch flags、Tree-shaking，包体和更新成本都降。工程：TS 一等公民。迁移的真实成本在老代码的 mixin、全局 API 和过滤器。

## 被追问三层时的诚实边界

我实际做过 Vue2 到 Vue3 的迁移，也读过两边响应式实现；Vue3 编译器 block tree 的具体机制我没有实操过，我的理解是更新性能的提升主要来自它跳过了静态部分。

## 本库深挖

- [[Vue3核心]] —— Vue3 的整体形态
- [[Object.defineProperty 与 Vue 响应式]] —— 换代的技术原因
- [[vue2-reactive-principle]] —— Vue2 侧的实现
