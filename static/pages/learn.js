/* =====================================================================
   知库 · learn.js —— 复习 / 刷题页（需求1 闪卡 / 需求2 刷题 / 需求3 侧栏掌握度）
   review.html 与 quiz.html 共用；页面差异全部由 root.dataset.kind 决定：
     review → 百科术语卡（4 档评分 重来/困难/良好/简单 = q 0/3/4/5）
     quiz   → 面试卡（2 档评分 不会/会 = q 0/4，按规范不进 q=5）
   依赖 kb-core.js（window.KB.api / KB.util / KB.keys），全局作用域直挂。
   ===================================================================== */
(function () {
  "use strict";
  var KB = window.KB;
  if (!KB || !KB.util || !KB.api) return;
  var U = KB.util, API = KB.api;

  var root = document.getElementById("kb-learn");
  if (!root) return;

  var IS_QUIZ = root.dataset.kind === "quiz";
  var MODE = IS_QUIZ ? "quiz" : "review";

  /* ---------------- 配置（评分档位写死，勿改枚举值） ---------------- */
  var CONF = {
    review: {
      label: "术语卡",
      due: { domain: "baike", limit: 20, include_new: "true", new_ratio: 0.3 },
      grades: [
        { q: 0, text: "重来", key: "1" },
        { q: 3, text: "困难", key: "2" },
        { q: 4, text: "良好", key: "3" },
        { q: 5, text: "简单", key: "4" }
      ],
      doneTitle: "今日已复习完",
      doneDesc: "这批到期的卡已经过完 —— 想继续就刷两道面试题，或去术语百科顺一条串学路径。",
      doneHref: "/quiz", doneText: "去刷题"
    },
    quiz: {
      label: "面试题",
      due: { kind: "interview_qa", limit: 20, include_new: "true", new_ratio: 0.3 },
      grades: [
        { q: 0, text: "不会", key: "1" },
        { q: 4, text: "会", key: "2" }
      ],
      doneTitle: "这批题刷完了",
      doneDesc: "面试卡已经过完一轮 —— 回术语卡把不熟的定义补上，或去总览看看今日进度。",
      doneHref: "/review", doneText: "去复习术语卡"
    }
  };
  var C = CONF[MODE];

  var KIND_LABEL = { baike_def: "定义卡", baike_trap: "误区卡", interview_qa: "面试题" };
  var RING_LEN = 276.46; // 2πr, r=44

  /* ---------------- DOM ---------------- */
  var el = {
    sub: U.$("#kb-learn-sub"),
    stage: U.$("#kb-stage"),
    card: U.$("#kb-card"),
    kicker: U.$("#kb-card-kicker"),
    term: U.$("#kb-card-term"),
    front: U.$("#kb-card-front"),
    backWrap: U.$("#kb-card-back-wrap"),
    back: U.$("#kb-card-back"),
    hint: U.$("#kb-card-hint"),
    hintT: U.$("#kb-card-hint-t"),
    src: U.$("#kb-card-src"),
    tags: U.$("#kb-card-tags"),
    cta: U.$("#kb-learn-cta"),
    grades: U.$("#kb-grades"),
    foot: U.$("#kb-learn-foot"),
    ringFg: U.$("#kb-ring-fg"),
    ringN: U.$("#kb-ring-n"),
    ringL: U.$("#kb-ring-l"),
    stats: U.$("#kb-side-stats"),
    filters: U.$("#kb-sub-filters")
  };

  /* ---------------- 状态 ---------------- */
  var S = {
    queue: [], idx: 0, cur: null, revealed: false,
    graded: {}, busy: false, fetching: false,
    sub: "", domain: "", subs: [],
    stats: { due_n: 0, new_n: 0, total_n: 0 },
    doneN: 0, startedAt: 0, loaded: false
  };

  function icon(n, s) { return U.icon(n, s); }

  /* ---------------- 队列 ---------------- */
  function loadQueue() {
    if (S.fetching) return Promise.resolve(null);
    S.fetching = true;
    var p = {};
    Object.keys(C.due).forEach(function (k) { p[k] = C.due[k]; });
    if (S.sub) p.sub = S.sub;
    return API.due(p).then(function (j) {
      var seen = {};
      S.queue.forEach(function (c) { seen[c.card_id] = 1; });
      (j.cards || []).forEach(function (c) { if (!seen[c.card_id]) S.queue.push(c); });
      S.stats.due_n = j.due_n || 0;
      S.stats.new_n = j.new_n || 0;
      S.stats.total_n = j.total_n || 0;
      if (!S.domain && S.queue.length) S.domain = S.queue[0].domain || "";
      return j;
    }).catch(function (e) {
      U.toast(API.msg(e));
      return null;
    }).then(function (j) { S.fetching = false; return j; });
  }

  /* ---------------- 渲染 ---------------- */
  function anchorHash(anchor) {
    var t = String(anchor || "").replace(/^#+\s*/, "").trim();
    return t ? "#" + encodeURIComponent(t.replace(/\s+/g, "-")) : "";
  }

  function renderTags(card) {
    var out = [];
    if (card.sub_label) out.push('<span class="kb-tag">' + U.esc(card.sub_label) + "</span>");
    (card.tags || []).slice(0, 5).forEach(function (t) { out.push('<span class="kb-tag mute">' + U.esc(t) + "</span>"); });
    if (card.state && card.state.interval) out.push('<span class="kb-tag mute">间隔 ' + card.state.interval + " 天</span>");
    if (card.state && card.state.mastered) out.push('<span class="kb-tag">已掌握</span>');
    el.tags.innerHTML = out.join("");
  }

  function renderGrades() {
    el.grades.hidden = false;
    el.grades.className = "kb-grades" + (C.grades.length === 2 ? " two" : "");
    el.grades.innerHTML = C.grades.map(function (g) {
      return '<button type="button" class="kb-grade q' + g.q + '" data-q="' + g.q + '">' +
        '<span class="kb-k">' + g.key + "</span><span>" + U.esc(g.text) + "</span></button>";
    }).join("");
  }

  function renderCta() {
    var card = S.cur;
    if (!card) { el.cta.innerHTML = ""; return; }
    if (S.revealed) { el.cta.innerHTML = ""; return; }
    var noAnswer = Number(card.has_answer) === 0;
    if (noAnswer) {
      el.cta.innerHTML =
        '<a class="kb-btn primary" id="kb-open-src" target="_blank" rel="noopener" href="' + U.esc(card.url + anchorHash(card.anchor)) + '">' +
        icon("i-external-link", 13) + "跳转原文 ↗</a>" +
        '<button type="button" class="kb-btn ghost" id="kb-skip">跳过这张</button>' +
        '<span class="kb-cta-tip">原文没附答案 —— 看原文自己组织一遍，再按 1 / 2 记分</span>';
      return;
    }
    el.cta.innerHTML =
      '<button type="button" class="kb-btn primary" id="kb-reveal">' + icon("i-eye", 13) + "显示答案</button>" +
      '<span class="kb-cta-tip">或按 <b>Space</b> 翻面</span>';
  }

  function showCard() {
    var card = S.queue[S.idx];
    if (!card) { showDone(); return; }
    S.cur = card;
    S.revealed = false;
    S.startedAt = Date.now();

    el.card.hidden = false;
    el.kicker.textContent = (KIND_LABEL[card.kind] || C.label) + " · " + (card.sub_label || card.sub || "");
    el.term.textContent = card.term || "";
    el.front.textContent = card.front || "";
    el.back.textContent = card.back || (Number(card.has_answer) === 0 ? "（原文没附答案，点上方「跳转原文」看完整内容）" : "");
    el.backWrap.hidden = true;
    el.card.classList.remove("kb-flip-in");
    void el.card.offsetWidth;
    el.card.classList.add("kb-flip-in");

    if (card.hint) { el.hint.hidden = false; el.hintT.textContent = card.hint; }
    else el.hint.hidden = true;

    el.src.innerHTML = card.source_rel
      ? '<a href="' + U.esc(card.url) + '" target="_blank" rel="noopener">' + U.esc(card.source_rel) + "</a>" +
        (card.anchor ? " · " + U.esc(card.anchor) : "")
      : "";
    renderTags(card);
    renderGrades();
    el.grades.hidden = true;
    renderCta();
    renderFoot();
  }

  function renderFoot() {
    var left = Math.max(0, S.queue.length - S.idx);
    el.foot.innerHTML =
      '<span class="kb-sess">本轮已答 ' + S.doneN + " 张 · 队列还剩 " + left + " 张</span>" +
      '<span class="kb-next"><kbd>j</kbd> 跳过 · <kbd>Space</kbd> 翻面 · <kbd>?</kbd> 帮助</span>';
  }

  function reveal() {
    if (S.revealed || !S.cur) return;
    S.revealed = true;
    el.backWrap.hidden = false;
    el.backWrap.classList.add("kb-flip-shown");
    el.grades.hidden = false;
    renderCta();
  }

  function setGradesEnabled(on) {
    U.$$(".kb-grade", el.grades).forEach(function (b) { b.disabled = !on; });
  }

  function advance() {
    S.idx++;
    var remain = S.queue.length - S.idx;
    if (remain < 3) {
      loadQueue().then(function () { showCard(); });
    } else {
      showCard();
    }
  }

  function grade(q) {
    if (!S.cur || S.busy) return;
    var card = S.cur;
    var ms = Math.max(0, Date.now() - S.startedAt);
    S.busy = true;
    setGradesEnabled(false);
    API.review({ card_id: card.card_id, q: q, elapsed_ms: ms }).then(function (j) {
      S.graded[card.card_id] = true;
      S.doneN++;
      var days = j && j.next ? j.next.due_in_days : 0;
      U.toast(U.dueText(days));
      S.busy = false;
      refreshStats();
      advance();
    }).catch(function (e) {
      S.busy = false;
      setGradesEnabled(true);
      U.toast(API.msg(e));
    });
  }

  function skip(delta) {
    if (S.busy) return;
    if (delta > 0) {
      if (S.idx + 1 >= S.queue.length) { loadQueue().then(function () { if (S.idx + 1 < S.queue.length) { S.idx++; showCard(); } else showDone(); }); return; }
      S.idx++; showCard();
      if (S.queue.length - S.idx < 3) loadQueue();
      return;
    }
    // 回退：只回到本轮还没评过分的卡，避免重复计分
    for (var i = S.idx - 1; i >= 0; i--) {
      if (!S.graded[S.queue[i].card_id]) { S.idx = i; showCard(); return; }
    }
    U.toast("前面都是已经评过分的卡了");
  }

  function showDone() {
    el.card.hidden = true;
    el.cta.innerHTML = "";
    el.grades.hidden = true;
    el.foot.innerHTML = "";
    var first = !S.loaded && S.doneN === 0;
    el.stage.innerHTML =
      '<div class="kb-done">' +
      '  <div class="kb-done-t">' + U.esc(first ? "暂时没有可学的卡" : C.doneTitle) + "</div>" +
      '  <div class="kb-done-d">' + U.esc(first
        ? "这个筛选下没有到期也没未学的卡。换个子域，或先去总览触发一次抽卡同步。"
        : C.doneDesc) + "</div>" +
      '  <div class="kb-done-acts">' +
      '    <a class="kb-btn primary" href="' + C.doneHref + '">' + icon("i-progress-ring", 13) + U.esc(C.doneText) + "</a>" +
      '    <a class="kb-btn" href="/glossary">' + icon("i-sort-alpha", 13) + "逛术语百科</a>" +
      '    <a class="kb-btn ghost" href="/home">' + icon("i-folder-open", 13) + "回总览</a>" +
      "  </div>" +
      "</div>";
    el.sub.innerHTML = first
      ? '<span class="kb-warn">队列为空</span> · 到期 ' + S.stats.due_n + " · 未学 " + S.stats.new_n
      : "本轮完成 " + S.doneN + " 张 · " + '<span class="kb-ok">已全部过完</span>';
  }

  /* ---------------- 侧栏：进度环 / 统计 / 子域筛选 ---------------- */
  function setRing(pct, num, label) {
    var p = Math.max(0, Math.min(100, Math.round(pct)));
    if (el.ringFg) el.ringFg.setAttribute("stroke-dashoffset", String(RING_LEN * (1 - p / 100)));
    if (el.ringN) el.ringN.textContent = num == null ? p + "%" : String(num);
    if (el.ringL) el.ringL.textContent = label || "今日进度";
  }

  function renderStats(st) {
    var items = [
      ["待复习", st.due_n == null ? "—" : st.due_n],
      ["连续天数", st.streak_days == null ? "—" : st.streak_days],
      ["今日已答", st.done_today == null ? "—" : st.done_today],
      ["掌握度", st.mastered_pct == null ? "—" : st.mastered_pct + "%"]
    ];
    el.stats.innerHTML = items.map(function (it) {
      return "<div><b>" + U.esc(String(it[1])) + "</b><span>" + U.esc(it[0]) + "</span></div>";
    }).join("");
  }

  function refreshStats() {
    var dom = S.domain || (IS_QUIZ ? "interview" : "baike");
    API.today({ domain: dom }).then(function (j) {
      var st = j.stats || {};
      var total = (st.done_today || 0) + (st.due_n || 0);
      if (total > 0) setRing(100 * (st.done_today || 0) / total, Math.round(100 * (st.done_today || 0) / total) + "%", "今日进度");
      else setRing(st.mastered_pct || 0, (st.mastered_pct || 0) + "%", "总掌握度");
      renderStats(st);
      if (el.sub && S.cur) {
        el.sub.innerHTML = "到期 " + U.esc(st.due_n) + " 张 · 未学 " + U.esc(st.new_left) +
          " 张 · 连续 " + U.esc(st.streak_days) + " 天 · 掌握度 " + U.esc(st.mastered_pct) + "%";
      }
    }).catch(function () { /* 侧栏统计失败不打断做题 */ });

    API.mastery({ scope: "sub", domain: dom }).then(function (j) {
      S.subs = j.items || [];
      renderFilters();
    }).catch(function () { el.filters.innerHTML = '<span style="font-size:11.5px;color:var(--faint)">掌握度暂不可用</span>'; });
  }

  function renderFilters() {
    if (!S.subs.length) { el.filters.innerHTML = '<span style="font-size:11.5px;color:var(--faint)">暂无子域</span>'; return; }
    var html = '<button type="button" class="kb-sub-chip' + (S.sub ? "" : " on") + '" data-sub="">全部</button>';
    html += S.subs.map(function (s) {
      var id = String(s.sub || s.id || "");
      return '<button type="button" class="kb-sub-chip' + (S.sub === id ? " on" : "") + '" data-sub="' + U.esc(id) + '">' +
        U.esc(s.label || id) + " · " + U.esc(s.total) + "</button>";
    }).join("");
    el.filters.innerHTML = html;
  }

  /* ---------------- 事件 ---------------- */
  el.cta.addEventListener("click", function (e) {
    if (e.target.closest("#kb-reveal")) { reveal(); return; }
    if (e.target.closest("#kb-skip")) { skip(1); }
  });
  el.grades.addEventListener("click", function (e) {
    var b = e.target.closest(".kb-grade");
    if (b) grade(Number(b.dataset.q));
  });
  el.filters.addEventListener("click", function (e) {
    var b = e.target.closest(".kb-sub-chip");
    if (!b) return;
    S.sub = b.dataset.sub || "";
    S.queue = []; S.idx = 0; S.graded = {};
    renderFilters();
    el.sub.textContent = "正在载入…";
    loadQueue().then(function () { showCard(); refreshStats(); });
  });

  /* 键盘：注册到 KB.keys 的页面上下文（输入态由 KB.keys 统一放行，这里不会误劫持） */
  KB.keys.setContext(function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return false;
    if (e.key === " " || e.key === "Spacebar") { e.preventDefault(); if (S.revealed) advance(); else reveal(); return true; }
    if (e.key === "Enter") { if (!S.revealed) { reveal(); return true; } return false; }
    if (/^[1-4]$/.test(e.key)) {
      var g = C.grades.filter(function (x) { return x.key === e.key; })[0];
      if (g) { e.preventDefault(); if (!S.revealed) reveal(); grade(g.q); return true; }
    }
    if (e.key === "j") { e.preventDefault(); skip(1); return true; }
    if (e.key === "k") { e.preventDefault(); skip(-1); return true; }
    return false;
  });

  /* ---------------- 启动 ---------------- */
  el.sub.textContent = "正在载入…";
  loadQueue().then(function () {
    S.loaded = true;
    showCard();
    refreshStats();
  });
})();
