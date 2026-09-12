---
title: "创建型模式（Creational Patterns）"
tags: ["设计模式", "创建型模式", "GoF", "面向对象设计"]
source: "baike"
source_path: "开发术语 / 设计模式"
collected: "2026-09-05"
status: "imported"
---

# 创建型模式（Creational Patterns）


> 📌 **导航**：本文是 **创建型模式（Creational Patterns）** 词条，属于 design-patterns 术语集。相关枢纽：[[创建型模式（Creational Patterns）]]、[[结构型模式（Structural Patterns）]]、[[行为型模式（Behavioral Patterns）]]。

> 创建型模式（Creational Patterns）关注**对象的创建机制**：把「创建什么对象、由谁创建、何时创建」从业务代码中解耦出来，用比直接 `new` 更灵活的方式组织实例化过程。其核心目标是让系统依赖抽象而非具体类，从而更容易扩展、替换与测试。

---

## 概述与背景

「设计模式」一词在软件领域由「四人帮」（Gang of Four，GoF）在其 1994 年的著作《设计模式：可复用面向对象软件的基础》中系统化提出。该书共收录 **23 种**经典设计模式，按目的分为三类：

| 分类 | 关注点 | 数量 | 代表模式 |
|------|--------|------|----------|
| 创建型（Creational） | 对象的创建机制 | 5 | 单例、工厂方法、抽象工厂、建造者、原型 |
| 结构型（Structural） | 类与对象的组合 | 7 | 适配器、装饰器、代理、外观…… |
| 行为型（Behavioral） | 对象间的职责与通信 | 11 | 观察者、策略、模板方法、命令…… |

GoF 的 5 种创建型模式为：**抽象工厂、建造者、工厂方法、原型、单例**。本文额外收录工程实践中常与它们并列讨论的 **对象池（Object Pool）**——它并非 GoF 23 种模式之一，其确切来源与归属在不同文献中说法不一（**建议人工核验**：可参考 PLoP（Pattern Languages of Programs）系列、Mark Grand《Patterns in Java》等模式目录）。

创建型模式共同要解决的问题：

- **解耦创建与使用**：调用方只依赖抽象接口，不关心具体类。
- **封装创建复杂度**：把「选哪个实现、如何装配」的细节收敛到一处。
- **支持开闭原则（OCP）**：新增产品类型时尽量不修改已有代码。
- **控制实例的生命周期与数量**：如全局唯一（单例）、复用昂贵对象（对象池）。

---

## 1. 单例模式（Singleton）

### 一句话定义

保证一个类**在其生命周期内仅有一个实例**，并由该类自身向整个系统提供一个访问此实例的**全局访问点**。

### 通俗类比

就像一家公司的公章——全公司只有一枚，任何部门盖章都要到同一个地方领用、用完归还，不允许任何人私自再刻一枚。公章的「唯一性」由制度（私有构造 + 统一发放点）强制保证，而非依赖使用者自觉。

### 结构与角色

- **Singleton 类**：定义私有构造函数（阻止外部 `new`），持有一个指向自身唯一实例的静态引用，并提供一个公共静态方法（如 `getInstance()`）作为全局访问点。
- **全局访问点**：所有客户端都通过该静态方法获得**同一个**实例。
- **关键约束**：唯一性必须由**类自身**保证，而不是依赖调用方不去重复创建。

### 具体示例

#### Java — 双重检查锁（DCL）

```java
public class Singleton {
    // volatile 必不可少：禁止指令重排序，保证其他线程看到已完成初始化的对象
    private static volatile Singleton instance;

    private Singleton() {}

    public static Singleton getInstance() {
        if (instance == null) {                // 第一次检查：已初始化则免加锁，提升性能
            synchronized (Singleton.class) {
                if (instance == null) {        // 第二次检查：防止多线程重复创建
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

> 说明：`new Singleton()` 在字节码层面并非原子操作（分配内存 → 初始化对象 → 将引用赋值三步）。若不加 `volatile`，可能发生指令重排序，使其他线程拿到「引用已赋值但对象尚未初始化完成」的半成品。DCL 只有在 Java 5（JSR-133 修订内存模型）之后配合 `volatile` 才是正确的。

#### Java — 静态内部类（Initialization-on-demand Holder）

```java
public class Singleton {
    private Singleton() {}

    private static class Holder {
        static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE;   // 首次调用 getInstance 时才触发 Holder 类加载
    }
}
```

> 说明：利用 JVM 类加载机制——静态内部类 `Holder` 只有在第一次被主动使用时才会加载，而类初始化过程由 JVM 保证线程安全（JLS 12.4.2）。因此它同时具备**懒加载**与**线程安全**，且无需显式加锁，是纯 Java 环境下推荐的写法之一。

#### Java — 枚举（最简洁，天然防反射与序列化破坏）

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

> 说明：枚举天然保证单例——JVM 保证每个枚举常量只被实例化一次；枚举的序列化按规范只写出常量名（而非字段），反序列化时按名查找，因此**不会因序列化产生第二个实例**；反射也无法实例化枚举类型（`Constructor.newInstance` 对枚举会抛 `IllegalArgumentException`）。Joshua Bloch 在《Effective Java》Item 3 中指出，单元素枚举类型已成为实现 Singleton 的最佳方法。局限：不能懒加载，且无法继承其他类。

#### Python — 重写 `__new__`（注意其缺陷）

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

> 说明：这种写法有两个隐患——① 每次 `Singleton()` 仍会调用 `__init__`，若其中有副作用会被重复执行；② 多线程下 `if cls._instance is None` 与赋值之间存在竞态，**并非线程安全**。Python 中更稳妥的单例是**模块级实例**（模块只会被导入一次，`sys.modules` 缓存保证唯一），或使用 `threading.Lock` 加锁的元类实现。

### 为什么需要它（应用场景）

- 数据库连接池、线程池等资源管理器，全局只需一份统一调度。
- 配置管理器 / 全局注册表，共享同一份状态。
- 日志记录器，避免重复打开文件句柄、便于统一串行写入。
- 硬件或系统资源的访问点（如打印后台、窗口管理器）。

### 优点与局限

**优点**

- 严格控制实例数量，节省频繁创建 / 销毁的开销。
- 提供统一的全局访问点，避免资源被重复占用。

**局限 / 代价**

- **引入全局状态**：造成隐式耦合，依赖不透明，违反依赖倒置原则。
- **可测试性差**：难以被 mock / 替换，单元测试易受执行顺序影响。
- **职责过重风险**：容易演变成「什么都往里塞」的上帝对象，违反单一职责原则。
- **并发与生命周期**：需自行处理线程安全；懒加载、销毁时机、序列化 / 反射破坏单例都是常见坑。

### 常见误区

- ❌「单例就是全局变量的高级说法，可随意使用」——单例同样带来全局状态的耦合与测试困难，**应克制使用**，很多场景可用依赖注入替代。
- ❌「DCL 不加 `volatile` 也没问题」——错，缺 `volatile` 时重排序会让其他线程拿到未初始化完成的对象。
- ❌「私有构造函数就万无一失」——反射、序列化、克隆都可能绕过约束（枚举实现能规避反射与序列化）。

### 与相关术语的对比

| 对比项 | 单例模式 | 全局变量 / 静态类 |
|--------|----------|-------------------|
| 实例数量 | 恰好一个（类自身保证） | 一份全局状态 |
| 生命周期 | 可控，支持懒加载 | 程序启动即存在 |
| 多态 / 可替换 | 可通过接口、子类替换实现 | 难以替换，硬编码依赖 |
| 线程安全 | 需自行实现（Holder / 枚举 / 加锁） | 本身不保证 |
| 可测试性 | 差（可借接口缓解） | 差，全局耦合 |

---

## 2. 工厂方法模式（Factory Method）

### 一句话定义

定义一个用于创建对象的接口，但**由子类决定实例化哪一个类**；工厂方法把类的实例化时机延迟到子类完成。

### 通俗类比

你去连锁餐厅点「一份套餐」，但具体做成汉堡套餐还是炸鸡套餐，由不同分店（子类）按本地口味决定。你只依赖「套餐」这个抽象，不必知道后厨怎么操作。

### 结构与角色

- **Product（产品接口）**：所有被创建对象的公共抽象（如 `Animal`）。
- **ConcreteProduct（具体产品）**：Product 的具体实现（如 `Dog`、`Cat`）。
- **Creator（抽象创建者）**：声明工厂方法，返回类型为 Product。
- **ConcreteCreator（具体创建者）**：重写工厂方法，返回某个 ConcreteProduct。

### 具体示例

```python
from abc import ABC, abstractmethod

# —— 产品层次 ——
class Animal(ABC):
    @abstractmethod
    def speak(self) -> str: ...

class Dog(Animal):
    def speak(self) -> str: return "汪汪汪"

class Cat(Animal):
    def speak(self) -> str: return "喵喵喵"

# —— 创建者层次 ——
class AnimalFactory(ABC):
    @abstractmethod
    def create_animal(self) -> Animal:
        """工厂方法：把实例化延迟到子类"""
        ...

class DogFactory(AnimalFactory):
    def create_animal(self) -> Animal: return Dog()

class CatFactory(AnimalFactory):
    def create_animal(self) -> Animal: return Cat()

# 使用：客户端只依赖抽象
factory: AnimalFactory = DogFactory()
animal = factory.create_animal()
print(animal.speak())  # 汪汪汪
```

### 为什么需要它（应用场景）

- 一个类无法预先知道它要创建的对象的具体类型（如运行时按配置 / 文件类型选择解析器）。
- 希望把「创建哪种产品」的决策下放给子类，框架只约定接口（如日志框架的 Appender、ORM 的数据库方言工厂）。
- 需要以**开闭原则**扩展系统：新增产品时只增加新的 Creator + Product，不改动已有工厂逻辑。

### 优点与局限

**优点**

- 创建与使用解耦，客户端只依赖 Product 抽象。
- 新增产品符合开闭原则，扩展成本低。
- 每个具体创建者职责单一、清晰。

**局限**

- 每新增一种产品就要新增一个对应的工厂子类，**类的数量成对增长**，系统复杂度上升。
- 引入抽象层，代码可读性与调试成本增加。

### 常见误区

- ❌ 把「简单工厂」当成工厂方法。**简单工厂（Simple Factory）不是 GoF 模式**，它用一个工厂类 + 参数 `switch`/`if` 决定创建哪种产品，新增产品时要**修改**工厂（违反开闭原则）；工厂方法则是**新增子类**来扩展。
- ❌ 认为工厂方法必须「每次返回全新对象」。工厂方法也可返回缓存 / 复用的对象，其本质是「把实例化延迟到子类」。

### 与相关术语的对比

| 对比项 | 工厂方法 | 简单工厂（非 GoF） | 抽象工厂 |
|--------|----------|--------------------|----------|
| 产品维度 | 单个产品等级 | 单个产品等级 | 一族（多个等级）产品 |
| 创建方式 | 每个产品一个工厂子类 | 一个工厂按参数分支 | 一个工厂创建整族产品 |
| 扩展方式 | 新增产品 = 新增子类（不改旧代码） | 新增产品 = 修改工厂分支 | 新增产品族 = 新增工厂；新增产品种类 = 改所有工厂 |
| 是否符合开闭 | 是 | 否 | 对产品族是，对产品种类否 |
| 复杂度 | 中 | 低 | 高 |

---

## 3. 抽象工厂模式（Abstract Factory）

### 一句话定义

提供一个接口，用于创建**一系列相关或相互依赖的对象（产品族）**，而无需指定它们的具体类。

### 通俗类比

装修时你选定「北欧风」，地板、窗帘、沙发、灯具会自动都是北欧风格的成套搭配；换成「工业风」只需切换一个「风格工厂」，整族产品随之统一替换，不会出现北欧沙发配工业风灯具的混搭。

### 结构与角色

- **AbstractFactory（抽象工厂）**：声明一组创建各抽象产品的方法。
- **ConcreteFactory（具体工厂）**：实现上述方法，产出同一产品族的具体产品。
- **AbstractProduct（抽象产品）**：某一类产品接口（如 `Button`、`TextBox`）。
- **ConcreteProduct（具体产品）**：具体实现（如 `WindowsButton`、`MacButton`）。
- **Client（客户端）**：只通过抽象工厂与抽象产品接口使用对象，不接触具体类。

关键概念：**产品族**（同一工厂产出的一组相关产品，如「Windows 风格」全套控件）与 **产品等级**（同一抽象产品的不同实现，如所有 `Button`）。

### 具体示例

```python
from abc import ABC, abstractmethod

# —— 抽象产品（两个产品等级）——
class Button(ABC):
    @abstractmethod
    def render(self) -> str: ...

class TextBox(ABC):
    @abstractmethod
    def render(self) -> str: ...

# —— 具体产品：Windows 族 ——
class WindowsButton(Button):
    def render(self) -> str: return "Windows 按钮"

class WindowsTextBox(TextBox):
    def render(self) -> str: return "Windows 文本框"

# —— 具体产品：Mac 族 ——
class MacButton(Button):
    def render(self) -> str: return "Mac 按钮"

class MacTextBox(TextBox):
    def render(self) -> str: return "Mac 文本框"

# —— 抽象工厂 ——
class UIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button: ...
    @abstractmethod
    def create_textbox(self) -> TextBox: ...

# —— 具体工厂 ——
class WindowsUIFactory(UIFactory):
    def create_button(self) -> Button: return WindowsButton()
    def create_textbox(self) -> TextBox: return WindowsTextBox()

class MacUIFactory(UIFactory):
    def create_button(self) -> Button: return MacButton()
    def create_textbox(self) -> TextBox: return MacTextBox()

# 客户端：切换工厂即可整族替换
def build_ui(factory: UIFactory):
    print(factory.create_button().render(), factory.create_textbox().render())

build_ui(MacUIFactory())   # Mac 按钮 Mac 文本框
```

### 为什么需要它（应用场景）

- 系统需要在多套「风格 / 平台 / 供应商」之间整体切换（跨平台 UI、不同数据库驱动族、不同支付渠道套件）。
- 需要**强制约束一组对象搭配使用**，防止把不同族的产品混在一起。
- 对外只暴露抽象接口，隐藏具体产品的实现细节。

### 优点与局限

**优点**

- 保证同族产品的一致性，杜绝错误混搭。
- 切换产品族只需替换一个工厂，符合开闭原则（针对「族」维度）。
- 客户端与具体类彻底解耦。

**局限**

- **新增产品等级困难**：若要给所有工厂都增加一种新产品（如新增 `Checkbox`），必须修改抽象工厂接口及全部具体工厂，**违反开闭原则**。
- 抽象层次多，初期设计与理解成本高。

### 常见误区

- ❌ 把抽象工厂当成「返回多个对象的工厂方法」。区别在于抽象工厂强调**一族相互关联的产品**，而工厂方法针对**单个产品等级**。
- ❌ 认为抽象工厂「任何维度都能开闭扩展」。它对**新增产品族**友好，对**新增产品等级**很不友好。

### 与工厂方法的区别

工厂方法关注**单个产品**的创建（一个工厂方法产一种产品，靠新增子类扩展）；抽象工厂关注**一族产品**的搭配（一个工厂暴露多个创建方法，产出成套产品）。抽象工厂内部通常由多个工厂方法组成，也可用原型或直接 `new` 实现。

---

## 4. 建造者模式（Builder）

### 一句话定义

将一个复杂对象的**构建过程**与其**表示（最终产物）**分离，使同样的分步构建流程可以产出不同的表示。

### 通俗类比

点奶茶：选杯型 → 选糖度 → 选加料 → 选温度 → 出杯。每一步独立、顺序可控，不同的选择组合最后装配成不同的定制奶茶；你不必理解后厨的完整配方，只需一步步表达需求。

### 结构与角色

GoF 经典结构（四角色）：

- **Builder（抽象建造者）**：声明构建各部件的接口。
- **ConcreteBuilder（具体建造者）**：实现构建步骤，装配并持有最终 Product，提供取回产物的方法。
- **Director（指挥者）**：按固定算法调用 Builder 的各步骤，封装「构建顺序」。
- **Product（产品）**：被构建的复杂对象。

现代（流式 / Fluent）变体：省略 Director，由 ConcreteBuilder 提供链式方法并直接 `build()`（即《Effective Java》Item 2 的写法）。

### 具体示例

#### Java — 流式建造者（现代常用，无 Director）

```java
public class Computer {
    private final String cpu;
    private final String ram;
    private final String storage;

    private Computer(Builder b) {   // 只能通过 Builder 构建
        this.cpu = b.cpu;
        this.ram = b.ram;
        this.storage = b.storage;
    }

    public static class Builder {
        private String cpu;                 // 可选
        private String ram;                 // 可选
        private String storage;             // 可选

        public Builder cpu(String cpu) { this.cpu = cpu; return this; }
        public Builder ram(String ram) { this.ram = ram; return this; }
        public Builder storage(String s) { this.storage = s; return this; }
        public Computer build() { return new Computer(this); }
    }
}

// 使用
Computer pc = new Computer.Builder()
    .cpu("i9-13900K")
    .ram("32GB")
    .storage("1TB SSD")
    .build();
```

> 说明：一种常见的错误写法是让 Builder 内部直接持有并返回**同一个可变** Product，这样多次 `build()` 得到的是同一对象、且字段可被后续修改。更稳妥的做法是（如上）在 `build()` 时用已收集的参数**新建**一个不可变 Product。

#### Python — Director 角色（GoF 经典结构，封装构建流程）

```python
class MealBuilder:
    def add_main_course(self): ...
    def add_side(self): ...
    def add_drink(self): ...
    def build(self): ...

class MealDirector:
    """指挥者：定义固定的构建顺序，与具体 Builder 解耦"""
    def construct(self, builder: MealBuilder):
        builder.add_main_course()
        builder.add_side()
        builder.add_drink()
        return builder.build()
```

### 为什么需要它（应用场景）

- 对象含**多个可选参数**，直接写重载构造函数会导致「**伸缩构造函数**（telescoping constructor）」——参数列表又长又难读、易传错顺序。
- 构建过程复杂、需要分步或按顺序装配（如拼接 SQL、组装复杂报表、生成游戏角色）。
- 同一构建流程要产出不同表示（如把同一份文档构建为 HTML / PDF / Markdown）。
- 需要产出**不可变对象**（构造完成后不允许再修改）。

### 优点与局限

**优点**

- 分步构建、参数可读性强，天然支持可选参数与默认值。
- 构建过程与最终表示解耦，可复用同一 Director 装配不同 Product。
- 便于构造不可变对象。

**局限**

- 需要额外编写 Builder 类，代码量增加。
- 对产品简单、参数很少的场景属于过度设计。

### 常见误区

- ❌ 把「任何链式 setter」都叫建造者。建造者的关键是**分步收集参数、最后一次性 `build()` 产出（通常不可变的）对象**，而不是随手返回 `this` 的可变设置器。
- ❌ 混淆 GoF 建造者与现代流式建造者。GoF 版本含 Director、强调「同一过程不同表示」；日常 Java/Python 中更常见的是《Effective Java》式的流式 Builder，主要用于解决多可选参数问题。

### 与相关术语的对比

| 对比项 | 建造者模式 | 工厂方法 | 抽象工厂 |
|--------|-----------|----------|----------|
| 关注点 | 复杂对象的分步构建过程 | 创建单个对象 | 创建一族相关对象 |
| 返回结果 | 一个（通常复杂的）产品 | 单一产品 | 一族产品 |
| 构建时机 | 分多步、最后装配 | 一步返回 | 一步返回 |
| 可选参数 | 天然支持 | 不方便 | 不适用 |
| 典型场景 | 参数多 / 构建流程复杂 | 类型由子类决定 | 多平台 / 多风格成套对象 |

---

## 5. 原型模式（Prototype）

### 一句话定义

用一个已有的对象作为**原型**，通过**复制（克隆）**它来创建新对象，而不是通过 `new` 从头构造。

### 通俗类比

老师发给你一份试卷的复印件：复印件与原件内容一致，但两者相互独立——你在复印件上涂改不会影响原件。原型模式就是「照着现成的样板复印一份」，省去重新排版印刷的成本。

### 结构与角色

- **Prototype（抽象原型）**：声明一个克隆接口（如 Java 的 `clone()`、Python 的 `__copy__` / `__deepcopy__`）。
- **ConcretePrototype（具体原型）**：实现克隆方法，返回自身的一个副本。
- **Client（客户端）**：通过调用原型的克隆方法获得新对象。

关键点：复制分**浅拷贝**与**深拷贝**，选错会引入隐蔽的共享状态 bug。

### 具体示例

#### Python — 浅拷贝 vs 深拷贝

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

# 浅拷贝：只复制顶层对象，内部的 Address 仍是同一个引用
p2 = copy.copy(p1)
print(p2 is p1)                  # False（外层是新对象）
print(p1.address is p2.address)  # True （内部对象共享）

# 深拷贝：递归复制，所有层级都相互独立
p3 = copy.deepcopy(p1)
print(p1.address is p3.address)  # False
```

#### Java — 通过序列化实现深拷贝

```java
import java.io.*;

public class Prototype implements Cloneable, Serializable {
    // 浅拷贝：Object.clone() 默认逐字段复制（引用类型只复制引用）
    @Override
    public Prototype clone() throws CloneNotSupportedException {
        return (Prototype) super.clone();
    }

    // 深拷贝：序列化再反序列化，得到完全独立的对象图
    public Prototype deepClone() throws IOException, ClassNotFoundException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(bos)) {
            oos.writeObject(this);
        }
        ByteArrayInputStream bis = new ByteArrayInputStream(bos.toByteArray());
        try (ObjectInputStream ois = new ObjectInputStream(bis)) {
            return (Prototype) ois.readObject();
        }
    }
}
```

> 说明：Java 的 `Cloneable` 是一个「残缺接口」——它本身不含 `clone()` 方法，`clone()` 定义在 `Object` 上且是 `protected`；`super.clone()` 只做浅拷贝，且不调用构造函数。《Effective Java》Item 13 因此建议**优先用拷贝构造函数或拷贝工厂**替代 `clone()`。

### 为什么需要它（应用场景）

- 对象创建成本高（涉及数据库查询、网络请求、大量计算、复杂初始化），复制现成对象更划算。
- 需要一个与当前对象状态**完全相同的副本**（如保存快照、支持撤销 / 回滚）。
- 运行时动态确定要创建的类型（把实例注册为原型，按需克隆）。
- 规避复杂的工厂层次，直接以对象为模板批量生产。

### 优点与局限

**优点**

- 可在运行期动态增删原型，比静态工厂更灵活。
- 复制已有对象可绕过昂贵的初始化过程。
- 深拷贝能快速得到相互独立的对象副本。

**局限**

- **深拷贝实现复杂**：对象图含循环引用时需谨慎处理，否则可能无限递归或漏拷。
- 每个类都要考虑克隆的正确性，侵入性强（尤其 Java 的 `clone()` 约定繁琐）。
- 克隆可能绕过构造函数中的校验 / 初始化逻辑，导致状态不一致。

### 常见误区

- ❌ 以为「复制对象」默认就是深拷贝。多数语言的默认克隆 / 赋值是**浅拷贝**，内部引用对象仍被共享。
- ❌ 忽略循环引用：深拷贝需借助「已拷贝对象」的缓存（如 Python `deepcopy` 内部的 `memo` 字典）避免无限递归。
- ❌ 克隆后忘记重置标识字段（如主键 id、唯一编号），导致两个「不同」对象却共享同一身份。

### 深拷贝 vs 浅拷贝

| 类型 | 复制范围 | 引用字段处理 | 类比 |
|------|----------|--------------|------|
| 浅拷贝 | 只复制顶层对象 | 复制引用（指向同一内部对象） | 复印正文，附带的便签仍是原件那一张 |
| 深拷贝 | 递归复制整个对象图 | 为每一层都新建副本 | 连同便签一起重新誊抄一份，完全独立 |

---

## 6. 对象池模式（Object Pool）

### 一句话定义

预先创建一批**可复用**的对象放入「池」中循环借用与归还，用复用代替反复创建 / 销毁，以降低昂贵对象带来的开销。

### 通俗类比

共享单车：你不必每次出行都买一辆新车，用完还到指定点位，下一个人接着骑；只有当车全部被借走时，运营方才补充新车。对象池就是这批「可循环借还的车」。

> 提示：对象池**不属于 GoF 的 23 种模式**，是工程实践中补充的创建型模式，其确切来源在不同文献中说法不一（**建议人工核验**）。

### 结构与角色

- **Pool（池）**：维护空闲对象集合，提供 `acquire()` / `release()`；负责池的初始化、上限、回收与失效处理。
- **PooledObject（被池化对象）**：可重复使用的资源（连接、线程、缓冲区等）；归还时通常需要重置状态。
- **Client（客户端）**：借用 → 使用 → 归还，且**不得继续使用已归还对象的引用**。

### 具体示例

```python
import queue

class ObjectPool:
    def __init__(self, creator, max_size=10):
        self._pool = queue.Queue(maxsize=max_size)
        self._creator = creator
        for _ in range(max_size):
            self._pool.put(creator())

    def acquire(self, timeout=None):
        return self._pool.get(timeout=timeout)   # 池空时可阻塞 / 超时

    def release(self, obj):
        self._pool.put(obj)                       # 归还前应先重置对象状态

# 使用
pool = ObjectPool(creator=lambda: {"conn": "数据库连接"}, max_size=5)
conn = pool.acquire()    # 借
try:
    ...                  # 用
finally:
    pool.release(conn)   # 还（务必放在 finally，避免泄漏）
```

> 说明：生产级对象池还要处理**池耗尽策略**（阻塞 / 超时 / 抛错）、**对象有效性校验**（借出前探活）、**空闲回收与最大生命周期**、**并发安全**等；手写容易出错，通常直接使用成熟实现（如数据库连接池 HikariCP、Apache Commons Pool）。

### 为什么需要它（应用场景）

- 对象创建 / 销毁开销大：数据库连接、TCP 连接、线程、文件句柄。
- 资源数量需要**受控上限**，防止无节制创建压垮下游（如连接数打满数据库）。
- 高频申请 / 释放且对象可安全复用的场景（如缓冲区、图形资源）。

### 优点与局限

**优点**

- 显著降低昂贵对象的创建 / 销毁开销，提升吞吐、降低延迟抖动。
- 通过上限约束保护后端资源。

**局限 / 代价**

- 增加复杂度：借还配对、状态重置、失效检测、并发控制都要正确实现，否则引发资源泄漏或脏数据。
- **对轻量对象可能得不偿失**：在带高效 GC 的语言（Java / .NET）中，短命的小对象由垃圾回收处理往往比池化更快，池化反而带来管理开销与内存常驻。
- 池大小需调优：过小会阻塞，过大会浪费内存。

### 常见误区

- ❌「对象池总能提升性能」。对**创建成本低、体积小**的对象，池化常常是**反模式**——现代 GC 对小对象的分配 / 回收极快，池化引入的簿记开销可能更慢。对象池主要对**重量级、创建昂贵**的资源才划算。
- ❌ 借出后忘记归还，或归还后仍继续使用旧引用（导致同一对象被两处并发使用）。
- ❌ 归还时不重置状态，把上一次使用的脏数据带给下一个使用者。

### 与相关术语的对比

| 对比项 | 对象池 | 单例 | 工厂 |
|--------|--------|------|------|
| 对象数量 | 多个（有上限） | 恰好一个 | 按需创建 |
| 复用方式 | 借用—归还 | 全局共享同一实例 | 通常用完即弃 |
| 关注点 | 复用昂贵对象、控制上限 | 唯一性与全局访问点 | 解耦「创建哪种对象」 |
| 适用场景 | 高频创建销毁的重量级资源 | 全局唯一实例 | 灵活创建不同实现 |

---

## 常见误区（跨模式）

- **为模式而模式**：模式是权衡而非教条；简单场景硬套模式只会增加抽象层与维护成本。
- **混淆「简单工厂」与 GoF 工厂**：简单工厂不是 GoF 模式，且违反开闭原则。
- **把单例当默认全局方案**：单例带来全局状态与测试困难，很多场景可用依赖注入（DI）替代。
- **误以为对象池必然更快**：对轻量对象，在 GC 语言中池化可能更慢。
- **忽视线程安全与生命周期**：单例的懒加载、工厂的并发创建、原型的深浅拷贝、对象池的借还，都与并发 / 内存模型密切相关。

## 相关术语与前置知识

- **设计原则（SOLID）**：开闭原则（OCP）、依赖倒置原则（DIP）、单一职责原则（SRP）、里氏替换原则（LSP）、接口隔离原则（ISP）。
- **相关模式**：结构型模式（适配器、装饰器、代理、外观……）、行为型模式（观察者、策略、模板方法……）。
- **配套机制**：依赖注入 / 控制反转（IoC / DI，如 Spring 容器可替代大量手写工厂与单例）、反射、序列化、深 / 浅拷贝、线程安全与内存模型、垃圾回收（GC）。
- **相关反模式**：上帝对象、过度设计、对象池误用。

## 参考资料

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides.《设计模式：可复用面向对象软件的基础》（*Design Patterns: Elements of Reusable Object-Oriented Software*）. Addison-Wesley, 1994. ISBN 0-201-63361-2.（GoF，创建型 5 种模式的权威来源）
2. Joshua Bloch.《Effective Java》（第 3 版）. Addison-Wesley, 2018. ISBN 978-0-13-468599-1.（Item 2 建造者、Item 3 枚举实现单例、Item 13 谨慎覆写 clone）
3. 关于**对象池**与**简单工厂**的确切出处与归属：二者均非 GoF 23 种模式，不同模式目录记载不一。**建议人工核验**：可参考 PLoP（Pattern Languages of Programs）系列、Mark Grand《Patterns in Java》等资料后再补充精确引用。

> 说明：以上书籍信息为公认版本；为避免虚构，未列出具体 URL 与页码，edition / 页码差异建议人工核验。

## 总结

```
创建型模式
├── 单例模式（Singleton）———— 保证全局仅一个实例，并提供访问点
├── 工厂方法（Factory Method）—— 把实例化延迟到子类
├── 抽象工厂（Abstract Factory）— 创建一族相互关联的产品
├── 建造者（Builder）——————— 分步构建复杂对象，构建与表示分离
├── 原型（Prototype）——————— 通过复制（克隆）已有对象来创建
└── 对象池（Object Pool）*———— 复用昂贵对象（* 非 GoF 模式）
```

> **选择建议**：类型由子类决定 → 工厂方法；需要成套切换一族产品 → 抽象工厂；对象参数多 / 构建流程复杂 → 建造者；创建成本高、需要状态副本 → 原型；全局唯一实例 → 单例（谨慎，优先考虑依赖注入）；重量级资源高频借还 → 对象池（轻量对象勿滥用）。能用成熟框架（如 Spring 的 IoC 容器、HikariCP 连接池）时，优先复用而非手写。
