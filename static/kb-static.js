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
   4) 只读裁剪（§4.3，两层各司其职）：
        · 静态写入口 → 本文件注入的 CSS 隐藏清单（按钮、页签、导航链接、引擎钮）
        · 动态生成的写入口（右键菜单项、拖拽移动、近 7 日阅读图、编辑器快捷键）
          → app.js / kb-core.js 里的 KB_READ_ONLY 单点关掉，判据是注入的
            window.KB_STATIC.readonly，不在这里抄第二份清单
   5) 界面修正：品牌链接指向工作台；状态栏与 <title> 换成公网口径（导出时烤进去的是
      构建机的「本地阅读器 / localhost / 那一篇的子域名」）；域筛选钮按导出树裁剪

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
      // catch 挂在最外层：loadDocIndex() 自己也可能被判死（离线且 doc/index.json 没缓存过，
      // 这正是"第一次离线打开某篇"的常态），只兜内层会漏成整块空白。
      return loadDocIndex().then(function (idx) {
        var rel = idx[key];
        if (!rel) return jsonResponse({ error: "not found" }, 404);
        return nativeFetch(dataUrl(rel)).then(function (r) {
          if (!r.ok) return jsonResponse({ error: "not found" }, 404);
          return r.json().then(function (j) { return jsonResponse(j); });
        });
      }).catch(function () {
        // 走到这里 = 请求被 SW 判死（离线且这一串数据没缓存过）。别回 404：
        // 那会让阅读器报"文档可能已被删除"，而它好端端在服务器上，只是这次没网。
        return jsonResponse({ error: "OFFLINE" }, 503);
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
    '.note-input', '#ni',
    'a[href$="/stats"]', 'a[href$="/favorites"]', 'a[href$="/inbox"]',
    /* 「全库快照」按钮 2026-10-07 恢复（用户拍板）：它的数据源 /api/globalstats 早已同构
       导出，公网拿得到真数字，上一轮属过度裁剪。但面板里两处本地专属跟着挡掉——
       「月度趋势」跳 /stats（公网没这页），「收件箱待归档」是本机收件箱的状态。 */
    '.kbm-stats a[href$="/stats"]', '.gs-inbox',
    /* 引擎钮容器是 class 不是 id（轮次 51 写成 #kb-search-engines，选择器从未命中，
       公网实测「语义 RAG」钮照样在、点下去走的是全文）——混合 = 全文+语义，同理不给。 */
    '.kb-search-engines [data-eng="semantic"]', '.kb-search-engines [data-eng="hybrid"]',
  ].join(",");
  function injectReadonly() {
    document.documentElement.classList.add("kb-readonly");
    var st = document.createElement("style");
    st.id = "kb-static-readonly";
    st.textContent = ".kb-readonly " + HIDE.split(",").join(",.kb-readonly ") + "{display:none!important}"
      + "\n.kb-recent{padding:8px 12px 10px;border-bottom:1px solid rgba(128,128,128,.25)}"
      + ".kb-recent-h{font-size:12px;opacity:.55;margin:0 0 6px;letter-spacing:.02em}"
      + ".kb-recent-i{display:block;font-size:13px;line-height:1.55;padding:1px 0;color:inherit;text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
      + ".kb-recent-i:hover{color:var(--acc,#0c9a6a)}"
      /* 首页态（方案 B）：中间列换成首页面板，正文列与右栏收起；栅格两档（常规 / 左栏收起）都要给值 */
      + "\n.kb-home-on main{grid-template-columns:280px minmax(0,1fr) 0!important}"
      + ".kb-home-on main.left-off{grid-template-columns:46px minmax(0,1fr) 0!important}"
      + ".kb-home-on #p-article,.kb-home-on #p-rail{display:none!important}"
      /* 首页面板本身也必须跟着首页态开关 —— 它一旦注入就常驻 DOM，
         只收起正文列/右栏的话，点开文档后它会继续占住中间那一列、把正文挤到右栏
         （用户实拍就是这个形状）。 */
      + "#kb-home{display:none;min-width:0;overflow:auto}"
      + ".kb-home-on #kb-home{display:flex}"
      + "#kb-home .land-panel{flex:1;min-width:0}"
      /* 片段里没有取景框那一列。居中用 grid 的 justify-content，**别用 margin:0 auto** ——
         .land-grid 是 .land-panel(列 flex) 的 flex item，auto 外边距会让它退化成 fit-content，
         实测整栏被压到 291px 宽。 */
      + "#kb-home .land-grid{grid-template-columns:minmax(0,420px);justify-content:center;"
      + "align-content:start;max-width:none;margin:0;padding:56px 20px}"
      + "#kb-home .land-cards{display:none}";
    (document.head || document.documentElement).appendChild(st);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectReadonly);
  } else { injectReadonly(); }

  /* ---------- ⑤ 界面修正（公网专属） ----------
     文案的权威仍是 base.html / app.js 那一份，这里只做"公网该说什么"的替换：
     导出时烤进产物的字符串是本地实例的口径（statusbar 写「本地阅读器」、右端地址
     是构建机看到的 localhost、<title> 冻结在导出时那一篇的子域名），照搬上线就是假信息。 */
  var RO_TAG = "公网只读档";
  /* 状态栏四段在 375px 档是横向滚动的（.statusbar{overflow-x:auto}），
     所以公网措辞按"不比本地版更长"来定：本地实测 sb-src 225px / sb-fts 106px，
     初稿写成「本档为只读快照（编辑与统计在本地阅读器）」把溢出从 105px 顶到 272px。 */
  function fixCopy() {
    var acc = document.querySelector(".sb-acc");
    if (acc) acc.textContent = "知库 · " + RO_TAG;
    var src = document.querySelector(".sb-src");
    if (src) src.textContent = "Markdown 唯一事实源 · 本档只读";
    var fts = document.querySelector(".sb-fts");
    if (fts) {
      var m = (fts.textContent || "").match(/\d+/);
      if (m) fts.textContent = m[0] + " 篇可全文检索";
    }
    var host = document.querySelector(".sb-host");
    if (host && location.host) host.textContent = location.host;
  }
  function fixTitle() {
    var onHome = document.documentElement.classList.contains("kb-home-on");
    var h1 = onHome ? null : document.querySelector(".article h1");
    var t = h1 ? (h1.textContent || "").trim() : "";
    document.title = t ? t.slice(0, 60) + " · 知库" : "知库 · " + RO_TAG;
  }
  /* 域筛选钮：模板按 taxonomy 全量 LABELS 派生（不变量 5），公网语料却是公开白名单，
     两者不等 —— projects / handbook 这类没进白名单的域会留一颗恒 0 结果的钮，
     还顺带告诉访客"这里有个看不见的域"。判据用导出树里真实存在的域，不抄第二份名单。
     （浮层里原先还有「仅收藏」「仅未掌握」两颗空转钮，2026-10-07 连模板一起删了。） */
  function pruneScopeChips(tree) {
    var ids = {};
    ((tree && tree.domains) || []).forEach(function (d) { ids[d.id] = 1; });
    var chips = document.querySelectorAll(".kb-scope-chip[data-scope]");
    for (var i = chips.length - 1; i >= 0; i--) {
      var s = chips[i].getAttribute("data-scope") || "";
      if (s === "" || ids[s]) continue;
      chips[i].parentNode.removeChild(chips[i]);
    }
  }
  function fixUI() {
    var b = document.querySelector("a.brand");
    if (b) { b.href = BASE + "/"; b.title = "回到阅读工作台"; }
    var se = document.querySelector(".sb-eng");
    if (se) se.textContent = "全文";
    var qi = document.getElementById("q");
    if (qi) qi.placeholder = "检索（全文）…";
    var so = document.getElementById("kb-so-q");
    if (so) so.placeholder = "检索正文 / 标签…";
    fixCopy();
    fixTitle();
    loadTree().then(pruneScopeChips).catch(function () {});
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
      if (!atRoot()) hideHome();                     // 真的打开文档了 → 首页让位（根路径上不动）
      fixTitle();                                    // 标题跟着正文走：导出时冻结的 <title> 是构建机那一篇
      if (_recentTimer) clearTimeout(_recentTimer);
      _recentTimer = setTimeout(recordVisit, 400);
    });
  }

  /* ---------- ⑧ 公网首页（方案 B：单壳 + 首页片段） ----------
     根路径不再停在"导出时恰好烤进来的那一篇"，而是本地首页那一屏。片段来自
     app/templates/landing_panel.html（导出器以 home_readonly=True 渲染成 data/home.html），
     与本地 landing 同一份标记，这里不复制第二份模板；公网只留两行能用的：
     「搜索」= 开现成的检索浮层并带上输入，「继续上次阅读」= app 自己写的 localStorage
     kb-last-doc（缺席时回退到本适配器的最近阅读首条）。收件箱/本月统计/架构图取景框
     在片段渲染时就不存在（公网没有 /inbox、/stats，也没有本地 reading.db）。 */
  var _homeNode = null, _homePromise = null;
  /* 首页那一屏的样式在 pages/landing.css 里，而阅读壳只带 workbench.css —— 不补这一份，
     注入进来的片段就是一堆裸元素（实测：搜索框退化成原生 input、卡片边框与药丸全没了）。 */
  function ensureHomeCss() {
    if (document.getElementById("kb-home-css")) return;
    var l = document.createElement("link");
    l.id = "kb-home-css";
    l.rel = "stylesheet";
    l.href = dataUrl("static/pages/landing.css");
    (document.head || document.documentElement).appendChild(l);
  }
  function homeHost() {
    if (_homeNode && _homeNode.isConnected) return _homeNode;
    var art = document.getElementById("p-article");
    if (!art || !art.parentNode) return null;
    _homeNode = document.createElement("div");
    _homeNode.id = "kb-home";
    art.parentNode.insertBefore(_homeNode, art);
    return _homeNode;
  }
  function loadHome() {
    if (_homePromise) return _homePromise;
    _homePromise = nativeFetch
      ? nativeFetch(dataUrl("data/home.html"))
        .then(function (r) { return r.ok ? r.text() : ""; })
        .catch(function () { return ""; })
      : Promise.resolve("");
    return _homePromise;
  }
  /* 「继续上次阅读」每次进首页都要重算 —— 片段只注入一次，若在注入那一刻算，
     用户读完一篇再点「阅读」回来时链接还是空的（实测踩过：kb-last-doc 已有值但钮仍 hidden）。
     本地 landing 没这问题，它是整页加载，每次都是新的一次注入。 */
  function syncContinue(host) {
    var cont = host && host.querySelector("#land-continue");
    if (!cont) return;
    var last = "";
    try { last = localStorage.getItem("kb-last-doc") || ""; } catch (e) {}
    if (!last) {
      var rec = lsGet(RKEY, [])[0];
      if (rec) last = "/" + rec.k;
    }
    if (!last) { cont.hidden = true; return; }
    cont.setAttribute("href", last.charAt(0) === "/" ? BASE + last : last);
    cont.hidden = false;
  }
  function wireHome(root) {
    var f = root.querySelector(".land-box");
    if (f) f.addEventListener("submit", function (e) {
      e.preventDefault();                            // 公网没有 /search 那一页
      var q = (f.querySelector("input[name=q]") || {}).value || "";
      if (typeof window.soOpen !== "function") return;
      window.soOpen();
      var so = document.getElementById("kb-so-q");
      if (so) so.value = q;
      if (typeof window.soRun === "function" && q) window.soRun();
    });
  }
  function showHome() {
    var host = homeHost();
    if (!host) return;
    ensureHomeCss();
    loadHome().then(function (html) {
      if (!html) return;                             // 片段没拿到：留在正文，别把屏幕清空
      if (!host.childElementCount) {
        host.innerHTML = html;
        wireHome(host);
        fixLinks(host);
      }
      syncContinue(host);
      document.documentElement.classList.add("kb-home-on");
      fixTitle();
    });
  }
  function hideHome() {
    document.documentElement.classList.remove("kb-home-on");
  }
  function atRoot() {
    var p = location.pathname.replace(/\/+$/, "");
    return p === BASE || p === BASE + "/index.html" || p === BASE + "/404.html" || !p;
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
      /* 「阅读」与品牌链接指向站根：不整页重载，直接切回首页态 */
      if (h === BASE || h === BASE + "/" || h === BASE + "/index.html") {
        e.preventDefault();
        if (location.pathname.replace(/\/+$/, "") !== BASE) {
          try { history.pushState(null, "", BASE + "/"); } catch (err) {}
        }
        showHome();
        return;
      }
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
          var r = _ps.call(history, state, title, url);
          /* app 把地址推到非根（打开文档 / 切子域）→ 首页让位。
             走 pushState 而不是只靠 kb:article-rendered：/browse 那一屏不发这个事件。 */
          if (typeof url === "string" && url !== BASE && url !== BASE + "/") hideHome();
          return r;
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
    if (trimmed === BASE || trimmed === BASE + "/index.html" || trimmed === BASE + "/404.html") {
      showHome();                                    // 根路径 = 首页那一屏（方案 B）
      return;
    }
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
