# 接口统一改造 — 批次2（vip / announcement）

> 改造日期：2026-08-29
> 关联任务：`docs/AI金项目-开发执行方案.md` 任务 #5「统一 API 响应格式」批次2
> 前置：批次1（auth/behavior/feedback）已完成

## 一、本批完成内容

### vip（`server/modules/vip/vip.controller.ts`）
原格式 `{ success, code, message, data }`（含 `success` 布尔，属「4 种格式混用」的第 4 种）。
- 全部成功返回 `{success:true, code:0, message, data}` → `ok(data, message)`
- 全部失败返回 `{success:false, code, message, data:null}` → `fail(message, code)`，**保留 401/400/404/-1 语义码**
- 顺带修复：`confirmPayment` 原返回 `{ success: true, data: {...} }` 缺 code/message 字段 → `ok({status, message}, 'OK')`
- `getAvatar` 返回二进制流，非信封，未改动
- 前端 `client/src/api/vip.ts` 解包已按 `code===0` 归一化（`success: result.success === true || code===0`），后端去掉 `success` 后仍走 code 分支，**无需改动**

### announcement（`server/modules/announcement/announcement.controller.ts`）
原格式 `{ success, data }` / `{ success:false, message }`，控制器用 `@Res()` 显式设置 HTTP 状态码。
- `res.json({success:true, data})` → `res.json(ok(data, 'OK'))`
- `res.status(401).json(fail('请先登录', 401))`、`400`、`500` 均保留对应 HTTP 状态码，body 切统一信封
- 前端 `client/src/api/announcement.ts` 的 `announcementRequest` 已兼容 `{code:0, data}`，**无需改动**

## 二、ai 模块择分（降风险）

ai.controller 使用第 3 种格式 `{ success, data } / { success, error }`，且：
- 控制器超 2000 行、端点数量多，含 SSE/流式（不产生信封体）及 `test/auto-test` 等调试接口
- `npm test` 基线中 ai 相关 spec 已有 `PipelineService` 三参签名导致的预存在失败
- 前端 `aiRequest` 已同时兼容 `{success,error}` 与 `{code,message}`，两端当前自洽

因此 ai 不并入本批，单独作为后续小批推进，避免一动即崩。

## 三、验证

- `npm run type:check:server`：通过
- 无专门覆盖 vip/announcement 控制器的单元测试；信封改动为纯结构替换且类型安全
- 遗留（预存在、与本批无关）：`npm test` 中 `ai-governance` / `local-retrieval-flow` 两套件失败（PipelineService 三参签名）

## 四、后续

- ai 成功信封统一（独立小批）
- 批次3：全局异常过滤器失败信封 `{error}` → `{code, message, data:null}`
- 批次4：各模块分页统一 `{items, total, page, pageSize}` + 全量回归