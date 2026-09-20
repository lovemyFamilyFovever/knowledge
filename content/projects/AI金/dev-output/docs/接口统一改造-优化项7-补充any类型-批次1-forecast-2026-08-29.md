# 接口统一改造 · 优化项7 · 补充 any 类型定义（批次1：forecast.service）

日期：2026-08-29
范围：`server/modules/ai/forecast.service.ts`（计划点名的生产代码重点，any 最多）
目标：将生产代码中的 `any` 替换为有意义的类型定义，纯类型收紧、运行时行为不变。

## 现状盘点结论

- 全仓 265 处 any（34 文件），计划按「优先生产代码」推进。
- **生产代码最大 offender 为 `forecast.service.ts`（27 处）**，本轮作为批次1。
- 剩余 any 主要集中于 spec 测试（`as any` 常见，属测试注入）与第三方结构。

## 改动内容

### 新增类型
- `PricePoint`：价格序列单点记录（本地 DB 历史价 / 51bxg 趋势价统一结构）。
  `PriceDate/Pricedate/Date/Name/NAME/Price/Close/Stock` 全可选，兼容多来源读取。
- `UsageInfo`：百炼兼容 API 用量结构（prompt/completion/total_tokens + cached_tokens）。

### any → 具体类型（27 → 9 处）
- `structured`/`priceStructured`：10+ 处 `any[]` → `PricePoint[]`
  （`fetchPriceData` 返回、`formatted.map`、`computeTechIndicators`、`buildChartData`、
  `buildForecastPrompt`、`buildJsonExports`）。
- `fetchInventoryData`：`DATAS as any[]` → `PricePoint[]`（复用 Stock/Name 通用字段）。
- `fetchNewsData`：`DATAS as any[]` → `Array<{ Title, CreateTime }>`（仅读两字段，精确收紧）。
- `lastUsage`、`extractForecastUsage`：`any` → `UsageInfo`；SSE `parsed.usage` 赋值仍合法。
- `catch (e: any)` → `catch (e: unknown)`：日志 `e instanceof Error ? e.message : String(e)`
  （Drizzle 落库只抛真 Error，行为等价）。

### 有意保留的 `any`（9 → 留作后续）
- `ForecastJsonExports` 8 个字段：AI 生成的**任意 JSON** 导出块，精确类型成本高，语义性宽松保留。
- 1 处 `} as any`：`insert(dataForecast).values()` 的 Drizzle 类型逃逸，单独处理。

## 验证结果

- `npm run type:check:server` 通过。
- `npm test`：143 用例通过（`forecast-persist.spec.ts` 通过）；2 个 ai 套件为既有
  PipelineService 三参签名失败，与本次无关。
- 双 Agent 核查 6 项全 OK：接口覆盖全部访问点、返回类型可赋值、usage 一致、catch 日志
  等价（唯一 note 为现实中不可达的非 Error 带 message 对象差异，Drizzle 不会抛）、
  保留的 any 未弱化、无运行时行为变化。

提交：`7aca6d4`（1 文件，43+/23-）

## 后续（优化项7剩余）

- `ForecastJsonExports` 8 字段任意 JSON → 逐块精确类型（如需要可单独批次）。
- 其余生产文件 any（collect.repository 20、kg.repository 12、ai.repository 10、
  import-staging.repository 9、content.repository 8、bailian 8 等）按批次继续。