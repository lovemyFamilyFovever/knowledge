# 书库阅读器（txt / epub）设计留存文档

> 目的：本仓库的 `content/小说/`、`content/漫画/` 已于 2026-09-30 整体移出（见 `AGENTS.md` 禁区末条与 `docs/handoff-2026093002.md`），但**处理这类文件的逻辑与它的测试原样留在仓库里**。本文是给"完全没有本仓库上下文、要在别处重做这套阅读功能"的工程师看的实现留存：写清楚每条判据、每个键名、每个顺序依赖，以及它对应哪一条测试断言。
>
> 代码坐标（行号按 2026-09-30 的工作树，可能因后续提交漂 ±10 行）：
>
> | 职责 | 位置 |
> |---|---|
> | 书库阅读引擎（唯一主体，1020 行） | `static/kb-novel.js`（全局对象 `window.KBNOVEL`，导出名一律 `N.*`） |
> | 格式分流 / 下载条 / xlsx / pdf / mobi / 偏好作用域判定 | `static/app.js`：`libBar` 244、`renderLibraryDoc` 249、`renderXlsx` 290、`isLib` 1161、`buildToc` 681 |
> | 语料层（扩展名白名单、扫描、路由解析、旁挂件） | `app/store.py`：`SKIP_DIRS` 30、`LIBRARY_EXTS` 34、`is_visible_doc` 294、`_visible_sub_files` 315、`_scan_sub` 502、`find_doc` 537、`notes_path` 567、`read_notes` 571、`sidecars_of` 584 |
> | 后端数据与写回 | `app/app.py::safe_rel` 172 / `collect_doc` 180、`app/routes_pages.py::raw` 190、`app/routes_edit.py::api_note` 89 |
> | 模板挂载 | `app/templates/workbench.html`：`is_lib` 40、`#pane-toc` 82、`<div class="article-inner" id="article">` 56 |
> | 设置抽屉的「小说」页签 | `static/kb-core.js`：section 384、页签按钮 791（内容来自 `KBNOVEL.panelHTML()/bindPanel()`） |
> | 样式 | `static/pages/novel.css`（阅读器骨架）、`static/pages/tagedit.css:39`（`.lib-frame-wrap`） |
> | 行为契约（最可信的规格） | `tests/test_js_props.py`（解析器，合成畸形样本）、`tests/test_ui_behavior.py`（探针 20 `probe_novel_prefs`、探针 22 `probe_novel_bar`）、`tests/test_ui_regress.py`（镜头 `novel_txt` / `novel_txt_prefs`） |
>
> **本文不含任何真实书库内容**，所有样本名（`长夜.txt`、`长篇样本.txt`、`p3b/*.epub`）都是测试里现造的合成语料。

---

## 1. 文件识别：什么算"一本的书"

### 1.1 三个扩展名集合，各自管一件事（不要合并成一个）

```python
# app/store.py:30-36
SKIP_DIRS = {"_inbox", "_assets", "_unfiled"}
WRITABLE_EXTS = {".md"}
SERVABLE_EXTS = {".md", ".html"}
LIBRARY_EXTS = {".txt", ".epub", ".pdf", ".xlsx", ".mobi"}
MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp", ".avif"}
```

四条独立的门，重合处刻意不重合：

- **进分类树**：`SERVABLE_EXTS | LIBRARY_EXTS`（`store._visible_sub_files` 326、`scan_corpus` 486、`find_doc` 560）。书库文件"看得见、点得开"。
- **`/raw` 直服**：`SERVABLE_EXTS | MEDIA_EXTS | LIBRARY_EXTS`（`routes_pages.py:198`）。图片也必须直服，否则正文相对图片与 epub 的封面都取不到。
- **可写回**：只有 `WRITABLE_EXTS`。**这是全套里最容易踩的一条**：`/api/save` 与 `/api/delete` 都用它（`routes_edit.py:42`、`api_delete`），所以书库文件**天然不可编辑、也不可经 `/api/delete` 单篇软删**（`POST /api/delete {"path":"小说/tiny.txt"}` 实测 400，台账 §3 备注 A 已结案）。前端必须与之自洽：`workbench.html:44-55` 的 crumb 整块包在 `{% if not is_lib %}` 里，`renderCrumb` 的 `isLib` 分支不渲染编辑/删除/标签/收藏（`app.js:1165`、`1175`）。**重做时二选一**：要么照搬"书库不进删除流程"（本项目的选择），要么给书库补一条软删路径 —— 但绝不能只改前端不改后端，那会做出一个点了必 400 的删除钮。
- **例外：`/api/note` 允许书库**。`routes_edit.py:93` 用的是 `WRITABLE_EXTS | store.LIBRARY_EXTS`，因为"章评"要能落在 `.txt`/`.epub` 的旁挂上。**它只少了这一处放宽**，且没有 `api_save` 那句"拒绝 `_` 前缀路径段"的守卫（`routes_edit.py:43-44`）—— 也就是说 `_trash/xxx.txt` 这种位置仍能写进备注。重做时建议补上。

### 1.2 "是书不是普通文档"的判定发生在三处，必须同步

同一件事在三处各写了一份，改一处要改三处（本项目没有把它们收敛成单一来源，这是**已知的重复实现**，重做时值得一次性消灭）：

1. 后端：`p.suffix in LIBRARY_EXTS`（`app.py:188`）→ `is_library` 为真时**一个字节都不读正文**，`raw = ""`、`fm = {}`、`body = ""`，只回元数据与 `size`（`doc["md"] = None`）。**这条"不读"是必须的**：366MB 的 epub 一旦进了 `read_text` 就是 OOM/秒级白屏。
2. 前端渲染分流：`(DOC.name || "").match(/\.(txt|pdf|xlsx|epub|mobi)$/i)`（`app.js:355`）→ 命中即走 `renderLibraryDoc`，**不进 markdown 管线**，并先 `el.classList.remove("pretty-mode")`。
3. 前端 chrome：同一串正则的 `test` 形式（`app.js:1161`、`1183`）。

判定用的是 **`DOC.name` 而不是 `DOC.rel`**，且 name 在书库侧**带完整后缀**（见 1.3）。

### 1.3 命名契约（最容易在重写时做错的一段）

`store._scan_sub`（`store.py:509-533`）给三种文件定了不同的 `name`：

```python
elif p.suffix in LIBRARY_EXTS:
    # name 保留完整后缀（路由 /doc/<dom>/<sub>/<name>），不读 frontmatter
    name, title, is_html = relp, p.stem + p.suffix, False
```

- **`.md`**：`name` = 去掉 `.md` 的相对路径（URL 段也不带后缀）。
- **书库**：`name` = **含后缀**的相对路径 `relp`；`title` = `stem + suffix`（即 `title` 是"文件名带扩展名"，不是干净书名 —— 这是本项目的实际行为，树里显示 `长夜.txt`，`DOC.title` 也是它）。
- **`.html` 独立篇**：`name` = `relp`，`title` = `stem + ".html"`。

于是 `kb-novel.js` 里所有"书名"都取自 `DOC.title`（含后缀），章节兜底标题也因此带后缀 —— 见 §2.4 的 `fallbackTitle`。

URL 侧的规整只有一处实现，必须带走（`static/kb-core.js:57-65`）：

```js
util.docUrl = rel => { const s = String(rel).replace(/\.md$/, "").split("/").filter(Boolean);
  if (s.length === 2) s = [s[0], "_root", s[1]];   // 域根散文件的哨兵子域
  return "/doc/" + s.map(encodeURIComponent).join("/"); };
util.rawUrl = rel => "/raw/" + rel.split("/").filter(Boolean).map(encodeURIComponent).join("/");
```

**注意**：`replace(/\.md$/,"")` 只削 `.md`，书库后缀原样进 URL；`_root` 只在"rel 恰好两段"时插入，三段以上（目录型书）直接用真实子域。前后端必须同集合，否则"树给的链接"和"路由能解析的链接"会分叉（本项目踩过，见 §7 坑 13）。

### 1.4 单文件型 vs 目录型（一本书一个文件夹）

本项目**没有专门的"书目录"概念**，目录型是靠通用的递归扫描自然成立的：`_visible_sub_files` 用 `os.walk` 且只剪 `_` 前缀目录（`store.py:320-327`），嵌套目录里的文件以**带斜杠的相对路径**当 `name`，路由 `/doc/<domain>/<sub>/<path:name>` 用 `<path:...>` 转换器接住多段（`routes_pages.py:184`），`find_doc` 再拿 `sdir / name` 命中（`store.py:557-562`）。

结论与约束：

- `小说/某书/上册.txt`、`小说/某书/下册.txt` → 同一个子域下两条文档，名字分别是 `某书/上册.txt`、`某书/下册.txt`。**分卷之间没有任何关联**（没有"同属一本书"的元数据，阅读进度也是按 rel 各存一份）。
- `小说/某书/_assets/cover.png` → **不出现在树里**（`_` 段被剪，`is_visible_doc` 同样排除，路由 `find_doc` 也拒绝），但 `/raw/小说/某书/_assets/cover.png` 可直服（`MEDIA_EXTS` 在白名单里）。这是 `_assets` 的全部语义：**不可索引、可取字节**。
- 图片型漫画（`*.png/*.jpg` 散放在子目录）→ 因为 `MEDIA_EXTS` **不在** `SERVABLE∪LIBRARY` 里，**既不进树也不能作为"文档"打开**，只能被 md/html 引用。本项目**没有做漫画阅读器**（没做 CBZ/CBR、没做逐页翻），这是明确的空缺。
- **注意 `find_doc` 的候选顺序**（`store.py:557`）：`(sdir/f"{name}.md", sdir/name, sdir/f"{name}.html")` —— 书库的 name 自带后缀，所以第 1 个候选 `a.txt.md` 通常不存在，靠第 2 个命中。若目录里同时存在 `a.txt` 与 `a.txt.md`，**`.md` 优先**（会被当普通文档渲染），这是隐式规则，重做时要么保留要么显式改掉。

### 1.5 三类旁挂件（sidecar）的挂法

| 旁挂 | 命名 | 代码 | 书库相关行为 |
|---|---|---|---|
| 备注 / 章评 | `<完整文件名>.notes.md` | `store.notes_path` 567 → `doc_path.name + ".notes.md"` | 于是 `长夜.txt.notes.md`、`book.epub.notes.md`。追加制：`- [YYYY-MM-DD HH:MM] 文本\n`（`routes_edit.py:99`）；读回按行正则 `- \[(.+?)\] (.*)` 并 `list(reversed(...))` = **最新在前**（`read_notes` 571-580） |
| 美化版 HTML twin | 同目录、**去一个后缀**的 `.html` | `app.py:193` `p.with_name(p.stem + ".html")` | **两处口径不一致，必须知道**：扫描侧算的是 `sdir/(name + ".html")`（`store.py:531`），书库 name 带后缀 → 找 `长夜.txt.html`；而 `collect_doc` 找 `长夜.html`。对 `.md` 两者等价，对书库不等价 → 书库的"美化版"入口实际永远不成立（右栏默认页签、crumb 的「新标签页」都不会出现）。重做时按一个口径写死。 |
| 派生索引 | 不在语料树内 | `indexes/index.db`、`rag.db` | **书库完全不进索引**：`md_files` 只收 `.md`（`store.py:305-312`）、`fts.build_index` 走 `md_files`、RAG 走 `md_corpus_files`。因此书库域的搜索钮是恒 0 结果 —— 解法是分类学里 `"search": false`（`content/_meta/taxonomy.json` 的域条目 → `store.load_taxonomy` 读成 `tax["search_hidden"]` → 模板过滤），**不是**在模板里抄一份域名单（不变量 5；台账 §6 第 30 行） |

`.notes.md` 的"不可见"口径在四条路径上都必须一致，否则会凭空多出幽灵文档：`is_visible_doc`（`store.py:301`）、`_visible_sub_files`（324）、`_tree_sig`（345，**排除是为了备注不失效缓存**）、`find_doc`（558）、`inbox_iter`（451）。`sidecars_of`（584）在移动/重命名时把 `.notes.md` 与同名 `.html` 一起搬走。

### 1.6 派生元数据：`has_html` / `notes` / `size`

`collect_doc` 对书库只给：`rel / title / fm={}/ md=None / is_html=false / favorite=false / notes=[…磁盘真实旁挂…] / size / domain / sub / name / *_label`。`size` 是 **`f"{bytes/1024:.1f} KB"` 字符串**（`app.py:201`），`kb-novel.js` 的调用侧再换算 MiB（`app.js:252` `(parseFloat(DOC.size)/1024).toFixed(1)`）—— 这个换算只为拿到"多少 MB"的口头数，**当前没有任何分支真的用它**（`N.renderTxt(wrap, rawHref, rel, sizeMiB)` 收了 `sizeMiB` 却没使用，见 §6.C 的"别照搬"清单）。

---

## 2. txt 线

入口：`app.js:278` → `KBNOVEL.renderTxt($("#lib-txt"), rawHref, DOC.rel, sizeMiB)`；实现在 `kb-novel.js:434-721`。整条链是：

```
fetch(rawHref) → r.arrayBuffer() → decodeTxt(bytes) → buildChapters(text, DOC.title)
→ 建 DOM（工具栏 + .nv-stage > .nv-pages + 搜索浮层）
→ registerPaneToc(章节 → 右栏「目录」页签)
→ renderScroll(0) 或 renderPaged(0)
→ rewireChrome()（下载/章评/朗读/滚动/搜索 全部重新接线）→ buildToc()
```

`rawHref` 是 `/raw/<rel>`（逐段 encode），`rel` 是 `content/` 下的 posix 相对路径 —— **`rel` 是进度与章评的唯一 key**，两者都按它取（`kb-nv-pos:<rel>`、`POST /api/note {path:rel}`）。

### 2.1 编码探测：判据与降级顺序（`decodeTxt`，`kb-novel.js:397-409`）

```js
function decodeTxt(buf) {
  var bytes = new Uint8Array(buf), t;
  if (bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF) {
    t = new TextDecoder("utf-8").decode(bytes.slice(3));        // 显式剥 UTF-8 BOM
  } else {
    try { t = new TextDecoder("utf-8", { fatal: true }).decode(bytes); }
    catch (e) {
      try { t = new TextDecoder("gb18030").decode(bytes); }
      catch (e2) { t = new TextDecoder("big5").decode(bytes); }
    }
  }
  return t;
}
```

要点逐条：

1. **只有 UTF-8 BOM 这一种 BOM 被特判**（`EF BB BF`）。UTF-16 的 `FF FE` / `FE FF` **不识别** —— 会走 fatal UTF-8 失败、落进 gb18030，得到满屏 mojibake。本项目没做 UTF-16（见"本项目没做"）。
2. BOM 分支其实是**冗余保险**：`TextDecoder("utf-8")` 默认 `ignoreBOM:false`，本来就会吃掉前导 BOM。测试的变异验证记录写得很明白（`test_js_props.py:31-32`）：摘掉这条 if **全套照样绿**，属于"等价变异"。保留它的理由是**不依赖运行时默认值**，重做时可以删但要知道删的是保险不是逻辑。
3. **判据是"能不能严格解成 UTF-8"，不是猜字节**。`{fatal:true}` 让非法序列抛异常，异常才降级 —— 不要用"统计高位字节比例"这类启发式（本项目实测：`b"\xff\xfe\x00\x01\xe9\x94\x99"` 这种纯垃圾也必须能返回字符串而不抛）。
4. 降级目标是 **`gb18030` 而不是 `gbk`**：gb18030 是 GBK/GB2312 的超集，且它**几乎任何字节序列都解得动**（非法序列出 U+FFFD 而不抛）—— 所以 `catch (e2) → big5` 这一层在实践中基本不可达，它只在运行时不提供 `big5`/`gb18030` 标签时才有意义。留着无害。
5. **失败时不报错、不提示、不二次确认**：`decodeTxt` 永远返回一个字符串。唯一的错误出口是 `fetch` 失败（非 2xx → `throw new Error("HTTP "+status)`），由 `renderTxt` 的 `.catch` 渲染成 `读取失败：<msg>`（`kb-novel.js:717-720`）。
6. 契约测试：`test_js_props.py` 的 `decodeTxt 对 8 种字节样本均不抛异常` / `BOM 被剥掉（首字符不是 U+FEFF，正文从「第一章」开始）` / `非法 UTF-8 自动降级到 GB18030（第三章能读出来）` / `空文件不崩（len=0 且有章节结论）` / `20 万字单行不崩且不挂起`。样本在 `TXT_FIXTURES`（`bom-utf8.txt / plain-utf8.txt / gb18030.txt / invalid-utf8.txt / empty.txt / nul.txt / crlf.txt / huge-line.txt`）。

### 2.2 章节切分：完整规则（`CHAP_RE` + `buildChapters`，`kb-novel.js:395-432`）

```js
var CHAP_RE = /^\s*(第[0-9零一二三四五六七八九十百千两]+[章回卷节部集]|Chapter\s+\d+|CHAPTER\s+\d+|序[章言]?|楔子|引子|番外[篇·]?\S*|尾声|终章|后记)\s*[^\n]{0,40}$/;
```

`buildChapters` 全文（不到 20 行，逐字照搬即可）：

```js
function buildChapters(text, fallbackTitle) {
  var lines = String(text == null ? "" : text).split(/\r?\n/);
  var chaps = [], cur = { title: "", start: 0, lines: [] };
  lines.forEach(function (ln, i) {
    if (CHAP_RE.test(ln) && ln.trim().length <= 42) {
      if (cur.lines.length || cur.title) chaps.push(cur);
      cur = { title: ln.trim(), start: i, lines: [] };
    } else cur.lines.push(ln);
  });
  if (cur.lines.length || cur.title) chaps.push(cur);
  if (chaps.filter(c => c.title).length < 2) { /* 兜底：整篇 1 章 */ }
  chaps.forEach(c => { c.paras = c.lines.join("\n").replace(/^\n+/,"")
    .split(/\n+/).filter(p => p.trim()); });
  return chaps;
}
```

规则拆解（每一条都有对应断言，见 §6）：

- **行级判定 + 二次长度闸**：`CHAP_RE` 的尾部 `[^\n]{0,40}` 已经限制了后缀长度，代码又叠了 `ln.trim().length <= 42`。**两道闸合起来的实际语义**是"标题行必须短"：42 包含"第X章"本体 + 空格 + 至多 40 字符的书名。所以 `第一章这是一串长得超过四十二个字符的章节标题…` 这类行**不会被当章节**，整篇退回兜底。别只搬一条。
- **标题与正文的分离**：命中的那一行**整行成为 title**（`ln.trim()`），不进 `lines`；其余全部进 `cur.lines`。标题之后的同一行残留（"第一章 长夜将尽"里的"长夜将尽"）算进标题而不是正文 —— 这是设计选择，本项目不做"标题/副标题分离"。
- **`start` 字段**存的是**原始行号**，但渲染只用 `paras`，`start` 当前无人消费（留给"原文定位/行内高亮"扩展位）。
- **两处 `push` 的判据是 `||` 不是 `&&`**：`cur.lines.length || cur.title`。这决定了两个边角 —— ① 正文之后紧跟一个只有标题没有正文的末章，必须仍然成章（`trailing-title` 样本）；② 第一个标题之前的正文（引子/序言）必须独立成一条无 title 的章（`preamble` 样本）。改成 `&&` 时"不丢字符"类断言**测不出来**（兜底会把碎片重新捞回成一整章），必须钉"每样本的带标题章数"。这是本项目最贵的一条测试方法学教训（`test_js_props.py:190-199`）。
- **兜底条件 `< 2` 而不是 `== 0`**：只识别出 1 个标题的书会被判"切分不可信"，整篇当 1 章（标题行退回正文里，标题取 `fallbackTitle`）。这条很反直觉但确实是有意的：单点误判（某一行正文恰好以"第一节"开头）会毁掉整本书的分章。断言：`超长标题不被当成章节标记（退回全文兜底，1 章）`、`txt 样本的章节数都 ≥1（永不出空书）`、`纯空白文本仍返回 1 章`。
- **兜底标题的取值顺序**：`fallbackTitle || (window.DOC && DOC.title) || "全文"`（`kb-novel.js:425`）。`fallbackTitle` 是**为可测性新加的第二参** —— 之前直接偷读全局 `DOC`，任何独立测试都得先造假 DOC。重做时保留这个"显式传参 + 全局兜底"的形状。
- **序言/楔子/番外/卷册**：全部**平铺**，没有层级。`第X卷` 也在词表里 → 一卷会成为一个"章"条目，与其中的 `第X章` 平级显示在同一个 TOC 里（视觉上没有缩进关系）。本项目**没有做卷/章两层树**。
- **段落化 = 连续非空行合并**：`join("\n").split(/\n+/)` —— 单个换行会被吞掉（散文排版语义），段首缩进/空格靠 CSS `text-indent:2em` 表达而不是保留原字符（每段渲染前还会 `p.trim()`，`kb-novel.js:491`）。**测试侧必须按 `/\n+/` 拆回去**，写成 `split('\n+')`（字面量）永远拆不开 —— 作者自己栽过一次，注释留在 `test_js_props.py:308`。
- **CRLF**：入口就是 `split(/\r?\n/)`，所以 `\r` 不会进 title 也不会进段落。断言：`带标题章数逐样本对得上（含 …crlf）`。
- **超长单章 / 超长单行**：**不再二次切分**。单行 20 万字也照样作为一个段落塞进 DOM（`huge-line.txt` 只断"不崩、不挂起"）。真正的性能手段是懒渲染：首屏只实例化起点附近 **8 章**，其余用占位（`placeholder` + `estHeight`），IntersectionObserver 进视口才 `materialize`（`kb-novel.js:543-560`）。占位高度估算是 `estHeight`（496-500）：`max(140, (有标题?50:0) + ceil(字数/38) * (字号×行高) + 段数 × 段距)` —— **每行 38 字**这个常数是中文排版下的经验值，换语言要重标。

### 2.3 TOC（目录）怎么从章节生成

**txt 的 TOC 就是章节数组本身**，没有独立解析步骤，也不读文件开头的"目录页"（本项目**没有做**"识别正文前置目录块并跳过"，若原书正文开头带目录，那些行会被当正文塞进首章）。

挂载方式很特别：**不在阅读器内部放目录，而是灌进阅读器右栏的「目录」页签**（`#pane-toc`，`workbench.html:82`）：

```js
// kb-novel.js:459 —— txt 侧
N.registerPaneToc(chaps.map(c => c.title || "（开头）"), function (i) { /* 跳转 */ });
```

`registerPaneToc/paintPaneToc/markPaneToc`（`kb-novel.js:361-392`）是一个模块级单例 `_pt = {items, jump, cur}`：

- `paintPaneToc` 渲染 `<a data-pt="i">`，空标题回落 `（无标题）`；
- 事件用 `pane.dataset.nvWired` **只绑一次**（委托到 pane，重绘不重复绑）；
- `markPaneToc(i)` 搬 `.on` 并 `scrollIntoView({block:"nearest"})`；
- `app.js:685` 的 `buildToc()` 分流条件是 `/\.(txt|epub)$/i.test(DOC.name) && KBNOVEL.hasPaneToc()` → 命中就 `paintPaneToc(pane)` 并 **直接 return**，不走 markdown 的标题扫描。`hasPaneToc()` 这道守卫是**时序必需**：`renderTxt` 是异步的（fetch + decode），`buildToc` 可能在章节注册前被调用，没有守卫就会把阅读器的目录擦成"本文没有小节标题"空态。

当前章跟随（滚动模式）用第二个 IntersectionObserver `spyIO`，`rootMargin: "0px 0px -85% 0px"`（`kb-novel.js:516-526`）—— 即"进入视口顶部 15% 才算当前章"，避免读到章尾就提前翻页码。分页模式则直接 `setCur(i)`。`setCur` 写的进度百分比**两种模式口径不同**（`kb-novel.js:529-531`）：分页 = `(i+1)/章数`，滚动 = `(scrollTop+clientHeight)/scrollHeight`。这不是疏漏，是两种模式下"读过多少"的两种自然定义。

### 2.4 阅读位置（续读）与状态存储

- 键：`"kb-nv-pos:" + rel`（`posKey`，`kb-novel.js:245`），值 `{ch, y}`（txt）或 `{cfi}`（epub）。**同一个键前缀两种 payload 形状**，靠字段存在性判别：txt 侧读时判 `typeof pos.ch === "number"`，epub 侧判 `cfi && cfi.cfi`。重做时**不要假设只有一个形状**（epub 的 CFI 记录喂给 txt 必须安全忽略，反之亦然）。
- 写入：txt 滚动模式在 `stage` 的 scroll 上**防抖 500ms** 存 `{ch:curCh, y:scrollTop-sec.offsetTop}`（`kb-novel.js:575-584`）；分页模式在每次 `renderPaged` 存 `{ch:i, y:0}`。
- 恢复：`renderScroll` 在 `requestAnimationFrame` 里读位置，若 `pos.ch !== startCh` 就改跳 `pos.ch`，再叠 `pos.y`（561-570）。
- **`savePos`/`loadPos` 各自的 `try/catch` 是唯一防线**，不是装饰：循环引用的对象（`JSON.stringify` 抛 TypeError）、localStorage 里的坏 JSON、2000 字超长 rel、被塞进去的标量（`123`/`"str"`/`null`/`[]`）都必须不抛。契约：`savePos/loadPos 对 9 种输入均不抛`、`9 条 pos 探针结果全为 true`，探针名 `roundtrip / overwrite / isolated / weirdRel / missingKey / circular / undefinedDropped / corruptJson / scalarStored`。**`loadPos` 对合法 JSON 标量只负责"不抛 + 原样给回"**，判定留给调用方（`scalarStored` 钉的就是这个语义）。
- 注意 `resetPaneToc`（`kb-novel.js:391`）**当前没有任何调用方** —— 换书时旧章节列表会留在 `_pt` 里直到新的 `registerPaneToc` 覆盖。若新项目要"离开书库就清空右栏目录"，得自己调它。

### 2.5 本项目没做（txt 线）

书签/句内高亮持久化、多分卷合并成一本、识别并跳过正文开头的"目录页"、UTF-16/GB2312 之外的编码（Big5 只是名义分支）、章节层级（卷/章两层）、全文索引（书库不进 FTS/RAG，书内搜索是纯前端遍历）、繁简转换、按字号重新分页（CSS 列）—— 都没有。

---

## 3. epub 线

入口 `app.js:266` → `KBNOVEL.renderEpub($("#lib-epub"), rawHref, DOC.rel)`（`kb-novel.js:796-1017`）。第三方库全部 vendored 在本地、懒加载、不联网：

```js
// kb-novel.js:725-732：单例 Promise，先 JSZip 后 epub.js（顺序依赖：epub.min.js 运行时要 JSZip 在场）
function ensureEpubLib() {
  if (window.ePub) return Promise.resolve();
  if (!_epubLibLoading) _epubLibLoading = loadScript("/static/vendor/jszip.min.js")
    .then(function () { return loadScript("/static/vendor/epub.min.js"); });
  return _epubLibLoading;
}
```

文件：`static/vendor/jszip.min.js`（97KB）、`static/vendor/epub.min.js`（223KB，vendored 的 epub.js）、`static/vendor/xlsx.full.min.js`（SheetJS，仅 xlsx 用）。

### 3.1 为什么必须先把 OPF/NCX 里的 href 就地解码（`normalizeEpubBytes`，`kb-novel.js:746-786`）

**动机（源码注释原样记录的事实）**：多看版等工具生成的 epub，把非法文件名字符（`* | :`）在 **OPF manifest / NCX 里做了百分号编码**，但 **zip 条目存的是原始名**。vendored `epub.min.js` 拿编码后的 href 直查 JSZip → 命中不了 → **整本空白**；而 nav 的编码 href 与 spine 的编码 href 还不一致 → 点目录报 **No Section Found**。这就是台账里"近三次线上 bug"之二。

**做法**（逐条都是判据，不是风格）：

1. `META-INF/container.xml` 正则抠 `full-path="…"` → `decodeAmp`（`&amp;` → `&`）得 OPF 路径；`prefix` = OPF 路径的目录部分（含尾斜杠，OPF 在根时为空串）。**`container.xml` 不存在 / 没有 `full-path` / `zip.file(opfPath)` 取不到 → 立即 `return null`**（= 不认识这个包，一律不动手，把原始字节交给 epub.js 自己试）。
2. `fixHref(raw)` 的**三段判据，顺序不可换**：

   ```js
   var clean = decodeAmp(raw.split("#")[0]);
   if (!clean) return raw;
   if (zip.file(prefix + clean)) return raw;            // ① 编码形式本来就能命中：不动
   var d = dec(clean);                                   // decodeURIComponent，失败原样
   if (d === clean || !zip.file(prefix + d)) return raw; // ② 解码后也查不到：不动
   fixes++;  return d + frag;                            // ③ 只有"编码查不到 & 解码查得到"才改
   ```
   `frag` 是 `#` 之后的片段（保留）。**② 里 `d === clean` 这一项**很关键：完全没编码的 href 不计数、不重写，保证"正常书返回 null、零改动"（`zip.generateAsync` 一次都不跑）。
3. 对 OPF 只替换 `<item … href="…">`；NCX/nav 同时替换 `src="…"` 与 `href="…"`，且**先 `decodeAmp` 再 `fixHref`**（与 OPF 支路不同，因为 NCX 里的 `&amp;` 更常见）。
4. **找 TOC 文件本身是"两条正则互为回退"**，这是属性顺序依赖：`/<item\b[^>]*href="([^"]+\.ncx)"[^>]*>/` 先试，失败再试 `media-type="application/x-dtbncx\+xml"` 在前、`href` 在后的写法；EPUB3 的 nav 同理两条（`properties="…nav…"` 在 href 前/后各一条）。**OPF 不保证属性顺序，所以任何单条正则都会漏书。**
5. `zip.file(opfPath, opfNew)` / `zip.file(ncxPath, navNew)` 就地替换条目内容，然后 **仅当 `fixes > 0`** 才 `zip.generateAsync({ type:"arraybuffer", compression:"STORE" })` 回一个新 ArrayBuffer；否则 `return null`。STORE（不重压缩）是为了省 CPU 并避免改写 zip 内部结构。
6. 契约：`正常书 normalize 返回 null（绝不多改一遍）`、`多看版错位书返回新 ArrayBuffer 且重写后零悬空 href`（测试把新 ArrayBuffer 再解一遍，逐条 `href` 检查 `zip.file` 可命中，`dangling === 0`）、`missing-target/no-container/wrong-opf-path/empty-zip → null（不认识的包一律不动手）`、`truncated/zero-byte/garbage/nul-name 有明确结论（null 或 error），不是静默挂死`、`normalizeEpubBytes 无一挂起（8 秒超时未触发）`。样本见 `test_js_props.py:149-170` 的 `FIXTURES`（10 个现造 zip）。
7. **两个版本要拆开**：`normalizeEpub(rawHref)`（URL 版，内部再 fetch）与 `normalizeEpubBytes(buf)`（字节版）。拆的理由写在源码注释里：畸形样本可以直接喂字节，不必"先上传成真书再抓回来"。测试与产品共用字节版。

### 3.2 为什么 epub.js 只认 ArrayBuffer、不认 blob URL

`kb-novel.js:812-814`：

```js
var epubUrl = rawHref;
try { var fixed = await normalizeEpub(rawHref); if (fixed) epubUrl = fixed; } catch (e) {}
var book = window.ePub(epubUrl);
```

`ePub()` 拿到的是**原始 `/raw/<rel>` URL**（epub.js 自己 fetch + range 请求）或 **`ArrayBuffer`**（重写后的包）。历史上踩过第三条路：**把重写结果包成 `URL.createObjectURL(blob)` 传进去会卡死**（无报错、无渲染、不返回）。因此判据是"返回 ArrayBuffer"而不是"返回一个可 fetch 的 URL"，测试侧用 `Promise.race` + 8 秒超时把**挂起本身**当失败信号（`normalizeEpubBytes 无一挂起`）。重做时：要么交字节，要么交原始 URL，**不要自造 blob/data URL**。

代价要如实说：走 ArrayBuffer 分支时，同一个 epub 字节会被 fetch **两次**（`normalizeEpub` 一次、书内搜索的 `ensureTexts` 又一次，`kb-novel.js:874`）。本地读盘无所谓，**搬到网络后端时应改成一次 fetch、共享 ArrayBuffer**。

### 3.3 主题/排版为什么必须直接往 iframe 插 `<style>`

**坑的原始形状**：vendored `epub.min.js` 的 `rendition.themes.default({...})` **对已经渲染出来的 section 文档不生效** —— 改字号/底色后当前页毫无变化（`themes.fontSize(scale+"%")` 里 `scale` 恒为 100，等于没做事，代码里留着只是历史痕迹）。

解法：`themeCss()` 生成一整段带 `!important` 的 CSS，`injectTheme()` 遍历阅读器容器里**所有 iframe**，往每个 `contentDocument.head` 插/更新 `<style id="kb-nv-epub">`（`kb-novel.js:825-852`）：

- `html{font-size/line-height/letter-spacing/font-family/background/color !important}`；
- `body{background:transparent !important; max-width:<widthMaxStr(widthRem)>; margin:0 auto; padding:8px 14px}`；
- `p,div,li,td,h1..h5`、`a/a:link/a:visited/a:hover` 全部强制成 `c.ink`（否则书自带样式会把链接画成蓝紫）；
- `p{margin:<gap>px 0 !important; font-size:100% !important}` + 可选 `text-indent:2em !important`。

**时机是三次，缺一次就漏**：`applyTheme()` 首帧一次、`setTimeout(injectTheme, 350)` 一次（`renderTo` 后 section iframe 可能还没挂载）、每次 `relocated` 事件再来一次（换章时新 iframe 出现）。跨 iframe 读 `contentDocument` 在同源 `/raw` 下才成立 —— **新项目若把语料放 CDN/不同源，这条路直接失效**，得改成 epub.js 的 `contents.each()` 注入或 postMessage。

`flow`（连续滚动 ↔ 分页）与主题不同，它必须走 epub.js 的 API，而 **`rendition.flow()` 会触发 `relocated` 从而把阅读位置重置回章首**。所以偏好处理器里有一道"只有真变了才调用"的守卫（`kb-novel.js:859-867`）：

```js
var lastFlow = p.flow === "page" ? "paginated" : "scrolled-doc";
var prefH = function () {
  var wantFlow = N.get().flow === "page" ? "paginated" : "scrolled-doc";
  if (wantFlow !== lastFlow) { lastFlow = wantFlow; rendition.flow(wantFlow); }  // 否则进度被重置
  applyTheme();
};
```

**这是全套 epub 线最隐蔽的顺序依赖**：没有这道守卫，用户每调一次字号，进度就回章首。台账 §2 也诚实登记过一条相关未确证项（切 scroll→page 后 CFI 从 `/6/2!/4/1:0` 变成 `/6/8!/4/1:0`，无法判定是"跳章"还是"分页模式 CFI 基准不同"）—— 重做时值得先把这个判据做实。

模块级单例也必须处理：`_epubBook` / `_epubRendition` 在每次 `renderEpub` 开头 `destroy()` 再置 null（`kb-novel.js:801-802`），否则切书会把上一本的 rendition 留在内存与 DOM 事件上。

### 3.4 封面图空白的编码别名坑

多看版书的封面/插图常因**图片文件名编码错乱**加载失败，留下大片空白，视觉上像"正文没了"（台账"近三次线上 bug"之三）。处理在 `injectTheme()` 尾部（`kb-novel.js:845-849`）：

```js
d.querySelectorAll("img").forEach(function (im) {
  if (im.complete && im.naturalWidth === 0) im.style.display = "none";   // 已失败的直接藏
  else if (!im.dataset.nvErr) { im.dataset.nvErr = "1";
    im.addEventListener("error", function () { im.style.display = "none"; }); }
});
```

三点值得注意：① 判据用 `complete && naturalWidth===0`（已经下完但解码失败/0 字节）而不是只看 `naturalWidth===0`（那会误藏"尚未加载"的图）；② 用 `dataset.nvErr` 去重 —— 因为 `injectTheme` 会被反复调用（首帧/350ms/每次 relocated），不加守卫就会给同一张图挂一串 error 监听；③ 这只是**掩盖症状**：图没显示出来。真正的修法是走 §3.1 的 href 解码（图片 href 也在 `<item>` 里，会被一起修正），但历史书里仍有 zip 条目名与 href 都对不上的情况，所以两层都保留。本项目**没有**做"从 zip 里按解码名重找图片并 rewrite src"。

### 3.5 两种模式：分页与连续滚动

- `flow === "page"` → `paginated`（epub.js 自己按容器宽高分栏，←→/上页下页 = `rendition.prev()/next()`）；否则 `scrolled-doc`（整章连续滚动，跨章需要继续翻）。
- 工具栏一律 `pager:"page"`、`autoScroll:false`（`kb-novel.js:803`）—— **epub 侧没有自动滚动**（那是 txt 的能力，`renderEpub` 不接）。文案随 pager 变"上页/下页"。
- 键盘：`wrap.tabIndex=0` + `keydown`，`ArrowLeft/ArrowRight` 在 epub 里**无条件**生效（txt 里只在分页模式生效）。
- 宽度：`body{max-width}` 由偏好滑杆给（`widthMaxStr`：`>=100` → `none`），`spread:"none"`、`width/height:"100%"`。

### 3.6 章评 / 搜索 / 朗读各自接在哪

| 能力 | 接线点 | 数据来源与关键细节 |
|---|---|---|
| 目录（TOC） | `book.loaded.navigation` → 递归 `walk(toc)` 展平（`kb-novel.js:911-919`）→ `registerPaneToc(flat.labels, jump)` | href 一律 `decodeAmp((it.href\|\|"").split("#")[0])`；点击 → `rendition.display(f.href)`。**展平是刻意的**（不做层级缩进）。当前章匹配（`relocated`，926-946）：先找 `flat[k].href === curHref`，再退一步 `curHref.indexOf(flat[k].href) === 0`（前缀命中）—— 因为 epub.js 给的 href 可能带子路径/片段。 |
| 进度 | `book.locations.generate(1024)`（947）+ `percentageFromCfi(loc.start.cfi)` | `generate` 是异步且**没被 await**，早期读数会 NaN → 代码判 `isNaN(pct)` 就不显示百分比。取位置时 `try/catch` 包住。重做时若不 await 就保留 NaN 守卫。 |
| 续读 | 先 `await rendition.display()`，再 `if (cfi.cfi) await rendition.display(cfi.cfi)`（904-909）；`relocated` 里**防抖 1500ms** 存 `{cfi: loc.start.cfi}` | 两次 display 是有意的（先出内容再跳位置），但代价是首屏可能闪一下章首。 |
| 章评 | `.nv-note-btn` → `notePrompt(rel, 当前章 label)`（956-959） | 当前章 label 由 `flat.filter(f => f.href === curHref)[0]` 取；取不到就传空串 → 章评不带 `〔章评·…〕` 前缀。**注意这里用的是精确相等**（不是 relocated 里那套前缀匹配），所以带片段的路径下章评可能不带章名 —— 已知的不一致。 |
| 书内搜索 | `.nv-find-btn` + `.nv-find-in`（回车下一处 / Esc 关）→ `ensureTexts()`（872-902） | epub.js **不提供全文检索**，所以直读 zip：spine 取 `book.spine.get(i)` 且**上限 800 次迭代**（防坏包死循环）；若 spine 拿不到就 `zip.forEach` 扫 `/\.x?html?$/i` 兜底；条目查找是**四级回退** `zip.file(href) \|\| zip.file(prefix+href) \|\| zip.file(decodeURIComponent(href)) \|\| zip.file(prefix+decodeURIComponent(href))` —— 正是为了同时容忍 §3.1 那类编码错位；`prefix` 取 `book.packaging.prefix`。文本用 `DOMParser().parseFromString(html,"text/html").body.textContent`，再 `.replace(/\s+\n/g,"\n").trim()`，空段跳过；标题用 navigation 展平出来的**面包屑** `path`（` › ` 连接），没有就回落 `href` 的最后一段。命中上限 100 条、`indexOf(lq, at+q.length)` 前进（不重叠）、snip 前后各 12/24 字。跳转 = `rendition.display(h.href)`（**不定位到章内偏移**，本项目没做）。 |
| 朗读 | `.nv-tts`（960-972） | 段落来源是**当前渲染的 iframe DOM**，不是 zip：`rendition.getContents()[0].document.querySelectorAll("p,h1,h2,h3")` → `map(el=>el.textContent.trim()).filter(Boolean)`；空则 toast「当前章节没有可朗读的文字」。因此朗读永远只念**当前可见的那份内容**，与 txt 侧"整章段落队列"语义不同。 |
| 下载 | `.nv-dl` → 造 `<a href=rawHref download=DOC.name>` 并 `.click()` | 走 `/raw`，不经后端包装。测试把 `HTMLAnchorElement.prototype.click` 换成记账函数来断属性。 |

### 3.7 失败面

`renderEpub` 整体包在 `(async function(){…})().catch(...)`，任何一步失败都渲染：`EPUB 解析失败：<msg>` + 一个「下载后用阅读器打开」的 `<a download>`（`kb-novel.js:1012-1016`）。`normalizeEpub` 外层单独 `try/catch`（**解码失败绝不影响开书**，最坏就是不修 href），`registerPaneToc`、`locations.generate`、`getContents()` 各自 `try/catch`。**原则：解析链上每一步都允许失败，但失败必须退化成"能看"而不是"空白页"。**

---

## 4. 阅读偏好

### 4.1 存储与键名

| 键 | 形状 | 归属 |
|---|---|---|
| `kb-novel-pref` | `norm()` 后的对象 | 书库/小说排版与阅读偏好（本文主题） |
| `kb-nv-pos:<rel>` | `{ch,y}`（txt）或 `{cfi}`（epub） | 每本书的阅读位置 |
| `kb-readpref` | 对象 | **文章正文**的排版偏好（`static/kb-core.js:240+`，与书库偏好**两套独立**，各自有 `--kb-*` / `--nv-*` 变量） |
| `kb-theme` / `kb-skin` / `kb-force-motion` | 字符串 | 明暗 / 皮肤 / 动效开关 |
| `kb-tree` / `kb-panels` / `kb-tree-open` / `kb-last-doc` | JSON | 树缓存、折叠态、上次打开 |

全部 localStorage、全部"读时钳制"，**不写进语料文件**（不变量 6/1：语料零污染）。`kb-novel-pref` 的读写各只有一处（`N.get`/`N.set`/`N.reset`，`kb-novel.js:59-76`），且都包 `try/catch`（隐私模式/配额满不许崩）。

### 4.2 有哪些开关（默认值 + 取值区间）

```js
// kb-novel.js:29-31
var DEF = { size: 17, line: 1.9, track: 0.5, gap: 10, indent: 1, widthRem: 44,
  font: "default", theme: "white", bgCustom: "", flow: "scroll", rate: 1 };
var NUM_RANGE = { size: [14, 26], line: [1.5, 2.6], track: [0, 3], gap: [4, 24],
  rate: [0.5, 3], widthRem: [24, 100] };
```

面板分三组（断言 `面板分三组（排版 / 外观 / 阅读）` 要求组名与顺序逐字相等）：**排版**（字号 / 行高 / 字间距 / 段间距 / 正文宽度 / 首行缩进开关）、**外观**（阅读字体 + 系统字体按钮、5 个护眼主题 + 自定义底色）、**阅读**（txt 阅读模式 scroll/page、朗读与自动滚动共用速率 rate）。加一个「恢复默认」。控件 id 全部是 `kb-npref-<key>`，读数 `<output>` id 是 `kb-npref-<key>-o`（断言依赖这个命名）。

`norm()` 的**执行顺序**是有意义的（`kb-novel.js:38-58`）：① 先做旧值迁移 `WIDTH_LEGACY`（`narrow/mid/wide/full → 34/44/56/100`，**仅当 `v.width` 存在且 `v.widthRem === undefined`** 时才迁）；② 覆盖 DEF（`undefined/null/""` 都视为"没给"）；③ 才做数值钳制；④ 非数值项逐个回退（`theme` 不在 `THEMES` → `white`；`flow` 不在 `scroll/page` → `scroll`；`indent` 一律归一到 `0/1`；`bgCustom` 只接受 `/^#[0-9a-fA-F]{6}$/`，否则清空）。**先迁后钳**这个顺序丢了，旧存档的 `width:"full"` 就会被钳成 24。

### 4.3 作用域：为什么只染书库阅读区

- 变量前缀 `--nv-*` 全部由 `N.apply()` 写到 `documentElement`，但**消费它们的只有 `.nv-stage / .nv-pages / .nv-p / .nv-chap-h`**（`static/pages/novel.css:24-36`），而 `.nv-*` 只存在于书库阅读态。
- 布局层由模板加类：`{% set is_lib = doc.name.endswith(('.txt','.pdf','.xlsx','.epub','.mobi')) %}`（`workbench.html:40`）→ `<section class="panel article-wrap nv-mode">`，`nv-mode` 把正文区改成"整屏高度 + 不滚动 + flex 列"（`novel.css:3-10`），滚动条归 `.nv-stage` 自己（**阅读区内滚动，不是整页滚动** —— 搜索/目录跟随/自动滚动的判据都建立在"滚动容器是 `.nv-stage`"之上）。
- 底色与墨色成对：`THEMES`（`white/cream/parchment/sage/night` 各带 `bg`+`ink`）；自定义底色优先于主题，文字色由 `N.inkFor(hex)` 按亮度 `(0.299R+0.587G+0.114B) > 150` 自动选深/浅（断言 `深色底自动配浅色字`）。点主题按钮会同时把 `bgCustom` 清空（`kb-novel.js:229`），否则按钮点了"看不出效果"。
- **CSS 变量 + 字面量 `<style id="kb-nv-style">` 两份都要写**。原因（源码注释 + 探针都记了）：Chromium 上 `:root` 自定义属性变更后，**已渲染**的 `.nv-p` 不会重算 `font-size`（新插入的节点正常）。所以 `N.apply()` 除了设 8 个变量，还整段重写一个字面量 `<style>`（`kb-novel.js:98-112`），改写即全量重匹配。断言因此是"四处一致"：**变量 / 字面量样式 / 读数 / localStorage**；定点变异把字面量标签抹掉 → **9 条红**而变量那批照绿（台账轮次 30）。
- `N.set()` 之后向 `document` 广播 `CustomEvent("kb-novel-pref", {detail})`（`kb-novel.js:69`）。两个消费者：`renderTxt` 用它做 **flow 变更时整阅读器重建**（重建工具栏 → `rewireChrome()` → `renderPaged/renderScroll` 保当前章），`renderEpub` 用 `prefH` 做样式重注入。**新页面也要监听这个事件**，否则"改了偏好但当前正开着一本书"就无响应。
- **但这两个监听器都只加不减**（`kb-novel.js:679` 与 `:868`）：每次 `renderTxt` / `renderEpub` 都往 `document` 挂一个新的 `kb-novel-pref` 监听，换书时从不清理。旧闭包操作的 `wrap` 已脱离文档，多数时候只是白跑一遍（txt 侧每个旧闭包有自己的 `paged`，所以各自都会重建一次自己那份 detached DOM）；epub 侧 `prefH` 里的 `rendition.flow(wantFlow)` **没有 try/catch**，对着已 destroy 的 rendition 可能抛。重做时按"每次渲染建一个 `AbortController`，`renderXxx` 入口与切书时 `abort()`"来管监听器生命周期，别照搬这里的形状。

### 4.4 双轨字体（中英文分别定）

机制是**字体栈的逐字形回落**：把"只有拉丁字形"的字体放前面、"含中文字形"的放后面，浏览器会按字符各取所需 —— 于是"英文用 A、中文用 B"不需要任何 `unicode-range` 声明。`NV_FONT_MAP`（`kb-novel.js:23-28`）：

```js
"default": "var(--f-body)",
serif: '"Source Han Serif SC", "Noto Serif SC", Georgia, "Times New Roman", serif',
sans:  '"PingFang SC", "Microsoft YaHei", system-ui, sans-serif',
mono:  '"Cascadia Mono", Consolas, monospace',
```

而 `--f-body`（`static/style.css:27`）= `"Segoe UI","Microsoft YaHei UI","Microsoft YaHei","PingFang SC",sans-serif` —— **拉丁在前（Segoe UI 无中文字形）+ 中文在后**，这就是全站正文的双轨栈。`--f-disp`（`style.css:26`）是更明确的一例：拉丁展示体列前、末位 `var(--f-body)` 兜中文。

三条**只有读代码才知道**的细节：

1. **同一个 `"default"` 在两个引擎里解析成不同的东西**：txt 侧走 `NV_FONT_MAP["default"] = var(--f-body)`（无衬线 UI 栈），**epub 侧**（`kb-novel.js:827`）写的是 `'Georgia, "Noto Serif SC", serif'`（**衬线、拉丁优先**）。原因是 iframe 里没有宿主页面的 `--f-body` 令牌，只能自带一份。重做时要么统一要么在文档里写明。
2. **字体值是注入面**。`safeFamily(v)` 剥掉 `["'\;{}<>()&]` 并截 80 字符（`kb-novel.js:34-37`）；`norm()` 的判据是 `out.font = NV_FONT_MAP[out.font] ? out.font : (safeFamily(out.font) || "default")` —— 即"命中别名表用别名，否则当系统字体名消毒"。因为括号被剥，`font` 里塞不进 `var(...)` 或 `expression(...)`；注入串 `a"b;c<div>` 消毒后是 `abcdiv`。**断言只检查 `font-family:` 那一段**（整段禁括号是错的，合法的 `var(--f-body)` 也带括号）。
3. **系统字体枚举**走 `window.queryLocalFonts()`（Chrome/Edge 专有），失败与"不支持"都必须出 toast，不许静默；结果去重后按 `localeCompare(…"zh-Hans-CN")` 排序，塞进一个 `<optgroup label="系统字体 · N 个家族">`，且**重新枚举前先移除旧 optgroup**，最后把 `select.value` 回读到当前偏好（`kb-novel.js:199-224`）。无头 Chrome 有该 API 但必然 `SecurityError`，所以测试只断"点了必有反馈（枚举出分组 **或** 给出失败/不支持提示）"。

### 4.5 偏好守门的入口必须是 localStorage

一条被定点变异揭穿的教训（台账 §6 第 39 行）：从滑杆入口喂 `size=999`，浏览器 `<input type=range max=26>` 会**先把越界值挡掉**，`norm()` 的钳制循环根本没执行；把钳制整段短路，断言照样绿。因此**钳制类逻辑必须从它真正的入口喂**（这里是 localStorage —— 偏好是"上次存的"不是"这次点的"）。`probe_novel_prefs` 用 `KB_GEOM_INIT` 在页面任何脚本前灌 `{"size":999,"line":0.2,"track":-5,"gap":99,"indent":7,"widthRem":999,"font":"a\"b;c<div>","theme":"nonsense","bgCustom":"red","flow":"sideways","rate":99,"width":"full"}`，断言 `999→26px / 0.2→1.5 / -5→0 / 99→24 / 999rem→none（撑满）`，并断"抽屉里控件初值也是钳制后的值"。

---

## 5. 不支持的格式：为什么直接给提示卡

| 格式 | 行为 | 位置 | 理由 |
|---|---|---|---|
| `.mobi` | **不给在线渲染**，只出一张提示卡：「MOBI 暂不支持在线阅读（Palm 私有格式）」+ 建议用 Calibre 转 EPUB 放回书库 + 一个下载钮 | `app.js:259-264`（`.lib-mobi-card`） | ① MOBI 是 Palm 私有格式、无可靠纯前端解析器（不引第三方大库是本项目硬约束）；② 转成 EPUB 后**整套能力（目录/护眼主题/朗读/续读）全部白得**，成本只在一次性转换。`LIBRARY_EXTS` 仍含 `.mobi` —— 意思是"能进树、能取字节、能下载"，只是没有渲染器。 |
| `.pdf` | iframe 直通 `/raw`，用浏览器内建查看器；上方一条 `libBar`（下载 / 新标签页） | `app.js:254-257` | 不做任何自研（浏览器已内置，重复实现无收益）。**注意它仍会进 `/api/track` 阅读统计**（打开就记一条 `open`），但没有翻页级进度。 |
| `.xlsx` | SheetJS 渲染每表**前 200 行**，标题写「共 N 行（预览前 200 行）」 | `app.js:290-309` | 截断是为了 DOM 规模；加载失败退回提示文案"表格渲染失败…（可下载后本地打开）"。CDN 回退链见 §6。 |
| `.azw3 / .fb2 / .djv / .cbz / .cbr` | **完全不认识**：不在 `LIBRARY_EXTS` 也不在 `MEDIA_EXTS` → 既不进分类树，`/raw` 也拒（`safe_rel` 的扩展名白名单 400） | `store.py:34`、`app.py:172-178` | 这是**"隐形"而不是"报错"**，用户视角是"文件放在那里但树里看不到"，容易困惑。新项目若支持 CBZ（漫画），必须同时改：扩展名集合、`/raw` 白名单、`isLib` 的三处正则、`find_doc` 候选、（若可删）`api_delete` 的写白名单。 |

`syncLibraryChrome` / `clearLibraryChrome`（`app.js:236-243`）名义上是"书库顶栏 chrome"，实际前者只调 `updateStatusBarPath()`、后者要找的 `#kb-lib-fmt` **在整个仓库里从未被创建** —— 死代码。**别照搬**（格式/体积信息现在统一在底部状态栏 `#sb-path`，`app.js:1124`）。

---

## 6. 重构清单（在另一个项目里重做这套）

### A. 必须**逐字照搬**的判据（改动 = 回归风险）

| # | 判据 | 为什么不能改 | 对应断言 |
|---|---|---|---|
| A1 | `CHAP_RE` 全文 + `ln.trim().length <= 42` **两道闸并存** | 词表就是"中文网络小说标题"的现实分布 | `buildChapters 不丢任何非空白字符（含无章节/超长标题/纯空白/120 章）`、`超长标题不被当成章节标记` |
| A2 | 两处 `if (cur.lines.length \|\| cur.title) chaps.push(cur)` | `&&` 会吞掉"末章只有标题"和"首标题前引子" | `带标题章数逐样本对得上`（`EXPECT_TITLED`：`trailing-title=2`、`preamble=2`、`one-chapter=1`、`crlf=2`）、`preamble 样本切出 3 章（引子独立成章 + 2 个带标题章）且引子行不丢` |
| A3 | 兜底阈值是**带标题章数 `< 2`** | 单点误判会毁整本书的分章 | `txt 样本的章节数都 ≥1（永不出空书）`、`纯空白文本仍返回 1 章` |
| A4 | 编码降级链 `BOM → utf-8(fatal) → gb18030 → big5`，且**永不抛** | "判据是能不能严格解成 UTF-8"，不是猜字节 | `decodeTxt 对 8 种字节样本均不抛异常`、`非法 UTF-8 自动降级到 GB18030（第三章能读出来）`、`20 万字单行不崩且不挂起` |
| A5 | `fixHref` 三段判据与顺序（编码可命中→不动；解码查不到→不动；只有"编码查不到 & 解码查得到"才改并计数） | 任何放宽都会把好书也改坏 | `正常书 normalize 返回 null`、`多看版错位书…零悬空 href`、`…→ null（不认识的包一律不动手）` |
| A6 | `if (!fixes) return null`（零改动交回原始 URL）+ 重写用 `compression:"STORE"` 的 **ArrayBuffer** | blob URL 会卡死；多改一遍是纯风险 | `normalizeEpubBytes 无一挂起（8 秒超时未触发）` |
| A7 | OPF 属性顺序不固定 → NCX/nav 各**两条正则互为回退** | 单条会漏书 | 由 `FIXTURES["dk-encoding.epub"]` 与 `dangling===0` 间接咬住 |
| A8 | 主题走 **iframe 插 `<style>`**，且首帧 / `setTimeout(…,350)` / 每次 `relocated` 各注入一次 | `themes.default()` 对已渲染文档无效；350ms 是给未挂载的 iframe 补刀 | `小说偏好 size/line/track/gap/width：滑杆 → CSS 变量 → 字面量样式 → 读数 → localStorage 四处一致`（txt 侧同类；epub 侧目前**只有手工截图验证**，见 D 项缺口） |
| A9 | `flow` 变更守卫 `if (wantFlow !== lastFlow) rendition.flow(wantFlow)` | `flow()` 触发 `relocated` → 重置续读位置 | 台账 §2 登记为**未确证**（本项目没有断言咬住它，重做时**补上**：改字号后位置必须不动） |
| A10 | `kb-novel-pref` 的 `norm()` 顺序：legacy 迁移 → 覆盖 → 数值钳制 → 逐项回退；`safeFamily` 的黑名单字符集与 80 字截断 | 顺序错会钳错；字体名是注入面 | `小说偏好守门：越界数字全部被 norm() 夹回区间`、`非法主题/底色回退到默认`、`脏字体名里的注入字符被 safeFamily 剥光`、`抽屉里的控件初值也是钳制后的值` |
| A11 | `widthRem >= 100 → "none"`（"撑满"是语义不是 100rem） | 写 `100rem` 会在窄屏溢出 | `小说偏好 宽度：拉到 100 是「撑满」语义` |
| A12 | `savePos/loadPos` 两层 `try/catch` 是**唯一防线**（循环引用 / 坏 JSON / 超长 rel / 标量） | 摘掉的表现是"读过的书再点就白屏"，且只在脏数据下复现 | `savePos/loadPos 对 9 种输入均不抛`、`9 条 pos 探针结果全为 true`（9 个探针名见 §2.4） |
| A13 | 懒渲染三件套：首屏 `startCh..startCh+8` 实体 + 其余 `placeholder(estHeight)` + `lazyIO rootMargin:"1200px 0px"`；当前章用 `spyIO rootMargin:"0px 0px -85% 0px"` | 15MB 全本可用的前提；换 rootMargin 会改变"当前章"跳变时机 | 间接：两张 novel 镜头（`novel_txt` 的画面由章节渲染决定）+ `自动滚动：开起来 1.4 秒内真的在往下走` |
| A14 | 章评只写旁挂 `<rel>.notes.md`，正文**一字节不动**；前缀格式 `〔章评·<章名>〕 ` | 不变量 1（语料是事实源，运行时数据不得入正文） | `章评：磁盘上真的出现旁挂 .notes.md，且带着章节标记`、`章评：正文那本 txt 一个字节都没被改`、`章评：弹窗正文说清落到哪个旁挂文件` |
| A15 | 书库文件不进 FTS/RAG、不可经 `/api/delete` 单删；搜索侧用 `taxonomy` 的 `search:false` 关掉筛选钮 | 恒 0 结果的钮比没有钮更糟 | `test_e2e_smoke.py` 的 chip 键集断言（`"search": false` 的域不给钮）、`POST /api/delete {"path":"小说/tiny.txt"}` → 4xx |

### B. 可以重写 / 应该顺手改掉的部分

1. `syncLibraryChrome` / `clearLibraryChrome`（找不存在的 `#kb-lib-fmt`）与 `.nv-stage.nv-night`（无人加的类）、`renderTxt` 的 `sizeMiB` 形参、`snip` 字段（算了但两处都不显示）、`rendition.themes.fontSize(scale+"%")`（scale 恒 100）—— 都是历史痕迹，**新项目直接删**。
2. 三处 `isLib` 正则（后端 `LIBRARY_EXTS`、前端两条 JS 正则、模板 Jinja `endswith`）应收敛成**一份由后端下发的能力表**（`/api/doc` 里加 `kind: "txt|epub|pdf|xlsx|unsupported"`），前端按 kind 分流。本项目的分散写法是 §37 那条"同一事物三种表示"病的同族。
3. 书库的"美化版 twin"两个口径（`name+".html"` vs `stem+".html"`）二选一写死。
4. epub 侧对同一 URL 的多次 fetch（normalize + ensureTexts）合并成一次。
5. 搜索的"回车只前进不重查"（`if (hits.length && hitIdx>=0) nextHit(); else doFind()`）—— 改关键词后按回车仍会在**旧结果**里循环；应改成"输入变化即失效 hits"。
6. 章评取当前章名的匹配（`flat.filter(f => f.href === curHref)[0]`）应复用 relocated 里那套"等值或前缀"匹配，否则某些书章评不带章名。
7. 目录层级（卷/章两层）在 txt 侧可用 `第X卷` 与 `第X章` 的词面区分重建；epub 侧 navigation 本来就是树，展平是刻意的取舍，可保留层级渲染。
8. `locations.generate(1024)` 应 await 或订阅完成事件后再显示百分比。
9. 跨 iframe 注入依赖同源（`/raw`）。若新项目用不同源的静态托管，改成 epub.js 的 `rendition.getContents()` + 显式注入，或直接把样式打进 `themes` 的自定义 theme 文件。

### C. 必须一起带走的依赖与前置

- **vendored**：`jszip.min.js`、`epub.min.js`、`xlsx.full.min.js`（本仓库不联网，`renderXlsx` 的 CDN 回退是**唯一例外**：本地失败才回 `cdn.jsdelivr.net`，`app.js:285`）。
- **加载顺序**：`base.html` 实际是 `kb-core.js → … → kb-novel.js → app.js`（`app/templates/base.html:17-22`），而 `kb-novel.js` 的头注释写的是"kb-core → app.js → 本文件"。**两者矛盾但不致命**：`kb-novel.js` 只在**模块末尾同步**用 `KB.util`（必须在 kb-core 之后），对 `app.js` 的全局（`icon` / `DOC` / `rawUrl` / `buildToc` / `kbModal`）全部是**运行时才取**，所以顺序不敏感。重做时请显式定顺序，别把"运行时才取"当契约。
- `KBNOVEL.panelHTML()` 由设置抽屉在打开时调用（`kb-core.js:384-386`、页签按钮 791）—— 书库偏好面板**不在模板里**，是 JS 注入的；没有 `KBNOVEL` 时那一格渲染成空（有 `window.KBNOVEL ?` 守卫）。
- 测试侧的前置：浏览器（真 Chrome，非 jsdom）、node、CDP 探针脚本（`scripts/agent/{evalcdp,geom,shot,quiesce}.mjs`），以及 `tests/_tmpapp.py` 的"临时 KB_ROOT + 现挑端口 + 断言不占 5001/5000/5031 + 起实例必把 `static/` 拷进临时根"。

### D. 测试移植清单（这套网本身是资产）

| 层 | 位置 | 带什么 |
|---|---|---|
| 解析器性质测试 | `tests/test_js_props.py`（47 条断言，缺 node/Chrome 自动 SKIP） | ① `FIXTURES`（10 个现造 zip：`good / dk-encoding / missing-target / no-container / wrong-opf-path / empty-zip / truncated / zero-byte / garbage / nul-name`）；② `TXT_FIXTURES`（8 个字节样本）；③ `CHAPTER_TEXTS` + `EXPECT_TITLED`（10 个切分样本 + 逐样本带标题章数）；④ 9 个 `pos` 探针；⑤ 文档头部那张**变异验证表**（9 处定点改坏，8 杀 1 等价）—— 它是"断言不是摆设"的证据，比断言本身更难重写 |
| UI 行为回归 | `tests/test_ui_behavior.py` 探针 20 `probe_novel_prefs`（13 个 check 站点，含两处逐键展开循环 → 实际数十条）、探针 22 `probe_novel_bar`（13 个 check 站点） | 偏好：三组标题逐字 / 8 个默认变量 / "四处一致"×5 项 / 撑满语义 / 缩进两态 / 字体栈 / 速率落盘 / 主题成对翻色 / 自定义底色 inkFor / 系统字体必有反馈 / 恢复默认回八项 / 刷新后生效（`init` 预灌 localStorage）/ 4 条 `norm()` 守门。工具栏：四个钮存在 / 章评到磁盘且带章节标记 / 正文不被写脏 / 朗读"引擎闲下来按钮不许亮"这条不变量 / 自动滚动真实位移与再点停住 / 下载 `<a href=/raw/… download=…>` |
| 视觉回归 | `tests/test_ui_regress.py` 镜头 `novel_txt`、`novel_txt_prefs`（`SHOTS` 表 309-311）+ 阈值 **AE ≤ 2 像素**（`floor.json` 实测噪声地板 0~1） | 合成语料 `NOVEL_TXT`（`content/nv-r/books/长夜.txt`，三章，`test_ui_regress.py:152-163`）、`TAXONOMY` 里 `"nv-r": {"search": False}`（让"派生 + 过滤"这条链在基线里真被走过） |
| 端到端 | `tests/test_e2e_smoke.py`：`小说/tiny.{txt,epub,pdf,xlsx,mobi}` 五个 `/raw` 直服 200、非法后缀 400、目录穿越 400、`POST /api/delete {"path":"小说/tiny.txt"}` 4xx；`tests/test_invariants.py` I2（`_` 前缀不进索引）、I5（模板不抄域名单） | 合成样本即可，**绝不拿真实书库跑**（见 E） |

已知**测试覆盖缺口**（本项目遗留，重做时应补）：① `normalizeEpubBytes` 只测到字节层，"重写后的 ArrayBuffer 真能被 epub.js 渲染出章节"仍靠手工；② `epub.min.js` 自身渲染不在覆盖面；③ A9 的"flow 变更不重置进度"没有断言；④ epub 主题注入（iframe `<style>`）只有截图级验证，没有 DOM 断言；⑤ pdf/xlsx/mobi 在真语料里 0 样本，只验过"直服 + 无 console error + chrome 隐藏"。

### E. 边界（不可协商）

**不读真实书库正文，也不写任何以真实书库为输入的脚本**，"只读不写""本地不外传"都不构成放宽理由（用户 2026-09-24 定的边界，AGENTS 禁区末条；台账 §14.2 把 P7「语料驱动伪 fuzz」标为"⛔ 用户否决，永久不做"，§8 同一条）。所有测试样本一律现造在 `tempfile` 里；搬家前先查 `content/` 下的 junction/符号链接（`mv`/`rmtree` 会穿透删到别处），git 历史里的旧文件永远 `git show <旧提交>:content/…` 取得回来，所以边界不因文件已移出而作废。

---

## 7. 踩过的坑（症状 → 根因 → 修法）

> 来源：`测试文件/覆盖台账.md` §6（第 25/30/33/37/39/40/41 行等）、§12（P3-B 专章）、`docs/handoff-2026092503.md`。只收真正属于**书库线**的。

1. **epub 整本空白 / 点目录报 No Section Found**
   症状：某些 epub（尤其多看版）打开后正文区一片白；目录点了报 "No Section Found"。
   根因：OPF/NCX 里 href 被百分号编码（`* | :` 这些字符），zip 条目却是原始名，vendored epub.js 用编码 href 直查 JSZip 命中不了；且 nav 与 spine 的编码形式互不一致。
   修法：`normalizeEpubBytes` 就地解码那些"编码查不到、解码查得到"的 href，使 spine/nav/zip 三者一致；只有真改过才重新打包回 ArrayBuffer（`§3.1`）。

2. **blob URL 让 epub.js 卡死**
   症状：修完 href 后改用 `URL.createObjectURL(blob)` 传入，页面既不报错也不渲染，永远停在那里。
   根因：epub.js 期望 ArrayBuffer 或可发 range 请求的真实 URL；blob URL 走到某条不返回的路径。
   修法：`generateAsync({type:"arraybuffer", compression:"STORE"})` 直传。测试侧把"挂起"当失败信号（`Promise.race` + 8 秒超时）。

3. **改了字号/底色，已渲染的章节纹丝不动**
   症状：`rendition.themes.default(...)` 调了没效果，当前页样式一点不变。
   根因：epub.js 的 theme API 不作用到已渲染的 section 文档（iframe 内文档）。
   修法：绕开 theme，直接往每个 iframe 的 head 插 `<style id="kb-nv-epub">`，全部声明 `!important`；注入时机三处（首帧 / +350ms / 每次 relocated）。

4. **每次调字号，阅读进度就回章首**
   症状：偏好一改，CFI 被重置。
   根因：`rendition.flow()` 触发 `relocated`，`relocated` 里会 `savePos`，于是"样式偏好"顺带写了个"新位置"。
   修法：`prefH` 里加 `wantFlow !== lastFlow` 守卫 —— **只有 flow 真变才调 flow()**。（这条至今没有断言，重做时补。）

5. **封面大片空白，看起来像"正文没了"**
   根因：多看版封面/插图的文件名编码错乱 → 图加载失败但不留痕。
   修法：`injectTheme` 里 `complete && naturalWidth===0` 或 `error` 时 `display:none`（用 `dataset.nvErr` 防重复挂监听）。这是掩盖，真正的修正仍是坑 1 的 href 解码。

6. **txt 乱码（GBK 存的书全是问号）**
   症状：UTF-8 之外的中文 txt 打开是 mojibake。
   根因：只用非 fatal 的 `TextDecoder("utf-8")` —— 它对非法序列静默替换成 U+FFFD，永远不会"失败"，也就没有降级机会。
   修法：`fatal:true` 试 UTF-8，抛异常才降 `gb18030`（不是 `gbk`，超集更宽容）。断言 `非法 UTF-8 自动降级到 GB18030（第三章能读出来）`。

7. **朗读报错后按钮永远亮着，再点一次变成"重新开始"**（台账 §6 第 40 行）
   症状：`speechSynthesis` 出错（无设备/语音包缺/被打断）后 `.nv-tts` 保持 `.on`；用户以为在读，点一下却不是停止而是重头再念。
   根因：`.on` 由三处负责（点击处理加、`onDone` 撤、`tts.stop()` 分支撤），但 `stop()` **只清 `busy` 不清 `.on`** —— onerror 恰好只走 `stop()`。一个视觉状态三个主人、只覆盖两条出口。
   修法：把视觉态收口到 `stop()` 一处（`busy` 与 `on` 同撤），`start()` 改为在 `stop()` **之后**自己 `add("on","busy")`（旧代码靠调用方先加类、再用 `.nv-tts.on` 找按钮，收口一改就踩空 —— 这处联动最容易漏）。
   测试写法教训：无头 Chrome 里 `speak()` **必然** `onerror`，所以断言不能写"点一下必须亮"，要写成不变量"**引擎闲下来时按钮不许亮**"（修复前必红、修复后必绿，两个环境都成立）。

8. **"越界会被钳制"是一条空断言**（台账 §6 第 39 行）
   症状：断言绿。定点变异把 `norm()` 的钳制循环整个短路，**照样绿**。
   根因：`<input type=range max=26>` 在赋值那一刻就把 999 挡成 26，代码根本走不到 `norm()`。**从 UI 控件入口测守门函数，很可能走不到它。**
   修法：clamp 那条改口径（只承认"滑杆到不了越界值"），另加从 **localStorage** 侧喂脏值的三条断言。推广结论：守门逻辑要从它真正的入口喂（偏好是"上次存的"，不是"这次点的"）。

9. **自动滚动那颗钮"点了没反应"**（台账轮次 31 ①）
   症状：截图和断言都显示没动。
   根因：`autoTick` 的停止判据是 `scrollTop + clientHeight >= scrollHeight - 2`，而视觉基线那本三章假小说在滚动模式下**只渲染第一章、`.nv-stage` 根本不溢出** → 第一帧 rAF 就 `autoStop`。
   修法：为这颗钮单独造一本够长的合成书（3 章 × 40 段，`test_ui_behavior.py:90-97` 的 `_long_book_text`）。推广结论：**测试靶子的"尺寸"经常就是判据的一部分**，别拿短样本测滚动类行为。

10. **Chromium 上改 CSS 变量不重算已渲染节点**（`kb-novel.js:98-99`）
    症状：`:root` 的 `--nv-size` 变了，新插入段落是新的，**已经在页面上的段落字号不动**。
    根因：Chromium 对自定义属性变更不做已渲染节点的 `font-size` 失效重算。
    修法：关键声明额外走一个字面量 `<style id="kb-nv-style">`（改写即全量重匹配）。断言因此是"四处一致"，抹掉字面量标签 → 9 条红而变量全绿。

11. **左树不高亮当前文档**（台账 §6 第 37 行，命名口径）
    症状：直开/刷新 `/doc/小说/xxx/长夜.txt` 这类页面，左树没有"你在这儿"；SPA 点着走却是对的。
    根因：比较跨了两种表示 —— `CUR.name`（来自 URL，**带后缀**）vs 树节点的 `doc.name`（`.md` 系是**不带后缀**的键）。书库文件把后缀问题永久暴露出来。
    修法：**拿同一层的量比** —— 链接比链接（两侧都过 `docUrl` 规范化），于是 md / txt / html 三种命名一起覆盖。
    重做提示：书库的 `name` 带后缀、`.md` 不带，任何按 name 的相等判断都是雷区。

12. **"只断不抛"是假网**（台账 §12.4 第 1 条）
    症状：第一版 `test_js_props` 里 `KBNOVEL` 因为临时根**没拷 `static/`** 而根本没加载，10 个 epub 全 error，看起来"跑完了"。
    根因：临时 KB_ROOT 缺 `static/` → `create_app` 的 static_folder 找不到 → `kb-novel.js`/vendor 全 404 → 测的是空气。
    修法：起实例必须 `shutil.copytree(ROOT/"static", tmp/"static")`；断言改成"每个样本都必须有结论"（`set(epub) == set(FIXTURES)`），error 也要显式记为 error。
    同族第二条：字符总数守恒**也会被兜底骗过**（标题不足 2 个时整篇兜底把碎片捞回来）→ 必须钉"每样本带标题章数"。

13. **探针连上了陌生浏览器 / 截图截早了**（台账 §6 第 41 行 + AGENTS 的 `clickWait` 说明）
    症状：js_props 报 `KeyError: 'roundtrip'`，`geom/shot` 读到陈旧状态。
    根因：固定调试端口 + Windows 下 `proc.kill()` 只杀父进程 → 上一轮泄漏的 headless Chrome 占着端口，`/json/new` 打进**别人那台**浏览器（还是后台标签页，rAF/IO 被节流）。
    修法：`pickPort()` 先探空、被占就 `listen(0)` 另要一个（并往 stderr 报"已改用 N —— 绝不连陌生浏览器"）；`killChrome()` 用 `taskkill /T /F` 杀进程树；`rmProfile()` 重试删。
    配套：每次点击后不能用"固定睡眠"当静默，`quiesce.mjs`（字体就绪 + 在途 fetch 归零 + DOM 连续 320ms 无变化）提前收敛，声明值只当上限。

14. **`.notes.md` 的可见性口径漏一处**（台账 §6 第 33 行）
    症状：收件箱徽标把备注当条目；点"归档"会把一条无处渲染的备注塞进正式语料目录。
    根因：扫描侧有 `.notes.md` 排除规则、收件箱侧没有。
    修法：`inbox_iter` 补同一条豁免。**推广到书库**：章评写的正是 `<书>.notes.md`，四条排除路径（`is_visible_doc` / `_visible_sub_files` / `_tree_sig` / `find_doc`）少一条就会凭空多出一篇可路由的幽灵"文档"（`_tree_sig` 少了它则是每次记备注都白白失效一轮缓存）。

---

## 附：本项目没做（别误以为该重做）

- 书签、句内高亮、划线笔记的持久化（只有章评，按章加前缀追加到旁挂）。
- 多分卷合并、书级元数据（作者/出版社/封面墙）、批量导入去重。
- 图片型漫画阅读器（CBZ/CBR 逐页翻）—— 完全没有。
- 书库全文索引（FTS/RAG 一律不收），书内搜索是纯前端线性遍历，上限 100 条。
- epub 的 CSS 列真分页 + 页码持久化（只有 CFI）。
- 阅读时长只按"打开文档"记（`/api/track` 的 `open`/`read_minute`/`finish`），**不区分章内实际停留**。
- 任何出站请求（不变量 9 已撤销 AI 链路，书库更是只进不出）。
