# 11 环境事实 —— 用户身份头 / 静态资源直出 / configureApp 装配细节（2026-08-26）

> 来源：飞书沙箱终端实测（grep+sed 读 `@lark-apaas/fullstack-nestjs-core/dist/index.js` 关键段）。

---

## 1. 平台用户身份：`suda_web_user` 请求头（关键）

```js
function getWebUserFromHeader(req) {
  const sudaWebUserContent = req.headers[sudaWebUserHeaderKey];  // 头名 suda_web_user
  if (!sudaWebUserContent) return null;                          // 无头 → null（前端未注入则匿名）
  try {
    const obj = JSON.parse(decodeURIComponent(sudaWebUserContent)); // 头内是 URI 编码的 JSON
    return obj;
  } catch (err) { console.error("parse suda webuser from header failed, err=%o", err); return null; }
}
```

`UserContextMiddleware.use()`：
```js
const webUser = getWebUserFromHeader(req);
req.userContext = {
  userId: webUser?.user_id,         // ⭐ 取到的字段
  tenantId: webUser?.tenant_id,
  appId: webUser?.app_id ?? "",
  loginUrl: webUser?.login_url ?? "",
  userType: webUser?.user_type ?? "",
  env: webUser?.env ?? "runtime",
  userName: webUser?.user_name?.zh_cn ?? "",
  userNameEn: webUser?.user_name?.en_us ?? "",
  userNameI18n: webUser?.user_name ?? {},
  isSystemAccount: webUser?.is_system_account ?? false,
  roles: webUser?.roles
};
next();
```

### 📌 关键结论
- **平台/组件的"当前用户"来自请求头 `suda_web_user`**（值 = URI 编码的 JSON），由平台一级网关注入；头缺失 → `req.userContext.userId` 为空（匿名）。
- 这个 `req.userContext` 正是 **RLS（SET ROLE/user_id）** 和业务"当前用户"的数据来源。
- **对「登录/取不到数」**：若前端请求没被平台网关正确注入 `suda_web_user`，平台侧就永远是匿名身份 → RLS 落到 `anon_` 角色 → 查不到业务行。**这是"线上取不到数"的高概率根因之二**（配合 RLS 一环比对）。

---

## 2. 静态资源直出（publicAssetsMiddleware）

- `clientDir = <cwd>/dist/client`，`basePath = CLIENT_BASE_PATH`。
- 逻辑：仅 GET/HEAD；剥前缀；`.html` 跳过；`PLATFORM_PREFIXES` 命中跳过；`path.normalize` 后必须仍在 `clientDir` 内（防路径穿越写出根）；存在才 serve。
- 响应：`ETag`（If-None-Match→304）、`Content-Type`（MIME 表）、`Cache-Control: public, max-age=0, must-revalidate`、HEAD 只回头部，`fs.createReadStream` 流式。
- 即：**构建产物打进 `dist/client`，平台用该中间件直出静态资源**，其余走 Prenest 路由。

### PLATFORM_PREFIXES（部分列出，完整见 36638 定义）—— 平台保留前缀，业务不该占用
（未在此轮截入完整数组，取值如登录/静态/系统相关前缀；业务自定义前缀需避开。）

---

## 3. configureApp 装配顺序（一次性看全，setup.ts）

```js
const DEFAULT_BODY_LIMIT = "1mb";
const defaultPerms = { disableSwagger: false };

async function configureApp(app, perms = defaultPerms) {
  const bodyLimit = perms.bodyLimit ?? process.env.BODY_SIZE_LIMIT ?? DEFAULT_BODY_LIMIT;  // ⭐1mb,可覆盖
  app.useLogger(app.get(AppLogger3));
  app.flushLogs();
  app.use(json({ limit: bodyLimit }));            // ⭐ body 限制 1mb（大文件上传会被拒）
  app.use(urlencoded({ limit: bodyLimit, extended: true }));
  app.use(cookieParser());
  app.use(createLegacyPathRedirectMiddleware());  // legacy 路径重定向
  app.use(createPublicAssetsMiddleware());        // 静态资源直出
  const globalPrefix = process.env.CLIENT_BASE_PATH ?? "";
  app.setGlobalPrefix(globalPrefix);              // ⭐ 全局前缀 = /app/xxx
  app.set("trust proxy", true);
  if (NODE_ENV !== "production" && perms.disableSwagger !== true) {
    await DevToolsV2Module.mount(app, { basePath: CLIENT_BASE_PATH, docsPath: "/api_docs", ... });
  }
  // ……（后续 PlatformModule.forRoot + 中间件注册见 05/06）
}
```

### 📌 完整装配流水（合并 05/06/11）：
```
logger → flushLogs → json(urlencoded) body限制1mb → cookieParser
→ legacy重定向 → 静态资源直出(dist/client) → setGlobalPrefix(/app/xxx)
→ trust proxy → swagger(dev, /api_docs) → [AppViews / view渲染 见06]
```

---

## 4. legacyPathRedirectMiddleware（补全）

- 仅当 basePath 匹配 `/^\/app\/[^/]/` 才生效。
- 对 `LEGACY_ROUTE_PATTERNS` 逐一匹配：取 `appId` + suffix。
- 重写新地址 = `<basePrefix>/<appId><suffix>`；若 suffix 是 `/api/` 或 `/__innerapi__/` → 直接 `req.url` 改写继续；GET → 302 重定向；否则 next。
- 即：兼容旧版「无前缀」路径，迁移到新 `/app/xxx/api/...` 形态。

---

## 5. 待补（本轮截断未取到）

- `mapToWindowEnvironment`（34722 定义）实现体。
- `PLATFORM_PREFIXES` 完整数组（36638）。
- `DEFAULT_BODY_LIMIT` 之后 configureApp 余下段（PlatformModule 挂载细节，见 05/06 已覆盖核心）。
- `runWithAuthContext` 实现（datapaas 的 SQL 会话上下文）。
- `PLATFORM_PREFIXES` 完整数组（36638）。

## 6. 命令可用性
- `miaoda db query --sql`：**当前沙箱不可用**（exit 1，报"db query 不可用"）→ RLS 实测改走「可视化 SQL 编辑器」或 migrate 侧。
- `miaoda deploy history --json`：无输出（空）→ 发布历史暂无缝得，改用 `miaoda deploy history` 普通格式另验。
- `@lark-apaas` 全量 **30 个包**（完整清单见上）。

> 敏感值（suda_web_user 真实内容、连接串）不落库。