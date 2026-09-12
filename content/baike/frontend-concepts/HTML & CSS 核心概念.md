---
title: "HTML & CSS 核心概念"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# HTML & CSS 核心概念


> 📌 **导航**：本文是 **HTML & CSS 核心概念** 词条，属于 frontend-concepts 术语集。相关枢纽：[[HTML & CSS 核心概念]]、[[JavaScript 基础核心概念]]、[[React深入]]、[[Vue3核心]]、[[前端工程化核心概念]]。

---

## HTML语义化标签

**一句话定义**：用有意义的标签名来描述内容的结构和含义，而不是全用 `div`。

**通俗类比**：就像写文章用标题、段落、列表来组织内容，而不是全部挤在一个大段落里。语义化标签让浏览器、搜索引擎和辅助工具都能"读懂"你的页面。

**具体示例**：
```html
<header>
  <nav>
    <a href="/">首页</a>
    <a href="/about">关于</a>
  </nav>
</header>

<main>
  <article>
    <h1>文章标题</h1>
    <section>
      <p>文章内容...</p>
    </section>
  </article>
  <aside>侧边栏</aside>
</main>

<footer>
  <p>版权信息</p>
</footer>
```

**为什么需要它**：搜索引擎（SEO）能更好理解页面结构；屏幕阅读器能为视障用户提供导航；代码可读性大幅提升，维护更轻松。

**与相关术语的对比和区分**：语义化标签 vs 无语义标签（div/span）。div 是通用容器，没有含义；语义化标签自带含义，能传达内容的角色和重要性。

---

## CSS 盒模型

**一句话定义**：每个 HTML 元素都被看作一个"盒子"，由 content、padding、border、margin 四层组成。

**通俗类比**：想象一个快递包裹——content 是里面的商品，padding 是防震泡沫，border 是纸箱外壳，margin 是包裹和其他物品之间的距离。

**具体示例**：
```css
.box {
  content: 内容区域;
  padding: 20px;      /* 内边距：内容到边框的距离 */
  border: 2px solid;   /* 边框 */
  margin: 10px;        /* 外边距：与其他元素的距离 */
}
```

**为什么需要它**：理解盒模型才能精确控制元素的尺寸和间距，避免布局"错位"的经典问题。

**与相关术语的对比和区分**：标准盒模型（`content-box`）的 width 只包含 content；IE 盒模型（`border-box`）的 width 包含 content + padding + border。

---

## box-sizing

**一句话定义**：控制 CSS 宽高的计算方式，是只算内容区，还是包含 padding 和 border。

**通俗类比**：标准模式下你说"我要 100cm 的箱子"指的是内部空间；border-box 模式下你说"100cm"是指整个箱子的外部尺寸。

**具体示例**：
```css
/* 推荐全局设置 */
*, *::before, *::after {
  box-sizing: border-box;
}

.element {
  width: 200px;
  padding: 20px;
  border: 5px solid;
  /* border-box: 总宽200px，内容区自动缩为150px */
  /* content-box: 总宽250px，内容区仍是200px */
}
```

**为什么需要它**：使用 `border-box` 后，设置 width 就是最终占用宽度，无需手动计算 padding 和 border，布局心算负担大幅降低。

**与相关术语的对比和区分**：`content-box`（默认）vs `border-box`，区别在于 width 的计算范围。

---

## Flexbox 布局

**一句话定义**：一种一维弹性布局方案，让容器内的子元素能灵活地排列、对齐和分配空间。

**通俗类比**：像排队时，你可以决定队伍是横排还是竖排（flex-direction），人与人之间的间距（gap），以及队伍整体在场地中的位置（justify-content）。

**具体示例**：
```css
.container {
  display: flex;
  flex-direction: row;          /* 主轴方向：横向 */
  justify-content: space-between; /* 主轴对齐：两端对齐 */
  align-items: center;           /* 交叉轴对齐：垂直居中 */
  flex-wrap: wrap;               /* 换行：允许换行 */
  gap: 16px;                     /* 子元素间距 */
}

.item {
  flex: 1; /* 按比例分配剩余空间 */
}
```

**为什么需要它**：传统 float 布局繁琐且有各种 hack，Flexbox 用一套简洁属性解决了居中、等分布局、自适应排列等常见需求。

**与相关术语的对比和区分**：Flexbox 是一维布局（一行或一列），Grid 是二维布局（行列同时控制）。Flexbox 适合组件内部排列，Grid 适合页面整体布局。

---

## CSS Grid 布局

**一句话定义**：二维网格布局系统，能同时控制行和列，是 CSS 中最强大的布局方案。

**通俗类比**：像设计一个表格，你可以精确指定每个单元格占几列、跨几行，甚至让一个元素"霸占"多个格子。

**具体示例**：
```css
.grid {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr; /* 三列：比例1:2:1 */
  grid-template-rows: auto;
  gap: 20px;
}

.header {
  grid-column: 1 / -1; /* 横跨所有列 */
}

.sidebar {
  grid-area: 2 / 1 / 4 / 2; /* 行/列起始 行/列结束 */
}
```

**为什么需要它**：Grid 能轻松实现复杂的二维布局（如仪表盘、圣杯布局），而 Flexbox 和 float 在这类场景下需要大量额外代码。

**与相关术语的对比和区分**：Grid 是二维（行列），Flexbox 是一维（一行/一列）。实际项目中常组合使用：Grid 做页面骨架，Flex 做组件内部排列。

---

## 响应式设计

**一句话定义**：让网页在手机、平板、桌面等不同屏幕尺寸下都能正常显示。

**通俗类比**：像水一样，倒入不同形状的容器就呈现不同形状——手机上竖排显示，平板上双列，桌面上多列。

**具体示例**：
```css
/* 移动优先：默认写手机样式 */
.container {
  padding: 16px;
}

/* 平板及以上 */
@media (min-width: 768px) {
  .container {
    padding: 24px;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}

/* 桌面 */
@media (min-width: 1200px) {
  .container {
    grid-template-columns: 1fr 1fr 1fr;
  }
}
```

**为什么需要它**：移动互联网时代，用户可能从任何设备访问你的网站，响应式设计确保所有人都有良好的体验。

**与相关术语的对比和区分**：响应式设计是策略/理念，媒体查询是实现手段，Flexbox/Grid 是布局工具。

---

## BFC（块级格式化上下文）

**一句话定义**：一个独立的渲染区域，内部元素的布局不影响外部，外部也不影响内部。

**通俗类比**：像一个独立房间，房间里的家具怎么摆放不影响隔壁房间，隔壁房间的装修也不会改变你房间的格局。

**具体示例**：
```css
/* 触发 BFC 的方式 */
.container {
  overflow: hidden;    /* 常用 */
  /* 或 display: flow-root; 推荐 */
  /* 或 float: left; */
  /* 或 position: absolute; */
}

/* 解决外边距塌陷 */
.parent {
  display: flow-root;
}
.child {
  margin-top: 20px; /* 不会穿透到父元素 */
}
```

**为什么需要它**：解决经典问题——父元素高度塌陷（子元素浮动后父元素高度为 0）、外边距塌陷（margin 重叠）。

**与相关术语的对比和区分**：BFC 是概念机制，不是属性。理解 BFC 才能理解"为什么浮动会造成塌陷"以及"为什么 overflow:hidden 能修复它"。

---

## CSS 选择器优先级

**一句话定义**：当多条规则作用于同一元素时，浏览器按优先级决定应用哪条规则。

**通俗类比**：像公司里的汇报关系——直属经理（类选择器）的指令优先于公司公告（标签选择器），但 CEO（!important）可以直接拍板。

**具体示例**：
```css
/* 优先级从低到高 */
p { }                    /* 0,0,1 - 标签 */
.intro { }               /* 0,1,0 - 类 */
#main { }                /* 1,0,0 - ID */
div.intro { }            /* 0,1,1 - 标签+类 */
#main .intro { }         /* 1,1,0 - ID+类 */
[style] { }              /* 0,1,0 - 属性选择器 ≈ 类 */
p:not(.intro) { }        /* 0,1,1 - 伪类 */

/* 最高优先级（慎用） */
p.important { color: red !important; }

/* 计算规则：(ID数量, 类数量, 标签数量) */
```

**为什么需要它**：避免"为什么我的样式没生效"的灵魂拷问，精准控制样式的应用。

**与相关术语的对比和区分**：优先级 vs 特异性（Specificity）。两者本质相同，特异性是优先级的数值化表达。优先级还受源码顺序影响（相同优先级后写的覆盖先写的）。

---

## 伪类与伪元素

**一句话定义**：伪类选择元素的特殊状态，伪元素创建不存在于 DOM 中的虚拟元素。

**通俗类比**：伪类像给人贴标签——"鼠标悬停的按钮"、"正在输入的输入框"；伪元素像给元素"画"出额外部分——"首字母放大"、"内容前加图标"。

**具体示例**：
```css
/* 伪类：选择状态 */
a:hover { color: red; }          /* 鼠标悬停 */
a:visited { color: gray; }       /* 已访问 */
input:focus { border-color: blue; } /* 获得焦点 */
li:first-child { font-weight: bold; } /* 第一个子元素 */
li:nth-child(odd) { background: #f5f5f5; } /* 奇数行 */

/* 伪元素：创建虚拟元素 */
p::first-letter { font-size: 2em; }  /* 首字母 */
p::before { content: "📌 "; }       /* 内容前插入 */
p::after { content: " (完)"; }      /* 内容后插入 */
::selection { background: yellow; }  /* 选中文本 */
```

**为什么需要它**：无需添加额外 HTML 标签就能实现交互效果和装饰效果，保持 HTML 的整洁。

**与相关术语的对比和区分**：伪类用单冒号 `:`（:hover），伪元素用双冒号 `::`（::before）。现代浏览器两者都兼容，但规范上建议伪元素用双冒号。

---

## CSS 变量（自定义属性）

**一句话定义**：在 CSS 中定义可复用的值，任何地方都能引用，修改一处全局生效。

**通俗类比**：像给颜色起了个名字，比如 `--primary-color`，以后要用这个颜色直接叫名字，想换颜色改定义就行。

**具体示例**：
```css
:root {
  --primary: #1890ff;
  --spacing-md: 16px;
  --radius: 8px;
  --shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.button {
  background: var(--primary);
  padding: var(--spacing-md);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

/* 带默认值 */
.card {
  padding: var(--card-padding, 20px);
}

/* 暗色主题 */
[data-theme="dark"] {
  --primary: #177ddc;
}
```

**为什么需要它**：解决了 CSS 中"魔法数字"泛滥的问题，实现主题切换、统一设计规范，也让 JS 能动态修改样式。

**与相关术语的对比和区分**：CSS 变量 vs Sass 变量。CSS 变量是浏览器原生支持，运行时生效，可被 JS 修改；Sass 变量是编译时处理，打包后不存在。

---

## CSS 动画（transition / animation / keyframes）

**一句话定义**：让 CSS 属性值的变化带有过渡或动画效果，而非瞬间切换。

**通俗类比**：transition 像翻页动画——鼠标移过去颜色慢慢变；animation 像一段自动播放的动画片——按设定的剧本（keyframes）循环播放。

**具体示例**：
```css
/* transition：简单的状态过渡 */
.button {
  background: #1890ff;
  transition: background 0.3s ease, transform 0.2s;
}
.button:hover {
  background: #40a9ff;
  transform: translateY(-2px);
}

/* animation + keyframes：复杂动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card {
  animation: fadeInUp 0.6s ease-out forwards;
}

/* 多阶段动画 */
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.loading {
  animation: pulse 1.5s infinite;
}
```

**为什么需要它**：提升用户体验，让界面变化更平滑自然，引导用户注意力。

**与相关术语的对比和区分**：transition 只能从 A→B（两个状态），animation 可以定义多个关键帧（A→B→C→...），且能自动循环。

---

## 层叠上下文（Stacking Context）

**一句话定义**：决定多个重叠元素谁在上谁在下的"层级规则体系"。

**通俗类比**：像 Photoshop 的图层——普通图层按顺序叠放，但一旦创建了图层组，组内的图层顺序就只在组内生效，不会影响组外。

**具体示例**：
```css
/* 创建层叠上下文 */
.parent {
  position: relative;
  z-index: 1; /* 创建新的层叠上下文 */
}

/* 层叠顺序（从低到高）：
   1. 层叠上下文背景和边框
   2. z-index 为负值
   3. 块级盒（文档流内）
   4. 浮动盒
   5. 内联盒（行内元素）
   6. z-index: 0 / auto
   7. z-index 为正值
*/

.child {
  position: absolute;
  z-index: 9999; /* 再大也出不了 parent 的层叠上下文 */
}
```

**为什么需要它**：解决"为什么 z-index 设了 9999 还是被遮住"的问题——因为父级的层叠上下文限制了子级的层级范围。

**与相关术语的对比和区分**：z-index 只在同一层叠上下文内比较。不同层叠上下文之间的比较，要看上下文本身的层级，而非子元素的 z-index。

## 相关术语

[[JavaScript 基础核心概念]]、[[React深入]]、[[Vue3核心]]、[[前端工程化]]、[[前端工程化核心概念]]、[[前端框架核心概念]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
