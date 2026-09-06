---
outline: [1,3]
head:
  - - meta
    - name: description
      content: 立即执行函数
  - - meta
    - name: keywords
      content: 立即执行函数
tags: [JavaScript]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/javascript/IIFE.md"
---

IIFE（Immediately Invoked Function Expression，立即调用函数表达式）是一种在定义后立即执行的函数模式。它常用于创建私有作用域、避免污染全局变量以及执行一次性初始化代码。

尽管核心思想一致，但 IIFE 有多种**语法变体**，主要区别在于如何将函数转换为“表达式”以防止 JavaScript 解析器将其解释为函数声明。

以下是常见的 IIFE 变体：

------

### ✅ 1. 标准括号包裹法（最常见）

```
// 标准 IIFE
(function() {
  console.log("IIFE 执行了！");
})();

// 异步 IIFE
(async () => {
  // 语句……
})();
```

- **原理**：外层括号 `( ... )` 将函数变为表达式。
- **执行**：后面紧跟 `()` 调用它。
- **优点**：清晰、通用、易读。

------



### ✅ 2. 感叹号（逻辑非）前缀



```
!function() {
  console.log("IIFE 执行了！");
}();
```

- **原理**：`!` 是一元操作符，强制其后的函数成为表达式。
- **注意**：返回值会被取反（`undefined` 变成 `true`），但通常忽略返回值，所以无影响。
- **用途**：压缩代码时可节省字符（比括号少一个字符）。

------

### ✅ 3. 加号前缀

```
+function() {
  console.log("IIFE 执行了！");
}();
```

- **原理**：`+` 也是一元操作符，使函数成为表达式。
- **返回值**：不会取反，但会尝试转换为数字（不常用）。

------

### ✅ 4. void 前缀

```
void function() {
  console.log("IIFE 执行了！");
}();
```

- **原理**：`void` 操作符总是返回 `undefined`，并强制其右侧为表达式。
- **优点**：确保返回值为 `undefined`，避免意外。
- **场景**：用于防止某些浏览器将 IIFE 解释为链接。

------

### ✅ 5. 逗号操作符

```
0,function() {
  console.log("IIFE 执行了！");
}();
```

- **原理**：逗号操作符执行多个表达式，返回最后一个。`0, function(){}` 是表达式。
- **不推荐**：可读性差，几乎不用。

------

### ✅ 6. 赋值操作符

```
var a = function() {
  console.log("IIFE 执行了！");
}();
```

- **原理**：赋值语句中，右侧必须是表达式。
- **副作用**：`a` 会接收函数的返回值（通常是 `undefined`）。
- **注意**：这不是纯粹的 IIFE，因为有变量声明。
- 没有外层括号，但因为 = 右边必须是表达式，所以函数自动成为表达式。
- 返回值无关紧要，重点是执行。

------

### ✅ 7. 箭头函数 IIFE（ES6+）

```
(() => {
  console.log("箭头函数 IIFE 执行了！");
})();
```

- **现代写法**：使用箭头函数语法。
- **注意**：箭头函数没有自己的 `this`、`arguments`、`super`，在某些场景下需注意上下文差异。

------

### ✅ 8. 传参的 IIFE （重要）

所有变体都可以接受参数：

```
(function(window, document) {
  // 在函数内安全使用 window 和 document
  console.log(window.location);
})(window, document);
```

- **用途**：提高性能（作用域链更短）或创建别名（如 `jQuery` 的 `$`）。

------

### ✅ 9. 返回值的 IIFE

和第六的区别是：强调“IIFE 返回一个有用的**对象**”

IIFE 可以返回值，用于初始化变量：

```
const config = (function() {
  const privateData = "secret";
  return {
    apiUrl: "https://api.example.com",
    getVersion: () => "1.0"
  };
})();
```

- **用途**：创建模块模式，暴露公共接口，隐藏私有变量。

------

### 📌 总结：IIFE 的核心思想

> **让函数变成表达式，然后立即调用它。**

| 变体                  | 语法     | 特点               |
| --------------------- | -------- | ------------------ |
| `(function(){})()`    | ✅ 最标准 | 推荐使用           |
| `!function(){}`()     | ✅ 常见   | 压缩友好           |
| `+function(){}`()     | ✅ 可用   | 少见               |
| `void function(){}`() | ✅ 安全   | 确保返回 undefined |
| `(() => {})()`        | ✅ 现代   | ES6 箭头函数       |

------

### ⚠️ 注意事项

- IIFE 在 **ES6 模块**和 **现代打包工具**（如 Webpack、Vite）中已较少使用，因为模块天然提供作用域隔离。
- 但在 **全局脚本**、**插件开发**、**兼容老代码**中仍有价值。

------

### 💡 经典应用场景

```
// 1. 避免全局变量污染
(function() {
  var temp = "临时变量";
  // 外部无法访问 temp
})();

// 2. 创建私有作用域的模块
const Counter = (function() {
  let count = 0;
  return {
    inc: () => ++count,
    dec: () => --count,
    val: () => count
  };
})();

Counter.inc(); // 1
```

总之，IIFE 的多种变体展示了 JavaScript 语法的灵活性，选择哪种主要取决于风格和上下文。