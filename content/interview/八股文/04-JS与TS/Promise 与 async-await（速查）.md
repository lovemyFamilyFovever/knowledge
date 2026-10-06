---
title: "Promise 与 async-await"
tags: [八股文, JavaScript 与 TypeScript]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# Promise 与 async-await

## 一句话定义

Promise 是可组合的结果占位，await 是把链写成直式。

## 面试官为什么问它

他想验证你懂不懂「await 不等于串行」——并发控制是现代前端性能的关键，也是最容易答错的点。

## 30 秒版回答

Promise 是一个状态机：pending 到 fulfilled 或 rejected，只变一次；then 返回新 Promise，所以能链式，异常沿链向下找最近的 catch。async 函数总是返回 Promise，await 把后续代码注册成微任务续体。要点有两个：错误要用 try/catch 且别吞；不相互依赖的请求要 Promise.all 一起发，写在循环里逐个 await 就变成串行。

## 被追问三层时的诚实边界

我实际处理最多的是并发上限控制与超时保护——本地检索链路就明确要求 1500ms 超时后降级，不能靠单个请求卡住整页；Promise.allSettled 与聚合错误上报我做过，我的理解是异步局部失败比整页失败更可接受。

## 本库深挖

- [[JavaScript 异步编程（事件循环·Promise·async·await·Generator）]] —— 状态、链式与异常传播
- [[异步结果与事件循环]] —— 多语言视角的同一模型
