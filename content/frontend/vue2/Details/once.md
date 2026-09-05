---
title: "once"
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/once.md"
---

# once

 `once` 函数，是函数式编程和前端开发中一个**极其经典且实用**的设计模式——**“只执行一次”**（Once Pattern）。

它看似简单，却在 Vue、React、Node.js 等几乎所有框架中广泛使用，用于确保某些关键逻辑**绝不重复执行**。

### 🔍 原始代码

```js
/**
 * Ensure a function is called only once.
 */
function once (fn) {
  var called = false;
  return function () {
    if (!called) {
      called = true;
      fn.apply(this, arguments);
    }
  }
}
```

------

## ✅ 1. 这个函数是干什么的？

> **答：把一个函数包装成“只能执行一次”的版本。**

### 🧩 示例：

```js
function doPayment() {
  console.log('Payment processed!');
}

var doPaymentOnce = once(doPayment);

doPaymentOnce(); // "Payment processed!"
doPaymentOnce(); // （无输出）
doPaymentOnce(); // （无输出）
```

👉 无论调用多少次 `doPaymentOnce`，`doPayment` 只执行一次。

------

## ✅ 2. 代码逐行解析

```js
function once (fn) {
  var called = false;           // 闭包变量，记录是否已调用
  return function () {          // 返回一个新函数
    if (!called) {              // 如果还没调用过
      called = true;            // 标记为已调用
      fn.apply(this, arguments); // 执行原函数，保持 this 和参数
    }
  }
}
```

### 🧩 核心机制：

- **闭包（Closure）**：`called` 变量被内层函数引用，形成闭包，长期驻留内存
- **卫语句（Guard Clause）**：`if (!called)` 阻止重复执行
- **`apply` 保持上下文**：确保 `fn` 调用时的 `this` 和参数正确

------

## ✅ 3. 为什么需要 `apply(this, arguments)`？

为了**保持原函数的调用上下文和参数**。

### 🧩 示例：方法绑定

```js
var user = {
  name: 'Alice',
  login: once(function(attempt) {
    console.log(this.name + ' logged in via ' + attempt);
  })
};

user.login('email');    // "Alice logged in via email"
user.login('google');   // （无输出）
```

- `this` 指向 `user`
- `arguments` 是 `['google']`
- 使用 `apply` 确保 `this.name` 能正确访问

------



### 🔍 关键点：`arguments` 属于**当前函数**（即 `return` 的那个匿名函数）

- `arguments` 是一个**类数组对象**，它存在于**每一个普通函数**中
- 它记录的是**该函数被调用时传入的实际参数**



```js
function once (fn) {
  var called = false;
  return function () {
    console.log('包装函数的 arguments:', arguments);
    if (!called) {
      called = true;
      fn.apply(this, arguments);
    }
  }
}

function greet(name, age) {
  console.log('Hello ' + name + ', you are ' + age + ' years old');
}

var greetOnce = once(greet);

greetOnce('Alice', 25);
```

## ✅ 4. 在 Vue 中的典型用途

### 🧩 1. **生命周期钩子的“只执行一次”逻辑**

```js
export default {
  mounted() {
    const initAnalytics = once(() => {
      console.log('Analytics initialized');
      // 初始化埋点、上报等
    });

    // 可能被多次触发（如事件监听）
    window.addEventListener('load', initAnalytics);
    window.addEventListener('DOMContentLoaded', initAnalytics);
    // 确保只初始化一次
  }
}
```

------

### 🧩 2. **组件的“首次渲染”优化**

```js
mounted() {
  const renderFirstTime = once(() => {
    this.$nextTick(() => {
      // 首次渲染后执行，如聚焦输入框
      this.$refs.input.focus();
    });
  });

  this.someAsyncAction().then(renderFirstTime);
  this.anotherAction().then(renderFirstTime); // 不会重复聚焦
}
```

------

### 🧩 3. **事件监听器的防重复绑定**

```js
methods: {
  setupWebSocket() {
    const onMessage = once((event) => {
      console.log('First message received:', event.data);
      // 只处理第一次消息
    });

    this.socket.addEventListener('message', onMessage);
    // 即使多次 setup，onMessage 也只执行一次
  }
}
```

------

### 🧩 4. **第三方库的“只加载一次”**

```js
const loadScript = once((src, callback) => {
  const script = document.createElement('script');
  script.src = src;
  script.onload = callback;
  document.head.appendChild(script);
});

// 多个组件都调用
loadScript('/lib/chart.js', () => { console.log('Chart.js loaded'); });
loadScript('/lib/chart.js', () => { /* 不会重复加载 */ });
```

------

## ✅ 5. 与 `lodash.once` 的对比

| 特性     | Vue `once`             | `lodash.once`    |
| -------- | ---------------------- | ---------------- |
| 源码     | 自研，轻量             | 通用工具库       |
| 功能     | 完全一致               | 支持更多边界处理 |
| 返回值   | 第一次调用的返回值缓存 | 同左             |
| 使用场景 | 内部专用               | 通用             |

👉 Vue 的 `once` 是一个极简、精准的实现。

------

## ✅ 6. 高级用法：带返回值缓存

有些 `once` 实现会**缓存第一次的返回值**，后续调用直接返回：

```js
function onceWithCache(fn) {
  let called = false;
  let result;
  return function() {
    if (!called) {
      called = true;
      result = fn.apply(this, arguments);
    }
    return result;
  };
}

const getAPIConfig = onceWithCache(() => {
  return fetch('/config').then(res => res.json());
});

getAPIConfig().then(config => { /* 第一次：真实请求 */ });
getAPIConfig().then(config => { /* 第二次：使用缓存结果 */ });
```

Vue 的 `once` **不缓存返回值**，只保证执行一次。

------

## ✅ 7. 潜在陷阱与注意事项

### ⚠️ 1. `this` 上下文必须正确

```js
const obj = {
  name: 'Bob',
  greet: once(function() {
    console.log('Hello, ' + this.name);
  })
};

const fn = obj.greet;
fn(); // "Hello, undefined" ❌ this 丢失
```

✅ 正确做法：始终绑定上下文或使用箭头函数。

### ⚠️ 2. 不适用于异步函数的“并发调用”

```js
const asyncInit = once(async () => {
  console.log('Start');
  await delay(1000);
  console.log('End');
});

asyncInit(); // Start → (等待) → End
asyncInit(); // Start（同时打印！）→ 不会等待
```

👉 `once` 不阻止并发执行，只阻止**多次进入函数体**。

✅ 解决方案：使用 `p-memoize` 或手动管理 Promise。

------

## ✅ 总结

| 项目              | 说明                                            |
| ----------------- | ----------------------------------------------- |
| **函数名**        | `once`                                          |
| **作用**          | 确保函数只执行一次                              |
| **核心机制**      | 闭包 + 标志位 + `apply`                         |
| **在 Vue 中用途** | 生命周期优化、防重复初始化、事件去重            |
| **设计思想**      | **幂等性（Idempotence）**：重复调用不产生副作用 |

------

### 💡 一句话总结

> `once` 是一个“**保险丝函数**”，它用闭包锁住执行权限，确保关键逻辑像“按下一次就弹出的按钮”一样，**只生效一次，永不误触**。