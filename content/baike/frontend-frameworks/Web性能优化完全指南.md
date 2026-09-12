---
title: "Web性能优化完全指南"
tags: []
source: "baike"
source_path: "技术文章 / Web开发框架"
collected: "2026-09-05"
status: "imported"
---

# Web性能优化完全指南


> 📌 **导航**：本文是 **Web性能优化完全指南** 词条，属于 frontend-frameworks 术语集。相关枢纽：[[GraphQL从入门到精通]]、[[WebAssembly完全指南]]、[[Web性能优化完全指南]]、[[现代前端工程化完全指南]]。

## Web性能优化完全指南

## 一、Core Web Vitals：用户体验的核心指标

Core Web Vitals是Google提出的一套衡量真实用户体验的核心指标，直接影响网站在搜索结果中的排名。这三个指标分别关注加载体验、交互响应和视觉稳定性。

### 1.1 Largest Contentful Paint (LCP)

**指标定义**：测量视口内最大可见内容元素（图片、视频、块级元素文本）的渲染时间。良好标准是≤2.5秒。

**优化策略**：

```html
<!-- 预加载关键资源 -->
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/images/hero.jpg" as="image">

<!-- 使用fetchpriority属性 -->
<img src="/images/hero.jpg" fetchpriority="high" loading="eager">
<script src="/app.js" async></script>
```

```javascript
// 使用Resource Hints API
const preloadLink = document.createElement('link');
preloadLink.rel = 'preload';
preloadLink.href = '/critical-data.json';
preloadLink.as = 'fetch';
preloadLink.crossOrigin = 'anonymous';
document.head.appendChild(preloadLink);

// 监控LCP性能
const lcpObserver = new PerformanceObserver((entryList) => {
  const entries = entryList.getEntries();
  const lastEntry = entries[entries.length - 1];
  console.log('LCP:', lastEntry.startTime);
  // 发送至监控系统
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/metrics', JSON.stringify({
      metric: 'LCP',
      value: lastEntry.startTime,
      url: window.location.href
    }));
  }
});
lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
```

**服务端优化**：

```nginx
# Nginx配置启用Brotli压缩
brotli on;
brotli_types text/plain text/css application/javascript application/json image/svg+xml;

# 设置长缓存策略
location ~* \.(js|css|png|jpg|jpeg|gif|ico|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 1.2 First Input Delay (FID) 与 Interaction to Next Paint (INP)

**指标定义**：
- **FID**：测量用户首次交互（点击、按键）到浏览器开始处理事件处理程序的时间
- **INP**：测量所有交互的响应时间，通过观察所有交互的延迟来评估页面的整体响应性

**优化策略**：

```javascript
// 使用requestIdleCallback处理非关键任务
function expensiveTask() {
  // 耗时计算任务
  return new Promise(resolve => {
    setTimeout(() => {
      const result = performHeavyComputation();
      resolve(result);
    }, 0);
  });
}

// 分解长任务
function breakLongTask(tasks) {
  return new Promise(resolve => {
    const chunkSize = 10;
    let index = 0;
    
    function processChunk() {
      const chunk = tasks.slice(index, index + chunkSize);
      chunk.forEach(task => task());
      index += chunkSize;
      
      if (index < tasks.length) {
        // 让出主线程
        requestIdleCallback(processChunk, { timeout: 50 });
      } else {
        resolve();
      }
    }
    
    processChunk();
  });
}

// 使用Web Worker处理CPU密集型任务
const worker = new Worker('worker.js');
worker.postMessage({ type: 'processData', data: largeDataSet });
worker.onmessage = (e) => {
  updateUI(e.data.result);
};
```

### 1.3 Cumulative Layout Shift (CLS)

**指标定义**：测量页面整个生命周期中所有意外布局偏移的累计分数。良好标准是≤0.1。

**优化策略**：

```css
/* 为所有媒体元素设置明确的宽高比 */
img, video, iframe {
  width: 100%;
  height: auto;
  aspect-ratio: attr(width) / attr(height);
  /* 或使用固定的宽高比 */
  aspect-ratio: 16/9;
}

/* 使用CSS contain属性限制布局影响 */
.container {
  contain: layout paint;
}

/* 为动态内容预留空间 */
.ad-container {
  min-height: 250px; /* 预估广告高度 */
}
```

```html
<!-- 图片优化示例 -->
<picture>
  <source media="(min-width: 800px)" 
          srcset="/images/hero-desktop.webp" 
          type="image/webp">
  <source media="(min-width: 800px)" 
          srcset="/images/hero-desktop.jpg" 
          type="image/jpeg">
  <source media="(min-width: 400px)" 
          srcset="/images/hero-mobile.webp" 
          type="image/webp">
  <img src="/images/hero-mobile.jpg" 
       alt="Hero image" 
       width="1200" 
       height="600"
       decoding="async">
</picture>
```

## 二、前端性能优化

### 2.1 资源加载优化

**关键渲染路径优化**：

```html
<!-- 资源加载优先级控制 -->
<link rel="preload" href="/critical.css" as="style" onload="this.rel='stylesheet'">
<link rel="preload" href="/main.js" as="script">

<!-- DNS预解析和预连接 -->
<link rel="dns-prefetch" href="//fonts.googleapis.com">
<link rel="preconnect" href="https://cdn.example.com" crossorigin>

<!-- HTTP/2 Server Push -->
<!-- 服务器配置示例 -->
<!-- 
Link: </styles/main.css>; rel=preload; as=style
Link: </scripts/app.js>; rel=preload; as=script
-->
```

**资源加载策略**：

```javascript
// 动态import实现路由级代码分割
const loadPage = async (pageName) => {
  try {
    const module = await import(`./pages/${pageName}.js`);
    return module.default;
  } catch (error) {
    // 回退方案
    const fallback = await import('./pages/fallback.js');
    return fallback.default;
  }
};

// 预加载下一页资源
const preloadPage = (pageName) => {
  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.href = `/pages/${pageName}.js`;
  link.as = 'script';
  document.head.appendChild(link);
};
```

### 2.2 代码分割与Tree Shaking

**Webpack配置示例**：

```javascript
// webpack.config.js
module.exports = {
  // 入口分割
  entry: {
    main: './src/index.js',
    vendor: ['react', 'react-dom']
  },
  
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        },
        styles: {
          name: 'styles',
          test: /\.css$/,
          chunks: 'all',
          enforce: true
        }
      }
    }
  },
  
  // Tree Shaking配置
  optimization: {
    usedExports: true,
    sideEffects: false,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true,
            dead_code: true,
            unused: true
          }
        }
      })
    ]
  }
};
```

**ES Modules的Tree Shaking**：

```javascript
// utils/math.js - 使用export
export function add(a, b) {
  return a + b;
}

export function subtract(a, b) {
  return a - b;
}

// main.js - 只导入需要的函数
import { add } from './utils/math.js';

// 配置package.json
{
  "sideEffects": false,
  "main": "dist/index.js",
  "module": "src/index.js" // 支持ES模块的构建工具会优先使用
}
```

### 2.3 懒加载实现

**图片懒加载**：

```javascript
// 原生懒加载
<img data-src="/images/lazy.jpg" 
     loading="lazy" 
     decoding="async" 
     alt="Lazy image" 
     width="300" 
     height="200">

// Intersection Observer API
const lazyImages = document.querySelectorAll('[data-src]');

const imageObserver = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const image = entry.target;
      image.src = image.dataset.src;
      image.srcset = image.dataset.srcset;
      image.classList.add('loaded');
      observer.unobserve(image);
    }
  });
}, {
  rootMargin: '200px 0px', // 提前200px加载
  threshold: 0.01
});

lazyImages.forEach(img => imageObserver.observe(img));

// 组件懒加载（React示例）
const LazyComponent = React.lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <LazyComponent />
    </Suspense>
  );
}
```

### 2.4 预加载策略

```javascript
// 预加载关键资源
const preloadResources = () => {
  const resources = [
    { href: '/fonts/main.woff2', as: 'font', type: 'font/woff2' },
    { href: '/images/hero.webp', as: 'image' },
    { href: '/api/critical-data', as: 'fetch' }
  ];

  resources.forEach(resource => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = resource.href;
    link.as = resource.as;
    if (resource.type) link.type = resource.type;
    if (resource.as === 'font') link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  });
};

// 基于用户行为的智能预加载
const intelligentPreload = () => {
  const links = document.querySelectorAll('a[href]');
  
  links.forEach(link => {
    // 鼠标悬停时预加载
    link.addEventListener('mouseenter', () => {
      const prefetchLink = document.createElement('link');
      prefetchLink.rel = 'prefetch';
      prefetchLink.href = link.href;
      document.head.appendChild(prefetchLink);
    });
    
    // 可视区域内的链接立即预加载
    if (isElementInViewport(link)) {
      const prerenderLink = document.createElement('link');
      prerenderLink.rel = 'prerender';
      prerenderLink.href = link.href;
      document.head.appendChild(prerenderLink);
    }
  });
};
```

## 三、图片优化策略

### 3.1 现代图片格式选择

```html
<!-- 渐进式图片加载 -->
<picture>
  <source srcset="image.avif" type="image/avif">
  <source srcset="image.webp" type="image/webp">
  <source srcset="image.jxl" type="image/jxl">
  <img src="image.jpg" 
       alt="描述"
       width="800" 
       height="600"
       loading="lazy"
       decoding="async"
       fetchpriority="low">
</picture>

<!-- 使用CSS背景图实现艺术方向 -->
<style>
.hero {
  background-image: url('/images/hero-mobile.webp');
  background-size: cover;
  background-position: center;
}

@media (min-width: 768px) {
  .hero {
    background-image: url('/images/hero-tablet.webp');
  }
}

@media (min-width: 1200px) {
  .hero {
    background-image: url('/images/hero-desktop.webp');
  }
}
</style>
```

**图片格式转换脚本**：

```javascript
// sharp.js - 服务器端图片处理
const sharp = require('sharp');
const fs = require('fs');

async function convertImage(inputPath, outputPath, options = {}) {
  const { width, height, format = 'webp', quality = 80 } = options;
  
  try {
    let transformer = sharp(inputPath);
    
    if (width || height) {
      transformer = transformer.resize(width, height, {
        fit: 'inside',
        withoutEnlargement: true
      });
    }
    
    switch (format) {
      case 'webp':
        transformer = transformer.webp({ quality, effort: 6 });
        break;
      case 'avif':
        transformer = transformer.avif({ quality, effort: 5 });
        break;
      case 'mozjpeg':
        transformer = transformer.jpeg({ quality, mozjpeg: true });
        break;
    }
    
    await transformer.toFile(outputPath);
    console.log(`Converted ${inputPath} to ${outputPath}`);
  } catch (error) {
    console.error('Error converting image:', error);
  }
}

// 批量转换
const images = fs.readdirSync('./images/raw');
images.forEach(img => {
  if (img.match(/\.(jpg|jpeg|png)$/i)) {
    const input = `./images/raw/${img}`;
    const baseName = img.replace(/\.[^.]+$/, '');
    
    convertImage(input, `./images/webp/${baseName}.webp`, { format: 'webp' });
    convertImage(input, `./images/avif/${baseName}.avif`, { format: 'avif' });
  }
});
```

### 3.2 响应式图片实现

```html
<!-- 使用srcset和sizes属性 -->
<img srcset="/images/small.jpg 300w,
             /images/medium.jpg 600w,
             /images/large.jpg 900w,
             /images/xlarge.jpg 1200w"
     sizes="(max-width: 600px) 100vw,
            (max-width: 900px) 50vw,
            33vw"
     src="/images/medium.jpg"
     alt="Responsive image"
     loading="lazy">

<!-- 使用picture元素实现艺术方向 -->
<picture>
  <source media="(min-width: 1200px)" 
          srcset="/images/hero-wide.webp" 
          type="image/webp">
  <source media="(min-width: 800px)" 
          srcset="/images/hero-medium.webp" 
          type="image/webp">
  <source media="(max-width: 799px)" 
          srcset="/images/hero-narrow.webp" 
          type="image/webp">
  
  <!-- 回退方案 -->
  <source media="(min-width: 1200px)" 
          srcset="/images/hero-wide.jpg">
  <source media="(min-width: 800px)" 
          srcset="/images/hero-medium.jpg">
  <img src="/images/hero-narrow.jpg" 
       alt="Hero image"
       width="1200" 
       height="600"
       class="hero-image">
</picture>
```

### 3.3 CDN图片优化配置

```nginx
# Nginx + CDN图片优化配置
location ~* \.(jpg|jpeg|png|gif|webp|avif)$ {
    # 启用图片优化模块
    image_filter_buffer 10M;
    image_filter_jpeg_quality 85;
    image_filter_webp_quality 80;
    
    # 根据Accept头返回最优格式
    if ($http_accept ~* "image/avif") {
        rewrite ^(.+)\.(jpg|jpeg|png|gif)$ $1.avif break;
    }
    if ($http_accept ~* "image/webp") {
        rewrite ^(.+)\.(jpg|jpeg|png|gif)$ $1.webp break;
    }
    
    # 缓存策略
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary "Accept";
}
```

**Cloudflare图片优化示例**：

```javascript
// 使用Cloudflare Image Resizing
const optimizeImage = (imageUrl, options = {}) => {
  const { width, height, format = 'auto', quality = 80 } = options;
  
  const params = new URLSearchParams();
  if (width) params.append('width', width);
  if (height) params.append('height', height);
  params.append('format', format);
  params.append('quality', quality);
  
  return `https://example.com/cdn-cgi/image/${params.toString()}/${imageUrl}`;
};

// 使用示例
const optimizedUrl = optimizeImage('/uploads/hero.jpg', {
  width: 800,
  format: 'webp',
  quality: 85
});
```

## 四、字体优化

### 4.1 FOUT与FOIT的平衡

```css
/* 字体加载策略 */
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2'),
       url('/fonts/myfont.woff') format('woff');
  font-weight: 400;
  font-style: normal;
  font-display: swap; /* 立即显示后备字体，加载后替换 */
}

/* 高级字体加载策略 */
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont-light.woff2') format('woff2');
  font-weight: 300;
  font-display: optional; /* 仅在快速加载时使用 */
}

@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont-bold.woff2') format('woff2');
  font-weight: 700;
  font-display: block; /* 阻塞渲染，但有限制时间 */
}
```

**JavaScript字体加载**：

```javascript
// 使用Font Loading API
async function loadFont(fontFamily, url, descriptors = {}) {
  try {
    // 检查字体是否已加载
    if (document.fonts.check(`1em "${fontFamily}"`)) {
      return;
    }
    
    // 创建字体对象
    const font = new FontFace(fontFamily, `url(${url})`, descriptors);
    
    // 加载字体
    const loadedFont = await font.load();
    
    // 添加到文档
    document.fonts.add(loadedFont);
    
    // 触发重绘
    document.body.classList.add('fonts-loaded');
    
    // 缓存字体（使用Cache API）
    const cache = await caches.open('font-cache');
    const response = await fetch(url);
    await cache.put(url, response);
    
    console.log(`Font ${fontFamily} loaded successfully`);
  } catch (error) {
    console.error(`Failed to load font ${fontFamily}:`, error);
    // 使用后备字体
    document.body.classList.add('fonts-failed');
  }
}

// 预加载关键字体
const preloadFonts = () => {
  const fonts = [
    { family: 'MyFont', url: '/fonts/myfont-regular.woff2', weight: 400 },
    { family: 'MyFont', url: '/fonts/myfont-bold.woff2', weight: 700 }
  ];
  
  fonts.forEach(font => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = font.url;
    link.as = 'font';
    link.type = 'font/woff2';
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  });
};
```

### 4.2 字体子集化

**Unicode Range子集化**：

```css
/* 只加载需要的字符范围 */
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont-latin.woff2') format('woff2');
  font-weight: 400;
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont-cyrillic.woff2') format('woff2');
  font-weight: 400;
  unicode-range: U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
}
```

**FontTools子集化脚本**：

```python
#!/usr/bin/env python3
"""
使用FontTools进行字体子集化
"""

import os
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options

def subset_font(input_path, output_path, text, **kwargs):
    """
    从字体中提取指定文本的字形
    """
    options = Options()
    options.desubroutinize = True
    options.flavor = 'woff2'
    options.layout_features = ['kern', 'liga', 'clig']
    
    # 加载字体
    font = TTFont(input_path)
    
    # 创建子集化器
    subsetter = Subsetter(options=options)
    subsetter.populate(text=text)
    
    # 执行子集化
    subsetter.subset(font)
    
    # 保存子集字体
    font.save(output_path)
    print(f"Subset saved to {output_path}")
    
    # 显示大小对比
    original_size = os.path.getsize(input_path)
    subset_size = os.path.getsize(output_path)
    reduction = (1 - subset_size / original_size) * 100
    print(f"Size reduction: {reduction:.2f}%")

# 使用示例
if __name__ == "__main__":
    # 英文常用字符
    latin_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;':\",./<>?"
    
    # 子集化字体
    subset_font(
        input_path="fonts/MyFont-Regular.ttf",
        output_path="fonts/MyFont-Regular-Latin.woff2",
        text=latin_text
    )
```

### 4.3 字体性能监控

```javascript
// 字体加载性能监控
const fontPerformance = {
  // 测量字体加载时间
  measureFontLoad: (fontFamily) => {
    const start = performance.now();
    
    // 等待字体加载完成
    return document.fonts.ready.then(() => {
      const end = performance.now();
      const duration = end - start;
      
      console.log(`Font ${fontFamily} loaded in ${duration.toFixed(2)}ms`);
      
      // 发送性能数据
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/metrics', JSON.stringify({
          type: 'font_load',
          fontFamily,
          duration,
          timestamp: Date.now()
        }));
      }
      
      return duration;
    });
  },
  
  // 检查字体是否可见
  checkFontVisibility: () => {
    const testString = 'Test String 123';
    const testElement = document.createElement('span');
    testElement.style.fontFamily = 'MyFont, Arial';
    testElement.style.position = 'absolute';
    testElement.style.visibility = 'hidden';
    testElement.textContent = testString;
    
    document.body.appendChild(testElement);
    
    const width = testElement.offsetWidth;
    const height = testElement.offsetHeight;
    
    // 如果宽度与Arial不同，说明字体已加载
    const isLoaded = width !== 146; // Arial的默认宽度
    
    document.body.removeChild(testElement);
    
    return isLoaded;
  }
};
```

## 五、CSS性能优化

### 5.1 关键CSS提取与内联

**Critical CSS工具**：

```javascript
// critical.js - 提取关键CSS
const critical = require('critical');

critical.generate({
  base: 'dist/',
  src: 'index.html',
  css: ['dist/css/main.css'],
  dimensions: [
    { width: 320, height: 480 },  // 移动端
    { width: 768, height: 1024 }, // 平板
    { width: 1280, height: 800 }  // 桌面
  ],
  inline: true,
  extract: true,
  penthouse: {
    blockJSRequests: false,
    timeout: 30000
  }
}).then(output => {
  console.log('Generated critical CSS');
}).catch(err => {
  console.error('Error generating critical CSS:', err);
});
```

**手动关键CSS策略**：

```html
<!-- 内联关键CSS -->
<style>
  /* 首屏关键样式 */
  .hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.9);
  }
</style>

<!-- 异步加载非关键CSS -->
<link rel="preload" href="/css/non-critical.css" as="style" onload="this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="/css/non-critical.css"></noscript>

<!-- 使用media属性实现CSS优先级 -->
<link rel="stylesheet" href="/css/above-fold.css">
<link rel="stylesheet" href="/css/below-fold.css" media="print" onload="this.media='all'">
```

### 5.2 减少重排与重绘

**性能友好的CSS写法**：

```css
/* 避免强制同步布局 */
.bad-example {
  width: element.offsetWidth; /* 避免在循环中访问布局属性 */
  height: element.offsetHeight;
}

/* 使用transform和opacity实现动画 */
.good-animation {
  /* 使用transform代替top/left */
  transform: translateX(100px);
  /* 使用opacity代替visibility */
  opacity: 0.8;
  /* 使用will-change提示浏览器 */
  will-change: transform, opacity;
}

/* 避免布局抖动 */
.container {
  /* 使用contain属性限制布局影响 */
  contain: layout style paint;
  /* 或使用content-visibility */
  content-visibility: auto;
  contain-intrinsic-size: 0 500px;
}

/* 优化选择器性能 */
/* 避免过度限定 */
.nav .item .link .icon { /* 太深 */ }
.icon { /* 更好 */ }

/* 避免通配选择器 */
* { /* 性能差 */ }
.nav-item { /* 更好 */ }
```

**JavaScript优化布局性能**：

```javascript
// 避免强制同步布局
function badLayoutPattern() {
  const elements = document.querySelectorAll('.item');
  
  // 强制同步布局 - 性能差
  elements.forEach(el => {
    const width = el.offsetWidth; // 触发重排
    el.style.width = `${width * 2}px`;
  });
}

function goodLayoutPattern() {
  const elements = document.querySelectorAll('.item');
  
  // 读取所有布局信息
  const widths = Array.from(elements).map(el => el.offsetWidth);
  
  // 然后批量写入
  elements.forEach((el, i) => {
    el.style.width = `${widths[i] * 2}px`;
  });
}

// 使用requestAnimationFrame优化
function optimizedAnimation() {
  const element = document.querySelector('.animated');
  let position = 0;
  
  function animate() {
    position += 1;
    element.style.transform = `translateX(${position}px)`;
    requestAnimationFrame(animate);
  }
  
  requestAnimationFrame(animate);
}

// 使用Intersection Observer优化滚动性能
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // 元素进入视口
      entry.target.classList.add('visible');
    } else {
      // 元素离开视口
      entry.target.classList.remove('visible');
    }
  });
}, {
  threshold: 0.1,
  rootMargin: '50px'
});

// 观察需要优化的元素
document.querySelectorAll('.scroll-item').forEach(el => {
  observer.observe(el);
});
```

### 5.3 CSS压缩与优化

**PostCSS配置**：

```javascript
// postcss.config.js
module.exports = {
  plugins: [
    require('postcss-preset-env')({
      stage: 3,
      features: {
        'nesting-rules': true,
        'custom-media-queries': true,
        'custom-properties': {
          preserve: false
        }
      }
    }),
    require('cssnano')({
      preset: ['advanced', {
        discardComments: { removeAll: true },
        reduceIdents: false,
        zindex: false
      }]
    }),
    require('autoprefixer')({
      grid: true,
      flexbox: 'no-2009'
    }),
    require('postcss-image-set-polyfill')
  ]
};
```

**CSS性能检测工具**：

```javascript
// 检测CSS性能问题
const cssPerformance = {
  // 检查未使用的CSS
  checkUnusedCSS: () => {
    const styles = document.styleSheets;
    const unusedRules = [];
    
    Array.from(styles).forEach(style => {
      try {
        const rules = Array.from(style.cssRules || style.rules || []);
        rules.forEach(rule => {
          if (rule.type === CSSRule.STYLE_RULE) {
            const selector = rule.selectorText;
            try {
              if (!document.querySelector(selector)) {
                unusedRules.push({
                  selector,
                  cssText: rule.cssText
                });
              }
            } catch (e) {
              // 忽略无效选择器
            }
          }
        });
      } catch (e) {
        // 跨域样式表
      }
    });
    
    return unusedRules;
  },
  
  // 计算CSS文件大小
  calculateCSSSize: () => {
    const styles = document.querySelectorAll('style, link[rel="stylesheet"]');
    let totalSize = 0;
    
    styles.forEach(style => {
      if (style.tagName === 'STYLE') {
        totalSize += style.textContent.length;
      } else if (style.sheet) {
        try {
          const rules = style.sheet.cssRules || style.sheet.rules;
          Array.from(rules).forEach(rule => {
            totalSize += rule.cssText.length;
          });
        } catch (e) {
          // 跨域样式表
        }
      }
    });
    
    return totalSize;
  }
};
```

## 六、JavaScript性能优化

### 6.1 Web Worker应用

**计算密集型任务**：

```javascript
// worker.js - 计算斐波那契数列
self.addEventListener('message', function(e) {
  const { type, data } = e.data;
  
  switch (type) {
    case 'calculate':
      const result = fibonacci(data.n);
      self.postMessage({
        type: 'result',
        data: { result, input: data.n }
      });
      break;
      
    case 'process-data':
      const processedData = processData(data.largeArray);
      self.postMessage({
        type: 'processed',
        data: processedData
      });
      break;
  }
});

function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

function processData(data) {
  // CPU密集型数据处理
  return data.map(item => {
    return {
      ...item,
      processed: heavyComputation(item)
    };
  });
}

// 主线程使用Worker
class WebWorkerManager {
  constructor() {
    this.workers = new Map();
    this.taskQueue = [];
  }
  
  createWorker(id, scriptPath) {
    const worker = new Worker(scriptPath);
    
    worker.onmessage = (e) => {
      this.handleWorkerMessage(id, e.data);
    };
    
    worker.onerror = (e) => {
      console.error(`Worker ${id} error:`, e);
    };
    
    this.workers.set(id, worker);
    return worker;
  }
  
  postMessage(workerId, message) {
    const worker = this.workers.get(workerId);
    if (worker) {
      worker.postMessage(message);
    }
  }
  
  handleWorkerMessage(workerId, message) {
    // 处理Worker返回的消息
    switch (message.type) {
      case 'result':
        this.handleResult(message.data);
        break;
      case 'error':
        this.handleError(message.error);
        break;
    }
  }
  
  terminateAll() {
    this.workers.forEach(worker => worker.terminate());
    this.workers.clear();
  }
}

// 使用示例
const workerManager = new WebWorkerManager();
workerManager.createWorker('calculator', 'calculator-worker.js');
workerManager.postMessage('calculator', {
  type: 'calculate',
  data: { n: 40 }
});
```

### 6.2 requestIdleCallback优化

```javascript
// 智能任务调度器
class TaskScheduler {
  constructor(options = {}) {
    this.options = {
      timeout: 2000,
      ...options
    };
    
    this.taskQueue = [];
    this.isProcessing = false;
    this.frameDeadline = 0;
  }
  
  // 添加任务
  addTask(task, priority = 'low') {
    const taskWithPriority = {
      task,
      priority,
      addedTime: performance.now()
    };
    
    this.taskQueue.push(taskWithPriority);
    
    // 根据优先级排序
    this.taskQueue.sort((a, b) => {
      const priorityOrder = { high: 0, medium: 1, low: 2 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });
    
    if (!this.isProcessing) {
      this.processQueue();
    }
  }
  
  // 处理任务队列
  processQueue() {
    if (this.taskQueue.length === 0) {
      this.isProcessing = false;
      return;
    }
    
    this.isProcessing
```

## 相关术语

[[GraphQL从入门到精通]]、[[Next.js全栈开发实战]]、[[WebAssembly完全指南]]、[[现代前端工程化完全指南]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
