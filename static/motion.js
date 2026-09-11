/* 知库 motion.js · Awwwards 动效基建（T0 产出）
   spec：docs/superpowers/specs/2026-09-11-zhiku-awwwards-refactor-design.md §4.2
   六个配方：revealGroup / countUp / magnetize / lineMaskReveal / scrubUnderline / initCursor
   约定：
   - 全部幂等（dataset.motionBound 防重复绑定），可重复调用 refresh()
   - 声明式挂载：data-reveal / data-counter / data-magnetic / data-line-mask / data-scrub-underline
   - prefers-reduced-motion: reduce → 全部 no-op（不隐藏内容、不做补间）
   - GSAP / ScrollTrigger 缺失时自动降级：reveal 走 IntersectionObserver + CSS 过渡，
     counter 直接置终值，其余跳过；页面始终完整可读 */
(function () {
  "use strict";
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var hasGsap = typeof window.gsap !== "undefined";
  var hasST = hasGsap && typeof window.ScrollTrigger !== "undefined";
  if (hasGsap && hasST) { try { window.gsap.registerPlugin(window.ScrollTrigger); } catch (e) { hasST = false; } }

  /* ---------- 1. revealGroup：进视口依次淡入 + translateY ---------- */
  function revealGroup(container, opts) {
    if (reduced) return;
    opts = opts || {};
    var root = container || document;
    var items = root.querySelectorAll("[data-reveal]:not([data-motion-bound])");
    if (!items.length) return;
    var stagger = opts.stagger != null ? opts.stagger : 0.05;
    var y = opts.y != null ? opts.y : 40;
    var duration = opts.duration != null ? opts.duration : 0.8;
    Array.prototype.forEach.call(items, function (el) { el.dataset.motionBound = "1"; });
    if (hasGsap && hasST) {
      window.gsap.fromTo(items,
        { opacity: 0, y: y },
        { opacity: 1, y: 0, duration: duration, stagger: stagger, ease: "power3.out",
          scrollTrigger: { trigger: opts.trigger || items[0], start: "top 88%", once: true },
          clearProps: "transform" });
    } else {
      /* CSS 降级：style.css 的 html.motion-ready [data-reveal] 过渡 + .in */
      Array.prototype.forEach.call(items, function (el, i) {
        el.style.transitionDelay = (i * stagger * 1000) + "ms";
        requestAnimationFrame(function () { requestAnimationFrame(function () { el.classList.add("in"); }); });
      });
    }
  }

  /* ---------- 2. countUp：数字从 0 计到 data-count ---------- */
  function countUp(el, opts) {
    if (!el || el.dataset.motionBound === "1") return;
    el.dataset.motionBound = "1";
    var to = parseFloat(el.dataset.count != null ? el.dataset.count : (opts && opts.to));
    if (isNaN(to)) return;
    var decimals = (String(to).split(".")[1] || "").length;
    var group = el.dataset.countGroup !== "off";
    var suffix = el.dataset.countSuffix || "";
    var render = function (v) {
      var s = decimals ? v.toFixed(decimals) : Math.round(v).toString();
      if (group) s = s.replace(/\B(?=(\d{3})+(?!\d))/g, "\u2009"); /* 细空格千分位，同设计稿 1 479 */
      el.textContent = s + suffix;
    };
    if (reduced || !hasGsap) { render(to); return; }
    opts = opts || {};
    var state = { v: 0 };
    window.gsap.to(state, {
      v: to, duration: opts.duration != null ? opts.duration : 1.5, ease: "power2.out",
      onUpdate: function () { render(state.v); },
      scrollTrigger: (hasST && opts.once !== false)
        ? { trigger: el, start: "top 90%", once: true } : undefined
    });
  }

  /* ---------- 3. magnetize：元素向光标偏移 ---------- */
  function magnetize(el, opts) {
    if (!el || el.dataset.motionBound === "1") return;
    el.dataset.motionBound = "1";
    if (reduced || !hasGsap) return;
    opts = opts || {};
    var strength = opts.strength != null ? opts.strength : 0.3;
    var xTo = window.gsap.quickTo(el, "x", { duration: 0.4, ease: "power3.out" });
    var yTo = window.gsap.quickTo(el, "y", { duration: 0.4, ease: "power3.out" });
    el.addEventListener("mousemove", function (e) {
      var r = el.getBoundingClientRect();
      xTo((e.clientX - (r.left + r.width / 2)) * strength);
      yTo((e.clientY - (r.top + r.height / 2)) * strength);
    });
    el.addEventListener("mouseleave", function () { xTo(0); yTo(0); });
  }

  /* ---------- 4. lineMaskReveal：段落逐行揭示 ----------
     若 el 内已有 .line 子元素则逐行 stagger；
     否则把直接子元素视为行单元；两者皆无时对 el 本身做一次 mask 揭示。 */
  function lineMaskReveal(el, opts) {
    if (!el || el.dataset.motionBound === "1") return;
    el.dataset.motionBound = "1";
    if (reduced || !hasGsap) return;
    opts = opts || {};
    var lines = el.querySelectorAll(".line:not([data-motion-bound])");
    if (!lines.length) {
      var kids = el.children;
      if (kids.length > 1) { lines = kids; }
      else {
        window.gsap.fromTo(el,
          { clipPath: "inset(0 0 100% 0)" },
          { clipPath: "inset(0 0 0% 0)", duration: opts.duration != null ? opts.duration : 0.5, ease: "power3.out" });
        return;
      }
    }
    Array.prototype.forEach.call(lines, function (l) { l.dataset.motionBound = "1"; });
    window.gsap.fromTo(lines,
      { clipPath: "inset(0 0 100% 0)", y: 8 },
      { clipPath: "inset(0 0 0% 0)", y: 0, duration: opts.duration != null ? opts.duration : 0.5,
        stagger: opts.lineStagger != null ? opts.lineStagger : 0.02, ease: "power3.out",
        clearProps: "clip-path,transform" });
  }

  /* ---------- 5. scrubUnderline：H2 底部 hairline 随滚动被 --acc 填充 ----------
     元素需带 .kinetic-underline（style.css 提供）；JS 驱动 CSS 变量 --ul 0→1。 */
  function scrubUnderline(el, opts) {
    if (!el || el.dataset.motionBound === "1") return;
    el.dataset.motionBound = "1";
    if (!el.classList.contains("kinetic-underline")) el.classList.add("kinetic-underline");
    if (reduced || !hasST) return; /* CSS 兜底：--ul 默认 0，静态极淡 hairline */
    opts = opts || {};
    var state = { ul: 0 };
    window.gsap.to(state, {
      ul: 1, ease: "none",
      scrollTrigger: { trigger: el, start: opts.start || "top 80%", end: opts.end || "bottom 60%", scrub: true },
      onUpdate: function () { el.style.setProperty("--ul", state.ul.toFixed(3)); }
    });
  }

  /* ---------- 6. initCursor：自定义跟随光标 + 上下文标签 ----------
     完整实现由 cursor.js 提供（window.KbCursor）；本函数做委托，
     cursor.js 未加载时退化为最小实现（dot + ring 展开，无标签）。 */
  function initCursor(opts) {
    if (reduced) return;
    if (window.KbCursor && typeof window.KbCursor.init === "function") { window.KbCursor.init(opts); return; }
    if (document.documentElement.classList.contains("cursor-on")) return;
    if (!window.matchMedia || !window.matchMedia("(pointer: fine)").matches) return;
    var dot = document.createElement("div"); dot.className = "cursor-dot";
    var ring = document.createElement("div"); ring.className = "cursor-ring";
    document.body.appendChild(dot); document.body.appendChild(ring);
    document.documentElement.classList.add("cursor-on");
    var x = innerWidth / 2, y = innerHeight / 2, rx = x, ry = y;
    document.addEventListener("mousemove", function (e) {
      x = e.clientX; y = e.clientY;
      dot.style.transform = "translate(" + x + "px," + y + "px)";
      var t = e.target.closest && e.target.closest("a,button,[role=button],input,textarea,select,[data-magnetic]");
      ring.classList.toggle("is-hover", !!t);
    }, { passive: true });
    (function loop() { rx += (x - rx) * 0.2; ry += (y - ry) * 0.2;
      ring.style.transform = "translate(" + rx + "px," + ry + "px)"; requestAnimationFrame(loop); })();
  }

  /* ---------- 声明式扫描 + 动态 DOM 观察 ---------- */
  function bindAll(root) {
    if (reduced) return;
    var els = (root && root.querySelectorAll) ? root : document;
    /* reveal：按最近的 [data-reveal-group] 分组 stagger，无组则各自独立 */
    var groups = {};
    Array.prototype.forEach.call(els.querySelectorAll("[data-reveal]:not([data-motion-bound])"), function (el) {
      var g = el.closest("[data-reveal-group]") || document;
      var key = g === document ? "_doc" : Array.prototype.indexOf.call(document.querySelectorAll("[data-reveal-group]"), g);
      (groups[key] = groups[key] || []).push(el);
    });
    Object.keys(groups).forEach(function (k) {
      var groupEls = groups[k];
      groupEls.forEach(function (el) { el.dataset.motionBound = "1"; });
      if (hasGsap && hasST) {
        window.gsap.fromTo(groupEls,
          { opacity: 0, y: parseFloat(groupEls[0].dataset.revealY) || 22 },
          { opacity: 1, y: 0, duration: 0.7, stagger: 0.05, ease: "power3.out", clearProps: "transform",
            scrollTrigger: { trigger: groupEls[0], start: "top 88%", once: true } });
      } else {
        groupEls.forEach(function (el, i) {
          el.style.transitionDelay = (i * 50) + "ms";
          requestAnimationFrame(function () { requestAnimationFrame(function () { el.classList.add("in"); }); });
        });
      }
    });
    Array.prototype.forEach.call(els.querySelectorAll("[data-counter]:not([data-motion-bound])"), function (el) { countUp(el); });
    Array.prototype.forEach.call(els.querySelectorAll("[data-magnetic]:not([data-motion-bound])"), function (el) { magnetize(el, { strength: parseFloat(el.dataset.magnetic) || 0.2 }); });
    Array.prototype.forEach.call(els.querySelectorAll("[data-line-mask]:not([data-motion-bound])"), function (el) { lineMaskReveal(el); });
    Array.prototype.forEach.call(els.querySelectorAll("[data-scrub-underline]:not([data-motion-bound])"), function (el) { scrubUnderline(el); });
  }

  var scanScheduled = false;
  function scheduleScan() {
    if (scanScheduled || reduced) return;
    scanScheduled = true;
    setTimeout(function () { scanScheduled = false; bindAll(document); }, 120);
  }

  window.Motion = {
    reduced: reduced,
    revealGroup: revealGroup,
    countUp: countUp,
    magnetize: magnetize,
    lineMaskReveal: lineMaskReveal,
    scrubUnderline: scrubUnderline,
    initCursor: initCursor,
    /* 页面/app.js 动态渲染后手动刷新（幂等） */
    refresh: function () { if (hasST) { try { window.ScrollTrigger.refresh(); } catch (e) {} } scheduleScan(); },
    init: function () {
      if (reduced) return; /* 静态呈现，不加 .motion-ready（内容始终可见） */
      document.documentElement.classList.add("motion-ready");
      initCursor();
      bindAll(document);
      if (window.MutationObserver) {
        new MutationObserver(function (muts) {
          for (var i = 0; i < muts.length; i++) {
            if (muts[i].addedNodes && muts[i].addedNodes.length) { scheduleScan(); break; }
          }
        }).observe(document.body, { childList: true, subtree: true });
      }
    }
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { window.Motion.init(); });
  else window.Motion.init();
})();
