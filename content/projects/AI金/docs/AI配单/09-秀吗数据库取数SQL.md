# 秀吗数据取数与 ERP 导出指南

> 生成：2026-08-16
> 用途：为 AI金 配单本地快照表补充 PRODUCT_ID 映射与供应商联系方式
> 数据获取原则（2026-08-16 确认）：**优先从 ERP 后台导出，不用 SQL 查询**；SQL 仅作为一次性/兜底手段

---

## 一、PRODUCT_ID 映射（从 ERP 后台导出，不用 SQL）

### 背景

货品导出文件（"下载结果"）不含数字 `PRODUCT_ID`（PRODUCT_ID 是页面隐藏列），但跳转秀吗详情页和成交下架都需要它。

已确认：**秀吗所有产品页面的"下载结果"默认都不含 PRODUCT_ID**（代码设计如此，`GetFormatter(false)` 排除隐藏列）。且不改秀吗代码。

### 方法 A：浏览器控制台导出（推荐，纯 ERP 后台操作）

秀吗 ERP 页面查询后，数据其实已含 PRODUCT_ID（只是表格隐藏），可从中导出：

1. 打开秀吗 ERP「卷板—信息」页面 → 查询出数据
2. 按 F12 → Console（控制台）
3. 粘贴执行 `scripts/xiuma-erp-export-with-id.js` 的内容（AI金 仓库 scripts 目录）
4. 自动下载 `product_info_with_id_YYYYMMDD.csv`，**含 PRODUCT_ID 列**

适用：新上架货品量少时补映射；或需要完整含 ID 数据时。

### 方法 B：数据库只读 SQL（一次性/兜底）

```sql
-- 库：ZERP_ERP
SELECT
    P.PRODUCT_CODE AS product_code,
    P.PRODUCT_ID   AS product_id
FROM ZERP_ERP.dbo.ERP_PRODUCT_INFO P (NOLOCK)
JOIN ZERP_ERP.dbo.ERP_BATCH_STOCK BS (NOLOCK)
    ON BS.PRODUCT_ID = P.PRODUCT_ID AND BS.PRODUCT_STATUS = 0
WHERE P.PRODUCT_TYPE = 0          -- 0=现货
GROUP BY P.PRODUCT_CODE, P.PRODUCT_ID;
```

- 已执行一次：**3011 条**，导入本地快照表（2026-08-16）
- 后续日常不需重复执行——本地已存映射，日常导入自动沿用（`upsertByCode` 已修复：无 PRODUCT_ID 的日常文件不会清空已有映射）

### 上传

导出文件（两列 `product_code` / `product_id`）上传到 AI金 ERP → 秀吗数据导入 → "PRODUCT_ID 映射"

---

## 二、供应商联系方式（补 TELEPHONE / SUPPLIER_ID / 会员等级）

AI金 配单展示联系方式来自两个来源，建议**都导出**后按需上传：

### 2.1 会员联系方式（原接口 LV.TELEPHONE 来源，含会员等级）

原配单接口的联系方式是"该供应商下会员等级最高的会员电话"，来自 `ERP_MEMBER_INFO`（按 `SUPPLIER_ID` 关联）。AI金 页面"查看联系方式"应展示此电话。

```sql
-- 库：ZERP_ERP
SELECT
    MI.SUPPLIER_ID                AS supplier_id,
    S.SUPPLIER_NAME               AS supplier_name,
    MI.MEMBER_ID                  AS member_id,
    MI.MEMBER_NAME                AS member_name,
    MI.TELEPHONE                  AS telephone,
    E.COL_VAL                     AS member_level_name
FROM ZERP_ERP.dbo.ERP_MEMBER_INFO MI (NOLOCK)
LEFT JOIN ZERP_ERP.dbo.ERP_SUPPLIER_INFO S (NOLOCK)
    ON S.SUPPLIER_ID = MI.SUPPLIER_ID
LEFT JOIN (
    SELECT MEMBER_ID, MAX(LEVEL_ID) AS MAX_LEVEL
    FROM ZERP_ERP.dbo.ERP_MEMBER_PAY_LEVEL (NOLOCK)
    WHERE STATUS = 0
    GROUP BY MEMBER_ID
) MPL ON MPL.MEMBER_ID = MI.MEMBER_ID
LEFT JOIN ZERP_ERP.dbo.ERP_ENUM_DICT E (NOLOCK)
    ON E.DB_NAME='ZERP_ERP' AND E.TAB_NAME='ERP_MEMBER_PAY_LEVEL'
   AND E.COL_NAME='LEVEL_ID' AND E.COL_KEY = MPL.MAX_LEVEL
WHERE MI.SUPPLIER_ID IS NOT NULL AND MI.SUPPLIER_ID > 0;
```

- 列名建议：`supplier_id` / `supplier_name` / `telephone` / `member_level_name`
- 上传到 AI金 ERP → 秀吗数据导入 → "供应商联系方式"

### 2.2 供应商固定电话（supplier_info.aspx 页面数据来源）

即 `supplier_info.aspx`（供应商信息管理）查询的 `ERP_SUPPLIER_INFO` 表数据，含供应商固定电话/传真等：

```sql
-- 库：ZERP_ERP
SELECT
    S.SUPPLIER_ID     AS supplier_id,
    S.SUPPLIER_NAME   AS supplier_name,
    S.SUPPLIER_CODE   AS supplier_code,
    S.TELEPHONE       AS telephone,
    S.FAX             AS fax,
    S.MOBILE          AS mobile,
    S.CONTACT         AS contact,
    S.PRIVILEGE_ID    AS privilege_id
FROM ZERP_ERP.dbo.ERP_SUPPLIER_INFO S (NOLOCK)
WHERE S.STATUS = 0;    -- 0=有效
```

---

## 三、ERP 菜单定位（已确认，2026-08-16）

ERP 菜单树配置在 **ZERP_SYS** 库，两张关键表：

| 表名 | 用途 |
| --- | --- |
| `USERS_PRIVILEGE_MODULE_DEFINE` | 模块定义：`MODULE_NAME` 菜单名 / `MODULE_ENTRY_LINK` 页面 URL |
| `USERS_PRIVILEGE_MODULE_MENU_TREE` | 菜单树：`ID` / `PARENT_ID` / `MENU_TEXT` 文件夹节点 |

### 已确认的菜单路径

| 菜单项 | 完整路径 | 页面 URL | 模块 ID |
| --- | --- | --- | --- |
| 供应商 | `ERP → 基础信息 → 商家信息 → 供应商` | `/erp/modules/erp/business_information/supplier_info.aspx` | 103 |
| 卷板—信息（货品信息） | `ERP → 基础信息 → 产品信息 → 卷板—信息` | `/erp/modules/erp/product_information/product_info.aspx` | 111 |

菜单树关键节点：

```
ERP (57807, PARENT_ID=0)
└─ 基础信息 (57808)
   ├─ 商家信息 (57814)
   │  └─ 供应商 (ID 103, supplier_info.aspx)
   └─ 产品信息 (57809)
      └─ 卷板—信息 (ID 111, product_info.aspx)
```

> 页面 URL 的 `menu_navigator` 参数与之一致：`%3AERP%3A基础信息%3A产品信息%3A卷板—信息`。
> 左侧菜单展开路径：**ERP → 基础信息 → 产品信息 → 卷板—信息**（导出用）；供应商在 **ERP → 基础信息 → 商家信息 → 供应商**。

---

## 执行注意事项

1. **全部为只读 SELECT**，不修改任何数据
2. 建议在业务低峰期执行（涉及 JOIN 会员/供应商表）
3. 导出文件命名建议：
   - `product_mapping.xlsx`（PRODUCT_ID 映射）
   - `supplier_contact.xlsx`（联系方式，可合并 2.1+2.2 的列）
4. 导出的文件通过 AI金 ERP 菜单"秀吗数据导入"上传，或交给开发放导入目录

## 已执行的取数记录（2026-08-16）

| 数据 | 结果 | 导入状态 |
| --- | --- | --- |
| 上架现货计数 | 3011（ERP 后台一致） | — |
| PRODUCT_ID 映射 | 3011 条（产品编码对照表.xlsx） | ✅ 已导入快照表 |
| 供应商联系方式/会员等级 | 29927 行会员（yonghu.csv），20 家供应商命中 | ✅ 已回填 3011 条（2920 有电话） |
| 仓库→城市/省份 | 705 仓库（仓库城市对照表.xlsx），47 仓库命中 | ✅ 已回填（2993 条有城市） |

快照表最终完整度：3011 条全部有 product_id / 会员等级 / 仓库；2920 有电话；2993 有城市。
