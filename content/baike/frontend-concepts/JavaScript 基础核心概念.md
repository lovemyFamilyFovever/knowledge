---
title: "JavaScript 基础核心概念"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# JavaScript 基础核心概念


> 📌 **导航**：本文是 **JavaScript 基础核心概念** 词条，属于 frontend-concepts 术语集。相关枢纽：[[HTML & CSS 核心概念]]、[[JavaScript 基础核心概念]]、[[React深入]]、[[Vue3核心]]、[[前端工程化核心概念]]。

---

## var / let / const 区别

**一句话定义**：三种变量声明方式，在作用域、提升行为和可变性上各有不同。

**通俗类比**：var 像写在便利贴上（全局可见、可覆盖）；let 像写在白板上（局部可见、可擦写）；const 像刻在石头上（局部可见、不可修改）。

**具体示例**：
```javascript
// var —— 函数作用域，会提升
console.log(x); // undefined（提升但未赋值）
var x = 10;

// let —— 块级作用域，暂时性死区
// console.log(y); // ReferenceError（TDZ）
let y = 20;

// const —— 块级作用域，声明时必须赋值，不可重新赋值
const z = 30;
// z = 40; // TypeError: Assignment to constant variable

// const 的陷阱：对象属性可修改
const user = { name: "Alice" };
user.name = "Bob"; // ✅ 可以修改属性
// user = {};      // ❌ 不能重新赋值
```

**为什么需要它**：var 的函数作用域和提升容易导致 bug，let/const 的块级作用域让代码更可预测。

**与相关术语的对比和区分**：var（函数作用域、提升、可重复声明）→ let（块作用域、TDZ、不可重复声明）→ const（同 let + 不可重新赋值）。

---

## 闭包（Closure）

**一句话定义**：函数能"记住"并访问它被创建时所在的词法作用域，即使这个函数在其他地方被调用。

**通俗类比**：像搬家时带走了家里的钥匙——即使你搬到了新小区，依然能回老家开门。

**具体示例**：
```javascript
function createCounter() {
  let count = 0; // 外部函数的局部变量

  return {
    increment: () => ++count,
    decrement: () => --count,
    getCount: () => count
  };
}

const counter = createCounter();
counter.increment(); // 1
counter.increment(); // 2
counter.getCount();  // 2
// count 变量在 createCounter 执行后本该销毁，
// 但被内部函数"闭包"住了，依然可以访问

// 经典应用：防抖函数
function debounce(fn, delay) {
  let timer = null; // 闭包持有 timer
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
```

**为什么需要它**：实现数据私有化、函数工厂、回调中保留状态等，是 JS 高阶函数的基础。

**与相关术语的对比和区分**：闭包 vs 作用域链。作用域链是 JS 引擎查找变量的机制；闭包是利用这个机制，让函数"携带"外部变量的实例。

---

## 原型链（Prototype Chain）

**一句话定义**：JS 对象通过 `__proto__` 指向另一个对象，层层向上查找属性和方法，直到 `null`，这条链路就是原型链。

**通俗类比**：像家谱——你找不到的东西去问父母，父母找不到去问爷爷，一直往上找，直到祖宗（Object.prototype）那里。

**具体示例**：
```javascript
function Person(name) {
  this.name = name;
}
Person.prototype.sayHi = function () {
  console.log(`Hi, I'm ${this.name}`);
};

const alice = new Person("Alice");

// alice 自身没有 sayHi，沿着原型链找到 Person.prototype
alice.sayHi(); // "Hi, I'm Alice"

// 原型链关系：
// alice.__proto__ === Person.prototype
// Person.prototype.__proto__ === Object.prototype
// Object.prototype.__proto__ === null

// ES6 class（语法糖，本质还是原型链）
class Animal {
  constructor(name) { this.name = name; }
  speak() { console.log(`${this.name} speaks`); }
}
class Dog extends Animal {
  speak() { console.log(`${this.name} barks`); }
}
```

**为什么需要它**：JS 没有传统的"类"，原型链是实现继承和代码复用的核心机制。

**与相关术语的对比和区分**：`__proto__`（实际的链路）vs `prototype`（构造函数上的属性，用于设置新对象的原型）。class 语法只是原型链的语法糖。

---

## 事件循环（Event Loop）与任务队列

**一句话定义**：JS 引擎用事件循环协调同步代码、异步回调和微任务的执行顺序。

**通俗类比**：像餐厅服务员——先处理桌上的菜（同步代码），然后去厨房端新菜（宏任务），但如果有 VIP 加单（微任务）会优先处理。

**具体示例**：
```javascript
console.log("1 - 同步");

setTimeout(() => {
  console.log("2 - 宏任务");
}, 0);

Promise.resolve().then(() => {
  console.log("3 - 微任务");
});

console.log("4 - 同步");

// 输出顺序：1 → 4 → 3 → 2
```

**事件循环流程图**：
```
┌───────────────────────┐
│     调用栈 (Call Stack)  │
│   执行同步代码（宏任务）    │
└──────────┬────────────┘
           │ 执行完毕
           ▼
┌───────────────────────┐
│    微任务队列 (Microtask) │
│  Promise.then, MutationObserver │
│  全部执行完才进入下一步      │
└──────────┬────────────┘
           │ 微任务清空
           ▼
┌───────────────────────┐
│    宏任务队列 (Macrotask) │
│  setTimeout, setInterval, │
│  I/O, UI 渲染            │
└──────────┬────────────┘
           │ 取一个宏任务执行
           ▼
        回到顶部循环
```

**为什么需要它**：JS 是单线程的，事件循环让它能在不阻塞主线程的情况下处理异步操作（网络请求、定时器等）。

**与相关术语的对比和区分**：宏任务（setTimeout/setInterval）每轮循环执行一个；微任务（Promise.then）每轮循环全部清空。微任务优先级高于宏任务。

---

## Promise

**一句话定义**：表示一个异步操作的最终结果（成功或失败），用链式调用替代回调地狱。

**通俗类比**：像餐厅点餐——给你一个取餐号（Promise），菜好了会叫号（resolve），菜卖完了会通知你换（reject）。

**具体示例**：
```javascript
// 基础用法
const fetchData = () => new Promise((resolve, reject) => {
  setTimeout(() => resolve("数据来了"), 1000);
});

fetchData()
  .then(data => console.log(data))     // "数据来了"
  .catch(err => console.error(err))
  .finally(() => console.log("结束"));

// Promise.all —— 全部成功才成功，有一个失败就失败
const p1 = fetch("/api/user");
const p2 = fetch("/api/posts");
Promise.all([p1, p2])
  .then(([user, posts]) => console.log(user, posts))
  .catch(err => console.error("有一个失败了"));

// Promise.race —— 谁先完成用谁的结果（包括失败）
Promise.race([
  fetch("/api/fast"),
  fetch("/api/slow")
]).then(fastest => console.log(fastest));

// Promise.allSettled —— 等所有 Promise 都结束，不管成败
Promise.allSettled([p1, p2]).then(results => {
  results.forEach(r => {
    if (r.status === "fulfilled") console.log(r.value);
    else console.error(r.reason);
  });
});
```

**为什么需要它**：解决回调地狱（callback hell），让异步代码更线性、可读、可组合。

**与相关术语的对比和区分**：Promise 是异步的"容器"，async/await 是 Promise 的语法糖，让异步代码看起来像同步。

---

## async / await

**一句话定义**：基于 Promise 的语法糖，让异步代码用同步的写法来表达。

**通俗类比**：Promise 像写信（.then/.catch），async/await 像打电话——同步地说"等一下"（await），但底层还是异步的。

**具体示例**：
```javascript
// async 函数自动返回 Promise
async function getUser() {
  try {
    const response = await fetch("/api/user");  // 等待 Promise 解析
    const user = await response.json();         // 等待 JSON 解析
    return user;
  } catch (error) {
    console.error("请求失败:", error);
    throw error;
  }
}

// 并发执行
async function loadDashboard() {
  const [user, posts, notifications] = await Promise.all([
    fetch("/api/user").then(r => r.json()),
    fetch("/api/posts").then(r => r.json()),
    fetch("/api/notifications").then(r => r.json()),
  ]);
  return { user, posts, notifications };
}

// 错误处理
async function riskyOperation() {
  try {
    await可能会失败的操作();
  } catch (e) {
    // 处理错误
  } finally {
    // 清理资源
  }
}
```

**为什么需要它**：比 .then() 链更直观，调试更友好（可以像调试同步代码一样设断点），try/catch 能统一处理错误。

**与相关术语的对比和区分**：async/await 是 Promise 的上层封装，不能替代 Promise.all 等组合方法，两者常配合使用。

---

## Generator 函数

**一句话定义**：可以暂停执行、分段返回值的特殊函数，用 `function*` 声明，用 `yield` 暂停。

**通俗类比**：像读小说按章节——每次调用 `next()` 读下一章（yield 返回值），可以随时暂停，也可以传入批注（传参）。

**具体示例**：
```javascript
function* numberGenerator() {
  console.log("开始");
  yield 1;           // 暂停，返回 1
  console.log("继续");
  yield 2;           // 暂停，返回 2
  yield 3;           // 暂停，返回 3
  console.log("结束");
}

const gen = numberGenerator();
gen.next(); // { value: 1, done: false } —— "开始"
gen.next(); // { value: 2, done: false } —— "继续"
gen.next(); // { value: 3, done: false }
gen.next(); // { value: undefined, done: true } —— "结束"

// 实际应用：自定义迭代器
function* range(start, end, step = 1) {
  for (let i = start; i < end; i += step) {
    yield i;
  }
}

// Generator 也能实现类似 async/await 的效果
function* fetchUser() {
  const user = yield fetch("/api/user");
  const data = yield user.json();
  return data;
}
```

**为什么需要它**：实现惰性求值、自定义迭代器、简化异步流程控制（async/await 底层就基于 Generator）。

**与相关术语的对比和区分**：Generator 返回迭代器，可多次 yield；普通函数一次执行到底。async/await 是 Generator + Promise 的语法糖。

---

## 模块化（CommonJS / ES Modules / AMD）

**一句话定义**：把 JavaScript 代码拆分成独立的、可复用的模块，每个模块有自己的作用域。

**通俗类比**：像工具箱——扳手放扳手格，螺丝刀放螺丝刀格，需要什么就拿什么，不用到处翻找。

**具体示例**：
```javascript
// ===== CommonJS (Node.js) =====
// math.js
const PI = 3.14159;
function add(a, b) { return a + b; }
module.exports = { PI, add };

// app.js
const { PI, add } = require("./math");

// ===== ES Modules (浏览器 + 现代 Node.js) =====
// math.js
export const PI = 3.14159;
export function add(a, b) { return a + b; }
export default class Calculator { /* ... */ }

// app.js
import Calculator, { PI, add } from "./math.js";

// ===== AMD (RequireJS, 已少见) =====
define(["jquery"], function ($) {
  return {
    init: function () { $("body").addClass("ready"); }
  };
});
```

**为什么需要它**：避免全局变量污染、代码按需加载、依赖关系清晰、便于团队协作和复用。

**与相关术语的对比和区分**：CommonJS 同步加载（require），适合 Node.js；ES Modules 异步加载（import），浏览器原生支持；AMD 是早期浏览器模块化方案，现已被 ESM 取代。

---

## 作用域与作用域链

**一句话定义**：作用域决定变量的可见范围，作用域链是从当前作用域逐层向外查找变量的路径。

**通俗类比**：作用域像房间，作用域链像楼层——你在 3 楼找不到东西，去 2 楼找，2 楼没有去 1 楼，一直找到大厅（全局）。

**具体示例**：
```javascript
const global = "全局变量"; // 全局作用域

function outer() {
  const outerVar = "外部变量"; // outer 作用域

  function inner() {
    const innerVar = "内部变量"; // inner 作用域
    console.log(global);   // ✅ 沿作用域链找到全局
    console.log(outerVar); // ✅ 沿作用域链找到 outer
    console.log(innerVar); // ✅ 自己的作用域
  }

  inner();
  // console.log(innerVar); // ❌ inner 的作用域对外不可见
}

// 块级作用域
if (true) {
  let blockVar = "块级变量";
}
// console.log(blockVar); // ❌ 块级作用域外不可见
```

**为什么需要它**：防止变量命名冲突，限制变量的可见性，是理解闭包、this 指向等概念的基础。

**与相关术语的对比和区分**：作用域（Scope）是"在哪能访问"，作用域链（Scope Chain）是"怎么找到"。词法作用域（Lexical Scope）= 静态作用域，由代码书写位置决定，JS 采用此规则。

---

## this 指向

**一句话定义**：`this` 是函数执行时的上下文对象，指向谁取决于函数的调用方式，而非定义位置。

**通俗类比**：this 像"我"这个代词——你说"我饿了"，"我"指的是你；他说"我饿了"，"我"指的是他。同一个词，不同人说指不同对象。

**具体示例**：
```javascript
const obj = {
  name: "Alice",
  greet() { console.log(this.name); }, // 指向 obj
};

obj.greet(); // "Alice" —— 对象调用，this = obj

const fn = obj.greet;
fn(); // undefined —— 独立调用，this = window（严格模式下 undefined）

// call / apply / bind 手动绑定
function greet(greeting) {
  console.log(`${greeting}, I'm ${this.name}`);
}
const user = { name: "Bob" };

greet.call(user, "Hello");       // "Hello, I'm Bob"（逐个传参）
greet.apply(user, ["Hello"]);    // "Hello, I'm Bob"（数组传参）
const boundGreet = greet.bind(user); // 返回新函数，this 永远是 user
boundGreet("Hi");                // "Hi, I'm Bob"

// 箭头函数：this 是定义时的外层作用域，不可修改
const person = {
  name: "Charlie",
  greet: () => {
    console.log(this.name); // window（箭头函数没有自己的 this）
  },
};
```

**为什么需要它**：理解 this 才能正确处理事件回调、类方法、回调函数中的上下文问题。

**与相关术语的对比和区分**：call/apply（立即调用，手动绑定）vs bind（返回新函数，延迟绑定）。箭头函数的 this 不可被 call/apply/bind 改变。

---

## 解构赋值

**一句话定义**：从数组或对象中快速提取值并赋给变量的简洁语法。

**通俗类比**：像拆快递包裹——不用一个个拆内包装，直接把东西倒出来按名字放好。

**具体示例**：
```javascript
// 数组解构
const [a, b, ...rest] = [1, 2, 3, 4, 5];
// a = 1, b = 2, rest = [3, 4, 5]

const [, second] = ["first", "second", "third"]; // 跳过第一个
// second = "second"

// 对象解构
const { name, age, city = "未知" } = {
  name: "Alice",
  age: 25,
};
// name = "Alice", age = 25, city = "未知"（默认值）

// 重命名
const { name: userName } = { name: "Bob" };
// userName = "Bob"

// 嵌套解构
const { address: { street, zip } } = {
  address: { street: "Main St", zip: "12345" },
};

// 函数参数解构
function createUser({ name, age, role = "user" }) {
  return { name, age, role };
}
createUser({ name: "Charlie", age: 30 });
```

**为什么需要它**：大幅简化从复杂数据结构中提取值的代码，减少临时变量。

**与相关术语的对比和区分**：解构赋值是语法特性，不是新变量声明方式。它配合展开运算符（...）和默认值（=）使用更强大。

---

## 展开运算符（...）

**一句话定义**：将数组/对象"展开"为独立的元素/属性，或收集剩余参数。

**通俗类比**：像把一盒巧克力倒出来（展开），或者把桌上的巧克力捡起来放进盒子（收集）。

**具体示例**：
```javascript
// 数组展开
const arr1 = [1, 2, 3];
const arr2 = [...arr1, 4, 5]; // [1, 2, 3, 4, 5]

// 对象展开
const obj1 = { a: 1, b: 2 };
const obj2 = { ...obj1, c: 3 }; // { a: 1, b: 2, c: 3 }

// 浅拷贝
const copy = [...arr1];     // 数组浅拷贝
const objCopy = { ...obj1 }; // 对象浅拷贝

// 收集剩余参数
function sum(...numbers) {
  return numbers.reduce((a, b) => a + b, 0);
}
sum(1, 2, 3); // 6

// 对象合并（后者覆盖前者）
const config = { theme: "dark", lang: "zh" };
const override = { lang: "en" };
const final = { ...config, ...override }; // { theme: "dark", lang: "en" }
```

**为什么需要它**：替代 `concat`、`Object.assign` 等旧写法，让数组/对象操作更直观简洁。

**与相关术语的对比和区分**：展开运算符（spread）是"展开"，剩余参数（rest）是"收集"，语法相同但方向相反。解构赋值 + 展开运算符是黄金搭配。

---

## 可选链（?.）

**一句话定义**：安全地访问嵌套对象的属性，如果中间环节是 `null`/`undefined`，直接返回 `undefined`，不会报错。

**通俗类比**：像问路——"请问张三的老板的老板的电话是多少？"中间任何一个人不在，就不问了，直接说"不知道"。

**具体示例**：
```javascript
const user = {
  name: "Alice",
  address: {
    street: "Main St",
  },
  // 没有 phone 字段
};

// 传统写法（啰嗦）
const street1 = user && user.address && user.address.street;

// 可选链（简洁）
const street2 = user?.address?.street; // "Main St"
const phone = user?.phone?.mobile;     // undefined（不会报错）

// 可选链调用方法
user.greet?.();         // 如果 greet 存在就调用，否则 undefined
user.getAddress?.();    // 如果方法存在才执行

// 可选链访问数组元素
const first = user?.friends?.[0]?.name; // undefined
```

**为什么需要它**：避免写大量 `&&` 防御性检查代码，减少 `Cannot read property of undefined` 错误。

**与相关术语的对比和区分**：`?.`（可选链）处理 null/undefined；`??`（空值合并）处理默认值。两者常配合使用：`data?.name ?? "匿名"`。

---

## 空值合并（??）

**一句话定义**：只有当左侧值为 `null` 或 `undefined` 时，才使用右侧的默认值。

**通俗类比**：像应急方案——只在"真的没人"（null/undefined）时才启用备选方案，其他情况（如 0、""、false）都算"有人在"。

**具体示例**：
```javascript
// ?? vs || 的区别
const count = 0;
console.log(count || 10); // 10（0 是 falsy，被替换）
console.log(count ?? 10); // 0（0 不是 null/undefined，保留）

const name = "";
console.log(name || "匿名"); // "匿名"（"" 是 falsy）
console.log(name ?? "匿名"); // ""（"" 不是 null/undefined，保留）

// 实际应用
function createUser(options) {
  return {
    name: options.name ?? "匿名",
    age: options.age ?? 18,
    role: options.role ?? "user",
  };
}

// 可选链 + 空值合并
const city = user?.address?.city ?? "未知城市";
```

**为什么需要它**：`||` 会把 `0`、`""`、`false` 也当作"无效值"，`??` 只处理真正的空值（null/undefined），语义更精确。

**与相关术语的对比和区分**：`??`（空值合并）只认 null/undefined；`||`（逻辑或）认所有 falsy 值。`??` 不能与 `||` 或 `&&` 直接混用（需加括号）。

---

## WeakMap 与 WeakRef

**一句话定义**：WeakMap 的键必须是对象且为弱引用（不阻止垃圾回收）；WeakRef 是对对象的弱引用，不会阻止垃圾回收。

**通俗类比**：WeakMap 像便利贴贴在东西上——东西扔了（被回收），便利贴也跟着消失，不会占用空间。WeakRef 像偷看隔壁窗户——窗户拆了你就什么都看不见了。

**具体示例**：
```javascript
// WeakMap —— 键必须是对象
const cache = new WeakMap();

let obj = { data: "重要数据" };
cache.set(obj, { timestamp: Date.now() });

console.log(cache.get(obj)); // { timestamp: ... }

obj = null; // 原对象可以被垃圾回收，WeakMap 中的条目自动清除

// 实际应用：给 DOM 节点附加元数据
const metadata = new WeakMap();
const button = document.querySelector("button");
metadata.set(button, { clicks: 0 });
// button 被移除后，相关数据自动清除，不会内存泄漏

// WeakRef —— 弱引用对象
let heavyObject = { data: new Array(1000000) };
const ref = new WeakRef(heavyObject);

heavyObject = null; // 可被回收
console.log()); // 可能是 undefined（已被回收）

// FinalizationRegistry —— 对象被回收时的回调
const registry = new FinalizationRegistry((heldValue) => {
  console.log(`对象被回收: ${heldValue}`);
});

let target = { name: "test" };
registry.register(target, "target的标识");
target = null; // 对象被回收时触发回调
```

**为什么需要它**：普通 Map/Set 会持有对象的强引用，导致对象无法被垃圾回收（内存泄漏）。WeakMap/WeakRef 让你附加数据而不阻止回收。

**与相关术语的对比和区分**：WeakMap（键弱引用）vs Map（键强引用）；WeakRef（值弱引用）vs 普通变量（值强引用）。WeakMap 键不可枚举（无 size、无 keys()），设计目的就是"偷偷附加数据"。

## 相关术语

[[HTML & CSS 核心概念]]、[[React深入]]、[[Vue3核心]]、[[前端工程化]]、[[前端工程化核心概念]]、[[前端框架核心概念]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
