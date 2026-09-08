/* 知库 reader 前端：主题、面板折叠、客户端路由、正文渲染、编辑/备注/收藏/删除、双链、快捷键 */
window.APP_JS_VERSION = 16;

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const toast = m => { const t = $("#toast"); t.innerHTML = m; t.classList.add("show"); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 2600); };

/* ---------- 主题 ---------- */
function applyTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  const b = $("#theme-btn"); if (b) b.textContent = t === "dark" ? "☾" : "☀";
  window.dispatchEvent(new CustomEvent("theme-changed", { detail: t }));
  try { localStorage.setItem("kb-theme", t); } catch (e) {}
}
const themeBtn = $("#theme-btn");
if (themeBtn) themeBtn.onclick = () => {
  const now = document.documentElement.getAttribute("data-theme");
  applyTheme(now === "dark" ? "light" : "dark");
  if (window.DOC && document.querySelector("#article .mermaid")) renderArticle();
};
try { const saved = localStorage.getItem("kb-theme"); if (saved) applyTheme(saved); } catch (e) {}

/* ---------- 面板折叠（workbench） ---------- */
function setPanel(which, off) {
  const pid = which === "left" ? "p-left" : "p-list";
  const cls = which === "left" ? "left-off" : "list-off";
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
  $$(".rtab").forEach(t => t.classList.remove("active")); el.classList.add("active");
  $$(".rpane").forEach(p => p.classList.remove("active")); $("#pane-" + id).classList.add("active");
  if (id === "links") loadLinks();
}

/* ---------- 正文渲染 ---------- */
let DOC = null;
let CUR = null; // {domain, sub, name}

function renderArticle() {
  const el = $("#article");
  if (!el || !DOC) return;
  if (DOC.is_html) {
    el.innerHTML = `<div class="a-kicker">HTML 文档</div>
      <h1 class="a-title">${esc(DOC.title)}</h1>
      <div class="a-rule"></div>
      <div class="a-body"><p>这是整页 HTML 文档，直通渲染以保留其自带样式。</p>
      <p><a class="iconbtn primary" href="/raw/${esc(DOC.rel)}" target="_blank">在新标签页打开原页面 ↗</a></p></div>`;
  } else {
    const chips = [
      `<span class="chip acc">${esc(DOC.source_label)}</span>`,
      DOC.fm.source_path ? `<span class="chip">${esc(DOC.fm.source_path)}</span>` : "",
      DOC.fm.collected ? `<span class="chip">${esc(DOC.fm.collected)} 收录</span>` : "",
      (DOC.fm.tags && DOC.fm.tags.length)
        ? DOC.fm.tags.map(t => `<span class="chip acc">${esc(t)}</span>`).join("")
        : `<span class="chip warn">tags 未打标</span>`,
    ].join("");
    el.innerHTML = `<div class="a-kicker">${esc(DOC.domain_label)} / ${esc(DOC.sub_label)}</div>
      <h1 class="a-title">${esc(DOC.title)}</h1>
      <div class="a-chips">${chips}</div>
      <div class="a-rule"></div>
      <div class="a-body">${DOMPurify.sanitize(marked.parse(DOC.md), { FORBID_TAGS: ['style', 'iframe', 'form', 'script'], ADD_ATTR: ['target'] })}</div>`;
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
      window.mermaid.run({ nodes: el.querySelectorAll("div.mermaid") }).catch(() => {});
    }).catch(() => toast("mermaid 库加载失败，图示暂以代码块显示"));
  }
  if (window.hljs) el.querySelectorAll("pre code:not(.language-mermaid)").forEach(b => {
    try { hljs.highlightElement(b); } catch (e) {}
  });
  buildToc();
}

function buildToc() {
  const pane = $("#pane-toc"); if (!pane) return;
  const heads = $$("#article .a-body h1, #article .a-body h2, #article .a-body h3");
  if (!heads.length) { pane.innerHTML = `<div style="font-size:12.5px;color:var(--faint);padding:6px 2px">本文无小节标题。</div>`; return; }
  pane.innerHTML = "";
  const pairs = [];
  heads.forEach((h, i) => {
    h.id = h.id || ("sec-" + i);
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
  function tocOn(a) { $$("#pane-toc a").forEach(x => x.classList.remove("on")); a.classList.add("on"); }
}

/* ---------- 分类树 / 文档列表（客户端渲染） ---------- */
function renderTree() {
  const nav = $("#tree"); if (!nav || !TREE) return;
  nav.innerHTML = TREE.map(d => `
   <div class="dom ${CUR && CUR.domain === d.id ? "open" : ""}" data-dom="${esc(d.id)}">
    <a class="dom-head ${CUR && CUR.domain === d.id ? "active" : ""}" href="/browse/${d.id}/${d.subs[0].id}">
     <span class="dom-glyph" style="--dh:${HUES[d.id] || 158}"><svg><use href="#i-${d.id}"/></svg></span>
     <span class="dom-name">${esc(d.label)}</span><span class="dom-n">${d.n}</span>
    </a>
    <div class="subs">${d.subs.map(s => `
      <a class="sub ${CUR && CUR.domain === d.id && CUR.sub === s.id ? "active" : ""}" data-dom="${esc(d.id)}" data-sub="${esc(s.id)}" href="/browse/${d.id}/${s.id}">${esc(s.label)}<span class="n">${s.n}</span></a>`).join("")}
    </div>
   </div>`).join("");
}

function renderDocList(docs, subLabel, activeName) {
  const title = $("#list-title");
  if (title) title.innerHTML = `${esc(subLabel)}<span class="cnt">${docs.length}</span><button class="fold" onclick="togglePanel('list')" title="收起列表"><svg><use href="#i-fold-l"/></svg></button>`;
  const list = $("#doclist"); if (!list) return;
  list.innerHTML = docs.map(d => `
    <a class="doc ${d.name === activeName ? "active" : ""}" data-name="${esc(d.name)}" href="/doc/${CUR.domain}/${CUR.sub}/${d.name.split("/").map(encodeURIComponent).join("/")}">
      <div class="doc-t">${d.has_html ? '<span class="star">◈</span>' : ""}${esc(d.title)}</div>
      <div class="doc-meta">
        ${(d.tags && d.tags.length) ? d.tags.map(t => `<span class="mini tag">${esc(t)}</span>`).join("") : `<span class="mini untag">未打标</span>`}
        ${d.has_html ? `<span class="mini html">美化版</span>` : ""}
        ${d.is_html ? `<span class="mini html">HTML</span>` : ""}
      </div>
    </a>`).join("") || `<div style="padding:20px;color:var(--faint);font-size:13px">无匹配文档</div>`;
}

function renderCrumb() {
  const crumb = $("#crumb"); if (!crumb || !DOC) return;
  const dirs = DOC.rel.split("/").slice(0, -1).join("/");
  crumb.innerHTML = `content<b>/</b>${esc(dirs)}<span class="sep">·</span><b>${esc(DOC.title)}</b><span class="spacer"></span>
    ${DOC.has_html ? `<button class="iconbtn" onclick="openPretty()" title="弹窗打开整页美化版">◈ 美化版</button>` : ""}
    ${!DOC.is_html ? `<button class="iconbtn" onclick="openEditor()">✎ 编辑</button>
    <button class="iconbtn" onclick="deleteDoc()" title="移入 content/_trash/">🗑 删除</button>` : ""}
    <button class="iconbtn primary ${DOC.favorite ? "faved" : ""}" id="fav-btn" onclick="toggleFav()">${DOC.favorite ? "★ 已收藏" : "☆ 收藏"}</button>`;
}

function renderInfo() {
  const pane = $("#pane-info"); if (!pane || !DOC) return;
  pane.innerHTML = (DOC.info_rows || []).map(([k, v]) =>
    `<div class="meta-row"><span class="k">${esc(k)}</span><span class="v">${esc(v)}</span></div>`).join("")
    + `<div class="meta-row"><span class="k">版本</span><span class="v">git 全程可追溯</span></div>`;
}

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

async function navigate(url, push) {
  if (!WORKBENCH) {
    // 非阅读页（总览/搜索/收藏）：同类 URL 原地不动，避免 back 触发重复刷新
    if (location.pathname + location.search !== url) location.href = url;
    return;
  }
  closeEditor();
  const path = url.split("?")[0];
  const segs = path.split("/").filter(Boolean).map(decodeURIComponent);
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
    const docUrl = `/doc/${segs[1]}/${segs[2]}/${first.name.split("/").map(encodeURIComponent).join("/")}`;
    if (push) history.pushState({}, "", url);
    await navigate(docUrl, false);
    return;
  }
  location.href = url; // 其余页面（总览/搜索/收藏）走整页加载
}

async function openDoc(domain, sub, name) {
  CUR = { domain, sub, name };
  const s = findSub(domain, sub);
  if (s) renderDocList(s.docs, s.label, name);
  renderTree();
  const r = await fetch(`/api/doc?domain=${encodeURIComponent(domain)}&sub=${encodeURIComponent(sub)}&name=${encodeURIComponent(name)}`);
  if (!r.ok) { toast(r.status === 404 ? "文档不存在（可能已被删除）" : "加载失败 " + r.status); return; }
  const data = await r.json();
  DOC = data.doc;
  renderArticle();
  renderCrumb();
  renderInfo();
  renderNotes();
  setTrackingDoc(DOC.rel);
  linksLoadedFor = null;
  if (document.querySelector("#pane-links.active")) loadLinks(); // 停在双链标签时跟随切换
  const art = document.querySelector(".article"); if (art) art.scrollTop = 0;
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
window.addEventListener("popstate", () => { if (WORKBENCH) navigate(location.pathname + location.search, false); });

/* ---------- 编辑 ---------- */
function openEditor() {
  if (!DOC || DOC.is_html) return;
  $("#article").style.display = "none";
  $("#editor").classList.add("show");
  const hint = $("#ed-hint");
  if (hint) hint.style.display = ""; // frontmatter 引导：这是编辑页顶部空白区的用途说明
  $("#ed-path").textContent = DOC.rel;
  $("#ed-text").value = "---\n" + Object.entries(DOC.fm).map(([k, v]) =>
    `${k}: ${v === true ? "true" : JSON.stringify(v)}`).join("\n") + "\n---\n\n" + DOC.md;
  $("#ed-text").focus();
  toast("编辑态 · 保存即写回文件系统，git 记录本次变更");
}
async function closeEditor() {
  const ed = $("#editor"); if (!ed) return;
  const hint = $("#ed-hint");
  if (hint) hint.style.display = "none";
  ed.classList.remove("show");
  $("#article").style.display = "";
}
async function saveDoc() {
  const text = $("#ed-text").value;
  const r = await fetch("/api/save", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: DOC.rel, content: text }) });
  if (!r.ok) { toast("保存失败：" + (await r.text()).slice(0, 120)); return; }
  const fm = {}, m = text.match(/\A---\n([\s\S]*?)\n---\n\n?/);
  let body = text;
  if (m) {
    for (const line of m[1].splitlines ? m[1].split("\n") : m[1].split("\n")) {
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
  closeEditor(); renderArticle();
  toast(`已写回 <span class="mono">${esc(DOC.rel)}</span> · 索引已更新 · git 可 diff`);
}
const edText = $("#ed-text");
if (edText) edText.onkeydown = e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); saveDoc(); }
};

/* ---------- 备注 ---------- */
async function addNote() {
  const i = $("#ni"); const text = i.value.trim(); if (!text) return;
  const r = await fetch("/api/note", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: DOC.rel, text }) });
  if (!r.ok) { toast("备注失败"); return; }
  const data = await r.json(); i.value = "";
  DOC.notes = data.notes;
  renderNotes();
  toast("备注已写入旁挂 <span class='mono'>.notes.md</span>");
}

/* ---------- 收藏 ---------- */
async function toggleFav() {
  const r = await fetch("/api/favorite", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: DOC.rel }) });
  if (!r.ok) { toast("操作失败"); return; }
  const data = await r.json();
  DOC.favorite = data.favorite;
  const b = $("#fav-btn");
  b.textContent = data.favorite ? "★ 已收藏" : "☆ 收藏";
  b.classList.toggle("faved", data.favorite);
  // 同步树缓存里的收藏标记，收藏页/列表星星即时一致
  const s = findSub(DOC.domain, DOC.sub);
  const td = s && s.docs.find(x => x.name === DOC.name);
  if (td) { td.favorite = data.favorite; persistTree(); }
  toast(data.favorite ? "已收藏 · favorite: true 写入 frontmatter" : "已取消收藏");
}

/* ---------- 树缓存持久化（增删改后即时同步） ---------- */
function persistTree() {
  try { localStorage.setItem(LS_TREE, JSON.stringify({ sig: "(本地已改)", domains: TREE })); } catch (e) {}
}

/* ---------- 删除（软删除：移入 _trash，两步确认，列表实时更新） ---------- */
let deleteArmed = false, deleteArmTimer = null;
async function deleteDoc() {
  if (!DOC || DOC.is_html) return;
  const btn = [...document.querySelectorAll("#crumb .iconbtn")].find(b => b.textContent.includes("删除"));
  if (!deleteArmed) {
    deleteArmed = true;
    btn.textContent = "⚠ 确认删除？";
    btn.style.borderColor = "var(--warn-edge)";
    btn.style.color = "var(--warn)";
    deleteArmTimer = setTimeout(() => {
      deleteArmed = false;
      btn.textContent = "🗑 删除";
      btn.style.borderColor = ""; btn.style.color = "";
    }, 3000);
    return;
  }
  clearTimeout(deleteArmTimer); deleteArmed = false;
  btn.textContent = "🗑 删除"; btn.style.borderColor = ""; btn.style.color = "";
  // 乐观更新：先改 UI，后台请求失败再提示（文档在回收站可找回）
  const rel = DOC.rel, deletedTitle = DOC.title;
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
  DOC = null;
  $("#article").innerHTML = `<div class="a-kicker">已删除</div>
    <h1 class="a-title">文档已移入回收站</h1>
    <div class="a-rule"></div>
    <div class="a-body"><p>《${esc(deletedTitle)}》及其美化版、备注已一起移入 <code>content/_trash/</code>，git 历史亦可找回。</p>
    <p>从左侧选择其他文档继续阅读。</p></div>`;
  $("#crumb").innerHTML = `<b>已删除</b><span class="sep">·</span>${esc(deletedTitle)}`;
  toast("已移入回收站 · 列表已实时更新");
  fetch("/api/delete", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: rel }) })
    .then(r => { if (!r.ok) toast("服务端删除失败（文件仍在，可重试）"); })
    .catch(() => toast("服务端删除失败（文件仍在，可重试）"));
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
        `<a class="result" href="/doc/${x.path}"><div class="doc-t">${esc(x.title)}</div><div class="rp">${esc(x.path)}</div></a>`).join("");
      const fwd = d.outgoing.map(x => x.resolved
        ? `<a class="result" href="/doc/${esc(x.path)}"><div class="doc-t">${esc(x.title)}</div><div class="rp">${esc(x.path)}</div></a>`
        : `<div class="result"><div class="doc-t" style="color:var(--warn)">未解析：${esc(x.raw)}</div><div class="rp">没有匹配的文档——整理时顺手修掉或删除</div></div>`).join("");
      pane.innerHTML =
        `<div class="home-sec" style="margin-top:4px">谁引用了它 · ${d.incoming.length}</div>` +
        (back || `<div style="font-size:12.5px;color:var(--faint);padding:4px 2px">还没有。写别的文档时打个 [[${esc(DOC.title)}]] 就连上了。</div>`) +
        `<div class="home-sec" style="margin-top:16px">它引用 · ${d.outgoing.length}</div>` +
        (fwd || `<div style="font-size:12.5px;color:var(--faint);padding:4px 2px">本文没有 [[双链]]。</div>`);
    })
    .catch(() => { pane.innerHTML = `<div class="empty" style="padding:10px 2px">加载失败，稍后再试。</div>`; linksLoadedFor = null; });
}

/* ---------- 美化版弹窗 ---------- */
function openPretty() {
  if (!DOC || !DOC.has_html) return;
  let ov = document.getElementById("pretty-ov");
  if (!ov) {
    ov = document.createElement("div");
    ov.id = "pretty-ov";
    ov.className = "pretty-ov";
    ov.innerHTML = `<div class="pretty-box">
      <div class="pretty-bar"><span class="pt" id="pretty-title"></span>
        <a class="iconbtn" id="pretty-newtab" target="_blank">↗ 新窗口</a>
        <button class="iconbtn" onclick="closePretty()">✕ 关闭</button></div>
      <iframe id="pretty-frame"></iframe></div>`;
    document.body.appendChild(ov);
    ov.addEventListener("click", e => { if (e.target === ov) closePretty(); });
  }
  ov.querySelector("#pretty-title").textContent = DOC.title + " · 美化版";
  ov.querySelector("#pretty-newtab").href = "/raw/" + DOC.html_rel;
  ov.querySelector("iframe").src = "/raw/" + DOC.html_rel;
  ov.classList.add("show");
}
function closePretty() {
  const ov = document.getElementById("pretty-ov");
  if (ov) { ov.classList.remove("show"); ov.querySelector("iframe").src = "about:blank"; }
}

/* ---------- 右键菜单：文档移动 / 复制双链 / 统计信息 ---------- */
let CTX = null; // 当前菜单目标 {kind:'doc'|'sub', rel|domain, sub, name}

function closeCtxMenu() {
  const m = document.getElementById("ctx-menu");
  if (m) { m.remove(); document.removeEventListener("click", closeCtxMenu); }
  CTX = null;
}

function docRelOf(domain, sub, name) {
  return sub === "_root" ? `${domain}/${name}.md` : `${domain}/${sub}/${name}.md`;
}

function openCtxMenu(x, y, items) {
  closeCtxMenu();
  const m = document.createElement("div");
  m.id = "ctx-menu";
  m.innerHTML = items.map((it, i) =>
    it === "-" ? `<div class="ctx-sep"></div>` :
    `<button class="ctx-item ${it.danger ? "danger" : ""}" data-i="${i}">${esc(it.label)}</button>`).join("");
  document.body.appendChild(m);
  const r = m.getBoundingClientRect();
  m.style.left = Math.min(x, innerWidth - r.width - 8) + "px";
  m.style.top = Math.min(y, innerHeight - r.height - 8) + "px";
  m.addEventListener("click", e => {
    const b = e.target.closest(".ctx-item");
    if (!b) return;
    const it = items[+b.dataset.i];
    closeCtxMenu();
    if (it && it.fn) it.fn();
  });
  setTimeout(() => document.addEventListener("click", closeCtxMenu), 0);
}

async function copyText(t, okMsg) {
  try { await navigator.clipboard.writeText(t); toast(okMsg); }
  catch (e) {
    const ta = document.createElement("textarea"); ta.value = t; document.body.appendChild(ta);
    ta.select(); document.execCommand("copy"); ta.remove(); toast(okMsg);
  }
}

async function showStats(rel) {
  const r = await fetch("/api/stats?path=" + encodeURIComponent(rel));
  if (!r.ok) { toast("统计失败"); return; }
  const s = await r.json();
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
  const ov = document.createElement("div");
  ov.className = "pretty-ov";
  ov.innerHTML = `<div class="pretty-box stats-box"><div class="pretty-bar"><span class="pt">统计信息</span><button class="iconbtn" onclick="this.closest('.pretty-ov').remove()">✕ 关闭</button></div>
    <div class="stats-body">${rows.map(([k, v]) => `<div class="meta-row"><span class="k">${esc(k)}</span><span class="v">${esc(v)}</span></div>`).join("")}</div></div>`;
  ov.addEventListener("click", e => { if (e.target === ov) ov.remove(); });
  document.body.appendChild(ov);
}

/* ---------- 通用弹窗（替代系统 prompt/alert/confirm） ----------
   kbModal({ title, body, html, inputs:[{key,label,value,placeholder}], confirmText, danger })
   → Promise<null | { values:{key:value} }>；Esc / 取消 / 点击遮罩返回 null。 */
function kbModal(opt) {
  return new Promise(resolve => {
    const ov = document.createElement("div");
    ov.className = "kbm-ov";
    const inputs = opt.inputs || [];
    ov.innerHTML = `<div class="kbm" role="dialog" aria-modal="true">
      <div class="kbm-title">${esc(opt.title || "")}</div>
      ${opt.body ? `<div class="kbm-body">${esc(opt.body)}</div>` : ""}
      ${opt.html ? `<div class="kbm-body">${opt.html}</div>` : ""}
      ${inputs.map(i => `<label class="kbm-label">${esc(i.label || "")}
        <input class="kbm-input" data-k="${esc(i.key)}" value="${esc(i.value ?? "")}"
          placeholder="${esc(i.placeholder || "")}" spellcheck="false"></label>`).join("")}
      <div class="kbm-btns">
        <button class="iconbtn kbm-cancel">取消</button>
        <button class="iconbtn primary kbm-ok ${opt.danger ? "danger" : ""}">${esc(opt.confirmText || "确定")}</button>
      </div></div>`;
    document.body.appendChild(ov);
    const done = val => { ov.remove(); document.removeEventListener("keydown", onKey); resolve(val); };
    const collect = () => {
      const values = {};
      ov.querySelectorAll(".kbm-input").forEach(inp => values[inp.dataset.k] = inp.value.trim());
      return values;
    };
    const onOk = () => done(collect());
    const onCancel = () => done(null);
    const onKey = e => {
      if (e.key === "Escape") onCancel();
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey || !inputs.length)) onOk();
    };
    ov.querySelector(".kbm-ok").onclick = onOk;
    ov.querySelector(".kbm-cancel").onclick = onCancel;
    ov.addEventListener("mousedown", e => { if (e.target === ov) onCancel(); });
    document.addEventListener("keydown", onKey);
    const first = ov.querySelector(".kbm-input");
    if (first) { first.focus(); first.select(); }
    else ov.querySelector(".kbm-ok").focus();
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
  await kbModal({
    title: `📊 ${s.label} · 目录统计`,
    html: `<div class="ss-grid">
      <div class="ss-cell"><div class="ss-n">${s.n_docs}</div><div class="ss-l">文档数</div></div>
      <div class="ss-cell"><div class="ss-n">${s.total_cjk.toLocaleString()}</div><div class="ss-l">总字数（CJK）</div></div>
      <div class="ss-cell"><div class="ss-n">${s.avg_cjk.toLocaleString()}</div><div class="ss-l">篇均字数</div></div>
      <div class="ss-cell"><div class="ss-n">${s.n_untagged}</div><div class="ss-l">未打标</div></div>
    </div>
    <div class="ss-sec">标签分布 Top ${s.tags.length}</div>
    <div class="ss-tags">${tagRows}</div>
    <div class="ss-sec">最近更新</div>
    <div class="kbm-li">《${esc(s.newest.title || "—")}》 · ${esc(s.newest.when)}</div>`,
    confirmText: "关闭",
  });
}

async function moveDocPrompt(rel) {
  const res = await kbModal({
    title: "移动 / 重命名",
    body: "目标为 content/ 下的相对路径（含 .md）。移动后 FTS、双链与向量索引自动级联更新。",
    inputs: [{ key: "dst", label: "新路径", value: rel, placeholder: "articles/vue2/目录/文档名.md" }],
    confirmText: "移动",
  });
  if (!res) return;
  const dst = res.dst;
  if (!dst || dst === rel) return;
  const r = await fetch("/api/move", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ src: rel, dst }) });
  const d = await r.json().catch(() => ({}));
  if (!r.ok || !d.ok) { toast("移动失败：" + (d.error || r.status)); return; }
  toast(`已移动至 <span class='mono'>${esc(d.dst)}</span> · 索引已级联更新`);
  TREE = null; localStorage.removeItem(LS_TREE); // 树缓存失效，下次渲染重新拉取
  const url = "/doc/" + d.dst.replace(/\.md$/, "").split("/").map(encodeURIComponent).join("/");
  location.href = url; // 移动涉及树/列表重排，整页跳转最可靠
}

document.addEventListener("contextmenu", e => {
  if (!WORKBENCH) return;
  const docA = e.target.closest("#doclist .doc");
  if (docA) {
    e.preventDefault();
    const name = docA.dataset.name;
    const rel = docRelOf(CUR.domain, CUR.sub, name);
    const title = (docA.querySelector(".doc-t") || {}).textContent || name;
    openCtxMenu(e.clientX, e.clientY, [
      { label: "📈 统计信息", fn: () => showStats(rel) },
      { label: "⧉ 复制 [[双链]]", fn: () => copyText(`[[${title.trim()}]]`, "已复制双链") },
      { label: "⧉ 复制 Obsidian URI", fn: () => copyText(`obsidian://open?vault=${encodeURIComponent("knowledge")}&file=${encodeURIComponent(rel.replace(/\.md$/, ""))}`, "已复制 URI") },
      "-",
      { label: "⇄ 移动 / 重命名…", fn: () => moveDocPrompt(rel) },
    ]);
    return;
  }
  const subA = e.target.closest("#tree .sub");
  if (subA) {
    e.preventDefault();
    const dom = subA.dataset.dom, sub = subA.dataset.sub;
    const base = sub === "_root" ? dom : `${dom}/${sub}`;
    openCtxMenu(e.clientX, e.clientY, [
      { label: "📂 在此新建文档…", fn: async () => {
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
          if (r.ok) { TREE = null; localStorage.removeItem(LS_TREE); location.href = "/doc/" + rel.slice(0, -3).split("/").map(encodeURIComponent).join("/"); }
          else toast("创建失败：" + r.status);
        } },
      { label: "📊 目录统计", fn: () => showSubStats(dom, sub) },
      "-",
      { label: "⧉ 复制目录路径", fn: () => copyText(base, "已复制路径") },
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
document.addEventListener("keydown", e => {
  if (e.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) { e.preventDefault(); const q = $("#q"); q && q.focus(); }
  if (e.key === "Escape") { closeEditor(); }
});
const q = $("#q");
if (q) q.addEventListener("keydown", e => {
  if (e.key === "Enter" && q.value.trim()) location.href = "/search?q=" + encodeURIComponent(q.value.trim());
});

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
loadTree().then(() => renderTree());
