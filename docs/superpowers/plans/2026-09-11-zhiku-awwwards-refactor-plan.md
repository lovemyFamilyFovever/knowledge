# 知库 UI Awwwards 重构 · 实现计划

**日期**：2026-09-11
**规格来源**：`docs/superpowers/specs/2026-09-11-zhiku-awwwards-refactor-design.md`
**范围**：Canvas 工作区 `qwenwork/canvas/mtvq30t7ur2d66tl/`，重塑 3 屏（Home · Workbench · Reading）
**不做**：本计划只覆盖"设计稿阶段"；生产代码迁移另开 `2026-XX-XX-zhiku-awwwards-migration-plan.md`

## 前置约定

- 所有新增依赖**本地化**，零外链 CDN（对齐 AGENTS.md 不变量 1、7）
- 每个 Phase 结束都是一个可回退点；出错只回退该 Phase
- 每个 Phase 完成后 `check_design_quality` 保持 P0=0；P1 允许在 Phase 结束前存在，最后统一清
- Token 敏感：Phase 内部避免重复大块 Write；优先小 Edit + Bash 增量拼接

## Phase 0 · 本地依赖就位（预估 3–5 分钟）

**目标**：把 GSAP 核心、ScrollTrigger、Space Grotesk 子集字体拉到工作区 `vendor/`，并验证大小 + 许可。

- [ ] **0.1** 建目录 `vendor/`：`mkdir -p qwenwork/canvas/mtvq30t7ur2d66tl/vendor`
- [ ] **0.2** 下载 `gsap.min.js`：
  ```
  curl -sSfLo vendor/gsap.min.js https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js
  ```
  校验：文件 25–35 KB；首行有 `/*!GSAP`；不含 `http://` 外链。
- [ ] **0.3** 下载 `ScrollTrigger.min.js`：
  ```
  curl -sSfLo vendor/ScrollTrigger.min.js https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrollTrigger.min.js
  ```
  校验：25–30 KB。
- [ ] **0.4** 下载 Space Grotesk variable woff2（Latin subset，Google Fonts）：
  ```
  curl -sSfLo vendor/space-grotesk-var.woff2 \
    "https://fonts.gstatic.com/s/spacegrotesk/v16/V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj6Pf1U.woff2"
  ```
  校验：30–45 KB；`file vendor/space-grotesk-var.woff2` 报 `Web Open Font Format`。
  **许可检查**：SIL OFL 1.1（Google Fonts 主页明确标注）。若不确定 → 退回"不加新字体，靠 Georgia + 极限字阶"，同步改 spec § 9 风险表。
- [ ] **0.5** 在 `vendor/` 下写一份 `README.md`：三条下载命令 + 许可摘要 + 校验大小；防止未来重下载走错版本。
- [ ] **0.6** `.gitignore` 检查：`qwenwork/` 已在仓库根 `.gitignore` 屏蔽，`vendor/` 不需要额外配置。
- [ ] **0.7** Phase 0 验收：4 个文件均在 `vendor/`，`ls -la vendor/` 大小合理，无 `http://` 出现在 index.html。

**回退**：`rm -rf vendor/`。

---

## Phase 1 · 底座（tokens + motion.js + cursor.js + CSS utility）

**目标**：把新字阶、`--hairline / --glow-accent / --wash-hero` token、motion.js 助手、cursor.js 都铺到位。这一步之后，任何一屏只需要贴 `data-*` 属性就能启动动效。

- [ ] **1.1** 在 `index.html` `:root` 中追加：
  ```
  --font-display-latin: "Space Grotesk Variable", "Georgia", serif;
  --hairline: color-mix(in oklab, var(--seed-fg), transparent 92%);
  --glow-accent: 0 0 0 1px color-mix(in oklab, var(--acc), transparent 65%),
                 0 8px 24px color-mix(in oklab, var(--acc), transparent 88%);
  --wash-hero: color-mix(in oklab, var(--acc), var(--seed-bg) 88%);
  --fs-hero: clamp(4rem, 12vw, 11rem);
  --fs-display: clamp(2rem, 4.5vw, 3.5rem);
  --fs-h2: clamp(1.25rem, 2vw, 1.75rem);
  --fs-label: 11.5px;
  ```
- [ ] **1.2** 追加 `@font-face`：`src: url("./vendor/space-grotesk-var.woff2") format("woff2-variations")`，`font-weight: 300 700`。
- [ ] **1.3** 在 `<body>` 结束前追加 `<script>` 块（3 个文件），全部 `defer`：
  ```
  <script src="./vendor/gsap.min.js" defer></script>
  <script src="./vendor/ScrollTrigger.min.js" defer></script>
  <script src="./motion.js" defer></script>
  <script src="./cursor.js" defer></script>
  ```
- [ ] **1.4** 新建 `motion.js`（约 200 行），暴露 6 个助手：
  ```
  Motion.revealGroup(container, {child, stagger, y, duration})
  Motion.countUp(el, {to, duration, ease})
  Motion.magnetize(el, {strength, ease})
  Motion.lineMaskReveal(el, {lineStagger, duration})
  Motion.scrubUnderline(el, {start, end})
  Motion.refresh()   // ScrollTrigger.refresh() 封装
  ```
  内部先检查 `matchMedia('(prefers-reduced-motion: reduce)').matches`，命中则所有函数变成 no-op。
  DOMContentLoaded 时扫描 `[data-reveal]` `[data-counter]` `[data-magnetic]` `[data-line-mask]` `[data-underline]` 自动挂载。
- [ ] **1.5** 新建 `cursor.js`（约 60 行）：
  - 一个 dot（8px `--acc`）+ 一个 ring（24px，`--acc` 描边 1px）
  - ring 用 lerp 0.15 跟随；dot 无延迟
  - `document.querySelectorAll('a,button,[data-cursor]')` hover 时 ring scale 1.8，可选显示 `[data-cursor-label]` 内容
  - `@media (pointer: coarse)` 与 `prefers-reduced-motion: reduce` 直接不初始化
- [ ] **1.6** 追加 CSS：`.progress-bar` sticky 顶部；`.marquee-track` 用 CSS `animation: marquee 60s linear infinite` + `:hover{animation-play-state:paused}`；`.kinetic-underline` 静态 fallback（无 JS 时 hover 从 0%→100% background-size）。
- [ ] **1.7** 追加 CSS：`.hero-mask` 用 `clip-path: inset(0 0 100% 0)` + `transition: clip-path 1.2s cubic-bezier(0.16,1,0.3,1)`，`[data-in="true"]` 时 `inset(0 0 0 0)`。
- [ ] **1.8** Phase 1 验收：三屏还没改，但加载 index.html 无 console error；motion.js / cursor.js 各自暴露 `window.Motion` / `window.Cursor`；`prefers-reduced-motion` 强制下无 JS 动效。

**回退**：删 `motion.js` `cursor.js`；`<script>` 三行；`@font-face`；`:root` 追加 token 单独 `git diff` 手动 revert 或直接删。

---

## Phase 2 · Home 重塑

**目标**：把 `M.home()` 模板函数替换成新 hero + 域卡 + marquee + counter 的完整版本。

- [ ] **2.1** 在 `:root` 加 `.hero-mask` 与 `.hero-word` 类，`--fs-hero` 与 display 字体。
- [ ] **2.2** 重写 `M.home()`（约 4 KB 字符串），结构：
  - `<div class="hero" data-preview-theme="light">` 60vh 高，内含 `.hero-left`（"知库"两字，各 `<span class="hero-word" data-reveal>`） + `.hero-right`（mascot SVG，`data-parallax data-depth="0.5"`）
  - `<p class="hero-tagline"><span data-word>把</span><span data-word>散落</span>...</p>`
  - `<div class="kpi-strip">` 4 个数字 `<span data-counter="1479">`
  - `<div class="dom-cards">` 8 列，每卡 `<article class="dom-card" data-magnetic>`
  - `<div class="marquee-track">` 7 条最近更新
- [ ] **2.3** 在 CSS 里补 `.dom-cards{grid-template-columns:repeat(8,1fr)}` 与响应式回退（1080px → 4 列，720px → 2 列）。
- [ ] **2.4** 让 `motion.js` 首屏 mount 时立刻触发 hero 的 `clip-path` reveal（`data-in=true`）+ 逐词 stagger。
- [ ] **2.5** Phase 2 验收：
  - Canvas 里 Home 首屏进入 → "知库"两字从下方升起 + mascot parallax 跟随
  - 4 个 KPI counter 首次进视口触发一次
  - 8 列域卡 hover 有磁吸 + glow
  - `prefers-reduced-motion` 下 hero 静态呈现（无 clip-path 动画）
  - 关 JS 页面仍完整

**回退**：把 `M.home()` 恢复成 v0.4 的字符串。

---

## Phase 3 · Workbench 重塑

**目标**：`M.workbench()` 里的 `.tree` `.doclist` `.article-inner` `.rail` 加动效属性；不改结构。

- [ ] **3.1** 在 `M.tree()`（现在通过 `tpl-tree-dom` 生成）的 `<div class="dom">` 加 `data-reveal data-stagger="40"`；`.sub` 保留 v0.4。
- [ ] **3.2** 在 `tpl-doc-item` 生成 `<div class="doc">` 时加 `data-reveal`；active 项加 `.doc.active::before` 呼吸 keyframe（2s loop，reduced-motion 关）。
- [ ] **3.3** `M.workbench()` 的文章 HTML 里：
  - 每个 `<p>` 外层包 `.line-mask` 容器（line-mask reveal 需要行单元）
  - copy 按钮加 `data-ripple="copy"`；star 按钮加 `data-bounce`
- [ ] **3.4** 在 rail 面板里给 `.toc-item` 加 `data-toc-anchor` 与 `Motion.scrubUnderline` 绑定；article scroll 时 active underline 跟随。
- [ ] **3.5** 顶栏搜索：`/` 聚焦时给 `.search` 加 `.is-focusing` class（CSS 呼吸 3px ring）。
- [ ] **3.6** Phase 3 验收：
  - 三栏之间 hover 有 --dh 竖条 scaleX；active 呼吸
  - 切换文档时 line-mask reveal 肉眼可辨
  - copy 按钮涟漪、star 弹跳迸星
  - TOC underline 跟随滚动
  - Reduced-motion 下这些全 static

**回退**：模板字符串逐段替换成 v0.4 版。

---

## Phase 4 · Reading 重塑

**目标**：`M.reading()` 里加进度条、drop cap、H2 underline、mermaid reveal、prev/next footer。

- [ ] **4.1** 在文章容器顶部加 `<div class="progress-bar" data-progress-of=".article">`，`motion.js` 里 ScrollTrigger `scrub:true` 更新 CSS 变量 `--progress: 0..1`，CSS `width: calc(var(--progress) * 100%)`。
- [ ] **4.2** `.article-inner p:first-of-type::first-letter` 加 drop cap 规则（`font: 700 5em/0.85 var(--font-display-latin); float: left; margin: 4px 8px 0 0; color: var(--acc)`）。
- [ ] **4.3** 每个 H2 底部加 `<span class="kinetic-underline" data-underline>`；`motion.js` 挂 scrub。
- [ ] **4.4** `.mermaid` 卡加 `data-scale-in`；`motion.js` 首次进视口 scale 0.95→1 + blur 4→0。
- [ ] **4.5** `.quote` hover 加 scaleY 生长；`.wikilink` hover 用 CSS `::after` 显示 tooltip（数据来自现有 `data-target-doc` 属性，先 mock）。
- [ ] **4.6** 文末加 `<footer class="read-done">`：一张 mascot 挥手 96 px + 前后文档 nav；`data-reveal` 触发。
- [ ] **4.7** Phase 4 验收：
  - 进度条顶部 1px 满屏跟滚
  - 首字下沉正确
  - H2 底条随滚动填充
  - mermaid 卡有 scale-in
  - 文末 mascot 挥手

**回退**：把 `M.reading()` 恢复成 v0.4 字符串。

---

## Phase 5 · 质量门 + Nudges + 交付

- [ ] **5.1** `check_design_quality`：目标 P0=0 / P1=0。P2 只保留 aurora + 对照 emoji 两项豁免（沿用上一轮）；如新增 P1，逐条修。
- [ ] **5.2** 刷新 set_nudges：Appearance 4 preset（Light/Dark/Editorial/High Contrast）+ Radius + Motion Intensity（新加，控制 stagger 时长 0.5× / 1× / 1.5×，通过 `--motion-scale` CSS 变量传 GSAP）。
- [ ] **5.3** `complete_design_execution`：拿到 `readyToPresent=true`。
- [ ] **5.4** 报告用户 3 屏效果，附文件路径与新增依赖清单。
- [ ] **5.5** 询问是否 commit 设计文档 + 是否进入生产迁移计划。

**回退**：`check_design_quality` 报错 → 修 → 重跑；`complete_design_execution` 不 ready → 按提示补。

---

## 时间/复杂度评估

| Phase | 预计 token 消耗（保守） | 主要成本 |
|---|---|---|
| 0 | 3–5 K | 下载 3 个文件 + 大小校验 |
| 1 | 25–35 K | 写 motion.js 200 行 + cursor.js 60 行 + CSS 追加 |
| 2 | 20–25 K | 重写 Home 模板 + CSS |
| 3 | 15–20 K | 加 data-* + motion 挂钩 |
| 4 | 15–20 K | Reading 模板重写 + 进度条 |
| 5 | 8–12 K | 质量循环 + Nudges + 交付 |
| **合计** | **85–120 K** |  |

**Token 保护**：
- 每个 Phase 用最小 Edit 增量改，不整段 Write 大文件
- 若中途任何 Phase 报错，立即停下汇报，不硬推
- 每 Phase 结束都跑一次 `wc -c` 看体积变化，避免膨胀回 v0.4 水平

## 完成定义

- [ ] Home / Workbench / Reading 三屏在 Canvas 中肉眼可辨"活着"（hero mask、counter、stagger、magnetic、kinetic underline 都能演示）
- [ ] `prefers-reduced-motion: reduce` 下所有动效关闭但视觉不破
- [ ] 关 JS 页面完整可读（无空占位）
- [ ] `check_design_quality` P0=0 / P1=0
- [ ] `complete_design_execution` `readyToPresent=true`
- [ ] 文件总大小 ≤ 200 KB（含 vendor 目录则 ≤ 320 KB）
- [ ] 无新增外部 CDN 引用（`grep -E "https?://" index.html motion.js cursor.js` 只在 vendor README 里出现）

---

**下一步**：本计划评审通过后，从 Phase 0 开始按序执行，每完成一个 Phase 汇报一次并等确认，避免"一口气推完发现方向错"。
