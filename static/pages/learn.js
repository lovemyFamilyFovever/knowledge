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
    note: null,                    // 「消息层」：抽题中 / 完成态 / 成绩单（见 stageNote）
    ringFg: U.$("#kb-ring-fg"),
    ringN: U.$("#kb-ring-n"),
    ringL: U.$("#kb-ring-l"),
    stats: U.$("#kb-side-stats"),
    filters: U.$("#kb-sub-filters")
  };

  /* ---------------- 状态 ---------------- */
  var S = {
    queue: [], idx: 0, cur: null, revealed: false, done: false,
    graded: {}, busy: false, fetching: false,
    sub: "", domain: "", subs: [],
    stats: { due_n: 0, new_n: 0, total_n: 0 },
    doneN: 0, startedAt: 0, loaded: false,
    mock: null, mockN: 10   /* 模拟面试：null=普通模式；{n,startedAt,answers[]} */
  };

  function icon(n, s) { return U.icon(n, s); }

  /* ---------------- 消息层（抽题中 / 完成态 / 成绩单） ----------------
     `#kb-stage` 里躺着的是**常驻**节点：卡片、CTA、评分区、底部条（模板 quiz.html /
     review.html 第 15~42 行）。旧实现写消息时用 `el.stage.innerHTML = ...`，等于把
     这四个常驻节点一次性炸掉 —— `el.card`/`el.cta`/`el.grades`/`el.foot` 立刻变成
     挂在脱离文档的孤儿节点上的引用，之后 showCard() 的所有写入都落在孤儿上：
     **点「随机抽题开考」后画面永远停在「随机抽题中…」**，答题卡再也不出现
     （2026-09-25 轮次 28 由行为回归抓到，台账 §6 第 35 行）。
     改成只切换一个独立的消息层：常驻节点从头到尾都在 DOM 里，显示/隐藏靠 hidden。 */
  function stageNote(html, extraClass) {
    var n = el.note;
    if (!n) {
      n = document.createElement("div");
      n.id = "kb-stage-note";
      n.className = "kb-done";
      el.stage.insertBefore(n, el.stage.firstChild);
      el.note = n;
    }
    n.className = "kb-done" + (extraClass ? " " + extraClass : "");
    n.innerHTML = html || "";
    n.hidden = !html;
    el.card.hidden = !!html;        // 有消息时把卡片收起来，反之露出来
    return n;
  }

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
    S.done = false;
    S.revealed = false;
    S.startedAt = Date.now();

    el.card.hidden = false;
    stageNote("");                 // 卡片上场 → 消息层清空（两者互斥，同一处管）
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
    if (S.mock) renderMockFoot(); else renderFoot();
  }

  function renderMockFoot() {
    var n = S.queue.length, i = S.idx + 1;
    var ok = S.mock ? S.mock.answers.filter(function (x) { return x.ok; }).length : 0;
    el.foot.innerHTML =
      '<span class="kb-sess">模拟面试 · 第 ' + i + " / " + n + " 题 · 目前答对 " + ok + "</span>" +
      '<span class="kb-next"><kbd>Space</kbd> 翻面 · <kbd>1</kbd> 不会 · <kbd>2</kbd> 会</span>';
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
    if (S.mock) {   /* 模拟面试：固定卷子，不补队列，答完出成绩单 */
      if (S.idx >= S.queue.length) { showMockReport(); return; }
      renderMockFoot();
      showCard();
      return;
    }
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
      if (S.mock) {   /* 模拟即复习：会/不会照常推进 SM-2，但不弹「N 天后再见」 */
        S.mock.answers.push({ card_id: card.card_id, sub: card.sub || "",
          sub_label: card.sub_label || "", q: q, ok: q >= 3 });
        S.busy = false;
        advance();
        return;
      }
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
    S.done = true;
    el.card.hidden = true;
    el.cta.innerHTML = "";
    el.grades.hidden = true;
    el.foot.innerHTML = "";
    // B9：旧判据 !S.loaded && doneN===0 恒为 false —— 启动路径先置 S.loaded 再进
    // showCard，全新用户零卡零复习会看到「今日已复习完」（文案撒谎）。没答过任何
    // 一张且队列本就为空 = 没卡可学；答过才算「这批过完」。
    var first = S.doneN === 0 && S.queue.length === 0;
    stageNote(
      '  <div class="kb-done-t">' + U.esc(first ? "暂时没有可学的卡" : C.doneTitle) + "</div>" +
      '  <div class="kb-done-d">' + U.esc(first
        ? "这个筛选下没有到期也没未学的卡。换个子域，或先去总览触发一次抽卡同步。"
        : C.doneDesc) + "</div>" +
      '  <div class="kb-done-acts">' +
      '    <a class="kb-btn primary" href="' + C.doneHref + '">' + icon("i-progress-ring", 13) + U.esc(C.doneText) + "</a>" +
      '    <a class="kb-btn" href="/glossary">' + icon("i-sort-alpha", 13) + "逛术语百科</a>" +
      '    <a class="kb-btn ghost" href="/home">' + icon("i-folder-open", 13) + "回总览</a>" +
      "  </div>");
    el.sub.innerHTML = first
      ? '<span class="kb-warn">队列为空</span> · 到期 ' + S.stats.due_n + " · 未学 " + S.stats.new_n
      : "本轮完成 " + S.doneN + " 张 · " + '<span class="kb-ok">已全部过完</span>';
  }

  /* ---------------- 模拟面试（quiz 页专属）：随机卷 + 计时 + 成绩单 ---------------- */
  function startMock(n) {
    S.mock = { n: n, startedAt: Date.now(), answers: [] };
    S.queue = []; S.idx = 0; S.graded = {}; S.doneN = 0; S.cur = null;
    el.sub.textContent = "模拟面试出卷中…";
    el.cta.innerHTML = ""; el.grades.hidden = true; el.foot.innerHTML = "";
    stageNote('<div class="kb-done-t">随机抽题中…</div>');
    fetch("/api/learn/mock?n=" + n).then(function (r) { return r.json(); }).then(function (j) {
      if (!j.ok || !(j.cards || []).length) {
        U.toast(j && j.detail ? j.detail : "出卷失败：面试题库为空");
        exitMock();
        return;
      }
      S.queue = j.cards;
      S.idx = 0;
      el.sub.textContent = "模拟面试 · " + S.queue.length + " 题 · 计时开始";
      showCard();
    }).catch(function () {
      U.toast("出卷失败：网络错误");
      exitMock();
    });
  }

  function exitMock() {
    S.mock = null;
    S.queue = []; S.idx = 0; S.graded = {}; S.doneN = 0; S.cur = null;
    el.sub.textContent = "正在载入…";
    loadQueue().then(function () { showCard(); refreshStats(); });
  }

  function showMockReport() {
    var a = S.mock.answers, total = a.length;
    var ok = a.filter(function (x) { return x.ok; }).length;
    var secs = Math.max(1, Math.round((Date.now() - S.mock.startedAt) / 1000));
    var mm = Math.floor(secs / 60), ss = ("0" + (secs % 60)).slice(-2);
    var bySub = {};
    a.forEach(function (x) {
      var k = x.sub_label || x.sub || "未分类";
      bySub[k] = bySub[k] || { ok: 0, n: 0 };
      bySub[k].n++;
      if (x.ok) bySub[k].ok++;
    });
    var rows = Object.keys(bySub).sort(function (x, y) { return bySub[y].n - bySub[x].n; }).map(function (k) {
      return '<div class="kb-rep-row"><span>' + U.esc(k) + "</span><b>" + bySub[k].ok + " / " + bySub[k].n + "</b></div>";
    }).join("");
    var pct = total ? Math.round(100 * ok / total) : 0;
    el.cta.innerHTML = ""; el.grades.hidden = true; el.foot.innerHTML = "";
    stageNote(
      '  <div class="kb-done-t">模拟面试 · 成绩单</div>' +
      '  <div class="kb-rep-score">' + ok + "<i> / " + total + "</i></div>" +
      '  <div class="kb-rep-meta">正确率 <b>' + pct + "%</b> · 用时 " + mm + ":" + ss +
      " · 本次作答已计入复习排期</div>" +
      (rows ? '<div class="kb-rep-subs">' + rows + "</div>" : "") +
      '  <div class="kb-done-acts">' +
      '    <button type="button" class="kb-btn primary" id="kb-mock-again">' + icon("i-clock-heartbeat", 13) + "再来一轮</button>" +
      '    <button type="button" class="kb-btn" id="kb-mock-exit">返回普通刷题</button>' +
      "  </div>", "kb-rep");
    el.sub.innerHTML = "模拟面试完成 · 答对 " + ok + " / " + total + " · 正确率 " + pct + "%";
  }

  function bindMockReport() {
    el.stage.addEventListener("click", function (e) {
      if (!S.mock || S.idx < S.queue.length) return;   /* 只在成绩单态响应 */
      if (e.target.closest("#kb-mock-again")) { startMock(S.mock.n); return; }
      if (e.target.closest("#kb-mock-exit")) { exitMock(); }
    });
  }

  function injectMockEntry() {
    if (!IS_QUIZ || !el.filters || !el.filters.parentElement) return;
    var box = document.createElement("div");
    box.className = "kb-side-box kb-mock-box";
    box.innerHTML =
      '<div class="kb-mock-t">' + icon("i-interview", 13) + "模拟面试</div>" +
      '<div class="kb-mock-choose">' +
      '  <button type="button" data-n="5">5 题</button>' +
      '  <button type="button" data-n="10" class="on">10 题</button>' +
      '  <button type="button" data-n="20">20 题</button>' +
      "</div>" +
      '<button type="button" class="kb-btn primary kb-mock-start" id="kb-mock-start">' + icon("i-clock-heartbeat", 13) + "随机抽题开考</button>" +
      '<div class="kb-mock-note">从全部面试题随机出卷，计时作答，交卷出成绩单；作答照常计入复习排期。</div>';
    el.filters.parentElement.insertBefore(box, el.filters.nextSibling);
    box.addEventListener("click", function (e) {
      var chip = e.target.closest(".kb-mock-choose button");
      if (chip) {
        S.mockN = Number(chip.dataset.n) || 10;
        U.$$(".kb-mock-choose button", box).forEach(function (b) { b.classList.toggle("on", b === chip); });
        return;
      }
      if (e.target.closest("#kb-mock-start")) startMock(S.mockN);
    });
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

  /* 统计刷新有**两个并发来源**：进页面时一次（loadQueue 之后）、每次记分后又一次。
     没有序号守卫时就是"谁的响应后到谁写 DOM"：记分最后一张卡后，副标题会在
     「本轮完成 1 张 · 已全部过完」和「到期 0 张 · 未学 0 张 …」之间随机定格 ——
     同一个动作两种结果（2026-09-24 P5 视觉矩阵的 review_graded 镜头靠 AE=637 的反复不稳定钓出来的，
     台账 §6 第 24 行）。修法：每次刷新领一个自增序号，回调发现自己已被更新的一次取代就放弃写。 */
  var statsSeq = 0;

  function refreshStats() {
    var seq = ++statsSeq;
    var stale = function () { return seq !== statsSeq; };
    var dom = S.domain || (IS_QUIZ ? "interview" : "baike");
    API.today({ domain: dom }).then(function (j) {
      if (stale()) return;
      var st = j.stats || {};
      var total = (st.done_today || 0) + (st.due_n || 0);
      if (total > 0) setRing(100 * (st.done_today || 0) / total, Math.round(100 * (st.done_today || 0) / total) + "%", "今日进度");
      else setRing(st.mastered_pct || 0, (st.mastered_pct || 0) + "%", "总掌握度");
      renderStats(st);
      // 副标题有两个写者：这里（队列口径）和 showDone()（本轮完成/队列为空）。
      // 记分最后一张卡后 advance() 会走 loadQueue→showDone，两个异步谁先落不定，
      // 所以**一旦进入 done 态，统计刷新就不许再改这一行**（P5 的 review_graded
      // 镜头实测：只加 seq 守卫仍反复 AE=637，补上这条才彻底稳定）。
      if (el.sub && S.cur && !S.done) {
        el.sub.innerHTML = "到期 " + U.esc(st.due_n) + " 张 · 未学 " + U.esc(st.new_left) +
          " 张 · 连续 " + U.esc(st.streak_days) + " 天 · 掌握度 " + U.esc(st.mastered_pct) + "%";
      }
    }).catch(function () { /* 侧栏统计失败不打断做题 */ });

    API.mastery({ scope: "sub", domain: dom }).then(function (j) {
      if (stale()) return;
      S.subs = j.items || [];
      renderFilters();
    }).catch(function () {
      if (stale()) return;
      el.filters.innerHTML = '<span style="font-size:11.5px;color:var(--faint)">掌握度暂不可用</span>';
    });
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
    if (S.mock) { U.toast("模拟面试进行中 —— 交卷后再切换子域"); return; }
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
  injectMockEntry();
  bindMockReport();
  el.sub.textContent = "正在载入…";
  loadQueue().then(function () {
    S.loaded = true;
    showCard();
    refreshStats();
  });

  /* 彻查 P5：挂一个最小可测面。tests/test_js_props.py 的"统计竞态"探针会
     临时替换 window.KB.api.today（learn.js 调用时才取属性，所以补丁生效）灌两个
     "慢的旧响应 / 快的新响应"，断言副标题取的是新的那次；再把状态摆成 done 态，
     断言统计刷新不许覆盖 showDone 写的那行。去掉 seq 守卫或 `!S.done` 判据，探针立刻变红。 */
  window.KBLEARN = {
    refreshStats: refreshStats,
    statsSeq: function () { return statsSeq; },
    setDone: function (v) { S.done = !!v; },
  };
})();
