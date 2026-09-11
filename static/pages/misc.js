/* =====================================================================
   知库 · T5 页面级脚本（tags / inbox；favorites 与 error 为纯静态页无需 JS）
   依赖 base.html 公共契约：esc / toast / kbModal（app.js 全局）。
   修复：原 inbox.html 内联脚本 res.dir.replace(/^\\/+|\\/+$/g, "") 的 \\ 使正则
   提前闭合（HEAD e041fa2 即存在），导致整段脚本 SyntaxError、批量归档失效；
   本文件中已修正为 /^\/+|\/+$/g。
   ===================================================================== */
(function () {
"use strict";

/* ---------------- 标签页 ---------------- */
function normTag(s) { return String(s).toLowerCase().replace(/[\s_\-\.]/g, ""); }
function lev(a, b) {
  const m = a.length, n = b.length;
  if (!m || !n) return Math.max(m, n);
  let prev = Array.from({ length: n + 1 }, (_, i) => i), cur = new Array(n + 1);
  for (let i = 1; i <= m; i++) {
    cur[0] = i;
    for (let j = 1; j <= n; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    [prev, cur] = [cur, prev];
  }
  return prev[n];
}
function suggestMerges(list) {
  const out = [], seen = new Set();
  const push = (src, dst, why, n) => {
    const key = [src, dst].sort().join("→");
    if (seen.has(key)) return;
    seen.add(key);
    out.push({ src, dst, why, n });
  };
  for (let i = 0; i < list.length; i++) {
    for (let j = i + 1; j < list.length; j++) {
      const a = list[i], b = list[j];
      const na = normTag(a.t), nb = normTag(b.t);
      if (!na || !nb) continue;
      if (na === nb) { /* 大小写 / 分隔符写法差异 → 并入文档数多的一侧 */
        if (a.n >= b.n) push(b.t, a.t, "大小写/写法差异", b.n);
        else push(a.t, b.t, "大小写/写法差异", a.n);
        continue;
      }
      if (na.length >= 3 && nb.length >= 3 &&
          (nb.startsWith(na) || na.startsWith(nb)) &&
          Math.min(na.length, nb.length) / Math.max(na.length, nb.length) >= 0.45) {
        /* 包含关系：短的并入长的（AI → AI 资产 / vue → vue3） */
        const short_ = na.length < nb.length ? a : b, long_ = na.length < nb.length ? b : a;
        push(short_.t, long_.t, "拼写近似（包含）", short_.n);
        continue;
      }
      if (na.length >= 4 && nb.length >= 4) {
        const d = lev(na, nb);
        if (d / Math.max(na.length, nb.length) <= 0.2) {
          if (a.n >= b.n) push(b.t, a.t, "拼写近似", b.n);
          else push(a.t, b.t, "拼写近似", a.n);
        }
      }
    }
  }
  return out.slice(0, 12);
}

function initTags() {
  const cloud = document.getElementById("tag-cloud");
  if (!cloud) return;
  let TAGDATA = [];
  try { TAGDATA = JSON.parse(document.getElementById("tags-data").textContent); } catch (e) {}
  const byTag = {};
  TAGDATA.forEach(x => { byTag[x.t] = x; });
  const drawer = document.getElementById("tag-drawer");
  const drawerH = document.getElementById("drawer-h");
  const drawerDocs = document.getElementById("drawer-docs");

  /* 1) 相似合并建议卡（客户端启发式；实际合并仍走两段确认 + 后端 dry-run 预览） */
  const suggSec = document.getElementById("sugg-sec");
  const grid = document.getElementById("merge-suggest");
  if (suggSec && grid) {
    const sugg = suggestMerges(TAGDATA);
    if (sugg.length) {
      suggSec.hidden = false;
      grid.innerHTML = sugg.map(s =>
        `<button type="button" class="merge-card" data-src="${esc(s.src)}" data-dst="${esc(s.dst)}" data-n="${s.n}">
          <span class="m-src">「${esc(s.src)}」</span>
          <svg class="arrow-ic" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-move-arrow"/></svg>
          <span class="t-new">${esc(s.dst)}</span>
          <span class="meta">${s.n} 篇 · 合并建议</span>
        </button>`).join("");
      grid.addEventListener("click", e => {
        const b = e.target.closest(".merge-card");
        if (b) mergeTagPrompt(b.dataset.src, b.dataset.dst);
      });
    }
  }

  /* 2) 胶囊交互：勾选批量合并；点胶囊展开文档抽屉；并入按钮走单标签合并 */
  cloud.addEventListener("click", e => {
    const t = e.target.closest(".t");
    if (!t) return;
    if (e.target.classList.contains("t-check")) return;
    const mb = e.target.closest(".t-merge");
    if (mb) { mergeTagPrompt(mb.dataset.merge); return; }
    const tag = t.dataset.tag;
    const d = byTag[tag];
    if (!d) return;
    const open = drawer && !drawer.hidden && drawer.dataset.tag === tag;
    cloud.querySelectorAll(".t.open").forEach(x => x.classList.remove("open"));
    if (open) { drawer.hidden = true; return; }
    t.classList.add("open");
    drawer.dataset.tag = tag;
    drawerH.textContent = `「${tag}」· ${d.n} 篇文档`;
    drawerDocs.innerHTML = d.docs.map(x =>
      `<a class="result" href="${esc(x.u)}"><div class="doc-t">${esc(x.t)}</div><div class="rp">${esc(x.p)}</div></a>`).join("");
    drawer.hidden = false;
  });
  cloud.addEventListener("change", e => {
    if (!e.target.classList.contains("t-check")) return;
    e.target.closest(".t").classList.toggle("sel", e.target.checked);
    tagSelUpdate();
  });
  function tagSel() {
    return [...cloud.querySelectorAll(".t-check:checked")].map(c => c.closest(".t").dataset.tag);
  }
  function tagSelUpdate() {
    const selbar = document.getElementById("tag-selbar");
    const n = tagSel().length;
    if (!selbar) return;
    selbar.hidden = !n;
    document.getElementById("tag-sel-count").textContent = n ? `已选 ${n} 个标签` : "未选择标签";
    document.getElementById("tag-merge-sel").disabled = !n;
  }
  const clearBtn = document.getElementById("tag-clear");
  if (clearBtn) clearBtn.addEventListener("click", () => {
    cloud.querySelectorAll(".t-check:checked").forEach(c => { c.checked = false; c.closest(".t").classList.remove("sel"); });
    tagSelUpdate();
  });
  const mergeSelBtn = document.getElementById("tag-merge-sel");
  if (mergeSelBtn) mergeSelBtn.addEventListener("click", mergeSelectedTags);

  /* 3) 合并流程：两段确认（预览 apply:false → 确认 apply:true），与原模板契约一致 */
  async function mergeSelectedTags() {
    const srcs = tagSel();
    if (!srcs.length) return;
    const listHtml = srcs.map(t => `<div class="kbm-li">${esc(t)}</div>`).join("");
    const res = await kbModal({
      title: `批量合并 ${srcs.length} 个标签`,
      body: `以下标签将全部并入同一目标标签（受影响文档的 frontmatter 会被改写，FTS 级联重建）：
        <div class="kbm-list">${listHtml}</div>`,
      inputs: [{ key: "dst", label: "目标标签", placeholder: "例如：AI资产" }],
      confirmText: "预览影响",
    });
    if (!res || !res.dst) return;
    const dst = res.dst;
    const affected = [];
    for (const src of srcs) {
      if (src === dst) continue;
      const r1 = await fetch("/api/tag/merge", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ src, dst, apply: false }) });
      const d1 = await r1.json();
      if (d1.ok && d1.n_docs) affected.push({ src, n: d1.n_docs });
    }
    if (!affected.length) { toast("所选标签均无可合并文档"); return; }
    const total = affected.reduce((s, x) => s + x.n, 0);
    const affHtml = affected.map(x => `<div class="kbm-li">${esc(x.src)} · ${x.n} 篇</div>`).join("");
    const res2 = await kbModal({
      title: "确认批量合并",
      body: `共 <b>${total}</b> 篇文档受影响，确认后写盘并级联更新 FTS 索引：
        <div class="kbm-list">${affHtml}</div>`,
      danger: true, confirmText: "执行合并",
    });
    if (!res2) return;
    let okN = 0;
    for (const { src } of affected) {
      const r2 = await fetch("/api/tag/merge", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ src, dst, apply: true }) });
      const d2 = await r2.json();
      if (d2.ok) okN += d2.n_docs;
    }
    toast(`已合并 ${okN} 篇 · ${affected.length} 个标签 → 「${dst}」 · FTS 已重建`);
    setTimeout(() => location.reload(), 1400);
  }

  async function mergeTagPrompt(src, preset) {
    const res = await kbModal({
      title: "标签合并",
      body: "把「<b>" + esc(src) + "</b>」并入另一个标签：受影响文档的 frontmatter 会被改写，FTS 级联重建。先预览受影响清单，确认后才写盘。",
      inputs: [{ key: "dst", label: "目标标签", value: preset || src, placeholder: "例如：AI资产" }],
      confirmText: "预览影响",
    });
    if (!res || !res.dst || res.dst === src) return;
    const dst = res.dst;
    const r1 = await fetch("/api/tag/merge", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ src, dst, apply: false }) });
    const d1 = await r1.json();
    if (!d1.ok) { toast("预览失败"); return; }
    if (!d1.n_docs) { toast("「" + src + "」没有可合并的文档"); return; }
    const listHtml = d1.docs.slice(0, 12).map(x => `<div class="kbm-li">${esc(x.path)}</div>`).join("")
      + (d1.n_docs > 12 ? `<div class="kbm-li">… 共 ${d1.n_docs} 篇</div>` : "");
    const res2 = await kbModal({
      title: "确认合并",
      body: `将把 <b>${d1.n_docs}</b> 篇文档的「<b>${esc(src)}</b>」改为「<b>${esc(dst)}</b>」，确认后写盘并级联更新 FTS / 双链 / 向量索引：
        <div class="kbm-list">${listHtml}</div>`,
      danger: true, confirmText: "执行合并",
    });
    if (!res2) return;
    const r2 = await fetch("/api/tag/merge", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ src, dst, apply: true }) });
    const d2 = await r2.json();
    if (d2.ok) { toast("已合并 " + d2.n_docs + " 篇 · FTS 已重建"); setTimeout(() => location.reload(), 1200); }
    else toast("合并失败");
  }
}

/* ---------------- 收件箱页 ---------------- */
function whenStr(ts) {
  const dt = new Date(ts), now = new Date();
  const hm = `${String(dt.getHours()).padStart(2, "0")}:${String(dt.getMinutes()).padStart(2, "0")}`;
  const day = 86400000, diff = now - ts;
  if (diff < 60000) return "刚刚";
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
  if (dt.toDateString() === now.toDateString()) return `今天 ${hm}`;
  if (diff < 7 * day) return `${Math.floor(diff / day)} 天前`;
  return `${dt.getMonth() + 1}-${dt.getDate()}`;
}

function initInbox() {
  const kanban = document.getElementById("inbox-kanban");
  if (!kanban) return;
  const colTodo = kanban.querySelector('[data-col="todo"]');
  const colStaged = kanban.querySelector('[data-col="staged"]');
  const colDone = kanban.querySelector('[data-col="done"]');
  const RECENT_KEY = "kb-inbox-recent";

  const recents = () => { try { return JSON.parse(localStorage.getItem(RECENT_KEY) || "[]"); } catch (e) { return []; } };
  function pushRecent(rel, dir) {
    const r = recents().filter(x => x.rel !== rel);
    r.unshift({ rel, dir, ts: Date.now() });
    try { localStorage.setItem(RECENT_KEY, JSON.stringify(r.slice(0, 8))); } catch (e) {}
    renderDone();
  }
  function fileName(rel) { return String(rel).split("/").pop(); }
  function renderDone() {
    if (!colDone) return;
    const list = recents();
    colDone.querySelectorAll(".kan-item,.kan-empty").forEach(x => x.remove());
    const html = list.length ? list.map(x =>
      `<div class="kan-item" data-col="done"><div class="head"><span class="t">${esc(fileName(x.rel))}</span></div>
       <div class="meta"><span class="dst">→ ${esc(x.dir)}</span><span>${whenStr(x.ts)}</span></div></div>`).join("")
      : `<div class="kan-empty">暂无归档记录</div>`;
    colDone.insertAdjacentHTML("beforeend", html);
    colDone.querySelector(".kh .n").textContent = list.length;
  }

  function items() { return [...kanban.querySelectorAll('.kan-item[data-col="todo"],.kan-item[data-col="staged"]')]; }
  function ibSel() { return items().filter(x => x.querySelector(".ib-check").checked); }
  function ibUpdate() {
    const sel = ibSel(), n = sel.length;
    const cnt = document.getElementById("ib-count");
    if (cnt) cnt.textContent = n ? `已选 ${n} 篇` : "未选择";
    const go = document.getElementById("ib-go");
    if (go) go.disabled = !n;
    const all = document.getElementById("ib-all");
    if (all) { const total = items().length; all.checked = n === total && n > 0; all.indeterminate = n > 0 && n < total; }
    /* 勾选 = 进「归档中」列（选中即暂存，按钮执行才真正写盘） */
    sel.forEach(x => { x.dataset.col = "staged"; x.classList.add("sel"); colStaged.appendChild(x); });
    items().filter(x => !x.querySelector(".ib-check").checked).forEach(x => {
      x.dataset.col = "todo"; x.classList.remove("sel"); colTodo.appendChild(x);
    });
    colTodo.querySelector(".kh .n").textContent = colTodo.querySelectorAll(".kan-item").length;
    colStaged.querySelector(".kh .n").textContent = colStaged.querySelectorAll(".kan-item").length;
  }

  kanban.addEventListener("change", e => { if (e.target.classList.contains("ib-check")) ibUpdate(); });
  const allBox = document.getElementById("ib-all");
  if (allBox) allBox.addEventListener("change", () => {
    items().forEach(x => { x.querySelector(".ib-check").checked = allBox.checked; });
    ibUpdate();
  });
  kanban.addEventListener("click", e => {
    const row = e.target.closest(".kan-item");
    if (!row) return;
    const act = e.target.closest("[data-act]");
    if (!act) return;
    if (act.dataset.act === "move") inboxMove(row);
    else if (act.dataset.act === "del") inboxDelete(row);
  });

  /* 拖拽：卡片拖入「归档中」= 勾选暂存；拖回「待读」= 取消；「已归档·最近」是记录列，不收卡 */
  let dragEl = null;
  kanban.addEventListener("dragstart", e => {
    const row = e.target.closest('.kan-item[data-col="todo"],.kan-item[data-col="staged"]');
    if (!row) { e.preventDefault(); return; }
    dragEl = row; row.classList.add("dragging");
    try { e.dataTransfer.setData("text/plain", row.dataset.rel); } catch (err) {}
    e.dataTransfer.effectAllowed = "move";
  });
  kanban.addEventListener("dragend", () => {
    if (dragEl) dragEl.classList.remove("dragging");
    dragEl = null;
    kanban.querySelectorAll(".kan-col").forEach(c => c.classList.remove("drop-hint", "drop-no"));
  });
  kanban.addEventListener("dragover", e => {
    const col = e.target.closest(".kan-col");
    if (!col || !dragEl) return;
    e.preventDefault();
    kanban.querySelectorAll(".kan-col").forEach(c => c.classList.remove("drop-hint", "drop-no"));
    col.classList.add("drop-hint");
    if (col === colDone) col.classList.add("drop-no");
  });
  kanban.addEventListener("drop", e => {
    const col = e.target.closest(".kan-col");
    if (!col || !dragEl) return;
    e.preventDefault();
    if (col === colDone) { toast("「已归档 · 最近」是记录列，直接勾选卡片进「归档中」即可批量归档"); return; }
    const box = dragEl.querySelector(".ib-check");
    box.checked = col === colStaged;
    ibUpdate();
  });

  /* 批量归档（原 inbox.html 缺陷修复点：正则两边斜杠转义错误已更正） */
  const goBtn = document.getElementById("ib-go");
  if (goBtn) goBtn.addEventListener("click", ibArchive);
  async function ibArchive() {
    const rows = ibSel();
    if (!rows.length) return;
    const listHtml = rows.map(r => `<div class="kbm-li">${esc(r.dataset.rel)}</div>`).join("");
    const res = await kbModal({
      title: `批量归档 ${rows.length} 篇`,
      body: `所选 ${rows.length} 篇将移入同一目标目录（文件名保持不变），写盘后级联更新 FTS / 双链 / 向量索引：
        <div class="kbm-list">${listHtml}</div>`,
      inputs: [{ key: "dir", label: "目标目录（content/ 下，不含文件名）", placeholder: "articles/ai" }],
      confirmText: "批量归档",
    });
    if (!res || !res.dir) return;
    const dir = res.dir.replace(/^\/+|\/+$/g, "");
    const payload = rows.map(r => ({ src: r.dataset.rel, dst: `${dir}/${r.dataset.rel.split("/").pop()}` }));
    const r = await fetch("/api/move/batch", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: payload }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.ok) { toast("批量归档失败：" + (d.error || r.status)); return; }
    if (d.n_fail) {
      const fails = d.results.filter(x => !x.ok).map(x => `<div class="kbm-li">${esc(x.src)} → ${esc(x.error)}</div>`).join("");
      await kbModal({ title: `完成（${d.n_ok} 成功 / ${d.n_fail} 失败）`,
        body: `<div class="kbm-list">${fails}</div>`, confirmText: "知道了" });
    } else {
      toast(`已批量归档 ${d.n_ok} 篇 → <span class='mono'>${esc(dir)}</span>`);
      rows.forEach(rw => pushRecent(rw.dataset.rel, dir));
    }
    TREE = null; localStorage.removeItem(LS_TREE);
    setTimeout(() => location.reload(), d.n_fail ? 1600 : 900);
  }

  async function inboxMove(row) {
    const rel = row.dataset.rel;
    const res = await kbModal({
      title: "归档到…",
      body: "把 <span class='mono'>" + esc(rel) + "</span> 移入正式领域目录（content/ 下的相对路径，含 .md）。移出 _inbox 后才算完成归档，写盘后级联更新 FTS / 双链 / 向量索引。",
      inputs: [{ key: "dst", label: "目标路径", placeholder: "articles/ai/文件名.md" }],
      confirmText: "归档",
    });
    if (!res || !res.dst) return;
    const r = await fetch("/api/move", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ src: rel, dst: res.dst }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.ok) { toast("归档失败：" + (d.error || r.status)); return; }
    pushRecent(rel, d.dst.split("/").slice(0, -1).join("/"));
    toast(`已归档至 <span class='mono'>${esc(d.dst)}</span>`); setTimeout(() => location.reload(), 900);
  }

  async function inboxDelete(row) {
    const rel = row.dataset.rel;
    const res = await kbModal({ title: "丢弃这篇？",
      body: "「" + esc(rel) + "」将移入 content/_trash/（软删除，可找回），索引级联更新。",
      danger: true, confirmText: "丢弃" });
    if (!res) return;
    const r = await fetch("/api/delete", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: rel }) });
    if (r.ok) { toast("已移入回收站"); row.remove(); ibUpdate(); }
    else toast("删除失败：" + r.status);
  }

  ibUpdate();
  renderDone();
}

/* ---------------- 挂载（脚本 defer，DOM 就绪后直接执行） ---------------- */
initTags();
initInbox();
})();
