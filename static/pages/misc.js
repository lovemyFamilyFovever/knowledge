/* =====================================================================
   知库 · T5 页面级脚本（tags / inbox；favorites 与 error 为纯静态页无需 JS）
   依赖 base.html 公共契约：esc / toast / kbModal（app.js 全局）。
   修复：原 inbox.html 内联脚本 res.dir.replace(/^\\/+|\\/+$/g, "") 的 \\ 使正则
   提前闭合（HEAD e041fa2 即存在），导致整段脚本 SyntaxError、批量归档失效；
   本文件中已修正为 /^\/+|\/+$/g。
   ===================================================================== */
(function () {
"use strict";

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
    /* 问题16：勾选 = 只加徽标，不再把卡片 appendChild 移进「归档中」列。
       原实现的两个毛病：每勾一张卡片列表跳动一次（重排心智负担）；勾选与拖拽
       是两套并存的暂存心智。现在卡片留在原位，「归档中」列只显示计数与提示，
       执行批量归档时卡片才真正离开看板（见 ibArchive 的 rw.remove()）。 */
    items().forEach(x => x.classList.toggle("sel", x.querySelector(".ib-check").checked));
    colTodo.querySelector(".kh .n").textContent = colTodo.querySelectorAll(".kan-item").length;
    if (colStaged) {
      colStaged.querySelectorAll(".kan-item,.kan-empty").forEach(x => x.remove());
      colStaged.insertAdjacentHTML("beforeend", n
        ? `<div class="kan-empty">已勾选 ${n} 篇 · 点「批量归档…」执行</div>`
        : `<div class="kan-empty">勾选卡片或把它拖到这里</div>`);
      colStaged.querySelector(".kh .n").textContent = n;
    }
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
    else if (act.dataset.act === "purge") inboxPurge(row);
    else if (act.dataset.act === "ignore") inboxIgnoreDir(row);
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
    /* 问题9：不再 setTimeout+reload（toast 曾随页面销毁）。
       按后端逐条 results 精确移除成功行、看板局部更新；缓存统一走 invalidate("all")。 */
    const relOk = new Set((d.results || []).filter(x => x.ok).map(x => x.src));
    rows.forEach(rw => {
      if (relOk.has(rw.dataset.rel)) { rw.remove(); pushRecent(rw.dataset.rel, dir); }
    });
    ibUpdate();
    if (window.invalidate) invalidate("all");
    if (d.n_fail) {
      const fails = d.results.filter(x => !x.ok).map(x => `<div class="kbm-li">${esc(x.src)} → ${esc(x.error)}</div>`).join("");
      await kbModal({ title: `完成（${d.n_ok} 成功 / ${d.n_fail} 失败）`,
        body: `<div class="kbm-list">${fails}</div>`, confirmText: "知道了" });
    } else {
      toast(`已批量归档 ${d.n_ok} 篇 → <span class='mono'>${esc(dir)}</span>`);
    }
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
    // 问题9：局部移除 + 缓存失效，toast 存活；不再 reload
    row.remove(); ibUpdate();
    if (window.invalidate) invalidate("all");
    pushRecent(rel, d.dst.split("/").slice(0, -1).join("/"));
    toast(`已归档至 <span class='mono'>${esc(d.dst)}</span>`);
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

  /* 彻底删除（2026-09-20 用户要求）：仅收件箱可用的不可逆删除。
     _inbox 不进 git 也不进索引，软删到 _trash 只是垃圾换个地方躺；
     须输入确认词，防手滑。后端 /api/inbox/purge 二次设防（路径前缀校验）。 */
  async function inboxPurge(row) {
    const rel = row.dataset.rel;
    const res = await kbModal({ title: "彻底删除（不可恢复）",
      body: "「<span class='mono'>" + esc(rel) + "</span>」将从磁盘直接删除：<b>不进回收站、git 也没有它</b>（_inbox 不被跟踪），删了就是没了。输入 <b>彻底删除</b> 以确认。",
      inputs: [{ key: "c", label: "确认词", placeholder: "输入：彻底删除" }],
      danger: true, confirmText: "彻底删除" });
    if (!res) return;
    if ((res.c || "").trim() !== "彻底删除") { toast("确认词不匹配，已取消"); return; }
    const r = await fetch("/api/inbox/purge", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: rel }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.ok) { toast("彻底删除失败：" + (d.error || r.status)); return; }
    row.remove(); ibUpdate();
    if (window.invalidate) invalidate("all");
    toast("已彻底删除");
  }

  /* 需求#3：开发产生的临时/日志/脚本类文件不再进待归档 —— 忽略整个来源目录。
     忽略清单落 content/_meta/inbox-ignore.json，可手工编辑回滚；源文件不动。 */
  async function inboxIgnoreDir(row) {
    const rel = row.dataset.rel;
    const inner = rel.replace(/^_inbox\//, "");
    const isDir = inner.includes("/");
    const dir = isDir ? inner.slice(0, inner.lastIndexOf("/")) : inner;
    // 根级文件没有父目录可忽略：后端会退化成"忽略这一个文件"（routes_files.py:186），
    // 所以文案必须跟着变 —— 原来这里一律写"忽略整个目录 /_inbox/<文件>/ "，
    // 既多了一个不存在的尾斜杠，又承诺了"以后扫进该目录的文件都不再出现"（并不成立）。
    // 旧代码那句 `if (!dir)` 是死分支（行必有名字），一并删掉。
    const res = await kbModal({
      title: isDir ? "忽略整个目录？" : "忽略这个文件？",
      body: isDir
        ? `把 <span class='mono'>_inbox/${esc(dir)}/</span> 加入忽略清单：本批与以后扫进该目录的文件都不再出现在待归档（清单可手工编辑回滚，源文件不动）。`
        : `<span class='mono'>_inbox/${esc(dir)}</span> 在收件箱根级，没有父目录可忽略 —— 这里忽略的是**这一个文件**：它不再出现在待归档，同目录其他文件不受影响（清单可手工编辑回滚，源文件不动）。`,
      inputs: [{ key: "d", label: isDir ? "要忽略的目录（相对 _inbox）" : "要忽略的文件（相对 _inbox）", value: dir }],
      confirmText: "忽略",
    });
    if (!res || !res.d) return;
    const edited = res.d.replace(/^\/+|\/+$/g, "");
    const r = await fetch("/api/inbox/ignore", { method: "POST", headers: { "Content-Type": "application/json" },
      // scope 必须跟着"这是目录还是根级文件"走：以前一律发 dir，根级文件就被记成
      // 一条永远匹配不到的规则（台账 §6 第 34 行）
      body: JSON.stringify({ path: "_inbox/" + edited, scope: isDir ? "dir" : "file" }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.ok) { toast("忽略失败：" + (d.error || r.status)); return; }
    // d.ignored 是**全路径**（"_inbox/开发产物"），旧写法又在前面拼了一次 "_inbox/"，
    // 前缀成了 "_inbox/_inbox/…" → 永远匹配不到 → 点了忽略行还在原地。
    const gone = isDir ? rowsInDir(d.ignored) : items().filter(x => x.dataset.rel === d.ignored);
    gone.forEach(x => x.remove());
    ibUpdate();
    toast(`已忽略 <span class='mono'>${esc(d.ignored)}</span> · ${gone.length} 篇从列表移除`);
  }
  function rowsInDir(dir) {
    const pfx = String(dir || "").replace(/\/+$/, "") + "/";
    return items().filter(x => (x.dataset.rel + "/").startsWith(pfx));
  }

  ibUpdate();
  renderDone();
}

/* ---------------- 挂载（脚本 defer，DOM 就绪后直接执行） ---------------- */
initInbox();
})();
