---
title: "ref 与 reactive"
tags: [八股文, Vue 与前端框架]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# ref 与 reactive

## 一句话定义

ref 包一个值靠 .value 访问，reactive 代理一个对象直接改。

## 面试官为什么问它

考的是你会不会踩两个经典坑：解构 reactive 丢响应式，以及 ref 在模板和脚本里的用法差异。

## 30 秒版回答

ref 内部是一个带 get/set 的对象，所以任何地方都要 `.value`（模板里自动解包），好处是能包基本类型、也不会因为传递丢响应。reactive 是 Proxy 对象，写法自然，但解构出来的是普通值，赋值整体替换也会断掉响应。我的实践是：基本类型一律 ref，对象用 reactive 但不解构、或配合 `toRefs`；组件对外暴露和跨模块传递时更偏爱 ref，因为不会被误改。

## 被追问三层时的诚实边界

我实际项目里以 ref 为主、对象状态放 store，就是为了避开解构断响应这一类 bug；`customRef` 和 `toRef` 我没有实操过，我的理解是它们主要服务于「把 props 透传成可写状态」这种边界场景。

## 本库深挖

- [[Vue3核心]] —— 两种声明的语义差别
- [[Object.defineProperty 与 Vue 响应式]] —— 为什么代理对象不能解构
