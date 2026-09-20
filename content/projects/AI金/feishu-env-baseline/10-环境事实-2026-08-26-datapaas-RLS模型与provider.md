# 10 环境事实 —— SqlExecutionContextMiddleware 实现体：平台数据库 RLS 安全模型（2026-08-26）

> 来源：飞书沙箱终端实测（sed 读 `@lark-apaas/nestjs-datapaas/dist/index.js` 683-725 实现体 + 800-935 provider）。

---

## 1. SqlExecutionContextMiddleware 完整实现

```js
// dist/index.js 683-723（近似还原）
var SqlExecutionContextMiddleware = class {
  config;                                     // Inject(DATAPAAS_CONFIG)
  constructor(config) { this.config = config; }

  use(req, _res, next) {
    const roleSchema = this.config.roleSchema ?? "";
    const userContext = req.userContext || {};
    const roles = (userContext.roles || []).join(",");      // 自定义角色
    const userId = userContext.userId;
    const isSystemAccount = userContext.isSystemAccount;
    const userType = userContext.userType;

    // ⭐ SQL 会话安全上下文：逐请求注入 PG 事务级 RLS 参数
    const sqls = [
      userId ? `SET LOCAL app.user_id = '${userId}'` : `SET LOCAL app.user_id = ''`,
      isSystemAccount ? `SET LOCAL ROLE 'service_role_${roleSchema}'`
        : userId ? `SET LOCAL ROLE 'authenticated_${roleSchema}'`
        : `SET LOCAL ROLE 'anon_${roleSchema}'`,
      roles ? `SET LOCAL app.role_ids = '${roles}'` : `SET LOCAL app.role_ids = ''`,
      userType ? `SET LOCAL app.user_type = '${userType}'` : `SET LOCAL app.user_type = ''`
    ].filter(Boolean).join(";");

    runWithAuthContext({ preSql: sqls }, () => { next(); });   // 在当前请求的数据库会话执行上述 SET
  }
};
```

### 📌 关键结论（平台数据库 RLS 安全模型）
- **飞书启用 PG Row-Level Security**：每次请求经它注入 `SET LOCAL` 事务级会话参数（`app.user_id` / `app.role_ids` / `app.user_type`）并切换 **`SET ROLE`**（`service_role_` / `authenticated_` / `anon_` + roleSchema）。
- **表若开启 RLS**，其 `POLICY` 会读这些应用会话参数来过滤行——这就是"**同库多租户/权限隔离**"的安全基础。
- 依赖 `runWithAuthContext`（DataPaas 的会话上下文工具）把 preSql 绑定到当前请求的数据库事务。
- `req.userContext`（来自 UserContextMiddleware 的请求头解析）是角色/userId 来源 → **RLS 的 user/role 由请求头的平台会话决定**。

### ⚠️ 对本项目的意义
- 本项目的业务 SQL（含 ERP）都走平台 DB 通道（datapaas）时，会被戴上这套 `SET ROLE / SET LOCAL` 会话。**若 `roleSchema` 未配或 RLS policy 缺失/不匹配，可能出现"查不到数据"或"越权"现象**——ERP/vip-admin 取不到数据可能与此相关（需确认 datasource 是否走 datapaas 而非直连库）。这是本轮对"取不到数"最有价值的线索之一。

---

## 2. DataPaasModule provider 注册（forRoot / forRootAsync）

### 统一 provider 集（两份路径共用）
| provider | token | 方式 | 说明 |
|---|---|---|---|
| `DATAPAAS_CONFIG` | 配置 | useValue | 连接信息 + roleSchema + 连接池参数 |
| `DrizzleDatabaseManager` | 类 | useClass | Drizzle DB 管理器（连接生命周期） |
| `DataPaasDatabaseService` | 类 | useClass | 数据访问服务 |
| `SqlExecutionContextMiddleware` | 类 | useClass | RLS 会话上下文（上文实现） |
| `DRIZZLE_DATABASE` | 库实例 | useFactory | 获管理器 DB，返回**Proxy 代理**绑定 this |

`DRIZZLE_DATABASE` 用 `new Proxy` 包住 manager 的 getter，把 DB 方法就地 bind 到连接实例——即业务拿到的 drizzle db 是**动态代理**（延迟取当前管理器连接）。这与**边缘函数/多租户**场景相关。

### forRoot（同步）与 forRootAsync（异步）差异
- `forRootAsync` 新增 `imports: options.imports` 异步获取配置（典型：`ConfigModule` -> `get('DATABASE_URL')`）——**本项目 app.module 用 `PlatformModule.forRoot()`，内部很可能 `forRootAsync` 注入 `DATABASE_URL`**。
- 两者导出集完全一致（Manager/Service/Middleware/DRIZZLE_DATABASE/CONFIG），`global:true`。

### 详细 config 字段
```js
const config = {
  connectionString: options.connectionString,       // 连接串
  schema: options.schema,
  logger: options.logger || false,
  timeout: options.timeout || 1e4,                  // 10s SQL 超时
  maxConnections: options.maxConnections || 1,
  idleTimeout: options.idleTimeout || 20,
  connectionTimeout: options.connectionTimeout || 10,
  ssl: options.ssl || (sslModeRequired ? "require" : false),   // ⭐ ssl 必填（require）
  autoContext: options.autoContext == null ? true : !!options.autoContext,
  roleSchema,                                       // ⭐ RLS 角色 schema 后缀
  connectionTokenFilePath: options.connectionTokenFilePath
};
```
- `ssl` 默认 `require`（线上必 TLS）；`roleSchema` 决定 RLS 角色后缀。

---

## 3. 导出面（index）
- 导出：`DataPaasModule`（778 定义，994 装饰），及其 Drizzle DB 系列 token。
- 多行 export 语句（1192-1200 区域）。

---

## 4. 与平台整体关系（更新装配全景）

```
DataPaas 链接口 = PlatformModule.forRoot()
  → DataPaasModule.forRootAsync (DATABASE_URL, roleSchema)
      DRIZZLE_DATABASE 代理懒连
      SqlExecutionContextMiddleware 注入 RLS SET ROLE / SET LOCAL app.*
Request → UserContext(web 用户头) → req.userContext
        → SqlExecutionContext(读 userContext → 组装 RLS SQL → 当前 DB 会话 SET)
        → 业务 Controller 经 drizzle DB 查询 → 表 RLS POLICY 按会话过滤行 → 返回
```

---

## 5. 下一步（可选）

- 确认 `roleSchema` / RLS：查飞书 DB 中某业务表是否开启 `row_security`（`SELECT relname, relrowsecurity FROM pg_class WHERE relrowsecurity`）→ 佐证"查不到数=RLS 过滤"。
- 对本项目：**确认业务数据源走 datapaas（drizzle）还是直连 'pg' 驱动** → 若是直连直连，则 RLS 不适用；若走 datapaas，则 RLS 是"取不到数"的高概率根因之一。

> 敏感值（连接串等）不落库。