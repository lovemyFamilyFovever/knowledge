# 接口统一改造 — 批次1（auth / behavior / feedback）

> 改造日期：2026-08-29
> 关联任务：`docs/AI金项目-开发执行方案.md` 任务 #5「统一 API 响应格式」批次1
> 试点参考：`dev-output/docs/接口统一改造-settlement试点-2026-08-29.md`

## 一、背景与契约

在 settlement 试点确认的统一信封基础上，将 auth、behavior、feedback 三个内部模块的成功/业务失败响应统一到同一契约：

- 成功：`{ code: 0, message, data }`（共享 `ok()`）
- 业务失败（服务层直接返回、非抛异常）：`{ code: 非0, message, data: null }`（共享 `fail()`）
- 字段名统一为 `message`（此前 auth/behavior/feedback 使用 `msg`，属文档所列「4种格式混用」之一）

### 涉及范围界定
- 排除：`proxy.service`/`api/proxy.ts`（第三方 51不锈钢 / 秀吗 透传，按用户约定除外）。
- 服务层内部非 HTTP shape（如 `feishu-auth.service.handleCallback` 的 `{ok, data, msg}`）**不属于** HTTP 信封，不做改动，仅保留 `data` 读取兼容。
- `/api/ai/*` 其余功能接口归批次2；本批仅因 `/api/feedback/submit` 共用 `aiRequest`，为其错误解包增加 `message` 兜底。

## 二、改动的文件

### 后端
- `shared/envelope.ts`：新增失败信封构造函数 `fail(message='请求失败', code=-1)`，返回 `{ code, message, data: null }`。
- `server/modules/auth/auth.service.ts`：`loginFailed`、注册/改密的各校验失败 → `fail()`；`createLoginResult` 成功 → `ok(data,'登录成功')`；改密成功 → `ok(null,'密码修改成功')`。
- `server/modules/feishu-auth/feishu-auth.controller.ts`：`POST /api/auth/feishu/exchange` 三个返回点改用 `ok()/fail()`（属 auth 域 HTTP 信封）。
- `server/modules/behavior/behavior.controller.ts`：onboarding-status / nickname-parse / onboarding 三处成功改用 `ok()`。
- `server/modules/ai/feedback.controller.ts`：`POST /api/feedback/submit` 成功 → `ok({success:true})`、失败 → `fail((err as Error).message)`。
- `server/modules/auth/auth-login.e2e-spec.ts`：断言 `body.msg` → `body.message`；顺带修复该 spec 预存在的编译错误 `jest.clearMocks` → `jest.clearAllMocks`（否则 ts-jest 下套件无法运行，无法验证本批改动）。

### 前端
- `client/src/api/auth.ts`：`fetchAuthApi` / `getAuthApi` 两个解包块 `result.msg` → `result.message`，类型 `{code?, message?, data?}`。
- `client/src/api/behavior.ts`：三处 `json.msg` → `json.message`。
- `client/src/api/ai.ts`：`aiRequest` 错误分支增加 `result.message` 兜底（兼容 `/api/feedback/submit` 等已上线端点的 `message` 信封）。

## 三、验证结果

- `npm run type:check:server`、`npm run type:check:client`：均通过。
- `auth-login.e2e-spec.ts`（内存 Nest App + mock）：5/5 通过（含改后的 `message` 断言）。
- `npm test`（默认 testMatch）：143/143 测试通过。
  - 另有 2 个套件失败：`ai-governance.service.spec.ts`、`local-retrieval-flow.spec.ts`，根因 `PipelineService` 构造由 2 参改为 3 参（新增 `plazaQaRetrievalService`），属**预存在**签名变更遗留问题，与本批改动无关，未触碰。

## 四、后续批次

- 批次2：vip / ai / announcement / xiuma-sync 成功信封统一（含前端 api 封装修正）
- 批次3：全局异常过滤器失败信封 `{error}` → `{code, message, data:null}`
- 批次4：各模块分页统一 `{items, total, page, pageSize}` + 全量 type:check + 全链路回归