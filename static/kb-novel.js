/* kb-novel.js — 书库/小说在线阅读引擎（2026-09-21）
   ① 小说排版偏好（localStorage kb-novel-pref，只染阅读区，不污染文章正文）
   ② txt 阅读器：编码嗅探 + 章节引擎 + 懒渲染（15MB 全本可用）+ 目录跟随 +
      书内搜索 + 续读定位 + 连续滚动/章节分页 + TTS 朗读 + 自动滚动 + 章评
   ③ epub 阅读器：设置接入（字号/行高/字距/段距/缩进/宽度/字体/护眼/flow）、
      CFI 续读、书内搜索（JSZip 直读 spine）、TTS、下载
   依赖加载顺序：kb-core.js → app.js → 本文件（icon/DOC/rawUrl 等 app.js 全局）。 */
(function () {
  "use strict";
  var N = (window.KBNOVEL = {});
  var util = KB.util;

  /* ================= 偏好 ================= */
  var LS = "kb-novel-pref";
  var THEMES = {
    white:     { name: "纯白", bg: "#ffffff", ink: "#17181a" },
    cream:     { name: "米黄", bg: "#fbf6e9", ink: "#3d3324" },
    parchment: { name: "羊皮纸", bg: "#f4ecd8", ink: "#43392a" },
    sage:      { name: "豆绿", bg: "#e9f0e6", ink: "#26332a" },
    night:     { name: "夜读", bg: "#1a1d21", ink: "#c9cdd3" }
  };
  var WIDTH_LEGACY = { narrow: 34, mid: 44, wide: 56, full: 100 };
  var NV_FONT_MAP = {
    "default": "var(--f-body)",
    serif: '"Source Han Serif SC", "Noto Serif SC", Georgia, "Times New Roman", serif',
    sans: '"PingFang SC", "Microsoft YaHei", system-ui, sans-serif',
    mono: '"Cascadia Mono", Consolas, monospace'
  };
  var DEF = { size: 17, line: 1.9, track: 0.5, gap: 10, indent: 1, widthRem: 44,
    font: "default", theme: "white", bgCustom: "", flow: "scroll", rate: 1 };
  var NUM_RANGE = { size: [14, 26], line: [1.5, 2.6], track: [0, 3], gap: [4, 24], rate: [0.5, 3], widthRem: [24, 100] };
  function widthMaxStr(rem) { return rem >= 100 ? "none" : rem + "rem"; }

  function safeFamily(v) {
    if (typeof v !== "string") return "";
    return v.replace(/["'\\;{}<>()&]/g, "").trim().slice(0, 80);
  }
  function norm(v) {
    var out = {}, k;
    Object.keys(DEF).forEach(function (key) { out[key] = DEF[key]; });
    if (v && typeof v === "object") {
      if (v.width && v.widthRem === undefined && WIDTH_LEGACY[v.width] !== undefined) v.widthRem = WIDTH_LEGACY[v.width];
      Object.keys(DEF).forEach(function (key) {
        if (v[key] === undefined || v[key] === null || v[key] === "") return;
        out[key] = v[key];
      });
    }
    Object.keys(NUM_RANGE).forEach(function (key) {
      var r = NUM_RANGE[key], x = Number(out[key]);
      out[key] = isNaN(x) ? DEF[key] : Math.min(r[1], Math.max(r[0], x));
    });
    if (!THEMES[out.theme]) out.theme = "white";
    if (out.flow !== "scroll" && out.flow !== "page") out.flow = "scroll";
    out.indent = out.indent ? 1 : 0;
    out.font = NV_FONT_MAP[out.font] ? out.font : (safeFamily(out.font) || "default");
    out.bgCustom = /^#[0-9a-fA-F]{6}$/.test(out.bgCustom || "") ? out.bgCustom : "";
    return out;
  }
  N.get = function () {
    try { return norm(JSON.parse(localStorage.getItem(LS) || "null") || {}); }
    catch (e) { return norm({}); }
  };
  N.set = function (patch) {
    var cur = N.get();
    Object.keys(patch || {}).forEach(function (k) { cur[k] = patch[k]; });
    var next = norm(cur);
    try { localStorage.setItem(LS, JSON.stringify(next)); } catch (e) {}
    N.apply();
    document.dispatchEvent(new CustomEvent("kb-novel-pref", { detail: next }));
    return next;
  };
  N.reset = function () {
    try { localStorage.setItem(LS, JSON.stringify(DEF)); } catch (e) {}
    N.apply();
    document.dispatchEvent(new CustomEvent("kb-novel-pref", { detail: N.get() }));
  };
  /** 阅读区色板：自定义背景优先于主题；按亮度自动配文字色 */
  N.inkFor = function (hex) {
    var r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16);
    return (0.299 * r + 0.587 * g + 0.114 * b) > 150 ? "#22242a" : "#d6dae0";
  };
  N.colors = function () {
    var p = N.get();
    if (p.bgCustom) return { bg: p.bgCustom, ink: N.inkFor(p.bgCustom) };
    return { bg: THEMES[p.theme].bg, ink: THEMES[p.theme].ink };
  };
  N.apply = function () {
    var p = N.get(), c = N.colors(), s = document.documentElement.style;
    s.setProperty("--nv-size", p.size + "px");
    s.setProperty("--nv-line", String(p.line));
    s.setProperty("--nv-track", p.track + "px");
    s.setProperty("--nv-gap", p.gap + "px");
    s.setProperty("--nv-indent", p.indent ? "2em" : "0");
    s.setProperty("--nv-maxw", widthMaxStr(p.widthRem));
    s.setProperty("--nv-font", NV_FONT_MAP[p.font] ? (p.font === "default" ? NV_FONT_MAP["default"] : NV_FONT_MAP[p.font]) : '"' + p.font + '", var(--f-body)');
    s.setProperty("--nv-bg", c.bg);
    s.setProperty("--nv-ink", c.ink);
    /* 实测坑（Chromium）：:root 自定义属性变更后，已渲染 .nv-p 的 font-size 不做
       失效重算（新插节点正常）——故关键声明另走字面量 style 标签，改写即全量重匹配。 */
    var fam = NV_FONT_MAP[p.font] ? (p.font === "default" ? "var(--f-body)" : NV_FONT_MAP[p.font]) : '"' + p.font + '", var(--f-body)';
    var tag = document.getElementById("kb-nv-style");
    if (!tag) {
      tag = document.createElement("style");
      tag.id = "kb-nv-style";
      document.head.appendChild(tag);
    }
    tag.textContent =
      ".nv-stage{background:" + c.bg + ";color:" + c.ink + "}" +
      ".nv-pages{max-width:" + widthMaxStr(p.widthRem) + "}" +
      ".nv-stage .nv-p{font-family:" + fam + ";font-size:" + p.size + "px;line-height:" + p.line +
      ";letter-spacing:" + p.track + "px;margin:" + p.gap + "px 0;text-indent:" + (p.indent ? "2em" : "0") + "}" +
      ".nv-stage .nv-chap-h{font-family:" + fam + ";font-size:" + (p.size * 1.25).toFixed(2) + "px}";
    return p;
  };
  N.themes = THEMES;

  /* ================= 设置面板（独立「小说」tab） ================= */
  N.panelHTML = function () {
    var p = N.get();
    var px = function (v) { return v + "px"; };
    var f2 = function (v) { return Number(v).toFixed(2); };
    var row = function (id, label, min, max, step, val, fmt) {
      return '<div class="kb-pref-row">' +
        '<label for="kb-npref-' + id + '">' + label + "</label>" +
        '<input type="range" id="kb-npref-' + id + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + val + '">' +
        '<output id="kb-npref-' + id + '-o">' + fmt(val) + "</output></div>";
    };
    var sel = function (id, label, opts, val) {
      return '<div class="kb-pref-row"><label for="kb-npref-' + id + '">' + label + "</label>" +
        '<select id="kb-npref-' + id + '">' + opts.map(function (o) {
          return '<option value="' + o[0] + '"' + (String(val) === o[0] ? " selected" : "") + ">" + util.esc(o[1]) + "</option>";
        }).join("") + "</select><output aria-hidden=\"true\"></output></div>";
    };
    var grp = function (iconName, title, body) {
      return '<div class="nv-grp"><div class="nv-grp-h">' + util.icon(iconName, 13) + title + "</div>" + body + "</div>";
    };
    var themeBtns = Object.keys(THEMES).map(function (k) {
      var t = THEMES[k];
      return `<button type="button" class="nv-theme-btn${!p.bgCustom && p.theme === k ? " on" : ""}" data-nvtheme="${k}" title="${util.esc(t.name)}" style="background:${t.bg};color:${t.ink};border:1px solid var(--c-line2)">${util.esc(t.name)}</button>`;
    }).join("");
    var curFont = NV_FONT_MAP[p.font] ? "" : '<option value="' + util.esc(p.font) + '" selected>' + util.esc(p.font) + "</option>";
    return '<div class="nv-set">' +
      grp("i-toc-list", "排版",
        row("size", "正文字号", 14, 26, 1, p.size, px) +
        row("line", "行高", 1.5, 2.6, 0.05, p.line, f2) +
        row("track", "字间距", 0, 3, 0.1, p.track, function (v) { return Number(v).toFixed(1) + "px"; }) +
        row("gap", "段间距", 4, 24, 1, p.gap, px) +
        row("widthRem", "正文宽度", 24, 100, 2, p.widthRem, function (v) { return v >= 100 ? "撑满" : v + "rem"; }) +
        '<div class="kb-pref-row nv-row-toggle"><label for="kb-npref-indent">首行缩进</label>' +
        '<label class="nv-switch"><input type="checkbox" id="kb-npref-indent"' + (p.indent ? " checked" : "") + '><span class="nv-switch-t"></span></label>' +
        '<output aria-hidden="true"></output></div>') +
      grp("i-palette", "外观",
        '<div class="kb-pref-row"><label for="kb-npref-font">阅读字体</label>' +
        '<select id="kb-npref-font">' + curFont +
        '<option value="default"' + (p.font === "default" ? " selected" : "") + ">跟随正文</option>" +
        '<option value="serif"' + (p.font === "serif" ? " selected" : "") + ">衬线（宋体）</option>" +
        '<option value="sans"' + (p.font === "sans" ? " selected" : "") + ">无衬线（黑体）</option>" +
        '<option value="mono"' + (p.font === "mono" ? " selected" : "") + ">等宽</option></select>" +
        '<button type="button" class="kb-pref-mini" id="kb-npref-fontsys" title="读取本机字体">系统字体</button></div>' +
        '<div class="nv-theme-grid"><span class="nv-theme-lb">护眼主题</span>' +
        '<div class="nv-theme-row">' + themeBtns +
        '<label class="nv-theme-custom" title="自定义背景色"><input type="color" id="kb-npref-bgcustom" value="' + (p.bgCustom || "#ffffff") + '"><span>自定义</span></label>' +
        "</div></div>") +
      grp("i-book-open", "阅读",
        sel("flow", "txt 阅读模式", [["scroll", "连续滚动"], ["page", "章节分页"]], p.flow) +
        sel("rate", "朗读/滚动速度", [["0.75", "0.75×"], ["1", "1×"], ["1.25", "1.25×"], ["1.5", "1.5×"], ["2", "2×"], ["3", "3×"]], String(p.rate))) +
      '<div class="kb-pref-foot"><button type="button" class="mbtn ghost" id="kb-npref-reset">恢复默认</button>' +
      '<span class="kb-pref-note">仅作用于小说/书库阅读区，存 localStorage</span></div>' +
      "</div>";
  };

  N.bindPanel = function (root) {
    var slider = function (id, key, fmt) {
      var el = root.querySelector("#kb-npref-" + id);
      if (!el) return;
      el.addEventListener("input", function () {
        var o = root.querySelector("#kb-npref-" + id + "-o");
        if (o) o.textContent = fmt(el.value);
        var patch = {}; patch[key] = Number(el.value);
        N.set(patch);
      });
    };
    slider("size", "size", function (v) { return v + "px"; });
    slider("line", "line", function (v) { return Number(v).toFixed(2); });
    slider("track", "track", function (v) { return Number(v).toFixed(1) + "px"; });
    slider("gap", "gap", function (v) { return v + "px"; });
    slider("widthRem", "widthRem", function (v) { return v >= 100 ? "撑满" : v + "rem"; });
    var ind = root.querySelector("#kb-npref-indent");
    if (ind) ind.addEventListener("change", function () { N.set({ indent: ind.checked ? 1 : 0 }); });
    var bindSel = function (id, key, cast) {
      var el = root.querySelector("#kb-npref-" + id);
      if (el) el.addEventListener("change", function () { var p = {}; p[key] = cast(el.value); N.set(p); });
    };
    bindSel("flow", "flow", String);
    bindSel("rate", "rate", Number);
    var font = root.querySelector("#kb-npref-font");
    if (font) font.addEventListener("change", function () { N.set({ font: font.value }); });
    var sysBtn = root.querySelector("#kb-npref-fontsys");
    if (sysBtn) sysBtn.addEventListener("click", function () {
      if (!window.queryLocalFonts) { util.toast("当前浏览器不支持读取系统字体（需 Chrome / Edge）"); return; }
      sysBtn.disabled = true;
      window.queryLocalFonts().then(function (list) {
        var seen = {}, names = [];
        list.forEach(function (f) { if (f.family && !seen[f.family]) { seen[f.family] = 1; names.push(f.family); } });
        names.sort(function (a, b) { return a.localeCompare(b, "zh-Hans-CN"); });
        var selEl = root.querySelector("#kb-npref-font");
        if (!selEl) return;
        selEl.querySelectorAll("optgroup").forEach(function (x) { x.remove(); });
        var og = document.createElement("optgroup");
        og.label = "系统字体 · " + names.length + " 个家族";
        names.forEach(function (n2) {
          var o = document.createElement("option");
          o.value = n2; o.textContent = n2;
          og.appendChild(o);
        });
        selEl.appendChild(og);
        selEl.value = N.get().font;
        sysBtn.disabled = false;
        sysBtn.textContent = "已加载";
      }).catch(function (err) {
        sysBtn.disabled = false;
        util.toast("读取系统字体失败：" + ((err && err.name) || err));
      });
    });
    var themeRow = root.querySelector(".nv-theme-row");
    if (themeRow) themeRow.addEventListener("click", function (e) {
      var b = e.target.closest(".nv-theme-btn");
      if (!b) return;
      N.set({ theme: b.dataset.nvtheme, bgCustom: "" });
      themeRow.querySelectorAll(".nv-theme-btn").forEach(function (x) { x.classList.toggle("on", x === b); });
    });
    var custom = root.querySelector("#kb-npref-bgcustom");
    if (custom) custom.addEventListener("input", function () { N.set({ bgCustom: custom.value }); });
    var reset = root.querySelector("#kb-npref-reset");
    if (reset) reset.addEventListener("click", function () {
      N.reset();
      util.toast("小说偏好已恢复默认");
      var body = root.closest(".kb-set-body") || root;
      var host = body.querySelector("#nv-panel-host");
      if (host) { host.innerHTML = N.panelHTML(); N.bindPanel(body); }
    });
  };

  /* ================= 公共小件 ================= */
  function posKey(rel) { return "kb-nv-pos:" + rel; }
  function savePos(rel, obj) { try { localStorage.setItem(posKey(rel), JSON.stringify(obj)); } catch (e) {} }
  function loadPos(rel) { try { return JSON.parse(localStorage.getItem(posKey(rel)) || "null"); } catch (e) { return null; } }
  N.savePos = savePos; N.loadPos = loadPos;

  /* TTS 引擎：txt/epub 共用，按段落队列朗读，段落级滚动跟随 */
  var tts = {
    on: false, chapter: -1, para: 0, paras: [],
    voice: null,
    pickVoice: function () {
      var vs = window.speechSynthesis ? speechSynthesis.getVoices() : [];
      return vs.filter(function (v) { return /^zh/i.test(v.lang); })[0] || null;
    },
    start: function (paras, chapterIdx, onPara, onDone) {
      if (!window.speechSynthesis) { util.toast("当前浏览器不支持语音朗读"); return; }
      tts.stop();
      tts.on = true; tts.paras = paras; tts.para = 0; tts.chapter = chapterIdx;
      tts.onPara = onPara; tts.onDone = onDone;
      var btn = document.querySelector(".nv-tts.on");
      if (btn) btn.classList.add("busy");
      tts.speakOne();
    },
    speakOne: function () {
      if (!tts.on) return;
      if (tts.para >= tts.paras.length) { tts.stop(); if (tts.onDone) tts.onDone(); return; }
      var text = tts.paras[tts.para];
      if (tts.onPara) tts.onPara(tts.para);
      var u = new SpeechSynthesisUtterance(text);
      u.lang = "zh-CN"; u.rate = N.get().rate;
      if (!tts.voice) tts.voice = tts.pickVoice();
      if (tts.voice) u.voice = tts.voice;
      u.onend = function () { if (!tts.on) return; tts.para++; tts.speakOne(); };
      u.onerror = function () { tts.stop(); };
      speechSynthesis.speak(u);
    },
    stop: function () {
      var was = tts.on;
      tts.on = false;
      if (window.speechSynthesis) speechSynthesis.cancel();
      var btn = document.querySelector(".nv-tts");
      if (btn) btn.classList.remove("busy");
      return was;
    }
  };

  /* 自动滚动：rAF 驱动，速度 = 60px/s × rate */
  var auto = { on: false, raf: 0, el: null };
  function autoTick() {
    if (!auto.on || !auto.el) return;
    var el = auto.el;
    el.scrollTop += (60 * N.get().rate) / 60;
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 2) { autoStop(); return; }
    auto.raf = requestAnimationFrame(autoTick);
  }
  function autoStart(el, btn) {
    if (auto.on) { autoStop(); return; }
    auto.on = true; auto.el = el;
    if (btn) btn.classList.add("on");
    auto.raf = requestAnimationFrame(autoTick);
  }
  function autoStop() {
    auto.on = false;
    if (auto.raf) cancelAnimationFrame(auto.raf);
    var b = document.querySelector(".nv-auto.on");
    if (b) b.classList.remove("on");
  }
  N.autoStop = autoStop;

  /* 章评：写旁挂 .notes.md（复用 /api/note 追加制） */
  function notePrompt(rel, chapTitle) {
    kbModal({
      title: "写章评" + (chapTitle ? " · " + util.esc(chapTitle) : ""),
      body: "备注会追加到该书的 <span class='mono'>" + util.esc(rel) + ".notes.md</span> 旁挂。",
      inputs: [{ key: "tx", label: (chapTitle ? "「" + chapTitle + "」" : "") + "章评内容", placeholder: "这一章……", multiline: true }],
      confirmText: "保存"
    }).then(function (res) {
      if (!res || !res.tx) return;
      fetch("/api/note", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: rel, text: (chapTitle ? "〔章评·" + chapTitle + "〕 " : "") + res.tx }) })
        .then(function (r) { return r.json(); })
        .then(function (d) { util.toast(d.ok ? "章评已记录" : "章评失败：" + (d.error || "")); });
    });
  }
  N.notePrompt = notePrompt;

  /* 工具栏 HTML（txt/epub 共用骨架）；pager: "chap"|"page"|false */
  function toolbarHTML(opts) {
    var pg = opts.pager;
    var prevTxt = pg === "page" ? "上页" : "上章";
    var nextTxt = pg === "page" ? "下页" : "下章";
    return '<div class="nv-toolbar">' +
      (pg ? '<span class="nv-pager"><button class="iconbtn nv-prev-chap" title="' + (pg === "page" ? "上一页" : "上一章") + '">' + icon("chev-left", 13) + " " + prevTxt + "</button>" +
        '<button class="iconbtn nv-next-chap" title="' + (pg === "page" ? "下一页" : "下一章") + '">' + nextTxt + " " + icon("chev-right", 13) + "</button></span>" : "") +
      '<span class="nv-pos" id="nv-pos">—</span>' +
      '<button class="iconbtn nv-pref-btn" title="小说排版设置">' + icon("palette", 13) + " 排版</button>" +
      '<button class="iconbtn nv-find-btn" title="书内搜索">' + icon("search-magnifier", 13) + " 搜索</button>" +
      '<button class="iconbtn nv-note-btn" title="给当前章写章评">' + icon("edit", 13) + " 章评</button>" +
      '<button class="iconbtn nv-tts" title="朗读本章（浏览器 TTS，再点停止）">' + icon("volume-2", 13) + " 朗读</button>" +
      (opts.autoScroll ? '<button class="iconbtn nv-auto" title="自动滚动阅读（再点停止）">' + icon("chev-down", 13) + " 滚动</button>" : "") +
      '<button class="iconbtn nv-dl" title="下载原文件">' + icon("download", 13) + " 下载</button>" +
      "</div>";
  }
  N.toolbarHTML = toolbarHTML;

  /* 右侧面板「目录」桥接：txt/epub 都把章节灌进 #pane-toc，阅读器内不再放左目录 */
  var _pt = { items: [], jump: null, cur: -1 };
  N.registerPaneToc = function (items, jump) {
    _pt.items = items || []; _pt.jump = jump; _pt.cur = 0;
    N.paintPaneToc();
  };
  N.paintPaneToc = function (pane) {
    pane = pane || document.getElementById("pane-toc");
    if (!pane) return;
    if (!_pt.items.length) return;
    pane.innerHTML = _pt.items.map(function (t, i) {
      return '<a href="#" data-pt="' + i + '" class="' + (i === _pt.cur ? "on" : "") + '">' + util.esc(t || "（无标题）") + "</a>";
    }).join("");
    if (!pane.dataset.nvWired) {
      pane.dataset.nvWired = "1";
      pane.addEventListener("click", function (e) {
        var a = e.target.closest("a[data-pt]");
        if (!a || !_pt.jump) return;
        e.preventDefault();
        _pt.jump(Number(a.dataset.pt));
      });
    }
  };
  N.markPaneToc = function (i) {
    if (i === _pt.cur) return;
    _pt.cur = i;
    var pane = document.getElementById("pane-toc");
    if (!pane || !pane.querySelector("a[data-pt]")) return;
    pane.querySelectorAll("a[data-pt]").forEach(function (a) { a.classList.toggle("on", Number(a.dataset.pt) === i); });
    var on = pane.querySelector("a[data-pt].on");
    if (on) on.scrollIntoView({ block: "nearest" });
  };
  N.resetPaneToc = function () { _pt.items = []; _pt.jump = null; _pt.cur = -1; };
  N.hasPaneToc = function () { return _pt.items.length > 0; };

  /* ================= txt 阅读器 ================= */
  var CHAP_RE = /^\s*(第[0-9零一二三四五六七八九十百千两]+[章回卷节部集]|Chapter\s+\d+|CHAPTER\s+\d+|序[章言]?|楔子|引子|番外[篇·]?\S*|尾声|终章|后记)\s*[^\n]{0,40}$/;

  function decodeTxt(buf) {
    var bytes = new Uint8Array(buf), t;
    if (bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF) {
      t = new TextDecoder("utf-8").decode(bytes.slice(3));
    } else {
      try { t = new TextDecoder("utf-8", { fatal: true }).decode(bytes); }
      catch (e) {
        try { t = new TextDecoder("gb18030").decode(bytes); }
        catch (e2) { t = new TextDecoder("big5").decode(bytes); }
      }
    }
    return t;
  }
  N.decodeTxt = decodeTxt;

  function buildChapters(text) {
    var lines = text.split(/\r?\n/);
    var chaps = [], cur = { title: "", start: 0, lines: [] };
    lines.forEach(function (ln, i) {
      if (CHAP_RE.test(ln) && ln.trim().length <= 42) {
        if (cur.lines.length || cur.title) chaps.push(cur);
        cur = { title: ln.trim(), start: i, lines: [] };
      } else cur.lines.push(ln);
    });
    if (cur.lines.length || cur.title) chaps.push(cur);
    if (chaps.filter(function (c) { return c.title; }).length < 2) {
      chaps = [{ title: DOC.title || "全文", start: 0, lines: lines }];
    }
    chaps.forEach(function (c) {
      c.paras = c.lines.join("\n").replace(/^\n+/, "").split(/\n+/).filter(function (p) { return p.trim(); });
    });
    return chaps;
  }

  N.renderTxt = function (wrap, rawHref, rel, sizeMiB) {
    autoStop(); tts.stop();
    wrap.innerHTML = '<div class="nv-reader"><div class="kb-skeleton" aria-busy="true"><i style="width:70%"></i><i style="width:92%"></i></div></div>';
    fetch(rawHref).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.arrayBuffer();
    }).then(decodeTxt).then(function (text) {
      if (!wrap.isConnected) return;
      var chaps = buildChapters(text);
      var paged = N.get().flow === "page";
      wrap.innerHTML = '<div class="nv-reader">' + toolbarHTML({ pager: paged ? "chap" : false, autoScroll: !paged }) +
        '<div class="nv-body-row">' +
        '<div class="nv-stage"><div class="nv-pages"></div></div></div>' +
        '<div class="nv-find" hidden><input class="nv-find-in" placeholder="书内搜索，回车下一处 · Esc 关闭"><span class="nv-find-n"></span><button class="iconbtn nv-find-x">' + icon("cancel-x", 12) + " 关闭</button></div></div>";

      var stage = wrap.querySelector(".nv-stage");
      var pages = wrap.querySelector(".nv-pages");
      var posEl = wrap.querySelector(".nv-pos");
      var findBox = wrap.querySelector(".nv-find");
      var findIn = wrap.querySelector(".nv-find-in");
      var findN = wrap.querySelector(".nv-find-n");
      var built = {};   // chIdx → 已渲染
      var curCh = 0;

      /* 章节目录挂到右侧面板「目录」页签（阅读器内不再放左目录，避免双份） */
      N.registerPaneToc(chaps.map(function (c) { return c.title || "（开头）"; }), function (i) {
        if (paged) { renderPaged(i); }
        else {
          var sec = materialize(i);
          if (!sec.parentNode) pages.appendChild(sec);
          stage.scrollTo({ top: sec.offsetTop - stage.offsetTop, behavior: "smooth" });
          setCur(i);
        }
      });

      function chapEl(i) {
        if (built[i]) return built[i];
        var c = chaps[i];
        var sec = document.createElement("section");
        sec.className = "nv-chap";
        sec.dataset.ch = i;
        if (c.title) {
          var h = document.createElement("h2");
          h.className = "nv-chap-h";
          h.textContent = c.title;
          sec.appendChild(h);
        }
        built[i] = sec;
        return sec;
      }
      function materialize(i) {
        var sec = chapEl(i);
        if (sec.dataset.done) return sec;
        sec.dataset.done = "1";
        chaps[i].paras.forEach(function (p) {
          var el = document.createElement("p");
          el.className = "nv-p";
          el.textContent = p.trim();
          sec.appendChild(el);
        });
        return sec;
      }
      function estHeight(i) {
        var c = chaps[i];
        var chars = c.paras.reduce(function (s, p) { return s + p.length; }, 0);
        return Math.max(140, (c.title ? 50 : 0) + Math.ceil(chars / 38) * (N.get().size * N.get().line) + c.paras.length * N.get().gap);
      }
      function placeholder(i) {
        var sec = chapEl(i);
        if (!sec.dataset.done) {
          var ph = sec.querySelector(".nv-ph");
          if (!ph) {
            ph = document.createElement("div");
            ph.className = "nv-ph";
            sec.appendChild(ph);
          }
          ph.style.height = estHeight(i) + "px";
        }
        return sec;
      }

      var io = null;
      function spyIO() {
        if (io) io.disconnect();
        io = new IntersectionObserver(function (ents) {
          ents.forEach(function (en) {
            if (!en.isIntersecting) return;
            var i = Number(en.target.dataset.ch);
            setCur(i);
          });
        }, { root: stage, rootMargin: "0px 0px -85% 0px", threshold: 0 });
        pages.querySelectorAll(".nv-chap").forEach(function (s) { io.observe(s); });
      }
      function setCur(i) {
        curCh = i;
        var pct = paged ? Math.round(((i + 1) / chaps.length) * 100)
          : Math.round(Math.min(100, (stage.scrollTop + stage.clientHeight) / Math.max(stage.scrollHeight, 1) * 100));
        posEl.textContent = "第 " + (i + 1) + "/" + chaps.length + " 节 · " + (chaps[i].title || "正文") + " · " + pct + "%";
        N.markPaneToc(i);
      }

      /* --- 渲染模式 --- */
      function renderPaged(i) {
        pages.innerHTML = "";
        pages.appendChild(materialize(i));
        setCur(i);
        stage.scrollTop = 0;
        savePos(rel, { ch: i, y: 0 });
      }
      function renderScroll(startCh) {
        pages.innerHTML = "";
        var n = chaps.length;
        // 首屏渲染起点附近 8 章，其余占位；滚动时经 IO 增量实体化
        for (var i = 0; i < n; i++) {
          pages.appendChild(i >= startCh && i < startCh + 8 ? materialize(i) : placeholder(i));
        }
        var lazyIO = new IntersectionObserver(function (ents) {
          ents.forEach(function (en) {
            if (!en.isIntersecting) return;
            materialize(Number(en.target.dataset.ch));
            lazyIO.unobserve(en.target);
          });
        }, { root: stage, rootMargin: "1200px 0px" });
        pages.querySelectorAll(".nv-chap").forEach(function (s) {
          if (!s.dataset.done) lazyIO.observe(s);
        });
        spyIO();
        requestAnimationFrame(function () {
          var pos = loadPos(rel);
          var target = startCh;
          if (pos && typeof pos.ch === "number" && pos.ch !== startCh) target = pos.ch;
          var sec = pages.querySelector('.nv-chap[data-ch="' + target + '"]');
          if (sec) {
            stage.scrollTop = sec.offsetTop + (pos && target === pos.ch ? pos.y || 0 : 0) - stage.offsetTop;
          }
          setCur(target);
        });
      }
      if (paged) renderPaged(0); else renderScroll(0);

      /* 滚动进度与续读记录 */
      var saveT = 0;
      stage.addEventListener("scroll", function () {
        if (paged) return;
        clearTimeout(saveT);
        saveT = setTimeout(function () {
          var sec = pages.querySelector('.nv-chap[data-ch="' + curCh + '"]');
          savePos(rel, { ch: curCh, y: sec ? Math.max(0, stage.scrollTop - sec.offsetTop) : 0 });
          setCur(curCh); // 进度百分比随滚动刷新
        }, 500);
      }, { passive: true });

      /* --- 目录点击已移至右侧面板（paneToc），高亮由 setCur 同步 --- */

      /* --- 分页模式：上/下章 --- */
      var prevB = wrap.querySelector(".nv-prev-chap"), nextB = wrap.querySelector(".nv-next-chap");
      function goCh(d) {
        var i = Math.min(chaps.length - 1, Math.max(0, curCh + d));
        if (paged) renderPaged(i);
        else {
          var sec = materialize(i);
          if (!sec.parentNode) pages.appendChild(sec);
          stage.scrollTo({ top: sec.offsetTop - stage.offsetTop, behavior: "smooth" });
          setCur(i);
        }
      }
      if (prevB) prevB.onclick = function () { goCh(-1); };
      if (nextB) nextB.onclick = function () { goCh(1); };
      wrap.tabIndex = 0;
      wrap.addEventListener("keydown", function (e) {
        if (e.key === "ArrowLeft" && paged) { e.preventDefault(); goCh(-1); }
        else if (e.key === "ArrowRight" && paged) { e.preventDefault(); goCh(1); }
      });

      /* --- 工具栏接线（下载/章评/朗读/自动滚动统一走 rewireChrome） --- */

      /* --- 书内搜索 --- */
      var hits = [], hitIdx = -1;
      function doFind(q) {
        hits = []; hitIdx = -1;
        if (!q || q.length < 1) { findN.textContent = ""; return; }
        var lq = q.toLowerCase();
        var pos = 0;
        for (var ci = 0; ci < chaps.length; ci++) {
          var ctext = chaps[ci].paras.join("\n");
          var low = ctext.toLowerCase();
          var at = low.indexOf(lq);
          while (at >= 0 && hits.length < 100) {
            hits.push({ ch: ci, at: at, snip: ctext.slice(Math.max(0, at - 12), at + q.length + 24).replace(/\n/g, " ") });
            at = low.indexOf(lq, at + q.length);
          }
          if (hits.length >= 100) break;
        }
        findN.textContent = hits.length ? "共 " + hits.length + (hits.length >= 100 ? "+" : "") + " 处" : "无结果";
        nextHit();
      }
      function nextHit() {
        if (!hits.length) return;
        hitIdx = (hitIdx + 1) % hits.length;
        var h = hits[hitIdx];
        findN.textContent = (hitIdx + 1) + "/" + hits.length + " · " + (chaps[h.ch].title || "");
        if (paged) renderPaged(h.ch);
        else {
          var sec = materialize(h.ch);
          if (!sec.parentNode) pages.appendChild(sec);
          stage.scrollTo({ top: sec.offsetTop - stage.offsetTop });
        }
        // 段内高亮：找到包含该偏移的段落
        var acc = 0, paraIdx = 0;
        for (var i = 0; i < chaps[h.ch].paras.length; i++) {
          var pl = chaps[h.ch].paras[i].length;
          if (h.at < acc + pl + 1) { paraIdx = i; break; }
          acc += pl + 1;
        }
        var sec2 = pages.querySelector('.nv-chap[data-ch="' + h.ch + '"]');
        var pel = sec2 && sec2.querySelectorAll(".nv-p")[paraIdx];
        if (pel) {
          sec2.querySelectorAll("mark.nv-hit").forEach(function (m) { m.replaceWith(document.createTextNode(m.textContent)); });
          var q = findIn.value.trim();
          var idx = pel.textContent.toLowerCase().indexOf(q.toLowerCase());
          if (idx >= 0) {
            var frag = document.createDocumentFragment();
            frag.appendChild(document.createTextNode(pel.textContent.slice(0, idx)));
            var mk = document.createElement("mark");
            mk.className = "nv-hit";
            mk.textContent = pel.textContent.slice(idx, idx + q.length);
            frag.appendChild(mk);
            frag.appendChild(document.createTextNode(pel.textContent.slice(idx + q.length)));
            pel.innerHTML = "";
            pel.appendChild(frag);
            mk.scrollIntoView({ block: "center" });
          } else pel.scrollIntoView({ block: "start" });
        }
      }
      wrap.querySelector(".nv-find-btn").onclick = function () {
        findBox.hidden = !findBox.hidden;
        if (!findBox.hidden) findIn.focus();
      };
      findBox.querySelector(".nv-find-x").onclick = function () { findBox.hidden = true; };
      findIn.addEventListener("keydown", function (e) {
        if (e.key === "Enter") { e.preventDefault(); if (hits.length && hitIdx >= 0) nextHit(); else doFind(findIn.value.trim()); }
        else if (e.key === "Escape") { findBox.hidden = true; }
      });

      /* --- 偏好联动：flow 切换即时重建 --- */
      document.addEventListener("kb-novel-pref", function () {
        var nowPaged = N.get().flow === "page";
        if (nowPaged !== paged) {
          var ch = curCh;
          paged = nowPaged;
          var tb = wrap.querySelector(".nv-toolbar");
          tb.outerHTML = toolbarHTML({ pager: paged ? "chap" : false, autoScroll: !paged });
          rewireChrome();
          if (paged) renderPaged(ch); else renderScroll(ch);
        }
      });
      function rewireChrome() {
        prevB = wrap.querySelector(".nv-prev-chap"); nextB = wrap.querySelector(".nv-next-chap");
        if (prevB) prevB.onclick = function () { goCh(-1); };
        if (nextB) nextB.onclick = function () { goCh(1); };
        wrap.querySelector(".nv-pref-btn").onclick = function () { KB.settings.open("novel"); };
        wrap.querySelector(".nv-dl").onclick = function () {
          var a = document.createElement("a");
          a.href = rawHref; a.download = DOC.name || "book.txt"; a.click();
        };
        wrap.querySelector(".nv-note-btn").onclick = function () { notePrompt(rel, chaps[curCh].title); };
        var tb2 = wrap.querySelector(".nv-tts");
        tb2.onclick = function () {
          if (tts.stop()) { tb2.classList.remove("on"); return; }
          tb2.classList.add("on");
          tts.start(chaps[curCh].paras.slice(), curCh, function (pi) {
            var sec = pages.querySelector('.nv-chap[data-ch="' + curCh + '"]');
            var ps = sec ? sec.querySelectorAll(".nv-p") : [];
            if (pi > 0 && ps[pi - 1]) ps[pi - 1].classList.remove("nv-speaking");
            if (ps[pi]) { ps[pi].classList.add("nv-speaking"); ps[pi].scrollIntoView({ block: "center", behavior: "smooth" }); }
          }, function () { tb2.classList.remove("on"); });
        };
        var ab = wrap.querySelector(".nv-auto");
        if (ab) ab.onclick = function () { autoStart(stage, ab); ab.classList.toggle("on", auto.on); };
        wrap.querySelector(".nv-find-btn").onclick = function () { findBox.hidden = !findBox.hidden; if (!findBox.hidden) findIn.focus(); };
      }
      rewireChrome();
      buildToc();
    }).catch(function (e) {
      wrap.innerHTML = '<div class="a-body"><p>读取失败：' + util.esc(String(e && e.message || e)) + "</p></div>";
      buildToc();
    });
  };

  /* ================= epub 阅读器 ================= */
  var _epubLibLoading = null;
  function ensureEpubLib() {
    if (window.ePub) return Promise.resolve();
    if (!_epubLibLoading) {
      _epubLibLoading = loadScript("/static/vendor/jszip.min.js")
        .then(function () { return loadScript("/static/vendor/epub.min.js"); });
    }
    return _epubLibLoading;
  }

  var _epubBook = null, _epubRendition = null;

  /* 实测坑：部分 epub（多看版等）把非法文件名字符（* | :）在 OPF manifest / NCX 里做了百分号编码，
     但 zip 条目存的是原始名。vendored epub.min.js 拿编码 href 直查 JSZip 命中不了（整本空白），
     且 nav 的编码 href 与 spine 的编码 href 还不一致 → 点目录报 No Section Found。
     解法：把 OPF/NCX 里那些"编码查不到、解码能查到"的 href 就地解码，使 spine/nav/zip 三者一致。
     仅当确有此类条目才重建并回传 ArrayBuffer（正常书返回 null，零改动）；ePub 只认 ArrayBuffer，blob URL 会卡死。 */
  async function normalizeEpub(rawHref) {
    var buf = await (await fetch(rawHref)).arrayBuffer();
    var zip = await window.JSZip.loadAsync(buf);
    var container = zip.file("META-INF/container.xml");
    if (!container) return null;
    var m = /full-path="([^"]+)"/.exec(await container.async("string"));
    if (!m) return null;
    var opfPath = decodeAmp(m[1]);
    var prefix = opfPath.indexOf("/") >= 0 ? opfPath.slice(0, opfPath.lastIndexOf("/") + 1) : "";
    var opfFile = zip.file(opfPath);
    if (!opfFile) return null;
    var opf = await opfFile.async("string");
    var dec = function (s) { try { return decodeURIComponent(s); } catch (e) { return s; } };
    var fixes = 0;
    var fixHref = function (raw) {
      var clean = decodeAmp(raw.split("#")[0]);
      if (!clean) return raw;
      if (zip.file(prefix + clean)) return raw;          // 编码形式本就能命中：不动
      var d = dec(clean);
      if (d === clean || !zip.file(prefix + d)) return raw; // 解码后也查不到：不动
      fixes++;
      var frag = raw.indexOf("#") >= 0 ? raw.slice(raw.indexOf("#")) : "";
      return d + frag;
    };
    var opfNew = opf.replace(/(<item\b[^>]*href=")([^"]+)(")/g, function (mm, a, h, b) { return a + fixHref(h) + b; });
    var ncxPath = null;
    var ncxM = /<item\b[^>]*href="([^"]+\.ncx)"[^>]*>/.exec(opfNew) || /<item\b[^>]*media-type="application\/x-dtbncx\+xml"[^>]*href="([^"]+)"/.exec(opfNew);
    if (ncxM) ncxPath = prefix + decodeAmp(ncxM[1]);
    else { var navM = /<item\b[^>]*href="([^"]+)"[^>]*properties="[^"]*nav/.exec(opfNew) || /<item\b[^>]*properties="[^"]*nav[^>]*href="([^"]+)"/.exec(opfNew); if (navM) ncxPath = prefix + decodeAmp(navM[1]); }
    zip.file(opfPath, opfNew);
    if (ncxPath) {
      var nf = zip.file(ncxPath);
      if (nf) {
        var nav = await nf.async("string");
        nav = nav.replace(/(src=")([^"]+)(")/g, function (mm, a, s, b) { return a + fixHref(decodeAmp(s)) + b; });
        nav = nav.replace(/(href=")([^"]+)(")/g, function (mm, a, s, b) { return a + fixHref(decodeAmp(s)) + b; });
        zip.file(ncxPath, nav);
      }
    }
    if (!fixes) return null;
    return zip.generateAsync({ type: "arraybuffer", compression: "STORE" });
  }
  function decodeAmp(s) { return s.replace(/&amp;/g, "&"); }

  N.renderEpub = function (wrap, rawHref, rel) {
    autoStop(); tts.stop();
    wrap.innerHTML = '<div class="nv-reader"><div class="kb-skeleton" aria-busy="true"><i style="width:65%"></i><i style="width:88%"></i></div><p style="color:var(--faint);font-size:12.5px">EPUB 解析中…</p></div>';
    (async function () {
      await ensureEpubLib();
      if (_epubRendition) { try { _epubRendition.destroy(); } catch (e) {} _epubRendition = null; }
      if (_epubBook) { try { _epubBook.destroy(); } catch (e) {} _epubBook = null; }
      wrap.innerHTML = '<div class="nv-reader">' + toolbarHTML({ pager: "page", autoScroll: false }) +
        '<div class="nv-body-row">' +
        '<div class="nv-stage epub"><div id="epub-view"></div></div></div>' +
        '<div class="nv-find" hidden><input class="nv-find-in" placeholder="书内搜索（全 spine），回车下一处 · Esc 关闭"><span class="nv-find-n"></span><button class="iconbtn nv-find-x">' + icon("cancel-x", 12) + " 关闭</button></div></div>";
      var posEl = wrap.querySelector(".nv-pos");
      var findBox = wrap.querySelector(".nv-find");
      var findIn = wrap.querySelector(".nv-find-in");
      var findN = wrap.querySelector(".nv-find-n");

      var epubUrl = rawHref;
      try { var fixed = await normalizeEpub(rawHref); if (fixed) epubUrl = fixed; } catch (e) {}
      var book = window.ePub(epubUrl);
      _epubBook = book;
      var p = N.get();
      var rendition = book.renderTo("epub-view", {
        width: "100%", height: "100%", spread: "none",
        flow: p.flow === "page" ? "paginated" : "scrolled-doc"
      });
      _epubRendition = rendition;
      var scale = 100;
      /* 实测坑：vendored epub.min.js 的 themes.default() 不会作用到已渲染的 section 文档。
         改为往每个 iframe document 注入 <style>（!important 压过书自带样式），随偏好即时重写。 */
      function themeCss() {
        var q = N.get(), c = N.colors();
        var fam = NV_FONT_MAP[q.font] ? (q.font === "default" ? 'Georgia, "Noto Serif SC", serif' : NV_FONT_MAP[q.font]) : '"' + q.font + '", Georgia, serif';
        return "html{font-size:" + q.size + "px !important;line-height:" + q.line + " !important;" +
          "letter-spacing:" + q.track + "px;font-family:" + fam + " !important;" +
          "background:" + c.bg + " !important;color:" + c.ink + " !important}" +
          "body{background:transparent !important;color:" + c.ink + " !important;max-width:" + widthMaxStr(q.widthRem) + ";margin:0 auto;padding:8px 14px}" +
          "p,div,li,td,h1,h2,h3,h4,h5{color:" + c.ink + " !important}" +
          "a,a:link,a:visited,a:hover{color:" + c.ink + " !important;text-decoration:none}" +
          "p{margin:" + q.gap + "px 0 !important;font-size:100% !important;" + (q.indent ? "text-indent:2em !important" : "") + "}";
      }
      function injectTheme() {
        var css = themeCss();
        Array.prototype.forEach.call(wrap.querySelectorAll("iframe"), function (f) {
          try {
            var d = f.contentDocument;
            if (!d || !d.head) return;
            var st = d.getElementById("kb-nv-epub");
            if (!st) { st = d.createElement("style"); st.id = "kb-nv-epub"; d.head.appendChild(st); }
            st.textContent = css;
            /* 多看版封面/插图常因图片文件名编码错乱加载失败，留下大片空白像"正文没了"——隐藏加载失败的图 */
            Array.prototype.forEach.call(d.querySelectorAll("img"), function (im) {
              if (im.complete && im.naturalWidth === 0) im.style.display = "none";
              else if (!im.dataset.nvErr) { im.dataset.nvErr = "1"; im.addEventListener("error", function () { im.style.display = "none"; }); }
            });
          } catch (e) {}
        });
      }
      function applyTheme() {
        try { rendition.themes.fontSize(scale + "%"); } catch (e) {}
        injectTheme();
        setTimeout(injectTheme, 350); // relocated 时 section iframe 可能尚未挂载
      }
      applyTheme();
      var lastFlow = p.flow === "page" ? "paginated" : "scrolled-doc";
      var prefH = function () {
        var q = N.get();
        var wantFlow = q.flow === "page" ? "paginated" : "scrolled-doc";
        /* 只有 flow 真变了才重建视图——rendition.flow() 会触发 relocated 覆盖续读位置，
           若每次改字号/宽度/主题都调用它，进度就被重置回章节开头。 */
        if (wantFlow !== lastFlow) { lastFlow = wantFlow; rendition.flow(wantFlow); }
        applyTheme();
      };
      document.addEventListener("kb-novel-pref", prefH);

      // 书内搜索数据：JSZip 直读 spine 文本（epub.js 不提供全文检索）
      var chapTexts = null;
      async function ensureTexts() {
        if (chapTexts) return chapTexts;
        var buf = await (await fetch(rawHref)).arrayBuffer();
        var zip = await window.JSZip.loadAsync(buf);
        var prefix = (book.packaging && book.packaging.prefix) || "";
        var items = [];
        try { for (var s, i = 0; i < 800 && (s = book.spine.get(i)); i++) { if (s && s.href) items.push(s.href); } } catch (e) { items = []; }
        if (!items.length) zip.forEach(function (path) { if (/\.x?html?$/i.test(path)) items.push(path); });
        var nav = await book.loaded.navigation;
        var tocFlat = [];
        (function walk(list, parents) {
          (list || []).forEach(function (it) {
            tocFlat.push({ href: (it.href || "").split("#")[0], label: (it.label || "").trim(), path: parents.concat(it).map(function (x) { return (x.label || "").trim(); }).filter(Boolean).join(" › ") });
            if (it.subitems && it.subitems.length) walk(it.subitems, parents.concat(it));
          });
        })(nav && nav.toc, []);
        chapTexts = [];
        for (var n = 0; n < items.length; n++) {
          var href = (items[n] || "").split("#")[0];
          if (!href) continue;
          var f = zip.file(href) || zip.file(prefix + href) || zip.file(decodeURIComponent(href)) || zip.file(prefix + decodeURIComponent(href));
          if (!f) continue;
          var html = await f.async("string");
          var doc = new DOMParser().parseFromString(html, "text/html");
          var text = (doc.body && doc.body.textContent || "").replace(/\s+\n/g, "\n").trim();
          if (!text) continue;
          var t = tocFlat.filter(function (x) { return x.href === href; })[0];
          chapTexts.push({ href: items[n], title: t ? t.path : href.split("/").pop(), text: text });
        }
        return chapTexts;
      }

      await rendition.display();
      // 续读：CFI 优先
      try {
        var cfi = loadPos(rel);
        if (cfi && cfi.cfi) await rendition.display(cfi.cfi);
      } catch (e) {}

      var nav2 = await book.loaded.navigation;
      var flat = [];
      (function walk(list) {
        (list || []).forEach(function (it) {
          flat.push({ href: decodeAmp((it.href || "").split("#")[0]), label: (it.label || "").trim() });
          if (it.subitems && it.subitems.length) walk(it.subitems);
        });
      })(nav2 && nav2.toc);
      var curHref = "";
      N.registerPaneToc(flat.map(function (f) { return f.label; }), function (i) {
        var f = flat[i];
        if (f && f.href) { try { rendition.display(f.href); } catch (e) {} }
      });

      var saveT = 0;
      rendition.on("relocated", function (loc) {
        injectTheme();
        var href = loc && loc.start && loc.start.href;
        if (href) {
          curHref = decodeAmp(href.split("#")[0]);
          var idx = -1;
          for (var k = 0; k < flat.length; k++) {
            if (flat[k].href === curHref || (flat[k].href && curHref.indexOf(flat[k].href) === 0)) { idx = k; break; }
          }
          if (idx >= 0) N.markPaneToc(idx);
        }
        if (loc && loc.start && loc.start.cfi) {
          clearTimeout(saveT);
          saveT = setTimeout(function () { savePos(rel, { cfi: loc.start.cfi }); }, 1500);
        }
        try {
          var pct = book.locations && book.locations.total ? Math.round(book.locations.percentageFromCfi(loc.start.cfi) * 100) : NaN;
          var cur = flat[Array.prototype.findIndex.call(flat, function (f) { return f.href === curHref; })];
          posEl.textContent = ((cur && cur.label) || "阅读中") + (isNaN(pct) ? "" : " · " + pct + "%");
        } catch (e) {}
      });
      try { book.locations.generate(1024); } catch (e) {}

      wrap.querySelector(".nv-prev-chap").onclick = function () { rendition.prev(); };
      wrap.querySelector(".nv-next-chap").onclick = function () { rendition.next(); };
      wrap.querySelector(".nv-pref-btn").onclick = function () { KB.settings.open("novel"); };
      wrap.querySelector(".nv-dl").onclick = function () {
        var a = document.createElement("a");
        a.href = rawHref; a.download = DOC.name || "book.epub"; a.click();
      };
      wrap.querySelector(".nv-note-btn").onclick = function () {
        var cur = flat.filter(function (f) { return f.href === curHref; })[0];
        notePrompt(rel, cur ? cur.label : "");
      };
      var ttsBtn = wrap.querySelector(".nv-tts");
      ttsBtn.onclick = async function () {
        if (tts.stop()) { ttsBtn.classList.remove("on"); return; }
        var paras = [];
        try {
          var contents = rendition.getContents();
          var doc = contents && contents[0] && contents[0].document;
          if (doc) paras = Array.prototype.map.call(doc.querySelectorAll("p,h1,h2,h3"), function (el) { return el.textContent.trim(); }).filter(Boolean);
        } catch (e) {}
        if (!paras.length) { util.toast("当前章节没有可朗读的文字"); return; }
        ttsBtn.classList.add("on");
        tts.start(paras, 0, null, function () { ttsBtn.classList.remove("on"); });
      };

      /* 搜索 */
      var hits = [], hitIdx = -1;
      async function doFind(q) {
        hits = []; hitIdx = -1;
        if (!q) { findN.textContent = ""; return; }
        findN.textContent = "索引中…";
        var texts = await ensureTexts();
        var lq = q.toLowerCase();
        for (var i = 0; i < texts.length && hits.length < 100; i++) {
          var low = texts[i].text.toLowerCase(), at = low.indexOf(lq);
          while (at >= 0 && hits.length < 100) {
            hits.push({ href: texts[i].href, title: texts[i].title, snip: texts[i].text.slice(Math.max(0, at - 12), at + q.length + 24).replace(/\s+/g, " ") });
            at = low.indexOf(lq, at + q.length);
          }
        }
        findN.textContent = hits.length ? "共 " + hits.length + (hits.length >= 100 ? "+" : "") + " 处" : "无结果";
        nextHit();
      }
      function nextHit() {
        if (!hits.length) return;
        hitIdx = (hitIdx + 1) % hits.length;
        var h = hits[hitIdx];
        findN.textContent = (hitIdx + 1) + "/" + hits.length + " · " + h.title.slice(-24);
        rendition.display(h.href);
      }
      wrap.querySelector(".nv-find-btn").onclick = function () { findBox.hidden = !findBox.hidden; if (!findBox.hidden) findIn.focus(); };
      findBox.querySelector(".nv-find-x").onclick = function () { findBox.hidden = true; };
      findIn.addEventListener("keydown", function (e) {
        if (e.key === "Enter") { e.preventDefault(); if (hits.length && hitIdx >= 0) nextHit(); else doFind(findIn.value.trim()); }
        else if (e.key === "Escape") findBox.hidden = true;
      });

      wrap.tabIndex = 0;
      wrap.addEventListener("keydown", function (e) {
        if (e.key === "ArrowLeft") { e.preventDefault(); rendition.prev(); }
        else if (e.key === "ArrowRight") { e.preventDefault(); rendition.next(); }
      });
      buildToc();
    })().catch(function (e) {
      wrap.innerHTML = '<div class="a-body"><p>EPUB 解析失败：' + util.esc(String(e && e.message || e)) + "</p>" +
        '<p><a class="chip chip-btn" href="' + rawHref + '" download>' + icon("download", 11) + " 下载后用阅读器打开</a></p></div>";
      buildToc();
    });
  };

  N.apply();
})();
