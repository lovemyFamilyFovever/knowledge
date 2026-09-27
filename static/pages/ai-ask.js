/* =====================================================================
   知库 · pages/ai-ask.js —— 选词问 AI（切片 2）
   只在文档页（workbench）加载。暴露 window.KBAI，其余全在闭包内。

   与后端的契约（app/routes_ai.py + app/ai_qa.py）：
     · 前端只交 path + selection + mode + question/history，**正文由服务端从磁盘现读**；
       所以这里发给服务端的只有选中的那几个字，绝不把整段正文塞进请求体。
     · 域级出站闸门在后端：career / interview / 标了 "ai": false 的域一律 403。
       前端按 /api/ai/config 的 egress_blocked_domains 提前不出现按钮 —— 那只是体验，
       不是防护（防护是那个 403，tests/test_ai_qa.py E 组锁着）。
     · 卡片上必须写明"本次将发送 N 字"：这是最小上下文策略唯一能被用户看见的地方。
   约束：无构建 / 无 ES module / 全局脚本；class 与 id 一律 kb-ai- 前缀。
   ===================================================================== */
(function () {
  "use strict";
  var util = (window.KB && window.KB.util) || null;
  if (!util) return;                       // kb-core 没起来就别插控件（宁可不出现）

  var state = {
    cfg: null,          // /api/ai/config 的脱敏视图（含出站黑名单）
    path: "",           // 当前文档 rel
    selection: "",
    mode: "term",
    history: [],        // 本次会话的多轮（只存内存 + 交给服务端进缓存键）
    last: null,         // 最近一次成功响应（复制 / 落盘动作要用）
    busy: false
  };

  function $(id) { return document.getElementById(id); }
  function bodyEl() { return document.querySelector("#article .a-body"); }
  function doc() { return window.DOC || null; }
  function esc(s) { return util.esc(s); }
  function toast(m) { try { util.toast(m); } catch (e) { } }

  function post(path, payload) {
    return fetch(path, {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then(function (r) {
      return r.json().catch(function () { return { ok: false, error: "响应不是合法 JSON" }; })
        .then(function (j) { j.__status = r.status; return j; });
    });
  }
  function get(path) {
    return fetch(path, { credentials: "same-origin" })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }

  function loadCfg() {
    if (state.cfg) return Promise.resolve(state.cfg);
    return get("/api/ai/config").then(function (j) {
      state.cfg = (j && j.ok) ? j : { egress_blocked_domains: [], key_present: false };
      return state.cfg;
    }).catch(function () {
      state.cfg = { egress_blocked_domains: [], key_present: false };
      return state.cfg;
    });
  }

  function blockedNow() {
    var d = doc();
    if (!d || !d.domain || !state.cfg) return false;
    return (state.cfg.egress_blocked_domains || []).indexOf(d.domain) >= 0;
  }

  /* ---------------------------------------------------------------- DOM */
  function ensureChip() {
    var el = $("kb-ai-chip");
    if (el) return el;
    el = document.createElement("button");
    el.type = "button";
    el.id = "kb-ai-chip";
    el.className = "kb-ai-chip";
    el.hidden = true;
    el.addEventListener("mousedown", function (e) { e.preventDefault(); });  // 别把选区弄没
    el.addEventListener("click", function () { openCard(); });
    document.body.appendChild(el);
    return el;
  }

  function ensureCard() {
    var el = $("kb-ai-card");
    if (el) return el;
    el = document.createElement("div");
    el.id = "kb-ai-card";
    el.className = "kb-ai-card";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-label", "问 AI");
    el.hidden = true;
    el.innerHTML =
      '<div class="kb-ai-ch"><b id="kb-ai-title">问 AI</b>' +
      '<button type="button" class="kb-ai-x" id="kb-ai-x" aria-label="关闭">✕</button></div>' +
      '<div class="kb-ai-modes" id="kb-ai-modes">' +
      '  <button type="button" data-mode="term">词</button>' +
      '  <button type="button" data-mode="passage">这段</button>' +
      '  <button type="button" data-mode="full">整篇</button>' +
      '  <span class="kb-ai-size" id="kb-ai-size">计算中…</span>' +
      "</div>" +
      '<div class="kb-ai-warn" id="kb-ai-warn" hidden></div>' +
      '<div class="kb-ai-answer" id="kb-ai-answer">点「问」开始。默认只发送选中内容、' +
      '所在段落前后各一段、本篇大纲与本地检索命中的三小段。</div>' +
      '<div class="kb-ai-meta" id="kb-ai-meta"></div>' +
      '<div class="kb-ai-ask"><input type="text" id="kb-ai-q" placeholder="追问一句…（Enter 发送）">' +
      '<button type="button" class="kb-ai-mini" id="kb-ai-go">问</button></div>' +
      '<div class="kb-ai-acts">' +
      '  <button type="button" class="kb-ai-mini" id="kb-ai-note">加进本篇批注</button>' +
      '  <button type="button" class="kb-ai-mini" id="kb-ai-term">存为术语</button>' +
      '  <button type="button" class="kb-ai-mini ghost" id="kb-ai-copy">复制</button>' +
      "</div>" +
      '<div class="kb-ai-draft" id="kb-ai-draft" hidden>' +
      '  <label for="kb-ai-dpath">落盘路径（可改）</label>' +
      '  <input type="text" id="kb-ai-dpath">' +
      '  <label for="kb-ai-dtext">词条草稿（可改）</label>' +
      '  <textarea id="kb-ai-dtext" rows="8" spellcheck="false"></textarea>' +
      '  <div class="kb-ai-dacts"><button type="button" class="kb-ai-mini" id="kb-ai-dsave">确认新建</button>' +
      '  <button type="button" class="kb-ai-mini ghost" id="kb-ai-dcancel">取消</button></div>' +
      '  <p class="kb-ai-note">走的是既有的 /api/save 写回路径（frontmatter 自动补齐、索引同步更新）；' +
      "AI 不会自己去改任何已有正文。</p>" +
      "</div>";
    document.body.appendChild(el);
    wireCard(el);
    return el;
  }

  function ensureRail() {
    var el = $("kb-ai-rail");
    if (el) return el;
    el = document.createElement("div");
    el.id = "kb-ai-rail";
    el.className = "kb-ai-rail";
    el.hidden = true;
    el.innerHTML = '<div class="kb-ai-rail-h">本篇问过的' +
      '<button type="button" class="kb-ai-x" id="kb-ai-rail-x" aria-label="收起">✕</button></div>' +
      '<div class="kb-ai-rail-b" id="kb-ai-rail-b"></div>';
    document.body.appendChild(el);
    $("kb-ai-rail-x").addEventListener("click", function () { el.hidden = true; });
    $("kb-ai-rail-b").addEventListener("click", function (e) {
      var it = e.target.closest("[data-sel]");
      if (!it) return;
      state.selection = it.getAttribute("data-sel") || "";
      state.mode = it.getAttribute("data-mode") || "term";
      state.history = [];
      openCard(true);
    });
    return el;
  }

  /* ---------------------------------------------------------------- 选区 */
  function currentSelection() {
    var s = window.getSelection && window.getSelection();
    if (!s || s.isCollapsed) return null;
    var text = String(s.toString() || "").replace(/\s+/g, " ").trim();
    if (text.length < 2) return null;
    var host = bodyEl();
    if (!host) return null;
    var range = s.rangeCount ? s.getRangeAt(0) : null;
    // 判据就一条：选区必须落在正文容器里。卡片/浮层是挂在 body 上的，不在 .a-body 内，
    // 所以在卡片里选字天然不会再来一层按钮 —— 不需要额外的"排除卡片"分支
    // （原先写了那条，变异测试证明它永远走不到，属于死代码，已删）。
    if (!range || !host.contains(range.commonAncestorContainer)) return null;
    var rect = range.getBoundingClientRect();
    return { text: text, rect: rect };
  }

  var hideTimer = null;
  function onSelectionChange() {
    var chip = ensureChip();
    var sel = currentSelection();
    var d = doc();
    if (!sel || !d || editorOpen() || inNovelView()) { chip.hidden = true; return; }
    loadCfg().then(function () {
      if (blockedNow()) { chip.hidden = true; return; }   // 后端还会再 403 一次
      state.selection = sel.text;
      state.mode = sel.text.length > 80 ? "passage" : "term";
      chip.textContent = sel.text.length > 80 ? "问 AI：这段" : "问 AI";
      chip.hidden = false;
      var w = chip.offsetWidth || 74, h = chip.offsetHeight || 26;
      chip.style.left = Math.max(8, Math.min(window.innerWidth - w - 8,
                                             sel.rect.right - w)) + "px";
      chip.style.top = Math.max(8, sel.rect.top - h - 6) + "px";
      chip.dataset.sel = sel.text;
      clearTimeout(hideTimer);
      // 选中后 6s 没人动就自己收起来，免得挡着阅读
      hideTimer = setTimeout(function () { chip.hidden = true; }, 6000);
    });
  }

  function editorOpen() {
    var ed = $("editor");
    return !!(ed && ed.classList.contains("show"));
  }
  function inNovelView() {
    // 小说/epub 阅读视图里没有 .a-body，但 iframe 里可能残留选区：一律不出现
    return !!document.querySelector(".nv-shell, #nv-frame") ||
      (doc() && /\.(txt|epub|mobi|pdf|xlsx)$/i.test((doc().name || "")));
  }

  /* ---------------------------------------------------------------- 卡片 */
  function openCard(silentAsk) {
    var card = ensureCard();
    card.hidden = false;
    positionCard();
    $("kb-ai-title").textContent = state.selection.length > 24
      ? state.selection.slice(0, 24) + "…" : state.selection;
    $("kb-ai-answer").textContent = "正在算要发出去多少字…";
    $("kb-ai-meta").textContent = "";
    $("kb-ai-draft").hidden = true;
    syncModes();
    preview();
    if (silentAsk) ask();
  }

  function positionCard() {
    var card = $("kb-ai-card"), chip = $("kb-ai-chip");
    if (!card || card.hidden) return;
    var cw = 380, chh = Math.min(card.offsetHeight || 420, window.innerHeight - 24);
    var left = Math.max(12, Math.min(window.innerWidth - cw - 12,
                                     (chip && !chip.hidden ? chip.offsetLeft : 200)));
    var top = (chip && !chip.hidden ? chip.offsetTop + 30 : 120);
    if (top + chh > window.innerHeight - 12) top = Math.max(12, window.innerHeight - chh - 12);
    card.style.left = left + "px";
    card.style.top = top + "px";
  }

  function syncModes() {
    util.$$("#kb-ai-modes [data-mode]").forEach(function (b) {
      b.classList.toggle("on", b.dataset.mode === state.mode);
    });
  }

  function setBusy(on, msg) {
    state.busy = !!on;
    var go = $("kb-ai-go");
    ["kb-ai-go", "kb-ai-note", "kb-ai-term", "kb-ai-copy"].forEach(function (id) {
      var el = $(id);
      if (el) el.disabled = !!on;
    });
    if (go) go.textContent = on ? "…" : "问";
    if (msg) { $("kb-ai-answer").textContent = msg; }
  }

  function payload(extra) {
    var p = { path: state.path, selection: state.selection, mode: state.mode };
    if (extra && extra.question) { p.question = extra.question; p.history = state.history; }
    if (extra && extra.dry) p.dry = true;
    return p;
  }

  function preview() {
    post("/api/ai/explain", payload({ dry: true })).then(function (j) {
      var size = $("kb-ai-size"), warn = $("kb-ai-warn");
      if (!j || j.ok !== true) {
        size.textContent = "预览失败";
        warn.hidden = false;
        warn.textContent = (j && (j.error || j.code)) || "读不到预览";
        $("kb-ai-answer").textContent = "先解决上面的提示再问。";
        return;
      }
      size.textContent = "本次将发送约 " + j.sent_chars + " 字" +
        (j.rag_hits ? "（含本地检索 " + j.rag_hits + " 段）" : "（无本地检索命中）");
      warn.hidden = !!j.located;
      if (!j.located) {
        warn.textContent = "服务端在文档里没定位到这段选中内容（文档可能刚被改过）——" +
          "这时问下去只会得到没有上下文的答案，建议重新选一次。";
        $("kb-ai-answer").textContent = "重新选中要问的词或句子。";
      }
    }).catch(function (e) {
      // 没有这个 catch，请求一失败卡片就永远停在"计算中…"—— 探针实测就是这样躺死的
      var size = $("kb-ai-size"), warn = $("kb-ai-warn");
      if (size) size.textContent = "预览失败";
      if (warn) { warn.hidden = false; warn.textContent = "算字数失败：" + ((e && e.message) || e); }
      var a = $("kb-ai-answer");
      if (a) a.textContent = "可以先点「问」直接试一次。";
    });
  }

  function ask() {
    if (state.busy) return;
    var qEl = $("kb-ai-q");
    var q = qEl ? qEl.value.trim() : "";
    setBusy(true, "问 AI 中…");
    post("/api/ai/explain", payload({ question: q })).then(function (j) {
      setBusy(false);
      render(j, q);
    }).catch(function (e) {
      setBusy(false);
      $("kb-ai-answer").textContent = "请求失败：" + ((e && e.message) || e);
    });
  }

  function render(j, q) {
    var ans = $("kb-ai-answer"), meta = $("kb-ai-meta");
    if (!j || j.ok !== true) {
      state.last = null;
      // 后端的 error 已经把"为什么 + 去哪修"讲清了（未配置时会写"设置 → AI 页签"），
      // 这里只补它没覆盖的那一种：403 的 error 里只有域名，得说明是谁定的规矩。
      ans.textContent = "没问出来：" + ((j && (j.error || j.code)) || "未知错误") +
        (j && j.code === "domain_blocked" ? " —— 这是分类学里定的不出站规矩，不是故障。" : "");
      meta.textContent = "";
      return;
    }
    state.last = j;
    ans.innerHTML = mdLite(j.answer || "");
    var bits = [];
    bits.push(j.cached ? "缓存里的答案（没再计费）" : "新问的 · " +
      ((j.usage && j.usage.total_tokens) || 0) + " tokens");
    bits.push("置信 " + ({ high: "高", medium: "中", low: "低" }[j.confidence] || j.confidence));
    bits.push("发送 " + j.sent_chars + " 字");
    if (j.where) bits.push(j.where);
    meta.textContent = bits.join(" · ");
    var src = (j.sources || []).filter(Boolean);
    if (src.length) {
      meta.innerHTML += '<div class="kb-ai-src">引用：' +
        src.map(function (s) { return "<code>" + esc(s) + "</code>"; }).join(" ") + "</div>";
    }
    if (q) {
      state.history = state.history.concat([
        { role: "user", content: q },
        { role: "assistant", content: String(j.answer || "").slice(0, 1200) }]);
      if (state.history.length > 6) state.history = state.history.slice(-6);
      $("kb-ai-q").value = "";
    }
    loadRail();
  }

  /* 只支持 **粗体** / `行内码` / 换行 / - 列表：先整体转义再拼，绝不把模型输出当 HTML 塞进去 */
  function mdLite(text) {
    var s = esc(String(text || ""));
    s = s.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*([^*\n]+)\*\*/g, "<b>$1</b>");
    s = s.replace(/^\s*[-*]\s+(.+)$/gm, "• $1");
    return s.split(/\n{2,}/).map(function (p) {
      return "<p>" + p.replace(/\n/g, "<br>") + "</p>";
    }).join("");
  }

  /* ---------------------------------------------------------------- 动作 */
  function noteIt() {
    var j = state.last;
    if (!j || !j.answer) { toast("还没有可落盘的答案"); return; }
    var oneLine = String(j.answer).replace(/\s*\n\s*/g, " ").trim();
    var text = "AI 问「" + state.selection.slice(0, 40) + "」：" + oneLine +
      "（" + (j.cached ? "缓存" : j.model || "AI") + " · 置信 " + j.confidence + "）";
    setBusy(true);
    post("/api/note", { path: state.path, text: text }).then(function (r) {
      setBusy(false);
      toast(r && r.ok ? "已写进本篇批注（sidecar .notes.md，正文一字未动）"
                      : "写批注失败：" + ((r && r.error) || "未知错误"));
    }).catch(function (e) { setBusy(false); toast("写批注失败：" + e.message); });
  }

  function slug(s) {
    return String(s).replace(/[\\/:*?"<>|\s]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40) || "术语";
  }

  function openDraft() {
    var j = state.last;
    if (!j || !j.answer) { toast("先问出答案再存术语"); return; }
    var d = doc() || {};
    var dir = (d.rel || "").split("/");
    dir.pop();
    var base = (dir.length >= 2 ? dir.slice(0, 2).join("/") : (d.domain || "baike"));
    $("kb-ai-dpath").value = base + "/" + slug(state.selection) + ".md";
    var terms = (j.terms || []).map(function (x) {
      return "- **" + x.term + "**：" + x.brief;
    }).join("\n");
    $("kb-ai-dtext").value = "---\ntitle: \"" + state.selection.replace(/"/g, "'") +
      "\"\ntags: [AI生成待核]\n---\n\n# " + state.selection +
      "\n\n## 定义\n\n> 💡 一句话定义：" +
      String(j.answer).replace(/\s*\n\s*$/, "").split(/\n/)[0] + "\n\n" +
      String(j.answer) + "\n" + (terms ? "\n## 相关术语\n\n" + terms + "\n" : "") +
      "\n## 出处\n\n- 本篇：" + (d.rel || "") + "\n" +
      (j.sources || []).map(function (s) { return "- " + s; }).join("\n") +
      "\n\n> ⚠️ 本词条由 AI 生成，未人工核对。\n";
    $("kb-ai-draft").hidden = false;
  }

  function saveDraft() {
    var path = $("kb-ai-dpath").value.trim();
    var content = $("kb-ai-dtext").value;
    if (!path.endsWith(".md")) { toast("路径必须以 .md 结尾"); return; }
    setBusy(true);
    post("/api/save", { path: path, content: content }).then(function (r) {
      setBusy(false);
      if (r && r.ok) {
        $("kb-ai-draft").hidden = true;
        toast("已新建 " + r.path + "（frontmatter " + r.fm_status + "）");
        setTimeout(function () { location.href = "/doc/" + r.path.replace(/\.md$/, ""); }, 900);
      } else {
        toast("保存失败：" + ((r && r.error) || "未知错误"));
      }
    }).catch(function (e) { setBusy(false); toast("保存失败：" + e.message); });
  }

  function copyIt() {
    var j = state.last;
    if (!j || !j.answer) { toast("还没有可复制的答案"); return; }
    var txt = "【" + state.selection + "】\n" + j.answer;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(function () { toast("已复制"); },
                                           function () { toast("浏览器拒绝剪贴板写入"); });
    } else { toast("当前环境没有剪贴板接口"); }
  }

  function loadRail() {
    var d = doc();
    var rail = ensureRail();
    if (!d || !d.rel || blockedNow()) { rail.hidden = true; return Promise.resolve(); }
    return get("/api/ai/qa?path=" + encodeURIComponent(d.rel)).then(function (j) {
      var items = (j && j.items) || [];
      if (!items.length) { rail.hidden = true; return; }
      rail.hidden = false;
      $("kb-ai-rail-b").innerHTML = items.map(function (it) {
        return '<button type="button" class="kb-ai-rail-i" data-sel="' + esc(it.selection) +
          '" data-mode="' + esc(it.mode) + '"><b>' + esc(it.selection) + "</b>" +
          "<span>" + esc(String(it.answer || "").slice(0, 46)) + "…</span></button>";
      }).join("");
    }).catch(function () { rail.hidden = true; });
  }

  function wireCard() {
    $("kb-ai-x").addEventListener("click", function () { $("kb-ai-card").hidden = true; });
    $("kb-ai-modes").addEventListener("click", function (e) {
      var b = e.target.closest("[data-mode]");
      if (!b) return;
      state.mode = b.dataset.mode;
      syncModes();
      preview();
    });
    $("kb-ai-go").addEventListener("click", ask);
    $("kb-ai-q").addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); ask(); }
    });
    $("kb-ai-note").addEventListener("click", noteIt);
    $("kb-ai-term").addEventListener("click", openDraft);
    $("kb-ai-copy").addEventListener("click", copyIt);
    $("kb-ai-dsave").addEventListener("click", saveDraft);
    $("kb-ai-dcancel").addEventListener("click", function () { $("kb-ai-draft").hidden = true; });
  }

  /* ---------------------------------------------------------------- 启动 */
  function resetFor(path) {
    state.path = path || "";
    state.history = [];
    state.last = null;
    var chip = $("kb-ai-chip"), card = $("kb-ai-card");
    if (chip) chip.hidden = true;
    if (card) card.hidden = true;
    loadRail();
  }

  var pending = null;
  document.addEventListener("selectionchange", function () {
    clearTimeout(pending);
    pending = setTimeout(onSelectionChange, 180);
  });
  window.addEventListener("scroll", function () {
    var chip = $("kb-ai-chip");
    if (chip && !chip.hidden) chip.hidden = true;
  }, true);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      var card = $("kb-ai-card");
      if (card && !card.hidden) { card.hidden = true; e.stopPropagation(); }
    }
  }, true);

  /* ---------------------------------------------------------------- 查漏补缺（切片 3） */
  function ensureAudit() {
    var el = $("kb-audit-panel");
    if (el) return el;
    el = document.createElement("div");
    el.id = "kb-audit-panel";
    el.className = "kb-ai-card kb-audit";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-label", "本篇查漏补缺");
    el.hidden = true;
    el.innerHTML =
      '<div class="kb-ai-ch"><b>本篇查漏补缺</b>' +
      '<button type="button" class="kb-ai-mini ghost" id="kb-au-rescan">重新扫描</button>' +
      '<button type="button" class="kb-ai-mini ghost" id="kb-au-domain">扫描整个域</button>' +
      '<button type="button" class="kb-ai-x" id="kb-au-x" aria-label="关闭">✕</button></div>' +
      '<div class="kb-au-sum" id="kb-au-sum">扫描中…</div>' +
      '<div id="kb-au-list"></div>' +
      '<div id="kb-au-gaps"></div>' +
      '<div class="kb-au-batch" id="kb-au-batch" hidden></div>' +
      '<p class="kb-ai-note">采纳只写 sidecar 批注（.notes.md），正文一个字节都不改；' +
      "改正文由你自己动手。忽略会被记住，重扫不会再来烦你。</p>";
    document.body.appendChild(el);
    $("kb-au-x").addEventListener("click", function () { el.hidden = true; });
    $("kb-au-rescan").addEventListener("click", function () { audit(true); });
    $("kb-au-domain").addEventListener("click", batchEstimate);
    function actHandler(scope) {
      return function (e) {
        var b = e.target.closest("[data-act]");
        if (!b) return;
        var item = b.closest("[data-id]");
        if (!item) return;
        auditAction(item.getAttribute("data-id"), item.getAttribute("data-title"),
                    item.getAttribute("data-sug"), b.getAttribute("data-act"), b, scope);
      };
    }
    $("kb-au-list").addEventListener("click", actHandler(null));
    // 域级待办走同一套处置，只是 path 换成了作用域键 @domain:<域>
    $("kb-au-gaps").addEventListener("click", actHandler("domain"));
    return el;
  }

  function audit(force) {
    var d = doc();
    if (!d || !d.rel) { toast("这一页没有可扫描的文档"); return; }
    var panel = ensureAudit();
    loadGaps(d.domain);
    panel.hidden = false;
    panel.style.left = "auto";
    panel.style.right = "16px";
    panel.style.top = "86px";
    var sum = $("kb-au-sum");
    if (sum) sum.textContent = (force ? "重新扫描中…" : "扫描中…");
    post("/api/ai/audit", { path: d.rel }).then(function (j) {
      if (!j || j.ok !== true) {
        if (sum) sum.textContent = "扫描失败：" + ((j && j.error) || "未知错误");
        $("kb-au-list").innerHTML = "";
        return;
      }
      renderAudit(j);
    }).catch(function (e) {
      if (sum) sum.textContent = "扫描失败：" + ((e && e.message) || e);
    });
  }

  /* -------------------------------------------------- 本域覆盖空白（切片 4 收尾算出来的） */
  var GAP_SEV = { high: "要紧", medium: "结构", low: "可选" };

  function loadGaps(domain) {
    var box = $("kb-au-gaps");
    if (!box || !domain) return;
    get("/api/ai/audit?path=" + encodeURIComponent("@domain:" + domain))
      .then(function (j) {
        var ps = ((j && j.proposals) || []).filter(function (p) {
          return p.kind === "coverage_gap";
        });
        if (!ps.length) { box.innerHTML = ""; return; }
        box.innerHTML = '<div class="kb-au-gaps-h">本域覆盖空白 · ' + ps.length +
          " 条（随「扫描整个域」算出来，不是这一篇的问题）</div>" +
          ps.map(function (p) {
            return '<div class="kb-au-item" data-id="' + esc(p.id) + '" data-title="' +
              esc(p.title) + '" data-sug="' + esc(p.suggestion) + '" data-status="' +
              esc(p.status || "pending") + '"><div class="kb-au-h"><span class="kb-au-sev ' +
              esc(p.severity) + '">' + (GAP_SEV[p.severity] || esc(p.severity)) + "</span><b>" +
              esc(p.title) + "</b>" + (p.status && p.status !== "pending"
                ? '<i class="kb-au-state">' + (p.status === "dismissed" ? "已忽略" : "已处理") +
                  "</i>" : "") + '</div><div class="kb-au-ev">' + esc(p.evidence) +
              "</div><div class=\"kb-au-sg\">" + esc(p.suggestion) + "</div>" +
              (p.ai_terms && p.ai_terms.length
                ? '<div class="kb-au-ai">AI 复核认为值得补：<b>' + esc(p.ai_terms.join("、")) +
                  "</b>" + (p.ai_note ? "<span>" + esc(p.ai_note) + "</span>" : "") + "</div>"
                : (p.ai_note ? '<div class="kb-au-ai muted">' + esc(p.ai_note) + "</div>" : "")) +
              '<div class="kb-au-acts">' +
              '<button type="button" class="kb-ai-mini ghost" data-act="dismiss">' +
              (p.status === "dismissed" ? "已忽略" : "忽略") + "</button>" +
              (p.status && p.status !== "pending"
                ? '<button type="button" class="kb-ai-mini ghost" data-act="pending">恢复待处理</button>'
                : "") + "</div></div>";
          }).join("") +
          '<p class="kb-au-gap-note">补哪一篇由你自己动手（新知识走 content/_inbox/）；' +
          "这里只列清单，不会替你建文件。</p>";
      }).catch(function () { /* 域待办读不到不影响本篇面板 */ });
  }

  var SEV_TEXT = { high: "要紧", medium: "结构", low: "可选" };

  /* ------------------------------------------------------------ 批量（切片 4） */
  var BATCH_TIMER = null;

  function batchBox() { return $("kb-au-batch"); }

  function estLine(e, avail) {
    var money = e.cost_est > 0 ? "≈ ¥" + e.cost_est.toFixed(4)
                               : "单价没填，只能给 token 数";
    var left = e.budget_left === null || e.budget_left === undefined
      ? "本月没设预算帽" : ("本月还剩 " + e.budget_left + " 次");
    // 抽样出来的都是估算值，一律冠"约"；精确扫的才准报整数。
    var p = e.sampled ? "约 " : "";
    return e.docs + " 篇 · 本地判据" + (e.sampled ? "抽样推出" : "查出") + " " +
      p + e.findings + " 条 · 还要问 AI " + p + e.calls_expected + " 次" +
      "（每篇都可能问一次，最多 " + e.calls_upper_bound + " 次）· " +
      (avail ? "已配 key" : "没配 key，问了也不会跑") + " · " +
      "预计 ≤ " + p + (e.tokens_in_est + e.tokens_out_est) + " tokens，" + money + " · " + left +
      (e.truncated ? " · 注：范围超过 " + e.will_scan + " 篇，这一批只跑前 " + e.will_scan + " 篇" : "");
  }

  function batchEstimate() {
    var d = doc();
    var box = batchBox();
    if (!d || !d.domain) { toast("这一页没有可扫描的域"); return; }
    box.hidden = false;
    box.innerHTML = '<div class="kb-au-est">正在估算…（本地扫一遍，不出网、不计费）</div>';
    post("/api/ai/batch/estimate", { scope: { domain: d.domain } }).then(function (j) {
      if (!j || j.ok !== true) {
        box.innerHTML = '<div class="kb-au-est bad">估算失败：' +
          esc((j && j.error) || "未知错误") + "</div>";
        return;
      }
      var e = j.estimate;
      // 能跑的那条路才画：没配 key / 超帽时画一颗灰钮只是让人多点一次失败，
      // 上面那行已经写清"为什么现在不能开"。
      var canAi = !e.over_budget && j.ai_available;
      box.innerHTML = '<div class="kb-au-est">' + esc(estLine(e, j.ai_available)) + "</div>" +
        (e.over_budget
          ? '<div class="kb-au-est warn">超出预算帽：带 AI 的批量不会开跑。' +
            "可以先调高设置 → AI 里的月度次数、把范围缩到子域，或者只跑本地判据。</div>"
          : "") +
        '<div class="kb-au-acts">' +
        '<button type="button" class="kb-ai-mini" id="kb-au-b-local">只跑本地（0 次）</button>' +
        (canAi ? '<button type="button" class="kb-ai-mini" id="kb-au-b-ai">按估算开跑</button>' : "") +
        "</div>";
      $("kb-au-b-local").onclick = function () { batchStart(false, d.domain); };
      if (canAi) $("kb-au-b-ai").onclick = function () { batchStart(true, d.domain); };
    }).catch(function (e2) {
      box.innerHTML = '<div class="kb-au-est bad">估算请求没成：' + esc(e2.message) + "</div>";
    });
  }

  function gapLine(g) {
    // 复核跑没跑都要报：清单少了什么、为什么少，用户得看得见（不静默降级）
    if (!g) return "";
    // 一批里一条空白都没有，就没必要再报一句"0 条里挑中 0 条" —— 那是噪声。
    // 但"有候选却没复核"必须报，否则用户会把本地清单当成 AI 认过的。
    if (g.ran) {
      if (!g.total) return "";
      return '<div class="kb-au-est">覆盖空白 AI 复核：' + g.total + " 条候选里挑中 " + g.picked +
        " 条值得补（没挑中的仍留在清单上，只是标了原因）</div>";
    }
    return '<div class="kb-au-est warn">覆盖空白 AI 复核没跑：' +
      esc(g.reason || "未启用") + "</div>";
  }

  function batchStart(withAi, domain) {
    post("/api/ai/batch/start", { scope: { domain: domain }, ai: withAi }).then(function (j) {
      if (!j || j.ok !== true) {
        toast((j && j.error) || "批量没开起来");
        if (j && j.code === "over_budget") batchEstimate();
        return;
      }
      toast("批量扫描已开始，可以随时点「扫描整个域」看进度");
      pollBatch();
    });
  }

  function pollBatch() {
    if (BATCH_TIMER) clearTimeout(BATCH_TIMER);
    var box = batchBox();
    var tick = function () {
      get("/api/ai/batch/status").then(function (j) {
        var s = (j && j.job) || {};
        if (box) {
          box.hidden = false;
          box.innerHTML = '<div class="kb-au-est">' + esc(s.state || "?") + " · 已完成 " +
            (s.done || 0) + " / " + (s.total || 0) + " 篇 · 问 AI " + (s.ai_calls || 0) + " 次" +
            (s.error_count ? " · " + s.error_count + " 篇没读动" : "") + "</div>" +
            (s.ai_stopped_reason
              ? '<div class="kb-au-est warn">' + esc(s.ai_stopped_reason) + "</div>" : "") +
            gapLine(s.gap_review) +
            (s.running
              ? '<div class="kb-au-acts"><button type="button" class="kb-ai-mini ghost" ' +
                'id="kb-au-b-stop">停止</button></div>'
              : "");
          if (s.running) {
            $("kb-au-b-stop").onclick = function () {
              post("/api/ai/batch/stop", {}).then(pollBatchNow);
            };
          }
        }
        if (!s.running) {
          BATCH_TIMER = null;
          if (s.state === "done" || s.state === "stopped") {
            toast("批量扫完了，打开任意一篇就能看到它的建议");
            audit(true);
          }
          return;
        }
        BATCH_TIMER = setTimeout(tick, 500);
      }).catch(function () { BATCH_TIMER = null; });
    };
    tick();
  }

  function pollBatchNow() {
    var box = batchBox();
    fetch("/api/ai/batch/status").then(function (r) { return r.json(); }).then(function (j) {
      var s = (j && j.job) || {};
      if (box) {
        box.innerHTML = '<div class="kb-au-est">已请求停止：跑完当前这篇就走（' +
          (s.done || 0) + " / " + (s.total || 0) + "）</div>";
      }
    });
  }

  function renderAudit(j) {
    var sum = $("kb-au-sum"), list = $("kb-au-list");
    var ps = j.proposals || [];
    var pend = ps.filter(function (p) { return p.status !== "pending"; }).length;
    sum.textContent = "本地判据 " + j.local_count + " 条" +
      (j.ai_enabled ? " · AI 判断已并入" : " · " + (j.ai_reason || "AI 未启用")) +
      (pend ? " · 已处置 " + pend + " 条" : "");
    if (!ps.length) {
      list.innerHTML = '<div class="kb-au-empty">没查出问题。这一篇的元数据、标题层级、' +
        "围栏、双链与附件都过得了本地判据。</div>";
      return;
    }
    list.innerHTML = ps.map(function (p) {
      var ai = (p.ai_terms && p.ai_terms.length)
        ? '<div class="kb-au-ai">AI 认为值得做：<b>' + esc(p.ai_terms.join("、")) + "</b>" +
          (p.ai_note ? "<span>" + esc(p.ai_note) + "</span>" : "") + "</div>"
        : (p.needs_ai ? '<div class="kb-au-ai muted">这条要 AI 判断，本次没跑（见上方原因）</div>' : "");
      return '<div class="kb-au-item" data-id="' + esc(p.id) + '" data-title="' + esc(p.title) +
        '" data-sug="' + esc(p.suggestion) + '" data-status="' + esc(p.status || "pending") + '">' +
        '<div class="kb-au-h"><span class="kb-au-sev ' + esc(p.severity) + '">' +
        (SEV_TEXT[p.severity] || esc(p.severity)) + "</span><b>" + esc(p.title) + "</b>" +
        (p.status && p.status !== "pending" ? '<i class="kb-au-state">' +
          (p.status === "adopted" ? "已采纳" : "已忽略") + "</i>" : "") + "</div>" +
        '<div class="kb-au-ev">' + esc(p.evidence) + "</div>" +
        '<div class="kb-au-sg">' + esc(p.suggestion) + "</div>" + ai +
        '<div class="kb-au-acts">' +
        '<button type="button" class="kb-ai-mini" data-act="adopt">记进批注</button>' +
        '<button type="button" class="kb-ai-mini ghost" data-act="dismiss">' +
        (p.status === "dismissed" ? "已忽略" : "忽略") + "</button>" +
        (p.status && p.status !== "pending"
          ? '<button type="button" class="kb-ai-mini ghost" data-act="pending">恢复待处理</button>'
          : "") + "</div></div>";
    }).join("");
  }

  var AUDIT_STATUS = { adopt: "adopted", dismiss: "dismissed", pending: "pending" };

  function auditAction(id, title, sug, act, btn, scope) {
    var d = doc();
    var status = AUDIT_STATUS[act];
    if (!status) return;
    // 域级待办没有"这一篇"可写批注，所以它只接受忽略 / 恢复两种处置
    var path = scope === "domain" ? "@domain:" + (d && d.domain ? d.domain : "") : d.rel;
    if (scope === "domain" && act === "adopt") { toast("域待办只能忽略或恢复：补哪一篇自己动手"); return; }
    var send = function () {
      return post("/api/ai/audit/status", { path: path, id: id, status: status })
        .then(function (j) {
          if (!j || j.ok !== true) {
            toast("状态没记住：" + ((j && j.error) || "未知错误"));
            return;
          }
          var item = btn.closest(".kb-au-item");
          if (item) item.setAttribute("data-status", status);
          // 三种处置都要重扫一次：汇总条上的"已处置 N 条"与「恢复待处理」按钮的显隐
          // 全靠服务端回的状态，客户端自己拼容易和派生库走岔。
          audit();
        });
    };
    if (act !== "adopt") { send(); return; }
    var text = "查漏｜" + title + "：" + sug;
    post("/api/note", { path: d.rel, text: text }).then(function (r) {
      if (!r || !r.ok) { toast("写批注失败：" + ((r && r.error) || "未知错误")); return; }
      send();
    }).catch(function (e) { toast("写批注失败：" + e.message); });
  }

  window.KBAI = {
    state: state,
    /** app.js 在渲染完正文后调用（SPA 式换文档时重置一次） */
    onDoc: function () { var d = doc(); resetFor(d && d.rel); },
    openFor: function (sel, mode) {
      state.selection = String(sel || "");
      state.mode = mode || (state.selection.length > 80 ? "passage" : "term");
      loadCfg().then(function () { openCard(); });
    },
    ask: ask,
    preview: preview,
    rail: loadRail,
    /** crumb 上的「查漏」按钮 —— 由 app.js::renderCrumb 每次现拼，点了才判本模块在不在 */
    audit: audit,
    /** 批量：估算条上的两个按钮走这里（探针也走这里，不靠猜 DOM） */
    batchEstimate: batchEstimate,
    batchStart: batchStart
  };

  // 首屏：app.js 渲染正文是异步的，这里等一次 DOC 出现再挂 rail
  loadCfg().then(function () {
    var tries = 0;
    var tick = setInterval(function () {
      var d = doc();
      if (d && d.rel) { clearInterval(tick); resetFor(d.rel); }
      else if (++tries > 40) clearInterval(tick);   // 4s 还没正文就别挂了（多半不是文档页）
    }, 100);
  });
})();
