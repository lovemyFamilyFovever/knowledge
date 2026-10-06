---
title: "SQL 基础术语"
tags: []
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# SQL 基础术语

> 📌 **导航**：本文是 **SQL 基础术语** 枢纽页。原十二个并列术语已归并为两族子词条——[[SQL 语言分类（DDL·DML·DQL·DCL·TCL）]] 与 [[SQL 查询与连接]]；窗口函数与 CTE 见 [[PostgreSQL高级特性]]。本页只做索引与串联，不复述子条。

## 定义

**一句话定义：** SQL 基础术语是关系数据库常用 SQL 语法的索引枢纽，把语句按"语言分类（DDL/DML/DQL/DCL/TCL）"与"查询与连接（SELECT 执行顺序、JOIN、子查询、UNION、GROUP BY+HAVING）"两族归口，高级特性（窗口函数、CTE）指向专条。

**通俗类比：** 像一份 SQL 语法总目录：先分"你在改结构还是查数据、要不要授权/提交"（语言分类），再看"怎么把多表数据查出来并分组排序"（查询与连接）；每类详细写法去对应分册。

## 为什么需要它

SQL 术语零散、易混（DELETE 还是 TRUNCATE？WHERE 能不能放聚合？JOIN 不写 ON 会怎样）。先给两张地图——按用途分类、按查询手法成族——再各指其条，能建立"看到语句知道属哪类、有什么坑"的框架，也避免在单页里堆十几个平铺小节而互相重复。

## 核心机制

本页是索引枢纽，原十二术语的归口如下（实质内容只在子条承载一次）：

| 主题 | 归口 |
|------|------|
| DDL / DML / DCL / DQL / TCL 五类与关键字 | [[SQL 语言分类（DDL·DML·DQL·DCL·TCL）]] |
| SELECT 执行顺序、JOIN、子查询、UNION、GROUP BY+HAVING | [[SQL 查询与连接]] |
| 窗口函数（RANK/ROW_NUMBER/累计） | [[PostgreSQL高级特性]] |
| CTE / WITH RECURSIVE | [[PostgreSQL高级特性]] |

一条真实查询常横跨两族：先分清它是 DQL，再在"查询与连接"里安排执行顺序与 JOIN；聚合排序之外若要排名，才引窗口函数专条。

## 具体示例

写"各部门平均薪资排名"：属 DQL（[[SQL 语言分类（DDL·DML·DQL·DCL·TCL）]]），用 `GROUP BY dept + HAVING` 聚合过滤（[[SQL 查询与连接]]），若要"部门内按薪资排名"再加窗口函数 `RANK() OVER(PARTITION BY dept ...)`（[[PostgreSQL高级特性]]）。三步各归其条、互不重复，读者按图索骥即可。

## 何时用 / 何时不用

- **用本页：** 需要快速定位某类 SQL 语法属哪族、去哪看时。
- **不用本页（转专条）：** 要具体语句写法与坑，直接进语言分类/查询与连接/PostgreSQL 专条。

## 优劣与代价

✅ 一屏建立 SQL 语法的分类与查询双框架，减少术语混淆与重复。
⚠️ 枢纽不含逐语句示例，细节在子条。
⚠️ 与 PostgreSQL 专条存在窗口/CTE 分工，避免两处重复承载。

## 与相关概念的区别

- **vs [[PostgreSQL高级特性]]：** 本篇是跨引擎的 SQL 通用语法索引，窗口/CTE 的具体示例在 PG 专条。
- **vs 两族子条：** 分类讲"语句属哪类"，查询讲"多表怎么查"，本页只串联。

## 常见误区

- SQL 只有一种，不存在按用途分类。
- 深分页和普通分页性能一样，不用担心大 OFFSET。
- JOIN 一定要写连接条件这件事无关紧要。

## 面试速答

> 🎯 SQL 基础按两族索引：语言分类 DDL/DML/DQL/DCL/TCL（DELETE 可回滚 vs TRUNCATE 属 DDL、DDL 隐式提交），查询与连接（执行顺序、JOIN/子查询/UNION/GROUP BY-HAVING）；窗口/CTE 见 PostgreSQL 专条，本页只导航。

## 相关术语

[[SQL 语言分类（DDL·DML·DQL·DCL·TCL）]]、[[SQL 查询与连接]]、[[PostgreSQL高级特性]]、[[索引与查询优化术语]]、[[数据库设计术语]]、[[事务与并发控制术语]]、[[NoSQL 数据库术语]]

## 参考资料

建议人工核验：可参考 ANSI SQL 标准（SQL:2016）与各数据库官方文档（MySQL/PostgreSQL/SQL Server），以及《SQL 必知必会》(Ben Forta)、*Database System Concepts* (Silberschatz 等)。
