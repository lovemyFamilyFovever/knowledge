# 合并方案：单仓双态发布（本地 Flask 阅读器 + 公网静态只读面）

日期：2026-10-07　状态：阶段 3 实施中（§7-1 已拍板：单仓 Pages；§7 其余待定）　负责人：LobsterAI 会话（本稿）；原始设计出自 QwenWork 会话（2026-10-07 凌晨，瘦身之前）

> 承接关系：本规格在瘦身提交 `6c79548` 之后的全量复核基线上重写。原始设计的决策不变（§2），但设计稿里的现场数字（fetch 54 处、顶栏 4+1 入口、语料 1061 个/9.6MB）已被瘦身改变，全部按现状刷新（§3）；引用时一律以复查数字为准。

## 1. 问题与目标

现状痛点（用户原话，2026-10-06 23:58）：做了两套系统——本地 `knowledge`（Flask，功能全但上不了公网）与 `E:\GitHub\knowledge-site`（Quartz 静态站，能上 Pages）；「每次更新都不同步，在 knowledge 中新增文章、目录，site 页面无法同步更新」。

目标：**不要两个项目**。一个事实源、本地能开、公网能看、公网功能适当裁剪——「最起码一个查阅的基础功能」。

## 2. 决策记录（用户已拍板，勿重开）

| # | 决策点 | 结论 |
|---|---|---|
| D1 | 目标口径 | 单事实源；本地照旧全功能；公网裁剪版「目录 + 正文 + 静态全文检索」；文件状态统一 |
| D2 | 公网功能边界 | **目录 + 正文 + 静态全文检索**（用户选定；术语表/统计等轻页面非承诺项） |
| D3 | 渲染层 | **① 同一前端 + 静态只读适配器**：公开面 = 本地阅读器的只读档（同一套 CSS 与正文约定）；构建时导出静态 JSON + 只读适配器；编译期关掉写功能。代价已接受：SPA、无 JS 不可读、SEO 不友好 |
| D4 | 发布形态 | 公网面 = 派生构建产物，推到**独立公共仓库**（取代手工维护的 knowledge-site）；**永不在 knowledge 仓本身开门**（泄露事故后升级为硬要求） |

被否备选（留档）：渲染层 ② Python 预渲染同 CSS（工程量中等）；③ 保留 Quartz 当公网面（两套排版语言永久并存，且要重实现正文约定）；发布层 B 强行单仓（需洗历史、正面违反禁区）；C 删库重传（不可逆，已废弃）。

## 3. 现状复核（2026-10-07 06:00–07:00 实测，瘦身 `6c79548` 之后）

- HEAD = `6c79548`；远端 main 与本地一致；工作区干净（仅未跟踪 `HANDOFF.md`）；本地阅读器 `127.0.0.1:5001` 运行中（最新代码）。
- **`fetch(` 直接调用 46 处**：`static/app.js` 38、`static/pages/misc.js` 5、`kb-core.js` 1、`tag-suggest.js` 1、`wikilink-suggest.js` 1；模板 0 处。「一个函数收口」假设仍不成立——适配器只能走 `window.fetch` 拦截（§4.2）。
- 语料（git 跟踪的 md/html，即公开面基准集）：

| 域 | 文件数 | 大小 |
|---|---|---|
| baike | 708 | 3.25 MB |
| interview | 190 | 2.06 MB |
| articles | 66 | 0.91 MB |
| career | 36 | 0.80 MB |
| ai-assets | 2 | ~0 |
| **合计** | **1002** | **7.03 MB** |

  另需随导出携带：`content/_meta/taxonomy.json`（域权威文件）与跟踪的 31 张图片（正文 img 引用）。`_inbox/_trash/projects/小说/漫画` 与 2 个 PII 文件不在基准集内（gitignore 硬边界，实测无跟踪例外）。
- 顶栏现为 **3 项：阅读 / 统计 / 收藏**；`/review /quiz /glossary /tags /governance` 已删，不需要再考虑裁剪它们。
- 页面模板：`base/workbench/home/landing/search/favorites/stats/inbox/error`；静态脚本：`static/app.js`、`kb-core.js`、`pages/*.js`（workbench/home/search/stats/misc/tag-suggest/wikilink-suggest/cm-editor）。
- 已解决：旧远端确认删除（服务器实回 `Repository not found`）；新同名私仓已推（本地=远端）。NO_PROXY 提交纪律已入 AGENTS.md。
- 仍待销：`content/.obsidian/` 4 个 json 仍被跟踪（§5-2）。

## 4. 实现分解

### 4.1 导出器 `scripts/export_static.py`（新增）

- 输入 = git 跟踪的公开白名单（基准集）；输出 = `site/`（**派生缓存**：按不变量 3 对待——`site/` 忽略已随本规格预置进 `.gitignore`；可删可重建，不进 git）。
- 产物结构（草案）：
  - `site/index.html` —— 阅读器壳（同一模板；注入 `KB_STATIC.readonly = true` 与 `KB_BASE`）；`site/404.html` = index 的副本（深链兜底）。
  - `site/data/tree.json`、`data/doc/…`、`data/links.json`、`data/meta.json`（域标签/日期/计数）、`data/search/<域>.json`（懒加载索引）、`data/palette/index.json`。
  - `site/raw/…` —— 正文引用的图片/附件（31 张图在内的白名单资源）。
  - `site/static/…` —— 复用现有静态资产（含新增 `kb-static.js`）+ 本地字体（`static/vendor/fonts/`）。
- **硬约束：导出的 JSON 必须与 Flask 端点逐字段同构**（否则同一份前端会精神分裂）。做法：导出器直接复用应用内产 payload 的函数（`app/store.py`、`app/fts.py`、`app/palette.py` 等，具体函数实现期逐一对应），**不许照抄一遍结构**。判据：新增断言「同一临时语料下，导出 JSON == Flask 端点响应」（§4.6）。
- 导出期静态重写（非 fetch 出口，必须逐个处理 + 断言）：
  - 模板与 CSS 中的绝对路径（`/static/…`、CSS `url("/static/vendor/fonts/…")`、`/raw/…`）→ 加 `KB_BASE` 前缀；
  - 服务端渲染出来的 `/raw/{{...}}` 链接（workbench 的「新标签页打开」、home/inbox 的原始文件链接）→ 重写；
  - JS 运行时构造的 `/raw/…`（`kb-core.util.rawUrl` 唯一实现处）→ 由适配器覆盖单点解决（§4.2）。
- 日期来源：frontmatter `collected`（约 95.8% 覆盖）+ `docs/history-dates-20261007.json`（1446 条）兜底；两处都缺的按空处理。
- 检索索引：CJK bigram、分域懒加载；**分片粒度实测后定，不承诺未测数字**。

### 4.2 只读适配器 `static/kb-static.js`（新增，仅公网构建注入）

- `window.fetch` 拦截（在全部页面脚本之前加载，构建产物专属）：
  - 读端点 → `site/data/*.json`：`/api/tree`、`/api/doc`、`/api/links`、`/api/search`、`/api/palette/index`（全量以 §4.4 分诊表为准）。
  - 写端点 → 一律返回 `{ok:false, error:"READ_ONLY"}`，走现成错误通道（toast/KB.api.msg），不静默。
  - `/api/track` → 静默 no-op；`/api/recent_read`（侧栏「近 7 日阅读」）→ UI 按开关隐藏 + fetch no-op。
- `kb-core.util` 的 `docUrl/rawUrl`（唯一实现处）→ 覆盖为静态路径。
- **壳内链接改写**：公网页壳里的根绝对链接（`/`、`/doc/…`、`/browse/…`）在运行时统一改写为 `KB_BASE` 前缀（MutationObserver 覆盖动态渲染），防止点击/中键/刷新跳出子路径（否则落到站外 404）。
- **本机阅读进度（2026-10-07 用户增补）**：左栏顶部「最近阅读」列表 + 逐篇滚动位置恢复；仅写浏览器 localStorage（不碰语料、不出站；换设备不同步、清浏览器数据会丢）。
- 残余风险（书面化）：非 fetch 的资源引用（`<img src="/raw/…">`、PDF iframe、`location.href` 直跳、CSS `url()`）不经过拦截器——**全部进导出器测试的显式断言清单**，不靠肉眼。
- 起步用方案 (a)（拦截）；「先把散落 fetch 收口进 KB.api.request」的 (b) 重构**不作为上线前置**，发布后单独立项（见 §7-4）。

### 4.3 模板裁剪（同一套模板 + 开关，不复制第二份）

- 开关：`KB_STATIC.readonly`（构建期常量）。公网隐藏：统计、收藏、收件箱 badge、状态栏统计快照、编辑/删除/收藏/移动/备注按钮、编辑器入口、命令面板写命令；`/stats /favorites /inbox` 页不生成产物。
- 保留：三栏骨架（含移动/平板断点）、分类树（域色点）、正文排版全套（`.a-body`、小节卡片、提示框、代码块、双链）、搜索浮层、只读快捷键、主题切换。

### 4.4 读路径端点全量分诊（实现第一步，逐端点定「映射 / 只读 / no-op / 重写」）

前台实测引用的 `/api/*` 全集（瘦身后，27 条）：tree、dir/tree、doc、docmark、links、search、palette/index、recent_read、track、wikilink/check、wikilink/suggest、stats、substats、globalstats、save、note、favorite、move、move/batch、delete、rename-sub、rename-domain、mkdir、rmdir、tags、import、inbox/ignore、inbox/purge（另有 rag 系列保留端点，公网不涉及）。

判据：**发布产物里跑一遍全页面（目录/正文/搜索/双链），任何未被分诊的 `/api/` 调用必须让测试红**——静态审计：扫描产物 JS 中的 `/api/` 字面量 ⊆ 分诊表。

### 4.5 构建与发布

- GitHub Actions + `actions/deploy-pages`；产物仓为**独立公共仓库**（机器生成、禁止手改）。**接线方式与仓库名见 §7-1 待拍板**（涉及一次性的人工仓库设置与只读凭据）。
- 触发：推 `main` 自动构建发布；首次上线用 `workflow_dispatch` 手动跑一次核验。
- 本地预览：对 `site/` 起静态服务（如 `python -m http.server -d site`），从本地浏览器核验只读档，再上云。
- 约束：CI 新增任务必须**无浏览器可跑**（纯 Python 校验；依赖 Chrome/node 的套件允许 SKIP）。

### 4.6 测试与门禁（新增套件）

1. **导出器契约测试**（纯 Python、合成语料）：JSON 与端点同构断言 + raw/绝对路径重写断言 + 分诊表覆盖断言 + 产物结构断言（index/404/data）。
2. **静态档行为测试**（本机 Chrome，非 CI 必跑）：无控制台报错、写操作一律 READ_ONLY、深链刷新可用、搜索可用。
3. 接入 `.githooks` / `ci.yml` / 覆盖台账（新套件注册 + 数字对账），与现有门禁同规。

## 5. 已知坑（逐条销）

1. GH Pages 深链：`404.html → index.html` 转发，否则刷新即死。（§4.1 已含，待实现）
2. `content/.obsidian/` 4 个 json **仍被跟踪**（本轮实测：app/appearance/core-plugins/graph）→ 与实现同批 `git rm --cached` + 入忽略。属「被跟踪即公开」的既有欠账，不随私仓状态豁免。
3. NO_PROXY 会让 `watch_ci` 假失败——已入 AGENTS.md，提交照做。（已销）
4. 旧远端删除确认——已确认；新私仓已推。（已销）
5. 无浏览器 runner：CI 的导出测试纯 Python，不依赖 Chrome/node 套件。
6. （本轮复核新发现）**设计稿正文数字会过期**：fetch 54→46、顶栏 4+1→3、语料 1061/9.6MB→1002/7.03MB——凡引用先现场量。本规格 §3 已刷新，其余章节引用处已按现状重写。

## 6. 验收判据（用户可感）

- 本地：一切照旧（现存全部套件绿、本地功能零损失）。
- 公网：与本地**同一套视觉**；目录/正文/全文检索可用；深链可刷新；所有写入口要么不存在、要么明确返回 READ_ONLY；手机可读。
- 同步：本地改一篇文章 → 推 `main` → 公网自动更新，**人不再手改第二处**（「更新不同步」痛点消失）。
- 诚实边界：SPA 无 JS 时不渲染正文（已接受）；语义检索（RAG）不在公网（模型不出网）。

## 7. 待拍板 / 未决

1. 已拍板（2026-10-07，路线变更）：**单仓方案**——knowledge 仓转公开（用户操作），用其自带 GitHub Pages 发布（Actions 构建），站点 URL `https://lovemyFamilyFovever.github.io/knowledge/`（项目页子路径；导出用 KB_BASE=/knowledge）；不需要任何新仓。公开面=全部被跟踪文件（用户明确放弃逐项复核、自行负责）；gitignore 硬边界与导出白名单继续排除 projects/小说/漫画与两个 PII 文件。
2. **knowledge-site（原 garden 仓）处置**：其 Quartz 双栏 UI 是约 10 个提交的手写成果（不可再生）。保留归档 / 留作视觉参考 / 删除，三选一；「恢复旧站」与否一并定。（未获指令前不碰该目录。）
3. **interview 底料复核**：仅当未来要把 knowledge 转公开才需要（当前路线保持私仓，无需）；转公开前必过这一关。
4. 附：「fetch 收口 (b)」重构不在上线前置，发布后单独立项。

## 8. 实施顺序（草案）

1. 导出器骨架 + 契约测试（不发布，本地产物）。
2. 适配器 + 裁剪开关（本地以 readonly 模式冒烟）。
3. 构建工作流 + 单仓 Pages 联调（§7-1 已拍板）→ 首次上线核验。
4. 线上核验（手机/电脑双端）+ 按结果补回归。
5. （按指令）退役 knowledge-site。

## 9. 与其它文档的关系

- 本规格上线后，`docs/spec-site-reading-ui.md`（2026-09-30 旧站对齐评估）不再需要执行；其素材留作 §7-2 决策参考。
- 引用：`docs/superpowers/specs/2026-10-07-slim-down-design.md`（瘦身前提）、`docs/history-dates-20261007.json`（日期兜底）、`AGENTS.md`（不变量 1 / 3 / 10）。
- 下一步技能产物：获批后另出实施计划（`superpowers-writing-plans`）。
