---
title: "ArrayMutating"
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/ArrayMutating.md"
---

你贴出的这段代码是 **Vue 2 响应式系统中对数组变异方法（mutating methods）进行拦截的关键实现**。它的目标是：**让通过 `push`、`pop` 等方法修改数组时，也能触发视图更新**。

我们知道，`Object.defineProperty` 只能拦截**属性的读取（getter）和设置（setter）**，但无法监听数组下标赋值（如 `arr[0] = val`）或长度变化（`arr.length = 0`）。更麻烦的是，像 `arr.push(1)` 这样的操作，本质上是调用 `Array.prototype.push`，并不会触发任何 setter！

为了解决这个问题，Vue 采用了一种巧妙的“**方法劫持（Method Hijacking）**”策略。

------

## 🔍 逐行解析

### 1. 获取原生数组原型

```js
var arrayProto = Array.prototype;
```

- 保存原始的 `Array.prototype` 引用，后续用于调用原生方法

### 2. 创建一个继承自数组原型的新对象

```js
var arrayMethods = Object.create(arrayProto);
```

- `arrayMethods` 是一个**空对象**，其 `__proto__` 指向 `Array.prototype`
- 这意味着：`arrayMethods.push === Array.prototype.push`（如果没有被覆盖）

> ✅ 这是实现“**代理 + 继承**”的关键一步。

### 3. 需要拦截的方法列表

```js
var methodsToPatch = [
  'push',
  'pop',
  'shift',
  'unshift',
  'splice',
  'sort',
  'reverse'
];
```

这些方法会**改变原数组**（mutating），因此需要被拦截。

> 📌 注意：`filter`、`map`、`slice` 等返回新数组的方法**不会改变原数组**，所以不需要拦截。

------

## 🛠 接下来会发生什么？（虽然你没贴，但这是完整逻辑）

在 Vue 源码中，紧接着会遍历 `methodsToPatch`，**重写这些方法**：

```js
methodsToPatch.forEach(function (method) {
  // 缓存原始方法
  var original = arrayProto[method];

  // 在 arrayMethods 上定义同名方法
  def(arrayMethods, method, function mutator (...args) {
    // 1. 先调用原始方法，完成实际的数组变更
    var result = original.apply(this, args);

    // 2. 获取当前数组对应的 Observer（响应式观察者）
    var ob = this.__ob__;

    // 3. 如果是插入类操作（push/unshift/splice 插入），需要对新元素也做响应式处理
    var inserted;
    switch (method) {
      case 'push':
      case 'unshift':
        inserted = args;
        break;
      case 'splice':
        inserted = args.slice(2); // splice(start, deleteCount, ...items)
        break;
    }
    if (inserted) ob.observeArray(inserted);

    // 4. 通知依赖更新！
    ob.dep.notify();

    // 5. 返回原始方法的结果
    return result;
  });
});
```

然后，在将一个数组变为响应式时，Vue 会**把它的原型指向 `arrayMethods`**：

```js
// 在 Observer 构造函数中
if (Array.isArray(value)) {
  value.__proto__ = arrayMethods; // 👈 关键！
  observeArray(value);
}
```

> ⚠️ 如果环境不支持 `__proto__`（如 IE10-），Vue 会 fallback 到直接在数组实例上挂载这些方法（性能较差）。

------

## 🌟 整体机制图解

```text
你的代码: arr.push(1)

         ↓
调用 arr.push → 实际调用 arrayMethods.push（已被重写）

         ↓
1. 调用原生 Array.prototype.push 完成插入
2. 对新插入的元素执行 observe（使其响应式）
3. 触发 dep.notify() → 通知所有 Watcher 更新
4. 返回结果

         ↓
视图自动更新！
```

------

## ✅ 为什么这样设计？

| 问题                      | Vue 的解决方案                                 |
| ------------------------- | ---------------------------------------------- |
| `arr[0] = val` 无法监听   | 不支持（Vue 2 的局限，需用 `Vue.set`）         |
| `arr.length = 0` 无法监听 | 不支持                                         |
| `arr.push()` 不触发更新   | **劫持数组方法，在内部手动触发 notify**        |
| 新增元素不是响应式的      | 在 `push/unshift/splice` 中递归 observe 新元素 |

------

## ⚠️ 局限性（Vue 2 的痛点）

1. **直接通过索引设置项** 不触发更新：

   ```js
   vm.items[0] = newValue; // ❌ 无效
   ```

   → 必须用 `Vue.set(vm.items, 0, newValue)`

2. **修改数组长度** 不触发更新：

   ```js
   vm.items.length = 0; // ❌ 无效
   ```

> 💡 这些限制在 **Vue 3（使用 Proxy）中已彻底解决**。

------

## 💡 一句话总结

> Vue 通过创建一个**继承自 Array.prototype 的新对象 `arrayMethods`**，并重写其中会改变原数组的 7 个方法，在方法内部**先调用原生实现，再手动触发响应式更新**，从而让 `push`、`pop` 等操作也能驱动视图变化。