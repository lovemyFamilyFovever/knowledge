---
outline: [2,3]
head:
  - - meta
    - name: description
      content: 什么是深拷贝？什么是浅拷贝？如何实现一个深拷贝函数？
  - - meta
    - name: keywords
      content: 深拷贝和浅拷贝 前端开发 前端框架 前端工程师
tags: [JavaScript]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/javascript/deep-shallow-copy.md"
---

# 什么是深拷贝？什么是浅拷贝？如何实现一个深拷贝函数？

在JS中，数据类型分为基本数据类型和引用数据类型两种，对于基本数据类型来说，它的值直接存储在栈内存中，而对于引用类型来说，它在栈内存中仅仅存储了一个引用，而真正的数据存储在堆内存中

当我们对数据进行操作的时候，会发生两种情况

## 一、基本数据类型

```JavaScript
var a = 3;
var b = a;
b = 5;
console.log(a); // 3
console.log(b); // 5
```

以上代码说明两个变量都使用的是独立的数据。

**对于基本数据类型来说，不存在深拷贝和浅拷贝的说法，因为赋值直接就是深拷贝。**

**而深拷贝和浅拷贝都是针对于<font color="#f00">引用类型(Object)</font>的**

## 二、引用数据类型

```JavaScript
var obj1 = {
    a:  1,
    b:  2,
    c:  3
}
var obj2 = obj1;
obj2.a = 5;
console.log(obj1.a);  // 5
console.log(obj2.a);  // 5
```

可以看到的是，两个对象的值全部被修改了

对象是引用类型的值，对于引用类型来说，我们将 obj1 赋予 obj2 的时候，我们其实仅仅只是将 obj1 存储在栈堆中的的引用赋予了 obj2 ，而两个对象此时指向的是在堆内存中的同一个数据，所以当我们修改任意一个值的时候，修改的都是堆内存中的数据，而不是引用，所以只要修改了，同样引用的对象的值也自然而然的发生了改变。

其实，上面的例子就是一个简单的浅拷贝。

### 浅拷贝

> 对于浅拷贝而言，就是只拷贝对象的引用，而不深层次的拷贝对象的值，多个对象指向堆内存中的同一对象，任何一个修改都会使得所有对象的值修改，因为它们公用一条数据。

### 深拷贝

> 深拷贝不会拷贝引用类型的引用，而是将引用类型的值全部拷贝一份，形成一个新的引用类型，这样就不会发生引用错乱的问题，使得我们可以多次使用同样的数据，而不用担心数据之间会起冲突。

我们在实际的项目中，肯定不能让每个对象的值都指向同一个堆内存，这样的话不便于我们做操作，所以自然而然的诞生了深拷贝。

### 深拷贝的实现

# 1、对象

#### 1. JSON.stringify() 、 JSON.parse()

*   是否支持深拷贝多层引用类型嵌套：支持
*   **不可以拷贝 undefined ， function， RegExp 等类型的数据**

```JavaScript
var obj1 = {
    a: 1,
    b: 2,
    c: 3
}
var obj2 = JSON.parse(JSON.stringify(obj1));
obj2.a = 5;
console.log(obj1.a);  // 1
console.log(obj2.a); // 5
```

#### 2. 展开运算符...

*   是否支持深拷贝多层引用类型嵌套：不支持

```JavaScript
let obj1 = {
  a: 'a',
  b: 'b'
};
// 第二种方式
let obj2 = {...obj1};
obj2.a='z'
console.log(obj2.a); // z
console.log(obj1.a); // a
```

#### 3. Object.assign(target, source)

是否支持深拷贝多层引用类型嵌套：**不支持**
  
```javascript
var obj1 = {
    a: 1,
    b: 2,
    c: 3
}
var obj2 = Object.assign({}, obj1);
obj2.b = 5;
console.log(obj1.b); // 2
console.log(obj2.b); // 5
```

如果是有多层嵌套就失效了

```javascript
var obj1 = {
    a: 1,
    b: 2,
    c: ['a','b','c']
}
var obj2 = Object.assign({}, obj1);
obj2.c[1] = 5;
console.log(obj1.c); // ["a", 5, "c"]
console.log(obj2.c); // ["a", 5, "c"]
```

可以看到如果对象的属性对应的是其它的引用类型的话，还是只拷贝了引用

#### 4. 递归拷贝 - 深拷贝函数

是否支持深拷贝多层引用类型嵌套：**支持**

```javascript
// 定义一个深拷贝函数  接收目标target参数
function deepClone(target) {
    // 定义一个变量
    let result;
    // 如果当前需要深拷贝的是一个对象的话
    if (typeof target === 'object') {
        // 如果是一个数组的话
        if (Array.isArray(target)) {
            result = []; // 将result赋值为一个数组，并且执行遍历
            for (let i in target) {
                // 递归克隆数组中的每一项
                result.push(deepClone(target[i]))
            }
            // 判断如果当前的值是null的话；直接赋值为null
        } else if (target === null) {
            result = null;
            // 判断如果当前的值是一个RegExp对象的话，直接赋值} else if(target.constructor===RegExp){
            result = target;
        } else {
            // 否则是普通对象，直接for in循环，递归赋值对象的所有值
            result = {};
            for (let i in target) {
                result[i] = deepClone(target[i]);
            }
        }
        // 如果不是对象的话，就是基本数据类型，那么直接赋值
    } else {
        result = target;
    }
    // 返回最终结果
    return result;
}
```


```javascript
let obj1 = {
    a: {
        c: /a/,
        d: undefined,
        b: null
    },
    b: function () { console.log(this.a) },
    c: [
        {
            a: 'c',
            b: /b/,
            c: undefined
        },
        'a',
        3
    ]
}
let obj2 = deepClone(obj1);
obj2.c[0].a = '哈哈'

console.log(obj1.c[0].a);  //c
console.log(obj2.c[0].a);  //哈哈/
```

# 2、数组
1. for循环实现数组的深拷贝

```javascript
var arr1 = [1, 2, 3];
var arr2 = [];
for (var i = 0; i < arr1.length; i++) {
    arr2.push(arr1[i]);
}
arr1[0] = 4;
console.log(arr1); //4, 2, 3
console.log(arr2); //1, 2, 3	
```

2.  concat 方法实现数组的深拷贝

    concat() 方法用于连接两个或多个数组。

    该方法不会改变现有的数组，而仅仅会返回被连接数组的一个副本。

```javascript
var arr1 = [1, 2, 3];
var arr2 = arr1.concat();
arr1[0] = 4;
console.log(arr1); //4, 2, 3
console.log(arr2); //1, 2, 3
```

3.  slice 方法实现数组的深拷贝

    slice() 方法可从已有的数组中返回选定的元素。

    arrayObject.slice(start,end)

    该方法返回一个新的数组，包含从 start 到 end （不包括该元素，数学上来讲是左闭右开，即包含左，不含右）的 arrayObject 中的元素。

```javascript
1 var arr1 = [1, 2, 3];
2 var arr2 = arr1.slice(0);
3 arr1[0] = 4;
4 console.log(arr1); //4, 2, 3
5 console.log(arr2); //1, 2, 3
```

4. ES6扩展运算符实现数组的深拷贝

```javascript
1 var arr1 = [1, 2, 3];
2 var [...arr2] = arr1;
3 arr1[0] = 4;
4 console.log(arr1); //4, 2, 3
5 console.log(arr2); //1, 2, 3
```

