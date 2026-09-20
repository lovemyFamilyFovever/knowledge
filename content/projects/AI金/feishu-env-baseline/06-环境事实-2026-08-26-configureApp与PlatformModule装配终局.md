# 06 环境事实 —— configureApp / PlatformModule 完整装配（终局）（2026-08-26）

> 来源：飞书妙搭沙箱终端实测（`sed -n` 读 `fullstack-nestjs-core/dist/index.js` 四个关键段）。这是平台运行时装配的核心实现，此前所有 `/app/xxx` + CSRF + 鉴权疑团的底层机制在此闭环。

---

## 1. `configureApp(app, perms)` —— 完整逻辑（index.js）

```
async function configureApp(app, perms = { disableSwagger: false }) {
  const bodyLimit = perms.bodyLimit ?? process.env.BODY_SIZE_LIMIT ?? "1mb";
  app.useLogger(app.get(AppLogger));        // 平台 logger（@lark-apaas/nestjs-logger）
  app.flushLogs();
  app.use(express.json({ limit: bodyLimit }));
  app.use(express.urlencoded({ limit: bodyLimit, extended: true }));
  app.use(cookieParser());                  // 需 cookie-parser
  app.use(createLegacyPathRedirectMiddleware());
  app.use(createPublicAssetsMiddleware());
  const globalPrefix = process.env.CLIENT_BASE_PATH ?? "";
  app.setGlobalPrefix(globalPrefix);        // ⭐⭐⭐ /app/xxx 前缀的最终来源
  app.set("trust proxy", true);
  if (process.env.NODE_ENV !== "production" && perms.disableSwagger !== true) {
    await DevToolsV2Module.mount(app, { basePath: CLIENT_BASE_PATH, docsPath: "/api_docs" });
  }
}
```

### 📌 关键结论
- **`CLIENT_BASE_PATH` 被 `setGlobalPrefix` 用作 Nest 全局路由前缀** → 所有 Controller 挂在 `/app/app_4k9x70cg0jws9` 下。这是此前 AuthGuard `startsWith('/api/...')` 失配、线上 ERP 登录 401 的**根本机制**。
- **平台不手动剥前缀**给 Nest——前缀剥除由 `setGlobalPrefix` 在 Nest RouterModule 内部完成；手动 `stripBasePath2`（S3/S4）只用于**平台自定义 Express 中间件**（legacy redirect / public assets）在应用层剥前缀。
- `bodyLimit` 优先级：`perms.bodyLimit(10mb，main.ts 传) ?? BODY_SIZE_LIMIT ?? 1mb`；且 main.ts 后续 `json/urlencoded limit:20mb` 覆盖 → **实际 20mb 生效**。

---

## 2. `PlatformModule.configure(consumer)` —— 中间件矩阵（S4 前段）

```
configure(consumer) {
  const options = PlatformModule.moduleOptions;
  // 1) API 响应拦截（统一包装响应体）
  consumer.apply(apiResponseInterceptor).forRoutes("/api/*", "/openapi/*");

  // 2) development 专属 debug 中间件
  if (NODE_ENV === "development")
    consumer.apply(FrameworkDebugMiddleware).forRoutes("/api/__framework__/debug");

  // 3) 全局上下文链路（用户/请求/日志/可观测/SQL执行）
  consumer.apply(UserContextMiddleware, RequestContextMiddleware,
                 LoggerContextMiddleware, ObservableTraceMiddleware,
                 ...(DISABLE_DATAPASS ? [] : [SqlExecutionContextMiddleware]))
    .forRoutes("/*");

  // 4) ⭐ 页面侧中间件（种 CSRF cookie 等）—— 排除 api/openapi/static
  consumer.apply(CsrfTokenMiddleware, ViewContextMiddleware, HtmlHotUpdateViewMiddleware)
    .exclude("/api/(.*)", "/openapi/(.*)", "/static/(.*)").forRoutes("*");

  // 5) ⭐ API CSRF 校验（双提交）—— 默认 /api/*
  if (options.enableCsrf !== false) {
    const csrfRoutes = options.csrfRoutes || ["/api/*"];
    consumer.apply(CsrfMiddleware).forRoutes(csrfRoutes);
  }
}
```
- `PlatformModule` 标注 `@Global()` + `@Module({})`（无显式 provider，全部行为在中间件）。

### 📌 关键结论（CSRF 分工）
- **CsrfTokenMiddleware**（种 cookie，页面侧）：作用于所有**非 api/openapi/static** 请求 → 页面(HTML)首次访问时把 `suda-csrf-token` 种进 cookie（`httpOnly:false`、`partitioned:true`、`secure:true`、`sameSite:none`）。
- **CsrfMiddleware**（校验，API 侧）：默认只对 `/api/*` 校验 `header(x-suda-csrf-token) == cookie(suda-csrf-token)`，失败 403。
- **这就是"先登前台才能登 ERP"的机制**：前台是**页面请求** → 触发种 cookie；而 ERP 若直开且 cookie 未种上、或 header 读不到 → 校验不过。刷新/先访问前台后可恢复（cookie 已生成）。

---

## 3. `CsrfMiddleware`（校验）—— S1 完整逻辑

```
use(req, res, next) {
  const { headerKey, cookieKey } = options;               // "x-suda-csrf-token"/"suda-csrf-token"
  const cookieCsrfToken = req.cookies[cookieKey.toLowerCase()];
  if (!cookieCsrfToken) return sendForbidden(res, "csrf token not found in cookie.");
  const headerCsrfToken = req.headers[headerKey.toLowerCase()];
  if (!headerCsrfToken) return sendForbidden(res, "csrf token not found in header.");
  if (cookieCsrfToken !== headerCsrfToken) return sendForbidden(res, "csrf token not match.");
  next();
}
```
- 大小写统一 `toLowerCase()` 匹配。
- 三种失败均 **403 Forbidden**。

---

## 4. `CsrfTokenMiddleware`（生成/种 cookie）—— S2 完整逻辑

```
use(req, res, next) {
  const originToken = req.cookies[cookieKey.toLowerCase()];
  if (originToken) { req.csrfToken = originToken; next(); }   // 已有则复用
  else {
    const token = genToken();
    req.csrfToken = token;
    res.cookie(cookieKey, token, {
      maxAge: cookieMaxAge, path: cookiePath,
      httpOnly: false, secure: true, sameSite: "none", partitioned: true
    });
    next();
  }
}
```
- httpOnly:**false** → 前端 JS 能读到 cookie 值，放进 header 完成双提交。
- `partitioned:true` + `sameSite:none` + `secure:true` → 跨站分域 cookie 语义，支持 CSRF 双提交。

---

## 5. 两个平台自定义中间件（S3/S4）

### 5.1 legacy path redirect（旧路径迁移）
- 匹配 `/af/p/([^/]+)(/.*)?`、`/spark/faas/([^/]+)(/.*)?`。
- 仅当 `CLIENT_BASE_PATH` 符合 `/^\/app\/[^/]/` 才启用。
- 把旧路径改写成 `/app/<appId>/...`；`/api/`、`/__innerapi__/` 改写 `req.url`；GET 其余 302 重定向。

### 5.2 public assets 直出
- 解析 `process.cwd()/dist/client` 为静态根。
- `stripBasePath2` 剥前缀 → 排除 `.html`（HTML 纯前端 serve）与 `PLATFORM_PREFIXES`（`api/` `openapi/` `__innerapi__/` `__runtime__/` `static/` `dev/` `assets/`）→ 其余文件直出（带 ETag/MIME/Cache-Control）。
- `assets/` 走 CDN（hashed 构建产物 base=CDN，不同源直出）。

---

## 6. 平台装配顺序全景（一次请求的生命周期，线上）

```
请求 → cookieParser → legacy-path-redirect → public-assets
     → [Nest Router: setGlobalPrefix(CLIENT_BASE_PATH) 剥前缀 → 匹配 Controller]
     → PlatformModule 中间件矩阵:
         ├ apiResponseInterceptor       /api/*,/openapi/*     (响应包装)
         ├ 上下文链路(用户/请求/日志/可观测/SqlExec)  /*       (datapaas 受 DISABLE_DATAPASS 控制)
         ├ CsrfTokenMiddleware + View + HotUpdate    "*"(exclude api/openapi/static) (种 CSRF cookie+视图)
         └ CsrfMiddleware                            /api/*     (校验双提交,403)
     → GlobalExceptionFilter(全局)  →  GlobalAuthGuard(全局,业务鉴权 401)
     → Controller → Module(业务) → DB
```

---

## 7. 本轮闭环 -> 对历史 bug 的解释

| 历史现象 | 现在可解释为 |
|---|---|
| ERP 登录 401 需先登前台 | globalPrefix=CLIENT_BASE_PATH → 路由带 `/app/xxx`；AuthGuard `startsWith('/api/')` 失配误判需登录(=401)。修复剥前缀对症 |
| "先登前台才能登 ERP"成功 | 前台=页面请求触发 CsrfTokenMiddleware 种 cookie；ERP 直开 cookie 未种/header 读不到 → CSRF 校验失败 |
| CSRF 401/403 疑云 | 双中间件：页面种 cookie(httpOnly:false,partitioned:true)，/api/* 校验 header==cookie；失败 403 |
| `/app/xxx` 前缀 | setGlobalPrefix = CLIENT_BASE_PATH |
| 首次访问 401 刷新恢复 | cookie 需先被页面请求种下 |

---

## 8. 下一步（可选，验证/收尾）

1. **`miaoda deploy history --json` rest 几条** —— 量化发布状态与耗时，收尾"发布慢"。
2. **验证线上 HTML 直出与 CDN**：`curl -I <base>/assets/xxx` 看是否 302 到 CDN。
3. 本项目含 `@lark-apaas/fullstack-nestjs-core` 类型声明时是否也 read 得到——不必，实现只在沙箱 dist。
   - 结论：**平台内核已基本摸清**。可沉淀为"平台架构图"报告，或继续下钻某中间件遗留细节（如 ViewContextMiddleware/legacy CSS）。
4. 后续若线上有 CSRF 相关疑点，直接对照本节（双中间件 + setGlobalPrefix + partitioned cookie）。

> 敏感值不落库。本文件仅含平台代码结构/逻辑，无密钥。