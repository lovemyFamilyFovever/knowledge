---
title: "ESLint 与 Prettier"
tags: [八股文, 工程化与 DevOps]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# ESLint 与 Prettier

## 一句话定义

一个管代码质量与规则，一个管排版与风格。

## 面试官为什么问它

考的是你会不会把两类规则混在一起导致天天打架，以及怎么在 CI 里落地。

## 30 秒版回答

分工是明确的：Prettier 只做格式化（换行、缩进、引号），确定且无意见；ESLint 做静态检查（未使用变量、可能的错误、依赖数组缺失这类语义问题）。两边会在「该不该换行」上打架，所以通行做法是让 ESLint 关掉所有排版类规则，只留质量规则，格式化交给 Prettier，编辑器保存时先格式化再 lint。落地靠 lint-staged 只检查改动文件，加 husky 在 pre-commit 挡住，CI 里再跑一次全量兜底。

## 被追问三层时的诚实边界

我实际配过 ESLint 与 TS 规则集的组合，也在 pre-commit 里做过按文件类型跑不同检查；自定义 ESLint 插件规则我没有实操过，我的理解是它本质是遍历 AST 上报 problem。

## 本库深挖

- [[代码规范与转换工具链（Babel · ESLint · PostCSS）]] —— 三者各管哪一段
- [[现代前端工程化完全指南]] —— lint 与格式化在流水线里的接法
- [[工程化与工具链面试题库 - 45道精选题目]] —— 代码质量板块的原题
