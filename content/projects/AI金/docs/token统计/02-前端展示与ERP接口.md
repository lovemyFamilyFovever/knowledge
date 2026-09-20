# Token 统计 — 前端展示与 ERP 接口

> 版本: v1.1 | 日期: 2026-07-27 | 状态: 已实现

## 一、前台页面（用户视角）

### 1.1 路由

| 入口 | 路径 | 说明 |
|------|------|------|
| 个人中心 | `/personal/token-stats` | 个人中心侧边栏「Token 统计」菜单 |

### 1.2 页面组件

`client/src/pages/TokenStatsPage.vue`

**接口**：`GET /api/ai/token-stats/my?days=30`

**展示内容**：

| 区域 | 内容 |
|------|------|
| 今日汇总卡片 | 总 Token 数 + 总调用次数，大字号突出 |
| 各分类明细 | 问答 / 测价 / 配单 三列卡片，显示各自 Token 数和调用次数 |
| 近 7 天趋势 | ECharts 折线图（横轴：日期，纵轴：Token 数） |
| 历史记录表 | 日期 + Token 数 + 调用次数，按日期降序 |

### 1.3 API 响应结构

```json
{
  "success": true,
  "data": {
    "today": {
      "totalTokens": 75000,
      "callCount": 26,
      "byCategory": {
        "qa": { "totalTokens": 45000, "callCount": 15 },
        "forecast": { "totalTokens": 18000, "callCount": 3 },
        "matching": { "totalTokens": 12000, "callCount": 8 }
      }
    },
    "daily": [
      { "date": "2026-07-26", "totalTokens": 75000, "callCount": 26 },
      { "date": "2026-07-25", "totalTokens": 82000, "callCount": 31 }
    ]
  }
}
```

### 1.4 关联文件

- `client/src/pages/TokenStatsPage.vue` — 前台页面
- `client/src/api/ai.ts` — `fetchMyTokenStats()` 接口函数
- `client/src/router/index.ts` — `/personal/token-stats` 路由
- `client/src/layouts/PersonalCenterLayout.vue` — 侧边栏菜单项

---

## 二、ERP 后台（管理员视角）

### 2.1 实现位置

ERP 后台 Token 统计看板已独立实现，详见 `docs/erp/07-AI用量统计与计费.md` 第九章。

| 项目 | 路径 |
|------|------|
| 页面路由 | `/erp/token-stats` |
| 前端目录 | `erp/token-stats/` |
| 后端服务 | `erp/server/erp-token-stats.service.ts` |
| 后端控制器 | `erp/server/erp-token-stats.controller.ts` |

### 2.2 ERP API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/erp/token-stats/overview?days=7` | 用量概览 + 每日趋势 |
| GET | `/api/erp/token-stats/ranking?days=7` | 用户用量排行 |
| GET | `/api/erp/token-stats/user-detail?userId=&days=30` | 单个用户详情 |

### 2.3 关键指标

| 指标 | 说明 |
|------|------|
| 总 Token 消耗 | 指定时间段内全平台 Token 总量 |
| 总调用次数 | 指定时间段内全平台调用次数 |
| 活跃用户数 | 时间段内有调用的用户数 |
| 日均 Token | 总 Token / 天数 |
| 按分类分布 | 问答 / 测价 / 配单 的 Token 和调用次数 |
| 用户排行 | 按 Token 消耗降序排列的用户列表 |

### 2.4 与前台 Token 统计页的关系

| 维度 | 前台 Token 统计页 | ERP Token 统计看板 |
|------|-------------------|---------------------|
| 用户范围 | 仅自己 | 全平台用户 |
| 数据粒度 | 按天+分类汇总 | 汇总+明细+排行 |
| 图表 | 个人趋势 | 全平台趋势+用户排行 |
| 权限 | 登录用户 | ERP 管理员 |

---

## 三、API 接口文档（详细）

### 3.1 `GET /api/ai/token-stats/my`

查询当前登录用户的 Token 统计（前台用）。

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `days` | number | 返回最近 N 天的数据（默认 30） |

### 3.2 `GET /api/ai/token-stats/all`

查询所有用户的 Token 统计（ERP 后台用，需管理员权限校验）。

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `startDate` | string | 开始日期 `YYYY-MM-DD` |
| `endDate` | string | 结束日期 `YYYY-MM-DD` |
| `category` | string | 可选筛选：`qa` / `forecast` / `matching` |
| `userId` | string | 可选筛选：指定用户 |

**响应示例：**

```json
{
  "success": true,
  "data": {
    "summary": {
      "totalTokens": 1250000,
      "totalCalls": 450,
      "activeUsers": 12,
      "byCategory": {
        "qa": { "totalTokens": 600000, "callCount": 300 },
        "forecast": { "totalTokens": 450000, "callCount": 50 },
        "matching": { "totalTokens": 200000, "callCount": 100 }
      }
    },
    "byUser": [
      {
        "userId": "user_001",
        "userName": "张三",
        "totalTokens": 320000,
        "callCount": 120,
        "qaTokens": 150000,
        "qaCalls": 80,
        "forecastTokens": 120000,
        "forecastCalls": 10,
        "matchingTokens": 50000,
        "matchingCalls": 30,
        "lastActiveAt": "2026-07-26 17:30"
      }
    ],
    "daily": [
      { "date": "2026-07-26", "totalTokens": 85000, "callCount": 45,
        "byCategory": { "qa": { "tokens": 45000, "calls": 25 } } },
      { "date": "2026-07-25", "totalTokens": 92000, "callCount": 52 }
    ],
    "records": [
      {
        "date": "2026-07-26",
        "userId": "user_001",
        "userName": "张三",
        "category": "qa",
        "callCount": 15,
        "totalTokens": 45000,
        "inputTokens": 28000,
        "outputTokens": 17000,
        "cachedTokens": 2000,
        "cacheCreationTokens": 0,
        "models": "qwen-turbo",
        "lastCallAt": "2026-07-26 17:30",
        "lastQuestion": "304不锈钢和316L有什么区别"
      }
    ]
  }
}
```

---

## 四、关联文件

- `client/src/pages/TokenStatsPage.vue` — 前台个人 Token 统计页
- `client/src/api/ai.ts` — `fetchMyTokenStats()` 接口函数
- `client/src/router/index.ts` — `/personal/token-stats` 路由
- `client/src/layouts/PersonalCenterLayout.vue` — 侧边栏菜单项
- `erp/token-stats/` — ERP 后台 Token 统计看板
- `erp/server/erp-token-stats.service.ts` — ERP Token 统计服务
- `erp/server/erp-token-stats.controller.ts` — ERP Token 统计 API
- `docs/erp/07-AI用量统计与计费.md` — ERP Token 消耗统计详细文档