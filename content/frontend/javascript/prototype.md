---
outline: [1,3]
head:
  - - meta
    - name: description
      content: prototype
  - - meta
    - name: keywords
      content: prototype
tags: [JavaScript, 原型链]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/javascript/prototype.md"
---

**prototype**


# JavaScript 中的 `prototype` 详解

`prototype` 是 JavaScript 中实现**继承**和**共享属性/方法**的核心机制之一，它基于 **原型链（Prototype Chain）** 的设计。理解 `prototype` 是掌握 JS 面向对象编程的关键。

---

## 一、什么是 `prototype`？

在 JavaScript 中：

> **每个函数（`Function`）都有一个 `prototype` 属性**，它是一个对象，用来存放**可以被该函数所有实例共享的属性和方法**。

当使用 `new` 关键字调用一个函数（构造函数）创建对象时，这个对象的内部会链接到该函数的 `prototype` 对象，从而可以访问其中的属性和方法。

### 🔍 简单比喻

想象一个“模板”：
- 你有一个叫 `Person` 的“模板”（构造函数）。
- 所有通过 `new Person()` 创建的人，都**继承**了这个模板的共同能力，比如 `sayHello()`。
- 这个“模板”就是 `Person.prototype`。

---

## 二、`prototype` 的基本用法

### ✅ 1. 定义构造函数

```js
function Person(name, age) {
    this.name = name;
    this.age = age;
}
```
### ✅ 2. 给 prototype 添加方法

``` js
Person.prototype.sayHello = function() {
    console.log(`你好，我是 ${this.name}`);
};

Person.prototype.walk = function() {
    console.log(`${this.name} 正在走路`);
};
```
### ✅ 3. 创建实例并使用

``` js
const p1 = new Person("小明", 25);
const p2 = new Person("小红", 23);

p1.sayHello(); // 输出：你好，我是 小明
p2.sayHello(); // 输出：你好，我是 小红

p1.walk(); // 小明 正在走路
p2.walk(); // 小红 正在走路

```

## 三、为什么用 prototype？（vs 直接在构造函数中定义）

### ❌ 方式1：在构造函数中定义方法（不推荐）


``` js
function Person(name, age) {
    this.name = name;
    this.age = age;
    this.sayHello = function() {
        console.log(`你好，我是 ${this.name}`);
    };
}
```
**问题：每创建一个实例，都会重新创建一个 sayHello 函数，浪费内存。**


### ✅ 方式2：使用 prototype（推荐）

``` js
function Person(name, age) {
    this.name = name;
    this.age = age;
}

Person.prototype.sayHello = function() {
    console.log(`你好，我是 ${this.name}`);
};
```

**优点：所有实例共享同一个方法，节省内存，效率更高。**

## 四、__proto__ 和 prototype 的关系

|  名称   | 含义  |
|  ----  | ----  |
| Person.prototype  | 是一个对象，构造函数的属性，存放共享方法 |
| `p1.__proto__`  | 是实例的内部属性，指向其构造函数的 prototype |
|Object.getPrototypeOf(p1)|推荐方式，获取对象的原型（等价于 `p1.__proto__`）|

### 🔗 关系图

``` js
p1.__proto__ === Person.prototype; // true
Object.getPrototypeOf(p1) === Person.prototype; // true
```
>✅ 所有 Person 的实例，其 __proto__ 都指向 Person.prototype。


## 五、原型链（Prototype Chain）

当访问一个对象的属性时，JS 会：

  - 先在对象自身查找；
  - 如果找不到，就去 `__proto__`（即构造函数的 prototype）中找；
  - 如果还找不到，继续向上找 prototype 的 `__proto__`，直到 null。


## 六、常见操作

### ✅ 1. 检查属性是否在原型上

``` js 
p1.hasOwnProperty('sayHello'); // false（不是自己的）
'sayHello' in p1; // true（在原型链上）
```
### ✅ 2. 遍历对象自身属性（忽略原型）

``` js 
for (let key in p1) {
    if (p1.hasOwnProperty(key)) {
        console.log(key); // 只输出 name, age
    }
}
```
### ✅ 3.修改原型

``` js
Person.prototype.sayBye = function() {
    console.log(`再见，${this.name}`);
};

p1.sayBye(); // 立即可用！
```

🎯 核心口诀

>函数有 prototype，实例有 `__proto__`，它们指向同一个地方。

``` js
 实例.__proto__ === 构造函数.prototype
```

 理解了这一点，你就掌握了 JavaScript 原型的核心！