---
outline: [1,3]
head:
  - - meta
    - name: description
      content: JavaScript对象方法介绍
  - - meta
    - name: keywords
      content: JavaScript 对象 方法 属性 前端开发
tags: [JavaScript, Object]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/javascript/Object.md"
---

# 总览

### 1. 对象创建和属性操作：

- **[Object.create()](#object-create)**：使用指定的原型对象和属性创建一个新对象。
- **[Object.defineProperty()](#object-defineproperty)**：给对象添加一个属性并指定该属性的配置。
- **[Object.defineProperties()](#object-defineproperties)**：给对象添加多个属性并分别指定它们的配置。
- **[Object.getOwnPropertyDescriptor()](#object-getownpropertydescriptor)**：返回对象属性的配置描述。
- **[Object.getOwnPropertyNames()](#object-getownpropertynames)**：返回对象所有自身属性的属性名组成的数组。
- **[Object.keys()](#object-keys)**：返回对象所有可枚举的自身属性的属性名组成的数组。
- **[Object.values()](#object-values)**：返回对象所有可枚举的自身属性的属性值组成的数组。
- **[Object.entries()](#object-entries)**：返回对象所有可枚举的自身属性的键值对组成的数组。

### 2. 对象原型和继承：

- **[Object.getPrototypeOf()](#object-getprototypeof)**：返回指定对象的原型。
- **[Object.setPrototypeOf()](#object-setprototypeof)**：设置对象的原型。
- **[Object.isPrototypeOf()](#object-isprototypeof)**：判断一个对象是否存在于另一个对象的原型链上。

### 3. 对象比较和扩展：

- **[Object.is()](#object-is)**：判断两个值是否为同一个值。
- **[Object.assign()](#object-assign)**：将所有可枚举属性的值从一个或多个源对象复制到目标对象。
- **[Object.freeze()](#object-freeze)**：冻结一个对象，使其不能被修改。
- **[Object.seal()](#object-seal)**：封闭一个对象，阻止添加新属性并将所有现有属性标记为不可配置。
- **[Object.preventExtensions()](#object-preventextensions)**：阻止对象扩展，使其不能添加新属性。

### 4. 对象状态检查：

- **[Object.hasOwn()](#object-hasown)**：判断对象自身属性中是否具有指定的属性。
- **[Object.isExtensible()](#object-isextensible)**：判断对象是否可扩展。
- **[Object.isSealed()](#object-issealed)**：判断对象是否被封闭。
- **[Object.isFrozen()](#object-isfrozen)**：判断对象是否被冻结。

这些方法涵盖了大部分对象操作的需求，合理使用这些方法可以使你的代码更加健壮和高效。

# JavaScript对象方法

### 1. Object.create() {#object-create}

```javascript
const proto = { greeting: 'Hello' };
const obj = Object.create(proto, {
  name: {
    value: 'John',
    writable: true
  }
});
console.log(obj.greeting); // "Hello"
console.log(obj.name); // "John"
```

1. `Object.create()` 方法创建一个新对象，使用现有的对象来提供新创建的对象的原型。
2. 第一个参数是原型对象，第二个参数是属性描述符对象（可选）。
3. 如果原型为 `null`，则创建的对象没有原型。
4. 常用于实现继承和创建纯净对象。



### 2. Object.defineProperty() {#object-defineproperty}

```javascript
const obj = {};
Object.defineProperty(obj, 'name', {
  value: 'John',
  writable: false,
  enumerable: true,
  configurable: true
});
console.log(obj.name); // "John"
obj.name = 'Jane'; // 严格模式下会报错
console.log(obj.name); // "John" (值未被修改)
```



1. `Object.defineProperty()` 方法会直接在一个对象上定义一个新属性，或者修改一个对象的现有属性。
2. 可以精确控制属性的行为（可写、可枚举、可配置）。
3. 属性描述符包括数据描述符和存取描述符。
4. 默认情况下，使用此方法添加的属性是不可写、不可枚举、不可配置的。

### 3. Object.defineProperties() 

```js
const obj = {};
Object.defineProperties(obj, {
  name: {
    value: 'John',
    writable: true
  },
  age: {
    value: 30,
    enumerable: true
  }
});
console.log(obj.name); // "John"
console.log(obj.age); // 30
```



1. `Object.defineProperties()` 方法直接在一个对象上定义一个或多个新的属性或修改现有属性。
2. 可以一次性定义多个属性。
3. 每个属性都有自己的配置描述符。
4. 返回修改后的对象。

### 4. Object.getOwnPropertyDescriptor() {#object-getownpropertydescriptor}

javascript

```js
const obj = { name: 'John' };
const descriptor = Object.getOwnPropertyDescriptor(obj, 'name');
console.log(descriptor);
// { value: "John", writable: true, enumerable: true, configurable: true }
```



1. `Object.getOwnPropertyDescriptor()` 方法返回指定对象上一个自有属性对应的属性描述符。
2. 自有属性指的是直接赋予该对象的属性，不需要从原型链上进行查找的属性。
3. 如果属性不存在，返回 `undefined`。
4. 可用于检查属性的配置。

### 5. Object.getOwnPropertyNames() {#object-getownpropertynames}

javascript

```js
const obj = {
  name: 'John',
  age: 30
};
Object.defineProperty(obj, 'hidden', {
  value: 'secret',
  enumerable: false
});
console.log(Object.getOwnPropertyNames(obj)); // ["name", "age", "hidden"]
```



1. `Object.getOwnPropertyNames()` 方法返回一个由指定对象的所有自身属性的属性名（包括不可枚举属性）组成的数组。
2. 不包括原型链上的属性。
3. 数组中枚举属性的顺序与通过 `for...in` 循环遍历该对象属性时一致。

### 6. Object.keys() {#object-keys}

javascript

```js
const obj = {
  name: 'John',
  age: 30,
  [Symbol('id')]: 123
};
Object.defineProperty(obj, 'hidden', {
  value: 'secret',
  enumerable: false
});
console.log(Object.keys(obj)); // ["name", "age"]
```



1. `Object.keys()` 方法返回一个由一个给定对象的自身可枚举属性组成的数组。
2. 数组中属性名的排列顺序和正常循环遍历该对象时返回的顺序一致。
3. 不包括不可枚举属性和 Symbol 属性。
4. 常用于遍历对象的可枚举属性。

### 7. Object.values() {#object-values}

javascript

```js
const obj = {
  name: 'John',
  age: 30,
  city: 'New York'
};
console.log(Object.values(obj)); // ["John", 30, "New York"]
```



1. `Object.values()` 方法返回一个给定对象自身的所有可枚举属性值的数组。
2. 值的顺序与使用 `for...in` 循环的顺序相同。
3. 不包括原型链上的属性值。
4. 如果属性名是数字，会按照数字大小排序。

### 8. Object.entries() {#object-entries}

javascript

```js
const obj = {
  name: 'John',
  age: 30
};
console.log(Object.entries(obj)); // [["name", "John"], ["age", 30]]
```



1. `Object.entries()` 方法返回一个给定对象自身可枚举属性的键值对数组。
2. 每个键值对都是一个包含两个元素的数组：`[key, value]`。
3. 顺序与 `Object.keys()` 一致。
4. 常用于将对象转换为 Map 或进行迭代。

### 9. Object.getPrototypeOf() {#object-getprototypeof}

javascript

```js
const proto = { greeting: 'Hello' };
const obj = Object.create(proto);
console.log(Object.getPrototypeOf(obj) === proto); // true
```



1. `Object.getPrototypeOf()` 方法返回指定对象的原型。
2. 如果没有继承属性，则返回 `null`。
3. 在 ES5 中，如果参数不是对象，会抛出 TypeError 异常。
4. 在 ES6 中，参数会被强制转换为对象。

### 10. Object.setPrototypeOf() {#object-setprototypeof}

javascript

```js
const proto = { greeting: 'Hello' };
const obj = { name: 'John' };
Object.setPrototypeOf(obj, proto);
console.log(obj.greeting); // "Hello"
```



1. `Object.setPrototypeOf()` 方法设置一个指定的对象的原型到另一个对象或 `null`。
2. 由于性能原因，应避免使用此方法，建议使用 `Object.create()`。
3. 可能会触发 JavaScript 引擎的优化失效。
4. 如果原型被设置为不可扩展的对象，会抛出 TypeError。

### 11. Object.isPrototypeOf() {#object-isprototypeof}

javascript

```js
function Animal() {}
function Dog() {}
Dog.prototype = Object.create(Animal.prototype);
const dog = new Dog();
console.log(Animal.prototype.isPrototypeOf(dog)); // true
console.log(Dog.prototype.isPrototypeOf(dog)); // true
```



1. `isPrototypeOf()` 方法用于测试一个对象是否存在于另一个对象的原型链上。
2. 与 `instanceof` 运算符不同，此方法直接检查原型链。
3. 如果原型是 `null` 或 `undefined`，返回 `false`。
4. 所有对象都会从 `Object.prototype` 继承 `isPrototypeOf()` 方法。

### 12. [Object.is](https://object.is/)() {#object-is}

javascript

```js
console.log(Object.is(0, -0)); // false
console.log(Object.is(NaN, NaN)); // true
console.log(Object.is('hello', 'hello')); // true
```



1. `Object.is()` 方法判断两个值是否为同一个值。
2. 与 `===` 类似，但有两个区别：
   - `Object.is(NaN, NaN)` 返回 `true`
   - `Object.is(0, -0)` 返回 `false`
3. 适用于需要精确相等比较的场景。
4. 在 ES6 中引入，用于解决 `===` 的一些边界情况。

### 13. Object.assign() {#object-assign}

javascript

```js
const target = { a: 1, b: 2 };
const source1 = { b: 3, c: 4 };
const source2 = { c: 5, d: 6 };
const result = Object.assign(target, source1, source2);
console.log(result); // { a: 1, b: 3, c: 5, d: 6 }
console.log(target); // { a: 1, b: 3, c: 5, d: 6 } (target也被修改)
```



1. `Object.assign()` 方法用于将所有可枚举属性的值从一个或多个源对象复制到目标对象。
2. 返回目标对象。
3. 如果目标对象中的属性具有相同的键，则属性将被源对象中的属性覆盖。
4. 只会拷贝源对象自身的可枚举属性。
5. **是浅拷贝，不是深拷贝。**

### 14. Object.freeze() {#object-freeze}

javascript

```js
const obj = { name: 'John', details: { age: 30 } };
Object.freeze(obj);
obj.name = 'Jane'; // 静默失败，严格模式下报错
obj.details.age = 25; // 嵌套对象仍然可以被修改
console.log(obj.name); // "John"
console.log(obj.details.age); // 25
```



1. `Object.freeze()` 方法可以冻结一个对象，使其不能被修改。
2. 冻结后不能添加新属性，不能删除现有属性，不能修改属性值。
3. 对象的原型也不能被修改。
4. 是浅冻结，嵌套对象不会被冻结。
5. 返回被冻结的对象。

### 15. Object.seal() {#object-seal}

javascript

```js
const obj = { name: 'John' };
Object.seal(obj);
obj.name = 'Jane'; // 允许修改现有属性
obj.age = 30; // 不允许添加新属性
delete obj.name; // 不允许删除属性
console.log(obj); // { name: "Jane" }
```



1. `Object.seal()` 方法封闭一个对象，阻止添加新属性并将所有现有属性标记为不可配置。
2. 当前属性的值只要可写就可以改变。
3. 不能添加新属性，不能删除现有属性。
4. 是浅封闭，嵌套对象不会被封闭。

### 16. Object.preventExtensions() {#object-preventextensions}

javascript

```
const obj = { name: 'John' };
Object.preventExtensions(obj);
obj.name = 'Jane'; // 允许修改
obj.age = 30; // 静默失败，严格模式下报错
delete obj.name; // 允许删除
console.log(obj); // {}
```



1. `Object.preventExtensions()` 方法让一个对象变的不可扩展，也就是永远不能再添加新的属性。
2. 可以修改和删除现有属性。
3. 是不可逆的操作。
4. 只影响对象本身，不影响其原型。

### 17. Object.hasOwn() {#object-hasown}

javascript

```
const obj = { name: 'John' };
console.log(Object.hasOwn(obj, 'name')); // true
console.log(Object.hasOwn(obj, 'toString')); // false
console.log(Object.hasOwn(obj, 'age')); // false
```



1. `Object.hasOwn()` 方法返回一个布尔值，指示对象自身属性中是否具有指定的属性。
2. 与 `Object.prototype.hasOwnProperty()` 类似，但更安全。
3. 不会受到原型链上 `hasOwnProperty` 方法被覆盖的影响。
4. 在 ES2022 中引入。

### 18. Object.isExtensible() {#object-isextensible}

javascript

```
const obj = { name: 'John' };
console.log(Object.isExtensible(obj)); // true
Object.preventExtensions(obj);
console.log(Object.isExtensible(obj)); // false
```



1. `Object.isExtensible()` 方法判断一个对象是否是可扩展的（是否可以在它上面添加新的属性）。
2. 默认情况下，对象是可扩展的。
3. 使用 `Object.preventExtensions()`、`Object.seal()` 或 `Object.freeze()` 后都不可扩展。

### 19. Object.isSealed() {#object-issealed}

javascript

```
const obj = { name: 'John' };
console.log(Object.isSealed(obj)); // false
Object.seal(obj);
console.log(Object.isSealed(obj)); // true
```



1. `Object.isSealed()` 方法判断一个对象是否被密封。
2. 密封对象是指那些不可扩展且所有自身属性都不可配置的对象。
3. 冻结的对象也是被密封的。

### 20. Object.isFrozen() {#object-isfrozen}

javascript

```
const obj = { name: 'John' };
console.log(Object.isFrozen(obj)); // false
Object.freeze(obj);
console.log(Object.isFrozen(obj)); // true
```



1. `Object.isFrozen()` 方法判断一个对象是否被冻结。
2. 冻结对象是最严格的不可变形式。
3. 冻结的对象不可扩展、所有属性不可配置、所有数据属性不可写。

### 21. Object.fromEntries() {#object-fromentries}

javascript

```
const entries = [['name', 'John'], ['age', 30]];
const obj = Object.fromEntries(entries);
console.log(obj); // { name: "John", age: 30 }

const map = new Map([['name', 'Jane'], ['city', 'Paris']]);
const objFromMap = Object.fromEntries(map);
console.log(objFromMap); // { name: "Jane", city: "Paris" }
```



1. `Object.fromEntries()` 方法把键值对列表转换为一个对象。
2. 是 `Object.entries()` 的逆操作。
3. 可以转换 Map、Array 等可迭代对象为普通对象。
4. 在 ES2019 中引入。

## 对象应用实例 {#object-example}

### 对象深拷贝

javascript

```
function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj);
  if (obj instanceof Array) return obj.map(item => deepClone(item));
  
  const cloned = Object.create(Object.getPrototypeOf(obj));
  Object.getOwnPropertyNames(obj).forEach(prop => {
    const descriptor = Object.getOwnPropertyDescriptor(obj, prop);
    if (descriptor.value && typeof descriptor.value === 'object') {
      descriptor.value = deepClone(descriptor.value);
    }
    Object.defineProperty(cloned, prop, descriptor);
  });
  return cloned;
}

const original = { name: 'John', details: { age: 30 } };
const copied = deepClone(original);
console.log(copied.details === original.details); // false
```



### 对象属性验证

javascript

```
function createValidatedObject(schema) {
  return Object.freeze({
    setProperty(key, value) {
      if (schema[key] && schema[key].validate(value)) {
        this[key] = value;
      } else {
        throw new Error(`Invalid value for property ${key}`);
      }
    }
  });
}

const schema = {
  name: { validate: val => typeof val === 'string' },
  age: { validate: val => typeof val === 'number' && val >= 0 }
};

const person = createValidatedObject(schema);
person.setProperty('name', 'John');
person.setProperty('age', 30);
```



### 对象观察者模式

javascript

```
function createObservable(target) {
  const handlers = [];
  
  return new Proxy(target, {
    set(obj, prop, value) {
      const oldValue = obj[prop];
      obj[prop] = value;
      handlers.forEach(handler => handler(prop, oldValue, value));
      return true;
    }
  });
}

const observable = createObservable({ name: 'John' });
observable.observe = handler => handlers.push(handler);

observable.observe((prop, oldValue, newValue) => {
  console.log(`Property ${prop} changed from ${oldValue} to ${newValue}`);
});

observable.name = 'Jane'; // 输出: Property name changed from John to Jane
```



### 对象合并与默认值

javascript

```
function mergeWithDefaults(defaults, overrides) {
  const result = Object.assign({}, defaults);
  
  for (const key in overrides) {
    if (overrides.hasOwnProperty(key)) {
      if (typeof overrides[key] === 'object' && overrides[key] !== null &&
          typeof defaults[key] === 'object' && defaults[key] !== null) {
        result[key] = mergeWithDefaults(defaults[key], overrides[key]);
      } else {
        result[key] = overrides[key];
      }
    }
  }
  
  return result;
}

const defaults = { theme: 'dark', settings: { volume: 50, notifications: true } };
const userSettings = { settings: { volume: 75 } };
const finalSettings = mergeWithDefaults(defaults, userSettings);
console.log(finalSettings);
// { theme: 'dark', settings: { volume: 75, notifications: true } }
```