/* =====================================================================
   知库 · Workbench 页面级交互（T1 产出 · frontend-redesign-tasks/T1-workbench-阅读.md）
   职责：不修改 app.js 公共段，只在页面级增强——
     [1] 文档列表密度切换（compact / comfortable，localStorage 持久化）
     [2] 阅读页增强：codeblock 顶栏（语言标签 + copy SVG）、mermaid 角标、
         字符图标（◈）→ 内联 SVG 清洗、H2 kinetic-underline（滚动时 --hairline 被 --acc 点亮）
     [3] 编辑器 overlay：删除按钮与 crumb 删除按钮的两步确认状态同步
     [4] 右 rail tabs 键盘可达（Enter/Space 触发，方向键切换）
     [5] 面板进视口 stagger reveal + Motion.refresh
   全部幂等；Motion 缺失时静态可用。
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

  /* ---------- [2] 阅读页增强 ---------- */
  function enhanceCodeblock(pre) {
    if (pre.dataset.cbBound) return;
    var code = pre.querySelector("code");
    if (!code) return;
    var lang = "text";
    var m = (code.className || "").match(/language-([\w+-]+)/);
    if (m) lang = m[1];
    else if ((code.className || "").indexOf("hljs") >= 0) {
      m = (code.className || "").match(/hljs-keyword/) ? null : null;
    }
    var wrap = document.createElement("div");
    wrap.className = "codeblock";
    var head = document.createElement("div");
    head.className = "cb-head";
    var langEl = document.createElement("span");
    langEl.className = "cb-lang";
    langEl.textContent = lang;
    var copy = document.createElement("button");
    copy.type = "button";
    copy.className = "cb-copy";
    copy.title = "复制代码";
    copy.innerHTML = SVG.replace(":id:", "i-copy-path") + "<span>复制</span>";
    copy.addEventListener("click", function () {
      var text = code.textContent || "";
      if (typeof window.copyText === "function") window.copyText(text, "代码已复制到剪贴板");
      else if (navigator.clipboard) navigator.clipboard.writeText(text).then(function () {}, function () {});
    });
    head.appendChild(langEl);
    head.appendChild(copy);
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(head);
    wrap.appendChild(pre); /* pre 原地移入，hljs 染色保留 */
    pre.dataset.cbBound = "1";
    wrap.dataset.cbBound = "1";
  }

  function enhanceMermaid(div) {
    if (div.dataset.capBound) return;
    div.dataset.capBound = "1";
    var cap = document.createElement("span");
    cap.className = "m-cap";
    cap.innerHTML = SVG.replace(":id:", "i-md-code") + "<span>mermaid</span>";
    div.appendChild(cap);
  }

  function cleanChars() {
    /* app.js 动态渲染的文档星标（◈）与 crumb 美化版（◈）→ 内联 SVG */
    $$(".doc-t .star").forEach(function (s) {
      if (s.dataset.svgBound) return;
      s.dataset.svgBound = "1";
      s.innerHTML = SVG.replace(":id:", "i-external-link");
      s.title = "有美化版";
    });
    $$("#crumb .iconbtn, #crumb a.iconbtn").forEach(function (b) {
      if (b.dataset.svgBound) return;
      if (/^\s*◈/.test(b.textContent)) {
        b.dataset.svgBound = "1";
        b.innerHTML = SVG.replace(":id:", "i-external-link") + " 美化版";
      }
    });
  }

  function enhanceArticle() {
    var art = $("#article");
    if (!art) return;
    $$("#article .a-body pre").forEach(enhanceCodeblock);
    $$("#article .mermaid").forEach(enhanceMermaid);
    /* H2 底部 hairline 随滚动被 --acc 点亮（T0 motion.js scrubUnderline） */
    $$("#article .a-body h2").forEach(function (h) {
      if (!h.hasAttribute("data-scrub-underline")) h.setAttribute("data-scrub-underline", "");
    });
    cleanChars();
    refreshMotion();
  }

  /* ---------- [3] 编辑器删除按钮状态同步（复用 app.js 两步确认） ---------- */
  var _origDelete = window.deleteDoc;
  if (typeof _origDelete === "function") {
    window.deleteDoc = function () {
      var r = _origDelete.apply(this, arguments);
      syncEditorDelete();
      if (r && typeof r.then === "function") r.then(syncEditorDelete, syncEditorDelete);
      return r;
    };
  }
  function syncEditorDelete() {
    var ed = $("#ed-del");
    if (!ed) return;
    var crumbDel = $$("#crumb .iconbtn").filter(function (b) { return b.textContent.indexOf("删除") >= 0; })[0];
    if (crumbDel) ed.innerHTML = crumbDel.innerHTML;
  }

  /* ---------- [4] rail tabs 键盘可达 ---------- */
  function bindTabs() {
    $$(".rtab").forEach(function (t) {
      if (t.dataset.kbBound) return;
      t.dataset.kbBound = "1";
      t.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); t.click(); }
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          var tabs = $$(".rtab");
          var i = tabs.indexOf(t);
          var next = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
          next.focus(); next.click();
        }
      });
    });
  }

  /* ---------- [6] 双链面板：已解析的链接加「→ 加入串学」（需求4） ---------- */
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

  /* ---------- [5] 动效刷新（幂等） ---------- */
  var motionTimer = null;
  function refreshMotion() {
    if (!window.Motion || window.Motion.reduced) return;
    clearTimeout(motionTimer);
    motionTimer = setTimeout(function () { try { window.Motion.refresh(); } catch (e) {} }, 150);
  }

  /* ---------- 变更观察：app.js 客户端路由会整体重写 doclist/article/crumb ---------- */
  var pending = false;
  function scheduleEnhance() {
    if (pending) return;
    pending = true;
    setTimeout(function () {
      pending = false;
      buildDensityToggle();
      enhanceArticle();
      cleanChars();
      bindTabs();
      enhanceRoamLinks();
    }, 60);
  }

  function init() {
    buildDensityToggle();
    enhanceArticle();
    bindTabs();
    syncEditorDelete();
    var target = document.body;
    if (window.MutationObserver) {
      new MutationObserver(function (muts) {
        for (var i = 0; i < muts.length; i++) {
          var m = muts[i];
          if (m.type !== "childList" || !m.addedNodes.length) continue;
          for (var j = 0; j < m.addedNodes.length; j++) {
            var n = m.addedNodes[j];
            if (n.nodeType !== 1) continue;
            /* 编辑器开合也会增删 hint 子树——排除 .editor 内部，避免误刷 */
            if (n.closest && n.closest("#editor") && !n.closest("#article")) continue;
            scheduleEnhance();
            return;
          }
        }
      }).observe(target, { childList: true, subtree: true });
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
