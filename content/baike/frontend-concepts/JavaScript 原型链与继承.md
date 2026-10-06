---
title: "JavaScript 原型链与继承"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# JavaScript 原型链与继承

> 📌 **导航**：本文是 **JavaScript 原型链与继承** 词条，属于 frontend-concepts 术语集。相关枢纽：[[JavaScript 基础核心概念]]、[[前端框架核心概念]]。

## 定义

**一句话定义：** JS 对象通过内部的原型指针指向另一个对象，读取属性时沿这条链逐级向上查找，直到 `Object.prototype` 的 `null` 为止——这条链路就是原型链，JS 的继承与代码复用全部由它实现，`class` 只是把它包成可读的语法。

**通俗类比：** 像家谱——自己答不上来的问题问父母，父母不知道问祖辈，一直问到祖宗（Object.prototype），祖宗的父辈是 null，查无可查。

## 为什么需要它

JS 没有传统的类：构造函数的 `prototype` 上的方法被所有实例共享，既省内存又让"改一处全体生效"成为可能；委托式查找还让多态不必先声明继承体系。理解了原型链，才说得清 `instanceof` 判的是什么、`class extends` 展开后是什么。

## 核心机制

- **读与写不对称**：读属性沿原型链向上找，写属性永远落在对象自身并遮蔽（shadow）链上同名属性；`hasOwnProperty` 只认自身，`in` 与 `for...in` 会连链上一起来。
- **两个易混指针**：`__proto__` 是实例上的实际链路（非标准访问器，正式 API 是 `Object.getPrototypeOf`），`prototype` 是构造函数自己的属性，new 时它成为实例的原型。链路是 `alice.__proto__ === Person.prototype`、`Person.prototype.__proto__ === Object.prototype`、`Object.prototype.__proto__ === null`。
- **class 是语法糖**：`constructor` 挂到构造函数的 prototype 上，`extends` 把子类原型的指针接到父类，`super.x()` 转发到父原型的方法；本质仍是原型链，不是新的继承模型。
- **判定与代价**：`instanceof` 沿链查找是否出现目标 prototype；链越深，未命中时的查找越贵，所以别靠 `Object.prototype` 挂公共方法。

## 具体示例

```javascript
function Person(name) { this.name = name; }
Person.prototype.sayHi = function () { return `Hi, ${this.name}`; };

const alice = new Person("Alice");
alice.sayHi();                       // 自身没有，沿链找到 Person.prototype
alice.talk = "shadow";               // 写只落在自身

class Animal { constructor(n) { this.name = n; } speak() { return "a"; } }
class Dog extends Animal { speak() { return "woof"; } }
new Dog("Rex").speak();              // "woof"，super.speak() 才转给 Animal
```

## 何时用与何时不用

- **用**：需要一组实例共享行为且要求运行时可扩展时用原型；写库/框架兼容老运行时用手写构造函数 + prototype；业务代码用 class 表达同一条链，可读性更好。
- **不用**：深层继承体系（A extends B extends C）——换组合或 mixin；需要真正私有状态时别指望 `_priv` 命名约定，走 class 私有字段或 WeakMap（见 [[JavaScript 弱引用（WeakMap 与 WeakRef）]]）。

## 优劣与代价

✅ 委托式复用零额外结构，实例不携带方法副本，改父原型即全体生效。
✅ 与 [[面向对象编程（OOP）概念]] 里的类继承相比，原型更动态：可以在任何对象上事后加方法。
⚠️ 隐式修改父原型会污染所有实例（给 `Array.prototype` 加方法是公认反模式）。
⚠️ 深链的性能与心智成本都高，属性未命中时整条链都要走一遍。

## 与相关概念的区别

- **vs [[面向对象编程（OOP）概念]]**：那条讲类/封装/继承/多态的通用模型与类继承树，本条讲 JS 的委托实现——没有类也能继承。
- **vs [[原型模式]]**：原型模式是 GoF 创建型模式，靠克隆已有实例造新对象；原型链是语言的属性查找机制，两者只是同词不同事。
- **vs [[JavaScript 作用域与 this]]**：变量沿作用域链向外找（词法、静态决定），属性沿原型链向上找（对象、动态可变）。

## 常见误区

- 以为 ES6 的 class 引入了新的继承模型，和原型链是两套机制。
- 以为 `hasOwnProperty(obj, "name")` 检出的属性可能来自原型链。
- 以为改 `obj.__proto__` 与改 `Constructor.prototype` 效果完全等价，可以随便用。

## 面试速答

> 🎯 原型链是对象属性查找的委托链：实例→构造函数 prototype→Object.prototype→null；读沿链向上、写落在自身并遮蔽；class/extends 只是语法糖，instanceof 沿链判定；与类继承的差别是它动态、事后仍可改。

## 相关术语

[[JavaScript 基础核心概念]]、[[JavaScript 作用域与 this]]、[[面向对象编程（OOP）概念]]、[[原型模式]]、[[JavaScript 弱引用（WeakMap 与 WeakRef）]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇承接原《JavaScript 基础核心概念》原型链（Prototype Chain）一节，Person/Dog 两组示例压缩自原稿；`__proto__` 非标准与写遮蔽行为建议对照 MDN 复核。
