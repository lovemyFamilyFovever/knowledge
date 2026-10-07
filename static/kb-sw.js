/* 知库 · 公网只读档的 Service Worker —— 只由 scripts/export_static.py 复制到站根
   （site/sw.js）并替换下面两个占位符后生效；本地 Flask 阅读器不加载它。

   为什么放 static/ 而不是写在导出脚本里：这份是要被 eslint 管、被人读的 JS，
   塞进 Python 字符串就没人检查它（同类事故见 AGENTS「正文里的 \n 被 Python 先吃掉」）。

   缓存口径（三条，按"错了会怎样"分档）：
   · 导航（HTML）—— 网络优先，断了回壳（index.html）。深链靠 SPA 自己按 pathname 路由，
     所以离线打开"上次看过的任意一篇"是成立的；没看过的回壳后走首页态。
   · data/*.json —— 网络优先 + 落缓存。语料是唯一事实源，线上永远给最新的；
     断网时才读缓存，读到的是上次访问的那份。
   · static/* 与 raw/* —— 缓存优先。JS/CSS 带 ?v=内容版本，改了 URL 就变，
     所以缓存优先不会把人钉在旧代码上；图片路径不变，靠 BUILD 换库来失效。
   每次部署 BUILD 变 → activate 里把旧 zhiku-* 库全删，不留第二份真相。 */

var KB_BASE = "__KB_BASE__";    // 导出器替换：'' 或 '/knowledge'
var KB_BUILD = "__KB_BUILD__";  // 导出器替换：本次导出的 git sha

var SHELL = KB_BASE + "/";
var HOME = KB_BASE + "/data/home.html";   // 首页片段：不预热的话离线打开站根会露出壳里烤死的那篇
/* 壳引用到的 static 资源清单，由导出器从产物 index.html 里扫出来原样写在这里
   （当前实测 30 件 / 1.5MB，条数随模板走，不手写名单）。为什么不让 SW 自己去抓一遍：
   首屏那趟加载发生在 SW 还没接管的时候，CSS/JS 根本没进缓存；等第二次导航才补，
   中间那次离线就会拿到整页裸 HTML —— 本机实测就是这个形状（style.css / app.js 全 ERR_FAILED）。
   清单从产物扫，不写死：模板加了资源也不会漏，也不会漂移出一份过时的名单。 */
var PRECACHE = __KB_PRECACHE__;  // eslint-disable-line no-undef -- 导出器把这一个 token 换成 JSON 数组
var CACHE_SHELL = "zhiku-shell-" + KB_BUILD;
var CACHE_DATA = "zhiku-data-" + KB_BUILD;
var CACHE_ASSET = "zhiku-asset-" + KB_BUILD;
var DATA_MAX = 800;             // data 缓存条数上限：全库 1000+ 篇，只留最近访问的这些

self.addEventListener("install", function () {
  self.skipWaiting();
  // 预热壳 + 首页片段 + 壳的 CSS/JS/字体；语料一条不预热（整站 42MB、data 就占 32MB，
  // 那是对用户磁盘的冒犯）。
  caches.open(CACHE_SHELL).then(function (c) {
    c.add(SHELL).catch(function () {});
    c.add(HOME).catch(function () {});
    PRECACHE.forEach(function (u) { c.add(u).catch(function () {}); });
  });
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) {
        return /^zhiku-(shell|data|asset)-/.test(k) &&
          k !== CACHE_SHELL && k !== CACHE_DATA && k !== CACHE_ASSET;
      }).map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

function underBase(u) {
  return u.origin === self.location.origin && (KB_BASE === "" || u.pathname === KB_BASE ||
    u.pathname.indexOf(KB_BASE + "/") === 0);
}
function kindOf(u) {
  var p = u.pathname;
  if (p.indexOf(KB_BASE + "/data/") === 0) return "data";
  if (p.indexOf(KB_BASE + "/static/") === 0 || p.indexOf(KB_BASE + "/raw/") === 0) return "asset";
  if (p === KB_BASE + "/manifest.webmanifest" || p === KB_BASE + "/sw.js") return "asset";
  return "nav";
}
function put(cacheName, req) {
  return caches.open(cacheName).then(function (c) {
    return c.add(req).then(function () {
      if (cacheName !== CACHE_DATA || !c.keys) return;
      return c.keys().then(function (ks) {
        if (ks.length <= DATA_MAX) return;
        return c.delete(ks[0]);            // Cache 没有 LRU，按插入顺序丢最旧的一条
      });
    });
  }).catch(function () {});                  // 配额满了就当没缓存，不影响读
}

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var u;
  try { u = new URL(req.url); } catch (err) { return; }
  if (!underBase(u)) return;                 // 跨源的一律放行不碰（本仓零出站，这里也不给例外开门）
  var kind = kindOf(u);
  if (req.mode === "navigate" || kind === "nav") {
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) put(CACHE_SHELL, SHELL);
        return res;
      }).catch(function () {
        return caches.match(SHELL, { ignoreSearch: true }).then(function (hit) {
          return hit || Response.error();
        });
      })
    );
    return;
  }
  if (kind === "data") {
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) put(CACHE_DATA, req);
        return res;
      }).catch(function () {
        return caches.match(req, { ignoreSearch: true }).then(function (hit) {
          return hit || Response.error();
        });
      })
    );
    return;
  }
  e.respondWith(
    caches.match(req, { ignoreSearch: false }).then(function (hit) {
      if (hit) return hit;
      return fetch(req).then(function (res) {
        if (res && res.ok) put(CACHE_ASSET, req);
        return res;
      });
    })
  );
});
