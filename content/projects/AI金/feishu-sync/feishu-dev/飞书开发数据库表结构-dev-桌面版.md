# 飞书开发数据库（dev）表结构

> 导出时间：2026-08-25
> Schema：`workspace_aadkdvw4kawau`
> 总计：39 张业务表

---

## 1. ai_chat_records — AI 聊天记录

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| session_id | varchar | | | 会话 ID |
| message_id | varchar | ✓ | | 消息 ID |
| member_code | varchar | | | 用户 MEMBER_CODE |
| question | text | ✓ | | 用户提问 |
| answer | text | ✓ | | AI 回答 |
| charts_json | text | ✓ | | 图表 JSON |
| answer_mode | varchar | ✓ | | 回答模式 |
| token_consumed | numeric | ✓ | 0 | Token 消耗 |
| chat_time | timestamptz | ✓ | | 聊天时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |
| title | varchar | ✓ | | 会话标题 |
| model_name | varchar | ✓ | | 模型名称 |
| status | varchar | ✓ | 'active' | 状态 |

**索引**：PK `id`、UNIQUE `message_id`、`session_id`、`member_code`、`chat_time`

---

## 2. ai_feedbacks — AI 反馈记录

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| session_id | varchar | | | 会话 ID |
| message_id | varchar | | | 消息 ID |
| feedback_type | varchar | | | 反馈类型 |
| question | text | ✓ | | 用户提问 |
| answer | text | ✓ | | AI 回答 |
| answer_mode | varchar | ✓ | | 回答模式 |
| model_name | varchar | ✓ | | 模型名称 |
| data_sources | text | ✓ | | 数据来源 |
| page_url | text | ✓ | | 页面 URL |
| client_info | text | ✓ | | 客户端信息 |
| member_code | varchar | ✓ | | 用户 MEMBER_CODE |
| feedback_tags | text | ✓ | | 反馈标签 |
| feedback_text | text | ✓ | | 反馈文本 |
| submit_status | varchar | ✓ | '成功' | 提交状态 |
| feedback_time | timestamptz | ✓ | | 反馈时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `message_id`、`session_id`、`feedback_type`、`message_id`

---

## 3. ai_jin_auth_credentials — AI金本地账号凭据

> 与 users 通过 MEMBER_CODE 1:1 关联

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| member_code | varchar | | | 用户 MEMBER_CODE |
| mobile | varchar | ✓ | | 手机号 |
| legacy_password_hash | varchar | ✓ | | 老平台 Pwd 原值（MD5 UTF-8 原始字节的 Base64），首次迁移后清空 |
| password_hash | text | ✓ | | AI金本地 scrypt 密码哈希 |
| password_algo | varchar | | 'legacy_md5_base64' | 密码算法 |
| password_migrated_at | timestamptz | ✓ | | 密码迁移时间 |
| _created_at | timestamptz | | now() | 审计：创建时间 |
| _updated_at | timestamptz | | now() | 审计：更新时间 |
| _created_by | varchar | | 'system' | 审计：创建人 |
| _updated_by | varchar | | 'system' | 审计：更新人 |

**索引**：PK `id`、UNIQUE `member_code`、UNIQUE `mobile`（WHERE mobile IS NOT NULL）、`password_algo`

---

## 4. ai_jin_verification_codes — AI金本地验证码

> AI金注册、短信登录和重置密码的本地验证码

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| mobile | varchar | | | 手机号 |
| purpose | varchar | | | 用途 |
| code_hash | varchar | | | 验证码哈希 |
| expires_at | timestamptz | | | 过期时间 |
| consumed_at | timestamptz | ✓ | | 使用时间 |
| attempt_count | integer | | 0 | 尝试次数 |
| _created_at | timestamptz | | now() | 审计：创建时间 |
| _updated_at | timestamptz | | now() | 审计：更新时间 |
| _created_by | varchar | | 'system' | 审计：创建人 |
| _updated_by | varchar | | 'system' | 审计：更新人 |

**索引**：PK `id`、`expires_at`、`(mobile, purpose, _created_at DESC)`

---

## 5. ai_token_records — AI Token 用量统计

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| date_key | date | | | 日期 |
| member_code | varchar | | | 用户 MEMBER_CODE |
| category | varchar | | | 分类 |
| call_count | numeric | | 1 | 调用次数 |
| total_tokens | numeric | | 0 | 总 Token |
| input_tokens | numeric | | 0 | 输入 Token |
| output_tokens | numeric | | 0 | 输出 Token |
| cached_tokens | numeric | | 0 | 缓存 Token |
| cache_creation_tokens | numeric | | 0 | 缓存创建 Token |
| last_active_at | timestamptz | ✓ | | 最后活跃时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `(date_key, member_code, category)`、`category`、`date_key`、`member_code`

---

## 6. feishu_user_bindings — 飞书 OAuth 用户绑定

> 飞书 open_id 与 AI金 MEMBER_CODE 的一对一绑定

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 UUID |
| member_code | varchar | | | AI金用户 MEMBER_CODE，一个账号仅绑定一个飞书身份 |
| feishu_open_id | varchar | | | 飞书应用内用户 ID（open_id），唯一 |
| feishu_union_id | varchar | ✓ | | 飞书企业内用户 ID（union_id），可为空 |
| feishu_name | varchar | ✓ | | 飞书显示名（授权时快照） |
| feishu_avatar_url | text | ✓ | | 飞书头像 URL（授权时快照） |
| feishu_mobile | varchar | ✓ | | 飞书绑定手机号（授权时快照，需手机号权限） |
| _created_at | timestamptz | | now() | 审计：创建时间 |
| _updated_at | timestamptz | | now() | 审计：更新时间 |
| _created_by | varchar | | 'system' | 审计：创建人 |
| _updated_by | varchar | | 'system' | 审计：更新人 |

**索引**：PK `id`、UNIQUE `member_code`、UNIQUE `feishu_open_id`、`feishu_mobile`

---

## 7. plaza_ai_helpers — 广场 AI 助手记录

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| session_id | varchar | | | 会话 ID |
| message_id | varchar | | | 消息 ID |
| member_code | varchar | ✓ | | 用户 MEMBER_CODE |
| helper_type | varchar | | | 助手类型 |
| question | text | ✓ | | 提问 |
| answer | text | ✓ | | 回答 |
| token_consumed | numeric | ✓ | 0 | Token 消耗 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `message_id`、`helper_type`、`member_code`

---

## 8. plaza_comment_likes — 评论点赞

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| comment_id | varchar | | | 评论 ID |
| member_code | varchar | | | 用户 MEMBER_CODE |
| create_time | timestamptz | ✓ | | 点赞时间 |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`、UNIQUE `(comment_id, member_code)`、`comment_id`、`member_code`

---

## 9. plaza_comments — 评论

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| comment_id | varchar | | | 评论 ID |
| article_id | varchar | | | 文章/帖子 ID |
| member_code | varchar | | | 用户 MEMBER_CODE |
| content | text | ✓ | | 评论内容 |
| reply_comment_id | varchar | ✓ | | 回复的评论 ID |
| is_reply | varchar | ✓ | | 是否回复 |
| status_id | varchar | | '10-正常' | 状态 |
| like_count | numeric | | 0 | 点赞数 |
| create_time | timestamptz | ✓ | | 评论时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `comment_id`、`article_id`、`comment_id`、`member_code`

---

## 10. plaza_demands — 广场供需信息

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| demand_no | varchar | | | 供需编号 |
| member_code | varchar | | | 用户 MEMBER_CODE |
| demand_type | varchar | | | 供需类型 |
| title | varchar | | | 标题 |
| content | text | ✓ | | 内容 |
| material_code | varchar | ✓ | | 材质代码 |
| grade | varchar | ✓ | | 等级 |
| spec_code | varchar | ✓ | | 规格代码 |
| surface_code | varchar | ✓ | | 表面代码 |
| thickness | numeric | ✓ | | 厚度 |
| width | numeric | ✓ | | 宽度 |
| length | numeric | ✓ | | 长度 |
| quantity | numeric | ✓ | | 数量 |
| quantity_unit | varchar | ✓ | '吨' | 数量单位 |
| weight | numeric | ✓ | | 重量 |
| price | numeric | ✓ | | 价格 |
| price_unit | varchar | ✓ | '元/吨' | 价格单位 |
| location | varchar | ✓ | | 所在地 |
| factory_name | varchar | ✓ | | 钢厂名称 |
| house_name | varchar | ✓ | | 仓库名称 |
| supplier_name | varchar | ✓ | | 供应商名称 |
| province_name | varchar | ✓ | | 省份 |
| city_name | varchar | ✓ | | 城市 |
| tags | text | ✓ | '[]' | 标签 JSON |
| parsed_params | jsonb | | '{}' | 解析后的参数 |
| status | varchar | | 'approved' | 状态 |
| expired_at | timestamptz | ✓ | | 过期时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `demand_no`、`material_code`、`city_name`、`house_name`、`supplier_name`、`created_at`、`(demand_type, status)`、`(price, status)`

---

## 11. plaza_favorites — 收藏

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| member_code | varchar | | | 用户 MEMBER_CODE |
| news_id | varchar | | | 帖子/内容 ID |
| tuck_time | timestamptz | ✓ | | 收藏时间 |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`、UNIQUE `(member_code, news_id)`、`member_code`、`news_id`

---

## 12. plaza_follows — 关注

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| member_code | varchar | | | 关注者 MEMBER_CODE |
| follow_member | varchar | | | 被关注者 MEMBER_CODE |
| follow_time | timestamptz | ✓ | | 关注时间 |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`、UNIQUE `(member_code, follow_member)`、`member_code`、`follow_member`

---

## 13. plaza_images — 广场图片

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| news_id | varchar | | | 帖子 ID |
| image_path | text | ✓ | | 图片路径 |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`、`news_id`

---

## 14. plaza_likes — 点赞

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| news_id | varchar | | | 帖子 ID |
| member_code | varchar | | | 用户 MEMBER_CODE |
| create_time | timestamptz | ✓ | | 点赞时间 |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`、UNIQUE `(news_id, member_code)`、`member_code`、`news_id`

---

## 15. plaza_notifications — 广场通知

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| recipient_member_code | varchar | | | 接收人 MEMBER_CODE |
| actor_member_code | varchar | ✓ | | 触发人 MEMBER_CODE |
| notification_type | varchar | | | 通知类型 |
| news_id | varchar | ✓ | | 帖子 ID |
| comment_id | varchar | ✓ | | 评论 ID |
| reply_comment_id | varchar | ✓ | | 回复评论 ID |
| aggregation_key | varchar | | | 聚合键 |
| dedupe_key | varchar | | | 去重键 |
| metadata | jsonb | | '{}' | 元数据 |
| metadata_version | smallint | | 1 | 元数据版本 |
| is_read | boolean | | false | 是否已读 |
| read_at | timestamptz | ✓ | | 阅读时间 |
| occurred_at | timestamptz | | now() | 发生时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |
| expires_at | timestamptz | | now()+180天 | 过期时间 |

**索引**：PK `id`、UNIQUE `(recipient_member_code, dedupe_key)`、`(recipient_member_code, notification_type, aggregation_key, occurred_at DESC)`、`(recipient_member_code, notification_type, occurred_at DESC, id DESC)`、`(recipient_member_code, notification_type, aggregation_key, occurred_at DESC) WHERE is_read=false`、`comment_id`、`reply_comment_id`、`news_id`、`expires_at`

---

## 16. plaza_posts — 广场帖子

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| news_id | varchar | | | 帖子 ID |
| member_code | varchar | | | 用户 MEMBER_CODE |
| news_type | numeric | ✓ | | 帖子类型 |
| title | varchar | ✓ | | 标题 |
| content | text | ✓ | | 内容 |
| create_time | timestamptz | ✓ | | 发布时间 |
| operator | varchar | ✓ | | 操作人 |
| status | varchar | | '10-正常展示' | 状态 |
| hit_nums | numeric | | 0 | 点击数 |
| comment_nums | numeric | | 0 | 评论数 |
| spec_activ_id | varchar | ✓ | | 活动 ID |
| event_type | numeric | ✓ | | 事件类型 |
| flash_id | varchar | ✓ | | 视频 ID |
| news_hit | numeric | | 0 | 热度 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |
| tags | text | ✓ | | 标签 |
| categories | varchar | ✓ | | 分类 |
| scheduled_time | timestamptz | ✓ | | 定时发布时间 |
| visibility | varchar | | 'public' | 可见性 |

**索引**：PK `id`、UNIQUE `news_id`、`member_code`、`news_id`、`status`、`create_time`、`(status, create_time DESC)`

---

## 17. plaza_questions — 广场问答

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| question_id | varchar | | | 问题 ID |
| news_id | varchar | | | 帖子 ID |
| asker_member_code | varchar | | | 提问者 MEMBER_CODE |
| title | varchar | ✓ | | 标题 |
| content | text | ✓ | | 内容 |
| categories | ARRAY | ✓ | | 分类标签 |
| status | varchar | | '待回答' | 状态 |
| accepted_answerer_member_code | varchar | ✓ | | 采纳回答者 |
| accepted_answer_content | text | ✓ | | 采纳回答内容 |
| create_time | timestamptz | ✓ | | 提问时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `question_id`、`asker_member_code`、`news_id`、`question_id`

---

## 18. plaza_videos — 广场视频

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| flash_id | varchar | | | 视频 ID |
| ld_type | numeric | ✓ | | 类型 |
| flash_name | varchar | ✓ | | 视频名称 |
| flash_path | text | ✓ | | 视频路径 |
| image_path | text | ✓ | | 封面图路径 |
| status | numeric | ✓ | | 状态 |
| flash_hits | numeric | | 0 | 播放量 |
| video_id | varchar | ✓ | | 视频 ID |
| spec_activ_id | varchar | ✓ | | 活动 ID |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`、UNIQUE `flash_id`、`flash_id`

---

## 19. price_baogangdesheng_304_no1 — 宝钢德盛 304 NO.1 价格

> 卷板价格明细：SheetCoilSettingCode=1684377230182442, ThinkCode=1236

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| sheet_coil_setting_code | bigint | | | 卷板设置代码 |
| price | numeric | | | 价格 |
| think_code | integer | | | Think 代码 |
| think_name | numeric | ✓ | | Think 名称 |
| date_year | integer | | | 年份 |
| price_date | date | | | 价格日期（唯一，每个交易日一条） |
| is_am | smallint | | 0 | 是否上午 |
| group_day | integer | | | 分组天 |
| width_name | numeric | ✓ | | 宽度 |
| market_name | varchar | ✓ | | 市场名称 |
| length_name | varchar | ✓ | | 长度 |
| price_unit | numeric | ✓ | | 价格单位 |
| factory_name | varchar | ✓ | | 钢厂名称 |
| material_name | varchar | ✓ | | 材质名称 |
| surface_name | varchar | ✓ | | 表面名称 |
| is_tax | smallint | ✓ | | 是否含税 |
| remark_name | varchar | ✓ | | 备注 |
| product_sort_name | varchar | ✓ | | 产品分类 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `price_date`

---

## 20. price_ningbobaoxin_430_2b — 宁波宝新 430 2B 价格

> 卷板价格明细：SheetCoilSettingCode=917126, ThinkCode=1231

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| sheet_coil_setting_code | bigint | | | 卷板设置代码 |
| price | numeric | | | 价格 |
| think_code | integer | | | Think 代码 |
| think_name | numeric | ✓ | | Think 名称 |
| date_year | integer | | | 年份 |
| price_date | date | | | 价格日期（唯一，每个交易日一条） |
| is_am | smallint | | 0 | 是否上午 |
| group_day | integer | | | 分组天 |
| width_name | numeric | ✓ | | 宽度 |
| market_name | varchar | ✓ | | 市场名称 |
| length_name | varchar | ✓ | | 长度 |
| price_unit | numeric | ✓ | | 价格单位 |
| factory_name | varchar | ✓ | | 钢厂名称 |
| material_name | varchar | ✓ | | 材质名称 |
| surface_name | varchar | ✓ | | 表面名称 |
| is_tax | smallint | ✓ | | 是否含税 |
| remark_name | varchar | ✓ | | 备注 |
| product_sort_name | varchar | ✓ | | 产品分类 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `price_date`

---

## 21. price_taigangbuxiu_304_2b — 太钢不锈 304 2B 价格

> 卷板价格明细：SheetCoilSettingCode=1462500075742458, ThinkCode=1234

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| sheet_coil_setting_code | bigint | | | 卷板设置代码 |
| price | numeric | | | 价格 |
| think_code | integer | | | Think 代码 |
| think_name | numeric | ✓ | | Think 名称 |
| date_year | integer | | | 年份 |
| price_date | date | | | 价格日期（唯一，每个交易日一条） |
| is_am | smallint | | 0 | 是否上午 |
| group_day | integer | | | 分组天 |
| width_name | numeric | ✓ | | 宽度 |
| market_name | varchar | ✓ | | 市场名称 |
| length_name | varchar | ✓ | | 长度 |
| price_unit | numeric | ✓ | | 价格单位 |
| factory_name | varchar | ✓ | | 钢厂名称 |
| material_name | varchar | ✓ | | 材质名称 |
| surface_name | varchar | ✓ | | 表面名称 |
| is_tax | smallint | ✓ | | 是否含税 |
| remark_name | varchar | ✓ | | 备注 |
| product_sort_name | varchar | ✓ | | 产品分类 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `price_date`

---

## 22. sales_pipeline_records — 销售全链路记录

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| order_no | varchar | | | 订单编号 |
| service_name | varchar | | | 服务名称 |
| company_name | varchar | | | 公司名称 |
| customer_type | varchar | | '其他' | 客户类型 |
| contract_sign_time | timestamptz | ✓ | | 合同签订时间 |
| contract_sign_status | varchar | | '未签订' | 合同签订状态 |
| sale_amount | numeric | | 0 | 销售金额 |
| received_amount | numeric | | 0 | 已收款金额 |
| payment_status | varchar | | '待收款' | 付款状态 |
| delivery_status | varchar | | '待交付' | 交付状态 |
| invoice_status | varchar | | '待开票' | 发票状态 |
| payment_cycle_months | integer | | 1 | 付款周期（月） |
| salesperson | varchar | ✓ | | 销售人员 |
| remark | text | ✓ | | 备注 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `order_no`、`company_name`、`contract_sign_time`、`delivery_status`、`invoice_status`、`order_no`、`payment_status`

---

## 23. site_feedback — 站点反馈

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| feedback_id | varchar | | | 反馈 ID |
| feedback_type | varchar | | | 反馈类型 |
| page_name | varchar | ✓ | | 页面名称 |
| page_route | varchar | ✓ | | 页面路由 |
| phone | varchar | ✓ | | 手机号 |
| user_name | varchar | ✓ | | 用户名称 |
| content | text | ✓ | | 反馈内容 |
| severity | varchar | ✓ | | 严重程度 |
| steps | text | ✓ | | 操作步骤 |
| product_name | varchar | ✓ | | 产品名称 |
| screenshots | text | ✓ | | 截图 |
| status | varchar | ✓ | '待处理' | 状态 |
| submitted_at | timestamptz | | | 提交时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |
| supplement | text | ✓ | | 补充说明 |
| member_code | varchar | ✓ | | 用户 MEMBER_CODE |

**索引**：PK `id`、`feedback_id`、`feedback_type`、`member_code`、`status`、`submitted_at`

---

## 24. site_feedback_images — 反馈截图

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| feedback_id | varchar | | | 反馈 ID |
| image | bytea | | | 图片二进制 |
| sort_order | integer | | 0 | 排序 |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`、`feedback_id`

---

## 25. sys_api_error_logs — API 错误日志

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| error_time | timestamptz | | now() | 错误时间 |
| source | varchar | | | 来源 |
| request_method | varchar | ✓ | | 请求方法 |
| request_url | text | ✓ | | 请求 URL |
| request_params | text | ✓ | | 请求参数 |
| error_type | varchar | ✓ | | 错误类型 |
| error_message | text | | | 错误信息 |
| error_stack | text | ✓ | | 错误堆栈 |
| response_status | integer | ✓ | | 响应状态码 |
| response_body | text | ✓ | | 响应体 |
| request_duration | integer | ✓ | | 请求耗时 |
| member_code | varchar | ✓ | | 用户 MEMBER_CODE |
| ip_address | varchar | ✓ | | IP 地址 |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`（名 `api_error_logs_pkey`）、`error_time`、`error_type`、`source`

---

## 26. trade_contact_view_logs — 联系方式查看日志

> 3 天限次计算与审计留痕

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| member_code | varchar | | | 查看人 MEMBER_CODE（不用手机号） |
| product_id | varchar | | | 商品 ID |
| supplier_id | varchar | ✓ | | 供应商 ID |
| deal_record_id | uuid | ✓ | | 本次查看生成的成交记录 id |
| viewed_at | timestamptz | | now() | 查看时间 |
| created_at | timestamptz | | now() | 创建时间 |
| feedback | varchar | ✓ | | 跟进结果反馈：已成交/未成交/仍在沟通 |
| material | varchar | ✓ | | 钢种（材质代码如 304），用于单钢种每日 2 次限次 |

**索引**：PK `id`、`(member_code, viewed_at DESC)`、`product_id`

---

## 27. trade_deal_records — 站内交易成交记录

> 查看联系方式即成交，商品立即从搜索结果过滤

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| product_id | varchar | | | 秀吗商品 ProductId |
| product_snapshot | jsonb | | '{}' | 成交时商品快照：材质/表面/规格/仓库/价格/吨数/城市等 |
| buyer_member_code | varchar | | | 买方 MEMBER_CODE（不用手机号） |
| supplier_id | varchar | ✓ | | 供应商 ID |
| supplier_name | varchar | ✓ | | 供应商名称 |
| supplier_type | varchar | | | 货源类型：self_operated=秀吗自营 / supplier_listed=供应商自挂 |
| certified | boolean | | false | 是否秀吗认证商家（已交保证金） |
| deal_time | timestamptz | | now() | 成交时间 |
| payment_status | varchar | | 'unpaid' | 付款状态：unpaid/paid/timeout |
| payment_remark | text | ✓ | | 付款备注 |
| registered_by | varchar | ✓ | | 付款登记操作人（客服） |
| registered_at | timestamptz | ✓ | | 付款登记时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |
| payment_deadline | timestamptz | ✓ | | 付款时限截止（现货=成交+24h；期货 48h） |
| violation_count | integer | | 0 | 累计违约次数（超时自动累加，>=2 拦截） |
| first_warned | boolean | | false | 首次超时是否已发豁免提醒 |

**索引**：PK `id`、UNIQUE `product_id`、`buyer_member_code`、`deal_time DESC`、`payment_status`

---

## 28. trade_negotiation_actions — 议价动作记录

> 站内交易轻量议价动作记录（同意/还价/确认意向）

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| deal_record_id | uuid | | | 关联成交记录 trade_deal_records.id |
| actor_member_code | varchar | | | 操作人 MEMBER_CODE |
| action | varchar | | | 动作类型：accept=同意 / counter=还价 / confirm=确认买卖意向 |
| price | numeric | ✓ | | 还价金额（元/吨，仅 counter 填写） |
| remark | text | ✓ | | 备注 |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`、`deal_record_id`、`actor_member_code`

---

## 29. trade_view_rules — 交易规则配置

> 站内交易规则配置（单行表，统一数据源控制限次/时限/违约阈值）

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 UUID |
| material_daily_limit | integer | | 2 | 单钢种每日查看联系方式上限（全用户统一） |
| payment_deadline_hours_spot | integer | | 24 | 现货付款时限（小时），超时自动判违约 |
| payment_deadline_hours_futures | integer | | 48 | 期货付款时限（小时） |
| violation_block_threshold | integer | | 2 | 累计违约达到该次数后拦截查看联系方式（首次豁免） |
| updated_at | timestamptz | | now() | 记录最后更新时间 |
| _created_at | timestamptz | | now() | 审计：创建时间 |
| _updated_at | timestamptz | | now() | 审计：更新时间 |
| _created_by | varchar | | 'system' | 审计：创建人 |
| _updated_by | varchar | | 'system' | 审计：更新人 |

**索引**：PK `id`

---

## 30. user_behavior_records — 用户行为记录

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| member_code | varchar | | | 用户 MEMBER_CODE |
| behavior_type | varchar | | | 行为类型 |
| behavior_time | timestamptz | | now() | 行为时间 |
| target_id | varchar | ✓ | | 目标 ID |
| content | text | ✓ | | 内容 |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`（名 `behavior_records_pkey`）、`(member_code, behavior_time)`、`(behavior_type, behavior_time)`

---

## 31. user_profiles — 用户画像

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| member_code | varchar | | | 用户 MEMBER_CODE |
| ai_profile_tags | text | ✓ | | AI 画像标签 |
| ai_profile_summary | text | ✓ | | AI 画像摘要 |
| ai_profile_updated_at | timestamptz | ✓ | | AI 画像更新时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |
| profile_tags | ARRAY | ✓ | | 画像标签 |
| frequent_steels | ARRAY | ✓ | | 常用钢种 |
| behavior_count | integer | | 0 | 行为计数 |
| last_active_at | timestamptz | ✓ | | 最后活跃时间 |
| behavior_updated_at | timestamptz | ✓ | | 行为更新时间 |

**索引**：PK `id`、UNIQUE `member_code`

---

## 32. user_recent_views — 用户最近浏览

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| member_code | varchar | | | 用户 MEMBER_CODE |
| target_type | varchar | | 'plaza_post' | 目标类型 |
| target_id | varchar | | | 目标 ID |
| title | varchar | ✓ | | 标题 |
| view_count | integer | | 1 | 浏览次数 |
| first_view_at | timestamptz | | now() | 首次浏览时间 |
| last_view_at | timestamptz | | now() | 最后浏览时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`（名 `recent_views_pkey`）、UNIQUE `(member_code, target_type, target_id)`、`(member_code, last_view_at DESC)`

---

## 33. users — 用户主表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| member_code | varchar | | | 用户 MEMBER_CODE |
| phone | varchar | ✓ | | 手机号 |
| email | varchar | ✓ | | 邮箱 |
| enterprise_id | varchar | ✓ | | 企业 ID |
| display_name | varchar | ✓ | | 显示名称 |
| registration_source | varchar | ✓ | | 注册来源 |
| last_login_at | timestamptz | ✓ | | 最后登录时间 |
| platform | varchar | ✓ | '51bxg' | 平台 |
| account_status | varchar | | 'active' | 账号状态 |
| remark | text | ✓ | | 备注 |
| nickname | varchar | ✓ | | 昵称 |
| avatar_url | text | ✓ | | 头像 URL |
| company_name | varchar | ✓ | | 公司名称 |
| real_name | varchar | ✓ | | 真实姓名 |
| gender | varchar | ✓ | | 性别 |
| position | varchar | ✓ | | 职位 |
| location | varchar | ✓ | | 所在地 |
| company_scale | varchar | ✓ | | 公司规模 |
| business_directions | ARRAY | ✓ | | 业务方向 |
| steel_grades | ARRAY | ✓ | | 钢种 |
| monthly_purchase_volume | numeric | ✓ | | 月均采购量 |
| onboarding_completed | boolean | | false | 是否完成新手引导 |
| ai_profile_tags | text | ✓ | | AI 画像标签 |
| ai_profile_summary | text | ✓ | | AI 画像摘要 |
| ai_profile_updated_at | timestamptz | ✓ | | AI 画像更新时间 |
| created_at | timestamptz | | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | timestamptz | | CURRENT_TIMESTAMP | 更新时间 |
| sex | varchar | ✓ | | 性别（旧字段） |
| avatar_data | bytea | ✓ | | 头像 JPEG 二进制数据（bytea），优先于 avatar_url 显示 |
| profile_background | text | ✓ | | 个人资料页背景设置（渐变 CSS 字符串或图片 data URL） |
| business_focus | varchar | ✓ | | AI金「业务侧重」（purchase / sales） |
| monthly_sales_volume | numeric | ✓ | | AI金「月均销售量」 |

**索引**：PK `id`、UNIQUE `member_code`、`account_status`、`company_name`、`created_at`、`member_code`、`phone`

---

## 34. vip_features — VIP 功能特性

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| capability_id | integer | | | 能力 ID |
| name | varchar | | | 名称 |
| category | varchar | ✓ | | 分类 |
| permission_type | varchar | | | 权限类型 |
| route | varchar | ✓ | | 路由 |
| feature_key | varchar | ✓ | | 功能键 |
| description | text | ✓ | | 描述 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`（名 `features_pkey`）、UNIQUE `capability_id`、`capability_id`、`category`、`permission_type`

---

## 35. vip_member_relations — VIP 成员关系

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| member_code | varchar | | | 成员 MEMBER_CODE |
| owner_member_code | varchar | | | 主账号 MEMBER_CODE |
| order_no | varchar | | | 订单编号 |
| role | varchar | | 'member' | 角色 |
| status | varchar | | 'active' | 状态 |
| joined_at | timestamptz | ✓ | | 加入时间 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`（名 `member_relations_pkey`）、`member_code`、`order_no`、`owner_member_code`、`role`、`status`

---

## 36. vip_operation_logs — VIP 操作审计日志

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| operation_time | timestamptz | | | 操作时间 |
| operator | varchar | | | 操作人 |
| operation_type | varchar | | | 操作类型 |
| description | text | | | 描述 |
| result | varchar | | 'success' | 结果 |
| related_order_no | varchar | ✓ | | 关联订单号 |
| ip_address | varchar | ✓ | | IP 地址 |
| created_at | timestamptz | | now() | 创建时间 |

**索引**：PK `id`（名 `operation_logs_pkey`）、`operation_time`、`operation_type`、`operator`、`related_order_no`、`result`

---

## 37. vip_packages — VIP 套餐

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| name | varchar | | | 套餐名称 |
| level | integer | | | 等级 |
| price_in_cents | integer | | 0 | 价格（分） |
| max_accounts | integer | | 1 | 最大账号数 |
| capabilities_text | text | ✓ | | 功能描述 |
| enabled | boolean | | true | 是否启用 |
| description | text | ✓ | | 描述 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |
| visible | boolean | | true | 是否可见 |
| view_window_days | integer | | 3 | 联系方式查看窗口（天） |
| view_max_count | integer | | 1 | 联系方式查看次数上限（0=禁止查看） |

**索引**：PK `id`（名 `packages_pkey`）、UNIQUE `name`、`level`、`name`

---

## 38. vip_purchase_records — VIP 购买记录

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| order_no | varchar | | | 订单编号 |
| member_code | varchar | | | 用户 MEMBER_CODE |
| phone | varchar | ✓ | | 手机号 |
| package_name | varchar | | | 套餐名称 |
| amount | integer | | 0 | 金额（分） |
| payment_method | varchar | ✓ | | 支付方式 |
| status | varchar | | 'pending' | 状态 |
| expire_at | timestamptz | ✓ | | 过期时间 |
| purchase_date | timestamptz | ✓ | | 购买日期 |
| expiry_date | timestamptz | ✓ | | 到期日期 |
| payment_time | timestamptz | ✓ | | 支付时间 |
| trade_no | varchar | ✓ | | 交易号 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |
| package_id | varchar | ✓ | | 套餐 UUID，防止改名后断联 |

**索引**：PK `id`（名 `purchase_records_pkey`）、UNIQUE `order_no`、`member_code`、`order_no`、`package_name`、`status`

---

## 39. xiuma_member_contact — 秀吗会员联系方式

> CRM 会员联系方式页面导出，货品导入时按公司名回填电话

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| contact_id | varchar | ✓ | | 秀吗联系人编号（CONTACT_ID） |
| member_name | varchar | | | 公司全称（MEMBER_NAME），与快照表 supplier_name 关联回填电话 |
| privilege_name | varchar | ✓ | | 权限名称 |
| contact_name | varchar | ✓ | | 联系人名称 |
| contact_title | varchar | ✓ | | 联系人职务 |
| telephone | varchar | ✓ | | 固定电话（TELEPHONE） |
| mobile | varchar | ✓ | | 移动电话（MOBILE） |
| main_contact | boolean | | false | 是否主联系人（MAIN_CONTANT），回填电话时优先 |
| policymaker | boolean | | false | 是否决策人 |
| status | varchar | ✓ | | 状态 |
| remark | text | ✓ | | 备注 |
| create_time | timestamptz | ✓ | | 创建时间 |
| sync_time | timestamptz | | now() | 同步时间 |
| source | varchar | | 'manual_import' | 来源 |
| is_active | boolean | | true | false=失效/已删联系人，回填时剔除 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `contact_id`、`member_name`、`(member_name, main_contact)`、`is_active`

---

## 40. xiuma_product_snapshot — 秀吗货品快照

> 每日从秀吗 ERP 导出导入，AI金 配单读本表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | uuid | | gen_random_uuid() | 主键 |
| product_id | varchar | ✓ | | 秀吗 PRODUCT_ID（数字，跳转详情页/成交定位用） |
| product_code | varchar | | | 秀吗货品编码（如 XH2607044327） |
| category_name | varchar | ✓ | | 分类名称 |
| series | varchar | ✓ | | 系列 |
| steel_no | varchar | ✓ | | 钢号 |
| sale_type | varchar | ✓ | | 销售类型 |
| sale_mode | varchar | ✓ | | 销售模式 |
| is_self_run | varchar | ✓ | | 是否自营 |
| earnest_money | numeric | ✓ | | 保证金 |
| package_no | varchar | ✓ | | 包裹号 |
| supplier_name | varchar | ✓ | | 供应商名称 |
| supplier_type | varchar | ✓ | | 供应商类型 |
| manufacturer_name | varchar | ✓ | | 钢厂名称 |
| house_name | varchar | ✓ | | 仓库名称 |
| useable_quantity | integer | ✓ | | 可用数量 |
| useable_weight | numeric | ✓ | | 可用重量 |
| discount_price | numeric | ✓ | | 折扣价格 |
| material_surface | varchar | ✓ | | 材质表面 |
| spec_code | varchar | ✓ | | 规格代码 |
| level_name | varchar | ✓ | | 等级名称 |
| package | varchar | ✓ | | 包装 |
| edge | varchar | ✓ | | 边部 |
| reference_thick | numeric | ✓ | | 参考厚度 |
| auctions_type | varchar | ✓ | | 拍卖类型 |
| promotion | varchar | ✓ | | 促销 |
| product_status | varchar | ✓ | | 商品状态 |
| info_status | varchar | ✓ | | 信息状态 |
| upload_time | timestamptz | ✓ | | 上传时间 |
| sale_end_time | timestamptz | ✓ | | 销售结束时间 |
| create_time | timestamptz | ✓ | | 创建时间 |
| import_time | timestamptz | ✓ | | 导入时间 |
| privilege_id | varchar | ✓ | | 权限 ID |
| supplier_id | varchar | ✓ | | 供应商 ID |
| city_name | varchar | ✓ | | 城市 |
| province_name | varchar | ✓ | | 省份 |
| member_level_name | varchar | ✓ | | 会员等级 |
| telephone | varchar | ✓ | | 供应商联系方式（由 supplier_info.aspx 导出补全） |
| sync_time | timestamptz | | now() | 同步时间 |
| source | varchar | | 'manual_import' | manual_import=手动导出导入 / initial=首次全量 |
| is_active | boolean | | true | false=已下架/售罄，搜索时剔除 |
| created_at | timestamptz | | now() | 创建时间 |
| updated_at | timestamptz | | now() | 更新时间 |

**索引**：PK `id`、UNIQUE `product_code`、UNIQUE `product_id`、`city_name`、`house_name`、`supplier_name`、`material_surface`、`upload_time`、`is_active`、`(is_active, upload_time DESC)`

---

## 汇总

| 统计项 | 数量 |
|--------|------|
| 总表数 | 39 |
| 启用 RLS 的表 | 0 |
| 有 PK 的表 | 39 |
| 账密表（含审计列） | 4（ai_jin_auth_credentials、ai_jin_verification_codes、feishu_user_bindings、trade_view_rules） |
| 含 bytea 列的表 | 2（users.avatar_data、site_feedback_images.image） |
| 含 jsonb 列的表 | 3（plaza_demands.parsed_params、plaza_notifications.metadata、trade_deal_records.product_snapshot） |