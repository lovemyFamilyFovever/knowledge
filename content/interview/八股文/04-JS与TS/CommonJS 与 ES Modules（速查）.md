---
title: "CommonJS 与 ES Modules"
tags: [八股文, JavaScript 与 TypeScript]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# CommonJS 与 ES Modules

## 一句话定义

一个运行时 require 值拷贝，一个编译期确定依赖且可树摇。

## 面试官为什么问它

简历写了 Vite 和多年原生 JS，混用报错是构建里最常见的问题，他要知道你是否理解差异。

## 30 秒版回答

CommonJS 是 Node 早期方案：`require` 同步加载、导出的是值的拷贝、可以条件加载，缺点是没法静态分析。ESM 是语言标准：`import/export` 静态结构，编译期就能确定依赖图，因此摇树优化可行；导出是实时绑定，模块内部改了外部能看到。互操作坑集中在扩展名、`package.json` 的 type 与 exports 映射、以及默认值解析规则。我的做法是新代码全用 ESM，只有必须接老包时才做适配层。

## 被追问三层时的诚实边界

我实际处理过 CJS 与 ESM 混用导致的构建与运行期报错、也配过 exports 映射；顶层 await 与 `import.meta` 的细节我用法不熟，我的理解是它们只在异步初始化和取当前模块路径时才需要。

## 本库深挖

- [[JavaScript 模块化（CommonJS·ES Modules·AMD）]] —— 三代模块方案的对照
- [[export]] —— 导出与解构的语法细节
- [[Node.js与全栈面试题库 - 50道精选题目]] —— 第 5、8 题：两套体系与模块解析算法
