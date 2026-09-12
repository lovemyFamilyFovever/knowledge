---
title: "函数式编程（Functional Programming）概念"
tags: []
source: "baike"
source_path: "开发术语 / 编程语言基础"
collected: "2026-09-05"
status: "imported"
---

# 函数式编程（Functional Programming）概念


> 📌 **导航**：本文是 **函数式编程（Functional Programming）概念** 词条，属于 programming-languages 术语集。相关枢纽：[[Go语言核心]]、[[Python高级编程完全指南]]、[[Rust系统编程入门到精通]]、[[Rust编程基础]]、[[TypeScript深入]]。

---

## 纯函数（Pure Function）

**一句话定义：** 纯函数就是给相同输入，永远返回相同输出，且没有任何"副作用"的函数。

**通俗类比：** 就像计算器——按 1+1 永远等于 2，不会因为你按了几次就变成别的结果。

**具体示例：**
```python
# 纯函数
def add(a, b):
    return a + b

# 非纯函数（依赖外部变量）
tax_rate = 0.1
def calculate_tax(amount):
    return amount * tax_rate  # 如果 tax_rate 变了，结果就变了

# 纯函数版本
def calculate_tax_pure(amount, rate):
    return amount * rate
```

```javascript
// 纯函数
const add = (a, b) => a + b;

// 非纯函数（修改了外部变量）
let discount = 0.1;
const applyDiscount = (price) => {
    discount = 0.2;  // 副作用！修改了外部状态
    return price * (1 - discount);
};

// 纯函数版本
const applyDiscountPure = (price, rate) => price * (1 - rate);
```

**为什么需要它：** 纯函数易于测试、调试和并行化，是函数式编程的基石。

**与相关术语对比：** 纯函数 vs 副作用——纯函数没有副作用，有副作用的函数不是纯函数。

---

## 副作用（Side Effect）

**一句话定义：** 副作用就是函数除了返回值之外，还做了其他"改变世界"的事情。

**通俗类比：** 你去餐厅点菜（调用函数），结果服务员不仅给你上了菜（返回值），还顺手帮你充了会员卡（副作用）——这就不只是"点菜"那么简单了。

**具体示例：**
```python
# 常见副作用
counter = 0

def increment():           # 副作用：修改了全局变量
    global counter
    counter += 1

def log_message(msg):      # 副作用：写入了控制台/文件
    print(msg)

def send_email(user):      # 副作用：发了邮件
    # 发送邮件的代码...
    pass

def read_file(path):       # 副作用：读取了文件系统
    return open(path).read()
```

```javascript
// 副作用示例
let globalState = { count: 0 };

const increment = () => {
    globalState.count++;  // 修改外部状态 = 副作用
};

const saveToDatabase = (data) => {
    db.save(data);  // 写入数据库 = 副作用
};

const fetchAPI = async (url) => {
    const res = await fetch(url);  // 网络请求 = 副作用
    return res.json();
};
```

**为什么需要它：** 副作用让程序行为不可预测，函数式编程鼓励尽量减少副作用。

**与相关术语对比：** 副作用 vs 纯函数——有副作用的函数输出可能依赖外部状态，纯函数的输出只依赖输入。

---

## 不可变性（Immutability）

**一句话定义：** 不可变性就是数据一旦创建就不能被修改，要变就创建新的副本。

**通俗类比：** 就像用铅笔写字 vs 刻在石碑上——铅笔可以擦改（可变），石碑上的字只能重新刻一块（不可变）。

**具体示例：**
```python
# Python 中 tuple 是不可变的
point = (3, 4)
# point[0] = 5  # 报错！不可修改

# 列表可变，但可以用新列表代替
original = [1, 2, 3]
modified = original + [4]  # 创建新列表，原列表不变
print(original)  # [1, 2, 3]
print(modified)  # [1, 2, 3, 4]

# 用 frozenset 创建不可变集合
fs = frozenset([1, 2, 3])
# fs.add(4)  # 报错！
```

```javascript
// JavaScript 中用 Object.freeze 实现不可变
const person = Object.freeze({
    name: "张三",
    age: 25
});
// person.age = 26;  // 静默失败（严格模式下报错）

// 函数式操作：创建新对象而不是修改
const original = { name: "张三", scores: [100, 90, 85] };
const updated = { ...original, name: "李四" };  // 新对象
console.log(original.name); // 张三（没变）
```

**为什么需要它：** 不可变数据天然线程安全，避免"改了一个地方，另一个地方也跟着变"的bug。

**与相关术语对比：** 不可变 vs 可变——不可变数据创建后不能修改（或修改产生新副本），可变数据可原地修改。

---

## 高阶函数（Higher-Order Function）

**一句话定义：** 高阶函数就是接收函数作为参数，或者返回一个函数作为结果的函数。

**通俗类比：** 就像一个"加工车间"——你送进去一个工具（函数），它帮你用这个工具加工别的东西。

**具体示例：**
```python
# 接收函数作为参数
def apply_twice(func, value):
    return func(func(value))

def double(x):
    return x * 2

print(apply_twice(double, 3))  # 12（3→6→12）

# 返回函数
def make_multiplier(n):
    return lambda x: x * n

double = make_multiplier(2)
triple = make_multiplier(3)
print(double(5))   # 10
print(triple(5))   # 15

# 常见高阶函数
nums = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x**2, nums))        # [1, 4, 9, 16, 25]
evens = list(filter(lambda x: x % 2 == 0, nums)) # [2, 4]
```

```javascript
// 接收函数作为参数
const applyTwice = (func, value) => func(func(value));
const double = x => x * 2;
console.log(applyTwice(double, 3)); // 12

// 返回函数
const makeMultiplier = (n) => (x) => x * n;
const double2 = makeMultiplier(2);
console.log(double2(5)); // 10

// 常见高阶函数
const nums = [1, 2, 3, 4, 5];
const squared = nums.map(x => x ** 2);    // [1, 4, 9, 16, 25]
const evens = nums.filter(x => x % 2 === 0); // [2, 4]
const sum = nums.reduce((a, b) => a + b, 0); // 15
```

**为什么需要它：** 高阶函数让代码更抽象、更灵活，是函数式编程的核心工具。

**与相关术语对比：** 高阶函数 vs 普通函数——普通函数接收值返回值，高阶函数可以接收/返回函数。

---

## Lambda 表达式

**一句话定义：** Lambda 就是没有名字的匿名函数，适合一次性使用的简短逻辑。

**通俗类比：** 就像临时工——不需要知道他的名字，只需要他干完活就走。

**具体示例：**
```python
# Lambda 表达式
square = lambda x: x ** 2
print(square(5))  # 25

# 常用于排序
students = [("张三", 85), ("李四", 92), ("王五", 78)]
students.sort(key=lambda s: s[1])  # 按成绩排序
print(students)  # [('王五', 78), ('张三', 85), ('李四', 92)]

# 作为高阶函数参数
nums = [1, 2, 3, 4, 5]
result = list(map(lambda x: x * 2, nums))
```

```javascript
// Lambda（箭头函数）
const square = x => x ** 2;
console.log(square(5)); // 25

// 常用场景
const nums = [3, 1, 4, 1, 5];
const sorted = [...nums].sort((a, b) => a - b);

const doubled = nums.map(x => x * 2);
const evens = nums.filter(x => x % 2 === 0);
```

**为什么需要它：** Lambda 让代码更简洁，特别适合传递给高阶函数的一次性逻辑。

**与相关术语对比：** Lambda vs 命名函数——Lambda 匿名且通常简短，命名函数有名字可复用；Lambda 常作为参数传递。

---

## 闭包（Closure）

**一句话定义：** 闭包就是函数"记住"了它被创建时的环境，即使外部函数已经执行完毕。

**通俗类比：** 就像你搬家了但还保留着老家的钥匙——虽然离开那个环境了，但还能回去拿东西。

**具体示例：**
```python
# 闭包
def make_counter():
    count = 0
    def counter():
        nonlocal count
        count += 1
        return count
    return counter

counter = make_counter()
print(counter())  # 1
print(counter())  # 2
print(counter())  3
# count 变量被 "关在" 闭包里，每次调用都能访问和修改
```

```javascript
// 闭包
function makeCounter() {
    let count = 0;
    return function() {
        count++;
        return count;
    };
}

const counter = makeCounter();
console.log(counter()); // 1
console.log(counter()); // 2
console.log(counter()); // 3
// count 在外部函数执行完后依然存在
```

```java
// Java 闭包（通过 Lambda 捕获 effectively final 变量）
public static Supplier<Integer> makeCounter() {
    int[] count = {0};  // 用数组绕过 final 限制
    return () -> count[0]++;
}

Supplier<Integer> counter = makeCounter();
System.out.println(counter.get()); // 0
System.out.println(counter.get()); // 1
```

**为什么需要它：** 闭包让函数可以携带状态，是实现数据私有化和函数工厂的强大工具。

**与相关术语对比：** 闭包 vs 全局变量——闭包的状态是私有的、函数级别的，全局变量是公共的、程序级别的。

---

## 柯里化（Currying）

**一句话定义：** 柯里化就是把一个多参数函数变成一系列单参数函数的过程。

**通俗类比：** 就像流水线——你先给第一个工人（参数1），他处理完交给第二个工人（参数2），最终得到结果。

**具体示例：**
```python
# 手动柯里化
def add(a):
    def add_b(b):
        return a + b
    return add_b

add_5 = add(5)    # 返回一个接收 b 的函数
print(add_5(3))   # 8
print(add_5(10))  # 15

# 通用柯里化装饰器
def curry(func):
    def curried(*args):
        if len(args) >= func.__code__.co_argcount:
            return func(*args)
        return lambda *more: curried(*args, *more)
    return curried

@curry
def add(a, b, c):
    return a + b + c

add_1 = add(1)
add_1_2 = add_1(2)
print(add_1_2(3))  # 6
```

```javascript
// 手动柯里化
const add = (a) => (b) => a + b;
const add5 = add(5);
console.log(add5(3));  // 8

// 通用柯里化函数
const curry = (fn) => {
    const curried = (...args) => {
        if (args.length >= fn.length) return fn(...args);
        return (...more) => curried(...args, ...more);
    };
    return curried;
};

const add3 = curry((a, b, c) => a + b + c);
console.log(add3(1)(2)(3)); // 6
console.log(add3(1, 2)(3)); // 6
```

**为什么需要它：** 柯里化方便创建特化函数，提升代码复用性，是函数组合的基础。

**与相关术语对比：** 柯里化 vs 偏应用——柯里化每次只传一个参数，偏应用可以一次传多个预设参数。

---

## 函数组合（Function Composition）

**一句话定义：** 函数组合就是把多个函数像管道一样串起来，前一个函数的输出作为后一个函数的输入。

**通俗类比：** 就像工厂流水线——原料经过一道工序变成半成品，再经过下一道工序变成成品。

**具体示例：**
```python
# 手动组合
def add_tax(price):
    return price * 1.1

def apply_discount(price):
    return price * 0.9

def format_price(price):
    return f"¥{price:.2f}"

# 管道式组合
def compose(*funcs):
    def composed(x):
        result = x
        for f in reversed(funcs):
            result = f(result)
        return result
    return composed

pipeline = compose(format_price, add_tax, apply_discount)
print(pipeline(100))  # ¥99.00（100→90→99→"¥99.00"）
```

```javascript
// 手动组合
const compose = (...fns) => (x) => fns.reduceRight((acc, fn) => fn(acc), x);
const pipe = (...fns) => (x) => fns.reduce((acc, fn) => fn(acc), x);

const addTax = price => price * 1.1;
const applyDiscount = price => price * 0.9;
const formatPrice = price => `¥${price.toFixed(2)}`;

const processPrice = pipe(applyDiscount, addTax, formatPrice);
console.log(processPrice(100)); // ¥99.00
```

**为什么需要它：** 函数组合让复杂逻辑由简单函数拼装而成，更易测试和维护。

**与相关术语对比：** compose 从右到左执行，pipe 从左到右执行；组合 vs 链式调用——组合是函数式的，链式调用是面向对象的。

---

## Monad（Maybe/Either/IO）

**一句话定义：** Monad 就是一个"容器"，它把值包起来，同时定义了如何把多个操作串联起来。

**通俗类比：** 就像一条传送带——每个包裹（值）都放在标准箱子里（Monad），传送带定义了箱子怎么传递和合并。

**具体示例：**
```python
# Maybe Monad（处理 null）
class Maybe:
    def __init__(self, value):
        self.value = value

    def is_nothing(self):
        return self.value is None

    def map(self, func):
        if self.is_nothing():
            return Maybe(None)
        return Maybe(func(self.value))

    def flat_map(self, func):
        if self.is_nothing():
            return Maybe(None)
        return func(self.value)

# 安全链式调用，不会因 None 报错
result = (Maybe(10)
    .map(lambda x: x * 2)
    .map(lambda x: x + 5)
    .map(lambda x: x / 0))  # 这里会出错

result = Maybe(None)
    .map(lambda x: x * 2)  # 自动跳过
    .map(lambda x: x + 5)  # 自动跳过
print(result.value)  # None（安全！）
```

```javascript
// Maybe Monad
const Maybe = (value) => ({
    isNothing: () => value === null || value === undefined,
    map: (fn) => value == null ? Maybe(null) : Maybe(fn(value)),
    flatMap: (fn) => value == null ? Maybe(null) : fn(value),
    getOrElse: (defaultVal) => value ?? defaultVal
});

const result = Maybe(10)
    .map(x => x * 2)
    .map(x => x + 5);
console.log(result.getOrElse(0)); // 25

// Either Monad（处理错误）
const Left = (value) => ({
    map: () => Left(value),
    flatMap: () => Left(value),
    isLeft: true
});

const Right = (value) => ({
    map: (fn) => Right(fn(value)),
    flatMap: (fn) => fn(value),
    isLeft: false
});

const divide = (a, b) => b === 0 ? Left("除以零") : Right(a / b);
console.log(divide(10, 2).map(x => x * 2)); // Right(10)
console.log(divide(10, 0).map(x => x * 2)); // Left("除以零")
```

**为什么需要它：** Monad 让错误处理、空值检查、副作用等变得优雅且可组合。

**与相关术语对比：** Maybe 处理空值，Either 处理错误/成功，IO 封装副作用；Monad vs Functor——Monad 可以 flatMap（展平嵌套），Functor 只能 map。

---

## Functor

**一句话定义：** Functor 就是一个可以被 map 的容器——你可以用函数去变换里面的值。

**通俗类比：** 就像一个透明盒子——你可以隔着盒子对里面的东西做操作，不需要打开它。

**具体示例：**
```python
# 列表就是 Functor
nums = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x**2, nums))
print(squared)  # [1, 4, 9, 16, 25]

# 自定义 Functor
class Box:
    def __init__(self, value):
        self.value = value

    def map(self, func):
        return Box(func(self.value))

    def __repr__(self):
        return f"Box({self.value})"

result = Box(5).map(lambda x: x * 2).map(lambda x: x + 1)
print(result)  # Box(11)
```

```javascript
// 数组就是 Functor
const nums = [1, 2, 3, 4, 5];
const squared = nums.map(x => x ** 2);
console.log(squared); // [1, 4, 9, 16, 25]

// Promise 也是 Functor
const fetchUser = (id) => Promise.resolve({ id, name: "张三" });
fetchUser(1).then(user => ({ ...user, age: 25 }));
```

**为什么需要它：** Functor 提供了统一的变换接口，让不同容器类型都能用 map 操作。

**与相关术语对比：** Functor 有 map 方法，Monad 有 flatMap 方法；Monad 是 Functor 的超集。

---

## Applicative

**一句话定义：** Applicative 就是一个"装在盒子里的函数"，可以应用到"装在盒子里的值"上。

**通俗类比：** 就像一个工具箱（装着函数）和一堆零件（装在盒子里的值）——你不需要拿出工具，直接隔着箱子操作。

**具体示例：**
```python
# Applicative 模式
class Box:
    def __init__(self, value):
        self.value = value

    def apply(self, other):
        if callable(self.value):
            return Box(self.value(other.value))
        return self

    def __repr__(self):
        return f"Box({self.value})"

# 普通函数
add = lambda x, y: x + y

# Functor：map 只能接收普通函数
# Applicative：可以接收 Box(函数)
boxed_add = Box(add)
result = boxed_add.apply(Box(3)).apply(Box(5))
print(result)  # Box(8)
```

```javascript
// JavaScript 中的应用函子
const Box = (value) => ({
    value,
    apply: (other) => Box(value(other.value)),
    map: (fn) => Box(fn(value))
});

const add = a => b => a + b;
const result = Box(add).apply(Box(3)).apply(Box(5));
console.log(result.value); // 8
```

**为什么需要它：** Applicative 让函数式编程能处理更复杂的组合场景，特别是涉及多个上下文时。

**与相关术语对比：** Functor 是单参数映射，Applicative 是双参数（函数+值）映射；Applicative 支持并行计算。

---

## 柯里化 vs 偏应用（Currying vs Partial Application）

**一句话定义：** 柯里化是把多参数函数转成一系列单参数函数的技术，偏应用是固定函数的部分参数生成新函数。

**通俗类比：** 柯里化像"一次只传一个球"，偏应用像"一次塞几个球进袋子然后拿走"。

**具体示例：**
```python
# 柯里化：每次传一个参数
def add(a):
    def add_b(b):
        return a + b
    return add_b

add_5 = add(5)
print(add_5(3))  # 8

# 偏应用：一次固定多个参数
from functools import partial

def add(a, b, c):
    return a + b + c

add_1_2 = partial(add, 1, 2)  # 固定 a=1, b=2
print(add_1_2(3))  # 6
```

```javascript
// 柯里化
const add = a => b => a + b;
const add5 = add(5);
console.log(add5(3)); // 8

// 偏应用（用 bind）
function add(a, b, c) { return a + b + c; }
const add12 = add.bind(null, 1, 2);
console.log(add12(3)); // 6
```

**为什么需要它：** 两者都方便创建特化函数，柯里化更系统化，偏应用更灵活。

**与相关术语对比：** 柯里化一定是逐个传参，偏应用可以一次固定任意多个参数；柯里化是偏应用的特例。

---

## 声明式编程 vs 命令式编程（Declarative vs Imperative）

**一句话定义：** 命令式关注"怎么做"（一步一步的指令），声明式关注"做什么"（描述期望结果）。

**通俗类比：** 命令式像"导航路线"——先左转、再直走、过两个红绿灯右转；声明式像"你要去哪"——告诉导航目的地就行。

**具体示例：**
```python
# 命令式
nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
evens = []
for n in nums:
    if n % 2 == 0:
        evens.append(n)

# 声明式
evens = [n for n in nums if n % 2 == 0]
# 或
evens = list(filter(lambda n: n % 2 == 0, nums))
```

```javascript
// 命令式
const nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const evens = [];
for (let i = 0; i < nums.length; i++) {
    if (nums[i] % 2 === 0) {
        evens.push(nums[i]);
    }
}

// 声明式
const evens2 = nums.filter(n => n % 2 === 0);

// SQL 也是声明式
// SELECT * FROM users WHERE age > 18 ORDER BY name;
```

**为什么需要它：** 声明式代码更简洁、更易读、更少出错，是函数式编程的风格特征。

**与相关术语对比：** 命令式控制流程（for/while/if），声明式描述数据转换（map/filter/reduce）；声明式更抽象，命令式更具体。

---

## 惰性求值（Lazy Evaluation）

**一句话定义：** 惰性求值就是"不到万不得已不算"——表达式只在真正需要其值时才被计算。

**通俗类比：** 就像外卖——你点餐时才开始做，不是提前做好等着。

**具体示例：**
```python
# Python 生成器是惰性求值
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

fib = fibonacci()
# 不会真的算出所有值，只在 next() 时才算
print(next(fib))  # 0
print(next(fib))  # 1
print(next(fib))  # 1
# 想要第100个值也不需要算前面99个

# 生成器表达式也是惰性的
squares = (x**2 for x in range(1000000))  # 不会立即计算所有值
print(next(squares))  # 0（按需计算）
```

```javascript
// JavaScript 迭代器协议实现惰性
function* fibonacci() {
    let a = 0, b = 1;
    while (true) {
        yield a;
        [a, b] = [b, a + b];
    }
}

const fib = fibonacci();
console.log(fib.next().value); // 0
console.log(fib.next().value); // 1

// 生成器管道
function* filter(iter, pred) {
    for (const item of iter) {
        if (pred(item)) yield item;
    }
}

function* map(iter, fn) {
    for (const item of iter) {
        yield fn(item);
    }
}

const naturals = (function*() { let i = 0; while (true) yield i++; })();
const result = map(filter(naturals, x => x % 2 === 0), x => x * 10);
// 前5个偶数乘以10：0, 20, 40, 60, 80
```

**为什么需要它：** 惰性求值节省内存和计算资源，特别适合处理无限序列和大数据流。

**与相关术语对比：** 惰性求值 vs 急切求值——惰性按需计算，急切立即计算所有值；Python 生成器是惰性的，列表是急切的。

## 相关术语

[[并发编程（Concurrent Programming）概念]]、[[面向对象编程（OOP）概念]]、[[Flutter跨平台开发实战]]、[[Go语言核心]]、[[Go语言系统编程指南]]、[[Python全栈开发教程]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
