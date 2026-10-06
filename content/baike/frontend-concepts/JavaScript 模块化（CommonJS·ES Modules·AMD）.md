---
title: "JavaScript 模块化（CommonJS·ES Modules·AMD）"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# JavaScript 模块化（CommonJS·ES Modules·AMD）

> 📌 **导航**：本文是 **JavaScript 模块化（CommonJS·ES Modules·AMD）** 词条，属于 frontend-concepts 术语集。相关枢纽：[[JavaScript 基础核心概念]]、[[前端工程化核心概念]]。

## 定义

**一句话定义：** 模块化把代码切成各有独立作用域、显式声明导入导出的单元；JS 先后有三套方案——CommonJS 的同步 `require`、ES Modules 的静态 `import`、AMD 的异步 `define`，差别在加载时机与能否静态分析，浏览器与 Node 的现在时是 ESM。

**通俗类比：** 像工具箱分格：扳手放扳手格、螺丝刀放螺丝刀格，要哪件取哪件。三套方案的分别是"当面递给你（同步）""先看清单再一次性配齐（静态）""下单后等送到（异步）"。

## 为什么需要它

JS 早期全量共享全局作用域，一个变量名冲突就能让两段代码互毁。模块给每份代码独立作用域、把依赖变成显式声明，才谈得上按需加载、tree-shaking 与多人协作；也才有"这个包对外暴露什么"的边界。

## 核心机制

| 维度 | CommonJS | ES Modules | AMD |
|---|---|---|---|
| 语法 | `require` / `module.exports` | `import` / `export` | `define([deps], factory)` |
| 加载 | 运行时同步读取 | 编译期静态解析声明 | 运行时异步取依赖 |
| 导出语义 | 值的拷贝（快照） | 活绑定（live binding） | 工厂返回值 |
| 静态分析 | 难（路径可动态拼） | 易 → tree-shaking 可行 | 一般 |
| 主场 | Node.js 老生态、`.cjs` | 浏览器原生 + 现代 Node | RequireJS 时代，已退场 |

- **拷贝 vs 活绑定**：CJS 拿到的是导出时刻的快照，源模块后续重新赋值不会同步过来；ESM 拿到的是绑定，值随源模块变。这是"require 与 import 不是换个写法"的核心分水岭。
- **静态结构换来工具能力**：ESM 的 import/export 在编译期即可确定，打包器能删掉未被引用的导出（tree-shaking）、能并行预取依赖；CJS 的动态 `require(variable)` 让这两件事失去前提。
- **异步性是历史动因**：AMD 为"浏览器要边下边执行"而生，`import()` 动态导入与 `<script type="module">` 之后，这个位置被原生方案接替。

## 具体示例

```javascript
// CommonJS（Node 老生态）：同步、值拷贝
const { PI, add } = require("./math.js");

// ES Modules：静态声明 + 默认导出 + 活绑定
export const PI = 3.14159;
export default class Calculator {}
import Calculator, { PI, add } from "./math.js";

// AMD（RequireJS）：异步声明依赖，工厂里拿实参
define(["jquery"], function ($) { return { init() {} }; });
```

## 何时用与何时不用

- **用**：新代码一律 ESM；写只给 Node 老版本消费的包才用 CJS；维护 RequireJS 遗留项目时按 AMD 读源码。混用时记住 `.mjs`/`type: "module"` 决定 Node 按哪套解析。
- **不用**：不要在浏览器里裸 `<script>` 直接 `require`（那是打包器注入的运行时，不是平台能力）；也别指望对 CJS 依赖做彻底 tree-shaking。

## 优劣与代价

✅ ESM 是语言标准：浏览器原生可跑、静态可分析、语义有活绑定与顶层 await。
✅ CJS 的心智模型极简（就是一段同步执行的代码返回一个对象），Node 交互式与脚本场景仍顺手。
⚠️ 两套体系长期共存带来的扩展名、`this`、`__dirname` 差异是构建配置的常见坑（工具链侧见 [[前端工程化]]）。
⚠️ AMD 已属历史方案，只在读老项目源码时还会遇到，不必再当作选型选项。

## 与相关概念的区别

- **vs [[前端工程化]]**：工程化管打包、拆包与交付流水线，本条管模块语法与加载语义；tree-shaking 的能力由本条的静态结构提供，实现由那条的构建工具承担。
- **vs [[包管理器与构建工具]]**：包管理器解"依赖从哪来、怎么装"，模块系统解"代码怎么互相引用"；`exports` 字段是两者交界。
- **vs [[JavaScript 作用域与 this]]**：模块作用域是比函数作用域更大一层的独立作用域，作用域链在模块内部照旧生效。

## 常见误区

- 以为 `import` 只是 `require` 换了个新写法，两者导出语义相同。
- 以为只要用了打包器，CommonJS 项目也能得到完整的 tree-shaking。
- 以为 `.js` 文件在任何 Node 环境里都按 ES Modules 解析。

## 面试速答

> 🎯 JS 模块三代：CommonJS 运行时同步 require、导出值拷贝，Node 老生态；ES Modules 编译期静态 import、活绑定、可 tree-shaking、浏览器原生；AMD 异步 define 已被取代。差别在加载时机与能否静态分析。

## 相关术语

[[JavaScript 基础核心概念]]、[[前端工程化]]、[[前端工程化核心概念]]、[[包管理器与构建工具]]、[[JavaScript 作用域与 this]]、[[TypeScript深入]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇承接原《JavaScript 基础核心概念》模块化（CommonJS / ES Modules / AMD）一节，三段示例压缩自原稿；`exports` 字段与顶层 await 建议对照 Node 官方文档复核。
