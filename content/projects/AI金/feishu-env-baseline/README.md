# 飞书妙搭环境基准（feishu-env-baseline）

> **唯一正确、最权威的飞书真实环境事实基准。**
> 所有信息均来自**飞书妙搭沙箱终端**的实测输出（用户本人在飞书终端执行命令获得），
> 不代表本地猜测或文档假设。后续排查以本目录为准，本地 `agents.md` / 记忆 / 旧 skill 如有冲突，以此处为准。

## 定位与用途

- 目标：摸透飞书妙搭环境（操作系统 / 运行时 / 编译流程 / 发布流程 / CLI / 依赖 / 环境变量 / 隐藏配置）。
- 用途：今后在本地高效复现、审查、定位问题——省去每次上飞书慢速排查。
- 原则：
  1. 只新增、不修改本目录之外的历史文件（本轮聚焦摸环境）。
  2. 每份记录注明「来源：飞书终端实测」及日期。
  3. 含密钥/敏感变量值**不落库**（本目录可能进 git），只记「键名 + 作用」。

## 目录

| 文件 | 内容 | 采集日期 |
|---|---|---|
| `01-环境事实-2026-08-26.md` | 首轮探针：根目录结构、`@lark-apaas` 依赖、npm scripts、环境变量键名清单、miaoda CLI 概览 + 解析 | 2026-08-26 |
| `02-环境事实-2026-08-26-工作区与脚本.md` | 工作区全貌、完整 package.json、@lark-apaas 26 包盘点、build.sh/dev-local.js/lint.js、CLI 子命令、CLIENT_BASE_PATH 确认 | 2026-08-26 |
| `03-环境事实-2026-08-26-run与prune与dev.md` | run.sh / prune-smart.js / dev.js：产物结构、依赖裁剪机制、沙箱守护 | 2026-08-26 |
| `04-环境事实-2026-08-26-server入口与配置.md` | main.ts / app.module.ts、fullstack-nestjs-core 产物结构、.env 键名、nest-cli/vite/tsconfig | 2026-08-26 |
| `05-环境事实-2026-08-26-平台内核CSRF与前缀.md` | CSRF 双提交三行、csrf_token 生成、CLIENT_BASE_PATH 前缀剥除机制 | 2026-08-26 |
| `06-环境事实-2026-08-26-configureApp与PlatformModule装配终局.md` | configureApp 完整逻辑、PlatformModule 中间件矩阵、装配顺序全景图、历史 bug 闭环 | 2026-08-26 |
| `07-环境事实-2026-08-26-中间件矩阵细节.md` | 各中间件职责/触发范围/归属（apiResponse/View/HTMLHotUpdate/SQL/User）、前端构建配置 | 2026-08-26 |
| `08-环境事实-2026-08-26-中间件实现体.md` | 中间件实现体：UserContext(请求头解析web用户)、ViewContext(应用元数据+basename)、apiResponse护栏、HTMLHotUpdate、SqlExec归属 | 2026-08-26 |
| `09-环境事实-2026-08-26-nestjs-datapaas包.md` | @lark-apaas/nestjs-datapaas 包：版本1.0.21、postgres+drizzle-orm0.44.6依赖、SqlExecutionContextMiddleware 定位683-722行 | 2026-08-26 |
| `10-环境事实-2026-08-26-datapaas-RLS模型与provider.md` | SqlExecutionContext 实现体=RLS(PG行级安全)、SET ROLE/service_role·authenticated·anon、DRIZZLE_DATABASE代理、ssl require | 2026-08-26 |
| `11-环境事实-2026-08-26-用户身份头与静态资源与configureApp装配.md` | 平台用户身份=suda_web_user头(UserContext解析)、静态资源直出dist/client、configureApp完整装配(1mb/legacy/前缀/trust proxy) | 2026-08-26 |
| `12-环境事实-2026-08-26-环境映射与前缀白名单与CSRF生成与runWithAuthContext.md` | mapToWindowEnvironment(boe→staging/pre→gray)、PLATFORM_PREFIXES完整数组(api/openapi/__innerapi__/__runtime__/static/dev/assets)、CSRF genToken(sha1-token)、runWithAuthContext定位660行 | 2026-08-26 |
| `13-依赖优化实录-2026-08-27.md` | 飞书 package.json 依赖优化实录（补 @element-plus/icons-vue/fast-xml-parser、xlsx迁deps、删tiptap全家桶等23个dev冗余包）+ 优化暴露的环境坑（build OOM需NODE_OPTIONS、devserver旧缓存假缺包） | 2026-08-27 |
| `feishu-platform-architecture/feishu-platform-architecture.html` | 综合 01-12 的架构速览报告（装配流程图/CSRF链路/RLS数据通道），浏览器打开可通读 | 2026-08-26 |

## 环境速览（首轮摘要）

- 登录用户/工作目录：`gem` @ `~/workspace/code`
- 部署形态：Faas（BYTEFAAS / _FAAS_*）托管运行时 + NGINX + supervisor，Linux 容器
- 语言栈：前端 Vue3 + Vite，后端 Nest.js（Node）
- 数据库：PostgreSQL（`SUDA_DATABASE_URL`）
- 平台依赖：`@lark-apaas/*`（schema.ts 由 `db-schema-sync` 生成）
- 发布/管理 CLI：`miaoda` v0.1.38（app / deploy / db / file / observability / skills / registry）

## 待办 / 下一步探针

- [x] 下载并解析 `@lark-apaas/*` 实际安装 JS 产物（读 `configureApp` / `PlatformModule` / CSRF / 前缀）→ 05/06
- [x] 读取 `scripts/build.sh` / `dev-local.js` / `lint.js`，还原编译与本地启动流程 → 02/03
- [x] 用 `miaoda deploy --help` / `db --help` 还原发布与数据库命令细节 → 02
- [x] 读 `package.json` 完整内容 + `.npmrc` + 隐藏配置 → 02
- [x] 抓 `CLIENT_BASE_PATH` 具体值，验证是否 `/app/app_xxx` 前缀来源 → 02（`/app/app_4k9x70cg0jws9/`）
- [x] 捕获首次访问的 `Set-Cookie`，验证 CSRF cookie 由谁种下 → 05/06（CsrfTokenMiddleware 页面种）
- [x] 下钻 4 个中间件实现体（apiResponse/View/HTMLHotUpdate/User + datapaas SqlExec）→ 08
- [ ] 下钻 `@lark-apaas/nestjs-datapaas/dist` 的 SqlExecutionContext（已确认为外部实现，可选）