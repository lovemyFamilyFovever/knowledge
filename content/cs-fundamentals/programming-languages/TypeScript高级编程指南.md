---
title: "TypeScript高级编程指南"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# TypeScript高级编程指南

# TypeScript 高级编程指南

## 1. 类型系统深入

### 1.1 条件类型
条件类型是TypeScript中一种根据条件选择类型的高级特性，类似于JavaScript中的三元表达式。

```typescript
// 基础语法：T extends U ? X : Y
type IsString<T> = T extends string ? 'yes' : 'no';

type A = IsString<string>;  // 'yes'
type B = IsString<number>;  // 'no'

// 分布式条件类型：当T是联合类型时，条件类型会分布到每个成员上
type ToArray<T> = T extends any ? T[] : never;
type C = ToArray<string | number>;  // string[] | number[]

// 使用infer关键字在条件类型中捕获类型
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : any;
type D = ReturnType<() => string>;  // string

// 条件类型与映射类型结合
type NonNullable<T> = T extends null | undefined ? never : T;
type E = NonNullable<string | null | undefined>;  // string

// 递归条件类型示例：深层嵌套类型提取
type DeepFlatten<T> = T extends object 
  ? { [K in keyof T]: DeepFlatten<T[K]> } 
  : T;
```

### 1.2 映射类型
映射类型允许基于已有类型创建新类型，通过映射每个属性来转换类型。

```typescript
// 基础映射类型语法：{ [K in keyof T]: NewType }
type Readonly<T> = {
  readonly [P in keyof T]: T[P];
};

interface User {
  name: string;
  age: number;
}

type ReadonlyUser = Readonly<User>;
// 等同于
// interface ReadonlyUser {
//   readonly name: string;
//   readonly age: number;
// }

// 带修饰符的映射类型
type Partial<T> = {
  [P in keyof T]?: T[P];
};

type Required<T> = {
  [P in keyof T]-?: T[P];  // -? 移除可选修饰符
};

type Mutable<T> = {
  -readonly [P in keyof T]: T[P];  // -readonly 移除只读修饰符
};

// 条件映射类型
type PickByType<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K];
};

interface Example {
  name: string;
  age: number;
  id: string;
}

type StringProperties = PickByType<Example, string>;  // { name: string; id: string }
```

### 1.3 模板字面量类型
模板字面量类型允许基于字符串模板创建新的字符串字面量类型。

```typescript
// 基础模板字面量类型
type World = "world";
type Greeting = `hello ${World}`;  // "hello world"

// 联合类型在模板字面量中的分布
type Color = "red" | "blue" | "green";
type HexColor = `#${string}`;
type RGBColor = `rgb(${number}, ${number}, ${number})`;
type AnyColor = HexColor | RGBColor;

// 工具类型实现：CamelCase转换
type CamelCase<S extends string> = S extends `${infer First}_${infer Rest}`
  ? `${First}${CamelCase<Capitalize<Rest>>}`
  : S;

type Camel = CamelCase<"some_property_name">;  // "somePropertyName"

// 结合条件类型和模板字面量类型
type ExtractRouteParams<Route extends string> = 
  Route extends `/:${infer Param}/${infer Rest}`
    ? Param | ExtractRouteParams<`/${Rest}`>
    : Route extends `/:${infer Param}`
      ? Param
      : never;

type Params = ExtractRouteParams<"/:userId/:postId">;  // "userId" | "postId"
```

### 1.4 递归类型
递归类型在处理深层次嵌套结构或递归数据结构时非常有用。

```typescript
// 深度只读类型
type DeepReadonly<T> = T extends object
  ? { readonly [P in keyof T]: DeepReadonly<T[P]> }
  : T;

interface NestedObject {
  a: number;
  b: {
    c: string;
    d: {
      e: boolean;
    };
  };
}

type ReadonlyNested = DeepReadonly<NestedObject>;

// 深度可选类型
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// JSON类型定义
type JSONPrimitive = string | number | boolean | null;
type JSONValue = JSONPrimitive | JSONArray | JSONObject;
interface JSONArray extends Array<JSONValue> {}
interface JSONObject {
  [key: string]: JSONValue;
}

// 递归类型验证示例：验证深度路径
type ValidPath<T, Path extends string> = 
  Path extends `${infer Key}.${infer Rest}`
    ? Key extends keyof T
      ? ValidPath<T[Key], Rest>
      : never
    : Path extends keyof T
      ? T[Path]
      : never;

interface Config {
  database: {
    host: string;
    port: number;
    credentials: {
      username: string;
      password: string;
    };
  };
  server: {
    port: number;
  };
}

type HostType = ValidPath<Config, "database.host">;  // string
type PortType = ValidPath<Config, "server.port">;    // number
```

### 1.5 infer关键字
infer关键字用于在条件类型中声明待推断的类型变量。

```typescript
// 推断函数返回类型
type ReturnType<T extends (...args: any) => any> = T extends (...args: any) => infer R ? R : any;

// 推断函数参数类型
type Parameters<T extends (...args: any) => any> = T extends (...args: infer P) => any ? P : never;

// 推断Promise的解析类型
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;

type Unwrapped = UnwrapPromise<Promise<string>>;  // string

// 推断构造函数参数
type ConstructorParameters<T extends new (...args: any) => any> = 
  T extends new (...args: infer P) => any ? P : never;

// 推断数组元素类型
type ElementType<T extends any[]> = T extends (infer E)[] ? E : never;
type Elem = ElementType<string[]>;  // string

// 多个infer推断
type SwapTuple<T extends [any, any]> = T extends [infer A, infer B] ? [B, A] : never;
type Swapped = SwapTuple<[string, number]>;  // [number, string]
```

## 2. 泛型编程

### 2.1 泛型约束
泛型约束通过extends关键字限制泛型参数必须满足某些条件。

```typescript
// 基础泛型约束
interface Lengthwise {
  length: number;
}

function logLength<T extends Lengthwise>(arg: T): T {
  console.log(arg.length);
  return arg;
}

logLength("hello");    // OK，字符串有length属性
logLength([1, 2, 3]);  // OK，数组有length属性
// logLength(123);      // Error，数字没有length属性

// keyof约束
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const person = { name: "Alice", age: 30 };
const name = getProperty(person, "name");  // OK
// const unknown = getProperty(person, "unknown");  // Error

// 构造函数约束
interface Constructor<T> {
  new (...args: any[]): T;
}

function createInstance<T>(constructor: Constructor<T>): T {
  return new constructor();
}

// 多重约束
interface Printable {
  print(): void;
}

interface Loggable {
  log(): void;
}

function logAndPrint<T extends Printable & Loggable>(item: T): void {
  item.print();
  item.log();
}
```

### 2.2 泛型默认值
泛型默认值为泛型参数提供默认类型，使其成为可选参数。

```typescript
// 基础默认值
interface ApiResponse<T = any> {
  data: T;
  status: number;
  message: string;
}

const response: ApiResponse<string> = {
  data: "success",
  status: 200,
  message: "OK"
};

const genericResponse: ApiResponse = {
  data: { id: 1 },
  status: 200,
  message: "OK"
};

// 多个泛型参数默认值
interface Pair<K = string, V = any> {
  key: K;
  value: V;
}

const stringPair: Pair = { key: "id", value: 123 };
const typedPair: Pair<number, string> = { key: 1, value: "one" };

// 泛型类默认值
class Cache<T = string> {
  private data: T[] = [];
  
  add(item: T): void {
    this.data.push(item);
  }
  
  getAll(): T[] {
    return [...this.data];
  }
}

const stringCache = new Cache<string>();
const numberCache = new Cache<number>();
const defaultCache = new Cache();  // 默认为string
```

### 2.3 泛型工具类型
TypeScript内置了许多实用的泛型工具类型。

```typescript
// Partial - 所有属性变为可选
type Partial<T> = {
  [P in keyof T]?: T[P];
};

// Required - 所有属性变为必需
type Required<T> = {
  [P in keyof T]-?: T[P];
};

// Readonly - 所有属性变为只读
type Readonly<T> = {
  readonly [P in keyof T]: T[P];
};

// Pick - 从T中选取指定属性K
type Pick<T, K extends keyof T> = {
  [P in K]: T[P];
};

// Omit - 从T中排除指定属性K
type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;

// Record - 构造一个属性键为K，属性值为T的类型
type Record<K extends keyof any, T> = {
  [P in K]: T;
};

// Exclude - 从联合类型T中排除可分配给U的类型
type Exclude<T, U> = T extends U ? never : T;

// Extract - 从联合类型T中提取可分配给U的类型
type Extract<T, U> = T extends U ? T : never;

// NonNullable - 排除null和undefined
type NonNullable<T> = T extends null | undefined ? never : T;

// Parameters - 获取函数参数类型
type Parameters<T extends (...args: any) => any> = 
  T extends (...args: infer P) => any ? P : never;

// ConstructorParameters - 获取构造函数参数类型
type ConstructorParameters<T extends abstract new (...args: any) => any> = 
  T extends abstract new (...args: infer P) => any ? P : never;

// ReturnType - 获取函数返回类型
type ReturnType<T extends (...args: any) => any> = 
  T extends (...args: any) => infer R ? R : any;

// InstanceType - 获取构造函数实例类型
type InstanceType<T extends abstract new (...args: any) => any> = 
  T extends abstract new (...args: any) => infer R ? R : any;
```

## 3. 类型体操实战

### 3.1 实现Partial
```typescript
type MyPartial<T> = {
  [P in keyof T]?: T[P];
};

// 深度Partial
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

interface User {
  name: string;
  address: {
    street: string;
    city: string;
    zip: number;
  };
  hobbies: string[];
}

type PartialUser = MyPartial<User>;
type DeepPartialUser = DeepPartial<User>;
```

### 3.2 实现Required
```typescript
type MyRequired<T> = {
  [P in keyof T]-?: T[P];
};

// 深度Required
type DeepRequired<T> = {
  [P in keyof T]-?: T[P] extends object ? DeepRequired<T[P]> : T[P];
};
```

### 3.3 实现Pick
```typescript
type MyPick<T, K extends keyof T> = {
  [P in K]: T[P];
};

// 条件Pick
type ConditionalPick<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K];
};
```

### 3.4 实现Omit
```typescript
type MyOmit<T, K extends keyof T> = MyPick<T, Exclude<keyof T, K>>;

// 条件Omit
type ConditionalOmit<T, U> = {
  [K in keyof T as T[K] extends U ? never : K]: T[K];
};
```

### 3.5 实现Record
```typescript
type MyRecord<K extends keyof any, T> = {
  [P in K]: T;
};

// 带验证的Record
type StrictRecord<K extends keyof any, T> = {
  readonly [P in K]: T;
};
```

### 3.6 实现Exclude和Extract
```typescript
type MyExclude<T, U> = T extends U ? never : T;
type MyExtract<T, U> = T extends U ? T : never;

// 示例
type NumberOrString = number | string | boolean;
type OnlyNumbers = MyExclude<NumberOrString, string | boolean>;  // number
type OnlyStrings = MyExtract<NumberOrString, string | boolean>;  // string | boolean
```

### 3.7 实现ReturnType
```typescript
type MyReturnType<T extends (...args: any[]) => any> = 
  T extends (...args: any[]) => infer R ? R : any;

// 更严格的版本
type StrictReturnType<T> = T extends (...args: any[]) => infer R
  ? R extends Promise<infer U>
    ? U
    : R
  : never;
```

### 3.8 复杂类型体操实战
```typescript
// 实现DeepOmit
type DeepOmit<T, K extends string> = {
  [P in keyof T as P extends K ? never : P]: 
    T[P] extends object ? DeepOmit<T[P], K> : T[P];
};

// 实现DeepPick
type DeepPick<T, K extends string> = {
  [P in keyof T as P extends K ? P : never]: 
    T[P] extends object ? DeepPick<T[P], K> : T[P];
};

// 实现UnionToIntersection
type UnionToIntersection<U> = 
  (U extends any ? (k: U) => void : never) extends 
  ((k: infer I) => void) ? I : never;

type Union = { a: string } | { b: number } | { c: boolean };
type Intersection = UnionToIntersection<Union>;  // { a: string } & { b: number } & { c: boolean }

// 实现Tuple转Union
type TupleToUnion<T extends any[]> = T[number];
type Tuple = [string, number, boolean];
type UnionFromTuple = TupleToUnion<Tuple>;  // string | number | boolean

// 实现KebabCase转CamelCase
type KebabToCamel<S extends string> = S extends `${infer Head}-${infer Tail}`
  ? `${Head}${KebabToCamel<Capitalize<Tail>>}`
  : S;

type Camel = KebabToCamel<"foo-bar-baz">;  // "fooBarBaz"
```

## 4. 装饰器

### 4.1 类装饰器
类装饰器应用于类构造函数，可以用来监视、修改或替换类定义。

```typescript
// 基础类装饰器
function sealed(constructor: Function) {
  Object.seal(constructor);
  Object.seal(constructor.prototype);
}

@sealed
class Greeter {
  greeting: string;
  constructor(message: string) {
    this.greeting = message;
  }
  greet() {
    return "Hello, " + this.greeting;
  }
}

// 工厂类装饰器
function classDecorator(value: string) {
  return function (constructor: Function) {
    console.log(`Class created with value: ${value}`);
  };
}

@classDecorator("example")
class Example {}

// 替换类构造函数
function replaceClass<T extends { new (...args: any[]): {} }>(
  constructor: T
) {
  return class extends constructor {
    newProperty = "new property";
    hello = "override";
  };
}

@replaceClass
class Original {
  property = "property";
  hello: string;
  constructor(m: string) {
    this.hello = m;
  }
}

console.log(new Original("world"));  // 输出包含新属性
```

### 4.2 方法装饰器
方法装饰器应用于方法的属性描述符，可以用来监视、修改或替换方法定义。

```typescript
// 基础方法装饰器
function log(
  target: any,
  propertyKey: string,
  descriptor: PropertyDescriptor
) {
  const originalMethod = descriptor.value;

  descriptor.value = function (...args: any[]) {
    console.log(`Calling ${propertyKey} with args: ${JSON.stringify(args)}`);
    const result = originalMethod.apply(this, args);
    console.log(`Result: ${result}`);
    return result;
  };

  return descriptor;
}

class Calculator {
  @log
  add(a: number, b: number): number {
    return a + b;
  }
}

// 工厂方法装饰器
function throttle(delay: number) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;
    let timeoutId: NodeJS.Timeout | null = null;

    descriptor.value = function (...args: any[]) {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      timeoutId = setTimeout(() => {
        originalMethod.apply(this, args);
        timeoutId = null;
      }, delay);
    };

    return descriptor;
  };
}

class Button {
  @throttle(300)
  click() {
    console.log("Button clicked!");
  }
}

// 缓存装饰器
function memoize(
  target: any,
  propertyKey: string,
  descriptor: PropertyDescriptor
) {
  const originalMethod = descriptor.value;
  const cache = new Map<string, any>();

  descriptor.value = function (...args: any[]) {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key);
    }

    const result = originalMethod.apply(this, args);
    cache.set(key, result);
    return result;
  };

  return descriptor;
}
```

### 4.3 属性装饰器
属性装饰器应用于类的属性，可以用来监视属性的定义。

```typescript
// 属性装饰器
function format(formatString: string) {
  return function (target: any, propertyKey: string) {
    let value: string;

    const getter = function () {
      return value;
    };

    const setter = function (newVal: string) {
      value = formatString.replace("{value}", newVal);
    };

    Object.defineProperty(target, propertyKey, {
      get: getter,
      set: setter,
      enumerable: true,
      configurable: true,
    });
  };
}

class User {
  @format("Name: {value}")
  name: string;

  constructor(name: string) {
    this.name = name;
  }
}

const user = new User("John");
console.log(user.name);  // 输出: "Name: John"

// 验证装饰器
function validate(validationFn: (value: any) => boolean) {
  return function (target: any, propertyKey: string) {
    let value: any;

    const getter = function () {
      return value;
    };

    const setter = function (newVal: any) {
      if (!validationFn(newVal)) {
        throw new Error(`Invalid value for ${propertyKey}`);
      }
      value = newVal;
    };

    Object.defineProperty(target, propertyKey, {
      get: getter,
      set: setter,
      enumerable: true,
      configurable: true,
    });
  };
}

class Product {
  @validate((price: number) => price > 0)
  price: number;

  constructor(price: number) {
    this.price = price;
  }
}
```

### 4.4 参数装饰器
参数装饰器应用于方法的参数，可以用来监视方法参数的定义。

```typescript
// 参数装饰器
function required(
  target: Object,
  propertyKey: string | symbol,
  parameterIndex: number
) {
  const existingRequiredParameters: number[] = 
    Reflect.getOwnMetadata("required", target, propertyKey) || [];
  existingRequiredParameters.push(parameterIndex);
  Reflect.defineMetadata(
    "required",
    existingRequiredParameters,
    target,
    propertyKey
  );
}

// 方法装饰器，验证必需参数
function validateRequired(
  target: any,
  propertyKey: string,
  descriptor: PropertyDescriptor
) {
  const method = descriptor.value;

  descriptor.value = function (...args: any[]) {
    const requiredParameters: number[] = 
      Reflect.getOwnMetadata("required", target, propertyKey) || [];
    
    requiredParameters.forEach((index) => {
      if (args[index] === undefined || args[index] === null) {
        throw new Error(`Missing required argument at index ${index}`);
      }
    });

    return method.apply(this, args);
  };
}

class UserService {
  @validateRequired
  createUser(@required name: string, @required email: string, age?: number) {
    return { name, email, age };
  }
}

const service = new UserService();
service.createUser("Alice", "alice@example.com");  // OK
// service.createUser("Alice", undefined);  // Error: Missing required argument at index 1
```

## 5. 模块系统

### 5.1 ES模块 (ESM)
ES模块是现代JavaScript的标准模块系统。

```typescript
// math.ts - 导出
export function add(a: number, b: number): number {
  return a + b;
}

export function subtract(a: number, b: number): number {
  return a - b;
}

export default class Calculator {
  calculate(a: number, b: number, operator: string): number {
    switch (operator) {
      case '+': return add(a, b);
      case '-': return subtract(a, b);
      default: throw new Error('Invalid operator');
    }
  }
}

// main.ts - 导入
import Calculator, { add, subtract } from './math';

// 或者整体导入
import * as MathUtils from './math';

const calc = new Calculator();
console.log(calc.calculate(5, 3, '+'));
```

### 5.2 CommonJS (CJS)
CommonJS是Node.js使用的模块系统。

```typescript
// math.cjs
const add = (a, b) => a + b;
const subtract = (a, b) => a - b;

module.exports = { add, subtract };

// 或者
exports.add = (a, b) => a + b;
exports.subtract = (a, b) => a - b;

// main.cjs
const { add, subtract } = require('./math');
console.log(add(5, 3));
```

### 5.3 AMD (Asynchronous Module Definition)
AMD是用于浏览器环境的异步模块系统。

```typescript
// 定义模块
define(['dependency'], function(dep) {
  return {
    method: function() {
      return dep.doSomething();
    }
  };
});

// 或者使用CommonJS风格
define(function(require, exports, module) {
  const dep = require('dependency');
  exports.method = function() {
    return dep.doSomething();
  };
});
```

### 5.4 UMD (Universal Module Definition)
UMD同时支持AMD、CommonJS和全局变量。

```typescript
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD
    define(['dependency'], factory);
  } else if (typeof module === 'object' && module.exports) {
    // CommonJS
    module.exports = factory(require('dependency'));
  } else {
    // 全局变量
    root.MyModule = factory(root.Dependency);
  }
}(typeof self !== 'undefined' ? self : this, function(dependency) {
  return {
    method: function() {
      return dependency.doSomething();
    }
  };
}));
```

## 6. 声明文件 (.d.ts) 编写

### 6.1 基础声明文件
```typescript
// types.d.ts
declare module 'my-module' {
  export function doSomething(): void;
  export class MyClass {
    constructor(value: string);
    getValue(): string;
  }
}

// 为没有类型定义的库添加类型
declare module 'lodash' {
  export function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait?: number
  ): T;
  export function throttle<T extends (...args: any[]) => any>(
    func: T,
    wait?: number
  ): T;
}
```

### 6.2 全局声明
```typescript
// global.d.ts
declare global {
  interface Window {
    myGlobalFunction: () => void;
    MyGlobalClass: new () => { doSomething(): void };
  }

  // 扩展已有类型
  interface Array<T> {
    last(): T | undefined;
  }

  // 全局变量
  declare const API_KEY: string;
  declare function trackEvent(name: string, data?: any): void;
}

export {};  // 确保文件被当作模块处理
```

### 6.3 模块增强
```typescript
// augmentation.d.ts
import 'express';

declare module 'express' {
  interface Request {
    user?: {
      id: string;
      email: string;
      roles: string[];
    };
  }

  interface Response {
    success(data: any): void;
    error(message: string, code?: number): void;
  }
}

// 使用增强的类型
import express from 'express';
const app = express();

app.use((req, res, next) => {
  // req.user 现在有类型定义
  if (req.user?.roles.includes('admin')) {
    next();
  }
});
```

### 6.4 复杂类型声明
```typescript
// advanced.d.ts
declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: 'development' | 'production' | 'test';
    PORT: string;
    DATABASE_URL: string;
    JWT_SECRET: string;
  }
}

declare module '*.module.css' {
  const classes: { readonly [key: string]: string };
  export default classes;
}

declare module '*.svg' {
  const content: React.FunctionComponent<React.SVGAttributes<SVGElement>>;
  export default content;
}

declare module '*.json' {
  const value: any;
  export default value;
}

// 泛型模块声明
declare module 'queue' {
  class Queue<T> {
    constructor(options?: { concurrency?: number });
    add(task: () => Promise<T>): Promise<T>;
    on(event: 'complete', callback: (result: T) => void): void;
    on(event: 'error', callback: (error: Error) => void): void;
  }
  export = Queue;
}
```

## 7. TypeScript编译器API

### 7.1 编译器API基础
```typescript
import * as ts from 'typescript';

// 创建编译器主机
const compilerHost: ts.CompilerHost = {
  getSourceFile: (fileName, languageVersion) => {
    const sourceText = fs.readFileSync(fileName, 'utf-8');
    return ts.createSourceFile(fileName, sourceText, languageVersion, true);
  },
  writeFile: (fileName, text) => {
    fs.writeFileSync(fileName, text);
  },
  getDefaultLibFileName: (options) => ts.getDefaultLibFilePath(options),
  useCaseSensitiveFileNames: () => false,
  getCanonicalFileName: (fileName) => fileName,
  getCurrentDirectory: () => process.cwd(),
  getNewLine: () => '\n',
  fileExists: (fileName) => fs.existsSync(fileName),
  readFile: (fileName) => fs.readFileSync(fileName, 'utf-8'),
};

// 编译选项
const compilerOptions: ts.CompilerOptions = {
  target: ts.ScriptTarget.ES2020,
  module: ts.ModuleKind.CommonJS,
  strict: true,
  esModuleInterop: true,
  skipLibCheck: true,
  outDir: './dist',
};

// 创建程序
const program = ts.createProgram(['src/index.ts'], compilerOptions, compilerHost);

// 获取诊断信息
const diagnostics = ts.getPreEmitDiagnostics(program);
diagnostics.forEach(diagnostic => {
  if (diagnostic.file) {
    const { line, character } = diagnostic.file.getLineAndCharacterOfPosition(
      diagnostic.start!
    );
    const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n');
    console.log(`${diagnostic.file.fileName} (${line + 1},${character + 1}): ${message}`);
  } else {
    console.log(ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n'));
  }
});

// 发射输出
program.emit();
```

### 7.2 AST遍历和转换
```typescript
import * as ts from 'typescript';

// 创建转换器
function transformer<T extends ts.Node>(context: ts.TransformationContext) {
  return (rootNode: T) => {
    function visit(node: ts.Node): ts.Node {
      // 查找console.log调用
      if (
        ts.isCallExpression(node) &&
        ts.isPropertyAccessExpression(node.expression) &&
        node.expression.expression.getText() === 'console' &&
        node.expression.name.getText() === 'log'
      ) {
        // 替换为自定义的日志函数
        return ts.factory.createCallExpression(
          ts.factory.createIdentifier('customLog'),
          undefined,
          node.arguments
        );
      }
      
      return ts.visitEachChild(node, visit, context);
    }
    
    return ts.visitNode(rootNode, visit);
  };
}

// 使用转换器
const sourceCode = `
console.log('Hello');
console.warn('Warning');
`;

const sourceFile = ts.createSourceFile(
  'example.ts',
  sourceCode,
  ts.ScriptTarget.Latest,
  true
);

const result = ts.transform(sourceFile, [transformer]);
const transformedSource = ts.createPrinter().printFile(result.transformed[0] as ts.SourceFile);

console.log(transformedSource);
// 输出包含customLog调用的代码
```

### 7.3 类型检查器使用
```typescript
import * as ts from 'typescript';

function getTypeInfo(fileName: string): void {
  const program = ts.createProgram([fileName], {
    target: ts.ScriptTarget.ES2020,
    module: ts.ModuleKind.CommonJS,
    strict: true,
  });
  
  const checker = program.getTypeChecker();
  const sourceFile = program.getSourceFile(fileName)!;
  
  function visit(node: ts.Node) {
    if (ts.isVariableDeclaration(node) && node.type) {
      const type = checker.getTypeAtLocation(node);
      const typeString = checker.typeToString(type);
      console.log(`Variable ${node.name.getText()}: ${typeString}`);
    }
    
    ts.forEachChild(node, visit);
  }
  
  visit(sourceFile);
}

// 使用类型检查器进行类型推断
function inferType(expression: string): string {
  const sourceCode = `const result = ${expression};`;
  const sourceFile = ts.createSourceFile(
    'temp.ts',
    sourceCode,
    ts.ScriptTarget.Latest,
    true
  );
  
  const program = ts.createProgram(['temp.ts'], {}, {
    getSourceFile: (fileName) => sourceFile,
    writeFile: () => {},
    getDefaultLibFileName: (options) => ts.getDefaultLibFilePath(options),
    useCaseSensitiveFileNames: () => false,
    getCanonicalFileName: (fileName) => fileName,
    getCurrentDirectory: () => '',
    getNewLine: () => '\n',
    fileExists: (fileName) => fileName === 'temp.ts',
    readFile: (fileName) => sourceCode,
  });
  
  const checker = program.getTypeChecker();
  const variableStatement = sourceFile.statements[0] as ts.VariableStatement;
  const variableDeclaration = variableStatement.declarationList.declarations[0];
  const type = checker.getTypeAtLocation(variableDeclaration);
  
  return checker.typeToString(type);
}

console.log(inferType('"hello"'));  // string
console.log(inferType('42'));       // number
console.log(inferType('[1, 2, 3]')); // number[]
```

## 8. 与React/Vue的集成

### 8.1 React + TypeScript
```typescript
// React组件类型定义
import React, { useState, useEffect, useMemo } from 'react';

// 基础组件Props
interface UserCardProps {
  user: {
    id: number;
    name: string;
    email: string;
  };
  onEdit?: (userId: number) => void;
  onDelete?: (userId: number) => void;
}

// 泛型组件
interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string;
  emptyComponent?: React.ReactNode;
}

function List<T>({ items, renderItem, keyExtractor, emptyComponent }: ListProps<T>) {
  if (items.length === 0) {
    return <>{emptyComponent}</> || <div>No items</div>;
  }
  
  return (
    <ul>
      {items.map((item, index) => (
        <li key={keyExtractor(item)}>
          {renderItem(item, index)}
        </li>
      ))}
    </ul>
  );
}

// Hook类型定义
interface UseAsyncResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  execute: (...args: any[]) => Promise<void>;
}

function useAsync<T>(
  asyncFunction: (...args: any[]) => Promise<T>,
  immediate = true
): UseAsyncResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const execute = useCallback(async (...args: any[]) => {
    setLoading(true);
    setError(null);
    try {
      const result = await asyncFunction(...args);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [asyncFunction]);
  
  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);
  
  return { data, loading, error, execute };
}

// 使用示例
const UserList: React.FC = () => {
  const { data: users, loading, error } = useAsync(fetchUsers);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <List
      items={users || []}
      renderItem={(user) => <UserCard user={user} />}
      keyExtractor={(user) => user.id.toString()}
    />
  );
};
```

### 8.2 Vue 3 + TypeScript
```typescript
// Vue 3组件类型定义
import { defineComponent, ref, computed, PropType } from 'vue';

// 基础组件
interface User {
  id: number;
  name: string;
  email: string;
}

export default defineComponent({
  name: 'UserCard',
  props: {
    user: {
      type: Object as PropType<User>,
      required: true,
    },
    showEmail: {
      type: Boolean,
      default: true,
    },
  },
  emits: {
    edit: (userId: number) => typeof userId === 'number',
    delete: (userId: number) => typeof userId === 'number',
  },
  setup(props, { emit }) {
    const isActive = ref(false);
    
    const displayName = computed(() => {
      return props.user.name.toUpperCase();
    });
    
    const handleEdit = () => {
      emit('edit', props.user.id);
    };
    
    const handleDelete = () => {
      emit('delete', props.user.id);
    };
    
    return {
      isActive,
      displayName,
      handleEdit,
      handleDelete,
    };
  },
});

// 组合式函数
import { ref, onMounted, onUnmounted } from 'vue';

interface UseMousePositionResult {
  x: Ref<number>;
  y: Ref<number>;
}