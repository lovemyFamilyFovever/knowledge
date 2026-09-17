/* =====================================================================
   知库 · Workbench 页面级交互
   阶段1·问题8 收口：body 级 MutationObserver + scheduleEnhance(60ms) +
   cleanChars/enhanceCodeblock/enhanceMermaid 整层已删除——渲染方（app.js
   renderArticle/renderDocList/renderCrumb）直接产出 final-form DOM，
   codeblock 包壳与 mermaid 角标在 app.js::enhanceArticleDOM 同帧完成。
   「渲染半成品 + 事后赌时序打补丁」的隐性契约不复存在。
   本文件只保留三类真·页面级职责：
     [1] 文档列表密度切换（compact / comfortable，localStorage 持久化）
     [2] 右 rail tabs 键盘可达（Enter/Space 触发，方向键切换）
     [3] 双链面板 roam 增强（监听 app.js 的 kb:links-rendered 显式事件）
   另：编辑器删除按钮状态同步（§4，随阶段2问题11 确认交互统一后一并移除）。
   ===================================================================== */
(function () {
  "use strict";
  var $ = function (s, p) { return (p || document).querySelector(s); };
  var $$ = function (s, p) { return Array.prototype.slice.call((p || document).querySelectorAll(s)); };
  var SVG = '<svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><use href="#:id:"/></svg>';

  /* ---------- [1] 密度切换 ---------- */
  var LS_DENSITY = "kb-wb-density";
  function buildDensityToggle() {
    var head = $("#doclist-head");
    if (!head || head.dataset.built) return;
    head.dataset.built = "1";
    head.innerHTML =
      '<span class="head-cap">文档列表</span>' +
      '<div class="density-toggle" role="group" aria-label="列表密度">' +
      '<button type="button" data-d="compact" title="紧凑密度"><svg viewBox="0 0 24 24"><use href="#i-md-list"/></svg>紧凑</button>' +
      '<button type="button" data-d="comfy" title="舒适密度"><svg viewBox="0 0 24 24"><use href="#i-md-image"/></svg>舒适</button>' +
      "</div>";
    var saved = "comfy";
    try { saved = localStorage.getItem(LS_DENSITY) || "comfy"; } catch (e) {}
    applyDensity(saved);
    head.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-d]");
      if (!b) return;
      applyDensity(b.dataset.d);
      try { localStorage.setItem(LS_DENSITY, b.dataset.d); } catch (err) {}
    });
  }
  function applyDensity(d) {
    var panel = $("#p-list");
    if (!panel) return;
    panel.classList.toggle("density-compact", d === "compact");
    $$(".density-toggle button").forEach(function (b) {
      var on = b.dataset.d === d;
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  /* ---------- [2] rail tabs 键盘可达 ---------- */
  /* rtab 为原生 button（问题13）：Enter/Space 由浏览器原生触发 click，
     这里只补 tablist 惯例的 ←→ 切换；aria-selected 由 app.js tab() 维护。 */
  function bindTabs() {
    $$(".rtab").forEach(function (t) {
      if (t.dataset.kbBound) return;
      t.dataset.kbBound = "1";
      t.addEventListener("keydown", function (e) {
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          var tabs = $$(".rtab");
          var i = tabs.indexOf(t);
          var next = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
          next.focus(); next.click();
        }
      });
    });
  }

  /* ---------- [3] 双链面板：已解析的链接加「→ 加入串学」（需求4） ---------- */
  /* app.js loadLinks 渲染完成后派发 kb:links-rendered——显式事件挂点，
     替代原先 observer 对 body 变更的盲目追赶。 */
  function enhanceRoamLinks() {
    var pane = document.getElementById("pane-links");
    if (!pane) return;
    Array.prototype.forEach.call(pane.querySelectorAll("a.result[href]"), function (a) {
      if (a.dataset.roamBound) return;
      a.dataset.roamBound = "1";
      var t = a.querySelector(".doc-t");
      var name = ((t && t.textContent) || "").trim();
      if (!name) return;
      var b = document.createElement("a");
      b.className = "kb-roam-link";
      b.href = "/glossary?roam=" + encodeURIComponent(name);
      b.title = "以「" + name + "」为起点做一次串学漫游";
      b.innerHTML = SVG.replace(":id:", "i-backlink-graph") + "<span>→ 加入串学</span>";
      a.parentNode.insertBefore(b, a.nextSibling);
    });
  }
  document.addEventListener("kb:links-rendered", enhanceRoamLinks);

  /* ---------- [4] 左侧分类目录：任意域可独立收起（不强制保持一个打开） ---------- */
  /* 每个域头部加折叠箭头；点击切换 .open 并持久化，刷新/跳转后保持用户选择。
     默认全部收起；用户点哪个开哪个，系统不再强制「永远有一个打开」。 */
  var LS_TREE = "kb-tree-open";
  function treeOpenSet() {
    try {
      var raw = localStorage.getItem(LS_TREE);
      if (raw) return new Set(JSON.parse(raw));
    } catch (e) {}
    var s = new Set();
    $$("#tree .dom.open").forEach(function (el) { if (el.dataset.dom) s.add(el.dataset.dom); });
    return s;
  }
  function treePersist(set) {
    try { localStorage.setItem(LS_TREE, JSON.stringify(Array.from(set))); } catch (e) {}
  }
  function treeApply(set) {
    $$("#tree .dom").forEach(function (dom) {
      var open = set.has(dom.dataset.dom);
      dom.classList.toggle("open", open);
      var h = dom.querySelector(".dom-head");
      if (h) h.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
  function initTreeCollapse() {
    var tree = $("#tree");
    if (!tree) return;
    var set = treeOpenSet();
    treePersist(set);   // 固化首次默认（当前域展开），保证后续行为确定
    treeApply(set);
    /* 无三角箭头版：折叠交互落在「域头整行」——点击域头切换展开/收起，
       不跳转（阻止 <a> 默认行为）；点击域头内的其它热区（如拖拽）不受影响。 */
    tree.addEventListener("click", function (e) {
      var head = e.target.closest && e.target.closest(".dom-head");
      if (!head) return;
      e.preventDefault(); e.stopPropagation();   // 阻止 <a> 跳转，仅切换折叠
      var dom = head.closest(".dom");
      if (!dom) return;
      var open = dom.classList.toggle("open");
      head.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) set.add(dom.dataset.dom); else set.delete(dom.dataset.dom);
      treePersist(set);
    });
    tree.addEventListener("keydown", function (e) {
      var head = e.target.closest && e.target.closest(".dom-head");
      if (!head) return;
      if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") {
        e.preventDefault(); e.stopPropagation();
        head.click();
      }
    });
  }

  /* ---------- 动效：正文渲染完成后刷新 reveal（显式事件，非 observer） ---------- */
  document.addEventListener("kb:article-rendered", function () {
    if (!window.Motion || window.Motion.reduced) return;
    setTimeout(function () { try { window.Motion.refresh(); } catch (e) {} }, 150);
  });

  function init() {
    buildDensityToggle();
    bindTabs();
    enhanceRoamLinks(); // 服务端已渲染双链面板时（首屏直开 links tab 极少），兜底跑一次
    initTreeCollapse(); // [4] 左侧分类目录独立收起
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
