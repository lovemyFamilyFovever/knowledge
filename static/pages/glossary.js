/* =====================================================================
   知库 · glossary.js —— 术语门户（需求8）+ 串学漫游（需求4）
   数据契约：GET /api/glossary → {total, buckets[], groups[], items_flat[]}
     group  = {sub, sub_label, hue, items[]}
     item   = {term, card_id, initial, sub, source_rel, anchor, url,
               mastered, is_new, due_ts, has_trap, def_brief}
   策略：全量只拉一次；之后的过滤 / 分桶 / 子域切换全部在前端完成，不重复请求。
   ===================================================================== */
(function () {
  "use strict";
  var KB = window.KB;
  if (!KB || !KB.util || !KB.api) return;
  var U = KB.util, API = KB.api;

  var root = document.getElementById("kb-glossary");
  if (!root) return;

  var el = {
    sub: U.$("#kb-gl-sub"),
    q: U.$("#kb-gl-q"),
    clear: U.$("#kb-gl-clear"),
    subs: U.$("#kb-gl-subs"),
    buckets: U.$("#kb-gl-buckets"),
    roam: U.$("#kb-roam"),
    body: U.$("#kb-gl-body")
  };

  var params = new URLSearchParams(location.search);
  var S = {
    flat: [], groups: [], buckets: {}, total: 0,
    q: params.get("q") || "",
    letter: params.get("letter") || "all",
    sub: params.get("sub") || "",
    openTerm: "",
    roam: params.get("roam") || "",
    ready: false
  };

  /* ---------------- 分桶：A–Z 或 # ---------------- */
  function bucketOf(term) {
    var h = String(term || "").charAt(0).toUpperCase();
    return (h && h >= "A" && h <= "Z" && /[A-Z]/.test(h)) ? h : "#";
  }
  var LETTERS = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

  /* ---------------- 渲染：首字母桶 ---------------- */
  function renderBuckets() {
    var counts = {};
    S.flat.forEach(function (it) {
      var b = bucketOf(it.term);
      counts[b] = (counts[b] || 0) + 1;
    });
    S.buckets = counts;
    var html = '<button type="button" class="kb-bucket' + (S.letter === "all" ? " on" : "") +
      '" data-letter="all" role="tab">全部<span class="kb-bn">' + S.total + "</span></button>";
    html += LETTERS.map(function (L) {
      var n = counts[L] || 0;
      return '<button type="button" class="kb-bucket' + (S.letter === L ? " on" : "") + (n ? "" : " zero") +
        '" data-letter="' + U.esc(L) + '" role="tab"' + (n ? "" : ' aria-disabled="true"') + ">" +
        U.esc(L) + '<span class="kb-bn">' + n + "</span></button>";
    }).join("");
    el.buckets.innerHTML = html;
  }

  /* ---------------- 渲染：子域切换 ---------------- */
  function renderSubs() {
    var html = '<button type="button" class="kb-gl-sub' + (S.sub ? "" : " on") + '" data-sub="">全部子域</button>';
    html += S.groups.map(function (g) {
      return '<button type="button" class="kb-gl-sub' + (S.sub === String(g.sub) ? " on" : "") +
        '" data-sub="' + U.esc(String(g.sub)) + '">' + U.esc(g.sub_label || g.sub) + " · " + (g.items || []).length + "</button>";
    }).join("");
    el.subs.innerHTML = html;
  }

  /* ---------------- 过滤 ---------------- */
  function visible() {
    var q = String(S.q || "").trim().toLowerCase();
    return S.flat.filter(function (it) {
      if (S.sub && String(it.sub) !== String(S.sub)) return false;
      if (S.letter && S.letter !== "all" && bucketOf(it.term) !== S.letter) return false;
      if (q && String(it.term).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
  }

  function dotClass(it) {
    if (it.mastered) return "mastered";
    if (!it.is_new) return "learning";
    return "new";
  }
  function dotTitle(it) {
    if (it.mastered) return "已掌握";
    if (!it.is_new) return "学习中";
    return "未学";
  }

  /* ---------------- 渲染：术语网格 ---------------- */
  function renderBody() {
    if (!S.ready) return;
    var items = visible();
    var bySub = {};
    items.forEach(function (it) { (bySub[it.sub] = bySub[it.sub] || []).push(it); });

    var html = "";
    S.groups.forEach(function (g) {
      var list = bySub[g.sub];
      if (!list || !list.length) return;
      var hue = Number(g.hue);
      html += '<section class="kb-gl-group" style="--dh:' + (isNaN(hue) ? 150 : hue) + '">' +
        '<div class="kb-gl-group-h"><span class="kb-gg-dot"></span>' + U.esc(g.sub_label || g.sub) +
        '<span class="kb-gg-n">' + list.length + " / " + (g.items || []).length + "</span></div>" +
        '<div class="kb-terms">' +
        list.map(function (it) {
          return '<button type="button" class="kb-term' + (S.openTerm === it.term ? " open" : "") +
            '" data-term="' + U.esc(it.term) + '" data-card="' + U.esc(it.card_id || "") + '">' +
            '<span class="kb-dotm ' + dotClass(it) + '" title="' + dotTitle(it) + '"></span>' +
            '<span class="kb-term-n">' + U.esc(it.term) + "</span>" +
            (it.has_trap ? '<span class="kb-trap" title="有对应的误区卡">误区</span>' : "") +
            "</button>";
        }).join("") +
        "</div></section>";
    });

    if (!items.length) {
      html = '<div class="kb-gl-empty">没有符合条件的术语。<br>当前筛选：<b>' +
        U.esc(S.sub || "全部子域") + "</b> · <b>" + U.esc(S.letter === "all" ? "全部首字母" : S.letter) + "</b>" +
        (S.q ? " · 关键词 <b>" + U.esc(S.q) + "</b>" : "") + "</div>";
    }
    el.body.innerHTML = html;
    if (S.openTerm) injectDetail();

    el.sub.innerHTML = "共 <b>" + S.total + "</b> 个术语 · 当前显示 <b>" + items.length + "</b> 个 · " +
      S.groups.length + " 个子域 · 数据只拉一次，过滤在本页完成";
  }

  /* ---------------- 内联展开详情 ---------------- */
  function findItem(term) {
    for (var i = 0; i < S.flat.length; i++) if (S.flat[i].term === term) return S.flat[i];
    return null;
  }

  function injectDetail() {
    var btn = el.body.querySelector('.kb-term[data-term="' + cssEscape(S.openTerm) + '"]');
    var it = findItem(S.openTerm);
    if (!btn || !it) return;
    var old = el.body.querySelector(".kb-term-detail");
    if (old) old.remove();
    var d = document.createElement("div");
    d.className = "kb-term-detail";
    d.setAttribute("data-for", it.term);
    var def = String(it.def_brief || "").trim() || "（这张卡还没有摘录定义 —— 点「跳转原文」看完整内容）";
    var meta = [it.mastered ? "已掌握" : (it.is_new ? "未学" : "学习中")];
    if (it.due_ts) {
      var days = Math.ceil((it.due_ts * 1000 - Date.now()) / 86400000);
      meta.push(days <= 0 ? "今天到期" : days + " 天后到期");
    }
    if (it.has_trap) meta.push("有误区卡");
    d.innerHTML =
      '<div class="kb-td-t">' + U.esc(it.term) + "</div>" +
      '<div class="kb-td-d">' + U.esc(def) + "</div>" +
      '<div class="kb-td-m">' + U.esc(it.source_rel || "") + (it.anchor ? " · " + U.esc(it.anchor) : "") +
      " · " + U.esc(meta.join(" · ")) + "</div>" +
      '<div class="kb-td-acts">' +
      '<button type="button" class="kb-act primary" data-act="review" data-card="' + U.esc(it.card_id || "") + '">' +
      U.icon("i-progress-ring", 12) + "加入复习</button>" +
      '<a class="kb-act" data-act="doc" href="' + U.esc(it.url || "#") + '" target="_blank" rel="noopener">' +
      U.icon("i-external-link", 12) + "跳转原文</a>" +
      '<a class="kb-act" data-act="roam" href="/glossary?roam=' + encodeURIComponent(it.term) + '">' +
      U.icon("i-backlink-graph", 12) + "串学</a>" +
      "</div>";
    btn.insertAdjacentElement("afterend", d);
  }

  function cssEscape(s) {
    return String(s).replace(/["\\]/g, "\\$&");
  }

  /* ---------------- 串学漫游（需求4） ---------------- */
  function renderRoamLoading(term) {
    el.roam.hidden = false;
    el.roam.innerHTML = '<div class="kb-roam-h">' + U.icon("i-backlink-graph", 13) +
      "串学路径 · 从「" + U.esc(term) + "」出发…</div>";
  }

  function loadRoam(term) {
    if (!term) { el.roam.hidden = true; el.roam.innerHTML = ""; return; }
    renderRoamLoading(term);
    API.roam({ from: term, n: 6 }).then(function (j) {
      var path = j.path || [];
      var dead = j.dead_ends || [];
      var html = '<div class="kb-roam-h">' + U.icon("i-backlink-graph", 13) +
        "串学路径 · 从「" + U.esc(j.start || term) + "」出发，沿 [[相关术语]] 走了 " + path.length + " 步" +
        '<span class="kb-roam-x" id="kb-roam-x" title="收起串学">' + U.icon("i-cancel-x", 12) + "</span></div>";

      if (!path.length) {
        html += '<div class="kb-roam-tip">没有找到以「' + U.esc(term) + '」为起点的卡片，换个术语试试。</div>';
      } else {
        html += '<div class="kb-roam-path">' + path.map(function (p, i) {
          return (i ? '<span class="kb-roam-sep">→</span>' : "") +
            '<button type="button" class="kb-roam-node' + (p.is_new ? " is-new" : "") +
            '" data-term="' + U.esc(p.term) + '" title="' + U.esc(p.is_new ? "还没学过" : "已学过") + '">' +
            U.esc(p.term) + '<span class="kb-rn-d">' + (p.depth == null ? "" : "d" + p.depth) + "</span></button>";
        }).join("") + "</div>";
      }
      if (dead.length) {
        html += '<div class="kb-roam-path" style="margin-top:8px">' +
          dead.map(function (t) {
            return '<span class="kb-roam-node dead" title="语料里还没有这张卡">' + U.esc(t) + " · 无卡片</span>";
          }).join("") + "</div>";
      }
      html += '<div class="kb-roam-tip">点任一节点就以它为新起点继续延伸；虚线 = 还没学过的卡。</div>';
      el.roam.innerHTML = html;
    }).catch(function (e) {
      el.roam.innerHTML = '<div class="kb-roam-h">' + U.icon("i-warning-triangle", 13) +
        "串学失败：" + U.esc(API.msg(e)) + "</div>";
    });
  }

  function setRoam(term, push) {
    S.roam = term || "";
    var url = "/glossary";
    var usp = new URLSearchParams();
    if (S.roam) usp.set("roam", S.roam);
    if (S.letter && S.letter !== "all") usp.set("letter", S.letter);
    if (S.sub) usp.set("sub", S.sub);
    var qs = usp.toString();
    if (push) history.pushState({ roam: S.roam }, "", qs ? url + "?" + qs : url);
    loadRoam(S.roam);
  }

  /* ---------------- 事件 ---------------- */
  el.buckets.addEventListener("click", function (e) {
    var b = e.target.closest(".kb-bucket");
    if (!b || b.classList.contains("zero")) return;
    S.letter = b.dataset.letter || "all";
    S.openTerm = "";
    renderBuckets();
    renderBody();
  });

  el.subs.addEventListener("click", function (e) {
    var b = e.target.closest(".kb-gl-sub");
    if (!b) return;
    S.sub = b.dataset.sub || "";
    S.openTerm = "";
    renderSubs();
    renderBody();
  });

  var onQ = U.debounce(function () { S.openTerm = ""; renderBody(); }, 120);
  el.q.addEventListener("input", function () { S.q = el.q.value; onQ(); });
  el.clear.addEventListener("click", function () {
    el.q.value = ""; S.q = ""; S.openTerm = ""; renderBody(); el.q.focus();
  });

  el.body.addEventListener("click", function (e) {
    var act = e.target.closest(".kb-act");
    if (act) {
      var kind = act.dataset.act;
      if (kind === "review") {
        var cid = act.dataset.card;
        if (!cid) { U.toast("这张卡没有 card_id，无法加入复习"); return; }
        API.review({ card_id: cid, q: 0, elapsed_ms: 0 }).then(function () {
          U.toast("已加入复习：稍后就会出现在今日队列里");
          var it0 = findItem(act.closest(".kb-term-detail").getAttribute("data-for"));
          if (it0) { it0.is_new = false; renderBody(); }
        }).catch(function (err) { U.toast(API.msg(err)); });
        e.preventDefault();
        return;
      }
      if (kind === "roam") {
        e.preventDefault();
        var t = act.closest(".kb-term-detail").getAttribute("data-for");
        setRoam(t, true);
        el.roam.scrollIntoView({ behavior: "smooth", block: "nearest" });
        return;
      }
      return; // doc：走 <a> 默认跳转
    }
    var cell = e.target.closest(".kb-term");
    if (!cell) return;
    var term = cell.dataset.term;
    S.openTerm = S.openTerm === term ? "" : term;
    U.$$(".kb-term", el.body).forEach(function (c) { c.classList.toggle("open", c.dataset.term === S.openTerm); });
    var old = el.body.querySelector(".kb-term-detail");
    if (old) old.remove();
    if (S.openTerm) injectDetail();
  });

  el.roam.addEventListener("click", function (e) {
    if (e.target.closest("#kb-roam-x")) { setRoam("", true); return; }
    var node = e.target.closest(".kb-roam-node");
    if (node && !node.classList.contains("dead")) setRoam(node.dataset.term, true);
  });

  window.addEventListener("popstate", function () {
    var p = new URLSearchParams(location.search);
    S.roam = p.get("roam") || "";
    loadRoam(S.roam);
  });

  /* 键盘：j/k 在术语网格里移动焦点，Enter 展开（输入框里不劫持，由 KB.keys 保证） */
  KB.keys.setContext(function (e) {
    if (document.activeElement !== document.body &&
        document.activeElement && document.activeElement.classList &&
        document.activeElement.classList.contains("kb-term")) {
      if (e.key === "Enter" || e.key === " ") return false; // 交给原生 click
    }
    if (e.key === "j" || e.key === "k") {
      var cells = U.$$(".kb-term", el.body);
      if (!cells.length) return false;
      var i = cells.indexOf(document.activeElement);
      var n = cells.length;
      var next = i < 0 ? 0 : (i + (e.key === "j" ? 1 : -1) + n) % n;
      cells[next].focus();
      if (cells[next].scrollIntoView) cells[next].scrollIntoView({ block: "nearest" });
      return true;
    }
    if (e.key === "/" && document.activeElement !== el.q) { el.q.focus(); return true; }
    return false;
  });

  /* ---------------- 启动：全量只拉一次 ---------------- */
  API.glossary({ domain: "baike" }).then(function (j) {
    S.total = j.total || 0;
    S.groups = j.groups || [];
    S.flat = j.items_flat || [];
    S.ready = true;
    if (S.q) el.q.value = S.q;
    renderBuckets();
    renderSubs();
    renderBody();
    if (S.roam) loadRoam(S.roam);
    if (S.letter && S.letter !== "all") {
      var b = el.buckets.querySelector('.kb-bucket[data-letter="' + cssEscape(S.letter) + '"]');
      if (b && b.scrollIntoView) b.scrollIntoView({ inline: "center", block: "nearest" });
    }
  }).catch(function (e) {
    el.body.innerHTML = '<div class="kb-gl-empty">术语索引载入失败：' + U.esc(API.msg(e)) +
      "<br>可以先运行一次抽卡同步（命令面板 → 或 POST /api/learn/sync）。</div>";
    el.sub.textContent = "载入失败";
  });
})();
