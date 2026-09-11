---
outline: [2,3]
head:
  - - meta
    - name: description
      content: JavaScript 前端开发教程
  - - meta
    - name: keywords
      content: JavaScript 前端开发 前端框架 前端工程师
tags: [JavaScript]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/javascript/instanceof-static-super.md"
---



## instanceof 

> instanceof是一个操作符，用于测试构造函数的prototype属性是否出现在对象的原型链中的任何位置。

- 简单来说：`instanceof`可以用来判断一个**对象**是否是某个构造函数的实例。

```javascript
let obj = new Object();
console.log(obj instanceof Object); // true
```

错误示例：

```javascript
1 instaceof Number; // 错误，instanceof只能用于对象，不能用于数字
```

- 对于原始数据类型（如Number、String、Boolean等），instanceof操作符并不适用，因为原始数据类型不是对象，它们没有原型链。[哪些数据没有原型链？](#prototype-chain-of-primitive-data-types)
- instanceof操作符检查的是对象的原型链，而不是原始值的类型。
  
如果你想要检查一个值是否为数字类型，你可以使用typeof操作符：
```javascript
typeof 123 === 'number'; // true
```
如果你确实需要使用instanceof来检查一个对象是否为Number的实例，你需要首先将原始值包装成一个对象，这可以通过调用构造函数来实现：
```javascript
Number.prototype.isPrototypeOf(new Number(123)); // true
new Number(1) instanceof Number
```

## 哪些原始数据没有原型链？  {#prototype-chain-of-primitive-data-types}

在JavaScript中，只有对象（包括数组和函数）才有原型链。原始数据类型不继承自任何对象，也没有方法，尽管它们可以调用一些看起来像方法的东西（如`'string'.toUpperCase()`），这是通过**装箱**操作实现的，即临时将原始数据类型转换为对应的对象类型（如`String`对象），执行方法后，再转换回原始数据类型。

原始数据类型没有原型链的原因有以下几点：

1. *原始数据类型没有自己的属性和方法，不能添加属性和方法。*
2. *原始数据类型没有自己的原型，不能继承属性和方法。*
3. *原始数据类型没有自己的构造函数，不能使用`new`操作符创建对象。*
4. *原始数据类型没有自己的原型链，不能使用`instanceof`操作符。*

**因此，在JavaScript中，只有对象才有原型链，原始数据类型没有原型链。**

需要注意的是，尽管原始数据类型没有原型链，但它们的包装对象（如`String`、`Number`、`Boolean`等）是对象，因此有原型链。例如，`new String('hello')`创建的是一个字符串对象，它是有原型链的，并且是`String`构造函数的实例。

1. Undefined: 表示未定义的值，例如变量声明但未初始化时的值。
2. Null: 表示空值或不存在对象的引用。
3. Boolean: 表示逻辑实体，有两个值true和false。
4. Number: 表示整数和浮点数。
5. String: 表示字符串，即一串字符序列。
6. Symbol (ES6新增): 表示唯一的、不可变的数据类型，主要用于对象属性的键。

## javascript中的static静态类

1. 静态类：在JavaScript中，静态类是指没有实例的类，也就是说，静态类不能被实例化，只能被调用。静态类可以包含静态方法和静态属性。

```javascript
// 静态类
class Person {
  static sayHello() {
    console.log('Hello, I am a static method.');
  }
}

// 调用静态方法
Person.sayHello(); // Hello, I am a static method.

let person = new Person(); 
// 错误：实例不能调用静态方法
person.sayHello(); // Uncaught TypeError: person.sayHello is not a function     

```

2. 静态类可以包含静态方法和静态属性。

```javascript
// 静态类
class Person {
  static name = 'Person';
  static sayHello() {
    console.log('Hello, I am a static method.');
  }
}

// 调用静态属性
console.log(Person.name); // Person

// 调用静态方法
Person.sayHello(); // Hello, I am a static method.
```

## super关键字

`super`关键字在JavaScript中是一个特殊的关键字，它可以用来访问父类的属性和方法。`super`主要用于继承和构造函数中。

### 构造函数中的super

```javascript
// 父类
class Animal {
  constructor(name) {
    this.name = name;
  }
  eat() {
    console.log(`${this.name} is eating.`);
  }
}

// 子类
class Dog extends Animal {
  constructor(name, breed) {
    super(name); // 调用父类的【构造函数】
    this.breed = breed;
  }
  bark() {
    console.log(`${this.name} is barking.`);
  }
}

// 实例化子类
let myDog = new Dog('Buddy', 'Labrador');

// 调用父类方法
myDog.eat(); // Buddy is eating.

// 调用子类方法
myDog.bark(); // Buddy is barking.
```

### 方法中的super

```javascript
class Parent {
  parentMethod() {
    console.log('Parent method');
  }
}

class Child extends Parent {
  childMethod() {
    super.parentMethod(); // 调用父类的 parentMethod 方法
    console.log('Child method');
  }
}

const child = new Child();
child.childMethod(); // 输出: Parent method, Child method
```

- 在这个例子中，`Child`类的`childMethod`方法调用了`super.parentMethod()`来调用父类的`parentMethod`方法。

### 静态方法中的super

- 在静态方法中，`super`仍然可以用来调用父类的静态方法。

```javascript
class Parent {
  static parentMethod() {
    console.log('Parent static method');
  }
}


class Child extends Parent {
  static childMethod() {
    super.parentMethod(); // 调用父类的 parentMethod 方法
    console.log('Child static method');
  }
}


Child.childMethod(); // 输出: Parent static method, Child static method
```

- 在这个例子中，`Child`类的`childMethod`方法调用了`super.parentMethod()`来调用父类的`parentMethod`方法。
  