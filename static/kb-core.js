/* =====================================================================
   知库 · kb-core.js —— 全局基座（全站生效）
   只暴露一个全局对象：window.KB = { api, palette, keys, prefs, wl, util }

   约束（与本项目技术栈一致，勿改）：
   - 无构建工具 / 无 ES module / 无 npm / 无 CDN：<script src defer> 直挂，全局作用域
   - 跨文件只能靠 window.* 与顶层 function 声明；本文件自给自足，不依赖 app.js 的 const
   - 新增 class 前缀 kb-，新增 id 前缀 kb-；不复用 #q #toast #theme-btn #article #doclist
   - 图标一律内联 SVG 引用 base.html 的精灵表 #i-<name>，零 emoji、零外链
   结构索引：
   [1] util  [2] api  [3] prefs（需求9 阅读偏好）  [4] palette（需求5 命令面板）
   [5] keys（需求7 键盘导航）  [6] wl（需求6 双链补全 + 断链提示）  [7] 启动
   ===================================================================== */
(function () {
  "use strict";
  if (window.KB && window.KB.__coreLoaded) return;
  var KB = (window.KB = window.KB || {});
  KB.__coreLoaded = true;
  KB.VERSION = 2; // v2：KB.overlay 原语 + palette 客户端路由 + dropCache

  /* ==================================================================
     [1] util —— 被 pages/*.js 复用（app.js 的 $ / esc / toast 是 const，外部读不到）
     ================================================================== */
  var util = (KB.util = {});

  util.$ = function (sel, root) { return (root || document).querySelector(sel); };
  util.$$ = function (sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  };
  util.esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  /* 后端 PALETTE_COMMANDS 会返回 #i-home 等图标名；base.html 精灵表里已补齐对应 symbol，
     这里只做一次「精灵表里查得到」的存在性校验，查不到就降级成不画图标（不再用别名顶替）。 */
  util.hasIcon = function (name) {
    return !!(name && document.getElementById(name));
  };
  util.icon = function (name, size) {
    var px = size || 14;
    var inner = util.hasIcon(name)
      ? '<use href="#' + util.esc(name) + '"/>'
      : "";
    return '<svg class="i" width="' + px + '" height="' + px + '" viewBox="0 0 24 24" fill="none" ' +
      'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" ' +
      'aria-hidden="true" style="flex:none">' + inner + '</svg>';
  };
  util.debounce = function (fn, ms) {
    var t = null;
    return function () {
      var self = this, a = arguments;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(self, a); }, ms == null ? 200 : ms);
    };
  };
  util.docUrl = function (rel) {
    var s = String(rel || "").replace(/\.md$/, "").split("/").filter(Boolean);
    if (s.length === 2) s = [s[0], "_root", s[1]];
    return "/doc/" + s.map(encodeURIComponent).join("/");
  };
  /* /raw 唯一实现：逐段 encode。app.js 与 pages/* 一律转调，不得再各写一份（问题7/8） */
  util.rawUrl = function (rel) {
    return "/raw/" + String(rel || "").split("/").filter(Boolean).map(encodeURIComponent).join("/");
  };
  util.toast = function (msg, ms) {
    var t = document.getElementById("toast");
    if (!t) return;
    t.innerHTML = msg;
    t.classList.add("show");
    clearTimeout(t._kbh);
    t._kbh = setTimeout(function () { t.classList.remove("show"); }, ms || 2600);
  };
  util.getJSON = function (key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      if (!raw) return fallback;
      var v = JSON.parse(raw);
      return v == null ? fallback : v;
    } catch (e) { return fallback; }
  };
  util.setJSON = function (key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); return true; } catch (e) { return false; }
  };
  util.clamp = function (v, lo, hi) {
    v = Number(v);
    if (isNaN(v)) return lo;
    return v < lo ? lo : (v > hi ? hi : v);
  };
  util.dueText = function (days) {
    days = Number(days || 0);
    if (days <= 0) return "稍后再见";
    if (days === 1) return "1 天后再见";
    if (days < 30) return days + " 天后再见";
    if (days < 365) return Math.round(days / 30) + " 个月后再见";
    return (days / 365).toFixed(1) + " 年后再见";
  };
  util.focusSearch = function () {
    var q = document.getElementById("q");
    if (q) { q.focus(); if (q.select) q.select(); }
  };
  util.isEditable = function (el) {
    if (!el) return false;
    if (el.isContentEditable) return true;
    var t = el.tagName;
    return t === "INPUT" || t === "TEXTAREA" || t === "SELECT";
  };

  /* ==================================================================
     [1.5] overlay —— 弹层原语（问题13：弹层无焦点管理的统一收口）
     KB.overlay.open({ className, html, onClose, initialFocus })
       → { root, close(reason) }
     契约：插入 body 的容器带 role=dialog / aria-modal；Tab 被困在弹层内；
     Esc 关闭并回调 onClose("esc")；关闭后焦点归还打开前的元素。
     所有弹层（kbModal / 统计 / 右键菜单 / 美化版弹窗）必须经此原语，
     不得再各写一套 Esc 监听（此前 overlay 不聚焦导致 Esc「碰巧能用」）。
     ================================================================== */
  var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
  KB.overlay = { openCount: 0, open: function (opt) {
    opt = opt || {};
    KB.overlay.openCount++;
      var lastFocus = document.activeElement;
      var root = document.createElement("div");
      root.className = opt.className || "kbm-ov";
      root.setAttribute("role", "dialog");
      root.setAttribute("aria-modal", "true");
      if (opt.html != null) root.innerHTML = opt.html;
      document.body.appendChild(root);
      var closed = false;
      function onKey(e) {
        if (e.key === "Escape") { e.stopPropagation(); e.preventDefault(); close("esc"); return; }
        if (e.key !== "Tab" || closed) return;
        var f = Array.prototype.filter.call(root.querySelectorAll(FOCUSABLE), function (x) { return x.offsetParent !== null; });
        if (!f.length) return;
        var first = f[0], last = f[f.length - 1];
        if (e.shiftKey && (document.activeElement === first || !root.contains(document.activeElement))) {
          e.preventDefault(); last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault(); first.focus();
        }
      }
      function close(reason) {
        if (closed) return;
        closed = true;
        KB.overlay.openCount--;
        document.removeEventListener("keydown", onKey, true);
        if (root.parentNode) root.remove();
        if (opt.returnFocus !== false && lastFocus && typeof lastFocus.focus === "function") {
          try { lastFocus.focus(); } catch (e) {}
        }
        if (opt.onClose) opt.onClose(reason);
      }
      document.addEventListener("keydown", onKey, true);
      var init = typeof opt.initialFocus === "function" ? opt.initialFocus(root) : null;
      var target = init || root.querySelector(FOCUSABLE);
      if (target) { try { target.focus(); } catch (e) {} }
      return { root: root, close: close };
    }
  };

  /* ==================================================================
     [2] api —— 全部后端接口的 fetch 封装，统一 ok/error 信封
     ================================================================== */
  var ERR_TEXT = {
    BAD_PARAM: "参数有问题",
    BAD_Q: "查询词为空或不可解析",
    BAD_CARD: "找不到这张卡片",
    NOT_SYNCED: "卡片库还没准备好，稍等几秒再试",
    SYNC_BUSY: "正在抽卡同步中，稍等几秒",
    CORPUS_EMPTY: "语料里还没有可学的卡片",
    PATH_ESCAPE: "路径越出了 content/",
    RAG_UNAVAILABLE: "语义检索不可用，已退回全文检索",
    INTERNAL: "服务内部错误"
  };

  function ApiError(code, detail, http) {
    this.name = "ApiError";
    this.code = code || "INTERNAL";
    this.detail = detail || "";
    this.http = http || 0;
    this.message = code + " " + (detail || "");
  }
  ApiError.prototype = Object.create(Error.prototype);
  ApiError.prototype.constructor = ApiError;

  function buildUrl(path, params) {
    if (!params) return path;
    var usp = new URLSearchParams();
    Object.keys(params).forEach(function (k) {
      var v = params[k];
      if (v === null || v === undefined || v === "") return;
      usp.append(k, String(v));
    });
    var qs = usp.toString();
    return qs ? path + "?" + qs : path;
  }

  /** 统一请求：成功返回业务 JSON；失败抛 ApiError（code 已归一）。 */
  function request(method, path, opts) {
    opts = opts || {};
    var init = { method: method, credentials: "same-origin", headers: {} };
    if (opts.body) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(opts.body);
    }
    return fetch(buildUrl(path, opts.params), init).then(function (r) {
      return r.json().catch(function () {
        throw new ApiError("INTERNAL", "响应不是合法 JSON", r.status);
      }).then(function (j) {
        if (!r.ok || j.ok === false) {
          throw new ApiError(j.error || "INTERNAL", j.detail || j.error || "", r.status);
        }
        return j;
      });
    });
  }

  var api = (KB.api = {
    ApiError: ApiError,
    /** 错误码 → 中文人话（detail 有值时附在后面） */
    msg: function (e) {
      if (!e) return "未知错误";
      var base = ERR_TEXT[e.code] || (e.code ? "请求失败（" + e.code + "）" : "请求失败");
      return e.detail ? base + "：" + e.detail : base;
    },
    sync: function (force) { return request("POST", "/api/learn/sync", { body: { force: !!force } }); },
    due: function (p) { return request("GET", "/api/learn/due", { params: p }); },
    review: function (b) { return request("POST", "/api/learn/review", { body: b }); },
    mastery: function (p) { return request("GET", "/api/learn/mastery", { params: p }); },
    today: function (p) { return request("GET", "/api/learn/today", { params: p }); },
    roam: function (p) { return request("GET", "/api/learn/roam", { params: p }); },
    wlSuggest: function (p) { return request("GET", "/api/wikilink/suggest", { params: p }); },
    wlCheck: function (b) { return request("POST", "/api/wikilink/check", { body: b }); },
    palette: function (p) { return request("GET", "/api/palette/index", { params: p }); },
    glossary: function (p) { return request("GET", "/api/glossary", { params: p }); },
    search: function (p) { return request("GET", "/api/search", { params: p }); }
  });

  /* ==================================================================
     [3] prefs —— 需求9 阅读偏好（localStorage['kb-readpref']）
     只写 4 个 CSS 变量；主题永远走 applyTheme() + kb-theme，不进这里
     ================================================================== */
  var LS_PREF = "kb-readpref";
  /* 行宽限宽已取消（用户要求正文撑满）——measure 保留为 null 仅作旧 localStorage 兼容，
     get()/set()/apply() 均忽略它，--kb-measure 恒为 none。
     2026-09-20 扩容（用户要求设置弹窗精细化）：新增标题字号 h1s/h2s/h3s（rem）、
     代码字号 code（px）、一级标题对齐 halign；默认值与 style.css [8] 区原始硬值一致，
     不动偏好时渲染零变化。 */
  var PREF_DEF = { scale: 1.0, font: "sans", line: 1.75, h1s: 1.55, h2s: 1.3, h3s: 1.12, code: 13, halign: "center" };
  var NUM_RANGE = { scale: [0.85, 1.6], line: [1.3, 2.4], h1s: [1.2, 2.4], h2s: [1.0, 1.8], h3s: [0.9, 1.5], code: [11, 17] };
  var FONT_MAP = { sans: "var(--f-body)", serif: "var(--f-disp)", mono: "var(--f-mono)" };

  function prefNum(v, key) {
    var r = NUM_RANGE[key];
    return (v == null || v === "" || isNaN(v)) ? PREF_DEF[key] : util.clamp(Number(v), r[0], r[1]);
  }

  var prefs = (KB.prefs = {
    LS: LS_PREF,
    def: function () { return Object.assign({}, PREF_DEF); },
    get: function () {
      var v = util.getJSON(LS_PREF, null) || {};
      /* 注意：字段缺失时必须显式回落到 PREF_DEF。
         不能写成 `clamp(v.scale, 0.85, 1.6) || PREF_DEF.scale` —— clamp 对 undefined 返回 lo（0.85），
         而 0.85 是 truthy，|| 永远不生效，会导致首次访问的用户拿到 0.85 倍字号 / 520px 行宽。 */
      var out = {};
      Object.keys(NUM_RANGE).forEach(function (k) { out[k] = prefNum(v[k], k); });
      out.font = FONT_MAP[v.font] ? v.font : PREF_DEF.font;
      out.halign = (v.halign === "left" || v.halign === "center") ? v.halign : PREF_DEF.halign;
      return out;
    },
    set: function (patch) {
      var cur = prefs.get();
      Object.keys(patch || {}).forEach(function (k) { cur[k] = patch[k]; });
      Object.keys(NUM_RANGE).forEach(function (k) { cur[k] = prefNum(cur[k], k); });
      if (!FONT_MAP[cur.font]) cur.font = PREF_DEF.font;
      if (cur.halign !== "left" && cur.halign !== "center") cur.halign = PREF_DEF.halign;
      util.setJSON(LS_PREF, cur);
      prefs.apply();
      return cur;
    },
    reset: function () {
      util.setJSON(LS_PREF, PREF_DEF);
      prefs.apply();
      return prefs.get();
    },
    /** 只写 CSS 变量到 documentElement.style（内联优先级最高，不用 !important）。
        行宽限宽已取消：--kb-measure 恒为 none（正文撑满），不再由偏好控制。 */
    apply: function () {
      var p = prefs.get(), s = document.documentElement.style;
      s.setProperty("--kb-fs-scale", String(p.scale));
      s.setProperty("--kb-measure", "none");
      s.setProperty("--kb-font", FONT_MAP[p.font] || FONT_MAP.sans);
      s.setProperty("--kb-line", String(p.line));
      s.setProperty("--kb-h1-size", p.h1s + "rem");
      s.setProperty("--kb-h2-size", p.h2s + "rem");
      s.setProperty("--kb-h3-size", p.h3s + "rem");
      s.setProperty("--kb-code-size", p.code + "px");
      s.setProperty("--kb-h1-align", p.halign);
      return p;
    },
    /** 设置面板 HTML：界面风格（皮肤格）→ 阅读排版 → 标题与代码 → 恢复默认 */
    panelHTML: function () {
      var p = prefs.get();
      var opt = function (v, label) {
        return '<option value="' + v + '"' + (p.font === v ? " selected" : "") + ">" + util.esc(label) + "</option>";
      };
      var skinSec = "";
      if (window.KB_SKINS && window.applySkin) {
        var curSkin = window.applySkin && (function () { try { return localStorage.getItem("kb-skin") || "celadon"; } catch (e) { return "celadon"; } })();
        skinSec = '<div class="kb-pref-head">' + util.icon("i-palette", 14) + "界面风格<span class=\"kb-pref-kbd-hint\">深浅色用顶栏太阳按钮切换</span></div>" +
          '<div class="kb-skin-grid kb-pref-skins">' + window.KB_SKINS.map(function (s) {
            // 双色点用模板字面量整段注入（check_dangling_tokens 的正则不识别跨字符串拼接的 style 值）
            return `<button type="button" class="kb-skin-card${s.id === curSkin ? " on" : ""}" data-skin="${util.esc(s.id)}">
              <span class="kb-skin-dot" style="--sd-a:${s.a};--sd-b:${s.b}"></span>
              <span><b>${util.esc(s.name)}</b><i>${util.esc(s.desc)}</i></span></button>`;
          }).join("") + "</div>";
      }
      var row = function (id, label, min, max, step, val, fmt) {
        return '<div class="kb-pref-row">' +
          '<label for="kb-pref-' + id + '">' + label + "</label>" +
          '<input type="range" id="kb-pref-' + id + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + val + '">' +
          '<output id="kb-pref-' + id + '-o">' + fmt(val) + "</output></div>";
      };
      var f2 = function (v) { return Number(v).toFixed(2); };
      var px = function (v) { return v + "px"; };
      /* 2026-09-20：抽屉顶部改 tab 切换（用户要求，参考 draw.io 属性面板页签）——
         look=界面风格，type=阅读排版+标题与代码；快捷键页签由 settings.open 追加。 */
      return '<section class="kb-set-sec" data-sec="look">' + skinSec + "</section>" +
        '<section class="kb-set-sec" data-sec="type" hidden>' +
        '<div class="kb-pref-head">' + util.icon("i-toc-list", 14) + "阅读排版</div>" +
        '<div class="kb-pref-row">' +
        '  <label for="kb-pref-scale">正文字号</label>' +
        '  <input type="range" id="kb-pref-scale" min="0.85" max="1.6" step="0.05" value="' + p.scale + '">' +
        '  <output id="kb-pref-scale-o">' + f2(p.scale) + '×</output>' +
        "</div>" +
        '<div class="kb-pref-row">' +
        '  <label for="kb-pref-line">行高</label>' +
        '  <input type="range" id="kb-pref-line" min="1.3" max="2.4" step="0.05" value="' + p.line + '">' +
        '  <output id="kb-pref-line-o">' + f2(p.line) + "</output>" +
        "</div>" +
        '<div class="kb-pref-row">' +
        '  <label for="kb-pref-font">正文字体</label>' +
        '  <select id="kb-pref-font">' + opt("sans", "无衬线（默认）") + opt("serif", "衬线 Georgia") + opt("mono", "等宽") + "</select>" +
        '  <output aria-hidden="true"></output>' +
        "</div>" +
        '<div class="kb-pref-head">' + util.icon("i-md-h1", 14) + "标题与代码</div>" +
        row("h1s", "一级标题", 1.2, 2.4, 0.05, p.h1s, f2) +
        row("h2s", "二级标题", 1.0, 1.8, 0.05, p.h2s, f2) +
        row("h3s", "三级标题", 0.9, 1.5, 0.02, p.h3s, f2) +
        row("code", "代码字号", 11, 17, 1, p.code, px) +
        '<div class="kb-pref-row">' +
        '  <label for="kb-pref-halign">标题对齐</label>' +
        '  <select id="kb-pref-halign">' +
        '<option value="center"' + (p.halign === "center" ? " selected" : "") + ">居中</option>" +
        '<option value="left"' + (p.halign === "left" ? " selected" : "") + ">居左</option></select>" +
        '  <output aria-hidden="true"></output>' +
        "</div>" +
        '<div class="kb-pref-foot">' +
        '  <button type="button" class="mbtn ghost" id="kb-pref-reset">恢复默认</button>' +
        '  <span class="kb-pref-note">偏好存 localStorage，不写语料文件</span>' +
        "</div></section>";
    },
    /** 绑定面板内控件（每次显示面板时调用一次，幂等） */
    bindPanel: function (root) {
      if (!root || root.dataset.bound) return;
      root.dataset.bound = "1";
      var slider = function (id, key, fmt) {
        var el = root.querySelector("#kb-pref-" + id);
        if (!el) return;
        el.addEventListener("input", function () {
          var o = root.querySelector("#kb-pref-" + id + "-o");
          if (o) o.textContent = fmt(el.value);
          var patch = {}; patch[key] = Number(el.value);
          prefs.set(patch);
        });
      };
      slider("scale", "scale", function (v) { return Number(v).toFixed(2) + "×"; });
      slider("line", "line", function (v) { return Number(v).toFixed(2); });
      slider("h1s", "h1s", function (v) { return Number(v).toFixed(2); });
      slider("h2s", "h2s", function (v) { return Number(v).toFixed(2); });
      slider("h3s", "h3s", function (v) { return Number(v).toFixed(2); });
      slider("code", "code", function (v) { return v + "px"; });
      var font = root.querySelector("#kb-pref-font");
      if (font) font.addEventListener("change", function () { prefs.set({ font: font.value }); });
      var halign = root.querySelector("#kb-pref-halign");
      if (halign) halign.addEventListener("change", function () { prefs.set({ halign: halign.value }); });
      var skins = root.querySelector(".kb-pref-skins");
      if (skins) skins.addEventListener("click", function (e) {
        var card = e.target.closest(".kb-skin-card");
        if (!card || !window.applySkin) return;
        window.applySkin(card.dataset.skin);
        skins.querySelectorAll(".kb-skin-card").forEach(function (x) { x.classList.toggle("on", x === card); });
      });
      var reset = root.querySelector("#kb-pref-reset");
      if (reset) reset.addEventListener("click", function () {
        var d = prefs.reset();
        root.querySelectorAll("input[type=range]").forEach(function (el) {
          var key = el.id.replace("kb-pref-", "");
          if (d[key] != null) el.value = d[key];
        });
        var so = root.querySelector("#kb-pref-scale-o"); if (so) so.textContent = d.scale.toFixed(2) + "×";
        var lo = root.querySelector("#kb-pref-line-o"); if (lo) lo.textContent = d.line.toFixed(2);
        var h1 = root.querySelector("#kb-pref-h1s-o"); if (h1) h1.textContent = d.h1s.toFixed(2);
        var h2 = root.querySelector("#kb-pref-h2s-o"); if (h2) h2.textContent = d.h2s.toFixed(2);
        var h3 = root.querySelector("#kb-pref-h3s-o"); if (h3) h3.textContent = d.h3s.toFixed(2);
        var co = root.querySelector("#kb-pref-code-o"); if (co) co.textContent = d.code + "px";
        var f = root.querySelector("#kb-pref-font"); if (f) f.value = d.font;
        var ha = root.querySelector("#kb-pref-halign"); if (ha) ha.value = d.halign;
        util.toast("阅读偏好已恢复默认");
      });
    }
  });

  /* ==================================================================
     [4] palette —— 需求5 命令面板（Ctrl/Cmd+K）
     DOM 容器：<div id="kb-palette">（base.html 里）
     ================================================================== */
  var LS_PAL = "kb-palette";
  var GROUP_META = [
    /* 阶段5 职责收窄（授权 #4）：命令/动作为主组，文档检索降为次级 section；
       Ctrl+K 搜文档能力保留（docs max 8→6，terms 靠后），不硬删 */
    { key: "commands", title: "命令", max: 6, icon: "i-palette" },
    { key: "subs", title: "子域", max: 4, icon: "i-scope-domain" },
    { key: "terms", title: "术语", max: 6, icon: "i-sort-alpha" },
    { key: "docs", title: "文档", max: 6, icon: "i-file" }
  ];

  var palette = (KB.palette = {
    data: null,        // {sig, terms, docs, subs, commands, counts}
    flat: [],          // 当前可见的扁平结果（供 ↑↓ 选择）
    sel: 0,
    open: false,
    loading: false
  });

  function palRoot() { return document.getElementById("kb-palette"); }

  /** 本地打分：精确 100 > 前缀 90 > 包含 70 > 子序列 45；不匹配返回 -1 */
  function scoreText(text, q) {
    var t = String(text || "").toLowerCase();
    var n = String(q || "").toLowerCase().trim();
    if (!n) return 10;
    if (t === n) return 100;
    if (t.indexOf(n) === 0) return 90;
    if (t.indexOf(n) > -1) return 70;
    // 子序列（"kmp" 命中 "kmp 算法" 已被前缀覆盖；这里兜 "km算" 之类）
    var i = 0, j = 0;
    while (i < t.length && j < n.length) { if (t[i] === n[j]) j++; i++; }
    return j === n.length ? 45 : -1;
  }

  /** 把后端返回的四类索引统一成 {group,title,sub,hint,icon,action,score} */
  function normalize(data) {
    var out = [];
    if (!data) return out;
    var terms = data.terms || [], docs = data.docs || [], subs = data.subs || [], cmds = data.commands || [];
    terms.forEach(function (t) {
      out.push({ group: "terms", title: t.name, sub: "术语 · " + (t.n ? t.n + " 张卡" : "baike"), icon: "i-sort-alpha", action: "/search?q=" + encodeURIComponent(t.name) });
    });
    docs.forEach(function (d) {
      out.push({ group: "docs", title: d.name, sub: d.rel || "", icon: "i-file", action: util.docUrl(d.rel) });
    });
    subs.forEach(function (s) {
      out.push({ group: "subs", title: s.name, sub: s.id || "", icon: "i-scope-domain", action: "/browse/" + String(s.id || "").split("/").map(encodeURIComponent).join("/") });
    });
    cmds.forEach(function (c) {
      out.push({ group: "commands", title: c.title, sub: c.hint || "命令", icon: c.icon || "i-palette", action: c.action, cmdId: c.id });
    });
    return out;
  }

  /** 过滤 + 排序 + 截断，返回按组排好序的扁平数组 */
  function filterItems(q) {
    var all = normalize(palette.data);
    var scored = [];
    all.forEach(function (it) {
      var s = scoreText(it.title, q);
      if (s < 0) {
        // 命令/子域额外给一次「副标题子串」机会（spec：对 commands/subs 做子串加权）
        if (it.group === "commands" || it.group === "subs") {
          var s2 = scoreText(it.sub, q);
          if (s2 < 0) return;
          s = s2 - 8;
        } else {
          return;
        }
      }
      if (it.group === "terms") s += 10;
      else if (it.group === "docs") s += 5;
      else if (it.group === "commands" || it.group === "subs") {
        if (String(it.title).toLowerCase().indexOf(String(q || "").toLowerCase().trim()) > -1) s += 8;
      }
      scored.push({ it: it, score: s });
    });
    scored.sort(function (a, b) {
      if (b.score !== a.score) return b.score - a.score;
      return String(a.it.title).localeCompare(String(b.it.title), "zh-Hans-CN");
    });
    var flat = [];
    GROUP_META.forEach(function (g) {
      var n = 0;
      for (var i = 0; i < scored.length && n < g.max; i++) {
        if (scored[i].it.group === g.key) { flat.push(scored[i].it); n++; }
      }
    });
    return flat;
  }

  function palHTML(items, q) {
    if (!items.length) {
      return '<div class="kb-pal-empty">' + util.icon("i-search-magnifier", 18) +
        "<div>没有匹配「" + util.esc(q) + "」的术语 / 文档 / 命令</div></div>";
    }
    var html = "", cursor = -1, lastGroup = null;
    items.forEach(function (it) {
      cursor++;
      if (it.group !== lastGroup) {
        lastGroup = it.group;
        var meta = GROUP_META.filter(function (g) { return g.key === it.group; })[0];
        html += '<div class="kb-pal-gtitle">' + util.esc(meta ? meta.title : it.group) + "</div>";
      }
      html += '<div class="kb-pal-item' + (cursor === palette.sel ? " sel" : "") + '" data-i="' + cursor + '" role="option"' +
        (cursor === palette.sel ? ' aria-selected="true"' : "") + ">" +
        '<span class="kb-pal-ic">' + util.icon(it.icon, 14) + "</span>" +
        '<span class="kb-pal-t">' + util.esc(it.title) + "</span>" +
        '<span class="kb-pal-s">' + util.esc(it.sub || "") + "</span>" +
        "</div>";
    });
    return html;
  }

  function palRender() {
    var root = palRoot();
    if (!root) return;
    var box = root.querySelector(".kb-pal-box");
    var input = root.querySelector("#kb-pal-input");
    var body = root.querySelector("#kb-pal-body");
    if (!box || !body) return;
    var q = input ? input.value.trim() : "";
    root.classList.toggle("show", palette.open);
    box.setAttribute("aria-hidden", palette.open ? "false" : "true");
    var items = filterItems(q);
    if (palette.sel >= items.length) palette.sel = items.length - 1;
    if (palette.sel < 0) palette.sel = items.length ? 0 : -1;
    palette.flat = items;
    body.innerHTML = palHTML(items, q);
    var cnt2 = root.querySelector("#kb-pal-count");
    if (cnt2) {
      if (!palette.data) cnt2.textContent = palette.loading ? "索引载入中…" : "索引不可用";
      else cnt2.textContent = (palette.data.counts ? (palette.data.counts.terms || 0) + " 术语 · " : "") +
        items.length + " / " + (normalize(palette.data).length) + " 条匹配";
    }
  }

  /* ESC 统一收口（readpref 模式已随设置抽屉重构移除：命令面板只剩结果列表一种形态）。 */
  function palEscape(e) {
    if (e && e.__kbPalEsc) return;
    if (e) e.__kbPalEsc = true;
    if (!palette.open) return;
    palette.close();
  }

  function palMove(delta) {
    var n = palette.flat.length;
    if (!n) return;
    palette.sel = (palette.sel + delta + n) % n;
    palRender();
    var el = palRoot().querySelector('.kb-pal-item[data-i="' + palette.sel + '"]');
    if (el && el.scrollIntoView) el.scrollIntoView({ block: "nearest" });
  }

  function execAction(action) {
    var a = String(action || "");
    // 后端 action 是 JSON 字符串字面量，如 "\"/home\"" / "\"kb:toggle-theme\""
    if (a.charAt(0) === '"') { try { a = JSON.parse(a); } catch (e) { a = a.replace(/^"|"$/g, ""); } }
    if (a.indexOf("kb:") === 0) {
      var key = a.slice(3);
      if (key === "toggle-theme") {
        if (typeof window.applyTheme === "function") {
          var now = document.documentElement.getAttribute("data-theme");
          window.applyTheme(now === "dark" ? "light" : "dark");
          util.toast("已切换" + (now === "dark" ? "浅色" : "深色") + "主题");
        } else if (document.getElementById("theme-btn")) {
          document.getElementById("theme-btn").click();
        }
        return true;
      }
      if (key === "readpref") {
        KB.settings.open();
        return true; // 关命令面板，露出右侧设置抽屉
      }
      util.toast("未识别的命令：" + util.esc(key));
      return false;
    }
    /* 问题12：目标是阅读页内文档/分类且当前就在 workbench → 走 app.js 客户端路由
       （~20ms 换文档，且经 dirty guard 保护）；否则整页跳转。 */
    if (a && typeof window.navigate === "function" && document.getElementById("article")
        && /^\/(doc|browse)\//.test(a)) {
      window.navigate(a, true);
      return true;
    }
    if (a) { location.href = a; return true; }
    return false;
  }

  function palExec(i) {
    var it = palette.flat[i == null ? palette.sel : i];
    if (!it) return;
    if (execAction(it.action)) palette.close();
  }

  function palLoad(force) {
    var cached = util.getJSON(LS_PAL, null);
    if (cached && Array.isArray(cached.terms)) { palette.data = cached; palRender(); }
    var sig = cached && cached.sig ? cached.sig : "";
    palette.loading = true;
    palRender();
    return api.palette({ sig: sig || undefined }).then(function (j) {
      palette.loading = false;
      if (j && j.fresh) { palRender(); return; }
      if (j && Array.isArray(j.terms)) {
        palette.data = { sig: j.sig, terms: j.terms, docs: j.docs || [], subs: j.subs || [], commands: j.commands || [], counts: j.counts || {} };
        util.setJSON(LS_PAL, palette.data);
      }
      palRender();
    }).catch(function () {
      palette.loading = false;
      palRender();
    });
  }

  palette.build = function () {
    var root = palRoot();
    if (!root || root.dataset.built) return;
    root.dataset.built = "1";
    root.innerHTML =
      '<div class="kb-pal-mask" data-close="1"></div>' +
      '<div class="kb-pal-box" role="dialog" aria-modal="true" aria-label="命令面板">' +
      '  <div class="kb-pal-head">' +
      '    <span class="kb-pal-head-ic">' + util.icon("i-search-magnifier", 14) + "</span>" +
      '    <input id="kb-pal-input" type="text" placeholder="搜术语 / 文档 / 子域，或执行命令…" autocomplete="off" spellcheck="false" aria-label="命令面板输入">' +
      '    <kbd>Esc</kbd>' +
      "  </div>" +
      '  <div class="kb-pal-body" id="kb-pal-body" role="listbox" aria-label="命令面板结果"></div>' +
      '  <div class="kb-pal-foot"><span>↑↓ 选择 · Enter 执行 · Esc 关闭</span><span class="kb-pal-count" id="kb-pal-count"></span></div>' +
      "</div>";
    var input = root.querySelector("#kb-pal-input");
    input.addEventListener("input", function () { palette.sel = 0; palRender(); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); palMove(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); palMove(-1); }
      else if (e.key === "Enter") { e.preventDefault(); palExec(); }
      else if (e.key === "Escape") { e.preventDefault(); palEscape(e); }
      e.stopPropagation(); // 面板内输入不吃全局快捷键
    });
    root.addEventListener("click", function (e) {
      // 遮罩 data-close="1" 此前无人消费：点空白处关不掉面板，只把焦点甩到 BODY，
      // 正是后续 ESC 行为漂移的触发点（见 palEscape 注释）
      if (e.target.closest && e.target.closest("[data-close]")) { palette.close(); return; }
      var item = e.target.closest ? e.target.closest(".kb-pal-item") : null;
      if (item) { palExec(Number(item.dataset.i)); }
    });
  };

  palette.toggle = function () { palette.open ? palette.close() : palette.show(); };
  palette.show = function () {
    palette.build();
    if (!palette.data) palLoad();
    palette.open = true;
    palette.sel = 0;
    palRender();
    var input = document.querySelector("#kb-pal-input");
    if (input) { input.value = ""; setTimeout(function () { input.focus(); }, 0); }
  };
  palette.close = function () {
    palette.open = false;
    var root = palRoot();
    if (root) root.classList.remove("show");
    var input = document.querySelector("#kb-pal-input");
    if (input) input.blur();
  };
  palette.isOpen = function () { return !!palette.open; };
  palette.refresh = function (force) { return palLoad(!!force); };
  /* 问题10：palette 缓存纳入统一失效体系——app.js 的 invalidate('palette') 转调这里。
     原 palLoad 里「先校验 sig」的空 if 死代码一并删除：sig 校验的真实执行体在
     api.palette({sig}) 的 fresh 应答里，本地段本来就不需要分支。 */
  palette.dropCache = function () {
    palette.data = null;
    try { localStorage.removeItem(LS_PAL); } catch (e) {}
  };

  /* settings —— 右侧设置抽屉（2026-09-20 重构，参考 draw.io 属性面板形态）：
     不再借命令面板的 readpref 模式；从右缘滑入、遮罩点击 / Esc / × 关闭。
     分区（界面风格 / 阅读排版 / 标题与代码 / 快捷键）由 prefs.panelHTML 提供。 */
  var settings = (KB.settings = {
    _ov: null,
    isOpen: false,
    el: function () {
      if (settings._ov) return settings._ov;
      var ov = document.createElement("div");
      ov.className = "kb-set-ov";
      ov.innerHTML = '<aside class="kb-set-drawer" role="dialog" aria-modal="true" aria-label="设置">' +
        '<div class="kb-set-h">' + util.icon("i-palette", 15) + "<b>设置</b>" +
        '<button type="button" class="kb-set-x" aria-label="关闭设置">' + util.icon("i-cancel-x", 13) + "</button></div>" +
        '<div class="kb-set-tabs" id="kb-set-tabs" role="tablist" aria-label="设置分区"></div>' +
        '<div class="kb-set-b" id="kb-set-body"></div></aside>';
      document.body.appendChild(ov);
      ov.addEventListener("click", function (e) {
        if (e.target === ov) { settings.close(); return; }
        if (e.target.closest && e.target.closest(".kb-set-x")) settings.close();
      });
      settings._ov = ov;
      return ov;
    },
    open: function () {
      var ov = settings.el();
      var body = ov.querySelector("#kb-set-body");
      /* 顶部页签（2026-09-20 用户要求 tab 化）：外观 / 排版 / 快捷键，
         各 section 由 data-sec 关联，切换只动 hidden，不重建 DOM（滑杆绑定不丢）。 */
      body.innerHTML =
        prefs.panelHTML() +
        '<section class="kb-set-sec" data-sec="keys" hidden>' +
        '<div class="kb-pref-head">' + util.icon("i-kbd-cmd", 14) + '快捷键<span class="kb-pref-kbd-hint">随时按 ? 唤出完整帮助</span></div>' +
        '<div class="kb-keys-list">' + HELP_HTML.map(function (r) {
            return '<div class="kb-help-row"><kbd>' + util.esc(r[0]) + "</kbd><span>" + util.esc(r[1]) + "</span></div>";
          }).join("") + "</div></section>";
      body.dataset.bound = ""; // 每次 open 都重建 DOM，绑定标记随之重置
      prefs.bindPanel(body);
      var tabs = ov.querySelector("#kb-set-tabs");
      tabs.innerHTML =
        '<button type="button" role="tab" class="on" data-sec="look" aria-selected="true">外观</button>' +
        '<button type="button" role="tab" data-sec="type" aria-selected="false">排版</button>' +
        '<button type="button" role="tab" data-sec="keys" aria-selected="false">快捷键</button>';
      if (!tabs.dataset.wired) {
        tabs.dataset.wired = "1";
        tabs.addEventListener("click", function (e) {
          var btn = e.target.closest("[data-sec]");
          if (!btn) return;
          tabs.querySelectorAll("[data-sec]").forEach(function (b) {
            var on = b === btn;
            b.classList.toggle("on", on);
            b.setAttribute("aria-selected", on ? "true" : "false");
          });
          body.querySelectorAll(".kb-set-sec").forEach(function (sec) {
            sec.hidden = sec.dataset.sec !== btn.dataset.sec;
          });
          body.scrollTop = 0;
        });
      }
      /* 强制回流让首帧停在 translateX(103%)，再加 .show 触发滑入过渡。
         不用 requestAnimationFrame：后台标签页 rAF 被节流，抽屉会永远停在关闭态。 */
      ov.classList.remove("show");
      void ov.offsetWidth;
      ov.classList.add("show");
      settings.isOpen = true;
    },
    close: function () {
      if (settings._ov) settings._ov.classList.remove("show");
      settings.isOpen = false;
    }
  });

  /* ==================================================================
     [5] keys —— 需求7 键盘导航（单一 keydown 捕获阶段分发器）
     铁律：INPUT / TEXTAREA / contenteditable 聚焦时，除 Esc 与 Ctrl/Cmd+K 外不劫持任何键
     ================================================================== */
  var keys = (KB.keys = {
    /** 页面级上下文钩子：learn.js / glossary.js 可注册，返回 true 表示已消费该键 */
    context: null,
    setContext: function (fn) { keys.context = fn; }
  });

  function docListMove(delta) {
    // 需求 #11：第二列列表移除后，文档在树内 —— 优先 #doclist，回退 #tree .doc
    var list = document.getElementById("doclist");
    var items = [];
    if (list) items = util.$$(".doc", list);
    if (!items.length) {
      var nav = document.getElementById("tree");
      if (nav) items = util.$$("#tree .doc", nav);
    }
    if (!items.length) return false;
    var cur = items.indexOf(document.activeElement);
    var next = cur < 0 ? (delta > 0 ? 0 : items.length - 1) : util.clamp(cur + delta, 0, items.length - 1);
    items[next].focus();
    if (items[next].scrollIntoView) items[next].scrollIntoView({ block: "nearest" });
    return true;
  }

  /* 问题18：快捷键唯一数据源。原 HELP_HTML 只 9 条硬编码，Ctrl+S、右键/菜单键、
     rtab 方向键、Esc 分层语义均缺失——帮助面板与实际行为是两套真相。
     scope: global 全站 / browse 阅读页 / editor 编辑器 / review 复习页。
     新增键位必须登记于此（? 帮助与 palette 快捷键区都从 registry 派生）。 */
  var KEY_REGISTRY = [
    { combo: "Ctrl / ⌘ + K", desc: "命令面板（术语 / 文档 / 子域 / 命令）", scope: "global" },
    { combo: "/", desc: "聚焦顶栏搜索框（? 前缀走语义检索）", scope: "global" },
    { combo: "Esc", desc: "分层关闭：补全 → 弹窗 / 菜单 → 帮助 → 编辑器（未保存先确认）", scope: "global" },
    { combo: "?", desc: "显示本帮助", scope: "global" },
    { combo: "Ctrl / ⌘ + S", desc: "保存并写回文件系统（编辑器内）", scope: "editor" },
    { combo: "[[ 输入", desc: "双链补全：↑↓ 选择，Tab / Enter 插入", scope: "editor" },
    { combo: "j / k", desc: "文档列表上下移动", scope: "browse" },
    { combo: "Enter", desc: "打开聚焦的文档", scope: "browse" },
    { combo: "Menu / Shift+F10", desc: "对聚焦的文档或目录打开右键菜单", scope: "browse" },
    { combo: "↑ ↓ ← →", desc: "右键菜单与移动弹窗目录树导航", scope: "browse" },
    { combo: "← →", desc: "右栏标签（目录 / 信息 / 备注 / 双链）切换", scope: "browse" },
    { combo: "j / k", desc: "上一张 / 下一张卡片", scope: "review" },
    { combo: "Space", desc: "翻面看答案", scope: "review" },
    { combo: "1 2 3 4", desc: "评分：重来 / 困难 / 良好 / 简单", scope: "review" }
  ];
  var HELP_HTML = KEY_REGISTRY.map(function (k) { return [k.combo, k.desc]; });
  keys.registry = KEY_REGISTRY;

  function toggleHelp(force) {
    var el = document.getElementById("kb-help");
    if (!el) {
      el = document.createElement("div");
      el.id = "kb-help";
      el.className = "kb-help";
      el.innerHTML = '<div class="kb-help-box" role="dialog" aria-label="键盘快捷键">' +
        '<div class="kb-help-h">' + util.icon("i-kbd-cmd", 14) + "键盘快捷键" +
        '<button type="button" class="kb-help-x" aria-label="关闭">' + util.icon("i-cancel-x", 12) + "</button></div>" +
        '<div class="kb-help-b">' + HELP_HTML.map(function (r) {
          return '<div class="kb-help-row"><kbd>' + util.esc(r[0]) + "</kbd><span>" + util.esc(r[1]) + "</span></div>";
        }).join("") + "</div></div>";
      document.body.appendChild(el);
      el.addEventListener("click", function (e) {
        if (e.target.closest && e.target.closest(".kb-help-x")) toggleHelp(false);
      });
    }
    var on = force == null ? !el.classList.contains("show") : !!force;
    el.classList.toggle("show", on);
  }
  keys.toggleHelp = toggleHelp;

  keys.handle = function (e) {
    var mod = e.ctrlKey || e.metaKey;
    /* ① Ctrl/Cmd+K：任何上下文都可用 */
    if (mod && (e.key === "k" || e.key === "K")) {
      e.preventDefault();
      palette.toggle();
      return true;
    }
    /* KB.overlay 系弹层在场时让位：Esc 由弹层自身处理（问题13），
       其余按键一律不劫持，防止「弹层开着按 j 也翻列表」的双动作。 */
    var soOv = document.getElementById("kb-search-ov");
    var soOpenState = !!(soOv && soOv.classList.contains("show"));
    var soTarget = soOpenState && (e.target === soOv || !soOv.querySelector(".kb-search-box").contains(e.target));
    if (!soTarget && KB.overlay && KB.overlay.openCount > 0) return false;
    /* ② Escape：关补全 → 关搜索浮层 → 关设置抽屉 → 关面板 → 关帮助 → 关编辑器（保留 app.js 原有行为） */
    if (e.key === "Escape") {
      if (KB.wl && KB.wl.suggestOpen && KB.wl.suggestOpen()) { KB.wl.hideSuggest(); e.preventDefault(); return true; }
      if (soOpenState) { soOv.classList.remove("show"); soOv.hidden = true; e.preventDefault(); return true; }
      if (KB.settings.isOpen) { KB.settings.close(); e.preventDefault(); return true; }
      if (palette.isOpen()) { palEscape(e); e.preventDefault(); return true; }
      var helpEl = document.getElementById("kb-help");
      if (helpEl && helpEl.classList.contains("show")) { toggleHelp(false); e.preventDefault(); return true; }
      if (typeof window.tryCloseEditor === "function") window.tryCloseEditor();
      else if (typeof window.closeEditor === "function") window.closeEditor();
      return false;
    }
    /* ③ 输入态一律放行（j/k、/、? 都不劫持），只允许上面两条 */
    if (util.isEditable(document.activeElement)) return false;
    if (e.altKey) return false;

    /* ④ / 聚焦搜索 */
    if (e.key === "/") { e.preventDefault(); util.focusSearch(); return true; }
    /* ⑤ ? 帮助 */
    if (e.key === "?") { e.preventDefault(); toggleHelp(); return true; }
    /* ⑥ 页面级上下文（复习翻面 / 评分 / 术语网格等） */
    if (keys.context) { try { if (keys.context(e) === true) return true; } catch (err) { /* 页面钩子出错不拖垮全局 */ } }
    /* ⑦ j / k：文档列表导航 */
    if (e.key === "j" || e.key === "k") {
      if (docListMove(e.key === "j" ? 1 : -1)) { e.preventDefault(); return true; }
    }
    /* ⑧ ← / →：目录树层级展开/收起（焦点在域头/子域/三级目录头上时生效）
          ← 收起当前层级；→ 展开当前层级。与点击行为语义一致（纯前端、不导航）。 */
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      if (treeLevelToggle(e.key === "ArrowRight")) { e.preventDefault(); return true; }
    }
    return false;
  };

  /* 目录树 ←/→ 展开收起：返回 true 表示已消费该键。
     定位目标节点优先序：
       ① 点击选中的树节点（window.KB_treeSelected）—— 点击时 preventDefault
          会阻止浏览器聚焦，document.activeElement 拿不到节点（实测落 BODY），
          故必须用显式记录的选中态，这是主路径；
       ② 退路：document.activeElement（Tab 键导航时生效）。
     - 域头 .dom-head      → 切换 .dom 的 open
     - 子域 .sub           → 切换其后 .sub-docs 的 collapsed
     - 三级 .tree-subdir-h → 切换所在 .tree-subdir 的 collapsed
     状态与点击路径共用 localStorage，避免两套真相。 */
  function treeLevelToggle(expand) {
    var el = null;
    try { if (typeof window.KB_treeSelected === "function") el = window.KB_treeSelected(); } catch (e) {}
    if (!el || !el.closest) el = document.activeElement;
    if (!el || !el.closest) return false;
    var tree = document.getElementById("tree");
    if (!tree || !tree.contains(el)) return false;

    /* 三级目录头 */
    var sdHead = el.closest(".tree-subdir-h");
    if (sdHead) {
      var box = sdHead.closest(".tree-subdir");
      var key = box && box.dataset.dirKey;
      if (!key) return false;
      setTreeCollapsed("kb-subdir-collapsed", key, box, expand);
      sdHead.setAttribute("aria-expanded", expand ? "true" : "false");
      return true;
    }
    /* 二级子域 */
    var subA = el.closest(".sub");
    if (subA) {
      var docsBox = subA.nextElementSibling;
      if (!docsBox || !docsBox.classList.contains("sub-docs")) return false;
      var subKey = subA.dataset.subKey || (subA.dataset.dom + "/" + subA.dataset.sub);
      setTreeCollapsed("kb-sub-open", subKey, docsBox, expand);
      subA.setAttribute("aria-expanded", expand ? "true" : "false");
      return true;
    }
    /* 一级域 */
    var domHead = el.closest(".dom-head");
    if (domHead) {
      var dom = domHead.closest(".dom");
      if (!dom) return false;
      /* 一级域用 .open 类（在 = 展开），与二级/三级的 .collapsed 语义相反，单独处理 */
      dom.classList.toggle("open", expand);
      domHead.setAttribute("aria-expanded", expand ? "true" : "false");
      try {
        var raw0 = localStorage.getItem("kb-tree-open");
        var set0 = new Set(raw0 ? JSON.parse(raw0) : []);
        if (expand) set0.add(dom.dataset.dom); else set0.delete(dom.dataset.dom);
        localStorage.setItem("kb-tree-open", JSON.stringify(Array.from(set0)));
      } catch (err) {}
      return true;
    }
    return false;
  }
  /* 二级/三级的可见性持久化：class .collapsed（在 = 收起）。
     storageKey 为 "kb-sub-open" 时集合语义是「已展开」；
     为 "kb-subdir-collapsed" 时语义是「已收起」。 */
  function setTreeCollapsed(storageKey, key, node, expand) {
    node.classList.toggle("collapsed", !expand);
    try {
      var raw = localStorage.getItem(storageKey);
      var set = new Set(raw ? JSON.parse(raw) : []);
      if (storageKey === "kb-subdir-collapsed") {
        if (expand) set.delete(key); else set.add(key);
      } else {
        if (expand) set.add(key); else set.delete(key);
      }
      localStorage.setItem(storageKey, JSON.stringify(Array.from(set)));
    } catch (err) {}
  }

  /* ==================================================================
     [6] wl —— 需求6 双链补全 + 断链提示（编辑器 #ed-text）
     ================================================================== */
  var wl = (KB.wl = {
    dead: [],
    sug: [],
    sugIdx: -1,
    sugOpen: false,
    token: 0
  });

  var sugEl = null, barEl = null;

  function ensureWlDom() {
    var ed = document.getElementById("ed-text");
    if (!ed) return null;
    if (!barEl) {
      barEl = document.createElement("div");
      barEl.className = "kb-wl-bar";
      barEl.id = "kb-wl-bar";
      barEl.hidden = true;
      ed.parentNode.insertBefore(barEl, ed.nextSibling);
    }
    if (!sugEl) {
      sugEl = document.createElement("div");
      sugEl.className = "kb-wl-sug";
      sugEl.id = "kb-wl-sug";
      sugEl.hidden = true;
      document.body.appendChild(sugEl);
    }
    return ed;
  }

  wl.suggestOpen = function () { return !!(sugEl && !sugEl.hidden && wl.sug.length); };

  wl.hideSuggest = function () {
    if (sugEl) { sugEl.hidden = true; sugEl.innerHTML = ""; }
    wl.sug = [];
    wl.sugIdx = -1;
    wl.sugOpen = false;
  };

  function renderSuggest() {
    if (!sugEl) return;
    sugEl.innerHTML = wl.sug.map(function (s, i) {
      return '<div class="kb-wl-sug-item' + (i === wl.sugIdx ? " sel" : "") + '" data-i="' + i + '">' +
        '<span class="kb-wl-sug-n">' + util.esc(s.name) + "</span>" +
        '<span class="kb-wl-sug-k">' + util.esc(s.kind === "term" ? "术语" : "文档") + "</span></div>";
    }).join("");
    sugEl.hidden = !wl.sug.length;
    wl.sugOpen = !!wl.sug.length;
  }

  /** 找光标前最近的未闭合 [[ —— 返回 {start, raw} 或 null */
  function pendingBracket(text, caret) {
    var head = text.slice(0, caret);
    var open = head.lastIndexOf("[[");
    if (open < 0) return null;
    var close = head.lastIndexOf("]]");
    if (close > open) return null;
    var raw = head.slice(open + 2);
    if (raw.indexOf("\n") > -1) return null;      // 跨行不再提示
    if (raw.length > 40) return null;             // 太长不当补全
    return { start: open, raw: raw };
  }

  function applySuggest(ed, item) {
    var p = pendingBracket(ed.value, ed.selectionStart);
    if (!p) return;
    var before = ed.value.slice(0, p.start);
    var after = ed.value.slice(ed.selectionStart);
    var insert = "[[" + item.name + "]]";
    ed.value = before + insert + after;
    var pos = (before + insert).length;
    ed.setSelectionRange(pos, pos);
    wl.hideSuggest();
    scheduleCheck();
  }

  var doSuggest = util.debounce(function () {
    var ed = document.getElementById("ed-text");
    if (!ed) return;
    var p = pendingBracket(ed.value, ed.selectionStart);
    if (!p) { wl.hideSuggest(); return; }
    var my = ++wl.token;
    api.wlSuggest({ q: p.raw, limit: 8 }).then(function (j) {
      if (my !== wl.token) return;
      wl.sug = (j.items || []).slice(0, 8);
      wl.sugIdx = wl.sug.length ? 0 : -1;
      var edNow = document.getElementById("ed-text");
      if (edNow && sugEl) {
        var r = edNow.getBoundingClientRect();
        sugEl.style.left = Math.round(r.left) + "px";
        sugEl.style.top = Math.round(Math.min(r.bottom, window.innerHeight - 240)) + "px";
        sugEl.style.minWidth = Math.round(Math.max(240, r.width * 0.5)) + "px";
      }
      renderSuggest();
    }).catch(function () { wl.hideSuggest(); });
  }, 120);

  var scheduleCheck = util.debounce(function () {
    var ed = document.getElementById("ed-text");
    if (!ed) return;
    var pathEl = document.getElementById("ed-path");
    var path = pathEl ? (pathEl.textContent || "").trim() : "";
    api.wlCheck({ body: ed.value, path: path || undefined }).then(function (j) {
      wl.dead = j.dead || [];
      renderDeadBar();
    }).catch(function () { /* 断链检测是增强项，失败不打扰 */ });
  }, 400);

  function renderDeadBar() {
    if (!barEl) return;
    if (!wl.dead.length) { barEl.hidden = true; barEl.innerHTML = ""; return; }
    barEl.hidden = false;
    barEl.innerHTML =
      '<span class="kb-wl-badge">' + util.icon("i-warning-triangle", 12) + "断链 " + wl.dead.length + " 处</span>" +
      wl.dead.map(function (d, i) {
        return '<button type="button" class="kb-wl-chip" data-line="' + (d.line || 0) + '" title="跳到第 ' + (d.line || 0) + " 行\">" +
          "断链 " + (i + 1) + " · " + util.esc(d.raw) +
          (d.suggest ? '<span class="kb-wl-fix">→ ' + util.esc(d.suggest) + "</span>" : "") +
          '<span class="kb-wl-line">第 ' + (d.line || 0) + " 行</span></button>";
      }).join("") +
      '<span class="kb-wl-tip">点 chip 跳到该行</span>';
  }

  function gotoLine(ed, line) {
    var lines = ed.value.split("\n");
    var pos = 0;
    for (var i = 0; i < line - 1 && i < lines.length; i++) pos += lines[i].length + 1;
    ed.focus();
    ed.setSelectionRange(pos, pos + (lines[line - 1] || "").length);
    var before = ed.value.slice(0, pos).split("\n").length;
    ed.scrollTop = Math.max(0, (before - 6) * 20);
  }

  wl.attach = function () {
    var ed = ensureWlDom();
    if (!ed || ed.dataset.kbWl) return;
    ed.dataset.kbWl = "1";
    ed.addEventListener("input", function () { doSuggest(); scheduleCheck(); });
    ed.addEventListener("click", function () { doSuggest(); });
    ed.addEventListener("blur", function () { setTimeout(function () { wl.hideSuggest(); }, 150); });
    ed.addEventListener("keydown", function (e) {
      if (!wl.suggestOpen()) return;
      if (e.key === "ArrowDown") { e.preventDefault(); wl.sugIdx = (wl.sugIdx + 1) % wl.sug.length; renderSuggest(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); wl.sugIdx = (wl.sugIdx - 1 + wl.sug.length) % wl.sug.length; renderSuggest(); }
      else if (e.key === "Enter" || e.key === "Tab") {
        if (wl.sugIdx >= 0 && wl.sug[wl.sugIdx]) { e.preventDefault(); applySuggest(ed, wl.sug[wl.sugIdx]); }
      }
    }, true);
    if (barEl) barEl.addEventListener("click", function (e) {
      var chip = e.target.closest ? e.target.closest(".kb-wl-chip") : null;
      if (chip) gotoLine(ed, Number(chip.dataset.line) || 1);
    });
  };

  /** 保存前断链提醒：非阻断（取消只是留在编辑器继续改，不丢内容） */
  wl.guardSave = function () {
    if (typeof window.saveDoc !== "function" || window.saveDoc.__kbGuarded) return;
    var orig = window.saveDoc;
    var wrapped = function () {
      var self = this, args = arguments;
      /* 问题6 修复：kb-core 曾在全仓库唯一一处用原生 window.confirm（与本仓
         「自研 kbModal 替代 prompt/confirm」的约定冲突）。断链确认改走 kbModal：
         danger 样式 + 「仍然保存 / 回去改」；kbModal 由 app.js 顶层函数声明挂到
         window，保存动作必然发生在 app.js 加载之后，可安全依赖；极端缺席时退回原生 confirm。 */
      if (!wl.dead || !wl.dead.length) return orig.apply(self, args);
      var names = wl.dead.slice(0, 3).map(function (d) { return d.raw; }).join("、");
      var more = wl.dead.length > 3 ? " 等 " + wl.dead.length + " 处" : "";
      var body = "检测到 <b>" + wl.dead.length + "</b> 处断链（" + util.esc(names) + util.esc(more) + "）。<br>" +
        "断链不会阻止保存，但右栏「双链」会一直显示未解析。";
      var proceed = function (ok) {
        if (!ok) { util.toast("已取消保存 —— 内容还在编辑器里，改完再点保存"); return Promise.resolve(); }
        return orig.apply(self, args);
      };
      if (typeof window.kbModal === "function") {
        return window.kbModal({ title: util.icon("i-warning-triangle", 15) + " 存在断链", body: body, danger: true, confirmText: "仍然保存", cancelText: "回去改" })
          .then(function (res) { return proceed(!!res); });
      }
      return Promise.resolve(proceed(window.confirm("检测到 " + wl.dead.length + " 处断链（" + names + more + "）。\n确定现在保存？")));
    };
    wrapped.__kbGuarded = true;
    window.saveDoc = wrapped;
  };

  /* ==================================================================
     [7] 启动
     ================================================================== */
  /* boot 幂等，最多跑两次：
     ① defer 脚本执行时（readyState==="interactive"：DOM 已就绪，但 app.js 还没执行）
     ② DOMContentLoaded（此时 app.js 的顶层 function 已挂到 window，才能包装 saveDoc） */
  var booted = false;
  function boot() {
    prefs.apply();                 // 先落地阅读偏好，避免首帧跳动
    palette.build();
    wl.attach();                   // #ed-text 已解析，可挂监听
    wl.guardSave();                // 依赖 window.saveDoc；第 ① 次会 no-op，第 ② 次补上
    var gear = document.getElementById("kb-settings-btn");
    if (gear && !gear.dataset.kbBound) {
      gear.dataset.kbBound = "1";  // boot 幂等跑两次，防重复绑定
      gear.addEventListener("click", function () { KB.settings.open(); });
    }
    /* 搜索浮层：点遮罩空白处关闭（点在 .kb-search-box 内部不关） */
    var soOv = document.getElementById("kb-search-ov");
    if (soOv && !soOv.dataset.kbMaskBound) {
      soOv.dataset.kbMaskBound = "1";
      soOv.addEventListener("click", function (e) {
        if (e.target === soOv) { soOv.classList.remove("show"); soOv.hidden = true; }
      });
    }
    if (booted) return;
    booted = true;
    /* 空闲时预热命令面板索引，保证 Ctrl+K 首帧就有东西 */
    if (!palette.data) setTimeout(function () { if (!palette.data) palLoad(); }, 1500);
  }

  /* 捕获阶段唯一入口。e.__kbHandled 去重：base.html 里 kb-core.js 先于 app.js 执行，
     app.js 的冒泡监听器会把同一个事件再交给 KB.keys.handle 一次（v18 兼容分支），
     不去重会导致 Ctrl+K 开完立刻关、Space 翻完面立刻跳下一张。 */
  document.addEventListener("keydown", function (e) {
    if (e.__kbHandled) return;
    e.__kbHandled = true;
    keys.handle(e);
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
    document.addEventListener("DOMContentLoaded", boot);
  }
})();
