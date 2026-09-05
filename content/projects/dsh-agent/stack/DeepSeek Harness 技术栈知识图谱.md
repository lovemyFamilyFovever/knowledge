---
title: "DeepSeek Harness 技术栈知识图谱"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 技术栈图谱"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 技术栈知识图谱
DeepSeek Harness
技术栈知识图谱 — 完整的运行时、构建、测试、质量工具链深度分析
v0.1.1-rc.2 • MIT License • @deepseek-ai/dsh
目录导航
1
运行时技术栈
2
构建工具链
3
测试工具链
4
代码质量工具
5
开发工具与 Git 工作流
6
第三方依赖分析
7
依赖关系图
8
技术选型分析
9
技术栈总结与演进建议
⚡
第一部分：运行时技术栈
22+
Node.js 最低版本
TS 6
TypeScript 版本
ESM
模块系统
pnpm
包管理器 (11.7.0)
1.1 Node.js 版本要求
engines 约束
"engines": { "node": "^22.19.0 || >=24.0.0" }
项目要求
Node.js 22.19.0+
或
24.0.0+
。CI 中的主版本为
Node 24
（
PRIMARY_NODE_VERSION: '24'
），同时在 matrix 策略中对 Node 22.19 和 Node 26 进行兼容性测试。这意味着项目充分利用了 Node 22 LTS 和 Node 24 Current 的最新特性，同时前瞻性地验证 Node 26 的兼容性。
值得注意的是，Node 24 在 Worker 线程中存在已知问题：其 CJS lexer 在 macOS/Linux/Windows 上可能因
v8::ToLocalChecked Empty MaybeLocal
而中止。Vitest 配置中明确使用
pool: 'forks'
而非
threads
来规避此问题。
1.2 TypeScript 版本
TypeScript ^6.0.3
项目使用
TypeScript 6.x
，这是截至 2026 年 8 月的最新主版本。配置中的关键编译选项包括：
{
  "target": "es2024",
  "module": "esnext",
  "moduleResolution": "bundler",
  "strict": true,
  "composite": true,
  "incremental": true,
  "noUncheckedIndexedAccess": true,
  "exactOptionalPropertyTypes": true,
  "allowImportingTsExtensions": true,
  "rewriteRelativeImportExtensions": true
}
核心编译特性解析：
target: "es2024"
— 输出 ES2024 语法，充分利用最新 JS 引擎特性
moduleResolution: "bundler"
— 使用 bundler 解析模式，配合 tsdown 构建
composite: true
— 启用项目引用（Project References），将 Host 和 Client 分离编译
allowImportingTsExtensions + rewriteRelativeImportExtensions
— 允许直接 import
.ts
文件，构建时自动重写为
.js
exactOptionalPropertyTypes
— 严格区分
undefined
和可选属性，属于 TypeScript 最严格的模式之一
1.3 模块系统
全量 ESM（"type": "module"）
根
package.json
声明
"type": "module"
，所有包均使用 ES Module。从
tsconfig.base.json
的
"module": "esnext"
到 tsdown 的
format: ['esm']
，整个工具链全面拥抱 ESM。
唯一例外是
vendor/schemastery
同时提供 ESM 和 CJS 双格式导出（
import: ./lib/index.mjs
+
require: ./lib/index.cjs
），这是为了兼容部分需要 CJS 的消费者场景。
测试运行时通过
tsx
（TypeScript Execute）直接运行 TypeScript 源码，无需预编译。脚本统一使用
node --import tsx/esm
或
tsx
命令入口。
1.4 包管理器：pnpm 11.7.0
pnpm monorepo 工作区
通过
"packageManager": "pnpm@11.7.0"
锁定 pnpm 版本（Corepack 兼容）。工作区配置定义了多层包路径：
packages:
  - vendor/*               # 框架层（cordis 生态）
  - packages/*/*           # 核心业务包（50+ 个子目录）
  - native/landlock-run    # 原生沙箱启动器
  - apps/*                 # 产品装配（cli + web）
  - website                # 文档站
  - examples               # 可运行示例
  - python/sdk-runtime     # Python SDK 运行时
关键 pnpm 配置：
linkWorkspacePackages: true
— 工作区内包自动链接
overrides
将
@deepseek-ai/cosmokit
和
@deepseek-ai/schemastery
重定向到 vendor 目录
allowBuilds
精确控制哪些依赖可以执行安装脚本（仅 esbuild、lefthook、node-pty、koffi）
patchedDependencies
对
node-pty@1.2.0-beta.15
应用补丁
🔧
第二部分：构建工具链
2.1 tsdown（核心构建工具）
tsdown ^0.22.2
工作区级 TypeScript 构建器
tsdown
是本项目的
核心构建工具
，负责将 TypeScript 源码编译为可分发的 JavaScript 库。它基于 Rolldown（Rust 编写的 Rollup 替代品），提供极快的构建速度。
// tsdown.config.ts 核心配置
export default defineConfig(({ env }) => {
  const client = isBuildFaceClient(env?.DSH_BUILD_FACE)
  return {
    workspace: ['vendor/*', 'packages/*/*', 'apps/cli'],
    entry: client ? '' : ['lib/types/{index,invariant,startup}.js'],
    outDir: 'lib',
    format: ['esm'],
    platform: 'node',
    target: 'es2024',
    fixedExtension: false,
    dts: false,
    clean: false,
    plugins: client ? [] : [typertPlugin({ mode: 'workspace', faces: ['host'] })],
  }
})
双面构建（Dual-Face Build）架构：
Host 面
（
DSH_BUILD_FACE=host
）：编译服务端/Node.js 代码，运行 Typert 类型注册插件
Client 面
（
DSH_BUILD_FACE=client
）：编译浏览器端代码，选择声明了 browser bundle 的包
构建入口策略独特：Host 面的 entry 仅为
lib/types/{index,invariant,startup}.js
，这意味着构建依赖于
tsc -b
先产出类型文件，tsdown 再做后续打包。Client 面则允许每个包定义自己的
tsdown.client.ts
配置。
2.2 tsx（TypeScript Execute）
tsx ^4.22.4
零配置 TypeScript 运行时
tsx
用于
直接运行 TypeScript 源码
，无需预编译。在项目中承担两大角色：
脚本执行
：所有
scripts/
下的构建、验证、发布脚本均通过
tsx
运行（如
tsx scripts/build.ts
、
tsx scripts/run-gates.ts
）
CLI 开发
：
"dsh": "node --import tsx/esm apps/cli/src/bin.ts"
直接从源码运行 CLI
Git Hooks
：lefthook 中的所有验证任务通过
node_modules/.bin/tsx
调用
2.3 Vite（前端构建）
vite ^6.0.0
Web 前端构建
Vite 专门用于
apps/web
的前端构建。该应用是一个 React 18 SPA，通过
@vitejs/plugin-react
插件支持 JSX 转换。
// apps/web/package.json
"scripts": {
  "build": "vite build",
  "dev": "vite",
  "watch": "vite build --watch --no-emptyOutDir"
}
构建产物
dist/
由
apps/cli
的
dsh web
命令通过内置的 Web 服务器（
dsh-host-webserver
）和静态文件服务（
dsh-host-frontend-static
）提供服务。
2.4 构建流程全景
完整构建管道
TypeScript 源码
→
tsc -b（项目引用）
→
类型声明 + .js 中间产物
→
tsdown（打包优化）
→
lib/ 最终产物
CLI 产品构建
Host tsc -b
→
Host tsdown
→
Client tsc -b
→
Client tsdown
→
dsh CLI
Web 前端构建
React + TypeScript 源码
→
Vite Build
→
dist/ 静态资源
→
dsh web 服务
2.5 TypeScript 项目引用架构
Solution-style tsconfig
根
tsconfig.json
采用 Solution 模式，仅作为引用聚合器：
{
  "extends": "./tsconfig.base.json",
  "files": [],
  "references": [
    { "path": "./tsconfig.host.json" },
    { "path": "./tsconfig.client.json" }
  ]
}
tsconfig.base.json
包含了
所有包的路径映射
（约 100+ 条
paths
规则），使用通配符模式
@deepseek-ai/dsh-*
自动映射到对应的
packages/*/src
目录。这种设计确保了：
源码级路径解析：测试和开发时直接引用源码，而非编译产物
Host/Client 分离：通过独立的
tsconfig.host.json
和
tsconfig.client.json
进行独立编译
增量构建：
composite + incremental
确保只重编译变更的包
2.6 Typert 类型注册系统
自研
Typert TypeScript 类型注册
这是项目中的
自研工具
，以 tsdown 插件形式集成。Typert 在构建时分析 TypeScript 类型信息，生成运行时类型注册表（Type Registry），用于驱动 API Gateway、客户端代码生成等跨进程类型安全通信场景。它包含独立的 generator、registry、loader、protocol 四个子包。
🧪
第三部分：测试工具链
3.1 Vitest（单元测试框架）
vitest ^4.1.8
+
@vitest/coverage-v8 ^4.1.8
Vitest 是项目的
唯一测试框架
，用于单元测试、E2E 测试、快照测试、性能测试和 Web UI 测试。项目配置了
多种 Vitest 配置文件
：
vitest.config.ts
主配置：thread-safe + process-bound 双项目池
vitest.e2e.config.ts
端到端集成测试
vitest.snapshot.config.ts
快照回归测试
vitest.web.config.ts
Web UI 组件快照测试
vitest.web.perf.config.ts
Web UI 性能基准测试
vitest.web-stress.config.ts
Web UI 压力测试
3.2 测试池策略
双项目池架构（forks 模式）
主配置定义了两个并行测试项目：
projects: [
  {
    test: {
      name: 'thread-safe',
      pool: 'forks',          // fork 模式，避免 Node 24 CJS lexer 崩溃
      include: testIncludes,  // 排除 processBoundTests
    }
  },
  {
    test: {
      name: 'process-bound',
      pool: 'forks',
      include: processBoundTests, // 进程敏感测试单独隔离
    }
  }
]
为什么使用 forks 而非 threads？
Node 24 在 Worker 线程中存在已知的 CJS lexer 崩溃问题。使用
forks
池通过独立进程隔离测试，避免共享线程路径上的崩溃。
process-bound 测试
：涉及全局进程状态、进程 API 或时序敏感 I/O 的测试（如 JSONL 持久化、子进程生成、LLM 适配器、Worker 线程工作流），在独立 fork 中运行以确保稳定性。
3.3 覆盖率策略
100% 逐文件覆盖门禁
覆盖率配置极为严格：
每个源文件
都必须达到 100% 的 statements/branches/functions/lines 覆盖率。
thresholds: {
  perFile: true,      // 逐文件，不允许大文件补贴小文件
  statements: 100,
  branches: 100,
  functions: 100,
  lines: 100,
}
覆盖范围排除策略：
类型文件
（
types.ts
）：无运行时代码，天然排除
入口胶水
（
bin.ts
、
worker.ts
）：通过子进程测试覆盖，不在单元测试中导入
GUI/Client 层
：大量 UI 组件文件被暂时排除，标记了 TODO(gui) 待后续补齐
平台特定代码
：Windows-only 代码（
sandbox-windows-acl
、
windows-inspector.ts
）在 Linux CI 中排除
Typert generator
：由独立的 fixture 套件保证正确性，不走 v8 覆盖率
覆盖率分区
：支持通过
DSH_COVERAGE_PARTITIONS
环境变量将覆盖率计算分成多个并行分区（CI 中设置为 4 或 8），加速大型仓库的覆盖率收集。
3.4 测试辅助设施
vite-tsconfig-paths
确保测试中使用源码级路径解析（
tsconfig.base.json
的 paths），而非编译产物
Standard Decorator Plugin
自研 Vite 插件，在测试时预处理 TypeScript 标准装饰器语法（TC39 Stage 3），通过
ts.transpileModule
降级
jsdom 29.1.1
用于客户端 UI 组件测试，通过
@vitest-environment jsdom
pragma 按文件启用
fast-check ^4.8.0
基于属性的测试（Property-Based Testing），用于验证关键逻辑的泛化正确性
3.5 E2E 与快照测试
多层级 E2E 测试体系
类型
配置文件
说明
E2E 测试
vitest.e2e.config.ts
跨包集成测试，测试真实组装后的功能
快照回归
vitest.snapshot.config.ts
CLI 输出、LLM 对话等的字节级快照比对
Web 快照
vitest.web.config.ts
Web UI 渲染结果的视觉快照
Web 性能
vitest.web.perf.config.ts
Web UI 性能基准（replay 模式）
Web 压力
vitest.web-stress.config.ts
Web UI 压力测试
Playwright E2E
apps/web 内
真实浏览器 E2E（Chromium）
快照测试支持三种模式：默认（比对）、
record
（录制新快照）、
refresh
（刷新预期值），通过
DSH_SNAPSHOT
环境变量控制。
🛡️
第四部分：代码质量工具
4.1 oxlint（代码检查）
oxlint 1.76.0
+
oxlint-tsgolint 7.0.2001
oxlint 是由 Oxidation Compiler 团队（Rust 编写的 TypeScript/JavaScript linter）开发的超快 linter，是本项目
唯一的代码检查工具
，完全替代了 ESLint。
配置特点：
Type-Aware Linting
：启用
"typeAware": true
，支持需要类型信息的高级规则
TypeScript 插件
：启用
typescript
插件，包含 50+ 条 TypeScript 专用规则
SonarJS 插件
：启用
eslint-plugin-sonarjs
，检测重复代码和逻辑缺陷
Stylistic 插件
：启用
@stylistic/eslint-plugin
，强制代码格式（缩进2空格、无分号、单引号、尾逗号）
tsgolint
：oxlint-tsgolint 是 TypeScript Go 编译器的 linter 集成
分层规则策略：
层级
严格程度
说明
源码 (
src/**
)
最严格
启用
no-non-null-assertion
、
no-unnecessary-condition
、
require-await
等
测试 (
tests/**
)
宽松
允许
no-non-null-assertion
（expect 后断言）、
no-unnecessary-condition
（刻意测试边界）
vendor/
忽略
上游代码保持原有风格
示例 (
examples/
)
中等
放宽
require-await
（demo 回调符合 async 接口）
最高价值规则
：
typescript/no-floating-promises
被视为"仓库最高价值 linted bug 类"，用于捕获 agent loop 中丢失的 promise。
4.2 knip（死代码检测）
knip ^6.16.1
未使用依赖 & 导出检测
knip 扫描整个 monorepo，检测未使用的文件、导出和依赖。配置文件
knip.json
定义了精细的 workspace 级别入口和排除规则。
关键配置：
忽略
vendor/*
和
python/sdk-runtime
工作区（它们有独立的管理策略）
为每个
packages/*/*
定义独立的 entry 和 project 模式
特殊处理示例项目的
@deepseek-ai/.+
正则忽略（避免将内部依赖误报为未使用）
忽略已知的二进制文件（
bwrap
、
icacls
、
sandbox-exec
等平台工具）
运行命令：
knip --treat-config-hints-as-errors
，将配置提示也视为错误。
4.3 jscpd（重复代码检测）
jscpd ^5.0.12
代码重复率检查
// .jscpd.json
{
  "minTokens": 60,
  "minLines": 6,
  "mode": "mild",
  "format": ["typescript", "tsx"],
  "pattern": "**/*.{ts,tsx}",
  "ignore": ["**/tests/**", "**/tsdown.config.ts"],
  "reporters": ["console"],
  "exitCode": 1
}
检测阈值：最少 60 个 token 或 6 行代码。"mild" 模式提供适度的检测灵敏度。仅扫描 TypeScript 源码，排除测试文件和构建配置。
4.4 publint（包发布检查）
publint ^0.3.21
npm 包发布质量验证
publint 验证每个即将发布到 npm 的包是否符合最佳实践：检查
exports
字段正确性、
types
声明是否存在、
files
字段是否包含必要文件等。通过
tsx scripts/publint-all.ts
对所有发布包执行批量检查。
🛠️
第五部分：开发工具与 Git 工作流
5.1 lefthook（Git Hooks）
lefthook ^2.1.9
本地 Git 质量门禁
lefthook 在本地 Git 操作的关键节点设置质量检查：
Hook
检查项
说明
pre-commit
translation pairing
验证
*.i18n.yaml
翻译文件的配对完整性
archived agent notes
验证归档的 agent 笔记格式
lint (staged)
对暂存的
*.{ts,tsx,mts,cts,mjs}
文件运行 oxlint（带
--fix
）
third-party notices
依赖变更时自动重新生成 THIRD_PARTY_NOTICES.md
whitespace
git diff --cached --check
检查尾随空格
pre-merge-commit
translation + agent notes
合并提交前的重复验证
pre-push
typecheck
推送前执行完整 TypeScript 类型检查
lefthook 通过
pnpm postinstall
自动安装（
node scripts/install-lefthook.mjs
）。
5.2 CI/CD 管道
GitHub Actions 工作流矩阵
项目维护了
18 个 GitHub Actions 工作流文件
，覆盖完整的开发生命周期：
工作流
触发条件
说明
ci.yml
pull_request
主要 PR 检查：static/coverage/consumers + Node 兼容 + Python + Windows
ci-master.yml
push to master
master 分支的额外验证
e2e.yml
按需
完整 E2E 测试
sandbox.yml
按需
沙箱安全测试
release.yml
按需
DSH 发布流程
release-vendor.yml
按需
Vendor 包发布
release-publish.yml
按需
npm 发布
docs-pages.yml
push
文档站构建部署（GitHub Pages）
issue-lifecycle.yml
issues
Issue 生命周期管理
landlock-run.yml
按需
Landlock 沙箱原生构建
build-exe-for-python-sdk.yml
reusable
Python SDK 可执行文件构建
python-release.yml
按需
Python SDK 发布
5.3 CI 架构详解
PR CI 矩阵（ci.yml 核心结构）
每个 PR 触发
7 个必要检查
+ 1 个可选检查：
node-24 (static)
TypeScript 编译 + oxlint + knip + jscpd + publint + 文档验证 + Agent Notes 归档验证
node-24-coverage
100% 逐文件覆盖率门禁（8 个 worker、4 个分区）
node-24-consumers
快照测试 + Web 快照 + Playwright E2E + 产物验证 + publint
node-compat (22.19 + 26)
Node.js 版本兼容性烟雾测试
python-sdk
Python 3.10 keyless SDK 测试（uv + pytest）
python-runtime
Python SDK 可执行文件构建验证
windows (Wine)
Linux 上通过 Wine 验证 Windows 构建和生产站点
windows-native (非阻塞)
原生 Windows 16-core 完整门禁（不阻塞合并）
故障转移机制：
CI 支持通过
DSH_CI_FAILOVER_LINUX
和
DSH_CI_FAILOVER_WINDOWS
仓库变量一键将所有任务切换到自托管 runner 池，防止 GitHub hosted runner 宕机阻塞开发。
5.4 门禁系统（Gates）
统一的门禁编排系统
所有质量检查通过
scripts/run-gates.ts
统一编排，定义了多个门禁矩阵：
check:all        → 完整本地门禁
check:ci         → 主 CI 门禁
check:ci:static  → 静态分析（编译+lint+knip+jscpd）
check:ci:coverage → 覆盖率门禁
check:ci:snapshot → 快照测试门禁
check:ci:consumers → 消费者/产物门禁
check:ci:artifacts → 产物验证门禁
这种门禁编排设计使得本地开发和 CI 环境运行完全相同的检查序列，确保 "CI 绿灯 = 本地通过"。
📦
第六部分：第三方依赖分析
6.1 根级开发依赖（devDependencies）
根 package.json 开发依赖分类
分类
依赖
版本
用途
构建
tsdown
^0.22.2
工作区 TypeScript 构建器
tsx
^4.22.4
TypeScript 直接运行时
typescript
^6.0.3
TypeScript 编译器
测试
vitest
^4.1.8
测试框架
@vitest/coverage-v8
^4.1.8
V8 代码覆盖率
fast-check
^4.8.0
基于属性的测试
浏览器测试
jsdom
29.1.1
DOM 模拟环境
@testing-library/react
^16.3.2
React 组件测试工具
代码质量
oxlint
1.76.0
代码检查
oxlint-tsgolint
7.0.2001
TS Go linter 集成
knip
^6.16.1
死代码检测
jscpd
^5.0.12
重复代码检测
文档/验证
mermaid
11.16.0
Mermaid 图表渲染
mdast-util-from-markdown
^2.0.3
Markdown AST 解析
js-yaml
^4.2.0
YAML 解析
smol-toml
^1.7.1
TOML 解析
spdx-expression-parse
^5.0.0
SPDX 许可证表达式解析
其他
lefthook
^2.1.9
Git hooks 管理
publint
^0.3.21
包发布质量检查
6.2 Vendor 框架层依赖
vendor/ 层（Cordis 插件生态系统）
包名
版本
关键外部依赖
用途
@deepseek-ai/cordis
4.0.1
@standard-schema/spec
元框架核心（IoC 容器、服务注册、生命周期）
@deepseek-ai/cosmokit
1.8.2
—
通用工具库（零依赖）
@deepseek-ai/schemastery
3.18.1
@standard-schema/spec
类型驱动的 Schema 验证器
cordis-plugin-loader
1.0.2
cosmokit
插件加载器
cordis-plugin-hmr
1.0.16
chokidar, picomatch, esbuild
模块热替换
cordis-plugin-include
1.0.6
js-yaml
配置文件 include 支持
cordis-plugin-group
1.0.1
—
嵌套插件分组
cordis-plugin-timer
1.1.3
cosmokit
定时器服务
cordis-plugin-logger-console
1.0.1
supports-color
控制台日志输出
6.3 CLI 产品依赖
apps/cli 关键依赖（@deepseek-ai/dsh）
CLI 包是产品装配层，将 50+ 个 workspace 内部包组装为可执行的
dsh
命令。少量外部依赖：
依赖
版本
用途
commander
^15.0.0
命令行参数解析
js-yaml
^4.2.0
YAML 配置解析
node-addon-require-builtin
^0.1.4
原生 addon 加载
6.4 Web 前端依赖
apps/web 技术栈
依赖
版本
用途
react
^18.2.0
UI 框架
react-dom
^18.2.0
React DOM 渲染
@vitejs/plugin-react
^4.0.0
Vite React 插件
vite
^6.0.0
前端构建工具
playwright
^1.49.0
浏览器 E2E 测试
fflate
^0.8.2
压缩/解压库
🔗
第七部分：依赖关系图
7.1 Vendor 层内部依赖拓扑
Cordis 插件生态内部依赖关系
@deepseek-ai/cosmokit
（零依赖基础工具库）
↑ 被所有其他 vendor 包依赖
@standard-schema/spec
+
cosmokit
→
cordis (核心)
cosmokit
+
@standard-schema/spec
→
schemastery
cordis
→
plugin-timer
→
plugin-hmr
cordis
→
plugin-loader
→
plugin-include
cordis
→
plugin-group
cordis
→
plugin-logger-console
7.2 Workspace 依赖关系层次
三层架构依赖流向
┌─────────────────────────────────────────────────────────────────┐
│                      产品装配层 (apps/)                          │
│  ┌─────────────────────────┐  ┌──────────────────────────────┐  │
│  │    apps/cli (dsh CLI)   │  │    apps/web (Web Frontend)   │  │
│  │    50+ workspace deps   │  │    React + Vite              │  │
│  └───────────┬─────────────┘  └──────────────┬───────────────┘  │
│              │                               │                  │
├──────────────┼───────────────────────────────┼──────────────────┤
│              │     核心业务层 (packages/*/*)   │                  │
│  ┌───────────▼───────────────────────────────────────────────┐  │
│  │  core/     llm/      shell/    session/    client/        │  │
│  │  agent     llm       bash      session     ui-*          │  │
│  │  scope     llm-deep  pwsh      projection  connection    │  │
│  │  tools     llm-pi    terminal  query       modules       │  │
│  │  agent-loop          subprocess            web           │  │
│  │                                                        │  │
│  │  skill/    fs/       mcp/      sandbox/    subagent/     │  │
│  │  storage/  settings/ workflow/ plan/       preset/       │  │
│  │  goal/     compaction/ acp/    credentials/ interaction/ │  │
│  │  jobs/     feedback/ schedule/ guard/      bundle/       │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│                              │     框架层 (vendor/)              │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │  cordis (IoC) → cosmokit (utils) → schemastery (schema)  │  │
│  │  plugin-loader, plugin-hmr, plugin-include, plugin-group  │  │
│  │  plugin-timer, plugin-logger-console                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
7.3 版本约束策略
版本管理规范
策略
实现
说明
Workspace 内部
workspace:^
始终链接最新开发版本
Workspace examples
workspace:*
examples 使用通配链接
外部依赖
^
(caret)
允许 minor/patch 更新
锁文件
pnpm-lock.yaml
CI 使用
--frozen-lockfile
pnpm 版本
Corepack
"packageManager": "pnpm@11.7.0"
发布年龄门禁
minimumReleaseAgeExclude
防止过新依赖（pi-ai 等除外）
Peer 兼容
peerDependencyRules
TypeScript 允许 >=5 <7
构建脚本控制
allowBuilds
仅允许 esbuild/lefthook/node-pty/koffi 执行安装脚本
🎯
第八部分：技术选型分析
8.1 为什么选 pnpm 而不是 npm/yarn？
维度
pnpm
npm
yarn
磁盘效率
内容寻址存储，硬链接共享
每个项目独立复制
PnP 零安装但兼容性差
幽灵依赖
严格隔离（node_modules 扁平化控制）
允许幽灵依赖
Classic 允许 / PnP 不允许
Monorepo 支持
原生 workspace + 过滤
基础 workspace 支持
良好但维护分裂
安装脚本控制
pnpm 10+
allowBuilds
白名单
npm 7+ lifecycle scripts
无内置白名单
补丁支持
patchedDependencies
原生支持
需要 patch-package
Yarn 4 内置
发布年龄门禁
minimumReleaseAgeExclude
无
无
性能
最快（硬链接 + 并行）
较慢
Yarn 4 较快
关键决策因素：
pnpm 的严格依赖隔离对 50+ 包的 monorepo 至关重要 — 幽灵依赖会导致运行时难以调试的模块解析错误。
allowBuilds
白名单机制增强了供应链安全。
patchedDependencies
允许直接在 manifest 中管理 node-pty 的自定义补丁。
8.2 为什么选 Vitest 而不是 Jest？
维度
Vitest
Jest
原生 TypeScript
通过 Vite 直接运行 TS，无需 Babel/ts-jest
需要额外配置转换器
ESM 支持
完整原生 ESM 支持
ESM 支持仍不完善
速度
Vite 的 HMR + 按需转换
较慢，全局转换
兼容性
Jest API 兼容（expect/describe/it）
—
项目隔离
原生 projects 配置
需要额外配置
覆盖率
V8 原生覆盖率（无 Istanbul 开销）
Istanbul/Babel 覆盖率
配置复杂度
与 Vite 共享插件生态
独立配置体系
关键决策因素：
项目全面采用 ESM + TypeScript 6，Vitest 原生支持这两者无需任何转译配置。Vite 插件生态（如
vite-tsconfig-paths
）使得源码级路径解析在测试中无缝工作。V8 覆盖率比 Istanbul 更准确且更快。
8.3 为什么选 tsdown 而不是 webpack/rollup/esbuild？
维度
tsdown
webpack
rollup
esbuild
TypeScript 原生
直接消费 tsc 产物
需要 loader
需要插件
内置但功能有限
工作区支持
原生 workspace 模式
需手动配置
需手动配置
无内置
构建速度
Rust 内核（Rolldown）
慢
中等
快
输出格式
ESM 优先
灵活
灵活
灵活
DTS 生成
可选（项目选择 tsc 生成）
需要插件
需要插件
不支持
复杂度
极简配置
高度复杂
中等
简单
关键决策因素：
tsdown 基于 Rolldown（Rust 编写的 Rollup 替代品），提供接近 esbuild 的速度同时保持 Rollup 的插件生态兼容性。其原生 workspace 模式自动扫描所有工作区包并应用统一构建配置，极大简化了 50+ 包的构建管理。项目选择让 tsc 负责类型检查和 DTS 生成，tsdown 仅负责 JS 产物打包，实现了关注点分离。
8.4 为什么选 oxlint 而不是 ESLint？
维度
oxlint
ESLint
速度
Rust 编写，10-100x 更快
JavaScript 编写
TypeScript 类型感知
原生支持（typeAware 模式）
需要 typescript-eslint
配置复杂度
单个 JSON 文件
需要多插件 + 配置
内置规则
400+ 内置规则
需要安装插件
JS 插件兼容
支持 jsPlugins（兼容 ESLint 插件）
—
零配置启动
开箱即用
需要初始化
关键决策因素：
在 50+ 包的大型 monorepo 中，ESLint 的运行时间可能达到分钟级别。oxlint 的 Rust 内核将其压缩到秒级。项目通过
jsPlugins
兼容层继续使用
eslint-plugin-sonarjs
和
@stylistic/eslint-plugin
，无需重写这些插件。值得注意的是，
.oxlintrc.json
顶部声明了
"plugins": []
但通过
overrides
的
plugins
和
jsPlugins
字段精细控制每个文件类型的规则集。
8.5 其他关键选型
React 18（而非 19）
Web 前端使用 React 18.2.0，可能因为 React 19 的新特性（Server Components 等）对于这个 CLI-first 的桌面/Web 混合应用并非必需。保持 18 也有利于与更广泛的生态兼容。
Playwright（E2E 测试）
仅在 apps/web 中使用 Playwright 进行真实浏览器 E2E 测试。CI 中仅安装 Chromium 以减少资源消耗。通过
pnpm --filter @deepseek-ai/dsh-web-frontend exec playwright install
精确安装。
Cordis 框架（自研 IoC）
项目基于自研的 Cordis IoC（控制反转）框架构建。所有功能模块作为 Cordis 插件注册，通过服务注入实现松耦合。vendor/ 目录包含 Cordis 核心及其 7 个官方插件。
LightningCSS
lightningcss ^1.32.0
用于 CSS 处理，基于 Rust 编写，速度远超 PostCSS。在 Web 前端构建中处理 CSS 优化和转换。
📊
第九部分：技术栈总结与演进建议
9.1 技术栈全景图
核心数字
50+
Workspace 包
9
Vendor 框架包
18
CI 工作流
100%
覆盖率门禁
技术栈分层总结
层级
技术选型
特点
运行时
Node.js 22+/24+, ESM
最新 LTS + Current 双版本支持
语言
TypeScript 6, ES2024 target
最严格模式（exactOptionalPropertyTypes）
包管理
pnpm 11.7, Monorepo workspace
严格隔离 + 供应链安全控制
框架
Cordis IoC (自研)
插件化架构，服务注入
构建
tsdown (Rolldown) + tsc -b
Rust 加速 + 项目引用增量编译
前端
React 18 + Vite 6
SPA with HMR
测试
Vitest 4, 100% coverage
forks 池 + 分区覆盖 + 快照回归
E2E
Playwright (Chromium)
Web UI 浏览器级验证
Lint
oxlint (Rust) + type-aware
替代 ESLint，100x 速度提升
死代码
knip
monorepo 级未使用依赖检测
重复检测
jscpd
代码重复率门禁
发布检查
publint
npm 包发布质量验证
Git Hooks
lefthook
pre-commit lint + pre-push typecheck
CI/CD
GitHub Actions
7 必要检查 + 故障转移 + 多平台
文档
VitePress
文档站 + Mermaid 图表
沙箱
Landlock (Linux) / ACL (Windows)
原生操作系统级沙箱
类型注册
Typert (自研)
构建时类型分析 + 运行时注册
Python
Python 3.10 + uv + pytest
Python SDK 运行时
9.2 与同类项目对比
对比维度分析
与同类型 AI 编码助手/Agent 框架项目相比，deepseek-harness 在以下方面表现突出：
维度
deepseek-harness
同类项目常见做法
覆盖率要求
100% 逐文件（行业罕见）
通常 80-90% 门禁
Lint 速度
oxlint (Rust)
ESLint (JS)
构建架构
Host/Client 双面构建
单一构建管道
模块化程度
50+ 微包 + IoC 插件架构
通常 3-10 个大包
类型安全
Typert 运行时类型注册 + 严格 TS
基础 TypeScript
CI 可靠性
自动故障转移 + 双平台
单一 CI 路径
供应链安全
allowBuilds 白名单 + 发布年龄门禁
基本无控制
9.3 升级和演进建议
短期优化建议
建议
优先级
说明
补齐 GUI 测试覆盖
高
大量 Client/UI 文件标记了 TODO(gui) 排除，应逐步收窄排除列表
评估 React 19 迁移
中
React 19 的改进（Compiler、Server Components）可能对 Web 前端有益
Node 26 稳定后升级主版本
低
已在 CI 中验证 Node 26 兼容性，可等待其 LTS
中长期演进方向
方向
说明
Bun/Deno 运行时兼容
项目已全面 ESM + 无 CJS 依赖（除 schemastery 双格式），为未来运行时迁移打下基础
Rust 工具链深化
已有 oxlint (Rust) + tsdown (Rolldown/Rust) + LightningCSS (Rust)，可考虑将更多构建步骤迁移到 Rust
类型注册自动生成
Typert 系统可扩展为自动从源码生成 API 文档和 SDK 类型定义
微前端扩展
Cordis 插件架构 + Client/Host 分离天然支持微前端模式
注意：
项目的 pnpm 版本锁定在 11.7.0，且使用了
minimumReleaseAgeExclude
等 pnpm 10+ 特性。升级 pnpm 主版本前需仔细测试
allowBuilds
和
patchedDependencies
的行为变化。
DeepSeek Harness 技术栈知识图谱 • 生成于 2026-08-29 • 基于项目源码配置文件深度分析
数据来源：package.json, pnpm-workspace.yaml, tsconfig.*, tsdown.config.ts, vitest.*.config.ts, .oxlintrc.json, knip.json, lefthook.yml, .github/workflows/