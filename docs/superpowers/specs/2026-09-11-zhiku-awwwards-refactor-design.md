# 知库 UI Awwwards 重构设计（3 屏深度重塑）

**日期**：2026-09-11
**参与者**：lxc（作者本人）+ 千问办公
**状态**：待评审
**取代**：`qwenwork/canvas/mtvq30t7ur2d66tl/index.html` v0.4（保留品牌语言，重塑 3 屏）

## 1. 背景与目标

v0.4 高保真设计稿在 Canvas 上评审后，作者的判断是"UI 还是太丑"。用两个正交维度精确描述：

1. **静态感太强**：整个设计稿"完美"但没呼吸；hover 只有色变，滚动没有编排。
2. **层级、密度、排印不到位**：字阶对比不够狠，留白不够自信，信息层次平铺。

作者**保留**：翡翠绿/薄荷荧光色板、aurora + grain + glass、7 域 hue 色相、内联 SVG 精灵、阅读者 mascot、无 emoji 政策。
作者**要求重构**：动效栈、排版尺度、密度节奏。

**范围**：三屏深度重塑 —— Workbench 主屏 · Home 总览 · Reading 阅读页。其余 10 屏（shell 状态组件、搜索、stats、tags、inbox、icon-sheet、mascot-board、illustration-board、narrow、Dark workbench）沿用 v0.4 现状，不做视觉断代。

**不做**：数据流、后端、API 完全不动；`content/` 与 `indexes/` 一切如旧；AGENTS.md 全部不变量原样遵守。

## 2. 保留 vs 修改

| 维度 | 处理 |
|---|---|
| 色板（`--seed-*` / `--acc` / `--acc2` / 7 域 hue） | **保留**，扩展三个层级 token |
| aurora / grain / glass 玻璃光斑 | **保留**，收紧到只出现在 hero 与 shell 外的背景层 |
| 阅读者 mascot + 130 内联 SVG 精灵 | **保留**，加动效 |
| 无 emoji / 无外链 CDN / 语料不出网 | **保留**（AGENTS.md 不变量 1、7） |
| Light / Dark 双主题 | **保留**，通过 `--seed-*` patch |
| Workbench 三栏 + 右 rail 结构 | **保留**，只换皮不换骨 |
| 字阶、留白、层级 | **重塑**（更极端对比） |
| 动效栈 | **新增**（GSAP + ScrollTrigger 本地化） |
| Latin display 字体 | **新增**（子集本地化） |

## 3. 视觉系统升级

### 3.1 字阶（新，三档极端对比）

| 层级 | 大小 | 字体 | 用途 |
|---|---|---|---|
| Hero display | `clamp(4rem, 12vw, 11rem)` | Space Grotesk Variable 700 / 中文 Georgia 600 | Home 首屏巨型字 |
| Section title | `clamp(2rem, 4.5vw, 3.5rem)` | Space Grotesk Variable 500 | 屏内小节标题 |
| H2 阅读正文 | `clamp(1.25rem, 2vw, 1.75rem)` | Georgia 600 | 保留 v0.4 尺寸，仅字距收紧到 `-0.02em` |
| Body | `15.5px / 1.75` | 现有 sans | 保留 |
| Mono label | `11.5px / 0.14em caps` | Consolas 500 | 数字/时间/域标签 |

**字距**：display `-0.03em`、h2 `-0.02em`、body normal、mono `+0.14em`。

**新增 CSS token**（放在 `:root`，通过 `[data-preview-theme="dark"]` 或 `html[data-theme="dark"]` 覆盖）：

- `--font-display-latin: "Space Grotesk Variable", "Georgia", serif`
- `--hairline`: 极淡分隔线（`color-mix(in oklab, var(--seed-fg), transparent 92%)`），滚动/hover 时被 `--acc` 点亮
- `--glow-accent`: hover 光晕（`0 0 0 1px color-mix(in oklab, var(--acc), transparent 65%), 0 8px 24px color-mix(in oklab, var(--acc), transparent 88%)`），替代重阴影
- `--wash-hero`: hero 底层的柔和翡翠晕（`color-mix(in oklab, var(--acc), var(--seed-bg) 88%)`），比 `--blob1` 更浓更聚焦

### 3.2 留白节奏

- section 外边距 `24px → 48px`
- 卡片内 padding `12px → 20px`
- Workbench 三栏 gutter `0 → 8px`
- Home 域卡列数 `4 → 8`（含"新建域"占位卡）
- 右 rail 段落条目上下 padding `3px → 6px`

### 3.3 域色相（`--dh-*`）扩展

现有 7 域 hue 只染 `.dom-glyph`。新增 5 个使用位：
- 左树项 hover 时**左侧竖条**从 0 scaleX→1
- 文档 active 项**左侧 3px 条带呼吸动画**（opacity 0.7↔1，2s loop）
- 面包屑末段文字色
- Home 域卡 hover 光晕中心色
- Reading H2 底部的 kinetic underline 填充色（当该文档所属域已知时）

## 4. 动效栈与本地依赖

**硬约束**：AGENTS.md 与 README 均要求"零外部 API / 零 CDN"。所有依赖必须下载到本地目录，与现有 `doT.min.js` 同一处理方式。

### 4.1 新增文件（在 Canvas 工作区 `vendor/`，Phase 0 已落）

| 路径 | 大小 | 内容 |
|---|---|---|
| `vendor/gsap.min.js` | **72 KB**（实测，计划估 30 KB） | GSAP 3.13.0 核心 |
| `vendor/ScrollTrigger.min.js` | **44 KB**（实测，计划估 25 KB） | 滚动驱动插件 |
| `vendor/space-grotesk-var.woff2` | **22 KB**（实测，计划估 40 KB） | Latin variable 子集，wght 300–700，SIL OFL 1.1 |
| `vendor/README.md` | ~1 KB | 许可 + 重下载命令 |
| `motion.js` | ~8 KB | reveal / counter / magnetic / kinetic-underline / line-mask 助手 |
| `cursor.js` | ~3 KB | 自定义跟随光标 + 上下文标签 |

**总计** ~150 KB 一次性依赖，加载后不再变化。

### 4.2 关键动效配方（在 `motion.js` 里）

```js
// 1. stagger reveal（进视口时依次淡入 + translateY）
revealGroup(container, { child:'[data-reveal]', stagger:0.05, y:40, duration:0.8 })

// 2. kinetic counter（数字从 0 计到实际值）
countUp(el, { to: parseFloat(el.dataset.count), duration:1.5, ease:'power2.out' })

// 3. magnetic hover（元素向光标偏移）
magnetize(el, { strength:0.3, ease:'power3.out' })

// 4. line-mask reveal（段落逐行揭示）
lineMaskReveal(el, { lineStagger:0.02, duration:0.5 })

// 5. scroll-scrubbed underline（H2 底部条随滚动填充）
scrubUnderline(h2, { start:'top 80%', end:'bottom 60%' })

// 6. custom cursor（跟随 + 上下文）
initCursor({ dot:true, ring:true, labels:{ a:'打开', 'data-action=delete':'删除' } })
```

### 4.3 降级与无障碍

- `prefers-reduced-motion: reduce` → 关闭所有 scroll reveal、kinetic、counter、parallax、magnetic、呼吸动画；只留 hover 静态色变与 focus ring。
- 无 JS / JS 报错 → 静态呈现（v0.4 现状），所有动效关键视觉走 CSS transition 兜底。
- 键盘：Tab 顺序 = 左树 → doclist → 文章正文 → 右 rail tabs → rail 内容 → 状态栏；focus-visible 全站统一 3px `--acc` ring。
- 对比度：正文对背景 ≥ 4.5:1（Light 与 Dark 双主题各自校验）；仅装饰性 SVG 加 `aria-hidden="true"`，功能性图标带 `<title>` 或 `aria-label`。

## 5. 三屏详细设计

### 5.1 Home 总览（激进）

**首屏 hero**（占屏 60vh）：
- 左 60%：巨型"知库"二字（12vw，中文走 Georgia 600，`letter-spacing: -0.04em`）。首屏进入时两字**逐字**从下方 mask 升起（clip-path inset 100%→0，stagger 0.04s，ease `power3.out`，duration 1.2s）。
- 右 40%：阅读者 mascot（沿用 v0.4 现有 SVG），从 `--wash-hero` 圆形光晕中淡入。**鼠标视差**：mascot transform +0.5、书签 +1、齿轮 -0.3、光斑背景 +0.2。
- 中下部一句话副标："把散落 8 年的知识，接回一个入口" → 从 `<p>` 提到 `--font-display-latin` 2.5vw；滚动时逐词 mask reveal（每词 30ms 差）。

**4 个 KPI 数字**（"1 479 · 14 791 · 3 · 21"）：
- counter 从 0 计到实际值（`power2.out` 1.5s，只在首次进视口触发一次）
- 每个数字下方一条 `--hairline`，进视口时 `--acc` 从左到右填充

**7 域入口卡**（8 列，含"新建域"占位）：
- 每卡有独立的域色相光晕，从中心散开
- hover 时磁吸（`magnetize(el, { strength:0.2 })`）+ scale 1.02 + `--glow-accent`
- 首次进视口：stagger 0.05s 依次 translateY 40px + opacity 0→1
- 卡内 mini trend polyline 用 `stroke-dashoffset` 从右向左"画"进来（1.2s，`ease: power2.inOut`）

**最近更新**：横向 marquee（CSS `animation: marquee 60s linear infinite`），hover 暂停。7 条真实数据（epoll、RAG v2、DSH Agent、SSR→Islands、分布式事务、Git rebase、Q3 团队复盘）。

**本月心跳**（4 行）：数字 counter + 环比小箭头（`--acc` / `--danger` 已就位）。

### 5.2 Workbench 主屏（三栏 + 右 rail，只换皮不换骨）

**左树**（分类目录）：
- 每个 `.dom` 项 hover：左侧 2px `--dh` 竖条从 0 scaleX→1，240ms `power3.out`
- `.sub` 项 hover：背景 `--acc-soft` 从左向右 mask 填充（`background-position` 变换）
- 树首次加载：7 个域按 stagger 0.04s 依次淡入 + translateX 20px

**文档列表**：
- 进入视口时 stagger 40ms 淡入 + translateY 8px
- active 项的**左侧 3px 竖条带呼吸动画**（opacity 0.7↔1，2s loop，reduced-motion 关）
- 列表顶部的"按最近编辑"标签 + density-toggle 保留 v0.4 现样

**文章区**：
- 切换文档：老内容 opacity 150ms 退场 → 新内容 line-mask reveal 逐行滑入（每行 20ms 差，`clip-path: inset(0 0 100% 0)` → `inset(0 0 0 0)`）
- 代码块 copy 按钮：点击 → 文字"复制"变"已复制" + 从按钮中心发出 radial-gradient 涟漪（600ms）
- 收藏 star 按钮：点击 → star back.out(1.7) 弹跳 + 从中心迸出 3 颗小星（`<use href="#ill-star-cluster">` 复用）
- 删除按钮 hover：图标从 trash-outline 抖一下（`x: -2 → 2 → 0`，150ms）

**右 rail**：
- tab 切换：active tab 下 2px `--acc` 条从旧 tab 滑到新 tab（GSAP Flip 或简单 transform）
- TOC 面板滚动跟高：article 滚动时当前 `.toc-item.active` 下方的 `--acc` underline 跟着滑动
- 双链面板：`谁引用了它 / 它引用谁` 分组间加 stagger reveal

**顶部搜索框**：
- `/` 快捷键聚焦 → search 边框 2px `--acc` ring + 呼吸 glow 2s loop
- 输入 `<code>?</code>` 时，pill 从"全文检索"变"语义检索"，颜色从 `--acc` 过渡到 `--info`

### 5.3 Reading 阅读页（长文体验）

**首段 drop cap**：
- 中文首字走 Georgia 700 5em 首字下沉（`float: left; line-height: 0.85; margin-right: 0.1em`）
- 英文/数字走 Space Grotesk

**H2 kinetic underline**：
- 每个 H2 底部一条 `--hairline`（默认极淡）
- 滚动到该标题时 `--acc` 从左到右填充（`scrubUnderline(el, { start:'top 80%', end:'top 40%' })`）

**顶部阅读进度条**（sticky）：
- 1px 高，色从 `--acc → --acc2` 渐变
- 宽度 = 滚动百分比（ScrollTrigger `scrub: true`）

**mermaid 图卡**：
- 进入视口时 scale 0.95→1 + `filter: blur(4px → 0)`（duration 600ms）
- 图内节点 hover 高亮 `--dh`

**引用块**（`.quote`）：
- hover 时左侧 3px 竖条 scaleY 0→1（240ms `power3.out`）
- 文字色 `--muted → --ink`（300ms）

**wikilink 双链**：
- 默认 `border-bottom: 1px dashed`
- hover 时虚线换成实线 + 从下方升起 tooltip（目标文档 title + 域标签 + 相对时间）
- tooltip 用 `data-target-doc` 属性从 store 里读，不引 API 请求

**代码块**：
- 语言标签淡入（首次 reveal）
- 每一行 `pre code > span` 逐行 fade-in 20ms 差
- 复制按钮点击 → "已复制" + 涟漪（同 Workbench）

**文末 prev/next**：
- 滚动到底时，一张"读完了 · 试试这篇" + mascot 挥手 96 px 小插画从下方升起（translateY 60px + opacity）
- prev/next 文档卡片横向排列，磁吸 hover

## 6. 交互态总表

| 状态 | 表现 |
|---|---|
| hover（可交互） | 磁吸 + `--glow-accent` 光晕 + 左侧 `--dh` 竖条 scaleX |
| focus-visible | 3px `--acc` ring（全站统一，reduced-motion 下仍可见） |
| active/pressed | scale 0.98 + 从点击点发出 radial-gradient 涟漪 600ms |
| 页面进入 | stagger reveal 分组（每屏 3–5 组） |
| 滚动中 | kinetic underline、进度条、counter、parallax、marquee |
| 数据变更（保存/收藏/删除） | back.out 弹跳 + toast 从底部滑入 |
| 空态 | mascot + 文案 + 主 CTA（沿用 v0.4） |
| 加载 | skeleton shimmer（沿用 v0.4），加"呼吸"pill 图标 |
| 错误 | mascot 皱眉 + 警示 SVG + warn-halo（沿用 v0.4），加 shake 动效 |

## 7. 迁移到生产代码

设计稿通过后，落到 `E:\GitHub\knowledge\` 时：

**新增文件**：
- `static/vendor/gsap.min.js` + `ScrollTrigger.min.js`
- `static/fonts/space-grotesk-var.woff2`（Latin subset）
- `static/motion.js`（约 300 行，暴露 `data-reveal` / `data-magnetic` / `data-counter` / `data-line-mask` 属性驱动）
- `static/cursor.js`（约 80 行）

**`static/style.css` 追加**：
- 字阶 scale 变量（`--fs-hero / --fs-display / --fs-h2 / --fs-body / --fs-label`）
- `--hairline / --glow-accent / --wash-hero`
- kinetic underline 的**静态版**（无 JS 时用 `background-image: linear-gradient(90deg, var(--acc), var(--acc)) no-repeat` + `background-size: 0% 2px`，CSS-only hover 到 100%）
- `@media (prefers-reduced-motion: reduce)` 全局关 animation

**`app/templates/base.html`** 顶部追加：
```html
<link rel="preload" as="font" href="/static/fonts/space-grotesk-var.woff2" type="font/woff2" crossorigin>
<script src="/static/vendor/gsap.min.js" defer></script>
<script src="/static/vendor/ScrollTrigger.min.js" defer></script>
<script src="/static/cursor.js" defer></script>
<script src="/static/motion.js" defer></script>
```

**`app/templates/home.html`** 结构改：
- Hero 拆 `.hero-mask > h1 > span[data-word]`
- 域卡从 4 列改 8 列，每卡 `data-reveal data-magnetic`
- 数字 `<span data-counter="1479">`
- KPI 用 counter
- 最近更新改 `<div class="marquee">`

**`app/templates/workbench.html`** 结构改：
- `.tree` 每个 `.dom > a` 加 `data-reveal data-stagger`
- `.doclist` 加 `data-reveal-stagger`
- `.article-inner` 由 `app.js` 渲染后逐行包 `.line` 单元，加 `data-line-mask`
- Rail TOC 项加 `data-toc-anchor="h2-slug"`

**`app/templates/doc.html`**（或 workbench 内文章渲染函数）：
- 每个 H2 加 `<span class="kinetic-underline">` 子元素
- 顶部加阅读进度条 `<div class="progress-bar">`
- 代码块 pre 内 span 加 `data-fade-line`

**`static/app.js`** 无功能改动，只是在 `renderDoc()` 后调用一次 `Motion.refresh()` 让 ScrollTrigger 重新扫描新 DOM。

**回退方案**：所有 `<script>` 加 `defer`；`motion.js` / `cursor.js` 在初始化前检查 `matchMedia('(prefers-reduced-motion: reduce)').matches`，命中则整段跳过；无 JS 时 CSS `@media (prefers-reduced-motion: reduce) and (scripting: none)` 提供静态兜底。

## 8. 验收标准

### 8.1 视觉
- [ ] Hero display 尺寸在 1440px 屏上是 ≥ 200px（≥ 12vw），字距 -0.03 到 -0.04
- [ ] 首屏在 1.5s 内完成所有 reveal / counter 动画，无 layout shift
- [ ] 三栏之间的 gutter 视觉可见，卡片留白比 v0.4 大一档

### 8.2 动效
- [ ] 首页 mascot 有 parallax；书签/齿轮/星视差层级不同
- [ ] Workbench 切文档时 article 有 line-mask reveal（肉眼可辨）
- [ ] Reading H2 底部 underline 随滚动填充
- [ ] 4 个 KPI counter 只在首次进视口触发一次
- [ ] Custom cursor 在可交互元素上展开并显示上下文文字

### 8.3 降级
- [ ] `prefers-reduced-motion: reduce` 下，所有 kinetic / counter / parallax / magnetic 关闭；hover 与 focus ring 仍在
- [ ] 关 JS，页面完整可读（无空占位、无错位）
- [ ] 键盘 Tab 顺序符合 § 4.3；focus-visible ring 全站一致

### 8.4 生产落地
- [ ] `static/vendor/` 与 `static/fonts/` 均本地，无 CDN 引用
- [ ] `git grep -E "cdn|unpkg|jsdelivr|googleapis"` 结果为空
- [ ] 3 套 smoke 测试（`test_reader.py` / `test_rag.py` / `test_govern.py`）全绿
- [ ] `.gitignore` 不需要新增（生产文件都在 `static/` 与 `app/templates/`，都是要提交的）

## 9. 风险与开放问题

| 风险 | 缓解 |
|---|---|
| Space Grotesk 商用许可 | 该字体 SIL OFL 1.1，可自由内嵌；下载前先核对最新许可。若变更则退回"用现有 Georgia 极限"（字阶不动，display 用 Georgia 700 + 8vw） |
| GSAP 商用许可 | GSAP 从 v3.13 起 core + 全部官方插件（含 ScrollTrigger）改为 Webflow Standard License，商用允许；本地引用不涉及分发链接 |
| Latin subset 覆盖不到项目符号 | 打包时把 ASCII + 常用标点全带上，实测覆盖 ≥ 99% 拉丁内容；缺字回退到 Georgia |
| 首屏 LCP 变慢 | hero 与 mascot 均内联 SVG，无外部图；`motion.js` defer + `IntersectionObserver` 懒挂载 |
| Reduced-motion 用户觉得"没做完" | 静态视觉破格本身（12vw 字、不对称布局）已经传递"Awwwards 味"，动效是加分不是必需 |

## 10. 交付节奏

1. **设计稿阶段**（本次任务）：在 Canvas 工作区把 3 屏深度重塑做出来，本地引用 GSAP + ScrollTrigger + 字体，通过 check_design_quality P0/P1=0，作者评审。
2. **生产落地阶段**（下一次任务，另开）：把 3 屏的视觉决策与动效映射到 `static/style.css` + `app/templates/*.html` + `static/motion.js` + `static/cursor.js`，跑 3 套 smoke 测试 + 巡检脚本，作者验收后 commit。

**本设计文档只覆盖第 1 阶段**。第 2 阶段等第 1 阶段评审通过、代码落地上生产时另开一份 `2026-XX-XX-zhiku-awwwards-migration-plan.md`。

---

**规格自审 checklist**（写完后自查，见文档 commit）：
- [x] 占位符：无 TBD / TODO
- [x] 内部一致：三屏结构与 § 3 token 表一致，无冲突
- [x] 范围聚焦：只做 3 屏深度重塑，不做 10 屏；迁移另开计划
- [x] 歧义：字体选型给了 fallback；动效降级有明确规则；无 JS 场景有静态兜底
