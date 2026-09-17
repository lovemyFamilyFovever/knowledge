/* 知库 reader 前端：主题、面板折叠、客户端路由、正文渲染、编辑/备注/收藏/删除、双链、快捷键 */
window.APP_JS_VERSION = 33;

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
/* 问题3 修复：toast 唯一实现收拢到 kb-core 的 KB.util.toast（kb-core defer 顺序在前，可依赖）。
   原先 app.js 与 kb-core.js 各持一个隐藏 timer（_h / _kbh）共用 #toast，两条 toast 先后出现时
   第二条会被第一条的旧 timer 提前隐藏。此处只转调，不再自管 timer。 */
const toast = (m, ms) => {
  if (window.KB && KB.util && KB.util.toast) { KB.util.toast(m, ms); return; }
  const t = $("#toast"); if (!t) return;
  t.innerHTML = m; t.classList.add("show");
  clearTimeout(t._kbh); t._kbh = setTimeout(() => t.classList.remove("show"), ms || 2600);
};
/* 问题8（阶段1）：/doc 与 /raw 的 URL 构造唯一实现在 kb-core.util（_root 补段 + 逐段 encode），
   app.js 只转调。此前 docUrl 在 app.js 与 kb-core 双实现、navigate 里还有第三处局部影子。 */
const docUrl = rel => KB.util.docUrl(rel);
const rawUrl = rel => KB.util.rawUrl(rel);

/* 统一图标：引用 base.html 精灵表 #i-<name>，替代所有彩色 emoji */
const icon = (n, s = 14) => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:none;display:inline-block;vertical-align:-.15em"><use href="#i-${n}"/></svg>`;

/* ---------- 主题 ---------- */
function applyTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  const b = $("#theme-btn"); if (b) b.innerHTML = icon(t === "dark" ? "moon" : "sun", 15);
  window.dispatchEvent(new CustomEvent("theme-changed", { detail: t }));
  try { localStorage.setItem("kb-theme", t); } catch (e) {}
}
/* 任务8：5 版皮肤切换（墨韵/午夜蓝/森绿/暮色玫瑰/石墨 + 默认青瓷） */
const SKINS = [
  { id: "celadon", name: "青瓷", desc: "默认 · 现状", a: "#0c9a6a", b: "#0f86b8" },
  { id: "ink", name: "墨韵", desc: "宣纸 × 朱砂", a: "#8c3a2e", b: "#3d5a80" },
  { id: "midnight", name: "午夜蓝", desc: "工程仪表感", a: "#2563eb", b: "#0891b2" },
  { id: "forest", name: "森绿", desc: "苔绿 × 菌菇棕", a: "#4a7c59", b: "#b0713a" },
  { id: "rose", name: "暮色玫瑰", desc: "玫瑰金 × 紫藤", a: "#a34a5e", b: "#7069a8" },
  { id: "graphite", name: "石墨", desc: "中性 × 橙点缀", a: "#1c1c1a", b: "#c2410c" },
];
function applySkin(id) {
  const skin = SKINS.find(s => s.id === id) || SKINS[0];
  if (skin.id === "celadon") document.documentElement.removeAttribute("data-skin");
  else document.documentElement.setAttribute("data-skin", skin.id);
  try { localStorage.setItem("kb-skin", skin.id); } catch (e) {}
  window.dispatchEvent(new CustomEvent("skin-changed", { detail: skin.id }));
}
function showSkinPicker() {
  const old = document.querySelector(".kb-skin-pop");
  if (old) { old.remove(); return; }
  const cur = (localStorage.getItem("kb-skin") || "celadon");
  const pop = document.createElement("div");
  pop.className = "kb-skin-pop";
  pop.innerHTML = `<div class="kb-skin-pop-h">界面风格 · 深浅色按钮继续可用</div>
    <div class="kb-skin-grid">${SKINS.map(s => `
      <button type="button" class="kb-skin-card ${s.id === cur ? "on" : ""}" data-skin="${s.id}">
        <span class="kb-skin-dot" style="--sd-a:${s.a};--sd-b:${s.b}"></span>
        <span><b>${s.name}</b><i>${s.desc}</i></span>
      </button>`).join("")}</div>`;
  const tr = $("#theme-btn").closest(".top-right");
  (tr || document.body).style.position = "relative";
  (tr || document.body).appendChild(pop);
  pop.addEventListener("click", e => {
    const card = e.target.closest(".kb-skin-card");
    if (card) { applySkin(card.dataset.skin); pop.remove(); }
  });
  setTimeout(() => document.addEventListener("mousedown", function h(ev) {
    if (!pop.contains(ev.target) && ev.target !== $("#theme-btn")) { pop.remove(); document.removeEventListener("mousedown", h); }
  }), 0);
}
window.applySkin = applySkin;
window.showSkinPicker = showSkinPicker;
const themeBtn = $("#theme-btn");
if (themeBtn) {
  themeBtn.onclick = () => {
    const now = document.documentElement.getAttribute("data-theme");
    applyTheme(now === "dark" ? "light" : "dark");
    if (window.DOC && document.querySelector("#article .mermaid")) renderArticle();
  };
  themeBtn.oncontextmenu = e => { e.preventDefault(); showSkinPicker(); }; // 右键弹皮肤选择
  themeBtn.title = "切换白天 / 夜间（右键换 5 版界面风格）";
}
try { const saved = localStorage.getItem("kb-theme"); if (saved) applyTheme(saved); } catch (e) {}
try { const savedSkin = localStorage.getItem("kb-skin"); if (savedSkin) applySkin(savedSkin); } catch (e) {}

/* ---------- 面板折叠（workbench） ---------- */
function setPanel(which, off) {
  const pid = which === "left" ? "p-left" : which === "rail" ? "p-rail" : "p-list";
  const cls = which === "left" ? "left-off" : which === "rail" ? "rail-off" : "list-off";
  const p = document.getElementById(pid), m = document.querySelector("main");
  if (!p || !m) return;
  p.classList.toggle("collapsed", off);
  m.classList.toggle(cls, off);
}
function togglePanel(which) {
  const pid = which === "left" ? "p-left" : "p-list";
  const off = !document.getElementById(pid).classList.contains("collapsed");
  setPanel(which, off);
  try { const s = JSON.parse(localStorage.getItem("kb-panels") || "{}"); s[which] = off;
    localStorage.setItem("kb-panels", JSON.stringify(s)); } catch (e) {}
}
try { const s = JSON.parse(localStorage.getItem("kb-panels") || "{}");
  if (s.left) setPanel("left", true); if (s.list) setPanel("list", true); } catch (e) {}

/* ---------- mermaid 懒加载 ---------- */
let mermaidLoading = null;
function ensureMermaid() {
  if (window.mermaid) return Promise.resolve();
  if (!mermaidLoading) mermaidLoading = loadScript("/static/mermaid.min.js");
  return mermaidLoading;
}
function loadScript(src) {
  return new Promise((res, rej) => {
    const s = document.createElement("script");
    s.src = src; s.onload = res; s.onerror = () => rej(new Error("load failed: " + src));
    document.head.appendChild(s);
  });
}

/* ---------- 分类树：localStorage 缓存 + 后台刷新 ---------- */
let TREE = null;
const LS_TREE = "kb-tree";

function findSub(domain, sub) {
  const d = (TREE || []).find(x => x.id === domain);
  return d ? d.subs.find(s => s.id === sub) : null;
}

async function loadTree() {
  if (TREE) return;
  try {
    const c = JSON.parse(localStorage.getItem(LS_TREE) || "null");
    if (c && Array.isArray(c.domains) && c.domains.length) { TREE = c.domains; renderTree(); }
  } catch (e) {}
  try {
    const r = await fetch("/api/tree");
    const d = await r.json();
    if (Array.isArray(d.domains) && d.domains.length) {
      TREE = d.domains;
      try { localStorage.setItem(LS_TREE, JSON.stringify(d)); } catch (e) {}
      renderTree();
    }
  } catch (e) { /* localStorage 缓存兜底 */ }
}

/* ---------- 右栏 tabs ---------- */
function tab(id, el) {
  $$(".rtab").forEach(t => { t.classList.remove("active"); t.setAttribute("aria-selected", "false"); });
  el.classList.add("active"); el.setAttribute("aria-selected", "true");
  if (!el.id) el.id = "rtab-" + id;
  $$(".rpane").forEach(p => p.classList.remove("active"));
  const pane = $("#pane-" + id); pane.classList.add("active");
  pane.setAttribute("aria-labelledby", el.id);
  if (id === "links") loadLinks();
}

/* ---------- 正文渲染 ---------- */
let DOC = null;
let CUR = null; // {domain, sub, name}

/* ---------- 渲染预处理（需求 #8/#9/#6） ----------
   #8：marked 对「列表内缩进开栏、顶格闭栏」的围栏会在文末产幽灵空代码块
   （删不掉的小尾巴）；把闭栏缩进对齐到开栏即可正常闭合。栈匹配：
   闭栏 = 同字符、长度≥开栏、缩进≤开栏。 */
function sanitizeFences(md) {
  const lines = String(md || "").split("\n");
  const open = [];
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(/^([ \t]*)(`{3,}|~{3,})/);
    if (!m) continue;
    const top = open[open.length - 1];
    if (!top) {
      open.push({ indentLen: m[1].length, ch: m[2][0], len: m[2].length });
    } else if (m[2][0] === top.ch && m[2].length >= top.len && m[1].length <= top.indentLen) {
      lines[i] = " ".repeat(top.indentLen) + m[2];
      open.pop();
    }
  }
  return lines.join("\n");
}
/* 渲染入口：源码围栏修复 + 解析后剥末尾幽灵空代码块（pre>code 仅空白） */
function renderMarkdownSafe(md) {
  const html = marked.parse(sanitizeFences(md));
  return html.replace(/(?:<pre><code[^>]*>[\s\u00a0]*<\/code><\/pre>\s*)+$/, "");
}

/* #9：正文外链一律新标签打开；#6：站内相对图片走 /raw 直服（语料 md 旁的
   imgs/、images/ 等任意扩展名资产，404 时占位提示）。渲染后同帧处理。 */
function enhanceRenderedBody(el) {
  el.querySelectorAll(".a-body a[href]").forEach(a => {
    const h = a.getAttribute("href") || "";
    if (/^(https?:)?\/\//i.test(h) || /^mailto:/i.test(h)) {
      a.target = "_blank";
      if (!a.rel) a.rel = "noopener";
    }
  });
  el.querySelectorAll(".a-body img").forEach(img => {
    const src = img.getAttribute("src") || "";
    if (!src || /^(https?:)?\/\/|^(data|blob):/i.test(src) || src.startsWith("/raw/")) {
      if (!img.dataset.kbErrBound) {
        img.dataset.kbErrBound = "1";
        img.addEventListener("error", () => {
          img.alt = (img.alt || "图片") + "（缺失：仅 Markdown 源入库，图片未随迁）";
          img.classList.add("kb-img-missing");
        }, { once: true });
      }
      return;
    }
    const docDir = DOC && DOC.rel ? DOC.rel.split("/").slice(0, -1).join("/") : "";
    const abs = src.startsWith("/") ? src.slice(1)
      : (docDir ? docDir + "/" : "") + src.replace(/^\.\//, "");
    const parts = [];
    abs.split("/").forEach(seg => {
      if (seg === "..") parts.pop(); else if (seg && seg !== ".") parts.push(seg);
    });
    img.src = "/raw/" + parts.map(encodeURIComponent).join("/");
    if (!img.dataset.kbErrBound) {
      img.dataset.kbErrBound = "1";
      img.addEventListener("error", () => {
        img.alt = (img.alt || "图片") + "（缺失：仅 Markdown 源入库，图片未随迁）";
        img.classList.add("kb-img-missing");
      }, { once: true });
    }
  });
}

/* 新建文档弹窗（空目录占位页复用；与 ctxSubItems 内联版同行为） */
async function promptNewDocInDir(dom, sub) {
  const base = sub ? `${dom}/${sub}` : dom;
  const res = await kbModal({
    title: "新建文档",
    body: `将在 <span class='mono'>${esc(base)}/</span> 下创建 Markdown 文件，首行自动写入标题。`,
    inputs: [{ key: "nm", label: "文件名（不含 .md）", placeholder: "示例：RAG 切块策略" }],
    confirmText: "创建",
  });
  if (!res || !res.nm) return;
  const rel = `${base}/${res.nm}.md`;
  const r = await fetch("/api/save", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: rel, content: `# ${res.nm}\n\n` }) });
  if (!r.ok) { toast("创建失败：" + r.status); return; }
  await afterMutation();
  await navigate(docUrl(rel), true);
}
window.promptNewDocInDir = promptNewDocInDir;

/* ---------- 需求 #12：书库格式分流渲染 ----------
   .txt  → fetch 原文 + <pre> 分页阅读（大文件截断展示头部 + 下载入口）
   .pdf  → 浏览器原生 PDF 查看器（iframe 直通 /raw/）
   .xlsx → SheetJS 渲染工作表前 200 行
   .epub → 暂不支持在线渲染，给下载与打开方式 */
/* ---------- 书库文档顶栏 chrome 同步（用户要求） ----------
   顶部 crumb 已显示完整标题 → 正文不重复标题；
   格式/体积/下载统一并入「crumb 按钮组」与「readhead 状态栏」同一行，不单独起行。 */
function syncLibraryChrome(ext, sizeMiB) {
  const readhead = document.querySelector(".readhead");
  if (!readhead) return;
  /* 格式 · 体积 chip → readhead 状态栏同一行（下载按钮由 renderCrumb 统一渲染，避免被重建冲掉） */
  const chipId = "kb-lib-fmt";
  let fmt = document.getElementById(chipId);
  if (!fmt) {
    fmt = document.createElement("span");
    fmt.id = chipId;
    fmt.className = "rh-chip rh-mono";
    readhead.appendChild(fmt);
  }
  fmt.textContent = ext.toUpperCase() + " · " + sizeMiB + " MB";
}

/* 切换到非书库文档时清掉上一个文档挂上的 chrome（防串场） */
function clearLibraryChrome() {
  const fmt = document.getElementById("kb-lib-fmt");
  if (fmt && fmt.parentNode) fmt.parentNode.removeChild(fmt);
}

function renderLibraryDoc(el, ext) {
  el.classList.remove("pretty-mode");
  const rawHref = rawUrl(DOC.rel);
  const sizeMiB = (parseFloat(DOC.size) / 1024).toFixed(1); // DOC.size 是 KB 字符串
  /* 用户要求：顶部 crumb 已显示完整标题 → 正文不再重复标题；
     格式/体积/下载统一并入「顶栏 crumb 按钮组」与「readhead 状态栏」，不再单独起行。
     syncLibraryChrome() 负责把这套 chrome 挂到正确位置（幂等）。 */
  syncLibraryChrome(ext, sizeMiB);
  if (ext === "pdf") {
    el.innerHTML = `<div class="a-body"><div class="lib-frame-wrap"><iframe class="lib-frame" src="${rawHref}" title="${esc(DOC.title)}"></iframe></div></div>`;
    buildToc(); // 清空残留目录
    return;
  }
  if (ext === "epub") {
    el.innerHTML = `<div class="a-body" id="lib-epub"><div class="kb-skeleton" aria-busy="true"><i style="width:65%"></i><i style="width:88%"></i><i style="width:76%"></i></div><p style="color:var(--faint);font-size:12.5px">EPUB 解析中…</p></div>`;
    renderEpub(rawHref);
    return;
  }
  if (ext === "xlsx") {
    el.innerHTML = `<div class="a-body" id="lib-xlsx"><div class="kb-skeleton" aria-busy="true"><i style="width:60%"></i><i style="width:90%"></i></div></div>`;
    renderXlsx(rawHref);
    buildToc();
    return;
  }
  // txt：>2MB 只展示前 512KB 预览，完整阅读走下载
  el.innerHTML = `<div class="a-body lib-txt" id="lib-txt"><div class="kb-skeleton" aria-busy="true"><i style="width:70%"></i><i style="width:92%"></i><i style="width:84%"></i></div></div>`;
  fetch(rawHref).then(r => {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.text();
  }).then(t => {
    const LIMIT = 512 * 1024;
    const truncated = t.length > LIMIT;
    const body = truncated ? t.slice(0, LIMIT) : t;
    /* 章节识别：按行扫描常见章节标题（第X章/Chapter N/序章/番外等），
       命中 ≥2 个则渲染为带锚点标题的可导航文本，右栏目录随之生成 */
    const lines = body.split(/\r?\n/);
    const chapRe = /^\s*(第[0-9零一二三四五六七八九十百千两]+[章回卷节部集]|Chapter\s+\d+|CHAPTER\s+\d+|序[章言]?|楔子|引子|番外[篇·]?\S*|尾声|终章|后记)\s*[^\n]{0,40}$/;
    const segs = [];
    let cur = null;
    lines.forEach(ln => {
      if (chapRe.test(ln) && ln.trim().length <= 42) {
        if (cur) segs.push(cur);
        cur = { title: ln.trim(), lines: [] };
      } else if (cur) cur.lines.push(ln);
      else { if (!cur) cur = { title: "", lines: [] }; cur.lines.push(ln); }
    });
    if (cur) segs.push(cur);
    const hasChapters = segs.filter(s => s.title).length >= 2;
    const wrap = $("#lib-txt");
    if (!wrap) return;
    wrap.innerHTML = "";
    if (hasChapters) {
      const used = new Set();
      segs.forEach(s => {
        if (s.title) {
          const h = document.createElement("h2");
          h.className = "lib-txt-chap";
          h.textContent = s.title;
          h.id = slugifyHeading(s.title, used);
          wrap.appendChild(h);
        }
        const pre = document.createElement("pre");
        pre.className = "lib-txt-pre";
        pre.textContent = s.lines.join("\n").replace(/^\n+/, "");
        wrap.appendChild(pre);
      });
    } else {
      const pre = document.createElement("pre");
      pre.className = "lib-txt-pre";
      pre.textContent = body;
      wrap.appendChild(pre);
    }
    if (truncated) {
      const note = document.createElement("div");
      note.className = "hint";
      note.style.marginTop = "10px";
      note.textContent = `文件较大（${sizeMiB} MB），仅预览前 512KB —— 下载后阅读全文。`;
      wrap.appendChild(note);
    }
    buildToc(); // 章节标题已就位，重建右栏目录（含空态提示）
  }).catch(e => {
    const wrap = $("#lib-txt");
    if (wrap) wrap.innerHTML = `<p>读取失败：${esc(String(e.message || e))}</p>`;
    buildToc();
  });
}

let _sheetjsLoading = null;
function ensureSheetJS() {
  if (window.XLSX) return Promise.resolve();
  if (!_sheetjsLoading) _sheetjsLoading = loadScript("/static/vendor/xlsx.full.min.js")
    .catch(() => loadScript("https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"));
  return _sheetjsLoading;
}

async function renderXlsx(url) {
  try {
    await ensureSheetJS();
    const buf = await (await fetch(url)).arrayBuffer();
    const wb = window.XLSX.read(buf, { type: "array" });
    const wrap = $("#lib-xlsx");
    if (!wrap) return;
    wrap.innerHTML = wb.SheetNames.map(sn => {
      const rows = window.XLSX.utils.sheet_to_json(wb.Sheets[sn], { header: 1, defval: "" });
      const view = rows.slice(0, 200);
      const th = (view[0] || []).map(c => `<th>${esc(String(c))}</th>`).join("");
      const tr = view.slice(1).map(r => `<tr>${r.map(c => `<td>${esc(String(c))}</td>`).join("")}</tr>`).join("");
      return `<div class="lib-sheet"><div class="lib-sheet-h">${esc(sn)} · 共 ${rows.length} 行${rows.length > 200 ? "（预览前 200 行）" : ""}</div>
        <div class="tbl-wrap"><table><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table></div></div>`;
    }).join("");
  } catch (e) {
    const wrap = $("#lib-xlsx");
    if (wrap) wrap.innerHTML = `<p>表格渲染失败：${esc(String(e.message || e))}（可下载后本地打开）</p>`;
  }
}

/* ---------- EPUB 在线阅读（epub.js + jszip，vendor 离线） ---------- */
let _epubLibLoading = null;
function ensureEpubLib() {
  if (window.ePub) return Promise.resolve();
  if (!_epubLibLoading) {
    _epubLibLoading = loadScript("/static/vendor/jszip.min.js")
      .then(() => loadScript("/static/vendor/epub.min.js"));
  }
  return _epubLibLoading;
}

let _epubBook = null, _epubRendition = null;
async function renderEpub(url) {
  const wrap = $("#lib-epub");
  if (!wrap) return;
  try {
    await ensureEpubLib();
    // 销毁上一本（切换文档时防泄漏）
    if (_epubRendition) { try { _epubRendition.destroy(); } catch (e) {} _epubRendition = null; }
    if (_epubBook) { try { _epubBook.destroy(); } catch (e) {} _epubBook = null; }

    wrap.innerHTML = `
      <div class="epub-reader">
        <div class="epub-toolbar">
          <button class="iconbtn epub-prev" title="上一页">${icon("chev-left", 13)} 上一页</button>
          <span class="epub-loc" id="epub-loc">—</span>
          <button class="iconbtn epub-next" title="下一页">下一页 ${icon("chev-right", 13)}</button>
          <span class="spacer" style="flex:1"></span>
          <button class="iconbtn epub-font-dec" title="缩小字号">A-</button>
          <button class="iconbtn epub-font-inc" title="放大字号">A+</button>
        </div>
        <div class="epub-body-row">
          <nav class="epub-toc" id="epub-toc" aria-label="书籍目录"></nav>
          <div class="epub-view" id="epub-view"></div>
        </div>
      </div>`;

    const book = window.ePub(url);
    _epubBook = book;
    const rendition = book.renderTo("epub-view", {
      width: "100%", height: "100%", spread: "none", flow: "scrolled-doc"
    });
    _epubRendition = rendition;
    // 主题适配：注入浅色阅读样式到 epub iframe
    rendition.themes.default({
      body: { color: "#131c23", background: "#ffffff", "font-size": "16px", "line-height": "1.85", padding: "8px 4px" },
      p: { "margin": "0.6em 0" }
    });

    let fontSize = 100;
    const applyFont = () => rendition.themes.fontSize(fontSize + "%");

    await rendition.display();

    // 目录
    const nav = await book.loaded.navigation;
    const tocEl = $("#epub-toc");
    if (nav && nav.toc && nav.toc.length) {
      tocEl.innerHTML = nav.toc.map(item =>
        `<a class="epub-toc-item" href="#" data-href="${esc(item.href)}" title="${esc(item.label)}">${esc(item.label.trim() || "（无标题）")}</a>`
      ).join("");
      tocEl.addEventListener("click", e => {
        const a = e.target.closest(".epub-toc-item");
        if (!a) return;
        e.preventDefault();
        rendition.display(a.dataset.href);
        tocEl.querySelectorAll(".epub-toc-item").forEach(x => x.classList.toggle("on", x === a));
      });
    } else {
      tocEl.innerHTML = `<div class="epub-toc-empty">本书无目录</div>`;
    }

    // 翻页与位置
    const locEl = $("#epub-loc");
    rendition.on("relocated", loc => {
      const pct = book.locations && book.locations.length() ? "" : "";
      locEl.textContent = (loc && loc.start && loc.start.cfi) ? "·" : "—";
      // 高亮当前章
      const href = loc && loc.start && loc.start.href;
      if (href) tocEl.querySelectorAll(".epub-toc-item").forEach(x =>
        x.classList.toggle("on", x.dataset.href === href || href.startsWith(x.dataset.href)));
    });
    const prev = () => rendition.prev();
    const next = () => rendition.next();
    wrap.querySelector(".epub-prev").onclick = prev;
    wrap.querySelector(".epub-next").onclick = next;
    wrap.querySelector(".epub-font-dec").onclick = () => { fontSize = Math.max(70, fontSize - 10); applyFont(); };
    wrap.querySelector(".epub-font-inc").onclick = () => { fontSize = Math.min(180, fontSize + 10); applyFont(); };
    // 键盘 ←→ 翻页（焦点在阅读器时）
    wrap.tabIndex = 0;
    wrap.addEventListener("keydown", e => {
      if (e.key === "ArrowLeft") { e.preventDefault(); prev(); }
      else if (e.key === "ArrowRight") { e.preventDefault(); next(); }
    });
    buildToc(); // epub 自带目录在工具栏左侧，右栏 rail 显示空态
  } catch (e) {
    wrap.innerHTML = `<div class="a-body"><p>EPUB 解析失败：${esc(String(e && e.message || e))}</p>
      <p><a class="chip chip-btn" href="${url}" download="${esc(DOC.name || "book.epub")}">${icon("download", 11)} 下载后用阅读器打开</a></p></div>`;
    buildToc();
  }
}
window.renderArticle = renderArticle;

function renderArticle(forceMd) {
  const el = $("#article");
  if (!el || !DOC) return;
  refreshDocMark(); // 已读/已掌握按钮状态（异步，不阻塞渲染）
  /* 需求 #12：书库格式分流渲染 —— .txt 直接读文本、.pdf 原生 iframe、
     .xlsx 用 SheetJS 渲染前 N 行、.epub 给下载/打开方式；不进 markdown 管线 */
  const libExt = (DOC.name || "").match(/\.(txt|pdf|xlsx|epub)$/i);
  if (libExt && !forceMd) { renderLibraryDoc(el, libExt[1].toLowerCase()); return; }
  clearLibraryChrome(); // 非书库文档：清掉上一个书库文档挂的下载钮/格式 chip
  /* 空目录占位（新建目录未放文档时不再 404，正文区给引导） */
  if (DOC.empty) {
    el.classList.remove("pretty-mode");
    el.innerHTML = `<h1 class="a-title">${esc(DOC.title)}</h1>
      <div class="a-rule"></div>
      <div class="kb-empty-dir">
        <p>这个目录还是空的。</p>
        <p class="sub">点下方按钮新建第一篇文档；或把收件箱里的内容归档到这里。</p>
        <button class="iconbtn primary" id="kb-empty-newdoc">${icon("folder-open", 13)} 新建第一篇文档</button>
      </div>`;
    const btn = el.querySelector("#kb-empty-newdoc");
    if (btn) btn.onclick = () => promptNewDocInDir(DOC.domain, DOC.sub === "_root" ? "" : DOC.sub);
    buildToc();
    document.dispatchEvent(new CustomEvent("kb:article-rendered"));
    return;
  }
  /* interview 域的题库类文档以美化版 HTML 为主（用户指定）：
     有旁挂 .html 且未强制 Markdown 视图时，直接内嵌美化版（forceMd=true 可切回） */
  const pretty = DOC.is_html || (DOC.has_html && DOC.domain === "interview" && !forceMd);
  el.classList.toggle("pretty-mode", pretty); // 美化版：去标题区、iframe 撑满父宽
  if (pretty) {
    // 整页 HTML：iframe 沙箱内嵌直通 /raw/（保留自带样式/脚本），
    // 绝不走 marked+DOMPurify 管线——大 HTML 过 markdown 解析会把源码平铺成数万节点 DOM，卡且不可读
    const srcRel = DOC.is_html ? DOC.rel : DOC.html_rel;
    const rawHref = rawUrl(srcRel);
    /* 用户要求：finish-bar 在最底部；美化版内部 .container 的 1200px 行宽注入覆盖为撑满
       （iframe 同源，onload 后向外层文档注入一条样式即可；不同美化版结构不一，用宽谱选择器） */
    el.innerHTML = `<div class="html-frame-wrap"><iframe class="html-frame" src="${rawHref}"
        sandbox="allow-same-origin allow-popups" title="${esc(DOC.title)}"
        onload="try{const d=this.contentDocument;d.head.insertAdjacentHTML('beforeend','<style>.container,body>main,body>div{max-width:100%!important;padding-left:1.4rem!important;padding-right:1.4rem!important}</style>')}catch(e){}"></iframe></div>
      <div class="kb-finish-bar" id="kb-finish-bar">
        <span class="kb-finish-q">读完这篇了？</span>
        <button type="button" class="kb-btn" id="mark-read-btn" onclick="toggleDocMark('read')" title="标记已读完（存本地复习库，不写语料）">已读完</button>
        <button type="button" class="kb-btn" id="mark-mastered-btn" onclick="toggleDocMark('mastered')" title="标记已掌握 —— 术语门户会显示为已掌握">已掌握</button>
      </div>`;
  } else {
    el.innerHTML = `<h1 class="a-title">${esc(DOC.title)}</h1>
      <div class="a-chips">${buildChipsRow()}</div>
      <div class="a-rule"></div>
      <div class="a-body">${DOMPurify.sanitize(renderMarkdownSafe(DOC.md), { FORBID_TAGS: ['style', 'iframe', 'form', 'script'], ADD_ATTR: ['target'] })}</div>
      <div class="kb-finish-bar" id="kb-finish-bar">
        <span class="kb-finish-q">读完这篇了？</span>
        <button type="button" class="kb-btn" id="mark-read-btn" onclick="toggleDocMark('read')" title="标记已读完（存本地复习库，不写语料）">已读完</button>
        <button type="button" class="kb-btn" id="mark-mastered-btn" onclick="toggleDocMark('mastered')" title="标记已掌握 —— 术语门户会显示为已掌握">已掌握</button>
      </div>`;
    applyReaderFonts(el); // 阅读字体双轨：英文 Cormorant/Work Sans + 中文宋黑回退（排版还原回 v2）
  }
  // mermaid：按需懒加载（3.5MB），仅文档真含 mermaid 图时加载
  const mm = el.querySelectorAll("pre code.language-mermaid");
  if (mm.length) {
    ensureMermaid().then(() => {
      const theme = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "neutral";
      window.mermaid.initialize({ startOnLoad: false, theme, securityLevel: "loose" });
      mm.forEach(b => {
        const div = document.createElement("div");
        div.className = "mermaid";
        div.textContent = b.textContent;
        b.closest("pre").replaceWith(div);
      });
      window.mermaid.run({ nodes: el.querySelectorAll("div.mermaid") }).then(() => {
        enhanceArticleDOM(el); // mermaid div 是异步产物，角标在此补挂（codeblock 部分幂等跳过）
      }).catch(() => {});
    }).catch(() => toast("mermaid 库加载失败，图示暂以代码块显示"));
  }
  if (window.hljs) el.querySelectorAll("pre code:not(.language-mermaid)").forEach(b => {
    try { hljs.highlightElement(b); } catch (e) {}
  });
  enhanceArticleDOM(el); // 问题8：渲染方直接产出 final-form，不再由 observer 事后打补丁
  enhanceRenderedBody(el); // 需求 #9 外链新标签 + #6 相对图片走 /raw 直服
  assignHeadingIds(el); // 文内锚点与 TOC 共用的标题 id
  enhanceInpageNav(el); // #7 片段链接平滑滚动 + #8 图片点击放大
  buildToc();
  decorateWikilinks(); // B4：[[双链]] 渲染为可点链接（正文里不再是方括号生肉）
  scrollToHash();      // B5：heading id 就绪后再兑现 URL 锚点
  document.dispatchEvent(new CustomEvent("kb:article-rendered")); // 页面级增强（Motion 刷新等）的显式挂点
}

/* ---------- B4：正文 [[双链]] → 可点链接 ----------
   解析结果复用 /api/links（FTS 派生），每文档缓存一次；保存/移动后随
   linksLoadedFor 一起失效重取。代码块 / 已有链接内的 [[..]] 不动。 */
let WL_MAP = null, WL_MAP_REL = "";
function invalidateWikilinkMap() { WL_MAP = null; WL_MAP_REL = ""; }

async function decorateWikilinks() {
  if (!DOC || DOC.is_html) return;
  const relAtStart = DOC.rel;
  if (!WL_MAP || WL_MAP_REL !== relAtStart) {
    try {
      const r = await fetch("/api/links?path=" + encodeURIComponent(relAtStart));
      if (!r.ok) return;
      const d = await r.json();
      const m = {};
      (d.outgoing || []).forEach(x => {
        if (!(x.raw in m)) m[x.raw] = x.resolved && x.path ? docUrl(x.path) : null;
      });
      WL_MAP = m; WL_MAP_REL = relAtStart;
    } catch (e) { return; }
  }
  if (!DOC || DOC.rel !== relAtStart) return; // 异步回来前已切文档
  const bodyEl = document.querySelector("#article .a-body");
  if (!bodyEl) return;
  const rx = /\[\[([^\[\]|#]+)(#[^\[\]|]*)?(?:\|([^\[\]]*))?\]\]/g;
  const walker = document.createTreeWalker(bodyEl, NodeFilter.SHOW_TEXT, {
    acceptNode(n) {
      if (!n.nodeValue || n.nodeValue.indexOf("[[") < 0) return NodeFilter.FILTER_REJECT;
      const p = n.parentElement;
      if (!p || p.closest("a, code, pre")) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach(node => {
    const text = node.nodeValue;
    rx.lastIndex = 0;
    if (!rx.test(text)) return;
    rx.lastIndex = 0;
    const frag = document.createDocumentFragment();
    let last = 0, m2;
    while ((m2 = rx.exec(text))) {
      if (m2.index > last) frag.appendChild(document.createTextNode(text.slice(last, m2.index)));
      const raw = m2[1].trim(), anchor = m2[2] || "", alias = (m2[3] || "").trim() || raw;
      const href = WL_MAP[raw];
      const a = document.createElement("a");
      if (href) {
        a.className = "wikilink";
        a.href = href + anchor; // B5：[[x#小节]] 带着锚点跳转
        a.textContent = alias;
        a.title = "双链 → " + raw;
      } else {
        a.className = "wikilink dead";
        a.textContent = alias;
        a.title = "未解析的双链：" + raw + "（语料里还没有这篇，右栏「双链」可见详情）";
      }
      frag.appendChild(a);
      last = m2.index + m2[0].length;
    }
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
    node.parentNode.replaceChild(frag, node);
  });
}

/* ---------- 正文后处理（阶段1·问题8，自 workbench.js observer 层迁入） ----------
   codeblock 顶栏（语言标签 + 复制）、mermaid 角标、H2 scrub 下划线属性。
   与 renderArticle 同帧执行：渲染方输出即最终形态，杜绝「半成品 + 赌时序清洗」的隐性契约。 */
function enhanceArticleDOM(el) {
  el.querySelectorAll(".a-body pre").forEach(pre => {
    if (pre.closest(".codeblock")) return; // 幂等：已包壳跳过
    if (pre.querySelector("code.language-mermaid")) return; // mermaid 源稍后整体替换为 div，不包壳
    const code = pre.querySelector("code");
    if (!code) return;
    const m = (code.className || "").match(/language-([\w+-]+)/);
    const lang = m ? m[1] : "text";
    const wrap = document.createElement("div"); wrap.className = "codeblock";
    const head = document.createElement("div"); head.className = "cb-head";
    head.innerHTML = `<span class="cb-lang">${esc(lang)}</span>` +
      `<button type="button" class="cb-copy" title="复制代码">${icon("copy-path", 12)}<span>复制</span></button>`;
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(head); wrap.appendChild(pre); // pre 原地移入，hljs 染色保留
    head.querySelector(".cb-copy").addEventListener("click", () =>
      copyText(code.textContent || "", "代码已复制到剪贴板"));
  });
  el.querySelectorAll(".a-body blockquote").forEach(bq => {
    if (bq.classList.contains("tip") || bq.classList.contains("warn")) return;
    const t = (bq.textContent || "").trim();
    // 引用变体（排版 v2）：首行 💡 → 蓝色提示；⚠️/❗ → 琥珀警告。纯前端约定，语料不用改。
    if (/^💡/.test(t)) bq.classList.add("tip");
    else if (/^[⚠️❗]/.test(t)) bq.classList.add("warn");
  });
  el.querySelectorAll(".a-body table").forEach(tb => {
    if (tb.closest(".tbl-wrap")) return; // 幂等：已包壳跳过
    const wrap = document.createElement("div"); wrap.className = "tbl-wrap";
    tb.parentNode.insertBefore(wrap, tb);
    wrap.appendChild(tb); // 圆角外框 + 横向滚动由 CSS 消费
  });
  el.querySelectorAll(".a-body ul li").forEach(li => {
    // GFM 任务清单：不同 marked 版本不一定给 task-list-item 类，同帧补齐
    if (li.querySelector(":scope > input[type=checkbox]")) li.classList.add("task-list-item");
  });
  el.querySelectorAll(".mermaid").forEach(div => {
    if (div.querySelector(".m-cap")) return;
    const cap = document.createElement("span");
    cap.className = "m-cap";
    cap.innerHTML = `${icon("md-code", 12)}<span>mermaid</span>`;
    div.appendChild(cap);
  });
  el.querySelectorAll(".a-body h1, .a-body h2, .a-body h3, .a-body h4").forEach(h => {
    if (h.id) return;
    // B5：标题 id = 文本去空白后空格→连字符，与 learn.js anchorHash 同一规则 ——
    // 闪卡「跳转原文」的 #锚点 第一次真正可定位（marked 不生成 heading id，
    // buildToc 的 sec-N 与卡片 anchor 永远接不上）。重名标题保留首个。
    const slug = (h.textContent || "").trim().replace(/\s+/g, "-");
    if (slug && !document.getElementById(slug)) h.id = slug;
  });
  el.querySelectorAll(".a-body h2").forEach(h => {
    if (!h.hasAttribute("data-scrub-underline")) h.setAttribute("data-scrub-underline", "");
  });
}

/* B5：URL fragment 定位（初始带 #锚点 进入 / 异步渲染完成后再滚一次） */
function scrollToHash() {
  const h = location.hash; if (!h || h.length < 2) return;
  let id; try { id = decodeURIComponent(h.slice(1)); } catch (e) { id = h.slice(1); }
  const t = id && document.getElementById(id);
  if (t) t.scrollIntoView({ block: "start" });
}

/* ---------- 阅读字体双轨（印刷排版还原后唯一保留项，2026-09-14 用户决定）：
   标题/引用用衬线栈（英文 Cormorant Garamond，中文思源宋/宋体），
   正文/UI 用无衬线栈（英文 Work Sans，中文思源黑/PingFang/微软雅黑）。
   字体离线 woff2 在 reader.css 注册；仅改字体家族，版式（字号/行高/间距/
   颜色/标题记号/表格/引用样式）全部维持 v2 排版不动。 ---------- */
function applyReaderFonts(el) {
  const body = el.querySelector(".a-body");
  if (!body || body.dataset.kbRdFont === "1") return;
  body.dataset.kbRdFont = "1";
  body.classList.add("rd-fonts");
}

/* 标题 slug id：marked 默认不给标题 id，文内 [x](#小节) 与右栏 TOC 都落不了点。
   规则与 GitHub 致：去标点、空白转 -、中文保留；重名追加 -1/-2。 */
function slugifyHeading(text, used) {
  let s = String(text).trim().toLowerCase()
    .replace(/[\u201c\u201d\u2018\u2019\u300c\u300d\u300e\u300f]/g, "")
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .replace(/\s+/g, "-");
  if (!s) s = "section";
  let id = s, i = 1;
  while (used.has(id)) { id = `${s}-${i++}`; }
  used.add(id);
  return id;
}
function assignHeadingIds(el) {
  const used = new Set([...el.querySelectorAll("[id]")].map(x => x.id));
  el.querySelectorAll(".a-body h1, .a-body h2, .a-body h3, .a-body h4").forEach(h => {
    if (!h.id) h.id = slugifyHeading(h.textContent, used);
  });
}
/* #7：文内片段链接（#开头）点击平滑滚动，不整页刷新；#8：图片点击放大 lightbox。 */
function enhanceInpageNav(el) {
  el.querySelectorAll(".a-body a[href^='#']").forEach(a => {
    if (a.dataset.kbNavBound) return;
    a.dataset.kbNavBound = "1";
    a.addEventListener("click", e => {
      e.preventDefault();
      let id; try { id = decodeURIComponent(a.getAttribute("href").slice(1)); } catch (_) { id = a.getAttribute("href").slice(1); }
      const t = id && document.getElementById(id);
      if (t) t.scrollIntoView({ behavior: "smooth", block: "start" });
      history.replaceState(null, "", "#" + encodeURIComponent(id));
    });
  });
  el.querySelectorAll(".a-body img").forEach(img => {
    if (img.dataset.kbZoomBound) return;
    img.dataset.kbZoomBound = "1";
    img.addEventListener("click", () => openImageZoom(img));
  });
}
function openImageZoom(img) {
  const ov = KB.overlay.open({
    className: "kb-imgzoom-ov",
    html: `<div class="kb-imgzoom"><img src="${esc(img.currentSrc || img.src)}" alt="${esc(img.alt || "")}"><div class="kb-imgzoom-hint">${esc(img.alt || "")} · 滚轮缩放 · 点击空白关闭</div></div>`,
    returnFocus: true,
  });
  const box = ov.root.querySelector(".kb-imgzoom");
  const big = ov.root.querySelector("img");
  let scale = 1;
  
  ov.root.addEventListener("wheel", e => {
    e.preventDefault();
    scale = Math.min(8, Math.max(0.3, scale * (e.deltaY < 0 ? 1.15 : 0.87)));
    big.style.transform = `scale(${scale})`;
  }, { passive: false });
}

function buildToc() {
  const pane = $("#pane-toc"); if (!pane) return;
  const heads = $$("#article .a-body h1, #article .a-body h2, #article .a-body h3");
  if (!heads.length) { pane.innerHTML = `<div style="font-size:12.5px;color:var(--faint);padding:6px 2px">本文无小节标题。</div>`; return; }
  pane.innerHTML = "";
  const used = new Set([...$("#article").querySelectorAll("[id]")].map(x => x.id));
  const pairs = [];
  heads.forEach((h, i) => {
    h.id = h.id || slugifyHeading(h.textContent, used);
    const a = document.createElement("a");
    a.textContent = h.textContent;
    a.className = h.tagName === "H3" ? "lv3" : "";
    a.onclick = () => { h.scrollIntoView({ behavior: "smooth", block: "start" }); tocOn(a); };
    pane.appendChild(a);
    pairs.push([h, a]);
  });
  const spy = new IntersectionObserver(entries => {
    entries.forEach(en => {
      if (!en.isIntersecting) return;
      const hit = pairs.find(([h]) => h === en.target);
      if (hit) tocOn(hit[1]);
    });
  }, { root: document.querySelector(".article"), rootMargin: "0px 0px -72% 0px", threshold: 0 });
  heads.forEach(h => spy.observe(h));
  tocOn(pairs[0][1]);
  renderTocSpark();
  function tocOn(a) { $$("#pane-toc a").forEach(x => x.classList.remove("on")); a.classList.add("on"); }
}

/* ---------- C3-B1：TOC 下方近 7 日阅读篇数 sparkline（reading.db 只读供数） ---------- */
let tocSparkSeq = 0;
function renderTocSpark() {
  const pane = $("#pane-toc"); if (!pane) return;
  const host = document.createElement("div");
  host.className = "kb-toc-spark";
  host.id = "kb-toc-spark";
  host.innerHTML = `<div class="kb-toc-spark-h">近 7 日阅读</div><div class="kb-toc-spark-b">…</div>`;
  pane.appendChild(host);
  const seq = ++tocSparkSeq;
  fetch("/api/learn/recent_read")
    .then(r => r.json())
    .then(d => {
      if (seq !== tocSparkSeq) return;           // 文档已切换，丢弃过期响应
      const body = host.querySelector(".kb-toc-spark-b");
      const days = (d && d.days) || [];
      const counts = days.map(x => x.count);
      if (!counts.length || counts.every(c => c === 0)) {
        body.innerHTML = `<div class="kb-toc-spark-empty">近 7 日暂无阅读</div>`;
        return;
      }
      const W = 210, H = 46, base = H - 14, top = 6;
      const max = Math.max(...counts, 1);
      const n = counts.length, slot = W / n, bw = Math.min(18, slot * 0.55);
      const avg = counts.reduce((s, c) => s + c, 0) / n;
      const peak = Math.max(...counts);
      let bars = "";
      counts.forEach((c, i) => {
        const h = c > 0 ? Math.max(2, (c / max) * (base - top)) : 1.5;
        const x = (i * slot + (slot - bw) / 2).toFixed(1);
        const y = (base - h).toFixed(1);
        const fill = c > 0 ? "var(--c-acc)" : "var(--c-line)";
        const op = c > 0 ? "" : ` opacity=".55"`;
        bars += `<rect x="${x}" y="${y}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" rx="2" fill="${fill}"${op}><title>${days[i].date}：${c} 篇</title></rect>`;
      });
      const avgY = (base - Math.max(2, (avg / max) * (base - top))).toFixed(1);
      body.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" height="${H}" role="img" aria-label="近 7 日阅读篇数柱状图">
        <line x1="0" y1="${base + 1}" x2="${W}" y2="${base + 1}" stroke="var(--c-line)" stroke-width="1"/>
        <line x1="0" y1="${avgY}" x2="${W}" y2="${avgY}" stroke="var(--c-line)" stroke-width="1" stroke-dasharray="3 3" opacity=".8"/>
        ${bars}</svg>
        <div class="kb-toc-spark-meta"><span>峰值 ${peak} 篇</span><span>日均 ${avg.toFixed(1)} 篇</span></div>`;
    })
    .catch(() => {
      const body = host.querySelector(".kb-toc-spark-b");
      if (body && seq === tocSparkSeq) body.innerHTML = `<div class="kb-toc-spark-empty">近 7 日暂无阅读</div>`;
    });
}

/* ---------- 分类树 / 文档列表（客户端渲染） ---------- */
/* 与 workbench.html 服务端模板保持一致：每个域带 .dom-caret 折叠箭头，且**默认全部收起**
   （不再强制当前域 open）。展开状态读/写 workbench.js 共用的 localStorage 钥匙 kb-tree-open，
   故客户端跳转（navigate）或 afterMutation 重渲染后，用户的折叠选择不会丢。 */
function treeOpenSet() {
  try { const raw = localStorage.getItem("kb-tree-open"); if (raw) return new Set(JSON.parse(raw)); } catch (e) {}
  return new Set();
}
function renderTree() {
  const nav = $("#tree"); if (!nav || !TREE) return;
  const open = treeOpenSet();   // 默认空集合 → 全部收起
  nav.innerHTML = TREE.map(d => {
    const isOpen = open.has(d.id);
    return `
   <div class="dom ${isOpen ? "open" : ""}" style="--dh:${HUES[d.id] || 158}" data-dom="${esc(d.id)}">
    <a class="dom-head ${CUR && CUR.domain === d.id ? "active" : ""}" href="/browse/${d.id}/${d.subs[0].id}" role="button" aria-expanded="${isOpen ? "true" : "false"}" title="${esc(d.label)} · 点击展开/收起">
     <span class="dom-glyph" style="--dh:${HUES[d.id] || 158}"><svg><use href="#i-${d.id}"/></svg></span>
     <span class="dom-name" title="${esc(d.label)}">${esc(d.label)}</span><span class="dom-n">${d.n}</span>
    </a>
    <div class="subs">${d.subs.map(s => {
      // 需求 #11：单列树 —— 文档内联在子域下（第二列列表列已移除）
      // 需求 #7：多层目录支持 —— name 含斜杠的深层文档按路径分组缩进
      const cur = CUR && CUR.domain === d.id && CUR.sub === s.id;
      const docsByDir = {};
      (s.docs || []).forEach(doc => {
        const slash = doc.name.lastIndexOf("/");
        const dir = slash >= 0 ? doc.name.slice(0, slash) : "";
        (docsByDir[dir] = docsByDir[dir] || []).push(doc);
      });
      const dirKeys = Object.keys(docsByDir).sort();
      const docLink = (doc, dir) => {
        const href = docUrl(`${d.id}/${s.id}/${doc.name}.md`);
        const leaf = dir ? doc.name.slice(dir.length + 1) : doc.name;
        const deep = dir ? dir.split("/").length : 0; // 多层缩进层级
        return `
        <a class="doc ${cur && CUR.name === doc.name ? "active" : ""} ${dir ? "in-subdir" : ""}" data-name="${esc(doc.name)}" data-dom="${esc(d.id)}" data-sub="${esc(s.id)}" draggable="true" style="--deep:${deep}" href="${href}" title="${esc(doc.name)}">
          <div class="doc-t">${doc.has_html ? `<span class="star" title="有美化版">${icon("external-link", 12)}</span>` : ""}${esc(leaf)}</div>
          <div class="doc-meta">${(doc.tags && doc.tags.length) ? doc.tags.map(t => `<span class="mini tag">${esc(t)}</span>`).join("") : ""}
          ${doc.has_html ? `<span class="mini html">美化版</span>` : ""}${doc.is_html ? `<span class="mini html">HTML</span>` : ""}</div>
        </a>`;
      };
      const groups = dirKeys.map(dir => dir === ""
        ? docsByDir[""].map(doc => docLink(doc, "")).join("")
        : `<div class="tree-subdir" style="--deep:${dir.split("/").length}"><div class="tree-subdir-h" title="${esc(dir)}">${icon("folder", 11)}<span class="tsd-t">${esc(dir.split("/").pop())}</span></div>${docsByDir[dir].map(doc => docLink(doc, dir)).join("")}</div>`
      ).join("");
      return `
      <a class="sub ${cur ? "active" : ""}" data-dom="${esc(d.id)}" data-sub="${esc(s.id)}" href="/browse/${d.id}/${s.id}" title="${esc(s.label)}"><span class="sub-t">${esc(s.label)}</span><span class="n">${s.n}</span></a>
      ${cur ? groups : ""}`;
    }).join("")}
    </div>
   </div>`;
  }).join("");
}

/* ---------- 目录聚合树（移动弹窗 + 目录统计共用；1 分钟缓存） ---------- */
let DIRTREE = null, DIRTREE_T = 0;
async function loadDirTree(force) {
  if (!force && DIRTREE && Date.now() - DIRTREE_T < 60000) return DIRTREE;
  const r = await fetch("/api/dir/tree");
  if (!r.ok) { toast("目录树加载失败：" + r.status); return null; }
  const d = await r.json();
  DIRTREE = d.domains || [];
  DIRTREE_T = Date.now();
  return DIRTREE;
}

function renderDocList(docs, subLabel, activeName) {
  const title = $("#list-title");
  if (title) title.innerHTML = `${esc(subLabel)}<span class="cnt">${docs.length}</span><button class="fold" onclick="togglePanel('list')" title="收起列表"><svg><use href="#i-fold-l"/></svg></button>`;
  const list = $("#doclist"); if (!list) return;
  /* 问题8：星标 ◈ 直接输出 SVG（原 workbench.js cleanChars 事后清洗的产物），
     href 统一走 docUrl(rel)（原手工拼接是第三份 encode 逻辑）。 */
  list.innerHTML = docs.map(d => `
    <a class="doc ${d.name === activeName ? "active" : ""}" data-name="${esc(d.name)}" draggable="true" href="${docUrl(`${CUR.domain}/${CUR.sub}/${d.name}.md`)}">
      <div class="doc-t">${d.has_html ? `<span class="star" title="有美化版">${icon("external-link", 12)}</span>` : ""}${esc(d.title)}</div>
      <div class="doc-meta">
        ${(d.tags && d.tags.length) ? d.tags.map(t => `<span class="mini tag">${esc(t)}</span>`).join("") : `<span class="mini untag">未打标</span>`}
        ${d.has_html ? `<span class="mini html">美化版</span>` : ""}
        ${d.is_html ? `<span class="mini html">HTML</span>` : ""}
      </div>
    </a>`).join("") || `<div style="padding:20px;color:var(--faint);font-size:13px">无匹配文档</div>`;
}

/* 图3：面包屑（正文区「域 / 子域」行）移除 —— 路径显示在底部状态栏左侧 #sb-path */
function updateStatusBarPath() {
  const el = document.getElementById("sb-path"); if (!el) return;
  el.textContent = DOC ? `${DOC.domain_label || ""} / ${DOC.sub_label || ""} · ${DOC.name || ""}`.replace(/^\s*\/\s*/, "") : "";
}

function renderCrumb() {
  const crumb = $("#crumb"); if (!crumb) return;
  if (!DOC) {
    // 无文档态（初始/已删除/404 自愈中）：给一个可用的空态行，不残留旧按钮也不留死白
    crumb.innerHTML = `<b>未选择文档</b><span class="spacer"></span>`;
    return;
  }
  /* 面包屑不再显示 content/<路径>（用户要求）；interview 域美化版文档的
     「Markdown 源 / 新标签页」按钮与 workbench.html 服务端渲染保持同一套结构 */
  const isInterviewPretty = DOC.has_html && DOC.domain === "interview" && !DOC.is_html;
  /* 书库格式（txt/pdf/xlsx/epub）：下载按钮统一并入本行最右（用户要求） */
  const libExt = (DOC.name || "").match(/\.(txt|pdf|xlsx|epub)$/i);
  crumb.innerHTML = `<b>${esc(DOC.title)}</b><span class="spacer"></span>
    ${isInterviewPretty ? `<button class="iconbtn" id="kb-md-src-btn" onclick="renderArticle(true)" title="切回 Markdown 渲染视图">${icon("file-md", 13)} Markdown 源</button>` : ""}
    ${DOC.has_html ? `<a class="iconbtn" href="${rawUrl(DOC.is_html ? DOC.rel : DOC.html_rel)}" target="_blank" title="新标签页打开美化版">${icon("external-link", 13)} 新标签页</a>` : ""}
    ${!DOC.is_html ? `<button class="iconbtn" onclick="openEditor()">${icon("edit",13)} 编辑</button>
    <button class="iconbtn" onclick="deleteDoc()" title="移入 content/_trash/">${icon("trash",13)} 删除</button>
    <button class="iconbtn" onclick="jumpToTagEdit()" title="编辑本篇标签（右栏信息·标签页）">${icon("tag-outline",13)} 标签</button>` : ""}
    <button class="iconbtn primary ${DOC.favorite ? "faved" : ""}" id="fav-btn" onclick="toggleFav()">${icon("star",13)} ${DOC.favorite ? "已收藏" : "收藏"}</button>
    ${libExt ? `<a class="iconbtn" id="kb-lib-dl" href="${rawUrl(DOC.rel)}" download="${esc(DOC.name || "文件")}" title="下载原文件">${icon("download", 13)} 下载</a>` : ""}`;
}

function renderInfo() {
  const pane = $("#pane-info"); if (!pane || !DOC) return;
  const rows = (DOC.info_rows || []).map(([k, v]) =>
    `<div class="meta-row"><span class="k">${esc(k)}</span><span class="v">${esc(v)}</span></div>`).join("");
  const editable = !DOC.is_html; // .md 可写；.html 美化版语料不可写 → 只读展示
  const tags = (DOC.fm && Array.isArray(DOC.fm.tags)) ? DOC.fm.tags : [];
  const tagChips = tags.length
    ? tags.map(t => `<span class="tagchip" data-tag="${esc(t)}"><span class="tagchip-name">${esc(t)}</span>${editable ? `<button type="button" class="tagchip-x" title="移除标签「${esc(t)}」" aria-label="移除标签 ${esc(t)}" onclick="removeTag(this.parentElement)">${icon("cancel-x", 11)}</button>` : ""}</span>`).join("")
    : (editable ? `<span class="tag-empty">还没有标签</span>` : `<span class="tag-empty">美化版不支持在线编辑标签</span>`);
  pane.innerHTML =
    `<div class="tag-edit${editable ? "" : " readonly"}">
      <div class="tag-edit-h">${icon("tag-outline", 13)} 标签${editable ? `<button type="button" class="tag-edit-addbtn" id="tag-add-btn" title="添加标签">+ 添加</button>` : ""}</div>
      <div class="tag-chips" id="tag-chips">${tagChips}</div>
      <div class="tag-inputrow" id="tag-inputrow" hidden>
        <input id="tag-in" placeholder="输入标签，逗号可批量，回车确认" maxlength="64" list="kb-tag-datalist" autocomplete="off">
      </div>
    </div>
    <div class="meta-row"><span class="k">版本</span><span class="v">git 全程可追溯</span></div>` + rows;
  const addBtn = pane.querySelector("#tag-add-btn");
  const row = pane.querySelector("#tag-inputrow");
  const input = pane.querySelector("#tag-in");
  if (addBtn && row && input) {
    addBtn.addEventListener("click", () => { row.hidden = !row.hidden; if (!row.hidden) { fillTagDatalist(); input.focus(); } });
    input.onkeydown = e => {
      if (e.key === "Enter") { e.preventDefault(); const raw = input.value.trim(); if (raw) addTagsFromRaw(raw); input.value = ""; }
      else if (e.key === "Escape") { row.hidden = true; }
    };
  }
}

/* 快赢：标签智能补全 —— 全库 Top 标签入 datalist，从录入端杜绝「C#/C#C#」式分叉。
   Story 4：datalist 提升为 body 级全局单例 —— 头部就地输入框与右栏 pane 输入框
   共用同一份（renderInfo 每次重建 pane，datalist 放 pane 里会导致头部引用悬空）。 */
function fillTagDatalist() {
  let dl = document.getElementById("kb-tag-datalist");
  if (!dl) {
    dl = document.createElement("datalist");
    dl.id = "kb-tag-datalist";
    document.body.appendChild(dl);
  }
  if (dl.options.length) return;
  fetch("/api/globalstats").then(r => r.json()).then(d => {
    if (!d || !Array.isArray(d.top_tags)) return;
    dl.innerHTML = d.top_tags.slice(0, 60).map(t => `<option value="${esc(t.tag)}">`).join("");
  }).catch(() => {});
}

/* ---------- 标签编辑（需求 #2）：走 /api/tags，服务端行级手术写回 ---------- */
function addTagsFromRaw(raw) {
  // 逗号 / 中文逗号 / 分号分隔批量输入；单枚去空白
  const tags = raw.split(/[,，;；]/).map(s => s.trim()).filter(Boolean);
  if (!tags.length) return;
  apiTags({ op: "add", tags });
}

function removeTag(chipEl) {
  const t = chipEl && chipEl.dataset.tag;
  if (!t) return;
  apiTags({ op: "remove", tags: [t] });
}

async function apiTags(payload) {
  if (!DOC) return;
  try {
    const r = await fetch("/api/tags", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: DOC.rel, ...payload })
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok || !data.ok) throw new Error(data.error || ("HTTP " + r.status));
    DOC.fm.tags = data.tags || [];
    renderInfo();
    renderChipsRow();          // 正文头部 chips 同步
    // 左列表徽标同步：列表数据来自 findSub(domain, sub).docs（含每篇的 tags 快照）
    if (CUR) {
      const s2 = findSub(CUR.domain, CUR.sub);
      if (s2) {
        const hit = (s2.docs || []).find(d => d.name === DOC.name);
        if (hit) hit.tags = data.tags || [];
        renderDocList(s2.docs, s2.label, CUR.name);
      }
    }
    toast(data.tags.length ? `标签已保存（${data.tags.length} 枚）` : "标签已清空");
  } catch (e) {
    toast("标签保存失败：" + e.message);
  }
}

/* Story 4：头部 chips 行构造 —— renderArticle 初始渲染与 renderChipsRow 刷新共用
   一份模板（此前两处手写重复，改一处漏一处）。标签 chip 就地可编辑：× 删除
   复用现有 removeTag（按钮自带 data-tag），+ 展开就地输入框回车添加；
   html 美化版语料不可写，保持只读。 */
function buildChipsRow() {
  const editable = !DOC.is_html;
  const tags = (DOC.fm && Array.isArray(DOC.fm.tags)) ? DOC.fm.tags : [];
  const tagChips = tags.length
    ? tags.map(t => `<span class="chip acc tag-chip">${esc(t)}${editable
        ? `<button type="button" class="chip-x" data-tag="${esc(t)}" title="移除标签「${esc(t)}」" aria-label="移除标签 ${esc(t)}" onclick="removeTag(this)">${icon("cancel-x", 9)}</button>`
        : ""}</span>`).join("")
    : `<span class="chip warn">tags 未打标</span>`;
  return [
    `<span class="chip acc">${esc(DOC.source_label)}</span>`,
    DOC.fm.source_path ? `<span class="chip">${esc(DOC.fm.source_path)}</span>` : "",
    DOC.fm.collected ? `<span class="chip">${esc(DOC.fm.collected)} 收录</span>` : "",
    tagChips,
    editable ? `<button type="button" class="chip chip-btn chips-add" onclick="chipsAddToggle()" title="添加标签">+ 标签</button>` : "",
  ].filter(Boolean).join("");
}

function renderChipsRow() {
  const el = document.querySelector(".a-chips"); if (!el || !DOC) return;
  el.innerHTML = buildChipsRow();
}

/* Story 4：头部「+ 标签」→ 就地展开输入框（复用全局 datalist 补全），
   回车批量添加走现有 addTagsFromRaw → /api/tags；Esc/空失焦收起。 */
function chipsAddToggle() {
  const row = document.querySelector(".a-chips"); if (!row || !DOC) return;
  const existed = row.querySelector(".chips-in");
  if (existed) { existed.remove(); return; } // 再点 + 收起
  fillTagDatalist();
  const input = document.createElement("input");
  input.className = "chips-in";
  input.maxLength = 64;
  input.placeholder = "标签，逗号分隔，回车添加";
  input.setAttribute("list", "kb-tag-datalist");
  input.setAttribute("autocomplete", "off");
  input.setAttribute("aria-label", "添加标签");
  row.appendChild(input);
  input.focus();
  input.addEventListener("keydown", e => {
    if (e.key === "Enter") {
      e.preventDefault();
      const raw = input.value.trim();
      input.remove();
      if (raw) addTagsFromRaw(raw); // 成功后 apiTags 会调 renderChipsRow 重建整行
    } else if (e.key === "Escape") {
      input.remove();
    }
  });
  input.addEventListener("blur", () => { if (!input.value.trim()) input.remove(); });
}

/* 需求 #2 补充：编辑标签入口在右上角 crumb 按钮组（收藏旁），点开右栏「信息·标签」页 */
function jumpToTagEdit() {
  const infoTab = document.querySelector('.rtab[data-pane="info"]');
  if (infoTab) tab("info", infoTab);
  const row = $("#tag-inputrow");
  if (row && row.hidden) { const b = $("#tag-add-btn"); if (b) b.click(); }
  else { const input = $("#tag-in"); if (input) input.focus(); }
}
window.jumpToTagEdit = jumpToTagEdit;

function renderNotes() {
  const pane = $("#pane-notes"); if (!pane || !DOC) return;
  pane.innerHTML = `<div id="notes-list">` + ((DOC.notes || []).map(n =>
    `<div class="note-card"><div class="when">${esc(n.when)} · 旁挂 .notes.md</div><p>${esc(n.text)}</p></div>`).join("")
    || `<div style="padding:6px 2px;font-size:12.5px;color:var(--faint)">还没有备注，写下第一条。</div>`)
    + `</div><div class="note-input"><input id="ni" placeholder="追加备注，回车保存…"><button onclick="addNote()">记</button></div>`;
  const ni = $("#ni"); if (ni) ni.onkeydown = e => { if (e.key === "Enter") addNote(); };
}

/* ---------- 客户端路由（仅阅读页；其他页面走普通跳转） ---------- */
const WORKBENCH = !!document.getElementById("article");
let ED_LAST_HREF = location.pathname + location.search; // 最近一次成功导航的地址（dirty guard 中止 popstate 时恢复地址栏用）

async function navigate(url, push) {
  if (!WORKBENCH) {
    // 非阅读页（总览/搜索/收藏）：同类 URL 原地不动，避免 back 触发重复刷新
    if (location.pathname + location.search !== url) location.href = url;
    return;
  }
  // 问题1：导航前必须过 dirty guard；用户选「继续编辑」则中止本次导航。
  // popstate（push=false）时地址栏已经变了，中止就把上一个成功地址推回去，保持地址与内容一致。
  if (!(await tryCloseEditor())) {
    if (!push) history.pushState({}, "", ED_LAST_HREF);
    return;
  }
  ED_LAST_HREF = url;
  const path = url.split("?")[0];
  const segs = path.split("/").filter(Boolean).map(s => { try { return decodeURIComponent(s); } catch (e) { return s; } });
  // /doc/<domain>/<sub>/<name...>
  if (segs[0] === "doc" && segs.length >= 4) {
    const domain = segs[1], sub = segs[2], name = segs.slice(3).join("/");
    await loadTree();
    if (push) history.pushState({}, "", url);
    await openDoc(domain, sub, name);
    return;
  }
  // /browse/<domain>/<sub> → 打开该子域第一篇
  if (segs[0] === "browse" && segs.length === 3) {
    await loadTree();
    const s = findSub(decodeURIComponent(segs[1]), decodeURIComponent(segs[2]));
    if (!s || !s.docs.length) { location.href = url; return; }
    const first = s.docs[0];
    // 问题8：原这里是局部 `const docUrl = …` 手工拼接（第三份 _root/encode 逻辑），
    // 改名并统一走 KB.util.docUrl(rel) 单一实现。
    const firstDocUrl = docUrl(`${segs[1]}/${segs[2]}/${first.name}.md`);
    if (push) history.pushState({}, "", url);
    await navigate(firstDocUrl, false);
    return;
  }
  location.href = url; // 其余页面（总览/搜索/收藏）走整页加载
}

async function openDoc(domain, sub, name) {
  CUR = { domain, sub, name };
  const s = findSub(domain, sub);
  if (s) renderDocList(s.docs, s.label, name);
  renderTree();
  /* 问题14：加载反馈——fetch 期间放骨架（3 行灰条）。本地通常 <50ms 无感知，
     但磁盘冷读 / 索引重建时不能让正文区挂着一篇旧文档静默等待。 */
  const artEl = $("#article");
  if (artEl) artEl.innerHTML = `<div class="kb-skeleton" aria-busy="true" aria-label="文档加载中">
    <i style="width:62%"></i><i style="width:93%"></i><i style="width:78%"></i></div>`;
  const r = await fetch(`/api/doc?domain=${encodeURIComponent(domain)}&sub=${encodeURIComponent(sub)}&name=${encodeURIComponent(name)}`);
  if (!r.ok) {
    if (artEl) artEl.innerHTML = `<div class="a-kicker">无法打开</div><h1 class="a-title">${esc(name)}</h1>
      <div class="a-rule"></div><div class="a-body"><p>${r.status === 404 ? "文档不存在（可能已被删除或移动）。" : "加载失败 " + r.status + "。"}</p></div>`;
    toast(r.status === 404 ? "文档不存在（可能已被删除）" : "加载失败 " + r.status);
    // 第三轮 #10：404 = 树缓存陈旧（文档已删/已移）→ 失效重拉树自愈，右侧列表同步消失
    if (r.status === 404) { invalidate("tree"); await loadTree(); renderTree();
      if (CUR) { const s2 = findSub(CUR.domain, CUR.sub); if (s2) renderDocList(s2.docs, s2.label, null); } }
    // bug 修复：404 也必须重建 crumb 按钮——此前 crumb 停在上一态（可能是“已删除”纯文本），
    // 用户看到的就是「编辑/删除/收藏按钮全消失」
    DOC = null;
    renderCrumb();
    updateStatusBarPath();
    return;
  }
  const data = await r.json();
  DOC = data.doc;
  updateStatusBarPath();
  // 编辑态残留防护：openDoc 必须从干净阅读态开始（删除文档后再开新文档时，
  // 编辑器/class 残留会让新文档的 crumb 按钮“消失”或编辑态错乱）
  const ed = $("#editor"); if (ed) ed.classList.remove("show");
  const artEl2 = $("#article"); if (artEl2) artEl2.style.display = "";
  ED_OPEN = false;
  renderArticle();
  renderCrumb();
  renderInfo();
  renderNotes();
  setTrackingDoc(DOC.rel);
  linksLoadedFor = null;
  if (document.querySelector("#pane-links.active")) loadLinks(); // 停在双链标签时跟随切换
  const art = document.querySelector(".article"); if (art) art.scrollTop = 0;
  resetReadProgress(); // C1：新文档渲染前进度归零（restoreReadPos 回跳时 scroll 事件自然续上）
  restoreReadPos();
}

/* ---------- 快赢：阅读位置记忆 ----------
   per-doc scrollTop 存 localStorage['kb-readpos']；进入文档恢复，滚动防抖写入。 */
const READPOS_LS = "kb-readpos";
let readposTimer = null;
function readposLoad(rel) {
  try { return (JSON.parse(localStorage.getItem(READPOS_LS) || "{}")[rel]) | 0; } catch (e) { return 0; }
}
function readposSave(rel, top) {
  try {
    const all = JSON.parse(localStorage.getItem(READPOS_LS) || "{}");
    all[rel] = Math.round(top);
    const keys = Object.keys(all);
    if (keys.length > 500) delete all[keys[0]]; // 控制体积：只保留最近 500 篇
    localStorage.setItem(READPOS_LS, JSON.stringify(all));
  } catch (e) {}
}
function wireReadPos() {
  const art = document.querySelector(".article");
  if (!art) return;
  art.addEventListener("scroll", () => {
    if (!DOC) return;
    clearTimeout(readposTimer);
    readposTimer = setTimeout(() => readposSave(DOC.rel, art.scrollTop), 400);
  }, { passive: true });
}
wireReadPos();
/* ---------- C1：阅读进度条接线（--kb-read-pct，阶段3 埋的 .article::before） ----------
   passive + rAF 节流（不每帧强制重排）；reset 与 navigate 的 scrollTop=0 同帧。 */
let readPctRaf = 0;
function wireReadProgress() {
  const art = document.querySelector(".article");
  if (!art || art.dataset.kbReadPct === "1") return;
  art.dataset.kbReadPct = "1";
  art.addEventListener("scroll", () => {
    if (readPctRaf) return;
    readPctRaf = requestAnimationFrame(() => {
      readPctRaf = 0;
      const max = art.scrollHeight - art.clientHeight;
      const pct = max > 40 ? Math.min(100, Math.max(0, (art.scrollTop / max) * 100)) : 0;
      art.style.setProperty("--kb-read-pct", pct.toFixed(2) + "%");
    });
  }, { passive: true });
}
wireReadProgress();
function resetReadProgress() {
  const art = document.querySelector(".article");
  if (art) art.style.setProperty("--kb-read-pct", "0%");
}
function restoreReadPos() {
  const art = document.querySelector(".article");
  if (!art || !DOC) return;
  const saved = readposLoad(DOC.rel);
  if (saved > 40) { art.scrollTop = saved; toast("已回到上次阅读位置"); }
}

/* 点击拦截：阅读页内站内文档/分类链接走客户端路由，不再整页刷新 */
document.addEventListener("click", e => {
  if (!WORKBENCH) return;
  if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  const a = e.target.closest("a");
  if (!a || a.target === "_blank" || a.hasAttribute("download")) return;
  const href = a.getAttribute("href");
  if (!href || !/^\/(doc|browse)\//.test(href)) return;
  e.preventDefault();
  navigate(href, true);
});
window.addEventListener("popstate", () => {
  if (!WORKBENCH) return;
  // #锚点点击也会触发 popstate：path+search 未变时不重渲染，只兑现滚动位置
  const now = location.pathname + location.search;
  if (now === ED_LAST_HREF || now === location.pathname + location.search && ED_LAST_HREF && ED_LAST_HREF.split("#")[0] === now) { scrollToHash(); return; }
  navigate(location.pathname + location.search, false);
});

/* ---------- 编辑 ---------- */
/* frontmatter 原文：openEditor 曾直接用 JSON.stringify 重建 fm，
   会把 `tags: [AI资产, 越狱词]` 写成 `tags: ["AI资产","越狱词"]` —— 用户「打开即保存」
   什么都没改也会把 content/ 弄脏。这里改为从 /raw/<rel> 取回原始 frontmatter 块原样填入。
   缓存键是 DOC.rel，换文档自动失效。 */
let FM_RAW = null;      // "---\n…\n---\n"；无 frontmatter 时为 ""；取不到时为 null
let FM_RAW_REL = "";
let ED_INITIAL_HEAD = "";  // 打开编辑器时填入的 frontmatter 区块，保存前用来判断用户动没动过
/* 问题1 修复（dirty guard）：语料是唯一事实源，编辑中途按 Esc / 点树 / 路由跳转
   曾经把未保存内容静默丢弃。ED_SNAPSHOT 记录打开瞬间的全文，tryCloseEditor() 是唯一
   关闭入口：无差异直接关，有差异弹三键弹窗（保存并关闭 / 丢弃修改 / 继续编辑）。
   Escape、navigate、popstate、编辑器「取消」按钮全部改走该入口。 */
let ED_OPEN = false;
let ED_SNAPSHOT = "";
let UC_OPEN = false; // confirmUnsavedChanges 在展示中：防重入（连按 Esc / 弹窗期间又点树）

async function fetchFmRaw() {
  if (!DOC || !DOC.rel) return null;
  if (FM_RAW_REL === DOC.rel && FM_RAW !== null) return FM_RAW;
  try {
    const r = await fetch(rawUrl(DOC.rel));
    if (!r.ok) return null;
    const txt = await r.text();
    const m = txt.match(/^\uFEFF?---[ \t]*\r?\n[\s\S]*?\r?\n---[ \t]*(?:\r?\n|$)/);
    FM_RAW = m ? m[0] : "";
    FM_RAW_REL = DOC.rel;
    return FM_RAW;
  } catch (e) {
    return null;
  }
}

/* 兜底序列化：只有 /raw 取不到原文时才用，尽量贴近语料常见的无引号列表风格 */
function fmSerialize(fm) {
  const one = (v) => {
    if (v === true || v === false) return String(v);
    if (Array.isArray(v)) return "[" + v.join(", ") + "]";
    const s = String(v);
    return /^[A-Za-z0-9_.\-\u4e00-\u9fa5][A-Za-z0-9_ .\-\u4e00-\u9fa5]*$/.test(s) ? s : JSON.stringify(s);
  };
  return "---\n" + Object.entries(fm || {}).map(([k, v]) => `${k}: ${one(v)}`).join("\n") + "\n---\n";
}

async function openEditor() {
  if (!DOC || DOC.is_html) return;
  // 需求 #12：书库格式（txt/pdf/xlsx/epub）不进 Markdown 编辑器
  if (/\.(txt|pdf|xlsx|epub)$/i.test(DOC.name || "")) { toast("书库文件不支持在线编辑，请下载后用本地应用处理"); return; }
  $("#article").style.display = "none";
  $("#editor").classList.add("show");
  const hint = $("#ed-hint");
  if (hint) hint.style.display = ""; // frontmatter 引导：这是编辑页顶部空白区的用途说明
  $("#ed-path").textContent = DOC.rel;
  const raw = await fetchFmRaw();
  const head = raw != null ? raw : fmSerialize(DOC.fm);
  $("#ed-text").value = (raw ? raw + "\n" : head + "\n") + DOC.md;
  ED_INITIAL_HEAD = head;   // 保存前用来判断用户有没有动过 frontmatter
  ED_OPEN = true;
  ED_SNAPSHOT = $("#ed-text").value; // dirty guard 基准快照
  /* Story 2：CodeMirror 接管输入载体。attach 内部会 loadIntoCM(ta.value)
     并把内容实时同步回 ta.value —— 上面刚设好的 value/ED_SNAPSHOT 契约不变。
     bundle 未加载时 attach 静默返回，回落裸 textarea。 */
  if (window.KBED) KBED.attach(); else $("#ed-text").focus();
  toast("编辑态 · 保存即写回文件系统，git 记录本次变更");
}
function editorIsOpen() {
  const ed = $("#editor");
  return !!ed && ed.classList.contains("show");
}
function closeEditor() {
  const ed = $("#editor"); if (!ed) return;
  const hint = $("#ed-hint");
  if (hint) hint.style.display = "none";
  ed.classList.remove("show");
  $("#article").style.display = "";
  ED_OPEN = false;
  // Story 2：退出编辑态前把 CM 最终内容落回 ta.value 并隐藏 CM
  if (window.KBED) KBED.detach();
}
/* 未保存确认弹窗：kbModal 只有两键，按其视觉规范做三键弹层（问题11 前例）。
   resolve "save" | "discard" | null（继续编辑 / Esc / 遮罩）。问题13：走 KB.overlay 原语。 */
function confirmUnsavedChanges() {
  return new Promise(resolve => {
    UC_OPEN = true;
    const ov = KB.overlay.open({
      html: `<div class="kbm" role="document">
      <div class="kbm-title">${icon("warn", 16)} 编辑器有未保存的修改<span class="spacer" style="flex:1"></span><button class="iconbtn uc-x" title="关闭（Esc）" aria-label="关闭">${icon("cancel-x", 14)}</button></div>
      <div class="kbm-body">关闭会丢失未写回的修改。先保存，还是直接丢弃？</div>
      <div class="kbm-btns">
        <button class="iconbtn uc-keep">继续编辑</button>
        <button class="iconbtn danger uc-discard">丢弃修改</button>
        <button class="iconbtn primary uc-save">保存并关闭</button>
      </div></div>`,
      onClose: () => { UC_OPEN = false; resolve(null); },
      initialFocus: root => root.querySelector(".uc-keep"),
    });
    let settled = false;
    const done = v => { if (settled) return; settled = true; resolve(v); ov.close("btn"); };
    ov.root.querySelector(".uc-keep").onclick = () => done(null);
    ov.root.querySelector(".uc-x").onclick = () => done(null);
    ov.root.querySelector(".uc-discard").onclick = () => done("discard");
    ov.root.querySelector(".uc-save").onclick = () => done("save");
    
  });
}
/* 唯一的「关编辑器」入口：无改动直接关；有改动先问。返回 true = 编辑器已可关闭。 */
async function tryCloseEditor() {
  if (UC_OPEN) return false; // 确认弹窗已在展示：不叠加第二个，调用方中止
  if (!editorIsOpen()) return true;
  const ta = $("#ed-text");
  if (!ta || ta.value === ED_SNAPSHOT) { closeEditor(); return true; }
  const act = await confirmUnsavedChanges();
  if (act === "discard") { closeEditor(); return true; }
  if (act === "save") {
    const ok = await saveDoc();
    if (ok) closeEditor(); // saveDoc 内部不再自行关闭，dirty 状态由快照刷新清除
    return !!ok;
  }
  return false; // 继续编辑：调用方（navigate 等）必须中止
}
async function saveDoc() {
  let text = $("#ed-text").value;
  /* 安全网：若用户没动过 frontmatter 区块，落盘前还原成语料原文区块，
     杜绝任何序列化差异（引号、顺序、空行）污染 content/。
     比对前两侧都归一到 LF：FM_RAW 来自 /raw（CRLF 语料含 \r），
     textarea 值永远是 LF——不归一则 head === ED_INITIAL_HEAD 永假，
     安全网沦为死逻辑（残留 2，2026-09-13 修复）。还原时用 FM_RAW 原文
     （含 \r），与语料字节保真一致。 */
  if (FM_RAW && ED_INITIAL_HEAD) {
    const m = text.match(/^\uFEFF?---[ \t]*\r?\n[\s\S]*?\r?\n---[ \t]*(?:\r?\n|$)/);
    const head = m ? m[0] : "";
    const lf = (s) => s.replace(/\r\n/g, "\n");
    if (head && lf(head) === lf(ED_INITIAL_HEAD) && lf(head) !== lf(FM_RAW)) text = FM_RAW + text.slice(head.length);
  }
  const r = await fetch("/api/save", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: DOC.rel, content: text }) });
  if (!r.ok) { toast("保存失败：" + (await r.text()).slice(0, 120)); return false; }
  /* 注意：JS 正则不支持 \A（那会被当成字面字母 A，导致永远匹配失败）——
     曾因这里写成 \A，保存后本地 DOC.md 被错误地存成「含 frontmatter 的全文」，
     下次打开编辑器就拼出双 frontmatter 落盘。JS 里文本开头用 ^（无 m 标志时）。 */
  const fm = {}, m = text.match(/^---\n([\s\S]*?)\n---\n\n?/);
  let body = text;
  if (m) {
    for (const line of m[1].split("\n")) {
      const i = line.indexOf(":");
      if (i > 0) {
        const k = line.slice(0, i).trim(), v = line.slice(i + 1).trim();
        fm[k] = v === "true" ? true : (v.startsWith("[") ? v.slice(1, -1).split(",").map(x => x.trim().replace(/^"|"$/g, "")).filter(Boolean) : v.replace(/^"|"$/g, ""));
      }
    }
    body = text.slice(m[0].length);
  }
  DOC.fm = fm; DOC.md = body; DOC.title = fm.title || DOC.title;
  const sd = findSub(CUR.domain, CUR.sub);
  const td = sd && sd.docs.find(x => x.name === DOC.name);
  if (td) { td.title = DOC.title; persistTree(); }
  linksLoadedFor = null;
  invalidateWikilinkMap(); // B4：正文双链解析结果随保存失效
  ED_SNAPSHOT = text; // dirty 基准同步（tryCloseEditor 不再弹「未保存」确认）
  /* 需求 #9 / 图4 第五修：先退编辑器，再重渲染。
     此前 closeEditor 排在 renderArticle/renderCrumb 之后——四次修复都加了退出逻辑，
     但任一重渲染抛异常（frontmatter 手改坏、DOM 竞态）都会中断执行链，
     编辑器永远收不回去，用户看到的就是「保存写回后还是编辑态」。
     现在：先 closeEditor 保证视图必然还原，渲染包 try/catch 兜底刷新页面。 */
  closeEditor();
  try {
    renderArticle(); renderCrumb(); renderInfo();
  } catch (err) {
    console.error("保存后重渲染失败，强制整页刷新兜底", err);
    toast("已保存，但视图刷新异常，正在刷新页面…");
    setTimeout(() => location.reload(), 600);
    return true;
  }
  toast(`已写回 <span class="mono">${esc(DOC.rel)}</span> · 索引已更新 · git 可 diff`);
  return true;
}const edText = $("#ed-text");
if (edText) edText.onkeydown = e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); saveDoc(); }
};

/* ---------- 备注 ---------- */
async function addNote() {
  const i = $("#ni"); const text = i.value.trim(); if (!text) return;
  const btn = i.closest(".note-input").querySelector("button"); // 问题14：pending 防连点
  if (btn) btn.disabled = true;
  try {
    const r = await fetch("/api/note", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: DOC.rel, text }) });
    if (!r.ok) { toast("备注失败"); return; }
    const data = await r.json(); i.value = "";
    DOC.notes = data.notes;
    renderNotes();
    toast("备注已写入旁挂 <span class='mono'>.notes.md</span>");
  } finally { if (btn) btn.disabled = false; }
}

/* ---------- 已读完 / 已掌握（文档级标记，存 indexes/reading.db 的 doc_marks，不写语料） ---------- */
function renderDocMark(m) {
  const rb = document.getElementById("mark-read-btn");
  const mb = document.getElementById("mark-mastered-btn");
  if (!rb || !mb) return;
  rb.classList.toggle("mark-on", !!m.read);
  rb.textContent = m.read ? "✓ 已读完" : "已读完";
  mb.classList.toggle("mark-on", !!m.mastered);
  mb.textContent = m.mastered ? "✓ 已掌握" : "已掌握";
}
function refreshDocMark() {
  if (!DOC || !DOC.rel) return;
  fetch("/api/docmark?path=" + encodeURIComponent(DOC.rel))
    .then(r => r.json())
    .then(j => { if (j.ok) renderDocMark(j); })
    .catch(() => {});
}
async function toggleDocMark(kind) {
  if (!DOC || !DOC.rel) return;
  const btn = document.getElementById(kind === "read" ? "mark-read-btn" : "mark-mastered-btn");
  const cur = btn.classList.contains("mark-on");
  btn.disabled = true; // 问题14：pending 防连点（连点会把 on/off 序列打到后端）
  let r;
  try {
    r = await fetch("/api/docmark", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: DOC.rel, mark: kind, on: !cur }) });
  } finally { btn.disabled = false; }
  if (!r.ok) { toast("标记失败：" + (await r.text()).slice(0, 100)); return; }
  const j = await r.json();
  renderDocMark(j);
  toast(kind === "mastered"
    ? (j.mastered ? "已标记掌握 —— 术语门户会显示为已掌握" : "已取消掌握标记")
    : (j.read ? "已标记读完" : "已取消读完（掌握标记一并取消）"));
}

/* ---------- 收藏 ---------- */
async function toggleFav() {
  const b = $("#fav-btn");
  if (b) b.disabled = true; // 问题14：pending 防连点
  let r;
  try {
    r = await fetch("/api/favorite", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: DOC.rel }) });
  } finally { if (b) b.disabled = false; }
  if (!r.ok) { toast("操作失败"); return; }
  const data = await r.json();
  DOC.favorite = data.favorite;
  b.innerHTML = `${icon("star",13)} ${data.favorite ? "已收藏" : "收藏"}`;
  b.classList.toggle("faved", data.favorite);
  // 同步树缓存里的收藏标记，收藏页/列表星星即时一致
  const s = findSub(DOC.domain, DOC.sub);
  const td = s && s.docs.find(x => x.name === DOC.name);
  if (td) { td.favorite = data.favorite; persistTree(); }
  toast(data.favorite ? "已收藏 · favorite: true 写入 frontmatter" : "已取消收藏");
}

/* ---------- 树缓存持久化（增删改后即时同步） ---------- */
function persistTree() {
  /* 问题10：废除 sig:"(本地已改)" 假标记——它从不参与任何校验（loadTree 只看
     domains 数组），留着只会让人误以为有 sig 机制。 */
  try { localStorage.setItem(LS_TREE, JSON.stringify({ domains: TREE })); } catch (e) {}
}
/* 缓存失效唯一入口（问题10）：kind ∈ tree | dirtree | palette | links | all。
   TREE/LS_TREE/DIRTREE 的作废只允许走这里；palette 缓存在 kb-core 手里，
   经 KB.palette.dropCache 接线。B4：正文双链映射（/api/links 派生）同属派生缓存，
   写操作后随 links/all 一起作废。 */
function invalidate(kind) {
  kind = kind || "all";
  if (kind === "all" || kind === "tree") {
    TREE = null;
    try { localStorage.removeItem(LS_TREE); } catch (e) {}
  }
  if (kind === "all" || kind === "dirtree") { DIRTREE = null; DIRTREE_T = 0; }
  if (kind === "all" || kind === "palette") {
    if (window.KB && KB.palette && KB.palette.dropCache) KB.palette.dropCache();
  }
  if (kind === "all" || kind === "links") invalidateWikilinkMap();
}
window.invalidate = invalidate; // 统一失效入口（pages/*.js 可用；invalidateCaches 别名在 misc 切换后已删除）
/* 写操作（移动/重命名/新建/删除等）后的统一局部重渲染（问题9）：
   缓存失效 → 重拉 /api/tree → 重画分类树 + 当前子域列表；当前文档自身被移动时
   由调用方再走 navigate(docUrl(dst)) 客户端跳转。禁止 setTimeout + location.reload——
   此前 6 处 reload 把 toast 随页面一起销毁，900–1600ms 假死还丢反馈。
   非工作台页（inbox/tags）各自有数据源，只需 invalidate("all") 后做局部 DOM 更新。 */
async function afterMutation() {
  invalidate("all");
  await loadTree();
  renderTree();
  if (WORKBENCH && CUR) {
    const s = findSub(CUR.domain, CUR.sub);
    if (s) renderDocList(s.docs, s.label, DOC && DOC.name);
  }
}
window.afterMutation = afterMutation;

/* ---------- 删除（软删除：移入 _trash，kbModal 统一确认，问题11） ---------- */
let undoDelete = null; // 快赢：删除可撤销 —— toast 撤销按钮触发的反向 move 闭包
async function deleteDoc() {
  if (!DOC || DOC.is_html) return;
  const rel = DOC.rel, deletedTitle = DOC.title;
  const c = await kbModal({
    title: icon("trash", 16) + " 删除这篇文档？",
    body: `《<b>${esc(deletedTitle)}</b>》及其旁挂美化版 / 备注将整体移入 <span class="mono">content/_trash/</span>（软删除，可找回；git 历史是第二重保险）。`,
    danger: true, confirmText: "移入回收站", cancelText: "取消",
  });
  if (!c) return;
  // 问题2：悲观更新——先等 /api/delete 落盘，成功后才动 UI 与树缓存；失败保持原状。
  const delBtns = [...document.querySelectorAll("#crumb .iconbtn, #ed-del")].filter(b => b.textContent.includes("删除") || b.id === "ed-del");
  delBtns.forEach(b => { b.disabled = true; });
  let r;
  try {
    r = await fetch("/api/delete", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: rel }) });
  } catch (e) {
    toast("删除请求失败（网络异常），文件未变动");
    return;
  } finally {
    delBtns.forEach(b => { b.disabled = false; });
  }
  if (!r.ok) {
    let err = ""; try { err = (await r.json()).error || ""; } catch (e) {}
    toast("服务端删除失败" + (err ? "：" + err : "") + "（文件仍在 " + esc(rel) + "，可重试）");
    return;
  }
  const s = findSub(DOC.domain, DOC.sub);
  if (s) {
    s.docs = s.docs.filter(x => x.name !== DOC.name);
    s.n = s.docs.length;
    const d = TREE.find(x => x.id === DOC.domain);
    if (d) d.n = d.subs.reduce((a, x) => a + x.n, 0);
    persistTree();
    renderTree();
    renderDocList(s.docs, s.label, null);
  }
  closeEditor(); // 删除已确认，编辑器（若开着）随文档一并作废
  DOC = null;
  $("#article").innerHTML = `<div class="a-kicker">已删除</div>
    <h1 class="a-title">文档已移入回收站</h1>
    <div class="a-rule"></div>
    <div class="a-body"><p>《${esc(deletedTitle)}》及其美化版、备注已一起移入 <code>content/_trash/</code>，git 历史亦可找回。</p>
    <p>从左侧选择其他文档继续阅读。</p></div>`;
  $("#crumb").innerHTML = `<b>已删除</b><span class="sep">·</span>${esc(deletedTitle)}`;
  // 快赢：删除可撤销 —— 5 秒内 toast 内点「撤销」反向 move 回原路径
  const trashRel = rel.replace(/^content\//, "");
  const undo = async () => {
    const r2 = await fetch("/api/move", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ src: trashRel, dst: rel }) });
    if (r2.ok) {
      toast("已撤销删除，文档已放回原位");
      invalidate("tree"); await loadTree(); renderTree();
    } else {
      toast("撤销失败：文件仍在回收站，可手动移回");
    }
  };
  undoDelete = undo; // 存到模块级变量，toast 按钮触发（toast 是 innerHTML 注入，无法直接闭包）
  toast(`已移入回收站 · <button type="button" class="undo-del" onclick="undoDelete()" style="background:none;border:1px solid var(--c-line);color:var(--c-acc);border-radius:6px;padding:2px 10px;margin-left:6px;cursor:pointer;font-size:12px">撤销</button>`, 6000);
}

/* ---------- 双链面板（懒加载） ---------- */
let linksLoadedFor = null;
function loadLinks() {
  const pane = $("#pane-links"); if (!pane) return;
  if (!DOC || DOC.is_html) { pane.innerHTML = `<div class="empty" style="padding:10px 2px">HTML 文档暂无双链解析。</div>`; return; }
  if (linksLoadedFor === DOC.rel) return;
  linksLoadedFor = DOC.rel;
  pane.innerHTML = `<div style="padding:6px 2px;font-size:12.5px;color:var(--faint)">解析中…</div>`;
  fetch("/api/links?path=" + encodeURIComponent(DOC.rel))
    .then(r => r.json())
    .then(d => {
      const back = d.incoming.map(x =>
        `<a class="result" href="${docUrl(x.path)}"><div class="doc-t">${esc(x.title)}</div><div class="rp">${esc(x.path)}</div></a>`).join("");
      const fwd = d.outgoing.map(x => x.resolved
        ? `<a class="result" href="${docUrl(x.path)}"><div class="doc-t">${esc(x.title)}</div><div class="rp">${esc(x.path)}</div></a>`
        : `<div class="kblink-row dead"><span class="t">未解析：${esc(x.raw)}</span><button type="button" class="fix" data-raw="${esc(x.raw)}" title="为该断链目标创建占位文档">补建</button></div>`).join("");
      pane.innerHTML =
        `<div class="home-sec" style="margin-top:4px">谁引用了它 · ${d.incoming.length}</div>` +
        (back || `<div style="font-size:12.5px;color:var(--faint);padding:4px 2px">还没有。写别的文档时打个 [[${esc(DOC.title)}]] 就连上了。</div>`) +
        `<div class="home-sec" style="margin-top:16px">它引用 · ${d.outgoing.length}</div>` +
        (fwd || `<div style="font-size:12.5px;color:var(--faint);padding:4px 2px">本文没有 [[双链]]。</div>`);
      pane.querySelectorAll(".kblink-row .fix").forEach(b => {
        b.addEventListener("click", () => fixDeadLink(b.dataset.raw || ""));
      });
      document.dispatchEvent(new CustomEvent("kb:links-rendered")); // roam 增强挂点（问题8：替代 observer）
    })
    .catch(() => { pane.innerHTML = `<div class="empty" style="padding:10px 2px">加载失败，稍后再试。</div>`; linksLoadedFor = null; });
}

/* ---------- C2：断链「补建占位」——走既有 /api/save 写回，不新造通道 ----------
   目标域解析：/api/wikilink/suggest Top1 有 → 落该建议所在子域（复用既有分类）；
   无建议 → 落当前文档同域根（不落 _inbox：_ 前缀目录 api_save 400 拒写且不进索引，
   补建的占位文档必须可解析、可检索）。确认弹窗防误建；失败 toast 不静默。 */
async function fixDeadLink(raw) {
  raw = String(raw || "").trim();
  if (!raw) return;
  let sug = null;
  try {
    const r = await fetch("/api/wikilink/suggest?q=" + encodeURIComponent(raw) + "&limit=1");
    const d = await r.json();
    if (d && d.items && d.items[0] && d.items[0].score >= 70) sug = d.items[0]; // 仅采信高分建议（精确/前缀/包含）
  } catch (e) {}
  const rel = sug ? sug.rel : (DOC ? DOC.rel.split("/").slice(0, 2).join("/") + "/" + raw + ".md" : raw + ".md");
  const where = sug ? `已有相似文档「${sug.name}」在 ${sug.rel}——将创建的占位仍按你输入命名` : `落当前文档同域：${rel}`;
  const res = await kbModal({
    title: "补建占位文档",
    body: `为断链 <span class='mono'>[[${esc(raw)}]]</span> 创建占位 Markdown。<br><span style="color:var(--faint);font-size:12px">${esc(where)}</span>`,
    inputs: [{ key: "nm", label: "目标路径（域/子域/文件名.md）", value: rel }],
    confirmText: "创建",
  });
  if (!res || !res.nm) return; // 取消 → 不建
  const r = await fetch("/api/save", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: res.nm, content: `# ${raw}\n\n> 由断链补建占位生成（源：[[${raw}]]），待整理。\n` }) });
  if (!r.ok) { toast("补建失败：" + r.status); return; }
  toast("占位已创建：" + res.nm);
  await afterMutation();          // 既有刷新链（FTS/树/计数）
  invalidateWikilinkMap();        // 正文 [[双链]] 解析表失效
  linksLoadedFor = null;          // 双链面板缓存失效
  if (DOC && $("#article")) renderArticle(); // 当前正文重渲染：dead wikilink 即时转正常
  if (document.querySelector("#pane-links.active")) loadLinks(); // 面板停留时立即重载（断链行消失）
}

/* ---------- 美化版弹窗（KB.overlay：Esc/遮罩/焦点归还统一，问题13） ---------- */
let PRETTY_OV = null;
function openPretty() {
  if (!DOC || !DOC.has_html) return;
  if (PRETTY_OV) PRETTY_OV.close("re-open");
  const rawHref = rawUrl(DOC.html_rel);
  const ov = KB.overlay.open({
    className: "pretty-ov show",
    html: `<div class="pretty-box">
      <div class="pretty-bar"><span class="pt">${esc(DOC.title)} · 美化版</span>
        <a class="iconbtn" id="pretty-newtab" href="${rawHref}" target="_blank">${icon("external-link", 12)} 新窗口</a>
        <button class="iconbtn pp-close">${icon("cancel-x", 12)} 关闭</button></div>
      <iframe src="${rawHref}" sandbox="allow-same-origin allow-popups" title="${esc(DOC.title)}"></iframe></div>`,
    onClose: () => { PRETTY_OV = null; },
  });
  PRETTY_OV = ov;
  ov.root.querySelector(".pp-close").onclick = () => ov.close("btn");
  
}
function closePretty() { if (PRETTY_OV) PRETTY_OV.close("api"); }

/* ---------- 右键菜单：文档移动 / 复制双链 / 统计信息 ----------
   问题13：改走 KB.overlay——Esc 关闭、关闭归还焦点、Tab 被困在菜单内；
   新增 ↑↓ 导航 + 打开即聚焦首项，配合下方 ContextMenu/Shift+F10 唤起入口。 */
let CTX = null; // 当前菜单目标 {kind:'doc'|'sub', rel|domain, sub, name}
let CTX_OV = null;

function closeCtxMenu() {
  if (CTX_OV) { const o = CTX_OV; CTX_OV = null; o.close("api"); }
  CTX = null;
}

function docRelOf(domain, sub, name) {
  return sub === "_root" ? `${domain}/${name}.md` : `${domain}/${sub}/${name}.md`;
}

function openCtxMenu(x, y, items) {
  if (CTX_OV) { const o = CTX_OV; CTX_OV = null; o.close("re-open"); }
  const ov = KB.overlay.open({
    className: "ctx-menu",
    html: items.map((it, i) =>
      it === "-" ? `<div class="ctx-sep"></div>` :
      `<button class="ctx-item ${it.danger ? "danger" : ""}" data-i="${i}">${it.icon ? `<span class="ctx-ic">${it.icon}</span>` : ""}<span>${esc(it.label)}</span></button>`).join(""),
    returnFocus: true,
  });
  CTX_OV = ov;
  const r = ov.root.getBoundingClientRect();
  ov.root.style.left = Math.min(x, innerWidth - r.width - 8) + "px";
  ov.root.style.top = Math.min(y, innerHeight - r.height - 8) + "px";
  ov.root.addEventListener("click", e => {
    const b = e.target.closest(".ctx-item");
    if (!b) return;
    const it = items[+b.dataset.i];
    CTX_OV = null; ov.close("pick");
    if (it && it.fn) it.fn();
  });
  ov.root.addEventListener("keydown", e => {
    const btns = [...ov.root.querySelectorAll(".ctx-item")];
    if (!btns.length) return;
    const i = btns.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); btns[(i + 1) % btns.length].focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); btns[(i - 1 + btns.length) % btns.length].focus(); }
    else if (e.key === "Home") { e.preventDefault(); btns[0].focus(); }
    else if (e.key === "End") { e.preventDefault(); btns[btns.length - 1].focus(); }
  });
  setTimeout(() => {
    const first = ov.root.querySelector(".ctx-item"); if (first) first.focus();
    // 点击菜单外任意处关闭（once + isConnected 守卫，close 后自动失效）
    document.addEventListener("mousedown", function off(ev) {
      if (!ov.root.isConnected) return;
      if (!ov.root.contains(ev.target)) { CTX_OV = null; ov.close("outside"); }
      else document.addEventListener("mousedown", off, { once: true });
    }, { once: true });
  }, 0);
}

async function copyText(t, okMsg) {
  try { await navigator.clipboard.writeText(t); toast(okMsg); }
  catch (e) {
    const ta = document.createElement("textarea"); ta.value = t; document.body.appendChild(ta);
    ta.select(); document.execCommand("copy"); ta.remove(); toast(okMsg);
  }
}

function showStats(rel) {
  fetch("/api/stats?path=" + encodeURIComponent(rel))
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(s => {
      const kb = (s.size / 1024).toFixed(1);
      const rows = [
        ["标题", s.title], ["路径", s.path],
        ["字数", `${s.chars} 字符（中文 ${s.cjk} · 英数词 ${s.words}）`],
        ["结构", `${s.lines} 行 · ${s.headings} 个标题 · ${s.code_blocks} 个代码块`],
        ["双链", s.wikilinks + " 条"],
        ["标签", s.tags.length ? s.tags.join("、") : "未打标"],
        ["来源", s.source || "—"], ["收录", s.collected || "—"],
        ["文件", kb + " KB · 修改 " + new Date(s.mtime * 1000).toLocaleString()],
      ];
      const ov = KB.overlay.open({
        className: "pretty-ov",
        html: `<div class="pretty-box stats-box"><div class="pretty-bar"><span class="pt">统计信息</span><button class="iconbtn gs-close">${icon("cancel-x", 12)} 关闭</button></div>
      <div class="stats-body">${rows.map(([k, v]) => `<div class="meta-row"><span class="k">${esc(k)}</span><span class="v">${esc(v)}</span></div>`).join("")}</div></div>`,
      });
      ov.root.querySelector(".gs-close").onclick = () => ov.close("btn");
      
    })
    .catch(err => toast("统计失败：" + (err.message || err)));
}

/* ---------- 通用弹窗（替代系统 prompt/alert/confirm） ----------
   kbModal({ title, body, html, inputs:[{key,label,value,placeholder}], confirmText, cancelText, danger })
   → Promise<null | { values:{key:value} }>；Esc / 取消 / 点击遮罩返回 null。
   问题13：焦点管理（Tab 陷阱 / 关闭归还）统一委托 KB.overlay 原语，不再各写 Esc。 */
function kbModal(opt) {
  return new Promise(resolve => {
    const inputs = opt.inputs || [];
    const ov = KB.overlay.open({
      html: `<div class="kbm" role="document">
      <div class="kbm-title"><span class="kbm-title-t">${opt.title && opt.title.indexOf("<") >= 0 ? opt.title : esc(opt.title || "")}</span><span class="spacer" style="flex:1"></span><button class="iconbtn kbm-x" title="关闭（Esc）" aria-label="关闭">${icon("cancel-x", 14)}</button></div>
      ${opt.body ? `<div class="kbm-body">${opt.body}</div>` : ""}
      ${opt.html ? `<div class="kbm-body">${opt.html}</div>` : ""}
      ${inputs.map(i => `<label class="kbm-label">${esc(i.label || "")}
        <input class="kbm-input" data-k="${esc(i.key)}" value="${esc(i.value ?? "")}"
          placeholder="${esc(i.placeholder || "")}" spellcheck="false"></label>`).join("")}
      <div class="kbm-btns">
        <button class="iconbtn kbm-cancel">${esc(opt.cancelText || "取消")}</button>
        <button class="iconbtn primary kbm-ok ${opt.danger ? "danger" : ""}">${esc(opt.confirmText || "确定")}</button>
      </div></div>`,
      onClose: () => resolve(null), // Esc / 遮罩（未显式完成时）统一按「取消」结算
      initialFocus: root => { const i = root.querySelector(".kbm-input"); return i || null; },
    });
    let settled = false;
    const done = val => { if (settled) return; settled = true; resolve(val); ov.close("done"); };
    const collect = () => {
      const values = {};
      ov.root.querySelectorAll(".kbm-input").forEach(inp => values[inp.dataset.k] = inp.value.trim());
      return values;
    };
    ov.root.querySelector(".kbm-ok").onclick = () => done(collect());
    ov.root.querySelector(".kbm-cancel").onclick = () => done(null);
    const xbtn = ov.root.querySelector(".kbm-x");
    if (xbtn) xbtn.onclick = () => done(null);
    
    ov.root.addEventListener("keydown", e => {
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey || !inputs.length)) { e.preventDefault(); done(collect()); }
    });
    const first = ov.root.querySelector(".kbm-input");
    if (first) { first.focus(); first.select(); }
  });
}

async function showSubStats(dom, sub) {
  const r = await fetch(`/api/substats?domain=${encodeURIComponent(dom)}&sub=${encodeURIComponent(sub)}`);
  if (!r.ok) { toast("目录统计失败：" + r.status); return; }
  const s = await r.json();
  const maxTag = s.tags.length ? s.tags[0].n : 1;
  const tagRows = s.tags.map(t => `
    <div class="ss-tag"><span class="ss-tag-name">${esc(t.tag)}</span>
      <span class="ss-bar"><i style="width:${Math.round(100 * t.n / maxTag)}%"></i></span>
      <span class="ss-tag-n">${t.n}</span></div>`).join("") || `<div class="kbm-li">无标签</div>`;
  // 兄弟目录排行（可点击切换）：与移动弹窗共用 /api/dir/tree 聚合数据
  const dirTree = await loadDirTree();
  const domObj = (dirTree || []).find(d => d.id === s.domain);
  const siblings = domObj ? domObj.subs.filter(x => x.id !== s.sub) : [];
  const sibRows = siblings.map(x => `
    <button class="ss-sib" onclick="openCtxStats('${esc(s.domain)}','${esc(x.id)}')">
      <span class="ss-sib-l">${esc(x.label)}</span>
      <span class="ss-sib-bar"><i style="width:${Math.round(100 * x.n / Math.max(1, domObj.subs[0].n))}%"></i></span>
      <span class="ss-sib-n">${x.n} 篇 · ${Math.round(x.cjk / 1000)}k 字</span>
    </button>`).join("") || `<div class="kbm-li">本域仅此一个目录</div>`;
  let ov = KB.overlay.open({ // 目录统计层实例（兄弟切换须走 close，见模块级 SUBSTATS_OV）
    html: `<div class="kbm kbm-stats" role="document">
    <div class="kbm-title">${icon("chart", 16)} ${esc(s.domain_label)} / ${esc(s.label)} · 目录统计<span class="spacer" style="flex:1"></span><button class="iconbtn ss-x" title="关闭（Esc）" aria-label="关闭">${icon("cancel-x", 14)}</button></div>
    <div class="kbm-body">
    <div class="gkpi">
      <div class="g"><div class="lab">文档</div><div class="num acc">${s.n_docs}</div><div class="sub">本目录篇数</div></div>
      <div class="g"><div class="lab">总字数</div><div class="num">${s.total_cjk.toLocaleString()}</div><div class="sub">CJK 字符</div></div>
      <div class="g"><div class="lab">篇均字数</div><div class="num">${s.avg_cjk.toLocaleString()}</div><div class="sub">字 / 篇</div></div>
      <div class="g"><div class="lab">未打标</div><div class="num ${s.n_untagged ? "warn" : "acc"}">${s.n_untagged}</div><div class="sub">待补 tags</div></div>
    </div>
    <div class="ss-sec">标签分布 Top ${s.tags.length}</div>
    <div class="ss-tags">${tagRows}</div>
    <div class="ss-sec">最近更新</div>
    <div class="kbm-li">《${esc(s.newest.title || "—")}》 · ${esc(s.newest.when)}</div>
    ${siblings.length ? `<div class="ss-sec">${esc(s.domain_label)} · 其他目录</div><div class="ss-sibs">${sibRows}</div>` : ""}
    </div>
    <div class="kbm-btns"><button class="iconbtn primary ss-close">关闭</button></div></div>`,
  });
  SUBSTATS_OV = ov;
  ov.root.querySelector(".ss-close").onclick = () => ov.close("btn");
  
}
let SUBSTATS_OV = null; // 当前目录统计层实例
function openCtxStats(dom, sub) {
  if (SUBSTATS_OV) SUBSTATS_OV.close("switch"); // 兄弟目录切换：走 close，别裸 remove（会泄漏监听与计数）
  showSubStats(dom, sub);
}

/* ---------- 全库聚合统计（顶栏全局「统计」按钮）----------
   与目录统计共用 .ss-* 视觉；数据来自 /api/globalstats。 */
let GS_OV = null; // 当前全库统计层实例（重开时 close 旧的）
/* ---------- 中期功能：AI 问吧（RAG 对话）—— /api/ask 检索增强问答 ----------
   v3 重构：内容区在上、输入区固定在底部（标准问答布局）；
   推荐问题作为空态卡片放进内容区（不再堆在输入框上方）；
   顶部说明文字移除，副标题一句话交代「问吧 = 生成答案，搜索 = 找文档」的区别。 */
let ASK_OV = null;
const ASK_SUGGESTIONS = [
  { icon: "i-file-md", q: "我最近收录了哪些笔记？" },
  { icon: "i-search-magnifier", q: "我记过哪些关于向量数据库的内容？" },
  { icon: "i-tag-outline", q: "帮我总结一下面试相关的要点" },
  { icon: "i-hint-bulb", q: "有哪些值得复习的知识点？" },
];
function askTime() { const d = new Date(); return String(d.getHours()).padStart(2,"0") + ":" + String(d.getMinutes()).padStart(2,"0"); }
function askEsc(s) { return String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c])); }
function askEmptyState() {
  return `<div class="ask-empty" id="ask-empty">
    <div class="ask-empty-h">${icon("hint-bulb", 15)} 直接提问，我读完你的语料再回答</div>
    <div class="ask-cards">
      ${ASK_SUGGESTIONS.map(s => `<button class="ask-card" data-q="${askEsc(s.q)}">${icon(s.icon, 13)}<span>${askEsc(s.q)}</span></button>`).join("")}
    </div>
  </div>`;
}
async function showAsk() {
  if (ASK_OV) ASK_OV.close("re-open");
  const ov = KB.overlay.open({
    html: `<div class="kbm kbm-ask" role="document">
      <div class="kbm-title ask-head">
        <span class="ask-logo">${icon("hint-bulb", 16)}</span>
        <span class="ask-title-txt">问吧</span>
        <span class="ask-sub">生成答案 · 附引用</span>
        <span class="spacer" style="flex:1"></span>
        <button class="iconbtn ask-clear" title="清空对话" aria-label="清空对话">${icon("trash-outline", 13)}</button>
        <button class="iconbtn ask-close" title="关闭（Esc）" aria-label="关闭">${icon("cancel-x", 14)}</button>
      </div>
      <div class="kbm-body ask-body" id="ask-body">${askEmptyState()}</div>
      <div class="ask-inputrow">
        <input id="ask-in" placeholder="问一个需要综合多篇文档的问题…" autocomplete="off" aria-label="提问">
        <button class="iconbtn primary ask-go" id="ask-go" title="发送（Enter）">${icon("move-arrow", 13)} 提问</button>
      </div>
      <div class="ask-foot">
        <span><kbd>Enter</kbd> 发送</span>
        <span><kbd>Shift</kbd>+<kbd>Enter</kbd> 换行</span>
        <span class="ask-foot-hint">只想找文档？用顶栏搜索框（<kbd>/</kbd>）</span>
      </div></div>`,
  });
  ASK_OV = ov;
  ov.root.querySelector(".ask-close").onclick = () => ov.close("btn");

  const bodyEl = ov.root.querySelector("#ask-body");
  const input = ov.root.querySelector("#ask-in");
  const go = ov.root.querySelector("#ask-go");
  const esc2 = askEsc;
  const scrollB = () => { bodyEl.scrollTop = bodyEl.scrollHeight; };

  /* 清空对话 */
  ov.root.querySelector(".ask-clear").onclick = () => {
    bodyEl.innerHTML = askEmptyState();
    input.focus();
  };

  /* 打字动效 */
  const showPending = () => {
    bodyEl.insertAdjacentHTML("beforeend",
      `<div class="ask-msg ask-ai ask-pending" id="ask-pending"><div class="ask-typing"><i></i><i></i><i></i></div><span class="ask-pending-txt">检索语料并生成中…</span></div>`);
    scrollB();
  };

  const addMsg = (cls, html, isAI) => {
    const id = "ask-m" + Date.now() + Math.random().toString(36).slice(2, 6);
    bodyEl.insertAdjacentHTML("beforeend",
      `<div class="ask-msg ${cls}" id="${id}">
        <div class="ask-msg-text">${html}</div>
        <div class="ask-msg-meta"><span class="ask-msg-time">${askTime()}</span>${isAI ? `<button class="ask-copy" title="复制回答">${icon("save-write", 11)} 复制</button>` : ""}</div>
      </div>`);
    scrollB();
    return ov.root.querySelector("#" + id);
  };

  const ask = async () => {
    const qv = input.value.trim();
    if (!qv || go.disabled) return;
    go.disabled = true; input.disabled = true;
    const empty = ov.root.querySelector("#ask-empty");
    if (empty) empty.remove();
    addMsg("ask-me", esc2(qv), false);
    input.value = "";
    showPending();
    try {
      const r = await fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q: qv }) });
      const d = await r.json().catch(() => ({}));
      const pending = ov.root.querySelector("#ask-pending");
      if (pending) pending.remove();
      if (!r.ok || !d.ok) {
        const hint = d.error === "not_configured" ? "AI 服务未配置：需要有效的 KB_AI_API_KEY（当前 key 无效或缺失）。其余功能不受影响。"
          : (d.error || "HTTP " + r.status);
        addMsg("ask-err", esc2(hint), false);
      } else {
        const srcs = (d.sources || []).map(s =>
          `<a href="${s.url || docUrl(String(s.path || "").replace(/\.md$/, ""))}" class="ask-src" title="${esc2(s.path)}">${icon("file-md", 10)} ${esc2(String(s.path || "").split("/").slice(-2).join("/"))}</a>`).join("");
        addMsg("ask-ai", esc2(d.answer).replace(/\n/g, "<br>") + (srcs ? `<div class="ask-srcs"><span class="ask-srcs-cap">来源</span>${srcs}</div>` : ""), true);
      }
    } catch (e) {
      const pending = ov.root.querySelector("#ask-pending");
      if (pending) pending.remove();
      addMsg("ask-err", "请求失败：" + esc2(String(e.message || e)), false);
    } finally {
      go.disabled = false; input.disabled = false; input.focus();
      scrollB();
    }
  };

  /* 空态推荐卡片（事件委托，清空后重建仍可用） */
  bodyEl.addEventListener("click", e => {
    const card = e.target.closest(".ask-card");
    if (card) { input.value = card.dataset.q; input.focus(); ask(); return; }
    const cp = e.target.closest(".ask-copy");
    if (cp) {
      const txt = cp.closest(".ask-msg").querySelector(".ask-msg-text").innerText;
      copyText(txt, "已复制到剪贴板");
    }
  });

  go.onclick = ask;
  input.onkeydown = e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); } };
  input.focus();
}
window.showAsk = showAsk;

async function showGlobalStats() {
  if (GS_OV) GS_OV.close("re-open"); // 重开时走 close，防监听/计数泄漏
  const ov = KB.overlay.open({
    html: `<div class="kbm kbm-stats" role="document">
    <div class="kbm-title">${icon("chart", 16)} 全库统计<span class="spacer" style="flex:1"></span><a class="iconbtn" href="/stats" title="月度阅读趋势在统计页">${icon("trend", 13)} 月度趋势</a><button class="iconbtn gs-close" title="关闭（Esc）" aria-label="关闭">${icon("cancel-x", 14)}</button></div>
    <div class="kbm-body" id="gs-body">统计中…</div></div>`,
  });
  GS_OV = ov;
  ov.root.querySelector(".gs-close").onclick = () => ov.close("btn");
  
  const bodyEl = ov.root.querySelector("#gs-body");
  let d;
  try {
    const r = await fetch("/api/globalstats");
    if (!r.ok) { bodyEl.textContent = "统计失败：" + r.status; return; }
    d = await r.json();
  } catch (e) { bodyEl.textContent = "统计失败：" + e; return; }
  const maxDom = Math.max(1, ...d.domains.map(x => x.n));
  const maxTag = Math.max(1, ...(d.top_tags || []).map(t => t.n));
  const L = d.links || { total: 0, dead: 0, dead_docs: 0 };
  bodyEl.innerHTML = `
    <div class="gkpi">
      <div class="g"><div class="lab">文档</div><div class="num acc">${d.n_docs.toLocaleString()}</div><div class="sub">美化版 ${d.n_html} · 收藏 ${d.n_fav}</div></div>
      <div class="g"><div class="lab">总字数</div><div class="num">${d.total_cjk.toLocaleString()}</div><div class="sub">CJK 字符</div></div>
      <div class="g"><div class="lab">标签覆盖</div><div class="num ${d.tagged_pct < 50 ? "warn" : "acc"}">${d.tagged_pct}<span class="u">%</span></div><div class="sub">共 ${d.n_tag_types} 种标签</div></div>
      <div class="g"><div class="lab">双链健康</div><div class="num ${L.dead ? "rose" : "acc"}">${L.dead}</div><div class="sub">死链 / 共 ${L.total} 链</div></div>
    </div>
    <div class="ss-sec">各域分布 · ${d.domains.length} 域</div>
    <div class="ss-tags">${d.domains.map(x => {
      const h = (window.HUES && HUES[x.id]) || 158;
      return `
      <div class="ss-tag"><span class="ss-tag-name"><i class="ss-dot" style="background:hsl(${h} 58% 45%)"></i>${esc(x.label)}</span>
        <span class="ss-bar"><i style="width:${Math.round(100 * x.n / maxDom)}%;background:linear-gradient(90deg,hsl(${h} 52% 40%),hsl(${h} 68% 55%))"></i></span>
        <span class="ss-tag-n">${x.n}</span></div>`;}).join("")}</div>
    <div class="ss-sec">Top 标签 · 共 ${d.n_tag_types} 种</div>
    <div class="ss-tags">${(d.top_tags || []).map(t => `
      <div class="ss-tag"><span class="ss-tag-name">${esc(t.tag)}</span>
        <span class="ss-bar"><i style="width:${Math.round(100 * t.n / maxTag)}%"></i></span>
        <span class="ss-tag-n">${t.n}</span></div>`).join("") || `<div class="kbm-li">无标签</div>`}</div>
    <div class="ss-sec">其他</div>
    <div class="kbm-li">美化版 HTML ${d.n_html} 份 · 收藏 ${d.n_fav} 篇 · 收件箱待归档 ${d.inbox}</div>
    ${L.dead ? `<div class="kbm-li" style="color:var(--rose)">${L.dead} 条死链分布在 ${L.dead_docs} 篇文档中</div>` : ""}`;
}

/* ---------- 移动 / 重命名：目录树选择器 ----------
   树节点 = 真实目录（域可展开为子目录）；目标目录点击选择，
   文件名可改，路径实时预览；同名冲突/越界/空名前端拦截，后端 /api/move 兜底。 */
async function moveDocPrompt(rel) {
  const dirTree = await loadDirTree(true);
  if (!dirTree || !dirTree.length) { toast("目录树为空，无法移动"); return; }
  const parts = rel.split("/");
  const fileName = parts.pop().replace(/\.md$/, "");
  const srcDir = parts.join("/");
  // 域根文档 → sub=_root；子目录文档（含嵌套 architecture/xx）→ sub=parts[1]
  const curSubId = parts.length >= 2 ? parts[1] : "_root";

  const ov = document.createElement("div");
  ov.className = "kbm-ov";
  ov.id = "mv-ov";
  ov.innerHTML = `<div class="kbm kbm-mv" role="dialog" aria-modal="true">
    <div class="kbm-title">${icon("swap", 16)} 移动 / 重命名<span class="spacer" style="flex:1"></span><button class="iconbtn mv-x" title="关闭（Esc）" aria-label="关闭">${icon("cancel-x", 14)}</button></div>
    <div class="mv-src mono">${esc(rel)}</div>
    <div class="mv-cols">
      <div class="mv-treebox">
        <input class="kbm-input mv-filter" placeholder="过滤目录…" spellcheck="false">
        <div class="mv-tree" tabindex="0"></div>
      </div>
      <div class="mv-side">
        <label class="kbm-label">文件名（不含 .md）
          <input class="kbm-input mv-name" value="${esc(fileName)}" spellcheck="false"></label>
        <div class="mv-dst-label">目标路径</div>
        <div class="mv-dst mono"></div>
        <div class="mv-hint">同名冲突、越界与未选目录会被拦截；移动后 FTS / 双链 / 向量索引自动级联更新，git 可追溯。</div>
      </div>
    </div>
    <div class="kbm-btns">
      <button class="iconbtn mv-cancel">取消</button>
      <button class="iconbtn primary mv-ok">移动</button>
    </div></div>`;
  document.body.appendChild(ov);

  const treeEl = ov.querySelector(".mv-tree");
  const nameEl = ov.querySelector(".mv-name");
  const dstEl = ov.querySelector(".mv-dst");
  const okBtn = ov.querySelector(".mv-ok");
  const filterEl = ov.querySelector(".mv-filter");
  const state = { dom: parts[0], sub: curSubId, open: new Set([parts[0]]) };

  function subDirOf(d, sid) { return sid === "_root" ? d.id : `${d.id}/${sid}`; }
  function refresh() {
    const dom = dirTree.find(d => d.id === state.dom);
    const sub = dom && dom.subs.find(s => s.id === state.sub);
    const nm = nameEl.value.trim();
    const invalidName = !nm || /[\\/:*?"<>|]/.test(nm);
    const same = !!(sub && `${subDirOf(dom, state.sub)}/${nm}.md` === rel);
    if (!sub) {
      dstEl.innerHTML = `<span class="mv-dst-empty">← 先在左侧选择目标目录</span>`;
    } else {
      const dir = subDirOf(dom, state.sub);
      dstEl.innerHTML = `<span class="mv-dst-dir">${esc(dir)}/</span><span class="mv-dst-file">${esc(nm || "（未命名）")}</span><span class="mv-dst-dir">.md</span>`;
    }
    dstEl.classList.toggle("mv-dst-same", same);
    okBtn.disabled = !sub || invalidName || same;
    okBtn.innerHTML = same ? "未变化" : `${icon("check", 13)} 移动`;
  }
  function renderTreeNodes() {
    const kw = filterEl.value.trim().toLowerCase();
    treeEl.innerHTML = dirTree.map(d => {
      if (kw && !(`${d.label}${d.id}`.toLowerCase().includes(kw) || d.subs.some(s => `${s.label}${s.id}`.toLowerCase().includes(kw)))) return "";
      const open = kw ? true : state.open.has(d.id);
      const subs = d.subs
        .filter(s => !kw || `${s.label}${s.id}`.toLowerCase().includes(kw) || `${d.label}${d.id}`.toLowerCase().includes(kw))
        .map(s => {
          const dir = subDirOf(d, s.id);
          const isCur = dir === srcDir;
          const sel = state.dom === d.id && state.sub === s.id;
          return `<div class="mv-node mv-sub ${sel ? "sel" : ""} ${isCur ? "cur" : ""}" data-dom="${esc(d.id)}" data-sub="${esc(s.id)}">
            <span class="mv-tw"></span><span class="mv-ic">${icon("file", 13)}</span>
            <span class="mv-lb">${esc(s.label)}</span><span class="mv-n">${s.n}</span></div>`;
        }).join("");
      return `<div class="mv-domrow ${state.open.has(d.id) ? "open" : ""}">
          <div class="mv-node mv-dom" data-dom="${esc(d.id)}">
            <span class="mv-tw">${open ? "▾" : "▸"}</span><span class="mv-ic">${icon("folder", 13)}</span>
            <span class="mv-lb">${esc(d.label)}</span><span class="mv-n">${d.n}</span></div>
          ${open ? subs : ""}
        </div>`;
    }).join("");
    refresh();
  }
  treeEl.addEventListener("click", e => {
    const node = e.target.closest(".mv-node");
    if (!node) return;
    const d = dirTree.find(x => x.id === node.dataset.dom);
    if (node.classList.contains("mv-dom")) {
      // 单击域头：展开/收起 + 选中该域“总览”子目录（与现有点击习惯一致）
      if (state.open.has(d.id) && state.dom === d.id) state.open.delete(d.id);
      else state.open.add(d.id);
      const first = d.subs.find(s => s.id === "_root") || d.subs[0];
      state.dom = d.id; state.sub = first.id;
    } else {
      state.dom = node.dataset.dom; state.sub = node.dataset.sub;
      state.open.add(node.dataset.dom);
    }
    renderTreeNodes();
  });
  // 键盘导航：↑↓ 移动高亮，←→ 折叠/展开，Enter 确认选中
  treeEl.addEventListener("keydown", e => {
    const nodes = [...treeEl.querySelectorAll(".mv-node:not(.mv-tw)")];
    const vis = nodes.filter(n => n.offsetParent !== null);
    if (!vis.length) return;
    let i = vis.findIndex(n => n.classList.contains("sel"));
    if (e.key === "ArrowDown") { e.preventDefault(); i = Math.min(i + 1, vis.length - 1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); i = Math.max(i - 1, 0); }
    else if (e.key === "ArrowRight" || e.key === "ArrowLeft" || e.key === "Enter") {
      e.preventDefault();
      const n = vis[i] || vis[0];
      if (n.classList.contains("mv-dom")) {
        if (e.key === "ArrowRight") state.open.add(n.dataset.dom);
        else if (e.key === "ArrowLeft") state.open.delete(n.dataset.dom);
        else { state.dom = n.dataset.dom; state.sub = (dirTree.find(d => d.id === n.dataset.dom).subs.find(s => s.id === "_root") || dirTree.find(d => d.id === n.dataset.dom).subs[0]).id; }
      } else { state.dom = n.dataset.dom; state.sub = n.dataset.sub; }
      renderTreeNodes();
      const cur = treeEl.querySelector(".mv-node.sel"); if (cur) cur.scrollIntoView({ block: "nearest" });
      return;
    } else return;
    vis.forEach(n => n.classList.remove("sel"));
    if (vis[i]) {
      const n = vis[i];
      if (n.classList.contains("mv-dom")) { state.dom = n.dataset.dom; state.sub = (dirTree.find(d => d.id === n.dataset.dom).subs.find(s => s.id === "_root") || dirTree.find(d => d.id === n.dataset.dom).subs[0]).id; }
      else { state.dom = n.dataset.dom; state.sub = n.dataset.sub; }
      renderTreeNodes();
      const cur = treeEl.querySelector(".mv-node.sel"); if (cur) cur.scrollIntoView({ block: "nearest" });
    }
  });
  filterEl.addEventListener("input", renderTreeNodes);
  nameEl.addEventListener("input", refresh);
  nameEl.addEventListener("keydown", e => { if (e.key === "Enter" && !okBtn.disabled) okBtn.click(); });

  const close = () => { ov.remove(); document.removeEventListener("keydown", onEsc); };
  const onEsc = e => { if (e.key === "Escape") close(); };
  document.addEventListener("keydown", onEsc);
  ov.querySelector(".mv-cancel").onclick = close;
    ov.querySelector(".mv-x").onclick = close;
  
  renderTreeNodes();
  nameEl.focus(); nameEl.select();

  okBtn.onclick = async () => {
    const nm = nameEl.value.trim();
    const dst = `${subDirOf(dirTree.find(d => d.id === state.dom), state.sub)}/${nm}.md`;
    okBtn.disabled = true; okBtn.textContent = "移动中…";
    const r = await fetch("/api/move", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ src: rel, dst }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.ok) { okBtn.disabled = false; okBtn.textContent = "移动"; toast("移动失败：" + (d.error || r.status)); return; }
    close();
    toast(`已移动至 <span class='mono'>${esc(d.dst)}</span> · 索引已级联更新`);
    // 问题9：不再 location.href 整页跳转。局部重渲染树/列表；
    // 当前正看的文档被移动时走客户端路由打开新位置。
    const movedCur = !!(DOC && DOC.rel === rel);
    await afterMutation();
    if (movedCur) await navigate(docUrl(d.dst), true);
  };
}

/* ---------- 拖拽移动：文档列表 → 左栏目录树 ---------- */
function wireDragMove() {
  const list = $("#doclist"), nav = $("#tree");
  if (!nav) return;
  // 需求 #11：列表列已移除，拖拽源改为树内文档（#doclist 存在时兼容旧模板）
  const dragSrc = list || nav;
  dragSrc.addEventListener("dragstart", e => {
    const a = e.target.closest(".doc");
    if (!a) return;
    const dom = a.dataset.dom || (CUR && CUR.domain);
    const sub = a.dataset.sub || (CUR && CUR.sub);
    e.dataTransfer.setData("text/kb-doc", docRelOf(dom, sub, a.dataset.name));
    e.dataTransfer.effectAllowed = "move";
    nav.classList.add("drop-armed");
  });
  dragSrc.addEventListener("dragend", () => {
    nav.classList.remove("drop-armed");
    nav.querySelectorAll(".drop-hint").forEach(x => x.classList.remove("drop-hint"));
  });
  ["dragover", "dragleave", "drop"].forEach(ev => nav.addEventListener(ev, e => {
    const t = e.target.closest(".sub, .dom-head");
    if (ev === "dragleave") { t && t.classList.remove("drop-hint"); return; }
    e.preventDefault(); // 允许 drop
    nav.querySelectorAll(".drop-hint").forEach(x => x.classList.remove("drop-hint"));
    if (!t) return;
    t.classList.add("drop-hint");
    if (ev === "drop") {
      t.classList.remove("drop-hint"); nav.classList.remove("drop-armed");
      const rel = e.dataTransfer.getData("text/kb-doc");
      if (!rel) return;
      const [dom, sub] = t.classList.contains("dom-head")
        ? [t.closest(".dom").dataset.dom, null] : [t.dataset.dom, t.dataset.sub];
      const d = (TREE || []).find(x => x.id === dom);
      const tgtSub = d && d.subs.find(s => s.id === (sub || "_root")) ? (sub || "_root") : (d && d.subs[0].id);
      const target = tgtSub || sub;
      if (!target) return;
      if (dom === CUR.domain && target === CUR.sub) { toast("已在该目录，无需移动"); return; }
      const nm = rel.split("/").pop().replace(/\.md$/, "");
      const dst = (target === "_root" ? dom : `${dom}/${target}`) + `/${nm}.md`;
      (async () => {
        const c = await kbModal({ title: "⇄ 拖拽移动",
          body: `将 <span class='mono'>${esc(rel)}</span><br>移动到 <span class='mono'>${esc(dst)}</span> ？<br>旁挂的备注 / 美化版会随行，索引自动级联。`,
          confirmText: "移动" });
        if (!c) return;
        const r = await fetch("/api/move", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ src: rel, dst }) });
        const dj = await r.json().catch(() => ({}));
        if (!r.ok || !dj.ok) { toast("移动失败：" + (dj.error || r.status)); return; }
        toast(`已移动至 <span class='mono'>${esc(dj.dst)}</span> · 索引已级联更新`);
        const movedCur = rel === (DOC && DOC.rel);
        await afterMutation();
        if (movedCur) await navigate(docUrl(dj.dst), true);
      })();
    }
  }));
}

/* 右键菜单 items（鼠标 contextmenu 与键盘 ContextMenu/Shift+F10 共用，问题13）
   第三轮 #7 重排：信息/复制在前，分隔线，移动/删除在后，危险项置底。 */
function ctxDocItems(docA) {
  const name = docA.dataset.name;
  // 需求 #11：树内联文档自带 data-dom/data-sub；列表文档回退 CUR
  const domain = docA.dataset.dom || (CUR && CUR.domain);
  const sub = docA.dataset.sub || (CUR && CUR.sub);
  const rel = docRelOf(domain, sub, name);
  return [
    { icon: icon("trend"), label: "统计信息", fn: () => showStats(rel) },
    "-",
    { icon: icon("copy"), label: "复制 Markdown 原文", fn: async () => {
        const r = await fetch(rawUrl(rel));
        if (!r.ok) { toast("读取原文失败：" + r.status); return; }
        copyText(await r.text(), "已复制 Markdown 原文");
      } },
    { icon: icon("copy-link"), label: "复制站内链接", fn: () => copyText(location.origin + docUrl(rel.replace(/\.md$/, "")), "已复制站内链接") },
    { icon: icon("copy-path"), label: "复制相对路径", fn: () => copyText(rel, "已复制路径") },
    "-",
    { icon: icon("swap"), label: "移动 / 重命名…", fn: () => moveDocPrompt(rel) },
    { icon: icon("trash"), label: "删除…", danger: true, fn: async () => {
        const s = findSub(CUR.domain, CUR.sub);
        const d = s && s.docs.find(x => x.name === name);
        if (!d) { toast("文档不在当前列表"); return; }
        const c = await kbModal({
          title: icon("trash", 16) + " 删除这篇文档？",
          body: `《<b>${esc(d.title)}</b>》及其旁挂美化版 / 备注将整体移入 <span class="mono">content/_trash/</span>（软删除，可找回）。`,
          danger: true, confirmText: "移入回收站", cancelText: "取消",
        });
        if (!c) return;
        const r = await fetch("/api/delete", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: rel }) });
        if (!r.ok) {
          let err = ""; try { err = (await r.json()).error || ""; } catch (e) {}
          // 第三轮 #10：404 = 文件已不在（早已删除/路径陈旧）→ 按「已删除」收尾，不再报错卡死
          if (r.status === 404) { toast("文件已不存在，列表已同步"); await ctxDiscardDoc(rel, d.title, false); return; }
          toast("删除失败：" + (err || r.status)); return;
        }
        // 第三轮 #9：删除的是当前打开的文档时，同步清理正文区（与 crumb 版 deleteDoc 同一套收尾）
        if (DOC && DOC.rel === rel) await ctxDiscardDoc(rel, d.title, true);
        else { toast("已移入回收站"); await afterMutation(); }
      } },
  ];
}
/* 第三轮 #9/#10：右键删除后的正文区收尾（从 deleteDoc 提取的共用逻辑）：
   局部更新树/列表 → 关编辑器 → 清 DOC → 正文区展示「已移入回收站」占位。
   deletedJustNow=false 表示 404 自愈（文件早已不在），文案改为「此前已删除」。 */
async function ctxDiscardDoc(rel, title, deletedJustNow) {
  const deletedTitle = title || rel;
  const s = findSub(CUR ? CUR.domain : "", CUR ? CUR.sub : "");
  const nm = rel.split("/").pop();
  if (s) {
    s.docs = s.docs.filter(x => x.name !== nm);
    s.n = s.docs.length;
    const d = TREE.find(x => x.id === (CUR && CUR.domain));
    if (d) d.n = d.subs.reduce((a, x) => a + x.n, 0);
    persistTree();
    renderTree();
    renderDocList(s.docs, s.label, null);
  }
  closeEditor();
  DOC = null;
  $("#article").innerHTML = `<div class="a-kicker">已删除</div>
    <h1 class="a-title">文档已移入回收站</h1>
    <div class="a-rule"></div>
    <div class="a-body"><p>《${esc(deletedTitle)}》及其美化版、备注已${deletedJustNow ? "" : "此前"}移入 <code>content/_trash/</code>，git 历史亦可找回。</p>
    <p>从左侧选择其他文档继续阅读。</p></div>`;
  $("#crumb").innerHTML = `<b>已删除</b><span class="sep">·</span>${esc(deletedTitle)}`;
  await afterMutation();
}
/* 新建子目录（需求 #4）：域下二级目录，或子域下嵌套目录。
   写 taxonomy.json 显示名（可留空走目录 id），空目录暂不入树，建完引导去新建文档。 */
async function promptNewSubdir(baseDomain, parentSub) {
  const parent = parentSub ? `${baseDomain}/${parentSub}` : "";
  const res = await kbModal({
    title: "新增目录",
    body: parent
      ? `将在 <span class='mono'>${esc(parent)}/</span> 下新建子目录。`
      : `将在 <span class='mono'>${esc(baseDomain)}/</span> 下新建二级目录（左侧分类树的一级条目）。`,
    inputs: [
      { key: "nm", label: "目录名（英文 id，如 rag-notes）", placeholder: "my-subdir" },
      { key: "lb", label: "显示名（可留空，默认同目录名）", placeholder: "我的笔记" },
    ],
    confirmText: "创建",
  });
  if (!res || !res.nm) return;
  const r = await fetch("/api/mkdir", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain: baseDomain, parent, name: res.nm.trim(), label: (res.lb || "").trim() }) });
  const d = await r.json().catch(() => ({}));
  if (!r.ok || !d.ok) { toast("创建失败：" + (d.error || r.status)); return; }
  await afterMutation();
  toast(`已创建 <span class='mono'>${esc(d.created)}</span> · 左侧树已同步，右键它可新建文档`);
}
function ctxSubItems(subA) {
  const dom = subA.dataset.dom, sub = subA.dataset.sub;
  const base = sub === "_root" ? dom : `${dom}/${sub}`;
  // 第三轮 #7：动词优先、危险置底；_root（域根散文件区）不给重命名/删除
  const items = [
    { icon: icon("new-file"), label: "在此新建文档…", fn: async () => {
        const res = await kbModal({
          title: "新建文档",
          body: `将在 <span class='mono'>${esc(base)}/</span> 下创建 Markdown 文件，首行自动写入标题。`,
          inputs: [{ key: "nm", label: "文件名（不含 .md）", placeholder: "示例：RAG 切块策略" }],
          confirmText: "创建",
        });
        if (!res || !res.nm) return;
        const nm = res.nm;
        const rel = `${base}/${nm}.md`;
        const r = await fetch("/api/save", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: rel, content: `# ${nm}\n\n` }) });
        if (r.ok) {
          await afterMutation();
          await navigate(docUrl(rel), true); // 问题9：客户端打开新文档，不整页跳转
        }
        else toast("创建失败：" + r.status);
      } },
    { icon: icon("plus-circle"), label: "新建子目录…", fn: () => promptNewSubdir(dom, sub === "_root" ? "" : sub) },
  ];
  if (sub !== "_root") {
    items.push(
      "-",
      { icon: icon("swap"), label: "重命名目录…", fn: () => renameSubPrompt(dom, sub) },
      { icon: icon("trash"), label: "删除目录…", danger: true, fn: () => rmdirPrompt(dom, sub) }
    );
  }
  items.push("-", { icon: icon("copy-path"), label: "复制路径", fn: () => copyText(base, "已复制路径") });
  return items;
}
/* 域级右键（第三轮 #7 契约）：新增二级目录 + 复制域名；
   #3：data-dom 挂在 .dom 父元素上，domA（.dom-head）需 closest 向上取。 */
function ctxDomItems(domA) {
  const host = domA.closest(".dom") || domA;
  const dom = host.dataset.dom || domA.dataset.dom;
  return [
    { icon: icon("plus-circle"), label: "新增二级目录…", fn: () => promptNewSubdir(dom, "") },
    "-",
    { icon: icon("copy"), label: "复制域名", fn: () => copyText(dom, "已复制域名") },
  ];
}
/* 第三轮 #8：删除目录（仅限空目录）。先确认；非空由后端 400 提示先清空。 */
async function rmdirPrompt(dom, sub) {
  const c = await kbModal({
    title: icon("trash", 16) + " 删除目录？",
    body: `将删除 <span class='mono'>${esc(dom)}/${esc(sub)}/</span>。仅限<b>空目录</b>：若里面还有文档，请先删除或移走，否则会被拒绝。`,
    danger: true, confirmText: "删除目录", cancelText: "取消",
  });
  if (!c) return;
  const r = await fetch("/api/rmdir", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain: dom, sub }) });
  const d = await r.json().catch(() => ({}));
  if (!r.ok || !d.ok) { toast("删除目录失败：" + (d.error || r.status)); return; }
  toast(`已删除目录 <span class='mono'>${esc(dom)}/${esc(sub)}</span>`);
  // 删除的若正是当前浏览的目录 → 回首页，避免右侧残留（第三轮 #9 同源问题）
  if (CUR && CUR.domain === dom && (CUR.sub === sub || `${CUR.domain}/${CUR.sub}` === `${dom}/${sub}`)) {
    invalidate("all"); location.href = "/"; return;
  }
  await afterMutation();
}
/* 第三轮 #1 目录重命名：/api/rename-sub（store.rename_sub 修复后经 Web 暴露）。 */
async function renameSubPrompt(dom, sub) {
  const res = await kbModal({
    title: "重命名目录",
    body: `重命名 <span class='mono'>${esc(dom)}/${esc(sub)}/</span>（文档与索引自动级联）。`,
    inputs: [{ key: "nm", label: "新目录名（英文 id）", value: sub, placeholder: "new-id" }],
    confirmText: "重命名",
  });
  if (!res || !res.nm) return;
  const nn = res.nm.trim();
  if (nn === sub) return;
  const r = await fetch("/api/rename-sub", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain: dom, sub, new: nn }) });
  const d = await r.json().catch(() => ({}));
  if (!r.ok || !d.ok) { toast("重命名失败：" + (d.error || r.status)); return; }
  toast(`已重命名为 <span class='mono'>${esc(dom)}/${esc(nn)}</span> · 索引已级联更新`);
  if (CUR && CUR.domain === dom && CUR.sub === sub) {
    invalidate("all"); location.href = `/browse/${encodeURIComponent(dom)}/${encodeURIComponent(nn)}`; return;
  }
  await afterMutation();
}
/* 问题13：键盘唤起——文档列表项或树子域获得焦点后按 Menu 键 / Shift+F10，
   菜单锚定在该元素下方（触摸设备右键不可达的键盘补偿路径） */
document.addEventListener("keydown", e => {
  if (!WORKBENCH || (e.key !== "ContextMenu" && !(e.shiftKey && e.key === "F10"))) return;
  const a = e.target.closest && (e.target.closest("#doclist .doc") || e.target.closest("#tree .doc") || e.target.closest("#tree .sub") || e.target.closest("#tree .dom-head"));
  if (!a) return;
  e.preventDefault();
  const r = a.getBoundingClientRect();
  const items = a.classList.contains("doc") ? ctxDocItems(a)
    : a.classList.contains("dom-head") ? ctxDomItems(a) : ctxSubItems(a);
  openCtxMenu(r.left + 8, r.bottom + 2, items);
});

document.addEventListener("contextmenu", e => {
  // 工作台（阅读页）：文档列表 / 分类树（含树内联文档）/ 域头的右键
  if (WORKBENCH) {
    const docA = e.target.closest("#doclist .doc") || e.target.closest("#tree .doc");
    if (docA) { e.preventDefault(); openCtxMenu(e.clientX, e.clientY, ctxDocItems(docA)); return; }
    const subA = e.target.closest("#tree .sub");
    if (subA) { e.preventDefault(); openCtxMenu(e.clientX, e.clientY, ctxSubItems(subA)); return; }
    const domA = e.target.closest("#tree .dom-head");
    if (domA) { e.preventDefault(); openCtxMenu(e.clientX, e.clientY, ctxDomItems(domA)); return; }
    return;
  }
  // 总览页：领域卡片 / 最近更新行的右键（此前被 WORKBENCH 门禁整体挡掉）
  const dcard = e.target.closest("#view-home .dcard");
  if (dcard) {
    e.preventDefault();
    const m = (dcard.getAttribute("href") || "").match(/^\/browse\/([^/]+)\/([^/]+)/);
    if (!m) return;
    const [_, dom, firstSub] = m;
    openCtxMenu(e.clientX, e.clientY, [
      { icon: icon("chart"), label: "统计信息", fn: () => showSubStats(dom, firstSub) },
      { icon: icon("folder"), label: "进入该目录", fn: () => { location.href = dcard.getAttribute("href"); } },
      { icon: icon("copy-path"), label: "复制目录路径", fn: () => copyText(dom, "已复制路径") },
    ]);
    return;
  }
  const rrow = e.target.closest("#view-home .rrow");
  if (rrow) {
    e.preventDefault();
    const href = rrow.getAttribute("href") || "";
    const rp = (rrow.querySelector(".rp") || {}).textContent || "";
    const dm = href.match(/^\/doc\/(.+)$/);
    if (!dm) { copyText(rp, "已复制路径"); return; } // _inbox 外链行：只给路径
    const rel = decodeURIComponent(dm[1]) + ".md";
    openCtxMenu(e.clientX, e.clientY, [
      { icon: icon("trend"), label: "统计信息", fn: () => showStats(rel) },
      { icon: icon("copy"), label: "复制 Markdown 原文", fn: async () => {
          const r = await fetch(rawUrl(rel));
          if (!r.ok) { toast("读取原文失败：" + r.status); return; }
          copyText(await r.text(), "已复制 Markdown 原文");
        } },
      { icon: icon("swap"), label: "移动 / 重命名…", fn: () => moveDocPrompt(rel) },
    ]);
  }
});

/* ---------- 阅读统计埋点（v1：open / 60s 心跳 / finish，全部本地） ---------- */
let READ_TRACK = { path: null, lastOpenSent: 0, minutes: 0, timer: null };

function trackEvent(event, seconds) {
  if (!READ_TRACK.path) return;
  fetch("/api/track", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: READ_TRACK.path, event, seconds }) }).catch(() => {});
}

function startReadTracking() {
  clearInterval(READ_TRACK.timer);
  READ_TRACK.minutes = 0;
  READ_TRACK.timer = setInterval(() => {
    // 页面不可见不计时长；每满 1 分钟上报一次增量
    if (document.visibilityState !== "visible" || !READ_TRACK.path) return;
    READ_TRACK.minutes += 1;
    trackEvent("read_minute", 60);
  }, 60000);
}

function setTrackingDoc(rel) {
  if (READ_TRACK.path === rel) return; // 同文档刷新不重复 open
  READ_TRACK.path = rel;
  READ_TRACK.minutes = 0;
  const now = Date.now();
  if (rel && now - READ_TRACK.lastOpenSent > 600000) { // 10 分钟同文档去重（双保险）
    READ_TRACK.lastOpenSent = now;
    trackEvent("open", 0);
  }
}

/* ---------- 快捷键与搜索 ---------- */
/* 全局 keydown 统一交给 kb-core.js 的 KB.keys 分发器（需求7）。
   kb-core.js 在本文件之前 defer 加载；若它没起来，退回 v18 的原始行为，
   保证 `/` 聚焦搜索、Escape 关编辑器不丢。 */
document.addEventListener("keydown", e => {
  if (window.KB && KB.keys && typeof KB.keys.handle === "function") {
    if (!e.__kbHandled) { e.__kbHandled = true; KB.keys.handle(e); } // kb-core 已在捕获阶段处理过就不再重复
    return;
  }
  if (e.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) { e.preventDefault(); const q = $("#q"); q && q.focus(); }
  if (e.key === "Escape") {
    // 沉浸模式优先退出（快赢）：编辑器内 Esc 仍归 dirty guard 管辖
    const mMain = document.querySelector("main");
    if (mMain && mMain.classList.contains("immersive") && !editorIsOpen()) {
      mMain.classList.remove("immersive");
      setPanel("left", false); setPanel("rail", false);
      toast("已退出沉浸模式");
    } else { tryCloseEditor(); }
  }
  // 快赢：沉浸阅读模式 —— W 键一键收起两侧栏只留正文，再按恢复（编辑器内不劫持）
  if ((e.key === "w" || e.key === "W") && !e.ctrlKey && !e.metaKey && !e.altKey
      && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)
      && !editorIsOpen() && WORKBENCH) {
    e.preventDefault();
    const m = document.querySelector("main");
    const immersive = m.classList.toggle("immersive");
    setPanel("left", immersive);
    setPanel("rail", immersive);
    toast(immersive ? "沉浸模式 · 按 W 或 Esc 退出" : "已退出沉浸模式");
  }
});
const q = $("#q");
if (q) q.addEventListener("keydown", e => {
  if (e.key === "Enter" && q.value.trim()) location.href = "/search?q=" + encodeURIComponent(q.value.trim());
});

/* ---------- 需求 #9：搜索框空态下拉 —— 点击空的搜索框展示探索面板 ----------
   数据源：命令面板索引（术语/文档/子域 Top）+ 固定快捷入口 + 最近更新。 */
/* ---------- L2 就地搜索浮层（阶段5 STEP2 授权接线） ----------
   旧 searchdrop 下拉退役：快速前往/探索语料并入浮层空态。
   钩子保留：#searchbox #q（触发器 + `/` 键）；Esc 关闭；无 backdrop 关闭（反模式纪律）。 */
const SO = {
  ov: null, box: null, input: null, body: null, stat: null,
  engine: "fts", scope: "", tag: "", timer: null, seq: 0, lastQ: "",
  esc2: s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c])),
};

function soOpen() {
  if (!SO.ov) SO.ov = document.getElementById("kb-search-ov");
  if (!SO.ov) return;
  SO.box = SO.box || SO.ov.querySelector(".kb-search-box");
  SO.input = SO.input || document.getElementById("kb-so-q");
  SO.body = SO.body || document.getElementById("kb-so-body");
  SO.stat = SO.stat || document.getElementById("kb-so-stat");
  SO.ov.hidden = false;
  SO.ov.classList.add("show");
  if (!SO.ov.dataset.wired) {
    soWire();
    SO.ov.dataset.wired = "1";
  }
  SO.body.innerHTML = soEmptyState();
  setTimeout(() => { if (SO.input) SO.input.focus(); }, 0);
  // 打开即带出最近查询（纯前端 localStorage，无编造）
  soRenderRecent();
}

function soClose() {
  if (!SO.ov) return;
  SO.ov.classList.remove("show");
  SO.ov.hidden = true;
  if (q) { try { q.blur(); } catch (e) {} }
}

function soWire() {
  SO.ov.addEventListener("keydown", e => {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); soClose(); }
    else if (e.key === "Enter" && e.shiftKey) { e.preventDefault(); soToL3(); }
    else if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); soOpenFirst(); }
    else if (e.key === "F2") { e.preventDefault(); soSetEngine("fts"); }
    else if (e.key === "F3") { e.preventDefault(); soSetEngine("semantic"); }
    e.stopPropagation();
  });
  SO.ov.querySelectorAll(".kb-eng-chip").forEach(ch => {
    ch.addEventListener("click", () => soSetEngine(ch.dataset.eng));
  });
  SO.ov.querySelectorAll(".kb-scope-chip").forEach(ch => {
    ch.addEventListener("click", () => {
      const v = ch.dataset.scope || "";
      SO.scope = v.startsWith("fav") || v.startsWith("unmastered") ? "" : v;
      SO.tag = "";
      SO.ov.querySelectorAll(".kb-scope-chip").forEach(x => x.classList.toggle("on", x === ch));
      soRun();
    });
  });
  if (SO.input) SO.input.addEventListener("input", () => {
    clearTimeout(SO.timer);
    SO.timer = setTimeout(soRun, 240);
  });
}

function soSetEngine(eng) {
  if (!["hybrid", "fts", "semantic"].includes(eng)) return;
  SO.engine = eng;
  SO.ov.querySelectorAll(".kb-eng-chip").forEach(ch => {
    const on = ch.dataset.eng === eng;
    ch.classList.toggle("on", on);
    ch.setAttribute("aria-pressed", on ? "true" : "false");
  });
  soRun();
}

function soEmptyState() {
  const shortcuts = [
    { icon: "i-inbox-tray", label: "收件箱（待归档）", href: "/inbox" },
    { icon: "i-favorite-heart", label: "我的收藏", href: "/favorites" },
    { icon: "i-tag-outline", label: "标签管理", href: "/tags" },
    { icon: "i-stats-chart", label: "月度统计", href: "/stats" },
    { icon: "i-sort-alpha", label: "术语门户（A-Z）", href: "/glossary" },
    { icon: "i-clock-heartbeat", label: "间隔复习", href: "/review" },
  ];
  return `<div class="kb-sr-group">快速前往</div>
    <div class="kb-sdrop-grid">${shortcuts.map(s =>
      `<a class="kb-sdrop-item" href="${s.href}"><svg class="i i-14"><use href="#${s.icon}"/></svg>${SO.esc2(s.label)}</a>`).join("")}</div>
    <div class="kb-sr-group">搜索语法</div>
    <div style="font:400 12px/1.8 var(--f-body);color:var(--faint);padding:2px 2px 8px">
      直接输入 = 混合检索 · <span class="mono">? 问题</span> = 语义 · <span class="mono">Enter</span> 打开首条 · <span class="mono">Shift+Enter</span> 结果页</div>`;
}

function soRenderRecent() {
  try {
    const list = JSON.parse(localStorage.getItem("kb-recent-queries") || "[]");
    if (!Array.isArray(list) || !list.length) return;
    const body = document.getElementById("kb-so-body");
    if (!body || body.dataset.hasResults === "1") return;
    const div = document.createElement("div");
    div.innerHTML = `<div class="kb-sr-group">最近查询<span class="n">本地</span></div>` +
      list.slice(0, 5).map(qs => `<div class="kb-sr"><div class="sr-top"><span class="idx">↺</span><span class="path">${SO.esc2(qs)}</span></div></div>`).join("");
    body.insertBefore(div, body.firstChild);
  } catch (e) {}
}

function soRemember(qstr) {
  try {
    let list = JSON.parse(localStorage.getItem("kb-recent-queries") || "[]");
    list = [qstr, ...list.filter(x => x !== qstr)].slice(0, 8);
    localStorage.setItem("kb-recent-queries", JSON.stringify(list));
  } catch (e) {}
}

function soRun() {
  const qstr = (SO.input ? SO.input.value : "").trim();
  SO.lastQ = qstr;
  if (!qstr) { SO.body.innerHTML = soEmptyState(); soRenderRecent(); if (SO.stat) SO.stat.textContent = "— · 输入以检索"; return; }
  const seq = ++SO.seq;
  const eng = SO.engine === "semantic" ? "semantic" : SO.engine;
  const pfx = SO.engine === "semantic" && !qstr.startsWith("?") ? "?" + qstr : qstr;
  const params = new URLSearchParams({ q: pfx, engine: eng, limit: "12" });
  if (SO.scope) params.set("domain", SO.scope);
  fetch("/api/search?" + params.toString()).then(r => r.json()).then(j => {
    if (seq !== SO.seq) return; // 旧响应丢弃
    soRenderResults(j, qstr);
  }).catch(() => {
    if (seq !== SO.seq) return;
    SO.body.innerHTML = `<div class="kb-sr-group">检索失败</div><div style="font:400 12.5px/1.7 var(--f-body);color:var(--faint);padding:8px 2px">网络或索引异常，稍后重试。</div>`;
  });
}

const SO_GROUP_TITLES = { exact: "精确命中", prefix: "标题前缀", contains: "标题包含", tag: "标签命中", title: "标题命中", body: "正文命中", semantic: "语义相近" };

function soRenderResults(j, qstr) {
  soRemember(qstr);
  const all = (j.exact || []).concat(j.hits || []);
  const hybrid = j.mode === "hybrid";
  const groups = {};
  all.forEach(it => {
    const g = hybrid ? (it.match || "body") : (it.match === "semantic" ? "semantic" : (it.match || "body"));
    (groups[g] = groups[g] || []).push(it);
  });
  let html = "";
  let idx = 0;
  Object.keys(groups).forEach(g => {
    const arr = groups[g];
    html += `<div class="kb-sr-group">${SO.esc2(SO_GROUP_TITLES[g] || g)}<span class="n">${arr.length}</span></div>`;
    arr.slice(0, 6).forEach(it => {
      idx += 1;
      const num = String(idx).padStart(2, "0");
      const hl = s => SO.esc2(s || "").replace(/&lt;mark&gt;/g, "<mark>").replace(/&lt;\/mark&gt;/g, "</mark>");
      let scoreHtml = "";
      if (hybrid && it.score_fts != null && it.score_semantic != null) {
        const wf = Math.max(2, Math.min(100, Math.round(parseFloat(it.score_fts) * 100)));
        const ws = Math.max(2, Math.min(100, Math.round(parseFloat(it.score_semantic) * 100)));
        scoreHtml = `<span class="sr-scores" title="FTS 与语义双路归一化分">
          <span class="sc sc-fts" style="--w:${wf}%"><i></i><b>${SO.esc2(String(it.score_fts))}</b></span>
          <span class="sc sc-sem" style="--w:${ws}%"><i></i><b>${SO.esc2(String(it.score_semantic))}</b></span></span>`;
      } else {
        scoreHtml = `<span class="score">${SO.esc2(it.score_label || "")}</span>`;
      }
      const pos = (it.hit_in_snippet != null && it.hit_in_snippet >= 0) ? ` · 命中位 ${it.hit_in_snippet}` : "";
      html += `<a class="kb-sr" href="${it.url || docUrl(it.path || "")}" data-path="${SO.esc2(it.path || "")}">
        <div class="sr-top"><span class="idx">${num}</span>
          <span class="path">${SO.esc2(it.path || "")}${SO.esc2(pos)}</span>${scoreHtml}</div>
        <div class="sr-title">${hl(it.title || "")}</div>
        <div class="sr-snippet">${(it.snippet || "")}</div>
        ${(it.tags && it.tags.length) ? `<div class="kb-res-tags">${it.tags.slice(0, 4).map(tg => `<span class="kb-tag mute">${SO.esc2(tg)}</span>`).join("")}</div>` : ""}
      </a>`;
    });
  });
  SO.body.innerHTML = html || `<div class="kb-sr-group">无结果</div><div style="font:400 12.5px/1.7 var(--f-body);color:var(--faint);padding:8px 2px">换个关键词，或 <span class="mono">Shift+Enter</span> 进结果页。</div>`;
  SO.body.dataset.hasResults = all.length ? "1" : "0";
  if (SO.stat) {
    const e = j.engines || {};
    const parts = [];
    if (e.fts_ms != null) parts.push("FTS " + e.fts_ms + "ms");
    if (e.rag_ms != null) parts.push("RAG " + e.rag_ms + "ms");
    SO.stat.textContent = (j.mode || "—") + " · " + (parts.join(" + ") || j.took_ms + "ms") + " · " + j.total + " 条";
  }
}

function soOpenFirst() {
  const first = SO.body.querySelector("a.kb-sr[href]");
  if (first && !first.href.endsWith("#")) location.href = first.href;
}

function soToL3() {
  const qstr = (SO.input ? SO.input.value : "").trim();
  if (!qstr) return;
  const eng = SO.engine;
  const pre = eng === "semantic" && !qstr.startsWith("?") ? "?" : "";
  location.href = "/search?q=" + encodeURIComponent(pre + qstr) + (eng !== "hybrid" ? "&engine=" + eng : "");
}

function initSearchDrop() {
  if (!q || q.dataset.sdrop) return;
  q.dataset.sdrop = "1";
  // L1 触发器（阶段5 STEP2）：点击容器任意位置（图标/文案/键帽）开 L2；
  // Tab 聚焦 input 也开；Esc 关闭在浮层内处理。旧 searchdrop 下拉退役。
  const sbEl = document.getElementById("searchbox");
  if (sbEl) sbEl.addEventListener("click", () => soOpen());
  q.addEventListener("focus", () => { if (!q.value.trim()) soOpen(); });
}
initSearchDrop();

/* ---------- 启动 ---------- */
const docData = document.getElementById("doc-data");
if (docData) {
  try {
    DOC = JSON.parse(docData.textContent);
    CUR = { domain: DOC.domain, sub: DOC.sub, name: DOC.name };
    renderArticle();
    renderCrumb();
    renderInfo();
    renderNotes();
    setTrackingDoc(DOC.rel);
    startReadTracking();
  } catch (e) { console.error("初始渲染失败", e); }
}
if (WORKBENCH) wireDragMove();
loadTree().then(() => {
  renderTree();
});
