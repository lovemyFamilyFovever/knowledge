---
outline: [1,3]
head:
  - - meta
    - name: description
      content: JavaScript字符串方法介绍
  - - meta
    - name: keywords
      content: JavaScript 字符串 前端开发 前端框架 前端工程师
tags: [JavaScript, String]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/javascript/String.md"
---

### 1. 字符串操作方法：

- **[charAt()](#string-charat)**：返回指定位置的字符
- **[charCodeAt()](#string-charcodeat)**：返回指定位置字符的Unicode编码
- **[concat()](#string-concat)**：连接两个或多个字符串
- **[slice()](#string-slice)**：提取字符串的片段
- **[substring()](#string-substring)**：提取字符串中介于两个指定下标之间的字符
- **[substr()](#string-substr)**：从起始索引号提取字符串中指定数目的字符
- **[split()](#string-split)**：把字符串分割为字符串数组

### 2. 字符串搜索方法：

- **[indexOf()](#string-indexof)**：返回某个指定的字符串值在字符串中首次出现的位置
- **[lastIndexOf()](#string-lastindexof)**：从后向前搜索字符串
- **[search()](#string-search)**：检索与正则表达式相匹配的值
- **[match()](#string-match)**：找到一个或多个正则表达式的匹配
- **[includes()](#string-includes)**：判断字符串是否包含指定的子字符串
- **[startsWith()](#string-startswith)**：判断字符串是否以指定的子字符串开头
- **[endsWith()](#string-endswith)**：判断字符串是否以指定的子字符串结尾

### 3. 字符串修改方法：

- **[replace()](#string-replace)**：替换与正则表达式匹配的子串
- **[replaceAll()](#string-replaceall)**：替换所有匹配的子串
- **[toLowerCase()](#string-tolowercase)**：把字符串转换为小写
- **[toUpperCase()](#string-touppercase)**：把字符串转换为大写
- **[trim()](#string-trim)**：去除字符串两端的空白字符
- **[trimStart()/trimLeft()](#string-trimstart)**：去除字符串开头的空白字符
- **[trimEnd()/trimRight()](#string-trimend)**：去除字符串结尾的空白字符
- **[padStart()](#string-padstart)**：在开头填充字符串
- **[padEnd()](#string-padend)**：在结尾填充字符串

### 4. 其他方法：

- **[length](#string-length)**：返回字符串的长度
- **[repeat()](#string-repeat)**：返回指定次数的字符串副本
- **[localeCompare()](#string-localecompare)**：用本地特定的顺序来比较两个字符串

# JavaScript字符串方法详解

### 1. String.prototype.charAt() {#string-charat}

```js
let str = "Hello World";
let char = str.charAt(1);
console.log(char); // "e"
```

1. `charAt()` 方法返回字符串中指定位置的字符
2. 位置从0开始计数
3. 如果位置超出字符串长度，返回空字符串

### 2. String.prototype.charCodeAt() {#string-charcodeat}

```js
let str = "Hello";
let code = str.charCodeAt(1);
console.log(code); // 101
```

1. `charCodeAt()` 方法返回指定位置字符的Unicode编码
2. 返回值是0-65535之间的整数
3. 如果位置超出字符串长度，返回NaN
   
### 3. String.prototype.concat() {#string-concat}

```js
let str1 = "Hello";
let str2 = "World";
let result = str1.concat(" ", str2);
console.log(result); // "Hello World"
```
1. `concat()` 方法连接两个或多个字符串
2. 不会修改原字符串，返回新字符串
3. 性能通常不如使用 `+` 或 `+=` 操作符

### 4. String.prototype.slice() {#string-slice}

```js
let str = "Hello World";
let result = str.slice(0, 5);
console.log(result); // "Hello"
```

1. `slice()` 方法提取字符串的某个部分
2. 第一个参数是开始位置，第二个参数是结束位置（不包括）
3. 支持负数索引（从末尾开始计算）

### 5. String.prototype.substring() {#string-substring}

```js
let str = "Hello World";
let result = str.substring(0, 5);
console.log(result); // "Hello"
```

1. `substring()` 方法提取字符串中介于两个指定下标之间的字符
2. 如果开始位置大于结束位置，会自动交换参数
3. 不支持负数索引

### 6. String.prototype.substr() {#string-substr}

```js
let str = "Hello World";
let result = str.substr(6, 5);
console.log(result); // "World"
```

1. `substr()` 方法从起始索引号提取字符串中指定数目的字符
2. 第一个参数是开始位置，第二个参数是要提取的字符数
3. 注意：该方法已不被推荐使用，建议使用 `slice()` 或 `substring()`

### 7. String.prototype.split() {#string-split}

```js
let str = "Hello World";
let arr = str.split(" ");
console.log(arr); // ["Hello", "World"]
```

1. `split()` 方法把字符串分割为字符串数组
2. 第一个参数是分隔符，可以是字符串或正则表达式
3. 第二个参数可选，指定返回数组的最大长度

### 8. String.prototype.indexOf() {#string-indexof}

```js
let str = "Hello World";
let position = str.indexOf("o");
console.log(position); // 4
```

1. `indexOf()` 方法返回某个指定的字符串值在字符串中首次出现的位置
2. 如果没有找到，返回-1
3. 第二个参数可选，指定开始搜索的位置

### 9. String.prototype.lastIndexOf() {#string-lastindexof}

```js
let str = "Hello World";
let position = str.lastIndexOf("o");
console.log(position); // 7
```

1. `lastIndexOf()` 方法从后向前搜索字符串
2. 返回指定文本最后一次出现的索引
3. 第二个参数可选，指定开始搜索的位置

### 10. String.prototype.search() {#string-search}

```js
let str = "Hello World";
let position = str.search(/World/);
console.log(position); // 6
```

1. `search()` 方法检索字符串中指定的子字符串或正则表达式匹配
2. 返回第一个匹配的位置，如果没有找到返回-1
3. 总是从字符串开头开始查找

### 11. String.prototype.match() {#string-match}

```js
let str = "The rain in SPAIN stays mainly in the plain";
let result = str.match(/ain/gi);
console.log(result); // ["ain", "AIN", "ain", "ain"]
```

1. `match()` 方法找到一个或多个正则表达式的匹配
2. 返回匹配结果的数组，如果没有匹配返回null
3. 使用 `g` 标志获取所有匹配，否则只返回第一个匹配

### 12. String.prototype.includes() {#string-includes}

```
let str = "Hello World";
let result = str.includes("World");
console.log(result); // true
```

1. `includes()`方法判断字符串是否包含指定的子字符串
2. 返回布尔值
3. 第二个参数可选，指定开始搜索的位置

### 13. String.prototype.startsWith() {#string-startswith}

```
let str = "Hello World";
let result = str.startsWith("Hello");
console.log(result); // true
```

1. `startsWith()`方法判断字符串是否以指定的子字符串开头
2. 返回布尔值
3. 第二个参数可选，指定开始搜索的位置

### 14. String.prototype.endsWith() {#string-endswith}

```
let str = "Hello World";
let result = str.endsWith("World");
console.log(result); // true
```

1. `endsWith()`方法判断字符串是否以指定的子字符串结尾
2. 返回布尔值
3. 第二个参数可选，指定要搜索的字符串长度

### 15. String.prototype.replace() {#string-replace}

```
let str = "Hello World";
let result = str.replace("World", "JavaScript");
console.log(result); // "Hello JavaScript"
```

1. `replace()`方法替换字符串中的文本
2. 第一个参数可以是字符串或正则表达式
3. 第二个参数是替换文本或函数
4. 只替换第一个匹配项（除非使用全局正则表达式）


✅ 为什么写成 (_, c)？

```js
function (_, c) { return c ? c.toUpperCase() : ''; }
```



```js
'John-Doe-30'.replace(/-(\w)-(\w)/g, function(match, p1, p2) {
  console.log(match); // '-D-3'
  console.log(p1);    // 'D'
  console.log(p2);    // '3'
  return p1 + p2;     // 返回 'D3'
});
// 结果：'JohnD30'
```


### 16. String.prototype.replaceAll() {#string-replaceall}

```
let str = "Hello World World";
let result = str.replaceAll("World", "JavaScript");
console.log(result); // "Hello JavaScript JavaScript"
```

1. `replaceAll()`方法替换所有匹配的子字符串
2. 第一个参数可以是字符串或全局正则表达式
3. 第二个参数是替换文本或函数

### 17. String.prototype.toLowerCase() {#string-tolowercase}

```
let str = "Hello World";
let result = str.toLowerCase();
console.log(result); // "hello world"
```

1. `toLowerCase()`方法把字符串转换为小写
2. 返回新字符串，不修改原字符串

### 18. String.prototype.toUpperCase() {#string-touppercase}

```
let str = "Hello World";
let result = str.toUpperCase();
console.log(result); // "HELLO WORLD"
```

1. `toUpperCase()`方法把字符串转换为大写
2. 返回新字符串，不修改原字符串

### 19. String.prototype.trim() {#string-trim}

```
let str = "   Hello World   ";
let result = str.trim();
console.log(result); // "Hello World"
```

1. `trim()`方法去除字符串两端的空白字符
2. 空白字符包括空格、制表符、换行符等
3. 返回新字符串，不修改原字符串

### 20. String.prototype.trimStart() / trimLeft() {#string-trimstart}

```
let str = "   Hello World   ";
let result = str.trimStart();
console.log(result); // "Hello World   "
```

1. `trimStart()`和 `trimLeft()`方法去除字符串开头的空白字符
2. 两个方法功能相同，`trimLeft()`是别名
3. 返回新字符串，不修改原字符串

### 21. String.prototype.trimEnd() / trimRight() {#string-trimend}

```
let str = "   Hello World   ";
let result = str.trimEnd();
console.log(result); // "   Hello World"
```

1. `trimEnd()`和 `trimRight()`方法去除字符串结尾的空白字符
2. 两个方法功能相同，`trimRight()`是别名
3. 返回新字符串，不修改原字符串

### 22. String.prototype.padStart() {#string-padstart}

```
let str = "5";
let result = str.padStart(4, "0");
console.log(result); // "0005"
```

1. `padStart()`方法用另一个字符串填充当前字符串
2. 第一个参数是目标长度，第二个参数是填充字符串
3. 从开头开始填充

### 23. String.prototype.padEnd() {#string-padend}

```
let str = "5";
let result = str.padEnd(4, "0");
console.log(result); // "5000"
```

1. `padEnd()`方法用另一个字符串填充当前字符串
2. 第一个参数是目标长度，第二个参数是填充字符串
3. 从结尾开始填充

### 24. String.prototype.length {#string-length}

```
let str = "Hello";
let len = str.length;
console.log(len); // 5
```

1. `length`属性返回字符串的长度
2. 这是属性而不是方法，不需要括号
3. 返回字符串中的字符数（包括空格和特殊字符）

### 25. String.prototype.repeat() {#string-repeat}

```
let str = "Hello";
let result = str.repeat(3);
console.log(result); // "HelloHelloHello"
```

1. `repeat()`方法返回指定次数的字符串副本
2. 参数是重复的次数（0到无穷大之间的整数）
3. 如果参数为0，返回空字符串

### 26. String.prototype.localeCompare() {#string-localecompare}

```
let str1 = "a";
let str2 = "b";
let result = str1.localeCompare(str2);
console.log(result); // -1 (表示str1在str2之前)
```

1. `localeCompare()`方法用本地特定的顺序来比较两个字符串
2. 返回数字：负数（前小后大）、0（相等）、正数（前大后小）
3. 考虑语言特定的排序规则


## 字符串应用实例 {#string-example}

### 字符串反转

```
let str = "Hello World";
let reversed = str.split("").reverse().join("");
console.log(reversed); // "dlroW olleH"
```

### 检查回文字符串

```
function isPalindrome(str) {
    let cleaned = str.toLowerCase().replace(/[^a-z0-9]/g, "");
    return cleaned === cleaned.split("").reverse().join("");
}

console.log(isPalindrome("A man, a plan, a canal: Panama")); // true
```

### 首字母大写

```
function capitalizeWords(str) {
    return str.toLowerCase().split(" ").map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(" ");
}

console.log(capitalizeWords("hello world")); // "Hello World"
```

### 统计字符出现次数

```
function countChars(str, char) {
    return str.split("").filter(c => c === char).length;
}

console.log(countChars("Hello World", "l")); // 3
```

### 模板字符串（ES6特性）

```
let name = "John";
let age = 30;
let message = `My name is ${name} and I am ${age} years old.`;
console.log(message); // "My name is John and I am 30 years old."
```

这些字符串方法涵盖了JavaScript中字符串操作的大部分需求，熟练掌握这些方法可以大大提高字符串处理的效率和代码质量。
































