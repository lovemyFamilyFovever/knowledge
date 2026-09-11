/* 知库 · Home 页面交互（T2 产出 · 只服务 home.html）
   依赖：T0 motion.js（window.Motion）+ vendor GSAP/ScrollTrigger。
   本页仅补两件 motion.js 不覆盖的事：
   1) hero mascot 鼠标视差（spec §5.1：data-depth 分层，reduced-motion 关）
   2) Motion.refresh() 兜底（本页 DOM 全部服务端渲染，正常无需；防御性调用一次）
   其余动效全部声明式：data-reveal / data-counter / data-magnetic / data-line-mask。 */
(function () {
  "use strict";
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
