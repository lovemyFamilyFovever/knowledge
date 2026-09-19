---
title: "MVC 与 MVVM"
tags: []
source: "baike"
source_path: "开发术语 / 设计模式"
collected: "2026-09-05"
status: "imported"
---

# MVC 与 MVVM

> 📌 **导航**：本文是 **MVC 与 MVVM** 词条，属 [[结构型模式（Structural Patterns）]] 子词条（二者是界面**架构模式**，非 GoF 设计模式）。

## 定义

**一句话定义：** MVC 与 MVVM 是界面分层架构模式：把应用拆成模型（数据与业务）、视图（展示）以及中间协调层（Controller / ViewModel），使三者职责分离、可独立演化与测试。

**通俗类比：** 餐厅分工——后厨（Model）做菜备料，服务员（Controller）接单并协调后厨与餐桌，菜单与摆盘（View）负责把成品呈现给顾客。

## 为什么需要它

把界面渲染、用户输入、业务数据揉成一团，代码既难维护又难测试，也无法让同一份数据支撑多种界面。MVC 家族通过分层把三类关注点解耦：业务逻辑不依赖具体 UI、UI 可独立替换、中间层可单独做单元测试，还支持多人并行开发。

## 核心机制

- **MVC**：Model（数据+业务）、View（展示）、Controller（接收输入、协调 M 与 V）。经典数据流里，Model 状态变化通过**观察者**机制通知 View，View 再从 Model 读取渲染。由 Trygve Reenskaug 于 1979 年在施乐 PARC 提出，最早用于 Smalltalk。
- **MVVM**：在 View 与 Model 间引入 ViewModel——它持有视图状态与命令、暴露**可观察**数据，靠**数据绑定**让 View 与 ViewModel 自动双向同步；关键是 **ViewModel 不直接引用 View**。术语由微软 John Gossman 于 2005 年介绍 WPF 时提出。
- GoF 书中把经典 MVC 视为**观察者 + 策略 + 组合**三种设计模式的复合运用，而非一种独立设计模式。

## 具体示例

一个极简 MVC：Controller 接收写操作、更新 Model、再让 View 渲染，三者互不越界：

```python
class UserModel:                       # Model
    def __init__(self): self.users = []
    def add(self, name): self.users.append(name)
class UserView:                        # View
    def show(self, users): [print(f"用户: {u}") for u in users]
class UserController:                  # Controller
    def __init__(self): self.m, self.v = UserModel(), UserView()
    def add(self, name): self.m.add(name); self.v.show(self.m.users)
```

Vue 单文件组件即典型 MVVM：`template` 是 View、`data`/`computed` 构成 ViewModel、`v-model`/`{{ }}` 是数据绑定，真正的 Model 在背后的接口/仓库层。

## 何时用与何时不用

- **用**：Web/移动/桌面应用 UI 分层；需要同一份 Model 支撑多视图（Web、移动端）；想让 UI 与业务独立演进、独立测试。
- **不用**：无 UI 的脚本与纯逻辑；很小、几乎无状态的页面硬套 ViewModel 反而繁重。

## 优劣与代价

✅ 职责分离、支持多视图共享模型、便于并行开发与单元测试。
✅ MVVM 数据驱动、View 逻辑极薄、天然支持响应式更新。
⚠️ 分层增加复杂度；View 与 Model 耦合不当（如 View 直接改 Model）会破坏分层，"胖控制器"是常见反模式。
⚠️ MVVM 的绑定与响应式使数据流向不易追踪、调试更复杂。

## 与相关概念的区别

| 对比项 | MVC | MVP | MVVM |
|---|---|---|---|
| 中间层 | Controller | Presenter | ViewModel |
| 中间层与 View | View 可读 Model | Presenter **持有 View 引用**、主动更新 | 靠**数据绑定**同步（ViewModel 不持有 View） |
| 数据流向 | 单向为主 | Presenter 驱动 | 双向绑定 |
| 典型场景 | 传统 Web / 服务端渲染 | 早期 Android / WinForms | Vue / Angular / WPF |

## 常见误区

- MVC / MVVM 属于 GoF 的 23 种结构型设计模式。
- Controller 应尽量把业务逻辑都塞进去，写成"胖控制器"。
- MVVM 里 ViewModel 直接持有并操作 View 的引用。

## 面试速答

> 🎯 MVC 与 MVVM 是界面分层架构模式：MVC 用 Controller 协调 Model/View（Reenskaug 1979），MVVM 引入不引用 View 的 ViewModel、靠数据绑定双向同步（Gossman 2005）。二者把 UI 与业务分离、便于测试与多视图；属架构模式，非 GoF 设计模式。
> 🔍 追问：MVC 和 MVVM 的核心区别是什么？
> 🔍 追问：为什么说 MVC 不算 GoF 的 23 种设计模式？

## 相关术语

[[结构型模式（Structural Patterns）]]、[[行为型模式（Behavioral Patterns）]]、[[组合模式]]

## 参考资料

- Trygve Reenskaug，MVC（Smalltalk-80），1979 —— MVC 起源，具体文献版本建议人工核验。
- John Gossman（Microsoft），关于 MVVM 的介绍，2005 —— MVVM 术语来源，建议人工核验。
