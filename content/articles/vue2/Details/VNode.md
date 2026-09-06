---
tags: [Vue2, 源码]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/VNode.md"
---

我们可以把 VNode 理解为 “对真实 DOM 节点的轻量级 JavaScript 描述” —— 它不直接操作 DOM，而是作为“蓝图”，在 diff 和 patch 阶段指导如何更新真实 DOM。

## 🧱 1. `VNode` 构造函数：虚拟节点的“数据结构”

```js
var VNode = function VNode (
  tag, data, children, text, elm, context,
  componentOptions, asyncFactory
) { ... }
```

### ✅ 核心字段说明

| 字段                | 含义                                | 示例                                  |
| ------------------- | ----------------------------------- | ------------------------------------- |
| `tag`               | 标签名                              | `'div'`, `'my-component'`             |
| `data`              | 节点属性/事件/指令等                | `{ class: 'red', on: { click: fn } }` |
| `children`          | 子 VNode 数组                       | `[VNode, VNode]`                      |
| `text`              | 文本内容（仅文本节点）              | `'Hello'`                             |
| `elm`               | 对应的真实 DOM 元素（patch 后赋值） | `Hello`                               |
| `key`               | 唯一标识（用于 diff 优化）          | `'item-1'`                            |
| `componentOptions`  | 组件选项（如果是组件）              | `{ Ctor, propsData, ... }`            |
| `componentInstance` | 组件实例（挂载后）                  | `vm`                                  |
| `isComment`         | 是否为注释节点                      | `true`                                |
| `isStatic`          | 是否为静态节点（无需更新）          | `true`（由编译器标记）                |

> 💡 一个 VNode **要么有 `tag`（元素/组件），要么有 `text`（文本节点）**，不会同时存在。

```
模板 (template)
   ↓ [编译]
render 函数 → 返回 VNode 树
   ↓ [首次渲染]
patch(oldVnode=null, newVnode) → 创建真实 DOM
   ↓ [数据变化]
重新执行 render → 新 VNode 树
   ↓
patch(oldVnode, newVnode) → diff + 更新 DOM
```

  VNode 是 **连接“声明式模板”和“命令式 DOM 操作”的桥梁**。 



## 举个实际例子

 模板： 

```html
<div id="app">
  <p>{{ msg }}</p>
  <my-component :name="user.name"></my-component>
</div>
```

对应的 VNode 树（简化）：

```js
new VNode('div', { attrs: { id: 'app' } }, [
  createTextVNode('\n  '), // 换行和缩进也是文本节点
  new VNode('p', undefined, [
    createTextVNode(vm.msg)
  ]),
  createTextVNode('\n  '),
  new VNode('my-component', {
    props: { name: vm.user.name }
  }, undefined, undefined, undefined, vm, {
    Ctor: MyComponent,
    propsData: { name: vm.user.name }
  }),
  createTextVNode('\n')
])
```

------

## ✅ 总结：VNode 的核心价值

1. **抽象 DOM**：让 Vue 不依赖浏览器环境（可用于 Weex、SSR）
2. **高效更新**：通过 diff 算法最小化 DOM 操作
3. **组件化基础**：每个组件返回一个 VNode，可嵌套组合
4. **编译优化载体**：`isStatic`、`key` 等标记由编译器注入，运行时利用

> 🔥 可以说，没有 VNode，就没有 Vue 的高性能和跨平台能力。

 `VNode` 是 Vue 的“**虚拟 DOM 积木**”——它用 JavaScript 对象描述 UI 结构，让框架能在不碰真实 DOM 的情况下进行计算、比较和优化，最终只在必要时精准地“砌砖”（更新 DOM）。 