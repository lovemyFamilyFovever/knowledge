---
title: "Functor 与 Monad"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Functor 与 Monad

> 📌 **导航**：本文是 **Functor 与 Monad** 词条，属 [[函数式编程完全指南]] 子词条。

## 定义

**一句话定义：** 函子（Functor）是"可被 map 的容器"，Applicative 再加"能把函数装进容器并 apply"，单子（Monad）则以 `bind/flatMap` 串接"返回包装值的函数"——它们用统一结构承载上下文（失败、缺失、副作用）并链式组合。

**通俗类比：** 容器像"带包装的水果"：Functor 让你隔着包装照样加工水果（map）；Monad 多一个 `flatMap` 能拆箱再接着装箱，把"可能失败/可能为空/带副作用"的连续步骤优雅串起来。

## 为什么需要它

纯函数难以直接组合"带上下文"的计算（可能出错、可能为空、有 I/O）。抽象出 map/flatMap 统一处理这层"包装"，就能把一串可能失败的步骤写成链式流水线，把副作用/错误控制交给结构而非散落判断。

## 核心机制

- **Functor**：实现 `map`，对容器内值施加函数（`Option.map`、`Array.map`）；满足恒等与组合律。
- **Applicative**：`of/pure` 把值升进容器，`ap` 施加"容器里的函数"，可并行组合。
- **Monad**：`of` + `bind(>>=/flatMap)`——`flatMap` 处理"函数本身返回包装值"，避免 `Option<Option<T>>` 嵌套；满足结合/左/右单位律。
- **常见实例**：`Either/Either<L,R>` 承载错误(右成功)、`Option/Maybe` 表达"可能没有"、`IO` 把副作用延迟为值组合。

## 具体示例

用 `Option`/`flatMap` 串"可能为空"的取数链，省掉层层 null 判断：

```javascript
const safe = v => (v == null ? None : Some(v));
Some("42").flatMap(safe).map(n => Number(n) + 1);   // Some(43)，任一环为空即 None
```

## 何时用与何时不用

- **用**：错误用 Either/Result、缺失用 Option/Maybe、副作用隔离用 IO/延迟执行；把连续可能失败的步骤用 flatMap 串起。
- **不用**：无上下文的普通映射用 map 即可、别硬套 Monad；语言/团队无这些抽象时，用等价惯用法（如 Rust 的 `?`、TS 的可选链）更直白。

## 优劣与代价

✅ 统一"上下文"处理、链式组合、把错误/空/副作用变成可组合的值。
✅ 律保证行为可预期、可推导。
⚠️ 抽象门槛高、命名（bind/map/ap）易与语言内建方法冲突。
⚠️ 过度 Monad 化会让命令式读者困惑、调试栈更深。

## 与相关概念的区别

- **map vs flatMap**：map 施加普通函数、可能产生嵌套容器；flatMap 施加"返回容器"的函数并自动展平。
- **Functor vs Applicative vs Monad**：能力递进——只能 map / 能 apply 容器函数 / 能 bind 串接。
- **Monad（函数式）vs 设计模式里的抽象**：与 [[命令模式]] 等无关，是类型结构。

## 常见误区

- flatMap 只是 map 的别名。
- Monad 就是"可 map 的容器"（那只是 Functor）。
- 所有函数式编程都必须手写一整套 Monad。

## 面试速答

> 🎯 能力递进：Functor=能 map 的容器；Applicative=加 of/ap；Monad=of+bind/flatMap 串接"返回容器"的函数并自动展平，把失败(Either)/缺失(Option)/副作用(IO)统一成可组合的值。map 会嵌套、flatMap 展平是关键区别。
> 🔍 追问：map 与 flatMap 的根本区别？
> 🔍 追问：Either/Option/IO 各解决什么？

## 相关术语

[[函数式编程完全指南]]、[[函数式编程基础]]、[[函数式错误处理与不可变数据结构]]、[[Rust 错误处理]]

## 参考资料

建议人工核验：以《Category Theory for Programmers》与各语言 FP 库文档为准；未编造文献编号。
