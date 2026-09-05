---
outline: [1,3]
layout: doc
tags: [建站, VitePress]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "blog/plugins/addPicPlugin.md"
---

# markdown-it-custom-attrs

[参考链接](http://t.csdnimg.cn/plgWG)

基于markdown-it 可设置自定义属性的插件

## 安装依赖

```bash
npm install markdown-it-custom-attrs --save
```

## 引入插件 

在`config.js`|`config.mjs`文件中引入插件

```javascript
import mdItCustomAttrs  from 'markdown-it-custom-attrs'
```

## 配置插件

在`config.js`|`config.mjs`文件中配置插件

```javascript
export default defineConfig({
    markdown:{
        config: (md) => {
            // use more markdown-it plugins!
            md.use(mdItCustomAttrs, 'image', {
                'data-fancybox': "gallery"
            })
        }
    }
})
```

## 引入图片灯箱

在`head`中引入图片灯箱的css和js文件

```javascript
export default defineConfig({
    head:[
        ["link",{ rel: "stylesheet", href: "https://cdn.jsdelivr.net/npm/@fancyapps/ui/dist/fancybox.css" }],
        ["script", { src: "https://cdn.jsdelivr.net/npm/@fancyapps/ui@4.0/dist/fancybox.umd.js" }],
    ]
})
```

## 渲染效果
   
```markdown
<!-- ![](图片地址) -->
```

渲染出的html代码如下：

```html
<img src="图片地址" data-fancybox="gallery"/>
```

## 测试图片灯箱效果

   点击图片，会弹出图片灯箱效果
   ![图片](../imgs/test.png)
