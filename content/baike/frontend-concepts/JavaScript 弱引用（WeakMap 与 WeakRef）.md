---
title: "JavaScript 弱引用（WeakMap 与 WeakRef）"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# JavaScript 弱引用（WeakMap 与 WeakRef）

> 📌 **导航**：本文是 **JavaScript 弱引用（WeakMap 与 WeakRef）** 词条，属于 frontend-concepts 术语集。相关枢纽：[[JavaScript 基础核心概念]]、[[前端框架核心概念]]。

## 定义

**一句话定义：** 普通变量与 Map/Set 持有强引用会阻止垃圾回收；WeakMap 以对象为键且只弱引用键，WeakRef 只弱引用一个值——两者都"附加数据而不延长生命周期"，被引用的对象该回收就回收。

**通俗类比：** WeakMap 像贴在东西上的便利贴：东西被扔了，便利贴跟着消失，不会因为写了字就让垃圾站拒收这件东西；WeakRef 像隔着窗看隔壁——窗被拆了就只能看到"什么都没有"。

## 为什么需要它

缓存与元数据最常见的泄漏形态是"我给它挂了数据，结果它永远回收不掉"：给 DOM 节点记状态、给实例记私有字段、给对象记一次计算结果，用 Map 就把对象的生命周期无限延长。弱引用把"附加信息"与"存活责任"解耦，回收器不再被自己的缓存挡住。

## 核心机制

- **WeakMap**：键必须是对象（或 symbol 等），`set/get/has/delete` 四个操作；键是弱引用，键对象失去其他强引用后条目自动消失。它不可枚举——没有 `size`、没有 `keys()`、不能迭代，因为条目何时消失取决于 GC 这一不可观察的时机。
- **典型用法**：给外部对象挂私有元数据（DOM 节点记点击数、实例记私有状态），对象被移除即数据一起走，无需手动清理，也不会像 `element._myData = {}` 那样形成环。
- **WeakRef**：`new WeakRef(obj)` 之后靠 `deref()` 取回对象，取回时可能已经是 undefined——所以每次使用都要判空，绝不能假设它还在。
- **FinalizationRegistry**：`register(target, heldValue)` 在 target 被回收后异步回调，用于释放外部资源。它既不保证触发也不保证及时，只能当清理的尽力而为，不能承载正确性。

## 具体示例

```javascript
const meta = new WeakMap();            // 键是对象，弱引用
const btn = document.querySelector("button");
meta.set(btn, { clicks: 0 });
meta.get(btn).clicks++;                // btn 被移除后条目自动消失

const ref = new WeakRef({ big: new Array(1e6) });
const alive = ref.deref();             // 可能 undefined，必须判空
if (alive) console.log(alive.big.length);
```

## 何时用与何时不用

- **用**：为不属于自己的对象（DOM 节点、第三方实例）附加状态；实现私有字段而不暴露；跨调用缓存以对象为键的计算结果且不希望缓存成为泄漏源。
- **不用**：需要遍历、统计或按序导出时（那是 Map 的活）；需要"对象没了就立刻关文件/退订"时别依赖 FinalizationRegistry，改成显式 dispose；也不要为了"内存友好"把短生命周期小对象全换成 WeakRef。

## 优劣与代价

✅ 消除一整类泄漏：缓存与元数据不再延长对象寿命，回收时机交给引擎。
✅ 语义天然适合"外部对象的私有状态"，比命名约定与手工 delete 更可靠。
⚠️ 行为依赖 GC，不可观察也不可复现：WeakRef 与 FinalizationRegistry 的测试与调试都很脆。
⚠️ 不可枚举意味着无法做缓存上限与命中率统计，容量策略要在别处实现。

## 与相关概念的区别

- **vs [[垃圾回收]]**：那条讲回收算法本身（可达性、分代、循环引用），本条是语言给你的一种"别挡回收"的工具；WeakMap 能绕过引用计数的循环引用问题正是那篇的续集。
- **vs [[内存管理]]**：内存管理是地址、栈堆与生命周期的通用模型，本条只管 JS 层的引用强度。
- **vs Map/Set**：Map 的键是强引用且可枚举，适合"我负责这些对象的存在"；WeakMap 适合"我只是顺手记点东西"。

## 常见误区

- 以为 WeakMap 也能像 Map 一样遍历或读 `size`。
- 以为 FinalizationRegistry 的回调会在对象失去引用后及时且必然执行，用它来保证关闭文件。
- 以为 `WeakRef` 取回的引用可以直接用，不需要每次判空。

## 面试速答

> 🎯 WeakMap 键为对象且弱引用、条目随键回收、不可枚举，用来给外部对象挂元数据或私有字段；WeakRef.deref() 可能 undefined；FinalizationRegistry 只是尽力清理，不保证触发时机，别放正确性。

## 相关术语

[[JavaScript 基础核心概念]]、[[垃圾回收]]、[[内存管理]]、[[JavaScript 原型链与继承]]、[[JS执行性能]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇承接原《JavaScript 基础核心概念》WeakMap 与 WeakRef 一节；原稿该节的 WeakRef 代码行存在抓取损伤（`deref()` 调用残缺），此处只按 API 语义散文承载，未据推测复原原代码。
