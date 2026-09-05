---
title: "JavaScript核心概念面试题库 - 100道精选题目"
tags: []
source: "baike"
source_path: "技术题库 / JavaScript核心"
collected: "2026-09-05"
status: "imported"
---

JavaScript核心概念面试题库 - 100道精选题目
JavaScript核心概念
100道精选面试题 | 涵盖语言核心、异步编程、面向对象等
📚 100道题目
💡 300+回答模板
🎯 高频考点
📈 从基础到高级
🔗 闭包与作用域
🔄 原型与继承
⏳ 异步编程
🔄 事件循环
📊 数据类型
⚡ 函数高级
📦 对象与数组
🚀 ES6+特性
🌐 DOM操作
⚠️ 错误处理
⚡ 性能优化
🎨 设计模式
🔗 闭包与作用域（15题）
1
请详细解释JavaScript中的闭包（Closure）是什么？它有哪些实际应用场景？
中等
核心概念
闭包
作用域
内存管理
展开答案
💡 回答模板一：基础概念型
"闭包是指一个函数能够记住并访问它的词法作用域，即使这个函数在其词法作用域之外执行。简单来说，闭包是由函数以及声明该函数的词法环境组合而成的。
                            
                            实际应用场景包括：
                            1. 数据私有化：创建私有变量和方法
                            2. 函数工厂：创建具有特定配置的函数
                            3. 回调函数：保持对外部变量的引用
                            4. 模块模式：实现模块化封装
                            5. 防抖和节流：保持定时器状态"
// 闭包示例：数据私有化
function createCounter() {
  let count = 0; // 私有变量
  
  return {
    increment() {
      count++;
      return count;
    },
    decrement() {
      count--;
      return count;
    },
    getCount() {
      return count;
    }
  };
}

const counter = createCounter();
console.log(counter.increment()); // 1
console.log(counter.increment()); // 2
console.log(counter.getCount());  // 2
💡 回答模板二：实际应用型
"闭包在实际开发中非常实用。我曾经在一个项目中使用闭包实现了状态管理器，让组件之间能够共享状态而不需要全局变量。
                            
                            具体实现：
                            - 创建了一个可复用的状态管理类
                            - 使用闭包封装状态，提供get/set方法
                            - 支持状态变化的订阅和通知
                            
                            这种方式既保证了数据的封装性，又提供了灵活的访问接口。在性能优化方面，我会注意避免不必要的闭包，特别是在循环中，因为闭包会阻止垃圾回收。"
💡 回答模板三：深度解析型
"闭包的本质是JavaScript词法作用域的延伸。当内部函数引用了外部函数的变量时，这些变量不会被垃圾回收，而是被内部函数捕获。
                            
                            这带来了灵活性，但也需要注意内存管理：
                            1. 闭包会持有外部变量的引用，可能导致内存泄漏
                            2. 在循环中创建闭包需要特别注意变量绑定
                            3. 现代JavaScript引擎对闭包有优化，但理解原理仍然重要
                            
                            在ES6+中，块级作用域（let/const）的出现让闭包的使用更加精细，我们可以更精确地控制变量的生命周期。"
💡 面试提示
这个问题考察你对JavaScript核心概念的理解深度。回答时要结合实际项目经验，展示你不仅知道概念，还能在实际场景中应用。如果提到性能注意事项，会显得更专业。
2
JavaScript中的作用域链是什么？它是如何工作的？
简单
作用域
作用域链
变量查找
展开答案
💡 回答模板一：概念解释型
"作用域链是JavaScript中用于变量查找的机制。当代码需要访问一个变量时，JavaScript引擎会首先在当前作用域中查找，如果找不到，就会向上级作用域查找，直到找到该变量或到达全局作用域。
                            
                            作用域链的形成：
                            1. 每个函数创建时都会形成一个作用域
                            2. 内部函数可以访问外部函数的变量
                            3. 这种层层嵌套的关系形成了作用域链
                            
                            例如：全局作用域 → 函数A作用域 → 函数B作用域"
💡 回答模板二：实际应用型
"理解作用域链对于避免变量污染和命名冲突非常重要。在我的项目中，我经常使用模块化来管理作用域，确保每个模块都有独立的作用域。
                            
                            同时，我会注意：
                            1. 避免全局变量的滥用
            ```javascript
// 模块模式避免全局污染
const myModule = (function() {
  let privateVar = '私有变量';
  
  function privateMethod() {
    console.log(privateVar);
  }
  
  return {
    publicMethod: function() {
      privateMethod();
    }
  };
})();
🔄 原型与继承（12题）
1
请解释JavaScript的原型链（Prototype Chain）是什么？它是如何实现继承的？
困难
面向对象
原型链
继承
面向对象
展开答案
💡 回答模板一：基础概念型
"原型链是JavaScript实现继承的核心机制。每个对象都有一个内部链接指向另一个对象，称为它的原型，这个原型对象也有自己的原型，如此层层向上，直到一个对象的原型为null。
                            
                            原型链的工作原理：
                            1. 每个函数都有一个prototype属性，指向一个对象
                            2. 通过构造函数创建的对象，其__proto__指向构造函数的prototype
                            3. 当访问对象属性时，如果对象本身没有，会沿着原型链向上查找
                            4. 直到找到该属性或到达原型链的末端（null）"
// 原型链示例
function Animal(name) {
  this.name = name;
}

Animal.prototype.speak = function() {
  console.log(this.name + ' makes a sound.');
};

function Dog(name) {
  Animal.call(this, name);
}

Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;

Dog.prototype.bark = function() {
  console.log(this.name + ' barks!');
};

const dog = new Dog('Rex');
dog.bark(); // Rex barks!
dog.speak(); // Rex makes a sound.
💡 回答模板二：ES6+继承型
"在ES6+中，我们可以使用class和extends关键字来实现继承，这实际上是原型链的语法糖。
                            
                            ES6继承的优势：
                            1. 语法更清晰，更接近传统面向对象语言
                            2. 可以使用super关键字调用父类构造函数
                            3. 支持静态方法和静态属性
                            4. 默认设置constructor属性
                            
                            但底层仍然是基于原型链的继承机制。"
// ES6继承示例
class Animal {
  constructor(name) {
    this.name = name;
  }
  
  speak() {
    console.log(`${this.name} makes a sound.`);
  }
}

class Dog extends Animal {
  bark() {
    console.log(`${this.name} barks!`);
  }
}

const dog = new Dog('Rex');
dog.bark(); // Rex barks!
dog.speak(); // Rex makes a sound.
⏳ 异步编程（15题）
1
请解释Promise的工作原理，以及如何处理异步操作？
中等
异步编程
Promise
异步
回调
展开答案
💡 回答模板一：基础概念型
"Promise是JavaScript中处理异步操作的一种方式，它代表一个异步操作的最终完成或失败。
                            
                            Promise有三种状态：
                            1. pending：初始状态，既不是成功，也不是失败
                            2. fulfilled：操作成功完成
                            3. rejected：操作失败
                            
                            Promise的工作原理：
                            - 创建Promise时，会立即执行传入的执行器函数
                            - 执行器函数接收resolve和reject两个参数
                            - 调用resolve会将Promise状态改为fulfilled
                            - 调用reject会将Promise状态改为rejected
                            - 状态一旦改变就不可逆"
// Promise基础示例
const myPromise = new Promise((resolve, reject) => {
  setTimeout(() => {
    const success = true;
    if (success) {
      resolve('操作成功！');
    } else {
      reject('操作失败！');
    }
  }, 1000);
});

myPromise
  .then(result => console.log(result))
  .catch(error => console.error(error))
  .finally(() => console.log('操作完成'));
💡 回答模板二：实际应用型
"在实际项目中，我经常使用Promise来处理网络请求、文件操作等异步任务。
                            
                            常用的Promise方法：
                            1. Promise.all()：并行执行多个Promise，全部成功才成功
                            2. Promise.race()：并行执行多个Promise，第一个完成的结果
                            3. Promise.allSettled()：等待所有Promise完成，不管成功失败
                            4. Promise.any()：并行执行多个Promise，第一个成功的
                            
                            这些方法让我能够优雅地处理复杂的异步场景。"
🔄 事件循环（12题）
1
请详细解释JavaScript的事件循环（Event Loop）机制？
困难
运行时机制
事件循环
调用栈
任务队列
展开答案
💡 回答模板一：基础概念型
"事件循环是JavaScript处理异步操作的核心机制。JavaScript是单线程语言，但通过事件循环实现了非阻塞的异步操作。
                            
                            事件循环的工作流程：
                            1. 执行同步代码，将异步操作放入任务队列
                            2. 同步代码执行完毕后，检查微任务队列
                            3. 执行所有微任务，直到微任务队列清空
                            4. 从宏任务队列中取出一个任务执行
                            5. 重复步骤2-4
                            
                            任务队列分为：
                            - 宏任务（Macro Task）：setTimeout、setInterval、I/O、UI渲染
                            - 微任务（Micro Task）：Promise.then、MutationObserver、process.nextTick"
// 事件循环示例
console.log('1'); // 同步代码

setTimeout(() => {
  console.log('2'); // 宏任务
}, 0);

Promise.resolve().then(() => {
  console.log('3'); // 微任务
});

console.log('4'); // 同步代码

// 输出顺序：1, 4, 3, 2
📊 数据类型（10题）
1
JavaScript有哪些数据类型？如何判断数据类型？
简单
基础概念
数据类型
typeof
类型判断
展开答案
💡 回答模板一：基础概念型
"JavaScript有8种数据类型：
                            
                            基本类型（7种）：
                            1. Number：数字类型
                            2. String：字符串类型
                            3. Boolean：布尔类型
                            4. Undefined：未定义类型
                            5. Null：空值类型
                            6. Symbol：符号类型（ES6新增）
                            7. BigInt：大整数类型（ES2020新增）
                            
                            引用类型（1种）：
                            8. Object：对象类型（包括Array、Function、Date等）
                            
                            类型判断方法：
                            - typeof：返回类型的字符串表示
                            - instanceof：判断对象是否是某个构造函数的实例
                            - Object.prototype.toString.call()：返回更准确的类型信息"
// 类型判断示例
console.log(typeof 123);          // "number"
console.log(typeof "hello");      // "string"
console.log(typeof true);         // "boolean"
console.log(typeof undefined);    // "undefined"
console.log(typeof null);         // "object" (历史遗留bug)
console.log(typeof []);           // "object"
console.log(typeof {});           // "object"

// 更准确的类型判断
console.log(Object.prototype.toString.call([]));     // "[object Array]"
console.log(Object.prototype.toString.call({}));     // "[object Object]"
console.log(Array.isArray([]));                      // true
⚡ 函数高级（10题）
1
什么是函数柯里化（Currying）？它有什么实际应用场景？
中等
函数式编程
柯里化
函数式编程
展开答案
💡 回答模板一：基础概念型
"函数柯里化是一种将多参数函数转换为一系列单参数函数的技术。柯里化后的函数每次接收一个参数，返回一个新函数，直到所有参数都被接收，最后执行原函数。
                            
                            柯里化的优势：
                            1. 参数复用：可以创建预设参数的函数
                            2. 延迟执行：可以推迟函数的执行
                            3. 提高复用性：更容易创建可复用的函数
                            
                            实际应用：
                            - 创建预设参数的函数
                            - 事件处理函数
                            - 函数式编程中的管道操作"
// 柯里化实现
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    } else {
      return function(...args2) {
        return curried.apply(this, args.concat(args2));
      };
    }
  };
}

// 使用示例
function add(a, b, c) {
  return a + b + c;
}

const curriedAdd = curry(add);
console.log(curriedAdd(1)(2)(3));    // 6
console.log(curriedAdd(1, 2)(3));    // 6
console.log(curriedAdd(1)(2, 3));    // 6
📦 对象与数组（10题）
1
如何实现深拷贝和浅拷贝？它们有什么区别？
中等
数据操作
深拷贝
浅拷贝
引用类型
展开答案
💡 回答模板一：基础概念型
"浅拷贝和深拷贝的区别在于是否复制嵌套对象的引用。
                            
                            浅拷贝：
                            - 只复制对象的第一层属性
                            - 嵌套对象仍然是引用
                            - 修改嵌套对象会影响原对象
                            
                            深拷贝：
                            - 递归复制所有层级的属性
                            - 完全独立的副本
                            - 修改任何副本都不会影响原对象
                            
                            实现方式：
                            1. 浅拷贝：Object.assign()、展开运算符、Array.prototype.slice()
                            2. 深拷贝：JSON.parse(JSON.stringify())、递归实现、lodash.cloneDeep()"
// 浅拷贝示例
const original = { a: 1, b: { c: 2 } };
const shallowCopy = { ...original };

shallowCopy.b.c = 3;
console.log(original.b.c); // 3（被修改了）

// 深拷贝示例
const deepCopy = JSON.parse(JSON.stringify(original));
deepCopy.b.c = 4;
console.log(original.b.c); // 3（未被修改）

// 更好的深拷贝实现
function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime());
  }
  
  if (obj instanceof Array) {
    return obj.map(item => deepClone(item));
  }
  
  if (obj instanceof Object) {
    const copy = {};
    Object.keys(obj).forEach(key => {
      copy[key] = deepClone(obj[key]);
    });
    return copy;
  }
}
🚀 ES6+特性（8题）
1
箭头函数与普通函数有什么区别？在什么场景下使用箭头函数？
简单
ES6特性
箭头函数
this绑定
展开答案
💡 回答模板一：基础概念型
"箭头函数与普通函数的主要区别：
                            
                            1. this绑定：
                            - 普通函数：this在调用时确定，取决于调用方式
                            - 箭头函数：this在定义时确定，继承外层作用域的this
                            
                            2. arguments对象：
                            - 普通函数：有arguments对象
                            - 箭头函数：没有arguments对象，使用rest参数代替
                            
                            3. 构造函数：
                            - 普通函数：可以用作构造函数，使用new关键字
                            - 箭头函数：不能用作构造函数
                            
                            4. 原型：
                            - 普通函数：有prototype属性
                            - 箭头函数：没有prototype属性"
// this绑定的区别
class Person {
  constructor(name) {
    this.name = name;
  }
  
  // 普通函数
  sayName() {
    setTimeout(function() {
      console.log(this.name); // undefined
    }, 100);
  }
  
  // 箭头函数
  sayNameArrow() {
    setTimeout(() => {
      console.log(this.name); // Person { name: 'John' }
    }, 100);
  }
}

const person = new Person('John');
person.sayName();      // undefined
person.sayNameArrow(); // John
🌐 DOM操作（8题）
1
如何优化DOM操作以提高性能？
中等
DOM优化
DOM性能
重绘重排
展开答案
💡 回答模板一：基础概念型
"DOM操作是昂贵的，因为每次操作都可能引起页面重绘和重排。优化DOM操作的方法：
                            
                            1. 减少DOM操作次数：
                            - 使用DocumentFragment批量插入
                            - 使用innerHTML代替多次createElement
                            
                            2. 避免频繁重排：
                            - 修改样式时批量修改
                            - 使用transform代替top/left
                            - 使用visibility代替display:none
                            
                            3. 使用虚拟DOM：
                            - React、Vue等框架的虚拟DOM机制
                            - 只更新变化的部分
                            
                            4. 使用requestAnimationFrame：
                            - 将DOM操作放在动画帧中
                            - 避免阻塞渲染"
⚠️ 错误处理（5题）
1
如何正确处理JavaScript中的错误和异常？
中等
错误处理
try-catch
错误类型
展开答案
💡 回答模板一：基础概念型
"JavaScript错误处理的最佳实践：
                            
                            1. 使用try-catch-finally：
                            - try：可能抛出错误的代码
                            - catch：处理错误
                            - finally：无论是否发生错误都执行
                            
                            2. 错误类型：
                            - Error：通用错误
                            - SyntaxError：语法错误
                            - ReferenceError：引用错误
                            - TypeError：类型错误
                            - RangeError：范围错误
                            
                            3. 自定义错误：
                            - 继承Error类
                            - 添加自定义属性
                            
                            4. 错误监控：
                            - window.onerror
                            - unhandledrejection事件
                            - 错误边界（React）"
// 错误处理示例
try {
  // 可能出错的代码
  const result = JSON.parse('invalid json');
} catch (error) {
  console.error('解析错误:', error.message);
  // 错误上报
  reportError(error);
} finally {
  // 清理资源
  cleanup();
}

// 自定义错误类
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
  }
}

// 使用自定义错误
function validateUser(user) {
  if (!user.name) {
    throw new ValidationError('姓名不能为空', 'name');
  }
  if (!user.email) {
    throw new ValidationError('邮箱不能为空', 'email');
  }
}
⚡ 性能优化（7题）
1
如何检测和优化JavaScript内存泄漏？
困难
性能优化
内存泄漏
性能监控
展开答案
💡 回答模板一：基础概念型
"内存泄漏是指程序中已动态分配的堆内存由于某种原因程序未释放或无法释放。
                            
                            常见的内存泄漏：
                            1. 全局变量：未使用var/let/const声明
                            2. 闭包：持有外部变量引用
                            3. 定时器：未清除的setInterval
                            4. 事件监听器：未移除的事件监听
                            5. DOM引用：保存已删除DOM元素的引用
                            6. 控制台日志：console.log保留引用
                            
                            检测方法：
                            - Chrome DevTools的Memory面板
                            - 使用heap snapshot对比
                            - 监控内存使用趋势
                            
                            优化策略：
                            - 及时释放不再需要的引用
                            - 使用弱引用（WeakMap、WeakSet）
                            - 避免不必要的闭包
                            - 清理定时器和事件监听"
// 内存泄漏示例和修复

// 泄漏：全局变量
function createLeak() {
  leak = '这是一个泄漏'; // 应该使用var/let/const
}

// 修复：使用局部变量
function createNoLeak() {
  const leak = '这没有泄漏';
}

// 泄漏：未清除的定时器
function createTimerLeak() {
  setInterval(() => {
    console.log('timer');
  }, 1000); // 没有保存引用，无法清除
}

// 修复：保存引用并清除
function createNoTimerLeak() {
  const timer = setInterval(() => {
    console.log('timer');
  }, 1000);
  
  // 需要时清除
  clearInterval(timer);
}

// 泄漏：闭包持有引用
function createClosureLeak() {
  const bigData = new Array(1000000).fill('*');
  
  return function() {
    console.log('闭包泄漏');
    // bigData被闭包持有，无法被垃圾回收
  };
}

// 修复：使用后释放
function createNoClosureLeak() {
  let bigData = new Array(1000000).fill('*');
  
  const fn = function() {
    console.log('没有泄漏');
  };
  
  bigData = null; // 释放引用
  return fn;
}
🎨 设计模式（5题）
1
请解释JavaScript中的单例模式（Singleton Pattern）及其应用场景？
中等
设计模式
单例模式
设计模式
展开答案
💡 回答模板一：基础概念型
"单例模式是一种创建型设计模式，它确保一个类只有一个实例，并提供一个全局访问点。
                            
                            单例模式的特点：
                            1. 只有一个实例
                            2. 全局访问点
                            3. 延迟初始化（可选）
                            
                            应用场景：
                            1. 配置管理器：全局配置对象
                            2. 日志记录器：统一的日志实例
                            3. 数据库连接池：共享连接资源
                            4. 缓存管理：统一的缓存实例
                            5. 状态管理：全局状态对象（如Redux Store）
                            
                            实现方式：
                            - 使用闭包
                            - 使用类的静态方法
                            - 使用模块导出"
// 单例模式实现
class Singleton {
  static instance = null;
  
  constructor() {
    if (Singleton.instance) {
      return Singleton.instance;
    }
    
    this.id = Math.random();
    Singleton.instance = this;
  }
  
  static getInstance() {
    if (!Singleton.instance) {
      Singleton.instance = new Singleton();
    }
    return Singleton.instance;
  }
}

// 使用示例
const instance1 = new Singleton();
const instance2 = new Singleton();
console.log(instance1 === instance2); // true

// 配置管理器示例
class ConfigManager {
  static instance = null;
  config = {};
  
  constructor() {
    if (ConfigManager.instance) {
      return ConfigManager.instance;
    }
    
    this.loadConfig();
    ConfigManager.instance = this;
  }
  
  loadConfig() {
    // 从服务器或本地存储加载配置
    this.config = {
      apiUrl: 'https://api.example.com',
      timeout: 5000,
      retries: 3
    };
  }
  
  get(key) {
    return this.config[key];
  }
  
  set(key, value) {
    this.config[key] = value;
  }
}
📚 JavaScript核心概念面试题库 | 100道精选题目
💡 每个问题提供2-3个回答模板，请根据实际情况选择和调整
🎯 建议：结合个人项目经验，用具体案例支撑观点
🔗
返回主页
|
下一章：React与Vue框架