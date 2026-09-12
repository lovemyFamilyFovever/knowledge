/* 知库 · Home 页面交互（T2 产出 · 只服务 home.html）
   依赖：T0 motion.js（window.Motion）+ vendor GSAP/ScrollTrigger。
   本页仅补两件 motion.js 不覆盖的事：
   1) hero mascot 鼠标视差（spec §5.1：data-depth 分层，reduced-motion 关）
   2) Motion.refresh() 兜底（本页 DOM 全部服务端渲染，正常无需；防御性调用一次）
   其余动效全部声明式：data-reveal / data-counter / data-magnetic / data-line-mask。 */
(function () {
  "use strict";

  /* =================================================================
     需求3：首页「今日学习」widget
     数据：GET /api/learn/today?domain=baike（今日一张 + 统计）
           GET /api/learn/mastery?scope=sub&domain=baike（按子域掌握度）
     全部渲染真实数字；接口不可用时给出人话提示，绝不写死占位数字。
     ================================================================= */
  (function renderTodayWidget() {
    var host = document.getElementById("kb-today");
    if (!host || !window.KB || !window.KB.api) return;
    var U = window.KB.util, API = window.KB.api;

    host.innerHTML =
      '<div class="kb-today-h">' + U.icon("i-clock-heartbeat", 14) + "<b>今日学习</b>" +
      '<span class="kb-today-date" id="kb-today-date"></span></div>' +
      '<div class="kb-today-grid">' +
      '  <div class="kb-today-card">' +
      '    <div class="kb-today-lab">今日术语</div>' +
      '    <div class="kb-today-term" id="kb-today-term">载入中…</div>' +
      '    <div class="kb-today-sub" id="kb-today-tip"></div>' +
      '    <div class="kb-today-def" id="kb-today-def"></div>' +
      '    <div class="kb-today-acts">' +
      '      <button type="button" class="kb-btn primary" id="kb-today-show">' + U.icon("i-eye", 13) + "显示定义</button>" +
      '      <a class="kb-btn" id="kb-today-doc" href="/review">' + U.icon("i-external-link", 13) + "跳转原文</a>" +
      "    </div>" +
      "  </div>" +
      '  <div class="kb-today-side">' +
      '    <div class="kb-today-stats" id="kb-today-stats"></div>' +
      '    <div class="kb-mastery" id="kb-mastery-bars"></div>' +
      '    <div class="kb-today-cta">' +
      '      <a class="kb-btn primary" href="/review">' + U.icon("i-progress-ring", 13) + "开始复习</a>" +
      '      <a class="kb-btn" href="/quiz">' + U.icon("i-interview", 13) + "去刷题</a>" +
      "    </div>" +
      "  </div>" +
      "</div>";

    var termEl = document.getElementById("kb-today-term");
    var tipEl = document.getElementById("kb-today-tip");
    var defEl = document.getElementById("kb-today-def");
    var showBtn = document.getElementById("kb-today-show");
    var docA = document.getElementById("kb-today-doc");
    var statsEl = document.getElementById("kb-today-stats");
    var barsEl = document.getElementById("kb-mastery-bars");
    var dateEl = document.getElementById("kb-today-date");
    var defText = "";

    if (showBtn) showBtn.addEventListener("click", function () {
      if (!defEl) return;
      var on = defEl.classList.toggle("show");
      showBtn.innerHTML = on ? U.icon("i-eye-off", 13) + "收起定义" : U.icon("i-eye", 13) + "显示定义";
    });

    API.today({ domain: "baike" }).then(function (j) {
      var c = j.card || {};
      var st = j.stats || {};
      if (dateEl) dateEl.textContent = j.date || "";
      if (termEl) termEl.textContent = c.term || "（暂无卡片）";
      if (tipEl) tipEl.textContent = j.tip || (c.sub_label ? c.sub_label + " · " + (c.kind || "") : "");
      defText = String(c.back || c.front || "").trim() || "这张卡还没有摘录内容，点「跳转原文」看完整文档。";
      if (defEl) defEl.textContent = defText;
      if (docA && c.url) { docA.href = c.url; docA.target = "_blank"; docA.rel = "noopener"; }

      var nums = [["待复习", st.due_n], ["连续天数", st.streak_days], ["掌握度", st.mastered_pct + "%"]];
      if (statsEl) {
        statsEl.innerHTML = nums.map(function (n) {
          return '<div class="kb-today-stat"><b>' + U.esc(String(n[1] == null ? "—" : n[1])) +
            "</b><span>" + U.esc(n[0]) + "</span></div>";
        }).join("");
      }
    }).catch(function (e) {
      if (dateEl) dateEl.textContent = "";
      if (termEl) termEl.textContent = "还没准备好";
      if (tipEl) tipEl.textContent = window.KB.api.msg(e) + "（可在命令面板里执行一次抽卡同步）";
      if (statsEl) statsEl.innerHTML = "";
      if (showBtn) showBtn.disabled = true;
    });

    API.mastery({ scope: "sub", domain: "baike" }).then(function (j) {
      var items = (j.items || []).slice().sort(function (a, b) { return (b.total || 0) - (a.total || 0); }).slice(0, 6);
      if (!items.length) { if (barsEl) barsEl.innerHTML = ""; return; }
      if (barsEl) {
        barsEl.innerHTML = items.map(function (it) {
          var pct = Math.max(0, Math.min(100, Number(it.pct) || 0));
          return '<div class="kb-mastery-row" style="--dh:' + U.esc(String(it.hue == null ? 150 : it.hue)) + '">' +
            '<span class="kb-ml" title="' + U.esc(it.label || it.id) + '">' + U.esc(it.label || it.id) + "</span>" +
            '<span class="kb-bar"><i style="width:' + pct + '%"></i></span>' +
            '<span class="kb-mv">' + pct + "%</span></div>";
        }).join("");
      }
    }).catch(function () { if (barsEl) barsEl.innerHTML = ""; });
  })();

  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced) return;

  var hero = document.querySelector("[data-parallax]");
  if (hero && window.gsap && !hero.dataset.parallaxBound) {
    hero.dataset.parallaxBound = "1";
    var layers = hero.querySelectorAll(".parallax-layer[data-depth]");
    /* 每层一个 quickTo，指针移动时按 depth 比例偏移；离开时归零 */
    var movers = [];
    Array.prototype.forEach.call(layers, function (el) {
      movers.push({
        depth: parseFloat(el.dataset.depth) || 0,
        x: window.gsap.quickTo(el, "x", { duration: 0.6, ease: "power3.out" }),
        y: window.gsap.quickTo(el, "y", { duration: 0.6, ease: "power3.out" })
      });
    });
    if (movers.length && window.matchMedia("(pointer: fine)").matches) {
      hero.addEventListener("mousemove", function (e) {
        var r = hero.getBoundingClientRect();
        var nx = (e.clientX - (r.left + r.width / 2)) / r.width;  /* -0.5 ~ 0.5 */
        var ny = (e.clientY - (r.top + r.height / 2)) / r.height;
        for (var i = 0; i < movers.length; i++) {
          movers[i].x(nx * 46 * movers[i].depth);
          movers[i].y(ny * 30 * movers[i].depth);
        }
      }, { passive: true });
      hero.addEventListener("mouseleave", function () {
        for (var i = 0; i < movers.length; i++) { movers[i].x(0); movers[i].y(0); }
      });
    }
  }

  /* 防御性刷新：motion.js 的 MutationObserver 已覆盖，这里补一次确保 ScrollTrigger 计算完成 */
  if (window.Motion && typeof window.Motion.refresh === "function") {
    if (document.readyState === "complete") window.Motion.refresh();
    else window.addEventListener("load", function () { window.Motion.refresh(); });
  }
})();
