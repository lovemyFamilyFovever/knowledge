# 反馈与 Token 统计（PostgreSQL 现行版）

> 最后更新：2026-08-21  
> 历史说明：早期 Bitable 字段与环境变量说明已废弃。

## 一、AI 回答二级反馈

### 1.1 调用链

```text
AiAnswerFeedback.vue
  → POST /api/ai/feedback 或 POST /api/feedback/submit
  → FeedbackService
  → AiRepository
  → PostgreSQL ai_feedbacks
```

### 1.2 功能

- 点赞 / 点踩。
- 反馈标签和补充文本。
- 记录问题、回答、模式、模型、数据来源、页面和客户端信息。
- 同一 `message_id` 再次提交时更新原记录。
- 支持撤回：`DELETE /api/ai/feedback/:messageId`，按当前用户限定删除。

### 1.3 并发与幂等

`FeedbackService` 使用 `messageWrites` 对同一 messageId 的进程内写入串行化；数据库以 `message_id` 唯一键查重并执行 create/update，避免连续点击产生重复反馈。

### 1.4 核心表

权威定义：`server/database/schema.ts` 的 `aiFeedbacks`。

主要字段包括：`session_id / message_id / feedback_type / feedback_tags / feedback_text / question / answer / answer_mode / model_name / data_sources / member_code / feedback_time / submit_status`。

## 二、Token 用量统计

### 2.1 调用链

```text
AI 调用完成
  → TokenRecordService.record()
  → AiRepository.upsertTokenRecord()
  → PostgreSQL ai_token_records
```

### 2.2 分类

| category | 含义 |
|---|---|
| `qa` | AI 问答 |
| `forecast` | AI 测价 |
| `matching` | AI 配单 |
| `plaza-helper` | 智能广场 AI 辅助 |

### 2.3 聚合粒度

按“北京时间日期 + MEMBER_CODE + category”聚合。PostgreSQL 使用 `ON CONFLICT` 原子 upsert，累计：

- 调用次数。
- 总 Token。
- 输入 / 输出 Token。
- 缓存命中 / 缓存创建 Token。
- 最近调用时间。

不再需要 Bitable 时代的应用层写锁和重试队列。

### 2.4 查询接口

| 接口 | 用途 |
|---|---|
| `GET /api/ai/token-stats/my?days=30` | 当前用户近 N 日用量 |
| `GET /api/ai/token-stats/all?startDate=&endDate=` | ERP 管理员统计 |

前台结果包含今日汇总和每日分类；ERP 结果包含总览、用户排行和每日趋势。

### 2.5 数据口径

- 运营和计费分析以 `ai_token_records` 为准。
- `ai_chat_records.token_consumed` 是单条问答附带字段，不应替代聚合表。
- 百炼返回字段缺失时可能记录 0，不能把所有 0 都解释为免费调用。
- `plaza-helper` 已进入总分类统计；当前 ERP 用户明细的固定列主要展示 qa/forecast/matching，扩展页面时需补 plaza-helper 列。

## 三、相关文件

| 文件 | 作用 |
|---|---|
| `server/modules/ai/feedback.service.ts` | 反馈 upsert 与撤回 |
| `server/modules/ai/token-record.service.ts` | Token 记录和汇总 |
| `server/database/ai.repository.ts` | PostgreSQL CRUD/upsert |
| `server/database/schema.ts` | `ai_feedbacks / ai_token_records` Schema |
| `client/src/components/ai/AiAnswerFeedback.vue` | 回答反馈 UI |
| `client/src/pages/TokenStatsPage.vue` | 用户用量统计 |
| `erp/token-stats/index.vue` | ERP Token 看板 |

## 四、验证清单

- 同一 messageId 连续提交反馈只保留一条并更新内容。
- 用户只能撤回自己的反馈。
- 同一天同用户同分类多次调用只累加一行。
- `my` 接口不接受前端冒充其他 memberCode。
- ERP 查询日期过滤使用 `YYYY-MM-DD`。
- `npm run type:check` 通过。
