# MEMBER_CODE 字段迁移方案

> 版本: v1.1 | 日期: 2026-07-27 | 状态: Phase 2 代码修改已完成，待 Bitable 表结构调整

## 一、字段映射规则

**统一规则：所有表中用户标识字段统一为 `'用户ID'`，填入 MEMBER_CODE。**

| 旧字段 | 新字段 | 说明 |
|--------|--------|------|
| `'登录名'` | `'用户ID'` | 填入 MEMBER_CODE |
| 新增 | `'手机号'` | 辅助字段，保留原手机号用于客服联系 |
| `'用户名'` | 保留 | Token 统计表用，显示用户名 |
| `'反馈人'` | 保留 | 反馈表用 |

---

## 二、Bitable 表变更（用户侧操作）

| # | 表 | 变更操作 | 备注 |
|---|-----|---------|------|
| 1 | VIP用户表 | "登录名"→改名为"用户ID"，填入 MEMBER_CODE | 主字段权限问题需在 UI 操作 |
| 2 | VIP购买记录表 | "登录名"→改名为"用户ID"，填入 MEMBER_CODE；新增"手机号" | |
| 3 | VIP成员关系表 | "登录名"→改名为"用户ID"，填入 MEMBER_CODE；新增"手机号" | 主字段权限问题同上 |
| 4 | 店铺装修表 | 新增"用户ID"，填入 MEMBER_CODE | 该表原用 SUPPLIER_ID 作为主键 |
| 5 | AI问答反馈表 | 新增"用户ID"+"手机号" | |
| 6 | 站点意见反馈表 | 新增"用户ID"+"手机号" | |
| 7 | Token 消耗统计 | 已有"用户ID"，无需改动 | 前端已传 MEMBER_CODE |

---

## 三、文件影响矩阵

| 文件 | Token统计 | 反馈表 | VIP用户 | VIP购买 | VIP成员 | 店铺装修 | 文档 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `server/modules/ai/token-record.service.ts` | ✅ | - | - | - | - | - | - |
| `server/modules/ai/feedback.service.ts` | - | ✅ | - | - | - | - | - |
| `server/modules/vip/vip.service.ts` | - | - | ✅ | ✅ | ✅ | - | - |
| `server/modules/store/store.service.ts` | - | - | - | - | - | ✅ | - |
| `erp/server/erp-vip-admin.service.ts` | - | - | ✅ | ✅ | ✅ | - | - |
| `erp/server/erp-vip-admin.controller.ts` | - | - | ✅ | ✅ | ✅ | - | - |
| `erp/server/erp-order.service.ts` | - | - | - | ✅ | ✅ | - | - |
| `erp/server/erp-revenue.service.ts` | - | - | - | ✅ | - | - | - |
| `erp/server/erp-retention.service.ts` | - | - | - | ✅ | - | - | - |
| `erp/server/erp-operation-log.service.ts` | - | - | - | - | - | - | ✅ |
| `docs/token统计/设计方案.md` | ✅ | - | - | - | - | - | ✅ |
| `docs/erp/07-AI用量统计与计费.md` | ✅ | - | - | - | - | - | ✅ |

---

## 四、代码变更清单

### 4.1 `server/modules/vip/vip.service.ts` (1353行 — **核心文件**)

#### A. 删除"登录名"回退逻辑，完全改为"用户ID"

读操作（5处）— 去掉 `|| toString(f['登录名'])` 回退：

| # | 行号 | 现在代码 | 改为 |
|---|------|----------|------|
| A1 | ~314 | `toString(f['用户ID']) \|\| toString(f['登录名'])` | `toString(f['用户ID'])` |
| A2 | ~398 | `user.fields['用户ID'] \|\| user.fields['登录名']` | `user.fields['用户ID']` |
| A3 | ~828 | `record.fields['用户ID'] \|\| record.fields['登录名']` | `record.fields['用户ID']` |
| A4 | ~538 | `r.fields['用户ID'] \|\| r.fields['登录名']` | `r.fields['用户ID']` |
| A5 | ~545 | 注释 | 确认手机号读写正确 |

搜索条件（7处）— 删掉"登录名"回退分支：

| # | 行号 | 现在代码 | 改为 |
|---|------|----------|------|
| B1 | ~83 | `{ fieldName: '用户ID', ... }` → 回退 `{ fieldName: '登录名', ... }` | 只保留 `{ fieldName: '用户ID', ... }` |
| B2 | ~105 | 同上 | 同上 |
| B3 | ~209 | 同上 | 同上 |
| B4 | ~500 | 同上 | 同上 |
| B5 | ~624 | 同上 | 同上 |
| B6 | ~920 | 同上 | 同上 |
| B7 | ~1005 | 同上 | 同上 |
| B8 | ~1077 | 同上 | 同上 |

写入（4处）— 已有 `'用户ID': loginName`，确认有以下字段：

| # | 行号 | 确认 |
|---|------|------|
| C1 | ~126 | `'用户ID': loginName, '登录名': loginName, '手机号': loginName` → 删除 `'登录名'` |
| C2 | ~679 | 同上 |
| C3 | ~832 | `'用户ID': buyerLoginName, '登录名': buyerLoginName` → 删除 `'登录名'` |
| C4 | ~1047 | `'用户ID': memberLoginName, '登录名': memberLoginName` → 删除 `'登录名'` |


### 4.2 `erp/server/erp-vip-admin.service.ts` (536行)

| # | 行号 | 现在代码 | 改为 |
|---|------|----------|------|
| D1 | ~158 | `this.toString(f['用户ID']) \|\| this.toString(f['登录名'])` | `this.toString(f['用户ID'])` |
| D2 | ~176 | `this.toString(f['用户ID']) \|\| this.toString(f['登录名'])` | `this.toString(f['用户ID'])` |
| D3 | ~184 | 读取成员关系表 (已改为回退) | 同上 |

### 4.3 `erp/server/erp-order.service.ts`

| # | 行号 | 现在代码 | 改为 |
|---|------|----------|------|
| E1 | ~316 | `f['用户ID'] \|\| f['登录名']` | `f['用户ID']` |
| E2 | ~405-411 | 用户存在性检查，双条件 | 只查 `'用户ID'` |
| E3 | ~427-443 | 成员关系查询，双条件 | 只查 `'用户ID'` |

### 4.4 `erp/server/erp-revenue.service.ts`

| # | 行号 | 现在代码 | 改为 |
|---|------|----------|------|
| F1 | ~340 | `f['用户ID'] \|\| f['登录名']` | `f['用户ID']` |

### 4.5 `erp/server/erp-retention.service.ts`

| # | 行号 | 现在代码 | 改为 |
|---|------|----------|------|
| G1 | ~336 | `f['用户ID'] \|\| f['登录名']` | `f['用户ID']` |

### 4.6 `erp/server/erp-vip-admin.controller.ts` — 导出 Excel

| # | 行号 | 现在代码 | 改为 |
|---|------|----------|------|
| H1 | ~71 | 导出表头 `'登录名'` | 改为 `'用户ID'` |
| H2 | ~126 | 导出数据行对应位置 | 改为 `'用户ID'` |

### 4.7 `server/modules/ai/feedback.service.ts` — 反馈表写入

| # | 行号 | 现在代码 | 改为 |
|---|------|----------|------|
| I1 | ~48 | `'反馈人': data.userName \|\| data.userId` | 保持不动（反馈人作为显示名称） |
| I2 | 新增 | 无 | 新增写入 `'用户ID': data.userId` 和 `'手机号': data.userName` |

### 4.8 `server/modules/ai/token-record.service.ts` — Token 统计表

| # | 行号 | 确认 |
|---|------|------|
| J1 | ~146 | `'用户ID': params.userId` — 已用 MEMBER_CODE，无需改 |
| J2 | ~147 | `'用户名': params.userName \|\| params.userId` — 已正确 |

### 4.9 `client/src/` — 前端代码

大部分前端使用的是 `loginName` 作为**用户显示名称**（AppHeader、会员管理 UI），这些不应改为 MEMBER_CODE。只有以下位置需要确认：

| # | 文件 | 操作 |
|---|------|------|
| K1 | `api/ai.ts` | `x-user-id` 已传 MEMBER_CODE ✅ |
| K2 | `api/vip.ts` | `x-login-name` header 保持不动（用于后端查用户） |
| K3 | `AddMemberModal.vue` | 用户输入的是"手机号"还是"用户ID"？需确认语义 |

---

## 五、分任务执行详情

### Task 1: Token 消耗统计 — 适配新字段集 ✅ 已完成

**新表结构变化（Token 消耗统计）：**
- 删除了 `模型列表`、`最后问题` 字段
- `功能分类` 从单选改为文本
- 新增 `记录` 字段（自动编号，代码不必操作）

**文件：** `server/modules/ai/token-record.service.ts`

### Task 2: AI问答反馈记录 — 适配新字段集 ✅ 已完成

**新表结构变化：**
- 新增 `用户ID`（文本）、`手机号`（文本）
- 删除了 `反馈人`、`反馈人姓名` 字段

**文件：** `server/modules/ai/feedback.service.ts`、`server/modules/ai/ai.controller.ts`

### Task 3: VIP用户表 — 完全使用 "用户ID" ✅ 已完成

**文件：** `server/modules/vip/vip.service.ts`、`erp/server/erp-vip-admin.service.ts`

### Task 4: VIP购买记录表 — "用户ID" + "手机号" ✅ 已完成

**文件：** `server/modules/vip/vip.service.ts`、`erp/server/erp-order.service.ts`、`erp/server/erp-revenue.service.ts`、`erp/server/erp-retention.service.ts`

### Task 5: VIP成员关系表 — "用户ID" + "手机号" ✅ 已完成

**文件：** `server/modules/vip/vip.service.ts`、`erp/server/erp-vip-admin.service.ts`、`erp/server/erp-order.service.ts`

### Task 6: 店铺装修表 — 增加 "用户ID" 写入 ✅ 已完成

**文件：** `server/modules/store/store.service.ts`

### Task 7: 操作日志表 — 字段类型确认 ✅ 已确认

原 Bitable 中 `操作描述` 类型被改为 `Attachment`、`操作时间` 类型被改为 `Url`，与代码不兼容。已确认代码中保持原有文本/数字类型写入，Bitable 表字段类型已修正。

### Task 8: 更新相关文档 ✅ 已完成

**文件：** `docs/token统计/设计方案.md`、`docs/erp/07-AI用量统计与计费.md`

### Task 9: 清理迁移控制器 ✅ 已完成

**文件：** `erp/server/erp-field-migration.controller.ts`

---

## 六、操作顺序

```
Phase 1 — Bitable 表结构调整（你来操作）
  ├── VIP用户表: "登录名"→"用户ID"，填 MEMBER_CODE
  ├── VIP购买记录表: "登录名"→"用户ID"+"手机号"
  ├── VIP成员关系表: "登录名"→"用户ID"+"手机号"
  ├── 店铺装修表: 新增"用户ID"
  ├── AI问答反馈表: 新增"用户ID"+"手机号"
  ├── 站点意见反馈表: 新增"用户ID"+"手机号"
  ├── Token 消耗统计表: 已有"用户ID" ✅
  └── 存量数据填充 MEMBER_CODE

Phase 2 — 代码修改（已完成） ✅
  ├── ✅ 删除所有"登录名"回退逻辑（约20处）
  ├── ✅ 搜索条件只查"用户ID"
  ├── ✅ 导出表头改为"用户ID"
  ├── ✅ 反馈表增加"用户ID"+"手机号"写入
  └── ✅ 编译验证 + Git 提交

Phase 3 — 验证
  ├── ERP 后台各项功能正常运行
  ├── 购买流程、成员管理、用户搜索正常
  ├── Token 统计数据正确显示
  └── AI 反馈数据正确写入
```

---

## 七、剩余问题

1. **存量数据**：已有记录的"用户ID"字段为空。需要 MEMBER_CODE ↔ 手机号的映射关系才能批量填充。
2. **店铺装修表**：目前用 `SUPPLIER_ID` 作为记录键（51bxg 的供应商 ID）。新增"用户ID"后，是同时保留 `SUPPLIER_ID`，还是用"用户ID"替代它？
3. **`AddMemberModal.vue`**：添加成员时，用户当前输入的是手机号还是 MEMBER_CODE？如果表里"用户ID"是 MEMBER_CODE，那通过 UI 添加成员时需要用户输入什么？