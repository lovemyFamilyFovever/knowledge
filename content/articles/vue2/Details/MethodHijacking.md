---
title: "MethodHijacking"
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/MethodHijacking.md"
---



 **Vue 2 响应式系统中对数组变异方法（mutating methods）进行拦截的关键实现**。

它的目标是：**让通过 `push`、`pop` 等方法修改数组时，也能触发视图更新**。 

`Object.defineProperty` 只能拦截**属性的读取（getter）和设置（setter）**，但无法监听数组下标赋值（如 `arr[0] = val`）或长度变化（`arr.length = 0`）。更麻烦的是，像 `arr.push(1)` 这样的操作，本质上是调用 `Array.prototype.push`，并不会触发任何 setter！

为了解决这个问题，Vue 采用了一种巧妙的“**方法劫持（Method Hijacking）**”策略。

```
var arrayProto = Array.prototype;
  // 创建一个继承自数组原型的新对象
  var arrayMethods = Object.create(arrayProto);//创建一个新对象，使用现有的对象来提供新创建的对象的原型。

  // 需要拦截的方法列表
  // 注意：filter、map、slice 等返回新数组的方法不会改变原数组，所以不需要拦截。
  var methodsToPatch = [
    'push', //在数组的末尾添加一个或多个元素，并返回新的长度。
    'pop', //移除数组的最后一个元素，并返回那个元素。
    'shift',//移除数组的第一个元素，并返回那个元素。
    'unshift',//在数组的开头添加一个或多个元素，并返回新的长度。
    'splice',//通过删除、替换或添加新元素来改变数组的内容。
    'sort',//对数组元素进行排序。
    'reverse'//颠倒数组中元素的顺序。
  ];

  /**
   * Intercept mutating methods and emit events
   */
  methodsToPatch.forEach(function (method) {
    // cache original method
    // 缓存原始方法
    var original = arrayProto[method];
    def(arrayMethods, method, function mutator () {
      var args = [], len = arguments.length;
      while ( len-- ) args[ len ] = arguments[ len ];

      var result = original.apply(this, args);
      var ob = this.__ob__;
      var inserted;
      switch (method) {
        case 'push':
        case 'unshift':
          inserted = args;
          break
        case 'splice':
          inserted = args.slice(2);
          break
      }
      if (inserted) { ob.observeArray(inserted); }
      // notify change
      ob.dep.notify();
      return result
    });
  });
```

