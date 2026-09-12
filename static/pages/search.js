/* 知库 · 搜索结果页交互（需求11 检索增强）
   职责：
   1. 顶栏搜索框语义状态（? 前缀 → #searchbox 挂 .semantic，图标换语义图标）—— 沿用 v1 行为
   2. 调 /api/search 重写结果区：facets chips（多选 + 写回 URL query 可分享）、
      exact[] 独立置顶并带「精确命中」标签、hits[] 常规列表
   3. 语义不可用时（semantic_available=false）禁用语义切换并给出人话提示
   约束：服务端渲染的初始列表留在 #kb-hits 里作无 JS / 接口失败的兜底；
         新 class 一律 kb- 前缀；不改 app.js 公共段。 */
(function () {
  "use strict";

  var KB = window.KB;
  var box = document.getElementById("searchbox");
  var input = document.getElementById("q");

  /* ---------- 1. 顶栏搜索框语义状态（保留原行为） ---------- */
  function isSemanticPage() {
    var q = new URLSearchParams(location.search).get("q") || "";
    return q.charAt(0) === "?";
  }
  function syncSemantic() {
    if (!box || !input) return;
    var semantic = /^\s*\?/.test(input.value) || isSemanticPage();
    box.classList.toggle("semantic", semantic);
    var icon = box.querySelector("svg use");
    if (icon) icon.setAttribute("href", semantic ? "#i-search-semantic" : "#i-search-magnifier");
  }
  if (input) {
    input.addEventListener("input", syncSemantic);
    input.addEventListener("focus", syncSemantic);
    syncSemantic();
  }

  /* ---------- 2. 结果区重写 ---------- */
  if (!KB || !KB.api || !KB.util) return;
  var U = KB.util, API = KB.api;

  var facetsEl = document.getElementById("kb-facets");
  var exactEl = document.getElementById("kb-exact");
  var hitsEl = document.getElementById("kb-hits");
  if (!hitsEl) return;

  var S = {
    raw: "",
    domain: splitVals(new URLSearchParams(location.search).get("domain")),
    sub: splitVals(new URLSearchParams(location.search).get("sub")),
    tag: splitVals(new URLSearchParams(location.search).get("tag")),
    items: [],
    mode: "fts",
    semantic: false
  };

  function splitVals(v) {
    if (!v) return [];
    return String(v).split(",").map(function (x) { return x.trim(); }).filter(Boolean);
  }
  function esc(s) { return U.esc(s); }
  function icon(n, s) { return U.icon(n, s); }

  function currentQ() {
    var p = new URLSearchParams(location.search);
    return p.get("q") || "";
  }

  /** 把当前筛选写回 URL（可分享），不触发整页刷新 */
  function pushUrl() {
    var usp = new URLSearchParams();
    if (S.raw) usp.set("q", S.raw);
    if (S.domain.length) usp.set("domain", S.domain.join(","));
    if (S.sub.length) usp.set("sub", S.sub.join(","));
    if (S.tag.length) usp.set("tag", S.tag.join(","));
    var qs = usp.toString();
    try { history.pushState({}, "", qs ? "/search?" + qs : "/search"); } catch (e) { /* 老浏览器忽略 */ }
  }

  function toggleIn(arr, v) {
    var i = arr.indexOf(v);
    if (i > -1) arr.splice(i, 1); else arr.push(v);
    return arr;
  }

  /* ---- 分面渲染 ---- */
  function renderFacets(facets) {
    if (!facetsEl) return;
    var groups = [
      { key: "domain", title: "域", list: (facets.domains || []).map(function (d) {
          return { id: d.id, label: d.label || d.id, n: d.n };
        }), sel: S.domain },
      { key: "sub", title: "子域", list: (facets.subs || []).map(function (s) {
          return { id: s.id, label: s.id, n: s.n };
        }), sel: S.sub },
      { key: "tag", title: "标签", list: (facets.tags || []).map(function (t) {
          return { id: t.tag, label: t.tag, n: t.n };
        }), sel: S.tag }
    ];
    var html = "";
    groups.forEach(function (g) {
      if (!g.list.length) return;
      html += '<div class="kb-facet-group"><span class="kb-facet-t">' + esc(g.title) + "</span>" +
        g.list.map(function (it) {
          var on = g.sel.indexOf(String(it.id)) > -1;
          return '<button type="button" class="kb-facet' + (on ? " on" : "") + '" data-type="' + g.key +
            '" data-id="' + esc(String(it.id)) + '" aria-pressed="' + (on ? "true" : "false") + '">' +
            esc(it.label) + '<span class="kb-facet-n">' + esc(String(it.n)) + "</span></button>";
        }).join("") + "</div>";
    });
    if (!html) { facetsEl.innerHTML = ""; facetsEl.hidden = true; return; }
    facetsEl.hidden = false;
    var active = S.domain.length + S.sub.length + S.tag.length;
    facetsEl.innerHTML = html +
      (active ? '<button type="button" class="kb-facet clear" id="kb-facet-clear" title="清空所有筛选">' +
        icon("i-clear-x-circle", 12) + "清空筛选</button>" : "");
  }

  /* ---- 结果卡渲染 ---- */
  function resultHTML(r, exact) {
    var dom = r.domain || String(r.path || "").split("/")[0] || "";
    return '<a class="result' + (exact ? " kb-exact" : "") + (S.semantic ? " info" : "") +
      '" href="' + esc(r.url || "#") + '" data-hue="' + esc(dom) + '">' +
      '<div class="rh">' +
      '  <span class="domain"><svg class="i i-11" aria-hidden="true"><use href="#i-' + esc(dom) + '-f"/></svg> ' +
      esc(dom) + "</span>" +
      '  <span class="path">' + esc(r.path || "") + "</span>" +
      (exact ? '<span class="kb-badge-exact">' + icon("i-check-circle", 11) + "精确命中</span>" : "") +
      '  <span class="score">' + (S.semantic ? "相似 " + esc(r.score_label || "") : esc(r.score_label || "")) + "</span>" +
      "</div>" +
      '<div class="title">' + esc(r.title || "") +
      (r.sub_label ? ' <span class="sub-sect">' + esc(r.sub_label) + "</span>" : "") + "</div>" +
      '<div class="snippet">' + (r.snippet || "") + "</div>" +
      ((r.tags && r.tags.length) ? '<div class="kb-res-tags">' + r.tags.slice(0, 4).map(function (t) {
        return '<span class="kb-tag mute">' + esc(t) + "</span>";
      }).join("") + "</div>" : "") +
      "</a>";
  }

  function renderResults(j) {
    var all = (j.exact || []).concat(j.hits || []);
    S.items = all;
    S.mode = j.mode || "fts";
    var picked = all.filter(function (r) {
      if (S.domain.length && S.domain.indexOf(String(r.domain || "")) < 0) return false;
      if (S.sub.length && S.sub.indexOf(String((r.domain || "") + "/" + (r.sub || ""))) < 0) return false;
      if (S.tag.length) {
        var tags = r.tags || [];
        var hit = false;
        S.tag.forEach(function (t) { if (tags.indexOf(t) > -1) hit = true; });
        if (!hit) return false;
      }
      return true;
    });
    var ex = picked.filter(function (r) { return r.match === "exact"; });
    var rest = picked.filter(function (r) { return r.match !== "exact"; });

    if (exactEl) {
      exactEl.hidden = !ex.length;
      exactEl.innerHTML = ex.length
        ? '<div class="rc-head">' + icon("i-check-circle", 13) + "精确命中 · " + ex.length +
          '<span class="n">标题与查询词完全一致</span></div><div class="results">' +
          ex.map(function (r) { return resultHTML(r, true); }).join("") + "</div>"
        : "";
    }
    if (hitsEl) {
      if (!picked.length) {
        hitsEl.innerHTML = '<div class="empty srch-empty" style="padding:26px 0">' +
          '<div class="e-title">当前筛选下没有结果</div>' +
          '<div class="e-desc">换掉一个筛选条件，或者换个关键词。</div></div>';
        return;
      }
      hitsEl.innerHTML =
        '<div class="results-col' + (S.semantic ? " info" : "") + '">' +
        '<div class="rc-head' + (S.semantic ? " info" : "") + '">' +
        '<span class="mode-ic"><svg aria-hidden="true"><use href="' +
        (S.semantic ? "#i-search-semantic" : "#i-search-magnifier") + '"/></svg></span>' +
        (S.semantic ? "语义命中" : "全部命中") + " · " + rest.length +
        '<span class="n">' + (S.semantic ? "向量近邻 · 余弦相似度" : "FTS5 关键词命中") + " · " +
        (j.took_ms == null ? "" : j.took_ms + " ms") + "</span></div>" +
        (rest.length ? '<div class="results">' + rest.map(function (r) { return resultHTML(r, false); }).join("") + "</div>" : "") +
        "</div>";
    }
  }

  function run() {
    S.raw = currentQ();
    S.semantic = S.raw.charAt(0) === "?";
    if (!S.raw.trim()) return; // 没有查询词：保留服务端渲染的空态引导

    var params = { q: S.raw, limit: 50 };
    if (S.domain.length === 1) params.domain = S.domain[0];
    if (S.sub.length === 1) params.sub = S.sub[0];
    if (S.tag.length === 1) params.tag = S.tag[0];

    API.search(params).then(function (j) {
      S.semantic = j.mode === "semantic";
      renderFacets(j.facets || {});
      renderResults(j);
      var meta = document.querySelector(".srch-meta");
      if (meta) meta.textContent = "共 " + (j.total || 0) + " 条 · " + (j.took_ms || 0) + " ms · " +
        (j.mode === "semantic" ? "语义" : "全文");
      if (S.semantic === false && S.raw.charAt(0) === "?" && j.rag_error) {
        var sw = document.querySelector(".query-chip.switch");
        if (sw) { sw.setAttribute("title", "语义检索不可用：" + j.rag_error); sw.style.opacity = ".5"; }
        if (hitsEl) hitsEl.insertAdjacentHTML("afterbegin",
          '<div class="empty srch-empty" style="padding:14px 0;text-align:left">' +
          '<div class="e-title" style="font-size:13px">已退回全文检索</div>' +
          '<div class="e-desc" style="max-width:none">' + esc(j.rag_error) +
          " —— 本地缺少语义检索依赖时属正常降级。</div></div>");
      }
    }).catch(function (e) {
      // 接口失败：保留服务端渲染的列表，只在顶部补一句提示
      if (facetsEl) facetsEl.innerHTML = '<div class="kb-facet-warn">' + icon("i-warning-triangle", 12) +
        "分面加载失败：" + esc(API.msg(e)) + "</div>";
    });
  }

  /* ---- 事件：分面 chips 多选 ---- */
  if (facetsEl) facetsEl.addEventListener("click", function (e) {
    if (e.target.closest("#kb-facet-clear")) {
      S.domain = []; S.sub = []; S.tag = [];
      pushUrl(); run();
      return;
    }
    var b = e.target.closest(".kb-facet");
    if (!b) return;
    var t = b.dataset.type, v = b.dataset.id;
    if (t === "domain") toggleIn(S.domain, v);
    else if (t === "sub") toggleIn(S.sub, v);
    else if (t === "tag") toggleIn(S.tag, v);
    pushUrl();
    run();
  });

  window.addEventListener("popstate", function () {
    S.domain = splitVals(new URLSearchParams(location.search).get("domain"));
    S.sub = splitVals(new URLSearchParams(location.search).get("sub"));
    S.tag = splitVals(new URLSearchParams(location.search).get("tag"));
    run();
  });

  run();

  /* ---------- 3. 结果列表 stagger reveal ---------- */
  if (window.Motion && typeof window.Motion.refresh === "function") {
    window.Motion.refresh();
  }
})();
