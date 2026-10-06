/* =====================================================================
   知库 · kb-static.js —— 公网静态只读适配器（合并方案 §4.2 / §4.3）
   仅静态构建产物注入（site/index.html 里由 scripts/export_static.py 插入），
   本地 Flask 从不加载本文件。

   职责：
   1) 拦截 window.fetch：
        · 读端点 → site/data/*.json（与 Flask 端点同构，导出器保证）
        · 写端点 → {ok:false,error:"READ_ONLY"}，走现成错误通道（toast）
        · /api/track、/api/recent_read → 静默 no-op
        · 只读档裁剪掉的端点 → {ok:false,error:"NOT_IN_STATIC"}（404）
   2) 覆盖 KB.util.docUrl / rawUrl 的单点实现 → 静态路径（带 KB_BASE）
   3) 深链兜底：/doc/… 直链（GH Pages 经 404.html 回落到壳）→ 客户端路由到正确文档
   4) 最小只读裁剪：注入一段 CSS 隐藏写入口

   分诊表与 scripts/export_static.py::ENDPOINT_TRIAGE 逐条对应（§4.4 静态审计同源）。
   约束（与本项目技术栈一致）：无构建工具 / 无 ES module / 经典脚本 / 全局作用域。
   ===================================================================== */
(function () {
  "use strict";
  var CFG = window.KB_STATIC;
  if (!CFG || !CFG.readonly) return;
  var BASE = CFG.base || "";

  /* ---------- 分诊表（镜像 export_static.py） ---------- */
  var READ_MAP = ["/api/tree", "/api/doc", "/api/links", "/api/palette/index",
    "/api/search", "/api/globalstats"];
  var WRITE = ["/api/save", "/api/note", "/api/favorite", "/api/tags", "/api/move",
    "/api/move/batch", "/api/delete", "/api/mkdir", "/api/rmdir", "/api/rename-sub",
    "/api/rename-domain", "/api/import", "/api/inbox/ignore", "/api/inbox/purge",
    "/api/wikilink/check"];
  var NOOP = ["/api/track", "/api/recent_read", "/api/docmark"];
  var CUT = ["/api/stats", "/api/substats", "/api/dir/tree", "/api/wikilink/suggest"];
  window.KB_STATIC.MAP_READ = READ_MAP.slice();
  window.KB_STATIC.WRITE = WRITE.slice();

  var nativeFetch = window.fetch ? window.fetch.bind(window) : null;

  function enc(s) {
    // 与 Python urllib.parse.quote(s, safe="") 对齐：再编码 ! ' ( ) *
    return encodeURIComponent(String(s)).replace(/[!'()*]/g,
      function (c) { return "%" + c.charCodeAt(0).toString(16).toUpperCase(); });
  }
  function jsonResponse(obj, status) {
    return new Response(JSON.stringify(obj), {
      status: status || 200, headers: { "Content-Type": "application/json" } });
  }
  function dataUrl(p) { return BASE + "/" + String(p).replace(/^\//, ""); }
  function getJSON(p) { return nativeFetch(dataUrl(p)).then(function (r) { return r.json(); }); }
  function readonlyResponse() {
    return jsonResponse({ ok: false, error: "READ_ONLY" }, 200);
  }
  function notInStatic(path) {
    return jsonResponse({ ok: false, error: "NOT_IN_STATIC", detail: path }, 404);
  }
  function pathOf(input) {
    var url = typeof input === "string" ? input : (input && input.url) || "";
    var p = url.split("#")[0].split("?")[0];
    if (BASE && p.indexOf(BASE + "/api/") === 0) p = p.slice(BASE.length);
    return p;
  }
  function paramsOf(input) {
    var url = typeof input === "string" ? input : (input && input.url) || "";
    var qs = url.split("?")[1] || "";
    try { return new URLSearchParams(qs.split("#")[0]); }
    catch { return new URLSearchParams(""); }
  }

  /* ---------- ① fetch 拦截 ---------- */
  if (nativeFetch) window.fetch = function (input, init) {
    var p = pathOf(input);
    if (p.indexOf("/api/") !== 0) return nativeFetch(input, init);
    var method = String((init && init.method) || (input && input.method) || "GET").toUpperCase();

    if (WRITE.indexOf(p) >= 0) return Promise.resolve(readonlyResponse());
    if (p === "/api/docmark") {
      return Promise.resolve(method === "GET"
        ? jsonResponse({ ok: true, read: false, mastered: false }) : readonlyResponse());
    }
    if (NOOP.indexOf(p) >= 0) {
      return Promise.resolve(p === "/api/recent_read"
        ? jsonResponse({ ok: true, days: [] }) : jsonResponse({ ok: true, tracked: false }));
    }
    if (CUT.indexOf(p) >= 0) return Promise.resolve(notInStatic(p));

    if (p === "/api/tree") return getJSON("data/tree.json").then(function (j) {
      return jsonResponse(j); });
    if (p === "/api/palette/index") return getJSON("data/palette/index.json").then(function (j) {
      return jsonResponse(j); });
    if (p === "/api/globalstats") return getJSON("data/meta.json").then(function (m) {
      return jsonResponse(m.stats); });
    if (p === "/api/doc") {
      var qp = paramsOf(input);
      var key = (qp.get("domain") || "") + "/" + (qp.get("sub") || "") + "/"
        + (qp.get("name") || "");
      return loadDocIndex().then(function (idx) {
        var rel = idx[key];
        if (!rel) return jsonResponse({ error: "not found" }, 404);
        return nativeFetch(dataUrl(rel)).then(function (r) {
          if (!r.ok) return jsonResponse({ error: "not found" }, 404);
          return r.json().then(function (j) { return jsonResponse(j); });
        });
      });
    }
    if (p === "/api/links") {
      var lp = paramsOf(input).get("path") || "";
      return getJSON("data/links.json").then(function (all) {
        return jsonResponse(all[lp] || { outgoing: [], incoming: [] }); });
    }
    if (p === "/api/search") return staticSearch(paramsOf(input));
    return Promise.resolve(notInStatic(p));
  };

  /* ---------- 静态检索（CJK bigram，分域懒加载） ---------- */
  var _idx = {}, _tree = null, _docIdx = null;
  function loadTree() {
    if (_tree) return Promise.resolve(_tree);
    return getJSON("data/tree.json").then(function (t) { _tree = t; return t; });
  }
  function loadDocIndex() {
    if (_docIdx) return Promise.resolve(_docIdx);
    return getJSON("data/doc/index.json").then(function (j) { _docIdx = j || {}; return _docIdx; });
  }
  function loadDomainIndex(d) {
    if (_idx[d]) return Promise.resolve(_idx[d]);
    return nativeFetch(dataUrl("data/search/" + enc(d) + ".json"))
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { _idx[d] = j; return j; })
      .catch(function () { return null; });
  }
  function tokens(text) {
    var out = {};
    String(text || "").replace(/[\u4e00-\u9fff]+/g, function (run) {
      if (run.length === 1) { out[run] = 1; }
      else { for (var i = 0; i < run.length - 1; i++) out[run.slice(i, i + 2)] = 1; }
      return run;
    });
    (String(text || "").match(/[A-Za-z0-9_]{2,}/g) || []).forEach(function (w) {
      out[w.toLowerCase()] = 1; });
    return Object.keys(out);
  }
  function staticSearch(params) {
    var raw = params.get("q") || "";
    var q = raw.charAt(0) === "?" ? raw.slice(1).trim() : raw.trim();
    var limit = parseInt(params.get("limit") || "30", 10) || 30;
    var fDom = (params.get("domain") || "").split(",").filter(Boolean);
    var fSub = (params.get("sub") || "").split(",").filter(Boolean);
    var fTag = (params.get("tag") || "").split(",").filter(Boolean);
    var toks = tokens(q);
    return loadTree().then(function (tree) {
      var doms = (tree.domains || []).map(function (d) { return d.id; });
      if (fDom.length) doms = doms.filter(function (d) { return fDom.indexOf(d) >= 0; });
      return Promise.all(doms.map(loadDomainIndex)).then(function (list) {
        var hits = [], facets = { domains: {}, subs: {}, tags: {} }, seen = {};
        list.forEach(function (ix) {
          if (!ix) return;
          var score = {};
          toks.forEach(function (t) {
            (ix.index[t] || []).forEach(function (i) { score[i] = (score[i] || 0) + 1; });
          });
          Object.keys(score).forEach(function (i) {
            var doc = ix.docs[i]; if (!doc) return;
            if (seen[doc.url]) return; seen[doc.url] = 1;
            var segs = doc.rel.split("/");
            var sub = segs.length > 2 ? segs[1] : "_root";
            var d = ix.domain;
            if (fSub.length && fSub.indexOf(sub) < 0 && fSub.indexOf(d + "/" + sub) < 0) return;
            if (fTag.length && !doc.tags.some(function (t) { return fTag.indexOf(t) >= 0; })) return;
            var tl = doc.title.toLowerCase(), ql = q.toLowerCase();
            var match = tl === ql ? "exact" : (tl.indexOf(ql) === 0 ? "prefix"
              : (tl.indexOf(ql) >= 0 ? "contains" : "body"));
            var sc = score[i];
            hits.push({ path: doc.rel, title: doc.title, url: doc.url,
              snippet: doc.excerpt || "", score_label: (match === "exact" ? "1.00" : sc.toFixed(2)),
              score: match === "exact" ? 1 : sc, domain: d, sub: sub, sub_label: sub,
              tags: doc.tags || [], match: match, hit_in_snippet: -1 });
            facets.domains[d] = (facets.domains[d] || 0) + 1;
            facets.subs[d + "/" + sub] = (facets.subs[d + "/" + sub] || 0) + 1;
            (doc.tags || []).forEach(function (t) { facets.tags[t] = (facets.tags[t] || 0) + 1; });
          });
        });
        hits.sort(function (a, b) { return b.score - a.score || (a.title < b.title ? -1 : 1); });
        var exact = hits.filter(function (x) { return x.match === "exact"; });
        var rest = hits.filter(function (x) { return x.match !== "exact"; });
        var fd = Object.keys(facets.domains).map(function (k) {
          return { id: k, label: k, n: facets.domains[k] }; })
          .sort(function (a, b) { return b.n - a.n; });
        var fs = Object.keys(facets.subs).map(function (k) {
          return { id: k, n: facets.subs[k] }; }).sort(function (a, b) { return b.n - a.n; }).slice(0, 20);
        var ft = Object.keys(facets.tags).map(function (k) {
          return { tag: k, n: facets.tags[k] }; }).sort(function (a, b) { return b.n - a.n; }).slice(0, 20);
        return jsonResponse({ ok: true, q: q, raw_q: raw, mode: "fts", engine: "fts",
          total: hits.length, took_ms: 0,
          exact: exact.slice(0, limit),
          hits: rest.slice(0, Math.max(0, limit - exact.slice(0, limit).length)),
          facets: { domains: fd, subs: fs, tags: ft },
          semantic_available: false, engines: { fts_ms: 0, rag_ms: null } });
      });
    });
  }

  /* ---------- ② docUrl / rawUrl 单点覆盖 ---------- */
  function patchUrls() {
    if (!window.KB || !KB.util) return false;
    KB.util.docUrl = function (rel) {
      var s = String(rel || "").replace(/\.md$/, "").split("/").filter(Boolean);
      if (s.length === 2) s = [s[0], "_root", s[1]];
      return BASE + "/doc/" + s.map(encodeURIComponent).join("/");
    };
    KB.util.rawUrl = function (rel) {
      return BASE + "/raw/" + String(rel || "").split("/").filter(Boolean)
        .map(encodeURIComponent).join("/");
    };
    return true;
  }
  patchUrls();

  /* ---------- ④ 只读裁剪（最小：隐藏写入口） ----------
     §4.3 的完整裁剪（顶栏项、页签、状态栏快照…）留后续阶段；此处只保证
     "能点到的写入口不存在"，与 fetch 层的 READ_ONLY 双保险。 */
  var HIDE = [
    '[onclick^="openEditor"]', '[onclick^="deleteDoc"]', '[onclick^="toggleFav"]',
    '[onclick^="jumpToTagEdit"]', '[onclick^="addNote"]', '[onclick^="removeTag"]',
    '[onclick^="toggleDocMark"]', '[onclick^="purgeInbox"]', '[onclick^="chipsAddToggle"]',
    '#editor', '#fav-btn', '#ed-del', '#tag-add-btn', '#tag-in', '#tag-inputrow',
    '.note-input', '#ni', '#global-stats-btn',
    'a[href="/stats"]', 'a[href="/favorites"]', 'a[href="/inbox"]',
  ].join(",");
  function injectReadonly() {
    document.documentElement.classList.add("kb-readonly");
    var st = document.createElement("style");
    st.id = "kb-static-readonly";
    st.textContent = ".kb-readonly " + HIDE.split(",").join(",.kb-readonly ") + "{display:none!important}";
    (document.head || document.documentElement).appendChild(st);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectReadonly);
  } else { injectReadonly(); }

  /* ---------- ③ 深链兜底 ---------- */
  function deepLink() {
    patchUrls();
    var m = location.pathname.match(/\/doc\/([^/]+)\/([^/]+)\/(.+)$/);
    if (!m || typeof window.navigate !== "function") return;
    var tail = location.pathname.replace(/\.md$/, "");
    window.navigate(tail, false);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", deepLink);
  } else { deepLink(); }
})();
