/* 知库 cursor.js · 自定义跟随光标 + 上下文标签（T0 产出）
   spec：docs/superpowers/specs/2026-09-11-zhiku-awwwards-refactor-design.md §4.2 第 6 条
   - dot 即时跟随，ring 以 lerp 缓动追赶；可交互元素上 ring 展开并显示上下文标签
   - 仅 pointer:fine 且非 prefers-reduced-motion 时启用；触屏 / 降级环境零副作用
   - 幂等：window.KbCursor.init() 重复调用安全；motion.js 会委托到这里 */
(function () {
  "use strict";
  var started = false;
  var DEFAULT_LABELS = { a: "打开", "data-action=delete": "删除" };

  function labelFor(target) {
    if (!target) return "";
    if (target.dataset && target.dataset.cursorLabel) return target.dataset.cursorLabel;
    var el = target.closest && target.closest("[data-cursor-label]");
    if (el) return el.dataset.cursorLabel;
    /* spec 示例映射：a → 打开；data-action=delete → 删除 */
    var act = target.closest && target.closest('[data-action="delete"]');
    if (act) return DEFAULT_LABELS["data-action=delete"];
    if (target.closest && target.closest("a[href]")) return DEFAULT_LABELS.a;
    return "";
  }

  function init(opts) {
    opts = opts || {};
    if (started) return;
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!window.matchMedia || !window.matchMedia("(pointer: fine)").matches) return;
    if (!document.body) return;
    started = true;

    var dot = document.createElement("div");
    dot.className = "cursor-dot";
    dot.setAttribute("aria-hidden", "true");
    var ring = document.createElement("div");
    ring.className = "cursor-ring";
    ring.setAttribute("aria-hidden", "true");
    var label = document.createElement("div");
    label.className = "cursor-label";
    label.setAttribute("aria-hidden", "true");
    document.body.appendChild(dot);
    document.body.appendChild(ring);
    document.body.appendChild(label);
    document.documentElement.classList.add("cursor-on");

    var x = innerWidth / 2, y = innerHeight / 2;   /* 指针即时位 */
    var rx = x, ry = y;                            /* ring 缓动位 */
    var visible = false;

    document.addEventListener("mousemove", function (e) {
      x = e.clientX; y = e.clientY;
      if (!visible) { visible = true; rx = x; ry = y; }
      dot.style.transform = "translate(" + x + "px," + y + "px)";
      label.style.transform = "translate(" + (x + 14) + "px," + (y + 14) + "px)";
      var t = e.target && e.target.closest
        ? e.target.closest("a,button,[role=button],input,textarea,select,label,[data-magnetic]")
        : null;
      ring.classList.toggle("is-hover", !!t);
      var text = labelFor(e.target);
      if (text) { label.textContent = text; label.classList.add("show"); }
      else label.classList.remove("show");
    }, { passive: true });

    document.addEventListener("mouseleave", function () {
      dot.style.opacity = "0"; ring.style.opacity = "0"; label.classList.remove("show");
    });
    document.addEventListener("mouseenter", function () {
      dot.style.opacity = ""; ring.style.opacity = "";
    });

    (function loop() {
      rx += (x - rx) * 0.2;
      ry += (y - ry) * 0.2;
      ring.style.transform = "translate(" + rx + "px," + ry + "px)";
      requestAnimationFrame(loop);
    })();
  }

  window.KbCursor = { init: init };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { init(); });
  else init();
})();
