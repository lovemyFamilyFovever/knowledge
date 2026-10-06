---
title: "JavaScript 构建工具（Webpack 与 Vite）"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# JavaScript 构建工具（Webpack 与 Vite）

> 📌 **导航**：本文是 **JavaScript 构建工具（Webpack 与 Vite）** 词条，属于 frontend-concepts 术语集。相关枢纽：[[前端工程化核心概念]]、[[前端工程化]]。

## 定义

**一句话定义：** 构建工具把散落的前端资源（JS、CSS、图片）变成浏览器能高效加载的产物；Webpack 的核心是"始终打包"——从 entry 起依赖图，输出带哈希的 bundle；Vite 的核心是"开发态不打包"——按原生 ES Modules 逐文件即时转换，生产才用 Rollup 打包。

**通俗类比：** Webpack 像中央厨房，所有菜先做好再上桌；Vite 像现点现做，浏览器要哪个模块就即时端哪个，所以开餐几乎不用等。

## 为什么需要它

一个页面依赖成百上千个文件，浏览器不会自己做依赖解析、语法降级与哈希命名。Webpack 用打包解决"该发给用户什么"，代价是冷启动要把整张依赖图先构建一遍，大项目可达几十秒；Vite 用原生 ESM 绕开这一步。

## 核心机制

| 维度 | Webpack | Vite |
|---|---|---|
| 开发态 | 全量打包后起 dev server，改动要重走依赖图 | 不打包，浏览器按 `import` 逐个请求、服务端实时转换 |
| 产物 | 自有 chunk 机制（`splitChunks`） | 生产走 Rollup（`rollupOptions.manualChunks`） |
| 非 JS 资源 | `module.rules` + loader 链 | 内置能力与插件（React/TS 交给 `@vitejs/plugin-react` 等） |
| 扩展与配置成本 | plugin 生命周期介入构建，灵活但繁 | plugin 体系、配置项收敛，开箱即用 |

- **loader 与 plugin 不是一回事**：loader 管"单个文件怎么解析"（`babel-loader` 转译 JSX、`css-loader` 解析 CSS、`asset/resource` 处理图片），plugin 管"整次构建的哪个时机插一脚"（生成 HTML、抽出 CSS、注入常量），把拆包需求写成 loader 是常见错配。
- **Vite 的快只属于开发态**：浏览器自己发请求，Vite 只回答被请求的那个文件；生产仍要一次打完整产物，所以"Vite 比 Webpack 快"必须补一句"快在哪一段"。
- **两者的拆包是同一件事的两种写法**：`splitChunks` 与 `manualChunks` 都在切 vendor 与路由块，粒度取舍见 [[前端构建优化策略]]。

## 具体示例

```javascript
// webpack.config.js（骨架）
module.exports = {
  entry: { main: "./src/index.js" },
  output: { filename: "[name].[contenthash].js", clean: true },
  module: { rules: [
    { test: /\.jsx?$/, exclude: /node_modules/, use: "babel-loader" },
    { test: /\.css$/, use: ["style-loader", "css-loader"] },
  ] },
  optimization: { splitChunks: { chunks: "all" } },
};
// vite.config.js：开发态不打包，生产才交给 Rollup
export default defineConfig({ plugins: [react()],
  build: { rollupOptions: { output: { manualChunks: { vendor: ["react"] } } } } });
```

## 何时用与何时不用

- **用 Vite**：新项目、以开发启动与热更新速度优先，目标浏览器不含需要走开发模式的旧版本。
- **用 Webpack**：历史项目已有整套 loader/plugin，或需要构建期精细介入。
- **都不用**：单页静态站一个 HTML 加 CDN 就够时，加工具只是把简单问题复杂化（整体判据见 [[前端工程化]]）。

## 优劣与代价

✅ Webpack 生态与配置面最全，几乎任何构建期需求都有对应 plugin。
✅ Vite 把开发反馈循环压到接近即时，配置量显著下降。
⚠️ Webpack 的配置复杂度本身就是维护成本，loader 顺序与 exclude 写错很难归因。
⚠️ Vite 开发模式依赖原生 ESM，旧浏览器兼容要挪到产物或 polyfill 层。

## 与相关概念的区别

- **vs [[代码规范与转换工具链（Babel · ESLint · PostCSS）]]**：本条管"文件怎么拼成产物"，那条管"单个文件的语法与质量"，`babel-loader` 是接缝。
- **vs [[构建流水线与 CI-CD 工具]]**：那条解"产物怎么自动构建并上线"，本条解"本地产物长什么样"。
- **vs [[包管理器与构建工具]]**：那条解依赖从哪来，本条解依赖怎么变成 bundle。

## 常见误区

- 以为 Vite 开发快是因为"打包打得更有效率"，实际是开发态根本不打包。
- 以为只要用了构建器就有 tree-shaking，忽略它依赖 ES Modules 的可静态分析结构。
- 把处理 CSS 的需求写成一条 plugin，而它本该是一条 loader 链。

## 面试速答

> 🎯 Webpack 始终打包：entry 起依赖图，loader 管单文件、plugin 管构建时机，配置灵活但重。Vite 开发态用原生 ESM 按需转换、几乎零启动，生产走 Rollup。差别在"打包发生在哪一段"。

## 相关术语

[[前端工程化核心概念]]、[[前端工程化]]、[[代码规范与转换工具链（Babel · ESLint · PostCSS）]]、[[前端构建优化策略]]、[[JavaScript 模块化（CommonJS·ES Modules·AMD）]]、[[包管理器与构建工具]]、[[构建流水线与 CI-CD 工具]]、[[JavaScript 基础核心概念]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。本篇承接原《前端工程化核心概念》Webpack 与 Vite 两节，原稿四块示例（webpack 全量配置、entry/loader/plugin/拆包概念清单、vite 配置与开发态注释段）压缩为上表与一段骨架配置；`asset/resource` 取代 `file-loader` 属 Webpack 5 行为，建议对照官方文档复核。
