---
outline: [1,3]
head:
  - - meta
    - name: description
      content: css3常用的样式整理
  - - meta
    - name: keywords
      content: css3常用的样式整理 前端开发 前端框架 前端工程师
tags: [CSS]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/css/normalStyle.md"
---

# 常用css3样式整理

<hr />

# 多行文本溢出省略号显示

- 让文本只显示一行，然后溢出省略号显示 

```css
overflow: hidden;
text-overflow: ellipsis;
white-space: nowrap;
```

- 让文本显示两行，然后溢出部分省略号显示   

```
line-height: 1.3rem;
max-height: 2.6rem;
display: -webkit-box;
-webkit-box-orient: vertical;
-webkit-line-clamp: 2;
word-break: break-all;
overflow: hidden;
```

# 滚动条的处理

CSS3中隐藏滚动条但仍能继续滚动 

```css
::-webkit-scrollbar {    
    width: 0px;    
    height: 0px; 
}          
```

清除浏览器默认的滚动条 

```css
::-webkit-scrollbar, 
::-webkit-scrollbar-track,
::-webkit-scrollbar-thumb,
::-webkit-scrollbar-corner {
    display: none;
}      
```

# Chrome浏览器下自动填充的输入框背景会变成黄色，可以用下面CSS声明修成白色*

```css
input:-webkit-autofill {    
    -webkit-box-shadow: inset 0 0 0 1000px #fff;     
    box-shadow:inset 0 0 0 1000px #fff;    
    background-color: transparent;  
}               
```

# 修改placeholder的颜色(样式)

```css
::-webkit-input-placeholder {/* WebKit, Blink, Edge */    
    color: #A0A0A0; 
} 
:-moz-placeholder { /* Mozilla Firefox 4 to 18 */    
    color: #A0A0A0; 
} 
::-moz-placeholder { /* Mozilla Firefox 19+ */    
    color: #A0A0A0; 
} 
:-ms-input-placeholder { /* Internet Explorer 10-11 */    
    color: #A0A0A0; 
}               
```

# 网站置灰