---
title: "PWA 渐进式 Web 应用"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# PWA 渐进式 Web 应用

> 📌 **导航**：本文是 **PWA 渐进式 Web 应用** 词条，属于 frontend-concepts 术语集。相关枢纽：[[前端工程化核心概念]]、[[前端工程化]]。

## 定义

**一句话定义：** PWA 让网页具备原生应用体验——离线可用、可添加到桌面、能收推送。它是一套渐进增强策略：有 Service Worker 就增强，没有也照样能当普通网站用；manifest 提供"像 App"的外壳（名称、图标、启动方式），Service Worker 提供"能离线"的内核。

**通俗类比：** 像给网站穿一件原生 App 的外衣：入口、图标、全屏外观由 manifest 决定，能不能断网打开由 Service Worker 决定。

## 为什么需要它

用户感知的差距在于：网页每次都要走网络、没有桌面入口、关掉就没了。PWA 用缓存把首屏之后变成"本地读取"，用 manifest 换来主屏幕图标与 standalone 显示，用 Service Worker 换来离线兜底与推送能力，而代价远小于为同一功能重写一套原生客户端。

## 核心机制

| 组成 | 负责什么 | 关键字段 / 事件 |
|---|---|---|
| `manifest.json` | 应用身份与显示形态 | `name` / `short_name` / `start_url` / `display: standalone` / `theme_color` / `icons`（192 与 512 两档） |
| Service Worker | 拦截请求、管理缓存 | `install` 预缓存资源清单、`fetch` 命中缓存否则回源 |
| 注册代码 | 把 SW 挂上 | `"serviceWorker" in navigator` 判存在后 `register("/service-worker.js")` |
| 渐进增强 | 能力缺失时退回普通网页 | 无 SW 时功能不成立但页面仍可用 |

- **`install` 阶段决定"离线时手里有什么"**：`caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))` 把 `/`、`index.html`、样式与脚本预写进名为 `v1` 的缓存；这一步没完成，离线打开就是空白页。
- **`fetch` 的"缓存优先、未命中回源"是最短路径而非唯一策略**：`caches.match(event.request).then(r => r || fetch(event.request))` 对静态资源合适，对会变的接口就意味着脏读风险——缓存口径要按资源类型分开决策。
- **能力与体积无关，与运行时有关**：PWA 不要求换框架、不要求打包器支持，产物仍是常规 bundle，因此它是 [[前端构建优化策略]] 之外的另一层——那一层让首次下载更快，这一层让"下一次"和"没网时"可用。

## 具体示例

```javascript
// service-worker.js
const CACHE_NAME = "v1";
const ASSETS = ["/", "/index.html", "/style.css", "/app.js"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(ASSETS)));
});
self.addEventListener("fetch", (e) => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
// 注册：if ("serviceWorker" in navigator) navigator.serviceWorker.register("/service-worker.js");
```

## 何时用与何时不用

- **用**：网络差或使用碎片化的内容型站点（阅读、报表、活动页），以及要有桌面入口却不想维护原生壳的场景。
- **不用**：强实时、强一致的数据面板（缓存优先会读到旧数据，代价大于收益）；要原生硬件能力或商店分发时那是 [[移动开发概览]] 那条线；只想首屏快一点就先做构建与加载优化。

## 优劣与代价

✅ 一套代码同时拿到离线、桌面入口与推送，不需要额外客户端。
✅ 渐进增强使失败面小：不支持的环境退化成普通网站而不是白屏。
⚠️ 缓存即负债：`CACHE_NAME` 不递增，旧客户端会一直拿着旧资源，升级与清理要自己写。
⚠️ 离线越强，"用户看到的是哪个版本"越难回答，排障要多问一句"你的缓存是哪次装的"。

## 与相关概念的区别

- **vs Service Worker**：SW 是实现技术（可拦截请求的浏览器工作线程），PWA 是由它加 manifest 组成的产品形态；本条讲后者怎么用前者。
- **vs [[资源加载优化]]**：那一条管首次与后续加载怎么更快到达，本条管到达之后能不能不带网络上。
- **vs [[缓存策略]]**：服务端与 HTTP 缓存的通用口径在那条，本条的缓存是浏览器内 Cache API 的手工版本。

## 常见误区

- 以为加了 manifest 图标就是 PWA，忽略离线能力取决于 Service Worker。
- 把 `fetch` 的缓存优先当成放之四海的策略，用到会变的数据接口上。

## 面试速答

> 🎯 PWA = manifest（名称/图标/standalone）+ Service Worker（install 预缓存、fetch 缓存优先否则回源）+ 渐进增强：有 SW 就离线可用可加桌面，没有也能当普通网站跑。核心是离线与入口。

## 相关术语

[[前端工程化核心概念]]、[[前端工程化]]、[[前端构建优化策略]]、[[资源加载优化]]、[[Web性能优化]]、[[Core Web Vitals]]、[[缓存策略]]、[[内容分发网络]]、[[移动开发概览]]、[[JavaScript 构建工具（Webpack 与 Vite）]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇承接原《前端工程化核心概念》PWA（渐进式 Web 应用）一节，原稿的 manifest 片段与 SW 注册代码压缩为上表与一段示例；原稿该节未展开缓存版本升级、推送权限与更新流程，此处不做推测性补写。
