---
title: "deliver-05-mined-material"
tags: []
source: "desktop"
collected: "2026-09-24"
status: "imported"
---

# 成品5 · 深挖素材库（第二轮"再好好挖掘"产出 · 全部带源码/文档出处）

> 用途：简历母版已折叠 A 类强证据项；本文件是**面试防守的弹药库**，按可信度分级。
> 纪律（D7）：A 类=已读生产源码，可直接讲；B 类=设计/方案文档（多标"已实现/已落地"但我未读到对应源码），讲时用"设计并实现"、**面试前补验源码**；C 类=勿写或需纠错。
> 出处路径根：`C:/Users/Administrator/Desktop/code/`

---

## A 类 · 已读生产源码（最强、可深挖、已上简历）

### A1. RAG 质量工程（不止调 API）——本轮最大新增长点
- **自建 11 个正式知识库**（7 md + 4 xlsx）：不锈钢标准与牌号、板管计算与价格折算、库存分析、废钢废料、进出口政策与规则、采购常识、长材及基础行业术语；企业信息库(126KB xlsx)、钢厂物流与包送规则、钢厂名称/简称映射词典、产量与产能(697KB xlsx)。（`docs/AI问答系统架构/知识库建设/正式知识库/`，ls 实证）
- **亲定《知识库整理规范》**：验收标准=单个知识块被独立召回时仍能答全 5 问（对象/结论/适用条件/例外/来源核验）；禁跨块指代；标题含对象+主题（标题即检索词）；参数与其单位/范围/例外不得拆散。（`知识库建设/02-知识库整理规范.md:10-65`）
- **检索词保全**：钢厂简称、旧牌号 `0Cr18Ni9`/`J1-J5`、英文缩写 NPI/MHP/RKEF/HPAL/AOD/LME 一律保留；正式名用于回答、别名用于召回不可互替；**禁止用 AI 常识自造映射**。（`02:70-83`）
- **稳定知识 vs 动态数据分流表**：牌号标准/采购规则/术语→知识库；价格/库存/进出口量→SQL；新闻→资讯；未来价→AI测价。（`02:162-172`）
- **自建 ERP 批测台** `/erp/ai-qa-optimization` + `POST /api/internal/ai-test/run`：仅 expert 模式、单批≤100、并发 1-10、AI 自动初评 + 人工复核、导出 JSON/Excel、批次历史留存。（`知识库建设/05-知识库测试与效果验证.md:59-76`）
- **100 题标准问题库覆盖 15 个一级分类**；明确"不是全都应命中知识库"，**路由正确本身即测试目标**。（`05:28-55`）
- **七类问题诊断分类法**（知识缺失/有知识未召回/召回错误/上下文不完整/召回对但答错/路由错误/时效信息误入长期库），各配"识别证据→修复位置"；固定定位顺序：正式文件→解析挂载→召回→路由→回答，**只有最后一步出错才改 Prompt**。（`05:139-159`）
- **诚实性硬证据**（面试可主动亮）：通过标准明写"项目现有资料没有定义统一的召回分数/Top-K/分段长度/准确率阈值，因此不在本文件编造数值"。（`05:177`）
- 内容深度举例：标准库写明 GB/T 20878-2024 只能解决牌号与成分、不能替代 GB/T 3280-2015 产品标准；国标/美标/日标/欧标只按"近似对应"（06Cr19Ni10↔304↔S30400↔SUS304↔1.4301）。（`正式知识库/不锈钢标准与牌号知识库.md:6-44`）
- 库存分析库沉淀"五问法"（变了什么/集中在哪/为什么/是否可持续/后续关注）+ 口径守卫（无锡样本仓 vs 佛山 vs 两地合计不可混比；社会库存 vs 仓单库存不可混算；只存方法不存某周数值）。（`正式知识库/库存分析知识库.md:5-39`）

### A2. 多模态 OCR 单据识别（qwen-vl-max）——现代化 AI 亮点
- `OcrService` 调 `BailianService.recognizeImage` → 阿里云百炼 DashScope OpenAI 兼容端点，模型 **`qwen-vl-max`**（视觉多模态）。（`server/modules/settlement/ocr.service.ts:137`；`bailian.service.ts:71-73,940-943`）
- 合同抽取字段：contractType/contractNo/partnerName/signDate/amount(不含税)/taxAmount/taxRate/board/paymentTerms/itemsSummary；发票抽取：invoiceType/code/no/date/amount/exclusiveAmount/taxAmount/taxRate/buyer/seller/projectSummary。（`ocr.service.ts:19-62`）
- **防幻觉**：结构化 Prompt 明确"识别不到必须输出 null"。（`ocr.service.ts:71-113`）
- **服务端字段清洗**：金额/日期归一、枚举白名单、8MB 限制、MIME 嗅探、容忍 markdown 围栏的 JSON 抽取。（`ocr.service.ts:116-214`）
- 沉淀**可复用 AI 接入范式**：Prompt 常量 + 百炼调用 + 清洗 + **人工确认后才写库**。（`docs/结算系统/04-AI能力设计.md:154-163`）
- ⚠️ `confidence: 0.9` 是硬编码、非模型返回（`ocr.service.ts:89,112`）——别把它说成"模型置信度"。

### A3. 智能广场个性化推荐 + 低成本用户画像（纯规则、生产代码）
- **请求期不调 LLM、非 ML、非向量**：候选池 400 条（75% 最新 + 25% 热门），评分=画像匹配35+近期行为25+作者偏好10+热度10+时效10+探索5，减去已看/已赞惩罚。（`docs/智能广场/06:38-65`；`server/modules/plaza/plaza-recommendation.service.ts:225-247`）
- **FNV-1a 稳定探索分**：哈希 `memberCode:日期:refreshSeed:newsId` → 刷新可换序、翻页不跳动。（`plaza-recommendation.service.ts:488-501`）
- **多样性贪心重排**：连续同作者 -12、同作者累计 -4/次、连续同钢种 -5，防信息茧房。（`plaza-recommendation.service.ts:300-329`）
- **V2 低成本画像=规则而非模型**（仅 15 活跃用户、训练不可靠）：得分=行为价值 × 时间衰减(半衰期 7/30 天) × 重复抑制(1+ln(viewCount))，指数归一到 0-100；置信度=min(1,(activeDays+2×高意图activeDays)/5)；消费端只用 confidence≥0.4 且 score≥20。（`docs/智能广场/13:246-288`）
- 五维画像（steels/markets/topics/businessIntents）存 JSONB `profile_features`，影子计算 6 小时聚合、旧字段双写兼容、可回滚；代码 `profile-scoring.ts` 已被推荐服务 import（真实）。（`docs/智能广场/13:115-173`；`plaza-recommendation.service.ts:6-10,158-167`）

### A4. 交易风控自动化（cron + 幂等 + 可配置规则）
- `@nestjs/schedule` 每小时：截止前 6h 预警 + 通知买家（幂等键 `dealId-warn`）；超时自动标记 `timeout`、violation_count+1、通知（`dealId-violation`）；≥2 次违约冻结 `viewContact`。（`server/modules/trade/trade-violation.automation.ts:9-62`）
- 阈值来自可配置 `trade_view_rules` 表 + 逐字段缺省回退（`trade.service.ts:69-105`）；业务规则"查看联系方式=绑定 deal + 下架快照"。（`trade.service.ts:49-55,107-111`）

### A5. 通知调度（cron）
- 每天 09:05（Asia/Shanghai）生成上周互动汇总（幂等键防重）；每天 03:20 分批（1000/批循环）清理过期通知。（`server/modules/plaza/plaza-notification-schedule.service.ts:13-33`）

### A6. 结算系统（51 数据真实化部分=真；明细五表=mock）
- **真实**：`sales_pipeline_records` 表（sql/018+081~085 幂等迁移），Drizzle `SalesPipelineRepository`(upsert/findByOwner/deleteByOwner)，JSON 导入 + 服务端直连同步 60s 冷却、300ms 分页、`bxgDegraded` 优雅降级。（`docs/结算系统/01:39-41`；`05:104-147`；`sales-pipeline.service.ts:64-74`）
- **真实**：`DashboardService` 从真实合同+节点+51 行算 KPI/趋势/逾期风险、DB 失败降级；统一结算进度公式（收款/交付/开票 各 1/3）；taxAmount/grossMargin 服务端推导、按 board 税率、priceType 含/不含税。（`dashboard.service.ts:34-174`；`contract.service.ts:49-56,117-131,295-344`）
- ⚠️ **mock**：contracts/partners/payment-nodes/delivery/config 五张明细表经 `MockStoreService` 写 JSON 文件（过渡态，docs 确认"待建"）；contract.service.ts:485-494 残留硬编码 mock 合作方名（华为/腾讯/小米）。**讲法**：51 平台数据已真实化落库、明细表在分批迁移中——别说"全链路已上生产库"。

### A7. Prompt 工程（真实技法，但版本口径要纠）
- 六原则：明确角色 / 结构化 JSON 输出 / Few-shot / 行为约束 / 输出前自校验 / 按 `intent_primary` 动态选约束模板。（`legacy-v2.3/09:16-24`）
- **温度分档**：意图分类/实体抽取/工具选择 0.1，问答生成 0.7，创意 0.9；top_p 0.8、max_tokens 2000。（`09:210-228`）
- 反幻觉输出守卫（无数据须明说未找到、禁猜测）+ 严格 JSON（禁额外文字/Markdown）。（`legacy-v2.3/10:299-326`）
- 业务字典注入：304↔SUS304↔0Cr18Ni9、无锡↔锡↔南方；口语化实体归一：一五→1.5mm、两个厚→2.0mm、四尺→1219mm。（`09:143-158`；`10:108-119`）
- Few-shot 作为**独立知识库挂载**而非塞进 prompt；Bad Case→归因→改 prompt→测试集验证→迭代闭环。（`09:339-369`）
- ⚠️ **纠错**：之前若写过"v8→v13"——文件确实存在 v8~v13 及 `v13_保守Token优化版.md`，但两份 PE 文档自我标注为 legacy、与现行 v2.5.5 不一致，**权威源是 `bailian-app-system-prompt-v5.md`（本次未读）**。简历未写版本号=安全；面试若被问版本，说"迭代了多个版本、并有保守 Token 优化版"即可，别报具体号除非先核对 v5。

---

## B 类 · 设计/方案文档（多标"已实现/已落地"，但我未读到对应源码 → 面试前补验）

- **Token 统计**（`docs/VIP系统/09`）：粒度=每天×用户×功能（问答/测价/配单），upsert 累加调用次数与总/输入/输出/缓存命中/缓存创建 Token；**多协议 usage 适配**（OpenAI 取 prompt/completion_tokens+cached；DashScope App API 取 usage.models[0] 自汇总；TTS 不统计）；**内存 Promise 链写锁**（同 key 串行、异 key 并行、写后即删防泄漏）；forecast 流式加 `stream_options.include_usage` 从 SSE 尾 chunk 提取；8 个 AI 接口统一 `recordTokenUsage()` 异步不阻塞。→ 未读 `token-record.service.ts`，**建议补验**。
- **VIP 多账号席位共享**（`docs/VIP系统/01:433-488`）：主账号按 51bxg 登录名加子账号；校验套餐有效 + active 成员数 < 套餐"最大账号数"（飞书表动态可配、5 分钟缓存）；移除即置 inactive、权限降免费。7 档年费套餐(0~49.8万)，价格以分存储。→ 存储为飞书 Bitable、未见服务端代码。
- **曝光特权**（`docs/VIP系统/03`）：特权=**商品所属企业**的权限而非当前用户；专业版起含 `ai_stock_priority_recommend`；配单方案 A：candidates 补 supplier → 并行 `checkEnterpriseFeature`（二级 Map 缓存 TTL 5min）→ prompt 标 priorityRecommend=true 让 qwen-turbo 打分 +5~10。→ `checkEnterpriseFeature` 标"阶段二已实现"，但 scoreMatches 集成未见源码。
- **AI 日报**（`docs/智能广场/14:49-100`）：`GET /api/ai/daily` 读画像 → 调百炼日报应用 → 解析结构化 JSON(headline/summary/priceInsights/chart/strategies) → 内存缓存 TTL 10min；价格由百炼"数据连接"直查库、代码不取价；失败返回 success:false 不阻塞。→ 标"已落地"，未读 `ai-daily.service.ts`。
- **画像 V1 行为采集**（`docs/智能广场/07:133-192`）：Controller 层拦截问答/配单/测价/点赞/评论/关注（无前端埋点），按需调百炼提炼标签+摘要、失败降级。→ ⚠️ docs/07 含**已废弃的飞书 Bitable 方案**，勿引用该部分。

---

## C 类 · 勿写 / 需谨慎（避免被戳穿）

- **AI 客服 / 飞书机器人**：`docs/项目说明书/12-AI客服方案设计.md`、`13-AI金飞书生态集成战略分析.md` 均为**设计/战略文档**，13 号状态明写"待领导决策"。→ 只能讲"**主导飞书生态集成的可行性分析与方案设计**（早报推送/H5 工作台/机器人三方案 ROI 与工期）"，**绝不能写成"已上线飞书机器人/AI 客服"**。
- **可核实的既有飞书成果**（这些是真的、可讲）：已部署飞书妙搭应用 `app_4k9x70cg0jws9`、已集成 `@lark-apaas/fullstack-nestjs-core`、已实现 `FeishuMessageService`、`/openapi/*` API Key 网关鉴权、PostgreSQL+Drizzle ~35 张表、AuthGuard+HMAC 会话。（`docs/项目说明书/13:34-41`）
- **结算明细五表 = mock**（见 A6 ⚠️）；**OCR confidence 0.9 = 硬编码**（见 A2 ⚠️）。
- **MCP**：用户提过"自研 MCP"，仓库未找到证据 → 仍**不写**，除非他给出路径。

---

## D 类 · 新增"困难/踩坑"行为故事素材（答"解决难题/抗压"用）

- **WAF 逆向真实细节**（比简历更硬）：明确记录"不能简单取 arg1 拼 cookie"，须 jsdom 完整执行混淆 JS 算出 `acw_sc__v2`；jsdom 非真浏览器，若 WAF 升级到浏览器指纹则须换 Playwright。（`docs/项目说明书/05-踩坑记录.md:59-69`）
- **51bxg 登录链路逆向**：必须先带 session GET `login.aspx` 取 WAF cookie(`_d_id`/`acw_tc`/`z_session`)否则 POST 直接 405/500；真实端点是 `/api_web/MBUserLogin/PostLogin` 而非 `General/PostLogin`；`AREA_CODE` 必须传 `"0086"`（传 `"86"` 报错）；按 loginName 缓存 cookie、TTL 2h。（`05:71-81`）
- **飞书平台坑**：网关对 `/api/*`（含 GET）全量校验 CSRF，缺 `x-suda-csrf-token` 即 403；妙搭部署后 `MODULE_NOT_FOUND`（依赖被 prune，须静态 import 或登记 `MIAODA_RUNTIME_ENTRIES`）。（`05:94-95`）
- **SSE 事件契约**：新增 SSE 事件必须同步 `client/src/api/ai.ts` 类型+分发，否则进度条/图表不渲染；已固化 8 类事件契约。（`05:30-45`）
- **iOS Safari 滚动**：父级 overflow-hidden + flex 阻断子滚动容器触摸事件，用 `min-h-0` 替代。（`05:51-53`）
- **跨环境编码坑**：PowerShell `Set-Content` 默认 GBK 写回损坏 UTF-8 中文 → 强制 `-Encoding UTF8`/改 Node；阿里云 RDS 公网不支持 `sslmode=require`。（`05:18-24`）

---

### 折叠状态
- ✅ A1/A2/A3/A4 已折叠进 `resume-master.md` + `resume-master.html`（RAG 质量工程 / 多模态 OCR / 推荐算法 / 交易风控 / VIP 曝光特权 / Token 统计）。
- ⏳ 待定：是否为 A1~A4 各出一张"面试官怎么挖+怎么答"能守卡（deliver-06）；B 类是否安排面试前补验源码。
