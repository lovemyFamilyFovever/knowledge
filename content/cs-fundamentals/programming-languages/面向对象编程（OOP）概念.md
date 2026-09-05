---
title: "面向对象编程（OOP）概念"
tags: []
source: "baike"
source_path: "开发术语 / 编程语言基础"
collected: "2026-09-05"
status: "imported"
---

# 面向对象编程（OOP）概念

---

## 类（Class）

**一句话定义：** 类就是创建对象的"模板"或"蓝图"，定义了一类事物共有的属性和行为。

**通俗类比：** 类就像建筑图纸——按照同一张图纸可以盖出很多栋房子，每栋房子的结构相同，但住的人不同。

**具体示例：**
```python
class Dog:
    def __init__(self, name, age):
        self.name = name    # 属性
        self.age = age

    def bark(self):         # 方法
        return f"{self.name}：汪汪！"

# 创建对象
dog1 = Dog("旺财", 3)
dog2 = Dog("小黑", 5)
print(dog1.bark())  # 旺财：汪汪！
```

```javascript
class Dog {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }

    bark() {
        return `${this.name}：汪汪！`;
    }
}

const dog1 = new Dog("旺财", 3);
console.log(dog1.bark()); // 旺财：汪汪！
```

```java
class Dog {
    String name;
    int age;

    Dog(String name, int age) {
        this.name = name;
        this.age = age;
    }

    String bark() {
        return name + "：汪汪！";
    }
}

Dog dog1 = new Dog("旺财", 3);
```

**为什么需要它：** 类让代码模块化，同一类事物只需定义一次，可反复创建实例。

**与相关术语对比：** 类是抽象模板，对象是具体实例；类定义了"有什么"和"能做什么"。

---

## 对象（Object）

**一句话定义：** 对象就是根据类创建出来的"实体"，拥有具体的属性值和行为。

**通俗类比：** 如果类是"狗"这个概念，对象就是具体的"旺财"或"小黑"。

**具体示例：**
```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def introduce(self):
        return f"我叫{self.name}，{self.age}岁"

# 对象是类的实例
p1 = Person("张三", 25)
p2 = Person("李四", 30)

print(p1.introduce())  # 我叫张三，25岁
print(p2.introduce())  # 我叫李四，30岁
```

```javascript
class Person {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }
    introduce() { return `我叫${this.name}，${this.age}岁`; }
}

const p1 = new Person("张三", 25);
const p2 = new Person("李四", 30);
```

**为什么需要它：** 对象封装了数据和行为，是程序运行时的基本单元。

**与相关术语对比：** 对象 vs 类——类是蓝图，对象是根据蓝图造出来的实物；一个类可创建多个对象。

---

## 封装（Encapsulation）

**一句话定义：** 封装就是把数据和操作数据的方法"打包"在一起，对外只暴露必要的接口。

**通俗类比：** 就像ATM机——你看不到里面的钱是怎么存放的，只能通过屏幕上的按钮（接口）来存取。

**具体示例：**
```python
class BankAccount:
    def __init__(self, balance):
        self.__balance = balance  # 私有属性（双下划线）

    def deposit(self, amount):    # 公开方法
        if amount > 0:
            self.__balance += amount
            return True
        return False

    def withdraw(self, amount):
        if 0 < amount <= self.__balance:
            self.__balance -= amount
            return True
        return False

    def get_balance(self):
        return self.__balance

account = BankAccount(1000)
account.deposit(500)
print(account.get_balance())  # 1500
# account.__balance  # 报错！无法直接访问私有属性
```

```java
class BankAccount {
    private double balance;  // private 封装

    public void deposit(double amount) {
        if (amount > 0) balance += amount;
    }

    public double getBalance() {
        return balance;
    }
}
```

**为什么需要它：** 隐藏内部实现细节，防止外部代码随意修改内部状态，提高安全性。

**与相关术语对比：** 封装 vs 抽象——封装是"藏起来"，抽象是"简化概念"；封装关注访问控制，抽象关注本质提取。

---

## 继承（Inheritance）

**一句话定义：** 继承就是子类自动获得父类的属性和方法，同时可以添加自己特有的功能。

**通俗类比：** 就像孩子继承父母的基因，同时又有自己的特长。

**具体示例：**
```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."

class Dog(Animal):           # Dog 继承 Animal
    def speak(self):         # 重写父类方法
        return "汪汪！"

class Cat(Animal):
    def speak(self):
        return "喵喵！"

dog = Dog("旺财")
cat = Cat("咪咪")
print(dog.speak())  # 汪汪！
print(cat.speak())  # 喵喵！
print(dog.name)     # 旺财（继承自 Animal）
```

```javascript
class Animal {
    constructor(name) { this.name = name; }
    speak() { return "..."; }
}

class Dog extends Animal {
    speak() { return "汪汪！"; }
}

const dog = new Dog("旺财");
console.log(dog.speak()); // 汪汪！
```

```java
class Animal {
    String name;
    void speak() { System.out.println("..."); }
}

class Dog extends Animal {
    @Override
    void speak() { System.out.println("汪汪！"); }
}
```

**为什么需要它：** 避免重复代码，建立类之间的层次关系，实现代码复用。

**与相关术语对比：** 继承 vs 组合——继承是"是一个"关系（狗是动物），组合是"有一个"关系（汽车有引擎）。

---

## 多态（Polymorphism）

**一句话定义：** 多态就是同一个方法在不同对象上表现出不同的行为。

**通俗类比：** 同样是"叫"这个动作，狗叫"汪汪"，猫叫"喵喵"，鸟叫"叽叽"——同一个指令，不同的响应。

**具体示例：**
```python
class Shape:
    def area(self):
        pass

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius
    def area(self):
        return 3.14 * self.radius ** 2

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height
    def area(self):
        return self.width * self.height

# 多态：统一调用 area()
shapes = [Circle(5), Rectangle(4, 6)]
for shape in shapes:
    print(shape.area())  # 不同对象，不同结果
```

```javascript
class Shape {
    area() { return 0; }
}

class Circle extends Shape {
    constructor(r) { super(); this.r = r; }
    area() { return Math.PI * this.r ** 2; }
}

class Rectangle extends Shape {
    constructor(w, h) { super(); this.w = w; this.h = h; }
    area() { return this.w * this.h; }
}

const shapes = [new Circle(5), new Rectangle(4, 6)];
shapes.forEach(s => console.log(s.area()));
```

**为什么需要它：** 多态让代码更灵活，新增子类无需修改已有调用代码。

**与相关术语对比：** 多态 vs 重载——多态是运行时根据对象类型决定调用哪个方法，重载是编译时根据参数决定。

---

## 抽象（Abstraction）

**一句话定义：** 抽象就是只关注事物的核心特征，忽略不必要的细节。

**通俗类比：** 地图就是抽象——它只显示道路和地标，忽略了每棵树、每块石头的细节。

**具体示例：**
```python
from abc import ABC, abstractmethod

class Vehicle(ABC):      # 抽象类
    @abstractmethod
    def start(self):     # 抽象方法（只有声明，没有实现）
        pass

    @abstractmethod
    def stop(self):
        pass

class Car(Vehicle):
    def start(self):
        print("引擎启动")
    def stop(self):
        print("引擎熄火")

# v = Vehicle()  # 报错！不能实例化抽象类
car = Car()
car.start()  # 引擎启动
```

```java
abstract class Vehicle {
    abstract void start();  // 抽象方法
    abstract void stop();

    void commonMethod() {   // 普通方法可有实现
        System.out.println("通用方法");
    }
}

class Car extends Vehicle {
    void start() { System.out.println("引擎启动"); }
    void stop() { System.out.println("引擎熄火"); }
}
```

**为什么需要它：** 抽象让设计更聚焦核心，定义统一接口规范，隐藏复杂实现。

**与相关术语对比：** 抽象 vs 封装——抽象关注"做什么"，封装关注"怎么做"和"谁能访问"。

---

## 接口（Interface）

**一句话定义：** 接口就是一组方法签名的集合，规定了类必须实现哪些方法。

**通俗类比：** 接口就像USB标准——不管是U盘、键盘还是鼠标，只要符合USB标准就能插上用。

**具体示例：**
```python
from abc import ABC, abstractmethod

class Drawable(ABC):
    @abstractmethod
    def draw(self):
        pass

class Circle(Drawable):
    def draw(self):
        print("画一个圆")

class Square(Drawable):
    def draw(self):
        print("画一个正方形")

def draw_shape(shape: Drawable):
    shape.draw()  # 只要是 Drawable 都能调用

draw_shape(Circle())   # 画一个圆
draw_shape(Square())   # 画一个正方形
```

```javascript
// JavaScript 没有真正的接口，用鸭子类型模拟
class Circle {
    draw() { console.log("画圆"); }
}

class Square {
    draw() { console.log("画正方形"); }
}

// 只要有 draw() 方法就行
function drawShape(shape) { shape.draw(); }
```

```java
interface Drawable {
    void draw();  // 接口方法默认 public abstract
}

class Circle implements Drawable {
    @Override
    public void draw() { System.out.println("画圆"); }
}

class Square implements Drawable {
    @Override
    public void draw() { System.out.println("画正方形"); }
}
```

**为什么需要它：** 接口定义统一契约，让不相关的类可以互换使用，支持多态。

**与相关术语对比：** 接口 vs 抽象类——接口只能有抽象方法（Java 8+可有默认方法），抽象类可以有实现；一个类可实现多个接口，但只能继承一个类。

---

## 抽象类（Abstract Class）

**一句话定义：** 抽象类是不能直接实例化的类，它既可以有抽象方法（无实现），也可以有普通方法（有实现）。

**通俗类比：** 抽象类就像"半成品"——你不能直接用它，但继承它的子类可以补全剩下的部分。

**具体示例：**
```python
from abc import ABC, abstractmethod

class Database(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def query(self, sql):
        pass

    def close(self):          # 普通方法有实现
        print("连接已关闭")

class MySQL(Database):
    def connect(self):
        print("连接 MySQL")
    def query(self, sql):
        print(f"MySQL 执行: {sql}")

# db = Database()  # 报错！
db = MySQL()
db.connect()       # 连接 MySQL
db.close()         # 连接已关闭（继承自抽象类）
```

```java
abstract class Database {
    abstract void connect();
    abstract void query(String sql);

    void close() { System.out.println("连接已关闭"); }
}

class MySQL extends Database {
    void connect() { System.out.println("连接 MySQL"); }
    void query(String sql) { System.out.println("MySQL 执行: " + sql); }
}
```

**为什么需要它：** 抽象类提供部分通用实现，强制子类实现核心方法，兼顾灵活性和约束。

**与相关术语对比：** 抽象类 vs 接口——抽象类可以有字段和方法实现，接口通常只定义方法签名；抽象类用继承，接口用实现。

---

## 构造函数与析构函数

**一句话定义：** 构造函数在创建对象时自动调用（初始化），析构函数在对象销毁时自动调用（清理）。

**通俗类比：** 构造函数就像搬进新房时的"装修"，析构函数就像搬走时的"打扫"。

**具体示例：**
```python
class Resource:
    def __init__(self, name):       # 构造函数
        self.name = name
        print(f"{name} 资源已创建")

    def __del__(self):              # 析构函数
        print(f"{self.name} 资源已释放")

r = Resource("数据库连接")
# 输出：数据库连接 资源已创建
del r
# 输出：数据库连接 资源已释放
```

```javascript
class Resource {
    constructor(name) {             // 构造函数
        this.name = name;
        console.log(`${name} 资源已创建`);
    }

    destroy() {                     // JS 没有真正的析构函数
        console.log(`${this.name} 资源已释放`);
    }
}
```

```java
class Resource {
    Resource(String name) {         // 构造函数
        System.out.println(name + " 已创建");
    }

    @Override
    protected void finalize() {     // 析构函数（不推荐使用）
        System.out.println("资源已释放");
    }
}
```

**为什么需要它：** 构造函数确保对象初始化完整，析构函数确保资源（内存、文件、连接）被正确释放。

**与相关术语对比：** 构造函数在对象诞生时执行，析构函数在对象死亡时执行；构造函数可重载，析构函数通常只有一个。

---

## 方法重载（Overload）与方法重写（Override）

**一句话定义：** 重载是在同一个类里定义多个同名但参数不同的方法；重写是子类重新定义父类的同名方法。

**通俗类比：** 重载就像"点餐"——都叫"点餐"，但点汉堡和点披萨的参数不同；重写就像"改菜单"——餐厅换了厨师，同一道菜做法变了。

**具体示例：**
```python
# Python 不支持传统重载，用默认参数模拟
class Calculator:
    def add(self, a, b, c=0):
        return a + b + c

calc = Calculator()
print(calc.add(1, 2))      # 3
print(calc.add(1, 2, 3))   # 6

# 方法重写
class Animal:
    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):        # 重写
        return "汪汪！"
```

```javascript
// JS 不支持重载，用 ...args 模拟
class Calculator {
    add(...args) {
        return args.reduce((a, b) => a + b, 0);
    }
}

// 方法重写
class Animal {
    speak() { return "..."; }
}
class Dog extends Animal {
    speak() { return "汪汪！"; }  // 重写
}
```

```java
// 方法重载（Overload）——同一类，参数不同
class Calculator {
    int add(int a, int b) { return a + b; }
    double add(double a, double b) { return a + b; }
    int add(int a, int b, int c) { return a + b + c; }
}

// 方法重写（Override）——子类覆盖父类方法
class Animal {
    String speak() { return "..."; }
}
class Dog extends Animal {
    @Override
    String speak() { return "汪汪！"; }
}
```

**为什么需要它：** 重载提供灵活的调用方式，重写实现多态和定制化行为。

**与相关术语对比：** 重载发生在同一个类，方法名相同参数不同；重写发生在父子类，方法签名完全相同。

---

## 访问修饰符（Access Modifiers）

**一句话定义：** 访问修饰符控制类、属性、方法能被哪些代码访问。

**通俗类比：** 就像房子的门——大门（public）谁都能进，卧室门（private）只有家人能进，院门（protected）邻居也能进。

**具体示例：**
```python
class Person:
    def __init__(self, name, age, secret):
        self.name = name          # public（公开）
        self._age = age           # protected（约定，技术上可访问）
        self.__secret = secret    # private（双下划线，名称改写）

p = Person("张三", 25, "密码123")
print(p.name)       # 张三（公开）
print(p._age)       # 25（约定保护，技术上可访问）
# print(p.__secret)  # 报错（私有）
```

```javascript
class Person {
    #secret;  // 私有字段（ES2022+）

    constructor(name, secret) {
        this.name = name;        // 公开
        this._age = 25;          // 约定保护
        this.#secret = secret;   // 真正私有
    }
}
```

```java
public class Person {
    public String name;         // 公开
    protected int age;          // 子类和同包可访问
    private String secret;      // 仅本类可访问
    String address;             // 默认（包级别）

    public void show() { }
    private void hide() { }
}
```

**为什么需要它：** 控制访问权限，保护内部数据，实现封装。

**与相关术语对比：** public 全部可见，protected 子类和同包可见，private 仅本类可见，default（Java）仅同包可见。

---

## 组合 vs 继承（Composition vs Inheritance）

**一句话定义：** 继承是"是一个"（is-a）关系，组合是"有一个"（has-a）关系。

**通俗类比：** 继承就像孩子是父母的"翻版"，组合就像汽车由引擎、轮胎等零件"拼装"而成。

**具体示例：**
```python
# 继承：Dog is an Animal
class Animal:
    def speak(self): pass

class Dog(Animal):  # Dog 是 Animal
    def speak(self):
        return "汪汪！"

# 组合：Car has an Engine
class Engine:
    def start(self):
        return "引擎启动"

class Car:
    def __init__(self):
        self.engine = Engine()  # Car 包含 Engine

    def start(self):
        return self.engine.start()
```

```javascript
// 继承
class Animal { speak() {} }
class Dog extends Animal { speak() { return "汪汪！"; } }

// 组合
class Engine { start() { return "引擎启动"; } }
class Car {
    constructor() { this.engine = new Engine(); }
    start() { return this.engine.start(); }
}
```

**为什么需要它：** 优先使用组合可以降低耦合度，让代码更灵活、更易测试。

**与相关术语对比：** 继承耦合度高（父类改子类可能崩），组合耦合度低（替换组件不影响整体）。

---

## 里氏替换原则（Liskov Substitution Principle, LSP）

**一句话定义：** 如果 S 是 T 的子类，那么在任何需要 T 的地方都可以用 S 替换，而不会出错。

**通俗类比：** 如果"电动车"是"车"的子类，那么任何需要"车"的地方都应该能用"电动车"来代替。

**具体示例：**
```python
class Bird:
    def fly(self):
        return "飞翔"

class Sparrow(Bird):
    def fly(self):
        return "麻雀飞翔"  # ✅ 符合 LSP

class Penguin(Bird):
    def fly(self):
        raise Exception("企鹅不会飞")  # ❌ 违反 LSP！
```

```javascript
// 正确示例：遵守 LSP
class Shape {
    area() { return 0; }
}

class Circle extends Shape {
    constructor(r) { super(); this.r = r; }
    area() { return Math.PI * this.r ** 2; }
}

class Rectangle extends Shape {
    constructor(w, h) { super(); this.w = w; this.h = h; }
    area() { return this.w * this.h; }
}

// 任何 Shape 的地方都可以安全地使用 Circle 或 Rectangle
function getArea(shape) { return shape.area(); }
```

**为什么需要它：** LSP 是面向对象设计的基本原则，保证继承体系的正确性和可替换性。

**与相关术语对比：** LSP 是 SOLID 原则之一，关注子类能否安全替换父类；与开闭原则（对扩展开放、对修改关闭）紧密相关。
