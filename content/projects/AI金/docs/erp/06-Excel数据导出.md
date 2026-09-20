# 06-Excel数据导出

> 版本: v1.0 | 日期: 2026-07-27 | 状态: 已实现

## 一、目标

为 ERP 后台提供 Excel 数据导出能力，支持用户数据、订单数据的灵活导出。

## 二、导出功能清单

| 功能 | 接口 | 说明 |
|------|------|------|
| 全量用户导出 | `GET /api/erp/vip-admin/export-all` | 导出所有 VIP 用户数据为单 Sheet Excel |
| 单用户导出 | `GET /api/erp/vip-admin/export/:userId` | 导出单个用户数据（含购买记录+成员关系）为多 Sheet Excel |
| 订单导出 | `GET /api/erp/orders/export` | 导出筛选后的订单列表为 Excel |

## 三、技术实现

### 3.1 技术栈

- 使用 `xlsx` 库（SheetJS）生成 Excel 文件
- 后端直接生成 Buffer 并返回文件流
- 文件名使用 UTF-8 编码（`encodeURIComponent`）

### 3.2 导出格式

**全量用户导出**（单 Sheet）：

| 列 | 字段 |
|----|------|
| 用户ID | loginName |
| 平台 | platform |
| 企业名称 | companyName |
| 手机号 | phone |
| 邮箱 | email |
| 当前套餐 | packageName |
| 套餐等级 | packageLevel |
| 购买记录数 | purchaseCount |
| 成员数 | memberCount |
| 最新购买日期 | latestPurchaseDate |
| 最新到期日期 | latestExpireDate |
| 状态 | 有效/已过期 |

**单用户导出**（多 Sheet）：
- Sheet 1「用户信息」：同上表头
- Sheet 2「购买记录」：套餐名称、购买日期、到期日期、金额、状态
- Sheet 3「成员关系」：成员登录名、角色、状态、关联购买日期

### 3.3 实现文件

- `erp/server/erp-vip-admin.controller.ts` — 用户数据导出（exportAll、exportSingle 方法）
- `erp/server/erp-order.controller.ts` — 订单数据导出

## 四、关联文件

- `erp/server/erp-vip-admin.controller.ts` — 用户导出接口
- `erp/server/erp-order.controller.ts` — 订单导出接口
- `erp/server/erp-vip-admin.service.ts` — 导出数据查询逻辑