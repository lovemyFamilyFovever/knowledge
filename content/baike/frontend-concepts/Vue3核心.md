---
title: "Vue3核心"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# Vue3核心


> 📌 **导航**：本文是 **Vue3核心** 词条，属于 frontend-concepts 术语集。相关枢纽：[[HTML & CSS 核心概念]]、[[JavaScript 基础核心概念]]、[[React深入]]、[[Vue3核心]]、[[前端工程化核心概念]]。

## 定义

**一句话定义：** Vue3 核心是 Proxy 响应式系统 + Composition API 逻辑复用 + 编译期静态提升与 PatchFlag 差量更新的三位一体设计。

**通俗类比：** 像装修全屋智能系统——Proxy 是所有电灯的门磁传感器（谁开了哪盏灯精确知道），Composition API 是模块化的功能面板（按需组装），编译优化是提前布好线只通电到会变的灯。

## 为什么需要它

Vue2 的 Object.defineProperty 无法拦截新增/删除属性和数组索引赋值；Options API 在组件 >500 行时逻辑分散难复用；全量 VDOM diff 在静态内容多的页面浪费性能——Vue3 三个设计逐一解决。

## 核心机制

**响应式（Proxy）**：new Proxy 拦截 get/set——get 时 track 收集依赖（哪个组件/effect 读了哪个属性），set 时 trigger 精确触发订阅者更新。可监听任意属性操作包括 delete 和数组索引。

**Composition API**：setup 函数内用 ref/computed/watch 组织逻辑，可按关注点拆分为可组合函数（composables），解决 Options API 逻辑碎片化问题。

**编译优化**：模板编译时标记动态节点（PatchFlag），静态内容提升到渲染函数外只创建一次，Block Tree 扁平化使 diff 仅遍历动态节点——从 O(n) 全量对比降为 O(动态节点数)。

## 具体示例

一个商品列表：模板中静态标题/表头被 HoistStatic 提升不重复创建；每个 item 的价格和库存标记 PatchFlag(PROPS)，只有这两个属性变化时 diff 才触及该节点；composable usePagination() 封装翻页逻辑在多个列表复用。

## 何时用与何时不用

- **用**：新 Vue 项目直接采用；从 Vue2 迁移时 Composition API 逐组件推进。
- **不用**：简单模板 + 少量状态，Options API 也能用——不必强迫所有逻辑搬进 setup。

## 优劣与代价

✅ Proxy 无死角响应式，不再需要 Vue.set/$set。
✅ 逻辑复用粒度从 Mixin（命名冲突）升级为函数级组合。
✅ Tree-shaking 友好——不用的 API 不打进 bundle。
⚠️ Composition API 学习曲线高于 Options API，团队需统一代码风格。

## 与相关概念的区别

- **vs React Hooks**：两者都实现逻辑组合复用，但 React 靠调用顺序链表（不能条件调用），Vue 靠 ref 对象引用（可条件、可任意传递）；React 每次 render 重新执行函数，Vue setup 只执行一次。
- **vs Vue2 响应式**：Vue2 用 defineProperty 逐属性劫持（初始化时无法监听后加属性），Vue3 用 Proxy 整体代理对象。

## 常见误区

- ref 和 reactive 功能完全一样只是写法不同。
- 响应式数据解构后依然能追踪变化。
- Vue3 性能提升主要来自 Composition API。

## 面试速答

> 🎯 Vue3 = Proxy 精确依赖追踪 + Composition API 函数级逻辑复用 + 编译期 PatchFlag 跳过静态节点；响应式是 get 时 track、set 时 trigger，不是脏检查也不是全量 diff。
> 🔍 追问：ref 和 reactive 的区别与选型？
> 🔍 追问：为什么解构 reactive 对象会丢失响应性？

## 相关术语

[[HTML & CSS 核心概念]]、[[JavaScript 基础核心概念]]、[[React深入]]、[[前端工程化]]、[[前端工程化核心概念]]、[[前端框架核心概念]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
