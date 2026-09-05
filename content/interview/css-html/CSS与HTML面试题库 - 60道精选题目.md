---
title: "CSS与HTML面试题库 - 60道精选题目"
tags: []
source: "baike"
source_path: "技术题库 / CSS与HTML"
collected: "2026-09-05"
status: "imported"
---

CSS与HTML面试题库 - 60道精选题目
🎨 CSS与HTML面试题库
60道精选题目 - 从基础到高级的全面覆盖
📚 60道题目
🎯 详细解答
💡 实战技巧
📱 响应式设计
📦 CSS基础
📐 布局技巧
✨ 动画效果
📱 响应式设计
🚀 高级特性
🏷️ HTML5
📦 CSS基础
1. CSS选择器的优先级是如何计算的？
简单
CSS选择器
优先级
基础概念
查看答案
回答模板1：基础解释
CSS选择器的优先级计算遵循以下规则：
1.
!important
具有最高优先级
2. 内联样式（style属性）优先级为 1,0,0,0
3. ID选择器（#id）优先级为 0,1,0,0
4. 类选择器（.class）、属性选择器、伪类优先级为 0,0,1,0
5. 元素选择器、伪元素优先级为 0,0,0,1
6. 通配符选择器（*）优先级为 0,0,0,0
回答模板2：实战应用
在实际开发中，我建议：
• 避免过度使用
!important
，因为它会破坏CSS的自然级联
• 使用BEM命名规范来避免选择器冲突
• 当需要覆盖第三方样式时，可以使用更高优先级的选择器
• 使用开发者工具查看元素的计算样式和应用的CSS规则
回答模板3：问题解决
当遇到样式不生效的问题时，我会：
1. 检查选择器优先级是否足够
2. 查看是否有其他样式规则覆盖了目标样式
3. 使用浏览器开发者工具的"Computed"面板查看最终应用的样式
4. 检查CSS规则是否被浏览器解析（语法错误可能导致规则失效）
2. 请解释盒模型（Box Model）是什么？
简单
盒模型
基础概念
布局
查看答案
回答模板1：概念解释
CSS盒模型描述了元素在页面中占据的空间，由四个部分组成：
•
Content（内容）
：元素的实际内容，如文本、图片等
•
Padding（内边距）
：内容与边框之间的空间
•
Border（边框）
：围绕内边距的边框
•
Margin（外边距）
：元素与其他元素之间的空间
回答模板2：两种盒模型
CSS有两种盒模型：
1.
标准盒模型（content-box）
：元素的width/height只包含内容区域，不包含padding和border
2.
IE盒模型（border-box）
：元素的width/height包含内容、padding和border
使用
box-sizing: border-box
可以切换到IE盒模型，这在响应式设计中非常有用。
回答模板3：实际应用
在实际项目中，我通常：
• 在全局CSS中设置
* { box-sizing: border-box; }
• 使用CSS变量统一管理间距和尺寸
• 利用Flexbox和Grid布局简化盒模型的计算
• 在响应式设计中，注意不同设备上的盒模型表现
3. CSS单位有哪些？它们各自适用什么场景？
简单
CSS单位
响应式
布局
查看答案
回答模板1：基础单位介绍
CSS中有多种单位，主要分为：
•
绝对单位
：px, cm, mm, in等（不推荐在响应式中使用）
•
相对单位
：em, rem, %, vw, vh等
•
特殊单位
：ch, ex, fr等
回答模板2：使用场景
px
：适用于需要精确控制的场景，如边框、阴影
em
：相对于父元素字体大小，适用于组件内间距
rem
：相对于根元素字体大小，适用于全局布局
%
：相对于父元素，适用于响应式宽度
vw/vh
：相对于视口尺寸，适用于全屏布局
回答模板3：最佳实践
我的单位使用原则：
1. 全局使用
rem
作为基础单位，便于统一缩放
2. 响应式布局使用
vw/vh
或
%
3. 需要精确控制时使用
px
4. 组件内部使用
em
保持相对性
5. 避免混合使用多种单位造成混乱
📦 CSS基础（续）
4. 请解释CSS继承的概念和规则
中等
CSS继承
级联
基础概念
查看答案
回答模板1：概念解释
CSS继承是指某些CSS属性会从父元素传递给子元素的特性。继承的属性包括：
• 字体相关：font-family, font-size, color等
• 文本相关：text-align, line-height, letter-spacing等
• 列表相关：list-style-type, list-style-position等
回答模板2：继承规则
继承遵循以下规则：
1.
自然继承
：如上所述的属性会自动继承
2.
强制继承
：使用
inherit
关键字强制继承父元素的值
3.
初始值
：使用
initial
关键字重置为默认值
4.
取消继承
：使用
unset
关键字
回答模板3：实际应用
在实际开发中，我这样处理继承：
• 在
body
上设置全局字体和颜色，利用继承减少重复代码
• 使用CSS变量（自定义属性）实现更灵活的继承
• 注意继承的级联顺序，避免意外的样式覆盖
• 使用开发者工具查看元素的继承链
5. 什么是CSS层叠（Cascade）？它如何影响样式应用？
中等
CSS层叠
级联
优先级
查看答案
回答模板1：基础概念
CSS层叠是指浏览器如何确定多个CSS规则应用于同一元素时的最终样式。层叠规则包括：
1.
来源
：用户样式 < 浏览器样式 < 开发者样式 < !important
2.
优先级
：按照选择器优先级计算
3.
顺序
：相同优先级时，后定义的规则覆盖先定义的
回答模板2：层叠算法
浏览器应用层叠算法的步骤：
1. 收集所有匹配元素的CSS规则
2. 按来源和优先级排序
3. 按特殊性排序
4. 按源顺序排序（后定义的优先）
5. 应用最终计算出的样式
回答模板3：实际影响
层叠机制对开发的影响：
• 可以利用层叠特性进行样式覆盖和主题切换
• 需要理解优先级计算，避免使用过多
!important
• 使用CSS预处理器可以更好地管理层叠关系
• 在大型项目中，需要建立清晰的CSS架构来管理层叠
6. 请解释CSS伪类和伪元素的区别和用法
中等
伪类
伪元素
选择器
查看答案
回答模板1：概念区分
伪类
：用于选择处于特定状态的元素，如
:hover
,
:focus
,
:active
伪元素
：用于创建不存在于DOM中的虚拟元素，如
::before
,
::after
,
::first-line
回答模板2：常用示例
常用伪类
：
•
:hover
- 鼠标悬停状态
•
:focus
- 元素获得焦点
•
:nth-child(n)
- 选择第n个子元素
•
:not(selector)
- 排除特定选择器
常用伪元素
：
•
::before
- 在元素内容前插入内容
•
::after
- 在元素内容后插入内容
•
::first-letter
- 选择首字母
回答模板3：实际应用
在实际项目中：
• 使用伪类实现交互效果，如悬停、聚焦状态
• 使用伪元素添加装饰性内容，如图标、分隔线
• 注意伪元素需要
content
属性才能显示
• 合理使用伪类和伪元素可以减少HTML和JavaScript的复杂度
7. 如何实现水平垂直居中？请列举至少5种方法
中等
居中
布局
Flexbox
Grid
查看答案
回答模板1：传统方法
1.
文本居中
：
text-align: center
（水平）+
line-height
（垂直）
2.
绝对定位
：
position: absolute
+
top: 50%
+
transform: translateY(-50%)
3.
表格布局
：
display: table-cell
+
vertical-align: middle
回答模板2：现代方法
4.
Flexbox
：父容器设置
display: flex
+
justify-content: center
+
align-items: center
5.
Grid
：父容器设置
display: grid
+
place-items: center
6.
Grid简化
：
display: grid
+
place-content: center
回答模板3：选择建议
我的选择原则：
• 简单文本居中：使用
text-align
• 已知尺寸的元素：使用绝对定位 + transform
• 不确定尺寸的元素：使用Flexbox或Grid
• 兼容性要求高的项目：使用传统方法
• 现代项目：优先使用Flexbox或Grid
8. 什么是CSS特异性（Specificity）？如何计算？
中等
CSS特异性
优先级
选择器
查看答案
回答模板1：概念解释
CSS特异性是浏览器决定哪个CSS规则应用于元素的权重计算方法。特异性值以四位数表示：
•
行内样式
：1,0,0,0
•
ID选择器
：0,1,0,0
•
类选择器
：0,0,1,0
•
元素选择器
：0,0,0,1
回答模板2：计算规则
特异性计算规则：
1. 从左到右比较每一位的值
2. 较高特异性的选择器优先
3. 相同特异性时，后定义的规则优先
4.
!important
具有最高优先级
5. 继承的样式特异性为0
回答模板3：实际应用
在实际开发中：
• 避免使用行内样式，保持关注点分离
• 使用BEM命名规范，避免ID选择器的高特异性
• 当需要覆盖第三方样式时，可以使用更高特异性的选择器
• 使用CSS预处理器时，注意嵌套选择器会增加特异性
9. CSS变量（自定义属性）有哪些优势？
中等
CSS变量
自定义属性
现代CSS
查看答案
回答模板1：基础优势
CSS变量（自定义属性）的主要优势：
1.
可重用性
：定义一次，多处使用
2.
可维护性
：修改一处即可全局更新
3.
动态性
：可以在JavaScript中动态修改
4.
作用域
：支持变量作用域和继承
回答模板2：使用示例
:root {
    --primary-color: #2196f3;
    --spacing-unit: 8px;
}

.button {
    background: var(--primary-color);
    padding: var(--spacing-unit) calc(var(--spacing-unit) * 2);
}

/* 动态修改 */
:root.dark-theme {
    --primary-color: #9c27b0;
}
回答模板3：实际应用
我在项目中使用CSS变量：
• 定义设计系统的基础值（颜色、间距、字体）
• 实现主题切换功能
• 创建响应式断点系统
• 与JavaScript结合实现动态样式
• 在组件库中保持一致性
10. 请解释CSS层叠层（@layer）的作用
困难
@layer
CSS层叠层
现代CSS
查看答案
回答模板1：概念解释
CSS层叠层（
@layer
）是一种新的CSS特性，用于控制样式的层叠顺序。它允许开发者创建多个样式层，并显式控制这些层的优先级。
回答模板2：使用方式
/* 声明层叠层顺序 */
@layer base, components, utilities;

/* 定义层 */
@layer base {
    body { font-family: sans-serif; }
}

@layer components {
    .button { background: blue; }
}

@layer utilities {
    .hidden { display: none; }
}
回答模板3：实际优势
层叠层解决了CSS的哪些问题：
1.
第三方样式冲突
：可以控制第三方库样式的优先级
2.
大型项目管理
：为不同类型的样式建立清晰的优先级
3.
工具类框架
：如Tailwind CSS可以更好地与自定义样式共存
4.
主题系统
：更容易实现主题切换和样式覆盖
📐 布局技巧
11. Flexbox布局的核心概念是什么？
简单
Flexbox
布局
现代CSS
查看答案
回答模板1：基础概念
Flexbox是一种一维布局模型，主要用于在容器中对齐和分布空间。核心概念包括：
•
主轴（Main Axis）
：默认水平方向
•
交叉轴（Cross Axis）
：默认垂直方向
•
容器（Container）
：设置
display: flex
的元素
•
项目（Item）
：容器的直接子元素
回答模板2：常用属性
容器属性
：
•
flex-direction
：主轴方向
•
justify-content
：主轴对齐
•
align-items
：交叉轴对齐
•
flex-wrap
：换行控制
项目属性
：
•
flex-grow
：放大比例
•
flex-shrink
：缩小比例
•
flex-basis
：基础大小
回答模板3：使用场景
Flexbox最适合的场景：
• 导航栏布局
• 卡片列表布局
• 表单元素对齐
• 不确定高度的垂直居中
• 等分布局
12. CSS Grid布局与Flexbox有何区别？
中等
Grid
Flexbox
布局对比
查看答案
回答模板1：核心区别
Flexbox
：一维布局，适用于行或列的布局
Grid
：二维布局，适用于行和列的复杂布局
回答模板2：使用场景
Flexbox更适合
：
• 导航栏、工具栏
• 卡片列表
• 表单元素对齐
• 不确定高度的布局
Grid更适合
：
• 整体页面布局
• 复杂的网格布局
• 需要精确控制行列的布局
• 响应式网格系统
回答模板3：选择原则
我的选择原则：
1. 如果只需要控制一个维度（行或列），使用Flexbox
2. 如果需要同时控制行和列，使用Grid
3. 如果布局比较复杂，通常Grid更简单
4. 两者可以结合使用，Grid用于整体布局，Flexbox用于组件内部
13. 如何实现多列等高布局？
中等
等高布局
Flexbox
Grid
查看答案
回答模板1：Flexbox方法
.container {
    display: flex;
}

.column {
    flex: 1; /* 等分空间 */
}
回答模板2：Grid方法
.container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
}

.column {
    /* Grid自动等高 */
}
回答模板3：传统方法
传统方法（不推荐）：
1.
padding-bottom + negative margin
：通过设置很大的padding-bottom和等大的负margin-bottom
2.
table布局
：使用
display: table
和
display: table-cell
3.
JavaScript计算
：动态计算并设置高度
现代项目中，推荐使用Flexbox或Grid，它们原生支持等高布局。
14. 请解释CSS的overflow属性及其值
简单
overflow
布局
滚动
查看答案
回答模板1：属性介绍
overflow属性控制内容溢出容器时的处理方式：
•
visible
：默认值，内容溢出容器边界显示
•
hidden
：隐藏溢出内容
•
scroll
：始终显示滚动条
•
auto
：需要时显示滚动条
回答模板2：使用场景
visible
：不需要隐藏内容时
hidden
：裁剪溢出内容，如卡片内容截断
scroll
：需要始终显示滚动条的场景
auto
：内容可能溢出也可能不溢出的场景
clip
：类似hidden，但不允许程序性滚动
回答模板3：最佳实践
使用overflow的注意事项：
1. 避免在body上设置overflow: hidden，可能影响滚动
2. 使用overflow: auto时，注意滚动条的空间
3. 结合text-overflow实现文本截断
4. 在响应式设计中，注意不同设备上的表现
15. 如何实现圣杯布局和双飞翼布局？
困难
圣杯布局
双飞翼布局
经典布局
查看答案
回答模板1：圣杯布局
.container {
    padding: 0 200px;
}

.left, .right {
    position: absolute;
    width: 200px;
    height: 100%;
}

.left { left: 0; }
.right { right: 0; }
.center { margin: 0 200px; }
回答模板2：双飞翼布局
.container {
    float: left;
    width: 100%;
}

.main {
    margin: 0 200px;
    height: 200px;
}

.left, .right {
    float: left;
    width: 200px;
    height: 200px;
}

.left { margin-left: -100%; }
.right { margin-left: -200px; }
回答模板3：现代方法
现代CSS推荐使用Flexbox或Grid实现类似布局：
/* Flexbox实现 */
.container {
    display: flex;
}

.main { flex: 1; }
.left, .right { width: 200px; }

/* Grid实现 */
.container {
    display: grid;
    grid-template-columns: 200px 1fr 200px;
}
现代方法更简洁，兼容性更好，推荐在新项目中使用。
16. 什么是BFC（块格式化上下文）？如何触发？
困难
BFC
格式化上下文
布局
查看答案
回答模板1：概念解释
BFC（Block Formatting Context）是CSS中的一个独立渲染区域，它决定了元素如何对其内部内容进行定位，以及与其他元素的关系。
回答模板2：触发条件
以下情况会创建BFC：
• 根元素（
<html>
）
• 浮动元素（
float
不为 none）
• 绝对定位元素（
position
为 absolute 或 fixed）
• 行内块元素（
display: inline-block
）
• 表格元素（
display: table-cell
,
table-caption
）
•
overflow
不为 visible 的元素
•
display: flow-root
回答模板3：实际应用
BFC的实际应用：
1.
清除浮动
：父元素触发BFC可以包含浮动子元素
2.
防止margin重叠
：相邻BFC之间的margin不会重叠
3.
阻止元素被浮动元素覆盖
：BFC区域不会与浮动元素重叠
4.
包含浮动元素
：解决父元素高度塌陷问题
17. 如何实现文本截断（单行和多行）？
中等
文本截断
溢出处理
响应式
查看答案
回答模板1：单行截断
.text-truncate {
    width: 200px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
回答模板2：多行截断
.text-truncate-lines {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3; /* 显示3行 */
    overflow: hidden;
    text-overflow: ellipsis;
}
回答模板3：注意事项
使用文本截断的注意事项：
1. 必须设置容器宽度
2. 单行截断需要
white-space: nowrap
3. 多行截断需要
-webkit-
前缀，兼容性有限
4. 考虑使用JavaScript实现更复杂的截断逻辑
5. 在响应式设计中，注意不同屏幕尺寸下的表现
18. CSS的position属性有哪些值？它们的区别是什么？
简单
定位
position
布局
查看答案
回答模板1：属性值介绍
CSS的position属性有5个主要值：
•
static
：默认值，元素在文档流中正常定位
•
relative
：相对定位，相对于自身正常位置定位
•
absolute
：绝对定位，相对于最近的定位祖先元素定位
•
fixed
：固定定位，相对于视口定位
•
sticky
：粘性定位，基于滚动位置定位
回答模板2：使用场景
static
：默认状态，不需要特殊定位时
relative
：微调元素位置，或作为绝对定位的参考
absolute
：弹窗、下拉菜单、工具提示等
fixed
：导航栏、返回顶部按钮等
sticky
：表头、侧边栏等需要粘在某个位置的元素
回答模板3：注意事项
使用定位的注意事项：
1. 绝对定位元素会脱离文档流
2. 固定定位元素在滚动时保持位置不变
3. 粘性定位需要设置
top
、
right
、
bottom
或
left
4. 定位元素可能影响其他元素的布局
5. 合理使用z-index控制层叠顺序
19. 如何实现响应式图片？
中等
响应式图片
性能优化
移动适配
查看答案
回答模板1：基础方法
响应式图片的基本方法：
/* 方法1：设置max-width */
img {
    max-width: 100%;
    height: auto;
}

/* 方法2：使用srcset属性 */
<img 
    srcset="small.jpg 480w, medium.jpg 800w, large.jpg 1200w"
    sizes="(max-width: 600px) 480px, (max-width: 1000px) 800px, 1200px"
    src="medium.jpg"
    alt="响应式图片"
>
回答模板2：picture元素
<picture>
    <source media="(min-width: 1200px)" srcset="large.jpg">
    <source media="(min-width: 768px)" srcset="medium.jpg">
    <img src="small.jpg" alt="响应式图片">
</picture>
回答模板3：最佳实践
响应式图片的最佳实践：
1. 始终设置
max-width: 100%
2. 使用
srcset
提供不同分辨率的图片
3. 使用
sizes
指定不同视口下的图片尺寸
4. 考虑使用WebP等现代图片格式
5. 使用图片CDN进行图片优化
6. 实现懒加载提升性能
20. CSS的display属性有哪些常用值？
简单
display
显示模式
基础概念
查看答案
回答模板1：基础值
display属性的常用值：
•
none
：隐藏元素
•
block
：块级元素
•
inline
：行内元素
•
inline-block
：行内块元素
回答模板2：布局相关
•
flex
：Flexbox容器
•
grid
：Grid容器
•
inline-flex
：行内Flexbox容器
•
inline-grid
：行内Grid容器
•
table
：表格布局
•
table-cell
：表格单元格
回答模板3：现代值
•
flow-root
：创建新的BFC
•
contents
：元素本身不渲染，只渲染子元素
•
list-item
：列表项
•
run-in
：运行框（实验性）
选择合适的display值可以大大简化布局代码。
✨ 动画效果
21. CSS过渡（transition）和动画（animation）有什么区别？
中等
过渡
动画
性能
查看答案
回答模板1：概念区别
Transition（过渡）
：需要触发事件才能执行，如:hover、:focus等
Animation（动画）
：可以自动执行，支持关键帧和循环
回答模板2：语法区别
/* 过渡 */
.box {
    transition: all 0.3s ease;
}

.box:hover {
    transform: scale(1.1);
}

/* 动画 */
@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.box {
    animation: rotate 2s linear infinite;
}
回答模板3：使用场景
使用过渡
：简单的状态变化，如悬停效果、焦点状态
使用动画
：复杂的动画序列、需要自动执行的动画、循环动画
性能考虑
：两者都应优先使用transform和opacity，避免触发布局重排
22. 如何优化CSS动画的性能？
困难
性能优化
动画
渲染
查看答案
回答模板1：性能原则
CSS动画性能优化的核心原则：
1.
使用transform和opacity
：这两个属性不会触发重排
2.
避免同时动画多个属性
：减少浏览器计算负担
3.
使用will-change
：提示浏览器优化动画元素
回答模板2：具体优化
/* 优化前 */
.box {
    animation: move 2s ease-in-out;
}

@keyframes move {
    0% { left: 0; top: 0; }
    100% { left: 200px; top: 100px; }
}

/* 优化后 */
.box {
    will-change: transform;
    animation: move 2s ease-in-out;
}

@keyframes move {
    0% { transform: translate(0, 0); }
    100% { transform: translate(200px, 100px); }
}
回答模板3：监控和调试
如何监控动画性能：
1. 使用Chrome DevTools的Performance面板
2. 观察帧率，确保动画保持在60fps
3. 使用浏览器的Layers面板查看合成层
4. 注意动画的内存使用，避免内存泄漏
5. 在低端设备上测试动画性能
23. 什么是CSS硬件加速？如何启用？
困难
硬件加速
GPU
性能
查看答案
回答模板1：概念解释
CSS硬件加速是指利用GPU（图形处理器）来处理某些CSS动画，从而提高性能和流畅度。
回答模板2：启用方式
启用硬件加速的方法：
1.
使用transform
：任何transform属性都会触发硬件加速
2.
使用opacity
：透明度变化会触发硬件加速
3.
使用will-change
：提示浏览器为元素创建独立层
.element {
    will-change: transform;
    transform: translateZ(0); /* 强制创建合成层 */
}
回答模板3：注意事项
使用硬件加速的注意事项：
1. 不要滥用will-change，过多的层会消耗更多内存
2. 硬件加速主要优化2D变换和透明度
3. 某些属性（如filter）可能在不同浏览器上表现不同
4. 在移动设备上，硬件加速可能更有效
5. 监控层的数量，避免过度使用
24. 如何实现平滑滚动效果？
中等
滚动
用户体验
CSS
查看答案
回答模板1：CSS方法
/* 全局平滑滚动 */
html {
    scroll-behavior: smooth;
}

/* 特定容器平滑滚动 */
.container {
    scroll-behavior: smooth;
}
回答模板2：JavaScript方法
// 使用scrollIntoView
element.scrollIntoView({
    behavior: 'smooth',
    block: 'start'
});

// 使用scrollTo
window.scrollTo({
    top: 0,
    behavior: 'smooth'
});
回答模板3：注意事项
平滑滚动的注意事项：
1.
scroll-behavior: smooth
在现代浏览器中支持良好
2. 某些浏览器可能需要特殊处理
3. 避免在动画期间同时使用平滑滚动
4. 考虑用户偏好，提供禁用动画的选项
5. 在移动端测试滚动性能
25. CSS动画的timing-function有哪些值？
中等
timing-function
动画曲线
缓动函数
查看答案
回答模板1：预定义值
常用的预定义缓动函数：
•
ease
：默认值，慢速开始，快速结束
•
linear
：匀速
•
ease-in
：慢速开始
•
ease-out
：慢速结束
•
ease-in-out
：慢速开始和结束
回答模板2：自定义值
/* 贝塞尔曲线 */
.box {
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

/* 步进函数 */
.box {
    animation: move 2s steps(4, end);
}
回答模板3：选择建议
如何选择合适的缓动函数：
•
ease
：通用选择，适合大多数UI动画
•
linear
：进度条、旋转等需要匀速的动画
•
ease-in
：退出动画，如元素离开视口
•
ease-out
：进入动画，如元素出现
•
ease-in-out
：状态变化，如悬停效果
📱 响应式设计
31. 什么是响应式设计？它的核心原则是什么？
简单
响应式设计
移动优先
核心概念
查看答案
回答模板1：概念解释
响应式设计是一种网页设计方法，使网站能够适应不同设备和屏幕尺寸，提供最佳的用户体验。
核心原则：
1.
移动优先
：先设计移动端，再逐步增强到更大屏幕
2.
流式布局
：使用百分比和相对单位
3.
弹性图片
：图片能够适应不同屏幕
4.
媒体查询
：根据屏幕尺寸应用不同样式
回答模板2：技术实现
响应式设计的技术实现：
•
Viewport meta标签
：
<meta name="viewport" content="width=device-width, initial-scale=1.0">
•
媒体查询
：
@media (min-width: 768px) { ... }
•
Flexbox/Grid
：现代布局技术
•
相对单位
：rem, em, vw, vh等
回答模板3：最佳实践
响应式设计的最佳实践：
1. 从移动端开始设计（移动优先）
2. 使用流式网格布局
3. 优化图片和媒体
4. 设置合适的断点
5. 测试多种设备和屏幕尺寸
6. 考虑触摸交互和手势
32. 如何设置CSS媒体查询？有哪些常见断点？
中等
媒体查询
断点
响应式
查看答案
回答模板1：媒体查询语法
/* 基础语法 */
@media media-type and (media-feature) {
    /* CSS规则 */
}

/* 示例 */
@media (min-width: 768px) {
    .container {
        max-width: 720px;
    }
}

/* 多条件 */
@media (min-width: 768px) and (max-width: 1024px) {
    /* 平板样式 */
}
回答模板2：常见断点
/* 移动设备 */
@media (max-width: 575px) { ... }

/* 平板设备 */
@media (min-width: 576px) and (max-width: 767px) { ... }

/* 小桌面 */
@media (min-width: 768px) and (max-width: 991px) { ... }

/* 大桌面 */
@media (min-width: 992px) and (max-width: 1199px) { ... }

/* 超大屏幕 */
@media (min-width: 1200px) { ... }
回答模板3：最佳实践
媒体查询的最佳实践：
1.
移动优先
：使用min-width而不是max-width
2.
内容决定断点
：根据内容布局选择断点，而不是设备
3.
保持简单
：避免过多的断点
4.
测试真实设备
：不要只依赖浏览器工具
5.
考虑打印样式
：使用@media print
33. 如何实现响应式导航菜单？
中等
响应式导航
菜单
移动适配
查看答案
回答模板1：基础实现
/* 移动端菜单 */
.nav-menu {
    display: none;
    flex-direction: column;
    width: 100%;
}

.nav-toggle {
    display: block;
}

/* 桌面端菜单 */
@media (min-width: 768px) {
    .nav-menu {
        display: flex;
        flex-direction: row;
        width: auto;
    }
    
    .nav-toggle {
        display: none;
    }
}
回答模板2：CSS-only实现
/* 使用checkbox实现 */
.nav-toggle {
    display: none;
}

.nav-menu {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
}

.nav-toggle:checked ~ .nav-menu {
    max-height: 300px;
}

@media (min-width: 768px) {
    .nav-menu {
        max-height: none;
    }
}
回答模板3：最佳实践
响应式导航的最佳实践：
1.
移动优先
：先设计移动端菜单
2.
触摸友好
：按钮足够大，间距合适
3.
清晰的视觉层次
：当前页面明显标识
4.
避免悬停菜单
：移动端没有悬停
5.
测试多种设备
：确保在所有设备上可用
34. 如何优化响应式图片加载？
困难
响应式图片
性能优化
图片加载
查看答案
回答模板1：HTML方法
<img 
    srcset="small.jpg 480w, medium.jpg 800w, large.jpg 1200w"
    sizes="(max-width: 600px) 480px, (max-width: 1000px) 800px, 1200px"
    src="medium.jpg"
    alt="响应式图片"
    loading="lazy"
>
回答模板2：picture元素
<picture>
    <source media="(min-width: 1200px)" srcset="large.webp" type="image/webp">
    <source media="(min-width: 1200px)" srcset="large.jpg">
    <source media="(min-width: 768px)" srcset="medium.webp" type="image/webp">
    <source media="(min-width: 768px)" srcset="medium.jpg">
    <img src="small.jpg" alt="响应式图片" loading="lazy">
</picture>
回答模板3：性能优化
响应式图片的性能优化：
1.
使用现代格式
：WebP、AVIF等
2.
懒加载
：使用loading="lazy"
3.
图片压缩
：使用工具压缩图片
4.
CDN
：使用图片CDN进行动态优化
5.
CSS图片
：使用背景图片和CSS sprites
6.
SVG
：使用SVG代替位图
35. 如何创建响应式表格？
中等
响应式表格
数据展示
移动适配
查看答案
回答模板1：水平滚动
.table-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

table {
    width: 100%;
    min-width: 600px;
}
回答模板2：重排为卡片
/* 移动端重排 */
@media (max-width: 767px) {
    table, thead, tbody, th, td, tr {
        display: block;
    }
    
    thead {
        display: none;
    }
    
    tr {
        margin-bottom: 1rem;
        border: 1px solid #ddd;
    }
    
    td {
        position: relative;
        padding-left: 50%;
    }
    
    td::before {
        content: attr(data-label);
        position: absolute;
        left: 10px;
        font-weight: bold;
    }
}
回答模板3：其他方法
响应式表格的其他方法：
1.
优先级列
：在移动端只显示重要列
2.
折叠面板
：每行可展开显示详细信息
3.
搜索和筛选
：减少显示的数据量
4.
分页
：每页显示少量数据
5.
图表替代
：用图表代替数据表格
36. 什么是移动优先设计？如何实现？
中等
移动优先
设计原则
响应式
查看答案
回答模板1：概念解释
移动优先是一种网页设计策略，先为移动设备设计和开发，然后逐步增强到更大的屏幕。
核心原则：
1.
内容优先
：在小屏幕上优先展示核心内容
2.
性能优先
：移动设备性能有限，需要优化
3.
触摸友好
：设计适合触摸操作的界面
回答模板2：实现方法
/* 移动优先的CSS */
.container {
    padding: 1rem;
    max-width: 100%;
}

/* 逐步增强 */
@media (min-width: 768px) {
    .container {
        padding: 2rem;
        max-width: 720px;
    }
}

@media (min-width: 1024px) {
    .container {
        padding: 3rem;
        max-width: 960px;
    }
}
回答模板3：优势
移动优先设计的优势：
1.
更好的性能
：先加载核心内容和样式
2.
更好的用户体验
：在移动设备上表现更好
3.
更清晰的代码结构
：CSS更简洁，更容易维护
4.
更好的SEO
：搜索引擎更喜欢移动友好的网站
5.
面向未来
：适应不断增长的移动用户
37. 如何处理响应式设计中的字体大小？
中等
响应式字体
排版
可读性
查看答案
回答模板1：媒体查询方法
/* 基础字体大小 */
html {
    font-size: 16px;
}

/* 平板 */
@media (min-width: 768px) {
    html {
        font-size: 18px;
    }
}

/* 桌面 */
@media (min-width: 1024px) {
    html {
        font-size: 20px;
    }
}
回答模板2：clamp函数
/* 使用clamp()实现流式字体 */
h1 {
    font-size: clamp(2rem, 5vw, 4rem);
}

p {
    font-size: clamp(1rem, 2vw, 1.25rem);
}

/* 或者使用calc() */
h1 {
    font-size: calc(1.5rem + 2vw);
}
回答模板3：最佳实践
响应式字体的最佳实践：
1.
使用rem单位
：便于统一缩放
2.
设置合理的行高
：通常1.4-1.6
3.
考虑可读性
：移动端不要小于16px
4.
限制最大字体大小
：避免在大屏幕上过大
5.
测试多种设备
：确保在所有设备上可读
38. 如何创建响应式布局网格系统？
困难
网格系统
Flexbox
Grid
查看答案
回答模板1：Flexbox网格
.grid {
    display: flex;
    flex-wrap: wrap;
    margin: -0.5rem;
}

.grid-item {
    flex: 1 1 300px;
    padding: 0.5rem;
}

/* 响应式列 */
@media (min-width: 768px) {
    .grid-item {
        flex: 1 1 calc(50% - 1rem);
    }
}

@media (min-width: 1024px) {
    .grid-item {
        flex: 1 1 calc(33.333% - 1rem);
    }
}
回答模板2：CSS Grid
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
}

/* 或者使用minmax和auto-fill */
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 2rem;
}
回答模板3：自定义断点
.container {
    --grid-columns: 1;
    display: grid;
    grid-template-columns: repeat(var(--grid-columns), 1fr);
    gap: 1rem;
}

@media (min-width: 576px) {
    .container {
        --grid-columns: 2;
    }
}

@media (min-width: 768px) {
    .container {
        --grid-columns: 3;
    }
}

@media (min-width: 1024px) {
    .container {
        --grid-columns: 4;
    }
}
39. 如何测试响应式设计？
中等
响应式测试
调试
质量保证
查看答案
回答模板1：浏览器工具
使用浏览器开发者工具：
1.
Chrome DevTools
：设备模拟器（Ctrl+Shift+M）
2.
Firefox响应式设计模式
：Ctrl+Shift+M
3.
Safari
：Develop > Enter Responsive Design Mode
回答模板2：真实设备测试
真实设备测试方法：
1.
本地网络测试
：在同一WiFi下测试
2.
远程调试
：使用Chrome Remote Debugging
3.
云测试服务
：BrowserStack、Sauce Labs等
4.
物理设备
：使用真实手机和平板测试
回答模板3：测试清单
响应式设计的测试清单：
1.
布局测试
：所有断点下的布局是否正确
2.
字体测试
：字体大小和可读性
3.
图片测试
：图片是否正确缩放
4.
交互测试
：按钮、表单等是否可用
5.
性能测试
：加载速度和流畅度
6.
可访问性测试
：屏幕阅读器支持
40. 如何优化响应式网站的性能？
困难
性能优化
响应式
加载速度
查看答案
回答模板1：图片优化
图片优化策略：
1.
使用现代格式
：WebP、AVIF等
2.
响应式图片
：使用srcset和sizes
3.
懒加载
：使用loading="lazy"
4.
图片压缩
：使用工具压缩图片
回答模板2：CSS优化
CSS优化策略：
1.
关键CSS
：内联首屏CSS
2.
异步加载
：非关键CSS异步加载
3.
CSS压缩
：压缩CSS文件
4.
避免重复
：减少重复的CSS规则
5.
使用变量
：减少CSS文件大小
回答模板3：JavaScript优化
JavaScript优化策略：
1.
代码分割
：按需加载JavaScript
2.
延迟加载
：非关键JavaScript延迟加载
3.
减少DOM操作
：批量操作DOM
4.
使用Web Workers
：将计算密集型任务移至Worker
5.
优化事件处理
：防抖和节流
🚀 高级特性
41. 什么是CSS预处理器？它们解决了什么问题？
中等
预处理器
Sass
Less
查看答案
回答模板1：概念解释
CSS预处理器是扩展CSS语法的工具，添加了变量、混合（mixins）、函数等特性。
主要解决的问题：
1.
代码重复
：通过变量和混合减少重复
2.
维护困难
：通过模块化提高可维护性
3.
功能有限
：添加编程语言的特性
回答模板2：常见预处理器
Sass/SCSS
：功能最强大，支持嵌套、变量、混合、函数等
Less
：语法更接近CSS，学习曲线较平缓
Stylus
：语法灵活，支持多种语法风格
// Sass示例
$primary-color: #2196f3;

@mixin flex-center {
    display: flex;
    justify-content: center;
    align-items: center;
}

.container {
    @include flex-center;
    color: $primary-color;
}
回答模板3：选择建议
选择预处理器的建议：
•
新项目
：推荐Sass/SCSS，功能最完善
•
已有Less项目
：继续使用Less
•
简单项目
：可以使用原生CSS变量
•
大型项目
：考虑CSS-in-JS解决方案
42. CSS-in-JS有哪些解决方案？各有什么优缺点？
困难
CSS-in-JS
样式方案
React
查看答案
回答模板1：主要方案
CSS-in-JS的主要解决方案：
1.
Styled Components
：最流行的CSS-in-JS库
2.
Emotion
：性能更好的替代方案
3.
Stitches
：零运行时解决方案
4.
CSS Modules
：局部作用域CSS
回答模板2：优缺点对比
优点
：
• 样式作用域隔离，避免全局冲突
• 动态样式支持
• 组件化开发
• 服务端渲染支持
缺点
：
• 运行时性能开销
• 调试困难
• 学习曲线
• 打包体积增加
回答模板3：选择建议
如何选择CSS-in-JS方案：
•
React项目
：Styled Components或Emotion
•
性能要求高
：零运行时方案如Stitches
•
大型项目
：CSS Modules + 预处理器
•
团队熟悉CSS
：CSS Modules
•
需要动态样式
：CSS-in-JS方案
43. 什么是CSS Houdini？它能做什么？
困难
CSS Houdini
浏览器API
扩展CSS
查看答案
回答模板1：概念解释
CSS Houdini是一组浏览器API，允许开发者扩展CSS引擎，自定义CSS解析和渲染行为。
主要API：
1.
Paint API
：自定义CSS绘制
2.
Layout API
：自定义布局算法
3.
Animation Worklet
：自定义动画
4.
Properties and Values API
：自定义CSS属性
回答模板2：使用示例
// 注册Paint Worklet
CSS.paintWorklet.addModule('my-paint-worklet.js');

// my-paint-worklet.js
class CheckerboardPainter {
    paint(ctx, size, props) {
        const tileSize = 20;
        for (let y = 0; y < size.height / tileSize; y++) {
            for (let x = 0; x < size.width / tileSize; x++) {
                ctx.fillStyle = (x + y) % 2 ? 'white' : 'black';
                ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
            }
        }
    }
}

registerPaint('checkerboard', CheckerboardPainter);
回答模板3：实际应用
CSS Houdini的实际应用：
1.
自定义背景
：创建复杂的CSS背景图案
2.
自定义布局
：实现特殊的布局需求
3.
性能优化
：将计算密集型任务移至GPU
4.
工具开发
：创建CSS开发工具
5.
实验性特性
：测试新的CSS功能
44. CSS容器查询（Container Queries）是什么？
困难
容器查询
响应式
现代CSS
查看答案
回答模板1：概念解释
容器查询允许根据容器的大小而不是视口的大小来调整样式，这是响应式设计的重大改进。
回答模板2：使用方法
/* 定义容器 */
.card-container {
    container-type: inline-size;
    container-name: card;
}

/* 容器查询 */
@container card (min-width: 400px) {
    .card {
        display: flex;
        flex-direction: row;
    }
}

@container card (min-width: 800px) {
    .card {
        flex-direction: column;
    }
}
回答模板3：实际优势
容器查询的优势：
1.
组件化响应式
：组件根据自身容器调整
2.
更好的复用性
：组件在不同上下文中表现一致
3.
更简洁的代码
：减少媒体查询的复杂性
4.
设计系统支持
：更容易构建可复用的组件库
5.
微前端友好
：每个微前端可以独立响应
45. 什么是CSS层叠层（@layer）？如何使用？
困难
@layer
CSS层叠层
样式优先级
查看答案
回答模板1：概念解释
CSS层叠层（
@layer
）是一种新的CSS特性，用于控制样式的层叠顺序，解决第三方样式冲突问题。
回答模板2：使用方法
/* 声明层叠层顺序 */
@layer base, components, utilities;

/* 定义层 */
@layer base {
    body { font-family: sans-serif; }
}

@layer components {
    .button { background: blue; }
}

@layer utilities {
    .hidden { display: none; }
}

/* 未分层的样式优先级最高 */
.button {
    background: red; /* 覆盖components层的样式 */
}
回答模板3：实际应用
层叠层的实际应用：
1.
第三方样式管理
：控制第三方库样式的优先级
2.
设计系统
：为不同类型的样式建立清晰的层次
3.
主题系统
：更容易实现主题切换
4.
工具类框架
：如Tailwind CSS与自定义样式共存
5.
大型项目
：管理复杂的CSS架构
46. 如何实现CSS中的深色模式？
中等
深色模式
主题
CSS变量
查看答案
回答模板1：CSS变量方法
:root {
    --bg-color: #ffffff;
    --text-color: #000000;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-color: #000000;
        --text-color: #ffffff;
    }
}

body {
    background: var(--bg-color);
    color: var(--text-color);
}
回答模板2：类切换方法
:root {
    --bg-color: #ffffff;
    --text-color: #000000;
}

:root.dark {
    --bg-color: #000000;
    --text-color: #ffffff;
}

body {
    background: var(--bg-color);
    color: var(--text-color);
}

/* JavaScript切换 */
document.documentElement.classList.toggle('dark');
回答模板3：最佳实践
深色模式的最佳实践：
1.
使用CSS变量
：便于主题切换
2.
尊重用户偏好
：使用prefers-color-scheme
3.
提供切换选项
：让用户手动切换
4.
测试可访问性
：确保对比度足够
5.
渐进增强
：先实现浅色模式，再添加深色模式
47. CSS滚动驱动动画（Scroll-driven Animations）是什么？
困难
滚动动画
CSS动画
现代CSS
查看答案
回答模板1：概念解释
滚动驱动动画允许开发者基于滚动位置创建动画，而不需要JavaScript的scroll事件监听。
回答模板2：使用方法
/* 基于滚动进度的动画 */
.element {
    animation: slide-in linear;
    animation-timeline: scroll();
}

@keyframes slide-in {
    from { transform: translateX(-100%); }
    to { transform: translateX(0); }
}

/* 基于视口进入的动画 */
.element {
    animation: fade-in linear;
    animation-timeline: view();
}

@keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}
回答模板3：实际应用
滚动驱动动画的实际应用：
1.
视差效果
：基于滚动位置的视差动画
2.
进度指示器
：页面滚动进度条
3.
元素进入
：元素进入视口时的动画
4.
时间线
：创建基于滚动的时间线
5.
性能优化
：替代JavaScript的scroll事件
48. 如何创建CSS中的玻璃态效果？
中等
玻璃态
backdrop-filter
视觉效果
查看答案
回答模板1：基础实现
.glass {
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 10px;
}
回答模板2：深色玻璃态
.glass-dark {
    background: rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    color: white;
}
回答模板3：注意事项
玻璃态效果的注意事项：
1.
性能考虑
：backdrop-filter可能影响性能
2.
浏览器兼容
：需要-webkit-前缀
3.
可访问性
：确保足够的对比度
4.
背景要求
：需要有内容在玻璃元素后面
5.
使用场景
：导航栏、模态框、卡片
49. CSS子网格（Subgrid）是什么？
困难
Subgrid
Grid
布局
查看答案
回答模板1：概念解释
CSS子网格允许嵌套的网格项继承父网格的网格轨道，解决嵌套网格对齐问题。
回答模板2：使用方法
/* 父网格 */
.parent {
    display: grid;
    grid-template-columns: 1fr 2fr 1fr;
    gap: 1rem;
}

/* 子网格 */
.child {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: subgrid;
    grid-template-rows: subgrid;
}
回答模板3：实际应用
子网格的实际应用：
1.
表单布局
：对齐表单标签和输入框
2.
卡片布局
：对齐卡片内的内容
3.
导航菜单
：对齐导航项
4.
复杂布局
：解决嵌套网格的对齐问题
5.
设计系统
：创建一致的布局系统
50. 如何实现CSS中的视口单位（vw, vh, vmin, vmax）？
中等
视口单位
响应式
布局
查看答案
回答模板1：基础概念
视口单位相对于浏览器视口尺寸：
•
vw
：视口宽度的1%
•
vh
：视口高度的1%
•
vmin
：视口宽度和高度中较小值的1%
•
vmax
：视口宽度和高度中较大值的1%
回答模板2：使用示例
/* 全屏元素 */
.hero {
    width: 100vw;
    height: 100vh;
}

/* 响应式字体 */
h1 {
    font-size: 5vw;
}

/* 正方形元素 */
.square {
    width: 50vmin;
    height: 50vmin;
}

/* 最大宽度限制 */
.container {
    width: min(90vw, 1200px);
}
回答模板3：注意事项
视口单位的注意事项：
1.
移动设备
：100vh可能包含地址栏高度
2.
性能考虑
：频繁使用可能影响性能
3.
可访问性
：字体大小可能过大或过小
4.
结合使用
：与clamp()结合实现响应式
5.
测试多种设备
：确保在所有设备上表现良好
🏷️ HTML5
51. HTML5新增了哪些语义化标签？
简单
HTML5
语义化
标签
查看答案
回答模板1：主要标签
HTML5新增的语义化标签：
•
<header>
：页头
•
<nav>
：导航
•
<main>
：主要内容
•
<article>
：文章
•
<section>
：章节
•
<aside>
：侧边栏
•
<footer>
：页脚
回答模板2：使用示例
<body>
    <header>
        <nav>导航菜单</nav>
    </header>
    
    <main>
        <article>
            <section>文章内容</section>
        </article>
        <aside>侧边栏</aside>
    </main>
    
    <footer>页脚信息</footer>
</body>
回答模板3：语义化优势
语义化标签的优势：
1.
可访问性
：屏幕阅读器能更好地理解页面结构
2.
SEO
：搜索引擎能更好地理解内容
3.
可维护性
：代码更易读和维护
4.
标准化
：遵循Web标准
5.
未来兼容
：为未来功能做好准备
52. HTML5的Canvas和SVG有什么区别？
中等
Canvas
SVG
图形
查看答案
回答模板1：核心区别
Canvas
：基于像素的位图图形，适合复杂动画和游戏
SVG
：基于矢量的图形，适合图标和图表
回答模板2：详细对比
Canvas
：
• 位图图形，缩放会失真
• 适合复杂动画和游戏
• 性能更好（大量元素时）
• 不支持事件处理
SVG
：
• 矢量图形，缩放不失真
• 适合图标和图表
• 支持DOM操作和事件
• 文件通常更小
回答模板3：选择建议
如何选择：
•
使用Canvas
：游戏、复杂动画、图像处理
•
使用SVG
：图标、图表、需要缩放的图形
•
混合使用
：复杂图形用Canvas，简单图标用SVG
•
性能考虑
：大量元素时Canvas性能更好
53. HTML5的表单新增了哪些输入类型？
简单
HTML5表单
输入类型
表单验证
查看答案
回答模板1：新增类型
HTML5新增的输入类型：
•
email
：电子邮件
•
url
：URL地址
•
tel
：电话号码
•
number
：数字
•
range
：滑块
•
date
：日期选择器
•
time
：时间选择器
•
datetime-local
：日期时间
•
month
：月份
•
week
：周
•
color
：颜色选择器
•
search
：搜索框
回答模板2：使用示例
<form>
    <input type="email" placeholder="email@example.com">
    <input type="url" placeholder="https://example.com">
    <input type="tel" placeholder="123-456-7890">
    <input type="number" min="0" max="100">
    <input type="date">
    <input type="time">
    <input type="color">
</form>
回答模板3：优势
HTML5表单的优势：
1.
内置验证
：无需JavaScript验证
2.
更好的用户体验
：原生日期选择器等
3.
移动设备优化
：合适的虚拟键盘
4.
语义化
：更清晰的代码
5.
可访问性
：更好的屏幕阅读器支持
54. 什么是HTML5的Web Storage API？
中等
Web Storage
localStorage
sessionStorage
查看答案
回答模板1：概念解释
Web Storage API提供了两种在客户端存储数据的方式：
•
localStorage
：持久化存储，数据永不过期
•
sessionStorage
：会话存储，关闭浏览器后清除
回答模板2：使用示例
// localStorage
localStorage.setItem('username', 'John');
const username = localStorage.getItem('username');
localStorage.removeItem('username');
localStorage.clear();

// sessionStorage
sessionStorage.setItem('token', 'abc123');
const token = sessionStorage.getItem('token');
回答模板3：注意事项
Web Storage的注意事项：
1.
存储限制
：通常5-10MB
2.
数据类型
：只支持字符串，需要JSON转换
3.
安全性
：不要存储敏感信息
4.
同步操作
：可能影响性能
5.
兼容性
：现代浏览器都支持
55. HTML5的Web Workers是什么？如何使用？
困难
Web Workers
多线程
性能
查看答案
回答模板1：概念解释
Web Workers允许在后台线程中运行JavaScript，不会阻塞主线程，适合执行计算密集型任务。
回答模板2：使用方法
// 主线程
const worker = new Worker('worker.js');
worker.postMessage({ data: largeArray });
worker.onmessage = function(e) {
    console.log('结果:', e.data);
};

// worker.js
self.onmessage = function(e) {
    const result = processLargeData(e.data);
    self.postMessage(result);
};
回答模板3：使用场景
Web Workers的使用场景：
1.
大数据处理
：排序、过滤大量数据
2.
图像处理
：滤镜、压缩等
3.
加密解密
：计算密集型加密操作
4.
物理模拟
：游戏物理引擎
5.
实时数据处理
：股票数据分析
56. 什么是HTML5的地理位置API？
中等
地理位置
Geolocation
API
查看答案
回答模板1：概念解释
Geolocation API允许网页获取用户的地理位置信息（经度、纬度），需要用户授权。
回答模板2：使用方法
// 获取当前位置
navigator.geolocation.getCurrentPosition(
    (position) => {
        console.log('纬度:', position.coords.latitude);
        console.log('经度:', position.coords.longitude);
    },
    (error) => {
        console.error('获取位置失败:', error.message);
    },
    {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0
    }
);

// 持续监听位置变化
const watchId = navigator.geolocation.watchPosition(callback);

// 停止监听
navigator.geolocation.clearWatch(watchId);
回答模板3：注意事项
地理位置API的注意事项：
1.
用户授权
：必须获得用户同意
2.
隐私安全
：不要滥用位置信息
3.
精度控制
：根据需求设置精度
4.
错误处理
：处理各种错误情况
5.
兼容性
：移动设备支持更好
57. HTML5的WebSocket是什么？与HTTP有何区别？
困难
WebSocket
实时通信
网络
查看答案
回答模板1：概念解释
WebSocket是一种在单个TCP连接上进行全双工通信的协议，允许服务器主动向客户端推送数据。
回答模板2：与HTTP的区别
HTTP
：
• 请求-响应模式
• 无状态协议
• 每次请求都需要建立连接
• 不支持服务器推送
WebSocket
：
• 全双工通信
• 有状态连接
• 建立连接后保持
• 支持服务器推送
回答模板3：使用场景
WebSocket的使用场景：
1.
实时聊天
：在线聊天应用
2.
实时游戏
：多人在线游戏
3.
实时数据
：股票行情、体育比分
4.
协作编辑
：在线文档协作
5.
物联网
：设备实时通信
58. 什么是HTML5的Service Worker？
困难
Service Worker
PWA
离线缓存
查看答案
回答模板1：概念解释
Service Worker是在浏览器后台运行的脚本，可以拦截网络请求、缓存资源，实现离线访问和推送通知。
回答模板2：使用方法
// 注册Service Worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
        .then(registration => {
            console.log('SW registered');
        });
}

// sw.js
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('v1').then(cache => {
            return cache.addAll([
                '/',
                '/index.html',
                '/styles.css',
                '/script.js'
            ]);
        })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});
回答模板3：实际应用
Service Worker的实际应用：
1.
离线缓存
：缓存关键资源
2.
推送通知
：服务器推送消息
3.
后台同步
：在后台同步数据
4.
性能优化
：预缓存常用资源
5.
PWA
：渐进式Web应用的核心技术
59. HTML5的Web Components是什么？
困难
Web Components
组件化
自定义元素
查看答案
回答模板1：概念解释
Web Components是一套用于创建可重用、封装的HTML组件的技术，包括Custom Elements、Shadow DOM和HTML Templates。
回答模板2：使用方法
// 自定义元素
class MyComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({mode: 'open'});
        shadow.innerHTML = `
            <style>
                p { color: red; }
            </style>
            <p>Hello World</p>
        `;
    }
}

customElements.define('my-component', MyComponent);

// 使用
<my-component></my-component>
回答模板3：优势
Web Components的优势：
1.
封装性
：样式和逻辑隔离
2.
可重用性
：跨框架使用
3.
标准化
：浏览器原生支持
4.
框架无关
：不依赖特定框架
5.
未来兼容
：Web标准的一部分
60. 如何优化HTML页面的加载性能？
中等
性能优化
加载速度
最佳实践
查看答案
回答模板1：HTML优化
HTML页面的优化策略：
1.
语义化标签
：使用正确的HTML标签
2.
减少DOM
：减少不必要的嵌套
3.
异步加载
：使用async和defer
4.
预加载
：使用link rel="preload"
回答模板2：资源优化
资源优化策略：
1.
关键CSS
：内联首屏CSS
2.
异步CSS
：非关键CSS异步加载
3.
图片优化
：使用现代格式和懒加载
4.
字体优化
：字体子集化和预加载
5.
压缩
：Gzip或Brotli压缩
回答模板3：最佳实践
HTML性能优化的最佳实践：
1.
减少HTTP请求
：合并文件、使用雪碧图
2.
使用CDN
：加速资源加载
3.
缓存策略
：设置合适的缓存头
4.
代码分割
：按需加载资源
5.
监控性能
：使用Lighthouse等工具
📚 CSS与HTML面试题库 - 60道精选题目
持续更新中... | 支持移动端访问