---
title: "SQL 查询与连接"
tags: []
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# SQL 查询与连接

> 📌 **导航**：本文是 **SQL 查询与连接** 词条，属于 database 术语集。相关枢纽：[[SQL 基础术语]]、[[SQL 语言分类（DDL·DML·DQL·DCL·TCL）]]、[[索引与查询优化术语]]、[[数据库范式]]、[[PostgreSQL高级特性]]。

## 定义

**一句话定义：** SQL 查询与连接是 SELECT 的核心手法集合——理解 FROM→WHERE→GROUP BY→HAVING→SELECT→ORDER BY→LIMIT 的执行顺序，配合 JOIN 横向拼接、子查询嵌套、UNION 纵向合并、GROUP BY+HAVING 分组过滤，完成多表数据分析。

**通俗类比：** 写 SQL 像做菜，但厨房按固定顺序开工：先从冰箱取食材(FROM)、洗掉坏的(WHERE)、同类归类(GROUP BY)、筛掉不合格的组(HAVING)、决定摆哪些盘(SELECT)、排序上菜(ORDER BY)、只上前几盘(LIMIT)——你书写顺序和它实际执行顺序并不一致。

## 为什么需要它

多数 SQL 错误（WHERE 里用聚合、GROUP BY 后 SELECT 了未分组列、JOIN 忘 ON 变笛卡尔积、深分页卡死）根因是不懂执行顺序与集合语义。掌握"书写顺序≠执行顺序"、各种 JOIN 保留哪些行、子查询/UNION/GROUP BY 的边界，才能写对复杂查询并看懂它快不快。

## 核心机制

- **执行顺序：** FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT。故 WHERE 不能用聚合、SELECT 里定义的别名常不能在 WHERE 引用。
- **JOIN：** INNER 取两表匹配交集；LEFT/RIGHT 保留左/右全集、缺配补 NULL；FULL 取并集（MySQL 用 UNION 模拟）。漏 ON 条件即笛卡尔积。
- **子查询：** 标量/IN/EXISTS/FROM 派生表；`EXISTS` 常比 `IN` 更适合大表半连接。
- **UNION vs UNION ALL：** UNION 合并去重（有排序开销），UNION ALL 仅纵向拼接不去重、更快。
- **GROUP BY + HAVING：** 先按维度分组聚合，HAVING 对"组"过滤（可用聚合），WHERE 对"行"过滤（不能用聚合）。

## 具体示例

统计"入职满一年的各部门平均薪资且人数>3"：`FROM emp` → `WHERE hire_date < 阈值`（先行过滤，不能放聚合）→ `GROUP BY dept` → `HAVING AVG(salary)>15000 AND COUNT(*)>3`（对组过滤）→ `SELECT dept, AVG(salary)`（此时才计算别名）→ `ORDER BY` → `LIMIT`。要连部门表取名就用 `JOIN dept ON e.dept_id=d.id`；要合并多来源数据用 `UNION ALL` 保性能。窗口函数、CTE 见 [[PostgreSQL高级特性]]。

## 何时用 / 何时不用

- **用：** 多表关联、分组聚合、跨结果集合并、半连接判定等分析型查询。
- **注意：** 深分页 `LIMIT 100000,10` 会扫过大量行、应用游标/覆盖索引；无 ON 的 JOIN、`SELECT *` + 大 JOIN 是常见性能雷区。

## 优劣与代价

✅ 声明式表达复杂关系运算，优化器可重写执行顺序，一行覆盖多表聚合。
⚠️ 书写与执行顺序差异带来心智负担；JOIN 与子查询写法不当易错且低效。
⚠️ 大结果集排序/去重（DISTINCT/UNION）开销显著。

## 与相关概念的区别

- **INNER vs OUTER JOIN：** 内连接只留两边匹配；外连接保留一侧全集补 NULL。
- **UNION vs JOIN：** UNION 纵向加行（列需可比），JOIN 横向加列（按关联键拼）。
- **WHERE vs HAVING：** 前者分组前行过滤、不用聚合；后者分组后组过滤、可用聚合。
- **vs [[索引与查询优化术语]]：** 本篇讲查询语义与写法，能否走索引属优化篇。

## 常见误区

- WHERE 子句里可以直接使用聚合函数（如 `WHERE COUNT(*)>3`）。
- 写了 JOIN 不写 ON 连接条件也没关系，结果一样。
- UNION 和 UNION ALL 完全等价，只是叫法不同。

## 面试速答

> 🎯 查询关键是执行顺序 FROM→WHERE→GROUP BY→HAVING→SELECT，故 WHERE 不能用聚合、SELECT 别名不能在 WHERE 用。JOIN 漏 ON 变笛卡尔积、外连接补 NULL；UNION 去重、UNION ALL 更快；GROUP BY+HAVING 做组级过滤；大 OFFSET 深分页是性能雷。

## 相关术语

[[SQL 基础术语]]、[[SQL 语言分类（DDL·DML·DQL·DCL·TCL）]]、[[索引与查询优化术语]]、[[数据库范式]]、[[PostgreSQL高级特性]]

## 参考资料

建议人工核验：可参考 ANSI SQL 标准与各数据库官方文档（JOIN/子查询/UNION/GROUP BY 语义、SELECT 逻辑处理顺序）。
