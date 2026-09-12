---
title: "结构型模式（Structural Patterns）"
tags: ["设计模式", "结构型模式", "GoF", "面向对象设计"]
source: "baike"
source_path: "开发术语 / 设计模式"
collected: "2026-09-05"
status: "imported"
---

# 结构型模式（Structural Patterns）


> 📌 **导航**：本文是 **结构型模式（Structural Patterns）** 词条，属于 design-patterns 术语集。相关枢纽：[[创建型模式（Creational Patterns）]]、[[结构型模式（Structural Patterns）]]、[[行为型模式（Behavioral Patterns）]]。

> 结构型模式关注**如何将类与对象组合成更大的结构**：用继承（类结构型）与组合（对象结构型）搭建灵活、可复用的架构。其核心目标是在不改动已有类的前提下，通过「拼装」获得新的协作能力或更清晰的接口。

---

## 概述与背景

结构型模式是 GoF《设计模式》三大类之一，共 **7 种**：适配器、桥接、组合、装饰器、外观、享元、代理。按实现手段又分两类：

| 子类 | 机制 | 代表模式 |
|------|------|----------|
| 类结构型 | 用**继承**在编译期组合 | 类适配器 |
| 对象结构型 | 用**组合/委托**在运行期装配（更灵活，主流） | 桥接、组合、装饰器、外观、享元、代理、对象适配器 |

本文除 7 种 GoF 结构型模式外，还收录工程/教学中常与之并列讨论的 **过滤器模式（Filter/Criteria）** 以及 **MVC / MVVM** 两种架构模式。**这三者均不属于 GoF 的结构型模式**：过滤器多见于教程类模式目录（来源**建议人工核验**）；MVC、MVVM 属于更宏观的**架构模式**，GoF 书中反而把经典 MVC 描述为观察者 + 策略 + 组合三种模式的复合运用。

结构型模式共同解决的问题：

- **接口转换与兼容**（适配器、外观）。
- **解耦抽象与实现、控制访问**（桥接、代理）。
- **统一处理整体与部分、动态扩展职责**（组合、装饰器）。
- **以共享支撑海量细粒度对象**（享元）。

---

## 1. 适配器模式（Adapter）

### 一句话定义

将一个类的接口**转换**成客户端期望的另一个接口，使原本因接口不兼容而不能一起工作的类能够协同工作。

### 通俗类比

电源转换插头——中国的两脚扁插去欧洲圆孔插座用不了，中间加一个转换器即可，双方都不必改造自身。适配器就是那个转换器。

### 结构与角色

- **Target（目标接口）**：客户端期望的接口。
- **Adaptee（被适配者）**：已存在、接口不兼容的类。
- **Adapter（适配器）**：实现 Target，内部持有（对象适配器）或继承（类适配器）Adaptee，把 Target 调用转成 Adaptee 调用。

### 具体示例

#### 对象适配器（组合方式，更常用）

```python
class OldPrinter:
    def print_old(self, text):
        return f"旧式打印: {text}"

# 适配器：对外暴露 print_new（Target），内部委托 OldPrinter（Adaptee）
class PrinterAdapter:
    def __init__(self, old_printer: OldPrinter):
        self._old = old_printer

    def print_new(self, text):
        return self._old.print_old(text)

adapter = PrinterAdapter(OldPrinter())
print(adapter.print_new("Hello"))  # 旧式打印: Hello
```

#### Java — 类适配器（继承方式）

```java
class OldPrinter {                       // Adaptee
    String printOld(String text) { return "旧式: " + text; }
}

interface NewPrinter {                   // Target
    String printNew(String text);
}

// 类适配器：继承 Adaptee + 实现 Target
class PrinterAdapter extends OldPrinter implements NewPrinter {
    @Override
    public String printNew(String text) {
        return printOld(text);           // 委托给父类
    }
}
```

### 为什么需要它（应用场景）

- 整合遗留系统 / 第三方库，接口不匹配又不便修改源码。
- 统一多套异构接口（如把多个支付渠道 SDK 适配成同一内部接口）。
- 让已存在的类适配到新的抽象体系中。

### 优点与局限

**优点**：复用现有实现、零侵入（不改 Adaptee）、提升类的透明性与复用。
**局限**：系统中会多出适配器层，过度使用会让调用链变绕、可读性下降。

### 类适配器 vs 对象适配器

| 类型 | 方式 | 优点 | 缺点 |
|------|------|------|------|
| 类适配器 | 继承 Adaptee | 可重写 Adaptee 方法；只引入一个对象 | Java 单继承下只能适配一个类；耦合更紧 |
| 对象适配器 | 组合持有 Adaptee | 可适配 Adaptee 及其子类；更灵活、低耦合 | 无法直接重写 Adaptee 方法（需间接） |

---

## 2. 桥接模式（Bridge）

### 一句话定义

将**抽象部分**与**实现部分**分离，使二者可以独立变化，用组合（桥）替代继承来连接两个层次。

### 通俗类比

遥控器与电视是两个独立变化的维度——万能遥控器可配小米电视，小米遥控器也可配三星电视，二者通过「红外/蓝牙信号」这座桥连接，各自升级互不影响。

### 结构与角色

- **Abstraction（抽象）**：持有对 Implementor 的引用，定义高层操作。
- **RefinedAbstraction（扩充抽象）**：扩展 Abstraction 的行为。
- **Implementor（实现接口）**：定义底层实现接口。
- **ConcreteImplementor（具体实现）**：实现 Implementor。

### 具体示例

```python
from abc import ABC, abstractmethod

# —— 实现层次（Implementor）：颜色 ——
class Color(ABC):
    @abstractmethod
    def fill(self) -> str: ...

class Red(Color):
    def fill(self) -> str: return "红色"

class Blue(Color):
    def fill(self) -> str: return "蓝色"

# —— 抽象层次（Abstraction）：形状，持有 Color 的引用 ——
class Shape(ABC):
    def __init__(self, color: Color):
        self.color = color            # 这座「桥」连接两个层次

    @abstractmethod
    def draw(self) -> str: ...

class Circle(Shape):
    def draw(self) -> str: return f"画一个{self.color.fill()}的圆"

class Square(Shape):
    def draw(self) -> str: return f"画一个{self.color.fill()}的方块"

# 两个维度自由组合
print(Circle(Red()).draw())    # 画一个红色的圆
print(Square(Blue()).draw())   # 画一个蓝色的方块
```

### 为什么需要它（应用场景）

- 一个类存在**两个（或多个）独立变化的维度**，且都需要扩展（形状×颜色、平台×功能、消息类型×发送方式）。
- 不想在抽象与实现之间用继承造成「类爆炸」。
- 需要在**运行时**切换实现。

### 优点与局限

**优点**：抽象与实现解耦、可独立扩展；用 M+N 个类替代 M×N；实现可运行时替换。
**局限**：要求一开始就正确识别出「两个独立维度」，对单一维度的简单类属于过度设计。

### 与继承的对比

| 方式 | 类数量 | 扩展性 |
|------|--------|--------|
| 多层继承 | M × N | 新增维度需派生大量子类 |
| 桥接模式 | M + N | 两个维度各自新增类即可 |

---

## 3. 组合模式（Composite）

### 一句话定义

将对象组合成**树形结构**以表示「部分—整体」的层次，使客户端对**单个对象**与**组合对象**的使用具有一致性。

### 通俗类比

公司组织架构——CEO 下辖部门经理，经理下辖员工。下发通知时，既可发给整个部门（容器），也可发给单个员工（叶子），操作方式一致。

### 结构与角色

- **Component（抽象构件）**：声明叶子与容器的公共接口。
- **Leaf（叶子）**：无子节点，实现业务方法。
- **Composite（容器）**：持有子构件集合，实现 add/remove 并递归委派给子节点。

### 具体示例

```python
from abc import ABC, abstractmethod

class Component(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def show(self, indent=0): ...

class Employee(Component):            # Leaf
    def show(self, indent=0):
        print("  " * indent + f"员工: {self.name}")

class Department(Component):          # Composite
    def __init__(self, name):
        super().__init__(name)
        self.children: list[Component] = []

    def add(self, component: Component):
        self.children.append(component)

    def show(self, indent=0):
        print("  " * indent + f"部门: {self.name}")
        for child in self.children:
            child.show(indent + 1)    # 递归委派

company = Department("总公司")
dev = Department("研发部")
dev.add(Employee("张三"))
dev.add(Employee("李四"))
company.add(dev)
company.add(Employee("CEO秘书"))
company.show()
# 部门: 总公司
#   部门: 研发部
#     员工: 张三
#     员工: 李四
#   员工: CEO秘书
```

### 为什么需要它（应用场景）

- 文件系统（目录嵌套文件）、UI 组件树（容器嵌套控件）、组织架构、XML/JSON 树、菜单与子菜单。
- 希望客户端**忽略叶子与容器的差异**，用统一方式处理。

### 优点与局限

**优点**：统一叶子与容器的调用、天然递归、新增节点符合开闭原则。
**局限**：设计较抽象；若各构件差异很大，统一接口会牵强。**透明式**（把 add/remove 放到 Component，叶子空实现或抛异常）与**安全式**（add/remove 只放在 Composite，客户端需区分类型）需权衡——上例为安全式。

### 常见误区

- ❌ 以为组合模式就是「一个类里放一个 List」。关键在于**叶子与容器共享 Component 接口**，从而能被一致地递归处理。

---

## 4. 装饰器模式（Decorator）

### 一句话定义

在**不改变原对象接口**的前提下，动态地给对象**叠加额外职责**；就扩展功能而言，比继承更灵活。

### 通俗类比

穿衣服——T 恤外加外套、外套外加羽绒服，每加一层多一项功能（保暖、防水、防风），而「你」这个被装饰对象的身份不变。

### 结构与角色

- **Component（抽象构件）**：定义统一接口（装饰器与被装饰对象都实现它，才能相互替换、层层包裹）。
- **ConcreteComponent（具体构件）**：被装饰的原始对象。
- **Decorator（抽象装饰器）**：持有 Component 引用并实现 Component 接口。
- **ConcreteDecorator（具体装饰器）**：在委托 Component 的基础上追加职责。

### 具体示例

```python
from abc import ABC, abstractmethod

class Coffee(ABC):                    # Component：装饰器与被装饰者共享此接口
    @abstractmethod
    def cost(self) -> int: ...
    @abstractmethod
    def description(self) -> str: ...

class SimpleCoffee(Coffee):           # ConcreteComponent
    def cost(self) -> int: return 10
    def description(self) -> str: return "普通咖啡"

class MilkDecorator(Coffee):          # ConcreteDecorator
    def __init__(self, coffee: Coffee):
        self._coffee = coffee
    def cost(self) -> int: return self._coffee.cost() + 3
    def description(self) -> str: return self._coffee.description() + " + 牛奶"

class SugarDecorator(Coffee):
    def __init__(self, coffee: Coffee):
        self._coffee = coffee
    def cost(self) -> int: return self._coffee.cost() + 1
    def description(self) -> str: return self._coffee.description() + " + 糖"

coffee: Coffee = SimpleCoffee()
coffee = MilkDecorator(coffee)        # 层层包裹
coffee = SugarDecorator(coffee)
print(f"{coffee.description()}: ¥{coffee.cost()}")  # 普通咖啡 + 牛奶 + 糖: ¥14
```

### 为什么需要它（应用场景）

- 需要**运行时**、可叠加、可撤销地扩展对象功能。
- 经典案例：Java I/O —— `new BufferedInputStream(new FileInputStream("file"))`，`BufferedInputStream` 装饰 `FileInputStream`，为其增加缓冲能力。
- Web 中间件中对请求/响应的逐层包装。

### 优点与局限

**优点**：比继承灵活（运行时组合、可任意叠加）；避免「为每种组合派生一个子类」的类爆炸；符合开闭原则。
**局限**：产生许多小对象、层层嵌套使调试与阅读变难；装饰顺序有时会影响结果。

### 常见误区

- ❌ 把 Python 的 `@decorator` 语法等同于 GoF 装饰器模式。前者是语言级的**函数/类包装**语法糖，后者强调**装饰器与被装饰对象实现同一接口、可层层替换包裹**；二者神似而形不同。
- ❌ 装饰器不实现 Component 接口——那样就无法透明替换、无法嵌套。

### 与继承的对比

| 方式 | 灵活性 | 组合能力 |
|------|--------|----------|
| 继承 | 编译期静态确定 | M 种组合需 M 个子类，易爆炸 |
| 装饰器 | 运行时动态叠加 | N 个装饰器按是否使用的子集可组合出约 2^N 种效果（不计顺序） |

---

## 5. 外观模式（Facade）

### 一句话定义

为子系统中的一组接口提供一个**统一的高层接口**，使子系统更易使用、降低客户端与其内部细节的耦合。

### 通俗类比

去医院看病——你不必分别跑挂号、缴费、检查、取药各个窗口，导诊台（外观）帮你把整套流程串起来，一个入口搞定。

### 结构与角色

- **Facade（外观）**：知晓各子系统的职责，把客户端请求委派给合适的子系统对象。
- **Subsystem（子系统类）**：实现具体功能；它们**可以不知道 Facade 的存在**（单向依赖）。

### 具体示例

```python
class CPU:
    def freeze(self): print("CPU 冻结")
    def execute(self): print("CPU 执行")

class Memory:
    def load(self): print("内存加载数据")

class HardDrive:
    def read(self): print("硬盘读取数据")

class ComputerFacade:                 # 外观：封装复杂子系统
    def __init__(self):
        self.cpu = CPU()
        self.memory = Memory()
        self.hard_drive = HardDrive()

    def start(self):
        self.cpu.freeze()
        self.hard_drive.read()
        self.memory.load()
        self.cpu.execute()
        print("电脑启动完成!")

ComputerFacade().start()              # 客户端只调一个方法
```

### 为什么需要它（应用场景）

- 为复杂子系统提供简单入口（SDK 封装、分层架构的 Service 门面、遗留系统的统一接口）。
- 降低客户端与子系统内部类的耦合，便于子系统独立演化。

### 优点与局限

**优点**：使用简单、解耦客户端与子系统、符合迪米特法则（最少知道）。
**局限**：外观可能膨胀成「上帝类」；它**不阻止**客户端直接使用子系统类（是「简化入口」而非「强制封装」）。

### 常见误区

- ❌ 以为加了外观就不能再访问子系统。外观只是提供便捷入口，高级用户仍可直接使用子系统类。
- ❌ 把外观与中介者混淆：外观简化「客户端→子系统」的**单向**调用；中介者协调「多个同僚对象」之间的**多向**交互。

---

## 6. 享元模式（Flyweight）

### 一句话定义

运用**共享**技术，让大量**细粒度**对象复用同一份公共状态，从而高效支撑海量对象。

### 通俗类比

字体渲染——屏幕上显示上千个「中」字，但字体文件里只存一份「中」的字形数据，所有「中」字共享它；每个字的位置、颜色等差异信息由外部临时传入。

### 结构与角色

- **Flyweight（享元接口）**：声明方法，接收**外在状态**作为参数。
- **ConcreteFlyweight（具体享元）**：持有**内在状态**（可共享、不随场景变），实现接口。
- **FlyweightFactory（享元工厂）**：创建并缓存享元，保证相同内在状态只存一份。
- 关键区分：**内在状态**（intrinsic，存于享元内、可共享，如字形）与**外在状态**（extrinsic，随场景变化、由客户端传入，如坐标/颜色）。

### 具体示例

```python
class FontFlyweight:                  # 具体享元：font_name 是内在状态（共享）
    def __init__(self, font_name):
        self.font_name = font_name

    def render(self, char):           # char 是外在状态（由客户端传入）
        return f"[{self.font_name}:{char}]"

class FlyweightFactory:
    _fonts: dict[str, FontFlyweight] = {}

    @classmethod
    def get_font(cls, name):
        if name not in cls._fonts:    # 相同内在状态只创建一次
            cls._fonts[name] = FontFlyweight(name)
            print(f"创建新字体: {name}")
        return cls._fonts[name]

for name in ["Arial", "Arial", "Arial", "Times", "Times"]:
    FlyweightFactory.get_font(name)

print(f"字体对象数量: {len(FlyweightFactory._fonts)}")  # 2（而不是 5）
```

### 为什么需要它（应用场景）

- 对象数量巨大且大部分状态可共享：文本编辑器的字符/字形、游戏里的粒子与地图块、棋类游戏的棋子、Java 的 `Integer.valueOf(-128~127)` 缓存。
- 前提：**内在状态可提取且共享，外在状态可由外部传入**。

### 优点与局限

**优点**：大幅减少内存中相似对象的实例数量，降低内存与创建开销。
**局限**：内在/外在状态分离会使代码复杂化；享元被多方共享时，若误将其内在状态改为可变，会引发数据串改与线程安全问题。

### 常见误区

- ❌ 享元 = 缓存/单例。享元强调**按内在状态共享一批实例**（一个工厂管理一组），单例是**全局唯一**，普通缓存未必区分内外在状态。

### 与相关术语的对比

| 对比项 | 享元模式 | 单例 | 对象池 |
|--------|---------|------|--------|
| 目的 | 共享细粒度对象、省内存 | 保证唯一实例 | 复用昂贵对象 |
| 对象数量 | 多个（同内在状态共享一个） | 一个 | 固定数量 |
| 关键特征 | 内在状态共享 + 外在状态外置 | 全局唯一 | 借用—归还 |

---

## 7. 代理模式（Proxy）

### 一句话定义

为某个对象提供一个**代理（替身）**，由代理控制对该对象的访问，并可在访问前后附加额外处理。

### 通俗类比

房产中介——房东把房子委托给中介，中介代为处理带看、签约、收租；租客不直接接触房东，中介还能在其中核验资质、记录流水。

### 结构与角色

- **Subject（抽象主题）**：声明真实主题与代理的共同接口（二者可互换）。
- **RealSubject（真实主题）**：代理所代表的真实对象。
- **Proxy（代理）**：持有对 RealSubject 的引用，实现 Subject 接口，在转调前后加入控制逻辑。

### 具体示例

#### 静态代理（虚拟代理 / 延迟加载）

```python
from abc import ABC, abstractmethod   # 原示例缺此导入，已补

class Image(ABC):                      # Subject
    @abstractmethod
    def display(self): ...

class RealImage(Image):                # RealSubject
    def __init__(self, filename):
        self.filename = filename
        self._load_from_disk()
    def _load_from_disk(self):
        print(f"从磁盘加载 {self.filename}（耗时操作）")
    def display(self):
        print(f"显示 {self.filename}")

class ProxyImage(Image):               # Proxy
    def __init__(self, filename):
        self.filename = filename
        self._real = None
    def display(self):
        if self._real is None:         # 延迟到首次使用才创建真实对象
            self._real = RealImage(self.filename)
        self._real.display()

proxy = ProxyImage("photo.jpg")
proxy.display()  # 从磁盘加载 + 显示
proxy.display()  # 直接显示（不重复加载）
```

#### Java — JDK 动态代理（需接口，基于反射）

```java
public class LogProxy implements InvocationHandler {
    private final Object target;
    public LogProxy(Object target) { this.target = target; }

    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        System.out.println("调用前: " + method.getName());
        Object result = method.invoke(target, args);
        System.out.println("调用后: " + method.getName());
        return result;
    }
}

// 使用
UserService proxy = (UserService) Proxy.newProxyInstance(
    UserService.class.getClassLoader(),
    new Class[]{UserService.class},
    new LogProxy(new UserServiceImpl())
);
```

#### Java — CGLIB 代理（无需接口，基于字节码生成子类）

```java
Enhancer enhancer = new Enhancer();
enhancer.setSuperclass(UserService.class);
enhancer.setCallback((MethodInterceptor) (obj, method, args, proxy) -> {
    System.out.println("CGLIB 拦截");
    return proxy.invokeSuper(obj, args);
});
UserService proxy = (UserService) enhancer.create();
```

### 为什么需要它（应用场景）

按用途分：**远程代理**（RPC 存根）、**虚拟代理**（延迟加载大对象）、**保护代理**（权限校验）、**缓存代理**（结果复用）、**日志/AOP 代理**（Spring AOP 的横切增强）、**智能引用**（引用计数、写时复制）。

### 优点与局限

**优点**：在不改真实对象的前提下控制访问、增强功能；解耦调用方与真实对象；支持延迟加载节省资源。
**局限**：类数量增多、多一层转发可能变慢；动态代理有运行时开销与调试难度。

### 常见误区

- ❌ 认为代理与装饰器等价。二者结构相似但**意图不同**：代理侧重「**控制访问**」（要不要、何时、以何种权限访问真实对象）；装饰器侧重「**增强功能**」（不改接口下叠加职责）。
- ❌ 以为 JDK 动态代理可代理任意类。它**只能代理接口**；无接口需用 CGLIB。CGLIB 通过继承生成子类，因此**无法代理 final 类 / final 方法**。Spring AOP 在目标实现接口时默认用 JDK 动态代理、否则用 CGLIB（Spring Boot 2.x 起默认更倾向 CGLIB，具体版本行为建议人工核验）。

### 三种代理实现对比

| 类型 | 实现方式 | 是否需要接口 | 典型场景 |
|------|---------|-------------|---------|
| 静态代理 | 手写代理类 | 需要共同接口 | 简单、固定的代理 |
| JDK 动态代理 | 反射（`java.lang.reflect.Proxy`） | 必须有接口 | Spring AOP（有接口时） |
| CGLIB 代理 | 字节码生成子类 | 不需要接口 | 无接口时；不能代理 final |

---

## 8. 过滤器模式（Filter / Criteria）

> **非 GoF 结构型模式**：多见于教学类模式目录（又称 Criteria Pattern），把「按条件筛选」抽象成可组合的对象。其确切出处**建议人工核验**。

### 一句话定义

把每个筛选条件封装成独立的**过滤器对象**，再以与/或/非等方式**自由组合**，从一组对象中筛出满足条件者。

### 通俗类比

电商筛选——你同时勾选「品牌=Apple」「价格<5000」「评分>4.5」，每个条件是一个过滤器，可任意叠加、复用。

### 结构与角色

- **Filter/Criteria（过滤器接口）**：声明 `matches(item)` 或 `filter(list)`。
- **ConcreteFilter（具体过滤器）**：实现单一条件（按颜色、按价格……）。
- **组合器**：And/Or/Not 等把多个过滤器合成一个。

### 具体示例

```python
from abc import ABC, abstractmethod

class Product:
    def __init__(self, name, color, size, price):
        self.name, self.color, self.size, self.price = name, color, size, price

class Filter(ABC):
    @abstractmethod
    def matches(self, product: Product) -> bool: ...

class ColorFilter(Filter):
    def __init__(self, color): self.color = color
    def matches(self, product): return product.color == self.color

class PriceFilter(Filter):
    def __init__(self, max_price): self.max_price = max_price
    def matches(self, product): return product.price <= self.max_price

def filter_products(products, filters):
    result = products
    for f in filters:                       # 逐个条件过滤（相当于 AND 组合）
        result = [p for p in result if f.matches(p)]
    return result

products = [
    Product("iPhone", "黑色", "M", 7999),
    Product("小米", "白色", "M", 3999),
    Product("华为", "黑色", "L", 5999),
]
for p in filter_products(products, [ColorFilter("黑色"), PriceFilter(6000)]):
    print(p.name)  # 华为
```

### 为什么需要它（应用场景）

- 把复杂的多条件查询拆成可复用、可组合的单元，避免大段嵌套 if-else。
- 规则引擎、权限过滤、数据清洗、搜索结果的二次筛选。

### 优点与局限

**优点**：条件可复用、可组合、符合单一职责；新增条件符合开闭原则。
**局限**：条件很多时对象数量增加；本质上是策略/规格模式（Specification）的一种特化，简单场景用语言内建的 `filter`/LINQ/Stream 即可，无需自建体系。

---

## 9. MVC 模式（Model-View-Controller）

> **架构模式，非 GoF 结构型模式**。GoF 书中把经典 MVC 视为**观察者 + 策略 + 组合**三种模式的复合运用。

### 一句话定义

把应用拆成**模型（数据与业务逻辑）、视图（展示）、控制器（接收输入、协调 M 与 V）**三部分，使三者分离、可独立演化。

### 通俗类比

餐厅分工：后厨（Model）负责做菜与备料，服务员（Controller）接单并协调后厨与餐桌，菜单/摆盘（View）负责把成品呈现给顾客。

### 历史与来源

MVC 由 **Trygve Reenskaug 于 1979 年在施乐 PARC** 提出，最早用于 Smalltalk-79/80 的图形交互应用，是最早的界面架构模式之一。

### 具体示例

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    View     │◄────│  Controller │────►│    Model    │
│  (页面展示)  │     │  (处理请求)  │     │  (数据逻辑)  │
└─────────────┘     └─────────────┘     └─────────────┘
```

> 说明：上图为常见的简化示意。经典 MVC 的完整数据流还包括——Controller 处理输入并更新 Model；**Model 状态变化时通过观察者机制通知 View**；View 从 Model 读取状态进行渲染。

```python
class UserModel:                      # Model
    def __init__(self):
        self.users = []
    def add_user(self, name):
        self.users.append(name)
    def get_users(self):
        return list(self.users)

class UserView:                       # View
    def show_users(self, users):
        for u in users:
            print(f"用户: {u}")

class UserController:                 # Controller
    def __init__(self):
        self.model = UserModel()
        self.view = UserView()
    def add_user(self, name):
        self.model.add_user(name)
        self.view.show_users(self.model.get_users())

UserController().add_user("张三")     # 用户: 张三
```

### 为什么需要它（应用场景）

- Web 应用分层（如 Django、Spring MVC、Ruby on Rails）。
- 需要同一份 Model 支撑多种 View（Web、移动端、桌面），或让 UI 与业务逻辑独立演进、独立测试。

### 优点与局限

**优点**：职责分离、便于并行开发与单元测试、支持多视图共享同一模型。
**局限**：分层增加复杂度；View 与 Model 若耦合不当（如 View 直接改 Model）会破坏分层；「胖控制器」是常见反模式。

---

## 10. MVVM 模式（Model-View-ViewModel）

> **架构模式，非 GoF 模式**，是 MVC/MVP 的演化，核心是 **ViewModel + 数据绑定**。术语由微软 **John Gossman 于 2005 年**在介绍 WPF/Silverlight 时提出。

### 一句话定义

在 View 与 Model 之间引入 **ViewModel**：它持有视图状态与命令、暴露**可观察**的数据，借助**数据绑定**让 View 与 ViewModel 自动（双向）同步。

### 通俗类比

智能手表——运动时传感器（Model）产生数据，表盘界面（View）自动刷新，无需手动同步；中间的处理器（ViewModel）持续把数据加工成界面可直接绑定的状态。

### 结构与角色

- **Model**：领域数据与业务逻辑（通常来自 API/仓库）。
- **View**：界面，通过绑定观察 ViewModel 的可观察状态，几乎不含逻辑。
- **ViewModel**：View 的抽象，暴露可观察属性与命令，把 Model 数据转成视图状态（**注意：ViewModel 不直接引用 View**）。

### 具体示例

```vue
<!-- Vue 单文件组件：data/computed 属于 ViewModel 层，template 是 View -->
<template>
  <div>
    <input v-model="message" />      <!-- 双向数据绑定 -->
    <p>{{ reversedMessage }}</p>     <!-- 绑定到 ViewModel 的计算属性 -->
  </div>
</template>

<script>
export default {
  data() {
    return { message: '' }           // ViewModel 暴露的可观察状态
  },
  computed: {
    reversedMessage() {              // ViewModel：由状态派生的视图数据
      return this.message.split('').reverse().join('')
    }
  }
}
</script>
```

> 说明：把 `data()` 直接标为「Model」并不严谨。在 Vue 组件里，`data`/`computed`/`methods` 共同构成 **ViewModel**；真正的 **Model** 是背后的业务数据与接口层。数据绑定（`v-model`/`{{ }}`）是 MVVM 的关键机制。

### 为什么需要它（应用场景）

- 现代前端框架：Vue、Angular、React（思想相近，用状态驱动渲染）、WPF/WinUI、小程序。
- 需要**视图与展示逻辑解耦**、ViewModel 可独立测试、UI 随数据自动更新。

### 优点与局限

**优点**：数据驱动、View 逻辑极薄、ViewModel 可单测、天然支持双向绑定与响应式更新。
**局限**：绑定与响应式带来调试复杂度（数据流向不易追踪）；小型页面引入 ViewModel 显得繁重；过度绑定可能影响性能。

### MVC vs MVP vs MVVM

| 对比项 | MVC | MVP | MVVM |
|--------|-----|-----|------|
| 中间层 | Controller | Presenter | ViewModel |
| View 与中间层 | View 可读 Model | Presenter 主动更新 View（持有 View 引用） | 通过**数据绑定**自动同步（ViewModel 不持有 View） |
| 数据流向 | 单向为主 | Presenter 驱动 | 双向绑定 |
| 典型场景 | 传统 Web/服务端渲染 | 早期 Android、WinForms | Vue/Angular/WPF 等数据驱动 UI |

---

## 常见误区（跨模式）

- **代理 vs 装饰器**：结构相似，意图不同——代理**控制访问**，装饰器**增强功能**。
- **外观 vs 中介者 vs 适配器**：外观简化「客户端→子系统」的单向入口；中介者协调多个同僚对象的多向交互；适配器只做**接口转换**、不简化功能。
- **桥接 vs 适配器**：桥接是**设计期**就分离抽象与实现以备各自扩展；适配器是**事后**弥补已存在的不兼容接口。
- **享元 vs 单例/缓存**：享元按内在状态共享**一批**实例并外置外在状态，单例是全局唯一，普通缓存不必然区分内外在状态。
- **MVC/MVVM/过滤器并非 GoF 结构型模式**：它们是架构模式或教学补充，勿与 7 种 GoF 结构型模式混为一谈。

## 相关术语与前置知识

- **设计原则**：开闭原则、依赖倒置原则、迪米特法则（最少知识）、合成复用原则（优先组合而非继承）。
- **前置知识**：接口与抽象类、继承 vs 组合/委托、多态、反射与动态代理、序列化、垃圾回收与内存占用。
- **相关模式**：创建型模式（工厂常与外观/适配器配合）、行为型模式（观察者/策略/组合构成经典 MVC）。

## 参考资料

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides.《设计模式：可复用面向对象软件的基础》（*Design Patterns: Elements of Reusable Object-Oriented Software*）. Addison-Wesley, 1994. ISBN 0-201-63361-2.（7 种 GoF 结构型模式的权威来源）
2. Trygve Reenskaug. *Applications Programming in Smalltalk-80: How to use Model-View-Controller (MVC)*. 1979.（MVC 起源，具体文献版本建议人工核验）
3. John Gossman（Microsoft）. 关于 MVVM 的介绍. 2005.（MVVM 术语来源，**建议人工核验**：可查微软官方博客/MSDN 存档）
4. **过滤器模式（Filter/Criteria）** 的出处：非 GoF，散见于教学类模式目录，**建议人工核验**后再补精确引用。

> 说明：为避免虚构，未列出具体 URL 与页码；MVC/MVVM/过滤器的精确文献出处建议人工核验。

## 总结

```
结构型模式
├── 适配器（Adapter）*———— 转换不兼容的接口
├── 桥接（Bridge）*——————— 分离抽象与实现，各自独立变化
├── 组合（Composite）*————— 树形结构，统一处理叶子与容器
├── 装饰器（Decorator）*——— 运行时动态叠加职责
├── 外观（Facade）*——————— 为子系统提供统一高层入口
├── 享元（Flyweight）*————— 共享内在状态，支撑海量细粒度对象
├── 代理（Proxy）*——————— 控制并增强对对象的访问
├── 过滤器（Filter）—————— 组合条件筛选对象（非 GoF）
├── MVC ———————————————— 模型-视图-控制器分层（架构模式，非 GoF）
└── MVVM ——————————————— ViewModel + 数据绑定（架构模式，非 GoF）
```

（带 `*` 者为 GoF 的 7 种结构型模式）

> **选择建议**：接口不兼容→适配器；两个维度独立扩展→桥接；树形「部分—整体」→组合；运行时叠加职责→装饰器；给子系统一个简单入口→外观；海量相似对象且状态可共享→享元；控制/增强访问、延迟加载、AOP→代理；多条件筛选→过滤器（或语言内建 filter/Stream）；界面分层→MVC/MVVM。

---
