---
title: "MVC"
tags: [八股文, 设计模式]
source: "knowledge"
collected: "2026-10-05"
status: "stable"
---

# MVC

## 一句话定义

模型、视图、控制器三层，各自管数据、展示、转发。

## 面试官为什么问它

他要从这个老词往下钻到双向绑定、MVVM、以及你项目里那层到底放在哪。

## 30 秒版回答

MVC 把职责切成三份：Model 管数据和规则，View 管渲染，Controller 接输入并决定改哪个 Model。关键点是流向——View 不写业务，Controller 不写渲染。前端框架里它被改造过：Vue 里组件同时扮演 View 和一部分 Controller，状态层承担 Model。

## 被追问三层时的诚实边界

我实际用过的是 NestJS 的 controller/service（Model 侧）加 Vue 组件（View 侧）这套显式分工；传统 Java 的 Servlet/JSP 时代 MVC 我没有实操过，我的理解是那正是双向绑定要解决的痛点。

## 本库深挖

- [[MVC 与 MVVM]] —— MVC/MVP/MVVM 三者对照
