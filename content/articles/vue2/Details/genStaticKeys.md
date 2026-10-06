---
tags: [Vue2, 源码]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/genStaticKeys.md"
---

# genStaticKeys

### 🔍 原始代码

```js
/**
 * Generate a string containing static keys from compiler modules.
 */
function genStaticKeys (modules) {
  return modules.reduce(function (keys, m) {
    return keys.concat(m.staticKeys || [])
  }, []).join(',')
}
```

## ✅ 1. 这个函数是干什么的？

> **答：从一组编译器模块中提取所有 `staticKeys`，合并成一个逗号分隔的字符串。**

### 🧩 示例：

```js
var modules = [
  {
    staticKeys: ['staticClass', 'staticStyle']
  },
  {
    staticKeys: ['attrs']
  },
  {
    // 没有 staticKeys
  },
  {
    staticKeys: ['props']
  }
];

var result = genStaticKeys(modules);
console.log(result);
// 输出："staticClass,staticStyle,attrs,props"
```


## ✅ 2. 代码逐行解析

```js
function genStaticKeys (modules) {
  return modules.reduce(function (keys, m) {
    return keys.concat(m.staticKeys || [])
  }, []).join(',')
}
```

### 🧩 步骤 1：`modules.reduce(...)`

- 遍历所有编译器模块
- 累积一个包含所有 `staticKeys` 的数组

### 🧩 步骤 2：`m.staticKeys || []`

- 安全访问：如果模块没有 `staticKeys` 属性，返回空数组 `[]`
- 避免 `undefined.concat` 报错

### 🧩 步骤 3：`keys.concat(...)`

- 合并当前模块的 `staticKeys` 到累积数组中
- 使用 `concat` 而不是 `push`，因为 `concat` 返回新数组（函数式风格）

### 🧩 步骤 4：`.join(',')`

- 将最终的数组合并成一个**逗号分隔的字符串**
- 为什么是字符串？为了后续快速匹配（见下文）


## ✅ 3. 什么是“编译器模块”（compiler modules）？

在 Vue 编译器中，功能被拆分为多个模块，每个模块负责处理模板中的某一部分。

### 🧩 常见的编译器模块：

| 模块          | 职责              | `staticKeys` 示例  |
| ------------- | ----------------- | ------------------ |
| `class` 模块  | 处理 `class` 绑定 | `'staticClass'`    |
| `style` 模块  | 处理 `style` 绑定 | `'staticStyle'`    |
| `attrs` 模块  | 处理静态属性      | `'attrs'`          |
| `props` 模块  | 处理 `props`      | `'props'`          |
| `events` 模块 | 处理事件          | `'on', 'nativeOn'` |


## ✅ 4. 什么是“静态键”（static keys）？

> **答：表示某些 AST 节点上的属性是“静态的”（不会变化），可以跳过响应式处理。**

### 🧩 示例：模板

```html
<div class="navbar" :id="dynamicId">
  Hello
</div>
```

### 🧩 生成的 AST 节点

```js
{
  type: 1,
  tag: 'div',
  staticClass: '"navbar"',     // ← 静态 class
  classBinding: 'dynamicClass', // 动态 class
  attrsList: [{ name: 'id', value: 'dynamicId' }]
}
```

- `staticClass: '"navbar"'` 是**静态的**
- 编译器知道它不会变，后续 diff 时可以跳过比较


## ✅ 5. 为什么要把 `staticKeys` 合并成字符串？

是为了**性能优化**！字符串比数组更容易做“包含判断”。

### 🧩 使用场景：判断一个 AST 节点是否“完全静态”

AST : Abstract Syntax Tree (抽象语法树)  

在编译器中，会有一个函数检查节点是否静态：

```js
function isStatic (node) {
  // 如果节点类型是 2（表达式）或 3（文本），直接判断
  if (node.type === 2) {
    return false
  }
  if (node.type === 3) {
    return true
  }
  // 关键：检查是否有非静态属性
  return !node.for && // 没有 v-for
         !node.if &&  // 没有 v-if
         !node.tag === 'template' && 
         Object.keys(node).every(key => {
           // 判断 key 是否在 staticKeys 字符串中
           return staticKeys.indexOf(key) > -1
         })
}
```

👉 `staticKeys` 是一个字符串，如 `"staticClass,staticStyle,attrs"`，通过 `indexOf` 快速判断某个 `key` 是否属于“静态属性”。

虽然现代 JS 中 `Set` 更快，但 Vue 为了兼容性和代码体积，选择用字符串 `indexOf`。


## ✅ 6. 在 Vue 编译流程中的位置

```tex
Template String
     ↓
parse() → AST
     ↓
optimize() → 标记静态节点
     ↓
generate() → Render Function
```

- `genStaticKeys` 在 `optimize` 阶段前被调用
- 它生成的 `staticKeys` 字符串被传给 `optimize` 函数
- `optimize` 用它来判断哪些节点可以标记为 `static: true`


## ✅ 7. 为什么设计成模块化提取？

- **可扩展性**：第三方可以注册自己的编译器模块，提供 `staticKeys`
- **解耦**：每个模块自己知道哪些属性是静态的
- **复用**：`genStaticKeys` 是通用聚合逻辑

------

## ✅ 总结

| 项目         | 说明                                                      |
| ------------ | --------------------------------------------------------- |
| **函数名**   | `genStaticKeys`                                           |
| **作用**     | 从编译器模块中提取所有 `staticKeys`，合并为逗号分隔字符串 |
| **输入**     | 编译器模块数组                                            |
| **输出**     | 如 `"staticClass,staticStyle,attrs"`                      |
| **核心机制** | `reduce` + `concat` + `join`                              |
| **用途**     | 优化 `optimize` 阶段的静态节点判断                        |
| **性能意义** | 通过字符串 `indexOf` 快速判断属性是否静态                 |
| **设计思想** | 模块化 + 聚合 + 性能优先                                  |

------

### 💡 一句话总结

> `genStaticKeys` 是 Vue 编译器的“**静态属性注册中心**”，它将分散在各模块中的“静态性”声明聚合为一个全局可查的字符串，为后续的**静态节点优化**提供了关键依据。