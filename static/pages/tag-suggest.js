/* =====================================================================
   知库 · 标签补全浮层（Story 4 追加：datalist → 自绘浮层）
   为什么弃 datalist：原生下拉的外观（白底/黑箭头/滚动条）浏览器不允许
   CSS 定制，与主题割裂；自绘浮层复用 [[ 双链补全的视觉 token（.tag-suggest
   与 .wl-suggest 共享样式），明暗主题自动跟随。
   交互（标准 combobox）：
     · focus/输入即弹出，按「最后一段逗号/分号之后」的文本过滤
     · ↑↓ 选择、Enter 填充当前段（返回 true=已消费，调用方不提交）
     · Esc 第一层关浮层（返回 true），调用方第二次 Esc 才收起输入框
     · Enter 无匹配项 / 浮层未开 → 返回 false，调用方走原有提交逻辑
   数据：/api/globalstats top_tags（[{tag,n}]），ensureIndex() 预热缓存。
   ===================================================================== */
(function () {
  "use strict";

  var box = null, input = null;
  var items = [];        // [{tag, n}]
  var filtered = [];
  var active = 0;
  var isOpen = false;
  var blurTimer = 0;
  var loaded = false;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function lastSepIdx(v) {
    return Math.max(v.lastIndexOf(","), v.lastIndexOf("，"),
                    v.lastIndexOf(";"), v.lastIndexOf("；"));
  }

  /* 当前过滤段：最后一个逗号/分号之后 */
  function seg() {
    return input.value.slice(lastSepIdx(input.value) + 1).trim();
  }

  function filter() {
    var q = seg().toLowerCase();
    var pre = [], inc = [];
    for (var i = 0; i < items.length && pre.length + inc.length < 60; i++) {
      var tl = items[i].tag.toLowerCase();
      if (!q || tl.indexOf(q) === 0) pre.push(items[i]);
      else if (tl.indexOf(q) >= 0) inc.push(items[i]);
    }
    filtered = pre.concat(inc).slice(0, 30);
  }

  function ensureBox() {
    if (box) return box;
    box = document.createElement("div");
    box.className = "tag-suggest";
    box.setAttribute("role", "listbox");
    box.style.display = "none";
    document.body.appendChild(box);
    box.addEventListener("mousedown", function (e) {
      e.preventDefault(); // 抢在 blur 之前完成填充
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

  function render() {
    box.innerHTML = filtered.map(function (t, i) {
      return '<div class="wl-item' + (i === active ? " on" : "") + '" role="option" data-idx="' + i +
        '" aria-selected="' + (i === active) + '">' +
        '<span class="wl-name">' + esc(t.tag) + "</span>" +
        (t.n ? '<span class="wl-sub">' + t.n + " 篇</span>" : "") +
        "</div>";
    }).join("");
    place();
    box.style.display = "";
    isOpen = true;
  }
  function paint() {
    var lis = box.querySelectorAll("[data-idx]");
    for (var i = 0; i < lis.length; i++) {
      lis[i].classList.toggle("on", i === active);
      lis[i].setAttribute("aria-selected", i === active ? "true" : "false");
    }
  }

  function place() {
    var r = input.getBoundingClientRect();
    box.style.left = r.left + "px";
    box.style.top = (r.bottom + 4) + "px";
    box.style.width = Math.max(r.width, 200) + "px";
  }

  function show(inputEl) {
    input = inputEl;
    if (!document.contains(input)) return close();
    ensureBox(); // 异步补弹（ensureIndex 回调）不经过 mousedown 等路径，box 可能尚未创建
    filter();
    if (!filtered.length) return close();
    active = 0;
    render();
  }
  function refresh() {
    if (!input) return;
    show(input); // show 内部「空过滤→close」自守；input 事件重开/重滤两用
  }
  function close() {
    isOpen = false;
    filtered = [];
    if (box) box.style.display = "none";
  }

  function pick(i) {
    var t = filtered[i];
    if (!t || !input) return;
    var v = input.value, idx = lastSepIdx(v);
    input.value = v.slice(0, idx + 1) + t.tag;
    close();
    input.focus();
  }

  /* 预热标签索引（幂等）。数据异步到达时若触发它的输入框仍持有焦点，
     立即补弹——否则 focus 先于 fetch 完成时 show 会因空索引关掉浮层，
     且 refresh 只重滤不重开，浮层从此再也弹不出来（实测坑）。 */
  function ensureIndex(inputEl) {
    if (loaded) return;
    fetch("/api/globalstats").then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
      if (d && Array.isArray(d.top_tags)) {
        items = d.top_tags;
        loaded = true;
        if (inputEl && document.activeElement === inputEl) show(inputEl);
      }
    }).catch(function () {});
  }

  /* 键盘分流：返回 true = 已消费（调用方 preventDefault，不再走提交/收起逻辑） */
  function handleKey(inputEl, e) {
    if (input !== inputEl || !isOpen) return false;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!filtered.length) return true; // 拦下，别动光标
      active = e.key === "ArrowDown"
        ? (active + 1) % filtered.length
        : (active - 1 + filtered.length) % filtered.length;
      paint();
      return true;
    }
    if (e.key === "Enter") { if (filtered.length) { pick(active); return true; } return false; }
    if (e.key === "Escape") { close(); return true; }
    return false;
  }

  function bind(inputEl) {
    inputEl.addEventListener("focus", function () {
      ensureIndex(inputEl);
      setTimeout(function () { show(inputEl); }, 0); // focus 一律 show（索引未就绪时 show 空自守，加载完由 ensureIndex 补弹）
    });
    inputEl.addEventListener("input", function () { input = inputEl; refresh(); });
    inputEl.addEventListener("blur", function () {
      clearTimeout(blurTimer);
      blurTimer = setTimeout(function () { if (input === inputEl) close(); }, 120);
    });
    /* 懒绑定场景：调用方在 focus 事件里才 bind（app.js 启动时 TagSuggest 尚未加载），
       此刻这一次 focus 事件已经派发完，新挂的监听收不到——立即补弹一次。 */
    if (document.activeElement === inputEl) {
      ensureIndex(inputEl);
      setTimeout(function () { show(inputEl); }, 0);
    }
  }

  window.TagSuggest = { bind: bind, ensureIndex: ensureIndex, handleKey: handleKey };
})();
