---
title: "Object-defineProperty"
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Object-defineProperty.md"
---

## Object.defineProperty  是怎么实现修改一次通知所有的呢？底层原理是什么？

这个问题问到了响应式系统的神经中枢。`Object.defineProperty` 本身只负责“拦截”，它自己并不知道要通知谁。**“通知所有”这个机制，是我们围绕它构建的一套发布-订阅模式的代码实现的。**

底层原理拆开来看，其实就两步：**收集依赖（知道要通知谁）** 和 **派发更新（挨个通知）**。

### 1. 谁来通知？—— Dep 依赖管理器

我们需要一个“花名册”，来记录所有依赖于某个属性的“订阅者”。每个被劫持的属性，背后都绑定一个独立的 `Dep`（Dependency）实例。

```javascript
class Dep {
    constructor() {
        // 存储所有订阅该属性的“观察者”（Watcher）
        this.subs = [];
    }
    // 添加订阅者
    depend() {
        if (Dep.target) {
            this.subs.push(Dep.target);
        }
    }
    // 通知所有订阅者更新
    notify() {
        this.subs.forEach(sub => sub.update());
    }
}
```

### 2. 谁是被通知的人？—— Watcher 观察者

`Watcher` 是真正要执行更新逻辑的角色。比如一个 `Watcher` 对应一个组件的渲染函数，或者一个 `computed` 属性的计算函数。它会在初次执行时，把自己暴露给 `Dep`。

```javascript
class Watcher {
    constructor(updateFn) {
        this.update = updateFn; // 更新时具体要做什么
        this.get();             // 创建时主动求值一次，触发依赖收集
    }
    get() {
        // 1. 把自己挂到一个全局的“钩子”上
        Dep.target = this;
        // 2. 执行更新函数，这会触发属性的 getter
        this.update();
        // 3. 收集完毕，撤下钩子
        Dep.target = null;
    }
}
```

### 3. 把管道接通

现在我们把 `Dep` 和 `Watcher` 接入 `Object.defineProperty` 的岗哨中：

```javascript
function defineReactive(obj, key, val) {
    // 每个属性都有自己专属的“花名册”
    const dep = new Dep();
    
    Object.defineProperty(obj, key, {
        get() {
            // 如果有 Watcher 正在求值，就把它记到花名册里
            if (Dep.target) {
                dep.depend();
            }
            return val;
        },
        set(newVal) {
            if (newVal === val) return;
            val = newVal;
            // 值变了，按花名册挨个通知
            dep.notify();
        }
    });
}
```

### 完整的流程图

用一句话串起来就是：**Watcher 求值时把自己暴露给全局，属性的 `getter` 发现后将其收集进 `Dep`；`setter` 触发时，让 `Dep` 通知所有收集过的 `Watcher` 执行更新。**

这个机制解释了 Vue 2 响应式的好几个关键行为：

-   **为什么模板里没用到的数据变化，视图不更新？** 因为 `getter` 没被触发过，`Dep` 的花名册是空的。
-   **为什么多次修改同一数据，视图只更新一次？** `Watcher` 的更新不是同步的，而是通过一个异步队列在下一个 tick 统一执行（批处理）。
-   **为什么需要 `Vue.set`？** 新增的属性没有经过 `defineReactive` 改造，它压根没有自己的 `Dep`，自然无从通知。

这个“拦截-收集-通知”的链路，就是 `Object.defineProperty` 实现修改通知的完整底层逻辑。

## 所以这个 dep 是 vue 自己实现的，不是 js 自带的函数啊，我以为是系统级的 api

对，你的这个发现非常关键。**`Dep` 完全是 Vue 自己实现的“数据-视图”中间层，JavaScript 引擎本身不提供任何“谁依赖了这个数据，数据变了就自动通知”的系统级 API。**

其实可以换个角度理解：`Object.defineProperty` 只是提供了一个“岗哨”，`Dep` 是 Vue 给这个岗哨配的“电话总机”。

### 为什么 JS 不提供系统级的依赖通知？

可以想象一下，如果每个属性的赋值操作都自动带一套依赖追踪机制，会产生一些问题：

-   **性能开销不可控**：很多数据操作并不需要视图更新。如果每次赋值都自动扫描一遍所有依赖，反而会造成大量不必要的计算。
-   **通知时机和策略无法统一**：是同步通知还是异步批量通知？用队列还是微任务？这属于框架策略层的决定，系统级的 API 不太适合直接内置。
-   **依赖的定义很模糊**：到底谁算“依赖者”？一个计算属性？一个 `watch` 回调？还是一个 DOM 元素？这种业务概念应该由框架来封装，而不是作为语言原语暴露。

所以，JS 引擎只负责执行最底层、最稳定的能力——**拦截属性存取并执行你给的函数**，其他的全部交给框架自由发挥。这是一种很好的设计平衡。

### 对你之前理解的复盘

你当时会有“Dep 是系统级 API”的感觉，其实很正常，说明 Vue 的封装做得非常自然。`Dep` 在调用时完全隐藏在 `get/set` 岗哨的背后，以至于产生了“这应该是原生能力”的错觉。

这种模块协作关系可以这么总结：
-   `Object.defineProperty`：提供“岗哨”（底层拦截能力，系统级 API）
-   `Dep`：提供“电话总机”（依赖收集与通知，Vue 自建）
-   `Watcher`：提供“要执行的任务”（更新函数，Vue 自建）

这三者缺一个，整个响应式就串联不起来。有了这个认识，应该能帮你更清晰地理解 Vue 的响应式系统了。

## 为什么多次修改同一数据，视图只更新一次？ Watcher 的更新不是同步的，而是通过一个异步队列在下一个 tick 统一执行（批处理）。这里插一个题外话，我以前学习的时候，老师说 js 是单线程，一次只能做一件事情，之所以感觉 js 在同一时间做了很多事情，是因为 js 执行的频率很快。那这个单线程和异步感觉有点冲突啊？我理解的有问题吗？

你的理解没有问题，你老师说的也完全正确。这两个概念放在一起感觉冲突，恰恰说明你已经触碰到了 JavaScript 最核心的运行机制。

**单线程和异步，不仅不冲突，异步反而是单线程的“生存之道”。**

我们用一个生活场景来类比，就能把这一切理清。

### 烤肉店老板的哲学

想象你是一家烤肉店的**唯一老板兼厨师（单线程）**。你一次只能做一件事。

-   **同步任务**：客人点了一份现成的凉菜。你必须立刻停下手头的事，拌好给他，然后再回去烤肉。这期间，其他客人和服务员都在干等着。（**阻塞**）
-   **异步任务**：客人点了一份需要慢烤 20 分钟的羊排。如果你一直站在烤炉前死等这 20 分钟，整个店就瘫痪了。
    -   你的正确做法是：把羊排放进烤炉，定好计时器（**交给浏览器/Node.js 的 Web API 去处理**），然后立刻大喊一声“下一位！”，继续处理其他客人的点单、结账。（**非阻塞**）
    -   20 分钟后，计时器响了，服务员把烤好的羊排放到你的取餐台上。但你正在给一位客人找零，你必须等手头这件事**完全结束**后，才能去处理取餐台上的羊排，端给客人。

在这个故事里：

-   **你**，就是 **JavaScript 引擎的单线程**（调用栈）。
-   **烤炉和计时器**，是**浏览器提供的 Web APIs**（如 `setTimeout`、AJAX）。
-   **计时器响后，羊排被放到取餐台**，这个动作是**异步任务完成，回调函数被推进任务队列**。
-   **你每次手头的事彻底做完，去取餐台上看一眼**，这个机制就是**事件循环**。

### 落实到代码层面

```javascript
console.log('1. 点凉菜（同步）');

setTimeout(() => {
    console.log('3. 羊排烤好了，上菜（异步回调）');
}, 0); // 即使定时为0

console.log('2. 继续点单（同步）');
```

这段代码的输出顺序永远是：
`1. 点凉菜（同步）` -> `2. 继续点单（同步）` -> `3. 羊排烤好了，上菜（异步回调）`

**执行过程解析：**

1.  **调用栈** 执行 `console.log('1...')`，立刻完成。
2.  遇到 `setTimeout`。JS 引擎说：“这活儿不归我干，`定时器` 老哥，你来处理。” 然后它就**立刻去执行下一行代码了**。这就是单线程的“非阻塞异步”。
3.  **调用栈** 执行 `console.log('2...')`，立刻完成。
4.  此时，调用栈空了。**事件循环**说：“我来看看**任务队列**里有啥。” 它发现 `setTimeout` 的回调已经在那里等着了。
5.  事件循环把这个回调**推入调用栈**执行。于是，`console.log('3...')` 最终得以执行。

### 回看 Watcher 的批处理

现在，这个机制就能完美解释“多次修改，一次更新”了：

1.  你连续改变了三次数据 `data.name`。
2.  每次改变，都会触发 `setter`，进而调用 `dep.notify()`，通知对应的 `Watcher`。
3.  **关键点来了**：`Watcher` 的更新函数，并不是直接同步执行的。它内部的逻辑是：先把“我这个 Watcher 需要更新”这个消息，放进一个**异步更新的队列**里，然后就不再管了。
4.  即使同一个 `Watcher` 被通知了三次，它也只会往队列里放三次“请更新我”的请求。但 Vue 内部做了去重处理，`Watcher` 在队列里是唯一的，**结果就是，这个更新函数只会被推入任务队列一次。**
5.  当前所有同步代码（包括这三次数据修改）都运行完毕，**调用栈清空**。
6.  **事件循环**在下一个 tick 把这个唯一的更新回调推入调用栈执行。此时，视图才发生改变，当然也只改一次。

所以，**单线程是“一次只能做一件事”的根本约束，而异步是“不让等待的琐事耽误正事”的高效调度策略**。事件循环就是这个调度策略的总指挥。

你没有理解错，只是这个机制的巧妙之处，需要一点时间来回味。现在，单线程和异步的关系清晰些了吗？


## 那就引申出几个问题
1. 那么 setTimeout 是哪个线程或者进程执行的？不是 js 主线程吗？哦，你稍微讲一下进程和线程的区别，我有点不太懂这块儿。
2. 类似 setTimeout 这样的还有哪些？
3. 这个和我了解的宏任务微任务有什么关系吗？
4. setTimeout 的执行顺序我了解了，那么 set interval 这个执行的顺序是啥呢？比如说一个倒计时的功能，这个事一直在重新渲染的，感觉这个也没有在 js 主线程执行的时候阻塞啊。
5. 既然 js 是单线程的开发语言，那多线程开发的有哪些呢？c#是吗？如果是的话，多线程开发执行的一些经典场景是什么？

这几个问题问得太好了，它们像一串钥匙，能帮你彻底打开浏览器运行机制的大门。我们一个一个来。

### 1. 定时器是谁在跑？以及进程与线程

**`setTimeout` 的计时，确实不是 JS 主线程干的。** 它是由**浏览器内核的其他线程**负责的。

为了解释清楚，需要先理清进程和线程：

-   **进程**：可以理解成一个正在运行的程序，它拥有自己独立的内存空间。比如你打开的浏览器，就是一个或多个进程。
-   **线程**：是进程里的“工人”，负责执行具体任务。同一进程里的多个线程**共享**该进程的内存。

**单线程的 JS，只是浏览器这个庞大进程里的一条线程。** 浏览器内还有其他线程，比如专门负责计时的**定时器线程**、负责网络请求的**网络线程**。JS 主线程只需把 `setTimeout` 的计时任务“外包”给它们，自己就能继续往下执行代码了。

### 2. 还有哪些“外包”的任务？

除了 `setTimeout` 和 `setInterval`，常见的会外包给其他线程的异步操作还有：

-   **AJAX (网络请求)**：由网络线程处理，响应回来后，回调被放入任务队列。
-   **事件监听**：比如 `addEventListener('click', ...)`。点击发生时，浏览器的事件处理线程会把回调放入队列。
-   **部分 HTML5 API**：如 `Blob`、`FileReader` 等读写操作。

### 3. 它们和宏任务、微任务的关系

它们就是任务队列的两大分类：

-   **宏任务 (Macro Task)**：我们刚讨论的这些，**整体代码块、`setTimeout`、`setInterval`、I/O、UI 渲染**都属于宏任务。每次事件循环只会从宏任务队列中取出一个来执行。
-   **微任务 (Micro Task)**：**`Promise.then`、`await` 后面的代码、`MutationObserver`** 等。它会在当前宏任务执行完毕后、UI 渲染前被**完全清空**。

这解释了经典问题：为什么 `Promise` 的回调比 `setTimeout` 先执行？因为 `Promise` 是微任务，它等当前宏任务一结束就立刻执行了，而 `setTimeout` 必须等下一个宏任务周期。

### 4. setInterval 的执行与倒计时不阻塞的秘密

**`setInterval` 与 `setTimeout` 类似，不会阻塞主线程。** 它只是每隔一段固定时间，尝试把它的回调函数塞进宏任务队列。

至于倒计时，它一直在“重绘”，但并不会阻塞，这得益于现代浏览器的**渲染管线**和 `requestAnimationFrame` API。

一个简单的倒计时结构可能是这样的：

```javascript
// 每一帧画面到来前，检查是否需要更新数字
function step() {
    let now = Date.now();
    if (now >= targetTime) {
        // 更新时间显示
    }
    // 注册下一次回调
    requestAnimationFrame(step);
}
```

**关键点在于：JS 只修改 DOM 或数据，浏览器会在自己的渲染线程中，在合适的时机（通常是每秒 60 帧）统一进行重绘。** 所以 JS 只是轻量地修改了数值，并没有去执行繁重的绘制工作，自然不会阻塞。

### 5. 多线程的语言与经典场景

没错，**C#、Java、C++、Go** 等都是天生支持多线程开发的。它们的程序可以主动创建多个线程，让它们同时执行，共享进程内存。

**经典场景：**

-   **图形用户界面 (GUI)**：主线程负责界面响应，后台线程处理复杂计算或网络请求，防止“假死”。这有点像我们刚讨论的浏览器架构，只是在这里是多条原生线程。
-   **Web 服务器**：为每个请求分配一个线程，同时处理成百上千的客户端连接。
-   **科学计算与数据分析**：将海量数据分块，交给多个 CPU 核心并行处理，例如矩阵乘法，能显著缩短计算时间。

多线程虽然强力，但也带来了**竞态条件**等复杂问题。而 JavaScript 通过事件循环的单线程模型，简化了编程心智负担，同时借助浏览器多线程和异步能力，也解决了高并发和 UI 流畅度的问题。这两种思路，没有绝对好坏，只是在解决不同场景的问题。

关于这些点，还有哪块希望我再展开讲讲吗？

## 我可不可以这么理解，js 虽然是单线程，但是浏览器可以执行多线程任务，那么就可以手动通过调用 ajax 网络请求、setTimeout 等操作来人为的创造出一个多线程的环境？那这个和 c#等多线程语言感觉还是看不出太大的区别啊？难道是因为c#可以更精细的控制多线程都相关操作吗？

你的理解非常敏锐，基本方向完全正确，只是差最后这一层“窗户纸”了。

你感觉它们好像没啥区别，是因为你把“并发”和“并行”这两个概念弄混了。把这层捅破，区别立现。

### 1. 核心区别：主厨 vs 行政总厨

**JavaScript 的模式（主厨）**
你（JS主线程）是店里唯一会做菜的**主厨**。你觉得忙不过来，于是雇了助手（浏览器线程）帮你**准备食材**（网络请求）、**看火计时**（定时器）。
但最终，所有配好的菜，都必须由**你一个人**来完成最后的烹饪和摆盘。你可以同时张罗 10 桌菜，但你的手在同一瞬间永远只在处理一道菜。这叫**并发**。

**C# 的模式（行政总厨）**
你不做菜了，你成了**行政总厨**。你手下有多个主厨，他们共享同一个厨房。
你可以直接命令：“你，去负责 A 桌的牛排；你，去负责 B 桌的鱼，**现在立刻同时开火**。”
在有多核 CPU 的厨房里，两把火是真的在同一秒一起烧。这叫**并行**。

### 2. 你创造的是“异步环境”，而非“多线程环境”

你用 `setTimeout` 或 Ajax，本质上是**把任务外包出去**，而不是**克隆出第二个你**。

**在 JS 中，你的代码执行永远只有一个调用栈。**

-   你用 Ajax，是让浏览器网络线程替你等数据。数据到了，扔到队列，但你（主线程）还是要等手头事忙完，才能去处理。
-   你用 `setTimeout`，是让定时器线程替你计时。时间到了，扔到队列，你依然要等。

**在 C# 中，你可以有多个调用栈。**
你可以直接 `new Thread(() => { ... })`。这个花括号里的代码，是有一个**独立的执行流**在和你的主线程代码**同步推进**。它们可以同时做两个不同的复杂计算。

### 3. 为什么你觉得区别不大？因为浏览器隐藏了细节

在 Web 开发中，你感觉差别不大，是因为浏览器帮你做了两件大事：

1.  **渲染管道的分离**：JS 改 DOM，浏览器在自己的合成器线程里做动画。你只负责下命令，它负责并行执行。
2.  **高性能 API 的包装**：`fetch` 请求背后，浏览器可能动用了真正的多线程去解析数据。你只拿到了最终结果。

这让你产生了“好像也在同时做事”的错觉。

### 4. C# 到底能“精细控制”什么？—— 真正的分水岭

这才是问题的关键。C# 能做的这些事，JS 在主线程上**绝对做不到**：

**① 纯粹的计算并行**
如果你在 JS 里写了一个从 1 加到 100 亿的死循环，你的整个网页就直接卡死了，按钮点不了，动画停住。因为唯一的厨子被困住了。
在 C# 里，你可以把这个计算丢给一个新线程。你的主线程（UI界面）依然顺滑，按钮照样点。这叫**利用多核 CPU 做并行计算**。

**② 控制线程的“生杀大权”**
C# 可以精细控制：

-   `thread.Start()`：手动启动一个线程。
-   `thread.Suspend()` / `thread.Abort()`：强制暂停或终止另一个线程。
-   `thread.Priority = High`：告诉系统“这个工人的活更紧急”。

JS 的 `setTimeout` 一旦丢出去，你就对它失去控制权了，只能等它自己回来。

**③ 处理共享资源的“锁”**
这是多线程编程最经典也最头疼的部分。因为是真正的并行，两个厨师可能同时去抢同一瓶酱油。
C# 里必须使用 `lock` 关键字，来确保同一时刻只有一个人能拿到酱油。

```csharp
// C# 经典场景
lock(someLockObject) {
    // 这段代码同一时间只允许一个线程进入
    // 防止账户余额被改乱
    balance -= money;
}
```

**JS 完全不需要 `lock`**。因为你的所有代码都在一个线程上排队执行，根本不存在两个操作同时修改一个变量的可能性。

**经典场景区别总结：**
你 JS 做图片压缩，搞不好会卡住界面，因为只能靠唯一的厨师拼命干。C# 做图片压缩，会把任务丢给后台线程，界面丝滑不说，还能同时开四个线程压缩四张图。

所以，**你在 JS 里努力调度任务，本质上是在玩“时间分片”的艺术（并发）。而 C# 等语言，是在玩“空间分核”的技术（并行）。**

这个解释有没有让你对“单线程”和“多线程”的底层区别更清晰一些？


## 了解了，有了一些浅薄的认知，非常感谢🙏难怪听说 chrome 浏览器源码有几十亿行代码，这其中的复杂程度可想而知

你这么说，说明真的领会到精髓了。

没错，你听到的这个“几十亿行”虽然可能是个比喻，但 **Chromium（Chrome 的开源版本）的代码量确实是一个天文数字**。

你可以这么想：我们刚才为了讲清楚一个 `setTimeout`，就牵扯出了：调用栈、浏览器线程、任务队列、事件循环、渲染管道。而 `setTimeout` 只是浏览器提供的数百个 API 中的一个小角色。

把这些庞大的功能全部实现出来，它的复杂度可以这么理解：

-   **它本身就是一个操作系统**：Chromium 需要管理进程（每个标签页一个进程）、管理线程（网络、渲染、GPU、插件）、处理进程间通信（IPC）、管理内存和沙箱安全。光是把这些做稳，代码量就已经是操作系统的级别了。
-   **它翻译并执行了整个现代 Web**：JS 引擎（V8）要瞬间把你的代码编译成机器码并极速优化。渲染引擎（Blink）要把 HTML、CSS 解析成一棵复杂的树，再用 GPU 画成像素。每一个 CSS 属性的组合，背后都是图形学的巨大工程。
-   **它比任何软件都更开放和暴露**：一个操作系统可以垄断 API，说不支持某个硬件就不支持。但浏览器不行，全球开发者写了无数的网页，浏览器必须完美兼容历史上所有的标准和非标准用法。这里的“兼容性”代码，可能是最庞大、最痛苦的部分。

把上面这些加在一起，你得到的不是一个大项目，而是一个**支撑起整个互联网应用层的基石平台**。

你从 `Object.defineProperty` 这样一个细微的点开始追问，一路剥开了响应式系统、事件循环，最后触碰到浏览器架构的冰山一角。这种追根溯源的好奇心很难得。这些基础越往后学，越会成为你理解更高层抽象的宝贵基石。


## ok，我们回到之前我们的对话的开头，我问你 watcher 的更新不是同步而是异步的相关问题，那么 vue 中的 watcher 是如何实现的呢？能看一下简单的源码示例吗？


好的，我们回到正题。你已经理解了“异步更新”的原理，现在我们来把它落实到源码层面，看看 Vue 的 `Watcher` 到底是怎么写的。

下面是一个**极大简化**但保留了核心骨架的实现。

### 1. 调度中心：异步更新队列

这是 Vue 异步更新的心脏。注意它如何利用“单线程”和“微任务”来实现批处理。

```javascript
// 1. 存放所有等待更新的 Watcher
const queue = [];
// 2. 去重标志。避免同一个 Watcher 被重复放进队列
const has = {};
// 3. 标记当前是否已经把“清空队列”的任务安排好了
let waiting = false;

function queueWatcher(watcher) {
    // 去重：如果这个 Watcher 已经在队列里了，就忽略
    if (has[watcher.id]) return;
    has[watcher.id] = true;
    queue.push(watcher);

    if (!waiting) {
        waiting = true;
        // 关键：把 flushSchedulerQueue 这个清空队列的函数，
        // 安排到下一个微任务执行。
        // 这样在当前同步代码块中的所有修改，都会被收集到 queue 里
        // 然后在下一次事件循环的微任务阶段一次性执行。
        Promise.resolve().then(flushSchedulerQueue);
    }
}
```

### 2. 清空队列：一次性执行所有更新

这个函数会在“下一个 tick”的微任务阶段被调用。

```javascript
function flushSchedulerQueue() {
    // 1. 排序，确保 Watcher 按照正确的顺序更新（父组件先于子组件）
    queue.sort((a, b) => a.id - b.id);

    // 2. 依次执行每个 Watcher 的更新
    for (let i = 0; i < queue.length; i++) {
        const watcher = queue[i];
        // 调用 Watcher 的 run 方法（接下来会讲）
        watcher.run();
    }

    // 3. 重置状态，准备下一轮
    queue.length = 0;
    has = {};
    waiting = false;
}
```

### 3. Watcher 本身：把自己交给队列

现在来看 `Watcher` 的核心结构。注意 `update` 方法，它不直接干活，而是把自己交给调度队列。

```javascript
let uid = 0;

class Watcher {
    constructor(vm, expOrFn, cb) {
        this.id = uid++;          // 唯一ID，用于去重
        this.vm = vm;             // Vue 实例
        this.cb = cb;             // 回调函数
        this.getter = expOrFn;    // 要触发的 getter，可能是渲染函数或计算属性函数

        // 初始化时求值一次，触发依赖收集
        this.value = this.get();
    }

    get() {
        // 把自己挂到全局钩子上，让 Dep 能收集到
        Dep.target = this;
        let value = this.getter.call(this.vm); // 执行渲染函数，触发 getter
        Dep.target = null;
        return value;
    }

    // 当依赖的数据变化时，Dep 会调用这个方法
    update() {
        // 不直接执行 run()，而是把自己推进异步队列！
        queueWatcher(this);
    }

    // 真正执行更新逻辑的方法
    run() {
        const value = this.get(); // 重新求值
        this.cb.call(this.vm, value, this.value); // 执行回调
        this.value = value;
    }
}
```

### 完整流程串联

假设我们修改了三次数据：

```javascript
// 假设有一个 Watcher 实例 w，它的 getter 会读取 data.name
data.name = 'Alice';    // 触发 setter -> Dep.notify() -> w.update()
                        // -> queueWatcher(w) -> w 进入队列，安排微任务

data.name = 'Bob';      // 再次触发 w.update()
                        // -> queueWatcher(w) -> 发现 w.id 已在队列，忽略！

data.name = 'Charlie';  // 再次忽略

// 同步代码全部执行完毕，调用栈清空。
// 事件循环进入微任务阶段，执行 flushSchedulerQueue。
// w.run() 只执行一次。视图得到最终值 'Charlie'。
```

这就是 Vue 异步更新的完整骨架。它没有魔法，完全是靠：
1.  **队列 `queue`** 做缓冲区。
2.  **`has` 对象**做去重。
3.  **`Promise.resolve().then()`** 做异步调度。
4.  **`Watcher` 的 `update` 方法**主动推入队列。

整个机制非常巧妙，而且代码量其实很少。希望这个源码层面的解析，能帮你把之前的所有理论点都串联起来。


## 整理以上内容

以下是根据我们的对话整理而成的 Markdown 文件，你可以直接复制并保存。

```markdown
# JavaScript 响应式原理与浏览器运行机制深度对话

## 一、Object.defineProperty 的原理

### 1. 核心作用
`Object.defineProperty` 是 JavaScript 实现属性拦截的核心方法。它可以在对象上定义新属性或修改现有属性，并精确控制属性的行为（描述符）。

### 2. 属性描述符
- **数据描述符**：属性本身持有值（`value`、`writable`、`enumerable`、`configurable`）。
- **存取描述符**：属性不直接持有值，而是由 `get` 和 `set` 函数代理。不能同时设置 `value` 和 `get`。

### 3. 拦截原理：重定向通路
当定义 `get`/`set` 后，属性的读取和赋值操作会被引擎重定向到我们定义的函数上。

```javascript
function defineReactive(obj, key, val) {
    let internalValue = val; // 值存储于闭包，而非对象本身
    Object.defineProperty(obj, key, {
        enumerable: true,
        configurable: true,
        get() {
            console.log(`获取 ${key}: ${internalValue}`);
            return internalValue;
        },
        set(newVal) {
            console.log(`设置 ${key} = ${newVal}`);
            if (newVal === internalValue) return;
            internalValue = newVal;
            updateView(); // 触发更新
        }
    });
}
```

**本质**：引擎内部属性访问机制被 `get/set` 接管，原来直接读写内存的通路被重定向到函数上，实现了完全拦截。

### 4. 重要局限（与 Proxy 对比的伏笔）
- 无法检测属性新增/删除（Vue 2 需用 `Vue.set/delete`）。
- 数组监听困难（性能差，需重写方法）。
- 必须深度递归遍历所有属性。

---

## 二、Dep 与 Watcher：如何实现“修改一次，通知所有”

### 1. 总体机制
`Object.defineProperty` 只负责拦截，真正的依赖收集与派发更新由 Vue 自己实现的 **Dep**（依赖管理器）和 **Watcher**（观察者）完成，是一套发布-订阅模式。

### 2. 三大角色
#### Dep（电话总机）
```javascript
class Dep {
    constructor() {
        this.subs = []; // 存储所有订阅者（Watcher）
    }
    depend() {
        if (Dep.target) {
            this.subs.push(Dep.target);
        }
    }
    notify() {
        this.subs.forEach(sub => sub.update());
    }
}
```

#### Watcher（观察者）
```javascript
class Watcher {
    constructor(updateFn) {
        this.update = updateFn;
        this.get(); // 初始化时主动求值，触发依赖收集
    }
    get() {
        Dep.target = this;   // 将自己暴露给全局钩子
        this.update();       // 执行更新函数，触发 getter
        Dep.target = null;   // 收集完毕，清空钩子
    }
}
```

#### 响应式属性定义
```javascript
function defineReactive(obj, key, val) {
    const dep = new Dep();
    Object.defineProperty(obj, key, {
        get() {
            if (Dep.target) dep.depend(); // 收集依赖
            return val;
        },
        set(newVal) {
            if (newVal === val) return;
            val = newVal;
            dep.notify(); // 派发更新
        }
    });
}
```

### 3. 关键解释
- **为什么没在模板使用的数据变化不更新？** 因为 `getter` 从未被触发，Dep 的订阅列表为空。
- **为什么多次修改只更新一次？** Watcher 的更新是异步批处理的（见下文）。

---

## 三、Proxy：代理整个对象的“总代理”

### 1. 基本语法
```javascript
const proxy = new Proxy(target, handler);
```

### 2. 原理
Proxy 拦截的是对象层面的**内部方法**（共 13 种），而不是具体属性。任何针对对象的操作（读取、赋值、删除、遍历等）都会被拦截。

### 3. 解决 defineProperty 的缺陷
```javascript
const handler = {
    get(target, key) { return target[key]; },
    set(target, key, value) {
        target[key] = value;
        updateView();
        return true;
    },
    deleteProperty(target, key) {
        delete target[key];
        updateView();
        return true;
    }
};
const proxyData = new Proxy(data, handler);
proxyData.age = 18;      // 新增属性也触发 set
delete proxyData.age;    // 删除属性也触发 deleteProperty
```

- 数组操作能完美捕获。
- 惰性劫持，只有访问到的嵌套对象才被包装为响应式。

---

## 四、单线程、异步与事件循环

### 1. 单线程与异步不冲突
- **单线程**：JavaScript 引擎一次只能执行一段代码（只有一个调用栈）。
- **异步**：遇到耗时任务（如定时器、网络请求）时，将其“外包”给浏览器其他线程，主线程继续执行。任务完成后，回调被推入任务队列，等待主线程空闲时执行。
- **事件循环**：不断检查调用栈是否为空，若为空则将任务队列中的回调推入执行。

### 2. setTimeout 的执行者
`setTimeout` 的计时由**浏览器定时器线程**负责，计时结束将回调放入宏任务队列，并非 JS 主线程在计时。

### 3. 进程与线程
- **进程**：运行中的程序，拥有独立内存空间。
- **线程**：进程内的执行单元，共享进程内存。
- 浏览器是多进程多线程的，JS 引擎只是其中一条线程。

### 4. 宏任务与微任务
- **宏任务**：整体脚本、`setTimeout`、`setInterval`、I/O、UI 渲染等。
- **微任务**：`Promise.then`、`await` 后续代码、`MutationObserver`。
- 执行顺序：当前宏任务执行完毕 → 清空所有微任务 → UI 渲染（如有）→ 取下一个宏任务。

### 5. setInterval 与倒计时不阻塞
`setInterval` 同样不会阻塞主线程，它只是定时将回调加入宏任务队列。实现流畅倒计时通常使用 `requestAnimationFrame`，JS 只负责轻量更新数据，浏览器在渲染线程中重绘。

---

## 五、JS 的并发 vs C# 的并行

### 1. 核心区别
- **并发（JS）**：单线程通过任务调度，交替执行多个任务，同一时刻只处理一件事。
- **并行（C#/Java 等）**：真正同时执行多个代码片段（利用多核 CPU）。

### 2. JS 的异步环境并非多线程
`setTimeout`、Ajax 等只是将任务外包给浏览器其他线程，最终代码执行仍由 JS 主线程串行完成。没有两个 JS 函数会同时运行。

### 3. C# 多线程的精细控制
- 可手动创建、启动、暂停、终止线程。
- 可设置线程优先级。
- 需要处理共享资源竞争，使用 `lock` 等同步机制。
- 典型场景：UI 主线程与后台计算分离、Web 服务器并发请求处理、科学计算并行加速。

### 4. 为什么你感觉区别不大？
浏览器已将大量复杂工作（如渲染、网络）用多线程实现并封装成 API，开发者只需调用异步接口，无需手动管理线程。

---

## 六、浏览器架构的复杂度
Chrome（Chromium）源码量极其庞大，因为它不仅包含：
- **多进程架构**（每个标签页一个进程）。
- **V8 引擎**（JS 即时编译与优化）。
- **Blink 渲染引擎**（HTML/CSS 解析、布局、绘制）。
- **海量 Web API** 及历史兼容性处理。
这些加在一起使它成为一个支撑整个互联网应用层的基石平台。

---

## 七、Vue 中 Watcher 异步更新的源码骨架

### 1. 调度队列（异步更新核心）
```javascript
const queue = [];
const has = {};
let waiting = false;

function queueWatcher(watcher) {
    if (has[watcher.id]) return;
    has[watcher.id] = true;
    queue.push(watcher);
    if (!waiting) {
        waiting = true;
        Promise.resolve().then(flushSchedulerQueue); // 下一个微任务执行
    }
}
```

### 2. 清空队列
```javascript
function flushSchedulerQueue() {
    queue.sort((a, b) => a.id - b.id);
    for (let i = 0; i < queue.length; i++) {
        queue[i].run();
    }
    queue.length = 0;
    has = {};
    waiting = false;
}
```

### 3. Watcher 类
```javascript
let uid = 0;
class Watcher {
    constructor(vm, expOrFn, cb) {
        this.id = uid++;
        this.vm = vm;
        this.cb = cb;
        this.getter = expOrFn;
        this.value = this.get();
    }
    get() {
        Dep.target = this;
        let value = this.getter.call(this.vm);
        Dep.target = null;
        return value;
    }
    update() {
        queueWatcher(this); // 不进直接执行，而是推入异步队列
    }
    run() {
        const value = this.get();
        this.cb.call(this.vm, value, this.value);
        this.value = value;
    }
}
```

### 4. 执行流程
1. 多次修改同一数据，每次都调用 `watcher.update()`。
2. `update()` 调用 `queueWatcher`，但同一个 watcher 因去重只被加入队列一次。
3. 微任务安排在下一个 tick 执行 `flushSchedulerQueue`。
4. 队列中该 watcher 的 `run()` 只执行一次，视图得到最终值。

---

*对话时间：2026-05-25 ～ 2026-05-26*
```