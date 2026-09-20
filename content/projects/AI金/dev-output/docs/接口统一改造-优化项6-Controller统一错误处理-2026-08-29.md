# 接口统一改造 · 优化项6 · Controller 层统一错误处理（runAsync）

日期：2026-08-29
范围：后端 Controller 层重复 `try/catch` 模板消除
目标：抽取统一错误封装 `runAsync`，消除 Controller 层「`try { service → ok } catch { log → fail }`」重复代码，语义与 HTTP 状态码、code、message 契约不变。

## 改造前问题

Controller 层大量方法重复同一模板：

```ts
try {
  const data = await this.service.xxx(...)
  return ok(data, '成功文案')
} catch (err) {
  this.logger.error(`xxx失败: 上下文..., err=${(err as Error).message}`)
  return fail((err as Error).message)
}
```

同一段错误处理在 vip.controller 出现 14 次，各处以不同 label 与成功文案复制粘贴。

## 现状盘点结论

- 采用「抽取助手·语义不变（推荐）」策略，不改变 HTTP 状态码与前端契约，低风险。
- **唯一集中且同构的 return-mode 模板**在 `vip.controller.ts`（13 处 `err=` + 1 处 confirmPayment）。
- 其余 Controller 为**异构**模式，不强行纳入本轮（避免过度工程）：
  - announcement/plaza-demand：`@Res()` 模式 + 固定 500 友好文案（语义不同）。
  - plaza：fire-and-forget `.catch()` 记录行为（非错误处理）+ 搜索分支特殊处理。
  - ai：含 SSE/流式 + 既有基线失败，体量大单独推进。

## 改动内容

### 新增 `server/common/utils/error-handler.ts`
- `runAsync<T>({ logger, label, successMessage='OK', failCode=-1 }, fn)` 助手：
  - 成功：`ok(data===undefined ? null : data, successMessage)`（void 结果归一为 `data:null`，与 `ok(null, ...)` 等价）。
  - 失败：`logger.error(label + ', err=' + msg)` + `return fail(msg, failCode)`。
- 参数校验/鉴权前置 guard 仍在 Controller 内用 `return fail(...)` 表达，不进入本助手。

### 重构 `server/modules/vip/vip.controller.ts`
- 14 处重复 try/catch → `runAsync`，逐条保留原语义：
  - 成功 code=0 与对应 successMessage（试用激活成功/订单创建成功/添加成功/移除成功/操作成功/更新成功等）。
  - 失败 failCode：confirmPayment=400，其余 -1；getPurchaseDetail 未命中数据分支保留 `fail('订单不存在', 404)`。
  - confirmPayment 保留 `{status, message}` 结果映射；多步服务用 `.then()` 串联。
  - getAvatar（`@Res()` 二进制输出）不属信封范围，未改。
- 日志文本统一追加 `err=` 前缀（confirmPayment 原无此前缀，现一致化，视为改进）。

## 兼容性分析

- 语义、HTTP 状态码、code、message 前端契约不变，前端零影响，无同步改动。
- 成功 `data` 在 void 返回时归一为 `null`，与改造前 `ok(null,...)` 精确等价。

## 验证结果

- `npm run type:check`（server + client）通过。
- `npm test`：**143 用例全部通过**；2 个失败套件（`ai-governance.service.spec.ts`、`local-retrieval-flow.spec.ts`）为 ai 模块**预存在**的 `PipelineService` 三参签名未更新问题，与本次无关。
- 双 Agent 验证：逐 handler 核验成功码/文案、失败码、data 形状、日志文本、前置 guard 均保真；唯一 note 为 confirmPayment 失败日志多出 `err=` 前缀，属一致性改进。

提交：`90da33b`（新增 error-handler.ts + 重构 vip.controller.ts，100+/107-）

## 后续

- 其他异构 Controller（announcement/ai/plaza 等）待各自重构时按需采用 runAsync，不强转换。