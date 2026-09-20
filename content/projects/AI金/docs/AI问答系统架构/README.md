# AI问答系统架构 — 文档索引

> 最后更新：2026-08-21  
> 当前架构：v3.0 增量版（数据治理 + 结构化回答 + canonical 价格口径 + PostgreSQL 会话同步）

---

## 架构一句话

```
用户提问 → PipelineService（权限治理 + 能力核验 + query-policy）
    → 快速模式 qwen-turbo / 专家模式百炼 Agent 2.0
    → 工具 observation → canonical 数据口径
    → SSE（delta/content + analysis_progress/thinking + chart/metrics/conclusion + done）
    → 前端任务级暂存与稳定排序
    → PostgreSQL（聊天记录 / Token统计 / 反馈）
```

---

## 文档清单

| 文档 | 说明 | 必读 |
|------|------|------|
| [00-工作总览与进度跟踪.md](./00-工作总览与进度跟踪.md) | 项目定位、当前架构、数据库表、路由、任务清单、决策记录 | ⭐ 入门 |
| [01-环境准备与配置指南.md](./01-环境准备与配置指南.md) | 环境要求、.env 配置、启动命令、端口（前端5173 → 后端8000） | ⭐ 上手 |
| [02-百炼平台操作指南.md](./02-百炼平台操作指南.md) | 百炼控制台操作、aijin-qu 配置、联网白名单、路由/图表配合 | 平台操作 |
| [03-现有代码精读指南.md](./03-现有代码精读指南.md) | 全部 AI 模块源码精读、SSE 事件流、共享类型与清洗 | ⭐ 开发 |
| [04-问题诊断与根因分析.md](./04-问题诊断与根因分析.md) | 架构演变史、5步Pipeline为何错、v3.0 演进、经验教训 | 复盘 |
| [05-问答数据保存方案.md](./05-问答数据保存方案.md) | PostgreSQL 聊天记录、结构化展示存储、历史接口与旧数据迁移 | 数据 |
| [06-反馈与Token统计.md](./06-反馈与Token统计.md) | 二级反馈 + Token 用量统计 | 运营 |
| [07-结构化回答与价格数据一致性.md](./07-结构化回答与价格数据一致性.md) | 图表、关键指标、一句话结论、canonical 同源数据 | ⭐ 数据展示 |
| [08-SSE流式协议与前端稳定渲染.md](./08-SSE流式协议与前端稳定渲染.md) | 完整 SSE 字典、乱序处理、任务绑定和稳定展示顺序 | ⭐ 流式链路 |
| [09-数据治理能力核验与内容安全.md](./09-数据治理能力核验与内容安全.md) | INTERNAL/EXTERNAL、能力状态、受限来源和输出过滤 | ⭐ 安全治理 |
| [10-历史记录会话同步与侧边栏交互.md](./10-历史记录会话同步与侧边栏交互.md) | PostgreSQL 历史、懒加载、批量管理与拖拽宽度 | ⭐ 会话体验 |
| [11-总结.md](./11-总结.md) | 技术总结、关键经验、Prompt 版本史、Pipeline 演变 | ⭐ 概览 |

---

## 权威文件

| 文件 | 说明 |
|------|------|
| [bailian-app-system-prompt-v13.md](./bailian-app-system-prompt-v13.md) | Prompt 完整候选稿（文件头当前标记 V12.1，发布前需与百炼控制台核对） |
| [bailian-app-system-prompt-v13_保守Token优化版.md](./bailian-app-system-prompt-v13_保守Token优化版.md) | V13 保守 Token 优化候选稿 |
| [bailian-app-system-prompt-v11.md](./bailian-app-system-prompt-v11.md) | 历史文件名，内容头已演进到 V12.1；不能仅凭文件名判断线上版本 |
| [bailian-app-system-prompt-v8.md](./archive/bailian-app-system-prompt-v8.md) | 历史版本（归档） |
| [bailian-app-system-prompt-v9.md](./archive/bailian-app-system-prompt-v9.md) | 历史版本（归档） |
| [bailian-app-system-prompt-v10.md](./archive/bailian-app-system-prompt-v10.md) | 历史版本（归档） |
| [legacy-v2.3/](./legacy-v2.3/) | v2.3 及更早历史参考（勿实施） |

---

## 关键配置速查

| 配置项 | 值 |
|--------|-----|
| 百炼 App ID（aijin-qu） | `37f9b024dd594c06ae272228a421e03b` |
| 测价 App ID | `edd37112268c4244857ba424fe583ccd` |
| 前端 / 后端端口 | 5173 / 8000 |
| 联网白名单 | gov.cn / cninfo.com.cn / sse.com.cn / szse.cn / hkexnews.hk |
| AI 业务存储 | PostgreSQL（`ai_chat_records / ai_token_records / ai_feedbacks`） |
| 问答页路由 | `/#/ai/qa` |
| 思考显示 | `AI_THINKING_DISPLAY_MODE=brief|original` |
| 历史侧栏宽度 | 200–420px，localStorage 键 `ai-qa-history-sidebar-width` |

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.3 ~ v2.5.5 | 2026-06 | 5步Pipeline（已废弃） |
| v3.0 | 2026-07-20 | 移除本地预处理，百炼直通，System Prompt v8 |
| v3.0+ | 2026-07 | query-policy 路由、结构化图表、合规联网（v9/v10/v11） |
| v3.0+ | 2026-08 | AI 业务数据迁移到 PostgreSQL；历史摘要同步和消息懒加载 |
| v3.0+ | 2026-08 | canonical 图表口径、指标卡、结论卡、结构化消息稳定释放 |
| v3.0+ | 2026-08-21 | 一句话走势结论、过程话术清洗、历史侧栏拖拽宽度；新增 07–10 专题文档 |

---

## 当前新增能力速览

| 能力 | 关键实现 |
|---|---|
| 数据权限治理 | `AiGovernanceService` 根据 VIP feature 区分 INTERNAL / EXTERNAL |
| 数据能力核验 | `DataCapabilityRegistry` 返回 FOUND / NOT_FOUND / NOT_SUPPORTED / PERMISSION_DENIED |
| 价格口径一致性 | 图表、指标、核心数据表、结论共用 canonical series |
| 结构化回答 | 新增 `metrics` 与 `conclusion` SSE，和 `chart` 一并持久化 |
| 流式稳定性 | 任务 ID 绑定、`content` 快照校正、任务级暂存、固定渲染顺序 |
| 思考治理 | 默认简要阶段进度；原版思考仅内部受控开启并经过内容过滤 |
| 会话同步 | PostgreSQL 摘要列表 + 点击会话懒加载消息 + 软删除/重命名/批量删除 |
| 侧边栏体验 | 搜索、批量管理、移动抽屉、桌面端 200–420px 拖拽调宽 |
