---
title: "React Native 新架构与原生桥接"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# React Native 新架构与原生桥接

> 📌 **导航**：本文是 **React Native 新架构与原生桥接** 词条，属 [[React Native移动应用开发]] 子词条。React 基础见 [[React深入]]。

## 定义

**一句话定义：** React Native 新架构用 JSI（直接双向调用）替换旧"异步桥"，配合 Fabric（新渲染）与 TurboModules（按需原生模块），降低通信开销与启动成本；原生桥接即通过它们把 JS 与 iOS/Android 原生能力连起来。

**通俗类比：** 旧架构像"两人隔着门缝传纸条"（异步、序列化、排队），新架构是"直接同屋对话"（JSI 同步直调），需要谁时才把谁叫来（TurboModules 懒加载）。

## 为什么需要它

旧 Bridge 把所有 JS↔原生调用/事件都过一条序列化、异步、单通道的桥：高频动画/手势卡顿、启动加载全部模块慢、类型不安全。新架构直接内存级调用 + 按需加载，显著改善性能与启动，并为 React 并发特性（如 Suspense）铺路。

## 核心机制

- **JSI (JavaScript Interface)**：让 JS 引擎与原生持有对方引用、直接同步调用，不经 JSON 序列化桥。
- **Fabric**：新渲染系统，同步布局/C++ 核心，支持并发渲染。
- **TurboModules**：原生模块按需初始化而非启动全量加载。
- **Codegen**：用类型规范生成 JS/原生接口，保证桥两端一致。
- **原生模块**：iOS（ObjC/Swift）、Android（Java/Kotlin）实现并注册；兼容层可新旧共存、逐步迁移。

## 具体示例

新架构下定义 Turbo Module（类型化，Codegen 生成两端胶水）：

```typescript
// NativeGreeting.ts（Spec）
import type { TurboModule } from 'react-native/Libraries/TurboModule/RCTExport';
export interface Spec extends TurboModule {
  greet(name: string): string;   // JS 直接同步调用原生实现
}
```

## 何时用与何时不用

- **用**：性能敏感（动画/大量原生交互）、需要启动裁剪、包原生能力模块时走新架构；已依赖旧库时评估兼容共存或等其迁移。
- **不用**：纯 JS、无重原生交互的小应用，旧/新感知不大，别为迁移引入风险。

## 优劣与代价

✅ 消除桥瓶颈：更快、可同步、启动更省、类型更安全，支持并发渲染。
✅ TurboModules 懒加载、Codegen 减少手写胶水错误。
⚠️ 迁移成本：三方原生库需适配新架构。
⚠️ 新架构栈更复杂，调试跨越 JS/原生两端。

## 与相关概念的区别

- **旧 Bridge vs 新 JSI**：异步序列化、单通道 vs 同步直调。
- **Fabric vs 旧渲染**：同步/C++ 渲染 vs 异步批量 UI 更新。
- **TurboModules vs 旧 NativeModule**：按需初始化 vs 启动即全载。

## 常见误区

- 新架构只是换包名，行为一样。
- 有了 TurboModules 就完全不需要 JS 线程/异步。
- 用了 RN 就纯 JS、永远不必碰原生模块。

## 面试速答

> 🎯 RN 新架构三大支柱：JSI(JS↔原生直接同步调用、替掉异步序列化桥)、Fabric(新渲染、C++ 同步布局、支持并发)、TurboModules(原生模块按需初始化)+Codegen(类型化生成两端接口)。收益是去掉桥瓶颈→更快/启动更省/类型安全；代价是三方原生库需迁移。
> 🔍 追问：Bridge 为什么会成为性能瓶颈？
> 🔍 追问：TurboModules 相比旧 NativeModule 的差别？

## 相关术语

[[React Native移动应用开发]]、[[React深入]]、[[React Native 组件与布局]]、[[Flutter跨平台开发实战]]

## 参考资料

建议人工核验：以 React Native 新架构官方文档为准；未编造文献编号。
