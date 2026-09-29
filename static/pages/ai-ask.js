/* =====================================================================
   知库 · pages/ai-ask.js —— 选词问 AI（轮次 53 起是极简版）
   只在文档页（workbench）加载。暴露 window.KBAI，其余全在闭包内。

   用户 2026-09-29 定的形态：**选中文字 → 一句解释 → 三个动作**，到此为止。
   所以这里没有档位（词/这段/整篇）、没有"本次将发送 N 字"、没有追问框、
   没有置信与引用、没有侧栏「本篇问过的」—— 那些都在轮次 53 被要求删掉，
   旧形状见 git 历史（切片 2 / 3 / 4 / 5 那几轮）。

   与后端的契约（app/routes_ai.py::api_ai_explain + app/ai_qa.py）：
     · 前端只交 path + selection。服务端**连正文都不读**：path 只用来过域闸门。
     · 域级出站闸门在后端：career / interview / 标了 "ai": false 的域一律 403。
       前端按 /api/ai/config 的 egress_blocked_domains 提前不出现按钮 —— 那只是体验，
       不是防护（防护是那个 403，tests/test_ai_qa.py E 组锁着）。
     · 三个动作里两个会写盘，且都不碰正文：批注 → sidecar `.notes.md`（/api/note），
       新术语 → 走既有 /api/save（不变量 9 ②：AI 的建议永不自动改正文）。
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
    last: null,         // 最近一次成功响应（三个动作要用）
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
      '<div class="kb-ai-answer" id="kb-ai-answer">问 AI 中…</div>' +
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

  /* ---------------------------------------------------------------- 选区 */
  function currentSelection() {
    var s = window.getSelection && window.getSelection();
    if (!s || s.isCollapsed) return null;
    var text = String(s.toString() || "").replace(/\s+/g, " ").trim();
    if (text.length < 2) return null;
    var host = bodyEl();
    if (!host) return null;
    var range = s.rangeCount ? s.getRangeAt(0) : null;
    // 判据就一条：选区必须落在正文容器里。卡片/浮层挂在 body 上，不在 .a-body 内，
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
      chip.textContent = "问 AI";
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
  function openCard() {
    var card = ensureCard();
    card.hidden = false;
    positionCard();
    $("kb-ai-title").textContent = state.selection.length > 24
      ? state.selection.slice(0, 24) + "…" : state.selection;
    $("kb-ai-draft").hidden = true;
    ask();                       // 点开就问：极简版没有"先预览 N 字再决定"那一步
  }

  function positionCard() {
    var card = $("kb-ai-card"), chip = $("kb-ai-chip");
    if (!card || card.hidden) return;
    var cw = 380, chh = Math.min(card.offsetHeight || 240, window.innerHeight - 24);
    var left = Math.max(12, Math.min(window.innerWidth - cw - 12,
                                     (chip && !chip.hidden ? chip.offsetLeft : 200)));
    var top = (chip && !chip.hidden ? chip.offsetTop + 30 : 120);
    if (top + chh > window.innerHeight - 12) top = Math.max(12, window.innerHeight - chh - 12);
    card.style.left = left + "px";
    card.style.top = top + "px";
  }

  function setBusy(on) {
    state.busy = !!on;
    ["kb-ai-note", "kb-ai-term", "kb-ai-copy"].forEach(function (id) {
      var el = $(id);
      if (el) el.disabled = !!on;
    });
  }

  function ask() {
    if (state.busy) return;
    var ans = $("kb-ai-answer");
    setBusy(true);
    ans.textContent = "问 AI 中…";
    post("/api/ai/explain", { path: state.path, selection: state.selection }).then(function (j) {
      setBusy(false);
      render(j);
    }).catch(function (e) {
      setBusy(false);
      state.last = null;
      ans.textContent = "请求失败：" + ((e && e.message) || e);
    });
  }

  function render(j) {
    var ans = $("kb-ai-answer");
    if (!j || j.ok !== true) {
      state.last = null;
      // 后端的 error 已经把"为什么 + 去哪修"讲清了（未配置时会写"设置 → AI 页签"），
      // 这里只补它没覆盖的那一种：403 的 error 里只有域名，得说明是谁定的规矩。
      ans.textContent = "没问出来：" + ((j && (j.error || j.code)) || "未知错误") +
        (j && j.code === "domain_blocked" ? " —— 这是分类学里定的不出站规矩，不是故障。" : "");
      return;
    }
    state.last = j;
    ans.innerHTML = mdLite(j.answer || "");
    positionCard();              // 答案长短不定，落位要跟着重算一次
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

  /* ---------------------------------------------------------------- 三个动作 */
  function noteIt() {
    var j = state.last;
    if (!j || !j.answer) { toast("还没有可落盘的答案"); return; }
    var oneLine = String(j.answer).replace(/\s*\n\s*/g, " ").trim();
    var text = "AI 问「" + state.selection.slice(0, 40) + "」：" + oneLine +
      "（" + (j.cached ? "缓存" : j.model || "AI") + "）";
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
    var first = String(j.answer).replace(/\s*\n\s*$/, "").split(/\n/)[0];
    $("kb-ai-dpath").value = base + "/" + slug(state.selection) + ".md";
    $("kb-ai-dtext").value = "---\ntitle: \"" + state.selection.replace(/"/g, "'") +
      "\"\ntags: [AI生成待核]\n---\n\n# " + state.selection +
      "\n\n## 定义\n\n> 💡 一句话定义：" + first + "\n\n" +
      String(j.answer) + "\n\n## 出处\n\n- 本篇：" + (d.rel || "") + "\n\n" +
      "> ⚠️ 本词条由 AI 生成，未人工核对。\n";
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

  function wireCard() {
    $("kb-ai-x").addEventListener("click", function () { $("kb-ai-card").hidden = true; });
    $("kb-ai-note").addEventListener("click", noteIt);
    $("kb-ai-term").addEventListener("click", openDraft);
    $("kb-ai-copy").addEventListener("click", copyIt);
    $("kb-ai-dsave").addEventListener("click", saveDraft);
    $("kb-ai-dcancel").addEventListener("click", function () { $("kb-ai-draft").hidden = true; });
  }

  /* ---------------------------------------------------------------- 启动 */
  function resetFor(path) {
    state.path = path || "";
    state.last = null;
    var chip = $("kb-ai-chip"), card = $("kb-ai-card");
    if (chip) chip.hidden = true;
    if (card) card.hidden = true;
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

  window.KBAI = {
    state: state,
    /** app.js 在渲染完正文后调用（SPA 式换文档时重置一次） */
    onDoc: function () { var d = doc(); resetFor(d && d.rel); },
    /** 外部/测试入口：给定选区直接开卡片（openCard 里自己发问，不再分档） */
    openFor: function (sel) {
      state.selection = String(sel || "");
      loadCfg().then(function () { openCard(); });
    },
    ask: ask
  };

  // 首屏：app.js 渲染正文是异步的，这里等一次 DOC 出现再挂
  loadCfg().then(function () {
    var tries = 0;
    var tick = setInterval(function () {
      var d = doc();
      if (d && d.rel) { clearInterval(tick); resetFor(d.rel); }
      else if (++tries > 40) clearInterval(tick);   // 4s 还没正文就别挂了（多半不是文档页）
    }, 100);
  });
})();
