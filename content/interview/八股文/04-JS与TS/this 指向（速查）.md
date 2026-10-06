---
title: "this 指向"
tags: [八股文, JavaScript 与 TypeScript]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# this 指向

## 一句话定义

this 由调用方式决定，箭头函数则继承外层。

## 面试官为什么问它

这题他有标准四问：普通调用、方法调用、new、call/apply/bind，外加箭头函数——答漏一条就扣一条。

## 30 秒版回答

按优先级判：显式 bind/call/apply 最大；其次 new，指向新实例；再次方法调用，指向点号左边那个对象；最后独立调用，严格模式是 undefined、非严格是 globalThis。箭头函数没有自己的 this，它定义时就从外层词法作用域拿——这也是回调里最怕 this 丢的时候该用它的原因。

## 被追问三层时的诚实边界

我实际遇到的多是事件回调和 setTimeout 里丢上下文，解法是箭头函数或一次性 bind；Vue2 里把 methods 自动绑定到实例这类框架行为我读过源码，我的理解是它就是在挂载时对函数做了 bind。

## 本库深挖

- [[JavaScript 作用域与 this]] —— 四种绑定规则
- [[call-apply-bind]] —— 三者差别与手写 bind
- [[IIFE]] —— 立即执行与 this 的历史坑
