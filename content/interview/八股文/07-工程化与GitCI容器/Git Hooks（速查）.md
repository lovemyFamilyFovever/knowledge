---
title: "Git Hooks"
tags: [八股文, 工程化与 DevOps]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# Git Hooks

## 一句话定义

在提交、推送等节点上挂脚本，让规矩自动执行。

## 面试官为什么问它

这题他会连着问「钩子被绕过怎么办」——知道边界才算真懂。

## 30 秒版回答

客户端钩子挂在本地动作上：pre-commit 在提交前跑（格式检查、lint、密钥扫描），commit-msg 校验提交信息格式，pre-push 跑测试。服务端钩子在接收时跑，用于强制策略。现代做法是 husky 管钩子文件加 lint-staged 只处理暂存文件，避免每次提交全量检查。要讲清两个局限：`--no-verify` 能绕过本地钩子，所以真正的约束必须在 CI 或服务端；另外 core.hooksPath 可以被改，团队里最好统一由工具管理。

## 被追问三层时的诚实边界

我实际写过 pre-commit 跑静态检查与 frontmatter 校验、也处理过钩子跑得比提交本身还久的问题（拆成快慢两层：本地只跑秒级检查，重活给 CI）；服务端 update hooks 与 Gerrit 那套我没有实操过，我的理解是那才是无法绕过的关口。

## 本库深挖

- [[Conventional Commits 约定式提交]] —— commit-msg 钩子校验的就是它
- [[版本控制与Git深入]] —— 钩子机制与实战位置
- [[03-代码质量]] —— 质量闸门的分层
