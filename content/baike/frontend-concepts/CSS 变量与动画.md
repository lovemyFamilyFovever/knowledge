---
title: "CSS 变量与动画"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# CSS 变量与动画

> 📌 **导航**：本文是 **CSS 变量与动画** 词条，属于 frontend-concepts 术语集。相关枢纽：[[HTML & CSS 核心概念]]、[[前端框架核心概念]]。

## 定义

**一句话定义：** CSS 变量（自定义属性）在样式表里定义可复用的值、任何地方用 var() 引用、改一处全局生效且运行时可被 JS 修改；动画由 transition 承担两态过渡、@keyframes 加 animation 承担多阶段自动播放——两者把静态样式表变成可编程的表现层。

**通俗类比：** 变量像给颜色起名字，以后直接叫 --primary，换主题只改名册；transition 是翻页动画——鼠标移过去颜色慢慢变；animation 是一段按剧本（keyframes）自动循环播放的动画片。

## 为什么需要它

变量解决 CSS 里"魔法数字"泛滥的问题：主题、间距、圆角一处定义全局引用，顺带实现主题切换并让 JS 能动态改样式；动画让界面变化平滑自然、引导用户注意力，而不是瞬间切换。

## 核心机制

- **变量**：`:root { --primary: #1890ff; --radius: 8px }` 声明，`var(--primary)` 引用，`var(--card-padding, 20px)` 带兜底默认值；属性沿继承与层联向下生效，在 `[data-theme="dark"]` 上重定义即可完成暗色主题。与 Sass 变量的本质区别：CSS 变量是浏览器原生、运行时生效、可被 JS 修改；Sass 变量编译时处理、打包后不复存在。
- **transition**：声明属性、时长与缓动（`transition: background 0.3s ease, transform 0.2s`），只能从 A→B 两个状态间过渡，由状态变化触发。
- **animation**：`@keyframes` 写 from/to 或多阶段百分关键帧，`animation: 名称 1.5s infinite` 自动循环，`forwards` 保持结束态；无需状态触发即可播放，这是与 transition 的分界线。
- **性能底线**：动效优先 transform 与 opacity——直达合成层、跳过重排重绘，机理见 [[CSS渲染性能]]。

## 具体示例

```css
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.05); }
}
.loading { animation: pulse 1.5s infinite; }
[data-theme="dark"] { --primary: #177ddc; }
```

## 何时用与何时不用

- **用**：设计令牌、主题切换、JS 联动样式用变量；hover 变色与位移微调用 transition；加载指示、入场等自动播放的多阶段动效用 animation。
- **不用**：不必把一切常量都包成变量——几处局部数值直接写更直观；高频动画别拿 width/top 等触发布局的属性做（掉帧），换 transform。

## 优劣与代价

✅ 一处定义全局生效，设计规格从"复制色值"变成"引用名字"。
✅ 动效是 CSS 原生能力，零 JS 开销，实现交互反馈成本低。
⚠️ 变量没有编译期校验，写错名字静默回退兜底值或整条失效。
⚠️ transition 只答两态、animation 要手排关键帧，复杂编排的声明式能力有限。

## 与相关概念的区别

- **vs CSS 预处理器变量**：编译时文本替换 vs 运行时层叠属性，前者不能随 DOM 状态重算，后者可以（暗色主题即例证）。
- **vs [[CSS 选择器与伪类伪元素]]**：选择器裁决哪条规则命中谁，本篇管命中之后用什么值、值怎么变。
- **vs [[响应式设计]]**：变量按 data 属性等运行时条件切换表现，媒体查询按视口切换布局，都是"运行时分支"。

## 常见误区

- 把 CSS 变量当成 Sass 变量换了个名字，以为打包后都不存在。
- 让容器"渐渐变宽"就写 width 过渡，掉帧后怀疑是设备太差。

## 面试速答

> 🎯 CSS 变量：自定义属性运行时生效、var() 引用可带兜底、JS 可改，与 Sass 编译期变量划清界限，主题切换靠它；动效：transition 两态、animation+keyframes 多阶段可循环，优先 transform/opacity 走合成层。

## 相关术语

[[HTML & CSS 核心概念]]、[[CSS渲染性能]]、[[CSS 选择器与伪类伪元素]]、[[CSS 布局（Flexbox 与 Grid）]]、[[响应式设计]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇合并原《HTML & CSS 核心概念》的 CSS 变量（自定义属性）与 CSS 动画（transition / animation / keyframes）两节，暗色主题与 pulse 关键帧示例压缩自原稿；原稿无截断。
