---
title: "React Native移动应用开发"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# React Native移动应用开发

> 📌 **导航**：本页是 **React Native 移动应用开发** 枢纽，索引其 4 个子词条；新架构、组件、导航/状态、网络/缓存的机制与代码已拆出，本页只讲"这套技术栈分几层、怎么学怎么选"。

## 定义

**一句话定义：** React Native（RN）是用 React 与 JavaScript 编写 iOS/Android 原生体验 App 的跨端框架；其知识分运行时架构、UI 组件、应用骨架、数据层四层，本枢纽只做分层导航，细节下沉到四篇子词条。

**通俗类比：** 像一套"用同一份 React 图纸，盖两座原生房子（iOS/Android）"的施工体系——图纸（JS 组件）共享，承重与水电（渲染、原生能力）各自落到平台真实控件上。

## 为什么需要它

一套代码覆盖双端、复用 React 心智与前端生态，是 RN 的核心价值。但"跨端"不是白拿的：JS 与原生如何高效通信、布局差异、多屏导航、状态与缓存都要各自选型踩坑。把这四类问题分层的意义在于——它们相对正交，可以独立演进、独立排障，也便于按需单查某一层。Web 侧 React 心智可迁移，差异集中在"原生渲染"与"平台行为"（见 [[React深入]]）。

## 核心机制

四篇子词条各管一层，学习顺序即"先建心智、再写界面、再串多屏、最后接数据"：

| 子词条 | 管哪层 | 解决什么 |
|---|---|---|
| [[React Native 新架构与原生桥接]] | 运行时架构 | JSI 免序列化直调 C++、Fabric 同步渲染、TurboModules 懒加载、新旧架构迁移 |
| [[React Native 组件与布局]] | UI 层 | Flexbox 默认 `column`、SafeAreaView 处理刘海、FlatList 大列表性能参数 |
| [[React Native 导航与状态管理]] | 应用骨架 | React Navigation 嵌套与深链、Zustand/Jotai 轻量状态 |
| [[React Native 网络与数据缓存]] | 数据层 | axios 拦截器鉴权重试、TanStack Query 缓存、MMKV 本地存储 |

本页不重复各层的定义与代码，仅给出这层地图；深入内容见对应子词条。

## 具体示例

从零起一个 RN App 的选型路线：确认 React Native 0.7x+ 直接启用新架构（见 [[React Native 新架构与原生桥接]]）→ 用 Flexbox 排布局、长列表一律 FlatList（见 [[React Native 组件与布局]]）→ 多屏用 React Navigation 的 Stack/Tab、跨屏共享态用 Zustand（见 [[React Native 导航与状态管理]]）→ 请求走带拦截器的 axios、服务端状态交给 TanStack Query、离线缓存落 MMKV（见 [[React Native 网络与数据缓存]]）。

## 何时用与何时不用

- **用**：目标是双端共享大部分 UI/逻辑、团队已有 React/TS 能力、需要 OTA 热更能力时，RN 性价比高。
- **不用**：重图形/重动画、大量平台专属交互、或对包体与极致性能敏感时，评估原生或 Flutter；纯 App、逻辑极少也别为"跨端"背上 JS 引擎。

## 优劣与代价

✅ 一套代码双端、复用 React 生态与热更新、开发效率高，新架构后性能与启动大幅改善。
✅ 分层清晰，UI/导航/数据可独立选型与替换。
⚠️ 依赖桥接与 JS 引擎，极端性能/新平台特性有滞后；三方库质量参差、升级偶有破坏性变更。
⚠️ 调试横跨 JS 与原生两条栈，排查成本高于纯 Web。

## 与相关概念的区别

- **RN vs Flutter**（[[Flutter跨平台开发实战]]）：RN 用 JS+React、渲染映射到原生控件；Flutter 用 Dart+自绘引擎 Skia，视觉一致性更强但包体更大。
- **RN vs 纯 Web React**（[[React深入]]）：组件/Hooks 心智同源，RN 无 DOM、布局是 Flexbox 子集、多了平台与原生能力层。
- **RN vs 原生开发**：牺牲部分性能与平台贴合度换取跨端与迭代速度。

## 常见误区

- React Native 就是"把网页塞进 WebView"，性能必然很差。
- 会写 Web React 就等于会写 RN，布局与平台差异可以忽略。
- 启用了新架构就自动零成本、不需要迁移原生模块。

## 面试速答

> 🎯 RN 用 React+JS 写跨端 App，分四层：新架构（JSI/Fabric/TurboModules）、组件布局（Flexbox/SafeArea/FlatList）、导航状态（React Navigation+Zustand/Jotai）、网络缓存（axios+Query+MMKV）。按层选型单查。
> 🔍 追问：新架构相比旧 Bridge 好在哪？
> 🔍 追问：RN 与 Flutter 如何做技术选型？

## 相关术语

[[React Native 新架构与原生桥接]]、[[React Native 组件与布局]]、[[React Native 导航与状态管理]]、[[React Native 网络与数据缓存]]、[[React深入]]、[[TypeScript深入]]、[[Flutter跨平台开发实战]]

## 参考资料

建议人工核验：本词条内容建议对照 React Native / React Navigation / Zustand / TanStack Query 官方文档做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
