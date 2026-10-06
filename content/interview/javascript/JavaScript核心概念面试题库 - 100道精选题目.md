---
title: "JavaScript核心概念面试题库 - 100道精选题目"
tags: []
source: "baike"
source_path: "技术题库 / JavaScript核心"
collected: "2026-09-05"
status: "imported"
---

# JavaScript 核心概念面试题库 - 100道精选题目

> 题量 **100 道**，覆盖变量与数据类型、作用域与闭包、原型与继承、this 与函数、异步编程、事件循环、对象与数组、ES6+ 语法、DOM 与浏览器、错误处理、性能与内存、设计模式共 12 个板块。
> 每题标注难度（初级 / 中级 / 高级），给参考答法、代码验证与追问方向；编号 1–100 连续。

---

## 一、变量与数据类型（9 题）

### 1. JavaScript 有哪些数据类型？typeof、instanceof、Object.prototype.toString 各自能判断什么？｜初级

共 8 种：7 个原始类型 `undefined`、`null`、`boolean`、`number`、`string`、`symbol`、`bigint`，加 1 个引用类型 `object`（Array / Function / Date / RegExp 等都是它的子类）。

三种判断手段各有死角：

| 手段 | 能区分 | 失效场景 |
|------|--------|----------|
| `typeof` | 原始类型、`function` | `typeof null === 'object'`；数组 / 日期 / 正则一律 `object` |
| `instanceof` | 具体构造器（走原型链） | 原始类型恒为 false；跨 iframe / Realm 失效 |
| `Object.prototype.toString.call` | 几乎所有内置类型 | 自定义类只返回 `[object Object]`，除非设置 `Symbol.toStringTag` |

```javascript
typeof null            // "object"  —— 1995 年的历史 bug，为兼容旧站点永不修复
typeof function(){}    // "function"
[] instanceof Array    // true；跨 iframe 时 Array 来自另一 Realm，判定为 false
Object.prototype.toString.call([])  // "[object Array]" —— 最可靠
```

> ⚠️ 注意：判定数组优先 `Array.isArray()`，它内部处理了跨 Realm；判定类数组用 `typeof x.length === 'number' && !Array.isArray(x)`。

> 🔍 追问：`Symbol.toStringTag` 怎么让自定义类的 toString 判定返回你想要的名字？

### 2. var、let、const 的区别是什么？暂时性死区（TDZ）什么时候会真的报错？｜初级

| 维度 | `var` | `let` | `const` |
|------|-------|-------|---------|
| 作用域 | 函数作用域 | 块级作用域 | 块级作用域 |
| 提升 | 提升并初始化为 `undefined` | 提升但进 TDZ | 提升但进 TDZ |
| 重复声明 | 允许 | 报错 | 报错 |
| 必须初始化 | 否 | 否 | 是 |
| 可重新赋值 | 是 | 是 | 否（绑定不可变） |

TDZ 不是“没提升”，而是提升后处于不可访问状态，从块开始到声明语句之间访问就抛 `ReferenceError`：

```javascript
console.log(a); // undefined —— var 已初始化
console.log(b); // ReferenceError: Cannot access 'b' before initialization
var a = 1;
let b = 2;

if (true) {
  // 下面这行的报错来自 TDZ，而不是“外部 c 没定义”
  typeof c; // ReferenceError（typeof 在 TDZ 上不安全，这是它唯一的破例）
  let c = 3;
}
```

> 🎯 关键要点：`const` 锁的是**绑定**不是**内容**——`const arr = []` 仍可 `arr.push()`，只是不能再 `arr = []`。

### 3. null 和 undefined 的区别？什么时候该用哪个？｜初级

- `undefined`：由引擎产生，代表“还没有值”——未赋值的变量、缺失的参数、函数无返回值、访问不存在的属性。
- `null`：由开发者显式写入，代表“这里就是空的”，是有意的语义。

```javascript
null == undefined   // true（Abstract Equality 里的特例）
null === undefined  // false
typeof null         // "object"；typeof undefined // "undefined"

JSON.stringify({ a: undefined, b: null })  // '{"b":null}' —— undefined 会被整条丢弃
function f(x = '默认') {}
f(undefined); // '默认'（默认值只对 undefined 生效）
f(null);      // null
```

> 💡 提示：接口返回里“字段缺失”用 `undefined` 或干脆不返回该键，“字段为空”用 `null`，两者语义混用会让 `??` 与 `\|\|` 产生不同的兜底结果。

### 4. 为什么 `0.1 + 0.2 !== 0.3`？金额计算应该怎么做？｜中级

IEEE 754 双精度用 64 位二进制表示，`0.1`、`0.2` 都是无限循环二进制，只能存近似值，相加后的舍入结果比 `0.3` 略大 `4.44e-17`。

```javascript
0.1 + 0.2                 // 0.30000000000000004
Math.abs(0.1 + 0.2 - 0.3) < Number.EPSILON  // true —— 浮点比较要用误差范围
(0.1 + 0.2).toFixed(2)    // "0.30"（字符串，别拿它继续算）
```

金额场景三条路，按场景选：

| 方案 | 做法 | 适用 |
|------|------|------|
| 整数分 | 全部以“分”为单位存储运算，出口再除 100 | 绝大多数电商 / 支付 |
| 字符串十进制库 | `decimal.js` / `big.js` | 利率、汇率、需要精确小数的场景 |
| `BigInt` | 原子单位（如 wei）整数运算 | 区块链、超大整数 ID |

顺带两个必答点：`NaN` 会污染所有算术运算，且 `NaN !== NaN`；判断必须用 `Number.isNaN(x)`（只对真 `NaN` 返回 true），而全局 `isNaN("abc")` 会先做类型转换返回 true，属于陷阱。

### 5. `==` 和 `===` 的区别？隐式类型转换的规则是什么？｜中级

`===` 要求类型与值都相等，不做转换；`==` 走 Abstract Equality Comparison，会按固定顺序转换：

```javascript
null == undefined        // true
'1' == 1                 // true：字符串转数字
true == 1                // true：布尔转数字
[] == false              // true：[] → '' → 0，false → 0
[] == ![]                // true：右侧 ![] 先算出 false
'0' == false             // true；但 [] == '0' 是 false（走的路径不同）
null == 0                // false —— null 只与 undefined 相等
```

对象与原始值比较时先走 `ToPrimitive`：默认 hint 是 `default`，依次尝试 `valueOf` → `toString`。

```javascript
const obj = { valueOf: () => 42 };
obj == 42   // true
```

> 🎯 关键要点：团队规范里禁掉 `==` 之后，唯一值得保留的例外是 `x == null`——一次同时覆盖 `null` 和 `undefined`，比 `x === null || x === undefined` 更简洁且无副作用。

### 6. Symbol 有什么用？内置的 well-known symbols 有哪些？｜中级

`Symbol()` 每次调用都返回唯一值，核心用途是**避免属性名冲突**，同时天然“不可被 `JSON.stringify` 序列化、不出现在 `for...in` / `Object.keys` 里”。

```javascript
const key = Symbol('id');
const obj = { [key]: 1, name: 'x' };
JSON.stringify(obj)   // '{"name":"x"}' —— Symbol 键被忽略
Object.getOwnPropertySymbols(obj)  // 只能这样拿到
```

内置符号是给引擎调用的钩子，面试常问这几个：

| 内置符号 | 触发时机 |
|----------|----------|
| `Symbol.iterator` | `for...of`、展开运算符、解构 |
| `Symbol.asyncIterator` | `for await...of` |
| `Symbol.toPrimitive` | 类型转换（优先级高于 `valueOf` / `toString`） |
| `Symbol.toStringTag` | `Object.prototype.toString.call` 的返回值 |
| `Symbol.hasInstance` | `instanceof` 的判定逻辑 |

`Symbol.for('x')` 走全局注册表，同名字符串返回同一个 Symbol——跨模块共享键时用它，否则用 `Symbol()`。

### 7. 原始类型为什么能调用方法？装箱是怎么发生的？｜中级

访问原始值的属性时，引擎临时创建一个包装对象（`new String/Number/Boolean`），读取完成后立刻丢弃，所以下面的赋值是无效的：

```javascript
const s = 'abc';
s.x = 1;
s.x        // undefined —— 包装对象用完即弃，属性没留在任何地方

(1).toString()   // 必须加括号，否则 .1 被解析成小数点
1..toString()    // 也可以这么写
```

转换到原始值的优先级：`Symbol.toPrimitive` → `valueOf` → `toString`；而 `String()`、模板字符串用的是 `hint = "string"`，顺序会变成 `toString` → `valueOf`。

> ⚠️ 注意：`new Boolean(false)` 是**真值对象**，`if (new Boolean(false)) {}` 会进分支；永远不要用 `new` 构造包装对象。

### 8. 变量提升提升的到底是什么？函数声明和 var 有什么不同？｜中级

提升的是**声明**，不是赋值。执行上下文创建阶段先扫一遍，把 `var` 初始化成 `undefined`、函数声明整体赋值，`let/const` 只登记不初始化。

```javascript
console.log(fn()); // 'ok' —— 函数声明整体提升，可以在定义前调用
function fn() { return 'ok'; }

console.log(expr()); // TypeError: expr is not a function —— 表达式按 var 处理
var expr = function () { return 'x'; };

// 同名冲突：函数声明优先级高于 var，后续赋值又会覆盖它
var a = 1;
function a() {}
console.log(typeof a); // "number"
```

块级作用域里的函数声明按块提升，行为在严格模式与非严格模式历史上不一致，现代引擎已统一到块内——但依赖这个细节本身就是坏味道。

> 🔍 追问：`if (true) { function g() {} }` 之后 `g` 在外面是否可见？为什么说这是要靠 `let` 规避的历史包袱？

### 9. 原始值和引用值在内存中如何存储和传递？｜中级

原始值大小固定，存放在栈上 / 值内联在变量槽里，赋值和传参都是**拷贝值**；引用值在栈上只放一个指向堆内存的指针，赋值传的是指针的拷贝，因此两个变量指向同一个对象。

```javascript
let a = { n: 1 };
let b = a;
b.n = 2;
console.log(a.n); // 2 —— 同一个对象

function change(o, p) {
  o.n = 99;      // 改的是堆里那个对象，外部可见
  p = { n: 100 };// 重新赋值只改了函数内的局部指针，外部看不到
}
let p = { n: 0 };
change(a, p);
console.log(a.n, p.n); // 99 0
```

这解释了两个高频疑问：为什么 `const` 声明的对象还能改（绑定不变，对象可变），以及为什么浅拷贝会“互相影响”（嵌套层仍共享指针）。

## 二、作用域、闭包与内存（12 题）

### 10. 请详细解释 JavaScript 中的闭包（Closure）是什么，它有哪些实际应用场景？｜中级

闭包 = 函数 + 声明它的词法环境。内部函数引用了外部函数的变量，即使外部函数已经返回，这些变量仍被保留在堆上供其访问。

```javascript
function createCounter() {
  let count = 0;              // 私有状态，外部拿不到
  return {
    inc: () => ++count,
    get: () => count,
  };
}
const c = createCounter();
c.inc(); c.inc();
c.get();        // 2
```

真实场景，按出现频率排：

| 场景 | 闭包里被捕获的东西 |
|------|-------------------|
| 防抖 / 节流 | `timer` 句柄 |
| 记忆化（memoize） | 缓存 Map |
| 模块私有状态 | 不想暴露的变量 |
| 一次性初始化（惰性单例） | 已创建的实例 |
| 柯里化 / 偏应用 | 已收集的参数 |

回答时别停在“能记住变量”，补一句代价：闭包持有引用，会让本该回收的对象活得更久，长生命周期的订阅 / 定时器里尤其要注意解绑。

> 💡 提示：能不能说出“闭包的变量保存在 `[[Environment]]` 指向的堆对象里，而非栈上”，是区分背书和理解的分水岭。

### 11. JavaScript 中的作用域链是什么？变量查找是怎么走的？｜初级

每个执行上下文都有一个变量对象，函数创建时把外层的作用域串进 `[[Scope]]`，查找变量就从当前作用域沿这条链向上找，直到全局作用域；找不到就是 `ReferenceError`（读取）或静默创建全局变量（非严格模式下赋值）。

```javascript
const global = 'g';
function outer() {
  const a = 'a';
  function inner() {
    const b = 'b';
    return [a, b, global]; // 沿作用域链逐级向外找
  }
  return inner();
}
```

关键性质：这条链在**函数定义时**就确定了，与调用位置无关——所以叫词法（静态）作用域。同一段代码放到别处调用，查到的变量不会变。

> ⚠️ 注意：作用域链查找是有成本的，深层嵌套里反复访问外层变量，现代引擎会靠内联缓存优化，但把高频变量缓存到局部（`const len = arr.length`）在热路径上依然有效。

### 12. 词法作用域和动态作用域有什么区别？`with` 和 `eval` 为什么被劝退？｜高级

词法作用域按代码书写位置决定查找路径；动态作用域按调用栈决定。JS 是词法作用域，但 `this` 是动态的——这是最容易混淆的一点：变量的作用域静态，`this` 的绑定动态。

```javascript
const x = 'outer';
function f() { return x; }
function g() { const x = 'inner'; return f(); }
g(); // 'outer' —— 若是动态作用域会返回 'inner'
```

`with` / `eval` 破坏静态可分析性：引擎无法在编译期确定变量位置，只能退化为慢速查找，且 `"use strict"` 下 `with` 直接语法报错。间接 `eval` 还会在全局作用域执行，是注入风险源。

> 🔍 追问：为什么说 `this` 是动态作用域在 JS 里的“局部实现”？箭头函数的 `this` 又为什么变回了词法的？

### 13. 循环里用 var 创建闭包为什么会输出同一批值？`let` 是怎么修好的？｜中级

`var` 是函数作用域，整个循环只有**一个** `i`，所有回调捕获的是同一个变量槽，等回调执行时循环早已结束：

```javascript
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i)); // 3 3 3
for (let j = 0; j < 3; j++) setTimeout(() => console.log(j)); // 0 1 2
```

`let` 的修复不是“块级作用域”四个字，而是规范里的**每次迭代绑定**：每轮循环创建一个新绑定，并把上一轮的值拷贝进去，所以每个回调捕获的是独立的 `j`。

老代码的三种等价改法：

```javascript
for (var i = 0; i < 3; i++) (function (k) { setTimeout(() => console.log(k)); })(i);
for (var i = 0; i < 3; i++) setTimeout(console.log, 0, i);   // 额外参数传参
for (var i = 0; i < 3; i++) { const k = i; setTimeout(() => console.log(k)); }
```

### 14. IIFE 解决什么问题？现在还需要它吗？｜初级

立即执行函数通过函数作用域造出私有空间，避免污染全局，同时让 `var` 时代也能拿到“一次性隔离环境”。经典用法是模块模式：

```javascript
const Counter = (function () {
  let count = 0;                       // 私有
  return { inc: () => ++count };       // 公开
})();
```

现代替代品已经覆盖了它的绝大部分用途：块级作用域加 `{}` 就能隔离 `let/const`；模块系统天然有文件级作用域；`await` 顶层可用后连“包一层 async IIFE”都省了。

> 🎯 关键要点：今天还在写 IIFE，只有两种情况合理——需要**函数表达式立即调用**来限定 `this`，或需要在一段同步代码里手工构造作用域给闭包垫底。

### 15. ES Module 和 CommonJS 的作用域与导出语义有何不同？｜高级

| 维度 | ESM | CommonJS |
|------|-----|----------|
| 加载时机 | 静态解析，编译期确定依赖 | 运行时 `require`，可条件加载 |
| 值语义 | **活绑定**，导出方后续变化可见 | 导出时的**值拷贝**（对象共享引用） |
| `this`（顶层） | `undefined` | `module.exports` |
| 循环依赖 | 提升后可拿到未初始化绑定（TDZ 报错） | 拿到半成品对象，常为 `undefined` |
| 严格模式 | 强制 | 默认非严格 |

```javascript
// a.mjs
export let n = 1;
export function bump() { n++; }
// b.mjs
import { n, bump } from './a.mjs';
bump();
console.log(n);  // 2 —— 活绑定
```

`import()` 动态导入返回 Promise，是唯一的条件加载手段，也是构建工具做代码分割的切入点。

> ⚠️ 注意：`import` 会被提升到文件顶部，写在中间也先执行——不要在模块顶层写有副作用的顺序依赖代码。

### 16. 变量遮蔽（shadowing）会带来什么问题？怎么排查意外的全局变量？｜初级

内层作用域用同名 `let/const` 声明会遮蔽外层同名变量，外层变量在该块内彻底不可访问。危险点是这种遮蔽往往是“手误 + 复制粘贴”的产物，且不报错：

```javascript
const user = { name: 'a' };
function f() {
  const user = 'oops';   // 遮蔽，外层对象在这里不可见
  return user.toUpperCase();
}
```

排查全局变量泄漏：`"use strict"` 让未声明赋值直接抛错，这是最有效的一道闸；`Object.keys(globalThis).filter(k => !whitelist.has(k))` 可以做运行时巡检；打包器 + 未使用变量告警能抓住大部分静态问题。

### 17. 闭包真的会导致内存泄漏吗？怎么验证？｜高级

“闭包导致内存泄漏”的说法不准确：闭包只是**延长生命周期**，泄漏的定义是“不再使用的对象仍被强引用而无法回收”。真正出问题的是这两类写法：

```javascript
// 1. 订阅/定时器拿到了闭包，但没人负责解绑
element.addEventListener('click', handler);  // 组件卸载时未 removeEventListener
setInterval(makeHandler(), 1000);            // 句柄丢失，永远清不掉

// 2. 闭包持有大对象，而闭包本身被长期引用
function attach() {
  const huge = new Array(1e6).fill('*');     // 只是为了用一个字段
  return () => huge.length;
}
```

验证方法：Chrome DevTools 的 Memory 面板取两次堆快照（Heap Snapshot），在 Comparison 视图里看被保留的对象增长；或直接用 `Performance monitor` 观察 JS Heap 的锯齿是否在强制 GC 后仍单调上升。

> 🎯 关键要点：只有“不需要 + 还被引用”才叫泄漏。先回答清楚这个定义，再谈弱引用（`WeakMap`、`WeakRef`）与手动解绑。

### 18. 用闭包实现私有状态，和 WeakMap、`#private` 字段相比怎么选？｜中级

```javascript
// 闭包：真私有，但每个实例都创建一份新函数，无法被外部工具探到
function create() { let v = 0; return { get: () => v, set: n => v = n }; }

// WeakMap：模块内可互相访问，实例销毁后自动释放，适合需要跨方法共享的私有数据
const priv = new WeakMap();
class A { constructor() { priv.set(this, 0); } }

// #private：语法级私有，引擎保证不可穿透，调试体验最好（能看到 #x）
class B { #v = 0; get v() { return this.#v; } }
```

取舍表：

| 方案 | 私有强度 | 内存/性能 | 典型场景 |
|------|----------|-----------|----------|
| 闭包 | 最高（连反射都拿不到） | 每个实例复制方法，实例多时开销大 | 少量实例、纯函数式模块 |
| WeakMap | 高（仅持有 map 的模块可见） | 无实例复制，GC 友好 | 需要在多个方法间共享且要能释放 |
| `#private` | 高（语法层强制） | 无额外开销 | 有类结构的现代代码 |

### 19. 手写一个 memoize，并说明缓存该什么时候失效｜中级

```javascript
function memoize(fn, keyFn = (...args) => JSON.stringify(args)) {
  const cache = new Map();
  return function (...args) {
    const k = keyFn(...args);
    if (cache.has(k)) return cache.get(k);
    const v = fn.apply(this, args);
    cache.set(k, v);
    return v;
  };
}
```

`JSON.stringify` 作默认键有三个坑：键顺序不同算不同键、`undefined` / 函数 / `Symbol` 会被丢弃或忽略、循环引用直接抛错。生产里通常显式传 `keyFn`，或只对单参数做记忆化。

缓存失效策略按场景选：纯函数且入参空间有限 → 永不失效；依赖外部状态 → 带上版本号或时间戳做键；长期运行的服务 → 用 `Map` 加 LRU 上限，避免缓存本身变成内存泄漏。

### 20. 垃圾回收（GC）是怎么判断对象“该死了”的？｜高级

主流引擎用**可达性**而非引用计数：从根（全局对象、当前调用栈、活跃闭包、DOM 引用等）出发遍历，遍历不到的对象才算垃圾，因此循环引用不会造成泄漏。

V8 的分代策略：

| 区域 | 对象特征 | 回收算法 |
|------|----------|----------|
| 新生代 | 新创建、存活短 | Scavenge：把存活对象复制到另一半空间，代价与存活量成正比 |
| 老生代 | 活过一次以上回收 | 标记 - 清除 + 标记 - 压缩：分步执行减少停顿 |

“全停顿”已经过时：V8 用并发标记、增量标记把整理工作切片到主线程空闲时，`FinalizationRegistry` 则给注册过的对象在回收时提供一次性回调（但时机不保证）。

> 🔍 追问：为什么说“对象池 / 对象复用”在高频创建场景下反而可能加重老生代压力？

### 21. 手写防抖与节流，并说明各自的适用场景｜中级

```javascript
function debounce(fn, wait, immediate = false) {
  let timer = null;
  return function (...args) {
    if (immediate && !timer) fn.apply(this, args);
    clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      if (!immediate) fn.apply(this, args);
    }, wait);
  };
}

function throttle(fn, wait) {
  let last = 0;
  return function (...args) {
    const now = Date.now();
    if (now - last >= wait) { last = now; fn.apply(this, args); }
  };
}
```

| 场景 | 选哪个 | 理由 |
|------|--------|------|
| 搜索联想输入 | 防抖（约 300ms） | 只在停止输入后发一次请求 |
| 窗口 resize 重算布局 | 节流或 `requestAnimationFrame` | 需要过程中的稳定节奏 |
| 按钮防连点 | 防抖 immediate 版 | 首次立即执行，后续窗口内忽略 |
| 滚动加载埋点 | 节流 | 保证按固定频率采样 |

> ⚠️ 注意：两者都返回闭包，组件卸载时一定要保留 `cancel()` 出口清掉定时器，否则就是第 17 题里的泄漏典型。

## 三、原型与继承（9 题）

### 22. 请解释原型链（Prototype Chain）是什么，它是如何实现继承的？｜高级

每个对象都有一个内部槽 `[[Prototype]]`（通过 `Object.getPrototypeOf` 读写，`__proto__` 只是它的访问器），指向另一个对象或 `null`。访问属性时先查自身，再沿 `[[Prototype]]` 链逐级向上，直到 `null` 返回 `undefined`——这就是原型链。

```javascript
function Animal(name) { this.name = name; }
Animal.prototype.speak = function () { return this.name + ' makes a sound'; };

function Dog(name) { Animal.call(this, name); }          // 借用构造：继承实例属性
Dog.prototype = Object.create(Animal.prototype);         // 断开旧原型，接上 Animal
Dog.prototype.constructor = Dog;                         // 修回构造器指向
Dog.prototype.bark = function () { return this.name + ' barks'; };

const d = new Dog('Rex');
d.bark();               // 自身原型链上找到
d.speak();              // 沿链找到 Animal.prototype
```

属性查找代价与原型链长度成正比，所以别做“层层继承十几级”的设计；链上找的是**属性**，`this` 始终指向调用者而非定义者——这是原型继承“方法共享、状态独立”的本质。

### 23. prototype、`__proto__`、constructor 三者是什么关系？｜中级

三句话定位：

- `prototype`：只有**函数**才有（箭头函数除外），它是“将来被 `new` 出来的实例的原型”。
- `[[Prototype]]`（`__proto__`）：每个**对象**都有，指向自己的原型，“我是谁的实例”。
- `constructor`：`prototype` 对象上的一个属性，默认指回构造函数，可被覆写，因此它不总是可靠的。

```javascript
function F() {}
const f = new F();
Object.getPrototypeOf(f) === F.prototype       // true
F.prototype.constructor === F                  // true（默认关系）
// 重写 prototype 会丢掉 constructor 指向，必须手动补回
F.prototype = {};
new F().constructor === F                      // false —— 变成 Object 了
```

> ⚠️ 注意：`f.__proto__` 与 `F.prototype` 指向同一个对象，但把 `F.prototype` 整个替换后，已存在的实例仍指向旧原型，不会自动跟着换。

### 24. `new` 操作符做了什么？手写一个 new｜中级

四步：创建空对象 → 把它的 `[[Prototype]]` 指向构造函数的 `prototype` → 以它为 `this` 执行构造函数 → 若构造函数返回对象则用返回值，否则用这个新对象。

```javascript
function myNew(Ctor, ...args) {
  if (typeof Ctor !== 'function') throw new TypeError('not a constructor');
  const obj = Object.create(Ctor.prototype);
  const ret = Ctor.apply(obj, args);
  return (ret !== null && (typeof ret === 'object' || typeof ret === 'function')) ? ret : obj;
}

// 验证
function P(name) { this.name = name; return 1; }        // 返回原始值被忽略
myNew(P, 'a').name;                                     // 'a'
function Q() { return { hijack: true }; }               // 返回对象则顶替实例
myNew(Q).hijack;                                        // true
```

> 🔍 追问：为什么 `new` 一个箭头函数会报错？（箭头函数没有 `[[Construct]]` 内部方法，也没有 `prototype`。）

### 25. `instanceof` 的原理是什么？哪些情况会判错？｜中级

`instanceof` 沿左侧对象的原型链查找，看能否命中右侧构造函数的 `prototype`。

```javascript
function myInstanceof(obj, Ctor) {
  if (typeof Ctor !== 'function') throw new TypeError('Right-hand side is not callable');
  const target = Ctor.prototype;
  let proto = Object.getPrototypeOf(obj);
  while (proto) {
    if (proto === target) return true;
    proto = Object.getPrototypeOf(proto);
  }
  return false;
}
```

失效场景：

| 场景 | 结果 | 原因 |
|------|------|------|
| `1 instanceof Number` | false | 原始值不是对象 |
| 跨 iframe / Realm | false | 两侧 `Array` 是不同的构造函数对象 |
| `Object.create(null) instanceof Object` | false | 原型链是空的 |
| 自定义 `Symbol.hasInstance` | 可能反直觉 | 判定逻辑已被改写 |

> 💡 提示：替代方案是 `Array.isArray`、`Object.prototype.toString.call`，或给类加一个显式的 `Symbol.hasInstance` / 品牌字段（duck-typing）。

### 26. ES6 class 和原型继承是什么关系？`super` 的两种语义是什么？｜高级

`class` 是原型继承的语法糖，但有三处不是纯粹糖：class 声明不提升（进 TDZ）、class 内部强制严格模式、类方法不可枚举。

```javascript
class Animal {
  constructor(name) { this.name = name; }
  speak() { return `${this.name} makes a sound`; }
  static create(n) { return new this(n); }      // static 方法里的 this 指向子类
}
class Dog extends Animal {
  constructor(name) { super(name); }            // 语义一：调用父类构造函数（必须在用 this 前调用）
  speak() { return super.speak() + ' woof'; }   // 语义二：调用父类同名方法（走父类原型）
}
```

继承链不是简单的 `Dog.prototype.__proto__ = Animal.prototype`，还有一条：`Object.getPrototypeOf(Dog) === Animal`，所以 `Dog.create()` 里的 `this` 是 `Dog` 而不是 `Animal`——这是很多人没答上来的点。

> ⚠️ 注意：子类构造函数中 `this` 由 `super()` 创建的，任何在 `super()` 之前访问 `this` 都会抛 `ReferenceError`。

### 27. 原型链继承、构造函数继承、组合继承、寄生组合继承各有什么问题？｜高级

| 方案 | 做法 | 问题 |
|------|------|------|
| 原型链继承 | `Child.prototype = new Parent()` | 引用类型属性被所有实例共享；无法传参 |
| 构造函数继承 | 父构造函数 `call(this)` | 方法每个实例一份，不复用；拿不到父类原型方法 |
| 组合继承 | 上面两者结合 | 父构造函数被调用两次，原型上多一份冗余实例属性 |
| 寄生组合继承 | 实例属性靠 `call`，原型靠 `Object.create(Parent.prototype)` | 无明显缺陷，是 ES5 时代的标准答案 |

```javascript
function inherit(Child, Parent) {
  Child.prototype = Object.create(Parent.prototype, {
    constructor: { value: Child, writable: true, configurable: true },
  });
  Object.setPrototypeOf(Child, Parent);   // 静态属性继承
}
```

`class extends` 编译后的产物本质就是寄生组合继承。回答时把“父构造函数只调用一次”作为判断标准，一说就清楚。

### 28. 为什么说给原型频繁加属性会拖慢性能？｜高级

JS 引擎为每个对象构建**隐藏类（hidden class / shape）**，并给属性访问点记录**内联缓存（inline cache）**。稳定形状的对象访问是单态（monomorphic）的，能被优化成一次偏移量读取；对象形状频繁变化会让调用点退化为多态甚至超态（megamorphic），优化失效。

```javascript
// 不好的写法：先创建再逐个加属性，每次加属性都触发隐藏类迁移
const p = {}; p.x = 1; p.y = 2;

// 好：字面量一次成型，形状稳定
const q = { x: 1, y: 2 };

// 更糟：删属性会把对象打成字典模式（dictionary mode）
delete q.x;   // 后续访问走哈希表，明显变慢
```

原型上增删属性会让所有依赖该原型的对象共享一个“形状变更”信号，波及面更大。实践结论：实例属性在构造函数 / 类字段里一次声明完；`delete` 用赋 `undefined` 或新建对象替代。

### 29. `Object.create(null)` 有什么用？`for...in` 和原型污染怎么防？｜中级

`Object.create(null)` 造出没有原型的裸对象，适合做**纯字典**：不带 `toString`、`hasOwnProperty` 这类继承来的键，也不会被原型链上的属性干扰。

```javascript
const dict = Object.create(null);
dict['__proto__'] = 1;      // 就是一条普通属性，不会去改原型
'toString' in dict;         // false

const normal = {};
console.log('toString' in normal);   // true —— 继承来的
```

原型污染的现实风险：把用户输入当键写进普通对象，`__proto__` / `constructor` / `prototype` 这类键可能一路污染到 `Object.prototype`。防线是三条——用 `Object.create(null)` 或 `Map` 承载不可信键、`Object.hasOwn(obj, k)` 判自身属性、递归合并时黑名单过滤危险键。

> 🔍 追问：`for...in` 会遍历原型链上的可枚举属性，怎么只拿自身属性？（`Object.keys` / `hasOwn` 过滤 / 加 `Object.prototype.hasOwnProperty.call`。）

### 30. “组合优于继承”在 JavaScript 里怎么落地？｜中级

继承表达的是“是一种”，组合表达的是“有一个 / 能做某事”。典型反例是让 `AdminUser extends User extends Person` 一路下去，加一个“能审核”的能力就得改整条链。

三种常见落地方案：

```javascript
// 1. Mixin：混入能力，注意 Object.assign 是浅拷贝，且同名会覆盖
const canLog = (Base) => class extends Base {
  log() { return `${this.constructor.name} logged`; }
};
class Service {}
class UserService extends canLog(Service) {}

// 2. 策略对象：把变化点抽成可替换的函数属性
class Exporter {
  constructor(strategy) { this.strategy = strategy; }
  run(data) { return this.strategy(data); }
}

// 3. 委托：持有而不继承，显式暴露所需方法
class Logger { info() {} }
class OrderService {
  #logger = new Logger();
  info(msg) { return this.#logger.info(msg); }
}
```

选型建议：需要复用**状态**用继承，需要复用**行为**用组合，需要横切能力（日志、重试、鉴权）优先装饰器 / 高阶函数。

## 四、this、函数与调用（9 题）

### 31. 箭头函数与普通函数有什么区别？什么场景必须用箭头函数？｜初级

四点差异，答全了才有说服力：

| 维度 | 普通函数 | 箭头函数 |
|------|----------|----------|
| `this` | 调用时确定，随调用方式变 | 定义时确定，取外层词法 `this`，且不可被 `call/apply/bind` 改 |
| `arguments` | 有自己的 `arguments` | 没有，用剩余参数 |
| 构造能力 | 可 `new`，有 `prototype` | 不可 `new`，无 `prototype` |
| 其他 | 可作生成器、有 `new.target` | 无 `new.target`，不能作生成器 |

```javascript
class Person {
  constructor(name) { this.name = name; }
  sayBad() { setTimeout(function () { return this.name; }, 0); }   // undefined（this 是 timer）
  sayGood() { setTimeout(() => this.name, 0); }                    // 'John'
}
```

必须用箭头函数的场景：把方法当回调传出去还想保留外层 `this`；需要保证 `this` 不被调用方改写（如类字段里的处理器）。不该用的场景：对象字面量里想用 `this` 指向该对象、需要 `arguments`、需要被 `new`。

### 32. this 的绑定规则有哪几条？优先级怎么排？｜中级

按优先级从高到低：`new` 绑定 → 显式绑定（`call/apply/bind`）→ 隐式绑定（`obj.fn()`）→ 默认绑定（严格模式 `undefined`，非严格模式全局对象）。箭头函数跳过整套规则，直接取词法 `this`。

```javascript
function who() { return this?.name ?? 'undefined'; }
const obj = { name: 'obj', who };
who();                 // 'undefined'（严格模式）/ 全局对象（非严格）
obj.who();             // 'obj' —— 隐式绑定
obj.who.call({ name: 'x' });  // 'x' —— 显式绑定赢

// 绑定丢失：方法被“摘”出来后就是一次普通调用
const f = obj.who;
f();                   // 'undefined'
setTimeout(obj.who, 0);// 同样是普通调用
```

> 🎯 关键要点：“隐式绑定丢失”是最高频的线上事故来源，固定套路是 `bind(this)` / 箭头函数 / 类字段保证 `this` 不被摘掉。

### 33. call、apply、bind 有什么区别？手写一个 bind｜中级

`call`/`apply` 立即执行，只是传参形式不同（列表 vs 数组）；`bind` 返回一个永久绑定 `this` 的新函数，且支持柯里化传参。

```javascript
Function.prototype.myBind = function (ctx, ...preset) {
  const fn = this;
  function bound(...args) {
    // new 调用时 this 应指向新实例而不是 ctx
    return fn.apply(this instanceof bound ? this : (ctx ?? globalThis), [...preset, ...args]);
  }
  bound.prototype = Object.create(fn.prototype || Object.prototype);
  return bound;
};
```

| 方法 | 执行时机 | 参数形式 | 返回 |
|------|----------|----------|------|
| `call` | 立即 | 逐个 | 原函数返回值 |
| `apply` | 立即 | 数组 | 原函数返回值 |
| `bind` | 延迟 | 逐个（可预设） | 新函数（可再 `new`） |

> ⚠️ 注意：`bind` 的 `this` 无法被再次 `bind` 覆盖，但用 `new` 调用绑定函数时，`this` 会被新实例接管——这处细节最能看出候选人是否真写过实现。

### 34. 什么是函数柯里化（Currying）？它有什么实际价值？｜中级

柯里化把 `f(a,b,c)` 变成 `f(a)(b)(c)`，本质是“固定部分参数，返回等待剩余参数的新函数”。

```javascript
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) return fn.apply(this, args);
    return (...rest) => curried.apply(this, [...args, ...rest]);
  };
}

const add = (a, b, c) => a + b + c;
const curriedAdd = curry(add);
curriedAdd(1)(2)(3);   // 6
curriedAdd(1, 2)(3);   // 6
curriedAdd(1)(2, 3);   // 6
```

| 价值 | 说明 |
|------|------|
| 参数复用 | 先固定公共参数，如 `const apiGet = request('GET')` |
| 延迟执行 | 等条件齐了再算，配合 `lodash.flow` 组管道 |
| 提升可测性 | 单参数函数更易组合、更易单测 |

`fn.length` 只统计**第一个默认值之前**的形参个数，所以带默认值或剩余参数的函数，`curry` 的行为会与预期不符——这是实现层面的必答补充。

### 35. 默认参数、剩余参数、arguments、`length` 之间有哪些坑？｜初级

```javascript
function f(a, b = 1, ...rest) {
  return { a, b, rest, len: f.length, args: arguments.length };
}
f(1, undefined, 2, 3);
// b 走默认值；f.length === 1（默认值会截断计数）；arguments 是类数组且有 length
```

- `f.length`：形参个数，遇到第一个默认值就停，因此 `f.length === 1`。
- `arguments`：类数组、非严格模式下与形参**双向同步**；用了默认值 / 剩余参数后两个特性都受影响，现代代码一律用剩余参数替代。
- 默认参数在**调用时**求值（不像 Python 那样在定义时求一次），因此可以写 `function f(x, arr = [])` 而不会共享数组。
- 类数组转真数组：`Array.from(arguments)` 或 `[...arguments]`。

> 💡 提示：`arguments` 在箭头函数中不存在，它会向上找外层普通函数的 `arguments`——这也是箭头函数不能完全替代普通函数的原因之一。

### 36. 什么是纯函数？副作用在什么情况下是不可避免的？｜中级

纯函数满足两条：相同输入必得相同输出（引用透明）；执行过程不产生可观察副作用（不改外部状态、不写 IO、不读随机 / 时间）。

```javascript
// 纯：不修改入参，输出只由入参决定
const addItem = (list, item) => [...list, item];

// 不纯：修改了外部数组
function pushItem(list, item) { list.push(item); return list; }
```

副作用不可避免的场景：网络请求、写 localStorage、打点上报、读写 DOM、`Date.now()` / `Math.random()`。工程做法不是消灭副作用，而是**把它推到边界**——核心计算保持纯、可测，副作用集中在应用层，便于测试与重放。

> 🔍 追问：`Array.prototype.sort` 是纯函数吗？（不是，它原地修改并返回同一数组，典型“看起来像纯的”陷阱。）

### 37. 递归一定会栈溢出吗？尾调用优化在 V8 里能用吗？｜高级

会——每次递归调用都压一个栈帧，深度超过引擎上限（V8 约 1 万多层，取决于帧大小）就抛 `RangeError: Maximum call stack size exceeded`。

```javascript
// 朴素递归：深度 = n，n 大就爆
const sum = n => (n <= 1 ? 1 : n + sum(n - 1));

// 手动转迭代：把中间状态放堆上，深度恒为 1
function sumIter(n) {
  let acc = 0;
  while (n > 0) { acc += n; n--; }
  return acc;
}

// 或显式用栈模拟递归（适合树遍历这类天然递归结构）
```

关于尾调用优化：ES2015 规范里有 PTC（Proper Tail Calls），但 V8 与 Safari、SpiderMonkey 出于调试体验与安全考虑**都没有实现**，只在严格模式下讨论过。所以现实中别指望 `return f(...)` 自动变成循环，要么改写迭代，要么上蹦床（trampoline）模式。

### 38. 实现 compose 和 pipe，并说明它们解决了什么问题？｜中级

```javascript
const compose = (...fns) => x => fns.reduceRight((acc, fn) => fn(acc), x);
const pipe = (...fns) => x => fns.reduce((acc, fn) => fn(acc), x);

const normalize = s => s.trim().toLowerCase();
const wrap = s => `[${s}]`;
pipe(normalize, wrap)('  JS  ');   // '[js]'
compose(wrap, normalize)('  JS  '); // '[js]' —— 数据流方向可读性更好
```

价值在于把“嵌套调用”变成“声明式的数据管道”，中间步骤可单独测试、可增删。工程上要注意两点：管道里混入异步函数会失效（需要 `asyncPipe` 并串行 `await`）；每一步都可能抛错，生产代码要配 `try/catch` 或 `Result` 风格包装，而不是让整条管道一起炸。

### 39. 什么样的写法会让引擎无法优化函数？｜高级

V8 依据调用点的类型反馈做优化，形状稳定才有单态内联缓存：

| 反模式 | 后果 |
|--------|------|
| 同一函数被传 `number` 又传 `string` 又传对象 | 调用点变多态 / 超态，退优化 |
| 函数体频繁变化（`eval`、运行时改原型） | 无法编译成优化代码 |
| 局部变量用过 `delete`、大对象混用 `arguments` | 转为字典模式，属性访问走哈希 |
| `try/catch` 包裹热路径 | 现代引擎已改善，但异常仍昂贵，不要把异常当控制流 |

```javascript
function hot(x) { return x.value; }     // 只传同形状对象才保持单态
hot({ value: 1 });
hot({ value: 2, extra: 'x' });          // 形状变了 → 多态，性能下滑
```

> ⚠️ 注意：这些都是**微观优化**，只有在 Profiler 明确指向该函数时才值得动手；先测再优化，别对着规范猜。

## 五、异步编程与 Promise（12 题）

### 40. 请解释 Promise 的工作原理，它解决了回调的什么问题？｜中级

Promise 是一个状态机：`pending` → `fulfilled` 或 `rejected`，状态一旦落定不可逆；回调通过微任务调度，保证顺序可预期。

```javascript
const p = new Promise((resolve, reject) => {
  // executor 同步执行，这是“Promise 不会捕获同步 throw 之外错误”的根源
  setTimeout(() => resolve('ok'), 100);
});
p.then(v => console.log(v))        // 'ok'
 .catch(e => console.error(e))
 .finally(() => console.log('done'));  // 不接收值、不改变状态
```

它解决三件事：回调嵌套造成的控制反转与错误无法冒泡（用 `.catch` 统一收敛）、无法表达“等待多个任务”（`all` 系列）、状态不可信（第三方库可能多次调用回调，Promise 只认第一次落定）。

> ⚠️ 注意：`new Promise` 的 executor 是**同步**执行的，很多人以为它异步——同步抛错会被自动转成 rejected，这是唯一被 Promise 捕获的同步错误。

### 41. `.then` 的返回值规则是怎样的？链式调用为什么能一直往下传？｜中级

三条规则：返回普通值 → 下一个 `then` 收到该值；返回 Promise / thenable → 等它落定后取值；抛错或返回 rejected → 跳到最近的 `catch`。

```javascript
Promise.resolve(1)
  .then(v => v + 1)                   // 2
  .then(v => Promise.resolve(v * 10)) // 展开，等内部 Promise 落定 → 20
  .then(v => { throw new Error('x'); })
  .then(v => console.log('不会执行'))
  .catch(e => console.log(e.message)) // 'x'
  .then(() => console.log('catch 之后链会恢复')); // 依然会执行
```

`.catch(fn)` 等价于 `.then(undefined, fn)`，只捕获它**上游**的错误；`.finally` 的回调不接收值，但如果它抛出异常或返回 rejected，会覆盖原结果。

### 42. Promise.all、allSettled、race、any 有什么区别？怎么选？｜中级

| 方法 | 落定条件 | 返回值 | 典型场景 |
|------|----------|--------|----------|
| `all` | 全部成功 / 任意一个失败（fail-fast） | 结果数组，顺序按传入顺序 | 并行拉取无依赖数据 |
| `allSettled` | 等全部结束，永不 reject | `{status, value/reason}` 数组 | 批量任务，要逐个报错 |
| `race` | 第一个落定（成功失败都算） | 该结果 | 超时控制、抢最快的镜像 |
| `any` | 第一个成功；全失败才 reject | 成功值 | 多线路探测，容错优先 |

```javascript
// 超时保护的经典写法：race 让超时 Promise 先落定
const timeout = (ms) => new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms));
const result = await Promise.race([fetchData(), timeout(3000)]);
```

> 🎯 关键要点：`all` 里任一失败不影响其余任务的**执行**，只是结果被丢弃；需要拿成功结果就用 `allSettled` 过滤。

### 43. async/await 相比 Promise 链，除了写法更同步化，还有什么实质差异？｜中级

```javascript
async function run() {
  const a = await step1();     // 每个 await 是一次微任务让出
  const b = await step2(a);
  return a + b;                // async 函数返回的总是 Promise
}
```

实质差异有三点：

1. **错误传播方式**：`await` 把 rejection 变成同步 throw，所以 `try/catch` 能捕获异步错误——但只包住 `await` 的表达式，不包住“忘了 await 的 Promise”。
2. **调试体验**：async 函数的调用栈穿过 `await` 后是连续的（引擎做了异步栈追踪），不再是断裂的 `.then` 链。
3. **错误吞没**：`async` 函数即便内部抛错，对外也只是一个 rejected Promise，没人 `.catch` 就是 unhandled rejection，静默丢错。

```javascript
// 最常见的 bug：并发请求忘了 await
try { doAsyncThing(); } catch (e) { /* 永远不会进来 */ }
```

### 44. 循环里 `await` 会有什么问题？怎么改造成并发？｜高级

`for...of` 里的 `await` 是**串行**的，N 个请求耗时是 N 倍；`forEach` 里的 `async` 回调更糟——外层不会等它，错误也逃逸。

```javascript
// 串行：3 次请求依次等
for (const id of ids) results.push(await fetchOne(id));

// 并发但要保序：map 出 Promise 数组，再统一 await
const results2 = await Promise.all(ids.map(fetchOne));

// 并发但不限流 → 打爆下游？用并发池控并发数
async function pool(tasks, limit = 3) {
  const ret = [];
  const running = new Set();
  for (const task of tasks) {
    const p = task().finally(() => running.delete(p));
    running.add(p);
    ret.push(p);
    if (running.size >= limit) await Promise.race(running);
  }
  return Promise.all(ret);
}

// 需要边流式处理边保证顺序 → for await...of（异步迭代器天然是串行的）
for await (const page of paginatedApi()) { /* ... */ }
```

> 🔍 追问：为什么 `ids.forEach(async id => { await fetchOne(id) })` 之后再写 `console.log` 会立刻打印？

### 45. 手写一个符合 Promise/A+ 规范的 Promise，最关键的几个点是什么？｜高级

核心不在 API 全，而在**异步调度 + 状态单次落定 + thenable 展开**。

```javascript
class MyPromise {
  #state = 'pending'; #value; #cbs = [];
  constructor(executor) {
    const settle = (state, v) => {
      if (this.#state !== 'pending') return;        // 只认第一次落定
      queueMicrotask(() => {                        // 回调必须异步执行
        this.#state = state; this.#value = v;
        this.#cbs.forEach(cb => cb());
      });
    };
    try {
      executor(v => settle('fulfilled', v), e => settle('rejected', e));
    } catch (e) { settle('rejected', e); }
  }
  then(onOk, onErr) {
    return new MyPromise((resolve, reject) => {
      const run = () => {
        queueMicrotask(() => {
          const handler = this.#state === 'fulfilled' ? onOk : onErr;
          if (typeof handler !== 'function') return this.#state === 'fulfilled'
            ? resolve(this.#value) : reject(this.#value);   // 透传
          try { resolve(handler(this.#value)); }            // 展开 thenable
          catch (e) { reject(e); }
        });
      };
      this.#state === 'pending' ? this.#cbs.push(run) : run();
    });
  }
}
```

五个必答细节：回调必须异步（规范要求，用微任务）；`then` 必须返回新 Promise 以支持链式；非函数 handler 要透传值 / 原因；handler 抛错要 reject；handler 返回 thenable 要递归展开。规范没有规定用哪种微任务（`queueMicrotask` / `process.nextTick` 都行），但同一实现必须一致。

### 46. `.then` 的回调究竟什么时候执行？和 `setTimeout` 的先后关系是什么？｜高级

`.then` 回调进**微任务**队列，`setTimeout` 进**宏任务**队列；每轮宏任务结束后会清空整个微任务队列，因此同样“0 延迟”，Promise 永远先于定时器。

```javascript
setTimeout(() => console.log('A'));
Promise.resolve().then(() => console.log('B'));
queueMicrotask(() => console.log('C'));
console.log('D');
// D → B → C → A
```

微任务里再产生微任务，会在**本轮**继续执行完（可能饿死渲染），这是“微任务递归导致页面卡死”的机理。`await` 之后的代码等价于 `.then` 回调，同样排微任务。

> ⚠️ 注意：`process.nextTick` 在 Node 里比 Promise 微任务还要早，清空 `nextTick` 队列优先级最高——浏览器没有这个层级。

### 47. 怎么取消一个已经在飞的异步任务？｜高级

Promise 本身不可取消，只能“放弃结果”。标准做法是 `AbortController` 把信号传给支持它的 API：

```javascript
const ctrl = new AbortController();
fetch('/api/slow', { signal: ctrl.signal }).catch(e => {
  if (e.name === 'AbortError') console.log('已取消');
});
ctrl.abort();   // 触发 fetch 中止，并 reject 一个 AbortError
```

对不支持 signal 的自研任务，用竞态标记 / 令牌：

```javascript
let token = 0;
async function search(q) {
  const my = ++token;
  const data = await api(q);
  if (my !== token) return;      // 结果过期，直接丢弃
  render(data);
}
```

选型：能传 `signal` 就传（真正 abort 掉网络请求，省流量）；不能传就用令牌丢弃结果（至少避免脏渲染）。组件卸载场景建议两者都做——先 `abort()` 再置 `token`。

### 48. 搜索框的竞态条件是怎么产生的？除了防抖还能怎么治？｜高级

用户输入 a → b → a，若 a 的响应最后到达，界面会被旧结果覆盖。防抖只降低请求频率，**不能**根治乱序。

```javascript
// 方案一：令牌 + 只采纳最新
let seq = 0;
async function query(kw) {
  const my = ++seq;
  const res = await api(kw);
  if (my !== seq) return;
  setList(res);
}

// 方案二：AbortController，发新请求前先中止旧的
let ctrl;
async function query2(kw) {
  ctrl?.abort();
  ctrl = new AbortController();
  try { setList(await api(kw, { signal: ctrl.signal })); }
  catch (e) { if (e.name !== 'AbortError') throw e; }
}

// 方案三：按 key 缓存结果，命中直接渲染
```

> 💡 提示：面试官很爱在这里追加“如果这个请求还带分页 / 无限滚动呢”——答案是多一个“页码 + 请求代次”的复合键，判断是否仍属于当前会话。

### 49. 异步迭代器解决什么场景？和一次性 `Promise.all` 有什么区别？｜高级

异步迭代器逐项拉取、逐项处理，内存占用恒定；`Promise.all` 是“全量并发 + 全量驻留”。数据量大、来源分页、或需要边到边处理时，异步迭代器明显更合适。

```javascript
async function* paginate(url) {
  let next = url;
  while (next) {
    const res = await fetch(next).then(r => r.json());
    yield res.items;              // 一页一页交出去
    next = res.nextUrl;
  }
}

for await (const page of paginate('/api/list')) {
  await store(page);              // 处理完一页再拉下一页，背压自然形成
}
```

流式响应（SSE / fetch Reader）同样适合包装成异步迭代器。要注意串行带来的时间成本，需要吞吐时用“生产者并发预取 + 消费端顺序处理”的双层结构。

### 50. 从回调到 Promise 再到 async/await，各自解决了什么遗留问题？｜初级

| 阶段 | 写法 | 遗留问题 |
|------|------|----------|
| 回调 | 嵌套回调 + err-first 约定 | 回调地狱、错误无法冒泡、无法表达并发 |
| Promise | 链式 `.then` | 错误要一路 `.catch`、中间变量传参靠闭包、调试栈断裂 |
| async/await | 同步写法 | 忘 `await` 静默失败；`await` 滥用导致串行化；循环里 await 拖慢 |

回调地狱的真实代价不是“难看”，而是：错误处理分支与业务逻辑交织、无法用 `try/catch`、无法组合、无法取消。Promise 统一了错误通道，async/await 补上了控制流可读性——三者不是替代关系，`await` 底层仍是 Promise。

### 51. 怎么实现请求超时与自动重试？指数退避为什么要加抖动？｜中级

```javascript
async function fetchWithRetry(url, { retries = 3, base = 300, timeout = 3000 } = {}) {
  for (let i = 0; i <= retries; i++) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeout);
    try {
      const res = await fetch(url, { signal: ctrl.signal });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      if (i === retries) throw e;
      const backoff = base * 2 ** i;
      const jitter = Math.random() * backoff * 0.5;   // 抖动：打散重试潮
      await new Promise(r => setTimeout(r, backoff + jitter));
    } finally {
      clearTimeout(timer);                            // 别忘了清，否则句柄泄漏
    }
  }
}
```

要点：只对**幂等**请求重试（GET / 带幂等键的写）；只重试可恢复错误（网络失败、429、5xx），4xx 重试无意义；退避加随机抖动，否则大量客户端会同时重试造成“惊群”，把刚恢复的服务再打垮一次；服务端若有 `Retry-After` 头，用它优先。

## 六、事件循环与运行时（8 题）

### 52. 请详细解释事件循环（Event Loop）机制｜高级

JS 主线程只有一个调用栈，异步任务交给宿主环境（浏览器 / Node）处理，完成后把回调排进任务队列，事件循环负责“栈空 → 取任务 → 执行”。

一轮循环的顺序：

1. 执行完当前宏任务中的同步代码；
2. 清空**微任务**队列（Promise.then、`queueMicrotask`、MutationObserver），期间新产生的微任务也在本轮清掉；
3. 需要时渲染（样式计算 → 布局 → 绘制），`requestAnimationFrame` 回调在渲染前执行；
4. 取**下一个宏任务**（`setTimeout`、事件回调、I/O、`MessageChannel`），回到第 1 步。

```javascript
console.log(1);
setTimeout(() => console.log(2));            // 宏任务
Promise.resolve().then(() => console.log(3)); // 微任务
queueMicrotask(() => console.log(4));         // 微任务
(async () => { await null; console.log(5); })(); // await 之后也是微任务
console.log(6);
// 输出：1 6 3 4 5 2
```

关键结论：微任务永远在一个宏任务之后、下一个宏任务之前全部执行完；渲染不是每轮都发生，浏览器按帧率与是否有变更决定。

### 53. 微任务和宏任务各有哪些？为什么微任务优先级更高？｜中级

| 队列 | 来源 | 特点 |
|------|------|------|
| 微任务 | `Promise.then/catch/finally`、`queueMicrotask`、`MutationObserver`、Node 的 `process.nextTick` | 每轮宏任务后**全部清空**，可能无限递归 |
| 宏任务 | `setTimeout/setInterval`、UI 事件、I/O、`MessageChannel`、`setImmediate`(Node) | 每轮只取**一个**执行 |

```javascript
// 经典混合题
setTimeout(() => { console.log('t1'); Promise.resolve().then(() => console.log('t1-micro')); });
Promise.resolve().then(() => console.log('main-micro'));
// main-micro → t1 → t1-micro
```

微任务优先是为了“尽快收敛状态”：Promise 是语言层的状态同步机制，如果排到宏任务之后，中间会被别的定时器插队，导致状态一致性变复杂；DOM 变更也依赖在同一轮内完成以避免中间态渲染。

> 🎯 关键要点：微任务队列递归添加会让页面无法渲染（饿死渲染），这是“微任务里再 await 长链会卡顿”的原因。

### 54. 浏览器和 Node 的事件循环有什么不同？｜高级

Node 的事件循环由 libuv 驱动，分六个阶段：`timers`（setTimeout/setInterval）→ `pending callbacks` → `idle/prepare` → `poll`（I/O）→ `check`（`setImmediate`）→ `close callbacks`；每个阶段之间会清空 `process.nextTick` 队列（优先级高于 Promise）与微任务队列。

```javascript
// Node 里的顺序差异（在 I/O 回调内 setImmediate 通常早于 setTimeout(0)）
const fs = require('fs');
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timeout'), 0);
  setImmediate(() => console.log('immediate'));   // 先于 timeout
});
```

| 维度 | 浏览器 | Node |
|------|--------|------|
| 渲染时机 | rAF + 渲染帧参与事件循环 | 无渲染概念 |
| 特有微任务 | `queueMicrotask`、MutationObserver | `process.nextTick`（比微任务还早） |
| 特有宏任务 | `MessageChannel`、UI 事件 | `setImmediate`、I/O 阶段 |
| 补充 API | `requestIdleCallback` | `setImmediate` + `worker_threads` |

### 55. `requestAnimationFrame` 和 `setTimeout` 做动画有什么区别？掉帧怎么定位？｜高级

`rAF` 由浏览器在**下一次重绘前**调用，天然与刷新率对齐（60Hz ≈ 16.7ms，120Hz ≈ 8.3ms），后台标签页会自动暂停；`setTimeout` 走宏任务队列，会被其他任务挤后，且最小间隔 4ms 累积漂移，必然抖动。

```javascript
let last = 0;
function step(ts) {
  const dt = ts - last; last = ts;      // 用真实时间差算位移，而不是固定步长
  box.style.transform = `translateX(${x += speed * dt}px)`;
  if (x < 500) requestAnimationFrame(step);
}
requestAnimationFrame(step);
```

掉帧定位流程：Performance 面板录一段 → 看 Frames 行是否有红条 → 对照 Main 线程的长任务（>50ms）找出罪魁 → 常见原因是大规模 DOM 批量操作、同步布局抖动（读 `offsetHeight` 后写样式反复交替）、未节流的事件回调、超大计算。修法是批量化读写（先读完再写）、用 transform/opacity 走合成层、把重计算搬进 Worker。

### 56. `setTimeout(fn, 0)` 真的是 0 毫秒吗？｜中级

不是。规范规定嵌套调用 5 层以上最小延迟为 4ms，且“0”只是“尽快排入宏任务队列”，前面所有同步代码、微任务、同队列中更早的任务都要先跑完。

```javascript
setTimeout(() => console.log('t'), 0);
const start = Date.now();
while (Date.now() - start < 100) {}    // 阻塞 100ms
// 't' 在 100ms 之后才打印 —— 队列里的任务无法抢占主线程
```

想“本轮结束就执行、且不计入宏任务延时”用 `queueMicrotask`；想“下一帧前执行”用 `rAF`；想“调度到空闲时”用 `requestIdleCallback`（可能饿了，记得传 `timeout`）。

> ⚠️ 注意：`setTimeout` 返回的是句柄，浏览器是数字、Node 是对象，两者不可混用判等——这是跨环境代码的常见 bug。

### 57. Web Worker 能解决什么、不能解决什么？｜高级

Worker 提供独立线程，适合纯计算密集任务：大数组处理、图像 / 视频解码、加密、复杂 diff、大数据解析。它**不能**直接访问 DOM、`window`、`localStorage`，与主线程只能通过 `postMessage` 或 `SharedArrayBuffer` 通信。

```javascript
// main.js
const worker = new Worker('./heavy.js', { type: 'module' });
worker.postMessage({ list: bigArray }, [transferable]);  // 第二参数转移所有权，零拷贝
worker.onmessage = (e) => console.log(e.data);

// heavy.js
self.onmessage = ({ data }) => {
  self.postMessage(compute(data));   // 结构化克隆，注意大对象的序列化成本
};
```

取舍：Worker 启动有成本（几十毫秒），任务太小反而更慢；数据来回要序列化（结构化克隆），用 `Transferable`（`ArrayBuffer`、`ImageBitmap`）可避免拷贝。前端框架生态（如 Vite）对 Worker 的打包支持要看构建配置。

### 58. 单个长任务卡住页面怎么办？怎么切分？｜高级

长任务（>50ms）会阻塞渲染与交互。切分原则是“把一段同步循环变成多段可控调度”，每段执行后让出主线程。

```javascript
// 1. 手动分片：每 50ms 左右让出一次
async function chunked(items, work, budget = 12) {
  let i = 0;
  while (i < items.length) {
    const end = Math.min(i + budget, items.length);
    while (i < end) work(items[i++]);
    await new Promise(r => setTimeout(r, 0));   // 让出，允许渲染与输入响应
  }
}

// 2. 用 rAF 做动画友好的切片（每帧一片）
// 3. 更现代：await scheduler.yield?.()（Chromium 支持，续接优先级更高）
// 4. 计算量实在大 → 交给 Worker，主线程只做渲染
```

React 的时间切片（Fiber 的中断 - 恢复）解决的是同一类问题，思路是“可中断的增量工作 + 优先级抢占”。回答时把“让出时机”说清楚：`setTimeout` 让出代价高（≥4ms），`MessageChannel` 与 `scheduler.yield` 让出更快。

### 59. 为什么一个死循环能让整个页面失去响应？怎么诊断？｜中级

主线程既执行 JS，也负责样式计算、布局、绘制与事件派发。死循环让调用栈永不释放，事件循环拿不到控制权：渲染不执行、事件回调排不进去、定时器不触发——不是“慢”，是彻底停摆。

```javascript
while (true) {}                       // 页面彻底冻结，连关闭标签都卡
function loopWithYield(n) {           // 至少让它有喘息：递归 + 定时器让出
  if (n <= 0) return;
  setTimeout(() => loopWithYield(n - 1), 0);
}
```

诊断手段：开 DevTools 时可以用 `Sources` 面板的 Pause 抓当前调用栈；无 DevTools 时看 Profiler 里的长任务火焰图；线上靠长任务监控（PerformanceObserver 监听 `longtask`）报警。预防靠代码评审 + lint 规则（禁止 `while` 无变更条件）+ 对不可信输入做上限保护。

## 七、对象与数组（9 题）

### 60. 深拷贝和浅拷贝有什么区别？分别怎么实现？｜中级

浅拷贝只复制第一层，嵌套对象仍是共享引用；深拷贝递归复制所有层级，完全独立。

```javascript
const original = { a: 1, b: { c: 2 } };

const shallow = { ...original };            // 或 Object.assign({}, original)
shallow.b.c = 3;
console.log(original.b.c);                  // 3 —— 被连带改了

const deep = structuredClone(original);     // 现代首选
deep.b.c = 4;
console.log(original.b.c);                  // 3 —— 未受影响
```

| 手段 | 支持 | 不支持 |
|------|------|--------|
| 展开 / `Object.assign` / `slice` | 一层拷贝 | 嵌套对象 |
| `JSON.parse(JSON.stringify())` | 纯数据 | `undefined`、函数、`Symbol`、`Date` 变字符串、`Map/Set` 变空对象、循环引用抛错 |
| `structuredClone` | 循环引用、`Date`、`Map/Set`、`ArrayBuffer`、`File` | 函数、`Symbol`、DOM 节点、原型链与类方法 |
| 递归 + 类型判断 | 几乎全部（需自己处理） | 要手写循环引用检测（`WeakMap` 记录已拷贝） |

手写版的关键是**循环引用**与**特殊类型**分支：

```javascript
function deepClone(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value;
  if (seen.has(value)) return seen.get(value);          // 环形结构
  if (value instanceof Date) return new Date(value);
  if (value instanceof RegExp) return new RegExp(value.source, value.flags);
  if (value instanceof Map) return new Map([...value].map(([k, v]) => [deepClone(k, seen), deepClone(v, seen)]));
  if (value instanceof Set) return new Set([...value].map(v => deepClone(v, seen)));
  const out = Array.isArray(value) ? [] : Object.create(Object.getPrototypeOf(value));
  seen.set(value, out);
  return Reflect.ownKeys(value).reduce((acc, k) => {
    acc[k] = deepClone(value[k], seen);
    return acc;
  }, out);
}
```

### 61. `structuredClone` 和 JSON 方案怎么选？有哪些现代拷贝的坑？｜中级

能用 `structuredClone` 就别用 JSON 往返：它是浏览器 / Node 内置的结构化克隆算法，保留类型信息、支持循环引用、还支持 `Transferable` 转移（零拷贝）。

```javascript
const src = { d: new Date(), m: new Map([['k', 1]]), s: new Set([1]) };
src.self = src;                                   // 循环引用

JSON.parse(JSON.stringify(src));                  // TypeError: Converting circular structure
const copy = structuredClone(src);
copy.d instanceof Date;                           // true
copy.m instanceof Map;                            // true
copy.self === copy;                               // true
```

三个已知边界：类实例会被“降级”为普通对象（原型丢失），方法是函数也拷不过去；`structuredClone` 不能克隆 DOM 节点；代理对象不能克隆。另外它不是万能的深拷贝替代——带 getter / 原型行为的对象需要手写方案。

> 💡 提示：Node 17+ 才有全局 `structuredClone`；`MessageChannel` 与 Worker 的 `postMessage` 用的也是同一套算法，这也是它成为事实标准的底气。

### 62. 哪些数组方法会修改原数组？｜初级

```javascript
const arr = [3, 1, 2];
arr.sort();        // 原地排序并返回同一引用（易被误当新数组）
arr.reverse();     // 原地反转
arr.push(4); arr.pop(); arr.shift(); arr.unshift(5);
arr.splice(0, 1);  // 原地增删
arr.fill(0); arr.copyWithin(0, 1);
```

| 类别 | 方法 |
|------|------|
| 变异（原地） | `push` `pop` `shift` `unshift` `splice` `sort` `reverse` `fill` `copyWithin` |
| 非变异（返回新数组） | `map` `filter` `slice` `concat` `flat` `flatMap` `toSorted`(ES2023) `toReversed` `with` |
| 遍历 / 归约 | `forEach` `some` `every` `find` `findIndex` `reduce` `reduceRight` |

ES2023 新增的 `toSorted` / `toReversed` / `toSpliced` / `with` 是为**不可变**编程准备的：React / Redux 场景下用它替代变异方法能直接消除引用相等性判断的坑。

### 63. `sort` 有哪些坑？比较函数怎么写才对？｜中级

默认比较函数把元素转成**字符串**再按 UTF-16 码元排序，所以数字数组会排成字典序：

```javascript
[10, 9, 1].sort();                       // [1, 10, 9] —— 字符串比较
[10, 9, 1].sort((a, b) => a - b);        // [1, 9, 10]

// 对象数组：写错比较函数的返回（忘记返回负数/正数）会导致原地乱序
list.sort((a, b) => a.age > b.age);      // 返回 true/false，等价于 1/0，永远不返回负数 → 排序错乱
list.sort((a, b) => a.age - b.age);      // 正确
```

要点：比较函数必须返回负数 / 0 / 正数；`sort` 自 ES2019 起保证**稳定**，依赖稳定排序的多字段排序可写成“先按次关键字排、再按主关键字排”；`NaN` 参与比较时结果不确定，要先清洗。

> ⚠️ 注意：`sort` 会就地修改原数组。要保留原数组请 `[...arr].sort(...)` 或用 `arr.toSorted(...)`。

### 64. 稀疏数组、类数组、可迭代对象分别是什么？怎么互转？｜中级

```javascript
const sparse = [1, , 3];          // 中间是空槽，不是 undefined
sparse.length;                    // 3
sparse.filter(() => true).length; // 2 —— 空槽被跳过
0 in sparse;                      // false

const arrayLike = { 0: 'a', 1: 'b', length: 2 };    // 有 length、有下标（arguments、NodeList）
Array.from(arrayLike);            // ['a', 'b'] —— 类数组转真数组
[...'abc'];                       // ['a', 'b', 'c'] —— 字符串是可迭代的
Array.from({ length: 3 }, (_, i) => i * 2);          // [0, 2, 4] —— 带映射函数
```

| 类型 | 判定依据 | 转换方式 |
|------|----------|----------|
| 类数组 | 有 `length` 与数字下标 | `Array.from` / `Array.prototype.slice.call` |
| 可迭代 | 有 `Symbol.iterator` | `[...x]` / `Array.from` |
| 两者兼有 | `NodeList`、`arguments` | 任选，`Array.from` 更直白 |

`Array.from` 同时接受两类，`Array.of` 则解决 `new Array(3)` 造出长度 3 的空槽数组而不是 `[3]` 的坑。

### 65. 属性描述符、getter/setter、`Object.freeze` 的边界在哪里？｜高级

```javascript
const obj = {};
Object.defineProperty(obj, 'x', {
  value: 1, writable: false, enumerable: false, configurable: false,
});

console.log(Object.getOwnPropertyDescriptor(obj, 'x'));
// { value: 1, writable: false, enumerable: false, configurable: false }

const withA = { _v: 1, get v() { return this._v; }, set v(n) { this._v = n * 2; } };
withA.v = 3;                 // setter 触发
withA.v;                     // 6
```

`Object.freeze` 是**浅冻结**：对象的顶层属性不可改、不可增删，但嵌套对象照改不误；`Object.seal` 只禁止增删，允许改值。

```javascript
const cfg = Object.freeze({ nested: { a: 1 } });
cfg.nested.a = 2;            // 依然成功 —— 冻结是浅的
Object.freeze(cfg.nested);   // 需要手动递归冻结
```

另有个高频陷阱：冻结后的对象在非严格模式下**静默失败**，严格模式下才抛 `TypeError`。

### 66. Map/Set 和普通对象/数组相比，什么时候该换？｜中级

```javascript
const m = new Map([['a', 1]]);
m.set('b', 2); m.get('a'); m.size;      // 键可以是任意类型、有 size、按插入序迭代
m.set(NaN, 'x'); m.get(NaN);            // 'x' —— SameValueZero，NaNaN 能命中
```

| 维度 | Object | Map |
|------|--------|-----|
| 键类型 | 字符串 / Symbol | 任意值（含对象、NaN） |
| 顺序 | 整数键优先 + 插入序 | 严格插入序 |
| 大小 | `Object.keys().length`（O(n)） | `.size`（O(1)） |
| 频繁增删 | 可能退化字典模式 | 专为增删设计 |
| 性能 | 小数据更快（形状优化） | 大量键值、频繁增删更快 |
| 序列化 | 直接 JSON 化 | 需要手动转数组 |

`Set` 的杀手锏是去重与 O(1) 存在性判断：`[...new Set(arr)]` 去重（注意 `NaN` 和引用类型按同值语义判定）；需要“映射到对象但不阻止其回收”用 `WeakMap`。

### 67. 迭代协议是什么？怎么让自定义对象支持 `for...of` 和展开？｜高级

两个角色：**可迭代对象**必须实现 `[Symbol.iterator]()`，返回**迭代器**；迭代器必须有 `next()`，返回 `{ value, done }`。

```javascript
class Range {
  constructor(start, end) { this.start = start; this.end = end; }
  [Symbol.iterator]() {
    let cur = this.start;
    const end = this.end;
    return {
      next: () => (cur <= end ? { value: cur++, done: false } : { value: undefined, done: true }),
      [Symbol.iterator]() { return this; },   // 让迭代器本身也可迭代
    };
  }
}

[...new Range(1, 3)];    // [1, 2, 3]
for (const n of new Range(1, 3)) {}
```

更简洁的写法是用生成器：`*[Symbol.iterator]() { for (let i = this.start; i <= this.end; i++) yield i; }`。实现了迭代协议，`for...of`、展开、解构、`Array.from`、`Map` 初始化全部自动生效——这就是“面向协议编程”的收益。

### 68. 扁平化、去重、分组、排序这些高频数组操作怎么写？｜初级

```javascript
// 扁平化
[1, [2, [3, [4]]]].flat(Infinity);                 // [1,2,3,4]
[[1, 2], [3]].flatMap(x => x);                     // [1,2,3]（flat + map 一步）

// 去重（对象数组按 id 去重）
[...new Map(list.map(o => [o.id, o])).values()];

// 分组：ES2024 的 Object.groupBy / Map.groupBy
Object.groupBy(list, o => o.type);                 // { a: [...], b: [...] }

// 按多字段排序
list.sort((a, b) => a.type.localeCompare(b.type) || a.id - b.id);

// 聚合：reduce 一次算多个指标（避免多次遍历）
const { sum, max } = list.reduce((acc, n) => ({
  sum: acc.sum + n,
  max: Math.max(acc.max, n),
}), { sum: 0, max: -Infinity });
```

`flat` 默认深度是 1，深扁平必须显式传参或 `Infinity`（后者在大数组上有栈风险）；`reduce` 适合“一次遍历出多个结果”，但可读性差时该拆成 `map` + `filter`。

## 八、ES6+ 与现代语法（10 题）

### 69. 解构赋值的规则和常见坑有哪些？｜初级

```javascript
const { a: alias = 1, b: { c } = {} } = obj;   // 别名 + 默认值 + 嵌套（默认值防 undefined 崩溃）
const [x, , y, ...rest] = [1, 2, 3, 4];        // 跳过、剩余
const { length } = 'ab';                       // 字符串可解构
function f({ a = 1 } = {}) {}                  // 参数解构三连：默认对象 + 默认值
```

坑点清单：

| 坑 | 说明 |
|----|------|
| `undefined` 触发默认值，`null` 不触发 | `const { a = 1 } = { a: null }` → `null` |
| 嵌套解构无默认值会抛错 | `const { b: { c } } = {}` → TypeError，写成 `{ b: {} = {} }` |
| 声明语句必须初始化 | `let { a };` 语法报错；`({ a } = obj)` 要加括号避免被当块 |
| 函数参数解构不能跳过位置 | 需要选项对象约定，别做成 `f(a, undefined, c)` |

### 70. 展开运算符和剩余参数是同一种东西吗？｜初级

语法形态相同，语义相反：展开（spread）把可迭代对象 / 对象“摊开”，剩余（rest）把零散参数“收拢”。

```javascript
const nums = [2, 3];
Math.max(...nums);                       // 展开
function sum(...args) { return args.reduce((a, b) => a + b, 0); }   // 剩余

const a = { x: 1 }, b = { x: 2, y: 3 };
{ ...a, ...b };                          // { x: 2, y: 3 } —— 后面的同名属性覆盖前面
[...'ab'];                               // ['a','b']  字符串可展开
{ ...[1, 2] };                           // { 0: 1, 1: 2 } 数组展开成对象会带下标键
```

两者都是**浅拷贝**，且对象展开只复制自有可枚举属性（原型上的、不可枚举的、getter 会被**求值后固化**）。展开 `null` / `undefined` 在对象里安全（忽略），在数组 / 函数调用里会抛错。

### 71. 可选链和空值合并的短路规则是什么？｜初级

```javascript
obj?.a?.b;            // 左侧为 null/undefined 时整体返回 undefined，不报错
fn?.();               // 函数不存在则返回 undefined
arr?.[0];             // 下标访问
a ?? b;               // 仅当 a 是 null/undefined 时才取 b（0、''、false 都算有效值）
a ??= 1;              // 空值赋值：a 为 null/undefined 才赋
```

对比表：

| 表达式 | `0` | `''` | `false` | `null` |
|--------|-----|------|---------|--------|
| `a \|\| b` | 取 b | 取 b | 取 b | 取 b |
| `a ?? b` | 取 0 | 取 '' | 取 false | 取 b |
| `a?.b` | 正常访问 | 正常访问 | 正常访问 | undefined |

限制：可选链**不能用于赋值左侧**（`a?.b = 1` 是语法错误），也不能与 `??`、`||` 混用不加括号（`a ?? b || c` 报错，避免歧义）。

### 72. 标签模板（Tagged Template）有什么用？｜初级

标签函数接收“字符串片段数组 + 插值列表”，可以在生成最终字符串前做处理，是模板引擎与样式方案的基础设施。

```javascript
function html(strings, ...values) {
  const out = strings.reduce((acc, s, i) => {
    const v = values[i - 1];
    return acc + (i ? escapeHtml(String(v)) : '') + s;
  }, '');
  return out;
}

const name = '<img onerror=alert(1)>';
html`<p>${name}</p>`;   // 自动转义，XSS 被挡住
```

两个易忘细节：`strings.raw` 取未转义原文（`String.raw` 就是用它）；插值只在**求值位置**插入，没法阻止其副作用——所以标签模板不是安全沙箱，只是可控的拼接入口。

### 73. Proxy 能拦截什么？怎么用它实现一个简易响应式？｜高级

`Proxy` 用 handler 拦截 13 种内部操作（`get`/`set`/`has`/`deleteProperty`/`ownKeys`/`apply`/`construct` 等），`Reflect` 提供对应的默认行为，便于“拦截后仍保持原语义”。

```javascript
function reactive(obj, onChange) {
  return new Proxy(obj, {
    get(target, key, receiver) {
      const v = Reflect.get(target, key, receiver);
      return (v !== null && typeof v === 'object') ? reactive(v, onChange) : v;   // 惰性深层代理
    },
    set(target, key, value, receiver) {
      const old = target[key];
      const ok = Reflect.set(target, key, value, receiver);
      if (ok && old !== value) onChange(key, value, old);
      return ok;
    },
  });
}
```

必答的边界：`get` 里的 `receiver` 决定了原型链上的 getter 用谁当 `this`；代理数组时 `push` 会触发多次 `get/set`（长度 + 下标），要用 `length` 变化去重；`ownKeys` 的返回值必须与目标对象一致，否则抛 `TypeError`。

### 74. Vue2 用 `Object.defineProperty`，Vue3 换成 Proxy，为什么？｜高级

| 维度 | `Object.defineProperty` | `Proxy` |
|------|-------------------------|---------|
| 拦截范围 | 只能拦截已存在的**属性读写** | 整体对象，含增删、`in`、遍历 |
| 新增 / 删除属性 | 检测不到，需要 `$set` / `$delete` | 天然可拦截 |
| 数组 | 需重写 7 个变异方法（`push` 等） | 直接可用 |
| 索引与 `length` | 无法拦截 | 可拦截 |
| 递归深度 | 初始化时必须递归遍历全部属性 | 支持惰性代理，按需深入 |
| 兼容性 | 支持到 IE9 | 不支持 IE（无 polyfill） |

```javascript
// defineProperty 的典型局限：新增属性不触发更新
const o = {}; let v;
Object.defineProperty(o, 'a', { get: () => v, set: n => { v = n; console.log('changed'); } });
o.b = 1;                 // 没有任何输出 —— b 不在劫持范围
```

代价是 Proxy 无法被降级到老浏览器、且每次访问都过一层 handler（Vue3 用惰性代理把代价摊到实际访问上）。

### 75. WeakMap、WeakSet、WeakRef、FinalizationRegistry 各适合什么场景？｜高级

弱引用的统一特征是：**不阻止 GC**，其内容不可枚举（无法遍历，因此没有 size / keys）。

| API | 语义 | 典型用途 |
|-----|------|----------|
| `WeakMap` | 弱键 → 强值 | 给对象挂私有数据 / 缓存，对象死则条目自动消失 |
| `WeakSet` | 弱引用集合 | 标记“已处理过的对象”，避免重复处理 |
| `WeakRef` | 弱引用单个对象 | 大对象缓存，`.deref()` 可能返回 undefined |
| `FinalizationRegistry` | 对象被回收后回调 | 释放外部资源（如关闭句柄），**时机不保证** |

```javascript
const cache = new WeakMap();     // DOM 节点 → 附加数据：节点被移除后条目自动清理
function meta(el) {
  if (!cache.has(el)) cache.set(el, { hits: 0 });
  return cache.get(el);
}
```

> ⚠️ 注意：`FinalizationRegistry` 的回调可能在任意时刻（或永不）执行，绝不能把关键清理逻辑押在它身上；它也不是内存泄漏的解药，它只是让你少写一些手动解绑。

### 76. ESM 与 CommonJS 的循环依赖分别会发生什么？｜高级

CJS 是运行时逐行执行、导出的是**已执行部分的对象**，循环依赖时容易拿到不完整导出：

```javascript
// a.js (CJS)
exports.done = false;
const b = require('./b');       // 此时 b 里拿到的 a.done 还是 false
exports.done = true;

// b.js (CJS)
const a = require('./a');       // a 尚未执行完，拿到 { done: false }
```

ESM 是先建好模块图（链接阶段绑定所有导出），再执行；循环依赖时拿到的是**活绑定**，只要不在初始化阶段就读取，通常能正常工作；若提前读取会命中 TDZ 报错。

```javascript
// a.mjs / b.mjs 循环：函数声明提升 + 活绑定让它可用，但顶层立即读取会炸
import { b } from './b.mjs';
export function a() { return b(); }
```

治理手段一致：抽取共享依赖到第三方模块、用依赖注入打破环、把“只在调用时才需要”的依赖改成动态 `import()`。

### 77. 生成器函数和 async/await 是什么关系？｜高级

生成器是“可暂停 / 恢复的函数”，`yield` 交出值并挂起，`next()` 恢复；async/await 本质是“引擎用状态机实现的自动执行器”，把 `await` 当成 `yield` 自动驱动到底。

```javascript
function* gen() {
  const a = yield 1;          // 外部 next('x') 时 x 成为 a
  const b = yield a + 1;
  return b;
}
const g = gen();
g.next();                     // { value: 1, done: false }
g.next(10);                   // { value: 11, done: false }
g.next(20);                   // { value: 20, done: true }

// 手写 runner 理解本质
function run(genFn) {
  const it = genFn();
  return new Promise((resolve, reject) => {
    const step = (method, arg) => {
      let r;
      try { r = it[method](arg); } catch (e) { return reject(e); }
      if (r.done) return resolve(r.value);
      Promise.resolve(r.value).then(v => step('next', v), e => step('throw', e));
    };
    step('next');
  });
}

// yield* 委托另一个可迭代对象
function* flat(arr) { for (const x of arr) Array.isArray(x) ? yield* flat(x) : yield x; }
```

生成器的另一大用途是**无限惰性序列**（配合 `take`）与自定义迭代协议，这两点 `async/await` 完全不覆盖。

### 78. 顶层 `await` 会带来什么问题？模块执行顺序怎么保证？｜高级

顶层 `await` 让模块变成**异步模块**：它的所有导入者都必须等它执行完才能继续，等于把异步依赖扩散进整张模块图，会拖慢首屏并让副作用顺序变得隐晦。

```javascript
// config.mjs
export const config = await fetch('/config.json').then(r => r.json());
// 任何 import 它的模块都会被这个网络请求阻塞（含所有传递依赖）
```

使用原则：只在应用入口（如 `main.js`）用，且明确它阻塞整图；库代码不要用——把异步初始化封装成显式函数，让调用方决定时机：

```javascript
export async function initConfig() { /* ... */ }
```

另一个陷阱是模块副作用顺序：`import './polyfill'` 会被提升到顶部，若依赖注入顺序（如全局变量）就必须拆成两个模块或改用动态 `import()`。

## 九、DOM 与浏览器环境（8 题）

### 79. 事件流有哪几个阶段？事件委托为什么能生效？｜初级

三个阶段：**捕获**（window → 目标父级）→ **目标**（到达绑定元素）→ **冒泡**（目标 → window）。`addEventListener` 第三个参数 `true` 或 `{ capture: true }` 表示在捕获阶段处理，默认是冒泡阶段。

```javascript
ul.addEventListener('click', (e) => {
  const li = e.target.closest('li');       // 从真实触发点向上找目标
  if (!li || !ul.contains(li)) return;
  console.log('点击了', li.dataset.id);
});
```

委托生效的前提就是冒泡，好处有三：只绑一个监听器、动态新增的子元素自动生效、卸载时只需解绑一次（少掉一类内存泄漏）。不适用的场景：`focus`/`blur` 不冒泡（用 `focusin`/`focusout` 或捕获阶段）、`mousemove` 之类高频事件、目标元素内部有交互阻断（如 `stopPropagation`）。

### 80. 如何优化 DOM 操作性能？｜中级

三类手段：减少次数、缩小范围、避开强制同步布局。

```javascript
// 1. 批量插入：DocumentFragment 或一次性 innerHTML
const frag = document.createDocumentFragment();
list.forEach(item => {
  const li = document.createElement('li');
  li.textContent = item.name;
  frag.appendChild(li);          // 在内存里拼好
});
ul.appendChild(frag);            // 只触发一次插入

// 2. 离线改样式：先 display:none 或 clone 到内存改完再换回
// 3. 批量读写分离，避免布局抖动
boxes.forEach(b => b.style.width = b.offsetWidth + 10 + 'px');  // 读-写-读-写，强制多次重排
const widths = boxes.map(b => b.offsetWidth);                   // 先全读
boxes.forEach((b, i) => b.style.width = widths[i] + 10 + 'px');// 再全写

// 4. 高频回调加节流 / rAF
```

| 手段 | 收益 |
|------|------|
| `DocumentFragment` / 拼字符串一次插入 | 插入次数 O(n) → O(1) |
| 读写分离 | 避免每次读属性都强制同步布局 |
| `className` / `cssText` / `classList` 整体替换 | 避免逐条改样式触发多次样式重算 |
| 虚拟滚动、`content-visibility` | 只渲染视口内节点 |

### 81. 重排（reflow）和重绘（repaint）有什么区别？怎么规避？｜高级

重排是几何属性变化（尺寸、位置、字体大小、增删节点），浏览器必须重算布局，代价最高；重绘是外观变化（颜色、背景、阴影），跳过布局只重画；两者的共同上游是**样式重算**。

触发重排的典型操作：读 `offsetTop` / `offsetWidth` / `getBoundingClientRect()` / `scrollTop`、写宽高与定位、增删 DOM、改字体、窗口 resize。

规避手段分三层：

```javascript
// 1. 合成层属性：transform / opacity 不触发重排，走 GPU 合成
el.style.transform = 'translate3d(10px, 0, 0)';   // 优于改 left / top

// 2. 让元素脱离文档流再操作（position:absolute/fixed 或 display:none）
// 3. will-change 提前提升，但别滥用
.el { will-change: transform; }   /* 每个层都要独立显存，几十个就爆内存 */
```

浏览器会把重排放进动画帧批量执行，所以“紧接着读几何属性”才是真正的性能杀手——它强制浏览器 flush 掉待执行的布局，即“强制同步布局”。

### 82. `preventDefault`、`stopPropagation`、`stopImmediatePropagation` 有什么区别？`passive` 有什么用？｜高级

| API | 作用 | 影响 |
|-----|------|------|
| `preventDefault()` | 阻止默认行为（跳转、提交、滚动） | 不影响事件传播 |
| `stopPropagation()` | 阻止继续传播（捕获 / 冒泡） | 不影响同元素其他监听器 |
| `stopImmediatePropagation()` | 阻止传播 + 同一元素剩余监听器 | 影响面最大，慎用 |
| `return false` | 仅 jQuery 里等价于两者组合 | 原生监听器中完全无效 |

`passive: true` 声明“我不会调用 preventDefault”，让浏览器不必等 JS 执行完就能开始滚动，是移动端滚动手感的关键：

```javascript
// 不写 passive，触摸滚动要等监听器跑完才动，滚动延迟明显
window.addEventListener('touchstart', handler, { passive: true });

// 想滚动时做拦截（如自定义下拉刷新）必须非 passive，代价是可能掉帧
window.addEventListener('touchmove', handler, { passive: false });
```

> ⚠️ 注意：Chrome 从 56 起把 `touchstart` / `touchmove` / `wheel` 在 window/document/body 上的默认值改成了 passive，此时调用 `preventDefault()` 会静默失效（控制台给警告）——自定义滚动必须显式写 `passive: false`。

### 83. cookie、localStorage、sessionStorage、IndexedDB 怎么选？｜中级

| 维度 | cookie | localStorage | sessionStorage | IndexedDB |
|------|--------|--------------|----------------|-----------|
| 容量 | 约 4KB | 约 5MB | 约 5MB | 按磁盘配额（数百 MB+） |
| 生命周期 | 可设过期时间 | 永久，需手动清 | 标签页关闭即清 | 永久 |
| 随请求发送 | **是**（同源自动携带） | 否 | 否 | 否 |
| 同步 / 异步 | 同步 | 同步（阻塞主线程） | 同步 | 异步 |
| 数据结构 | 字符串 | 键值字符串 | 键值字符串 | 索引 + 事务，可存二进制 |

选型结论：登录凭证用 **HttpOnly + Secure cookie**（JS 读不到，防 XSS 窃取）；用户偏好、主题这类小配置用 `localStorage`；表单草稿用 `sessionStorage`；离线数据集、大文件缓存用 `IndexedDB`。

> 💡 提示：`localStorage` 是同步 API，读写大对象会阻塞主线程；存对象必须 `JSON.stringify`，且没有过期机制，需要自己封装带时间戳的包装层。

### 84. 跨域是怎么产生的？CORS 的预检请求什么时候触发？｜高级

同源策略要求协议、域名、端口三者完全一致，否则浏览器禁止 JS 读取响应（请求本身可能已经发出，只是响应被拦）。服务端通过 CORS 响应头授权：

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 600
```

**预检（OPTIONS）触发条件**：请求方法不是 `GET`/`HEAD`/`POST`，或 `Content-Type` 不是 `application/x-www-form-urlencoded`/`multipart/form-data`/`text/plain`，或带了自定义请求头。满足“简单请求”条件时直接发，无预检。

```javascript
// 这一句必然触发预检：Content-Type 为 application/json
fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });

// 带凭证时，服务端不能把 Origin 写成 *，必须回显具体来源
fetch(url, { credentials: 'include' });
```

其它跨域方案：开发环境代理（`server.proxy`，本质是服务端转发，无跨域）、`postMessage` 跨窗口通信、JSONP（只支持 GET，已过时）、Nginx 反向代理同源化（生产最常用）。

### 85. 强缓存和协商缓存怎么配合？为什么发版后用户还在用旧代码？｜高级

| 类型 | 请求头 / 响应头 | 行为 |
|------|-----------------|------|
| 强缓存 | `Cache-Control: max-age=31536000, immutable` | 直接读本地，不发请求 |
| 协商缓存 | `ETag` / `If-None-Match`、`Last-Modified` / `If-Modified-Since` | 发请求，命中返回 304 无响应体 |

正确的发版策略是“**HTML 不缓存 + 静态资源永久缓存 + 文件名带哈希**”：

```http
# index.html：禁止缓存，保证每次拿到最新引用
Cache-Control: no-cache

# app.3f9a2c.js：内容变了文件名就变，可以永久缓存
Cache-Control: public, max-age=31536000, immutable
```

只给 `index.html` 设 `no-cache` 是关键——它引用的资源名带内容哈希，内容一变文件名就变，天然绕过旧缓存。常见的坑：把 `index.html` 也设成长期强缓存（用户永远拿不到新版本）、改了资源却没改哈希（要么强刷，要么手动加版本号参数）、`Service Worker` 的缓存优先级高于 HTTP 缓存（要配 `skipWaiting` + `clients.claim`）。

### 86. 虚拟 DOM 到底解决了什么？它的收益边界在哪里？｜高级

虚拟 DOM 是“用 JS 对象描述 UI 树”，更新时先 diff 新旧树算出最小变更集，再批量落到真实 DOM。它真正的价值是**把声明式写法与最小化 DOM 操作解耦**：开发者只描述“状态该长什么样”，框架负责算差异，并且这一层是跨端的（React Native、SSR、测试渲染器都复用同一层）。

收益边界要说清楚：

| 场景 | 虚拟 DOM 的收益 |
|------|-----------------|
| 高频、大范围的状态驱动更新 | 高（批量 + 最小化） |
| 静态内容、一次性渲染 | 负收益（多一层对象开销与 diff） |
| 极致性能要求的局部动画 / 大表格 | 低（手写 DOM 或 Canvas 更快） |

```javascript
// 手写 DOM 在“一次性创建大量节点”时反而更快
const frag = document.createDocumentFragment();
for (let i = 0; i < 10000; i++) { /* ... */ }
// 虚拟 DOM 要为每个节点分配对象 + diff，内存与时间都更高
```

所以 Svelte / Solid 这类“编译期消除 diff”的方案才出现，Vue3 也加了静态提升与 Patch Flag 来减少运行时比较。回答时别把“虚拟 DOM 快”当结论——**快的是批量与最小化更新，不是那一层对象结构本身**。

## 十、错误处理与健壮性（5 题）

### 87. JavaScript 错误处理的最佳实践是什么？｜中级

```javascript
try {
  const data = JSON.parse(text);
  return data;
} catch (err) {
  if (err instanceof SyntaxError) { /* 数据坏了：走降级 */ }
  reportError(err);       // 上报（带上下文）
  throw new AppError('解析失败', { cause: err });   // 转成业务错误再抛
} finally {
  hideLoading();          // 一定会执行，用于清理
}
```

四条原则：

1. **只捕获能处理的错误**，不要把 `try` 当成万能壳——吞掉异常比崩溃更难查（`catch {}` 空块是反模式）。
2. 捕获后要么修复、要么**补充上下文再抛**（`Error.cause` 保留原始错误链）。
3. 异常不用于控制流：预期内的分支（如校验失败）用返回值 / `Result` 表达，异常只留给意外。
4. 分层处理：函数内部抛、业务边界（API 层）统一转成可展示的错误文案。

常见错误类型：`SyntaxError`（解析期）、`ReferenceError`（未声明）、`TypeError`（类型不对）、`RangeError`（越界 / 栈溢出）、`URIError`（编解码失败）。

### 88. 哪些错误 `try/catch` 抓不到？全局兜底怎么做？｜高级

抓不到的情形：

```javascript
// 1. 未 await / 未 .catch 的 Promise 拒绝 —— 逃出 try 的作用域
try { Promise.reject(new Error('x')); } catch (e) { /* 抓不到 */ }

// 2. 语法错误：代码根本没跑起来，try 包不住（同文件内）
// 3. 异步回调里抛错（setTimeout、事件处理器），栈已经换了
try { setTimeout(() => { throw new Error('y'); }, 0); } catch (e) { /* 抓不到 */ }

// 4. 跨域脚本的运行时错误被脱敏为 "Script error."，看不到堆栈
```

兜底靠三条全局通道：

```javascript
window.addEventListener('error', (e) => {
  // 资源加载失败（img/script）也走这里：e.target 是元素而非 window
  if (e.target && e.target !== window) return reportResourceError(e.target);
  reportError(e.error ?? e.message, { source: e.filename, line: e.lineno });
});

window.addEventListener('unhandledrejection', (e) => {
  reportError(e.reason);
  e.preventDefault();          // 可选：阻止控制台报错
});

// 跨域脚本脱敏的解法：<script crossorigin="anonymous"> + 服务端 Access-Control-Allow-Origin
```

> 🎯 关键要点：`error` 事件同时覆盖 JS 异常与资源加载失败，后者 `e.error` 为 undefined、`e.target` 是元素——判错分支就靠这一点。

### 89. 自定义错误类怎么设计？错误边界是什么？｜中级

```javascript
class AppError extends Error {
  constructor(message, { cause, code, context } = {}) {
    super(message, { cause });      // cause 保留原始错误链
    this.name = this.constructor.name;
    this.code = code;
    this.context = context;
  }
}

class NetworkError extends AppError {}    // 可重试
class ValidationError extends AppError {  // 不可重试，直接展示给用户
  constructor(message, field) { super(message, { code: 'VALIDATION' }); this.field = field; }
}

// 分层处理：网络错误可自动重试，校验错误不行
function handle(err) {
  if (err instanceof NetworkError) return retry(err);
  if (err instanceof ValidationError) return showFieldError(err.field, err.message);
  throw err;   // 不认识的错误继续往上抛，别吞
}
```

三个必须做的细节：`extends Error` 后要修 `name`（否则全是 `"Error"`）；`Object.setPrototypeOf` 在老转译目标下需要手动修复原型链；`Error.captureStackTrace`（V8）可隐藏构造函数自身的栈帧。React 里的错误边界组件（`componentDidCatch` / `getDerivedStateFromError`）是同一思路的 UI 层实现——隔离故障区域，避免整树崩溃。

### 90. 防御式编程和 fail-fast 冲突吗？怎么取舍？｜中级

不冲突，它们作用于不同边界：

- **fail-fast** 用在开发期与内部模块边界：参数不符合契约立刻抛错，暴露问题（`if (typeof id !== 'string') throw new TypeError(...)`）。
- **防御式**用在系统边界与不可信输入：外部接口返回、用户输入、第三方 SDK，全部当作可能不合法处理，兜底降级而不是崩掉整个页面。

```javascript
function renderUser(raw) {
  // 边界：防御式，缺字段给默认值，保证渲染不炸
  const user = {
    name: raw?.name ?? '匿名用户',
    age: Number.isFinite(raw?.age) ? raw.age : null,
    tags: Array.isArray(raw?.tags) ? raw.tags.filter(t => typeof t === 'string') : [],
  };
  return view(user);
}

function setAge(n) {
  // 内部：fail-fast，调用方写错立刻暴露
  if (!Number.isInteger(n) || n < 0) throw new RangeError(`非法年龄: ${n}`);
}
```

分层原则一句话：**对外宽容、对内严格**。反过来做（内部到处兜底、外部不校验）就是典型的线上事故配方。

### 91. 线上 JS 报错怎么定位到源码？监控上报要注意什么？｜高级

生产代码压缩后堆栈是 `a.b.c is not a function at main.3f9a2c.js:1:48213`，必须靠 **sourcemap** 还原。正确做法是上传 sourcemap 到监控平台（或私有存储），**不要**把 `.map` 部署到 CDN 公开目录——它会把源码全暴露出去。

```javascript
const { SourceMapConsumer } = require('source-map');
const consumer = await new SourceMapConsumer(mapJson);
consumer.originalPositionFor({ line: 1, column: 48213 });
// { source: 'src/utils/format.ts', line: 42, column: 8, name: 'formatDate' }
```

上报侧的关键考量：

| 问题 | 做法 |
|------|------|
| 报错风暴 | 按“错误栈指纹”聚合去重，单位时间限流 |
| 采样 | 首屏 / 核心链路全量，其余按比例采样 |
| 上下文 | 带上用户 ID、路由、版本、UA、前置操作（面包屑） |
| 丢数据 | `sendBeacon` 在页面卸载时更可靠；失败落 `localStorage` 下次补传 |
| 噪音 | 过滤浏览器插件、爬虫、`ResizeObserver loop` 这类已知无害错误 |

## 十一、性能与内存（5 题）

### 92. 怎么检测和修复内存泄漏？｜高级

泄漏 = 不再需要的对象仍被强引用。六种高频来源：

| 泄漏源 | 修复 |
|--------|------|
| 未清除的定时器 / 轮询 | 保存句柄，卸载时 `clearInterval` |
| 未解绑的事件监听 | `removeEventListener` / `AbortController` 统一取消 |
| 全局变量（漏写声明） | `"use strict"` + lint |
| 闭包持有大对象 | 用后置 `null`，或只捕获需要的字段 |
| DOM 已删除但引用仍在 | 用 `WeakMap` 关联数据，别在 JS 里长期持有节点 |
| 无上限的缓存 / 数组 | LRU 上限，或 `WeakRef` + `FinalizationRegistry` |

检测流程：DevTools Memory 面板取两个时间点的 Heap Snapshot，在 Comparison 里看 `#Delta` 持续为正的构造函数；或开 `Performance monitor` 观察 GC 后 JS Heap 是否仍单调上升；Allocation instrumentation on timeline 可精确定位分配点。

```javascript
// 统一的取消入口，比散落的 removeEventListener 可靠
const ac = new AbortController();
el.addEventListener('click', onClick, { signal: ac.signal });
setInterval(poll, 1000);
// 卸载时
ac.abort();
```

### 93. 万级列表怎么渲染才不卡？｜高级

一次渲染上万 DOM 节点，光是创建 + 布局就要几百毫秒。核心策略是**只渲染视口内可见的项**：

```javascript
// 虚拟滚动原理：外层固定高度可滚动，内层用撑高的占位，只渲染可视区 + 缓冲
function render() {
  const scrollTop = container.scrollTop;
  const start = Math.floor(scrollTop / ITEM_H);
  const end = Math.min(start + Math.ceil(VIEW_H / ITEM_H) + BUFFER, total);
  inner.style.height = total * ITEM_H + 'px';
  inner.style.transform = `translateY(${start * ITEM_H}px)`;
  paint(items.slice(start, end));
}
container.addEventListener('scroll', () => requestAnimationFrame(render), { passive: true });
```

必须处理的三件事：**不定高**项要用测量 + 估算混合（否则滚动条乱跳）；**滚动锚定**（列表上方插入内容时保持视口位置）；**键盘 / 搜索定位**到未渲染项（先滚动到估算位置再校正）。若列表只是要快速浏览且节点简单，也可以先上 `content-visibility: auto` 让浏览器跳过屏外渲染，成本更低。

### 94. Core Web Vitals 的三个指标分别怎么优化？｜高级

| 指标 | 含义 | 主要优化手段 |
|------|------|--------------|
| LCP（最大内容绘制） | 首屏主内容出现时间 | 图片预加载 / `fetchpriority`、字体 `font-display: swap`、SSR 直出、CDN、减少阻塞资源 |
| INP（交互到下次绘制） | 交互响应速度 | 拆长任务、事件回调轻量化、`scheduler.yield`、避免同步布局 |
| CLS（累积布局偏移） | 视觉稳定性 | 图片 / 广告位预留尺寸、字体 `size-adjust` 或 `fallback` 定量、避免插入式横幅 |

```html
<!-- 关键资源提前拉，不要等 CSS 解析完 -->
<link rel="preload" as="image" href="/hero.webp" fetchpriority="high">
<!-- 图片占位，杜绝 CLS -->
<img src="hero.webp" width="1200" height="600" alt="">
```

采集方式：`PerformanceObserver` 监听 `largest-contentful-paint`、`layout-shift`、`event`，或用 `web-vitals` 库；注意 LCP 会被后续更大的元素刷新、CLS 在用户交互后 500ms 内的偏移不计入（手动滚动导致的偏移不算）。

### 95. tree-shaking 为什么有时候不生效？｜中级

前提是 **ESM 静态结构 + 无副作用可判定**。破坏条件主要有四个：

```javascript
// 1. CommonJS：require 是运行时行为，静态分析看不到
const _ = require('lodash');           // 整个包进包

// 2. 副作用：顶层执行了不可消除的代码
import './polyfill';                    // 有副作用，必须保留
export const registry = new Map();      // 顶层 new Map 视为副作用，可能被保留

// 3. 类 / 对象的属性被动态访问，无法证明未使用
// 4. babel 转译成 CJS（preset-env 的 modules: 'commonjs'）—— 最常见的元凶
```

```json
// package.json：声明哪些文件无副作用，允许打包器安全剔除
{ "sideEffects": ["*.css", "./src/polyfill.ts"] }
```

其余体积治理手段：按路由做代码分割（`import()`）、依赖替换（`dayjs` 替 `moment`、`lodash-es` 替 `lodash`）、`externals` / CDN 外置、构建产物分析（`rollup-plugin-visualizer`）找出体积大头。压缩与 gzip / brotli 是最后一道，不要用它掩盖依赖膨胀。

### 96. 计算缓存和空闲调度怎么配合？｜中级

三层调度，按“什么时候必须算完”选：

```javascript
// 1. 立即需要 → 同步算，但结果要缓存（memoize）
// 2. 可延后到空闲 → requestIdleCallback（记得设 timeout 兜底）
requestIdleCallback((deadline) => {
  while (deadline.timeRemaining() > 5 && queue.length) process(queue.shift());
}, { timeout: 2000 });

// 3. 与渲染相关 → requestAnimationFrame
// 4. 纯计算重活 → Worker
```

React 生态的等价物是 `useMemo` / `useCallback`（缓存）与并发渲染的时间切片（调度）。注意 `useMemo` 不是性能银弹：依赖数组写错会导致陈旧结果，缓存本身也有内存与比较成本——只在 Profiler 显示重复计算明显时才加。

> ⚠️ 注意：`requestIdleCallback` 在 Safari 长期不支持（需 polyfill），且空闲回调可能长时间不执行；涉及用户可见的更新不要依赖它。

## 十二、设计模式与工程实践（4 题）

### 97. 单例模式有哪些实现方式？在什么场景下它是坏味道？｜中级

```javascript
// 1. 类静态字段（推荐：语义清晰，可测试性尚可）
class ConfigService {
  static #instance;
  static get instance() { return (this.#instance ??= new ConfigService()); }
  #config = {};
  load(url) { /* ... */ }
}

// 2. 模块单例（ESM 天然保证只执行一次，最省事）
export const config = { apiUrl: '/api', timeout: 3000 };

// 3. 惰性单例 + 闭包（需要“首次使用时才初始化”的重资源）
let conn;
export const getConn = () => (conn ??= createConnection());
```

真实用途：全局配置、日志器、连接 / 连接池、缓存、全局事件总线。

坏味道场景：把单例当**全局可变状态**用——任何模块都能改，测试之间互相污染，并行测试直接失效。判据很简单：如果这个单例持有业务状态且会被多处写，就该改成依赖注入（构造时传入实例），把生命周期交给上层管理，测试时也能替换成假实现。

### 98. 发布订阅和观察者模式有什么区别？“事件总线”为什么容易失控？｜中级

```javascript
// 观察者：主题持有观察者列表，直接调用（强耦合、一对一）
class Subject {
  #observers = new Set();
  subscribe(o) { this.#observers.add(o); return () => this.#observers.delete(o); }
  notify(d) { this.#observers.forEach(o => o.update(d)); }
}

// 发布订阅：中间有事件中心，发布者与订阅者互不认识（松耦合、多对多）
class Bus {
  #map = new Map();
  on(evt, fn) { (this.#map.get(evt) ?? this.#map.set(evt, new Set()).get(evt)).add(fn);
                return () => this.off(evt, fn); }
  off(evt, fn) { this.#map.get(evt)?.delete(fn); }
  emit(evt, payload) { this.#map.get(evt)?.forEach(fn => fn(payload)); }
}
```

| 维度 | 观察者 | 发布订阅 |
|------|--------|----------|
| 耦合 | 主题知道观察者 | 双方只依赖事件中心 |
| 关系 | 一对多 | 多对多 |
| 典型实现 | DOM 事件、`MutationObserver` | EventBus、`mitt`、Node `EventEmitter` |

事件总线失控的三种症状：**事件名散落成魔法字符串**（拼错就静默失败）；**订阅方不解绑**（组件卸载后仍在响应，甚至内存泄漏）；**调用链藏在事件里**（追一个数据变更要全局搜，调试成本极高）。治理：事件名集中定义成常量并加类型、订阅统一返回取消函数并在卸载钩子里调用、跨模块通信优先用显式函数调用或状态管理。

### 99. 怎么用高阶函数实现日志、重试、缓存这类横切关注点？｜高级

思路是把“非业务逻辑”包成装饰器，业务函数保持纯净：

```javascript
const withLog = (fn, name = fn.name) => (...args) => {
  const t0 = performance.now();
  try {
    const result = fn(...args);
    console.log(`${name} ok ${(performance.now() - t0).toFixed(1)}ms`, args);
    return result;
  } catch (e) {
    console.error(`${name} failed`, e);
    throw e;
  }
};

const withRetry = (fn, { times = 3, isRetryable = () => true } = {}) => async (...args) => {
  for (let i = 0; ; i++) {
    try { return await fn(...args); }
    catch (e) { if (i >= times - 1 || !isRetryable(e)) throw e; }
  }
};

const withCache = (fn) => {
  const cache = new Map();
  return (key) => (cache.has(key) || cache.set(key, fn(key)), cache.get(key));
};

// 组合：顺序即语义（谁在外层谁先看到调用）
const fetchUser = withLog(withRetry(withCache(rawFetchUser), { times: 3 }));
```

要点：组合顺序决定语义（重试应在缓存**内层**，否则缓存命中前会白重试）；异步版本要 `await`；装饰后要保留原函数的 `length` / `name`（便于调试与框架识别），可用 `Object.defineProperty` 修正。TS 里就是装饰器 / `AOP` 的实践形态。

### 100. 前端项目怎么做依赖注入？循环依赖怎么治理？｜高级

DI 的本质是“**依赖由外部传入，而不是模块内部自己 new/import 具体实现**”，好处是可替换、可测试、生命周期集中管理。

```javascript
// 显式注入：构造时传入，最容易测试
class OrderService {
  constructor({ api, logger }) { this.api = api; this.logger = logger; }
  async create(dto) {
    this.logger.info('create order');
    return this.api.post('/orders', dto);
  }
}

// 极简容器：注册 + 解析，注意用工厂函数避免过早初始化
const container = new Map();
const register = (key, factory) => container.set(key, { factory, instance: null });
const resolve = (key) => {
  const entry = container.get(key);
  if (!entry) throw new Error(`未注册: ${key}`);
  return (entry.instance ??= entry.factory());
};
register('logger', () => createLogger());
register('api', () => createApi(resolve('logger')));
register('orderService', () => new OrderService({ api: resolve('api'), logger: resolve('logger') }));
```

循环依赖的三种治理手套，从轻到重：

| 手段 | 做法 | 代价 |
|------|------|------|
| 抽取共享模块 | 把互相依赖的共同部分下沉 | 需要重构，最健康 |
| 依赖注入 / 事件解耦 | A 不直接引用 B，通过接口或事件通信 | 增加一层间接 |
| 动态 `import()` | 需要时再加载，绕开顶层环 | 变成异步，治标 |

排查工具：构建时告警（`madge --circular src`）、ESM 里遇到“拿到未初始化绑定”的 TDZ 报错基本就是环。

