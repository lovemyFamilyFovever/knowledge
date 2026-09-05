---
tags: [Vue2, 源码]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/constant.md"
---

# Vue2常量定义



## 🔹 1. `var SSR_ATTR = 'data-server-rendered';`

### ✅ 含义

这是一个**DOM 属性名常量**，用于标记一个组件是否是由**服务器端渲染（SSR）**生成的。

### 🧩 作用

- 当 Vue 在服务端（Node.js）渲染组件时，会自动给根元素添加这个属性：

  ```html
  <div data-server-rendered="true">...</div>
  ```

- 客户端挂载（mount）时，Vue 会检查这个属性：

  - 如果存在，表示这是 SSR 渲染的 HTML，需要进行“激活”（hydration），而不是重新渲染。
  - 如果不存在，表示是纯客户端渲染。

### 🌐 使用场景

```js
new Vue({
  el: '#app',
  // 服务端渲染时，#app 内部已有 HTML
  // Vue 会尝试“激活”它，而不是 replace it
})
```

### 💡 设计思想

- **环境感知**：让客户端 Vue 知道自己是在“接续”服务端的工作。
- **性能优化**：避免重复渲染，提升首屏性能。
- **同构统一**：实现“一套代码，两端运行”的关键标识。

## 🔹 2. `var ASSET_TYPES = [ 'component', 'directive', 'filter' ]`

### ✅ 含义

这是 Vue 中“**资源类型**”（Asset Types）的枚举数组，定义了可以在 `Vue.component`、`Vue.directive`、`Vue.filter` 中注册的全局资源类型。

### 🧩 用途一：全局 API 注册

```js
Vue.component('my-button', { /* ... */ })
Vue.directive('focus', { /* ... */ })
Vue.filter('capitalize', function(value) { /* ... */ })
```

这些注册的信息最终都会存储在 `Vue.options.components`、`directives`、`filters` 中。

### 🧩 用途二：选项合并（Options Merge）

在 `mergeOptions`（选项合并）过程中，Vue 会遍历 `ASSET_TYPES`，对每种资源类型使用特定的合并策略。

例如：

```js
// 父组件
components: { A }

// 子组件
components: { B }

// 合并后
components: { A, B }  // 不是覆盖，而是合并
```

而普通选项如 `data` 是“后者覆盖前者”，但资源类选项是“合并”。

### 🧩 用途三：构建工具识别

一些构建工具或 IDE 插件会通过扫描 `ASSET_TYPES` 来识别 Vue 的自定义语法。

### ⚠️ 注意：`filter` 已被 Vue 3 弃用

在 Vue 3 中，`filter` 被移除，所以如果你看到的是 Vue 2 源码，`filter` 还在；Vue 3 中已删除。

------

## 🔹 3. `var LIFECYCLE_HOOKS = [ /* 生命周期钩子列表 */ ]`

### ✅ 含义

这是 Vue 组件**所有生命周期钩子函数名**的枚举数组。

### 🧩 完整列表及作用

| 钩子             | 触发时机                                                     |
| ---------------- | ------------------------------------------------------------ |
| `beforeCreate`   | 实例初始化之后，数据观测 (data observer) 和 event/watcher 事件配置之前被调用 |
| `created`        | 实例创建完成后被调用，此时已完成数据观测，可以访问 `data`、`props` |
| `beforeMount`    | 挂载开始之前被调用，`render` 函数首次被调用                  |
| `mounted`        | 实例挂载到 DOM 后调用，可以访问 `$el`                        |
| `beforeUpdate`   | 数据更新时调用，发生在虚拟 DOM 重新渲染和打补丁之前          |
| `updated`        | 组件 DOM 更新后调用                                          |
| `beforeDestroy`  | 实例销毁之前调用                                             |
| `destroyed`      | 实例销毁后调用，所有指令已被解绑，子实例也被销毁             |
| `activated`      | `keep-alive` 组件激活时调用                                  |
| `deactivated`    | `keep-alive` 组件停用时调用                                  |
| `errorCaptured`  | 当捕获到后代组件错误时被调用                                 |
| `serverPrefetch` | 服务端渲染期间，组件实例在渲染前获取数据的钩子               |

------

### 🧩 用途一：选项合并（Merge Options）

和 `ASSET_TYPES` 类似，在 `mergeOptions` 时，Vue 会识别这些名字是“生命周期钩子”，并使用**合并策略**：

```js
// 父组件
created() { console.log(1) }

// 子组件
created() { console.log(2) }

// 合并后：两个都会执行
created: [function () { console.log(1) }, function () { console.log(2) }]
```

👉 生命周期钩子是“数组合并”，而不是覆盖。

### 🧩 用途二：事件系统集成

你可以这样监听生命周期：

```js
vm.$on('hook:mounted', () => {
  console.log('Component mounted!');
});
```

Vue 内部就是通过 `LIFECYCLE_HOOKS` 数组动态注册了这些 `hook:` 事件。

### 🧩 用途三：调试与开发工具

Vue DevTools 依赖这个列表来识别和展示组件的生命周期。

------

## ✅ 总结：这三个常量的设计哲学

| 常量              | 作用         | 设计思想                         |
| ----------------- | ------------ | -------------------------------- |
| `SSR_ATTR`        | SSR 标识     | **环境感知**，同构应用的关键     |
| `ASSET_TYPES`     | 资源类型枚举 | **分类管理**，统一注册与合并     |
| `LIFECYCLE_HOOKS` | 生命周期枚举 | **元编程**，让框架可扩展、可监听 |

------

### 💡 一句话总结

> 这三个常量是 Vue 框架的“**宪法性条款**”——它们定义了：
>
> - **如何标记服务端渲染**（`SSR_ATTR`）
> - **哪些是可注册的全局资源**（`ASSET_TYPES`）
> - **组件的一生有哪些阶段**（`LIFECYCLE_HOOKS`）
>
> 它们看似简单，却是 Vue 架构清晰、扩展性强的基石。