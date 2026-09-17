/* =====================================================================
   知库 · 治理驾驶舱（Story 5/6）
   依赖 base.html 公共契约：esc / toast / kbModal（app.js 全局）。
   职责：
     [1] 扫描：GET /api/governance/scan → 三桶渲染
     [2] 断链批量处置：转为纯文本 / 移除链接标记 —— 写回走 /api/save
         （不引入新写入路径），逐篇读原文→正则替换→提交，附结果摘要
     [3] 近义标签合并：/api/tag/merge 先 dry-run 看受影响文档，确认再 apply
     [4] 孤儿白名单：localStorage 本地豁免（不改语料，个人偏好级）
   设计纪律：所有处置动作两步确认（预览 → 执行），与 govern_tags.py
   的 dry-run 先行一致；批量处置前必须看到“影响哪些文件”。
   ===================================================================== */
(function () {
  "use strict";

  var $ = function (s, p) { return (p || document).querySelector(s); };
  var $$ = function (s, p) { return Array.prototype.slice.call((p || document).querySelectorAll(s)); };

  var DATA = null;                    // 最近一次扫描结果
  var LS_ORPHAN_WL = "kb-gov-orphan-whitelist";

  /* ---------- 孤儿白名单（本地偏好，不写语料） ---------- */
  function wlLoad() {
    try { return new Set(JSON.parse(localStorage.getItem(LS_ORPHAN_WL) || "[]")); }
    catch (e) { return new Set(); }
  }
  function wlSave(set) {
    try { localStorage.setItem(LS_ORPHAN_WL, JSON.stringify(Array.from(set))); } catch (e) {}
  }

  /* ---------- 扫描 ---------- */
  async function scan() {
    var btn = $("#gov-scan-btn");
    btn.disabled = true;
    var old = btn.innerHTML;
    btn.innerHTML = "扫描中…";
    try {
      var r = await fetch("/api/governance/scan");
      var d = await r.json();
      if (!r.ok || !d.ok) throw new Error(d.error || ("HTTP " + r.status));
      DATA = d;
      render();
      $("#gov-idle").hidden = true;
      $("#gov-result").hidden = false;
      $("#gov-summary").textContent =
        d.counts.dead_links + " 断链 · " + d.counts.orphans + " 孤儿 · " + d.counts.tag_pairs + " 标签对";
      toast("扫描完成：" + $("#gov-summary").textContent);
    } catch (e) {
      toast("扫描失败：" + e.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = old;
    }
  }

  /* ---------- 渲染 ---------- */
  function render() {
    if (!DATA) return;
    $("#cnt-dead").textContent = DATA.dead_links.length;
    $("#cnt-orphan").textContent = DATA.orphans.length;
    $("#cnt-tag").textContent = DATA.tag_pairs.length;
    renderDead();
    renderOrphans();
    renderTagPairs();
  }

  /* 桶一：断链（可批量勾选） */
  function renderDead() {
    var list = $("#list-dead_links");
    var items = DATA.dead_links || [];
    if (!items.length) {
      list.innerHTML = '<div class="gov-none">没有断链，双链很健康。</div>';
      return;
    }
    list.innerHTML = items.map(function (it, i) {
      return '<label class="gov-item">' +
        '<input type="checkbox" class="dead-ck" data-idx="' + i + '">' +
        '<span class="gov-item-main">' +
          '<span class="gov-raw">[[' + esc(it.raw) + ']]</span>' +
          (it.suggest ? '<span class="gov-sug">→ 建议改为 [[' + esc(it.suggest) + ']]</span>' : '') +
          '<span class="gov-where">' + esc(it.src_title) + '</span>' +
        '</span>' +
        '<a class="gov-open" href="' + docHref(it.src) + '" title="打开所在文档">打开</a>' +
      '</label>';
    }).join("");
    bindDeadChecks();
  }

  function bindDeadChecks() {
    var all = $("#dead-all");
    var cks = $$(".dead-ck");
    function sync() {
      var n = cks.filter(function (c) { return c.checked; }).length;
      $("#dead-toplain").disabled = n === 0;
      $("#dead-remove").disabled = n === 0;
      all.checked = n > 0 && n === cks.length;
    }
    all.onchange = function () { cks.forEach(function (c) { c.checked = all.checked; }); sync(); };
    cks.forEach(function (c) { c.onchange = sync; });
    sync();
    $("#dead-toplain").onclick = function () { batchDead("toplain"); };
    $("#dead-remove").onclick = function () { batchDead("remove"); };
  }

  function selectedDead() {
    return $$(".dead-ck").filter(function (c) { return c.checked; })
      .map(function (c) { return DATA.dead_links[parseInt(c.dataset.idx, 10)]; });
  }

  /* 断链批量处置：按 src 分组（同一文档只读一次、写一次），
     逐篇 dry-run 预览 → 确认 → 走 /api/save 写回。 */
  async function batchDead(mode) {
    var picked = selectedDead();
    if (!picked.length) return;
    var bySrc = {};
    picked.forEach(function (it) { (bySrc[it.src] = bySrc[it.src] || []).push(it.raw); });
    var srcs = Object.keys(bySrc);
    var label = mode === "toplain" ? "转为纯文本" : "移除链接标记";

    // 预览：读原文算出每篇的改动条目数，展示给用户确认
    var preview = [];
    for (var i = 0; i < srcs.length; i++) {
      try {
        var res = await fetch(rawHref(srcs[i]));
        if (!res.ok) continue;
        var text = toLF(await res.text()); // 归一 LF，避免回写时二次翻译成 \r\r\n
        var hits = bySrc[srcs[i]].filter(function (raw) {
          return linkRe(raw).test(text); // 含别名/锚点/嵌入变体，与 FTS 提取器同口径
        });
        if (hits.length) preview.push({ src: srcs[i], hits: hits, text: text });
      } catch (e) { /* 跳过读不到的文件 */ }
    }
    if (!preview.length) { toast("选中的断链在原文中未找到（可能已被修改）"); return; }

    var total = preview.reduce(function (a, p) { return a + p.hits.length; }, 0);
    var ok = await confirmModal(
      "批量" + label,
      "将处理 <b>" + total + "</b> 处断链，涉及 <b>" + preview.length + "</b> 篇文档：<br>" +
      preview.slice(0, 8).map(function (p) {
        return '<span class="mono">' + esc(p.src) + '</span>（' + p.hits.length + " 处）";
      }).join("<br>") +
      (preview.length > 8 ? "<br>…等 " + preview.length + " 篇" : "")
    );
    if (!ok) return;

    // 执行：逐篇替换写回
    var done = 0, failed = 0;
    for (var j = 0; j < preview.length; j++) {
      var p = preview[j];
      var newText = p.text;
      p.hits.forEach(function (raw) {
        if (mode === "toplain") {
          // 转纯文本：[[x]]→x，[[x|别名]]→别名，![[x]]→x（去掉嵌入标记）
          newText = newText.replace(linkRe(raw), function (_m, alias) {
            return alias != null ? alias : raw;
          });
        } else {
          newText = newText.replace(linkRe(raw), ""); // 移除链接标记（含别名/锚点尾巴）
        }
      });
      try {
        var w = await fetch("/api/save", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: p.src, content: newText }),
        });
        var wd = await w.json().catch(function () { return {}; });
        if (w.ok && wd.ok) done += p.hits.length; else failed += p.hits.length;
      } catch (e) { failed += p.hits.length; }
    }
    toast(label + "完成：成功 " + done + " 处" + (failed ? "，失败 " + failed + " 处" : ""));
    await scan(); // 刷新桶
  }

  /* 桶二：孤儿文档（白名单本地豁免，默认折叠只显示前 30） */
  var orphanExpanded = false;
  function renderOrphans() {
    var list = $("#list-orphans");
    var wl = wlLoad();
    var items = (DATA.orphans || []).filter(function (o) { return !wl.has(o.path); });
    if (!items.length) {
      list.innerHTML = '<div class="gov-none">没有孤儿文档' + (wl.size ? "（已豁免 " + wl.size + " 篇）" : "") + '。</div>';
      return;
    }
    var shown = orphanExpanded ? items : items.slice(0, 30);
    list.innerHTML = shown.map(function (o) {
      return '<div class="gov-item">' +
        '<span class="gov-item-main">' +
          '<span class="gov-title">' + esc(o.title) + '</span>' +
          '<span class="gov-where mono">' + esc(o.path) + '</span>' +
        '</span>' +
        '<a class="gov-open" href="' + docHref(o.path) + '">打开</a>' +
        '<button class="gov-wl" data-path="' + esc(o.path) + '" title="加入白名单，不再报警">豁免</button>' +
      '</div>';
    }).join("") +
    (items.length > 30 && !orphanExpanded
      ? '<div class="gov-more">还有 ' + (items.length - 30) + " 篇未显示（孤儿占全库比例较高时，建议先在正文里补双链，而非逐条豁免）</div>"
      : "");
    $$(".gov-wl", list).forEach(function (b) {
      b.onclick = function () {
        var s = wlLoad(); s.add(b.dataset.path); wlSave(s);
        renderOrphans();
        toast("已豁免，不再出现在孤儿列表（仅本地，不改语料）");
      };
    });
    $("#orphan-expand").hidden = items.length <= 30;
    $("#orphan-expand").textContent = orphanExpanded ? "收起" : "展开全部";
    $("#orphan-expand").onclick = function () { orphanExpanded = !orphanExpanded; renderOrphans(); };
  }

  /* 桶三：近义标签（dry-run 预览 → 确认合并） */
  function renderTagPairs() {
    var list = $("#list-tag_pairs");
    var items = DATA.tag_pairs || [];
    if (!items.length) {
      list.innerHTML = '<div class="gov-none">标签体系很干净，没有疑似重复。</div>';
      return;
    }
    list.innerHTML = items.map(function (t, i) {
      return '<div class="gov-item">' +
        '<span class="gov-item-main">' +
          '<span class="gov-pair"><span class="mono">' + esc(t.src) + '</span>' +
          '<span class="gov-arrow">→</span><span class="mono gov-dst">' + esc(t.dst) + "</span>" +
          '<span class="gov-score" title="可疑度：1.0 大小写差异 / 0.9 包含关系 / 0.6 编辑距离">' + t.score + "</span></span>" +
        '</span>' +
        '<button class="gov-merge" data-idx="' + i + '">合并</button>' +
      '</div>';
    }).join("");
    $$(".gov-merge", list).forEach(function (b) {
      b.onclick = function () { mergeTags(DATA.tag_pairs[parseInt(b.dataset.idx, 10)]); };
    });
  }

  async function mergeTags(pair) {
    // 第一步：dry-run，列出受影响文档（API 契约：docs + n_docs + skipped）
    var r = await fetch("/api/tag/merge", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ src: pair.src, dst: pair.dst, apply: false }),
    });
    var d = await r.json();
    if (!r.ok || !d.ok) { toast("预览失败：" + (d.error || r.status)); return; }
    var affected = d.docs || [];
    var n = d.n_docs != null ? d.n_docs : affected.length;
    if (!n) { toast("没有文档使用标签「" + pair.src + "」，无需合并"); return; }
    var ok = await confirmModal(
      "合并标签 " + pair.src + " → " + pair.dst,
      "将改动 <b>" + n + "</b> 篇文档的标签：" +
      affected.slice(0, 8).map(function (a) { return '<span class="mono">' + esc(a.path || "") + "</span>"; }).join("<br>") +
      (n > 8 ? "<br>…等 " + n + " 篇" : "") +
      ((d.skipped && d.skipped.length) ? '<br><br>⚠ 有 ' + d.skipped.length + " 篇无法安全改写（结构复杂），将被跳过" : "") +
      '<br><br>合并走行级手术，只改 tags 一行，其余字节原样。'
    );
    if (!ok) return;
    // 第二步：apply
    var r2 = await fetch("/api/tag/merge", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ src: pair.src, dst: pair.dst, apply: true }),
    });
    var d2 = await r2.json();
    if (!r2.ok || !d2.ok) { toast("合并失败：" + (d2.error || r2.status)); return; }
    toast("已合并「" + pair.src + "」→「" + pair.dst + "」，改动 " + (d2.n_docs != null ? d2.n_docs : (d2.docs || []).length) + " 篇");
    await scan();
  }

  /* ---------- 共用：两步确认弹层 ---------- */
  function confirmModal(title, bodyHtml) {
    return new Promise(function (resolve) {
      var ov = KB.overlay.open({
        html: '<div class="kbm" role="document">' +
          '<div class="kbm-title">' + esc(title) + '<span class="spacer" style="flex:1"></span>' +
          '<button class="iconbtn gov-x" title="关闭（Esc）" aria-label="关闭">×</button></div>' +
          '<div class="kbm-body">' + bodyHtml + "</div>" +
          '<div class="kbm-btns">' +
          '<button class="iconbtn gov-cancel">取消</button>' +
          '<button class="iconbtn primary gov-ok">确认执行</button>' +
          "</div></div>",
        onClose: function () { resolve(false); },
        initialFocus: function (root) { return root.querySelector(".gov-cancel"); },
      });
      var done = false;
      function fin(v) { if (done) return; done = true; resolve(v); ov.close("btn"); }
      ov.root.querySelector(".gov-cancel").onclick = function () { fin(false); };
      ov.root.querySelector(".gov-x").onclick = function () { fin(false); };
      ov.root.querySelector(".gov-ok").onclick = function () { fin(true); };
    });
  }

  /* 路由构造一律转调 KB.util（唯一实现在 kb-core.js，含 _root 补段 + 逐段 encode）。
     此前 governance 里自写 docHref = 第三份影子实现，正是 kb-core 注释警告的反模式。 */
  function docHref(rel) { return KB.util.docUrl(rel); }
  function rawHref(rel) { return KB.util.rawUrl(rel); }

  /* 处置写回前归一到 LF：/raw 读到的原文可能是 CRLF（语料实况），而 /api/save
     按平台翻译换行——直接回写会二次翻译成 \r\r\n 污染语料（Story 2 护栏同源约束）。 */
  function toLF(s) { return String(s == null ? "" : s).replace(/\r\n?/g, "\n"); }

  function escapeRe(s) { return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  /* 匹配一个 raw（链接目标，不含 [[ 与 ]]）的全部字面写法，与 app.js FTS 提取器同族：
     [[raw]] / [[raw#锚点]] / [[raw|别名]] / ![[raw|别名]] ……
     结尾强制 ]]，故更长按链的目标前缀（如 raw="AI" vs [[AIX]]）不会被误匹配。 */
  function linkRe(raw) {
    return new RegExp("!?\\[\\[" + escapeRe(raw) + "(?:#[^\\[\\]|]*)?(?:\\|([^\\[\\]]*))?\\]\\]", "g");
  }

  /* ---------- 桶切换 ---------- */
  function bindTabs() {
    $$(".gov-tab").forEach(function (t) {
      t.onclick = function () {
        $$(".gov-tab").forEach(function (x) {
          var on = x === t;
          x.classList.toggle("on", on);
          x.setAttribute("aria-selected", on ? "true" : "false");
        });
        $$(".gov-pane").forEach(function (p) {
          p.classList.toggle("on", p.id === "pane-" + t.dataset.bucket);
        });
      };
    });
  }

  function init() {
    var btn = $("#gov-scan-btn");
    if (!btn) return;
    btn.onclick = scan;
    bindTabs();
    // 进页不自动扫描：全库扫描有成本，与后端 docstring / 模板空态的约定一致，按钮是唯一触发点
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
