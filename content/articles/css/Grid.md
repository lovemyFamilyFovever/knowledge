---
tags: [CSS, 布局]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/css/Grid.md"
---

## CSS Grid 布局完全指南

CSS Grid 是强大的二维布局系统，可以同时控制行和列。以下是核心用法和实战示例：

## 1️⃣ 基础概念


```css
.container {
    display: grid;              /* 块级网格 */
    display: inline-grid;      /* 行内级网格 */
}
```

CSS Grid 布局是一个非常强大的二维布局系统，可以同时控制行和列。它的属性主要分为两部分：**作用于父容器（网格容器）的属性** 和 **作用于子项（网格项）的属性**。

下面为你梳理最核心和实用的属性清单。

## 2️⃣ 属性说明

### 一、父容器属性（定义网格结构）

这些属性写在 `display: grid;` 的容器上。

| 属性 | 说明 | 常用值示例 |
| :--- | :--- | :--- |
| **`grid-template-columns`** | 定义列宽和数量 | `100px 1fr 200px` (固定、剩余、固定)<br>`repeat(3, 1fr)` (三等分)<br>`auto` (内容宽度) |
| **`grid-template-rows`** | 定义行高 | `auto 200px` (第一行靠内容，第二行固定)<br>`repeat(4, 100px)` (四行固定高) |
| **`gap`** (或 `grid-gap`) | 设置行列间距的简写 | `20px` (行列间距都是20px)<br>`10px 20px` (行间距10px，列间距20px) |
| **`justify-items`** | 水平对齐单元格内的内容 | `start`, `end`, `center`, `stretch`(默认拉伸) |
| **`align-items`** | 垂直对齐单元格内的内容 | `start`, `end`, `center`, `stretch` |
| **`place-items`** | `align-items` 和 `justify-items` 的简写 | `center center` (水平和垂直都居中) |
| **`justify-content`** | 当网格总宽度小于容器时，整体水平对齐 | `start`, `end`, `center`, `space-between`, `space-around` |
| **`align-content`** | 当网格总高度小于容器时，整体垂直对齐 | 同上，也支持 `space-evenly` |
| **`place-content`** | `align-content` 和 `justify-content` 的简写 | `center space-between` |
| **`grid-auto-rows`** | 设置隐式创建的行（超出定义行数的行）的高度 | `minmax(100px, auto)` (最小100px，最大自动) |
| **`grid-auto-columns`** | 设置隐式创建的列的宽度 | 使用频率较低，逻辑同上 |
| **`grid-auto-flow`** | 控制自动布局的排列方向 | `row`(默认行排列), `column`, `dense`(紧密填充) |

### 二、子项属性（定位单个项目）

这些属性写在网格项目的样式上。

| 属性 | 说明 | 常用值示例 |
| :--- | :--- | :--- |
| **`grid-column-start`**<br>`grid-column-end` | 定义项目从哪条列线开始/结束 | `1` (第一条列线) / `3` (第三条列线) |
| **`grid-column`** | 上面两个的简写 | `1 / 3` (从第1条列线跨越到第3条，即占2列) |
| **`grid-row-start`**<br>`grid-row-end` | 定义项目从哪条行线开始/结束 | `2 / 4` (占两行) |
| **`grid-row`** | 上面两个的简写 | `span 2` (占两行，不指定起始线) |
| **`justify-self`** | 只针对单个项目，水平对齐 | `start`, `end`, `center`, `stretch` |
| **`align-self`** | 只针对单个项目，垂直对齐 | `start`, `end`, `center`, `stretch` |
| **`place-self`** | 上面两个的简写 | `center stretch` |

### 三、必须记住的几个关键概念和值

1.  **`fr` 单位**：`fr` (fraction) 是 Grid 特有的单位，代表剩余空间的比例。例如 `1fr 2fr` 表示按 1:2 分配剩余宽度。
2.  **`repeat()`**：简化重复代码。`repeat(3, 1fr)` 等价于 `1fr 1fr 1fr`。
3.  **`minmax()`**：定义最小和最大尺寸。`minmax(100px, auto)` 表示最小100px，最大可随内容撑开。
4.  **`auto`**：非常灵活，常表示“由内容决定”。
5.  **隐式网格**：当你定义了 `grid-template-columns: 1fr 1fr;` (两列)，却放了4个项目，多出来的行就会按照 `grid-auto-rows` 的规则自适应高度。

## 3️⃣ 实战示例

### 📱 示例1：响应式卡片布局

```html
<div class="card-grid">
    <div class="card">卡片 1</div>
    <div class="card">卡片 2</div>
    <div class="card">卡片 3</div>
    <div class="card">卡片 4</div>
    <div class="card">卡片 5</div>
    <div class="card">卡片 6</div>
</div>
```

```css
.card-grid {
    display: grid;
    gap: 20px;
    padding: 20px;
    
    /* 响应式：最小250px，自动填充 */
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
}

.card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 40px 20px;
    border-radius: 12px;
    color: white;
    text-align: center;
    transition: transform 0.3s;
}

.card:hover {
    transform: translateY(-5px);
}
```

### 📐 示例2：经典博客布局

```html
<div class="blog-layout">
    <header class="header">头部</header>
    <nav class="sidebar">侧边栏导航</nav>
    <main class="content">主要内容区域</main>
    <aside class="ad">广告栏</aside>
    <footer class="footer">底部</footer>
</div>
```

```css
.blog-layout {
    display: grid;
    gap: 20px;
    padding: 20px;
    
    /* 定义区域名称 */
    grid-template-areas:
        "header header header"
        "sidebar content ad"
        "footer footer footer";
    
    /* 列宽：侧边栏200px，内容自适应，广告150px */
    grid-template-columns: 200px 1fr 150px;
    
    /* 行高：自动，自适应，自动 */
    grid-template-rows: auto 1fr auto;
    
    min-height: 100vh;
}

.header {
    grid-area: header;
    background: #3b82f6;
    padding: 20px;
}

.sidebar {
    grid-area: sidebar;
    background: #10b981;
    padding: 20px;
}

.content {
    grid-area: content;
    background: #f59e0b;
    padding: 20px;
}

.ad {
    grid-area: ad;
    background: #ef4444;
    padding: 20px;
}

.footer {
    grid-area: footer;
    background: #8b5cf6;
    padding: 20px;
}

/* 移动端适配 */
@media (max-width: 768px) {
    .blog-layout {
        grid-template-areas:
            "header"
            "sidebar"
            "content"
            "ad"
            "footer";
        grid-template-columns: 1fr;
    }
}
```

### 🎨 示例3：瀑布流相册

```html
<div class="gallery">
    <div class="gallery-item tall">高图 1</div>
    <div class="gallery-item wide">宽图 1</div>
    <div class="gallery-item">普通图</div>
    <div class="gallery-item tall">高图 2</div>
    <div class="gallery-item wide">宽图 2</div>
    <div class="gallery-item">普通图</div>
</div>
```

```css
.gallery {
    display: grid;
    gap: 16px;
    padding: 20px;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    grid-auto-rows: 200px;
    grid-auto-flow: dense;  /* 紧凑填充 */
}

.gallery-item {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
}

/* 跨行 */
.tall {
    grid-row: span 2;
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

/* 跨列 */
.wide {
    grid-column: span 2;
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}
```

### 📊 示例4：仪表盘布局

```html
<div class="dashboard">
    <div class="stat-card">访问量: 10,000</div>
    <div class="stat-card">用户数: 5,000</div>
    <div class="stat-card">收入: ¥50,000</div>
    <div class="chart-large">图表区域</div>
    <div class="chart-small">小图表1</div>
    <div class="chart-small">小图表2</div>
    <div class="table">数据表格</div>
</div>
```

```css
.dashboard {
    display: grid;
    gap: 20px;
    padding: 20px;
    background: #f3f4f6;
    min-height: 100vh;
    
    grid-template-columns: repeat(4, 1fr);
    grid-auto-rows: auto;
}

.stat-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.chart-large {
    grid-column: span 2;
    grid-row: span 2;
    background: white;
    border-radius: 12px;
    padding: 20px;
}

.chart-small {
    background: white;
    border-radius: 12px;
    padding: 20px;
}

.table {
    grid-column: span 4;
    background: white;
    border-radius: 12px;
    padding: 20px;
}

@media (max-width: 1024px) {
    .dashboard {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .chart-large {
        grid-column: span 2;
    }
    
    .table {
        grid-column: span 2;
    }
}

@media (max-width: 640px) {
    .dashboard {
        grid-template-columns: 1fr;
    }
    
    .chart-large,
    .table {
        grid-column: span 1;
    }
}
```

## 5️⃣ 对齐方式

```css
/* 水平对齐 (justify) */
.grid {
    justify-items: start | end | center | stretch;
    justify-content: start | end | center | space-between | space-around | space-evenly;
}

/* 垂直对齐 (align) */
.grid {
    align-items: start | end | center | stretch;
    align-content: start | end | center | space-between | space-around | space-evenly;
}

/* 简写 place-items: align justify */
.grid {
    place-items: center center;  /* 水平和垂直都居中 */
}
```

## 6️⃣ 自动放置

```css
.grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-auto-rows: 100px;           /* 自动行高 */
    grid-auto-flow: row dense;       /* 自动放置策略 */
}
```

## 7️⃣ 子元素定位

```css
/* 基于网格线编号（从1开始） */
.item {
    grid-column: 1 / 3;    /* 从第1列线到第3列线（占2列） */
    grid-row: 2 / 4;       /* 从第2行线到第4行线（占2行） */
}

/* 使用 span 关键字 */
.item {
    grid-column: span 2;    /* 占2列 */
    grid-row: span 3;       /* 占3行 */
}

/* 基于区域名称 */
.item {
    grid-area: header;      /* 对应 grid-template-areas 中的名称 */
}
```

## 🎯 快速参考

| 场景 | 推荐写法 |
|------|---------|
| 响应式卡片 | `grid-template-columns: repeat(auto-fill, minmax(250px, 1fr))` |
| 圣杯布局 | 使用 `grid-template-areas` |
| 固定侧边栏 | `grid-template-columns: 250px 1fr` |
| 等宽列 | `grid-template-columns: repeat(4, 1fr)` |
| 混合布局 | `grid-template-columns: 200px 1fr 300px` |

Grid 和 Flex 配合使用效果最佳：外层用 Grid 控制大框架，内部用 Flex 处理细节对齐。