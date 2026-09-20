# 08 — MVP 技术落地与接口契约

> 目的：把 00-06 从"产品设计"压成"程序员可以直接开工"的技术契约。**后端与前端明天早上按照本文档的协议开发，避免互相等、反复改接口、AI agent 猜字段。**
> 适用：P1 明早 MVP 范围。非 MVP 部分仅列接口占位，不展开。
> 关联：表结构权威见 02 文档；流程见 03；图谱见 04；输出见 05；分期见 06。

---

## 一、MVP 表结构总览（最终权威）

| 域 | 表 | 状态 | 说明 |
|---|---|---|---|
| dict_ | dict_industry_category / dict_grade / dict_region / dict_event_category / dict_event_sub_category / dict_inventory_type / dict_tax_status / dict_analysis_type / dict_forecast_model / dict_channel / dict_article_style / dict_entity_alias | MVP 建 | 枚举与别名词典 |
| data_ | data_articles | MVP 建 | 原始文章 + 任务容器（去重键 content_hash + source_name） |
| data_ | data_events | MVP 建 | 事件（E1-E11 + O1-O11 + validity_days/valid_until） |
| data_ | data_daily_price | MVP 建 | 日价（唯一键含 tax_status/unit/origin） |
| data_ | data_weekly_inventory / data_monthly_production / data_quarterly_demand | 仅建表 | 抽取模板 P2 扩展 |
| data_ | data_analysis / data_forecast | 仅建表 | 抽取模板 P2 扩展 |
| data_ | data_content / data_content_citations | MVP 建 | 生成内容产物 + 素材引用 |
| kg_ | kg_entities / kg_relations | MVP 建 | 图谱节点（entity/record 两类）+ 关系（含 nature） |

> SQL 迁移编号从 034 起（⚠️ 2026-08-23 更新：034 被飞书用户绑定占用，实际从 035 起，当前上限 045，新脚本从 046 起），每表独立文件、幂等（IF NOT EXISTS）；部署前验证 gen_random_uuid() 可用。

---

## 二、状态机（两套 + 生成内容一套，写死）

### 2.1 文章状态机（data_articles.status）

```
pending → processing → reviewing → completed / partial / failed / duplicate
```

**聚合函数**（由子记录状态集合确定，不手动维护）：

| 子记录状态集合 | 父任务状态 |
|---|---|
| 全部 confirmed/active | completed |
| 全部 draft | reviewing |
| 存在 confirmed + 其余 draft | reviewing |
| 存在 confirmed + 其余 failed | partial |
| 全部 failed | failed |
| 处理中无子记录 | processing → 全败则 failed |

### 2.2 业务记录状态机（data_events / data_analysis / data_forecast.status）

```
draft → confirmed → archived
非主链：skipped（跳过回队列）/ rejected（放弃，不触发图谱）
```

**数据轨例外（B2）**：data_daily_price 等 4 表 AI 直通 active；仅低置信度/异常转 draft。

### 2.3 生成内容状态机（data_content.status）

```
draft（AI 草稿）→ editing（人工修改中）→ confirmed（定稿）→ archived
```

### 2.4 预测表双状态

```
review_status: draft → confirmed → archived
verification_status: pending（未到期）→ verified（已回填），与 review_status 正交
```

---

## 三、API 清单（MVP，前缀 /api/collect/*）

| 方法 | 路径 | 功能 | 对应文档 |
|---|---|---|---|
| POST | /api/collect/articles | 提交文章（粘贴/上传/URL） | 03 第 1 步 |
| POST | /api/collect/articles/:id/route | 类型路由（AI） | 03 第 3 步 |
| POST | /api/collect/articles/:id/extract | 约束抽取（AI，产 draft 子记录） | 03 第 4 步 |
| POST | /api/collect/records/:id/review | 校核提交（一键全过/提交，带 field_reviewed） | 03 第 5 步 |
| POST | /api/collect/records/:id/skip | 跳过（回队列） | 03 5.2 |
| POST | /api/collect/records/:id/reject | 放弃（永久不处理） | 03 5.2 |
| POST | /api/collect/records/:id/retry | 重新抽取（failed 恢复） | 03 异常 |
| GET | /api/collect/workbench/todos | 待处理队列（首页） | 03 1.1 |
| GET | /api/collect/articles/:id | 文章 + 子记录 + ai_draft 详情 | 03 1.2 |
| POST | /api/collect/records/:id/ai-suggestion | AI 修改建议（历史同类/规则） | 03 5.0.1 |
| GET | /api/kg/search?q= | 实体搜索 | 04 5.3 |
| GET | /api/kg/subgraph?entityId=&depth=&types= | 子图查询 {nodes, edges} | 04 5.3 |
| GET | /api/kg/entity/:id | 实体详情 | 04 5.3 |
| GET | /api/kg/stats | 图谱规模统计 | 04 5.3 |
| POST | /api/content/generate | 生成内容（素材包 → 草稿） | 05 2.4 |
| POST | /api/content/:id/regenerate | 重新生成（版本递增） | 05 2.4 |
| POST | /api/content/:id/finalize | 定稿存档 | 05 2.4 |
| GET | /api/content/:id | 内容详情（含引用标注） | 05 2.1 |

> 所有写接口鉴权走现有 AuthGuard；前端统一走 aiRequest（带 CSRF header，飞书规则见项目 AGENTS.md）。
>
> ⚠️ <!-- 2026-08-23 更新 --> 前后端契约以后端实际返回为准（snake_case）；本文档示例字段若与运行时 API 返回结构不一致，以运行时返回为唯一依据（见 20 号文档踩坑记录）。

---

## 四、AI Router 输入输出（JSON Schema）

### 4.1 类型路由

> **路由全集（与 03 文档第 3 步 8+ 类对齐）**：event（7 大类事件）/ data_price（日价）/ data_inventory（周库）/ data_production（月产）/ data_demand（季需）/ analysis（分析）/ forecast（预测）/ mixed（复合文，多模板同时抽取）/ unknown（无法判定，转人工）。
> **MVP 边界**：路由判定器**全类型可识别并输出**（LLM prompt 覆盖全集），但**业务处理只实现 event / data_price / mixed**（mixed 的 components 仅限 event+data_price 组合）；data_inventory / data_production / data_demand / analysis / forecast 命中后返回"模板未启用"提示（对应表已建，抽取 P2 扩展）；unknown 弹人工选择。

```json
// 输入
{ "title": "太钢1780热轧8月检修15天", "content": "全文…" }

// 输出
{
  "route": "event" | "data_price" | "data_inventory" | "data_production"
        | "data_demand" | "analysis" | "forecast" | "mixed" | "unknown",
  "confidence": 0.93,
  "mixed_components": ["event", "data_price"],  // route=mixed 时必填，MVP 仅支持 event/data_price 组合
  "mvp_supported": true                         // false = 命中未启用模板（MVP 返回提示）
}
```

**MVP 路由判定规则**：
- route ∈ {event, data_price, mixed} 且 confidence ≥ 阈值（默认 0.8，可配置）→ 静默通过
- route ∈ {event, data_price, mixed} 但 confidence < 阈值 → 弹人工确认
- route ∈ {data_inventory, data_production, data_demand, analysis, forecast} → 提示"模板未启用（P2 扩展）"，人工可改判
- route = unknown → 弹人工选择类型

### 4.2 事件抽取（event extractor）

```json
{
  "event": {
    "title": "太钢1780热轧8月检修15天",
    "category": "A",
    "sub_category": "产线检修",
    "event_date": "2026-08-16",
    "related_grades": ["304"],
    "related_regions": ["华东"],
    "subject": "太钢不锈",
    "summary": "太钢1780热轧8月10日起检修15天，影响月产约5万吨。",
    "impact_direction": [{"dimension": "月产", "direction": "下跌"}],
    "impact_level": 4
  },
  "fields_meta": {
    "title":        {"confidence": "high", "nature": "FACT",       "evidence": {"text": "太钢1780热轧8月检修15天", "pos": "title"}},
    "impact_level": {"confidence": "low",  "nature": "INFERENCE",  "evidence": {"text": "预计此次检修将对304供应形成明显影响", "pos": "p3"}}
  }
}
```

**规则**：无证据字段返回 null（禁猜）；推断值必标 INFERENCE + 低置信度；AI 只输出 draft，入库需人工确认。

### 4.3 日价抽取（daily price extractor）

```json
{
  "price": {
    "price_date": "2026-08-16",
    "category": "不锈钢",
    "grade": "304/2B",
    "brand_short_name": "太钢",
    "origin": "太原",
    "region": "华东",
    "market": "无锡市场",
    "spec": "1.0*1219*C",
    "price": 14200,
    "unit": "元/吨",
    "tax_status": "含税"
  },
  "fields_meta": {
    "price":     {"confidence": "high", "nature": "FACT", "evidence": {"text": "无锡304/2B报14200元/吨含税", "pos": "p1"}},
    "price_date": {"confidence": "high", "nature": "FACT", "evidence": {"text": "8月16日", "pos": "p1"}}
  }
}
```

**数值一等公民**：value/unit/tax_status 必须拆分，禁止整串"14200元/吨含税"。

---

## 五、数据结构（Evidence / Confidence / Nature / field_reviewed）

### 5.1 字段级元数据（存 ai_draft JSONB）

```json
{
  "field": "impact_level",
  "value": 4,
  "confidence": "low",
  "nature": "INFERENCE",
  "evidence": {"text": "预计此次检修将对304供应形成明显影响", "pos": "p3"},
  "field_reviewed": "unreviewed"  // unreviewed / confirmed / modified / rejected
}
```

### 5.2 审核判定（组合规则，非评分）

```
Decision = Rule(confidence, nature, field_risk)
field_risk ∈ {normal, core, judgment}
judgment = E10/E11/I1-I4/A13/B13/P5/Q5/R5/P12 → 即使高置信度也硬拦截必须人工
```

前端只呈现三态：🟢 正常 / 🟡 建议确认（core+中置信度）/ 🔴 必须确认（低/INFERENCE/judgment）。

---

## 六、图谱 JSON

### 6.1 节点

```json
{
  "entity_id": "ENT-xxx",
  "name": "太钢",
  "node_category": "entity",           // entity | record
  "entity_type": "factory",            // 实体 12 类 或 业务记录 7 类
  "biz_record_id": null,
  "properties": {"产能": "..."},
  "aliases": ["太原钢铁", "TISCO"],
  "source_ids": ["article:xxx"]
}
```

### 6.2 关系

```json
{
  "relation_id": "REL-xxx",
  "source_entity_id": "ENT-A",
  "target_entity_id": "ENT-B",
  "relation_type": "IMPACTS",
  "nature": "FACT",                    // FACT / OPINION / INFERENCE
  "properties": {"direction": "利多", "magnitude": "+2%", "time": "2026-08-16"},
  "confidence": 0.9,
  "source_ids": ["article:xxx"]
}
```

**约束**：同一对节点同类型关系允许多条（relation_id 唯一）；关系方向规范见 04 文档 3.3。

### 6.3 G6 渲染输入（子图查询返回，直接喂 G6）

```json
{
  "nodes": [
    {"id": "ENT-A", "label": "太钢", "category": "entity", "type": "factory"},
    {"id": "ENT-B", "label": "检修事件", "category": "record", "type": "event"}
  ],
  "edges": [
    {"id": "REL-1", "source": "ENT-A", "target": "ENT-B", "label": "关联", "nature": "FACT"}
  ]
}
```

节点样式按 category/type 区分（实体=方形、业务记录=六边形等），边颜色按 relation_type 区分。

---

## 七、内容生成 API 契约

### 7.1 素材包（生成 API 输入）

```json
{
  "material_pack": {
    "core_fact": "太钢1780热轧8月10日起检修15天",
    "time": "2026-08-16",
    "subject": "太钢不锈",
    "grades": ["304"],
    "impact": {"direction": "利多", "level": 4},
    "prices": [{"market": "无锡", "value": 14200, "unit": "元/吨", "mom_pct": "+0.35%"}],
    "analysis": ["供给收紧，短期价格有支撑（ANA-xxx）"],
    "forecast": null,
    "sources": ["EVT-20260816-001", "DP-20260816-304-WX"]
  },
  "channel": "公众号",
  "style": "深度报道"
}
```

**规则**：素材包只含 confirmed/active 记录；链上缺失的不补造（forecast=null 就不写预测）。

### 7.2 生成输出

```json
{
  "content_id": "CTN-20260817-001",
  "title": "太钢检修：304供给收紧，短期价格有支撑",
  "content": "正文…",
  "citations": [
    {"record_id": "EVT-20260816-001", "record_type": "event", "position": "p1", "evidence": "…"},
    {"record_id": "DP-20260816-304-WX", "record_type": "daily_price", "position": "p2"}
  ],
  "version": 1,
  "status": "draft"
}
```

### 7.3 渠道 × 风格兼容矩阵（校验服务）
<!-- 2026-08-23 更新：下方 4×3 为历史版本，保留不删 -->

| 渠道 | 新闻简讯 | 日评 | 深度报道 |
|---|---|---|---|
| 51号APP | ✅ | ✅ | △ |
| 公众号 | ✅ | ✅ | ✅ |
| 抖音/快手 | ✅ | △ | ❌ |
| 行业群 | ✅ | ❌ | ❌ |
（历史版本，已被扩展）
> ⚠️ **已扩展为 6 渠道 × 6 风格 = 36 格**（新增 AI金客服 / AI金推送渠道 + 周报 / 月报 / 季报风格），详见 20 号文档；逐格取值以前端 `COMPAT_MATRIX` 与后端 `CHANNEL_STYLE_MATRIX` 为准。

---

## 八、错误码与 AI 重试机制

### 8.1 错误码（统一前缀）

| 码 | 含义 | 处理 |
|---|---|---|
| E1001 | 路由判定失败 | 弹人工选择类型 |
| E2001 | 抽取格式错误（JSON 校验失败） | 自动重试（最多 2 次） |
| E2002 | 抽取超时 | 自动重试 → 仍失败标记 failed |
| E2003 | 必填核心字段缺失（按模板门槛） | 提示信息不足，人工决定 |
| E3001 | 审核硬拦截（含低置信度/必填空/判断类未确认） | 提示拦截原因 |
| E4001 | 图谱写入失败（UNIQUE 冲突/节点缺失） | 记录错误日志，子记录已 confirmed 保留 |
| E5001 | 生成素材含非 confirmed 记录 | 拒绝并提示 |
| E5002 | 渠道×风格组合无效 | 拒绝并提示（UI 已置灰，双保险） |

### 8.2 AI 重试机制

```
路由/抽取调用失败 → 指数退避重试（1s/2s/4s，最多 2 次）→ 仍失败标记 failed
failed → 人工可点"重新抽取"（丢弃人工改动重新走 AI）或"手动填表"（draft → 人工确认）
```

---

## 九、P1 开发顺序（前后端可并行）

| 序号 | 任务 | 依赖 | 产出 |
|---|---|---|---|
| 1 | 建表 SQL（034 起 ⚠️ 2026-08-23 更新：实际从 035 起，当前上限 045，新脚本从 046 起）+ schema.ts 合并 | 无 | 数据库就绪 |
| 2 | 字典数据初始化 | 1 | 枚举齐 |
| 3 | 后端：文章提交 + 去重 API | 1 | /articles |
| 4 | 后端：类型路由 + 事件/日价抽取（LLM prompt + JSON 校验） | 1 | route/extract |
| 5 | 后端：校核提交（field_reviewed + 硬拦截 + 聚合函数） | 4 | review/skip/reject |
| 6 | 后端：图谱写入（节点/关系 + nature + UNIQUE） | 5 | 入库自动建图 |
| 7 | 后端：图谱 4 API | 6 | kg 接口 |
| 8 | 后端：内容生成（素材包 + 模板 + 引用标注 + 版本） | 5 | generate API |
| 9 | 前端：工作台三页（首页/处理页/我的记录） | 3-5 | 主流程可操作 |
| 10 | 前端：图谱页（G6 5 功能） | 7 | 图谱可视化 |
| 11 | 前端：内容编辑工作台 | 8 | 生成/修改/定稿 |
| 12 | 明早演示联调（黄金路径 + 金标准测试集跑测） | 全部 | 演示就绪 |

**并行提示**：前端 9 可与后端 6-8 并行（用 mock 数据）；金标准测试集由同事先行填写。

---

## 十、验收关键口径（与 06 P1 一致）

| 指标 | 口径 |
|---|---|
| 关键事实错误率 | 核心字段准确率 ≥95%、普通字段 ≥90%、严重错误率 ≤2%（价格/日期/钢种/主体/正负方向/单位） |
| 黄金路径 | 一篇真实文章：AI 识别 → 结构化 → 人工改 ≤3 处 → 入库 → 图谱 → 生成 3 成品，全程现场演示 |
| 操作量 | 打开记录到提交 ≤3 分钟（不含 AI 等待） |
