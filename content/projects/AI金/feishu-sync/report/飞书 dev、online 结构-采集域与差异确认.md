# 飞书 dev/online 结构 —— 采集域与差异确认

> 导出时间：dev=2026-08-25T14:11:43.909Z / online=2026-08-25T14:13:07.066Z
> schema：workspace_aadkdvw4kawau

## 一、表数量

| 维度 | dev | online |
| --- | --- | --- |
| tables[] 数 | 40 | 40 |
| all_relations_audit 数 | 58 | 57 |
| 报告 table_count | 40 | 40 |

## 二、采集域（AI金采集）表是否存在

- **dict_**: dev=缺失(0)  |  online=缺失(0)
- **data_**: dev=缺失(0)  |  online=缺失(0)
- **kg_**: dev=缺失(0)  |  online=缺失(0)
- **import_**: dev=缺失(0)  |  online=缺失(0)

### 关键单表现状

- batch_daily_token: dev=缺失 | online=缺失
- erp_user_account: dev=缺失 | online=缺失
- report_user_skill: dev=缺失 | online=缺失
- price_hongwang: dev=缺失 | online=缺失
- price_kucun: dev=缺失 | online=缺失
- report_user_account: dev=缺失 | online=缺失
- report_user_skills: dev=缺失 | online=缺失

## 三、dev vs online 表清单差异

- 仅 dev 有（0）：无

- 仅 online 有（0）：无

## 四、防漏表校验（all_relations_audit 有 但 tables[] 未展开的表）

- dev 漏展开：_volc_dts_pg_ddl_c7e8a74cbb5748a6add942090258f5ac、_volc_dts_pg_ddl_ecaa9f69ea124388872e710b554782fd、app_mapping、app_resources、buckets、mt_enum、mt_foreign_server、mt_function、mt_migration、mt_table、mt_trigger、mt_workspace、objects、suda_buckets、suda_objects、suda_pats、suda_users、workspace_admin
- online 漏展开：_volc_dts_pg_ddl_ecaa9f69ea124388872e710b554782fd、app_mapping、app_resources、buckets、mt_enum、mt_foreign_server、mt_function、mt_migration、mt_table、mt_trigger、mt_workspace、objects、suda_buckets、suda_objects、suda_pats、suda_users、workspace_admin
