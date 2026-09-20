# 飞书数据库对齐 —— 迁移执行说明

> 目标：把「本地 bxg_app（最新）」与「飞书 dev / online」数据库结构+种子数据对齐到一致且更规范的水平。
> 所有 SQL 均为**只读本地导出、交由你在飞书沙箱终端执行**，本机不直接改飞书库。

## 执行环境

`miaoda` 只在**妙搭沙箱终端**存在，你本地终端没有。所有脚本在沙箱执行。

**️ 关键机制（2026-08-25 实测确认）：**
- **DDL（表结构）通过发布自动同步**：`miaoda deploy` 时 pipeline 含"数据库更新"步骤，自动对比 dev/online 差异并 apply DDL 到 online
- **DML（数据）需手动同步**：`miaoda db sql < file.sql --env online`
- **⛔ online 禁止手动 DDL/DCL**（错误 `k_dl_4000001` / "forbid ddl/dcl operation in online env"）：可视化 SQL 编辑器与 `miaoda db sql --env online` 都会拒绝 CREATE/ALTER/DROP 等。**online 的 DDL 只能靠 deploy 自动同步**，不要手动执行含 DDL 的脚本（如 05 的 DROP+CREATE 会报错）。
- **online 的 DML 用可视化 SQL 编辑器执行**（INSERT/UPDATE/DELETE 允许，实测 03 成功）；`miaoda db sql --env online` 在终端可能报 `loginUser is nil`（认证问题），优先用可视化 SQL 编辑器。

**dev（开发库）—— 手动执行全部脚本：**

```bash
miaoda db sql < 01_add_tables.sql      # 建表
miaoda db sql < 02_fix_shared.sql      # 补列/索引
miaoda db sql < 03_seed_dicts.sql      # 预填字典数据
```

**online（线上库）—— 发布 + 手动灌数据（仅 DML）：**

```bash
# 1. 发布（自动同步 DDL 到 online；发布前先 npm install 新增依赖）
miaoda deploy

# 2. 手动灌种子数据（数据不同步，需手动；用可视化 SQL 编辑器执行纯 DML 文件）
#    03_seed_dicts.sql 内容 → online 可视化 SQL 编辑器
#    08_seed_report_user_skill.sql 内容 → online 可视化 SQL 编辑器
```

## 执行顺序

### dev（开发库）

按顺序执行：

```bash
miaoda db sql < 01_add_tables.sql      # 1. 新增 40 张表
miaoda db sql < 02_fix_shared.sql      # 2. 共有表补列/索引
miaoda db sql < 03_seed_dicts.sql      # 3. 预填字典数据
```

### online（线上库）

```bash
# 1. 发布（自动同步 DDL 到 online；发布前先 npm install 新增依赖）
miaoda deploy

# 2. 手动灌种子数据（仅 DML，用 online 可视化 SQL 编辑器执行纯 DML 文件）
#    03_seed_dicts.sql 内容 → online 可视化 SQL 编辑器
#    08_seed_report_user_skill.sql 内容 → online 可视化 SQL 编辑器
```

| 文件 | 内容 | 说明 |
|---|---|---|
| `01_add_tables.sql` | 新增 40 张表（本地有、飞书缺） | 采集域 32 + 应用域 8；全部 `IF NOT EXISTS` 可重复执行 |
| `02_fix_shared.sql` | 共有表补齐（飞书缺列/缺索引） | `plaza_images` 补 2 列、`vip_packages`/`xiuma_product_snapshot` 补 2 个普通索引 |
| `03_seed_dicts.sql` | 字典/种子数据预填 | 15 张 `dict_*` 共 185 行，保留主键 id 保引用 |
| `04_price_tables.sql` | 5 张价格表（权威 026~030） | `IF NOT EXISTS` 可重复执行 |
| `05_fix_report_user_skill.sql` | report_user_skill 重建为权威 6 列 + admin 行 | 含 DDL（DROP+CREATE），**仅 dev 可执行**；online 的 DDL 靠 deploy 同步、admin 行用 08 |
| `06_feishu_dev_sync.sql` | 补飞书 dev：价格表 + report_user_skill 修正 | 合并 04+05，仅 dev 执行 |
| `07_drop_dead_tables.sql` | 删除 5 张死表 | `DROP IF EXISTS` 幂等；online 靠 deploy 同步 |
| `08_seed_report_user_skill.sql` | erp_user_account.admin + report_user_skill.admin 行（纯 DML） | **online 可视化 SQL 编辑器执行**；先插 FK 父表 erp_user_account 再插 report_user_skill；`ON CONFLICT DO NOTHING` 幂等 |
| `09_seed_users_avatar.sql` | users.avatar_data 补全（本地 bytea→base64，纯 DML） | **online 可视化 SQL 编辑器执行**；4 个用户头像；UPDATE 幂等；修复头像接口 404 |

每组内同末尾文件也可拆分到 `01_create/`（每表一个 .sql）按需单独执行。

## 注意事项

- **表名不带 schema 前缀**（平台按工作区自动路由）。
- 遵循 PG 方言；已按「分批 / ≤1000 行」拆分避免沙箱 30s 超时与超大语句；若单次超时再拆表执行。
- **序列依赖（重要）**：`content_tasks`、`platform_sessions` 的 `id` 用 `nextval('..._id_seq')` 默认值，DDL 已在其建表前显式声明 `CREATE SEQUENCE IF NOT EXISTS ... + ALTER SEQUENCE ... OWNED BY <表>.id`。**勿删这两行**，否则在无同名序列的全新库建表会直接失败。
- **发布冻结警告**：本任务里的 033 一期涉及表单结构/迁移，**落库完成前严禁 `miaoda deploy`**，避免代码与库结构不一致。
- RLS / 审计列：已有表结构含 `_created_at/_updated_at/_created_by/_updated_by` 等，本批新增表已按本地定义生成。

## 执行后校验

执行完成后重新采集飞书两端结构（见 `queries/飞书大模型-结构导出提示词.md`），覆盖 `feishu-sync/feishu-{dev,online}/` 后重跑：

```bash
node feishu-sync/compare.mjs   # 重新输出 report/对比报告.md，应不再有「需新增」与补列/补索引项
```

---

## 附：本地收敛建议（可选，飞书更规范 → 本地补齐）

按你选择的「收敛到更规范」方向，以下项**飞书本就符合规范（无需改飞书），本地对应偏差建议回填**。如不需要可忽略，不影响上线。仅作本地 DDL 参考，**勿在飞书执行**。

1. **时间类型统一为 `timestamptz`（本地为 `timestamp without time zone`）**，涉及 4 表 19 列：
   - `plaza_demands`：`expired_at`、`created_at`、`updated_at`
   - `plaza_notifications`：`read_at`、`occurred_at`、`created_at`、`updated_at`、`expires_at`
   - `xiuma_member_contact`：`create_time`、`sync_time`、`created_at`、`updated_at`
   - `xiuma_product_snapshot`：`upload_time`、`sale_end_time`、`create_time`、`import_time`、`sync_time`、`created_at`、`updated_at`
2. **补唯一约束（飞书有、本地无）**：
   - `price_baogangdesheng_304_no1` / `price_ningbobaoxin_430_2b` / `price_taigangbuxiu_304_2b`：`UNIQUE (price_date)`
   - `trade_deal_records`：`UNIQUE (product_id)`；`ai_jin_auth_credentials`：`UNIQUE (mobile) WHERE mobile IS NOT NULL`
   - `xiuma_product_snapshot`：`UNIQUE (product_code)`
3. **`trade_view_rules`** 加 4 审计列：`_created_at`、`_updated_at`（`timestamptz DEFAULT now()`）、`_created_by`、`_updated_by`（`text`）。
4. **`users.avatar_data`**：`text` → `bytea`（与飞书一致）。
5. **`plaza_posts.visibility`**：改为 `NOT NULL DEFAULT 'public'`。
6. `plaza_demands.tags`（本地 `NOT NULL DEFAULT '[]'::text` vs 飞书可空）：飞书更宽松，本地可保留不改。

> 各列精确类型/默认见 `feishu-sync/target/local-schema.json`。本地收敛建议会随限时版本更新，如需在本地应用请在**本地数据库**手动执行。