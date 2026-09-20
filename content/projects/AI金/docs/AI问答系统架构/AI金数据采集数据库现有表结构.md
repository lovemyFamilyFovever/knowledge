# AI金数据采集数据库现有表结构

> 本文档由当前本地 PostgreSQL 实时只读查询生成。
>
> - 数据库：`bxg_app`
> - Schema：`public`
> - PostgreSQL：`17.10`
> - 检查时间：`2026-08-20T09:01:25.323Z`
> - 信息来源：`information_schema`、`pg_catalog`、`pg_indexes`、`pg_constraint`、`col_description`、`obj_description`、`pg_policies`
> - 数据库操作：事务级 `REPEATABLE READ READ ONLY`；仅执行系统目录查询、`COUNT(*)`、`DISTINCT/GROUP BY` 和字典对照查询，未执行任何 DML、DDL。

# 一、数据库总览

当前数据采集标准体系共24张表：12张标准字典表、10张采集/分析/内容表、2张知识图谱表。

| 表名 | 表用途 | 当前行数 |
| --- | --- | ---: |
| `dict_industry_category` | 采集标注系统-品类字典（不锈钢/铜/碳钢等） | 7 |
| `dict_grade` | 采集标注系统-钢种/品种字典（304/316L/201 等） | 16 |
| `dict_region` | 采集标注系统-区域字典（华东/华南/全国合计等） | 9 |
| `dict_event_category` | 采集标注系统-事件大类字典（A-G 七大类） | 7 |
| `dict_event_sub_category` | 采集标注系统-事件子类字典（关联大类 code，01 文档 3.3 全量枚举） | 50 |
| `dict_inventory_type` | 采集标注系统-库存类型字典 | 4 |
| `dict_tax_status` | 采集标注系统-含税状态字典 | 2 |
| `dict_analysis_type` | 采集标注系统-解读类型字典 | 5 |
| `dict_forecast_model` | 采集标注系统-预测模型字典 | 4 |
| `dict_channel` | 采集标注系统-分发渠道字典 | 6 |
| `dict_article_style` | 采集标注系统-文章风格字典 | 6 |
| `dict_entity_alias` | 采集标注系统-实体别名唯一真源（alias→standard_name 映射；kg_entities.aliases 为其只读缓存） | 7 |
| `data_articles` | 采集标注系统-原始文章表（原文存储+去重+任务容器，一篇文章可挂多条业务子记录） | 31 |
| `data_events` | 采集标注系统-事件表（业务子记录，挂 data_articles 任务容器） | 25 |
| `data_daily_price` | 采集标注系统-每日价格（数据轨，AI 直通 active，低置信度转 draft） | 13 |
| `data_weekly_inventory` | 采集标注系统-每周库存（数据轨，周频；抽取模板 P2 扩展） | 0 |
| `data_monthly_production` | 采集标注系统-每月产量（数据轨，月频；抽取模板 P2 扩展） | 0 |
| `data_quarterly_demand` | 采集标注系统-每季度需求量（数据轨，季频；抽取模板 P2 扩展） | 0 |
| `data_analysis` | 采集标注系统-分析表（A 事件解读 / B 数据解读合并一表；抽取模板 P2 扩展） | 0 |
| `data_forecast` | 采集标注系统-预测表（P 价格/Q 库存/R 需求产量合并一表；抽取模板 P2 扩展） | 0 |
| `data_content` | 采集标注系统-生成内容产物表（独立于 data_articles，多平台多风格草稿与定稿） | 42 |
| `data_content_citations` | 采集标注系统-生成内容与素材业务记录的引用关系（一对多，支撑来源追溯与 BASED_ON 边） | 160 |
| `kg_entities` | 采集标注系统-知识图谱节点表（行业实体 + 业务记录节点，业务记录入库时同步建节点） | 39 |
| `kg_relations` | 采集标注系统-知识图谱关系边表（全系统关系唯一真源；同对节点同类型允许多条，relation_id 唯一） | 94 |

# 二、每张表完整结构

## dict_industry_category

### 用途

采集标注系统-品类字典（不锈钢/铜/碳钢等）

当前精确行数：7。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `name` | `text` | 否 | — | 品类名称（唯一） |
| `sort_order` | `integer` | 否 | `0` | 排序号，越小越靠前 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_industry_category_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_industry_category_name`：方法 `btree`；字段：`name`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_grade

### 用途

采集标注系统-钢种/品种字典（304/316L/201 等）

当前精确行数：16。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `name` | `text` | 否 | — | 钢种/品种名称（唯一） |
| `sort_order` | `integer` | 否 | `0` | 排序号 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_grade_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_grade_name`：方法 `btree`；字段：`name`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_region

### 用途

采集标注系统-区域字典（华东/华南/全国合计等）

当前精确行数：9。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `name` | `text` | 否 | — | 区域名称（唯一） |
| `sort_order` | `integer` | 否 | `0` | 排序号 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_region_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_region_name`：方法 `btree`；字段：`name`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_event_category

### 用途

采集标注系统-事件大类字典（A-G 七大类）

当前精确行数：7。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `code` | `text` | 否 | — | 大类编码：A/B/C/D/E/F/G（唯一） |
| `name` | `text` | 否 | — | 大类名称，如 A=钢厂/工厂 |
| `sort_order` | `integer` | 否 | `0` | 排序号 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_event_category_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_event_category_code`：方法 `btree`；字段：`code`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_event_sub_category

### 用途

采集标注系统-事件子类字典（关联大类 code，01 文档 3.3 全量枚举）

当前精确行数：50。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `category` | `text` | 否 | — | 所属事件大类编码：A/B/C/D/E/F/G |
| `name` | `text` | 否 | — | 子类名称 |
| `sort_order` | `integer` | 否 | `0` | 排序号 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_event_sub_category_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_event_sub_category`：方法 `btree`；字段：`category`、`name`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_inventory_type

### 用途

采集标注系统-库存类型字典

当前精确行数：4。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `name` | `text` | 否 | — | 库存类型：市场库存/钢厂库存/港口库存/保税区库存 |
| `sort_order` | `integer` | 否 | `0` | 排序号 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_inventory_type_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_inventory_type_name`：方法 `btree`；字段：`name`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_tax_status

### 用途

采集标注系统-含税状态字典

当前精确行数：2。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `name` | `text` | 否 | — | 含税状态：含税/不含税 |
| `sort_order` | `integer` | 否 | `0` | 排序号 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_tax_status_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_tax_status_name`：方法 `btree`；字段：`name`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_analysis_type

### 用途

采集标注系统-解读类型字典

当前精确行数：5。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `name` | `text` | 否 | — | 解读类型：原因解读/影响评估/趋势研判/风险提示/机会提示 |
| `sort_order` | `integer` | 否 | `0` | 排序号 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_analysis_type_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_analysis_type_name`：方法 `btree`；字段：`name`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_forecast_model

### 用途

采集标注系统-预测模型字典

当前精确行数：4。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `name` | `text` | 否 | — | 预测模型：AI金LLM/历史规律/专家经验/综合 |
| `sort_order` | `integer` | 否 | `0` | 排序号 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_forecast_model_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_forecast_model_name`：方法 `btree`；字段：`name`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_channel

### 用途

采集标注系统-分发渠道字典

当前精确行数：6。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `name` | `text` | 否 | — | 渠道：公众号/51号APP/抖音快手/行业群/AI金客服/AI金推送 |
| `sort_order` | `integer` | 否 | `0` | 排序号 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_channel_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_channel_name`：方法 `btree`；字段：`name`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_article_style

### 用途

采集标注系统-文章风格字典

当前精确行数：6。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `name` | `text` | 否 | — | 风格：日评/周报/月报/季报/新闻简讯/深度报道 |
| `sort_order` | `integer` | 否 | `0` | 排序号 |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_article_style_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_article_style_name`：方法 `btree`；字段：`name`

### 普通索引

无。

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## dict_entity_alias

### 用途

采集标注系统-实体别名唯一真源（alias→standard_name 映射；kg_entities.aliases 为其只读缓存）

当前精确行数：7。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `alias` | `text` | 否 | — | 别名（唯一） |
| `standard_name` | `text` | 否 | — | 标准名 |
| `entity_type` | `text` | 否 | — | 实体类型：factory/raw_material/policy/industry/macro_indicator/region_market/product_grade/organization/person/project/trade_measure/other |
| `source` | `text` | 是 | — | 来源：人工确认/AI 建议/导入 |
| `is_confirmed` | `boolean` | 否 | `false` | 是否人工确认 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `dict_entity_alias_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_dict_entity_alias_alias`：方法 `btree`；字段：`alias`

### 普通索引

- `idx_dict_entity_alias_standard_name`：方法 `btree`；字段：`standard_name`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## data_articles

### 用途

采集标注系统-原始文章表（原文存储+去重+任务容器，一篇文章可挂多条业务子记录）

当前精确行数：31。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `title` | `text` | 是 | — | 文章标题 |
| `content` | `text` | 否 | — | 文章全文 |
| `content_hash` | `text` | 否 | — | 正文 SHA-256 去重指纹 |
| `source_url` | `text` | 是 | — | 来源链接 |
| `source_name` | `text` | 否 | — | 来源平台（如 51bxg/公众号/自写） |
| `author` | `text` | 是 | — | 作者（自写文章用） |
| `article_type` | `text` | 是 | — | 路由判定结果：event/data_price/data_inventory/data_production/data_demand/analysis/forecast/mixed/unknown |
| `status` | `text` | 否 | `'pending'::text` | 文章状态机：pending 待提取/processing 处理中/reviewing 待校核/completed 完成/partial 部分完成/failed 失败/duplicate 重复 |
| `confidence_summary` | `jsonb` | 是 | — | 各字段置信度汇总（供校核页标红） |
| `ai_draft` | `jsonb` | 是 | — | AI 草稿原始内容（含每字段 evidence 证据链 + nature 性质） |
| `extracted_at` | `timestamp with time zone` | 是 | — | 提取完成时间 |
| `reviewed_at` | `timestamp with time zone` | 是 | — | 校核完成时间 |
| `reviewed_by` | `text` | 是 | — | 校核人 |
| `related_entity_ids` | `text[]` | 是 | — | 关联图谱实体 ID（只读缓存，图谱回刷，不允许人工维护） |
| `duplicate_of` | `uuid` | 是 | — | 转载溯源：指向最早来源文章 ID（仅标记不合并，可空） |
| `version` | `integer` | 否 | `1` | 版本号（重提递增） |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `data_articles_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_data_articles_hash_source`：方法 `btree`；字段：`content_hash`、`source_name`

### 普通索引

- `idx_data_articles_article_type`：方法 `btree`；字段：`article_type`
- `idx_data_articles_created_at`：方法 `btree`；字段：`_created_at`
- `idx_data_articles_status`：方法 `btree`；字段：`status`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## data_events

### 用途

采集标注系统-事件表（业务子记录，挂 data_articles 任务容器）

当前精确行数：25。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `source_article_id` | `uuid` | 是 | — | 来源文章外键（逻辑引用 data_articles.id，可空：数据快填/人工填报） |
| `event_id` | `text` | 是 | — | E1 对外 ID（EVT-YYYYMMDD-XXX，唯一） |
| `title` | `text` | 是 | — | E2 事件标题（≤30 字） |
| `category` | `text` | 是 | — | E3 事件大类（dict_event_category：A-G） |
| `sub_category` | `text` | 是 | — | E4 事件子类（dict_event_sub_category） |
| `event_date` | `date` | 是 | — | E5 发生时间 |
| `related_grades` | `text[]` | 是 | — | E6 涉及品类/钢种（多选） |
| `related_regions` | `text[]` | 是 | — | E7 涉及地域（多选，可全国） |
| `subject` | `text` | 是 | — | E8 事件主体（≤50 字） |
| `summary` | `text` | 是 | — | E9 事件简述（填空模板，≤200 字） |
| `impact_direction` | `jsonb` | 是 | — | E10 数据影响方向：[{dimension: 日价/周库/月产/季需, direction: 上涨/下跌/持平}] |
| `impact_level` | `smallint` | 是 | — | E11 影响程度 1-5 星 |
| `validity_days` | `integer` | 是 | `30` | 事件有效期天数（检修=15/政策=180/关税=365/突发=7，默认 30） |
| `valid_until` | `date` | 是 | — | 系统衍生：event_date + validity_days，问答层按 valid_until >= CURRENT_DATE 过滤 |
| `detail` | `text` | 是 | — | O1 事件详情（≤1000 字） |
| `data_comparison` | `text` | 是 | — | O2 数据对比 |
| `affected_companies` | `text[]` | 是 | — | O3 受影响企业 |
| `duration` | `text` | 是 | — | O4 预计持续时间 |
| `follow_up` | `jsonb` | 是 | — | O5 后续动态跟踪 [{time, content}] |
| `source_links` | `text[]` | 是 | — | O6 信源链接 |
| `policy_attachments` | `jsonb` | 是 | — | O7 关联政策文件（文件元数据） |
| `media_attachments` | `jsonb` | 是 | — | O8 图片/视频附件 |
| `collector_name` | `text` | 是 | — | O9 业务采集人（填表的同事） |
| `collected_at` | `timestamp with time zone` | 是 | — | O10 采集时间 |
| `remark` | `text` | 是 | — | O11 备注 |
| `related_data_ids` | `text[]` | 是 | — | 反向关联数据记录 ID（图谱回刷缓存，唯一真源 kg_relations） |
| `related_analysis_ids` | `text[]` | 是 | — | 关联分析记录 ID（图谱回刷缓存） |
| `related_forecast_ids` | `text[]` | 是 | — | 关联预测记录 ID（图谱回刷缓存） |
| `status` | `text` | 否 | `'draft'::text` | 业务记录状态机：draft AI 预填草稿/confirmed 人工确认/archived 归档；非主链 skipped 跳过/rejected 放弃；failed 抽取失败可重试 |
| `ai_draft` | `jsonb` | 是 | — | AI 草稿原始内容（evidence + nature + field_reviewed，供回溯） |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `data_events_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_data_events_event_id`：方法 `btree`；字段：`event_id`

### 普通索引

- `idx_data_events_category`：方法 `btree`；字段：`category`
- `idx_data_events_event_date`：方法 `btree`；字段：`event_date`
- `idx_data_events_related_grades`：方法 `gin`；字段：`related_grades`
- `idx_data_events_source_article`：方法 `btree`；字段：`source_article_id`
- `idx_data_events_status`：方法 `btree`；字段：`status`
- `idx_data_events_sub_category`：方法 `btree`；字段：`sub_category`
- `idx_data_events_subject`：方法 `btree`；字段：`subject`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## data_daily_price

### 用途

采集标注系统-每日价格（数据轨，AI 直通 active，低置信度转 draft）

当前精确行数：13。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `source_article_id` | `uuid` | 是 | — | 来源文章外键（逻辑引用 data_articles.id，可空：数据快填/人工录入） |
| `price_date` | `date` | 否 | — | 日期（YYYY-MM-DD） |
| `category` | `text` | 否 | — | 品类（dict_industry_category） |
| `grade` | `text` | 否 | — | 钢种/品种（dict_grade） |
| `brand_full_name` | `text` | 是 | — | 品牌全称 |
| `brand_short_name` | `text` | 是 | — | 品牌简称（可空，NULL 时不参与唯一判定） |
| `origin` | `text` | 是 | — | 产地 |
| `region` | `text` | 是 | — | 区域（dict_region） |
| `market` | `text` | 是 | — | 市场/报价来源地 |
| `spec` | `text` | 是 | — | 规格 |
| `price` | `numeric` | 是 | — | 价格数值（数值一等公民，禁止字符串整串存储） |
| `unit` | `text` | 是 | — | 单位（如 元/吨） |
| `tax_status` | `text` | 是 | — | 含税状态（dict_tax_status：含税/不含税） |
| `mom_change` | `numeric` | 是 | — | 环比增减额（系统计算） |
| `mom_change_pct` | `numeric` | 是 | — | 环比增减比例（系统计算） |
| `yoy_change` | `numeric` | 是 | — | 同比增减额（系统计算） |
| `yoy_change_pct` | `numeric` | 是 | — | 同比增减比例（系统计算） |
| `reason_supply` | `text` | 是 | — | R1 供给因素 |
| `reason_demand` | `text` | 是 | — | R2 需求因素 |
| `reason_macro` | `text` | 是 | — | R3 宏观因素 |
| `reason_inventory` | `text` | 是 | — | R4 库存因素 |
| `reason_other` | `text` | 是 | — | R5 其他原因 |
| `impact_trend` | `text` | 是 | — | I1 短期价格趋势判断（看涨/看跌/震荡/观望） |
| `impact_confidence` | `text` | 是 | — | I2 趋势置信度（高/中/低） |
| `impact_detail` | `text` | 是 | — | I3 影响因素说明 |
| `impact_range` | `text` | 是 | — | I4 预计波动区间 |
| `related_event_ids` | `text[]` | 是 | — | 关联事件 ID 列表（图谱回刷缓存） |
| `data_source` | `text` | 是 | — | 数据来源：manual 人工/ai AI 抽取/system 系统 |
| `status` | `text` | 否 | `'draft'::text` | 数据轨状态机：active 正式数据（AI 直通）/draft 低置信度或异常待人工/archived 归档；failed 抽取失败可重试 |
| `ai_draft` | `jsonb` | 是 | — | AI 草稿原始内容（evidence + nature + field_reviewed，供回溯） |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `data_daily_price_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_data_daily_price_biz`：方法 `btree`；字段：`price_date`、`category`、`grade`、`brand_short_name`、`origin`、`region`、`market`、`spec`、`tax_status`、`unit`

### 普通索引

- `idx_data_daily_price_category_grade`：方法 `btree`；字段：`category`、`grade`
- `idx_data_daily_price_date`：方法 `btree`；字段：`price_date`
- `idx_data_daily_price_source_article`：方法 `btree`；字段：`source_article_id`
- `idx_data_daily_price_status`：方法 `btree`；字段：`status`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## data_weekly_inventory

### 用途

采集标注系统-每周库存（数据轨，周频；抽取模板 P2 扩展）

当前精确行数：0。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `source_article_id` | `uuid` | 是 | — | 来源文章外键（逻辑引用 data_articles.id，可空） |
| `week_key` | `text` | 是 | — | 统计周次 YYYY-W##（系统生成） |
| `date_range` | `text` | 是 | — | 日期区间 MM/DD-MM/DD（系统生成） |
| `category` | `text` | 是 | — | 品类（dict_industry_category） |
| `grade` | `text` | 是 | — | 钢种（dict_grade） |
| `brand_full_name` | `text` | 是 | — | 品牌全称（如有） |
| `brand_short_name` | `text` | 是 | — | 品牌简称（如有） |
| `inventory_type` | `text` | 是 | — | 库存类型（dict_inventory_type：市场/钢厂/港口/保税区库存） |
| `region` | `text` | 是 | — | 区域（dict_region） |
| `warehouse` | `text` | 是 | — | 具体市场/仓库 |
| `inventory_qty` | `numeric` | 是 | — | 库存量 |
| `unit` | `text` | 是 | — | 单位 |
| `mom_change` | `numeric` | 是 | — | 环比增减额（系统计算） |
| `mom_change_pct` | `numeric` | 是 | — | 环比增减比例（系统计算） |
| `yoy_change` | `numeric` | 是 | — | 同比增减额（系统计算） |
| `yoy_change_pct` | `numeric` | 是 | — | 同比增减比例（系统计算） |
| `reason_arrival` | `text` | 是 | — | R1 到货因素 |
| `reason_delivery` | `text` | 是 | — | R2 提货因素 |
| `reason_shipment` | `text` | 是 | — | R3 出库因素 |
| `reason_seasonal` | `text` | 是 | — | R4 季节性因素 |
| `reason_other` | `text` | 是 | — | R5 其他原因 |
| `impact_trend` | `text` | 是 | — | I1 库存趋势（持续增加/开始下降/维持平稳/不确定） |
| `impact_price_direction` | `text` | 是 | — | I2 对价格影响（利多/利空/中性） |
| `impact_detail` | `text` | 是 | — | I3 影响因素说明 |
| `related_event_ids` | `text[]` | 是 | — | 关联事件 ID（图谱回刷缓存） |
| `data_source` | `text` | 是 | — | 数据来源：manual/ai/system |
| `status` | `text` | 否 | `'draft'::text` | 数据轨状态机：active/draft/archived；failed 抽取失败可重试 |
| `ai_draft` | `jsonb` | 是 | — | AI 草稿原始内容（evidence + nature + field_reviewed） |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `data_weekly_inventory_pkey`：`PRIMARY KEY (id)`

### 唯一约束

无。

### 普通索引

- `idx_data_weekly_inventory_source_article`：方法 `btree`；字段：`source_article_id`
- `idx_data_weekly_inventory_status`：方法 `btree`；字段：`status`
- `idx_data_weekly_inventory_week`：方法 `btree`；字段：`week_key`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## data_monthly_production

### 用途

采集标注系统-每月产量（数据轨，月频；抽取模板 P2 扩展）

当前精确行数：0。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `source_article_id` | `uuid` | 是 | — | 来源文章外键（逻辑引用 data_articles.id，可空） |
| `month_key` | `text` | 是 | — | 统计月份 YYYY-MM（系统生成） |
| `category` | `text` | 是 | — | 品类（dict_industry_category） |
| `grade` | `text` | 是 | — | 钢种（dict_grade） |
| `brand_full_name` | `text` | 是 | — | 品牌全称 |
| `brand_short_name` | `text` | 是 | — | 品牌简称 |
| `factory_origin` | `text` | 是 | — | 钢厂/产地 |
| `region` | `text` | 是 | — | 区域（dict_region） |
| `output_qty` | `numeric` | 是 | — | 产量 |
| `unit` | `text` | 是 | — | 单位 |
| `capacity_utilization` | `numeric` | 是 | — | 产能利用率 % |
| `maintenance_status` | `text` | 是 | — | 检修/停产状态 |
| `mom_change` | `numeric` | 是 | — | 环比增减额（系统计算） |
| `mom_change_pct` | `numeric` | 是 | — | 环比增减比例（系统计算） |
| `yoy_change` | `numeric` | 是 | — | 同比增减额（系统计算） |
| `yoy_change_pct` | `numeric` | 是 | — | 同比增减比例（系统计算） |
| `reason_maintenance` | `text` | 是 | — | R1 检修因素 |
| `reason_new_capacity` | `text` | 是 | — | R2 新产能因素 |
| `reason_cut` | `text` | 是 | — | R3 减产因素 |
| `reason_seasonal` | `text` | 是 | — | R4 季节性因素 |
| `reason_policy` | `text` | 是 | — | R5 政策因素 |
| `reason_other` | `text` | 是 | — | R6 其他原因 |
| `impact_trend` | `text` | 是 | — | I1 产量趋势 |
| `impact_supply` | `text` | 是 | — | I2 对供应影响 |
| `impact_price_direction` | `text` | 是 | — | I3 对价格影响（利多/利空/中性） |
| `impact_detail` | `text` | 是 | — | I4 影响因素说明 |
| `related_event_ids` | `text[]` | 是 | — | 关联事件 ID（图谱回刷缓存） |
| `data_source` | `text` | 是 | — | 数据来源：manual/ai/system |
| `status` | `text` | 否 | `'draft'::text` | 数据轨状态机：active/draft/archived；failed 抽取失败可重试 |
| `ai_draft` | `jsonb` | 是 | — | AI 草稿原始内容（evidence + nature + field_reviewed） |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `data_monthly_production_pkey`：`PRIMARY KEY (id)`

### 唯一约束

无。

### 普通索引

- `idx_data_monthly_production_month`：方法 `btree`；字段：`month_key`
- `idx_data_monthly_production_source_article`：方法 `btree`；字段：`source_article_id`
- `idx_data_monthly_production_status`：方法 `btree`；字段：`status`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## data_quarterly_demand

### 用途

采集标注系统-每季度需求量（数据轨，季频；抽取模板 P2 扩展）

当前精确行数：0。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `source_article_id` | `uuid` | 是 | — | 来源文章外键（逻辑引用 data_articles.id，可空） |
| `quarter_key` | `text` | 是 | — | 统计季度 YYYY-Q#（系统生成） |
| `category` | `text` | 是 | — | 品类（dict_industry_category） |
| `grade` | `text` | 是 | — | 钢种（dict_grade） |
| `downstream_industries` | `text[]` | 是 | — | 下游行业（多选） |
| `application_scenarios` | `text` | 是 | — | 具体应用场景 |
| `region` | `text` | 是 | — | 区域（dict_region） |
| `demand_qty` | `numeric` | 是 | — | 需求量/消费量 |
| `unit` | `text` | 是 | — | 单位 |
| `apparent_consumption` | `numeric` | 是 | — | 表观消费量 |
| `mom_change` | `numeric` | 是 | — | 环比增减额（系统计算） |
| `mom_change_pct` | `numeric` | 是 | — | 环比增减比例（系统计算） |
| `yoy_change` | `numeric` | 是 | — | 同比增减额（系统计算） |
| `yoy_change_pct` | `numeric` | 是 | — | 同比增减比例（系统计算） |
| `reason_industry` | `text` | 是 | — | R1 行业景气因素 |
| `reason_substitute` | `text` | 是 | — | R2 替代品因素 |
| `reason_export` | `text` | 是 | — | R3 出口因素 |
| `reason_infrastructure` | `text` | 是 | — | R4 基建因素 |
| `reason_seasonal` | `text` | 是 | — | R5 季节性因素 |
| `reason_other` | `text` | 是 | — | R6 其他原因 |
| `impact_trend` | `text` | 是 | — | I1 需求趋势 |
| `impact_price_direction` | `text` | 是 | — | I2 对价格影响（利多/利空/中性） |
| `impact_detail` | `text` | 是 | — | I3 影响因素说明 |
| `related_event_ids` | `text[]` | 是 | — | 关联事件 ID（图谱回刷缓存） |
| `data_source` | `text` | 是 | — | 数据来源：manual/ai/system |
| `status` | `text` | 否 | `'draft'::text` | 数据轨状态机：active/draft/archived；failed 抽取失败可重试 |
| `ai_draft` | `jsonb` | 是 | — | AI 草稿原始内容（evidence + nature + field_reviewed） |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `data_quarterly_demand_pkey`：`PRIMARY KEY (id)`

### 唯一约束

无。

### 普通索引

- `idx_data_quarterly_demand_quarter`：方法 `btree`；字段：`quarter_key`
- `idx_data_quarterly_demand_source_article`：方法 `btree`；字段：`source_article_id`
- `idx_data_quarterly_demand_status`：方法 `btree`；字段：`status`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## data_analysis

### 用途

采集标注系统-分析表（A 事件解读 / B 数据解读合并一表；抽取模板 P2 扩展）

当前精确行数：0。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `source_article_id` | `uuid` | 是 | — | 来源文章外键（逻辑引用 data_articles.id，可空） |
| `analysis_id` | `text` | 是 | — | 对外 ID（ANA-YYYYMMDD-A/BXXX，唯一） |
| `analysis_type` | `text` | 是 | — | 解读类型：A 事件解读/B 数据解读 |
| `related_event_ids` | `text[]` | 是 | — | A2/B3 关联事件 ID（图谱回刷缓存） |
| `related_data_ids` | `text[]` | 是 | — | A3/B2 关联数据 ID（图谱回刷缓存） |
| `title` | `text` | 是 | — | A4/B4 解读标题（≤30 字） |
| `analysis_subtype` | `text[]` | 是 | — | A5 解读类型多选（dict_analysis_type：原因解读/影响评估/趋势研判/风险提示/机会提示） |
| `anomaly_type` | `text` | 是 | — | B5 异动类型（涨/跌/持平/异常波动；B 类用） |
| `anomaly_magnitude` | `text` | 是 | — | B6 异动幅度（B 类用） |
| `dimensions` | `text[]` | 是 | — | B7 涉及维度（B 类用） |
| `analyst_id` | `text` | 是 | — | 分析师 ID |
| `analyst_name` | `text` | 是 | — | A6/A7/B10 分析师姓名（分析撰写人） |
| `analyzed_at` | `timestamp with time zone` | 是 | — | A8/B11 解读时间 |
| `core_conclusion` | `text` | 是 | — | A9/B12 核心结论（填空模板，≤200 字） |
| `related_grades` | `text[]` | 是 | — | A10/B8 涉及钢种（多选） |
| `related_regions` | `text[]` | 是 | — | A11/B9 涉及地域（多选） |
| `time_dimension` | `text` | 是 | — | A12 时间维度（即时/1日内/1周内/1月内） |
| `confidence` | `smallint` | 是 | — | A13/B13 置信度 1-5 星（判断类字段，必须人工确认） |
| `detail` | `text` | 是 | — | AO1/BO1 详细解读（≤2000 字） |
| `data_comparison` | `text` | 是 | — | AO2/BO2 数据对比/异动原因 |
| `affected_companies` | `text[]` | 是 | — | AO3 受影响企业 |
| `historical_comparison` | `text` | 是 | — | AO4 历史同类事件对比 |
| `anomaly_reasons` | `text[]` | 是 | — | BO2 异动原因（7 大类枚举） |
| `impact` | `text` | 是 | — | BO3 异动影响 |
| `forecast_directions` | `jsonb` | 是 | — | BO4 数据预测方向（短期/中期/长期 × 看涨/看跌/震荡） |
| `follow_up` | `jsonb` | 是 | — | AO5/BO5 后续跟踪/建议 |
| `source_links` | `text[]` | 是 | — | AO6 信源链接 |
| `attachments` | `jsonb` | 是 | — | AO7 附件 |
| `remark` | `text` | 是 | — | AO8/BO6 备注 |
| `ai_draft` | `jsonb` | 是 | — | AI 草稿原始内容（evidence + nature + field_reviewed，供回溯） |
| `content_source` | `text` | 是 | — | 内容来源性质：extracted 抽取自原文 OPINION/ai_generated AI 生成 INFERENCE/manual 人工撰写 |
| `reviewed_by` | `text` | 是 | — | 校核人 |
| `reviewed_at` | `timestamp with time zone` | 是 | — | 校核时间 |
| `status` | `text` | 否 | `'draft'::text` | 业务记录状态机：draft/confirmed/archived；非主链 skipped/rejected；failed 抽取失败可重试 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `data_analysis_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_data_analysis_analysis_id`：方法 `btree`；字段：`analysis_id`

### 普通索引

- `idx_data_analysis_source_article`：方法 `btree`；字段：`source_article_id`
- `idx_data_analysis_status`：方法 `btree`；字段：`status`
- `idx_data_analysis_type`：方法 `btree`；字段：`analysis_type`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## data_forecast

### 用途

采集标注系统-预测表（P 价格/Q 库存/R 需求产量合并一表；抽取模板 P2 扩展）

当前精确行数：0。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `source_article_id` | `uuid` | 是 | — | 来源文章外键（逻辑引用 data_articles.id，可空） |
| `forecast_id` | `text` | 是 | — | 对外 ID（PRC-/INV-/DMN-YYYYMMDD-XXX，唯一） |
| `forecast_type` | `text` | 是 | — | 预测类型：P 价格/Q 库存/R 需求产量 |
| `target` | `jsonb` | 是 | — | 预测对象 {grade, spec, region, dimension, warehouse_type, industry…} |
| `forecast_period` | `text` | 是 | — | 预测时间（今日/明日/本周/本月/本季度，按类型不同档位） |
| `current_value` | `numeric` | 是 | — | P4/Q4/R4 当前数值（系统引用） |
| `forecast_value` | `numeric` | 是 | — | P5/Q5/R5 预测数值（判断类，必须人工确认） |
| `direction` | `text` | 是 | — | 涨/跌/持平 或 增/减/持平 |
| `forecast_pct` | `numeric` | 是 | — | P6/Q6/R6 预测幅度（系统计算） |
| `time_window` | `text` | 是 | — | P7/Q7/R7 时间窗口（1日/7日/30日/90日/180日） |
| `related_event_ids` | `text[]` | 是 | — | P8/Q8/R8 关联事件 ID（图谱回刷缓存） |
| `related_analysis_ids` | `text[]` | 是 | — | P9/Q9/R9 关联解读 ID（图谱回刷缓存） |
| `related_history_ids` | `text[]` | 是 | — | P10 关联历史数据 ID |
| `model_type` | `text` | 是 | — | 预测模型（dict_forecast_model：AI金LLM/历史规律/专家经验/综合） |
| `confidence` | `smallint` | 是 | — | P12 置信度 1-5 星（判断类，必须人工确认） |
| `forecaster` | `text` | 是 | — | P13 预测来源：人工=分析师姓名，AI=AI 金模型版本号 |
| `content_source` | `text` | 是 | — | 内容来源性质：ai_generated AI 生成草稿 INFERENCE/manual 人工分析师 OPINION |
| `detail` | `text` | 是 | — | PO1 详细预测依据（≤2000 字） |
| `key_variables` | `jsonb` | 是 | — | PO2 关键变量 [{name, current, expected}] |
| `upside_risks` | `text[]` | 是 | — | PO3 上行风险 |
| `downside_risks` | `text[]` | 是 | — | PO4 下行风险 |
| `historical_accuracy_pct` | `numeric` | 是 | — | PO5 模型历史准确率 % |
| `forecast_range` | `text` | 是 | — | PO6 预测区间 |
| `follow_up` | `text` | 是 | — | PO7 跟踪建议 |
| `remark` | `text` | 是 | — | PO8 备注 |
| `actual_value` | `numeric` | 是 | — | 预测回填：到期后系统回填实际值 |
| `forecast_error_pct` | `numeric` | 是 | — | 预测误差率（系统计算：\|预测-实际\|/\|实际\|） |
| `verified_at` | `timestamp with time zone` | 是 | — | 回填验证时间 |
| `review_status` | `text` | 否 | `'draft'::text` | 内容审核状态：draft AI 草稿/confirmed 已确认发布/archived 归档 |
| `verification_status` | `text` | 否 | `'pending'::text` | 预测验证状态（与审核状态正交）：pending 未到期/verified 已回填验证 |
| `ai_draft` | `jsonb` | 是 | — | AI 草稿原始内容（evidence + nature + field_reviewed，供回溯） |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `data_forecast_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_data_forecast_forecast_id`：方法 `btree`；字段：`forecast_id`

### 普通索引

- `idx_data_forecast_review_status`：方法 `btree`；字段：`review_status`
- `idx_data_forecast_source_article`：方法 `btree`；字段：`source_article_id`
- `idx_data_forecast_type`：方法 `btree`；字段：`forecast_type`
- `idx_data_forecast_verification_status`：方法 `btree`；字段：`verification_status`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## data_content

### 用途

采集标注系统-生成内容产物表（独立于 data_articles，多平台多风格草稿与定稿）

当前精确行数：42。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `content_id` | `text` | 是 | — | 对外 ID（CTN-YYYYMMDD-XXX，唯一） |
| `title` | `text` | 是 | — | 标题 |
| `content` | `text` | 是 | — | 正文 |
| `content_type` | `text` | 是 | — | 内容形态：article 文章/card 事件卡片/newsflash 快讯/script 短视频脚本 |
| `channel` | `text` | 是 | — | 渠道（dict_channel：公众号/51号APP/抖音快手/行业群…） |
| `style` | `text` | 是 | — | 风格（dict_article_style：新闻简讯/日评/深度报道…） |
| `version` | `integer` | 否 | `1` | 版本号（重新生成递增 v1→v2→v3） |
| `source_record_ids` | `text[]` | 是 | — | 素材业务记录 ID 列表（事件/数据/分析/预测，全部为 confirmed/active） |
| `citations` | `jsonb` | 是 | — | 引用标注 [{record_id, record_type, position, evidence}] |
| `generation_history` | `jsonb` | 是 | — | 生成历史 [{version, prompt_params, model, created_at, generated_by}] |
| `reviewer` | `text` | 是 | — | 审核人 |
| `status` | `text` | 否 | `'draft'::text` | 生成内容状态机：draft AI 草稿/editing 人工修改中/confirmed 定稿/archived 归档 |
| `source_article_id` | `uuid` | 是 | — | 关联原始文章（逻辑引用 data_articles.id，可空，素材可能来自多篇） |
| `remark` | `text` | 是 | — | 备注 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `data_content_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_data_content_content_id`：方法 `btree`；字段：`content_id`

### 普通索引

- `idx_data_content_channel`：方法 `btree`；字段：`channel`
- `idx_data_content_created_at`：方法 `btree`；字段：`_created_at`
- `idx_data_content_status`：方法 `btree`；字段：`status`
- `idx_data_content_style`：方法 `btree`；字段：`style`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## data_content_citations

### 用途

采集标注系统-生成内容与素材业务记录的引用关系（一对多，支撑来源追溯与 BASED_ON 边）

当前精确行数：160。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `content_id` | `uuid` | 否 | — | 生成内容（逻辑引用 data_content.id） |
| `record_type` | `text` | 否 | — | 素材类型：event/daily_price/inventory/production/demand/analysis/forecast |
| `record_id` | `text` | 否 | — | 素材业务记录对外 ID（EVT-xxx/PRC-xxx…） |
| `position` | `text` | 是 | — | 引用位置（段落号/句子号，可空） |
| `evidence` | `text` | 是 | — | 原文依据片段（可空，配合素材表 ai_draft） |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `data_content_citations_pkey`：`PRIMARY KEY (id)`

### 唯一约束

无。

### 普通索引

- `idx_data_content_citations_content`：方法 `btree`；字段：`content_id`
- `idx_data_content_citations_record`：方法 `btree`；字段：`record_type`、`record_id`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## kg_entities

### 用途

采集标注系统-知识图谱节点表（行业实体 + 业务记录节点，业务记录入库时同步建节点）

当前精确行数：39。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `entity_id` | `text` | 是 | — | 对外 ID（ENT-xxx，唯一） |
| `name` | `text` | 否 | — | 节点标准名（实体如"太钢"；业务记录如"EVT-20260816-001"） |
| `node_category` | `text` | 否 | `'entity'::text` | 节点类别：entity 行业实体/record 业务记录 |
| `aliases` | `text[]` | 是 | — | 别名（只读缓存，唯一真源 dict_entity_alias；仅实体类节点使用，业务记录节点为空） |
| `entity_type` | `text` | 否 | — | 节点类型：实体 12 类 factory/raw_material/policy/industry/macro_indicator/region_market/product_grade/organization/person/project/trade_measure/other + 业务记录 7 类 event/daily_price/inventory/production/demand/analysis/forecast |
| `biz_record_type` | `text` | 是 | — | 业务记录节点来源表标记（data_events/data_daily_price/...）；实体节点为 NULL |
| `biz_record_id` | `text` | 是 | — | 业务记录对外 ID（EVT-xxx/PRC-xxx…）；实体节点为 NULL |
| `properties` | `jsonb` | 是 | — | 属性（如钢厂-产能、政策-发布机构、业务记录-关键数值） |
| `description` | `text` | 是 | — | 一句话描述 |
| `confidence` | `numeric` | 是 | — | 抽取置信度 |
| `source_ids` | `text[]` | 是 | — | 来源追溯缓存（provenance）：产出该节点的文章/记录 ID |
| `is_verified` | `boolean` | 否 | `false` | 是否人工核验过 |
| `status` | `text` | 否 | `'active'::text` | active 有效/merged 已合并/archived 归档 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `kg_entities_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_kg_entities_biz_record`：方法 `btree`；字段：`biz_record_type`、`biz_record_id`
- `uq_kg_entities_entity_id`：方法 `btree`；字段：`entity_id`

### 普通索引

- `idx_kg_entities_aliases`：方法 `gin`；字段：`aliases`
- `idx_kg_entities_entity_type`：方法 `btree`；字段：`entity_type`
- `idx_kg_entities_name`：方法 `btree`；字段：`name`
- `idx_kg_entities_node_category`：方法 `btree`；字段：`node_category`
- `idx_kg_entities_status`：方法 `btree`；字段：`status`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

## kg_relations

### 用途

采集标注系统-知识图谱关系边表（全系统关系唯一真源；同对节点同类型允许多条，relation_id 唯一）

当前精确行数：94。

### 字段

| 字段名 | PostgreSQL类型 | 是否可空 | 默认值 | 字段注释 |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 UUID |
| `relation_id` | `text` | 是 | — | 对外 ID（REL-xxx，唯一） |
| `source_entity_id` | `uuid` | 否 | — | 起点节点（逻辑引用 kg_entities.id，实体或业务记录） |
| `target_entity_id` | `uuid` | 否 | — | 终点节点（逻辑引用 kg_entities.id，实体或业务记录） |
| `relation_type` | `text` | 否 | — | 关系类型：CAUSED_BY/IMPACTS/LEADS_TO/REFERS_TO/PRODUCES/USES/IS_A/LOCATED_IN/ANNOUNCED_BY/ASSOCIATED_WITH/PREDICTS/VERIFIES |
| `nature` | `text` | 否 | `'FACT'::text` | 关系性质：FACT 原文明确事实/OPINION 原文观点/INFERENCE AI 推断 |
| `properties` | `jsonb` | 是 | — | 关系属性（如影响程度 direction、magnitude、时间 time） |
| `confidence` | `numeric` | 是 | — | 置信度 |
| `source_ids` | `text[]` | 是 | — | 来源追溯缓存（provenance） |
| `is_verified` | `boolean` | 否 | `false` | 是否人工核验 |
| `status` | `text` | 否 | `'active'::text` | active 有效/merged 已合并/archived 归档 |
| `_created_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_updated_at` | `timestamp with time zone` | 是 | `now()` | 数据库未设置字段注释 |
| `_created_by` | `text` | 是 | — | 数据库未设置字段注释 |
| `_updated_by` | `text` | 是 | — | 数据库未设置字段注释 |

### 主键

- `kg_relations_pkey`：`PRIMARY KEY (id)`

### 唯一约束

- `uq_kg_relations_relation_id`：方法 `btree`；字段：`relation_id`

### 普通索引

- `idx_kg_relations_source_type`：方法 `btree`；字段：`source_entity_id`、`relation_type`
- `idx_kg_relations_status`：方法 `btree`；字段：`status`
- `idx_kg_relations_target_type`：方法 `btree`；字段：`target_entity_id`、`relation_type`

### 外键

无。

### CHECK约束

无。

### RLS

未启用（`pg_class.relrowsecurity = false`）。

# 三、字段标准问题

本章只记录当前数据库系统元数据和现有数据能够直接证明的结构或值域差异。“高度相似字段”可能是有意的缓存、快照或派生字段，不等同于必须删除。

## 3.1 同类字段命名不一致

- 审核人字段同时存在 `reviewed_by`（`data_articles`、`data_analysis`）和 `reviewer`（`data_content`）。
- 状态字段主要使用 `status`，但 `data_forecast` 拆分为 `review_status` 与 `verification_status`。两者语义正交，但统一状态查询需要单独适配。
- 产地字段在日价表使用 `origin`，在月产量表使用 `factory_origin`。
- 外部业务编号分别使用 `event_id`、`analysis_id`、`forecast_id`、`content_id`、`entity_id`、`relation_id`；日价、周库存、月产量、季需求表没有对应的对外业务编号字段。
- 时间主键按频率分别使用 `price_date`、`week_key`、`month_key`、`quarter_key`，事件使用 `event_date`。这是频率差异，但跨表时间查询没有统一字段名。

## 3.2 字典值与业务表实际值不一致


### data_events.(category, sub_category) → dict_event_sub_category.(category, name)

- `category`=`A`，`value`=`产线改造`，`row_count`=`1`
- `category`=`A`，`value`=`产业政策`，`row_count`=`1`
- `category`=`A`，`value`=`复产投产`，`row_count`=`1`
- `category`=`A`，`value`=`停产减产`，`row_count`=`1`
- `category`=`B`，`value`=`库存变化`，`row_count`=`1`

下列对照在当前已有数据中未发现越界值：

- `data_events.category → dict_event_category.code`
- `data_events.related_grades[] → dict_grade.name`
- `data_events.related_regions[] → dict_region.name`
- `data_daily_price.category → dict_industry_category.name`
- `data_daily_price.grade → dict_grade.name`
- `data_daily_price.region → dict_region.name`
- `data_daily_price.tax_status → dict_tax_status.name`
- `data_weekly_inventory.inventory_type → dict_inventory_type.name`
- `data_analysis.analysis_subtype[] → dict_analysis_type.name`
- `data_forecast.model_type → dict_forecast_model.name`
- `data_content.channel → dict_channel.name`
- `data_content.style → dict_article_style.name`

以下表当前为0行，只能确认结构，无法用实际业务值验证字典一致性：`data_analysis`、`data_forecast`、`data_monthly_production`、`data_quarterly_demand`、`data_weekly_inventory`。

## 3.3 明显绕过字典的值

当前 `data_events` 存在以下 `category + sub_category` 组合，在 `dict_event_sub_category` 中找不到完全匹配项：

- `category`=`A`，`value`=`产线改造`，`row_count`=`1`
- `category`=`A`，`value`=`产业政策`，`row_count`=`1`
- `category`=`A`，`value`=`复产投产`，`row_count`=`1`
- `category`=`A`，`value`=`停产减产`，`row_count`=`1`
- `category`=`B`，`value`=`库存变化`，`row_count`=`1`

数据库层没有针对上述字典字段的外键或 CHECK 约束，因此应用层、导入脚本或历史数据可以写入字典外值。

## 3.4 逻辑关联但没有FK的字段

当前24张表的真实外键数量为 0。以下字段从名称或数据库注释可确认承担逻辑关联，但没有 PostgreSQL FK：

| 表 | 逻辑关联字段 | 注释或命名指向 |
| --- | --- | --- |
| `data_articles` | `duplicate_of` | data_articles.id |
| `data_events` | `source_article_id` | data_articles.id |
| `data_events` | `related_data_ids / related_analysis_ids / related_forecast_ids` | 对应业务记录或图谱缓存 |
| `data_daily_price` | `source_article_id / related_event_ids` | data_articles.id / data_events.event_id |
| `data_weekly_inventory` | `source_article_id / related_event_ids` | data_articles.id / data_events.event_id |
| `data_monthly_production` | `source_article_id / related_event_ids` | data_articles.id / data_events.event_id |
| `data_quarterly_demand` | `source_article_id / related_event_ids` | data_articles.id / data_events.event_id |
| `data_analysis` | `source_article_id / related_event_ids / related_data_ids` | 文章、事件及数据业务记录 |
| `data_forecast` | `source_article_id / related_event_ids / related_analysis_ids / related_history_ids` | 文章、事件、分析及历史记录 |
| `data_content` | `source_article_id / source_record_ids` | 原始文章及素材业务记录 |
| `data_content_citations` | `content_id / record_id` | data_content.id 及各素材业务记录 |
| `kg_entities` | `biz_record_id / source_ids` | 业务记录及来源追溯 |
| `kg_relations` | `source_entity_id / target_entity_id / source_ids` | kg_entities.id 及来源追溯 |

## 3.5 注释标准与实际值不一致

| 字段 | 注释标准 | 当前注释外实际值 | 行数 |
| --- | --- | --- | ---: |
| `data_daily_price.data_source` | 注释限定 manual/ai/system | `51bxg` | 2 |
| `data_daily_price.data_source` | 注释限定 manual/ai/system | `51不锈钢` | 6 |
| `data_daily_price.data_source` | 注释限定 manual/ai/system | `51不锈钢测试` | 1 |
| `data_daily_price.data_source` | 注释限定 manual/ai/system | `51不锈钢网` | 2 |
| `data_daily_price.data_source` | 注释限定 manual/ai/system | `手动投稿` | 1 |
| `data_daily_price.status` | 注释列出 active/draft/archived/failed | `skipped` | 1 |
| `kg_entities.entity_type` | 注释列出行业实体12类及业务记录7类 | `grade` | 5 |
| `kg_entities.entity_type` | 注释列出行业实体12类及业务记录7类 | `market` | 2 |
| `kg_entities.entity_type` | 注释列出行业实体12类及业务记录7类 | `region` | 3 |
| `kg_entities.biz_record_type` | 注释称保存 data_events/data_daily_price/... 来源表标记 | `daily_price` | 9 |
| `kg_entities.biz_record_type` | 注释称保存 data_events/data_daily_price/... 来源表标记 | `event` | 11 |

## 3.6 重复或高度相似字段

- `data_content.citations` 以 JSONB 保存引用列表，同时 `data_content_citations` 逐条保存相同引用关系，属于“主表快照 + 明细表”双存储。
- `data_content.source_record_ids`、`data_content.citations.record_id` 和 `data_content_citations.record_id` 均保存素材来源ID。
- `dict_entity_alias` 是实体别名唯一真源，而 `kg_entities.aliases` 是别名数组缓存。
- 多张 `data_*` 表保存 `related_*_ids` 数组，同时 `kg_relations` 被注释为关系唯一真源，前者属于关系回刷缓存。
- `data_articles.related_entity_ids` 与 `kg_entities.source_ids` / `kg_relations.source_ids` 都承担来源或关联缓存，但方向和粒度不同。
- `data_events.validity_days` 与 `valid_until` 同时保存有效期参数和派生日期；`data_forecast.forecast_value`、`actual_value`、`forecast_error_pct` 同时保存预测、回填值和派生误差。
- 日价、库存、产量、需求表同时保存 `mom_change` / `mom_change_pct` 和 `yoy_change` / `yoy_change_pct`，属于绝对值与比例值，需要同步计算。

## 3.7 数据库约束层面的客观结论

- 24张表均有 UUID 主键。
- 当前真实外键数量：0。
- 当前真实 CHECK 约束数量：0。
- 当前启用 RLS 的表数量：0；`pg_policies` 策略数量：0。
- 唯一性主要通过独立 UNIQUE INDEX 实现，而不是 `pg_constraint` 中的 UNIQUE 约束。
