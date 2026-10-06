---
title: "CSS 布局（Flexbox 与 Grid）"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# CSS 布局（Flexbox 与 Grid）

> 📌 **导航**：本文是 **CSS 布局（Flexbox 与 Grid）** 词条，属于 frontend-concepts 术语集。相关枢纽：[[HTML & CSS 核心概念]]、[[前端框架核心概念]]。

## 定义

**一句话定义：** Flexbox 是一维弹性布局系统，控制一行（或一列）内子元素的排列、对齐与空间分配；Grid 是二维网格布局系统，行列同时控制——两者合起来取代 float，是现代 CSS 的两套布局方案。

**通俗类比：** Flexbox 像排队：决定横排还是竖排（flex-direction）、人与人之间距（gap）、整列队伍在场地的位置（justify-content）；Grid 像排签到表格：可以精确指定每个单元格占几列跨几行，甚至让一个元素霸占多个格子。

## 为什么需要它

传统 float 布局繁琐且全靠 hack。Flexbox 用一套简洁属性解决居中、等分与自适应排列；Grid 解决仪表盘、圣杯布局这类二维结构——它们在 Flexbox 与 float 下需要大量额外代码。

## 核心机制

- **Flex 容器**：`display: flex` 起手，`flex-direction` 定主轴方向，`justify-content: space-between` 管主轴对齐，`align-items: center` 管交叉轴对齐，`flex-wrap: wrap` 允许换行，`gap` 管子元素间距；子项 `flex: 1` 按比例分配剩余空间。
- **Grid 容器**：`display: grid` 配 `grid-template-columns: 1fr 2fr 1fr` 定义三列比例 1:2:1，`gap: 20px` 给行列间距；子项 `grid-column: 1 / -1` 横跨所有列，`grid-area: 2 / 1 / 4 / 2` 按行/列起始与结束落位。

| 维度 | Flexbox | Grid |
|---|---|---|
| 管理范围 | 一行或一列（一维） | 行与列同时（二维） |
| 对齐抓手 | 主轴 justify-content + 交叉轴 align-items | 轨道定义 + 子项落位 |
| 典型场景 | 组件内部排列 | 页面骨架、仪表盘、圣杯 |
| 换行/断轨 | flex-wrap 自动换行 | 显式轨道，子项跨行跨列 |

## 具体示例

```css
.page { display: grid; grid-template-columns: 200px 1fr; gap: 20px; }
.header { grid-column: 1 / -1; }          /* 横跨所有列 */
.toolbar { display: flex; align-items: center;
           justify-content: space-between; gap: 16px; }
.item { flex: 1; }                        /* 按比例分剩余空间 */
```

## 何时用与何时不用

- **用**：组件内部一维排列用 Flexbox；页面级二维骨架用 Grid；组合是常态——Grid 铺骨架、Flex 填组件。
- **不用**：纯文本流不必硬套网格；新项目无需退回 float 布局。

## 优劣与代价

✅ 一套属性解决居中、等分、换行，hack 代码大幅减少。
✅ fr 比例单位与 gap 让"比例 + 间距"成为一等公民，适配成本下降。
⚠️ 属性面大，主轴/交叉轴易混，flex-direction 一变 justify/align 语义跟着换。
⚠️ Grid 命名区域与行号线嵌套写深后可读性差，长项目宜收敛成模板。

## 与相关概念的区别

- **vs [[响应式设计]]**：响应式是策略/理念，媒体查询是实现手段，Flex/Grid 是布局工具，三层不混。
- **vs float 布局**：float 的本意是文字环绕，拿它排版属滥用且要处理清除。
- **vs [[CSS 盒模型与 BFC 与层叠上下文]]**：盒模型决定单个盒子多大，本篇决定多个盒子怎么排。

## 常见误区

- 把 Flexbox 与 Grid 当互斥的二选一，选型时不问布局维度。
- 写完 justify-content: center 就疑惑垂直方向为何不居中——它管主轴，交叉轴要用 align-items。

## 面试速答

> 🎯 Flexbox 一维：主轴 justify-content、交叉轴 align-items、子项 flex:1 分剩余空间；Grid 二维：grid-template 定轨道、子项跨行跨列。骨架用 Grid、组件内用 Flex，组合而非二选一。

## 相关术语

[[HTML & CSS 核心概念]]、[[响应式设计]]、[[CSS 盒模型与 BFC 与层叠上下文]]、[[CSS渲染性能]]、[[前端框架核心概念]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇承接原《HTML & CSS 核心概念》Flexbox 布局与 CSS Grid 布局两节的定义、示例与对比；原稿无截断。
