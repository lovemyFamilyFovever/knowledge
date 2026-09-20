# SSE 流式协议与前端稳定渲染

> 最后更新：2026-08-26
> 核心文件：`ai.controller.ts`（SSE 事件）、`client/src/api/ai.ts`（`forecastPriceStream`）、`client/src/pages/AiPredictPage.vue`（渲染）

## 一、SSE 事件字典（后端）


后端在 `ai.controller.ts` 第 1857-1910 行实现流式端点。响应头：`Content-Type: text/event-stream`、`Cache-Control: no-cache`、`Connection: keep-alive`、`X-Accel-Buffering: no`。

| 事件名 | 说明 | 数据结构 |
|--------|------|----------|
| `start` | 后端开始处理 | `{ type: "start" }` |
| `progress` | 字段级进度推进 | `{ type: "progress", step, detail, progress }` |
| `chunk` | AI token 片段累积 | `{ type: "chunk", content }` |
| `done` | 预测完成 | `{ type: "done", data: ForecastResponse }` |
| `error` | 错误 | `{ type: "error", message }` |
| `keepalive` | 心跳 | `: keepalive <timestamp>`（每 15s） |

**progress.step 值**：

```
fetch_data(10) → compute_indicators(25) → ai_analyzing(35/40) → ai_price_range(48)
→ ai_trend(55) → ai_volatility(62) → ai_support_resistance(70)
→ ai_recommendation(78) → ai_analysis(85) → ai_finalizing(95) → ai_parsing(97) → done(100)
```

## 二、客户端接收（forecastPriceStream）

**技术选型**：`fetch` + `ReadableStream.getReader()`（非 `EventSource`，因需 POST 传 JSON 与鉴权头）。

请求：`POST /api/ai/v1/forecast/stream`，头含 `Content-Type: application/json` + `x-suda-csrf-token` + 用户身份 header。返回 `Response` 由其 `body.getReader()` 读取。

**SSE 解析（`processChunk`）**：

1. 读取 `reader.read()` → `Uint8Array`
2. `TextDecoder.decode(value, { stream: true })` 解码
3. `buffer += text`，按 `\n` 分割，保留末行
4. 跳过空行、注释行（`:` 开头）
5. `data:` 行截取 payload → `JSON.parse` → 按 `parsed.type` 分发回调

**回调映射**：

| 事件 | 回调 |
|------|------|
| `start` | `callbacks.onStart?.()` |
| `progress` | `callbacks.onProgress?.({step, detail, progress})` |
| `chunk` | `callbacks.onChunk?.(content, fullText)` |
| `done` | `callbacks.onDone?.(data)` |
| `error` | `callbacks.onError?.(message)` |

**异常兜底**：

- `done` 且 buffer 有残留 → 再 `processChunk('\n')` 处理最后一条
- 未收到终止事件且未中止 → `onError?.('连接中断，本次生成未完成')`
- 前端中断遗留流：新预测开始时 `streamHandle?.abort()` 中断旧连接

## 三、进度条合并机制

前端用 `waitingProgress`（0-100）驱动进度条，`totalProgressPercent` 为计算属性取整。三套机制取较大值：

| 机制 | 触发 | 规则 |
|------|------|------|
| 假进度爬升 `startFakeProgressCrawl` | 预测开始 | 每 1500ms +0.5%，封顶 80% |
| 后端真实进度 `applyBackendProgress` | progress 事件 | `math.max(假进度, 真实进度)` |
| 最终爬升 `startFinalProgressCrawl` | 后端 ≥85% | 每 1500ms +0.5%，封顶 100% |

后端进度 ≥80% 时清除假进度定时器，≥85% 时启动最终爬升。完成时 `finishThinkingSteps()` 清定时器、全部步骤标 done、`waitingProgress=100`。

## 四、思考步骤渲染

步骤标题 `text-base`（非 text-sm）、描述 `text-sm`（非 text-xs）。状态图标：done 绿环对勾、running `Loader2` 旋转、pending 灰环。running 描述带 `animate-pulse`。步骤完成记录 `duration`（`${elapsedSec}s`）展示耗时。

`markStepDone(idx)` 由 step 值映射到 8 步索引（见 [04-预测算法与多因子模型.md](./04-预测算法与多因子模型.md) 第一节）。

## 五、4 张图表渲染

### 5.1 价格预测走势图（renderChart）

- **X 轴**：从今日（`todayStr`）起，到今日 + 周期天数；不显示更早日期。
- **预测起点**：`predData = [lastHistPrice, ...futurePreds]`（今日价 = 最后历史价）。
- **数据映射**：AI 预测值 `>0` 过滤 → 按比例采样到未来天数；无有效值则调 `generateForwardPredictions()`（OU 过程）生成。
- **样式**：虚线 + diamond 标记 + 橙色 `#d97706` + 面积渐变，`connectNulls: false`。
- **Y 轴**：基于未来预测值 + 最后历史价计算，padding = `max(区间×0.2, 500)`，按 100 取整。

### 5.2 历史价格走势图（renderHistoryChart）

- 绿色 `#2d9e8a` 面积线，`smooth: true`。
- 重大事件 `markPoints`：大涨红、大跌蓝、高点橙、低点绿（旋转 180°），标签截 15 字符。
- X 轴标签间隔：>180 天取 `floor(len/12)`，>90 天取 `floor(len/8)`，否则 auto。

### 5.3 往期预测结果走势图（renderHistoryForecastChart）

- 数据源 `forecastHistoryData`（默认静态 `FORECAST_HISTORY_DATA`，经 `loadForecastHistory()` 动态从后端刷新）。
- 按当前预测周期截取（如近一周只显示近 7 天），`cutoffDate = now - (rangeDays-1)`。
- 靛蓝 `#6366f1` + circle 标记 + 面积渐变。

### 5.4 预测价与真实价价差走势图（renderPriceSpreadChart）

- **价差 = 往期预测结果价格 − 同期历史真实价格**。
- 正数（预测偏高）红 `#ef4444`、负数（偏低）绿 `#22c55e`、零（正确）蓝 `#3b82f6`。
- 正向/负向面积填充 + 主曲线全程连续（`connectNulls: true`，跨零不断线）+ `visualMap` 分段着色。
- tooltip 显示：往期预测结果、历史真实价格、价差、状态。
- 空数据显示占位「暂无价差数据」。

## 六、历史数据懒加载

`ensureForecastHistoryLoaded()` 用共享 Promise 避免重复请求；每次图表渲染前重新拉取最新数据，保证 Excel 更新后刷新页面即同步（对应 `GET /api/ai/forecast-history`）。