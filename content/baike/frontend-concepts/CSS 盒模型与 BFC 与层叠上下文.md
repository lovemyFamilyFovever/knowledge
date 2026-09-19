---
title: "CSS 盒模型与 BFC 与层叠上下文"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# CSS 盒模型与 BFC 与层叠上下文

> 📌 **导航**：本文是 **CSS 盒模型与 BFC 与层叠上下文** 词条，属于 frontend-concepts 术语集。相关枢纽：[[HTML & CSS 核心概念]]、[[前端框架核心概念]]。

## 定义

**一句话定义：** 盒模型把每个元素定义为 content、padding、border、margin 四层，box-sizing 决定 width 的计算范围；BFC 是内部布局与外界互不影响的独立渲染区域；层叠上下文规定重叠元素谁上谁下——三者承接"盒子"的尺寸、布局隔离与层级三问。

**通俗类比：** 盒模型像快递包裹：商品是 content、防震泡沫是 padding、纸箱外壳是 border、与其他物品的间距是 margin；BFC 像一个独立房间，屋里家具怎么摆不影响隔壁；层叠上下文像 Photoshop 的图层组——组内的层序只能在组内争。

## 为什么需要它

不懂盒子与层级，调布局只能瞎试 hack：为什么浮动后父元素高度变 0、为什么相邻 margin 重叠穿透、为什么 z-index 设了 9999 还被遮住——三个经典问题的因果都在这里。

## 核心机制

- **盒的四层与算法**：content → padding → border → margin。`content-box`（默认）的 width 只算内容区；`border-box` 的 width 含 content + padding + border——`width: 200px` 配 `padding: 20px`、`border: 5px`，前者总宽 250px，后者总宽仍是 200px、内容区自动缩为 150px。全局 `*, *::before, *::after { box-sizing: border-box }` 是推荐起手式，设 width 即最终占位。
- **BFC 是机制不是属性**：`overflow: hidden` 常用，`display: flow-root` 更推荐（无裁剪副作用），`float` 或 `position: absolute` 也会创建。它解决两类经典问题：子元素浮动后的父元素高度塌陷、外边距塌陷（margin 重叠穿透父级）。
- **层叠上下文**：`position` 非 static 配整数 `z-index` 即新建；上下文内部从低到高依次为：背景与边框 → 负 z-index → 块级盒 → 浮动盒 → 内联盒 → z-index 0/auto → 正值。z-index 只在同一上下文内比较，子元素再大也出不了父级。

## 具体示例

弹窗被后文内容遮住：排查发现其父级已因 `position: relative; z-index: 1` 创建了层叠上下文，弹窗的 9999 只能在本组内争。修复是把弹层节点移出受限父级，或提升父级自身层级，而不是继续加大数字。

## 何时用与何时不用

- **用**：尺寸心算不对先看 box-sizing；塌陷找 BFC；"谁盖谁"找层叠上下文。
- **不用**：别用 overflow: hidden 强行造 BFC——它会连投影与下拉层一起裁掉，flow-root 更礼貌；也不要为"预防"给每个容器都建层叠上下文。

## 优劣与代价

✅ border-box 让 width 即最终占位宽度，布局心算负担大幅降低。
✅ BFC 与层叠上下文把诡异布局变成可推导的因果，修复动作可预期。
⚠️ content-box 仍是默认值，跨项目协作要显式声明全局规则才生效。
⚠️ 层叠上下文建得过多，z-index 数字互相压不住，最终还得梳理层级结构。

## 与相关概念的区别

- **vs [[CSS 布局（Flexbox 与 Grid）]]**：布局管盒子怎么排，本篇管单个盒子怎么量尺寸、怎么分层级。
- **vs [[CSS渲染性能]]**：层叠上下文决定渲染结果里谁盖谁，合成层决定一帧要重算多少，属管线不同环节。
- **vs [[CSS 选择器与伪类伪元素]]**：伪元素生成的也是盒，一样参与盒模型与层叠。

## 常见误区

- 把"z-index 越大越靠上"当普适真理，忽略父级层叠上下文的封顶。
- 设了 width 就以为总宽等于 width，忘了 content-box 下 padding 与 border 也参与计算。

## 面试速答

> 🎯 盒模型四层 content/padding/border/margin，border-box 让 width 含内边距与边框；BFC 是隔离布局的独立渲染区，治高度与 margin 塌陷；层叠上下文圈定 z-index 的比较范围，9999 出不了父级组。

## 相关术语

[[HTML & CSS 核心概念]]、[[CSS 布局（Flexbox 与 Grid）]]、[[CSS渲染性能]]、[[CSS 选择器与伪类伪元素]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇合并原《HTML & CSS 核心概念》的 CSS 盒模型、box-sizing、BFC（块级格式化上下文）与层叠上下文四节，逐条定义与 CSS 示例按 v1.2 §8.1 收敛为机制与散文；原稿无截断。
