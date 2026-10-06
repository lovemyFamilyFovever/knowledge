---
title: "JavaScript 作用域与 this"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# JavaScript 作用域与 this

> 📌 **导航**：本文是 **JavaScript 作用域与 this** 词条，属于 frontend-concepts 术语集。相关枢纽：[[JavaScript 基础核心概念]]、[[HTML & CSS 核心概念]]。

## 定义

**一句话定义：** 作用域决定变量在哪可见，作用域链决定引擎按什么顺序向外查找变量；var/let/const 是这套机制的入口（函数作用域+提升 / 块级作用域+暂时性死区 / 再加不可重新赋值）；而 this 不走作用域链，它由函数的调用方式在运行时绑定。

**通俗类比：** 作用域像房间、作用域链像楼层——3 楼找不到去 2 楼、再找不到去大厅；this 像代词"我"，同一个词不同人说指代不同对象。

## 为什么需要它

var 的函数作用域与提升会让变量泄漏到意图之外的整块代码，this 在回调里静默换主则是 JS 最高频的"值怎么变了"故障。声明方式与绑定规则一旦确定，这两类问题就能写代码时预测，而不是事后靠打日志调试。

## 核心机制

- **三种声明**：var 函数作用域、声明提升（赋值前读到 undefined）、可重复声明；let/const 块级作用域、声明前访问落进暂时性死区（TDZ）直接 ReferenceError；const 声明即须赋值且不可重新赋值——但它锁的是绑定不是值，`const user = { name: "Alice" }; user.name = "Bob"` 合法，`user = {}` 才报 TypeError。
- **作用域链**：JS 用词法（静态）作用域，路径由代码书写位置决定，运行时调用位置不改它。内层能读写外层、外层看不见内层；这条单向查找路径正是 [[闭包]] 能"带走"外部变量的机制，闭包本身与其循环捕获坑由 [[闭包]] 专条承载。
- **this 四条规则**：默认绑定（独立调用，非严格模式指向 window，严格模式 undefined）、隐式绑定（`obj.greet()` 取最近的 obj）、显式绑定（call 逐个传参、apply 收数组、bind 返回 this 锁死的新函数）、new 绑定。优先级从右往左盖住前者。
- **箭头函数**：没有自己的 this，取定义时外层的 this 且无法被 call/apply/bind 改写。所以对象方法写成 `greet: () => this.name` 拿到的是外层上下文，不是这个对象。

## 具体示例

```javascript
console.log(a); // undefined —— var 提升但未赋值
var a = 10;
// console.log(b); // ReferenceError —— let 的暂时性死区
let b = 20;

const obj = { name: "Alice", greet() { console.log(this.name); } };
obj.greet();          // "Alice" —— 隐式绑定
const fn = obj.greet;
fn();                 // undefined —— 退回默认绑定

function greet(g) { console.log(`${g}, ${this.name}`); }
const bob = { name: "Bob" };
greet.call(bob, "Hi");        // 显式绑定，立即调用
const bound = greet.bind(bob); // this 永久锁成 bob
```

## 何时用与何时不用

- **用**：默认 const，需要重新赋值才改 let；变量生命周期交给块级作用域（if/for/try 结束即失效）；回调里要保持上下文用箭头函数或 bind，别靠 `const self = this`。
- **不用**：不再用 var（除非必须跑在无块级语义的老环境）；不要把 const 当不可变用，需要冻结值走 `Object.freeze`。

## 优劣与代价

✅ 块级作用域把变量活性压到最小，配合 const 默认写法令"谁改了这个值"可肉眼追踪。
✅ 词法作用域让 this 的漂移有确定规则可推，背下四条绑定规则即可预测结果。
⚠️ TDZ 让顺序敏感：同一块里先引用后声明会从"拿到 undefined"变成抛错。
⚠️ 解构方法、把方法当回调传出去、类方法当事件处理器，三种写法都会丢隐式绑定。

## 与相关概念的区别

- **vs [[闭包]]**：作用域链是引擎的查找机制，闭包是函数携带创建时词法环境的实例；那条讲应用（私有化、防抖、循环捕获），本条只管查找路径与绑定规则。
- **vs [[编程语言通用概念]]**：那条给跨语言的"作用域是什么"（全局/局部/块级 + 多语言对照），本条是 JS 的落地规则（提升、TDZ、this）。
- **vs [[JavaScript 原型链与继承]]**：变量沿作用域链向外找（函数维度），属性沿原型链向上找（对象维度），两条链互不相干。

## 常见误区

- 以为 const 声明的对象就不可修改，写 `const user = {}` 后连属性一起改不动。
- 以为 this 由函数定义在哪里决定，把对象方法赋给变量再调用仍指向该对象。
- 以为 let 变量在声明之前只是 undefined，跟 var 一样可以提前读。

## 面试速答

> 🎯 var 函数作用域+提升，let/const 块级+TDZ，const 只锁绑定不锁属性；作用域链按词法位置向外找变量，this 偏由调用方式定（默认/隐式/显式/new，箭头函数继承定义处）；闭包另见 [[闭包]]。

## 相关术语

[[JavaScript 基础核心概念]]、[[闭包]]、[[JavaScript 原型链与继承]]、[[JavaScript 异步编程（事件循环·Promise·async·await·Generator）]]、[[编程语言通用概念]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇合并原《JavaScript 基础核心概念》的 var/let/const 区别、作用域与作用域链、this 指向三节；闭包一节归 [[闭包]] 专条不在本篇重复。
