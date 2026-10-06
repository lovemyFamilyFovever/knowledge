/* ============================================================
   kb-particles.js —— 蒲公英粒子连线背景
   来源：桌面 dandelion.js（经典 cnblogs 粒子连线），按本项目纪律重写：
   1) 不再往 window 撒 o/j/k/b/m/a/f/r/n/e/u/t 单字母全局变量（整段包进闭包）
   2) 不再赋值 window.onmousemove / onresize（会覆盖既有处理器），改 addEventListener
   3) 按 devicePixelRatio 画，1px 点在高分屏不发虚
   4) 颜色运行时读 --c-acc，六套皮肤与明暗态自动跟随（原脚本写死 70,180,254）
   5) 有生命周期：页面隐藏 / 挂载点被移除 / prefers-reduced-motion 时停帧，不空烧 CPU
   6) 挂载点可配：默认整屏浮层，也可塞进某个面板作局部背景
   用法：<body data-kb-particles="1" data-kb-count="70" data-kb-link="1">
   ============================================================ */
(function () {
  "use strict";
  var root = document.documentElement;
  var body = document.body;
  if (!body || !body.hasAttribute("data-kb-particles")) return;

  /* 降级：系统要求减少动效且未开「强制动效」时不启动 */
  var reduced = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced && !root.classList.contains("motion-force")) return;

  var COUNT = parseInt(body.getAttribute("data-kb-count") || "85", 10);
  var LINK = body.hasAttribute("data-kb-link");            /* 是否画粒子间连线 */
  var mountSel = body.getAttribute("data-kb-mount");
  var MOUNT = (mountSel && document.querySelector(mountSel)) || null;   /* 空串会让 querySelector 抛错，必须先判空 */

  var cv = document.createElement("canvas");
  cv.className = "kb-particles";
  cv.setAttribute("aria-hidden", "true");
  (MOUNT || body).appendChild(cv);
  var ctx = cv.getContext("2d");

  var dpr = 1, W = 0, H = 0, raf = 0, live = false;
  var dots = [];
  var mouse = { x: null, y: null, max: 26000 };
  var rgb = "31, 78, 140";   /* 兜底 = 玄青主色 */

  function readColor() {
    var v = getComputedStyle(root).getPropertyValue("--hex-primary").trim()
         || getComputedStyle(root).getPropertyValue("--c-acc").trim();
    if (!v) return;
    if (v.charAt(0) === "#") {
      var h = v.slice(1);
      if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
      var n = parseInt(h, 16);
      rgb = [(n >> 16) & 255, (n >> 8) & 255, n & 255].join(", ");
    }
  }

  function size() {
    var host = MOUNT || { clientWidth: window.innerWidth, clientHeight: window.innerHeight };
    var r = MOUNT ? MOUNT.getBoundingClientRect() : null;
    W = (r ? r.width : host.clientWidth) || window.innerWidth;
    H = (r ? r.height : host.clientHeight) || window.innerHeight;
    dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
    cv.width = Math.round(W * dpr);
    cv.height = Math.round(H * dpr);
    cv.style.width = W + "px";
    cv.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function seed() {
    dots.length = 0;
    for (var i = 0; i < COUNT; i++) {
      dots.push({ x: Math.random() * W, y: Math.random() * H,
                  xa: 2 * Math.random() - 1, ya: 2 * Math.random() - 1, max: 9000 });
    }
  }

  function frame() {
    ctx.clearRect(0, 0, W, H);
    var all = dots.concat([mouse]);
    for (var i = 0; i < dots.length; i++) {
      var p = dots[i];
      p.x += p.xa; p.y += p.ya;
      if (p.x > W || p.x < 0) p.xa *= -1;
      if (p.y > H || p.y < 0) p.ya *= -1;
      ctx.beginPath();                       /* 画实心圆点而非 1px 方点：高分屏与低透明度下才不消失 */
      ctx.fillStyle = "rgba(" + rgb + ",.85)";
      ctx.arc(p.x, p.y, 1.7, 0, 6.2832);
      ctx.fill();
      if (!LINK) continue;
      for (var j = i + 1; j < all.length; j++) {
        var q = all[j];
        if (q === p || q.x === null || q.x === undefined) continue;
        var dx = p.x - q.x, dy = p.y - q.y, d2 = dx * dx + dy * dy;
        if (d2 < q.max) {
          if (q === mouse && d2 >= q.max / 2) { p.x -= 0.03 * dx; p.y -= 0.03 * dy; }
          var a = (q.max - d2) / q.max;
          ctx.beginPath();
          ctx.lineWidth = 0.4 + a * 1.1;
          ctx.strokeStyle = "rgba(" + rgb + "," + (0.12 + a * 0.55) + ")";
          ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
        }
      }
    }
    raf = requestAnimationFrame(frame);
  }

  function start() { if (!live) { live = true; raf = requestAnimationFrame(frame); } }
  function stop() { live = false; if (raf) cancelAnimationFrame(raf); raf = 0; }

  function onMove(e) {
    var r = cv.getBoundingClientRect();
    var x = e.clientX - r.left, y = e.clientY - r.top;
    if (x < 0 || y < 0 || x > r.width || y > r.height) { mouse.x = mouse.y = null; return; }
    mouse.x = x; mouse.y = y;
  }
  function onOut() { mouse.x = mouse.y = null; }

  var ro = null;
  function onResize() { size(); seed(); }

  size(); readColor(); seed(); start();
  window.addEventListener("resize", onResize);
  window.addEventListener("mousemove", onMove);
  document.addEventListener("mouseleave", onOut);
  document.addEventListener("visibilitychange", function () { document.hidden ? stop() : start(); });

  /* 换肤 / 切明暗：重读取色令牌，下一帧生效 */
  if (window.MutationObserver) {
    new MutationObserver(readColor).observe(root, { attributes: true, attributeFilter: ["data-theme", "data-skin"] });
  }
  /* 挂载点被移除（SPA 换页）就自我了断，不留后台循环 */
  if (MOUNT && window.ResizeObserver) { ro = new ResizeObserver(onResize); ro.observe(MOUNT); }
  if (window.MutationObserver) {
    new MutationObserver(function () {
      if (!document.body.contains(cv)) {
        stop(); window.removeEventListener("resize", onResize); window.removeEventListener("mousemove", onMove);
        if (ro) ro.disconnect();
      }
    }).observe(document.body, { childList: true, subtree: true });
  }
})();
