---
tags: [Vue2, 源码]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/looseEqual.md"
---

#  looseEqual 

### 🔍 原始代码

```js
/**
 * Check if two values are loosely equal - that is,
 * if they are plain objects, do they have the same shape?
 */
function looseEqual (a, b) {
  if (a === b) { return true }
  var isObjectA = isObject(a);
  var isObjectB = isObject(b);
  if (isObjectA && isObjectB) {
    try {
      var isArrayA = Array.isArray(a);
      var isArrayB = Array.isArray(b);
      if (isArrayA && isArrayB) {
        return a.length === b.length && a.every(function (e, i) {
          return looseEqual(e, b[i])
        })
      } else if (a instanceof Date && b instanceof Date) {
        return a.getTime() === b.getTime()
      } else if (!isArrayA && !isArrayB) {
        var keysA = Object.keys(a);
        var keysB = Object.keys(b);
        return keysA.length === keysB.length && keysA.every(function (key) {
          return looseEqual(a[key], b[key])
        })
      } else {
        /* istanbul ignore next */
        return false
      }
    } catch (e) {
      /* istanbul ignore next */
      return false
    }
  } else if (!isObjectA && !isObjectB) {
    return String(a) === String(b)
  } else {
    return false
  }
}
```

## ✅ 1. 这个函数是干什么的？

> **答：判断两个值是否“松散相等”，即：**
>
> - 基本类型：转成字符串后相等
> - 数组：长度相同，每个元素松散相等
> - 对象：键相同，每个值松散相等
> - 日期：时间戳相等
> - 其他：不相等

它比 `===` 更宽松，比 `==` 更安全，是 Vue 实现**响应式依赖追踪**和**变化检测**的核心。

## ✅ 2. 代码逐行解析

### 🧩 第 1 步：严格相等（短路优化）

```js
if (a === b) { return true }
```

- 如果 `a === b`，直接返回 `true`
- 这是最常见的场景，快速返回

- ### 🧩 第 2 步：判断是否都是对象

  ```js
  var isObjectA = isObject(a);
  var isObjectB = isObject(b);
  if (isObjectA && isObjectB) {
    // 都是对象，进入深度比较
  }
  ```

  - `isObject` 是 Vue 的工具函数，判断是否是**纯对象**（plain object）
  - `isObject({})` → `true`
  - `isObject([])` → `false`（数组不是纯对象）
  - `isObject(null)` → `false`



  ### 🧩 第 3 步：都是对象时的深度比较

  ```js
  try {
    // ...
  } catch (e) {
    return false
  }
  ```

  - 用 `try/catch` 包裹，防止 `Object.keys` 等操作报错（如访问不可枚举属性）
  - 出错就认为不相等（安全降级）



  #### 📌 情况 1：都是数组

  ```js
  if (isArrayA && isArrayB) {
    return a.length === b.length && a.every(function (e, i) {
      return looseEqual(e, b[i])
    })
  }
  ```

  - 长度必须相同
  - 每个元素都要 `looseEqual`（递归）
  - 顺序敏感：`[1,2]` 和 `[2,1]` 不相等



  #### 📌 情况 2：都是日期

  ```js
  else if (a instanceof Date && b instanceof Date) {
    return a.getTime() === b.getTime()
  }
  ```

  - 日期对象不能直接比较 `a === b`
  - 必须比较时间戳（毫秒数）
  - `new Date('2020-01-01')` 和 `new Date('2020-01-01')` 应该相等



  #### 📌 情况 3：都是纯对象（非数组）

  ```js
  else if (!isArrayA && !isArrayB) {
    var keysA = Object.keys(a);
    var keysB = Object.keys(b);
    return keysA.length === keysB.length && keysA.every(function (key) {
      return looseEqual(a[key], b[key])
    })
  }
  ```

  - 获取所有**自身可枚举属性**
  - 键的数量必须相同
  - 每个键对应的值都要 `looseEqual`（递归）
  - 键名必须完全一致（结构相同）



  #### 📌 情况 4：混合类型（对象 vs 数组）

  ```js
  else {
    return false
  }
  ```

  - 对象和数组不相等
  - `[]` 和 `{}` 不相等



  ### 🧩 第 4 步：都不是对象（基本类型）

  ```js
  else if (!isObjectA && !isObjectB) {
    return String(a) === String(b)
  }
  ```

  - 把两个值都转成字符串再比较
  - 这就是“松散”的体现

  ### 🧩 示例：

  ```js
  looseEqual(1, '1')        // true  → String(1) === '1'
  looseEqual(true, 'true')  // true  → String(true) === 'true'
  looseEqual(null, 'null')  // true  → String(null) === 'null'
  looseEqual(undefined, 'undefined') // true
  ```



  ### 🧩 第 5 步：一对象一基本类型

  ```js
  else {
    return false
  }
  ```

  - 对象和基本类型不相等
  - `{}` 和 `'{}'` 不相等



  ## ✅ 3. 在 Vue 中的典型用途

  ### 🧩 1. `v-model` 的 `select` 选项比较

  ```html
  <select v-model="selected">
    <option :value="{ id: 1, name: 'Vue' }">Vue</option>
  </select>
  ```

  当用户选择时，Vue 需要判断 `selected` 是否等于某个 `option` 的 `value`。由于是对象，不能用 `===`，必须用 `looseEqual`。

  ### 🧩 2. `watch` 的深度监听

  ```js
  watch: {
    someObject: {
      handler(newVal, oldVal) {
        console.log('changed');
      },
      deep: true
    }
  }
  ```

  Vue 内部会用 `looseEqual` 判断 `newVal` 和 `oldVal` 是否真的变了。

  ### 🧩 3. `computed` 缓存失效判断

  ```js
  computed: {
    fullName() {
      return this.user.firstName + this.user.lastName;
    }
  }
  ```

  Vue 会记住 `this.user` 的“形状”，如果 `looseEqual` 判断它没变，就不重新计算。

  ### 🧩 4. `props` 变化检测

  父组件传 `:user="{ name: 'John' }"`，Vue 需要判断新 `user` 是否和旧 `user` 不同。



  ## ✅ 4. 与 `===` 和 `==` 的对比

  | 比较         | `1` vs  `'1'` | `{a:1}` vs `{a:1}` | `[1]` vs `[1]` | `new Date()` vs `new Date()` |
  | ------------ | ------------- | ------------------ | -------------- | ---------------------------- |
  | `===`        | ❌             | ❌                  | ❌              | ❌                            |
  | `==`         | ✅             | ❌                  | ❌              | ❌                            |
  | `looseEqual` | ✅             | ✅                  | ✅              | ✅                            |

  👉 `looseEqual` 在“松散”和“准确”之间找到了完美平衡。



  ## ✅ 5. 与 `lodash.isEqual` 的对比

  | 特性             | `looseEqual` | `lodash.isEqual` |
  | ---------------- | ------------ | ---------------- |
  | 字符串化基本类型 | ✅            | ❌（严格类型）    |
  | 递归比较         | ✅            | ✅                |
  | 性能             | 轻量，无依赖 | 更重，功能多     |
  | 用途             | Vue 内部专用 | 通用工具         |

  👉 `looseEqual` 是为 Vue 量身定制的“最小可用”实现。



  ## ✅ 总结

  | 项目              | 说明                                             |
  | ----------------- | ------------------------------------------------ |
  | **函数名**        | `looseEqual`                                     |
  | **作用**          | 判断两个值是否松散相等（结构一致）               |
  | **核心机制**      | 递归 + 类型分支 + 字符串化                       |
  | **在 Vue 中用途** | `v-model`, `watch`, `computed`, `props` 变化检测 |
  | **设计思想**      | **实用主义**：在性能、准确性、兼容性之间平衡     |



  ### 💡 一句话总结

  > `looseEqual` 是 Vue 的“**变化感知引擎**”，它让框架能够聪明地判断“数据到底变没变”，从而决定是否需要更新视图，是响应式系统的核心判官。

- 