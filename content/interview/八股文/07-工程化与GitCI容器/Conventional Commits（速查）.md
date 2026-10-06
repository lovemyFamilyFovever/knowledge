---
title: "Conventional Commits"
tags: [八股文, 工程化与 DevOps]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# Conventional Commits

## 一句话定义

用 type(scope): 描述 的固定格式，让工具读得懂这次改动。

## 面试官为什么问它

简历写了它，他会问「然后你得到了什么」——规范本身没有价值，自动化才有。

## 30 秒版回答

格式是类型加可选作用域加冒号加描述：feat、fix、docs、refactor、perf、test、chore，破坏性变更加感叹号或在脚注写 BREAKING CHANGE。收益是可自动化——从提交历史生成变更日志、按类型推断语义化版本号、用 commit-msg 钩子挡下不合规提交、还能从提交直接关联发布。我的取舍是给小团队只约定 feat 与 fix 两类加破坏性标记就够用，规范太重只会逼人写废话。它和语义化版本是一对，和发布链是第二对。

## 被追问三层时的诚实边界

我实际做的是提交格式加钩子校验，并用它驱动发布说明；semantic-release 全自动发版我没有实操过，我的理解是它对分支与凭证要求高，配错会误发版本。

## 本库深挖

- [[Conventional Commits 约定式提交]] —— 格式细节与类型表
- [[语义化版本（速查）]] —— 提交类型怎么映射版本号
