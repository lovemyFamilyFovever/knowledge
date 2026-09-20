# 09 环境事实 —— @lark-apaas/nestjs-datapaas 包（SqlExecutionContext 定位）（2026-08-26）

> 来源：飞书沙箱终端实测（cat package.json + grep 定位 `nestjs-datapaas/dist/index.js`）。
> 结论：SqlExecutionContextMiddleware 实现在该包 683-722 行；本节先归档包信息，实现体待 10 补读。

---

## 1. 包基本盘

| 项 | 值 |
|---|---|
| 包名 | `@lark-apaas/nestjs-datapaas` |
| 版本 | `1.0.21` |
| 类型 | `module`（ESM），main `./dist/index.js` |
| 产物 | `index.js`(40KB) / `index.cjs` / `.d.ts` / `.map` |
| license | MIT |
| node | >=18.0.0 |

### 依赖
- **dependencies**：`@types/pg`、`postgres@^3.4.3`、`reflect-metadata`
- **peerDependencies**：`@lark-apaas/nestjs-common@^0.1.9`、`@lark-apaas/nestjs-observable@^0.0.12`、`@nestjs/common@^10`、`@nestjs/core@^10`、`drizzle-orm@0.44.6`

### 📌 关键洞察
- **底层用 `postgres` 驱动（pg 客户端）+ `drizzle-orm@0.44.6`（严格锁版本）** 做数据访问。
- peer 依赖表明它对 @nestjs/common/core v10、nestjs-common、nestjs-observable 有强绑定——是平台数据库访问层的核心。

---

## 2. SqlExecutionContextMiddleware 定位

```
683  var SqlExecutionContextMiddleware = class {
685    __name(this, "SqlExecutionContextMiddleware");
715  SqlExecutionContextMiddleware = _ts_decorate3([ ... ], SqlExecutionContextMiddleware);
722  ]
```
- 实现体 = `dist/index.js` 的 **683-722 行**（约 40 行，class 实现）。
- 另在 831/899 两处以 `provide + useClass` 注册（可能 dev/online 两份 provider 配置），861/930 导出到模块数组，1200 聚合导出。

### 职责（据平台中间件矩阵推断，待 10 证实）
- 数据通道 SQL 执行上下文：向当前请求的 SQL 执行注入上下文（约束/租户隔离/审计 trace）。
- 受 `DISABLE_DATAPASS` 门控（core 装配处 `...DISABLE_DATAPASS ? [] : [SqlExecutionContextMiddleware]` 控制是否挂载）。

---

## 3. 下一步（一读实现体即可闭环）

在飞书沙箱终端执行：
```bash
echo "=====DP-IMPL-BODY====="; sed -n '683,725p' node_modules/@lark-apaas/nestjs-datapaas/dist/index.js
echo "=====DP-PROVIDER====="; sed -n '800,935p' node_modules/@lark-apaas/nestjs-datapaas/dist/index.js
```
- 第一段读 class 实现（683-725），确认它到底做了什么（DB 上下文 / 租户 / 审计）。
- 第二段（800-935）看 provider 注册方式，理解 dev/online 两份配置差异。

> 敏感值不落库。