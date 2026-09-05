---
outline: [2,3]
tags: [JavaScript, 模块化]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/javascript/export.md"
---

# 导出模块

在 `JavaScript` 中，使用 `export` 关键字可以将模块中的函数、对象、原始值等导出，以便其他模块可以使用。有两种常见的导出方式：分别暴露（命名导出）和统一暴露（默认导出）。

## 分别暴露（命名导出）

分别暴露允许您导出多个命名的导出项。这是通过在导出语句中指定每个项的名称来实现的。

```javascript
// mathFunctions.js
function add(a, b) {
    return a + b;
}

function subtract(a, b) {
    return a - b;
}

export { add, subtract };
```
在上面的例子中，`add` 和 `subtract` 函数被分别导出。其他模块可以通过导入语句导入这些函数：


```javascript
// app.js
import { add, subtract } from './mathFunctions';

console.log(add(2, 3)); // Output: 5
console.log(subtract(5, 2)); // Output: 3
```

也可以重命名导出项：

```javascript
// mathFunctions.js
//...
export { add as sum, subtract as difference };
```

在上面的例子中，`add` 函数被重命名为 `sum`，`subtract` 函数被重命名为 `difference`。其他模块可以通过导入语句导入这些函数：

```javascript
// app.js
import { sum, difference } from './mathFunctions';
```

## 统一暴露（默认导出）

统一暴露允许导出一个默认的导出项。每个模块只能有一个默认导出。

```JavaScript
// mathFunctions.js
function add(a, b) {
    return a + b;
}

function subtract(a, b) {
    return a - b;
}

export default { add, subtract };
```

在上面的例子中，`add` 和 `subtract` 函数被导出为默认导出。其他模块可以通过导入语句导入这些函数：

**【注意，默认导出时不需要大括号 {}。】**

```javascript
// app.js
import mathFunctions from './mathFunctions';

console.log(mathFunctions.add(2, 3)); // Output: 5
console.log(mathFunctions.subtract(5, 2)); // Output: 3
```

也可以重命名默认导出项：

```javascript
// mathFunctions.js
//...
export default { add as sum, subtract as difference };
```

在上面的例子中，`add` 函数被重命名为 `sum`，`subtract` 函数被重命名为 `difference`。其他模块可以通过导入语句导入这些函数：

```javascript
// app.js
import mathFunctions from './mathFunctions';

console.log(mathFunctions.sum(2, 3)); // Output: 5
console.log(mathFunctions.difference(5, 2)); // Output: 3
```

## 混合使用

也可以混合使用分别暴露和统一暴露。

```javascript
// utils.js
function add(a, b) {
  return a + b;
}

function subtract(a, b) {
  return a - b;
}

function multiply(a, b) {
  return a * b;
}

export { add, subtract };
export default multiply;
```

在上面的例子中，`add` 和 `subtract` 函数分别被分别暴露，`multiply` 函数被默认暴露。其他模块可以通过导入语句导入这些函数：


```javascript
// app.js
import { add, subtract } from './utils';
import multiply from './utils';


console.log(add(2, 3)); // Output: 5
console.log(subtract(5, 2)); // Output: 3
console.log(multiply(2, 3)); // Output: 6