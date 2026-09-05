---
tags: [建站, VitePress]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "blog/config.md"
---

# 站点配置

## hero
```md
hero:
  actions:
    - theme: brand
      text: Markdown示例
      link: /markdown-examples
    - theme: alt
      text: API示例
      link: /api-examples
    - theme: custom-button
      text: blog记录
      link: /blog-config
```

在 VitePress 的主页配置文件中，actions 字段用于定义页面上的动作按钮，而 theme 是用于定义按钮的主题的属性之一。theme 属性接受两种预定义的主题值：brand 和 alt。


- `brand`：该主题通常用于强调页面中的主要操作，比如 "Get Started" 这样的按钮。它通常会使用品牌的主题颜色，并以醒目的方式呈现。
- `alt`：该主题通常用于次要操作或者辅助功能的按钮。它通常会使用非品牌的颜色，比如灰色或者其他中性颜色，并以不那么醒目的方式呈现。
- 除了 theme 属性之外，actions 字段还可以包含自定义按钮，通过设置 theme 属性为 custom-button 来实现。自定义按钮的配置项如下：


## head
添加外部链接,在`head`中添加如下：
```md
 [
      'script',
      {},
      `window._hmt = window._hmt || [];
      (function() {
      var hm = document.createElement("script");
      hm.src = "lib/dandelion.js";
      var s = document.getElementsByTagName("script")[0];
      s.parentNode.insertBefore(hm, s);
      })();`
    ]

```
` hm.src = "dandelion.js"` 这个`dandelion.js`是放在`public`中，作为静态文件来引用。


## 添加锚点

先在目标标题元素上添加 id 属性，例如：

```md
## 我的标题 {#my-anchor}
```

然后在文档的任意位置添加锚点链接，例如：

```md
[点击跳转到config.js的位置](#my-anchor)
```

这样，当用户点击锚点"[点击跳转到config.js的位置](#my-anchor)"时，页面会自动滚动到目标标题位置。



---