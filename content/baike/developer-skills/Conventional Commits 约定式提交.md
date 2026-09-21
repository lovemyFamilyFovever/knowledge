---
title: "Conventional Commits 约定式提交"
tags: []
source: "knowledge"
collected: "2026-09-21"
status: "reviewed"
---

# Conventional Commits 约定式提交

> 📌 **导航**：本文是 **Conventional Commits（约定式提交）** 词条。相关：[[Git高级用法]]、[[02-版本控制]]、[[CI 与 CD]]、[[构建流水线与 CI-CD 工具]]。Monorepo 场景下的搭档见 [[Monorepo 单一仓库]]。

## 定义

**一句话定义：** Conventional Commits 是一套 **commit message 的书写格式规范**——`<type>[scope]: <description>` 加可选 body/footer——目的是让提交信息既对人可读，又能被程序**确定性地解析**，从而驱动版本号计算、CHANGELOG 生成和自动发布。源自 Angular 团队惯例，2017 年由社区标准化为 conventionalcommits.org。

**通俗类比：** 提交信息从"自由体日记"变成"电子小票"：人照常能读，但更重要的是收银机（工具链）能自动记账——哪些条目算新功能、哪些算修补、哪些要整本重印账目（主版本）。

## 格式

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

```
feat(auth): 增加微信登录功能

支持扫码和公众号两种方式。

BREAKING CHANGE: 移除了旧的 /login/wx 接口
```

常用的 type 其实只有一手数：

| type | 含义 | 影响版本？ |
|------|------|-----------|
| `feat` | 新功能 | MINOR |
| `fix` | 修 bug | PATCH |
| `docs` / `test` / `refactor` / `perf` / `chore` / `build` / `ci` | 其余改动 | 否 |
| `BREAKING CHANGE`（footer 或 type 后加 `!`） | 破坏性变更 | MAJOR |

> 💡 全表里真正"值钱"的只有 `feat`、`fix` 和 `BREAKING CHANGE` 三个——它们直接映射 SemVer 的三级；其余 type 纯粹给人看。破坏性变更两种写法等价：`feat!:` 或 footer 写 `BREAKING CHANGE:`。

> 💡 本知识库的 `git log`（`feat(reader): …` / `fix(theme): …`）就是这套规范的日常实践。

## 为什么需要它：一条自动化链

约定式提交的价值不在"整齐"，在于它撑起了全自动发布链：

```
开发者写规范提交
  → husky + commitlint 在 commit 时拦截不合格格式
  → CI 上 semantic-release 解析提交历史：
      有 BREAKING CHANGE？→ MAJOR
      有 feat？→ MINOR
      只有 fix？→ PATCH
  → 自动升版本、生成 CHANGELOG、打 tag、发包
```

没有机器可读的格式，上面每一步都要人脑判断"这次算 minor 还是 patch？"——人会忘、会不一致，发布就退化成手工仪式。

## 工具链

| 环节 | 工具 | 备注 |
|------|------|------|
| 校验 | commitlint + husky | 门槛，进 pre-commit/CI |
| 生成 | commitizen / cz-git | 交互式问答产出规范信息 |
| 半自动发布 | standard-version | 本地升版本 + CHANGELOG |
| 全自动发布 | semantic-release | CI 里跑，零人工干预 |
| Monorepo 多包 | changesets | 见下方追问 |

> 🔍 **追问：changesets 和 semantic-release 什么区别？**
> ① **推断依据**：semantic-release 完全从 git 历史自动推断，全自动但对提交纪律零容错；changesets 要求每次改动跑 `changeset` 命令显式声明"动了哪个包、升哪级"，是**意图声明**而非事后推断。② **战场**：semantic-release 适合单包；changesets 是 Monorepo 多包独立发布的事实标准——各包版本、各自 CHANGELOG，一次发布协调完成。

## 边界与注意

- **规范管格式、不管内容**：`feat: 优化` 格式全对、信息量为零。description 仍要写清"做了什么"。
- **历史有效性前提**：rebase/squash 合码时若把 feat 压进一堆 chore 里，版本计算就会失真——squash 后的提交信息要重新按规范写。
- **落地靠门禁不靠自觉**：commitlint 不进 pre-commit/CI，规范三周内必然名存实亡。

## 面试视角

> 🔍 **追问：Conventional Commits 和 SemVer 什么关系？**
> CC 是**输入格式**，SemVer 是**输出版本号规则**；semantic-release 这类工具是中间的翻译器——feat→MINOR、fix→PATCH、BREAKING→MAJOR 这条映射就是两者的接口。

> 🎯 关键要点：一句话总结——**给 commit message 定一套机器可解析的格式，让版本号、CHANGELOG、发布流程从"人肉仪式"变成 CI 流水线**。答题时把"格式→解析→SemVer→自动发布"这条链讲完整，比背 type 表更加分。
