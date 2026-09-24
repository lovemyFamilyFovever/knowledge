---
title: "deliver-03-three-links-defense"
tags: []
source: "desktop"
collected: "2026-09-24"
status: "imported"
---

# 能守卡 03 · 数据库迁移 / AI 配单 / WAF 逆向（三条链路，基于真实代码）

> 证据：`server/common/services/waf-bypass.service.ts`、`docs/AI配单/02-匹配引擎规则.md`(9/6 刷新)、`server/database/sql/0xx-*.sql`(001–086+)、`server/database/manual-schema.ts`、`docs/AI问答系统架构/`。
> ⚠️ 本卡最重要的部分是每节末尾的**"数字级陷阱"**——我核对代码发现简历素材里有几处和真实实现**不一致**,不修会在技术面当场穿。

---

# 链路 A · WAF 逆向（你的"问题求解"高光）

## 电梯
"我们数据要从 51bxg 老平台接口取，但接口被阿里云 WAF 拦。老技术负责人不给权限、教不了，我自己啃：先**识别 WAF 挑战页**,再用 **jsdom 执行挑战页那段混淆 JS 算出 cookie**,带 cookie 回头把请求发出去,把接口打通。后来不放心'绕过'会不会被反制,再查文档定位到**配阿里云白名单**的正解,拿着方案让运维配好——从 hack 绕过升级到正规配置。"

## 逐层
- **L2 怎么识别挑战页**：响应 HTML 里含 `aliyun_waf_aa` / `aliyun_waf_bb` / `acw_sc__v2` / `aliyunwaf` 标记,即判定为挑战页(`isChallenge`)。
- **L2 怎么"算"出 cookie**：把挑战页 HTML 丢进 `new JSDOM(html, { url, referrer, runScripts:'dangerously', resources:'usable' })`,让那段混淆 JS 在模拟浏览器里真跑一遍,读完从 `dom.window.document.cookie` 取出 WAF 下发的验证 cookie,再复用去请求真实接口。`runScripts:'dangerously'` 是"允许执行脚本"的关键开关。
- **L3 为什么用 jsdom / 风险**：因为挑战本质是"执行一段 JS 生成 cookie",纯 HTTP 客户端不会执行 JS,所以要一个能跑 JS 的无头 DOM 环境;jsdom 足够且轻。风险是**WAF 换算法就得跟着调**,所以我后续推动白名单正规化(不再依赖绕过)。
- **L3 抽象能力**：这段后来我从 `ProxyService` 里**抽成独立的 `WafBypassService`**,给代理和认证复用——顺手体现重构/分层意识。

## ⚠️ 陷阱
- 别说成"破解了阿里云"。准确口径:"识别挑战页 + 在 jsdom 里执行它的验证脚本拿 cookie,属于把浏览器行为自动化;最终解法是配白名单正规放行"。**诚实反而更专业,也别碰法律敏感措辞("绕过风控/入侵")**。
- 被追"为什么不用真无头浏览器(Puppeteer/Playwright)"→ 答:"目标只是执行一段 JS 拿 cookie,jsdom 更轻、无需起浏览器进程;若挑战要真实渲染/指纹才需要上 Puppeteer。"

---

# 链路 B · AI 配单（LLM 直通，非规则引擎）

## 电梯
"配单不是写规则去匹配商品,而是**LLM 直通**两步:① `parse-enquiry-params` 用 qwen-turbo 把采购的自然语言('无锡要 50 吨 304 冷轧,预算 1.6 万以内')解析成结构化参数;② `score-matches` 把搜索回来的候选(前 **100 条**)喂给 qwen-turbo,让它按**五维 100 分制**打分、选出**最多 15 条**并给分层推荐理由。为什么不用规则引擎——不锈钢规格/材质/场景的组合判断规则写不完、也迭代不动,交给大模型理解 + 打分,迭代快得多。"

## 逐层
- **L2 五维是哪五维**(简历写的"四维"是**错的**,见陷阱)：`materialMatch 材质/表面/规格`、`priceAdvantage 价格竞争力`、`locationMatch 仓库距离(本地100/同省80/跨省50/未指定60)`、`stockLevel 库存满足度`、`creditLevel 供应商会员等级(钻石100…无等级50)`。Prompt 里还塞了领域规则(厚度 ±0.3mm 公差算正常、大厂太钢宝钢加分、"面议"给中等分)。
- **L2 输出怎么落**：要求模型**直接返回纯 JSON**(不套 markdown),后端用正则 `\{[\s\S]*\}` 抠首个 JSON 再 `JSON.parse`,校验 `ranked` 是数组。推荐理由**分三档**(前5名180–220字/6-10名80-120字/11-15名10-20字)。
- **L3 挂了怎么办(关键)**：**两层 Fallback**——① 后端 `scoreMatches` 的 catch:LLM 失败/JSON 抠不出/`ranked` 缺失时不抛错,退回 candidates 前 3 条、score=0 的结构;② 前端 `doSearch` 再包一层 catch:请求本身失败也用前 3 条零分兜底。**保证页面永不白屏**。
- **L3 为什么"最多15、最少1"**：宁可少选也不给不匹配的;不足 15 全返回、低匹配给低分即可。

## ⚠️ 陷阱（必改）
1. **简历素材写"四维 100 分制",真实代码是"五维"(多了 `creditLevel 会员等级`)**。→ 统一改成**五维**,否则面试官问"哪四维"你张口就来错。
2. **别把它讲成"搜索引擎/推荐算法"**——本质是"检索出候选 + LLM 打分排序"。诚实讲"排序/打分开销给了大模型,我做的是候选构造、prompt 工程和兜底链路"。
3. 被追"LLM 打分不稳定/幻觉怎么办"→ 用上面两层 Fallback + "最少 1 条、纯 JSON 校验" 来答,**别说'很准不会错'**。

---

# 链路 C · 数据库工程化与迁移（你的 SQL/运维长板复活）

## 电梯
"数据库这块是我的主场(早期做运维死磕 Oracle 出身)。AI 金在飞书妙搭上,平台会**自动重写 `schema.ts`**,我建了 `manual-schema.ts` 手工维护表定义**摆脱平台覆盖**;建表全部走**编号化幂等 SQL 迁移脚本(001 一路到 086+)**;做过一次**表前缀规范化(033 rename 迁移 + 配套 rollback 回滚脚本)**;早期聊天记录/Token 统计写在飞书多维表格(Bitable),8 月**统一迁到 PostgreSQL + Drizzle**,不再依赖 Bitable 的环境差异。"

## 逐层
- **L2 幂等怎么做**：迁移脚本用 `create table if not exists` / 先删后写(`data_forecast` 落库:`forecastType='P'`+同材质+同周期+同模型+pending 时先删旧再写,防重复入库);命名 `0xx-create-xxx.sql` 顺序编号。
- **L2 为什么要 manual-schema**：飞书妙搭平台每次会用自动生成的 `schema.ts` 覆盖,把我手工加的列冲掉 → 我把表定义拆到独立的 `manual-schema.ts`,平台不碰它,保证类型和字段定义稳定(还配套解决过 SVN 冲突、合并两套表)。
- **L2 表前缀规范**：`erp_/data_/ai_/plaza_` 等前缀统一业务域,`033-rename-table-prefixes` 一次性重命名 + `033-rollback-...` 可回滚——**体现"迁移要可逆"**的工程习惯。
- **L3 RLS/安全**：飞书环境用 datapaaS 的 **RLS 行级安全模型**与 provider 机制(见 `feishu-env-baseline/10-datapaas-RLS`),我摸清楚了本地 `DATABASE_URL` + `DRIZZLE_DB` 与飞书 `SUDA_DATABASE_URL` 注入的**双环境差异**(`isLocal = !SUDA_DATABASE_URL`)。

## ⚠️ 陷阱（**上简历前必须核实**）
- **简历素材里的"26→22 张表 / 成功率 99.96% / 34,159/34,174 条"这几个精确数字,我在仓库 docs 和代码里都没查到出处**。→ 要么你回去翻当时的迁移执行日志拿到真实数,要么简历**别写这些具体百分比**。**虚报一个查无实据的数,恰恰是我们说好的"不编"红线**——数据库这条是你的真长板,不需要靠一个编的数字撑场面。
- 被追"PostgreSQL 和 Oracle 差异"→ 用你运维老底讲分页(ROWNUM vs OFFSET/FETCH)、空值(NVL/COALESCE)、递归/层级(Connect by vs WITH RECURSIVE)即可,**这是你能反杀的舒适区**。

---

## 收尾：这三条给你的一句话
- **WAF**：受限/无支持环境下把不可能变可能的解决问题能力(最稀缺)。
- **配单**：会用 LLM 做业务 + 懂兜底工程化,不是只会调 API。
- **数据库**：把 Oracle 老底子平移到 PG + 工程化(幂等/可回滚/双环境),是你能"降维打击普通前端"的护城河。

## 全局待修（汇总进简历重写）
1. 配单"四维"→**五维**;
2. 迁移"99.96%/26→22/34159"→ **核实后再写,拿不到真实出处就删**;
3. WAF 用"识别挑战页+jsdom 执行验证脚本取 cookie+推动白名单"的**中性技术措辞**,不碰"破解/绕过风控"字眼。
