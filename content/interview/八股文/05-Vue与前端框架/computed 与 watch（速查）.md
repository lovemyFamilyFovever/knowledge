---
title: "computed 与 watch"
tags: [八股文, Vue 与前端框架]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# computed 与 watch

## 一句话定义

computed 是带缓存的派生值，watch 是变化后的副作用。

## 面试官为什么问它

他想验证你分得清「有返回值给模板用」和「没返回值只做事情」，以及缓存到底靠什么。

## 30 秒版回答

computed 描述的是「从别的数据算出一个值」，依赖不变就不重算，所以适合价格合计、过滤列表这类派生；它有缓存是因为依赖收集后记录脏标记，只有依赖变化才重新求值。watch 描述的是「变化了要做一件事」：发请求、联动第三方库、写本地存储，没有返回值。反过来用是坏味道——用 watch 手动把派生值塞进 ref，等于把缓存丢了，还容易漏初始值。

## 被追问三层时的诚实边界

我实际用的是 computed 做条件显隐与格式化，`watchEffect` 只在依赖多且明确时用来做同步；`watch` 的 deep 与 immediate 的开销我踩过（深监听大对象会明显卡），我的理解是那种情况应该改监听具体路径或走 store 的选择器。

## 本库深挖

- [[Vue3核心]] —— computed 的缓存实现角度
- [[前端框架核心概念]] —— 派生值与副作用的通用区分
- [[articles/vue3/index|vue3/index]] —— computed 与 watch 的笔记
