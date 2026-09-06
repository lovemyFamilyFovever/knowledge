---
tags: [Vue2, 源码]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/cache.md"
---

# cached 

cached 函数，是 Vue 源码中一个非常经典且高频使用的优化技巧——它实现了一个简单的记忆化（Memoization）缓存机制。

## 🔍 原始代码：

```js
/**
 * Create a cached version of a pure function.
 */
function cached (fn) {
  var cache = Object.create(null);
  return (function cachedFn (str) {
    var hit = cache[str];
    return hit || (cache[str] = fn(str))
  })
}
```

## 📝 注释翻译

```js
/**
 * Create a cached version of a pure function.
 */
```

> **翻译**：创建一个**纯函数的缓存版本**。

📌 关键词：

- **纯函数（pure function）**：相同的输入，永远返回相同的输出，没有副作用。
- **缓存版本**：把之前计算过的结果存起来，下次直接用，避免重复计算。

👉 这就是所谓的 **“记忆化”（Memoization）**。

------

## ✅ 函数逻辑详解

### 1. `function cached(fn)`

- 接收一个函数 `fn` 作为参数。
- 这个 `fn` 必须是**纯函数**，比如：`str => str.toUpperCase()`

### 2. `var cache = Object.create(null);`

- 创建一个**纯净的空对象**，没有原型链。

- 用来存储 `输入 → 输出` 的映射。

- 使用

   

  ```js
  Object.create(null)
  ```

   

  是为了：

  - 避免原型污染（比如 `toString`、`hasOwnProperty` 等）
  - 性能更高，查找更快

### 3. 返回一个新函数 `cachedFn(str)`

- 这个函数接收一个字符串 `str`（作为 key）
- 内部通过闭包访问 `cache` 和 `fn`

### 4. `var hit = cache[str];`

- 尝试从缓存中读取 `str` 对应的结果

### 5. `return hit || (cache[str] = fn(str))`

这是最精妙的一行！我们拆解：

```js
hit || (cache[str] = fn(str))
```

等价于：

```js
if (hit) {
  return hit;
} else {
  var result = fn(str);
  cache[str] = result;
  return result;
}
```

👉 **短路运算 + 赋值表达式** 的巧妙结合！

- 如果 `hit` 存在（即缓存命中），直接返回
- 否则，执行 `fn(str)`，把结果存入 `cache[str]`，并返回这个结果

📌 注意：`cache[str] = fn(str)` 这个表达式本身会返回 `fn(str)` 的值，所以可以直接 `return`。

------

## ✅ 举个例子：缓存 `camelize`

Vue 中一个典型用法是缓存**字符串格式化函数**，比如“短横线转驼峰”：

```js
// 原始函数：短横线转驼峰
function camelize(str) {
  return str.replace(/-(\w)/g, (_, c) => c.toUpperCase());
}

// 创建缓存版本
var cachedCamelize = cached(camelize);

// 第一次调用：执行函数，结果被缓存
cachedCamelize('hello-world'); // 'helloWorld'，同时 cache['hello-world'] = 'helloWorld'

// 第二次调用：直接从缓存读取，不执行函数
cachedCamelize('hello-world'); // 'helloWorld'（直接返回）
```

------

## 💡 在 Vue 中的用途

`cached` 在 Vue 源码中被**大量用于字符串处理函数的性能优化**，因为：

- 模板编译、属性名解析等操作会**频繁调用**这些函数
- 但输入往往是**重复的**（比如 `v-bind:class`、`v-on:click`）

### 常见的缓存函数：

| 函数         | 作用         | 示例                             |
| ------------ | ------------ | -------------------------------- |
| `camelize`   | 短横线转驼峰 | `'hello-world'` → `'helloWorld'` |
| `capitalize` | 首字母大写   | `'div'` → `'Div'`                |
| `hyphenate`  | 驼峰转短横线 | `'helloWorld'` → `'hello-world'` |

它们的创建方式都是：

```js
var camelize = cached(function (str) {
  return str.replace(/-(\w)/g, function (_, c) {
    return c ? c.toUpperCase() : '';
  });
});
```

------

## ✅ 加了详细注释的版本：

```js
/**
 * 创建一个函数的缓存版本（记忆化）
 * 适用于纯函数：相同输入 → 相同输出
 * 
 * @param {Function} fn - 要缓存的纯函数，接受一个字符串参数，返回任意类型
 * @returns {Function} 缓存版本的函数
 */
function cached(fn) {
  // 创建一个纯净的缓存对象（无原型链）
  var cache = Object.create(null);

  // 返回一个带缓存逻辑的包装函数
  return function cachedFn(str) {
    // 尝试从缓存中读取结果
    var hit = cache[str];
    
    // 如果缓存命中，直接返回
    // 否则执行原函数，将结果存入缓存并返回
    return hit || (cache[str] = fn(str));
  };
}
```

------

## ✅ 为什么这样设计？优势在哪？

| 优势           | 说明                               |
| -------------- | ---------------------------------- |
| ⚡ **性能优化** | 避免重复计算，尤其是复杂字符串处理 |
| 🧱 **封装性好** | 缓存逻辑与业务逻辑分离             |
| 🔁 **可复用**   | 可用于任何纯函数                   |
| 🧩 **轻量**     | 不依赖外部库，代码极简             |
| 🛡️ **安全**     | `Object.create(null)` 避免原型污染 |

------

## ⚠️ 注意事项

### 1. **只适用于纯函数**

```js
// ❌ 不行！每次返回不同值
cached(Math.random)

// ✅ 可以！输入相同，输出相同
cached(str => str.toUpperCase())
```

### 2. **只接受字符串参数**

- 这个 `cached` 函数假设 `fn` 的参数是字符串，因为 `cache[str]` 用 `str` 作为 key。
- 如果参数是对象或多个参数，需要更复杂的缓存策略（比如 JSON.stringify 或 WeakMap）。

### 3. **缓存无限增长**

- 这个缓存是**无限的**，不会清理旧数据。
- 但在 Vue 的使用场景中，输入是有限的（比如标签名、指令名），所以没问题。
- 如果用于无限输入场景，需要加 LRU 等缓存淘汰策略。

------

## ✅ 总结

| 项目                | 说明                                          |
| ------------------- | --------------------------------------------- |
| **函数名**          | `cached`                                      |
| **作用**            | 为纯函数创建一个带缓存的版本                  |
| **核心思想**        | 记忆化（Memoization）                         |
| **关键技术**        | 闭包 + 短路运算 + `Object.create(null)`       |
| **在 Vue 中的用途** | 缓存 `camelize`、`hyphenate` 等字符串处理函数 |
| **设计模式**        | 装饰器模式 / 高阶函数                         |

------

这个函数虽然只有 5 行，但它体现了函数式编程中的一个重要思想：

> **“用空间换时间”** —— 用一点内存存储结果，换来巨大的性能提升。