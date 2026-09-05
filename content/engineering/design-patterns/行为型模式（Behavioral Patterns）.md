---
title: "行为型模式（Behavioral Patterns）"
tags: []
source: "baike"
source_path: "开发术语 / 设计模式"
collected: "2026-09-05"
status: "imported"
---

# 行为型模式（Behavioral Patterns）

> 行为型模式关注**对象之间的职责分配和通信方式**。它们描述对象如何协作完成复杂任务，以及如何管理算法、对象间的关系和职责。

---

## 1. 策略模式（Strategy）

### 一句话定义

定义一系列算法，把它们各自封装起来，并且可以互相替换。

### 通俗类比

导航路线选择——去同一个目的地，你可以选"最快路线"、"最短路线"或"不走高速"。路线算法不同，但目的地一样，随时可以切换。

### 具体示例

```python
from abc import ABC, abstractmethod

class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data): pass

class BubbleSort(SortStrategy):
    def sort(self, data):
        print("使用冒泡排序")
        return sorted(data)

class QuickSort(SortStrategy):
    def sort(self, data):
        print("使用快速排序")
        return sorted(data)

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy):
        self._strategy = strategy

    def do_sort(self, data):
        return self._strategy.sort(data)

# 使用 —— 运行时切换算法
sorter = Sorter(BubbleSort())
print(sorter.do_sort([3, 1, 2]))  # 冒泡排序

sorter.set_strategy(QuickSort())
print(sorter.do_sort([3, 1, 2]))  # 快速排序
```

### 为什么需要它

避免大量 if-else 或 switch 判断算法选择，符合开闭原则——新增算法不需要修改已有代码。

### 与相关术语的对比

| 对比项 | 策略模式 | 状态模式 | 模板方法 |
|--------|---------|---------|---------|
| 切换时机 | 客户端主动选择 | 内部状态自动切换 | 子类覆写钩子 |
| 关注点 | 算法的替换 | 对象状态的转换 | 流程骨架不变 |
| 数量 | 通常多个策略 | 通常多个状态 | 一个模板 |

---

## 2. 观察者模式（Observer）

### 一句话定义

当一个对象状态变化时，所有依赖它的对象都会自动收到通知并更新。

### 通俗类比

微信公众号——你关注了某个号（订阅），它每次发文章（状态变化），你的订阅列表里就会出现新文章（自动通知）。

### 具体示例

```python
class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event, *args, **kwargs):
        for cb in self._listeners.get(event, []):
            cb(*args, **kwargs)

# 使用 —— 发布-订阅模式
emitter = EventEmitter()

def on_user_login(user):
    print(f"发送欢迎邮件给 {user}")

def on_user_login_log(user):
    print(f"记录登录日志: {user}")

emitter.on("login", on_user_login)
emitter.on("login", on_user_login_log)

emitter.emit("login", "张三")
# 发送欢迎邮件给 张三
# 记录登录日志: 张三
```

#### Java — Spring Event

```java
// 定义事件
public class OrderEvent extends ApplicationEvent {
    private String orderId;
    public OrderEvent(Object source, String orderId) {
        super(source);
        this.orderId = orderId;
    }
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

### 为什么需要它

松耦合——发布者不需要知道谁在监听，订阅者之间也互不影响。广泛用于 GUI 事件处理、消息队列、响应式编程。

### 发布-订阅 vs 观察者

| 对比项 | 观察者模式 | 发布-订阅模式 |
|--------|-----------|-------------|
| 耦合度 | 发布者知道观察者 | 通过中间件解耦 |
| 通知方式 | 直接通知 | 通过事件通道 |
| 复杂度 | 简单 | 稍复杂 |

---

## 3. 命令模式（Command）

### 一句话定义

将请求封装为**对象**，使你可以参数化操作、排队执行、记录日志，甚至支持撤销。

### 通俗类比

餐厅点菜单——你写在纸上的是"命令对象"，服务员不关心谁点的、什么时候点的，只按单子执行。你可以修改、撤销、重新下单。

### 具体示例

```python
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self): pass
    @abstractmethod
    def undo(self): pass

class TextEditor:
    def __init__(self):
        self.text = ""

class InsertCommand(Command):
    def __init__(self, editor, text):
        self.editor = editor
        self.text = text

    def execute(self):
        self.editor.text += self.text

    def undo(self):
        self.editor.text = self.editor.text[:-len(self.text)]

class CommandManager:
    def __init__(self):
        self._history = []

    def execute(self, command):
        command.execute()
        self._history.append(command)

    def undo(self):
        if self._history:
            self._history.pop().undo()

# 使用
editor = TextEditor()
manager = CommandManager()

manager.execute(InsertCommand(editor, "Hello "))
manager.execute(InsertCommand(editor, "World"))
print(editor.text)  # Hello World

manager.undo()
print(editor.text)  # Hello 
```

### 为什么需要它

支持撤销/重做（文本编辑器）、命令队列（任务调度）、宏命令（批量执行）、事务回滚。

---

## 4. 状态模式（State）

### 一句话定义

允许对象在内部状态改变时改变其行为，看起来像改变了对象的类。

### 通俗类比

游戏角色状态——同一角色在"正常状态"下可以跑步，在"受伤状态"下只能走路，在"眩晕状态"下不能移动。行为随状态变化。

### 具体示例

```python
from abc import ABC, abstractmethod

class State(ABC):
    @abstractmethod
    def handle(self, context): pass

class NormalState(State):
    def handle(self, context):
        print("正常状态: 可以移动")
        context.state = RunningState()

class RunningState(State):
    def handle(self, context):
        print("跑步状态: 加速移动")
        context.state = NormalState()

class InjuredState(State):
    def handle(self, context):
        print("受伤状态: 只能缓慢移动")

class Character:
    def __init__(self):
        self._state = NormalState()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    def move(self):
        self._state.handle(self)

# 使用
char = Character()
char.move()  # 正常状态: 可以移动
char.move()  # 跑步状态: 加速移动
char.state = InjuredState()
char.move()  # 受伤状态: 只能缓慢移动
```

### 为什么需要它

消除复杂的条件分支，状态转换逻辑集中在各 State 类中，而不是散落在代码各处。

### 状态模式 vs 策略模式

| 对比项 | 状态模式 | 策略模式 |
|--------|---------|---------|
| 切换主体 | 对象自己切换 | 客户端切换 |
| 目的 | 行为随状态变化 | 选择算法 |
| 状态之间 | 有转换关系 | 互不相关 |

---

## 5. 模板方法模式（Template Method）

### 一句话定义

在父类中定义算法的**骨架**，将某些步骤延迟到子类实现。

### 通俗类比

泡茶和泡咖啡的流程都是：烧水 → 冲泡 → 倒入杯中 → 加料。前三步一样，但"冲泡"和"加料"不同。

### 具体示例

```python
from abc import ABC, abstractmethod

class Beverage(ABC):
    def prepare(self):  # 模板方法 —— 定义流程骨架
        self.boil_water()
        self.brew()
        self.pour_in_cup()
        self.add_condiments()

    def boil_water(self):
        print("烧开水")

    def pour_in_cup(self):
        print("倒入杯中")

    @abstractmethod
    def brew(self): pass

    @abstractmethod
    def add_condiments(self): pass

class Tea(Beverage):
    def brew(self):
        print("浸泡茶叶")

    def add_condiments(self):
        print("加柠檬")

class Coffee(Beverage):
    def brew(self):
        print("冲泡咖啡粉")

    def add_condiments(self):
        print("加糖和牛奶")

# 使用
tea = Tea()
tea.prepare()
# 烧开水
# 浸泡茶叶
# 倒入杯中
# 加柠檬
```

### 为什么需要它

复用不变的部分（boil_water、pour_in_cup），只让子类定制变化的部分（brew、add_condiments）。

### 模板方法 vs 策略模式

| 对比项 | 模板方法 | 策略模式 |
|--------|---------|---------|
| 实现方式 | 继承 | 组合 |
| 算法骨架 | 固定在父类 | 由策略对象提供 |
| 灵活性 | 编译时确定 | 运行时切换 |

---

## 6. 迭代器模式（Iterator）

### 一句话定义

提供一种方法顺序访问集合元素，而不暴露其底层表示。

### 通俗类比

遥控器上的"下一个"按钮——你不需要知道电视台列表是怎么存的，按一下就跳到下一个。

### 具体示例

```python
class Book:
    def __init__(self, title):
        self.title = title

class BookShelf:
    def __init__(self):
        self._books = []

    def add(self, book):
        self._books.append(book)

    def __iter__(self):
        return iter(self._books)

# 使用 —— Python 的 for 循环就是迭代器
shelf = BookShelf()
shelf.add(Book("设计模式"))
shelf.add(Book("代码整洁之道"))
shelf.add(Book("重构"))

for book in shelf:
    print(book.title)
```

### 为什么需要它

隐藏集合的内部结构（数组、链表、树），提供统一的遍历接口。Python 的 `for...in` 和 Java 的 `Iterator` 都是迭代器模式的体现。

---

## 7. 责任链模式（Chain of Responsibility）

### 一句话定义

将请求沿着处理者链传递，直到有一个处理者处理它为止。

### 通俗类比

公司报销审批——组长 → 部门经理 → 总监 → CFO，金额小的组长批了就行，金额大的要一路往上。

### 具体示例

```python
from abc import ABC, abstractmethod

class Handler(ABC):
    def __init__(self):
        self._next = None

    def set_next(self, handler):
        self._next = handler
        return handler  # 支持链式调用

    @abstractmethod
    def handle(self, amount): pass

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

# 构建责任链
chain = TeamLeader()
chain.set_next(DepartmentManager()).set_next(CFO())

print(chain.handle(500))     # 组长审批通过: ¥500
print(chain.handle(5000))    # 部门经理审批通过: ¥5000
print(chain.handle(50000))   # CFO审批通过: ¥50000
```

### 为什么需要它

解耦请求发送者和接收者，处理者可以动态调整。常见于 Web 中间件、审批流、异常处理链。

---

## 8. 中介者模式（Mediator）

### 一句话定义

用一个中介对象封装一组对象之间的交互，使对象不需要显式地互相引用。

### 通俗类比

机场塔台——飞机之间不直接通信，都通过塔台协调。塔台知道所有飞机的位置，统一调度。

### 具体示例

```python
class ChatRoom:
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

class User:
    def __init__(self, name, room):
        self.name = name
        self.room = room
        room.register(self)

    def send(self, message, to_name=None):
        self.room.send(message, self, to_name)

    def receive(self, message, from_name):
        print(f"{self.name} 收到 {from_name}: {message}")

# 使用
room = ChatRoom()
alice = User("Alice", room)
bob = User("Bob", room)
charlie = User("Charlie", room)

alice.send("大家好!")            # Bob/Charlie 都收到
bob.send("你好 Alice!", "Alice")  # 只有 Alice 收到
```

### 为什么需要它

N 个对象两两交互需要 N*(N-1)/2 个连接，中介者将其简化为 N 个连接，降低复杂度。

### 与观察者的对比

| 对比项 | 中介者模式 | 观察者模式 |
|--------|-----------|-----------|
| 通信方式 | 对象间双向通信 | 一对多单向通知 |
| 中心节点 | 有（中介者） | 无（发布者不感知订阅者） |
| 复杂度 | 管理所有交互 | 只管理订阅关系 |

---

## 9. 备忘录模式（Memento）

### 一句话定义

在不暴露对象内部细节的情况下，保存和恢复对象的先前状态。

### 通俗类比

游戏存档——你在打 Boss 之前存个档，打不过可以读档重来，不需要从头玩。

### 具体示例

```python
class Memento:
    def __init__(self, state):
        self._state = state

    def get_state(self):
        return self._state

class Editor:
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

class Caretaker:
    def __init__(self):
        self._history = []

    def save(self, editor):
        self._history.append(editor.save())

    def undo(self, editor):
        if self._history:
            editor.restore(self._history.pop())

# 使用
editor = Editor()
caretaker = Caretaker()

caretaker.save(editor)
editor.type("第一段文字")
print(editor)  # 第一段文字

caretaker.save(editor)
editor.type(" 第二段文字")
print(editor)  # 第一段文字 第二段文字

caretaker.undo(editor)
print(editor)  # 第一段文字
```

### 为什么需要它

实现撤销/重做功能，同时不破坏封装（备忘录存储的是内部状态快照，外部无法直接修改）。

---

## 10. 访问者模式（Visitor）

### 一句话定义

在不修改元素类的前提下，定义作用于元素的新操作。

### 通俗类比

体检中心——体检项目（操作）每年可能变化，但人体（元素）不变。新增一个体检项目不需要修改"人"这个类。

### 具体示例

```python
from abc import ABC, abstractmethod

class Element(ABC):
    @abstractmethod
    def accept(self, visitor): pass

class Book(Element):
    def __init__(self, price):
        self.price = price

    def accept(self, visitor):
        return visitor.visit_book(self)

class Fruit(Element):
    def __init__(self, price, weight):
        self.price = price
        self.weight = weight

    def accept(self, visitor):
        return visitor.visit_fruit(self)

class Visitor(ABC):
    @abstractmethod
    def visit_book(self, book): pass
    @abstractmethod
    def visit_fruit(self, fruit): pass

class PriceCalculator(Visitor):
    def visit_book(self, book):
        return book.price * 0.8  # 书籍八折

    def visit_fruit(self, fruit):
        return fruit.price * fruit.weight  # 水果按重量算

# 使用
items = [Book(100), Fruit(10, 2)]
calc = PriceCalculator()
total = sum(item.accept(calc) for item in items)
print(f"总价: ¥{total}")  # 总价: ¥100
```

### 为什么需要它

当对象结构稳定，但需要经常添加新操作时，用访问者模式比在每个类中添加方法更优雅。

---

## 11. 解释器模式（Interpreter）

### 一句话定义

给定一种语言，定义其文法表示，并定义一个解释器来解释这种语言中的句子。

### 通俗类比

翻译官——你和外国人各说各的语言，翻译官负责把"一种语言"翻译成"另一种语言"。

### 具体示例

```python
class Expression(ABC):
    @abstractmethod
    def interpret(self): pass

class Number(Expression):
    def __init__(self, value):
        self.value = int(value)

    def interpret(self):
        return self.value

class Add(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def interpret(self):
        return self.left.interpret() + self.right.interpret()

class Multiply(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def interpret(self):
        return self.left.interpret() * self.right.interpret()

# 解析 "3 + 5 * 2"
expr = Add(Number("3"), Multiply(Number("5"), Number("2")))
print(expr.interpret())  # 13
```

### 为什么需要它

适用于简单的 DSL（领域特定语言）、数学表达式解析、SQL 解析、正则表达式等。但复杂语法建议用专业解析器。

---

## 总结

```
行为型模式
├── 策略模式 ——— 封装可互换的算法
├── 观察者模式 ——— 状态变化自动通知
├── 命令模式 ——— 将请求封装为对象
├── 状态模式 ——— 行为随内部状态改变
├── 模板方法 ——— 定义算法骨架，子类填充细节
├── 迭代器模式 ——— 统一集合遍历方式
├── 责任链模式 ——— 请求沿链传递直到处理
├── 中介者模式 ——— 用中心节点协调交互
├── 备忘录模式 ——— 保存和恢复对象状态
├── 访问者模式 ——— 不修改类就添加新操作
└── 解释器模式 ——— 定义语言文法并解释执行
```

> **选择建议**：需要动态切换算法用策略模式；对象间松耦合通知用观察者；需要撤销功能用命令模式或备忘录；复杂条件分支用状态模式；固定流程可变步骤用模板方法；集合遍历用迭代器；审批流用责任链；多对象交互复杂用中介者；频繁添加新操作用访问者；简单 DSL 用解释器。
