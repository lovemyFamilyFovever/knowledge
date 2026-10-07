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
   3) 深链兜底：/doc/… 直链（GH Pages 经 404.html 回落到壳）→ 客户端路由到正确文档；
      其余未知路径（已裁剪入口 /home /stats /favorites /inbox、旧书签）→ 回工作台
   4) 最小只读裁剪：注入一段 CSS 隐藏写入口
   5) 界面修正：品牌链接指向工作台；公网文案与可用引擎对齐（全文）

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
  var CUT = ["/api/stats", "/api/substats", "/api/wikilink/suggest"];
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
    if (p === "/api/dir/tree") return getJSON("data/dir-tree.json").then(function (j) {
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
    return nativeFetch(dataUrl("data/search/" + d + ".json"))
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
    'a[href$="/stats"]', 'a[href$="/favorites"]', 'a[href$="/inbox"]',
    '#kb-search-engines [data-eng="semantic"]',
  ].join(",");
  function injectReadonly() {
    document.documentElement.classList.add("kb-readonly");
    var st = document.createElement("style");
    st.id = "kb-static-readonly";
    st.textContent = ".kb-readonly " + HIDE.split(",").join(",.kb-readonly ") + "{display:none!important}"
      + "\n.kb-recent{padding:8px 12px 10px;border-bottom:1px solid rgba(128,128,128,.25)}"
      + ".kb-recent-h{font-size:12px;opacity:.55;margin:0 0 6px;letter-spacing:.02em}"
      + ".kb-recent-i{display:block;font-size:13px;line-height:1.55;padding:1px 0;color:inherit;text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
      + ".kb-recent-i:hover{color:var(--acc,#0c9a6a)}";
    (document.head || document.documentElement).appendChild(st);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectReadonly);
  } else { injectReadonly(); }

  /* ---------- ⑤ 界面修正（公网专属） ---------- */
  function fixUI() {
    var b = document.querySelector("a.brand");
    if (b) { b.href = BASE + "/"; b.title = "回到阅读工作台"; }
    var se = document.querySelector(".sb-eng");
    if (se) se.textContent = "全文";
    var qi = document.getElementById("q");
    if (qi) qi.placeholder = "检索（全文）…";
    fixLinks(document);
  }

  /* ---------- ⑥ 链接改写：根绝对路径 → KB_BASE 前缀 ----------
     本地壳里 href 多为 "/"、"/doc/…"、"/browse/…"；公网档若原样点击/中键打开
     会跳出 /knowledge/ 子路径（GH Pages 落站外 → 404）。统一改写；MutationObserver
     覆盖动态渲染（目录树、浮层）—— 用户能点到的链接在渲染后 200ms 内已带前缀。 */
  var _linkTimer = null;
  function fixLinks(root) {
    if (!BASE) return;
    var scope = root || document;
    if (!scope.querySelectorAll) return;
    var as = scope.querySelectorAll('a[href^="/"]');
    for (var i = 0; i < as.length; i++) {
      var h = as[i].getAttribute("href") || "";
      if (h.charAt(1) === "/") continue;                       // "//host" 协议相对，放过
      if (h === BASE || h.indexOf(BASE + "/") === 0) continue; // 已带前缀
      as[i].setAttribute("href", BASE + h);
    }
  }
  function watchLinks() {
    fixLinks(document);
    if (typeof MutationObserver !== "function") return;
    var obs = new MutationObserver(function () {
      if (_linkTimer) return;
      _linkTimer = setTimeout(function () { _linkTimer = null; fixLinks(document); }, 200);
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });
  }

  /* ---------- ⑦ 本机阅读进度（仅浏览器本地：最近阅读列表） ----------
     2026-10-07 用户增补：公网档要能「接着上次读」。滚动位置跳过/恢复由 app 自带的
     kb-readpos 负责（监听 .article 滚动容器）；这里只补公网档缺失的入口——
     左栏顶部「最近阅读」列表。只写 localStorage，不碰语料、不出站；换设备不同步。 */
  var RKEY = "kb-static:recent";
  function lsGet(k, d) { try { return JSON.parse(localStorage.getItem(k)) || d; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function docKeyNow() {
    var p = location.pathname;
    if (BASE && p.indexOf(BASE + "/doc/") === 0) return p.slice(BASE.length + 1);
    if (!BASE && p.indexOf("/doc/") === 0) return p.slice(1);
    return null;
  }
  function recentTitle() {
    var now = String(location.pathname || "").replace(/\.md$/, "");
    var links = document.querySelectorAll(".tree a[href]");
    for (var i = 0; i < links.length; i++) {
      if ((links[i].getAttribute("href") || "") === now) {
        var t = (links[i].textContent || "").trim();
        if (t) return t.slice(0, 60);
      }
    }
    var h = document.querySelector(".article h1");
    if (h && (h.textContent || "").trim()) return h.textContent.trim().slice(0, 60);
    return now.split("/").filter(Boolean).slice(-1)[0] || "";
  }
  function recordVisit() {
    var k = docKeyNow(); if (!k) return;
    var list = lsGet(RKEY, []).filter(function (x) { return x.k !== k; });
    list.unshift({ k: k, t: recentTitle(), ts: Date.now() });
    lsSet(RKEY, list.slice(0, 20));
    renderRecent();
  }
  function renderRecent() {
    var host = document.getElementById("kb-recent");
    if (!host) {
      var left = document.getElementById("p-left") || document.querySelector(".panel");
      if (!left) return;
      host = document.createElement("div");
      host.id = "kb-recent"; host.className = "kb-recent";
      var tree = left.querySelector(".tree");
      if (tree) left.insertBefore(host, tree); else left.appendChild(host);
    }
    var list = lsGet(RKEY, []).slice(0, 8);
    while (host.firstChild) host.removeChild(host.firstChild);
    if (!list.length) { host.style.display = "none"; return; }
    host.style.display = "";
    var hd = document.createElement("div");
    hd.className = "kb-recent-h"; hd.textContent = "最近阅读（本机）";
    host.appendChild(hd);
    for (var i = 0; i < list.length; i++) {
      var a = document.createElement("a");
      a.className = "kb-recent-i";
      a.setAttribute("href", BASE + "/" + list[i].k);
      a.textContent = list[i].t || list[i].k;
      a.title = list[i].t || list[i].k;
      host.appendChild(a);
    }
  }
  var _recentTimer = null;
  function hookRecent() {
    document.addEventListener("kb:article-rendered", function () {
      if (_recentTimer) clearTimeout(_recentTimer);
      _recentTimer = setTimeout(recordVisit, 400);
    });
  }

  /* ---------- ③ 客户端路由桥 + 深链兜底（公网专属） ----------
     app 的点击拦截正则只认裸路径（/^\/(doc|browse)\//）。壳里链接已带 KB_BASE 前缀
     （中键/刷新可用），这里用捕获监听把带前缀的点击翻译回裸路径交给 app；再给
     pushState 补前缀、给 navigate 去前缀，保证地址栏始终留在 /knowledge/ 内。 */
  var _clicksBridged = false;
  function bridgeClicks() {
    document.addEventListener("click", function (e) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
      if (!a || a.target === "_blank" || a.hasAttribute("download")) return;
      var h = a.getAttribute("href") || "";
      if (h.indexOf(BASE + "/doc/") !== 0 && h.indexOf(BASE + "/browse/") !== 0) return;
      e.preventDefault();
      if (typeof window.navigate === "function") window.navigate(h.slice(BASE.length), true);
    }, true);
  }
  var _psBridged = false, _navBridged = false;
  function bridgeRouting() {
    if (!_psBridged) {
      _psBridged = true;
      try {
        var _ps = history.pushState;
        history.pushState = function (state, title, url) {
          if (typeof url === "string" && url.charAt(0) === "/" && url.charAt(1) !== "/" &&
              BASE && url !== BASE && url.indexOf(BASE + "/") !== 0) url = BASE + url;
          return _ps.call(history, state, title, url);
        };
      } catch (e) {}
    }
    if (!_navBridged && typeof window.navigate === "function") {
      _navBridged = true;
      var _nav = window.navigate;
      window.navigate = function (url, push) {
        if (typeof url === "string" && BASE && url.indexOf(BASE + "/") === 0) {
          var raw = url.slice(BASE.length);
          if (/^\/(doc|browse)\//.test(raw)) url = raw;
        }
        return _nav.call(window, url, push);
      };
    }
  }

  /* ---------- 启动编排（幂等；先跑一次，DOMContentLoaded/load 再补跑） ---------- */
  var _linksWatched = false, _recentHooked = false, _routed = false;
  function routeNow() {
    var path = location.pathname;
    var m = path.match(/\/doc\/([^/]+)\/([^/]+)\/(.+)$/);
    if (m) {
      if (typeof window.navigate !== "function") return;   // app 未就绪：留给下一次
      if (_routed) return;
      _routed = true;
      window.navigate(path.replace(/\.md$/, ""), false);
      return;
    }
    var trimmed = path.replace(/\/+$/, "");
    if (trimmed === BASE || trimmed === BASE + "/index.html" || trimmed === BASE + "/404.html") return;
    location.replace(BASE + "/");
  }
  function onReady() {
    patchUrls();
    fixUI();
    if (!_linksWatched) { _linksWatched = true; watchLinks(); }
    if (!_clicksBridged) { _clicksBridged = true; bridgeClicks(); }
    bridgeRouting();
    if (!_recentHooked) { _recentHooked = true; hookRecent(); }
    renderRecent();
    routeNow();
  }
  onReady();
  if (document.readyState !== "complete") {
    document.addEventListener("DOMContentLoaded", onReady);
    window.addEventListener("load", onReady);
  }
})();
