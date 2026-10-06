---
outline: [1,3]
head:
  - - meta
    - name: description
      content: TypeScript
  - - meta
    - name: keywords
      content: TypeScript 前端开发 前端框架 前端工程师
tags: [TypeScript]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/TypeScript/index.md"
---

# TypeScript

TypeScript是JavaScript的超集，它可以编译成纯JavaScript代码，并且可以提供静态类型检查，使代码更加可靠。

## 安装TypeScript

TypeScript可以通过npm安装：

```bash
npm install -g typescript
```

## 编译TS文件to JS文件

TypeScript编译器可以编译单个文件或整个项目。

编译单个文件：

```bash
tsc hello.ts
```

# TS类型

| 类型        |      例子      |  描述 |
| :------: | :---------------: | :----------------------------: |
|  number  |    1, -33, 2.5    |            任意数字            |
|  string  | 'hi', "hi", `hi`  |           任意字符串           |
| boolean  |    true、false    |       布尔值true或false        |
|  字面量  |      其本身       |  限制变量的值就是该字面量的值  |
|   any    |         *         |            任意类型            |
| unknown  |         *         |         类型安全的any          |
|   void   | 空值（undefined） |     没有值（或undefined）      |
|  never   |      没有值       |          不能是任何值          |
|  object  |  {name:'孙悟空'}  |          任意的JS对象          |
|  array   |      [1,2,3]      |           任意JS数组           |
|  tuple   |       [4,5]       | 元素，TS新增类型，固定长度数组 |
|   enum   |    `enum{A, B}`   |       枚举，TS中新增类型       |


## 编译类型 

```typescript
// 基本类型
let name: string = "Tom";
let age: number = 25;
let isMarried: boolean = true;
// 数组类型
let fruits: string[] = ["apple", "banana", "orange"];
let numbers: number[] = [1, 2, 3];
// 对象类型
let person: {name: string, age: number} = {name: "Tom", age: 25};
// 函数类型
function greet(name: string): void {
  console.log("Hello, " + name);
}
//接口类型 
interface Person {
  name: string;
  age: number;
  greet(name: string): void;
}
//类类型
class Person {
  name: string;
  age: number;
  constructor(name: string, age: number) {
    this.name = name;
    this.age = age;
  }
  greet(name: string): void {
    console.log("Hello, " + name);
  }
}
let tom = new Person("Tom", 25);
//泛型类型 
function reverse<T>(arr: T[]): T[] {
  return arr.reverse();
}

let fruits = ["apple", "banana", "orange"];
let reversed = reverse(fruits);
```

## 编译声明文件 

TypeScript编译器可以生成声明文件，声明文件可以让TypeScript编译器知道某些变量的类型。

```typescript
// my-declarations.d.ts
declare let name: string;
declare let age: number;
declare let isMarried: boolean;
declare let fruits: string[];
declare let numbers: number[];
declare let person: {name: string, age: number};
declare function greet(name: string): void;
```

# 注意事项
## 任意属性

``` typescript
interface IUser {
    name: string;
    age: number;
    [propName: string]: any;
}

let userObj: IUser = {
    name: "张三",
    age: 25,
    address: "北京市海淀区",
    phone: "13800138000",
    email: "123@qq.com"
}
```

```typescript
interface IUser {
    name: string;
    age: number;
    [propName: string]: number | string;
}
```

**注意：一旦定义了任意属性，那么确定属性和可选属性的类型都必须是它的类型的子集：**

## 只读属性

```typescript
interface IUser {
    readonly id: number;
    name: string;
}
```

## 接口数组

**只要索引的类型是数字时，那么值的类型必须是数字。
```typescript
interface IUser {
    name: string;
    age: number;
}

interface IUsers {
    [index: number]: nmumber | IUser;
}

let users: IUsers = [
    {name: "张三", age: 25},
    {name: "王五", age: 20}
];
```

## 类数组

```typescript
interface IUser {
    name: string;
    age: number;
}

function greet(users: IUser[]): void {
    for (let user of users) {
        console.log("Hello, " + user.name);
    }
}

let users: IUser[] = [
    {name: "张三", age: 25},
    {name: "王五", age: 20}
];

greet(users);
```

## 接口继承 implements

**一个类(`class`)可以实现(`implements`)多个接口(`interface`)，这意味着它必须【满足所有】接口中定义的契约。**

```typescript
interface IAnimal {
    name: string;
    eat(): void;
    sleep(): void;
}

interface ICanEat {
    eat(): void;
    swim(): void;
}

class Dog implements IAnimal, ICanEat {
    name: string;

    constructor(name: string) {
        this.name = name;
    }

    eat(): void {
        console.log(this.name + " is eating");
    }

    sleep(): void {
        console.log(this.name + " is sleeping");
    }

    swim(): void {
        console.log(this.name + " is swimming");
    }
}

let myDog = new Dog("旺财");
myDog.eat();
```

## 类继承 extends

**用于类继承另一个类，一个类只能扩展一个其他类，这意味着它继承了那个类的属性和方法。** 

```typescript
class Animal {
    name: string;

    constructor(name: string) {
        this.name = name;
    }

    eat(): void {
        console.log(this.name + " is eating");
    }
}


class Dog extends Animal {    
    bark(): void {
        console.log(this.name + " is barking");
    }
}

let myDog = new Dog("旺财");
myDog.eat();
myDog.bark();
``` 

## 类型别名

> 类型别名用于给一个类型起一个新名字。这样，你可以在代码中的其他地方使用这个别名来代替原始类型。

```typescript
type Name = string;
type Age = number;

interface IUser {
    name: Name;
    age: Age;
}

let user: IUser = {
    name: "张三",
    age: 25
};
``` 

# Partial类型

> Partial类型是指将所有属性都设置为可选的，即属性的类型可以是任意类型。


```typescript
interface IUser {
    name: string;
    age: number;
    address: string;
}

let user: Partial<IUser> = {
    name: "张三"
};

user.age = 25;
user.address = "北京市海淀区";
``` 

# Readonly类型

> Readonly类型是指将所有属性都设置为只读的，即属性的类型只能是不能被修改的。

```typescript
interface IUser {
    readonly id: number;
    name: string;
}

let user: IUser = {
    id: 1,
    name: "张三"
};

user.id = 2; // error: Cannot assign to 'id' because it is a read-only property.
``` 

# 参考

- [TypeScript 官方文档](https://www.typescriptlang.org/docs/)