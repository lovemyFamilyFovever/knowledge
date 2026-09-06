---
outline: [1,3]
head:
  - - meta
    - name: description
      content: JavaScript数组方法介绍
  - - meta
    - name: keywords
      content: JavaScript 数组 方法 前端开发 前端框架 前端工程师
tags: [JavaScript, Array]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/javascript/Array.md"
---

# 总览

[数组应用实例](#array-example)

[Array树形图知识图谱](#array-pic)

### 1. 改变原数组的方法：(刚好是Vue劫持重写的几个array的方法，因为他们会改变原数组)

- **[push()](#array-push)**：在数组的末尾添加一个或多个元素，并返回新的长度。
- **[pop()](#array-pop)**：移除数组的最后一个元素，并返回那个元素。
- **[shift()](#array-shift)**：移除数组的第一个元素，并返回那个元素。
- **[unshift()](#array-unshift)**：在数组的开头添加一个或多个元素，并返回新的长度。
- **[splice()](#array-splice)**：通过删除、替换或添加新元素来改变数组的内容。
- **[sort()](#array-sort)**：对数组元素进行排序。
- **[reverse()](#array-reverse)**：颠倒数组中元素的顺序。

### 2. 不改变原数组的方法：

- **[slice()](#array-slice)**：返回数组的一个片段或子数组。
- **[concat()](#array-concat)**：合并两个或多个数组，并返回一个新的数组。
- **[join()](#array-join)**：将数组的所有元素连接成一个字符串。
- **[indexOf()](#array-indexof)**：返回数组中首次出现指定元素的索引，如果不存在则返回-1。
- **[lastIndexOf()](#array-lastindexof)**：返回数组中最后出现指定元素的索引，如果不存在则返回-1。
- **[includes()](#array-includes)**：判断数组是否包含某个指定的值，根据情况返回 true 或 false。
- **[forEach()](#array-foreach)**：对数组的每个元素执行一次提供的函数。
- **[map()](#array-map)**：创建一个新数组，其结果是该数组中的每个元素都调用一次提供的函数后的返回值。
- **[filter()](#array-filter)**：创建一个新数组，包含通过所提供函数实现的测试的所有元素。
- **[reduce()](#array-reduce)**：将数组中的每个元素按顺序执行一个由您提供的reducer函数(升序执行)，将其结果汇总为单个返回值。
- **[reduceRight()](#array-reduceright)**：功能和reduce()类似，但是从数组的末尾开始累加。
- **[find()](#array-find)**：返回数组中满足提供的测试函数的第一个元素的值，否则返回undefined。
- **[findIndex()](#array-findindex)**：返回数组中满足提供的测试函数的第一个元素的索引，否则返回-1。
- **[fill()](#array-fill)**：用一个值填充数组中从起始索引到终止索引内的元素。
- **[some()](#array-some)**：测试数组中是否至少有一个元素通过了被提供的函数测试。
- **[every()](#array-every)**：测试数组中是否所有元素都通过了被提供的函数测试。

这些方法涵盖了大部分数组操作的需求，合理使用这些方法可以使你的代码更加简洁和高效。需要注意的是，这些方法不会改变原始数组，而是返回一个新的数组。`forEach`方法本身不会改变原始数组, 除非它的回调函数修改了数组。

# JavaScript数组方法 

### 1. Array.prototype.push() {#array-push}

```javascript
let arr = [1, 2, 3];
arr.push(4);
console.log(arr); // [1, 2, 3, 4]
```

1. `push()` 方法用于在数组的末尾添加一个或多个元素，并返回数组的新长度。
2. 该方法可以接受多个参数，每个参数都会被添加到数组末尾。


### 2. Array.prototype.pop(){#array-pop}

```javascript
let arr = [1, 2, 3];
arr.pop();
console.log(arr); // [1, 2]
```

1. `pop()` 方法用于删除数组的最后一个元素，并返回该元素的值。
2. 如果数组为空，则返回 `undefined`。


### 3. Array.prototype.shift(){#array-shift}

```javascript
let arr = [1, 2, 3];
arr.shift();
console.log(arr); // [2, 3]
```

1. `shift()` 方法用于删除数组的第一个元素，并返回该元素的值。
2. 如果数组为空，则返回 `undefined`。


### 4. Array.prototype.unshift(){#array-unshift}

```javascript
let arr = [1, 2, 3];
arr.unshift(0);
console.log(arr); // [0, 1, 2, 3]
```

1. `unshift()` 方法用于在数组的开头添加一个或多个元素，并返回数组的新长度。
2. 该方法可以接受多个参数，每个参数都会被添加到数组开头。


### 5. Array.prototype.splice(){#array-splice}

```javascript
let arr = [1, 2, 3, 4, 5];
arr.splice(2, 0, 6, 7);
console.log(arr); // [1, 2, 6, 7, 3, 4, 5]
```

1. `splice()` 方法用于删除原数组的一部分元素，并/或用新的元素替换被删除的元素，并返回被删除的元素。
2. 第一个参数指定了插入位置，第二个参数指定了要删除的元素个数，第三个参数及以后的参数指定了要插入的元素。
3. 如果只指定第一个参数，则删除数组中从指定位置开始到末尾的所有元素。
4. 如果只指定第二个参数，则删除数组中从开头到指定位置的所有元素。
5. 如果指定第三个参数，则插入数组中指定位置的元素。
6. 如果没有指定第三个参数，则只删除数组中指定位置的元素。
7. 返回值是一个包含被删除元素的数组。


### 6. Array.prototype.concat(){#array-concat}

```javascript
let arr1 = [1, 2, 3];
let arr2 = [4, 5, 6];
let arr3 = arr1.concat(arr2);
console.log(arr3); // [1, 2, 3, 4, 5, 6]
```

1. `concat()` 方法用于连接两个或多个数组，并返回一个新数组。
2. 该方法不会修改原数组，而是返回一个新数组。
3. 该方法可以接受多个参数，每个参数都会被添加到数组末尾。
4. 如果参数是数组，则会被直接添加到结果数组中。
5. 如果参数不是数组，则会被转换成字符串，然后再添加到结果数组中。


### 7. Array.prototype.slice(){#array-slice}

```javascript
let arr = [1, 2, 3, 4, 5];
let newArr = arr.slice(2, 4);
console.log(newArr); // [3, 4]
```
1. `slice()` 方法用于从数组中返回一个新的数组，包含从开始索引到结束索引（不包括结束索引）的所有元素。
2. 该方法不会修改原数组，而是返回一个新数组。
3. 第一个参数指定了开始索引，第二个参数指定了结束索引。
4. 如果省略第二个参数，则返回从开始索引到数组末尾的所有元素。
5. 如果开始索引大于或等于数组长度，则返回一个空数组。
6. 如果结束索引大于数组长度，则使用数组长度作为结束索引。


### 8. Array.prototype.map(){#array-map}

```javascript
let arr = [1, 2, 3, 4, 5];
let newArr = arr.map(v => v * 2);
console.log(newArr); // [2, 4, 6, 8, 10]
```

1. `map()` 方法创建一个新数组，其结果是该数组中的每个元素都调用一次提供的函数后返回的结果。
2. 该方法不会修改原数组，而是返回一个新数组。
3. 该方法接受一个函数作为参数，该函数将为每个元素调用一次。
4. 函数参数有三个：当前元素、当前索引、原数组。
5. 函数返回值会被添加到新数组中。


### 9. Array.prototype.filter(){#array-filter}

```javascript
let arr = [1, 2, 3, 4, 5];
let newArr = arr.filter(v => v > 3);
console.log(newArr); // [4, 5]
```

1. `filter()` 方法创建一个新数组，其包含通过所提供的函数实现的测试的所有元素。
2. 该方法不会修改原数组，而是返回一个新数组。
3. 该方法接受一个函数作为参数，该函数将为每个元素调用一次。
4. 函数参数有三个：当前元素、当前索引、原数组。
5. 函数返回值为 `true` 的元素会被添加到新数组中。


### 10. Array.prototype.reduce(){#array-reduce}

```javascript
let arr = [1, 2, 3, 4, 5];
let sum = arr.reduce((acc, cur) => acc + cur, 0);
console.log(sum); // 15
```

1. `reduce()` 方法对数组中的每个元素执行一个由您提供的reducer函数，将其结果汇总为单个返回值。
2. 该方法不会修改原数组，而是返回一个新数组。
3. 该方法接受一个函数作为参数，该函数将为每个元素调用一次。
4. 函数参数有四个：前一个值、当前元素、当前索引、原数组。
5. 函数返回值会被用作下一次迭代的第一个参数。
6. 如果没有初始值，则将使用数组中的第一个元素。
7. 如果数组为空，则返回 `undefined`。


### 11. Array.prototype.forEach(){#array-foreach}

```javascript
let arr = [1, 2, 3, 4, 5];
arr.forEach(v => console.log(v));
```

1. `forEach()` 方法为数组中的每个元素执行一次提供的函数。
2. 该方法不会返回任何值。
3. 该方法接受一个函数作为参数，该函数将为每个元素调用一次。
4. 函数参数有三个：当前元素、当前索引、原数组。
5. 如果数组为空，则不会执行任何操作。
   

### 12. Array.prototype.some(){#array-some}

```javascript
let arr = [1, 2, 3, 4, 5];
let hasEven = arr.some(v => v % 2 === 0);
console.log(hasEven); // true
```

1. `some()` 方法测试数组中是否至少有一个元素通过了被提供的函数测试。
2. 该方法接受一个函数作为参数，该函数将为每个元素调用一次。
3. 函数参数有三个：当前元素、当前索引、原数组。
4. 函数返回值为 `true` 的元素会停止执行，并返回 `true`。
5. 如果没有元素通过测试，则返回 `false`。


### 13. Array.prototype.every(){#array-every}

```javascript
let arr = [1, 2, 3, 4, 5];
let allEven = arr.every(v => v % 2 === 0);
console.log(allEven); // false
```

1. `every()` 方法测试数组中是否所有元素都通过了被提供的函数测试。
2. 该方法接受一个函数作为参数，该函数将为每个元素调用一次。
3. 函数参数有三个：当前元素、当前索引、原数组。
4. 函数返回值为 `true` 的元素会继续执行，直到所有元素都通过测试。
5. 如果有一个元素未通过测试，则返回 `false`。


### 14. Array.prototype.sort(){#array-sort}

```javascript
let arr = [5, 3, 1, 4, 2];
arr.sort((a, b) => a - b);
console.log(arr); // [1, 2, 3, 4, 5]
```

1. `sort()` 方法对数组中的元素进行排序，并返回排序后的数组。
2. 该方法不会修改原数组，而是返回一个新数组。
3. 该方法可以接受一个比较函数作为参数，该函数用于指定元素的排序顺序。
4. 如果省略比较函数，则使用默认排序顺序。
5. 默认排序顺序是按照字符串的 Unicode 位序进行排序。
6. 如果数组包含非字符串值，则会先进行类型转换，再进行排序。
7. 如果数组包含 NaN 值，则会被排在所有其他值之前。
8. 如果数组包含 undefined 值，则会被排在所有其他值之前。
   

### 15. Array.prototype.reverse(){#array-reverse}

```javascript
let arr = [1, 2, 3, 4, 5];
arr.reverse();
console.log(arr); // [5, 4, 3, 2, 1]
```

1. `reverse()` 方法将数组中的元素反转，并返回反转后的数组。
2. 该方法不会修改原数组，而是返回一个新数组。
   
### 16. Array.prototype.find() {#array-find}

```javascript
let arr = [1, 2, 3, 4, 5];
let found = arr.find(v => v > 3);
console.log(found); // 4
```

1. `find()` 方法返回数组中满足提供的测试函数的第一个元素的值。
2. 该方法不会修改原数组，而是返回一个新数组。
3. 该方法接受一个函数作为参数，该函数将为每个元素调用一次。
4. 函数参数有三个：当前元素、当前索引、原数组。
5. 函数返回值为 `true` 的元素会停止执行，并返回该元素的值。
6. 如果没有元素通过测试，则返回 `undefined`。


### 17. Array.prototype.findIndex() {#array-findindex}

```javascript
let arr = [1, 2, 3, 4, 5];
let index = arr.findIndex(v => v > 3);
console.log(index); // 3
```

1. `findIndex()` 方法返回数组中满足提供的测试函数的第一个元素的索引。
2. 该方法不会修改原数组，而是返回一个新数组。
3. 该方法接受一个函数作为参数，该函数将为每个元素调用一次。
4. 函数参数有三个：当前元素、当前索引、原数组。
5. 函数返回值为 `true` 的元素会停止执行，并返回该元素的索引。
6. 如果没有元素通过测试，则返回 `-1`。
7. 该方法与 `find()` 方法的区别在于，`findIndex()` 方法返回的是索引，而 `find()` 方法返回的是值。


### 18. Array.prototype.fill() {#array-fill}

```javascript
let arr = [1, 2, 3, 4, 5];
arr.fill(0, 1, 3);
console.log(arr); // [1, 0, 0, 4, 5]
```

1. `fill()` 方法用一个值，填充一个数组中从起始索引到终止索引内的元素。
2. 该方法不会修改原数组，而是返回一个新数组。
3. 该方法接受三个参数：一个值、起始索引（可选）、终止索引（可选）。
4. 如果省略起始索引，则从 0 开始填充。
5. 如果省略终止索引，则填充到数组末尾。
6. 如果起始索引大于或等于数组长度，则返回原数组。
7. 如果终止索引大于数组长度，则使用数组长度作为终止索引。


### 19. Array.prototype.includes() {#array-includes}

```javascript
let arr = [1, 2, 3, 4, 5];
let hasThree = arr.includes(3);
console.log(hasThree); // true
```

1. `includes()` 方法用来判断一个数组是否包含一个指定的值，根据情况返回 `true` 或 `false`。
2. 该方法不会修改原数组，而是返回一个布尔值。
3. 该方法可以接受两个参数：要查找的值和（可选）从索引位置开始查找的索引。
4. 如果没有指定索引，则从数组的头部开始查找。
5. 如果没有找到指定的值，则返回 `false`。

### 20. Array.prototype.lastIndexOf() {#array-lastindexof}

```javascript
let arr = [1, 2, 3, 4, 5];
let lastIndex = arr.lastIndexOf(3);
console.log(lastIndex); // 2
```

1. `lastIndexOf()` 方法返回数组中lastIndexOf指定元素的索引，如果不存在则返回-1。
2. 该方法不会修改原数组，而是返回一个索引值。
3. 该方法可以接受两个参数：要查找的值和（可选）从索引位置开始查找的索引。
4. 如果没有指定索引，则从数组的末尾开始查找。
5. 如果没有找到指定的值，则返回 `-1`。

### 21. Array.prototype.join() {#array-join}

```javascript
let arr = [1, 2, 3, 4, 5];
let str = arr.join('-');
console.log(str); // "1-2-3-4-5"
```

1. `join()` 方法将数组中的所有元素转换为字符串，并返回连接后的字符串。
2. 该方法不会修改原数组，而是返回一个字符串。
3. 该方法可以接受一个参数，用于指定分隔符。
4. 如果省略参数，则使用逗号作为分隔符。
5. 如果数组为空，则返回空字符串。

### 22. Array.prototype.indexOf() {#array-indexof}

```javascript
let arr = [1, 2, 3, 4, 5];
let index = arr.indexOf(3);
console.log(index); // 2
```

1. `indexOf()` 方法返回数组中第一个指定元素的索引，如果不存在则返回-1。
2. 该方法不会修改原数组，而是返回一个索引值。
3. 该方法可以接受两个参数：要查找的值和（可选）从索引位置开始查找的索引。
4. 如果没有指定索引，则从数组的头部开始查找。
5. 如果没有找到指定的值，则返回 `-1`。

### 23. Array.prototype.reduceRight() {#array-reduceright}

```javascript
let arr = [1, 2, 3, 4, 5];
let sum = arr.reduceRight((acc, cur) => acc + cur, 0);
console.log(sum); // 15
```

1. `reduceRight()` 方法与 `reduce()` 方法类似，但它是从右到左执行。
2. 该方法不会修改原数组，而是返回一个新数组。
3. 该方法接受一个函数作为参数，该函数将为每个元素调用一次。
4. 函数参数有四个：前一个值、当前元素、当前索引、原数组。
5. 函数返回值会被用作下一次迭代的第一个参数。
6. 如果没有初始值，则将使用数组中的第一个元素。
7. 如果数组为空，则返回 `undefined`。

### 24. Array.isArray() {#array-isarray}

```javascript
let arr = [1, 2, 3];
let isArr = Array.isArray(arr);
console.log(isArr); // true
``` 

1. `isArray()` 方法用来判断一个值是否为数组。
2. 该方法返回一个布尔值。


### 25. Array.from() {#array-from}

```javascript
let arr = Array.from([1, 2, 3]);
console.log(arr); // [1, 2, 3]
```

1. `from()` 方法将类似数组或可迭代对象转换为数组。
2. 该方法返回一个新数组。
3. 该方法可以接受两个参数：一个类似数组或可迭代对象，和一个映射函数（可选）。
4. 如果映射函数为 `undefined`，则返回原数组。
5. 如果映射函数为 `null`，则返回原数组。
6. 如果映射函数为函数，则返回映射后的数组。


### 26. Array.of()  {#array-of}

```javascript
let arr = Array.of(1, 2, 3);
console.log(arr); // [1, 2, 3]
```

1. `of()` 方法创建一个具有可变数量参数的新数组实例，并返回该实例。
2. 该方法返回一个新数组。
3. 该方法可以接受任意数量的参数。

## Array树形图知识图谱  {#array-pic}
![array](./MindMap/imgs/jsArray.jpg) 

## 数组应用实例  {#array-example}

### 数组去重

```javascript
let arr = [1, 2, 3, 2, 1, 4, 5, 4];
let result=new Set(arr);//利用Set去重
let newArr = [...result];//利用展开运算符转换Set为数组
console.log(newArr); // [1, 2, 3, 4, 5]
```
