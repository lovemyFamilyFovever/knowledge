/* =====================================================================
   知库 · 编辑器 [[ 双链补全（Story 1 + Story 2 双模式）
   契约：输入 [[ 触发；调 /api/wikilink/suggest（后端现成，返回
   items:[{name,rel,kind,sub_label}]）；↑↓ 选择、Enter/Tab 插入、Esc 关闭；
   鼠标 hover/click 同步。插入 [[name]]（name=标题/词，与 fts.resolve_wikilink
   的 by_title/by_stem 解析对齐，不产生死链）。
   两种输入载体（Story 2 后 textarea 被 CM 接管并隐藏）：
     · CM 模式（KBED.active()）：事件走 KBED.on('doc'/'key'/'blur'/'state')，
       定位用 view.coordsAtPos，插入用 KBED.replaceRange。
     · textarea 模式（回落）：事件走原生 DOM listener，定位用镜像法。
   不改 app.js 保存/fm 逻辑；插入后 CM 分支自动 syncToTextarea，textarea
   分支 dispatch input，两条路都让 ED_SNAPSHOT dirty 契约看到新值。
   ===================================================================== */
(function () {
  "use strict";
  var $ = function (s, p) { return (p || document).querySelector(s); };

  var ta = null;          // textarea#ed-text
  var box = null;         // 补全下拉 DOM
  var items = [];
  var active = 0;
  var open = false;
  var trigStart = -1;     // `[[` 中第一个 [ 的下标
  var debounceTimer = 0;
  var blurTimer = 0;
  var lastQuery = "";

  /* ---------- 模式判定与位置抽象（CM / textarea 两分支） ---------- */
  function cmMode() { return !!(window.KBED && KBED.active && KBED.active()); }
  function beforeText() {
    return cmMode() ? KBED.textBeforeCursor() : ta.value.slice(0, ta.selectionStart);
  }
  function cursorPos() {
    if (cmMode()) { var s = KBED.cursorPos(); return s ? s.from : -1; }
    return ta.selectionStart;
  }
  function cursorCollapsed() {
    if (cmMode()) { var s = KBED.cursorPos(); return !!s && s.from === s.to; }
    return ta.selectionStart === ta.selectionEnd;
  }

  /* ---------- DOM ---------- */
  function ensureBox() {
    if (box) return box;
    box = document.createElement("div");
    box.className = "wl-suggest";
    box.setAttribute("role", "listbox");
    box.style.display = "none";
    document.body.appendChild(box);
    box.addEventListener("mousedown", function (e) {
      e.preventDefault(); // 抢在 blur 之前完成插入
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
    if (!cursorCollapsed()) return -1; // 有选区不触发
    var before = beforeText();
    var m = before.match(/\[\[([^\[\]\n]{0,40})$/);
    if (!m) return -1;
    return before.length - m[0].length; // `[[` 起始下标
  }

  function currentQuery() {
    if (trigStart < 0) return "";
    return beforeText().slice(trigStart + 2);
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
        if (currentQuery() !== lastQuery) return; // 竞态守卫：旧响应丢弃
        items = d.items || [];
        active = 0;
        if (!items.length) { renderEmpty(); return; }
        render();
      })
      .catch(function () { close(); });
  }

  /* ---------- 渲染 ---------- */
  function kindBadge(kind) { return kind === "term" ? '<span class="wl-kind">术语</span>' : ""; }
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

  /* ---------- 定位：CM 用 coordsAtPos（精确）；textarea 用镜像法 ---------- */
  var mirror = null;
  function caretRect() {
    if (cmMode()) {
      var v = KBED.view, pos = cursorPos();
      var c = v.coordsAtPos(pos); // 可能 null（行未渲染）
      if (c) return { left: c.left, top: c.top, lineH: Math.max(12, c.bottom - c.top) };
      // 回落：取 scroller 左上角
      var sc = v.scrollDOM.getBoundingClientRect();
      return { left: sc.left + 20, top: sc.top + 20, lineH: 20 };
    }
    // textarea 镜像法
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
    if (y + bh > window.innerHeight - 8) y = c.top - bh - 4; // 下方放不下翻到上方
    box.style.left = x + "px";
    box.style.top = Math.max(8, y) + "px";
    box.style.width = bw + "px";
  }

  /* ---------- 插入 ---------- */
  function pick(i) {
    var it = items[i];
    if (!it) return;
    var insert = "[[" + it.name + "]]";
    if (cmMode()) {
      KBED.replaceRange(trigStart, cursorPos(), insert); // 内部 dispatch + syncToTextarea
    } else {
      var pos = ta.selectionStart;
      ta.setRangeText(insert, trigStart, pos, "end");
      ta.dispatchEvent(new Event("input", { bubbles: true })); // dirty 追踪一致
      ta.focus();
    }
    close();
  }

  function close() {
    open = false;
    trigStart = -1;
    items = [];
    lastQuery = "";
    if (box) box.style.display = "none";
  }

  /* ---------- 事件处理（两模式共用） ---------- */
  function handleInput() {
    clearTimeout(debounceTimer);
    var t = detectTrigger();
    if (t < 0) { close(); return; }
    trigStart = t;
    var q = currentQuery();
    lastQuery = q;
    debounceTimer = setTimeout(function () { fetchSuggest(q); }, 120);
  }
  /* 返回 true = 已消费该按键（CM 模式下阻止默认行为） */
  function handleKey(e) {
    if (!open) return false;
    if (e.key === "ArrowDown") { if (items.length) { active = (active + 1) % items.length; paint(); } return true; }
    if (e.key === "ArrowUp") { if (items.length) { active = (active - 1 + items.length) % items.length; paint(); } return true; }
    if (e.key === "Enter" || e.key === "Tab") { if (items.length) { pick(active); return true; } return false; }
    if (e.key === "Escape") { close(); return true; }
    return false;
  }
  function handleBlur() {
    clearTimeout(blurTimer);
    blurTimer = setTimeout(close, 150); // 让 box 的 mousedown 先触发（双保险）
  }
  function handleScrollOrResize() { if (open) place(); }

  /* ---------- 挂载 ---------- */
  function init() {
    ta = $("#ed-text");
    if (!ta) return;
    // textarea 回落分支：原生 DOM 事件（CM 未接管时才触发）
    ta.addEventListener("input", function () { if (!cmMode()) handleInput(); });
    ta.addEventListener("keydown", function (e) { if (!cmMode() && handleKey(e)) { e.preventDefault(); e.stopPropagation(); } });
    ta.addEventListener("blur", function () { if (!cmMode()) handleBlur(); });
    ta.addEventListener("scroll", handleScrollOrResize);
    window.addEventListener("resize", handleScrollOrResize);
    // CM 分支：订阅桥接层事件
    if (window.KBED && KBED.on) {
      KBED.on("doc", handleInput);
      KBED.on("key", handleKey);
      KBED.on("blur", handleBlur);
      KBED.on("state", function (on) { if (!on) close(); }); // detach 时关下拉
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
