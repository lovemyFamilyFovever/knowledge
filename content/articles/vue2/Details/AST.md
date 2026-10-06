---
tags: [Vue2, 源码]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/AST.md"
---

# AST

## 🌟 什么是 AST？

**AST = Abstract Syntax Tree（抽象语法树）**

它是一种**代码的结构化表示形式**，把“文本代码”变成“树形数据结构”。

### 🧩 类比：把一段话变成思维导图

原文：

> “我有一个红色的苹果。”

思维导图（结构化）：

```tex
- 主语：我
- 动作：有
- 宾语：苹果
  - 颜色：红色
```

👉 **AST 就是代码的“思维导图”**。

------

## 💡 举个 HTML 模板的例子

假设你有这样一段 Vue 模板：

```html
<div class="navbar" id="main">
  <p v-if="showText">Hello {{ name }}</p>
</div>
```

Vue 编译器会先把它**解析**（parse）成一个 **AST（抽象语法树）**，就像这样：

```js
{
  type: 1,                    // 表示是元素节点
  tag: 'div',                 // 标签名
  attrsList: [
    { name: 'class', value: 'navbar' },
    { name: 'id', value: 'main' }
  ],
  staticClass: '"navbar"',    // 静态 class
  children: [
    {
      type: 1,
      tag: 'p',
      directives: [
        { name: 'if', value: 'showText' }  // v-if 指令
      ],
      children: [
        {
          type: 3,            // 文本节点
          text: 'Hello ',
          static: true
        },
        {
          type: 2,            // 表达式节点
          expression: '_s(name)',  // 经过编译的表达式
          text: '{{ name }}'
        }
      ]
    }
  ]
}
```

------

## ✅ 什么是“AST 节点”？

> **答：AST 树中的每一个对象，就是一个“AST 节点”（AST Node）。**

就像上面例子中：

- 外层的 `div` 是一个节点
- 内层的 `p` 是一个节点
- `Hello ` 文本是一个节点
- `{{ name }}` 表达式是一个节点

每个节点都描述了**代码中某一部分的结构和属性**。

------

## 📌 AST 节点的常见属性

| 属性         | 含义                                 |
| ------------ | ------------------------------------ |
| `type`       | 节点类型（1=元素，2=表达式，3=文本） |
| `tag`        | 标签名（如 `div`, `p`）              |
| `attrsList`  | 属性列表                             |
| `children`   | 子节点数组（形成树结构）             |
| `text`       | 文本内容                             |
| `expression` | 表达式（如 `{{ name }}` 编译后）     |
| `directives` | 指令（如 `v-if`, `v-model`）         |
| `static`     | 是否是静态节点（优化用）             |

------

## 🔄 Vue 编译器的三大步骤

1. **Parse（解析）**
    → 把模板字符串变成 AST
2. **Optimize（优化）**
    → 遍历 AST，标记静态节点（如 `class="navbar"` 永远不会变）
3. **Generate（生成）**
    → 把 AST 转成 `render` 函数代码

```tex
Template String
     ↓
   parse()   → AST（树形结构）
     ↓
optimize()   → 标记 static: true
     ↓
generate()   → render() { return ... }
```

在整个过程中，**AST 节点就是被不断处理的数据单元**。

------

## ✅ 为什么需要 AST？

因为**字符串很难分析和转换**，而**树形结构很容易操作**。

### 🧩 举例：优化静态节点

编译器遍历 AST，发现：

```js
{
  type: 3,
  text: 'Hello ',
  static: true   // 标记为静态，后续 diff 时可跳过
}
```

👉 因为它是纯文本，没有变量，永远不会变，所以可以优化。

------

## 🌐 其他场景中的 AST

| 工具           | 用途                                                       |
| -------------- | ---------------------------------------------------------- |
| Babel          | 把 ES6+ 代码转成 ES5：`parse → AST → transform → generate` |
| ESLint         | 检查代码：分析 AST 是否符合规则                            |
| TypeScript     | 类型检查：在 AST 上做类型推断                              |
| Webpack loader | 自定义代码转换                                             |

👉 所有现代前端工具都在操作 AST。

------

## ✅ 总结

| 术语          | 解释                                                         |
| ------------- | ------------------------------------------------------------ |
| **AST**       | 抽象语法树，是代码的树形结构表示                             |
| **AST 节点**  | AST 中的每一个对象，代表代码中的一部分（如标签、文本、表达式） |
| **作用**      | 让代码变得可分析、可修改、可优化                             |
| **在 Vue 中** | 模板 → AST → 优化 → render 函数                              |

------

### 💡 一句话总结

> **AST 节点就是 Vue 编译器“看懂”模板的“最小理解单位”**，就像你读一句话时，大脑会自动拆解出“主语、谓语、宾语”一样，Vue 通过 AST 节点来“理解”你的模板。

现在你就能明白，为什么 `genStaticKeys` 要生成一个字符串来判断“哪些属性是静态的”了——它是为了在遍历 AST 节点时，快速判断某个属性（如 `staticClass`）是否可以被优化。