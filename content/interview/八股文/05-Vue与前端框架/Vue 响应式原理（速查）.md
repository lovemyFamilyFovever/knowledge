---
title: "Vue 响应式原理"
tags: [八股文, Vue 与前端框架]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# Vue 响应式原理

## 一句话定义

劫持数据的读写，读时记依赖，写时通知更新的函数。

## 面试官为什么问它

这是他验证你「用过还是懂」的招牌题。说到依赖收集、effect、以及 Vue2 的漏网之处才算答完。

## 30 秒版回答

响应式就是给数据装一层拦截：读到某个属性时，把当前正在运行的副作用记成这个属性的依赖；写入时，把收集到的依赖重新执行，组件重渲染。Vue2 用 `Object.defineProperty` 逐层递归劫持 getter/setter，所以有已知盲区——新增删除属性、改数组下标和长度都监听不到，得靠 `Vue.set` 和重写数组方法。Vue3 换成 `Proxy`，能拦整个对象的操作，配 `Reflect` 保证 this 正确，还改成惰性深度代理，性能和覆盖面都更好。

## 被追问三层时的诚实边界

我实际读过 Vue2 源码的依赖收集那条线（Dep、Watcher 到渲染 watcher），也清楚 Vue3 用 Proxy 重写的原因；自己从 0 写一个完整响应式系统我没有实操过，我的理解是它的难点不在代理本身，在依赖清理与调度。

## 本库深挖

- [[Object.defineProperty 与 Vue 响应式]] —— 从 defineProperty 到 Proxy 的演进
- [[vue2-reactive-principle]] —— Vue2 侧的实现拆解
- [[Vue3核心]] —— Vue3 响应式的工程用法
