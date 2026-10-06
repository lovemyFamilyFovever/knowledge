---
title: "CSS与HTML面试题库 - 60道精选题目"
tags: []
source: "baike"
source_path: "技术题库 / CSS与HTML"
collected: "2026-09-05"
status: "imported"
---

本页汇总 60 道 CSS 与 HTML 面试题，覆盖基础、布局、动画、渲染性能、响应式、高级特性与 HTML5 七大板块；难度由初级到高级梯度分布，每题含核心结论、关键要点与面试官追问。

## CSS 基础（10 题）

### 1. CSS选择器的优先级是如何计算的？｜初级

核心结论：浏览器按「来源与重要性 → 选择器特异性 → 书写顺序」三级依次比较，特异性用 (行内, ID, 类/属性/伪类, 元素/伪元素) 四元组衡量，高位大者胜。

- 权重六档（由高到低）：
  1. `!important` 声明（最高优先级，但会被更高层来源的 `!important` 反超）
  2. 行内样式 `style` 属性：`1,0,0,0`
  3. ID 选择器 `#id`：`0,1,0,0`
  4. 类 `.class`、属性 `[type]`、伪类 `:hover`：`0,0,1,0`
  5. 元素 `div`、伪元素 `::before`：`0,0,0,1`
  6. 通配符 `*`、子代/相邻等组合符：`0,0,0,0`
- 比较规则：从四元组最高位逐位比较，先比行内再比 ID、再比类、最后比元素；`!important` 会反转来源顺序（开发者/用户的 `!important` 高于普通作者样式）。
- 继承与默认：继承得到的样式特异性为 0，低于任何直接匹配规则；浏览器默认样式优先级最低。
- 同特异性时，后定义的规则覆盖先定义的（源顺序取胜）。

> 🎯 关键要点
> - 特异性四元组从左到右比较，先比行内、再比 ID。
> - `!important` 是「最后手段」，会破坏自然级联、极难被覆盖。
> - 通配符与组合符不增加特异性。
> - 继承值特异性为 0，遇到任何匹配规则都会被覆盖。
> - 调试用开发者工具的 Computed/Styles 面板查看最终生效来源。

> 🔍 追问
> - 行内 `style` 上的 `!important` 与作者样式表的 `!important` 谁更高？
> - `:not(.a.b)` 的特异性等于多少？

### 2. 请解释盒模型（Box Model）是什么？｜初级

核心结论：CSS 盒模型描述每个元素在页面中占据的空间，由外到内分四层；`box-sizing` 决定 `width/height` 是否包含 padding 与 border。

- 四个组成部分：
  - Content（内容）：文本、图片等实际内容区。
  - Padding（内边距）：内容与边框之间的空白。
  - Border（边框）：环绕内边距的边界。
  - Margin（外边距）：元素与其他元素之间的间距，不计入自身尺寸。
- 两种盒模型：
  - 标准盒模型 `content-box`：`width/height` 只包含内容区，不含 padding 和 border。
  - IE 盒模型 `border-box`：`width/height` 包含内容、padding 和 border。
- 现代实践：全局设置 `box-sizing: border-box`，在响应式布局中设置固定 `width` 时 padding 不会撑破容器。

| 盒模型 | `width/height` 包含 | 元素实际占宽 | 定宽 + padding 时 |
| --- | --- | --- | --- |
| `content-box`（标准） | 仅内容区 | width + padding + border | 容器被撑大，可能溢出 |
| `border-box`（IE） | 内容 + padding + border | width | 外尺寸受控，内容区被压缩 |


```css
*, *::before, *::after {
  box-sizing: border-box;
}
```

> 🎯 关键要点
> - 四个区域由外到内为 margin / border / padding / content。
> - `content-box` 与 `border-box` 的差异仅在于 `width` 的计算口径。
> - `margin` 不计入元素自身所占盒尺寸，但影响外部排布。
> - `box-sizing: border-box` 能避免 padding 撑大定宽容器，是响应式常用基线。
> - 背景绘制到 padding 区，border 区默认也覆盖背景。

> 🔍 追问
> - `margin` 重叠（collapse）发生在哪些场景？如何消除？
> - `box-sizing` 能否被继承？

### 3. CSS单位有哪些？它们各自适用什么场景？｜初级

核心结论：CSS 单位分绝对单位与相对单位，响应式项目应以相对单位为主、绝对单位只用于需要精确控制的细节。

- 绝对单位：`px`、`cm`、`mm`、`in` 等，1in = 96px；不随环境缩放，响应式中不推荐做主单位。
- 相对单位：
  - `em`：相对父元素字体大小，适合组件内间距。
  - `rem`：相对根元素（`<html>`）字体大小，适合全局布局与统一缩放。
  - `%`：相对父元素，适合响应式宽度。
  - `vw`/`vh`：相对视口宽/高，适合全屏布局。
- 特殊单位：`ch`（字符 0 宽度）、`ex`（x 高度）、`fr`（Grid 轨道剩余比例）。

```css
:root { font-size: 16px; }
.card { padding: 1rem; width: 50%; }      /* rem 全局、% 相对父 */
.title { font-size: 5vw; }                /* vw 全屏标题 */
.grid { display: grid; grid-template-columns: 1fr 2fr; }
```

> 🎯 关键要点
> - `px` 精确但僵化，`rem` 易于整体缩放，`em` 在组件内保持相对性。
> - `vw/vh` 依赖视口，移动端 `100vh` 可能包含地址栏高度。
> - `fr` 仅用于 Grid，表示剩余空间分配比例。
> - 避免在同一布局中无意义地混用多种单位。

> 🔍 追问
> - `rem` 与 `em` 嵌套时各自如何计算？
> - `vmin/vmax` 在横竖屏切换时分别取什么值？

### 4. 请解释CSS继承的概念和规则｜中级

核心结论：CSS 继承指部分属性自动从父元素传递给子元素；开发者可用 `inherit`/`initial`/`unset`/`revert` 显式控制继承行为。

- 自然继承的属性：
  - 字体相关：`font-family`、`font-size`、`color`、`font-weight`。
  - 文本相关：`text-align`、`line-height`、`letter-spacing`、`word-spacing`。
  - 列表相关：`list-style-type`、`list-style-position`。
- 继承规则与关键字：
  - 自然继承：上述属性自动向下传递。
  - `inherit`：强制继承父元素的计算值。
  - `initial`：重置为属性的初始值（未必是 0 或空）。
  - `unset`：有继承性的属性表现为 `inherit`，否则表现为 `initial`。
  - `revert`：回退到用户代理/作者样式表中的上一层定义。

> ⚠️ 注意
> `unset` 与 `initial` 不同：`unset` 对可继承属性等价于 `inherit`，对不可继承属性才等价于 `initial`。

> 🎯 关键要点
> - 不是所有属性都会继承，`margin`、`padding`、`border` 等盒模型属性默认不继承。
> - 在 `<body>` 上设置字体与颜色可借助继承减少重复代码。
> - `color` 可继承，但 `background` 不继承。
> - CSS 变量（自定义属性）天然可继承，是更灵活的「继承」手段。

> 🔍 追问
> - `all: unset` 会对一个按钮造成哪些副作用？
> - `revert` 与 `unset` 在级联来源上的区别是什么？

### 5. 什么是CSS层叠（Cascade）？它如何影响样式应用？｜中级

核心结论：层叠（Cascade）是浏览器在多条规则同时匹配同一元素时，决定最终样式的一套算法，综合「来源、重要性、特异性、源顺序」四个维度。

- 层叠的来源与重要性顺序（由低到高）：
  1. 浏览器默认样式（user agent）
  2. 用户样式（user）
  3. 作者样式（author）
  4. 作者 `!important` ＞ 用户 `!important` ＞ 浏览器 `!important`
  - 注意：`!important` 会反转「作者优先于用户」的常规顺序。
- 层叠算法步骤：
  1. 收集所有匹配该元素的声明。
  2. 按来源与重要性筛选排序。
  3. 同组内按选择器特异性排序。
  4. 特异性相同则按源顺序，后定义者胜。
  5. 得出最终计算样式。
- 实际影响：可利用层叠做主题覆盖与样式重置，但应克制使用 `!important`。

> 🎯 关键要点
> - 层叠 = 来源重要性 + 特异性 + 顺序，三者逐级兜底。
> - 默认来源顺序为「浏览器 < 用户 < 作者」。
> - `!important` 反转来源优先级，是维护噩梦的根源。
> - 大型项目要靠清晰的架构（如 @layer、BEM）而非堆特异性来管理层叠。

> 🔍 追问
> - 浏览器默认样式与作者样式冲突时，谁优先？
> - 如何用 `@layer` 改变来源之外的层叠次序？

### 6. 请解释CSS伪类和伪元素的区别和用法｜中级

核心结论：伪类用于选中「处于某状态的元素」（不新增节点），伪元素用于创建「DOM 中不存在的虚拟节点」；伪类用单冒号、伪元素用双冒号。

- 伪类（单冒号）：描述元素的特定状态或特征。
  - `:hover` 鼠标悬停、`:focus` 获得焦点、`:active` 激活态。
  - `:nth-child(n)` 第 n 个子元素、`:not(selector)` 排除特定选择器。
- 伪元素（双冒号）：在元素内生成虚拟节点承载装饰内容。
  - `::before` 在内容前插入、`::after` 在内容后插入。
  - `::first-line` 首行、`::first-letter` 首字母、`::selection` 选中文本。
- 关键差异：伪元素默认需要 `content` 属性才会渲染；伪类不依赖 `content`，仅匹配已有元素。

| 维度 | 伪类 | 伪元素 |
| --- | --- | --- |
| 作用 | 选中处于某状态的已有元素 | 创建 DOM 中不存在的虚拟节点 |
| 语法 | 单冒号 `:hover` | 双冒号 `::before` |
| 是否依赖 `content` | 否 | 是（否则不渲染） |
| 典型值 | `:hover` `:focus` `:nth-child()` `:not()` | `::before` `::after` `::first-line` `::selection` |


```css
a:hover { color: #f60; }
.tip::after {
  content: "↑";
  margin-left: 4px;
}
li:nth-child(odd) { background: #f5f5f5; }
```

> 🎯 关键要点
> - 伪类选中「状态」，伪元素生成「虚拟节点」。
> - 伪元素必须写 `content`（即使是空串）才会显示。
> - `::before/::after` 生成的内容无法被屏幕阅读器可靠朗读，勿放关键信息。
> - 历史写法 `:before` 仍被兼容，但新代码应统一用双冒号。

> 🔍 追问
> - `:nth-child(2n+1)` 与 `:nth-of-type(odd)` 有何区别？
> - 伪元素能再嵌套伪元素吗？

### 7. 如何实现水平垂直居中？请列举至少5种方法｜中级

核心结论：已知尺寸用绝对定位 + `transform`，未知尺寸优先 Flexbox/Grid，纯文本用 `text-align`+`line-height`，老方案可用 table 布局。

- 方法一·文本居中：`text-align: center`（水平）+ `line-height` 等于容器高（垂直，仅单行文本）。
- 方法二·绝对定位 + `transform`：`position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%)`，不依赖子元素尺寸。
- 方法三·表格布局：`display: table-cell; vertical-align: middle`，父容器需为 `table`。
- 方法四·Flexbox：父容器 `display: flex; justify-content: center; align-items: center`。
- 方法五·Grid：`display: grid; place-items: center`（同时控制行列）或 `place-content: center`。

```css
/* Flexbox */
.parent { display: flex; justify-content: center; align-items: center; }
/* Grid */
.parent { display: grid; place-items: center; }
/* 绝对定位 */
.child { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
```

> 🎯 关键要点
> - `place-items: center` 是 Grid 一行实现双轴居中的最简写法。
> - `transform: translate(-50%,-50%)` 不引发重排，性能优于改 `top/left`。
> - 老 IE 不支持 Flex/Grid，必要时回退 table 或绝对定位方案。
> - 单行文本可用 `line-height` 居中，多行则不行。

> 🔍 追问
> - `justify-content` 与 `align-items` 在 Flex 中分别对应哪个轴？
> - 为什么 `margin: auto` 在 Flex/Grid 中也能居中？

### 8. 什么是CSS特异性（Specificity）？如何计算？｜中级

核心结论：特异性是「选择器权重的工程侧管控」，重点不是比较大小，而是用 `:is()/:where()/:not()` 与 @layer 等机制主动降低或隔离特异性，避免用 `!important` 堆优先级。

- 现代特异性计数要点：
  - 类、属性选择器 `[type]`、伪类 `:hover` 三者等价，各计 `(0,0,1,0)`。
  - `:is()` 取「括号内特异性最高的参数」作为整体特异性；`:where()` 与 `:not()` 的括号本身计 0，但 `:not(.a)` 内部的 `.a` 正常计数。
  - 元素、伪元素各计 `(0,0,0,1)`；组合符不计数。
- 工程控制而非硬扛：
  - 用 `:where()` 包裹重置规则，使其特异性恒为 0，方便后续覆盖。
  - 用 `@layer` 把工具类、第三方样式放进低优先级层，组件样式放高层，避免比谁选择器更长。
  - 优先「降低自身特异性 / 用层隔离」而非追加 `!important` 或使用 ID 选择器。
- 与 Q1 的分工：Q1 讲权重怎么算、怎么比较；本题讲如何主动控制特异性。

```css
/* :where 特异性为 0，便于覆盖 */
:where(button, input) { margin: 0; }
/* :is 取参数中最高特异性 */
:is(section, #hero) p { color: #333; }   /* 等于 #hero p 的特异性 */
@layer utilities, components;
@layer components { .btn { color: blue; } }
```

> ⚠️ 注意
> `:is()` 会「继承」其参数里最高的特异性，容易意外拉高权重；而 `:where()` 永远为 0，重置样式优先用 `:where()`。

> 🎯 关键要点
> - 类、属性选择器、伪类三者权重相同。
> - `:where()` 恒为 0 特异性，`:is()` 取参数最高特异性。
> - `:not()` 括号内选择器正常计数。
> - 与其堆 `!important`，不如用 @layer 隔离或降低选择器特异性。

> 🔍 追问
> - `:is(.a, #b)` 作为整体特异性是多少？
> - 为什么说 @layer 比 `!important` 更适合管理第三方样式？

### 9. CSS变量（自定义属性）有哪些优势？｜中级

核心结论：CSS 自定义属性（`--x`）提供可复用、可继承、可被 JS 动态修改的设计令牌，是主题化与响应式系统的基石。

- 核心优势：
  - 可重用性：定义一次（`--primary`），多处 `var(--primary)` 引用。
  - 可维护性：改一处即可全局更新，优于散落的硬编码值。
  - 动态性：可在 JS 中读写 `style.setProperty('--primary', ...)`，无需改样式表。
  - 作用域与继承：声明在 `:root` 全局可用，声明在局部则仅该子树生效，并沿 DOM 向下继承。
- 配合 `calc()` 可做运行时计算，如 `padding: var(--u) calc(var(--u) * 2)`。

```css
:root {
  --primary-color: #2196f3;
  --spacing-unit: 8px;
}
.button {
  background: var(--primary-color);
  padding: var(--spacing-unit) calc(var(--spacing-unit) * 2);
}
:root.dark-theme { --primary-color: #9c27b0; }
```

> 🎯 关键要点
> - 自定义属性天然继承，是比 `inherit` 关键字更灵活的机制。
> - `var()` 可带兜底值：`var(--x, #000)`。
> - 自定义属性区分大小写，值可以是任意合法 token。
> - 结合 `@media` 或类名切换根变量即可实现主题切换。

> 🔍 追问
> - `var()` 的回退值里能再嵌套 `var()` 吗？
> - 自定义属性参与动画有哪些限制？

### 10. 请解释CSS层叠层（@layer）的作用｜高级

核心结论：@layer 把样式划成「层」，层间按声明顺序比较优先级（后声明的层高于先声明的层），层内仍是常规层叠；但 `!important` 在层间会反转顺序，这是反直觉的关键点。

- 层叠顺序：未分层的普通样式优先级最高；分层样式中，后定义的层（在 `@layer a, b` 中靠右的）高于先定义的层。
- 层内行为：层内部依然按「特异性 + 源顺序」正常层叠，层的存在不改变层内比较规则。
- 反直觉点——`!important` 反转：在普通重要性下「后层胜先层」，但一旦加上 `!important`，顺序反过来——先声明的层反而高于后声明的层。这正是 @layer 用来「让基础样式 `!important` 兜底、工具类自由覆盖」的机制。
- 价值：把 reset、第三方库、组件、工具类分别入层，组件层天然覆盖基础层，无需提高选择器特异性。

```css
@layer base, components, utilities;   /* 后写的 utilities 优先级更高 */
@layer base {
  a { color: blue; }                  /* 基础层 */
}
@layer components {
  a.btn { color: red; }               /* 组件层覆盖基础层 */
}
/* 未分层样式优先级最高 */
a { color: green; }
```

> 🎯 关键要点
> - 未分层的样式永远高于任何 @layer 内的样式。
> - 普通重要性下「后声明层胜先声明层」。
> - `!important` 下层的优先级顺序反转，先声明层反而胜出。
> - @layer 让「低特异性选择器」也能稳定覆盖「高特异性选择器」。

> 🔍 追问
> - 为什么有时给第三方样式加 `!important` 反而被你的基础层盖住？
> - `@import` 语句放在 @layer 内外有何差异？

## 布局技巧（10 题）

### 11. Flexbox布局的核心概念是什么？｜初级

核心结论：Flexbox 是一维布局模型，沿「主轴 / 交叉轴」对齐与分布子项，靠容器属性控制整体、靠项目属性控制个体。

- 核心概念：
  - 主轴（Main Axis）：默认水平，由 `flex-direction` 决定方向。
  - 交叉轴（Cross Axis）：默认垂直，垂直于主轴。
  - 容器（Container）：设 `display: flex` 的元素。
  - 项目（Item）：容器的直接子元素。
- 容器属性：`flex-direction`（主轴方向）、`justify-content`（主轴对齐）、`align-items`（交叉轴对齐）、`flex-wrap`（换行）。
- 项目属性：`flex-grow`（放大比例）、`flex-shrink`（缩小比例）、`flex-basis`（基础尺寸）。

```css
.container {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}
.item { flex: 1 1 auto; }   /* grow shrink basis */
```

> 🎯 关键要点
> - Flexbox 只管「一个维度」的行或列。
> - `justify-content` 管主轴，`align-items` 管交叉轴，别混淆。
> - `flex: 1` 等价于 `flex: 1 1 0%`，会均分剩余空间。
> - 适合导航栏、卡片列表、表单对齐、垂直居中。

> 🔍 追问
> - `flex-basis: 0` 与 `auto` 在 `flex-grow` 时表现有何不同？
> - `align-content` 在什么条件下才生效？

### 12. CSS Grid布局与Flexbox有何区别？｜中级

核心结论：Flexbox 是一维（行或列）布局，Grid 是二维（同时管行与列）布局；整体页面骨架用 Grid，组件内部对齐用 Flexbox。

- 维度差异：
  - Flexbox：一维，沿单一主轴排列，适合「一条线」的流式分布。
  - Grid：二维，用 `grid-template-columns/rows` 显式定义行列轨道，适合矩阵式布局。
- 适用场景：
  - Flexbox 更适合：导航栏、工具栏、卡片行、表单元素对齐、不确定高度的居中。
  - Grid 更适合：整页布局、复杂网格、需精确控制行列交叠的区域、响应式网格系统。
- 协同：Grid 负责整体骨架，Flexbox 负责组件内部细节，二者不互斥。

| 维度 | Flexbox | Grid |
| --- | --- | --- |
| 维度 | 一维（行或列） | 二维（行 + 列） |
| 轨道 | 无显式轨道，沿主轴排布 | `grid-template-columns/rows` 显式定义 |
| 思路 | 内容驱动尺寸 | 布局驱动内容位置 |
| 典型场景 | 导航、工具栏、卡片行、居中 | 整页骨架、矩阵布局、区域交叠 |
| 换行/自适应 | `flex-wrap` 逐行排 | `auto-fill/auto-fit` + `minmax()` |


```css
/* Grid 二维 */
.page { display: grid; grid-template-columns: 200px 1fr 200px; }
/* Flex 一维 */
.nav  { display: flex; justify-content: space-between; }
```

> 🎯 关键要点
> - 只控制一个维度选 Flexbox，行列都要控制选 Grid。
> - Grid 的 `fr` 单位分配剩余空间，等价于弹性轨道。
> - Grid 可用 `grid-template-areas` 做语义化布局。
> - 复杂布局通常 Grid 比嵌套 Flex 更简洁。

> 🔍 追问
> - Grid 的 `1fr` 与 `auto` 轨道在内容溢出时如何分配？
> - Flex 的 `wrap` 与 Grid 的 `auto-fill` 各解决什么问题？

### 13. 如何实现多列等高布局？｜中级

核心结论：等高布局的本质是「让同一行的列共享行高」，现代用 Flexbox/Grid 天然等高，传统方案（padding 负 margin、table）已不推荐。

- Flexbox 方法：父容器 `display: flex`，子项 `flex: 1`，Flex 行内各项目默认拉伸到同行最高。
- Grid 方法：父容器 `display: grid; grid-template-columns: repeat(3, 1fr)`，Grid 同一行的单元格自动等高。
- 传统方案（不推荐）：
  - `padding-bottom` + 等大同向负 `margin-bottom` 撑高后裁切。
  - `display: table` / `table-cell`，单元格天然等高。
  - JS 动态测量并设置最高列高度。

```css
/* Flexbox 等高 */
.container { display: flex; }
.column { flex: 1; }
/* Grid 等高 */
.container { display: grid; grid-template-columns: repeat(3, 1fr); }
```

> 🎯 关键要点
> - Flex/Grid 的「拉伸对齐」默认即等高，无需额外代码。
> - `align-items: stretch`（默认）是等高的前提，设为 `flex-start` 会失效。
> - 传统 padding 负 margin 方案可读性差且有溢出隐患。
> - 现代项目直接上 Flex/Grid，原生支持等高。

> 🔍 追问
> - 若某列内容远超其他列，Flex 等高会撑高整行吗？
> - `align-items: stretch` 对绝对定位子项有效吗？

### 14. 请解释CSS的overflow属性及其值｜初级

核心结论：overflow 控制内容溢出容器边界时的处理方式，常用 `visible/hidden/scroll/auto/clip`，它还会影响 BFC 与滚动表现。

- 各值语义：
  - `visible`：默认，溢出内容照常显示、可超出容器。
  - `hidden`：裁剪溢出内容，不可滚动查看。
  - `scroll`：始终显示滚动条（即使无需滚动）。
  - `auto`：仅在内容溢出时显示滚动条。
  - `clip`：类似 hidden 但不允许程序性滚动（无滚动容器），更可控。
- 使用场景：卡片截断用 hidden；可能溢出也可能不溢出用 auto；`clip` 适合纯裁剪且不想生成滚动容器的场景。
- 副作用：`overflow` 非 `visible` 会触发 BFC；`overflow-x/y` 可单独设置，但其中一个为 `visible` 另一个非 visible 时，visible 会被计算为 `auto`。

```css
.box { overflow: hidden; }      /* 裁剪 */
.box { overflow: auto; }        /* 按需滚动 */
.box { overflow: clip; }        /* 裁剪且不可滚动 */
```

> ⚠️ 注意
> 在 `<body>` 上设 `overflow: hidden` 可能禁用整页滚动；`overflow-x: hidden` 配合 `overflow-y: visible` 时，浏览器会把 y 计算成 `auto`，可能引发意外滚动条。

> 🎯 关键要点
> - `auto` 与 `scroll` 的区别在于「是否始终显示滚动条」。
> - `clip` 比 `hidden` 更现代，且不会创建滚动容器。
> - `overflow` 非 visible 会建立 BFC。
> - 常与 `text-overflow` 配合实现文本截断。

> 🔍 追问
> - `overflow: hidden` 与 `display: flow-root` 在建立 BFC 上有何取舍？
> - 为什么 `overflow-x: hidden` 有时会让页面无法纵向滚动？

### 15. 如何实现圣杯布局和双飞翼布局？｜高级

核心结论：圣杯与双飞翼都是「两侧固定宽、中间自适应」的三栏布局；圣杯靠父 padding + 绝对定位，双飞翼靠中间额外包裹层 + 负 margin，现代用 Flex/Grid 更简洁。

- 圣杯布局：父容器左右 padding 预留侧栏位；左/右栏绝对定位贴边，中间栏 `margin` 让出侧栏宽度。
- 双飞翼布局：中间多一层 `.main` 包裹内容，三栏全部 `float: left`；左栏 `margin-left: -100%`、右栏 `margin-left: -200px` 拉回，中间内容靠自身 `margin` 让位。
- 现代实现：Flex（`.main { flex: 1 }` + 两侧定宽）或 Grid（`grid-template-columns: 200px 1fr 200px`），语义清晰、无负 margin 黑魔法。

```css
/* 圣杯 */
.container { padding: 0 200px; position: relative; }
.left, .right { position: absolute; width: 200px; }
.left { left: 0; } .right { right: 0; }
.center { margin: 0 200px; }
/* 双飞燕（双飞翼） */
.container { float: left; width: 100%; }
.main { margin: 0 200px; }
.left  { float: left; width: 200px; margin-left: -100%; }
.right { float: left; width: 200px; margin-left: -200px; }
```

> 🎯 关键要点
> - 二者目标一致：中间优先渲染且自适应，两侧固定。
> - 圣杯用绝对定位、双飞翼用负 margin + 包裹层。
> - 负 margin 的 `-100%` 表示拉回「一整行宽度」到左栏位。
> - 新项目直接用 Grid/Flex，可读性与兼容性都更好。

> 🔍 追问
> - 双飞翼为什么需要中间额外加一层 `.main`？
> - Grid 实现时如何保证中间列优先加载（DOM 顺序）？

### 16. 什么是BFC（块格式化上下文）？如何触发？｜高级

核心结论：BFC 是一个独立的块级渲染区域，内部布局不影响外部、外部浮动也不侵入；常用于清除浮动、阻止 margin 重叠、隔离浮动。

- 触发条件清单：
  - 根元素 `<html>`。
  - 浮动元素（`float` 不为 `none`）。
  - 绝对/固定定位（`position: absolute | fixed`）。
  - 行内块（`display: inline-block`）。
  - 表格相关（`display: table-cell`、`table-caption`、`table` 等）。
  - `overflow` 不为 `visible`（如 `hidden/auto/scroll`）。
  - `display: flow-root`（专门为此而生，无副作用）。
- 三大用途：
  1. 包含浮动：父元素触发 BFC 可包裹浮动子元素，避免高度塌陷。
  2. 阻止 margin 重叠：相邻 BFC 之间的垂直 margin 不合并。
  3. 隔离浮动：BFC 区域不与外部浮动元素重叠（实现文字环绕侧栏布局）。

```css
.clearfix { display: flow-root; }     /* 推荐：专用于建立 BFC */
.modal-body { overflow: auto; }       /* overflow 非 visible 也触发 */
```

> 🎯 关键要点
> - `display: flow-root` 是建立 BFC 的「无副作用」首选。
> - `overflow: hidden` 能触发 BFC，但会裁剪溢出内容。
> - BFC 隔离浮动，也能抑制 margin 折叠。
> - 根元素天然是 BFC。

> 🔍 追问
> - `display: flow-root` 相比 `overflow: hidden` 建立 BFC 好在哪？
> - 两个相邻 BFC 的垂直 margin 会合并吗？

### 17. 如何实现文本截断（单行和多行）？｜中级

核心结论：单行截断用 `white-space + overflow + text-overflow`，多行截断用 `-webkit-line-clamp`，二者都依赖定宽容器。

- 单行截断：容器定宽 + `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`。
- 多行截断（基于 WebKit 弹性盒）：`display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: N; overflow: hidden`，`N` 为显示行数。
- 注意事项：必须设容器宽度；多行方案依赖 `-webkit-` 前缀，Firefox 也支持该前缀属性，但非WebKit内核（如旧 IE）不支持，必要时用 JS 兜底。

```css
.text-truncate {
  width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.text-clamp {
  width: 200px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}
```

> 🎯 关键要点
> - 单行三件套缺一不可：`nowrap + overflow:hidden + ellipsis`。
> - `-webkit-line-clamp` 需配合 `-webkit-box` 与 `overflow:hidden`。
> - 多行截断兼容性有限，关键业务用 JS 测量兜底。
> - 截断会隐藏文本，考虑提供 `title` 属性方便查看全文。

> 🔍 追问
> - `-webkit-line-clamp` 在非 WebKit 浏览器（如 Firefox）是否可用？
> - 如何在不支持 line-clamp 时优雅降级？

### 18. CSS的position属性有哪些值？它们的区别是什么？｜初级

核心结论：`position` 有 `static/relative/absolute/fixed/sticky` 五个常用值，区别在于是否脱离文档流、定位参照物是什么。

- 各值语义：
  - `static`：默认，正常文档流定位，忽略 `top/left` 等偏移。
  - `relative`：相对自身原位置偏移，不脱离文档流，仍占位。
  - `absolute`：脱离文档流，相对「最近的非 static 定位祖先」定位。
  - `fixed`：脱离文档流，相对视口定位，滚动时位置不变。
  - `sticky`：混合态，在阈值内像 relative，越过阈值后像 fixed（相对滚动容器/视口）。
- 使用场景：弹窗/下拉用 absolute，导航栏/返回顶部用 fixed，表头/侧栏用 sticky，微调用 relative。

| 值 | 是否脱离文档流 | 定位参照 | 典型用途 |
| --- | --- | --- | --- |
| `static` | 否 | 无（正常文档流） | 默认态，忽略偏移属性 |
| `relative` | 否（仍占位） | 自身原位置 | 微调、给 absolute 当参照 |
| `absolute` | 是 | 最近的非 static 祖先 | 弹窗、下拉、角标 |
| `fixed` | 是 | 视口（有 transform 祖先时改为该祖先） | 固定导航、返回顶部 |
| `sticky` | 否（越阈值后视觉吸附） | 最近的滚动容器 | 表头吸顶、侧栏跟随 |


```css
.modal { position: absolute; top: 50%; left: 50%; }
.bar   { position: fixed; top: 0; }
.th    { position: sticky; top: 0; }
```

> ⚠️ 注意
> `sticky` 必须设置 `top/right/bottom/left` 之一才生效；若祖先存在 `overflow: hidden/auto` 滚动容器，sticky 会相对该容器而非视口粘滞。

> 🎯 关键要点
> - absolute 的参照是「最近的非 static 祖先」，没有则到初始包含块。
> - fixed 相对视口，移动端某些浏览器对 fixed 支持有差异。
> - sticky 是 relative 与 fixed 的混合，需阈值触发。
> - 定位元素可用 `z-index` 控制层叠（需先形成层叠上下文）。

> 🔍 追问
> - absolute 元素没有定位祖先时会相对什么定位？
> - 为什么 sticky 在 `overflow: auto` 的父容器里「粘不住」？

### 19. 如何实现响应式图片？｜中级

核心结论：响应式图片靠「约束尺寸 + 按分辨率/视口切换源」实现，核心是 `max-width:100%`、`srcset/sizes` 与 `<picture>`。

- 基础约束：

```css
img { max-width: 100%; height: auto; }
```

- 按分辨率切换（`srcset` + `sizes`）：浏览器据设备 DPR 与视口选最合适图源，`sizes` 描述「该图在不同断点下的显示宽度」。
- 按艺术方向切换（`<picture>`）：用 `<source media>` 在不同视口给不同裁切/格式的图，`<img>` 作兜底。

```html
<img
  srcset="small.jpg 480w, medium.jpg 800w, large.jpg 1200w"
  sizes="(max-width: 600px) 480px, (max-width: 1000px) 800px, 1200px"
  src="medium.jpg" alt="响应式图片">

<picture>
  <source media="(min-width: 1200px)" srcset="large.jpg">
  <source media="(min-width: 768px)" srcset="medium.jpg">
  <img src="small.jpg" alt="响应式图片">
</picture>
```

> 🎯 关键要点
> - `max-width: 100%` 防止大图撑破布局，是响应式图片底线。
> - `srcset` 的 `w` 描述图源真实宽度，浏览器据 DPR 选择。
> - `sizes` 要如实反映显示宽度，否则选错图源。
> - `<picture>` 还能按格式优先给 WebP/AVIF。

> 🔍 追问
> - `srcset` 的 `480w` 中 `w` 代表什么？浏览器如何结合 DPR 选择？
> - `sizes` 写错会导致什么问题？

### 20. CSS的display属性有哪些常用值？｜初级

核心结论：`display` 决定元素如何参与布局，从基础的 `block/inline` 到布局型的 `flex/grid` 与语义型的 `flow-root/contents`，各有明确用途。

- 基础显示：
  - `none`：不渲染且不占空间。
  - `block`：块级，独占一行。
  - `inline`：行内，不独占行、不设宽高。
  - `inline-block`：行内块，可设宽高且同行排列。
- 布局相关：`flex`/`grid`/`inline-flex`/`inline-grid`/`table`/`table-cell`。
- 现代/语义值：
  - `flow-root`：建立 BFC，专用于清除浮动。
  - `contents`：元素自身不渲染，子元素「提升」到父级参与布局。
  - `list-item`：生成列表项标记；`run-in`：实验性运行框。

```css
.wrap { display: flow-root; }   /* 清除浮动且无裁剪副作用 */
.card { display: inline-block; }
```

> 🎯 关键要点
> - `inline-block` 既有 inline 同行特性又有 block 可设尺寸特性。
> - `display: none` 与 `visibility: hidden` 的差异：前者不占空间。
> - `flow-root` 比 `overflow:hidden` 更适合单纯建立 BFC。
> - `display: contents` 会让元素「消失」但保留子节点布局。

> 🔍 追问
> - `display: contents` 对可访问性（屏幕阅读器）有何影响？
> - `inline-flex` 与 `flex` 容器的外部表现有何不同？

## 动画与过渡（5 题）

### 21. CSS过渡（transition）和动画（animation）有什么区别？｜中级

核心结论：transition 是「状态变化补间」，需事件触发、无循环；animation 是「关键帧序列」，可自动播放、循环、控制多帧。

- 触发方式：transition 依赖状态切换（如 `:hover`、class 变化）才执行；animation 通过 `animation-name` 立即/定时自动运行。
- 能力差异：transition 只有起止两态；animation 支持多关键帧（`@keyframes`）、`iteration-count` 循环、`direction` 反向、`fill-mode` 保持终态。
- 性能共识：二者都应优先动画 `transform` 与 `opacity`，避免触发布局重排与重绘。

```css
.box { transition: all 0.3s ease; }
.box:hover { transform: scale(1.1); }

@keyframes rotate {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.spin { animation: rotate 2s linear infinite; }
```

> 🎯 关键要点
> - 简单悬停/状态变化用 transition。
> - 复杂序列、自动播放、循环用 animation。
> - 优先 `transform/opacity`，二者可走合成线程不触发重排。
> - transition 无法在「首帧即需动画」时自动运行，要靠 animation。

> 🔍 追问
> - 为什么 animation 可以自动播放而 transition 不行？
> - `animation-fill-mode: forwards` 解决什么问题？

### 22. 如何优化CSS动画的性能？｜高级

核心结论：动画性能优化的核心是「只动 compositor-only 属性（transform/opacity），把元素提升到独立合成层，避免重排重绘」。

- 优化原则：
  - 只用 `transform` 与 `opacity` 做动画，二者可由 GPU 合成线程处理，不触发 Layout/Paint。
  - 避免同时动画过多属性、避免动画 `width/height/top/left`（会重排）。
  - 用 `will-change` 提前提示浏览器为元素建层，但勿滥用。
- 工具与指标：用 Chrome DevTools Performance 面板看帧率，动画目标稳定 60fps（高刷屏可 120fps）；用 Layers 面板检查合成层数量，层数过多反而耗内存。

```css
/* 优化前：动 left/top → 重排 */
@keyframes move1 { 0%{left:0;top:0} 100%{left:200px;top:100px} }
/* 优化后：动 transform → 仅合成 */
.box { will-change: transform; }
@keyframes move2 { 0%{transform:translate(0,0)} 100%{transform:translate(200px,100px)} }
```

> ⚠️ 注意
> `will-change` 不是「越多越好」：每个合成层都占内存，低端设备上层过多会加剧卡顿甚至 OOM。

> 🎯 关键要点
> - 动画属性选择优先级：transform/opacity > 其他。
> - `will-change` 应「即用即加、用完移除」，避免常驻。
> - 目标 60fps，用 Performance/Layers 面板验证。
> - 低端设备务必实测，合成层内存开销不可忽视。

> 🔍 追问
> - 为什么动画 `top/left` 比 `transform: translate` 慢？
> - 如何判断一个动画是否触发了重排（Layout）？

### 23. 什么是CSS硬件加速？如何启用？｜高级

核心结论：硬件加速指把渲染工作交给 GPU（合成线程）处理，主要通过把元素提升为独立合成层实现；`transform`/`opacity`/`will-change` 是关键触发手段。

- 启用方式：
  - `transform`：任何 transform 动画会触发 GPU 合成（如 `translateZ(0)`）。
  - `opacity`：透明度变化走合成线程。
  - `will-change: transform`：显式提示浏览器建独立层。
- 注意：`transform: translateZ(0)` 是经典的「强制合成层」hack；但层过多会吃内存，filter 等属性跨浏览器表现不一。

```css
.element {
  will-change: transform;
  transform: translateZ(0);   /* 强制创建合成层 */
}
```

> 🎯 关键要点
> - 硬件加速本质是「元素进入 GPU 合成层」。
> - `transform`/`opacity` 是天然 compositor-only 属性。
> - `translateZ(0)` 是强制建层的兼容写法。
> - 层不是免费的：内存与合成成本需权衡。

> 🔍 追问
> - 硬件加速一定能提升性能吗？什么情况下反而变慢？
> - `will-change` 与 `translateZ(0)` 建层有何异同？

### 24. 如何实现平滑滚动效果？｜中级

核心结论：平滑滚动可用纯 CSS 的 `scroll-behavior: smooth`（整页或容器）或 JS 的 `scrollIntoView`/`scrollTo`，并应尊重用户的「减少动效」偏好。

- CSS 方案：`html { scroll-behavior: smooth }` 让锚点跳转与 `scrollTo` 平滑；也可只作用于某个可滚动容器。
- JS 方案：`element.scrollIntoView({ behavior: 'smooth' })`、`window.scrollTo({ top, behavior: 'smooth' })`，可控到具体坐标。
- 注意：`scroll-behavior: smooth` 现代浏览器支持良好；应配合 `prefers-reduced-motion` 在用户要求时降级为 `auto`。

```css
html { scroll-behavior: smooth; }
```

```js
element.scrollIntoView({ behavior: 'smooth', block: 'start' });
window.scrollTo({ top: 0, behavior: 'smooth' });
```

> 🎯 关键要点
> - 锚点跳转的平滑滚动用 CSS 即可，无需 JS。
> - JS 的 `scrollIntoView` 能精确控制对齐与行为。
> - 移动端滚动性能需实测，过度平滑可能拖慢低端机。
> - 尊重 `prefers-reduced-motion`，必要时降级为瞬时滚动。

> 🔍 追问
> - `scroll-behavior: smooth` 对 `scrollIntoView` 有效吗？
> - 如何在用户开启「减少动效」时关闭平滑滚动？

### 25. CSS动画的timing-function有哪些值？｜中级

核心结论：`timing-function` 控制动画/过渡的「进度节奏」，分预定义缓动函数、贝塞尔曲线 `cubic-bezier()` 与步进函数 `steps()` 三类。

- 预定义值：
  - `ease`：默认，慢起快落。
  - `linear`：匀速。
  - `ease-in`：慢起。
  - `ease-out`：慢落。
  - `ease-in-out`：慢起慢落。
- 自定义：
  - `cubic-bezier(x1,y1,x2,y2)`：任意三次贝塞尔曲线，精细控制加速/减速。
  - `steps(n, start|end)`：把动画切成 n 段阶梯式跳变，适合逐帧/打字机效果。
- 选择：进入动画用 ease-out，退出用 ease-in，状态切换用 ease-in-out，进度条/旋转用 linear。

```css
.box { transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94); }
.frames { animation: step 2s steps(4, end); }
```

> 🎯 关键要点
> - `ease` 是默认且通用，多数 UI 动效够用。
> - `linear` 用于旋转、进度条等需匀速的场景。
> - `cubic-bezier` 可精确塑形曲线。
> - `steps()` 做离散跳变，而非连续过渡。

> 🔍 追问
> - `steps(1, end)` 与 `steps(1, start)` 视觉差异是什么？
> - 贝塞尔曲线的 y 值能否大于 1？意味着什么？

## 渲染与性能（5 题）

### 26. 浏览器渲染流程中重排（Reflow）与重绘（Repaint）有什么区别？哪些 CSS 属性会触发重排？如何避免强制同步布局（layout thrashing）？｜高级

核心结论：重排（Reflow/Layout）是重新计算元素几何位置、成本高；重绘（Repaint）只重画外观、跳过布局；渲染管线为 JS→Style→Layout→Paint→Composite，强制同步布局发生在「写 DOM 后立刻读几何属性」时。

- 二者区别：
  - 重排：改变几何信息（尺寸、位置）时，浏览器重新计算布局树，并连带触发后续 Paint 与 Composite。
  - 重绘：仅视觉属性（颜色、阴影、可见性）变化时跳过 Layout，直接 Paint；比重排轻，但仍消耗主线程。
- 触发重排的典型属性：`width/height`、`margin/padding/border`、`top/left/right/bottom`、`display`、`position`、`float`、`font-size`、`line-height`、`vertical-align`、内容增删、`offsetWidth`/`clientHeight` 读取、`viewport` resize。
- 强制同步布局（layout thrashing）：在 JS 中交替「写样式/改 DOM」与「读 `offsetTop/clientWidth/getBoundingClientRect` 等几何属性」，浏览器被迫在每个读之前同步 flush 一次布局，循环放大开销。
- 规避：先批量读、再批量写；用 `requestAnimationFrame` 把写集中到一帧；或借助 `fastdom` 库读写分离。

```js
// 反例：读写交错 → 每次读都强制重排
for (const el of items) {
  el.style.width = el.offsetWidth + 10 + 'px'; // 写后立刻读
}
// 正例：先读后写
const widths = items.map(el => el.offsetWidth);
items.forEach((el, i) => { el.style.width = widths[i] + 10 + 'px'; });
```

> 🎯 关键要点
> - 重排必带重绘，重绘不一定带重排。
> - 渲染管线：JS→Style→Layout→Paint→Composite。
> - 几何读取类属性（offset*/client*/getBoundingClientRect）会触发强制同步布局。
> - 读写分离 + rAF 是消除 layout thrashing 的通用手段。

> 🔍 追问
> - 修改 `color` 与修改 `width` 在渲染管线上的差异在哪一步？
> - `will-change` 能否消除强制同步布局？

### 27. 什么是层叠上下文（Stacking Context）？哪些属性会创建它？为什么 z-index 有时会"失效"？｜高级

核心结论：层叠上下文是元素在 z 轴上的「隔离渲染单元」，子元素的 `z-index` 只在同一上下文内比较；z-index「失效」几乎都是因为比较的不是同一上下文。

- 什么是层叠上下文：每个上下文是一个独立的 z 轴盒子，内部子元素按上下文内规则堆叠，整体作为一个单元参与父上下文的排序。
- 创建条件（常见）：
  - 根元素 `<html>`（最外层上下文）。
  - `position` 非 static 且 `z-index` 非 auto。
  - `opacity` 小于 1。
  - `transform`/`filter`/`perspective`/`clip-path`/`mask` 非 none。
  - `will-change` 取值为上述任一属性。
  - `mix-blend-mode` 非 normal。
  - `isolation: isolate`。
  - Flex/Grid 的直接子项且 `z-index` 非 auto。
  - `position: fixed`（现代浏览器中）。
  - `contain: layout/paint` 等。
- 为什么 z-index 失效：z-index 只在「同一个层叠上下文」中比较大小；一个被层层嵌套在父上下文里的子元素，无论 `z-index` 多大，都无法越过父上下文的边界，盖到父上下文的兄弟之上。

> 💡 提示
> 调试 z-index 问题时，先沿 DOM 向上找「最近的创建了层叠上下文的祖先」，确认比较范围，再决定给谁加 `z-index` 或 `isolation`。

```css
.parent { position: relative; z-index: 1; }      /* 创建上下文 A */
.child  { position: absolute; z-index: 9999; }    /* 只在 A 内比较 */
.sibling-of-parent { position: relative; z-index: 2; } /* 与 A 同级比较 */
```

> 🎯 关键要点
> - z-index 的比较严格局限于同一层叠上下文。
> - transform/opacity/filter 等都会「意外」创建上下文。
> - 想要隔离比较范围可用 `isolation: isolate`。
> - Flex/Grid 子项设 z-index 也会建上下文。

> 🔍 追问
> - `opacity: 0.99` 为何会悄悄创建层叠上下文？
> - `isolation: isolate` 相比设 `z-index` 有何优势？

### 28. contain 与 content-visibility 是什么？如何用它们降低长列表/复杂页面的渲染开销？｜高级

核心结论：`contain` 把子树与页面其余部分在布局/绘制/尺寸上隔离，`content-visibility: auto` 跳过屏外元素的渲染；二者都能显著减少长列表与复杂页面的渲染与更新成本。

- `contain` 的取值与含义：
  - `size`：元素尺寸不依赖子内容（需自定尺寸），外部布局不受其内部影响。
  - `layout`：内部布局变化不向外传播，隔离重排。
  - `paint`：子内容不溢出元素绘制边界，可裁剪。
  - `style`：抑制部分属性（如 counters）向子树外扩散。
  - `strict` = `size layout paint`；`content` = `layout paint style`（常用，不强制自定尺寸）。
- `content-visibility: auto`：浏览器对「屏外」元素跳过其布局与绘制（相当于 `contain: layout style paint` + 跳过渲染），首屏与滚动性能大幅提升；配合 `contain-intrinsic-size` 预留占位尺寸，避免滚动条跳动。
- 兼容性：Chromium 系支持良好；Firefox 对 `content-visibility` 仍在推进；Safari 18+ 起支持。不支持的浏览器会「正常渲染」，无破坏性副作用，可放心渐进增强。

```css
/* 长列表项：跳过屏外渲染 */
.card { content-visibility: auto; contain-intrinsic-size: 200px; }
/* 复杂组件：隔离布局与绘制 */
.widget { contain: content; }
```

> ⚠️ 注意
> 用 `content-visibility: auto` 却不设 `contain-intrinsic-size`，元素屏外时高度为 0，会导致页面滚动条长度和锚点定位在滚动过程中剧烈跳动。

> 🎯 关键要点
> - `contain` 隔离重排/重绘，「影响范围」被锁在子树内。
> - `content-visibility: auto` 是长列表渲染优化的利器。
> - `contain-intrinsic-size` 必须配合，否则滚动跳动。
> - 两者均为渐进增强，不支持时仅退化为普通渲染。

> 🔍 追问
> - `contain: strict` 与 `content` 的差异为何关键（size 的副作用）？
> - `content-visibility: auto` 对 SEO 与可访问性有无影响？

### 29. 移动端 1px 边框问题是怎么产生的？设备像素比（DPR）与视口缩放有什么关系，如何解决？｜高级

核心结论：1px 边框「变粗」是因为 CSS 的 1px 是逻辑像素，在高 DPR 屏上被映射成多个物理像素；要得到真正发丝级细线需按 DPR 缩放绘制。

- 成因：CSS 像素是逻辑单位，`devicePixelRatio = 物理像素 / CSS 像素`。在 DPR=2 的屏上，1 个 CSS px = 2 个物理像素，于是 `border: 1px` 实际渲染为 2 物理像素，肉眼显得比预期「粗」；反过来若想画「1 物理像素」发丝线，用 `1px` 反而做不到。
- 视口关系：`<meta name="viewport" content="width=device-width, initial-scale=1">` 让 1 CSS px 对应 DPR 个设备像素；若 `initial-scale=1` 不变，DPR 越高逻辑像素越「密」，同一 CSS px 占的物理像素越多。
- 解决方案：
  - 伪元素 + `transform: scale`：用 `::after` 画 1px 边框，按 `scale(0.5)`（DPR=2）或 `scale(0.333)`（DPR=3）缩放为发丝线。
  - `border-image` / `background` 渐变：用 0.5px 渐变模拟单像素线。
  - 媒体查询按 DPR 切换：`@media (min-resolution: 2dppx)` 时启用缩放方案。
  - 现代方案：直接依赖 `0.5px` 边框在部分高分屏被识别为 1 物理像素（兼容性有限，需兜底）。

```css
.hairline {
  position: relative;
}
.hairline::after {
  content: "";
  position: absolute;
  left: 0; top: 0;
  width: 200%; height: 200%;
  border: 1px solid #ccc;
  transform: scale(0.5);
  transform-origin: 0 0;
  box-sizing: border-box;
  pointer-events: none;
}
@media (min-resolution: 3dppx) {
  .hairline::after { transform: scale(0.333); }
}
```

> 🎯 关键要点
> - 1px 变粗的本质是 DPR 把逻辑像素放大成多物理像素。
> - DPR = 物理像素 / CSS 像素，视口 meta 决定二者映射。
> - 伪元素 + `transform: scale` 是最稳的发丝线方案。
> - 应针对 DPR=2/3 分别缩放，并保留普通边框兜底。

> 🔍 追问
> - 为什么 `border-width: 0.5px` 在部分手机上仍是 1px？
> - `initial-scale=0.5` 缩放整页能否解决 1px 问题？代价是什么？

### 30. 如何用 prefers-reduced-motion 等媒体特性实现可降级的动效与无障碍适配？｜中级

核心结论：`prefers-reduced-motion` 让用户表达「减少动效」偏好，开发者应在 `reduce` 时关闭/简化装饰性动画，保留必要的状态变化；同类媒体特性还有 `prefers-color-scheme`/`prefers-contrast` 等。

- 机制：操作系统（Windows 动画设置、macOS 减弱动态效果、iOS 辅助功能）会把用户偏好暴露为媒体查询 `prefers-reduced-motion: reduce / no-preference`。
- 实践：默认用 `no-preference` 提供丰富动效；在 `reduce` 中把 `animation`/`transition` 设为 `none` 或极短，仅保留「信息性」的状态切换（如颜色变化），去掉位移、缩放、视差等易引发眩晕的效果。
- 相关无障碍媒体特性：`prefers-color-scheme`（深/浅色）、`prefers-contrast`（高对比）、`prefers-reduced-transparency`（减少透明）。
- 降级原则：动效是增强而非功能本身，关闭后页面须完全可用；不要全局 `*{animation:none}` 一刀切时破坏焦点提示等关键反馈。

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}
```

> 🎯 关键要点
> - 动效应尊重「减少动态效果」系统设置。
> - `reduce` 下禁用位移/缩放类眩晕动效，保留必要反馈。
> - 同类特性可一并做深/浅色、高对比适配。
> - 降级后页面必须仍完整可用，不能牺牲功能。

> 🔍 追问
> - 为什么 `reduce` 下仍要保留极短 transition 而非完全 none？
> - 如何用 JS 读取用户的 reduced-motion 偏好？

## 响应式设计（10 题）

### 31. 什么是响应式设计？它的核心原则是什么？｜初级

核心结论：响应式设计让同一套页面自适应不同屏幕尺寸与设备，核心是「移动优先 + 流式布局 + 弹性媒体 + 媒体查询」。

- 核心原则：
  1. 移动优先：先设计小屏，再逐步增强到大屏。
  2. 流式布局：用百分比/`fr` 等相对单位而非固定宽。
  3. 弹性图片：图片随容器缩放（`max-width:100%`）。
  4. 媒体查询：按断点切换布局与样式。
- 技术实现：viewport meta 标签 + `@media` + Flex/Grid + 相对单位（rem、vw、vh）。

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

> 🎯 关键要点
> - 响应式 ≠ 单纯缩放，而是「重构布局适配」。
> - 移动优先能控制 CSS 复杂度与加载成本。
> - viewport meta 是移动端响应式的前提。
> - 断点应由内容决定，而非死盯设备尺寸。

> 🔍 追问
> - 没有 viewport meta，移动端会如何渲染页面？
> - 为什么强调「内容决定断点」？

### 32. 如何设置CSS媒体查询？有哪些常见断点？｜中级

核心结论：媒体查询用 `@media` 按视口/特性应用样式；推荐「移动优先用 min-width」，断点跟着内容布局走而非设备型号。

- 语法：

```css
@media (min-width: 768px) { .container { max-width: 720px; } }
@media (min-width: 768px) and (max-width: 1024px) { /* 平板 */ }
```

- 常见断点（参考 Bootstrap 体系）：
  - `≤575px` 手机；`576–767px` 大手机/小平板；`768–991px` 平板；`992–1199px` 小桌面；`≥1200px` 大桌面。
- 最佳实践：移动优先（min-width 递增）、断点随内容、避免过多断点、别忘 `@media print` 打印样式。

> 🎯 关键要点
> - `min-width` 是移动优先的写法，`max-width` 是桌面优先。
> - 多条件用 `and` 连接，支持 `orientation`/`resolution` 等特性。
> - 断点应落在「布局开始难看」的位置，而非固定设备宽度。
> - 真实设备测试优于纯模拟器。

> 🔍 追问
> - `min-width` 与 `max-width` 在层叠顺序上如何叠加？
> - 如何用 `orientation: portrait` 区分横竖屏？

### 33. 如何实现响应式导航菜单？｜中级

核心结论：响应式导航的移动端用「汉堡菜单（默认隐藏、切换展开）」，桌面端展开为横排；可用纯 CSS（checkbox/`:checked`）或 JS 控制显隐。

- 基础切换：移动端 `.nav-menu { display:none }`，桌面端 `@media (min-width:768px)` 改 `display:flex` 横排；汉堡按钮反之。
- CSS-only：用隐藏 checkbox + `:checked ~ .nav-menu { max-height: ... }` 做无 JS 展开，过渡 `max-height`。
- 最佳实践：移动优先设计、触摸目标够大、当前页明确标识、避免依赖 hover（移动端无 hover）、多设备实测。

```css
.nav-menu { display: none; flex-direction: column; }
@media (min-width: 768px) {
  .nav-menu { display: flex; flex-direction: row; }
  .nav-toggle { display: none; }
}
/* 纯 CSS 展开 */
.nav-toggle:checked ~ .nav-menu { max-height: 300px; }
```

> 🎯 关键要点
> - 移动端菜单靠「显隐 + 展开」而非 hover。
> - 纯 CSS 方案可用 checkbox `:checked` 控制。
> - 触摸目标要够大，间距合理。
> - 桌面展开、移动折叠是主流模式。

> 🔍 追问
> - 纯 CSS 菜单用 `:checked` 有什么可访问性短板？
> - 为什么移动端要避免过度依赖 `:hover`？

### 34. 如何优化响应式图片加载？｜高级

核心结论：响应式图片优化 = 「正确尺寸图源 + 现代格式 + 懒加载 + CDN」，核心是 `srcset/sizes` 与 `<picture>` 按设备给图。

- HTML 手段：`srcset`（按 DPR 给多分辨率）+ `sizes`（声明显示宽度）+ `loading="lazy"` 懒加载。
- `<picture>` 进阶：按 `media` 给不同裁切，并优先 `type="image/webp"`/`avif`，`<img>` 兜底。
- 性能策略：采用 WebP/AVIF 等现代格式（体积显著小于 JPEG/PNG）；压缩工具处理；图片 CDN 动态优化；关键图预加载、非关键图懒加载；能用 SVG 的图标优先 SVG。

```html
<picture>
  <source media="(min-width: 1200px)" srcset="large.webp" type="image/webp">
  <source media="(min-width: 768px)" srcset="medium.webp" type="image/webp">
  <img src="small.jpg" alt="响应式图片" loading="lazy">
</picture>
```

> 🎯 关键要点
> - `srcset + sizes` 让浏览器按 DPR 选图，避免大图小用。
> - WebP/AVIF 通常比 JPG 小 25%–50%。
> - `loading="lazy"` 推迟屏外图片请求。
> - 图标类优先 SVG，矢量无损且体积小。

> 🔍 追问
> - AVIF 相比 WebP 的优势与兼容性现状？
> - `loading="lazy"` 对 LCP（最大内容绘制）有无负面影响？

### 35. 如何创建响应式表格？｜中级

核心结论：窄屏表格常用「横向滚动」「重排为卡片」两类思路；卡片式用 `data-label` + `::before` 把表头信息塞进每格。

- 横向滚动：外层 `overflow-x: auto`，表格 `min-width` 保宽，移动端可滚动查看。
- 重排为卡片：`@media (max-width:767px)` 把 `table/thead/tbody/tr/td` 全设 `display:block`，隐藏 `thead`，每格用 `td::before { content: attr(data-label) }` 显示字段名。
- 其他方法：移动端只显示关键列、行可展开看详情、分页/搜索减少数据量、必要时用图表替代表格。

```css
@media (max-width: 767px) {
  table, thead, tbody, th, td, tr { display: block; }
  thead { display: none; }
  td { position: relative; padding-left: 50%; }
  td::before { content: attr(data-label); position: absolute; left: 10px; font-weight: bold; }
}
```

> 🎯 关键要点
> - 简单表格用横向滚动最省事。
> - 卡片重排依赖 `data-label` 属性携带表头。
> - 隐藏 `thead` 后必须用 `::before` 补字段名，否则数据无上下文。
> - 超大数据用分页/搜索而非硬塞进小屏。

> 🔍 追问
> - 卡片重排后屏幕阅读器如何朗读表头与单元格的对应关系？
> - 何时应放弃表格改用图表？

### 36. 什么是移动优先设计？如何实现？｜中级

核心结论：移动优先是先为小屏设计与开发，再用 `min-width` 媒体查询逐步增强到大屏；它带来更好的性能、代码结构与 SEO。

- 核心原则：内容优先（小屏只放核心）、性能优先（移动端资源受限）、触摸友好（点击目标、手势）。
- 实现：基础样式面向移动端（小 padding、单列），`@media (min-width:768px)`、`(min-width:1024px)` 逐级增大间距与最大宽度。

```css
.container { padding: 1rem; max-width: 100%; }   /* 移动端基线 */
@media (min-width: 768px)  { .container { padding: 2rem; max-width: 720px; } }
@media (min-width: 1024px) { .container { padding: 3rem; max-width: 960px; } }
```

> 🎯 关键要点
> - 移动优先 = 先写小屏样式，大屏用 min-width 增强。
> - 与「桌面优先（max-width）」相比，CSS 更简洁、覆盖更少。
> - 优先加载核心内容与样式，性能更优。
> - 触摸交互（足够大的点击区）要提前考虑。

> 🔍 追问
> - 移动优先相比桌面优先在 CSS 体积上有何优势？
> - 移动优先如何影响图片与 JS 的资源策略？

### 37. 如何处理响应式设计中的字体大小？｜中级

核心结论：响应式字体以 `rem` 为基准、用媒体查询或 `clamp()` 做流式缩放，兼顾可读性与大屏不过大。

- 媒体查询法：根元素 `font-size` 随断点变化（如 16→18→20px），子元素用 `rem` 联动缩放。
- 流式法：`clamp(最小, 理想vw, 最大)` 让字号在视口间平滑过渡且有上下界；也可用 `calc(1.5rem + 2vw)`。
- 最佳实践：用 rem 便于整体缩放；行高 1.4–1.6 较舒适；移动端正文不小于 16px；限制最大字号避免大屏过大。

```css
html { font-size: 16px; }
@media (min-width: 1024px) { html { font-size: 20px; } }
h1 { font-size: clamp(2rem, 5vw, 4rem); }
```

> 🎯 关键要点
> - `rem` 让字号随根元素统一缩放。
> - `clamp()` 一次实现「流式 + 上下限」，比多断点更顺滑。
> - 正文别小于 16px，保证移动端可读。
> - 行高 1.4–1.6 是通用舒适区间。

> 🔍 追问
> - `clamp()` 的「理想值」用 vw 时，极端窄屏会怎样？
> - 为什么推荐用 rem 而非 em 控制全局字号？

### 38. 如何创建响应式布局网格系统？｜高级

核心结论：响应式网格可用 Flex 的 `flex-wrap + flex-basis` 或 Grid 的 `auto-fit/minmax`；Grid 的 `repeat(auto-fit, minmax())` 能零媒体查询自适应列数。

- Flexbox 网格：`display:flex; flex-wrap:wrap`，子项 `flex: 1 1 300px`，再用 `min-width` 断点调整每列基准。
- CSS Grid 自适应：`grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))`，容器变宽时自动增列，无需媒体查询；`auto-fill` 与 `auto-fit` 差异在于空轨道是否折叠。
- 自定义断点：用 CSS 变量 `--grid-columns` 配 `@media` 逐级设 1/2/3/4 列，兼容性与可控性最佳。

```css
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
/* 变量控制 */
.grid { --cols: 1; display: grid; grid-template-columns: repeat(var(--cols), 1fr); }
@media (min-width: 768px)  { .grid { --cols: 3; } }
```

> 🎯 关键要点
> - `auto-fit + minmax` 是无媒体查询自适应的首选。
> - `auto-fit` 折叠空轨道，`auto-fill` 保留空轨道占位。
> - Flex 网格用 `flex-basis` 控制最小列宽。
> - 变量 + 媒体查询适合需要精确控制列数的场景。

> 🔍 追问
> - `auto-fit` 与 `auto-fill` 在只有 1 个项目时表现有何不同？
> - 为什么 `minmax(300px, 1fr)` 比固定列数更稳？

### 39. 如何测试响应式设计？｜中级

核心结论：响应式测试应「开发者工具模拟 + 真机验证 + 清单核对」三结合，模拟器不能替代真实设备与触控。

- 浏览器工具：Chrome DevTools 设备模拟（Ctrl+Shift+M）、Firefox 响应式设计模式、Safari Develop 响应式模式。
- 真机测试：同 WiFi 局域网访问、Chrome Remote Debugging 远程调试、BrowserStack/Sauce Labs 云真机、物理手机/平板实测。
- 测试清单：各断点布局、字体可读性、图片缩放、交互（按钮/表单触控）、性能（加载与帧率）、可访问性（屏幕阅读器）。

> 🎯 关键要点
> - 模拟器只能验证布局，触控/手势必须真机。
> - 真机覆盖主流 iOS/Android 机型与系统版本。
> - 性能与可访问性是响应式验收的硬指标。
> - 云真机服务可弥补设备不足。

> 🔍 追问
> - 模拟器的 DPR 与真机是否完全一致？
> - 如何用 Lighthouse 在 CI 中做响应式性能门禁？

### 40. 如何优化响应式网站的性能？｜高级

核心结论：响应式性能优化覆盖「图片、CSS、JS」三线：图片用现代格式 + srcset + 懒加载，CSS 内联关键样式并异步非关键样式，JS 做代码分割与防抖节流。

- 图片优化：WebP/AVIF、`srcset/sizes`、`loading="lazy"`、压缩、CDN。
- CSS 优化：内联首屏关键 CSS（Critical CSS）、非关键 CSS 异步加载、压缩去重、用变量减体积。
- JS 优化：代码分割按需加载、非关键脚本延迟、`requestAnimationFrame` 批量 DOM 操作、计算密集任务移入 Web Worker、事件处理防抖/节流。

> 🎯 关键要点
> - Critical CSS 直出可消除首屏渲染阻塞。
> - 图片是响应式流量大头，优先级最高。
> - 防抖/节流避免滚动/缩放时高频回调卡顿。
> - Web Worker 把重计算移出主线程，保交互流畅。

> 🔍 追问
> - 如何抽取并内联 Critical CSS 而不阻塞构建？
> - 防抖与节流的适用场景分别是什么？

## 高级特性（10 题）

### 41. 什么是CSS预处理器？它们解决了什么问题？｜中级

核心结论：CSS 预处理器（Sass/Less/Stylus）通过变量、嵌套、mixin、函数扩展原生 CSS，解决重复代码与可维护性问题。

- 解决的问题：
  - 代码重复：变量与 mixin 复用样式片段。
  - 维护困难：模块化/分文件组织样式。
  - 功能有限：引入条件、循环、函数等编程能力。
- 常见方案：Sass/SCSS（功能最全，主流）、Less（接近 CSS 语法）、Stylus（语法灵活）。

```scss
$primary-color: #2196f3;
@mixin flex-center { display: flex; justify-content: center; align-items: center; }
.container { @include flex-center; color: $primary-color; }
```

> 🎯 关键要点
> - 预处理器在「构建期」编译为普通 CSS。
> - Sass 的嵌套会增加选择器特异性，需克制。
> - mixin 与函数减少重复，但滥用会膨胀产物。
> - 新项目也可考虑原生 CSS 变量 + @layer 替代部分能力。

> 🔍 追问
> - Sass 嵌套过深会带来什么副作用？
> - 原生 CSS 变量能否完全替代预处理器变量？

### 42. CSS-in-JS有哪些解决方案？各有什么优缺点？｜高级

核心结论：CSS-in-JS 把样式写进组件（Styled Components/Emotion/Stitches/CSS Modules），换来作用域隔离与动态样式，代价是运行时开销与调试成本。

- 主要方案：Styled Components（最流行）、Emotion（性能更好）、Stitches（零运行时）、CSS Modules（局部作用域、编译期）。
- 优点：样式作用域隔离避免全局冲突、支持基于 props 的动态样式、组件化、SSR 友好。
- 缺点：运行时性能开销（除零运行时方案）、调试较难（生成类名）、学习曲线、打包体积增大。

| 方案 | 运行时 | 动态样式 | 适用 |
| --- | --- | --- | --- |
| Styled Components | 有 | 强 | React 通用 |
| Emotion | 有（更轻） | 强 | 性能敏感 React |
| Stitches | 零运行时 | 强 | 性能优先 |
| CSS Modules | 编译期 | 弱 | 大型/框架无关 |

> 🎯 关键要点
> - 运行时方案有开销，零运行时（Stitches/CSS Modules）更轻。
> - 动态样式是 CSS-in-JS 最大卖点。
> - SSR 需注意样式提取与 FOUC。
> - 团队熟悉 CSS 时，CSS Modules + 预处理器也很稳。

> 🔍 追问
> - 零运行时 CSS-in-JS 如何实现「动态样式」？
> - CSS-in-JS 在 SSR 下易踩哪些坑？

### 43. 什么是CSS Houdini？它能做什么？｜高级

核心结论：CSS Houdini 是一组暴露 CSS 引擎底层能力的浏览器 API，让开发者用 JS 自定义绘制、布局、动画与属性，突破原生 CSS 的限制。

- 主要 API：
  - Paint API：自定义 `background`/`border` 等绘制（如棋盘格、波形）。
  - Layout API：自定义布局算法。
  - Animation Worklet：在独立线程跑自定义动画，不阻塞主线程。
  - Properties & Values API：用 `CSS.registerProperty` 注册带类型/默认值的自定义属性，使其可过渡/动画。
- 示例：注册 Paint Worklet 后 `background-image: paint(checkerboard)` 调用 JS 绘制。
- 现状：Chrome/Edge 支持较好，Firefox/Safari 覆盖不全；适合实验性特性与高性能绘制。

```js
CSS.paintWorklet.addModule('checkerboard.js');
// checkerboard.js
class CheckerboardPainter {
  paint(ctx, size) {
    const t = 20;
    for (let y = 0; y * t < size.height; y++)
      for (let x = 0; x * t < size.width; x++) {
        ctx.fillStyle = (x + y) % 2 ? 'white' : 'black';
        ctx.fillRect(x * t, y * t, t, t);
      }
  }
}
registerPaint('checkerboard', CheckerboardPainter);
```

> 🎯 关键要点
> - Houdini 把 CSS 引擎能力「开放」给 JS。
> - Properties & Values API 让自定义属性可动画。
> - Animation Worklet 在独立线程，利于流畅度。
> - 兼容性仍是落地的主要障碍，宜渐进增强。

> 🔍 追问
> - `CSS.registerProperty` 相比普通自定义属性多了什么能力？
> - 为什么 Houdini 的 Paint API 比纯 canvas 更适合做背景？

### 44. CSS容器查询（Container Queries）是什么？｜高级

核心结论：容器查询让组件依据「自身容器的尺寸」而非视口来响应，解决组件在不同布局上下文里「无法自适配」的痛点。

- 概念：传统媒体查询看视口，组件被塞进侧栏或主区时表现一样；容器查询看容器宽度，组件可因地制宜。
- 用法：父容器设 `container-type: inline-size`（或 `size`）+ 可选 `container-name`；子项用 `@container 名称 (min-width: ...)` 写查询。
- 价值：组件化响应式、复用性更强、减少媒体查询复杂度、利于设计系统与微前端。

```css
.card-container { container-type: inline-size; container-name: card; }
@container card (min-width: 400px) { .card { display: flex; flex-direction: row; } }
@container card (min-width: 800px) { .card { flex-direction: column; } }
```

> ⚠️ 注意
> `container-type: size` 会要求容器有确定尺寸，可能触发布局限制；多数场景用 `inline-size` 即可，开销更小。

> 🎯 关键要点
> - 容器查询的参照是「容器」而非「视口」。
> - `inline-size` 只测宽度，`size` 测宽高（限制更多）。
> - 与媒体查询互补：页面级用媒体查询，组件级用容器查询。
> - 现代 Chromium/Firefox/Safari 均支持，可放心使用。

> 🔍 追问
> - 容器查询与媒体查询能否混用？优先级如何？
> - `container-type: size` 为何会限制子元素影响父尺寸？

### 45. 什么是CSS层叠层（@layer）？如何使用？｜高级

核心结论：@layer 的工程价值在于「把第三方/工具类/组件样式分层管理、用声明顺序而非特异性控制优先级」，并要警惕「未分层样式优先级最高」这一常见坑。

- 用法：先声明层顺序 `@layer base, components, utilities`（靠右优先级更高），再分别填充各层；未写入任何层的普通样式优先级高于所有层。
- 工程落地：
  - 第三方库入「底层」：把组件库/reset（如 normalize）放进 `base`，让业务 `components` 天然覆盖它，无需 `!important`。
  - Tailwind 与自定义共存：把 Tailwind 的 `utilities`/`components` 作为层引入，自定义组件写在更高层或同样分层，避免工具类被意外压过。
  - 坑：未分层样式优先级最高——若你随手写了一条不带层的 `.btn { ... }`，它会盖过 `@layer components` 里的 `.btn`，造成「明明写了层却覆盖不掉」的错觉。
  - 迁移策略：新增样式优先放进合适的层；存量高特异性选择器可逐步用 `:where()` 降权或移入低层，再删 `!important`。
- 与 Q10 分工：Q10 讲层叠顺序与 `!important` 反转的原理，本题讲真实项目如何落地与避坑。

```css
@layer base, components, utilities;
@layer base { a { color: blue; } }        /* 第三方/reset 底层 */
@layer components { .btn { color: red; } }/* 业务组件层 */
/* 未分层：优先级最高，会盖过 components 里的 .btn */
.btn { color: green; }
```

> 🎯 关键要点
> - 层顺序「靠右更高」，用来替代堆特异性。
> - 未分层样式优先级最高，是常见覆盖失败根源。
> - 第三方库放底层，业务放高层，天然可覆盖。
> - 迁移靠 `:where()` 降权 + 分层，逐步清除 `!important`。

> 🔍 追问
> - 如何让一条未分层样式「降级」到某层之下？
> - Tailwind 的 `@layer` 与手写 `@layer` 冲突时如何共存？

### 46. 如何实现CSS中的深色模式？｜中级

核心结论：深色模式用 CSS 变量承载配色，靠 `prefers-color-scheme` 自动适配或手动切换 `class` 实现，关键是提供「尊重系统 + 可手动覆盖」双层机制。

- 变量法：在 `:root` 定义浅色变量，`@media (prefers-color-scheme: dark)` 下覆盖为深色变量，业务统一引用 `var()`。
- 类切换法：`:root.dark` 覆盖变量，JS `document.documentElement.classList.toggle('dark')` 切换，优先级高于媒体查询（用户手动意图优先）。
- 最佳实践：用变量集中管理、尊重系统偏好、提供手动开关、保证对比度达标（可访问性）、渐进增强先浅后深。

```css
:root { --bg: #fff; --text: #000; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #000; --text: #fff; }
}
:root.dark { --bg: #000; --text: #fff; }
body { background: var(--bg); color: var(--text); }
```

> 🎯 关键要点
> - 配色全部走变量，主题切换零改业务样式。
> - `prefers-color-scheme` 做自动，`class` 做手动且优先级更高。
> - 深色模式必须保证文本/背景对比度，避免低对比。
> - 图片/阴影在深色下也需重新评估可见性。

> 🔍 追问
> - 手动 `dark` class 与系统 `prefers-color-scheme` 谁的优先级高？
> - 深色模式下如何避免纯黑背景导致的眩光？

### 47. CSS滚动驱动动画（Scroll-driven Animations）是什么？｜高级

核心结论：滚动驱动动画让动画进度绑定「滚动位置/元素进入视口」，无需 JS 监听 scroll 事件，由浏览器合成线程驱动，性能更好。

- 两种时间线：
  - `scroll()`：动画进度跟随某滚动容器（默认根滚动条）的滚动量。
  - `view()`：进度跟随元素「进入/离开视口」的可见程度。
- 用法：`animation-timeline: scroll()` 或 `view()`，配合普通 `@keyframes`，可设 `animation-range` 限定起止区间。
- 价值：视差、滚动进度条、元素进入视口的淡入、替代 scroll 事件做性能友好的滚动动画。

```css
.element {
  animation: slide-in linear;
  animation-timeline: scroll();
}
@keyframes slide-in {
  from { transform: translateX(-100%); }
  to   { transform: translateX(0); }
}
.element { animation: fade-in linear both; animation-timeline: view(); }
```

> 🎯 关键要点
> - `scroll()` 看滚动量，`view()` 看元素进出视口。
> - 无需 JS scroll 监听，避免主线程抖动。
> - `animation-range` 可精确控制动画起止区间。
> - 兼容性以 Chromium 系为主，需为不支持的浏览器保留静止终态。

> 🔍 追问
> - `scroll()` 与 `view()` 的进度基准有何不同？
> - 不支持时如何保证内容仍可见（而非停在初始帧）？

### 48. 如何创建CSS中的玻璃态效果？｜中级

核心结论：玻璃态（Glassmorphism）靠半透明背景 + `backdrop-filter: blur()` 模糊底层内容实现，需保证对比度与性能。

- 基础实现：`background: rgba(255,255,255,0.2)` + `backdrop-filter: blur(10px)`（加 `-webkit-` 前缀兼容），配细边框与圆角。
- 深色玻璃态：背景改 `rgba(0,0,0,0.3)`、文字转白，效果更通透。
- 注意：`backdrop-filter` 有性能成本（需合成层）；需 `-webkit-` 前缀（Safari）；背后必须有内容才看得出模糊；务必保证文本对比度可访问。

```css
.glass {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
}
```

> ⚠️ 注意
> `backdrop-filter` 在部分浏览器/旧版本需 `-webkit-` 前缀；背后无内容时玻璃态「看不见模糊」，且大面积使用会拖慢合成。

> 🎯 关键要点
> - `backdrop-filter` 是玻璃态核心，模糊「元素背后」内容。
> - 半透明背景 + 细边框 + 圆角构成典型观感。
> - 必须有底层内容才显效。
> - 注意性能与对比度，导航栏/卡片/模态框最常用。

> 🔍 追问
> - `backdrop-filter` 与 `filter: blur` 作用于什么不同？
> - 为什么玻璃态在大面积使用时性能下降明显？

### 49. CSS子网格（Subgrid）是什么？｜高级

核心结论：Subgrid 让嵌套网格项「继承父网格的行列轨道」，解决卡片内部元素与父网格对齐的难题，无需重复定义轨道。

- 概念：子网格项设 `display: grid; grid-template-columns: subgrid`（行同理 `grid-template-rows: subgrid`），其轨道直接复用父网格的对应轨道。
- 用法：子项跨满父网格（`grid-column: 1 / -1`），内部再 `subgrid`，即可让标签、输入框等与父网格列严格对齐。
- 应用：表单标签/输入对齐、卡片内多块内容对齐、导航项对齐、设计系统统一栅格。

```css
.parent { display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 1rem; }
.child {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: subgrid;
  grid-template-rows: subgrid;
}
```

> 🎯 关键要点
> - subgrid 复用父轨道，避免「内外两套栅格对不齐」。
> - 子项需跨满目标区域（`1 / -1`）才能正确继承轨道。
> - 行与列都可单独 subgrid。
> - 现代浏览器（Chromium/Firefox/Safari 16+）已支持。

> 🔍 追问
> - subgrid 与「再定义一遍同样的 fr 轨道」为何不同？
> - 父网格改 gap 时，subgrid 子项如何响应？

### 50. 如何实现CSS中的视口单位（vw, vh, vmin, vmax）？｜中级

核心结论：视口单位相对浏览器视口尺寸，`vw/vh` 管宽高、`vmin/vmax` 取宽高较小/较大值，适合全屏与流式尺寸，但移动端 `100vh` 有坑。

- 语义：
  - `vw`：视口宽度的 1%。
  - `vh`：视口高度的 1%。
  - `vmin`：视口宽高较小值的 1%。
  - `vmax`：视口宽高较大值的 1%。
- 用法：全屏 `.hero { width:100vw; height:100vh }`、响应式 `h1 { font-size:5vw }`、正方形 `50vmin`、结合 `min(90vw, 1200px)` 限宽。

```css
.hero { width: 100vw; height: 100vh; }
.square { width: 50vmin; height: 50vmin; }
.container { width: min(90vw, 1200px); }
```

> ⚠️ 注意
> 移动端 `100vh` 常包含地址栏高度，导致全屏元素被地址栏裁切；可用 `100dvh`（动态视口高度）或 `svh/lvh` 解决。

> 🎯 关键要点
> - `vmin/vmax` 在横竖屏切换时自适应取极值。
> - `100vh` 移动端含地址栏，推荐 `100dvh`。
> - 与 `clamp()`/`min()` 配合做流式限宽很实用。
> - 字体用 vw 需设上下限，避免极端屏过大过小。

> 🔍 追问
> - `dvh/svh/lvh` 分别解决 100vh 的什么问题？
> - `vmin` 在横屏与竖屏下分别取宽度还是高度？

## HTML5（10 题）

### 51. HTML5新增了哪些语义化标签？｜初级

核心结论：HTML5 引入 `<header>/<nav>/<main>/<article>/<section>/<aside>/<footer>` 等语义标签，用含义代替无意义的 `<div>`，提升可访问性与 SEO。

- 主要语义标签：
  - `<header>` 页头、`<nav>` 导航、`<main>` 主要内容、`<article>` 独立文章、`<section>` 章节、`<aside>` 侧边栏、`<footer>` 页脚。
- 结构示例：`<header><nav>` 内，`<main>` 含 `<article><section>` 与 `<aside>`，最后 `<footer>`。
- 优势：屏幕阅读器更好理解结构、搜索引擎更易解析、代码更易维护、符合 Web 标准。

```html
<header><nav>导航菜单</nav></header>
<main>
  <article><section>文章内容</section></article>
  <aside>侧边栏</aside>
</main>
<footer>页脚信息</footer>
```

> 🎯 关键要点
> - 语义标签替代 `<div>`，让结构「自解释」。
> - `<main>` 一个页面最好只一个。
> - 语义化提升无障碍与 SEO。
> - 不要为样式滥用语义标签当 div 用。

> 🔍 追问
> - `<section>` 与 `<article>` 如何区分？
> - `<header>`/`<footer>` 能否出现在 `<article>` 内部？

### 52. HTML5的Canvas和SVG有什么区别？｜中级

核心结论：Canvas 是位图、靠 JS 逐帧绘制，适合游戏/图像；SVG 是矢量、是 DOM 节点，适合图标/图表且可交互。

- Canvas：基于像素的位图，缩放会失真；适合复杂动画、游戏、图像处理；大量元素时性能好；不支持单元素事件（要自己算坐标）。
- SVG：基于矢量的 DOM，缩放不失真；适合图标、图表；支持 DOM 操作与原生事件；文件通常更小（简单图）。
- 选择：游戏/复杂动画/图像用 Canvas；图标/图表/需缩放交互用 SVG；复杂图形用 Canvas、简单图标用 SVG。

| 维度 | Canvas | SVG |
| --- | --- | --- |
| 本质 | 位图（像素） | 矢量（DOM） |
| 缩放 | 失真 | 不失真 |
| 事件 | 需手动命中 | 原生事件 |
| 适用 | 游戏/影像 | 图标/图表 |

> 🎯 关键要点
> - Canvas 改一点要整块重绘，SVG 改节点局部更新。
> - SVG 可被 CSS/JS 直接控制，可访问性更好。
> - 元素极多时 Canvas 性能更优。
> - 二者可混合：背景 Canvas + 前景 SVG 图标。

> 🔍 追问
> - 为什么 Canvas 缩放会模糊而 SVG 不会？
> - 海量数据点可视化该选 Canvas 还是 SVG？

### 53. HTML5的表单新增了哪些输入类型？｜初级

核心结论：HTML5 新增了 `email/url/tel/number/range/date/time/color` 等输入类型，带来原生校验、合适键盘与更好体验。

- 新增类型：`email`、`url`、`tel`、`number`、`range`（滑块）、`date`、`time`、`datetime-local`、`month`、`week`、`color`、`search`。
- 优势：内置基础校验（如 email 格式）、移动端弹出合适虚拟键盘、原生日期/颜色选择器、语义更清晰、屏幕阅读器支持更好。

```html
<form>
  <input type="email" placeholder="email@example.com">
  <input type="url" placeholder="https://example.com">
  <input type="tel" placeholder="123-456-7890">
  <input type="number" min="0" max="100">
  <input type="date"> <input type="color">
</form>
```

> 🎯 关键要点
> - 类型带来原生校验，减少手写 JS。
> - `tel/email/url` 在移动端唤出对应键盘。
> - `date/time/color` 提供原生选择器。
> - 校验失败可用 `:invalid`/`:valid` 配合样式提示。

> 🔍 追问
> - `number` 与 `range` 在 UX 上怎么选？
> - 原生校验失败如何自定义提示文案？

### 54. 什么是HTML5的Web Storage API？｜中级

核心结论：Web Storage 提供 `localStorage`（持久）与 `sessionStorage`（会话）两种客户端键值存储，比 cookie 简单且容量更大，但仅存字符串、同步、有 XSS 风险。

- 两类：
  - `localStorage`：持久化，关闭浏览器仍保留，同源共享。
  - `sessionStorage`：会话级，关闭标签页即清，仅当前标签可用。
- API：`setItem/getItem/removeItem/clear`，值均为字符串，对象需 `JSON.stringify/parse`。
- 注意：容量通常 5–10MB；只存字符串、需 JSON 转换；勿存敏感信息（同源 JS 可读，XSS 可窃取）；同步操作大量读写可能阻塞；现代浏览器均支持。

```js
localStorage.setItem('username', 'John');
const username = localStorage.getItem('username');
localStorage.removeItem('username');
sessionStorage.setItem('token', 'abc123');
```

> ⚠️ 注意
> Web Storage 是同步 API，存大对象会阻塞主线程；且任何同源 XSS 都能读取，敏感 token 请勿明文存放，必要时用 httpOnly Cookie。

> 🎯 关键要点
> - localStorage 持久、sessionStorage 会话级。
> - 仅字符串，复杂数据需 JSON 序列化。
> - 容量约 5–10MB，远大于 cookie。
> - 勿存密码/令牌，避免 XSS 泄露。

> 🔍 追问
> - localStorage 与 sessionStorage 的生命周期与作用域差异？
> - 为什么敏感信息不适合放 localStorage？

### 55. HTML5的Web Workers是什么？如何使用？｜高级

核心结论：Web Workers 在后台线程运行 JS，不阻塞主线程（UI），适合排序、图像处理、加密等计算密集任务；但不能直接操作 DOM。

- 机制：主线程 `new Worker('worker.js')` 创建线程，通过 `postMessage` 发、`onmessage` 收；Worker 内用 `self.onmessage` 处理。
- 限制：Worker 中无 `document`/`window`（部分 API 受限），不能直接操作 DOM，需把结果回传主线程渲染。
- 场景：大数据排序/过滤、图像滤镜/压缩、加密解密、物理模拟、实时数据分析。

```js
// 主线程
const worker = new Worker('worker.js');
worker.postMessage({ data: largeArray });
worker.onmessage = e => console.log('结果:', e.data);
// worker.js
self.onmessage = e => { self.postMessage(processLargeData(e.data)); };
```

> 🎯 关键要点
> - Worker 跑在独立线程，保主线程交互流畅。
> - 无法直接访问 DOM，只能算、不能画。
> - 通信靠结构化克隆（postMessage），大对象有拷贝成本。
> - SharedArrayBuffer 可零拷贝共享，但需特定跨域头。

> 🔍 追问
> - Worker 为何不能直接操作 DOM？如何把计算结果呈现到页面？
> - `postMessage` 传大数组的性能隐患与解法？

### 56. 什么是HTML5的地理位置API？｜中级

核心结论：Geolocation API 通过 `navigator.geolocation` 获取用户经纬度，必须用户授权，常用于定位、路线、附近服务。

- 用法：`getCurrentPosition(success, error, options)` 取一次位置；`watchPosition` 持续监听；`clearWatch` 停止。
- 选项：`enableHighAccuracy`（高精度，耗电）、`timeout`（超时毫秒）、`maximumAge`（可复用缓存的时长）。
- 注意：必须用户授权；涉及隐私勿滥用；注意错误处理（拒绝/超时/不可用）；移动端支持更好。

```js
navigator.geolocation.getCurrentPosition(
  pos => console.log(pos.coords.latitude, pos.coords.longitude),
  err => console.error(err.message),
  { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
);
```

> 🎯 关键要点
> - 取位置前必须获得用户明确授权。
> - `watchPosition` 适合导航类持续定位，记得 `clearWatch`。
> - 高精度模式更耗电，按需开启。
> - 务必处理拒绝/失败，避免静默卡死。

> 🔍 追问
> - `maximumAge` 设为 0 意味着什么？
> - 后台持续定位在移动端有哪些限制？

### 57. HTML5的WebSocket是什么？与HTTP有何区别？｜高级

核心结论：WebSocket 是基于单条 TCP 连接的全双工协议，连接建立后服务端可主动推送；HTTP 是请求-响应、无状态、默认不由服务端推送。

- 差异对比：
  - HTTP：请求-响应模式、无状态、每次通信需建/复用连接、服务端不主动推。
  - WebSocket：全双工、有状态长连接、握手后持续打开、支持服务端主动推送。
- 握手：WebSocket 借一次 HTTP 升级（Upgrade 头）建立，之后走独立帧协议，开销远低于反复 HTTP 轮询。
- 场景：实时聊天、多人在线游戏、股票/比分推送、协作编辑、IoT 设备通信。

```js
const ws = new WebSocket('wss://example.com/socket');
ws.onmessage = e => console.log(e.data);
ws.send(JSON.stringify({ type: 'ping' }));
```

> 🎯 关键要点
> - WebSocket 是「长连接 + 双向」，HTTP 是「一来一回」。
> - 建立靠一次 HTTP Upgrade 握手。
> - 服务端可主动推，省去轮询开销。
> - 生产用 `wss://`（加密），并自行处理重连与心跳。

> 🔍 追问
> - WebSocket 握手为何要借 HTTP Upgrade？
> - 相比 HTTP 长轮询（long-polling），WebSocket 省在哪？

### 58. 什么是HTML5的Service Worker？｜高级

核心结论：Service Worker 是运行在浏览器后台的脚本，能拦截网络请求、缓存资源，实现离线访问、推送与后台同步，是 PWA 的核心。

- 能力：拦截 fetch、缓存静态资源实现离线、接收推送通知、后台同步数据。
- 生命周期：注册 → `install`（预缓存资源到 Cache Storage）→ `activate`（清理旧缓存）→ `fetch`（决定走缓存还是网络）。
- 注意：需在 HTTPS（localhost 除外）下运行；作用域受注册路径限制；更新需新 SW 接管并 `skipWaiting`/`clients.claim`。

```js
// 注册
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');
// sw.js
self.addEventListener('install', e => {
  e.waitUntil(caches.open('v1').then(c => c.addAll(['/', '/index.html', '/styles.css'])));
});
self.addEventListener('fetch', e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
```

> 🎯 关键要点
> - Service Worker 是 PWA 离线能力的基石。
> - 缓存策略常见「缓存优先 / 网络优先 /  stale-while-revalidate」。
> - 必须 HTTPS（本地 localhost 豁免）。
> - 更新逻辑易踩坑，注意 activate 阶段清理旧缓存。

> 🔍 追问
> - `stale-while-revalidate` 策略如何兼顾速度与新鲜？
> - 为什么 Service Worker 更新有时「不生效」需刷新两次？

### 59. HTML5的Web Components是什么？｜高级

核心结论：Web Components 是浏览器原生的组件化方案，由 Custom Elements + Shadow DOM + HTML Templates 组成，样式与逻辑封装、跨框架复用。

- 三大支柱：
  - Custom Elements：用 `customElements.define` 注册自定义标签（如 `<my-component>`）。
  - Shadow DOM：为组件创建隔离的 DOM 与样式作用域，外部样式不渗入、内部样式不外泄。
  - HTML Templates：`<template>`/`<slot>` 提供可复用的标记与内容分发。
- 优势：强封装、可跨框架（React/Vue/原生皆可）、浏览器原生、无运行时框架依赖。

```js
class MyComponent extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `<style>p{color:red}</style><p>Hello World</p>`;
  }
}
customElements.define('my-component', MyComponent);
```

> 🎯 关键要点
> - Shadow DOM 提供「样式隔离」，解决全局污染。
> - Custom Elements 让标签语义化、可复用。
> - 与框架无关，适合设计系统/组件库。
> - `mode: 'open'` 才允许外部访问 shadowRoot。

> 🔍 追问
> - Shadow DOM 的样式隔离为何有利于设计系统？
> - `<slot>` 在 Web Components 中解决什么问题？

### 60. 如何优化HTML页面的加载性能？｜中级

核心结论：HTML 加载性能优化贯穿「语义结构、资源加载、关键路径」三线：减少阻塞、预加载关键资源、压缩与缓存并行。

- HTML 结构：用正确语义标签、减少无意义 DOM 嵌套、合理拆分内容。
- 资源加载：脚本用 `async`（不依赖顺序）或 `defer`（保序、DOM 后执行）；关键 CSS 内联、非关键 CSS 异步；图片用现代格式 + 懒加载；字体子集化并 `preload`。
- 网络与构建：Gzip/Brotli 压缩、CDN 加速、合理缓存头、代码分割按需加载；用 Lighthouse 持续度量。

```html
<link rel="preload" href="critical.css" as="style">
<script src="app.js" defer></script>
<img src="hero.avif" loading="lazy" alt="">
```

> 🎯 关键要点
> - `defer` 保序且不在解析期阻塞，`async` 不保序。
> - 关键 CSS 内联可消除首屏渲染阻塞。
> - `preload` 提前获取关键资源，但勿滥用以免争抢带宽。
> - 压缩（Brotli）+ CDN + 缓存头是通用三板斧。

> 🔍 追问
> - `async` 与 `defer` 在 DOM 解析期的行为差异？
> - 字体 `preload` 为何还要 `font-display: swap` 配合？
