# 接口统一改造 · 优化项7 · 补充 any 类型定义（批次2：collect/ai repository）

日期：2026-08-29
范围：`server/database/collect.repository.ts`、`server/database/ai.repository.ts`
目标：继续将生产代码中的 `any` 替换为精确类型，纯类型收紧、运行时行为不变。

## 改动内容

### collect.repository.ts（16 → 11 处）
- 4 个**已知表**检索方法返回 `Promise<any[]>` → 精确 `$inferSelect` 别名：
  - `searchEventsForQa` → `EventRecord[]`（dataEvents）
  - `searchAnalysisForQa` → `AnalysisRecord[]`（dataAnalysis，新增别名）
  - `searchDailyPricesForQa` → `DailyPriceRecord[]`（dataDailyPrice）
  - `searchConfirmedContentForQa` → `ContentRecord[]`（dataContent，新增别名）
  - 唯一消费方 `local-retrieval.service.ts` 读取字段（title/summary/coreConclusion/
    priceDate/category/grade/market/spec/price）全部存在且经 `String()/truncate/?./??` 处理。
- `updateArticleStatus`：移除冗余 `as any`（`extra` 本为 `Partial<inferInsert>`，set 类型自洽）。

### ai.repository.ts（10 → 2 处）
- `conditions: any[]` → `SQL[]`（导入 drizzle 的 `type SQL`；`and(...conditions)` 仍合法）。
- 7 处 raw SQL 结果 `(rows as any[])` → `(rows as Array<Record<string, unknown>>)`：
  读取点全部经 `String()/Number()/真值/三元`，`lastActiveAt` 用 `as string|number|Date` 收口。

## 有意保留的 `any`（语义性/技术性宽松）

- collect.repository：`createSubRecord/updateSubRecord/findSubRecordsByArticleId/
  findRecordWithDraft` 的 `target as any` 与 `Promise<any>` —— 动态子记录表（7 张异构表）外部
  Agent-2 契约；强类型 union 会破坏 batch-process.spec mock 与运行语义，暂不改。
- ai.repository：2 处 `.set(updates as any)` —— 动态构造更新的 Drizzle 类型逃逸。

## 验证结果

- `npm run type:check:server` 通过。
- `npm test`：143 用例通过（batch-process.spec 等全 PASS）；2 个 ai 套件为既有
  PipelineService 三参签名基线失败（预存在，与本次无关）。
- 双 Agent 核查 5 项全 OK：4 检索方法 schema/消费方字段匹配、updateArticleStatus 类型自洽、
  SQL[] 合法、unknown 读取全部显式转换、.set(updates as any) 有意保留；无运行时行为变化。

提交：`1af24b9`（2 文件，17+/15-）

## 后续（优化项7剩余）

- 其余生产文件 any 继续：content.repository(8)、bailian.service(8)、ai.controller(9)、
  daily-recommend.service(5)、import-staging.repository(9) 等。
- collect 动态子记录 / kg 图属性 / UUID inArray / ai 动态 updates 等技术性 `as any` 依
  「语义性宽松」原则保留。