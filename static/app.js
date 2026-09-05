/* 知库 reader 前端：主题、面板折叠、正文渲染、编辑/备注/收藏、快捷键 */
window.APP_JS_VERSION = 7;
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const toast = m => { const t = $("#toast"); t.innerHTML = m; t.classList.add("show"); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 2600); };

/* ---------- 主题 ---------- */
function applyTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  const b = $("#theme-btn"); if (b) b.textContent = t === "dark" ? "☾" : "☀";
  try { localStorage.setItem("kb-theme", t); } catch (e) {}
}
const themeBtn = $("#theme-btn");
if (themeBtn) themeBtn.onclick = () => {
  const now = document.documentElement.getAttribute("data-theme");
  applyTheme(now === "dark" ? "light" : "dark");
  if (DOC && document.querySelector("#article .mermaid")) renderArticle(); // mermaid 随主题重上色
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

/* ---------- 右栏 tabs ---------- */
function tab(id, el) {
  $$(".rtab").forEach(t => t.classList.remove("active")); el.classList.add("active");
  $$(".rpane").forEach(p => p.classList.remove("active")); $("#pane-" + id).classList.add("active");
}

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

/* ---------- 正文渲染（workbench） ---------- */
let DOC = null;
const docData = document.getElementById("doc-data");
if (docData) {
  DOC = JSON.parse(docData.textContent);
  renderArticle();
}

function renderArticle() {
  const el = $("#article");
    if (DOC.is_html) {
    el.innerHTML = `<div class="a-kicker">HTML 文档</div>
      <h1 class="a-title">${DOC.title}</h1>
      <div class="a-rule"></div>
      <div class="a-body"><p>这是整页 HTML 文档，直通渲染以保留其自带样式。</p>
      <p><a class="iconbtn primary" href="/raw/${DOC.rel}" target="_blank">在新标签页打开原页面 ↗</a></p></div>`;
    buildToc();
    return;
  }
  const chips = [
    `<span class="chip acc">${DOC.source_label}</span>`,
    DOC.fm.source_path ? `<span class="chip">${DOC.fm.source_path}</span>` : "",
    DOC.fm.collected ? `<span class="chip">${DOC.fm.collected} 收录</span>` : "",
    (DOC.fm.tags && DOC.fm.tags.length)
      ? DOC.fm.tags.map(t => `<span class="chip acc">${t}</span>`).join("")
      : `<span class="chip warn">tags 未打标</span>`,
  ].join("");
  el.innerHTML = `<div class="a-kicker">${DOC.domain_label} / ${DOC.sub_label}</div>
    <h1 class="a-title">${DOC.title}</h1>
    <div class="a-chips">${chips}</div>
    <div class="a-rule"></div>
    <div class="a-body">${marked.parse(DOC.md)}</div>`;

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
  // 代码高亮（mermaid 块已替换，不参与）
  if (window.hljs) el.querySelectorAll("pre code:not(.language-mermaid)").forEach(b => {
    try { hljs.highlightElement(b); } catch (e) {}
  });
  buildToc();
}

/* mermaid 懒加载（声明见 renderArticle 之前，避免 TDZ） */

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

/* ---------- 编辑 ---------- */
function openEditor() {
  if (!DOC || DOC.is_html) return;
  $("#article").style.display = "none";
  $("#editor").classList.add("show");
  $("#ed-text").value = "---\n" + Object.entries(DOC.fm).map(([k, v]) =>
    `${k}: ${v === true ? "true" : JSON.stringify(v)}`).join("\n") + "\n---\n\n" + DOC.md;
  $("#ed-text").focus();
}
function closeEditor() {
  $("#editor").classList.remove("show");
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
    for (const line of m[1].splitlines()) { const i = line.indexOf(":");
      if (i > 0) { const k = line.slice(0, i).trim(), v = line.slice(i + 1).trim();
        fm[k] = v === "true" ? true : (v.startsWith("[") ? v.slice(1, -1).split(",").map(x => x.trim().replace(/^"|"$/g, "")).filter(Boolean) : v.replace(/^"|"$/g, "")); } }
    body = text.slice(m[0].length);
  }
  DOC.fm = fm; DOC.md = body; DOC.title = fm.title || DOC.title;
  closeEditor(); renderArticle();
  toast(`已写回 <span class="mono">${DOC.rel}</span> · 索引已更新 · git 可 diff`);
}
$("#editor textarea") && ($("#editor textarea").onkeydown = e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); saveDoc(); }
});

/* ---------- 备注 ---------- */
async function addNote() {
  const i = $("#ni"); const text = i.value.trim(); if (!text) return;
  const r = await fetch("/api/note", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: DOC.rel, text }) });
  if (!r.ok) { toast("备注失败"); return; }
  const data = await r.json(); i.value = "";
  $("#notes-list").innerHTML = data.notes.map(n =>
    `<div class="note-card"><div class="when">${n.when} · 旁挂 .notes.md</div><p>${n.text.replace(/</g, "&lt;")}</p></div>`).join("");
  toast("备注已写入旁挂 <span class='mono'>.notes.md</span>");
}
const ni = $("#ni"); if (ni) ni.onkeydown = e => { if (e.key === "Enter") addNote(); };

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
  toast(data.favorite ? "已收藏 · favorite: true 写入 frontmatter" : "已取消收藏");
}

/* ---------- 删除（软删除：移入 _trash） ---------- */
async function deleteDoc() {
  if (!DOC || DOC.is_html) return;
  if (!confirm("删除后移入 content/_trash/（git 历史亦可找回）。确定删除这篇文档吗？")) return;
  const r = await fetch("/api/delete", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: DOC.rel }) });
  if (!r.ok) { toast("删除失败：" + (await r.text()).slice(0, 120)); return; }
  const moved = (await r.json()).moved || [];
  toast(`已移入回收站（${moved.length} 个文件） · 随时可恢复`);
  setTimeout(() => { location.href = "/"; }, 700);
}

/* ---------- 快捷键与搜索 ---------- */
document.addEventListener("keydown", e => {
  if (e.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) { e.preventDefault(); $("#q").focus(); }
  if (e.key === "Escape") { if ($("#editor") && $("#editor").classList.contains("show")) closeEditor(); }
});
const q = $("#q");
if (q) q.addEventListener("keydown", e => {
  if (e.key === "Enter" && q.value.trim()) location.href = "/search?q=" + encodeURIComponent(q.value.trim());
});
