---
title: "TypeScript 模块与声明文件"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# TypeScript 模块与声明文件

> 📌 **导航**：本文是 **TypeScript 模块与声明文件** 词条，属 [[TypeScript高级编程指南]] 子词条。

## 定义

**一句话定义：** TS 模块系统决定代码如何按 import/export 拆分与解析（ESM / CommonJS / UMD 等），而 `.d.ts` 声明文件只为 JS 或外部库"补充类型"——描述形状、不含运行时代码。

**通俗类比：** 模块是"房间怎么打通、门牌怎么寻址"；`.d.ts` 是"给一件没标签的商品贴说明书"——东西照用，但你知道它是什么。

## 为什么需要它

前端打包生态长期并存多种模块规范，选错会导致互操作、tree-shaking、`moduleResolution` 报错等问题。而大量 JS 库无类型，TS 世界靠 `.d.ts`（或 `@types`）给它们补上类型，才能既有生态又有类型安全。

## 核心机制

- **模块规范**：ESM（`import`/`export`、静态、利于摇树、现代默认）；CommonJS（`require`/`module.exports`、Node 传统、动态）；AMD/UMD（浏览器异步/通用兼容，历史包袱）。`tsconfig` 的 `module`/`target`/`moduleResolution` 决定编译与解析。
- **声明文件 `.d.ts`**：`declare` 描述变量/函数/类/模块的类型；`declare global`/ambient 声明全局；`declare module 'x'` 给无类型包补声明；同名接口**声明合并/模块增强**给已有类型加成员。
- 优先用 `@types/*` 或库自带类型；自定义 `.d.ts` 放 `types/` 并纳入 `tsconfig`。

## 具体示例

给无类型的 JS 模块补一份最小声明，并用声明合并增强第三方类型：

```typescript
declare module 'legacy-lib' {
  export function doThing(a: string): number;
}
declare module 'express-serve-static-core' {
  interface Request { user?: { id: string } }  // 模块增强
}
```

## 何时用与何时不用

- **用**：包互操作/打包配置按运行环境选 `module`；给无类型 JS/库写 `.d.ts` 或用 `@types`；给框架对象挂自定义字段用声明合并。
- **不用**：别在 `.d.ts` 里写实现（它只描述）；能不手写声明就别写（先找 `@types`/官方类型）。

## 优劣与代价

✅ 模块规范解耦复用、ESM 利于 tree-shaking；声明文件把类型带到无类型生态。
✅ 模块增强/全局声明让跨文件扩类型无需改源。
⚠️ ESM/CJS 混用易踩坑（默认导入互操作、扩展名/解析）。
⚠️ 手写 `.d.ts` 可能与真实运行时脱节、维护成本。

## 与相关概念的区别

- **`.d.ts` vs 普通 `.ts`**：前者纯类型、编译产物为 JS/被擦除；后者有运行时逻辑。
- **ESM vs CJS**：静态、同步加载 vs 动态 `require`、CommonJS 互操作差异。
- 与 [[类型系统]]/[[泛型]]：模块与声明文件管"如何组织与描述外部代码"，类型系统管"值如何被约束"。

## 常见误区

- `.d.ts` 里可以写实际函数实现。
- `export default` 在 ESM 与 CJS 里行为完全一致、互操作无坑。
- 想要类型只能自己给 JS 库写 `.d.ts`，没有 `@types` 这条路。

## 面试速答

> 🎯 模块：ESM(import/export 静态可摇树) / CJS(require 动态) / AMD·UMD(兼容)，由 tsconfig module/moduleResolution 决定；.d.ts 用 declare 给 JS 补类型、支持全局与模块增强(声明合并)。优先 @types，别在 .d.ts 写实现。
> 🔍 追问：ESM 与 CommonJS 的关键差异与互操作坑？
> 🔍 追问：.d.ts 和 .ts 有何本质不同？

## 相关术语

[[TypeScript高级编程指南]]、[[TypeScript深入]]、[[包管理器与构建工具]]、[[类型系统]]

## 参考资料

建议人工核验：以 TypeScript Handbook（Modules / Declaration Files）为准；未编造文献编号。
