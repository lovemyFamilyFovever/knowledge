---
title: "Node 事件循环"
tags: [八股文, Node 与后端]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# Node 事件循环

## 一句话定义

单线程调度加 libuv 线程池，异步 IO 回来再排进队列。

## 面试官为什么问它

考的是他和浏览器事件循环的差别——只会讲宏微任务说明只懂前端那一半。

## 30 秒版回答

Node 的主线程负责执行 JS，真正的阻塞 IO 交给 libuv：内核的 epoll/kqueue 或线程池（默认四到六个线程）做完之后把回调交回事件循环。它按阶段走：timers（到点的 setTimeout）→ pending callbacks → poll（取 IO 事件，这里是主要等待点）→ check（setImmediate）→ close callbacks，而每个阶段之间都会清空微任务队列。和浏览器最大的区别是微任务的清空时机与 `process.nextTick`——它在每个异步操作完成点后立刻跑，比 Promise 回调更早。

## 被追问三层时的诚实边界

我实际遇到的是事件循环被同步代码卡住导致整服务无响应，判断方式是看请求延迟而不是 CPU；`--stack-trace-limit` 与 libuv 内部队列调优我没有实操过，我的理解是排查靠「计时器与 poll 阶段的时间占比」这类观测。

## 本库深挖

- [[Node.js与全栈面试题库 - 50道精选题目]] —— 第 2、6、7、11 题：Node 与浏览器事件循环、nextTick 顺序、libuv 线程池
- [[异步结果与事件循环]] —— 多语言的同一模型
