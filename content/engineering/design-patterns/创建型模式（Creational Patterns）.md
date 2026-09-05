---
title: "创建型模式（Creational Patterns）"
tags: []
source: "baike"
source_path: "开发术语 / 设计模式"
collected: "2026-09-05"
status: "imported"
---

# 创建型模式（Creational Patterns）

> 创建型模式关注的是**对象的创建机制**，试图以适合当前情况的方式创建对象，而不是直接 new 一个对象。它们将对象的创建和使用分离，让系统更灵活、更容易扩展。

---

## 1. 单例模式（Singleton）

### 一句话定义

整个程序运行期间，某个类**只能有一个实例**，谁来要都给同一个。

### 通俗类比

就像公司里的公章——全公司只有一枚，谁需要盖章都得找同一个地方取，盖完了还回去。你不能自己刻一枚新的。

### 具体示例

#### Java — 双重检查锁实现

```java
public class Singleton {
    private static volatile Singleton instance;

    private Singleton() {}

    public static Singleton getInstance() {
        if (instance == null) {                // 第一次检查，避免不必要的同步
            synchronized (Singleton.class) {
                if (instance == null) {        // 第二次检查，防止重复创建
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

#### Java — 静态内部类实现

```java
public class Singleton {
    private Singleton() {}

    private static class Holder {
        static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE;
    }
}
```

#### Java — 枚举实现（最简洁，天然防止反射和序列化破坏）

```java
public enum Singleton {
    INSTANCE;

    public void doSomething() {
        System.out.println("执行业务逻辑");
    }
}

// 使用
Singleton.INSTANCE.doSomething();
```

#### Python — 模块级单例

```python
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

s1 = Singleton()
s2 = Singleton()
print(s1 is s2)  # True
```

### 为什么需要它

- 数据库连接池只需要维护一个
- 配置管理器全局共享同一份配置
- 日志记录器避免重复打开文件句柄

### 与相关术语的对比

| 对比项 | 单例模式 | 全局变量 |
|--------|----------|----------|
| 生命周期 | 可控，支持懒加载 | 程序启动就存在 |
| 线程安全 | 需要额外处理 | 本身不保证 |
| 可测试性 | 可通过接口替换 | 全局耦合，难测试 |

---

## 2. 工厂方法模式（Factory Method）

### 一句话定义

定义一个创建对象的**接口**，但让子类决定实例化哪个类。

### 通俗类比

你去餐厅说"来一份套餐"，但具体是汉堡套餐还是炸鸡套餐，由各个分店自己决定。你不需要知道厨房怎么操作。

### 具体示例

```python
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "汪汪汪"

class Cat(Animal):
    def speak(self):
        return "喵喵喵"

# 工厂方法
class AnimalFactory(ABC):
    @abstractmethod
    def create_animal(self) -> Animal:
        pass

class DogFactory(AnimalFactory):
    def create_animal(self) -> Animal:
        return Dog()

class CatFactory(AnimalFactory):
    def create_animal(self) -> Animal:
        return Cat()

# 使用
factory = DogFactory()
animal = factory.create_animal()
print(animal.speak())  # 汪汪汪
```

### 为什么需要它

当新增一种动物时，只需要新增一个工厂类，不修改已有代码，符合**开闭原则**。

### 与相关术语的对比

| 对比项 | 工厂方法 | 简单工厂 | 抽象工厂 |
|--------|----------|----------|----------|
| 创建方式 | 每个产品一个工厂 | 一个工厂通过参数区分 | 一个工厂创建一族产品 |
| 扩展方式 | 新增产品需新增工厂 | 修改工厂类 switch | 新增产品族需新增工厂 |
| 复杂度 | 中等 | 低 | 高 |

---

## 3. 抽象工厂模式（Abstract Factory）

### 一句话定义

提供一个接口，用于创建**一族相关或相互依赖**的对象，而不需要指定具体类。

### 通俗类比

装修房子时，你选了"北欧风"，地板、窗帘、沙发、灯具都是北欧风格的，它们是一个整体。你不需要分别指定每件家具的风格。

### 具体示例

```python
from abc import ABC, abstractmethod

# 抽象产品
class Button(ABC):
    @abstractmethod
    def render(self): pass

class TextBox(ABC):
    @abstractmethod
    def render(self): pass

# 具体产品 - Windows 风格
class WindowsButton(Button):
    def render(self): return "Windows 按钮"

class WindowsTextBox(TextBox):
    def render(self): return "Windows 文本框"

# 具体产品 - Mac 风格
class MacButton(Button):
    def render(self): return "Mac 按钮"

class MacTextBox(TextBox):
    def render(self): return "Mac 文本框"

# 抽象工厂
class UIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button: pass
    @abstractmethod
    def create_textbox(self) -> TextBox: pass

# 具体工厂
class WindowsUIFactory(UIFactory):
    def create_button(self): return WindowsButton()
    def create_textbox(self): return WindowsTextBox()

class MacUIFactory(UIFactory):
    def create_button(self): return MacButton()
    def create_textbox(self): return MacTextBox()
```

### 为什么需要它

确保同一族的产品风格一致（不会出现 Windows 按钮配 Mac 文本框），切换产品族只需要换一个工厂。

### 与工厂方法的区别

工厂方法关注**单个产品**的创建，抽象工厂关注**一族产品**的搭配。

---

## 4. 建造者模式（Builder）

### 一句话定义

将一个复杂对象的**构建过程**和**表示**分离，同样的构建过程可以创建不同的表示。

### 通俗类比

点奶茶：选杯型 → 选糖度 → 选加料 → 选温度 → 下单。每一步都是独立的，顺序固定但每步可以不同，最后组装成一杯定制奶茶。

### 具体示例

#### 链式调用（Java 风格）

```java
public class Computer {
    private String cpu;
    private String ram;
    private String storage;

    private Computer() {}

    public static class Builder {
        private Computer computer = new Computer();

        public Builder cpu(String cpu) { computer.cpu = cpu; return this; }
        public Builder ram(String ram) { computer.ram = ram; return this; }
        public Builder storage(String s) { computer.storage = s; return this; }
        public Computer build() { return computer; }
    }
}

// 使用
Computer pc = new Computer.Builder()
    .cpu("i9-13900K")
    .ram("32GB")
    .storage("1TB SSD")
    .build();
```

#### Director 角色（预定义构建流程）

```python
class MealDirector:
    def construct(self, builder):
        builder.add_main_course()
        builder.add_side()
        builder.add_drink()
        return builder.build()
```

### 为什么需要它

当一个对象有多种可选配置时，避免出现"构造函数参数爆炸"（telescoping constructor）的问题。

### 与相关术语的对比

| 对比项 | 建造者模式 | 工厂方法 | 抽象工厂 |
|--------|-----------|----------|----------|
| 关注点 | 构建过程的步骤 | 创建单个对象 | 创建一族对象 |
| 返回结果 | 完整的复杂对象 | 单一产品 | 一族产品 |
| 可选参数 | 天然支持 | 不方便 | 不适用 |

---

## 5. 原型模式（Prototype）

### 一句话定义

通过**复制已有对象**来创建新对象，而不是从头构建。

### 通俗类比

考试时，老师给你一份试卷的复印件。复印件和原件内容一样，但它们是独立的两份——你在复印件上涂改不会影响原件。

### 具体示例

#### Python — 深拷贝 vs 浅拷贝

```python
import copy

class Address:
    def __init__(self, city, street):
        self.city = city
        self.street = street

class Person:
    def __init__(self, name, address):
        self.name = name
        self.address = address

p1 = Person("张三", Address("北京", "长安街"))

# 浅拷贝 — 地址对象是同一个引用
p2 = copy.copy(p1)
print(p1.address is p2.address)  # True

# 深拷贝 — 完全独立
p3 = copy.deepcopy(p1)
print(p1.address is p3.address)  # False
```

#### Java — 通过序列化实现深拷贝

```java
public class Prototype implements Cloneable, Serializable {
    @Override
    public Prototype clone() throws CloneNotSupportedException {
        return (Prototype) super.clone();
    }

    // 通过序列化实现深拷贝
    public Prototype deepClone() throws Exception {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        ObjectOutputStream oos = new ObjectOutputStream(bos);
        oos.writeObject(this);

        ByteArrayInputStream bis = new ByteArrayInputStream(bos.toByteArray());
        ObjectInputStream ois = new ObjectInputStream(bis);
        return (Prototype) ois.readObject();
    }
}
```

### 为什么需要它

创建对象的成本很高（如涉及网络请求、数据库查询、大量计算）时，复制已有对象更高效。

### 深拷贝 vs 浅拷贝

| 类型 | 说明 | 类比 |
|------|------|------|
| 浅拷贝 | 基本类型复制值，引用类型复制地址 | 复印纸质文件（内容一样，但附带的便签纸是同一张） |
| 深拷贝 | 所有字段都完全独立 | 拍照后重新打印一份（连便签纸也复制了） |

---

## 6. 对象池模式（Object Pool）

### 一句话定义

预先创建一批对象放在"池子"里反复使用，用完归还，而不是每次都创建和销毁。

### 通俗类比

共享单车——你不需要每次出行都买一辆新车，用完还到指定地点，下一个人接着用。如果所有车都骑走了，才会制造新车。

### 具体示例

```python
import queue

class ObjectPool:
    def __init__(self, creator, max_size=10):
        self._pool = queue.Queue(maxsize=max_size)
        self._creator = creator
        for _ in range(max_size):
            self._pool.put(creator())

    def acquire(self):
        return self._pool.get()

    def release(self, obj):
        self._pool.put(obj)

# 使用
pool = ObjectPool(creator=lambda: {"conn": "数据库连接"}, max_size=5)
conn = pool.acquire()   # 从池中取一个
# ... 使用连接 ...
pool.release(conn)       # 归还
```

### 为什么需要它

- 数据库连接创建和销毁开销极大
- 线程创建需要系统资源
- 网络连接建立耗时

### 与相关术语的对比

| 对比项 | 对象池 | 单例 | 工厂 |
|--------|--------|------|------|
| 对象数量 | 多个（有上限） | 一个 | 按需创建 |
| 复用方式 | 借用-归还 | 全局共享 | 用完即弃 |
| 适用场景 | 高频创建销毁的对象 | 全局唯一实例 | 灵活创建不同对象 |

---

## 总结

```
创建型模式
├── 单例模式 ——— 保证只有一个实例
├── 工厂方法 ——— 让子类决定创建什么
├── 抽象工厂 ——— 创建一族相关产品
├── 建造者模式 ——— 分步构建复杂对象
├── 原型模式 ——— 复制已有对象
└── 对象池模式 ——— 复用昂贵对象
```

> **选择建议**：先从简单工厂开始，当需要扩展时升级到工厂方法；当产品成族出现时用抽象工厂；对象创建开销大时考虑原型模式或对象池；全局唯一实例用单例；复杂对象构建用建造者。
