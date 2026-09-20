# 内部接口格式统一 —— settlement 试点改造记录

日期：2026-08-29
状态：试点验证通过，铺开留待后续轮次
审查：请醒来后核查本页留痕。

## 一、背景

除第三方接口（51不锈钢 / 秀吗，走 `/api/proxy/*`）外，内部所有接口格式需统一。
现状：后端各模块**成功响应**格式五花八门，而**错误**统一走全局异常过滤器 `{error:{...}}`，成功态没有统一信封，前后端解包契约混乱。

**平台方确认**（source: `feishu-env-baseline/06、07、08`）：飞书 `configureApp` 注册的 `apiResponseInterceptor` 只把 `/api/*` 的 `res.render` 劫持为 404 JSON、防止 API 落到 HTML 视图，**并不会帮业务包裹统一响应**——统一必须由业务层自己做。

**后端现状（改造前）**：

| 模块 | 成功格式 | 失败 |
|---|---|---|
| auth / behavior / feedback / proxy | `{ code, msg, data }`(0/-1) | 全局 error |
| xiuma-sync | `{ code: 0\|-1, msg, data }` | 全局 error |
| vip / settlement | `{ success, code, message, data }` | 全局 error |
| ai | `{ success, error, data }` | 全局 error |
| announcement | `@Res().json({success,data}/{success:false,message})` | 全局 error |
| chat.stream（SSE）/ proxy.proxyImage（图片流） | 特殊响应，豁免统一 | — |
| 全局异常 | — | `{ error:{code,message,details,fieldErrors,timestamp} }` |

## 二、统一契约（目标，铺开时全项目对齐）

- **信封**：成功 `{ code: 0, message, data }`；失败 `{ code: <非0>, message, data: null }`
- **分页 shell**：`{ items: T[], total, page, pageSize }`（settlement 已是此结构，作为全项目标准）
- **载体**：`shared/envelope.ts`（`ApiEnvelope<T>` + `OK_CODE` + `ok()`）

## 三、本轮试点改动（已落地）

1. 新增 `shared/envelope.ts`：统一信封类型与 `ok()` 工厂。
2. `server/modules/settlement/settlement.controller.ts`：`ok()` 移除 `success` 字段，改用共享 `ok()`，38 处调用点全部切换（无残留），更新文件头注释。
3. `client/src/api/settlement.ts`：`fetchSettlementApi` 成功态 `success` 改由 `code===0` 推导（不再读后端 `success`）；**失败分支增强**——非 2xx 时尝试从 body 的 `error.message` / `message` 提取真实错误信息（此前只会显示 `HTTP 500`）。
4. 调用方页面（7 处 import `@/api/settlement`）因 `ApiResponse.success` 语义不变，**零改动**，无回归面。

## 四、实测验证（已跑通）

环境：本地 server `localhost:8000`（`SUDA_DATABASE_URL` 为空 → 本地模式）、登录账号 `13800000000/test1234`。

```http
POST /api/auth/login
  {"loginName":"13800000000","Password":"test1234"}
  → {"code":0,"msg":"登录成功","data":{"MEMBER_CODE":"AIMSXIQIVD73439296","sessionToken":"...",...}}   // auth 模块，本轮未改

GET /api/settlement/dashboard/todo-stats
  → {"code":0,"message":"OK","data":{"pendingApproval":0,"expiringWarning":0,"pendingWriteOff":0}}      ✅ 无 success

GET /api/settlement/partners?page=1&pageSize=3
  → {"code":0,"message":"OK","data":{"items":[...],"total":9,"page":1,"pageSize":3}}                     ✅ 分页 shell 统一
```

类型检查：`npm run type:check`（server+client 均 exit 0）通过。

## 五、铺开计划（后续轮次，待用户确认节奏）

1. 后端各 controller 去掉各自成功包装字段（auth/behavior/vip/ai/announcement/feedback/xiuma/proxy），改用 `shared/envelope.ts` 的 `ok()`。
2. **全局异常过滤器对齐失败信封**：`{error:{...}}` → `{ code, message, data: null }`（保留 ResponseCode/HTTP 映射；SSE / 图片流豁免）。⚠ 此步影响全项目前端错误解包，需同步收敛前端解包层，是铺开中风险最高的一步。
3. 前端统一解包：以 settlement 为样板，把 `proxy.ts / auth.ts / ai.ts / plaza.ts / mobile/api.ts / trade.ts` 收敛为同一套 `ApiResponse` 解包（`success` 由 `code===0` 推导）。
4. 各模块分页返回统一为 `{ items, total, page, pageSize }`。

## 六、留痕与未决

- **未决**：失败信封统一（改全局异常过滤器）是本轮刻意留出的铺开步骤——避免试点即爆炸式影响全项目前端解包。用户可决定下一步节奏（建议沿用"先试点 1 模块再铺开"）。
- **本次改动文件**：`shared/envelope.ts`（新增）、`server/modules/settlement/settlement.controller.ts`、`client/src/api/settlement.ts`、`docs/AI金项目-开发执行方案.md`（#5 进度标注）。