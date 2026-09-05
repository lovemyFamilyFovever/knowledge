---
title: "不锈钢市场使用中心：项目说明"
tags: []
source: "desktop"
source_path: "桌面/AGENTS.md"
collected: "2026-09-06"
status: "imported"
---

# 不锈钢市场使用中心 - 项目说明

> 最后更新：2026-08-18

## 公司与产品概述

- **公司**：我要不锈钢科技无锡有限公司
- **产品**：AI金 · 不锈钢智能伙伴（中后台管理系统）
- **目标用户**：不锈钢市场运营人员、行业分析师、管理人员、贸易商
- **界面语言**：中文
- **技术栈**：Vue 3 + TypeScript + NestJS + Tailwind CSS v4 + PostgreSQL（Drizzle ORM）

### 旗下三大平台

| 平台 | 域名 | 定位 | 盈利模式 |
|------|------|------|---------|
| **51 不锈钢** | 51bxg.com | 信息门户（行情、资讯、数据） | 会员费 |
| **秀吗** | xiuma.com | 交易平台（担保交易、ERP） | 店铺费 + 手续费 |
| **AI 金** | 本项目 | AI 智能配单 + 行业问答 + 测价 | VIP 年费套餐 |

**战略关系**：51 不锈钢 + 秀吗未来作为 AI 金的代理商，为拓展其他固体金属行业做预演。飞书官方背书 + 七折渠道采购，长期可能接入飞书模型体系。

### 关键业务规则

- **三平台账号互通**，统一使用 `MEMBER_CODE`（非手机号）
- **AI 配单成交规则**：点击查看联系方式 = 成交，商品立即下架
- **数据单向通道**：秀吗 ERP 手动导出 → AI金导入，反向链路永远不存在
- **AI 金数据增量产生且永不同步回秀吗**
- **51bxg / 秀吗红线**：源码禁止修改、生产库严格只读、接口报警邮件


## 技术栈

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.5.35 | 核心框架 |
| TypeScript | ^5.9.2 | 类型系统 |
| Vue Router | ^4.6.4 | 路由管理（Hash 模式） |
| Pinia | ^2.3.1 | 状态管理 |
| Tailwind CSS | ^4.1.13 | 样式框架（@theme 语义色） |
| Vite | ^7.3.1 | 构建工具 |
| ECharts + vue-echarts | ~5.6.0 / ^7.0.3 | 图表 |
| Lucide Vue Next | ^0.454.0 | 图标 |
| Axios | ^1.12.2 | HTTP 客户端 |
| Marked | ^18.0.5 | Markdown 渲染 |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| NestJS | ^10.4.20 | 后端框架 |
| Drizzle ORM | 0.44.6 | 数据库 ORM（PostgreSQL） |
| @lark-apaas/fullstack-nestjs-core | — | 飞书妙搭平台集成（仅飞书环境） |
| class-validator | ^0.14.2 | 数据校验 |
| jsdom | ^29.1.1 | WAF 绕过（执行混淆 JS） |
| PostgreSQL | — | 全量业务数据存储 |

### 外部服务

| 服务 | 用途 |
|------|------|
| 51bxg API | 不锈钢行业数据（REST API） |
| xiuma API | 交易平台数据（SOAP WebService） |
| 阿里云百炼 | AI 问答能力（qwen-plus / qwen-turbo） |
| 飞书开放平台 | 用户认证、消息通知 |

---

## 项目结构

```
code/
├── client/                # 前端代码
│   ├── src/
│   │   ├── api/           # API 封装（ai / auth / vip / proxy / trade 等）
│   │   ├── components/    # 组件（ai/ / chat/ / plaza/ / vip/ + AppHeader/Sidebar/Footer）
│   │   ├── composables/   # 组合式函数
│   │   ├── constants/     # 常量（menu 配置等）
│   │   ├── data/          # 静态数据
│   │   ├── layouts/       # 布局（AppLayout / PersonalCenterLayout）
│   │   ├── marketing/     # 营销页（StyleMintPage）
│   │   ├── pages/         # 页面（含 settlement/ / plaza/ / prototype/）
│   │   ├── router/        # 路由（Hash 模式）
│   │   ├── stores/        # Pinia store（auth / vip / feedback）
│   │   ├── styles/        # tailwind.css @theme 语义色 + global.css
│   │   └── utils/         # 工具函数
│   └── index.html
├── server/                # 后端代码（NestJS）
│   ├── common/            # 公共模块（services / filters / guards / utils）
│   ├── database/          # Drizzle ORM Schema + Repository
│   ├── modules/           # 12 个业务模块（见下文）
│   ├── app.module.ts      # 根模块
│   └── main.ts            # 入口
├── shared/                # 共享类型
├── erp/                   # ERP 管理后台（独立路由 /erp/*，独立鉴权）
│   ├── server/            # ERP 后端服务
│   └── 各管理页面/
├── docs/                  # 项目文档
├── scripts/               # 辅助脚本
├── skills/                # Agent Skills
└── .env                   # 环境变量
```

---

## 页面清单

以 `client/src/router/index.ts` 为权威。

### 主应用页面（AppLayout 子路由）

| 页面文件 | 路由 | 标题 |
|---------|------|------|
| AiPartnerPage.vue | `/ai/partner` | AI智能伙伴（首页） |
| AiQaPage.vue | `/ai/qa` | AI 问答 |
| AiPredictPage.vue | `/ai/price` | AI 价格预测 |
| AiStockPage.vue | `/ai/stock` | AI 智能配单 |
| AiSalesPage.vue | `/ai/sales-strategy` | AI 采销策略 |
| AiSalesSmartPage.vue | `/ai/sales-smart` | AI 全自动采销 |
| TokenStatsPage.vue | `/ai/token-stats` | Token 统计 |
| DataApiPage.vue | `/data/api` | 产业数据·联网版 |
| PlazaShellPage.vue | `/promo/plaza` | 智能广场 |
| PlazaPostDetailPage.vue | `/promo/plaza/post/:id` | 广场内容详情 |
| PlazaDemandDetailPage.vue | `/promo/plaza/demand/:id` | 广场供需详情 |
| UserProfilePage.vue | `/user/:memberCode` | 用户主页 |
| EnterpriseBasePage.vue | `/value-added/enterprise-ai` | 企业AI |
| VipMyPackagePage.vue | `/vip/my-package` | 我的套餐 |
| SettlementWorkbench.vue | `/settlement/workbench` | 结算工作台 |
| SalesPipeline.vue | `/settlement/sales-pipeline` | 销售全链路 |
| ContractManage.vue | `/settlement/contract` | 合同管理 |
| PaymentManage.vue | `/settlement/payment` | 收支节点 |
| DeliveryManage.vue | `/settlement/delivery` | 交付核销 |

### 个人中心（PersonalCenterLayout）

| 页面文件 | 路由 | 标题 |
|---------|------|------|
| PersonalProfilePage.vue | `/personal/profile` | 个人资料 |
| PersonalPackagePage.vue | `/personal/package` | 我的套餐 |
| TokenStatsPage.vue | `/personal/token-stats` | 用量统计 |
| PersonalNotificationsPage.vue | `/personal/notifications` | 消息中心 |

### 认证页面（独立路由）

LoginPage / RegisterPage / ForgetPasswordPage（`/account/*`）

### 独立路由页面

| 页面 | 路由 | 说明 |
|------|------|------|
| StyleMintPage | `/style-mint` | 定价套餐落地页（白名单免登录） |
| AgreementPage | `/vip/agreement` | 商用授权协议（白名单） |
| PlazaSharePage | `/share/:newsId` | 广场分享页（白名单） |

### ERP 页面（`/erp/*`，erp_auth_token 鉴权）

| 路由 | 说明 |
|------|------|
| `/erp/vip-admin` | VIP 用户管理 |
| `/erp/package-admin` | 套餐管理 |
| `/erp/order-admin` | 订单管理 |
| `/erp/revenue-report` | 营收报表 |
| `/erp/retention-warning` | 留存分析与流失预警 |
| `/erp/token-stats` | Token 消耗统计 |
| `/erp/api-test` | 接口测试 |
| `/erp/cache-admin` | 缓存管理 |
| `/erp/xiuma-data-import` | 秀吗数据导入 |
| `/erp/error-log` | 错误日志监控 |
| `/erp/operation-log` | 操作日志 |
| `/erp/ai-qa-optimization` | AI 问答测试看板 |

---

## 后端模块

共 12 个业务模块，全部注册在 `server/app.module.ts`。

### AI 模块（`server/modules/ai/`）

| 文件 | 说明 |
|------|------|
| ai.controller.ts | 路由 /api/ai/*（问答 / 配单 / 测价 / 反馈 / 解析 / 导出） |
| bailian.service.ts | 百炼 API 调用（askFastSync / askFastStream / askSync / askStream） |
| forecast.service.ts | AI 测价（SSE 流式 + 8 步思考 + 字段级进度） |
| pipeline.service.ts | 专家模式 Pipeline（百炼 App API + 知识库） |
| feedback.service.ts | AI 反馈服务 |
| ai-batch-test.*.ts | AI 批量测试 |
| ai.openapi.controller.ts | OpenAPI（关键词回填 / 反馈补录） |
| ai-query-policy.ts | 路由决策（4 类策略） |
| price-chart-policy.ts | 图表意图判定 |
| search-source-policy.ts | 联网来源白名单 |
| ai-chart-builder.ts | 结构化图表构建 |
| chat-record.service.ts | 聊天记录持久化 |
| token-record.service.ts | Token 用量统计 |

**AI 问答**：快速模式（qwen-turbo 流式）+ 专家模式（百炼 App API + query-policy 路由）
**AI 配单**：LLM 直通（parse-enquiry-params → score-matches），不使用规则引擎
**AI 测价**：SSE 流式 8 步思考，假进度爬升算法（每 800ms +0.5%，封顶 80%）

### 认证模块（`server/modules/auth/`）

- 路由 /api/auth/*（登录 / 注册 / 改密码 / 短信验证码）
- 51bxg API 验证 + VipService.ensureUser 自动创建/绑定本地账户
- HMAC sessionToken（30 天有效期），写操作使用服务端 MEMBER_CODE
- WAF 绕过服务（waf-bypass.service.ts，@Global）

### VIP 模块（`server/modules/vip/`）

- 路由 /api/vip/*（5 个接口）
- PostgreSQL + Drizzle ORM（VipRepository）
- 8 档套餐（0-7），三层权限：pageAccess / features / exposure_privilege
- 5 分钟缓存，成员变更时清除

### 智能广场模块（`server/modules/plaza/`）

核心社交功能模块，详见下文「智能广场」章节。

### 广场供需模块（`server/modules/plaza/plaza-demand.controller.ts`）

- 路由 /api/plaza/demands/*
- 求购/供应信息 CRUD + AI 智能匹配 + 按品类/材质筛选

### 交易模块（`server/modules/trade/`）

- 路由 /api/trade/*
- 查看联系方式（view-contact）= 成交
- 风控：3 天限看 1 次、成交超时限制
- 表：trade_deal_records / trade_contact_view_logs

### 秀吗数据同步模块（`server/modules/xiuma-sync/`）

- 路由 /api/xiuma-sync/*
- 秀吗 ERP 导出文件上传导入（货品快照 + 会员联系方式）
- 接口清单：
  - `POST /import-product`：货品快照导入（product_info.aspx 导出，38 列中文表头，≤50MB）
  - `POST /import-mappings`：PRODUCT_CODE → PRODUCT_ID 映射导入（数据库只读导出）
  - `POST /import-contacts`：供应商联系方式导入（supplier_info.aspx 导出）
  - `POST /import-member-contacts`：会员联系方式导入（member_contact.aspx，CRM 导出，导入用户表并回填快照表电话）
  - `GET /search`：配单搜索（@Public，读本地快照表，返回与旧 XiumaProductSearchData 兼容结构，并入智能广场"供应挂单" plaza_demands）
  - `GET /list`：管理页分页列表 + 详细筛选（ERP 秀吗数据导入页正文表格）
  - `GET /categories`：有效货品去重分类列表（管理页分类下拉选项）
  - `GET /stats`：快照统计（ERP 导入菜单）
  - `POST /deactivate`：标记指定 productId 失效（成交/下架）
- 表：xiuma_product_snapshot / xiuma_member_contact
- 数据获取唯一方式：秀吗 ERP 后台**手动导出文件 → 页面上传**，禁止数据库直连取数、禁止文件夹定时扫描、禁止调任何外部接口（详见下文「AI 配单数据源」）

### 聊天模块（`server/modules/chat/`）

- 路由 /api/chat/*（会话创建 / 消息发送 / SSE 流 / 关闭）

### 行为模块（`server/modules/behavior/`）

- 路由 /api/behavior/*（onboarding 状态 / 昵称解析 / 提交）

### 代理模块（`server/modules/proxy/`）

- 路由 /api/proxy/*（51bxg / xiuma / 百炼 AI 转发）
- 仅 6 个只读方法，无交易类接口

### 结算模块（`server/modules/settlement/`）

> **⚠️ 由同事开发，本团队只审查不修改。** 站内交易需对接时先与用户确认。

### 其他模块

- **me**：飞书用户信息（仅飞书环境）
- **view**：视图渲染

---

## AI 配单数据源（2026-08-16 改造，重要）

**背景**：51bxg `CustomerData.PostQueryData`（UI_ID=1784553230838779）接口已**彻底禁用**。AI金 配单（AiStockPage、daily-recommend）此前每次实时调用该接口，现**全部改读本地快照表**。

**数据链路（唯一合法，用户明确要求）**：
`秀吗 ERP 后台手动导出文件 → AI金 ERP「秀吗数据导入」页面上传 → xiuma_product_snapshot`
禁止数据库直连取数、禁止文件夹定时扫描、禁止调任何外部接口。

**数据事实**（2026-08-16 实测）：
- 全量上架现货 **3011 条**（与 ERP 后台计数一致）
- product_info.aspx 导出 38 列，**无 PRODUCT_ID**（只有货品编码如 XH2607044327）、**无城市/省份列**（只有仓库名如"无锡臻鼎库"）、**无联系方式**
- 联系方式：ERP_MEMBER_INFO（按 SUPPLIER_ID 关联，原接口 LV.TELEPHONE）或 ERP_SUPPLIER_INFO.TELEPHONE
- 城市/省份：需从 ERP_WAREHOUSE_INFO 关联 ERP_CITY_CODE / ERP_PROVINCE_CODE 补充

**ERP 菜单定位**（ZERP_SYS 库 `USERS_PRIVILEGE_MODULE_DEFINE` 模块表 + `USERS_PRIVILEGE_MODULE_MENU_TREE` 菜单树表）：
- 供应商：`ERP → 基础信息 → 商家信息 → 供应商`（supplier_info.aspx，模块ID **103**）
- 卷板—信息：`ERP → 基础信息 → 产品信息 → 卷板—信息`（product_info.aspx，模块ID **111**）
- 节点链：ERP(57807) → 基础信息(57808) → {商家信息(57814), 产品信息(57809)}

**数据库取数工作方式（用户强要求）**：
- **每次只给一条 SQL**，先 `SELECT COUNT(*)` 确认数量合理再给完整 SELECT 导出（用户原话"下次直接先让我查count"）
- 导出文件用户粘贴到本地 Excel 放桌面，约定文件名：`产品编码对照表.xlsx` / `yonghu.csv` / `仓库城市对照表.xlsx`
- 用户的 SQL 工具对跨库 `库名.dbo.表` 语法报错，需去库前缀直接写 `dbo.表`（当前连接即目标库）
- 遇到不清楚必须问用户，不许自己猜

**关键代码位置**：schema.ts `xiumaProductSnapshot` / `sql/023-create-xiuma-product-snapshot.sql` / `xiuma-product-snapshot.repository.ts` / `server/modules/xiuma-sync/` / `daily-recommend.service.ts` / `client/src/api/proxy.ts queryXiumaProductSearch` / `erp/xiuma-data-import/index.vue` / `docs/AI配单/08-数据源改造与同步方案.md`、`docs/AI配单/09-秀吗数据库取数SQL.md`

---

## 智能广场

智能广场是 AI金的核心社交功能，用户可发布行业动态、分析观点，支持关注/点赞/收藏/评论/分享等完整社交互动。

### 前端页面

| 页面 | 路由 | 说明 |
|------|------|------|
| PlazaShellPage | `/promo/plaza` | 广场主页（信息流 + 发布入口） |
| PlazaPublishPage | `/promo/plaza/publish` | 发布页（AI 模板生成封面） |
| PlazaPostDetailPage | `/promo/plaza/post/:id` | 内容详情 |
| PlazaDemandDetailPage | `/promo/plaza/demand/:id` | 供需详情 |
| PlazaSharePage | `/share/:newsId` | 外部分享页（免登录） |

### 后端接口

| Controller | 路由前缀 | 核心功能 |
|-----------|---------|---------|
| PlazaController | /api/plaza | 帖子列表/搜索/评论/关注/点赞/收藏/浏览历史 |
| PlazaDemandController | /api/plaza/demands | 供需 CRUD/AI 匹配/按材质匹配 |

### 后端服务

| Service | 职责 |
|---------|------|
| PlazaService | 帖子核心逻辑（发布/列表/搜索/互动） |
| PlazaDemandService | 供需信息管理 + AI 智能匹配 |
| PlazaRecommendationService | 个性化推荐（基于用户画像 + 行为） |
| PlazaNotificationService | 互动通知（评论/点赞/关注聚合） |
| PlazaScheduleService | 定时任务（数据聚合/过期清理） |
| PlazaNotificationScheduleService | 通知定时（每周汇总推送） |

### 数据库表（plaza_* 系列）

plaza_posts / plaza_videos / plaza_questions / plaza_likes / plaza_images / plaza_follows / plaza_favorites / plaza_comments / plaza_comment_likes / plaza_notifications / plaza_ai_helpers / plaza_demands

### 前端组件

PlazaRecommendRail / PlazaStrategyCard / PlazaAiPushRail / AiDailySummary / AiDailyContent / OnboardingModal / PlazaProfileHoverCard / AiPushDrawer

---

## 数据库

所有业务数据存储在 **PostgreSQL**，通过 Drizzle ORM 访问。

### 数据库连接

**2026-09-04 起全环境主库切换为阿里云 RDS**（`server/database/index.ts`）：

- 优先级：`DATABASE_URL`（远程 RDS）`||` 回退 `SUDA_DATABASE_URL`（妙搭平台内置库）
- RDS：`pgm-bp1233q7n37by1456o.pg.rds.aliyuncs.com:5432/bxgAI`（公网可达，已实测沙箱/云函数出站可连）；连接串密码含 `@` 必须 URL 转义为 `%40`
- 本地：.env 配 `DATABASE_URL`；飞书发布：**必须在妙搭控制台配置 `DATABASE_URL` 环境变量**（.env 不随发布走），不配则回退平台库
- 平台注入的 `SUDA_DATABASE_URL` 永远存在，但仅在未配 `DATABASE_URL` 时生效
- **副作用**：妙搭数据库管理界面、`miaoda db sql/migration` 仍作用于平台内置库，不再管理业务数据；建表/改表直接对 RDS 执行

**平台 RLS 补丁还原机制（重要）**：平台包 `@lark-apaas/nestjs-datapaas` 在模块加载时对 `drizzle-orm/postgres-js` 的 `PostgresJsPreparedQuery.prototype.execute` 打全局 monkey-patch，每个请求的查询会被包上 `SET LOCAL ROLE 'authenticated_workspace_*'`（妙搭内置库的 RLS 机制，角色名含环境专属 workspace 后缀）。该角色在 RDS 上不存在，导致所有查询报 `role "authenticated_workspace_*" does not exist`。修复：`server/database/index.ts` 在平台模块加载前捕获原始 `execute`，`DatabaseModule.onModuleInit`（及 `getDb()` 首次调用）在配置了 `DATABASE_URL` 时还原原型，抵消补丁。仅回退平台库模式（未配 DATABASE_URL）时补丁保持生效。

DatabaseModule（@Global）通过 `DRIZZLE_DB` token 提供数据库实例，本地和飞书环境通用。

**⚠️ DRIZZLE token 双环境区别**：本地用 `DRIZZLE_DB`（`server/database/database.module.ts` 自定义 Provider）；飞书用 `DRIZZLE_DATABASE`（`@lark-apaas/fullstack-nestjs-core` 平台注入）。代码里 `@Inject` 必须用本环境的 token，Repository 全部走 `@Inject(DRIZZLE_DB)`。

**⚠️ DATABASE_URL 事故记录**：2026-08-16 曾发生 .env 被覆盖为 `192.168.1.64:5432/bxg_app`（内网测试库）导致连接超时、服务端大量报错。同步 .env 后必须检查 DATABASE_URL 主机是否为 `127.0.0.1`。

### 核心数据表（~35 张）

**用户与认证**：users / user_profiles
**VIP 系统**：vip_packages / vip_features / vip_purchase_records / vip_member_relations / vip_operation_logs（operation_logs 为旧名）
**AI 模块**：ai_chat_records / ai_feedbacks / ai_token_records
**智能广场**：plaza_posts / plaza_videos / plaza_questions / plaza_likes / plaza_images / plaza_follows / plaza_favorites / plaza_comments / plaza_comment_likes / plaza_notifications / plaza_ai_helpers / plaza_demands
**交易**：trade_deal_records / trade_contact_view_logs
**秀吗数据**：xiuma_product_snapshot / xiuma_member_contact
**结算**：sales_pipeline_records
**行为**：user_behavior_records / user_recent_views / site_feedback / site_feedback_images / sys_api_error_logs
**运营统计**：platform_daily_stats / frontend_success_daily / frontend_monthly_target / frontend_key_account_daily / frontend_acquisition_daily

### Schema 管理

- `server/database/schema.ts`：**手工维护**（2026-08-18 起，原为妙搭数据面板自动生成）
- **禁止从妙搭后台下载覆盖**：会回退表前缀重命名（见下方「数据库建表与命名规范」）
- 同步妙搭新表时必须手工合并，保留既有物理表名
- 本地 `npm run gen:db-schema` 当前为空占位（`echo ok`），不可用
- 本地新增表通过 SQL 迁移文件管理（`server/database/sql/`）

### 数据库建表与命名规范

> 2026-08-18 制定（sql/033 表前缀规范化迁移），适用于所有新建表与表改名。

#### 表名前缀规范（功能域划分）

新建表必须使用对应功能域前缀：

| 前缀 | 域 | 示例 |
|---|---|---|
| user_ | 用户基础信息与行为 | users、user_profiles、user_behavior_records、user_recent_views |
| vip_ | VIP 套餐/购买/成员/操作审计 | vip_packages、vip_features、vip_purchase_records、vip_member_relations、vip_operation_logs |
| ai_ | AI 问答/反馈/用量 | ai_chat_records、ai_feedbacks、ai_token_records |
| plaza_ | 广场社交 | plaza_posts 等 12 张 |
| trade_ | 站内交易 | trade_deal_records 等 4 张 |
| xiuma_ | 秀吗数据同步 | xiuma_product_snapshot、xiuma_member_contact |
| site_ | 站点反馈 | site_feedback、site_feedback_images |
| sys_ | 系统级日志/配置 | sys_api_error_logs |
| sales_pipeline_ | 结算 | sales_pipeline_records |
| ai_jin_ | 登录认证（历史前缀，例外保留） | ai_jin_auth_credentials、ai_jin_verification_codes |

**例外说明**：

- `users` / `user_profiles`：全项目广泛引用的核心表，保持原名作特例（2026-08 用户确认）。
- `ai_jin_auth_credentials` / `ai_jin_verification_codes`：实际属认证域但已带 ai_jin_ 前缀，经用户确认保持不变；未来新建认证表应优先 sys_ 前缀。
- 孤儿表 `price_baogangdesheng_304_no1` / `price_ningbobaoxin_430_2b` / `price_taigangbuxiu_304_2b`：AI 测价历史遗留、代码零引用，不在规范管理范围，待另行决策。

**本次重命名映射表**（2026-08-18 执行，迁移脚本 `sql/033-rename-table-prefixes.sql`，8 张表）：

| 旧表名 | 新表名 |
|---|---|
| packages | vip_packages |
| features | vip_features |
| purchase_records | vip_purchase_records |
| member_relations | vip_member_relations |
| operation_logs | vip_operation_logs |
| behavior_records | user_behavior_records |
| recent_views | user_recent_views |
| api_error_logs | sys_api_error_logs |

#### 注释规范

- 每张表必须 `COMMENT ON TABLE`，每列必须 `COMMENT ON COLUMN`。
- 枚举字段必须在注释中写明取值范围。

示例：

```sql
CREATE TABLE IF NOT EXISTS vip_operation_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_code TEXT NOT NULL,
  action_type TEXT NOT NULL,
  _created_at TIMESTAMPTZ DEFAULT now(),
  _updated_at TIMESTAMPTZ DEFAULT now(),
  _created_by TEXT,
  _updated_by TEXT
);

COMMENT ON TABLE vip_operation_logs IS 'VIP 操作审计日志';
COMMENT ON COLUMN vip_operation_logs.member_code IS '用户 MEMBER_CODE';
COMMENT ON COLUMN vip_operation_logs.action_type IS '操作类型：GRANT=授予 / REVOKE=回收 / RENEW=续期';
```

#### SQL 脚本规范

- 新建表须在 `server/database/sql/` 下创建独立 `NNN-create-表名.sql`（三位编号续号，当前已到 033，新脚本从 **034** 起，禁止重号）。
- 必须幂等：`CREATE TABLE IF NOT EXISTS`、`CREATE INDEX IF NOT EXISTS`、触发器用 `DROP TRIGGER IF EXISTS` + `CREATE TRIGGER`。
- 飞书环境表必须包含 4 个审计列 `_created_at / _updated_at / _created_by / _updated_by`。
- 表改名时必须同步改名索引/UNIQUE 约束/触发器（主键约束名 `*_pkey` 不随表改名，属 PG 已知行为）。
- 数据插入类脚本已按当前（2026-08-18 表名前缀规范化后）表名书写：002-insert-packages-data 使用 vip_packages / vip_features，028-import-test-account（原 028/032 已合并） 使用 users / ai_jin_auth_credentials，执行前确认目标库表名一致即可，无需再人工替换表名。

#### schema.ts 维护声明

`server/database/schema.ts` 已转为**手工维护**：**禁止从妙搭数据面板下载覆盖**（覆盖会回退表名重命名）；如需同步妙搭新表，必须手工合并并保留既有物理表名。

#### ✅ 飞书发布冻结（已解除，2026-09-01 验证）

sql/033 表前缀迁移已在 online 库执行完成（已实测确认 `vip_packages` 等 8 张新表名存在、旧表名不存在），发布禁令解除。历史背景：迁移前 online 库为旧表名，部署后涉及改名表的接口会 42P01。

---

## 飞书妙搭平台技术细节

### 应用信息

- **应用 ID**：app_4k9x70cg0jws9
- **访问域名**：https://hcnbikrs8vvb.feishuapp.com/app/app_4k9x70cg0jws9
- **平台类型**：妙搭 Spark 全栈应用（@lark-apaas/fullstack-nestjs-core）

### 双数据库机制（dev / online）

| 维度 | 说明 |
|------|------|
| 物理隔离 | dev 和 online 是独立 PostgreSQL 实例，数据不互通 |
| 代码发布 | `miaoda deploy` 部署 git HEAD，代码自动同步 |
| 表结构同步 | `miaoda db migration diff` → `miaoda db migration apply`，**不会自动同步** |
| 数据同步 | **不会自动同步**，需手动 `miaoda db sql < file.sql --env online` |
| 连接串 | `SUDA_DATABASE_URL` 由平台自动注入，无需手动配置 |

### SQL 导入限制

| 限制 | 值 |
|------|------|
| 语句超时 | 30 秒硬限制 |
| 单语句行数 | ≤ 5000 行 / 1 MB |
| SELECT 限制 | 1000 行 |

应对策略：按表拆分、每批 500~1000 条 INSERT。

### OpenAPI 对外接口

| 路由前缀 | 鉴权 | 调用方 |
|---------|------|-------|
| /api/* | 用户登录态（AuthGuard） | 应用前端 |
| /openapi/* | API Key（网关层自动校验） | 第三方系统 |

- /openapi Controller 不需要 @NeedLogin()，user_id 固定为 -1（系统身份）
- 调用方式：`Authorization: Bearer <api_key>` 或 `X-Api-Key: <key>`
- **当前仓库无 openapi controller 实现**（曾有的 `ai.openapi.controller.ts` 已不存在），`docs/openapi.json` 也不存在，`npm run gen:openapi` 是空占位（UNSUPPORTED, SKIP）——要对外暴露接口需自行创建 `*.openapi.controller.ts` 并手动维护 OpenAPI 3.0 文档
- **API Key 获取/轮换**（妙搭 Spark Open API 体系）：`miaoda apps +openapi-key-create --app-id "$app_id"` 创建；密钥**仅创建时一次性可见**，丢失只能 `miaoda apps +openapi-key-reset --app-id "$app_id" --id <key-id> --yes` 轮换（旧密钥立即失效）。用户已有 Key（ID 1872128960518442，名称"数据库"，allow_all: true）
- **飞书 aPaaS Open API 与妙搭 Spark Open API 是两套体系**：aPaaS（低代码平台内置）在「应用管理页 → Open API」创建凭证，用 Client ID/Secret 先换 token；Spark 用 API Key 直接鉴权。本项目是**妙搭 Spark 全栈应用**（依据 @lark-apaas/fullstack-nestjs-core + SUDA_DATABASE_URL），走 Spark 体系
- **spark-v1 API**（open.feishu.cn/open-apis/spark/v1/...，执行 SQL）需要管理员审批权限（spark:app.sql_commands:write），**不可用，放弃该路线**
- **发布后域名**：`https://{随机字符串}.aiforce.cloud/app/{app_id}`（浏览器地址栏可见）；openapi 路径拼在**域名根路径**下：`https://{随机字符串}.aiforce.cloud/openapi/xxx`，不是 `/app/app_xxx/` 下面
- 自建 /openapi 接口（NestJS + Drizzle）不受 aPaaS QPS 限制（aPaaS：通用 40 QPS、单条创建 150、批量创建 10、单次 100 条），瓶颈在 PG 连接池与 FaaS 并发

### 数据库操作规范

- 必须使用 `@Inject(DRIZZLE_DB)` 注入，禁止自建连接
- 新建表必须包含 4 个审计列：`_created_at / _updated_at / _created_by / _updated_by`
- DDL 建议使用 `IF NOT EXISTS`
- 飞书特有 `uuid_generate_v4()` 需转为 `gen_random_uuid()`
- schema.ts 已转**手工维护**，禁止从妙搭后台下载覆盖（详见「数据库建表与命名规范」）

### 妙搭 CLI 常用命令

```bash
miaoda db sql "SELECT count(*) FROM users"              # dev 库执行 SQL
miaoda db sql "SELECT count(*) FROM users" --env online  # online 库执行 SQL
miaoda db sql < file.sql                                 # 导入 SQL 文件（等价控制台编辑器执行）
miaoda db schema list --env online                       # 查看线上表结构
miaoda db migration diff                                 # 查看 DDL 差异
miaoda db migration apply                                # 发布 DDL 到线上
```

**miaoda db sql 细节**：
- 表名**不带 schema 前缀**（写 `vip_packages`，不要写 `public.vip_packages`）
- 多条语句用分号分隔；**不会自动包事务**，需要原子性时手动在首尾加 `BEGIN;` / `COMMIT;`
- 不支持 MySQL 方言（SHOW TABLES / DESCRIBE / 内联 COMMENT），必须用 PG 语法
- DDL 建议 `IF NOT EXISTS`；**新建表必须包含 4 个审计列 + RLS + 默认 policy**（平台要求）
- 大文件建议分批执行避免超时

### 妙搭 PostgreSQL 容量与性能限制（2026-08 平台信息）

| 指标 | 基础免费版 | 商业标准版 |
|------|-----------|-----------|
| 数据存储 | 0.4 GB（约 20 万行） | 0.4 GB + 平台席位×200MB + 应用访问席位×50MB（可增购） |
| 单表最大行数 | 50 万行 | 200 万行（可扩展） |
| 数据查询 QPS | 5 | 200 |
| 数据库 CRUD（云函数/OpenAPI） | 10 万/天 | 100 万/天（可扩展） |
| 云函数运行量 | 1,000/天 | 100 万/天（可扩展） |
| OpenAPI 调用量 | 0 | 线上 100 万/天，沙箱 1 万/天 |

底层为**火山引擎 PostgreSQL Serverless**：非活跃实例自动 Scale-to-Zero；推荐约束 TPS ≤10/分支、QPS ≤20/分支、活跃连接 ≤10/分支、单分支数据量 ≤10GB。

### 数据库管理界面 SQL 鉴权机制（不可复用）

平台 Web 控制台（数据库管理界面）执行 SQL 时前端 Network 看不到 Authorization header，因为**鉴权由平台网关层完成**：浏览器持有 session cookie（suda_*），网关识别身份后注入鉴权转发给数据库服务——这是平台内部通道（innerAPI），**不对外暴露、外部程序无法复用**。外部只能走 miaoda CLI（沙箱）或自建 /openapi 接口。

---

## VIP 权限体系

### 套餐结构

8 档（level 0-7）：免费/试用/入门(3980)/进阶(9800)/专业(19800)/企业(49800)/旗舰(119900)/尊享定制(498000)
共享账号数从 packages 表读取：1/1/3/9/9/9/9/9

### 三层权限

1. **pageAccess** — 页面访问控制
2. **features** — 功能开关
3. **exposure_privilege** — AI 配单/问答中的曝光优先级

### 前端集成

| 文件 | 说明 |
|------|------|
| client/src/api/vip.ts | VIP API 封装 |
| client/src/stores/vip.ts | Pinia store |
| client/src/stores/auth.ts | 登录后 loadPermission |

---

## 色彩系统

Tailwind CSS v4 `@theme` 语义色，定义在 `client/src/styles/tailwind.css`：

| 令牌 | 用途 |
|------|------|
| `--color-brand` | 品牌主色（按钮、链接） |
| `--color-brand-light` | 品牌浅色（hover） |
| `--color-brand-lighter` | 品牌极浅（侧边栏背景） |
| `--color-brand-bg` | 页面/卡片背景 |
| `--color-brand-hover` | 品牌深色（hover） |
| `--color-text-primary` | 正文主色 |
| `--color-text-secondary` | 次要文本 |
| `--color-text-muted` | 弱化文本 |
| `--color-text-dark` | 深色文本（标题） |
| `--color-border` | 边框 |
| `--color-success` | 成功 |
| `--color-warning` | 警告 |
| `--color-danger` | 危险/删除 |

**禁止使用 Tailwind 预设色**（如 `bg-blue-100`），必须使用语义色。

---

## 跨环境同步

### 同步范围

本地和飞书两地同步：**client/、server/、shared/、erp/** 四个目录。

> **同步前必须** `npm run type:check` 确认无 TS 错误。

### 绝对不复制到飞书的文件

package.json、vite.config.ts、tsconfig.*.json、tailwind.config.ts、nest-cli.json、eslint.config.js、.stylelintrc.js、.env、.gitignore、start-local.bat、scripts/、docs/、node_modules/、*.tsbuildinfo、package-lock.json

> 飞书版这些配置含 `@lark-apaas/fullstack-presets` 框架差异，不可覆盖。

### 新增依赖处理

- 不复制 package.json，在飞书终端单独 `npm install`
- 飞书编辑器不能改 package.json（平台保护），用 `npm pkg set` 或 `node -e`

### isLocal 机制

```typescript
const isLocal = !process.env.SUDA_DATABASE_URL;
```

| 环境 | 行为 |
|------|------|
| 本地（isLocal=true） | 跳过 PlatformModule、MeModule；DATABASE_URL 连本地 PG |
| 飞书（isLocal=false） | 加载 PlatformModule；SUDA_DATABASE_URL 自动注入 |

### 文件分类

| 分类 | 内容 |
|------|------|
| 双向同步 | server/modules/、server/common/、client/src/、shared/、erp/ |
| 按环境修改 | .env（SUDA_DATABASE_URL、SERVER_PORT 按环境区分） |
| 本地独有 | .env.local、logs/、.uploads/、.tmp-meeting/ |

### 已废弃文件（禁止使用）

`.env.miaoda`、`server/app.module.miaoda.ts`、`server/main.miaoda.ts`、`client/vite.config.local.ts`、`restart.bat`、`server/modules/erp/`（已迁移到 erp/server/）

---

## 飞书环境 fetch 规则

在飞书环境中前端 `fetch()` 必须遵循以下规则，否则触发 CSRF 403：

| 场景 | 正确做法 |
|------|---------|
| GET 无 body | `fetch(url, { cache: 'no-store' })` — **零 header** |
| POST 有 body | `Content-Type` + `x-suda-csrf-token` — 双 header |
| SSE 流 | `Content-Type` + `x-suda-csrf-token` — 双 header |

**核心规律**：GET 不带 body 就不加任何自定义 header；POST 带 body 必须加 CSRF token。

---

## 开发命令

| 命令 | 说明 |
|------|------|
| `npm run dev:server:win` | 启动后端（Windows，cross-env） |
| `npm run dev:client:win` | 启动前端（Windows） |
| `npm run type:check` | TS 类型检查（前后端） |
| `npx vite build` | 前端构建验证 |
| `npm run build:server` | 后端构建到 dist/server（改动后端后需重建重启） |
| 手工编辑 schema.ts | 已转手工维护，**禁止从妙搭后台下载覆盖**（见「数据库建表与命名规范」） |

**本地后端运行方式（实测）**：`node --enable-source-maps dist/server/main`（构建产物，非 watch）；监听 **`::1:8000`（IPv6 回环）**——PowerShell `Invoke-RestMethod http://127.0.0.1:8000` 连不上属正常，用 `http://localhost:8000` 或 `http://[::1]:8000`。改了 TS 源码后必须 `npm run build:server` 再重启进程才生效。

> PowerShell 不支持 `set NODE_ENV=xxx &&` 语法，必须使用 `cross-env`。Node 版本锁定 22.23.1。

---

## 文档目录

| 目录 | 说明 |
|------|------|
| `docs/项目说明书/` | 项目概览 / 环境配置 / 部署同步 / 踩坑记录 |
| `docs/AI问答系统架构/` | v3.0 query-policy 路由模式 + System Prompt |
| `docs/AI配单/` | LLM 直通架构 + 每日数据导入 SOP |
| `docs/AI测价/` | SSE 流式 + 8 步思考 |
| `docs/VIP系统/` | VIP 权限方案 |
| `docs/结算系统/` | 结算模块文档（同事维护） |
| `docs/团队开发规范.md` | SVN + git 双轨工作流 |

---

## 规则与约束

### 硬约束

#### 运行时
1. npm scripts 必须用 `cross-env`
2. `.env` 不提交；修改后必须重启后端
3. 端口：前端 5173，后端 3000（本地常以 8000 运行）

#### 版本控制
4. `node_modules/`、`dist/`、`*.log` 等不可提交
5. 依赖变更单独 commit
6. 提交前 `npm run type:check`

#### VIP 系统
7. 8 档套餐，共享账号数从 packages 表读取
8. 购买记录必须包含"购买价格（分）"
9. 成员关系表校验引用的购买记录
10. `check-feature` 接口使用 POST

#### 登录与数据
11. 登录独立维护本地账户表，不修改 51bxg 数据库
12. 所有用户 ID 使用 MEMBER_CODE
13. 数据单向通道：秀吗 → AI金，反向永远不存在

#### AI 工具
14. 不自动修改配置文件（package.json / vite.config.ts 等）
15. AI 生成的测试/临时文件不提交

#### 安全
16. API Key 使用环境变量
17. SQL 必须参数化

#### 老平台红线
18. 51bxg / 秀吗源码禁止修改
19. 生产库严格只读（SELECT only）
20. 接口报警邮件 → 减少无谓请求

#### 用户铁律与沟通（全局适用）
21. **绝不删除/清空用户数据文件**（用户担心大模型清空 C 盘的严重事故）；危险操作（删除/格式化/覆盖/剪切）宁停不干，删除前必须备份并确认目标
22. **不用 Plan 模式（/plan）**，确认需求直接提问
23. 对 51/秀吗 数据库取数：**每次只给一条 SQL、先 COUNT、遇到不清楚必须问用户不猜**（见「AI 配单数据源」）
24. **飞书写操作（同步/部署/上传/执行命令）必须事先经用户明确允许**；本地 git commit 按「git 提交规范」可自行判断时机执行（见下）

### 工程约定

- **DTO**：用 interface 而非 class-validator
- **代码搜索**：必须包含 erp/ 目录
- **飞书 fetch**：GET 零 header / POST 双 header（CSRF）
- **ERP 页面**：蓝色主题 `#2f71ff`
- **结算模块**：只审查不修改
- **编码四准则（Karpathy，全局 skill 自动加载）**：①先思考再编码——不确定就停下来问，有多种解读都列出来别偷偷选一个；②简单优先——最少代码解决问题，不写没被要求的功能/一次性抽象/投机配置/不可能场景的错误处理；③外科手术式改动——只改必须改的，不顺手重构，清理只删自己造成的废弃代码，旧代码明显缺陷单独提 issue 不混入本次改动；④目标驱动——加校验写测试、修 bug 先复现、重构保测试、优化写基准
- **git 提交**（用户明确要求，详见 `docs/团队开发规范.md` 与记忆）：每完成一个可独立回滚的阶段（功能点/修复/重构）**自行判断时机执行 commit**，不等用户指示；只提交自己改动的文件，`git add` 逐个列文件**绝不 `git add .`**（工作区常有用户未跟踪文件）；中文详细日志（格式 `type(scope): 主题` + 正文分条）；Windows 下中文提交信息先写 `.git/COMMIT_MSG_TMP.txt` 再 `git commit -F`（直接 -m 会被 shell 吞引号），提交后删除临时文件；中文路径 add 时不加引号；提交前保证 `npm run type:check` 无新增错误；临时脚本/日志不提交、用后删除
- **后端运行方式**：本地统一用 `start-local.bat`（`npm run dev:server` = `nest start --watch` 直接跑 TS 源码，改代码自动重启）；**不要跑 `npm run build:server` 产 dist**（无人使用，纯多余）；改完代码只需 `type:check` + commit

---

## 已知问题与经验

### 飞书环境特有问题

| # | 问题 | 根因 | 修复 |
|---|------|------|------|
| 1 | 侧边栏 403 | fetch 带自定义 header 触发 CSRF | GET 零 header |
| 2 | SSE 进度条不渲染 | ai.ts 缺事件类型分发 | 补全 SSE case |
| 3 | 飞书白屏 | index.html 脚本路径错误 | 统一 `/client/src/main.ts` |
| 4 | AI 返回原始 JSON | 飞书 ai.controller.ts 旧版 | 同步本地版本 |
| 5 | 登录页按钮无反应 | 飞书 auth.ts 缺导出 | 同步文件 |
| 6 | 登录后不跳转 | 冗余 isLoggedIn 检查 | 移除冗余检查 |
| 23 | AI 问答专家模式线上 network error（2026-09-01） | 专家模式 pipeline + 百炼 App 耗时 70~120s，chat SSE 无心跳，飞书网关空闲超时强制断连 | chat-stream.service.ts 补 15s keepalive + pipeline 45s 超时降级直连；本地实测百炼 App API 会 60s 请求超时，此时 error 事件可正常送达前端 |

### 编码/数据问题

| # | 问题 | 修复 |
|---|------|------|
| 7 | Bitable 字段显示 [object Object] | 服务层 normalize |
| 8 | VIP 表用户 ID 不一致 | 统一 MEMBER_CODE |
| 9 | flex + overflow-hidden 阻断滚动 | 使用 min-h-0 |
| 10 | PowerShell 写文件损坏中文 | `-Encoding UTF8` |

### 外部服务问题

| # | 问题 | 修复 |
|---|------|------|
| 11 | 51bxg WAF 拦截 | waf-bypass.service.ts（jsdom 执行混淆 JS） |
| 12 | 51bxg 会话过期 | Cookie TTL 2 小时，过期重新登录 |
| 13 | QueryCoilPriceInfo 产品 ID 30/31/36/37 返回 500 | 51bxg 后端 dtTrend 为 null 未判空（ForecastController.cs:1942/1975/2038）；proxy parseResponse 识别 {"Message":...} 转 {code:-1}，前端检查 trend_data 静默跳过；`KNOWN_FAILING_IDS=[30,31,36,37]` 过滤避免无效请求与报警邮件 |

### 飞书数据库经验

| # | 经验 |
|---|------|
| 14 | dev/online 数据库物理隔离，发布代码不携带数据 |
| 15 | schema.ts 已转手工维护（2026-08），禁止从妙搭后台下载覆盖（会回退表名重命名） |
| 16 | 妙搭 PG 不支持公网直连，本地可用 Navicat 直连本地 PG |
| 17 | SQL 导入 30 秒超时，大批量需分批（500~1000 条/批） |
| 18 | 飞书 `uuid_generate_v4()` 需转为 `gen_random_uuid()` |
| 19 | 飞书 SQL 编辑器建表后 schema.ts 不会即时重新生成（滞后）；表是否存在以 pg_tables 查询为准 |
| 20 | DATABASE_URL 曾被覆盖为 192.168.1.64（内网测试库）导致连接超时；2026-09-04 起 DATABASE_URL 故意指向远程 RDS，此检查改为：主机必须是 `pgm-bp1233q7n37by1456o.pg.rds.aliyuncs.com` 且密码 `@` 已转义为 `%40` |
| 21 | HeidiSQL(MySQL 模式) 导出 PG 备份 1.sql 有 6 类缺陷需修复：`ON ""` 表名丢失、CREATE 间缺分号、UNKNOWN→TEXT[]、MySQL 函数块 DELIMITER、`_binary 0x`→bytea、外键顺序（users 先于 user_profiles） |
| 22 | 本地后端监听 `::1:8000`（IPv6），`127.0.0.1` 连不上属正常，用 `localhost` 或 `[::1]`；跑 dist 产物需先 `npm run build:server` |
