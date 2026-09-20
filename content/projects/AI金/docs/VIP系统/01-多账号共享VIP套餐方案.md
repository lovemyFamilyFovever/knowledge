# 多账号共享VIP套餐方案

> **文档状态**：v4 — 根据最终套餐矩阵更新能力清单和各档套餐的精确能力配置

## 一、需求背景

### 1.1 业务场景

当前系统通过 51bxg 的 `SERVICES` 字段（`includes('003')`）判断用户是否为 VIP。虽然后台管理界面定义了 L0-L7 共 8 个权限等级，但实际代码中 `auth.ts:113` 硬编码了 `userLevel = services.includes('003') ? 1 : 0`，只有 L0（普通用户）和 L1（VIP）两个值真正生效。L2-L7 从未被任何用户获取过。

新需求：

- 推出 **7 档年费制套餐**，从试用到尊享定制版
- 套餐购买者（主账号）可将套餐共享给多个子账号
- 共享账号数量**动态可配置**，从飞书多维表格读取，后台管理员可调整
- 子账号通过自己的 51bxg 账号登录，享有套餐对应的权限
- 同时保留非年费入门方式（免费/试用/积分兑换）作为补充

### 1.2 套餐定价体系（年费制）

| 套餐档位 | 年费 | 定位说明 |
|---------|------|---------|
| 免费 | 0 元 | 永久可用，含通用知识库、行业数据库、AI配单（高效配单+企业录入） |
| 试用 | 0 元 | 7 天限时体验，全域功能开放，每天 10 次调用，Token 额度 50 万 |
| 入门版 | 3,980 元/年 | 测 1 系，查 1 系数据 |
| 进阶版 | 9,800 元/年 | 测全钢种，查全系 |
| 专业版 | 19,800 元/年 | AI 金 + GEO（AI配单优质推荐） |
| 企业版（推荐） | 49,800 元/年 | AI 金 + 全量接口 |
| 旗舰版 | 119,900 元/年 | AI 金 + 自有数据 + 训练（1 系） |
| 尊享定制版 | 498,000 元/年 | AI 金 + 自有数据 + 训练（全系）+ 智能采销 |

### 1.3 能力清单（12 项子能力，分 8 个分类）

> **能力项说明**：老板最终给出的套餐矩阵包含 12 个子项，分属 8 个分类。
> - "通用知识库"和"行业数据库"在所有套餐中**总是同时出现**（对应 AI 问答的快速模式和专家模式）
> - "AI预测"和"AI查询"在所有套餐中**总是同时出现**（对应现有 AI 测价功能，后期不拆分）
> - 实际权限控制按 12 个子项独立设计，便于未来灵活调整

| 编号 | 分类 | 子能力名称 | 对应现有功能 | 权限类型 |
|------|------|-----------|------------|---------|
| 1 | AI 问答 | 通用知识库 | `/ai/qa` 快速模式 | 页面访问 |
| 2 | AI 问答 | 行业数据库 | `/ai/qa` 专家模式 | 页面访问 |
| 3 | AI 预测 | AI 预测 | `/ai/price` | 页面访问 |
| 4 | AI 预测 | AI 查询 | `/ai/price` | 页面访问 |
| 5 | AI 配单 | AI 高效配单 | `/ai/stock` | 页面访问 |
| 6 | AI 配单 | 秀吗保交付 | `/ai/stock` 内功能特性 | **功能特性** |
| 7 | AI 配单 | 企业录入 | 企业录入页面 | **功能特性** |
| 8 | 配企/GEO | AI 配单优质推荐 | `/ai/stock` 内排序逻辑 | **业务曝光特权** |
| 9 | API | API 全量接口 | `/data/api` | 页面访问 |
| 10 | 专属 | 专属服务 | — | 页面访问 |
| 11 | 定制 | 场景定制 | — | 页面访问 |
| 12 | 私有化 | 私有化部署 | — | 页面访问 |

### 1.4 套餐能力矩阵（最终版）

这是老板确认的各档套餐与能力的精确对应关系：

| 能力 → | 1 通用知识库 | 2 行业数据库 | 3 AI预测 | 4 AI查询 | 5 AI高效配单 | 6 秀吗保交付 | 7 企业录入 | 8 AI配单优质推荐 | 9 API全量接口 | 10 专属服务 | 11 场景定制 | 12 私有化部署 |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **免费** | ✓ | ✓ | | | ✓ | | ✓ | | | | | |
| **试用** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | | | | |
| **入门版 3,980** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | | | | |
| **进阶版 9,800** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | | | | |
| **专业版 19,800** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | | | |
| **企业版 49,800** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | | |
| **旗舰版 119,900** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | |
| **尊享定制版 498,000** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |

**关键观察**：

1. **"私有化部署"在所有标准套餐中均未勾选** — 可能是单独洽谈的业务，不包含在标准年费套餐内
2. **"AI配单优质推荐"从专业版（19,800元）开始** — 这是曝光特权，进阶版及以下没有
3. **免费用户有"企业录入"但没有"秀吗保交付"** — 免费用户可以录入产品，但配单结果中不显示保交付标记
4. **试用与入门版/进阶版的能力范围相同**（前 7 项），差异在于试用是 7 天限时且限次
5. **入门版与进阶版的能力清单完全相同** — 差异在"测1系/查1系"vs"测全钢种/查全系"，是数据范围限制不是能力项差异

### 1.5 非年费入门方式

| 方式 | 说明 | 能力范围 |
|------|------|---------|
| 免费 | 永久可用 | 通用知识库 + 行业数据库 + AI高效配单 + 企业录入（4项） |
| 试用 | 7 天全域功能开放，每天 10 次调用，Token 额度 50 万 | 前 7 项能力（限时） |
| 51 号积分兑换 | 9,800 积分 = 1 天 1 次报价 + 3 天 1 次图文；19,800 积分 = 3 天 1 次买单 + 9 天 1 次成交 | 按次/按时 |

### 1.6 核心约束

- **不能修改 51bxg 数据库** — 51bxg 是外部平台，无权操作其数据库
- **登录验证仍走 51bxg API** — 账号密码验证依赖 51bxg 的 `PostLogin` 接口
- **数据存储使用飞书多维表格** — 与项目现有数据层保持一致
- **共享账号数动态可配置** — 从飞书多维表格读取，后台管理员可调整

---

## 二、权限模型设计（双层）

### 2.1 为什么需要双层权限

老板给的套餐表里，"推荐（竞价排名）"、"企业录入"、"秀吗保交付"、"优质排名（GEO）"这些功能点**不是页面访问权限**，而是**业务曝光特权**：

| 类型 | 表现 | 控制方式 |
|------|------|---------|
| 页面访问型 | 用户能进/不能进某个路由 | 按套餐等级控制路由访问 |
| 功能特性型 | 用户能进页面，但页面内行为不同（如可录入数据、有认证标记） | 按"功能标记"控制页面内功能 |
| 业务曝光特权型 | 用户的信息在别人的页面里被优先展示 | 在 AI 问答/配单的结果排序逻辑中加权 |

**关键认知**："推荐（竞价排名）"是让买了该功能点的用户，**他的商品**在**别人**的 AI 配单结果里优先展示。这是曝光特权，不是页面访问权限。

### 2.2 权限模型定义

```typescript
interface UserPermission {
  // 第一层：页面访问权限（按套餐等级控制路由）
  pageAccess: {
    '/ai/qa': boolean
    '/ai/price': boolean
    '/ai/stock': boolean
    '/ai/sales-strategy': boolean
    '/ai/sales-smart': boolean
    '/data/view': boolean
    // ... 其他页面
  }
  
  // 第二层：功能特性标记（按套餐包含的功能点）
  features: {
    'enterprise_input': boolean             // #7 企业录入 — 可录入企业产品到配单池
    'guaranteed_delivery': boolean          // #6 秀吗保交付 — 配单结果认证标记
    'ai_stock_priority_recommend': boolean  // #8 AI配单优质推荐 — 配单优先推荐我的商品
    'api_access': boolean                   // #9 API 全量接口
    // ... 其他功能特性
  }
  
  // 套餐信息
  packageId: string
  packageName: string
  packageLevel: number  // 0=免费, 1=试用, 2=入门, 3=进阶, 4=专业, 5=企业, 6=旗舰, 7=尊享
  maxAccounts: number   // 共享账号数（动态从飞书读取）
  role: 'owner' | 'member' | null
  expiryDate: string | null
}
```

### 2.3 各功能点的控制点

| 编号 | 功能点 | 控制点 | 实现方式 |
|------|--------|--------|---------|
| 1-2 | 通用知识库 / 行业数据库 | 前端路由守卫 + 后端 API 鉴权 | `pageAccess['/ai/qa']` |
| 3-4 | AI 预测 / AI 查询 | 前端路由守卫 + 后端 API 鉴权 | `pageAccess['/ai/price']` |
| 5 | AI 高效配单 | 前端路由守卫 + 后端 API 鉴权 | `pageAccess['/ai/stock']` |
| 6 | 秀吗保交付 | `/ai/stock` 配单结果中显示"保交付"标记 | `features['guaranteed_delivery']` |
| 7 | 企业录入 | `/ai/stock` 页面内"录入"入口可见性 + 后端 API 鉴权 | `features['enterprise_input']` |
| 8 | AI 配单优质推荐 | 后端 AI 配单结果排序时加权（不是用户自己的权限，是**别人的**结果排序） | 见 2.4 节 |
| 9 | API 全量接口 | `/data/api` 页面访问 + API Key 发放 | `pageAccess['/data/api']` + `features['api_access']` |
| 10-12 | 专属服务 / 场景定制 / 私有化部署 | 待确认对应路由 | 待定 |

### 2.4 业务曝光特权的特殊性

"AI 配单优质推荐"（#8）的权限控制逻辑与普通功能不同：

```
用户 A（专业版，含AI配单优质推荐）登录后查询 AI 配单
  → 系统检索商品库
  → 用户 A 的商品（如果上架）在结果中优先展示
  → 用户 A 看到的是：自己买的功能，自己被优先推荐

用户 B（入门版，不含推荐功能）查询 AI 配单
  → 系统检索商品库
  → 用户 A 的商品（买了推荐）排在用户 B 自己的商品前面
  → 用户 B 看到的是：别人买的曝光特权，影响了自己看到的结果
```

**实现要点**：

- 曝光特权**不是当前登录用户的权限判断**，而是**商品库中每个商品所属企业的权限判断**
- AI 配单结果排序时，需要查询每个候选商品所属企业是否拥有 `ai_stock_priority_recommend` 特权
- 这意味着 AI 配单服务需要能查询"某企业是否有某功能点"

### 2.5 待确认事项

> 以下事项需要与业务方确认后再细化，详见第十一章：

1. **"秀吗保交付"的具体含义** — 是配单结果中的认证标记？还是下单后的服务流程？还是供应商入驻秀吗的资格？
2. **"专属服务"、"场景定制"、"私有化部署"的对应路由** — 这三项能力目前没有对应的现有页面
3. **企业录入的数据存储** — 企业录入的产品/报价存在哪里？飞书多维表格？还是 51bxg 的商品库？
4. **入门版与进阶版的数据范围差异** — 能力清单相同，但"测1系/查1系"vs"测全钢种/查全系"如何在代码中实现

---

## 三、飞书多维表格设计

### 3.1 存储架构

项目数据层统一使用飞书多维表格（bitable），通过已有的 `FeishuBitableService`（`@Global()` 模块）进行 CRUD 操作。VIP 相关数据存储在同一个飞书多维表格应用中，包含 5 张数据表。

**环境变量配置**（`.env`）：

```bash
# VIP 飞书多维表格
BITABLE_MAIN_APP_TOKEN=bascnxxxxxxxxxxxx     # 多维表格应用 ID
BITABLE_VIP_USERS_TABLE_ID=tblxxxxxxxx       # 用户表
BITABLE_VIP_PACKAGES_TABLE_ID=tblxxxxxxxx    # 套餐表
BITABLE_VIP_PURCHASES_TABLE_ID=tblxxxxxxxx   # 购买记录表
BITABLE_VIP_MAPPING_TABLE_ID=tblxxxxxxxx     # 成员关系表
BITABLE_VIP_FEATURES_TABLE_ID=tblxxxxxxxx    # 功能特性表（新增）
```

### 3.2 表结构定义

#### 用户表（`BITABLE_VIP_USERS_TABLE_ID`）

| 字段名 | 字段类型 | 必填 | 说明 |
|--------|---------|------|------|
| 登录名 | 文本 | 是 | 51bxg 登录名，业务唯一标识 |
| 平台 | 单选 | 是 | 固定值 `51bxg` |
| 显示名称 | 文本 | 否 | 用户显示名称 |
| 企业名称 | 文本 | 否 | 用户所属企业（用于曝光特权匹配） |
| 51bxg企业ID | 文本 | 否 | 关联 51bxg 企业 ID（如有） |
| 创建时间 | 日期 | 是 | 自动填充 |
| 更新时间 | 日期 | 否 | 自动填充 |

> 注：多维表格的 `record_id` 作为用户唯一 ID（即 `userId`），由飞书自动生成。

#### 套餐表（`BITABLE_VIP_PACKAGES_TABLE_ID`）— 种子数据

| 字段名 | 字段类型 | 必填 | 说明 |
|--------|---------|------|------|
| 套餐名称 | 文本 | 是 | 试用 / 入门版 / 进阶版 / 专业版 / 企业版 / 旗舰版 / 尊享定制版 |
| 套餐等级 | 数字 | 是 | 1-7（对应 7 档） |
| 年费（分） | 数字 | 是 | 0 / 398000 / 980000 / 1980000 / 4980000 / 11999000 / 49800000 |
| 最大账号数 | 数字 | 是 | **动态可配置**，后台管理员可修改 |
| 定位说明 | 文本 | 否 | 套餐定位描述 |
| 是否启用 | 复选框 | 是 | 勾选=启用 |
| 包含能力 | 文本 | 否 | 逐行列出能力编号，如"1\n2\n3\n4\n5\n6"（代码用 split 解析） |

> **「最大账号数」设计**：不硬编码，从飞书表格读取。后台管理员修改该字段后，下次查询立即生效（5 分钟缓存内可能延迟）。暂不处理"已满后减少数量"的边界情况——如果管理员把某档从 9 人改为 3 人，已有 9 人的套餐不会主动剔除成员，代码后续优化。

**种子数据**（在飞书中手动录入 8 行，包含免费档）：

| 套餐名称 | 套餐等级 | 年费（分） | 最大账号数 | 定位说明 | 包含能力 |
|---------|---------|-----------|-----------|---------|---------|
| 免费 | 0 | 0 | 1 | 永久可用 | 1<br>2<br>5<br>7 |
| 试用 | 1 | 0 | 1 | 7 天限时体验 | 1<br>2<br>3<br>4<br>5<br>6<br>7 |
| 入门版 | 2 | 398000 | 3 | 测 1 系，查 1 系数据 | 1<br>2<br>3<br>4<br>5<br>6<br>7 |
| 进阶版 | 3 | 980000 | 9 | 测全钢种，查全系 | 1<br>2<br>3<br>4<br>5<br>6<br>7 |
| 专业版 | 4 | 1980000 | 9 | AI 金 + GEO | 1<br>2<br>3<br>4<br>5<br>6<br>7<br>8 |
| 企业版 | 5 | 4980000 | 9 | AI 金 + 全量接口 | 1<br>2<br>3<br>4<br>5<br>6<br>7<br>8<br>9 |
| 旗舰版 | 6 | 11999000 | 9 | AI 金 + 自有数据 + 训练（1 系） | 1<br>2<br>3<br>4<br>5<br>6<br>7<br>8<br>9<br>10 |
| 尊享定制版 | 7 | 49800000 | 9 | AI 金 + 自有数据 + 训练（全系）+ 智能采销 | 1<br>2<br>3<br>4<br>5<br>6<br>7<br>8<br>9<br>10<br>11 |

> 注：价格以「分」为单位存储，避免浮点数精度问题。398000 分 = 3980.00 元。
>
> **包含能力说明**：数字对应 1.3 节能力清单中的编号，用换行符分隔，代码中用 `split('\n')` 解析。各档套餐的精确能力配置见 1.4 节套餐能力矩阵。
>
> **"私有化部署"（编号12）**：在所有标准套餐中均未勾选，可能是单独洽谈的业务。如需加入某档套餐，只需在飞书表格的「包含能力」字段中追加"12"即可。

#### 功能特性表（`BITABLE_VIP_FEATURES_TABLE_ID`）— 新增

用于定义 12 项子能力的元数据，便于后台管理和前端展示。

| 字段名 | 字段类型 | 必填 | 说明 |
|--------|---------|------|------|
| 能力编号 | 数字 | 是 | 1-12 |
| 能力名称 | 文本 | 是 | 如"通用知识库"、"AI配单优质推荐" |
| 分类 | 单选 | 是 | AI问答 / AI预测 / AI配单 / 配企GEO / API / 专属 / 定制 / 私有化 |
| 权限类型 | 单选 | 是 | page_access / feature_flag / exposure_privilege |
| 对应路由 | 文本 | 否 | 如 `/ai/qa`（页面访问型必填） |
| 特性标记Key | 文本 | 否 | 如 `ai_stock_priority_recommend`（功能特性型必填） |
| 描述 | 文本 | 否 | 能力说明 |

**种子数据**（在飞书中手动录入 12 行）：

| 能力编号 | 能力名称 | 分类 | 权限类型 | 对应路由 | 特性标记Key |
|---------|---------|------|---------|---------|------------|
| 1 | 通用知识库 | AI问答 | page_access | `/ai/qa` | — |
| 2 | 行业数据库 | AI问答 | page_access | `/ai/qa` | — |
| 3 | AI预测 | AI预测 | page_access | `/ai/price` | — |
| 4 | AI查询 | AI预测 | page_access | `/ai/price` | — |
| 5 | AI高效配单 | AI配单 | page_access | `/ai/stock` | — |
| 6 | 秀吗保交付 | AI配单 | feature_flag | — | `guaranteed_delivery` |
| 7 | 企业录入 | AI配单 | feature_flag | — | `enterprise_input` |
| 8 | AI配单优质推荐 | 配企GEO | exposure_privilege | — | `ai_stock_priority_recommend` |
| 9 | API全量接口 | API | page_access | `/data/api` | `api_access` |
| 10 | 专属服务 | 专属 | page_access | （待定） | — |
| 11 | 场景定制 | 定制 | page_access | （待定） | — |
| 12 | 私有化部署 | 私有化 | page_access | （待定） | — |

#### 购买记录表（`BITABLE_VIP_PURCHASES_TABLE_ID`）

| 字段名 | 字段类型 | 必填 | 说明 |
|--------|---------|------|------|
| 套餐记录ID | 文本 | 是 | 套餐表中的 `record_id` |
| 购买者记录ID | 文本 | 是 | 用户表中的 `record_id`（主账号） |
| 购买者手机号 | 文本 | 否 | 冗余字段，便于在飞书 UI 中辨别购买者 |
| 购买价格（分） | 数字 | 是 | 购买时的套餐价格，固化历史价格 |
| 购买日期 | 日期 | 是 | 自动填充 |
| 到期日期 | 日期 | 否 | 空=永久有效；试用套餐=7 天后 |
| 状态 | 单选 | 是 | active / expired / cancelled |
| 订单编号 | 文本 | 否 | 订单号，如 `VIP202607220001` |
| 支付方式 | 单选 | 否 | alipay / wechat / bank |
| 支付时间 | 日期 | 否 | 完成支付的时间 |
| 备注 | 文本 | 否 | 任意备注信息 |

> **为什么需要「购买价格（分）」**：套餐表中的价格是"当前售价"，可能随时间调整。购买时写入当时的价格，确保历史数据不变。
>
> **字段拆分说明**：原「订单信息」字段（多行文本存储 JSON 字符串）已于阶段七拆分为「订单编号」「支付方式」「支付时间」「备注」4 个独立字段，避免 JSON 解析转换的复杂性和出错风险。

#### 成员关系表（`BITABLE_VIP_MAPPING_TABLE_ID`）

| 字段名 | 字段类型 | 必填 | 说明 |
|--------|---------|------|------|
| 用户记录ID | 文本 | 是 | 用户表中的 `record_id` |
| 购买记录ID | 文本 | 是 | 购买记录表中的 `record_id` |
| 角色 | 单选 | 是 | owner / member |
| 状态 | 单选 | 是 | active / inactive |
| 加入日期 | 日期 | 是 | 自动填充 |

### 3.3 与 SQL 数据库的关键差异

| 差异点 | SQLite | 飞书多维表格 | 应对方式 |
|--------|--------|-------------|---------|
| JOIN 查询 | 一条 SQL 完成 | 不支持 JOIN | 分步查询，先查 A 表再查 B 表 |
| 唯一约束 | UNIQUE 索引 | 无内置约束 | 写入前在代码中查询去重 |
| 自增 ID | AUTOINCREMENT | record_id | 使用飞书自动生成的 record_id |
| 分页 | LIMIT/OFFSET | page_token | 逐页拉取（参考 `fetchAllEntries` 模式） |
| 事务 | 支持 | 不支持 | 关键操作串行执行，失败时手动回滚（见下方说明） |

> **无事务保护的具体应对**：以"添加子账号"为例，步骤为 `ensureUser`（先查后建）→ 校验 → `batchCreate` 成员关系。如果成员关系写入失败：
> - 子账号**已存在**于用户表中 → 无需回滚（该用户可能在其他场景中已创建）
> - 子账号**刚创建** → 用户表中留下一条无套餐关联的"孤儿记录"，但这不影响功能（下次登录时 `queryUserPermission` 返回 level=0，用户体验无差异）
>
> 因此 `ensureUser` 被拆为 `findUserByLoginName` + `createUser` 两个独立方法，调用方可以决定失败时是否需要回滚。对于登录场景，回滚不是必需的——多余的用户记录不产生副作用。

---

## 四、核心业务流程

### 4.1 登录流程（含权限解析）

```
用户输入 51bxg 账号密码
       │
       ▼
┌──────────────────────────────┐
│ 1. 调用 51bxg PostLogin API  │  ← 现有流程不变
│    验证账号密码               │
└──────────────┬───────────────┘
               │ 验证失败 → 返回登录失败
               │ 验证成功
               ▼
┌──────────────────────────────┐
│ 2. ensureUser 飞书用户表     │
│    先查后建，返回 userId     │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 3. queryUserPermission       │
│    查询用户完整权限：         │
│    - 成员关系 → 购买记录     │
│    - 购买记录 → 套餐         │
│    - 套餐 → 包含能力         │
│    - 能力 → pageAccess +    │
│           features          │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 4. 返回:                     │
│    - 51bxg 用户信息          │
│    - permission: {           │
│        pageAccess,           │
│        features,             │
│        packageId,            │
│        packageName,          │
│        packageLevel,         │
│        maxAccounts,          │
│        role,                 │
│        expiryDate            │
│      }                       │
└──────────────────────────────┘
```

### 4.2 权限解析详细流程

```
queryUserPermission(loginName)
       │
       ▼
┌──────────────────────────────┐
│ 1. 查用户表 → userId         │
└──────────────┬───────────────┘
               │ 不存在 → 返回默认权限（免费用户）
               ▼
┌──────────────────────────────┐
│ 2. 查成员关系表              │
│    filter: userId + active  │
└──────────────┬───────────────┘
               │ 无 → 返回免费用户权限
               ▼
┌──────────────────────────────┐
│ 3. 查购买记录表              │
│    校验状态 + 到期日期       │
└──────────────┬───────────────┘
               │ 无效 → 返回免费用户权限
               ▼
┌──────────────────────────────┐
│ 4. 查套餐表                  │
│    获取套餐等级、最大账号数  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 5. 解析「包含能力」字段      │
│    split('\n') → 能力编号[] │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 6. 查功能特性表              │
│    获取每个能力的权限类型    │
│    和对应路由/特性Key        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 7. 构建权限对象：            │
│    - pageAccess: 按路由填充  │
│    - features: 按特性Key填充 │
│    - 曝光特权: 留给配单/问答 │
│      服务查询时使用          │
└──────────────────────────────┘
```

### 4.3 子账号添加流程

```
主账号在套餐管理页输入子账号的 51bxg 登录名
       │
       ▼
┌──────────────────────────────┐
│ 1. 校验主账号是否拥有有效套餐│
│    且 role='owner'           │
└──────────────┬───────────────┘
               │ 无权限 → 拒绝
               ▼
┌──────────────────────────────┐
│ 2. 统计当前 active 成员数    │
│    校验 < 套餐.最大账号数    │
│    （从飞书动态读取）         │
└──────────────┬───────────────┘
               │ 已满 → 提示"账号数已达上限"
               ▼
┌──────────────────────────────┐
│ 3. ensureUser 子账号         │
│    （先查后建）              │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 4. 校验子账号是否已有有效套餐│
│    （防重复加入）             │
└──────────────┬───────────────┘
               │ 已有 → 提示"该用户已在其他套餐中"
               ▼
┌──────────────────────────────┐
│ 5. batchCreate 成员关系表     │
│    清除子账号缓存            │
└──────────────────────────────┘
```

### 4.4 子账号移除流程

```
主账号在套餐管理页移除某个子账号
       │
       ▼
┌──────────────────────────────┐
│ 1. 校验操作者 role='owner'   │
└──────────────┬───────────────┘
               │ 否 → 拒绝
               ▼
┌──────────────────────────────┐
│ 2. batchUpdate 成员关系表     │
│    状态='inactive'           │
│    清除被移除用户缓存         │
└──────────────────────────────┘
```

> 子账号被移除后再次登录，权限降为免费用户。

### 4.5 曝光特权查询流程（AI 配单场景）

```
任意用户查询 AI 配单
       │
       ▼
┌──────────────────────────────┐
│ 1. 正常检索商品库             │
│    得到候选商品列表           │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 2. 对每个候选商品：           │
│    查商品所属企业的用户记录   │
│    查该用户是否有有效套餐     │
│    查该套餐是否包含能力 #8    │
│    （AI配单优质推荐）         │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 3. 按特权加权排序：           │
│    有推荐特权的企业商品优先   │
└──────────────────────────────┘
```

> **性能注意**：步骤 2 需要批量查询多个企业的权限。建议引入"企业权限缓存"——以企业 ID 为键，缓存其曝光特权状态，TTL 5 分钟。

---

## 五、后端 API 设计

### 5.1 新建模块

```
server/modules/vip/
├── vip.module.ts
├── vip.controller.ts
├── vip.service.ts
├── permission.service.ts       # 权限解析服务（新增）
└── dto/
    └── vip.dto.ts
```

### 5.2 接口清单

| 方法 | 路由 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/vip/packages` | 获取可用套餐列表 | 登录用户 |
| GET | `/api/vip/my-package` | 获取当前用户的套餐信息 | 登录用户 |
| GET | `/api/vip/my-permission` | 获取当前用户的完整权限 | 登录用户 |
| POST | `/api/vip/purchase` | 购买套餐（模拟） | 登录用户 |
| POST | `/api/vip/package/members` | 添加子账号 | 套餐 owner |
| DELETE | `/api/vip/package/members/:userId` | 移除子账号 | 套餐 owner |
| GET | `/api/vip/package/members` | 查看套餐成员列表 | 套餐成员 |
| GET | `/api/vip/features` | 获取能力清单（12项） | 登录用户 |
| POST | `/api/vip/internal/check-feature` | 内部接口：检查某企业是否有某曝光特权 | 内部调用 |

### 5.3 接口详情

#### GET /api/vip/my-permission

返回当前登录用户的完整权限对象。

```json
{
  "success": true,
  "data": {
    "pageAccess": {
      "/ai/qa": true,
      "/ai/price": true,
      "/ai/stock": true,
      "/ai/sales-strategy": false,
      "/ai/sales-smart": false
    },
    "features": {
      "ai_stock_priority_recommend": true,
      "enterprise_input": true,
      "guaranteed_delivery": true,
      "ai_qa_priority_recommend": false,
      "api_access": false
    },
    "package": {
      "id": "rec_xxx",
      "name": "进阶版",
      "level": 3,
      "maxAccounts": 9,
      "currentMembers": 5,
      "role": "owner",
      "purchaseDate": "2026-07-01",
      "expiryDate": "2027-07-01"
    }
  }
}
```

#### GET /api/vip/packages

返回可购买的套餐列表。

```json
{
  "success": true,
  "data": [
    {
      "id": "rec_xxx",
      "name": "入门版",
      "level": 2,
      "price": 398000,
      "maxAccounts": 3,
      "description": "测 1 系，查 1 系数据",
      "capabilities": [
        { "id": 1, "name": "通用知识库", "category": "AI问答" },
        { "id": 2, "name": "行业数据库", "category": "AI问答" },
        { "id": 3, "name": "AI预测", "category": "AI预测" },
        { "id": 4, "name": "AI查询", "category": "AI预测" },
        { "id": 5, "name": "AI高效配单", "category": "AI配单" },
        { "id": 6, "name": "秀吗保交付", "category": "AI配单" },
        { "id": 7, "name": "企业录入", "category": "AI配单" }
      ]
    }
  ]
}
```

#### GET /api/vip/my-package

返回当前登录用户的套餐信息（含成员列表）。

```json
{
  "success": true,
  "data": {
    "hasPackage": true,
    "package": {
      "id": "rec_xxx",
      "name": "进阶版",
      "level": 3,
      "maxAccounts": 9,
      "currentMembers": 5,
      "role": "owner",
      "purchaseDate": "2026-07-01",
      "expiryDate": "2027-07-01"
    },
    "members": [
      { "id": "rec_xxx", "loginName": "zhangsan", "role": "owner", "joinedAt": "2026-07-01" },
      { "id": "rec_yyy", "loginName": "lisi", "role": "member", "joinedAt": "2026-07-05" }
    ]
  }
}
```

#### POST /api/vip/internal/check-feature

内部接口，供 AI 配单/AI 问答服务调用，检查某企业是否拥有曝光特权。

```json
// Request
{
  "enterpriseName": "某某钢厂",
  "featureKey": "ai_stock_priority_recommend"
}

// Response
{
  "success": true,
  "data": { "hasFeature": true }
}
```

### 5.4 VipService 核心逻辑

```typescript
import { Injectable, Logger } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import { FeishuBitableService } from '../../common/services/feishu-bitable.service'

interface UserPermission {
  pageAccess: Record<string, boolean>
  features: Record<string, boolean>
  package: PackageInfo | null
}

interface PermissionCache {
  permission: UserPermission
  expiresAt: number
}

@Injectable()
export class VipService {
  private readonly logger = new Logger(VipService.name)
  /** 用户权限缓存：key=loginName, TTL=5分钟 */
  private permissionCache = new Map<string, PermissionCache>()
  /** 企业曝光特权缓存：key=enterpriseName, TTL=5分钟 */
  private enterpriseFeatureCache = new Map<string, Map<string, boolean>>()
  private readonly CACHE_TTL_MS = 5 * 60 * 1000

  constructor(
    private configService: ConfigService,
    private bitableService: FeishuBitableService,
  ) {}

  private get appToken(): string {
    return this.configService.getOrThrow<string>('BITABLE_MAIN_APP_TOKEN')
  }
  private get usersTableId(): string {
    return this.configService.getOrThrow<string>('BITABLE_VIP_USERS_TABLE_ID')
  }
  private get packagesTableId(): string {
    return this.configService.getOrThrow<string>('BITABLE_VIP_PACKAGES_TABLE_ID')
  }
  private get purchasesTableId(): string {
    return this.configService.getOrThrow<string>('BITABLE_VIP_PURCHASES_TABLE_ID')
  }
  private get mappingTableId(): string {
    return this.configService.getOrThrow<string>('BITABLE_VIP_MAPPING_TABLE_ID')
  }
  private get featuresTableId(): string {
    return this.configService.getOrThrow<string>('BITABLE_VIP_FEATURES_TABLE_ID')
  }

  /** 按登录名查找用户（仅查询，不创建） */
  async findUserByLoginName(loginName: string): Promise<string | null> {
    const res = await this.bitableService.searchRecords(this.appToken, this.usersTableId, {
      filter: {
        conjunction: 'and',
        conditions: [{ fieldName: '登录名', operator: 'is', value: [loginName] }],
      },
      pageSize: 1,
    })
    return res.records.length > 0 ? res.records[0].id : null
  }

  /** 创建用户，返回 record_id */
  async createUser(loginName: string): Promise<string> {
    const created = await this.bitableService.batchCreate(this.appToken, this.usersTableId, [{
      fields: {
        '登录名': loginName,
        '平台': '51bxg',
        '创建时间': Date.now(),
      },
    }])
    return created.records[0].id
  }

  /** 确保用户存在：先查后建，避免创建孤儿记录 */
  async ensureUser(loginName: string): Promise<string> {
    const existing = await this.findUserByLoginName(loginName)
    if (existing) return existing
    return this.createUser(loginName)
  }

  /** 获取用户完整权限（带缓存） */
  async getUserPermission(loginName: string): Promise<UserPermission> {
    const cached = this.permissionCache.get(loginName)
    if (cached && cached.expiresAt > Date.now()) {
      return cached.permission
    }

    const permission = await this.queryUserPermission(loginName)
    this.permissionCache.set(loginName, {
      permission,
      expiresAt: Date.now() + this.CACHE_TTL_MS,
    })
    return permission
  }

  /** 清除用户权限缓存 */
  clearPermissionCache(loginName: string) {
    this.permissionCache.delete(loginName)
  }

  /** 核心查询逻辑 */
  private async queryUserPermission(loginName: string): Promise<UserPermission> {
    const defaultPermission: UserPermission = {
      pageAccess: this.getDefaultPageAccess(),
      features: {},
      package: null,
    }

    // 1. 查找用户
    const userId = await this.findUserByLoginName(loginName)
    if (!userId) return defaultPermission

    // 2. 查找有效成员关系
    const mappingRes = await this.bitableService.searchRecords(this.appToken, this.mappingTableId, {
      filter: {
        conjunction: 'and',
        conditions: [
          { fieldName: '用户记录ID', operator: 'is', value: [userId] },
          { fieldName: '状态', operator: 'is', value: ['active'] },
        ],
      },
      pageSize: 1,
    })
    if (mappingRes.records.length === 0) return defaultPermission
    const purchaseId = mappingRes.records[0].fields['购买记录ID'] as string

    // 3. 查购买记录（悬挂引用保护）
    const purchaseRes = await this.bitableService.searchRecords(this.appToken, this.purchasesTableId, {
      filter: { conjunction: 'and', conditions: [{ fieldName: '状态', operator: 'is', value: ['active'] }] },
      pageSize: 500,
    })
    const purchase = purchaseRes.records.find(r => r.id === purchaseId)
    if (!purchase) return defaultPermission

    // 4. 检查到期
    const expiryDate = purchase.fields['到期日期'] as number | undefined
    if (expiryDate && expiryDate < Date.now()) return defaultPermission

    // 5. 查套餐
    const packageId = purchase.fields['套餐记录ID'] as string
    const pkgRes = await this.bitableService.searchRecords(this.appToken, this.packagesTableId, {
      filter: { conjunction: 'and', conditions: [{ fieldName: '是否启用', operator: 'is', value: ['启用'] }] },
      pageSize: 50,
    })
    const pkg = pkgRes.records.find(r => r.id === packageId)
    if (!pkg) return defaultPermission

    // 6. 解析「包含能力」
    const capabilitiesRaw = (pkg.fields['包含能力'] as string) || ''
    const capabilityIds = capabilitiesRaw.split('\n').map(s => parseInt(s.trim())).filter(n => !isNaN(n))

    // 7. 查功能特性表，构建权限对象
    const featuresRes = await this.bitableService.searchRecords(this.appToken, this.featuresTableId, {
      pageSize: 50,
    })
    const pageAccess: Record<string, boolean> = this.getDefaultPageAccess()
    const features: Record<string, boolean> = {}

    for (const feat of featuresRes.records) {
      const capId = feat.fields['能力编号'] as number
      if (!capabilityIds.includes(capId)) continue

      const permissionType = feat.fields['权限类型'] as string
      if (permissionType === 'page_access') {
        const route = feat.fields['对应路由'] as string
        if (route) pageAccess[route] = true
      } else if (permissionType === 'feature_flag' || permissionType === 'exposure_privilege') {
        const key = feat.fields['特性标记Key'] as string
        if (key) features[key] = true
      }
    }

    return {
      pageAccess,
      features,
      package: {
        id: pkg.id,
        name: pkg.fields['套餐名称'] as string,
        level: pkg.fields['套餐等级'] as number,
        maxAccounts: pkg.fields['最大账号数'] as number,
        role: (mappingRes.records[0].fields['角色'] as string) || 'member',
        purchasePrice: purchase.fields['购买价格（分）'] as number,
        purchaseDate: purchase.fields['购买日期'] as string,
        expiryDate: purchase.fields['到期日期'] as string || null,
      },
    }
  }

  /** 默认页面访问权限（免费用户） */
  private getDefaultPageAccess(): Record<string, boolean> {
    // 免费用户：AI 问答 + AI 配单（根据 1.4 节非年费入门方式）
    return {
      '/ai/qa': true,
      '/ai/price': false,
      '/ai/stock': true,
      '/ai/sales-strategy': false,
      '/ai/sales-smart': false,
      '/data/view': false,
      '/data/api': false,
      // ... 其他页面默认 false
    }
  }

  /** 检查某企业是否有某曝光特权（供 AI 配单/问答服务调用） */
  async checkEnterpriseFeature(enterpriseName: string, featureKey: string): Promise<boolean> {
    // 1. 查企业权限缓存
    let entCache = this.enterpriseFeatureCache.get(enterpriseName)
    if (!entCache) {
      entCache = new Map()
      this.enterpriseFeatureCache.set(enterpriseName, entCache)
    }
    const cached = entCache.get(featureKey)
    if (cached !== undefined) return cached

    // 2. 查用户表中该企业的用户
    const userRes = await this.bitableService.searchRecords(this.appToken, this.usersTableId, {
      filter: {
        conjunction: 'and',
        conditions: [{ fieldName: '企业名称', operator: 'is', value: [enterpriseName] }],
      },
      pageSize: 100,
    })
    if (userRes.records.length === 0) {
      entCache.set(featureKey, false)
      return false
    }

    // 3. 遍历该企业的用户，任一拥有该特权即返回 true
    for (const user of userRes.records) {
      const permission = await this.getUserPermission(user.fields['登录名'] as string)
      if (permission.features[featureKey]) {
        entCache.set(featureKey, true)
        return true
      }
    }

    entCache.set(featureKey, false)
    return false
  }

  /** 添加子账号 */
  async addMember(ownerLoginName: string, memberLoginName: string): Promise<Result> {
    // 1. 校验 owner 权限
    // 2. 校验名额（从飞书动态读取 maxAccounts）
    // 3. ensureUser 子账号（先查后建）
    // 4. 校验子账号未加入其他套餐
    // 5. batchCreate 成员关系表
    // 6. 清除子账号缓存
  }

  /** 移除子账号 */
  async removeMember(ownerLoginName: string, memberLoginName: string): Promise<void> {
    // ... 更新成员关系表状态为 inactive
    this.clearPermissionCache(memberLoginName)
  }
}
```

### 5.5 缓存策略

| 缓存 | 位置 | TTL | 失效时机 |
|------|------|-----|---------|
| 用户权限 | `permissionCache: Map<loginName, UserPermission>` | 5 分钟 | 添加/移除成员时主动清除 |
| 企业曝光特权 | `enterpriseFeatureCache: Map<enterpriseName, Map<featureKey, boolean>>` | 5 分钟 | 套餐变更时清除该企业所有用户的权限缓存 |
| 套餐列表 | 不缓存（实时查询） | — | — |

> **为什么不用 Redis**：当前项目没有 Redis 基础设施。单实例内存缓存足够——VIP 数据量小，服务重启后缓存自动重建，不丢数据。

---

## 六、与登录模块的集成

### 6.1 登录接口增强

在 `auth.service.ts`（重构方案阶段二）的 `login()` 方法中，51bxg 验证通过后增加飞书权限查询：

```typescript
async login(loginName: string, password: string) {
  // 1. 调用 ProxyService 转发至 51bxg PostLogin（现有逻辑）
  const bxgResult = await this.proxyService.forward('51bxg', 'General', 'PostLogin', {
    loginName,
    Password: password,
  })

  if (!bxgResult.success) return bxgResult

  // 2. 本地用户同步（懒创建，写入飞书用户表）
  const userId = await this.vipService.ensureUser(loginName)

  // 3. 查询用户完整权限（内部有5分钟缓存）
  const permission = await this.vipService.getUserPermission(loginName)

  // 4. 合并返回
  return {
    ...bxgResult,
    data: {
      ...bxgResult.data,
      permission,  // 新增：完整权限对象
    },
  }
}
```

### 6.2 前端 auth store 适配

在现有 `stores/auth.ts` 的 `login()` 方法中，新增权限存储：

```typescript
// 在 login() 方法中，51bxg 验证通过后：
if (res.data) {
  // ... 现有字段赋值保持不变 ...

  // 新增：完整权限对象
  const permission = res.data.permission
  if (permission) {
    // 页面访问权限
    const vipStore = useVipStore()
    vipStore.loadPageAccess(permission.pageAccess)
    
    // 功能特性标记
    vipStore.loadFeatures(permission.features)
    
    // 套餐信息
    if (permission.package) {
      setStorage('auth_package', JSON.stringify(permission.package))
    }
  }
}
```

### 6.3 新旧 VIP 判断逻辑过渡

| 场景 | 旧逻辑 | 新逻辑 |
|------|--------|--------|
| 新用户登录 | `SERVICES.includes('003')` → VIP | `permission` 来自飞书套餐查询 |
| 已有 51bxg VIP 用户 | `SERVICES.includes('003')` → VIP | 同时检查飞书套餐，取较高权限 |
| 过渡期 | 保持旧逻辑 | 新增飞书权限，双轨运行 |

> 过渡期：旧逻辑保留作为兜底。51bxg 的 `SERVICES` 字段和飞书套餐可以共存，页面访问权限取两者中的较宽松值。

---

## 七、前端页面设计

### 7.1 新建页面

| 页面 | 路由 | 说明 |
|------|------|------|
| VIP套餐 | `/vip/packages` | 套餐展示页，展示 8 个套餐卡片（含免费档） |
| 我的套餐 | `/vip/my-package` | 套餐管理页，查看成员、添加/移除子账号 |

### 7.2 VIP 套餐页（`/vip/packages`）

- 8 个套餐卡片按等级递进排列（含免费档）
- 每个卡片显示：套餐名、年费、共享人数、定位说明、包含能力列表
- 当前套餐高亮标记「当前套餐」
- 「购买」按钮（第一阶段为模拟购买）

### 7.3 我的套餐页（`/vip/my-package`）

- 套餐信息卡片：套餐名、等级、到期时间、共享人数
- 成员列表：显示所有成员及其角色
- 「添加成员」按钮：弹出输入框，输入 51bxg 登录名
- 每个成员行右侧「移除」按钮（仅 owner 可见）

### 7.4 功能特性在前端的展现

| 编号 | 功能点 | 前端展现方式 |
|------|--------|------------|
| 6 | 秀吗保交付 | `/ai/stock` 配单结果中显示「保交付」认证标记 |
| 7 | 企业录入 | `/ai/stock` 页面显示「录入商品」入口（无权限则隐藏） |
| 8 | AI 配单优质推荐 | 前端不展现该权限（后端排序逻辑处理） |
| 9 | API 全量接口 | `/data/api` 页面显示「申请 API Key」入口 |

### 7.5 导航入口

在 Sidebar 中增加「增值服务」菜单下的子菜单项：

| 子菜单 | 标签 | 路由 |
|--------|------|------|
| VIP套餐 | VIP | `/vip/packages` |

或者将入口放在 Header 用户头像下拉菜单中，作为「我的套餐」链接。

---

## 八、实施计划

### 8.1 前置依赖

本方案依赖「账号登录模块重构方案」的阶段二（auth 模块）完成，因为：

- 需要独立的 `/api/auth/login` 路由来集成权限查询
- 需要 `AuthService` 作为权限查询的调用入口

### 8.2 实施步骤

| 阶段 | 内容 | 新建文件 | 修改文件 | 风险 |
|------|------|---------|---------|------|
| 一 | 飞书多维表格建表 + 种子数据录入（5张表） | —（在飞书后台操作） | `.env`（新增5个环境变量） | 低 |
| 二 | VipModule（Service + Controller + PermissionService） | 5 个文件 | 1 个（app.module.ts） | 中 |
| 三 | 登录接口增强（集成权限查询） | — | 1 个（auth.service.ts） | 中 |
| 四 | 前端 auth store + vip store 适配 | — | 2 个（auth.ts + vip.ts store） | 中 |
| 五 | 前端套餐页面 + 功能特性展现 | 2 个页面 + 路由 | 1 个（导航配置） | 中 |
| 六 | AI 配单/问答集成曝光特权排序 | — | 2 个（配单服务 + 问答服务） | 高 |
| **合计** | | **7+ 个** | **7 个** | **中-高** |

### 8.3 飞书多维表格创建

**步骤一**：在飞书后台创建多维表格应用，记录 `appToken`。

**步骤二**：在该应用中创建 5 张数据表，按 3.2 节定义设置字段：

| 表名 | 说明 | 获取 tableId |
|------|------|-------------|
| 用户表 | 存储本地用户 | 从 URL 中提取 |
| 套餐表 | 8 个套餐种子数据（含免费档） | 手动录入 |
| 功能特性表 | 12 项能力元数据 | 手动录入 |
| 购买记录表 | 套餐购买记录 | 运行时写入 |
| 成员关系表 | 用户-套餐关联 | 运行时写入 |

**步骤三**：在套餐表中手动录入 8 行种子数据（含免费档，见 3.2 节）。

**步骤四**：在功能特性表中手动录入 12 行能力元数据（见 3.2 节）。

**步骤五**：将 `appToken` 和 5 个 `tableId` 配置到 `.env` 文件。

> 不需要数据库初始化代码 — `FeishuBitableService` 已在 `FeishuModule`（`@Global()`）中提供，VipService 直接注入即可。

---

## 九、安全与边界

### 9.1 安全考虑

| 风险 | 措施 |
|------|------|
| 子账号越权操作 | 所有套餐管理接口校验 `role='owner'` |
| 子账号被移除后仍可访问 | 每次请求实时查询飞书成员关系表，不依赖前端缓存 |
| 套餐到期后仍可访问 | 查询时检查「到期日期」，过期自动降级为免费用户 |
| 同一用户加入多个套餐 | 写入成员关系表前，先查询是否已有 active 记录 |
| 购买记录被误删（悬挂引用） | `queryUserPermission` 中查找 purchase 为 null 时返回默认权限，不抛异常 |
| 飞书 API 调用频率限制 | 引入 5 分钟内存缓存（用户权限 + 企业曝光特权） |
| 飞书 token 过期 | `FeishuBitableService.ensureToken()` 已内置自动刷新机制 |
| 曝光特权被绕过 | AI 配单/问答服务端排序逻辑必须调用 `checkEnterpriseFeature`，不信任前端 |

### 9.2 明确不涉及的内容

- **不接真实支付** — 第一阶段仅模拟购买（`POST /api/vip/purchase` 直接创建记录）
- **不修改 51bxg 数据库** — 所有数据存储在飞书多维表格，独立于 51bxg
- **不引入 JWT** — 与重构方案一致，认证仍依赖 51bxg API
- **不做套餐升级/降级** — 第一阶段仅支持单一套餐购买
- **不做支付回调** — 等接入真实支付后再实现
- **不处理"已满后减少账号数"** — 管理员下调 `maxAccounts` 后，已有成员不主动剔除，代码后续优化

---

## 十、与现有 VIP 体系的兼容

### 10.1 现有系统状态

当前 VIP 权限配置存储在飞书多维表格 `vip_page_permission` 中，定义如下：

- 表中有 `allow_level_0` 到 `allow_level_7` 共 8 个字段（对应 L0-L7）
- 但实际代码中 `userLevel` 只有 0/1 两个值（`auth.ts:113`）
- 所以 `allow_level_2` 到 `allow_level_7` 从未被使用

### 10.2 迁移方案

新方案采用**双层权限模型**（pageAccess + features），不再使用 `allowLevels` 数组。迁移策略：

| 旧字段 | 新模型 | 说明 |
|--------|--------|------|
| `allow_level_0` ~ `allow_level_7` | `pageAccess: { '/route': boolean }` | 按套餐包含的能力动态构建，不再用固定数组 |

**迁移步骤**：

| 步骤 | 操作 | 方式 |
|------|------|------|
| 1 | 创建新的 `vip_packages` 表（含 7 档套餐） | 飞书后台操作 |
| 2 | 创建 `vip_features` 表（含 10 项能力元数据） | 飞书后台操作 |
| 3 | 在 `vip_packages` 表中为每档套餐配置「包含能力」 | 飞书后台手动录入 |
| 4 | 更新 `stores/vip.ts`：`canAccess(path)` 改为查 `pageAccess` 对象 | 代码修改 |
| 5 | 更新后端 `ErpVipService`：从新表读取权限配置 | 代码修改 |
| 6 | 验证通过后，旧的 `vip_page_permission` 表可保留作为备份 | — |

### 10.3 新旧权限模型对比

| 维度 | 旧模型 | 新模型 |
|------|--------|--------|
| 权限粒度 | 按等级（L0-L7） | 按能力（10项）+ 按功能特性 |
| 权限类型 | 仅页面访问 | 页面访问 + 功能特性 + 曝光特权 |
| 配置方式 | 每页 8 列 allowLevels | 每套餐「包含能力」字段 |
| 扩展性 | 加等级需改代码 | 加能力只需改飞书表 |

---

## 十一、待确认事项

> 以下事项需要与业务方确认后再细化，当前文档基于合理假设：

1. **"秀吗保交付"的具体含义** — 当前假设为"配单结果中的认证标记"，需确认是认证标记、交易担保服务、还是上架秀吗资格
2. **"专属服务"、"场景定制"、"私有化部署"的对应路由** — 这三项能力目前没有对应的现有页面，需确认是否需要新建页面还是仅作为业务标记
3. **"私有化部署"为何在所有套餐中均未勾选** — 是单独洽谈的业务，还是遗漏？如需加入某档套餐，只需在飞书表格中修改
4. **企业录入的数据存储位置** — 企业录入的产品/报价存在飞书表格？还是 51bxg 商品库？还是独立表？
5. **曝光特权的查询性能** — AI 配单每次查询都要遍历候选商品所属企业的功能特权，是否需要更激进的缓存策略
6. **试用套餐的到期处理** — 7 天后自动降级为免费用户，是否需要到期前提醒
7. **积分兑换与套餐体系的关系** — 51 号积分兑换是独立体系还是与年费套餐共用权限模型
8. **入门版与进阶版的能力清单完全相同** — 差异仅在数据范围（测1系/查1系 vs 测全钢种/查全系），这个数据范围限制如何在代码中实现？是否需要增加"数据范围"字段？

---

## 十二、注意事项

1. **依赖约束**：必须等待「账号登录模块重构方案」阶段二完成后才能开始本方案的实施
2. **飞书环境**：本地开发和生产环境需配置相同的飞书多维表格应用（或分别创建开发/生产应用）
3. **向后兼容**：现有 `SERVICES.includes('003')` 逻辑保留作为兜底
4. **价格单位**：飞书存储以「分」为单位，前端展示时除以 100
5. **无 JOIN 查询**：飞书多维表格不支持 JOIN，关联查询需要分步执行
6. **种子数据**：套餐表和功能特性表数据在飞书后台手动录入，不通过代码自动创建
7. **缓存失效**：添加/移除成员后必须调用 `clearPermissionCache()`，否则被操作的用户在 5 分钟内仍看到旧权限
8. **动态账号数**：`maxAccounts` 从飞书表格动态读取，管理员修改后下次查询生效（缓存内可能延迟 5 分钟）
9. **曝光特权特殊性**：推荐/GEO 不是当前登录用户的权限判断，而是商品所属企业的权限判断，需在 AI 配单/问答服务端实现
10. **能力项数**：共 12 个子项，分 8 个分类（见 1.3 节）。其中"通用知识库"和"行业数据库"在所有套餐中总是同时出现，"AI预测"和"AI查询"也总是同时出现，但权限控制按 12 个子项独立设计
