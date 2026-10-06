---
title: "interface 与 type"
tags: [八股文, JavaScript 与 TypeScript]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# interface 与 type

## 一句话定义

interface 声明可合并的对象契约，type 是类型的别名。

## 面试官为什么问它

他八成只是想确认你不是「不知道该用哪个」，答出选择规则就够了。

## 30 秒版回答

能力上两者大部分重叠，都能描述对象、都能 extends 或用交叉类型组合。差别在语义与规则：interface 可以同名声明合并、错误信息和 IDE 提示更稳、是描述公共 API 契约的默认选择；type 能表达联合、元组、映射类型、条件类型这些 interface 表达不了的东西，也能给函数类型起名。我的规则是对外暴露的对象结构用 interface，联合与工具型推导用 type。

## 被追问三层时的诚实边界

我实际项目里两者混用但有分工约定（DTO 用 interface，联合和派生用 type）；声明合并带来的隐式覆盖风险我吃过一次亏，我的理解是公共库用 type 反而更安全，因为它不会在别处被悄悄加长。

## 本库深挖

- [[TypeScript深入]] —— 两种声明的语法边界
- [[articles/typescript/index|typescript/index]] —— 接口继承与类型别名的对照笔记
- [[TypeScript 模块与声明文件]] —— 对外声明时的取舍
