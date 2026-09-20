# 不锈钢市场使用中心 - 项目说明

> 最后更新：2026-09-04

## 公司与产品概述

- **公司**：我要不锈钢科技无锡有限公司

- **产品**：AI金 · 不锈钢智能伙伴（中后台管理系统）

- **目标用户**：不锈钢市场运营人员、行业分析师、管理人员、贸易商

- **界面语言**：中文

- **技术栈**：Vue 3 + TypeScript + NestJS + Tailwind CSS v4 + PostgreSQL（Drizzle ORM）

### 旗下三大平台

| 平台         | 域名        | 定位                  | 盈利模式      |
| ---------- | --------- | ------------------- | --------- |
| **51 不锈钢** | 51bxg.com | 信息门户（行情、资讯、数据）      | 会员费       |
| **秀吗**     | xiuma.com | 交易平台（担保交易、ERP）      | 店铺费 + 手续费 |
| **AI 金**   | 本项目       | AI 智能配单 + 行业问答 + 测价 | VIP 年费套餐  |

**战略关系**：51 不锈钢 + 秀吗未来作为 AI 金的代理商，为拓展其他固体金属行业做预演。飞书官方背书 + 七折渠道采购，长期可能接入飞书模型体系。

### 关键业务规则

- **三平台账号互通**，统一使用 `MEMBER_CODE`（非手机号）

- **AI 配单成交规则**：点击查看联系方式 = 成交，商品立即下架

- **数据单向通道**：秀吗 ERP 手动导出 → AI金导入，反向链路永远不存在

- **AI 金数据增量产生且永不同步回秀吗**

- **51bxg / 秀吗红线**：源码禁止修改、生产库严格只读、接口报警邮件

## 技术栈

### 前端

| 技术                    | 版本               | 用途               |
| --------------------- | ---------------- | ---------------- |
| Vue 3                 | ^3.5.35          | 核心框架             |
| TypeScript            | ^5.9.2           | 类型系统             |
| Vue Router            | ^4.6.4           | 路由管理（Hash 模式）    |
| Pinia                 | ^2.3.1           | 状态管理             |
| Tailwind CSS          | ^4.1.13          | 样式框架（@theme 语义色） |
| Vite                  | ^7.3.1           | 构建工具             |
| ECharts + vue-echarts | \~5.6.0 / ^7.0.3 | 图表               |
| Lucide Vue Next       | ^0.454.0         | 图标               |
| Axios                 | ^1.12.2          | HTTP 客户端         |
| Marked                | ^18.0.5          | Markdown 渲染      |

### 后端

| 技术                                | 版本       | 用途                  |
| --------------------------------- | -------- | ------------------- |
| NestJS                            | ^10.4.20 | 后端框架                |
| Drizzle ORM                       | 0.44.6   | 数据库 ORM（PostgreSQL） |
| @lark-apaas/fullstack-nestjs-core | —        | 飞书妙搭平台集成（仅飞书环境）     |
| class-validator                   | ^0.14.2  | 数据校验                |
| jsdom                             | ^29.1.1  | WAF 绕过（执行混淆 JS）     |
| PostgreSQL                        | —        | 全量业务数据存储            |

### 外部服务

| 服务        | 用途                              |
| --------- | ------------------------------- |
| 51bxg API | 不锈钢行业数据（REST API）               |
| xiuma API | 交易平台数据（SOAP WebService）         |
| 阿里云百炼     | AI 问答能力（qwen-plus / qwen-turbo） |
| 飞书开放平台    | 用户认证、消息通知                       |

***

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

***

## 页面清单

以 `client/src/router/index.ts` 为权威。

### 主应用页面（AppLayout 子路由）

| 页面文件                      | 路由                           | 标题                          |
| ------------------------- | ---------------------------- | --------------------------- |
| AiPartnerPage.vue         | `/ai/partner`                | AI智能伙伴（首页）                  |
| AiQaPage.vue              | `/ai/qa`                     | AI 问答                       |
| AiPredictPage.vue         | `/ai/price`                  | AI 价格预测                     |
| AiStockPage.vue           | `/ai/stock`                  | AI 智能配单                     |
| AiSalesPage.vue           | `/ai/sales-strategy`         | AI 采销策略                     |
| AiSalesSmartPage.vue      | `/ai/sales-smart`            | AI 全自动采销                    |
| TokenStatsPage.vue        | `/ai/token-stats`            | Token 统计                    |
| DataApiPage.vue           | `/data/api`                  | 产业数据·联网版                    |
| PlazaShellPage.vue        | `/promo/plaza`               | 智能广场                        |
| PlazaPostDetailPage.vue   | `/promo/plaza/post/:id`      | 广场内容详情                      |
| PlazaDemandDetailPage.vue | `/promo/plaza/demand/:id`    | 广场供需详情                      |
| UserProfilePage.vue       | `/user/:memberCode`          | 用户主页                        |
| EnterpriseBasePage.vue    | `/value-added/enterprise-ai` | 企业AI                        |
| VipMyPackagePage.vue      | `/vip/my-package`            | 我的套餐                        |
| SettlementWorkbench.vue   | `/settlement/workbench`      | 结算工作台                       |
| SalesPipeline.vue         | `/settlement/sales-pipeline` | 采销全链路（四阶段就地操作，含收款/付款/交付/开票） |
| ContractManage.vue        | `/settlement/contract`       | 合同管理                        |

### 个人中心（PersonalCenterLayout）

| 页面文件                          | 路由                        | 标题   |
| ----------------------------- | ------------------------- | ---- |
| PersonalProfilePage.vue       | `/personal/profile`       | 个人资料 |
| PersonalPackagePage.vue       | `/personal/package`       | 我的套餐 |
| TokenStatsPage.vue            | `/personal/token-stats`   | 用量统计 |
| PersonalNotificationsPage.vue | `/personal/notifications` | 消息中心 |

### 认证页面（独立路由）

LoginPage / RegisterPage / ForgetPasswordPage（`/account/*`）

### 独立路由页面

| 页面             | 路由               | 说明              |
| -------------- | ---------------- | --------------- |
| StyleMintPage  | `/style-mint`    | 定价套餐落地页（白名单免登录） |
| AgreementPage  | `/vip/agreement` | 商用授权协议（白名单）     |
| PlazaSharePage | `/share/:newsId` | 广场分享页（白名单）      |

### ERP 页面（`/erp/*`，erp\_auth\_token 鉴权）

| 路由                        | 说明         |
| ------------------------- | ---------- |
| `/erp/vip-admin`          | VIP 用户管理   |
| `/erp/package-admin`      | 套餐管理       |
| `/erp/order-admin`        | 订单管理       |
| `/erp/revenue-report`     | 营收报表       |
| `/erp/retention-warning`  | 留存分析与流失预警  |
| `/erp/token-stats`        | Token 消耗统计 |
| `/erp/api-test`           | 接口测试       |
| `/erp/cache-admin`        | 缓存管理       |
| `/erp/xiuma-data-import`  | 秀吗数据导入     |
| `/erp/error-log`          | 错误日志监控     |
| `/erp/operation-log`      | 操作日志       |
| `/erp/ai-qa-optimization` | AI 问答测试看板  |

***

## 后端模块

共 12 个业务模块，全部注册在 `server/app.module.ts`。

### AI 模块（`server/modules/ai/`）

| 文件                       | 说明                                                           |
| ------------------------ | ------------------------------------------------------------ |
| ai.controller.ts         | 路由 /api/ai/\*（问答 / 配单 / 测价 / 反馈 / 解析 / 导出）                   |
| bailian.service.ts       | 百炼 API 调用（askFastSync / askFastStream / askSync / askStream） |
| forecast.service.ts      | AI 测价（SSE 流式 + 8 步思考 + 字段级进度）                                |
| pipeline.service.ts      | 专家模式 Pipeline（百炼 App API + 知识库）                              |
| feedback.service.ts      | AI 反馈服务                                                      |
| ai-batch-test.\*.ts      | AI 批量测试                                                      |
| ai.openapi.controller.ts | OpenAPI（关键词回填 / 反馈补录）                                        |
| ai-query-policy.ts       | 路由决策（4 类策略）                                                  |
| price-chart-policy.ts    | 图表意图判定                                                       |
| search-source-policy.ts  | 联网来源白名单                                                      |
| ai-chart-builder.ts      | 结构化图表构建                                                      |
| chat-record.service.ts   | 聊天记录持久化                                                      |
| token-record.service.ts  | Token 用量统计                                                   |

**AI 问答**：快速模式（qwen-turbo 流式）+ 专家模式（百炼 App API + query-policy 路由）
**AI 配单**：LLM 直通（parse-enquiry-params → score-matches），不使用规则引擎
**AI 测价**：SSE 流式 8 步思考，假进度爬升算法（每 800ms +0.5%，封顶 80%）

### 认证模块（`server/modules/auth/`）

- 路由 /api/auth/\*（登录 / 注册 / 改密码 / 短信验证码）

- 51bxg API 验证 + VipService.ensureUser 自动创建/绑定本地账户

- HMAC sessionToken（30 天有效期），写操作使用服务端 MEMBER\_CODE

- WAF 绕过服务（waf-bypass.service.ts，@Global）

### VIP 模块（`server/modules/vip/`）

- 路由 /api/vip/\*（5 个接口）

- PostgreSQL + Drizzle ORM（VipRepository）

- 8 档套餐（0-7），三层权限：pageAccess / features / exposure\_privilege

- 5 分钟缓存，成员变更时清除

### 智能广场模块（`server/modules/plaza/`）

核心社交功能模块，详见下文「智能广场」章节。

### 广场供需模块（`server/modules/plaza/plaza-demand.controller.ts`）

- 路由 /api/plaza/demands/\*

- 求购/供应信息 CRUD + AI 智能匹配 + 按品类/材质筛选

### 交易模块（`server/modules/trade/`）

- 路由 /api/trade/\*

- 查看联系方式（view-contact）= 成交

- 风控：3 天限看 1 次、成交超时限制

- 表：trade\_deal\_records / trade\_contact\_view\_logs

### 秀吗数据同步模块（`server/modules/xiuma-sync/`）

- 路由 /api/xiuma-sync/\*

- 分层：Controller 只依赖 `XiumaSyncService`，数据访问全部在 Service 层（2026-08-30 重构，详见「后端分层架构规范」）

- 秀吗 ERP 导出文件上传导入（货品快照 + 会员联系方式）

- 接口清单：

  - `POST /import-product`：货品快照导入（product\_info.aspx 导出，38 列中文表头，≤50MB）

  - `POST /import-mappings`：PRODUCT\_CODE → PRODUCT\_ID 映射导入（数据库只读导出）

  - `POST /import-contacts`：供应商联系方式导入（supplier\_info.aspx 导出）

  - `POST /import-member-contacts`：会员联系方式导入（member\_contact.aspx，CRM 导出，导入用户表并回填快照表电话）

  - `GET /search`：配单搜索（@Public，读本地快照表，返回与旧 XiumaProductSearchData 兼容结构，并入智能广场"供应挂单" plaza\_demands）

  - `GET /list`：管理页分页列表 + 详细筛选（ERP 秀吗数据导入页正文表格）

  - `GET /categories`：有效货品去重分类列表（管理页分类下拉选项）

  - `GET /stats`：快照统计（ERP 导入菜单）

  - `POST /deactivate`：标记指定 productId 失效（成交/下架）

- 表：xiuma\_product\_snapshot / xiuma\_member\_contact

- 数据获取唯一方式：秀吗 ERP 后台**手动导出文件 → 页面上传**，禁止数据库直连取数、禁止文件夹定时扫描、禁止调任何外部接口（详见下文「AI 配单数据源」）

### 聊天模块（`server/modules/chat/`）

- 路由 /api/chat/\*（会话创建 / 消息发送 / SSE 流 / 关闭）

### 行为模块（`server/modules/behavior/`）

- 路由 /api/behavior/\*（onboarding 状态 / 昵称解析 / 提交）

### 代理模块（`server/modules/proxy/`）

- 路由 /api/proxy/\*（51bxg / xiuma / 百炼 AI 转发）

- 仅 6 个只读方法，无交易类接口

### 结算模块（`server/modules/settlement/`）

> **⚠️ 由同事开发，本团队只审查不修改。** 站内交易需对接时先与用户确认。

### 其他模块

- **me**：飞书用户信息（仅飞书环境）

- **view**：视图渲染

***

## 后端分层架构规范（Controller → Service → Repository）

**原则**：三层架构，Controller 只做 HTTP 层（参数解析/校验/组装统一信封），业务逻辑与数据访问全部下沉 Service；Repository 只做单表/聚合查询。**禁止 Controller 直接注入** **`DRIZZLE_DB`** **或 Repository。**

**违规案例（2026-08-30 修复，commit eb28338）**：

- 修复前 `xiuma-sync.controller.ts` 构造函数注入 `XiumaProductSnapshotRepository`、`XiumaMemberContactRepository`、`DRIZZLE_DB`，`search` 等接口直接调 repo，并手写 `db.select(...)` 合并 plaza\_demands 数据。

- 修复后 Controller 只注入 `XiumaSyncService`；6 处 Repository 直调 + 1 处 db 直查全部下沉 Service（新增 `search / list / listCategories / setActive / contactViewStats / statsWithMemberContact`）。

- 同类修复：`ai.controller.ts` 拆分出 `chat-stream.service.ts` + `ai-plaza-data.service.ts`（#14 拆分 / #20 Repository 下沉），Controller 不再直连 Repository。

**检查方法**：grep 各 `*.controller.ts` 中的 `@Inject(DRIZZLE_DB)` 或 `XxxRepository` 引用——只应出现在 Service；重构后验证 `npm run type:check:server` + 接口实测（search/list/stats 等）行为与重构前一致。

***

## AI 配单数据源（2026-08-16 改造，重要）

**背景**：51bxg `CustomerData.PostQueryData`（UI\_ID=1784553230838779）接口已**彻底禁用**。AI金 配单（AiStockPage、daily-recommend）此前每次实时调用该接口，现**全部改读本地快照表**。

**数据链路（唯一合法，用户明确要求）**：
`秀吗 ERP 后台手动导出文件 → AI金 ERP「秀吗数据导入」页面上传 → xiuma_product_snapshot`
禁止数据库直连取数、禁止文件夹定时扫描、禁止调任何外部接口。

**数据事实**（2026-08-16 实测）：

- 全量上架现货 **3011 条**（与 ERP 后台计数一致）

- product\_info.aspx 导出 38 列，**无 PRODUCT\_ID**（只有货品编码如 XH2607044327）、**无城市/省份列**（只有仓库名如"无锡臻鼎库"）、**无联系方式**

- 联系方式：ERP\_MEMBER\_INFO（按 SUPPLIER\_ID 关联，原接口 LV.TELEPHONE）或 ERP\_SUPPLIER\_INFO.TELEPHONE

- 城市/省份：需从 ERP\_WAREHOUSE\_INFO 关联 ERP\_CITY\_CODE / ERP\_PROVINCE\_CODE 补充

**ERP 菜单定位**（ZERP\_SYS 库 `USERS_PRIVILEGE_MODULE_DEFINE` 模块表 + `USERS_PRIVILEGE_MODULE_MENU_TREE` 菜单树表）：

- 供应商：`ERP → 基础信息 → 商家信息 → 供应商`（supplier\_info.aspx，模块ID **103**）

- 卷板—信息：`ERP → 基础信息 → 产品信息 → 卷板—信息`（product\_info.aspx，模块ID **111**）

- 节点链：ERP(57807) → 基础信息(57808) → {商家信息(57814), 产品信息(57809)}

**数据库取数工作方式（用户强要求）**：

- **每次只给一条 SQL**，先 `SELECT COUNT(*)` 确认数量合理再给完整 SELECT 导出（用户原话"下次直接先让我查count"）

- 导出文件用户粘贴到本地 Excel 放桌面，约定文件名：`产品编码对照表.xlsx` / `yonghu.csv` / `仓库城市对照表.xlsx`

- 用户的 SQL 工具对跨库 `库名.dbo.表` 语法报错，需去库前缀直接写 `dbo.表`（当前连接即目标库）

- 遇到不清楚必须问用户，不许自己猜

**关键代码位置**：schema.ts `xiumaProductSnapshot` / `sql/023-create-xiuma-product-snapshot.sql` / `xiuma-product-snapshot.repository.ts` / `server/modules/xiuma-sync/` / `daily-recommend.service.ts` / `client/src/api/proxy.ts queryXiumaProductSearch` / `erp/xiuma-data-import/index.vue` / `docs/AI配单/08-数据源改造与同步方案.md`、`docs/AI配单/09-秀吗数据库取数SQL.md`

***

## 智能广场

智能广场是 AI金的核心社交功能，用户可发布行业动态、分析观点，支持关注/点赞/收藏/评论/分享等完整社交互动。

### 前端页面

| 页面                    | 路由                        | 说明               |
| --------------------- | ------------------------- | ---------------- |
| PlazaShellPage        | `/promo/plaza`            | 广场主页（信息流 + 发布入口） |
| PlazaPublishPage      | `/promo/plaza/publish`    | 发布页（AI 模板生成封面）   |
| PlazaPostDetailPage   | `/promo/plaza/post/:id`   | 内容详情             |
| PlazaDemandDetailPage | `/promo/plaza/demand/:id` | 供需详情             |
| PlazaSharePage        | `/share/:newsId`          | 外部分享页（免登录）       |

### 后端接口

| Controller            | 路由前缀               | 核心功能                     |
| --------------------- | ------------------ | ------------------------ |
| PlazaController       | /api/plaza         | 帖子列表/搜索/评论/关注/点赞/收藏/浏览历史 |
| PlazaDemandController | /api/plaza/demands | 供需 CRUD/AI 匹配/按材质匹配      |

### 后端服务

| Service                          | 职责                  |
| -------------------------------- | ------------------- |
| PlazaService                     | 帖子核心逻辑（发布/列表/搜索/互动） |
| PlazaDemandService               | 供需信息管理 + AI 智能匹配    |
| PlazaRecommendationService       | 个性化推荐（基于用户画像 + 行为）  |
| PlazaNotificationService         | 互动通知（评论/点赞/关注聚合）    |
| PlazaScheduleService             | 定时任务（数据聚合/过期清理）     |
| PlazaNotificationScheduleService | 通知定时（每周汇总推送）        |

### 数据库表（plaza\_\* 系列）

plaza\_posts / plaza\_videos / plaza\_questions / plaza\_likes / plaza\_images / plaza\_follows / plaza\_favorites / plaza\_comments / plaza\_comment\_likes / plaza\_notifications / plaza\_ai\_helpers / plaza\_demands

### 前端组件

PlazaRecommendRail / PlazaStrategyCard / PlazaAiPushRail / AiDailySummary / AiDailyContent / OnboardingModal / PlazaProfileHoverCard / AiPushDrawer

***

## 数据库

所有业务数据存储在 **PostgreSQL**，通过 Drizzle ORM 访问。

### 数据库连接

> **2026-09-04 起全环境主库切换为阿里云 RDS**（`server/database/index.ts`）：
>
> - 优先级：`DATABASE_URL`（远程 RDS）`||` 回退 `SUDA_DATABASE_URL`（妙搭平台内置库）
>
> - RDS：`pgm-bp1233q7n37by1456o.pg.rds.aliyuncs.com:5432/bxgAI`（公网可达，已实测沙箱/云函数出站可连）；连接串密码含 `@` 必须 URL 转义为 `%40`
>
> - 本地：.env 配 `DATABASE_URL`；飞书发布：**必须在妙搭控制台配置** **`DATABASE_URL`** **环境变量**（.env 不随发布走），不配则回退平台库
>
> - 平台注入的 `SUDA_DATABASE_URL` 永远存在，但仅在未配 `DATABASE_URL` 时生效
>
> - **副作用**：妙搭数据库管理界面、`miaoda db sql/migration` 仍作用于平台内置库，不再管理业务数据；建表/改表直接对 RDS 执行
>
> - **结论（2026-09-05 更新）**：全环境统一连同一 RDS，内置库（`SUDA_DATABASE_URL`）无业务数据、可当不存在、不需要同步；code\_gen/数据面板/miaoda 对 RDS 无感知生成不了业务表。今后只要 **RDS 表结构 ↔** **`server/database/manual-schema.ts`（本地权威，手工维护，2026-09-05 起替代 schema.ts）** 保持一致即可。`server/database/schema.ts` 是平台每轮自动重写（dataloom 生成 text 版），**无人引用、永不覆盖、永不 git add**。

| 环境 | 连接方式                                               | 说明                                     |
| -- | -------------------------------------------------- | -------------------------------------- |
| 本地 | `DATABASE_URL` 环境变量（默认 192.168.1.64:5432/bxg\_app） | 可用 Navicat 直连（PG 16.14，postgres:admin） |
| 飞书 | `DATABASE_URL`（远程 RDS）优先，回退 `SUDA_DATABASE_URL`    | 远程 RDS 公网可达；回退平台库不支持公网直连               |

DatabaseModule（@Global）通过 `DRIZZLE_DB` token 提供数据库实例，本地和飞书环境通用。

**⚠️ 平台 RLS 补丁还原机制（重要）**：平台包 `@lark-apaas/nestjs-datapaas` 在模块加载时对 `drizzle-orm/postgres-js` 的 `PostgresJsPreparedQuery.prototype.execute` 打全局 monkey-patch，每个请求的查询会被包上 `SET LOCAL ROLE 'authenticated_workspace_*'`（妙搭内置库的 RLS 机制，角色名含环境专属 workspace 后缀）。该角色在 RDS 上不存在，导致所有查询报 `role "authenticated_workspace_*" does not exist`。修复：`server/database/index.ts` 在平台模块加载前捕获原始 `execute`，`DatabaseModule.onModuleInit`（及 `getDb()` 首次调用）在配置了 `DATABASE_URL` 时还原原型，抵消补丁。仅回退平台库模式（未配 DATABASE\_URL）时补丁保持生效。

### 核心数据表（\~35 张）

**用户与认证**：users / user\_profiles
**VIP 系统**：vip\_packages / vip\_features / vip\_purchase\_records / vip\_member\_relations / vip\_operation\_logs（operation\_logs 为旧名）
**AI 模块**：ai\_chat\_records / ai\_feedbacks / ai\_token\_records
**智能广场**：plaza\_posts / plaza\_videos / plaza\_questions / plaza\_likes / plaza\_images / plaza\_follows / plaza\_favorites / plaza\_comments / plaza\_comment\_likes / plaza\_notifications / plaza\_ai\_helpers / plaza\_demands
**交易**：trade\_deal\_records / trade\_contact\_view\_logs
**秀吗数据**：xiuma\_product\_snapshot / xiuma\_member\_contact
**结算**：sales\_pipeline\_records
**行为**：user\_behavior\_records / user\_recent\_views / site\_feedback / site\_feedback\_images / sys\_api\_error\_logs
**运营统计**：platform\_daily\_stats / frontend\_success\_daily / frontend\_monthly\_target / frontend\_key\_account\_daily / frontend\_acquisition\_daily

### Schema 管理

- `server/database/manual-schema.ts`：**本地权威表定义文件**（2026-09-05 起，原 schema.ts 全量迁移至此），**手工维护**

- `server/database/schema.ts`：**平台托管、自动重写**（每轮对话 db-schema-sync 用 dataloom 元数据覆盖，生成 text 适配版），**无人引用、不要覆盖、不要 git add**

- **禁止从妙搭后台下载覆盖**：会回退表前缀重命名（见下方「数据库建表与命名规范」）

- 同步妙搭新表时必须手工合并进 manual-schema.ts，保留既有物理表名

- 本地 `npm run gen:db-schema` 为空占位（`echo ok`），不可用；表定义一律手工维护在 manual-schema.ts

- 本地新增表通过 SQL 迁移文件管理（`server/database/sql/`）+ 手工补 manual-schema.ts 定义

### 数据库建表与命名规范

> 2026-08-18 制定（sql/033 表前缀规范化迁移），适用于所有新建表与表改名。

#### 表名前缀规范（功能域划分）

新建表必须使用对应功能域前缀：

| 前缀                | 域                 | 示例                                                                                             |
| ----------------- | ----------------- | ---------------------------------------------------------------------------------------------- |
| user\_            | 用户基础信息与行为         | users、user\_profiles、user\_behavior\_records、user\_recent\_views                               |
| vip\_             | VIP 套餐/购买/成员/操作审计 | vip\_packages、vip\_features、vip\_purchase\_records、vip\_member\_relations、vip\_operation\_logs |
| ai\_              | AI 问答/反馈/用量       | ai\_chat\_records、ai\_feedbacks、ai\_token\_records                                             |
| plaza\_           | 广场社交              | plaza\_posts 等 12 张                                                                            |
| trade\_           | 站内交易              | trade\_deal\_records 等 4 张                                                                     |
| xiuma\_           | 秀吗数据同步            | xiuma\_product\_snapshot、xiuma\_member\_contact                                                |
| site\_            | 站点反馈              | site\_feedback、site\_feedback\_images                                                          |
| sys\_             | 系统级日志/配置          | sys\_api\_error\_logs                                                                          |
| sales\_pipeline\_ | 结算                | sales\_pipeline\_records                                                                       |
| ai\_jin\_         | 登录认证（历史前缀，例外保留）   | ai\_jin\_auth\_credentials、ai\_jin\_verification\_codes                                        |

**例外说明**：

- `users` / `user_profiles`：全项目广泛引用的核心表，保持原名作特例（2026-08 用户确认）。

- `ai_jin_auth_credentials` / `ai_jin_verification_codes`：实际属认证域但已带 ai\_jin\_ 前缀，经用户确认保持不变；未来新建认证表应优先 sys\_ 前缀。

- 孤儿表 `price_baogangdesheng_304_no1` / `price_ningbobaoxin_430_2b` / `price_taigangbuxiu_304_2b`：AI 测价历史遗留、代码零引用，不在规范管理范围，待另行决策。

**本次重命名映射表**（2026-08-18 执行，迁移脚本 `sql/033-rename-table-prefixes.sql`，8 张表）：

| 旧表名               | 新表名                     |
| ----------------- | ----------------------- |
| packages          | vip\_packages           |
| features          | vip\_features           |
| purchase\_records | vip\_purchase\_records  |
| member\_relations | vip\_member\_relations  |
| operation\_logs   | vip\_operation\_logs    |
| behavior\_records | user\_behavior\_records |
| recent\_views     | user\_recent\_views     |
| api\_error\_logs  | sys\_api\_error\_logs   |

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

- 数据插入类脚本已按当前（2026-08-18 表名前缀规范化后）表名书写：002-insert-packages-data 使用 vip\_packages / vip\_features，028-import-test-account（原 028/032 已合并） 使用 users / ai\_jin\_auth\_credentials，执行前确认目标库表名一致即可，无需再人工替换表名。

#### schema.ts 维护声明

`server/database/schema.ts` 已转为**手工维护**：**禁止从妙搭数据面板下载覆盖**（覆盖会回退表名重命名）；如需同步妙搭新表，必须手工合并并保留既有物理表名。

#### ⚠️ 飞书发布冻结警告

飞书 online 库仍为旧表名，在 online 库执行 sql/033 迁移之前，**严禁** **`miaoda deploy`**（部署后涉及改名表的接口会 42P01）；重写后的建表脚本（002/003/004/013/014 等以新表名书写）同样禁止在 online 库先于 033 执行，否则会以 IF NOT EXISTS 静默创建空壳新表；⚠️ **online 禁止** **`db sql`** **直接跑 DDL**（033 属表结构迁移），online 结构变更只能走 `miaoda db migration diff → apply`，且 DDL 量大受 175s 单事务硬超时限制，建议低峰期按表分批 apply 后立即发布。

***

## 飞书妙搭平台技术细节

### 应用信息

- **应用 ID**：app\_4k9x70cg0jws9

- **访问域名**：<https://hcnbikrs8vvb.feishuapp.com/app/app_4k9x70cg0jws9>

- **平台类型**：妙搭 Spark 全栈应用（@lark-apaas/fullstack-nestjs-core）

### 双数据库机制（dev / online）

| 维度    | 说明                                                                                 |
| ----- | ---------------------------------------------------------------------------------- |
| 物理隔离  | dev 和 online 是独立 PostgreSQL 实例，数据不互通                                               |
| 代码发布  | `miaoda deploy` 部署 git HEAD，代码自动同步                                                 |
| 表结构同步 | **`miaoda deploy`** **发布时自动同步**（pipeline 含"数据库更新"步骤，对比 dev/online 差异并自动 apply DDL） |
| 数据同步  | **不会自动同步**，需手动 `miaoda db sql < file.sql --env online`                             |
| 连接串   | `SUDA_DATABASE_URL` 由平台自动注入，无需手动配置                                                 |

**️ 重要（2026-08-25 实测确认）：**

- 发布 pipeline 流程：`开始 → 代码编译 → 数据库更新 → 代码分支落后检查 → 容器部署`

- "数据库更新"步骤会自动执行 DDL（CREATE TABLE / ALTER TABLE / CREATE INDEX 等），无需手动 `migration apply`

- 之前记录的 `miaoda db migration diff → apply` 是备用通道，正常情况下走发布自动同步即可

- 表数据（INSERT / UPDATE / DELETE）仍需手动同步到 online

### SQL 导入限制

| 限制        | 值               |
| --------- | --------------- |
| 语句超时      | 30 秒硬限制         |
| 单语句行数     | ≤ 5000 行 / 1 MB |
| SELECT 限制 | 1000 行          |

应对策略：按表拆分、每批 500\~1000 条 INSERT。

### 前端请求 CSRF 规则（403 红线，2026-08-19 实战教训）

妙搭生产网关对 `/app/<appId>/api/*` 的\*\*所有请求（含 GET）\*\*执行双提交 CSRF 校验，缺 `x-suda-csrf-token` 请求头直接被网关拦截返回 **403**。

- token 来源：`document.cookie` 中的 `suda-csrf-token`，取值函数 `getCsrfToken()`（`client/src/api/ai.ts`）。

- 新增前端接口调用**必须**携带该 header：优先走统一入口 `aiRequest` / `aiStreamRequest`（已内置）；确需裸写 `fetch` 时必须手动带上，参考 `client/src/api/trade.ts` 的 `tradeGet`、`client/src/api/proxy.ts` 的 `queryXiumaProductSearch`。

- **排查要点**：403 由平台网关返回，不是后端 NestJS（AuthGuard 只抛 401）。浏览器控制台出现批量 403 时，先检查请求头是否带 `x-suda-csrf-token`，而不是去查后端路由/鉴权。

- 事故案例（2026-08-19）：AI 配单 8-16 新增的 `/api/trade/*`（view-limit / dealt-product-ids / contacted-product-ids）与 `/api/xiuma-sync/search` 裸 fetch GET 未带该 header，飞书环境配单第二步「搜索市场现货」全部 403、页面空白；本地环境无此网关层，问题只在飞书线上暴露。

### OpenAPI 对外接口

| 路由前缀        | 鉴权               | 调用方   |
| ----------- | ---------------- | ----- |
| /api/\*     | 用户登录态（AuthGuard） | 应用前端  |
| /openapi/\* | API Key（网关层自动校验） | 第三方系统 |

- /openapi Controller 不需要 @NeedLogin()，user\_id 固定为 -1（系统身份）

- 调用方式：`Authorization: Bearer <api_key>` 或 `X-Api-Key: <key>`

- **当前仓库无 openapi controller 实现**（曾有的 `ai.openapi.controller.ts` 已不存在），`docs/openapi.json` 也不存在，`npm run gen:openapi` 是空占位（UNSUPPORTED, SKIP）——要对外暴露接口需自行创建 `*.openapi.controller.ts` 并手动维护 OpenAPI 3.0 文档

- **API Key 获取/轮换**（妙搭 Spark Open API 体系）：`miaoda apps +openapi-key-create --app-id "$app_id"` 创建；密钥**仅创建时一次性可见**，丢失只能 `miaoda apps +openapi-key-reset --app-id "$app_id" --id <key-id> --yes` 轮换（旧密钥立即失效）。用户已有 Key（ID 1872128960518442，名称"数据库"，allow\_all: true）

- **飞书 aPaaS Open API 与妙搭 Spark Open API 是两套体系**：aPaaS（低代码平台内置）在「应用管理页 → Open API」创建凭证，用 Client ID/Secret 先换 token；Spark 用 API Key 直接鉴权。本项目是**妙搭 Spark 全栈应用**（依据 @lark-apaas/fullstack-nestjs-core + SUDA\_DATABASE\_URL），走 Spark 体系

- **spark-v1 API**（open.feishu.cn/open-apis/spark/v1/...，执行 SQL）需要管理员审批权限（spark:app.sql\_commands:write），**不可用，放弃该路线**

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

- **`db sql`** **只对 dev 可直接跑 DDL；online 的 DDL 走** **`migration`，`db sql ... --env online`** **仅用于 DML**（详见上文「Online 结构同步约束」）

### 妙搭 PostgreSQL 容量与性能限制（2026-08 平台信息）

| 指标                    | 基础免费版           | 商业标准版                                  |
| --------------------- | --------------- | -------------------------------------- |
| 数据存储                  | 0.4 GB（约 20 万行） | 0.4 GB + 平台席位×200MB + 应用访问席位×50MB（可增购） |
| 单表最大行数                | 50 万行           | 200 万行（可扩展）                            |
| 数据查询 QPS              | 5               | 200                                    |
| 数据库 CRUD（云函数/OpenAPI） | 10 万/天          | 100 万/天（可扩展）                           |
| 云函数运行量                | 1,000/天         | 100 万/天（可扩展）                           |
| OpenAPI 调用量           | 0               | 线上 100 万/天，沙箱 1 万/天                    |

底层为**火山引擎 PostgreSQL Serverless**：非活跃实例自动 Scale-to-Zero；推荐约束 TPS ≤10/分支、QPS ≤20/分支、活跃连接 ≤10/分支、单分支数据量 ≤10GB。

### 数据库管理界面 SQL 鉴权机制（不可复用）

平台 Web 控制台（数据库管理界面）执行 SQL 时前端 Network 看不到 Authorization header，因为**鉴权由平台网关层完成**：浏览器持有 session cookie（suda\_\*），网关识别身份后注入鉴权转发给数据库服务——这是平台内部通道（innerAPI），**不对外暴露、外部程序无法复用**。外部只能走 miaoda CLI（沙箱）或自建 /openapi 接口。

### 飞书平台运行时环境基准（feishu-env-baseline，2026-08-26 实测白盒化）

> **`feishu-env-baseline/`** **是飞书妙搭环境唯一权威基准**，内容全部来自飞书终端实测（非推测）。`migrate/README.md` 仍是同步执行入口，二者互补。排查任何"本地正常、线上异常"时**先查此目录**。

已摸透并归档（01-10 十余份基准 md + 架构报告 `feishu-platform-architecture/feishu-platform-architecture.html`）：

| 领域      | 关键结论                                                                                                                                                                                   |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 部署形态    | Faas 托管：nginx + supervisor + `dev.js` 守护 `nest start --watch`+vite；每次启动 `cleanStaleDist` 全量清 dist（"慢"主因），日志落 `logs/dev.std.log`（`miaoda observability log`）                            |
| 构建/发布   | `scripts/build.sh` 6 步；发布 pipeline：编译→数据库更新→分支检查→容器部署；`prune-smart.js` 用 `@vercel/nft` 静态裁剪 node\_modules（新增动态 import 依赖需加入 `.env` 的 `MIAODA_RUNTIME_ENTRIES` 否则线上 MODULE\_NOT\_FOUND） |
| 内核装配    | `configureApp` 完整顺序 + `PlatformModule`；全局前缀 = `CLIENT_BASE_PATH`（`/app/{appId}/`）；schema.ts 由 `npx @lark-apaas/db-schema-sync@latest` 生成                                               |
| CSRF/身份 | 双中间件：页面请求种 `suda-csrf-token` cookie + `/api/*` 校验 header==cookie（GET 也校验）；平台 web 用户从 `suda_web_user` 请求头解析（非 cookie），前端须让网关注入否则 `req.userContext` 空                                    |
| 数据层     | 业务走原生 `postgres` 直连 `SUDA_DATABASE_URL`（不走 datapaas 代理）；datapaas 才有 RLS（SET ROLE/anon\_/service\_role\_），**直连查询不受 RLS 影响**                                                             |
| 依赖      | `@lark-apaas` 全 30 包；仅 `fullstack-nestjs-core` + `nestjs-datapaas` 是运行时核心（`configureApp`/PlatformModule/CSRF/中间件都在这两个）                                                                 |
| CLI     | `miaoda` v0.1.38 子命令：app/deploy/db/file/observability/skills/registry                                                                                                                  |

***

## VIP 权限体系

### 套餐结构

8 档（level 0-7）：免费/试用/入门(3980)/进阶(9800)/专业(19800)/企业(49800)/旗舰(119900)/尊享定制(498000)
共享账号数从 packages 表读取：1/1/3/9/9/9/9/9

### 三层权限

1. **pageAccess** — 页面访问控制
2. **features** — 功能开关
3. **exposure\_privilege** — AI 配单/问答中的曝光优先级

### 前端集成

| 文件                        | 说明                 |
| ------------------------- | ------------------ |
| client/src/api/vip.ts     | VIP API 封装         |
| client/src/stores/vip.ts  | Pinia store        |
| client/src/stores/auth.ts | 登录后 loadPermission |

***

## ERP 权限分级（#37，2026-08-29 完成）

**功能**：ERP 管理后台菜单可见性分级 + 账号/权限管理页 + 接口级拦截 + 停用账号 token 即时吊销。

| 层    | 实现                                                                         |
| ---- | -------------------------------------------------------------------------- |
| 数据   | `erp_user_account.permissions` JSONB（迁移 060），超管 `['*']`                    |
| 前端   | `erp/menu.ts` 菜单目录 + 角色预设；`ErpLayout` 按账号 permissions 动态过滤侧边栏（菜单可见 = 接口可调） |
| 登录   | 登录接口返回 `permissions / isAdmin`；`getPermissions` 失败回落为空数组                   |
| 权限管理 | 权限管理模块（账号 CRUD，仅超管，清洗 `*`）                                                 |

**接口级拦截（`erp-path-permission.ts`** **+** **`ErpAuthGuard`）**：

- `PATH_PERMISSION_RULES` 按「API 路由前缀 → 菜单权限」映射，取**最长 prefix** 匹配（如 `/api/collect/dicts` 优先命中 dict 规则而非笼统 `/api/collect`）。

- 哨兵 `ANY_ERP_USER='@any'`：任意有效账号可访问（如侧边栏菜单数据）。

- `null`（未映射路由）：**仅超管**可访问（默认收紧，如 permission / error-logs / operation-logs）。

- 示例：`/api/erp/trade-admin` 归 `/erp/order-admin` 域，授权给持订单管理权限的账号。

- `ErpAuthGuard` 每请求联合查询账号 `isActive + permissions`：停用账号即时吊销已签发 token（返回 401）；未映射路由非超管返回 403；GET 导出下载支持 `?token=` 兜底（浏览器直链无法带 header）。

**验证**：`acc_tradetest`（order-admin 权限）可访问 `/api/erp/trade-admin/deals`；停用后同 token 立即 401。文档 `dev-output/docs/EPR权限分级-优化项37-2026-08-29.md`。

***

## 色彩系统

Tailwind CSS v4 `@theme` 语义色，定义在 `client/src/styles/tailwind.css`：

| 令牌                       | 用途          |
| ------------------------ | ----------- |
| `--color-brand`          | 品牌主色（按钮、链接） |
| `--color-brand-light`    | 品牌浅色（hover） |
| `--color-brand-lighter`  | 品牌极浅（侧边栏背景） |
| `--color-brand-bg`       | 页面/卡片背景     |
| `--color-brand-hover`    | 品牌深色（hover） |
| `--color-text-primary`   | 正文主色        |
| `--color-text-secondary` | 次要文本        |
| `--color-text-muted`     | 弱化文本        |
| `--color-text-dark`      | 深色文本（标题）    |
| `--color-border`         | 边框          |
| `--color-success`        | 成功          |
| `--color-warning`        | 警告          |
| `--color-danger`         | 危险/删除       |

**禁止使用 Tailwind 预设色**（如 `bg-blue-100`），必须使用语义色。

***

## 跨环境同步

### 同步范围

本地和飞书两地同步：**client/、server/、shared/、erp/** 四个目录。

> **同步前必须** `npm run type:check` 确认无 TS 错误。

### 绝对不复制到飞书的文件

package.json、vite.config.ts、tsconfig.*.json、tailwind.config.ts、nest-cli.json、eslint.config.js、.stylelintrc.js、.env、.gitignore、start-local.bat、scripts/、docs/、node\_modules/、*.tsbuildinfo、package-lock.json

> 飞书版这些配置含 `@lark-apaas/fullstack-presets` 框架差异，不可覆盖。`feishu-env-baseline/`（本地飞书环境基准研究）同样不复制，仅本地排查用。

### 新增依赖处理

- 不复制 package.json，在飞书终端单独 `npm install`

- 飞书编辑器不能改 package.json（平台保护），用 `npm pkg set` 或 `node -e`

### isLocal 机制

```typescript
const isLocal = !process.env.SUDA_DATABASE_URL;
```

| 环境                | 行为                                              |
| ----------------- | ----------------------------------------------- |
| 本地（isLocal=true）  | 跳过 PlatformModule、MeModule；DATABASE\_URL 连本地 PG |
| 飞书（isLocal=false） | 加载 PlatformModule；SUDA\_DATABASE\_URL 自动注入      |

### 文件分类

| 分类    | 内容                                                      |
| ----- | ------------------------------------------------------- |
| 双向同步  | server/modules/、server/common/、client/src/、shared/、erp/ |
| 按环境修改 | .env（SUDA\_DATABASE\_URL、SERVER\_PORT 按环境区分）            |
| 本地独有  | .env.local、logs/、.uploads/、.tmp-meeting/                |

### 已废弃文件（禁止使用）

`.env.miaoda`、`server/app.module.miaoda.ts`、`server/main.miaoda.ts`、`client/vite.config.local.ts`、`restart.bat`、`server/modules/erp/`（已迁移到 erp/server/）

***

## 飞书环境 fetch 规则（CSRF 头，2026-08-26 修正）

> ⚠️ **重大修正**：早期"GET 零 header"是错误的，它导致 ERP 13 个页面的 GET 请求在飞书被网关 403（数据取不到）。
> 飞书平台对 `/api/*` **所有请求（含 GET）** 执行双提交 CSRF 校验，只要请求带了自定义 header（哪怕只有 `Authorization`），就必须同时带 `x-suda-csrf-token`，否则返回 403。

| 场景                           | 正确做法                                                      |
| ---------------------------- | --------------------------------------------------------- |
| 任何带自定义 header 的 GET/POST/SSE | **必须**带 `x-suda-csrf-token`（值 = cookie `suda-csrf-token`） |
| 完全裸 fetch（无任何自定义 header）     | 可不带 CSRF 头但极不建议，一律显式加更稳妥                                  |

**getCsrfToken() 取值函数**（读 cookie）：

```ts
function getCsrfToken(): string {
  const match = document.cookie.match(/(?:^|;\s*)suda-csrf-token=([^;]*)/)
  return match ? match[1] : ''
}
```

- 每个页面的**统一请求封装**（api.ts 的 fetchJson/request/getAuthHeaders 等）**必须**内置该 header，让页面调用者无需手写。

- 排查：页面能登录、但数据取不到 → F12 看是否批量 **403 "csrf token not found in header"** → 即 GET 封装漏了 CSRF 头（2026-08-26 vip-admin 等 13 页全部中招，已统一修复，提交 e33ba05）。

***

## 开发命令

| 命令                   | 说明                                                                |
| -------------------- | ----------------------------------------------------------------- |
| `npm run dev:server` | 启动后端（`nest start --watch`，直接跑 TS 源码，改代码自动重启；等价 `start-local.bat`） |
| `npm run dev:client` | 启动前端（Vite，5173）                                                   |
| `npm run dev:local`  | 本地一键启动脚本（`node ./scripts/dev-local.js`）                           |
| `npm run type:check` | TS 类型检查（前后端：`type:check:server` + `type:check:client`）            |
| `npm run test:unit`  | 单元测试（`jest test/unit --runInBand`）                                |
| `npm run build`      | 生产构建（`build:server` + `build:client`，仅发布用）                        |

**本地后端运行方式（唯一推荐）**：`start-local.bat`（=`npm run dev:server`，`nest start --watch` 直接跑 TS 源码，改代码自动重启）。**不要跑** **`npm run build:server`** **产 dist**（无人使用，纯多余）；改完代码只需 `type:check` + commit。后端监听 **`http://localhost:3000`**（`SERVER_PORT=3000`），vite 代理目标必须与之匹配，否则登录 500（详见「已知问题 #21」）。

> PowerShell 不支持 `set NODE_ENV=xxx &&` 语法，必须使用 `cross-env`。Node 版本锁定 22.23.1。

***

## 超大文件拆分经验（#15 / #16）

> 2026-08-29 \~ 08-30 大批量拆分实践沉淀。目标：超长 `.vue`（>1500 行）与超长 `.service/.controller`（>2000 行）按内聚模块拆分，提升可维护性；**拆分不改变业务逻辑**。

**拆分方法**：

1. 按高内聚子模块抽取为独立子组件/子服务，父子通信用 props + emit 解耦（父保留状态与业务编排，子做展示与局部逻辑）。
2. 模板中事件/图标等类型绑定由子组件持有，需在 `<script setup>` 导入；ECharts 实例等自持资源在子组件内 mount/dispose。
3. 样式随组件走 scoped 迁移；父组件遗留的历史死样式可后续单独清理（`#16` 结尾统一清过 524 行死样式，commit 50fa865），不混入拆分提交。
4. 清理因拆分产生的孤儿 import/死代码（lucide 图标、API、composable 等）；重复加载逻辑抽 composable（如 `usePaginationList`）。
5. 验证：`npm run type:check:client` + ESLint；拆分不含逻辑变更，接口/行为保持一致。

**已拆分清单**：

| 文件                              | 拆分产物                                                                                                                                          | 参考 commit         |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| forecast.service.ts（2625→835 行） | F1 数据加载 / F2 `forecast-validator.ts` / F3 `forecast-engine.ts`                                                                                | d83eca0 / 28fcc51 |
| ai.controller.ts（2250→1490 行）   | `chat-stream.service.ts` + `ai-plaza-data.service.ts`                                                                                         | 1aa9d98           |
| PlazaPublishPage.vue            | 12 子组件（DemandPublishForm / EditorToolbar / MediaUploader / PublishPreview / TagSelector / PublishSettings / AiAssistantPanel / DraftDrawer 等） | 0723382 等         |
| PersonalProfilePage.vue（3959 行） | ProfileEditModals / AvatarCropModal / MyPostsGrid / FollowModal / ProfileHeroHeader / ProfileTabBar / ProfilePostGrid + `usePaginationList`   | c672c58 起         |
| PlazaPostDetailPage.vue（3700 行） | CommentPanel / PostSidebarPanel / PostMediaViewer / PostPageShell                                                                             | 6aa94d9 等         |
| AiStockPage.vue PC 部分（4384 行）   | PcStatusArea / PcRankTable / PcDetailCard                                                                                                     | b9b4ae9 等         |

***

## 文档目录

| 目录                     | 说明                                     |
| ---------------------- | -------------------------------------- |
| `docs/项目说明书/`          | 项目概览 / 环境配置 / 部署同步 / 踩坑记录              |
| `docs/AI问答系统架构/`       | v3.0 query-policy 路由模式 + System Prompt |
| `docs/AI配单/`           | LLM 直通架构 + 每日数据导入 SOP                  |
| `docs/AI测价/`           | SSE 流式 + 8 步思考                         |
| `docs/VIP系统/`          | VIP 权限方案                               |
| `docs/结算系统/`           | 结算模块文档（同事维护）                           |
| `docs/团队开发规范.md`       | SVN + git 双轨工作流                        |
| `feishu-env-baseline/` | **飞书平台运行时环境唯一权威基准**（已实测白盒化，见下节）        |

***

## 规则与约束

### 硬约束

#### 运行时

1. npm scripts 必须用 `cross-env`
2. `.env` 不提交；修改后必须重启后端
3. 端口：前端 5173，后端 3000（`SERVER_PORT=3000`，vite 代理目标必须一致）

#### 版本控制

1. `node_modules/`、`dist/`、`*.log` 等不可提交
2. 依赖变更单独 commit
3. 提交前 `npm run type:check`

#### VIP 系统

1. 8 档套餐，共享账号数从 packages 表读取
2. 购买记录必须包含"购买价格（分）"
3. 成员关系表校验引用的购买记录
4. `check-feature` 接口使用 POST

#### 登录与数据

1. 登录独立维护本地账户表，不修改 51bxg 数据库
2. 所有用户 ID 使用 MEMBER\_CODE
3. 数据单向通道：秀吗 → AI金，反向永远不存在

#### AI 工具

1. 不自动修改配置文件（package.json / vite.config.ts 等）
2. AI 生成的测试/临时文件不提交

#### 安全

1. API Key 使用环境变量
2. SQL 必须参数化

#### 老平台红线

1. 51bxg / 秀吗源码禁止修改
2. 生产库严格只读（SELECT only）
3. 接口报警邮件 → 减少无谓请求

#### 用户铁律与沟通（全局适用）

1. **绝不删除/清空用户数据文件**（用户担心大模型清空 C 盘的严重事故）；危险操作（删除/格式化/覆盖/剪切）宁停不干，删除前必须备份并确认目标
2. **不用 Plan 模式（/plan）**，确认需求直接提问
3. 对 51/秀吗 数据库取数：**每次只给一条 SQL、先 COUNT、遇到不清楚必须问用户不猜**（见「AI 配单数据源」）
4. **飞书写操作（同步/部署/上传/执行命令）必须事先经用户明确允许**；本地 git commit 按「git 提交规范」可自行判断时机执行（见下）

### 工程约定

- **DTO**：用 interface 而非 class-validator

- **代码搜索**：必须包含 erp/ 目录

- **飞书 fetch**：所有带自定义 header 的 GET/POST/SSE 必须带 `x-suda-csrf-token`（无自定义 header 的裸 GET 可不带但极不建议；「GET 零 header」旧规则已废弃，详见「飞书环境 fetch 规则」）

- **ERP 页面**：蓝色主题 `#2f71ff`

- **结算模块**：只审查不修改

- **接口统一信封**：内部接口统一 `{code, message, data}`；`shared/envelope.ts` 的 `ok()/fail()` 是唯一来源（`fail()` 默认 `BIZ_ERROR=-1`）；全局异常过滤器统一失败信封 `{code, message, data: null}`；分页响应必须 `{items, total, page, pageSize}`；错误码用语义常量（`BIZ_ERROR=-1 / BAD_REQUEST=400 / UNAUTHORIZED=401 / FORBIDDEN=403 / NOT_FOUND=404 / INTERNAL_ERROR=500 / OK_CODE=0`）。第三方代理（51bxg/秀吗）与 SSE 流式接口不套信封。

- **后端分层**：Controller 禁止直连数据库/Repository，数据访问全部下沉 Service（详见「后端分层架构规范」）

- **移动端品牌视觉**：梯度头部/AI 光晕、白卡片、梯度图标背景（`from-brand-lighter`→`brand-bg`）；智能广场瀑布流卡片左右间距 32px

- **AI 问答两列布局**：左主菜单常驻 + 中 280px 会话历史列，禁止被替换

- **编码四准则（Karpathy，全局 skill 自动加载）**：①先思考再编码——不确定就停下来问，有多种解读都列出来别偷偷选一个；②简单优先——最少代码解决问题，不写没被要求的功能/一次性抽象/投机配置/不可能场景的错误处理；③外科手术式改动——只改必须改的，不顺手重构，清理只删自己造成的废弃代码，旧代码明显缺陷单独提 issue 不混入本次改动；④目标驱动——加校验写测试、修 bug 先复现、重构保测试、优化写基准

- **后端运行方式**：本地统一用 `start-local.bat` / `npm run dev:server`（watch 模式），不要产 dist（详见「开发命令」）

***

## 已知问题与经验

### 飞书环境特有问题

| #  | 问题                                          | 根因                                                                           | 修复                                                                               |
| -- | ------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1  | 侧边栏 403                                     | fetch 带自定义 header 触发 CSRF                                                    | 统一请求封装带 `x-suda-csrf-token`（早期「GET 零 header」方案已于 2026-08-26 推翻，见「飞书环境 fetch 规则」） |
| 2  | SSE 进度条不渲染                                  | ai.ts 缺事件类型分发                                                                | 补全 SSE case                                                                      |
| 3  | 飞书白屏                                        | index.html 脚本路径错误                                                            | 统一 `/client/src/main.ts`                                                         |
| 4  | AI 返回原始 JSON                                | 飞书 ai.controller.ts 旧版                                                       | 同步本地版本                                                                           |
| 5  | 登录页按钮无反应                                    | 飞书 auth.ts 缺导出                                                               | 同步文件                                                                             |
| 6  | 登录后不跳转                                      | 冗余 isLoggedIn 检查                                                             | 移除冗余检查                                                                           |
| 22 | ERP 各页数据取不到（GET 403 "csrf token not found"） | ERP 各页 GET 通用封装只带 Authorization，漏 `x-suda-csrf-token`（误从"GET 零 header"旧规则继承） | 13 个页面统一请求封装补 getCsrfToken + x-suda-csrf-token 头（e33ba05）；详见上文「飞书环境 fetch 规则」    |

### 编码/数据问题

| #  | 问题                                                                          | 修复                                                          |
| -- | --------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 7  | Bitable 字段显示 \[object Object]                                               | 服务层 normalize                                               |
| 8  | VIP 表用户 ID 不一致                                                              | 统一 MEMBER\_CODE                                             |
| 9  | flex + overflow-hidden 阻断滚动                                                 | 使用 min-h-0                                                  |
| 10 | PowerShell 写文件损坏中文                                                          | `-Encoding UTF8`                                            |
| 23 | `v-if` / `v-else-if` 之间残留注释节点导致模板编译错误                                       | 删除条件指令间的注释节点（2026-08-30 PersonalProfilePage，commit db152e5） |
| 24 | AI 配单初始化误显示「暂无匹配的现货挂单」                                                      | 空态仅在分析完成后才渲染（PcRankTable，commit a211991）                    |
| 25 | AI 解析失败仍报错（表单已填好）                                                           | 表单选择数据优先，LLM 解析失败用表单兜底补剩余空字段（commit db152e5）                |
| 26 | TokenStatsPage `LineChart` 已声明（lucide-vue-next 图标 vs echarts/charts 图表导入冲突） | ECharts 图表改别名 `EChartsLineChart`                            |
| 27 | 改代码后仍测到旧逻辑                                                                  | 浏览器缓存/热更新失效，硬刷新 Ctrl+F5                                     |

### 外部服务问题

| #  | 问题                                          | 修复                                                                                                                                                                                         |
| -- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 11 | 51bxg WAF 拦截                                | waf-bypass.service.ts（jsdom 执行混淆 JS）                                                                                                                                                       |
| 12 | 51bxg 会话过期                                  | Cookie TTL 2 小时，过期重新登录                                                                                                                                                                     |
| 13 | QueryCoilPriceInfo 产品 ID 30/31/36/37 返回 500 | 51bxg 后端 dtTrend 为 null 未判空（ForecastController.cs:1942/1975/2038）；proxy parseResponse 识别 {"Message":...} 转 {code:-1}，前端检查 trend\_data 静默跳过；`KNOWN_FAILING_IDS=[30,31,36,37]` 过滤避免无效请求与报警邮件 |

### 飞书数据库经验

| #  | 经验                                                                                                                                                         |
| -- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 14 | dev/online 数据库物理隔离，发布代码不携带数据                                                                                                                               |
| 15 | schema.ts 已转手工维护（2026-08），禁止从妙搭后台下载覆盖（会回退表名重命名）                                                                                                            |
| 16 | 妙搭 PG 不支持公网直连，本地可用 Navicat 直连本地 PG                                                                                                                         |
| 17 | SQL 导入 30 秒超时，大批量需分批（500\~1000 条/批）                                                                                                                        |
| 18 | 飞书 `uuid_generate_v4()` 需转为 `gen_random_uuid()`                                                                                                            |
| 19 | 飞书 SQL 编辑器建表后 schema.ts 不会即时重新生成（滞后）；表是否存在以 pg\_tables 查询为准                                                                                                |
| 20 | HeidiSQL(MySQL 模式) 导出 PG 备份 1.sql 有 6 类缺陷需修复：`ON ""` 表名丢失、CREATE 间缺分号、UNKNOWN→TEXT\[]、MySQL 函数块 DELIMITER、`_binary 0x`→bytea、外键顺序（users 先于 user\_profiles） |
| 21 | 本地后端监听 `http://localhost:3000`（`SERVER_PORT=3000`）；vite 代理目标必须匹配该端口（曾由 8000 改为 3000，若不匹配登录 500，commit 3ff183f）                                             |

