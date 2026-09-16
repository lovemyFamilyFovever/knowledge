/* 知库 stats.js · 月度统计页（问题13 重构）
   数据来源：仅模板内嵌的真实统计数据（#st-daily-data，来自 ReadingStore.monthly）。
   设计要点：
   1. 横轴按**日历**定位（1..当月天数），缺失日 0 高但保留刻度；
      不再用 plotW/len 那种「按数组下标均分」的畸形柱位。
   2. 只有真正有数据时才画图：无序列直接返回，不写 "NO SERIES"、不留空白图卡。
   3. 图表全部内联 SVG（零外链），配色只用已有 CSS 变量（--acc/--acc2/--edge）。
   4. 揭示动画兜底：任何 [data-reveal] 若被卡成隐形，超时后强制可见。
   依赖 T0：window.Motion（可选，缺失即静态呈现）。 */
(function () {
  "use strict";

  var SVGNS = "http://www.w3.org/2000/svg";
  var H = 240;                                   // svg 逻辑高度（与模板一致）
  var PAD = { l: 44, r: 18, t: 20, b: 34 };
  var reduced = !!(window.Motion && window.Motion.reduced);

  function el(tag, attrs) {
    var n = document.createElementNS(SVGNS, tag);
    if (attrs) for (var k in attrs) if (attrs[k] !== null && attrs[k] !== undefined) n.setAttribute(k, attrs[k]);
    return n;
  }
  function say(node, s) { node.textContent = s; return node; }
  function niceCeil(v) {
    if (!(v > 0)) return 1;
    var pow = Math.pow(10, Math.floor(Math.log(v) / Math.LN10));
    var f = v / pow;
    var n = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10;
    return n * pow;
  }
  function dayNum(s) {
    var m = /(\d{4})-(\d{2})-(\d{2})/.exec(String(s == null ? "" : s));
    if (m) return +m[3];
    var n = parseInt(s, 10);
    return isFinite(n) ? n : NaN;
  }

  /* ---------- 读原始序列 ---------- */
  var daily = (function () {
    var raw = document.getElementById("st-daily-data");
    try { return JSON.parse((raw && raw.textContent) || "[]") || []; } catch (e) { return []; }
  })();

  /* ---------- 月份信息（当月天数，来自模板 [data-ym]） ---------- */
  function monthInfo() {
    var host = document.querySelector("[data-ym]");
    var ym = host ? (host.getAttribute("data-ym") || "") : "";
    var m = /^(\d{4})-(\d{1,2})$/.exec(ym);
    if (m) return { y: +m[1], m: +m[2], days: new Date(+m[1], +m[2], 0).getDate() };
    return null;
  }

  /* 把（可能稀疏的）daily 序列铺成「当月每一天」的连续序列，下标即日 */
  function buildSeries() {
    var info = monthInfo();
    var maxDay = 0;
    daily.forEach(function (d) { var k = dayNum(d.day); if (isFinite(k) && k > maxDay) maxDay = k; });
    var N = (info && info.days) || maxDay || daily.length || 1;
    var rows = [];
    for (var i = 0; i < N; i++) rows.push({ day: i + 1, minutes: 0, docs: 0 });
    daily.forEach(function (d, i) {
      var k = dayNum(d.day);
      if (!isFinite(k) || k < 1 || k > N) k = i + 1;   // 无日期字段时退回下标
      var r = rows[k - 1];
      if (r) { r.minutes += (+d.minutes || 0); r.docs += (+d.docs || 0); }
    });
    return { N: N, rows: rows };
  }

  var SERIES = buildSeries();

  /* ---------- KPI 迷你 sparkline（无数据不画、不写占位） ---------- */
  function sparkline(container, values, stroke) {
    var max = Math.max.apply(null, values.concat([0]));
    if (values.length < 2 || !(max > 0)) return false;
    var w = 100, h = 24, pad = 3;
    var pts = values.map(function (v, i) {
      var x = i * w / (values.length - 1);
      var y = h - pad - (v / max) * (h - pad * 2);
      return [x.toFixed(1), y.toFixed(1)];
    });
    var svg = el("svg", { viewBox: "0 0 " + w + " " + h, preserveAspectRatio: "none" });
    var poly = pts.map(function (p) { return p.join(","); }).join(" ");
    svg.appendChild(el("polygon", { class: "spark-fill", fill: stroke, stroke: "none",
      points: "0," + h + " " + poly + " " + w + "," + h }));
    svg.appendChild(el("polyline", { fill: "none", stroke: stroke, "stroke-width": "1.6",
      "stroke-linecap": "round", "stroke-linejoin": "round", points: poly }));
    var last = pts[pts.length - 1];
    svg.appendChild(el("circle", { class: "spark-dot", fill: stroke, cx: last[0], cy: last[1] }));
    container.appendChild(svg);
    return true;
  }

  function initSparks() {
    var minutes = SERIES.rows.map(function (r) { return r.minutes; });
    var docs = SERIES.rows.map(function (r) { return r.docs; });
    var presence = SERIES.rows.map(function (r) { return r.minutes > 0 ? 1 : 0; });
    var map = { minutes: [minutes, "var(--c-acc)"], docs: [docs, "var(--c-info)"], presence: [presence, "var(--c-acc)"] };
    Array.prototype.forEach.call(document.querySelectorAll("[data-spark]"), function (c) {
      var cfg = map[c.getAttribute("data-spark")];
      c.textContent = "";
      if (!cfg) return;
      sparkline(c, cfg[0], cfg[1]);
    });
  }

  /* ---------- 每日柱状图：柱=阅读分钟（左轴），折线=打开文档数（右轴） ---------- */
  function drawDaily() {
    var svg = document.getElementById("stDailyChart");
    if (!svg) return false;
    var rows = SERIES.rows, N = SERIES.N;
    var sumMin = rows.reduce(function (s, r) { return s + r.minutes; }, 0);
    var sumDoc = rows.reduce(function (s, r) { return s + r.docs; }, 0);
    while (svg.firstChild) svg.removeChild(svg.firstChild);     // 幂等重绘
    if (!(sumMin > 0) && !(sumDoc > 0)) return false;           // 无数据 → 不渲染

    var W = Math.max(320, Math.round(svg.clientWidth || (svg.parentNode && svg.parentNode.clientWidth) || 900));
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("preserveAspectRatio", "none");

    var plotW = W - PAD.l - PAD.r;
    var base = H - PAD.b, top = PAD.t;
    var slot = plotW / N;

    var maxMin = niceCeil(Math.max.apply(null, rows.map(function (r) { return r.minutes; }).concat([0])));
    var maxDoc = niceCeil(Math.max.apply(null, rows.map(function (r) { return r.docs; }).concat([0])));
    var yTicks = 4, t, y;

    /* 纵轴网格 + 分钟刻度（左） */
    var grid = el("g");
    var ylbl = el("g");
    for (t = 0; t <= yTicks; t++) {
      y = base - t * (base - top) / yTicks;
      if (t > 0) grid.appendChild(el("line", { class: "st-grid", x1: PAD.l, y1: y.toFixed(1), x2: W - PAD.r, y2: y.toFixed(1) }));
      ylbl.appendChild(say(el("text", { class: "st-lbl", x: PAD.l - 8, y: (y + 3).toFixed(1), "text-anchor": "end" }),
        String(Math.round(maxMin * t / yTicks))));
    }
    /* 右轴：文档数刻度（淡） */
    var ylblDoc = el("g");
    if (maxDoc > 0) {
      for (t = 0; t <= yTicks; t++) {
        y = base - t * (base - top) / yTicks;
        ylblDoc.appendChild(say(el("text", { class: "st-lbl-doc", x: W - PAD.r + 6, y: (y + 3).toFixed(1), "text-anchor": "start" }),
          String(Math.round(maxDoc * t / yTicks))));
      }
    }
    grid.appendChild(el("line", { class: "st-axis", x1: PAD.l, y1: base, x2: W - PAD.r, y2: base }));
    svg.appendChild(grid); svg.appendChild(ylbl); svg.appendChild(ylblDoc);

    /* 柱 + 折线 */
    var barW = Math.max(3, Math.min(18, slot * 0.56));
    var bars = el("g");
    var docPts = [];
    var peak = rows.reduce(function (a, b) { return b.minutes > a.minutes ? b : a; }, rows[0]);
    rows.forEach(function (r) {
      var cx = PAD.l + (r.day - 1) * slot + slot / 2;
      var g = el("g", { class: "st-bar" + (r === peak && r.minutes > 0 ? " st-bar-hot" : "") });
      g.appendChild(say(el("title"), "第 " + r.day + " 天：" + r.minutes + " 分钟 / " + r.docs + " 篇"));
      if (r.minutes > 0) {
        var hMin = Math.max(2, (r.minutes / maxMin) * (base - top));
        g.appendChild(el("rect", { x: (cx - barW / 2).toFixed(1), y: (base - hMin).toFixed(1),
          width: barW.toFixed(1), height: hMin.toFixed(1), rx: 2, fill: "var(--c-acc)" }));
      } else {
        /* 缺失/零数据日：留一条极细基线刻度，保证日历连续可读 */
        g.appendChild(el("rect", { x: (cx - barW / 2).toFixed(1), y: (base - 1.5).toFixed(1),
          width: barW.toFixed(1), height: 1.5, rx: 0.6, fill: "var(--c-line)" }));
      }
      bars.appendChild(g);
      docPts.push([cx, base - (maxDoc > 0 ? (r.docs / maxDoc) * (base - top) : 0), r.docs]);
    });
    svg.appendChild(bars);

    if (maxDoc > 0) {
      svg.appendChild(el("polyline", { class: "st-doc-line",
        points: docPts.map(function (p) { return p[0].toFixed(1) + "," + p[1].toFixed(1); }).join(" ") }));
      docPts.forEach(function (p) {
        if (p[2] > 0) svg.appendChild(el("circle", { class: "st-doc-dot", cx: p[0].toFixed(1), cy: p[1].toFixed(1), r: 2 }));
      });
    }

    /* 横轴刻度：1、每 5 天一个、末尾补最后一天 */
    var xlbl = el("g");
    var marks = [1];
    for (var d = 5; d <= N; d += 5) marks.push(d);
    if (N - marks[marks.length - 1] >= 2) marks.push(N);
    marks.forEach(function (d) {
      var cx = PAD.l + (d - 1) * slot + slot / 2;
      xlbl.appendChild(say(el("text", { class: "st-lbl", x: cx.toFixed(1), y: base + 15, "text-anchor": "middle" }), String(d)));
    });
    xlbl.appendChild(say(el("text", { class: "st-lbl", x: W - PAD.r, y: base + 29, "text-anchor": "end" }), "日"));
    svg.appendChild(xlbl);

    /* 峰值标注（真实数值，不让高度独自表意） */
    if (peak.minutes > 0) {
      var pcx = PAD.l + (peak.day - 1) * slot + slot / 2;
      var pcy = base - Math.max(2, (peak.minutes / maxMin) * (base - top));
      svg.appendChild(say(el("text", { class: "st-peak-lbl", x: pcx.toFixed(1), y: (pcy - 6).toFixed(1), "text-anchor": "middle" }),
        peak.minutes + "\u2032"));
    }

    /* 底部文案 */
    var note = document.getElementById("stChartNote");
    if (note) {
      var activeDays = rows.filter(function (r) { return r.minutes > 0; }).length;
      note.innerHTML = "峰值 <b>第 " + peak.day + " 天 · " + peak.minutes + " 分钟</b>"
        + " · 有记录 " + activeDays + " 天 · 日均 " + (sumMin / N).toFixed(1) + " 分钟"
        + " · 悬停柱体看每日明细";
    }
    return true;
  }

  /* ---------- 揭示动画兜底 ---------- */
  function ensureRevealed() {
    Array.prototype.forEach.call(document.querySelectorAll(".stats-body [data-reveal]"), function (n) {
      if (parseFloat(getComputedStyle(n).opacity) < 0.99) {
        n.classList.add("in");
        n.style.opacity = "";
        n.style.transform = "";
      }
    });
  }

  var resizeTimer = null;
  function onResize() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { drawDaily(); }, 180);
  }

  /* ---------- C3-B2：复习卡覆盖 · 阶段分布（7 域骨架，三段计数堆叠条） ---------- */
  function initMastery() {
    var body = document.getElementById("stMasteryBody");
    var sum = document.getElementById("stMasterySum");
    if (!body || !window.KB || !KB.api) return;
    KB.api.mastery({ scope: "domain", all: 1 }).then(function (j) {
      var items = j.items || [];
      var tot = j.totals || {};
      if (!items.length || !tot.total) {
        body.innerHTML = '<div class="kb-empty" style="padding:8px 2px">复习库暂无数据</div>';
        return;
      }
      var covered = items.filter(function (x) { return x.total > 0; }).length;
      if (sum) sum.textContent = tot.total + " 卡 · 覆盖 " + covered + "/" + items.length +
        " 域 · new " + (tot.new || 0) + " / learning " + (tot.learning || 0) + " / mastered " + (tot.mastered || 0);
      body.innerHTML = items.map(function (it) {
        var total = it.total || 0;
        var wN = total ? (it.new / total) * 100 : 0;
        var wL = total ? (it.learning / total) * 100 : 0;
        var wM = total ? (it.mastered / total) * 100 : 0;
        var segs = total ? (
          '<i class="s-new" style="width:' + wN.toFixed(2) + '%"></i>' +
          '<i class="s-learn" style="width:' + wL.toFixed(2) + '%"></i>' +
          '<i class="s-master" style="width:' + wM.toFixed(2) + '%"></i>'
        ) : "";
        var counts = total
          ? '<span class="st-mastery-n"><b class="c-new">' + it.new + '</b> / <b class="c-learn">' + it.learning + '</b> / <b class="c-master">' + it.mastered + '</b></span>'
          : '<span class="st-mastery-none">未建卡</span>';
        return '<div class="st-mastery-row' + (total ? "" : " is-empty") + '">' +
          '<span class="dot" style="--dh:' + (it.hue || 158) + '"></span>' +
          '<span class="lab">' + it.label + '</span>' +
          '<span class="bar">' + segs + '</span>' + counts + '</div>';
      }).join("");
    }).catch(function () {
      body.innerHTML = '<div class="kb-empty" style="padding:8px 2px">复习库暂无数据</div>';
    });
  }

  function init() {
    initSparks();
    drawDaily();
    initMastery();
    if (!(window.gsap && window.Motion && !reduced)) ensureRevealed();   // GSAP 未就绪 → 立即显示
    setTimeout(ensureRevealed, 1200);                                   // 失败安全：超时仍隐形就强制显示
    window.addEventListener("resize", onResize);
    if (window.Motion && typeof window.Motion.refresh === "function") window.Motion.refresh();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
