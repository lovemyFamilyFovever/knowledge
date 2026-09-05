---
outline: [1,3]
head:
  - - meta
    - name: description
      content: 前端优化方案
  - - meta
    - name: keywords
      content: 前端 前端优化方案
tags: [性能优化]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/optimization/index.md"
---

# 首屏优化方案

## css 样式的调整：

JavaScript外联文件引用放在html文档底部；CSS外联文件引用在html文档头部，位于head内；对首屏页面用到的 css内容，可以style 的形式写在首页

## 首屏不需要展示的较大尺寸图片，请使用lazyload；

## 避免404错误：尽量减少外联js；

## 减少cookies的大小：尽量减少cookies的体积对减少用户获得响应的时间十分重要；

## 减少DOM Elements的数量；

## Webpack开启gzip压缩

## 服务端渲染SSR

## Skeleton Screen (骨架屏)

## 路由懒加载

## 图片懒加载(vue-lazyload)

## Promise优化

## 减少http请求

## 精灵图可以大大地减少CSS背景图片的HTTP请求次数；

## 压缩图片

## CDN优化

## 少用location.reload()

## 正确使用display的属性

## 采用按需加载

## 压缩图片优化

## 合理使用缓存

## 预加载

## 几种常见web页面渲染方式对比

 FP: "首次绘制"（First Paint）不包括默认背景绘制（例如浏览器默认的白色背景），但是包含非默认的背景绘制，与ifram

 FCP:"首次内容绘制"（First Contentful Paint）包含文本，图片（包含背景图），非白色canvas与SV

 iframe:父级浏览上下文不应该知道子浏览上下文的绘制事件，反之亦然。这就意味着如果一个浏览上下文只包含一个iframe，那么将只有“首次绘制"，但没有“首次内容绘制

## 1.CSR（客户端渲染）

1. 最近几年流行的SPA，web app都是CSR模式，页面只有一个空div

2. 优点：

（1）不依赖数据

（2）FP时间最块；就是留了一个div挂载组件嘛

（3）客户端用户体验好

（4）内存数据共享

3. 缺点：

（1）SEO不友好

（2）FCP（首次有内容的渲染）、FMP（ 首次有意义的绘制）慢；要各种发请求；

## 2.预渲染

使用puppeteer或者 rize.js 提前渲染一遍，另存起来；这种方式太傻了，就不详细介绍了；具体可以看他们的官方文档；

## 3.SSR和同构（服务端渲染）

1.服务端渲染，服务器把内容全都拼好直接输出，服务端用一套模板引擎

2.服务器和客户端使用一套代码就是同构

3.优点：

（1）SEO友好

（2）首屏性能高，FMP比CSR和预渲染都要快

4.缺点：

（1）客户端数据共享成本高

（2）模板维护成本高

## 4.最优的渲染方式

**Skeleton Screen (骨架屏)**

简单来说，骨架屏就是在页面内容未加载完成的时候，先使用一些图形进行占位，待内容加载完成之后再把它替换掉。体验的效果就是，在页面完全渲染完成之前，用户会看到一个样式简单，描绘了当前页面的大致框架，能够感知到页面正在逐步加载，最终骨架屏中各个占位部分被完全替换。

**Vue-Router路由懒加载（利用Webpack的代码切割）**

把不同路由对应的组件分割为不同的代码块，当路由被访问的时候，再加载对应的组件，对中大型项目来说，会显得很高效，对开发者而言，也方便维护。不过这里要对生产环境和开发环境做区分，因为如果项目很大的话，每次更改代码触发的热更新时间都会很长，所以只在生产环境中使用路由懒加载。

## 图片懒加载(vue-lazyload)


更多使用方式可参考[vue-lazyload](https://links.jianshu.com/go?to=https%3A%2F%2Fyq.aliyun.com%2Fgo%2FarticleRenderRedirect%3Furl%3Dhttps%3A%2F%2Flink.juejin.im%3Ftarget%3Dhttps%253A%252F%252Fgithub.com%252Fhilongjw%252Fvue-lazyload) 这里呈现的效果就是，请求完成数据，再去请求阿里云存放的图片，这个阶段中，图片资源加载过程中，显示loading的状态，加载完毕，显示图片，如果图片加载失败，显示失败的图片。

## 减少http请求

网页中的的图片、form、flash等等元素都会发出HTTP请求，尽可能的减少页面中非必要的元素，可以减少HTTP请求的次数。

## CSS Sprites ——精灵（雪碧）图

图片是增加HTTP请求的最大可能者；把全站的图标都放在一个图像文件中，然后用CSS的background-image和background-position属性定位来显示其中的一小部分。

## 压缩图片

图片是最占流量的资源，因此尽量避免使用它，使用时选择最合适的格式（实现需求的前提下，以大小判断），合适的大小，然后使用智图压缩，同时在代码中用Srcset来按需显示。

PS：过度压缩图片大小影响图片显示效果

a） 使用智图（ [http://zhitu.tencent.com/](https://links.jianshu.com/go?to=http%3A%2F%2Fzhitu.tencent.com%2F) ）

b） 使用其它方式代替图片(1. 使用CSS3 2. 使用SVG 3. 使用IconFont）

c） 使用Srcset

d） 选择合适的图片(1. webP优于JPG 2. PNG8优于GIF）

e） 选择合适的大小（1. 首次加载不大于1014KB 2. 不宽于640（基于手机屏幕一般宽度））

## CDN内容分发网络

## 少用location.reload()

使用`location.reload()` 会刷新页面，刷新页面时页面所有资源（css，js，img等）会重新请求服务器；建议使用	`location.href="当前页url"` 代替`location.reload()` ，使用location.href 浏览器会读取本地缓存资源。

## 正确使用display的属性

display属性会影响页面的渲染，需要合理使用。

a） display:inline后不应该再使用width、height、margin、padding以及float

b） display:inline-block后不应该再使用float

c） display:block后不应该再使用vertical-align

d） display:table-*后不应该再使用margin或者float

## 按需加载

将不影响首屏的资源和当前屏幕资源不用的资源放到用户需要时才加载，可以大大提升重要资源的显示速度和降低总体流量。

PS：按需加载会导致大量重绘，影响渲染性能

a） LazyLoad

b） 滚屏加载

c） 通过Media Query加载

## 合理使用缓存

使用缓存可以减少向服务器的请求数，节省加载时间，所以所有静态资源都要在服务器端设置缓存，并且尽量使用长Cache（长Cache资源的更新可使用时间戳

## 预加载

以下是几个通过浏览器特性来很容易提高资源加载速度的方法：

**1：DNS prefetching**

DNS解析的速度可用通过下面的标签来进行预解析

`<link rel="dns-prefetch" href="//weibo.com">`

**2：Preconnect**

和DNS预解析差不多，Preconnect还会做TCP握手和TLS Negotiation：

`<link rel="preconnect" href="http://css-tricks.com">`

**3：Prefetching**

如果我们猜测用户接下来将要访问哪个具体的资源，那就可以用prefetching来预加载确定的资源了

`<link rel="prefetch" href="image.png">`

**4：Prerendering pages**

预先渲染页面，这是更牛的预加载方式了，他的作用就类似打开一个隐藏的tab差不多

`<link rel="prerender" href="http://css-tricks.com">`

**5：新特性：Preloading**

和prefetching不同的是，preloading会让浏览器无论如何都下载指定的资源

`<link rel="preload" href="image.png">`

**6：H5音乐预加载**

`<audio src="music.mp3" autoplay="autoplay" loop preload="auto" id="sendid2"></audio>`

参考资料：

[最近做首屏优化学到的知识点](https://links.jianshu.com/go?to=https%3A%2F%2Fbaijiahao.baidu.com%2Fs%3Fid%3D1644777703316083708%26wfr%3Dspider%26for%3Dpc)

[关于首屏优化](https://links.jianshu.com/go?to=https%3A%2F%2Fyq.aliyun.com%2Farticles%2F608255)

[首屏加载优化有哪些方案？](https://www.jianshu.com/p/805432d98f3f)

[网站首屏优化总结](https://links.jianshu.com/go?to=https%3A%2F%2Fblog.csdn.net%2Fweixin_42748934%2Farticle%2Fdetails%2F107666834)

[web前端性能优化之CDN](https://links.jianshu.com/go?to=https%3A%2F%2Fwww.cnblogs.com%2Fchanglon%2Fp%2F10165053.html)