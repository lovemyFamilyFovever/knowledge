---
tags: [Vue2, 源码]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/toArray.md"
---

# toArray

### 🔍 原始代码

```js
/**
 * Convert an Array-like object to a real Array.
 */
function toArray (list, start) {
  start = start || 0;
  var i = list.length - start;
  var ret = new Array(i);
  while (i--) {
    ret[i] = list[i + start];
  }
  return ret
}
```

------

## ✅ 1. 这个函数是干什么的？

> **答：把一个“像数组的东西”变成真正的 JavaScript 数组。**

### 🧩 什么是“类数组对象”（Array-like）？

一个对象，有：

- `.length` 属性
- 用数字索引访问元素（如 `[0]`, `[1]`）

但**不是 `Array` 的实例**，不能使用 `push`、`map`、`filter` 等数组方法。

### 🧩 常见的类数组对象：

| 类型             | 示例                                              |
| ---------------- | ------------------------------------------------- |
| `arguments`      | 函数内的 `arguments` 对象                         |
| `NodeList`       | `document.querySelectorAll('div')` 返回的节点列表 |
| `HTMLCollection` | `document.getElementsByTagName('p')`              |
| 自定义类数组     | `{ 0: 'a', 1: 'b', length: 2 }`                   |

------

## ✅ 2. 为什么要转换？直接用不行吗？

❌ 不行！类数组对象**不能使用数组方法**：

```js
function demo() {
  // arguments 是类数组，不是真数组
  arguments.map(x => x); // ❌ 报错：arguments.map is not a function
}
```

✅ 所以需要先转成真数组：

```js
function demo() {
  var args = toArray(arguments);
  args.map(x => x); // ✅ 成功
}
```

------

## ✅ 3. 代码逐行解析

```js
function toArray (list, start) {
  start = start || 0;                    // 设置起始索引，默认 0
  var i = list.length - start;           // 计算要复制的元素个数
  var ret = new Array(i);                // 预分配数组空间
  while (i--) {                          // 从后往前遍历
    ret[i] = list[i + start];            // 复制元素
  }
  return ret                             // 返回新数组
}
```

### 🧩 参数说明

- `list`：类数组对象（必须有 `.length`）
- `start`：可选，从哪个索引开始转换（默认 0）

👉 支持“截取部分”转换，比如跳过前几个参数。

------

### 🧩 `start = start || 0`

- 如果 `start` 没传或为 `0`，则设为 `0`
- 注意：如果 `start` 是 `0`，`0 || 0` 还是 `0`，没问题
- 但如果 `start` 可能是负数？Vue 内部调用时会确保合法

------

### 🧩 `var i = list.length - start`

- 计算新数组的长度
- 例如：`list.length = 5`, `start = 2` → `i = 3`

------

### 🧩 `var ret = new Array(i)`

- **预分配数组空间**，性能更高
- 避免后续 `push` 导致动态扩容

------

### 🧩 `while (i--)`：从后往前遍历

这是**性能优化的关键**！

#### 为什么从后往前？

- `i--` 本身会返回 `i` 的值，并让 `i` 减 1

  **（重点注意：while(i--)首先先返回i的值，执行判断之后,这个i的值在进行-1；跟--i正好相反，--i是先执行-1，再进行判断。）**

- 当 `i` 变成 `0` 时，条件为 `false`，循环结束

- 不需要额外判断 `i >= 0`

#### 对比传统 `for` 循环：

```js
// 传统方式
for (var i = 0; i < len; i++) {
  ret[i] = list[i + start];
}

// 优化方式（当前代码）
var i = len;
while (i--) {
  ret[i] = list[i + start];
}
```

👉 **优化点**：

- 少一次变量声明（`len` 可以省略）
- 循环条件更简单（`i--` 本身就是布尔判断）
- 在某些 JS 引擎中，倒序遍历更快（缓存友好）

------

### 🧩 `ret[i] = list[i + start]`

- 从 `start` 位置开始复制
- 例如：`start = 2`，则 `list[2]` → `ret[0]`，`list[3]` → `ret[1]`，依此类推

------

## ✅ 4. 使用示例

### 🧩 示例 1：处理 `arguments`

```js
function logArgs() {
  var args = toArray(arguments, 1); // 跳过第一个参数
  console.log('Rest args:', args);
}

logArgs('ignore', 'a', 'b', 'c');
// 输出：Rest args: ['a', 'b', 'c']
```

### 🧩 示例 2：转换 `NodeList`

```js
var divs = document.querySelectorAll('div');
var divArray = toArray(divs);
divArray.forEach(div => div.classList.add('active'));
```

------

## ✅ 5. 与现代写法对比

### 🆚 现代 ES6+ 写法

```js
// 更简洁
const toArray = (list, start = 0) => [...list].slice(start);

// 或
const toArray = (list, start = 0) => Array.from(list).slice(start);
```

### ✅ 但 Vue 为什么不用？

因为 Vue 2 需要支持**老浏览器**（IE9+），而：

- `...` 扩展运算符不支持
- `Array.from` 不支持
- `slice` 在某些类数组上可能有问题（如 `arguments` 在 IE 中 `slice` 可能失败）

所以 Vue 选择**手动实现**，确保兼容性。

------

## ✅ 6. 在 Vue 中的用途

`toArray` 在 Vue 源码中被广泛使用，例如：

### 🧩 1. `$emit` 传递参数

```js
vm.$emit('event', a, b, c);
// 内部可能用 toArray(arguments, 1) 获取所有参数
```

- `vm`：通常指一个 Vue 实例或组件实例（ViewModel）。
- `.$emit()`：Vue 实例上的一个方法，用于**触发（发射）一个自定义事件**。
- `'event'`：你要触发的**事件名称**（可以是任意自定义名字，比如 `'update'`, `'submit'`, `'close'` 等）。
- `a, b, c`：你想要**传递给事件监听者的数据参数**（可以是任意类型：字符串、数字、对象、数组等）。

### 🧩 2. 事件系统、生命周期钩子

收集多个回调函数时，统一转成数组处理。

------

## ✅ 总结

| 项目             | 说明                             |
| ---------------- | -------------------------------- |
| **函数名**       | `toArray`                        |
| **作用**         | 将类数组对象转为真数组           |
| **核心机制**     | 预分配数组 + 倒序遍历复制        |
| **性能优化**     | `while(i--)` 减少判断开销        |
| **兼容性**       | 支持老浏览器（IE9+）             |
| **`start` 参数** | 支持从指定位置开始转换           |
| **设计思想**     | 实用主义 + 性能优先 + 兼容性保障 |

------

### 💡 一句话总结

> `toArray` 是一个**为兼容性和性能而生的底层工具函数**，它用最稳妥的方式，把“像数组的东西”变成“真正的数组”，让 Vue 可以放心地使用数组方法。