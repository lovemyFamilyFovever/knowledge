/* 知库 motion.js · Awwwards 动效基建（T0 产出）
   spec：docs/superpowers/specs/2026-09-11-zhiku-awwwards-refactor-design.md §4.2
   五个配方：revealGroup / countUp / magnetize / lineMaskReveal / scrubUnderline（initCursor 已移除：原生光标还原）
   约定：
   - 全部幂等（dataset.motionBound 防重复绑定），可重复调用 refresh()
   - 声明式挂载：data-reveal / data-counter / data-magnetic / data-line-mask / data-scrub-underline
   - prefers-reduced-motion: reduce → 全部 no-op（不隐藏内容、不做补间）
   - reveal 一律走 IntersectionObserver + CSS 过渡（style.css 的 html.motion-ready [data-reveal] + .in）。
     历史：曾用 gsap.fromTo(opacity:0,y) 先藏后放，ScrollTrigger 异常时元素会永久卡在
     中间态（2026-09-13 用户实测复现：收件箱占位空条、tagline stagger 错位）——已废弃，
     初态归 CSS、JS 只加 .in，过渡一旦开始必然完成。
     counter/magnetize/lineMask/scrub 仍可用 gsap（无卡死风险） */
(function () {
  "use strict";
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var hasGsap = typeof window.gsap !== "undefined";
  var hasST = hasGsap && typeof window.ScrollTrigger !== "undefined";
  if (hasGsap && hasST) { try { window.gsap.registerPlugin(window.ScrollTrigger); } catch (e) { hasST = false; } }

  /* ---------- 1. reveal：进视口淡入 + 上移归位（IO + CSS 类，不用 gsap.fromTo） ----------
     初态由 style.css 的 html.motion-ready [data-reveal] 提供（opacity:0 + translateY），
     本函数只负责在元素接近视口时加 .in；无 IO 时立即显示。 */
  function revealByClass(els, staggerMs) {
    var list = Array.prototype.slice.call(els);
    if (!list.length) return;
    var show = function (el) {
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { el.classList.add("in"); });
      });
    };
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          io.unobserve(en.target);
          var i = list.indexOf(en.target);
          en.target.style.transitionDelay = ((i > 0 ? i : 0) * staggerMs) + "ms";
          show(en.target);
        });
      }, { rootMargin: "0px 0px -12% 0px" }); /* 近似原 start:"top 88%" */
      list.forEach(function (el) { io.observe(el); });
    } else {
      list.forEach(function (el, i) {
        el.style.transitionDelay = (i * staggerMs) + "ms";
        show(el);
      });
    }
  }

  function revealGroup(container, opts) {
    if (reduced) return;
    opts = opts || {};
    var root = container || document;
    var items = root.querySelectorAll("[data-reveal]:not([data-motion-bound])");
    if (!items.length) return;
    var stagger = opts.stagger != null ? opts.stagger : 0.05;
    Array.prototype.forEach.call(items, function (el) { el.dataset.motionBound = "1"; });
    revealByClass(items, stagger * 1000);
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
    var dur = opts.duration != null ? opts.duration : (parseFloat(el.dataset.countDuration) || 1.5);
    var dly = opts.delay != null ? opts.delay : (parseFloat(el.dataset.countDelay) || 0);
    var state = { v: 0 };
    window.gsap.to(state, {
      v: to, duration: dur, delay: dly, ease: "power2.out",
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
      revealByClass(groupEls, 50);
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
    /* 页面/app.js 动态渲染后手动刷新（幂等） */
    refresh: function () { if (hasST) { try { window.ScrollTrigger.refresh(); } catch (e) {} } scheduleScan(); },
    init: function () {
      if (reduced) return; /* 静态呈现，不加 .motion-ready（内容始终可见） */
      document.documentElement.classList.add("motion-ready");
      
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
