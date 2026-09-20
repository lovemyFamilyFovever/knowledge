# 本地权威数据库基准（target）

> 导出时间：2026-08-25T14:30:43.441Z
> 表总数：80

## 全表清单（简便表 + 行数估算 + RLS）

| 表名 | schema | 列数 | 行数估算 | RLS | 主键 | 注释 |
|---|---|---:|---:|:--:|---|---|
| ai_chat_records | public | 15 | 196 |  | id | AI 对话记录：会话/问答/图表/token 消耗留痕 |
| ai_feedbacks | public | 18 | 0 |  | id | AI 回答反馈：用户对 AI 回答的纠错/评价，一条消息仅一条反馈 |
| ai_jin_auth_credentials | public | 11 | 0 |  | id | AI金本地账号凭据；与 users 通过 MEMBER_CODE 1:1 关联 |
| ai_jin_verification_codes | public | 11 | 0 |  | id | AI金注册、短信登录和重置密码的本地验证码 |
| ai_token_records | public | 13 | 114 |  | id | AI token 消耗按日统计：按日期+用户+类别聚合，供配额与用量报表使用 |
| batch_daily_token | public | 4 | 0 |  | day | 批量处理当日 token 用量日账（P4-2 熔断预算落库，051） |
| content_accounts | public | 10 | 0 |  | id |  |
| content_platforms | public | 12 | 0 |  | id |  |
| content_publish_tasks | public | 18 | 20 |  | id |  |
| content_tasks | public | 15 | 15 |  | id |  |
| data_analysis | public | 39 | 0 |  | id | 采集标注系统-分析表（A 事件解读 / B 数据解读合并一表；抽取模板 P2 扩 |
| data_articles | public | 23 | 65 |  | id | 采集标注系统-原始文章表（原文存储+去重+任务容器，一篇文章可挂多条业务子记录） |
| data_content | public | 19 | 0 |  | id | 采集标注系统-生成内容产物表（独立于 data_articles，多平台多风格草 |
| data_content_citations | public | 10 | 231 |  | id | 采集标注系统-生成内容与素材业务记录的引用关系（一对多，支撑来源追溯与 BASE |
| data_daily_price | public | 35 | 42 |  | id | 采集标注系统-每日价格（数据轨，AI 直通 active，低置信度转 draft |
| data_events | public | 35 | 0 |  | id | 采集标注系统-事件表（业务子记录，挂 data_articles 任务容器） |
| data_forecast | public | 37 | 0 |  | id | 采集标注系统-预测表（P 价格/Q 库存/R 需求产量合并一表；抽取模板 P2  |
| data_monthly_production | public | 35 | 0 |  | id | 采集标注系统-每月产量（数据轨，月频；抽取模板 P2 扩展） |
| data_quarterly_demand | public | 32 | 0 |  | id | 采集标注系统-每季度需求量（数据轨，季频；抽取模板 P2 扩展） |
| data_weekly_inventory | public | 33 | 0 |  | id | 采集标注系统-每周库存（数据轨，周频；抽取模板 P2 扩展） |
| dict_analysis_type | public | 9 | 0 |  | id | 采集标注系统-解读类型字典 |
| dict_article_images | public | 9 | 0 |  | id | 采集标注-文章图片表（压缩后二进制，独立于文章正文存储，dict_ 前缀统一 E |
| dict_article_style | public | 9 | 0 |  | id | 采集标注系统-文章风格字典 |
| dict_channel | public | 9 | 0 |  | id | 采集标注系统-分发渠道字典 |
| dict_entity_alias | public | 10 | 0 |  | id | 采集标注系统-实体别名唯一真源（alias→standard_name 映射；k |
| dict_event_category | public | 10 | 0 |  | id | 采集标注系统-事件大类字典（A-G 七大类） |
| dict_event_sub_category | public | 10 | 91 |  | id | 采集标注系统-事件子类字典（关联大类 code，01 文档 3.3 全量枚举） |
| dict_forecast_model | public | 9 | 0 |  | id | 采集标注系统-预测模型字典 |
| dict_grade | public | 9 | 16 |  | id | 采集标注系统-钢种/品种字典（304/316L/201 等） |
| dict_impact_direction | public | 9 | 0 |  | id | 采集标注系统-影响方向字典（利多/利空/中性，事件 E10 判断字段） |
| dict_industry_category | public | 9 | 0 |  | id | 采集标注系统-品类字典（不锈钢/铜/碳钢等） |
| dict_inventory_type | public | 9 | 0 |  | id | 采集标注系统-库存类型字典 |
| dict_market | public | 9 | 0 |  | id | 采集标注系统-市场字典（无锡市场/佛山市场等） |
| dict_region | public | 9 | 0 |  | id | 采集标注系统-区域字典（华东/华南/全国合计等） |
| dict_source_name | public | 9 | 0 |  | id | 文章来源名称词典（ERP 后台统一维护，用户可管理） |
| dict_tax_status | public | 9 | 0 |  | id | 采集标注系统-含税状态字典 |
| dict_unit | public | 9 | 0 |  | id | 采集标注系统-计价单位字典（元/吨/元/千克/元/张） |
| erp_user_account | public | 8 | 0 |  | username | ERP 登录账号表（本地化账号，密码暂明文） |
| feishu_user_bindings | public | 11 | 0 |  | id | 飞书 OAuth 登录用户绑定表：飞书 open_id 与 AI金 MEMBER |
| import_batch_runs | public | 21 | 0 |  | id | P4 存量批量处理-批次运行日志（登记/体检/运行/门禁/成本/熔断全程留痕） |
| import_batch_samples | public | 10 | 0 |  | id |  |
| import_staging | public | 13 | 50 |  | id | P4 存量批量处理-导入暂存表（用户灌库旧平台 CSV，import_ 前缀独立 |
| kg_entities | public | 18 | 64 |  | id | 采集标注系统-知识图谱节点表（行业实体 + 业务记录节点，业务记录入库时同步建节 |
| kg_relations | public | 15 | 118 |  | id | 采集标注系统-知识图谱关系边表（全系统关系唯一真源；同对节点同类型允许多条，re |
| platform_sessions | public | 11 | 1 |  | id |  |
| plaza_ai_helpers | public | 10 | 0 |  | id | 广场 AI 小工具调用记录：标题/摘要等辅助生成能力的调用留痕 |
| plaza_comment_likes | public | 5 | 5 |  | id | 广场评论点赞：同一用户对同一评论仅一条（comment_id+member_co |
| plaza_comments | public | 12 | 739 |  | id | 广场评论：支持楼中楼回复（reply_comment_id），comment_i |
| plaza_demands | public | 30 | 0 |  | id | 供需信息：用户发布的求购/供应信息，为 AI 配单提供数据来源 |
| plaza_favorites | public | 5 | 2713 |  | id | 广场收藏：同一用户对同一帖子仅一条（member_code+news_id 唯一 |
| plaza_follows | public | 5 | 12243 |  | id | 广场关注：用户对用户的关注关系（member_code+follow_membe |
| plaza_images | public | 6 | 1868 |  | id | 广场作品图片：按 news_id 关联 plaza_posts；历史图片保存 i |
| plaza_likes | public | 5 | 10384 |  | id | 广场帖子点赞：同一用户对同一帖子仅一条（news_id+member_code  |
| plaza_notifications | public | 17 | 0 |  | id | 广场消息中心通知事件：关注/点赞/评论/收藏通知与每周互动汇总，按 aggreg |
| plaza_posts | public | 21 | 4459 |  | id | 广场帖子：内容社区主表，news_id 为帖子业务 ID |
| plaza_questions | public | 13 | 0 |  | id | 广场问答：提问与采纳答案记录，question_id 为问题业务 ID |
| plaza_videos | public | 11 | 1515 |  | id | 广场视频：flash_id 为视频业务 ID，可被 plaza_posts.fl |
| price_baogangdesheng_304_no1 | public | 21 | 0 |  | id | 卷板价格明细：宝钢德盛 304 NO.1（SheetCoilSettingCod |
| price_ningbobaoxin_430_2b | public | 21 | 0 |  | id | 卷板价格明细：宁波宝新 430 2B（SheetCoilSettingCode= |
| price_taigangbuxiu_304_2b | public | 21 | 0 |  | id | 卷板价格明细：太钢不锈 304 2B（SheetCoilSettingCode= |
| report_user_skill | public | 4 | 0 |  | username | 周期报告-账号级定制 skill（写作风格提示词，每账号一份） |
| sales_pipeline_records | public | 17 | 0 |  | id | 销售全链路：订单签约/收款/交付/开票状态跟踪（结算系统） |
| site_feedback | public | 18 | 301 |  | id | 站点意见反馈：Bug 上报/功能建议等用户反馈，图片存 site_feedbac |
| site_feedback_images | public | 5 | 153 |  | id | 反馈截图：site_feedback 的附件图片二进制存储 |
| sys_api_error_logs | public | 15 | 649 |  | id | API 错误日志：后端异常留痕，供问题排查与错误趋势分析 |
| trade_contact_view_logs | public | 9 | 0 |  | id | 联系方式查看日志：单钢种每日限次计算与审计留痕 |
| trade_deal_records | public | 18 | 0 |  | id | 站内交易成交记录：用户反馈「已成交」后生成，商品立即从搜索结果过滤 |
| trade_negotiation_actions | public | 7 | 0 |  | id | 站内交易轻量议价动作记录（同意/还价/确认意向） |
| trade_view_rules | public | 6 | 0 |  | id | 站内交易规则配置（单行表，统一数据源控制限次/时限/违约阈值） |
| user_behavior_records | public | 7 | 621 |  | id | 用户行为记录：浏览/搜索等行为留痕，供 AI 画像与最近浏览使用 |
| user_profiles | public | 12 | 12 |  | id | 用户画像扩展表：AI 画像与行为统计，与 users 按 member_code |
| user_recent_views | public | 10 | 107 |  | id | 最近浏览：按用户+目标类型+目标 ID 聚合，重复浏览累加 view_count |
| users | public | 33 | 0 |  | id | 用户主表：AI金 / 51bxg 存量用户的本地账号档案，member_code |
| vip_features | public | 10 | 0 |  | id | VIP 权益能力定义：按 capability_id 与套餐关联，控制路由/功能 |
| vip_member_relations | public | 9 | 0 |  | id | VIP 成员关系：企业套餐主账号（owner）与子账号成员的归属关系 |
| vip_operation_logs | public | 9 | 0 |  | id | VIP 后台操作日志：套餐管理/订单处理等操作留痕与审计 |
| vip_packages | public | 13 | 0 |  | id | VIP 套餐定义：等级/价格/账号数/可见性/联系方式查看配额 |
| vip_purchase_records | public | 16 | 0 |  | id | VIP 套餐购买记录：订单/支付状态/会员有效期，status 变更驱动会员开通 |
| xiuma_member_contact | public | 18 | 26771 |  | id | 秀吗会员联系方式：CRM 会员联系方式页面导出，货品导入时按公司名回填电话 |
| xiuma_product_snapshot | public | 43 | 3011 |  | id | 秀吗货品快照：每日从秀吗 ERP 导出导入，AI金 配单读本表 |

> 行数估算来自 `pg_class.reltuples`（未 `ANALYZE` 可能偏小），非精确 count。