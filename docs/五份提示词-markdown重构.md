# 五份提示词 · 面试库 Markdown 渲染重构

> 前提：agent 在本仓库 `E:\GitHub\knowledge` 上下文运行，可读写文件。Prompt-R 独占 `static/style.css`+`static/app.js`；C1–C4 各改互不相同的 `.md`，都不碰那两个文件。全部完成后本地统一软删面试 `.html` 孪生。

---

## ① Prompt-R（渲染层 · 独占 style.css + app.js）

```
你在改本地知识库阅读器（E:\GitHub\knowledge，Flask+原生JS，语料不出网）。任务：把 markdown 正文（.a-body）重做成已验证的设计。设计基准可参考桌面实验页 C:\Users\Administrator\Desktop\markdown-restyle-experiment\experiment.html（明暗两态已验证）。

只改两个文件：static/style.css、static/app.js。

【style.css · .a-body 重设计】
- h1：居中、底部 3px 主题色(--c-acc)下划线。
- h2：整条渐变底+白字+圆角；渐变色由 JS 注入的 --gh/--gh2 决定，CSS 写 background:linear-gradient(135deg,hsl(var(--gh,160) var(--bar-s) var(--bar-l)),hsl(var(--gh2,200) var(--bar-s) var(--bar-l)))，其中 --bar-s/--bar-l 在 :root 与 html[data-theme=dark] 分别定义（暗色降低明度）。
- h3：--c-acc 文字色 + 左侧 4px --c-acc 竖条。
- 新增 .sec-card：卡片底(--c-panel)+1px 边框(--c-line)+圆角+padding:1.4rem 1.6rem+margin-bottom:1.6rem。
- 四类提示框 blockquote.tip/.warn/.kp/.fu：各自左边框色+浅底（用 --c-info/--c-warn/--c-acc/--c-acc2 派生），明暗两套。
- 字体：.a-body 与代码 font-family: Consolas,"梦源黑体 CN","Microsoft YaHei",sans-serif（拉丁走 Consolas、CJK 回退梦源黑体 CN）。
- 铁律：所有颜色引用阅读器现有主题变量（--c-acc/--c-ink/--c-panel/--c-sunk/--c-line/--c-info/--c-warn 等）与 html[data-theme]；raw hex 只允许写在 [2] token 定义区；禁止引入外部字体/CDN。

【style.css · 代码块随主题 + 克制单色】不换 hljs 主题文件、不加第二套高亮，靠高特异性覆盖仓库已载的 hljs-github-dark.min.css。
(a) 在 [2] token 定义区新增：
  :root{ --code-bg:#f6f8fa; --code-fg:#24292f; --code-com:#6a737d; --code-key:#0b6e4f; --code-str:#0a5c46; --code-num:#8a4b00; --bar-s:62%; --bar-l:44%; }
  html[data-theme="dark"]{ --code-bg:#161b22; --code-fg:#c9d1d9; --code-com:#8b949e; --code-key:#7ee787; --code-str:#a5d6ff; --code-num:#f2cc60; --bar-s:52%; --bar-l:40%; }
(b) 在 .a-body 区加：
  .a-body pre{ background:var(--code-bg); border:1px solid var(--c-line); border-radius:var(--rd-card); padding:16px 18px; margin:16px 0; overflow-x:auto; }
  .a-body pre code{ background:none; border:none; color:var(--code-fg); font-family:Consolas,monospace; font-size:13px; line-height:1.75; }
  .a-body pre code.hljs{ background:transparent; padding:0; }
  .a-body pre code span{ color:inherit; font-style:normal; font-weight:inherit; }
  .a-body pre code .hljs-comment,.a-body pre code .hljs-quote,.a-body pre code .hljs-doctag{ color:var(--code-com); font-style:italic; }
  .a-body pre code .hljs-keyword,.a-body pre code .hljs-built_in,.a-body pre code .hljs-literal,.a-body pre code .hljs-type,.a-body pre code .hljs-symbol,.a-body pre code .hljs-params{ color:var(--code-key); font-weight:600; }
  .a-body pre code .hljs-string,.a-body pre code .hljs-regexp{ color:var(--code-str); }
  .a-body pre code .hljs-number,.a-body pre code .hljs-boolean{ color:var(--code-num); }

【app.js · 扩展 enhanceArticleDOM(el)】顺序敏感、全部幂等（已处理过的节点跳过），别破坏现有 codeblock 包壳/tbl-wrap/wikilink/mermaid/buildToc：
  1) 分组卡片：遍历 el 内 .a-body 的直接子节点，遇 H2 建 <div class="sec-card">、把该 H2 及其后直到下一个 H1/H2 的兄弟移入；标题 id 保留在标题元素上。
  2) 稳定随机主题条：对每个 .a-body h2，用 textContent 做 hash 得色相 h（如 h=ΣcharCode*31 %360），setProperty('--gh',h) 与 ('--gh2',(h+42)%360)。同标题恒定、不同标题各异。
  3) 难度徽章：对每个 .a-body h3，若文本尾部匹配 /[｜|]\s*(初级|中级|高级)\s*$/，去掉该后缀并 appendChild <span class="badge">（初级→class b、中级→m、高级→a，CSS 里给绿/黄/红、明暗各一套）。
  4) 提示框分类：对每个 .a-body blockquote，首行 💡→tip、⚠️/❗→warn、🎯或“关键要点/关键知识点”→kp、🔍或“追问”→fu（扩展现有 tip/warn 逻辑）。
  5) 语法高亮仍走仓库 hljs（app.js 已有 hljs.highlightElement），不要新增正则高亮器。

【验证，全过才算完成】node --check static/app.js；python tests/test_reader.py 全绿；起服务取 3 篇不同域 markdown（含代码/表格/多级标题/提示框）在明、暗两主题各截图，确认与实验页一致、无外壳污染、buildToc 与代码复制不坏。
```

---

## ② Prompt-C1（内容 · javascript / industry / career）

```
你在本地知识库 E:\GitHub\knowledge 写面试题库语料（markdown 为唯一事实源）。只改下列 .md 正文，保留其 frontmatter，不碰 style.css/app.js/任何 .html。
目标（补全到标题宣称题数）：
- content/interview/javascript/JavaScript核心概念面试题库 - 100道精选题目.md → 100 题
- content/interview/industry/行业洞察面试题库 - 28道精选题目.md → 28 题
- content/interview/career/职业发展面试题库 - 30道精选题目.md → 30 题
规则：保留现有真实题；删除占位假题（“示例问题N…请详细解释相关概念”“回答模板（您可根据经验填充）”）；缺失数用真实、有深度、彼此不重复的题补齐；题干编号连续 1..N；严禁灌水/模板复制。行业/职业类出真实情境题（趋势判断、职业规划、转型取舍），不要技术八股。
排版约定（供渲染层识别，务必使用）：大节用 `## 小节名`；题干用 `### N. 题干｜初级|中级|高级`；提示框用 `> 💡 提示`、`> 🎯 关键要点`、`> 🔍 追问`、`> ⚠️ 注意`；代码用三反引号围栏、对比用 markdown 表格。
逐篇处理、逐篇自检并报告：题数=N？占位残留=0？编号连续 1..N？约定用对？无重复灌水？
```

---

## ③ Prompt-C2（内容 · frameworks / architecture / behavioral）

```
你在本地知识库 E:\GitHub\knowledge 写面试题库语料（markdown 为唯一事实源）。只改下列 .md 正文，保留 frontmatter，不碰 style.css/app.js/任何 .html。
目标（补全到标题宣称题数）：
- content/interview/frameworks/React与Vue框架面试题库 - 80道精选题目.md → 80 题（React/Vue 原理、hooks、响应式、diff、状态管理、性能）
- content/interview/architecture/系统架构设计面试题库 - 60道精选题目.md → 60 题（CAP/一致性/分库分表/缓存/消息队列/高可用/分布式事务/服务治理）
- content/interview/behavioral/行为面试题库 - 40道精选题目.md → 40 题（STAR 行为题，真实情境，非技术八股）
规则：保留现有真实题；删除占位假题（“示例问题N…请详细解释相关概念”“回答模板（您可根据经验填充）”）；缺失数用真实、有深度、彼此不重复的题补齐；题干编号连续 1..N；严禁灌水/模板复制。
排版约定（供渲染层识别，务必使用）：大节用 `## 小节名`；题干用 `### N. 题干｜初级|中级|高级`；提示框用 `> 💡 提示`、`> 🎯 关键要点`、`> 🔍 追问`、`> ⚠️ 注意`；代码用三反引号围栏、对比用 markdown 表格。
逐篇处理、逐篇自检并报告：题数=N？占位残留=0？编号连续 1..N？约定用对？无重复灌水？
```

---

## ④ Prompt-C3（内容 · css-html / node-fullstack / ai）

```
你在本地知识库 E:\GitHub\knowledge 写面试题库语料（markdown 为唯一事实源）。只改下列 .md 正文，保留 frontmatter，不碰 style.css/app.js/任何 .html。
目标（补全到标题宣称题数）：
- content/interview/css-html/CSS与HTML面试题库 - 60道精选题目.md → 60 题
- content/interview/node-fullstack/Node.js与全栈面试题库 - 50道精选题目.md → 50 题（事件循环/流/cluster/Express/Koa/ORM/全栈工程）
- content/interview/ai/AI技术应用面试题库 - 40道精选题目.md → 40 题（RAG/Agent/微调/评测/推理优化/多模态落地）
规则：保留现有真实题；删除占位假题（“示例问题N…请详细解释相关概念”“回答模板（您可根据经验填充）”）；缺失数用真实、有深度、彼此不重复的题补齐；题干编号连续 1..N；严禁灌水/模板复制。
排版约定（供渲染层识别，务必使用）：大节用 `## 小节名`；题干用 `### N. 题干｜初级|中级|高级`；提示框用 `> 💡 提示`、`> 🎯 关键要点`、`> 🔍 追问`、`> ⚠️ 注意`；代码用三反引号围栏、对比用 markdown 表格。
逐篇处理、逐篇自检并报告：题数=N？占位残留=0？编号连续 1..N？约定用对？无重复灌水？
```

---

## ⑤ Prompt-C4（内容 · performance / management / engineering）

```
你在本地知识库 E:\GitHub\knowledge 写面试题库语料（markdown 为唯一事实源）。只改下列 .md 正文，保留 frontmatter，不碰 style.css/app.js/任何 .html。
目标（补全到标题宣称题数）：
- content/interview/performance/性能优化面试题库 - 70道精选题目.md → 70 题（加载/渲染/网络/构建/运行时/指标度量）
- content/interview/management/团队管理面试题库 - 50道精选题目.md → 50 题（带团队/招聘/绩效/冲突/向上管理，真实情境）
- content/interview/engineering/工程化与工具链面试题库 - 45道精选题目.md → 45 题（Webpack/Vite/Babel/ESLint/测试/CI-CD/包管理）
规则：保留现有真实题；删除占位假题（“示例问题N…请详细解释相关概念”“回答模板（您可根据经验填充）”）；缺失数用真实、有深度、彼此不重复的题补齐；题干编号连续 1..N；严禁灌水/模板复制。管理/工程类按各自领域出真实题。
排版约定（供渲染层识别，务必使用）：大节用 `## 小节名`；题干用 `### N. 题干｜初级|中级|高级`；提示框用 `> 💡 提示`、`> 🎯 关键要点`、`> 🔍 追问`、`> ⚠️ 注意`；代码用三反引号围栏、对比用 markdown 表格。
逐篇处理、逐篇自检并报告：题数=N？占位残留=0？编号连续 1..N？约定用对？无重复灌水？
```
