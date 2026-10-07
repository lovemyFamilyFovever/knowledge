/* 知库 · 公网只读档的 PWA 注册件。
   只有 scripts/export_static.py 把它写进 <head>（本地阅读器不加载：热重载开发上再叠一层
   缓存，得到的只是"我明明改了为什么没变"）。
   这里任何一步失败都不影响阅读 —— manifest 与 SW 是增强层，不是依赖。 */
(function () {
  var S = window.KB_STATIC;
  if (!S || !S.readonly) return;
  if (!("serviceWorker" in navigator)) return;
  var base = S.base || "";
  // 等 load 再注册：别和首屏的 tree/doc JSON 抢带宽
  window.addEventListener("load", function () {
    navigator.serviceWorker.register(base + "/sw.js", { scope: base + "/" }).catch(function () {
      // 注册不上（http 非安全上下文、隐私模式、GH Pages 还没上线这个文件）就当没有 PWA
    });
  });
})();
