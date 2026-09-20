# AI金项目 — 开发执行方案

> 生成时间：2026-08-29
> 背景：利用 38B 免费 token（MIMO V2.5 PRO）加速 AI金项目的开发落地

---

## 一、讨论背景与核心问题

### 1.1 资源情况
- 免费 API key，380 亿 token 量（MIMO V2.5 PRO）
- 已完成：程序员题库、文章生成、DeepSeek harness 开源项目分析
- 目标：把 token 消耗在真正有价值的项目开发上，而非"暴力浪费"

### 1.2 项目现状
- 项目：AI金 — 不锈钢 B2B 智能伙伴
- 技术栈：Vue3 + NestJS + PostgreSQL（Drizzle ORM）
- 状态：基础设施功能尚未完成，进入"缝补迭代"阶段
- 痛点：很多外部老平台接口申请不了，需要跨部门协调

### 1.3 核心担忧（经过三轮讨论确认）

| 担忧 | 具体表现 |
|------|---------|
| **代码质量** | 重复造轮子、风格不统一、写臃肿代码 |
| **需求偏离** | 没人盯着就南辕北辙，AI 猜测用户意图导致走偏 |
| **外部依赖** | 老平台接口不可用，AI 用 mock 混过导致产出无效 |
| **过度开发** | 项目被写得特别臃肿，超出实际需要 |
| **单上下文盲区** | 同一个模型/对话中讨论多轮，仍会考虑不周；换模型总能找出问题 |

---

## 二、解决方案

### 2.1 总体原则

> **宁可少做，不可做错；宁可暂停，不可猜测。**

### 2.2 三层执行架构

#### 第一层：项目现状摸底
- 全面扫描项目代码结构、缺失模块、已有规范
- 生成 **"基建缺口清单"**：哪些模块完整、哪些是骨架、哪些完全缺失
- 产出：项目认知基线，后续所有任务以此为依据

#### 第二层：任务分级

| 分类 | 定义 | 执行方式 |
|------|------|---------|
| **A类：可独立执行** | 不依赖外部接口、需求明确、边界清晰 | 直接执行，无需确认 |
| **B类：需确认后执行** | 涉及业务逻辑、交互设计、数据结构选择 | 先出设计方案，用户确认后再写代码 |
| **C类：需用户手动处理** | 外部接口申请、跨部门协调、权限配置 | 生成待办清单，用户自行处理 |

**A类任务示例：**
- 补充缺失的单元测试
- 补充数据库迁移脚本
- 补充 TypeScript 类型定义
- 代码风格统一化
- lint 错误修复
- 文档补充

**B类任务示例：**
- 数据库 schema 设计
- API 契约定义
- 核心业务逻辑（配单算法、价格计算）
- 前端页面布局/交互方案

**C类任务示例：**
- 老平台接口申请
- 跨部门数据对接
- 第三方服务鉴权配置
- 生产环境部署配置

#### 第三层：执行节奏
- A类任务 → 直接跑，完成后 git commit
- B类任务 → 出方案文档 → 用户花 30 秒确认 → 写代码 → commit
- C类任务 → 输出待办清单 → 用户手动处理 → 处理完后再接回 A/B 类

---

### 2.3 代码质量保障

#### 硬约束（不依赖人的判断）
1. **强制代码考古**：写代码前必须先 grep/Read 现有代码，了解已有工具函数、DTO、错误处理模式
2. **风格克隆**：匹配项目现有代码风格，不引入新的编码风格
3. **禁止清单**：不引入项目未使用的依赖
4. **工具兜底**：每次改动后运行 TypeScript 编译、lint、测试，用工具保证基本质量

#### 软约束（减少"想不周全"的风险）
5. **对抗性自审**：重要设计方案产出后，以"刁钻审查者"角色找漏洞
6. **单次输出长度封顶**：单次任务代码不超过 500 行，超出则拆分交付
7. **歧义暂停**：遇到需求歧义时，列出 2-3 种解读，暂停等待澄清，不自行猜测

---

### 2.4 外部依赖处理

**铁律：凡不在已知可用列表中的外部接口，一律视为"不可用"。**

对不可用的依赖，必须执行以下动作之一（**禁止默默 mock**）：
1. **明确标记阻断点**：在代码中写入注释和 throw Error，标记为"待替换"
2. **生成对接待办清单**：列出需要用户手动协调的参数、URL、鉴权方式
3. **输出基建缺口报告**：告诉用户"哪些功能因外部依赖卡住了"，而非"哪些功能做完了"

---

### 2.5 单上下文盲区应对

**问题本质**：同一个对话中建立的假设体系会产生盲区，后续推理都在假设之上自洽，不会自己发现问题。

**应对策略：**
1. **技术手段兜底**：类型检查 + 测试 + lint，这些不依赖"想得全不全"
2. **关键节点用户介入**（只需几十秒确认）：
   - 数据库 schema 设计（表结构改了很难回退）
   - API 契约定义（前后端对接边界）
   - 外部依赖决策（mock vs 真实接口）
   - 核心业务逻辑（配单算法、价格计算）
3. **小步提交**：每完成一个子功能就 git commit，出问题容易回滚
4. **重要方案可外部审查**：如果用户对某个方案不放心，可以把方案文档发给其他模型做交叉验证

---

## 三、执行红线

1. **不猜测用户意图** — 有歧义就暂停问
2. **不引入未授权依赖** — 只用项目已有的
3. **不默默 mock 外部接口** — 必须显式标记
4. **不一次写超过 500 行** — 拆分交付
5. **不跳过类型检查和测试** — 工具兜底是底线
6. **每个子功能完成后 git commit** — 保证可回滚
7. **临时文件任务完成后删除** — 保持工作区干净

---

## 四、项目现状扫描报告（2026-08-29）

### 4.1 前端代码问题

#### 超大 .vue 文件（72 个文件超过 300 行）

**严重（>2000 行，需优先拆分）：**

| 文件 | 行数 | 说明 |
|------|------|------|
| PlazaPublishPage.vue | 5354 | 广场发布页，功能最复杂的页面之一 |
| AiStockPage.vue | 4384 | AI 配单页 |
| PersonalProfilePage.vue | 3984 | 个人资料页（你提到的"几千行"） |
| PlazaShellPage.vue | 3024 | 广场外壳页 |
| kg-graph/index.vue | 2918 | ERP 知识图谱 |
| ai-qa-optimization/index.vue | 2325 | ERP AI问答优化 |
| OnboardingModal.vue | 2293 | 引导弹窗 |
| AiPredictPage.vue | 2199 | AI 测价页 |
| dict-admin/index.vue | 2039 | ERP 词典管理 |

**中等（500-2000 行）：** 63 个文件

#### UI 组件库混用
- **Element Plus**：ERP 管理后台全部使用（ElMessage 19个文件218处、ElMessageBox 11个文件29处）
- **TDesign**：仅 client 移动端组件使用（11个文件）
- **ElDialog / ElDrawer / ElNotification**：均未使用，弹窗全部为自定义实现

#### 空状态文案不统一
- 30+ 个文件、约 80 处使用了各种变体："暂无数据"、"暂无公告"、"暂无操作日志"、"暂无购买记录"等
- 没有统一的空状态组件或文案常量

#### 加载状态
- v-loading 指令：19 个文件 30 处（ERP 专用）
- client 端使用自定义 loading 组件（MobileLoading.vue 等）
- 前后端加载状态实现方式不统一

### 4.2 后端代码问题

#### 超大 .ts 文件（36 个文件超过 300 行）

**严重（>1000 行）：**

| 文件 | 行数 | 说明 |
|------|------|------|
| forecast.service.ts | 2625 | AI 预测服务，9处技术性 any（第三方异构响应） |
| ai.controller.ts | 2250 | AI 控制器，4种错误格式混用 |
| schema.ts | 2017 | 数据库 schema，单文件过大 |
| plaza.repository.ts | 1730 | 广场数据仓库 |
| plaza.service.ts | 1445 | 广场服务 |
| proxy.service.ts | 1379 | 代理服务 |
| vip.service.ts | 1296 | VIP 服务 |
| bailian.service.ts | 1082 | 百炼 AI 服务 |

#### 错误处理严重不统一（4 种格式混用）

| 格式 | 使用模块 |
|------|---------|
| `{ success, code, message, data }` | VIP 模块 |
| `{ code, msg, data }` | ERP 模块、proxy、xiuma-sync |
| `{ success, error }` | AI 模块、trade、chat |
| `{ code, message }` | token-stats |

Service 层同样不统一：settlement 用 NestJS 标准 HttpException，vip/erp-order 用原生 `throw new Error()`。

#### Controller 层重复模板代码
几乎所有 controller 方法都重复相同的 try/catch + 日志 + 响应格式，最严重的 vip.controller.ts 有 16 个方法全部重复此模式。

#### any 类型滥用
首轮收敛已完成：生产代码 `any` 由 255 处收敛到 **24 处**（均为有意保留的技术性 any，见 8.4 节）；测试文件中的 any 未纳入治理范围。

- 已收敛：proxy / xiuma-sync（`UploadedMulterFile`、`httpsS.RequestOptions`）、app.module（`Array<DynamicModule | Promise<DynamicModule> | Type<unknown>>`）、plaza.controller `parseMultipartBody`（`Record<string, unknown>` + `str`/`array` 收敛器）、plaza-demand status（`PlazaDemandStatus` 桥接）、feishu-bot（`MessageReceivePayload`）、ai/agent/vip 等相关 repository/service（`Partial<typeof table.$inferInsert>`、`Array<Type<unknown>>`、去冗余强转等）。
- 保留：collect（动态子表映射）、kg（UUID 列告警屏蔽）、forecast（第三方异构响应）、schema/daily-recommend（类型转换辅助），详见 8.4 节。

#### settlement 模块使用内存 mock 存储
6 个 service 文件使用 MockStoreService（JSON 文件内存存储），未接入真实数据库。

### 4.3 文档状态

#### AGENTS.md 与实际代码
- 技术栈版本**完全一致**，无偏差
- 项目结构描述准确

#### 文档时效性
| 文档 | 最后更新 | 状态 |
|------|---------|------|
| AI测价/ | 2026-08-26 | 较新 |
| AI问答系统架构/ | 2026-08-21 | 较新 |
| 智能广场/ | 2026-08-26 | 较新 |
| 结算系统/ | 2026-08-26 | 较新 |
| 个人中心/ | 2026-08-26 | 较新 |
| 项目说明书/ | 2026-08-02~17 | 部分过时 |
| AI配单/ | 2026-07-22 | 较旧，需更新 |
| VIP系统/ | 2026-07-27 | 较旧，需更新 |
| 客服/ | 2026-07-23~27 | 较旧 |
| 数据库迁移/ | 2026-07-30~08-03 | 部分过时 |
| 不锈钢市场使用中心-项目综合文档.md | 2026-07-22 | 较旧 |

#### feishu-env-baseline/（可信文档）
14 个 .md 文件，全部为 2026-08-26~27 经实测验证的环境事实，用户确认真实有效。

---

## 五、夯实基础行动计划（优先级排序）

> 核心思路：先修已有的问题，再做新功能。修的过程本身就是大量 token 消耗。

### 第一阶段：统一基础架构（A类，可直接执行）

| # | 任务 | 优先级 | 预估改动 |
|---|------|--------|---------|
| 1 | **统一 API 响应格式**：定义全局响应拦截器，统一为 `{ code, message, data }` 格式，消除 4 种格式混用 | P0 | 后端全局 |
| 2 | **统一错误处理**：Controller 层抽取全局异常过滤器，消除重复 try/catch 模板代码 | P0 | 后端全局 |
| 3 | **补充 any 类型定义**：已完成首轮收敛，生产 any 由 255 处降至 24 处（技术性 any 保留） | P1 | 已完结 |
| 4 | **统一空状态组件**：抽取统一的 EmptyState 组件和文案常量 | P1 | 前端全局 |
| 5 | **统一加载状态**：定义统一的 loading 指令/组件规范 | P1 | 前端全局 |
| 6 | **统一错误提示**：规范 ElMessage.error 的使用方式和文案格式 | P2 | 前端全局 |

### 第二阶段：拆分超大文件（B类，需确认拆分方案）

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| 7 | **拆分 PersonalProfilePage.vue（3984行）** | P0 | 你明确提到的，拆为多个子组件 |
| 8 | **拆分 PlazaPublishPage.vue（5354行）** | P0 | 最大的前端文件 |
| 9 | **拆分 forecast.service.ts（2625行）** | P0 | 最大的后端文件 |
| 10 | **拆分 ai.controller.ts（2250行）** | P0 | 按功能拆为多个 controller |
| 11 | **拆分 schema.ts（2017行）** | P1 | 按业务域拆分 schema |
| 12 | **拆分其他 >1000 行文件** | P2 | 逐个处理 |

### 第三阶段：清理与优化（A类）

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| 13 | **settlement 模块从 mock 迁移到真实 DB** | P2 | 需确认是否仍需要 |
| 14 | **清理未使用的导入/组件** | P3 | 全局扫描清理 |
| 15 | **UI 交互体验优化** | P2 | 交互逻辑、性能、美观度全面优化 |

### 第四阶段：文档更新（A类）

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| 16 | **更新 AI配单/ 文档** | P1 | 2026-07-22 → 最新 |
| 17 | **更新 VIP系统/ 文档** | P1 | 2026-07-27 → 最新 |
| 18 | **更新项目说明书/ 文档** | P2 | 部分内容过时 |
| 19 | **更新客服/ 文档** | P2 | 2026-07-23 → 最新 |
| 20 | **核实并更新其他过时文档** | P3 | 逐个检查 |

### 第五阶段：未完成功能（B/C类）

> 等前四阶段完成后，再基于《2026-08-10上线工作计划》中的 P1/P2 功能清单逐项推进。
> 具体功能列表见 docs/2026-08-10上线工作计划.md 第三节"后期工作计划"。

---

## 六、执行红线

1. **不猜测用户意图** — 有歧义就暂停问
2. **不引入未授权依赖** — 只用项目已有的
3. **不默默 mock 外部接口** — 必须显式标记
4. **不一次写超过 500 行** — 拆分交付
5. **不跳过类型检查和测试** — 工具兜底是底线
6. **每个子功能完成后 git commit** — 保证可回滚
7. **临时文件任务完成后删除** — 保持工作区干净

---

## 七、可信文档清单

以下目录文档经用户确认真实有效，可作为开发依据：
- `feishu-env-baseline/`（14 个文件，2026-08-26~27 实测验证）
- `docs/AI测价/`（2026-08-26 更新）
- `docs/AI问答系统架构/`（2026-08-21 更新）
- `docs/智能广场/`（2026-08-26 更新）
- `docs/结算系统/`（2026-08-26 更新）
- `AGENTS.md`（技术栈版本与 package.json 完全一致）

---

## 八、全量代码质量侦察报告（2026-08-29）

> 执行方式：基于 Code Smells 和 AGENTS.md 硬约束的语义级静态扫描，非关键词字面匹配。

### 8.1 第一步：架构健康度扫描

#### 上帝类候选（Service > 600 行，共 5 个）

| 文件 | 行数 | 建议 |
|------|------|------|
| `server/modules/ai/forecast.service.ts` | 2625 | P0 — 价格预测引擎，行数是第二名近2倍 |
| `server/modules/plaza/plaza.service.ts` | 1445 | P1 — 广场核心服务，职责过多 |
| `server/modules/proxy/proxy.service.ts` | 1379 | P1 — 代理服务，可能包含多种代理逻辑 |
| `server/modules/vip/vip.service.ts` | 1296 | P1 — VIP/套餐管理，业务复杂度高 |
| `server/modules/ai/bailian.service.ts` | 1082 | P2 — 百炼API封装，含多种调用模式 |

#### Controller 分层违规

| 文件 | 违规类型 | 具体位置 | 说明 |
|------|---------|---------|------|
| `xiuma-sync.controller.ts` | 直接数据库操作 | 第21行注入 DRIZZLE_DB，第129-142行直接构建 Drizzle 查询（含 join） | Controller 不应直接操作数据库 |
| `xiuma-sync.controller.ts` | 直接 Repository 调用 | 第121/247/256/269/281/293行，共6处 | 应下沉到 Service 层 |
| `ai.controller.ts` | 直接 Repository 调用 | 第152/155/219/305/427行，共5处调用 PlazaRepository | 应抽取到独立 Service |
| `ai.controller.ts` | 深层嵌套业务逻辑 | 第954-1001行（4层）、第1297-1374行（4层）、第1424-1448行（4层）、第1474-1492行（4层） | chat方法726行，含完整SSE流式链路+图表/指标/结论卡构建，严重"胖Controller" |

---

### 8.2 第二步：飞书环境专项红线

#### CSRF 保护缺失（P0 级安全风险）

| 文件 | 缺失端点数 | 缺失内容 | 严重程度 |
|------|-----------|---------|---------|
| `client/src/api/settlement.ts` | **19个** POST/PATCH/DELETE | 无 CSRF、无 Authorization | **P0/高危** |
| `client/src/api/chat.ts` | **3个** POST | 无 CSRF、无 Authorization | **P0/高危** |
| `client/src/mobile/pages/ai/MobileAiQa.vue` | 1个 POST | 无 CSRF、无 Authorization | **P0/高危** |
| `client/src/mobile/pages/ai/MobileAiStock.vue` | 2个 POST | 无 CSRF、无 Authorization | **P0/高危** |
| `erp/announcement-admin/api.ts` | **4个** POST | 有 Authorization 但无 CSRF | **P1/中危** |

**settlement.ts 影响的19个端点**：createPartner、updatePartner、deletePartner、getCreditScore、getRating、createContract、updateContract、deleteContract、registerInvoice、aiContractReview、aiContractCompare、createPaymentNode、updatePaymentNode、aiPaymentAnomalyCheck、createAndWriteOff、aiDeliveryAnomalyCheck、recognizeOcr、updateTaxRates、updateBoardLabels

**chat.ts 影响的3个端点**：createSession、sendMessage、closeSession

**风险说明**：飞书妙搭网关对 `/api/*` 路径执行 CSRF 双提交 cookie 校验，缺少 token 返回 HTTP 403。settlement 和 chat 模块的所有写入接口在飞书环境下必然失败。

---

### 8.3 第三步：数据库与异步陷阱

#### 异步循环
server/ 目录中**未发现** `.map(async ...)` 或 `.forEach(async ...)` 模式，异步循环方面是干净的。

#### SQL 迁移与 schema.ts 不一致

| 问题类型 | 影响范围 | 缺失字段数 |
|---------|---------|-----------|
| 8个 price_* 表完全缺少字段注释 | 025~030 SQL文件 | ~155个字段 |
| 12个 dict_* 表审计字段缺注释 | 035 SQL文件 | 48个字段 |
| erp_user_account / report_user_skill 审计字段缺注释 | 052 SQL文件 | 8个字段 |
| **schema.ts 与 SQL 不一致**：`users` 表的 `business_focus` 和 `monthly_sales_volume` 字段在 SQL 中存在但 schema.ts 中缺失 | 001 SQL文件 vs schema.ts | 2个字段 |

**总计**：~213个字段缺少 COMMENT ON COLUMN，1处 schema.ts 与实际数据库结构不一致。

---

### 8.4 第四步：死代码与类型安全

#### any 类型使用 Top 5（生产代码，第一轮收敛后，排除测试文件）

| 排名 | 文件 | 剩余 any | 性质 |
|------|------|---------|------|
| 1 | `server/modules/ai/forecast.service.ts` | 9 | 第三方异构响应与 JSON 解析，技术性保留 |
| 2 | `server/database/collect.repository.ts` | ~9 | 动态子表 `target as any` 映射，技术性保留 |
| 3 | `server/database/kg.repository.ts` | 4 | `inArrayUuid/inArrayType` UUID 列告警屏蔽 |
| 4 | `server/database/schema.ts` | 1 | 类型转换辅助（dayjs↔date） |
| 5 | `server/modules/ai/daily-recommend.service.ts` | 1 | 外部数据驱动行映射 |

> 生产代码剩余 any 合计约 **24 处**，均为有意保留的技术性 any；其余生产 any 已收敛为准确类型（`UploadedMulterFile`、`httpsS.RequestOptions`、`ModuleDefinition` 联合、`MessageReceivePayload`、`PlazaDemandStatus`、`Partial<typeof table.$inferInsert>` 等）。测试文件中的 any 未纳入治理。

#### 僵尸代码
仅发现 **1处**：`server/modules/plaza/plaza.service.ts` 第905-910行，6行旧版飞书妙搭 API 风格的注释代码（`this.text(fields.FLASH_ID)` 等），紧接其后是功能相同的新版代码，可安全删除。

---

### 8.5 侦察报告汇总表

| 严重级别 | 问题分类 | 具体文件路径 | 违规特征描述 | 建议修复方式 |
| :--- | :--- | :--- | :--- | :--- |
| **P0/高危** | CSRF缺失 | `client/src/api/settlement.ts` | 19个POST/PATCH/DELETE端点无CSRF+无Authorization | 统一fetchSettlementApi的headers构造，注入getCsrfToken()和Authorization |
| **P0/高危** | CSRF缺失 | `client/src/api/chat.ts` | 3个POST端点无CSRF+无Authorization | 在chat请求中注入getHeaders() |
| **P0/高危** | CSRF缺失 | `client/src/mobile/pages/ai/MobileAi*.vue` | 3个POST端点无CSRF+无Authorization | 使用mobileRequest替代直接fetch |
| **P0/高危** | 分层违规 | `server/modules/ai/ai.controller.ts` | 2250行胖Controller，5处直调Repository，4处4层嵌套 | 将chat方法拆为独立Service（ChatStreamService），Repository调用下沉 |
| **P0/高危** | 上帝类 | `server/modules/ai/forecast.service.ts` | 2625行，剩9处any | 按职责拆分为ForecastEngine、ForecastDataLoader、ForecastValidator等 |
| **P0/高危** | Schema不一致 | `server/database/schema.ts` vs `001-create-users-table.sql` | users表缺少business_focus和monthly_sales_volume字段 | 补齐schema.ts定义或确认SQL字段已废弃 |
| **P1/中危** | CSRF缺失 | `erp/announcement-admin/api.ts` | 4个POST端点有Authorization但无CSRF | 在fetchJson的headers中注入x-suda-csrf-token |
| **P1/中危** | 分层违规 | `server/modules/xiuma-sync/xiuma-sync.controller.ts` | 直接注入DRIZZLE_DB做join查询，6处直调Repository | 将数据库操作下沉到xiuma-sync.service.ts |
| **P1/中危** | 上帝类 | `server/modules/plaza/plaza.service.ts` | 1445行，职责过多 | 拆分为PlazaPostService、PlazaSearchService等 |
| **P1/中危** | 上帝类 | `server/modules/proxy/proxy.service.ts` | 1379行 | 按代理类型拆分 |
| **P1/中危** | 上帝类 | `server/modules/vip/vip.service.ts` | 1296行 | 拆分为VipPackageService、VipMemberService等 |
| **P1/中危** | 上帝类 | `server/modules/ai/bailian.service.ts` | 1082行 | 拆分为BailianClient、BailianPromptBuilder等 |
| **P1/中危** | 类型安全 | `server/modules/ai/forecast.service.ts` | 剩 9 处技术性 any（第三方异构响应） | 定义 ForecastApiResponse 等接口 |
| **P1/中危** | 类型安全 | `server/database/collect.repository.ts` | 剩 ~9 处动态子表 `target as any` 映射 | 定义 SubRecordQueryResult 等接口 |
| **P1/中危** | 类型安全 | `server/database/ai.repository.ts` | 已收敛为 0 处 any | - |
| **P1/中危** | 类型安全 | `server/database/kg.repository.ts` | 剩 4 处 UUID 列告警屏蔽 | 定义图操作结果类型 |
| **P2/低危** | 缺少字段注释 | `server/database/sql/025~030-*.sql` | 8个price_*表~155个字段缺少COMMENT ON COLUMN | 补充COMMENT ON COLUMN语句 |
| **P2/低危** | 缺少字段注释 | `server/database/sql/035-*.sql` | 12个dict_*表48个审计字段缺注释 | 补充审计字段注释 |
| **P2/低危** | 僵尸代码 | `server/modules/plaza/plaza.service.ts` | 第905-910行，6行旧版注释代码 | 安全删除 |

---

### 8.6 风险总结

如果以上问题不修，上线后最可能崩溃的 **3 个场景**：

1. **结算模块全面 403**：`settlement.ts` 的 19 个写入端点全部缺少 CSRF token，在飞书妙搭网关下必然被拦截返回 403，导致合同创建、付款节点、AI 异常检测等核心业务功能完全不可用。

2. **AI 问答流式响应不稳定**：`ai.controller.ts` 的 chat 方法 726 行内嵌 4 处 4 层嵌套逻辑，SSE 流式链路中图表构建、结论卡提取、内容治理等子系统紧耦合，任一环节异常（如 JSON 解析失败、正则匹配越界）会导致整个流式会话中断，用户看到"AI 无响应"。

3. **价格预测引擎雪崩**：`forecast.service.ts` 2625 行 + 27 处 any 类型，外部数据源（51bxg API）返回格式一旦变化，any 类型绕过编译检查，运行时 undefined 访问直接抛异常，且该 Service 无降级链路，单点故障导致整个测价功能瘫痪。

---

## 九、飞书妙搭环境关键认知（基于 feishu-env-baseline/ 14篇实测文档）

> 以下认知均来自飞书沙箱终端实测，是开发时必须遵循的环境约束。

### 9.1 运行环境本质

| 维度 | 事实 |
|------|------|
| 部署形态 | Linux 容器 + FaaS(BYTEFAAS) + NGINX + supervisor |
| 本地判定 | `isLocal = !process.env.SUDA_DATABASE_URL`，仅凭一个变量 |
| 本地启动 | `dev-local.js`：拉沙箱 .env.local → skills sync → 并发 dev:server + dev:client |
| 沙箱启动 | `dev.js`：保活守护 + 自动重启（指数退避2s→8s）+ 清 dist 强制全量重编译 |
| 生产启动 | dist/ 下 `node server/main.js`（cwd=dist） |
| 模板栈 | `fullstack-nestjs-template` 2.2.5，含 26 个 `@lark-apaas/*` 平台包 |

### 9.2 CSRF 双提交机制（开发必知）

**完整链路**：
```
页面 GET → CsrfTokenMiddleware 种 suda-csrf-token cookie (httpOnly:false, 30天)
         → ViewContextMiddleware 注入 req.__platform_data__.csrfToken
         → 前端脚本读 cookie 或 __platform_data__ 拿到 token
API POST  → 前端带 header x-suda-csrf-token = token
         → CsrfMiddleware 校验 header == cookie → 失败返回 403
```

**对开发的约束**：
- 所有 POST/PUT/PATCH/DELETE 请求**必须**携带 `x-suda-csrf-token` header
- token 从 `document.cookie` 的 `suda-csrf-token` 读取，或从 `getCsrfToken()` 工具函数获取
- 首次访问必须先请求页面（触发种 cookie），否则 API 请求必然 403
- 这是侦察报告中 settlement.ts（19个端点）和 chat.ts（3个端点）缺 CSRF 的底层原因

### 9.3 CLIENT_BASE_PATH 前缀机制

**事实**：
- `CLIENT_BASE_PATH = /app/app_4k9x70cg0jws9/`
- `configureApp` 内部调用 `app.setGlobalPrefix(CLIENT_BASE_PATH)`
- 所有 Controller 路由自动挂在此前缀下：`/app/app_4k9x70cg0jws9/api/xxx`
- 平台中间件用 `stripBasePath2` 剥前缀后再路由

**历史 bug 根因**：AuthGuard 用 `startsWith('/api/')` 判断放行时，若基于未剥前缀的原始 path（`/app/xxx/api/...`），会失配 → 误判需登录 → 401。修复方式：AuthGuard 必须基于剥前缀后的路径判断。

### 9.4 RLS 安全模型（数据库访问）

**事实**：
- 飞书启用 PG Row-Level Security
- 每个请求经 `SqlExecutionContextMiddleware` 注入：
  - `SET LOCAL app.user_id = '{userId}'`
  - `SET ROLE 'service_role_' / 'authenticated_' / 'anon_' + roleSchema`
  - `SET LOCAL app.role_ids = '{roles}'`
  - `SET LOCAL app.user_type = '{userType}'`
- 表若开启 RLS，POLICY 按会话参数过滤行

**对开发的约束**：
- `req.userContext` 来自请求头 `suda_web_user`（网关注入的 URI 编码 JSON）
- 若请求头缺失 → userId 为空 → RLS 落到 `anon_` 角色 → 查不到业务数据
- "线上取不到数"的排查顺序：① 检查 `suda_web_user` 头是否注入 ② 检查 RLS POLICY 是否匹配 ③ 检查 roleSchema 是否配置

### 9.5 依赖裁剪风险（prune-smart.js）

**事实**：
- 构建时 `@vercel/nft` 静态追踪入口文件的 import 依赖
- 只保留可追踪的包，其余全部剪掉
- BFS 递归补充子依赖 + actionPlugins 机制
- 动态 import 的包若未被静态追踪，会被剪掉

**对开发的约束**：
- 新增后端依赖后，必须确保被静态 import 或写入 `.env` 的 `MIAODA_RUNTIME_ENTRIES`
- 若线上出现"本地跑得好好的但部署后 MODULE_NOT_FOUND" → 大概率被 prune 剪了
- 排查顺序：prune 剪没剪 → exportsOnly 影响 → 子依赖 BFS 是否捞到

### 9.6 构建与部署注意事项

| 事项 | 说明 |
|------|------|
| build:client OOM | 飞书沙箱必须加 `NODE_OPTIONS=--max-old-space-size=4096` |
| devserver 假缺包 | Node 模块解析缓存陈旧，重启 devserver 即恢复 |
| 发布约束 | 发布跑的是**当前分支远端 HEAD**，本地未 commit/push 不进产物 |
| 禁止异步 deploy | `&`/nohup/后台 task 会让命令提前返回，Agent 误判已完成 |
| schema.ts 生成 | `@lark-apaas/db-schema-sync@latest --export-custom-types` |
| nest-cli.json | `deleteOutDir: false`（必须，否则 nest build 清掉 dist） |
| body limit | configureApp 默认 1mb → main.ts 覆盖为 20mb（业务需要） |

### 9.7 平台中间件矩阵（请求生命周期）

```
请求进入
  → cookieParser
  → legacy-path-redirect（旧路径兼容）
  → public-assets（dist/client 静态直出，排除 PLATFORM_PREFIXES）
  → Nest Router: setGlobalPrefix(/app/xxx) 剥前缀 → 匹配 Controller
  → PlatformModule 中间件矩阵:
      ├ apiResponseInterceptor         /api/*,/openapi/*    (res.render→404 JSON 护栏)
      ├ UserContextMiddleware          /*                   (从 suda_web_user 头解析平台用户)
      ├ RequestContextMiddleware        /*                   (请求上下文)
      ├ LoggerContextMiddleware         /*                   (日志上下文)
      ├ ObservableTraceMiddleware       /*                   (可观测链路)
      ├ SqlExecutionContextMiddleware   /*                   (RLS SET ROLE/SET LOCAL，受 DISABLE_DATAPASS 门控)
      ├ CsrfTokenMiddleware            页面(非api)          (种 CSRF cookie)
      ├ ViewContextMiddleware           页面(非api)          (注入 __platform_data__ + 应用元数据)
      ├ HtmlHotUpdateViewMiddleware    页面(非api)          (生产 HTML 热更新)
      └ CsrfMiddleware                 /api/*               (校验双提交，失败 403)
  → GlobalExceptionFilter（全局异常）
  → GlobalAuthGuard（业务鉴权，401）
  → Controller → Service → DB (带 RLS 会话)
```

### 9.8 环境变量关键项（只列键名，不落值）

| 分类 | 键名 |
|------|------|
| 数据库 | `SUDA_DATABASE_URL`、`DATABASE_URL` |
| AI 业务 | `BAILIAN_API_KEY`、`BAILIAN_APP_ID`、`BAILIAN_ENABLE_THINKING`、`BAILIAN_FORECAST_*` |
| 外部接口 | `BXG_API_HOST`、`XIUMA_API_HOST`、`XIUMA_API_PORT` |
| 前端开关 | `VITE_TOKEN_EXPIRE_DAYS`、`VITE_REQUIRE_AUTH`、`VITE_SHOW_QUICK_MODE` |
| ERP | `ERP_ADMIN_USER`、`ERP_ADMIN_PASSWORD` |
| 飞书 | `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_OAUTH_REDIRECT_URI` |
| 极验 | `GEETEST_CAPTCHA_ID`、`GEETEST_CAPTCHA_KEY` |
| 平台框架 | `FORCE_FRAMEWORK_*`（build loose/lint loose/datapass/environment） |
| 前缀 | `CLIENT_BASE_PATH`（= `/app/app_4k9x70cg0jws9/`） |

---

## 十、飞书环境专项复核（基于第九节认知的二次扫描）

### 10.1 AuthGuard 前缀处理 — **已正确处理，无风险**

`server/common/guards/auth.guard.ts` 第 27-28 行：
```typescript
const rawPath: string = request.path || request.url || '';
const path: string = rawPath.replace(/^\/app\/app_[^/]+/, '');
```
基于剥除后的 `path` 判断 `startsWith('/api/erp/')`，且有单元测试覆盖前缀场景。

### 10.2 RLS 安全模型 — **主动绕过，设计决策**

- 项目使用 `postgres` 驱动直连 `SUDA_DATABASE_URL`，不走 datapaas 通道
- 平台 `SqlExecutionContextMiddleware` 注入的 `SET LOCAL` / `SET ROLE` 对本项目查询无效
- 行级隔离通过代码层面 `WHERE member_code = ${memberCode}` 实现
- **风险**：若飞书平台未来对表强制开启 RLS policy，当前所有查询将受影响

### 10.3 suda_web_user 请求头 — **未使用，无风险**

- 项目完全不读取 `suda_web_user`，建立独立鉴权体系（自签 token + HMAC-SHA256）
- 平台 `UserContextMiddleware` 注入的 `req.userContext` 被业务 AuthGuard 覆写
- 下游控制器统一通过 `req.headers['x-user-id']`（AuthGuard 写入）获取用户身份
- `@UserId()` 装饰器有回退链（userContext → header → body），`@Public()` 路由需注意伪造风险

---

## 十一、工作内容总览（待办清单）

> 基于《2026-08-10上线工作计划》《岗位职责分工计划书》和代码质量侦察报告整合。

### 11.1 基础设施修复（我来做，A类）

| # | 任务 | 优先级 | 涉及文件 | 说明 |
|---|------|--------|---------|------|
| 1 | 修复 settlement.ts CSRF 缺失 | P0 | `client/src/api/settlement.ts` | 19个端点缺 CSRF+Authorization，飞书环境必然403 |
| 2 | 修复 chat.ts CSRF 缺失 | P0 | `client/src/api/chat.ts` | 3个端点缺 CSRF+Authorization |
| 3 | 修复移动端 CSRF 缺失 | P0 | `MobileAiQa.vue`、`MobileAiStock.vue` | 3个端点缺 CSRF+Authorization |
| 4 | 修复 erp/announcement-admin CSRF 缺失 | P1 | `erp/announcement-admin/api.ts` | 4个端点有 Authorization 但无 CSRF |
| 5 | 统一 API 响应格式 | P0 | 后端全局 | 4种格式混用 → 统一为 `{ code, message, data }`。✅ **试点(settlement)已完成并实测通过**：新增 `shared/envelope.ts` 统一信封，settlement.controller 去掉 success、切到共享 `ok()`；前端 settlement.ts 改 `code===0` 推导+错误 message 提取。✅ **批次1(auth/behavior/feedback)已完成并实测通过**：新增共享失败信封 `fail()`；auth.service/feishu-auth.exchange/behavior.controller/feedback.controller 的 `{code,msg,data}` 全部切到共享 `ok()/fail()`、`msg`→`message`；前端 auth.ts/behavior.ts、ai.ts 的 `aiRequest` 解包对齐 `message`；auth e2e 5 用例通过、type:check 通过、全量 143 用例通过（另 2 个 ai 套件为预存在的 PipelineService 三参签名失败，与本批无关）。✅ **批次2(vip/announcement)已完成**：vip.controller（20+端点）从 `{success,code,message,data}` 全部切到共享 `ok()/fail()`（保留 401/400/404/-1 状态码，`confirmPayment` 原缺 code 一并补齐）；announcement.controller（`@Res` 显式状态）切到 `ok()/fail()` 并保留 HTTP 状态码；前端 vip.ts/announcement.ts 已按 `code===0` 归一化，无需改动。✅ **批次3(全局异常过滤器)已完成**：`exception.filter.ts` 从 `{error:{code,message,details,...}}` 改为统一失败信封 `{code,message,data:null}`（code 取数值 HTTP 状态码，与成功信封 `code===0` 及 vip/announcement 的 `fail(msg, 状态码)` 对齐）；前端 settlement.ts 错误解包收敛为仅读 `body.message`（移除旧 `body.error` 兼容分支）；axios/Error 双路径均可被统一过滤，全量 143 用例通过、type:check 通过。✅ **批次2补充(ai)已完成**：`ai.controller`（2067 行）路由处理器的 `{success,data}/{success,error}` 全部切到共享 `ok()/fail()`（77 处 + 导入未登录分支 1 处归一化），`v1/forecast`/`v1/forecast/export` 返回类型注解改为 `ApiEnvelope<...>`；SSE 流式（`chat`/`plaza-search-insight/stream`/`v1/forecast/stream`）、`@Res` 调试端点（`test`/`auto-test`）、私有辅助函数 `plazaSearchFallback` 均保留不动；前端 `aiRequest` 本就兼容双格式无需改动，type:check 通过。✅ **批次4(分页低风险对齐)已完成**：盘点全文分页返回，`announcement.service.list` 已为 `{total,items}` 服务端分页，补齐 `page/pageSize` → 符合契约 `{items,total,page,pageSize}`，前端结构性兼容；`settlement/contract` 本已合规；`sales-pipeline` 为全量非分页（`hasMore:false`），不强行造分页元数据；`xiuma-sync/{total,rows}` 属 ERP `{code,msg,data}` 信封范围留待信封统一；plaza 及多仓库 `{rows,total}/{list,total}` 与前端深度耦合，留待全量统一。✅ **分页全量统一(对外契约层)已完成**：plaza 是主要对外分页契约遗留，`plaza.service.ts` 的 `PlazaFeedData` 由 `{NEWS_DATAS,TOTAL_NUM}` 改为 `{items,total,page,pageSize}`（6 处返回点：getMyFavorites/getMyFollows/getMyFollowers/getMyLikes/getMyHistory/loadPosts），前端 `plaza.ts` 的 `RawPlazaFeedData` 与全部读取字段同步为 `items/total`，最终组件层 `{items,total}` 契约不变；仓库层 `{rows,total}` 为内部结构、由 service 消费转换，非对外分页契约、不纳入；✅ **xiuma-sync ERP 信封统一已完成（续做）**：`xiuma-sync.controller.ts` 全部 12 端点由 ERP `{code,msg,data}` 统一为内部信封 `ok()/fail()`，data 内层结构（list `{total,rows}`、search `DATAS/TOTAL_NUM` 第三方兼容结构）保持不变；前端 `erp/xiuma-data-import/index.vue`（4 处）与 `erp/contact-stats/index.vue`（1 处）`json.msg`→`json.message`，`client/src/api/proxy.ts` 的 xiuma-sync search 本地解包 `result.msg`→`result.message`；`fetchProxyApi` 读 `msg` 仍为 51bxg/秀吗 第三方透传、保留。type:check 通过、全量 143 用例通过（2 个 ai 套件为既有 PipelineService 三参签名失败，与本次无关）。✅ **前端 api 封装收敛**：对后端已统一信封的 wrapper 移除死亡 `success` 分支——`announcement.ts` 成功判定收紧为 `code===0`、错误消息读 `result.message`；`vip.ts` 成
功判定收紧为 `code===0`；`auth/behavior/settlement` 批次中已收敛；`aiRequest` 非SSE 已走 `code!==0`+`message`（`test/auto-test` 调试端点返回 `{success,message}` 无 `code`，`success` 分支为防御保留）。type:check 通过。✅ **后端4模块统一+前端收敛（本轮）**：`chat.controller` 全部响应切 `ok()/fail()`（SSE `stream` 端点排除）；`trade.controller` 新增 `toEnvelope()` 在 HTTP 边界把 service 层 `{success,data,error}` 映射为信封；`plaza.controller` 全部 `{code:0,msg,data}` 切 `ok()` 并修 plaza 图片端点的 3 处裸 `{code,msg}` 残留为 `fail()`；`plaza-demand.controller`（`@Res` 模式）成功切 `res.json(ok())`、失败切 `res.status().json(fail())`。对应前端 `plaza.ts` 成功判定收紧为 `code===0`、错误消息读 `message`（移除 `msg` 旧分支与 `success` 双格式）；`trade.ts` 新增 `unpack()` 将 `{code,message,data}` 转为页面层依赖的 `{success,data,error}`，保持历史调用方不变；`chat.ts` 成功判定 `code===0`、读 `message`。`proxy` 属第三方透传（51bxg/秀吗）排除在信封外；✅ **proxy 内部失败信封字段名收尾（本轮）**：`proxy.controller.ts` 自建的 3 处失败返回 `{code:-1,msg,data:null}`（参数缺失/文件上传失败/已停用认证接口）统一 `msg`→`message`，与内部信封 `{code,message,data}` 对齐（第三方透传的 forward 结构不动）；前端 `client/src/api/proxy.ts` 第 82、382 行读取改为「优先 `message`、回退第三方 `msg`」。type:check:server+client 通过。详见 `dev-output/docs/接口统一改造-前端api封装收敛-2026-08-29.md` |
| 6 | 统一错误处理（抽取全局异常过滤器） | P0 | 后端全局 | 消除 Controller 层重复 try/catch 模板。✅ **已完成（本轮）**：新增 `server/common/utils/error-handler.ts` 的 `runAsync({logger,label,successMessage,failCode}, fn)` 助手，统一封装「try { service → ok } catch { log → fail }」，void 结果归一为 `data:null`；`vip.controller.ts` 14 处重复 try/catch 全部切到 `runAsync`，成功 code=0/文案、失败 failCode（confirmPayment=400 其余 -1）、getPurchaseDetail 404 分支、confirmPayment 结果映射均保真，getAvatar(@Res 二进制) 保留；其余 Controller 为异构模式（@Res 固定500/ai SSE/plaza 特判）不强转换避免过度工程。日志统一追加 `err=` 前缀。前端零影响。type:check 通过、全量 143 用例通过（2 个 ai 套件为既有 PipelineService 三参签名失败，与本次无关）。详见 `dev-output/docs/接口统一改造-优化项6-Controller统一错误处理-2026-08-29.md`（commit 90da33b） |
| 7 | 补充 any 类型定义 | P1 | forecast.service.ts 等 | 255处 any，优先处理生产代码。✅ **批次1(forecast.service)已完成**：新增 `PricePoint`（DB/51bxg 价格单点结构）、`UsageInfo`（百炼 usage）接口；`structured/priceStructured` 10+ 处 `any[]`→`PricePoint[]`、库存 `DATAS as any[]`→`PricePoint[]`、新闻 `DATAS as any[]`→`Array<{Title,CreateTime}>`、`lastUsage/extractForecastUsage`→`UsageInfo`、`catch(e:any)`→`(e:unknown)`（日志 instanceof 归一化），27处 any→9处；保留 `ForecastJsonExports`8 个 AI 任意 JSON 字段与 1 处 Drizzle 类型逃逸作后续。纯类型收紧、运行时行为不变。type:check:server 通过、全量 143 用例通过（forecast-persist 通过，2 个 ai 套件为既有 PipelineService 三参签名失败）。详见 `dev-output/docs/接口统一改造-优化项7-补充any类型-批次1-forecast-2026-08-29.md`（commit 7aca6d4）。**批次2(collect/ai repository)已完成**：4 个已知表检索方法 `Promise<any[]>`→精确 `$inferSelect` 别名（searchEvents/Analysis/DailyPrices/ConfirmedContent→Event/Analysis/DailyPrice/ContentRecord），`updateArticleStatus` 去冗余 `as any`；ai.repository `conditions:any[]`→`SQL[]`、7 处 raw SQL `(rows as any[])`→`Array<Record<string,unknown>>`；collect 16→11、ai 10→2（保留动态子表/动态 updates 等技术性 escapes）。纯类型收紧、运行时不变。type:check:server 通过、143 用例通过（2 个 ai 套件为既有 PipelineService 基线失败）。详见 `dev-output/docs/接口统一改造-优化项7-补充any类型-批次2-collect-ai-repo-2026-08-29.md`（commit 1af24b9） |
| 8 | 统一空状态组件 | P1 | 前端全局 | 30+文件80处变体 → 抽取 EmptyState 组件。✅ **已完成（抽取组件+同构试点）**：新增 `client/src/components/EmptyState.vue`（props `icon/title/desc/outerStyle` + 操作区插槽，保留品牌视觉与渐变按钮），结构完全同构的 `PersonalPackagePage.vue`（3 处）与 `VipMyPackagePage.vue`（4 处）全部切到统一组件，各删冗余样式约 52 行；剩余页（AiStock/PersonalPlaza/PersonalFeedback/PersonalProfile/ContractManage）空态结构异构，本轮不强改防过度工程。type:check:client 通过。详见 `dev-output/docs/UI优化-优化项8-前端空状态组件抽取-2026-08-29.md` |
| 9 | 统一加载状态 | P1 | 前端全局 | v-loading + 自定义 loading 混用。✅ **已完成（组件抽取+纯文字加载块试点）**：新增 `client/src/components/LoadingState.vue`（props `variant`＝`block`白底卡片／`bare`纯居中、`text`，品牌色 Loader2 旋转图标 + 文字，rotation 用 `transform: rotate` 专用过渡规避 `transition:all`），将纯文字/自研加载块落地到 `PersonalContactsPage.vue`（`variant="block"`）、`UserProfilePage.vue`（2 处）、`PersonalProfilePage.vue`（作品/点赞/收藏/观看历史 4 处 tab + 关注弹窗 1 处），删除各页冗余样式（`.profile-loading`、`.post-grid-loading`、`.follow-loading`）；`PersonalProfilePage.vue` 的孤儿 `EmptyState` 导入一并清除。按钮级 loading 仍用 `Loader2 + animate-spin` 内联、非全局重构待后续；v-loading 区域与加载体量大、本轮试点后量产待评估。type:check:client 通过 |
| 10 | 清理僵尸代码 | P2 | `plaza.service.ts:905-910` | ✅ **已完成**：`plaza.service.ts` `getSharePreview` 内 6 行被注释的旧版代码（基于旧 `fields`/`member` 变量的 type/Name/TITLE/summary/likeCount/commentCount 实现）已随 commit `f857c83`（2026-08-29 08:36）删除，当前文件无残留僵尸注释代码 |
| 11 | 补齐 schema.ts 缺失字段 | P1 | `server/database/schema.ts` | ✅ **已完成**：`users` 表补上 DB 已存在但声明缺失的 `business_focus`（`businessFocus varchar(20)`）与 `monthly_sales_volume`（`monthlySalesVolume numeric`），与 `001-create-users-table.sql`（54-55 行建列、107-108 行注释）及 `vip.repository`/`plaza.repository` 既有 raw SQL 读写对齐；纯声明补齐、无 DDL 变更，type:check:server 通过 |
| 12 | 补充 SQL 字段注释 | P2 | `025~030-*.sql`、`035-*.sql` | ✅ **已完成**：为 8 个 SQL 文件补齐字段 `COMMENT ON COLUMN`（共 173 + 5 个表注释）：025 三张卷板价格表各补除 price_date 外 20 列（3×20）、026 宏旺表全 21 列（price_unit 为文本类型单独标注）、027/028/029 库存表各 12 列、030 历史预测结果表 8 列、035 十二张 dict 表各补 4 个审计字段（_created_at/_updated_at/_created_by/_updated_by，12×4=48）；仅补注释、无 DDL 结构变更，已用事务回滚方式对本地库验证全部文件语法通过（CREATE/INDEX 因表已存在跳过的 NOTICE 属正常） |
| 13 | 统一错误码定义 | P1 | `shared/envelope.ts` + 各 controller | ✅ **已完成（抽取语义常量）**：`shared/envelope.ts` 新增错误码常量 `BIZ_ERROR=-1`/`BAD_REQUEST=400`/`UNAUTHORIZED=401`/`FORBIDDEN=403`/`NOT_FOUND=404`/`INTERNAL_ERROR=500`（`OK_CODE=0` 沿用，码值与既有 HTTP 语义一致、不改值，前端零影响），`fail()` 默认码改用 `BIZ_ERROR`；将 `announcement.controller`/`vip.controller`/`plaza-demand.controller` 中散落的 `res.status(N)` 与 `fail(..., N)` 魔法数字全部替换为常量（含 `vip.runAsync` 的 `failCode:400`），controller 层已无裸数字失败码。type:check:server 通过 |

### 11.2 超大文件拆分（我来做，B类，需确认方案）

| # | 文件 | 行数 | 拆分思路 |
|---|------|------|---------|
| 13 | `forecast.service.ts` | 2625 | ✅ **已完成**：按职责拆为三份——`forecast-data-loader.ts`（F1，取数：价格/库存/资讯/成本基准）、`forecast-validator.ts`（F2，解析/校验/兜底/技术指标/基准价）、`forecast-engine.ts`（F3，多因子预测序列生成/历史图表构建/价格事件检测/支撑阻力/8个JSON导出）。`forecast.service.ts` 收窄为编排 + AI 调用（取数、指标、Prompt 构建、百炼调用、P4-5 落库），由 2625 行降至约 835 行，剩 `any` 也随拆分同步收敛。type:check:server 通过、forecast-persist.spec 3 用例通过（commit `f857c83` 前后、`d83eca0`/`28fcc51`） |
| 14 | `ai.controller.ts` | 2250 | ✅ **已完成**：新建 `chat-stream.service.ts`（ChatStreamService）承载 `/api/ai/chat` 的 SSE 流式问答核心（fast/expert 双流程、pipeline 编排、结构化图表/指标/结论、输出治理、Token/聊天记录落库、错误兜底）。`ai.controller.ts` 的 `chat` 缩为薄委托（约 21 行），删除随之成孤儿的 import/注入（PipelineService、AiThinkingDisplayService、AiGovernanceService 仅 chat 使用）。随后收口 5 处直接调用 PlazaRepository→下沉至新服务 `ai-plaza-data.service.ts`（AiPlazaDataService，封装 getSearchRecommendationCandidates/getUserProfile/searchPostsPage），`ai.controller.ts` 不再直连 Repository。文件由 2250 行降至约 1490 行。验证：type:check:server 通过；chart-sse-order / structured-insight-sse / structured-message-flow 三个 SSE 时序套件转指向 `chat-stream.service.ts` 后全部通过（14 用例）；review agent 比对确认 chat 逻辑零改动、分层正确。已知 2 个 AI 套件失败为既有 PipelineService 构造函数签名基线（与本次无关） |
| 15 | `PlazaPublishPage.vue` | 5354 | 🔄 **进行中**：步骤一（供需发布表单）已完成——新建 `DemandPublishForm.vue`（供需表单模板 + demandForm 状态/常量/submitDemand 等方法），父组件用 `<DemandPublishForm v-else-if @toast>` 替换并移除重置弹窗，删孤儿状态/常量/函数与 import（icon `Send/Package/Ruler/MapPin/Layers/Zap/Settings/TrendingUp`、`publishPlazaDemand`、`usePlazaStore`/`plazaStore`）。步骤二（编辑器工具栏）已完成——新建 `EditorToolbar.vue`（格式按钮模板 + `editorTools` 常量 + `EditorTool` 类型，通过普通 `<script>` 块导出），父组件用 `<EditorToolbar @exec="execFormat" />` 替换原工具栏模板，`execFormat`/`insertTable`（依赖 articleEditorRef 与文章状态）留在父组件、签名改为结构类型解耦，移除 9 个工具栏专属 icon（Bold/Italic/Underline/Strikethrough/Quote/List/ListOrdered/Minus/Table）。每次验证：type:check:client 通过。待续：媒体上传区/预览区/标签选择/发布设置/AI助手侧栏/草稿箱抽屉等子组件拆分 |
| 16 | `PersonalProfilePage.vue` | 3984 | → 拆为资料编辑/头像/企业信息等子组件 |
| 17 | `AiStockPage.vue` | 4384 | → 拆为搜索表单/匹配结果/供应商详情等子组件 |
| 18 | `PlazaShellPage.vue` | 3024 | → 拆为信息流/侧栏/推荐等子组件 |
| 19 | 其他 >1000 行文件 | — | 逐个处理 |

### 11.3 分层违规修复（我来做，B类）

| # | 文件 | 违规 | 修复方式 |
|---|------|------|---------|
| 20 | `ai.controller.ts` | 5处直调 PlazaRepository | ✅ **已完成**：下沉至 `ai-plaza-data.service.ts`（AiPlazaDataService），Controller 不再直连 Repository |
| 21 | `xiuma-sync.controller.ts` | 直接注入 DRIZZLE_DB + 6处直调 Repository | 下沉到 xiuma-sync.service.ts |

### 11.4 文档更新（我来做，A类）

| # | 文档 | 当前日期 | 说明 |
|---|------|---------|------|
| 22 | `docs/AI配单/` | 2026-07-22 | 较旧，需根据当前代码更新 |
| 23 | `docs/VIP系统/` | 2026-07-27 | 较旧，需更新 |
| 24 | `docs/客服/` | 2026-07-23 | 较旧，需更新 |
| 25 | `docs/项目说明书/` | 2026-08-02 | 部分过时 |

### 11.5 P1 功能开发（9/10前，按分工计划）

| # | 功能 | 负责人 | 我的角色 | 说明 |
|---|------|--------|---------|------|
| 26 | AI 配单匹配准确度提升 | 我 | 主开发 | LLM 打分参数调优 + 降级链路验证 |
| 27 | AI 配单数据源覆盖补全 | 我 | 主开发 | 缺的钢种/供应商 |
| 28 | ~~AI 配单保交付最小链路~~ | ~~我~~ | — | **不做**，涉及外部接口，用户明确跳过 |
| 29 | 广场消息提醒 | 夏康乐 | 终验 | 关注/点赞/评论通知中心 |
| 30 | 广场收藏功能接入 | 夏康乐 | 终验 | 表已迁移，前端未接 |
| 31 | VIP 购买流程校验 | 夏康乐 | 终验 | 下单/支付/回调全链路回归 |
| 32 | AI 问答图表增强 | 黄颖 | 终验 | 结构化图表生成 |
| 33 | AI 问答关联广场帖子 | 黄颖 | 终验 | 回答关联广场帖子/历史问答 |
| 34 | 移动端重构 | 王雪照 | 终验 | TDesign 三阶段（骨架→样板→铺开） |
| 35 | AI 测价 P1 功能 | 朱铮勋 | 终验 | 预测vs实际对比/导出/多参数对比 |
| 36 | 结算系统 | 许晓雨 | 终验 | 独立推进 |
| 37 | **ERP 权限分级**（新增） | 我 | 主开发 | 可配置的菜单权限系统，详见 13.5 |

### 11.6 C类事项（需用户手动处理）

| # | 事项 | 说明 |
|---|------|------|
| 38 | 老平台数据接口申请 | 需跨部门协调，只能你做 |
| 39 | 线上数据库清理 | 清理旧测试数据 + 真实业务数据混存 |
| 40 | KPI/OKR 定制 | 给每人做考核指标 |

---

## 十二、功能扩展说明（基于上线工作计划的补充思考）

> 以下是对《2026-08-10上线工作计划》中 P1/P2 功能的扩展描述，结合代码现状给出具体想法。

### 12.1 AI 测价 — P1 功能扩展

**预测 vs 实际对比**：当前 `forecast.service.ts` 已有 `price_history_results` 表存储历史预测结果。扩展思路：在预测完成后自动创建一个"回填任务"，7天后提醒用户输入实际价格，系统自动计算偏差率并生成对比报告。可复用现有的 ECharts 组件做预测曲线 vs 实际曲线的叠加展示。

**结果导出**：利用 `html2canvas` 或 Puppeteer（飞书环境已内置）将预测结果页截图导出为图片。考虑到飞书环境有 Puppeteer（`BROWSER_EXECUTABLE_PATH` 已配置），可以用服务端截图方案，质量更高。

**多参数对比预测**：在 `AiPredictPage.vue` 中增加"对比模式"，左右两栏各放一个预测表单，共享同一个时间轴 ECharts 图表，用不同颜色区分两条预测曲线。后端只需复用现有预测接口调用两次。

### 12.2 AI 配单 — P1 功能扩展

**保交付最小链路**：当前配单结果展示后，用户需要手动去秀吗下单。最小链路：在配单结果的供应商卡片上加一个"立即采购"按钮，点击后跳转到秀吗商品详情页并携带订单参数（钢种、规格、数量）。需要与秀吗 API 对接商品详情 URL 生成。这个功能涉及外部接口（C类），需要你确认秀吗的跳转 URL 格式。

**匹配准确度提升**：当前 `ai.controller.ts` 的 `scoreMatches` 方法使用 qwen-turbo 做4维评分。优化方向：① 增加 few-shot 示例（用历史成功匹配案例做 few-shot）② 调整评分维度权重（当前4维等权，可按用户采购场景动态调整）③ 增加降级链路（LLM 超时 → 规则引擎兜底评分）。

### 12.3 智能广场 — P1 功能扩展

**消息提醒**：当前 `plaza_notifications` 表已建好，`plaza-notification.service.ts`（268行）已有基础实现。需要做的是前端通知中心页面（铃铛图标 + 未读红点 + 通知列表）。建议复用 `PlazaShellPage.vue` 的侧栏空间，在顶部导航栏加铃铛图标，点击展开通知下拉面板。

**收藏功能接入**：`plaza_favorites` 表已迁移，后端 `plaza.service.ts` 已有收藏相关方法。前端需要在帖子详情页加收藏按钮，在个人中心加"我的收藏"列表页。改动量不大，主要是前端对接。

**会员个人主页**：`UserProfilePage.vue`（637行）已有基础骨架。需要补全：用户发布的帖子列表、互动统计（获赞/关注/粉丝）、企业标签展示。后端需要新增聚合查询接口。

### 12.4 VIP 系统 — P1 功能扩展

**购买流程稳定性校验**：当前 VIP 购买流程涉及 `vip.service.ts`（1296行）和 `PaymentFlowModal.vue`（479行）。需要全链路回归：选择套餐 → 创建订单 → 支付（模拟）→ 回调确认 → 套餐生效 → 权限刷新。重点检查支付回调的幂等性和异常恢复。

**个人中心功能补全**：当前个人中心有多个页面（PersonalProfilePage/PersonalPackagePage/PersonalAccountPage 等），需要逐一校验：资料编辑是否保存成功、我的套餐是否正确显示、账号管理是否完整、Token 统计是否准确。

### 12.5 ERP 后台 — P1 功能扩展

**公告与消息推送**：方案已在 `docs/erp/08-公告与消息推送` 中设计完成。核心：ERP 后台公告管理（CRUD + 发布/撤回）→ 前端通知中心展示 → 顶部横幅公告。`erp-announcement-admin.service.ts`（399行）已有基础实现，需要补全前端展示层。

**AI 用量计费层**：方案已在 `docs/erp/07-AI用量统计与计费` 中设计完成。核心：按用户/模型/时间段统计 Token 消耗 → 成本计算 → 账单大盘。`erp-token-stats.service.ts` 已有基础统计，需要扩展为完整的计费模型。

### 12.6 用户画像 — P0 功能扩展

**引导页采集**：`OnboardingModal.vue`（2293行）已实现引导流程。需要确认：首次进入是否正确触发、采集的数据是否写入 `user_profiles` 表、后续推荐是否使用了画像数据。

**行为记忆采集**：`behavior.service.ts`（110行）+ `behavior.controller.ts`（47行）已有基础。需要确认：问答/配单/测价/广场行为是否都被正确记录、记录频率是否合理、存储是否影响性能。

### 12.7 AI 客服 — P1 功能扩展

**AI 客服自动应答**：`chat.service.ts`（141行）+ `feishu-bot.service.ts`（194行）已有基础。核心逻辑：用户输入 → 匹配 FAQ 知识库 → 百炼生成回答 → 返回。需要补全：FAQ 知识库的维护界面（ERP 侧）、回答质量监控、转人工触发条件的精确判断。

**转人工策略**：当 AI 连续 2 次无法回答（置信度低于阈值）或用户输入"人工"时，自动转接飞书 Bot。需要在 `chat.service.ts` 中增加对话轮次计数和关键词检测逻辑。

---

## 十三、开发执行约束（用户明确要求）

### 13.1 数据与测试约束

| 约束 | 说明 |
|------|------|
| **禁止硬编码 mock 数据** | 可以用模拟数据测试，但代码中绝对不能残留硬编码的 mock 数据。提交前必须检查 |
| **本地数据库为测试库** | 可以在数据库中伪造假数据进行测试（如 AI 配单的挂单数据） |
| **测试账号** | 前台：13800000000 / 13800000001 / 13800000002，密码均为 test1234；ERP：admin / admin |
| **测试方式** | 使用 Trae 内置浏览器模拟登录后测试相关功能 |

### 13.2 提交与留痕约束

| 约束 | 说明 |
|------|------|
| **提交节奏** | 每个最小步骤：执行 → 测试 → 测试通过 → git commit |
| **留痕要求** | 安装依赖、修改配置文件、关键决策必须留痕，用户醒来后要检查 |
| **B/C 类任务** | 先自主处理，用模拟数据跑通。遇到不确定的，留文档记录疑问，等用户醒来决定 |
| **不能改了不管** | 每次改动必须测试验证，遗留问题必须留痕 |

### 13.3 UI 与框架约束

| 约束 | 说明 |
|------|------|
| **PC 端 UI 风格** | 保持与当前项目一致，PC 端前端 UI 全部手写，保持风格统一 |
| **ERP 系统** | 使用 Element Plus（饿了么框架库），必须统一使用 |
| **前台移动端** | 必须使用 TDesign（腾讯框架库），不能自己手写、不能重复造轮子 |
| **ERP 无移动端** | ERP 系统不需要移动端适配 |

### 13.4 功能取舍约束

| 功能 | 决策 |
|------|------|
| **AI 配单 — 保交付最小链路** | **不做**（涉及外部接口对接，用户明确跳过） |
| **AI 配单 — 测试** | 可在数据库伪造假挂单数据，在前台进行配单测试 |
| **智能广场** | 按文档继续做，购买流程可以继续 |
| **AI 客服** | **暂不做跨应用测试**（涉及飞书机器人，用户电脑他人要用）。等所有其他工作做完后再考虑 |
| **ERP 权限分级** | **新增功能**，需单独做（详见 13.7） |

### 13.5 数据库连接

| 项 | 值 |
|---|---|
| 连接地址 | `postgresql://postgres:admin@127.0.0.1:5432/bxg_app` |
| 数据库名 | `bxg_app` |
| 用户名 | `postgres` |
| 密码 | `admin` |
| 端口 | `5432` |
| .env 配置 | `DATABASE_URL=postgresql://postgres:admin@127.0.0.1:5432/bxg_app` |

### 13.6 文档查阅与产出规范

**查阅旧文档**：
- 开发某功能前，先去 `docs/` 目录查看是否有相关模块的说明文档
- `docs/` 下按功能模块建了子文件夹，每个文件夹内有开发过程的解决方案说明
- **注意**：这些文档可能已过时或需要调整，仅作为参考（了解当时的设计思路和完成程度），不能完全信赖

**产出新文档**：
- **不要修改 `docs/` 目录下的任何文件**
- 开发过程中产出的所有内容（脚本、测试文件、说明文档），统一放在一个**单独的文件夹**中
- 建议文件夹名：`dev-output/`（放在项目根目录下）
- 子目录建议：`dev-output/scripts/`（脚本）、`dev-output/tests/`（测试）、`dev-output/docs/`（说明文档）
- 方便用户醒来后集中查看，不会东一个西一个找不到

### 13.7 新增功能：ERP 后台权限分级

> 用户明确提出，原文档中未包含此功能。

**需求概述**：
- 当前 ERP 只有 admin 一个账号，拥有全部权限
- 需要做权限分级：不同账号看到不同菜单，admin 全部可见
- 权限分级本身要做成**可配置的**：admin 在 ERP 后台有一个专门的菜单项来配置每个账号的权限
- 配置完成后刷新页面，菜单动态显示/隐藏

**设计思路**：
1. **数据库**：新增 `erp_users` 表（id, username, password_hash, role, permissions JSON, created_at）
2. **后端**：新增 `erp-permission` 模块，提供权限 CRUD 接口
3. **前端**：ERP 侧栏菜单根据当前用户的 permissions 动态过滤
4. **配置界面**：在 ERP 后台新增"权限管理"菜单，admin 可以给每个账号分配可见菜单列表
5. **测试账号**：需要新建模拟账号用于测试不同权限级别（安装后留痕）

### 13.8 设计图生成

> 用户询问是否可以用 Trae 的 design 模式出设计图再转 UI。

**现状**：Trae 有 `电脑控制` MCP 工具可以操作电脑，有 `Frontend Design` skill 可以做 UI 设计。
**方案**：对于需要设计图的功能（如 ERP 权限管理页面），先用 Frontend Design skill 出设计稿，确认后再写代码。

### 13.10 双 Agent 校验策略

> 核心策略：放弃"全量生成"，改为"契约式填充 + 双Agent校验"

**为什么需要**：单 Agent 写代码容易遗漏 NestJS 依赖注入规则、Drizzle schema 约束、飞书 CSRF 规则等项目上下文。

**执行方式**：
1. **写代码 Agent（我）**：按精确的文件路径 + 上下文写代码，输出严格限定在指定文件
2. **审查 Agent（Task subagent）**：读取我刚写的代码，检查以下维度：
   - TypeScript 类型是否严格（无新增 any）
   - Drizzle 查询是否异步（await）
   - SQL 是否幂等（IF NOT EXISTS）
   - CSRF token 是否正确注入
   - 是否符合项目现有代码风格
   - 是否有硬编码 mock 数据
3. **修复**：审查 Agent 返回问题清单 → 我修复 → 再 commit

**适用场景**：所有 B 类任务（涉及业务逻辑的代码修改）必须走双 Agent 校验。A 类任务（简单修复）可跳过。

**代价**：Token 消耗约翻倍，但质量显著提升。

### 13.11 会话断连风险

**问题**：MIMO V2.5 PRO 模型不稳定，会话可能中途断开。Trae 会话断开后无法自动恢复。
**应对措施**：
1. **频繁 commit**：每完成一个最小功能就 commit，断连后可从上次 commit 继续
2. **进度留痕**：每次在文档中记录当前进度和下一步计划
3. **任务拆小**：每个任务控制在可在一个会话内完成的范围内
4. **断连恢复清单**：如果断连，恢复后先读本执行方案文档第十三节，找到上次进度标记继续

---

## 十四、当前进度标记

> 每次结束工作前更新此节，记录当前进度和下一步计划。

**最后更新**：2026-08-29
**当前状态**：
- ✅ 登录500错误已修复（vite代理 3000→8000）
- ✅ CSRF 修复全部完成（settlement 19端点 / chat 3端点 / 移动端3端点 / ERP公告4端点）
- ✅ 僵尸代码清理完成
- ✅ 类型检查通过（前后端）

**下一步计划**：
- ⏸ #5 统一API响应格式 / #6 统一错误处理：**高风险，需用户在场终验**（涉及全后端，可能破坏现有功能）
- ⏸ schema.ts 缺失字段：**红区**，需用户拍板（涉及DB结构）
- ⏸ 超大文件拆分：B类，需走双Agent校验，建议用户确认优先级
- 详细留痕见：`dev-output/docs/工作日志-2026-08-29.md`

### 执行顺序（用户最终确认）

1. **第一阶段：代码结构优化**（不改变业务功能）
   - 先做基础设施修复（CSRF、响应格式、错误处理）
   - 再做超大文件拆分
   - 再做分层违规修复
   - 最后做 UI 统一（空状态、加载状态等）

2. **第二阶段：功能新增与更新**（优化完成后再做）

### UI 改进优先级（用户最终确认）

| 页面 | 改进要求 |
|------|---------|
| 个人中心 | 需要好好改 UI |
| 前台移动端 | 需要好好改 UI（太丑陋） |
| 其他前台页面 | 不用改 |
| ERP 界面 | 用 Element Plus 正常开发 |

### 设计图生成

对于需要改 UI 的功能（个人中心、移动端），先用 Design 模式出设计图，再写代码。
