/* 知库 stats.js · 月度统计页
   数据来源：仅模板内嵌的真实统计数据（#st-daily-data，来自 ReadingStore.monthly）。
   设计要点：
   1. 横轴按**日历**定位（1..当月天数），缺失日 0 值仍保留刻度；
   2. 只有真正有数据时才画图：无序列直接返回，不留空白图卡、不编数；
   3. 图表引擎用本地 Chart.js（static/vendor/chart.umd.js，零 CDN、零外链）；
      取色一律从 CSS 变量读，主题切换后整组销毁重建，保证深浅色都跟手；
   4. 峰值等真实数值用自定义 plugin 直接标在图上，不让高度独自表意；
   5. 揭示动画兜底：任何 [data-reveal] 若被卡成隐形，超时后强制可见。
   依赖：window.Chart（缺失时图表留白，页面其余部分照常工作）、
        window.Motion（可选，缺失即静态呈现）。 */
(function () {
  "use strict";

  var reduced = !!(window.Motion && window.Motion.reduced);
  var ANIM = reduced ? false : { duration: 600, easing: "easeOutQuart" };

  /* ---------- 令牌取色（CSS 变量 → canvas 可用色） ---------- */
  function cssVar(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback || "";
  }
  /* #rgb / #rrggbb → rgba(...)；其它色形式（函数式/关键字）原样返回，不做透明度处理 */
  function withAlpha(color, alpha) {
    var m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(color);
    if (!m) return color;
    var hex = m[1];
    if (hex.length === 3) hex = hex.split("").map(function (c) { return c + c; }).join("");
    var n = parseInt(hex, 16);
    return "rgba(" + [(n >> 16) & 255, (n >> 8) & 255, n & 255].join(",") + "," + alpha + ")";
  }
  /* 自上而下的淡出渐变（面积填充用），拿不到绘图区时退回纯色 */
  function fade(color, ctx, area, alpha) {
    if (!area) return withAlpha(color, alpha);
    var g = ctx.createLinearGradient(0, area.top, 0, area.bottom);
    g.addColorStop(0, withAlpha(color, alpha));
    g.addColorStop(1, withAlpha(color, 0));
    return g;
  }

  /* ---------- 读原始序列 ---------- */
  var daily = (function () {
    var raw = document.getElementById("st-daily-data");
    try { return JSON.parse((raw && raw.textContent) || "[]") || []; } catch { return []; }
  })();

  function dayNum(s) {
    var m = /(\d{4})-(\d{2})-(\d{2})/.exec(String(s == null ? "" : s));
    if (m) return +m[3];
    var n = parseInt(s, 10);
    return isFinite(n) ? n : NaN;
  }

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

  /* ---------- 实例登记：主题切换时统一销毁重建 ---------- */
  var charts = [];
  function mount(canvas, cfg) {
    var c = new window.Chart(canvas, cfg);
    charts.push(c);
    return c;
  }

  /* ---------- KPI 迷你 sparkline（无坐标轴；无数据不画、不写占位） ---------- */
  function sparkline(container, values, token) {
    var max = Math.max.apply(null, values.concat([0]));
    if (values.length < 2 || !(max > 0)) return false;
    var color = cssVar(token);
    var cv = document.createElement("canvas");
    container.appendChild(cv);
    mount(cv, {
      type: "line",
      data: {
        labels: values.map(function (_, i) { return i + 1; }),
        datasets: [{
          data: values,
          borderColor: color,
          borderWidth: 1.6,
          tension: 0.35,
          fill: true,
          backgroundColor: function (c) {
            return fade(color, c.chart.ctx, c.chart.chartArea, 0.16);
          },
          pointRadius: values.map(function (v, i) {
            return i === values.length - 1 && v > 0 ? 2.4 : 0;
          }),
          pointBackgroundColor: color,
          pointBorderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: ANIM,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: { x: { display: false }, y: { display: false, beginAtZero: true } }
      }
    });
    return true;
  }

  function initSparks() {
    var minutes = SERIES.rows.map(function (r) { return r.minutes; });
    var docs = SERIES.rows.map(function (r) { return r.docs; });
    var presence = SERIES.rows.map(function (r) { return r.minutes > 0 ? 1 : 0; });
    var map = { minutes: [minutes, "--c-acc"], docs: [docs, "--c-info"], presence: [presence, "--c-acc"] };
    Array.prototype.forEach.call(document.querySelectorAll("[data-spark]"), function (c) {
      c.textContent = "";                                   // 幂等：重绘前先清空容器
      var cfg = map[c.getAttribute("data-spark")];
      if (!cfg || !window.Chart) return;
      sparkline(c, cfg[0], cfg[1]);
    });
  }

  /* ---------- 每日图：柱=阅读分钟（左轴），虚线折线=打开文档数（右轴） ---------- */
  function drawDaily() {
    var cv = document.getElementById("stDailyChart");
    var note = document.getElementById("stChartNote");
    var rows = SERIES.rows, N = SERIES.N;
    var sumMin = rows.reduce(function (s, r) { return s + r.minutes; }, 0);
    var sumDoc = rows.reduce(function (s, r) { return s + r.docs; }, 0);
    if (!cv || !window.Chart) return false;
    if (!(sumMin > 0) && !(sumDoc > 0)) return false;        // 无数据 → 不渲染

    var acc = cssVar("--c-acc"), info = cssVar("--c-info"), warn = cssVar("--c-warn"),
      line = cssVar("--c-line"), line2 = cssVar("--c-line2"),
      faint = cssVar("--faint"), ink = cssVar("--c-ink"), panel = cssVar("--c-panel"),
      mono = cssVar("--f-mono", "monospace");
    var font = { family: mono };

    var peakIdx = 0;
    rows.forEach(function (r, i) { if (r.minutes > rows[peakIdx].minutes) peakIdx = i; });

    /* 峰值真实数值直接标在柱顶（色盲兜底：数值 + 高度双重编码） */
    var peakLabel = {
      id: "kbPeakLabel",
      afterDatasetsDraw: function (chart) {
        var el = chart.getDatasetMeta(0).data[peakIdx];
        if (!el || !(rows[peakIdx].minutes > 0)) return;
        var ctx = chart.ctx;
        ctx.save();
        ctx.font = "600 10px " + mono;
        ctx.fillStyle = warn;
        ctx.textAlign = "center";
        ctx.fillText(rows[peakIdx].minutes + "\u2032", el.x, el.y - 6);
        ctx.restore();
      }
    };

    mount(cv, {
      type: "bar",
      data: {
        labels: rows.map(function (r) { return r.day; }),
        datasets: [
          {
            label: "阅读分钟",
            yAxisID: "y",
            data: rows.map(function (r) { return r.minutes; }),
            backgroundColor: function (c) {
              var hot = c.dataIndex === peakIdx;
              return fade(hot ? warn : acc, c.chart.ctx, c.chart.chartArea, hot ? 0.95 : 0.88);
            },
            borderRadius: 3,
            borderSkipped: false,
            maxBarThickness: 18,
            order: 2
          },
          {
            type: "line",
            label: "打开文档数",
            yAxisID: "y1",
            data: rows.map(function (r) { return r.docs; }),
            borderColor: info,
            borderWidth: 1.6,
            borderDash: [4, 4],                              // 色盲兜底：线型 + 色双重编码
            tension: 0.3,
            fill: false,
            pointRadius: function (c) { return c.raw > 0 ? 2.4 : 0; },
            pointBackgroundColor: info,
            pointBorderWidth: 0,
            order: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: ANIM,
        interaction: { mode: "index", intersect: false },
        layout: { padding: { top: 16 } },
        plugins: {
          legend: { display: false },                        // 图例走卡头 HTML（可点选的那套留给后续）
          tooltip: {
            backgroundColor: panel,
            titleColor: ink,
            bodyColor: ink,
            borderColor: line2,
            borderWidth: 1,
            padding: 10,
            cornerRadius: 6,
            titleFont: font,
            bodyFont: font,
            usePointStyle: true,
            callbacks: {
              title: function (items) { return "第 " + items[0].label + " 天"; },
              label: function (it) {
                return it.dataset.yAxisID === "y"
                  ? " 阅读 " + it.formattedValue + " 分钟"
                  : " 打开 " + it.formattedValue + " 篇";
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            border: { color: line2 },
            ticks: {
              color: faint,
              font: font,
              autoSkip: false,
              maxRotation: 0,
              callback: function (_v, i) {
                var d = i + 1;
                return (d === 1 || d % 5 === 0 || d === N) ? d : "";
              }
            }
          },
          y: {
            beginAtZero: true,
            position: "left",
            grid: { color: withAlpha(line, 0.7), tickLength: 0 },
            border: { display: false },
            ticks: { color: faint, font: font, maxTicksLimit: 5, padding: 6 }
          },
          y1: {
            beginAtZero: true,
            position: "right",
            grid: { drawOnChartArea: false },
            border: { display: false },
            ticks: { color: info, font: font, maxTicksLimit: 5, precision: 0, padding: 6 }
          }
        }
      },
      plugins: [peakLabel]
    });

    if (note) {
      var activeDays = rows.filter(function (r) { return r.minutes > 0; }).length;
      var peak = rows[peakIdx];
      note.innerHTML = "峰值 <b>第 " + peak.day + " 天 · " + peak.minutes + " 分钟</b>"
        + " · 有记录 " + activeDays + " 天 · 日均 " + (sumMin / N).toFixed(1) + " 分钟"
        + " · 悬停查看每日明细";
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

  /* ---------- 渲染 / 重渲染（主题切换后取色必须重来一遍） ---------- */
  function renderCharts() {
    charts.forEach(function (c) { c.destroy(); });
    charts = [];
    initSparks();
    drawDaily();
  }

  function init() {
    renderCharts();
    initMastery();
    if (!(window.gsap && window.Motion && !reduced)) ensureRevealed();   // GSAP 未就绪 → 立即显示
    setTimeout(ensureRevealed, 1200);                                   // 失败安全：超时仍隐形就强制显示
    /* 主题永远走 applyTheme() + html[data-theme]，这里只观察属性变化，不碰写入 */
    new MutationObserver(function () { renderCharts(); })
      .observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    if (window.Motion && typeof window.Motion.refresh === "function") window.Motion.refresh();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
