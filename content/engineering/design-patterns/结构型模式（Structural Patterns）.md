---
title: "结构型模式（Structural Patterns）"
tags: []
source: "baike"
source_path: "开发术语 / 设计模式"
collected: "2026-09-05"
status: "imported"
---

# 结构型模式（Structural Patterns）

> 结构型模式关注**如何将类和对象组合成更大的结构**，以实现新功能或简化设计。它们用继承和组合来搭建灵活的架构。

---

## 1. 适配器模式（Adapter）

### 一句话定义

将一个类的接口转换成客户端期望的另一个接口，让不兼容的类可以一起工作。

### 通俗类比

电源转换插头——中国的两脚插头去欧洲用不了，但一个转换器就能解决。适配器就是那个转换器。

### 具体示例

#### 对象适配器（组合方式，更常用）

```python
class OldPrinter:
    def print_old(self, text):
        return f"旧式打印: {text}"

class NewPrinter:
    def print_new(self, text):
        return f"新式打印: {text}"

# 适配器 —— 让旧接口适配新接口
class PrinterAdapter:
    def __init__(self, old_printer: OldPrinter):
        self._old = old_printer

    def print_new(self, text):
        return self._old.print_old(text)

# 客户端只认 print_new 接口
adapter = PrinterAdapter(OldPrinter())
print(adapter.print_new("Hello"))  # 旧式打印: Hello
```

#### Java — 类适配器（继承方式）

```java
class OldPrinter {
    String printOld(String text) { return "旧式: " + text; }
}

interface NewPrinter {
    String printNew(String text);
}

// 类适配器 —— 继承 + 实现
class PrinterAdapter extends OldPrinter implements NewPrinter {
    @Override
    public String printNew(String text) {
        return printOld(text);  // 委托给父类
    }
}
```

### 为什么需要它

整合遗留系统、第三方库时，接口往往不匹配，适配器让你无需修改原有代码。

### 类适配器 vs 对象适配器

| 类型 | 方式 | 优点 | 缺点 |
|------|------|------|------|
| 类适配器 | 继承 | 可以重写父类方法 | 只能适配一个类 |
| 对象适配器 | 组合 | 可适配多个对象 | 无法重写被适配者的方法 |

---

## 2. 桥接模式（Bridge）

### 一句话定义

将**抽象部分**与**实现部分**分离，使它们可以独立变化。

### 通俗类比

遥控器和电视是两个独立变化的维度——你可以有万能遥控器配小米电视，也可以用小米遥控器配三星电视。它们通过"红外信号"这个桥梁连接。

### 具体示例

```python
from abc import ABC, abstractmethod

# 实现部分 —— 颜色
class Color(ABC):
    @abstractmethod
    def fill(self): pass

class Red(Color):
    def fill(self): return "红色"

class Blue(Color):
    def fill(self): return "蓝色"

# 抽象部分 —— 形状
class Shape(ABC):
    def __init__(self, color: Color):
        self.color = color

    @abstractmethod
    def draw(self): pass

class Circle(Shape):
    def draw(self):
        return f"画一个{self.color.fill()}的圆"

class Square(Shape):
    def draw(self):
        return f"画一个{self.color.fill()}的方块"

# 使用 —— 两个维度自由组合
circle_red = Circle(Red())
print(circle_red.draw())  # 画一个红色的圆

square_blue = Square(Blue())
print(square_blue.draw())  # 画一个蓝色的方块
```

### 为什么需要它

当一个类有两个或多个独立变化的维度时（如形状×颜色、平台×功能），继承会导致类爆炸（M×N 个类），桥接模式只需 M+N 个类。

### 与继承的对比

| 方式 | 类数量 | 扩展性 |
|------|--------|--------|
| 多层继承 | M × N | 新增维度需修改大量类 |
| 桥接模式 | M + N | 新增维度只需添加新类 |

---

## 3. 组合模式（Composite）

### 一句话定义

将对象组合成**树形结构**来表示"部分-整体"的层次，使单个对象和组合对象的使用方式一致。

### 通俗类比

公司组织架构——CEO 下面有部门经理，部门经理下面有员工。发通知时，你可以对整个部门发，也可以对单个员工发，操作方式一样。

### 具体示例

```python
from abc import ABC, abstractmethod

class Component(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def show(self, indent=0): pass

class Employee(Component):
    def show(self, indent=0):
        print("  " * indent + f"员工: {self.name}")

class Department(Component):
    def __init__(self, name):
        super().__init__(name)
        self.children = []

    def add(self, component):
        self.children.append(component)

    def show(self, indent=0):
        print("  " * indent + f"部门: {self.name}")
        for child in self.children:
            child.show(indent + 1)

# 构建组织架构
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

### 为什么需要它

文件系统（文件夹嵌套文件）、UI 组件树（容器嵌套控件）、组织架构等树形结构，用组合模式可以统一处理叶子和容器。

---

## 4. 装饰器模式（Decorator）

### 一句话定义

动态地给对象添加额外职责，比继承更灵活。

### 通俗类比

穿衣服——你可以在 T 恤外面加外套，外套外面加羽绒服，每加一层就多一个功能（保暖、防水、防风），但你本身没变。

### 具体示例

```python
class Coffee:
    def cost(self):
        return 10

    def description(self):
        return "普通咖啡"

class MilkDecorator:
    def __init__(self, coffee):
        self._coffee = coffee

    def cost(self):
        return self._coffee.cost() + 3

    def description(self):
        return self._coffee.description() + " + 牛奶"

class SugarDecorator:
    def __init__(self, coffee):
        self._coffee = coffee

    def cost(self):
        return self._coffee.cost() + 1

    def description(self):
        return self._coffee.description() + " + 糖"

# 使用 —— 自由叠加
coffee = Coffee()
coffee = MilkDecorator(coffee)   # 加牛奶
coffee = SugarDecorator(coffee)  # 加糖
print(f"{coffee.description()}: ¥{coffee.cost()}")
# 普通咖啡 + 牛奶 + 糖: ¥14
```

### 为什么需要它

Java I/O 流（BufferedInputStream 包装 FileInputStream）就是经典的装饰器：`new BufferedInputStream(new FileInputStream("file"))`。

### 与继承的对比

| 方式 | 灵活性 | 组合方式 |
|------|--------|----------|
| 继承 | 编译时确定，静态 | 类爆炸（M 种组合需要 M 个子类） |
| 装饰器 | 运行时动态叠加 | 任意组合，N 个装饰器可拼出 2^N 种效果 |

---

## 5. 外观模式（Facade）

### 一句话定义

为子系统中的一组接口提供一个**统一的高层接口**，降低使用难度。

### 通俗类比

去医院看病——你不需要分别挂挂号、缴费、检查、取药的号，一个导诊台帮你搞定所有流程。

### 具体示例

```python
class CPU:
    def freeze(self): print("CPU 冻结")
    def execute(self): print("CPU 执行")

class Memory:
    def load(self): print("内存加载数据")

class HardDrive:
    def read(self): print("硬盘读取数据")

# 外观类 —— 封装复杂子系统
class ComputerFacade:
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

# 使用 —— 客户端只调一个方法
pc = ComputerFacade()
pc.start()
```

### 为什么需要它

简化复杂系统的使用，减少客户端与子系统的耦合。适用于分层架构中定义入口点。

---

## 6. 享元模式（Flyweight）

### 一句话定义

通过**共享**来高效地支持大量细粒度的对象。

### 通俗类比

字体渲染——屏幕上显示 1000 个"中"字，但字体文件里只存储了一个"中"的字形数据，所有"中"字共享这一个。

### 具体示例

```python
class FontFlyweight:
    def __init__(self, font_name):
        self.font_name = font_name

    def render(self, char):
        return f"[{self.font_name}:{char}]"

class FlyweightFactory:
    _fonts = {}

    @classmethod
    def get_font(cls, name):
        if name not in cls._fonts:
            cls._fonts[name] = FontFlyweight(name)
            print(f"创建新字体: {name}")
        return cls._fonts[name]

# 使用
fonts = []
for name in ["Arial", "Arial", "Arial", "Times", "Times"]:
    f = FlyweightFactory.get_font(name)
    fonts.append(f)

print(f"字体对象数量: {len(FlyweightFactory._fonts)}")  # 2（而不是 5）
```

### 为什么需要它

文本编辑器中大量相同格式的字符、游戏中的粒子效果、棋盘上的棋子等场景，避免为每个对象分配独立内存。

### 与相关术语的对比

| 对比项 | 享元模式 | 单例 | 对象池 |
|--------|---------|------|--------|
| 目的 | 共享细粒度对象 | 保证唯一实例 | 复用昂贵对象 |
| 对象数量 | 多个（同类共享） | 一个 | 固定数量 |
| 关键特征 | 内部状态共享 | 全局唯一 | 借用-归还 |

---

## 7. 代理模式（Proxy）

### 一句话定义

为其他对象提供一个**代理**来控制对它的访问。

### 通俗类比

房产中介——房东把房子委托给中介，中介代替房东处理看房、签约、收租等事务。你和房东不直接打交道。

### 具体示例

#### 静态代理

```python
class Image(ABC):
    @abstractmethod
    def display(self): pass

class RealImage(Image):
    def __init__(self, filename):
        self.filename = filename
        self._load_from_disk()

    def _load_from_disk(self):
        print(f"从磁盘加载 {self.filename}（耗时操作）")

    def display(self):
        print(f"显示 {self.filename}")

class ProxyImage(Image):
    def __init__(self, filename):
        self.filename = filename
        self._real = None

    def display(self):
        if self._real is None:
            self._real = RealImage(self.filename)  # 延迟加载
        self._real.display()

# 使用 —— 第一次 display 才真正加载
proxy = ProxyImage("photo.jpg")
proxy.display()  # 从磁盘加载 photo.jpg + 显示
proxy.display()  # 直接显示（不重复加载）
```

#### 动态代理（JDK）

```java
public class LogProxy implements InvocationHandler {
    private Object target;

    public LogProxy(Object target) {
        this.target = target;
    }

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

#### CGLIB 代理（无需接口）

```java
// CGLIB 通过继承实现代理，不要求目标类实现接口
Enhancer enhancer = new Enhancer();
enhancer.setSuperclass(UserService.class);
enhancer.setCallback((MethodInterceptor) (obj, method, args, proxy) -> {
    System.out.println("CGLIB 拦截");
    return proxy.invokeSuper(obj, args);
});
UserService proxy = (UserService) enhancer.create();
```

### 为什么需要它

远程代理（RPC）、虚拟代理（延迟加载）、保护代理（权限控制）、日志代理（AOP）。

### 三种代理对比

| 类型 | 实现方式 | 是否需要接口 | 适用场景 |
|------|---------|-------------|---------|
| 静态代理 | 手写代理类 | 需要 | 简单场景 |
| JDK 动态代理 | 反射 | 需要接口 | Spring AOP 默认 |
| CGLIB 代理 | 字节码生成子类 | 不需要 | 没有接口时 |

---

## 8. 过滤器模式（Filter）

### 一句话定义

使用不同的过滤器**独立地**组合条件，筛选符合要求的对象。

### 通俗类比

淘宝筛选商品——你可以同时勾选"品牌=Apple"、"价格<5000"、"评分>4.5"，每个条件是一个过滤器，组合使用。

### 具体示例

```python
from abc import ABC, abstractmethod

class Product:
    def __init__(self, name, color, size, price):
        self.name = name
        self.color = color
        self.size = size
        self.price = price

class Filter(ABC):
    @abstractmethod
    def matches(self, product): pass

class ColorFilter(Filter):
    def __init__(self, color):
        self.color = color
    def matches(self, product):
        return product.color == self.color

class PriceFilter(Filter):
    def __init__(self, max_price):
        self.max_price = max_price
    def matches(self, product):
        return product.price <= self.max_price

def filter_products(products, filters):
    result = products
    for f in filters:
        result = [p for p in result if f.matches(p)]
    return result

# 使用
products = [
    Product("iPhone", "黑色", "M", 7999),
    Product("小米", "白色", "M", 3999),
    Product("华为", "黑色", "L", 5999),
]
results = filter_products(products, [ColorFilter("黑色"), PriceFilter(6000)])
for p in results:
    print(p.name)  # 华为
```

### 为什么需要它

避免在代码中写大量嵌套 if-else，过滤器可以自由组合、复用，符合单一职责原则。

---

## 9. MVC 模式

### 一句话定义

将应用分为**模型（Model）、视图（View）、控制器（Controller）**三层，各司其职。

### 通俗类比

餐厅分工：后厨（Model）负责做菜，服务员（Controller）负责接单传菜，菜单（View）负责展示给顾客看。

### 具体示例

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    View     │◄────│  Controller │────►│    Model    │
│  (页面展示)  │     │  (处理请求)  │     │  (数据逻辑)  │
└─────────────┘     └─────────────┘     └─────────────┘
```

```python
# Model
class UserModel:
    def __init__(self):
        self.users = []
    def add_user(self, name):
        self.users.append(name)
    def get_users(self):
        return self.users.copy()

# View
class UserView:
    def show_users(self, users):
        for u in users:
            print(f"用户: {u}")

# Controller
class UserController:
    def __init__(self):
        self.model = UserModel()
        self.view = UserView()

    def add_user(self, name):
        self.model.add_user(name)
        self.view.show_users(self.model.get_users())

# 使用
ctrl = UserController()
ctrl.add_user("张三")  # 用户: 张三
```

### 为什么需要它

职责分离，Model 和 View 可以独立变化，支持多种 View（Web、移动端）共享同一个 Model。

---

## 10. MVVM 模式

### 一句话定义

将 View 和 ViewModel 通过**数据绑定**自动同步，ViewModel 负责业务逻辑和视图状态。

### 通俗类比

智能手表——你运动时（Model 产生数据），手表界面（View）自动更新，你不需要手动刷新，中间的处理器（ViewModel）自动同步。

### 具体示例

```javascript
// Vue.js 中的 MVVM
<template>
  <div>
    <input v-model="message" />
    <p>{{ reversedMessage }}</p>
  </div>
</template>

<script>
export default {
  data() {
    return { message: '' }       // Model（数据）
  },
  computed: {
    reversedMessage() {           // ViewModel（逻辑）
      return this.message.split('').reverse().join('')
    }
  }
}
</script>
```

### MVC vs MVVM

| 对比项 | MVC | MVVM |
|--------|-----|------|
| 数据同步 | 手动更新 View | 数据绑定自动同步 |
| View 的角色 | 主动从 Model 拉数据 | 被动接收 ViewModel 推送 |
| 适用场景 | 传统 Web 应用 | 现代前端框架（Vue、Angular） |

---

## 总结

```
结构型模式
├── 适配器模式 ——— 转换不兼容的接口
├── 桥接模式 ——— 分离抽象与实现
├── 组合模式 ——— 统一处理树形结构
├── 装饰器模式 ——— 动态添加职责
├── 外观模式 ——— 简化复杂子系统
├── 享元模式 ——— 共享细粒度对象
├── 代理模式 ——— 控制对象访问
├── 过滤器模式 ——— 灵活组合筛选条件
├── MVC 模式 ——— 模型-视图-控制器分离
└── MVVM 模式 ——— 数据驱动视图自动同步
```

> **选择建议**：接口不匹配用适配器；两个维度独立变化用桥接；树形结构用组合；需要动态扩展功能用装饰器；简化复杂系统用外观；大量相似对象用享元；需要控制访问用代理；多条件筛选用过滤器；Web 应用分层用 MVC/MVVM。
