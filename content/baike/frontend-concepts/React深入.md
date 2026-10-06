---
title: "React深入"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# React深入


> 📌 **导航**：本文是 **React深入** 词条，属于 frontend-concepts 术语集。相关枢纽：[[HTML & CSS 核心概念]]、[[JavaScript 基础核心概念]]、[[React深入]]、[[Vue3核心]]、[[前端工程化核心概念]]。

## 定义

**一句话定义：** React 深入指理解其渲染引擎从 Virtual DOM 到 Fiber 可中断架构、Hooks 链表状态管理和并发调度的内部实现原理。

**通俗类比：** 用开车类比——Virtual DOM 是导航规划路线，Fiber 是把长途驾驶拆成一段段可休息可插队的行程，Hooks 是车上固定的储物格（顺序不可乱）。

## 为什么需要它

面试和性能调优需要超越 API 使用层面：为什么 Hooks 不能条件调用？为什么大列表渲染会卡顿？React 18 的 Transition 做了什么？理解内部机制才能正确诊断和修复性能问题。

## 核心机制

**Hooks 原理**：组件每次渲染按调用顺序在链表/数组中存取状态，index 即身份——因此条件/循环调用会错位。setState 触发的是调度更新而非同步重渲。

**Fiber 架构**：React 16 将递归不可中断的渲染改为可中断的链表遍历。每帧执行若干 Fiber 单元（beginWork/completeWork），超时让出主线程。分为 Render 阶段（可中断）和 Commit 阶段（同步不可中断）。

**并发模式（Concurrent Mode）**：基于优先级调度——用户输入（高优）可打断数据筛选（低优）渲染。startTransition 标记可被打断的低优更新，保持输入响应不卡顿。

**Server Components**：组件在服务端执行后只发送序列化结果到客户端，不传输自身 JS 代码——减少 bundle 体积；交互逻辑通过 'use client' 标记的客户端组件承担。

## 具体示例

搜索页面输入时：setInputValue（高优）立即响应渲染输入框；startTransition 包裹的 setSearchResults（低优，需过滤万条数据）若渲染到一半被新输入打断，丢弃中间结果重新开始——用户打字始终流畅。

## 何时用与何时不用

- **用**：性能瓶颈排查、面试解释 React 工作原理、设计并发交互。
- **不用**：日常 CRUD 开发——API 层使用无需了解 Fiber 细节。

## 优劣与代价

✅ 可中断渲染消除大组件树造成的帧率卡顿。
✅ Server Components 显著减少客户端 JS 体积。
⚠️ 内部机制变更频繁（Fiber 设计从 16 到 19 持续演进），过度依赖实现细节可能升级时踩坑。

## 与相关概念的区别

- **vs Vue3 响应式**：React 用"渲染函数重执行+链表 diff"驱动 UI 更新，Vue3 用 Proxy 精确追踪依赖并仅更新受影响节点——前者更简单粗暴（重跑整个组件函数），后者更精细（按需更新）。

## 常见误区

- Virtual DOM 比真实 DOM 操作更快。
- setState 是同步更新状态的。
- React 组件每次渲染都重建函数，所以状态存在组件函数里。

## 面试速答

> 🎯 React 核心演进：Stack 递归 → Fiber 可中断遍历 → 并发优先级调度 → RSC 服务端执行；Hooks 按调用顺序存链表、setState 触发调度而非同步更新。
> 🔍 追问：为什么 Hooks 不能放在 if 里？
> 🔍 追问：Render 阶段和 Commit 阶段的区别是什么？

## 相关术语

[[HTML & CSS 核心概念]]、[[JavaScript 基础核心概念]]、[[Vue3核心]]、[[前端工程化]]、[[前端工程化核心概念]]、[[前端框架核心概念]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
