---
title: "行为型模式（Behavioral Patterns）"
tags: ["设计模式", "行为型模式", "GoF", "面向对象设计"]
source: "baike"
source_path: "开发术语 / 设计模式"
collected: "2026-09-05"
status: "imported"
---

# 行为型模式（Behavioral Patterns）


> 📌 **导航**：本文是 **行为型模式（Behavioral Patterns）** 词条，属于 design-patterns 术语集。相关枢纽：[[创建型模式（Creational Patterns）]]、[[结构型模式（Structural Patterns）]]、[[行为型模式（Behavioral Patterns）]]。

> 行为型模式关注**对象之间的职责分配与通信方式**：描述一组对象如何协作完成单个对象无法独立完成的任务，以及如何管理算法、对象间关系与职责的流转。

---

## 概述与背景

行为型模式是 GoF《设计模式》三大类中数量最多的一类，共 **11 种**，本文全部收录。按实现手段分两类：

| 子类 | 机制 | 模式 |
|------|------|------|
| 类行为型 | 用**继承**在类之间分派行为 | 模板方法、解释器 |
| 对象行为型 | 用**组合/委托**在对象之间协作 | 策略、观察者、命令、状态、迭代器、责任链、中介者、备忘录、访问者 |

行为型模式共同解决的问题：

- **算法与流程的可替换/可扩展**（策略、模板方法）。
- **对象间松耦合的通信与协作**（观察者、中介者、责任链、命令）。
- **封装状态、请求、遍历与状态快照**（状态、命令、迭代器、备忘录）。
- **在不改元素类的前提下增加新操作 / 解释语言**（访问者、解释器）。

---

## 1. 策略模式（Strategy）

### 一句话定义

定义一系列算法，把它们各自**封装**起来并可**相互替换**，使算法的变化独立于使用它的客户端。

### 通俗类比

导航路线选择——去同一目的地，可选「最快路线」「最短路线」「不走高速」。算法不同但目标一致，可随时切换。

### 结构与角色

- **Strategy（策略接口）**：声明所有算法的公共方法。
- **ConcreteStrategy（具体策略）**：实现某一具体算法。
- **Context（上下文）**：持有一个 Strategy 引用，把计算委托给它（可运行时替换）。

### 具体示例

```python
from abc import ABC, abstractmethod

class SortStrategy(ABC):              # Strategy
    @abstractmethod
    def sort(self, data): ...

class BubbleSort(SortStrategy):       # ConcreteStrategy
    def sort(self, data):
        print("使用冒泡排序")
        return sorted(data)

class QuickSort(SortStrategy):
    def sort(self, data):
        print("使用快速排序")
        return sorted(data)

class Sorter:                         # Context
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy
    def set_strategy(self, strategy):  # 运行时替换算法
        self._strategy = strategy
    def do_sort(self, data):
        return self._strategy.sort(data)

sorter = Sorter(BubbleSort())
print(sorter.do_sort([3, 1, 2]))       # 冒泡排序
sorter.set_strategy(QuickSort())
print(sorter.do_sort([3, 1, 2]))       # 快速排序
```

> 说明：上例两个策略都调用 `sorted()` 只为演示「可替换」；真实场景中 BubbleSort / QuickSort 应有各自不同的实现与复杂度（冒泡 O(n²)、快排平均 O(n log n)）。

### 为什么需要它（应用场景）

- 同一功能有多种算法实现，需要在运行时按条件选择或切换（排序、压缩、计费规则、风控策略）。
- 希望用组合替代大量 `if-else`/`switch` 分支，新增算法符合开闭原则。

### 优点与局限

**优点**：算法可独立于客户端变化、可运行时切换、消除条件分支、符合开闭原则。
**局限**：策略数量增多会使类变多；客户端必须了解各策略的差异才能正确选择；对极简场景属于过度设计。

### 与相关术语的对比

| 对比项 | 策略模式 | 状态模式 | 模板方法 |
|--------|---------|---------|---------|
| 切换时机 | 客户端主动选择 | 内部状态自动切换 | 子类覆写步骤 |
| 关注点 | 算法的替换 | 对象状态的转换 | 流程骨架不变 |
| 实现手段 | 组合 | 组合 | 继承 |

---

## 2. 观察者模式（Observer）

### 一句话定义

定义对象间**一对多**的依赖，当一个对象（主题）状态改变时，所有依赖它的对象（观察者）都自动收到通知并更新。

### 通俗类比

微信公众号——你关注某个号（订阅），它每次发文（状态变化），你的订阅列表里就出现新文章（自动通知），号主无需知道具体是谁在看。

### 结构与角色

- **Subject（主题）**：维护观察者列表，提供 `attach`/`detach`/`notify`。
- **ConcreteSubject（具体主题）**：状态变化时通知所有观察者。
- **Observer（观察者接口）**：声明 `update`。
- **ConcreteObserver（具体观察者）**：收到通知后更新自身（常回查主题获取新状态）。

### 具体示例

```python
class EventEmitter:                  # 发布—订阅风格的事件通道
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event, *args, **kwargs):
        for cb in self._listeners.get(event, []):
            cb(*args, **kwargs)

emitter = EventEmitter()
emitter.on("login", lambda user: print(f"发送欢迎邮件给 {user}"))
emitter.on("login", lambda user: print(f"记录登录日志: {user}"))
emitter.emit("login", "张三")
# 发送欢迎邮件给 张三
# 记录登录日志: 张三
```

> 说明：上例是**发布—订阅**风格（通过事件通道解耦）。经典 GoF 观察者中，Subject 直接持有观察者列表并提供 `attach/detach/notify`，Observer 收到通知后回查 Subject——二者耦合更紧。下表区分两者。

#### Java — Spring Event（容器级发布—订阅）

```java
// 定义事件
public class OrderEvent extends ApplicationEvent {
    private final String orderId;
    public OrderEvent(Object source, String orderId) {
        super(source);
        this.orderId = orderId;
    }
    public String getOrderId() { return orderId; }
}

// 监听器
@Component
public class OrderEventListener {
    @EventListener
    public void handleOrderEvent(OrderEvent event) {
        System.out.println("订单创建: " + event.getOrderId());
    }
}
```

### 为什么需要它（应用场景）

- 松耦合的事件驱动：GUI 事件处理、消息队列、响应式编程、领域事件、配置热更新广播。
- 一个变化需要触发多个互不相关的后续动作，且不希望发起方硬编码这些动作。

### 优点与局限

**优点**：主题与观察者松耦合、支持广播、新增观察者符合开闭原则。
**局限**：通知顺序通常不应被依赖；观察者过多时通知开销大；若通知链过长易引发「雪崩」或难以调试的连锁更新。

### 发布—订阅 vs 观察者

| 对比项 | 观察者模式 | 发布—订阅模式 |
|--------|-----------|-------------|
| 耦合度 | 主题直接持有观察者引用 | 通过消息中间件/事件通道解耦 |
| 通知方式 | 主题直接通知观察者 | 发布者发到通道，通道分发给订阅者 |
| 是否知晓对方 | 主题知道观察者集合 | 发布者与订阅者互不感知 |

---

## 3. 命令模式（Command）

### 一句话定义

将一个**请求封装为对象**，从而可以用不同请求对客户参数化，支持请求排队、记录日志与**可撤销**操作。

### 通俗类比

餐厅点菜单——写在纸上的是「命令对象」，服务员不关心谁点的、何时点的，只按单执行；单子还能修改、撤销、重下。

### 结构与角色

- **Command（命令接口）**：声明 `execute`（及可选的 `undo`）。
- **ConcreteCommand（具体命令）**：绑定一个 Receiver 与一个动作。
- **Receiver（接收者）**：真正执行与请求相关的业务逻辑。
- **Invoker（调用者）**：持有命令并触发 `execute`（可排队、记录历史）。
- **Client（客户端）**：创建具体命令并设置其接收者。

### 具体示例

```python
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self): ...
    @abstractmethod
    def undo(self): ...

class TextEditor:                     # Receiver
    def __init__(self):
        self.text = ""

class InsertCommand(Command):         # ConcreteCommand
    def __init__(self, editor, text):
        self.editor = editor
        self.text = text
    def execute(self):
        self.editor.text += self.text
    def undo(self):
        self.editor.text = self.editor.text[:-len(self.text)]

class CommandManager:                 # Invoker
    def __init__(self):
        self._history = []
    def execute(self, command):
        command.execute()
        self._history.append(command)
    def undo(self):
        if self._history:
            self._history.pop().undo()

editor = TextEditor()
manager = CommandManager()
manager.execute(InsertCommand(editor, "Hello "))
manager.execute(InsertCommand(editor, "World"))
print(editor.text)                    # Hello World
manager.undo()
print(editor.text)                    # Hello 
```

### 为什么需要它（应用场景）

- 撤销/重做（文本编辑器、绘图软件）、命令队列与任务调度、宏命令（批量执行）、事务与回滚、操作日志与审计。

### 优点与局限

**优点**：调用者与接收者解耦、命令可组合/排队/持久化、易于实现撤销重做、新增命令符合开闭原则。
**局限**：命令类数量可能急剧增多；实现完整的 undo/redo（尤其涉及复杂状态）成本较高。

---

## 4. 状态模式（State）

### 一句话定义

允许对象在其**内部状态改变时改变行为**，对外看起来就像改变了它的类。

### 通俗类比

游戏角色状态——同一角色在「正常」下可跑步，在「受伤」下只能走，在「眩晕」下不能动。行为随状态而变，而非靠一堆 `if 状态==...`。

### 结构与角色

- **State（状态接口）**：声明与某一状态相关的行为。
- **ConcreteState（具体状态）**：实现该状态下的行为，并决定何时切换到其他状态。
- **Context（上下文）**：持有当前 State 引用，把行为委托给它。

### 具体示例

```python
from abc import ABC, abstractmethod

class State(ABC):
    @abstractmethod
    def handle(self, context): ...

class NormalState(State):
    def handle(self, context):
        print("正常状态: 可以移动")
        context.state = RunningState()      # 状态转换封装在状态内部

class RunningState(State):
    def handle(self, context):
        print("跑步状态: 加速移动")
        context.state = NormalState()

class InjuredState(State):
    def handle(self, context):
        print("受伤状态: 只能缓慢移动")

class Character:                            # Context
    def __init__(self):
        self._state = NormalState()
    @property
    def state(self): return self._state
    @state.setter
    def state(self, state): self._state = state
    def move(self):
        self._state.handle(self)            # 委托给当前状态

char = Character()
char.move()                                 # 正常状态: 可以移动
char.move()                                 # 跑步状态: 加速移动
char.state = InjuredState()
char.move()                                 # 受伤状态: 只能缓慢移动
```

### 为什么需要它（应用场景）

- 对象行为强依赖其状态，且状态较多、转换规则复杂（订单状态机、审批流转、TCP 连接状态、游戏角色状态）。
- 希望消除散落在各处的大型 `if-else`/`switch` 状态判断。

### 优点与局限

**优点**：把状态相关行为局部化到各 State 类、消除庞杂条件分支、状态转换显式化、新增状态符合开闭原则。
**局限**：状态很少或转换简单时属于过度设计；状态类之间存在依赖（一个状态需知道下一个状态），可能分散转换逻辑。

### 状态模式 vs 策略模式

| 对比项 | 状态模式 | 策略模式 |
|--------|---------|---------|
| 切换主体 | 对象内部自动切换 | 客户端主动切换 |
| 目的 | 行为随内部状态变化 | 选择可替换的算法 |
| 各实现间关系 | 状态之间有转换关系 | 策略之间通常互不相关 |

---

## 5. 模板方法模式（Template Method）

### 一句话定义

在父类中定义一个算法的**骨架**，而将其中某些步骤延迟到子类实现，使子类不改变算法结构即可重定义特定步骤。

### 通俗类比

泡茶与泡咖啡流程都是：烧水 → 冲泡 → 倒入杯中 → 加料。前后步骤一样，只有「冲泡」和「加料」因饮品而异。

### 结构与角色

- **AbstractClass（抽象类）**：定义**模板方法**（算法骨架，通常用 `final` 防止覆写）、若干**抽象步骤**（子类必须实现）与**钩子方法**（hook，有默认实现、子类可选覆写）。
- **ConcreteClass（具体子类）**：实现抽象步骤、按需覆写钩子。

### 具体示例

```python
from abc import ABC, abstractmethod

class Beverage(ABC):
    def prepare(self):                # 模板方法：定义不变的流程骨架
        self.boil_water()
        self.brew()
        self.pour_in_cup()
        if self.customer_wants_condiments():   # 钩子方法
            self.add_condiments()

    def boil_water(self):             # 公共步骤（父类实现）
        print("烧开水")

    def pour_in_cup(self):
        print("倒入杯中")

    def customer_wants_condiments(self) -> bool:  # 钩子：默认 True，子类可覆写
        return True

    @abstractmethod
    def brew(self): ...               # 抽象步骤：子类必须实现

    @abstractmethod
    def add_condiments(self): ...

class Tea(Beverage):
    def brew(self): print("浸泡茶叶")
    def add_condiments(self): print("加柠檬")

class Coffee(Beverage):
    def brew(self): print("冲泡咖啡粉")
    def add_condiments(self): print("加糖和牛奶")

Tea().prepare()
# 烧开水 / 浸泡茶叶 / 倒入杯中 / 加柠檬
```

### 为什么需要它（应用场景）

- 多个流程骨架相同、仅个别步骤不同（数据导出、报表生成、框架的生命周期回调、ETL 流程）。
- 框架中由父类控制流程、把可变点交给使用者实现（好莱坞原则：「别调用我们，我们会调用你」）。

### 优点与局限

**优点**：复用不变的代码、把变化点集中到子类、由父类统一控制流程。
**局限**：基于继承，灵活性不如组合（Java 单继承限制）；子类实现会影响父类流程的结果，反向控制增加理解成本；步骤越多越难维护。

### 模板方法 vs 策略模式

| 对比项 | 模板方法 | 策略模式 |
|--------|---------|---------|
| 实现手段 | 继承 | 组合/委托 |
| 算法粒度 | 复用算法的一部分步骤 | 替换整个算法 |
| 灵活性 | 编译期确定 | 运行时切换 |

---

## 6. 迭代器模式（Iterator）

### 一句话定义

提供一种方法**顺序访问**聚合对象中的各个元素，而**不暴露其底层表示**。

### 通俗类比

遥控器上的「下一个」按钮——你不必知道频道列表是数组还是链表，按一下就跳到下一个。

### 结构与角色

- **Iterator（迭代器接口）**：声明 `hasNext`/`next`（或语言内建的迭代协议）。
- **ConcreteIterator（具体迭代器）**：实现遍历，跟踪当前位置。
- **Aggregate（聚合接口）**：声明创建迭代器的方法。
- **ConcreteAggregate（具体聚合）**：返回其对应的具体迭代器。

### 具体示例

```python
class Book:
    def __init__(self, title):
        self.title = title

class BookShelf:                      # Aggregate：实现 __iter__ 即可被遍历
    def __init__(self):
        self._books = []
    def add(self, book):
        self._books.append(book)
    def __iter__(self):               # 不暴露 _books 的内部结构
        return iter(self._books)

shelf = BookShelf()
shelf.add(Book("设计模式"))
shelf.add(Book("代码整洁之道"))
shelf.add(Book("重构"))
for book in shelf:                    # Python 的 for...in 即迭代器模式
    print(book.title)
```

### 为什么需要它（应用场景）

- 统一遍历不同底层结构的集合（数组、链表、树、图），对客户端隐藏实现。
- 支持多种遍历方式（正序、逆序、过滤、深度/广度优先）。
- Python 的 `for...in`/生成器、Java 的 `Iterator`/`Iterable`、C# 的 `IEnumerable` 都是该模式的体现。

### 优点与局限

**优点**：遍历与集合实现解耦、支持多种遍历、新增集合类型符合开闭原则。
**局限**：对简单集合，直接用语言内建遍历即可，另建迭代器反而繁琐；某些复杂遍历（如需回溯）实现成本较高。

---

## 7. 责任链模式（Chain of Responsibility）

### 一句话定义

使多个对象都有机会处理请求，从而避免请求的发送者与接收者耦合；将这些对象连成一条链，沿链传递请求，直到有对象处理它。

### 通俗类比

公司报销审批——组长 → 部门经理 → 总监 → CFO，金额小的组长批了即可，金额大的一路往上，直到有人能处理。

### 结构与角色

- **Handler（处理者接口）**：声明 `handle`，并持有对下一个处理者的引用。
- **ConcreteHandler（具体处理者）**：能处理则处理，否则转发给后继。
- **Client**：组装链并发起请求。

### 具体示例

```python
from abc import ABC, abstractmethod

class Handler(ABC):
    def __init__(self):
        self._next = None
    def set_next(self, handler):
        self._next = handler
        return handler                # 支持链式组装
    @abstractmethod
    def handle(self, amount): ...
    def pass_to_next(self, amount):
        if self._next:
            return self._next.handle(amount)
        return "没有更多审批人了"

class TeamLeader(Handler):
    def handle(self, amount):
        if amount <= 1000:
            return f"组长审批通过: ¥{amount}"
        return self.pass_to_next(amount)

class DepartmentManager(Handler):
    def handle(self, amount):
        if amount <= 10000:
            return f"部门经理审批通过: ¥{amount}"
        return self.pass_to_next(amount)

class CFO(Handler):
    def handle(self, amount):
        return f"CFO审批通过: ¥{amount}"

chain = TeamLeader()
chain.set_next(DepartmentManager()).set_next(CFO())
print(chain.handle(500))     # 组长审批通过: ¥500
print(chain.handle(5000))    # 部门经理审批通过: ¥5000
print(chain.handle(50000))   # CFO审批通过: ¥50000
```

### 为什么需要它（应用场景）

- Web 中间件（Express/Koa/Gin 的 `next()`）、Servlet Filter、审批流、异常处理链、日志分级、DOM 事件冒泡。
- 发送者无需知道最终由谁处理，链的组成可动态调整。

### 优点与局限

**优点**：发送者与接收者解耦、链可动态增删/重排、每个处理者职责单一、符合开闭原则。
**局限**：请求可能到达链尾仍未被处理（需兜底）；链过长会影响性能与调试；不易观察整条链的运行特征。

### 常见误区

- ❌ 以为责任链保证「一定有人处理」。若链上无人处理且无兜底，请求可能被静默丢弃——应设置默认处理者或显式报错。

---

## 8. 中介者模式（Mediator）

### 一句话定义

用一个**中介对象**封装一组对象之间的交互，使各对象不必显式相互引用，从而松耦合，并可独立改变它们的交互。

### 通俗类比

机场塔台——飞机之间不直接通信，都通过塔台协调。塔台掌握全局、统一调度，避免飞机两两喊话造成混乱。

### 结构与角色

- **Mediator（中介者接口）**：声明与各同僚通信的方法。
- **ConcreteMediator（具体中介者）**：持有各同僚引用，协调它们的交互。
- **Colleague（同僚类）**：与中介者通信，而非彼此直接通信。

### 具体示例

```python
class ChatRoom:                       # ConcreteMediator
    def __init__(self):
        self._users = {}
    def register(self, user):
        self._users[user.name] = user
    def send(self, message, from_user, to_name=None):
        if to_name:
            self._users[to_name].receive(message, from_user.name)
        else:
            for name, user in self._users.items():
                if name != from_user.name:
                    user.receive(message, from_user.name)

class User:                           # Colleague
    def __init__(self, name, room):
        self.name = name
        self.room = room
        room.register(self)
    def send(self, message, to_name=None):
        self.room.send(message, self, to_name)   # 只与中介者通信
    def receive(self, message, from_name):
        print(f"{self.name} 收到 {from_name}: {message}")

room = ChatRoom()
alice, bob, charlie = User("Alice", room), User("Bob", room), User("Charlie", room)
alice.send("大家好!")                 # Bob/Charlie 都收到
bob.send("你好 Alice!", "Alice")      # 只有 Alice 收到
```

### 为什么需要它（应用场景）

- 多对象之间形成「网状」引用、交互逻辑分散难维护时，用一个中心协调者收敛（聊天室、MVC 的 Controller、表单控件联动、微服务编排、航空/铁路调度）。

### 优点与局限

**优点**：把「多对多」交互降为「一对多」、同僚间解耦、交互逻辑集中可复用、可独立改变协作方式。
**局限**：中介者容易膨胀成难以维护的「上帝对象」——把过多逻辑塞进中介者会适得其反。

### 复杂度对比

N 个对象两两交互最多需要 N×(N−1)/2 条连接；引入中介者后降为 N 条（每个同僚只连中介者），把网状拓扑变为星型拓扑。

### 与观察者的对比

| 对比项 | 中介者模式 | 观察者模式 |
|--------|-----------|-----------|
| 通信方式 | 对象间（经中介）双向协调 | 一对多的单向通知 |
| 中心节点 | 有（中介者） | 无独立中间件（主题直接通知观察者） |
| 关注点 | 管理一组对象的交互规则 | 管理订阅与广播 |

---

## 9. 备忘录模式（Memento）

### 一句话定义

在**不破坏封装**的前提下，捕获并在对象外部保存其内部状态，以便日后将对象恢复到该状态。

### 通俗类比

游戏存档——打 Boss 前存个档，打不过就读档重来，无需从头再玩；存档文件不暴露游戏内部实现细节。

### 结构与角色

- **Originator（发起人）**：创建备忘录记录当前状态，并能用备忘录恢复状态。
- **Memento（备忘录）**：存储发起人的内部状态；对 caretaker 应是「不透明」的（不可被随意读写）。
- **Caretaker（管理者）**：负责保存备忘录，但**不能修改或查看**其内容。

### 具体示例

```python
class Memento:                        # 备忘录：状态快照
    def __init__(self, state):
        self._state = state
    def get_state(self):
        return self._state

class Editor:                         # Originator
    def __init__(self):
        self._text = ""
    def type(self, words):
        self._text += words
    def save(self):
        return Memento(self._text)
    def restore(self, memento):
        self._text = memento.get_state()
    def __str__(self):
        return self._text

class Caretaker:                      # 管理者：只保管，不改内容
    def __init__(self):
        self._history = []
    def save(self, editor):
        self._history.append(editor.save())
    def undo(self, editor):
        if self._history:
            editor.restore(self._history.pop())

editor, caretaker = Editor(), Caretaker()
caretaker.save(editor)
editor.type("第一段文字")
caretaker.save(editor)
editor.type(" 第二段文字")
print(editor)                         # 第一段文字 第二段文字
caretaker.undo(editor)
print(editor)                         # 第一段文字
```

### 为什么需要它（应用场景）

- 撤销/回滚、事务补偿、快照与恢复（编辑器历史、数据库事务保存点、游戏存档、状态机快照）。

### 优点与局限

**优点**：提供可靠的状态恢复能力、不暴露对象内部细节（保持封装）。
**局限**：状态较大时，频繁保存快照会**消耗大量内存**；caretaker 需管理备忘录生命周期，可能引入资源开销。

### 常见误区

- ❌ 备忘录 = 直接暴露 getter/setter 存全部字段。备忘录的关键是**对 caretaker 不透明**、只由 originator 解读，从而不破坏封装。

---

## 10. 访问者模式（Visitor）

### 一句话定义

表示一个作用于某对象结构中各元素的操作，使你**在不改变各元素类**的前提下，定义作用于这些元素的**新操作**。

### 通俗类比

体检中心——体检项目（操作）每年可能新增，但「人」（元素）不变。新增一项检查，不必修改「人」这个类，只需新增一个「体检项目」访问者。

### 结构与角色

- **Visitor（访问者接口）**：为每种 ConcreteElement 声明一个 `visitXxx` 方法。
- **ConcreteVisitor（具体访问者）**：实现各 `visitXxx`，承载新操作。
- **Element（元素接口）**：声明 `accept(visitor)`。
- **ConcreteElement（具体元素）**：实现 `accept`，回调 `visitor.visitXxx(this)`。
- **ObjectStructure（对象结构）**：容纳元素集合，提供遍历入口。
- 关键机制：**双分派（double dispatch）**——先由元素类型分派到 `accept`，再由 visitor 类型分派到 `visitXxx`。

### 具体示例

```python
from abc import ABC, abstractmethod

class Element(ABC):
    @abstractmethod
    def accept(self, visitor): ...

class Book(Element):                  # ConcreteElement
    def __init__(self, price):
        self.price = price
    def accept(self, visitor):
        return visitor.visit_book(self)   # 回调访问者，传入自身

class Fruit(Element):
    def __init__(self, price, weight):
        self.price = price
        self.weight = weight
    def accept(self, visitor):
        return visitor.visit_fruit(self)

class Visitor(ABC):
    @abstractmethod
    def visit_book(self, book): ...
    @abstractmethod
    def visit_fruit(self, fruit): ...

class PriceCalculator(Visitor):       # ConcreteVisitor
    def visit_book(self, book):
        return book.price * 0.8       # 书籍八折
    def visit_fruit(self, fruit):
        return fruit.price * fruit.weight   # 水果按重量计价

items = [Book(100), Fruit(10, 2)]
calc = PriceCalculator()
total = sum(item.accept(calc) for item in items)
print(f"总价: ¥{total}")              # 总价: ¥100（80 + 20）
```

### 为什么需要它（应用场景）

- 对象结构**稳定**但需频繁增加**新操作**：编译器对 AST 执行类型检查/代码生成/优化；文件系统遍历做统计/压缩/权限校验；报表对固定数据结构做多维度计算。

### 优点与局限

**优点**：新增操作非常容易（加一个 Visitor 即可）、把分散在各元素中的相关行为集中到一个访问者、符合单一职责。
**局限（关键权衡）**：**新增元素类型很困难**——每加一种 Element，所有 Visitor 接口及其实现都要改，违反开闭原则；且访问者需能访问元素内部数据，可能破坏封装。故适用于「元素种类稳定、操作多变」的场景。

### 常见误区

- ❌ 以为访问者对「新增元素」也开闭。恰恰相反——访问者对**新增操作**友好，对**新增元素类型**很不友好，这是它最大的取舍。

---

## 11. 解释器模式（Interpreter）

### 一句话定义

给定一个语言，定义其**文法的一种表示**，并定义一个**解释器**，用该文法表示来解释语言中的句子。

### 通俗类比

翻译官——把「一种语言的句子」按规则翻译成「另一种语言」；解释器则是把符合文法的表达式解析并求值。

### 结构与角色

- **AbstractExpression（抽象表达式）**：声明 `interpret`。
- **TerminalExpression（终结符表达式）**：实现文法中终结符的解释。
- **NonterminalExpression（非终结符表达式）**：实现文法中规则的解释，通常递归调用子表达式。
- **Context（上下文）**：存放解释器共享的全局信息。

### 具体示例

```python
from abc import ABC, abstractmethod   # 原示例缺此导入，已补

class Expression(ABC):                # AbstractExpression
    @abstractmethod
    def interpret(self) -> int: ...

class Number(Expression):             # TerminalExpression
    def __init__(self, value):
        self.value = int(value)
    def interpret(self) -> int:
        return self.value

class Add(Expression):                # NonterminalExpression
    def __init__(self, left, right):
        self.left, self.right = left, right
    def interpret(self) -> int:
        return self.left.interpret() + self.right.interpret()

class Multiply(Expression):
    def __init__(self, left, right):
        self.left, self.right = left, right
    def interpret(self) -> int:
        return self.left.interpret() * self.right.interpret()

# 对应表达式 "3 + 5 * 2"（已按优先级构建好抽象语法树）
expr = Add(Number("3"), Multiply(Number("5"), Number("2")))
print(expr.interpret())               # 13
```

> 说明：解释器模式通常只负责「解释已构建好的语法树」，把字符串解析成语法树一般由专门的解析器（parser）完成；复杂文法建议直接用 ANTLR 等解析器生成工具，而非手写解释器。

### 为什么需要它（应用场景）

- 简单 DSL（领域特定语言）、数学表达式求值、SQL/正则的语法解释、规则引擎、脚本语言。
- 适用前提：**文法简单且相对稳定**；文法复杂时类数量爆炸、效率低，应改用专业解析工具。

### 优点与局限

**优点**：文法即类结构，扩展文法规则（新增表达式类）较容易、易实现简单语言。
**局限**：文法复杂时会导致类爆炸、难以维护；解释执行效率低。复杂语言/文法不建议使用本模式。

---

## 常见误区（跨模式）

- **策略 vs 状态**：结构相似，意图不同——策略由**客户端主动选择**可替换的算法，各策略间通常无关联；状态由**对象内部自动切换**，各状态间存在转换关系。
- **命令 vs 策略**：命令把「请求」封装成对象（强调解耦调用与执行、支持排队/撤销）；策略把「算法」封装成对象（强调可替换）。
- **观察者 vs 中介者**：观察者是一对多的单向广播；中介者收敛多个同僚间的多向交互。
- **备忘录 vs 命令的撤销**：备忘录保存「状态快照」；命令的 undo 保存「逆操作」。二者都能实现撤销，但机制不同，可结合使用。
- **模板方法 vs 策略**：模板方法用继承、复用算法的部分步骤；策略用组合、替换整个算法且可运行时切换。

## 相关术语与前置知识

- **设计原则**：开闭原则、单一职责、依赖倒置、里氏替换、迪米特法则。
- **前置知识**：接口/抽象类、继承 vs 组合、多态与动态分派（访问者的「双分派」）、回调与闭包、事件驱动。
- **相关模式**：结构型的组合（常与迭代器、访问者配合遍历对象结构）、观察者（构成 MVC 的核心）、创建型的工厂（创建命令/策略）。

## 参考资料

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides.《设计模式：可复用面向对象软件的基础》（*Design Patterns: Elements of Reusable Object-Oriented Software*）. Addison-Wesley, 1994. ISBN 0-201-63361-2.（11 种 GoF 行为型模式的权威来源）
2. Joshua Bloch.《Effective Java》（第 3 版）. Addison-Wesley, 2018. ISBN 978-0-13-468599-1.（Item 42：lambda 与函数式接口对策略/命令等模式的简化与取舍）
3. 关于**解释器**与专业解析工具的选型：可参考 ANTLR 等解析器生成器的官方文档（**建议人工核验**具体版本与用法）。

> 说明：为避免虚构，未列出具体 URL 与页码；相关框架/工具的精确出处建议人工核验。

## 总结

```
行为型模式（GoF 11 种）
├── 策略（Strategy）——————— 封装可互换的算法，运行时选择
├── 观察者（Observer）————— 一对多依赖，状态变化自动通知
├── 命令（Command）———————— 将请求封装为对象，支持排队/撤销
├── 状态（State）————————— 行为随内部状态改变而改变
├── 模板方法（Template Method）— 父类定骨架，子类填步骤
├── 迭代器（Iterator）————— 顺序访问元素而不暴露内部结构
├── 责任链（Chain of Responsibility）— 请求沿链传递直到被处理
├── 中介者（Mediator）————— 用中心节点协调多对象交互
├── 备忘录（Memento）————— 不破坏封装地保存与恢复状态
├── 访问者（Visitor）————— 不改元素类即新增操作（双分派）
└── 解释器（Interpreter）—— 定义文法表示并解释执行句子
```

> **选择建议**：动态切换算法→策略；一对多的松耦合通知→观察者；需要撤销/排队/日志→命令；复杂状态与转换→状态；固定流程可变步骤→模板方法；统一遍历集合→迭代器；请求处理者链式解耦→责任链；多对象网状交互→中介者；保存/恢复状态快照→备忘录；结构稳定但操作多变→访问者；简单 DSL/文法→解释器（复杂文法改用专业解析器）。

---
