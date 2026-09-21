---
title: "Monorepo 单一仓库"
tags: []
source: "knowledge"
collected: "2026-09-21"
status: "reviewed"
---

# Monorepo 单一仓库

> 📌 **导航**：本文是 **Monorepo（单一代码仓库策略）** 词条。相关：[[前端工程化核心概念]]、[[Git高级用法]]、[[CI 与 CD]]、[[02-版本控制]]。提交规范侧的搭档见 [[Conventional Commits 约定式提交]]。

## 定义

**一句话定义：** Monorepo（Monolithic Repository）是把**多个相关项目、包或服务放进同一个代码仓库**统一管理的策略——共享一套版本历史、工具链和 CI 配置；与它相对的是 Multirepo（每个项目一个独立仓库）。

**通俗类比：** Multirepo 像各部门在城市各处单独租楼，串个门要先约快递（发包、装依赖）；Monorepo 是全员坐同一栋楼——开会抬脚就到、会议室共用，代价是大楼本身得有一套管用的物业系统（权限、电梯运力、增量服务）。

## 为什么需要它

Multirepo 的典型痛点的反面，就是 Monorepo 的收益：

- **版本矩阵地狱**：组件库改一行，要走"发包 → 应用升依赖 → 再验证"的发布链；两个应用各锁 v1、v2 时，改动要维护两遍。Monorepo 里 `web-app` 直接 `import` 本地 `ui-components`，改完立即生效。
- **原子化提交**：一个特性往往同时动 UI、组件库、工具函数。单仓里一次 commit 改完，主干永远自洽；多仓里这三笔提交散在三个仓库，中间的破碎窗口无法消除。
- **统一治理**：一份 ESLint / TypeScript / 构建配置，全局重构和依赖升级一次做完，而不是 N 个仓库各催一遍。
- **协作透明**：跨团队能直接看到彼此代码与调用方式，接口对齐成本低。

> 💡 引入信号：当"同一个共享库被 2 个以上应用消费"或"多个服务需要共享协议/类型定义"出现时，Monorepo 的收益才开始盖过它的管理成本。

## 结构与工具链

目录的通行形态是 `apps/`（可部署的应用）+ `packages/`（可复用的库）：

```
github.com/org/my-project
├── apps/
│   ├── web-app/
│   └── admin-app/
├── packages/
│   ├── ui-components/
│   └── utils/
└── package.json
```

| 层次 | 工具 | 干什么 |
|------|------|--------|
| 依赖链接 | pnpm workspaces | 包之间软链直引，monorepo 的地基 |
| 任务编排 + 缓存 | Turborepo | 按依赖图跑构建，本地/远程缓存，轻量 |
| 增量计算 + 工程规范 | Nx | affected 分析、generators、插件生态，重型 |
| 多语言超大规模 | Bazel | Google 出品，跨语言构建图 |
| 版本与发布 | Changesets | 多包各自的版本号与 CHANGELOG 管理 |

> ⚠️ **Monorepo 能不能落地，分水岭在增量构建**：仓库变大后，如果 CI 每个 commit 都全量构建所有项目，流水线时间会爆炸。"只构建受本次改动影响的项目"（affected-only）+ 远程缓存是 nx/turbo 真正的价值主张——没有这层，Monorepo 只剩痛苦。

## 代价与适用边界

- **仓库体积**：clone、IDE 索引变慢。缓解：浅克隆、Git sparse checkout、让工具缓存代替重复构建。
- **权限粒度粗**：整个仓库一套读权限。CODEOWNERS 能做到"评审级"管控，但做不到"读隔离"——有保密边界的业务不适合合仓。
- **主干破坏半径大**：一个坏 commit 可能影响全部下游，必须配强 pre-commit 门禁和快速回滚。
- **不适用**：项目彼此无关；各应用需要强隔离的独立发布节奏；单应用小团队——那是过度工程。

采用者：Google、Meta、微软，开源侧 Babel、Vue、React 等都是单仓多包。

## 面试视角

> 🔍 **追问：Monorepo 里各包怎么打 tag、怎么发版？**
> 全仓一个版本号（简单，但发版节奏被最慢的包绑架）vs 每包独立 semver（主流）。实践上走 Changesets：改动时记录"这次动了哪个包、升哪一级"，发布时统一计算版本、打 `pkg@x.y.z` 前缀 tag、各包独立生成 CHANGELOG。

> 🔍 **追问：仓库太大 clone 慢怎么办？**
> `git clone --depth`、sparse-checkout 只拉需要的目录、服务端对象缓存；治本靠构建/索引增量化，而不是把仓库拆回去。

> 🎯 关键要点：Monorepo 的本质交易是**用"仓库变大、工具链变重"换"代码复用、原子提交、统一治理"**。答题时先给出这个权衡，再谈工具，比背工具表更能体现理解。
