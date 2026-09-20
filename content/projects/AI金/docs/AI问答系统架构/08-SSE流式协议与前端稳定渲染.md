# SSE 流式协议与前端稳定渲染

> 当前实现快照：2026-08-21

## 一、接口与传输

AI 问答入口为 `POST /api/ai/chat`，响应类型为 `text/event-stream`。每个事件使用：

```text
data: {JSON}

```

服务端 `sendEvent()` 会把当前生成任务的 `taskId / conversationId / assistantMessageId` 绑定到事件。前端据此丢弃属于旧任务或其他消息的事件，避免快速切换会话、停止重问时串流。

## 二、事件字典

| 类型 | 主要字段 | 用途 |
|---|---|---|
| `start` | `sessionId` | 建立会话 |
| `analysis_progress` | `stage/status/title/detail/timestamp` | 简要分析进度 |
| `thinking` | `text` | 原版思考过程，仅受控模式发送 |
| `delta` | `text` | 正文增量 |
| `content` | `text` | 清洗后的完整正文快照，用于校正 |
| `chart` | `AiStructuredChart` | 后端结构化图表 |
| `metrics` | `AiMetricCardGroup` | 关键指标卡 |
| `conclusion` | `AiConclusionCard` | 一句话结论卡 |
| `done` | `sessionId/requestId/totalTokens/references/durationMs`；客户端兼容可选 `suggestedQuestions` | 成功终态 |
| `error` | `message` | 失败终态 |

事件顺序不是前端正确性的前提。网络缓冲、模型回调和工具 observation 的到达时间可能不同，前端必须按事件类型合并状态。

## 三、简要进度与原版思考

`AiThinkingDisplayService` 支持两种模式：

| 模式 | 行为 |
|---|---|
| `brief` | 默认；发送 `analysis_progress`，不向前端发送原始 reasoning |
| `original` | 仅内部权限且请求开启时发送 `thinking`；原始内容仍经过治理过滤 |

环境变量：`AI_THINKING_DISPLAY_MODE=brief|original`。ERP 批量测试接口可读取或修改进程内模式：

- `GET /api/internal/ai-test/thinking-display-mode`
- `PUT /api/internal/ai-test/thinking-display-mode`

简要阶段顺序由 `analysis-progress.service.ts` 定义：

```text
identify → data_query → data_organization → chart_generation → answer_generation
```

没有发生的阶段可以省略；失败阶段使用 `status='failed'` 和可读原因。

## 四、任务级暂存

`client/src/composables/useChatSession.ts` 为每次生成创建 `GenerationTask`，结构化内容先进入任务暂存：

- `pendingCharts`
- `pendingMetrics`
- `pendingConclusion`

assistant 消息创建后、每次 `delta/content` 更新后以及 `done` 时都会调用挂载逻辑。这样可以处理“图表先到、正文后到”或“结论后到”等情况，不依赖固定 SSE 顺序。

`content` 是正文快照，只更新文本字段，不替换整个消息对象；否则已经挂载的图表、指标和结论会被覆盖。

## 五、稳定展示顺序

`client/src/utils/structured-message-flow.ts` 把正文拆为：

- `summaryText`：回答开头的简短摘要。
- `bodyText`：摘要后的详细正文。
- `structuredAnchorLength`：固定切分锚点。
- `structuredReleased`：结构化区域是否可以展示。

有图表或指标时，前端通常等待 `conclusion` 到齐再统一释放结构化区域，避免结论卡晚到后插入导致页面跳动。最终固定顺序由 `BotMessage.vue` 决定，不由 SSE 到达顺序决定：

```text
分析进度/思考折叠区
开头摘要
AI 结论
关键指标
图表
详细正文
来源、反馈、追问建议
```

`done` 或失败时会强制释放，兼容没有结论卡的旧响应。

## 六、停止、重问与并发保护

- 每个任务绑定具体会话和 assistant message。
- 停止生成后，迟到事件不得写入新的当前消息。
- 重问或刷新会删除被替换消息对应的服务端记录。
- 前端日志保存实际收到的 SSE 类型和结构化对象 ID，便于判断问题发生在服务端生成、网络接收、状态挂载还是组件渲染。

关键日志：

- `SseEventReceived`
- `SseEventTypesReceived`
- `StructuredMessageLifecycle`
- `StructuredMessageFinalState`
- `StructuredPresentationRenderState`

## 七、服务端终态约束

在 `done` 前必须完成：

1. 合并最终 `toolObservations`。
2. 生成并校验图表。
3. 生成指标卡。
4. 清洗最终正文并必要时发送 `content` 校正。
5. 生成一句话结论。
6. 发送完成进度和 `done`。

`done` 之后不得补发 `chart / metrics / conclusion`。

## 八、前端相关文件

| 文件 | 职责 |
|---|---|
| `client/src/api/ai.ts` | SSE 解码、任务绑定校验、事件分发 |
| `client/src/composables/useChatSession.ts` | 生成任务、消息状态、结构化暂存与挂载 |
| `client/src/utils/structured-message-flow.ts` | 摘要锚点和稳定释放 |
| `client/src/components/ai/BotMessage.vue` | 固定渲染顺序、思考/进度、引用、反馈 |
| `client/src/components/ai/AiConclusionCard.vue` | 一句话结论 |
| `client/src/components/ai/AiMetricCards.vue` | 指标卡 |
| `client/src/components/ai/EChartsBlock.vue` | 结构化图表 |

## 九、排障顺序

1. 后端日志确认是否发送对应 SSE 类型。
2. 浏览器日志确认事件是否收到，任务 ID 是否匹配。
3. 检查 `pending*` 是否挂载到目标 assistant message。
4. 检查 `structuredReleased` 和正文是否为空。
5. 检查 `BotMessage` 的最终渲染判定。

不要只根据页面上“没看到图表”判断后端没生成，也不要通过调整事件发送顺序掩盖前端状态覆盖问题。
