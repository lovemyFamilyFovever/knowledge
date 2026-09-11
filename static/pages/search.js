/* 知库 · 搜索结果页交互（T3 产出 · frontend-redesign-tasks/T3-search.md）
   职责：
   1. 顶栏搜索框语义状态：输入以 ? 开头（或当前 URL 的 q 参数以 ? 开头，即语义结果页）时，
      #searchbox 挂 .semantic（style.css [6] 已提供绿→蓝 token 变色），放大镜图标换成语义图标。
   2. 结果列表 stagger reveal：服务端渲染完成后触发 Motion 扫描（motion.js 已有
      MutationObserver，这里首帧手动 refresh 一次，保证首屏就播）。
   约束：不改 app.js 公共段；全部幂等；reduced-motion 由 motion.js 自行短路。 */
(function () {
  "use strict";

  var box = document.getElementById("searchbox");
  var input = document.getElementById("q");
  if (!box || !input) return;

  /* ---------- 1. 顶栏搜索框语义状态 ---------- */
  function isSemanticPage() {
    var q = new URLSearchParams(location.search).get("q") || "";
    return q.charAt(0) === "?";
  }
  function syncSemantic() {
    var semantic = /^\s*\?/.test(input.value) || isSemanticPage();
    box.classList.toggle("semantic", semantic);
    var icon = box.querySelector("svg use");
    if (icon) icon.setAttribute("href", semantic ? "#i-search-semantic" : "#i-search-magnifier");
  }

  input.addEventListener("input", syncSemantic);
  input.addEventListener("focus", syncSemantic);
  syncSemantic();

  /* ---------- 2. 结果列表 stagger reveal ---------- */
  if (window.Motion && typeof window.Motion.refresh === "function") {
    window.Motion.refresh();
  }
})();
