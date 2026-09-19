---
title: "CSS 预处理与模块化（Sass·Less·CSS Modules）"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# CSS 预处理与模块化（Sass·Less·CSS Modules）

> 📌 **导航**：本文是 **CSS 预处理与模块化（Sass·Less·CSS Modules）** 词条，属于 frontend-concepts 术语集。相关枢纽：[[前端工程化核心概念]]、[[HTML & CSS 核心概念]]。

## 定义

**一句话定义：** 两件事被常混为一谈：预处理器（Sass/Less）给 CSS 加上变量、嵌套、mixin、函数这些编程能力，解决"写起来重复"；CSS Modules 在构建期把类名哈希化，解决"作用域会撞车"。前者改语法，后者改名字。

**通俗类比：** CSS 像记流水账，同一条数值抄十遍；Sass/Less 是把它写成程序（有变量和函数）。CSS Modules 则是给每个类名发身份证号——不同组件里的 `.title` 编译后是两个互不相干的哈希名。

## 为什么需要它

原生 CSS 缺变量与嵌套时，一次改主题色要全文替换；SPA 里所有组件样式共享同一个全局作用域，`.title` 之类的短名冲突是常态。预处理器把重复收敛成定义，模块化把作用域收敛到文件内。

## 核心机制

| 维度 | Sass | Less | CSS Modules |
|---|---|---|---|
| 文件与语法 | `.scss`，功能最全、社区最大 | `.less`，语法更接近 CSS | 约定文件名 `*.module.css` |
| 解决的问题 | 值复用、嵌套、mixin、函数 | 同左，能力子集 | 类名作用域隔离 |
| 运行时机 | 构建期编译回标准 CSS（编译期常量） | 同左 | 构建期由打包器把类名换成哈希名，样式内容不变 |
| 典型写法 | `$primary`、`@mixin` / `@include`、`&` | 变量、嵌套 | `styles[variant]` |

- **`&` 嵌套解决的是"选择器手写重复"而不是作用域**：`.card { &-header {} }` 编译成 `.card-header`，嵌套只是拼接与缩进，它不阻止别人覆盖你——隔离只能交给 CSS Modules 或命名约定。
- **CSS Modules 是编译期方案，不是运行时方案**：`Button.module.css` 里的 `.primary` 渲染成 `Button_primary__a1b2c` 这类哈希名，代价是必须在 JS 里以对象引用类名；这与 BEM 靠人守命名、CSS-in-JS 运行时生成样式是三种不同取舍。
- **原生 CSS 正在吃掉预处理器的地盘**：CSS 变量与原生嵌套补齐了两大卖点，新项目可优先考虑原生 CSS + PostCSS（兼容转换见 [[代码规范与转换工具链（Babel · ESLint · PostCSS）]]）；运行时可改的主题值属 CSS 变量而非编译期变量，见 [[CSS 变量与动画]]。

## 具体示例

```scss
// Sass（SCSS）
$primary: #1890ff;
$spacing-md: 16px;
@mixin flex-center { display: flex; justify-content: center; align-items: center; }
.card {
  background: white; padding: $spacing-md;
  &-header { font-size: 18px; }        // → .card-header
  &-body { @include flex-center; }
  @media (max-width: 768px) { padding: 8px; }
}
/* Button.module.css → JS 里 import styles from "./Button.module.css"
   className={styles.primary} 渲染为 class="Button_primary__a1b2c" */
```

## 何时用与何时不用

- **用**：重复色值/间距多、要用 mixin 复用布局片段时上 Sass；组件多、多人并行写样式时上 CSS Modules（最轻量的隔离方案）。
- **不用**：设计令牌要运行时切换（主题、换肤）时编译期变量与 mixin 都不动，要用 CSS 变量；样式量很小或已有框架级样式方案时，再加预处理器只是多一条编译管线。

## 优劣与代价

✅ 预处理让"改一个值改全站"成为可能，嵌套让 DOM 结构与 CSS 结构对得上。
✅ CSS Modules 不需要团队遵守命名纪律，隔离由构建保证，是三者里最省心智的。
⚠️ 预处理语法是额外一层学习成本，且与原生能力重叠后会出现"同一项目两种写法"。
⚠️ 类名哈希化后调试要认得编译产物，跨文件复用样式（`:global`、组合类）比全局 CSS 麻烦。

## 与相关概念的区别

- **vs [[代码规范与转换工具链（Babel · ESLint · PostCSS）]]**：PostCSS 把标准 CSS 转成兼容 CSS，不发明写法；Sass/Less 发明写法再编译回标准 CSS。
- **vs BEM**：BEM 用 `block__element--modifier` 的命名约定换隔离，靠人守；CSS Modules 用哈希换隔离，靠构建守。
- **vs [[CSS渲染性能]]**：那一条讲样式怎么在浏览器里变成像素，本条讲样式怎么被写出来与编出来。

## 常见误区

- 以为 Sass 嵌套天然提供作用域隔离，其实深层嵌套照样被外层命中。
- 把编译期的 `$primary` 当成运行时可改的 CSS 变量，据此做主题切换。
- 以为 CSS Modules 会重写样式内容，其实它只改类名。

## 面试速答

> 🎯 Sass/Less 是预处理器：变量、嵌套（`&`）、mixin、函数，构建期编译回标准 CSS；CSS Modules 是作用域方案：类名编译期哈希化避免全局冲突。一个改语法，一个改名字。

## 相关术语

[[前端工程化核心概念]]、[[HTML & CSS 核心概念]]、[[CSS 变量与动画]]、[[CSS 布局（Flexbox 与 Grid）]]、[[CSS 选择器与伪类伪元素]]、[[代码规范与转换工具链（Babel · ESLint · PostCSS）]]、[[JavaScript 构建工具（Webpack 与 Vite）]]、[[CSS渲染性能]]、[[响应式设计]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇合并原《前端工程化核心概念》Sass/Less 与 CSS Modules 两节，原稿两段示例（含 `&` 编译结果对照）压缩为上表与一段示例；原生 CSS 嵌套与变量的标准化进度建议对照官方文档复核。
