/* =====================================================================
   知库 · 编辑器 [[ 双链补全（Story 1）
   契约：textarea#ed-text 输入 [[ 触发；调 /api/wikilink/suggest（后端现成，
   返回 items: [{name, rel, kind, sub_label}]）；键盘 ↑↓ 选择、Enter/Tab 插入、
   Esc 关闭；鼠标 hover/click 同步。插入格式 [[name]]（name 即标题/词，
   与 fts.resolve_wikilink 的 by_title / by_stem 解析对齐，不产生死链）。
   设计约束：不改 app.js 任何保存/fm 逻辑，纯增强层；textarea 值读写走
   原生 value + setRangeText，ED_SNAPSHOT dirty 契约不受影响。
   ===================================================================== */
(function () {
  "use strict";
  var $ = function (s, p) { return (p || document).querySelector(s); };

  var ta = null;          // textarea#ed-text
  var box = null;         // 补全下拉 DOM
  var items = [];         // 当前候选
  var active = 0;         // 高亮下标
  var open = false;
  var trigStart = -1;     // `[[` 中第一个 [ 的 caret 位置
  var debounceTimer = 0;
  var blurTimer = 0;
  var lastQuery = "";

  /* ---------- DOM ---------- */
  function ensureBox() {
    if (box) return box;
    box = document.createElement("div");
    box.className = "wl-suggest";
    box.setAttribute("role", "listbox");
    box.style.display = "none";
    document.body.appendChild(box);
    box.addEventListener("mousedown", function (e) {
      // 用 mousedown 而非 click：抢在 textarea blur 之前完成插入
      e.preventDefault();
      var li = e.target.closest && e.target.closest("[data-idx]");
      if (li) pick(parseInt(li.dataset.idx, 10));
    });
    box.addEventListener("mousemove", function (e) {
      var li = e.target.closest && e.target.closest("[data-idx]");
      if (!li) return;
      var i = parseInt(li.dataset.idx, 10);
      if (i !== active) { active = i; paint(); }
    });
    return box;
  }

  /* ---------- 触发检测：caret 前是否处于 [[... 未闭合 ---------- */
  function detectTrigger() {
    var pos = ta.selectionStart;
    if (pos !== ta.selectionEnd) return -1; // 有选区不触发
    var before = ta.value.slice(0, pos);
    var m = before.match(/\[\[([^\[\]\n]{0,40})$/);
    if (!m) return -1;
    // 排除 [[a]]b 这种已闭合后再输入的情形：match 已保证 [[ 后无 ]，天然排除
    return pos - m[0].length; // 返回 `[[` 起始下标
  }

  function currentQuery() {
    if (trigStart < 0) return "";
    return ta.value.slice(trigStart + 2, ta.selectionStart);
  }

  /* ---------- 取数 ---------- */
  function fetchSuggest(q) {
    var url = "/api/wikilink/suggest?limit=8&q=" + encodeURIComponent(q);
    // 排除当前文档自身（避免自指死链噪音，与后端 wikilink_check 自指排除对齐）
    if (window.DOC && DOC.title) url += "&exclude=" + encodeURIComponent(DOC.title);
    if (window.DOC && DOC.name) url += "&exclude=" + encodeURIComponent(DOC.name.replace(/\.md$/i, ""));
    fetch(url)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !d.ok) return close();
        // 竞态守卫：请求发出后用户又敲了字，旧响应直接丢
        if (currentQuery() !== lastQuery) return;
        items = d.items || [];
        active = 0;
        if (!items.length) { renderEmpty(); return; }
        render();
      })
      .catch(function () { close(); });
  }

  /* ---------- 渲染 ---------- */
  function kindBadge(kind) {
    return kind === "term" ? '<span class="wl-kind">术语</span>' : "";
  }
  function render() {
    ensureBox();
    box.innerHTML = items.map(function (it, i) {
      return '<div class="wl-item' + (i === active ? " on" : "") + '" role="option" data-idx="' + i + '" aria-selected="' + (i === active) + '">' +
        '<span class="wl-name">' + esc(it.name) + "</span>" + kindBadge(it.kind) +
        (it.sub_label ? '<span class="wl-sub">' + esc(it.sub_label) + "</span>" : "") +
        "</div>";
    }).join("");
    place();
    box.style.display = "";
    open = true;
  }
  function renderEmpty() {
    ensureBox();
    box.innerHTML = '<div class="wl-empty">无匹配文档 · 继续输入或 Esc 关闭</div>';
    place();
    box.style.display = "";
    open = true;
  }
  function paint() {
    if (!box) return;
    var lis = box.querySelectorAll("[data-idx]");
    for (var i = 0; i < lis.length; i++) {
      lis[i].classList.toggle("on", i === active);
      lis[i].setAttribute("aria-selected", i === active ? "true" : "false");
    }
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* ---------- 定位：镜像法测 caret 视口坐标 ---------- */
  var mirror = null;
  function caretRect() {
    if (!mirror) {
      mirror = document.createElement("div");
      mirror.setAttribute("aria-hidden", "true");
      document.body.appendChild(mirror);
    }
    var cs = getComputedStyle(ta);
    var m = mirror.style;
    m.position = "fixed"; m.visibility = "hidden"; m.whiteSpace = "pre-wrap";
    m.wordWrap = "break-word"; m.overflowWrap = "break-word";
    m.top = "0"; m.left = "0";
    m.width = ta.clientWidth + "px";
    m.font = cs.font; m.lineHeight = cs.lineHeight;
    m.padding = cs.padding; m.border = cs.border; m.boxSizing = cs.boxSizing;
    mirror.textContent = ta.value.slice(0, ta.selectionStart);
    var marker = document.createElement("span");
    marker.textContent = "​";
    mirror.appendChild(marker);
    var r = ta.getBoundingClientRect();
    var mr = marker.getBoundingClientRect();
    return {
      left: r.left + (mr.left - mirror.getBoundingClientRect().left) - ta.scrollLeft,
      top: r.top + (mr.top - mirror.getBoundingClientRect().top) - ta.scrollTop,
      lineH: parseFloat(cs.lineHeight) || 20
    };
  }
  function place() {
    var c = caretRect();
    var bw = 320, bh = Math.min(box.offsetHeight || 240, 280);
    var x = Math.max(8, Math.min(c.left, window.innerWidth - bw - 8));
    var y = c.top + c.lineH + 4;
    if (y + bh > window.innerHeight - 8) y = c.top - bh - 4; // 下方放不下翻转到上方
    box.style.left = x + "px";
    box.style.top = Math.max(8, y) + "px";
    box.style.width = bw + "px";
  }

  /* ---------- 插入 ---------- */
  function pick(i) {
    var it = items[i];
    if (!it) return;
    var pos = ta.selectionStart;
    var insert = "[[" + it.name + "]]";
    // 替换从 trigStart 到 caret 的整段（含用户已敲的查询词）
    ta.setRangeText(insert, trigStart, pos, "end");
    ta.dispatchEvent(new Event("input", { bubbles: true })); // 保持 dirty 追踪一致
    close();
    ta.focus();
  }

  function close() {
    open = false;
    trigStart = -1;
    items = [];
    lastQuery = "";
    if (box) box.style.display = "none";
  }

  /* ---------- 事件 ---------- */
  function onInput() {
    clearTimeout(debounceTimer);
    var t = detectTrigger();
    if (t < 0) { close(); return; }
    trigStart = t;
    var q = currentQuery();
    lastQuery = q;
    debounceTimer = setTimeout(function () { fetchSuggest(q); }, 120);
  }

  function onKeydown(e) {
    if (!open) return;
    if (e.key === "ArrowDown") { e.preventDefault(); if (items.length) { active = (active + 1) % items.length; paint(); } }
    else if (e.key === "ArrowUp") { e.preventDefault(); if (items.length) { active = (active - 1 + items.length) % items.length; paint(); } }
    else if (e.key === "Enter" || e.key === "Tab") {
      if (items.length) { e.preventDefault(); e.stopPropagation(); pick(active); }
    }
    else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); }
  }

  function onBlur() {
    // 延迟关闭：让 box 的 mousedown 先触发（虽然已 preventDefault，双保险）
    clearTimeout(blurTimer);
    blurTimer = setTimeout(close, 150);
  }

  function onScrollOrResize() { if (open) place(); }

  /* ---------- 挂载：编辑器打开时绑定（textarea 是静态 DOM，直接绑一次即可） ---------- */
  function init() {
    ta = $("#ed-text");
    if (!ta) return;
    ta.addEventListener("input", onInput);
    ta.addEventListener("keydown", onKeydown);
    ta.addEventListener("blur", onBlur);
    ta.addEventListener("scroll", onScrollOrResize);
    window.addEventListener("resize", onScrollOrResize);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
