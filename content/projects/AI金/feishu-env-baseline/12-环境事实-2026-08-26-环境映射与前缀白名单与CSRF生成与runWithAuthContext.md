# 12 环境事实 —— 环境映射 / PLATFORM_PREFIXES / CSRF token 生成 / runWithAuthContext（2026-08-26）

> 来源：飞书沙箱终端实测（sed/grep 读 core+datapaas dist 最后一组未知细节）。

---

## 1. mapToWindowEnvironment（环境名映射）

```js
function mapToWindowEnvironment(input) {
  const value = (input || "").trim().toLowerCase();
  if (value === "boe") return "staging";
  if (value === "pre") return "gray";
  if (value === "online") return "online";
  return "online";                       // ⭐ 默认 online
}
```
- 把平台环境标识归一：`boe→staging`、`pre→gray`、`online→online`，其余一律 `online`。
- 用于 `FORCE_FRAMEWORK_ENVIRONMENT` / `env` 归一，决定行为分支。

---

## 2. PLATFORM_PREFIXES 完整数组 + stripBasePath（静态直出白名单）

```js
var PLATFORM_PREFIXES = [
  "api/",          // 后端接口
  "openapi/",      // 开放 API
  "__innerapi__/", // 内部接口
  "__runtime__/",  // 运行时
  "static/",       // 静态
  "dev/",          // 开发工具
  "assets/"        // hashed 构建产物：走 CDN(base=CDN)，不在同源重复直出
];
```
- `createPublicAssetsMiddleware` 对命中这些前缀的路径 `next()`（交给 Nest 路由），其余才尝试从 `dist/client` 静态直出。
- `assets/` 特意走 CDN，所以同源不重复 serve 构建产物。
- `stripBasePath(pathname, basePath)`：剥 `/app/xxx` 前缀（或任意 basePath）→ 相对路径（去开头 `/`）。

---

## 3. CsrfTokenMiddleware —— token 生成与 cookie（补全）

```js
resolveCsrfTokenOptions:  { cookieKey: "suda-csrf-token", cookieMaxAge: 1e3*3600*24*30(30天), cookiePath: "/" }
genToken():
  ts = floor(Date.now()/1000)
  randInt64 = BigInt("0x" + randomBytes(8).toString("hex")).toString()
  s = `${randInt64}.${ts}`
  token = sha1(s) 的 hex + "-" + ts        // 形如 <sha1hex>-<ts>
```
- 页面请求种 `suda-csrf-token`（httpOnly:false），值 = `<sha1hex>-<ts>`，30 天。
- 与 05 中 `/api/*` 的 `CsrfMiddleware`（校验 header==cookie）配套成双提交。

---

## 4. runWithAuthContext 定位（datapaas）

- 在 `@lark-apaas/nestjs-datapaas/dist/index.js` 的 **660 行** `function runWithAuthContext`。
- 职责（据 10 推断）：把 `store.preSql`（RLS 的 SET LOCAL/SET ROLE）绑定到当前请求的数据库事务会话执行。
- 实现体本文件可继续 sed 660-700 行取到（非必需）。

---

## ✅ 至此平台运行时核心「完全闭环」确认

附：`mapToWindowEnvironment`/`PLATFORM_PREFIXES`/`stripBasePath`/`genToken`/`runWithAuthContext` 定位 全部摸清。

> 敏感值不落库。