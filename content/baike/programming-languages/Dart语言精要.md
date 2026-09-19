---
title: "Dart语言精要"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Dart语言精要

> 📌 **导航**：本文是 **Dart 语言精要** 词条，属 [[Flutter跨平台开发实战]] 子词条。

## 定义

**一句话定义：** Dart 是 Flutter 的官方语言——一门面向对象、单继承但支持 mixin、带空安全与 async/await 的现代语言，用 Future/Stream 处理异步、用扩展与集合方法支撑函数式风格。

**通俗类比：** 像"给写 App 量身定做的 Java+JS 混合体"：静态类型 + 空安全像 Java，异步与集合链式像现代 JS，还专为 UI 热重载与跨端优化。

## 为什么需要它

Flutter 的一切 Widget 都用 Dart 写，语言特性直接决定开发体验：空安全在编译期消灭 NullPointerException，单 Isolate 事件循环让 UI 不被阻塞，mixin 让无多继承的语言也能复用行为。

## 核心机制

- **空安全**：默认非空，`T?` 表可空；`?.` 安全访问、`??` 空合并、`late` 延迟初始化；判空后类型自动提升。
- **异步**：单线程事件循环 + microtask；`Future`（一次性结果）/`Stream`（多值，`async*`+`yield`）；CPU 密集任务用 **Isolate**（`compute()` 封装）避免卡 UI。
- **函数式与扩展**：高阶函数、`map/where/reduce` 链式；`extension` 给已有类型加方法。
- **复用**：单继承 + `mixin`（`with`）叠加能力 + 抽象类/接口。

## 具体示例

空安全三件套与 Future：可空值用 `?.`、`??`，判空后自动提非空：

```dart
String? maybe;
int? n = maybe?.length;      // 安全访问，可能为 null
print(n ?? 0);               // 空合并给默认值
Future<User> fetch() async => User.fromJson(await http.get(url));
```

## 何时用与何时不用

- **用**：写 Flutter；开启空安全、用 `compute` 卸载重计算、用 Stream 表达连续异步数据。
- **不用**：非 Flutter 生态时 Dart 生态较小；纯 CPU 重任务别放主 Isolate。

## 优劣与代价

✅ 空安全提前消灭一类运行期崩溃，语法对 UI/异步友好、上手快。
✅ mixin + 扩展让复用灵活。
⚠️ 异步坑（忘记 await、Future 未处理错误）仍常见；Isolate 通信需序列化。
⚠️ 单语言绑定 Flutter，跨场景生态不及主流语言。

## 与相关概念的区别

- **Future vs Stream**：前者表示"将来一个值"，后者是"一串随时间到达的值"。
- **async/await vs Isolate**：前者让异步代码好写、仍在单线程；后者才是真正并行跑重计算、保护 UI 线程。
- **mixin vs 继承/接口**：mixin 复用实现（可叠加多个），接口只约定契约、继承受单继承限制。

## 常见误区

- Dart 的 `late` 可以随便用，不会出问题。
- 加了 `async` 就不会阻塞 UI，重计算也放心放主线程。
- 可空变量加了 `!` 断言运行时就一定安全。

## 面试速答

> 🎯 Dart：面向对象、单继承+mixin、默认空安全(`?`/`?.`/`??`/`late`+类型提升)；异步靠单线程事件循环的 Future(一次性)/Stream(多值)，CPU 密集用 Isolate(`compute`)保 UI；扩展方法与集合链式支撑函数式风格。是 Flutter 的基石语言。
> 🔍 追问：Future 和 Stream 的区别？重计算为什么不放主线程？
> 🔍 追问：Dart 靠什么复用行为（无多继承）？

## 相关术语

[[Flutter跨平台开发实战]]、[[Flutter Widget体系]]、[[协程]]、[[函数式编程完全指南]]

## 参考资料

建议人工核验：以 dart.dev 语言Tour 与空安全/异步文档为准；未编造文献编号。
