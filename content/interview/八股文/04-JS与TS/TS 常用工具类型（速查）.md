---
title: "TS 常用工具类型"
tags: [八股文, JavaScript 与 TypeScript]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# TS 常用工具类型

## 一句话定义

对已有类型做映射加工：可选、只读、挑键、去键。

## 面试官为什么问它

考的是你会不会用它们避免类型复制——两个类型不一致往往是复制粘贴造成的。

## 30 秒版回答

常用的是 Partial 把全部变可选、Required 反过来、Readonly 只读、Pick 挑几个键、Omit 去掉几个键、Record 建键值映射、Exclude 与 Extract 在联合类型上做集合运算、NonNullable 去空、ReturnType 从函数取返回类型。它们本质都是映射类型加 keyof 写的，所以能自己造。我的实践是用 Pick/Omit 从同一个源类型派生入参和出参，改一处两边跟着变。

## 被追问三层时的诚实边界

我实际天天用 Partial 做更新入参、用 Pick 裁剪响应类型；`infer` 和分发条件类型那些刁钻写法我没有实操过，我的理解是工具类型读源码比背名字有用，十行就能看完。

## 本库深挖

- [[TypeScript 高级类型与类型体操]] —— 每个工具类型的展开式
- [[TypeScript高级编程指南]] —— 映射类型与内置工具的写法
