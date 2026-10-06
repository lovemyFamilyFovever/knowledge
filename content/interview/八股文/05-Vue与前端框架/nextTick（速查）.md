---
title: "nextTick"
tags: [八股文, Vue 与前端框架]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# nextTick

## 一句话定义

等这次数据变更引起的 DOM 更新完成后，再执行你的回调。

## 面试官为什么问它

考的是「响应式是异步更新」这条你是否知道——很多人以为赋值立刻反映到 DOM。

## 30 秒版回答

因为数据变更到 DOM 更新是异步的：状态一改，更新任务被排进微任务队列合并执行，所以紧接着读 DOM 还是旧的。`nextTick` 把回调放到这一轮 flush 之后，Vue3 里它返回 Promise。典型用法是改完数据要聚焦输入框、量测元素尺寸、或和第三方图表同步。

## 被追问三层时的诚实边界

我实际用的场景是弹窗里初始化编辑器与滚动定位；自己实现一个 nextTick（微任务多方案降级）我没写过，我的理解是浏览器现在有 Promise 微任务就够了，历史上才需要 setImmediate 兜底。

## 本库深挖

- [[sourcecode]] —— nextTick 在更新队列里的位置
- [[JavaScript 异步编程（事件循环·Promise·async·await·Generator）]] —— 为什么这是微任务
