---
title: "Object.defineProperty 与 Vue 响应式"
tags: []
source: "knowledge"
collected: "2026-09-21"
status: "reviewed"
---

# Object.defineProperty 与 Vue 响应式

> 📌 **导航**：本文是 **Object.defineProperty 与 Vue 响应式原理** 词条。相关：[[Vue3核心]]（Proxy 在 Vue 3 的落地）、[[虚拟 DOM 与 Diff 算法]]（更新之后的事）、[[浏览器单线程与多线程模型]]（异步批更新依赖的调度模型）。

## 定义

**一句话定义：** `Object.defineProperty` 是 JS 引擎原生的"属性拦截"能力——把一个属性的读写重定向到你提供的 `get`/`set` 函数上；Vue 2 的响应式就建在它上面：**劫持属性（岗哨）+ Dep 记名册（谁依赖我）+ Watcher 执行更新（通知谁）**。

**通俗类比：** 普通属性像仓库里的标准储物格，取放直接走人；defineProperty 的存取器属性则是一个**带岗哨的特殊储物间**——每次取放都经岗哨登记上报。但岗哨只管自己这一间，仓库大门没人看守，这正是它一切局限的根源。

## 拦截的原理：通路被重定向

属性有两种"身份"（描述符），互斥不可混用：

- **数据描述符**：属性自己持有值（`value` + writable/enumerable/configurable）。
- **存取描述符**：属性不持有值，只存 `get`/`set` 两个函数指针；**真正的值被"外包"到闭包里**。

```javascript
function defineReactive(obj, key, val) {
    let internalValue = val;          // 值存在闭包，不在对象属性区
    Object.defineProperty(obj, key, {
        enumerable: true, configurable: true,
        get() { /* 依赖收集 */ return internalValue; },
        set(newVal) {
            if (newVal === internalValue) return;
            internalValue = newVal;   /* 派发更新 */
        }
    });
}
```

引擎执行 `data.name` 时，内部算法 `[[Get]]` 查描述符 → 发现是存取器 → 调用你的 `get` → 返回值由你决定。`[[Set]]` 同理。**读写通路被路由到框架完全掌控的函数里，连值的存放位置都变了**——这就是"拦截"的本质。

## 静态岗哨的三个局限

1. **感知不到新增/删除属性**：`data.age = 18` 会直接建一个普通储物格，不经过任何岗哨。Vue 2 的 `Vue.set` 本质是"补建一间带岗哨的储物间"。
2. **对数组天然不友好**：为每个索引设岗哨开销巨大，而 `push` 的核心是改 `length`、元素位移——静态劫持完全无法感知。Vue 2 只能绕开它，重写 7 个数组方法。
3. **初始化必须深度遍历**：所有层级全部劫持一遍，哪怕某些属性永远用不到。

## Proxy：给仓库大门派总代理

```javascript
const proxy = new Proxy(target, handler);
```

`Proxy` 不再修饰单个属性，而是创建一个**代理对象**，引擎对它的任何 `[[Get]]`/`[[Set]]`/`[[HasProperty]]`… 都先查 `handler` 里的拦截器（trap），共 **13 种内部方法可拦截**（get/set/has/deleteProperty/ownKeys/apply/construct 等）。三个决定性优势：

- **新增、删除、数组索引与 length 全部触发**（`push(4)` 会依次触发 get('push') → get('length') → set('3') → set('length')）。
- **惰性劫持**：访问到嵌套对象时才包一层，不必初始化时全量递归。
- **代理的是对象整体**而非属性，天然覆盖"还没出现的属性"。

> 💡 代价：Proxy 的粒度是"对象"，属性级的依赖关系（哪个 effect 用了哪个 key）要框架自己维护——这正是 Vue 3 在 `get` trap 里做 track 的原因。

## 改一次通知所有：Dep 与 Watcher（Vue 2）

先划清一条关键边界：**`Dep`、`Watcher` 全是 Vue 自己写的代码，不是 JS 系统 API**。JS 引擎只给"读写时调用你的函数"这一种原语；"谁依赖了这个数据、变了通知谁"是框架业务。

```javascript
class Dep {                        // 每个被劫持属性一本花名册
    subs = [];
    depend() { if (Dep.target) this.subs.push(Dep.target); }
    notify() { this.subs.forEach(sub => sub.update()); }
}
class Watcher {                    // 一个渲染函数/computed 一个
    get() {
        Dep.target = this;         // 把自己挂到全局钩子
        this.getter.call(this.vm); // 执行渲染 → 触发各属性 getter → 被收集
        Dep.target = null;
    }
    update() { queueWatcher(this); }  // 注意：不直接干活
}
```

> 🎯 一条链背下来：**Watcher 求值 → 属性 getter 触发 → `dep.depend()` 记名 → setter 触发 → `dep.notify()` → 各 Watcher update**。

这个模型顺手解释了三个经典行为：模板没用到的数据变了视图不动（getter 没触发、名册为空）；`Vue.set` 必要（新属性没有 Dep）；多次修改只渲染一次（见下节）。

## 异步批更新：为什么改三次只渲染一次

`update()` 不执行更新，而是 `queueWatcher(this)`：入队 + 用 `has[id]` 去重，同一 Watcher 只进队一次；首次入队时用 `Promise.resolve().then(flushSchedulerQueue)` 把"清队列"排进**微任务**。当前同步代码（三次赋值）跑完、调用栈清空，事件循环进入微任务阶段，flush 按 id 排序（父先于子）逐个 `run()`——视图只更新一次，拿到最终值。

> 🔍 **追问：为什么用微任务而不是 setTimeout？** 微任务在当前宏任务结束、UI 渲染前执行，视图在同一帧内更新；宏任务要等下一个周期，可能闪一下旧画面。

## 面试视角

> 🔍 **追问：defineProperty 和 Proxy 怎么选？** 别停在"Proxy 更强大"：说清 Proxy 拦对象级 13 种内部方法、惰性劫持，代价是属性级依赖要框架自建；defineProperty 精细到单属性但静态绑定，新增/删除/数组三盲区。

> 🔍 **追问：响应式是 JS 特性还是框架特性？** 语言只给拦截原语（岗哨），Dep 是电话总机、Watcher 是要执行的任务——全是 Vue 自建。三者缺一，链路不通。这句话能直接区分背题和理解。
