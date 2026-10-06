---
title: "JavaScript 异步编程（事件循环·Promise·async·await·Generator）"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# JavaScript 异步编程（事件循环·Promise·async·await·Generator）

> 📌 **导航**：本文是 **JavaScript 异步编程（事件循环·Promise·async·await·Generator）** 词条，属于 frontend-concepts 术语集。相关枢纽：[[JavaScript 基础核心概念]]、[[前端框架核心概念]]。

## 定义

**一句话定义：** JS 单线程，靠事件循环在同步代码跑完后依次清空微任务队列、再取一个宏任务执行；Promise 是异步结果的可组合容器，async/await 是它的同步写法，Generator 是可暂停可恢复的函数——四者合起来构成 JS 的异步栈。

**通俗类比：** 像餐厅服务员：先把手上那桌的菜上完（同步代码），VIP 加单（微任务）一律插队到当前这轮结束前处理完，再去厨房端下一份普通菜（一个宏任务）。

## 为什么需要它

单线程不能有阻塞式等待，否则页面直接冻住，事件循环让"发起请求后继续跑"成为默认。Promise 把异步结果变成可组合、可传递、只结算一次的值，取代回调地狱；async/await 再把它写成线性可读、能 try/catch、能打断点的代码。

## 核心机制

- **事件循环与两条队列**：调用栈清空后先跑微任务直到队列空（`Promise.then`、`MutationObserver`），再取一个宏任务（`setTimeout`、`setInterval`、I/O、UI 渲染），如此往复。宏任务每轮一个、微任务整队清空，这是所有"为什么我的回调排在后面"的唯一判据，顺序题实测见下方示例。
- **Promise**：pending → fulfilled / rejected 只结算一次；`.then/.catch/.finally` 链式组合。组合子分工：`all` 全成才成、一个失败即失败（其余不会取消，只是结果被忽略），`race` 取最先结算者（含失败），`allSettled` 等全部结束并给出每项 `status/value/reason`。
- **async/await**：async 函数恒返回 Promise，await 把"等结果"写成同步形状，错误统一交 try/catch。并发要靠先发起再 `Promise.all` 等齐，而不是在循环里逐个 await——后者把并发串成瀑布。
- **Generator**：`function*` + `yield` 每次暂停并交出 `{ value, done }`，`next(v)` 可把值注回内部；用于惰性求值与自定义迭代器（`for...of` 消费），也是 async/await 的底层形状（协程一般模型见 [[协程]]）。

## 具体示例

```javascript
console.log("1");
setTimeout(() => console.log("宏"));      // 排入宏任务
Promise.resolve().then(() => console.log("微"));
console.log("4");                          // 1 → 4 → 微 → 宏

async function loadDash() {
  const [u, p] = await Promise.all([        // 先并发发起再等齐
    fetch("/api/user").then(r => r.json()),
    fetch("/api/posts").then(r => r.json()),
  ]);
  return { u, p };
}
function* range(start, end) { for (let i = start; i < end; i++) yield i; }
```

## 何时用与何时不用

- **用**：互不依赖的多请求先并发再 `Promise.all`；有依赖的串行 await；超时竞速用 `race`；多接口容错用 `allSettled`；按需产出的序列用 Generator。
- **不用**：别再手工 `new Promise` 包一层 await（async 函数本身就返回 Promise）；也别把 `setTimeout(fn, 0)` 当"下一轮"的精确调度，它只保证排在队尾。

## 优劣与代价

✅ async/await 让异步代码可调试、可 try/catch，认知成本回到同步水平。
✅ Promise 组合子把并发编排变成声明式数据结构，易测易复用。
⚠️ 微任务整队清空意味着递归 `Promise.resolve().then()` 可以饿死宏任务与渲染。
⚠️ 长时间占住调用栈的同步循环同样饿死事件循环，表现就是掉帧（拆片与调度见 [[JS执行性能]]）。

## 与相关概念的区别

- **vs [[协程]]**：Generator 是 JS 给协程开的口子（可暂停可恢复），await 只恢复不交出执行权；调度模型在那条。
- **vs [[并发编程（Concurrent Programming）概念]]**：那条讲多线程共享与竞态，本条是单线程内的任务编排。
- **vs [[JavaScript 作用域与 this]]**：回调里的变量由词法作用域与 [[闭包]] 持有，事件循环只决定何时执行，不改作用域。

## 常见误区

- 以为 `setTimeout(fn, 0)` 会让 fn 立即执行，它只是被排进宏任务队尾。
- 以为 await 之后的代码要等到下一个宏任务才执行，它其实是 Promise 结算后排入的微任务续体。
- 以为 `Promise.all` 里有一个失败，其余 Promise 会被取消。

## 面试速答

> 🎯 栈清空→微任务整队清空→取一个宏任务，故同步 → 微任务 → 宏任务；Promise 一次性结算可组合（all/race/allSettled），async/await 是它的同步写法、并发要 Promise.all，Generator 可暂停是底层形状。

## 相关术语

[[JavaScript 基础核心概念]]、[[协程]]、[[并发编程（Concurrent Programming）概念]]、[[闭包]]、[[JS执行性能]]、[[JavaScript 作用域与 this]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇合并原《JavaScript 基础核心概念》的事件循环与任务队列、Promise、async/await、Generator 函数四节（原稿含 ASCII 流程图，此处按"微任务整队清空"的文字判据承载，不重复一份）；原稿该四节无截断。
