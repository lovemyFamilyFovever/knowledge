---
tags: [Vue2, 源码]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/isPromise.md"
---

# isPromise

## 🔍 原始代码
``` js
/**
 * 检查一个值是否是 Promise 对象（或类 Promise 对象）
 * 使用“鸭子类型”判断：只要有 .then 和 .catch 方法，就认为是 Promise
 *
 * @param {*} val - 要检查的值
 * @returns {boolean} 是否为 Promise
 */
function isPromise (val) {
  return (
    // 确保值存在（不是 null 或 undefined）
    isDef(val) &&
    // 必须有 .then 方法，且是函数（Promise 核心）
    typeof val.then === 'function' &&
    // 必须有 .catch 方法，且是函数（提高判断准确性）
    typeof val.catch === 'function'
  );
}

```


```js
function isPromise (val) {
  return (
    isDef(val) &&
    typeof val.then === 'function' &&
    typeof val.catch === 'function'
  )
}
```

## ✅ 分解解析

### 1. `isDef(val)`

- `isDef` 是 Vue 内部的一个工具函数，意思是 "**is defined**"（已定义）。

- 它通常定义为：

  ```js
  function isDef (v) {
    return v !== undefined && v !== null
  }
  ```

- 所以 `isDef(val)` 确保 `val` 不是 `null` 或 `undefined`。

📌 **为什么需要这一步？**

因为如果 `val` 是 `null` 或 `undefined`，那么访问 `val.then` 会报错（Cannot read property 'then' of null）。

👉 这是一个**安全防护**，防止后续属性访问出错。

------

### 2. `typeof val.then === 'function'`

- 检查 `val` 是否有 `.then` 方法，且是一个函数。
- 这是 Promise 的**核心特征**。
- 所有符合 Promises/A+ 规范的 Promise 对象都必须提供 `.then()` 方法。

📌 举例：

```js
new Promise(() => {}).then   // 是函数
Promise.resolve().then      // 是函数
```

------

### 3. `typeof val.catch === 'function'`

- 检查是否有 `.catch` 方法。
- `.catch` 用于捕获 Promise 中的错误。
- 虽然从技术上讲，`.catch` 可以通过 `.then(null, onError)` 模拟，但绝大多数 Promise 实现（包括原生 Promise）都提供了 `.catch` 方法。

> ✅ Vue 这里加了双重判断，是为了**提高判断的准确性**，避免误判。

------

## ✅ 为什么这样判断？——“鸭子类型”思想

Vue 并没有使用 `val instanceof Promise` 来判断，而是采用了 **“鸭子类型”（Duck Typing）** 的思想：

> “如果它走起来像鸭子，叫起来像鸭子，那它就是鸭子。”

在 Promise 的语境下就是：

> “如果一个对象有 `.then` 和 `.catch` 方法，那它就可以当作 Promise 来用。”

这种方法的好处是：

| 优势                        | 说明                                                         |
| --------------------------- | ------------------------------------------------------------ |
| ✅ **跨 iframe 兼容**        | `instanceof Promise` 在不同 window 环境下会失效（比如 iframe 中的 Promise 不等于主窗口的 Promise） |
| ✅ **兼容自定义 Promise 类** | 比如 Bluebird、Q 等第三方 Promise 库                         |
| ✅ **兼容 polyfill**         | 即使浏览器没有原生 Promise，只要实现了 `.then` 和 `.catch`，也能被识别 |

------

## ✅ 举个例子：哪些值返回 `true`？

| 输入 `val`                  | `isPromise(val)` | 说明                 |
| --------------------------- | ---------------- | -------------------- |
| `Promise.resolve()`         | ✅ `true`         | 原生 Promise         |
| `new Promise(() => {})`     | ✅ `true`         | 手动创建             |
| `fetch('/api')`             | ✅ `true`         | `fetch` 返回 Promise |
| `axios.get('/api')`         | ✅ `true`         | axios 返回 Promise   |
| `{ then() {}, catch() {} }` | ✅ `true`         | 符合“鸭子类型”       |
| `Bluebird.resolve()`        | ✅ `true`         | 第三方 Promise 库    |

------

## ❌ 哪些值返回 `false`？

| 输入 `val`       | `isPromise(val)` | 说明                     |
| ---------------- | ---------------- | ------------------------ |
| `undefined`      | ❌ `false`        | 未定义                   |
| `null`           | ❌ `false`        | 空值                     |
| `{}`             | ❌ `false`        | 没有 `.then` 或 `.catch` |
| `{ then() {} }`  | ❌ `false`        | 缺少 `.catch`            |
| `{ catch() {} }` | ❌ `false`        | 缺少 `.then`             |
| `[]`             | ❌ `false`        | 数组                     |
| `function() {}`  | ❌ `false`        | 函数                     |
| `123`            | ❌ `false`        | 数字                     |

------

## 💡 在 Vue 中的用途

### 1. **异步组件（Async Components）**

```js
Vue.component('async-comp', function (resolve, reject) {
  // 模拟异步加载
  setTimeout(() => {
    resolve({
      template: '<div>I am async!</div>'
    })
  }, 1000)
})
```

或者返回 Promise：

```js
Vue.component('async-comp', () => import('./MyComp.vue'))
```

Vue 内部会用 `isPromise` 判断返回值是否是 Promise，如果是，就用 `.then()` 处理。

### 2. **`$nextTick` 返回 Promise**

```js
Vue.nextTick(() => {
  // DOM 更新后执行
}).then(() => {
  // 如果浏览器支持 Promise，$nextTick 会返回一个 Promise
})
```

Vue 需要判断是否支持 Promise，有时也会用到类似逻辑。

### 3. **Vuex 中的异步 action**

```js
actions: {
  async fetchData({ commit }) {
    const res = await api.get('/data')
    commit('setData', res)
  }
}
```

返回的 `async` 函数会返回 Promise，Vue/Vuex 需要识别并处理。



## ⚠️ 小知识：为什么不只判断 `.then`？

理论上，只要 `.then` 存在，就可以认为是“thenable”（可被 `await` 的对象）。

但 Vue 这里加了 `.catch`，是为了：

- **提高准确性**：避免某些只实现了 `.then` 的非标准对象被误判。
- **确保可用性**：如果一个“Promise”没有 `.catch`，Vue 在处理错误时会出问题。

所以这是一个**更严格的判断**。

------

## ✅ 总结

| 项目                | 说明                                         |
| ------------------- | -------------------------------------------- |
| **函数名**          | `isPromise`                                  |
| **作用**            | 判断一个值是否是 Promise（或类 Promise）对象 |
| **判断依据**        | 鸭子类型：有 `.then` 和 `.catch` 方法        |
| **优点**            | 兼容性强、跨环境、支持第三方库               |
| **在 Vue 中的用途** | 异步组件、`$nextTick`、Vuex action 等        |

------

这个函数再次体现了 Vue 在设计上的**健壮性**和**兼容性考量**：不依赖具体构造函数，而是基于行为（behavior）来判断。