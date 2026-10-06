---
title: "MVVM"
tags: [八股文, 设计模式]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# MVVM

## 一句话定义

ViewModel 持有可观察状态，View 与它双向绑定。

## 面试官为什么问它

这是前端候选人必答，因为他紧接着会问「那 Vue 的响应式怎么实现绑定」。

## 30 秒版回答

MVVM 的改动是让 View 和 ViewModel 通过数据绑定连起来：你只改数据，界面自己更新；用户操作也让数据更新，不需要手写 DOM 同步。Vue 就是最典型的落地——组件是 View，setup 里的响应式状态加方法近似 ViewModel。我把 Vue 归到 MVVM 而不是 MVC，因为绑定层替掉了 Controller 的胶水。

## 被追问三层时的诚实边界

我实际用 Vue2/Vue3 做了多年，清楚 ViewModel 在工程里其实就是组件加 store；「MVVM 里的 V 和 VM 边界」各家定义不统一，我的理解是别把它当教条，重点是数据驱动和单向数据流的取舍。

## 本库深挖

- [[MVC 与 MVVM]] —— MVC/MVVM 的演化线
- [[Object.defineProperty 与 Vue 响应式]] —— 绑定层的实现
