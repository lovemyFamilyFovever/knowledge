/* 知库 stats.js · T4 月度统计页（设计基准 v0.4 第 07 屏）
   数据来源：仅 /stats 模板内嵌的真实统计数据（#st-daily-data，来自 ReadingStore.monthly）。
   不造假数据：无序列的图直接不渲染，不填充占位。
   依赖 T0：window.Motion（reduced 标志、refresh）；GSAP 缺失时全部静态呈现。 */
(function () {
  "use strict";

  var raw = document.getElementById("st-daily-data");
  var daily = [];
  try { daily = JSON.parse(raw && raw.textContent || "[]") || []; } catch (e) { daily = []; }
  var reduced = window.Motion && window.Motion.reduced;

  var SVGNS = "http://www.w3.org/2000/svg";
  function el(tag, attrs) {
    var n = document.createElementNS(SVGNS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  /* ---------- KPI 迷你 sparkline（内联 SVG polyline） ---------- */
  function sparkline(container, values, stroke) {
    if (!container || !values.length) return;
    var w = 100, h = 24, max = Math.max.apply(null, values) || 1;
    var pts = values.map(function (v, i) {
      var x = values.length > 1 ? i * w / (values.length - 1) : 0;
      return x.toFixed(1) + "," + (h - 2 - (v / max) * (h - 4)).toFixed(1);
    });
    var svg = el("svg", { viewBox: "0 0 " + w + " " + h, preserveAspectRatio: "none" });
    svg.appendChild(el("polygon", {
      class: "spark-fill", fill: stroke, stroke: "none",
      points: "0," + h + " " + pts.join(" ") + " " + w + "," + h
    }));
    svg.appendChild(el("polyline", {
      fill: "none", stroke: stroke, "stroke-width": "1.5",
      "stroke-linecap": "round", "stroke-linejoin": "round", points: pts.join(" ")
    }));
    var last = pts[pts.length - 1].split(",");
    svg.appendChild(el("circle", {
      class: "spark-dot", fill: stroke, cx: last[0], cy: last[1]
    }));
    container.appendChild(svg);
  }

  function initSparks() {
    var minutes = daily.map(function (d) { return d.minutes; });
    var docs = daily.map(function (d) { return d.docs; });
    var presence = daily.map(function (d) { return d.minutes > 0 ? 1 : 0; });
    var map = { minutes: [minutes, "var(--acc)"], docs: [docs, "var(--acc2)"], presence: [presence, "var(--acc)"] };
    Array.prototype.forEach.call(document.querySelectorAll("[data-spark]"), function (c) {
      var cfg = map[c.dataset.spark];
      if (cfg && cfg[0].length) sparkline(c, cfg[0], cfg[1]);
      else c.innerHTML = '<span class="st-spark-none">NO SERIES</span>';
    });
  }

  /* ---------- 每日条形图：双色柱（阅读分钟 --acc · 打开文档数 --acc2） ---------- */
  function buildChart() {
    var svg = document.getElementById("stDailyChart");
    if (!svg || !daily.length) return;
    var W = 900, H = 200, padL = 34, padR = 10, base = 180, top = 14;
    var maxMin = Math.max.apply(null, daily.map(function (d) { return d.minutes; })) || 1;
    var maxDoc = Math.max.apply(null, daily.map(function (d) { return d.docs; })) || 1;
    /* 整数档刻度：向上取整到 1/2/5×10^n 的 nice step */
    function niceMax(v) {
      var pow = Math.pow(10, Math.floor(Math.log(v || 1) / Math.LN10));
      var f = v / pow;
      var n = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10;
      return n * pow;
    }
    maxMin = niceMax(maxMin);
    var plotW = W - padL - padR;
    var slot = plotW / daily.length;
    var barW = Math.min(18, Math.max(6, slot * 0.42));
    var ticks = 4;

    /* 网格 + mono 坐标（分钟轴，左） */
    var grid = el("g", { stroke: "var(--edge)", "stroke-width": "1", fill: "none" });
    var labels = el("g", { "font-family": "var(--mono)", "font-size": "9", fill: "var(--faint)", stroke: "none" });
    for (var t = 0; t <= ticks; t++) {
      var yv = base - t * (base - top) / ticks;
      var v = maxMin * t / ticks;
      grid.appendChild(el("line", {
        x1: padL, y1: yv, x2: W - padR, y2: yv,
        "stroke-dasharray": t === 0 ? "" : "2 4", opacity: t === 0 ? "1" : ".5"
      }));
      var txt = el("text", { x: padL - 6, y: yv + 3, "text-anchor": "end" });
      txt.textContent = Math.round(v);
      labels.appendChild(txt);
    }
    svg.appendChild(grid);
    svg.appendChild(labels);

    /* 柱：主序列分钟（--acc）+ 副序列文档数（--acc2，独立归一） */
    var bars = el("g");
    var days = el("g", { "font-family": "var(--mono)", "font-size": "8", fill: "var(--faint)", stroke: "none" });
    var peak = daily.reduce(function (a, b) { return b.minutes > a.minutes ? b : a; }, daily[0]);
    daily.forEach(function (d, i) {
      var cx = padL + slot * i + slot / 2;
      var hMin = Math.max(2, (d.minutes / maxMin) * (base - top));
      var g = el("g", { class: "st-bar" + (d === peak ? " st-bar-hot" : "") });
      var title = el("title");
      title.textContent = d.day + "：" + d.minutes + " 分钟 / " + d.docs + " 篇";
      g.appendChild(title);
      g.appendChild(el("rect", {
        x: (cx - barW - 1).toFixed(1), y: (base - hMin).toFixed(1),
        width: barW, height: hMin.toFixed(1), rx: "2", fill: "var(--acc)"
      }));
      if (d.docs > 0) {
        var hDoc = Math.max(2, (d.docs / maxDoc) * (base - top));
        g.appendChild(el("rect", {
          x: (cx + 1).toFixed(1), y: (base - hDoc).toFixed(1),
          width: barW, height: hDoc.toFixed(1), rx: "2", fill: "var(--acc2)", opacity: ".85"
        }));
      }
      var dt = el("text", { x: cx.toFixed(1), y: base + 14, "text-anchor": "middle" });
      dt.textContent = d.day.slice(8);
      days.appendChild(dt);
      bars.appendChild(g);
    });
    svg.appendChild(bars);
    svg.appendChild(days);

    /* 峰值注释（mono，真实数据） */
    var note = document.getElementById("stChartNote");
    if (note) {
      var avg = daily.reduce(function (s, d) { return s + d.minutes; }, 0) / daily.length;
      note.innerHTML = "峰值 <b>" + peak.day.slice(5) + " · " + peak.minutes + " 分钟</b>"
        + " · 有记录 " + daily.length + " 天 · 日均 " + avg.toFixed(1) + " 分钟"
        + " · 悬停柱体查看每日明细 · 峰值日描边高亮";
      var hot = svg.querySelector(".st-bar-hot rect");
      if (hot) hot.setAttribute("stroke", "var(--warn)"), hot.setAttribute("stroke-width", "1.5");
    }
  }

  function init() {
    initSparks();
    buildChart();
    if (window.Motion && typeof window.Motion.refresh === "function") window.Motion.refresh();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
