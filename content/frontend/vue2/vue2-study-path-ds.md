---
title: "vue2-study-path-ds"
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/vue2-study-path-ds.md"
---



下面是一个分阶段的学习计划，按从易到难、从核心到外围排列。



    阶段 0：准备工作（半天）

      1. 克隆仓库
         git clone https://github.com/vuejs/vue.git
         cd vue
         git checkout v2.7.14   # 最后一个 2.x 稳定版

      2. 让测试跑起来
         npm install
         npm test

         能跑通测试是关键——之后你可以改代码、跑对应单测，立刻验证理解是否正确。

      3. 建一个自己的调试项目
         在 examples/ 或外部建一个最简单的 HTML，用 script 引入 dist/vue.js（开发版，带警告），方便打断点调试。

      4. 安装一个可跳转的工具
         VS Code + 「Search node_modules」关掉，不然会卡。装上 Vue 官方 VSCode 扩展的 vetur 或者至少保证 JS 跳转正常。



    阶段 1：响应式系统——这是 Vue 的「心脏」（2-3 天）

    核心文件：src/core/observer/index.js
    涉及文件：
      - src/core/observer/dep.js     —— 依赖收集的「订阅中心」
      - src/core/observer/watcher.js —— 观察者，连接数据和视图
      - src/core/observer/array.js   —— 数组的拦截处理
      - src/core/observer/scheduler.js —— 异步更新队列

    按这个顺序读：

      Day 1: 先读 index.js 的 observe() 和 defineReactive()
             搞清楚 Object.defineProperty 是怎么劫持 get/set 的。
             在调试项目的 data 上打断点，看 get 时怎么收集依赖，set 时怎么通知更新。

      Day 2: dep.js + watcher.js
             Dep 是发布订阅的「中间人」，Watcher 是订阅者。
             画一张图：data → Dep → Watcher → 视图更新

      Day 3: array.js — 为什么 Vue 不能检测数组索引赋值和 length 修改？
             scheduler.js — nextTick 是怎么实现的？（微任务优先 Promise → MutationObserver → setImmediate → setTimeout）

      验证方法：写一个最简单的 Vue 实例，data 里放一个对象和一个数组，在 defineReactive 里加 console.log / debugger，看收集和派发的完整链路。



    阶段 2：虚拟 DOM 和 Diff 算法（2 天）

    核心文件：src/core/vdom/
      - vnode.js       —— VNode 的定义（就是一个 JS 对象）
      - patch.js       —— 核心 diff，新旧 VNode 对比，更新真实 DOM
      - create-element.js —— 从 VNode 创建真实 DOM
      - create-component.js —— 组件 VNode 的特殊处理

      阅读顺序：
      Day 4: vnode.js → create-element.js
             搞清楚一个 VNode 长什么样：tag、data、children、text、elm（对应真实 DOM）、context。

      Day 5: patch.js
             这是全书最难的部分之一。核心是同层比较（sameVnode 判断 key + tag），然后：
               - 新有旧无 → 创建
               - 旧有新无 → 删除
               - 都有且 sameVnode → patchVnode（更新）
             patchVnode 里的 updateChildren 是经典的双端比较算法（头头、尾尾、头尾、尾头）。

      学习方法：自己用纸笔画一个 diff 场景，比如两个各有 5 个 li 的列表，中间插入一个，
      然后跟着 updateChildren 的四个指针走一遍。这一步花时间但非常值得。



    阶段 3：组件系统（2 天）

    核心文件：src/core/instance/
      - init.js        —— Vue 构造函数，初始化所有东西
      - lifecycle.js   —— 生命周期（beforeCreate → created → beforeMount → mounted ...）
      - render.js      —— render 函数调用和 nextTick 的关系
      - state.js       —— data/props/methods/computed/watch 的初始化
      - events.js      —— $on $emit $off $once

      阅读路径：
      Day 6: new Vue() 发生了什么？
             从 init.js 入口，追到 state.js 的 initData → observe(data)
             再到 lifecycle.js 的 mountComponent → new Watcher → updateComponent → _render → _update → patch

      Day 7: 组件通信
             父子组件的创建顺序（先父后子，挂载反过来）、
             $emit 怎么找到父组件的、props 的单向数据流是怎么强制实现的、
             computed 的缓存是怎么做的（Watcher 的 lazy + dirty）。



    阶段 4：模板编译（1-2 天，选读）

    核心文件：src/compiler/
      - parser/       —— HTML 模板 → AST
      - optimizer/    —— 标记静态节点，优化 diff
      - codegen/      —— AST → render 函数字符串

      因为你用 CDN 方式开发，模板编译是在浏览器里完成的（带 compiler 的完整版）。
      这一块可以先了解整体流程，不深入每一行。



    阶段 5：插件和周边（可选）

      - Vue.use() 的机制（src/core/global-api/use.js，就十几行）
      - Vue.mixin() 的实现（mergeOptions 的策略模式）
      - Vue.directive() 的钩子怎么和 DOM 生命周期对应
      - $nextTick 和事件循环的关系



    核心学习原则

      1. 带着问题读，不要通读。比如「为什么修改 data 后视图就变了？」带着这个问题把响应式链路走完。

      2. 改代码 + 跑单测。比如把 defineReactive 改成 Proxy 试试看哪里会炸；把 nextTick 的微任务改成 setTimeout 看看行为差异。

      3. 画图。响应式系统一张图，diff 流程一张图，组件生命周期一张图。画出来就真的理解了。

      4. 看不过来的部分先放掉。Vue 2 源码大概 1 万多行核心逻辑，不是每行都要懂。优先吃透：observer（响应式）→ vdom/patch（diff）→ instance/lifecycle（组件） 。

